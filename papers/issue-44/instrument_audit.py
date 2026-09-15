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
# changes with them is evidence about the checkout, not about the artefact.
#
# TWO DETECTORS PER CLASS, AND A ROW NAMES THE ONE THAT DECIDES IT.  A re-check of this census found
# its rows printing "0 site(s) ... none: the read cannot occur" while the detector was a set of
# *spellings*: the zero was a statement about the pattern set, published as a statement about the
# package.  An aliased import (`import time as t` ... `t.time()`), or another spelling of the same
# read (`wget`, `http.client.HTTPSConnection`), moved neither the count nor the note.  The census
# therefore runs two detectors per class and prints both:
#
#   * STRUCTURAL -- each Python source is parsed, import aliases are resolved to dotted names, and
#     every CALL is tested against the class's resolved callable set (and, for the two classes whose
#     read lives in a binary name, against the first argument of a subprocess call).  A rename
#     cannot evade it, so where a class has a callable form THIS count decides the disposition, and
#     `0` means "no call in this package resolves to a construct of this class".
#   * PATTERN -- the published spelling set, because a spelling set is readable evidence in a way an
#     AST walk is not, and because a `.sh` file cannot be parsed as Python.  It is a NET, not a
#     proof: a read in a spelling it does not carry is invisible to it.
#
# A row with no callable form (C2 above-package read: a path, not a call) says so, and its zero --
# were it zero -- would be a statement about spellings only.  Every row prints its instrument and
# its disposition, and every pattern match that no call was found on is printed with what it is
# (comment, string, prose), so no count is read as more than it measures.
#
# DISPOSITIONS, printed with each row:
#   REQUIRED EMPTY      no read of this class may occur anywhere; a structural site fails the audit
#   CONFINED:<module>   reads may occur only in that module (the one that declares the coordinate)
#   DECLARED:<control>  reads exist and are declared, with the compensating control named
#   INFORMATIONAL       reported, not gated: the row answers "where can a coordinate enter?"
COORD_CLASSES = [
    # (class, disposition, pattern set, resolved callables | None, subprocess binaries | None)
    ("C1 git object read", "CONFINED:coordinate_evidence_v1.py",
     r'\["git",|"git"\s*,\s*"|\bgit\s+(?:show|rev-parse|log|diff|status)\b',
     None, ("git",)),
    ("C2 above-package read", "DECLARED:verify_refs.repo_root() -> None when absent",
     r'refgate\.py|repo_root|\.github/tools|dirname\(HERE\)',
     None, None),
    ("C3 environment", "INFORMATIONAL",
     r'os\.environ|getenv|PYTHONPATH',
     ("os.environ", "os.getenv", "os.putenv"), None),
    ("C4 argv", "INFORMATIONAL",
     r'sys\.argv|argparse\.',
     ("sys.argv", "argparse.ArgumentParser"), None),
    ("C5 cwd / absolute path", "INFORMATIONAL",
     r'cwd=|abspath|getcwd|chdir',
     ("os.getcwd", "os.path.abspath", "os.chdir", "pathlib.Path.cwd"), None),
    ("C6 network", "CONFINED:verify_refs.py",
     r'\bcurl\b|\bwget\b|urlopen|urllib\.request|requests\.(?:get|post)|socket\.socket|'
     r'http\.client|HTTPSConnection|ftplib|smtplib',
     # `curl` is this package's own helper: it is where the binary is run, so every site that calls
     # it reaches the network, and the class's structural count must include those call sites.
     ("curl", "socket.socket", "socket.create_connection", "socket.getaddrinfo",
      "urllib.request.urlopen", "urllib.request.Request",
      "http.client.HTTPSConnection", "http.client.HTTPConnection",
      "ftplib.FTP", "smtplib.SMTP", "xmlrpc.client.ServerProxy"),
     ("curl", "wget", "nc", "ncat", "ssh", "scp", "sftp", "ftp", "dig", "host", "nslookup",
      "ping", "telnet")),
    ("C7 clock / entropy", "REQUIRED EMPTY",
     r'time\.time\(|time\.monotonic|perf_counter|datetime\.|os\.urandom|uuid4|secrets\.|'
     r'random\.(?!Random)',
     ("time.time", "time.monotonic", "time.perf_counter", "time.time_ns", "time.process_time",
      # declared as SUFFIXES: the same construct resolves to `datetime.now` or
      # `datetime.datetime.now` depending on how the module was imported.
      "datetime.now", "datetime.utcnow", "datetime.today", "datetime.fromtimestamp",
      "os.urandom", "uuid.uuid4", "secrets.token_bytes", "secrets.token_hex", "secrets.randbelow", "random.random", "random.randrange",
      "random.randint", "random.choice", "random.shuffle", "random.sample", "random.uniform",
      "random.gauss"), None),
    ("C8 interpreter", "INFORMATIONAL",
     r'sys\.version|platform\.python_version',
     ("sys.version", "sys.version_info", "platform.python_version"), None),
    ("C9 dynamic surface", "INFORMATIONAL: what a static detector cannot reach",
     r'\bgetattr\s*\(|\bsetattr\s*\(|\beval\s*\(|\bexec\s*\(|importlib|__import__',
     ("getattr", "setattr", "delattr", "eval", "exec", "compile", "__import__", "vars",
      "globals", "locals", "importlib.import_module"), None),
]
# The call forms a subprocess entry point can take: which class a subprocess call belongs to is
# decided by the BINARY in its first argument, not by the callable, so it is a separate rule.
SUBPROCESS_CALLS = ("subprocess.run", "subprocess.Popen", "subprocess.call",
                    "subprocess.check_call", "subprocess.check_output",
                    "subprocess.getoutput", "subprocess.getstatusoutput")
