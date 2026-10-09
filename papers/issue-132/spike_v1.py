#!/usr/bin/env python3
"""Issue #132 -- spike_v1: the FRAME LEVEL on the LANGUAGE axis (P1 and P2).

R584 (`spike_v0.py`) established the mechanism on the book/author axis: for a unit confined to a
population of share s, df_corpus(u) = s * df_pool(u) < df_pool(u), so a unit GENERIC INSIDE a
small-share community can sit BELOW a corpus-wide DF cutoff theta.  This instrument carries that
to the axis the registered P2 turns on -- LANGUAGE -- and measures what a corpus-wide frame does.

THE GUARD.
    fire  <=>  sim(a,b) >= tau  AND  |shared(a,b) \\ F_level| >= r.
F_level acts on the RESIDUE GATE ONLY: sim(a,b) is on the raw unit sets, so it is level-independent,
and the two levels differ ONLY in which shared units the frame removes.

THE REGISTER.  A register is a recurring block a community shares (greeting, licence header, template
clause).  Its prevalence inside the POOL is phi; the community is a share s of the corpus, so its
prevalence IN THE CORPUS is s * phi.  Therefore a register with
        s * phi < theta <= phi
is IN the pool frame (the community's own frame removes it) and OUT of the corpus frame (a deployed,
corpus-wide frame keeps it).  That is the whole of P2: the corpus frame is BLIND to a community's own
generic material, and WHICH community it is blind to is set by s.

MEASUREMENT.  The corpus is FIXED (all documents); the pool is ONE community's documents.  Two
communities of different share are compared at identical (phi, theta, tau, stat): Italian
(s~0.18) and English (s~0.43).  For pairs of that community's documents, fire is evaluated at three
levels -- none (control), corpus, pool.  The LEVEL-INDUCED flag count is
        fire_corpus - fire_pool,
flags the deployed frame raises and the community's own frame does not.  Two controls bracket it:
phi = 1.0 (register in every corpus document -> in BOTH frames -> difference exactly 0) and phi
just above the critical prevalence (register in the corpus frame -> difference exactly 0).

Deterministic: fixed seed, sorted iteration, no clocks, no environment reads.
Usage:  /usr/bin/python3 spike_v1.py [--selftest]
Out:    spike_v1_results.json
"""
import hashlib
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("SPIKE_OUT") or os.path.join(HERE, "spike_v1_results.json")   # SPIKE_OUT lets a reproduction run write OUTSIDE the package

CAP = 400                    # documents per book, UNIFORM -- the share is set by COUNT
MIN_DOC_CHARS = 120
DOC_CHARS_MAX = 200    # cap so a register is not diluted by a long paragraph past the sim gate
R_RESIDUE = 10

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
PHIS = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.0)
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


