# -*- coding: utf-8 -*-
"""check_claims.py -- does the artefact still say what the paper says it says?

Every quantitative statement in the manuscript is a sentence about `results/crossover.json`. This
program is what keeps those sentences honest: it reads the artefact and re-derives

  (1) each registered prior's verdict (MET / UNMET / NOT RUN) from the numbers, and
  (2) the internal identities the artefact must satisfy whatever the data says.

and then asserts the registered verdicts are still the ones the paper reports. If a number moves
far enough to flip a prior, this fails -- which is the point: a refuted prior that quietly becomes
agreement is the failure mode a measurement paper cannot afford.

Exit: 0 every claim holds · 1 a claim moved or an identity broke · 3 NOT RUN (no artefact).

`--selftest` runs the identical predicate on two mutated copies of the artefact and requires both to
be refused, so the gate is demonstrated to bite rather than asserted to.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "results", "crossover.json")
PROVENANCE = os.path.join(HERE, "fixture", "MEMBER_SHA256")

# The priors as registered on issue #160, with the threshold each one names. `test` is applied to a
# value read out of the artefact -- a prior is never compared against a number typed here.
CLAIMS = [
    dict(id="P2' limb 1", path="cells.0.binds_frac", op=">=", threshold=0.50,
         registered="MET",
         text="censoring binds on at least half the rows at a 2x-median timeout"),
    dict(id="P2' limb 2", path="cells.4.binds_frac", op="<", threshold=0.10,
         registered="UNMET",
         text="censoring binds on under a tenth of the rows at a 32x-median timeout"),
    dict(id="P3", path="cost.K_at_5.median", op=">=", threshold=20,
         registered="MET",
         text="the median workload needs at least 20 timeout levels to certify within 5%"),
]

CONTROL = dict(id="no-censoring control", path="controls.no_censoring_identified_and_exact_frac",
               op="==", threshold=1.0, registered="MET",
               text="a timeout above the row maximum identifies the quantile exactly, every time")


def get(art, dotted):
    """Read a dotted path out of the artefact; a missing path is a failure, never a default."""
    cur = art
    for part in dotted.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError("artefact has no %s" % dotted)
    return cur


def holds(value, op, threshold):
    if op == ">=":
        return value >= threshold
    if op == "<":
        return value < threshold
    if op == "==":
        return abs(value - threshold) <= 1e-12
    if op == ">":
        return value > threshold
    raise ValueError("unknown operator %r" % op)


def verdict(claim, art):
    v = get(art, claim["path"])
    return v, ("MET" if holds(v, claim["op"], claim["threshold"]) else "UNMET")


def identities(art):
    """The statements that must hold whatever the data turns out to be. Returns [(name, ok, detail)]."""
    out = []
    cl = art["count_limit"]
    refused = sum(cl["refused"].values())
    out.append(("rows read = usable + refused",
                cl["rows"] == cl["usable"] + refused,
                "%d vs %d + %d" % (cl["rows"], cl["usable"], refused)))
    # Exact, not re-multiplied: asserting `resolvable + round(frac * usable) == usable` passes on a
    # rounding coincidence, so it would stay green while the fractions drifted from their counts.
    out.append(("resolvable_frac is resolvable/usable to 4 dp",
                cl["resolvable_frac"] == round(cl["resolvable"] / float(cl["usable"]), 4),
                "%d/%d = %.4f vs %.4f" % (cl["resolvable"], cl["usable"],
                                          cl["resolvable"] / float(cl["usable"]), cl["resolvable_frac"])))
    out.append(("unresolvable_frac is the complement of resolvable_frac",
                cl["unresolvable_frac"] == round(1.0 - cl["resolvable_frac"], 4),
                "%.4f vs 1 - %.4f" % (cl["unresolvable_frac"], cl["resolvable_frac"])))
    # A real implication of the definition, not an identity in disguise. A row with Count < 100
    # expects fewer than 1 observation above a p99 (100 * (1-q) is exactly 1), so every such row must
    # be unresolvable: below_100 must fit inside usable - resolvable. Written as a tautology
    # (`resolvable == 0 + resolvable`) this line stayed green while measuring nothing.
    out.append(("every row with Count < 100 is unresolvable",
                cl["below_100"] <= cl["usable"] - cl["resolvable"],
                "%d below 100 vs %d unresolvable (%d - %d)"
                % (cl["below_100"], cl["usable"] - cl["resolvable"], cl["usable"], cl["resolvable"])))
    out.append(("below_100 <= below_1000", cl["below_100"] <= cl["below_1000"],
                "%d <= %d" % (cl["below_100"], cl["below_1000"])))
    out.append(("below_100_frac is below_100/usable to 4 dp",
                cl["below_100_frac"] == round(cl["below_100"] / float(cl["usable"]), 4),
                "%d/%d = %.4f vs %.4f" % (cl["below_100"], cl["usable"],
                                          cl["below_100"] / float(cl["usable"]), cl["below_100_frac"])))
    for cell in art["cells"]:
        out.append(("k=%d: binds + identified = 1" % cell["k"],
                    abs(cell["binds_frac"] + cell["identified_frac"] - 1.0) < 5e-5,
                    "%.4f + %.4f" % (cell["binds_frac"], cell["identified_frac"])))
        out.append(("k=%d: rows == usable" % cell["k"], cell["rows"] == cl["usable"],
                    "%d vs %d" % (cell["rows"], cl["usable"])))
    fracs = [c["binds_frac"] for c in art["cells"]]
    out.append(("binds is non-increasing in the timeout multiplier",
                all(a >= b for a, b in zip(fracs, fracs[1:])),
                " -> ".join("%.4f" % f for f in fracs)))
    # The registration is the authority, not the artefact. Without these two lines the artefact
    # certifies its own configuration: change Q or the timeout grid inside the program and the
    # artefact regenerates consistently, step 3 stays byte-identical, and every claim below is
    # evaluated against numbers that answer a different question. Found by planting exactly that.
    out.append(("q is the registered 0.99", art["q"] == 0.99, "q = %r" % (art["q"],)))
    out.append(("the timeout grid is the registered {2,4,8,16,32}",
                list(art["kgrid"]) == [2, 4, 8, 16, 32]
                and [c["k"] for c in art["cells"]] == [2, 4, 8, 16, 32],
                str(art["kgrid"])))
    out.append(("the precision ladder is the registered {5%,10%,20%}",
                sorted(art["eps"]) == [0.05, 0.1, 0.2], str(art["eps"])))
    out.append(("every k in the pre-declared grid is present",
                [c["k"] for c in art["cells"]] == list(art["kgrid"]),
                str([c["k"] for c in art["cells"]])))
    out.append(("the artefact records the digest of the bytes it read",
                len(get(art, "input.sha256_of_decompressed_bytes")) == 64,
                get(art, "input.sha256_of_decompressed_bytes")[:16] + "..."))
    return out


def evaluate(art, provenance=PROVENANCE):
    """(claims, identities, failures). Pure: same artefact in, same verdicts out."""
    claims = []
    fails = []
    for c in CLAIMS + [CONTROL]:
        try:
            v, got = verdict(c, art)
        except (KeyError, IndexError, TypeError) as e:
            claims.append((c["id"], None, "MISSING", c["registered"], str(e)))
            fails.append("%s: %s" % (c["id"], e))
            continue
        claims.append((c["id"], v, got, c["registered"], c["text"]))
        if got != c["registered"]:
            fails.append("%s moved: registered %s, artefact now says %s (value %s)"
                         % (c["id"], c["registered"], got, v))
    ids = identities(art)
    for name, ok, detail in ids:
        if not ok:
            fails.append("identity broken: %s (%s)" % (name, detail))
    # the numbers must belong to the committed bytes, not merely to some run
    if os.path.exists(provenance):
        for line in open(provenance, encoding="utf-8"):
            tok = line.split()
            if tok and not tok[0].startswith("#") and len(tok[0]) == 64:
                rec = tok[0].lower()
                if get(art, "input.sha256_of_decompressed_bytes") != rec:
                    fails.append("the artefact was produced from other bytes than the fixture records")
                break
    return claims, ids, fails


def report(art):
    claims, ids, fails = evaluate(art)
    print("claim                                        value      now      registered")
    for cid, v, got, reg, text in claims:
        shown = "-" if v is None else ("%.4f" % v if isinstance(v, float) else str(v))
        flag = "" if got == reg else "   <-- MOVED"
        print("  %-42s %9s  %-8s %-8s%s" % (cid, shown, got, reg, flag))
    print("\nidentities (%d):" % len(ids))
    for name, ok, detail in ids:
        print("  [%s] %s -- %s" % ("ok" if ok else "FAIL", name, detail))
    return fails


def selftest():
    """The gate must refuse two mutations, using the same `evaluate` the real run uses."""
    fails = 0

    def expect(name, ok, detail=""):
        nonlocal fails
        print("  [%s] %s%s" % ("ok" if ok else "FAIL", name, (" -- " + detail) if detail else ""))
        if not ok:
            fails += 1

    if not os.path.exists(ART):
        print("  [SKIP] no artefact to mutate")
        return 1
    base = json.load(open(ART, encoding="utf-8"))

    print("selftest: the artefact as committed")
    f0 = report(base)
    expect("the committed artefact satisfies every claim", not f0, "; ".join(f0[:2]))

    # 1. the refuted limb quietly becomes agreement -- the exact drift this gate exists to catch.
    m1 = json.loads(json.dumps(base))
    m1["cells"][4]["binds_frac"] = 0.05
    m1["cells"][4]["identified_frac"] = 0.95
    f1 = evaluate(m1)[2]
    expect("a refuted limb flipped into agreement is refused",
           any("limb 2" in x for x in f1), (f1 or ["(not refused)"])[0])

    # 2. an identity broken by a plausible-looking single edit: the split fractions no longer sum.
    m2 = json.loads(json.dumps(base))
    m2["cells"][0]["identified_frac"] = 0.50
    f2 = evaluate(m2)[2]
    expect("binds + identified != 1 is refused", any("binds + identified" in x for x in f2),
           (f2 or ["(not refused)"])[0])

    # 3. numbers that belong to a different input than the fixture records.
    m3 = json.loads(json.dumps(base))
    m3["input"]["sha256_of_decompressed_bytes"] = "0" * 64
    f3 = evaluate(m3)[2]
    expect("an artefact from other bytes than the fixture is refused",
           any("other bytes" in x for x in f3), (f3 or ["(not refused)"])[0])

    print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if not os.path.exists(ART):
        print("NOT RUN: %s is absent, so no claim was checked" % os.path.relpath(ART, HERE))
        return 3
    art = json.load(open(ART, encoding="utf-8"))
    fails = report(art)
    if fails:
        print("\nCLAIMS: %d PROBLEM(S)" % len(fails))
        for f in fails:
            print("   - %s" % f)
        return 1
    print("\nCLAIMS: OK -- every registered prior's verdict follows from the artefact")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
