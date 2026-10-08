#!/usr/bin/env python3
"""spike_v7 -- the THIRD OPERATOR on the fusion: does the composition story survive the character ladder?

R571 measured the fusion at the DECISION level under ONE operator (token substitution -- spike_v4's design
commitment: a fused rule mixes members, so a single edit ladder per cell). The next step it named was a
third operator, with a prediction recorded in notes.md:

    "under a CHARACTER edit `dice2c` is the robust member, so which one is brittle should swap".

This script tests that, and -- more usefully -- separates the fusion into its TWO ARMS, because they have
different operator dependence:

  * the CALIBRATION arm (the joint null: tau, the marginal FPRs, the indicator covariance, the
    excess = +-Cov identity, the floor absorption).  Its objects are UNPERTURBED pairs, so the edit
    operator cannot enter them.  It is stated STRUCTURALLY, and the certificate only checks that the pools
    this script uses ARE spike_v4's pools (a reproduction, not a re-derivation).
  * the BOUNDARY arm (the recall ladder and the eps* transfer: which member's boundary OR recovers and
    which one AND inherits).  Its objects are PERTURBED pairs, so the operator enters completely -- and a
    character edit is a different instrument from a token edit (spike_v3: 2-20x at the same nominal rate).

Certificates (each able to fail):
  X1 pool reproduction   this script's recomputed tau equals spike_v4's certified artefact, per (L, stat).
                         If it does not, the two scripts are not measuring the same object and no
                         cross-operator claim is admissible.
  X2 composition bounds  R_or >= max(R_a, R_b) and R_and <= min(R_a, R_b) at EVERY eps, under BOTH
                         operators (a union/intersection bound: it must hold for any operator).
  X3 eps* transfer       eps*(OR) >= max(member eps*) and eps*(AND) <= min(member eps*), both operators.
  X4 no operator leak    the calibration arm is recorded as STRUCTURALLY operator-free, and explicitly NOT
                         reported as a measurement (the null is unperturbed; "certifying" it would be the
                         Class 171 tautology).

Real text only (Project Gutenberg, pinned in corpus/SHA256SUMS).  Ground truth by construction.
"""
import hashlib
import io
import json
import math
import os
import random
from collections import Counter
from itertools import combinations

import spike_v0 as s0
import spike_v2 as s2
import spike_v3 as s3
import spike_v4 as s4

STATS = s4.STATS
PAIRS = [tuple(p) for p in combinations(STATS, 2)]
RULES = s4.RULES
LGRID = s4.LGRID
EPS = s4.EPS
N_NULL, N_FRESH, N_REFS = s4.N_NULL, s4.N_FRESH, s4.N_REFS


def chr_perturb(toks, eps, rng):
    return s3.pert_chr(" ".join(toks), eps, rng).split()


def same(a, b):
    """The eps-grid interpolation is piecewise linear, so 'recovered' means equal to within the local
    grid step. A global tolerance hides the near-tie cells, which are exactly the informative ones."""
    if a is None or b is None:
        return "n/a"
    d = abs(a - b)
    return "exact" if d <= 1e-9 else ("close" if d <= 0.02 else "apart")


