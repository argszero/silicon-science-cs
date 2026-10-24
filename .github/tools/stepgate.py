#!/usr/bin/env python3
"""stepgate_v1 - the step count a package states, read against the count its script states.

A one-command reproduction ends in a verdict line that carries the number of steps the
run took - `REPRODUCE: ALL GREEN (10 steps)`. That number is a **claim about a program**,
and the package states it in up to three carriers: the script's own header (the block
that tells a reader what the last line will be), `README.md`, and `manuscript.md`. The
program is the authority; the two documents are copies of what it prints.

Why the copies need a collector, stated as the class rather than as a slogan: a step
count is **a number a program produces, written down by hand in two other files**, and
nothing in the tree re-compared any of them until this tool. Measured over this
repository's own record, three times, all three by hand:

  * `papers/issue-145` (in review, R622/R623): `reproduce.sh:12` and `README.md:18` both
    state `(9 steps)` and the run takes **10** - a stale copy, found by running it.
  * `papers/issue-128` (published): the three inline comments above the `--full` blocks
    numbered them `[08]`-`[10]`, the numbers the default tier already uses, while the
    header's own table and the run both said `[11]`-`[13]` - two copies of one
    enumeration disagreeing inside **one file**, found by a census (R626) and repaired
    by hand (R627).
  * `papers/issue-128` (published, still live): `manuscript.md:413` states
    `ALL GREEN (7 steps)` for the default tier and `:414` states `(10 steps)` for
    `--full`, while the script's header, the README and the run all say **10** and
    **13**. The paper tells a reader that a run takes 7 and 10 steps; it takes 10 and 13.

The third is what this tool was written for and what it reports on its first run.

**What this tool reads.** For each `papers/issue-<N>/` package directory, two sides:

  * the **stated claim**, in three carrier kinds and no others:
      - `reproduce.sh`: a literal `(N steps)` on a line that also carries the verdict
        word `REPRODUCE:`, with the tier read off a `# default` / `# --full` marker on
        that same line; or the **one computed form** the tree uses -
        `NAME=$(( $(echo $LIST | wc -w) + K ))` - evaluated as `len($LIST) + K` with
        `$LIST` resolved from its own quoted assignment in the same file;
      - `README.md` / `manuscript.md`: a literal `(N steps)`, with the tier read off the
        invocation it belongs to - `--full` on the same line, else the nearest preceding
        line naming `reproduce.sh` within ten lines, else `unspecified`;
      - a **dated measurement** - `N steps green` beside a date - is a record of one run
        and not a specification of the program, so it is reported as its own kind and
        **not checked** (see *what this tool does not read*).
  * the **script's own count**, from the same two forms. The script is the authority
    because it is the program; where the script states no count for a tier, a copy's
    claim about that tier is reported as **not checked** and never as a pass.

Set equality is not the question here; **agreement is**. A package that states no count
at all is reported as `not stated` - it has nothing this tool can read, and that is not
a pass either. The verdict line carries both numbers, so a `PASS` cannot be read as
"22 packages checked".

**What this tool does not read, and why each gap is named rather than guessed.**

  * **the per-site step label.** `papers/issue-128/reproduce.sh` repeats a label at the
    block it names (`[07]` in the header table at line 21 and at line 162), so a label
    occurs twice in a healthy file and a "labels are unique" test would go red on the
    repair it is meant to protect. The defect R626 found was not a duplicate but a
    **wrong** one - a site labelled `[08]` where its own tier's numbering says `[11]` -
    and pairing a header row to the block that implements it is not mechanically
    determinable from the text. So this tool reads the **extent** of a script's step
    table (its largest label, against the largest count the script states) and leaves
    the per-site label to a hand; that is the half it cannot do, stated here so no
    reader takes a `PASS` for the other half.
  * **a measured count.** `papers/issue-141/README.md:26` records *"Measured 2026-10-20:
    28 steps green"*. That is a dated observation of one run, not a spec of the program,
    and the script reaches 28 through loops no static reader can count without guessing;
    it is printed as `NOT CHECKED` with the date and the number, and it never counts as
    agreement.
  * **whether the run's own count is right.** This is a **static** gate: it compares
    documents to the program's declaration, never a document to a run. A script whose
    header understates what it actually does passes here and fails its reproduction - and
    catching that is the *package's* own collector, at the step that runs it (issue-126
    compares the line it prints against what the README and the manuscript quote;
    issue-139 compares the README's quoted manuscript line, with a planted copy that must
    be refused).
  * **two counts inside one script.** Where a script feeds its success line and its
    failure/NOT RUN lines from **different** variables (issue-126: `$ALL_STEPS` on
    success, `$STEPS` on the failure paths), the report prints a note naming both sites.
    It is a note and not a finding: on the healthy path the two variables hold the same
    value - issue-126's twelve instrument steps plus one figure step plus three checker
    steps plus three singles come to 21, the same 21 its arithmetic declares - and where
    they do diverge, one leg is `NOT RUN` and the run exits 2 printing the count it
    actually took. A gate that went red here would be crying wolf.

Usage:
    python3 .github/tools/stepgate.py --check      # the whole tree, from the repository root
    python3 .github/tools/stepgate.py --root DIR   # read another checkout
    python3 .github/tools/stepgate.py --json       # the same reading as data
    python3 .github/tools/stepgate.py --selftest   # the plant battery

Verdict: `STEPGATE: PASS` (every claim a package states agrees with its script),
`STEPGATE: FAIL` (at least one does not; one `FINDING` line per member), `STEPGATE: NOT
RUN` (no package under `papers/` states a count this tool reads, or the tree has no
packages - an empty set is that gate's `NOT RUN`, never a `PASS`). Exit 0 / 1 / 2.
"""

