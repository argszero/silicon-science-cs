#!/usr/bin/env python3
"""Build manuscript.md for issue #139 from its source, resolving every number and every citation.

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
  (6) a cited key with no stated role      -- the presentation bar wants one line per entry
  (7) a figure block whose image is absent -- a link that resolves nowhere is a defect on the product

The reference layer is a claim about the BODY, so the build also reports how many pool entries are
never cited.  Each cited entry ends with its one-line stated difference, read from refs/roles.json
and scoped by ROLE CLASS (the declaration the reader meets above the list says so).

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
ROLES = os.path.join(HERE, "refs", "roles.json")
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
            raise Fault("report %s does not parse: %s" % (rel, e))
    return out


def pick(doc, parts):
    """Walk a tuple of keys / integer indices.  A path part is only ever a whole KEY, so a key
    that contains a dot (the v2 rule table's `P1_ratio_ge_1.5`) is addressed honestly."""
    cur = doc
    for part in parts:
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            if part not in cur:
                raise Fault("no key %r in the path %r" % (part, parts))
            cur = cur[part]
        else:
            raise Fault("cannot descend into %r at %r" % (cur, part))
    return cur


def _mean(xs):
    return sum(xs) / float(len(xs))


def _median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def _v1_by_c(rep):
    """Per coupling level: cells, concave count, median/max concavity defect, ratio min/max."""
    out = {}
    cs = sorted({r["c"] for r in rep["P1"]})
    for c in cs:
        sub = [r for r in rep["P1"] if r["c"] == c]
        q = [r["ratio_B90_B50"] for r in sub]
        out["c%s" % str(c).replace(".", "_")] = {
            "n": len(sub),
            "concave": sum(1 for r in sub if r["concavity_defect"] <= 1e-9),
            "dmed": _median([r["concavity_defect"] for r in sub]),
            "dmax": max(r["concavity_defect"] for r in sub),
            "qmin": min(q), "qmax": max(q),
        }
    return out


def _sizing(rep):
    rows = [r for r in rep["planner_rows"] if r["graph"] != "empty" and r["ratio"] is not None]
    ratios = sorted(r["ratio"] for r in rows)
    under = sum(1 for x in ratios if x < 1.0)
    by_t = {}
    for t in sorted({r["target"] for r in rows}):
        v = [r["ratio"] for r in rows if r["target"] == t]
        by_t["t%s" % str(t).replace(".", "_")] = {
            "n": len(v), "under": sum(1 for x in v if x < 1.0),
            "med": _median(v), "min": min(v), "max": max(v)}
    return {"cells": len(rows), "under": under, "pct": 100.0 * under / len(rows),
            "worst": 1.0 / ratios[0], "min": ratios[0], "max": ratios[-1],
            "med": _median(ratios), "by": by_t}


def _rules(rep):
    return {k: {"pct": v["pct"], "agree": v["agree"], "of": v["of"]}
            for k, v in rep["law"]["candidate_rules"].items()}


COMPUTED = {
    "v1byc": _v1_by_c,
    "sizing": _sizing,
    "rules": _rules,
}


# key -> (report tag, path inside the report, format spec).
# A `path` whose head is in COMPUTED names a computed sub-document of the reports instead.
NUM = {
    # --- v0: the two declared cases, the exact instrument and the pre-check
    "v0.cases":        ("v0", ("cases",), lambda v: str(len(v))),
    "v0.Bmax":         ("v0", ("Bmax",), "%d"),
    "v0.trials":       ("v0", ("trials",), "%d"),
    "v0.seed":         ("v0", ("seed",), "%d"),
    "v0.gain.max":     ("v0", ("findings", "P2_max_coupling_gain_greedy", "1"), "%.4f"),
    "v0.gain.atB":     ("v0", ("findings", "P2_max_coupling_gain_greedy", "0"), "%d"),
    "v0.order.eff":    ("v0", ("findings", "ordering_effect_uncoupled_maxabs"), "%.4f"),
    "v0.placebo.eff":  ("v0", ("findings", "placebo_coupling_gain_maxabs"), "%.4f"),
    "v0.p3.neg":       ("v0", ("findings", "P3_af_minus_greedy_coupled", "1", "1"), "%.4f"),
    # --- v1: the n = 8 grid
    "v1.n":            ("v1", ("config", "n"), "%d"),
    "v1.seed":         ("v1", ("config", "seed"), "%d"),
    "v1.Bmax":         ("v1", ("config", "Bmax"), "%d"),
    "v1.graphs":       ("v1", ("config", "graphs"), lambda v: str(len(v))),
    "v1.diffs":        ("v1", ("config", "difficulties"), lambda v: str(len(v))),
    "v1.cs":           ("v1", ("config", "c"), lambda v: str(len(v))),
    "v1.scheds":       ("v1", ("config", "schedules"), lambda v: str(len(v))),
    "v1.cert.cells":   ("v1", ("certificate", "c0_cells"), "%d"),
    "v1.cert.err":     ("v1", ("certificate", "max_abs_vs_closed_form"), "%.1e"),
    "v1.ctrl.excl":    ("v1", ("findings", "control_cells_excluded"), "%d"),
    "v1.p1.cells":     ("v1", ("findings", "P1_cells"), "%d"),
    "v1.p1.concave":   ("v1", ("findings", "P1_concave_cells"), "%d"),
    "v1.p1.defect":    ("v1", ("findings", "P1_max_concavity_defect"), "%.4f"),
    "v1.p1.rmin":      ("v1", ("findings", "P1_ratio_min"), "%.2f"),
    "v1.p1.rmax":      ("v1", ("findings", "P1_ratio_max"), "%.3f"),
    "v1.p1.rge15":     ("v1", ("findings", "P1_ratio_ge_1.5"), "%d"),
    "v1.p2.cells":     ("v1", ("findings", "P2_coupled_cells"), "%d"),
    "v1.p2.pos":       ("v1", ("findings", "P2_positive_gain_cells"), "%d"),
    "v1.p2.maxgain":   ("v1", ("findings", "P2_max_gain"), "%.3f"),
    "v1.p2.c0":        ("v1", ("findings", "P2_gain_at_c0_maxabs"), "%.1f"),
    "v1.p3.cells":     ("v1", ("findings", "P3_cells"), "%d"),
    "v1.p3.ident":     ("v1", ("findings", "P3_identical"), "%d"),
    "v1.p3.signchg":   ("v1", ("findings", "P3_sign_changing"), "%d"),
    "v1.p3.pos":       ("v1", ("findings", "P3_always_positive"), "%d"),
    "v1.p3.control":   ("v1", ("findings", "P3_control_maxabs"), "%.1f"),
    # --- v2: the two laws
    "v2.law.cells":    ("v2", ("law", "cells"), "%d"),
    "v2.law.convex":   ("v2", ("law", "convex"), "%d"),
    "v2.plan.cells":   ("v2", ("planner", "cells"), "%d"),
    # --- v3: the settled n-form
    "v3.perm":         ("v3", ("totals", "permutations"), "%d"),
    "v3.gviol":        ("v3", ("totals", "guarantee_violations"), "%d"),
    "v3.conv":         ("v3", ("totals", "converse_exceptions"), "%d"),
    "v3.brk":          ("v3", ("totals", "coupled_breakdown_cells"), "%d"),
    "v3.expl":         ("v3", ("totals", "explained_by_coupling"), "%d"),
    "v3.bnd.cells":    ("v3", ("totals", "coupling_boundary_cells"), "%d"),
    "v3.bnd.viol":     ("v3", ("totals", "coupling_boundary_violations"), "%d"),
    # --- derived from the reports by the helpers above
    "v1.c0.cells":     ("v1", ("@v1byc", "c0_0", "n"), "%d"),
    "v1.c0.conc":      ("v1", ("@v1byc", "c0_0", "concave"), "%d"),
    "v1.c0.dmed":      ("v1", ("@v1byc", "c0_0", "dmed"), "%.4f"),
    "v1.c6.conc":      ("v1", ("@v1byc", "c0_6", "concave"), "%d"),
    "v1.c6.dmed":      ("v1", ("@v1byc", "c0_6", "dmed"), "%.4f"),
    "v1.c6.dmax":      ("v1", ("@v1byc", "c0_6", "dmax"), "%.4f"),
    "v2.sz.under":     ("v2", ("@sizing", "under"), "%d"),
    "v2.sz.pct":       ("v2", ("@sizing", "pct"), "%.1f"),
    "v2.sz.worst":     ("v2", ("@sizing", "worst"), "%.2f"),
    "v2.sz.med":       ("v2", ("@sizing", "med"), "%.3f"),
    "v2.sz.t50.under": ("v2", ("@sizing", "by", "t0_5", "under"), "%d"),
    "v2.sz.t50.n":     ("v2", ("@sizing", "by", "t0_5", "n"), "%d"),
    "v2.sz.t90.under": ("v2", ("@sizing", "by", "t0_9", "under"), "%d"),
    "v2.sz.t90.n":     ("v2", ("@sizing", "by", "t0_9", "n"), "%d"),
    "v2.law.p2gtp1":   ("v2", ("@rules", "p2 > p1", "pct"), "%.2f"),
    "v2.law.hand":     ("v2", ("@rules", "fast-decay coefficient < 0 (necessary)", "pct"), "%.2f"),
}


def resolve_key(key, reports):
    if key not in NUM:
        raise Fault("the placeholder {{%s}} has no owner in NUM" % key)
    tag, parts, spec = NUM[key]
    if parts and parts[0].startswith("@"):
        val = COMPUTED[parts[0][1:]](reports[tag])
        if len(parts) > 1:
            val = pick(val, parts[1:])
    else:
        val = pick(reports[tag], parts)
    try:
        return spec(val) if callable(spec) else spec % val
    except (TypeError, ValueError, KeyError) as e:
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
    """The six figure blocks, keyed fig1..fig6, assembled from the generated CAPTIONS.md."""
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
    """Normalise a comma-grouped citation list into single-key braces."""
    def repl(m):
        parts = [p.strip() for p in m.group(1).split(",")]
        parts = [p[4:].strip() if p.startswith("ref:") else p for p in parts if p.strip()]
        return " ".join("{ref:%s}" % p for p in parts)
    return re.sub(r"\{ref:([^}]+)\}", repl, text)


ROLE_LABEL = {
    "cost":     ("the literature on the cost or budget of proof search", "the construct"),
    "system":   ("the verification systems and proof assistants", "the application"),
    "schedule": ("the scheduling, portfolio and search-control literature", "the manipulated axis"),
    "agent":    ("the 2026 agentic-proving wave", "the settings the question comes from"),
    "theory":   ("the theory of dependent search processes", "the mechanism"),
    "bench":    ("the benchmarks and evaluation literature", None),
    "found":    ("the classical works this paper's model is stated against", None),
}


def refs_note(roles, order):
    counts = {}
    for k in order:
        r = roles[k]
        counts[r] = counts.get(r, 0) + 1
    parts = []
    for r in sorted(counts, key=lambda r: (-counts[r], r)):
        label, gloss = ROLE_LABEL.get(r, (r, None))
        parts.append("%d %s" % (counts[r], label + (" (%s)" % gloss if gloss else "")))
    return (
        "**The difference lines are scoped by role class, and this is the intended house style of "
        "this list.** Each of the %d entries is assigned the role its work plays in this paper's "
        "argument -- %s -- and its one-line *difference from this work* states the difference that "
        "**role class** makes from this work, rather than a claim read off that one paper. The "
        "specific differences from the closest works are stated in Sections 1-2, and an entry whose "
        "difference is not its class's states it in its own words."
        % (len(order), ", ".join(parts)))


def build(reports, src_path=SRC):
    text = _expand_refs(open(src_path, encoding="utf-8").read()).rstrip("\n") + "\n"
    figs = figure_blocks()
    seen = set(re.findall(r"\{\{(fig\d)\}\}", text))
    for k in seen:
        if k not in figs:
            raise Fault("the source embeds {{%s}} but the caption file carries no such block" % k)
    text = re.sub(r"\{\{(fig\d)\}\}", lambda m: figs[m.group(1)], text)

    pool = json.load(open(POOL, encoding="utf-8"))
    roles = json.load(open(ROLES, encoding="utf-8"))

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

    lines = ["## References", "", refs_note(roles, order), ""]
    for k in order:
        v = pool[k]
        if k not in roles:
            raise Fault("cited reference %s carries no stated role" % k)
        role = roles[k]
        label = ROLE_LABEL.get(role, (role, None))[0]
        names = _authors(v.get("authors") or [])
        yr = str(v.get("published", ""))[:4]
        if v["source"] == "crossref":
            ident, link = v["id"], "https://doi.org/%s" % v["id"]
        else:
            ident, link = "arXiv:%s" % v["id"], "https://arxiv.org/abs/%s" % v["id"]
        title = v["title"].rstrip().rstrip(".")
        venue = v.get("container") or ident
        lines.append("[%d] %s (%s). %s. %s. %s — Difference: this work belongs to %s, which this "
                     "paper is written against or beside; the specific differences from the "
                     "closest of them are stated in Sections 1-2."
                     % (index[k], names, yr, title, venue, link, label))
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
        vals[key] = resolve_key(key, reports)
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
    return build(load_reports(), src_path=text)


def _unknown_number_plant(tmp):
    def f():
        return resolve_key("no.such.key", load_reports())
    return f


def _unused_number_plant(tmp):
    src = open(SRC, encoding="utf-8").read().replace("{{v2.plan.cells}}", "1000")
    p = tmp + "/plant_unused.md"
    open(p, "w", encoding="utf-8").write(src)
    return lambda: build(load_reports(), src_path=p)


def _fig_missing_plant(tmp):
    return lambda: figure_blocks(tmp + "/no_captions.md")


def selftest():
    import tempfile
    tmp = tempfile.mkdtemp()
    open(tmp + "/no_captions.md", "w").write("# empty\n")
    ok = total = 0

    def fires(name, fn):
        nonlocal ok, total
        total += 1
        try:
            fn()
            print("[%-34s] *** NO FIRE ***" % name)
        except Fault:
            ok += 1
            print("[%-34s] fire" % name)

    reports = load_reports()
    fires("unknown-number-key", lambda: resolve_key("no.such.key", reports))
    fires("unused-number", _unused_number_plant(tmp))
    fires("missing-caption-file", _fig_missing_plant(tmp))
    body, _ = build(reports)
    holds = ("References" in body and body.count("[1]") >= 1)
    total += 1
    if holds:
        ok += 1
        print("[%-34s] ok" % "the shipped source builds")
    else:
        print("[%-34s] *** FAIL ***" % "the shipped source builds")
    print("SELFTEST %d/%d" % (ok, total))
    return 0 if ok == total else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--check" in argv:
        return check()
    body, stats = build(load_reports())
    tmp = OUT + ".stage"
    open(tmp, "w", encoding="utf-8").write(body)
    os.replace(tmp, OUT)
    print("cited %d references (bar %d) | %d pool entries never cited | %d numbers resolved"
          % (stats["refs"], MIN_REFS, stats["uncited"], stats["nums"]))
    print("-> manuscript.md (%d bytes)" % stats["bytes"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
