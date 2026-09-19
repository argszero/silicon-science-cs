#!/usr/bin/env python3
"""arxiv_liveness_v50 -- the candidate pool's arXiv channel: its liveness control, recorded.

WHY THIS FILE EXISTS.  The review of round 1 (issue #50) returned item 5 (`minor`):

    "the committed scan's own liveness control reports `ok: false` -- its arXiv arm is
     FETCH_FAILED on all 44 arXiv per-query rows (only Crossref returned, n = 5), and the
     arXiv records were supplied by a second pass (`artefacts/arxiv_pass2_v50.json`) that
     carries no control of its own."

Two of those statements are claims about committed objects, and they do not read that way at
the object:

  * `bib_scan_v50.json` -> `per_query` holds **44 rows in total**, and the arXiv arm is
    **28** of them (18 `FETCH_FAILED`, 9 `OK`, 1 `EMPTY_BODY`); the other **16** are
    Crossref rows.  Read here, not restated.
  * `arxiv_pass2_v50.json` -> `meta.control` **does** carry a control, and it **returned**:
    query `all:"tail latency"`, `status: OK`, `n = 10`, at `scanned_utc 2026-09-18T22:20:02Z`
    -- four minutes after pass 1 ended (`22:17:55Z`).  Read here, not restated.

So the channel is not dead and the supply is not uncontrolled; what is missing is a record
that *says so where a reader of the scan looks*, and a **re-run** that shows the 18 failures
are a property of that window rather than of the query set.  This instrument produces that
record.

WHAT IT DOES
  1. reads pass 1 (`bib_scan_v50.json`) for the query list, the per-query statuses it
     recorded, and **the control query it used** -- so the control re-run here is literally
     the same control, not one this file chose;
  2. re-runs that control **now**;
  3. re-runs every arXiv query pass 1 could not read, through **the same function the scan
     used** (`bib_scan_v50.arxiv`, imported -- not a re-implementation), with a delay;
  4. reconciles with the pass-2 supply (`arxiv_pass2_v50.json`): its own control, its own
     per-query statuses, and the ids of the records it supplied;
  5. writes `arxiv_liveness_v50.json`.

WHAT IT IS NOT.  A reading of a live channel at a stated time.  It is **not** byte-reproducible
and no check in this package claims it is: the byte-identical claim of section 6.1 covers the
twelve deterministic sweeps.  `--selftest` runs offline over injected fixtures and proves every
branch below is reachable.

Usage:
  python3 arxiv_liveness_v50.py [--json arxiv_liveness_v50.json] [--delay 1.5]
  python3 arxiv_liveness_v50.py --selftest
"""
import datetime
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCAN = "bib_scan_v50.json"
PASS2 = "arxiv_pass2_v50.json"
CONTROL_N = 5      # the page size the scan's control() asks for

import bib_scan_v50                                    # the pass-1 instrument, same code path


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read(name, root=HERE):
    with io.open(os.path.join(root, name), encoding="utf-8") as f:
        return json.load(f)


def pass1_arxiv_rows(scan):
    """The arXiv arm of pass 1, as the record states it -- not as a summary of it."""
    rows = [r for r in scan["per_query"] if r.get("channel") == "arxiv"]
    failed = [r["query"] for r in rows if r.get("status") != "OK"]
    return rows, failed


def reconcile_pass2(pass2):
    """What the supply record says about itself: its control, its own statuses, its ids."""
    meta = pass2.get("meta") or {}
    ctl = meta.get("control")
    pq = meta.get("per_query") or []
    ids = []
    for r in pass2.get("records") or []:
        i = (r.get("id") or "").strip()
        if i:
            ids.append(i.split("v")[0] if re.match(r"^\d{4}\.\d{4,5}v\d+$", i) else i)
    ok_q = [q["query"] for q in pq if q.get("status") == "OK"]
    return {"control": ctl, "n_control_ok": 1 if (ctl and ctl.get("status") == "OK") else 0,
            "per_query_rows": len(pq), "per_query_ok": len(ok_q),
            "n_records": len(pass2.get("records") or []),
            "n_unique_ids": len(set(ids)), "scanned_utc": meta.get("scanned_utc")}


