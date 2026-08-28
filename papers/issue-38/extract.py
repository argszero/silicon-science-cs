#!/usr/bin/env python3
"""Issue #38 — eBPF census extraction pipeline (snapshot-cached).

For each corpus repo: enumerate candidate BPF program source paths, fetch raw
sources (cached under snapshots/<repo>/), and extract per-file signals:
  - SEC("...") program-type prefixes
  - bpf_* helper calls (frequency)
  - BPF_MAP_TYPE_* map definitions
  - verifier features: bounded loops, tail calls, BPF-to-BPF calls, ringbuf

Usage:
  python3 extract.py <repo> <path-spec...> [--prefix P]  # e.g. --prefix a  (resumable batches)
  python3 extract.py <repo> <path> --prefix a
"""
import base64, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

def gh(endpoint, timeout=60):
    r = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"gh api {endpoint} failed: {r.stderr[:200]}")
    return json.loads(r.stdout)

def tree_files(repo, branch, path):
    """List blob paths under repo:path (one level)."""
    try:
        data = gh(f"repos/{repo}/git/trees/{branch}:{path}")
    except RuntimeError:
        return []
    return [t["path"] for t in data.get("tree", []) if t["type"] == "blob"]

def fetch_raw(repo, branch, path):
    """Fetch raw file content via contents API (base64), cached."""
    cache = SNAP / repo.replace("/", "__") / path
    if cache.exists():
        return cache.read_text(errors="replace")
    try:
        data = gh(f"repos/{repo}/contents/{path}?ref={branch}")["content"]
    except RuntimeError as e:
        if "404" in str(e):
            return None
        raise
    try:
        content = base64.b64decode(data).decode("utf-8", errors="replace")
    except Exception:
        return None
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(content)
    return content

# SEC prefix -> program-type family
SEC_TYPES = {
    "xdp": "XDP", "xdp.frags": "XDP",
    "tc": "TC", "tc/ingress": "TC", "tc/egress": "TC", "classifier": "TC", "action": "TC",
    "sched_cls": "TC", "sched_act": "TC",
    "kprobe": "kprobe", "kretprobe": "kprobe", "kprobe.multi": "kprobe", "kretprobe.multi": "kprobe",
    "fentry": "tracing", "fexit": "tracing", "fmod_ret": "tracing",
    "tracepoint": "tracing", "raw_tracepoint": "tracing", "raw_tp": "tracing",
    "tp_btf": "tracing", "perf_event": "perf_event",
    "socket": "socket", "sk_msg": "sk_msg", "sk_skb": "sockops", "sockops": "sockops",
    "cgroup_skb": "cgroup", "cgroup_sock": "cgroup", "cgroup_sock_addr": "cgroup",
    "cgroup/skb": "cgroup", "cgroup/sock": "cgroup", "cgroup/sock_addr": "cgroup",
    "cgroup/connect4": "cgroup", "cgroup/connect6": "cgroup", "cgroup/sendmsg4": "cgroup",
    "cgroup/getsockopt": "cgroup", "cgroup/setsockopt": "cgroup",
    "lsm": "lsm", "struct_ops": "struct_ops", "iter": "iter", "fentry.s": "tracing",
}

