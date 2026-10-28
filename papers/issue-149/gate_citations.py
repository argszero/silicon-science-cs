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
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from placements import PLACEMENTS, PRUNED, COMPARISON_KEYS

FLOOR = 100

# What this paper does in each section the corpus is placed against. The difference line is
# `<what that work does, as placed>; <what this paper does here>`, so its two halves are authored
# rather than templated, and the ten clauses are written out rather than abbreviated to a section
# id: "(serves S7)" is a pointer a reader of the manuscript cannot resolve, which is the defect
# the editorial triage recorded against a round label cited inside a script.
SECTION_DIFFERENCE = {
    "S1": "this paper asks what one declaration admits before anyone installs it, and prices the "
          "difference",
    "S2": "this paper makes the admissible set the object and reports it as a share of edges, not "
          "as a property of a package",
    "S3": "this paper asks whether the alternatives differ in consequence, and reports that "
          "separation as the finding rather than the raw ambiguity",
    "S4": "this paper attributes the difference to the range's syntax, separating a bounded range "
          "from a wild one",
    "S5": "this paper reads both registries with one instrument, so the conventions are the "
          "comparison and not the background",
    "S6": "this paper uses the registry as the instrument and states what the instrument cannot see",
    "S7": "this paper proposes no alternative mechanism; it measures what a declared range leaves "
          "open beside these",
    "S8": "this paper uses the constraint formulation to compute the solution support exactly "
          "rather than to bound it",
    "S9": "this paper reports Wilson intervals throughout, so every rate is read with its "
          "uncertainty",
    "S10": "this paper names the threats this instrument cannot answer and what each would require",
}


def resolve(named, keys):
    if named in keys:
        return named
    hits = [k for k in keys if k.startswith(named)]
    return hits[0] if len(hits) == 1 else None


def first_family_token(name):
    """The family token in a form the house style admits: letters, apostrophes, hyphens only.

    A stored "Wynn Jr." or "Claes" carries particles and suffixes the component's class does not
    admit; the token before the first space is what the entry prints, and it stays inside the class
    rather than being dropped from the window.
    """
    if not name:
        return "Anon"
    tok = str(name).strip().split()[0]
    tok = "".join(ch for ch in tok if ch.isalpha() or ch in "'\u2019-")
    return tok or "Anon"


def corpus_numbers(placed):
    """number -> key, fixed by the corpus so the list and the body cannot disagree."""
    return {k: i for i, k in enumerate(sorted(placed), 1)}


def render_entry(number, e):
    """One bibliography entry. The ONLY place an entry is produced.

    The house style resolves the components in one order: `[n]` -- authors -- the year in
    parentheses -- the title -- the venue -- the link printed as a **resolvable URL** -- and the
    entry closes with its one-line `Difference:`. Two things were wrong here and both were the
    emitter's, not the 102 lines it wrote: the link was printed as a bare `DOI 10.x/...` string (a
    reader cannot follow it from the rendered page; the journal's own corpus carries a URL on 23
    of 23 packages), and there was no stated difference.

    The URL is built from the DOI the corpus stores, so an entry whose record carries no DOI
    cannot silently print an identifier nobody can click -- it stops the build.
    """
    venue = (e.get("venue") or "").strip()
    year = e.get("year") or "n.d."
    title = html.unescape((e.get("title") or "").strip().rstrip("."))
    bits = ["%s. (%s)." % (first_family_token(e.get("first_author")), year), "%s." % title]
    if venue:
        bits.append("%s." % html.unescape(venue).rstrip("."))
    doi = (e.get("doi") or "").strip()
    if not doi:
        raise SystemExit("entry [%d] (%s) carries no DOI, so the entry has no resolvable link to "
                         "print" % (number, e.get("key")))
    bits.append("https://doi.org/%s." % doi)
    # The stated difference comes from the placement that put this entry in the manuscript: the
    # section it serves and the claim it was placed to support. Both are authored in placements.py
    # rather than derived from the title, and both are checked there (C1: every placement resolves
    # to exactly one kept entry; C2: every placed entry carries stored verification).
    try:
        section, claim = PLACEMENTS[_placement_key(e)]
    except (KeyError, TypeError):
        raise SystemExit("entry [%d] (%s) is placed with no claim, so it has no stated difference"
                         % (number, e.get("key")))
    bits.append("Difference: %s; %s." % (claim.rstrip("."), SECTION_DIFFERENCE[section]))
    return "[%d] %s" % (number, " ".join(bits))


