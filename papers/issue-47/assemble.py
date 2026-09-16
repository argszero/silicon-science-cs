#!/usr/bin/env python3
"""Assemble manuscript.md for issue #47 from the part files.

Adapted from the accepted #44 package's `assemble.py`, with two changes that this package needs:

  * the measurement namespaces are `X` = `canonical_results.json` (facts / claims / criteria) and
    `D` = the DESIGN constants, read out of the stage artefacts (`instrument_v0_results.json`) rather
    than typed -- so the grid, the replicate count and the problem parameters in the prose come from
    the same place the run did;
  * a citation key written `[@key]` must have an entry in `references.md` (the resolver's output) or
    the assembly FAILS.  That is the tie between the prose and the reference layer: a sentence
    cannot cite a work the reference layer never verified.

Nothing in the prose that a run can change is typed: every measurement is `{{ns:path|spec}}`.
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = ["manuscript_part1.md", "manuscript_part2.md", "manuscript_part3.md"]
PLACEHOLDER = re.compile(r"\{\{([A-Za-z]+):([^}|]+?)(?:\|([^}]*))?\}\}")
TABLE = re.compile(r"\{\{T:([A-Za-z0-9_]+)\}\}")
CITE = re.compile(r"\[@([A-Za-z0-9_.:-]+)\]")

# Tables rendered from an artefact rather than typed: the design grid is a run artefact like any
# other number, and a typed copy can drift from the run that produced it.
TABLES = ("profiles",)
PROFILE_COLS = ("bias", "spread", "autocorrelation", "tail probability", "tail multiplier")


def load(path):
    return json.load(io.open(path, encoding="utf-8"))


def namespaces():
    cr = load(os.path.join(HERE, "canonical_results.json"))
    v0 = load(os.path.join(HERE, "instrument_v0_results.json"))
    return {
        "X": cr,
        "D": {
            "n_profiles": len(v0["profiles"]),
            "n_lambdas": len(v0["lambdas"]),
            "replicates": v0["replicates"],
            "traces_per_rep": v0["traces_per_rep"],
            "k_pages": v0["k_pages"],
            "n_pages": v0["n_pages"],
            "n_jobs": v0["n_jobs"],
            "trace_len": v0["trace_len"],
        },
        "_v0": v0,
        # S = counts DERIVED from the aggregate itself (stages run, facts recomputed, criteria
        # declared).  Derived rather than typed: a run that adds a stage or a fact moves them.
        "S": {
            "n_stages": len(cr["stages"]),
            "n_facts": len(cr["facts"]),
            "n_criteria": len(cr["criteria"]),
            "stages_all_pass": cr["ALL_PASS"],
        },
    }


def resolve(root, path):
    """Resolve a dotted path, longest segment first.

    Backtracking is required because artefact keys contain dots: the facts are keyed
    `claim1.worst_loss_gap` and the sign-flip tables carry keys like `0.3`.  A greedy split on
    "." never reaches them.
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
        raise KeyError("no such fact: %s" % path)
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
    refs = {}
    if not os.path.exists(path):
        return refs
    for line in io.open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("[@"):
            key, _, text = line[2:].partition("] ")
            refs[key] = text
    return refs


def assemble(facts_ns=None, refs_path=None, parts=None):
    roots = facts_ns or namespaces()
    refs = parse_references(refs_path or os.path.join(HERE, "references.md"))
    text = "".join(io.open(os.path.join(HERE, p), encoding="utf-8").read()
                   for p in (parts or PARTS) if os.path.exists(os.path.join(HERE, p)))

    n = [0]

    def repl(m):
        ns, path, spec = m.group(1), m.group(2), m.group(3)
        if ns not in roots:
            raise KeyError("unknown namespace %r in %s" % (ns, m.group(0)))
        n[0] += 1
        return fmt(resolve(roots[ns], path), spec)

    n_tables = [0]

    def trepl(m):
        name = m.group(1)
        if name not in TABLES:
            raise KeyError("unknown table %r" % name)
        if name == "profiles":
            profs = roots["_v0"]["profiles"]
            if len(profs) != roots["D"]["n_profiles"]:
                raise AssertionError("table 'profiles' has %d rows, design says %d"
                                     % (len(profs), roots["D"]["n_profiles"]))
            out = ["| profile | " + " | ".join(PROFILE_COLS) + " |",
                   "|---" * (len(PROFILE_COLS) + 1) + "|"]
            for k in sorted(profs):
                b, s, a, tp, tm = profs[k]
                out.append("| `%s` | %.2f | %.2f | %.2f | %.2f | %.1f |" % (k, b, s, a, tp, tm))
            n_tables[0] += 1
            return "\n".join(out)
        raise KeyError("unhandled table %r" % name)

    text = TABLE.sub(trepl, text)
    text = PLACEHOLDER.sub(repl, text)

    order = []

    def crepl(m):
        key = m.group(1)
        if key not in refs:
            raise KeyError("cited but no reference entry: %s" % key)
        if key not in order:
            order.append(key)
        return "[%d]" % (order.index(key) + 1)

    text = CITE.sub(crepl, text)
    if "<!-- REFERENCES -->" in text:
        lines = ["[%d] %s" % (i + 1, refs[k]) for i, k in enumerate(order)]
        text = text.replace("<!-- REFERENCES -->", "\n".join(lines) if lines else "_(none cited)_")
    return text, order, n[0], n_tables[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "manuscript.md"))
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("--check-only", action="store_true",
                    help="resolve and cite-check without writing manuscript.md")
    args = ap.parse_args()
    text, order, n, nt = assemble()
    if args.stdout:
        sys.stdout.write(text)
        return 0
    if not args.check_only:
        io.open(args.out, "w", encoding="utf-8").write(text)
    print("assemble: %d placeholder(s) resolved, %d table(s) rendered, "
          "%d reference(s) cited, %d line(s)"
          % (n, nt, len(order), text.count("\n") + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
