#!/usr/bin/env python3
"""Issue #132 -- spike_v2: the (theta, tau, r) grid, and a rate owed over the ELIGIBLE subset.

R585 (`spike_v1.py`) established, on the language axis, that a corpus-wide DF frame is blind to a
community register exactly when `s * phi < theta` (critical prevalence `phi* = theta / s`), with the
frame acting on the RESIDUE gate only.  Its parameters were swept by hand and the headline number
was a COUNT of 120/120 -- a count over ALL pairs, some of which the level could not possibly act on.

THIS INSTRUMENT ADDS TWO THINGS.

1. THE r AXIS.  The guard's second gate is `|shared \\ F_level| >= r`.  R585 held r = 10 fixed.  But
   the register has a FIXED size in units (reg_units), so r is not free: for r > reg_units the
   register can NEVER supply the residue, and the level-induced count is 0 BY CONSTRUCTION -- a
   DERIVED zero, not a measurement.  Sweeping r locates the boundary and separates the two.

2. THE ELIGIBLE SUBSET (rant item 16).  `fire <=> sim >= tau AND |shared \\ F| >= r`.  A level can
   only act on a pair that PASSES the similarity gate: for a pair with `sim < tau` the frame is
   irrelevant, the pair is not a "non-flag" it is INELIGIBLE, and counting it in the denominator
   deflates the rate by exactly the pass fraction.  So every rate here is reported as
      eligible_rate = (fire_corpus - fire_pool) / sim_pass
   with the DILUTION factor `sim_pass / n_pairs` stated beside it.  When `sim_pass = 0` the rate is
   UNDEFINED and is printed as such -- never as 0.000 (a 0/0 cell is not a measurement).

Deterministic: fixed seed, sorted iteration, no clocks, no environment reads.
Usage:  /usr/bin/python3 spike_v2.py [--selftest]
Out:    spike_v2_results.json
"""
import hashlib
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("SPIKE_OUT") or os.path.join(HERE, "spike_v2_results.json")   # SPIKE_OUT lets a reproduction run write OUTSIDE the package

CAP = 400
MIN_DOC_CHARS = 120
DOC_CHARS_MAX = 200

EN_DIR = os.path.join(HERE, "corpus")
I18N_DIR = os.path.join(HERE, "corpus_i18n")
BOOKS = {
    "en": [(EN_DIR, "pg1342"), (EN_DIR, "pg1661"), (EN_DIR, "pg2701"), (EN_DIR, "pg345"),
           (EN_DIR, "pg74"), (EN_DIR, "pg76"), (EN_DIR, "pg84"), (EN_DIR, "pg98")],
    "es": [(I18N_DIR, "pg2000_es"), (I18N_DIR, "pg15532_es"), (I18N_DIR, "pg29640_es"),
           (I18N_DIR, "pg29731_es"), (I18N_DIR, "pg67248_es")],
    "fr": [(I18N_DIR, "pg14155_fr"), (I18N_DIR, "pg17989_fr")],
    "de": [(I18N_DIR, "pg2229_de")],
    "it": [(I18N_DIR, "pg1012_it"), (I18N_DIR, "pg21425_it"), (I18N_DIR, "pg47786_it"),
           (I18N_DIR, "pg49626_it")],
}
FILLER = ("en", "es", "fr", "de")

REGISTER_IT = ("buongiorno a tutti spero che stiate tutti bene e che la giornata sia serena un caro "
               "saluto e buona lettura a chiunque passi di qui ci vediamo nei commenti")
REGISTER_EN = ("hello everyone i hope you are all doing well and having a wonderful day best wishes "
               "and happy reading to anyone who passes by see you in the comments")

TAUS = (0.3, 0.5, 0.7)
THETAS = (0.02, 0.05, 0.10)
PHIS = (0.0, 0.05, 0.10, 0.20, 0.30, 1.0)
R_VALUES = (5, 10, 20, 27, 40)
PAIRS = 120
STATS = ("char2", "word3")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sums(d):
    p = os.path.join(d, "SHA256SUMS")
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                want, name = line.split(None, 1)
                out[name.strip()] = want
    return out


GUT_S = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG", re.I)
GUT_E = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG", re.I)


def strip_gutenberg(t):
    L = t.split("\n")
    a, b = 0, len(L)
    for i, l in enumerate(L):
        if GUT_S.search(l):
            a = i + 1
            break
    for i in range(len(L) - 1, -1, -1):
        if GUT_E.search(L[i]):
            b = i
            break
    return "\n".join(L[a:b])


def verify_corpus():
    se, si = load_sums(EN_DIR), load_sums(I18N_DIR)
    bad = []
    for lang, books in BOOKS.items():
        for d, b in books:
            f = os.path.join(d, b + ".txt")
            if not os.path.exists(f):
                bad.append(b + " (missing)")
                continue
            want = (si if d == I18N_DIR else se).get(b + ".txt")
            if want and sha256(f) != want:
                bad.append(b + " (sha mismatch)")
    return bad


