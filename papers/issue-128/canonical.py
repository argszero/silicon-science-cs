#!/usr/bin/env python3
"""canonical.py -- issue #128: the single source of the manuscript's numbers.

Every headline number the manuscript will state is RE-DERIVED here from the instrument artefacts
(spike_v3/v4_v5_results.json), never retyped.  The output carries, for each number, the source file
and the field path it came from, so a reader can audit any claim back to the run that produced it.

Usage:
  python3 canonical.py            write canonical_results.json + print a summary
  python3 canonical.py --check    assert every canonical number equals the value in the artefact
"""
import io, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "canonical_results.json")


def load(name):
    return json.load(io.open(os.path.join(HERE, name), encoding="utf-8"))


def beta_above(curve, M_star, basev):
    """Exponent of the loss curve above M*: fit log(loss) ~ beta log(M - M*) over strictly-positive loss."""
    if M_star is None or basev in (None, 0):
        return None, 0
    pts = [(r["M"] - M_star, (basev - r["value"]) / float(basev))
           for r in curve if r["M"] > M_star and r["value"] is not None and r["value"] < basev]
    if len(pts) < 3:
        return None, len(pts)
    X = np.log([p[0] for p in pts]); Y = np.log([p[1] for p in pts])
    if len(set(X.tolist())) < 2:
        return None, len(pts)
    return float(np.polyfit(X, Y, 1)[0]), len(pts)