def selftest():
    u = units_of(REGISTER_IT, "word3")
    eu = units_of(REGISTER_EN, "word3")
    checks = [
        ("the Italian register yields at least r word3 units", len(u) >= R_RESIDUE),
        ("the English register yields at least r word3 units", len(eu) >= R_RESIDUE),
        ("word3 of a 2-word string is empty (no spurious units)",
         len(units_of("ciao mondo", "word3")) == 0),
        ("Dice is 1.0 on an identical pair", abs(dice({1, 2, 3}, {1, 2, 3}) - 1.0) < 1e-12),
        ("a frame at theta=1.0 keeps only units in EVERY document",
         frame({"a": 3, "b": 2}, 3, 1.0) == {"a"}),
        ("a unit at the exact cutoff is kept (>=, not >)", frame({"a": 1}, 20, 0.05) == {"a"}),
        ("an empty pair is not similar", dice(set(), set()) == 0.0),
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

    # two communities of DIFFERENT share, both genuine populations of this corpus
    strata = [("minority_it", by_lang["it"], REGISTER_IT),
              ("majority_en", by_lang["en"], REGISTER_EN)]

    res = {
        "instrument": "spike_v1.py", "issue": 132,
        "question": ("does the frame LEVEL decide the flag count, and is the resulting "
                     "misclassification concentrated in the smaller-share community?"),
        "corpus": {"n_docs_total": n_corpus, "cap_per_book": CAP, "min_doc_chars": MIN_DOC_CHARS,
                   "doc_chars_max": DOC_CHARS_MAX,
                   "n_docs_by_lang": {k: len(v) for k, v in sorted(by_lang.items())},
                   "sha256_pin_ok": True},
        "params": {"taus": list(TAUS), "thetas": list(THETAS), "phis": list(PHIS), "r": R_RESIDUE,
                   "pairs_per_cell": PAIRS, "stats": list(STATS)},
        "strata": [{"name": s[0], "n_pool": len(s[1]), "share": len(s[1]) / n_corpus} for s in strata],
        "dilution": [], "critical_share": [], "ladder": [], "templates": [],
    }

    rng = random.Random(20261009)

    for name, pool_idx, reg_text in strata:
        share = len(pool_idx) / n_corpus
        for stat in STATS:
            reg = units_of(reg_text, stat)
            base = [units_of(d["text"], stat) for d in docs]
            c_corpus, _ = df_table(base, corpus_idx)
            c_pool, _ = df_table(base, pool_idx)
            for theta in THETAS:
                Fc, Fp = frame(c_corpus, n_corpus, theta), frame(c_pool, len(pool_idx), theta)
                hidden = Fp - Fc
                res["dilution"].append({
                    "stratum": name, "stat": stat, "theta": theta, "share": share,
                    "critical_prevalence": theta / share,
                    "n_F_pool": len(Fp), "n_hidden": len(hidden),
                    "hidden_fraction": (len(hidden) / len(Fp)) if Fp else 0.0})

            for phi in PHIS:
                if phi >= 1.0:
                    reg_docs = set(corpus_idx)               # whole corpus (control)
                elif phi <= 0.0:
                    reg_docs = set()
                else:
                    n_reg = int(round(phi * len(pool_idx)))
                    reg_docs = set(pool_idx[:n_reg])
                aug = [set(base[i]) for i in range(len(docs))]
                for i in sorted(reg_docs):
                    aug[i] |= reg
                a_corpus, _ = df_table(aug, corpus_idx)
                a_pool, _ = df_table(aug, pool_idx)
                corpus_prev = len(reg_docs) / n_corpus
                pool_prev = len(set(pool_idx) & reg_docs) / len(pool_idx)
                for theta in THETAS:
                    Fc = frame(a_corpus, n_corpus, theta)
                    Fp = frame(a_pool, len(pool_idx), theta)
                    reg_in_corpus = len(reg & Fc)
                    reg_in_pool = len(reg & Fp)
                    res["critical_share"].append({
                        "stratum": name, "stat": stat, "theta": theta, "phi": phi,
                        "corpus_prevalence": corpus_prev, "pool_prevalence": pool_prev,
                        "predicted_hidden_from_corpus": corpus_prev < theta,
                        "observed_hidden_from_corpus": reg_in_corpus == 0,
                        "register_units": len(reg), "reg_in_corpus_frame": reg_in_corpus,
                        "reg_in_pool_frame": reg_in_pool})
                    if phi <= 0.0:
                        pairs = pair_ids(rng, sorted(pool_idx), PAIRS)
                    else:
                        pairs = pair_ids(rng, sorted(set(pool_idx) & reg_docs), PAIRS) \
                            if len(set(pool_idx) & reg_docs) >= 2 else \
                            pair_ids(rng, sorted(pool_idx), PAIRS)
                    for tau in TAUS:
                        fn = fc = fp = simpass = 0
                        for (i, j) in pairs:
                            A, B = aug[i], aug[j]
                            sh = A & B
                            ok_sim = dice(A, B) >= tau
                            simpass += 1 if ok_sim else 0
                            fn += 1 if (ok_sim and len(sh) >= R_RESIDUE) else 0
                            fc += 1 if (ok_sim and len(sh - Fc) >= R_RESIDUE) else 0
                            fp += 1 if (ok_sim and len(sh - Fp) >= R_RESIDUE) else 0
                        res["ladder"].append({
                            "stratum": name, "stat": stat, "share": share, "theta": theta,
                            "phi": phi, "tau": tau, "r": R_RESIDUE, "register_units": len(reg),
                            "corpus_prevalence": corpus_prev, "pool_prevalence": pool_prev,
                            "n_pairs": len(pairs), "sim_gate_pass": simpass,
                            "fire_none": fn, "fire_corpus": fc, "fire_pool": fp,
                            "level_induced": fc - fp,
                            "level_ratio": (fc / fp) if fp else (float("inf") if fc else 0.0)})

    # ---- TEMPLATE CONTROLS: exact repost and 1% edit under the corpus frame ----------------------
    units = [units_of(d["text"], "word3") for d in docs]
    long_i = max(by_lang["en"], key=lambda i: len(units[i]))
    A = units[long_i]
    edited = set(A)
    for u in sorted(A)[:max(1, len(A) // 100)]:
        edited.discard(u)
    for theta in THETAS:
        F = frame(*df_table(units, corpus_idx), theta)
        res["templates"].append({
            "theta": theta, "doc_units": len(A), "dice_exact": dice(A, A),
            "dice_edit1pct": dice(edited, A),
            "exact_fires": dice(A, A) >= 0.5 and len((A & A) - F) >= R_RESIDUE,
            "edit1pct_fires": dice(edited, A) >= 0.5 and len((edited & A) - F) >= R_RESIDUE})

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
        f.write("\n")

    print("corpus: %d docs (%s)" % (n_corpus, res["corpus"]["n_docs_by_lang"]))
    print("strata: " + ", ".join("%s n=%d share=%.3f" % (s["name"], s["n_pool"], s["share"])
                                 for s in res["strata"]))
    print()
    print("level ladder (word3, tau=0.5)  --  none / corpus / pool / induced / ratio")
    for row in res["ladder"]:
        if row["stat"] != "word3" or row["tau"] != 0.5 or row["theta"] != 0.05:
            continue
        print("  %-11s phi=%.2f  regprev=%.3f/%-.3f  | %3d %4d %4d %5d %6s"
              % (row["stratum"], row["phi"], row["pool_prevalence"], row["corpus_prevalence"],
                 row["fire_none"], row["fire_corpus"], row["fire_pool"], row["level_induced"],
                 ("inf" if row["level_ratio"] == float("inf") else "%.2f" % row["level_ratio"])))
    print()
    cs = [c for c in res["critical_share"] if c["stat"] == "word3"]
    agree = sum(1 for c in cs if c["predicted_hidden_from_corpus"] == c["observed_hidden_from_corpus"])
    print("critical-share certificate (word3): corpus_prevalence < theta  <=>  register hidden "
          "from the corpus frame -- %d/%d cells agree" % (agree, len(cs)))
    c2 = [c for c in res["critical_share"] if c["stat"] == "char2"]
    print("   char2 (NOT language-specific): hidden from the corpus frame in %d/%d cells"
          % (sum(1 for c in c2 if c["observed_hidden_from_corpus"]), len(c2)))
    print()
    tf = sum(1 for t in res["templates"] if t["exact_fires"])
    te = sum(1 for t in res["templates"] if t["edit1pct_fires"])
    print("templates (word3, tau=0.5): exact fires %d/%d, 1%%-edit fires %d/%d"
          % (tf, len(res["templates"]), te, len(res["templates"])))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
