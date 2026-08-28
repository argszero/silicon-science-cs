#!/usr/bin/env python3
"""reproduce.py — issue #29: RISC-V ISA extension usage measurement pipeline.

Modes:
  fetch [repo...]  : download tarball snapshot (codeload), scan detection channels,
                     write data_snapshot/<repo>.json (+ manifest.json)
  summary          : print per-repo extension groups from data_snapshot/
  offline          : re-aggregate snapshots -> expected_output/discovery_results.txt
                     (byte-identical to fetch-time aggregation)

Channels:
  C1 -march= build flags | C2 .arch/.option asm directives | C3 __riscv_* macros
  C4 riscv_* intrinsics headers | C5 CONFIG_RISCV_ISA_* (Kconfig)
  X1 x86 (AVX/SSE) | X2 ARM (NEON/SVE) — cross-ISA baseline
"""
import json, os, re, subprocess, sys, tarfile, urllib.request, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data_snapshot"
RAW = ROOT / "data_raw"
OUT = ROOT / "expected_output"
CORPUS = ROOT / "corpus.json"
TARBALL_LIMIT_MB = 250

# ---------------- detection regexes ----------------
RE_MARCH = re.compile(r'-march\s*=\s*"?((?:rv32|rv64)[a-z0-9_]+)"?')
RE_ARCH_ASM = re.compile(r'\.arch\s+((?:rv32|rv64)[a-z0-9_]*)')
RE_OPTION_ARCH = re.compile(r'\.option\s+arch,\s*\+([a-z0-9_]+)')
RE_RISCV_MACRO = re.compile(r'\b__riscv_([a-z0-9_]+)\b')
RE_INTRINSIC_H = re.compile(r'#\s*include\s*[<"](riscv_[a-z0-9_]+\.h)[>"]')
RE_KCONFIG_DEF = re.compile(r'^\s*config\s+RISCV_ISA_([A-Z0-9_]+)', re.M)
RE_KCONFIG_USE = re.compile(r'CONFIG_RISCV_ISA_([A-Z0-9_]+)')
RE_X86_MACRO = re.compile(r'\b(__AVX512[A-Z0-9_]*|__AVX2__|__SSE4_2__|__SSSE3__)\b')
RE_ARM_MACRO = re.compile(r'\b(__ARM_NEON|__ARM_FEATURE_SVE[A-Z0-9_]*)\b')
RE_X86_H = re.compile(r'#\s*include\s*[<"](immintrin\.h)[>"]')
RE_ARM_H = re.compile(r'#\s*include\s*[<"](arm_neon\.h|arm_sve\.h)[>"]')
RE_EXT_IN_STRING = re.compile(r'_([a-z][a-z0-9]*)')

EXT_GROUPS = {
    "V":   {"v", "zve32x", "zve32f", "zve64x", "zve64f", "zve32d", "zve64d",
            "zvbb", "zvbc", "zvbkb", "zvkg", "zvkn", "zvkned", "zvknha",
            "zvknhb", "zvks", "zvksed", "zvksh", "zvkt", "zvfh", "zvfhmin",
            "zvl32b", "zvl64b", "zvl128b", "zvl256b", "zvl512b", "zvl1024b",
            "zvl2048b", "zvl4096b"},
    "Zb":  {"zba", "zbb", "zbc", "zbs", "zbkb"},
    "K":   {"zk", "zkn", "zknd", "zkne", "zknh", "zkr", "zks", "zksed", "zksh",
            "zkt", "zkne", "zknd"},
    "MiscRatified": {"zicbom", "zicboz", "zicond", "zihintpause", "zihintntl",
                     "zfa", "zfh", "zfhmin", "zfinx", "zdinx", "zinx",
                     "zimop", "zawrs", "zmmul", "zcmt", "zcmp", "zcd", "zcf",
                     "zicfilp", "zicfiss", "zaamo", "zalrsc", "zacas",
                     "zabha", "svnapot", "svpbmt", "svinval", "ssqosid",
                     "supm", "zicntr", "zihpm", "zawrs", "ztso"},
}

def wilson_ci(k, n, z=1.96):
    """Wilson score interval for a proportion k/n."""
    if n == 0:
        return 0.0, 0.0
    import math
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def classify(exts):
    """exts: set of lowercase extension letters -> sorted group list."""
    groups = []
    for g, members in EXT_GROUPS.items():
        if exts & members:
            groups.append(g)
    if any(e.startswith("x") for e in exts):
        groups.append("Custom")
    return sorted(groups)

