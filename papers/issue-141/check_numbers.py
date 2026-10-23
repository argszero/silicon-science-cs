#!/usr/bin/env python3
"""issue #141 -- the traceability gate.

`manuscript.src.md` carries, after each sentence that quotes a number, an HTML comment naming the
canonical key(s) that own it:

    ... 474 of 684 cells ... <!-- n: v4.P1.G_pos, v4.P1.cells -->

The gate fails on either of two defects:

  1. an annotated key `canonical.py` does not emit  (the number has no source at all);
  2. a key whose VALUE does not occur in the annotated PARAGRAPH  (the prose's digit string and the
     artefact have drifted apart -- the estimate-side half of the same rule).

Two lessons are built in rather than described, because this file's first version had both defects:

  * An annotation may WRAP across lines (the paragraph is the unit, not the line).  The first version
    scanned line by line, so a comment broken by the writer's own line wrapping was checked only up to
    the newline and the rest of its keys were silently unchecked -- a guard that reported OK while
    four of its keys, including a wildcard that was never a key at all, went unexamined.
  * Therefore the paragraph is what a value must appear in, and `--selftest` plants a wrapped comment
    as well as an unknown key and a mismatched value.

A third lesson was added by the correction round of 2026-10-23, because the paragraph was named but
not read: `block_of` fell back to `return text` whenever it could not resolve a paragraph, and on this
manuscript it could not resolve ANY -- 45 of 45 annotation blocks were judged against the whole
document, 0 against a real paragraph.  So:

  * the unit is the paragraph, resolved by CONTAINMENT in `paragraph_spans` and never by re-finding
    the paragraph's text (which returns the first occurrence of a repeated paragraph);
  * an unresolvable paragraph is a FAILURE with a diagnostic, never a widening -- there is no path
    from "I could not find its paragraph" to "test it against everything";
  * `--selftest` plants the geometry that exposed the class: a MULTI-paragraph fixture whose annotated
    paragraph is wrong and whose later paragraph holds the value must fire.  Every earlier fixture was
    a single paragraph, where falling back to the whole text and reading the paragraph are the same
    object -- a fixture that cannot separate the two units cannot test the difference between them.

  python3 check_numbers.py            # the gate
  python3 check_numbers.py --selftest
"""
import hashlib
import json
import os
import re
import sys

import canonical

SRC = "manuscript.src.md"
CAPTIONS = os.path.join("figures", "captions.json")
IMG = re.compile(r"!\[[^\]]*\]\((figures/[^)\s]+)\)")
TAG = re.compile(r"<!--\s*n:\s*([^>]*?)-->", re.S)


def blocks(text):
    """Paragraphs, as (first_line, text) -- blank lines separate them."""
    out, cur, start = [], [], 0
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            if cur:
                out.append((start, "\n".join(cur)))
                cur = []
        else:
            if not cur:
                start = i
            cur.append(line)
    if cur:
        out.append((start, "\n".join(cur)))
    return out


def paragraph_spans(text):
    """(start, end) character spans of the paragraphs -- exact, not searched for.

    A paragraph is resolved by CONTAINMENT in these offsets.  The first version of this file instead
    re-found the paragraph's text in the document with `text.find`, which returns the FIRST
    occurrence: two identical paragraphs resolve to the first one, so the second is judged against
    text that is not its own.  Spans have no such ambiguity.
    """
    out, i, n = [], 0, len(text)
    while i < n:
        while i < n and text[i] == "\n":
            i += 1
        if i >= n:
            break
        s = i
        while i < n and not (text[i] == "\n" and (i + 1 >= n or text[i + 1] == "\n")):
            i += 1
        out.append((s, i))
    return out


def block_of(text, offset, spans=None):
    """The paragraph containing `offset`, or None when no paragraph contains it.

    None is a FAILURE the caller reports; it is never a widening to the whole document.  The
    published version ended in `return text`, and on this corpus that fallback fired for all 45
    annotation blocks: its middle condition demanded the paragraph appear entirely BEFORE the
    annotation's offset, and an annotation sits INSIDE its paragraph, so the condition never held
    and every annotated key was judged against the whole 57 172-character manuscript -- 0 keys
    against a real paragraph.  A guard that answers "present somewhere in the paper" cannot report
    a paragraph drifting away from its artefact.
    """
    if spans is None:
        spans = paragraph_spans(text)
    for s, e in spans:
        if s <= offset <= e:
            return text[s:e]
    return None