def sec_types(text):
    types = {}
    for m in re.finditer(r'SEC\s*\(\s*"([^"]+)"\s*\)', text):
        sec = m.group(1)
        if sec == "license" or sec.startswith("version") or sec == ".maps" or sec.startswith(".maps/"):
            continue
        # kernel '?' prefix = optional/disabled program (convention), strip for family
        stripped = sec.lstrip("?")
        fam = "other"
        for k, v in SEC_TYPES.items():
            if stripped == k or stripped.startswith(k + "/") or stripped.startswith(k + "."):
                fam = v
                break
        # dot-variants not covered by exact keys
        if fam == "other":
            for k, v in [("kprobe", "kprobe"), ("kretprobe", "kprobe"), ("fentry", "tracing"),
                         ("fexit", "tracing"), ("fmod_ret", "tracing"), ("lsm", "lsm"),
                         ("uprobe", "uprobe"), ("uretprobe", "uprobe"), ("raw_tp", "tracing"),
                         ("tp_btf", "tracing"), ("raw_tracepoint", "tracing"),
                         (".struct_ops", "struct_ops")]:
                if stripped.startswith(k + "."):
                    fam = v
                    break
        # standalone names: syscall, sk_lookup, flow_dissector, netfilter, freplace, usdt, ...
        if fam == "other":
            for k, v in [("syscall", "syscall"), ("sk_lookup", "socket"), ("sk_reuseport", "socket"),
                         ("flow_dissector", "flow_dissector"), ("netfilter", "netfilter"),
                         ("freplace", "tracing"), ("usdt", "uprobe"), ("uprobe", "uprobe"),
                         ("tp/", "tracing"), ("tp/btf", "tracing"), ("sk_skb", "sockops")]:
                if stripped == k or stripped.startswith(k):
                    fam = v
                    break
        types.setdefault(fam, 0)
        types[fam] += 1
    return types

# context-type -> program family (fallback when SEC names are custom, old-style)
CTX_TYPES = {
    "struct xdp_md": "XDP", "struct xdp_buff": "XDP", "xdp_md": "XDP",
    "struct __sk_buff": "TC", "struct sk_buff": "TC", "__sk_buff": "TC",
    "struct pt_regs": "kprobe", "pt_regs": "kprobe",
    "struct bpf_sock": "socket", "struct bpf_sock_addr": "sockops",
    "struct bpf_sock_ops": "sockops", "struct bpf_skb": "socket",
    "struct bpf_cgroup_dev_ctx": "cgroup", "struct bpf_perf_event_data": "perf_event",
}

def infer_ctx_family(text):
    """Best-guess program family from first-arg context types of top-level funcs."""
    fams = []
    # find function definitions with SEC-like context args:  <ret> <name>(struct ... *ctx)
    for m in re.finditer(r'\([^)]*?(struct\s+\w+)\s*[*&]\s*\w+\s*\)', text):
        ctx = m.group(1).strip()
        for k, v in CTX_TYPES.items():
            if ctx == k or ctx.endswith(k):
                fams.append(v)
                break
    return fams

# cilium-style: __section_entry (compile-time PROG_TYPE/entry) + ctx header include
CILIUM_CTX_FAM = {
    "bpf/ctx/skb.h": "TC", "bpf/ctx/xdp.h": "XDP", "bpf/ctx/sock.h": "socket",
    "bpf/ctx/sockaddr.h": "cgroup", "bpf/ctx/trace.h": "tracing",
    "bpf/ctx/url.h": "other", "bpf/ctx/unspec.h": "other",
}

def cilium_signals(text):
    """Return (has_entry_marker, ctx_family) for cilium-style programs."""
    has_entry = "__section_entry" in text
    fam = None
    for inc in re.finditer(r'#\s*include\s*[<"]([^>"]*ctx[^>"]*)[>"]', text):
        inc_name = inc.group(1)
        if inc_name in CILIUM_CTX_FAM:
            fam = CILIUM_CTX_FAM[inc_name]
            break
    return has_entry, fam

def helpers(text):
    h = {}
    for m in re.finditer(r'\bbpf_[a-z_0-9]+', text):
        name = m.group(0)
        if name in ("bpf_helpers", "bpf_helper_defs", "bpf_core_read", "bpf_tracing",
                    "bpf_endian", "bpf_compiler", "bpf_pseudo"):
            continue
        h[name] = h.get(name, 0) + 1
    return h

def map_types(text):
    m = {}
    for mt in re.finditer(r'BPF_MAP_TYPE_[A-Z_0-9]+', text):
        m[mt.group(0)] = m.get(mt.group(0), 0) + 1
    return m

