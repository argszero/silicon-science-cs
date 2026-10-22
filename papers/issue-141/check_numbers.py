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


def block_of(text, offset):
    """The paragraph containing a character offset in `text`."""
    for start, blk in blocks(text):
        if blk in text and text.rfind(blk, 0, offset + 1) != -1 and txt_index(text, blk) <= offset \
                <= txt_index(text, blk) + len(blk):
            return blk
    return text


def txt_index(text, blk):
    return text.find(blk)


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


def _norm(s):
    """A digit string with or without thousand separators is the same number to a reader."""
    return re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)


def gate(text, known):
    """Return [(kind, line, key, detail)] for every defect found."""
    bad = []
    for m in TAG.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        keys = [k.strip() for k in m.group(1).split(",") if k.strip()]
        para = block_of(text, m.start())
        for k in keys:
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
            if not any(c and _norm(c) in _norm(para) for c in cands):
                bad.append(("value-absent", line_no, k, known[k]["value"]))
    return bad


def keys_in(text):
    return [k for m in TAG.finditer(text) for k in
            (x.strip() for x in m.group(1).split(",")) if k]


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
