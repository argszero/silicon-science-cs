"""Validate the manuscript's regime-table numbers against reproduce.py output.

Reads CELL lines from a reproduce run log (file arg or stdin) and asserts the
six central outcomes with tolerance against the manuscript's reported values
(eval seed 777). Exit 0 if all pass, 1 otherwise.

Usage:
    python reproduce.py > repro.log 2>&1
    python validate.py repro.log
or: python validate.py < repro.log
"""
import re
import sys

TOL = 0.03

# (cell-key-prefix, [(metric-key, expected, human-label, mode)])
# mode: "abs" = |got-exp|<=TOL ; "degrade" = got < base AND |got-exp|<=TOL+0.02
EXPECT = [
    ("CELL add cov000 s0", [("rl_ca", 0.000, "WALL rl_ca", "abs")]),
    ("CELL count L20 s0", [("rl_g", 0.172, "RACE s0 rl_g", "abs")]),
    ("CELL count L20 s1", [("rl_g", 0.076, "RACE s1 rl_g", "abs")]),
    ("CELL count L20 s2", [("rl_g", 0.000, "RACE s2 rl_g", "abs")]),
    ("CELL count L12 s0", [("rl_g", 0.378, "CREATE s0 rl_g", "abs")]),
    ("CELL count L12 s1", [("rl_g", 0.505, "CREATE s1 rl_g", "abs")]),
    ("CELL count L12 s2", [("rl_g", 0.565, "CREATE s2 rl_g", "abs")]),
    ("CELL add cov010 s0", [("rl_ca", 0.083, "DESTROY rl_ca", "degrade")]),
    ("CELL par cov100 s0", [("rl_odd", 0.000, "GB rl_odd", "abs"),
                            ("rl_p64", 1.000, "GB rl_p64", "abs")]),
]


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
    fails = 0
    checks = 0
    for prefix, subs in EXPECT:
        # exact key: cells keys look like 'add cov000 s0', 'count L20 s0', ...
        cell = cells.get(prefix[len("CELL "):])
        if cell is None:
            print("MISSING %s" % prefix)
            fails += 1
            continue
        for skey, exp, what, mode in subs:
            checks += 1
            got = cell.get(skey)
            base = cell.get("base_ca") or cell.get("base_odd") or cell.get("base_g")
            if got is None:
                print("FAIL %s: no %s key" % (what, skey))
                fails += 1
                continue
            if mode == "degrade":
                ok = (base is not None and got < base - 1e-9
                      and abs(got - exp) <= TOL + 0.02)
            else:
                ok = abs(got - exp) <= TOL
            print("%s %s (got %.3f expected %.3f%s)" % (
                "PASS" if ok else "FAIL", what, got, exp,
                "" if ok else " [base %.3f]" % base if base is not None else ""))
            if not ok:
                fails += 1
    print("\n%d/%d checks passed" % (checks - fails, checks))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