# Keyword arguments that ARE the coordinate.  A call carrying one is a site of that class whatever
# callable it is: without this rule `subprocess.run(cmd, cwd=...)` reaches the working directory
# while the class that exists to report it counts nothing.  (The excluded span needs no table of its
# own: it is checked with the same alias-resolving detector, so a read through a renamed module is
# still a read there.)
COORD_KWARGS = {"C5 cwd / absolute path": ("cwd",)}
# Each class's PATTERN SET must match a planted instance -- a detector that never fires is
# decoration.  These live HERE and nowhere else, so the audit body carries no read to trip on.
COORD_CANARIES = {
    "C1 git object read": 'r = subprocess.run(["git", "show", "HEAD:a.py"], cwd=".")',
    "C2 above-package read": 'r = subprocess.run([sys.executable, ".github/tools/refgate.py", rel])',
    "C3 environment": 'u = os.getenv("HOME"); env = dict(os.environ)',
    "C4 argv": 'ap = argparse.ArgumentParser(); args = sys.argv[1:]',
    "C5 cwd / absolute path": 'HERE = os.path.abspath(os.getcwd())',
    "C6 network": 'r = subprocess.run(["curl", "-s", url])',
    "C7 clock / entropy": 't = time.time()',
    "C8 interpreter": 'v = platform.python_version(); n = sys.version_info',
    "C9 dynamic surface": 'f = getattr(mod, name); g = eval(src)',
}
# The probes the earlier census MISSED: a read in a spelling its pattern set does not contain, so
# the structural detector is the only thing that can catch it.  A control that plants the pattern's
# own example proves only that the pattern matches itself, which is what this table exists to stop
# being the whole test.  `invisible` is asserted below, not asserted by hand.
COORD_ALIAS_PROBES = [
    ("C7", "import time as t\nt = t.time()", "the module renamed by `import ... as`"),
    ("C7", "from time import time as tm\nx = tm()",
     "the callable renamed by `from ... import ... as`"),
    ("C7", "from datetime import datetime as dt\nx = dt.now()",
     "the class renamed, so the call resolves to a path the net never spells"),
    ("C6", 'import subprocess\nr = subprocess.run(["wget", "-q", url])',
     "another network binary the pattern set never named"),
    ("C6", "import http.client\nc = http.client.HTTPSConnection(host)",
     "a network client built through a dotted module path"),
    ("C1", 'import subprocess as sp\nb = sp.run(["git", "show", "HEAD:x"])',
     "a git read through a renamed subprocess module"),
    ("C1", 'import subprocess\nb = subprocess.check_call("git show HEAD:a.py", shell=True)',
     "a git read in the shell-STRING form, which the list-form rule would not see"),
    ("C9", 'import sys as s\nf = vars(s)["modules"].get(name)',
     "a dynamic lookup spelled with `vars`, which no pattern above names"),
]
CENSUS_SELF = "instrument_audit.py"
COORD_SOURCES = sorted(f for f in os.listdir(PKG) if f.endswith((".py", ".sh")))
# --- census declaration: end --------------------------------------------------------------------