def scan_text(text, path):
    """Return dict of channel -> {token: [paths]}. path is the repo-relative file path."""
    hits = {}
    def add(ch, tok, p):
        hits.setdefault(ch, {}).setdefault(tok, []).append(p)
    for m in RE_MARCH.finditer(text): add("C1_march", m.group(1), path)
    for m in RE_ARCH_ASM.finditer(text): add("C2_arch", m.group(1), path)
    for m in RE_OPTION_ARCH.finditer(text): add("C2_option_arch", m.group(1), path)
    for m in RE_RISCV_MACRO.finditer(text): add("C3_macro", m.group(1), path)
    for m in RE_INTRINSIC_H.finditer(text): add("C4_intrinsics", m.group(1), path)
    for m in RE_KCONFIG_DEF.finditer(text): add("C5_kconfig_def", m.group(1), path)
    for m in RE_KCONFIG_USE.finditer(text): add("C5_kconfig_use", m.group(1), path)
    for m in RE_X86_MACRO.finditer(text): add("X1_x86_macro", m.group(1), path)
    for m in RE_ARM_MACRO.finditer(text): add("X2_arm_macro", m.group(1), path)
    for m in RE_X86_H.finditer(text): add("X1_x86_header", m.group(1), path)
    for m in RE_ARM_H.finditer(text): add("X2_arm_header", m.group(1), path)
    return hits

def get_head_sha(repo):
    try:
        out = subprocess.run(["gh", "api", f"repos/{repo}/commits/HEAD", "--jq", ".sha"],
                             capture_output=True, text=True, timeout=20)
        sha = out.stdout.strip()
        if out.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", sha):
            return sha
    except Exception:
        pass
    return None

def get_default_branch(repo):
    try:
        out = subprocess.run(["gh", "api", f"repos/{repo}", "--jq", ".default_branch"],
                             capture_output=True, text=True, timeout=20)
        b = out.stdout.strip()
        if out.returncode == 0 and b:
            return b
    except Exception:
        pass
    return "main"

def rate_remaining():
    try:
        out = subprocess.run(["gh", "api", "rate_limit", "--jq", ".resources.core.remaining"],
                             capture_output=True, text=True, timeout=15)
        return int(out.stdout.strip())
    except Exception:
        return None

# candidate file filter: riscv-named paths + build-system files + Kconfig*
BUILD_BASENAMES = {"makefile", "cmakelists.txt", "meson.build", "configure", "configure.ac"}
BUILD_SUFFIXES = (".mk", ".cmake")
SRC_SUFFIXES = (".s", ".sx", ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".S")
def is_candidate(relpath):
    pl = relpath.lower()
    bn = pl.rsplit("/", 1)[-1]
    if "riscv" in pl or re.search(r"(^|/)rv(32|64)", pl):
        return True
    if bn in BUILD_BASENAMES or bn.endswith(BUILD_SUFFIXES) or bn.startswith("kconfig"):
        return True
    if bn.endswith(SRC_SUFFIXES) and ("rvv" in pl or "rv64" in pl or "rv32" in pl):
        return True
    return False

def get_token():
    """Read gh token once, keep in memory (never persisted/printed)."""
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not tok:
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=20)
        tok = out.stdout.strip()
    return tok

_TOKEN = None
def _gh_http(url):
    global _TOKEN
    if _TOKEN is None:
        _TOKEN = get_token()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {_TOKEN}",
        "User-Agent": "emrgd-journal",
        "Accept": "application/vnd.github+json",
        "Accept-Encoding": "gzip",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            import gzip as _gzip
            data = _gzip.decompress(data)
        return data

def fetch_blob(repo, blob_sha, timeout=30):
    """Fetch blob content via api.github.com git/blobs (fast + reliable)."""
    data = json.loads(_gh_http(f"https://api.github.com/repos/{repo}/git/blobs/{blob_sha}"))
    return bytes(data["content"], "utf-8").decode("base64") if False else __import__("base64").b64decode(data["content"])

