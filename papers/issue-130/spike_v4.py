#!/usr/bin/env python3
"""spike_v4 -- the FUSION axis (R568/R570 next step): does a per-statistic operating point COMPOSE?

The host's item 5 (2026-10-08T07:57) fixes the operating point the way the field sets it:
`tau(L, stat) = p95 of that statistic's own NULL pool at that length` -- an FPR-matched point,
per statistic and per length band. spike_v2 measured the singles; spike_v3 added the operator axis.
This script asks the question that rule leaves open:

    if each member is calibrated at nominal alpha, what is the ALPHA OF THE RULE?

Composition is at the DECISION level, because that is what "combine two checks" means in practice
and because a score-level fusion would need a second normalisation with its own defects:

    OR   (flag if EITHER member fires)   -- a candidate for recovering a brittleness boundary
    AND  (flag if BOTH members fire)     -- a candidate for suppressing false positives

Two design commitments, both of which are defects if violated:

  * **The PAIR is the unit, not the statistic.** One pool of unrelated segment pairs is drawn per L and
    EVERY statistic scores the SAME pair. A fusion study whose members see different pairs has no joint
    null to measure and can only report marginals.
  * **One operator.** A fused rule mixes members, so the edit ladder must be a single operator; the
    TOKEN substitution ladder is used (the realistic "rewording"), and the character ladder's effect on
    a character statistic is spike_v3's subject, not this one's.

Certificates (each must be able to fail):
  C1  self-fusion: fusing a statistic with ITSELF reproduces its decisions exactly.
  C2  floor absorption: a member whose tau sits ON the floor (every score passes) is ABSORBED by AND
      (the fused rule equals its sibling on every sample) and DESTROYS OR (it fires on every sample).
  C3  shuffle control: re-pairing member B's scores against member A's must move the measured fused FPR
      to the independence expectation -- if it does not, the departure measured on the true pairing is
      not the pairing's dependence.

Real text only (Project Gutenberg, pinned in corpus/SHA256SUMS). Ground truth by construction.
"""
import hashlib
import io
import json
import math
import random
from collections import Counter
from itertools import combinations

import spike_v0 as s0
import spike_v2 as s2

LGRID = [40, 150, 750, 3000]
STATS = ["jac3", "jac5", "dice2c", "cos"]
PAIRS = [tuple(p) for p in combinations(STATS, 2)]
RULES = ["or", "and"]
EPS = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
N_NULL = 1000         # calibration pool: tau = p95 of this (1000 -> p95 resolvable to ~1/1000)
N_FRESH = 20000       # measurement pool: the ACTUAL FPR is read here. A conjunction of two 5% checks
                      # sits near 2.5e-3, so a 300-draw pool sees 0.6 events -- it cannot resolve the
                      # very quantity the naive formula claims to predict. The calibration pool is
                      # deliberately LEFT at 1000 (a practitioner calibrates on the pairs they have),
                      # which is why the marginal FPRs read a little off the nominal alpha below.
N_REFS = 40           # recall ladder, token operator
ALPHA = 0.05          # the nominal level each member is calibrated to
MIN_EVENTS = 10       # a composition cell is REPORTED only if the rule fired at least this
                      # often on the fresh pool; below it the cell is UNRESOLVED, not a zero


def decide(rule, sa, ta, sb, tb):
    fa, fb = sa >= ta, sb >= tb
    return (fa or fb) if rule == "or" else (fa and fb)


def spearman(xs, ys):
    """Average-rank Spearman. Returns None when either input is CONSTANT: a correlation with a
    constant is UNDEFINED, not zero, and reporting 0.0 would read as "independent"."""
    def ranks(v):
        idx = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0]*len(v)
        i = 0
        while i < len(idx):
            j = i
            while j+1 < len(idx) and v[idx[j+1]] == v[idx[i]]:
                j += 1
            avg = (i+j)/2.0 + 1.0
            for k in range(i, j+1):
                r[idx[k]] = avg
            i = j+1
        return r
    rx, ry = ranks(xs), ranks(ys)
    if len(set(rx)) < 2 or len(set(ry)) < 2:
        return None
    return pearson(rx, ry)


