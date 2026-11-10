#!/usr/bin/env python3
"""check_claims.py -- read the artefact back and test the claims the paper makes about it.

A paper's sentences are claims about numbers, and a number that no program re-checks will drift
away from the sentence that describes it. This program is that check: it reads
`results/mechanism.json` and asserts, mechanically, the statements the manuscript will carry. If a
claim stops holding -- because a cell changed, or because a run was made on a different corpus --
this exits 1 and the reproduction fails.

Two of the checks are the instrument's endpoint controls, and they are the reason the table means
anything: an instrument that cannot return "fully identified" on input where the answer is known,
and cannot return "maximally unidentified" on constructed input, has not been shown to measure
either, and any number it produces elsewhere is uninterpreted.

Reads : results/mechanism.json
Exit  : 0 all claims hold; 1 a claim does not hold or the artefact is missing.
"""
import json
import sys

FAILED = 0


def check(name, ok, detail=""):
    global FAILED
    print("  [%s] %s%s" % ("ok" if ok else "FAIL", name, (" -- " + detail) if detail else ""))
    if not ok:
        FAILED += 1


def main():
    try:
        d = json.load(open("results/mechanism.json"))
    except FileNotFoundError:
        print("  [FAIL] results/mechanism.json is missing -- run run_mechanism.py first")
        return 1

    cells = d["cells"]
    try:
        scale = json.load(open("results/scale.json"))
    except FileNotFoundError:
        scale = None
    try:
        medium = json.load(open("results/medium.json"))
    except FileNotFoundError:
        medium = None
    by = {c["tag"]: c for c in cells}
    corpus = d["corpus"]
    n = corpus["n"]
    fams = [c for c in cells if c["tag"].split("/")[0] in ("Hamming", "PQ", "SQ")]

    print("claims about results/mechanism.json (%d x %d corpus, %d queries, k=%d)"
          % (n, corpus["d"], corpus["n_queries"], corpus["k"]))

    # ---- endpoint control 1: identified where the answer is known -------------------------
    fl = by["float/raw descriptors"]
    check("float endpoint is fully identified (median boundary tie group == 1)",
          fl["median_t"] == 1, "median_t=%s" % fl["median_t"])
    check("float endpoint floor == 1.0000", fl["mean_floor"] == 1.0, "mean_floor=%s" % fl["mean_floor"])

    # ---- endpoint control 2: maximally unidentified on constructed input ------------------
    cn = by["constructed/all points identical"]
    check("constructed endpoint puts every point in one tie group",
          cn["median_t"] >= n - 1, "median_t=%s of n=%d" % (cn["median_t"], n))
    check("constructed endpoint floor == 0.0000", cn["mean_floor"] == 0.0, "mean_floor=%s" % cn["mean_floor"])

    # ---- the axis ------------------------------------------------------------------------
    check("the axis orders the table (log-log Pearson < -0.9)",
          d["log_log_pearson"] < -0.9, "r=%.4f over %d cells" % (d["log_log_pearson"], len(fams)))
    coarsest = min(fams, key=lambda c: c["median_atoms"])
    finest = max(fams, key=lambda c: c["median_atoms"])
    check("the coarsest cell has the largest tie group",
          coarsest["median_t"] >= finest["median_t"],
          "%s t=%s vs %s t=%s" % (coarsest["tag"], coarsest["median_t"],
                                  finest["tag"], finest["median_t"]))

    # ---- the count is stated, and stated as what it is ------------------------------------
    configs = {tuple(c["tag"].split("/")[:2]) for c in fams}
    check("every family cell declares its query count",
          all(c["n_queries"] == corpus["n_queries"] for c in fams))
    print("  [info] %d seed-level cells over %d distinct (family, budget) configurations"
          % (len(fams), len(configs)))
    print("  [info] seeds are not independent confirmations: the cell count is the seed count, "
          "the configuration count is the evidence count")

    # The manuscript prints a configuration count beside each correlation. That count must come from
    # the same set the correlation was composed over, so this compares the generator's own function
    # (imported, not re-implemented here) against the set composed above. Counting the two endpoint
    # controls as configurations -- what the manuscript did until review M1 -- fails this line.
    import make_manuscript
    check("the printed configuration count is over the family cells, not the controls",
          make_manuscript.configs_of(cells) == len(configs),
          "manuscript prints %d, the correlations are composed over %d"
          % (make_manuscript.configs_of(cells), len(configs)))
    try:
        scale = json.load(open("results/scale.json"))
        b_configs = {tuple(c["tag"].split("/")[:2])
                     for c in scale["cells"] if make_manuscript.is_family_cell(c)}
        check("tier B's printed configuration count is over the family cells too",
              make_manuscript.configs_of(scale["cells"]) == len(b_configs),
              "manuscript prints %d, the cells carry %d"
              % (make_manuscript.configs_of(scale["cells"]), len(b_configs)))
    except FileNotFoundError:
        check("tier B's configuration count", False,
              "results/scale.json is missing -- this check has NOT RUN, it is not a pass")

    # ---- the statistic and its threshold sit on the same denominator ----------------------
    # Section 8 calls the configuration count the evidence count, and a threshold computed over the
    # seed-level cells is then a threshold for a different design (review M2). The pair is now stored
    # in the artefact, and this asserts the stored pair still equals what the cells compose to --
    # so a re-run that moved the cells without moving the stored pair, or a stored pair typed by
    # hand, fails here rather than in a reader's recomputation.
    import axis
    for label, art in (("A", d), ("B", scale), ("M", medium)):
        if art is None:
            continue
        composed = axis.at_evidence_count(art["cells"])
        check("%s: the stored axis is the one the committed cells compose" % label,
              all(art[k] == composed[k] for k in composed),
              "stored %s vs composed %s"
              % ({k: art[k] for k in composed}, composed))
        check("%s: the correlation clears the threshold at the evidence count" % label,
              abs(composed["log_log_pearson_configs"]) > composed["mde_pearson_configs"],
              "|r|=%.4f over %d configurations vs MDE=%.4f"
              % (abs(composed["log_log_pearson_configs"]), composed["n_configs"],
                 composed["mde_pearson_configs"]))

    # ---- tier M: the scale axis a reader can recompute from committed bytes ----------------
    # Review M4: the 1M number's only path used to be a 501 MB fetch, so it was read from an
    # artefact and re-derived nowhere. The 200k fixture gives it a second instrument, and what
    # makes that instrument a CHECK rather than a second opinion is that the tiers are nested:
    # tier A's descriptors are the head of tier M's train block, so the three scales are views of
    # one inclusion chain and a sentence comparing them compares one population. The array-level
    # comparison is `run_scale.py --medium`'s (it holds both files and numpy); this asserts the
    # binding the ARTEFACTS carry, so a rebuild of either fixture that moved the relation fails
    # here as well as there.
    if medium is None:
        check("tier M: the 200k artefact exists", False,
              "results/medium.json is missing -- this check has NOT RUN, it is not a pass")
    else:
        m_fam = {tuple(c["tag"].split("/")[:2]) for c in medium["cells"]
                 if make_manuscript.is_family_cell(c)}
        check("tier M: the printed configuration count is over the family cells",
              make_manuscript.configs_of(medium["cells"]) == len(m_fam),
              "manuscript prints %d, the cells carry %d"
              % (make_manuscript.configs_of(medium["cells"]), len(m_fam)))
        check("tier M: the two committed fixtures are nested (tier A is tier M's first rows)",
              medium["fixture"]["nested_rows"] == n,
              "nested_rows=%s vs tier A's n=%d" % (medium["fixture"]["nested_rows"], n))
        check("tier M: the medium scale really is larger than tier A",
              medium["fixture"]["n"] > n,
              "M.n=%d vs A.n=%d" % (medium["fixture"]["n"], n))

    # ---- each artefact names the bytes it measured, and names the right ones ----------------
    # Review M4 gave this package a second fixture, and adding it silently changed what tier A
    # recorded: `verify_fixture.py --print-sha` printed the first `.npz` in sorted order, so
    # `mechanism.json` began stamping the MEDIUM fixture's digest while every number in it still
    # came from the 20k one. The build stayed green -- both runs of the byte comparison produced
    # the same new value -- and what noticed was `git status`. A digest is only an identity if it is
    # bound to the name it belongs to, so each artefact's stamp is compared against the pin of the
    # file that artefact is measured from.
    import verify_fixture as VF
    pins = VF.recorded()
    for label, art, key in (("A", d, "fixture_sha256"), ("M", medium, None)):
        if art is None:
            continue
        if key is None:
            path = art["fixture"]["path"]
            stamp = art["fixture"]["sha256"]
        else:
            path = VF.SUBSET
            stamp = art[key]
        check("%s: the recorded fixture digest is the pin of the fixture it measured" % label,
              pins.get(path) is not None and stamp == pins.get(path),
              "%s stamps %s..., %s is pinned at %s..."
              % (label, str(stamp)[:16], path, str(pins.get(path))[:16]))

    # ---- the figure asserts the same thing the artefacts do (review m3) --------------------
    # A picture is an assertion in a second language, and the way it goes wrong is silently: it keeps
    # rendering while the numbers under it move. `make_figure.py` writes beside the image what it
    # plotted, so the claim can be read back off the record instead of off the pixels -- and the
    # record carries the image's digest, so swapping the picture for another one also fails here.
    import make_figure as MF
    arts = {"A": d, "M": medium, "B": scale}
    missing = sorted(k for k, v in arts.items() if v is None)
    if missing:
        check("the figure's three artefacts exist", False,
              "no artefact for %s -- this check has NOT RUN, it is not a pass" % ", ".join(missing))
    else:
        try:
            plot = json.load(open(MF.DATA))
            for name, ok, detail in MF.figure_claim_holds(plot, arts):
                check(name, ok, detail)
        except FileNotFoundError:
            check("the figure's data record exists", False,
                  "%s is missing -- run make_figure.py; this check has NOT RUN" % MF.DATA)

    # ---- the absence claim's search record (review m5) --------------------------------------
    # The paper says the recall literature does not ask its question. That is falsifiable, and this
    # is where it is falsified if it ever becomes false: if the search surfaces a record that does
    # ask it, this check goes red and the paper's framing -- not the search -- has to change. The
    # other four invariants keep the record honest about its own coverage: a record nobody read, a
    # reading whose record the index no longer returns, a declared index that did not answer, and a
    # window that is not closed at both ends.
    try:
        rec = json.load(open("search/absence_search.json"))
    except FileNotFoundError:
        rec = None
    if rec is None:
        check("the absence claim's search record exists", False,
              "search/absence_search.json is missing -- run search_record.py")
    else:
        L = rec["ledger"]
        check("the search read every record its own screen put in front of it",
              L["n_unreviewed"] == 0,
              "%d of %d survivor(s) unread" % (L["n_unreviewed"], L["survived_screen"]))
        check("no recorded reading names a record the index no longer returns",
              L["n_stale"] == 0, "%d stale judgement(s)" % L["n_stale"])
        check("every declared index answered",
              not L["sources_not_run"],
              "NOT RUN: %s" % (", ".join(L["sources_not_run"]) or "none"))
        check("the window is closed at both ends and names its date field per index",
              bool(rec["window"].get("from")) and bool(rec["window"].get("to"))
              and set(rec["window"].get("date_field", {})) == set(rec["indices"]),
              "from=%s to=%s fields=%s" % (rec["window"].get("from"), rec["window"].get("to"),
                                           sorted(rec["window"].get("date_field", {}))))
        check("nothing the search returned asks what determines the width of the identified set",
              L["n_asks_width"] == 0,
              "%d of %d read record(s) ask it -- the absence claim would then be false"
              % (L["n_asks_width"], L["read_by_hand"]))

    # ---- is the measured effect above what this design could have detected? ---------------
    # A correlation a design of this size could not have seen is not evidence either way, so the
    # sensitivity is printed and asserted here rather than quoted from a note.
    mde = d["mde_pearson"]
    check("the measured correlation is above the design's own minimum detectable effect",
          abs(d["log_log_pearson"]) > mde,
          "|r|=%.4f vs MDE=%.4f" % (abs(d["log_log_pearson"]), mde))

    # ---- the counts the paper states about its own design ----------------------------------
    # Round-2 review M1: the subtitle and the contribution-level line said "two scales" while the
    # body enumerated three, and no gate read that sentence. The count is composed now, and this
    # compares the composition against the artefacts on disk -- a fourth scale artefact that the
    # render does not count is named here rather than reaching a reader as a stale word.
    import glob
    on_disk = []
    for path in sorted(glob.glob("results/*.json")):
        art = json.load(open(path))
        block_ = art.get("corpus") or art.get("fixture") or {}
        if "n" in block_:
            on_disk.append((path, block_["n"]))
    if scale is None or medium is None:
        check("the scale count the paper prints is the scale artefacts on disk", False,
              "a scale artefact is missing -- this check has NOT RUN, it is not a pass")
    else:
        tiers = make_manuscript.scale_tiers(d, scale, medium)
        check("the scale count the paper prints is the number of scale artefacts on disk",
              len(tiers) == len(on_disk),
              "the render counts %d (%s); results/ holds %d (%s)"
              % (len(tiers), ", ".join(str(n) for _, n in tiers), len(on_disk),
                 ", ".join("%s=%d" % (p, n) for p, n in on_disk)))
        check("the tiers the render counts are the tiers on disk, by corpus size",
              sorted(n for _, n in tiers) == sorted(n for _, n in on_disk),
              "render %s vs disk %s"
              % (sorted(n for _, n in tiers), sorted(n for _, n in on_disk)))
        fams = {label: make_manuscript.families_of(art["cells"])
                for label, art in (("A", d), ("B", scale), ("M", medium))}
        check("every tier carries the same quantiser families the family count is composed from",
              len({tuple(v) for v in fams.values()}) == 1,
              "; ".join("%s=%s" % (k, ",".join(v)) for k, v in sorted(fams.items())))

    # ---- the abstract's denominator is the read pile (round-2 review M2) -------------------
    # The abstract said "92 records of which 0 asks this question": the retrieval set's size with the
    # read pile's finding. Section 7 reads 15 of the 92. The sentence now quotes the read pile, and
    # this keeps the two piles distinguishable, so a re-run that narrows the screen cannot leave the
    # abstract claiming coverage of records nobody read.
    search = rec if "rec" in dir() else None
    if search is None:
        check("the abstract's read pile is the set the hand reading covers", False,
              "search/absence_search.json is missing -- this check has NOT RUN")
    else:
        L2 = search["ledger"]
        check("every record the screen kept was read, so the read pile is the screened pile",
              L2["survived_screen"] == L2["read_by_hand"],
              "%d survived the screen, %d were read"
              % (L2["survived_screen"], L2["read_by_hand"]))
        check("the read pile is the set the hand reading actually covers",
              L2["read_by_hand"] == len(search["hand_review"]["records"]),
              "ledger says %d read, the hand reading holds %d record(s)"
              % (L2["read_by_hand"], len(search["hand_review"]["records"])))
        check("the retrieved set and the read pile are different denominators",
              L2["records_retrieved"] > L2["read_by_hand"],
              "%d retrieved, %d read" % (L2["records_retrieved"], L2["read_by_hand"]))

    # ---- does the conclusion rest on the two single-measurement configurations? --------------
    # Question 5 of the round-2 review: tier A's scalar-quantisation cells are seedless, and the
    # sensitivity is composed over the configuration means as though all of them carried the same
    # independent information. The threshold is a property of the number of points, not of
    # within-configuration replication, so it does not weight by seed count -- but the worry is
    # testable on the committed cells, which is what this does: drop the two seedless points and
    # ask whether the ordering still clears its own, larger threshold.
    seeded = [c for c in d["cells"] if not c["tag"].endswith("/seedless")]
    keys_s, xs_s, ys_s = axis.config_means(seeded)
    r_s, m_s, n_s = axis.pearson_logs(xs_s, ys_s), axis.mde(len(keys_s)), len(keys_s)
    all_axis = axis.at_evidence_count(d["cells"])
    check("the axis holds over the configurations that carry seeds, without the seedless ones",
          abs(r_s) > m_s,
          "|r|=%.4f over %d seeded configuration means vs MDE=%.4f (all %d configurations: "
          "|r|=%.4f vs %.4f)"
          % (abs(r_s), n_s, m_s, all_axis["n_configs"],
             abs(all_axis["log_log_pearson_configs"]), all_axis["mde_pearson_configs"]))
    print("  [info] tier A without its two seedless cells: %d configuration means, |r|=%.4f, "
          "MDE=%.4f" % (n_s, abs(r_s), m_s))

    print("CLAIMS: %s" % ("PASS" if FAILED == 0 else "%d FAILED" % FAILED))
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
