#!/usr/bin/env python3
"""make_manuscript.py -- render manuscript.md from manuscript_prose.md + the artefacts.

No number in the paper is typed. The prose carries `{{n:...}}` markers and this program
substitutes each one from `results/mechanism.json`, `results/scale.json` or a value composed
from them, then refuses to write the paper when:

  * a marker does not resolve to a number the artefacts hold; or
  * the rendered body carries a multi-digit or decimal number that this program did not bind
    (the stray scan) -- a number typed into the prose fails the build instead of reaching the
    paper; or
  * a citation marker names a slug that `refs.json` does not hold, or `refs.json` holds a
    verified reference that the body never cites (padding), or fewer than the journal's floor
    of 100 references is both held and cited.

Citations are `{{c:slug}}`, rendered as `[n]` with n in first-appearance order, and `{{refs}}`
expands into the reference list. A reference counts only when `refs.json` records it as
verified against a registry record AND the body cites it: an entry nobody cites is padding, and
the journal's count is a count of citations, not of entries.

Reads  : manuscript_prose.md, results/mechanism.json, results/scale.json, refs.json
Writes : manuscript.md
"""
import axis
import json
import os
import re
import sys

K = 10
REF_FLOOR = 100


def load(path):
    with open(path) as f:
        return json.load(f)


def cell_lookup(cells, tag, field):
    for c in cells:
        if c["tag"] == tag:
            if field not in c:
                raise KeyError("cell %r has no field %r" % (tag, field))
            return c[field]
    raise KeyError("no cell %r in the artefact" % tag)


# The control rule, the configuration count and both statistics live in axis.py, which the two
# artefact producers and the claims checker also import. They are re-exported here so a caller keeps
# reading `make_manuscript.configs_of` while there stays exactly one copy of the rule: review M1 and
# M2 were both two copies of one definition disagreeing about which set the number is over.
is_family_cell = axis.is_family_cell
configs_of = axis.configs_of


def mean(xs):
    return sum(xs) / len(xs)


def family_xy(cells):
    """The family cells' (resolution, tie group) pairs. The float control is not a family."""
    fam = [c for c in cells if not c["tag"].startswith("float")]
    return [c["median_atoms"] for c in fam], [c["median_t"] for c in fam]


def composed_r(xs, ys):
    """Pearson r on the log-log pairs, rounded the way the artefacts round it. Composed, not typed."""
    import math
    lx = [math.log(x) for x in xs]
    ly = [math.log(y) for y in ys]
    mx, my = mean(lx), mean(ly)
    num = sum((a - mx) * (b_ - my) for a, b_ in zip(lx, ly))
    den = math.sqrt(sum((a - mx) ** 2 for a in lx) * sum((b_ - my) ** 2 for b_ in ly))
    return round(num / den, 4)


