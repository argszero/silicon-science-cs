#!/usr/bin/env python3
"""Read the FOLLOW-UP required changes of the round-2 decision at the objects they name.

WHICH CLOCK THIS FILE'S NAME USES.  The journal's clock counts EDITOR decisions.  This thread's open decision is
**round 2** (the R444 decision; the sibling file `verify_revision_round2.py` reads its four items), and the three
items below come from the R446 re-check of that same round -- a comment asking for a further change does not open
a round.  The author's own turn count, which this file carried as `verify_revision_round3.py`, is not the
journal's clock: an artifact that numbers a decision differently from the thread it reads is the defect R446
filed against `reproduce.sh`'s step list, one level up (there, two bases for one step list).  Aligned here rather
than filed again.  **Author turn R420 = journal revision round 2, follow-up 1.**

WHAT IT READS.  Every item is read at its object -- a file, or an instrument actually run -- and the script prints
what it read, so the verdict is auditable:

  1, 1b  one numbering basis for the run's steps, and each step names how it was read
  2, 2a  the run's own declaration of how many build-bound steps it carries, and that each header's declared
         reading is the one its body carries (read at TWO objects: what it declares and what it calls)
  2b     the SOURCE orders the reported steps before the exact ones -- stated as the source property it reads
  2c     the manifest names every step and its reading
  3      the comparator's verdicts, MEASURED on plants, at the DECLARED build
  3b     where the comparator cannot run it says NOT RUN and exits 2 -- not FAIL, and not a traceback
  4      a required count LOST from a carrier turns the counts checker red
  5-5d   the README declares the three build-bound steps, carries the foreign-build reading, states the
         matplotlib absence as local, and computes its tolerance margins from the numbers it names

THE BUILD IS DECLARED, NOT HARDCODED -- this is what the R446 re-check required.  The first version pinned
`PY = "/usr/bin/python3"` for its child processes and printed no build line, so on a host whose `/usr/bin/python3`
carries no numpy, item 3 read the child's traceback as `(1, '?')` and the script printed
**`(D) NOT DISCHARGED`** -- a finding about the INTERPRETER reported as a finding about the manuscript, which is
the very rule this round's required change is about (*a reading names the build it is read against*).  Now:

  * `$PY` (this file's own interpreter; stdlib only) and `$CMP_PY` (the interpreter that runs the comparator, so
    it needs numpy) are read from the environment with a declared fallback order, and BOTH are printed with the
    version of every dependency that enters the comparison;
  * if no candidate can carry numpy, item 3 is **NOT RUN** and the verdict is **NOT ASSESSED** (exit 2) -- the
    journal's own code for *not run* -- never "NOT DISCHARGED".

Exit: 0 = every item discharged | 1 = an item NOT discharged | 2 = at least one item NOT RUN (not assessed).

Usage:
  python3 artefacts/assembly/verify_revision_round2_followup.py [--pkg DIR] [--cmp-py PATH]
  python3 artefacts/assembly/verify_revision_round2_followup.py --selftest      the battery, on scratch copies
"""
import importlib.util
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FOREIGN = os.path.expanduser("~/.asdf/installs/python/3.14.6/bin/python3")   # this study's second build
GATES = os.path.expanduser("~/.local/bin/python3.12")                        # the journal's gates' interpreter
READING_WORDS = ("reported", "rendered", "exact")
# The declared fallback order for the comparator's interpreter.  `$CMP_PY` first (a reviewer's own build), then
# the pinned build's interpreter, then the study's second build.  Nothing is probed silently: the choice is
# printed with the version it carries.
CMP_CANDIDATES = ["/usr/bin/python3", FOREIGN]   # used only when the caller names no interpreter

_spec = importlib.util.spec_from_file_location("build_bound", os.path.join(HERE, "build_bound.py"))
build_bound = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_bound)      # the comparator is IMPORTED, not copied: one owner for the probe
PINNED = build_bound.PINNED


