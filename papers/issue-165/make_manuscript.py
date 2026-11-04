#!/usr/bin/env python3
"""issue-165 -- the manuscript is GENERATED. Every quantity in it is a placeholder resolved here.

Why: a number typed into prose cannot be checked by any gate (a published lesson from this journal's
own record). So the template carries only `{{...}}` markers, and this program is the one place a
quantity becomes text. Two rules are enforced mechanically:

  (1) A bare run of two or more digits may not appear in the template outside a marker. A year or a
      constant that is genuinely literal must be written `{{lit:...}}` so that it is visible as a
      claim of literalism rather than lost among the numbers.
  (2) The same rule applies to the rendered manuscript... except for bytes this program produced
      itself, which are scanned in the SKELETON before substitution -- a gate must not read its own
      output.

Usage:
  python3 make_manuscript.py            -> writes manuscript.md
  python3 make_manuscript.py --check    -> recompute and compare with the committed manuscript.md
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "manuscript_template.md")
RESULTS = os.path.join(HERE, "results.json")
OUT = os.path.join(HERE, "manuscript.md")

MARKER = re.compile(r"\{\{([a-z]+):([^}]*)\}\}")
BARE_NUMBER = re.compile(r"(?<![\w.])\d{2,}(?![\w.])")


def walk(node, path):
    cur = node
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            if part not in cur:
                raise KeyError("no such key: %s (at %s)" % (path, part))
            cur = cur[part]
        else:
            raise KeyError("cannot descend into %r at %s" % (type(cur), part))
    return cur


def fmt(value, spec):
    """One rounding, from the artefact. Percentages multiply once, here, not in prose."""
    if spec == "int":
        return str(int(round(value)))
    if spec == "f1":
        return "%.1f" % value
    if spec == "f2":
        return "%.2f" % value
    if spec == "f3":
        return "%.3f" % value
    if spec == "f4":
        return "%.4f" % value
    if spec == "pct1":
        return "%.1f" % (100 * value)
    if spec == "pct2":
        return "%.2f" % (100 * value)
    if spec == "signed_pct1":
        return "%+.1f" % (100 * value)
    if spec == "ci3":
        return "[%.3f, %.3f]" % (value[0], value[1])
    if spec == "cipct1":
        return "[%.1f, %.1f]" % (100 * value[0], 100 * value[1])
    if spec == "raw":
        return str(value)
    raise SystemExit("unknown format spec %r" % spec)


def render(template, results):
    def sub(m):
        kind, body = m.group(1), m.group(2)
        if kind == "lit":
            return body
        if kind == "n":
            return str(walk(results, body))
        if kind == "f":
            path, _, spec = body.rpartition("|")
            return fmt(walk(results, path), spec)
        raise SystemExit("unknown marker kind %r" % kind)
    return MARKER.sub(sub, template)


def skeleton(template):
    """The template with every marker blanked: what a gate may scan without reading its own output."""
    return MARKER.sub(lambda m: "x", template)


def gate(template):
    bad = [(m.start(), m.group(0)) for m in BARE_NUMBER.finditer(skeleton(template))]
    if bad:
        for pos, tok in bad:
            line = skeleton(template)[:pos].count("\n") + 1
            print("HAND-TYPED NUMBER at line %d: %r -- a quantity must be a marker, or {{lit:...}}"
                  % (line, tok), file=sys.stderr)
        return 1
    return 0


def main():
    results = json.load(open(RESULTS))
    template = open(TEMPLATE).read()
    if gate(template):
        print("make_manuscript: REFUSED -- the template carries hand-typed numbers", file=sys.stderr)
        return 1
    text = render(template, results)
    if "--check" in sys.argv:
        if open(OUT).read() != text:
            print("CHECK FAILED: manuscript.md differs from what this run renders", file=sys.stderr)
            return 1
        print("CHECK OK: manuscript.md matches this render byte for byte")
        return 0
    with open(OUT, "w") as fh:
        fh.write(text)
    markers = len(MARKER.findall(template))
    print("make_manuscript: %d markers resolved, %d bytes written" % (markers, len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
