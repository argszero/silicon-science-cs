#!/usr/bin/env python3
"""#93 R427 -- section 5's numbers, recomputed from the instruments that own them.

Why this file exists.  Section 5 is the paper's results, and every number in it is an instrument output.  Writing
it by hand produced three defects that a reader would have had to catch: a substitution-gap table whose values were
wrong by a factor of two AND carried the wrong sign, and a cross-channel identity that was simply false (asserted
to 9e-17, actually off by 0.81).  All three were found by *recomputing* from the record rather than by reading the
prose, which is the only reason to keep this script: it makes that recomputation repeatable, so the next round's
edit to section 5 cannot silently drift from the instruments.

What it reads.  Each entry names a CLAIM (the quantity as a phrase), a SOURCE (the instrument function or the
record field that computes it), and the resolution the prose writes it at; then it asks whether the section states
that value.  It reports `MISSING` (no token in the section states the computed value -- a claim that lost its
carrier) and `NOT RUN` (an instrument or the section cannot be read: an unreadable object has not been checked and
must not look like a pass).  It does NOT detect a wrong number sitting in the claim's own slot: this reading has no
anchor from a phrase to a sentence, so `0.12` written where `0.012` belongs is reported only if nothing else in the
section states `0.012`.  That limit is why the battery plants a claim's carriers rather than a single occurrence --
the strongest per-claim statement this reading supports is "the section carries the value, and removing every token
that carries it makes the claim fail".

Two rules do the work, and both were found by breaking them.  (1) Resolution: a token states the claim only if it
is at least as precise as the claim; without that floor `0` states every quantity below 0.5, and a section
consisting of the single token `0` satisfied 22 of the 51 claims then on the list (measured, R427) -- a one-token
page passing a check that exists to notice missing evidence.  (2) Reachability: a claim's verdict must depend on
the section carrying it, one plant per claim, or the claim is decoration.

Run:  /usr/bin/python3 verify_s5.py            (recompute and compare against the manuscript)
      /usr/bin/python3 verify_s5.py --selftest (a plant per claim + the alphabet control)
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCT = os.path.join(HERE, "manuscript.md")
PART5 = os.path.join(HERE, "manuscript", "part5.md")
sys.path.insert(0, HERE)


def section_5(text):
    """Section 5 of the product: the `## 5 ` heading up to the next top-level heading.

    The package ships the PRODUCT, not the parts, so this is the object the check reads when it is shipped -- and
    reading the product is the stronger reading in any case (a part that never reached the manuscript would other-
    wise be checked in its own favour).  An empty slice is reported as NOT RUN rather than as a pass.
    """
    m = re.search(r"(?m)^## 5\b.*$", text)
    if not m:
        return ""
    rest = text[m.end():]
    n = re.search(r"(?m)^## ", rest)
    return text[m.start():m.end() + (n.start() if n else len(rest))]


def source():
    if os.path.exists(PRODUCT):
        return section_5(io.open(PRODUCT, encoding="utf-8").read())
    return io.open(PART5, encoding="utf-8").read() if os.path.exists(PART5) else ""


def load():
    import gate_v0 as V0
    import gate_v1 as V1
    recs = {}
    for tag in ("v1", "v2", "v3", "v4", "v5", "v6"):
        p = os.path.join(HERE, "gate_%s_results.json" % tag)
        recs[tag] = json.loads(io.open(p, encoding="utf-8").read())
    return V0, V1, recs


def claims(V0, V1, r):
    """(label, value, decimals, kind) -- value recomputed here, decimals = the prose's resolution.

    `kind` is `"value"` (a float the prose writes at `decimals` places) or `"count"` (an exact integer).  The
    distinction is the resolution rule's two-sided half, and it was found by running this check: the cost ratio
    at which the misrepresentation bar vanishes is `109.99999999999999` in the record and is written `110` in the
    prose, so demanding exact float equality reported a claim the section DOES state.  Rounding is the honest
    comparison for a value; equality is the honest comparison for a count (`29` must not cover `29.6`).
    """
    b = dict(V0.DEFAULT)
    out = []
    def add(item):
        """Accept 3-tuples (label, value, decimals) as `value` claims and 4-tuples with an explicit kind."""
        if len(item) == 3:
            out.append(tuple(item) + ("value",))
        else:
            out.append(tuple(item))
    # 5.1 -- the two bars and their gap
    add(("b* misrepresentation", V1.bstar_closed(b, "mismatch"), 4))
    add(("b* laundering", V1.bstar_closed(b, "substitution"), 4))
    add(("the gap between the bars", V1.bstar_closed(b, "substitution") - V1.bstar_closed(b, "mismatch"), 3))
    # 5.1 -- the two channels' zero-coverage behaviour (both grids)
    for bb in (1.0, 0.5, 0.0):
        gap = V1.value_closed(b, "substitution", bb, 0.0) - V1.value_closed(b, "none", bb, 0.0)
        add(("laundering gap at zero coverage, b=%s" % bb, gap, 4))
    for eta in (0.0, 0.5, 1.0):
        p = dict(b, eta=eta)
        v = V1.value_closed(p, "substitution", 0.0, 0.0)
        add(("laundering gap at b=0, eta=%s" % eta, v, 4))
    add(("screening slope at b=1", V1.slope_closed(b, "mismatch", 1.0), 6))
    add(("misrepresentation slope at b=0", V1.slope_closed(b, "mismatch", 0.0), 6))
    add(("laundering slope at b=0", V1.slope_closed(b, "substitution", 0.0), 6))
    # 5.2 -- the ladder and the headline count
    tbl = {x["design"]: x for x in r["v2"]["design_table"]}
    for d in ("D1", "D2", "D3", "D4", "D5"):
        add(("%s value" % d, tbl[d]["value"], 4))
    hs = r["v3"]["headline_sensitivity"]
    add(("harmful (cell, design) readings", len(hs["harmful"]), 0, "count"))
    add(("grid cells with a harmful gate", len(hs["cells_with_a_harmful_gate"]), 0, "count"))
    add(("gated designs harmful somewhere", len(hs["designs_harmful_somewhere"]), 0, "count"))
    add(("weakest instance as a fraction of the no-gate loss", hs["min_margin_frac"], 4))
    add(("D2 - D1, the rendering's own worth", tbl["D2"]["value"] - tbl["D1"]["value"], 3))
    # 5.3 -- the axis ratio
    fc = [c for c in r["v4"]["checks"] if c["id"] == "F-crossover"][0]
    add(("crossover, misrepresentation", fc["cross"]["mismatch"]["predicted"], 6))
    add(("crossover, laundering (predicted)", fc["cross"]["substitution"]["predicted"], 2))
    add(("axis ratio at b=1, laundering", r["v4"]["pb2_verdict"]["substitution"]["1.0"]["ratio"], 4))
    # 5.4 -- the interval and the cost-ratio law
    d5 = {(x["cell"], x["channel"]): x for x in r["v5"]["readings"] if x["family"] == "adjacent"}
    for ch in ("mismatch", "substitution"):
        add(("%s interval low" % ch, d5[("defaults", ch)]["fieller"]["lo"], 4))
        add(("%s interval high" % ch, d5[("defaults", ch)]["fieller"]["hi"], 4))
    add(("interval width, misrepresentation", d5[("defaults", "mismatch")]["fieller"]["width"], 4))
    add(("interval width, laundering", d5[("defaults", "substitution")]["fieller"]["width"], 4))
    add(("in-axis readings covered", r["v5"]["C7_calibration"]["fieller_covered"], 0, "count"))
    add(("in-axis readings", r["v5"]["C7_calibration"]["denominator"], 0, "count"))
    add(("worst departure from the width law (percent)", 100.0 * r["v5"]["C4_width_law"]["worst_dev_in_regime"], 1))
    for row in r["v5"]["C5_scaling"]["rows"]:
        add(("width ratio at 4x, %s" % row["channel"], row["ratio"], 4))
    add(("the crossover cost ratio R_c", r["v6"]["C5_crossover"]["R_c_closed"], 3))
    add(("the cost ratio where the laundering bar saturates",
         r["v6"]["limits"]["substitution_limit"], 4))
    add(("the cost ratio where the misrepresentation bar vanishes",
         r["v6"]["limits"]["mismatch_R_zero"], 0))
    for row in r["v6"]["C1_law"]["rows"]:
        if row["channel"] == "mismatch" and row["R"] in (8.0, 50.0):
            add(("misrepresentation bar at R=%s" % row["R"], row["closed"], 4))
        if row["channel"] == "substitution" and row["R"] in (8.0, 50.0):
            add(("laundering bar at R=%s" % row["R"], row["closed"], 4))
    for ch in ("mismatch", "substitution"):
        for v in r["v6"]["C3_rate"][ch]["differences_ratio"]:
            add(("rate ladder ratio, %s" % ch, v, 4))
    # 5.5 -- the affineness resolution and the fatigue floor
    add(("worst relative second difference", r["v1"]["curvature"]["worst_relative"], 2))
    add(("curvature cells", r["v1"]["curvature"]["n"], 0, "count"))
    add(("the fatigue floor", r["v1"]["P5_fatigue"]["b_floor_closed"], 6))
    add(("interior cells above the floor", r["v1"]["P5_fatigue"]["n_above"], 0, "count"))
    add(("corner cells below the floor", r["v1"]["P5_fatigue"]["n_below"], 0, "count"))
    return out


NUMBER = r"[-−]?\d+\.\d+(?:[eE][-−]?\d+)?|(?<![\d.])[-−]?\b\d+\b(?![\d.])"
PARSE = re.compile(r"(?P<sign>[-−]?)(?P<int>\d+)(?:\.(?P<frac>\d+))?(?:[eE](?P<exp>[-−]?\d+))?$", re.U)


def finditer(text):
    return re.finditer(NUMBER, text)


def toks(text):
    return sorted(set(m.group(0) for m in finditer(text)))


def stated(tok, value, decimals, kind="value"):
    """Does the prose write `value` at `decimals` places?  A token COARSER than the claim does NOT state it.

    Two rules, two directions of the same mistake.  A `count` demands equality at every resolution (a token that
    rounds a count is not the count).  A `value` is compared at the resolution the TOKEN carries, because rounding
    is what prose does -- but only if the token is at least as precise as the claim, and that floor is the whole
    reason this function is not one line: without it `0` states every quantity smaller than 0.5, and a section
    consisting of the single token `0` satisfied 22 of the 51 claims below (measured, R427).  A check that a
    one-token page can talk past is not a check on the section.
    """
    m = PARSE.match(tok)
    if not m:
        return False
    got = float(tok.replace("−", "-"))
    if m.group("exp") is not None:                              # scientific notation: precision = significant digits
        sig = len(m.group("int").lstrip("0")) + len(m.group("frac") or "")
        d = max(sig - 1, 0)
    else:
        d = len(m.group("frac") or "")
    if kind == "count":
        return got == value
    if d < decimals:
        return False
    return got == round(value, d)


def plant(text, value, decimals, kind):
    """Every token that STATES the claim, replaced by a non-number.  Returns (new_text, how_many_removed).

    The plant has to remove all of them, not the first: a claim's number is often written twice (prose and table),
    and a check that reads the section as a whole stays green when one carrier survives -- which says nothing about
    whether the claim was plantable.  Written in the check's own alphabet, so the plant cannot drift from it.
    """
    hits = [m.span() for m in finditer(text) if stated(m.group(0), value, decimals, kind)]
    out, last = [], 0
    for a, b in hits:
        out.append(text[last:a]); out.append("X"); last = b
    out.append(text[last:])
    return "".join(out), len(hits)


def report(text):
    """Recompute every claim and ask whether the prose states it.  Returns (rows, failures, not_run)."""
    try:
        V0, V1, recs = load()
    except Exception as exc:                                    # an unreadable instrument is NOT a pass
        return [], [], "cannot read the instruments: %r" % exc
    if not text:
        return [], [], "the section could not be read"
    rows, bad = [], []
    have = toks(text)
    for label, value, dec, kind in claims(V0, V1, recs):
        ok = any(stated(t, value, dec, kind) for t in have)
        rows.append((label, round(value, dec), "stated" if ok else "MISSING"))
        if not ok:
            bad.append("%s: computed %r at %d decimal place(s) as a %s; the section states no such number"
                       % (label, round(value, dec), dec, kind))
    return rows, bad, None


def main():
    text = source()
    rows, bad, notrun = report(text)
    if notrun:
        print("NOT RUN -- %s" % notrun)
        return 2
    for label, value, verdict in rows:
        print("  %-56s %-14s %s" % (label[:56], value, verdict))
    print("SECTION 5 NUMBERS: %s -- %d claim(s), %d missing" % ("PASS" if not bad else "FAIL",
                                                               len(rows), len(bad)))
    for b in bad:
        print("  " + b)
    rc = 0 if not bad else 1
    if "--selftest" in sys.argv:
        try:
            V0, V1, recs = load()
        except Exception as exc:
            print("BATTERY NOT RUN -- cannot read the instruments: %r" % exc)
            return 2
        allclaims = claims(V0, V1, recs)
        fired, inert = 0, []
        for label, value, dec, kind in allclaims:
            probe, n = plant(text, value, dec, kind)
            if n == 0:
                inert.append((label, "the section carries no token that states it"))
                continue
            rows2, bad2, nr2 = report(probe)
            if nr2 is not None:
                inert.append((label, "the probe could not be read: %s" % nr2))
            elif [b for b in bad2 if b.startswith(label + ":")]:
                fired += 1
            else:
                inert.append((label, "PLANT SURVIVED: %d token(s) removed, the claim is still counted as stated"
                              % n))
        print("BATTERY: %d of %d claim(s) fired when every token stating them was removed"
              % (fired, len(allclaims)))
        for l, why in inert:
            print("  NOT PLANTABLE: %s -- %s" % (l, why))
        if fired != len(allclaims):
            rc = 1

        # ALPHABET CONTROL.  The check's verdict is read off a token set, so the token set has to exclude the
        # numbers that state nothing.  Before the precision floor was added, `0` on its own satisfied 22 of the 51
        # claims: the check reported a section full of evidence for a one-token page, because agreeing at ZERO
        # decimal places is something `0` does with every quantity below 0.5.  This control is that page, and it
        # must be empty of claims.
        alphabet, loose = "0 1 2 10 0.5", []
        rows3, bad3, nr3 = report(alphabet)
        if nr3 is not None:
            print("ALPHABET CONTROL NOT RUN -- %s" % nr3)
            rc = 1
        elif len(rows3) - len(bad3):
            loose = [l for l, v, verdict in rows3 if verdict == "stated"]
            print("ALPHABET CONTROL FAILED -- %d of %d claim(s) are satisfied by %r: %s"
                  % (len(loose), len(rows3), alphabet, ", ".join(loose[:6])))
            rc = 1
        else:
            print("ALPHABET CONTROL: 0 of %d claim(s) satisfied by %r" % (len(rows3), alphabet))
    return rc


if __name__ == "__main__":
    sys.exit(main())