def features(text):
    f = {}
    f["bounded_loops"] = len(re.findall(r'#pragma\s+unroll|#pragma\s+clang\s+loop', text)) or \
                         ("for (" in text and "__nr_loops" in text)
    f["tail_calls"] = text.count("bpf_tail_call")
    f["bpf2bpf"] = text.count("__noinline") + text.count("__always_inline")
    f["ringbuf"] = len(re.findall(r'bpf_ringbuf_(output|reserve|submit|discard|query|discard_dynptr|reserve_dynptr)', text))
    f["perfbuf"] = len(re.findall(r'bpf_perf_event_output', text))
    f["arena"] = len(re.findall(r'bpf_arena_alloc|bpf_arena_free|__arena', text))
    return f

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    repo = sys.argv[1]
    prefix = None
    paths = sys.argv[2:]
    if "--prefix" in paths:
        i = paths.index("--prefix")
        prefix = paths[i + 1]
        paths = paths[:i]
    corpus = json.load(open(ROOT / "corpus.json"))
    meta = next((r for r in corpus["repos"] if r["repo"] == repo), None)
    if not meta:
        print(f"repo {repo} not in corpus.json"); sys.exit(1)
    branch = meta["default_branch"]

    results = []
    for p in paths:
        files = tree_files(repo, branch, p)
        print(f"{repo}:{p}: {len(files)} blobs")
        if prefix:
            files = [f for f in files if f.lower().startswith(prefix.lower())]
            print(f"  prefix '{prefix}': {len(files)} files")
        for f in files:
            if not f.endswith((".c", ".h")):
                continue
            text = fetch_raw(repo, branch, f"{p}/{f}")
            if not text:
                continue
            # candidate BPF program source: .bpf.c / _kern.c with SEC, or SEC-bearing
            # program source (exclude _user.c loaders, .h headers, non-program C)
            is_loader = "_user." in f or f.endswith("_user.c") or f.endswith("_user.h")
            sec = sec_types(text)
            ctx = infer_ctx_family(text)
            cilium_entry, cilium_fam = cilium_signals(text)
            # directory-context rule (kernel build system ground truth): every .c under
            # tools/testing/selftests/bpf/progs/ is compiled as a BPF program — catches
            # wrapper files (profiler3.c -> profiler.inc.h) with no local SEC signal
            dir_is_progs = "selftests/bpf/progs/" in f"{p}/{f}"
            named_prog = ".bpf.c" in f or "_kern.c" in f
            is_prog = (not is_loader) and (dir_is_progs or cilium_entry or named_prog or
                                           bool(sec) or "BPF_PROG_TYPE" in text or
                                           "BPF_PROG_LOAD" in text or "bpf_prog" in text.lower())
            # guard: signal-free detection only counts when backed by naming/dir convention
            if is_prog and not sec and not ctx and not dir_is_progs and not cilium_entry and not named_prog:
                is_prog = False
            rec = {
                "repo": repo, "path": f"{p}/{f}", "bytes": len(text),
                "is_bpf_source": is_prog,
                "sec": sec, "ctx_families": ctx, "cilium_entry": cilium_entry, "cilium_fam": cilium_fam,
                "helpers": helpers(text),
                "maps": map_types(text), "features": features(text),
            }
            results.append(rec)
            if is_prog:
                fams = "/".join(sorted(rec["sec"].keys())) or "no-sec"
                cxf = ("ctx:" + "/".join(sorted(set(ctx)))) if ctx else ""
                print(f"  prog {f}: {len(text)}B SEC[{fams}] {cxf} helpers={len(rec['helpers'])}")

    out = SNAP / (repo.replace("/", "__") + "_index.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    # merge with previously indexed files (resumable batch runs)
    existing = {}
    if out.exists():
        prev = json.load(open(out))
        existing = {r["path"]: r for r in prev.get("files", [])}
    for r in results:
        existing[r["path"]] = r
    merged = sorted(existing.values(), key=lambda r: r["path"])
    json.dump({"repo": repo, "branch": branch, "head_sha": meta["head_sha"],
               "files": merged}, open(out, "w"), indent=1)
    progs = [r for r in merged if r["is_bpf_source"]]
    print(f"saved {out.name}: {len(merged)} files, {len(progs)} BPF program sources")

if __name__ == "__main__":
    main()
