#!/usr/bin/env python3
"""#93 R416 -- stage 2's checks: read every number the stage-2 notes quote back out of the artifacts.

The stage-2 artifacts (`refs_anchors.json`, `refs_built.json`) are claims about the bibliography, and a claim
no check can reach is decoration.  This script derives each one from the committed papers' own content, and
then MUTATES a copy per check to show the check fires -- a check that has never been seen to fail is not
evidence (this journal's verification lesson, classes 1-105).

Each check is named for the property it reads, and the mutation battery asserts the mutation CHANGED the copy
before demanding the check fail (a perturbation below the value's resolution proves nothing, R415 class 105).

Run:  python3 refs_check.py            (checks against the artifacts as they are)
      python3 refs_check.py --selftest (checks + the battery)
"""
import copy
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import refs_selection_v93 as SEL       # noqa: E402

PLACEHOLDERS = ("n/a", "na", "todo", "tbd", "?", "...", "-", "--", "none")
# ids the selection named in an earlier draft and the pools REFUSED; none may appear in the built artifact
REFUSED = ["2609.01373", "2609.01374", "2608.24786", "10.1111/j.1749-4486.2009.02137.x"]
MIN_DIFF = 60
BAR = 100


def load():
    rep = json.loads(io.open(os.path.join(HERE, "refs_built.json"), encoding="utf-8").read())
    anc = json.loads(io.open(os.path.join(HERE, "refs_anchors.json"), encoding="utf-8").read())
    cla = json.loads(io.open(os.path.join(HERE, "refs_classic.json"), encoding="utf-8").read())
    arx_pool, doi_pool = set(), {}
    # R482: `refs_reread.json` is a pool too, so C3 ("every identifier is in a declared pool") must read it --
    # a limb the check cannot see would be a record outside the property the check asserts.
    for name in ("refs_raw.json", "refs_raw2.json", "refs_anchors.json", "refs_reread.json"):
        p = json.loads(io.open(os.path.join(HERE, name), encoding="utf-8").read())
        for blk in p["arxiv"].values():
            for r in blk["rows"]:
                arx_pool.add(r["id"])
    for _t, v in cla["queries"].items():
        m = v.get("matched")
        if m:
            doi_pool[m["doi"].lower()] = m
    return rep, anc, cla, arx_pool, doi_pool


