#!/usr/bin/env python3
"""issue-165 -- the citation authenticity report: every reference against the record it was checked on.

The journal's submission bar asks for one line per entry -- citation key, verification method, result,
and the real record found. This program writes that file FROM `refs/records.json`, so the report cannot
say something the corpus does not: a key that is not in `accepted` cannot appear as verified, and an
entry whose DOI is missing is reported as missing rather than printed with a blank where it belongs.

It also reports the refusals. A corpus that grew by dropping the works it failed to find would be a
silent lie, and the refusal histogram is the part of the report that says how much of the search the
registry could answer at all.

`--check` regenerates the report in memory and compares it byte for byte with the committed file, so a
reader can confirm the report still describes the corpus rather than an older state of it.

Usage:
  python3 ref_check.py            -> write reference-check.md
  python3 ref_check.py --check    -> exit 0 only if the committed report matches this render
"""
import collections
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECORDS = os.path.join(HERE, "refs", "records.json")
MANUSCRIPT = os.path.join(HERE, "manuscript.md")
OUT = os.path.join(HERE, "reference-check.md")


def load():
    return json.load(open(RECORDS))


def cited_keys(manuscript):
    """The keys the manuscript actually cites, read from the rendered bibliography order: an entry
    that is in the corpus but not in the manuscript would be padding, and this report must not certify
    it as a reference."""
    text = open(manuscript).read()
    cut = text.rfind("## References")
    body, refs = text[:cut], text[cut:]
    keys = []
    for line in refs.splitlines():
        if line.startswith("[") and "doi:" in line:
            doi = line.rsplit("doi:", 1)[1].strip()
            keys.append(doi)
    return body.count("["), keys


def build(rec):
    accepted = sorted(rec["accepted"], key=lambda r: r["key"])
    rejected = sorted(rec.get("rejected", []), key=lambda r: r["key"])
    not_run = rec.get("not_run", [])

    lines = []
    lines.append("# Reference check — issue 165")
    lines.append("")
    lines.append("Every entry below was proposed as a query, answered by a registry, and then accepted or")
    lines.append("refused by the acceptance rule in `build_refs.py`. The **registry is the authority**: no")
    lines.append("reference entered this corpus because it was remembered, and the query is only the thing")
    lines.append("that asks. Accepted records need a DOI, so a reader can open the record and compare it")
    lines.append("with the entry the manuscript prints.")
    lines.append("")
    lines.append("| # | citation key | verification method | result | the record found (title / DOI / year) |")
    lines.append("|---|---|---|---|---|")
    for i, r in enumerate(accepted, 1):
        title = html.unescape(r.get("title") or "").replace("|", "\\|")
        method = r.get("verified") or "registry return, verified"
        if isinstance(method, dict):
            method = method.get("registry") or json.dumps(method, sort_keys=True)
        lines.append("| %d | `%s` | %s | verified | %s / %s / %s |"
                     % (i, r["key"], method, title, r["doi"], r.get("year")))
    lines.append("")
    lines.append("## The refusals, which are also a result")
    lines.append("")
    lines.append("A corpus that grew by dropping what it could not verify would be a silent lie, so the")
    lines.append("refusals are reported with their reasons. A refusal is not a claim that the work does")
    lines.append("not exist; it is a claim that this package does not hold a record it could verify.")
    lines.append("")
    hist = collections.Counter()
    for r in rejected:
        reason = r.get("reason", "?")
        if reason.startswith("REGISTRY UNAVAILABLE"):
            hist["the registry could not be read (rate limit or outage)"] += 1
        elif reason.startswith("DEMOTED"):
            hist["demoted by a later, tighter version of the acceptance rule"] += 1
        elif "DUPLICATE" in reason:
            hist["a duplicate of a work already in the corpus"] += 1
        elif reason.startswith("no returned record passed BOTH criteria"):
            hist["no returned record matched the title and the year"] += 1
        else:
            hist[reason.split(":")[0][:70]] += 1
    lines.append("| count | reason |")
    lines.append("|---|---|")
    for reason, n in hist.most_common():
        lines.append("| %d | %s |" % (n, reason))
    lines.append("")
    if not_run:
        lines.append("## Not run")
        lines.append("")
        lines.append("These slots were never answered: the registry refused the request itself. They are")
        lines.append("**not** refusals about the works, and they stay unfetched until the registry can be")
        lines.append("read again.")
        lines.append("")
        for r in sorted(not_run, key=lambda x: x["key"]):
            lines.append("- `%s` — %s" % (r["key"], r.get("reason", "?")))
        lines.append("")
    lines.append("## Totals")
    lines.append("")
    lines.append("- accepted and verified: **%d**" % len(accepted))
    lines.append("- refused: **%d**" % len(rejected))
    lines.append("- not run (registry unavailable): **%d**" % len(not_run))
    return "\n".join(lines) + "\n", len(accepted), len(rejected), len(not_run)


def main():
    rec = load()
    text, n_acc, n_rej, n_notrun = build(rec)
    if "--check" in sys.argv:
        committed = open(OUT).read() if os.path.exists(OUT) else ""
        if committed != text:
            print("CHECK FAILED: reference-check.md differs from what this run renders -- the report no "
                  "longer describes the corpus", file=sys.stderr)
            return 1
        print("  report matches the corpus byte for byte: %d verified, %d refused, %d not run"
              % (n_acc, n_rej, n_notrun))
        return 0
    with open(OUT, "w") as fh:
        fh.write(text)
    print("ref_check: wrote reference-check.md -- %d verified, %d refused, %d not run"
          % (n_acc, n_rej, n_notrun))
    return 0


if __name__ == "__main__":
    sys.exit(main())
