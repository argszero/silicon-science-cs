#!/bin/sh
# reproduce.sh -- one command for every number this package states.
#
# Exit contract (the journal's, from #158's self-triage): a step that fails increments FAILED and the
# script exits with the number of failed steps. A step whose program reports NOT RUN is counted
# separately -- never a failed step, and never a pass either.
#
# There is ONE tier, and it needs nothing but a CPython standard library. That is deliberate: this
# package has no dependency a clean machine might lack, so no step hides behind "absent dependency".
# The input (the trace's day-01 duration table) is committed xz-compressed, so no step needs a fetch
# either. The one NOT RUN below is not a missing dependency -- it is a claim the data cannot carry,
# and step 5 prints why on every run.
#
# Usage: ./reproduce.sh
set -u

HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE" || exit 1
SELF=$HERE/$(basename "$0")
PY=${PY:-python3}

FAILED=0
NOTRUN=0
RUN_STEPS=0
TOTAL_STEPS=6

step() {
    _label=$1
    _needs=$2
    _cmd=$3
    RUN_STEPS=$((RUN_STEPS + 1))
    printf '== %s/%s %s\n' "$RUN_STEPS" "$TOTAL_STEPS" "$_label"

    # The declared set is what the step's own program imports. Today that is the standard library
    # only, so this loop is empty on purpose; it is kept because the moment a step needs something
    # else, an absent dependency must be NOT RUN -- not a failure, and not a silent skip.
    for _mod in $_needs; do
        if ! "$PY" -c "import $_mod" >/dev/null 2>&1; then
            printf '   NOT RUN: declared dependency %s is not importable by %s\n' "'$_mod'" "$PY"
            printf '            this is not a failure; name an interpreter that has it: PY=/path/to/python3 ./reproduce.sh\n'
            NOTRUN=$((NOTRUN + 1))
            return 0
        fi
    done

    # A step's program has three outcomes, and the contract keeps them apart: 0 = it ran and agreed;
    # 3 = it did NOT RUN and says so; anything else = it failed. Collapsing the middle one into 0 is
    # how a verdict comes to claim a number that no run computed.
    sh -c "$_cmd"
    _rc=$?
    if [ "$_rc" -eq 0 ]; then
        return 0
    fi
    if [ "$_rc" -eq 3 ]; then
        printf '   NOT RUN: the step'"'"'s own program reported NOT RUN (exit 3) and printed why above.\n'
        printf '            this is not a failure, and it is not a pass: the step measured nothing.\n'
        NOTRUN=$((NOTRUN + 1))
        return 0
    fi
    printf '   FAILED: %s\n' "$_cmd"
    FAILED=$((FAILED + 1))
}

# The step total is not a number this script may state and not check: it is counted back off the call
# sites in this file. A step added without bumping TOTAL_STEPS would otherwise leave every later step
# misnumbered, and any README quoting the header would repeat the error.
SITES=$(grep -c -E '^step "' "$SELF")
if [ "$SITES" -ne "$TOTAL_STEPS" ]; then
    printf 'reproduce: DECLARED_STEPS MISMATCH -- %s call site(s) in this script, TOTAL_STEPS=%s\n' \
           "$SITES" "$TOTAL_STEPS"
    printf '          the header would misnumber every step after the one added; fix the constant\n'
    exit 1
fi

printf 'reproduce: (%s steps) with %s\n' "$TOTAL_STEPS" "$PY"
printf 'working directory: %s\n\n' "$HERE"

# ---- 1: the committed input is the bytes this package measured ---------------------------
# The digest identifies the DECOMPRESSED member, so a re-compression does not read as a different
# input while a different day's table cannot pass.
step "fixture integrity: the committed input decodes to its recorded sha256" "" \
     "$PY verify_fixture.py"

# ---- 2: the lemma and every refusal the instrument can perform ----------------------------
# A guard nobody has seen fail is not a guard, and a formula nobody evaluated at its known answer is a
# guess. This is where the boundary case, the unbounded case and the four refusals are exercised.
step "the censoring lemma and every refusal hold (instrument selftest)" "" \
     "$PY censored_tail.py"

# ---- 3: the measurement, and its reproducibility rather than its production ---------------
# A second run must produce the same bytes. A number that moves between two runs of the same program
# on the same input is not a measurement, and this package states numbers.
step "the artefact regenerates byte-identically" "" \
     "TMPF=\$(mktemp) && cp results/crossover.json \"\$TMPF\" && $PY run_crossover.py >/dev/null && \
      cmp -s \"\$TMPF\" results/crossover.json && rm -f \"\$TMPF\" && echo '   byte-identical'"

# ---- 4: the paper's claims, read back off the artefact -----------------------------------
# Every registered prior's verdict (MET / UNMET) is re-derived from the numbers, and the artefact's
# internal identities are checked. A refuted prior that quietly becomes agreement fails here.
step "every claim the paper makes about the table still follows from the artefact" "" \
     "$PY check_claims.py"

# ---- 5: the claim this data cannot carry, reported as NOT RUN ----------------------------
# Registered prior P1's second limb needs a noise estimate this data does not contain: the published
# table is 30-second interval means and one day is one measurement. Exit 3 is the honest outcome and
# it is why `ALL GREEN` is unreachable for this package -- see README.
step "the sampling-noise claim (P1 limb 2): can this data estimate it?" "" \
     "$PY check_noise.py"

# ---- 6: the gates themselves can refuse --------------------------------------------------
# Each of these runs the refusal paths of the guards used in steps 1 and 4, on fixtures. Without this
# the guards are only asserted to exist; with it they are shown to bite on every reproduction.
step "the fixture guard and the claim gate can each refuse what they must" "" \
     "$PY verify_fixture.py --selftest >/dev/null && $PY check_claims.py --selftest >/dev/null && \
      echo '   both gates refuse as documented'"

printf '\n'
if [ "$FAILED" -eq 0 ] && [ "$NOTRUN" -eq 0 ]; then
    printf 'REPRODUCE: ALL GREEN (%s steps)\n' "$RUN_STEPS"
elif [ "$FAILED" -eq 0 ]; then
    printf 'REPRODUCE: %s STEP(S) NOT RUN, 0 failed (%s steps)\n' "$NOTRUN" "$RUN_STEPS"
else
    printf 'REPRODUCE: %s STEP(S) FAILED, %s NOT RUN (%s steps)\n' "$FAILED" "$NOTRUN" "$RUN_STEPS"
fi
exit "$FAILED"
