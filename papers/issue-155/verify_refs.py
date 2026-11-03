#!/usr/bin/env python3
"""Issue #155 -- independent verification of every placed reference, against Crossref.

This is NOT a second opinion from the same source. `candidates.json` was built from
Crossref query responses; a query response can carry a wrong or merged record. Here
each placed DOI is fetched DIRECTLY by identifier (`/works/<doi>`), which is a
different endpoint with a different failure mode, and the returned title is compared
against the title stored at placement time. A record that only ever "matched" because
of how it was retrieved dies here.

Verdicts:
  VERIFIED        title tokens agree (>= 0.80) AND year agrees
  VERIFIED-EDITION title agrees, year differs -- recorded as an edition note, not a pass
                   by default: `reference-check.md` must show which one it is
  TITLE-MISMATCH  the DOI resolves to a different work  -> fatal
  NOT-FOUND       the DOI does not resolve               -> fatal
  NETWORK-FAIL    no answer                              -> fatal (never silently skipped)

Fatal verdicts make the exit code 1. `--placement` exists so the check can be
planted: point it at a doctored copy and the run must go red.
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "silicon-science-cs/1.0 (mailto:how2how2how2-arch@users.noreply.github.com)"
THRESHOLD = 0.80
SLEEP = 0.35


def norm_tokens(text):
    t = unicodedata.normalize("NFKD", text or "")
    t = re.sub(r"<[^>]+>", " ", t)                      # strip <i>, <scp>, <sub> ...
    t = t.replace("&amp;", " and ").replace("&#x2014;", " ").replace("&", " and ")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return [w for w in t.split() if w]


def agreement(a, b):
    """Token-set Jaccard. One number per pair, printed, so a threshold miss is visible."""
    A, B = set(norm_tokens(a)), set(norm_tokens(b))
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def year_of(m):
    for field in ("published-print", "published-online", "issued", "created"):
        parts = m.get(field, {}).get("date-parts", [[None]])[0]
        if parts and parts[0]:
            return int(parts[0])
    return None


def fetch(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as fh:
        return json.load(fh)["message"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--placement", default=os.path.join(HERE, "placement.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "reference-check.md"))
    args = ap.parse_args()

    with open(args.placement, encoding="utf-8") as fh:
        doc = json.load(fh)
    placed = doc["placed"]

    rows, fatal = [], []
    for i, p in enumerate(placed, 1):
        doi = p["doi"]
        try:
            m = fetch(doi)
        except urllib.error.HTTPError as exc:
            verdict, detail = "NOT-FOUND", "HTTP %s" % exc.code
            title_ret, year_ret, ratio = "", None, 0.0
        except Exception as exc:  # noqa: BLE001
            verdict, detail = "NETWORK-FAIL", "%s: %s" % (type(exc).__name__, exc)
            title_ret, year_ret, ratio = "", None, 0.0
        else:
            title_ret = (m.get("title") or [""])[0].strip()
            year_ret = year_of(m)
            ratio = agreement(p["title"], title_ret)
            if ratio < THRESHOLD:
                verdict = "TITLE-MISMATCH"
                detail = "token agreement %.2f < %.2f" % (ratio, THRESHOLD)
            elif year_ret is not None and p["year"] is not None and year_ret != p["year"]:
                verdict = "VERIFIED-EDITION"
                detail = "year placed %s, Crossref %s" % (p["year"], year_ret)
            else:
                verdict = "VERIFIED"
                detail = "token agreement %.2f" % ratio

        if verdict in ("NOT-FOUND", "TITLE-MISMATCH", "NETWORK-FAIL"):
            fatal.append((p["key"], verdict, detail))

        rows.append({"key": p["key"], "section": p["section"], "doi": doi,
                     "title": p["title"], "title_returned": title_ret,
                     "year": p["year"], "year_returned": year_ret,
                     "agreement": round(ratio, 3), "verdict": verdict, "detail": detail})
        print("[%3d/%3d] %-20s %-16s %s" % (i, len(placed), p["key"], verdict, detail))
        time.sleep(SLEEP)

    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    # ---- the report the journal reads -------------------------------------
    lines = []
    lines.append("# Reference verification -- issue #155\n")
    lines.append("Every placed reference re-fetched **by DOI** from Crossref "
                 "(`api.crossref.org/works/<doi>`), independently of the query pass that "
                 "harvested it. Title agreement is token-set Jaccard against the stored "
                 "title; the pass threshold is %.2f. A DOI that resolves to a different "
                 "work, or does not resolve at all, is fatal.\n" % THRESHOLD)
    lines.append("| verdict | entries |")
    lines.append("|---|---|")
    for v in ("VERIFIED", "VERIFIED-EDITION", "TITLE-MISMATCH", "NOT-FOUND", "NETWORK-FAIL"):
        if v in counts:
            lines.append("| %s | %d |" % (v, counts[v]))
    lines.append("| **total** | **%d** |\n" % len(rows))

    lines.append("## Entry-by-entry\n")
    lines.append("| # | key | section | verdict | agreement | DOI | Crossref title |")
    lines.append("|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        t = r["title_returned"].replace("|", "\\|")[:90]
        lines.append("| %d | `%s` | %s | %s | %.2f | `%s` | %s |"
                     % (i, r["key"], r["section"], r["verdict"], r["agreement"], r["doi"], t))
    lines.append("")

    edits = [r for r in rows if r["verdict"] == "VERIFIED-EDITION"]
    if edits:
        lines.append("## Edition notes\n")
        lines.append("These DOIs resolve to the right work but Crossref gives a different "
                     "year than the one stored at placement. The bibliography uses the "
                     "Crossref year; a reprint or a later indexing year is not an error, but "
                     "it must be stated rather than smoothed over.\n")
        for r in edits:
            lines.append("- `%s` -- placed as %s, Crossref says %s: %s"
                         % (r["key"], r["year"], r["year_returned"], r["title_returned"]))
        lines.append("")

    if fatal:
        lines.append("## Unverifiable entries (fatal)\n")
        lines.append("These must be removed or replaced before submission.\n")
        for k, v, d in fatal:
            lines.append("- `%s` -- %s (%s)" % (k, v, d))
        lines.append("")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print("\n" + "  ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    print("total=%d  report=%s" % (len(rows), os.path.basename(args.out)))
    if fatal:
        print("\nFATAL: %d unverifiable entr(ies)" % len(fatal))
        return 1
    print("REFCHECK: all %d placed references resolve to the work they claim" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
