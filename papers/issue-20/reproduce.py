#!/usr/bin/env python3
"""reproduce.py — Issue #20 canonical runner (revision round 1).

Coding-Agent Instruction Files in Popular Open-Source Repositories:
  C1. adoption of agent-instruction files (AGENTS.md / CLAUDE.md /
      .github/copilot-instructions.md / .cursorrules / .cursor/rules/*)
      + naming fragmentation + per-ecosystem breakdown
  C2. content-structure heterogeneity (size, stub rate, markdown section
      presence: build/test/architecture/conventions/security/...)
  C3. cross-file duplication (SHA-256 identity of co-existing files)

Revision-round-1 changes (responding to review emrg-fe7d5b07):
  1. Section detection now uses WORD-BOUNDARY token matching instead of
     substring matching — "pr" no longer matches "Prohibited"/"Preferences"/
     "Pre-flight"/"Project"; "check" no longer matches "checklist".
     Exact semantics: headings are normalized (lowercase, non-alphanumeric
     runs -> single space) and each canonical section matches a fixed list
     of regex patterns anchored with \\b.
  2. Each snapshot file records `triggers`: for every detected section, the
     heading text that fired it — the taxonomy itself is now reproducible.
  3. C1 gains a per-ecosystem table and an AI-native-vs-popular contrast.
  4. C3 states the exact comparison scope (agent files only, same-repo).

Modes:
  reproduce.py fetch          — pull fresh data via gh api into data_snapshot/
  reproduce.py                — offline: read data_snapshot/, compute, print results
  reproduce.py --only <repo>  — fetch only <repo> (additive; snapshots frozen)

Deterministic: classification is a pure function of committed snapshot JSON;
offline output is byte-identical across runs. stdlib-only.
"""
import argparse, base64, collections, hashlib, json, math, os, re, subprocess, sys

# #18's 41 popular repos + an AI-native stratum (6)
CORPUS = [
    # JS/TS
    "react/react", "microsoft/vscode", "vuejs/vue", "angular/angular",
    "sveltejs/svelte", "mui/material-ui", "facebook/react-native",
    # Python
    "python/cpython", "django/django", "pallets/flask", "pandas-dev/pandas",
    "huggingface/transformers", "numpy/numpy",
    # Go
    "kubernetes/kubernetes", "golang/go", "gin-gonic/gin", "ollama/ollama",
    "hashicorp/terraform",
    # Rust
    "rust-lang/rust", "tokio-rs/tokio", "BurntSushi/ripgrep", "serde-rs/serde",
    # C/C++
    "torvalds/linux", "git/git", "openssl/openssl", "curl/curl",
    "tensorflow/tensorflow", "google/googletest", "redis/redis", "neovim/neovim",
    # Java/Scala
    "apache/spark", "spring-projects/spring-boot", "elastic/elasticsearch",
    # Ruby
    "rails/rails", "Homebrew/brew", "jekyll/jekyll",
    # PHP
    "laravel/laravel", "composer/composer", "symfony/symfony",
    # Dart / C++
    "flutter/flutter", "nodejs/node",
    # AI-native stratum
    "opencode-ai/opencode", "Aider-AI/aider", "cline/cline",
    "langchain-ai/langchain", "microsoft/autogen", "vercel/ai",
]

# Ecosystem map — mirrors the corpus grouping in README / manuscript §3.1.
ECOSYSTEM = {
    "JS/TS": ["react/react", "microsoft/vscode", "vuejs/vue", "angular/angular",
              "sveltejs/svelte", "mui/material-ui", "facebook/react-native"],
    "Python": ["python/cpython", "django/django", "pallets/flask",
               "pandas-dev/pandas", "huggingface/transformers", "numpy/numpy"],
    "Go": ["kubernetes/kubernetes", "golang/go", "gin-gonic/gin",
           "ollama/ollama", "hashicorp/terraform"],
    "Rust": ["rust-lang/rust", "tokio-rs/tokio", "BurntSushi/ripgrep",
             "serde-rs/serde"],
    "C/C++": ["torvalds/linux", "git/git", "openssl/openssl", "curl/curl",
              "tensorflow/tensorflow", "google/googletest", "redis/redis",
              "neovim/neovim"],
    "Java/Scala": ["apache/spark", "spring-projects/spring-boot",
                   "elastic/elasticsearch"],
    "Ruby": ["rails/rails", "Homebrew/brew", "jekyll/jekyll"],
    "PHP": ["laravel/laravel", "composer/composer", "symfony/symfony"],
    "Dart/C++": ["flutter/flutter", "nodejs/node"],
    "AI-native": ["opencode-ai/opencode", "Aider-AI/aider", "cline/cline",
                  "langchain-ai/langchain", "microsoft/autogen", "vercel/ai"],
}
REPO_ECOSYSTEM = {r: e for e, rs in ECOSYSTEM.items() for r in rs}