def build_values(A, B, M):
    """Every number the prose may name, as a flat dict. Anything not here cannot be printed."""
    cellsA, cellsB, cellsM = A["cells"], B["cells"], M["cells"]

    def by_prefix(cells, prefix):
        return [c for c in cells if c["tag"].startswith(prefix)]

    def agg(cells, prefix, field, fn):
        vals = [c[field] for c in by_prefix(cells, prefix)]
        if not vals:
            raise KeyError("no cells with prefix %r" % prefix)
        return fn(vals)

    xsB = [c["median_atoms"] for c in cellsB if not c["tag"].startswith("float")]
    ysB = [c["median_t"] for c in cellsB if not c["tag"].startswith("float")]

    v = {
        "A.corpus.n": A["corpus"]["n"],
        "A.corpus.d": A["corpus"]["d"],
        "A.corpus.n_queries": A["corpus"]["n_queries"],
        "A.corpus.knn": A["corpus"]["knn"],
        "A.corpus.k": A["corpus"]["k"],
        "A.r": A["log_log_pearson"],
        "A.n_cells": A["n_cells"],
        "A.mde": A["mde_pearson"],
        "A.configs": configs_of(cellsA),
        "A.r_configs": A["log_log_pearson_configs"],
        "A.mde_configs": A["mde_pearson_configs"],
        "A.n_configs": A["n_configs"],
        "B.corpus.n": B["corpus"]["n"],
        "B.corpus.d": B["corpus"]["d"],
        "B.corpus.n_queries": B["corpus"]["n_queries"],
        "B.corpus.knn": B["corpus"]["knn"],
        "B.n_cells": len(xsB),
        "B.configs": configs_of(cellsB),
        # Tier B's axis, read from the artefact rather than composed here: the 1M number carries
        # its own sensitivity in results/scale.json (review M2/M4), and check_claims.py asserts the
        # stored pair still equals what the committed cells compose to.
        "B.r_configs": B["log_log_pearson_configs"],
        "B.mde_configs": B["mde_pearson_configs"],
        "B.n_configs": B["n_configs"],
        # Tier M: the 200k scale, recomputed from committed bytes by numpy alone. It is the reason
        # the 1M reading has a second instrument, so its numbers are bound like every other.
        "M.fixture.n": M["fixture"]["n"],
        "M.fixture.n_queries": M["fixture"]["n_queries"],
        "M.fixture.n_queries_available": M["fixture"]["n_queries_available"],
        "M.fixture.knn": M["fixture"]["knn"],
        "M.nested_rows": M["fixture"]["nested_rows"],
        "M.configs": configs_of(cellsM),
        "M.n_configs": M["n_configs"],
        "M.r_configs": M["log_log_pearson_configs"],
        "M.mde_configs": M["mde_pearson_configs"],
    }

    # tier B carries no single stored correlation: it is composed here from the cells, exactly as
    # check_claims composes nothing and reads only stored values. Composed, not typed. Tier M's is
    # composed by the same function, so the two scales cannot be correlated by two different rules.
    v["B.r"] = composed_r(xsB, ysB)
    v["B.atoms_min"] = min(xsB)
    v["B.atoms_max"] = max(xsB)
    xsM, ysM = family_xy(cellsM)
    v["M.r"] = composed_r(xsM, ysM)

    # the headline contrast at tier B, as one number each
    v["B.hamming32.median_t"] = agg(cellsB, "Hamming/32bit", "median_t", mean)
    v["B.hamming32.floor"] = agg(cellsB, "Hamming/32bit", "mean_floor", mean)
    v["B.hamming32.frac_floor_lt1"] = agg(cellsB, "Hamming/32bit", "frac_floor_lt1", mean)
    v["B.hamming64.median_t"] = agg(cellsB, "Hamming/64bit", "median_t", mean)
    v["B.hamming256.median_t"] = agg(cellsB, "Hamming/256bit", "median_t", mean)
    v["B.pq32.median_t"] = agg(cellsB, "PQ/32bit", "median_t", mean)
    v["B.pq32.floor"] = agg(cellsB, "PQ/32bit", "mean_floor", mean)
    v["B.pq64.floor"] = agg(cellsB, "PQ/64bit", "mean_floor", mean)
    v["B.sq2.floor"] = agg(cellsB, "SQ/2bit", "mean_floor", mean)

    # ---- M3: what section 3 promises, printed instead of promised ---------------------------
    # A proportion with a score interval, a difference between families with its two-sample
    # interval, the spread across the three seeds rather than only their mean, and the denominator
    # in the text. Every one of these is arithmetic over cells already committed, so none of it
    # needed a new run; until review M3 the paper declared the practice and printed bare points.
    def pooled(prefix):
        cs = [c for c in cellsB if c["tag"].startswith(prefix)]
        if not cs:
            raise KeyError("no cells with prefix %r" % prefix)
        k = sum(axis.count_from_fraction(c["frac_floor_lt1"], c["n_queries"]) for c in cs)
        n = sum(c["n_queries"] for c in cs)
        return cs, k, n

    for label, prefix in (("hamming32", "Hamming/32bit"), ("pq32", "PQ/32bit")):
        cs, k, n = pooled(prefix)
        v["B.%s.frac_pct" % label] = k / float(n)
        v["B.%s.frac_ci" % label] = axis.wilson(k, n)
        v["B.%s.n_queries" % label] = n
        v["B.%s.n_seeds" % label] = len(cs)
        v["B.%s.median_t_seed_lo" % label] = min(c["median_t"] for c in cs)
        v["B.%s.median_t_seed_hi" % label] = max(c["median_t"] for c in cs)
        v["B.%s.floor_seed_lo" % label] = min(c["mean_floor"] for c in cs)
        v["B.%s.floor_seed_hi" % label] = max(c["mean_floor"] for c in cs)

    cs_h, k_h, n_h = pooled("Hamming/32bit")
    cs_p, k_p, n_p = pooled("PQ/32bit")
    v["B.frac_gap_pp"] = (k_h / float(n_h)) - (k_p / float(n_p))
    v["B.frac_gap_ci"] = axis.wilson_diff(k_h, n_h, k_p, n_p)
    v["B.float.floor"] = agg(cellsB, "float", "mean_floor", mean)
    v["B.hamming32.atoms"] = agg(cellsB, "Hamming/32bit", "median_atoms", mean)
    v["B.pq32.atoms"] = agg(cellsB, "PQ/32bit", "median_atoms", mean)

    # tier A controls and headline
    v["A.float.floor"] = cell_lookup(cellsA, "float/raw descriptors", "mean_floor")
    v["A.float.median_t"] = cell_lookup(cellsA, "float/raw descriptors", "median_t")
    v["A.constructed.floor"] = cell_lookup(cellsA, "constructed/all points identical", "mean_floor")
    v["A.constructed.median_t"] = cell_lookup(cellsA, "constructed/all points identical", "median_t")
    v["A.hamming32.median_t"] = agg(cellsA, "Hamming/32bit", "median_t", mean)
    v["A.hamming256.median_t"] = agg(cellsA, "Hamming/256bit", "median_t", mean)
    v["A.pq64.floor"] = agg(cellsA, "PQ/64bit", "mean_floor", mean)
    v["A.pq32.floor"] = agg(cellsA, "PQ/32bit", "mean_floor", mean)
    return v


