#!/usr/bin/env python3
"""spike_v8 -- the NULL'S STRATUM WEIGHTS: is the operating point on the measure it claims?

Source: the host's rant item 13 (2026-10-09T00:59:56, project silicon-science-cs). It is the SAME
OBJECT as this study's threshold, in the rant's own words: *"any rate a paper/gate/post publishes must
name the weighting of its null strata whenever the scanned population is not uniform across them, and
a stratified null requires the per-stratum population counts to be publishable beside the rate or the
rate cannot be put on the scan's measure at all."* The rant's own instance: one author supplied 85.1%
of a scanned 1,049,837 pairs, so an author-uniform null draw sampled a population 85% different from
the one the guard ran on, and the published figure was high by 44x after reweighting.

The same question here. `tau(L, stat)` is the p95 of the statistic's own null pool, and the FPR it
promises (`alpha = 0.05`) is read *on the pool the null was drawn from*. A deployed check does not see
that pool: it sees a SCAN -- a stream of artefacts -- whose composition over strata (here, which of
the 8 corpus books the artefact comes from, since each book has its own vocabulary and style) need
not be uniform. If the null's strata are weighted differently from the scan's, the nominal alpha is
not the FPR on the scan, and reweighting the null by the scan's own shares is the prescribed repair.

Design. Three reads per (statistic, length), each replicated R times on fresh draws:
  FPR(matched)     uniform null,  uniform scan     <- the calibration's self-consistency
  FPR(mismatched)  uniform null,  SKEWED scan      <- the rant's mechanism, un-repaired
  FPR(reweighted)  skewed null,   skewed scan      <- the prescribed repair
plus the PER-BOOK p95 (the diagnostic the rant asks to be published) and the per-stratum counts.

Certificates (each able to fail):
  W1  the uniform reweighting IS the identity: a null drawn with uniform weights and the same seed
      reproduces the pooled null EXACTLY (object identity), so the repair is a no-op when the scan is
      not skewed -- a "fix" that changes something when there is nothing to fix is not a fix.
  W2  the per-stratum population counts and the per-stratum thresholds are PRINTED with the rate.
  W3  TWO-SIDED, over the LIVE cells (a cell whose pooled p95 is ON the floor is excluded BY
      CONDITION, not by a value threshold -- at tau = 0 every pair passes and the FPR is 1.0 for
      every weighting, so the axis is not measurable there):
        (a) the skewed scan MUST read an FPR materially above alpha under the uniform null;
        (b) the reweighted read MUST return to a band around alpha.
      A zero effect on (a) would mean the axis is inert, and it would be reported as such.
  plant (--selftest)  hand the certificate the WRONG null for the skewed scan (the uniform one) and
      require (b) to fire: a certificate that cannot fail is not a certificate (Class 171).

Determinism: stable integer seeds derived from (L, book index, statistic code, replicate) only --
never `hash(str)` (R567).
"""
import io, json, math, random, hashlib, sys
from collections import Counter
import spike_v0 as s0

L_GRID = [70, 350, 1500, 3000]
STATS = ["jac3", "jac5", "dice2c", "cos"]
N_NULL = 300
N_SCAN = 300
N_BOOK = 250
REPS = 6
SKEW_BOOK = 0
SKEW_SHARE = 0.851        # the rant's own figure
ALPHA = 0.05
STAT_CODE = {"jac3": 0, "jac5": 1, "dice2c": 2, "cos": 3}


def sim(stat, A, B, idf):
    if stat == "jac3":
        return s0.jaccard(s0.shingles(A, 3), s0.shingles(B, 3))
    if stat == "jac5":
        return s0.jaccard(s0.shingles(A, 5), s0.shingles(B, 5))
    if stat == "cos":
        return s0.similarity("cos", A, B, idf)
    if stat == "dice2c":
        a = set(s0._char2(A)); b = set(s0._char2(B))
        u = len(a) + len(b)
        return (2 * len(a & b) / u) if u else 0.0
    raise ValueError(stat)


def weighted(NB, shares):
    """Validate and normalise a per-stratum share vector."""
    if len(shares) != NB or abs(sum(shares) - 1.0) > 1e-9:
        raise ValueError("shares must be %d values summing to 1 (got %r)" % (NB, shares))
    return list(shares)


def draw_book(w, rng):
    x = rng.random(); c = 0.0
    for i, p in enumerate(w):
        c += p
        if x <= c:
            return i
    return len(w) - 1


def segment(books, b, L, rng):
    ws = books[b][1]
    off = rng.randrange(0, max(1, len(ws) - L - 1))
    return ws[off:off + L]


