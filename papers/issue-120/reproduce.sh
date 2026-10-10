#!/usr/bin/env bash
# =============================================================================
# One-command reproduction for issue #120
#
#   "What Limits Memory Tiering? An Exact Oracle and the Workload-Intrinsic
#    Floor on Slow-Tier Traffic"
#
# WORKING DIRECTORY: the script cd's to its own directory, the package root:
#
#     papers/issue-120/
#
# and every path it prints is relative to that directory.
#
# What it does, in order:
#
#   1. recompute the six artefacts from the instruments
#        spike_v0.py  the two-route certificate, the bound control, the first P1 reading
#        spike_v1.py  the 42-cell grid: P1 limbs, the mechanism, the normalisation, the P2
#                     collision test, the reference layer's LRU/Mattson certificate
#        spike_v2.py  P3: below-head relief, the knee detector with a two-sided plant, Mattson
#        spike_v3.py  the closed form, the relief scale, the eight-candidate fit and holdout
#        spike_v4.py  the matched profile pair and the genericity sweep
#        spike_v5.py  the exhaustive and mid-scale profile-class spread
#   2. regenerate the five figures from those artefacts       (make_figures.py)
#   3. validate the manuscript's claims against the artefacts (validate.py)
#  3c. cross-check two carriers against their owners: this file's declared check count against
#      validate.py's, and the build the manuscript NAMES against the build run.log RECORDS
#   4. validate the reference layer's committed report        (inside validate.py)
#
# Expected output is stated in README.md.  The verdict a verifier compares is:
#
#     VALIDATE 41/41
#     RESULT: PASS
#
# plus, on the heavy tier, one `wrote <name>_results.json` line per instrument.
#
# TOLERANCE: exact, not statistical.  validate.py prints an integer count of checks that passed
# out of the number it ran; every one of the 41 must pass, and each is attached to a specific
# claim in manuscript.md (the check labels name the section).  A single failed check fails the
# run.  The two-way contract is: this script passes on a fresh checkout, and it passes again on
# the same checkout immediately afterwards (it rewrites only the artefacts and figures it owns).
#
# Environment:
#   EMRG_PYTHON       interpreter for the instruments and the validator.  Any CPython >= 3.8;
#                     the instruments import NOTHING outside the standard library.
#   EMRG_FIG_PYTHON   interpreter with matplotlib, for step 2 only.
#   REPRODUCE_QUICK=1 skip step 1 and validate the artefacts as committed (about 3 s).
#
# Measured wall-clock on the authoring machine (Apple silicon, /usr/bin/python3 3.9.6):
#   full (recompute + figures + validate):  84 s
#   quick (figures + validate):              5 s
# =============================================================================
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || { echo "cannot enter $HERE"; exit 1; }

# matplotlib writes its font cache under MPLCONFIGDIR.  Left unset on a host whose ~/.matplotlib is
# not writable, it prints an advisory naming a PER-RUN temporary directory, which is an environment
# reading rather than evidence -- and it would put a different string in run.log on every run, so the
# log could not reproduce byte-for-byte.  Pinning it here removes the advisory and the nondeterminism.
MPLCACHE="$(mktemp -d "${TMPDIR:-/tmp}/issue120-mpl.XXXXXX")"
export MPLCONFIGDIR="$MPLCACHE"
trap 'rm -rf "$MPLCACHE"' EXIT

echo "reproduce.sh -- issue #120 reproduction"
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

PY="$(pick json "${EMRG_PYTHON:-}" python3 /usr/bin/python3 || true)"
if [ -z "$PY" ]; then
    echo "FATAL: no usable python3 found; set EMRG_PYTHON" >&2
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
    echo "# issue #120 reproduction run"
    echo "# interpreter:    $PY  ($("$PY" -V 2>&1))"
    echo "# matplotlib:     ${PY_FIG:-none}"
    echo "# mode:           $([ "$QUICK" = "1" ] && echo quick || echo full)"
    echo "#"
} >> "$RUNLOG"

step() {  # step <label> <command...>
    label="$1"; shift
    t0="$(date +%s)"
    if "$@" >> "$RUNLOG" 2>&1; then
        echo "   $(printf '%-34s' "$label") ok   $(( $(date +%s) - t0 )) s"
    else
        echo "   $(printf '%-34s' "$label") FAIL $(( $(date +%s) - t0 )) s" >&2
        tail -25 "$RUNLOG" >&2
        exit 1
    fi
}

