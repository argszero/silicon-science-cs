#!/usr/bin/env python3
"""Build manuscript.md for issue #135 from its source, resolving every number and every citation.

Nothing in the product is typed twice.  Three placeholder kinds are resolved here:

  {{key}}    a NUMBER, read out of the committed report that owns it (never typed in prose)
  {ref:ID}   a CITATION, resolved against the verified pool (refs/pool.json)
  {{figN}}   a FIGURE BLOCK, assembled from the generated figures/CAPTIONS.md

The build FAILS on each way a number, a citation or a figure can be wrong:
  (1) a placeholder with no owner          -- the key is not in NUM, or not in the pool
  (2) a value that nothing uses            -- a declared value the source never references; a
                                              number that drifted out of the prose is how an
                                              artefact and a sentence silently stop agreeing
  (3) an unreadable report                 -- a missing source file is a Fault, not a traceback
  (4) fewer than 100 cited references      -- the journal's citation bar is a gate, not a print
  (5) an unresolved placeholder            -- a stray brace means the source is not what was built
  (6) a cited key with no stated difference-- the presentation bar wants one line per entry
  (7) a figure block whose image is absent -- a link that resolves nowhere is a defect on the product

The reference layer is a claim about the BODY, so the build also reports how many pool entries are
never cited.  Each cited entry ends with its one-line stated difference, read from
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
CAPTIONS = os.path.join(HERE, "figures", "CAPTIONS.md")
MIN_REFS = 100

REPORTS = {
    "v0": "spike_v0_results.json",
    "v1": "spike_v1_results.json",
    "v2": "spike_v2_results.json",
    "v3": "spike_v3_results.json",
}


class Fault(Exception):
    pass


def load_reports(here=HERE):
    out = {}
    for tag, rel in REPORTS.items():
        path = os.path.join(here, rel)
        if not os.path.isfile(path):
            raise Fault("report %s is missing at %s" % (tag, rel))
        try:
            out[tag] = json.load(open(path, encoding="utf-8"))
        except ValueError as e:
            raise Fault("report %s is not readable JSON: %s" % (tag, e))
    return out


def pick(doc, path):
    cur = doc
    for part in path.split("/"):
        if isinstance(cur, list):
            if part == "$len":
                cur = len(cur)
            elif part.lstrip("-").isdigit():
                cur = cur[int(part)]
            else:
                raise Fault("path %s: a list takes an index or $len, not %r" % (path, part))
        elif isinstance(cur, dict):
            if part not in cur:
                try:
                    num = float(part)
                except ValueError:
                    num = None
                if num is not None and num in cur:
                    cur = cur[num]
                    continue
                raise Fault("path %s: no key %r" % (path, part))
            cur = cur[part]
        else:
            raise Fault("path %s: cannot descend into %s" % (path, type(cur).__name__))
    return cur


def _eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(b, float) or isinstance(a, float):
        return abs(a - b) < 1e-9
    return a == b


def _cell1(rep, key, **want):
    """The unique cell of a report's list at `key` matching every field in `want`."""
    rows = [c for c in rep[key] if all(_eq(c[k], v) for k, v in want.items())]
    if len(rows) != 1:
        raise Fault("%s: %d cells match %s (want exactly 1)" % (key, len(rows), want))
    return rows[0]


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _c11(rep):
    return rep["v2"]["checks"]["C11_spread_ratio"]


def _c17(rep):
    return rep["v3"]["checks"]["C17_closed_form_comparison"]


def _devs(rep, field):
    """|dev_X| (A/B/C) over the cells the three-form comparison (fig5) is drawn on: the linear
    probing, uniform-hashing arm at a 1e-3 level.  The scope is stated because a mean deviation
    quoted without its cell set is not comparable to the figure's."""
    rows = _c17(rep)["linear|uniform|0.001"]
    return [abs(row[field]) for row in rows.values() if row.get(field) is not None]


def _devs_C(rep):
    rows = rep["v3"]["checks"]["C19_scheme_calibrated"]["rows"]["linear|uniform|0.001"]
    return [abs(row["dev_C"]) for row in rows.values() if row.get("dev_C") is not None]


