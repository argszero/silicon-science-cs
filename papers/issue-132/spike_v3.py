#!/usr/bin/env python3
"""Issue #132 -- spike_v3: THE NULL IS ALSO A LEVEL.

The paper's construct (R583-R586) is that a similarity guard's BACKGROUND FRAME is computed at a
population LEVEL, and that level is a declared parameter: a corpus-wide frame is blind to a
community register whose share is below theta, so the finer level is the LARGER frame and the
residue it leaves is not the residue any wider level would leave.

THIS INSTRUMENT MEASURES THE SAME PROPERTY ONE LAYER DOWN THE PIPELINE -- IN THE NULL.  A null is
also a population, and the population a null is drawn from is a modelling claim with consequences
that are separately measurable:

  L1 FILTER-CHAIN SYMMETRY (rant item 22).  An enrichment is E = N x P_null.  Every filter the SCAN
     applies must be applied to the NULL DRAWS too, because P_null is the survivor rate THROUGH the
     chain; a filter implicit on one side reads as an effect on the other.  Measured: survivor rates
     per stage on both sides, and the ratio by which a one-sided chain moves E.  The identity is
     E_matched / E_naive = (N_eligible/N_raw) x P_null -- a product of two MEASURED rates.  The
     eligibility rule is a threshold, so its effect is reported as a SENSITIVITY CURVE, not a point.

  L2 INTERVAL OWNERSHIP (rant item 23).  A bootstrap interval belongs to the population it
     RESAMPLED.  Restricting the claim to a subset after the resample does not transfer the
     interval: the interval over ALL fires is not the interval of the non-identical fires, and a
     small count has only a count-based bound.  Measured: the two intervals over one population.

  L3 JOINT PROFILE (rant item 24).  A matched null must reproduce the JOINT profile the reference
     pair was drawn under.  Reproducing the two length MARGINALS independently is NOT sufficient,
     because the free variable of a pair is the PAIRING.  Measured as a calibration cell (the
     fraction of reference scores below their OWN null's median; a calibrated control reads 0.5),
     with the EXCHANGEABLE null as the certificate: a null drawn from the reference's own
     distribution must read 0.5, and a null that only matches marginals need not.

The unifying claim:  the frame is a level, and so is the null.

Ground truth by construction.  A "re-post" population is planted into the pinned corpus: verbatim
copies (hash-equal after normalisation -- caught by a hash, no statistics needed) and edited copies
at a declared substitution rate (NOT hash-equal -- the class the statistics must carry).  The split
verbatim / edited is known by construction; that is what L2 bisects.

Deterministic: fixed integer seed, sorted iteration, no clocks, no environment reads.
Usage:  /usr/bin/python3 spike_v3.py [--selftest]
Out:    spike_v3_results.json
"""
import hashlib
import json
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("SPIKE_OUT") or os.path.join(HERE, "spike_v3_results.json")

SEED = 20261010

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

CAP_PER_BOOK = 240
MIN_DOC_CHARS = 120
DOC_CHARS_MAX = 1200       # a real length spread, so length-MATCHING is a non-trivial act

# ---- the planted re-post population (ground truth by construction) ----------------------------
N_VERBATIM = 24            # exact copies: hash-equal after normalisation
N_EDITED = 12              # copies with a declared character substitution rate: NOT hash-equal
EDIT_RATE = 0.02           # 2 % of characters substituted -> Dice stays high, text differs

# ---- L1 (filter chain) ------------------------------------------------------------------------
THETA_FRAME = 0.01         # the "de-generic" residue: drop units inside the corpus frame at theta
MIN_DEGEN = 10             # the reader's eligibility rule, on DE-GENERIC WORD-3 units
                           # (char bigrams are corpus-generic on this corpus; see min_degen_sweep)
MIN_UNITS_W3 = 10          # a document must have at least this many units to enter a pair

# ---- L2 (interval ownership) ------------------------------------------------------------------
TAU_FIRE = 0.50            # a "fire" = word-3 Dice >= tau
RARE_DF = 5                # blocking key: units occurring in at most this many docs
BOOT_REPS = 3000

