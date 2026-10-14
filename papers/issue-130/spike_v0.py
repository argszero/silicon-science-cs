#!/usr/bin/env python3
"""spike_v0 -- the operating characteristic of artefact-similarity checks (de-risk P1).

Object: a check that flags "duplicate" when S(artifact, reference) >= tau.
  * recall  R(eps; tau, L) = P( S < tau | artifact perturbed at exact rate eps )
  * the calibration population fixes tau (two conventions):
      A "unrelated":  tau_A = 95th pct of S over UNRELATED segment pairs  (FPR 5%)
      B "benign":     tau_B = 5th pct of S over pairs edited at eps_benign (gate tolerates rewording)
Registered question P1: does eps* (R = 0.5) move with the artefact length L ?

Real text only (Project Gutenberg, pinned in corpus/SHA256SUMS). Ground truth by construction.
"""
import sys, json, io, hashlib, random, math, re
from collections import Counter

WORDS = re.compile(r"[A-Za-z']+")
L_GRID   = [25, 50, 100, 200, 400]
EPS_GRID = [0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
EPS_BENIGN = 0.05
N_REFS = 40
N_CAL  = 200
SEED0  = 20261008
K5, K3 = 5, 3
# DETERMINISM (R567): `hash(stat)` is randomized per process (PYTHONHASHSEED), so a seed built from
# it drew a DIFFERENT sample every run (measured on spike_v0: benign eps* spread up to 0.037 over 3
# runs). Statistics now carry an explicit, stable integer code.
STAT_CODE = {"jac5": 0, "cos": 1, "jac3c": 2}

def load_books():
    import glob, os
    books = []
    for p in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "corpus", "pg*.txt"))):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        i = t.find("*** START OF THE PROJECT GUTENBERG EBOOK")
        j = t.find("*** END OF THE PROJECT GUTENBERG EBOOK")
        if i > 0 and j > i: t = t[i:j]
        w = WORDS.findall(t.lower())
        if len(w) > 30000: books.append((os.path.basename(p), w))
    return books

def shingles(toks, k):
    return set(tuple(toks[i:i+k]) for i in range(len(toks)-k+1))

def jaccard(a, b):
    if not a and not b: return 1.0
    u = len(a | b)
    return len(a & b)/u if u else 0.0

def similarity(stat, A, B, idf):
    if stat == "jac5":  return jaccard(shingles(A,K5), shingles(B,K5))
    if stat == "jac3c": return jaccard(set(x for x in _char3(A)), set(x for x in _char3(B)))
    if stat == "cos":
        # weights must be applied CONSISTENTLY: component = tf * idf appears in BOTH the
        # inner product and the two norms, so that S(A,A) == 1 exactly (identity certificate).
        ca, cb = Counter(A), Counter(B)
        wa = {w: v*idf.get(w,1.0) for w, v in ca.items()}
        wb = {w: v*idf.get(w,1.0) for w, v in cb.items()}
        # DETERMINISM (R567): a SET INTERSECTION iterates in string-hash order, and Python randomizes
        # string hashing per process, so `sum(...)` over it accumulated in a different order each run
        # and landed on different last bits (measured: max |delta| 2.78e-15, cosine cells only; the
        # artefact's sha256 therefore did not reproduce). Iterate a SORTED key list and accumulate with
        # math.fsum (correctly rounded, order-independent). Reproducibility is a property of the
        # instrument, not of the seed -- the identity certificate (|S-1|<1e-12) cannot see this.
        num = math.fsum(wa[w]*wb[w] for w in sorted(wa.keys() & wb.keys()))
        na = math.sqrt(math.fsum(v*v for v in wa.values()))
        nb = math.sqrt(math.fsum(v*v for v in wb.values()))
        return num/(na*nb) if na and nb else 0.0
    raise ValueError(stat)

def _char3(toks):
    s = " ".join(toks)
    return [s[i:i+K3] for i in range(max(0,len(s)-K3+1))]

def perturb(toks, eps, vocab, rng):
    """exact-rate substitution: each token replaced w.p. eps by a draw from the vocab."""
    return [ (rng.choice(vocab) if rng.random() < eps else w) for w in toks ]

