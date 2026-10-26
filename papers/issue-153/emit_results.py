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


def decisions_block(R, K, T):
    """Decision-level census: how many decisions, how many suboptimal, fan-in and price gaps."""
    import itertools
    n_dec = n_sub = 0
    fanin_max = None
    paid_min = None
    for tr in itertools.product(range(R), repeat=T):
        a = C.Analyser(tr, R, K)
        a.run()
        for d in a.decisions:
            n_dec += 1
            n_sub += d["y"]
            fanin_max = d["fanin_gap"] if fanin_max is None else max(fanin_max, d["fanin_gap"])
            paid_min = d["paid_gap"] if paid_min is None else min(paid_min, d["paid_gap"])
    return dict(decisions=n_dec, suboptimal=n_sub, fanin_gap_max=fanin_max,
                paid_gap_min=paid_min)


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

    prop = S.analyse(3, 3, 6, keep_witness=True)
    dec = decisions_block(3, 3, 6)

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
        proposition=dict(R=3, K=3, T=6, states=len(prop["groups"]),
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