import json
import os
import re
import shutil
import sys
import tempfile

# a stated count: `(N steps)` - the form every carrier in this tree writes
STEPS = re.compile(r"\((\d+)\s+steps?\b")
# the one computed form: NAME=$(( $(echo $LIST | wc -w ...) + K ))
COMPUTED = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)="
                      r"\$\(\(\s*\$\(\s*echo\s+\$([A-Za-z_][A-Za-z0-9_]*)\s*\|"
                      r"\s*wc\s+-w[^)]*\)\s*\+\s*(\d+)\s*\)\)")
ASSIGN_QUOTED = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=\"([^\"]*)\"")
# a dated measurement of a run: `28 steps green`
MEASURED = re.compile(r"\b(\d+)\s+steps?\s+green\b")
# a step table's labels, in a comment position: `# [07]  ...`
LABEL = re.compile(r"\[(\d{2})\]")
# the variable a verdict line prints as a count: `$STEPS steps`
COUNT_VAR = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\s+steps?\b")
# the tier a line declares for itself, on the script side
TIER_MARK = re.compile(r"#\s*(--full|default)\b")
TIER_FULL = re.compile(r"--full")

COPY_CARRIERS = ("README.md", "manuscript.md")
SCRIPT = "reproduce.sh"
PACKAGE = re.compile(r"^issue-(\d+)$")
LOOKBACK = 10

KNOWN_OPTIONS = ("--check", "--root", "--json", "--selftest")


def _read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().split("\n")
    except OSError:
        return None


def _tier_of(text):
    """The tier a copy's line belongs to, from the invocation it carries."""
    return "full" if TIER_FULL.search(text) else "default"


def _invocation_tier(lines, idx):
    """The tier of a claim, from the `reproduce.sh` invocation it belongs to.

    The same line first (a one-line `bash reproduce.sh --full # -> (13 steps)`), then
    the nearest preceding line naming the script within LOOKBACK lines - a fenced
    block writes the command and the expected last line several lines apart.
    """
    if SCRIPT in lines[idx]:
        return _tier_of(lines[idx])
    low = max(0, idx - LOOKBACK)
    for j in range(idx - 1, low - 1, -1):
        if SCRIPT in lines[j]:
            return _tier_of(lines[j])
    return "unspecified"


def read_script(path):
    """The counts a script states, its step table's extent, and its count sites."""
    lines = _read(path)
    if lines is None:
        return None
    stated = []          # (tier, n, lineno)
    labels = set()
    count_vars = []      # (var, lineno)
    lists = {}
    for i, line in enumerate(lines):
        no = i + 1
        m = ASSIGN_QUOTED.match(line)
        if m:
            lists[m.group(1)] = m.group(2).split()
        m = COMPUTED.match(line)
        if m:
            _name, listvar, k = m.group(1), m.group(2), int(m.group(3))
            words = lists.get(listvar)
            if words is not None:
                stated.append(("unspecified", len(words) + k, no))
        if "REPRODUCE:" in line:
            m = STEPS.search(line)
            if m:
                tier = "unspecified"
                tm = TIER_MARK.search(line)
                if tm:
                    tier = "full" if tm.group(1) == "--full" else "default"
                stated.append((tier, int(m.group(1)), no))
            for vm in COUNT_VAR.finditer(line):
                count_vars.append((vm.group(1), no))
        if line.lstrip().startswith("#"):
            for lm in LABEL.finditer(line):
                labels.add(int(lm.group(1)))
    table_max = max(labels) if len(labels) >= 3 else None
    return {"path": path, "stated": stated, "table_max": table_max,
            "count_vars": count_vars}


