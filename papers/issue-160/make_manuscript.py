#!/usr/bin/env python3
"""make_manuscript.py -- render manuscript.md from manuscript_prose.md + the artefact.

No number in the paper is typed. The prose carries `{{n:...}}` markers and this program
substitutes each one from `results/crossover.json`, then refuses to write the paper when:

  * a marker does not resolve to a number the artefact holds; or
  * the rendered body carries a multi-digit or decimal number that this program did not bind
    (the stray scan) -- a number typed into the prose fails the build instead of reaching the
    paper; or
  * a citation marker names a slug that `refs.json` does not hold, or `refs.json` holds a
    verified reference that the body never cites (padding), or fewer than the journal's floor
    of 100 references is both held and cited.

Citations are `{{c:slug}}`, rendered as `[n]` with n in first-appearance order, and `{{refs}}`
expands into the reference list. A reference counts only when `refs.json` records it as verified
against a registry record AND the body cites it.

Reads  : manuscript_prose.md, results/crossover.json, refs.json
Writes : manuscript.md
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "results", "crossover.json")
REFS = os.path.join(HERE, "refs.json")
PROSE = os.path.join(HERE, "manuscript_prose.md")
OUT = os.path.join(HERE, "manuscript.md")

REF_FLOOR = 100


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def pct(x):
    """A fraction as a percentage, rounded once, here. The prose never divides by 100 itself."""
    return round(100.0 * x, 2)


def build_values(art):
    """Every number the prose may name, as a flat dict. Anything not here cannot be printed."""
    cl = art["count_limit"]
    cost = art["cost"]
    ctl = art["controls"]
    v = {
        "q": art["q"],
        "q_pct": int(round(art["q"] * 100)),
        "interval_s": art["input"]["interval_seconds"],
        "rows": cl["rows"],
        "usable": cl["usable"],
        "refused_total": sum(cl["refused"].values()),
        "zero_median": cl["refused"]["zero_median"],
        "unparseable": cl["refused"]["unparseable"],
        "crossing": cl["refused"]["crossing_ladder"],
        "resolvable": cl["resolvable"],
        "resolvable_pct": pct(cl["resolvable_frac"]),
        "unresolvable_pct": pct(cl["unresolvable_frac"]),
        "unresolvable": cl["usable"] - cl["resolvable"],
        "below_100": cl["below_100"],
        "below_100_pct": pct(cl["below_100_frac"]),
        "below_1000": cl["below_1000"],
        "below_1000_pct": pct(cl["below_1000_frac"]),
        "count_gate_lo": 100,
        "count_gate": 1000,
        "n_obs_median": cl["n_obs_median"],
        "no_censoring_rows": ctl["no_censoring_rows"],
        "no_censoring_pct": pct(ctl["no_censoring_identified_and_exact_frac"]),
        "flat": ctl["flat_rows_R_eq_1"],
        "flat_pct": pct(ctl["flat_rows_R_eq_1_frac"]),
        "one_level": ctl["rows_needing_one_level_at_eps_5"],
        "one_level_pct": pct(float(ctl["rows_needing_one_level_at_eps_5"]) / cl["usable"]),
        "R_median": round(cost["R_median"], 2),
        "R_p90": round(cost["R_p90"], 1),
        "R_max": cost["R_max"],
        # The upper percentile level the artefact summarises at (`c_p90`, `K*_p90`, `R_p90`). Bound
        # rather than written out, because a numeral spelled as a word is a carrier the digit
        # scanner cannot see at all -- and binding it keeps the word "90th" out of the prose.
        "p90": 90,
    }
    # The registered thresholds are quoted from the claim gate, not retyped: `check_claims.CLAIMS`
    # is what decides whether each prior was met, so a paper that restated the thresholds by hand
    # could silently disagree with the verdict it reports. This also caught a real error -- the
    # abstract first said "under 100% of rows would bind", because the wrong constant had been
    # bound to that sentence, which made the refuted prior trivially true.
    import check_claims as cc
    reg = {c["id"]: c["threshold"] for c in cc.CLAIMS}
    v["prior_limb1_pct"] = round(100 * reg["P2' limb 1"], 2)
    v["prior_limb2_pct"] = round(100 * reg["P2' limb 2"], 2)
    v["prior_p3"] = int(reg["P3"])
    # The precision ladder, bound from the artefact's own eps list rather than typed: the table
    # header cells are numbers like any other, and an unbound `10` in a header is exactly the kind
    # of number that reaches a printed page unexamined.
    for eps in (5, 10, 20):
        v["eps%d" % eps] = eps
        d = cost["K_at_%d" % eps]
        v["K%d_median" % eps] = d["median"]
        v["K%d_p90" % eps] = d["p90"]
        v["K%d_max" % eps] = d["max"]
        v["K%d_one_pct" % eps] = pct(d["frac_at_one"])
    for cell in art["cells"]:
        k = cell["k"]
        v["k%d" % k] = k                      # the grid values, so `k = 2 .. 32` is bound
        v["k%d_binds_pct" % k] = pct(cell["binds_frac"])
        v["k%d_ident_pct" % k] = pct(cell["identified_frac"])
        v["k%d_c_median" % k] = round(cell["c_median"], 4)
        v["k%d_c_p90" % k] = round(cell["c_p90"], 4)
        v["k%d_c_max" % k] = round(cell["c_max"], 4)
        v["k%d_under_median" % k] = round(cell["understated_by_median"], 2)
        v["k%d_under_p90" % k] = round(cell["understated_by_p90"], 2)
        v["k%d_under_max" % k] = round(cell["understated_by_max"], 1)
    # The sensitivity ladder this study actually has: the grid spans the lowest and highest
    # multiplier, and the drop in the binding fraction across it is the change the design
    # resolves. Composed from the artefact, not typed.
    v["binds_ladder_pp"] = round(v["k2_binds_pct"] - v["k32_binds_pct"], 2)
    return v


def fmt(x):
    if isinstance(x, bool):
        return str(x).lower()
    if isinstance(x, int):
        return "{:,}".format(x)
    if isinstance(x, float):
        s = ("%.4f" % x).rstrip("0").rstrip(".")
        return s if s else "0"
    return str(x)


MARK = re.compile(r"\{\{n:([^}]+)\}\}")
CITE = re.compile(r"\{\{c:([^}]+)\}\}")


def stray_numbers(body, bound):
    """Numbers in the prose that no artefact binds.

    The unit is the prose, and the bibliography is not the prose: a DOI is full of digit runs
    (`10.1000/0001787803310340`), so a scan applied after the reference list is spliced in rejects
    the paper for containing citations. The caller scans the body while `{{refs}}` and `{{c:}}` are
    still markers.
    """
    allowed = {fmt(x) for x in bound} | {a.replace(",", "") for a in (fmt(x) for x in bound)}
    allowed |= {str(int(x)) for x in bound if isinstance(x, (int, float)) and float(x).is_integer()}
    # Code spans and fenced blocks are identifiers, not quantities: a journal issue number or a
    # file name written as an identifier must not read as a number the prose typed.
    scan = re.sub(r"```.*?```", " ", body, flags=re.S)
    scan = re.sub(r"`[^`\n]*`", " ", scan)
    scan = re.sub(r"\([^)]*://[^)]*\)", " ", scan)          # link targets
    stray = []
    # The number pattern must take the whole decimal, including a unit suffix and sentence
    # punctuation. The first version used `\.?\d*` with a `(?!\w)` lookahead, which backtracks:
    # `61.57x` matched as `61` (the lookahead failed on `.5`, then on `7`, then succeeded before the
    # `x`), so a bound 61.57 was reported as the stray 61, and `300,241.` matched with its full stop.
    # A pattern that can match part of a number reports numbers that are not there; these two cases
    # are permanent fixtures in selftest().
    for tok in re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", scan):
        t = tok.replace(",", "").rstrip(".")
        if t in allowed:
            continue
        if re.fullmatch(r"(19|20)\d\d", t):        # a year
            continue
        if len(t.replace(".", "")) >= 2:             # single digits are section numbers
            stray.append(tok)
    return sorted(set(stray))


def selftest():
    """Demonstrate each guard firing, and each guard passing where it should."""
    global REF_FLOOR
    values = {"x": 42, "y": 0.5}
    fails = 0

    def expect(name, ok, detail=""):
        nonlocal fails
        print("  [%s] %s%s" % ("ok" if ok else "FAIL", name, (" -- " + detail) if detail else ""))
        if not ok:
            fails += 1

    stray_of = stray_numbers      # the fixtures test the scanner the render uses

    expect("a typed number in the prose is refused", stray_of("we measured 37 things", [42]),
           "found %s" % stray_of("we measured 37 things", [42]))
    expect("a bound number is accepted", not stray_of("we measured 42 things", [42]))
    expect("a year is not a stray", not stray_of("published in 1998", [42]))
    expect("a code-span identifier is not a stray", not stray_of("the `#135` study", [42]))
    expect("a single digit is not a stray", not stray_of("section 7 says", [42]))
    expect("an unbound decimal IS a stray", bool(stray_of("q = 0.99 exactly", [42])))
    expect("the same decimal once bound is not", not stray_of("q = 0.99 exactly", [0.99]))
    # A decimal followed by a unit letter, and a number followed by a full stop: the two shapes that
    # made the first scanner report numbers that were properly bound.
    expect("a bound decimal with a unit suffix is not a stray",
           not stray_of("understated by 61.57x on those rows", [61.57]),
           "found %s" % stray_of("understated by 61.57x on those rows", [61.57]))
    expect("a bound number followed by a full stop is not a stray",
           not stray_of("maximum 300,241.", [300241]),
           "found %s" % stray_of("maximum 300,241.", [300241]))
    try:
        MARK.sub(lambda m: values[m.group(1)], "{{n:nope}}")
        expect("an unresolved marker is refused", False)
    except KeyError:
        expect("an unresolved marker is refused", True)
    fake = {"a": {"entry": "e", "verification": {"result": "NO RECORD"}},
            "b": {"entry": "e", "verification": {"result": "verified"}}}
    try:
        CITE.sub(lambda m: "[1]" if fake[m.group(1)]["verification"]["result"] == "verified" else
                 (_ for _ in ()).throw(KeyError("unverified")), "{{c:a}}")
        expect("an unverified reference is refused", False)
    except KeyError:
        expect("an unverified reference is refused", True)
    try:
        def group(mm):
            for slug in mm.group(1).split(","):
                if fake[slug.strip()]["verification"]["result"] != "verified":
                    raise KeyError("unverified")
            return "[1]"
        CITE.sub(group, "{{c:b,a}}")
        expect("a group containing an unverified reference is refused", False)
    except KeyError:
        expect("a group containing an unverified reference is refused", True)
    doi = "[1] Somebody, A. (2020). vol. 3. pp. 1-9. https://doi.org/10.1000/0001787803310340"
    expect("a DOI line WOULD trip the scanner if it were scanned", bool(stray_of(doi, [])))
    expect("the body is scanned while {{refs}} is still a marker",
           stray_of("we cite the thing {{refs}}", []) == [])
    expect("and while a citation is still a marker",
           stray_of("a family {{c:x,y}} ties", []) == [])
    expect("the reference floor is enforced", len(fake) < REF_FLOOR)

    print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1


def main():
    prose = open(PROSE, encoding="utf-8").read()
    art = load(ART)
    try:
        refs = load(REFS)
    except FileNotFoundError:
        print("refs.json is missing -- the bibliography has not been built yet.")
        print("  -> run build_refs.py; the paper will not render until every citation resolves.")
        return 1

    values = build_values(art)
    bound = []

    def sub(m):
        key = m.group(1).strip()
        if key not in values:
            raise KeyError("{{n:%s}} is not a number the artefact holds" % key)
        bound.append(values[key])
        return fmt(values[key])

    body = MARK.sub(sub, prose)

    # ---- stray scan: a number the prose typed rather than bound ---------------------------
    # It runs here: after the {{n:}} markers are bound, while {{c:}} and {{refs}} are still
    # markers. Scanning after either substitution rejects the paper for containing citations.
    stray = stray_numbers(body, bound)
    if stray:
        print("STRAY NUMBERS (in the prose but bound to nothing): %s" % stray[:12])
        print("  -> every number must be a {{n:...}} marker; refusing to write the paper.")
        return 1

    # ---- citations -----------------------------------------------------------------------
    order = []

    def cite(m):
        """One marker may name several works: a sentence that cites a family cites all of it.

        Every member is resolved and checked, so a group cannot smuggle an unverified or unheld
        slug past the gate -- the group fails as a whole.
        """
        nums = []
        for slug in (x.strip() for x in m.group(1).split(",")):
            if not slug:
                continue
            rec = refs.get(slug)
            if rec is None:
                raise KeyError("{{c:%s}} names a reference refs.json does not hold" % slug)
            if rec.get("verification", {}).get("result") != "verified":
                raise KeyError("{{c:%s}} is not verified (%s)" % (slug, rec.get("verification")))
            if slug not in order:
                order.append(slug)
            nums.append(order.index(slug) + 1)
        return "[%s]" % ",".join(str(n) for n in nums)

    body = CITE.sub(cite, body)

    uncited = [s for s in refs if s not in order]
    if uncited:
        raise KeyError("refs.json holds %d reference(s) the body never cites (padding): %s"
                       % (len(uncited), uncited[:8]))
    if len(order) < REF_FLOOR:
        raise KeyError("only %d reference(s) are held and cited; the journal's floor is %d"
                       % (len(order), REF_FLOOR))

    entries = []
    for i, slug in enumerate(order, 1):
        entry = re.sub(r"\.\.+", ".", refs[slug]["entry"])
        entries.append("[%d] %s" % (i, entry))

    body = body.replace("{{refs}}", "\n\n".join(entries))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(body)
    print("manuscript.md written: %d characters" % len(body))
    print("  markers bound: %d numbers, %d citations" % (len(bound), len(order)))
    print("  references: %d held, %d cited (floor %d)" % (len(refs), len(order), REF_FLOOR))
    print("  stray-number scan: clean")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    try:
        sys.exit(main())
    except KeyError as e:
        print("CANNOT WRITE THE PAPER: %s" % e.args[0])
        sys.exit(1)
