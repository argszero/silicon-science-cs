#!/usr/bin/env python3
"""Issue #122 -- build manuscript.md from manuscript.src.md.

Every number in the manuscript is a PLACEHOLDER `{{name}}` or `{{name:format}}` resolved here from
the instruments' committed artefacts.  Nothing is typed into the prose: a number typed into a
sentence is a claim with no owner, and it goes stale the moment an artefact changes (`#120` shipped
three such numbers before a validation suite found them).

The build FAILS on:
  * a placeholder that no value owns            (a claim with no artefact behind it)
  * an unresolved placeholder in the output     (the substitution silently missing a case)
  * a VALUE THAT NOTHING USES                   (dead scaffolding, or a value that drifted out of
                                                 the prose without anyone noticing)

It also writes `values.json`: every name, its rendered text, the artefact it came from, and the
tool that produced it -- so a reader can trace a printed number back to the file that owns it.

Usage:  /usr/bin/python3 build_manuscript.py
Out:    manuscript.md   (the assembled paper)
        values.json     (name -> value -> artefact provenance)
"""
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "manuscript.src.md")
OUT = os.path.join(HERE, "manuscript.md")
VALS = os.path.join(HERE, "values.json")

PLACEHOLDER = re.compile(r"\{\{([A-Za-z0-9_]+)(?::([^{}]+))?\}\}")
# A SECOND, WIDER pattern, used only to REFUSE: `{{...}}` is what a placeholder looks like to a
# reader, and the substitution pattern above is narrower than that shape (its name alphabet excludes
# `/`, `(`, `-`, ...).  A token outside the alphabet was therefore neither substituted nor reported
# by the leftover check -- it simply appeared in the built manuscript.  Anything that LOOKS like a
# placeholder must resolve, so the check is a superset of the substitution, not a copy of it.
LOOSE = re.compile(r"\{\{([^{}]*)\}\}")


def load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)


def mean_of(x):
    return x["mean"] if isinstance(x, dict) else x