def _candidates(v):
    """The strings that would count as 'the value appears in the prose'."""
    if isinstance(v, bool):
        return [str(v)]
    if isinstance(v, (int, float)):
        return [("%g" % v)]
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        return [str(x) for x in v]
    if isinstance(v, dict):
        out = []
        for x in v.values():
            if isinstance(x, (int, float, str)) and not isinstance(x, bool):
                out.append(("%g" % x) if isinstance(x, float) else str(x))
            elif isinstance(x, dict):
                for y in x.values():
                    if isinstance(y, (int, float, str)) and not isinstance(y, bool):
                        out.append(("%g" % y) if isinstance(y, float) else str(y))
        return out
    return [str(v)]


# English number words, so that a paragraph stating "Eleven of the nineteen protocols" is read as
# stating 11 and 19.  Without this the binding is NOMINAL for any statistic the prose spells out: the
# key is attached, the digit never appears, and nothing can drift.  On this manuscript that was 8 of
# 140 keys -- found by the correction round of 2026-10-23 when the paragraph unit was finally read.
#
# "one" is deliberately ABSENT: it is the one English number word that doubles as a pronoun and a
# determiner, and this paper uses it that way ("one (`random_fixed`) reads neither ..."), so mapping it
# would let an arbitrary sentence satisfy a key whose value is 1.
_NUMWORDS = {
    "zero": 0, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_NUMWORD_RE = re.compile(r"\b(%s)\b" % "|".join(sorted(_NUMWORDS, key=len, reverse=True)), re.I)


def _spell(s):
    """A digit string a reader would read off the paragraph, number words included."""
    return _NUMWORD_RE.sub(lambda m: str(_NUMWORDS[m.group(1).lower()]), s)


def _norm(s):
    """A digit string with or without thousand separators is the same number to a reader."""
    return re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)


def _reads(para, value_string):
    """Does a reader of `para` read `value_string` as one of its numbers?

    Boundary-anchored, NOT a substring test.  The first version was `t in para`, which reads the
    value 2 out of "42" and the value 1 out of "16" -- so `cond.coord0.min_distinct` (2) was
    satisfied by the phrase "the excess across the 42 pairs" and stayed green when its own
    "2 to 8" drifted to "5 to 8".  Found by the correction round's own probe, not by inspection.
    """
    return _reads_count(para, value_string) > 0


def _reads_count(para, value_string):
    """How many times a reader of `para` reads `value_string` as one of its numbers."""
    p, t = _spell(_norm(para)), _norm(value_string)
    if not t:
        return 0
    n, i = 0, 0
    while True:
        j = p.find(t, i)
        if j < 0:
            break
        before = p[j - 1] if j else ""
        after = p[j + len(t)] if j + len(t) < len(p) else ""
        if not before.isdigit() and not after.isdigit():
            n += 1
        i = j + 1
    return n


# --- per-occurrence binding (required change 4, correction round 2026-10-23) ----------------------
#
# Presence in the paragraph is not agreement when a paragraph states one statistic more than once:
# "a minimum of 2 distinct values ... still spans 2 to 8" satisfies every key that owns a 2, and the
# same was true of the number the editor drifted.  The repair is that a key may name the OCCURRENCE it
# owns -- `key@"3 cells over 42+6+6 pairs"` -- and then the claim, not the digit, is what must appear.
#
# The anchor is checked in both directions, so it cannot be used to rubber-stamp anything: it must
# NAME the key's value (an anchor without the value in it is refused), and it must APPEAR in the unit.
# Emphasis markers and line wrapping are stripped before the match, because a reader of the rendered
# page does not see `**` or the writer's newline.
_EMPH = re.compile(r"[*_`]+")
_SPEC = re.compile(r'^\s*([A-Za-z0-9_.]+)\s*(?:@\s*"(.*)")?\s*$', re.S)


def _plain(s):
    return re.sub(r"\s+", " ", _EMPH.sub("", s)).strip()


def _spec(group):
    """'a, b@"x, y", c' -> [('a', None), ('b', 'x, y'), ('c', None)] -- commas inside quotes stay."""
    out, cur, q = [], "", False
    for ch in group:
        if ch == '"':
            q = not q
            cur += ch
        elif ch == "," and not q:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    parsed = []
    for raw in out:
        if not raw.strip():
            continue
        m = _SPEC.match(raw)
        if m:
            parsed.append((m.group(1), m.group(2)))
        else:
            parsed.append((raw.strip(), None))
    return parsed