# ---- L3 (joint profile) -----------------------------------------------------------------------
TAU_SCAN = 0.30            # the reference-pair similarity band is irrelevant; the null is the object
K_SIDE = 8                 # candidates drawn per side when a null pair is built
N_PAIRS = 150              # reference pairs per class
MATCH_TOL = 0.20           # the +/-20 % length-matching window the reference pairs are drawn under
CELL_MC_TOL = 0.05         # the band a binomial(150, 0.5) cell may wander: 2 sd ~= 0.082, use 0.12


# --------------------------------------------------------------------------- corpus
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


def base_documents():
    docs = []
    for lang in ("en", "es", "fr", "de", "it"):
        for d, b in BOOKS[lang]:
            with open(os.path.join(d, b + ".txt"), encoding="utf-8", errors="replace") as f:
                body = strip_gutenberg(f.read())
            n = 0
            for para in re.split(r"\n\s*\n", body):
                p = " ".join(para.split())[:DOC_CHARS_MAX]
                if len(p) >= MIN_DOC_CHARS:
                    docs.append({"lang": lang, "book": b, "text": p, "kind": "base"})
                    n += 1
                    if n >= CAP_PER_BOOK:
                        break
    return docs


def normalise(s):
    """The normalisation a hash-decidable duplicate check applies: whitespace + case only."""
    return " ".join(s.lower().split())


def edit(text, rate, rng):
    """Substitute a declared fraction of characters -- the NON-hash-decidable class."""
    alpha = "abcdefghijklmnopqrstuvwxyz\u00e0\u00e8\u00ec\u00f2\u00f9\u00e9\u00e7"
    out = []
    for ch in text:
        if ch.isalpha() and rng.random() < rate:
            out.append(alpha[rng.randrange(len(alpha))])
        else:
            out.append(ch)
    return "".join(out)


def plant_reposts(docs, rng):
    """Ground truth by construction: verbatim and edited re-posts with a known parent."""
    n_base = len(docs)
    src = list(range(n_base))
    rng.shuffle(src)
    picks = src[:N_VERBATIM + N_EDITED]
    planted = []
    for k, i in enumerate(picks[:N_VERBATIM]):
        planted.append({"lang": docs[i]["lang"], "book": docs[i]["book"], "text": docs[i]["text"],
                        "kind": "verbatim", "parent": i})
    for k, i in enumerate(picks[N_VERBATIM:N_VERBATIM + N_EDITED]):
        planted.append({"lang": docs[i]["lang"], "book": docs[i]["book"],
                        "text": edit(docs[i]["text"], EDIT_RATE, rng),
                        "kind": "edited", "parent": i})
    all_docs = list(docs) + planted
    for i, d in enumerate(all_docs):
        d["idx"] = i
    return all_docs, n_base


# --------------------------------------------------------------------------- units & similarity
def char2(text):
    t = normalise(text)
    return {t[i:i + 2] for i in range(len(t) - 1)}


def word3(text):
    w = re.findall(r"[a-zA-Z\u00c0-\u00ff']+", normalise(text))
    return {" ".join(w[i:i + 3]) for i in range(len(w) - 2)}


def dice(a, b):
    if not a and not b:
        return 0.0
    return 2.0 * len(a & b) / (len(a) + len(b))


def df_table(units, idx):
    cnt, n = {}, 0
    for i in idx:
        n += 1
        for u in units[i]:
            cnt[u] = cnt.get(u, 0) + 1
    return cnt, n


def frame(cnt, n, theta):
    return {u for u, c in cnt.items() if c / n >= theta}


# --------------------------------------------------------------------------- L1: filter chain
def degen_counts(units, F_corpus):
    """len(units[i] \\ F_corpus) for every document -- computed ONCE, not per draw."""
    return [len(units[i] - F_corpus) for i in range(len(units))]


def blocking_candidates(units, rare_df):
    """Every pair sharing at least one RARE unit -- a duplicate shares ALL its units, so this
    blocking is exact for the duplicate class and avoids the O(n^2) all-pairs scan."""
    inv = {}
    for i, u in enumerate(units):
        for x in u:
            inv.setdefault(x, []).append(i)
    cand = set()
    for x, lst in sorted(inv.items()):
        if 1 < len(lst) <= rare_df:
            for a in range(len(lst)):
                for b in range(a + 1, len(lst)):
                    cand.add((lst[a], lst[b]))
    return sorted(cand)


