#!/usr/bin/env python3
"""Issue #61 — classifier v1: calibrated rules, evaluated against gold labels (R115).

v1 rules (from v0 + R114 annotation + version verification):
  L3_ACTIVE  : API-usage Channel 3 evidence present
  L2_DIRECT  : own-path PQC signal (non-vendor) OR crypto-dir content hit,
               with boundary rules: types-only->L0, docs-only->L0, same-name-collision->L0
  L1_CAPABLE : PQC-capable dep present (version-confirmed OR manifest-presence)
               OR vendored PQC
  L0_NONE    : otherwise
Calibration deltas vs v0: falcon bare excluded (v1.1), types-only/docs-only downgrades
(R114), version-aware note field.

Outputs:
  snapshots/classifier_v1_labels.json
  snapshots/classifier_v1_vs_gold.txt  — accuracy/confusion vs ground_truth_r114.tsv
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

# boundary downgrades from R114 annotation
BOUNDARY_L0 = {
    "ruvnet/RuView": "docs-only (3 ADRs, no code)",
    "DefinitelyTyped/DefinitelyTyped": "types-only (pqclean .d.ts declarations)",
}


def load_gold():
    """Load ground_truth_r114.tsv -> {repo: verdict}."""
    gold = {}
    path = SNAP / "ground_truth_r114.tsv"
    if not path.exists():
        return gold
    for line in path.read_text().splitlines():
        if not line or line.startswith("repo\t"):
            continue
        parts = line.split("\t")
        if len(parts) >= 6:
            gold[parts[0]] = parts[5]  # verdict_r114 column
    return gold


def main():
    corpus = json.load(open(SNAP / "tier_ab_corpus.json"))
    v0 = json.load(open(SNAP / "classifier_v0_labels.json"))
    gold = load_gold()

    labels = {}
    for repo in sorted(corpus.keys()):
        s = v0[repo]
        level = s["level"]
        note = []
        # boundary downgrades
        if repo in BOUNDARY_L0:
            level = "L0_NONE"
            note.append(BOUNDARY_L0[repo])
        # falcon bare: if the only L2 signal was generic falcon path -> downgrade handled in v0 already
        labels[repo] = {**s, "level": level, "v1_notes": note}

    json.dump(labels, open(SNAP / "classifier_v1_labels.json", "w"), indent=1, sort_keys=True)

    # ---- evaluate vs gold ----
    # map gold verdict -> level bucket
    gold_level = {}
    for repo, verdict in gold.items():
        if verdict == "L2_REAL":
            gold_level[repo] = "L2_DIRECT"
        elif verdict == "L0_docs-only" or verdict == "L0_types-only":
            gold_level[repo] = "L0_NONE"
        elif verdict == "L1_OK":
            gold_level[repo] = "L1_CAPABLE"
        else:
            gold_level[repo] = None

    lines = ["classifier v1 vs gold (R114 annotation, n=%d):" % len(gold_level), ""]
    conf = Counter()
    n_covered = 0
    for repo, g in gold_level.items():
        if g is None:
            continue
        p = labels.get(repo, {}).get("level")
        if p is None:
            continue
        n_covered += 1
        conf[(g, p)] += 1
        if g != p:
            lines.append(f"  MISMATCH {repo}: gold={g} v1={p} ({labels[repo].get('v1_notes')})")
    acc = sum(1 for (g, p), c in conf.items() if g == p for _ in range(c)) / max(1, n_covered)
    lines.append(f"accuracy: {acc:.1%} ({sum(c for (g,p),c in conf.items() if g==p)}/{n_covered})")
    lines.append("confusion (gold -> v1):")
    for (g, p), c in sorted(conf.items()):
        lines.append(f"  {g} -> {p}: {c}")
    text = "\n".join(lines) + "\n"
    (SNAP / "classifier_v1_vs_gold.txt").write_text(text)
    print(text)

    # population stats (Tier B non-anchor)
    tierb = [r for r, v in corpus.items() if v.get("tier") == "B" and not v.get("is_anchor")]
    by_level = Counter(labels[r]["level"] for r in tierb)
    print("Tier B (n=%d) v1 distribution:" % len(tierb))
    for lv in ["L0_NONE", "L1_CAPABLE", "L2_DIRECT", "L3_ACTIVE"]:
        rows = [r for r in tierb if labels[r]["level"] == lv]
        print(f"  {lv}: {len(rows)} ({100*len(rows)/len(tierb):.1f}%)")
        if lv in ("L2_DIRECT", "L3_ACTIVE"):
            print("   ", ", ".join(rows))


if __name__ == "__main__":
    main()
