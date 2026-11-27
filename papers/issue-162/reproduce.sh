#!/bin/sh
# reproduce.sh -- one command, a verdict per step.
#
# The contract this script keeps (and that this journal has paid for twice):
#   * a step that cannot run is NOT RUN, which is neither a pass nor a failure;
#   * a step that fails increments FAILED and the script exits non-zero;
#   * the step count printed is counted by this script, not typed (a header that drifts from the
#     script is the "standard must be the program" defect in its cheapest form).
#
# Network steps (harvest_refs.py --harvest / --verify) are deliberately NOT here: reproduction must
# run offline against the committed corpus. Re-harvesting is a maintenance action, documented in
# README.md, and it carries its own record of what it did.
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE" || exit 1

FAILED=0
NOTRUN=0
STEPS=0

step() {
    STEPS=$((STEPS + 1))
    name=$1
    shift
    printf '== %d %s\n' "$STEPS" "$name"
    if "$@" >> reproduce.log 2>&1; then
        printf '   [ok]   %s\n' "$name"
    else
        rc=$?
        if [ "$rc" -eq 3 ]; then
            NOTRUN=$((NOTRUN + 1))
            printf '   [n/r]  %s -- NOT RUN (exit 3): it measured nothing\n' "$name"
            printf '   [n/r]  %s\n' "$name" >> reproduce.log
        else
            printf '   [FAIL] %s (exit %d)\n' "$name" "$rc"
            FAILED=$((FAILED + 1))
        fi
    fi
}

: > reproduce.log
printf 'reproduce.sh -- issue #162\n'

step "instrument self-test (controls + one plant each)" ./nines.py --selftest
step "reading emitted from the grid"                  ./nines.py --grid --emit nines_findings.json
step "citations gated, manuscript rendered, report"   ./gate_citations.py --render manuscript.md --report reference-check.md

# Every derived artefact must come back byte-identical, and that comparison must run in the READER's
# hands. It used to be `git diff` / `git ls-files`, which needs a .git directory: in a `git archive`
# export -- what this journal's audit uses, and what a tarball download gives -- the three steps
# reported NOT RUN for every reader while reporting [ok] for the author. The manifest travels inside
# the package instead, so the check needs no git and no network.
step "artefacts match their sealed digests (no git needed)" ./seal_artefacts.py --verify

# The README's module list is a claim about the build, and it was wrong: `gate_citations.py` imports
# `html` and the sentence did not name it. The journal's `envgate` cannot catch that -- it asks only
# whether every THIRD-PARTY name is declared, and never asserts a stdlib one -- so the check lives
# here, where it reads both directions: a name the code imports and the sentence omits, and a name
# the sentence declares that nothing imports.
step "declared module list matches the modules the code imports" ./check_declared_env.py

# Section 8 answers a question about the literature. A hedge there was a requirement with no
# collector, so the collector is a step: it re-applies the declared screen to the stored search and
# refuses the whole step if a query never ran or a record that passed the screen carries no verdict.
# The harvest itself is a maintenance action (network), like `harvest_refs.py --harvest`.
step "the section-8 price search, re-derived offline"  ./price_search.py

# The step count this file prints and the count its documents state are two carriers, and they had
# drifted: the script ran six, the README's expected-output block printed five, and this file's own
# header said "three". The count is now read from the documents and compared with the call sites
# above, so a step added without the documents fails here. The header cannot be derived, so the rule
# for it is stricter: it states no count at all.
step "the file table matches the files this package ships" ./check_file_table.py
step "the stated step count matches the steps this script runs" ./check_step_count.py

printf '\nSTEPS RUN: %d   NOT RUN: %d\n' "$STEPS" "$NOTRUN"
if [ "$FAILED" -eq 0 ] && [ "$NOTRUN" -gt 0 ]; then
    printf 'REPRODUCE: %d STEP(S) NOT RUN -- they measured nothing, so this is neither a pass nor a failure\n' "$NOTRUN"
    exit 3
fi
if [ "$FAILED" -eq 0 ]; then
    printf 'REPRODUCE: ALL GREEN (%d steps)\n' "$STEPS"
    exit 0
fi
printf 'REPRODUCE: %d STEP(S) FAILED (%d steps)\n' "$FAILED" "$STEPS"
exit "$FAILED"
