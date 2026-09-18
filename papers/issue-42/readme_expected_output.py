#!/usr/bin/env python3
"""The README's quoted expected output, checked against a real run of the one command.

`README.md` shows the tail of `bash reproduce.sh` as the output a reader should compare their own run
against. That block is a reading like any other in this package: it is evidence about what the command
prints, so nothing re-derived it -- and it had drifted, twice, in exactly the way an unowned quote does.
It quoted a verdict form no run printed, and declared-line counts that no run produced.

This checker derives the reading rather than trusting it: it runs the one command (or reads a saved
transcript with `--log`) and requires every line the README quotes LITERALLY to be a line the command
actually printed. Lines containing `...` are the README's own elisions and are skipped; the extraction
refuses to pass on an empty or trivial set, so a block that stopped being parsed cannot look like a
block that matches.

It is deliberately NOT a step of `reproduce.sh`: it runs `reproduce.sh` itself, and a spec that runs its
own spec recurses. Run it directly:

    python3 readme_expected_output.py            # runs bash reproduce.sh and compares
    python3 readme_expected_output.py --log L    # compares against a saved transcript
    python3 readme_expected_output.py --selftest # plants a wrong quote in a copy of the README
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "README.md")
MIN_QUOTED = 20             # a block that quotes fewer lines than this is not the block (see --selftest)


def quoted_lines(readme):
    """The literal lines the README's `Expected output (tail)` block quotes. An elision (`...`) is the
    README's own shorthand and is skipped; everything else must have been printed by a real run."""
    md = io.open(readme, encoding="utf-8").read().split("\n")
    starts = [i for i, l in enumerate(md) if l.strip() == "Expected output (tail):"]
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
        if "..." in t or "<" in t:            # the README's elisions and placeholders
            continue
        out.append(t)
    return out


def run_command():
    env = dict(os.environ)
    p = subprocess.run(["bash", "reproduce.sh"], cwd=HERE, capture_output=True, text=True, env=env)
    return p.stdout + p.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=None, help="compare against this saved transcript instead of running")
    ap.add_argument("--readme", default=README, help="the README to read the block from")
    ap.add_argument("--selftest", action="store_true", help="plant a wrong quote and require it to be named")
    a = ap.parse_args()

    if a.selftest:
        if not a.log:
            raise SystemExit("--selftest needs --log (the transcript a real run produced)")
        log = io.open(a.log, encoding="utf-8").read()
        bad = 0
        tmp = tempfile.mkdtemp()
        try:
            clean = os.path.join(tmp, "clean.md")
            shutil.copyfile(README, clean)
            n, miss = compare(clean, log)
            print("arm clean        : %d quoted, %d missing -> %s" % (n, len(miss), "ok" if not miss else "BAD"))
            bad += 1 if miss else 0

            planted = os.path.join(tmp, "planted.md")
            t = io.open(clean, encoding="utf-8").read()
            assert "VALIDATE 54/54" in t, "plant anchor: VALIDATE 54/54"
            io.open(planted, "w", encoding="utf-8", newline="\n").write(
                t.replace("VALIDATE 54/54", "VALIDATE 53/54", 1))
            n2, miss2 = compare(planted, log)
            hit = [m for m in miss2 if "VALIDATE 53/54" in m]
            print("arm wrong-quote  : %d quoted, %d missing, names the planted line: %s"
                  % (n2, len(miss2), bool(hit)))
            bad += 0 if hit else 1

            empty = os.path.join(tmp, "empty.md")
            io.open(empty, "w", encoding="utf-8", newline="\n").write(
                "Expected output (tail):\n\n**a block that quotes nothing**\n")
            n3, miss3 = compare(empty, log)
            print("arm block-gone   : %d quoted (floor %d) -> %s"
                  % (n3, MIN_QUOTED, "ok" if n3 < MIN_QUOTED else "BAD"))
            bad += 0 if n3 < MIN_QUOTED else 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print("SELFTEST: %s" % ("ALL PASS" if not bad else "FAILED (%d)" % bad))
        return 1 if bad else 0

    log = io.open(a.log, encoding="utf-8").read() if a.log else run_command()
    if not a.log:
        print("transcript: %d line(s) from a real `bash reproduce.sh`" % len(log.split("\n")))
    n, miss = compare(a.readme, log)
    print("README expected output vs the run: %d literal line(s) quoted, %d not printed" % (n, len(miss)))
    for m in miss:
        print("   !! the README quotes this line and the run did not print it: %s" % m[:150])
    if n < MIN_QUOTED:
        print("   !! the block quotes only %d line(s): the extraction found no block to read" % n)
        return 1
    print("README EXPECTED OUTPUT: %s" % ("MATCHES THE RUN" if not miss else "DOES NOT MATCH"))
    return 1 if miss else 0


def compare(readme, log):
    q = quoted_lines(readme)
    printed = set(l.strip() for l in log.split("\n"))
    return len(q), [x for x in q if x not in printed]


if __name__ == "__main__":
    sys.exit(main())
