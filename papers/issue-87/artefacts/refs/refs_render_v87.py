#!/usr/bin/env python3
"""#87 R404 -- render the bibliography in the journal's house entry form, as the block the manuscript embeds.

The form (README -> Presentation requirements), read as a *test over every entry*:
  `[n] ` -- the authors (`Family, I.`, `et al.` for four or more, family first, mixed case) -- the year in
  parentheses -- the title in title case -- the venue or the identifier -- the link as a resolvable URL --
  the entry closing with its one-line `Difference: ...`.
Entries are separated by a BLANK LINE: the list is read as it is rendered, and consecutive entry lines are
one paragraph to every CommonMark renderer.

Writes references_block.md (the block, headed `## References`) and references.json (the same entries as data,
which is what the manuscript's assembly step cites by key).
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILT = os.path.join(HERE, "refs_built.json")
VERIFIED = os.path.join(HERE, "refs_verified.json")
BLOCK = os.path.join(HERE, "references_block.md")
DATA = os.path.join(HERE, "references.json")


def main():
    built = json.loads(io.open(BUILT, encoding="utf-8").read())
    ver = json.loads(io.open(VERIFIED, encoding="utf-8").read())
    verdict = {r["key"]: r for r in ver["rows"]}

    entries = []
    for i, e in enumerate(built["entries"], start=1):
        key = e["id"] if e["source"] == "arxiv" else e["doi"]
        v = verdict[key]
        if not v["identity_match"]:
            raise SystemExit("entry %d (%s) has no identity match: refusing to render" % (i, key))
        entries.append(dict(n=i, key=key, source=e["source"], authors=e["authors"], year=e["year"],
                            title=e["title"], venue=e["venue"], url=e["url"],
                            difference=e["difference"], verified=v["method"],
                            live_title=v["live_title"], pool_title=e["pool_title"]))

    lines = ["## References", ""]
    for e in entries:
        lines.append("[%d] %s (%s). %s. %s. %s Difference: %s"
                     % (e["n"], e["authors"], e["year"], e["title"], e["venue"], e["url"], e["difference"]))
        lines.append("")
    io.open(BLOCK, "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")
    io.open(DATA, "w", encoding="utf-8").write(json.dumps(
        dict(round="R404", scan_date=ver["scan_date"], n=len(entries),
             order_note="The numbering below is the selection order (the manuscript's order of first "
                        "citation); the assembly step asserts that the body cites every key exactly as the "
                        "bibliography numbers it, and refuses a key the body never reaches.",
             controls=ver["controls"], entries=entries), indent=1, sort_keys=True))
    print("rendered %d entries -> %s and %s" % (len(entries), os.path.basename(BLOCK), os.path.basename(DATA)))
    print("first three lines:")
    for l in ("\n".join(lines).split("\n")[2:8]):
        print("   " + l[:150])
    return 0


if __name__ == "__main__":
    sys.exit(main())
