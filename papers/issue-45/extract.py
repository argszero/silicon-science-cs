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
MANIFESTS = SNAP / "manifests"

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

# ---------- a11y signals (issue #45) ----------
# a11y-SPECIFIC testing/lint dependencies only (generic e2e like playwright and
# generic testing-library DOM/React/Vue helpers are NOT a11y signals)
A11Y_TEST_DEPS = [
    "axe-core", "jest-axe", "react-axe", "@axe-core/playwright", "@axe-core/puppeteer",
    "@storybook/addon-a11y", "eslint-plugin-jsx-a11y", "@testing-library/jest-dom",
    "pa11y",
]
# manifest path segments that are NOT library source (docs apps, sandboxes,
# CLI test fixtures, examples) — a11y deps there are not the library's practice
NON_LIBRARY_MANIFEST_SEGMENTS = {"app", "apps", "docs", "website", "examples",
                                 "example", "playground", "sandbox", "test", "tests",
                                 "e2e", "fixtures", "site", "codemod", "cli"}
ARIA_ROLES = ["dialog", "switch", "combobox", "tooltip", "tablist", "tab", "menu",
              "menuitem", "alert", "alertdialog", "progressbar", "slider", "checkbox",
              "radio", "listbox", "option", "tree", "treeitem", "grid", "row",
              "columnheader", "rowheader", "gridcell", "tabpanel", "status", "banner",
              "navigation", "main", "complementary", "contentinfo", "region", "search",
              "form", "presentation", "none", "button", "link", "heading", "img",
              "textbox", "searchbox", "spinbutton", "timer", "toolbar", "log", "marquee"]

def manifest_a11y_deps(repo):
    """Scan fetched manifests for accessibility-testing dependencies."""
    repo_dir = MANIFESTS / f"{repo.replace('/', '__')}"
    hits = []
    if not repo_dir.exists():
        return hits
    for mf in sorted(repo_dir.rglob("*")):
        if not mf.is_file():
            continue
        rel = str(mf.relative_to(repo_dir))
        rel_parts = [p for p in rel.split("/") if p]
        # skip non-library manifests (docs app, sandbox, test fixtures, ...)
        if any(seg in NON_LIBRARY_MANIFEST_SEGMENTS for seg in rel_parts):
            continue
        try:
            txt = mf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(mf.relative_to(repo_dir))
        tl = txt.lower()
        for name in A11Y_TEST_DEPS:
            if re.search(rf"\b{re.escape(name)}\b", tl):
                hits.append((rel, name))
    return sorted(set(hits))[:60]

def tree_role_paths(repo):
    """Roles appearing in file paths (e.g. components/dialog, components/switch) as a
    light structural signal; content-level ARIA extraction comes in a later fetch step."""
    t = json.load(open(TREES / f"{repo.replace('/', '__')}.json"))
    paths = [e.get("path", "") for e in t["tree"]]
    roles = {}
    for p in paths:
        pl = p.lower()
        segs = set(pl.split("/"))
        for role in ARIA_ROLES:
            if role in segs or role in pl:
                roles.setdefault(role, 0)
                roles[role] += 1
    return {"tree_size": len(paths), "role_path_hits": dict(sorted(roles.items()))}

def list_component_paths(repo, cap=150, seed=42):
    """List non-test component source files (deterministic sampled, capped).

    Component-ish = contains '/src/' (library source), not a type/declaration file
    (.d.ts), not a story/index file, real implementation extension.
    """
    t = json.load(open(TREES / f"{repo.replace('/', '__')}.json"))
    # per-repo package whitelist: library source only (excludes apps/examples/demos)
    PKG_WHITELIST = {
        "twbs/bootstrap": ("scss/", "js/src/"),
        "shadcn-ui/ui": ("apps/v4/registry/",),          # registry IS the library
        "ant-design/ant-design": ("components/",),        # antd has no /src/ layout
        "mui/material-ui": ("packages/mui-material/", "packages/mui-system/", "packages/mui-lab/", "packages/mui-styled-engine/"),
        "chakra-ui/chakra-ui": ("packages/react/",),
        "mantinedev/mantine": ("packages/@mantine/",),
        "TanStack/table": ("packages/",),
        "element-plus/element-plus": ("packages/components/",),
        "microsoft/fluentui": ("packages/react/", "packages/react-components/", "packages/web-components/"),
        "radix-ui/primitives": ("packages/react/",),
        "ariakit/ariakit": ("packages/",),
        "primefaces/primereact": ("components/",),        # primereact has no /src/ layout
        "reach/reach-ui": ("packages/",),
        "vuejs/core": ("packages/",),
    }
    # repos whose library source does NOT live under a /src/ segment
    NO_SRC_LAYOUT = {"ant-design/ant-design", "primefaces/primereact", "shadcn-ui/ui"}
    # top-level demo/example/app dirs — never library source (checked only when
    # no whitelist applies, i.e. whitelisted repos already restrict to packages/)
    NOISE_PREFIXES = ("apps/", "app/", "examples/", "example/", "playground/",
                      "sandbox/", "site/", "website/", "docs/", "test/", "tests/",
                      "e2e/", "cypress/", "benchmark/", "scripts/")
    whitelist = PKG_WHITELIST.get(repo)
    paths = []
    for e in t["tree"]:
        p = e.get("path", "")
        pl = p.lower()
        name = pl.split('/')[-1]
        if not p.endswith(('.tsx', '.jsx', '.ts', '.js', '.vue')): continue
        if p.endswith('.d.ts'): continue
        if whitelist and not pl.startswith(whitelist): continue
        if not whitelist and pl.startswith(NOISE_PREFIXES): continue
        if any(x in pl for x in ('/test', '/tests', '/__tests__', '/spec', '.test.', '.spec.',
                                 '/docs', '/website', '/examples', '/node_modules', '/storybook',
                                 '.stories.', '.story.', '/dist/', '/benchmark', '/scripts', '/build',
                                 '/apps/', '/playground', '/packages/test', 'icons-material', '/icons/',
                                 '/Icons/', 'mui-icons', 'core-docs', 'material-ui-gatsby', '/docs-',
                                 '-docs', 'gatsby', '/site/', '/demo/', '/doc/', '/stories/',
                                 '/sandbox/')): continue
        if name.startswith('index.') or name.startswith('test'): continue
        if '/src/' not in pl and repo not in NO_SRC_LAYOUT: continue
        paths.append(p)
    # deterministic sample: prefer component-like names (containing a component dir) first
    def comp_rank(p):
        # component dirs (/components/ + /src/) rank above src-only package code
        # (e.g. panda-preset recipes, codemod), keeping the cap sample on the
        # actual component library rather than alphabetical package order.
        pl = p.lower()
        score = 0
        if '/components/' in pl: score += 4
        if '/src/' in pl: score += 2
        if any(x in pl for x in ('/utils/', '/types/', '/styles/', '/theme/', '/hooks/')): score -= 2
        return score
    paths.sort(key=lambda p: (-comp_rank(p), p))
    if len(paths) > cap:
        paths = paths[:cap]
    return paths

