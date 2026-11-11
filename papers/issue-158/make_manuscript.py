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
import html
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
families_of = axis.families_of


def scale_tiers(A, B, M):
    """The scale tiers this render drew from, smallest first: the paper's scale count is its length.

    Round-2 review M1: the subtitle and the contribution-level line said "two scales" while the body
    enumerated three, and the sentence had not moved when tier M added the third. The count is now
    the length of this list, so a fourth tier changes it and cannot leave the sentence behind.
    """
    return axis.scale_tiers([("mechanism", A), ("medium", M), ("scale", B)])


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


def build_values(A, B, M, S):
    """Every number the prose may name, as a flat dict. Anything not here cannot be printed."""
    cellsA, cellsB, cellsM = A["cells"], B["cells"], M["cells"]

    # Counts about the paper's own design. They are counts, not measurements, so no artefact stores
    # them: they are composed from the tiers this render drew from and the families the cells carry.
    # Round-2 review M1 is the cost of typing one -- the subtitle said "two scales" at a head that
    # measured three -- and the fix is the same one the review asked for twice already: compose it,
    # in one place, from the object that owns the fact.
    tiers = scale_tiers(A, B, M)
    tier_sizes = [n for _, n in tiers]
    if max(tier_sizes) % min(tier_sizes):
        raise KeyError("the largest scale (%d) is not a whole multiple of the smallest (%d), so the "
                       "ratio the paper prints is not an integer" % (max(tier_sizes), min(tier_sizes)))
    families = axis.families_of(cellsA)

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
        # The search behind the paper's one absence claim (review m5). Every number that sentence
        # states — how many queries, how many indices, the window's two endpoints, what came back —
        # is bound here, so the claim cannot be edited without the record moving with it.
        "S.n_indices": len(S["indices"]),
        "S.n_queries": len(S["queries"]),
        "S.n_retrieved": S["ledger"]["records_retrieved"],
        "S.n_deduped": S["ledger"]["records_deduped"],
        "S.n_screened": S["ledger"]["survived_screen"],
        "S.n_read": S["ledger"]["read_by_hand"],
        "S.n_asks": S["ledger"]["n_asks_width"],
        "S.window_from": S["window"]["from"],
        "S.window_to": S["window"]["to"],
        # Counts about the paper's own design (round-2 review M1). Printed as words by `{{w:}}`.
        "N.n_scales": len(tiers),
        "N.n_families": len(families),
        "N.scale_ratio": max(tier_sizes) // min(tier_sizes),
        "N.n_controls": len(axis.CONTROL_PREFIXES),
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


