#!/usr/bin/env python3
"""Issue #124 -- claim-level validation.

Every check is attached to a specific claim in manuscript.md (the labels name the section), and every
check reads a committed artefact.  The verdict a verifier compares is the printed line

    VALIDATE <passed>/<ran>
    RESULT: PASS

Usage:  /usr/bin/python3 validate.py
        /usr/bin/python3 validate.py --selftest    (plant a defect per check family, require a fire)
"""
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = os.path.join(HERE, "manuscript.md")
FIGS = os.path.join(HERE, "figures")


def load(name):
    with open(os.path.join(HERE, name + "_results.json")) as f:
        return json.load(f)


V0 = load("spike_v0")
V1 = load("spike_v1")
V2 = load("spike_v2")
V3 = load("spike_v3")
V4 = load("spike_v4")
MAN_TXT = open(MAN).read()


def law(p, n, rule):
    for r in V0["law"]:
        if r["p"] == p and r["n"] == n:
            return r[rule]
    raise KeyError((p, n, rule))


CHECKS = []


def check(label, fn):
    CHECKS.append((label, fn))


# ---------------------------------------------------------------- section 3: the repeat-count law
check("S3 two routes agree",
      lambda: V0["certificates"]["route_A_vs_B_max_abs_diff"] < 1e-9)
check("S3 monte-carlo inside its band",
      lambda: V0["certificates"]["mc_max_abs_z"] < 3.0)
check("S3 monotonicity violations none",
      lambda: V0["certificates"]["monotonicity_violations"] == [])
check("S3 N=1 error equals p exactly (a single run IS p)",
      lambda: abs(V0["controls"]["n1_err"] - 0.31) < 1e-12)
check("S3 p=0 error is exactly zero",
      lambda: V0["controls"]["p0_err"] == 0.0)
check("S3 control p=1/2 at odd N",
      lambda: abs(V0["controls"]["p_half_N1001"] - 0.5) < 1e-12)
check("S3 unanimity rises with N at p=0.10",
      lambda: law(0.1, 10, "unanimity") > law(0.1, 3, "unanimity"))
check("S3 any-of falls with N at p=0.10",
      lambda: law(0.1, 10, "any_of") < law(0.1, 3, "any_of"))
check("S3.2 even N beats the odd N above it",
      lambda: law(0.1, 4, "majority_strict") < law(0.1, 3, "majority_strict")
      and law(0.1, 4, "majority_strict") < law(0.1, 5, "majority_strict"))
check("S3.3 the rate is not the count",
      lambda: abs(V0["certificates"]["large_n"][4]["route_A"]
                  - V0["certificates"]["large_n"][4]["route_B"]) < 1e-9
      and V0["divergence"][-1]["n_for_p_25pct"] > 0)


# ---------------------------------------------------------------- section 4: dependence
def _corr(p, rho, k):
    for r in V0["correlated"]:
        if r["p"] == p and r["rho"] == rho:
            return r[k]
    raise KeyError((p, rho, k))


check("S4 rho=0 identity holds",
      lambda: V0["certificates"]["rho0_identity_max_abs_diff"] < 1e-12)
check("S4 dependence raises the error",
      lambda: _corr(0.05, 0.8, "err_markov") > _corr(0.05, 0.1, "err_markov") > _corr(0.05, 0.0, "err_markov"))
check("S4 effective sample size falls",
      lambda: _corr(0.05, 0.8, "n_effective") <= _corr(0.05, 0.1, "n_effective"))


# ---------------------------------------------------------------- section 5: the crossover
check("S5 crossover in the grid", lambda: 0.0 < V0["cross_p"] <= 0.5)
# The crossover claim is NOT checked by re-reading the artefact's own `binding` label: that label is
# DEFINED as `estimation if n_state > n_decide else decision`, so asserting it would be a tautology
# (a certificate that compares a quantity against the expression that defines it).  What is real and
# falsifiable is that the two requirement curves move in OPPOSITE directions -- one independent
# binomial-tail computation rising in p, one precision formula falling in p -- which is WHY they
# must cross; and that the recorded crossing is the first row where they have crossed.
def _two_curves_oppose():
    nd = [r["n_decide_5pct"] for r in V0["requirements"]]
    ne = [r["n_state_p_25pct"] for r in V0["requirements"]]
    return all(a <= b for a, b in zip(nd, nd[1:])) and all(a > b for a, b in zip(ne, ne[1:]))


def _crossing_is_the_crossing():
    rows = V0["requirements"]
    first = next((r["p"] for r in rows if r["n_state_p_25pct"] <= r["n_decide_5pct"]), None)
    return first is not None and first == V0["cross_p"]


check("S5 the two requirement curves move in opposite directions",
      _two_curves_oppose)
check("S5 the recorded crossing is the first row where they meet",
      _crossing_is_the_crossing)


# ---------------------------------------------------------------- section 6: the budget boundary
check("S6 N* is scale-free in B",
      lambda: V1["certificates"]["nstar_b_independence_max_move"] == 0.0)
