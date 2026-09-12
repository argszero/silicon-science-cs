"""Validator for the issue #1 canonical artefact.

Two tiers, mirroring the practice adopted in this journal:
  Tier A (structural)  - the artefact is internally complete and self-consistent
  Tier B (mechanism)   - the manuscript claims are actually present in the data

Every check asserts a number that the manuscript quotes, so a re-run that silently changes a
result fails validation instead of quietly rewriting the paper.

Usage: python validate.py
"""
import hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CANONICAL = os.path.join(HERE, "canonical_results.json")

TIMING_PAT = re.compile(r"(second|elapsed|wall|runtime|duration|timestamp|minutes|hours)", re.I)


def gt(a, b):
    return a - b > 0


def lt(a, b):
    return a - b < 0


class Checks:
    def __init__(self):
        self.rows = []

    def ok(self, cid, desc, cond, detail=""):
        self.rows.append({"id": cid, "desc": desc, "passed": bool(cond), "detail": str(detail)})
        print("%-4s %-4s %-56s %s" % (cid, "PASS" if cond else "FAIL", desc, detail))

    def summary(self):
        n = len(self.rows)
        k = sum(1 for r in self.rows if r["passed"])
        print("\nVALIDATE %d/%d" % (k, n))
        return k == n


def timing_keys(obj, path=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if TIMING_PAT.search(k):
                out.append(path + "/" + k)
            out += timing_keys(v, path + "/" + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += timing_keys(v, path + "/%d" % i)
    return out


def between(x, lo, hi):
    return gt(x, lo) and lt(x, hi)


def main():
    if not os.path.exists(CANONICAL):
        print("canonical_results.json missing - run canonical_runner.py first")
        return 1
    d = json.loads(open(CANONICAL).read())
    c = Checks()

    # ---- Tier A: structural ----
    sha = d.get("sha256", "")
    payload = {k: v for k, v in d.items() if k != "sha256"}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    c.ok("A01", "canonical sha256 recomputes from the payload",
         sha == hashlib.sha256(blob).hexdigest(), sha[:16])

    tk = timing_keys(d)
    c.ok("A02", "no wall-clock field anywhere in the artefact", not tk, "found %s" % tk[:3])

    sw = d["sweep"]
    c.ok("A03", "plan size is 84 cells", sw["plan_size"] == 84, sw["plan_size"])
    arms = {}
    for cell in sw["cells"]:
        arms[cell["arm"]] = arms.get(cell["arm"], 0) + 1
    c.ok("A04", "arm composition is 36 MAIN / 8 POSITION / 2 TYPE_entity / 2 FILLER_neutral / 36 recall-matched control",
         arms == {"MAIN": 36, "POSITION": 8, "TYPE_entity": 2, "FILLER_neutral": 2,
                  "TYPERM_status": 18, "TYPERM_entity": 18}, arms)
    rm = [c for c in sw["cells"] if c["arm"].startswith("TYPERM_")]
    c.ok("A04b", "the recall-matched control pairs both families at the same density and instance",
         len(rm) == 36 and
         sorted({(c["n_chunks"], c["interference"]) for c in rm}) == [(64, 0.15), (64, 0.3), (128, 0.15)] and
         {c["kind"] for c in rm} == {"status", "entity"}, len(rm))
    c.ok("A05", "84 cells stored", len(sw["cells"]) == 84, len(sw["cells"]))
    req = ("full", "dense_k1", "dense_k4", "dense_k8", "bm25_k4", "no_evidence", "oracle",
           "dense_rank_gold", "bm25_rank_gold", "tell_audit", "n_family")
    missing = [k for k in req if k not in sw["cells"][0]]
    c.ok("A06", "every cell carries the required condition keys", not missing, missing)

    c.ok("A07", "sampled decoding uses 4 seeds", len(sw["seeds"]) == 4, sw["seeds"])
    c.ok("A08", "temperature is 0.7", abs(sw["temperature"] - 0.7) < 1e-9, sw["temperature"])
    c.ok("A09", "retrieval budgets are k in 1,2,4,8", sw["k"] == [1, 2, 4, 8], sw["k"])

    v = d["fidelity"]["verdict"]
    checks = v.get("checks", {})
    npass = sum(1 for x in checks.values() if x)
    c.ok("A10", "reader fidelity gate is complete and green",
         gt(len(checks), 11) and npass == len(checks), "%d/%d checks" % (npass, len(checks)))
    c.ok("A11", "held-out perplexity is in the plausible band",
         between(d["fidelity"]["held_out"]["bits_per_token"], 3.0, 8.0),
         d["fidelity"]["held_out"]["bits_per_token"])
    c.ok("A12", "KV cache is exact against the uncached path",
         d["fidelity"]["kv_cache"]["full_vs_cached_max_abs_diff"] == 0.0,
         d["fidelity"]["kv_cache"]["full_vs_cached_max_abs_diff"])

    der = d["derived"]
    c.ok("A13", "derived artefact covers all 84 cells", der["n_cells"] == 84, der["n_cells"])
    c.ok("A14", "main grid has 18 (length, interference) rows", len(der["main_grid"]) == 18,
         len(der["main_grid"]))
    c.ok("A15", "tell audit is clean in every cell that has distractors",
         all(x["tell_audit"]["clean"] for x in sw["cells"] if x["interference"] != 0.0),
         "distractor cells: %d" % der["n_with_distractor"])

    # ---- Tier B: mechanism ----
    g = der["gap_by_interference"]
    c.ok("B01", "the zero-interference rung's point estimate is positive (a null, not a lead)", gt(g["0.0"], 0.0), g["0.0"])
    nz = [k for k in g if float(k) != 0.0]
    c.ok("B02", "retrieval loses at every interference level that has distractors",
         all(lt(g[k], 0.0) for k in nz), {k: g[k] for k in nz})
    c.ok("B03", "the deficit saturates instead of growing without bound",
         lt(max(abs(g[k]) for k in nz), 1.5), max(abs(g[k]) for k in nz))
    c.ok("B04", "the advantage is confined to the zero-interference rung",
         lt(der["retrieval_ahead_with_distractor"], 3) and gt(der["retrieval_ahead_no_distractor"], 2),
         "ahead %d/%d no-distractor, %d/%d distractor" % (
             der["retrieval_ahead_no_distractor"], der["n_no_distractor"],
             der["retrieval_ahead_with_distractor"], der["n_with_distractor"]))

    lo = der["length_only"]
    spread = max(lo.values()) - min(lo.values())
    c.ok("B05", "length alone does not move the reader (4x context range)",
         lt(spread, 0.15), "spread %.3f" % spread)
    c.ok("B06", "the length control covers 64, 128 and 256 chunks",
         sorted(lo.keys()) == ["128", "256", "64"], sorted(lo.keys()))
    fc = der["filler_control"]
    c.ok("B07", "neutral out-of-domain filler behaves like related filler",
         lt(abs(fc["neutral"] - fc["related"]), 0.2), fc)

    mx = {}
    for row in der["main_grid"]:
        mx.setdefault(row["L"], {})[row["I"]] = row
    for L in (64, 256):
        reader_drop = mx[L][0.8]["full"] - mx[L][0.0]["full"]
        dense_drop = mx[L][0.8]["dense_k4"] - mx[L][0.0]["dense_k4"]
        c.ok("B08.%d" % L, "at L=%d the retriever collapses faster than the reader" % L,
             lt(dense_drop, reader_drop - 0.5),
             "reader %.3f retriever %.3f" % (reader_drop, dense_drop))

    tc, tcd = der["type_contrast"], der["type_contrast_dense4"]
    c.ok("B09", "same-entity confusables leave reading ahead of dense retrieval",
         lt(tcd["same_entity_status"], tc["same_entity_status"]),
         "full %.3f dense4 %.3f" % (tc["same_entity_status"], tcd["same_entity_status"]))
    c.ok("B10", "different-entity distractors flip the sign to retrieval",
         gt(tcd["different_entity"], tc["different_entity"]),
         "full %.3f dense4 %.3f" % (tc["different_entity"], tcd["different_entity"]))

    pos = der["position"]
    middle = pos["0.5"]
    ends = [pos["0.0"], pos["1.0"]]
    c.ok("B11", "evidence position is U-shaped: the middle is the worst point",
         lt(middle, min(ends) - 0.5) and not gt(middle, min(pos.values())),
         {k: pos[k] for k in sorted(pos)})
    c.ok("B12", "all five position points are present", len(pos) == 5, sorted(pos.keys()))

    c.ok("B13", "expanding the retrieval budget does not rescue it at high interference",
         lt(mx[256][0.6]["dense_k8"], mx[256][0.6]["full"]),
         "L=256 I=0.60: full %.3f dense_k8 %.3f" % (mx[256][0.6]["full"], mx[256][0.6]["dense_k8"]))
    c.ok("B14", "pooled BM25 recall over distractor cells is low",
         der["pooled_recall_bm25_k4"] == "0/30", der["pooled_recall_bm25_k4"])
    c.ok("B15", "dense recall improves with budget but stays poor",
         der["pooled_recall_distractor_cells"]["dense_k1"].endswith("/30") and
         der["pooled_recall_distractor_cells"]["dense_k8"].startswith("15"),
         der["pooled_recall_distractor_cells"])

    def ci(L, I):
        for row in der["sampled_wilson"]:
            if row["L"] == L and abs(row["I"] - I) < 1e-9:
                return row
        return None

    r0, rh = ci(256, 0.0), ci(256, 0.45)
    c.ok("B16", "the no-distractor CI is disjoint from the high-interference CI",
         gt(r0["lo"], rh["hi"]), "%.3f vs %.3f" % (r0["lo"], rh["hi"]))
    c.ok("B17", "sampled exact match is 1.000 without distractors", r0["rate"] == 1.0, r0["rate"])
    c.ok("B18", "sampled exact match is 0.000 at I=0.45 and above (L=256)",
         all(ci(256, I)["rate"] == 0.0 for I in (0.45, 0.6, 0.8)),
         [ci(256, I)["rate"] for I in (0.45, 0.6, 0.8)])
    zero = [row for row in der["main_grid"] if row["I"] == 0.0]
    gaps = [row["no_evidence"] - row["full"] for row in zero]
    c.ok("B19", "with no distractors, removing the evidence costs the reader about two nats",
         all(lt(g, -1.0) for g in gaps), "min gap %.3f over %d cells" % (min(gaps), len(gaps)))
    hi = [row for row in der["main_grid"] if row["I"] == 0.8]
    hi_gaps = [row["no_evidence"] - row["full"] for row in hi]
    c.ok("B21", "at high interference the evidence-free gap narrows (reader is already degraded)",
         gt(min(hi_gaps), min(gaps)) or min(hi_gaps) - min(gaps) > -0.0,
         "I=0.80 min gap %.3f against I=0.00 min gap %.3f" % (min(hi_gaps), min(gaps)))
    c.ok("B20", "the oracle arm answers, so the instrument can answer",
         all(cell["oracle"]["greedy_exact"] for cell in sw["cells"]),
         "oracle exact in %d cells" % len(sw["cells"]))

    ok = c.summary()
    print("sha256 %s" % sha[:32])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
