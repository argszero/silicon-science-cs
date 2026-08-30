#!/usr/bin/env python3
"""Issue #43 — LLM evaluation-practice census extraction.

Pipeline (mirrors #41/#38):
  trees   : fetch recursive git trees for all corpus repos -> snapshots/trees/<repo>.json
            (pins head SHAs into corpus.json on first run)
  signals : extract per-repo eval signals from trees (+ optional raw files) -> snapshots/*_index.json
  view    : print a quick aggregate

TBD: raw file fetch for manifest/test-dir mining (fetch command added once signal
schema stabilizes; reuse issue-41 fetch_one.sh pattern with resume-safe cache).
"""
import json, re, subprocess, sys, time
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
TREES = SNAP / "trees"
RAW = SNAP / "raw"

# ---------- corpus ----------
def load_corpus():
    return json.load(open(ROOT / "corpus.json"))

def all_repos():
    return [r["repo"] for r in load_corpus()["tiers"]["projects"]]

def repo_meta(repo):
    for r in load_corpus()["tiers"]["projects"]:
        if r["repo"] == repo:
            return r
    return None

def save_corpus(c):
    tmp = ROOT / "corpus.json"
    json.dump(c, open(tmp, "w"), indent=2, ensure_ascii=False)
    tmp.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n")

# ---------- helpers ----------
def gh_api(path, jq=None):
    cmd = ["gh", "api", path]
    if jq:
        cmd += ["--jq", jq]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {r.stderr[:200]}")
    return r.stdout.strip()

def repo_head_sha(repo):
    # default_branch head SHA (pins the snapshot deterministically)
    return gh_api(f"repos/{repo}/git/ref/heads/{repo_meta(repo)['default_branch']}", jq=".object.sha") if repo_meta(repo).get("default_branch") else gh_api(f"repos/{repo}", jq=".default_branch")

def fetch_tree(repo, sha):
    r = gh_api(f"repos/{repo}/git/trees/{sha}?recursive=1")
    return json.loads(r)

def cmd_trees(repos):
    c = load_corpus()
    TREES.mkdir(parents=True, exist_ok=True)
    done = [f.stem for f in TREES.glob("*.json")]
    todo = [r for r in repos if r.replace("/", "__") not in done]
    print(f"trees: {len(done)} cached, fetching {len(todo)}", flush=True)
    for i, repo in enumerate(todo, 1):
        meta = next((r for r in c["tiers"]["projects"] if r["repo"] == repo), None)
        # pin default branch
        db = gh_api(f"repos/{repo}", jq=".default_branch")
        meta["default_branch"] = db
        sha = gh_api(f"repos/{repo}/git/ref/heads/{db}", jq=".object.sha")
        meta["head_sha"] = sha
        t = fetch_tree(repo, sha)
        out = TREES / f"{repo.replace('/', '__')}.json"
        json.dump({"sha": sha, "repo": repo, "truncated": t.get("truncated"),
                   "tree": t.get("tree", [])}, open(out, "w"))
        n = len(t.get("tree", []))
        print(f"  {repo} @ {sha[:10]} tree={n}{' (TRUNCATED)' if t.get('truncated') else ''}", flush=True)
        if i % 3 == 0:
            time.sleep(2)  # pace against secondary rate limits
    save_corpus(c)
    print(f"trees: {len(todo)} fetched, SHAs pinned in corpus.json", flush=True)

# ---------- signals v1 (manifest-content harness detection + tree-path benchmarks) ----------
# v1 design (R70): harness/tracing detection reads DEPENDENCY MANIFEST CONTENTS
# (v0 path-substring matching was noisy: tracing integrations and module filenames
#  polluted hits). Benchmark detection stays path-based with word boundaries.
# v1.1 (R80, revision round 1): boundary rule stated and applied by INTEGRATION
# CATEGORY in the repo, not by the vendor's product surface: a dependency is a
# harness iff its manifest-declared integration point is an evaluation module
# (e.g. llama_index's llama-index-integrations/evaluation/*); dependencies wired
# as callbacks/telemetry (langfuse, opik, langsmith, wandb, promptlayer, uptrain)
# are tracing — observability ≠ eval. Promptlayer/uptrain integrations in
# llama_index are callbacks (llama_index.callbacks.promptlayer/.uptrain), hence
# tracing; tonic-validate (llama_index.evaluation.tonic_validate) is the genuine
# harness signal.
HARNESS_DEPS = [
    "deepeval", "deep-eval", "ragas", "promptfoo", "trulens", "trulens-eval",
    "giskard", "evidently", "langcheck", "prompttools", "promptimize",
    "tonic-validate", "tonic_validate", "lm-eval", "lm_eval",
    "microsoft.extensions.ai.evaluation",
]
TRACING_DEPS = ["langfuse", "opik", "langsmith", "wandb", "promptlayer", "uptrain"]  # control: observability ≠ eval

