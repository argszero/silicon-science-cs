#!/usr/bin/env python3
"""Issue #38 — offline aggregation: extraction indexes -> canonical output.

Reads snapshots/*_index.json (per-repo extracted program sources with SEC/helper/
map/feature signals, fetch-pinned) and emits expected_output/discovery_results.txt
(byte-identical contract).

Modes:
  offline : aggregate indexes -> expected_output/discovery_results.txt
"""
import json, glob, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
OUT = ROOT / "expected_output"

def load_indexes():
    """Load all repo indexes, return list of (repo, head_sha, progs)."""
    out = []
    for ix in sorted(glob.glob(str(SNAP / "*_index.json"))):
        d = json.load(open(ix))
        progs = [r for r in d["files"] if r["is_bpf_source"]]
        out.append((d["repo"], d.get("head_sha", "?"), progs))
    return out

def main():
    freeze = len(sys.argv) > 1 and sys.argv[1] == "freeze"
    indexes = load_indexes()
    out = []
    out.append("EBPF PROGRAM CENSUS — issue #38 (canonical, offline)")
    out.append(f"corpus: {len(indexes)} repos, snapshot 2026-08-28 (GitHub tree API, pinned head SHAs)")
    out.append("")
    # ---- per-repo program counts ----
    out.append("per-repo program sources:")
    total_progs = 0
    for repo, sha, progs in indexes:
        total_progs += len(progs)
        out.append(f"  {repo:42s} {len(progs):5d}  head={sha[:8]}")
    out.append(f"  TOTAL: {total_progs} BPF program sources")
    out.append("")
    # ---- SEC-instance census ----
    sec_all = Counter()
    for _, _, progs in indexes:
        for r in progs:
            sec_all.update(r.get("sec", {}))
    out.append(f"SEC-instance census ({sum(sec_all.values())} instances, excl license/version/.maps):")
    for k, v in sec_all.most_common():
        out.append(f"  {k:16s} {v:5d}  ({v/sum(sec_all.values()):.1%})")
    top3 = sum(v for k, v in sec_all.most_common(3))
    top4 = sum(v for k, v in sec_all.most_common(4))
    s3 = sum(sec_all.values())
    out.append(f"H1 concentration: top-3 families (tracing+socket+TC) {top3}/{s3} = {top3/s3:.1%}; "
               f"top-4 (incl. other) {top4}/{s3} = {top4/s3:.1%}")
    out.append("")
    # ---- helper census: artifact-filtered (broad) ----
    ARTIFACTS = {"bpf_misc","bpf_dynptr","bpf_map","bpf_sock","bpf_sock_addr","bpf_sock_tuple",
                 "bpf_list_node","bpf_list_head","bpf_rb_root","bpf_rb_node","bpf_refcount",
                 "bpf_experimental","bpf_tracing","bpf_helpers","bpf_helper_defs","bpf_core_read",
                 "bpf_endian","bpf_compiler","bpf_pseudo","bpf_arena","bpf_skb","bpf_sk_lookup",
                 "bpf_testmod","bpf_iter","bpf_hash","bpf_lpm","bpf_local_storage","bpf_xdp",
                 "bpf_prog","bpf_attach","bpf_link","bpf_object","bpf_program","bpf_insn",
                 "bpf_verifier","bpf_func","bpf_ctx","bpf_args","bpf_task","bpf_cgroup",
                 "bpf_kptr","bpf_ringbuf","bpf_perf","bpf_timer","bpf_spin","bpf_htons","bpf_htonl",
                 "bpf_ntohs","bpf_ntohl","bpf_get_prandom_u32"}
    helpers = Counter()
    for _, _, progs in indexes:
        for r in progs:
            for k, v in r.get("helpers", {}).items():
                if k not in ARTIFACTS:
                    helpers[k] += v
    out.append(f"helper-call census (broad, artifact-filtered): {sum(helpers.values())} calls, "
               f"{len(helpers)} distinct callable names")
    b10 = sum(v for _, v in helpers.most_common(10))
    b20 = sum(v for _, v in helpers.most_common(20))
    out.append(f"  broad concentration: top-10 {b10/sum(helpers.values()):.1%} | "
               f"top-20 {b20/sum(helpers.values()):.1%} (naive name-level baseline)")
    for k, v in helpers.most_common(10):
        out.append(f"  {k:32s} {v:5d}")
    out.append("")
    # ---- helper census: canonical kernel helpers only (from committed list) ----
    enum = set()
    kf = ROOT / "kernel_helpers.txt"
    if kf.exists():
        enum = set(l.strip() for l in open(kf) if l.strip())
    canon = Counter()
    for _, _, progs in indexes:
        for r in progs:
            for k, v in r.get("helpers", {}).items():
                name = k[len("bpf_"):] if k.startswith("bpf_") else k
                if name in enum:
                    canon[k] += v
    ctot = sum(canon.values())
    out.append(f"helper-call census (canonical kernel helpers only): {ctot} calls, "
               f"{len(canon)} distinct of {len(enum)} canonical helpers")
    top10 = sum(v for _, v in canon.most_common(10))
    top20 = sum(v for _, v in canon.most_common(20))
    top50 = sum(v for _, v in canon.most_common(50))
    out.append(f"  concentration: top-10 {top10/ctot:.1%} | top-20 {top20/ctot:.1%} | top-50 {top50/ctot:.1%}")
    for k, v in canon.most_common(15):
        out.append(f"  {k:32s} {v:5d}  ({v/ctot:.1%})")
    out.append("")
    # ---- feature adoption ----
    feat = Counter()
    for _, _, progs in indexes:
        for r in progs:
            for k, v in r.get("features", {}).items():
                if v:
                    feat[k] += 1
    out.append(f"verifier-feature adoption (of {total_progs} program sources):")
    for k, v in feat.most_common():
        out.append(f"  {k:16s} {v:5d} files  ({v/total_progs:.1%})")
    out.append("")
    # ---- feature adoption by ecosystem (H3): kernel tree vs production repos ----
    kern = [r for repo, _, progs in indexes if repo == "torvalds/linux" for r in progs]
    prod = [r for repo, _, progs in indexes if repo != "torvalds/linux" for r in progs]
    out.append(f"feature adoption by ecosystem (kernel {len(kern)} vs production {len(prod)} program sources):")
    allf = sorted({k for r in (kern + prod) for k, v in r.get("features", {}).items() if v})
    out.append(f"  {'feature':16s} {'kernel':>12s} {'prod':>12s}")
    for k in allf:
        kc = sum(1 for r in kern if r.get("features", {}).get(k))
        pc = sum(1 for r in prod if r.get("features", {}).get(k))
        out.append(f"  {k:16s} {kc/len(kern):>10.1%} {pc/len(prod):>10.1%}")
    out.append("")
    out.append("canonical-run key: every number derives from snapshots/*_index.json "
               "via deterministic offline aggregation.")
    if freeze:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "discovery_results.txt").write_text("\n".join(out) + "\n")
        print(f"frozen -> {OUT / 'discovery_results.txt'}")
    else:
        print("\n".join(out))

if __name__ == "__main__":
    main()
