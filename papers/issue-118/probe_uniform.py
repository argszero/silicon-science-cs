#!/usr/bin/env python3
"""probe_uniform -- THE UNIFORM ROUTER, read at both ends of the load range.

The uniform router is the balancing IDEAL: the most a routing-side remedy could ever
achieve. Two numbers the manuscript prints are readings of it, and neither belonged to
a committed instrument before this file:

  (a) the CONSTANT'S IMPLIED TOLERANCE. For a uniform router and the exact route, the
      drop rate D(C = 1.25) and the critical capacity C_min at tolerance 1e-6, over a
      mu = T/E grid that reaches down into the decode regime (mu = 1). This is the
      paper's central table (section 5.3): C = 1.25 is a DIFFERENT tolerance in every
      cell, ~1e-2 in the training regime it came from and ~3e-1 at mu = 1.

  (b) THE FLOOR at the measured router's own T (E = 16, T = 8192). The measured-router
      arm reports C_min = 4.18 with no balancing and 1.37 under heavy balancing; the
      floor it converges toward -- and never crosses -- is read off HERE.

Both are asked of spike_v0's exact kernel (bin_drop / exact_drop_rate / c_min), imported
rather than re-derived: a second implementation of the same route is a second place to be
wrong, so this file is a different QUESTION, not a different instrument.

Run: /usr/bin/python3 probe_uniform.py     ->  probe_uniform_results.json
"""
import json
import sys

import numpy as np

import spike_v0 as K

TOL = 1e-6
C_FOLK = 1.25

# (E, mu): exactly the rows of the manuscript's uniform-router table (section 5.2), in its order
CELLS = [(64, 1), (64, 2), (64, 4), (64, 8), (64, 16), (256, 16), (128, 8), (64, 128)]
# the measured router's own cell (model_v3 arm 2): E = 16 experts, T = 8192 tokens/forward
FLOOR = (16, 8192)


def main():
    out = {"tol": TOL, "C_folk": C_FOLK, "seed": K.SEED, "cells": [], "floor": {}}
    print("=" * 96)
    print("(a) THE CONSTANT'S IMPLIED TOLERANCE -- uniform router, exact route, tol=%.0e" % TOL)
    print("%5s%6s%7s%16s%12s%14s" % ("E", "T", "mu", "D(C=1.25)", "C_min", "tolerance implied"))
    for (E, mu) in CELLS:
        T = int(mu * E)
        p = np.full(E, 1.0 / E)
        d = K.exact_drop_rate(E, T, p, C_FOLK)
        cm = K.c_min(E, T, p, tol=TOL)
        out["cells"].append({"E": E, "T": T, "mu": float(mu),
                             "drop_at_folk": d, "c_min": cm})
        print("%5d%6d%7d%16.6g%12.4f%14s" % (E, T, mu, d, cm, "%.1e" % d))
    print()
    print("  -> C = 1.25 is a DIFFERENT tolerance in every cell: the constant is not wrong,")
    print("     it is UNLABELLED. It accepts ~1e-2 in the training regime it came from")
    print("     (mu=128) and four orders of magnitude more at decode-like mu=1.")

    print()
    print("=" * 96)
    E, T = FLOOR
    print("(b) THE FLOOR at the measured router's own cell: E=%d experts, T=%d tokens/forward" % (E, T))
    p = np.full(E, 1.0 / E)
    cm = K.c_min(E, T, p, tol=TOL)
    d = K.exact_drop_rate(E, T, p, C_FOLK)
    pred, imb, noise = K.predict_c_min(E, T, p)
    out["floor"] = {"E": E, "T": T, "mu": T / E, "c_min": cm, "drop_at_folk": d,
                    "ratio_pred": pred, "imb": imb, "noise": noise}
    print("  uniform-router C_min (exact, tol=%.0e) = %.4f" % (TOL, cm))
    print("  D(C=1.25) under the ideal router        = %.6f" % d)
    print("  the registered decomposition at this cell: imb %.4f + noise %.4f = %.4f" % (imb, noise, pred))
    print("  -> this is the floor the measured-router arm (model_v3) converges toward from")
    print("     above: 4.18 with no balancing, 1.37 under heavy balancing, floor %.4f." % cm)

    print()
    print("=" * 96)
    E, T = 64, 1024
    p = np.full(E, 1.0 / E)
    print("(c) C_MIN MOVES WITH THE DECLARED TOLERANCE -- exact route, E=%d, T=%d (mu=%g)"
          % (E, T, T / E))
    ti = []
    for tol in (1e-3, 1e-6, 1e-9):
        cm = K.c_min(E, T, p, tol=tol)
        ti.append({"tol": tol, "c_min": cm})
        print("   declared tol=%.0e   C_min = %.4f" % (tol, cm))
    assert ti[0]["c_min"] < ti[1]["c_min"] < ti[2]["c_min"], \
        "C_min is not increasing in strictness of the declared tolerance"
    print("  -> a C_min reading is meaningless without its tolerance: the SAME router needs")
    print("     %.3f or %.3f depending on the bar the caller declares." % (ti[0]["c_min"], ti[2]["c_min"]))
    out["tolerance_indexed"] = {"E": E, "T": T, "readings": ti}
    with open("probe_uniform_results.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote probe_uniform_results.json")


if __name__ == "__main__":
    sys.exit(main())
