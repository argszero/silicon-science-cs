#!/usr/bin/env python3
"""Issue #41 — offline aggregation: QUIC census signals -> canonical output.

Reads snapshots/*_index.json (per-repo extracted feature/embedding signals,
fetch-pinned) and emits expected_output/discovery_results.txt
(byte-identical contract, mirrors #38).

Modes:
  offline/freeze : aggregate indexes -> expected_output/discovery_results.txt
  (freeze writes the canonical file; default prints)
"""
import json, glob, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
OUT = ROOT / "expected_output"

FEATURES = ["0rtt", "migration", "key_update", "pmtu", "multipath", "datagram", "ecn"]
STACKS = ["quiche", "quic-go", "quinn", "msquic", "ngtcp2", "aioquic", "lsquic",
          "mvfst", "neqo", "picoquic", "s2n-quic", "wtransport"]

def load_indexes():
    out = []
    for ix in sorted(glob.glob(str(SNAP / "*_index.json"))):
        d = json.load(open(ix))
        out.append(d)
    return out

def main():
    freeze = len(sys.argv) > 1 and sys.argv[1] == "freeze"
    rows = load_indexes()
    impls = [r for r in rows if r["tier"] == "implementation"]
    cons = [r for r in rows if r["tier"] == "consumer"]
    out = []
    out.append("QUIC CENSUS — issue #41 (canonical, offline)")
    out.append(f"corpus: {len(impls) + len(cons)} repos ({len(impls)} implementations + "
               f"{len(cons)} consumers), snapshot 2026-08-29 (GitHub tree API, pinned head SHAs)")
    out.append("")

    # ---- Tier A: feature coverage ----
    out.append("Tier A — feature coverage (implementation source files containing the marker):")
    hdr = f"{'repo':30s} {'src':>5s}  " + " ".join(f"{f:>9s}" for f in FEATURES)
    out.append(hdr)
    feat_totals = Counter()
    for r in impls:
        feats = r["features"]
        row = f"{r['repo']:30s} {r['source_files']:5d}  " + \
              " ".join(f"{feats.get(f, 0):9d}" for f in FEATURES)
        out.append(row)
        for f in FEATURES:
            if feats.get(f, 0) > 0:
                feat_totals[f] += 1
    out.append("")
    out.append("H2 feature adoption (stacks with ≥1 marker hit, of 12):")
    for f in FEATURES:
        out.append(f"  {f:12s} {feat_totals[f]:2d}/12  ({feat_totals[f]/len(impls):.0%})")
    out.append("")

    # ---- Tier B: embedding matrix ----
    out.append("Tier B — embedding matrix (consumer files matching stack, incl. manifests/vendor dirs):")
    out.append(f"{'repo':30s} " + " ".join(f"{s[:8]:>8s}" for s in STACKS))
    embed_totals = Counter()   # consumers embedding each stack
    embed_vol = Counter()      # total files matching each stack across consumers
    for r in cons:
        emb = r["embeddings"]
        out.append(f"{r['repo']:30s} " + " ".join(f"{emb.get(s, 0):8d}" for s in STACKS))
        for s in STACKS:
            if emb.get(s, 0) > 0:
                embed_totals[s] += 1
                embed_vol[s] += emb[s]
    out.append("")
    out.append(f"H1/H3 embedding concentration (consumers embedding each stack, of {len(cons)}):")
    for s in sorted(embed_totals, key=lambda k: -embed_totals[k]):
        out.append(f"  {s:12s} {embed_totals[s]:2d}/{len(cons)} consumers")
    out.append("")
    out.append("H1 embedding-file volume (consumer files matching each stack):")
    tot_vol = sum(embed_vol.values())
    for s in sorted(embed_vol, key=lambda k: -embed_vol[k]):
        out.append(f"  {s:12s} {embed_vol[s]:5d}  ({embed_vol[s]/tot_vol:.1%})")
    top1_vol = embed_vol.most_common(1)[0][1]
    out.append(f"  top-1 stack share of embedding-file volume: {top1_vol/tot_vol:.1%}")
    out.append("")

    # ---- self-implemented category (H3) ----
    out.append("H3 self-implemented category (no external stack embedding):")
    for r in cons:
        native = not r["embeddings"]
        out.append(f"  {r['repo']:30s} {'self-implemented' if native else 'embedded'}")
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