def api_tree_recursive(repo, sha):
    """Try recursive=1 tree; returns (list_of_(path, blob_sha), ok)."""
    try:
        data = json.loads(_gh_http(f"https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1"))
        entries = data.get("tree", [])
        if data.get("truncated"):
            return [], False
        pairs = [(e["path"], e["sha"]) for e in entries if e.get("type") == "blob"]
        return pairs, True
    except Exception:
        return [], False

def api_walk_per_level(repo, root_sha, cap=4000, scope=None):
    """Per-level non-recursive descent (robust for huge trees). Returns (path, blob_sha) pairs.
    When scope prefixes are given, only directories inside those prefixes are descended."""
    from collections import deque

    def in_scope(rel):
        if not scope:
            return True
        return any(rel == s or rel.startswith(s + "/") or
                   s.startswith(rel + "/") or rel == ""
                   for s in scope)

    found = []
    dq = deque([(root_sha, "")])
    seen = set()
    while dq and len(found) < cap:
        tree_sha, prefix = dq.popleft()
        if tree_sha in seen:
            continue
        seen.add(tree_sha)
        try:
            data = json.loads(_gh_http(f"https://api.github.com/repos/{repo}/git/trees/{tree_sha}"))
        except Exception:
            continue
        for e in data.get("tree", []):
            rel = f"{prefix}/{e['path']}" if prefix else e["path"]
            if e.get("type") == "tree":
                if in_scope(rel):
                    dq.append((e["sha"], rel))
            elif e.get("type") == "blob" and is_candidate(rel) and in_scope(rel):
                found.append((rel, e["sha"]))
    return found



def fetch_tarball(repo, branch):
    """Download + extract repo tarball into data_raw/<repo>/. Returns extracted dir."""
    dest = RAW / repo
    if dest.exists():
        return dest
    owner, name = repo.split("/")
    url = f"https://codeload.github.com/{owner}/{name}/tar.gz/refs/heads/{branch}"
    dest.mkdir(parents=True, exist_ok=True)
    tmp = dest / "repo.tar.gz"
    for attempt in (1, 2, 3):
        try:
            subprocess.run(["curl", "-sL", "-m", "900", "-o", str(tmp), url], check=True)
            break
        except subprocess.CalledProcessError:
            if attempt == 3:
                raise
            print(f"   curl attempt {attempt} failed, retrying...", flush=True)
    with tarfile.open(tmp) as tf:
        members = tf.getmembers()
        # strip top-level dir
        rootname = members[0].name.split("/")[0]
        for m in members:
            if m.name == rootname:
                continue
            m.name = m.name[len(rootname)+1:]
        tf.extractall(dest, filter="data")
    tmp.unlink()
    return dest

def fetch_raw(repo, sha, path, timeout=30):
    """Fetch raw file content via raw.githubusercontent.com."""
    url = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "emrgd-journal"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

MACRO_EXT_RE = re.compile(r"z[a-z0-9]{1,6}|zv[a-z0-9]{1,6}|v")
PSEUDO_MACROS = {"xlen", "flen", "vlen", "elen", "xlen32", "xlen64", "freg", "vreg"}

# RISC-V intrinsics headers → canonical extension letters
INTRINSIC_HEADER_EXTS = {
    "riscv_vector.h": "v",
    "riscv_bitmanip.h": "zbb",
    "riscv_crypto.h": "zk",
    "riscv_svector.h": "s",
    # zv* vector-crypto / vector-fp16 headers (as shipped by LLVM/gcc)
    "riscv_zvbb.h": "zvbb", "riscv_zvbc.h": "zvbc", "riscv_zvkg.h": "zvkg",
    "riscv_zvkned.h": "zvkned", "riscv_zvknha.h": "zvknha",
    "riscv_zvksed.h": "zvksed", "riscv_zvksh.h": "zvksh",
    "riscv_zvfh.h": "zvfh", "riscv_zvfhmin.h": "zvfhmin",
}

