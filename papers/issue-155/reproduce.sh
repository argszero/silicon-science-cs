#!/bin/sh
# Issue #155 -- one command reproduces every number in the manuscript.
#
# Contract: each step's exit status is accumulated into FAILED and the script
# exits with that count, so a failing step can never be masked by a later one.
# Everything here is offline and deterministic: exhaustive enumeration over all
# arrival orders, no sampling, no random seeds, no network.
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE" || exit 1
PY=${PY:-/usr/bin/python3}
MPLCONFIGDIR=${MPLCONFIGDIR:-/tmp/mplcfg}
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

step "1/5 results: certificate, threshold statistics, gap distributions, rule control" \
     "$PY" emit_results.py
step "2/5 figure: the discipline-gap figure, redrawn from results.json" \
     "$PY" make_figure.py
step "3/5 check: every stored summary recomputed from its rows" \
     "$PY" check_results.py
step "4/5 references: the placement still resolves and still matches the committed artifact" \
     "$PY" place_refs.py --check
step "5/5 manuscript: every number still binds, every reference is still cited, bytes unchanged" \
     "$PY" make_manuscript.py --check

printf '\nREPRODUCE: %s\n' "$([ "$FAILED" -eq 0 ] && echo 'ALL GREEN (5 steps)' || echo "$FAILED STEP(S) FAILED")"
exit "$FAILED"