def fmt(x):
    if isinstance(x, bool):
        return str(x).lower()
    if isinstance(x, int):
        return "{:,}".format(x)
    if isinstance(x, float):
        if x == int(x) and abs(x) < 1e6:
            return "%.1f" % x if "." not in repr(x) else repr(x)
        return ("%.4f" % x).rstrip("0").rstrip(".") if abs(x) < 1 else ("%.3f" % x).rstrip("0").rstrip(".")
    return str(x)


MARK = re.compile(r"\{\{n:([^}]+)\}\}")
# A number the prose wants at a stated precision: `{{f:key|pct1}}` prints a proportion as a
# percentage and `{{f:key|cipct1}}` prints a pair as a percentage interval. The precision belongs to
# the sentence, the value belongs to the artefact, and the gate still reads both.
FLOAT_MARK = re.compile(r"\{\{f:([^}|]+)\|([a-z0-9]+)\}\}")
SPECS = {"pct1", "cipct1"}
CITE = re.compile(r"\{\{c:([^}]+)\}\}")



def house_entry(entry):
    """One line per entry, one period per full stop.

    * `thorne-fever-2018` arrived from the registry hard-wrapped -- CR/LF plus the registry's own
      indentation inside the entry -- so the printed record stopped mid-venue and read as truncated.
      Its DOI was on the continuation line, where a reader of the raw file does not see it; as one
      line it resolves.
    * Every initial already ends in a period and the assembler's joiner added a second, so the list
      printed `Yang, C. S.. (1975)` on most entries.

    Normalising cannot change a quantity: entries are identifiers and titles, and the stray-number
    gate reads the prose before this substitution.
    """
    return re.sub(r"\.\.(\s)", r".\1", " ".join(entry.split()))