def _target(script, tier):
    """The script's count for one tier, or (None, why)."""
    by_tier = {}
    for t, n, _no in script["stated"]:
        by_tier.setdefault(t, set()).add(n)
    if tier in by_tier and len(by_tier[tier]) == 1:
        return list(by_tier[tier])[0], None
    if tier in by_tier:
        return None, "the script states more than one %s count" % tier
    if tier in ("default", "full"):
        every = set()
        for vals in by_tier.values():
            every |= vals
        if len(every) == 1:
            return list(every)[0], None
        if not every:
            return None, "the script states no count this gate reads"
        return None, "the script states no %s count and more than one count overall" % tier
    every = set()
    for vals in by_tier.values():
        every |= vals
    if len(every) == 1:
        return list(every)[0], None
    if not every:
        return None, "the script states no count this gate reads"
    return None, "the claim names no tier and the script states more than one count"


def read_package(root, name):
    pkg = os.path.join(root, "papers", name)
    script = read_script(os.path.join(pkg, SCRIPT))
    rec = {"package": name, "claims": [], "statements": [], "findings": [],
           "notes": [], "unchecked": [], "verdict": "not stated"}
    if script is None:
        rec["unchecked"].append("no %s" % SCRIPT)
        return rec
    if script["count_vars"]:
        seen = {}
        for var, no in script["count_vars"]:
            seen.setdefault(var, no)
        if len(seen) > 1:
            rec["notes"].append(
                "two counts: %s - one program prints two different variables as the "
                "number of steps, and no line compares them (a note, not a finding: "
                "they hold the same value on every path that prints both - "
                "issue-126's instrument loop of 12, one figure step, three checkers "
                "and three singles come to 21, the same 21 its own arithmetic "
                "declares - and where they diverge, one leg is NOT RUN and the run "
                "exits 2 printing the count it took)"
                % "; ".join("$%s at line %d" % (v, no) for v, no in
                            sorted(seen.items(), key=lambda kv: kv[1])))
    for carrier in COPY_CARRIERS:
        lines = _read(os.path.join(pkg, carrier))
        if lines is None:
            continue
        for i, line in enumerate(lines):
            m = MEASURED.search(line)
            if m:
                rec["unchecked"].append(
                    "%s:%d states %s steps - a dated measurement of one run, not a "
                    "specification of the program" % (carrier, i + 1, m.group(1)))
                continue
            m = STEPS.search(line)
            if not m:
                continue
            tier = _invocation_tier(lines, i)
            rec["claims"].append((carrier, i + 1, tier, int(m.group(1))))
    stated = script["stated"]
    if stated:
        rec["statements"] = ["%s:%d (%d, %s)" % (SCRIPT, no, n, t)
                             for t, n, no in stated]
    if rec["claims"]:
        rec["verdict"] = "PASS"
    for carrier, no, tier, n in rec["claims"]:
        want, why = _target(script, tier)
        if want is None:
            rec["unchecked"].append("%s:%d states %d steps (%s) - %s"
                                    % (carrier, no, n, tier, why))
            continue
        if want != n:
            site = None
            for t, sn, sno in stated:
                if t == tier or (tier in ("default", "full") and t == "unspecified"
                                 and sn == want):
                    site = sno
                    break
            if site is None:
                for t, sn, sno in stated:
                    if sn == want:
                        site = sno
                        break
            rec["findings"].append(
                "%s:%d states %d steps (%s); %s:%s states %d"
                % (carrier, no, n, tier, SCRIPT,
                   site if site is not None else "?", want))
    if script["table_max"] is not None and stated:
        largest = max(n for _t, n, _no in stated)
        if script["table_max"] != largest:
            rec["findings"].append(
                "%s's step table reaches [%02d] but its largest stated count is %d"
                % (SCRIPT, script["table_max"], largest))
    if rec["findings"]:
        rec["verdict"] = "FAIL"
    elif not rec["claims"] and rec["unchecked"]:
        # it states something, and this gate could not read it: naming that as
        # `not stated` would say the package is silent when it is not.
        rec["verdict"] = "NOT CHECKED"
    return rec


