#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_step_count.py -- the package's own step-count collector.

ISSUE #128, CORRECTION ROUND 2.

THE CLAIM.  A one-command reproduction ends in a verdict line that carries the number of
steps the run took: `REPRODUCE: ALL GREEN (10 steps)`.  That number is a claim about a
PROGRAM, and this package states it in three carriers:

    reproduce.sh        the header block that tells a reader what the last line will be
    README.md           the expected-output block and the --full command line
    manuscript_source.md  section 10, the command a reader of the PAPER runs

Round 2 was opened because the third carrier had drifted: the manuscript said 7 and 10
while the program took 10 and 13.  It drifted because round 1 grew the program (7/10 ->
10/13) and the prose copy of what the program prints stayed where it was.

WHERE THE TRUTH IS.  Not in the header.  The header is a copy; `reproduce.sh` prints its
verdict from the counter it actually took (`echo "REPRODUCE: ALL GREEN ($STEPS steps)"`).
So this collector derives the pair from the COUNTER'S OWN SEMANTICS -- the step-emitting
constructs the run reaches -- and then reads the header as one more claim to be checked,
not as the standard.  A collector that compared header against manuscript would be a copy
checking a copy, which is the shape that produced the defect.

HOW THE COUNTER IS DERIVED WITHOUT RUNNING (running --full costs ~11 minutes, and running
reproduce.sh from inside a step of reproduce.sh is a recursion).  The script increments
its counter once per construct reached, where a construct is one of

    step "LABEL" ...        step_dep "LABEL" MOD ...        byte "LABEL" FILES ...        notrun "LABEL" WHY

and the alternative arms of one construct -- a `notrun` where a `byte` would go, or the
`STEPS=$((STEPS + 1))` line in a construct's own failure branch -- share that construct's
LABEL.  So the unit is the DISTINCT LABEL per tier, not the number of increment sites:
counting increment sites would double-count every step that has a failure branch.

Two assertions make that derivation safe rather than merely plausible:
  (i) every literal-label `printf '  [%02d] ...'` line (the manual failure arms) must name
      a label some construct already carries -- an unmatched one is an increment no
      construct accounts for, which would make the counter exceed the constructs;
  (ii) the increments inside `step()` / `notrun()` / `byte()` themselves are recognised by
      their VARIABLE label ("$label", "$1") and are the counting mechanism, not steps.

Tiers: fast = every construct before the `if [ "$FULL" = "1" ]; then` line; --full = that
plus every construct after it.

A DATED RECORD IS NOT A CLAIM.  `heilmeier.md` carries the pair at five occurrences, all
inside narrative that names the head it describes ("Gates at this head", "in 11m08s",
"head `21df858`"): those are measurements taken at an earlier head, and 7/10 was true when
they were written.  This collector does not read heilmeier.md at all -- its carriers are
named explicitly -- and `--audit FILE` classifies the occurrences in ANY file as a claim or
a dated record, so the distinction is demonstrated on the real file rather than asserted.
A check that goes red on a dated record is turned off by its first false alarm, and then
the class it was written for goes unread again.

MEASURED LIMIT (recorded, like round 1's 4th-decimal boundary).  The dated-record window is
+/-3 lines, which is what the real file requires: at heilmeier.md:699 the nearest head
marker (`head `21df858``) sits three lines below.  A dated record whose head marker is four
or more lines from its counts would be read as a claim -- a false alarm, not a missed defect.

USAGE
    python3 check_step_count.py                  # check this package
    python3 check_step_count.py --audit FILE     # classify count occurrences in FILE
    python3 check_step_count.py --selftest       # four readings + the dated-record silence
    python3 check_step_count.py --root DIR       # check a copy of the package in DIR

Exit 0 = every carrier states what the counter takes; exit 1 = a disagreement, named.
Standard library only, Python 3.9, no import out of the journal's tooling: an exported
copy of this package can check itself.
"""
import io
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

SCRIPT = "reproduce.sh"
CARRIERS = ("manuscript_source.md", "README.md")   # the prose carriers, named -- never a directory scan

VERDICT = re.compile(r"\((\d+) steps?\)")     # the count literal, wherever a reader meets it
CALL = re.compile(r'^\s*(step|step_dep|byte|notrun)\s+"([^"]+)"')
MANUAL_INC = "STEPS=$((STEPS + 1))"
PRINTF_LITERAL = re.compile(r"""printf '  \[%02d\] %-52s [A-Z ]+\\n' "\$STEPS" "([^"]+)" """)
CMD = re.compile(r"\bbash\s+reproduce\.sh\b(.*)$")
HEAD = re.compile(r"`[0-9a-f]{7,40}`")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
DURATION = re.compile(r"\b\d+m\d+s\b|\b\d+(?:\.\d+)?\s*s\b|\b\d+\s*seconds?\b")
DATED_WINDOW = 3          # see MEASURED LIMIT in the docstring


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


