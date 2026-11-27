#!/usr/bin/env python3
"""The step count this package states, read against the count its script runs.

Why this exists. `reproduce.sh` printed six steps while `README.md`'s expected-output block printed
five and the script's own header said "three" -- three carriers, three numbers, none of them read by
any program. A count quoted in a document and a count computed by a program drift apart; the quoted
one is a copy, and a copy's default behaviour is to drift. This gate makes the copy decidable.

Three carriers are read, and the third one matters as much as the first two:

  1. `README.md`'s `STEPS RUN: N` line;
  2. `README.md`'s `REPRODUCE: ... (N steps)` line;
  3. the script's own header. A shell comment cannot be derived from the run, so the rule is not
     "the header's number must agree" -- it is "the header states no count at all". The header said
     "one command, three steps", a SPELLED numeral, which is the carrier a gate reading only digits
     is blind to (a lesson this package's own history already paid for).

The counted side is the script's `step "..."` call sites, read from the file, so adding a step and
forgetting the documents fails here rather than silently.

Usage:
  ./check_step_count.py                    # the package's own files
  ./check_step_count.py --readme R --script S   # read other copies (used by the selftest)
  ./check_step_count.py --selftest         # both directions, on fixtures

Exit codes: 0 the stated counts agree with the counted one; 1 a stated count disagrees, or the
header states one; 3 NOT RUN -- the README states no count, so there is nothing to compare and no
verdict is taken.
"""
import argparse
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

CALL = re.compile(r'^step\s+"', re.M)
STEPS_RUN = re.compile(r'^STEPS RUN:\s*(\d+)', re.M)
ALL_GREEN = re.compile(r'^REPRODUCE:.*\((\d+)\s+steps?\)', re.M)
HEADER = re.compile(r'^#.*$', re.M)
WORDS = ("one two three four five six seven eight nine ten eleven twelve "
         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty").split()
SPELLED = re.compile(r'\b(%s)[\s-]+steps?\b' % "|".join(WORDS), re.I)


def counted(script_text):
    """The number of `step "..."` call sites: the count the run actually executes."""
    return len(CALL.findall(script_text))


def header_block(script_text):
    """The script's LEADING comment block, and nothing else.

    Scope matters: a comment further down may describe a past failure ("the three steps reported
    NOT RUN for every reader") without making any claim about this script's count. Reading every
    `#` line would fire on that history and the gate would be crying wolf on correct code -- a
    false positive is as expensive as a miss, because it teaches the reader to ignore the line.
    So the header is the contiguous run of comments and blank lines before the first executable
    line, which is exactly the region a reader takes as the file's own description of itself.
    """
    out = []
    for line in script_text.split("\n"):
        if line.startswith("#") or not line.strip():
            out.append(line)
        else:
            break
    return "\n".join(out)


def header_claim(script_text):
    """A count stated in the script's leading comment block, in digits or in words."""
    head = header_block(script_text)
    bad = []
    m = SPELLED.search(head)
    if m:
        bad.append("the header states the count in words (%r)" % m.group(0))
    m = re.search(r'\b(\d+)\s+steps?\b', head, re.I)
    if m:
        bad.append("the header states the count in digits (%r)" % m.group(0))
    return bad


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def check(readme_path, script_path):
    """Return (verdict, findings, counted_n, stated) where verdict is PASS/FAIL/NOT RUN."""
    readme = read(readme_path)
    script = read(script_path)
    n = counted(script)

    stated = []
    for label, rx in (("STEPS RUN", STEPS_RUN), ("REPRODUCE", ALL_GREEN)):
        for m in rx.finditer(readme):
            stated.append((label, int(m.group(1))))

    findings = []
    for label, value in stated:
        if value != n:
            findings.append("%s states %d step(s); the script runs %d" % (label, value, n))
    findings.extend(header_claim(script))

    if not stated and not findings:
        return "NOT RUN", ["README.md states no step count, so there is nothing to compare"], n, stated
    return ("FAIL" if findings else "PASS"), findings, n, stated


def selftest():
    """Both directions on fixtures: the clean pair passes, each doctored one fails."""
    script = (b'#!/bin/sh\n'
              b'# reproduce.sh -- one command, a verdict per step.\n'
              b'step "a" ./a\n'
              b'step "b" ./b\n')
    readme_clean = b'STEPS RUN: 2   NOT RUN: 0\nREPRODUCE: ALL GREEN (2 steps)\n'
    readme_wrong = b'STEPS RUN: 5   NOT RUN: 0\nREPRODUCE: ALL GREEN (5 steps)\n'
    readme_none = b'no count stated here\n'
    script_words = script.replace(b'a verdict per step', b'one command, three steps, a verdict each')

    cases = [
        ("clean pair passes", script, readme_clean, "PASS"),
        ("a doctored README count fails", script, readme_wrong, "FAIL"),
        ("a count only in words in the header fails", script_words, readme_clean, "FAIL"),
        # The header branch refuses a count in the header even when the count is CORRECT: a comment
        # cannot be derived from the run, so it must not compete with the run. This case states 2,
        # which is the true number, and must still fail -- a fixture with a wrong number would be
        # caught by the README comparison instead and would prove nothing about this branch.
        ("a correct count in digits in the header still fails",
         script.replace(b'a verdict per step', b'2 steps, a verdict each'),
         readme_clean, "FAIL"),
        ("no stated count is NOT RUN, not a pass", script, readme_none, "NOT RUN"),
        # Scope: this comment is BELOW the first executable line and describes a past failure. It
        # states a count of something that is not this script's steps, and must not fire.
        ("a later comment describing history does not fire",
         script.replace(b'step "b" ./b\n',
                        b'step "b" ./b\n# the three steps reported NOT RUN for every reader\n'),
         readme_clean, "PASS"),
    ]
    ok = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, s, r, want in cases:
            sp = os.path.join(tmp, "reproduce.sh")
            rp = os.path.join(tmp, "README.md")
            open(sp, "wb").write(s)
            open(rp, "wb").write(r)
            got, findings, n, stated = check(rp, sp)
            good = got == want
            ok += good
            print("  %s %-44s want %-7s got %-7s (counted %d, stated %s)"
                  % ("ok  " if good else "FAIL", name, want, got, n, stated or "-"))
            for f in findings:
                print("       %s" % f)
    print("\nSELFTEST: %d/%d cases ok" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--readme", default=os.path.join(HERE, "README.md"))
    ap.add_argument("--script", default=os.path.join(HERE, "reproduce.sh"))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    verdict, findings, n, stated = check(args.readme, args.script)
    print("check_step_count -- the stated step count against the steps the script runs")
    print("  script: %s" % os.path.basename(args.script))
    print("  counted: %d call site(s)" % n)
    for label, value in stated:
        print("  stated (%s): %d" % (label, value))
    if not stated:
        print("  stated: none")
    print()
    for f in findings:
        print("  FINDING %s" % f)
    print("STEPCOUNT: %s" % verdict)
    if verdict == "PASS":
        return 0
    if verdict == "NOT RUN":
        return 3
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
