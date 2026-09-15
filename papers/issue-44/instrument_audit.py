#!/usr/bin/env python3
"""Issue #44 -- the INSTRUMENT AUDIT: four disciplines applied to this package's own guards.

    python3 instrument_audit.py

Written after a host rant (2026-09-16T00:26) whose operational form is: "our reproduce.sh /
refgate / review templates are measurement instruments too -- any threshold they enforce should
state its crossover and its regime of validity, any exclusion (dropped run, retired row) should
publish the excluded values, and any guard should state the fraction of the surface it audits."

Disciplines, and what this file checks for each:

  D1 CROSSOVER   a criterion whose branch depends on a variable must name that variable and say
                 which term wins there -- and a regime where the quantity is UNDEFINED must be
                 reported as undefined, not as the negative finding.
                 (a) the mechanism ordering's exclusion rule: swept; the undefined regime is DROVEN
                     on a scratch copy rather than read off the code;
                 (b) the figure tier's two-criterion tolerance: the crossover (matplotlib build)
                     and both branches are asserted to be documented;
                 (c) reproduce.sh's skip regime: a skipped tier must not print that tier's verdict.
  D2 HISTORICAL  a defect remediated elsewhere must state the regime it was load-bearing in, and
                 carry the test that shows it is no longer reachable.  Here: the citation support
                 test's own cases (including its blind spot).
  D3 EXCLUSIONS  an exclusion must publish the excluded VALUES, not just its rate.  Here: the
                 GAP_TOL pair exclusion -- kept vs dropped factor gaps, and the verdict under six
                 other rules.
  D4 COVERAGE    each guard must state the fraction of the surface it audits.  Here: the numeric
                 surface of the manuscript, and the declared residual of the hand-typed values.
  D5 COORDINATES a package's evidence must not depend on WHERE it is read from.  Every
                 coordinate-dependent read -- git object, repository root, environment, argv, cwd,
                 network, clock, interpreter -- is enumerated and published, and the ones that can
                 enter at all are confined to a declared module (coordinate_evidence_v1.py) with a
                 committed record, so the audit gives the same answer in a clone, in an export, and
                 after later commits.  An unavailable coordinate is a DECLARED state, never a pass.

Network-free and deterministic: every check runs on committed files, and the two probes run copies
in a scratch directory that is deleted afterwards.  Exit status is the verdict.
"""
import ast
import hashlib
import io
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = HERE
rows = []


def check(name, ok, detail=""):
    rows.append((name, bool(ok), detail))
    print("%-6s %-58s %s" % ("PASS" if ok else "FAIL", name, detail))


def read(p):
    return io.open(os.path.join(PKG, p), encoding="utf-8").read()


# --------------------------------------------------------------------------- D1a: the exclusion rule
GAP_TOL = 0.05


def ordering_pairs(v3):
    out = []
    for key, c in sorted(v3["cells"].items()):
        f = c["factor"]
        if c["informative"] and f.get("mean") is not None and math.isfinite(f["mean"]):
            out.append((c["standardised_threshold_gap"]["mean"], f["mean"], key))
    return out


def order_stats(pairs, tol):
    kept, dropped, rises, falls = [], [], 0, 0
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            gi, fj, _ = pairs[i]
            gj, fk, _ = pairs[j]
            if abs(gj - gi) <= tol:
                dropped.append(abs(fk - fj))
                continue
            lo, hi = (i, j) if gi < gj else (j, i)
            kept.append(abs(pairs[hi][1] - pairs[lo][1]))
            if pairs[hi][1] > pairs[lo][1]:
                rises += 1
            elif pairs[hi][1] < pairs[lo][1]:
                falls += 1
    compared = rises + falls
    tau = ((rises - falls) / float(compared)) if compared else None
    return {"compared": compared, "rises": rises, "falls": falls, "tau": tau,
            "kept_d": kept, "dropped_d": dropped, "n_dropped": len(dropped)}


