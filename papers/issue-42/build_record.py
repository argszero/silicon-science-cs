#!/usr/bin/env python3
"""The BUILD coordinate for issue #42 -- the environment's second debt (correction round 2).

The reproduction spec owes its environment twice, and the two debts have different creditors:

  * the **interpreter** decides *which path runs at all* (`reproduce.sh` picks one that can import
    numpy and fails with the requirement if none can) -- that debt was already paid;
  * the **build** -- that interpreter's version together with the versions of the dependencies whose
    values enter the comparison -- decides *which values come out*. That is what a declared tolerance
    is measured against, and it is invisible in the first: this package's four artefacts come out
    byte-identical under some builds and differ under others, from the same command over the same
    seeds and the same committed inputs.

`build.json` is the package's record of that coordinate, and this file owns it:

    python3 build_record.py --write --declaration "..."   records the RUNNING build (measured, never
                                                          typed) beside the declaration it rests on
    python3 build_record.py --line                        one line: this run's build and the named one
    python3 build_record.py --render                      writes the generated block in README.md
    python3 build_record.py --check                       re-renders and compares; exit non-zero on a
                                                          disagreement (a step of reproduce.sh)

**The block is rendered, not typed.** What a reader meets in `README.md` between the
`<!-- BUILD-COORDINATE -->` markers is produced by `--render` from `build.json`: the interpreter
version, the pinned dependency version, the declared band and the largest deviation measured between
builds at this head. A coordinate copied by hand into prose is a claim with no owner; here the owner
is `build.json`, the renderer is this file, and `--check` is what makes a stale copy impossible.

**Two kinds of statement, kept apart.** The build pair is MEASURED (`--write` reads the running
interpreter and imports numpy); the band and the cross-build deviation are DECLARED, with the source
of each named in `build.json`, because they are properties of a comparison between builds and not of
the machine that records them. The block states both, and names which is which.

Exit codes:  0 in agreement  |  1 on a disagreement (or on a refused `--write`).
"""
import argparse
import io
import json
import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD = os.path.join(HERE, "build.json")
README = os.path.join(HERE, "README.md")
START = "<!-- BUILD-COORDINATE:START -->"
END = "<!-- BUILD-COORDINATE:END -->"


def fmt(x):
    """`%g`: 1e-09 / 1e-12 / 1.243e-14 -- the form a reader can compare at a glance."""
    return "%g" % x


def measure():
    """The running build, MEASURED. numpy is imported, not name-dropped from memory."""
    import numpy
    return {"python": sys.version.split()[0], "numpy": numpy.__version__}


def block(record):
    """The generated block -- a pure function of the record, so `--render` and `--check` agree on
    every machine. What THIS run is doing is `--line`'s job, printed at run time and committed
    nowhere: a per-run fact written into a document is the same defect as a typed number.

    The lines are indented four spaces, where the spec already lives (`README.md` -> *One-command
    reproduction* renders as one indented code block), so the generated region is part of the block
    the item names rather than a paragraph beside it.
    """
    band, span = record["band"], record["cross_build_span"]
    lines = [START,
             "environment:  Python %s / numpy %s  --  the build the committed artefacts were re-derived"
             % (record["python"], record["numpy"]),
             "              under, byte-identically (see 'Builds measured' below)"]
    lines += textwrap.wrap(
        "tolerance:    exact on that build: the canonical comparison returns the committed digests, no "
        "band. On any OTHER build: |difference| <= %s absolute or %s relative, whichever is larger -- a "
        "difference inside that band is a COORDINATE, not a defect of the artefact; one outside it, or a "
        "non-numeric difference that is not a digest recomputed from the same artefact, is a failure."
        % (fmt(band["absolute"]), fmt(band["relative"])),
        width=98, subsequent_indent="              ")
    lines += textwrap.wrap(
        "Largest deviation measured between builds at this head: %s absolute -- %s."
        % (fmt(span["worst_absolute"]), span["fields"]),
        width=98, initial_indent="              ", subsequent_indent="              ")
    lines += textwrap.wrap("Source of that deviation: %s." % span["source"],
                           width=98, initial_indent="              ", subsequent_indent="              ")
    lines.append(END)
    return "\n".join("    " + l for l in lines)


