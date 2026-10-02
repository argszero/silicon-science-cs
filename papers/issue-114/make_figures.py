#!/usr/bin/env python3
"""Build every figure of issue #114 from `canonical_results.json`.

The figures are a VIEW of the committed artefact: this script reads nothing else, and it
records in `figures/manifest.json` the sha256 of both the PNG it wrote and the slice of the
artefact it drew -- so a figure can never drift away from the numbers it claims to show
without the manifest changing, and `reproduce.sh` requires the manifest to match.

Run:  python3 make_figures.py          (writes figures/*.png and figures/manifest.json)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

from plotlib import (Axes, BLACK, BLUE, GREEN, GREY, LIGHT, ORANGE, PURPLE, RED, WHITE,
                     Canvas)

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
CANON = os.path.join(HERE, "canonical_results.json")

S_GRID = [0.0, 0.0625, 0.125, 0.25, 0.5, 0.75, 1.0]
R_GRID = [0.0, 0.05, 0.10, 0.20, 0.30]
LAMBDAS = [0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
R_COLOR = {0.0: BLACK, 0.05: BLUE, 0.10: GREEN, 0.20: ORANGE, 0.30: RED}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def series_hash(obj) -> str:
    return sha(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode())


def key(s, r):
    return f"{s}|{r}"


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------

def fig1(can: Canvas, D) -> str:
    """The frontier in s: detection and breakage bands at three exposures."""
    cap = ("Detection and breakage against specificity `s`, each drawn as the full band over the "
           "96 declared draws. Left: detection saturates in `s` and its band narrows as the spec "
           "gets stronger. Right: breakage is exactly 0 at every `s` when exposure `r = 0`, and "
           "rises with `r` once representation is exposed.")
    left = Axes(can, (100, 70, 450, 400), (0, 1), (0, 1.05),
                "SPECIFICITY S", "DETECTION", xticks=[0, 0.25, 0.5, 0.75, 1.0],
                yticks=[0, 0.25, 0.5, 0.75, 1.0], yfmt="{:.2f}", xfmt="{:.2f}", scale=2,
                title="A  DETECTION")
    right = Axes(can, (620, 70, 950, 430), (0, 1), (0, 1.05),
                 "SPECIFICITY S", "BREAKAGE", xticks=[0, 0.25, 0.5, 0.75, 1.0],
                 yticks=[0, 0.25, 0.5, 0.75, 1.0], yfmt="{:.2f}", xfmt="{:.2f}", scale=2,
                 title="B  BREAKAGE")
    left.frame()
    right.frame()
    for r in (0.05, 0.20):
        cells = [D["cells"][key(s, r)] for s in S_GRID]
        lo = [c["det_band"][0] for c in cells]
        hi = [c["det_band"][1] for c in cells]
        left.vband(S_GRID, lo, hi, R_COLOR[r])
        left.plot(S_GRID, [(a + b) / 2 for a, b in zip(lo, hi)], R_COLOR[r], 2)
    for r in (0.0, 0.05, 0.20):
        cells = [D["cells"][key(s, r)] for s in S_GRID]
        lo = [c["break_band"][0] for c in cells]
        hi = [c["break_band"][1] for c in cells]
        right.vband(S_GRID, lo, hi, R_COLOR[r])
        right.plot(S_GRID, [(a + b) / 2 for a, b in zip(lo, hi)], R_COLOR[r], 2)
    left.legend([(R_COLOR[0.05], "R = 0.05"), (R_COLOR[0.20], "R = 0.20")], 110, 330, 2)
    right.legend([(R_COLOR[0.0], "R = 0.00"), (R_COLOR[0.05], "R = 0.05"),
                  (R_COLOR[0.20], "R = 0.20")], 630, 300, 2)
    return cap


def fig2(can: Canvas, D) -> str:
    """The frontier s*(lambda, r) as a band over the draws."""
    cap = ("The graded optimum `s*(lambda, r)`: each horizontal bar spans the argmax observed "
           "across the 96 draws, with the modal value marked. At `r = 0` the optimum is the "
           "boundary `s = 1` for every `lambda` (the strongest spec wins, because there is no "
           "breakage to pay for). For `r > 0` the optimum moves interior and falls with `lambda`, "
           "until the empty spec (`s = 0`) wins outright at `lambda >= 2`.")
    ax = Axes(can, (150, 70, 900, 440), (0, 1.02), (0, len(LAMBDAS) * len(R_GRID) + 0.5),
              "S*  (ARGMAX OF DETECTION - LAMBDA * BREAKAGE)", "", xticks=[0, 0.25, 0.5, 0.75, 1.0],
              yticks=[], scale=2, title="THE FRONTIER, AS A BAND OVER 96 DRAWS")
    ax.frame()
    y = len(LAMBDAS) * len(R_GRID) - 0.5
    labels = []
    for lam in LAMBDAS:
        labels.append((y, f"L={lam:g}"))
        for r in R_GRID:
            f = D["frontier"][f"{lam}|{r}"]
            col = R_COLOR[r]
            x0, x1 = ax.X(f["min"]), ax.X(f["max"])
            can.rect(min(x0, x1), int(ax.Y(y)) - 3, max(x0, x1), int(ax.Y(y)) + 3, col, True)
            m = ax.X(f["mode"])
            can.rect(int(m) - 2, int(ax.Y(y)) - 7, int(m) + 2, int(ax.Y(y)) + 7, BLACK, True)
            y -= 1
        y -= 0.6
    for yy, lab in labels:
        can.text(14, int(ax.Y(yy)) - 6, lab, BLACK, 2)
    ax.vline(1.0, GREY, dash=True)
    ax.legend([(R_COLOR[r], f"R = {r:.2f}") for r in R_GRID], 560, 305, 2)
    can.text(150, 16, "BAR = RANGE OVER DRAWS;  BLACK TICK = MODE", GREY, 2)
    return cap


def fig3(can: Canvas, D) -> str:
    """Alignment: the same specificity, twelve pin sets."""
    cap = ("Matched specificity, twelve pin-set alignments (prior P1). Detection against `s` at "
           "`r = 0.05`: the structured pin sets are the extremes (`edges` best, `block-low`/`high` "
           "worst) and the seeded random ones sit between them. The span is 1.37x at most and "
           "collapses to 1.00 at `s = 1` -- the registered prediction of at least 2x is refuted.")
    ax = Axes(can, (100, 70, 700, 420), (0, 1), (0.6, 1.02), "SPECIFICITY S", "DETECTION",
              xticks=[0, 0.25, 0.5, 0.75, 1.0], yticks=[0.6, 0.7, 0.8, 0.9, 1.0],
              xfmt="{:.2f}", yfmt="{:.2f}", scale=2,
              title="P1: THE SAME S, TWELVE PIN SETS (R = 0.05)")
    ax.frame()
    names = ["low", "high", "even", "odd", "edges", "None", "1", "2", "3", "4", "5", "6"]
    pal = [BLUE, ORANGE, GREEN, RED, PURPLE, BLACK, GREY, GREY, GREY, GREY, GREY, GREY]
    for name, col in zip(names, pal):
        ys = [D["alignment"][key(s, 0.05)]["values"].get(name) for s in S_GRID]
        pts = [(s, v) for s, v in zip(S_GRID, ys) if v is not None]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], col, 2)
    ax.legend([(BLUE, "LOW"), (ORANGE, "HIGH"), (GREEN, "EVEN"), (RED, "ODD"),
               (PURPLE, "EDGES"), (BLACK, "SPREAD"), (GREY, "RANDOM")], 710, 90, 2)
    return cap


def fig4(can: Canvas, D) -> str:
    """Composition moves breakage, not detection."""
    cap = ("The composition band at matched (s, r): for each exposure `r` at `s = 0.125`, the "
           "vertical extent of breakage across the eight clause orderings (which kinds fill the "
           "budget; the clause COUNT is unchanged) against the same extent for detection. "
           "Breakage swings by up to 0.479 while detection never moves by more than 0.096, so a "
           "claim of the form 'at exposure r the false-alarm rate is x' is not well posed.")
    ax = Axes(can, (110, 70, 760, 420), (0, 0.32), (0, 1.05), "EXPOSURE R", "SHARE",
              xticks=[0, 0.1, 0.2, 0.3], yticks=[0, 0.25, 0.5, 0.75, 1.0],
              xfmt="{:.2f}", yfmt="{:.2f}", scale=2,
              title="THE MIX BAND AT S = 0.125")
    ax.frame()
    rs = [r for r in R_GRID]
    blo = [D["mix"][key(0.125, r)]["break_band"][0] for r in rs]
    bhi = [D["mix"][key(0.125, r)]["break_band"][1] for r in rs]
    dlo = [D["mix"][key(0.125, r)]["det_band"][0] for r in rs]
    dhi = [D["mix"][key(0.125, r)]["det_band"][1] for r in rs]
    ax.vband(rs, blo, bhi, ORANGE)
    ax.vband(rs, dlo, dhi, BLUE)
    ax.plot(rs, [(a + b) / 2 for a, b in zip(blo, bhi)], ORANGE, 2)
    ax.plot(rs, [(a + b) / 2 for a, b in zip(dlo, dhi)], BLUE, 2)
    ax.legend([(ORANGE, "BREAKAGE (BAND)"), (BLUE, "DETECTION (BAND)")], 780, 100, 2)
    return cap


def fig5(can: Canvas, D) -> str:
    """The reachable region: exposure is cheap at low specificity and capped at high."""
    cap = ("The reachable region of the (s, r) plane. A specification that spends `s*M` clauses "
           "on observable behaviour can carry at most `r <= B/(B + s*M)` representational ones, "
           "with `B` the menu the reference's syntax offers (21-47 here). The curve is the "
           "boundary for the smallest, median and largest menu; the points are the measured "
           "cells, hollow where the request was out of reach.")
    ax = Axes(can, (110, 70, 720, 420), (0, 1), (0, 0.8), "SPECIFICITY S", "EXPOSURE R",
              xticks=[0, 0.25, 0.5, 0.75, 1.0], yticks=[0, 0.2, 0.4, 0.6, 0.8],
              xfmt="{:.2f}", yfmt="{:.1f}", scale=2,
              title="THE REACHABLE REGION OF THE (S, R) PLANE")
    ax.frame()
    ss = [i / 100 for i in range(1, 101)]
    for B, col in ((21, RED), (29, BLUE), (47, GREEN)):
        ys = [B / (B + s * 256) for s in ss]
        ax.plot(ss, ys, col, 1)
    for s in S_GRID:
        for r in R_GRID:
            c = D["cells"][key(s, r)]
            x, y = ax.X(s), ax.Y(r)
            col = BLACK if c["reached"] else GREY
            can.rect(int(x) - 2, int(y) - 2, int(x) + 2, int(y) + 2, col, True)
    ax.legend([(RED, "B = 21 (BOUNDARY)"), (BLUE, "B = 29"), (GREEN, "B = 47"),
               (BLACK, "MEASURED CELL")], 740, 100, 2)
    return cap


def fig6(can: Canvas, D) -> str:
    """The mechanism: which clause kinds can reject what, alone."""
    cap = ("The mechanism, by clause kind: the share of semantics-changing mutations a kind "
           "alone can reject, against the share of semantics-preserving mutations it alone "
           "rejects. The observational family rejects every defect and no legitimate change; "
           "among the representational kinds the literal-presence family is the only one with a "
           "favourable ratio (const_present 0.643 against 0.0005), while `size_le` and `depth_le` "
           "reject a thousand legitimate rewrites and no defect at all.")
    kinds = sorted(D["mechanism_by_kind"], key=lambda k: -(
        D["mechanism_by_kind"][k]["changing"] / max(1, D["mechanism_by_kind"][k]["preserving"])))
    ax = Axes(can, (250, 60, 900, 420), (0, 1.02), (0, len(kinds) + 0.5), "SHARE OF MUTANTS",
              "", xticks=[0, 0.25, 0.5, 0.75, 1.0], yticks=[], scale=2,
              title="WHAT EACH CLAUSE KIND CAN REJECT, ALONE")
    ax.frame()
    y = len(kinds) - 0.5
    for k in kinds:
        v = D["mechanism_by_kind"][k]
        d = v["changing"] / D["population"]["changing_mutations"]
        f = v["preserving"] / D["population"]["preserving_mutations"]
        yy = ax.Y(y)
        can.rect(int(ax.X(0)), int(yy) - 5, int(ax.X(d)), int(yy) - 1, BLUE, True)
        can.rect(int(ax.X(0)), int(yy) + 1, int(ax.X(f)), int(yy) + 5, ORANGE, True)
        can.text(14, int(yy) - 5, k, BLACK, 2)
        y -= 1
    ax.legend([(BLUE, "REJECTS A CHANGE"), (ORANGE, "REJECTS A LEGIT REWRITE")], 560, 36, 2)
    return cap


def main() -> int:
    argv = sys.argv[1:]
    check = "--check" in argv
    outdir = FIGDIR
    tmp = None
    if check:
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        outdir = tmp.name

    with open(CANON) as fh:
        D = json.load(fh)
    os.makedirs(outdir, exist_ok=True)
    canon_sha = sha(open(CANON, "rb").read())

    # each entry: (canvas size, draw fn, artifact path, the artefact slice it draws)
    specs = [
        ((980, 480), fig1, "fig1_bands.png",
         {"cells": D["cells"], "r": [0.0, 0.05, 0.20]}),
        ((980, 520), fig2, "fig2_frontier.png", {"frontier": D["frontier"]}),
        ((980, 520), fig3, "fig3_alignment.png",
         {"alignment": {key(s, 0.05): D["alignment"][key(s, 0.05)] for s in S_GRID}}),
        ((980, 500), fig4, "fig4_mixband.png", {"mix": D["mix"]}),
        ((980, 520), fig5, "fig5_region.png",
         {"cells": {key(s, r): D["cells"][key(s, r)] for s in S_GRID for r in R_GRID},
          "menu_sizes": D["menu_sizes"]}),
        ((980, 500), fig6, "fig6_mechanism.png",
         {"mechanism_by_kind": D["mechanism_by_kind"], "population": D["population"]}),
    ]

    manifest = {"artifact": "canonical_results.json", "artifact_sha256": canon_sha,
                "renderer": "plotlib.py (stdlib PNG; no third-party dependency)",
                "figures": []}
    print(f"  rendering to {'a temporary directory (--check)' if check else 'figures/'}")
    for (w, h), fn, name, slice_ in specs:
        can = Canvas(w, h, WHITE)
        cap = fn(can, D)
        path = os.path.join(outdir, name)
        png = can.save(path)
        manifest["figures"].append({
            "figure": f"figures/{name}",
            "caption": cap,
            "png_sha256": sha(png),
            "series_sha256": series_hash(slice_),
            "sources": {"canonical_results.json": canon_sha},
        })
        print(f"  {name:<22} {w}x{h}  {len(png):>7} bytes  {sha(png)[:16]}…")

    if check:
        committed = json.load(open(os.path.join(FIGDIR, "manifest.json")))
        same_png = same_series = 0
        problems = []
        by_name = {f["figure"].split("/")[-1]: f for f in committed["figures"]}
        for entry in manifest["figures"]:
            name = entry["figure"].split("/")[-1]
            want = by_name.get(name)
            got = open(os.path.join(outdir, name), "rb").read()
            if want is None:
                problems.append(f"{name}: absent from the committed manifest")
                continue
            if sha(got) == want["png_sha256"]:
                same_png += 1
            else:
                problems.append(f"{name}: PNG differs from the committed one")
            if entry["series_sha256"] == want["series_sha256"]:
                same_series += 1
            else:
                problems.append(f"{name}: the artefact slice it draws has changed")
            if entry["caption"] != want["caption"]:
                problems.append(f"{name}: caption differs from the committed one")
        print(f"  FIGURES regenerated vs committed: {same_png}/{len(manifest['figures'])} PNG "
              f"byte-identical, {same_series}/{len(manifest['figures'])} series hashes equal, "
              f"{len(problems)} problems")
        for p in problems:
            print(f"    - {p}")
        tmp.cleanup()
        return 0 if not problems else 1

    mpath = os.path.join(outdir, "manifest.json")
    with open(mpath, "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"  manifest.json written ({len(manifest['figures'])} figures)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
