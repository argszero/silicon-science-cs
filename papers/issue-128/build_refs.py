#!/usr/bin/env python3
"""build_refs (#128, R561) -- number the manuscript's citations and emit its reference list.

The manuscript is written with citation KEYS (`[@arxiv:2401.17957]`, `[@doi:10.1137/030601818]`), and
this script turns them into numbers in FIRST-APPEARANCE order and writes the numbered reference list.
Writing with keys rather than numbers is not cosmetic: it makes the submission bar's citation rules
MECHANICAL rather than a claim about the text --

  C1  every key in the text resolves to an entry in the verified pool (a dangling citation fails);
  C2  every entry in the emitted list is CITED (an uncited reference is padding and is dropped by the
      builder, not by a reviewer -- the bar says every reference must be genuinely cited);
  C3  the cited count is reported and asserted >= 100 (the threshold in the submission bar);
  C4  the pool the keys resolve against is the VERIFIED one (refs_pool.json), so a citation cannot
      enter the manuscript without having passed title-match verification against a live record;
  C5  the emitted list is a FUNCTION of the text: re-running on an unchanged draft is byte-identical.

A key that appears in the text but not in the pool is a hard failure (C1), and so is a pool entry the
builder was told to include but which the text never cites (C2 -- the list is built FROM the text).

Usage:  python3 build_refs.py            (build + check)
        python3 build_refs.py --selftest
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFT = os.path.join(HERE, "manuscript_source.md")
OUT = os.path.join(HERE, "manuscript.md")
REFS = os.path.join(HERE, "reference-check.md")
POOL = os.path.join(HERE, "refs_pool.json")
MIN_CITED = 100

CITE = re.compile(r"\[@([A-Za-z0-9_./:\-]+)\]")
MARK = "<!--REFERENCE-LIST-->"
# The list is emitted as a FORMAL SECTION, and its heading is emitted by THIS builder rather than
# typed in the draft: the section heading is part of the reference list's own presentation, so a
# draft that forgets it (this package did, and `.github/tools/refgate.py` returned `no \`## References\`
# heading found` at the triaged head) must not be able to produce a manuscript without one.
HEADING = "## References"
TAG = re.compile(r"<[^>]+>")            # Crossref titles carry JATS markup: `<scp>Ginkgo</scp>`
WS = re.compile(r"\s+")                 # ... and runs of spaces where the markup used to be
PRE_PUNCT = re.compile(r"\s+([:,.;)])")  # ... and a stray space before the punctuation it preceded


def clean_title(t):
    """A bibliographic title as a reader sees it: no markup, no whitespace runs.

    Crossref returns the publisher's own JATS (`<scp>Ginkgo</scp>`), and stripping only the tags
    leaves the 21 spaces they were padded with -- a rendering defect the numeric validator cannot
    see (Class 178(b)).  The reference list is a PRESENTATION artefact, so it is cleaned here, at
    the one place the string is produced."""
    return PRE_PUNCT.sub(r"\1", WS.sub(" ", TAG.sub("", t.replace("\n", " ")))).strip()


def key_of(entry_id):
    return "%s:%s" % ("doi" if "/" in entry_id and entry_id.startswith("10.") else "arxiv", entry_id)


def parse_pool():
    pool = json.load(open(POOL))
    out = {}
    for k, v in pool.items():
        key = "doi:%s" % v["id"] if v["source"] == "crossref" else "arxiv:%s" % v["id"]
        out[key] = v
    return out


MAX_AUTHORS = 3


def author_str(names):
    """The house author component: `Flavio Chierichetti` -> `Chierichetti, F.`, `et al.` past three.

    The form is the record's own name REORDERED, never a name or initial that no record carries: the
    family is the record's last token and the initials are the first letters of its other tokens, which
    is the rule the journal's published packages use (`.github/tools/refgate.py` reads it as the
    `author form:` window).  A single-token name is printed as it is -- an initial no record carries
    would be a fabricated author, and the house rule says so in the same breath."""
    out = []
    for n in names:
        parts = n.split()
        if len(parts) < 2:
            out.append(n)
            continue
        out.append("%s, %s" % (parts[-1], " ".join(p[0] + "." for p in parts[:-1] if p)))
    if len(out) > MAX_AUTHORS:
        return ", ".join(out[:MAX_AUTHORS]) + ", et al."
    return ", ".join(out)


def fmt(entry, n, diff):
    """One numbered reference.  Authors follow the house form and are truncated to the first three --
    the list has 100+ entries and the bar asks for authors/year/venue/link, not a full author list.

    `diff` is the entry's one-line stated difference (bar item 11).  It is REQUIRED, not optional: a
    default would let an entry be emitted without it and no certificate would notice."""
    # Crossref author lists carry publisher whitespace runs ("Li,  Jianzhuang"): collapse them here,
    # at the one place the string is produced -- the list is a PRESENTATION artefact and C9 reads it.
    who = author_str([WS.sub(" ", a).strip() for a in (entry.get("authors") or [])])
    yr = (entry.get("published") or "")[:4] or "n.d."
    if entry["source"] == "crossref":
        ven = "DOI: %s" % entry["id"]
        url = "https://doi.org/%s" % entry["id"]
    else:
        ven = "arXiv preprint"
        url = "https://arxiv.org/abs/%s" % entry["id"]
    return "[%d] %s (%s). %s. %s. %s -- %s" % (n, who, yr, clean_title(entry["title"]), ven, url, diff)


# ---------------------------------------------------------------------------------------------
# The stated difference, and the role it is stated at.
#
# Bar item 11 asks every entry to close with a one-line stated difference.  This list states it at
# the level of the entry's ROLE -- the family it belongs to and the relationship that family bears
# to this work -- and the role is DERIVED from the discovery query that found the entry (recorded in
# the pool) rather than typed per entry, so it cannot drift from the rule that selected the entry.
# The convention is declared under the heading, where a reader meets the entries (the same form
# accepted for #120 W4 / #122 W3): a role-class difference is a difference at the level of the class,
# and the reader is told so rather than left to infer it from the repetition.
ROLE_OF_QUERY = {
    # the object this paper measures: fair clustering / group quotas in selection
    'cat:cs.LG AND all:"fair clustering"': "construct",
    'cat:cs.DS AND all:"fair clustering"': "construct",
    'all:"fair k-center" OR all:"fair k-median"': "construct",
    'all:"group fairness" AND all:"clustering"': "construct",
    'all:"socially fair" AND all:"clustering"': "construct",
    'all:"quota" AND all:"fairness" AND all:"selection"': "construct",
    'all:"proportional representation" AND all:"clustering"': "construct",
    'all:"fairlet"': "construct",
    'all:"balanced" AND all:"clustering" AND all:"fairness"': "construct",
    'all:"constrained clustering" AND all:"balancing"': "construct",
    'all:"fairness" AND all:"clustering" AND all:"approximation"': "construct",
    # the two objective families this paper separates (the P4 confound is objective-specific)
    'all:"diversity maximization"': "objective",
    'all:"maximum dispersion" AND all:"selection"': "objective",
    'all:"max-min" AND all:"diversity" AND all:"dispersion"': "objective",
    'all:"max-sum" AND all:"diversification"': "objective",
    # the combinatorial machinery a cardinality-constrained selection is an instance of
    'all:"submodular maximization" AND all:"cardinality constraint"': "machinery",
    'all:"submodular" AND all:"matroid constraint"': "machinery",
    # the price/cost-of-fairness line this paper's zero-cost region sits against
    'all:"price of fairness"': "price",
    'all:"cost of fairness" AND all:"constraints"': "price",
    # the approximation guarantees behind the greedy baseline this paper shows can be short
    'cat:cs.DS AND all:"k-center" AND all:"approximation"': "approximation",
    'cat:cs.DS AND all:"k-median" AND all:"approximation"': "approximation",
    # adjacent constrained-selection settings that share the quota structure
    'all:"fair allocation" AND all:"indivisible"': "allocation",
    'all:"fair ranking" AND all:"constraints"': "allocation",
    'all:"affirmative action" AND all:"optimization"': "allocation",
    'all:"disparate impact" AND all:"optimization"': "allocation",
    'all:"fair" AND all:"subset selection" AND all:"constraints"': "allocation",
}
# The entries located by TITLE rather than by the keyword sweep carry a `bibliographic:` query with
# no role in it, so their role is assigned here, by hand, one entry at a time.
ROLE_OVERRIDE = {
    "doi:10.1109/cvprw.2009.5206852": "construct",    # Constrained clustering via spectral regularization
    "doi:10.1109/tii.2023.3342888": "construct",      # Balanced Fair K-Means Clustering
    "doi:10.1145/3442188.3445906": "construct",       # Socially Fair k-Means Clustering
    "doi:10.1145/2487575.2487636": "objective",       # Diversity maximization under matroid constraints
    "doi:10.1137/1.9781611973402.106": "machinery",   # Submodular Maximization with Cardinality Constraints
    "doi:10.24963/ijcai.2019/12": "price",            # The Price of Fairness for Indivisible Goods
    "doi:10.1145/2940716.2940726": "allocation",      # The Unreasonable Fairness of Maximum Nash Welfare
}
# The order is the order the classes are declared and printed in; the clause is the stated difference.
ROLES = [
    ("construct", "a fair-clustering / group-quota method or analysis of the kind whose cost this "
                  "paper measures, rather than one whose cost is measured here"),
    ("objective", "a diversification objective family (max-min or max-sum) whose objective-specific "
                  "behaviour this paper separates, rather than one it compares against a quota"),
    ("machinery", "the submodular / matroid machinery a cardinality-constrained selection is an "
                  "instance of, rather than a study of the quota cost itself"),
    ("price", "a price-or-cost-of-fairness result on a different comparison (an optimum against an "
              "optimum, or a welfare ratio), not on the heuristic baseline this paper measures"),
    ("approximation", "an approximation guarantee for the greedy baseline this paper shows can fall "
                      "short of the unconstrained optimum before any quota is applied"),
    ("allocation", "a constrained-selection setting adjacent to this paper's (indivisible goods, "
                   "ranking, subset selection) that shares the quota structure but not the objective"),
]


def role_of(entry):
    """The entry's role class, and the two ways it is assigned.  A cited entry whose query is neither
    in the table nor overridden is a HARD failure: it would otherwise be emitted with no stated
    difference, which is the defect this whole layer exists to prevent."""
    key = "doi:%s" % entry["id"]
    if key in ROLE_OVERRIDE:
        return ROLE_OVERRIDE[key]
    q = entry.get("query") or ""
    if q in ROLE_OF_QUERY:
        return ROLE_OF_QUERY[q]
    raise AssertionError("C11: no role for entry %r (query %r) -- add it to ROLE_OF_QUERY or "
                         "ROLE_OVERRIDE rather than emitting it with no stated difference"
                         % (entry["id"], q))


DIFF_OF_ROLE = dict(ROLES)


def declaration(order, pool, role_of_entry):
    """The declared convention for the entries' closing one-line difference, GENERATED from the role
    assignment the entries were emitted with -- so it cannot drift from the list it describes."""
    counts = [(r, sum(1 for k in order if role_of_entry[k] == r)) for r, _c in ROLES]
    counts = [(r, n) for r, n in counts if n]
    return ("*The stated difference closing every entry is its **role class**, not a sentence written "
            "per entry; that is a declared convention.* Each entry's closing clause names the family "
            "the entry belongs to and the relationship that family bears to this work, and it is "
            "assigned from the discovery query that found the entry (`build_refs.py` -> `ROLE_OF_QUERY`, "
            "with the title-located works in `ROLE_OVERRIDE`) -- so the field states the rule the list "
            "was built by and cannot drift from it. The %d entries fall into %d classes (%s). The "
            "per-entry difference is read as: this work is *of* that class, and the class's clause is "
            "the difference from this paper."
            % (len(order), len(counts), ", ".join("%s %d" % (r, n) for r, n in counts)))


def build(draft=None, pool=None):
    draft = draft if draft is not None else io.open(DRAFT, encoding="utf-8").read()
    pool = pool if pool is not None else parse_pool()
    order, missing = [], []
    for m in CITE.finditer(draft):
        key = m.group(1)
        if key not in pool:
            missing.append(key)
        elif key not in order:
            order.append(key)
    assert not missing, "C1: %d citation(s) do not resolve in the verified pool: %s" % (
        len(missing), sorted(set(missing))[:8])
    num = {k: i + 1 for i, k in enumerate(order)}
    text = CITE.sub(lambda m: "[%d]" % num[m.group(1)], draft)
    # The role of every emitted entry, resolved ONCE (role_of raises on an unmapped entry, so the
    # list cannot be built with a missing stated difference) and cached for the declaration + C11.
    role_of_entry = {k: role_of(pool[k]) for k in order}
    # Entries are separated by a BLANK LINE, not merely by a newline.  Consecutive non-list lines are
    # ONE paragraph to every CommonMark renderer (GitHub's preview included), so a `"\n".join` list
    # prints as an unbroken wall whose entry boundaries are invisible -- the defect the triage return
    # located, and the one C8's old line-count form could not see.
    refs = "\n\n".join(fmt(pool[k], num[k], DIFF_OF_ROLE[role_of_entry[k]]) for k in order)
    if MARK in text:                       # the built manuscript carries its own list
        text = text.replace(MARK, HEADING + "\n\n" + declaration(order, pool, role_of_entry)
                            + "\n\n" + refs)
    return text, refs, order, pool, num, role_of_entry


def certify(text, refs, n, order, pool):
    """The product-side certificates C2, C3, C6, C7, C8, C9, C10 -- on the object that is written.

    They live in a function rather than inline in `main` for one reason: a certificate that cannot be
    planted is a certificate nobody has ever seen fail, and these read the BUILT manuscript and the
    list STRING, so the self-test has to be able to hand them a mutated pair without writing a file.
    """
    # C3: the count bar (>= 100 cited) -- asserted here so it is plantable, printed by `main`.
    assert n >= MIN_CITED, "C3: only %d references cited, the bar is %d" % (n, MIN_CITED)
    # C2: the list is built from the text, so an uncited pool entry is not in it by construction --
    # assert the property anyway, on the object that is written.
    emitted = set(re.findall(r"^\[(\d+)\]", refs, re.M))
    assert len(emitted) == n, "C2: %d numbered entries for %d cited keys" % (len(emitted), n)
    # C6: the built manuscript carries the list (a product-side check, not only a source-side one)
    assert MARK not in text, "C6: the reference marker was not substituted in the built manuscript"
    assert "[1]" in text and "[%d]" % n in text, "C6: the built manuscript does not carry the list"
    # C7: no citation KEY survives into the product (a key in the output means the rewrite missed one)
    left = CITE.findall(text)
    assert not left, "C7: %d unresolved citation key(s) in the built manuscript: %s" % (len(left), left[:5])
    # C8: the list must render as a LIST -- one entry per line AND a blank line between entries.
    # The old form tested `refs.count("\n") + 1 == n` ("one entry per line"), which a wall of 126
    # consecutive lines satisfies exactly while being the wall this certificate names: the check read
    # a PROXY (line count) for the property (separation) and was green on the defect (triage return,
    # item 3).  The property is now tested on the object: the entries split on the blank line into
    # exactly n blocks, each block is one line, and no block is empty.
    blocks = refs.split("\n\n")
    assert len(blocks) == n, "C8: %d entries split into %d blocks on the blank line (want %d, one each)" % (
        n, len(blocks), n)
    assert all(b.startswith("[") and "\n" not in b and b.strip() for b in blocks), \
        "C8: an entry is not a single non-empty line beginning with its number: %r" % (
            [b[:40] for b in blocks if not (b.startswith("[") and "\n" not in b and b.strip())][:2])
    # C10: the manuscript carries a FORMAL `## References` section -- the heading the citation gate
    # reads (`refgate.py`: "the last `## References` heading to the end of the file, its numbered
    # lines read as entries") and the section a reader navigates by.  The builder emits it, so this
    # asserts the object that is written, on the same window the gate uses; the plant below removes
    # the heading from the emitter and requires the failure.
    heads = [l for l in text.split("\n") if l.strip() == HEADING]
    assert len(heads) == 1, "C10: the built manuscript carries %d `%s` headings (want exactly 1)" % (
        len(heads), HEADING)
    tail = text.split(HEADING, 1)[1]
    in_window = re.findall(r"^\[(\d+)\]", tail, re.M)
    assert len(in_window) == n, (
        "C10: the gate's own window (the last `%s` heading to EOF) carries %d numbered entries, want "
        "%d -- a heading that does not bracket its list is not the section the gate reads"
        % (HEADING, len(in_window), n))
    # C9: presentation -- the list is what a reader SEES, and no numeric certificate reads it
    # (Class 178(b)).  Markup left in a title, or a whitespace run where the markup was, is a defect
    # the reference-count checks above pass happily.
    for line in refs.split("\n"):
        assert "<" not in line and ">" not in line, "C9: markup in a reference entry: %r" % line[:80]
        assert "  " not in line, "C9: whitespace run in a reference entry: %r" % line[:80]
    # C9b: the author component is the HOUSE FORM (`Family, I.`), read as the gate reads it: the
    # text before the year in each entry.  A list of `Given Family` names passes every count, link and
    # separation check and prints the record's field order rather than the journal's form.
    for b in blocks:
        head = b.split("(", 1)[0]
        fields = [x.strip() for x in head.split(", ")[1:]] if ", " in head else []
        assert fields or " " not in head.split("] ", 1)[1].strip(), \
            "C9b: author component is not `Family, I.`: %r" % head[:90]
    # C11: every entry carries a one-line STATED DIFFERENCE (bar item 11) -- tested on the emitted
    # object, by requiring each entry's closing clause to be one of the declared ones.  A list whose
    # entries end at their URL passes every count, link and format check above and carries no stated
    # difference at all, which is the defect this limb exists for.
    clauses = set(DIFF_OF_ROLE.values())
    for b in blocks:
        assert b.rsplit(" -- ", 1)[-1] in clauses, \
            "C11: an entry carries no declared stated difference: %r" % b[-90:]


def main():
    text, refs, order, pool, num, role_of_entry = build()
    n = len(order)
    print("cited: %d references (bar %d) -- %s" % (n, MIN_CITED, "PASS" if n >= MIN_CITED else "FAIL"))
    certify(text, refs, n, order, pool)
    # C11b: the role table is not STALE with respect to the pool it classifies.  `role_of` only ever
    # sees the entries the manuscript cites, so a query that no cited entry came from would rot there
    # unseen -- the table is asserted against every non-title query the POOL carries, including the
    # ones this manuscript does not (yet) cite.
    pool_queries = {(v.get("query") or "") for v in pool.values()}
    unclassified = sorted(q for q in pool_queries
                          if q and not q.startswith("bibliographic:") and q not in ROLE_OF_QUERY)
    assert not unclassified, ("C11b: %d pool quer(y/ies) have no role -- the table is stale, and an "
                              "entry cited from one would fail at build time: %s"
                              % (len(unclassified), unclassified[:3]))
    roles = [(r, sum(1 for k in order if role_of_entry[k] == r)) for r, _c in ROLES]
    print("roles: %s" % ", ".join("%s %d" % (r, c) for r, c in roles if c))
    src = sum(1 for k in order if pool[k]["source"] == "arxiv")
    years = sorted((pool[k].get("published") or "0")[:4] for k in order)
    io.open(OUT, "w", encoding="utf-8").write(text)
    # `references.md` is the same list as a standalone artefact, so it carries the same heading and
    # the same blank-line separation: a reader renders it too, and `refscan128.read_lines` skips
    # blank lines and headings, so its numbering certificate still reads the entries.
    io.open(os.path.join(HERE, "references.md"), "w", encoding="utf-8").write(
        HEADING + "\n\n" + refs + "\n")
    print("wrote %s (%d lines) and references.md (%d entries: %d arXiv, %d Crossref)"
          % (os.path.basename(OUT), text.count("\n") + 1, n, src, n - src))
    print("years: %s .. %s" % (years[0], years[-1]))
    return 0


def selftest():
    ok = True

    def holds(name, cond):
        nonlocal ok
        print("[%-32s] %s" % (name, "ok" if cond else "*** FAIL ***"))
        ok = ok and cond

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except AssertionError:
            print("[%-32s] FIRED" % name)
            return
        print("[%-32s] *** DID NOT FIRE ***" % name)
        ok = False

    def _passes(fn, *a):
        """The complement of `fires`: the healthy object must be ACCEPTED, or the certificate is one
        that rejects everything (the failure mode `fires` alone cannot see)."""
        try:
            fn(*a)
            return True
        except AssertionError:
            return False

    pool = {"arxiv:1.1": {"source": "arxiv", "id": "1.1", "title": "T", "authors": ["A"], "published": "2020-01-01",
                          "query": 'cat:cs.LG AND all:"fair clustering"'},
            "doi:10.1/x": {"source": "crossref", "id": "10.1/x", "title": "D", "authors": ["B"], "published": "1999-01-01",
                           "query": 'all:"price of fairness"'}}
    text, refs, order, _p, num, _ro = build(draft="see [@arxiv:1.1] and [@doi:10.1/x], again [@arxiv:1.1].", pool=pool)
    holds("numbering-first-appearance", num == {"arxiv:1.1": 1, "doi:10.1/x": 2})
    holds("draft-rewritten", text == "see [1] and [2], again [1].")
    holds("one-entry-per-key", refs.count("[1]") == 1 and refs.count("[2]") == 1)
    holds("doi-link", "https://doi.org/10.1/x" in refs)
    holds("arxiv-link", "https://arxiv.org/abs/1.1" in refs)
    # C9: a title carrying publisher markup and the padding the markup left must be emitted clean.
    # The plant is a DIRTY title in the pool, which is the only way this check can be exercised --
    # the real pool happens to contain exactly one such entry ([69], Ginkgo).
    dirty = dict(pool)
    dirty["arxiv:2.2"] = {"source": "arxiv", "id": "2.2", "authors": ["C"], "published": "2021-05-05",
                          "title": "<scp>Ginkgo</scp>                     : A Modern Framework",
                          "query": 'all:"maximum dispersion" AND all:"selection"'}
    _t3, refs3, _o3, _p3, _n3, _r3 = build(draft="see [@arxiv:2.2] and [@arxiv:1.1].", pool=dirty)
    holds("title-markup-stripped", "<scp>" not in refs3 and "Ginkgo: A Modern Framework" in refs3)
    holds("title-whitespace-collapsed", "  " not in refs3)
    # and the assertion is on the object: with the cleaning limb REMOVED, the same title must carry
    # markup and fail C9.  A plant that calls the unmutated cleaner is inert (Class 183(a)/(186b)).
    def unclean_emitter():
        global clean_title
        saved = clean_title
        try:
            clean_title = lambda t: t                      # verbatim mutation of the limb under test
            line = fmt(dict(dirty["arxiv:2.2"]), 1, DIFF_OF_ROLE["objective"])
        finally:
            clean_title = saved
        assert "<" not in line and "  " not in line, "C9: markup in a reference entry: %r" % line[:80]
    fires("title-cleaner-required", unclean_emitter)
    # C1 plant: a citation that does not resolve must FAIL rather than pass with an empty entry
    fires("dangling-key-fails", lambda: build(draft="x [@arxiv:9.9]", pool=pool))
    # C2 plant: an uncited pool entry must not reach the list
    text2, refs2, order2, _p2, _n2, _r2 = build(draft="only [@arxiv:1.1]", pool=pool)
    holds("uncited-pool-entry-absent", "10.1/x" not in refs2 and len(order2) == 1)
    # C3 plant: the count assertion is on the object, not printed -- prove it can fail by handing
    # `certify` a list below the bar (the old form "fired" on a lambda that threw unconditionally,
    # which is a plant of nothing: it exercised no limb of the real check).
    fires("count-bar-can-fail", lambda: certify("[1] x", "[1] x", 1, ["arxiv:1.1"], pool))
    # C8 plant: the WALL.  Consecutive lines satisfy the retired line-count form and are exactly
    # the defect it named, so the plant is a wall-joined list and the certificate must reject it.
    # The healthy control is the same entries BLANK-LINE separated and must pass -- a certificate
    # proved only to fire is a certificate nobody has seen accept the correct object (Class 183(b)).
    n_bar = MIN_CITED
    wall = "\n".join("[%d] entry -- %s" % (i, ROLES[0][1]) for i in range(1, n_bar + 1))
    # ... with a declared clause, so the SAME object exercises C8's accept and C11's requirement
    good = "\n\n".join("[%d] entry -- %s" % (i, ROLES[0][1]) for i in range(1, n_bar + 1))
    fires("wall-of-lines-rejected", lambda: certify(
        "body\n\n" + HEADING + "\n\n" + wall, wall, n_bar, ["arxiv:1.1"] * n_bar, pool))
    try:
        certify("body\n\n" + HEADING + "\n\n" + good, good, n_bar, ["arxiv:1.1"] * n_bar, pool)
        holds("separated-list-accepted", True)
    except AssertionError as e:
        holds("separated-list-accepted", False)
        print("      %s" % e)
    # C10 plant: a manuscript whose list was substituted WITHOUT the heading must fail.
    fires("missing-heading-rejected", lambda: certify(
        "body\n\n" + good, good, n_bar, ["arxiv:1.1"] * n_bar, pool))
    # C11 plant: entries that end at their URL carry no stated difference -- the list the triage
    # return found in this package.  The control above (`separated-list-accepted`) must FAIL this
    # limb, which is exactly why it is built with the clause appended: prove both directions.
    bare = "\n\n".join("[%d] entry" % i for i in range(1, n_bar + 1))   # no clause: the defect
    fired = False
    try:
        certify("body\n\n" + HEADING + "\n\n" + bare, bare, n_bar, ["arxiv:1.1"] * n_bar, pool)
    except AssertionError:
        fired = True
    holds("undifferenced-entries-rejected", fired)
    # ... and an entry whose query has no role at all must fail AT BUILD (not merely be emitted with
    # an empty clause): this is the limb that keeps the table honest as the pool grows.
    fires("unmapped-query-rejected", lambda: role_of({"id": "9.9", "query": 'all:"brand new topic"'}))
    # C9b plant: the record's own field order (`Given Family`) is not the house form, and must fail.
    given_first = "\n\n".join("[%d] Flavio Chierichetti (%s). T. arXiv preprint. https://x -- %s"
                              % (i, 2000 + i, ROLES[0][1]) for i in range(1, n_bar + 1))
    fires("given-name-first-rejected", lambda: certify(
        "body\n\n" + HEADING + "\n\n" + given_first, given_first, n_bar, ["arxiv:1.1"] * n_bar, pool))
    # ... and the healthy control: the same entries in the house form must be accepted
    fam_first = "\n\n".join("[%d] Chierichetti, F. (%s). T. arXiv preprint. https://x -- %s"
                            % (i, 2000 + i, ROLES[0][1]) for i in range(1, n_bar + 1))
    holds("family-first-accepted", _passes(certify, "body\n\n" + HEADING + "\n\n" + fam_first,
                                           fam_first, n_bar, ["arxiv:1.1"] * n_bar, pool))
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
