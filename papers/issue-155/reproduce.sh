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

# The step count lives in three carriers -- this script's labels, README.md and the manuscript's
# reproducibility section -- and nothing used to compare them; they agreed by hand. It is the same
# defect that appeared on #128, #145 and #149, so here the program decides: TOTAL_STEPS is declared
# once, every label's "N/M" is checked against it, and both prose carriers are grepped for the
# verdict line this script actually prints.
TOTAL_STEPS=5
EXECUTED=0

step() {
    name=$1; shift
    n=${name%%/*}
    rest=${name#*/}
    m=${rest%% *}
    EXECUTED=$((EXECUTED + 1))
    if [ "$n" != "$EXECUTED" ]; then
        printf '   [FAIL] label says step %s, this is executed step %s\n' "$n" "$EXECUTED"
        FAILED=$((FAILED + 1))
    fi
    if [ "$m" != "$TOTAL_STEPS" ]; then
        printf '   [FAIL] label %s carries denominator %s, the script declares %s steps\n' \
               "$n" "$m" "$TOTAL_STEPS"
        FAILED=$((FAILED + 1))
    fi
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

# ---- the step count is checked, not remembered -------------------------------
printf '== step count\n'
if [ "$EXECUTED" != "$TOTAL_STEPS" ]; then
    printf '   [FAIL] the script declares %s steps and executed %s\n' "$TOTAL_STEPS" "$EXECUTED"
    FAILED=$((FAILED + 1))
else
    printf '   [ok]   %s steps declared, %s executed\n' "$TOTAL_STEPS" "$EXECUTED"
fi
for carrier in README.md manuscript.md; do
    if grep -q "ALL GREEN ($TOTAL_STEPS steps)" "$carrier"; then
        printf '   [ok]   %s states %s steps\n' "$carrier" "$TOTAL_STEPS"
    else
        printf '   [FAIL] %s does not state "ALL GREEN (%s steps)" -- it is a second copy of this script\n' \
               "$carrier" "$TOTAL_STEPS"
        FAILED=$((FAILED + 1))
    fi
done

printf '\nREPRODUCE: %s\n' "$([ "$FAILED" -eq 0 ] && echo "ALL GREEN ($TOTAL_STEPS steps)" || echo "$FAILED STEP(S) FAILED")"
exit "$FAILED"