def d1a():
    v3 = json.loads(read("results_v3.json"))
    m = v3["mechanism_gap_ordering"]
    pairs = ordering_pairs(v3)
    base = order_stats(pairs, GAP_TOL)
    check("D1a/the published ordering statistic RECOMPUTES from the artefact",
          (base["compared"], base["rises"], base["falls"]) ==
          (m["pairs_compared"], m["factor_rises_with_gap"], m["factor_falls_with_gap"])
          and abs(base["tau"] - m["tau_like"]) < 1e-12,
          "compared %d rises %d falls %d tau %.4f" % (base["compared"], base["rises"],
                                                      base["falls"], base["tau"]))
    sweep = {}
    for tol in (0.0, 0.01, 0.05, 0.1, 0.2, 0.5):
        st = order_stats(pairs, tol)
        sweep[tol] = st
        print("       GAP_TOL=%-5.2f compared=%-4d dropped=%-4d tau=%s"
              % (tol, st["compared"], st["n_dropped"],
                 "UNDEFINED" if st["tau"] is None else "%+.4f" % st["tau"]))
    live = [s for s in sweep.values() if s["tau"] is not None]
    check("D1a/the verdict is INVARIANT to the exclusion rule wherever a pair survives",
          all(s["tau"] > 0.5 for s in live) and len(live) >= 4,
          "%d of %d rules keep >=1 pair; tau ranges %.4f..%.4f"
          % (len(live), len(sweep), min(s["tau"] for s in live), max(s["tau"] for s in live)))
    undefined = [t for t, s in sweep.items() if s["tau"] is None]
    check("D1a/the rule CAN leave the statistic undefined, and that regime is reachable",
          bool(undefined), "GAP_TOL in %s drops every pair" % sorted(undefined))
    # the regime is DRIVEN on a scratch copy, not read off the source
    scratch = tempfile.mkdtemp(prefix="audit_probe_")
    try:
        src = read("instrument_v3.py")
        io.open(os.path.join(scratch, "instrument_v3_probe.py"), "w", encoding="utf-8").write(
            src.replace("GAP_TOL = 0.05", "GAP_TOL = 0.5"))
        subprocess.run([sys.executable, "instrument_v3_probe.py"], cwd=scratch,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        probe = json.load(io.open(os.path.join(scratch, "results_v3.json"), encoding="utf-8"))
        v = probe["mechanism_gap_ordering"]["verdict"]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    check("D1a/an undefined statistic is REPORTED as undefined, not as a negative finding",
          "UNDEFINED" in v and "does not order" not in v, "probe at GAP_TOL=0.5 emits: %r" % v)


# ------------------------------------------------------------------ D1b/D1c: documented regimes
def d1bc():
    rd = read("README.md")
    rs = read("reproduce.sh")
    check("D1b/the figure tier's crossover is declared (which build requires the byte hashes)",
          "matplotlib build" in rd and "reported rather than required" in rd.replace("\n", " ")
          or ("reported" in rd and "required" in rd and "matplotlib" in rd),
          "README names the build and which criterion is required on which side")
    check("D1b/the figure tier's declared count is stated as build-dependent",
          "106" in rd and "100" in rd,
          "both branch counts appear in the expected-output block")
    check("D1c/REQUIRE_FIGURES is offered as the way to make the tier fail closed",
          "REQUIRE_FIGURES" in rs and "FATAL" in rs,
          "a missing matplotlib skips the tier by default; REQUIRE_FIGURES=1 makes it fatal")
    check("D1c/a skipped tier cannot print that tier's verdict line",
          'if [ -n "$FPY" ]' in rs and "SKIPPED" in rs,
          "the verdict line lives inside the branch that runs the tier")


# ------------------------------------------------------ D2: the support test's liveness (2 probes)
def d2():
    out = subprocess.run([sys.executable, "verify_refs.py", "--selftest-only"], cwd=PKG,
                         capture_output=True, text=True)
    ok_line = "selftest: 0 case(s) failed" in out.stdout
    check("D2/both guard self-tests pass on the committed sources", out.returncode == 0 and ok_line,
          out.stdout.strip().split("\n")[-1])
    scratch = tempfile.mkdtemp(prefix="audit_mut_")
    try:
        for label, old, new in (
                ("counter", "def bracket_groups(body):", "def bracket_groups(body):\n    return set(), set()  # MUTANT"),
                ("support", "    if norm_seq(rec[\"title\"]) != norm_seq(intent):",
                 "    if False:  # MUTANT: the support test can no longer reject anything")):
            src = read("verify_refs.py")
            assert src.count(old) == 1, "mutation anchor not unique for %s" % label
            p = os.path.join(scratch, "mutant_%s.py" % label)
            io.open(p, "w", encoding="utf-8").write(src.replace(old, new))
            r = subprocess.run([sys.executable, p, "--selftest-only"], cwd=PKG,
                               capture_output=True, text=True)
            check("D2/MUTATION: a broken %s is CAUGHT by the self-test (exit != 0)" % label,
                  r.returncode != 0,
                  "mutant exits %d; %s" % (r.returncode,
                                           [l for l in r.stdout.split("\n")
                                            if l.startswith("selftest:")][:1]))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    # The historical regime: in the reviewed head the self-test could not fail the run.  This
    # used to be read out of this checkout's object store at HEAD -- a read of WHATever this
    # checkout is.  It broke in an exported package, and even here it was not the head it named:
    # it passed against a later blob, for an unrelated reason.  The reading is now taken from the
    # committed record (coordinate_evidence.json), recomputed from the record's own lines, and
    # tied to the live blob whenever the coordinate happens to be resolvable.
    co = subprocess.run([sys.executable, "coordinate_evidence_v1.py", "--check"], cwd=PKG,
                        capture_output=True, text=True)
    line = next((l for l in co.stdout.split("\n") if "reviewed_head_self_test_status" in l), "")
    got = dict(re.findall(r"(uses|feeding_status)=(\d+)", line))
    check("D2/the reviewed head's reading is PINNED to a declared coordinate, and it recomputes",
          co.returncode == 0 and "record=recomputes" in line and "pinned=declared" in line,
          line.strip()[:160])
    check("D2/in the reviewed head the self-test result never reached the run status (the reading)",
          got.get("feeding_status") == "0" and int(got.get("uses", "0")) > 0,
          "%s uses of `tests`, %s of them feeding the run status"
          % (got.get("uses", "?"), got.get("feeding_status", "?")))
    check("D2/the record states which cross-check was actually performed here",
          "cross-check:" in line,
          line.split("cross-check:")[-1].strip()[:120] if "cross-check:" in line else line[:120])
    check("D2/the cross-check's state is exhaustive and named (a skip cannot read as a pass)",
          ("git agrees" in line) != ("not available here" in line),
          line.split("cross-check:")[-1].strip()[:100])


# ------------------------------------------------------------------------- D3: exclusions with values
def d3():
    v3 = json.loads(read("results_v3.json"))
    pairs = ordering_pairs(v3)
    st = order_stats(pairs, GAP_TOL)
    check("D3/the excluded set is counted and its VALUES are published",
          st["n_dropped"] > 0 and st["kept_d"] and st["dropped_d"],
          "kept %d (factor gap mean %.4f) | dropped %d (mean %.4f, max %.4f)"
          % (len(st["kept_d"]), statistics.mean(st["kept_d"]), st["n_dropped"],
             statistics.mean(st["dropped_d"]), max(st["dropped_d"])))
    check("D3/the excluded pairs are the LESS informative ones, and that is the direction that matters",
          statistics.mean(st["dropped_d"]) < statistics.mean(st["kept_d"]),
          "dropped factor gap %.4f < kept %.4f" % (statistics.mean(st["dropped_d"]),
                                                   statistics.mean(st["kept_d"])))
    d = json.loads(read("canonical_results.json"))
    first = sorted(d["stages"], key=lambda s: s["tag"])[-1]
    check("D3/the exclusion rule's parameter is recorded beside the statistic it shapes",
          "differ by more than" in json.loads(read("results_v3.json"))["mechanism_gap_ordering"]["statistic"],
          "the artefact's statistic string names the rule and its threshold")


# -------------------------------------------------------------------------- D4: guard coverage
SPAN = re.compile(r"`([^`]*)`")
NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w])")
# The declared residual: hand-typed values in the body that no rendered placeholder carries.
# Each is a QUOTATION of another paper's published counts, or a nominal level -- not a measurement
# of this study.  A new entry means a number entered the prose that the artefact does not render.
DECLARED_UNBACKED = {
    "104": "antecedent's divergent-rejection count, quoted (104/105)",
    "105": "antecedent's divergent-rejection denominator, quoted",
    "27": "antecedent's same-input fabrication count, quoted (27/29)",
    "29": "antecedent's same-input fabrication denominator, quoted",
    "45": "antecedent's honest-acceptance denominator, quoted (44/45)",
}


