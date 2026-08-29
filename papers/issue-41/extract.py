#!/usr/bin/env python3
"""Issue #41 — QUIC census extraction (Tier A feature census + Tier B embedding census).

Pipeline (mirrors #38's pattern):
  trees   : fetch recursive git trees for all corpus repos -> snapshots/trees/<repo>.json
  fetch-a : fetch Tier A implementation source files (parallel, cached under snapshots/raw/)
  fetch-b : fetch Tier B consumer manifest files
  signals : extract per-repo signals from cached raws -> snapshots/*_index.json
  view    : print a quick aggregate (feature coverage / embedding matrix)
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
    c = json.load(open(ROOT / "corpus.json"))
    if "tiers" in c:
        return {"implementations": c["tiers"]["implementations"],
                "consumers": c["tiers"]["consumers"]}
    return c

def all_repos():
    c = load_corpus()
    return [r["repo"] for r in c["implementations"]] + [r["repo"] for r in c["consumers"]]

def repo_meta(repo):
    c = load_corpus()
    for tier in ("implementations", "consumers"):
        for r in c[tier]:
            if r["repo"] == repo:
                return r
    return None

def save_head_shas():
    """Persist head_sha values into the on-disk corpus.json (preserving structure)."""
    c = json.load(open(ROOT / "corpus.json"))
    meta = load_corpus()
    for tier_key in ("implementations", "consumers"):
        for r in meta[tier_key]:
            if r.get("head_sha"):
                for orig in c["tiers"][tier_key]:
                    if orig["repo"] == r["repo"]:
                        orig["head_sha"] = r["head_sha"]
    json.dump(c, open(ROOT / "corpus.json", "w"), indent=1)

# ---------- signals ----------
FEATURES = ["0rtt", "migration", "key_update", "pmtu", "multipath", "datagram", "ecn"]
FEATURE_PATTERNS = {
    "0rtt": re.compile(r"0rtt|zero_rtt|early_data", re.I),
    "migration": re.compile(r"\bmigration\b|path_challenge|migrat", re.I),
    "key_update": re.compile(r"key_update|keyupdate|update_key", re.I),
    "pmtu": re.compile(r"\bpmtu\b|mtu_discover|mtu_probe|pmtu_discover", re.I),
    "multipath": re.compile(r"multipath|mp_path|multipath_", re.I),
    "datagram": re.compile(r"\bdatagram\b|\bdgram\b", re.I),
    "ecn": re.compile(r"\becn\b|ect[01]|congestion_experienced", re.I),
}
STACKS = ["quiche", "quic-go", "quinn", "msquic", "ngtcp2", "aioquic", "lsquic",
          "mvfst", "neqo", "picoquic", "s2n-quic", "wtransport"]
STACK_PATTERNS = {
    "quiche": re.compile(r"quiche"),
    "quic-go": re.compile(r"quic-go|github\.com/quic-go"),
    "quinn": re.compile(r"\bquinn\b|quinn-"),
    "msquic": re.compile(r"msquic|MsQuic"),
    "ngtcp2": re.compile(r"ngtcp2"),
    "aioquic": re.compile(r"aioquic"),
    "lsquic": re.compile(r"lsquic"),
    "mvfst": re.compile(r"mvfst|facebook::quic"),
    "neqo": re.compile(r"\bneqo\b"),
    "picoquic": re.compile(r"picoquic"),
    "s2n-quic": re.compile(r"s2n-quic|s2n_quic"),
    "wtransport": re.compile(r"wtransport"),
}
SRC_EXT = {".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".rs", ".go", ".py"}
MANIFEST_NAMES = {"cargo.toml", "go.mod", "cmakelists.txt", "meson.build", "setup.py",
                  "pyproject.toml", "package.json", "requirements.txt", "buck", "bzl",
                  "build.gradle", "pom.xml", "configure.ac", "configure"}
VENDOR_DIR_MARKERS = re.compile(
    r"(^|/)(deps?|vendor|third_party|3rdparty)/[^/]*(quic|http3|quiche|ngtcp2|lsquic|msquic|picoquic|mvfst|aioquic)",
    re.I)

# ---------- helpers ----------
def sh(cmd, timeout=120):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)

def gh_api(path, jq=None):
    cmd = f"gh api {path}"
    if jq:
        cmd += f" --jq '{jq}'"
    r = sh(cmd)
    if r.returncode != 0:
        print(f"  [gh api fail] {path}: {r.stderr.strip()[:120]}", file=sys.stderr)
        return None
    return r.stdout.strip()

def repo_head_sha(repo):
    meta = repo_meta(repo)
    if meta and meta.get("head_sha"):
        return meta["head_sha"]
    sha = gh_api(f"repos/{repo}/commits/HEAD", ".sha")
    if sha and meta:
        meta["head_sha"] = sha
    return sha

def fetch_tree(repo, sha):
    out = TREES / (repo.replace("/", "__") + ".json")
    if out.exists():
        return json.load(open(out))
    r = gh_api(f"repos/{repo}/git/trees/{sha}?recursive=1")
    if r is None:
        return None
    try:
        d = json.loads(r)
    except Exception:
        print(f"  [tree parse fail] {repo}", file=sys.stderr)
        return None
    TREES.mkdir(parents=True, exist_ok=True)
    json.dump(d, open(out, "w"))
    return d

def fetch_raw(repo, sha, path):
    dest = RAW / repo.replace("/", "__") / path
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    url = f"https://cdn.jsdelivr.net/gh/{repo}@{sha}/{path}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = sh(f"curl -sL --max-time 30 '{url}'")
    if r.returncode == 0 and r.stdout:
        dest.write_bytes(r.stdout.encode("utf-8", errors="replace"))
        if dest.stat().st_size > 0:
            return dest
    # fallback to raw.githubusercontent
    raw = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
    r = sh(f"curl -sL --max-time 30 '{raw}'")
    if r.returncode == 0 and r.stdout:
        dest.write_bytes(r.stdout.encode("utf-8", errors="replace"))
        return dest
    return None

# ---------- commands ----------
def cmd_trees(repos):
    shas = {}
    for repo in repos:
        sha = repo_head_sha(repo)
        if not sha:
            print(f"skip {repo}: no head sha")
            continue
        t = fetch_tree(repo, sha)
        n = len(t.get("tree", [])) if t else 0
        shas[repo] = sha
        print(f"{repo:40s} head={sha[:8]} tree_entries={n}")
        time.sleep(0.5)
    # write-through: persist head shas into on-disk corpus.json
    c = json.load(open(ROOT / "corpus.json"))
    for tier_key in ("implementations", "consumers"):
        for r in c["tiers"][tier_key]:
            if r["repo"] in shas:
                r["head_sha"] = shas[r["repo"]]
    json.dump(c, open(ROOT / "corpus.json", "w"), indent=1)
    print(f"head shas persisted: {len(shas)} repos")

def cmd_fetch_a(repos):
    """Tier A: fetch all source files of implementation repos (parallel)."""
    impls = [r["repo"] for r in load_corpus()["implementations"]]
    for repo in repos:
        if repo not in impls:
            print(f"skip {repo}: not an implementation repo")
            continue
        sha = repo_head_sha(repo)
        t = fetch_tree(repo, sha)
        if not t:
            print(f"skip {repo}: no tree")
            continue
        paths = [e["path"] for e in t.get("tree", [])
                 if e["type"] == "blob" and Path(e["path"]).suffix in SRC_EXT
                 and not e["path"].startswith("third_party/")]
        print(f"{repo}: fetching {len(paths)} source files", flush=True)
        todo = []
        for p in paths:
            if not (RAW / repo.replace("/", "__") / p).exists():
                todo.append((p, f"https://cdn.jsdelivr.net/gh/{repo}@{sha}/{p}"))
        if todo:
            listf = ROOT / ".fetch_list.txt"
            with open(listf, "w") as f:
                for p, url in todo:
                    dest = RAW / repo.replace("/", "__") / p
                    f.write(f"{url} {dest}\n")
            script = (f"cat {listf} | xargs -P 16 -n 2 bash {ROOT / 'fetch_one.sh'}")
            sh(script, timeout=280)
        got = sum(1 for p in paths if (RAW / repo.replace("/", "__") / p).exists())
        print(f"{repo}: done ({got}/{len(paths)})", flush=True)

def cmd_fetch_b(repos):
    """Tier B: fetch manifest files (shallow paths) — embedding via declared deps."""
    cons = [r["repo"] for r in load_corpus()["consumers"]]
    for repo in repos:
        if repo not in cons:
            print(f"skip {repo}: not a consumer repo")
            continue
        sha = repo_head_sha(repo)
        t = fetch_tree(repo, sha)
        if not t:
            print(f"skip {repo}: no tree")
            continue
        paths = [e["path"] for e in t.get("tree", [])
                 if e["type"] == "blob"
                 and Path(e["path"]).name.lower() in MANIFEST_NAMES
                 and e["path"].count("/") <= 3]
        todo = []
        for p in paths:
            dest = RAW / repo.replace("/", "__") / p
            if not (dest.exists() and dest.stat().st_size > 0):
                todo.append((p, f"https://cdn.jsdelivr.net/gh/{repo}@{sha}/{p}"))
        print(f"{repo}: fetching {len(todo)} shallow manifest files", flush=True)
        if todo:
            listf = ROOT / ".fetch_list.txt"
            with open(listf, "w") as f:
                for p, url in todo:
                    dest = RAW / repo.replace("/", "__") / p
                    f.write(f"{url} {dest}\n")
            script = (f"cat {listf} | xargs -P 12 -n 2 bash {ROOT / 'fetch_one.sh'}")
            sh(script, timeout=280)
        got = sum(1 for p in paths
                  if (RAW / repo.replace("/", "__") / p).exists()
                  and (RAW / repo.replace("/", "__") / p).stat().st_size > 0)
        print(f"{repo}: done ({got}/{len(paths)})", flush=True)

def cmd_signals():
    c = load_corpus()
    impls = [r["repo"] for r in c["implementations"]]
    for repo in all_repos():
        tier = "implementation" if repo in impls else "consumer"
        meta = repo_meta(repo)
        sha = meta.get("head_sha") or ""
        t = TREES / (repo.replace("/", "__") + ".json")
        tree = json.load(open(t)) if t.exists() else {}
        paths = [e["path"] for e in tree.get("tree", []) if e["type"] == "blob"]
        features = Counter()
        n_cached = 0
        for p in paths:
            f = RAW / repo.replace("/", "__") / p
            if not f.exists():
                continue
            n_cached += 1
            text = f.read_text(errors="replace")
            for feat, pat in FEATURE_PATTERNS.items():
                if pat.search(text):
                    features[feat] += 1
        embeddings = Counter()
        embed_files = defaultdict(list)
        for p in paths:
            f = RAW / repo.replace("/", "__") / p
            matched = set()
            if f.exists():
                text = f.read_text(errors="replace")
                for stack, pat in STACK_PATTERNS.items():
                    if pat.search(text):
                        matched.add(stack)
            if VENDOR_DIR_MARKERS.search(p):
                for stack in STACKS:
                    if stack.replace("-", "").lower() in p.lower():
                        matched.add(stack)
            for st in matched:
                embeddings[st] += 1
                if len(embed_files[st]) < 3:
                    embed_files[st].append(p)
        index = {
            "repo": repo, "tier": tier, "head_sha": sha,
            "source_files": n_cached,
            "features": dict(features),
            "embeddings": dict(embeddings),
            "embed_examples": dict(embed_files),
        }
        SNAP.mkdir(parents=True, exist_ok=True)
        json.dump(index, open(SNAP / (repo.replace("/", "__") + "_index.json"), "w"), indent=1)
        print(f"{repo:40s} [{tier}] src={n_cached} feat={dict(features)} emb={dict(embeddings)}")

def cmd_view():
    rows = []
    for ix in sorted(SNAP.glob("*_index.json")):
        rows.append(json.load(open(ix)))
    impls = [r for r in rows if r["tier"] == "implementation"]
    cons = [r for r in rows if r["tier"] == "consumer"]
    print("\n=== Tier A: feature coverage (files with marker) ===")
    print(f"{'repo':32s} {'files':>6s}  " + " ".join(f"{f:>9s}" for f in FEATURES))
    for r in impls:
        feats = r["features"]
        print(f"{r['repo']:32s} {r['source_files']:6d}  " +
              " ".join(f"{feats.get(f, 0):9d}" for f in FEATURES))
    print("\n=== Tier B: embedding matrix (files matching stack) ===")
    print(f"{'repo':32s} " + " ".join(f"{s:>9s}" for s in STACKS))
    for r in cons:
        emb = r["embeddings"]
        print(f"{r['repo']:32s} " +
              " ".join(f"{emb.get(s, 0):9d}" for s in STACKS))
    print("\n=== Tier B: vendor-dir / manifest signals (examples) ===")
    for r in cons:
        ex = r["embed_examples"]
        if ex:
            print(f"{r['repo']}: " + "; ".join(f"{k}:{v[0]}" for k, v in sorted(ex.items())[:4]))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "view"
    args = sys.argv[2:] or all_repos()
    if cmd == "trees":
        cmd_trees(args)
    elif cmd == "fetch-a":
        cmd_fetch_a(args)
    elif cmd == "fetch-b":
        cmd_fetch_b(args)
    elif cmd == "signals":
        cmd_signals()
    elif cmd == "view":
        cmd_view()
    else:
        print(__doc__)