COMPUTED = {
    # --- v0: the linear-probing arm ---------------------------------------------------------
    "v0_fs_dip": lambda r: r["v0"]["checks"]["C5_finite_size"]["rows"][1]["abs_mean_dev"],
    "v0_p99_max": lambda r: max(v["mean"] for v in r["v0"]["checks"]["C2_p99_over_mean"].values()),
    # --- v2: the P2 decision on the larger grid ---------------------------------------------
    "v2_spread_max": lambda r: max(v["ratio"] for v in _c11(r).values() if v.get("ratio") is not None),
    "v2_hold_cells": lambda r: sum(1 for v in _c11(r).values() if v.get("registered_holds")),
    "v2_cells_total": lambda r: len(_c11(r)),
    "v2_hold_linear_ge90": lambda r: sum(
        1 for k, v in _c11(r).items()
        if k.startswith("linear|") and float(k.rsplit("|", 1)[1]) >= 0.90 and v.get("registered_holds")),
    "v2_lin_ge90_total": lambda r: sum(
        1 for k in _c11(r) if k.startswith("linear|") and float(k.rsplit("|", 1)[1]) >= 0.90),
    "v2_oos_worst_cluster": lambda r: max(
        v["cluster_longest_run"]["worst_rel_dev"]
        for v in r["v2"]["checks"]["C12_out_of_sample"].values()),
    "v2_oos_within_cluster": lambda r: sum(
        1 for v in r["v2"]["checks"]["C12_out_of_sample"].values()
        if v["cluster_longest_run"]["within_20pct"]),
    "v2_oos_cells": lambda r: len(r["v2"]["checks"]["C12_out_of_sample"]),
    "v2_tx_worst": lambda r: max(v["worst_rel_dev"]
                                 for v in r["v2"]["checks"]["C15_cross_scheme_transport"].values()),
    # --- v3: the theory arm ------------------------------------------------------------------
    "v3_A_worst": lambda r: max(_devs(r, "dev_A")),
    "v3_A_meandev": lambda r: _mean(_devs(r, "dev_A")),
    "v3_B_meandev": lambda r: _mean(_devs(r, "dev_B")),
    "v3_C_meandev": lambda r: _mean(_devs_C(r)),
    "v3_A_over_B": lambda r: _mean(_devs(r, "dev_A")) / _mean(_devs(r, "dev_B")),
    "v3_bracketed": lambda r: sum(
        1 for cells in r["v3"]["checks"]["C16_measured_boundary"].values()
        for row in cells.values() if row["crossing"].get("bracketed")),
}

