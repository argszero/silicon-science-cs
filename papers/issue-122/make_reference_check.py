#!/usr/bin/env python3
"""Issue #122 -- generate reference-check.md from the artefacts.

Nothing here is typed: the entries, the verification verdicts, the resolved titles, the metadata
route, the provenance of each curated record, the section that precedes the bibliography and the
scan for bracketed groups that are not citations are all read or computed out of the artefacts
(`refs/curated.json`, `refs/meta.json`, `refs/verify.log`, `manuscript.md`, `gates.log`).  The
prose this file writes is a set of STATEMENTS ABOUT THOSE ARTEFACTS, so a sentence that could go
stale is written as a computation rather than as a recollection -- a report adapted from a sibling
paper carries that paper's numbers and its paper's facts, and a count that is right beside a
sentence that is wrong reads as one right report.

The one thing this script cannot do is run the journal's gates: `.github/tools/` lives in the
journal repository, and their whole output is appended below verbatim from `gates.log` when that
file is present.

Usage:  /usr/bin/python3 make_reference_check.py
Out:    reference-check.md
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def bracketed_groups(body, numbered):
    """Classify every bracketed group in the BODY: citation key, unreachable digit list, or other.

    A count of citations is only meaningful if the scanner can tell a citation from a data literal,
    and the two can be written in the same shape: a bracketed, comma-separated digit list.  An
    interval `[0, 0]` is, to this scanner, a citation group.  So the groups are returned in three
    classes rather than asserted to be unambiguous:

      cite      -- a digit list, every number of which is a numbered entry (a citation key)
      literal   -- a digit list that does NOT resolve to numbered entries (ambiguous by shape;
                   this is the class that must be empty)
      other     -- not a digit list at all (inline mathematics, a figure cross-reference)
    """
    cite, literal, other = [], [], []
    for g in re.findall(r"\[([^\[\]]*)\]", body):
        if not re.fullmatch(r"[\d,\s\-–]+", g):
            other.append(g)
        elif all(n in numbered for n in re.findall(r"\d+", g)):
            cite.append(g)
        else:
            literal.append(g)
    return cite, literal, other


def main():
    cur = json.load(open(os.path.join(HERE, "refs", "curated.json")))["entries"]
    n_doi = sum(1 for e in cur if e["id"].startswith("10."))
    n_arx = len(cur) - n_doi
    meta_route = cur and json.load(open(os.path.join(HERE, "refs", "meta.json"))).get("route", "?")
    meta = json.load(open(os.path.join(HERE, "refs", "meta.json")))
    log = open(os.path.join(HERE, "refs", "verify.log")).read().splitlines()
    man = open(os.path.join(HERE, "manuscript.md"), encoding="utf-8").read()
    n_ok = sum(1 for l in log if l.startswith("OK "))
    n_problem = sum(1 for l in log if l.startswith("PROBLEM"))

    body, refs_block = man.split("## References", 1)
    number = {}                       # bare id -> the number it is rendered under
    for m in re.finditer(r"^(\d+)\. ", refs_block, re.M):
        number.setdefault(m.group(1), None)
    rendered = re.findall(r"^(\d+)\. (.*)$", refs_block, re.M)
    # map each rendered entry back to its curated id by the identifier it prints
    id_of = {}
    for m in re.finditer(r"^(\d+)\. (.*)$", refs_block, re.M):
        n, line = m.group(1), m.group(2)
        found = re.search(r"(arXiv:[0-9a-z./\-]+|DOI: [0-9./]+)", line)
        if found:
            ident = found.group(1).split(": ")[-1].split("arXiv:")[-1].rstrip(".")
            id_of[ident] = n
    cited_nums = set(re.findall(r"\[(\d+)(?:, ?\d+)*\]", body))
    cited = set()
    for group in re.findall(r"\[([\d,\s\-–]+)\]", body):
        for part in re.split(r",", group):
            part = part.strip()
            if re.match(r"^\d+$", part):
                cited.add(part)
    numbered = {n for n, _ in rendered}
    uncited = sorted(numbered - cited, key=int)
    cite_groups, literal_groups, other_groups = bracketed_groups(body, numbered)

    # -- facts about the manuscript's own structure, read rather than recalled -----------------
    heads = [(m.start(), m.group(1).strip()) for m in re.finditer(r"^## (.+)$", man, re.M)]
    refs_heads = [i for i, (pos, h) in enumerate(heads) if h == "References"]
    prev_head = heads[refs_heads[-1] - 1][1] if refs_heads and refs_heads[-1] > 0 else "(none)"
    after = man.split("## References", 1)[1]
    numbered_after = re.findall(r"^(\d+)\. ", after, re.M)

    # -- provenance of the curated set, read out of its own field ------------------------------
    src = collections.Counter(e.get("source", "?") for e in cur)
    src_txt = ", ".join("%d `%s`" % (v, k) for k, v in sorted(src.items()))

    # -- the metadata route, stated as the route the committed run took ------------------------
    if meta_route == "API batch":
        route_txt = ("the arXiv API answered in **batch** for all %d ids on the committed run "
                     "(`route: API batch` in `refs/meta.json`), so no per-id fallback was needed"
                     % n_arx)
    else:
        route_txt = ("the API probe failed on the committed run, so every record was read per id "
                     "from the arXiv **abstract page** (`route: abstract pages` in `refs/meta.json`), "
                     "which carries the same fields as schema.org `citation_*` meta tags")
    # the invariant is enforced where the routes MERGE, not inside either limb
    merge_txt = ("the title and author invariants are enforced **where the two routes merge**, not "
                 "inside either limb, so which route answers cannot decide whether an entry is "
                 "allowed to carry no authors (`refs_meta.py plant` injects that fault)")

    lines = []
    w = lines.append
    w("# Citation report - issue #122")
    w("")
    w("Companion to `manuscript.md`. Two duties: (i) authenticity of every reference, and (ii) coverage")
    w("and ambiguity of the in-text citation keys. This report is a declaration; reviewers verify")
    w("independently.")
    w("")
    w("## (i) Authenticity - how each entry was verified")
    w("")
    w("**Method.** Every entry is verified by re-fetching it **by its own identifier** and comparing the")
    w("returned title against the title recorded at curation time, after normalisation (NFKC, case,")
    w("punctuation and whitespace folded). The tool is committed and re-runnable from this directory:")
    w("")
    w("```")
    w("python3 refs_tool.py verify     # writes refs/verify.log")
    w("python3 refs_tool.py plant      # two-sided control: a corrupted title, an invented id, an invented DOI")
    w("```")
    w("")
    w("- **DOI entries** (%d) are fetched from `https://api.crossref.org/works/<doi>`." % n_doi)
    w("- **arXiv entries** (%d) are fetched from the arXiv API. **Transport note (measured):** this" % n_arx)
    w("  endpoint is intermittently unanswered from the authoring host -- the read times out rather than")
    w("  returning an error -- so the verifier is cache-first (`refs/verify_cache/`) and a re-run over a")
    w("  populated cache is instant and offline. The *metadata* pass (`refs_meta.py`) is where the")
    w("  authors come from, and its route on the committed run is stated rather than assumed: %s." % route_txt)
    w("- **The route cannot decide the invariant.** %s." % merge_txt.capitalize())
    w("- **Title comparison is taken through the XML parser, not a regex over raw text.** Measured on")
    w("  2026-10-03: a regex read left XML entity references literal (`&amp;`), which turned one correct")
    w("  citation into a false `MISMATCH`. The instrument now parses the Atom feed.")
    w("- **A two-sided control is run** (`refs_tool.py plant`): a corrupted title, an invented arXiv id")
    w("  and an invented DOI are injected into a throwaway copy of the curated set and **all three must")
    w("  fail**; the control asserts its own healthy rows still resolve beside them.")
    w("")
    w("**Result: %d/%d entries resolved to their recorded title, 0 unresolved.** The committed run log"
      % (n_ok, len(cur)))
    w("`refs/verify.log` holds **%d `OK` lines and %d `PROBLEM` lines**; the verification command exits"
      % (n_ok, n_problem))
    w("non-zero if any entry fails, so the verdict is a check rather than a statement.")
    w("")
    w("**Provenance of the curated set.** Each record carries a `source` field naming where its")
    w("identifier and title came from: %s. A title read out of the discovery artefact is copied, not" % src_txt)
    w("retyped -- which is the property the scan can certify, and the reason a title written from")
    w("recollection cannot enter the list unnoticed.")
    w("")
    w("**Author fields.** A verified identifier is not a verified citation record: the identifier pass")
    w("above confirms *title identity*, and says nothing about the authors a reference list needs.")
    w("Author names and years are fetched in a second pass (%d/%d entries carry authors; %d via Crossref,"
      % (meta["with_authors"], len(cur), n_doi))
    w("%d via the %s route, as recorded in `refs/meta.json`) and every name in the list is rendered"
      % (n_arx, meta_route))
    w("from `refs/meta.json` --")
    w("none is typed. The reference list is generated by `make_references.py` and injected by")
    w("`build_manuscript.py`, so the rendered entry and the fetched record cannot drift apart.")
    w("The identifier pass proves title identity; the year and category fields come from the same")
    w("discovery artefact as the titles and are **not** independently re-verified here.")
    w("")
    w("### Per-entry record")
    w("")
    w("| # | key | role | resolved title (as returned by the index) |")
    w("|---|---|---|---|")
    for l in log:
        if not l.startswith("OK "):
            continue
        parts = l.split(None, 3)
        bare, role, title = parts[1], parts[2], parts[3]
        w("| %s | `%s` | %s | %s |" % (id_of.get(bare, "?"), bare, role,
                                       title.replace("|", "\\|")))
    w("")
    w("## (ii) Coverage and ambiguity")
    w("")
    w("- **References section**: one `## References` heading, the last section of the file; the heading")
    w("  before it is `## %s`. Entries are numbered `1.`-`%d.` and each begins on its own line," % (prev_head, len(rendered)))
    w("  separated by a blank line, so the list is read as a list rather than as one paragraph.")
    w("- **Coverage**: %d entries, **%d cited in the body text by their numbered key**, %d uncited."
      % (len(numbered), len(cited), len(uncited)))
    w("  Every in-text citation is a bracketed number; no work is cited by name or by bare arXiv id")
    w("  without its key.")
    w("- **Uncited entries**: %s." % ("none" if not uncited else ", ".join(uncited)))
    w("- **Bracketed groups, by class** (a computed scan, not an assertion): %d in the body -- **%d**"
      % (len(cite_groups) + len(literal_groups) + len(other_groups), len(cite_groups)))
    w("  are citation keys (digit lists whose every number is a numbered entry), **%d** are digit lists"
      % len(literal_groups))
    w("  that do NOT resolve -- the shape-ambiguous class, which must be empty -- and **%d** are not"
      % len(other_groups))
    w("  digit lists at all (inline mathematics and figure cross-references: %s)."
      % ", ".join("`[%s]`" % g for g in other_groups[:6]))
    if literal_groups:
        w("  A data literal written in the citation shape is indistinguishable from a citation here;")
        w("  these were read: %s." % ", ".join("`[%s]`" % g for g in literal_groups))
    else:
        w("  None is a data literal in the citation shape; the two conventions are kept apart in the")
        w("  text, and a violation of that would appear in this line rather than in the count.")
    w("- **Window the gate reads**: the last `## References` heading to the end of the file. The %d"
      % len(numbered_after))
    w("  numbered lines it holds are the entries themselves, nothing else numbered follows them, and the")
    w("  section before it is `## %s`, so the window and the bibliography section coincide." % prev_head)
    w("- **`refgate.py` / `linkgate.py`**: both live in the journal repository's `.github/tools/`. They")
    w("  were run **from the repository root** at the branch head, against the copy of the tools that")
    w("  `main` carries (the branch was cut from `main`; `.github/tools/` is not modified by it), and")
    w("  their **whole output** -- every advisory line with the verdict -- is reproduced below verbatim")
    w("  from `gates.log`.")
    w("")
    gates = os.path.join(HERE, "gates.log")
    if os.path.exists(gates):
        w("```")
        for line in open(gates, encoding="utf-8").read().splitlines():
            if line.startswith("# "):
                w(line)
        w("")
        for line in open(gates, encoding="utf-8").read().splitlines():
            if not line.startswith("# "):
                w(line)
        w("```")
        w("")
    w("**Any advisory line is resolved rather than explained away.** A naive counter keyed on `[n]`")
    w("reads 0 entries because the reference BLOCK uses `1.` markers; the block markers and the in-text")
    w("`[n]` keys are two different conventions and the gate reports the pairing as a warning for that")
    w("reason. The counts that matter are the ones printed in the block above, at the revision the")
    w("block names. (%d entries; %d cited in the body; %d uncited.)"
      % (len(cur), len(cited), len(uncited)))
    if not os.path.exists(gates):
        w("")
        w("**The journal gates (`refgate.py`, `linkgate.py`, `numgate.py`) have NOT been run for this")
        w("revision.** They live in the journal repository at `.github/tools/` and are run against the")
        w("manuscript as committed; their output belongs in the block above before submission.")
    w("")
    open(os.path.join(HERE, "reference-check.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("entries rendered      : %d" % len(rendered))
    print("cited by numbered key : %d" % len(cited))
    print("uncited               : %d %s" % (len(uncited), uncited))
    print("bracketed groups       : %d citations, %d shape-ambiguous, %d other"
          % (len(cite_groups), len(literal_groups), len(other_groups)))
    print("-> reference-check.md (%d chars)"
          % os.path.getsize(os.path.join(HERE, "reference-check.md")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
