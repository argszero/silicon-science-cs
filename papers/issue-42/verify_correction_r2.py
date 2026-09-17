#!/usr/bin/env python3
"""The round-2 correction checker for issue #42 -- one check per required change, each two-sided.

The round-2 decision asks for four changes, all of them properties of the **build coordinate**:
name the build, print the build at every run, scope the tolerance to that build, and attribute a
cross-build difference instead of reporting it as a defect.

A check that never fires is decoration, so every check here PLANTS the condition it claims to detect
in a throwaway copy and requires the verdict to flip -- and every planted mutation lives either in a
temporary copy of the package or in a temporary arm directory. This file writes nothing outside the
temporary directories it creates and deletes them when it is done.

    python3 verify_correction_r2.py            # prints the verdict, writes correction_r2_verify.log

Exit codes: 0 all checks pass | 1 at least one check failed.
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "correction_r2_verify.log")
PY = sys.executable
START = "<!-- BUILD-COORDINATE:START -->"
END = "<!-- BUILD-COORDINATE:END -->"
VERSIONS = "0123"

OUT = []
RESULTS = []


def say(line=""):
    OUT.append(line)
    print(line)


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
# R2-2 -- the block is GENERATED, not typed: it cannot go stale and cannot be hand-edited.
# Two-sided: the untouched copy passes; a mutation in the block, and a mutation in the record, fail.
# ---------------------------------------------------------------------------------------------
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
    # R2-3 -- the run PRINTS its build. Two-sided: the named build says so; another build says the
    # tolerance rule applies. The other build is derived from the record, never typed.
    # -----------------------------------------------------------------------------------------
    rc3, out3 = run([PY, "build_record.py", "--line"], HERE)
    says_named = rc3 == 0 and "(the named build)" in out3

    other = os.path.join(tmp, "other-build.json")
    rec3 = dict(record)
    rec3["numpy"] = record["numpy"] + "-control"
    write(other, json.dumps(rec3, indent=1, sort_keys=True) + "\n")
    rc3b, out3b = run([PY, "build_record.py", "--line", "--record", other], HERE)
    says_other = rc3b == 0 and "DIFFERENT -- the tolerance rule in README.md applies" in out3b

    check("R2-3", "every run prints this run's build beside the named one (both branches)",
          says_named and says_other,
          "named branch=%s ; mismatch branch=%s" % (says_named, says_other))

    # -----------------------------------------------------------------------------------------
    # R2-4 -- reproduce.sh RUNS the coordinate: step 0 prints the build and checks the rendered
    # block; a coordinate verdict is a separate exit path from a failure.
    # -----------------------------------------------------------------------------------------
    sh = read(os.path.join(HERE, "reproduce.sh"))
    has_steps = ("build_record.py --line" in sh and "build_record.py --check" in sh
                 and "artefact_compare.py --build" in sh and "--root" in sh)
    has_paths = ("REPRODUCE: COORDINATE MISMATCH" in sh and "REPRODUCE: FAILED" in sh
                 and "exit 4" in sh)
    check("R2-4", "reproduce.sh runs the coordinate and keeps failure and coordinate apart",
          has_steps and has_paths,
          "steps present=%s ; both endings present=%s" % (has_steps, has_paths))

    # -----------------------------------------------------------------------------------------
    # R2-5 -- the comparison ATTRIBUTES: each arm states the exit code AND the sentence it must
    # print, and a traceback fails the arm even when the exit code is the wanted one.
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
        rec = dict(record)
        rp = os.path.join(top, "build.json")
        write(rp, json.dumps(rec, indent=1, sort_keys=True) + "\n")
        args = [PY, os.path.join(HERE, "artefact_compare.py"), "--build", os.path.join(top, "build"),
                "--root", top, "--record", rp, "--run-python", record["python"]]
        args += ["--run-numpy", record["numpy"]] if rn is None else ["--run-numpy", rn]
        p = subprocess.run(args, cwd=HERE, capture_output=True, text=True)
        out = p.stdout + p.stderr
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
    # R2-6 -- the package's own verdict, read from the real command: the comparison on the named
    # build must be exact (all four artefacts identical), which is what makes the band a statement
    # about OTHER builds and not a licence on this one.
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
        rc, out = run([PY, os.path.join(HERE, "artefact_compare.py"), "--build", build,
                       "--root", HERE, "--record", os.path.join(HERE, "build.json"),
                       "--run-python", record["python"], "--run-numpy", record["numpy"]], HERE)
        exact = rc == 0 and "IDENTICAL" in out and "results_v3.json" in out
        check("R2-6", "on the NAMED build the comparison is exact -- no difference to attribute",
              all(ran) and exact,
              "four instruments ran=%s ; comparator exit=%d" % (all(ran), rc))
    finally:
        shutil.rmtree(build, ignore_errors=True)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

passed = sum(1 for _c, ok in RESULTS if ok)
say()
say("CORRECTION R2: %s (%d/%d)" % ("ALL PASS" if passed == len(RESULTS) else "FAILED",
                                   passed, len(RESULTS)))
say("  named build: Python %s / numpy %s ; band %s absolute / %s relative ; arms planted in a"
    " temporary copy, nothing written beside the package but this log"
    % (record["python"], record["numpy"], "%g" % record["band"]["absolute"],
       "%g" % record["band"]["relative"]))
write(LOG, "\n".join(OUT) + "\n")
sys.exit(0 if passed == len(RESULTS) else 1)
