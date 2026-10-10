#!/usr/bin/env python3
"""#93 R414 -- stage 1's checker: every number `NOTES.md` quotes is re-derived from the artefacts here.

A note that quotes a number owns it.  This script re-derives each quoted reading from `refs_form.json` and
the pools on disk (never from the note), and `--selftest` perturbs a copy in memory to prove the checks can
FAIL -- a check that cannot fail is decoration.

Run:  python3 refs_check.py            (reads the artefacts; exit 0 = every quoted number holds)
      python3 refs_check.py --selftest (also runs the adversarial self-test; prints one line per mutation)
"""
import copy
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(HERE, "NOTES.md")


def derive():
    """Re-derive the readings the note quotes, from the artefacts."""
    form = json.load(io.open(os.path.join(HERE, "refs_form.json"), encoding="utf-8"))
    cl = json.load(io.open(os.path.join(HERE, "refs_classic.json"), encoding="utf-8"))
    r1 = json.load(io.open(os.path.join(HERE, "refs_classic_r1.json"), encoding="utf-8"))
    nf = [v for v in cl["queries"].values() if v["verdict"] == "NOT FOUND"]
    both = sum(1 for v in cl["queries"].values()
               if v["ruleA"]["verdict"] == "match" and v["ruleB"]["verdict"] == "match")
    with open(os.path.join(HERE, "refs_form.json"), "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()[:16]
    return dict(
        pass1_queries=form["measured"]["pass1"]["queries"],
        pass1_rows=form["measured"]["pass1"]["rows"],
        pass1_ids=form["measured"]["pass1"]["unique_ids"],
        pass2_queries=form["measured"]["pass2"]["queries"],
        pass2_rows=form["measured"]["pass2"]["rows"],
        pass2_ids=form["measured"]["pass2"]["unique_ids"],
        union=form["measured"]["arxiv_union"],
        shared=form["measured"]["arxiv_ids_returned_by_more_than_one_query"],
        classic_queries=form["measured"]["classic"]["queries"],
        classic_matched=form["measured"]["classic"]["matched"],
        ruleA=cl["n_ruleA"], ruleB=cl["n_ruleB"], both=both,
        collisions=len(cl["collisions"]),
        controls_ok=sum(1 for c in cl["controls"].values() if c["ok"]), controls=len(cl["controls"]),
        ref_reason_authors=sum(1 for v in nf if "authors" in (v["ruleB_refusal_reason"] or "")),
        ref_reason_nocand=sum(1 for v in nf if "no candidate row" in (v["ruleB_refusal_reason"] or "")),
        ref_reason_noexp=sum(1 for v in nf if "no expectation" in (v["ruleB_refusal_reason"] or "")),
        not_found=len(nf),
        no_candidate_row=sum(1 for v in nf if not any(h["jaccard_main"] >= 0.85 for h in v["hits"])),
        r1_matched=r1["n_matched"], r1_ruleA=r1["n_ruleA"], r1_ruleB=r1["n_ruleB"],
        form_sha=sha,
    )


def checks(d):
    """(name, holds) for every number the note quotes. `d` is the derived reading (or a mutation of it)."""
    return [
        ("pass1 queries 35", d["pass1_queries"] == 35),
        ("pass1 rows 914", d["pass1_rows"] == 914),
        ("pass1 ids 843", d["pass1_ids"] == 843),
        ("pass2 queries 28", d["pass2_queries"] == 28),
        ("pass2 rows 637", d["pass2_rows"] == 637),
        ("pass2 ids 607", d["pass2_ids"] == 607),
        ("arxiv union 1263", d["union"] == 1263),
        ("ids shared by >1 query 213", d["shared"] == 213),
        ("classic queries 64", d["classic_queries"] == 64),
        ("classic matched 50", d["classic_matched"] == 50),
        ("rule A 41", d["ruleA"] == 41),
        ("rule B 13", d["ruleB"] == 13),
        ("A and B overlap 4", d["both"] == 4),
        ("rule B added 9 (A + (B minus overlap) == matched)", (d["ruleA"] + d["ruleB"] - d["both"]) == d["classic_matched"]),
        ("collisions 0", d["collisions"] == 0),
        ("controls 4/4", d["controls_ok"] == 4 and d["controls"] == 4),
        ("refusals: authors 3", d["ref_reason_authors"] == 3),
        ("refusals: no candidate row 6", d["ref_reason_nocand"] == 6),
        ("refusals: no expectation 5", d["ref_reason_noexp"] == 5),
        ("refusals partition the NOT FOUND set", d["ref_reason_authors"] + d["ref_reason_nocand"] + d["ref_reason_noexp"] == d["not_found"]),
        ("NOT FOUND total 14", d["not_found"] == 14),
        ("10 NOT FOUND have no candidate row", d["no_candidate_row"] == 10),
        ("pre-correction 48 (A 41, B 11)", d["r1_matched"] == 48 and d["r1_ruleA"] == 41 and d["r1_ruleB"] == 11),
        ("form sha 39885c8490bf8d2f", d["form_sha"] == "39885c8490bf8d2f"),
    ]


MUTATIONS = [
    ("pass1 rows off by one", "pass1_rows", lambda v: v + 1),
    ("union off by one", "union", lambda v: v - 1),
    ("matched 50 -> 49", "classic_matched", lambda v: v - 1),
    ("rule B 13 -> 11 (the pre-correction reading)", "ruleB", lambda v: 11),
    ("collisions 0 -> 1", "collisions", lambda v: 1),
    ("controls 4 -> 3", "controls_ok", lambda v: 3),
    ("a refusal moved from no-expectation to authors", "ref_reason_authors", lambda v: v + 1),
    ("NOT FOUND 14 -> 13", "not_found", lambda v: v - 1),
    ("form sha replaced", "form_sha", lambda v: "deadbeefdeadbeef"),
]


def main():
    d = derive()
    fails = [n for n, ok in checks(d) if not ok]
    for n, ok in checks(d):
        print("%-58s %s" % (n, "ok" if ok else "FAIL"))
    print("\n%d checks, %d failed" % (len(checks(d)), len(fails)))
    if fails:
        return 1
    if "--selftest" in sys.argv:
        print("\n-- adversarial self-test: each mutation must make at least one check FAIL --")
        caught = 0
        for name, key, fn in MUTATIONS:
            m = copy.deepcopy(d)
            m[key] = fn(m[key])
            hit = [n for n, ok in checks(m) if not ok]
            print("  %-46s -> %s" % (name, ("caught by: " + hit[0]) if hit else "NOT CAUGHT"))
            caught += 1 if hit else 0
        print("  %d/%d mutations caught" % (caught, len(MUTATIONS)))
        return 0 if caught == len(MUTATIONS) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