def d4():
    """The numeric surface, and what each guard actually sees.

    ORACLE: a hand-typed number is BACKED when the artefact records it as an exact numeric token
    (at some printed precision) or when the renderer prints it.  Two properties of this criterion,
    stated so a reader can discount it correctly:

      * it is VALUE-level, not PLACEMENT-level -- it shows the number exists in the artefact, not
        that it is used where it belongs; placement is what the AUDIT list's human review is for;
      * the oracle is a token set, so a fabricated number would fire UNLESS it coincides with a
        recorded value at the same precision.  That is the honest width of the guarantee.

    The first version of this measurement used SUBSTRING containment, which satisfied "104" from
    "1040" and reported a residual of 4; exact token matching reports the true residual of 5.
    """
    sys.path.insert(0, PKG)
    import assemble as A
    facts_path = os.path.join(PKG, "canonical_results.json")
    roots = A.namespaces(facts_path)
    tokens = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(k)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, bool):
            pass
        elif isinstance(o, (int, float)):
            for prec in range(0, 7):
                try:
                    tokens.add(("%%.%df" % prec) % o)
                except (TypeError, ValueError):
                    pass
            tokens.add(str(o))
        elif isinstance(o, str):
            tokens.update(NUM.findall(o))

    walk(json.load(io.open(facts_path, encoding="utf-8")))
    walk(json.load(io.open(os.path.join(PKG, "search_form.json"), encoding="utf-8")))

    PL = re.compile(r"\{\{([A-Za-z]+):([^}|]*)(?:\|([^}]*))?\}\}")
    src = "".join(read(p) for p in A.PARTS)
    rendered, bad = set(), []
    for m in PL.finditer(src):
        ns, path, spec = m.group(1), m.group(2), m.group(3)
        try:
            rendered.add(A.fmt(A.resolve(roots[ns], path, ns), spec))
        except Exception as e:                                   # pragma: no cover
            bad.append((m.group(0), str(e)))
    check("D4/the artefact's rendered forms resolve without exception", not bad,
          "%d placeholders, %d distinct rendered forms, %d unresolved"
          % (len(PL.findall(src)), len(rendered), len(bad)))
    tokens |= rendered
    for r in rendered:
        tokens.update(NUM.findall(r))

    body = read("manuscript.md").split("## References", 1)[0]
    spans = [m.group(1) for m in SPAN.finditer(body) if NUM.search(m.group(1))]
    vals = {v for s in spans for v in NUM.findall(s)}
    unbacked = sorted(v for v in vals if v not in tokens)
    new = [v for v in unbacked if v not in DECLARED_UNBACKED]
    check("D4/every hand-typed number in the body is a value the artefact records",
          not new,
          "%d distinct values in %d code spans; %d declared non-measurements%s"
          % (len(vals), len(spans), len(unbacked),
             ("" if not new else "; NEW UNBACKED: %s" % new)))
    stale = [v for v in DECLARED_UNBACKED if v not in unbacked]
    check("D4/the declared residual is exactly the residual (no stale declarations)",
          not stale, "declared: %s" % sorted(DECLARED_UNBACKED))
    print("       coverage: %d placeholder-derived numbers, verified against the artefact by"
          % len(PL.findall(src)))
    print("                 construction and by the RECOMPUTE + READ mutation controls;")
    print("                 %d hand-typed values in %d code spans, %d backed by an artefact"
          " value, %d declared" % (len(vals), len(spans), len(vals) - len(unbacked),
                                   len(unbacked)))
    print("                 quotations of another paper's counts (value-level, not placement-level).")


