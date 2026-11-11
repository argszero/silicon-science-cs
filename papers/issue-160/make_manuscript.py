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


# --- bibliography author form (review minor 4) ------------------------------------------------
# A registry record is not the form an entry prints. Three of this trace's references arrive with the
# family name in capitals (`GENTLEMAN, D. R.`) and one arrives with a name SUFFIX in the family field
# (`family: "III"`, `given: "James Pickands"`), because DOI metadata stores what the publisher
# deposited. Printing the stored field is faithful and wrong: the work is indexed under a suffix
# rather than under its author. Normalisation happens HERE, at render, so `refs.json` keeps the
# registry's form and a reader can always see what was actually deposited.
AUTHOR_FIXUPS = {
    # A suffix cannot be re-cased into a surname: no rule recovers "Pickands" from "III", so this one
    # is an explicit override and the only place in the package where a name is asserted rather than
    # derived. The published work is Pickands (1975), Annals of Statistics 3:119-131.
    "pickands-1975": ("III, J. P.", "Pickands, J."),
}
# An all-caps family name is a deposited-form artefact: at least three capitals followed by a comma.
# Deliberately narrow -- an ALL-CAPS TITLE must not be touched (titles sit after the year, and the
# normaliser only ever sees the author segment), and a single initial (`J.`) is not a name.
ALLCAPS_FAMILY = re.compile(r"(?:^|[.\s,;])([A-Z][A-Z'\u2019\-]{2,})(?=,)")
_YEAR = re.compile(r"\((\d{4})\)")
_SUFFIXES = ("II", "III", "IV", "V")


def _split_at_year(entry):
    """(author segment, year, rest) -- so normalisation can never touch a title."""
    m = _YEAR.search(entry)
    if not m:
        return entry, "", ""
    return entry[:m.start()], entry[m.start():m.end()], entry[m.end():]


# A slot the registry stored as a null. `10.1007/springerreference_65446` is a reference-entry with
# no issued date, and the assembler wrote `(None)` into the entry, which then printed on the page:
# a placeholder standing where a reader expects a year. Review round 2, minor 3 named one entry; the
# census over all 120 found three (also `smith-1990` and `tamer-2010`), which is why this is a rule
# rather than a fix to one line.
NULL_SLOTS = re.compile(r"\(\s*(?:None|null|NULL|nan|NaN)\s*\)|(?<![\w.])None(?![\w.])")


def strip_null_slots(entry):
    """The entry with null slots removed, and how many were removed.

    The absence is PRINTED by the census (`check_claims.py`) rather than rendered as a slot: an entry
    whose record carries no year prints like the entries whose record carries no author -- with the
    field simply not there. The count is what makes that a decision and not a deletion.
    """
    cleaned, n = NULL_SLOTS.subn("", entry)
    if n:
        # A slot that stood between two bits leaves their join behind it: `Manski, C. F. (None). p`
        # becomes `Manski, C. F. . p` and `(None). Order Statistics` becomes `. Order Statistics`.
        # The separator is part of the slot, so it goes with it -- otherwise the fix trades a visible
        # placeholder for a punctuation defect in the same position.
        cleaned = re.sub(r"\s+\.", ".", cleaned)
        cleaned = re.sub(r"^\s*\.\s*", "", cleaned)
        # The bit's own closing stop now sits next to the join's: `C. F.` + `.` reads `C. F..`.
        cleaned = re.sub(r"\.\.+", ".", cleaned)
    return re.sub(r"\s{2,}", " ", cleaned).strip(), n


