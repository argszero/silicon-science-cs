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
# read the artefact hash rather than hard-coding it, so a rebuild cannot silently make the
# C01 corruption a no-op (which would then look like a check that failed to fire).
PAYLOAD16 = json.load(open(os.path.join(HERE, "canonical_results.json")))["sha256"][:16]
BASE = ["canonical_results.json", "manuscript.md", "results_table.md", "references.json",
        "figures/manifest.json"]
FIGURES = ["figures/fig1_crossover.png", "figures/fig2_distractor_type.png",
           "figures/fig3_position.png"]


def snapshot(dst):
    """Copy the whole package except the git-ignored research workspace.

    The gate now reads the package's own documentation (C27 hashes every file the README's
    table names; C28 walks the tree), so a partial copy would make those checks fail for
    missing files rather than for the corruption under test.
    """
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in ("research", "__pycache__", ".git")]
        for f in files:
            if f.startswith("."):
                continue
            src = os.path.join(root, f)
            d = os.path.join(dst, os.path.relpath(src, HERE))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(src, d)


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


def flip_row(rel):
    """Flip the first hex digit of one README file-hash row, without hard-coding its value."""
    def f(t):
        m = re.search(r"^\| `%s` \| `([0-9a-f]{16})` \|" % re.escape(rel), t, re.M)
        assert m, "README hash row for %s not found" % rel
        h = m.group(1)
        return t[:m.start(1)] + ("0" if h[0] != "0" else "1") + h[1:] + t[m.end(1):]
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
     lambda t: t.replace(PAYLOAD16, "0" + PAYLOAD16[1:]), False),
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
    ("C19", "one rung interval in the manuscript row changed", "manuscript.md",
     rep1("[-1.683, -0.454] |", "[-1.684, -0.454] |"), False),
    ("C20", "the zero-interference rung is no longer called indistinguishable", "manuscript.md",
     repall("indistinguishable", "comparable"), False),
    ("C21", "the separation threshold claim is reworded", "manuscript.md",
     rep1("onward", "forward"), False),
    ("C22", "the k = 8 ladder mean in the manuscript changed", "manuscript.md",
     rep1("| k = 8 | **-0.554** |", "| k = 8 | **-0.555** |"), False),
    ("C23", "the matched-control difference changed everywhere it is quoted", "manuscript.md",
     repall("-0.155", "-0.156"), False),
    ("C24", "the matched pair count changed everywhere it is quoted", "manuscript.md",
     repall("12 matched pairs", "11 matched pairs"), False),
    ("C25", "the worst single cell is misquoted", "manuscript.md",
     repall("-1.926", "-1.927"), False),
    ("C26", "the bracket tolerance claim is changed", "manuscript.md",
     rep1("0.003-nat inversion", "0.004-nat inversion"), False),
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
     repall("84 cells", "83 cells"), False),
    ("C10", "the no-distractor denominator moves in the artefact", "canonical_results.json",
     set_derived("n_no_distractor", 7), False),
    ("C11", "the sign-test ratio changed", "manuscript.md",
     rep1("31/36", "30/36"), False),
    ("C13", "the held-out bits/token changed", "manuscript.md",
     rep1("5.242516", "5.242517"), False),
    ("C14", "the KV-cache exactness claim is no longer exact", "manuscript.md",
     rep1("logit difference 0.0", "logit difference 0.1"), False),
    ("C15", "a second References heading is added", "manuscript.md",
     rep1("\n## References\n", "\n## References\n\n## References\n"), False),
    ("C16", "one bibliography entry is deleted", "manuscript.md", lambda t: re.sub(
        r"\n\[[0-9]+\][^\n]*", "", t, count=1), False),
    ("C17", "every in-text citation of one entry is removed", "manuscript.md",
     repall("[105]", ""), False),
    # --- the package's specification vs the package (C27-C33)
    ("C27", "one row of the README file-hash table no longer matches its file", "README.md",
     flip_row("run.log"), False),
    ("C28", "a stale hash appears in README prose (not in the hash table)", "README.md",
     rep1("**Tolerance: exact, not statistical.**",
          "**Tolerance: exact, not statistical.** (superseded run 8dc43a9cc1d0a982)"), False),
    ("C29", "the expected-output payload is not a 16-digit prefix of the artefact", "README.md",
     rep1("canonical payload sha256: e801274596d9b662\n",
          "canonical payload sha256: e801274596d9b6621ccf\n"), False),
    ("C30", "the status paragraph quotes a superseded artefact file hash", "README.md",
     rep1("byte-identical to the committed file (`cmp` reports no difference; file sha256\n"
          "`69960d951cfaa2231152932515feadbc984f0a9f3acf596d5387ddf305df712c`",
          "byte-identical to the committed file (`cmp` reports no difference; file sha256\n"
          "`de241d916e5885a82a6ecea8f258a2b47705b546f89c427e49dec9cc0d303a6e`"), False),
    ("C31", "the tier table reverts to the pre-revision sweep-cell count", "README.md",
     rep1("all 84 sweep cells from the corpus definitions",
          "all 48 sweep cells from the corpus definitions"), False),
    ("C32", "the stated validation tally reverts to the pre-revision split", "README.md",
     rep1("it asserts 38 individual conditions (16 structural, 22 mechanism)",
          "it asserts 37 individual conditions (14 structural, 23 mechanism)"), False),
    ("C33", "one stated consistency count is stale", "README.md",
     rep1("    CONSISTENCY 36/36\n", "    CONSISTENCY 35/35\n"), False),
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
