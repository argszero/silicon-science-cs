#!/usr/bin/env python3
"""The README's quoted expected output, checked against a real run of the one command.

`README.md` shows the tail of `bash reproduce.sh` as the output a reader should compare their own run
against. That block is a reading like any other in this package: it is evidence about what the command
prints, so nothing re-derived it -- and it had drifted, twice, in exactly the way an unowned quote does.

**THE BLOCK IS THE NAMED BUILD'S TAIL, SO THIS CHECK NAMES THE BUILD IT READ.** `build.json` records the
pair the committed artefacts were re-derived under; the quoted block opens with that pair's own lines and
ends with that build's verdict. Seven of its literal lines are **facts about the coordinate the block was
taken on**, not about the command's behaviour:

    taken on: build Python …        (the evidence-log coordinate line)
    build: this run Python …        (the run's own build, printed by step 0 and step 2)
    <n> declared line(s) …          (the log comparison's declared-line tally)
    REPRODUCE: …                    (this build's verdict: ALL GREEN, or COORDINATE MISMATCH)

**Only the build-independent lines are compared, and this check says which those are.** The seven are
DECLARED: their *values* are not compared -- a comparison of them would be reading this machine's
arithmetic and reporting it as a property of the document, which is the defect class this round removed
one file over. What IS checked about them is a claim about the **package**, and the package owns its
object: each one must name the pair `build.json` records, the block must quote as many `taken on:` lines as
declared-line counts (one log has one of each), and the block's verdict must be the green one the named
build warrants. So the verdict is the same string on every machine, and the declared lines are still read
-- against the record, not against the machine.

**THE RUN IS ITSELF CONTROLLED.** A command that did not start, or whose output never reached the block's
own head line (`== 0. build coordinate ==`), is a defect of the **reading** -- never a drifted document.
That case has its own verdict and its own exit code, and it names what the transcript did contain. Without
it, a command that printed three lines of preflight and a command that printed a different result were the
same verdict: `N lines the README quotes and the run did not print`.

Run:
    python3 readme_expected_output.py            # runs bash reproduce.sh and compares
    python3 readme_expected_output.py --log L    # compares against a saved transcript
    python3 readme_expected_output.py --selftest # builds its own transcript; plants each defect

Exit: 0 the compared lines were printed and the declared lines name the record; 1 a finding about the
document; 2 the reading could not be taken (the run never reached the block).

It is deliberately NOT a step of `reproduce.sh`: it runs `reproduce.sh`, and a spec that runs its own spec
recurses.
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

import evidence_log as EL

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "README.md")
BLOCK_HEAD = "== 0. build coordinate =="
MIN_QUOTED = 20             # a block quoting fewer lines than this is not the block (see --selftest)
VERDICTS = ("REPRODUCE: ALL GREEN", "REPRODUCE: COORDINATE MISMATCH", "REPRODUCE: FAILED")

# The four forms a quoted line takes when it states the coordinate the block was taken on. Presence is
# required; the VALUE is declared -- not compared against this machine, but checked against build.json.
COORDINATE_FORMS = (
    ("taken on:", re.compile(r"^taken on:")),
    ("build: this run", re.compile(r"^build: this run ")),
    ("declared line(s)", re.compile(r"^\d+ declared line\(s\)")),
    ("REPRODUCE:", re.compile(r"^REPRODUCE: ")),
)
DECLARED_COUNT_RE = re.compile(r"^\d+ declared line\(s\)")


def is_coordinate(line):
    """Is this quoted line a fact about the coordinate (the build, the tree) rather than about the
    command's behaviour? Measured over two builds: exactly the lines this predicate names are the ones
    that differ between them, and no build-independent line is named (`--selftest` plants each form)."""
    return any(rx.match(line.strip()) for _, rx in COORDINATE_FORMS)


def quoted_lines(readme):
    """The literal lines the README's `Expected output (tail)` block quotes. An elision (`...`) is the
    README's own shorthand and a `<...>` is its placeholder; both are skipped. Everything else is a claim
    about what the command printed."""
    md = io.open(readme, encoding="utf-8").read().split("\n")
    starts = [i for i, l in enumerate(md) if l.strip().startswith("Expected output (tail)")]
    if len(starts) != 1:
        raise SystemExit("expected exactly one 'Expected output (tail):' block, found %d" % len(starts))
    start = starts[0]
    stop = next((i for i in range(start + 1, len(md))
                 if md[i].startswith("**") or md[i].startswith("###") or md[i].startswith("## ")), len(md))
    out = []
    for l in md[start + 1:stop]:
        if not l.startswith("    ") or not l.strip():
            continue
        t = l.strip()
        if "..." in t or "<" in t:
            continue
        out.append(t)
    return out


def run_command():
    """(transcript, exit code) of the one command, run here. The exit code is read, and printed: 0, 4
    (coordinate) and 1 (failure) are all legitimate runs, but a run that never reached the block is not a
    run that can witness anything."""
    p = subprocess.run(["bash", "reproduce.sh"], cwd=HERE, capture_output=True, text=True,
                       env=dict(os.environ))
    return p.stdout + p.stderr, p.returncode


def coordinate_statement():
    """One sentence, in the check's own words, naming the build this reading was taken on and the build
    the block belongs to -- both read from `build.json` and this interpreter, through the same owner the
    evidence logs use (`evidence_log.py`), never typed."""
    here = EL.measured_build()
    named = EL.named_build(HERE)
    if named is None:
        return ("build: this run Python %s / numpy %s   |   no build.json in this package: the block's own"
                " coordinate cannot be named" % (here["python"], here["numpy"]), None)
    same = here["python"] == named["python"] and here["numpy"] == named["numpy"]
    return ("build: this run Python %s / numpy %s   |   the README's block is the tail of the NAMED build"
            " Python %s / numpy %s (%s)"
            % (here["python"], here["numpy"], named["python"], named["numpy"],
               "this run is that build" if same else "this run is NOT that build"), named)


def record_problems(declared, named):
    """The declared lines are not compared for value -- but they are claims about the package, and the
    package owns their object: `build.json`. Each check here is machine-independent."""
    probs = []
    if named is None:
        return ["the package carries no build.json, so the block's declared coordinate has no owner"]
    pair = (named["python"], named["numpy"])
    for l in declared:
        t = l.strip()
        if t.startswith(("taken on:", "build: this run")):
            if not all(v in t for v in pair):
                probs.append("this declared line does not name the pair build.json records (%s / %s): %s"
                             % (pair[0], pair[1], t[:110]))
    n_on = sum(1 for l in declared if l.strip().startswith("taken on:"))
    n_cnt = sum(1 for l in declared if DECLARED_COUNT_RE.match(l.strip()))
    if n_on != n_cnt:
        probs.append("the block quotes %d `taken on:` line(s) but %d declared-line count(s): each log has"
                     " one of each" % (n_on, n_cnt))
    verdicts = [l.strip() for l in declared if l.strip().startswith("REPRODUCE:")]
    if not verdicts:
        probs.append("the block quotes no verdict line")
    for v in verdicts:
        if not any(v.startswith(k) for k in VERDICTS):
            probs.append("this line is none of the three verdicts the command prints: %s" % v[:110])
        elif not v.startswith("REPRODUCE: ALL GREEN"):
            probs.append("the block is the named build's tail and build.json records that the committed"
                         " artefacts were re-derived under it, so that build's verdict is the green one:"
                         " %s" % v[:110])
    return probs


def classify(readme, transcript):
    """(quoted, declared, compared, missing, absent_forms) for the README's block against a transcript."""
    q = quoted_lines(readme)
    printed = set(l.strip() for l in transcript.split("\n"))
    declared = [x for x in q if is_coordinate(x)]
    compared = [x for x in q if not is_coordinate(x)]
    missing = [x for x in compared if x not in printed]
    absent = [name for name, rx in COORDINATE_FORMS if not any(rx.match(x) for x in q)]
    return q, declared, compared, missing, absent