# name -> (report tag, path-or-computed-name, format spec)
NUM = {
    # ---- instrument --------------------------------------------------------------------------
    "sim.m": ("v2", "m", "%d"),
    "sim.m.v3": ("v3", "m", "%d"),
    "v0.cells": ("v0", "cells/$len", "%d"),
    "v1.cells": ("v1", "cells/$len", "%d"),
    "v2.cells": ("v2", "cells/$len", "%d"),
    "v3.cells": ("v3", "cells/$len", "%d"),
    "v3.alphas": ("v3", "alphas/$len", "%d"),
    "v2.seeds": ("v2", "seeds/$len", "%d"),
    "v1.kmax": ("v1", "kmaxes/$len", "%d"),

    # ---- v0: the classical forms and the mean (P1) -------------------------------------------
    "v0.c1.pass": ("v0", "checks/C1_mean_agreement/pass", "%d"),
    "v0.c1.fail": ("v0", "checks/C1_mean_agreement/fail", "%d"),
    "v0.c1.band": ("v0", "checks/C1_mean_agreement/band", "%g"),
    "v0.c1.worst": ("v0", "checks/C1_mean_agreement/worst_rel_dev", "%.3f"),
    "v0.plant.fires": ("v0", "checks/C1_plant_identity/fires", "%s"),
    "v0.uni.mixer": ("v0", "checks/C4_uniformity/mixer/max", "%g"),
    "v0.uni.plant": ("v0", "checks/C4_uniformity/plant/max", "%g"),
    "v0.fs.m4096": ("v0", "checks/C5_finite_size/rows/0/abs_mean_dev", "%.3f"),
    "v0.fs.m16384": ("v0", "checks/C5_finite_size/rows/1/abs_mean_dev", "%.3f"),
    "v0.fs.m65536": ("v0", "checks/C5_finite_size/rows/2/abs_mean_dev", "%.3f"),
    "v0.fs.n": ("v0", "checks/C5_finite_size/rows/2/n", "%d"),
    "v0.p99.95": ("v0", "checks/C2_p99_over_mean/uniform@0.95/mean", "%.2f"),
    "v0.p99.90": ("v0", "checks/C2_p99_over_mean/uniform@0.90/mean", "%.2f"),
    "v0.p99.85": ("v0", "checks/C2_p99_over_mean/uniform@0.85/mean", "%.2f"),
    "v0.p99.max": ("v0", "v0_p99_max", "%.2f"),
    "v0.spread.85": ("v0", "checks/C6_instance_spread/uniform@0.85/spread_ratio_p99_over_mean", "%.2f"),

    # ---- v1: the classical form against two schemes -------------------------------------------
    "v1.dev.rh99": ("v1", "checks/C10_deviation_from_linear_formula/robinhood|0.99/mean", "%.3f"),
    "v1.dev.rh99.spread": ("v1", "checks/C10_deviation_from_linear_formula/robinhood|0.99/spread", "%.3f"),
    "v1.dev.rh50": ("v1", "checks/C10_deviation_from_linear_formula/robinhood|0.50/mean", "%.3f"),
    "v1.dev.lin95.spread": ("v1", "checks/C10_deviation_from_linear_formula/linear|0.95/spread", "%.2f"),
    "v1.dev.lin50.spread": ("v1", "checks/C10_deviation_from_linear_formula/linear|0.50/spread", "%.3f"),
    "v1.chi2.low": ("v1", "checks/C4_uniformity_chi2/power_by_load/0.01/separates", "%s"),
    "v1.chi2.hi": ("v1", "checks/C4_uniformity_chi2/power_by_load/0.10/separates", "%s"),

    # ---- v2: is the instance the level? (P2) --------------------------------------------------
    "v2.spread.max": ("v2", "v2_spread_max", "%.2f"),
    "v2.spread.uni90": ("v2", "checks/C11_spread_ratio/linear|uniform|0.90/ratio", "%.2f"),
    "v2.spread.uni50": ("v2", "checks/C11_spread_ratio/linear|uniform|0.50/ratio", "%.2f"),
    "v2.spread.uni97": ("v2", "checks/C11_spread_ratio/linear|uniform|0.97/ratio", "%.2f"),
    "v2.hold.cells": ("v2", "v2_hold_cells", "%d"),
    "v2.cells.total": ("v2", "v2_cells_total", "%d"),
    "v2.hold.linear.ge90": ("v2", "v2_hold_linear_ge90", "%d"),
    "v2.lin.ge90.total": ("v2", "v2_lin_ge90_total", "%d"),
    "v2.oos.worst": ("v2", "v2_oos_worst_cluster", "%.3f"),
    "v2.oos.within": ("v2", "v2_oos_within_cluster", "%d"),
    "v2.oos.cells": ("v2", "v2_oos_cells", "%d"),
    "v2.c14.pairs": ("v2", "checks/C14_clustering_is_not_scheme_invariant/n_pairs", "%d"),
    "v2.c14.same": ("v2", "checks/C14_clustering_is_not_scheme_invariant/same_longest_run", "%d"),
    "v2.c14.min": ("v2", "checks/C14_clustering_is_not_scheme_invariant/p99_ratio_linear_over_robinhood/min", "%.1f"),
    "v2.c14.med": ("v2", "checks/C14_clustering_is_not_scheme_invariant/p99_ratio_linear_over_robinhood/median", "%.1f"),
    "v2.c14.max": ("v2", "checks/C14_clustering_is_not_scheme_invariant/p99_ratio_linear_over_robinhood/max", "%.1f"),
    "v2.tx.max": ("v2", "v2_tx_worst", "%.1f"),
    "v2.tx.50": ("v2", "checks/C15_cross_scheme_transport/sequential|0.50/worst_rel_dev", "%.2f"),

    # ---- v3: the budget boundary (P3) and the theory arm --------------------------------------
    "v3.b.lin2": ("v3", "checks/C16_measured_boundary/linear|uniform|0.001/2/crossing/alpha", "%.4f"),
    "v3.b.lin8": ("v3", "checks/C16_measured_boundary/linear|uniform|0.001/8/crossing/alpha", "%.3f"),
    "v3.b.lin16": ("v3", "checks/C16_measured_boundary/linear|uniform|0.001/16/crossing/alpha", "%.3f"),
    "v3.b.lin64": ("v3", "checks/C16_measured_boundary/linear|uniform|0.001/64/crossing/alpha", "%.3f"),
    "v3.b.rh4": ("v3", "checks/C16_measured_boundary/robinhood|uniform|0.001/4/crossing/alpha", "%.3f"),
    "v3.b.rh8": ("v3", "checks/C16_measured_boundary/robinhood|uniform|0.001/8/crossing/alpha", "%.3f"),
    "v3.b.rh16": ("v3", "checks/C16_measured_boundary/robinhood|uniform|0.001/16/crossing/alpha", "%.3f"),
    "v3.b.rh32.bound": ("v3", "checks/C16_measured_boundary/robinhood|uniform|0.001/32/crossing/bound", "%s"),
    "v3.bracketed": ("v3", "v3_bracketed", "%d"),
    "v3.A.worst": ("v3", "v3_A_worst", "%.3f"),
    "v3.A.meandev": ("v3", "v3_A_meandev", "%.3f"),
    "v3.B.meandev": ("v3", "v3_B_meandev", "%.3f"),
    "v3.C.meandev": ("v3", "v3_C_meandev", "%.3f"),
    "v3.A.over.B": ("v3", "v3_A_over_B", "%.2f"),
    "v3.decay.lin.lo": ("v3", "checks/C18_geometric_in_k/linear|0.30/ratio", "%.3f"),
    "v3.decay.lin.hi": ("v3", "checks/C18_geometric_in_k/linear|0.95/ratio", "%.3f"),
    "v3.decay.rh.lo": ("v3", "checks/C18_geometric_in_k/robinhood|0.30/ratio", "%.3f"),
    "v3.decay.rh.hi": ("v3", "checks/C18_geometric_in_k/robinhood|0.95/ratio", "%.3f"),
    "v3.c.linear": ("v3", "checks/C19_scheme_calibrated/c_by_scheme/linear", "%.3f"),
    "v3.c.rh": ("v3", "checks/C19_scheme_calibrated/c_by_scheme/robinhood", "%.3f"),
}