def run_checks(rep, anc, cla, arx_pool, doi_pool):
    """Returns (name -> (ok, detail)).  One entry per property, so the battery can name which one fires."""
    out = {}
    ents = rep.get("entries", [])
    arx = [e for e in ents if e.get("source") == "arxiv"]
    doi = [e for e in ents if e.get("source") == "crossref"]

    # C1  a clean build, and no entry silently lost between selection and artifact
    out["C1-build-clean"] = (not rep.get("errors") and not rep.get("duplicate_keys")
                             and len(ents) == rep.get("n_selected_arxiv", 0) + rep.get("n_selected_doi", 0),
                             "errors %d duplicates %d entries %d of %d selected"
                             % (len(rep.get("errors", [])), len(rep.get("duplicate_keys", [])), len(ents),
                                rep.get("n_selected_arxiv", 0) + rep.get("n_selected_doi", 0)))

    # C2  every Difference is a real sentence, not a placeholder or an empty carrier
    bad = [e["key"] for e in ents
           if len(e.get("difference", "")) < MIN_DIFF or e.get("difference", "").strip().lower() in PLACEHOLDERS]
    out["C2-no-placeholder-difference"] = (not bad, "min length %d chars, placeholders %s, offenders %s"
                                                     % (MIN_DIFF, PLACEHOLDERS[:3], bad[:4]))

    # C3  every identifier is in a declared pool (the control that caught 43 recollections this round)
    miss = [e["key"] for e in arx if e["key"] not in arx_pool] + \
           [e["key"] for e in doi if e["key"].lower() not in doi_pool]
    out["C3-keys-in-pools"] = (not miss, "%d arXiv ids against %d pooled ids; %d DOIs against %d matched "
                                         "records; unresolvable %s"
                                         % (len(arx), len(arx_pool), len(doi), len(doi_pool), miss[:4]))

    # C4  the record's own fields came from the pool, and are complete
    bad = [e["key"] for e in ents if not e.get("pool_title") or not isinstance(e.get("year"), int)
           or not e.get("authors") or not e.get("venue")]
    out["C4-record-fields-complete"] = (not bad, "missing title/year/authors/venue on %s" % bad[:4])

    # C5  the URL denotes the key it sits beside (a URL that points elsewhere is the classic mismatch)
    bad = []
    for e in ents:
        if e["source"] == "arxiv":
            if e["url"] != "https://arxiv.org/abs/" + e["key"]:
                bad.append(e["key"])
        else:
            if not e["url"].lower().startswith("https://doi.org/" + e["key"].lower()):
                bad.append(e["key"])
    out["C5-url-denotes-key"] = (not bad, "%d urls checked; offenders %s" % (len(ents), bad[:4]))

    # C6  the anchor limb resolved, and it is the limb that exists BECAUSE no harvest returned those ids
    declared_anchors = [a["id"] for a in anc["declared"]]
    got = {e["key"]: e.get("pool", "") for e in arx}
    # The limb exists for the ids NO HARVEST HOLDS, so the property is exact rather than a count: every declared
    # anchor the harvest pools lack must be resolved from the anchor pool -- and there must be at least one such
    # id, or the limb is decoration.  (`>= 2 resolved from anywhere` was this check's first shape and it stopped
    # reaching its object once four anchors resolved from the limb: a plant that moved one away never crossed it.)
    harvest_ids = set()
    for name in ("refs_raw.json", "refs_raw2.json"):
        hp = json.loads(io.open(os.path.join(HERE, name), encoding="utf-8").read())
        for blk in hp["arxiv"].values():
            for r in blk["rows"]:
                harvest_ids.add(r["id"])
    limb_only_expected = [i for i in declared_anchors if i not in harvest_ids]
    resolved_from_limb = [i for i in declared_anchors if "refs_anchors" in got.get(i, "")]
    missing_from_limb = [i for i in limb_only_expected if i not in resolved_from_limb]
    anc_errs = anc.get("errors", [])
    out["C6-anchor-limb"] = (not anc_errs and not missing_from_limb and len(limb_only_expected) >= 1,
                             "declared %d; of these the harvest pools lack %s and the limb resolved %s; "
                             "missing %s; limb errors %d"
                             % (len(declared_anchors), limb_only_expected, resolved_from_limb,
                                missing_from_limb, len(anc_errs)))

    # C7  the refused identifiers are ABSENT from the artifact (what the round dropped stays dropped)
    present = [r for r in REFUSED if any(e["key"].lower() == r.lower() for e in ents)]
    out["C7-refused-ids-absent"] = (not present, "refused %d, present %s" % (len(REFUSED), present))

    # C8  the artifact is exactly the selection: same keys, same order, nothing skipped or invented
    sel_arx = [i for i, _ in SEL.ARXIV]
    sel_doi = [i.lower() for i, _ in SEL.DOI]
    same = ([e["key"] for e in arx] == sel_arx
            and sorted(e["key"].lower() for e in doi) == sorted(sel_doi)
            and len(sel_doi) == len(set(sel_doi)) and len(sel_arx) == len(set(sel_arx)))
    out["C8-artifact-equals-selection"] = (same, "selection %d arXiv + %d DOI; artifact %d + %d; arXiv order "
                                                  "identical %s"
                                                  % (len(sel_arx), len(sel_doi), len(arx), len(doi),
                                                     [e["key"] for e in arx] == sel_arx))

    # C9  the house title form, read as the bar states it: **title case** (the first word capitalised).  The
    # bar's component list does not include a full stop, and a registry title that carries one is the record's
    # own property rather than a defect: #87's published bibliography prints 1 of its 44 Crossref titles that
    # way (`Theory of Reproducing Kernels.`), so this check COUNTS the trailing periods instead of policing
    # them -- a check that demands more than its bar states is the same over-reach as one that demands less.
    bad = [e["key"] for e in ents if not e["title"].strip() or not e["title"][:1].isupper()]
    period = [e["key"] for e in ents if e["title"].rstrip().endswith(".")]
    out["C9-title-form"] = (not bad, "not title-cased or empty: %s; for the record, %d of %d titles carry the "
                                     "record's own terminal period (#87 published 1 of 44)"
                                     % (bad[:4], len(period), len(ents)))

    # C10 the Difference is written as a sentence (the house entry form ends with it)
    bad = [e["key"] for e in ents
           if not e["difference"][:1].isupper() or not e["difference"].rstrip().endswith(".")]
    out["C10-difference-is-a-sentence"] = (not bad, "offenders %s" % bad[:4])

    # C11 the journal's reference floor
    out["C11-reference-floor"] = (len(ents) >= BAR, "%d entries against the bar of %d" % (len(ents), BAR))

    # C12 no id carries both limbs (a DOI that is also an arXiv id would double-count a work)
    both = set(e["key"] for e in arx) & set(e["key"].lower() for e in doi)
    out["C12-limbs-disjoint"] = (not both, "shared keys %s" % sorted(both)[:4])

    # C15 the REGISTRATION's anchor table is a carrier of this bibliography's completeness: every work it
    # names is a work the paper's evidence base rests on, so each must be (a) declared in the anchor limb and
    # (b) actually selected.  Found in R417 by reading that table rather than this artifact: `2608.24569` was
    # fetched but never selected, and `2609.15576` was in no pool and no limb at all -- while the manuscript's
    # external-validation arm cites both.  A check whose object is the paper's own evidence base, not the list.
    heil = io.open(os.path.join(HERE, "..", "heilmeier.md"), encoding="utf-8").read()
    blk = re.search(r"## 2\. Anchor table.*?(?=\n## )", heil, re.S)
    reg_ids = list(dict.fromkeys(re.findall(r"\b(\d{4}\.\d{4,5})\b", blk.group(0)))) if blk else []
    declared = [a["id"] for a in anc.get("declared", [])]
    sel_ids = set(e["key"] for e in arx) | set(e["key"].lower() for e in doi)
    not_declared = [i for i in reg_ids if i not in declared]
    not_selected = [i for i in reg_ids if i not in sel_ids]
    out["C15-registration-anchors-covered"] = (
        bool(reg_ids) and not not_declared and not not_selected,
        "the registration's anchor table names %d works; absent from the anchor limb %s; absent from the "
        "bibliography %s" % (len(reg_ids), not_declared, not_selected))

    # C13 each arXiv entry names which pool resolved it, and the counts partition the limb
    miss_pool = [e["key"] for e in arx if not e.get("pool") or e["pool"] == "?"]
    by_pool = {}
    for e in arx:
        by_pool[e.get("pool", "?")] = by_pool.get(e.get("pool", "?"), 0) + 1
    out["C13-pool-provenance"] = (not miss_pool and sum(by_pool.values()) == len(arx),
                                  "%d arXiv entries over %d pool labels, unlabelled %s"
                                  % (len(arx), len(by_pool), miss_pool[:4]))
    return out


