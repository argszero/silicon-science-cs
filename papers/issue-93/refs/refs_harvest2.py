#!/usr/bin/env python3
"""#93 R414 -- pass 2 of the arXiv harvest: ONE wide window, NARROW terms, relevance-sorted.

Pass 1 (`refs_harvest.py`) reads two windows with broad terms under the default date sort, which biases
the pool toward whatever was posted most recently.  Pass 2 asks the complementary question: given a wide
window, which works does the index consider *about* these narrow phrases?  Relevance sorting is the whole
point of the pass -- the two passes disagree on purpose, and the union is what selection reads.

WINDOW  W3 submittedDate [2015-01-01, 2026-09-22] (one wide window), sort = relevance

SCAN DATE 2026-09-22      OUTPUT  refs_raw2.json
"""
import io
import json
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refs_harvest import fetch, arxiv_query   # noqa: E402  -- one HTTP form, not two

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "refs_raw2.json")
SCAN_DATE = "2026-09-22"
W3 = ("201501010000", "202609222359")

ARX_QUERIES = [
    ("arx-W3-approvalgate", 'abs:"human approval"', 30),
    ("arx-W3-approvalagent", 'abs:"approval" AND abs:"agent" AND cat:cs.AI', 30),
    ("arx-W3-approvalfatigue", 'abs:"approval fatigue" OR abs:"rubber stamp"', 25),
    ("arx-W3-oversight", 'abs:"human oversight" OR abs:"scalable oversight"', 30),
    ("arx-W3-escalation", 'abs:"escalation" AND abs:"human"', 30),
    ("arx-W3-defer", 'abs:"defer" AND abs:"expert"', 30),
    ("arx-W3-reject", 'abs:"reject option" OR abs:"selective prediction"', 30),
    ("arx-W3-faithful", 'abs:"faithfulness" AND abs:"user interface"', 25),
    ("arx-W3-substitution", 'abs:"semantic" AND abs:"substitution" AND abs:"tool"', 25),
    ("arx-W3-toctou", 'abs:"time-of-check" OR abs:"TOCTOU" OR abs:"race condition" AND abs:"authorization"', 25),
    ("arx-W3-injection", 'abs:"indirect prompt injection"', 30),
    ("arx-W3-hijack", 'abs:"hijack" AND abs:"approval"', 25),
    ("arx-W3-attenuation", 'abs:"capability" AND abs:"attenuation"', 25),
    ("arx-W3-pep", 'abs:"policy enforcement point" OR abs:"reference monitor"', 25),
    ("arx-W3-monitorability", 'abs:"monitorability" OR abs:"monitoring" AND abs:"untrusted"', 25),
    ("arx-W3-entropy", 'abs:"detection" AND abs:"entropy" AND abs:"attack"', 25),
    ("arx-W3-guardrailbypass", 'abs:"guardrail" AND (abs:"bypass" OR abs:"jailbreak")', 30),
    ("arx-W3-mcpsec", 'abs:"Model Context Protocol" AND abs:"security"', 25),
    ("arx-W3-toolpoison", 'abs:"tool" AND abs:"poison" AND abs:"agent"', 25),
    ("arx-W3-crywolf", 'abs:"false alarm" AND abs:"trust"', 25),
    ("arx-W3-habituation", 'abs:"habituation" AND abs:"warning"', 25),
    ("arx-W3-sepduty", 'abs:"separation of duties" OR abs:"least privilege"', 25),
    ("arx-W3-principalagent", 'abs:"principal-agent" AND abs:"security"', 25),
    ("arx-W3-costverif", 'abs:"costly" AND abs:"verification" AND abs:"monitoring"', 25),
    ("arx-W3-screening", 'abs:"signal detection" AND abs:"threshold"', 25),
    ("arx-W3-mixedinit", 'abs:"mixed-initiative" OR abs:"when to ask"', 25),
    ("arx-W3-withhold", 'abs:"abstain" AND abs:"safety"', 25),
    ("arx-W3-audit", 'abs:"audit" AND abs:"agent" AND abs:"authorization"', 25),
]


def main():
    rep = dict(scan_date=SCAN_DATE,
               form=dict(index="arXiv API (export.arxiv.org)", date_field="submittedDate",
                         windows={"W3": list(W3)}, sort="relevance",
                         queries=[q[0] for q in ARX_QUERIES], scan_date=SCAN_DATE),
               arxiv={}, errors=[])
    for label, qbody, n in ARX_QUERIES:
        try:
            rows = arxiv_query(qbody, W3, n)
            for r in rows:
                r["query"] = label
                r["query_body"] = qbody
            rep["arxiv"][label] = dict(query=qbody, window=list(W3), n_returned=len(rows), rows=rows)
            print("%-24s %-3d rows" % (label, len(rows)), flush=True)
        except Exception as e:      # noqa: BLE001
            rep["errors"].append((label, repr(e)))
            print("%-24s ERROR %r" % (label, e), flush=True)
        time.sleep(3.2)
    ids = {r["id"] for blk in rep["arxiv"].values() for r in blk["rows"]}
    rep["n_unique_arxiv"] = len(ids)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    print("\nqueries %d | unique arXiv ids %d | errors %d | wrote %s"
          % (len(ARX_QUERIES), len(ids), len(rep["errors"]), os.path.basename(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