def documents():
    docs = []
    for lang in ("en", "es", "fr", "de", "it"):
        for d, b in BOOKS[lang]:
            with open(os.path.join(d, b + ".txt"), encoding="utf-8", errors="replace") as f:
                body = strip_gutenberg(f.read())
            n = 0
            for para in re.split(r"\n\s*\n", body):
                p = " ".join(para.split())[:DOC_CHARS_MAX]
                if len(p) >= MIN_DOC_CHARS:
                    docs.append({"lang": lang, "book": b, "text": p})
                    n += 1
                    if n >= CAP:
                        break
    return docs


def units_of(text, stat):
    t = " ".join(text.lower().split())
    if stat == "char2":
        return {t[i:i + 2] for i in range(len(t) - 1)}
    w = re.findall(r"[a-zA-Z\u00c0-\u00ff']+", t)
    return {" ".join(w[i:i + 3]) for i in range(len(w) - 2)}


def dice(a, b):
    return (2.0 * len(a & b) / (len(a) + len(b))) if (a or b) else 0.0


def df_table(units, idx):
    cnt, n = {}, 0
    for i in idx:
        n += 1
        for u in units[i]:
            cnt[u] = cnt.get(u, 0) + 1
    return cnt, n


def frame(cnt, n, theta):
    return {u for u, c in cnt.items() if c / n >= theta}


def eligible_rate(numerator, denominator):
    """The eligible-subset rule (rant item 16): a rate exists only where the test is defined."""
    return (numerator / denominator) if denominator else None


def selftest():
    u = units_of(REGISTER_IT, "word3")
    checks = [
        ("the register yields at least 27 word3 units", len(u) >= 27),
        ("word3 of a 2-word string is empty", len(units_of("ciao mondo", "word3")) == 0),
        ("Dice is 1.0 on an identical pair", abs(dice({1, 2, 3}, {1, 2, 3}) - 1.0) < 1e-12),
        ("a frame at theta=1.0 keeps only units in EVERY document",
         frame({"a": 3, "b": 2}, 3, 1.0) == {"a"}),
        ("a unit at the exact cutoff is kept (>=, not >)", frame({"a": 1}, 20, 0.05) == {"a"}),
        ("an empty pair is not similar", dice(set(), set()) == 0.0),
        ("the eligible rate is None (not 0) on an empty denominator",
         eligible_rate(0, 0) is None and eligible_rate(3, 12) == 0.25),
    ]
    bad = 0
    for lab, ok in checks:
        print("   %-4s %s" % ("ok" if ok else "FAIL", lab))
        bad += 0 if ok else 1
    print("SELFTEST %d/%d" % (len(checks) - bad, len(checks)))
    return 1 if bad else 0


def pair_ids(rng, pool, n):
    out = []
    for _ in range(n):
        i = pool[rng.randrange(len(pool))]
        j = pool[rng.randrange(len(pool))]
        for _ in range(8):
            if j != i:
                break
            j = pool[rng.randrange(len(pool))]
        if j != i:
            out.append((i, j))
    return out


