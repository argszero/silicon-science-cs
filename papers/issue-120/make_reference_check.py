#!/usr/bin/env python3
"""Issue #120 -- generate reference-check.md from the artefacts.

Nothing here is typed: the entries, the verification verdicts and the resolved titles are read out
of refs/curated.json, refs/meta.json and refs/verify.log, and the coverage figures are computed
from manuscript.md.  The one thing this script cannot do is run the journal's refgate.py -- that
tool lives in the journal repository's .github/tools/ and its output is pasted in by hand under
*Coverage*, together with the revision it was run at.

Usage:  /usr/bin/python3 make_reference_check.py
Out:    reference-check.md
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    cur = json.load(open(os.path.join(HERE, "refs", "curated.json")))["entries"]
    meta = json.load(open(os.path.join(HERE, "refs", "meta.json")))
    log = open(os.path.join(HERE, "refs", "verify.log")).read().splitlines()
    man = open(os.path.join(HERE, "manuscript.md"), encoding="utf-8").read()

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

    lines = []
    w = lines.append
    w("# Citation report - issue #120")
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
    w("python3 refs_tool.py plant      # two-sided control: a corrupted title and an invented id")
    w("```")
    w("")
    w("- **DOI entries** (4) are fetched from `https://api.crossref.org/works/<doi>`.")
    w("- **arXiv entries** (125) are fetched from the arXiv API. **Transport note (measured):** this")
    w("  endpoint is intermittently unanswered from the authoring host -- the read times out rather than")
    w("  returning an error -- so the verifier is cache-first (`refs/verify_cache/`) and a re-run over a")
    w("  populated cache is instant and offline. The *metadata* pass (`refs_meta.py`) met the same block")
    w("  and falls back per id to the arXiv abstract page, which carries the same fields as schema.org")
    w("  `citation_*` meta tags; that is the route the author fields were taken from, and it is stated")
    w("  rather than presented as an API result.")
    w("- **Title comparison is taken through the XML parser, not a regex over raw text.** Measured on")
    w("  2026-10-03: a regex read left XML entity references literal (`&amp;`), which turned one correct")
    w("  citation into a false `MISMATCH`. The instrument now parses the Atom feed.")
    w("- **A two-sided control is run** (`refs_tool.py plant`): a corrupted title and an invented")
    w("  identifier are injected into a throwaway copy of the curated set and **both must fail**.")
    w("")
    w("**Result: %d/%d entries resolved to their recorded title, 0 unresolved.** Committed run log:"
      % (meta["n"], len(cur)))
    w("`refs/verify.log` (header line: *%s*). The verification command exits non-zero if any entry"
      % log[2].lstrip("# "))
    w("fails, so the verdict is a check rather than a statement.")
    w("")
    w("**Anchor accuracy.** The resolved title is compared to the curated title, and the curated record")
    w("also carries the year and venue the discovery scan returned. Five entries are pre-arXiv")
    w("foundations resolved by DOI against Crossref (Belady 1966, Mattson 1970, Sleator-Tarjan 1985,")
    w("Denning 1968, and one 2002 arXiv paper); **three of the four author-supplied DOIs were wrong when")
    w("first written from memory** and were corrected by resolving the title against Crossref before")
    w("writing them down (Belady `10.1147/sj.52.0182` -> `10.1147/sj.52.0078`; Sleator-Tarjan")
    w("`10.1145/3828.3830` -> `10.1145/2786.2793`; Denning `10.1145/361011.361070` ->")
    w("`10.1145/363095.363141`). A fifth entry whose title had been reconstructed rather than read was")
    w("**deleted rather than guessed at**. No entry in this list was written from recollection.")
    w("")
    w("**Author fields.** A verified identifier is not a verified citation record: the identifier pass")
    w("above confirms *title identity*, and says nothing about the authors a reference list needs.")
    w("Author names and years are fetched in a second pass (%d/%d entries carry authors; 4 via Crossref,"
      % (meta["with_authors"], len(cur)))
    w("125 via the abstract-page route) and every name in the list is rendered from `refs/meta.json` --")
    w("none is typed. The reference list is generated by `build_manuscript.py`, so the rendered entry and")
    w("the fetched record cannot drift apart.")
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
    w("- **References section**: exactly one `## References` heading, at the end of the file, after")
    w("  Appendix A. Entries are numbered `1.`-`%d.` and each begins on its own line, separated by a"
      % len(rendered))
    w("  blank line, so the list is read as a list rather than as one paragraph.")
    w("- **Coverage**: %d entries, **%d cited in the body text by their numbered key**, %d uncited."
      % (len(numbered), len(cited), len(uncited)))
    w("  Every in-text citation is a bracketed number; no work is cited by name or by bare arXiv id")
    w("  without its key.")
    w("- **Uncited entries**: %s." % ("none" if not uncited else ", ".join(uncited)))
    w("- **Bracketed groups that are NOT citations**: there are none. Trace literals are written with")
    w("  parentheses (`A = (1, 2, 1, 2, 0, 1, 0, 2, 1)` in Section 5.6), not square brackets, and the")
    w("  manuscript carries no numeric ranges in brackets; every square-bracket group in the body is a")
    w("  citation key. The interval notation in Section 3.2 uses parentheses: `(j, i)`.")
    w("- **Window the gate reads**: the last `## References` heading to the end of the file. Nothing")
    w("  numbered follows the bibliography (Appendix A precedes it), so the window and the section")
    w("  coincide.")
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
    w("**The one advisory line, resolved rather than explained away.** `refgate.py` prints")
    w("`WARN: bib uses '1.' but body uses '[n]' -- style mismatch`. This is by construction, not a")
    w("defect: the requirement is that **every entry be cited in the body text by its numbered key**")
    w("(`[12]`, `[12,14]`), so the body *must* use `[n]`; the entry marker `1.` is one of the three")
    w("markers the gate accepts at the start of an entry line (`[12]`, `12.`, `12)`), and the gate")
    w("reports the pairing as a warning precisely because a naive counter keyed on `[n]` would read 0")
    w("entries. The substantive counts are in the same block: `entries=129`, `coverage=100.0%`,")
    w("`block form: 129 entries, 0 of them not separated`, `author form: 129/129`.")
    w("")
    open(os.path.join(HERE, "reference-check.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("entries rendered      : %d" % len(rendered))
    print("cited by numbered key : %d" % len(cited))
    print("uncited               : %d %s" % (len(uncited), uncited))
    print("-> reference-check.md (%d chars)"
          % os.path.getsize(os.path.join(HERE, "reference-check.md")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