def build_values():
    """name -> (value, artefact, how it was obtained).

    Only the numbers the prose CITES are exposed.  A value that is built but never used is dead
    scaffolding, and `main` treats it as an error -- so this list stays as short as the paper.
    """
    v1, v2, v3 = load("spike_v1_results.json"), load("spike_v2_results.json"), load("spike_v3_results.json")
    man = load("figures/manifest.json")
    meta = load("refs/meta.json")
    cur = load("refs/curated.json")["entries"]
    V = {}

    def put(name, val, art, how):
        if name in V:
            sys.exit("duplicate value name: %s" % name)
        V[name] = (val, art, how)

    def cell(v, src, n, lam):
        return [x for x in v["cells"] if x["source"] == src and x["n"] == n and x["lam"] == lam][0]

    def fp(v, src, n, lam):
        return [r for r in v["first_passage"] if r["source"] == src and r["n"] == n and r["lam"] == lam][0]

    def p1(v, src, n, lam):
        return [r for r in v["part1"] if r["source"] == src and r["n"] == n and r["lam"] == lam][0]

    def bnd(v, src, n, w):
        return [r for r in v["part2"] if r["source"] == src and r["n"] == n][0]["boundary"][str(w)]

    def bndratio(v, src, n):
        return [r for r in v["part2"] if r["source"] == src and r["n"] == n][0]["ratio_w64_over_w1"]

    def rate(v, w, lam, mode):
        r = [x for x in v["part3"] if x["w"] == w and x["lam"] == lam][0]
        return r["rate_measured"] if mode == "m" else r["rate_ma_eig"]

    def crit(v, src, w, key):
        c = [x for x in v["controls"] if x["kind"] == "criterion_dependence"
             and x["source"] == src and x["w"] == w][0]
        return {"stat": c["lambda_stationary"], "heal": c["lambda_heal"],
                "ratio": c["ratio_stationary_over_heal"]}[key]

    # ---- the loop -----------------------------------------------------------------------------
    put("K", v1["K"], "spike_v1_results.json", "K")
    put("seed0", v1["seed0"], "spike_v1_results.json", "seed0")
    put("n_cells", len(v1["cells"]), "spike_v1_results.json", "len(cells)")
    put("n_reps_hyst", fp(v1, "uniform", 50, 0.005)["n_obs_loss"], "spike_v1_results.json",
        "first_passage(uniform,n=50,lam=0.005).n_obs_loss (replicates per cell)")
    put("gap_pairs", v1["n_gap_pairs"], "spike_v1_results.json", "n_gap_pairs")
    put("gap_median", v1["cf_over_meas_median"], "spike_v1_results.json", "cf_over_meas_median")
    put("gap_min", v1["cf_over_meas_min"], "spike_v1_results.json", "cf_over_meas_min")
    put("gap_median_recip", 1.0 / v1["cf_over_meas_median"], "spike_v1_results.json",
        "1 / cf_over_meas_median (how many times the measured rate exceeds the bound)")
    put("gap_max", v1["cf_over_meas_max"], "spike_v1_results.json", "cf_over_meas_max")
    put("gap_above1", v1["n_gap_above1"], "spike_v1_results.json", "n_gap_above1")
    put("gap_below1", v1["n_gap_below1"], "spike_v1_results.json", "n_gap_below1")
    # the same readings, binned by the absence fraction of the symbol that produced them: the
    # variable that decides which side of the bound a conditional reading lands on.
    for b in v1["gap_by_absence"]:
        tag = "lo%dhi%d" % (round(100 * b["lo"]), round(100 * b["hi"]))
        put("gapab_%s_n" % tag, b["n"], "spike_v1_results.json", "gap_by_absence(%s).n" % tag)
        put("gapab_%s_above1" % tag, b["n_above1"], "spike_v1_results.json",
            "gap_by_absence(%s).n_above1" % tag)
        put("gapab_%s_med" % tag, b["median_ratio"], "spike_v1_results.json",
            "gap_by_absence(%s).median_ratio" % tag)
    put("route_rel", v1["rel_A_vs_B_max_wellcounted"], "spike_v1_results.json",
        "rel_A_vs_B_max_wellcounted")
    for n in (25, 200):
        c = cell(v1, "uniform", n, 0.01)
        i = c["worst_symbol"]
        put("lossA_u_n%d" % n, c["loss_A"][i], "spike_v1_results.json",
            "cell(uniform,n=%d,lam=0.01).loss_A[worst_symbol]" % n)
        put("losscf_u_n%d" % n, c["loss_cf"][i], "spike_v1_results.json",
            "cell(uniform,n=%d,lam=0.01).loss_cf[worst_symbol]" % n)
    for src, lam in (("uniform", 0.005), ("uniform", 0.01), ("twohot", 0.02), ("twohot", 0.005)):
        r = fp(v1, src, 50, lam)
        tag = "%s_lam%s" % (src, str(lam).replace(".", ""))
        for key, fld in (("tloss", "T_loss"), ("trecov", "T_recov"), ("hiratio", "ratio_recov_over_loss"),
                         ("censrecov", "cens_recov")):
            val = r[fld]
            # A field that is NaN in the artefact is NOT exposed as a value: it is undefined, and the
            # prose says so in words (with the censoring fraction, which IS defined).  Exposing it
            # would print "nan" in a results table and call it a measurement.
            if isinstance(val, float) and val != val:
                continue
            put("%s_%s" % (key, tag), val, "spike_v1_results.json",
                "first_passage(%s,n=50,lam=%s).%s" % (src, lam, fld))
    for k in ("uniform/n50", "uniform/n200", "twohot/n50", "twohot/n200"):
        c = v1["crossing"][k]
        tag = k.replace("/", "_")
        put("cross_lo_%s" % tag, c["lam_lo"], "spike_v1_results.json", "crossing[%s].lam_lo" % k)
        put("cross_hi_%s" % tag, c["lam_hi"], "spike_v1_results.json", "crossing[%s].lam_hi" % k)
    put("ctrl_lam0_abs", v1["controls"]["lam0"]["abs_overall"], "spike_v1_results.json",
        "controls.lam0.abs_overall")
    put("ctrl_lam0_exact", v1["controls"]["lam0"]["exact"], "spike_v1_results.json", "controls.lam0.exact")
    put("ctrl_lam1_rel", max(v1["controls"][k]["rel"] for k in ("lam1_uniform", "lam1_twohot", "lam1_zipf")),
        "spike_v1_results.json", "max over controls.lam1_*.rel")

    # ---- the protocol ------------------------------------------------------------------------
    put("v2_c1_maxdiff", v2["controls"]["C1_w1_is_replacement"]["max_abs_diff_vs_spike_v1"],
        "spike_v2_results.json", "controls.C1_w1_is_replacement.max_abs_diff_vs_spike_v1")
    for src in ("uniform", "zipf"):
        for n in (50, 200):
            for w in (1, 4, 64):
                put("bnd_%s_n%d_w%d" % (src, n, w), bnd(v2, src, n, w), "spike_v2_results.json",
                    "part2(source=%s,n=%d).boundary[%d]" % (src, n, w))
            put("bndratio_%s_n%d" % (src, n), bndratio(v2, src, n), "spike_v2_results.json",
                "part2(source=%s,n=%d).ratio_w64_over_w1" % (src, n))
    for w in (1, 64):
        for lam in (0.02, 0.05):
            tag = "w%d_lam%s" % (w, str(lam).replace(".", ""))
            put("rate_%s" % tag, rate(v2, w, lam, "m"), "spike_v2_results.json",
                "part3(w=%d,lam=%s).rate_measured" % (w, lam))
            put("rateeig_%s" % tag, rate(v2, w, lam, "e"), "spike_v2_results.json",
                "part3(w=%d,lam=%s).rate_ma_eig" % (w, lam))
    rel = [abs(x["rate_measured"] - x["rate_ma_eig"]) / x["rate_ma_eig"] for x in v2["part3"]]
    put("rate_rel_max", max(rel), "spike_v2_results.json", "max |measured-eig|/eig over part3 (12 cells)")
    put("rate_span", max(x["rate_measured"] for x in v2["part3"]) / min(x["rate_measured"] for x in v2["part3"]),
        "spike_v2_results.json", "max/min rate_measured over part3")
    put("rate_w1_law_lam005", [x["rate_w1_law"] for x in v2["part3"] if x["lam"] == 0.05][0],
        "spike_v2_results.json", "part3(lam=0.05).rate_w1_law")
    put("rate_wrong_at_w64", [x["rate_w1_law"] / x["rate_measured"] for x in v2["part3"]
                              if x["lam"] == 0.05 and x["w"] == 64][0], "spike_v2_results.json",
        "part3(lam=0.05,w=64).rate_w1_law / rate_measured")
    put("seedcount", p1(v2, "uniform", 50, 0.01)["T_loss_median"]["n_seeds"], "spike_v2_results.json",
        "part1(uniform,n=50,lam=0.01).T_loss_median.n_seeds (seeds per cell)")
    for src, n, lam in (("uniform", 50, 0.005), ("uniform", 50, 0.01), ("uniform", 50, 0.02),
                        ("twohot", 50, 0.005), ("twohot", 50, 0.01), ("twohot", 50, 0.02),
                        ("twohot", 200, 0.005)):
        r = p1(v2, src, n, lam)
        tag = "%s_n%d_lam%s" % (src, n, str(lam).replace(".", ""))
        put("pheal_%s" % tag, mean_of(r["p_heal"]), "spike_v2_results.json",
            "part1(%s,n=%d,lam=%s).p_heal.mean" % (src, n, lam))
        put("pheal_hi_%s" % tag, r["p_heal"]["hi"], "spike_v2_results.json",
            "part1(%s,n=%d,lam=%s).p_heal.hi" % (src, n, lam))
        put("pheal_lo_%s" % tag, r["p_heal"]["lo"], "spike_v2_results.json",
            "part1(%s,n=%d,lam=%s).p_heal.lo" % (src, n, lam))

    # ---- the criterion axis ------------------------------------------------------------------
    for src, w in (("uniform", 1), ("uniform", 4), ("twohot", 1), ("twohot", 4)):
        for key in ("stat", "heal", "ratio"):
            put("crit_%s_w%d_%s" % (src, w, key), crit(v3, src, w, key), "spike_v3_results.json",
                "controls criterion_dependence(%s,w=%d).lambda_stationary|heal|ratio" % (src, w))
    b = [c for c in v3["controls"] if c["kind"] == "behavioural" and c["source"] == "uniform" and c["w"] == 1][0]
    put("beh_below_full", b["below"]["full_support_fraction"], "spike_v3_results.json",
        "controls behavioural(uniform,w=1).below.full_support_fraction")
    put("beh_above_full", b["above"]["full_support_fraction"], "spike_v3_results.json",
        "controls behavioural(uniform,w=1).above.full_support_fraction")
    put("v3_resolution_decades", max(c["log_resolution_decades"] for c in v3["cells"]),
        "spike_v3_results.json", "max cells.log_resolution_decades")
    put("v3_cells", len(v3["cells"]), "spike_v3_results.json", "len(cells)")
    # §4.6 -- the held-out test of every candidate mechanism quantity, and the raw spans
    for cand, src, name in (("rate_MA", "uniform", "pred_rate_uni"),
                            ("snr", "uniform", "pred_snr_uni"),
                            ("snr", "twohot", "pred_snr_twohot")):
        r = [x for x in v3["predictions"] if x["candidate"] == cand and x["source"] == src][0]
        put("%s_miss" % name, r["held_out_max_rel_miss"], "spike_v3_results.json",
            "predictions(%s,%s).held_out_max_rel_miss" % (cand, src))
    vs = [c["mean_var"] for c in v3["cells"]]
    put("var_lo", min(vs), "spike_v3_results.json", "min cells.mean_var")
    put("var_hi", max(vs), "spike_v3_results.json", "max cells.mean_var")
    put("var_span", max(vs) / min(vs), "spike_v3_results.json", "max/min cells.mean_var")
    sn = [c["snr"] for c in v3["cells"]]
    put("snr_lo", min(sn), "spike_v3_results.json", "min cells.snr")
    put("snr_hi", max(sn), "spike_v3_results.json", "max cells.snr")

    # ---- the reference layer -----------------------------------------------------------------
    put("n_refs", len(cur), "refs/curated.json", "len(entries)")
    put("n_refs_authored", meta["with_authors"], "refs/meta.json", "with_authors")
    put("n_curated_verified", sum(1 for l in open(os.path.join(HERE, "refs", "verify.log")) if l.startswith("OK")),
        "refs/verify.log", "count of OK lines")
    put("n_figs", len(man["figures"]), "figures/manifest.json", "len(figures)")
    return V