# ISA march-string parsing: rv64gcv_zba_zbb -> base letters {g,c,v} + exts {zba,zbb}
def march_letters(march):
    """Return (base_letters, extension_letters) from a march string like
    rv64gcv_zba_zbb_zvl512b or rv32imv or rv64gc_zfh_xtheadvector."""
    m = re.match(r"rv(?:32|64)([a-z]+)(.*)$", march.lower())
    if not m:
        return set(), set()
    base, rest = m.group(1), m.group(2)
    # base letters: everything before the first z/x extension marker
    base = re.match(r"([a-z]*?)(?:z|x)", base).group(1) if re.match(r"([a-z]*?)(?:z|x)", base) else base
    exts = set()
    # 'v' in base letters (rv64gcv, rv32imv) means the V extension
    if "v" in base:
        exts.add("v")
    for part in re.split(r"[_]", rest):
        part = part.strip()
        if not part:
            continue
        if part.startswith("z") or part.startswith("x"):
            exts.add(part)
        elif part in ("svinval", "svnapot", "svpbmt", "ssqosid", "supm"):
            exts.add(part)
    base_set = set(base)
    return base_set, exts

def exts_from_hits(hits):
    """Extension letters from channel hits only (no free-text regex noise)."""
    exts = set()
    for ch in ("C1_march", "C2_arch"):
        for tok in hits.get(ch, {}):
            _, e = march_letters(tok)
            exts |= e
    for tok in hits.get("C2_option_arch", {}):
        exts.add(tok.lower())
    for tok in hits.get("C3_macro", {}):
        if tok in PSEUDO_MACROS:
            continue
        if re.fullmatch(MACRO_EXT_RE, tok):
            exts.add(tok)
    for tok in hits.get("C4_intrinsics", {}):
        m = re.match(r"riscv_([a-z0-9_]+)\.h", tok)
        if m:
            canon = INTRINSIC_HEADER_EXTS.get(tok)
            if canon:
                exts.add(canon)
    for tok in hits.get("C5_kconfig_def", {}):
        exts.add(tok.lower())
    for tok in hits.get("C5_kconfig_use", {}):
        exts.add(tok.lower())
    return {e for e in exts if re.fullmatch(r"[a-z][a-z0-9]*", e)}

RISCV_PATH_RE = re.compile(r"(^|/)(riscv|rv\d{2}|rvv)", re.I)
X86_PATH_RE = re.compile(r"(^|/)(x86|x64|avx|avx2|avx512|sse|sse2|ssse3|sse4)", re.I)
ARM_PATH_RE = re.compile(r"(^|/)(arm|arm64|neon|sve)", re.I)
CROSSISA_PATH_RE = re.compile(
    r"(^|/)(riscv|rv\d{2}|rvv|x86|x64|avx|avx2|avx512|sse|sse2|ssse3|sse4|"
    r"arm|arm64|neon|sve)", re.I)

def scan_repo_api(repo, branch, scope=None, riscv_paths_only=False,
                  crossisa=False):
    sha = get_head_sha(repo)
    if not sha:
        print(f"   !! could not resolve head sha (rate limit?) — skipping", flush=True)
        return None
    pairs, ok = api_tree_recursive(repo, sha)
    if not ok or not pairs:
        print(f"   recursive=1 failed/truncated -> per-level walk (scope-pruned)",
              flush=True)
        pairs = api_walk_per_level(repo, sha, scope=scope)
    if riscv_paths_only:
        pairs = [(p, b) for (p, b) in pairs if RISCV_PATH_RE.search(p)]
        print(f"   riscv-path-filtered: {len(pairs)} files", flush=True)
    if crossisa:
        pairs = [(p, b) for (p, b) in pairs
                 if CROSSISA_PATH_RE.search(p) or is_candidate(p)]
        print(f"   cross-isa-path-filtered (+build files): {len(pairs)} files",
              flush=True)
    if scope:
        pairs = [(p, b) for (p, b) in pairs
                 if any(p.startswith(s + "/") or p == s for s in scope)]
        print(f"   scoped to {scope}: {len(pairs)} files", flush=True)
    total = len(pairs)
    if total == 0:
        print(f"   !! tree walk returned 0 files (rate limit?) — skipping", flush=True)
        return None
    # cross-ISA scans keep ALL filtered paths (isa-named kernel files must not
    # be dropped by the riscv-biased candidate filter); cap to fit rate budget
    if crossisa or riscv_paths_only:
        cands = pairs[:3000]
        sel = "all-filtered"
    # full scan only for small repos (complete coverage); candidate filter for big trees
    elif total <= 600:
        cands = pairs
        sel = "all"
    else:
        cands = [(p, b) for (p, b) in pairs if is_candidate(p)]
        sel = "candidates"
    print(f"   tree: {total} files, {len(cands)} {sel} (cap 3000)", flush=True)
    cands = cands[:3000]
    all_hits = {}
    per_file = {}
    files_scanned = 0
    done = 0
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_blob, repo, b): p for (p, b) in cands}
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                data = fut.result()
            except Exception:
                continue
            done += 1
            if done % 50 == 0:
                print(f"   ...{done}/{len(cands)} fetched", flush=True)
            if b"\x00" in data[:4096]:
                continue
            try:
                text = data.decode("utf-8", errors="ignore")
            except Exception:
                continue
            files_scanned += 1
            h = scan_text(text, p)
            if h:
                per_file[p] = h
                for ch, toks in h.items():
                    for tok, paths_ in toks.items():
                        all_hits.setdefault(ch, {}).setdefault(tok, []).extend(paths_)
    exts = exts_from_hits(all_hits)
    return {
        "repo": repo, "branch": branch, "head_sha": sha,
        "fetched_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "api", "n_files_scanned": files_scanned,
        "channel_hits": all_hits, "n_files_with_hits": len(per_file),
        "exts": sorted(exts),
    }

