#!/usr/bin/env python3
"""The round-2 correction checker for issue #42 -- one check per required change, each two-sided.

The round-2 decision asks for four changes, all of them properties of the **build coordinate**:
name the build, print the build at every run, scope the tolerance to that build, and attribute a
cross-build difference instead of reporting it as a defect.

A check that never fires is decoration, so every check here PLANTS the condition it claims to detect
in a throwaway copy and requires the verdict to flip -- and every planted mutation lives either in a
temporary copy of the package or in a temporary arm directory.

**Correction round 3 -- a check whose verdict depends on a coordinate pins that coordinate, or says it
is not applicable.** Two arms here used to read the MACHINE while their sentence named a behaviour:

  * R2-3 ran `build_record.py --line` against the package's own record and required the string
    `(the named build)`, which appears only where the machine IS the named build, so the arm asserted
    this machine rather than the branch it names. Both branches are now driven from **control records
    derived from this run's own measured pair**, and the pair the tool prints is read back and required
    to be the pair it was told.
  * R2-6 pinned the comparator's *labels* to the named pair while the four instruments ran under the
    machine's interpreter, so on another build the arm reported the machine's arithmetic as a failure
    of the check. It is now two statements: R2-6a is about the comparator's **logic** (a produced set
    identical to the committed one is identical on any machine), and R2-6b is about **this machine**,
    whose warranted outcome is read from this machine's own coordinate -- exact on the named build,
    identical-or-attributed on any other -- with the named build's exactness DECLARED NOT TAKEN where
    this machine is not that build.

Every reading that could not be taken is reported as a DECLARED `NOT TAKEN:` line beside the verdict,
and nothing is written unless `--log PATH` asks for it, so a reader's run cannot overwrite the committed
copy. `--check` re-derives the log and compares it with the committed one: the declared lines (which name
the build, the tree, or a reading not taken) are present on both sides rather than equal, every check
line is paired with the same check on the other side, and everything else must be identical.

    python3 verify_correction_r2.py              # verdict to stdout, writes no file
    python3 verify_correction_r2.py --log FILE   # and writes the log to FILE
    python3 verify_correction_r2.py --check      # re-derive and compare with the committed log

Exit codes: 0 all checks pass | 1 at least one check failed.
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import evidence_log as EL

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
LOG_NAME = "correction_r2_verify.log"
LOG = os.path.join(HERE, LOG_NAME)
PY = sys.executable
START = "<!-- BUILD-COORDINATE:START -->"
END = "<!-- BUILD-COORDINATE:END -->"
VERSIONS = "0123"

OUT = []
RESULTS = []
NOT_TAKEN = []
HEADER_HEAD = None          # the revision the reading is taken at, when the tree cannot say (see --head)


def say(line=""):
    OUT.append(line)
    print(line)


def not_taken(what, why):
    """A reading this run could not take. It is printed as a DECLARED line just before the verdict --
    present in every log, its content a fact about this run's coordinate -- so a reader of the verdict
    sees it and the comparison does not read the machine as a disagreement."""
    NOT_TAKEN.append((what, why))


def check(cid, name, ok, detail=""):
    RESULTS.append((cid, ok))
    say("%-5s %-62s %s%s" % (cid, name, "PASS" if ok else "FAIL",
                             "" if not detail else "  -- " + detail))


def run(args, cwd):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def read(path):
    return io.open(path, encoding="utf-8").read()


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def block_of(text):
    i, j = text.find(START), text.find(END)
    return None if i < 0 or j < 0 else text[i:j + len(END)]


def block_numbers(blk):
    """The numeric claims the committed block makes: %g forms only, so version numbers are not read
    as deviations."""
    return {"band": re.search(r"\|\s*difference\|\s*<=\s*([0-9.]+e-?[0-9]+)\s*absolute", blk),
            "band_rel": re.search(r"([0-9.]+e-?[0-9]+)\s*relative", blk),
            "span": re.search(r"measured between builds at this head:\s*([0-9.]+e-?[0-9]+)", blk)}


def run_checks():
    OUT[:] = []
    for line in EL.header(HERE, declared_head=HEADER_HEAD):
        say(line)

    say("issue #42 correction round 2 -- the build coordinate, four required changes, each two-sided")
    say("")

    # ---------------------------------------------------------------------------------------------
    # R2-1 -- the spec NAMES the build: interpreter + the dependency whose values enter the comparison.
    # ---------------------------------------------------------------------------------------------
    record = json.load(io.open(os.path.join(HERE, "build.json"), encoding="utf-8"))
    readme = read(os.path.join(HERE, "README.md"))
    blk = block_of(readme)

    names_the_build = bool(blk) and ("Python %s" % record["python"]) in blk \
        and ("numpy %s" % record["numpy"]) in blk
    band_is_numeric = isinstance(record["band"]["absolute"], (int, float)) \
        and isinstance(record["band"]["relative"], (int, float))
    decl = record.get("declaration", "")
    # The evidence must name the HEAD the pair was measured at -- a coordinate whose evidence names no
    # revision is a claim with no owner. (A hex token, not the word "reproduced": the object is the head.)
    evidenced = bool(decl) and re.search(r"\b[0-9a-f]{7,40}\b", decl) is not None
    check("R2-1", "the record names the build, its band and the head the pair was measured at",
          names_the_build and band_is_numeric and evidenced,
          "Python %s / numpy %s in the block=%s ; band numeric=%s ; evidence names a head=%s"
          % (record["python"], record["numpy"], names_the_build, band_is_numeric, evidenced))

    # and the numbers the block STATES are the record's -- read from the text, not from the renderer
    nums = block_numbers(blk)
    stated = [m.group(1) for m in (nums["band"], nums["band_rel"], nums["span"]) if m]
    want = ["%g" % record["band"]["absolute"], "%g" % record["band"]["relative"],
            "%g" % record["cross_build_span"]["worst_absolute"]]
    check("R2-1b", "every number the committed block states is the record's own (read as text)",
          stated == want, "block states %s ; build.json holds %s" % (", ".join(stated), ", ".join(want)))

    # ---------------------------------------------------------------------------------------------
    # The rest runs in temporary directories: nothing is written beside the package.
    # ---------------------------------------------------------------------------------------------
    here = EL.measured_build()
    named_pair = {"python": record["python"], "numpy": record["numpy"]}
    is_named = here == named_pair
    tmp = tempfile.mkdtemp(prefix="r2verify-")
    try:
        for f in ("README.md", "build.json", "build_record.py"):
            shutil.copy(os.path.join(HERE, f), os.path.join(tmp, f))

        rc0, out0 = run([PY, "build_record.py", "--check"], tmp)
        clean = rc0 == 0 and "matches a fresh render: True" in out0

        write(os.path.join(tmp, "README.md"),
              readme.replace("Python %s" % record["python"], "Python 9.9.9", 1))
        rc1, out1 = run([PY, "build_record.py", "--check"], tmp)
        hand_edit_caught = rc1 != 0 and "matches a fresh render: False" in out1

        rec2 = dict(record)
        rec2["numpy"] = record["numpy"] + "-control"
        write(os.path.join(tmp, "build.json"), json.dumps(rec2, indent=1, sort_keys=True) + "\n")
        write(os.path.join(tmp, "README.md"), readme)
        rc2_, out2 = run([PY, "build_record.py", "--check"], tmp)
        stale_edit_caught = rc2_ != 0 and "matches a fresh render: False" in out2

        check("R2-2", "the block is generated from the record, so a hand-edit cannot survive",
              clean and hand_edit_caught and stale_edit_caught,
              "clean copy=%s ; edited block rejected=%s ; record-change rejected=%s"
              % (clean, hand_edit_caught, stale_edit_caught))

        # ---- R2-1c: the mechanisms that keep the pair from being TYPED, on a plantable copy --------
        write(os.path.join(tmp, "build.json"), json.dumps(record, indent=1, sort_keys=True) + "\n")
        rc_, out_ = run([PY, "build_record.py", "--write"], tmp)
        refuses_undeclared = rc_ != 0 and "REFUSED" in out_ and "--declaration" in out_
        rc_, out_ = run([PY, "build_record.py", "--write", "--declaration", "x at head deadbee"], tmp)
        refuses_retype = rc_ != 0 and "REFUSED" in out_ and "--force" in out_
        bare = os.path.join(tmp, "bare.json")
        write(bare, json.dumps({"band": record["band"],
                                "cross_build_span": record["cross_build_span"]}, indent=1) + "\n")
        rc_, out_ = run([PY, "build_record.py", "--line", "--record", bare], tmp)
        refuses_unrecorded = rc_ != 0 and "BUILD RECORD FAILED" in out_
        check("R2-1c", "the recorded pair cannot be typed: undeclared, unforced and unrecorded runs refuse",
              refuses_undeclared and refuses_retype and refuses_unrecorded,
              "--write without --declaration refused=%s ; re-recording without --force refused=%s ;"
              " a block with no record refused=%s"
              % (refuses_undeclared, refuses_retype, refuses_unrecorded))

        # -----------------------------------------------------------------------------------------
        # R2-3 -- the run PRINTS its build, BOTH branches, from control records derived from THIS
        # run's own pair. The arm must assert the mechanism (the record's pair against the running
        # one), not this machine: a record whose pair is this run's pair takes the named branch here,
        # and one whose pair differs takes the other. The pair the tool prints is read back.
        # -----------------------------------------------------------------------------------------
        mine = os.path.join(tmp, "control-mine.json")
        other = os.path.join(tmp, "control-other.json")
        write(mine, json.dumps({"python": here["python"], "numpy": here["numpy"],
                                "band": record["band"], "cross_build_span": record["cross_build_span"]},
                               indent=1, sort_keys=True) + "\n")
        write(other, json.dumps({"python": here["python"], "numpy": here["numpy"] + "-control",
                                 "band": record["band"],
                                 "cross_build_span": record["cross_build_span"]},
                                indent=1, sort_keys=True) + "\n")
        rc3, out3 = run([PY, "build_record.py", "--line", "--record", mine], HERE)
        said = re.search(r"build: this run Python (\S+) / numpy (\S+) \|", out3)
        says_named = (rc3 == 0 and "(the named build)" in out3 and said is not None
                      and [said.group(1), said.group(2)] == [here["python"], here["numpy"]])
        rc3b, out3b = run([PY, "build_record.py", "--line", "--record", other], HERE)
        says_other = rc3b == 0 and "DIFFERENT -- the tolerance rule in README.md applies" in out3b

        check("R2-3", "both branches of --line fire from control records derived from this run",
              says_named and says_other,
              "named branch (a record naming this run's own pair)=%s ; mismatch branch=%s" % (says_named, says_other))

        # What the COMMITTED record makes the run print HERE is a fact about this machine, not a
        # pass or a failure: recorded so a reader of the log can see which arm this machine is.
        rc3c, out3c = run([PY, "build_record.py", "--line"], HERE)
        say("observed: the committed record on THIS machine: %s" % out3c.strip().splitlines()[0])

        # -----------------------------------------------------------------------------------------
        # R2-4 -- reproduce.sh RUNS the coordinate and the checkers: step 0 prints the build and
        # checks the rendered block; a coordinate verdict is a separate exit path from a failure.
        # -----------------------------------------------------------------------------------------
        sh = read(os.path.join(HERE, "reproduce.sh"))
        has_steps = ("build_record.py --line" in sh and "build_record.py --check" in sh
                     and "artefact_compare.py --build" in sh and "--root" in sh)
        has_checkers = ("verify_correction_r1.py --check" in sh and "verify_correction_r2.py --check" in sh)
        has_paths = ("REPRODUCE: COORDINATE MISMATCH" in sh and "REPRODUCE: FAILED" in sh
                     and "exit 4" in sh)
        check("R2-4", "reproduce.sh runs the coordinate and re-derives both evidence logs",
              has_steps and has_checkers and has_paths,
              "coordinate steps present=%s ; both log checks present=%s ; both endings present=%s"
              % (has_steps, has_checkers, has_paths))

        # -----------------------------------------------------------------------------------------
        # R2-5 -- the comparison ATTRIBUTES: each arm states the exit code AND the sentence it must
        # print, and a traceback fails the arm even when the exit code is the wanted one. Every arm
        # is a FIXTURE (the comparator is told which pair it is on), so the arms are the same on any
        # machine.
        # -----------------------------------------------------------------------------------------
        REF = {v: json.load(io.open(os.path.join(HERE, "artefacts", "results_v%s.json" % v),
                                    encoding="utf-8")) for v in VERSIONS}

        def leaves(o, p=""):
            if isinstance(o, dict):
                for k in o:
                    yield from leaves(o[k], "%s/%s" % (p, k))
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    yield from leaves(v, "%s/%d" % (p, i))
            else:
                yield p, o

        def first_of(d, pred):
            for p, v in leaves(d):
                if pred(v):
                    return p

        def getpath(d, path):
            node = d
            for q in [q for q in path.split("/") if q]:
                node = node[int(q)] if isinstance(node, list) else node[q]
            return node

        def setpath(d, path, val):
            parts = [q for q in path.split("/") if q]
            node = d
            for q in parts[:-1]:
                node = node[int(q)] if isinstance(node, list) else node[q]
            k = parts[-1]
            if isinstance(node, list):
                node[int(k)] = val
            else:
                node[k] = val

        FLOAT2 = first_of(REF["2"], lambda x: isinstance(x, float) and x not in (0.0,))
        FLOAT3 = first_of(REF["3"], lambda x: isinstance(x, float) and x not in (0.0,))
        STR0 = first_of(REF["0"], lambda x: isinstance(x, str))
        OTHER = record["numpy"] + "-control"

        def redigest(d):
            rest = {k: x for k, x in d.items() if k != "digest"}
            return hashlib.sha256(json.dumps(rest, sort_keys=True).encode()).hexdigest()

        def inband(v, d):
            if v == "2":
                setpath(d, FLOAT2, getpath(d, FLOAT2) * (1 + 1e-14))

        def outofband(v, d):
            if v == "2":
                setpath(d, FLOAT2, getpath(d, FLOAT2) * (1 + 1e-6))

        def astring(v, d):
            if v == "0":
                setpath(d, STR0, getpath(d, STR0) + "TAMPERED")

        def rebuild(v, d):
            if v == "3":
                setpath(d, FLOAT3, getpath(d, FLOAT3) * (1 + 1e-14))
                d["digest"] = redigest(d)

        def stale(v, d):
            if v == "3":
                setpath(d, FLOAT3, getpath(d, FLOAT3) * (1 + 1e-14))

        def nothing(v, d):
            return None

        def refbroken(v, d):
            if v == "3":
                d["digest"] = "0" * 64

        ARMS = [
            ("A-inband-diffbuild", inband, OTHER, "produced", 4, "COORDINATE:",
             "an in-band difference on another build is the build's to explain"),
            ("B-inband-samebuild", inband, None, "produced", 1,
             "FAILURE: the running build IS the named build",
             "in band, but this IS the named build -- not the build's"),
            ("C-outofband-diffbuild", outofband, OTHER, "produced", 1, "OUTSIDE the band",
             "the band is a band, not a blank cheque"),
            ("D-nonnumeric-diffbuild", astring, OTHER, "produced", 1,
             "FAILURE: the build differs, but a difference is not explained by it",
             "a non-numeric difference is never a build effect"),
            ("E-rebuild-diffbuild", rebuild, OTHER, "produced", 4, "COORDINATE:",
             "a coupled difference whose digest was recomputed is the build's"),
            ("F-stale-digest", stale, OTHER, "produced", 1, "BROKEN",
             "a digest the artefact itself says is stale is not a build effect"),
            ("G-clean-diffbuild", nothing, OTHER, "produced", 0, "identical to the committed ones",
             "identical artefacts are identical on any build"),
            ("H-reference-digest-broken", refbroken, OTHER, "reference", 1, "BROKEN",
             "the REFERENCE artefact contradicting its own digest is a defect, not a licence"),
            ("I-missing-artefact", nothing, OTHER, "produced", 1, "MISSING",
             "a produced artefact that is not there is not a coordinate"),
            ("J-no-reference", nothing, OTHER, "reference", 1, "NO REFERENCE",
             "a committed artefact that is not there is a defect of the package"),
        ]
        arms = os.path.join(tmp, "arms")
        arm_fail = []
        for name, mut, rn, side, want, marker, why in ARMS:
            top = os.path.join(arms, name)
            for tag, sub in (("reference", "artefacts"), ("produced", "build")):
                d = os.path.join(top, sub)
                os.makedirs(d, exist_ok=True)
                for v in VERSIONS:
                    obj = json.loads(json.dumps(REF[v]))
                    if tag == side:
                        mut(v, obj)
                    write(os.path.join(d, "results_v%s.json" % v), json.dumps(obj, indent=1))
            if name == "I-missing-artefact":
                os.remove(os.path.join(top, "build", "results_v1.json"))
            if name == "J-no-reference":
                os.remove(os.path.join(top, "artefacts", "results_v1.json"))
            rp = os.path.join(top, "build.json")
            write(rp, json.dumps(record, indent=1, sort_keys=True) + "\n")
            args = [PY, os.path.join(HERE, "artefact_compare.py"), "--build", os.path.join(top, "build"),
                    "--root", top, "--record", rp, "--run-python", record["python"]]
            args += ["--run-numpy", record["numpy"]] if rn is None else ["--run-numpy", rn]
            p = subprocess.run(args, cwd=HERE, capture_output=True, text=True)
            problems = []
            if p.returncode != want:
                problems.append("exit %d, wanted %d" % (p.returncode, want))
            if marker not in p.stdout:
                problems.append("printed no %r" % marker)
            if "Traceback" in p.stderr:
                problems.append("raised %s" % p.stderr.strip().split("\n")[-1])
            say("        arm %-26s exit=%d want=%d  %s" % (name, p.returncode, want,
                                                          "ok" if not problems else "PROBLEM"))
            for pr in problems:
                say("            !! " + pr)
            if problems:
                arm_fail.append(name)
        check("R2-5", "the comparison attributes a cross-build difference (10 planted arms)",
              not arm_fail,
              "all %d arms reported the wanted verdict AND the wanted sentence" % len(ARMS)
              if not arm_fail else "failed: %s" % ", ".join(arm_fail))

        # -----------------------------------------------------------------------------------------
        # R2-6a -- the comparator's LOGIC, on any machine: a produced set identical to the committed
        # one is identical, so the verdict is exit 0 with no band invoked and no label pinned.
        # -----------------------------------------------------------------------------------------
        fix = os.path.join(tmp, "identical-fixture")
        os.makedirs(fix, exist_ok=True)
        for v in VERSIONS:
            shutil.copy(os.path.join(HERE, "artefacts", "results_v%s.json" % v), fix)
        rc6a, out6a = run([PY, os.path.join(HERE, "artefact_compare.py"), "--build", fix, "--root", HERE,
                           "--record", os.path.join(HERE, "build.json")], HERE)
        check("R2-6a", "identical artefacts are identical on ANY machine (the comparator's logic)",
              rc6a == 0 and "identical to the committed ones" in out6a,
              "a fixture copied from the committed artefacts: exit=%d, and the verdict says so=%s"
              % (rc6a, "identical to the committed ones" in out6a))

        # -----------------------------------------------------------------------------------------
        # R2-6b -- THIS machine, declared. The four instruments really run under this interpreter and
        # the comparator is told THIS machine's pair, so the warranted outcome is the one this
        # machine's own coordinate implies: exact on the named build, identical-or-attributed
        # otherwise. Never a failure that belongs to the machine.
        # -----------------------------------------------------------------------------------------
        build = tempfile.mkdtemp(prefix="r2verify-build-")
        try:
            shutil.copytree(os.path.join(HERE, "instruments"), os.path.join(build, "instruments"))
            shutil.copytree(os.path.join(HERE, "evidence"), os.path.join(build, "evidence"))
            for f in ("instrument_v0.py", "instrument_v1.py", "instrument_v2.py", "instrument_v3.py"):
                shutil.copy(os.path.join(HERE, "instruments", f), os.path.join(build, f))
            shutil.copy(os.path.join(HERE, "artefacts", "calibration_dossier.json"), build)
            ran = []
            for v in VERSIONS:
                rc, out = run([PY, "instrument_v%s.py" % v], build)
                ran.append(rc == 0)
            rc6, out6 = run([PY, os.path.join(HERE, "artefact_compare.py"), "--build", build,
                             "--root", HERE, "--record", os.path.join(HERE, "build.json"),
                             "--run-python", here["python"], "--run-numpy", here["numpy"]], HERE)
            if is_named:
                ok6 = rc6 == 0 and "IDENTICAL" in out6
                outcome = "the named build: exactness is required, and the four artefacts are identical"
            else:
                ok6 = rc6 in (0, 4)
                outcome = ("not the named pair: the warranted outcome is identical (0) or attributed"
                           " (4), and this run took %s" % ("identical" if rc6 == 0 else "attributed"))
            # the DETAIL is invariant (it is compared with the committed log on any machine); what this
            # machine specifically did is a fact about the run's coordinate and goes on a declared line
            check("R2-6b", "the package on THIS machine reaches the outcome its own coordinate warrants",
                  all(ran) and ok6,
                  "the four instruments ran under this machine's interpreter and the comparator was told"
                  " THIS machine's pair, never the named one -- so this check cannot report the machine's"
                  " arithmetic as a failure of the package")
            say("observed: R2-6b on this machine (Python %s / numpy %s): instruments ran=all,"
                " comparator exit=%d, %s" % (here["python"], here["numpy"], rc6, outcome))
            # -----------------------------------------------------------------------------------
            # R2-7 -- the LOG COMPARISON is two-sided. It is the rule this round added, and a rule
            # nobody has seen fire is decoration: a real difference must be caught, while a difference
            # in a declared line, or a reading not taken, must not be read as a disagreement.
            # -----------------------------------------------------------------------------------
            # Each arm is built from the COMMITTED text alone (the object the comparison is taken
            # against), never from this run's own render: a fixture that moved with the checker would
            # have been a control on the checker, not on the rule.
            committed_log = read(LOG) if os.path.exists(LOG) else ""
            arm_real = arm_coord = arm_skip = None
            if committed_log:
                lines = committed_log.split("\n")
                # (a) one character moved in a COMPARED line: must be caught
                for k, l in enumerate(lines):
                    if l.startswith("CORRECTION R2:"):
                        lines[k] = l.replace("ALL PASS", "FAIL")
                        break
                arm_real = EL.compare(committed_log, "\n".join(lines) + "\n")[0]
                # (b) the coordinate lines replaced wholesale: declared, not a disagreement
                lines2 = [("taken on: build Python 9.9.9 / numpy 9.9.9   |   named build Python 9.9.9"
                           " / numpy 9.9.9 (DIFFERENT)") if l.startswith("taken on:") else l
                          for l in committed_log.split("\n")]
                ok2, declared2, _nt2, _m2 = EL.compare(committed_log, "\n".join(lines2))
                # ONE changed coordinate line is one declared line. (This arm read `>= 2` while the
                # comparison counted a both-sides declared line twice -- the control was pinned to the
                # defect it was meant to detect, and it is the reason the count is asserted, not just ok.)
                arm_coord = ok2 and declared2 == 1
                # (c) a reading reported as not taken, inserted where the committed log records one
                lines3 = []
                for l in committed_log.split("\n"):
                    if l.startswith("CORRECTION R2:"):
                        lines3.append("NOT TAKEN: a planted reading -- planted by this control")
                    lines3.append(l)
                ok3, d3, _nt3, _m3 = EL.compare(committed_log, "\n".join(lines3))
                # the inserted reading is accounted for as DECLARED (the comparison does not read the
                # machine as a disagreement); that it is counted, not ignored, is the assertion
                arm_skip = ok3 and d3 >= 1
            check("R2-7", "the log comparison is itself two-sided (a real difference vs a declared one)",
                  arm_real is False and arm_coord and arm_skip,
                  "a planted verdict change is caught=%s ; one changed coordinate line is declared"
                  " (counted once)=%s ; an inserted reading reported as not taken is not a"
                  " disagreement=%s"
                  % (arm_real is False, bool(arm_coord), bool(arm_skip)))
            if not is_named:
                not_taken("R2-6 the named build's exactness",
                          "this machine is Python %s / numpy %s; the named pair is Python %s / numpy %s"
                          " and is not installed here, so that reading cannot be re-taken on this"
                          " machine (R2-6a covers the comparator's logic on any machine)"
                          % (here["python"], here["numpy"], named_pair["python"], named_pair["numpy"]))
        finally:
            shutil.rmtree(build, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    passed = sum(1 for _c, ok in RESULTS if ok)
    say("")
    # DECLARED: every reading this run could not take, in a form a reader cannot mistake for a pass.
    # Its content is a fact about this run's coordinate, so it is present in every log and compared for
    # presence rather than for equality -- otherwise the log could only be re-derived on one machine.
    for w, y in NOT_TAKEN:
        say("NOT TAKEN: %s -- %s" % (w, y))
    say("CORRECTION R2: %s (%d/%d)" % ("FAIL" if passed != len(RESULTS) else "ALL PASS",
                                       passed, len(RESULTS)))
    say("   every check above was read on this machine; a reading marked NOT TAKEN is not covered by this"
        " verdict and is reported as not taken, never as a pass")
    say("   named build: Python %s / numpy %s ; band %s absolute / %s relative ; arms planted in a"
        " temporary copy, nothing written beside the package unless --log asks for it"
        % (record["python"], record["numpy"], "%g" % record["band"]["absolute"],
           "%g" % record["band"]["relative"]))
    return 0 if passed == len(RESULTS) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=None, help="also write the log to this path (default: write nothing)")
    ap.add_argument("--check", action="store_true",
                    help="re-derive the log and compare it with the committed %s" % LOG_NAME)
    ap.add_argument("--head", default=None,
                    help="the revision this reading is taken at, DECLARED: a plain directory (a git"
                         " archive export) cannot derive it")
    args = ap.parse_args()
    global HEADER_HEAD
    HEADER_HEAD = args.head

    rc = run_checks()
    lines = list(OUT)
    if args.check:
        committed = io.open(LOG, encoding="utf-8").read()
        ok, declared, nottaken, mism = EL.compare(committed, EL.render(lines))
        print("")
        print("%s vs a fresh run: %s" % (LOG_NAME, "MATCH" if ok else "MISMATCH"))
        print("   %d declared line(s) (a build, a tree, or a reading not taken); %d line(s) where this"
              " run took no reading where the committed log records one" % (declared, nottaken))
        for n, x, y in mism[:6]:
            print("   !! line %d" % n)
            print("      committed: %s" % x[:160])
            print("      fresh:     %s" % y[:160])
        return 0 if ok else 1
    if args.log:
        EL.write(args.log, lines)
        print("")
        print("log written to %s" % args.log)
    return rc


if __name__ == "__main__":
    sys.exit(main())