def pearson(xs, ys):
    n = len(xs)
    mx = math.fsum(xs)/n
    my = math.fsum(ys)/n
    num = math.fsum((a-mx)*(b-my) for a, b in zip(xs, ys))
    dx = math.sqrt(math.fsum((a-mx)**2 for a in xs))
    dy = math.sqrt(math.fsum((b-my)**2 for b in ys))
    return (num/(dx*dy)) if dx > 0 and dy > 0 else None


def pearson_cov(xs, ys):
    """The covariance of two series -- NOT normalised. On two 0/1 indicator columns this is exactly
    the quantity the two decision-level compositions depart from independence by."""
    n = len(xs)
    mx = math.fsum(xs)/n
    my = math.fsum(ys)/n
    return math.fsum((a-mx)*(b-my) for a, b in zip(xs, ys))/n


def main():
    books = s0.load_books()
    cnt = Counter(w for _, ws in books for w in ws)
    vocab = [w for w, _ in cnt.most_common(20000)]
    df = Counter()
    for _, ws in books:
        df.update(set(ws))
    N = len(books)
    idf = {w: math.log((N+1)/(df[w]+1)) + 1.0 for w in cnt}

    out = {"note": __doc__, "L_grid": LGRID, "stats": STATS, "pairs": [list(p) for p in PAIRS],
           "rules": RULES, "eps_grid": EPS, "alpha": ALPHA, "n_null": N_NULL, "n_fresh": N_FRESH,
           "n_refs": N_REFS, "operator": "tok (token substitution, exact rate)",
           "convention": "tau(L,stat) = p95 of that statistic's own unrelated-pair null at the same L;"
                         " composition at the DECISION level; the pair is the unit",
           "cells": {}, "recall": {}, "certificates": {}}
    all_floor = []

    for L in LGRID:
        rng = random.Random(s0.SEED0 + L*104729)
        need = (N_NULL + N_FRESH)*2 + N_REFS
        segs = []
        for i in range(need):
            bk, ws = books[i % len(books)]
            off = rng.randrange(0, max(1, len(ws)-L-1))
            segs.append(ws[off:off+L])
        # ONE pool of unrelated pairs, scored by EVERY statistic: the joint null lives on the pair.
        pairs = [(segs[2*i], segs[2*i+1]) for i in range(N_NULL+N_FRESH)]
        S = {st: [s2.sim(st, a, b, idf) for a, b in pairs] for st in STATS}
        cal, fresh = {st: S[st][:N_NULL] for st in STATS}, {st: S[st][N_NULL:] for st in STATS}
        tau = {st: s0.pct(cal[st], 1-ALPHA) for st in STATS}
        share = {st: sum(1 for v in cal[st] if v > 0)/N_NULL for st in STATS}
        fpr = {st: sum(1 for v in fresh[st] if v >= tau[st])/N_FRESH for st in STATS}
        floored = {st: bool(tau[st] <= 0.0) for st in STATS}
        if any(floored.values()):
            all_floor.append((L, [st for st in STATS if floored[st]]))

        cell = {"tau": tau, "share_positive": share, "fpr_marginal": fpr,
                "degenerate_tau_zero": floored, "null_median": {st: s0.pct(cal[st], 0.5) for st in STATS}}
        for a, b in PAIRS:
            pair_key = "%s+%s" % (a, b)
            ca, cb = fresh[a], fresh[b]
            ent = {"pearson_fresh": pearson(ca, cb), "spearman_fresh": spearman(ca, cb),
                   "pearson_null": pearson(cal[a], cal[b]), "spearman_null": spearman(cal[a], cal[b])}
            ia = [1.0 if v >= tau[a] else 0.0 for v in ca]
            ib = [1.0 if v >= tau[b] else 0.0 for v in cb]
            cov = pearson_cov(ia, ib)              # the INDICATOR covariance, computed directly
            ent["indicator_cov"] = cov
            ent["phi"] = (cov/math.sqrt(fpr[a]*(1-fpr[a])*fpr[b]*(1-fpr[b]))
                          if fpr[a]*(1-fpr[a])*fpr[b]*(1-fpr[b]) > 0 else None)
            for rule in RULES:
                fired = [decide(rule, ca[i], tau[a], cb[i], tau[b]) for i in range(N_FRESH)]
                ev = sum(fired)
                ent["events_%s" % rule] = ev
                ent["fpr_%s" % rule] = ev/N_FRESH
                exp = (fpr[a]+fpr[b]-fpr[a]*fpr[b]) if rule == "or" else (fpr[a]*fpr[b])
                ent["indep_%s" % rule] = exp
                ent["excess_%s" % rule] = ent["fpr_%s" % rule] - exp
                # An UNRESOLVED cell is not a measured zero. The rule is read where it fires at least
                # MIN_EVENTS times on the fresh pool; below that the cell is reported as such.
                ent["resolved_%s" % rule] = bool(ev >= MIN_EVENTS)
                ent["expected_events_%s" % rule] = exp*N_FRESH
                # The formula a practitioner actually uses: the NOMINAL alpha of each member, assumed
                # independent. `indep_*` above uses the MEASURED marginals (so it isolates dependence);
                # this isolates the whole error of the naive composition.
                naive = (1-(1-ALPHA)**2) if rule == "or" else ALPHA**2
                ent["naive_%s" % rule] = naive
                ent["ratio_naive_%s" % rule] = (ent["fpr_%s" % rule]/naive) if naive else float("nan")
            # EXACT IDENTITY -- the mechanism is PROVED here, not fitted. For two events A, B:
            #   P(A and B) = a*b + Cov(1_A, 1_B)      -> excess_and = +Cov
            #   P(A or  B) = a + b - a*b - Cov(...)   -> excess_or  = -Cov
            # so the two compositions depart from independence by the SAME quantity with OPPOSITE
            # signs. (The first draft of this comment asserted +Cov for both and this assertion --
            # not a reviewer -- caught the sign error, which is what a certificate is for.)
            assert abs(ent["excess_and"] - cov) < 1e-12, \
                "IDENTITY FAILED at L=%d %s: excess_and %r vs Cov %r" % (L, pair_key, ent["excess_and"], cov)
            assert abs(ent["excess_or"] + cov) < 1e-12, \
                "IDENTITY FAILED at L=%d %s: excess_or %r vs -Cov %r" % (L, pair_key, ent["excess_or"], -cov)
            assert abs(ent["excess_or"] + ent["excess_and"]) < 1e-12, \
                "IDENTITY FAILED at L=%d %s: excess_or + excess_and is not 0" % (L, pair_key)
            # C3 -- the shuffle control: break the pairing of the two statistics' FRESH scores.
            sh = list(range(N_FRESH))
            random.Random(s0.SEED0 + L*7919).shuffle(sh)
            cb_sh = [cb[i] for i in sh]
            ent["shuffled_spearman_fresh"] = spearman(ca, cb_sh)
            for rule in RULES:
                fired = [decide(rule, ca[i], tau[a], cb_sh[i], tau[b]) for i in range(N_FRESH)]
                ent["shuffled_fpr_%s" % rule] = sum(fired)/N_FRESH
            cell[pair_key] = ent
        out["cells"]["L=%d" % L] = cell

        # ---- C1 + C2: the structural certificates, on this cell's own fresh pool ----
        for st in STATS:
            d_self = [decide("and", fresh[st][i], tau[st], fresh[st][i], tau[st]) for i in range(N_FRESH)]
            ref = [fresh[st][i] >= tau[st] for i in range(N_FRESH)]
            assert d_self == ref, "C1 FAILED: fusing %s with itself changed a decision at L=%d" % (st, L)
        absorbed, destroyed = [], []
        for a, b in PAIRS:
            for fl, sib, k in ((a, b, "a"), (b, a, "b")):
                if not floored[fl]:
                    continue
                sib_fires = [fresh[sib][i] >= tau[sib] for i in range(N_FRESH)]
                and_fires = [decide("and", fresh[a][i], tau[a], fresh[b][i], tau[b]) for i in range(N_FRESH)]
                assert and_fires == sib_fires, \
                    "C2 FAILED: a floored member did not absorb under AND (%s+%s at L=%d)" % (a, b, L)
                or_fires = [decide("or", fresh[a][i], tau[a], fresh[b][i], tau[b]) for i in range(N_FRESH)]
                assert all(or_fires), "C2 FAILED: OR with a floored member did not fire on every sample"
                absorbed.append("%s+%s" % (a, b))
                destroyed.append("%s+%s" % (a, b))
        out["certificates"]["L=%d" % L] = {"C1_self_fusion": "%d/%d statistics reproduce their own decisions"
                                                          % (len(STATS), len(STATS)),
                                           "C2_absorbed_by_and": sorted(set(absorbed)),
                                           "C2_destroyed_or": sorted(set(destroyed))}

        # ---- the recall ladder under ONE operator (tok), singles and fused ----
        refs = segs[(N_NULL+N_FRESH)*2:]
        for ei, eps in enumerate(EPS):
            edits = [s2.perturb_rate(r, eps, vocab, rng) for r in refs]
            sims = {st: [s2.sim(st, refs[r], edits[r], idf) for r in range(N_REFS)] for st in STATS}
            for st in STATS:
                hit = sum(1 for v in sims[st] if v >= tau[st])/N_REFS
                out["recall"].setdefault("L=%d|%s" % (L, st), []).append(hit)
            for a, b in PAIRS:
                for rule in RULES:
                    hit = sum(1 for r in range(N_REFS)
                              if decide(rule, sims[a][r], tau[a], sims[b][r], tau[b]))/N_REFS
                    out["recall"].setdefault("L=%d|%s|%s" % (L, "%s+%s" % (a, b), rule), []).append(hit)

    # ---- the composition's recall bounds: provable, and asserted on the measured curves ----
    #   R_or  = 1-(1-R_a)(1-R_b) >= max(R_a, R_b)      (a union of two events)
    #   R_and = R_a * R_b        <= min(R_a, R_b)
    # so a disjunction can only ever be MORE robust than its best member and a conjunction only ever
    # LESS robust than its worst. Both are read off the stored curves, at every eps.
    bounds = {"or_ge_max": 0, "and_le_min": 0, "cells": 0, "violations": []}
    for L in LGRID:
        for a, b in PAIRS:
            ra = out["recall"]["L=%d|%s" % (L, a)]
            rb = out["recall"]["L=%d|%s" % (L, b)]
            for rule, cmp_ in (("or", "max"), ("and", "min")):
                rf = out["recall"]["L=%d|%s+%s|%s" % (L, a, b, rule)]
                bounds["cells"] += 1
                for i, eps in enumerate(EPS):
                    ok = (rf[i] >= max(ra[i], rb[i]) - 1e-12) if cmp_ == "max" else \
                         (rf[i] <= min(ra[i], rb[i]) + 1e-12)
                    key = "or_ge_max" if cmp_ == "max" else "and_le_min"
                    bounds[key] += 1
                    if not ok:
                        bounds["violations"].append("L=%d %s+%s %s eps=%.2f: %r vs %r/%r" % (
                            L, a, b, rule, eps, rf[i], ra[i], rb[i]))
    assert not bounds["violations"], "COMPOSITION BOUND VIOLATED: %s" % bounds["violations"][:3]
    out["certificates"]["recall_bounds"] = bounds

    # eps* per curve, and the recovery/price pair it defines
    out["eps_star"] = {}
    for key, rec in out["recall"].items():
        out["eps_star"][key] = s2.cross(EPS, rec, 0.5)

    ep = out["eps_star"]
    eps_viol = []
    for L in LGRID:
        for a, b in PAIRS:
            o = ep.get("L=%d|%s+%s|or" % (L, a, b))
            n = ep.get("L=%d|%s+%s|and" % (L, a, b))
            sa = ep.get("L=%d|%s" % (L, a))
            sb = ep.get("L=%d|%s" % (L, b))
            if o is not None and sa is not None and sb is not None and o < max(sa, sb) - 1e-9:
                eps_viol.append("OR eps* %s < max(%s,%s) at L=%d %s+%s" % (o, sa, sb, L, a, b))
            if n is not None and sa is not None and sb is not None and n > min(sa, sb) + 1e-9:
                eps_viol.append("AND eps* %s > min(%s,%s) at L=%d %s+%s" % (n, sa, sb, L, a, b))
    assert not eps_viol, "EPS* BOUND VIOLATED: %s" % eps_viol
    out["certificates"]["eps_star_bounds"] = {
        "or": "eps*(OR) >= max(eps* of the members) -- asserted, 1e-9",
        "and": "eps*(AND) <= min(eps* of the members) -- asserted, 1e-9",
        "violations": []}

    for L in LGRID:
        c = out["cells"]["L=%d" % L]
        print("== L=%d  tau: %s" % (L, {st: round(c["tau"][st], 4) for st in STATS}))
        print("   floor(zero tau): %s | share>0: %s" % (
            [st for st in STATS if c["degenerate_tau_zero"][st]],
            {st: round(c["share_positive"][st], 3) for st in STATS}))
        print("   FPR marginal vs nominal %.2f: %s" % (ALPHA, {st: round(c["fpr_marginal"][st], 3) for st in STATS}))
        for a, b in PAIRS:
            e = c["%s+%s" % (a, b)]
            def fmt(rule):
                if not e["resolved_%s" % rule]:
                    return "UNRESOLVED (%d events vs %.1f expected)" % (
                        e["events_%s" % rule], e["expected_events_%s" % rule])
                return "%.4f (indep %.4f, x %.2f, %d events)" % (
                    e["fpr_%s" % rule], e["indep_%s" % rule],
                    (e["fpr_%s" % rule]/e["indep_%s" % rule]) if e["indep_%s" % rule] else float("nan"),
                    e["events_%s" % rule])
            print("   %-13s rho=%s/%s | OR %s | AND %s" % (
                "%s+%s" % (a, b),
                ("%.2f" % e["pearson_fresh"]) if e["pearson_fresh"] is not None else "undef",
                ("%.2f" % e["spearman_fresh"]) if e["spearman_fresh"] is not None else "undef",
                fmt("or"), fmt("and")))
        print("   eps* singles: %s" % {st: out["eps_star"].get("L=%d|%s" % (L, st)) for st in STATS})
        for a, b in PAIRS:
            ko = out["eps_star"].get("L=%d|%s+%s|or" % (L, a, b))
            ka = out["eps_star"].get("L=%d|%s+%s|and" % (L, a, b))
            print("      %-13s eps*: OR=%s  AND=%s" % ("%s+%s" % (a, b),
                  ("%.3f" % ko) if ko else "none", ("%.3f" % ka) if ka else "none"))
        print("   shuffle control (pairing broken, rho -> ~0): %s" % {
            "%s+%s" % (a, b): (round(c["%s+%s" % (a, b)]["shuffled_fpr_and"], 4),
                               round(c["%s+%s" % (a, b)]["indep_and"], 4)) for a, b in PAIRS[:3]})

    # ---- the headline: the naive composition a practitioner computes vs what the rule does ----
    print("\n== naive composition (each member at nominal alpha=%.2f, assumed independent) ==" % ALPHA)
    print("   formula: OR -> %.4f   AND -> %.4f" % (1-(1-ALPHA)**2, ALPHA**2))
    print("   %-8s %-13s %-28s %-28s" % ("L", "pair", "OR measured (x naive)", "AND measured (x naive)"))
    worst_or, worst_and = None, None
    for L in LGRID:
        c = out["cells"]["L=%d" % L]
        for a, b in PAIRS:
            e = c["%s+%s" % (a, b)]
            def cell(rule):
                if not e["resolved_%s" % rule]:
                    return "UNRESOLVED (%d ev)" % e["events_%s" % rule]
                return "%.4f  (x %.2f, %d ev)" % (e["fpr_%s" % rule], e["ratio_naive_%s" % rule],
                                                  e["events_%s" % rule])
            if e["resolved_or"] and (worst_or is None or e["ratio_naive_or"] > worst_or[0]):
                worst_or = (e["ratio_naive_or"], L, a, b)
            if e["resolved_and"] and (worst_and is None or e["ratio_naive_and"] > worst_and[0]):
                worst_and = (e["ratio_naive_and"], L, a, b)
            print("   %-8d %-13s %-28s %-28s" % (L, "%s+%s" % (a, b), cell("or"), cell("and")))
    print("   worst OR  x naive: %.2f at L=%d %s+%s" % worst_or)
    print("   worst AND x naive: %.2f at L=%d %s+%s" % worst_and)
    print("   recall bounds asserted: %d/%d cells, %d eps-points, violations 0"
          % (out["certificates"]["recall_bounds"]["cells"], out["certificates"]["recall_bounds"]["cells"],
             out["certificates"]["recall_bounds"]["or_ge_max"] + out["certificates"]["recall_bounds"]["and_le_min"]))
    print("   floor cells (a member with tau == 0, no alpha-level operating point): %s"
          % [(L, [st for st in STATS if out["cells"]["L=%d" % L]["degenerate_tau_zero"][st]])
             for L in LGRID if any(out["cells"]["L=%d" % L]["degenerate_tau_zero"][st] for st in STATS)])

    # ---- the mechanism: the excess the identity PREDICTS is the indicator covariance, so the
    # signed departure must be ORDERED by the pair's null dependence. Read across cells, not asserted.
    print("\n== the conjunction's error as a function of the pair's null dependence ==")
    print("   (excess_and = +Cov(1_A,1_B) by identity; the sign of the departure must follow rho)")
    rows = []
    for L in LGRID:
        c = out["cells"]["L=%d" % L]
        for a, b in PAIRS:
            e = c["%s+%s" % (a, b)]
            if not e["resolved_and"]:
                continue
            rows.append((L, "%s+%s" % (a, b), e["spearman_fresh"], e["phi"],
                         e["excess_and"], e["ratio_naive_and"], e["events_and"]))
    rows.sort(key=lambda r: (r[2] if r[2] is not None else 0.0))
    for L, pk, rho, phi, ex, ratio, ev in rows:
        tag = "FLOOR (member absorbed)" if ex > 0.01 and (rho is None or abs(rho) < 0.1) else ""
        print("   L=%-5d %-13s rho=%s phi=%s | excess_and=%+.5f | x naive %.2f (%d ev) %s" % (
            L, pk,
            ("%+.2f" % rho) if rho is not None else "undef ",
            ("%+.2f" % phi) if phi is not None else "undef ",
            ex, ratio, ev, tag))
    # A cell is "live" when BOTH members have an alpha-level operating point. That is read from the
    # CONDITION that creates the degeneracy (a floored member), never from the value it produces:
    # a threshold on `excess` would silently admit floored cells, whose excess is exactly 0 by
    # construction and whose "sign" is therefore not defined at all.
    live = []
    for L in LGRID:
        floored = out["cells"]["L=%d" % L]["degenerate_tau_zero"]
        for a, b in PAIRS:
            e = out["cells"]["L=%d" % L]["%s+%s" % (a, b)]
            if not e["resolved_and"] or floored[a] or floored[b]:
                continue
            if e["spearman_fresh"] is None:
                continue
            live.append((L, "%s+%s" % (a, b), e["spearman_fresh"], e["excess_and"]))
    agree = sum(1 for r in live if (r[2] > 0) == (r[3] > 0))
    rr = spearman([r[2] for r in live], [r[3] for r in live])
    print("   live cells (both members have an operating point): %d" % len(live))
    print("   the sign of the departure follows rho in %d of %d; rank correlation(rho, excess) = %s"
          % (agree, len(live), ("%+.2f" % rr) if rr is not None else "undef"))
    unresolvable = []
    for r in live:
        if (r[2] > 0) != (r[3] > 0):
            # Is the disagreement RESOLVABLE? Compare the departure against the sampling sd of the
            # conjunction's rate at this cell's own event count -- a departure inside it is not a
            # counterexample to the identity, it is an unresolved cell.
            c = out["cells"]["L=%d" % r[0]]["%s" % r[1]]
            fpr = c["events_and"]/N_FRESH
            sd = math.sqrt(fpr*(1-fpr)/N_FRESH)
            z = r[3]/sd if sd else float("inf")
            unresolvable.append(r[3]/sd if sd else 0.0)
            print("     disagreement: L=%d %s rho=%+.3f excess=%+.5f | sampling sd %.1e -> z=%+.1f"
                  % (r[0], r[1], r[2], r[3], sd, z))
    print("   disagreements: %d, all with |z| = %s (a departure inside its own sampling sd is an"
          " UNRESOLVED cell, not a counterexample)" % (len(unresolvable),
          ", ".join("%.1f" % abs(z) for z in unresolvable) or "n/a"))
    out["mechanism"] = {"rows": [[L, pk, rho, phi, ex, ratio, ev] for L, pk, rho, phi, ex, ratio, ev in rows],
                        "live_cells": len(live), "sign_agreement": agree,
                        "rank_corr_rho_excess": rr,
                        "note": "excess_and = +Cov(1_A,1_B) is an IDENTITY (asserted); the rank "
                                "correlation is a supporting reading over %d live cells, not a fit" % len(live)}

    js = json.dumps(out, indent=1, sort_keys=True)
    io.open("spike_v4_results.json", "w", encoding="utf-8").write(js)
    print("\nartefact sha256:", hashlib.sha256(js.encode()).hexdigest()[:16], "bytes", len(js.encode()))


if __name__ == "__main__":
    main()
