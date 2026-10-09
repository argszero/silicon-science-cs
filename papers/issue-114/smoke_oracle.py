#!/usr/bin/env python3
"""Smoke battery for the issue #114 instrument skeleton.

Runs the reference interpreter, the mutation algebra and the preservation oracle
over a fixed, deterministic set of seed programs, prints the computed table, and
asserts the controls.  Exit status 0 == every control held.

Controls (each is a NEGATIVE test against this instrument, not a demo):
  C1  every mutation the algebra declares legit is computed preserving
      (0 broken-legit).  A bug in a legit rewrite is caught here.
  C2  at least one defect mutation is computed PRESERVING -- the oracle is not
      echoing `intent`.  Printed with its witness so a reader can check it.
  C3  hand-written pairs: (add x 0) == x ; (add x 1) != x ;
      (ite c a a) == (ite c a a) trivially, and a masked ite-swap is found.
  C4  a planted defect that is definitely NOT masked is flagged changing
      (two-sided: the oracle does fire).
  C5  determinism: two runs produce byte-identical JSON.

Usage: python3 smoke_oracle.py      (prints a report, exits 0/1)
"""

from __future__ import annotations

import sys

from mutations import enumerate_mutations
from oracle import analyze, dumps, summarize
from toylang import M, equivalent, parse, table, to_str

# Deterministic seed programs, hand-written, increasing in size.
SEEDS = [
    "(add x 1)",
    "(mul x x)",
    "(max (min x 200) 10)",
    "(ite (lt x 128) (mul x 2) (sub 200 x))",
    "(mod (add (mul x 3) 7) 5)",
    "(ite (and (lt x 100) (not (lt x 50))) (sub x 50) x)",
    "(ite (lt x 10) (add x 1) (add x 1))",  # both branches equal -> masked defects exist
]


def main() -> int:
    fails = []
    print("=" * 78)
    print("issue #114 instrument skeleton -- smoke battery")
    print("=" * 78)

    all_rows = []
    print("\n[1] programs, mutations, oracle verdicts (computed, not declared)")
    print(f"{'base':<52} {'mut':>4} {'legit':>6} {'defect':>7} {'masked':>7}")
    for src in SEEDS:
        prog = parse(src)
        rows = analyze(prog)
        s = summarize(rows)
        all_rows.extend(rows)
        print(f"{src:<52} {s['total']:>4} {s['legit']:>6} {s['defect']:>7} "
              f"{s['defect_masked']:>7}")

    total = summarize(all_rows)
    print(f"\n  TOTAL: {total['total']} mutations  "
          f"(legit {total['legit']}, defect {total['defect']})")
    print(f"  legit  preserving: {total['legit_preserving']}  changing: {total['legit_changing']}")
    print(f"  defect changing  : {total['defect_changing']}  masked(preserving): {total['defect_masked']}")

    # ---- C1: no broken legit -------------------------------------------------
    print("\n[C1] every legit mutation is computed preserving")
    if total["legit_changing"] == 0:
        print(f"     PASS  0 broken legit out of {total['legit']}")
    else:
        fails.append("C1")
        print(f"     FAIL  {total['legit_changing']} legit mutation(s) changed semantics:")
        for r in all_rows:
            if r["intent"] == "legit" and not r["preserving"]:
                print(f"           {r['operator']} on {r['base']} -> {r['mutant']}")

    # ---- C2: masked defects exist -------------------------------------------
    print("\n[C2] at least one defect is computed PRESERVING (oracle != intent)")
    masked = [r for r in all_rows if r["intent"] == "defect" and r["preserving"]]
    if masked:
        print(f"     PASS  {len(masked)} masked defect(s); witnesses:")
        for r in masked[:3]:
            print(f"           {r['operator']}: {r['base']}  ->  {r['mutant']}"
                  f"   (intent=defect, oracle=preserving)")
    else:
        fails.append("C2")
        print("     FAIL  no masked defect found -- oracle may be echoing intent")

    # ---- C3: hand-written pairs ---------------------------------------------
    print("\n[C3] hand-written semantic pairs")
    checks = [
        ("(add x 0) == x", equivalent(parse("(add x 0)"), parse("x")), True),
        ("(add x 1) != x", equivalent(parse("(add x 1)"), parse("x")), False),
        ("(mul x 1) == x", equivalent(parse("(mul x 1)"), parse("x")), True),
        ("(ite (lt x 128) x x) == (ite (lt x 128) x (add x 0))",
         equivalent(parse("(ite (lt x 128) x x)"), parse("(ite (lt x 128) x (add x 0))")), True),
        ("(lt x 1) != (lt 1 x)", equivalent(parse("(lt x 1)"), parse("(lt 1 x)")), False),
    ]
    for label, got, want in checks:
        ok = got == want
        print(f"     {'PASS' if ok else 'FAIL'}  {label}  -> {got}")
        if not ok:
            fails.append(f"C3:{label}")

    # ---- C4: the oracle fires (two-sided) -----------------------------------
    print("\n[C4] a planted, definitely-unmasked defect is flagged CHANGING")
    base = parse("(add x 1)")
    rows_c4 = [r for r in analyze(base)
               if r["intent"] == "defect" and r["operator"] == "const-off-by-one"]
    fired = [r for r in rows_c4 if not r["preserving"]]
    if fired:
        r = fired[0]
        print(f"     PASS  {r['base']} -> {r['mutant']}  "
              f"({r['n_differing_inputs']} of 256 inputs differ)")
    else:
        fails.append("C4")
        print(f"     FAIL  const-off-by-one on {to_str(base)} was not flagged")

    # ---- C5: determinism -----------------------------------------------------
    print("\n[C5] determinism: two runs give byte-identical analysis")
    again = []
    for src in SEEDS:
        again.extend(analyze(parse(src)))
    if dumps(all_rows) == dumps(again):
        print(f"     PASS  {len(all_rows)} rows, identical bytes over two runs")
    else:
        fails.append("C5")
        print("     FAIL  analysis is not deterministic")

    # ---- C6: the domain is pinned (this is what makes the oracle an ORACLE) ---
    # A truncated domain is the one corruption every other control survives:
    # a change that differs only at a high input would look preserving.  So the
    # domain size is asserted and a high-input-only difference is required to be
    # detected.  `(mod x 255)` agrees with `x` on 255 of 256 inputs.
    print("\n[C6] semantics domain is complete and high-input differences are seen")
    dom = len(table(parse("x")))
    hi_only = equivalent(parse("x"), parse("(mod x 255)"))
    identity = equivalent(parse("x"), parse("(add x 0)"))
    ok6 = (dom == M) and (hi_only is False) and (identity is True)
    print(f"     {'PASS' if ok6 else 'FAIL'}  domain size {dom} (need {M}); "
          f"(mod x 255) == x -> {hi_only} (need False); (add x 0) == x -> {identity} (need True)")
    if not ok6:
        fails.append("C6")

    print("\n" + "=" * 78)
    if fails:
        print(f"SMOKE: FAIL ({len(fails)} control(s)): {', '.join(fails)}")
        return 1
    print(f"SMOKE: ALL PASS  ({total['total']} mutations over {len(SEEDS)} programs)")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