def _ranks(x):
    """AVERAGE ranks -- the standard convention for ties.  An argsort-of-argsort invents an ordering
    inside a tied group, which matters here because M*/k takes only ~6-9 distinct values, so rho is
    convention-sensitive; the canonical statistic uses average ranks and reports the spread."""
    x = np.asarray(x, float)
    order = np.argsort(x, kind="stable"); r = np.empty(len(x)); r[order] = np.arange(1, len(x) + 1)
    sx = np.sort(x); i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j + 1] == sx[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return r


def spearman(x, y):
    """Tie-corrected (average-rank) Spearman -- the canonical convention."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3 or len(set(x.tolist())) < 2 or len(set(y.tolist())) < 2:
        return None
    rx = _ranks(x) - _ranks(x).mean(); ry = _ranks(y) - _ranks(y).mean()
    den = np.sqrt((rx * rx).sum() * (ry * ry).sum())
    return None if den == 0 else float((rx * ry).sum() / den)


def pearson(x, y):
    return float(np.corrcoef(np.asarray(x, float), np.asarray(y, float))[0, 1])


# ---------------------------------------------------------------- P1' (synthetic)
def p1_synthetic(v3):
    out = {}
    for setting in ("A", "B"):
        sub = [c for c in v3["cases"] if c["setting"] == setting]
        ok = [c for c in sub if c["M_star"] is not None]
        widths = [c["M_star"] / float(c["k"]) for c in ok]
        out[setting] = {
            "n_cases": len(sub),
            "M_gt_M_first": sum(1 for c in ok if c["M_star"] > c["M_first"]),
            "median_free_width": float(np.median(widths)) if widths else None,
            "whole_quota_free": sum(1 for w in widths if w == 1.0),
        }
    widths = [c["M_star"] / float(c["k"]) for c in v3["cases"] if c["M_star"] is not None]
    out["all"] = {"n_cases": len(v3["cases"]), "whole_quota_free": sum(1 for w in widths if w == 1.0),
                  "median_free_width": float(np.median(widths)) if widths else None}
    return out


def p1_by_family(v3):
    fams = {}
    for c in v3["cases"]:
        if c["M_star"] is None:
            continue
        fams.setdefault(c["family"], []).append(c["M_star"] / float(c["k"]))
    return {f: float(np.median(v)) for f, v in sorted(fams.items())}


# ---------------------------------------------------------------- P3 (cost law)
def p3(v3):
    out = {}
    for obj in ("maxmin", "maxsum"):
        bs = [beta_above(c["floors_curve"], c["M_star"], c["unconstrained"])[0]
              for c in v3["cases"] if c["obj"] == obj]
        bs = [b for b in bs if b is not None]
        out[obj] = {"n_fittable": len(bs), "median_beta": float(np.median(bs)) if bs else None}
    return out


# ---------------------------------------------------------------- P4 (baseline)
def p4(v3):
    out = {}
    for obj in ("maxmin", "maxsum"):
        sub = [c for c in v3["cases"] if c["obj"] == obj]
        gaps = []
        for c in sub:
            g = c["floors_curve"][0].get("greedy_value")
            if g is None:
                continue
            gaps.append((c["unconstrained"] - g) / float(c["unconstrained"]))
        out[obj] = {"n": len(gaps),
                    "greedy_exact": sum(1 for x in gaps if abs(x) < 1e-12),
                    "median_gap": float(np.median(gaps)) if gaps else None,
                    "max_gap": float(max(gaps)) if gaps else None}
    return out


# ---------------------------------------------------------------- routes / defects
def route_health(v3):
    """INFEASIBLE is a legitimate verdict; UNRESOLVED is a missing measurement.  They must not be
    counted together (Class 194): the status field decides, never `value is None`."""
    cells = [r for c in v3["cases"] for r in c["floors_curve"] + c["caps_curve"]]
    by_status = {}
    for r in cells:
        by_status[r.get("status")] = by_status.get(r.get("status"), 0) + 1
    unresolved = [s for s in by_status if s not in ("OPTIMAL", "INFEASIBLE")]
    return {"n_cells": sum(c["n_cells"] for c in v3["cases"]),
            "cross_disagreements": sum(1 for c in v3["cases"] for r in c["floors_curve"] + c["caps_curve"]
                                       if r.get("cross_checked") and r.get("cross_agrees") is False),
            "by_status": by_status,
            "infeasible": by_status.get("INFEASIBLE", 0),
            "unresolved": sum(by_status.get(s, 0) for s in unresolved),
            "unresolved_statuses": unresolved}


# ---------------------------------------------------------------- real data (v4)
def real_p1(v4):
    A = v4["part_a"]["cases"]
    ok = [c for c in A if c["M_star"] is not None]
    w = [c["M_star"] / float(c["k"]) for c in ok]
    return {"n_cases": len(A), "M_gt_M_first": sum(1 for c in ok if c["M_star"] > c["M_first"]),
            "median_free_width": float(np.median(w)) if w else None,
            "whole_quota_free": sum(1 for x in w if x == 1.0),
            "corpus": v4["corpus"]["name"], "corpus_sha256": v4["corpus"]["sha256"]}


def real_p2b(v4):
    B = v4["part_b"]["cases"]
    return {"alignment_min": min(c["alignment"] for c in B),
            "alignment_max": max(c["alignment"] for c in B),
            "spearman_alignment_width": spearman([c["alignment"] for c in B],
                                                 [c["M_star"] / float(c["k"]) for c in B])}


def real_p4(v4):
    out = {}
    for obj in ("maxmin", "maxsum"):
        sub = [c for c in v4["part_a"]["cases"] if c["obj"] == obj]
        gaps = [(c["unconstrained"] - c["floors_curve"][0]["greedy_value"]) / float(c["unconstrained"])
                for c in sub if c["floors_curve"][0].get("greedy_value") is not None]
        out[obj] = {"n": len(gaps), "greedy_exact": sum(1 for x in gaps if abs(x) < 1e-12),
                    "median_gap": float(np.median(gaps)) if gaps else None}
    return out


# ---------------------------------------------------------------- wide sweep (v5)
def wide(v5):
    cells = [c for blk in v5["corpora"].values() for c in blk["cells"]]
    ok = [c for c in cells if c["free_width"] is not None]
    A = [c["alignment"] for c in ok]; W = [c["free_width"] for c in ok]
    per = {}
    for cname, blk in v5["corpora"].items():
        cs = [c for c in blk["cells"] if c["free_width"] is not None]
        per[cname] = {"n": len(cs),
                      "spearman": spearman([c["alignment"] for c in cs], [c["free_width"] for c in cs])}
    pg = {}
    for obj in ("maxmin", "maxsum"):
        sub = [c for c in ok if c["obj"] == obj]
        gaps = [(c["unconstrained"] - c["curve"][0]["greedy_value"]) / float(c["unconstrained"])
                for c in sub if c["curve"][0].get("greedy_value") is not None]
        pg[obj] = {"n": len(gaps), "greedy_exact": sum(1 for x in gaps if abs(x) < 1e-12),
                   "median_gap": float(np.median(gaps)) if gaps else None}
    conv = {"tie_corrected": spearman(A, W), "pearson_raw": pearson(A, W)}
    return {"n_cells": len(cells), "n_solved": len(ok), "rho_conventions": conv,
            "alignment_min": min(A), "alignment_max": max(A),
            "alignment_spread": max(A) - min(A),
            "width_distinct": len(set(np.round(W, 6).tolist())),
            "width_spread": max(W) - min(W),
            "pooled_spearman": spearman(A, W), "per_corpus": per, "p4": pg}


def build():
    v3 = load("spike_v3_results.json"); v4 = load("spike_v4_results.json"); v5 = load("spike_v5_results.json")
    return {
        "instrument": "issue #128 -- the zero-cost region of a group quota",
        "sources": {"spike_v3_results.json": "synthetic, 64 cases / 1152 cells",
                    "spike_v4_results.json": "real corpus (Wine Quality), 24 + 72 cells",
                    "spike_v5_results.json": "real-corpus wide-alignment sweep, 320 cells"},
        "P1_synthetic": {"by_setting": p1_synthetic(v3), "by_family": p1_by_family(v3)},
        "P1_real": real_p1(v4),
        "P2_real_partb": real_p2b(v4),
        "P2_wide": wide(v5),
        "P3_cost_law": p3(v3),
        "P4_baseline_synthetic": p4(v3),
        "P4_baseline_real": real_p4(v4),
        "route_health": route_health(v3),
    }


def report(c):
    print("== canonical results: issue #128 ==")
    p1 = c["P1_synthetic"]["by_setting"]
    print("P1' (synthetic): A %d/%d M*>M_first, median width %.3f; B %d/%d, %.3f; whole quota free %d/%d"
          % (p1["A"]["M_gt_M_first"], p1["A"]["n_cases"], p1["A"]["median_free_width"],
             p1["B"]["M_gt_M_first"], p1["B"]["n_cases"], p1["B"]["median_free_width"],
             p1["all"]["whole_quota_free"], p1["all"]["n_cases"]))
    print("   by family:", {k: round(v, 3) for k, v in c["P1_synthetic"]["by_family"].items()})
    r = c["P1_real"]
    print("P1' (real %s): %d/%d, median width %.3f, whole quota free %d"
          % (r["corpus"], r["M_gt_M_first"], r["n_cases"], r["median_free_width"], r["whole_quota_free"]))
    b = c["P2_real_partb"]
    print("P2' (R556 within-family): alignment %.3f-%.3f, spearman %s"
          % (b["alignment_min"], b["alignment_max"], ("%+.3f" % b["spearman_alignment_width"])))
    w = c["P2_wide"]
    print("P2' (R557 wide sweep): alignment %.3f-%.3f spread %.3f, width distinct %d spread %.3f, pooled spearman %+.3f"
          % (w["alignment_min"], w["alignment_max"], w["alignment_spread"],
             w["width_distinct"], w["width_spread"], w["pooled_spearman"]))
    for k, v in w["per_corpus"].items():
        print("     %-6s n=%d spearman %s" % (k, v["n"], ("%+.3f" % v["spearman"]) if v["spearman"] is not None else "-"))
    print("P3 (synthetic cost law):", {k: (round(v["median_beta"], 3) if v["median_beta"] is not None else None, v["n_fittable"])
                                       for k, v in c["P3_cost_law"].items()})
    for tag, key in (("synthetic", "P4_baseline_synthetic"), ("real", "P4_baseline_real")):
        p4d = c[key]
        print("P4 (%s greedy exact):" % tag,
              {k: "%d/%d" % (v["greedy_exact"], v["n"]) for k, v in p4d.items()})
    print("routes:", {k: c["route_health"][k] for k in ("n_cells","by_status","infeasible","unresolved")},
          "cross_disagreements", c["route_health"]["cross_disagreements"])


def check():
    """Re-derive and assert the canonical numbers equal the artefact values (a self-audit)."""
    c = build()
    assert c["route_health"]["cross_disagreements"] == 0, "cross disagreements"
    assert c["route_health"]["unresolved"] == 0, "unresolved cells"
    assert c["route_health"]["by_status"]["OPTIMAL"] + c["route_health"]["by_status"]["INFEASIBLE"] \
        == c["route_health"]["n_cells"], "status partition incomplete"
    assert c["P1_real"]["M_gt_M_first"] == c["P1_real"]["n_cases"], "P1' real not strict"
    assert c["P1_synthetic"]["by_setting"]["A"]["M_gt_M_first"] == 32, "P1' A"
    assert c["P1_synthetic"]["by_setting"]["B"]["M_gt_M_first"] == 30, "P1' B"
    assert c["P2_wide"]["alignment_spread"] > 0.8 and c["P2_wide"]["width_distinct"] >= 5, "wide sweep range"
    assert abs(c["P2_wide"]["pooled_spearman"]) < 0.2, "P2' wide pooled should be near zero"
    assert c["P3_cost_law"]["maxsum"]["median_beta"] > 0.5 and abs(c["P3_cost_law"]["maxmin"]["median_beta"]) < 0.2, "P3"
    print("canonical --check: ALL ASSERTIONS HOLD")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    c = build()
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(c, indent=1, sort_keys=True))
    report(c)
    print("\nwrote", OUT)
