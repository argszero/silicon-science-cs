#!/bin/sh
# Issue #153 -- one command reproduces every number in the manuscript.
#
# Contract: each step's exit status is accumulated into FAILED and the script exits with it,
# so a failing step can never be masked by a later one.  Steps 1-5 are offline and
# deterministic; step 6 re-renders the reference report from the STORED verification state,
# so reproduction needs no network.  Refreshing the pool itself does need network and is a
# separate, explicitly-network step (build_refs.py, place_refs.py without --render-only).
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE" || exit 1
PY=${PY:-/usr/bin/python3}
# matplotlib (used only by the figure step) needs a writable cache dir; without this it
# writes into the reader's HOME and can fail there for reasons unrelated to the figure
MPLCONFIGDIR=${MPLCONFIGDIR:-/tmp/mplcfg};
export MPLCONFIGDIR
FAILED=0
NOTRUN=0

step() {
    name=$1; shift
    printf '== %s\n' "$name"
    # A declared dependency, probed in the interpreter this run will use.  Absent -> NOT RUN, never
    # a failed step: the journal's exit-code contract says a step that could not run must not be
    # counted as one that ran and disagreed.  Declared here rather than in a wrapper so the step
    # invocation keeps its `step \"N/M ...\"` form, which is what check_steps.py reads.
    if [ "${1:-}" = "--needs" ]; then
        pkg=$2; shift 2
        if ! "$PY" -c "import $pkg" >/dev/null 2>&1; then
            notrun "declared dependency '$pkg' is not importable by $PY, so this step was not taken"
            return 0
        fi
    fi
    "$@"
    rc=$?
    if [ "$rc" -ne 0 ]; then
        printf '   FAILED (exit %s): %s\n' "$rc" "$name"
        FAILED=$((FAILED + 1))
    fi
    return 0
}

# A declared dependency that is absent is NOT RUN, never a failed step.  The exit-code contract
# this package follows says so, and the distinction is not cosmetic: a reader who sees `FAILED`
# goes looking for a defect in the figure, while the figure step was simply never taken.  The
# count of steps stays nine either way, because the step is still a step of this script.
notrun() {
    printf '   NOT RUN: %s\n' "$1"
    NOTRUN=$((NOTRUN + 1))
}

step "1/9 certificate: DP vs independent brute force, every instance enumerated" \
     "$PY" certificate.py
step "2/9 characterisation: per-cell losses, horizon, anti-rule control" \
     "$PY" characterise.py
step "3/9 proposition: empty-intersection witness for non-locality" \
     "$PY" lemma.py
step "4/9 scale test: the falsifier, with the K=2 control and the positive rule" \
     "$PY" lemma_scale.py
step "5/9 results: every number the manuscript states, emitted from the programs above" \
     "$PY" emit_results.py
step "6/9 figure: the discipline figure, redrawn from results.json, byte-identical" \
     --needs matplotlib "$PY" make_figure.py --check
step "7/9 manuscript: regenerate manuscript.md from results.json + placement.json" \
     "$PY" make_manuscript.py
step "8/9 reference report: regenerate from STORED verification state, must be byte-identical" \
     sh ./check_reference_report.sh
step "9/9 step statement: the count this package states, against the count this script runs" \
     "$PY" check_steps.py

if [ "$FAILED" -eq 0 ] && [ "$NOTRUN" -eq 0 ]; then
    printf '\nREPRODUCE: ALL GREEN (9 steps)\n'
else
    printf '\nREPRODUCE: %s%s\n' \
        "$([ "$FAILED" -gt 0 ] && echo "$FAILED STEP(S) FAILED, ")" \
        "$([ "$NOTRUN" -gt 0 ] && echo "$NOTRUN STEP(S) NOT RUN")"
fi
exit "$FAILED"