def main():
    books = s0.load_books()
    cnt = Counter(w for _, ws in books for w in ws)
    vocab = [w for w, _ in cnt.most_common(20000)]
    df = Counter()
    for _, ws in books:
        df.update(set(ws))
    N = len(books)
    idf = {w: math.log((N + 1) / (df[w] + 1)) + 1.0 for w in cnt}

    stored = {}
    sp4 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spike_v4_results.json")
    # HARD PREREQUISITE, not a soft one: X1 (this script's pools ARE spike_v4's pools) is only assertable
    # against spike_v4's own artefact.  A soft `if stored:` would silently drop X1 and emit a DIFFERENT
    # artefact when the file were missing -- a certificate whose subject is absent reports nothing, while
    # still looking like a clean run (Class 205(c)).  repro_check runs spike_v4 before spike_v7.
    assert os.path.exists(sp4), (
        "spike_v4_results.json is required: spike_v7 asserts its pools ARE spike_v4's (X1). Run spike_v4 "
        "first, or via repro_check.py which orders the family correctly.")
    stored = json.load(io.open(sp4, encoding="utf-8"))

    out = {"stats": STATS, "pairs": [list(p) for p in PAIRS], "rules": RULES, "L_grid": LGRID,
           "eps_grid": EPS, "operators": ["tok", "chr"], "n_refs": N_REFS,
           "note": ("calibration arm reused from spike_v4 (the null is unperturbed); boundary arm measured "
                    "under both operators"),
           "calibration": {}, "recall": {}, "eps_star": {}, "transfer": {}, "certificates": {}}

    recall = {}
    for L in LGRID:
        # --- pool construction replicated from spike_v4, seed for seed, so tau is the SAME object ----
        rng = random.Random(s0.SEED0 + L * 104729)
        need = (N_NULL + N_FRESH) * 2 + N_REFS
        segs = []
        for i in range(need):
            _bk, ws = books[i % len(books)]
            off = rng.randrange(0, max(1, len(ws) - L - 1))
            segs.append(ws[off:off + L])
        pairs = [(segs[2 * i], segs[2 * i + 1]) for i in range(N_NULL + N_FRESH)]
        cal = {st: [s2.sim(st, a, b, idf) for a, b in pairs[:N_NULL]] for st in STATS}
        tau = {st: s0.pct(cal[st], 1 - s4.ALPHA) for st in STATS}
        refs = segs[(N_NULL + N_FRESH) * 2:]

        # X1 -- the pools must BE spike_v4's pools, not new draws from the same distribution.
        # X1 -- the pools must BE spike_v4's pools, not new draws from the same distribution.
        st_tau = stored["cells"]["L=%d" % L]["tau"]
        x1 = all(abs(tau[st] - st_tau[st]) < 1e-15 for st in STATS)
        out["certificates"].setdefault("X1_pool_reproduction", []).append(
            {"L": L, "equal_to_spike_v4_tau": bool(x1),
             "max_abs_diff": max(abs(tau[st] - st_tau[st]) for st in STATS)})
        out["calibration"]["L=%d" % L] = {
            "tau": tau, "floored": {st: bool(tau[st] <= 0.0) for st in STATS},
            "fpr_marginal": (stored["cells"]["L=%d" % L]["fpr_marginal"] if stored else None),
            "note": "tau is an unperturbed-pair p95 -> the edit operator cannot enter this arm"}

        for op in ("tok", "chr"):
            for ei, eps in enumerate(EPS):
                if op == "tok":
                    edits = [s2.perturb_rate(r, eps, vocab, rng) for r in refs]
                else:
                    edits = [chr_perturb(r, eps, random.Random(
                        s0.SEED0 + L * 97 + ri * 7919 + ei * 104729 + 1)) for ri, r in enumerate(refs)]
                sims = {st: [s2.sim(st, refs[r], edits[r], idf) for r in range(N_REFS)] for st in STATS}
                for st in STATS:
                    recall.setdefault("L=%d|%s|%s" % (L, st, op), []).append(
                        sum(1 for v in sims[st] if v >= tau[st]) / N_REFS)
                for a, b in PAIRS:
                    for rule in RULES:
                        hit = sum(1 for r in range(N_REFS)
                                  if s4.decide(rule, sims[a][r], tau[a], sims[b][r], tau[b])) / N_REFS
                        recall.setdefault("L=%d|%s+%s|%s|%s" % (L, a, b, rule, op), []).append(hit)
        print("L=%-5d tau=%s%s" % (L, {st: round(tau[st], 4) for st in STATS},
                                   "" if (x1 is None or x1) else "  << X1 FAILED"))

    x1_rows = out["certificates"]["X1_pool_reproduction"]
    assert all(r["equal_to_spike_v4_tau"] for r in x1_rows), \
        "X1 FAILED: this script's pools are not spike_v4's pools: %s" % x1_rows
    out["certificates"]["X1_pool_reproduction_summary"] = {
        "L_checked": [r["L"] for r in x1_rows], "all_equal": True,
        "max_abs_diff": max(r["max_abs_diff"] for r in x1_rows),
        "reading": ("the CALIBRATION arm is spike_v4's, character for character -- so any cross-operator "
                    "difference measured here is the BOUNDARY arm's and cannot be a re-drawn null")}
    out["recall"] = recall
    for key, rec in recall.items():
        out["eps_star"][key] = s2.cross(EPS, rec, 0.5)

    # --- X2 / X3: the bounds, per operator -------------------------------------------------
    x2 = {"cells": 0, "violations": []}
    x3 = {"violations": []}
    for op in ("tok", "chr"):
        for L in LGRID:
            for a, b in PAIRS:
                ra = recall["L=%d|%s|%s" % (L, a, op)]
                rb = recall["L=%d|%s|%s" % (L, b, op)]
                rf_or = recall["L=%d|%s+%s|or|%s" % (L, a, b, op)]
                rf_and = recall["L=%d|%s+%s|and|%s" % (L, a, b, op)]
                for i, eps in enumerate(EPS):
                    x2["cells"] += 2
                    if rf_or[i] < max(ra[i], rb[i]) - 1e-12:
                        x2["violations"].append("OR %s L=%d %s+%s eps=%.2f %r < max(%r,%r)" % (
                            op, L, a, b, eps, rf_or[i], ra[i], rb[i]))
                    if rf_and[i] > min(ra[i], rb[i]) + 1e-12:
                        x2["violations"].append("AND %s L=%d %s+%s eps=%.2f %r > min(%r,%r)" % (
                            op, L, a, b, eps, rf_and[i], ra[i], rb[i]))
                ep = out["eps_star"]
                o = ep.get("L=%d|%s+%s|or|%s" % (L, a, b, op))
                n = ep.get("L=%d|%s+%s|and|%s" % (L, a, b, op))
                sa = ep.get("L=%d|%s|%s" % (L, a, op))
                sb = ep.get("L=%d|%s|%s" % (L, b, op))
                if o is not None and sa is not None and sb is not None and o < max(sa, sb) - 1e-9:
                    x3["violations"].append("OR eps* %r < max(%r,%r) %s L=%d %s+%s" % (o, sa, sb, op, L, a, b))
                if n is not None and sa is not None and sb is not None and n > min(sa, sb) + 1e-9:
                    x3["violations"].append("AND eps* %r > min(%r,%r) %s L=%d %s+%s" % (n, sa, sb, op, L, a, b))
    assert not x2["violations"], "X2 COMPOSITION BOUND VIOLATED: %s" % x2["violations"][:3]
    assert not x3["violations"], "X3 EPS* BOUND VIOLATED: %s" % x3["violations"][:3]
    out["certificates"]["X2_composition_bounds"] = {
        "cells_checked": x2["cells"], "violations": [], "operators": ["tok", "chr"]}
    out["certificates"]["X3_eps_star_bounds"] = {"violations": [], "operators": ["tok", "chr"]}
    out["certificates"]["X4_calibration_arm_operator_free"] = {
        "statement": ("tau, the marginal FPRs, the indicator covariance and the excess = +-Cov identity are "
                      "properties of the UNPERTURBED joint null, so the edit operator cannot enter them; "
                      "this is STRUCTURAL, not a measurement"),
        "measured_here": False}

    # --- the transfer: which member OR recovers and which AND inherits, per operator --------
    for op in ("tok", "chr"):
        rows = []
        for L in LGRID:
            for a, b in PAIRS:
                ep = out["eps_star"]
                sa = ep.get("L=%d|%s|%s" % (L, a, op))
                sb = ep.get("L=%d|%s|%s" % (L, b, op))
                if sa is None or sb is None:
                    continue
                robust, brittle = (a, b) if sa >= sb else (b, a)
                o = ep.get("L=%d|%s+%s|or|%s" % (L, a, b, op))
                n = ep.get("L=%d|%s+%s|and|%s" % (L, a, b, op))
                rows.append({"L": L, "pair": "%s+%s" % (a, b), "robust": robust, "brittle": brittle,
                             "eps_robust": max(sa, sb), "eps_brittle": min(sa, sb),
                             "eps_or": o, "eps_and": n,
                             "or_vs_robust": same(o, max(sa, sb)),
                             "and_vs_brittle": same(n, min(sa, sb)),
                             "or_recovers_robust": same(o, max(sa, sb)) in ("exact", "close"),
                             "and_inherits_brittle": same(n, min(sa, sb)) in ("exact", "close")})
        out["transfer"][op] = rows
        print("\n[%s] member roles and transfer (L=3000):" % op)
        for r in rows:
            if r["L"] != 3000:
                continue
            print("   %-13s robust=%-7s brittle=%-7s | eps* OR=%-6s AND=%-6s | recovers_robust=%s inherits_brittle=%s"
                  % (r["pair"], r["robust"], r["brittle"],
                     fmt(r["eps_or"]), fmt(r["eps_and"]), r["or_recovers_robust"], r["and_inherits_brittle"]))

    # --- the PREDICTION: does the robust/brittle role SWAP between operators? --------------
    swap_rows = []
    for L in LGRID:
        for a, b in PAIRS:
            ta, tc = out["transfer"]["tok"], out["transfer"]["chr"]
            rt = next((r for r in ta if r["L"] == L and r["pair"] == "%s+%s" % (a, b)), None)
            rc = next((r for r in tc if r["L"] == L and r["pair"] == "%s+%s" % (a, b)), None)
            if rt is None or rc is None:
                continue
            swap_rows.append({"L": L, "pair": rt["pair"], "robust_tok": rt["robust"],
                              "robust_chr": rc["robust"], "swapped": rt["robust"] != rc["robust"],
                              "eps_robust_tok": rt["eps_robust"], "eps_robust_chr": rc["eps_robust"],
                              "eps_brittle_tok": rt["eps_brittle"], "eps_brittle_chr": rc["eps_brittle"]})
    n_swap = sum(1 for r in swap_rows if r["swapped"])
    # THE REGISTERED PREDICTION NAMES AN OBJECT: "under a CHARACTER edit `dice2c` is the robust member".
    # The first draft of this block scored it as "did ANY cell change which member is robust" -- a
    # criterion that does not answer the registered question (Class 208(b): a ranking that changes for one
    # reason scored as a change for another).  Tested here as written: in how many pairs is `dice2c` the
    # ROBUST member under the character operator?
    dice_cells = [r for r in swap_rows if "dice2c" in r["pair"]]
    dice_robust_chr = [r["pair"] for r in dice_cells if r["robust_chr"] == "dice2c"]
    dice_robust_tok = [r["pair"] for r in dice_cells if r["robust_tok"] == "dice2c"]
    # The registered sentence is GENERAL ("dice2c IS the robust member"), so the test must be whether it
    # holds across its cells -- an existential test ("at least one cell") answers a different question and
    # would report CONFIRMED for a claim the measurement refutes.
    made_robust_by_chr = [r["pair"] for r in dice_cells
                          if r["robust_chr"] == "dice2c" and r["robust_tok"] != "dice2c"]
    out["role_swap"] = {
        "registered_prediction": ("notes.md R571: under a CHARACTER edit `dice2c` is the robust member, "
                                  "so which one is brittle should swap"),
        "prediction_test": {
            "criterion": ("the registered claim is GENERAL -- `dice2c` is the robust member -- so it is "
                          "scored over its cells, not by whether any one cell satisfies it"),
            "cells_with_dice2c": len(dice_cells),
            "n_where_dice2c_robust_chr": len(dice_robust_chr),
            "n_where_dice2c_robust_tok": len(dice_robust_tok),
            "n_where_chr_MADE_dice2c_robust": len(made_robust_by_chr),
            "cells_where_dice2c_is_robust_chr": dice_robust_chr,
            "outcome": ("CONFIRMED" if len(dice_robust_chr) == len(dice_cells) and dice_cells
                        else "REFUTED (as a general claim)")},
        "generic_role_changes": {
            "criterion": "the robust member differs between the two operators (a DIFFERENT and weaker "
                         "statement, reported separately so the two cannot be conflated)",
            "n_compared": len(swap_rows), "n_changed": n_swap,
            "changed_cells": [{"pair": r["pair"], "L": r["L"], "tok": r["robust_tok"],
                               "chr": r["robust_chr"],
                               "margin_tok": abs(r["eps_robust_tok"] - r["eps_brittle_tok"]),
                               "margin_chr": abs(r["eps_robust_chr"] - r["eps_brittle_chr"])}
                              for r in swap_rows if r["swapped"]]},
        "rows": swap_rows}
    pt = out["role_swap"]["prediction_test"]
    print("\nPREDICTION (as registered: a GENERAL claim): `dice2c` is the robust member under a character "
          "edit -> %s" % pt["outcome"])
    print("   dice2c robust under chr in %d of %d cells (under tok: %d); the character edit MADE it robust "
          "in %d" % (pt["n_where_dice2c_robust_chr"], pt["cells_with_dice2c"],
                     pt["n_where_dice2c_robust_tok"], pt["n_where_chr_MADE_dice2c_robust"]))
    print("generic: robust member changed in %d of %d (L,pair) cells" % (n_swap, len(swap_rows)))
    for r in swap_rows:
        print("   L=%-5d %-13s robust: %-7s -> %-7s  changed=%s  margin tok=%.3f chr=%.3f" % (
            r["L"], r["pair"], r["robust_tok"], r["robust_chr"], r["swapped"],
            abs(r["eps_robust_tok"] - r["eps_brittle_tok"]),
            abs(r["eps_robust_chr"] - r["eps_brittle_chr"])))

    js = json.dumps(out, indent=1, sort_keys=True)
    io.open("spike_v7_results.json", "w", encoding="utf-8").write(js)
    print("\nartefact sha256:", hashlib.sha256(js.encode()).hexdigest()[:16],
          "bytes", len(js.encode()))


def fmt(v):
    return "none" if v is None else "%.3f" % v


if __name__ == "__main__":
    main()
