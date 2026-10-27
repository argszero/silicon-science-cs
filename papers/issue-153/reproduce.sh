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

step() {
    name=$1; shift
    printf '== %s\n' "$name"
    "$@"
    rc=$?
    if [ "$rc" -ne 0 ]; then
        printf '   FAILED (exit %s): %s\n' "$rc" "$name"
        FAILED=$((FAILED + 1))
    fi
    return 0
}

step "1/8 certificate: DP vs independent brute force, every instance enumerated" \
     "$PY" certificate.py
step "2/8 characterisation: per-cell losses, horizon, anti-rule control" \
     "$PY" characterise.py
step "3/8 proposition: empty-intersection witness for non-locality" \
     "$PY" lemma.py
step "4/8 scale test: the falsifier, with the K=2 control and the positive rule" \
     "$PY" lemma_scale.py
step "5/8 results: every number the manuscript states, emitted from the programs above" \
     "$PY" emit_results.py
step "6/8 figure: the discipline figure, redrawn from results.json, byte-identical" \
     "$PY" make_figure.py --check
step "7/8 manuscript: regenerate manuscript.md from results.json + placement.json" \
     "$PY" make_manuscript.py
step "8/8 reference report: regenerate from STORED verification state, must be byte-identical" \
     sh ./check_reference_report.sh

printf '\nREPRODUCE: %s\n' "$([ "$FAILED" -eq 0 ] && echo 'ALL GREEN (8 steps)' || echo "$FAILED STEP(S) FAILED")"
exit "$FAILED"
