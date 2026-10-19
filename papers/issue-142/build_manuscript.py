#!/usr/bin/env python3
"""Build manuscript.md for issue #142 from its source, resolving every citation.

Nothing in the product is typed twice.  One placeholder kind is resolved here:

  {ref:ID}        a CITATION, resolved against the verified pool (refs/pool.json)
  {{REFERENCES}}  the numbered reference list, assembled from the cited keys in order of first use
  {{FIG:key}}     a FIGURE BLOCK -- image + caption, read from figures/captions.json

The build FAILS on each way a citation can be wrong:
  (1) a placeholder with no owner          -- the key is not in the verified pool
  (2) a cited key with no stated difference-- the presentation bar wants one line per entry
  (3) fewer than 100 cited references      -- the journal's citation bar is a gate, not a print
  (4) an unresolved placeholder            -- a stray brace means the source is not what was built
  (5) a reference listed but never cited   -- padding does not count toward the total
  (6) an unreadable report                 -- a missing source file is a Fault, not a traceback
  (7) a figure block whose IMAGE is absent  -- a link that resolves nowhere is a defect on the product

The reference layer is a claim about the BODY, so the build reports how many pool entries are never
cited, and each rendered entry ends with its one-line stated difference, read from
refs/differences.json.

Run:  python3 build_manuscript.py            (write manuscript.md, staged then os.replace'd)
      python3 build_manuscript.py --check    (render into memory; compare with the shipped file)
      python3 build_manuscript.py --selftest (plant a defect per check, require a fire)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "manuscript.src.md")
OUT = os.path.join(HERE, "manuscript.md")
POOL = os.path.join(HERE, "refs", "pool.json")
DIFFS = os.path.join(HERE, "refs", "differences.json")
# the author basis for records whose own registry record carries no author field (see fmt_authors)
AUTHOR_BASIS = {}
_ab = os.path.join(HERE, "refs", "author-basis.json")
if os.path.isfile(_ab):
    with open(_ab, encoding="utf-8") as _fh:
        AUTHOR_BASIS = {k: v for k, v in json.load(_fh).items() if not k.startswith("_")}
CAPTIONS = os.path.join(HERE, "figures", "captions.json")
RECEIPT = os.path.join(HERE, "refs", "verify-run.txt")
MIN_REFS = 100


class Fault(Exception):
    pass


def load(path, what):
    if not os.path.isfile(path):
        raise Fault("%s is missing at %s" % (what, os.path.relpath(path, HERE)))
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:                                        # noqa: BLE001
        raise Fault("%s is unreadable: %s" % (what, e))


def fmt_authors(a, record=None):
    """`Family, G. T.; Family, G.` -- the house list form.

    Two repairs over the first version, both found by reading the journal gate's advisories rather
    than by trusting the build: (a) initials take a PERIOD each -- a record storing `given: "B T"`
    produced `Polyak, B T.`, which is not the form the gate reads; (b) a record with NO author field
    at all (measured on four canonical books) printed `(n/a)`.

    A THIRD REPAIR, from review of #142 (2026-10-19): repair (b) put the RECORD'S PUBLISHER in the
    author slot, so the rendered entry read as if `Springer-Verlag` had written the book. A publisher
    in the author slot is a false statement about who wrote the work, whatever basis note follows it.
    The layer `refs/author-basis.json` now supplies the human author for those keys TOGETHER WITH THE
    RECORD THE NAME WAS READ FROM, and where no real record names one the slot is left EMPTY and
    says so -- an unverified name is never printed.
    """
    a = a or []
    out = []
    for name in a[:3]:
        parts = name.split()
        if len(parts) >= 2:
            out.append("%s, %s" % (parts[-1], " ".join(p[0] + "." for p in parts[:-1])))
        else:
            out.append(name)
    if len(a) > 3:
        out.append("et al.")
    if out:
        return "; ".join(out)
    key = (record or {}).get("id")
    basis = AUTHOR_BASIS.get(key) if key else None
    if basis and basis.get("authors"):
        return "%s [%s; the cited record carries no author field]" % (
            fmt_authors(basis["authors"]), basis["basis"])
    if basis:
        return "[author not carried by the source record, and no real record names one]"
    # NO FALLBACK TO THE PUBLISHER, even inside a bracketed note: the slot is the AUTHOR slot, and a
    # publisher's name there reads as authorship however it is decorated.  (The plant below fired on
    # exactly this line on its first run -- the first repair still echoed `published by Springer-
    # Verlag` in the slot, which is the defect wearing a note.)
    return "[author not carried by the source record]"


def fmt_venue(rec):
    if rec.get("source") == "arxiv":
        return "arXiv:%s" % rec["id"]
    return "doi:%s" % rec["id"]


def fmt_link(rec):
    if rec.get("source") == "arxiv":
        return "https://arxiv.org/abs/%s" % rec["id"]
    return "https://doi.org/%s" % rec["id"]


def render(src_text, pool, diffs, captions=None):
    """Return (product_text, cited_keys_in_order, used_counts)."""
    order, index = [], {}

    def cite(m):
        key = m.group(1).strip()
        if key not in pool:
            raise Fault("citation key %r is not in the verified pool" % key)
        if key not in diffs or not str(diffs[key]).strip():
            raise Fault("cited key %r has no stated difference in refs/differences.json" % key)
        if key not in index:
            order.append(key)
            index[key] = len(order)
        return "[%d]" % index[key]

    body = re.sub(r"\{ref:([^}]+)\}", cite, src_text)

    # FIGURE BLOCKS.  A figure link resolves at the LINKING file's own directory, so the block is
    # written relative to the manuscript's directory and the build ASSERTS the image is actually there
    # (Class 216a: a link that resolves nowhere is a defect on the product, not on the source).
    def figure(m):
        key = m.group(1).strip()
        if not captions or key not in captions:
            raise Fault("figure key %r is not in figures/captions.json" % key)
        rec = captions[key]
        img = os.path.join(HERE, "figures", rec["file"])
        if not os.path.isfile(img):
            raise Fault("figure %r names an image that is absent: %s" % (key, rec["file"]))
        # Alt text is the caption's FIRST SENTENCE, cut at a word boundary -- a mid-word truncation is
        # a defect a sighted reader never sees and a screen reader always reads.
        cap = rec["caption"]
        first = cap.split(". ")[0].rstrip(".")
        if len(first) > 90:
            first = first[:90].rsplit(" ", 1)[0] + "..."
        return "![Figure %s: %s](figures/%s)\n\n*%s*" % (key[1:], first, rec["file"], cap)
    used_figs = set(re.findall(r"\{\{FIG:([^}]+)\}\}", body))
    body = re.sub(r"\{\{FIG:([^}]+)\}\}", figure, body)
    # A figure DECLARED beside the manuscript and quoted by no sentence is a defect a reader cannot
    # see: the figure exists, the caption exists, and the paper never shows it (Class 216b).  So the
    # set of declared figures and the set the source embeds must be equal, both ways.
    if captions:
        declared, embedded = set(captions), used_figs
        if declared - embedded:
            raise Fault("figure(s) %s are declared but never embedded in the manuscript"
                        % sorted(declared - embedded))
        if embedded - declared:
            raise Fault("the manuscript embeds undeclared figure(s) %s" % sorted(embedded - declared))

    # Shape checks FIRST.  A stray placeholder is a defect in the SOURCE, and reporting it as "too few
    # references" would name the wrong fault -- and, worse, mask it: a one-key source fails the bar
    # first, so the placeholder check would never run and its plant would read `ok` while firing
    # nothing (a plant that cannot reach its check is not a check).  The one legitimate double-brace
    # form is the REFERENCES seat, which is excluded by name rather than by pattern.
    if re.search(r"\{ref:", body):
        raise Fault("an unresolved {ref:...} placeholder survived the build")
    stray = [b for b in re.findall(r"\{\{[^}]*\}\}", body) if b != "{{REFERENCES}}"]

    if stray:
        raise Fault("unrecognised placeholder(s) %s survived the build" % stray[:3])
    if re.search(r"\[ref\]", body):
        raise Fault("a legacy [ref] seat survived the build")

    if len(order) < MIN_REFS:
        raise Fault("only %d cited references (the journal's bar is %d)" % (len(order), MIN_REFS))

    lines = []
    for i, key in enumerate(order, 1):
        r = pool[key]
        lines.append("[%d] %s (%s). %s. %s. %s -- Difference: %s"
                     % (i, fmt_authors(r.get("authors", []), r), str(r.get("published", ""))[:4],
                        r["title"], fmt_venue(r), fmt_link(r), diffs[key]))
    # A blank line between entries.  Without it every entry line is ONE paragraph to a CommonMark
    # renderer, so the list renders as a wall -- and the journal's own gate says so in as many words
    # ("read the page, not the source").  The separator is part of the PRODUCT, not decoration.
    body = body.replace("{{REFERENCES}}", "\n\n".join(lines))
    if re.search(r"\{\{|\}\}", body):
        raise Fault("a brace survived into the product")
    return body, order, index


def main(argv):
    if "--selftest" in argv:
        return selftest()
    try:
        pool = load(POOL, "the reference pool refs/pool.json")
        diffs = load(DIFFS, "the stated-differences file refs/differences.json")
        captions = load(CAPTIONS, "the figure captions figures/captions.json")
        if not os.path.isfile(SRC):
            raise Fault("manuscript.src.md is missing")
        with open(SRC, encoding="utf-8") as fh:
            src_text = fh.read()
        body, order, _ = render(src_text, pool, diffs, captions)
    except Fault as e:
        print("BUILD FAILED: %s" % e)
        return 1
    uncited = [k for k in pool if k not in set(order)]
    if "--check" in argv:
        if not os.path.isfile(OUT):
            print("CHECK FAILED: manuscript.md is not present")
            return 1
        with open(OUT, encoding="utf-8") as fh:
            shipped = fh.read()
        if shipped != body:
            print("CHECK FAILED: manuscript.md is not what the source builds")
            return 1
        print("CHECK OK: manuscript.md == build(src) (%d refs)" % len(order))
        return 0
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(body)
    os.replace(tmp, OUT)
    print("wrote manuscript.md: %d refs cited, %d pool entries never cited, %d lines"
          % (len(order), len(uncited), body.count("\n") + 1))
    return 0


def selftest():
    ok = True

    def holds(name, cond):
        nonlocal ok
        print("[%-38s] %s" % (name, "ok" if cond else "*** FAIL ***"))
        ok = ok and cond

    pool = {"k1": {"id": "k1", "source": "arxiv", "title": "T1", "published": "2020",
                   "authors": ["A B"]},
            "k2": {"id": "k2", "source": "crossref", "title": "T2", "published": "2021",
                   "authors": ["C D"]}}
    diffs = {"k1": "difference one", "k2": "difference two"}
    # a source that cites two keys, padded with enough repeats to clear the bar is NOT enough --
    # the bar counts DISTINCT cited references, so a repeated key cannot inflate it
    many = " ".join("{ref:k1}" for _ in range(MIN_REFS + 5))
    try:
        render(many + " {{REFERENCES}}", pool, diffs)
        holds("repeat-of-one-key-cannot-clear-the-bar", False)
    except Fault as e:
        holds("repeat-of-one-key-cannot-clear-the-bar", "cited references" in str(e))

    # a key outside the pool
    try:
        render("{ref:nope} {{REFERENCES}}", pool, diffs)
        holds("unknown-key-fires", False)
    except Fault as e:
        holds("unknown-key-fires", "not in the verified pool" in str(e))
    # a cited key with no stated difference
    try:
        render("{ref:k1} {{REFERENCES}}", pool, {})
        holds("missing-difference-fires", False)
    except Fault as e:
        holds("missing-difference-fires", "no stated difference" in str(e))
    # a stray placeholder survives -> caught (planted with a WRONG seat name, which is what a typo
    # actually looks like; the earlier version of this plant concatenated into the VALID name and so
    # planted nothing)
    try:
        render("{{FIGURES}} {ref:k1} {{REFERENCES}}", pool, diffs)
        holds("stray-placeholder-fires", False)
    except Fault as e:
        holds("stray-placeholder-fires", "unrecognised placeholder" in str(e))
    # a legacy [ref] seat is refused -- on a source that ALREADY clears the bar, so the shape check is
    # the one that must fire (otherwise the bar fires first and the plant proves nothing)
    big = _big_src()
    try:
        render(big.replace("{{REFERENCES}}", "[ref] {{REFERENCES}}"), _big_pool()[0], _big_pool()[1])
        holds("legacy-seat-fires", False)
    except Fault as e:
        holds("legacy-seat-fires", "legacy [ref] seat" in str(e))
    # a figure key with no caption entry
    big = _big_src()
    try:
        render(big + " {{FIG:nope}}", _big_pool()[0], _big_pool()[1],
               {"p1": {"file": "fig_does_not_exist.png", "caption": "c", "sha256": "x"}})
        holds("unknown-figure-key-fires", False)
    except Fault as e:
        holds("unknown-figure-key-fires", "not in figures/captions.json" in str(e))
    # a figure whose IMAGE is absent -- the caption entry exists, the file does not
    try:
        render(big + " {{FIG:p1}}", _big_pool()[0], _big_pool()[1],
               {"p1": {"file": "fig_does_not_exist.png", "caption": "c", "sha256": "x"}})
        holds("absent-figure-image-fires", False)
    except Fault as e:
        holds("absent-figure-image-fires", "names an image that is absent" in str(e))
    # the REAL captions resolve to files that exist, and the block carries the image link.  The source
    # must embed EVERY declared figure, so this case embeds all of them -- and the check that they are
    # all embedded gets its own plant below.
    real = load(CAPTIONS, "figure captions")
    all_fig = " ".join("{{FIG:%s}}" % k for k in sorted(real))
    body_f, _, _ = render(big + " " + all_fig, _big_pool()[0], _big_pool()[1], real)
    holds("real-figure-blocks-resolve",
          "](figures/fig1_p1_quadrature.png)" in body_f and "](figures/fig2_p2_span_law.png)" in body_f)
    holds("figure-caption-is-italicised", "*P1:" in body_f)
    # THE AUTHOR SLOT (review of #142, 2026-10-19).  A record with no author field used to print its
    # PUBLISHER in the author slot, so the rendered entry read as if the publisher had written the
    # work.  Two plants: the fallback must NOT emit the publisher as an author, and the empty slot
    # must say plainly that nobody is named.
    _noauth = fmt_authors([], {"id": "TEST-NO-SUCH-KEY", "publisher": "Springer-Verlag",
                               "container": "Some Series"})
    holds("publisher-is-never-printed-in-the-author-slot",
          "Springer-Verlag" not in _noauth.split(" -- ")[0])
    holds("empty-author-slot-says-so", "author" in _noauth.lower() and _noauth.startswith("["))
    holds("alt-text-is-not-a-mid-word-cut",
          all(not a.split("]")[0].endswith(("-", "…")) for a in re.findall(r"!\[[^\]]*\]", body_f)))
    # a declared figure that no sentence embeds -- the picture exists and the paper never shows it
    try:
        render(big + " {{FIG:p1}}", _big_pool()[0], _big_pool()[1], real)
        holds("never-embedded-figure-fires", False)
    except Fault as e:
        holds("never-embedded-figure-fires", "declared but never embedded" in str(e))

    # numbering follows order of first use, and a repeat reuses its number.  Asserted on the INDEX MAP
    # and on the citation text, not on `body.count("[n]")` -- the reference LIST also begins lines with
    # `[n]`, so a raw count conflates a citation with a listing and passes for the wrong reason.
    body, order, index = _tiny()
    head = body.split("## References")[0]
    holds("numbering-is-first-use", order[:2] == ["k0", "k1"] and index["k0"] == 1 and index["k1"] == 2)
    holds("repeat-reuses-number", head.startswith("[1] then [2] then [1] "))
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def _big_pool():
    """A 100-key pool and its differences, so a source can clear the bar in the selftest."""
    pool, diffs = {}, {}
    for i in range(MIN_REFS):
        k = "k%d" % i
        pool[k] = {"id": k, "source": "arxiv", "title": "T%d" % i, "published": "2020",
                   "authors": ["A B"]}
        diffs[k] = "difference %d" % i
    return pool, diffs


def _big_src():
    pool, _ = _big_pool()
    return " ".join("{ref:%s}" % k for k in sorted(pool)) + " {{REFERENCES}}"


def _tiny():
    """A bar-clearing source whose first two keys repeat, so the numbering assertion can run."""
    pool, diffs = _big_pool()
    keys = sorted(pool)
    src = "{ref:%s} then {ref:%s} then {ref:%s} " % (keys[0], keys[1], keys[0])
    src += " ".join("{ref:%s}" % k for k in keys[2:])
    return render(src + " {{REFERENCES}}", pool, diffs)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
