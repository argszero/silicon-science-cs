"""Gate the manuscript's citations against the corpus, and emit the reference list.

Three judgements, each of which has failed before in this project:

  C1  every key cited in the manuscript resolves to a PLACED corpus entry (a citation to a record
      that was pruned is a citation to something we decided supports no claim here);
  C2  every placed entry is cited in the manuscript -- an entry we placed and do not cite is
      padding counted toward the floor, which is the failure the floor exists to prevent;
  C3  the cited count meets the floor.

`--list` writes the reference list as a numbered markdown section, sorted by key, with each entry's
real record (title, first author, year, venue, DOI). The list is generated from the corpus, never
hand-typed: a hand-typed reference list is a derived artefact that goes stale silently.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from placements import PLACEMENTS, PRUNED, COMPARISON_KEYS

FLOOR = 100


def resolve(named, keys):
    if named in keys:
        return named
    hits = [k for k in keys if k.startswith(named)]
    return hits[0] if len(hits) == 1 else None


def corpus_numbers(placed):
    """number -> key, fixed by the corpus so the list and the body cannot disagree."""
    return {k: i for i, k in enumerate(sorted(placed), 1)}


def numbered_keys(text, numbers):
    """[n] tokens in the rendered manuscript, mapped back to keys."""
    rev = {v: k for k, v in numbers.items()}
    found = []
    for group in re.findall(r"\[([0-9][0-9,\s]*)\]", text):
        for n in re.split(r"[,\s]+", group.strip()):
            if n.isdigit() and int(n) in rev:
                found.append(rev[int(n)])
    return found


def cited_keys(text):
    """Keys inside {{...}} (a group may list several, comma-separated)."""
    found = []
    for group in re.findall(r"\{\{([^}]*)\}\}", text):
        for k in group.split(","):
            k = k.strip()
            if k:
                found.append(k)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", default="manuscript.md")
    ap.add_argument("--corpus", default="research/references.json")
    ap.add_argument("--list", metavar="MD", default=None,
                    help="write the generated reference list to this file")
    ap.add_argument("--cite", action="store_true",
                    help="rewrite {{a,b}} markers into numbered citations [n] and emit --list")
    a = ap.parse_args()

    doc = json.load(open(a.corpus))
    kept = {e["key"]: e for e in doc["entries"] if e.get("review", "kept") == "kept"}
    placed = {}
    for named in PLACEMENTS:
        k = resolve(named, kept)
        if k:
            placed[k] = PLACEMENTS[named]

    text = open(a.manuscript, encoding="utf-8").read()
    numbers = corpus_numbers(placed)
    cited = cited_keys(text) + numbered_keys(text, numbers)

    bad = 0

    def ck(cond, msg):
        nonlocal bad
        print(("  [ok]   " if cond else "  [FAIL] ") + msg)
        if not cond:
            bad += 1

    # C1 every cited key resolves to a placed entry
    unresolved = [k for k in cited if resolve(k, placed) is None]
    ck(not unresolved,
       "C1 every cited key is a placed entry (%d keys cited, %d unresolved: %s)"
       % (len(set(cited)), len(unresolved), ", ".join(sorted(set(unresolved))[:6])))

    resolved = {resolve(k, placed) for k in cited if resolve(k, placed)}

    # C2 no padding
    uncited = sorted(set(placed) - resolved)
    ck(not uncited, "C2 every placed entry is cited (%d uncited: %s)"
       % (len(uncited), ", ".join(uncited[:8])))

    # C3 floor
    ck(len(resolved) >= FLOOR, "C3 cited >= %d (%d)" % (FLOOR, len(resolved)))

    # duplicated markers are a rendering hazard, not an error: report them
    dupes = [k for k in set(cited) if cited.count(k) > 1]
    if dupes:
        print("  [note] %d key(s) cited more than once: %s"
              % (len(dupes), ", ".join(sorted(dupes)[:6])))

    if bad:
        print("\nVERDICT: FAIL")
        return 1

    numbers = corpus_numbers(placed)

    if a.cite:
        def repl(m):
            group = [resolve(x.strip(), placed) for x in m.group(1).split(",") if x.strip()]
            nums = sorted({numbers[g] for g in group if g})
            return "[" + ", ".join(str(n) for n in nums) + "]"

        out = re.sub(r"\{\{([^}]*)\}\}", repl, text)
        open(a.manuscript, "w", encoding="utf-8").write(out)
        print("  [ok]   rewrote citation markers into %d numbered citations" % len(resolved))

    if a.list:
        L = ["## References", ""]
        for k in sorted(placed):
            e = kept[k]
            venue = (e.get("venue") or "").strip()
            bits = ["%s." % (e.get("first_author") or "anon"),
                    "%s." % (e.get("year") or "n.d."),
                    "%s." % (e.get("title") or "").strip().rstrip(".")]
            if venue:
                bits.append("%s." % venue.rstrip("."))
            if e.get("doi"):
                bits.append("DOI %s." % e["doi"])
            L.append("%d. %s" % (numbers[k], " ".join(bits)))
            L.append("")          # a blank line between entries: CommonMark reads a bare list
                                 # of lines as one paragraph and the editor's refgate said so on #145
        open(a.list, "w", encoding="utf-8").write("\n".join(L) + "\n")
        print("  [ok]   wrote %s (%d entries)" % (a.list, len(placed)))

    print("\nVERDICT: PASS (%d cited of %d placed, floor %d)"
          % (len(resolved), len(placed), FLOOR))
    return 0


if __name__ == "__main__":
    sys.exit(main())