def resolve(key, reports):
    if key not in NUM:
        raise Fault("the placeholder {{%s}} has no owner in NUM" % key)
    tag, path, spec = NUM[key]
    head, _, rest = path.partition("/")
    if head in COMPUTED:
        val = COMPUTED[head](reports)
        if rest:
            val = pick(val, rest)
    else:
        val = pick(reports[tag], path)
    try:
        return spec % val
    except (TypeError, ValueError) as e:
        raise Fault("{{%s}} = %r does not fit its spec %r (%s)" % (key, val, spec, e))


def _authors(au):
    """The journal's house author form: `Family, I.`; `et al.` for four or more."""
    out = []
    for nm in (au[:3] if len(au) > 3 else au):
        parts = nm.split()
        if len(parts) == 1:
            out.append(parts[0])
        else:
            out.append("%s, %s" % (parts[-1], " ".join(p[0].upper() + "." for p in parts[:-1])))
    s = "; ".join(out)
    return s + "; et al." if len(au) > 3 else s


def figure_blocks(captions_path=CAPTIONS):
    """The six figure blocks, keyed fig1..fig6, assembled from the generated CAPTIONS.md.

    CAPTIONS.md is generated by make_figures.py from the same reports the SVGs are drawn from, so a
    caption cannot drift from its picture.  It carries one section per figure:

        ## `fig1_budget_boundary.svg`

        <caption text>

    The manuscript sits at the PACKAGE ROOT while the SVGs sit in figures/, and a markdown link
    resolves at the LINKING file's own directory -- so the link is written here, in the one place
    both files are related, rather than assumed.
    """
    raw = open(captions_path, encoding="utf-8").read()
    blocks = {}
    pat = re.compile(r"^## `(fig(\d)_[a-z_]+\.svg)`\s*\n\s*\n([\s\S]*?)(?=\n## |\Z)", re.M)
    for m in pat.finditer(raw):
        name, num, text = m.group(1), m.group(2), m.group(3).strip()
        head, _, rest = text.partition(". ")
        title = head.rstrip(".") if rest else text
        body = rest if rest else ""
        if not os.path.isfile(os.path.join(HERE, "figures", name)):
            raise Fault("the caption file names %s but figures/ does not carry it" % name)
        blocks["fig%s" % num] = "![%s](figures/%s)\n\n**Figure %s. %s.** %s" % (
            name, name, num, title, body)
    missing = [k for k in ("fig1", "fig2", "fig3", "fig4", "fig5", "fig6") if k not in blocks]
    if missing:
        raise Fault("the generated caption file carries no block for %s" % ", ".join(missing))
    return blocks