# Exact-path probes (root + common nested locations)
PROBE_PATHS = [
    "AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md",
    ".cursorrules", "docs/AGENTS.md", "docs/CLAUDE.md",
    "CONTRIBUTING.md",  # traditional convention baseline
]

# Directory probes: (path, label) — we list the dir and count matching files
DIR_PROBES = [
    (".cursor/rules", "cursor_rules"),
]

# Canonical section -> word-boundary-anchored regex patterns.
# Semantics (documented in manuscript §3.3):
#   * headings are normalized: lowercase; every run of non-alphanumeric
#     characters becomes a single space (so "Getting-Started" == "Getting Started")
#   * a heading fires a canonical section iff it matches ANY of the section's
#     patterns; patterns are anchored at word boundaries (\\b)
#   * the first firing heading per canonical section per file is recorded as
#     that section's `trigger`
# This replaces the substring matching used in round 0, which produced false
# positives ("pr" matched "Prohibited", "Preferences", "Pre-flight", "Project";
# "check" matched "checklist").
SECTION_RULES = {
    "build": [
        r"\bbuild(?:s|ing)?\b", r"\bcompil(?:e|es|ing|er|ers|ation)?\b",
        r"\bsetup\b", r"\binstall(?:s|ing|ed|ation)?\b",
        r"\bgetting started\b", r"\brun(?:s|ning)?\b",
        r"\bbuild from source\b",
    ],
    "test": [
        r"\btest(?:s|ing|ed|able|er|ers)?\b", r"\blint(?:s|ing|ed)?\b",
        r"\bc[íi] tests?\b", r"\btest commands?\b",
    ],
    "architecture": [
        r"\barchitectur(?:e|es|al)?\b", r"\bstructur(?:e|es|al|ing)?\b",
        r"\bdesign(?:s|ing)?\b", r"\boverview\b", r"\bcodebase\b",
    ],
    "conventions": [
        r"\bconventions?\b", r"\bstyles?\b", r"\bstyling\b",
        r"\bguidelines?\b", r"\bbest practices?\b", r"\bnaming\b",
    ],
    "security": [
        r"\bsecurity\b", r"\bvulnerab(?:le|ility|ilities)?\b",
        r"\bthreats?\b",
    ],
    "commit": [
        r"\bcommit(?:s|ted|ting)?\b", r"\bpull requests?\b", r"\bprs?\b",
        r"\bconventional commits?\b",
    ],
    "commands": [
        r"\bcommands?\b", r"\bcli\b", r"\bterminals?\b", r"\busage\b",
    ],
}
# Precompile once.
SECTION_PATTERNS = {c: [re.compile(p, re.IGNORECASE) for p in pats]
                    for c, pats in SECTION_RULES.items()}

BASE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(BASE, "data_snapshot")
MAX_BYTES = 64 * 1024  # contents API base64 cap ~ 100KB raw; we cap decoded size


def gh_json(url):
    out = subprocess.run(["gh", "api", url], capture_output=True, text=True,
                         timeout=45)
    if out.returncode != 0:
        raise RuntimeError(f"gh api {url}: {out.stderr.strip()[:160]}")
    return json.loads(out.stdout)


def _normalize_heading(title: str) -> str:
    """Lowercase; collapse every non-alphanumeric run to a single space."""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def detect_sections(content: str):
    """Deterministic markdown-heading -> section detection.

    Returns (sections, triggers): sections is a sorted list of canonical
    section names; triggers maps each canonical section to the heading text
    that first fired it (normalized).
    """
    found = []
    triggers = {}
    for line in content.splitlines():
        m = re.match(r"^\s{0,3}#{1,4}\s+(.+)$", line)
        if not m:
            continue
        heading = _normalize_heading(m.group(1))
        if not heading:
            continue
        for canon in SECTION_RULES:  # dict order = stable tie-break
            if canon in found:
                continue
            if any(p.search(heading) for p in SECTION_PATTERNS[canon]):
                found.append(canon)
                triggers[canon] = heading
                break
    return sorted(found), triggers


