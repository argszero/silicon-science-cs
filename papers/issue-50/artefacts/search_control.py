#!/usr/bin/env python3
"""R349 -- a POSITIVE CONTROL for the reverse-gap search, because an empty response and an empty set
are the same string.

Two failures happened while this registration's search was being run, and neither was a property of the
index:

  1. the arXiv leg returned **0 records for all eight queries** because the quoted phrases went into the
     URL unencoded -- the API answered with an empty body, which the parser reported as *"returned 0"*;
  2. the Crossref leg returned `total-results: None` for all four queries because the filter was built
     from **two** field names joined by "/" (`from-created-date/until-created-date:…`) instead of one
     field with two bounds -- a malformed filter, which Crossref answered with an error body.

Both were read as results-shaped output until the shape was inspected.  An absence claim whose
instrument can silently return nothing has no evidential value, so every scan query here is required to
pass a control: **a query whose answer is known to be non-empty must come back non-empty, or the scan
aborts.**  This file is that control, kept beside the scans it validates.
"""
import json
import subprocess
import sys
from urllib.parse import quote

CONTROLS = [
    ("arXiv", "https://export.arxiv.org/api/query?search_query=" + quote('cat:cs.DC AND all:"tail latency"', safe="")
     + "&sortBy=submittedDate&sortOrder=descending&max_results=5", "<opensearch:totalResults>"),
    ("Crossref", "https://api.crossref.org/works?query.bibliographic=speculative+execution&rows=3"
     "&mailto=how2how2how2@example.com&filter=from-created-date:2026-03-17,until-created-date:2026-09-17",
     '"total-results"'),
]


def main():
    bad = 0
    for name, url, marker in CONTROLS:
        r = subprocess.run(["curl", "-sL", "--max-time", "45", url], capture_output=True, text=True)
        body = r.stdout or ""
        if marker == "<opensearch:totalResults>":
            import re
            m = re.search(r"<opensearch:totalResults>(\d+)</opensearch:totalResults>", body)
            n = int(m.group(1)) if m else None
        else:
            try:
                n = json.loads(body)["message"]["total-results"]
            except Exception:
                n = None
        ok = isinstance(n, int) and n > 0
        print("%-6s %-9s control query returned total=%s (bytes=%d)%s"
              % ("PASS" if ok else "FAIL", name, n, len(body), "" if ok else "  <-- the instrument cannot be trusted"))
        bad += 0 if ok else 1
    print("search control: %d control(s), %d failed%s"
          % (len(CONTROLS), bad, "" if not bad else " -- DO NOT read any zero from a scan whose control fails"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