def cmd_fetch_components(repos, cap=150):
    RAW.mkdir(parents=True, exist_ok=True)
    listf = ROOT / ".fetch_list.txt"
    lines = []
    total = 0
    for repo in repos:
        for p in list_component_paths(repo, cap=cap):
            dest = RAW / f"{repo.replace('/', '__')}" / p
            if dest.exists() and dest.stat().st_size > 0:
                continue
            url = f"https://cdn.jsdelivr.net/gh/{repo}@{repo_meta(repo)['head_sha']}/{p}"
            lines.append(f"{url}\t{dest}")
            total += 1
    listf.write_text("\n".join(lines) + "\n")
    print(f"fetch-components: {total} to fetch (cap {cap}/repo)", flush=True)
    if total == 0:
        return
    script = f"cat {listf} | xargs -P 16 -n 2 bash {ROOT / 'fetch_one.sh'}"
    r = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=280)
    if r.returncode != 0:
        print(r.stderr[-500:], file=sys.stderr)
    print(f"fetch-components: done (exit {r.returncode})", flush=True)

# Count literal aria-* / role usage in BOTH syntaxes: JSX attribute (aria-x="..")
# and JS/TS object-key style ("aria-x": .., role: "dialog") — syntax-agnostic
# measure of whether library source references the attributes at all.
ARIA_ATTR_RE = re.compile(r"""["']?aria-[a-z0-9-]+["']?\s*(?::|=)""")
ROLE_RE = re.compile(r"""["']?role["']?\s*(?::|=)\s*["']([a-z0-9-]+)["']""", re.I)

def aria_content_signals(repo):
    """ARIA density + role counts from fetched component files."""
    d = RAW / f"{repo.replace('/', '__')}"
    if not d.exists():
        return {"files": 0, "aria_attrs": 0, "roles": {}}
    n_files = 0; n_aria = 0; roles = {}
    for f in sorted(d.rglob("*")):
        if not f.is_file(): continue
        if not f.name.endswith(('.tsx', '.jsx', '.ts', '.js', '.vue')): continue
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except Exception: continue
        n_files += 1
        n_aria += len(ARIA_ATTR_RE.findall(txt))
        for m in ROLE_RE.finditer(txt):
            role = m.group(1).lower()
            roles[role] = roles.get(role, 0) + 1
    return {"files": n_files, "aria_attrs": n_aria,
            "aria_density_per_file": round(n_aria / n_files, 3) if n_files else 0,
            "roles": dict(sorted(roles.items()))}

def cmd_aria():
    for repo in all_repos():
        s = aria_content_signals(repo)
        # merge into index
        idx_path = SNAP / f"{repo.replace('/', '__')}_index.json"
        idx = json.load(open(idx_path))
        idx["aria_content"] = s
        json.dump(idx, open(idx_path, "w"), indent=2)
        print(f"{repo}: files={s['files']} aria={s['aria_attrs']} density={s['aria_density_per_file']} roles={len(s['roles'])}", flush=True)

def cmd_signals():
    SNAP.mkdir(parents=True, exist_ok=True)
    cached = {f.stem.replace("__", "/") for f in TREES.glob("*.json")}
    for repo in all_repos():
        if repo not in cached:
            print(f"{repo}: tree not cached — skipping (resume-safe)", flush=True)
            continue
        a11y = manifest_a11y_deps(repo)
        tp = tree_role_paths(repo)
        s = {"repo": repo, "tree_size": tp["tree_size"],
             "a11y_test_deps": a11y,
             "role_path_hits": tp["role_path_hits"]}
        out = SNAP / f"{repo.replace('/', '__')}_index.json"
        json.dump(s, open(out, "w"), indent=2)
        deps = sorted(set(n for _, n in a11y))
        print(f"{repo}: tree={s['tree_size']} a11y_test_deps={deps} role_path_roles={len(s['role_path_hits'])}", flush=True)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "trees"
    repos = all_repos() if len(sys.argv) < 3 else sys.argv[2:]
    if cmd == "trees":
        cmd_trees(repos)
    elif cmd == "fetch-manifests":
        cmd_fetch_manifests(repos)
    elif cmd == "fetch-components":
        cmd_fetch_components(repos)
    elif cmd == "signals":
        cmd_signals()
    elif cmd == "aria":
        cmd_aria()
    elif cmd == "view":
        cmd_view()
    else:
        print(__doc__)
        sys.exit(1)
