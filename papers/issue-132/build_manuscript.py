#!/usr/bin/env python3
"""Build manuscript.md for issue #132 from its source, resolving every number and every citation.

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
            elif part == "$span":
                cur = cur[-1] // cur[0]
            elif part.lstrip("-").isdigit():
                cur = cur[int(part)]
            else:
                raise Fault("path %s: a list takes an index or $len, not %r" % (path, part))
        elif isinstance(cur, dict):
            if part not in cur:
                # a computed selector may key by NUMBER (e.g. `phi -> cell`); a path can only
                # carry a string, so try the numeric reading of it before failing.
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


def _range(rep, key, field):
    vals = [c[field] for c in rep[key]]
    return (min(vals), max(vals))


# NOTE: the first parameter is `rep`, not `r` -- the caller passes `r=<residue threshold>` as a
# cell field, and a parameter named `r` collides with it ("multiple values for argument 'r'").
V1L = lambda rep, **w: _cell1(rep["v1"], "ladder", **w)
V2C = lambda rep, **w: _cell1(rep["v2"], "cells", **w)

COMPUTED = {
    # --- v0: the de-risk spike -------------------------------------------------------------
    "v0_cor_not_pool_lo": lambda r: _range(r["v0"], "containment", "cor_not_pool")[0],
    "v0_cor_not_pool_hi": lambda r: _range(r["v0"], "containment", "cor_not_pool")[1],
    "v0_pool_not_cor_lo": lambda r: _range(r["v0"], "containment", "pool_not_cor")[0],
    "v0_pool_not_cor_hi": lambda r: _range(r["v0"], "containment", "pool_not_cor")[1],
    "v0_sweep": lambda r: [round(x["hidden_fraction_of_F_pool"] * 100, 1)
                           for x in r["v0"]["share_sweep_word3_theta_0.01"]],
    "v0_char_sweep": lambda r: [round(x["hidden_fraction_of_F_pool"] * 100, 1)
                                for x in r["v0"]["share_sweep_char_bigram_theta_0.01"]],
    # --- v1: the frame-level ladder --------------------------------------------------------
    "v1_n_docs": lambda r: sum(r["v1"]["corpus"]["n_docs_by_lang"].values()),
    "v1_it_share": lambda r: _cell1(r["v1"], "strata", name="minority_it")["share"],
    "v1_en_share": lambda r: _cell1(r["v1"], "strata", name="majority_en")["share"],
    "v1_it_n_pool": lambda r: _cell1(r["v1"], "strata", name="minority_it")["n_pool"],
    "v1_en_n_pool": lambda r: _cell1(r["v1"], "strata", name="majority_en")["n_pool"],
    "v1_lad_it_lo": lambda r: V1L(r, stat="word3", stratum="minority_it", theta=0.05, tau=0.5, phi=0.2),
    "v1_lad_it_0505": lambda r: V1L(r, stat="word3", stratum="minority_it", theta=0.05, tau=0.5, phi=0.05),
    "v1_lad_it_hi": lambda r: V1L(r, stat="word3", stratum="minority_it", theta=0.05, tau=0.5, phi=0.3),
    "v1_lad_it_full": lambda r: V1L(r, stat="word3", stratum="minority_it", theta=0.05, tau=0.5, phi=1.0),
    "v1_lad_en": lambda r: V1L(r, stat="word3", stratum="majority_en", theta=0.05, tau=0.5, phi=0.2),
    "v1_cs_w3_agree": lambda r: sum(1 for c in r["v1"]["critical_share"] if c["stat"] == "word3"
                                    and c["predicted_hidden_from_corpus"] == c["observed_hidden_from_corpus"]),
    "v1_cs_w3_total": lambda r: sum(1 for c in r["v1"]["critical_share"] if c["stat"] == "word3"),
    "v1_cs_c2_hidden": lambda r: sum(1 for c in r["v1"]["critical_share"] if c["stat"] == "char2"
                                     and c["observed_hidden_from_corpus"]),
    "v1_cs_c2_total": lambda r: sum(1 for c in r["v1"]["critical_share"] if c["stat"] == "char2"),
    "v1_phi_it": lambda r: 0.05 / V1L(r, stat="word3", stratum="minority_it", theta=0.05,
                                      tau=0.5, phi=0.2)["share"],
    "v1_phi_en": lambda r: 0.05 / V1L(r, stat="word3", stratum="majority_en", theta=0.05,
                                      tau=0.5, phi=0.2)["share"],
    # --- v2: the grid, the residue boundary, the eligible subset ---------------------------
    "v2_r_lo": lambda r: V2C(r, stat="word3", stratum="minority_it", theta=0.05, tau=0.5,
                             phi=0.2, r=5, sample="affected"),
    "v2_r_last": lambda r: V2C(r, stat="word3", stratum="minority_it", theta=0.05, tau=0.5,
                               phi=0.2, r=27, sample="affected"),
    "v2_r_over": lambda r: V2C(r, stat="word3", stratum="minority_it", theta=0.05, tau=0.5,
                               phi=0.2, r=40, sample="affected"),
    "v2_elig": lambda r: {p: V2C(r, stat="word3", stratum="minority_it", theta=0.05, tau=0.5,
                                 phi=p, r=10, sample="affected") for p in (0.05, 0.2, 0.3, 1.0)},
    "v2_comm": lambda r: V2C(r, stat="word3", stratum="minority_it", theta=0.05, tau=0.5,
                             phi=0.2, r=10, sample="community"),
    "v2_r_exceeds_cells": lambda r: sum(1 for c in r["v2"]["cells"] if c["r_exceeds_register"]),
    # --- v3: the null is also a level ------------------------------------------------------
    "v3_infl": lambda r: {k: r["v3"]["L1_filter_chain"]["min_degen_sweep"][k]
                             ["inflation_one_sided_over_matched"] for k in ("10", "25", "50", "100")},
}

# name -> (report tag, path-or-computed-name, format spec)
NUM = {
    "v0.cells": ("v0", "containment_summary/cells", "%d"),
    "v0.viol.both": ("v0", "containment_summary/cells_where_F_corpus_NOT_subset_F_pool", "%d"),
    "v0.viol.lo": ("v0", "v0_cor_not_pool_lo", "%d"),
    "v0.viol.hi": ("v0", "v0_cor_not_pool_hi", "%d"),
    "v0.viol.p.lo": ("v0", "v0_pool_not_cor_lo", "%d"),
    "v0.viol.p.hi": ("v0", "v0_pool_not_cor_hi", "%d"),
    "v0.docs": ("v0", "corpus/n_docs", "%d"),
    "v0.dil.char.pairs": ("v0", "dilution/char_bigram_theta_0.01/n_confined_pairs", "%d"),
    "v0.dil.char.worst": ("v0", "dilution/char_bigram_theta_0.01/worst_abs_violation", "%.1e"),
    "v0.dil.char.hidden": ("v0", "dilution/char_bigram_theta_0.01/n_pool_generic_but_corpus_invisible", "%d"),
    "v0.dil.w3.pairs": ("v0", "dilution/word3_theta_0.01/n_confined_pairs", "%d"),
    "v0.dil.w3.worst": ("v0", "dilution/word3_theta_0.01/worst_abs_violation", "%.1e"),
    "v0.dil.w3.hidden": ("v0", "dilution/word3_theta_0.01/n_pool_generic_but_corpus_invisible", "%d"),
    "v0.unit": ("v0", "dilution/word3_theta_0.01/worst_where/unit", "%s"),
    "v0.sweep.1": ("v0", "v0_sweep/0", "%.1f"),
    "v0.sweep.2": ("v0", "v0_sweep/1", "%.1f"),
    "v0.sweep.4": ("v0", "v0_sweep/2", "%.1f"),
    "v0.sweep.8": ("v0", "v0_sweep/3", "%.1f"),
    "v0.char.sweep.1": ("v0", "v0_char_sweep/0", "%.1f"),
    "v0.char.sweep.2": ("v0", "v0_char_sweep/1", "%.1f"),
    "v0.char.sweep.4": ("v0", "v0_char_sweep/2", "%.1f"),
    "v0.char.sweep.8": ("v0", "v0_char_sweep/3", "%.1f"),
    "v0.Fpool.1": ("v0", "share_sweep_word3_theta_0.01/0/|F_pool|", "%d"),
    "v0.hidden.1": ("v0", "share_sweep_word3_theta_0.01/0/hidden", "%d"),
    "v0.share.1": ("v0", "share_sweep_word3_theta_0.01/0/share", "%.3f"),

    "v1.docs": ("v1", "v1_n_docs", "%d"),
    "v1.it.share": ("v1", "v1_it_share", "%.3f"),
    "v1.en.share": ("v1", "v1_en_share", "%.3f"),
    "v1.it.pool": ("v1", "v1_it_n_pool", "%d"),
    "v1.en.pool": ("v1", "v1_en_n_pool", "%d"),
    "v1.lad.lo.corpus": ("v1", "v1_lad_it_lo/fire_corpus", "%d"),
    "v1.lad.lo.pool": ("v1", "v1_lad_it_lo/fire_pool", "%d"),
    "v1.lad.lo.induced": ("v1", "v1_lad_it_lo/level_induced", "%d"),
    "v1.lad.lo.reg": ("v1", "v1_lad_it_lo/register_units", "%d"),
    "v1.lad.lo.cprev": ("v1", "v1_lad_it_lo/corpus_prevalence", "%.3f"),
    "v1.lad.05.corpus": ("v1", "v1_lad_it_0505/fire_corpus", "%d"),
    "v1.lad.05.pass": ("v1", "v1_lad_it_0505/sim_gate_pass", "%d"),
    "v1.lad.hi.corpus": ("v1", "v1_lad_it_hi/fire_corpus", "%d"),
    "v1.lad.full.corpus": ("v1", "v1_lad_it_full/fire_corpus", "%d"),
    "v1.lad.en.corpus": ("v1", "v1_lad_en/fire_corpus", "%d"),
    "v1.lad.en.cprev": ("v1", "v1_lad_en/corpus_prevalence", "%.3f"),
    "v1.cells": ("v1", "ladder/$len", "%d"),
    "v1.cs.w3.agree": ("v1", "v1_cs_w3_agree", "%d"),
    "v1.cs.w3.total": ("v1", "v1_cs_w3_total", "%d"),
    "v1.cs.c2.hidden": ("v1", "v1_cs_c2_hidden", "%d"),
    "v1.cs.c2.total": ("v1", "v1_cs_c2_total", "%d"),
    "v1.phi.it": ("v1", "v1_phi_it", "%.3f"),
    "v1.phi.en": ("v1", "v1_phi_en", "%.3f"),
    "v1.tmpl.cells": ("v1", "templates/$len", "%d"),
    "v1.tmpl.dice": ("v1", "templates/0/dice_edit1pct", "%.3f"),

    "v2.cells": ("v2", "cells/$len", "%d"),
    "v2.r.lo.induced": ("v2", "v2_r_lo/level_induced", "%d"),
    "v2.r.last.induced": ("v2", "v2_r_last/level_induced", "%d"),
    "v2.r.over.induced": ("v2", "v2_r_over/level_induced", "%d"),
    "v2.r.over.corpusmax": ("v2", "v2_r_over/max_residue_corpus", "%d"),
    "v2.r.over.poolmax": ("v2", "v2_r_over/max_residue_pool", "%d"),
    "v2.r.over.pass": ("v2", "v2_r_over/sim_gate_pass", "%d"),
    "v2.r.reg": ("v2", "v2_r_last/register_units", "%d"),
    "v2.elig.20": ("v2", "v2_elig/0.2/eligible_rate", "%.3f"),
    "v2.elig.30": ("v2", "v2_elig/0.3/eligible_rate", "%.3f"),
    "v2.elig.30.fire": ("v2", "v2_elig/0.3/fire_corpus", "%d"),
    "v2.elig.30.pass": ("v2", "v2_elig/0.3/sim_gate_pass", "%d"),
    "v2.elig.100.fire": ("v2", "v2_elig/1.0/fire_corpus", "%d"),
    "v2.elig.100.pass": ("v2", "v2_elig/1.0/sim_gate_pass", "%d"),
    "v2.elig.20.fire": ("v2", "v2_elig/0.2/fire_corpus", "%d"),
    "v2.elig.20.pass": ("v2", "v2_elig/0.2/sim_gate_pass", "%d"),
    "v2.elig.05.fire": ("v2", "v2_elig/0.05/fire_corpus", "%d"),
    "v2.elig.05.pass": ("v2", "v2_elig/0.05/sim_gate_pass", "%d"),
    "v2.comm.fire": ("v2", "v2_comm/fire_corpus", "%d"),
    "v2.comm.pass": ("v2", "v2_comm/sim_gate_pass", "%d"),
    "v2.comm.dil": ("v2", "v2_comm/dilution", "%.3f"),
    "v2.comm.n": ("v2", "v2_comm/n_pairs", "%d"),
    "v2.r.exceeds": ("v2", "v2_r_exceeds_cells", "%d"),

    "v3.docs": ("v3", "corpus/n_docs", "%d"),
    "v3.verbatim": ("v3", "corpus/n_verbatim_reposts", "%d"),
    "v3.edited": ("v3", "corpus/n_edited_reposts", "%d"),
    "v3.editrate": ("v3", "corpus/edit_rate", "%.2f"),
    "v3.E": ("v3", "L1_filter_chain/E_naive_filters_neither_side", "%d"),
    "v3.Em": ("v3", "L1_filter_chain/E_matched_filter_on_both", "%.2f"),
    "v3.ident": ("v3", "L1_filter_chain/identity_E_matched_over_E_naive", "%.4f"),
    "v3.pnull": ("v3", "L1_filter_chain/p_null_stage1", "%.4f"),
    "v3.obs.E": ("v3", "L1_filter_chain/observed_over_E_matched", "%.4f"),
    "v3.infl.10": ("v3", "v3_infl/10", "%.2f"),
    "v3.infl.25": ("v3", "v3_infl/25", "%.2f"),
    "v3.infl.50": ("v3", "v3_infl/50", "%.2f"),
    "v3.infl.100": ("v3", "v3_infl/100", "%.2f"),
    "v3.fires": ("v3", "L2_interval_ownership/n_fires", "%d"),
    "v3.nonid": ("v3", "L2_interval_ownership/n_non_identical", "%d"),
    "v3.verb.fires": ("v3", "L2_interval_ownership/n_verbatim", "%d"),
    "v3.int.nonid.lo": ("v3", "L2_interval_ownership/interval_over_NON_IDENTICAL/lo", "%.3f"),
    "v3.int.nonid.hi": ("v3", "L2_interval_ownership/interval_over_NON_IDENTICAL/hi", "%.3f"),
    "v3.int.nonid.med": ("v3", "L2_interval_ownership/interval_over_NON_IDENTICAL/median", "%.3f"),
    "v3.pois.1": ("v3", "L2_interval_ownership/poisson_upper_95_one_sided_for_the_small_count/upper", "%.1f"),
    "v3.pois.2": ("v3", "L2_interval_ownership/poisson_upper_95_two_sided_for_the_small_count/upper", "%.1f"),
    "v3.ctl.anchor": ("v3", "L3_joint_profile/constructions/control/anchor/cell", "%.3f"),
    "v3.ctl.exch": ("v3", "L3_joint_profile/constructions/control/exchangeable/cell", "%.3f"),
    "v3.ctl.marg": ("v3", "L3_joint_profile/constructions/control/marginal/cell", "%.3f"),
    "v3.ctl.n": ("v3", "L3_joint_profile/n_control_pairs", "%d"),
    "v3.nd.exch": ("v3", "L3_joint_profile/constructions/neardup/exchangeable/cell", "%.3f"),
    "v3.nd.anchor": ("v3", "L3_joint_profile/constructions/neardup/anchor/cell", "%.3f"),
    "v3.nd.n": ("v3", "L3_joint_profile/n_neardup_pairs", "%d"),

    "sim.tau": ("v1", "params/taus/1", "%g"),
    "sim.theta": ("v1", "params/thetas/1", "%g"),
    "sim.r": ("v1", "params/r", "%d"),
    "sim.seed": ("v3", "params/seed", "%d"),
    "sim.k": ("v3", "params/k_side", "%d"),
    "sim.pairs": ("v3", "params/n_pairs", "%d"),
    "sim.mindegen": ("v3", "params/min_degen", "%d"),
}


def resolve(key, reports):
    if key not in NUM:
        raise Fault("the placeholder {{%s}} has no owner in NUM" % key)
    tag, path, spec = NUM[key]
    if path.startswith("@"):
        path = path[1:]
    head, _, rest = path.partition("/")
    if head in COMPUTED:
        # a computed selector, optionally followed by a path INTO its result
        val = COMPUTED[head](reports)
        if rest:
            val = pick(val, rest)
    else:
        val = pick(reports[tag], path)
    try:
        return spec % val
    except (TypeError, KeyError) as e:
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
    """The five figure blocks, keyed fig1..fig5, assembled from the generated CAPTIONS.md.

    CAPTIONS.md is generated by make_figures.py from the same reports the SVGs are drawn from, so a
    caption cannot drift from its picture.  It carries one section per figure:

        ## `fig1_dilution_law.svg`

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
        # the caption's own first sentence is the figure's title
        head, _, rest = text.partition(". ")
        title = head.rstrip(".") if rest else text
        body = rest if rest else ""
        if not os.path.isfile(os.path.join(HERE, "figures", name)):
            raise Fault("the caption file names %s but figures/ does not carry it" % name)
        blocks["fig%s" % num] = "![%s](figures/%s)\n\n**Figure %s. %s.** %s" % (
            name, name, num, title, body)
    missing = [k for k in ("fig1", "fig2", "fig3", "fig4", "fig5") if k not in blocks]
    if missing:
        raise Fault("the generated caption file carries no block for %s" % ", ".join(missing))
    return blocks