# --------------------------------------------------------------------------- the counter

def parse_script(path):
    """Derive the pair the counter takes, from the constructs the run reaches."""
    lines = read(path).split("\n")
    split = None
    for i, line in enumerate(lines):
        if 'if [ "$FULL" = "1" ]; then' in line:
            split = i
            break
    if split is None:
        raise ValueError("%s: no `if [ \"$FULL\" = \"1\" ]` line -- cannot tell the tiers apart" % path)

    fast, full = {}, {}
    for idx, line in enumerate(lines):
        m = CALL.match(line)
        if m:
            label = m.group(2)
            bucket = full if idx > split else fast
            bucket.setdefault(label, idx + 1)

    # (i) every literal-label failure arm must belong to a construct already counted
    known = set(fast) | set(full)
    orphans = []
    for idx, line in enumerate(lines):
        m = PRINTF_LITERAL.search(line)
        if m and m.group(1) not in known:
            orphans.append((idx + 1, m.group(1)))
    return {"fast": fast, "full": full, "orphans": orphans, "path": path}


def derived(parsed):
    fast_n = len(parsed["fast"])
    full_n = fast_n + len(parsed["full"])
    return fast_n, full_n


# --------------------------------------------------------------------------- the claims

def header_claims(path):
    """reproduce.sh's header block: a count literal whose trailing comment names the tier."""
    out = []
    for n, line in enumerate(read(path).split("\n"), start=1):
        for m in VERDICT.finditer(line):
            if "# --full" in line:
                tier = "full"
            elif "# default" in line:
                tier = "default"
            else:
                tier = None      # a count with no tier is not readable as a claim
            out.append((tier, int(m.group(1)), n))
    return out


def carrier_claims(path):
    """README.md / manuscript_source.md: command lines, and the bare expected-last-line.

    The tier of a bare verdict line is the most recent `bash reproduce.sh[ --full]` above
    it -- which is what a reader does: the verdict belongs to the command they last read.
    """
    out = []
    last_tier = "default"
    for n, line in enumerate(read(path).split("\n"), start=1):
        cmd = CMD.search(line)
        if cmd:
            last_tier = "full" if "--full" in cmd.group(1) else "default"
        for m in VERDICT.finditer(line):
            out.append((last_tier, int(m.group(1)), n))
    return out


def classify(path):
    """Every verdict literal in ANY file, as a claim or a dated record (see --audit)."""
    lines = read(path).split("\n")
    out = []
    for n, line in enumerate(lines, start=1):
        hits = list(VERDICT.finditer(line))
        if not hits:
            continue
        lo = max(0, n - 1 - DATED_WINDOW)
        hi = min(len(lines), n + DATED_WINDOW)
        window = "\n".join(lines[lo:hi])
        why = None
        if HEAD.search(window):
            why = "a head marker within +/-%d lines" % DATED_WINDOW
        elif DATE.search(window):
            why = "a date within +/-%d lines" % DATED_WINDOW
        elif DURATION.search(window):
            why = "a measured duration within +/-%d lines" % DATED_WINDOW
        for m in hits:
            out.append((n, int(m.group(1)), "dated record" if why else "claim", why))
    return out


# --------------------------------------------------------------------------- the check