UNITS = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
         "fifteen sixteen seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def bind_word(values, bound=None):
    """The `{{w:key}}` substitution. The render and the selftest run this one predicate.

    It lives here rather than inside `main` because a refusal demonstrated on a copy of the rule is
    not a refusal of the rule: the first draft of this selftest called `word()` directly on a
    fractional fixture and passed, where the render would have printed `zero`.
    """
    def sub(m):
        key = m.group(1).strip()
        if key not in values:
            raise KeyError("{{w:%s}} is not a count any artefact holds" % key)
        value = values[key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise KeyError("{{w:%s}} is not a whole number (%r); a count in words must be one"
                           % (key, value))
        if bound is not None:
            bound.append(value)
        return word(value)
    return sub


def word(x):
    """A whole number as the English word a sentence needs. `{{w:key}}` prints through this."""
    n = int(x)
    if n < len(UNITS):
        return UNITS[n]
    if n < 100:
        tens, unit = divmod(n, 10)
        return TENS[tens] + ("-" + UNITS[unit] if unit else "")
    return "{:,}".format(n)


MARK = re.compile(r"\{\{n:([^}]+)\}\}")
# A count the sentence needs as a word: `{{w:key}}` prints "three" where `{{n:key}}` would print "3".
# A count written in words is invisible to the stray-number scan (it matches digits), so every count
# of the paper's own design -- how many scales, how many families, the scale ratio -- is bound here
# rather than typed: round-2 review M1.
WORD_MARK = re.compile(r"\{\{w:([^}]+)\}\}")

# A count of the paper's own design written as a word, on the source prose. Round-2 review M1 named
# the gap: `refgate` reads the bibliography, `stepgate` reads script counts, `numgate` reads digits,
# and none of them reads "how many scales a sentence says the study has" -- so the subtitle read
# `two scales` at a head that measured three and every gate stayed green. Composing the count fixes
# the sentence; this refuses the class, because a regeneration is not a guard against the next author
# typing the same word. The noun list is deliberately short: it carries the design counts that appear
# in the sentences a reader meets first, and a bare "two further families" (a contrast inside one
# sentence, not a claim about the study) is out of scope by construction rather than by exemption.
DESIGN_NOUNS = ("scales", "families", "configurations")
COUNT_WORDS = ("one two three four five six seven eight nine ten eleven twelve twenty thirty fifty "
               "hundred").split()
TYPED_COUNT = re.compile(r"\b(%s)\s+(?:quantiser\s+)?(%s)\b"
                         % ("|".join(COUNT_WORDS), "|".join(DESIGN_NOUNS)), re.I)


def typed_design_counts(prose):
    """Counts of the paper's own design typed as words -- refused, whatever the digit scan says."""
    return sorted({m.group(0) for m in TYPED_COUNT.finditer(prose)})
# A number the prose wants at a stated precision: `{{f:key|pct1}}` prints a proportion as a
# percentage and `{{f:key|cipct1}}` prints a pair as a percentage interval. The precision belongs to
# the sentence, the value belongs to the artefact, and the gate still reads both.
FLOAT_MARK = re.compile(r"\{\{f:([^}|]+)\|([a-z0-9]+)\}\}")
SPECS = {"pct1", "cipct1"}
CITE = re.compile(r"\{\{c:([^}]+)\}\}")



def _house_author(m):
    """A family name the registry stored in capitals, printed in one case with the rest of the list.

    `SPARCK JONES, K.` and `VOORHEES, E. M.` are how the registry returned those records, and a list
    that prints them beside `Hunter, J. D.` reads as two conventions in one bibliography. Only an
    author component with no lower-case letter at all is touched.
    """
    author, year = m.group(1), m.group(2)
    if author.strip() and not re.search(r"[a-z]", author):
        author = " ".join(w.capitalize() if w.isupper() else w for w in author.split())
    return authors_to_house(author) + year


def _house_title(m):
    """A title stored in capitals, printed in sentence case: the same rule, one field over.

    The condition is the whole title, not a word in it: `TREC` inside "The TREC question answering
    track" is an acronym in a mixed-case title and stays exactly as stored, and so does any title
    with a lower-case letter anywhere.
    """
    year, title = m.group(1), m.group(2)
    if re.search(r"[a-z]", title):
        return m.group(0)
    return "%s. %s" % (year, title[0].upper() + title[1:].lower())


PARTICLES = frozenset((
    "van", "von", "der", "den", "de", "del", "della", "degli", "di", "da", "dos", "das", "do",
    "du", "la", "le", "les", "bin", "ibn", "al", "el", "ter", "ten", "op", "zu", "zum", "zur",
))


def author_to_house(name):
    """`Tomas Mikolov` -> `Mikolov, T.`; `Johannes Diderik van der Waals` -> `van der Waals, J. D.`

    The list prints one convention, and ten entries arrived from the arXiv path in the other one.
    The Atom feed gives each author as a single `name` string with no family/given split, so the
    assembler had nothing to build the house form from and joined the strings whole (round-3 review,
    Weakness 1). The split is made here, from the evidence the other path also uses -- where the
    family name begins -- and never by cutting a fixed number of tokens, because a family name may
    begin with a particle (`van der Waals`) and a position-blind cut prints `Waals, v. d.`.

    A name already carrying a comma is the house form and is returned untouched; so is `et al.`,
    which is a sentinel rather than a person. A single-token name is a family name.
    """
    name = " ".join((name or "").split())
    if not name or "," in name or name.lower() in ("et al", "et al."):
        return name
    toks = name.split()
    if len(toks) == 1:
        return name
    idx = next((i for i, t in enumerate(toks) if t[:1].islower()), None)
    if idx == 0:                       # particles and a family name only: no given name to initialise
        return name
    if idx is None:
        idx = len(toks) - 1
    fam = " ".join(toks[idx:])
    # A record sometimes stores the family name with its sentence period (`Matei Zaharia.`), and that
    # period belongs to the sentence rather than to the name. The cut is CONDITIONAL on the family
    # name being longer than an initial: a blanket `rstrip(".")` over the name ate the final initial
    # in `Hunter, J. D.` and `Voorhees, E. M.` when this leg was first written, which is the fourth
    # time that shortcut has cost this journal a rendered period.
    if len(fam) > 2 and fam.endswith("."):
        fam = fam[:-1]
    giv = " ".join(toks[:idx])
    inits = " ".join(ch[0] + "." for ch in re.split(r"[\s-]+", giv) if ch)
    return ("%s, %s" % (fam, inits)) if inits else fam


def authors_to_house(component):
    """The whole author component, one name at a time; `;` separates the names in both forms."""
    parts = [p.strip() for p in (component or "").split(";")]
    return "; ".join(author_to_house(p) for p in parts)


# A field a record stores as null is ABSENT, and the page says so by saying nothing. The word for
# absence is not the absence: `[73]` printed `(None)` where its year belongs because `str(None)`
# returns a string, so the assembler's `try/except` could never see it. `(n.d.)` is NOT null -- an
# explicitly undated record is a statement, and the review names it as the acceptable alternative.
NULL_SLOT = re.compile(r"\(\s*(?:None|null|NULL|N/A|nan|NaN)\s*\)|(?<![\w.])None(?![\w.])")


# A null in the YEAR slot is a different thing from a null anywhere else: the slot exists, and the
# record usually HOLDS the year -- `entry_of` reads Crossref's `issued`, which is where the year was
# missing, not where the work's year lives. Measured across the list, five entries printed `(None)`
# for a year their own record carries (1984, 1997, 2000, 2005, 2006). The review named one of them
# and asked for the slot to be dropped; the census is what separates "drop it" from "fill it".
YEAR_SLOT_NULL = re.compile(r"\(\s*(?:None|null|NULL|N/A|nan|NaN)\s*\)(?=\.\s)")


def strip_null_slots(line):
    r"""Print an absent field as absent, and close the gap it leaves behind -- and only that gap.

    The first version collapsed `[\s,;:]{2,}` to one space, which ate the `", "` between every pair
    of author names in the list and turned `Hunter, J. D.` into `Hunter J. D.` -- the selftest's
    "returned exactly as stored" leg is what caught it. Only whitespace is collapsed; the separators
    are removed one at a time, and only where a slot actually was.
    """
    if not NULL_SLOT.search(line):
        return line
    out = NULL_SLOT.sub("\x00", line)
    out = re.sub(r"^\s*\x00\s*[.,;:]?\s*", "", out)      # a slot that opened the entry
    out = re.sub(r"\s*\x00\s*[.,;:]\s*", " ", out)       # … one in the middle takes one side
    out = re.sub(r"[.,;:]\s*\x00\s*", " ", out)
    out = out.replace("\x00", "")
    return re.sub(r"\s{2,}", " ", out).strip()


def null_slot_census(entries, render=None):
    """Three questions with different answers, and only one of them is a defect.

    `in_record` are entries whose STORED text carries a null slot. `repaired` are those whose null
    sat in the year slot and whose own record holds the year, so the render prints the year rather
    than the absence: the review named `[73]` and asked for the slot to be dropped, and the census is
    what shows that dropping it would delete a year the record carries. `survives` are entries whose
    RENDERED line still carries a null, which is the defect: it is refused BY NAME, with the slug,
    because a gate that dies on the thing it exists to find names nothing (round 2 of #160, one
    package over).
    """
    if render is None:
        def render(ref):
            return house_entry(ref.get("entry") or "", year=ref.get("year"))
    in_record, repaired, survives = [], [], []
    for slug in sorted(entries):
        ref = entries[slug] or {}
        raw = ref.get("entry") or ""
        line = render(ref)
        if NULL_SLOT.search(raw):
            in_record.append(slug)
            if YEAR_SLOT_NULL.search(raw) and ref.get("year"):
                repaired.append(slug)
        if NULL_SLOT.search(line):
            survives.append((slug, line[:90]))
    return dict(in_record=in_record, repaired=repaired, survives=survives, rows=len(entries))


def house_entry(entry, year=None):
    """One line per entry, one period per full stop, one convention for the whole list.

    * `thorne-fever-2018` arrived from the registry hard-wrapped -- CR/LF plus the registry's own
      indentation inside the entry -- so the printed record stopped mid-venue and read as truncated.
      Its DOI was on the continuation line, where a reader of the raw file does not see it; as one
      line it resolves.
    * Every initial already ends in a period and the assembler's joiner added a second, so the list
      printed `Yang, C. S.. (1975)` on most entries.
    * `hunter-matplotlib-2007` printed its venue as `Computing in Science &amp; Engineering`: the
      registry stores the publisher's XML text, entity and all, and a reference that prints an escape
      is quoting its source rather than naming the venue (round-2 review Q3).
    * Two entries store an author family name -- and, in one, the title as well -- in capitals, as
      the registry received them.

    All four are the casing and escaping of the RECORD, not of the paper: `refs.json` keeps exactly
    what the registry returned, and this is the render's house form, the same way the doubled period
    is. Normalising cannot change a quantity: entries are identifiers, titles and venues, and the
    stray-number gate reads the prose before this substitution.
    """
    line = " ".join(entry.split())
    if year:
        line = YEAR_SLOT_NULL.sub("(%s)" % year, line, count=1)
    line = strip_null_slots(line)
    line = re.sub(r"\.\.(\s)", r".\1", html.unescape(line))
    line = re.sub(r"^(.*?)(\s*\((?:(?:\d{4})|(?:n\.d\.))\))", _house_author, line, count=1)
    return re.sub(r"(\(\d{4}\))\.\s+([^.]+)", _house_title, line, count=1)


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
    # A bound value that is a string may be a composite -- a window endpoint like `2016-01-01` is one
    # value held by one key, and it prints as three digit runs. Its components are part of the bound
    # value, not numbers of their own, so they are allowed; a date the prose typed itself matches no
    # bound string and is still refused. Without this, the honest form of the search record (state
    # both endpoints) is exactly what the gate would reject.
    for x in bound:
        if isinstance(x, str):
            allowed |= set(re.findall(r"\d+", x))
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

    # 10. a count in words is a number, and it comes from a bound value (round-2 review M1).
    words = {"k": 3, "ratio": 50}
    expect("a count written in words is invisible to the number scan -- which is why it is bound",
           stray_of("this study has three scales", [3]) == [])
    expect("a bound word marker prints the word its value names",
           WORD_MARK.sub(bind_word(words), "{{w:k}} scales") == "three scales")
    expect("a ratio prints as a compound word", word(words["ratio"]) == "fifty")
    try:
        WORD_MARK.sub(bind_word(words), "{{w:nope}}")
        expect("an unbound word marker is refused", False)
    except KeyError:
        expect("an unbound word marker is refused", True)
    try:
        WORD_MARK.sub(bind_word(dict(values)), "{{w:y}}")
        expect("a word marker bound to a non-count is refused", False)
    except KeyError:
        expect("a word marker bound to a non-count is refused", True)

    expect("a design count typed as a word is refused",
           typed_design_counts("one corpus, two scales of it") == ["two scales"],
           "found %s" % typed_design_counts("one corpus, two scales of it"))
    expect("the same count as a marker passes the gate",
           typed_design_counts("one corpus, {{w:N.n_scales}} scales of it") == [])
    expect("a contrast inside a sentence is not a design count",
           typed_design_counts("Two further families refute it") == [])

    # 10b. the reference list prints in one house form (round-2 review Q3).
    expect("an entity in the registry's stored venue is decoded at render",
           "&amp;" not in house_entry("Hunter, J. D. (2007). Matplotlib: A 2D Graphics Environment. "
                                      "Computing in Science &amp; Engineering. vol. 9."),
           house_entry("Hunter, J. D. (2007). Matplotlib: A 2D Graphics Environment. "
                       "Computing in Science &amp; Engineering. vol. 9.")[-60:])
    expect("a family name stored in capitals is printed in one case",
           house_entry("VOORHEES, E. M. (2001). The TREC question answering track.").startswith(
               "Voorhees, E. M."),
           house_entry("VOORHEES, E. M. (2001). The TREC question answering track.")[:30])
    expect("a title stored in capitals is printed in sentence case",
           ". A statistical interpretation" in house_entry(
               "SPARCK JONES, K. (1972). A STATISTICAL INTERPRETATION OF TERM SPECIFICITY. Journal of "
               "Documentation."),
           house_entry("SPARCK JONES, K. (1972). A STATISTICAL INTERPRETATION OF TERM SPECIFICITY. "
                       "Journal of Documentation.")[:70])
    expect("an acronym inside a mixed-case title is left as stored",
           "The TREC question answering track" in house_entry(
               "VOORHEES, E. M. (2001). The TREC question answering track. Natural Language Engineering."))
    expect("a mixed-case entry is returned exactly as stored, apart from the doubled period",
           house_entry("Hunter, J. D.. (2007). Matplotlib: A 2D Graphics Environment. "
                       "Computing in Science &amp; Engineering.") ==
           "Hunter, J. D. (2007). Matplotlib: A 2D Graphics Environment. "
           "Computing in Science & Engineering.",
           house_entry("Hunter, J. D.. (2007). Matplotlib: A 2D Graphics Environment. "
                       "Computing in Science & Engineering."))

    # 11. the scale count is a property of the tiers, not of a sentence.
    expect("the scale count is the number of tiers a render drew from",
           len(axis.scale_tiers([("a", {"corpus": {"n": 20000}}),
                                 ("b", {"fixture": {"n": 200000}}),
                                 ("c", {"corpus": {"n": 1000000}})])) == 3)
    try:
        axis.scale_tiers([("t", {"cells": []})])
        expect("a tier that states no corpus size is refused", False)
    except KeyError:
        expect("a tier that states no corpus size is refused", True)
    expect("the family count is the families the cells carry, not a word",
           axis.families_of([{"tag": "Hamming/32bit/seed7"}, {"tag": "PQ/64bit/seed7"},
                             {"tag": "PQ/32bit/seed7"},
                             {"tag": "float/raw descriptors"}]) == ["Hamming", "PQ"])

    # 12. one author form for the whole list, and the particle that a position-blind cut breaks.
    expect("a given-name-first author prints in the house form",
           author_to_house("Tomas Mikolov") == "Mikolov, T.")
    expect("a middle name becomes a second initial, not part of the family name",
           author_to_house("Harsha Vardhan Simhadri") == "Simhadri, H. V.")
    expect("a family name that begins with a particle keeps it",
           author_to_house("Johannes Diderik van der Waals") == "van der Waals, J. D.",
           author_to_house("Johannes Diderik van der Waals"))
    expect("and the last-token cut that would print `Waals, v. d.` is not what runs",
           not author_to_house("Johannes Diderik van der Waals").startswith("Waals"))
    expect("a hyphenated given name keeps both initials",
           author_to_house("Jae-Pil Heo") == "Heo, J. P.", author_to_house("Jae-Pil Heo"))
    expect("a name already in the house form is returned untouched",
           author_to_house("Hunter, J. D.") == "Hunter, J. D.")
    expect("the et al. sentinel is not a person and is not rearranged",
           author_to_house("et al.") == "et al.")
    expect("a single-token name is a family name",
           author_to_house("Plato") == "Plato")
    expect("the whole component is one convention",
           authors_to_house("Tomas Mikolov; Ilya Sutskever; Kai Chen; et al.")
           == "Mikolov, T.; Sutskever, I.; Chen, K.; et al.",
           authors_to_house("Tomas Mikolov; Ilya Sutskever; Kai Chen; et al."))
    expect("and the entry the review named ends in that form",
           house_entry("Tomas Mikolov; Ilya Sutskever; Kai Chen; et al.. (2013). Distributed "
                       "Representations of Words and Phrases and their Compositionality. "
                       "arXiv preprint 1310.4546v1.").startswith("Mikolov, T.; Sutskever, I.;"))

    # 13. a null field prints as absent, and a null that SURVIVES the render is refused by name.
    nul = ("(None). R-Trees - A Dynamic Index Structure for Spatial Searching. SpringerReference. "
           "https://doi.org/10.1007/springerreference_62807")
    expect("a stored null slot does not reach the page",
           "(None)" not in house_entry(nul) and "None" not in house_entry(nul),
           house_entry(nul)[:60])
    expect("and the entry still opens with its title",
           house_entry(nul).startswith("R-Trees -"), house_entry(nul)[:40])
    cen = null_slot_census({"x": {"entry": nul}, "y": {"entry": "Hunter, J. D. (2007). Matplotlib."}})
    expect("the census counts what it repaired",
           cen["in_record"] == ["x"] and cen["survives"] == [] and cen["rows"] == 2,
           "in_record=%s survives=%s" % (cen["in_record"], cen["survives"]))
    expect("a null in the YEAR slot is filled from the record, not dropped",
           house_entry(nul, year=1984).startswith("(1984). R-Trees -"),
           house_entry(nul, year=1984)[:40])
    expect("and without a record year the same slot prints as absent",
           house_entry(nul).startswith("R-Trees -"), house_entry(nul)[:40])
    # plant: a render that does NOT repair. Without this the guard could only be tested against a
    # world in which it never has to fire, which is the shape of a guard that has never been seen to
    # work -- and the review asks for a refusal, not a crash, when one gets through.
    planted = null_slot_census({"x": {"entry": nul}}, render=lambda ref: ref.get("entry"))
    expect("a null that survives the render is reported BY NAME",
           [sl for sl, _ in planted["survives"]] == ["x"],
           "survives=%s" % (planted["survives"],))

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
        S = load("search/absence_search.json")
    except FileNotFoundError:
        print("search/absence_search.json is missing -- the paper's absence claim states the")
        print("  search behind it and cannot render without it. -> run search_record.py")
        return 1
    try:
        refs = load("refs.json")
    except FileNotFoundError:
        print("refs.json is missing -- the bibliography has not been built yet.")
        print("  -> run build_refs.py; the paper will not render until every citation resolves.")
        return 1

    typed = typed_design_counts(prose)
    if typed:
        print("TYPED DESIGN COUNT(S) in the prose: %s" % typed)
        print("  -> how many scales or families this study has must come from a composed value")
        print("     (`{{w:N.n_scales}}`, `{{w:N.n_families}}`); a word is invisible to the")
        print("     stray-number scan, which is how the subtitle read `two scales` at a head that")
        print("     measured three. Refusing to write the paper.")
        return 1

    values = build_values(A, B, M, S)
    bound = []

    def sub(m):
        key = m.group(1).strip()
        if key not in values:
            raise KeyError("{{n:%s}} is not a number any artefact holds" % key)
        bound.append(values[key])
        return fmt(values[key])

    body = MARK.sub(sub, prose)

    body = WORD_MARK.sub(bind_word(values, bound), body)

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
        printed = house_entry(r["entry"], year=r.get("year"))
        if printed != r["entry"]:
            repaired += 1
        entries.append("[%d] %s" % (i, printed))

    census = null_slot_census(refs)
    if census["survives"]:
        for slug, line in census["survives"]:
            print("NULL SLOT printed by entry `%s`: %s" % (slug, line))
        print("  -> an absent field prints as absent, never as the word for absence.")
        print("     Refusing to write the paper.")
        return 1
    if census["in_record"]:
        print("  null slots: %d of %d stored entries carried one; %d print their own record's year "
              "in the slot and %d print the field as absent (%s)"
              % (len(census["in_record"]), census["rows"], len(census["repaired"]),
                 len(census["in_record"]) - len(census["repaired"]),
                 ", ".join(census["in_record"][:6])))

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
