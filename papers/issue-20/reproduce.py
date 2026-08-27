#!/usr/bin/env python3
"""reproduce.py — Issue #20 canonical runner.

Coding-Agent Instruction Files in Popular Open-Source Repositories:
  C1. adoption of agent-instruction files (AGENTS.md / CLAUDE.md /
      .github/copilot-instructions.md / .cursorrules / .cursor/rules/*)
      + naming fragmentation
  C2. content-structure heterogeneity (size, stub rate, markdown section
      presence: build/test/architecture/conventions/security/...)
  C3. cross-file duplication (SHA-256 identity of co-existing files)

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

# Markdown heading section detection: keyword -> canonical section name
SECTION_KEYWORDS = {
    "build": ("build", "compile", "setup", "install", "getting started", "run"),
    "test": ("test", "testing", "lint", "linting", "check"),
    "architecture": ("architecture", "structure", "design", "overview", "codebase"),
    "conventions": ("convention", "style", "guideline", "best practice", "naming"),
    "security": ("security", "vulnerab", "threat"),
    "commit": ("commit", "pull request", "pr", "conventional"),
    "commands": ("command", "cli", "terminal", "usage"),
}

BASE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(BASE, "data_snapshot")
MAX_BYTES = 64 * 1024  # contents API base64 cap ~ 100KB raw; we cap decoded size


def gh_json(url):
    out = subprocess.run(["gh", "api", url], capture_output=True, text=True,
                         timeout=45)
    if out.returncode != 0:
        raise RuntimeError(f"gh api {url}: {out.stderr.strip()[:160]}")
    return json.loads(out.stdout)


def detect_sections(content: str) -> list:
    """Deterministic markdown-heading -> section keyword detection."""
    found = []
    for line in content.splitlines():
        m = re.match(r"^\s{0,3}#{1,4}\s+(.+)$", line)
        if not m:
            continue
        title = m.group(1).lower()
        for canon, kws in SECTION_KEYWORDS.items():
            if canon in found:
                continue
            if any(k in title for k in kws):
                found.append(canon)
                break
    return sorted(found)


def fetch_repo(repo: str) -> dict:
    files = {}      # probe_label -> {size, lines, sha256, sections, preview}
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
            files[label] = {
                "size": len(content.encode("utf-8")),
                "lines": content.count("\n") + (0 if content.endswith("\n") else 1),
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "sections": detect_sections(content),
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
            dup_repos.append((r, dup))
    out.append(f"  repos with >=2 agent files sharing identical content: "
               f"{len(dup_repos)}/{len(any_agent) if any_agent else 1} of agent-file repos")
    for r, dup in dup_repos:
        for sha, labs in dup.items():
            out.append(f"    {r}: {', '.join(labs)} (identical SHA {sha[:12]})")

    # ---- per-repo posture table
    out.append("")
    out.append("per-repo posture (A=AGENTS, C=CLAUDE, P=copilot-instructions, "
               "R=cursor/rules, D=docs-agent):")
    for r, h, fs in per_repo:
        marks = ""
        if h["agents"]: marks += "A"
        if h["claude"]: marks += "C"
        if h["copilot"]: marks += "P"
        if h["cursor_rules"]: marks += "R"
        if h["docs_agents"] or h["docs_claude"]: marks += "D"
        out.append(f"    {marks if marks else '-'}  {r}")
    out.append("")
    out.append("canonical-run key: every number above derives from data_snapshot/ "
               "via deterministic classification.")
    print("\n".join(out))


if __name__ == "__main__":
    main()