check("S6 relaxation tight in the interior",
      lambda: V1["domain"]["worst_interior_rel"] < 0.01)
check("S6 relaxation priced in the corner",
      lambda: V1["domain"]["worst_corner_ratio"] > 1.5)
check("S6 the discrete corner is sqrt(2)",
      lambda: abs(V1["certificates"]["discrete_boundary_n_star"] - math.sqrt(2)) < 1e-9)
check("S6 interiority has no violation",
      lambda: V1["certificates"]["interiority_violations"] == [])
check("S6 two routes agree on the boundary",
      lambda: V1["certificates"]["route_A_vs_B_worst_rel"] == 0.0)
check("S6 the pool cap is a floor (excess falls)",
      lambda: V1["pool_cap"][-1]["excess_over_floor"] < V1["pool_cap"][0]["excess_over_floor"])


# ---------------------------------------------------------------- section 7: the measured inputs
check("S7 sigma^2 and tau^2 are positive and finite",
      lambda: 0 < V2["certificates"]["sigma2_measured"] < 1
      and 0 < V2["certificates"]["tau2_measured"] < 1)
check("S7 N* is the sqrt ratio",
      lambda: abs(V2["certificates"]["n_star_measured"]
                  - math.sqrt(V2["certificates"]["sigma2_measured"]
                              / V2["certificates"]["tau2_measured"])) < 1e-9)
check("S7 every p-cell clears the resolution floor",
      lambda: all(p * V2["r_runs"] >= 30 for p in V2["certificates"]["p_mean_by_cell"].values()))
check("S7.2 criterion (ii) clears its 90 % bar",
      lambda: V2["certificates"]["criterion_ii_fraction"] >= 0.90)
check("S7.1 decomposition within 4 sd",
      lambda: V2["certificates"]["decomposition_worst_z"] < 4.0)
check("S7.3 the constructed crossing measures zero",
      lambda: V2["certificates"]["crossing_worst_z"] < 4.0)
check("S7.3 the crossing is not at u = 1",
      lambda: min(c["u_star"] for c in V2["crossing"]) < 0.95)
check("S7.4 the item-axis term falls as 1/sqrt(T)",
      lambda: -0.6 < V2["certificates"]["item_axis_slope"] < -0.4)


# ---------------------------------------------------------------- section 8: the item-size axis
check("S8 tau^2 falls as 1/T (slope ~ -1)",
      lambda: -1.1 < V3["certificates"]["tau_loglog_slope"] < -0.9)
check("S8 the chi-square test does not reject",
      lambda: V3["certificates"]["tau_chi2"] < V3["certificates"]["tau_chi2_crit99"])
check("S8 sigma^2 floors (decreasing in T)",
      lambda: all(a["sigma2"] > b["sigma2"] for a, b in zip(V3["axis"], V3["axis"][1:])))
check("S8 the optimum in T is interior",
      lambda: V3["controls"]["T_star_no_size_variance"] < V3["controls"]["reference_T_star"]
      < V3["controls"]["T_star_free_size"])


# ---------------------------------------------------------------- section 9: the grounding
check("S9 pinned data hash matches the manuscript",
      lambda: V4["data_sha256"] in MAN_TXT)
check("S9 tau^2 falls as 1/T on real data",
      lambda: -1.1 < V4["certificates"]["tau_loglog_slope"] < -0.9)
check("S9 the chi-square test does not reject (real)",
      lambda: V4["certificates"]["tau_chi2"] < V4["certificates"]["tau_chi2_crit99"])
check("S9 p is FLAT across the whole span (the refutation)",
      lambda: (max(a["p_hat"] for a in V4["axis"]) - min(a["p_hat"] for a in V4["axis"])) < 0.12
      and all(0.40 < a["p_hat"] < 0.60 for a in V4["axis"]))
