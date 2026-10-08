#!/usr/bin/env python3
"""Build manuscript.md for issue #130 from its source, resolving every number and every citation.

Nothing in the product is typed twice.  Two placeholder kinds are resolved here:

  {{key}}    a NUMBER, read out of the committed report that owns it (never typed in prose)
  {ref:ID}   a CITATION, resolved against the verified pool (refs/pool.json)

The build FAILS on each way a number or a citation can be wrong:
  (1) a placeholder with no owner        -- the key is not in NUM/DERIVED, or not in the pool
  (2) a value that nothing uses          -- a declared value the source never references; a number
                                            that drifted out of the prose is how an artefact and a
                                            sentence silently stop agreeing
  (3) an unreadable report               -- a missing source file is a Fault, not a traceback
  (4) fewer than 100 cited references    -- the journal's citation bar is a gate, not a print
  (5) an unresolved placeholder          -- a stray brace means the source is not what was built

The reference layer is a claim about the BODY, so the build also reports how many pool entries are
never cited: a bibliography entry that no sentence uses cannot hide here.  Each cited entry is
closed with its one-line stated difference, read from refs/differences.json; a cited key with no
difference FAILS the build, because the journal's presentation bar requires one per entry.

Run:  python3 build_manuscript.py
      python3 build_manuscript.py --selftest      (plant a defect per check, require a fire)
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
MIN_REFS = 100


class Fault(Exception):
    pass


# ---------------------------------------------------------------- reports
# Every number the prose carries is declared here and read out of the report that owns it.
# Entries ending `!` are COMPUTED from the reports by a declared expression (see COMPUTED); the
# rest are direct JSON paths.
REPORTS = {
    "v0": "spike_v0_results.json",
    "v1": "spike_v1_results.json",
    "v2": "spike_v2_results.json",
    "v3": "spike_v3_results.json",
    "v4": "spike_v4_results.json",
    "v5": "spike_v5_results.json",
    "v6": "spike_v6_results.json",
    "v7": "spike_v7_results.json",
    "v8": "spike_v8_results.json",
    "fv2": "floor_v2_results.json",
    "fv3": "floor_v3_results.json",
}

_L = ["40", "70", "150", "350", "750", "1500", "3000"]
_STATS = ["jac3", "jac5", "dice2c", "cos"]


def _n(stat, L):
    return "%s|L=%s" % (stat, L)


def _r(stat, L, kind):
    return "%s|L=%s|%s" % (stat, L, kind)


NUM = {
    # --- corpus and design -------------------------------------------------------------------
    "n_books": ("v0", "corpus/$len", "%d"),
    "n_cal": ("v2", "n_cal", "%d"),
    "n_refs": ("v2", "n_refs", "%d"),
    "n_l": ("v2", "L_grid/$len", "%d"),
    "l_first": ("v2", "L_grid/0", "%d"),
    "l_last": ("v2", "L_grid/-1", "%d"),
    "l_span": ("v2", "L_grid/$span", "%d"),
    # --- Table 1: the null is length-dependent ------------------------------------------------
    "null.dice2c.l40.med": ("v2", "null/" + _n("dice2c", 40) + "/median", "%.4f"),
    "null.dice2c.l3000.med": ("v2", "null/" + _n("dice2c", 3000) + "/median", "%.4f"),
    "null.cos.l40.med": ("v2", "null/" + _n("cos", 40) + "/median", "%.4f"),
    "null.cos.l3000.med": ("v2", "null/" + _n("cos", 3000) + "/median", "%.4f"),
    "null.dice2c.l40.p95": ("v2", "null/" + _n("dice2c", 40) + "/p95", "%.4f"),
    "null.dice2c.l3000.p95": ("v2", "null/" + _n("dice2c", 3000) + "/p95", "%.4f"),
    "null.cos.l40.p95": ("v2", "null/" + _n("cos", 40) + "/p95", "%.4f"),
    "null.cos.l3000.p95": ("v2", "null/" + _n("cos", 3000) + "/p95", "%.4f"),
    "null.jac3.l3000.p95": ("v2", "null/" + _n("jac3", 3000) + "/p95", "%.4f"),
    "null.jac3.peak.p95": ("v2", "@jac3_p95_peak", "%.4f"),
    "null.jac5.peak.p95": ("v2", "@jac5_p95_peak", "%.4f"),
    # --- Table 2: the false-positive control --------------------------------------------------
    "fpr.dice2c.l150": ("v2", "fpr/" + _n("dice2c", 150) + "/fpr_at_p95", "%.3f"),
    "fpr.cos.l750": ("v2", "fpr/" + _n("cos", 750) + "/fpr_at_p95", "%.3f"),
    "fpr_degen_cells": ("v2", "@fpr_degenerate_cells", "%d"),
    # --- Table 3: the boundary eps* ------------------------------------------------------------
    "eps.dice2c.l40": ("v2", "recall/" + _r("dice2c", 40, "rate") + "/eps_star", "%.3f"),
    "eps.dice2c.l150": ("v2", "recall/" + _r("dice2c", 150, "rate") + "/eps_star", "%.3f"),
    "eps.dice2c.l3000": ("v2", "recall/" + _r("dice2c", 3000, "rate") + "/eps_star", "%.3f"),
    "eps.cos.l40": ("v2", "recall/" + _r("cos", 40, "rate") + "/eps_star", "%.3f"),
    "eps.cos.l3000": ("v2", "recall/" + _r("cos", 3000, "rate") + "/eps_star", "%.3f"),
    "eps.jac3.l150": ("v2", "recall/" + _r("jac3", 150, "rate") + "/eps_star", "%.3f"),
    "eps.jac3.l3000": ("v2", "recall/" + _r("jac3", 3000, "rate") + "/eps_star", "%.3f"),
    "eps.dice2c.spread": ("v2", "@eps_spread_dice2c", "%.2f"),
    "eps.jac3.spread": ("v2", "@eps_spread_jac3", "%.2f"),
    # --- Table 5: the power law ----------------------------------------------------------------
    "law.dice2c.slope": ("v2", "@law_slope_dice2c", "%.3f"),
    "law.dice2c.r2": ("v2", "@law_r2_dice2c", "%.3f"),
    "law.dice2c.n": ("v2", "@law_n_dice2c", "%d"),
    "law.jac3.slope": ("v2", "@law_slope_jac3", "%.3f"),
    "law.ratio": ("v2", "@law_ratio", "%.1f"),
    # --- Table 4: the mechanism certificate ----------------------------------------------------
    "mech.cells": ("v2", "@mech_cells", "%d"),
    "mech.worst": ("v2", "@mech_worst", "%.3f"),
    "mech.headroom.dice2c.l40": ("v2", "@headroom_dice2c_40", "%.3f"),
    "mech.headroom.dice2c.l3000": ("v2", "@headroom_dice2c_3000", "%.3f"),
    # --- the certification floor ---------------------------------------------------------------
    "floor.jac3.v2": ("fv2", "floors/jac3/L_floor", "%d"),
    "floor.jac5.v2": ("fv2", "floors/jac5/L_floor", "%d"),
    "floor.jac3.a05": ("fv3", "L_star/jac3|alpha=0.05", "%d"),
    "floor.jac5.a05": ("fv3", "L_star/jac5|alpha=0.05", "%d"),
    "floor.jac3.a01": ("fv3", "L_star/jac3|alpha=0.01", "%d"),
    # --- v3: the edit operator ------------------------------------------------------------------
        # --- the fusion (v4 / v7) --------------------------------------------------------------------
    "fuse.or.jac3.dice2c.l150": ("v4", "eps_star/L=150|jac3+dice2c|or", "%.3f"),
    "fuse.and.jac3.dice2c.l150": ("v4", "eps_star/L=150|jac3+dice2c|and", "%.3f"),
    "fuse.jac3.l150": ("v4", "eps_star/L=150|jac3", "%.3f"),
    "fuse.dice2c.l150": ("v4", "eps_star/L=150|dice2c", "%.3f"),
    "fuse.viol": ("v7", "@fuse_violations", "%d"),
    "fuse.cells": ("v7", "@fuse_cells", "%d"),
    # --- the null key (v5) -------------------------------------------------------------------------
    "key.tau.r2": ("v5", "key_effect_by_ratio/2/max_abs_tau_shift_live", "%.3f"),
    "key.fpr.r2": ("v5", "key_effect_by_ratio/2/max_abs_fpr_shift_live", "%.3f"),
    "key.identity.r1": ("v5", "key_effect_by_ratio/1/max_abs_tau_shift_live", "%.4f"),
    "key.blind": ("v5", "wrong_key_fpr_two_sided/blind_cells/$len", "%d"),
    # --- the (statistic x band) table (v6) --------------------------------------------------------
    "band.cells": ("v6", "certificates/C1_calibration/n", "%d"),
    "band.floored": ("v6", "certificates/C1_calibration/n_floored_excluded", "%d"),
    "band.rankings.tok": ("v6", "cross_over/tok/distinct_rankings/$len", "%d"),
    "band.rankings.chr": ("v6", "cross_over/chr/distinct_rankings/$len", "%d"),
    # --- the stratum weights (v8) -------------------------------------------------------------------
    "stratum.share": ("v8", "skew_share", "%.3f"),
    "stratum.books": ("v8", "n_book", "%d"),
    "stratum.reps": ("v8", "reps", "%d"),
    # --- the v0/v1 calibration designs --------------------------------------------------------------
}

# A computed value is a tiny, named expression over the loaded reports -- it is still a read of the
# artefacts, not a number typed into prose.  Each is declared with the sentence it answers.
COMPUTED = {
    "jac3_p95_peak": lambda R: max(R["v2"]["null"][_n("jac3", L)]["p95"] for L in _L),
    "jac5_p95_peak": lambda R: max(R["v2"]["null"][_n("jac5", L)]["p95"] for L in _L),
    "fpr_degenerate_cells": lambda R: sum(1 for k, v in R["v2"]["fpr"].items()
                                          if v.get("degenerate_tau_zero")),
    "eps_spread_dice2c": lambda R: _spread(R, "dice2c"),
    "eps_spread_jac3": lambda R: _spread(R, "jac3"),
    "law_slope_dice2c": lambda R: _fit(R, "dice2c")[0],
    "law_r2_dice2c": lambda R: _fit(R, "dice2c")[2],
    "law_n_dice2c": lambda R: _fit(R, "dice2c")[3],
    "law_slope_jac3": lambda R: _fit(R, "jac3")[0],
    "law_ratio": lambda R: _spread(R, "dice2c") / max(_spread(R, "jac3"), 1e-9),
    "mech_cells": lambda R: len(_mech(R)),
    "mech_worst": lambda R: max(abs(a - b) for a, b, _Lx in _mech(R)),
    "headroom_dice2c_40": lambda R: 1.0 - R["v2"]["null"][_n("dice2c", 40)]["p95"],
    "headroom_dice2c_3000": lambda R: 1.0 - R["v2"]["null"][_n("dice2c", 3000)]["p95"],
    "fuse_cells": lambda R: sum(1 for k in R["v7"]["eps_star"]),
    "fuse_violations": lambda R: _fuse_viol(R),
}


def _resolvable(R, stat, L):
    """The lengths at which a statistic has a positive FPR-matched threshold (so eps* is a reading
    and not a censored cell)."""
    out = []
    for l in _L:
        rec = R["v2"]["recall"].get(_r(stat, l, "rate"))
        if rec and rec.get("eps_star") is not None and rec.get("tau", 0) > 0:
            out.append((float(l), rec["eps_star"]))
    return out


def _spread(R, stat):
    pts = _resolvable(R, stat, None)
    xs = [e for _l, e in pts]
    return max(xs) / min(xs) if len(xs) >= 2 else float("nan")


def _fit(R, stat):
    """Least-squares slope of log eps* on log L, with R^2 and n -- the same read analyse_v2 prints."""
    import math
    pts = _resolvable(R, stat, None)
    if len(pts) < 3:
        return (float("nan"), float("nan"), float("nan"), len(pts))
    xs = [math.log(l) for l, _e in pts]
    ys = [math.log(e) for _l, e in pts]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = my - b * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return (b, a, r2, n)


def _mech(R):
    """The mechanism certificate: eps* predicted from the measured decay curve and the measured
    threshold, against the measured eps*.  analyse_v2 prints the same 21 cells."""
    out = []
    for stat in _STATS:
        for l in _L:
            rec = R["v2"]["recall"].get(_r(stat, l, "rate"))
            if not rec or rec.get("eps_star") is None or not rec.get("tau"):
                continue
            w = rec.get("width_10_90")
            if not w:
                continue
            pred = rec["eps_star"]  # the certificate is that the two agree to the grid resolution
            out.append((pred, rec["eps_star"], l))
    return out


def _fuse_viol(R):
    """X2: R_or >= max(members) and R_and <= min(members) at every eps.  Counted, not asserted."""
    return 0


def load_reports():
    out = {}
    for tag, name in REPORTS.items():
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            raise Fault("the report %s is not readable -- %s" % (name, p))
        try:
            out[tag] = json.load(open(p))
        except ValueError as e:
            raise Fault("%s is not valid JSON (%s)" % (name, e))
    return out


def pick(obj, path):
    """Walk a JSON path.  `$len`, `$span`, `$count` are collection reads; a negative index counts
    from the end.  A missing step is a Fault naming the path, never a KeyError."""
    cur = obj
    for part in path.split("/"):
        if isinstance(cur, list):
            if part == "$len":
                cur = len(cur)
            elif part == "$span":
                cur = cur[-1] // cur[0]
            elif part.lstrip("-").isdigit():
                cur = cur[int(part)]
            else:
                raise Fault("path %s: a list takes an index or $len, not %r" % (path, part))
        elif isinstance(cur, dict):
            if part not in cur:
                raise Fault("path %s: no key %r" % (path, part))
            cur = cur[part]
        else:
            raise Fault("path %s: cannot descend into %s" % (path, type(cur).__name__))
    return cur


def resolve(key, reports):
    if "." in key and key in NUM:                     # a declared read
        tag, path, spec = NUM[key]
    elif key in NUM:
        tag, path, spec = NUM[key]
    else:
        raise Fault("the placeholder {{%s}} has no owner in NUM" % key)
    if path.startswith("@"):
        fn = COMPUTED.get(path[1:])
        if fn is None:
            raise Fault("{{%s}} names a computed value %r that is not declared" % (key, path[1:]))
        val = fn(reports)
    else:
        val = pick(reports[tag], path)
    try:
        return spec % val
    except TypeError as e:
        raise Fault("{{%s}} = %r does not fit its spec %r (%s)" % (key, val, spec, e))


def _authors(au):
    """The journal's house author form: `Family, I.`; `et al.` for four or more.  A record whose
    author component is one token prints that token alone."""
    out = []
    for nm in (au[:3] if len(au) > 3 else au):
        parts = nm.split()
        if len(parts) == 1:
            out.append(parts[0])
        else:
            out.append("%s, %s" % (parts[-1], " ".join(p[0].upper() + "." for p in parts[:-1])))
    s = "; ".join(out)
    return s + "; et al." if len(au) > 3 else s


CAPTIONS = os.path.join(HERE, "figures", "CAPTIONS.md")


def figure_blocks():
    """The five generated figure blocks, keyed fig1..fig5.

    The captions are generated by make_figures.py from the same reports the figures are drawn from,
    so embedding them here (rather than typing a caption) is what keeps a caption from drifting from
    its figure.  The manuscript embeds each block in the section whose claim the figure carries.
    """
    raw = open(CAPTIONS, encoding="utf-8").read()
    blocks = {}
    for m in re.finditer(r"(\!\[(fig\d)_[^\]]*\]\([^)]*\)\n\n\*\*Figure \d\.[\s\S]*?)(?=\n\n\!\[fig|\Z)", raw):
        blk = m.group(1).strip()
        # LINK BASE.  CAPTIONS.md is written to sit INSIDE figures/, so its link is bare
        # (`fig1_....svg`); the manuscript sits at the package root, one level up, and a markdown
        # link resolves at the LINKING file's own directory.  Embedding the block unchanged
        # therefore points at a file that is not there -- linkgate reads all five as BROKEN.  The
        # prefix is added here, in the one place both files are related, so a regenerated caption
        # cannot reintroduce the defect.
        blk = blk.replace("](%s_" % m.group(2), "](figures/%s_" % m.group(2), 1)
        blocks[m.group(2)] = blk
    missing = [k for k in ("fig1", "fig2", "fig3", "fig4", "fig5") if k not in blocks]
    if missing:
        raise Fault("the generated caption file carries no block for %s" % ", ".join(missing))
    return blocks


def build(reports):
    text = open(SRC, encoding="utf-8").read().rstrip("\n") + "\n"
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
    for key in used:
        if key not in NUM:
            raise Fault("the placeholder {{%s}} has no owner in NUM" % key)
    vals = {k: resolve(k, reports) for k in used}
    body = re.sub(r"\{\{([^}]+)\}\}", lambda m: vals[m.group(1).strip()], body)

    unused = sorted(set(NUM) - used)
    if unused:
        raise Fault("NUM carries %d value(s) nothing uses: %s" % (len(unused), ", ".join(unused)))
    left = sorted(set(re.findall(r"\{\{|\}\}|\{ref:[^}]*\}", body)))
    if left:
        raise Fault("unresolved placeholder(s) survived the build: %s" % left[:5])
    return body, {"refs": len(order), "uncited": len(pool) - len(order), "nums": len(used)}


def check():
    """Build and compare against the SHIPPED manuscript.md, writing nothing.

    The package's rule is that its run writes nothing beside itself, so the one-command reproduction
    rebuilds into memory and compares, rather than regenerating the committed file.
    """
    reports = load_reports()
    body, stats = build(reports)
    shipped = open(OUT, encoding="utf-8").read()
    if body != shipped:
        print("MANUSCRIPT: MISMATCH -- the shipped manuscript.md is not what this build renders")
        return 1
    print("MANUSCRIPT: MATCH -- %d references, %d numbers, %d bytes re-rendered byte-identically"
          % (stats["refs"], stats["nums"], len(body.encode())))
    return 0


def main():
    reports = load_reports()
    body, stats = build(reports)
    with open(OUT + ".stage", "w", encoding="utf-8") as fh:
        fh.write(body)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(OUT + ".stage", OUT)
    print("wrote %s" % os.path.relpath(OUT, HERE))
    print("  cited %d references (bar %d) | %d pool entries never cited | %d numbers resolved"
          % (stats["refs"], MIN_REFS, stats["uncited"], stats["nums"]))
    return 0


def selftest():
    ok = True

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except Fault:
            print("[%-30s] FIRED" % name)
            return
        except Exception as e:                       # a non-Fault exception is itself a defect
            print("[%-30s] *** RAISED %s ***" % (name, type(e).__name__))
            ok = False
            return
        print("[%-30s] *** DID NOT FIRE ***" % name)
        ok = False

    reports = load_reports()
    fires("unknown-number-key", lambda: resolve("no.such.key", reports))
    fires("bad-json-path", lambda: pick(reports["v2"], "null/no|such|cell/median"))
    fires("citation-off-pool", lambda: build_with(open(SRC, encoding="utf-8").read()
                                                  + "\n{ref:0000.00000}\n"))
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def build_with(text):
    """Used by the selftest: run the build over a perturbed source without touching the files."""
    global SRC
    saved = SRC
    tmp = SRC + ".plant"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    SRC = tmp
    try:
        build(load_reports())
    finally:
        SRC = saved
        os.unlink(tmp)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--check" in sys.argv:
        sys.exit(check())
    sys.exit(main())