def _anchor_present(para, anchor):
    return _plain(_spell(_norm(anchor))) in _plain(_spell(_norm(para)))


def _anchor_names_value(anchor, cands):
    a = _plain(_spell(_norm(anchor)))
    return any(_norm(c) and _norm(c) in a for c in cands)


def gate(text, known, spans=None):
    """Return [(kind, line, key, detail)] for every defect found."""
    if spans is None:
        spans = paragraph_spans(text)
    bad = []
    for m in TAG.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        specs = _spec(m.group(1))
        para = block_of(text, m.start(), spans)
        if para is not None:
            # THE ANNOTATION IS NOT EVIDENCE.  Its own text sits inside the paragraph, so a key whose
            # value -- or whose ANCHOR -- is written in the tag would satisfy itself: the first
            # version of the anchor check passed `v4.law_mismatches@"0 mismatches"` against prose that
            # said "1 mismatches", because "0 mismatches" was in the annotation.  Every match below
            # runs on the unit with the annotation blocks cut out.
            para = TAG.sub(" ", para)
        if para is None:
            # the unit could not be resolved at all: that is a defect of the ANNOTATION, and it is
            # reported as one.  Widening to the whole document here is what made every key below
            # pass vacuously.
            bad.append(("unresolvable-paragraph", line_no, m.group(1).strip(),
                        "no paragraph contains offset %d" % m.start()))
            continue
        scalar = {}                       # value string -> [key]  (for the ambiguity rule below)
        for k, anchor in specs:
            if k.startswith("external"):
                continue
            if k not in known:
                bad.append(("unknown-key", line_no, k, ""))
                continue
            cands = _candidates(known[k]["value"])
            if not cands:
                # an EMPTY collection has no string to look for: a presence test on it would pass by
                # vacuity.  Say so and send the author to the count key instead.
                bad.append(("unsearchable-value", line_no, k, known[k]["value"]))
                continue
            if len(cands) == 1:
                scalar.setdefault(_norm(cands[0]), []).append((k, anchor))
            if anchor is not None:
                if not _anchor_names_value(anchor, cands):
                    bad.append(("anchor-does-not-name-value", line_no, k, anchor))
                elif not _anchor_present(para, anchor):
                    # the claim this key owns is not in its unit, though the digit may be
                    bad.append(("value-absent-anchored", line_no, k, anchor))
                continue
            if not any(c and _reads(para, c) for c in cands):
                bad.append(("value-absent", line_no, k, known[k]["value"]))
        # --- agreement, not presence: a digit doing double duty must be resolved by an anchor ------
        # When two DIFFERENT statistics of one annotation share a value string, and the unit reads
        # that string more than once, neither key is bound by presence: each occurrence can serve
        # either.  The annotation must say which occurrence it owns.  Measured over this manuscript
        # that condition holds in 8 places; the cheap alternative -- anchoring all 146 pairs -- was
        # NOT taken, and anchoring none of them is what the editor's probe caught.
        for v, entries in scalar.items():
            if len(entries) > 1 and _reads_count(para, v) > 1:
                for k, anchor in entries:
                    if anchor is None:
                        bad.append(("ambiguous-occurrence", line_no, k,
                                    "value %s is read %d times in this paragraph and shared with %s"
                                    % (v, _reads_count(para, v),
                                       ", ".join(x for x, _a in entries if x != k))))
    return bad


def keys_in(text):
    return [k for m in TAG.finditer(text) for k, _a in _spec(m.group(1)) if k]


def figure_gate(text, base):
    """The manuscript's figures, read the way a renderer reads them.

    Three defects this catches that the number gate cannot:
      * an embedded image whose path does not exist (the picture simply does not appear, and a
        markdown renderer is silent about it);
      * a declared caption that no sentence embeds (the figure is in the package and the paper
        never shows it -- the presentation defect this journal has filed before);
      * an image whose bytes changed without `figures/captions.json` being regenerated, i.e. a
        figure the reader cannot reproduce from the declared hash.
    """
    bad = []
    embedded = IMG.findall(text)
    caps = {}
    if os.path.isfile(os.path.join(base, CAPTIONS)):
        with open(os.path.join(base, CAPTIONS), encoding="utf-8") as fh:
            caps = json.load(fh)
    else:
        bad.append(("no-captions-file", 0, CAPTIONS, ""))

    declared_files = {v["file"]: k for k, v in caps.items()}
    for path in embedded:
        fp = os.path.join(base, path)
        if not os.path.isfile(fp):
            bad.append(("image-missing", 0, path, ""))
            continue
        name = os.path.basename(path)
        key = declared_files.get(name)
        if key is None:
            bad.append(("image-not-declared", 0, path, ""))
            continue
        with open(fp, "rb") as fh:
            got = hashlib.sha256(fh.read()).hexdigest()
        if got != caps[key]["sha256"]:
            bad.append(("image-hash-stale", 0, name, caps[key]["sha256"][:16]))
    for name, key in declared_files.items():
        if not any(os.path.basename(e) == name for e in embedded):
            bad.append(("declared-but-never-embedded", 0, key, name))
    return bad


