#!/usr/bin/env python3
"""Issue #87 -- R397 side-check: are the TWO stored null blocks (cal 40, val 20) EXACTLY what this
generator produces, cell by cell?

WHY THIS CHECK EXISTS.  R397's F1 asserted identity on ONE cell (shifted|0.5, cal seed #0).  The whole
round's conclusion is read off the cal-vs-val dispersion gap, so the premise that BOTH blocks came out of
the same construction the round is now drawing from has to be verified across the blocks, not at a single
point.  If one block fails to reproduce, the gap is an artefact of the stored file, not a property of the
seed stream -- and that is a cheaper explanation than either the drift or the small-sample story.

Reads smoke_v8_results.json; writes r397_identity_results.json.  Run: /usr/bin/python3 r397_identity.py
"""
import hashlib
import io
import json
import os
import sys

import numpy as np

import smoke_v5 as S5
import smoke_v8 as S8
import smoke_v9 as S9
import smoke_v11 as S11

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "r397_identity_results.json")
BANDS = [("shifted", 0.5), ("shifted", 2.0), ("unshifted", 1.0), ("unshifted", 3.0)]


def main():
    q = S9.QUBITS
    edges = S5.edges_for(S9.EDGE_KIND, q)
    Z = S5.bits_of(q)
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, S9.LAYERS) for g in S5.GAMMAS} for c in S11.CONVS}
    raw = json.loads(io.open(S11.SRC8, encoding="utf-8").read())
    n_cal = len(raw["cal_means"]["shifted"]["0.5"])
    n_val = len(raw["val_means"]["shifted"]["0.5"])

    rows = []
    for conv, gamma in BANDS:
        Kq, rival = S11.band_kernels(q, edges, Z, conv, gamma, metrics[conv])
        for tag, seed0, step, n in (("cal", S8.CAL_SEED0, 37, n_cal), ("val", S8.VAL_SEED0, 53, n_val)):
            stored = [float(x) for x in raw["%s_means" % tag][conv][str(gamma)]]
            got = [S11.null_cell_means(q, edges, Z, conv, gamma, None, Kq, rival, seed0 + step * i)["mean"]
                   for i in range(n)]
            exact = [bool(a == b) for a, b in zip(stored, got)]
            worst = max(abs(a - b) for a, b in zip(stored, got))
            rows.append(dict(band="%s|%g" % (conv, gamma), block=tag, n=n, n_exact=sum(exact),
                             worst_absdiff=float(worst),
                             sd_stored=float(np.std(stored, ddof=1)), sd_reproduced=float(np.std(got, ddof=1))))
            print("%-16s %s n=%2d exact %2d/%2d  worst |diff| %.3e  sd stored %.5f reproduced %.5f"
                  % ("%s|%g" % (conv, gamma), tag, n, sum(exact), n, worst,
                     np.std(stored, ddof=1), np.std(got, ddof=1)))
    ok = all(r["n_exact"] == r["n"] for r in rows)
    rep = dict(bands=[list(b) for b in BANDS], rows=rows, all_cells_exact=bool(ok),
               cal_seed0=S8.CAL_SEED0, val_seed0=S8.VAL_SEED0, cal_step=37, val_step=53)
    txt = json.dumps(rep, indent=1, sort_keys=True, default=float)
    io.open(OUT, "w", encoding="utf-8").write(txt)
    rep["report_sha256"] = hashlib.sha256(txt.encode("utf-8")).hexdigest()
    print("\nall cells exact: %s" % ok)
    print("report sha256 = %s" % rep["report_sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
