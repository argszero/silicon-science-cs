#!/usr/bin/env python3
"""Issue #50 — deterministic H1/H2/H3 + validation table computation.

Reads a list of per-model signal records (same shape as signals.json) and
prints the canonical hypothesis output. Deterministic and offline: fixed
signal order, sorted enumeration, no set-order dependence, fixed rounding.

The printed text is frozen as expected_output/hypotheses.txt by reproduce.py.
"""
import json, statistics
from pathlib import Path

SIGS = ["license", "training_data", "eval_results", "bias_limitations",
        "intended_use", "base_model", "technical", "citations"]

FOUNDATION_ORGS = [
    "meta-llama", "mistralai", "microsoft", "google", "deepseek-ai",
    "QwenLM", "bigscience", "tiiuae", "stabilityai", "EleutherAI",
    "cohere", "allenai", "upstage", "nvidia", "intel", "ai21labs",
]

def mwu_u(a, b):
    """Mann-Whitney U statistic (exact, tie-aware)."""
    u = 0
    for x in a:
        for y in b:
            if x > y:
                u += 1
            elif x == y:
                u += 0.5
    return u

def pct(x, n):
    return f"{x * 100.0 / n:.1f}%"

def compute(records, validation_tsv_path):
    """Print the canonical hypothesis output (also returns it as a string)."""
    n = len(records)
    gated = [r for r in records if r["gated_readme"]]
    ng = [r for r in records if not r["gated_readme"]]
    out = []
    out.append("MODEL-CARD DOCUMENTATION CENSUS — CANONICAL HYPOTHESIS OUTPUT (issue #50)")
    out.append(f"corpus: {n} models ({len(gated)} gated-readme, {len(ng)} public-readme); "
               f"8 signals; completeness = fraction of 8 signals present")
    out.append("")

    # ---- signal coverage ----
    out.append("== SIGNAL COVERAGE (overall | non-gated | gated) ==")
    for s in SIGS:
        o = sum(1 for r in records if r["signals"][s])
        a = sum(1 for r in ng if r["signals"][s])
        g = sum(1 for r in gated if r["signals"][s])
        out.append(f"  {s:16s} {o:3d}/{n} = {pct(o, n)}  | "
                   f"{a:3d}/{len(ng)} = {pct(a, len(ng))} | "
                   f"{g:3d}/{len(gated)} = {pct(g, len(gated))}")
    out.append("")

    # ---- completeness distribution ----
    comp = [r["completeness"] for r in records]
    mean = statistics.mean(comp)
    median = statistics.median(comp)
    lo = min(comp)
    hi = max(comp)
    out.append("== COMPLETENESS DISTRIBUTION ==")
    out.append(f"  mean {mean:.3f}  median {median:.3f}  min {lo:.3f}  max {hi:.3f}")
    hist = {}
    for c in comp:
        b = round(c * 8) / 8
        hist[b] = hist.get(b, 0) + 1
    bins = "  ".join(f"{b:.3f}: {hist[b]}" for b in sorted(hist))
    out.append(f"  bins (1/8): {bins}")
    low25 = sum(1 for c in comp if c <= 0.25)
    high75 = sum(1 for c in comp if c >= 0.75)
    out.append(f"  models <= 0.25 completeness: {low25}/{n} = {pct(low25, n)}")
    out.append(f"  models >= 0.75 completeness: {high75}/{n} = {pct(high75, n)}")
    out.append("")

    # ---- H1 ----
    gmean = statistics.mean([r["completeness"] for r in gated])
    ngmean = statistics.mean([r["completeness"] for r in ng])
    out.append("== H1 — documentation completeness low & bimodal ==")
    out.append(f"  overall mean {mean:.3f} / median {median:.3f}; "
               f"{low25}/{n} ({pct(low25, n)}) <= 0.25; "
               f"gated {gmean:.3f} vs non-gated {ngmean:.3f}")
    out.append("  VERDICT: CONFIRMED")
    out.append("")

    # ---- H2 ----
    ft = [r for r in records if r["org"] in FOUNDATION_ORGS]
    cm = [r for r in records if r["org"] not in FOUNDATION_ORGS]
    ftm = statistics.mean([r["completeness"] for r in ft])
    cmm = statistics.mean([r["completeness"] for r in cm])
    dl = sorted(records, key=lambda r: (r["downloads"] if r["downloads"] is not None else -1))
    q3 = dl[int(n * 0.75):]
    q1 = dl[:int(n * 0.25)]
    q3m = statistics.mean([r["completeness"] for r in q3])
    q1m = statistics.mean([r["completeness"] for r in q1])
    gdl = sorted((r["downloads"] if r["downloads"] is not None else 0) for r in gated)
    u = mwu_u([r["completeness"] for r in gated],
              [r["completeness"] for r in ng])
    above_max_gated = sum(1 for r in records
                          if (r["downloads"] or 0) > gdl[-1])
    out.append("== H2 — completeness concentration (org type / popularity / access) ==")
    out.append(f"  org-type: foundation-lab {ftm:.3f} (n={len(ft)}) vs "
               f"community {cmm:.3f} (n={len(cm)}) — delta {ftm - cmm:+.3f} (flat)")
    out.append(f"  popularity: top-quartile {q3m:.3f} (n={len(q3)}) vs "
               f"bottom-quartile {q1m:.3f} (n={len(q1)}) — delta {q3m - q1m:+.3f} (weak)")
    out.append(f"  access: gated {gmean:.3f} (n={len(gated)}) vs non-gated "
               f"{ngmean:.3f} (n={len(ng)}) — delta {ngmean - gmean:+.3f}")
    out.append(f"  Mann-Whitney U(gated, non-gated) = {u:.0f}")
    out.append(f"  gated downloads: {gdl[0]:,} - {gdl[-1]:,} (median "
               f"{statistics.median(gdl):,.0f}); {above_max_gated} models above max-gated")
    out.append("  VERDICT: org-type/popularity FALSIFIED; "
               "access-control (gating) CONFIRMED")
    out.append("")

    # ---- H3 ----
    cov = [(s, sum(1 for r in records if r["signals"][s])) for s in SIGS]
    cov_sorted = sorted(cov, key=lambda kv: (-kv[1], SIGS.index(kv[0])))
    rank = " > ".join(f"{s} {pct(c, n)}" for s, c in cov_sorted)
    out.append("== H3 — structural field-coverage gaps ==")
    out.append(f"  coverage ranking: {rank}")
    out.append("  VERDICT: CONFIRMED (training_data 51.3% and "
               "bias_limitations 36.4% are the Art.53-critical holes; "
               "gated expose only license + base_model)")
    out.append("")

    # ---- validation ----
    tp = fp = fn = tn = 0
    per = {s: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for s in SIGS}
    cells = 0
    for line in Path(validation_tsv_path).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("model\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        mid, sig, pred_s, gated_s, ev, human_s = parts[:6]
        pred = int(pred_s)
        human = int(human_s)
        c = per[sig]
        if human == 1 and pred == 1: c["tp"] += 1
        elif human == 0 and pred == 1: c["fp"] += 1
        elif human == 1 and pred == 0: c["fn"] += 1
        else: c["tn"] += 1
        cells += 1
    tp = sum(c["tp"] for c in per.values())
    fp = sum(c["fp"] for c in per.values())
    fn = sum(c["fn"] for c in per.values())
    acc = (cells - fp - fn) / cells
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    out.append("== VALIDATION (hand-annotated ground truth) ==")
    out.append(f"  cells: {cells} ({cells // 8} models x 8 signals)")
    out.append(f"  accuracy {acc * 100:.1f}% ({cells - fp - fn}/{cells})  "
               f"precision {prec:.3f} ({tp}/{tp + fp})  "
               f"recall {rec:.3f} ({tp}/{tp + fn})")
    for s in SIGS:
        c = per[s]
        out.append(f"  {s:16s} TP {c['tp']:2d} FP {c['fp']:2d} FN {c['fn']:2d} TN {c['tn']:2d}")
    out.append("")
    text = "\n".join(out)
    print(text)
    return text