def scan_repo(repo, branch, scope=None, riscv_paths_only=False,
             crossisa=False):
    return scan_repo_api(repo, branch, scope=scope,
                         riscv_paths_only=riscv_paths_only,
                         crossisa=crossisa)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    if mode == "fetch":
        corpus = json.loads(CORPUS.read_text())
        repos = sys.argv[2:] or [c["repo"] for c in corpus]
        manifest = []
        SNAP.mkdir(parents=True, exist_ok=True)
        for repo in repos:
            c = next((x for x in corpus if x["repo"] == repo), {"repo": repo, "channels": []})
            branch = "main"
            # resolve default branch
            try:
                out = subprocess.run(["gh", "api", f"repos/{repo}", "--jq", ".default_branch"],
                                     capture_output=True, text=True, timeout=20)
                branch = out.stdout.strip() or branch
            except Exception:
                pass
            print(f"== fetching {repo} ({branch}) ==", flush=True)
            rem = rate_remaining()
            if rem is not None and rem < 2000:
                print(f"   !! API rate remaining {rem} < 2000 — stopping to avoid exhaustion", flush=True)
                break
            scope = c.get("scope")
            rpo = c.get("riscv_paths_only", False)
            ci = c.get("crossisa", False)
            snap = scan_repo(repo, branch, scope=scope,
                             riscv_paths_only=rpo, crossisa=ci)
            if snap is None:
                print(f"   !! snapshot failed for {repo}, skipping", flush=True)
                continue
            (SNAP / (repo.replace("/", "__") + ".json")).write_text(json.dumps(snap, indent=1, ensure_ascii=False))
            manifest.append({"repo": repo, "branch": branch, "head_sha": snap["head_sha"],
                             "fetched_at": snap["fetched_at"]})
            print(f"   {snap['n_files_scanned']} files, hits: {sum(len(v) for v in snap['channel_hits'].values())} tokens", flush=True)
        (SNAP / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
        print("fetch done ->", SNAP)
    elif mode == "summary":
        corpus = json.loads(CORPUS.read_text())
        for c in corpus:
            sp = SNAP / (c["repo"].replace("/", "__") + ".json")
            if not sp.exists():
                print(f"{c['repo']}: NO SNAPSHOT")
                continue
            s = json.loads(sp.read_text())
            exts = exts_from_hits(s["channel_hits"])
            groups = classify(exts)
            toks = sum(len(v) for v in s["channel_hits"].values())
            print(f"{c['repo']}: {len(exts)} ext tokens, {toks} hit-tokens, groups={groups}")
    elif mode == "offline":
        out = []
        corpus = json.loads(CORPUS.read_text()) if CORPUS.exists() else []
        snaps = []
        for sp in sorted(SNAP.glob("*__*.json")):
            if sp.name == "manifest.json":
                continue
            snaps.append(json.loads(sp.read_text()))
        snap_date = "not pinned"
        mf = SNAP / "manifest.json"
        if mf.exists():
            m = json.loads(mf.read_text())
            if m and m[0].get("fetched_at"):
                snap_date = m[0]["fetched_at"][:19]
        out.append("RISC-V ISA EXTENSIONS IN POPULAR OPEN-SOURCE SOFTWARE — "
                   "canonical results")
        out.append(f"corpus: n={len(snaps)} repos | snapshot date: {snap_date}")
        out.append("")
        out.append(f"{'repo':35s} {'files':>5s} {'groups':22s} key-extensions")
        for s in sorted(snaps, key=lambda x: x["repo"]):
            exts = set(s.get("exts") or [])
            groups = classify(exts)
            key = sorted(exts)
            # prefer interesting exts
            interesting = [e for e in key if e.startswith(("z", "x"))][:6]
            out.append(f"{s['repo']:35s} {s['n_files_scanned']:5d} "
                       f"{','.join(groups):22s} {','.join(interesting)}")
        out.append("")
        # ecosystem adoption
        n = len(snaps)
        def adopt(grp):
            k = sum(1 for s in snaps if grp in classify(set(s.get("exts") or [])))
            return k, n
        for grp in ("V", "Zb", "K", "MiscRatified", "Custom"):
            k, _ = adopt(grp)
            lo, hi = wilson_ci(k, n)
            out.append(f"adoption {grp:12s}: {k}/{n} ({k/n:.1%}, "
                       f"Wilson95 {lo:.1%}-{hi:.1%})")
        baseline_only = [s["repo"] for s in snaps
                         if not classify(set(s.get("exts") or []))]
        out.append(f"baseline-only (no extension groups): "
                   f"{len(baseline_only)}/{n} "
                   f"({', '.join(r.split('/')[-1] for r in baseline_only)})")
        out.append("")
        # domain analysis
        out.append("per-domain extension groups:")
        dom_groups = {}
        for s in snaps:
            dom = next((c.get("domain") for c in corpus
                        if c["repo"] == s["repo"]), "other")
            groups = tuple(classify(set(s.get("exts") or [])))
            dom_groups.setdefault(dom, set()).add(groups)
        for dom in sorted(dom_groups):
            gs = sorted(dom_groups[dom])
            out.append(f"  {dom:18s}: {gs}")
        out.append("")
        # cross-ISA (H3): per-ISA FILE coverage (files containing any per-ISA
        # marker) — comparable across ISAs (macro-occurrence density differs)
        out.append("cross-ISA per-ISA file coverage (files with any marker):")
        for s in snaps:
            x86_files = set()
            arm_files = set()
            rvv_files = set()
            for ch in ("X1_x86_macro", "X1_x86_header"):
                for toks in s["channel_hits"].get(ch, {}).values():
                    x86_files.update(toks)
            for ch in ("X2_arm_macro", "X2_arm_header"):
                for toks in s["channel_hits"].get(ch, {}).values():
                    arm_files.update(toks)
            for ch in ("C3_macro", "C4_intrinsics"):
                for toks in s["channel_hits"].get(ch, {}).values():
                    rvv_files.update(toks)
            if x86_files or arm_files or rvv_files:
                out.append(f"  {s['repo']:30s} scanned={s['n_files_scanned']:5d} "
                           f"x86={len(x86_files):4d} arm={len(arm_files):4d} "
                           f"rvv={len(rvv_files):4d}")
        out.append("")
        out.append("cross-ISA macro-occurrence counts (per-ISA marker uses):")
        for s in snaps:
            x86 = sum(len(v) for v in s["channel_hits"].get("X1_x86_macro", {}).values()) \
                + sum(len(v) for v in s["channel_hits"].get("X1_x86_header", {}).values())
            arm = sum(len(v) for v in s["channel_hits"].get("X2_arm_macro", {}).values()) \
                + sum(len(v) for v in s["channel_hits"].get("X2_arm_header", {}).values())
            rvv = sum(len(v) for v in s["channel_hits"].get("C3_macro", {}).values()) \
                + sum(len(v) for v in s["channel_hits"].get("C4_intrinsics", {}).values())
            if x86 or arm or rvv:
                out.append(f"  {s['repo']:30s} x86={x86:7d} arm={arm:7d} rvv={rvv:7d}")
        out.append("")
        out.append("canonical-run key: every number derives from "
                   "data_snapshot/ via deterministic classification.")
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "discovery_results.txt").write_text("\n".join(out) + "\n")
        print("\n".join(out))
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