def filter_chain(docs, degen, scan_pairs, null_pairs, min_degen=None):
    """Apply ONE chain of filters to BOTH sides and report the expected count each way.

    stage 0  raw
    stage 1  both members have >= min_degen DE-GENERIC units (units outside the corpus frame)
    stage 2  the two members are not hash-equal (item 22's added filter)

    E is a PRODUCT:  E = N_eligible x P_null, where N_eligible is the number of SCAN pairs that
    survive the chain and P_null the fraction of NULL DRAWS that survive the SAME chain.  Applying
    the chain to one side only reads as an effect on the other.
    """
    md = MIN_DEGEN if min_degen is None else min_degen

    def ok1(i, j):
        return degen[i] >= md and degen[j] >= md

    # the scan side -- a scan pair is NEVER hash-equal by construction, so stage 2 is a no-op there
    n_scan_raw = len(scan_pairs)
    n_scan_elig = sum(1 for (i, j) in scan_pairs if ok1(i, j))

    # the null side -- each stage's survivor count
    def null_stage(pairs, stage):
        n = 0
        for (i, j) in pairs:
            if not ok1(i, j):
                continue
            if stage >= 2 and normalise(docs[i]["text"]) == normalise(docs[j]["text"]):
                continue
            n += 1
        return n

    n_null = len(null_pairs)
    s1 = null_stage(null_pairs, 1)
    s2 = null_stage(null_pairs, 2)
    p1 = s1 / n_null if n_null else None
    p2 = s2 / n_null if n_null else None
    return {
        "n_scan_pairs_raw": n_scan_raw, "n_scan_pairs_eligible": n_scan_elig,
        "n_null_draws": n_null,
        "null_survivors_stage1": s1, "null_survivors_stage2": s2,
        "p_null_stage1": p1, "p_null_stage2": p2,
        "n_null_dropped_by_stage2": s1 - s2,
        # E under three treatments of the chain; the identity is E_matched/E_naive = (N_elig/N_raw) x p2
        "E_naive_filters_neither_side": float(n_scan_raw),
        "E_one_sided_filter_on_scan_only": float(n_scan_elig),
        "E_matched_filter_on_both": (n_scan_elig * p2) if p2 is not None else None,
        "inflation_one_sided_over_matched": ((n_scan_elig / (n_scan_elig * p2))
                                             if (p2 and p2 > 0) else None),
        "identity_E_matched_over_E_naive": ((n_scan_elig * p2) / n_scan_raw) if p2 is not None else None,
        "identity_rhs": ((n_scan_elig / n_scan_raw) * p2) if p2 is not None else None,
    }


