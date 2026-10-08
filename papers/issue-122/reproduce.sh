#!/usr/bin/env bash
# =============================================================================
# One-command reproduction for issue #122
#
#   "Prevention Is Not Cure: What Fresh-Data Rate a Self-Consuming Training Loop
#    Needs to Stay Stable, and What It Needs to Recover"
#
# WORKING DIRECTORY: the script cd's to its own directory, the package root
#
#     papers/issue-122/
#
# and every path it prints is relative to that directory.
#
# What it does, in order:
#
#   1. recompute the three artefacts from the instruments
#        spike_v1.py  the Jensen gap and its scope (both sides of the bound, binned by absence
#                     fraction), the two-route check, the hysteresis first-passage pair, the
#                     crossing brackets, the mean/variance certificates and the planted controls
#        spike_v2.py  the pool-window boundary, the moving-average mechanism, the w=1 and lam=1
#                     controls
#        spike_v3.py  the two criteria, the log-scale bisection, the behavioural control, the
#                     held-out test of every candidate mechanism quantity
#   2. regenerate the five figures from those artefacts      (make_figures.py)
#   3. regenerate the reference list and the citation report (make_references.py,
#                                                             make_reference_check.py)
#   4. re-assemble the manuscript and refuse if a number has no owner
#                                                             (build_manuscript.py)
#   5. validate the manuscript's claims against the artefacts (validate.py)
#   6. run the validation suite's own plant control            (validate.py --selftest)
#   7. verify the committed artefacts byte-for-byte            (checksums.sha256)
#
# Expected output, and the verdict a verifier compares:
#
#     VALIDATE 42/42
#     RESULT: PASS
#     SELFTEST 10/10 plants caught
#     CHECKSUMS [HARD] 30/30 files match the committed record
#     RESULT: PASS
#
# TOLERANCE: exact, not statistical.  validate.py prints an integer count of checks passed out of
# the number it ran, each attached to a specific claim in manuscript.md (the labels name the
# section); one failed check fails the run.  checksums.sha256 is the record of the submitted
# bytes.  The two-way contract is: this script passes on a fresh checkout, and it passes again on
# the same checkout immediately afterwards (it rewrites only the artefacts and figures it owns).
#
# Environment:
#   EMRG_PYTHON       interpreter for the instruments and the validator.  Any CPython >= 3.8 with
#                     numpy; the instruments otherwise import nothing outside the standard library.
#   EMRG_FIG_PYTHON   interpreter with matplotlib, for step 2 only.
#   REPRODUCE_QUICK=1 skip step 1 and validate the artefacts as committed (about 4 s).
#
# Measured wall-clock on the authoring machine (Apple silicon, /usr/bin/python3 3.9.6, numpy 2.0.2,
# matplotlib 3.9.4):
#   full (recompute + figures + validate): 78 s
#   quick (figures + validate):              9 s
# =============================================================================
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || { echo "cannot enter $HERE"; exit 1; }

echo "reproduce.sh -- issue #122 reproduction"
echo "working directory: $HERE"

QUICK="${REPRODUCE_QUICK:-0}"
START="$(date +%s)"

has_mod() { "$1" -c "import $2" >/dev/null 2>&1; }

pick() {  # pick <module> <candidate...>
    mod="$1"; shift
    for c in "$@"; do
        [ -n "$c" ] || continue
        command -v "$c" >/dev/null 2>&1 || continue
        if has_mod "$c" "$mod"; then echo "$c"; return 0; fi
    done
    return 1
}

PY="$(pick numpy "${EMRG_PYTHON:-}" python3 /usr/bin/python3 || true)"
if [ -z "$PY" ]; then
    echo "FATAL: no python3 with numpy found; set EMRG_PYTHON" >&2
    exit 1
fi
PY_FIG="$(pick matplotlib "${EMRG_FIG_PYTHON:-}" /usr/bin/python3 python3 || true)"

echo "interpreter (instruments): ${PY}"
echo "interpreter (matplotlib):  ${PY_FIG:-none found}"
echo "python version:            $("$PY" -V 2>&1)"
[ "$QUICK" = "1" ] && echo "mode: QUICK -- validating the committed artefacts without recomputing"

RUNLOG="run.log"
: > "$RUNLOG"
{
    echo "# issue #122 reproduction run"
    echo "# interpreter:    $PY  ($("$PY" -V 2>&1))"
    echo "# numpy:          $("$PY" -c 'import numpy; print(numpy.__version__)' 2>/dev/null)"
    echo "# matplotlib:     ${PY_FIG:-none}"
    echo "# mode:           $([ "$QUICK" = "1" ] && echo quick || echo full)"
    echo "#"
} >> "$RUNLOG"

step() {  # step <label> <command...>
    label="$1"; shift
    t0="$(date +%s)"
    if "$@" >> "$RUNLOG" 2>&1; then
        echo "   $(printf '%-30s' "$label") ok    $(( $(date +%s) - t0 )) s"
    else
        echo "   $(printf '%-30s' "$label") FAIL  $(( $(date +%s) - t0 )) s" >&2
        tail -25 "$RUNLOG" >&2
        exit 1
    fi
}