# ----------------------------------------------------------------- step 1: instruments
if [ "$QUICK" != "1" ]; then
    echo
    echo "== 1. instruments =========================================================="
    for s in spike_v0 spike_v1 spike_v2 spike_v3 spike_v4 spike_v5; do
        step "$s.py" "$PY" "$s.py"
        tail -1 "$RUNLOG"
    done
fi

# ----------------------------------------------------------------- step 2: figures
echo
echo "== 2. figures ============================================================="
if [ -n "$PY_FIG" ]; then
    step "make_figures.py" "$PY_FIG" make_figures.py
    sed -n '/figures from the committed/,$p' "$RUNLOG" | sed 's/^/   /' | tail -7
else
    echo "SKIP: no matplotlib interpreter found (figures left as committed; this is stated, not"
    echo "      silently treated as a pass -- the manifest check in step 3 still reads them)"
fi

# ----------------------------------------------------------------- step 3: validation
echo
echo "== 3. validation of the manuscript's claims ================================"
"$PY" validate.py || { echo "FATAL: validation failed" >&2; exit 1; }
"$PY" validate.py >> "$RUNLOG" 2>&1

# ----------------------------------------------------------------- step 3b: the suite's own control
echo
echo "== 3b. two-sided control on the validation suite itself ===================="
"$PY" validate.py --selftest || { echo "FATAL: the suite's plant control did not fire" >&2; exit 1; }
"$PY" validate.py --selftest >> "$RUNLOG" 2>&1

# ----------------------------------------------------------------- step 3c: the carriers
echo
echo "== 3c. the carriers of the count and the build agree with their owners ======"
# Two statements a reader follows, each owned by an instrument, checked here so the drift is a
# FAILED RUN rather than a reader's find.  The editorial return of 2026-10-10 named both:
#   * the declared check count in this file's OWN header, against what validate.py prints (it said
#     40 while the suite ran 41);
#   * the build the manuscript NAMES, against the build run.log RECORDS (the manuscript said
#     "Python 3.9" while the committed artefacts were produced by CPython 3.13.9).
SELF="$HERE/$(basename "$0")"
declared="$(sed -nE 's/^#     VALIDATE ([0-9]+\/[0-9]+)$/\1/p' "$SELF" | head -1)"
actual="$("$PY" validate.py | sed -nE 's/^VALIDATE ([0-9]+\/[0-9]+).*/\1/p' | head -1)"
logbuild="$(sed -nE 's/^# interpreter:.*\(Python ([0-9.]+)\).*/\1/p' "$RUNLOG" | head -1)"
manbuild="$(grep -m1 -oE 'CPython [0-9]+\.[0-9]+\.[0-9]+' manuscript.md | sed 's/CPython //')"
carrier_fail=0
[ "$declared" = "$actual" ] || {
    echo "   FAIL this file declares VALIDATE $declared; the suite prints VALIDATE $actual" >&2
    carrier_fail=1; }
[ -n "$manbuild" ] || { echo "   FAIL the manuscript names no CPython build" >&2; carrier_fail=1; }
[ "$logbuild" = "$manbuild" ] || {
    echo "   FAIL the manuscript names CPython $manbuild; run.log records $logbuild" >&2
    carrier_fail=1; }
[ "$carrier_fail" = 0 ] || exit 1
echo "   declared VALIDATE $declared == the suite's; manuscript's CPython $manbuild == run.log's"
{
    echo "# 3c carriers: VALIDATE $declared == suite; manuscript CPython $manbuild == run.log"
} >> "$RUNLOG"

# ----------------------------------------------------------------- step 4: reference layer
echo
echo "== 4. reference layer ======================================================"
echo "committed report: refs/verify.log ($(grep -c '^OK ' refs/verify.log) entries resolved by identifier)"
echo "NOTE: a full RE-verification re-fetches every identifier from arXiv/Crossref and needs"
echo "      network reachability; run it when the network allows:"
echo "          python3 refs_tool.py verify"
echo "      On a host where arXiv's API endpoint is unreachable this step cannot run; the"
echo "      committed report is the record of the run that was performed, and step 3 reads it."

END="$(date +%s)"
{
    echo "#"
    echo "# wall-clock: printed to the terminal, NOT written here -- it is a host reading, and a log"
    echo "#             that carries one cannot reproduce byte-for-byte."
    echo "RESULT: PASS"
} >> "$RUNLOG"
echo
echo "wall-clock: $((END - START)) s"
echo "RESULT: PASS"
