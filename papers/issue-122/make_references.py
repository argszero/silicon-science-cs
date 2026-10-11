#!/usr/bin/env python3
"""Issue #122 -- render the numbered reference list from the artefacts.

Nothing is typed here.  Each line is built from `refs/curated.json` (identifier, title, role and the
role's one-line statement of where the entry is used) and `refs/meta.json` (authors, year).  The
numbering is *declared*, in `ORDER`, because it cannot yet be derived from a manuscript that does not
exist -- and a declared order that lives in code is reproducible, whereas one agreed by eye is not.

Conventions taken from the journal's own published manuscript (issue #120, read at its PR branch) and
from the journal's style sheet (`README.md`, *Formal References section*: numbered `[1]`-`[n]`):
    [N] Family, I., Family, I., Family, I., et al. (YEAR). *Title*. arXiv:ID. URL -- where it is used
Three authors are listed, then `et al.`; the identifier is printed VERBATIM (an old-style arXiv id
keeps its category prefix, so `math/0508451` is never rendered as `0508451`).  The marker is `[n]`,
the SAME form the body cites with, so the block and the in-text keys are one convention.

Usage:  /usr/bin/python3 make_references.py
Out:    references.md            the block to paste into the manuscript
        refs/numbering.json      bare id -> rendered number (for the coverage check)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.join(HERE, "refs", "curated.json")
META = os.path.join(HERE, "refs", "meta.json")
OUT = os.path.join(HERE, "references.md")
NUM = os.path.join(HERE, "refs", "numbering.json")

# The declared order: the paper's own argument path, so a reader meeting the list cold sees the
# literature in the order the text uses it.  Within a family, oldest first.
ORDER = ["construct", "theory", "mechanism", "protocol", "prevention", "measurement", "adjacent"]

MAX_AUTHORS = 3          # three named, then "et al."


def author_str(names):
    """`Sina Alemohammad` -> `Alemohammad, S.`  A single-token name is printed as it is."""
    out = []
    for n in names:
        parts = n.split()
        if len(parts) < 2:
            out.append(n)
            continue
        family, given = parts[-1], parts[:-1]
        initials = " ".join(g[0] + "." for g in given if g)
        out.append("%s, %s" % (family, initials))
    if not out:
        return ""
    if len(out) > MAX_AUTHORS:
        return ", ".join(out[:MAX_AUTHORS]) + ", et al."
    if len(out) == 1:
        return out[0]
    return ", ".join(out[:-1]) + ", and " + out[-1]


def declaration(n, by_role):
    """The declared convention for the entries' closing one-line difference field.

    The field is generated FROM the entry's role, so it is a role-class difference rather than a
    sentence written per entry.  The house style asks each entry to close with a one-line stated
    difference; a class-level line is a difference at the level of the class, and that is a choice
    the reader must be TOLD about where the entries are read rather than left to infer from the
    repetition (revision round 1's W3; the same shape #120's W4 required corrected).  The
    declaration is GENERATED here from the role assignment the entries were selected by, so it
    cannot drift from the list it describes.
    """
    roles = [r for r in ORDER if by_role[r]]
    classes = ", ".join("%s %d" % (r, len(by_role[r])) for r in roles)
    return (
        "*The stated difference closing every entry is its **role class**, not a sentence written "
        "per entry; that is a declared convention.* Each entry's closing clause names the family the "
        "entry belongs to and the relationship that family bears to this work, and it is generated "
        "from the same role assignment that selected the entry (`refs_curate.py`) — so the field "
        "states the rule the list was built by and cannot drift from it.  The %d entries fall into "
        "%d classes (%s).  The per-entry difference is therefore read as: this work is *of* that "
        "class, and the class's clause is the difference from this paper."
        % (n, len(roles), classes))


def main():
    cur = json.load(open(CUR))["entries"]
    meta = json.load(open(META))["meta"]
    by_role = {r: [] for r in ORDER}
    unknown = []
    for e in cur:
        if e["role"] not in by_role:
            unknown.append(e["role"])
        else:
            by_role[e["role"]].append(e)
    extra = sorted(set(unknown))
    if extra:
        sys.exit("roles not covered by ORDER: %s (add them, do not silently drop the entries)"
                 % extra)

    lines, numbering, seen = [], {}, set()
    for role in ORDER:
        for e in sorted(by_role[role], key=lambda x: (x["published"], x["bare"])):
            b = e["bare"]
            if b in seen:
                sys.exit("duplicate identifier in the curated set: %s" % b)
            seen.add(b)
            if b not in meta:
                sys.exit("no author metadata for %s -- run refs_meta.py" % b)
            m = meta[b]
            n = len(lines) + 1
            numbering[b] = n
            url = ("https://doi.org/" + b) if b.startswith("10.") else ("https://arxiv.org/abs/" + b)
            ident = ("DOI: " + b) if b.startswith("10.") else ("arXiv:" + b)
            lines.append("[%d] %s (%s). *%s*. %s. %s -- %s"
                         % (n, author_str(m["authors"]), m["year"], e["title"], ident, url,
                            e["diff"]))

    # A list where the numbering skips or repeats is a list a reader cannot cite: assert contiguity
    # rather than trust that the loop produced it.
    nums = [numbering[b] for b in numbering]
    if sorted(nums) != list(range(1, len(nums) + 1)):
        sys.exit("numbering is not 1..N contiguous")
    if len(lines) != len(cur):
        sys.exit("%d rendered lines for %d curated entries" % (len(lines), len(cur)))
    no_authors = [b for b in numbering if not meta[b]["authors"]]
    if no_authors:
        sys.exit("entries without authors would render an empty author field: %s" % no_authors)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("## References\n\n")
        f.write(declaration(n=len(lines), by_role=by_role) + "\n\n")
        f.write("\n\n".join(lines) + "\n")
    json.dump({"order": ORDER, "max_authors": MAX_AUTHORS, "n": len(numbering),
               "numbering": numbering}, open(NUM, "w"), indent=1, sort_keys=True)
    print("rendered %d references -> %s (%s)" % (len(lines), OUT, NUM))
    for role in ORDER:
        print("   %-12s %d" % (role, len(by_role[role])))
    print("   n with 4+ authors (rendered 'et al.'): %d"
          % sum(1 for b in numbering if len(meta[b]["authors"]) > MAX_AUTHORS))


if __name__ == "__main__":
    main()
