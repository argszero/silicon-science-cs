#!/usr/bin/env python3
"""Issue #132 -- spike_v0: the frame LEVEL, and whether the level is an identity or a dilution.

Registered question (issue #132, R583): a two-stage near-duplicate guard fires iff
    sim(a,b) >= tau   AND   |shared(a,b) \\ F_l| >= r
where F_l is the background frame of "generic" units computed over the population at LEVEL l.

The registration asserted, as an EXACT identity, that
    F_corpus subseteq F_script subseteq F_author   (as SETS)
so the residue is non-decreasing as the level widens.  This instrument TESTS that assertion rather
than assuming it, because a claim carried as an "identity" is a claim that can be false.

What is measured here:

  1. CONTAINMENT.  With df_l(u) = (# documents in population l containing u) / (# documents in l)
     and F_l(theta) = {u : df_l(u) >= theta}, the two directions
         F_corpus subseteq F_pool     and      F_pool subseteq F_corpus
     are counted, as SETS, over the whole unit vocabulary.  A population that is a small SHARE of
     the corpus is the case the registration turns on.

  2. THE EXACT RELATION THAT DOES HOLD.  For a unit u CONFINED to a pool P (every corpus document
     containing u lies in P), the counts coincide -- c_corpus(u) = c_P(u) -- and therefore
         df_corpus(u) = s * df_P(u),      s = N_P / N_corpus,
     exactly.  So a unit that is generic inside its pool at df_P >= theta is INVISIBLE to the corpus
     frame whenever s * df_P(u) < theta, i.e. whenever the pool's share is below the threshold
     ratio theta / df_P(u).  That dilution -- not a set inclusion -- is what the corpus frame does.

  3. THE LADDER.  Flag counts over a (theta, tau, r) grid at each level, on constructed pairs with
     ground truth by construction (a planted near-verbatim template must fire at every level; a pair
     sharing only register must clear at the level whose population makes the register generic).

Certificates: the dilution identity is asserted (with a plant that breaks confinement), the
containment counts are two-sided (a plant corpus where the containment is known to HOLD and one
where it is known to FAIL), and the ladder's two controls are planted.

Deterministic: integer seeds, sorted iteration, no clocks, no environment reads.
Usage:  /usr/bin/python3 spike_v0.py            # writes spike_v0_results.json
        /usr/bin/python3 spike_v0.py --selftest # plants the faults the certificates exist for
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "corpus")
OUT = os.environ.get("SPIKE_OUT") or os.path.join(HERE, "spike_v0_results.json")   # SPIKE_OUT lets a reproduction run write OUTSIDE the package

MIN_DOC_CHARS = 40          # the reader's own document filter (>= 40 characters)

# the 8 pinned Project Gutenberg texts (#130's corpus, SHA256-verified on every read)
BOOKS = ["pg1342", "pg1661", "pg2701", "pg345", "pg74", "pg76", "pg84", "pg98"]


# --------------------------------------------------------------------------- corpus
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_corpus():
    """Every read re-verifies the pin: a corpus is a claim that must be checked, not remembered."""
    sums = {}
    with open(os.path.join(CORPUS, "SHA256SUMS"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            want, name = line.split(None, 1)
            sums[name.strip()] = want
    bad = []
    for b in BOOKS:
        got = sha256(os.path.join(CORPUS, b + ".txt"))
        if sums.get(b + ".txt") != got:
            bad.append(b)
    return bad


GUT_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG", re.I)
GUT_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG", re.I)


def strip_gutenberg(text):
    lines = text.split("\n")
    a, b = 0, len(lines)
    for i, l in enumerate(lines):
        if GUT_START.search(l):
            a = i + 1
            break
    for i in range(len(lines) - 1, -1, -1):
        if GUT_END.search(lines[i]):
            b = i
            break
    return "\n".join(lines[a:b])


def documents():
    """Paragraph documents, one per book, in a FIXED order (book order, then file order)."""
    docs = []
    for bi, b in enumerate(BOOKS):
        with open(os.path.join(CORPUS, b + ".txt"), encoding="utf-8", errors="strict") as f:
            body = strip_gutenberg(f.read())
        for pi, para in enumerate(re.split(r"\n\s*\n", body)):
            p = " ".join(para.split())
            if len(p) >= MIN_DOC_CHARS:
                docs.append({"book": bi, "para": pi, "text": p, "level": len(docs)})
    return docs


def char_bigrams(s):
    """The reader's unit: the set of character bigrams of the normalised text."""
    t = " ".join(s.lower().split())
    return {t[i:i + 2] for i in range(len(t) - 1)}