def main(argv):
    text = open(SRC, encoding="utf-8").read()
    known = canonical.numbers()

    if "--selftest" in argv:
        ok = True

        def holds(name, cond):
            nonlocal ok
            print("[%-52s] %s" % (name, "ok" if cond else "*** FAIL ***"))
            ok = ok and cond

        # a good annotation, split over two lines the way real prose wraps
        good = ("Sentence one says 474 of 684 cells.\n"
                "<!-- n: v4.P1.G_pos,\n     v4.P1.cells -->\n")
        holds("a wrapped annotation's keys are all checked",
              not [b for b in gate(good, known)])

        bad = gate("Sentence two <!-- n: v9.no_such_key -->\n", known)
        holds("an unknown key fires", any(k == "v9.no_such_key" for _t, _l, k, _d in bad))

        wrapped_bad = ("Sentence.\n<!-- n: v4.P1.G_pos,\n   v9.wrapped_unknown -->\n")
        holds("an unknown key on the SECOND line of a wrapped comment fires",
              any(k == "v9.wrapped_unknown" for _t, _l, k, _d in gate(wrapped_bad, known)))

        holds("a value absent from its paragraph fires",
              any(t == "value-absent" for t, _l, _k, _d in
                  gate("The count is nine.\n<!-- n: v4.P1.G_pos -->\n", known)))
        holds("a value present in its paragraph passes",
              not gate("The count is 474 of 684.\n<!-- n: v4.P1.G_pos -->\n", known))

        holds("a thousands-separated prose number matches its artefact value",
              not gate("It reads 1,026 entries.\n<!-- n: v4.transport_entries -->\n", known))
        holds("an empty-collection value is refused, not passed by vacuity",
              any(tp == "unsearchable-value" for tp, _l, _k, _d in
                  gate("Nothing mixed here.\n<!-- n: census.conv.mixed_orientation_protocols -->\n",
                       known)))
        holds("an embedded image that does not exist fires",
              any(t == "image-missing" for t, _l, _k, _d in
                  figure_gate("![a](figures/nope.png)\n", ".")))
        holds("a declared figure that no sentence embeds fires",
              any(t == "declared-but-never-embedded" for t, _l, _k, _d in
                  figure_gate("no figures here\n", ".")))
        holds("the real draft has annotations", len(TAG.findall(text)) > 0)

        # --- the unit, planted in the geometry that exposed the class (correction round 2026-10-23) --
        # Every fixture above is ONE paragraph, where "the paragraph" and "the whole text" are the
        # same object -- so none of them could fail if the paragraph were never resolved.  These do.
        two = ("Paragraph one says the count is nine.\n<!-- n: v4.P1.G_pos -->\n"
               "\n"
               "Paragraph two says %s of 684.\n" % known["v4.P1.G_pos"]["value"])
        holds("a value in a LATER paragraph does not satisfy an annotation in an earlier one",
              any(tp == "value-absent" for tp, _l, _k, _d in gate(two, known)))
        holds("...but the same annotation passes when its own paragraph carries the value",
              not gate("Paragraph one says %s of 684.\n<!-- n: v4.P1.G_pos -->\n"
                       % known["v4.P1.G_pos"]["value"], known))
        holds("an unresolvable paragraph is reported, never widened to the whole document",
              block_of("a\n\nb\n", 1000) is None
              and any(tp == "unresolvable-paragraph"
                      for tp, _l, _k, _d in gate("x <!-- n: v4.P1.G_pos -->", known, spans=[])))
        holds("every annotation in the real draft resolves to a real paragraph",
              all(block_of(text, m.start()) is not None
                  and len(block_of(text, m.start())) < len(text) for m in TAG.finditer(text)))

        # a statistic the prose spells out is still BOUND -- and one that spells a DIFFERENT number
        # is still a drift.  Without the first, 8 of the real draft's keys were nominal.
        holds("a statistic stated as a word satisfies its key",
              not gate("Eleven of the nineteen protocols read the row.\n"
                       "<!-- n: v4.row_reading_count, v4.protocols -->\n", known))
        holds("a statistic spelled as the WRONG word still fires",
              any(tp == "value-absent" for tp, _l, k, _d in
                  gate("Twelve of the nineteen protocols read the row.\n"
                       "<!-- n: v4.row_reading_count, v4.protocols -->\n", known)
                  if k == "v4.row_reading_count"))
        holds("'one' as a pronoun does not satisfy a key whose value is 1",
              any(tp == "value-absent" for tp, _l, _k, _d in
                  gate("One (`random_fixed`) reads neither.\n<!-- n: v4.law_mismatches -->\n", known))
              or known.get("v4.law_mismatches", {}).get("value") != 1)

        # --- agreement, not presence (required change 4): the editor's own probe, as a plant -------
        # §10's shape: one digit stands in for several statistics, and a drift of ONE occurrence left
        # the gate green because the other occurrence still carried the digit.  These fixtures are that
        # paragraph in miniature, and they must separate "the digit is here" from "this claim is here".
        shared_bad = ("We report 0 mismatches over the grid and 0 counterexamples, with 0 elsewhere.\n"
                      "<!-- n: v4.law_mismatches, v4.T3.counterexamples -->\n")
        holds("a digit shared by two statistics, stated twice, with no anchor, fires",
              any(tp == "ambiguous-occurrence" for tp, _l, _k, _d in gate(shared_bad, known)))
        shared_anchored = ('We report 0 mismatches over the grid.\n'
                           '<!-- n: v4.law_mismatches@"0 mismatches", '
                           'v4.T3.counterexamples@"0 counterexamples" -->\n'
                           'And 0 counterexamples elsewhere.\n'
                           '<!-- n: v4.T3.counterexamples@"0 counterexamples" -->\n')
        holds("...and is bound once each statistic names its own occurrence",
              not [b for b in gate(shared_anchored, known)])
        drifted = ('We report **0** mismatches over the grid and 0 counterexamples everywhere.\n'
                   '<!-- n: v4.law_mismatches@"0 mismatches", v4.T3.counterexamples@"0 counterexamples" -->\n')
        holds("a drifted occurrence fires NAMING the key (and its line)",
              any(tp == "value-absent-anchored" and k == "v4.law_mismatches" and ln == 2
                  for tp, ln, k, _d in
                  gate('We report **1** mismatches over the grid and 0 counterexamples.\n'
                       '<!-- n: v4.law_mismatches@"0 mismatches", '
                       'v4.T3.counterexamples@"0 counterexamples" -->\n', known)))
        holds("an anchor that does not name the key's value is refused",
              any(tp == "anchor-does-not-name-value" for tp, _l, _k, _d in
                  gate("gives 3 cells.\n<!-- n: cond.coord.cells@\"99 cells\" -->\n", known)))
        holds("emphasis and line wrapping do not break an anchor",
              not gate("gives **3** cells over\n42+6+6 pairs.\n"
                       "<!-- n: cond.coord.cells@\"3 cells over 42+6+6 pairs\" -->\n", known))
        print("CHECK_NUMBERS:", "ALL PASS" if ok else "A CHECK IS DECORATION")
        return 0 if ok else 1

    bad = gate(text, known)
    fbad = figure_gate(text, ".")
    ks = keys_in(text)
    if fbad:
        print("FIGURE FAILURES (%d):" % len(fbad))
        for kind, _line, key, detail in fbad:
            print("  %-28s %s %s" % (kind, key, ("(%s)" % detail) if detail else ""))
        print("NUMBERS: FAIL")
        return 1
    if bad:
        print("TRACEABILITY FAILURES (%d over %d annotated keys):" % (len(bad), len(ks)))
        for kind, line_no, k, detail in bad:
            print("  line %d: %-18s %s%s" % (line_no, k, kind,
                                             "" if not detail else "  (artefact: %r)" % (detail,)))
        print("NUMBERS: FAIL")
        return 1
    print("NUMBERS: OK (%d annotation blocks, %d keys -- each emitted by canonical.py and each "
          "value present in its own paragraph)" % (len(TAG.findall(text)), len(ks)))
    print("FIGURES: OK (%d embedded, each present on disk and matching its declared sha256, "
          "and every declared figure embedded)" % len(IMG.findall(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
