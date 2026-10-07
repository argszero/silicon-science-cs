#!/usr/bin/env python3
"""check_numbers (#126, R551) -- every headline number in the manuscript, re-derived from the artefact
that produced it and matched against the sentence that states it.

Why this exists: the manuscript's numbers were typed from the research notes while it was written, and
an audit in the same round found FOUR blocks where the notes had drifted (the conditioning exponents, the
path-condition ratios, the per-case lane split, one library range).  A typed copy of a number is a claim
with no owner (Classes 124(b)/164(c)): nothing in the package can tell a reader that 18-20% became 14-18%
when the lane arm was corrected.  So each number is ANCHORED here to (i) the artefact field it comes from
and (ii) the literal sentence in manuscript.md that carries it -- both sides of the comparison are
objects that can change independently, which is what makes the check able to fire.

The anchor is a literal fragment of the manuscript with ONE `%s` slot for the value rendered from the
artefact, so a wrong renderer AND a stale sentence both fail, and the failure names the sentence.

Usage:  python3 check_numbers.py                 (check the manuscript against the artefacts)
        python3 check_numbers.py --selftest      (check + prove every case can fail)
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, "manuscript.md")
_NUM = re.compile(r"\d+(?:\.\d+)?")


def load(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


class A(object):
    """Artefacts, loaded once."""

    def __init__(self):
        self.v1 = load("spike_v1_results.json")
        self.v2 = load("spike_v2_results.json")
        self.r2 = load("spike_real2_results.json")
        self.r3 = load("spike_real3_results.json")
        self.mm = load("spike_mm_results.json")
        self.lb = load("spike_lib_results.json")
        self.st = load("spike_struct_results.json")

    def band(self, fmt):
        b = self.r2["formats"][fmt]["band_spread_kappa1_1_1p5"]
        return b["lo"], b["hi"]


# --- renderers: artefact -> the string the manuscript must contain -------------------------------------------------

def r_band_global(a):
    los = [a.band(f)[0] for f in ("bf16", "fp16", "fp32")]
    his = [a.band(f)[1] for f in ("bf16", "fp16", "fp32")]
    return "[%.2f, %.2f]" % (min(los), max(his))


def r_band_spread(a):
    sp = [a.band(f)[1] / a.band(f)[0] for f in ("bf16", "fp16", "fp32")]
    return "%.1f-%.1fx" % (min(sp), max(sp))


def r_band_fmt(fmt):
    def f(a):
        lo, hi = a.band(fmt)
        return "%s %.2f-%.2f" % (fmt, lo, hi)
    return f


def r_beta(fmt):
    def f(a):
        fit = a.r2["formats"][fmt]["families"]["cancel"]["fits"]
        return "| %s | %.3f +- %.3f | %.3f +- %.3f | **%.3f +- %.3f** |" % (
            fmt, fit["all"]["beta"], fit["all"]["se"],
            fit["kappa1>=1.5"]["beta"], fit["kappa1>=1.5"]["se"],
            fit["kappa1>=10"]["beta"], fit["kappa1>=10"]["se"])
    return f


def r_r2_vals(a):
    v = [a.r2["formats"][f]["c_trend"]["fit_a_over_k1_plus_b"][2] for f in ("bf16", "fp16", "fp32")]
    return "`R^2` = %.2f / %.2f / %.2f" % tuple(v)


def r_order_fp32(a):
    p = a.r3["order_arm_pooled"]["fp32"]
    return "a median **%.1fx** (up to %.1fx) in fp32" % (p["c_spread_median"], p["c_spread_max"])


def r_order_fp16_row(a):
    p = a.r3["order_arm_pooled"]["fp16"]
    return "| fp16 constant-spread | %.2fx | %.1fx | %.1fx |" % (
        p["c_spread_min"], p["c_spread_median"], p["c_spread_max"])


def r_lane_median(a):
    r = [a.mm["formats"][f]["median_c"]["L4_rr"] / a.mm["formats"][f]["median_c"]["L1_rr"]
         for f in ("bf16", "fp16", "fp32")]
    return "%.0f-%.0f%%" % (100 * (1 - max(r)), 100 * (1 - min(r)))


def r_lane_worse(a):
    w = [100 * a.mm["formats"][f]["per_case_ratio"]["L4_rr"]["frac_worse"]
         for f in ("bf16", "fp16", "fp32")]
    return "%.0f-%.0f%%" % (min(w), max(w))


def r_lane_row(fmt):
    def f(a):
        pc = a.mm["formats"][fmt]["per_case_ratio"]["L4_rr"]
        return "| %s | %.1f%% | %.1f%% | %.1f%% |" % (
            fmt, 100 * pc["frac_better"], 100 * pc["frac_equal"], 100 * pc["frac_worse"])
    return f


def r_lib_medians(a):
    m = [a.lb["formats"][f]["median_c"] for f in ("fp16", "fp32", "fp64")]
    return "%.2f-%.2f" % (min(m), max(m))


def r_lib_slopes(a):
    s = ["%+.2f +- %.2f" % (a.lb["formats"][f]["n_slope"], a.lb["formats"][f]["n_slope_se"])
         for f in ("fp16", "fp32", "fp64")]
    return " / ".join(s)


def r_lib_row(fmt):
    def f(a):
        v = a.lb["formats"][fmt]
        return "| %s | %.4f | %.4f-%.4f | %.1f%% | %+.3f +- %.3f |" % (
            fmt, v["median_c"], v["c_min"], v["c_max"], 100 * v["frac_in_emulator_band"],
            v["n_slope"], v["n_slope_se"])
    return f


def r_struct_best(a):
    out = []
    for f in ("fp16", "fp32", "fp64"):
        d = a.st["formats"][f]
        best = [r for r in d["q1"] if r["name"] == d["best_by_exact_reproduction"]][0]
        out.append("%s %d/%d" % (f, best["exact"], d["n_library_rounds"]))
    return ", ".join(out)


def r_struct_chain(a):
    return "/".join(str([r for r in a.st["formats"][f]["q1"] if r["name"] == "chain"][0]["exact"])
                    for f in ("fp16", "fp32", "fp64"))


def r_pstar(a):
    return "to within %d bit" % a.v1["pstar_prediction_maxerr"]


def r_bulk(a):
    v = [a.r2["formats"][f]["families"]["cancel"]["fits"]["all"]["beta"] for f in ("bf16", "fp16", "fp32")]
    return "%.2f-%.2f" % (min(v), max(v))


def r_tail(a):
    v = [a.r2["formats"][f]["families"]["cancel"]["fits"]["kappa1>=10"]["beta"]
         for f in ("bf16", "fp16", "fp32")]
    return "%.2f-%.2f" % (min(v), max(v))


def r_eps_range(a):
    e = [p["eps_norm"] for p in a.v1["sweep_pstar"]]
    return "%dx range in `eps`" % int(max(e) / min(e))


# label, renderer, anchor template (one %s), what the number is
CASES = [
    ("band-global", r_band_global, "`c` measured in `%s` across three formats"),
    ("band-spread", r_band_spread, "varies **%s across matrices**"),
    ("band-bf16", r_band_fmt("bf16"), "(%s, fp16"),
    ("band-fp16", r_band_fmt("fp16"), ", %s,"),
    ("band-fp32", r_band_fmt("fp32"), "%s). An additive reading"),
    ("beta-bf16", r_beta("bf16"), "%s"),
    ("beta-fp16", r_beta("fp16"), "%s"),
    ("beta-fp32", r_beta("fp32"), "%s"),
    ("r2-trend", r_r2_vals, "%s for bf16/fp16/fp32, down from"),
    ("order-fp32", r_order_fp32, "%s"),
    ("order-fp16-row", r_order_fp16_row, "%s"),
    ("lane-median", r_lane_median, "reduce the median constant by **%s**"),
    ("lane-worse", r_lane_worse, "while making %s"),
    ("lane-bf16-row", r_lane_row("bf16"), "%s"),
    ("lane-fp16-row", r_lane_row("fp16"), "%s"),
    ("lane-fp32-row", r_lane_row("fp32"), "%s"),
    ("lib-medians", r_lib_medians, "The medians land at %s in all three formats"),
    ("lib-slopes", r_lib_slopes, "the slope is `%s`"),
    ("lib-fp16-row", r_lib_row("fp16"), "%s"),
    ("lib-fp32-row", r_lib_row("fp32"), "%s"),
    ("lib-fp64-row", r_lib_row("fp64"), "%s"),
    ("struct-best", r_struct_best, "(%s cases)"),
    ("struct-chain", r_struct_chain, "reproduces only %s."),
    ("pstar-1bit", r_pstar, "accurate **%s**"),
    ("eps-range", r_eps_range, "%s, with `c`"),
    ("beta-bulk-range", r_bulk, "the floor grows more slowly (%s)"),
    ("beta-tail-range", r_tail, "(exponent %s for"),
]


def run(scale=1.0):
    """Return (n_pass, n_fail, failures).  `scale` perturbs every rendered value, which is how the
    selftest proves each check can fire."""
    raw = io.open(MS, encoding="utf-8").read()
    # The manuscript is hard-wrapped, so a claim can straddle a line break.  Whitespace is a
    # PRESENTATION detail, not content: both sides are compared with runs collapsed, or the check
    # would report a defect for the way the paragraph was wrapped (Classes 178(b)/190).
    text = " ".join(raw.split())
    a = A()
    fails = []
    for label, render, anchor in CASES:
        val = render(a)
        if scale != 1.0:                      # perturb the NUMBER, keeping its shape
            val = _perturb(val, scale)
        want = " ".join((anchor % val).split())
        if want not in text:
            fails.append((label, val, anchor, want[:80]))
    return len(CASES) - len(fails), len(fails), fails


def _perturb(val, k):
    """Scale every NUMBER inside a rendered value, keeping the rendering precision.

    A hand-rolled sign-aware scanner treats `3.1-5.8x` as ONE token, fails to convert it, and leaves the
    string unchanged -- an INERT plant that reads as 'the check did not fire' (Class 189(a): the plant's
    INPUT is part of the plant).  Matching the digits alone has no such blind spot."""
    def f(m):
        s = m.group(0)
        dec = len(s.split(".")[1]) if "." in s else 0
        return "%.*f" % (dec, float(s) * k)
    return _NUM.sub(f, val)


def main():
    n, nf, fails = run()
    for label, val, anchor, want in fails:
        print("*** FAIL %-16s value=%r  not found: %r" % (label, val, want))
    print("check_numbers: %d/%d manuscript numbers match their artefacts" % (n, len(CASES)))
    return 0 if nf == 0 else 1


PLANT_SCALE = 1.5      # must move every RENDERED string, not merely the float behind it


def selftest():
    n, nf, _ = run()
    ok = nf == 0
    print("[%-32s] %s" % ("all numbers match", "ok" if ok else "*** FAIL ***"))
    a = A()
    _, nf2, fails2 = run(scale=PLANT_SCALE)
    fired = set(l for l, _v, _a, _w in fails2)
    for label, render, _anchor in CASES:
        val = render(a)
        moved = _perturb(val, PLANT_SCALE) != val
        if not moved:
            # An INERT plant is a defective CHECK, not a passing one (Classes 178(a)/189): scaling a
            # value whose rendering rounds it back to itself tests nothing.
            print("[%-32s] *** PLANT INERT: %r survives the plant ***" % (label, val))
            ok = False
        elif label in fired:
            print("[%-32s] FIRED" % ("plant:" + label,))
        else:
            print("[%-32s] *** DID NOT FIRE ***" % ("plant:" + label,))
            ok = False
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
