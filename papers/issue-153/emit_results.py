"""Issue #153: emit every number the manuscript states, from the committed programs.

The manuscript is generated from this file (make_manuscript.py), so no figure in the paper
is typed by hand.  Anything not in results.json cannot appear in the paper: make_manuscript
scans the prose for numeric claims and refuses any it cannot bind here.

Run: /usr/bin/python3 emit_results.py   ->  results.json
"""
import json
import sys

import characterise as C
import lemma_scale as S

CELLS = [(3, 2, 5), (3, 2, 6), (4, 2, 5),
         (3, 3, 5), (3, 3, 6), (3, 3, 7), (3, 3, 8),
         (4, 3, 5), (4, 3, 6), (4, 3, 7),
         (3, 4, 6), (3, 4, 7), (4, 4, 6),
         (3, 5, 6), (3, 5, 7), (5, 3, 5), (5, 3, 6)]


# The cell the decision-level census is taken in.  It was two hard-coded triples inside main()
# and a phrase -- "the base cell" -- used four times in the manuscript and defined nowhere, which
# is why the review could not tie the abstract's first claim to any row of the table: the artifact
# carried the counts but not the coordinates.  It is named once here, and the manifest prints it.
BASE_CELL = (3, 3, 6)


def decisions_block(R, K, T):
    """Decision-level census: how many decisions, how many suboptimal, fan-in and price gaps.

    The coordinates travel WITH the counts.  A census whose cell is unnamed is a number attached
    to a phrase; a reader cannot check it and neither could the review.
    """
    import itertools
    n_dec = n_sub = 0
    fanin_min = None
    fanin_max = None
    below_max_fanin = 0
    below_and_unique = 0
    paid_min = None
    paid_max = None
    for tr in itertools.product(range(R), repeat=T):
        a = C.Analyser(tr, R, K)
        a.run()
        for d in a.decisions:
            n_dec += 1
            n_sub += d["y"]
            g = d["fanin_gap"]
            fanin_min = g if fanin_min is None else min(fanin_min, g)
            fanin_max = g if fanin_max is None else max(fanin_max, g)
            if g < 0:
                below_max_fanin += 1
                if not d["paid_tied"]:
                    below_and_unique += 1
            paid_min = d["paid_gap"] if paid_min is None else min(paid_min, d["paid_gap"])
            paid_max = d["paid_gap"] if paid_max is None else max(paid_max, d["paid_gap"])
    # The two gaps are read on their informative side, and which side that is follows from how
    # each is computed in `characterise.py`:
    #   fanin_gap = rule.n - max(n over alternatives)  ->  <= 0 always, so its MAX is fixed and
    #     says nothing; `fanin_gap_min == 0` over a cell means no decision sits below the widest
    #     alternative, which is exactly the correspondence the paper claims, and
    #     `below_max_fanin` is that claim as a count with a denominator.
    #   paid_gap  = rule.paid - min(paid over alternatives) ->  >= 0 always, so its MIN is fixed
    #     for the same reason, AND the rule's selection key IS the bytes paid, so the price half
    #     of the claim is definitional, not measured.  `paid_gap_max` is the honest form: how far
    #     above the cheapest legal alternative the rule ever goes.  The paper states this rather
    #     than scoring it, because a statistic pinned by construction cannot be evidence.
    return dict(R=R, K=K, T=T, decisions=n_dec, suboptimal=n_sub,
                fanin_gap_min=fanin_min, fanin_gap_max=fanin_max,
                decisions_below_max_fanin=below_max_fanin,
                decisions_below_max_fanin_unique_max_paid=below_and_unique,
                paid_gap_min=paid_min, paid_gap_max=paid_max)


