"""Validate the issue #83 manuscript's recovery claims against reproduce.py output.

Two-tier scheme (manuscript §8): Tier A exact-value/structural cells + Tier B
mechanism-level cells with slack for run-to-run stochasticity (per [1] R179 lesson:
stochastic cells vary ~±0.1 across independent runs; exact values are per-run-reported
in README_repro.md, not asserted).

Reads CELL lines from a reproduce run log (file arg or stdin). Exit 0 iff all pass.
"""
import re
import sys

# Tier A: structural cells (asserted) — the DESTROY signature is a RELATIVE claim
# (greedy-recovered while the sampling channel collapsed vs the same run's base), so
# both checks compare collapsed_s0 against the in-run base_s0 cell.


def checks_tier_a(cells):
    chk = []
    base = cells.get("base_s0")
    coll = cells.get("collapsed_s0")

    def add(desc, ok, detail=""):
        chk.append((desc, bool(ok), detail))

    if base and coll:
        add("DESTROY: collapsed greedy within 0.1 of base greedy (greedy-recovered)",
            coll["ca"] >= base["ca"] - 0.1,
            "base=%.3f collapsed=%.3f" % (base["ca"], coll["ca"]))
        add("DESTROY: collapsed pass@64 <= base pass@64 - 0.4 (channel collapsed)",
            coll["p64"] <= base["p64"] - 0.4,
            "base=%.3f collapsed=%.3f" % (base["p64"], coll["p64"]))
    else:
        add("base_s0/collapsed_s0 cells present", False)
    return chk


# Tier B: mechanism-level checks over parsed cells


def checks_tier_b(cells):
    chk = []

    def add(desc, ok, detail=""):
        chk.append((desc, bool(ok), detail))

    base = cells.get("base_s0")
    coll = cells.get("collapsed_s0")
    cont = cells.get("continue")
    kl01 = cells.get("klreanchor_b001")
    kl10 = cells.get("klreanchor_b10")
    rep = cells.get("sftreplay")
    if base and coll and rep:
        add("RECOVERY: replay pass@64 within 0.1 of base after 600 steps (n=48 noise floor)",
            rep["p64"] >= base["p64"] - 0.1,
            "base=%.3f replay=%.3f" % (base["p64"], rep["p64"]))
        add("RECOVERY: fold-over-collapsed >= 2x",
            rep["p64"] >= 2 * coll["p64"] + 0.05,
            "collapsed=%.3f replay=%.3f" % (coll["p64"], rep["p64"]))
    else:
        add("base/collapsed/replay cells present", False)
    for name, c in [("continue", cont), ("klreanchor_b001", kl01), ("klreanchor_b10", kl10)]:
        if c is not None and base is not None:
            add("POLICY-SPACE FAIL: %s pass@64 < base - 0.3" % name,
                c["p64"] < base["p64"] - 0.3,
                "arm=%.3f base=%.3f" % (c["p64"], base["p64"]))
        else:
            add("%s cell present" % name, False)
    return chk


def parse_cells(lines):
    cells = {}
    for ln in lines:
        m = re.match(r"CELL (\w+):", ln)
        if not m:
            continue
        key = m.group(1)
        kv = {}
        for pm in re.finditer(r"(\w+)=([0-9.]+)", ln):
            kv[pm.group(1)] = float(pm.group(2))
        cells[key] = kv
    return cells


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    f = open(path) if path else sys.stdin
    cells = parse_cells(f)
    if path:
        f.close()
    if not cells:
        print("No CELL lines found in input")
        sys.exit(1)
    print("Observed per-cell values:")
    for key in sorted(cells):
        print("  %-18s %s" % (key, " ".join("%s=%.3f" % (k, v) for k, v in sorted(cells[key].items()))))
    print()
    fails = 0
    checks = 0
    print("Tier A (structural cells):")
    for desc, ok, detail in checks_tier_a(cells):
        checks += 1
        print("  %s %s%s" % ("PASS" if ok else "FAIL", desc, (" [%s]" % detail) if detail else ""))
        if not ok:
            fails += 1
    print("\nTier B (mechanism-level cells):")
    for desc, ok, detail in checks_tier_b(cells):
        checks += 1
        print("  %s %s%s" % ("PASS" if ok else "FAIL", desc, (" [%s]" % detail) if detail else ""))
        if not ok:
            fails += 1
    print("\n%d/%d checks passed" % (checks - fails, checks))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
