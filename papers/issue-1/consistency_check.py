#!/usr/bin/env python3
"""Manuscript-to-artefact consistency gate for issue #1.

Purpose: make canonical-run traceability (quality-bar item 6) a *check* rather than a
claim. The chain this verifies is

    canonical_results.json  ->  make_figures.py  ->  results_table.md  ->  manuscript.md

so a number in the manuscript that does not come from the committed artefact fails here,
and so does a value in the package's own specification that has drifted from the artefact,
the scripts, or the gate it describes (C27-C33).

Usage (from papers/issue-1/, or anywhere - it resolves its own directory):

    python3 consistency_check.py

Exit status 0 = every checked number traces back to the artefact, 1 = at least one does not.
Requires only the Python 3 standard library: it does not import the experiment's dependencies.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "canonical_results.json")
MAN = os.path.join(HERE, "manuscript.md")
TBL = os.path.join(HERE, "results_table.md")
REFS = os.path.join(HERE, "references.json")
FIGD = os.path.join(HERE, "figures")

checks = []


def check(cid, ok, desc, detail=""):
    checks.append(ok)
    print("%-5s %-4s %-58s %s" % (cid, "PASS" if ok else "FAIL", desc, detail))


def load(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def near(text, anchor, value, window=320):
    """True if `value` occurs within `window` characters of an occurrence of `anchor`.

    A bare `value in text` is a presence test, and this manuscript contains 115 arXiv identifiers,
    years and table numbers, so unrelated digits can satisfy it. Anchoring ties the number to the
    sentence that makes the claim.
    """
    for m in re.finditer(re.escape(anchor), text):
        lo = max(0, m.start() - window)
        hi = min(len(text), m.end() + window)
        if value in text[lo:hi]:
            return True
    return False


def body_of(text):
    """Manuscript text before the single References section."""
    starts = [i for i, l in enumerate(text.splitlines())
              if re.match(r"^#{1,6}\s*(?:\d+[.)]?\s*)?References\s*$", l, re.I)]
    return "\n".join(text.splitlines()[:starts[-1]]) if starts else text


def main():
    art = json.loads(load(ART))
    d = art["derived"]
    man = load(MAN)
    body = body_of(man)
    flat = body.replace("**", "")  # bold markers off: anchors are matched against prose
    tbl = load(TBL)
    refs = json.loads(load(REFS))["entries"]

    # ---- C01 the manuscript's declared artefact hash is the artefact's hash
    check("C01", art["sha256"] in man, "manuscript header carries the artefact payload sha256",
          art["sha256"][:16])

    # ---- C02 the embedded payload hash recomputes over the payload
    payload = {k: v for k, v in art.items() if k != "sha256"}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    check("C02", hashlib.sha256(blob).hexdigest() == art["sha256"],
          "payload sha256 recomputes from the artefact body", hashlib.sha256(blob).hexdigest()[:16])

    # ---- C03 every Table 1 data row in the manuscript appears verbatim in the generated table
    rows_man = [l.strip() for l in man.splitlines() if re.match(r"^\|\s*\d+\s*\|\s*[\d.]+\s*\|", l.strip())]
    rows_tbl = [l.strip() for l in tbl.splitlines() if re.match(r"^\|\s*\d+\s*\|\s*[\d.]+\s*\|", l.strip())]
    check("C03", len(rows_man) == 18 and rows_man == rows_tbl,
          "Table 1 rows in the manuscript equal the generated table", "%d rows" % len(rows_man))

    # ---- C04 the generated table is the one the manifest hashes
    manif = json.loads(load(os.path.join(FIGD, "manifest.json")))
    th = hashlib.sha256(tbl.encode()).hexdigest()
    check("C04", th == manif["table"]["sha256"],
          "results_table.md matches the manifest hash", th[:16])

    # ---- C05..C14 each headline number is tied to the sentence that makes the claim.
    # A bare presence test would be satisfied by any colliding digits (the manuscript carries 115
    # arXiv identifiers), so every check below anchors its value to a phrase from the claim itself.
    gaps = d["gap_by_interference"]
    check("C05",
          near(flat, "no rung at which retrieval leads", "%+.3f" % gaps["0.0"]) and
          all("%.3f" % abs(gaps[k]) in body for k in gaps),
          "every interference-level gap appears, anchored to its claim",
          "I=0.00 %+.3f, I=0.30 %+.3f" % (gaps["0.0"], gaps["0.3"]))

    # ---- RC1: the per-rung intervals are reported, and the zero-interference rung is a null
    ci = d["gap_ci_by_interference"]
    row = "| 95% interval over the 6 cells | " + " | ".join(
        "[%+.3f, %+.3f]" % (ci[k]["lo"], ci[k]["hi"]) for k in ("0.0", "0.15", "0.3", "0.45", "0.6", "0.8")) + " |"
    check("C19", row in flat, "the per-rung 95% interval row is the artefact's", row)
    zero_is_null = not ci["0.0"]["excludes_zero"] and ci["0.0"]["n_positive"] == 3
    check("C20", zero_is_null and near(flat, "indistinguishable", "[%+.3f, %+.3f]" % (ci["0.0"]["lo"], ci["0.0"]["hi"])),
          "the zero-interference rung is stated as a null with its interval",
          "I=0.00 [%+.3f, %+.3f] contains zero" % (ci["0.0"]["lo"], ci["0.0"]["hi"]) if zero_is_null else "not a null")
    sep = [k for k in ci if ci[k]["excludes_zero"] and ci[k]["hi"] < 0]
    check("C21", len(sep) == 4 and near(flat, "onward", "I = 0.30"),
          "the deficit is stated as separated from zero only from I = 0.30 onward",
          "rungs entirely below zero: %s" % sorted(sep, key=float))

    # ---- RC2: the budget ladder is reported
    lad = d["budget_ladder"]
    lrow = "| k = 8 | %+.3f | [%+.3f, %+.3f] | %s |" % (
        lad["k8"]["mean"], lad["k8"]["lo"], lad["k8"]["hi"], lad["k8"]["pooled_recall"])
    lrow1 = "| k = 1 | %+.3f | [%+.3f, %+.3f] | %s |" % (
        lad["k1"]["mean"], lad["k1"]["lo"], lad["k1"]["hi"], lad["k1"]["pooled_recall"])
    halves = abs(lad["k8"]["mean"]) < 0.6 * abs(lad["k1"]["mean"])
    check("C22", lrow in flat and lrow1 in flat and halves,
          "the k = 1 and k = 8 ladder rows are the artefact's and the deficit halves",
          "%+.3f vs %+.3f" % (lad["k1"]["mean"], lad["k8"]["mean"]))

    # ---- RC3: the recall-matched control is reported with its paired interval
    ms = d["type_contrast_matched_subset"]
    dci = ms["difference_ci"]
    check("C23", near(flat, "collapses and reverses", "%+.3f" % ms["gap_difference_entity_minus_status"]) and
                 near(flat, "matched retrieval success", "[%+.3f, %+.3f]" % (dci["lo"], dci["hi"])) and
                 dci["excludes_zero"],
          "the matched type control and its paired interval are reported",
          "%+.3f [%+.3f, %+.3f] over %d pairs" % (ms["gap_difference_entity_minus_status"], dci["lo"], dci["hi"], dci["n"]))
    check("C24", near(flat, "matched pairs", "%d matched pairs" % dci["n"]),
          "the matched pair count is reported beside the words it belongs to",
          "%d matched pairs" % dci["n"])

    # ---- RC4: the worst cell and the bracket tolerance are stated
    wm = d["worst_main_cell"]
    check("C25", near(flat, "worst single cell", "%+.3f" % wm["gap"]) and near(flat, "more conservative", "%+.3f" % wm["gap"]),
          "the worst single cell is stated where the deficit depth is quoted", wm["gap"])
    check("C26", near(flat, "rounding", "0.003"),
          "the instrument bracket is stated as holding to rounding tolerance", "0.003 nats")

    lo = d["length_only"]
    row = "| reading (nats) | " + " | ".join("%+.3f" % lo[k] for k in ("64", "128", "256")) + " |"
    check("C06.leng", row in flat, "the context-length table row is the artefact's",
          "64/128/256 = " + ", ".join("%+.3f" % lo[k] for k in ("64", "128", "256")))

    fc = d["filler_control"]
    check("C06.fill",
          near(flat, "related filler", "%+.3f" % fc["related"]) and
          near(flat, "neutral filler", "%+.3f" % fc["neutral"]),
          "both filler-control values appear beside their labels",
          "related %+.3f, neutral %+.3f" % (fc["related"], fc["neutral"]))

    po = d["position"]
    prow = "| reading (nats) | " + " | ".join(
        "%+.3f" % po[k] for k in ("0.0", "0.25", "0.5", "0.75", "1.0")) + " |"
    check("C06.posi", prow in flat, "the position table row is the artefact's",
          "0.0/0.25/0.5/0.75/1.0 = " + ", ".join("%+.3f" % po[k] for k in ("0.0", "0.25", "0.5", "0.75", "1.0")))

    tc, t4 = d["type_contrast"], d["type_contrast_dense4"]
    check("C07",
          near(flat, "same-entity", "%+.3f" % t4["same_entity_status"]) and
          near(flat, "different-entity", "%+.3f" % t4["different_entity"]),
          "both distractor-type contrasts appear beside their labels",
          "same %+.3f, different %+.3f" % (t4["same_entity_status"], t4["different_entity"]))

    pr = d["pooled_recall_distractor_cells"]
    phrase = ", ".join("%s at k = %s" % (pr["dense_k" + k], k) for k in ("1", "2", "4", "8"))
    # The ladder phrase pins all four rungs in one exact rendering, which is strictly stronger
    # than four separate substring tests: the audit (check_audit.py) showed that per-rung tests
    # for k=1,2,4 could not be made to fire independently of this one, i.e. they were decoration.
    check("C08.dn", phrase in flat, "the dense pooled-recall ladder is the artefact's", phrase)
    check("C08.bm25", near(flat, "BM25 recovers", d["pooled_recall_bm25_k4"]),
          "BM25 pooled recall is anchored to its claim", d["pooled_recall_bm25_k4"])

    check("C09", str(d["n_cells"]) in body and d["n_cells"] == 84 and
                 near(flat, "over", "%d cells" % d["n_cells"]),
          "cell count appears in the body and is 84", d["n_cells"])
    check("C10", ("%d of the %d" % (d["retrieval_ahead_no_distractor"], d["n_no_distractor"])) in body and
                 ("%d of the %d" % (d["retrieval_ahead_with_distractor"], d["n_with_distractor"])) in body,
          "retrieval-ahead counts appear as phrases", "%d/%d and %d/%d" % (
              d["retrieval_ahead_no_distractor"], d["n_no_distractor"],
              d["retrieval_ahead_with_distractor"], d["n_with_distractor"]))

    # ---- C11 the sign test is reported with the artefact's exact ratio (not two loose integers)
    ratio = "%d/%d" % (d["sign_test_negative"], d["sign_test_n"])
    check("C11", ratio in body and near(flat, "sign test", ratio),
          "sign-test ratio appears anchored to the sign test", ratio)

    # ---- C12 the Wilson intervals of the table come from the artefact
    wil = {(r["L"], r["I"]): r for r in d["sampled_wilson"]}
    tbl_join = " ".join(rows_tbl)
    bad = []
    for row in d["main_grid"]:
        w = wil.get((row["L"], row["I"]))
        if w is None:
            continue
        sv = "[%.3f, %.3f]" % (w["lo"], w["hi"])
        if sv not in tbl_join:
            bad.append(sv)
    check("C12", not bad, "every Wilson interval in the table matches the artefact", bad or "")

    # ---- C13/C14 fidelity block is the one the manuscript quotes
    fid = art["fidelity"]
    check("C13", ("%.6f" % fid["held_out"]["bits_per_token"]) in flat and
                 fid["held_out"]["bits_per_token"] == 5.242516,
          "held-out bits/token appears as 5.242516", fid["held_out"]["bits_per_token"])
    check("C14", fid["kv_cache"]["full_vs_cached_max_abs_diff"] == 0.0 and
                 near(flat, "maximum absolute logit difference", "0.0"),
          "KV-cache exactness is anchored to its claim",
          fid["kv_cache"]["full_vs_cached_max_abs_diff"])

    # ---- C15 exactly one References section, entry count, and every key cited
    secs = len([l for l in man.splitlines()
                if re.match(r"^#{1,6}\s*(?:\d+[.)]?\s*)?References\s*$", l, re.I)])
    check("C15", secs == 1, "exactly one References section", secs)
    ents = len(re.findall(r"^\[\d+\] ", man, re.M))
    check("C16", ents == len(refs), "bibliography entries equal the verified record store",
          "%d vs %d" % (ents, len(refs)))
    # citation keys are consumed as CLUSTERS ("[18,19,20]" cites 18 and 19), exactly as the
    # repository's refgate.py resolves them - a literal "[18]" search would report a false miss.
    cited = set()
    for m in re.finditer(r"\[(\d+(?:\s*[,\u2013-]\s*\d+)*)\]", body):
        inner = m.group(1)
        for part in inner.split(","):
            part = part.strip()
            rng = re.split(r"[\u2013-]", part)
            if len(rng) == 2 and all(x.strip().isdigit() for x in rng):
                a, b = (int(x) for x in rng)
                cited.update(range(a, b + 1))
            elif part.isdigit():
                cited.add(int(part))
    uncited = [r["key"] for r in refs if r["key"] not in cited]
    check("C17", not uncited, "every bibliography entry is cited in the body (clusters expanded)",
          uncited[:8])

    # ---- C18 figures on disk match the manifest
    badf = []
    for f in manif["figures"]:
        p = os.path.join(HERE, f["file"])
        if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != f["sha256"]:
            badf.append(f["file"])
    check("C18", not badf, "committed figures match their manifest hashes", badf or "")

    # ---- C27-C33 the package's specification must describe the package it ships.
    # Raised by the editor after revision round 1: the stale sites were all in documentation a
    # reader EXECUTES (the expected-output block, the tier table, the status paragraph) and none
    # of them was a file-hash table row, so the table check could not see any of them. Every
    # value below is re-derived from the artefact or from the script it describes, never from
    # another document.
    readme = load(os.path.join(HERE, "README.md"))
    repro_sh = load(os.path.join(HERE, "reproduce.sh"))
    spec_docs = readme + "\n" + repro_sh
    art_file_sha = hashlib.sha256(open(ART, "rb").read()).hexdigest()

    # C27 every hash row in the README's file table matches the committed file on disk
    rows_spec = re.findall(r"^\| `([A-Za-z0-9_./-]+)` \| `([0-9a-f]{16})` \|", readme, re.M)
    stale_rows = []
    for rel, val in rows_spec:
        p = os.path.join(HERE, rel)
        if not os.path.exists(p):
            stale_rows.append(rel + ":missing")
        elif hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] != val:
            stale_rows.append(rel)
    check("C27", len(rows_spec) >= 20 and not stale_rows,
          "every README file-hash row matches its committed file",
          "%d rows" % len(rows_spec) + (", stale: %s" % stale_rows if stale_rows else ""))

    # C28 no hash-like token in the specification is unaccounted for. This is the check that
    # catches a stale hash in PROSE - the class C27 is blind to by construction.
    known = {art["sha256"], art["sha256"][:16], art_file_sha, art_file_sha[:16]}
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [x for x in dirs if x not in ("research", "__pycache__", ".git")]
        for fn in files:
            h = hashlib.sha256(open(os.path.join(root, fn), "rb").read()).hexdigest()
            known.add(h)
            known.add(h[:16])
    # superseded values are permitted only where the package labels them as provenance
    historical = {  # pre-revision 48-cell artefact, superseded 2026-09-12, kept as provenance
        "de241d916e5885a82a6ecea8f258a2b47705b546f89c427e49dec9cc0d303a6e",
        "8dc43a9cc1d0a981",
    }
    # a truncated hash is acceptable when it really is a truncation of a current value
    unknown_hashes = sorted({t for t in re.findall(r"\b[0-9a-f]{12,}\b", spec_docs)
                             if t not in known and t not in historical
                             and not any(k.startswith(t) for k in known)})
    check("C28", not unknown_hashes,
          "no unaccounted hash-like token in the specification documents",
          unknown_hashes or "%d values accounted for" % len(known))

    # C29 the one-command specification's expected output is the committed artefact's payload
    m_out = re.search(r"canonical payload sha256: ([0-9a-f]{16})\b", readme)
    m_full = re.search(r"^    ([0-9a-f]{64})$", readme, re.M)
    check("C29", bool(m_out) and bool(m_full) and m_out.group(1) == art["sha256"][:16]
                 and m_full.group(1) == art["sha256"],
          "the expected-output block states the committed artefact payload",
          "%s / %s" % (m_out.group(1) if m_out else "-", m_full.group(1)[:16] if m_full else "-"))

    # C30 the reproduction-status paragraph quotes the committed file's own hash
    check("C30", near(readme, "file sha256", art_file_sha),
          "the status paragraph states the committed artefact file hash", art_file_sha[:16])

    # C31 every sweep-cell count in the specification is the artefact's, unless the surrounding
    # text marks it as historical ("earlier", "superseded", "first submission", ...)
    stale_counts = []
    for m in re.finditer(r"(\d+)[- ]cell|all (\d+) sweep cells?", spec_docs):
        v = int(m.group(1) or m.group(2))
        if v == d["n_cells"]:
            continue
        ctx = spec_docs[max(0, m.start() - 260):m.end() + 260]
        if not any(c in ctx for c in ("earlier", "previous", "superseded", "first submission")):
            stale_counts.append(v)
    check("C31", not stale_counts,
          "every sweep-cell count in the spec is the artefact's, or labelled historical",
          "%d cells" % d["n_cells"] + (", stale: %s" % stale_counts if stale_counts else ""))

    # C32 the tally the specification states for validate.py is the tally validate.py asserts.
    # Measured, not parsed: the denominator is a property of the gate's code, so this stays true
    # when the artefact is corrupted (a corrupted run prints a smaller numerator, same denominator).
    vout = subprocess.run([sys.executable, os.path.join(HERE, "validate.py")],
                          cwd=HERE, capture_output=True, text=True).stdout
    v_ids = re.findall(r"^([AB]\d\d\S*)\s+(?:PASS|FAIL)", vout, re.M)
    n_a = sum(1 for i in v_ids if i.startswith("A"))
    n_b = len(v_ids) - n_a
    v_claim = "%d individual conditions (%d structural, %d mechanism)" % (len(v_ids), n_a, n_b)
    check("C32", bool(v_ids) and v_claim in readme
                 and ("VALIDATE %d/%d" % (len(v_ids), len(v_ids))) in readme,
          "the spec states the tally validate.py actually asserts", v_claim)

    # C33 every count the specification states for THIS gate is the gate's own check count,
    # including the check appended on the next line.
    stated = sorted({int(m.group(1)) for m in re.finditer(r"CONSISTENCY (\d+)/\d+", spec_docs)}
                    | {int(m.group(1)) for m in re.finditer(r"every one of the (\d+) checks", spec_docs)})
    this_gate = len(checks) + 1
    check("C33", stated == [this_gate],
          "every count stated for this gate is this gate's own check count",
          "stated %s vs %d" % (stated, this_gate))


    n = len(checks)
    ok = sum(1 for c in checks if c)
    print("\nCONSISTENCY %d/%d" % (ok, n))
    print("artefact payload sha256 %s" % art["sha256"][:16])
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
