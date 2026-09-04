"""Validate the manuscript's regime table against reproduce.py output — TWO-TIER scheme.

Tier A (exact-value cells): structural outcomes that reproduce identically across
independent runs (author R177 log and the editor's independent clean-clone run,
2026-09-04, agree on these): WALL rl_ca/rl_p64 = 0.000 and GREEDY-BLIND rl_odd =
0.000. No sampling support exists in the base, so the zeros are structural, not
lucky draws.

Tier B (mechanism-level cells): directional/ordering checks with slack for the
run-to-run stochasticity observed at 1.8M-token scale (stochastic cells varied by
~±0.1 across the two independent runs; exact values are reported per run and
collected in README_repro.md, not asserted). Mechanism = the taxonomy and effect
directions of §5.8: RACE seed-lottery (a strong seed appears, outcomes spread,
mean positive), CREATE RL lifts greedy over base in >=2/3 seeds with a positive
mean, DESTROY degrades RL carry greedy below the SFT base (base competence must
exist), GREEDY-BLIND keeps a *base* pass@64 >= 0.6 search channel while RL odd
greedy stays 0 (post-RL rl_p64 is bimodal across runs — §5.5 — and is printed
report-only).

Reads CELL lines from a reproduce run log (file arg or stdin).
Exit 0 iff all checks pass; also prints the observed per-cell values for the
variance record.

Usage:
    bash reproduce.sh            # self-contained: reproduce.py > log; validate.py log
    python validate.py repro.log
    python validate.py < repro.log
"""
import re
import sys

# Tier A: exact-value cells (structural; identical on both independent runs).
TIER_A = [
    ("add cov000 s0", "rl_ca", 0.01, "WALL rl_ca <= 0.01 (structural zero)"),
    ("add cov000 s0", "rl_p64", 0.01, "WALL rl_p64 <= 0.01 (structural zero)"),
    ("par cov100 s0", "rl_odd", 0.01, "GREEDY-BLIND rl_odd <= 0.01 (structural zero)"),
]

# Tier B: mechanism-level checks, each a (description, predicate) over parsed cells.
RACE_CELLS = ["count L20 s0", "count L20 s1", "count L20 s2"]
CREATE_CELLS = ["count L12 s0", "count L12 s1", "count L12 s2"]


def cell_vals(cells, key, metric):
    return [cells[k][metric] for k in (key if isinstance(key, list) else [key]) if k in cells]


def checks_tier_b(cells):
    chk = []

    def add(desc, ok, detail=""):
        chk.append((desc, bool(ok), detail))

    # RACE: count L20 seeds 0..2 — bootstrap seed-lottery
    rl = [cells[k]["rl_g"] for k in RACE_CELLS if k in cells]
    if len(rl) == 3:
        add("RACE: strong seed present (max rl_g >= 0.10)",
            max(rl) >= 0.10, "max=%.3f" % max(rl))
        add("RACE: seed-lottery spread (max - min >= 0.08 or min <= 0.03)",
            (max(rl) - min(rl)) >= 0.08 or min(rl) <= 0.03,
            "spread=%.3f" % (max(rl) - min(rl)))
        add("RACE: positive mean (mean rl_g >= 0.04)",
            sum(rl) / 3 >= 0.04, "mean=%.3f" % (sum(rl) / 3))
    else:
        add("RACE cells present", False, "found %d/3" % len(rl))

    # CREATE: count L12 seeds 0..2 — RL lifts greedy over the SFT base
    lifts = 0
    mean_g = None
    for k in CREATE_CELLS:
        if k in cells and cells[k].get("base_g") is not None:
            if cells[k]["rl_g"] > cells[k]["base_g"]:
                lifts += 1
    rl12 = [cells[k]["rl_g"] for k in CREATE_CELLS if k in cells]
    if len(rl12) == 3:
        mean_g = sum(rl12) / 3
        add("CREATE: RL lifts greedy over base in >=2/3 seeds", lifts >= 2,
            "lifts %d/3" % lifts)
        add("CREATE: positive mean (mean rl_g >= 0.25)", mean_g >= 0.25,
            "mean=%.3f" % mean_g)
    else:
        add("CREATE cells present", False, "found %d/3" % len(rl12))

    # DESTROY: add c=0.01 seed 0 — RL carry greedy degrades below the SFT base
    d = cells.get("add cov010 s0")
    if d is not None:
        base_ca = d.get("base_ca")
        rl_ca = d.get("rl_ca")
        add("DESTROY: base competence exists (base_ca >= 0.08)",
            base_ca is not None and base_ca >= 0.08,
            "base_ca=%.3f" % base_ca if base_ca is not None else "n/a")
        add("DESTROY: RL degrades carry greedy (rl_ca < base_ca - 0.01)",
            base_ca is not None and rl_ca is not None and rl_ca < base_ca - 0.01,
            "base_ca=%.3f rl_ca=%.3f" % (base_ca or 0, rl_ca or 0))
    else:
        add("DESTROY cell present", False, "missing")

    # GREEDY-BLIND: parity c=0.10 seed 0 — base sampling channel solves the class;
    # post-RL rl_p64 is bimodal across independent runs (manuscript §5.5), so it is
    # REPORTED below, not asserted. rl_odd <= 0.01 is asserted in Tier A.
    g = cells.get("par cov100 s0")
    if g is not None:
        add("GREEDY-BLIND: base search channel alive (base_p64 >= 0.60)",
            g.get("base_p64") is not None and g["base_p64"] >= 0.60,
            "base_p64=%.3f" % g.get("base_p64", -1))
        if g.get("rl_p64") is not None:
            print("  NOTE GREEDY-BLIND rl_p64=%.3f (bimodal across runs: ~1.0 in 2/3, ~0 in 1/3; report-only, see manuscript §5.5)" % g["rl_p64"])
    else:
        add("GREEDY-BLIND cell present", False, "missing")
    return chk


def parse_cells(lines):
    cells = {}
    for ln in lines:
        m = re.match(r"CELL (.*?):", ln)
        if not m:
            continue
        key = m.group(1).strip()
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

    print("Observed per-cell values (variance record — see README_repro.md):")
    for key in sorted(cells):
        print("  %-16s %s" % (key, " ".join("%s=%.3f" % (k, v) for k, v in sorted(cells[key].items()))))
    print()

    fails = 0
    checks = 0
    print("Tier A (exact-value cells):")
    for key, skey, tol, what in TIER_A:
        cell = cells.get(key)
        checks += 1
        if cell is None or skey not in cell:
            print("  FAIL %s: cell/metric missing" % what)
            fails += 1
            continue
        got = cell[skey]
        ok = got <= tol
        print("  %s %s (got %.3f, must be <= %.2f)" % ("PASS" if ok else "FAIL", what, got, tol))
        if not ok:
            fails += 1

    print("\nTier B (mechanism-level cells):")
    for desc, ok, detail in checks_tier_b(cells):
        checks += 1
        print("  %s %s%s" % ("PASS" if ok else "FAIL", desc,
                             (" [%s]" % detail) if detail else ""))
        if not ok:
            fails += 1

    print("\n%d/%d checks passed (Tier A exact: %d checks; Tier B mechanism: %d checks)"
          % (checks - fails, checks, len(TIER_A), checks - len(TIER_A)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