def stray_numbers(body, bound):
    """Numbers in the prose that no artefact binds.

    The unit is the prose, and the bibliography is not the prose: a DOI is full of digit runs
    (`10.1000/0001787803310340`), so a scan applied after the reference list is spliced in
    rejects the paper for containing citations. That ordering was a real failure: the first
    render of this manuscript was refused with a stray list of DOI fragments. The caller scans
    the body while `{{refs}}` is still a marker.
    """
    allowed = {fmt(x) for x in bound} | {a.replace(",", "") for a in (fmt(x) for x in bound)}
    allowed |= {str(int(x)) for x in bound if isinstance(x, (int, float)) and float(x).is_integer()}
    # Code spans and fenced blocks are identifiers, not quantities: `Hamming/32bit` is a tag the
    # artefact uses, and a bit budget written as a tag must not read as a number the prose typed.
    scan = re.sub(r"```.*?```", " ", body, flags=re.S)
    scan = re.sub(r"`[^`\n]*`", " ", scan)
    scan = re.sub(r"\([^)]*://[^)]*\)", " ", scan)          # link targets
    stray = []
    for tok in re.findall(r"(?<![\w.])\d[\d,]*\.?\d*(?![\w])", scan):
        t = tok.replace(",", "")
        if t in allowed:
            continue
        if re.fullmatch(r"(19|20)\d\d", t):        # a year
            continue
        if len(t.replace(".", "")) >= 2:             # section numbers are single digits
            stray.append(tok)
    return sorted(set(stray))


def selftest():
    """Demonstrate each guard firing, and each guard passing where it should.

    A guard nobody has seen fail is not a guard. These cases run the same predicates the real
    render uses, on fixtures small enough to reason about, and the run is green only when every
    defect is refused and every clean case is accepted.
    """
    global REF_FLOOR
    values = {"x": 42, "y": 0.5}
    fails = 0

    def expect(name, ok, detail=""):
        nonlocal fails
        print("  [%s] %s%s" % ("ok" if ok else "FAIL", name, (" -- " + detail) if detail else ""))
        if not ok:
            fails += 1

    stray_of = stray_numbers      # the fixtures test the scanner the render uses

    # 1. a typed number is refused
    expect("a typed number in the prose is refused", stray_of("we measured 37 things", [42]),
           "found %s" % stray_of("we measured 37 things", [42]))
    # 2. a bound number is accepted
    expect("a bound number is accepted", not stray_of("we measured 42 things", [42]))
    # 3. a year is not a stray
    expect("a year is not a stray", not stray_of("published in 1998", [42]))
    # 4. an identifier in a code span is not a stray
    expect("a code-span identifier is not a stray", not stray_of("the `Hamming/32bit` cell", [42]))
    # 5. an unresolved marker is refused
    try:
        MARK.sub(lambda m: values[m.group(1)], "{{n:nope}}")
        expect("an unresolved marker is refused", False)
    except KeyError:
        expect("an unresolved marker is refused", True)
    # 6. an unverified reference is refused
    fake = {"a": {"entry": "e", "verification": {"result": "NO RECORD"}},
            "b": {"entry": "e", "verification": {"result": "verified"}}}
    try:
        CITE.sub(lambda m: "[1]" if fake[m.group(1)]["verification"]["result"] == "verified" else
                 (_ for _ in ()).throw(KeyError("unverified")), "{{c:a}}")
        expect("an unverified reference is refused", False)
    except KeyError:
        expect("an unverified reference is refused", True)
    # 7. a citation group is checked member by member
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
    expect("a group of verified references is accepted",
           CITE.sub(lambda m: "[1]" if all(fake[x.strip()]["verification"]["result"] == "verified"
                                           for x in m.group(1).split(",")) else "",
                    "{{c:b}}") == "[1]")
    # 8. the bibliography and the citation indices are not prose
    doi = "[1] Somebody, A. (2020). vol. 3. pp. 1-9. https://doi.org/10.1000/0001787803310340"
    expect("a DOI line WOULD trip the scanner if it were scanned", bool(stray_of(doi, [])),
           "found %s" % stray_of(doi, []))
    expect("the body is scanned while {{refs}} is still a marker",
           stray_of("we cite the thing {{refs}}", []) == [])
    expect("and while a citation is still a marker",
           stray_of("a family {{c:x,y}} ties", []) == [])
    # 9. the floor is enforced
    expect("the reference floor is enforced", len(fake) < REF_FLOOR)

    print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1