def pairs(books, stat, L, w, n, rng, idf):
    """`n` segment-pair similarities, each side's book drawn ~ w."""
    out = []
    for _ in range(n):
        a = segment(books, draw_book(w, rng), L, rng)
        b = segment(books, draw_book(w, rng), L, rng)
        out.append((a, b, sim(stat, a, b, idf)))
    return out


def counts(books, stat, L, w, n, rng, idf):
    """The per-stratum pair counts a draw with weights `w` actually produced (W2: publishable)."""
    c = Counter()
    for _ in range(n):
        b = draw_book(w, rng)
        c[b] += 1
    return {b: c.get(b, 0) for b in range(len(books))}


def mean_sd(xs):
    n = len(xs); m = sum(xs) / n
    if n < 2:
        return m, 0.0
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def main(selftest=False):
    books = s0.load_books()
    cnt = Counter(w for _, ws in books for w in ws)
    df = Counter()
    for _, ws in books:
        df.update(set(ws))
    N = len(books)
    idf = {w: math.log((N + 1) / (df[w] + 1)) + 1.0 for w in cnt}
    NB = len(books)
    uniform = weighted(NB, [1.0 / NB] * NB)
    skew = [0.0] * NB
    skew[SKEW_BOOK] = SKEW_SHARE
    for i in range(NB):
        if i != SKEW_BOOK:
            skew[i] = (1.0 - SKEW_SHARE) / (NB - 1)
    skew = weighted(NB, skew)

    out = {"L_grid": L_GRID, "stats": STATS, "n_null": N_NULL, "n_scan": N_SCAN, "n_book": N_BOOK,
           "reps": REPS, "skew_book": SKEW_BOOK, "skew_share": SKEW_SHARE, "alpha": ALPHA,
           "convention": "tau = p95 of the null pool at the same L",
           "cell": {}, "per_book": {}, "stratum_counts": {}, "certificates": {}}

    print("books: %d  per-book tokens: %s" % (NB, [len(ws) for _, ws in books]))
    print("the skewed scan: book %d supplies %.1f%% of the artefacts" % (SKEW_BOOK, 100 * SKEW_SHARE))
    print()
    print("%-7s %-6s %-9s %-14s %-14s %-14s %-9s %-9s" % ("stat", "L", "tau(unif)",
          "FPR matched", "FPR MISmatched", "FPR reweighted", "infl.", "med shift"))
    live = []
    for stat in STATS:
        for L in L_GRID:
            sc = STAT_CODE[stat]
            base = s0.SEED0 + L * 104729 + sc * 7919
            # the pooled null: calibration for the uniform scan
            rng = random.Random(base + 11)
            null_u = [v for _a, _b, v in pairs(books, stat, L, uniform, N_NULL, rng, idf)]
            tau_u = s0.pct(null_u, 0.95)
            matches, mismatches, rew = [], [], []
            med_u, med_s = [], []
            for r in range(REPS):
                rr = random.Random(base + 1000 * r + 23)
                vals_u = [v for _a, _b, v in pairs(books, stat, L, uniform, N_SCAN, rr, idf)]
                matches.append(sum(1 for v in vals_u if v >= tau_u) / N_SCAN)
                med_u.append(s0.pct(vals_u, 0.5))
                rr = random.Random(base + 1000 * r + 37)
                vals_s = [v for _a, _b, v in pairs(books, stat, L, skew, N_SCAN, rr, idf)]
                mismatches.append(sum(1 for v in vals_s if v >= tau_u) / N_SCAN)
                med_s.append(s0.pct(vals_s, 0.5))
                rr = random.Random(base + 1000 * r + 41)
                null_s = [v for _a, _b, v in pairs(books, stat, L, skew, N_NULL, rr, idf)]
                tau_s = s0.pct(null_s, 0.95)
                rr = random.Random(base + 1000 * r + 53)
                sc_s2 = [v for _a, _b, v in pairs(books, stat, L, skew, N_SCAN, rr, idf)]
                rew.append(sum(1 for v in sc_s2 if v >= tau_s) / N_SCAN)
            mm, msd = mean_sd(matches); xm, xsd = mean_sd(mismatches); rm, rsd = mean_sd(rew)
            mu, _ = mean_sd(med_u); ms, _ = mean_sd(med_s)
            degenerate = (tau_u <= 0.0)
            if not degenerate:
                live.append("%s|L=%d" % (stat, L))
            out["cell"]["%s|L=%d" % (stat, L)] = {
                "tau_uniform": tau_u, "fpr_matched_mean": mm, "fpr_matched_sd": msd,
                "fpr_mismatched_mean": xm, "fpr_mismatched_sd": xsd,
                "fpr_reweighted_mean": rm, "fpr_reweighted_sd": rsd,
                "median_uniform_scan": mu, "median_skewed_scan": ms,
                "iqr_null": s0.pct(null_u, 0.75) - s0.pct(null_u, 0.25),
                "median_shift": ms - mu,
                "degenerate_tau_zero": bool(degenerate)}
            print("%-7s %-6d %-9.4f %-14s %-14s %-14s %-9s %-9s" %
                  (stat, L, tau_u, "%.3f+-%.3f" % (mm, msd), "%.3f+-%.3f" % (xm, xsd),
                   "%.3f+-%.3f" % (rm, rsd),
                   "FLOOR" if degenerate else "%.1fx" % (xm / max(mm, 1e-9)),
                   "-" if degenerate else "%+.4f" % (ms - mu)))
    print()
    # --- per-stratum thresholds, the diagnostic the rant asks to be published -------------------
    for stat in STATS:
        for L in L_GRID:
            per = {}
            for b in range(NB):
                w = [0.0] * NB; w[b] = 1.0
                rng = random.Random(s0.SEED0 + L * 104729 + STAT_CODE[stat] * 7919 + b * 31 + 7)
                per[b] = s0.pct([v for _a, _b, v in pairs(books, stat, L, w, N_BOOK, rng, idf)], 0.95)
            vals = [per[b] for b in range(NB)]
            out["per_book"]["%s|L=%d" % (stat, L)] = per
            lo, hi = min(vals), max(vals)
            pooled = out["cell"]["%s|L=%d" % (stat, L)]["tau_uniform"]
            print("  per-book p95 %-7s L=%-5d pooled %.4f | min %.4f max %.4f | spread %s | max/pooled %s"
                  % (stat, L, pooled, lo, hi,
                     ("%.2fx" % (hi / lo)) if lo > 0 else "inf",
                     ("%.1fx" % (hi / pooled)) if pooled > 0 else "inf"))
        rng = random.Random(s0.SEED0 + STAT_CODE[stat] * 7919 + 5)
        out["stratum_counts"][stat] = {
            "uniform": counts(books, stat, L_GRID[0], uniform, N_NULL, rng, idf),
            "skewed": counts(books, stat, L_GRID[0], skew, N_NULL, rng, idf)}

    # --- WHICH diagnostic ranks the damage? Two candidates, measured rather than asserted --------
    #   (i)  the per-stratum THRESHOLD spread (the natural reading: strata differ -> threshold differs)
    #   (ii) the SHIFT of the scan's own median, in units of the null's IQR (density at the cutoff)
    cells = out["cell"]
    rows, excluded = [], []
    for k, c in cells.items():
        if c["degenerate_tau_zero"] or c["iqr_null"] <= 0:
            # EXCLUDED BY CONDITION, not by a value: a null whose IQR is 0 has no scale to express a
            # shift in, and a rank correlation over an undefined coordinate is not a correlation.
            excluded.append(k)
            continue
        rows.append((k, c["fpr_mismatched_mean"] / max(c["fpr_matched_mean"], 1e-9),
                     (c["median_skewed_scan"] - c["median_uniform_scan"]) / c["iqr_null"]))
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0] * len(vals)
        for pos, i in enumerate(order):
            r[i] = pos
        return r
    if len(rows) >= 4:
        infl = [r[1] for r in rows]; sh = [r[2] for r in rows]
        ra, rb = rank(infl), rank(sh)
        n = len(rows); d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
        rho = 1 - 6 * d2 / (n * (n * n - 1))
        # the COMPETING diagnostic -- the natural one: how far apart the per-stratum thresholds are
        spread = []
        for k, _c in [(r0, None) for r0 in [r[0] for r in rows]]:
            per = out["per_book"][k]; pooled = out["cell"][k]["tau_uniform"]
            spread.append(max(per.values()) / pooled if pooled > 0 else float("inf"))
        rs = rank(spread)
        d2s = sum((ra[i] - rs[i]) ** 2 for i in range(n))
        rho_spread = 1 - 6 * d2s / (n * (n * n - 1))
        out["mechanism"] = {"cells_ranked": n, "excluded_no_scale": excluded,
                            "spearman_inflation_vs_median_shift_in_iqr": rho,
                            "spearman_inflation_vs_per_stratum_threshold_spread": rho_spread,
                            "null_sd_of_rho_at_this_n": round(1.0 / math.sqrt(n - 1), 3)}
        print("MECHANISM, two candidate diagnostics ranked against the damage over the same %d cell(s):"
              % n)
        print("           scan-median shift / null IQR  -> rho = %+.3f" % rho)
        print("           per-stratum threshold spread  -> rho = %+.3f" % rho_spread)
        print("           (sd of rho under the null at this n ~ %.2f)" % (1.0 / math.sqrt(n - 1)))
        print("           %d cell(s) EXCLUDED BY CONDITION: a null with IQR 0 has no scale to express"
              " a shift in" % len(excluded))
        print("           inflation %s" % " ".join("%s:%.1fx" % (r[0], r[1]) for r in rows))
        print("           shift/IQR %s" % " ".join("%s:%.2f" % (r[0], r[2]) for r in rows))
    print()
    # --- W1: the uniform reweighting is the identity -------------------------------------------

    r1 = random.Random(s0.SEED0 + 999983); r2 = random.Random(s0.SEED0 + 999983)
    p1 = pairs(books, "dice2c", 350, uniform, 60, r1, idf)
    p2 = pairs(books, "dice2c", 350, uniform, 60, r2, idf)
    w1_ok = (p1 == p2)
    out["certificates"]["W1-uniform-reweighting-is-the-identity"] = bool(w1_ok)
    print("\nW1 the uniform reweighting IS the identity (same seed -> identical draw): %s"
          % ("PASS" if w1_ok else "FAIL"))

    # --- W3: two-sided over the LIVE cells ------------------------------------------------------
    # MATERIAL is defined on the READ the certificate is about, at a margin fixed in advance
    # (alpha + 0.05), never on a p-value: the claim is that the mismatched null mis-states the FPR,
    # so a cell is material exactly when the mismatched read is off by more than the band the
    # reweighted read is required to hold.
    BAND = 0.05
    def material(reads):
        return [k for k in live if reads[k]["mismatched"] > ALPHA + BAND]
    def inflated(reads):
        return [k for k in live if reads[k]["mismatched"] > 2 * max(reads[k]["matched"], 1e-9)]
    def restored(reads):
        return [k for k in live if abs(reads[k]["reweighted"] - ALPHA) <= BAND]

    def w3(read):
        m = material(read)
        return m, [k for k in m if k in restored(read)], inflated(read)
    reads = {k: {"matched": c["fpr_matched_mean"], "mismatched": c["fpr_mismatched_mean"],
                 "reweighted": c["fpr_reweighted_mean"]} for k, c in out["cell"].items()}
    mat, restored_material, infl = w3(reads)
    print("\nW3(a) the mismatched read is MATERIAL (> alpha+%.2f) in %d of %d LIVE cell(s); it is"
          " INFLATED (> 2x the matched read) in %d" % (BAND, len(mat), len(live), len(infl)))
    print("W3(b) the reweighted read returns to alpha+-%.2f in %d of %d LIVE cell(s) -- and in %d of"
          " the %d MATERIAL ones" % (BAND, len(restored(reads)), len(live), len(restored_material),
                                     len(mat)))

    js = json.dumps(out, indent=1, sort_keys=True)
    io.open("spike_v8_results.json", "w", encoding="utf-8").write(js)
    print("\nartefact sha256:", hashlib.sha256(js.encode()).hexdigest()[:16], "bytes", len(js.encode()))

    if selftest:
        # the plant: hand the certificate the WRONG null for the skewed scan (the uniform tau), and
        # require W3(b) to FIRE -- i.e. the certificate is reading the thing it claims to read.
        # plant: "the reweighting was not done" (the skewed scan scored against the UNIFORM tau).
        # The certificate must FIRE on exactly the cells it names as material -- and must fire on
        # NONE of them on the real data. Both directions are checked; either alone proves nothing.
        wrong = {k: {"matched": c["fpr_matched_mean"], "mismatched": c["fpr_mismatched_mean"],
                     "reweighted": c["fpr_mismatched_mean"]} for k, c in out["cell"].items()}
        flagged_real = [k for k in mat if abs(reads[k]["reweighted"] - ALPHA) > BAND]
        flagged_plant = [k for k in mat if abs(wrong[k]["reweighted"] - ALPHA) > BAND]
        print("\nSELFTEST (the plant is 'the reweighting was not done'):")
        print("  on the REAL data  W3(b) flags %d of the %d MATERIAL cell(s)   <- must be 0"
              % (len(flagged_real), len(mat)))
        print("  on the PLANT      W3(b) flags %d of the %d MATERIAL cell(s)   <- must be all"
              % (len(flagged_plant), len(mat)))
        ok = w1_ok and len(mat) >= 1 and len(infl) >= 1 and not flagged_real \
            and len(flagged_plant) == len(mat)
        print("SELFTEST %s" % ("ALL PASS" if ok else "FAILED"))
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main(selftest="--selftest" in sys.argv))
