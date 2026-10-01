#!/usr/bin/env python3
"""#93 R416 -- build the bibliography's records from the committed pools, in the journal's house entry form.

Input :  refs_selection_v93.py  (the AUTHORED selection: identifier -> one-line Difference)
         refs_raw.json / refs_raw2.json / refs_classic.json  (the harvest; each entry keeps `pool_title`, the
         title the difference line was written against, so a later read can check the live record still bears it)
Output:  refs_built.json

House entry form (README -> presentation requirements): `[n] ` authors (`Family, I.`; `et al.` for four or
more) -- the year in parentheses -- the title in title case -- the venue or identifier -- a resolvable URL --
the entry closing with its one-line `Difference: ...`.

The record's own fields are never typed by hand: the pipeline refuses a field it cannot resolve (an identifier
that is not in the pool is an ERROR, which is the control that caught two hand-typed ids in this journal's
previous bibliography, R404).  The house-form helpers are this journal's own (`papers/issue-87/artefacts/refs/
refs_build_v87.py`), copied here so this package is self-contained.
"""
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import refs_selection_v93 as SEL       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "refs_built.json")

SMALL = {"a", "an", "the", "and", "but", "or", "for", "nor", "of", "on", "in", "to", "with", "at", "by",
         "from", "as", "into", "over", "under", "vs", "via", "per"}
KEEP_UPPER = re.compile(r"^[A-Z0-9]{2,}$|^[A-Z][a-z]*[A-Z]")


def title_case(s):
    """Title case that leaves acronyms alone (MCP, LLM, TOCTOU, BPF)."""
    words = (s or "").split()
    out = []
    for i, w in enumerate(words):
        core = w.strip("()[]{}:;,.?!\"'")
        starts_clause = i == 0 or (out and out[-1][-1:] in "?.!:")
        if KEEP_UPPER.match(core):
            out.append(w)
        elif core.lower() in SMALL and not starts_clause and i != len(words) - 1:
            out.append(w.lower())
        elif "-" in core and len(core) > 1:
            out.append("-".join(p[:1].upper() + p[1:] if p and not KEEP_UPPER.match(p) else p
                                for p in w.split("-")))
        else:
            out.append(w[:1].upper() + w[1:] if w else w)
    return " ".join(out)


def family_initial(name):
    """Two record shapes: 'Yunseo Hwang' and 'Hwang, Yunseo'.  A mononym keeps its lone token."""
    s = (name or "").strip()
    if not s:
        return ""
    if ", " in s:
        fam, given = s.split(", ", 1)
        given = given.strip()
        return "%s, %s." % (fam.strip(), given[0].upper()) if given else fam.strip()
    parts = s.split()
    if len(parts) == 1:
        return parts[0] + "."
    return "%s, %s." % (parts[-1], parts[0][0].upper())


def author_string(names, n_authors=None):
    """House form: `Family, I.`; `et al.` for four or more, one period."""
    if not names:
        return ""
    n = n_authors if n_authors else len(names)
    if n >= 4:
        return family_initial(names[0]) + " et al."
    return ", ".join(family_initial(x) for x in names)


def load_pools():
    """Three sources, and the third is not decoration: the registration's anchors were read by ID at
    registration and live in no keyword harvest, so without `refs_anchors.json` a bibliography that cites
    its own registration's anchors cannot resolve them -- measured this round as 3 of the 43 errors."""
    arxiv, doi, sources = {}, {}, {}
    # `refs_reread.json` joined in R482 and it OVERRIDES.  It carries (A) a work that appeared AFTER the
    # registration and after the harvests closed, so it is in neither pool, and (B) an id whose pool title no
    # longer matches the live record -- the check that `pool_title` exists for, run this round, which fired.
    # A later reading wins on the FIELDS (the bibliography must cite the title the link now shows); the
    # provenance label stays with the pool that first found the id, because that fact has not changed.
    for name in ("refs_raw.json", "refs_raw2.json", "refs_anchors.json", "refs_reread.json"):
        pool = json.loads(io.open(os.path.join(HERE, name), encoding="utf-8").read())
        for label, blk in pool["arxiv"].items():
            for r in blk["rows"]:
                if r["id"] not in arxiv:
                    arxiv[r["id"]] = r
                    sources[r["id"]] = name + ":" + label
                elif name == "refs_reread.json":
                    arxiv[r["id"]] = r
    classic = json.loads(io.open(os.path.join(HERE, "refs_classic.json"), encoding="utf-8").read())
    for _title, v in classic["queries"].items():
        m = v.get("matched")
        if m:
            doi[m["doi"].lower()] = dict(doi=m["doi"], title=m["title"], year=m["year"],
                                         authors=m.get("authors"), n_authors=m.get("n_authors"),
                                         venue=m.get("venue"), type=m.get("type"),
                                         url="https://doi.org/" + m["doi"])
    return arxiv, doi, sources