# ----------------------------------------------------------------- step 1: instruments
if [ "$QUICK" != "1" ]; then
    echo
    echo "== 1. instruments =========================================================="
    step "spike_v1.py" "$PY" spike_v1.py
    step "spike_v2.py" "$PY" spike_v2.py
    step "spike_v3.py" "$PY" spike_v3.py
    grep -E "^(wrote|route A vs B|Jensen gap|   above the closed)" "$RUNLOG" | sed 's/^/   /'
fi

# ----------------------------------------------------------------- step 2: figures
echo
echo "== 2. figures =============================================================="
if [ -n "$PY_FIG" ]; then
    step "make_figures.py" "$PY_FIG" make_figures.py
    grep -E "^   fig[0-9]" "$RUNLOG" | sed 's/^/   /'
else
    echo "SKIP: no matplotlib interpreter found (figures left as committed; this is stated, not"
    echo "      silently treated as a pass -- the manifest check in step 5 still reads them)"
fi

# ----------------------------------------------------------------- step 3: reference layer
echo
echo "== 3. reference layer ======================================================"
step "make_references.py" "$PY" make_references.py
step "make_reference_check.py" "$PY" make_reference_check.py
echo "   committed verification log: refs/verify.log ($(grep -c '^OK ' refs/verify.log) entries resolved by identifier)"
echo "   NOTE: a full RE-verification re-fetches every identifier from arXiv/Crossref and needs"
echo "         network reachability:   python3 refs_tool.py verify      (two-sided control: refs_tool.py plant)"

# ----------------------------------------------------------------- step 4: the manuscript
echo
echo "== 4. the manuscript ======================================================="
"$PY" build_manuscript.py || { echo "FATAL: the manuscript did not build" >&2; exit 1; }
"$PY" build_manuscript.py >> "$RUNLOG" 2>&1

# ----------------------------------------------------------------- step 5: validation
echo
echo "== 5. validation of the manuscript's claims ================================"
"$PY" validate.py || { echo "FATAL: validation failed" >&2; exit 1; }
"$PY" validate.py >> "$RUNLOG" 2>&1

# ----------------------------------------------------------------- step 6: the suite's own control
echo
echo "== 6. two-sided control on the validation suite itself ====================="
"$PY" validate.py --selftest || { echo "FATAL: the suite's plant control did not fire" >&2; exit 1; }
"$PY" validate.py --selftest >> "$RUNLOG" 2>&1

# ----------------------------------------------------------------- step 7: the committed bytes
echo
echo "== 7. the committed artefacts, byte for byte ==============================="
if [ -f checksums.sha256 ]; then
    EMRG_BUILD_PY="$PY" "$PY" - <<'EOF' | tee -a "$RUNLOG"
import hashlib, json, os, platform, subprocess, sys

# The byte-identity claim is scoped to the build that produced the committed artefacts: CPython
# 3.12 changed sum() to compensated summation, so the same code on a different interpreter can
# differ in the last ULP.  The check is therefore HARD on the recorded build and ADVISORY on any
# other, and it says which of the two it is rather than letting a build difference read as a defect.
here_py = "%d.%d.%d" % sys.version_info[:3]
try:
    rec = json.load(open("build.json"))
except Exception:
    rec = {}
same = rec.get("python", here_py) == here_py
try:
    import numpy
    same = same and rec.get("numpy", numpy.__version__) == numpy.__version__
except Exception:
    pass

bad = miss = ok = 0
for line in open("checksums.sha256"):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    want, name = line.split(None, 1)
    name = name.lstrip("*")
    if not os.path.exists(name):
        print("   MISSING %s" % name); miss += 1; continue
    got = hashlib.sha256(open(name, "rb").read()).hexdigest()
    if got != want:
        print("   DIFFERS %s" % name); bad += 1
    else:
        ok += 1
tag = "HARD" if same else "ADVISORY (build %s vs recorded %s/%s)" % (
    here_py, rec.get("python", "?"), rec.get("numpy", "?"))
print("CHECKSUMS [%s] %d/%d files match the committed record" % (tag, ok, ok + bad + miss))
sys.exit(1 if (bad or miss) and same else 0)
EOF
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "FATAL: the recomputed artefacts differ from the committed record on the SAME build" >&2
        exit 1
    elif ! grep -q "CHECKSUMS \[HARD\]" "$RUNLOG"; then
        echo "NOTE: the artefacts were produced by a different build; the checksum comparison above"
        echo "      is advisory, and every claim check in step 5 still had to pass."
    fi
else
    echo "CHECKSUMS: no checksums.sha256 in this package (skipped, and said so)"
fi

END="$(date +%s)"
{
    echo "#"
    echo "# wall-clock: $((END - START)) s"
    echo "RESULT: PASS"
} >> "$RUNLOG"
echo
echo "wall-clock: $((END - START)) s"
echo "RESULT: PASS"