def py_version(path):
    r = subprocess.run([path, "-c", "import sys;print(sys.version.split()[0])"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def resolve_cmp(explicit=None):
    """(path, build) for the comparator's interpreter -- or (None, why not).

    An interpreter NAMED by the caller (`--cmp-py`, else `$CMP_PY`) is **binding**: the caller declared the build
    the readings are to be taken at, so silently falling back to another one would answer a different question
    than the one asked -- and if the named interpreter cannot carry numpy, that is the finding (`NOT ASSESSED`).
    Only when nothing is named does the default path walk the declared candidate list, and it prints its choice
    with the version it carries.
    """
    named = explicit or os.environ.get("CMP_PY")
    order = [named] if named else list(CMP_CANDIDATES)
    tried = []
    for cand in order:
        if not cand:
            continue
        cand = os.path.expanduser(cand)
        if not os.path.exists(cand):
            tried.append("%s (absent)" % cand)
            continue
        v = build_bound.numpy_at(cand)
        if v:
            return cand, "python %s / numpy %s%s" % (py_version(cand), v,
                                                    "  [named by the caller, so binding]" if named else "")
        tried.append("%s (numpy ABSENT)" % cand)
    return None, ("the named interpreter carried no numpy: " if named else "no candidate carries numpy: ") \
        + ", ".join(tried)


def numpy_less_interpreter():
    """An interpreter to exercise the comparator's NOT RUN path, found by MEASUREMENT, never by assumption.

    The candidates are declared (this file's own interpreter, the pinned build's, the study's second build, the
    journal's gates' interpreter) and the first that cannot import numpy is returned; None if every one carries
    it -- in which case the battery reports that case NOT RUN rather than scoring it against an unmutated file.
    """
    for cand in sorted({sys.executable, "/usr/bin/python3", FOREIGN, GATES}):
        if os.path.exists(cand) and build_bound.numpy_at(cand) is None:
            return cand
    return None


def checks(pkg, cmp_py=None, cmp_build=None):
    """Returns (verdict, rows).  verdict: 'discharged' | 'not-discharged' | 'not-assessed'.

    A row's third field is True (ok), False (not discharged) or None (NOT RUN -- not assessed), so an item that
    could not be taken is never counted as either verdict about the manuscript.
    """
    p = lambda *a: os.path.join(pkg, *a)
    rows = []
    add = lambda i, w, ok, e: rows.append((i, w, ok, e))
    rep = io.open(p("reproduce.sh"), encoding="utf-8").read()
    readme = io.open(p("README.md"), encoding="utf-8").read()
    # A phrase is what a READER sees: a hard line break inside it is a property of the file, not of the
    # sentence.  Every prose probe below reads this flattened form (R415's lesson, relearned when the
    # foreign-build sentence wrapped between "Python" and "3.9.6 / numpy 2.0.2").
    flat = " ".join(readme.split())
    cc_src = io.open(p("artefacts", "assembly", "counts_check.py"), encoding="utf-8").read()
    bodies = re.split(r'^echo "=== \d+/\d+ ', rep, flags=re.M)[1:]   # one block per step, split at the NUMBERED
    # step headers only -- the preamble is `echo "=== build ...` and splitting on a bare `=== ` put it in the
    # list, shifting every body by one (an earlier version of this check read step 5's body as step 4's).

    # ---- 1: ONE numbering basis -- the steps are 1..N with no duplicate and no gap, and each carries a
    # reading word, so "five steps" is a property of the file rather than of the prose around it.
    heads = re.findall(r'^echo "=== (\d+)/(\d+) ([^\n]*)', rep, re.M)
    nums = [int(a) for a, _, _ in heads]
    dens = set(b for _, b, _ in heads)
    worded = [h for h in heads if any(w in h[2].lower() for w in READING_WORDS)]
    add("1", "the run numbers its steps on one basis (1..N, no duplicate, no gap)",
        nums == list(range(1, len(nums) + 1)) and len(dens) == 1 and len(nums) >= 5,
        "step headers read: %s | denominator(s): %s" % (nums, sorted(dens)))
    add("1b", "every step header names how it was read (REPORTED / RENDERED / EXACT)",
        len(worded) == len(heads) and len(heads) > 0,
        "with a reading word: %d of %d -- %s"
        % (len(worded), len(heads), [h[2][:34] for h in heads]))

    # ---- 2: the build-bound steps are DECLARED, and none of them is last.
    declared = {int(a): ("build-bound" if any(w in h.lower() for w in ("reported", "rendered")) else "exact")
                for a, _, h in heads}
    called = {}
    for head, body in zip(heads, bodies):
        bb_call = ("build_bound.py" in body) or ("--control-only" in body)
        ex_call = ("cmp -s" in body) or ("GATE: PASS" in body) or ("same " in body)
        called[int(head[0])] = ("build-bound" if bb_call and not ex_call else
                                "exact" if ex_call and not bb_call else "mixed")
    bb = sorted(n for n, k in declared.items() if k == "build-bound")
    ex = sorted(n for n, k in declared.items() if k == "exact")
    disagree = {n: (declared[n], called[n]) for n in declared if declared[n] != called[n]}
    m = re.search(r'TOLERANCE -- WHICH STEPS ARE READ AGAINST THE PINNED BUILD: \*\*(\w+)\*\*', rep)
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    n_declared = words.get(m.group(1).lower()) if m else None
    add("2", "the run declares the number of build-bound steps that its bodies carry",
        n_declared is not None and n_declared == len(bb),
        "preamble declares %s build-bound step(s); the headers declare %s (steps %s)"
        % (n_declared, len(bb), bb))
    add("2a", "every step's declared reading is the one its body carries",
        not disagree, "declared vs called: %s" % {n: called[n] for n in sorted(called)})
    # 2b reads the SOURCE's ordering.  The property the round is about -- a foreign-build reader REACHING the
    # reported reading -- is a property of a run, and a run is where it is measured (the editorial re-check ran
    # it on two foreign builds at this head).  This item names the property it actually reads.
    add("2b", "SOURCE ordering: every reported-for-build step precedes every exact (stop-condition) step",
        len(bb) > 0 and len(ex) > 0 and max(bb) < min(ex),
        "read top to bottom (bash runs them in this order: no parallelism, no conditional reordering): "
        "build-bound steps %s | exact steps %s" % (bb, ex))
    man = rep[rep.index("manifest of what was compared"):]
    man_steps = [l.strip() for l in man.split("\n") if re.match(r'\s*echo "\s*\d+/%d ' % len(heads), l)]
    add("2c", "the manifest names all %d steps and their readings" % len(heads),
        len(man_steps) == len(heads)
        and all(any(w in l for w in ("REPORTED", "RENDERED", "EXACT")) for l in man_steps)
        and sum(1 for w in ("REPORTED", "RENDERED", "EXACT") if w in man) == 3,
        "%d manifest line(s): %s" % (len(man_steps), [l.split("--")[0].strip() for l in man_steps]))

    # ---- 3: the comparator's verdicts, MEASURED on plants at the DECLARED build.  If no interpreter can run
    # it, this item is NOT RUN -- a third state, so that an environment fact is never printed as a verdict
    # about the manuscript.
    dig = p("artefacts", "results_digest.json")
    runs = {}
    cmp_note = "NOT RUN -- %s" % cmp_build if not cmp_py else ""
    if cmp_py:
        with tempfile.TemporaryDirectory() as tmp:
            d = json.load(io.open(dig, encoding="utf-8"))
            key = "panel.q8_over_q6_ratio_of_the_mid_band"
            base = d["quantities"][key]["value"]["mean"]
            plants = {}
            for name, val in (("ulp", math.nextafter(base, 2.0)), ("big", base * (1 + 1e-5))):
                c = json.loads(json.dumps(d))
                c["quantities"][key]["value"]["mean"] = val
                fp = os.path.join(tmp, name + ".json")
                io.open(fp, "w", encoding="utf-8").write(json.dumps(c, sort_keys=True))
                plants[name] = fp
            c = json.loads(json.dumps(d))
            del c["quantities"][key]
            fp = os.path.join(tmp, "struct.json")
            io.open(fp, "w", encoding="utf-8").write(json.dumps(c, sort_keys=True))
            plants["struct"] = fp
            for name, arg in (("unperturbed", dig), ("ulp", plants["ulp"]), ("big", plants["big"]),
                              ("struct", plants["struct"])):
                r = subprocess.run([cmp_py, p("artefacts", "assembly", "build_bound.py"), "json", dig, arg,
                                    "--label", name], capture_output=True, text=True)
                v = re.search(r'verdict\s+:\s+(NOT RUN|BITWISE|BUILD_BOUND|FAIL)', r.stdout)
                runs[name] = (r.returncode, v.group(1) if v else "?")
        cmp_note = "at %s: unperturbed %s | 1-ULP plant %s | 1e-5 plant %s | structural plant %s" % (
            cmp_build, runs["unperturbed"], runs["ulp"], runs["big"], runs["struct"])
    add("3", "the comparator's three verdicts are reachable at the declared build, and only a real departure "
             "exits non-zero",
        None if not cmp_py else (runs["unperturbed"] == (0, "BITWISE") and runs["ulp"] == (0, "BUILD_BOUND")
                                 and runs["big"] == (1, "FAIL") and runs["struct"] == (1, "FAIL")),
        cmp_note)

    # ---- 3b: where it cannot run, it says NOT RUN (exit 2) -- not FAIL, and not a traceback.
    nl = numpy_less_interpreter()
    ok3b, note3b = None, "NOT RUN -- every declared interpreter carries numpy, so the path could not be exercised"
    if nl is not None:
        r = subprocess.run([nl, p("artefacts", "assembly", "build_bound.py"), "json", dig, dig, "--label", "nr"],
                           capture_output=True, text=True)
        v = (re.search(r'verdict\s+:\s+(NOT RUN|BITWISE|BUILD_BOUND|FAIL)', r.stdout) or [None, "?"])[1]
        ok3b = (r.returncode == 2 and v == "NOT RUN" and "NOTHING WAS COMPARED" in r.stdout
                and "Traceback" not in r.stderr)
        note3b = ("%s: exit %d, verdict %s, 'NOTHING WAS COMPARED' present %s, traceback on stderr %s"
                  % (nl, r.returncode, v, "NOTHING WAS COMPARED" in r.stdout, "Traceback" in r.stderr))
    add("3b", "the comparator says NOT RUN and exits 2 where it cannot run (never FAIL, never a traceback)",
        ok3b, note3b)

    # ---- 4: the loss that slipped past the previous checker is now caught, at the object, by a plant.
    with tempfile.TemporaryDirectory() as tmp:
        dst = os.path.join(tmp, "pkg")
        os.makedirs(os.path.join(dst, "artefacts", "assembly"))
        for rel in ("README.md", "reproduce.sh", "manuscript.md",
                    "artefacts/assembly/assembly-report.txt", "artefacts/results_digest.json"):
            shutil.copy(p(*rel.split("/")), os.path.join(dst, rel))
        rd, rpm = os.path.join(dst, "README.md"), os.path.join(dst, "reproduce.sh")
        t = io.open(rd, encoding="utf-8").read()
        assert "76 quantities, each read out" in t
        io.open(rd, "w", encoding="utf-8").write(t.replace("76 quantities, each read out", "76 quantities"))
        lost = subprocess.run([sys.executable, p("artefacts", "assembly", "counts_check.py"), "--pkg", dst],
                              capture_output=True, text=True)
        shutil.copy(p("README.md"), rd)
        t = io.open(rpm, encoding="utf-8").read()
        assert "76 quantities read out" in t
        io.open(rpm, "w", encoding="utf-8").write(t.replace("76 quantities read out", "the digest"))
        lost2 = subprocess.run([sys.executable, p("artefacts", "assembly", "counts_check.py"), "--pkg", dst],
                               capture_output=True, text=True)
    own = subprocess.run([sys.executable, p("artefacts", "assembly", "counts_check.py")],
                         capture_output=True, text=True)
    bat = subprocess.run([sys.executable, p("artefacts", "assembly", "counts_check.py"), "--selftest"],
                         capture_output=True, text=True)
    add("4", "a required count LOST from a carrier turns the counts checker red (the previous version passed it)",
        lost.returncode == 1 and "no longer stated" in lost.stdout and lost2.returncode == 1
        and own.returncode == 0 and "absent-by-design" in cc_src
        and bat.returncode == 0 and re.search(r'(\d+) case\(s\), \1 caught', bat.stdout) is not None,
        "planted loss -> counts_check exit %d | planted run-loss -> exit %d | unmutated -> exit %d | "
        "battery: %s" % (lost.returncode, lost2.returncode, own.returncode, bat.stdout.strip().split("\n")[0]))

    # ---- 5: the README declares the three build-bound steps and no longer calls every artefact exact.
    i = flat.find("**Measured on a foreign build")
    sec = readme[readme.index("## Which steps are read against the pinned build"):] \
        if "## Which steps are read against the pinned build" in readme else ""
    add("5", "the README declares the three build-bound steps and no longer calls every artefact exact",
        "Tolerance: exact" not in readme
        and sec.count("| 1/5 |") == 1 and sec.count("| 2/5 |") == 1 and sec.count("| 3/5 |") == 1
        and "**REPORTED**" in sec and "**RENDERED**" in sec and sec.count("**EXACT**") >= 2,
        "the tolerance section's rows: %s" % re.findall(r'\| (\d)/5 \|', sec))
    # The readings are read in the paragraph that MAKES the claim: a whole-file probe is satisfied by a
    # quotation elsewhere, which is how an inert plant stayed invisible in the previous version.
    para = flat[i:i + 2200] if i >= 0 else ""
    add("5b", "the foreign-build paragraph names both builds, the verdict, the worst departure and the exit code",
        i >= 0 and "3.14.6" in para and "2.5.1" in para and "3.9.6" in para and "2.0.2" in para
        and "BUILD_BOUND" in para and "1.610e-16" in para and "exits **0**" in para,
        "the paragraph reads: %s" % para[:200])
    # 5c: R446's required change 2 -- the absence must be stated as LOCAL, and the measured RENDER_BOUND reading
    # must be recorded.  The locality is read in the SENTENCE THAT STATES THE ABSENCE, not anywhere in the
    # paragraph: a marker sitting elsewhere leaves the absence itself reading as a property of the interpreter,
    # which is exactly the sentence the re-check called false (and which this check's first version let through).
    aidx = flat.find("no matplotlib")
    window = flat[max(0, aidx - 300):aidx] if aidx >= 0 else ""
    sentence = re.split(r'(?<=[.;])\s+', window)[-1] if window else ""      # the absence's own sentence
    local = re.search(r'(authored in|this environment|this host|installed here|locally)', sentence)
    add("5c", "the matplotlib absence is stated as LOCAL in its own sentence, and the measured RENDER_BOUND "
              "reading is recorded",
        aidx >= 0 and bool(local) and "matplotlib 3.11.1" in flat and "RENDER_BOUND" in para,
        "the absence's own sentence: %r | locality marker: %s | measured renderer recorded: %s"
        % (sentence[-120:], local.group(0) if local else "NONE",
           "matplotlib 3.11.1" in flat))
    # 5d: R446's required change 3 -- the margins must be arithmetic on the numbers they name, AND the two
    # carriers of that one claim (this README and reproduce.sh's preamble) must state the SAME numbers.  The
    # defect was not only the wrong margin: the two carriers named two different departures for one sentence.
    def margins(text):
        # The phrase and the number after it must be read in the SAME string: slicing the raw file at an offset
        # taken in the flattened one lands somewhere else and silently reads a neighbouring number (this check's
        # first version did exactly that and reported 1e-8 as the value of a phrase that names 2.192e-11).
        f = " ".join(text.split())
        out = []
        for mm in re.finditer(r'\*\*([\d.]+) orders (above|below)\*\*', f):
            nm = re.search(r'(\d+(?:\.\d+)?e[+-]?\d+)', f[mm.end():mm.end() + 200])
            out.append((float(mm.group(1)), mm.group(2), nm.group(1) if nm else None))
        return out[:3]

    rd_m, rep_m = margins(readme), margins(rep)
    ok_marg, note_marg = False, "the margins are not stated as arithmetic on three named numbers in both carriers"
    if len(rd_m) == 3 and len(rep_m) == 3:
        same_claim = rd_m == rep_m
        want = [round(abs(math.log10(1e-8 / float(num))), 2) for _, _, num in rd_m]
        ok_marg = same_claim and all(abs(stated - w) <= 0.15 for (stated, _, _), w in zip(rd_m, want))
        note_marg = ("README %s | reproduce.sh %s | the arithmetic gives %s orders | the two carriers agree %s"
                     % (rd_m, rep_m, want, same_claim))
    add("5d", "the tolerance's margins follow from the numbers they name, and both carriers state the same ones",
        ok_marg, note_marg)

    bad = [r for r in rows if r[2] is False]
    nr = [r for r in rows if r[2] is None]
    return ("not-discharged" if bad else "not-assessed" if nr else "discharged"), rows


def report(pkg, cmp_py=None):
    chosen, build = resolve_cmp(cmp_py)
    print("build -- every reading below names the interpreter it was taken at, and this file declares it")
    print("  verifier   : %s  (%s)" % (sys.executable, build_bound.build_line()))
    print("  comparator : %s" % ("NOT RUN -- %s" % build if not chosen else "%s  (%s)" % (chosen, build)))
    print("  build pinned: %s   (the build the committed records name)" % PINNED)
    print()
    verdict, rows = checks(pkg, chosen, build)
    for i, what, ok, ev in rows:
        print("%-4s %-78s %s\n     %s"
              % (i, what, "ok" if ok is True else "NOT RUN (not assessed)" if ok is None else "NOT DISCHARGED",
                 ev))
    n_ok = sum(1 for _, _, ok, _ in rows if ok is True)
    n_nr = sum(1 for _, _, ok, _ in rows if ok is None)
    print("\n%d of %d item(s) pass at their objects%s"
          % (n_ok, len(rows), "" if not n_nr else ", %d NOT RUN" % n_nr))
    if verdict == "discharged":
        print("(D) and the R446 follow-up items DISCHARGED")
        return 0
    if verdict == "not-assessed":
        print("(D) NOT ASSESSED at this build -- an item above could not be run, which is a fact about the "
              "interpreter, not a verdict about the manuscript.  Name an interpreter that carries numpy "
              "(`--cmp-py PATH` or `CMP_PY=PATH`).  Exit 2 = NOT RUN, the journal's own code.")
        return 2
    print("(D) NOT DISCHARGED")
    return 1


def selftest():
    """The battery: re-introduce each property's defect on scratch copies and require the exit code to move.

    One case exercises a STATE rather than a defect (the R446 requirement: a missing dependency must not read as
    a verdict), and a case that cannot run on this host is reported NOT RUN and COUNTED -- never scored against
    an unmutated package, because an inert plant proves nothing (R415).
    """
    pkg = os.path.dirname(os.path.dirname(HERE))
    cases, allok, skipped = [], True, []
    tmpdir = tempfile.mkdtemp()

    def scratch():
        dst = os.path.join(tmpdir, "pkg")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(pkg, "artefacts", "assembly"), os.path.join(dst, "artefacts", "assembly"))
        for rel in ("README.md", "reproduce.sh", "manuscript.md"):
            shutil.copy(os.path.join(pkg, rel), os.path.join(dst, rel))
        shutil.copy(os.path.join(pkg, "artefacts", "results_digest.json"),
                    os.path.join(dst, "artefacts", "results_digest.json"))
        return dst

    def edit(rel, old, new, count=1):
        def apply(dst):
            fp = os.path.join(dst, rel)
            t = io.open(fp, encoding="utf-8").read()
            assert old in t, "plant not present in %s: %r" % (rel, old)
            out = t.replace(old, new, -1 if count == 0 else count)   # count=0 means ALL: str.replace's own
            # `count=0` replaces NOTHING, and a plant that changes no text is inert -- it would score the case
            # against an unmutated package and read as "the check missed it".  So the mutation is asserted.
            assert out != t, "plant made no change in %s: %r" % (rel, old)
            io.open(fp, "w", encoding="utf-8").write(out)
        return apply

    def case(name, mutate, want, env=None, must=None, must_not=None):
        nonlocal allok
        dst = scratch()
        if mutate:
            mutate(dst)
        e = dict(os.environ)
        e.update(env or {})
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--pkg", dst],
                           capture_output=True, text=True, env=e)
        good = r.returncode == want
        if must:
            good = good and must in r.stdout
        if must_not:
            good = good and must_not not in r.stdout
        allok = allok and good
        cases.append((name, want, r.returncode, good, r.stdout))

    case("unmutated package", None, 0)
    case("(D) re-introduced: the digest step made the FIRST step, before the reported ones",
         lambda d: io.open(os.path.join(d, "reproduce.sh"), "w", encoding="utf-8").write(
             io.open(os.path.join(pkg, "reproduce.sh"), encoding="utf-8").read().replace(
                 "=== 2/5 results digest", "=== 1/5 results digest", 1).replace(
                 "=== 1/5 the two new instruments", "=== 2/5 the two new instruments", 1)),
         1)
    case("(D) re-introduced: a second numbering basis appears (the assembly step renumbered 3/5)",
         lambda d: io.open(os.path.join(d, "reproduce.sh"), "w", encoding="utf-8").write(
             io.open(os.path.join(pkg, "reproduce.sh"), encoding="utf-8").read().replace(
                 "=== 4/5 manuscript assembly", "=== 3/5 manuscript assembly", 1)),
         1)
    case("(D) re-introduced: the preamble's count of build-bound steps understated (three -> one)",
         edit("reproduce.sh", "PINNED BUILD: **three**", "PINNED BUILD: **one**"), 1)
    case("(D) re-introduced: the build-bound reading declared but never built (the comparator removed)",
         edit("reproduce.sh", "artefacts/assembly/build_bound.py json", "true # "), 1)
    case("a step header that declares no reading word",
         edit("reproduce.sh", "=== 3/5 figures (a rendering: reported, never a stop condition)", "=== 3/5 figures"),
         1)
    case("the README's foreign-build measurement removed (the build is no longer named)",
         edit("README.md", "3.14.6", "3.14.5", count=0), 1)
    case("the README's tolerance section removed (the under-declaration returns)",
         edit("README.md", "## Which steps are read against the pinned build",
              "## Tolerance: exact -- byte-identical"), 1)
    case("R446 item 2 re-introduced: the absence is no longer stated as local to this environment",
         edit("README.md", "On the environment this package was authored in, that same interpreter has",
              "That interpreter has"), 1)
    case("R446 item 3 re-introduced: the margin no longer follows from its number",
         edit("README.md", "**7.8 orders\nabove**", "**three orders above**"), 1)
    case("R446 item 3 (other half): the two carriers disagree on the number one claim names",
         edit("reproduce.sh", "**7.8 orders above** the digest's\n#     (1.610e-16)",
              "**7.8 orders above** the digest's\n#     (2.192e-11)"), 1)
    case("the counts checker's two-sidedness removed (required rows made optional)",
         edit("artefacts/assembly/counts_check.py", 'REQUIRED = "required"', 'REQUIRED = "absent-design"'), 1)
    # The R446 requirement itself, as a STATE: with the comparator's interpreter carrying no numpy, the script
    # must say NOT ASSESSED (exit 2) and must NOT print a verdict about the manuscript.
    nl = numpy_less_interpreter()
    if nl is None:
        skipped.append("the comparator's interpreter cannot carry numpy -> NOT ASSESSED (no numpy-less "
                       "interpreter among the declared candidates on this host)")
    else:
        case("R446 item 1: a comparator interpreter without numpy -> NOT ASSESSED, never 'NOT DISCHARGED'",
             None, 2, env={"CMP_PY": nl}, must="NOT ASSESSED", must_not="NOT DISCHARGED")
    print("FOLLOW-UP VERIFIER SELFTEST -- %d case(s) run, %d caught%s"
          % (len(cases), sum(1 for c in cases if c[3]),
             "" if not skipped else ", %d case(s) NOT RUN" % len(skipped)))
    for name, want, got, good, out in cases:
        print("  %-6s %-84s exit %d (want %d)" % ("ok" if good else "MISSED", name, got, want))
        if not good:
            for line in [l for l in out.split("\n") if "NOT DISCHARGED" in l or "MISSED" in l][:4]:
                print("         %s" % line.strip()[:150])
    for name in skipped:
        print("  NOT RUN %s" % name)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("SELFTEST: %s" % ("PASS" if allok else "FAIL"))
    return 0 if allok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    pkg = argv[argv.index("--pkg") + 1] if "--pkg" in argv else os.path.dirname(os.path.dirname(HERE))
    cmp_py = argv[argv.index("--cmp-py") + 1] if "--cmp-py" in argv else None
    return report(pkg, cmp_py)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