def check_notes(rep, anc, cla, n_checks, n_muts):
    """C14 -- the notes quote numbers, and a quoted number is a carrier of a claim: read each back from the
    artifact that owns it (this journal's rule -- a count with several carriers needs one owner and a checker,
    never an edit).  The one figure that no artifact can own is the refusal count of THIS round's first run,
    and the check therefore demands its provenance marker beside it."""
    p = os.path.join(HERE, "NOTES.md")
    text = io.open(p, encoding="utf-8").read()
    # NOTES.md is a file of per-round sections, and a number stated in it is either CURRENT (it must match the
    # artifact that owns it) or HISTORICAL (marked with its epoch, `(at R417`), in which case it is the record
    # and must NOT be re-checked: the round that wrote it is the round it was true in.  So the read is
    # FILE-WIDE and the rule is per READING.  Two earlier shapes were each wrong: checking only the newest
    # carrier compared the artifact against the REFUSING run's build line (class 105), and demanding that the
    # newest section restate every pipeline number made each round duplicate the file to keep a check green.
    secs = re.split(r"\n(?=# )", text)
    stage2 = text
    sec_title = "%d sections" % len(secs)
    ents = rep["entries"]
    n_arx = sum(1 for e in ents if e["source"] == "arxiv")
    n_doi = sum(1 for e in ents if e["source"] == "crossref")
    matched = sum(1 for _t, v in cla["queries"].items() if v.get("matched"))
    shared = [c for c in anc["checks"] if c["id"] == "C3-cross-source-agreement"][0]
    checks, bad = [], []

    def read(pattern, expect, label):
        """Every reading the file carries is checked, EXCEPT one carrying an epoch marker: an epoch-marked
        value is the record of the round it was true in (`33 citations (at R417)` while the manuscript reads 34
        today), so it is neither re-checked nor silently skipped -- epoch readings are counted and reported."""
        ms = list(__import__("re").finditer(pattern, stage2))
        current, epoch = [], []
        for mm in ms:
            tail = stage2[mm.end():mm.end() + 140]
            (epoch if re.match(r"\s*\(at R\d", tail) else current).append(tuple(int(x) for x in mm.groups()))
        ok = all(v == tuple(expect) for v in current)
        checks.append(("%s (%d current, %d epoch)" % (label, len(current), len(epoch)),
                       current[-1] if current else None, tuple(expect), ok))
        if not ok:
            bad.append("%s: notes %s vs artifact %s"
                       % (label, [v for v in current if v != tuple(expect)], tuple(expect)))

    read(r"built (\d+) of (\d+) selected entries \((\d+) arXiv \+ (\d+) DOI\)",
         (len(ents), len(ents), n_arx, n_doi), "build line")
    read(r"(\d+) are selected; (\d+) are excluded", (n_doi, matched - n_doi), "DOI selection")
    read(r"C3 cross-source: shared (\d+), agree (\d+), disagree (\d+)",
         (shared["n_shared"], shared["shared"], len(shared["disagree"])), "anchor cross-source")
    read(r"(\d+) checks, (\d+)/(\d+) PASS; (\d+) mutations, (\d+)/(\d+) caught",
         (n_checks, n_checks, n_checks, n_muts, n_muts, n_muts), "verdict line")

    # A refusal figure is a claim about a RUN, and the round that fixes the selection cannot re-derive it from
    # the artifact (`refs_built.json` is overwritten by every run).  The clause is TWO-SIDED and both sides are
    # non-vacuous: a section that STATES a refusal figure must carry the provenance marker **in that same
    # section** (a marker elsewhere in the file is another section's business -- the first version of this
    # clause was file-wide, and the battery's plant then went MISSED because R416's marker satisfied a figure
    # appended at the end of the file); a file that states NO figure is read against the run log's latest
    # record, which must then be a clean run.
    log = [json.loads(l) for l in io.open(os.path.join(HERE, "refs_build_log.jsonl"), encoding="utf-8")]
    last = log[-1]
    figs, no_marker = 0, []
    for sec in secs:
        if re.search(r"\d+ of \d+ identifiers were refused", sec):
            figs += 1
            if "refs_build_log.jsonl" not in sec:
                no_marker.append(sec.split("\n")[0][:44])
    if figs:
        ok_hist = not no_marker
        got = (figs, len(no_marker))
        expect = (figs, 0)
        why = ("a refusal figure is a claim about a run and its provenance marker belongs in its own section: "
               "%d section(s) state a figure, %d of them miss the marker (%s)" % (figs, len(no_marker), no_marker))
    else:
        ok_hist = last["n_errors"] == 0 and not last["duplicate_keys"]
        got = (last["n_errors"], len(last["duplicate_keys"]))
        expect = (0, 0)
        why = ("no refusal figure anywhere in this file; the run log's latest record (%s) has %d errors and %d "
               "duplicate keys" % (last["at"], last["n_errors"], len(last["duplicate_keys"])))
    checks.append(("refusal figure (or a clean run log)", got, expect, ok_hist))
    if not ok_hist:
        bad.append(why)
    if not ok_hist:
        bad.append(why)

    # The manuscript's citation numbers are owned by the manuscript's own checker, so they are RE-DERIVED
    # through it rather than counted here (one owner per count; never a second reckoning).
    # Two layouts, both named explicitly: in the WORKING tree the manuscript checker sits in `../manuscript`
    # beside the parts, and in the shipped PACKAGE it sits in the parent directory beside the product.  Both are
    # inserted because relying on either -- or on the caller's working directory, which is what made this import
    # succeed by accident on the authoring machine -- is a reading whose object depends on where it was run from.
    for _cand in (os.path.join(HERE, "..", "manuscript"), os.path.dirname(HERE)):
        if _cand not in sys.path:
            sys.path.insert(0, _cand)
    import cite_check                                                     # noqa: E402
    kman = cite_check.load_keys()
    texts_ = [(os.path.basename(q), io.open(q, encoding="utf-8").read()) for q in cite_check.PARTS]
    # The product cites the number the bibliography prints; the index resolves it.  Without it the citation line
    # reads `0 citations, 0 distinct keys` on the shipped package (R481).
    idx_, _un_ = cite_check.num_index(texts_, kman)
    order_, occ_ = cite_check.scan(texts_, idx_)
    read(r"(\d+) citations, (\d+) distinct keys of (\d+) built records",
         (len(occ_), len([k for k in order_ if k in kman]), len(kman)),
         "manuscript citation line read by %s" % os.path.relpath(cite_check.__file__, os.path.dirname(HERE)))

    ok_log = any(r["n_entries"] == len(ents) and r["n_errors"] == 0 and not r["duplicate_keys"] for r in log)
    checks.append(("the run log holds this round's clean run", (len(log), ok_log), (">=1", True), ok_log))
    if not ok_log:
        bad.append("refs_build_log.jsonl holds no record of a clean run at the current entry count")
    return (not bad, "; ".join("%s -> %s (expect %s)" % (a, b, c) for a, b, c, _ok in checks) if bad
            else "%d numbers read back from the artifacts across %s: %s; refusal figure carries its "
                 "provenance marker" % (len(checks), sec_title, [c[0] for c in checks]))