def check(root):
    """Return (ok, lines). Compares every carrier against the derived pair."""
    rep = []
    script = os.path.join(root, SCRIPT)
    parsed = parse_script(script)
    fast_n, full_n = derived(parsed)
    truth = {"default": fast_n, "full": full_n}
    rep.append("counter: %s -> default %d steps, --full %d steps"
               % (SCRIPT, fast_n, full_n))
    rep.append("         (derived from %d distinct step labels before the tier split, %d after)"
               % (len(parsed["fast"]), len(parsed["full"])))
    ok = True

    if parsed["orphans"]:
        ok = False
        for ln, label in parsed["orphans"]:
            rep.append("FAIL    %s:%d  an increment whose label no construct carries: %r"
                       % (SCRIPT, ln, label))

    header = header_claims(script)
    if not header:
        ok = False
        rep.append("FAIL    %s  no declared pair in the header -- the reader is told nothing" % SCRIPT)
    for tier, n, ln in header:
        if tier is None:
            ok = False
            rep.append("FAIL    %s:%d  states %d steps with no tier ('# default' / '# --full')"
                       % (SCRIPT, ln, n))
            continue
        if n != truth[tier]:
            ok = False
            rep.append("FAIL    %s:%d  HEADER says %d, COUNTER takes %d (%s tier) -- a copy, not the standard"
                       % (SCRIPT, ln, n, truth[tier], tier))
        else:
            rep.append("ok      %s:%d  header %d (%s) = counter" % (SCRIPT, ln, n, tier))

    for name in CARRIERS:
        path = os.path.join(root, name)
        if not os.path.exists(path):
            ok = False
            rep.append("FAIL    %s  carrier missing" % name)
            continue
        claims = carrier_claims(path)
        seen = set()
        for tier, n, ln in claims:
            seen.add(tier)
            if n != truth[tier]:
                ok = False
                rep.append("FAIL    %s:%d  states %d steps (%s), counter takes %d"
                           % (name, ln, n, tier, truth[tier]))
            else:
                rep.append("ok      %s:%d  %d (%s) = counter" % (name, ln, n, tier))
        for tier in ("default", "full"):
            if tier not in seen:
                ok = False
                rep.append("FAIL    %s  states no count for the %s tier" % (name, tier))
    rep.append("")
    rep.append("STEP-COUNT: %s -- %d claim(s) checked against a counter of %d/%d"
               % ("ALL AGREE" if ok else "DISAGREE", sum(1 for r in rep if r.startswith(("ok ", "FAIL"))),
                  fast_n, full_n))
    return ok, rep


# --------------------------------------------------------------------------- the selftest

def _copy_package(dest):
    for name in (SCRIPT, "manuscript_source.md", "README.md"):
        shutil.copy(os.path.join(HERE, name), os.path.join(dest, name))
    return dest


def _run_quiet(root):
    try:
        ok, rep = check(root)
    except ValueError as exc:
        return False, ["FAIL    %s" % exc]
    return ok, rep


