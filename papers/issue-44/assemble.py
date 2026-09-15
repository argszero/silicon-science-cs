#!/usr/bin/env python3
"""Assemble manuscript.md from the part files.

Every measurement printed in the manuscript is a placeholder resolved out of a
committed artefact, so the prose cannot drift from the data: no number in the
body was typed by hand.  Placeholders look like

    {{F:crit_a.median_abs_error|5f}}      namespace F = canonical_results.json["manuscript_facts"]
    {{G:counts.0|d}}                      namespace G = search_form.json
    {{X:cross_checks.n_checks|d}}         namespace X = canonical_results.json
    {{C:a.status}}                        namespace C = canonical_results.json["criteria"]

Specs:  d = integer, Nf = fixed decimals, Ne = scientific, g = general, pN =
percentage with N decimals, empty = the value's own str.

Citation keys written [@key] in the parts are renumbered as [n] in order of first
appearance, and the numbered list is rendered from references.md into the
<!-- REFERENCES --> marker.  An unresolvable placeholder or an uncited /
unmatching reference key is a hard error: this script exits non-zero rather than
producing a manuscript with a number whose home cannot be found.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = ["manuscript_part1.md", "manuscript_part2.md", "manuscript_part3.md"]
PLACEHOLDER = re.compile(r"\{\{([A-Za-z]+):([^}|]+?)(?:\|([^}]*))?\}\}")
CITE = re.compile(r"\[@([A-Za-z0-9_.:-]+)\]")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def namespaces(facts_path):
    cr = load_json(facts_path)
    return {
        "F": cr["manuscript_facts"],
        "C": cr["criteria"],
        "P": cr["prior_evidence"],
        "X": cr,
        "G": load_json(os.path.join(HERE, "search_form.json")),
    }


def resolve(root, path, ns):
    """Resolve a dotted path, longest segment first.

    Backtracking is required because artefact keys contain dots -- the spread
    grid is keyed "0.5", "1.0", "2.0" and the sign-flip tables are keyed "0.3",
    "1.497".  A greedy split on "." would never reach them.
    """
    segs = path.split(".")

    def rec(node, i):
        if i == len(segs):
            return node
        for j in range(len(segs), i, -1):
            key = ".".join(segs[i:j])
            if isinstance(node, dict) and key in node:
                got = rec(node[key], j)
                if got is not None:
                    return got
            if isinstance(node, list) and key.isdigit() and int(key) < len(node):
                got = rec(node[int(key)], j)
                if got is not None:
                    return got
        return None

    got = rec(root, 0)
    if got is None:
        raise KeyError("no such fact: %s:%s" % (ns, path))
    return got


def fmt(value, spec):
    if spec in (None, ""):
        return str(value)
    if spec == "d":
        return "%d" % int(round(float(value)))
    if spec == "g":
        return "%g" % float(value)
    m = re.fullmatch(r"(\d+)f", spec)
    if m:
        return "%.*f" % (int(m.group(1)), float(value))
    m = re.fullmatch(r"(\d+)e", spec)
    if m:
        return "%.*e" % (int(m.group(1)), float(value))
    m = re.fullmatch(r"p(\d+)", spec)
    if m:
        return "%.*f%%" % (int(m.group(1)), float(value) * 100.0)
    raise ValueError("unknown format spec %r" % spec)


def parse_references(path):
    """references.md: one entry per line, each starting with [@key]."""
    refs = {}
    if not os.path.exists(path):
        return refs
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.startswith("[@"):
                continue
            key, _, text = line[2:].partition("] ")
            refs[key] = text
    return refs


def render_citations(text, refs):
    order = []

    def repl(m):
        key = m.group(1)
        if key not in refs:
            raise KeyError("cited but no reference entry: %s" % key)
        if key not in order:
            order.append(key)
        return "[%d]" % (order.index(key) + 1)

    return CITE.sub(repl, text), order


def assemble(facts_path, refs_path=None):
    roots = namespaces(facts_path)
    refs = parse_references(refs_path or os.path.join(HERE, "references.md"))
    body = []
    for part in PARTS:
        with open(os.path.join(HERE, part), encoding="utf-8") as fh:
            body.append(fh.read())
    text = "".join(body)

    n_resolved = [0]

    def repl(m):
        ns, path, spec = m.group(1), m.group(2), m.group(3)
        if ns not in roots:
            raise KeyError("unknown namespace %r in %s" % (ns, m.group(0)))
        n_resolved[0] += 1
        return fmt(resolve(roots[ns], path, ns), spec)

    text = PLACEHOLDER.sub(repl, text)
    text, order = render_citations(text, refs)

    if "<!-- REFERENCES -->" in text:
        # The entry marker is the form the body cites with, so the bibliography and the
        # running text carry ONE numbering style (the journal's checklist names [1]-[n]).
        lines = ["[%d] %s" % (i + 1, refs[k]) for i, k in enumerate(order)]
        block = "\n".join(lines) if lines else "_(no references cited)_"
        text = text.replace("<!-- REFERENCES -->", block)
    body_text = text.split("## References")[0]
    return text, order, n_resolved[0], body_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", default=os.path.join(HERE, "canonical_results.json"))
    ap.add_argument("--refs", default=os.path.join(HERE, "references.md"))
    ap.add_argument("--out", default=os.path.join(HERE, "manuscript.md"))
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()

    text, order, n_resolved, _ = assemble(args.facts, args.refs)
    if args.stdout:
        sys.stdout.write(text)
        return 0
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("assemble: %d placeholders resolved, %d references cited -> %s"
          % (n_resolved, len(order), os.path.basename(args.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