def _expand_refs(text):
    """Normalise a comma-grouped citation list into single-key braces.

    Prose carries `{ref:A, ref:B, ref:C}` so a family reads as one line; the resolver and the
    reference list work on one key per brace, so the grouping is expanded HERE -- in one place, before
    anything reads it -- rather than taught to every reader."""
    def repl(m):
        parts = [p.strip() for p in m.group(1).split(",")]
        parts = [p[4:].strip() if p.startswith("ref:") else p for p in parts if p.strip()]
        return " ".join("{ref:%s}" % p for p in parts)
    return re.sub(r"\{ref:([^}]+)\}", repl, text)


def build(reports, src_path=SRC):
    text = _expand_refs(open(src_path, encoding="utf-8").read()).rstrip("\n") + "\n"
    figs = figure_blocks()
    seen = set(re.findall(r"\{\{(fig\d)\}\}", text))
    for k in seen:
        if k not in figs:
            raise Fault("the source embeds {{%s}} but the caption file carries no such block" % k)
    text = re.sub(r"\{\{(fig\d)\}\}", lambda m: figs[m.group(1)], text)

    pool = json.load(open(POOL, encoding="utf-8"))
    diffs = json.load(open(DIFFS, encoding="utf-8"))

    order = []
    for m in re.finditer(r"\{ref:([^}]+)\}", text):
        k = m.group(1).strip()
        if k not in pool:
            raise Fault("the citation key '%s' is not in the verified pool (%d entries)"
                        % (k, len(pool)))
        if k not in order:
            order.append(k)
    index = {k: i + 1 for i, k in enumerate(order)}
    body = re.sub(r"\{ref:([^}]+)\}", lambda m: "[%d]" % index[m.group(1).strip()], text)

    lines = ["## References", ""]
    for k in order:
        v = pool[k]
        if k not in diffs:
            raise Fault("cited reference %s carries no stated difference" % k)
        names = _authors(v.get("authors") or [])
        yr = str(v.get("published", ""))[:4]
        if v["source"] == "crossref":
            ident, link = v["id"], "https://doi.org/%s" % v["id"]
        else:
            ident, link = "arXiv:%s" % v["id"], "https://arxiv.org/abs/%s" % v["id"]
        title = v["title"].rstrip().rstrip(".")
        venue = v.get("container") or ident
        lines.append("[%d] %s (%s). %s. %s. %s — Difference: %s"
                     % (index[k], names, yr, title, venue, link, diffs[k]))
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    body = body + "\n" + "\n".join(lines) + "\n"

    if len(order) < MIN_REFS:
        raise Fault("only %d references are cited; the journal bar is %d" % (len(order), MIN_REFS))

    used = set(re.findall(r"\{\{([^}]+)\}\}", body))
    vals = {}
    for key in used:
        if key not in NUM:
            raise Fault("the placeholder {{%s}} has no owner in NUM" % key)
        vals[key] = resolve(key, reports)
    body = re.sub(r"\{\{([^}]+)\}\}", lambda m: vals[m.group(1).strip()], body)

    unused = sorted(set(NUM) - used)
    if unused:
        raise Fault("NUM carries %d value(s) nothing uses: %s" % (len(unused), ", ".join(unused)))
    left = sorted(set(re.findall(r"\{\{|\}\}|\{ref:[^}]*\}", body)))
    if left:
        raise Fault("unresolved placeholder(s) survived the build: %s" % left[:5])
    return body, {"refs": len(order), "uncited": len(pool) - len(order), "nums": len(used),
                  "bytes": len(body.encode("utf-8"))}