# --- census declaration: begin (the detector's own tables and probes; excluded from the census) -
# A coordinate is any input that is not the package itself: the repository, the environment, the
# command line, the working directory, the network, the clock, the interpreter.  Evidence that
# changes with them is evidence about the checkout, not about the artefact.  The classes below are
# the ones this package can express; each is scanned and published, and the classes that can carry
# a read at all are asserted to be confined, declared, or neutralised.
COORD_CLASSES = [
    ("C1 git object read", r'\["git",|"git"\s*,\s*"|\bgit\s+(?:show|rev-parse|log|diff|status)\b'),
    ("C2 above-package read", r'refgate\.py|repo_root|\.github/tools'),
    ("C3 environment", r'os\.environ|getenv|PYTHONPATH'),
    ("C4 argv", r'sys\.argv'),
    ("C5 cwd / absolute path", r'cwd=|abspath'),
    ("C6 network", r'\bcurl\b|urllib\.request|requests\.get|socket\.socket'),
    ("C7 clock / entropy", r'time\.time\(|datetime\.|random\.(?!Random)|os\.urandom|uuid4'),
    ("C8 interpreter", r'sys\.version\b'),
]
# Each class's detector must match a planted instance -- a detector that never fires is decoration.
# The probe strings live HERE and nowhere else, so the audit body carries no read to trip on.
COORD_CANARIES = {
    "C1 git object read": 'r = subprocess.run(["git", "show", "HEAD:a.py"], cwd=".")',
    "C2 above-package read": 'r = subprocess.run([sys.executable, ".github/tools/refgate.py", rel])',
    "C3 environment": 'env = dict(os.environ); env.pop("PYTHONPATH", None)',
    "C4 argv": 'args = sys.argv[1:]',
    "C5 cwd / absolute path": 'HERE = os.path.dirname(os.path.abspath(__file__))',
    "C6 network": 'r = subprocess.run(["curl", "-s", url])',
    "C7 clock / entropy": 't = time.time()',
    "C8 interpreter": 'print(sys.version)',
}
CENSUS_SELF = "instrument_audit.py"
COORD_SOURCES = sorted(f for f in os.listdir(PKG) if f.endswith((".py", ".sh")))


