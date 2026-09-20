"""verify_runs.py -- re-derive an instrument's byte-identity claim.

    python3 verify_runs.py <instrument.py> [scratch_dir]

Runs the instrument TWICE CONCURRENTLY from the research directory and ONCE from a FOREIGN working
directory (absolute paths only), then compares the four JSON artefacts (the three runs plus the landed
one) byte for byte, and the four logs after the DECLARED coordinate lines.

The declared coordinate lines are the ones that are properties of the INVOCATION rather than of the
run: the wall clock the instrument prints, and the output path the caller asked for.  They are dropped
EXPLICITLY and NAMED here -- a comparison loosened by a tolerant rule cannot see a difference that
matters, whereas a comparison that drops two named lines and says so can be read.

This file owns that form for the whole issue-50 instrument family.  (It began as
verify_fixedpoint_runs.py for one instrument; a second instrument copying it would have given the form
two owners, and a form with two owners drifts -- so it was generalised instead.  The fixedpoint claim
is still re-derived by `python3 verify_runs.py fixedpoint_v1.py`.)
"""
import hashlib
import io
import os
import re
import subprocess
import sys
import tempfile

COORDINATE_LINES = (r"^-- elapsed ", r"^wrote ")


def sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def norm(path):
    return "\n".join(l for l in io.open(path, encoding="utf-8").read().splitlines()
                     if not any(re.match(rx, l) for rx in COORDINATE_LINES))


def main(argv):
    script = argv[1] if len(argv) > 1 else "external_v1.py"
    W = os.path.dirname(os.path.abspath(__file__))
    T = argv[2] if len(argv) > 2 else tempfile.mkdtemp(prefix="verify_runs_")
    if not os.path.isabs(script):
        script = os.path.join(W, script)
    stem = os.path.basename(script)[:-3]
    codes = {}
    procs = []
    for tag in ("a", "b"):
        procs.append((tag, subprocess.Popen(
            [sys.executable, script, "--json", os.path.join(T, "run_%s.json" % tag)],
            cwd=W, stdout=io.open(os.path.join(T, "run_%s.log" % tag), "w"), stderr=subprocess.STDOUT)))
    for tag, p in procs:
        codes[tag] = p.wait()
    with io.open(os.path.join(T, "run_c.log"), "w") as fh:
        codes["c"] = subprocess.call([sys.executable, script, "--json", os.path.join(T, "run_c.json")],
                                     cwd=tempfile.gettempdir(), stdout=fh, stderr=subprocess.STDOUT)
    runs = [("a concurrent, research cwd", os.path.join(T, "run_a.json"), os.path.join(T, "run_a.log")),
            ("b concurrent, research cwd", os.path.join(T, "run_b.json"), os.path.join(T, "run_b.log")),
            ("c FOREIGN cwd, absolute paths", os.path.join(T, "run_c.json"), os.path.join(T, "run_c.log")),
            ("landed artefact", os.path.join(W, stem + ".json"), os.path.join(W, stem + ".log"))]
    ref_json, ref_log = sha(runs[0][1]), norm(runs[0][2])
    json_ok, log_ok = True, True
    for name, j, l in runs:
        sj, sl = sha(j) == ref_json, norm(l) == ref_log
        json_ok &= sj
        log_ok &= sl
        print("  %-32s json=%s %s  log=%s" % (name, sha(j)[:16], "same" if sj else "DIFFERENT",
                                              "same" if sl else "DIFFERENT"))
    print("declared coordinate lines dropped from the log comparison: %s" % (COORDINATE_LINES,))
    print("artefact sha256: %s" % ref_json)
    print("exit codes: %s" % codes)
    print("VERDICT %s: json byte-identical (4/4): %s | logs identical after the declared lines: %s"
          % (stem, json_ok, log_ok))
    print("OVERALL: %s" % ("PASS" if (json_ok and log_ok and set(codes.values()) == {0}) else "FAIL"))
    return 0 if (json_ok and log_ok and set(codes.values()) == {0}) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