def main():
    bad = verify_corpus()
    if bad:
        sys.exit("CORPUS PIN FAILED: %s -- refusing to measure an unverified corpus" % bad)

    docs = documents()
    by_lang = {}
    for i, d in enumerate(docs):
        by_lang.setdefault(d["lang"], []).append(i)
    corpus_idx = list(range(len(docs)))
    n_corpus = len(corpus_idx)
    strata = [("minority_it", by_lang["it"], REGISTER_IT),
              ("majority_en", by_lang["en"], REGISTER_EN)]

    res = {
        "instrument": "spike_v2.py", "issue": 132,
        "question": ("over the (theta, tau, r) grid, is the level-induced effect a band, and what "
                     "rate does it have over the subset where the check is DEFINED?"),
        "corpus": {"n_docs_total": n_corpus, "n_docs_by_lang": {k: len(v) for k, v in sorted(by_lang.items())},
                   "doc_chars_max": DOC_CHARS_MAX, "sha256_pin_ok": True},
        "params": {"taus": list(TAUS), "thetas": list(THETAS), "phis": list(PHIS), "rs": list(R_VALUES),
                   "pairs_per_cell": PAIRS, "stats": list(STATS)},
        "strata": [{"name": s[0], "n_pool": len(s[1]), "share": len(s[1]) / n_corpus} for s in strata],
        "cells": [],
    }

    rng = random.Random(20261009)
    for name, pool_idx, reg_text in strata:
        share = len(pool_idx) / n_corpus
        for stat in STATS:
            reg = units_of(reg_text, stat)
            base = [units_of(d["text"], stat) for d in docs]
            for phi in PHIS:
                if phi >= 1.0:
                    reg_docs = set(corpus_idx)
                elif phi <= 0.0:
                    reg_docs = set()
                else:
                    reg_docs = set(pool_idx[:int(round(phi * len(pool_idx)))])
                aug = [set(base[i]) for i in range(len(docs))]
                for i in sorted(reg_docs):
                    aug[i] |= reg
                a_corpus, _ = df_table(aug, corpus_idx)
                a_pool, _ = df_table(aug, pool_idx)
                # TWO sampling rules for the pair population -- the eligible-subset rule (rant
                # item 16) makes the denominator explicit, so both are reported:
                #   community  = random pairs of the community (what a deployed guard sees)
                #   affected   = pairs whose two members BOTH carry the register (the subpopulation
                #                the level can act on; the effect lives entirely here)
                aff = sorted(set(pool_idx) & reg_docs)
                samples = [("community", pair_ids(rng, sorted(pool_idx), PAIRS))]
                samples.append(("affected", pair_ids(rng, aff, PAIRS) if len(aff) >= 2 else []))
                corpus_prev = len(reg_docs) / n_corpus
                for sample, pairs in samples:
                    if not pairs:
                        continue
                    sims = [dice(aug[i], aug[j]) for (i, j) in pairs]
                    shareds = [aug[i] & aug[j] for (i, j) in pairs]
                    for theta in THETAS:
                        Fc = frame(a_corpus, n_corpus, theta)
                        Fp = frame(a_pool, len(pool_idx), theta)
                        res_c = [len(s - Fc) for s in shareds]
                        res_p = [len(s - Fp) for s in shareds]
                        for tau in TAUS:
                            elig = [k for k, s in enumerate(sims) if s >= tau]
                            sim_pass = len(elig)
                            for r in R_VALUES:
                                fc = sum(1 for k in elig if res_c[k] >= r)
                                fp = sum(1 for k in elig if res_p[k] >= r)
                                induced = fc - fp
                                res["cells"].append({
                                    "stratum": name, "stat": stat, "share": share, "sample": sample,
                                    "theta": theta, "tau": tau, "r": r, "phi": phi,
                                    "register_units": len(reg),
                                    "corpus_prevalence": corpus_prev,
                                    "critical_prevalence": theta / share,
                                    "hidden_from_corpus": len(reg & Fc) == 0,
                                    "n_pairs": len(pairs), "sim_gate_pass": sim_pass,
                                    "dilution": sim_pass / len(pairs),
                                    "fire_none_all": sum(1 for s in shareds if len(s) >= r),
                                    "max_residue_corpus": max((res_c[k] for k in elig), default=None),
                                    "max_residue_pool": max((res_p[k] for k in elig), default=None),
                                    "max_residue_gap": max((res_c[k] - res_p[k] for k in elig),
                                                           default=None),
                                    "fire_corpus": fc, "fire_pool": fp, "level_induced": induced,
                                    "eligible_rate": eligible_rate(induced, sim_pass),
                                    "r_exceeds_register": r > len(reg)})

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
        f.write("\n")

    # ---- certificates -----------------------------------------------------------------------
    cells = res["cells"]

    def cert(pred, lab):
        ok = sum(1 for c in cells if pred(c))
        print("   %-4s %s: %d/%d" % ("ok" if ok == len(cells) else "FAIL", lab, ok, len(cells)))
        return ok == len(cells)

    print("cells: %d" % len(cells))
    a = cert(lambda c: (c["eligible_rate"] is None) == (c["sim_gate_pass"] == 0),
             "the eligible rate is None IFF nothing passed the sim gate (no 0/0 cell)")
    b = cert(lambda c: not (c["r_exceeds_register"] and c["level_induced"] > 0),
             "r > register_units  =>  level-induced count is 0 (a DERIVED zero)")
    b2 = cert(lambda c: not (c["max_residue_corpus"] is not None
                             and c["max_residue_corpus"] < c["r"] and c["fire_corpus"] > 0),
              "the corpus level cannot fire where its residue NEVER reaches r (the r-boundary is "
              "explained, not observed)")
    b3 = cert(lambda c: not (c["max_residue_gap"] is not None and c["hidden_from_corpus"]
                             and c["max_residue_gap"] > c["register_units"]),
              "the level-induced residue gap never exceeds the register's own size (the register "
              "is the whole of the hidden material in these documents)")
    c_ = cert(lambda c: c["level_induced"] >= 0, "the level-induced count is never negative")

    print()
    print("word3 tau=0.5 theta=0.05, minority_it -- none/corpus/pool | induced | rate(simpass) | dil")
    for c in cells:
        if (c["stratum"], c["stat"], c["tau"], c["theta"], c["sample"]) != \
                ("minority_it", "word3", 0.5, 0.05, "affected"):
            continue
        rate = "undef" if c["eligible_rate"] is None else "%.3f" % c["eligible_rate"]
        print("  phi=%.2f r=%2d reg=%-3d | %3d %4d %4d | %4d | %-6s (%3d) | maxRes c/p=%s/%s%s"
              % (c["phi"], c["r"], c["register_units"], c["fire_none_all"], c["fire_corpus"],
                 c["fire_pool"], c["level_induced"], rate, c["sim_gate_pass"],
                 c["max_residue_corpus"], c["max_residue_pool"],
                 "  <r>REG" if c["r_exceeds_register"] else ""))
    print()
    print("CERTIFICATES", "ALL PASS" if (a and b and b2 and b3 and c_) else "FAIL")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