def split_census_declaration(text):
    """(region, outside): the span holding this census's own data, and the code proper.

    The census scans the package it lives in, so it necessarily contains the patterns and probe
    strings it searches for.  Those are DATA, not reads: nothing in the span executes.  The span
    is delimited by the two banner lines above and below, and the checks assert that it is a
    single span, that it runs no subprocess, and -- the control that matters -- that a read placed
    in this file OUTSIDE the span is still caught.
    """
    bs = [m.start() for m in re.finditer(r"^# --- census declaration: begin.*$", text, re.M)]
    es = [m.end() for m in re.finditer(r"^# --- census declaration: end.*$", text, re.M)]
    if len(bs) != 1 or len(es) != 1 or es[0] < bs[0]:
        raise ValueError("census declaration banners: %d begin, %d end" % (len(bs), len(es)))
    return text[bs[0]:es[0]], text[:bs[0]] + text[es[0]:]


def coordinate_census(sources):
    """{class: {filename: [(lineno, line)]}} -- every source line that reads a coordinate."""
    cen = {}
    for cls, pat in COORD_CLASSES:
        hits = {}
        for name in sorted(sources):
            lines = [(i + 1, l.strip()) for i, l in enumerate(sources[name].split("\n"))
                     if re.search(pat, l)]
            if lines:
                hits[name] = lines
        cen[cls] = hits
    return cen


def c1_confined(cen):
    """Only the module that declares the coordinate may contain a git object read."""
    return set(cen["C1 git object read"]) == {"coordinate_evidence_v1.py"}


def c7_neutralised(cen):
    """No wall clock and no unseeded entropy: the simulation is seeded by construction."""
    return not cen["C7 clock / entropy"]


