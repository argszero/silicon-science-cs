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


def configs_of(cells):
    """Distinct (family, budget) configurations -- the evidence count, as against cell count."""
    return len({tuple(c["tag"].split("/")[:2]) for c in cells})


def mean(xs):
    return sum(xs) / len(xs)


def build_values(A, B):
    """Every number the prose may name, as a flat dict. Anything not here cannot be printed."""
    cellsA, cellsB = A["cells"], B["cells"]

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
        "A.configs": configs_of(cellsA),
        "B.corpus.n": B["corpus"]["n"],
        "B.corpus.d": B["corpus"]["d"],
        "B.corpus.n_queries": B["corpus"]["n_queries"],
        "B.corpus.knn": B["corpus"]["knn"],
        "B.n_cells": len(xsB),
        "B.configs": configs_of(cellsB),
    }

    # tier B carries no single stored correlation: it is composed here from the cells, exactly as
    # check_claims composes nothing and reads only stored values. Composed, not typed.
    import math
    n = len(xsB)
    lx = [math.log(x) for x in xsB]
    ly = [math.log(y) for y in ysB]
    mx, my = mean(lx), mean(ly)
    num = sum((a - mx) * (b_ - my) for a, b_ in zip(lx, ly))
    den = math.sqrt(sum((a - mx) ** 2 for a in lx) * sum((b_ - my) ** 2 for b_ in ly))
    v["B.r"] = round(num / den, 4)
    v["B.atoms_min"] = min(xsB)
    v["B.atoms_max"] = max(xsB)

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


MARK = re.compile(r"\{\{n:([^}]+)\}\}")
CITE = re.compile(r"\{\{c:([^}]+)\}\}")


def main():
    prose = open("manuscript_prose.md").read()
    A = load("results/mechanism.json")
    B = load("results/scale.json")
    try:
        refs = load("refs.json")
    except FileNotFoundError:
        print("refs.json is missing -- the bibliography has not been built yet.")
        print("  -> run build_refs.py; the paper will not render until every citation resolves.")
        return 1

    values = build_values(A, B)
    bound = []

    def sub(m):
        key = m.group(1).strip()
        if key not in values:
            raise KeyError("{{n:%s}} is not a number any artefact holds" % key)
        bound.append(values[key])
        return fmt(values[key])

    body = MARK.sub(sub, prose)

    # ---- citations -----------------------------------------------------------------------
    order = []

    def cite(m):
        slug = m.group(1).strip()
        rec = refs.get(slug)
        if rec is None:
            raise KeyError("{{c:%s}} names a reference refs.json does not hold" % slug)
        if rec.get("verification", {}).get("result") != "verified":
            raise KeyError("{{c:%s}} is not verified (%s)" % (slug, rec.get("verification")))
        if slug not in order:
            order.append(slug)
        return "[%d]" % (order.index(slug) + 1)

    body = CITE.sub(cite, body)

    uncited = [s for s in refs if s not in order]
    if uncited:
        raise KeyError("refs.json holds %d reference(s) the body never cites (padding): %s"
                       % (len(uncited), uncited[:8]))
    if len(order) < REF_FLOOR:
        raise KeyError("only %d reference(s) are held and cited; the journal's floor is %d"
                       % (len(order), REF_FLOOR))

    entries = []
    for i, slug in enumerate(order, 1):
        r = refs[slug]
        entries.append("[%d] %s" % (i, r["entry"]))
    body = body.replace("{{refs}}", "\n\n".join(entries))

    # ---- stray scan: a number the prose typed rather than bound ---------------------------
    allowed = {fmt(x) for x in bound} | {a.replace(",", "") for a in (fmt(x) for x in bound)}
    allowed |= {str(int(x)) for x in bound if isinstance(x, (int, float)) and float(x).is_integer()}
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
        if len(t.replace(".", "")) >= 2:           # section numbers are single digits
            stray.append(tok)
    if stray:
        uniq = sorted(set(stray))
        print("STRAY NUMBERS (in the prose but bound to nothing): %s" % uniq[:12])
        print("  -> every number must be a {{n:...}} marker; refusing to write the paper.")
        return 1

    body = body.replace("{{refs}}", "\n\n".join(entries))
    open("manuscript.md", "w").write(body)
    print("manuscript.md written: %d characters" % len(body))
    print("  markers bound: %d numbers, %d citations" % (len(bound), len(order)))
    print("  references: %d held, %d cited (floor %d)" % (len(refs), len(order), REF_FLOOR))
    print("  stray-number scan: clean")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyError as e:
        print("CANNOT WRITE THE PAPER: %s" % e.args[0])
        sys.exit(1)