def split_census_declaration(text):
    """(region, outside): the span holding this census's own data, and the file proper.

    The census scans the package it lives in, so it necessarily contains the patterns, callable
    names and probe strings it searches for.  Those are DATA: nothing in the span reads a
    coordinate, and the checks assert that structurally.  The span is delimited by the two banner
    lines; an exclusion wider than what it excludes would be the same defect this census is being
    audited for, so the boundary is drawn at the data and the file that holds it stays inside the
    scan (asserted below, by planting a read in this file OUTSIDE the span).
    """
    bs = [m.start() for m in re.finditer(r"^# --- census declaration: begin.*$", text, re.M)]
    es = [m.end() for m in re.finditer(r"^# --- census declaration: end.*$", text, re.M)]
    if len(bs) != 1 or len(es) != 1 or es[0] < bs[0]:
        raise ValueError("census declaration banners: %d begin, %d end" % (len(bs), len(es)))
    return text[bs[0]:es[0]], text[:bs[0]] + text[es[0]:]


def textual_census(sources):
    """{class: {file: [(lineno, stripped line, match start col, match end col)]}}: the spelling net."""
    cen = {}
    for cls, _d, pat, _c, _b in COORD_CLASSES:
        hits = {}
        for name in sorted(sources):
            out = []
            for i, l in enumerate(sources[name].split("\n")):
                m = re.search(pat, l)
                if m:
                    out.append((i + 1, l.strip(), m.start(), m.end()))
            if out:
                hits[name] = out
        cen[cls] = hits
    return cen