def battery(rep, anc, cla, arx_pool, doi_pool):
    """One mutation per check; each must CHANGE the copy and then be caught by the check it names."""
    ents = rep["entries"]
    muts = [
        ("C1-build-clean", lambda r: r["entries"].append(dict(ents[0]))),
        ("C1-build-clean", lambda r: r.__setitem__("duplicate_keys", [ents[0]["key"]])),
        ("C2-no-placeholder-difference", lambda r: r["entries"][0].__setitem__("difference", "N/A")),
        ("C2-no-placeholder-difference", lambda r: r["entries"][1].__setitem__("difference", "short.")),
        ("C3-keys-in-pools", lambda r: r["entries"][0].__setitem__("key", "9999.99999")),
        ("C4-record-fields-complete", lambda r: r["entries"][2].__setitem__("year", None)),
        ("C4-record-fields-complete", lambda r: r["entries"][3].__setitem__("authors", "")),
        ("C4-record-fields-complete", lambda r: r["entries"][4].__setitem__("pool_title", "")),
        ("C5-url-denotes-key", lambda r: r["entries"][0].__setitem__("url", "https://arxiv.org/abs/2601.00001")),
        ("C6-anchor-limb", lambda r: [e.__setitem__("pool", "refs_raw.json:x") for e in r["entries"]
                                      if e["key"] == "2606.29406"]),
        ("C7-refused-ids-absent", lambda r: r["entries"].append(dict(ents[0], key="2608.24786",
                                                                     url="https://arxiv.org/abs/2608.24786"))),
        ("C8-artifact-equals-selection", lambda r: r["entries"].pop(0)),
        ("C9-title-form", lambda r: r["entries"][0].__setitem__("title", "reframing LLM Agent Security")),
        ("C10-difference-is-a-sentence", lambda r: r["entries"][0].__setitem__("difference", "x" * 80)),
        ("C11-reference-floor", lambda r: r.__setitem__("entries", r["entries"][:50])),
        # C12 needs its own plant: an arm with no case is decoration by arithmetic (every check owes one)
        ("C12-limbs-disjoint", lambda r: next(e for e in r["entries"]
                                              if e["source"] == "crossref").__setitem__("key", "2605.24309")),
        ("C13-pool-provenance", lambda r: r["entries"][0].__setitem__("pool", "")),
        # C15's two clauses, one plant each: a declared anchor dropped from the LIMB, and one dropped from the
        # BIBLIOGRAPHY.  The second is the exact shape of this round's real defect (2608.24569).
        ("C15-registration-anchors-covered",
         lambda r, a: a.__setitem__("declared", [d for d in a["declared"] if d["id"] != "2606.29406"])),
        ("C15-registration-anchors-covered",
         lambda r: r.__setitem__("entries", [e for e in r["entries"] if e["key"] != "2606.29406"])),
    ]
    rows, bad = [], []
    for name, fn in muts:
        r, a = copy.deepcopy(rep), copy.deepcopy(anc)
        before = json.dumps([r, a], sort_keys=True)
        if fn.__code__.co_argcount == 2:      # a two-argument plant reaches the limb's DECLARATION
            fn(r, a)
        else:
            fn(r)
        after = json.dumps([r, a], sort_keys=True)
        if before == after:
            rows.append((name, "MUTATION INERT", "the mutation did not change the copy"))
            bad.append(name)
            continue
        got = run_checks(r, a, cla, arx_pool, doi_pool)
        ok, detail = got[name]
        rows.append((name, "caught" if not ok else "MISSED", detail[:96]))
        if ok:
            bad.append(name)
    return rows, bad


