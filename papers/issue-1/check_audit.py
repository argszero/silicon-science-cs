#!/usr/bin/env python3
"""Reversion audit for consistency_check.py: does every check earn its place?

Motivation (host bar proposal raised on the issue #1 thread, 2026-09-12): a suite that
reports "24/24" is evidence about the suite only if each check can be shown to REJECT
something. A check that fires on nothing, or that merely re-reports another check's verdict,
is decoration - it inflates the denominator without constraining the artefact. The same
standard the fidelity gate already meets for the model port (four named corruptions, three of
which must degrade the metric and one of which must improve it) is applied here to the
manuscript-to-artefact chain.

Method: for each check, apply ONE targeted corruption to a fresh copy of the committed
package, then run consistency_check.py there and record the exact set of checks that fail.
Targets are surgical - a corruption is aimed at the single value the check reads, and the
mutator asserts that it changed something, so a silently ineffective corruption cannot be
mistaken for a check that failed to fire.

Reported: which checks are load-bearing, which have a witness that ONLY they catch, which
never fire at all (decoration), and which corruptions more than one check catches (overlap,
stated rather than hidden - C02 guards the artefact body, so any body edit necessarily trips
it alongside the check that reads the mutated field).

    python3 check_audit.py        # prints the matrix; exit 1 if any check is decoration

Standard library only; it never writes to the committed package.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = "consistency_check.py"
BASE = ["canonical_results.json", "manuscript.md", "results_table.md", "references.json",
        "figures/manifest.json"]
FIGURES = ["figures/fig1_crossover.png", "figures/fig2_distractor_type.png",
           "figures/fig3_position.png"]


def snapshot(dst):
    for f in BASE + FIGURES + [CHECKER]:
        d = os.path.join(dst, f)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(os.path.join(HERE, f), d)


def edit(path, fn, binary=False):
    mode = "rb" if binary else "r"
    kw = {} if binary else {"encoding": "utf-8"}
    with open(path, mode, **kw) as fh:
        t = fh.read()
    t2 = fn(t)
    assert t2 != t, "corruption was a no-op on %s" % os.path.basename(path)
    with open(path, "w" if not binary else "wb", **kw) as fh:
        fh.write(t2)


def rep1(old, new):
    def f(t):
        assert t.count(old) >= 1, "pattern absent: %r" % old[:60]
        return t.replace(old, new, 1)
    return f


def repall(old, new):
    def f(t):
        assert t.count(old) >= 1, "pattern absent: %r" % old[:60]
        return t.replace(old, new)
    return f


def set_derived(key, value, sub=None):
    """Set derived[key] (or derived[key][sub]) without refreshing the embedded sha256."""
    def f(t):
        d = json.loads(t)
        if sub is None:
            d["derived"][key] = value
        else:
            d["derived"][key][sub] = value
        return json.dumps(d, indent=1, sort_keys=True)
    return f


def set_fidelity(path, value):
    def f(t):
        d = json.loads(t)
        node = d["fidelity"]
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = value
        return json.dumps(d, indent=1, sort_keys=True)
    return f


def set_wilson(delta=0.5):
    def f(t):
        d = json.loads(t)
        w = d["derived"]["sampled_wilson"][0]
        w["lo"] = round(max(0.0, w["lo"] - delta), 6)
        return json.dumps(d, indent=1, sort_keys=True)
    return f


# (label, description, relative file, mutator, binary)
CORRUPTIONS = [
    # --- artefact-integrity checks
    ("C01", "manuscript no longer carries the artefact payload sha256", "manuscript.md",
     repall("8dc43a9cc1d0a981", "0dc43a9cc1d0a981"), False),
    ("C02", "artefact body edited without refreshing its embedded sha256",
     "canonical_results.json",
     lambda t: json.dumps(dict(json.loads(t), audit_probe=1), indent=1, sort_keys=True), False),
    ("C04", "results_table.md edited so the manifest hash is stale", "results_table.md",
     rep1("Gold-answer mean", "Gold answer mean"), False),
    ("C18", "a committed figure no longer matches its manifest hash",
     "figures/fig1_crossover.png", lambda t: t + b"x", True),
    # --- table-vs-artefact
    ("C03", "one value inside a manuscript Table 1 row changed", "manuscript.md",
     rep1("| 64 | 0.00 | -0.180 |", "| 64 | 0.00 | -0.181 |"), False),
    ("C12", "a Wilson interval moves in the artefact (table goes stale)",
     "canonical_results.json", set_wilson(), False),
    # --- headline numbers, each anchored to its claim
    ("C05", "the zero-interference gap changed away from its artefact value", "manuscript.md",
     repall("+0.062", "+0.063"), False),
    ("C06.length", "one value in the context-length table row changed", "manuscript.md",
     rep1("| -0.180 | -0.228 | -0.206 |", "| -0.180 | -0.229 | -0.206 |"), False),
    ("C06.fill", "the neutral-filler control value changed", "manuscript.md",
     rep1("neutral filler at -0.150", "neutral filler at -0.151"), False),
    ("C06.posi", "one value in the position table row changed", "manuscript.md",
     rep1("-1.054 |", "-1.055 |"), False),
    ("C07", "a distractor-type contrast changed everywhere it is claimed", "manuscript.md",
     repall("-1.856", "-1.857"), False),
    ("C08.dn", "one rung of the dense pooled-recall ladder changed", "manuscript.md",
     rep1("5/30 at k = 4", "6/30 at k = 4"), False),
    ("C08.k8", "dense pooled recall at k=8 changed", "manuscript.md",
     rep1("15/30 at k = 8", "14/30 at k = 8"), False),
    ("C08.bm25", "the BM25 pooled recall changed", "manuscript.md",
     rep1("BM25 recovers **0/30**", "BM25 recovers **1/30**"), False),
    ("C09", "the cell count changed everywhere it is claimed", "manuscript.md",
     repall("48 cells", "47 cells"), False),
    ("C10", "the no-distractor denominator moves in the artefact", "canonical_results.json",
     set_derived("n_no_distractor", 7), False),
    ("C11", "the sign-test ratio changed", "manuscript.md",
     rep1("31/36", "30/36"), False),
    ("C13", "the held-out bits/token changed", "manuscript.md",
     rep1("5.242516", "5.242517"), False),
    ("C14", "the KV-cache exactness claim is no longer exact", "manuscript.md",
     rep1("logit difference 0.0", "logit difference 0.1"), False),
    # --- bibliography structure
    ("C15", "a second References heading is added", "manuscript.md",
     rep1("\n## References\n", "\n## References\n\n## References\n"), False),
    ("C16", "one bibliography entry is deleted", "manuscript.md", lambda t: re.sub(
        r"\n\[[0-9]+\][^\n]*", "", t, count=1), False),
    ("C17", "every in-text citation of one entry is removed", "manuscript.md",
     repall("[105]", ""), False),
]


def run_case(label, desc, fname, mut, binary):
    tmp = tempfile.mkdtemp(prefix="audit-")
    try:
        snapshot(tmp)
        edit(os.path.join(tmp, fname), mut, binary=binary)
        pr = subprocess.run([sys.executable, os.path.join(tmp, CHECKER)],
                            capture_output=True, text=True, cwd=tmp)
        failed = sorted(set(re.findall(r"^(C\d+(?:\.\w+)?)\s+FAIL", pr.stdout, re.M)))
        return {"label": label, "desc": desc, "exit": pr.returncode, "failed": failed}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    clean = subprocess.run([sys.executable, os.path.join(HERE, CHECKER)],
                           capture_output=True, text=True, cwd=HERE)
    ids = re.findall(r"^(C\d+(?:\.\w+)?)\s+PASS", clean.stdout, re.M)
    assert ids, "could not enumerate the checks from a clean run"
    print("clean run: %s" % re.search(r"CONSISTENCY \d+/\d+", clean.stdout).group(0))
    print("checks under audit: %d\n" % len(ids))

    print("%-11s %-5s %s" % ("corruption", "exit", "checks that fired"))
    print("-" * 76)
    rows = []
    for label, desc, fname, mut, binary in CORRUPTIONS:
        r = run_case(label, desc, fname, mut, binary)
        rows.append(r)
        print("%-11s %-5s %s" % (label, r["exit"],
                                 " ".join(r["failed"]) or "(SURVIVED - nothing fired)"))

    fired = {}
    for r in rows:
        for c in r["failed"]:
            fired.setdefault(c, []).append(r["label"])
    never = [c for c in ids if c not in fired]
    unique = {c: v[0] for c, v in fired.items() if len(v) == 1}
    survived = [r["label"] for r in rows if not r["failed"]]

    print("\n--- per check ---")
    for c in ids:
        w = fired.get(c)
        print("%-11s %s" % (c, ("caught by " + ", ".join(w) +
                                ("   [sole witness]" if len(w) == 1 else "")) if w
                            else "*** NEVER FIRED - decoration ***"))

    print("\nchecks load-bearing      : %d/%d" % (len(ids) - len(never), len(ids)))
    print("collectively witnessed   : %d/%d corruptions caught"
          % (len(rows) - len(survived), len(rows)))
    print("sole-witness checks      : %d (%s)"
          % (len(unique), ", ".join("%s<-%s" % (c, u) for c, u in sorted(unique.items()))))
    print("decoration (never fired) : %s" % (never or "none"))
    print("corruptions that survived: %s" % (survived or "none"))
    multi = {r["label"]: r["failed"] for r in rows if len(r["failed"]) > 1}
    print("caught by >1 check       : %d (C02 guards the artefact body, so a body edit trips\n"
          "                           it beside the check that reads the mutated field)" % len(multi))
    for k, v in sorted(multi.items()):
        print("    %-11s -> %s" % (k, " ".join(v)))
    ok = not never and not survived
    print("\nAUDIT %s" % ("CLEAN - every one of the %d checks rejects something" % len(ids)
                           if ok else "FINDINGS - never=%s survived=%s" % (never, survived)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