def resolved_bindings(tree):
    """binding -> dotted name, from the module's own imports: that is what makes an alias visible."""
    b = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                b[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            for a in node.names:
                b[a.asname or a.name] = ("%s.%s" % (base, a.name)) if base else a.name
    return b


def dotted(func, binds):
    """The dotted name a call site resolves to, or None when it is not a static name at all."""
    parts = []
    node = func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    # the head is the module binding and the attributes follow it in source order: `a.b.c` -> a.b.c
    return ".".join([binds.get(node.id, node.id)] + list(reversed(parts)))


def matches(resolved, callables):
    """True when `resolved` IS a declared construct of this class, or reaches one.

    A DOTTED declaration matches a longer or shorter resolution (`datetime.now` for
    `datetime.datetime.now`, `os.environ` for `os.environ.copy`).  A BARE declaration (a builtin --
    `getattr`, `compile`, `vars`) matches only itself, or itself under `builtins.`: without that
    rule `re.compile` would be booked as the builtin `compile`, which is a different construct.
    """
    for c in callables:
        if resolved == c:
            return True
        if "." in c:
            if resolved.endswith("." + c) or resolved.startswith(c + "."):
                return True
        elif resolved == "builtins." + c:
            return True
    return False


def structural_census(sources):
    """({class: {file: [(lineno, resolved)]}}, {file: set(call linenos)},
        {file: {lineno: [(callee_start_col, callee_end_col)]}}).

    Three rules per Call: the resolved callable set, the subprocess binary in the first argument,
    and the keyword-argument set.  Attribute LOADS of a declared construct are counted as well,
    because a construct can be read without being called (`dict(os.environ)`).  `.sh` files cannot
    be parsed as Python: they are absent from all three maps, and the run prints that rather than
    counting them as clean.  The third map is what lets a spelling-only match be classified
    honestly -- a match whose span is not a callee is not a call this detector missed.
    """
    cen = {cls: {} for cls, _d, _p, _c, _b in COORD_CLASSES}
    call_lines, callee_spans = {}, {}
    for name in sorted(sources):
        if not name.endswith(".py"):
            continue
        try:
            tree = ast.parse(sources[name])
        except SyntaxError:
            continue
        binds = resolved_bindings(tree)
        lines, spans, funcs = set(), {}, []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            lines.add(node.lineno)
            funcs.append(id(node.func))
            if hasattr(node.func, "col_offset"):
                spans.setdefault(node.lineno, []).append(
                    (node.func.col_offset, node.func.end_col_offset))
            r = dotted(node.func, binds)
            if r is None:
                continue
            binary = None
            if r in SUBPROCESS_CALLS and node.args:
                first = node.args[0]
                if isinstance(first, (ast.List, ast.Tuple)) and first.elts:
                    e0 = first.elts[0]
                    if isinstance(e0, ast.Constant) and isinstance(e0.value, str):
                        binary = e0.value
                elif isinstance(first, ast.Constant) and isinstance(first.value, str):
                    # the shell-STRING form: `subprocess.call("git show HEAD", shell=True)`.  The
                    # binary is the first token, and the list-form rule above would not see it.
                    toks = first.value.split()
                    binary = toks[0] if toks else None
            kws = [k.arg for k in node.keywords if k.arg]
            for cls, _d, _p, calls, bins in COORD_CLASSES:
                note = None
                if calls and matches(r, calls):
                    note = r
                elif bins and r in SUBPROCESS_CALLS and binary in bins:
                    note = r + "/binary=" + binary
                elif kws and any(k in COORD_KWARGS.get(cls, ()) for k in kws):
                    note = r + "/kw=" + ",".join(k for k in kws if k in COORD_KWARGS[cls])
                if note:
                    cen[cls].setdefault(name, []).append((node.lineno, note))
        for node in ast.walk(tree):                     # attribute loads of a declared construct
            if not isinstance(node, ast.Attribute) or id(node) in funcs:
                continue
            r = dotted(node, binds)
            if r is None:
                continue
            for cls, _d, _p, calls, _b in COORD_CLASSES:
                if calls and matches(r, calls):
                    cen[cls].setdefault(name, []).append((node.lineno, r + " (load)"))
        call_lines[name] = lines
        callee_spans[name] = spans
    return cen, call_lines, callee_spans


def _wrap(names, width=86, indent=13):
    """The instrument, spelled out: a count would be the same defect at a smaller scale."""
    out, line = [], ""
    for n in names:
        if len(line) + len(n) + 2 > width:
            out.append(line)
            line = ""
        line = (line + ", " + n) if line else n
    if line:
        out.append(line)
    return [(" " * indent) + l for l in out]


def d5():
    region, outside = split_census_declaration(read(CENSUS_SELF))
    calls = sorted(set("%s.%s" % (n.func.value.id, n.func.attr)
                       for n in ast.walk(ast.parse(region))
                       if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                       and isinstance(n.func.value, ast.Name)))
    # The span is DATA, and this check must be as hard to evade as the census it audits: it runs the
    # census's own alias-resolving detector over the span, so a read written through a renamed
    # module is a read here too.
    span_cen, _sl, _sp = structural_census({"span.py": region})
    span_hits = [(c, ln, r) for c, hits in span_cen.items()
                 for _f, v in sorted(hits.items()) for ln, r in v]
    check("D5/the census excludes a declaration span that READS no coordinate (structural,"
          " alias-resolving)",
          not span_hits,
          "%d line(s) of %s excluded; the span's only calls are %s; structural hits: %s"
          % (region.count("\n") + 1, CENSUS_SELF, ", ".join(calls) or "none",
             ", ".join("%s:%d %s" % h for h in span_hits) or "none"))

    sources = {f: read(f) for f in COORD_SOURCES}
    sources[CENSUS_SELF] = outside
    txt = textual_census(sources)
    stc, call_lines, callee_spans = structural_census(sources)
    unparsed = sorted(f for f in COORD_SOURCES if not f.endswith(".py"))
    print("       coordinate census over %d source file(s); the structural detector parses %d"
          " Python file(s); the spelling net also covers %s"
          % (len(sources), len(sources) - len(unparsed), ", ".join(unparsed) or "none"))

    problems, kind_of = [], {}
    for cls, disposition, pat, callables, bins in COORD_CLASSES:
        n_s = sum(len(v) for v in stc[cls].values())
        n_t = sum(len(v) for v in txt[cls].values())
        structural = bool(callables) or bool(bins)
        print("         %-22s structural %2d | spellings %2d | %s" % (cls, n_s, n_t, disposition))
        if structural:
            if callables:
                print("           instrument (decides this row): %d resolved callable(s)"
                      % len(callables))
                for l in _wrap(callables, indent=13):
                    print(l)
            else:
                print("           instrument (decides this row): subprocess binaries %s"
                      % ", ".join(bins))
        else:
            print("           instrument: SPELLING NET ONLY -- this class has no callable form"
                  " (a path, not a call); an unspelled form of it is not counted")
        print("           spelling net: %s" % pat)
        for f in sorted(stc[cls]):
            for ln, r in stc[cls][f][:8]:
                print("           READ: %s:%d  %s" % (f, ln, r))
            if len(stc[cls][f]) > 8:
                print("           READ: ... %d more in %s" % (len(stc[cls][f]) - 8, f))
        # A spelling match whose span IS a call's callee, and which the callable set did not flag,
        # is an INSTRUMENT GAP: this class's own structural surface is incomplete, and its zero
        # would be too wide.  The rest are classified rather than assumed -- the census's own prose
        # about itself, a string, a keyword argument, a shell line it cannot parse.
        for f in sorted(txt[cls]):
            for ln, l, s0, s1 in txt[cls][f]:
                if any(ln == s[0] for s in stc[cls].get(f, [])):
                    continue
                is_callee = any(s0 < e and s1 > b
                                for b, e in callee_spans.get(f, {}).get(ln, []))
                if is_callee:
                    kind = "CALL -- INSTRUMENT GAP" if structural else "callee (textual class)"
                elif f not in call_lines:
                    kind = "shell line (no Python parse)"
                elif l.startswith("#"):
                    kind = "comment"
                else:
                    kind = "string / prose"
                print("           spelling-only (%s): %s:%d  %s" % (kind, f, ln, l[:74]))
                kind_of[(cls, f, ln)] = kind
                if kind.startswith("CALL --"):
                    problems.append("%s: the spelling net matched a callee at %s:%d that the "
                                    "callable set did not flag: %s" % (cls, f, ln, l[:60]))
        if disposition == "REQUIRED EMPTY" and n_s:
            problems.append("%s is REQUIRED EMPTY but has %d structural site(s)" % (cls, n_s))
        if disposition.startswith("CONFINED:"):
            allowed = disposition.split(":", 1)[1]
            others = sorted(set(stc[cls]) - {allowed})
            if others:
                problems.append("%s is confined to %s but reads occur in %s"
                                % (cls, allowed, ", ".join(others)))

    # (1) every class's SPELLING NET fires on a planted instance
    blind = [cls for cls, line in COORD_CANARIES.items()
             if not textual_census({"planted.py": line})[cls]]
    check("D5/every class's spelling net fires on a planted instance (a silent detector is decoration)",
          not blind, "%d of %d fire" % (len(COORD_CLASSES) - len(blind), len(COORD_CLASSES)))
    # (2) the canary of every class that HAS a callable form is caught by BOTH detectors: the class's
    # spelling net and its structural set must agree on the class's own example, or one of the two is
    # describing something else.
    disagree = []
    for cls, disposition, _p, callables, bins in COORD_CLASSES:
        if not (callables or bins):
            continue
        cen = structural_census({"planted.py": COORD_CANARIES[cls]})[0]
        if not cen[cls]:
            disagree.append(cls)
    check("D5/the spelling net and the callable set agree on every structural class's own example",
          not disagree, "classes where the canary is a spelling but not a resolved call: %s"
                        % (", ".join(disagree) if disagree else "none"))
    # (3) the STRUCTURAL detector catches reads in spellings the net does not contain -- the control
    # the earlier census lacked, and whose absence let a zero be printed as "the read cannot occur"
    # on the strength of a spelling net alone.
    caught, missed, invisible = [], [], 0
    for prefix, src, why in COORD_ALIAS_PROBES:
        cls = next(c for c, _d, _p, _c, _b in COORD_CLASSES if c.startswith(prefix))
        s_hit = bool(structural_census({"probe.py": src})[0][cls])
        t_hit = bool(textual_census({"probe.py": src})[cls])
        if s_hit:
            caught.append((cls, why, t_hit))
        else:
            missed.append((cls, why))
        if s_hit and not t_hit:
            invisible += 1
    check("D5/the STRUCTURAL detector catches every read whose spelling the net does not carry",
          not missed, "caught %d of %d" % (len(caught), len(COORD_ALIAS_PROBES)))
    check("D5/at least one probe IS invisible to the spelling net (else the control never leaves the"
          " surface the earlier census tested)", invisible >= 1,
          "%d of %d probes were caught by the callable set and not by the net"
          % (invisible, len(caught)))
    for cls, why, t_hit in caught:
        print("           alias probe caught: %-8s %s%s" % (cls.split()[0], why,
              " (the net also matches this spelling)" if t_hit else " (INVISIBLE to the net)"))
    # (4) the confinement and emptiness requirements, each with its control
    check("D5/the package's only git object read is the module that declares the coordinate",
          set(stc["C1 git object read"]) == {"coordinate_evidence_v1.py"},
          "C1 structural sites: %s" % (sorted(stc["C1 git object read"]) or "none"))
    leak = dict(sources)
    leak["leaky.py"] = COORD_CANARIES["C1 git object read"]
    check("D5/MUTATION: a leaked git read in another module is caught",
          set(structural_census(leak)[0]["C1 git object read"]) != {"coordinate_evidence_v1.py"},
          "planted a git read in leaky.py")
    leak2 = dict(sources)
    leak2[CENSUS_SELF] = outside + COORD_CANARIES["C1 git object read"] + "\n"
    check("D5/MUTATION: a git read in this file OUTSIDE the excluded span is still caught",
          set(structural_census(leak2)[0]["C1 git object read"]) != {"coordinate_evidence_v1.py"},
          "the exclusion is a boundary, not an immunity")
    check("D5/the network class is CONFINED to the resolver, which is what its row says",
          set(stc["C6 network"]) == {"verify_refs.py"},
          "C6 structural sites: %s" % (sorted(stc["C6 network"]) or "none"))
    c7 = next(c for c, _d, _p, _c, _b in COORD_CLASSES if c.startswith("C7"))
    c7_spell = [(f, ln) for f in txt[c7] for ln, _l, _a, _b2 in txt[c7][f]]
    c7_callee = [(f, ln) for (c, f, ln), kind in kind_of.items()
                 if c == c7 and kind.startswith(("CALL", "callee"))]
    check("D5/no clock read and no unseeded entropy read: 0 STRUCTURAL sites, and every"
          " spelling-only match is prose rather than a callee",
          not stc[c7] and not c7_callee,
          "C7: %d structural site(s); the net matched %d line(s), of which %d are a callee"
          % (sum(len(v) for v in stc[c7].values()), len(c7_spell), len(c7_callee)))
    clk = dict(sources)
    clk["clock.py"] = "import time as t\nx = t.time()\n"
    check("D5/MUTATION: an unseeded clock read is caught even when the module is RENAMED",
          bool(structural_census(clk)[0][c7]),
          "planted `import time as t; t.time()` -- the spelling the net would miss")
    c9 = next(c for c, _d, _p, _c, _b in COORD_CLASSES if c.startswith("C9"))
    probe = {"probe.py": "import http.client\nc = getattr(http.client, 'HTTPSConnection')(host)"}
    pstc = structural_census(probe)[0]
    elsewhere = [c for c in pstc if c != c9 and pstc[c]]
    check("D5/the boundary is a ROW, not an inference: a read whose callee is built at runtime is"
          " reported under C9 and by no other structural class",
          bool(pstc[c9]) and not elsewhere,
          "at this head C9 has %d structural site(s) and the net matches %d line(s); the"
          " runtime-built probe is caught by %s"
          % (sum(len(v) for v in stc[c9].values()), sum(len(v) for v in txt[c9].values()),
             ", ".join(c.split()[0] for c in elsewhere) or "C9 only"))
    # (5) the declared / informational classes, each with the line that makes it harmless named, so
    # the census answers "where can a coordinate enter?" line by line rather than by absence of hits
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

    for p in problems:
        print("       CENSUS VIOLATION: %s" % p)
    return len(problems)


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