def fetch_repo(repo: str) -> dict:
    files = {}      # probe_label -> {size, lines, sha256, sections, triggers}
    dirs = {}       # dir_label -> [matched filenames]
    errors = []
    for path in PROBE_PATHS:
        label = path.replace("/", "_").lower()
        try:
            data = gh_json(f"repos/{repo}/contents/{path}")
            # contents API returns a dict for a file, list for a dir
            if isinstance(data, list):
                errors.append(f"{path}: unexpected dir listing")
                continue
            content = base64.b64decode(data.get("content", "")).decode(
                "utf-8", errors="replace")
            if len(content) > MAX_BYTES:
                content = content[:MAX_BYTES]
            sections, triggers = detect_sections(content)
            files[label] = {
                "size": len(content.encode("utf-8")),
                "lines": content.count("\n") + (0 if content.endswith("\n") else 1),
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "sections": sections,
                "triggers": triggers,
                "content": content,  # committed so the taxonomy is re-derivable
            }
        except RuntimeError as e:
            if "404" in str(e):
                continue  # absent
            errors.append(str(e)[:100])
    for path, label in DIR_PROBES:
        try:
            entries = gh_json(f"repos/{repo}/contents/{path}")
            if isinstance(entries, list):
                names = sorted(e.get("name", "") for e in entries
                               if e.get("type") == "file" and e["name"].endswith(".md"))
                dirs[label] = names
        except RuntimeError as e:
            if "404" not in str(e):
                errors.append(str(e)[:100])
    return {"repo": repo, "files": files, "dirs": dirs, "errors": errors}