def main():
    cells = []
    for (R, K, T) in CELLS:
        res = S.analyse(R, K, T, keep_witness=False)
        dep_n, _, dep_worst = C.losses(R, K, T, None)
        anti_n = C.losses(R, K, T, 0)[0]
        i_first = C.first_choice_index(R, K, T)
        wstar = 0 if i_first is None else T - 1 - i_first
        cells.append(dict(R=R, K=K, T=T, traces=R ** T, states=len(res["groups"]),
                          refuting=len(res["refuting"]), sharp=res["sharp"],
                          greedy_loss=dep_n, greedy_worst=dep_worst,
                          anti_loss=anti_n, i_first=i_first, wstar=wstar))
        print("R=%d K=%d T=%d done" % (R, K, T))

    # the certificate's instance count, derived from the certificate's own cell list
    # (never typed), and its agreement is proven by running certificate.py in reproduce.sh
    import certificate as CERT
    cert_instances = sum(R ** T for (R, K, T) in CERT.CELLS)

    prop = S.analyse(BASE_CELL[0], BASE_CELL[1], BASE_CELL[2], keep_witness=True)

    # The decision-level census, in EVERY cell.  The review's first question was whether the
    # fan-in/price equivalence had been checked anywhere but the base cell; answering it in prose
    # would have been a claim with one cell behind it.  It costs ~2 s for all 17, so it is run in
    # all 17 and the equivalence is then a measured statement over the whole grid.
    dec_by_cell = []
    for (R, K, T) in CELLS:
        d = decisions_block(R, K, T)
        dec_by_cell.append(d)
        print("  census R=%d K=%d T=%d: %d decisions, %d non-optimal, "
              "%d collapse fewer runs than the widest alternative, paid above cheapest at most %d"
              % (R, K, T, d["decisions"], d["suboptimal"],
                 d["decisions_below_max_fanin"], d["paid_gap_max"]))
    dec = [d for d in dec_by_cell if (d["R"], d["K"], d["T"]) == BASE_CELL][0]

    # the positive control, both directions
    def rule_losses(R, K, T):
        return S.analyse(R, K, T)["refuting"], None

    out = dict(
        scan_date="2026-10-27",
        # values transcribed from the registration on issue #153, not measured here
        priors=dict(p2_threshold=1.3,
                    source="issue #153 registration ('worst-case ratio >1.3x')"),
        certificate=dict(instances=cert_instances, cells=len(CERT.CELLS),
                         cells_list=[dict(R=R, K=K, T=T) for (R, K, T) in CERT.CELLS]),
        cells=cells,
        n_cells=len(cells),
        n_traces_total=sum(c["traces"] for c in cells),
        n_states_total=sum(c["states"] for c in cells),
        n_refuting_total=sum(c["refuting"] for c in cells),
        decisions=dec,
        decisions_by_cell=dec_by_cell,
        decisions_all_cells=sum(d["decisions"] for d in dec_by_cell),
        suboptimal_all_cells=sum(d["suboptimal"] for d in dec_by_cell),
        # the count of cells where the correspondence the abstract states holds -- read off
        # `fanin_gap_min == 0`, because `fanin_gap <= 0` by construction and a cell whose minimum
        # is 0 is a cell with no decision below the widest alternative.  Derived, never typed: if
        # a cell ever disagrees this number drops and the sentence under it is wrong.  The two
        # counts it replaces were pinned by construction (`fanin_gap_max` is always 0,
        # `paid_gap_min` is always 0) and could not have moved for any input.
        cells_with_fanin_gap_min_zero=sum(1 for d in dec_by_cell if d["fanin_gap_min"] == 0),
        # The failures are owned by ONE key (`fanin_exception.below`) rather than by an aggregate
        # beside it: two keys holding the same number is how a paper ends up quoting two versions
        # of it.  Together with `cells_with_fanin_gap_min_zero` the two add to `n_cells`.
        # The failures, gathered so a reader can see they are one cell and not a smear: where the
        # max-bytes choice collapses fewer runs than the widest alternative, the cell it sits in,
        # that cell's denominator, and how many of the failures had a UNIQUE max-bytes merge --
        # i.e. how many the rule's key produced rather than its index tie-break.
        fanin_exception=dict(
            cells=sum(1 for d in dec_by_cell if d["decisions_below_max_fanin"] > 0),
            below=sum(d["decisions_below_max_fanin"] for d in dec_by_cell),
            below_unique=sum(d["decisions_below_max_fanin_unique_max_paid"] for d in dec_by_cell),
            decisions_in_cells=sum(d["decisions"] for d in dec_by_cell
                                   if d["decisions_below_max_fanin"] > 0),
            list=[dict(R=d["R"], K=d["K"], T=d["T"], decisions=d["decisions"],
                       below=d["decisions_below_max_fanin"],
                       below_unique=d["decisions_below_max_fanin_unique_max_paid"])
                  for d in dec_by_cell if d["decisions_below_max_fanin"] > 0]),
        paid_gap_max_over_cells=max(d["paid_gap_max"] for d in dec_by_cell),
        cells_with_paid_gap_max_positive=sum(1 for d in dec_by_cell if d["paid_gap_max"] > 0),        proposition=dict(R=3, K=3, T=6, states=len(prop["groups"]),
                         refuting=len(prop["refuting"])),
        refuted_cells=[dict(R=c["R"], K=c["K"], T=c["T"]) for c in cells if c["refuting"]],
        unrefuted_cells=[dict(R=c["R"], K=c["K"], T=c["T"], wstar=c["wstar"])
                         for c in cells if not c["refuting"]],
        max_worst=max(c["greedy_worst"] for c in cells),
        cells_at_max_worst=[dict(R=c["R"], K=c["K"], T=c["T"]) for c in cells
                            if c["greedy_worst"] == max(c["greedy_worst"] for c in cells)],
        wstar_ge1_cells=sum(1 for c in cells if c["wstar"] >= 1),
        wstar_eq0_cells=sum(1 for c in cells if c["wstar"] == 0),
        anti_choice_cells=sum(1 for c in cells if c["K"] >= 3),
        anti_wins=sum(1 for c in cells if c["K"] >= 3 and c["anti_loss"] < c["greedy_loss"]),
        anti_loses=sum(1 for c in cells if c["K"] >= 3 and c["anti_loss"] > c["greedy_loss"]),
        anti_ties=sum(1 for c in cells if c["K"] >= 3 and c["anti_loss"] == c["greedy_loss"]),
        anti_exception=[dict(R=c["R"], K=c["K"], T=c["T"], anti=c["anti_loss"],
                             deployed=c["greedy_loss"]) for c in cells
                        if c["K"] >= 3 and c["anti_loss"] > c["greedy_loss"]],
        k2_ties=[dict(R=c["R"], K=c["K"], T=c["T"]) for c in cells
                 if c["K"] == 2 and c["anti_loss"] == c["greedy_loss"]],
        lookahead_worse=None,   # filled below, needs w=1
    )
    # a lookahead of one against none, in the cell where it was measured
    out["lookahead_worse"] = dict(
        R=3, K=3, T=7,
        w1_loss=C.losses(3, 3, 7, 1)[0],
        w0_loss=C.losses(3, 3, 7, 0)[0],
        deployed_loss=C.losses(3, 3, 7, None)[0])
    json.dump(out, open("results.json", "w"), indent=1, sort_keys=True)
    print("\nresults.json written: %d cells, %d traces, %d states, %d refuting"
          % (out["n_cells"], out["n_traces_total"], out["n_states_total"],
             out["n_refuting_total"]))
    print("max worst excess %.3f ; anti wins %d loses %d ties(K=2) %d"
          % (out["max_worst"], out["anti_wins"], out["anti_loses"], len(out["k2_ties"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