def _placement_key(entry):
    """The PLACEMENTS key this corpus entry was placed under (keys are prefix-resolved)."""
    for named in PLACEMENTS:
        if resolve(named, {entry["key"]}) == entry["key"]:
            return named
    return None


def render_list(placed, numbers, kept):
    L = ["## References", ""]
    for k in sorted(placed):
        # `[n]` entries against `[n]` citations: a list numbered `1.` beside a body citing `[n]`
        # makes a naive bib-count read 0 entries, which refgate reports as a style mismatch.
        L.append(render_entry(numbers[k], kept[k]))
        L.append("")          # a blank line between entries: CommonMark reads a bare list
                              # of lines as one paragraph and the editor's refgate said so on #145
    return "\n".join(L) + "\n"


def splice_references(text, rendered):
    """Replace the manuscript's `## References` section with the rendered one.

    The section is derived from the corpus exactly as `references.md` is, and it is checked against
    that render rather than trusted -- otherwise the manuscript's list and the package's list are
    two copies of one derivation, which is how the bare-DOI form survived in both at once.
    """
    marker = "\n## References"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("manuscript.md has no `## References` section to rewrite")
    return text[:idx + 1] + rendered


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
    ap.add_argument("--corpus", default="refs/references.json")
    ap.add_argument("--list", metavar="MD", default=None,
                    help="write the generated reference list to this file")
    ap.add_argument("--rewrite-references", action="store_true",
                    help="rewrite the manuscript's `## References` section from the corpus")
    ap.add_argument("--check-references", action="store_true",
                    help="assert the manuscript's section and --list are the same render")
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
        rendered = render_list(placed, numbers, kept)
        open(a.list, "w", encoding="utf-8").write(rendered)
        print("  [ok]   wrote %s (%d entries)" % (a.list, len(placed)))

    if a.rewrite_references:
        rendered = render_list(placed, numbers, kept)
        open(a.manuscript, "w", encoding="utf-8").write(splice_references(text, rendered))
        print("  [ok]   rewrote the manuscript's `## References` section from the corpus "
              "(%d entries)" % len(placed))

    if a.check_references:
        # The manuscript's section and `references.md` are two copies of ONE derivation. Checking
        # that they agree is what keeps the entry form from surviving in one after being fixed in
        # the other -- which is exactly how the bare-DOI form lived in both at once.
        rendered = render_list(placed, numbers, kept)
        now = open(a.manuscript, encoding="utf-8").read()
        got = now[now.find("\n## References") + 1:] if "\n## References" in now else ""
        if got == rendered:
            print("  [ok]   the manuscript's References section is the corpus render "
                  "(%d entries, every entry carrying a resolvable URL)" % len(placed))
        else:
            print("  [FAIL] the manuscript's References section is not the corpus render -- "
                  "regenerate it (gate_citations.py --rewrite-references)")
            return 1
        if a.list:
            if open(a.list, encoding="utf-8").read() == rendered:
                print("  [ok]   %s is the same render" % a.list)
            else:
                print("  [FAIL] %s is not the same render (regenerate with --list)" % a.list)
                return 1

    print("\nVERDICT: PASS (%d cited of %d placed, floor %d)"
          % (len(resolved), len(placed), FLOOR))
    return 0


if __name__ == "__main__":
    sys.exit(main())