def fetch(only=None):
    os.makedirs(SNAP_DIR, exist_ok=True)
    targets = [only] if only else CORPUS
    for repo in targets:
        dest = os.path.join(SNAP_DIR, repo.replace("/", "__") + ".json")
        if os.path.exists(dest) and not only:
            continue
        try:
            snap = fetch_repo(repo)
            with open(dest, "w") as f:
                json.dump(snap, f, indent=1, sort_keys=True)
            n = len(snap["files"])
            print(f"fetched {repo}: {n} agent files, "
                  f"cursor_rules={len(snap['dirs'].get('cursor_rules', []))}")
        except Exception as e:
            print(f"ERROR {repo}: {e}", file=sys.stderr)
    if not only:
        import datetime
        manifest = {
            "fetched_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "corpus_n": len(CORPUS),
            "probe_paths": PROBE_PATHS,
        }
        with open(os.path.join(SNAP_DIR, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=1, sort_keys=True)
        print(f"manifest written: fetched_at={manifest['fetched_at']}")


# --------------------------------------------------------------- offline mode

def load():
    snaps = []
    manifest = {}
    mp = os.path.join(SNAP_DIR, "manifest.json")
    if os.path.exists(mp):
        with open(mp) as f:
            manifest = json.load(f)
    for fn in sorted(os.listdir(SNAP_DIR)):
        if not fn.endswith(".json") or fn == "manifest.json":
            continue
        with open(os.path.join(SNAP_DIR, fn)) as f:
            snaps.append(json.load(f))
    return snaps, manifest


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="offline")
    ap.add_argument("--only")
    a = ap.parse_args()
    if a.mode == "fetch":
        fetch(a.only)
        return
    snaps, manifest = load()
    if not snaps:
        print("no snapshot data — run `reproduce.py fetch` first", file=sys.stderr)
        sys.exit(2)
    n = len(snaps)
    snap_date = manifest.get("fetched_at", "not pinned")
    out = []
    out.append("CODING-AGENT INSTRUCTION FILES IN POPULAR OSS REPOSITORIES — canonical results")
    out.append(f"corpus: n={n} repos | snapshot date: {snap_date} "
               f"(data_snapshot/manifest.json)")
    out.append("")

    # ---- classify per repo: which agent-file types present
    FILE_TYPES = ["agents", "claude", "copilot", "cursorrules", "docs_agents",
                  "docs_claude"]
    TYPE_LABEL = {"agents": "AGENTS.md", "claude": "CLAUDE.md",
                  "copilot": ".github/copilot-instructions.md",
                  "cursorrules": ".cursorrules",
                  "docs_agents": "docs/AGENTS.md", "docs_claude": "docs/CLAUDE.md"}
    AGENT_LABELS = {l for l in TYPE_LABEL.values()} | {".cursor/rules/*.md"}
    # CONTRIBUTING.md is the traditional baseline — excluded from C2/C3
    BASELINE_LABEL = "contributing.md"
    per_repo = []
    for s in snaps:
        fs = s.get("files", {})
        has = {t: (TYPE_LABEL[t].replace("/", "_").lower() in fs)
               for t in FILE_TYPES}
        has["cursor_rules"] = bool(s.get("dirs", {}).get("cursor_rules"))
        has["contributing"] = (BASELINE_LABEL in fs)
        per_repo.append((s["repo"], has, fs))

    # ---- C1: adoption + fragmentation
    out.append("C1 adoption of agent-instruction file types (n=%d):" % n)
    for t in FILE_TYPES + ["cursor_rules"]:
        k = sum(1 for _, h, _ in per_repo if h[t])
        lo, hi = wilson_ci(k, n)
        out.append(f"  {TYPE_LABEL.get(t, '.cursor/rules/*.md'):38s} {k:3d}/{n} "
                   f"({k/n:.1%}, Wilson95 {lo:.1%}-{hi:.1%})")
    k_base = sum(1 for _, h, _ in per_repo if h["contributing"])
    lo, hi = wilson_ci(k_base, n)
    out.append(f"  {'CONTRIBUTING.md (baseline)':38s} {k_base:3d}/{n} "
               f"({k_base/n:.1%}, Wilson95 {lo:.1%}-{hi:.1%})")
    any_agent = [r for r, h, _ in per_repo if any(h[t] for t in FILE_TYPES + ["cursor_rules"])]
    multi_type = [r for r, h, _ in per_repo
                  if sum(h[t] for t in FILE_TYPES + ["cursor_rules"]) >= 2]
    out.append(f"  repos with >=1 agent file: {len(any_agent)}/{n} "
               f"({len(any_agent)/n:.1%})")
    out.append(f"  repos with >=2 agent file types (fragmentation): "
               f"{len(multi_type)}/{n} ({len(multi_type)/n:.1%})")
    if multi_type:
        out.append("    multi-type repos: " + ", ".join(multi_type))
    no_agent = [r for r, h, _ in per_repo
                if not any(h[t] for t in FILE_TYPES + ["cursor_rules"])]
    out.append(f"  repos with NO agent file: {len(no_agent)}/{n}")
    if no_agent:
        out.append("    no-agent repos: " + ", ".join(no_agent))

    # ---- C1 by ecosystem (AGENTS.md + any-agent-file + dup-pair counts)
    out.append("  C1 by ecosystem (AGENTS.md / CLAUDE.md / >=1 agent file / "
               "byte-identical pairs):")
    for eco in sorted(ECOSYSTEM):
        repos = ECOSYSTEM[eco]
        hmap = {r: h for r, h, _ in per_repo if r in set(repos)}
        if not hmap:
            continue
        ka = sum(1 for r, h in hmap.items() if h["agents"])
        kc = sum(1 for r, h in hmap.items() if h["claude"])
        kany = sum(1 for r, h in hmap.items()
                   if any(h[t] for t in FILE_TYPES + ["cursor_rules"]))
        out.append(f"    {eco:10s} n={len(repos):2d} AGENTS={ka:2d} "
                   f"CLAUDE={kc:2d} any={kany:2d}")
    ai_repos = ECOSYSTEM["AI-native"]
    ai_any = sum(1 for r in ai_repos if any(h[t] for t in FILE_TYPES + ["cursor_rules"]
                                            for _, h, _ in [next(p for p in per_repo if p[0] == r)]))
    ai_ag = sum(1 for r in ai_repos if next(p for p in per_repo if p[0] == r)[1]["agents"])
    pop_repos = [r for r, _, _ in per_repo if r not in ai_repos]
    pop_any = len(any_agent) - ai_any
    pop_ag = sum(1 for r in pop_repos if next(p for p in per_repo if p[0] == r)[1]["agents"])
    out.append(f"  AI-native vs popular (AGENTS / >=1 agent file): "
               f"AI-native {ai_ag}/{len(ai_repos)} ({ai_ag/len(ai_repos):.1%}) / "
               f"{ai_any}/{len(ai_repos)} ({ai_any/len(ai_repos):.1%}) vs "
               f"popular {pop_ag}/{len(pop_repos)} ({pop_ag/len(pop_repos):.1%}) / "
               f"{pop_any}/{len(pop_repos)} ({pop_any/len(pop_repos):.1%})")
    # CONTRIBUTING overlap among agent-file repos (reviewer Q5)
    agent_with_c = sum(1 for r, h, _ in per_repo
                       if any(h[t] for t in FILE_TYPES + ["cursor_rules"]) and h["contributing"])
    out.append(f"  agent-file repos also having CONTRIBUTING.md: "
               f"{agent_with_c}/{len(any_agent)} ({agent_with_c/len(any_agent):.1%})")

    # ---- C2: content structure (agent files only — exclude baseline)
    out.append("")
    out.append("C2 content structure of found agent files (excl. CONTRIBUTING.md):")
    all_files = []
    for r, h, fs in per_repo:
        for label, meta in fs.items():
            if label == BASELINE_LABEL:
                continue
            all_files.append((r, label, meta))
    sizes = [m["size"] for _, _, m in all_files]
    if sizes:
        sizes_sorted = sorted(sizes)
        med = sizes_sorted[len(sizes_sorted) // 2]
        stubs = [m for m in all_files if m[2]["size"] < 50]
        out.append(f"  files found: {len(all_files)} | size min={sizes_sorted[0]} "
                   f"median={med} max={sizes_sorted[-1]} B")
        out.append(f"  stub files (<50 B): {len(stubs)} ({len(stubs)/len(all_files):.1%})")
        for label in sorted({l for _, l, _ in all_files}):
            grp = [(r, m) for r, l, m in all_files if l == label]
            if not grp:
                continue
            sizes_g = sorted(m["size"] for _, m in grp)
            out.append(f"  {label}: n={len(grp)} size "
                       f"min={sizes_g[0]} med={sizes_g[len(sizes_g)//2]} "
                       f"max={sizes_g[-1]}")
            if len(grp) <= 8:
                for r, m in grp:
                    out.append(f"      {r}: {m['size']}B {m['lines']}L "
                               f"sections={m['sections']}")
        # section presence across ALL agent files (root AGENTS/CLAUDE/etc)
        sec_counter = collections.Counter()
        for _, _, m in all_files:
            for s_ in m["sections"]:
                sec_counter[s_] += 1
        if sec_counter:
            out.append("  section presence (across all found agent files):")
            for s_, k in sec_counter.most_common():
                out.append(f"    {s_:14s} {k:3d}/{len(all_files)} ({k/len(all_files):.1%})")

        # ---- section taxonomy with triggering headings (reviewer Q2)
        out.append("  section taxonomy per agent file (triggering heading "
                   "normalized, in brackets):")
        for r, label, m in sorted(all_files, key=lambda x: (x[0], x[1])):
            if not m["sections"]:
                out.append(f"    {r:32s} {label:12s} no sections")
                continue
            trig = " ".join(f"{s}[{m['triggers'].get(s, '?')}]"
                            for s in m["sections"])
            out.append(f"    {r:32s} {label:12s} {trig}")

    # ---- C3: duplication (agent files only — exclude baseline)
    out.append("")
    out.append("C3 cross-file duplication (SHA-256 identity within a repo, "
               "agent files only):")
    dup_repos = []
    for r, h, fs in per_repo:
        agent_fs = {l: m for l, m in fs.items() if l != BASELINE_LABEL}
        if len(agent_fs) < 2:
            continue
        sha_map = collections.defaultdict(list)
        for label, meta in agent_fs.items():
            sha_map[meta["sha256"]].append(label)
        dup = {sha: labs for sha, labs in sha_map.items() if len(labs) >= 2}
        if dup:
            dup_repos.append((r, dup, agent_fs))
    out.append(f"  repos with >=2 agent files sharing identical content: "
               f"{len(dup_repos)}/{len(any_agent) if any_agent else 1} of agent-file repos")
    for r, dup, agent_fs in dup_repos:
        for sha, labs in dup.items():
            size = next(m["size"] for m in agent_fs.values() if m["sha256"] == sha)
            out.append(f"    {r}: {', '.join(labs)} (identical SHA {sha[:12]}, "
                       f"{size} B each)")
    # ecosystem composition of dup pairs (reviewer Q4)
    if dup_repos:
        out.append("  ecosystem of duplicated pairs:")
        for r, dup, _ in dup_repos:
            out.append(f"    {r} ({REPO_ECOSYSTEM.get(r, '?')})")
        eco_counter = collections.Counter(REPO_ECOSYSTEM.get(r, "?") for r, _, _ in dup_repos)
        out.append("  duplicated pairs by ecosystem: "
                   + ", ".join(f"{e} {c}" for e, c in eco_counter.most_common()))

    # ---- per-repo posture table (b = also has CONTRIBUTING.md baseline)
    out.append("")
    out.append("per-repo posture (A=AGENTS, C=CLAUDE, P=copilot-instructions, "
               "R=cursor/rules, D=docs-agent, b=CONTRIBUTING.md):")
    for r, h, fs in per_repo:
        marks = ""
        if h["agents"]: marks += "A"
        if h["claude"]: marks += "C"
        if h["copilot"]: marks += "P"
        if h["cursor_rules"]: marks += "R"
        if h["docs_agents"] or h["docs_claude"]: marks += "D"
        if h["contributing"]: marks += "b"
        out.append(f"    {marks if marks else '-'}  {r}")
    out.append("")
    out.append("canonical-run key: every number above derives from data_snapshot/ "
               "via deterministic classification.")
    print("\n".join(out))


if __name__ == "__main__":
    main()