def check(a):
    """The reading. Returns an exit code: 0 match, 1 a finding about the document, 2 the reading could
    not be taken."""
    if a.log:
        transcript = io.open(a.log, encoding="utf-8").read()
        rc = None
        print("transcript: %s (%d line(s)); no exit code to read -- it was supplied, not run"
              % (a.log, len(transcript.split("\n"))))
    else:
        transcript, rc = run_command()
        print("transcript: %d line(s) from a real `bash reproduce.sh` (exit %s)"
              % (len(transcript.split("\n")), rc))

    sentence, named = coordinate_statement()
    print(sentence)

    # ---- the run is controlled before the document is judged: an absent block is a defect of the READING
    if BLOCK_HEAD not in transcript:
        last = [l.strip() for l in transcript.split("\n") if l.strip()]
        how = ("the transcript was supplied, not run" if rc is None else "the command exited %s" % rc)
        print("")
        print("README EXPECTED OUTPUT: THE READING COULD NOT BE TAKEN -- the transcript never reached the"
              " block (%s)" % BLOCK_HEAD)
        print("   !! %s and its output does not contain the block's own head line `%s`, so nothing was read"
              ": this is a defect of the READING, not of the README" % (how, BLOCK_HEAD))
        print("   !! what the transcript did contain (last non-empty line): %s"
              % (last[-1][:140] if last else "(nothing)"))
        print("   !! re-run it with an interpreter that carries numpy (see reproduce.sh's preflight), or"
              " pass --log with a transcript from a command that reached the block")
        return 2

    q, declared, compared, missing, absent = classify(a.readme, transcript)
    probs = record_problems(declared, named)
    if absent:
        probs.append("the block no longer quotes %d form(s) that state its coordinate: %s"
                     % (len(absent), ", ".join(absent)))
    if len(q) < MIN_QUOTED:
        probs.append("the block quotes only %d line(s): the extraction found no block to read" % len(q))

    print("README expected output: %d literal line(s) quoted -- %d compared on this build, %d DECLARED"
          " (they state the coordinate the block was taken on)" % (len(q), len(compared), len(declared)))
    for d in declared:
        print("   declared (value not compared here): %s" % d[:120])
    print("   of the compared %d line(s), %d the run did not print" % (len(compared), len(missing)))
    for m in missing:
        print("   !! the README quotes this line and the run did not print it: %s" % m[:150])
    for p in probs:
        print("   !! %s" % p[:170])

    print("")
    if declared:
        print("NOT TAKEN: the %d declared line(s) above were not compared against this machine's run --"
              " they state the named build's coordinate, and comparing them here would read this machine's"
              " arithmetic and report it as a property of the document; they are instead checked against"
              " build.json, which owns what they claim, and required to be quoted as forms" % len(declared))
    else:
        print("NOT TAKEN: none -- the block quotes no coordinate line, which is itself reported above")
    if probs:
        print("README EXPECTED OUTPUT: DOES NOT MATCH")
        return 1
    if missing:
        print("README EXPECTED OUTPUT: DOES NOT MATCH")
        return 1
    print("README EXPECTED OUTPUT: MATCHES THE RUN on the %d line(s) that do not depend on the build, and"
          " the %d declared line(s) name the record" % (len(compared), len(declared)))
    return 0