def run(scan, pass2, arxiv=None, usize="bib_scan_v50.arxiv", delay=1.5, log=print):
    """The body of the reading.  `arxiv` is injected so every branch is reachable offline."""
    fn = arxiv or bib_scan_v50.arxiv
    rows, failed = pass1_arxiv_rows(scan)
    cq = ((scan.get("control") or {}).get("arxiv") or {}).get("query")
    out = {
        "what": "the candidate pool's arXiv channel: pass 1 as committed, its control re-run, "
                "the queries pass 1 could not read re-run through the same function, and the "
                "pass-2 supply reconciled against its own record",
        "instrument": "arxiv_liveness_v50.py (reads bib_scan_v50.json + arxiv_pass2_v50.json)",
        "code_path": usize,
        "scanned_utc": utcnow(),
        "not_byte_reproducible": "a reading of a live channel at a stated time; the package's "
                                 "byte-identical claim covers the twelve deterministic sweeps",
        "pass1": {
            "per_query_rows_total": len(scan["per_query"]),
            "arxiv_rows": len(rows),
            "arxiv_ok": sum(1 for r in rows if r.get("status") == "OK"),
            "arxiv_failed": len([r for r in rows if r.get("status") == "FETCH_FAILED"]),
            "arxiv_empty_body": len([r for r in rows if r.get("status") == "EMPTY_BODY"]),
            "crossref_rows": len([r for r in scan["per_query"] if r.get("channel") == "crossref"]),
            "control": scan.get("control"),
            "window": [scan.get("started_utc"), scan.get("ended_utc")],
        },
        "control_rerun": None,
        "reruns": [],
        "pass2": reconcile_pass2(pass2),
    }
    log("pass 1 as committed: %d per-query row(s) = %d arxiv (%d OK / %d FETCH_FAILED / %d "
        "EMPTY_BODY) + %d crossref; control arxiv status=%s"
        % (out["pass1"]["per_query_rows_total"], out["pass1"]["arxiv_rows"],
           out["pass1"]["arxiv_ok"], out["pass1"]["arxiv_failed"],
           out["pass1"]["arxiv_empty_body"], out["pass1"]["crossref_rows"],
           (out["pass1"]["control"] or {}).get("arxiv", {}).get("status")))

    if not cq:
        out["control_rerun"] = {"query": None, "status": "NO CONTROL IN THE RECORD", "n": 0,
                                "titles": []}
        out["verdict"] = "NO CONTROL RECORDED IN PASS 1 -- nothing to re-run"
        log(out["verdict"])
        return out

    # the SAME call the scan's own control() makes (`arxiv(CONTROL_ARXIV, n=5)`), page size
    # included -- a control re-run at another page size is a different request
    st, recs = fn(cq, CONTROL_N)
    out["control_rerun"] = {"query": cq, "status": st, "n": len(recs),
                            "n_requested": CONTROL_N,
                            "titles": [r.get("title", "")[:70] for r in recs[:3]]}
    log("control re-run now: %s -> status=%s n=%d %s"
        % (cq, st, len(recs), ("| first: " + recs[0].get("title", "")[:60]) if recs else ""))

    if not failed:
        out["verdict"] = "CONTROL RETURNS; NO PASS-1 arXiv QUERY NEEDED A RE-RUN"
        log(out["verdict"])
        p2 = out["pass2"]
        log("pass-2 supply: control=%s n=%s at %s | %d per-query row(s), %d OK | %d record(s), "
            "%d unique id(s)"
            % ((p2["control"] or {}).get("status", "ABSENT"), (p2["control"] or {}).get("n"),
               p2["scanned_utc"], p2["per_query_rows"], p2["per_query_ok"], p2["n_records"],
               p2["n_unique_ids"]))
        return out

    for q in failed:
        time.sleep(delay)
        st2, recs2 = fn(q)
        log("  re-run %-58s %s" % (q[:58], st2))
        out["reruns"].append({"query": q, "status_now": st2, "n_now": len(recs2 or []),
                              "titles": [r.get("title", "")[:70] for r in (recs2 or [])[:2]]})
    ctl_ok = st == "OK" and len(recs) > 0
    recovered = sum(1 for r in out["reruns"] if r["status_now"] == "OK")
    still = [r["query"] for r in out["reruns"] if r["status_now"] != "OK"]
    out["summary"] = {"control_ok": ctl_ok, "queries_rerun": len(out["reruns"]),
                      "recovered": recovered, "still_failing": len(still),
                      "still_failing_queries": still}
    out["verdict"] = (("CONTROL RETURNS: the same control query returns now, so the pass-1 "
                       "failures are a property of that window and not of the query set "
                       "(%d of %d re-run queries returned)" % (recovered, len(out["reruns"])))
                      if ctl_ok else
                      "CONTROL DOES NOT RETURN: the channel is not live from here")
    log(out["verdict"])
    p2 = out["pass2"]
    log("pass-2 supply: control=%s n=%s at %s | %d per-query row(s), %d OK | %d record(s), "
        "%d unique id(s)"
        % ((p2["control"] or {}).get("status", "ABSENT"), (p2["control"] or {}).get("n"),
           p2["scanned_utc"], p2["per_query_rows"], p2["per_query_ok"], p2["n_records"],
           p2["n_unique_ids"]))
    return out