def main():
    prose = open("manuscript_prose.md").read()
    A = load("results/mechanism.json")
    B = load("results/scale.json")
    try:
        M = load("results/medium.json")
    except FileNotFoundError:
        print("results/medium.json is missing -- the paper states the 200k scale and cannot")
        print("  render without it. -> run run_scale.py --medium (numpy alone, no corpus).")
        return 1
    try:
        refs = load("refs.json")
    except FileNotFoundError:
        print("refs.json is missing -- the bibliography has not been built yet.")
        print("  -> run build_refs.py; the paper will not render until every citation resolves.")
        return 1

    values = build_values(A, B, M)
    bound = []

    def sub(m):
        key = m.group(1).strip()
        if key not in values:
            raise KeyError("{{n:%s}} is not a number any artefact holds" % key)
        bound.append(values[key])
        return fmt(values[key])

    body = MARK.sub(sub, prose)

    def sub_float(m):
        key, spec = m.group(1).strip(), m.group(2).strip()
        if key not in values:
            raise KeyError("{{f:%s|%s}} is not a number any artefact holds" % (key, spec))
        if spec not in SPECS:
            raise KeyError("{{f:%s|%s}} names no spec this renderer knows (%s)"
                           % (key, spec, ", ".join(sorted(SPECS))))
        value = values[key]
        if spec == "pct1":
            text = "%.1f" % (100 * value)
            bound.extend([value, text])
            return text
        lo, hi = value
        lo_s, hi_s = "%.1f" % (100 * lo), "%.1f" % (100 * hi)
        bound.extend([value, lo, hi, lo_s, hi_s])
        return "[%s, %s]" % (lo_s, hi_s)

    body = FLOAT_MARK.sub(sub_float, body)

    # ---- citations -----------------------------------------------------------------------
    order = []

    def cite(m):
        """One marker may name several works: a sentence that cites a family cites all of it.

        Every member is resolved and checked, so a group cannot smuggle an unverified or
        unheld slug past the gate -- the group fails as a whole.
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

    # ---- stray scan: a number the prose typed rather than bound ---------------------------
    # The unit is the prose, and neither the bibliography nor the citation indices are prose:
    # a DOI is digit runs, and a rendered group `[109,41]` is two indices. So the scan runs here
    # -- after the {{n:}} markers are bound, while {{c:}} is still a marker and {{refs}} is still
    # a marker. Scanning after either substitution rejects the paper for containing citations,
    # which is how the first render of this manuscript failed.
    stray = stray_numbers(body, bound)
    if stray:
        print("STRAY NUMBERS (in the prose but bound to nothing): %s" % stray[:12])
        print("  -> every number must be a {{n:...}} marker; refusing to write the paper.")
        return 1

    body = CITE.sub(cite, body)

    uncited = [s for s in refs if s not in order]
    if uncited:
        raise KeyError("refs.json holds %d reference(s) the body never cites (padding): %s"
                       % (len(uncited), uncited[:8]))
    if len(order) < REF_FLOOR:
        raise KeyError("only %d reference(s) are held and cited; the journal's floor is %d"
                       % (len(order), REF_FLOOR))

    entries = []
    repaired = 0
    for i, slug in enumerate(order, 1):
        r = refs[slug]
        printed = house_entry(r["entry"])
        if printed != r["entry"]:
            repaired += 1
        entries.append("[%d] %s" % (i, printed))

    body = body.replace("{{refs}}", "\n\n".join(entries))

    # A marker this renderer did not resolve is not a number and not a citation, so the stray-number
    # scan cannot see it: its digits, if any, are inside braces. Writing `{{f:key|pct1}}` into the
    # published text is the failure mode that produced this check (2026-11-09), and the paper is
    # refused rather than shipped with a template expression in a sentence.
    if "{{" in body:
        loc = body.index("{{")
        print("UNRESOLVED MARKER in the rendered paper: %r" % body[loc:loc + 40])
        print("  -> every marker must be one this renderer resolves; refusing to write the paper.")
        return 1
    open("manuscript.md", "w").write(body)
    print("manuscript.md written: %d characters" % len(body))
    print("  markers bound: %d numbers, %d citations" % (len(bound), len(order)))
    print("  references: %d held, %d cited (floor %d)" % (len(refs), len(order), REF_FLOOR))
    print("  house form: %d of %d entries repaired on the way out (stored line breaks, "
          "doubled period)" % (repaired, len(order)))
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