def read_block():
    t = io.open(README, encoding="utf-8").read()
    i, j = t.find(START), t.find(END)
    if i < 0 or j < 0:
        raise SystemExit("BUILD RECORD FAILED: README.md carries no %s / %s marker pair" % (START, END))
    return t, i, j, t[i:j + len(END)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", action="store_true", help="print this run's build and the named build")
    ap.add_argument("--write", action="store_true", help="record the RUNNING build into build.json")
    ap.add_argument("--declaration", default="", help="the evidence the recorded build rests on")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--render", action="store_true", help="write the generated block into README.md")
    ap.add_argument("--check", action="store_true", help="re-render and compare")
    ap.add_argument("--record", default=RECORD)
    args = ap.parse_args()

    build = measure()
    record = json.load(io.open(args.record, encoding="utf-8")) if os.path.exists(args.record) else {}

    if args.write:
        if not args.declaration:
            print("REFUSED: --write records a coordinate, so it requires --declaration naming the"
                  " evidence: what was run, on which head, and what came out.")
            return 1
        if os.path.exists(args.record) and not args.force and record.get("python") and record.get("numpy"):
            print("REFUSED: %s already records Python %s / numpy %s. Re-recording a measured"
                  " coordinate needs --force and a new --declaration."
                  % (os.path.basename(args.record), record["python"], record["numpy"]))
            return 1
        for k in ("band", "cross_build_span"):
            if k not in record:
                print("REFUSED: %s must already carry %r -- it is a DECLARED property of the"
                      " comparison (a band and the cross-build evidence it rests on), not something a"
                      " recording run can measure." % (os.path.basename(args.record), k))
                return 1
        rec = {"python": build["python"], "numpy": build["numpy"], "band": record["band"],
               "cross_build_span": record["cross_build_span"], "declaration": args.declaration}
        io.open(args.record, "w", encoding="utf-8").write(json.dumps(rec, indent=1, sort_keys=True) + "\n")
        print("recorded build: Python %s / numpy %s -> %s" % (build["python"], build["numpy"],
                                                              os.path.basename(args.record)))
        print("  declaration: %s" % args.declaration)
        return 0

    if not record.get("python"):
        print("BUILD RECORD FAILED: %s carries no recorded build -- run --write under the named build"
              % os.path.basename(args.record))
        return 1

    if args.line:
        same = build["python"] == record["python"] and build["numpy"] == record["numpy"]
        print("build: this run Python %s / numpy %s | named Python %s / numpy %s (%s)"
              % (build["python"], build["numpy"], record["python"], record["numpy"],
                 "the named build" if same else "DIFFERENT -- the tolerance rule in README.md applies"))
        return 0

    if args.render:
        t, i, j, _blk = read_block()
        io.open(README, "w", encoding="utf-8").write(t[:i] + block(record) + t[j + len(END):])
        print("rendered the build-coordinate block into %s from %s"
              % (os.path.basename(README), os.path.basename(args.record)))
        return 0

    if args.check:
        _t, _i, _j, committed = read_block()
        fresh = block(record)
        same = committed.strip() == fresh.strip()
        print("build-coordinate block matches a fresh render: %s" % same)
        print("  named build: Python %s / numpy %s ; band %s absolute / %s relative ; declared span %s"
              % (record["python"], record["numpy"], fmt(record["band"]["absolute"]),
                 fmt(record["band"]["relative"]), fmt(record["cross_build_span"]["worst_absolute"])))
        if not same:
            print("  the committed block differs from the render -- run `build_record.py --render`")
        return 0 if same else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