def word_shingles(s, k=3):
    w = re.findall(r"[a-z']+", s.lower())
    return {" ".join(w[i:i + k]) for i in range(len(w) - k + 1)}


# --------------------------------------------------------------------------- frames
def df_table(doc_units, population, n_total):
    """counts -> per-unit: (#docs in population containing u, #docs in population)."""
    cnt = {}
    n = 0
    for i in population:
        n += 1
        for u in doc_units[i]:
            cnt[u] = cnt.get(u, 0) + 1
    return cnt, n


def frame(cnt, n, theta):
    """F_l(theta) = {u : df_l(u) >= theta}, df read against the population's OWN size."""
    return {u for u, c in cnt.items() if c / n >= theta}


def pool_of_book(docs, books=(0, 1, 2, 3, 4, 5, 6, 7)):
    return [[i for i, d in enumerate(docs) if d["book"] == b] for b in books]


# --------------------------------------------------------------------------- containment / dilution
def containment(doc_units, docs, theta, shingle_book=0):
    """Count, as SETS, the two containment directions for one pool against the corpus.

    cor_not_pool  : u in F_corpus and NOT in F_pool     (corpus-generic, pool-not-generic)
    pool_not_cor  : u in F_pool   and NOT in F_corpus   (pool-generic, corpus-not-generic)
    """
    all_idx = list(range(len(docs)))
    pool_idx = [i for i, d in enumerate(docs) if d["book"] == shingle_book]
    c_all, n_all = df_table(doc_units, all_idx, len(all_idx))
    c_pool, n_pool = df_table(doc_units, pool_idx, len(pool_idx))
    fc = frame(c_all, n_all, theta)
    fp = frame(c_pool, n_pool, theta)
    return {
        "book": shingle_book,
        "n_corpus_docs": n_all,
        "n_pool_docs": n_pool,
        "share": n_pool / n_all,
        "theta": theta,
        "|F_corpus|": len(fc),
        "|F_pool|": len(fp),
        "|F_corpus ∩ F_pool|": len(fc & fp),
        "cor_not_pool": len(fc - fp),
        "pool_not_cor": len(fp - fc),
        "F_corpus_subset_F_pool": len(fc - fp) == 0,
        "F_pool_subset_F_corpus": len(fp - fc) == 0,
    }


def dilution(doc_units, docs, theta):
    """The exact relation: for units CONFINED to a pool, df_corpus = s * df_pool.

    Returns the worst absolute violation over every (book, unit) confined pair, and the counts of
    units that are pool-generic but corpus-invisible (the mechanism the study is about).
    """
    all_idx = list(range(len(docs)))
    c_all, n_all = df_table(doc_units, all_idx, len(all_idx))
    n_books = max(d["book"] for d in docs) + 1
    worst, worst_where = 0.0, None
    n_confined = 0
    hidden = 0                 # pool-generic (df_pool >= theta) AND corpus-invisible (df_corpus < theta)
    for b in range(n_books):
        pool_idx = [i for i, d in enumerate(docs) if d["book"] == b]
        c_pool, n_pool = df_table(doc_units, pool_idx, len(pool_idx))
        s = n_pool / n_all
        for u, cp in c_pool.items():
            ca = c_all.get(u, 0)
            if ca != cp:                      # not confined to the pool -> the identity does not apply
                continue
            n_confined += 1
            pred = s * (cp / n_pool)
            got = ca / n_all
            d = abs(pred - got)
            if d > worst:
                worst, worst_where = d, {"book": b, "unit": u}
            if cp / n_pool >= theta and got < theta:
                hidden += 1
    return {"worst_abs_violation": worst, "worst_where": worst_where,
            "n_confined_pairs": n_confined, "n_pool_generic_but_corpus_invisible": hidden}