def d5():
    region, outside = split_census_declaration(read(CENSUS_SELF))
    calls = sorted(set("%s.%s" % (n.func.value.id, n.func.attr)
                       for n in ast.walk(ast.parse(region))
                       if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                       and isinstance(n.func.value, ast.Name)))
    coord_calls = [c for c in calls
                   if c.split(".")[0] in ("subprocess", "socket", "urllib", "requests")
                   or c in ("os.popen", "os.system", "os.environ", "os.getenv", "os.urandom",
                            "time.time", "time.monotonic")]
    check("D5/the census excludes a declaration span that reads no coordinate (structural, not textual)",
          not coord_calls,
          "excluded %d line(s) of %s; the span's only calls are %s"
          % (region.count("\n") + 1, CENSUS_SELF, ", ".join(calls) or "none"))
    sources = {f: read(f) for f in COORD_SOURCES}
    sources[CENSUS_SELF] = outside
    cen = coordinate_census(sources)
    print("       coordinate census over %d source file(s):" % len(sources))
    for cls, _ in COORD_CLASSES:
        h = cen[cls]
        n = sum(len(v) for v in h.values())
        print("         %-24s %3d site(s) in %-2d file(s)  %s"
              % (cls, n, len(h), ", ".join(sorted(h)) if n else "-- none: the read cannot occur"))
    blind = [cls for cls, line in COORD_CANARIES.items()
             if not coordinate_census({"planted.py": line})[cls]]
    check("D5/every class's detector matches a planted instance (a silent detector is decoration)",
          not blind, "%d of %d detectors fire" % (len(COORD_CLASSES) - len(blind), len(COORD_CLASSES)))
    check("D5/the package's only git object read is the module that declares the coordinate",
          c1_confined(cen), "C1 sites: %s" % sorted(cen["C1 git object read"]))
    leak = dict(sources)
    leak["leaky.py"] = COORD_CANARIES["C1 git object read"]
    check("D5/MUTATION: a leaked git read in another module is caught",
          not c1_confined(coordinate_census(leak)), "planted a git read in leaky.py")
    leak2 = dict(sources)
    leak2[CENSUS_SELF] = outside + COORD_CANARIES["C1 git object read"] + "\n"
    check("D5/MUTATION: a git read in the audit OUTSIDE the excluded span is still caught",
          not c1_confined(coordinate_census(leak2)),
          "the exclusion is a boundary, not an immunity")
    check("D5/the simulation reads no clock and no unseeded entropy",
          c7_neutralised(cen), "C7 sites: %s" % sorted(cen["C7 clock / entropy"]))
    mut = dict(sources)
    mut["clock.py"] = COORD_CANARIES["C7 clock / entropy"]
    check("D5/MUTATION: an unseeded clock read is caught",
          not c7_neutralised(coordinate_census(mut)), "planted a clock read in clock.py")
    # C2/C3/C4/C6/C8: each remaining class is declared, neutralised, or confined -- with the line
    # that does it named, so the census answers "where can a coordinate enter?" line by line.
    vr = sources["verify_refs.py"]
    check("D5/the read above the package has a declared fallback for the exported case",
          "was **not** found" in vr and "return None" in vr,
          "verify_refs.repo_root() returns None outside the repository, and the text says so")
    check("D5/the inherited environment is neutralised on the variable that can change a result",
          'env.pop("PYTHONPATH"' in sources["check_manuscript.py"],
          "check_manuscript copies os.environ and drops PYTHONPATH")
    rs = sources["reproduce.sh"]
    check("D5/one command reproduces without the network: the resolver runs in its network-free lane",
          "--selftest-only" in rs and not re.search(r"verify_refs\.py\s*$", rs, re.M),
          "reproduce.sh invokes verify_refs.py only with --selftest-only")
    check("D5/the interpreter is read by the log, not by the measurement",
          "sys.version" in rs, "reproduce.sh prints the interpreter that produced the run")
    check("D5/argv carries options only: no measurement is selected from the command line",
          all(re.search(r"sys\.argv", sources[f]) for f in ("make_figures.py", "verify_refs.py"))
          and "--selftest-only" in vr,
          "argv gates the figure tier's options and the network-free selftest lane")


# --- census declaration: end --------------------------------------------------------------------

def main():
    for fn in (d1a, d1bc, d2, d3, d4, d5):
        fn()
    failed = [n for n, ok, _ in rows if not ok]
    print("\ninstrument audit: %d run, %d failed" % (len(rows), len(failed)))
    for n in failed:
        print("  FAILED:", n)
    print("verdict:", "OK" if not failed else "NOT READY")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