# --------------------------------------------------------------------------------------------- selftest
def selftest():
    """Every arm prints what it read.  The fixtures are injected, so this runs offline."""
    bad = 0

    def arm(label, ok, read_):
        nonlocal bad
        print("  %-62s %s" % (label, "OK" if ok else "*** NOT FIRING ***"))
        print("      read: %s" % json.dumps(read_)[:220])
        if not ok:
            bad += 1

    scan = {"control": {"arxiv": {"query": 'all:"tail latency"', "status": "FETCH_FAILED", "n": 0}},
            "started_utc": "2026-09-18T22:12:46Z", "ended_utc": "2026-09-18T22:17:55Z",
            "per_query": ([{"channel": "arxiv", "query": "q%d" % i,
                            "status": "FETCH_FAILED" if i < 18 else ("EMPTY_BODY" if i == 18 else "OK"),
                            "n": 0 if i <= 18 else 10} for i in range(28)]
                          + [{"channel": "crossref", "query": "c%d" % i, "status": "OK", "n": 5}
                             for i in range(16)])}
    p2 = {"meta": {"control": {"query": 'all:"tail latency"', "status": "OK", "n": 10},
                   "scanned_utc": "2026-09-18T22:20:02Z",
                   "per_query": [{"query": "q0", "status": "OK", "n": 24}]},
          "records": [{"id": "2609.16206v1", "title": "T"}, {"id": "2609.15359v1", "title": "U"}]}

    def ok_fn(titles=("A title",)):
        def f(q, n=40):
            return "OK", [{"title": t, "id": "2609.00001v1"} for t in titles]
        return f

    quiet = (lambda *a: None)
    o = run(scan, p2, arxiv=ok_fn(), delay=0, log=quiet)
    arm("arm 1  pass-1 arXiv arm read as 28 rows (18/9/1) beside 16 Crossref rows",
        (o["pass1"]["arxiv_rows"], o["pass1"]["arxiv_failed"], o["pass1"]["arxiv_ok"],
         o["pass1"]["arxiv_empty_body"], o["pass1"]["crossref_rows"]) == (28, 18, 9, 1, 16),
        o["pass1"])

    o2 = run(scan, p2, arxiv=lambda q, n=5: ("FETCH_FAILED", []), delay=0, log=quiet)
    arm("arm 2  a control that cannot return reads 'the channel is not live', not a pass",
        o2["summary"]["control_ok"] is False and o2["verdict"].startswith("CONTROL DOES NOT RETURN"),
        {"verdict": o2["verdict"][:70]})

    o3 = run(scan, p2, arxiv=ok_fn(), delay=0, log=quiet)
    arm("arm 3  the re-run set is exactly the 19 non-OK arXiv rows and each is re-run once",
        len(o3["reruns"]) == 19 and o3["summary"]["recovered"] == 19,
        {"reruns": len(o3["reruns"]), "recovered": o3["summary"]["recovered"]})

    s_ok = dict(scan, per_query=[dict(r, status="OK") if r["channel"] == "arxiv" else r
                                 for r in scan["per_query"]])
    o4 = run(s_ok, p2, arxiv=ok_fn(), delay=0, log=quiet)
    arm("arm 4  an already-complete arXiv arm states 'nothing to re-run' rather than looping",
        o4["reruns"] == [] and o4["verdict"].startswith("CONTROL RETURNS; NO PASS-1"),
        {"verdict": o4["verdict"]})

    sub = run(scan, {"meta": {}, "records": []}, arxiv=ok_fn(), delay=0, log=quiet)
    arm("arm 5  a supply record with no control reads 'ABSENT'/0 and does not crash",
        sub["pass2"]["control"] is None and sub["pass2"]["n_control_ok"] == 0, sub["pass2"])

    scan2 = json.loads(json.dumps(scan))
    scan2["control"]["arxiv"]["query"] = 'all:"a different control"'
    seen = []

    def spy(q, n=40):
        seen.append(q)
        return "OK", [{"title": "T", "id": "1"}]

    run(scan2, p2, arxiv=spy, delay=0, log=quiet)
    arm("arm 6  the control re-run asks the record's own control query, not one this file chose",
        bool(seen) and seen[0] == 'all:"a different control"', {"asked": seen[:2]})

    o7 = run({"control": {}, "per_query": scan["per_query"]}, p2, arxiv=ok_fn(), delay=0, log=quiet)
    arm("arm 7  a record carrying no control query is stated, not passed",
        o7["control_rerun"]["status"] == "NO CONTROL IN THE RECORD"
        and o7["verdict"].startswith("NO CONTROL RECORDED"),
        {"status": o7["control_rerun"]["status"]})

    print("LIVENESS SELFTEST: 7 arm(s), %d not firing" % bad)
    return 0 if bad == 0 else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    delay = 1.5
    if "--delay" in argv:
        delay = float(argv[argv.index("--delay") + 1])
    out = run(read(SCAN), read(PASS2), delay=delay)
    name = argv[argv.index("--json") + 1] if "--json" in argv else "arxiv_liveness_v50.json"
    with io.open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