def battery_note_free(rep, anc, cla, arx_pool, doi_pool):
    rows, bad = battery(rep, anc, cla, arx_pool, doi_pool)
    return rows, bad


def main():
    rep, anc, cla, arx_pool, doi_pool = load()
    got = run_checks(rep, anc, cla, arx_pool, doi_pool)
    rows, bad_muts = battery_note_free(rep, anc, cla, arx_pool, doi_pool)
    got["C14-notes-numbers-read-back"] = check_notes(rep, anc, cla, len(got) + 1, len(rows) + 3)
    n_ok = sum(1 for v in got.values() if v[0])
    for k in sorted(got, key=lambda s: int(s.split("-")[0][1:])):
        ok, detail = got[k]
        print("  %-32s %-4s %s" % (k, "PASS" if ok else "FAIL", detail))
    print("\nchecks %d/%d PASS" % (n_ok, len(got)))
    rc = 0 if n_ok == len(got) else 1
    if "--selftest" in sys.argv:
        rows, bad = rows, list(bad_muts)
        rows = [(n, v, d) for n, v, d in rows]
        n_mut = len(rows)
        # the notes' own mutations: a quoted number changed, and the provenance marker removed
        # A plant is aimed at the CURRENT section's text; when a later round changes the artifact, the plant
        # that targeted the previous round's numbers becomes inert.  (Both misaimed plants this round were found
        # by the battery reporting MUTATION-as-MISS, not by reading.)
        for label, fn in (("note build line",
                           lambda t: t.replace("built 121 of 121 selected entries (75 arXiv + 46 DOI)",
                                               "built 120 of 121 selected entries (74 arXiv + 46 DOI)")),
                          ("note cross-source numbers",
                           lambda t: t.replace("shared 4, agree 4, disagree 0", "shared 3, agree 4, disagree 0")),
                          ("note refusal figure w/o provenance",
                           lambda t: t.rstrip("\n") + "\n\n(stage-3 note: 12 of 130 identifiers were refused.)\n")):
            t0 = io.open(os.path.join(HERE, "NOTES.md"), encoding="utf-8").read()
            t1 = fn(t0)
            if t0 == t1:
                rows.append(("C14-notes-numbers-read-back", "MUTATION INERT", label))
                bad.append("C14-notes-numbers-read-back")
                continue
            backup = t0
            io.open(os.path.join(HERE, "NOTES.md"), "w", encoding="utf-8").write(t1)
            try:
                ok, detail = check_notes(rep, anc, cla, len(got), n_mut + 3)
            finally:
                io.open(os.path.join(HERE, "NOTES.md"), "w", encoding="utf-8").write(backup)
            rows.append(("C14-notes-numbers-read-back", "caught" if not ok else "MISSED", label + ": " + detail[:70]))
            if ok:
                bad.append("C14-notes-numbers-read-back")
        print("\nmutation battery (%d mutations, one per check):" % len(rows))
        for name, verdict, detail in rows:
            print("  %-32s %-8s %s" % (name, verdict, detail))
        print("  caught %d/%d" % (len(rows) - len(bad), len(rows)))
        if bad:
            print("  MISSED/INERT: %s" % bad)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