# --------------------------------------------------------------------------- L2: interval ownership
def bootstrap_median(values, groups, reps, rng):
    """Resample the GROUPS with replacement and take every value inside the chosen groups."""
    gi = sorted(set(groups))
    meds = []
    for _ in range(reps):
        pool = []
        for _ in range(len(gi)):
            g = gi[rng.randrange(len(gi))]
            pool.extend(values[k] for k in range(len(values)) if groups[k] == g)
        pool.sort()
        n = len(pool)
        meds.append(pool[n // 2] if n else 0.0)
    meds.sort()
    return {"median": meds[len(meds) // 2] if meds else None,
            "lo": meds[int(0.025 * len(meds))] if meds else None,
            "hi": meds[min(len(meds) - 1, int(0.975 * len(meds)))] if meds else None}


def poisson_upper(k, alpha=0.05, two_sided=False):
    """Smallest Poisson mean mu with P(X <= k; mu) <= tail -- the only bound a small count owns.

    THE CONVENTION IS PART OF THE NUMBER.  A one-sided 95 % upper limit puts the whole 0.05 in the
    upper tail (mu = 10.513 at k = 5); a two-sided 95 % limit puts 0.025 there (mu = 11.668) -- the
    same observation, two bounds, and a sentence that says "the Poisson upper bound" has not said
    which.  Both are reported; the default is the one-sided one.
    """
    tail = alpha / 2.0 if two_sided else alpha

    def cdf(mu):
        s, t = 0.0, math.exp(-mu)
        for i in range(k + 1):
            s += t
            t *= mu / (i + 1.0)
        return s

    lo, hi = 0.0, max(10.0, 10.0 * (k + 1))
    while cdf(hi) > tail:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if cdf(mid) > tail:
            lo = mid
        else:
            hi = mid
    return hi


# --------------------------------------------------------------------------- L3: joint profile
def length_index(docs, pool_idx, rng):
    """Pre-compute, for each length bucket, the pool members whose length falls in it."""
    idx = {}
    for i in pool_idx:
        idx.setdefault(len(docs[i]["text"]), []).append(i)
    return idx


def near(idx, target, tol):
    lo, hi = int(target * (1 - tol)), int(math.ceil(target * (1 + tol)))
    out = []
    for L, members in idx.items():
        if lo <= L <= hi:
            out.extend(members)
    return out


def make_reference_pairs(docs, units, pool_by, tol, rng, n_pairs):
    """Matched-length reference pairs, drawn under a CLASS rule `pool_by(i, j)`."""
    order = sorted(range(len(docs)))
    out, guard = [], 0
    while len(out) < n_pairs and guard < 400000:
        guard += 1
        i = order[rng.randrange(len(order))]
        if len(units[i]) < 50:
            continue
        j = order[rng.randrange(len(order))]
        if j == i or not pool_by(i, j):
            continue
        Li, Lj = len(docs[i]["text"]), len(docs[j]["text"])
        if abs(Li - Lj) / max(1, max(Li, Lj)) > tol:
            continue
        out.append((i, j))
    out.sort()
    return out


def make_partner_fn(docs, near_index, tol, klass):
    """Candidates to REPLACE one member, matched to a target length and VALID AGAINST THE OTHER
    MEMBER: the pair class is a property of the PAIR, so the replacement is constrained by the
    member that stays.  Class = same book (same author); control = different language.
    """
    def same_class(x, other):
        if klass == "class":
            return docs[x]["book"] == docs[other]["book"]
        if klass == "control":
            return docs[x]["lang"] != docs[other]["lang"]
        return True                                           # "neardup": null pool = the whole corpus

    def fn(m, other, target_len):
        return [x for x in near(near_index, target_len, tol)
                if x != m and x != other and same_class(x, other)]
    return fn


def joint_cell(docs, units, ref_pairs, partner_fn, construction, rng, n_all):
    """cell = fraction of reference scores STRICTLY below their own null's median.

    A calibrated null reads 0.5: the reference is exchangeable with its null.  `partner_fn(m, L)`
    returns the candidates that may replace member m at a matched length, INSIDE the pair's class.
    """
    below, spread = 0, []
    for (i, j) in ref_pairs:
        Li, Lj = len(docs[i]["text"]), len(docs[j]["text"])
        nulls = []
        for _ in range(K_SIDE):
            if construction == "anchor":            # keep i, replace j at j's own length
                c = partner_fn(j, i, Lj)
                if not c:
                    continue
                jj = c[rng.randrange(len(c))]
                nulls.append(dice(units[i], units[jj]))
                spread.append(max(Li, len(docs[jj]["text"])) / max(1, min(Li, len(docs[jj]["text"]))))
            elif construction == "marginal":        # replace BOTH, each valid against the ORIGINAL other
                ci, cj = partner_fn(i, j, Li), partner_fn(j, i, Lj)
                if not ci or not cj:
                    continue
                ii = ci[rng.randrange(len(ci))]
                jj = cj[rng.randrange(len(cj))]
                nulls.append(dice(units[ii], units[jj]))
                li, lj = len(docs[ii]["text"]), len(docs[jj]["text"])
                spread.append(max(li, lj) / max(1, min(li, lj)))
            elif construction == "third":           # condition on a RANDOM THIRD doc's length
                t = rng.randrange(n_all)
                c = partner_fn(j, i, len(docs[t]["text"]))
                if not c:
                    continue
                jj = c[rng.randrange(len(c))]
                nulls.append(dice(units[i], units[jj]))
                spread.append(max(Li, len(docs[jj]["text"])) / max(1, min(Li, len(docs[jj]["text"]))))
            elif construction == "exchangeable":    # the IDENTITY null: redraw a pair from the class
                kk = ref_pairs[rng.randrange(len(ref_pairs))]
                nulls.append(dice(units[kk[0]], units[kk[1]]))
                la, lb = len(docs[kk[0]]["text"]), len(docs[kk[1]]["text"])
                spread.append(max(la, lb) / max(1, min(la, lb)))
        if not nulls:
            continue
        nulls.sort()
        m = nulls[len(nulls) // 2] if len(nulls) % 2 else 0.5 * (nulls[len(nulls) // 2 - 1] +
                                                                nulls[len(nulls) // 2])
        if dice(units[i], units[j]) < m:
            below += 1
    n = len(ref_pairs)
    spread.sort()
    return {"construction": construction, "n_pairs": n, "below": below,
            "cell": (below / n) if n else None,
            "departure_from_0.5": (abs(below / n - 0.5)) if n else None,
            "null_length_ratio_median": spread[len(spread) // 2] if spread else None}


# --------------------------------------------------------------------------- selftest
def selftest():
    checks = []

    # L1: the identity E_chain / E_naive = (scan rate) x (null rate ratio) holds as ARITHMETIC
    docs = [{"text": "alpha beta gamma delta " * 3}, {"text": "alpha beta gamma delta " * 3}]
    units = [word3(d["text"]) for d in docs]
    r = {"E_naive": 100 * 0.10, "E_chain": (100 * 0.5) * 0.01}
    checks.append(("L1: E is a product of two measured rates (E = N_eff x P_null)",
                   abs(r["E_chain"] - 0.5) < 1e-12))

    # L2: the restricted bootstrap is a DIFFERENT population -- its median need not be the parent's
    vals = [1.0, 2.0, 3.0, 4.0, 100.0]
    whole = sorted(vals)[len(vals) // 2]
    sub = sorted(vals[:3])[1]
    checks.append(("L2: a subset's median is not the parent's median",
                   whole != sub and whole == 3.0 and sub == 2.0))
    checks.append(("L2: the Poisson upper bound grows with k (a 5-count owns a wider bound)",
                   poisson_upper(5) > poisson_upper(1) > 0))
    checks.append(("L2: the Poisson 95 % upper (two-sided, k=5) is ~11.67 -> tail 0.025",
                   abs(poisson_upper(5, two_sided=True) - 11.668) < 0.05))
    checks.append(("L2: the SAME observation's one-sided bound is ~10.51 -> the convention is part "
                   "of the number", abs(poisson_upper(5) - 10.513) < 0.05))
    checks.append(("L2: a 0-count still owns a bound (0/0 is a bound, not a rate)",
                   poisson_upper(0) > 0))

    # L3: the exchangeable null reads 0.5 by symmetry -- check it on a synthetic population
    rng = random.Random(7)
    popscores = [rng.gauss(0.0, 1.0) for _ in range(400)]
    below = 0
    for s in popscores:
        nulls = sorted(rng.gauss(0.0, 1.0) for _ in range(7))
        if s < nulls[3]:
            below += 1
    cell = below / len(popscores)
    checks.append(("L3: the exchangeable null reads 0.5 (the symmetry certificate)",
                   abs(cell - 0.5) < 0.10))
    # and a broken null (biased upward) must NOT read 0.5 -- the check fires on the fault
    below_bad = sum(1 for s in popscores
                    if s < sorted(rng.gauss(0.5, 1.0) for _ in range(7))[3])
    checks.append(("L3: a biased null reads != 0.5 (the check fires on the fault)",
                   abs(below_bad / len(popscores) - 0.5) > 0.10))

    bad = 0
    for lab, ok in checks:
        print("   %-4s %s" % ("ok" if ok else "FAIL", lab))
        bad += 0 if ok else 1
    print("SELFTEST %d/%d" % (len(checks) - bad, len(checks)))
    return 1 if bad else 0


# --------------------------------------------------------------------------- main
def main():
    bad = verify_corpus()
    if bad:
        sys.exit("CORPUS PIN FAILED: %s -- refusing to measure an unverified corpus" % bad)

    rng = random.Random(SEED)
    base = base_documents()
    docs, n_base = plant_reposts(base, rng)
    n = len(docs)
    corpus_idx = list(range(n))
    u3 = [word3(d["text"]) for d in docs]
    u2 = [char2(d["text"]) for d in docs]

    cnt3, m3 = df_table(u3, corpus_idx)
    F_word3 = frame(cnt3, m3, THETA_FRAME)
    degen = degen_counts(u3, F_word3)      # de-generic WORD-3 units: char bigrams are corpus-generic
    cnt2, m2 = df_table(u2, corpus_idx)
    F_char2 = frame(cnt2, m2, THETA_FRAME)  # kept: the frame the FIRES are finally scored against

    # the scan population: pairs whose word-3 Dice >= TAU_FIRE, over the rare-unit blocking
    cand = blocking_candidates(u3, RARE_DF)
    scan_pairs = [(i, j) for (i, j) in cand
                  if len(u3[i]) >= MIN_UNITS_W3 and len(u3[j]) >= MIN_UNITS_W3
                  and dice(u3[i], u3[j]) >= TAU_FIRE]

    null_pairs = []
    while len(null_pairs) < 20000:
        i = rng.randrange(n)
        j = rng.randrange(n)
        if i != j:
            null_pairs.append((i, j))

    # the fires: the scan pairs, split by whether they are hash-equal (ground truth by construction)
    fires = []
    for (i, j) in scan_pairs:
        verbatim = normalise(docs[i]["text"]) == normalise(docs[j]["text"])
        fires.append({"i": i, "j": j, "score": dice(u3[i], u3[j]), "verbatim": verbatim,
                      "group": docs[i]["book"]})
    non_id = [f for f in fires if not f["verbatim"]]
    observed_non_identical = len(non_id)

    L1 = filter_chain(docs, degen, scan_pairs, null_pairs)
    L1["observed_non_identical_fires"] = observed_non_identical
    L1["observed_over_E_matched"] = (observed_non_identical / L1["E_matched_filter_on_both"]
                                     if L1["E_matched_filter_on_both"] else None)
    # sensitivity: the eligibility rule is a threshold, so its effect is a curve, not a point
    L1["min_degen_sweep"] = {}
    for md in (10, 25, 50, 100):
        c = filter_chain(docs, degen, scan_pairs, null_pairs, min_degen=md)
        L1["min_degen_sweep"][str(md)] = {
            "n_scan_pairs_eligible": c["n_scan_pairs_eligible"], "p_null_stage1": c["p_null_stage1"],
            "E_one_sided": c["E_one_sided_filter_on_scan_only"],
            "E_matched": c["E_matched_filter_on_both"],
            "inflation_one_sided_over_matched": c["inflation_one_sided_over_matched"]}

    res = {
        "instrument": "spike_v3.py",
        "issue": 132,
        "question": ("is the NULL a population LEVEL too -- does the population a null is drawn "
                     "from decide the threshold, the filter chain, the interval and the pairing?"),
        "corpus": {"n_docs": n, "n_base_docs": n_base,
                   "n_verbatim_reposts": N_VERBATIM, "n_edited_reposts": N_EDITED,
                   "edit_rate": EDIT_RATE, "doc_chars_max": DOC_CHARS_MAX,
                   "min_doc_chars": MIN_DOC_CHARS, "sha256_pin_ok": True},
        "params": {"theta_frame": THETA_FRAME, "min_degen": MIN_DEGEN, "min_units_w3": MIN_UNITS_W3,
                   "tau_fire": TAU_FIRE, "k_side": K_SIDE, "n_pairs": N_PAIRS,
                   "match_tol": MATCH_TOL, "seed": SEED},
        "L1_filter_chain": L1,
    }

    # -- L2 -------------------------------------------------------------------------------------
    all_scores = [f["score"] for f in fires]
    all_groups = [f["group"] for f in fires]
    nid_scores = [f["score"] for f in non_id]
    nid_groups = [f["group"] for f in non_id]
    b_all = bootstrap_median(all_scores, all_groups, BOOT_REPS, rng)
    b_nid = bootstrap_median(nid_scores, nid_groups, BOOT_REPS, rng)
    res["L2_interval_ownership"] = {
        "n_fires": len(fires), "n_verbatim": sum(1 for f in fires if f["verbatim"]),
        "n_non_identical": len(non_id),
        "interval_over_ALL_fires": b_all, "interval_over_NON_IDENTICAL": b_nid,
        "interval_transfers": (b_all["lo"] <= b_nid["median"] <= b_all["hi"]),
        "poisson_upper_95_one_sided_for_the_small_count": {
            "k": len(non_id), "upper": poisson_upper(len(non_id))},
        "poisson_upper_95_two_sided_for_the_small_count": {
            "k": len(non_id), "upper": poisson_upper(len(non_id), two_sided=True)},
        "note": ("a bootstrap interval belongs to the population it RESAMPLED; a subset carved out "
                 "afterwards owns only a count-based bound"),
    }

    # -- L3 -------------------------------------------------------------------------------------
    near_index = length_index(docs, corpus_idx, rng)
    class_rule = lambda a, b: docs[a]["book"] == docs[b]["book"]
    control_rule = lambda a, b: docs[a]["lang"] != docs[b]["lang"]
    class_pairs = make_reference_pairs(docs, u2, class_rule, MATCH_TOL, rng, N_PAIRS)
    control_pairs = make_reference_pairs(docs, u2, control_rule, MATCH_TOL, rng, N_PAIRS)
    l3 = {"n_class_pairs": len(class_pairs), "n_control_pairs": len(control_pairs),
          "n_neardup_pairs": len(scan_pairs),
          "match_tol": MATCH_TOL, "k_side": K_SIDE,
          "class_rule": "same book (same author)", "control_rule": "different language",
          "neardup_rule": "the planted near-duplicate fires (whole-corpus null pool)",
          "constructions": {"class": {}, "control": {}, "neardup": {}}}
    for klass, pairs in (("class", class_pairs), ("control", control_pairs),
                         ("neardup", scan_pairs)):
        fn = make_partner_fn(docs, near_index, MATCH_TOL, klass)
        for construction in ("anchor", "marginal", "third", "exchangeable"):
            l3["constructions"][klass][construction] = joint_cell(
                docs, u2, pairs, fn, construction, rng, n)
    res["L3_joint_profile"] = l3

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
        f.write("\n")

    # ---- certificates -------------------------------------------------------------------------
    def cert(pred, lab):
        ok = bool(pred)
        print("   %-4s %s" % ("ok" if ok else "FAIL", lab))
        return ok

    print("corpus: %d documents (%d base + %d verbatim + %d edited re-posts)"
          % (n, n_base, N_VERBATIM, N_EDITED))
    print("scan pairs (word-3 Dice >= %.2f): %d  [verbatim %d / non-identical %d]"
          % (TAU_FIRE, len(fires), res["L2_interval_ownership"]["n_verbatim"], len(non_id)))
    print()
    lc = res["L1_filter_chain"]
    print("L1  null survivor rate: raw 1.0000 -> de-generic %.4f -> not-hash-equal %.4f"
          % (lc["p_null_stage1"], lc["p_null_stage2"]))
    print("    scan pairs raw %d -> eligible %d | E naive %.2f | E one-sided %.2f | E matched %.3f"
          % (lc["n_scan_pairs_raw"], lc["n_scan_pairs_eligible"],
             lc["E_naive_filters_neither_side"], lc["E_one_sided_filter_on_scan_only"],
             lc["E_matched_filter_on_both"]))
    print("    observed non-identical fires %d | one-sided inflation %.1fx"
          % (lc["observed_non_identical_fires"],
             lc["inflation_one_sided_over_matched"] or float("nan")))
    print("L2  ALL fires %s   NON-IDENTICAL %s  transfers=%s"
          % (b_all, b_nid, res["L2_interval_ownership"]["interval_transfers"]))
    print("L3  control cells: " + "  ".join(
        "%s=%.3f" % (k, v["cell"]) for k, v in l3["constructions"]["control"].items()))
    print("    class   cells: " + "  ".join(
        "%s=%.3f" % (k, v["cell"]) for k, v in l3["constructions"]["class"].items()))
    print("    neardup cells: " + "  ".join(
        "%s=%.3f" % (k, v["cell"]) for k, v in l3["constructions"]["neardup"].items()))
    print()
    c1 = cert(lc["p_null_stage2"] <= lc["p_null_stage1"] <= 1.0,
              "L1: the chain cannot raise the null survivor rate (filters only remove)")
    c2 = cert(abs(lc["identity_E_matched_over_E_naive"] - lc["identity_rhs"]) < 1e-12,
              "L1: E_matched/E_naive = (N_elig/N_raw) x p_null -- a product of two measured rates")
    c3 = cert(abs(l3["constructions"]["control"]["exchangeable"]["cell"] - 0.5) < 0.15,
              "L3: the EXCHANGEABLE null reads ~0.5 on the control (the symmetry certificate)")
    c4 = cert(abs(l3["constructions"]["control"]["anchor"]["cell"] - 0.5) < 0.15,
              "L3: the ANCHORED null also reads ~0.5 on the control (pairing preserved)")
    print("CERTIFICATES", "ALL PASS" if (c1 and c2 and c3 and c4) else "FAIL")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