def main():
    arxiv, doi, sources = load_pools()
    entries, errors = [], []
    n_by_source = {}
    # The selection is a FIELD, and it is read two-sided before anything is built.  R424: R416 recorded a refusal
    # as a sentence inside the `difference` line of a row that sat in `ARXIV`, and this loop -- which takes every
    # row of a selection table as selected -- built it into the bibliography.  Neither side of the property is
    # optional: a not-selected id in a selected table is the defect that happened, and a selected id parked in the
    # not-selected register would silently DROP a work the study cites.
    selected_ids = [i for i, _d in SEL.ARXIV] + [i for i, _d in SEL.DOI]
    not_selected_ids = [i for i, _r in SEL.NOT_SELECTED]
    for ident in not_selected_ids:
        if ident in selected_ids:
            errors.append(dict(source="selection", id=ident,
                               why="declared NOT_SELECTED and also present in a selected table"))
    for ident in selected_ids:
        if ident in not_selected_ids:
            errors.append(dict(source="selection", id=ident,
                               why="selected and also declared NOT_SELECTED"))
    if len(set(selected_ids)) != len(selected_ids):
        for ident in sorted({i for i in selected_ids if selected_ids.count(i) > 1}):
            errors.append(dict(source="selection", id=ident, why="present twice in the selected tables"))
    if errors:
        for e in errors:
            print("  ERR %s %s: %s" % (e["source"], e["id"], e["why"]))
        print("selection integrity failed: %d error(s); nothing written" % len(errors))
        return 1
    for src, pairs in (("arxiv", SEL.ARXIV), ("doi", SEL.DOI)):
        for ident, difference in pairs:
            rec = arxiv.get(ident) if src == "arxiv" else doi.get(ident.lower())
            if rec is None:
                errors.append(dict(source=src, id=ident, why="not found in the committed pools"))
                continue
            # Provenance label.  The DOI limb resolved through `load_pools`'s Crossref branch, whose labels are
            # keys of `sources` (arxiv ids) -- so `sources.get(ident, "?")` labelled all 46 of them "?", a
            # provenance field that named nothing.  A label with no owner is the same defect as a count with two.
            label = sources.get(ident, "refs_classic.json:crossref-doi" if src == "doi" else "?")
            n_by_source[label] = n_by_source.get(label, 0) + 1
            if src == "arxiv":
                e = dict(source="arxiv", key=ident, url="https://arxiv.org/abs/" + ident,
                         pool=sources.get(ident, "?"),
                         pool_title=rec["title"], authors_raw=rec["authors"], year=rec["year"],
                         venue="arXiv:%s" % ident, primary=rec.get("primary", ""))
            else:
                e = dict(source="crossref", key=rec["doi"], url=rec.get("url") or ("https://doi.org/" + rec["doi"]),
                         pool_title=rec["title"], authors_raw=rec.get("authors") or [],
                         n_authors=rec.get("n_authors"), year=rec.get("year"),
                         venue=rec.get("venue") or "Crossref record", type=rec.get("type", ""))
            e["difference"] = " ".join(difference.split())
            e["title"] = title_case(e["pool_title"])
            e["authors"] = author_string(e["authors_raw"], e.get("n_authors") or len(e["authors_raw"]))
            if not e["authors"]:
                errors.append(dict(source=src, id=ident, why="no author resolved by the pool record"))
            if not e["year"]:
                errors.append(dict(source=src, id=ident, why="no year resolved by the pool record"))
            entries.append(e)
    seen = {}
    dupes = []
    for e in entries:
        if e["key"] in seen:
            dupes.append(e["key"])
        seen[e["key"]] = e
    rep = dict(round="R416; re-run at R482", resolved_by_pool=n_by_source,
               n_selected_arxiv=len(SEL.ARXIV), n_selected_doi=len(SEL.DOI),
               n_not_selected=len(SEL.NOT_SELECTED),
               not_selected=[dict(id=i, reason=" ".join(r.split())) for i, r in SEL.NOT_SELECTED],
               n_entries=len(entries), n_unique_keys=len(seen), duplicate_keys=dupes, errors=errors,
               entries=entries)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    # Append-only run log.  `OUT` is OVERWRITTEN by every run, so a number taken from a run's stdout -- e.g.
    # this round's "43 of 115 refused" -- stops being re-readable the moment the selection is fixed.  The log
    # keeps each run's refusals: what the pipeline refused is evidence, and evidence must outlive the fix.
    with io.open(os.path.join(HERE, "refs_build_log.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(round="R416; re-run at R482", at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 n_selected_arxiv=len(SEL.ARXIV), n_selected_doi=len(SEL.DOI),
                                 n_not_selected=len(SEL.NOT_SELECTED),
                                 n_entries=len(entries), n_unique=len(seen), duplicate_keys=dupes,
                                 n_errors=len(errors),
                                 refused=[dict(source=e["source"], id=e["id"], why=e["why"]) for e in errors]),
                          sort_keys=True) + "\n")
    print("built %d of %d selected entries (%d arXiv + %d DOI) | not selected %d | unique keys %d | "
          "duplicates %d | errors %d"
          % (len(entries), len(SEL.ARXIV) + len(SEL.DOI), len(SEL.ARXIV), len(SEL.DOI),
             len(SEL.NOT_SELECTED), len(seen), len(dupes), len(errors)))
    for k in sorted(n_by_source):
        print("  resolved from %-34s %d" % (k, n_by_source[k]))
    for e in errors:
        print("  ERR %s %s: %s" % (e["source"], e["id"], e["why"]))
    return 1 if (errors or dupes) else 0


if __name__ == "__main__":
    sys.exit(main())