CITE = re.compile(r"\{ref:(?:role:)?(?:in:)?([A-Za-z0-9_:.\-/]+)\}")


def expand_citations(text, cur):
    """Expand `{ref:...}` into bracketed numbers, and CHECK every claims it makes.

    Three forms, each with its own check:
      {ref:role:<family>}      -> a citation group of the whole family
      {ref:in:<family>:<bare>} -> one reference, ASSERTED to be filed under that family (so a
                                  reference cited as, say, a prevention method must actually have
                                  been curated as one)
      {ref:<bare>}             -> one reference
    A bare identifier that is not in the curated set is an error: it would render a citation number
    that does not exist.
    """
    by_bare = {e["bare"]: e for e in cur}
    number = json.load(open(os.path.join(HERE, "refs", "numbering.json")))["numbering"]
    by_role = {}
    for e in cur:
        by_role.setdefault(e["role"], []).append(e["bare"])
    for r in by_role:
        by_role[r].sort(key=lambda b: number[b])
    cited = set()

    def take(bares, where):
        for b in bares:
            if b not in number:
                sys.exit("CITATION NOT IN THE CURATED SET: %s (cited as %s) -- every citation must "
                         "resolve to a numbered, verified reference" % (b, where))
            cited.add(number[b])
        return bares

    def repl(m):
        key = m.group(1)
        if m.group(0).startswith("{ref:role:"):
            if key not in by_role:
                sys.exit("no such reference family: %s" % key)
            bares = take(by_role[key], "family " + key)
            return "[" + ", ".join(str(number[b]) for b in bares) + "]"
        if m.group(0).startswith("{ref:in:"):
            role, bare = key.split(":", 1)
            if bare not in by_bare:
                sys.exit("CITATION NOT IN THE CURATED SET: %s" % bare)
            if by_bare[bare]["role"] != role:
                sys.exit("MIS-FILED CITATION: %s is curated as `%s` but cited as a `%s` reference"
                         % (bare, by_bare[bare]["role"], role))
            take([bare], "in-family")
            return "[%d]" % number[bare]
        take([key], "single")
        return "[%d]" % number[key]

    out = CITE.sub(repl, text)
    # every reference must be genuinely cited in the body
    allnums = set(int(n) for n in number.values())
    missing = sorted(allnums - set(int(c) for c in cited))
    if missing:
        sys.exit("%d of %d references are never cited in the text (padding is not allowed): %s"
                 % (len(missing), len(allnums), missing[:20]))
    return out, len(cited)


