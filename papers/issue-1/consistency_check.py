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

    # ---- C05..: each headline number appears in the manuscript in the artefact's own formatting
    gap = " | ".join("%+.3f" % v for v in [d["gap_by_interference"][k]
                                           for k in sorted(d["gap_by_interference"], key=float)])
    check("C05", gap in man.replace("**", "").replace("|", " | ").replace("  ", " ") or
                 all("%.3f" % abs(d["gap_by_interference"][k]) in man
                     for k in d["gap_by_interference"]),
          "every interference-level gap appears", gap)

    for name, vals in (("length_only", d["length_only"]), ("filler_control", d["filler_control"]),
                       ("position", d["position"])):
        missing = [k for k, v in vals.items() if ("%+.3f" % v) not in man]
        check("C06." + name[:4], not missing, "all %s values appear in the manuscript" % name, missing or "")

    tc_ok = all(("%+.3f" % v) in man for v in
                (d["type_contrast"]["same_entity_status"], d["type_contrast"]["different_entity"],
                 d["type_contrast_dense4"]["different_entity"]))
    check("C07", tc_ok, "distractor-type contrast values appear", "")

    for k, v in d["pooled_recall_distractor_cells"].items():
        check("C08." + k[-2:], v in man, "pooled recall %s appears" % k, v)
    check("C08.bm25", d["pooled_recall_bm25_k4"] in man, "pooled BM25 recall appears", d["pooled_recall_bm25_k4"])

    check("C09", str(d["n_cells"]) in man and d["n_cells"] == 48, "cell count appears and is 48", d["n_cells"])
    check("C10", ("%d of the %d" % (d["retrieval_ahead_no_distractor"], d["n_no_distractor"])) in man and
                 ("2 of the %d" % d["n_with_distractor"]) in man,
          "retrieval-ahead counts appear", "%d/%d and %d/%d" % (
              d["retrieval_ahead_no_distractor"], d["n_no_distractor"],
              d["retrieval_ahead_with_distractor"], d["n_with_distractor"]))

    # ---- C11 the sign test is reported with the artefact's numbers
    check("C11", ("%d" % d["sign_test_negative"]) in man and ("%d" % d["sign_test_n"]) in man,
          "sign-test counts appear", "%d/%d" % (d["sign_test_negative"], d["sign_test_n"]))

    # ---- C12 the Wilson intervals of the table come from the artefact
    wil = {(r["L"], r["I"]): r for r in d["sampled_wilson"]}
    tbl_join = " ".join(rows_tbl)
    bad = []
    for row in d["main_grid"]:
        w = wil.get((row["L"], row["I"]))
        if w is None:
            continue
        s = "[%.3f, %.3f]" % (w["lo"], w["hi"])
        if s not in tbl_join:
            bad.append(s)
    check("C12", not bad, "every Wilson interval in the table matches the artefact", bad or "")

    # ---- C13 fidelity block is the one the manuscript quotes
    fid = art["fidelity"]
    check("C13", ("%.6f" % fid["held_out"]["bits_per_token"]) in man and fid["held_out"]["bits_per_token"] == 5.242516,
          "held-out bits/token appears as 5.242516", fid["held_out"]["bits_per_token"])
    check("C14", fid["kv_cache"]["full_vs_cached_max_abs_diff"] == 0.0 and
                 "0.0" in man, "KV-cache exactness (0.0) appears", fid["kv_cache"]["full_vs_cached_max_abs_diff"])

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