def check():
    body, stats = build(load_reports())
    shipped = open(OUT, encoding="utf-8").read()
    if body != shipped:
        print("MANUSCRIPT: MISMATCH -- the shipped manuscript.md is not what this build renders")
        return 1
    print("MANUSCRIPT: MATCH -- %d references, %d numbers, %d bytes re-rendered byte-identically"
          % (stats["refs"], stats["nums"], stats["bytes"]))
    return 0


def build_with(text):
    tmp = SRC + ".plant"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    try:
        return build(load_reports(), src_path=tmp)
    finally:
        os.unlink(tmp)


def _a_key_without_difference():
    pool = json.load(open(POOL, encoding="utf-8"))
    diffs = json.load(open(DIFFS, encoding="utf-8"))
    for k in sorted(pool):
        if k not in diffs:
            return k
    raise Fault("every pool entry carries a difference -- the plant has nothing to plant")


def _unused_number_plant():
    """Declare a number the source never references; the build must refuse to render."""
    NUM["zz.unused.plant"] = ("v0", "cells/$len", "%d")
    try:
        build(load_reports())
    finally:
        del NUM["zz.unused.plant"]


def _fig_missing_plant():
    """Point a caption at a figure file that is not there; the build must refuse.

    The plant is written OUTSIDE the package (the package's rule is that its run writes nothing
    beside itself) and removed in a `finally`.
    """
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".md")
    try:
        text = open(CAPTIONS, encoding="utf-8").read().replace("fig1_budget_boundary.svg",
                                                               "fig1_no_such_file.svg")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        figure_blocks(captions_path=tmp)
    finally:
        os.unlink(tmp)


def selftest():
    ok = True

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except Fault:
            print("[%-32s] FIRED" % name)
            return
        except Exception as e:
            print("[%-32s] *** RAISED %s ***" % (name, type(e).__name__))
            ok = False
            return
        print("[%-32s] *** DID NOT FIRE ***" % name)
        ok = False

    reports = load_reports()
    src = open(SRC, encoding="utf-8").read()
    fires("unknown-number-key", lambda: resolve("no.such.key", reports))
    fires("bad-json-path", lambda: pick(reports["v2"], "cells/x/y/z"))
    fires("citation-off-pool", lambda: build_with(src + "\n{ref:0000.00000}\n"))
    fires("cited-with-no-difference", lambda: build_with(src + "\n{ref:%s}\n" % _a_key_without_difference()))
    fires("unused-number", _unused_number_plant)
    fires("figure-file-missing", _fig_missing_plant)
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def main():
    body, stats = build(load_reports())
    with open(OUT + ".stage", "w", encoding="utf-8") as fh:
        fh.write(body)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(OUT + ".stage", OUT)
    print("wrote %s" % os.path.relpath(OUT, HERE))
    print("  cited %d references (bar %d) | %d pool entries never cited | %d numbers resolved"
          % (stats["refs"], MIN_REFS, stats["uncited"], stats["nums"]))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--check" in sys.argv:
        sys.exit(check())
    sys.exit(main())
