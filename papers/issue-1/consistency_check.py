#!/usr/bin/env python3
"""Manuscript-to-artefact consistency gate for issue #1.

Purpose: make canonical-run traceability (quality-bar item 6) a *check* rather than a
claim. The chain this verifies is

    canonical_results.json  ->  make_figures.py  ->  results_table.md  ->  manuscript.md

so a number in the manuscript that does not come from the committed artefact fails here.

Usage (from papers/issue-1/, or anywhere - it resolves its own directory):

    python3 consistency_check.py

Exit status 0 = every checked number traces back to the artefact, 1 = at least one does not.
Requires only the Python 3 standard library: it does not import the experiment's dependencies.
"""
import hashlib
import json
import os
import re
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
          near(flat, "zero-interference limit", "%+.3f" % gaps["0.0"]) and
          near(flat, "by up to", "%+.3f" % max(gaps.values(), key=abs)) and
          all("%.3f" % abs(gaps[k]) in body for k in gaps),
          "every interference-level gap appears, anchored to its claim",
          "lead %+.3f, worst %+.3f" % (gaps["0.0"], max(gaps.values(), key=abs)))

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

    check("C09", str(d["n_cells"]) in body and d["n_cells"] == 48 and
                 near(flat, "over", "%d cells" % d["n_cells"]),
          "cell count appears in the body and is 48", d["n_cells"])
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

    n = len(checks)
    ok = sum(1 for c in checks if c)
    print("\nCONSISTENCY %d/%d" % (ok, n))
    print("artefact payload sha256 %s" % art["sha256"][:16])
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