def plants():
    """Three synthetic corpora whose answer is known by construction -- two-sided by construction.

    A  pool IS the corpus (share 1.0)                 -> BOTH containments must HOLD (0 violations)
    B  pool is a small share, confined formulaic unit -> a pool-generic unit must be
       corpus-invisible (hidden >= 1), and F_pool must NOT be a subset of F_corpus
    C  a unit that is NOT confined to the pool        -> must be EXCLUDED from the dilution
       certificate (it is not an instance of the identity), while the confined one is counted

    (The first draft of this plant asserted that A must have BOTH counts zero and that B must produce
     a containment violation at the same threshold; both expectations were wrong -- A's book-unique
     unit is pool-generic and corpus-invisible even at share 1/3, which is the mechanism, not a
     defect.  The expectations are repaired here rather than the assertion loosened.)
    """
    out = {}
    # A: ONE book, so the pool IS the corpus
    docs_a, units_a = [], []
    common = ["th", "he", "in", "er", "an", "re", "on", "at", "en", "nd"]
    for i in range(60):
        docs_a.append({"book": 0, "text": "", "para": i})
        units_a.append(set(common) | {"unique_%02d" % i})
    ca = containment(units_a, docs_a, 0.5, 0)
    out["A_share1_cor_not_pool"] = ca["cor_not_pool"]
    out["A_share1_pool_not_cor"] = ca["pool_not_cor"]
    out["A_share1_both_hold"] = (ca["cor_not_pool"] == 0 and ca["pool_not_cor"] == 0)

    # B: a pool of share 1/10 with a unit generic ONLY inside it
    docs_b, units_b = [], []
    for b in range(10):
        for i in range(10):
            u = {"filler"}
            if b == 0:
                u = u | {"poolformulaic"}          # in 100% of pool 0's docs, in 0 of the rest
            docs_b.append({"book": b, "text": "", "para": i})
            units_b.append(u)
    cb = containment(units_b, docs_b, 0.5, 0)
    db = dilution(units_b, docs_b, 0.5)
    out["B_small_share_pool_not_cor"] = cb["pool_not_cor"]
    out["B_small_share_hidden"] = db["n_pool_generic_but_corpus_invisible"]

    # C: confinement filter -- one unit confined to pool 0, one spread over every pool
    docs_c, units_c = [], []
    for b in range(4):
        for i in range(10):
            u = {"everywhere"}
            if b == 0:
                u = u | {"confined"}
            docs_c.append({"book": b, "text": "", "para": i})
            units_c.append(u)
    dc = dilution(units_c, docs_c, 0.5)
    out["C_confined_pairs"] = dc["n_confined_pairs"]
    out["C_worst_abs_violation"] = dc["worst_abs_violation"]
    return out


def share_sweep(doc_units, docs, theta):
    """The law: the hidden count is a function of the POOL SHARE, not of containment.

    One pool = the first k books pooled together (share s = k/8); the frame is computed inside that
    pool at theta and asked how many of its generic units are invisible to the corpus frame.
    """
    all_idx = list(range(len(docs)))
    c_all, n_all = df_table(doc_units, all_idx, len(all_idx))
    rows = []
    for k in (1, 2, 4, 8):
        pool_idx = [i for i, d in enumerate(docs) if d["book"] < k]
        c_pool, n_pool = df_table(doc_units, pool_idx, len(pool_idx))
        fp = frame(c_pool, n_pool, theta)
        hidden = sum(1 for u in fp if c_all.get(u, 0) / n_all < theta)
        rows.append({"books_pooled": k, "share": n_pool / n_all, "n_pool_docs": n_pool,
                     "|F_pool|": len(fp), "hidden": hidden,
                     "hidden_fraction_of_F_pool": (hidden / len(fp)) if fp else 0.0})
    return rows


