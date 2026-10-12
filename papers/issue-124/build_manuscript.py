#!/usr/bin/env python3
"""Build manuscript.md for issue #124 from its source parts.

Nothing in the product is typed twice.  Two placeholder kinds are resolved here:

  {{key}}    a NUMBER, read out of the committed artefact that owns it (never typed in prose)
  {ref:ID}   a CITATION, resolved against the verified 245-entry pool (research/refs_pool.json)

The build FAILS on each way a number or a citation can be wrong:
  (1) a placeholder with no owner        -- the key is not in NUM / not in the pool
  (2) a value that nothing uses          -- a NUM key the source never references; a number that
                                            drifted out of the prose is how an artefact and a
                                            sentence silently stop agreeing
  (3) an unreadable artefact             -- a missing source file is a Fault, not a traceback
  (4) fewer than 100 cited references    -- the journal's citation bar is a gate, not a print

The reference layer is a claim about the BODY, so the build also reports how many pool entries are
never cited: a bibliography entry that no sentence uses cannot hide here.

Run:  python3 build_manuscript.py
      python3 build_manuscript.py --selftest      (plant a defect per check, require a fire)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = HERE   # the artefacts are committed BESIDE this script (self-contained package)
SRC = os.path.join(HERE, "manuscript.src.md")
SRC2 = os.path.join(HERE, "manuscript.part2.md")
OUT = os.path.join(HERE, "manuscript.md")
POOL = os.path.join(HERE, "refs", "pool.json")
DIFFS = os.path.join(HERE, "refs", "differences.json")
MIN_REFS = 100


def _authors(au):
    """The journal's house author form: `Family, I.`; `et al.` for four or more.

    The pool stores each author as the record's full name, so the family token is the last
    whitespace token and the initials are the first letters of the tokens before it.  A record
    whose author component is one token is printed as that token alone (the house rule's second
    admitted form).  Every family token in the cited set was checked to have an ASCII first letter
    and no lowercase particle, so this reading is exact for this pool and not a guess.
    """
    out = []
    for nm in (au[:3] if len(au) > 3 else au):
        parts = nm.split()
        if len(parts) == 1:
            out.append(parts[0] + ".")
        else:
            out.append("%s, %s" % (parts[-1], " ".join(p[0].upper() + "." for p in parts[:-1])))
    s = "; ".join(out)
    return s + "; et al." if len(au) > 3 else s


_DIFFS = None


def diff_of(key):
    """The one-line stated difference for a cited key, from refs/differences.json.

    A cited entry with no stated difference FAILS the build: the journal's presentation
    requirements close every entry with one, and a missing line must not render silently.
    """
    global _DIFFS
    if _DIFFS is None:
        _DIFFS = json.load(open(DIFFS))
    if key not in _DIFFS:
        raise Fault("cited reference %s carries no stated Difference" % key)
    return _DIFFS[key]

ARTEFACTS = {
    "v0": "spike_v0_results.json",
    "v1": "spike_v1_results.json",
    "v2": "spike_v2_results.json",
    "v3": "spike_v3_results.json",
    "v4": "spike_v4_results.json",
}


class Fault(Exception):
    pass


def load_artefacts():
    out = {}
    for tag, name in ARTEFACTS.items():
        p = os.path.join(RESEARCH, name)
        if not os.path.exists(p):
            raise Fault("the artefact %s is not readable -- %s" % (name, p))
        try:
            out[tag] = json.load(open(p))
        except ValueError as e:
            raise Fault("%s is not valid JSON (%s)" % (name, e))
    return out


def pick(obj, path):
    """Walk a JSON path; a missing step is a Fault naming the path, not a KeyError."""
    cur = obj
    for part in path.split("/"):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                raise Fault("path %s does not index the list (%d entries)" % (path, len(cur)))
        elif isinstance(cur, dict):
            if part not in cur:
                raise Fault("path %s: no key %r" % (path, part))
            cur = cur[part]
        else:
            raise Fault("path %s: cannot descend into %s" % (path, type(cur).__name__))
    return cur


def row(rows, key, val, field):
    for r in rows:
        if r[key] == val:
            return r[field]
    raise Fault("no row with %s=%r" % (key, val))


# ---------------------------------------------------------------- the owned numbers
# key -> (artefact tag, JSON path, format).  Every number the prose carries is declared here and read
# out of the artefact that owns it; the build refuses a key the source never uses (check 2).
NUM = {
    # --- spike_v0: the repeat-count law -------------------------------------------------------
    "v0.ab_max_abs_diff": ("v0", "certificates/route_A_vs_B_max_abs_diff", "%.3e"),
    "v0.ab_cells": ("v0", "certificates/route_cells", "%d"),
    "v0.mc_max_abs_z": ("v0", "certificates/mc_max_abs_z", "%.2f"),
    "v0.mc_cells": ("v0", "certificates/mc_cells", "%d"),
    "v0.mono_viol": ("v0", "LEN/mono", "%d"),
    "v0.rho0_identity": ("v0", "certificates/rho0_identity_max_abs_diff", "%.3e"),
    "v0.markov_mc_z": ("v0", "certificates/markov_mc_max_abs_z", "%.2f"),
    "v0.mc_trials": ("v0", "mc_trials", "%d"),
    "v0.ctl.n1_err": ("v0", "controls/n1_err", "%.3f"),
    "v0.ctl.p_half_N1000": ("v0", "controls/p_half_N1000", "%.4f"),
    "v0.ctl.p_half_N1000_unres": ("v0", "controls/p_half_N1000_unres", "%.4f"),
    "v0.ctl.p_half_N1001": ("v0", "controls/p_half_N1001", "%.4f"),
    # the error surface, strict majority at the folk p = 0.10
    "v0.maj.p010.n3": ("v0", "LAW/p=0.1/n=3/majority_strict", "%.5f"),
    "v0.maj.p010.n5": ("v0", "LAW/p=0.1/n=5/majority_strict", "%.5f"),
    "v0.maj.p010.n10": ("v0", "LAW/p=0.1/n=10/majority_strict", "%.6f"),
    "v0.maj.p002.n3": ("v0", "LAW/p=0.02/n=3/majority_strict", "%.3e"),
    # the other rules at the same (p, N)
    "v0.unanimity.p010.n3": ("v0", "LAW/p=0.1/n=3/unanimity", "%.4f"),
    "v0.unanimity.p010.n10": ("v0", "LAW/p=0.1/n=10/unanimity", "%.4f"),
    "v0.anyof.p010.n3": ("v0", "LAW/p=0.1/n=3/any_of", "%.4f"),
    "v0.anyof.p010.n10": ("v0", "LAW/p=0.1/n=10/any_of", "%.3e"),
    "v0.mean.p010.n1": ("v0", "LAW/p=0.1/n=1/mean_ds1", "%.4f"),
    "v0.mean.p010.n10": ("v0", "LAW/p=0.1/n=10/mean_ds1", "%.5f"),
    # even vs odd at equal budget
    "v0.eo.p010.n3": ("v0", "EO/p=0.1/n3", "%.4f"),
    "v0.eo.p010.n4": ("v0", "EO/p=0.1/n4", "%.5f"),
    "v0.eo.p010.n5": ("v0", "EO/p=0.1/n5", "%.5f"),
    # the divergence is a rate, not a count
    "v0.div.p049": ("v0", "DIV/p=0.49/divergence", "%.6f"),
    "v0.div.p049.n25": ("v0", "DIV/p=0.49/n_for_p_25pct", "%d"),
    "v0.div.p020": ("v0", "DIV/p=0.02/divergence", "%.6f"),
    "v0.div.p020.n25": ("v0", "DIV/p=0.02/n_for_p_25pct", "%d"),
    # the estimate-versus-decide crossover (P3)
    "v0.cross_p": ("v0", "cross_p", "%.2f"),
    "v0.req.p002.dec": ("v0", "REQ/p=0.02/n_decide_5pct", "%d"),
    "v0.req.p002.est": ("v0", "REQ/p=0.02/n_state_p_25pct", "%d"),
    "v0.req.p005.est": ("v0", "REQ/p=0.05/n_state_p_25pct", "%d"),
    "v0.req.p010.est": ("v0", "REQ/p=0.1/n_state_p_25pct", "%d"),
    # dependence (the registered boundary of P1)
    "v0.corr.rho0": ("v0", "CORR/p=0.05/rho=0.0/err_markov", "%.3e"),
    "v0.corr.rho010": ("v0", "CORR/p=0.05/rho=0.1/err_markov", "%.3e"),
    "v0.corr.rho080": ("v0", "CORR/p=0.05/rho=0.8/err_markov", "%.3e"),
    "v0.corr.ratio010": ("v0", "RATIO/p=0.05/rho=0.1", "%.1f"),
    "v0.corr.ratio080": ("v0", "RATIO/p=0.05/rho=0.8", "%.1f"),
    "v0.corr.neff010": ("v0", "CORR/p=0.05/rho=0.1/n_effective", "%.1f"),
    "v0.corr.neff080": ("v0", "CORR/p=0.05/rho=0.8/n_effective", "%.1f"),
    # --- spike_v1: the item-repeat budget boundary --------------------------------------------
    "v1.ab_worst_rel": ("v1", "certificates/route_A_vs_B_worst_rel", "%.1e"),
    "v1.ab_cells": ("v1", "certificates/route_A_vs_B_cells", "%d"),
    "v1.interior_cells": ("v1", "certificates/interiority_cells", "%d"),
    "v1.interior_viol": ("v1", "LEN/interior", "%d"),
    "v1.domain.interior_worst_rel": ("v1", "domain/worst_interior_rel", "%.4f"),
    "v1.domain.corner_worst_ratio": ("v1", "domain/worst_corner_ratio", "%.2f"),
    "v1.boundary_relax": ("v1", "certificates/relaxation_boundary_n_star", "%.3g"),
    "v1.boundary_discrete": ("v1", "certificates/discrete_boundary_n_star", "%.6f"),
    "v1.scalefree_move": ("v1", "certificates/nstar_b_independence_max_move", "%.1f"),
    "v1.pool.K": ("v1", "K_pool", "%d"),
    "v1.pool.cap_excess": ("v1", "POOLCAP/last/excess_over_floor", "%.2e"),
    "v1.ctl.tau2_zero_expect": ("v1", "controls/tau2_zero_expect", "%.3g"),
    "v1.ctl.sigma2_zero_expect": ("v1", "controls/sigma2_zero_expect", "%.3g"),
    # --- spike_v2: the measured inputs (the empirical arm) ------------------------------------
    "v2.r_runs": ("v2", "r_runs", "%d"),
    "v2.n_reps": ("v2", "n_reps", "%d"),
    "v2.n_test": ("v2", "n_test", "%d"),
    "v2.n_train": ("v2", "n_train", "%d"),
    "v2.k_info": ("v2", "k_info", "%d"),
    "v2.d": ("v2", "d", "%d"),
    "v2.p.u000": ("v2", "PMEAN/0.0", "%.4f"),
    "v2.p.u050": ("v2", "PMEAN/0.5", "%.4f"),
    "v2.p.u080": ("v2", "PMEAN/0.8", "%.4f"),
    "v2.p.u095": ("v2", "PMEAN/0.95", "%.4f"),
    "v2.p.u099": ("v2", "PMEAN/0.99", "%.4f"),
    "v2.p.spread": ("v2", "certificates/p_spread_over_cells", "%.0f"),
    "v2.p.events_u000": ("v2", "EVENTS/0.0", "%.1f"),
    "v2.sigma2": ("v2", "certificates/sigma2_measured", "%.6e"),
    "v2.tau2": ("v2", "certificates/tau2_measured", "%.6e"),
    "v2.nstar": ("v2", "certificates/n_star_measured", "%.3f"),
    "v2.crit2_frac": ("v2", "C2FRAC", "%.0f"),
    "v2.crit2_cells": ("v2", "certificates/criterion_ii_cells", "%d"),
    "v2.crit2_excl": ("v2", "certificates/criterion_ii_excluded", "%d"),
    "v2.decomp_worst_z": ("v2", "certificates/decomposition_worst_z", "%.2f"),
    "v2.p_within_worst_z": ("v2", "certificates/p_within_cell_max_z", "%.2f"),
    "v2.item_slope": ("v2", "certificates/item_axis_slope", "%.3f"),
    "v2.item.250.ratio": ("v2", "ITEM/n_test=250/cross_over_pop", "%.2f"),
    "v2.item.16000.ratio": ("v2", "ITEM/n_test=16000/cross_over_pop", "%.2f"),
    "v2.cross.reps": ("v2", "CROSSLEN", "%d"),
    "v2.cross.worst_z": ("v2", "certificates/crossing_worst_z", "%.2f"),
    "v2.cross.u_rep0": ("v2", "CROSS/rep=0/u_star", "%.3f"),
    "v2.cross.u_rep3": ("v2", "CROSS/rep=3/u_star", "%.3f"),
    "v2.cross.pop_se_rep0": ("v2", "CROSSPOPSE/rep=0", "%.1f"),
    "v2.cross.pop_se_rep3": ("v2", "CROSSPOPSE/rep=3", "%.1f"),
    "v2.ctl.n3_err_u000": ("v2", "controls/N3_err_u0", "%.5f"),
    "v2.ctl.n3_err_u099": ("v2", "controls/N3_err_u99", "%.3f"),
    "v2.cell.meas_u050": ("v2", "CELL/u=0.5/measured_delta", "%.5f"),
    "v2.cell.pred_u050": ("v2", "CELL/u=0.5/pred_delta", "%.5f"),
    "v2.cell.cross_u080": ("v2", "CELL/u=0.8/cross_over_pop", "%.2f"),
    # --- spike_v3: the item-SIZE axis and the three-knob budget -------------------------------
    "v3.tau_slope": ("v3", "certificates/tau_loglog_slope", "%.3f"),
    "v3.tau_chi2": ("v3", "certificates/tau_chi2", "%.2f"),
    "v3.tau_df": ("v3", "certificates/tau_chi2_df", "%d"),
    "v3.tau_chi2_crit": ("v3", "certificates/tau_chi2_crit99", "%.2f"),
    "v3.c_tau": ("v3", "certificates/tau_c_tau_weighted", "%.4f"),
    "v3.sigma_inf": ("v3", "certificates/sigma_inf", "%.6e"),
    "v3.c_sig": ("v3", "certificates/sigma_c_sig", "%.4f"),
    "v3.tau_at_125": ("v3", "AXIS/T=125/tau2", "%.6e"),
    "v3.tau_at_8000": ("v3", "AXIS/T=8000/tau2", "%.6e"),
    "v3.Tstar": ("v3", "controls/reference_T_star", "%.2f"),
    "v3.Tspan": ("v3", "TSPAN", "%d"),
    "v3.ctl.free_size": ("v3", "controls/T_star_free_size", "%.0f"),
    "v3.ctl.no_size_var": ("v3", "controls/T_star_no_size_variance", "%.1f"),
    "v3.holdout_rel_sigma2": ("v3", "certificates/holdout_rel_sigma2", "%.4f"),
    "v3.holdout_rel_tau2": ("v3", "certificates/holdout_rel_tau2", "%.3f"),
    # --- spike_v4: grounding on a public benchmark --------------------------------------------
    "v4.tau_slope": ("v4", "certificates/tau_loglog_slope", "%.3f"),
    "v4.tau_chi2": ("v4", "certificates/tau_chi2", "%.2f"),
    "v4.tau_df": ("v4", "certificates/tau_chi2_df", "%d"),
    "v4.sigma_inf": ("v4", "certificates/sigma_inf", "%.3f"),
    "v4.c_sig": ("v4", "certificates/sigma_c_sig", "%.1f"),
    "v4.Tstar": ("v4", "controls/reference_T_star", "%.2f"),
    "v4.n_star_in_budget": ("v4", "BUDGET/0/N_star", "%.3f"),
    "v4.data_sha": ("v4", "data_sha256", "%s"),
    "v4.k_items": ("v4", "k_items", "%d"),
    "v4.n_train": ("v4", "n_train", "%d"),
    "v4.r_runs": ("v4", "r_runs", "%d"),
    "v4.pop_gap": ("v4", "population_gap", "%.3f"),
    "v4.pop_gap_se": ("v4", "population_gap_se", "%.3f"),
    "v4.p.T16": ("v4", "AXIS/T=16/p_hat", "%.3f"),
    "v4.p.T128": ("v4", "AXIS/T=128/p_hat", "%.3f"),
    "v4.p.T4096": ("v4", "AXIS/T=4096/p_hat", "%.3f"),
    "v4.Tspan": ("v4", "TSPAN", "%d"),
    "v4.holdout_rel_sigma2": ("v4", "certificates/holdout_rel_sigma2", "%.4f"),
    "v4.holdout_rel_tau2": ("v4", "certificates/holdout_rel_tau2", "%.4f"),
}


def synth(tag, data):
    """The few derived/selected values the NUM table names by a synthetic path.

    Derived values are computed HERE from the artefact, never typed, so a change in the artefact
    moves them."""
    if tag == "v0":
        law, corr = {}, {}
        for r in data["law"]:
            law.setdefault("p=%s" % r["p"], {})["n=%s" % r["n"]] = r
        for r in data["correlated"]:
            corr.setdefault("p=%s" % r["p"], {})["rho=%s" % r["rho"]] = r
        ratio = {p: {rho: v["err_markov"] / max(v["err_iid"], 1e-30) for rho, v in byrho.items()}
                 for p, byrho in corr.items()}
        return {
            "LAW": law,
            "EO": {"p=%s" % r["p"]: r for r in data["even_odd"]},
            "DIV": {"p=%s" % r["p"]: r for r in data["divergence"]},
            "REQ": {"p=%s" % r["p"]: r for r in data["requirements"]},
            "CORR": corr,
            "RATIO": ratio,
            "LEN": {"mono": len(data["certificates"]["monotonicity_violations"])},
        }
    if tag == "v1":
        return {"POOLCAP": {"last": data["pool_cap"][-1]},
                "LEN": {"interior": len(data["certificates"]["interiority_violations"])}}
    if tag == "v2":
        cross = {"rep=%s" % c["rep"]: c for c in data["crossing"]}
        return {
            "PMEAN": data["certificates"]["p_mean_by_cell"],
            "EVENTS": {u: p * data["r_runs"] for u, p in data["certificates"]["p_mean_by_cell"].items()},
            "C2FRAC": 100.0 * data["certificates"]["criterion_ii_fraction"],
            "ITEM": {"n_test=%d" % r["n_test"]: r for r in data["item_axis"]},
            "CROSS": cross,
            "CROSSLEN": len(data["crossing"]),
            "CROSSPOPSE": {k: abs(v["delta_pop"]) / v["se"] for k, v in cross.items()},
            "CELL": {"u=%s" % c["u"]: c for c in data["cells"]},
        }
    if tag == "v3":
        return {"AXIS": {"T=%d" % r["T"]: r for r in data["axis"]},
                "TSPAN": data["t_grid"][-1] // data["t_grid"][0]}
    if tag == "v4":
        return {
            "AXIS": {"T=%d" % r["T"]: r for r in data["axis"]},
            "BUDGET": {str(i): b for i, b in enumerate(data["budget"])},
            "TSPAN": data["t_grid"][-1] // data["t_grid"][0],
        }
    return {}


def walk(table, key, parts):
    """Walk the synthetic tables: each path segment names the next dict key (a missing key is a
    Fault that names the key, not a KeyError)."""
    node = table
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            raise Fault("{{%s}}: no entry %r in the synthetic table" % (key, part))
        node = node[part]
    return node


def resolve(key, arts, synth_map):
    tag, path, spec = NUM[key]
    parts = path.split("/")
    if parts[0] in synth_map[tag]:
        val = walk(synth_map[tag], key, parts)
    else:
        val = pick(arts[tag], path)
    return spec % val


def build(arts, texts, synth_map):
    text = "\n\n".join(t.rstrip("\n") for t in texts) + "\n"

    pool = json.load(open(POOL))
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
        au = v.get("authors") or []
        names = _authors(au)
        yr = str(v.get("published", ""))[:4]
        if v["source"] == "crossref":
            ident, link = v["id"], "https://doi.org/%s" % v["id"]
        else:
            ident, link = "arXiv:%s" % v["id"], "https://arxiv.org/abs/%s" % v["id"]
        title = v["title"].rstrip().rstrip(".")   # some stored titles carry their own full stop
        lines.append("[%d] %s (%s). *%s*. %s. %s — Difference: %s"
                     % (index[k], names, yr, title, ident, link, diff_of(k)))
        # A blank line between entries, as the journal's published manuscripts do: without it the
        # whole bibliography is ONE paragraph to a CommonMark renderer (GitHub's preview included),
        # so the list a reader sees is a wall rather than a list -- and a per-entry read (the
        # author-form check in .github/tools/refgate.py) collapses to the first line.
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    lines.append("")
    body = body + "\n" + "\n".join(lines)

    if len(order) < MIN_REFS:
        raise Fault("only %d references are cited; the journal bar is %d" % (len(order), MIN_REFS))

    used = set()
    for m in re.finditer(r"\{\{([^}]+)\}\}", body):
        key = m.group(1).strip()
        used.add(key)
        if key not in NUM:
            raise Fault("the placeholder {{%s}} has no owner in NUM" % key)
    vals = {k: resolve(k, arts, synth_map) for k in used}
    body = re.sub(r"\{\{([^}]+)\}\}", lambda m: vals[m.group(1).strip()], body)

    unused = sorted(set(NUM) - used)
    if unused:
        raise Fault("NUM carries %d value(s) nothing uses: %s" % (len(unused), ", ".join(unused)))
    left = sorted(set(re.findall(r"\{\{|\}\}|\{ref:[^}]*\}", body)))
    if left:
        raise Fault("unresolved placeholder(s) survived the build: %s" % left[:5])

    return body, {"refs": len(order), "uncited": len(pool) - len(order), "nums": len(used)}


def main():
    arts = load_artefacts()
    synth_map = {t: synth(t, arts[t]) for t in arts}
    texts = []
    for p in (SRC, SRC2):
        if not os.path.exists(p):
            raise Fault("the source part %s is not readable" % p)
        texts.append(open(p).read())
    body, r = build(arts, texts, synth_map)
    open(OUT, "w").write(body)
    words = len(re.findall(r"\S+", re.sub(r"<[^>]+>", " ", body)))
    print("wrote %s" % os.path.relpath(OUT, HERE))
    print("  cited references: %d (bar %d) | verified pool entries never cited: %d"
          % (r["refs"], MIN_REFS, r["uncited"]))
    print("  owned numbers resolved: %d | words: %d" % (r["nums"], words))
    return 0


def selftest():
    """Plant a defect per check and require it to FIRE; require the healthy case to HOLD."""
    ok = True
    arts = load_artefacts()
    synth_map = {t: synth(t, arts[t]) for t in arts}
    src = open(SRC).read()
    src2 = open(SRC2).read()

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except (Fault, SystemExit) as e:
            print("[%-30s] FIRED: %s" % (name, str(e)[:52]))
            return
        print("[%-30s] *** DID NOT FIRE ***" % name)
        ok = False

    def holds(name, fn):
        nonlocal ok
        try:
            fn()
            print("[%-30s] holds (no fire)" % name)
        except (Fault, SystemExit) as e:
            print("[%-30s] *** FIRED ON A HEALTHY CASE *** %s" % (name, str(e)[:40]))
            ok = False

    good = lambda t1=src, t2=src2: build(arts, [t1, t2], synth_map)

    # (1) an unowned placeholder, an unknown citation key, a value nothing uses
    fires("number-with-no-owner",
          lambda: build(arts, [src + "\nA stray {{v9.not.a.key}} here.\n", src2], synth_map))
    fires("citation-not-in-pool",
          lambda: build(arts, [src + "\nSee {ref:9999.99999}.\n", src2], synth_map))
    # the owned value must be unused in EVERY source part to be caught: `v0.cross_p` appears in both
    # (its prose in part 1, its registration outcome in part 2), so the plant strips both.
    fires("value-nothing-uses",
          lambda: build(arts, [src.replace("{{v0.cross_p}}", "0.40"),
                               src2.replace("{{v0.cross_p}}", "0.40")], synth_map))

    # (2) a citation-count bar that is a gate: strip the parts down under 100 cited keys
    short = re.sub(r"\{ref:[^}]+\}", "", src)
    short2 = re.sub(r"\{ref:[^}]+\}", "", src2)
    fires("citation-bar", lambda: build(arts, [short, short2], synth_map))

    # (3) an unreadable artefact is a Fault, not a traceback
    def missing():
        global RESEARCH
        keep = RESEARCH
        try:
            RESEARCH = os.path.join(HERE, "research-does-not-exist")
            load_artefacts()
        finally:
            RESEARCH = keep
    fires("unreadable-artefact", missing)

    # (4) a wrong JSON path is a Fault that names the path
    fires("bad-json-path", lambda: pick(arts["v0"], "certificates/no_such_field"))

    # healthy
    holds("healthy-build", good)

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(selftest() if "--selftest" in sys.argv else main())
    except Fault as e:
        print("Fault: %s" % e)
        sys.exit(2)