def selftest():
    """The control that proves the check can fail -- derived from the README itself, so it runs on any
    machine (it needs no transcript from a real run: the coupling the round-3 re-check named). Each arm
    plants one defect and requires exactly that defect to be reported."""
    md = io.open(README, encoding="utf-8").read()
    q = quoted_lines(README)
    good = "\n".join([BLOCK_HEAD] + q) + "\n"      # what a named build prints if the block is true
    bad = 0
    tmp = tempfile.mkdtemp()
    try:
        def arm(tag, readme_text, transcript, want, want_in=()):
            nonlocal bad
            rp = os.path.join(tmp, "r.md")
            tp = os.path.join(tmp, "t.log")
            io.open(rp, "w", encoding="utf-8", newline="\n").write(readme_text)
            io.open(tp, "w", encoding="utf-8", newline="\n").write(transcript)
            p = subprocess.run([sys.executable, os.path.abspath(__file__), "--log", tp, "--readme", rp],
                               capture_output=True, text=True)
            out = p.stdout + p.stderr
            hit = all(s in out for s in want_in)
            ok = (p.returncode == want) and hit
            print("   %-27s exit=%d want=%d %s%s" % (tag, p.returncode, want, "ok" if ok else "BAD",
                                                     "" if hit else " (missing sentence)"))
            if not ok:
                for l in p.stdout.split("\n")[-7:]:
                    print("      | %s" % l[:130])
            bad += 0 if ok else 1

        arm("clean", md, good, 0, ("MATCHES THE RUN",))
        arm("wrong value", md.replace("VALIDATE 54/54", "VALIDATE 53/54", 1), good, 1,
            ("VALIDATE 53/54", "DOES NOT MATCH"))
        arm("absent compared line", md, good.replace("TRACE: OK\n", "", 1), 1, ("TRACE: OK",))
        for name, rx in COORDINATE_FORMS:
            plant = next((l for l in q if rx.match(l)), None)
            if plant is None:
                print("   %-27s BAD (the block quotes no `%s` line to plant)" % ("coordinate form", name))
                bad += 1
                continue
            arm("declared: %s" % name, md, good.replace(plant + "\n", "", 1), 0, ("MATCHES THE RUN",))
        # a declared line whose VALUE contradicts the record it names -- caught without any machine
        on_line = next(l for l in q if l.startswith("taken on:"))
        arm("declared names wrong pair",
            md.replace(on_line, "taken on: build Python 8.8.8 / numpy 8.8.8 (a pair no record names)", 1),
            good, 1, ("does not name the pair",))
        arm("declared verdict not green",
            md.replace("REPRODUCE: ALL GREEN", "REPRODUCE: FAILED", 1), good, 1, ("verdict is the green one",))
        arm("form removed from block", md.replace("REPRODUCE: ALL GREEN\n", "", 1), good, 1,
            ("no longer quotes",))
        arm("run never started", md, "FATAL: no interpreter with numpy found.\n", 2,
            ("THE READING COULD NOT BE TAKEN", "defect of the READING"))
        arm("block gone", md.replace("Expected output (tail)", "The output of the command", 1),
            good, 1, ("expected exactly one",))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("SELFTEST: %s" % ("ALL PASS" if not bad else "FAILED (%d)" % bad))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=None, help="compare against this saved transcript instead of running")
    ap.add_argument("--readme", default=README, help="the README to read the block from")
    ap.add_argument("--selftest", action="store_true",
                    help="build a transcript from the README and require each planted defect to be named")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    return check(a)


if __name__ == "__main__":
    sys.exit(main())
