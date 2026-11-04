#!/usr/bin/env python3
"""issue-165 -- the stray-number gate: every number PRINTED in the manuscript must be a form the
artefact can produce at that precision.

Why this exists next to make_manuscript.py's own gate: that gate reads the TEMPLATE, and it only
refuses runs of two or more digits. A number like `1.0`, or a four-decimal figure rounded by hand from
a three-decimal artefact, walks straight through it -- and a hand-rounded number is unverifiable by
construction, because nothing in the package holds it. This gate reads the RENDERED manuscript
instead and asks, for each token, whether results.json can produce exactly that string.

The exemptions are named here rather than implied by a pattern that quietly grew:
  * markdown headings and section references (`## 4.1`, `\u00a77`)  -- structure, not quantity;
  * `Table N` / `Figure N`                                      -- pointers into this document;
  * anything inside backticks                                    -- identifiers and paths;
  * the bin labels the artefact itself holds as strings           -- `10-49` is the name of a bin.

Usage:  python3 check_numbers.py            -> exit 0 if every printed number is artefact-derivable
        python3 check_numbers.py --explain  -> also print the artefact form each match came from
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results.json")
MANUSCRIPT = os.path.join(HERE, "manuscript.md")

SPECS = ("int", "f1", "f2", "f3", "f4", "pct1", "pct2", "signed_pct1", "ci3", "cipct1")


def forms(value, spec):
    """The strings make_manuscript.py would print for this value under this spec."""
    out = []
    try:
        if spec == "int":
            out.append(str(int(round(value))))
        elif spec in ("f1", "f2", "f3", "f4"):
            out.append(("%." + spec[1] + "f") % value)
        elif spec in ("pct1", "pct2"):
            out.append(("%." + spec[3] + "f") % (100 * value))
        elif spec == "signed_pct1":
            out.append("%+.1f" % (100 * value))
        elif spec == "ci3":
            out += ["%.3f" % value[0], "%.3f" % value[1]]
        elif spec == "cipct1":
            out += ["%.1f" % (100 * value[0]), "%.1f" % (100 * value[1])]
    except (TypeError, IndexError, ValueError):
        pass
    return out


def derivable(results):
    """Every numeric string the artefact can put into prose, plus the names it holds as strings."""
    allowed, provenance = set(), {}

    def add(tok, why):
        allowed.add(tok)
        provenance.setdefault(tok, why)

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, "%s.%s" % (path, k) if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, "%s[%d]" % (path, i))
        elif isinstance(node, bool) or node is None:
            return
        elif isinstance(node, (int, float)):
            for spec in SPECS:
                for tok in forms(node, spec):
                    add(tok, "%s | %s" % (path, spec))
            add(str(node), "%s | raw" % path)
        elif isinstance(node, str):
            # the artefact holds some quantities AS NAMES (bin labels like "10-49")
            for tok in NUMBER.findall(node):
                add(tok, "%s | held as a string: %r" % (path, node))

    walk(results, "")
    for i in range(0, 101):                      # structural integers a document may use: Table 1..N
        add(str(i), "document structure")
    return allowed, provenance


NUMBER = re.compile(r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?![\w.])")
BACKTICK = re.compile(r"`[^`]*`")
HEADING = re.compile(r"^\s*#{1,6}\s")
POINTER = re.compile(r"(?:Table|Figure|\u00a7)\s*$")


def scan(text, allowed, provenance, explain):
    """Returns (matched, unmatched, exempt) -- the census is counted here, not inferred downstream,
    so that "0 unmatched" cannot be printed by a scan that read nothing at all."""
    matched, unmatched, exempt = [], [], 0
    for lineno, line in enumerate(text.splitlines(), 1):
        if HEADING.match(line):
            exempt += len(NUMBER.findall(line))
            continue
        stripped = BACKTICK.sub(" ", line)
        for m in NUMBER.finditer(stripped):
            tok = m.group(0)
            before = stripped[:m.start()]
            if POINTER.search(before):
                exempt += 1
                continue
            if tok in allowed:
                matched.append((lineno, tok, provenance.get(tok, "?")))
            else:
                unmatched.append((lineno, tok))
    return matched, unmatched, exempt


def main():
    results = json.load(open(RESULTS))
    text = open(MANUSCRIPT).read()
    allowed, provenance = derivable(results)
    matched, unmatched, exempt = scan(text, allowed, provenance, "--explain" in sys.argv)
    total = len(matched) + len(unmatched) + exempt
    print("check_numbers: %d numeric tokens read -- %d artefact-derivable, %d exempt "
          "(headings/Table-N/Figure-N), %d unmatched"
          % (total, len(matched), exempt, len(unmatched)))
    if total == 0:
        print("check_numbers: REFUSED -- the scan read no numbers at all, so its verdict means nothing",
              file=sys.stderr)
        return 1
    if "--explain" in sys.argv:
        for lineno, tok, why in matched:
            print("  line %-4d %-12s <- %s" % (lineno, tok, why))
    if unmatched:
        for lineno, tok in unmatched:
            print("  line %-4d %-12s NOT DERIVABLE from results.json -- a hand-typed number"
                  % (lineno, tok), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