def selftest():
    """Four readings. Two must be red, one must stay green, one must stay silent."""
    ok = True
    print("== the four readings =====================================================")

    # 1. control: the package as committed must be GREEN
    ctrl = tempfile.mkdtemp(prefix="stepcount-control-")
    _copy_package(ctrl)
    good, rep = _run_quiet(ctrl)
    print("[1] CONTROL  right count        -> %s" % ("GREEN" if good else "FALSELY RED"))
    if not good:
        ok = False
        for line in rep[-6:]:
            print("        " + line)

    # 2. plant: a wrong count in the manuscript must go RED
    p2 = tempfile.mkdtemp(prefix="stepcount-plant-ms-")
    _copy_package(p2)
    ms = os.path.join(p2, "manuscript_source.md")
    text = read(ms)
    fast_n, _ = derived(parse_script(os.path.join(p2, SCRIPT)))
    doctored = text.replace("(%d steps)" % fast_n, "(7 steps)", 1)
    assert doctored != text, "the manuscript plant did not apply"
    with io.open(ms, "w", encoding="utf-8") as fh:
        fh.write(doctored)
    red, rep = _run_quiet(p2)
    print("[2] PLANT    manuscript wrong  -> %s" % ("RED" if not red else "NOT CAUGHT"))
    if red:
        ok = False
    else:
        print("        " + [r for r in rep if r.startswith("FAIL")][0])

    # 3. the discriminating plant: HEADER and MANUSCRIPT agree on a stale pair while the
    #    counter takes something else.  A collector that compares the manuscript against the
    #    header goes GREEN here -- that collector is a copy checking a copy, which is exactly
    #    the round-1 shape.  Binding to the counter makes it RED.
    p3 = tempfile.mkdtemp(prefix="stepcount-plant-pair-")
    _copy_package(p3)
    sc = os.path.join(p3, SCRIPT)
    ms = os.path.join(p3, "manuscript_source.md")
    stale = fast_n - 1
    s_text = read(sc).replace("(%d steps)      # default" % fast_n,
                              "(%d steps)      # default" % stale, 1)
    m_text = read(ms).replace("(%d steps)" % fast_n, "(%d steps)" % stale, 1)
    with io.open(sc, "w", encoding="utf-8") as fh:
        fh.write(s_text)
    with io.open(ms, "w", encoding="utf-8") as fh:
        fh.write(m_text)
    red, rep = _run_quiet(p3)
    caught = [r for r in rep if r.startswith("FAIL") and "HEADER" in r]
    print("[3] PLANT    header=manuscript, both stale -> %s"
          % ("RED (header vs counter)" if not red and caught else "NOT CAUGHT"))
    if red or not caught:
        ok = False
    else:
        print("        " + caught[0])

    # 4. the dated record stays SILENT: not a claim, so not a failure
    h = os.path.join(HERE, "heilmeier.md")
    if os.path.exists(h):
        rows = classify(h)
        claims = [r for r in rows if r[2] == "claim"]
        dated = [r for r in rows if r[2] == "dated record"]
        silent = len(claims) == 0
        print("[4] SILENCE  heilmeier.md      -> %d occurrence(s): %d dated record(s), %d claim(s) -- %s"
              % (len(rows), len(dated), len(claims), "SILENT" if silent else "FALSE ALARM"))
        for n, val, kind, why in rows:
            print("        :%d  %d steps  %s%s" % (n, val, kind, (" (%s)" % why) if why else ""))
        if not silent:
            ok = False
    else:
        print("[4] SILENCE  heilmeier.md absent -- not applicable in this copy")

    # 5. the classifier must not be silent about everything: a bare, undated count is a claim
    p5 = tempfile.mkdtemp(prefix="stepcount-undated-")
    undated = os.path.join(p5, "undated.md")
    with io.open(undated, "w", encoding="utf-8") as fh:
        fh.write("The run ends `REPRODUCE: ALL GREEN (7 steps)` on this build.\n")
    rows = classify(undated)
    caught = len(rows) == 1 and rows[0][2] == "claim"
    print("[5] CONTROL  undated count      -> %s" % ("read as a claim" if caught else "NOT READ"))
    if not caught:
        ok = False

    print()
    print("SELFTEST: %s" % ("ALL ASSERTIONS HOLD" if ok else "FAILED"))
    return ok


# --------------------------------------------------------------------------- main

def main(argv):
    if "--selftest" in argv:
        return 0 if selftest() else 1
    if "--audit" in argv:
        path = argv[argv.index("--audit") + 1]
        rows = classify(path)
        for n, val, kind, why in rows:
            print("%s:%d  %d steps  %s%s" % (path, n, val, kind, (" (%s)" % why) if why else ""))
        print("AUDIT: %d occurrence(s), %d claim(s), %d dated record(s)"
              % (len(rows), sum(1 for r in rows if r[2] == "claim"),
                 sum(1 for r in rows if r[2] == "dated record")))
        return 0
    root = HERE
    if "--root" in argv:
        root = argv[argv.index("--root") + 1]
    ok, rep = check(root)
    for line in rep:
        print(line)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