def pct(xs, p):
    xs = sorted(xs); 
    if not xs: return float("nan")
    i = min(len(xs)-1, max(0, int(round(p*(len(xs)-1)))))
    return xs[i]

def crossing(eps_grid, rec):
    """linear interpolation of the eps where recall crosses 0.5."""
    for i in range(len(eps_grid)-1):
        r0, r1 = rec[i], rec[i+1]
        if (r0-0.5)*(r1-0.5) <= 0 and r0 != r1:
            return eps_grid[i] + (0.5-r0)*(eps_grid[i+1]-eps_grid[i])/(r1-r0)
    return None

def main():
    books = load_books()
    print("books: %d  (tokens: %s)" % (len(books), [len(b[1]) for b in books]))
    allt = [w for _, ws in books for w in ws]
    cnt = Counter(allt); vocab = [w for w, _ in cnt.most_common(20000)]
    # idf over the book corpus (document = book)
    df = Counter()
    for _, ws in books: df.update(set(ws))
    N = len(books); idf = {w: math.log((N+1)/(df[w]+1))+1.0 for w in cnt}

    out = {"corpus": [b[0] for b in books], "L_grid": L_GRID, "eps_grid": EPS_GRID,
           "eps_benign": EPS_BENIGN, "n_refs": N_REFS, "n_cal": N_CAL, "seed0": SEED0,
           "cells": {}, "eps_star": {}}
    for stat in ("jac5", "cos", "jac3c"):
        for L in L_GRID:
            rng = random.Random(SEED0 + L*1000 + STAT_CODE[stat])
            # draw N_REFS reference segments, each from a distinct (book, offset)
            refs = []
            for r in range(N_REFS):
                bk, ws = books[r % len(books)]
                off = rng.randrange(0, max(1, len(ws)-L-1))
                refs.append(ws[off:off+L])
            # calibration A: unrelated pairs (different segments)
            unrel = []
            for c in range(N_CAL):
                a = refs[c % N_REFS]
                b = refs[(c*7+3) % N_REFS]
                unrel.append(similarity(stat, a, b, idf))
            tauA = pct(unrel, 0.95)
            # calibration B: pairs edited at the benign rate (same segment)
            ben = []
            for c in range(N_CAL):
                a = refs[c % N_REFS]
                ben.append(similarity(stat, a, perturb(a, EPS_BENIGN, vocab, rng), idf))
            tauB = pct(ben, 0.05)
            recA, recB = [], []
            for eps in EPS_GRID:
                hitA = hitB = 0
                for r in range(N_REFS):
                    a = refs[r]
                    e = perturb(a, eps, vocab, rng)
                    s = similarity(stat, a, e, idf)
                    hitA += (s < tauA); hitB += (s < tauB)
                recA.append(hitA/N_REFS); recB.append(hitB/N_REFS)
            key = "%s|L=%d" % (stat, L)
            out["cells"][key] = {"tau_unrelated": tauA, "tau_benign": tauB,
                                 "recall_unrelated": recA, "recall_benign": recB,
                                 "n_per_cell": N_REFS}
            ea = crossing(EPS_GRID, recA); eb = crossing(EPS_GRID, recB)
            out["eps_star"][key] = {"unrelated": ea, "benign": eb}
            print("%-7s L=%-4d tauA=%.4f tauB=%.4f | eps*: unrel=%s benign=%s | R_benign=%s"
                  % (stat, L, tauA, tauB,
                     ("%.3f"%ea) if ea else "none", ("%.3f"%eb) if eb else "none",
                     " ".join("%.2f"%v for v in recB)))

    js = json.dumps(out, indent=1, sort_keys=True)
    io.open("spike_v0_results.json", "w", encoding="utf-8").write(js)
    print("\nartefact sha256:", hashlib.sha256(js.encode()).hexdigest()[:16],
          "bytes", len(js.encode()))

if __name__ == "__main__":
    main()


def _char2(toks):
    s = " ".join(toks)
    return [s[i:i+2] for i in range(max(0,len(s)-1))]