def rendered_entry(ref, slug=""):
    """The entry as it is printed: the registry's stored form in, house form out."""
    entry = ref["entry"] if isinstance(ref, dict) else str(ref)
    entry, _dropped = strip_null_slots(entry)
    old, new = AUTHOR_FIXUPS.get(slug, (None, None))
    if old:
        entry = entry.replace(old, new, 1)
    head, year, tail = _split_at_year(entry)

    def _recase(m):
        name = m.group(1)
        if name in _SUFFIXES:                 # a suffix is not a family name
            return m.group(0)
        return m.group(0).replace(name, name[0] + name[1:].lower())

    entry = ALLCAPS_FAMILY.sub(_recase, head) + year + tail
    return re.sub(r"\.\.+", ".", entry)


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
    # The cost law's CHECK (registered criterion (ii)). `K` in the law counts the gaps between timed
    # levels, so a certification needs one more level than the law's own number; the artefact settles
    # which count attains `eps` on EVERY row, and both are bound here so the distinction is printable
    # and neither can be quoted in place of the other.
    cc = art["cost_check"]
    for eps in (5, 10, 20):
        tag = "eps_%d" % eps
        blk = cc["by_eps"][tag]
        held = cc["holds_at"][tag]
        v["K%d_levels" % eps] = blk[held]["levels_median"]
        v["K%d_levels_p90" % eps] = blk[held]["levels_p90"]
        # Review round 2, minor 1: the verdict line of a registered prior printed the law's `K`
        # under the word "levels", one below the checked price the abstract prints three paragraphs
        # earlier. Both quantities are bound here under names that say which is which, so a sentence
        # can state the pair instead of quoting one of them as the other.
        v["K%d_gap_median" % eps] = blk["at_K"]["levels_median"]
        v["K%d_attained_pct" % eps] = pct(blk[held]["achieved_median"])
        v["K%d_resid_max" % eps] = blk[held]["residual_max"]
        v["K%d_resid_at_K" % eps] = blk["at_K"]["residual_max"]
        v["K%d_over_pct" % eps] = pct(blk["at_K"]["rows_over_eps_frac"])
    v["recon_rows"] = cc["reconstruction"]["rows"]
    v["recon_draws"] = cc["reconstruction"]["draws_per_row"]
    # The draw-based limb has a RESOLUTION, and its worst row is a fact about that resolution rather
    # than about the ladder: a q-quantile estimated from this many draws rests on only
    # `draws * (1-q)` observations above it. Bound so the prose reports all three and cannot quote
    # the median as though it were the worst case.
    rec = cc["reconstruction"]
    v["recon_err_median_pct"] = pct(rec["rel_err_median"])
    v["recon_err_p90_pct"] = pct(rec["rel_err_p90"])
    v["recon_err_max_pct"] = pct(rec["rel_err_max"])
    v["recon_tail_draws"] = int(round(rec["draws_per_row"] * (1.0 - art["q"])))
    # Review minor 2: the step count is READ off the script that runs them, not remembered. The
    # manuscript said "six" while the script ran eight; a number derived from its own object cannot
    # go stale, and `check_claims.py` re-derives the same count through the same function. Imported
    # here rather than at module scope: `check_claims` imports this module to re-apply the renderer's
    # own author form, so a top-level import would be a cycle, and one function must serve both.
    import check_claims
    v["steps"] = check_claims.reproduction_steps()
    # Review question 2: is the refuted margin an artefact of the reconstruction? The same measurement
    # over coarser ladders, so the prose can state the spread instead of asserting robustness.
    ks = art["knot_sweep"]
    v["knot_sweep_sets"] = len(ks["sets"])
    v["knot_sweep_min_pct"] = pct(min(s["binds_frac"] for s in ks["sets"]))
    v["knot_sweep_max_pct"] = pct(max(s["binds_frac"] for s in ks["sets"]))
    v["knot_sweep_full_pct"] = pct([s for s in ks["sets"] if s["knots"] == ks["full_knots"]][0]
                                   ["binds_frac"])
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
    # How far the refutation clears the threshold it refutes, in percentage points, and the spread the
    # reconstruction alone can produce. Both are printed because the second is larger than the first:
    # a reader is owed that comparison, not the margin on its own.
    v["binds_margin_pp"] = round(v["k32_binds_pct"] - v["prior_limb2_pct"], 2)
    v["knot_sweep_span_pp"] = round(v["knot_sweep_max_pct"] - v["knot_sweep_min_pct"], 2)
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

    # 10. a null slot is a decision, not a slot (review round 2, minor 3).
    cleaned, n = strip_null_slots("Manski, C. F. (None). partial identification. Palgrave.")
    expect("a null year slot is removed and counted", n == 1 and "(None)" not in cleaned,
           "%d removed -> %r" % (n, cleaned[:60]))
    expect("removing a slot does not leave its join behind",
           cleaned == "Manski, C. F. partial identification. Palgrave.", cleaned)
    headless, n2 = strip_null_slots("(None). Order Statistics. SpringerReference.")
    expect("a slot at the head of an entry leaves no leading stop",
           n2 == 1 and headless.startswith("Order Statistics"), headless[:50])
    expect("an entry with no null slot is returned unchanged",
           strip_null_slots("Shahrad, M. (2020). Serverless in the Wild.")[1] == 0)

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
    dropped_year = 0
    for i, slug in enumerate(order, 1):
        _clean, _n = strip_null_slots(refs[slug]["entry"] if isinstance(refs[slug], dict)
                                      else str(refs[slug]))
        dropped_year += 1 if _n else 0
        entries.append("[%d] %s" % (i, rendered_entry(refs[slug], slug)))

    # A null that reaches the page has to be a decision, not a slot. `strip_null_slots` is the
    # decision; this is what makes it one -- an entry that still carries a null sentinel after the
    # pass would print a placeholder where a reader expects a field, and the paper is refused instead
    # of shipped with one (review round 2, minor 3).
    leftover = [e for e in entries if NULL_SLOTS.search(e) or "None" in e]
    if leftover:
        print("NULL SLOT in the rendered bibliography: %r" % leftover[0][:90])
        print("  -> a record field with no value must print as an absent field, never as a slot;")
        print("     refusing to write the paper.")
        return 1

    body = body.replace("{{refs}}", "\n\n".join(entries))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(body)
    print("manuscript.md written: %d characters" % len(body))
    print("  markers bound: %d numbers, %d citations" % (len(bound), len(order)))
    print("  references: %d held, %d cited (floor %d)" % (len(refs), len(order), REF_FLOOR))
    print("  stray-number scan: clean")
    print("  null slots: %d entry(ies) printed without the field their record stored as null"
          % dropped_year)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    try:
        sys.exit(main())
    except KeyError as e:
        print("CANNOT WRITE THE PAPER: %s" % e.args[0])
        sys.exit(1)