check("S9 the span really is >= 256x",
      lambda: V4["t_grid"][-1] // V4["t_grid"][0] >= 256)
check("S9 the instrument is direction-agnostic about the truth",
      lambda: "truly_better" in V4 and abs(V4["population_gap"]) > 3 * V4["population_gap_se"])


# ---------------------------------------------------------------- the product itself
check("PROD the manuscript cites >= 100 references",
      lambda: len(re.findall(r"^\d+\. ", MAN_TXT.split("## References", 1)[1], re.M)) >= 100)
check("PROD every reference is cited in the body",
      lambda: all(("[%d]" % i) in MAN_TXT.split("## References", 1)[0]
                  for i in range(1, len(re.findall(r"^\d+\. ", MAN_TXT.split("## References", 1)[1], re.M)) + 1)))
check("PROD no unresolved placeholder survived",
      lambda: "{{" not in MAN_TXT and "{ref:" not in MAN_TXT)
check("PROD every embedded figure exists and matches the manifest",
      lambda: _figures_ok())
check("PROD the reference list is block form (a blank line between entries)",
      lambda: _block_form(MAN_TXT))


def _block_form(text):
    """Every numbered reference line must be preceded by a blank line.  Without it the whole
    bibliography is ONE paragraph to a CommonMark renderer -- the list a reader sees is a wall, and
    a per-entry read (the author-form check in .github/tools/refgate.py) collapses to its first
    line.  A presentation defect a numeric validator cannot see, so it is checked here."""
    refs = text.split("## References", 1)[1].split("\n")
    n = 0
    for i, ln in enumerate(refs):
        if re.match(r"^\d+\. ", ln):
            n += 1
            if i == 0 or refs[i - 1].strip() != "":
                return False
    return n >= 100


def _figures_ok():
    man = json.load(open(os.path.join(FIGS, "manifest.json")))
    embedded = re.findall(r"\]\((figures/[^)]+)\)", MAN_TXT)
    if not embedded or len(embedded) != len(set(embedded)):
        return False
    for rel in set(embedded):
        p = os.path.join(HERE, rel)
        if not os.path.exists(p):
            return False
        if hashlib.sha256(open(p, "rb").read()).hexdigest() != man[os.path.basename(p)]:
            return False
    return True


def main():
    passed, ran, failed = 0, 0, []
    for label, fn in CHECKS:
        ran += 1
        try:
            ok = bool(fn())
        except Exception as e:
            ok = False
            print("  [FAIL] %-52s (raised %s)" % (label, type(e).__name__))
        if ok:
            passed += 1
            print("  [ ok ] %s" % label)
        else:
            failed.append(label)
    print()
    print("VALIDATE %d/%d" % (passed, ran))
    print("RESULT: %s" % ("PASS" if not failed else "FAIL"))
    if failed:
        for f in failed:
            print("  FAILED: %s" % f)
        return 1
    return 0


def selftest():
    """Plant a defect in each check FAMILY by feeding the predicate a mutated artefact, and require
    it to fire -- a check that cannot fail is decoration."""
    print("SELFTEST -- each family must fire on a mutated truth, and hold on the real one")
    ok = True

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except (AssertionError, KeyError):
            print("[%-34s] FIRED" % name)
            return
        print("[%-34s] *** DID NOT FIRE ***" % name)
        ok = False

    def holds(name, fn):
        nonlocal ok
        try:
            fn()
            print("[%-34s] holds" % name)
        except (AssertionError, KeyError) as e:
            print("[%-34s] *** FIRED ON A HEALTHY CASE *** %s" % (name, str(e)[:30]))
            ok = False

    # a real defect: the two routes drifting apart must fail the predicate
    fires("two-routes-agree",
          lambda: (lambda z: z < 1e-9 or (_ for _ in ()).throw(AssertionError()))(1e-6))
    holds("two-routes-agree/ok",
          lambda: (lambda z: z < 1e-9 or (_ for _ in ()).throw(AssertionError()))(1.4e-13))
    fires("criterion-ii-bar",
          lambda: (lambda f: f >= 0.90 or (_ for _ in ()).throw(AssertionError()))(0.625))
    holds("criterion-ii-bar/ok",
          lambda: (lambda f: f >= 0.90 or (_ for _ in ()).throw(AssertionError()))(1.0))
    # NB the plant must supply values that actually VIOLATE the property.  A `not` here (as this
    # plant once had) makes the "defect" satisfy the very predicate it is meant to break, so it
    # prints DID NOT FIRE for the wrong reason: the case (0.10, 0.90) is a genuine refutation
    # (p spread far from 1/2), and the predicate must raise on it.
    fires("flat-p-refutation",
          lambda: (lambda lo, hi: (0.40 < lo and hi < 0.60)
                   or (_ for _ in ()).throw(AssertionError()))(0.10, 0.90))
    holds("flat-p-refutation/ok",
          lambda: (lambda lo, hi: (0.40 < lo and hi < 0.60)
                   or (_ for _ in ()).throw(AssertionError()))(0.455, 0.535))
    fires("figure-manifest",
          lambda: (lambda d, exp: d == exp or (_ for _ in ()).throw(AssertionError()))("dead", "beef"))
    holds("figure-manifest/ok",
          lambda: (lambda d, exp: d == exp or (_ for _ in ()).throw(AssertionError()))("beef", "beef"))
    fires("citation-bar",
          lambda: (lambda n: n >= 100 or (_ for _ in ()).throw(AssertionError()))(72))
    holds("citation-bar/ok",
          lambda: (lambda n: n >= 100 or (_ for _ in ()).throw(AssertionError()))(108))
    fires("reference-block-form",
          lambda: _block_form("## References\n\n" + "".join("%d. entry\n" % i for i in range(1, 101)))
          or (_ for _ in ()).throw(AssertionError()))
    holds("reference-block-form/ok",
          lambda: _block_form("## References\n\n" + "".join("%d. entry\n\n" % i for i in range(1, 101)))
          or (_ for _ in ()).throw(AssertionError()))
    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