def read_tree(root):
    papers = os.path.join(root, "papers")
    report = {"root": root, "packages": [], "findings": [], "unchecked": [],
              "notes": [], "stated": 0, "not_stated": 0, "not_checked": 0,
              "agree": 0, "disagree": 0, "verdict": "NOT RUN", "reason": None}
    if not os.path.isdir(papers):
        report["reason"] = "no papers/ directory under %s" % root
        return report
    names = sorted((n for n in os.listdir(papers)
                    if PACKAGE.match(n) and os.path.isdir(os.path.join(papers, n))),
                   key=lambda n: int(PACKAGE.match(n).group(1)))
    if not names:
        report["reason"] = "no papers/issue-<N>/ package directory under %s" % root
        return report
    for name in names:
        rec = read_package(root, name)
        report["packages"].append(rec)
        if rec["verdict"] == "not stated":
            report["not_stated"] += 1
            continue
        report["stated"] += 1
        if rec["verdict"] == "NOT CHECKED":
            report["not_checked"] += 1
        if rec["verdict"] == "FAIL":
            report["disagree"] += len(rec["findings"])
        else:
            report["agree"] += len(rec["claims"])
        for f in rec["findings"]:
            report["findings"].append("%s/%s" % (name, f))
        for u in rec["unchecked"]:
            report["unchecked"].append("%s/%s" % (name, u))
        for nt in rec["notes"]:
            report["notes"].append("%s/%s" % (name, nt))
    if report["findings"]:
        report["verdict"] = "FAIL"
    elif report["agree"] == 0:
        report["verdict"] = "NOT RUN"
        report["reason"] = ("no claim was compared, so this gate took no reading of "
                            "the tree: %d package(s) read, %d state a count it could "
                            "not read, %d state no count at all"
                            % (len(names), report["stated"], report["not_stated"]))
    else:
        report["verdict"] = "PASS"
    return report


def render(report, as_json=False):
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
        return
    print("stepgate_v1 - the step count a package states, read against the count "
          "its script states")
    print("root: %s" % report["root"])
    print("set: %d package(s) under papers/ - an issue-<N> directory is a publication"
          % len(report["packages"]))
    print("instrument: a stated count is a literal `(N steps)` in reproduce.sh / "
          "README.md / manuscript.md, or the computed form "
          "`VAR=$(( $(echo $LIST | wc -w) + K ))`; the script is the authority, the "
          "documents are copies of what it prints")
    print("  stated: %d of %d package(s) state a count (%d compared, %d not checked)"
          % (report["stated"], len(report["packages"]),
             report["stated"] - report["not_checked"], report["not_checked"]))
    silent = []
    for rec in report["packages"]:
        if rec["verdict"] == "not stated":
            silent.append(rec["package"])
            continue
        print("    %-16s %s" % (rec["package"], rec["verdict"]))
        for st in rec["statements"]:
            print("        the script states: %s" % st)
        for c in rec["claims"]:
            print("        claim: %s:%d states %d steps (%s)"
                  % (c[0], c[1], c[3], c[2]))
        for f in rec["findings"]:
            print("        FINDING: %s" % f)
        for u in rec["unchecked"]:
            print("        NOT CHECKED: %s" % u)
        for nt in rec["notes"]:
            print("        note: %s" % nt)
    print("  not stated (%d, named so a reader can see which, and it is not a pass): %s"
          % (len(silent), ", ".join(silent) if silent else "none"))
    if report["unchecked"]:
        print("  not checked: %d claim(s) - named above, each with its reason"
              % len(report["unchecked"]))
    if report["verdict"] == "NOT RUN":
        print("STEPGATE: NOT RUN - %s" % report["reason"])
        return
    print("STEPGATE: %s - %d claim(s) agree; %d disagree; %d not checked; "
          "%d package(s) state no count"
          % (report["verdict"], report["agree"], len(report["findings"]),
             len(report["unchecked"]), report["not_stated"]))


def _plant(root, files):
    for rel, body in files.items():
        path = os.path.join(root, rel)
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)


