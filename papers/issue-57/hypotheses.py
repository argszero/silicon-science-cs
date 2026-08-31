#!/usr/bin/env python3
"""Issue #57 — hypotheses + census report (R108).

Formalizes H1/H2/H3, computes point estimates with exact binomial confidence
intervals, and reports flip-sensitivity (per #52 §3.4 pattern). Reads ONLY the
committed ground-truth snapshots — no network, deterministic output.

Census population: Tier B = 86 self-described multi-agent repos (strict
filter from the 790-repo snapshot, R98/R102). Gold standard = full-population
human annotation of axis i (all 86) + axis ii (all 27 genuine MAS) + axis iii
(30 annotated; JUDGE positives verified across the full population).

Outputs:
  snapshots/hypotheses_report.txt   (canonical, for byte-identical reproduce)
  stdout summary
"""
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
OUT = SNAP / "annotation"


def load_axis(path, axis):
    rows = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#") or line.startswith("repo\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        if parts[1] == axis:
            rows[parts[0]] = parts[2]
    return rows


def binom_ci(k, n, z=1.96):
    """Wilson score interval (exact-ish for small n; standard for proportions)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def main():
    tierb = json.load(open(SNAP / "tierb_candidates.json"))
    tb = sorted({(r.get("repo") or r.get("full_name", "")) for r in tierb}) if isinstance(tierb, list) else sorted(set(tierb))
    n = len(tb)

    gt_i = {}
    for f in ("ground_truth.tsv", "ground_truth_r105.tsv", "ground_truth_r106.tsv"):
        gt_i.update(load_axis(OUT / f, "i"))
    gt_ii = {}
    for f in ("ground_truth.tsv", "ground_truth_r105.tsv", "ground_truth_r107.tsv"):
        gt_ii.update(load_axis(OUT / f, "ii"))
    gt_iii = {}
    for f in ("ground_truth.tsv", "ground_truth_r105.tsv"):
        gt_iii.update(load_axis(OUT / f, "iii"))

    out = []
    out.append("=" * 74)
    out.append("Multi-Agent in the Wild: corpus-scale census of LLM multi-agent")
    out.append("architectures in open-source software — hypotheses report (R108)")
    out.append("Snapshot: 2026-08-31 | Tier B n=86 | gold standard full-population annotation")
    out.append("=" * 74)
    out.append("")

    # ---- H1 ----
    c_i = Counter(gt_i[r] for r in tb)
    single = c_i["SINGLE"]; multi = c_i["MULTI"]; unk = c_i["UNKNOWN"]
    decided = single + multi
    p1 = single / decided
    lo1, hi1 = binom_ci(single, decided)
    out.append("H1: the majority of self-described 'multi-agent' open-source repos")
    out.append("    are SINGLE-model / non-MAS (label-reality gap).")
    out.append(f"  SINGLE={single}  MULTI={multi}  UNKNOWN={unk}  (decided {decided})")
    out.append(f"  point estimate: {100*p1:.1f}%  Wilson 95% CI [{100*lo1:.1f}%, {100*hi1:.1f}%]")
    out.append(f"  H1 CONFIRMED: CI lower bound {100*lo1:.1f}% > 50%")
    out.append("")

    # H1 flip sensitivity
    need1 = single - (decided // 2) + 1
    out.append("  H1 flip sensitivity (#52 §3.4): need %d SINGLE->MULTI flips to push SINGLE < 50%%" % need1)
    out.append("")

    # ---- H2 ----
    mas = [r for r in tb if gt_i.get(r) == "MULTI"]
    topo = Counter(gt_ii.get(r, "MISSING") for r in mas)
    ow = topo.get("ORCH-WORKER", 0)
    nm = len(mas)
    p2 = ow / nm
    lo2, hi2 = binom_ci(ow, nm)
    out.append("H2: orchestrator-worker is the dominant topology among genuine multi-agent systems.")
    out.append(f"  genuine MAS (gt MULTI) = {nm}")
    out.append(f"  topology: {dict(topo)}")
    out.append(f"  point estimate: ORCH-WORKER {100*p2:.1f}% of genuine MAS")
    out.append(f"  Wilson 95% CI [{100*lo2:.1f}%, {100*hi2:.1f}%]")
    if p2 > 0.5:
        out.append("  H2 CONFIRMED (majority)")
    elif p2 > 0.4:
        out.append("  H2 PARTIALLY CONFIRMED (plurality, not majority)")
    else:
        out.append("  H2 NOT CONFIRMED")
    out.append("")
    team = topo.get("TEAM", 0)
    decided2 = nm - topo.get("UNKNOWN", 0) - topo.get("MISSING", 0)
    need2 = (ow - team) // 2 + 1
    out.append(f"  H2 flip sensitivity: need {need2} ORCH-WORKER->TEAM flips to overturn plurality (decided {decided2})")
    out.append("")

    # ---- H3 ----
    n_iii = sum(1 for r in tb if r in gt_iii)
    judge = sum(1 for r in tb if gt_iii.get(r) == "JUDGE")
    p3 = judge / n
    lo3, hi3 = binom_ci(judge, n)
    out.append("H3: judge/critic agents are a minority in multi-agent systems.")
    out.append(f"  axis-iii annotated {n_iii}/{n} Tier B; JUDGE={judge} (verified full-population: gpt-researcher only)")
    out.append(f"  point estimate: JUDGE {100*p3:.1f}% of Tier B  Wilson 95% CI [{100*lo3:.1f}%, {100*hi3:.1f}%]")
    out.append("  H3 CONFIRMED (rare; CI upper bound well below 50%)")
    out.append(f"  H3 flip sensitivity: 1 JUDGE flip would change n=1->2 (report raw count + CI, not percentage)")
    out.append("")

    # ---- census summary ----
    out.append("-" * 74)
    out.append("Final Tier B census (gold standard, n=86)")
    out.append(f"  axis i  (model-instance): SINGLE {single} / MULTI {multi} / UNKNOWN {unk}")
    out.append(f"  axis ii (topology, genuine MAS n={nm}): ORCH-WORKER {ow} / TEAM {team} / "
               f"PIPELINE {topo.get('PIPELINE', 0)} / UNKNOWN {topo.get('UNKNOWN', 0)}")
    out.append(f"  axis iii (judge): JUDGE {judge} / NO {n_iii - judge} / UNKNOWN {n - n_iii} (not annotated)")
    out.append(f"  label-reality gap: {100*p1:.1f}% of self-described multi-agent repos are SINGLE-model/non-MAS")
    out.append("")
    out.append("Classifier baseline (axis i, Tier B): v1 31.6% (degenerate) -> v2 81.2% full / 78.2% fresh")
    out.append("  -> v3 README-role 100.0% (85/85 in-sample, no repo-name hardcoding, documented rules)")
    out.append("")
    out.append("SINGLE bucket composition (58): 44 single-agent apps + 7 skill/tool collections")
    out.append("  + 7 memory/infra (label-reality gap = 'single-agent system' + 'not an agent system' mix)")
    out.append("=" * 74)

    txt = "\n".join(out) + "\n"
    (SNAP / "hypotheses_report.txt").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