def main():
    V = build_values()
    src = open(SRC, encoding="utf-8").read()
    used = set()

    def sub(m):
        name, fmt = m.group(1), m.group(2)
        if name not in V:
            sys.exit("NO SUCH VALUE: {{%s}} -- every number in the prose must be owned by an "
                     "artefact; add it to build_values() or fix the name" % name)
        used.add(name)
        val = V[name][0]
        if fmt:
            try:
                return format(val, fmt)
            except (ValueError, TypeError) as e:
                sys.exit("bad format '{{%s:%s}}': %s" % (name, fmt, e))
        if isinstance(val, float):
            return ("%.6g" % val)
        return str(val)

    # the reference list is an artefact (rendered by make_references.py) -- injected, never retyped
    refs = open(os.path.join(HERE, "references.md"), encoding="utf-8").read()
    body = refs.split("## References", 1)[1].strip()
    src = src.replace("{{references}}", body)
    cur = load("refs/curated.json")["entries"]
    src, n_cited = expand_citations(src, cur)
    odd = [m.group(1) for m in LOOSE.finditer(src) if not PLACEHOLDER.fullmatch(m.group(0))]
    if odd:
        sys.exit("PLACEHOLDER-SHAPED token(s) the substitution cannot read: %s -- a value name is "
                 "[A-Za-z0-9_]+; compute the number in build_values() and give it a name" % odd)
    out = PLACEHOLDER.sub(sub, src)
    left = LOOSE.findall(out)
    if left:
        sys.exit("UNRESOLVED placeholder-shaped text survived substitution: %s" % left)
    unused = sorted(set(V) - used)
    if unused:
        sys.exit("%d value(s) built but never used in the prose: %s" % (len(unused), unused))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    prov = {n: {"value": (v[0] if isinstance(v[0], (int, float, str)) else str(v[0])),
                "artefact": v[1], "how": v[2]} for n, v in sorted(V.items())}
    json.dump(prov, open(VALS, "w"), indent=1, sort_keys=True)
    words = len(re.findall(r"\S+", out))
    print("built %s: %d placeholders resolved from %d values, %d citations (%d references), %d words"
          % (os.path.basename(OUT), len(used), len(V), n_cited, len(cur), words))
    print("-> %s (provenance for every number)" % os.path.basename(VALS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