def _run(root):
    report = read_tree(root)
    import io
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        render(report)
    finally:
        sys.stdout = old
    out = buf.getvalue()
    if report["verdict"] == "PASS":
        return 0, out
    if report["verdict"] == "FAIL":
        return 1, out
    return 2, out


SCRIPT_ONE_TIER = """#!/usr/bin/env bash
# Expected last line:
#
#     REPRODUCE: ALL GREEN (10 steps)
#
set -u
echo "REPRODUCE: ALL GREEN (10 steps)"
"""

SCRIPT_TWO_TIERS = """#!/usr/bin/env bash
# Expected last line, for each tier:
#
#     REPRODUCE: ALL GREEN (10 steps)      # default
#     REPRODUCE: ALL GREEN (13 steps)      # --full
#
# WHAT THE STEPS ARE
#
#   [01]      corpus pins
#   [02]-[06] the certificate suites
#   [07]      check_one_statistic.py
#   [08]      make_figures --selftest-title
#   [09]      canonical.py --check
#   [10]      make_figures --check
#
#   --full adds three byte-identity steps:
#   [11]      the instruments re-run
#   [12]      canonical re-derived
#   [13]      figures + manuscript rebuilt
set -u
"""

SCRIPT_COMPUTED = """#!/usr/bin/env bash
# Expected last line:
#
#     REPRODUCE: ALL GREEN (21 steps, 0 failures)
set -u
INSTRUMENTS="a b c d e f g h i j k l"
STEPS=0
ALL_STEPS=$(( $(echo $INSTRUMENTS | wc -w | tr -d ' ') + 9 ))
LINE="REPRODUCE: ALL GREEN ($ALL_STEPS steps, 0 failures)"
echo "REPRODUCE: $STEPS FAILURE(S) over $STEPS steps"
echo "$LINE"
"""

README_ONE = """# issue 10

```
bash reproduce.sh
```

Expected output (last line):

```
REPRODUCE: ALL GREEN (%s steps)
```
"""

README_TWO = """# issue 10

```
bash reproduce.sh
```

Expected output (last line):

```
REPRODUCE: ALL GREEN (10 steps)
```

A fuller check:

```
bash reproduce.sh --full        # -> REPRODUCE: ALL GREEN (13 steps)
```
"""