BENCHMARK_PATTERNS = [
    r"gsm8k", r"humaneval", r"human_eval", r"mmlu", r"swe-?bench", r"hellaswag",
    r"math500", r"\baime\b", r"gpqa", r"simpleqa", r"big-?bench", r"arc_challenge",
    r"arc_easy", r"truthfulqa", r"winogrande", r"gaia\b", r"agbench", r"beir", r"hotpotqa",
]

def parse_manifest_text(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""

def manifest_content_signals(repo):
    """Scan fetched manifests of a repo for harness/tracing dependency names."""
    repo_dir = MANIFESTS / f"{repo.replace('/', '__')}"
    hits = {"harness": [], "tracing": []}
    if not repo_dir.exists():
        return hits
    for mf in sorted(repo_dir.rglob("*")):
        if not mf.is_file():
            continue
        txt = parse_manifest_text(str(mf))
        rel = str(mf.relative_to(repo_dir))
        tl = txt.lower()
        for name in HARNESS_DEPS:
            if re.search(rf"\b{re.escape(name)}\b", tl):
                hits["harness"].append((rel, name))
        for name in TRACING_DEPS:
            if re.search(rf"\b{re.escape(name)}\b", tl):
                hits["tracing"].append((rel, name))
    # dedupe (manifest, name) pairs
    for k in hits:
        hits[k] = sorted(set(hits[k]))
    return hits

def tree_path_signals(repo):
    """Benchmark + judge markers from tree paths (word-boundary)."""
    t = json.load(open(TREES / f"{repo.replace('/', '__')}.json"))
    paths = [e.get("path", "") for e in t["tree"]]
    bench, judge = [], []
    for p in paths:
        pl = p.lower()
        segs = pl.split("/")
        # docs/website/blog/examples/tutorials are teaching, not evaluation practice
        if any(s in ("docs", "docs-website", "website", "blog", "examples", "tutorial", "node_modules",
                     "versioned_docs", "api_reference", ".github", "learn_resources") for s in segs[:3]):
            continue
        for pat in BENCHMARK_PATTERNS:
            if re.search(pat, pl):
                bench.append((p, pat))
                break
        if re.search(r"(^|/)(judge|grader|rubric)[a-z_]*\.", pl) or "llm_judge" in pl or "llm-as-a-judge" in pl:
            judge.append(p)
    return {"tree_size": len(paths), "benchmark_paths": sorted(set(bench))[:60],
            "judge_paths": sorted(set(judge))[:40]}

VALIDATION_PATTERNS = [
    r"cohen", r"kappa", r"inter-?rater", r"inter-?annotator", r"\bagreement\b",
    r"calibration", r"golden set", r"human-?annotat", r"human-?label", r"ground truth",
]

# content-level judge detection (R72): judge/grading markers + LLM-call markers
# 'evaluate' verb excluded (generic); component words only (judge/grader/rubric/evaluator/criteria)
JUDGE_CONTENT_RE = re.compile(
    r"(llm[_-]?judge|llm[_-]as[_-]a[_-]judge|judge|grader|rubric|evaluator|criteria)",
    re.I)
LLM_CALL_RE = re.compile(
    r"(chat\.completions|\.generate\(|\.complete\(|client\.chat|model\.generate|"
    r"completion\(|llm\.|gpt-|claude|gemini|prompt\b|messages=|response_model)",
    re.I)

def content_judge_signal(repo):
    """Scan fetched raw source files for judge+LLM markers (content-level)."""
    d = RAW / f"{repo.replace('/', '__')}"
    hits = []
    if not d.exists():
        return hits
    for f in sorted(d.rglob("*.py")):
        rel = f.relative_to(d)
        segs = rel.as_posix().lower().split("/")
        if any(s in ("docs", "docs-website", "website", "examples", "tutorial",
                     "versioned_docs", "api_reference", "learn_resources") for s in segs[:3]):
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if JUDGE_CONTENT_RE.search(txt) and LLM_CALL_RE.search(txt):
            hits.append(str(rel))
    return sorted(set(hits))[:40]

def validation_markers(repo):
    """Scan fetched raw + manifests for human-ground-truth validation markers."""
    hits = []
    for base in (RAW, MANIFESTS):
        d = base / f"{repo.replace('/', '__')}"
        if not d.exists():
            continue
        for f in sorted(d.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(base)
            segs = rel.as_posix().lower().split("/")
            # docs are teaching, not evaluation practice
            if any(s in ("docs", "docs-website", "website", "examples", "tutorial",
                         "versioned_docs", "api_reference", "learn_resources") for s in segs[:3]):
                continue
            try:
                txt = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            tl = txt.lower()
            for pat in VALIDATION_PATTERNS:
                if re.search(pat, tl):
                    hits.append((str(rel), pat))
                    break
    return sorted(set(hits))[:40]

def cmd_signals():
    SNAP.mkdir(parents=True, exist_ok=True)
    cached = {f.stem.replace("__", "/") for f in TREES.glob("*.json")}
    for repo in all_repos():
        if repo not in cached:
            print(f"{repo}: tree not cached — skipping (resume-safe)", flush=True)
            continue
        content = manifest_content_signals(repo)
        tree = tree_path_signals(repo)
        s = {"repo": repo, "tree_size": tree["tree_size"],
             "harness_deps": content["harness"],
             "tracing_deps": content["tracing"],
             "benchmark_paths": tree["benchmark_paths"],
             "judge_paths": tree["judge_paths"],
             "content_judge": content_judge_signal(repo),
             "validation_markers": validation_markers(repo)}
        out = SNAP / f"{repo.replace('/', '__')}_index.json"
        json.dump(s, open(out, "w"), indent=2)
        h = sorted(set(n for _, n in s["harness_deps"]))
        tr = sorted(set(n for _, n in s["tracing_deps"]))
        v = len(s["validation_markers"])
        print(f"{repo}: tree={s['tree_size']} harness={h} tracing={tr} bench={len(s['benchmark_paths'])} judge={len(s['judge_paths'])} valid={v}", flush=True)

def cmd_view():
    from tabulate import tabulate
    rows = []
    for repo in all_repos():
        idx = json.load(open(SNAP / f"{repo.replace('/', '__')}_index.json"))
        h = sorted(set(n for _, n in idx.get("harness_deps", [])))
        tr = sorted(set(n for _, n in idx.get("tracing_deps", [])))
        rows.append([repo, idx["tree_size"], ",".join(h) or "—", ",".join(tr) or "—",
                     len(idx.get("benchmark_paths", [])), len(idx.get("judge_paths", [])),
                     len(idx.get("validation_markers", []))])
    print(tabulate(rows, headers=["repo", "tree", "harness", "tracing", "bench", "judge", "valid"]))
MANIFEST_NAMES = {
    "pyproject.toml", "package.json", "go.mod", "requirements.txt",
    "requirements-dev.txt", "requirements-dev.in", "requirements-test.txt",
    "Cargo.toml", "setup.py", "setup.cfg",
}
MANIFESTS = SNAP / "manifests"

def list_manifest_paths(repo):
    t = json.load(open(TREES / f"{repo.replace('/', '__')}.json"))
    out = []
    for e in t["tree"]:
        p = e.get("path", "")
        name = p.rsplit("/", 1)[-1]
        if name in MANIFEST_NAMES or p.endswith(".csproj"):
            # exclude vendored / docs-only / template copies
            pl = p.lower()
            if any(x in pl for x in ("node_modules/", "/docs/", "docs/", "/examples/", "/benchmark/", "/tests/benchmark", "{{", "}")):
                continue
            out.append(p)
    return out

def cmd_fetch_manifests(repos):
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    listf = ROOT / ".fetch_list.txt"
    lines = []
    total = 0
    for repo in repos:
        for p in list_manifest_paths(repo):
            dest = MANIFESTS / f"{repo.replace('/', '__')}" / p
            if dest.exists() and dest.stat().st_size > 0:
                continue
            url = f"https://cdn.jsdelivr.net/gh/{repo}@{repo_meta(repo)['head_sha']}/{p}"
            lines.append(f"{url}\t{dest}")
            total += 1
    listf.write_text("\n".join(lines) + "\n")
    print(f"fetch-manifests: {total} to fetch", flush=True)
    if total == 0:
        return
    script = (f"cat {listf} | xargs -P 16 -n 2 bash {ROOT / 'fetch_one.sh'}")
    r = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=280)
    if r.returncode != 0:
        print(r.stderr[-500:], file=sys.stderr)
    print(f"fetch-manifests: done (exit {r.returncode})", flush=True)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "trees"
    repos = all_repos() if len(sys.argv) < 3 else sys.argv[2:]
    if cmd == "trees":
        cmd_trees(repos)
    elif cmd == "fetch-manifests":
        cmd_fetch_manifests(repos)
    elif cmd == "signals":
        cmd_signals()
    elif cmd == "view":
        cmd_view()
    else:
        print(__doc__)
        sys.exit(1)