def build(reports, src_path=SRC):
    text = open(src_path, encoding="utf-8").read().rstrip("\n") + "\n"
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
    fires("cited-with-no-difference",
          lambda: build_with(src.replace("{ref:0909.4385}", "", 1)
                             .replace("0909.4385", "0909.4385", 1)
                             + "\n{ref:" + _a_key_without_difference() + "}\n"))
    fires("unused-number", _unused_number_plant)
    fires("figure-file-missing", _fig_missing_plant)
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def _unused_number_plant():
    """Declare a number the source never references; the build must refuse to render."""
    NUM["zz.unused.plant"] = ("v0", "corpus/n_docs", "%d")
    try:
        build(load_reports())
    finally:
        del NUM["zz.unused.plant"]


def _a_key_without_difference():
    pool = json.load(open(POOL, encoding="utf-8"))
    diffs = json.load(open(DIFFS, encoding="utf-8"))
    for k in sorted(pool):
        if k not in diffs:
            return k
    raise Fault("every pool entry carries a difference -- the plant has nothing to plant")


def _fig_missing_plant():
    """Point a caption at a figure file that is not there; the build must refuse.

    The plant is written OUTSIDE the package (the package's rule is that its run writes nothing
    beside itself) and removed in a `finally` -- the first draft wrote `<CAPTIONS>.plant` and left it
    behind, which the export check caught as an untracked file in the tree.
    """
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".md")
    try:
        text = open(CAPTIONS, encoding="utf-8").read().replace("fig1_dilution_law.svg",
                                                               "fig1_no_such_file.svg")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        figure_blocks(captions_path=tmp)
    finally:
        os.unlink(tmp)


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