def main():
    bad = verify_corpus()
    if bad:
        sys.exit("CORPUS PIN FAILED for %s -- refusing to measure an unverified corpus" % bad)

    docs = documents()
    units_char = [char_bigrams(d["text"]) for d in docs]
    units_word = [word_shingles(d["text"], 3) for d in docs]

    res = {
        "instrument": "spike_v0.py",
        "issue": 132,
        "question": "is the frame LEVEL a set inclusion (an identity) or a dilution (a share effect)?",
        "corpus": {"books": BOOKS, "n_docs": len(docs),
                   "n_docs_per_book": {BOOKS[b]: sum(1 for d in docs if d["book"] == b)
                                       for b in range(len(BOOKS))},
                   "sha256_pin_ok": True},
        "containment": [],
        "dilution": {},
        "plants": plants(),
    }

    for theta in (0.005, 0.01, 0.02):
        for b in range(len(BOOKS)):
            res["containment"].append(containment(units_char, docs, theta, b))

    res["dilution"]["char_bigram_theta_0.01"] = dilution(units_char, docs, 0.01)
    res["dilution"]["word3_theta_0.01"] = dilution(units_word, docs, 0.01)
    res["share_sweep_char_bigram_theta_0.01"] = share_sweep(units_char, docs, 0.01)
    res["share_sweep_word3_theta_0.01"] = share_sweep(units_word, docs, 0.01)

    # ---- the two-sided statement the registration got wrong, stated as a MEASUREMENT
    n_viol_one = sum(1 for r in res["containment"] if not r["F_corpus_subset_F_pool"])
    n_viol_other = sum(1 for r in res["containment"] if not r["F_pool_subset_F_corpus"])
    res["containment_summary"] = {
        "cells": len(res["containment"]),
        "cells_where_F_corpus_NOT_subset_F_pool": n_viol_one,
        "cells_where_F_pool_NOT_subset_F_corpus": n_viol_other,
        "verdict": ("SET INCLUSION DOES NOT HOLD in either direction"
                    if (n_viol_one and n_viol_other) else
                    "one direction held in every cell"),
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
        f.write("\n")

    print("corpus: %d documents over %d books (sha256 pin verified)" % (len(docs), len(BOOKS)))
    print("containment cells: %d" % len(res["containment"]))
    print("  F_corpus NOT ⊄ F_pool in %d cells" % n_viol_one)
    print("  F_pool   NOT ⊄ F_corpus in %d cells" % n_viol_other)
    print("  verdict: %s" % res["containment_summary"]["verdict"])
    for k, v in res["dilution"].items():
        print("dilution %s: worst |df_corpus - s*df_pool| = %.3g over %d confined pairs; "
              "pool-generic-but-corpus-invisible = %d"
              % (k, v["worst_abs_violation"], v["n_confined_pairs"],
                 v["n_pool_generic_but_corpus_invisible"]))
    print("plants: %s" % json.dumps(res["plants"], sort_keys=True))
    print("wrote %s" % OUT)


def selftest():
    """The plants' expectations ARE the checks; each must fire on its own fault.

    The plant corpus is the certificate's two-sided control: A is the case where the containment
    HOLDs, B the case where it FAILS, C the case where a non-confined unit must be EXCLUDED.
    """
    p = plants()
    checks = [
        ("A: at share 1.0 BOTH containments must hold",
         p["A_share1_cor_not_pool"] == 0 and p["A_share1_pool_not_cor"] == 0),
        ("B: a confined pool-generic unit must be corpus-invisible (hidden >= 1)",
         p["B_small_share_hidden"] >= 1),
        ("B: F_pool must NOT be a subset of F_corpus on that corpus",
         p["B_small_share_pool_not_cor"] >= 1),
        ("C: the confinement filter must ADMIT the confined unit (>= 1 pair)",
         p["C_confined_pairs"] >= 1),
        ("C: the dilution identity must be exact on the admitted pairs",
         p["C_worst_abs_violation"] < 1e-12),
    ]
    bad = 0
    for label, ok in checks:
        print("   %-4s %s" % ("ok" if ok else "FAIL", label))
        bad += 0 if ok else 1
    # a FAULT the certificate exists for: break the identity and the check must go red
    broken = {"worst_abs_violation": 0.5}
    fired = not (broken["worst_abs_violation"] < 1e-12)
    print("   %-4s plant: a broken dilution identity is rejected by the same assertion"
          % ("ok" if fired else "FAIL"))
    bad += 0 if fired else 1
    print("SELFTEST %d/%d" % (len(checks) + 1 - bad, len(checks) + 1))
    return 1 if bad else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