def selftest():
    tmp = tempfile.mkdtemp(prefix="stepgate-selftest-")
    cases = []
    ok = 0
    try:
        plant = {
            # a copy that states a stale count: the shape of issue-145 and issue-128's
            # manuscript - the script says 10, the README says 9
            "stale-copy": ({"papers/issue-10/reproduce.sh": SCRIPT_ONE_TIER,
                            "papers/issue-10/README.md": README_ONE % "9"},
                           "FAIL", 1, ["README.md:10", "states 9 steps", "states 10"]),
            # the same package with its copy corrected: green, and the negative control
            # that proves the red above came from the number and not from the plant
            "copy-correct": ({"papers/issue-10/reproduce.sh": SCRIPT_ONE_TIER,
                              "papers/issue-10/README.md": README_ONE % "10"},
                             "PASS", 0, []),
            # the tier half: the --full line is compared with the --full count, so a
            # default count written on the --full line is a finding - issue-128's
            # manuscript:414, whose `--full` line states the default tier's number
            "tier-confused": ({"papers/issue-10/reproduce.sh": SCRIPT_TWO_TIERS,
                               "papers/issue-10/README.md": README_TWO.replace(
                                   "(13 steps)", "(10 steps)")},
                              "FAIL", 1, ["README.md:16", "states 10 steps (full)",
                                          "states 13"]),
            "two-tiers-agree": ({"papers/issue-10/reproduce.sh": SCRIPT_TWO_TIERS,
                                 "papers/issue-10/README.md": README_TWO},
                                "PASS", 0, []),
            # the computed form: 12 words + 9 = 21, and the copy that states it agrees
            "computed-agree": ({"papers/issue-10/reproduce.sh": SCRIPT_COMPUTED,
                                "papers/issue-10/README.md":
                                    "```\nbash reproduce.sh\n```\n\n"
                                    "REPRODUCE: ALL GREEN (21 steps, 0 failures)\n"},
                               "PASS", 0, []),
            "computed-stale": ({"papers/issue-10/reproduce.sh": SCRIPT_COMPUTED,
                                "papers/issue-10/README.md":
                                    "```\nbash reproduce.sh\n```\n\n"
                                    "REPRODUCE: ALL GREEN (20 steps, 0 failures)\n"},
                               "FAIL", 1, ["states 20 steps", "states 21"]),
            # the script's own table reaching further than the count it states
            "table-runs-past-the-count": ({"papers/issue-10/reproduce.sh":
                                           SCRIPT_TWO_TIERS.replace("(13 steps)", "(11 steps)"),
                                           "papers/issue-10/README.md": README_TWO},
                                          "FAIL", 1, ["step table reaches [13]",
                                                      "largest stated count is 11"]),
            # a dated measurement is named and never counted as agreement
            "measured": ({"papers/issue-10/reproduce.sh": SCRIPT_ONE_TIER,
                          "papers/issue-10/README.md": README_ONE % "10" +
                          "\nMeasured 2026-10-20: 28 steps green.\n"},
                         "PASS", 0, ["NOT CHECKED", "28 steps", "not checked: 1"]),
            # a package whose only statement is a measurement of a run: the reading is
            # named, the package is NOT CHECKED, and with no claim compared at all the
            # tree verdict is NOT RUN - the shape issue-141 would have if it were alone
            "measured-only": ({"papers/issue-10/reproduce.sh":
                               "#!/usr/bin/env bash\nset -u\necho REPRODUCE: ALL GREEN\n",
                               "papers/issue-10/README.md":
                               "Measured 2026-10-20: 28 steps green.\n"},
                              "NOT RUN", 2, ["NOT CHECKED", "28 steps",
                                             "no claim was compared"]),
            # a package that states nothing is `not stated`, never a pass - and a tree
            # in which nothing is stated is this gate's NOT RUN, not its PASS
            "silent": ({"papers/issue-10/reproduce.sh":
                        "#!/usr/bin/env bash\nset -u\necho REPRODUCE: ALL GREEN\n"},
                       "NOT RUN", 2, ["NOT RUN", "not stated (1"]),
            # the two-counts note: two variables feed one program's verdict lines, the
            # issue-126 shape - reported, and deliberately not a finding
            "two-counts-noted": ({"papers/issue-10/reproduce.sh": SCRIPT_COMPUTED,
                                  "papers/issue-10/README.md":
                                      "```\nbash reproduce.sh\n```\n\n"
                                      "REPRODUCE: ALL GREEN (21 steps, 0 failures)\n"},
                                 "PASS", 0, ["note: two counts", "$ALL_STEPS",
                                             "$STEPS"]),
        }
        for label, (files, want, want_code, members) in plant.items():
            root = os.path.join(tmp, label)
            _plant(root, files)
            code, out = _run(root)
            m = re.search(r"^STEPGATE: (PASS|FAIL|NOT RUN)", out, re.M)
            verdict = m.group(1) if m else "NO VERDICT LINE"
            good = verdict == want and code == want_code
            missing = [s for s in members if s not in out]
            if missing:
                good = False
            cases.append((label, good, "%s/exit %d (want %s/exit %d)%s"
                          % (verdict, code, want, want_code,
                             "" if not missing else " missing: %s" % ", ".join(missing))))
            ok += 1 if good else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for label, good, detail in cases:
        print("  [%s] %-28s %s" % ("ok" if good else "FAIL", label, detail))
    print("selftest: %d/%d cases ok" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    unknown = [a for a in argv
               if a.startswith("-") and a not in KNOWN_OPTIONS]
    if unknown:
        print("stepgate_v1 - the stated step count read against the script that "
              "states it (tree-wide: it reads every package under papers/)")
        print("NOT RUN: %s is not an option of this gate, so no window was read and "
              "no verdict is taken.\n         This gate takes no path; its options "
              "are %s." % (unknown[0], ", ".join(KNOWN_OPTIONS)))
        print()
        print("usage: stepgate.py --check | --root DIR [--json] | --selftest")
        return 2
    as_json = "--json" in argv
    root = os.getcwd()
    for i, a in enumerate(argv):
        if a == "--root" and i + 1 < len(argv):
            root = os.path.abspath(argv[i + 1])
    if not os.path.isdir(root):
        print("stepgate: %s is not a directory" % root, file=sys.stderr)
        return 2
    report = read_tree(root)
    render(report, as_json)
    if report["verdict"] == "PASS":
        return 0
    if report["verdict"] == "FAIL":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
