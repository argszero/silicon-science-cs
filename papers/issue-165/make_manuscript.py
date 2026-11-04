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
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "manuscript_template.md")
RESULTS = os.path.join(HERE, "results.json")
OUT = os.path.join(HERE, "manuscript.md")

MARKER = re.compile(r"\{\{([a-z]+):([^}]*)\}\}")
CITE = re.compile(r"\{\{c:([^}]*)\}\}")          # a citation: keys, rendered to [n,m] by first use
REFSMARK = re.compile(r"\{\{refs\}\}")           # where the numbered list goes
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


RECORDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs", "records.json")


def load_accepted():
    """The verified corpus, by key. Only records that passed the registry rule live in `accepted`."""
    rec = json.load(open(RECORDS))
    return {r["key"]: r for r in rec["accepted"]}


def fmt_entry(r):
    """One bibliography entry. No URL wrapping around the DOI: a bare `doi:` cannot be mistaken
    for a hyperlink that a reader's tool would then try to resolve."""
    names = [html.unescape(n) for n in (r.get("authors") or [])]
    if len(names) > 3:
        who = "; ".join(names[:3]) + "; et al."
    else:
        who = "; ".join(names)
    bits = [b for b in (who, html.unescape((r.get("title") or "").strip())) if b]
    tail = []
    if r.get("container"):
        tail.append(html.unescape(r["container"].strip()))
    if r.get("year"):
        tail.append(str(r["year"]))
    body = ". ".join(bits)
    if tail:
        body += ". " + ", ".join(tail)
    if not body.endswith("."):
        body += "."
    return "%s doi:%s" % (body, r["doi"])


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
        if kind in ("c", "refs"):
            return m.group(0)          # left in place for the citation pass
        if kind == "lit":
            return body
        if kind == "n":
            return str(walk(results, body))
        if kind == "f":
            path, _, spec = body.rpartition("|")
            return fmt(walk(results, path), spec)
        raise SystemExit("unknown marker kind %r" % kind)
    return MARKER.sub(sub, template)


def prose(template, results):
    """The author's text with the numbers resolved and the DERIVED text removed: citation markers are
    dropped, the bibliography is dropped. This is what a number gate may scan -- the tokens a renderer
    inserts (citation ordinals, DOI digits) are not words the author wrote."""
    return REFSMARK.sub("", CITE.sub("", render(template, results)))


def with_citations(template, results, accepted):
    """Resolve `{{c:...}}` to bracketed ordinals by FIRST APPEARANCE, then the list. Returns
    (text, order, unknown_keys, uncited_keys) so the caller can refuse rather than quietly drop."""
    text = render(template, results)
    order, unknown = [], []

    def sub(m):
        nums = []
        for key in [k.strip() for k in m.group(1).split(",") if k.strip()]:
            if key not in accepted:
                unknown.append(key)
                continue
            if key not in order:
                order.append(key)
            nums.append(order.index(key) + 1)
        return "[%s]" % ",".join(str(n) for n in sorted(set(nums)))

    text = CITE.sub(sub, text)
    entries = "\n\n".join("[%d] %s" % (i + 1, fmt_entry(accepted[k])) for i, k in enumerate(order))
    text = REFSMARK.sub(lambda m: entries, text)
    return text, order, unknown, sorted(set(accepted) - set(order))


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
    accepted = load_accepted()
    text, order, unknown, uncited = with_citations(template, results, accepted)
    if unknown:
        print("make_manuscript: REFUSED -- these cited keys have no verified record: %s"
              % ", ".join(sorted(set(unknown))), file=sys.stderr)
        return 1
    if uncited:
        print("make_manuscript: REFUSED -- %d verified reference(s) are never cited in the text, "
              "and a bibliography entry that says nothing is padding: %s"
              % (len(uncited), ", ".join(uncited)), file=sys.stderr)
        return 1
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
    print("make_manuscript: %d verified references, %d citation sites, 0 uncited"
          % (len(order), len(CITE.findall(template))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
