#!/bin/sh
# reproduce.sh -- one command for every number this package states.
#
# Exit contract (the journal's): a step that fails increments FAILED and the script exits with the
# number of failed steps. A declared dependency that is ABSENT is NOT RUN, never a failed step --
# a reader must never see a failure where the run was never taken, and a real failure must never
# hide behind a skip.
#
# Two tiers, declared separately because they need different things:
#   TIER A  needs nothing but numpy and the committed fixture. Reproduces the mechanism table, both
#           endpoint controls, the gate selftests and the manuscript -- the numbers the paper's
#           claim rests on.
#   TIER B  needs the 1M corpus (501 MB, fetched by ./fetch_corpus.sh with a pinned sha256). Adds
#           the same axis at the harness's scale. NOT RUN when the corpus is absent.
#
# Usage: ./reproduce.sh [core|full]        (default: core = tier A only)
#        ./reproduce.sh full              (tier A + tier B)
set -u

HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE" || exit 1
SELF=$HERE/$(basename "$0")
MODE=${1:-core}
PY=${PY:-python3}

FAILED=0
NOTRUN=0
RUN_STEPS=0
TOTAL_STEPS=7

step() {
    _label=$1
    _needs=$2
    _cmd=$3
    RUN_STEPS=$((RUN_STEPS + 1))
    printf '== %s/%s %s\n' "$RUN_STEPS" "$TOTAL_STEPS" "$_label"
    # One call site per numbered slot: a tier that is not requested is a property of the step,
    # not a second copy of it in the other branch of an if. The `+tierB` prefix says "this step
    # exists only in full mode", and it is stripped before the dependency test.
    case $_needs in
      +tierB)
        if [ "$MODE" != "full" ]; then
            printf '   NOT RUN: tier B was not requested (run ./reproduce.sh full); tier A is unaffected\n'
            NOTRUN=$((NOTRUN + 1))
            return 0
        fi
        _needs=numpy ;;
    esac

    if [ -n "$_needs" ]; then
        if ! "$PY" -c "import $_needs" >/dev/null 2>&1; then
            printf '   NOT RUN: declared dependency %s is not importable by %s\n' "'$_needs'" "$PY"
            printf '            this is not a failure; to run this tier, name an interpreter that has it: PY=/path/to/python3 ./reproduce.sh %s\n' "$MODE"
            NOTRUN=$((NOTRUN + 1))
            return 0
        fi
    fi
    if sh -c "$_cmd"; then
        return 0
    fi
    printf '   FAILED: %s\n' "$_cmd"
    FAILED=$((FAILED + 1))
}

# The step total is not a number this script is allowed to state and not check: it is counted back
# off the call sites in this file. A step added without bumping TOTAL_STEPS used to leave the header
# claiming one fewer step than the run took, and a README quoting that header repeated the lie.
SITES=$(grep -c -E '^step "' "$SELF")
if [ "$SITES" -ne "$TOTAL_STEPS" ]; then
    printf 'reproduce: DECLARED_STEPS MISMATCH -- %s call site(s) in this script, TOTAL_STEPS=%s\n' \
           "$SITES" "$TOTAL_STEPS"
    printf '          the header would misnumber every step after the one added; fix the constant\n'
    exit 1
fi

printf 'reproduce: %s (%s steps) with %s\n' "$MODE" "$TOTAL_STEPS" "$PY"
printf 'working directory: %s\n\n' "$HERE"

# ---- 1: the committed fixture is the bytes this package measured -------------------------
step "fixture integrity: the committed subsample matches its recorded sha256" "" \
     "$PY verify_fixture.py"

# ---- 2: tier A, the mechanism table plus both endpoint controls -------------------------
step "mechanism table from the committed fixture (tier A)" "numpy" \
     "FIXTURE_SHA256=$($PY verify_fixture.py --print-sha) $PY run_mechanism.py"

# ---- 3: the artefact is reproducible, not merely produced --------------------------------
# A second run must produce the same bytes. A number that moves between two runs of the same
# program on the same input is not a measurement, and this package states numbers.
step "the artefact regenerates byte-identically" "numpy" \
     "cp results/mechanism.json /tmp/mechanism.1.json && \
      FIXTURE_SHA256=$($PY verify_fixture.py --print-sha) $PY run_mechanism.py >/dev/null && \
      cmp -s /tmp/mechanism.1.json results/mechanism.json && echo '   byte-identical'"

# ---- 4: the manuscript's claims, read back off the artefact ------------------------------
step "every claim the paper makes about the table holds" "" \
     "$PY check_claims.py"

# ---- 5: the gates that guard the paper can each refuse what they should ------------------
# A guard nobody has seen fail is not a guard. Both of these are offline: they run the refusal
# paths on fixtures, so this step proves the gates can reject, on every reproduction.
step "the reference gate and the manuscript gate can each refuse" "" \
     "$PY build_refs.py --selftest >/dev/null && $PY make_manuscript.py --selftest >/dev/null && \
      echo '   both gates refuse as documented'"

# ---- 6: the manuscript is generated, and regenerates byte-identically ---------------------
# Every number in the paper is a marker bound to an artefact, and every citation is resolved by
# program; the generator refuses to write the file at all if either is untrue.
step "the manuscript regenerates byte-identically from artefact and registry" "" \
     "cp manuscript.md /tmp/manuscript.1.md && $PY make_manuscript.py && \
      cmp -s /tmp/manuscript.1.md manuscript.md && echo '   byte-identical'"

# ---- 7: tier B, the same axis at 1M (needs the corpus) -----------------------------------
step "the same axis at 1M descriptors (tier B)" "+tierB" \
     "$PY run_scale.py"

printf '\n'
if [ "$FAILED" -eq 0 ] && [ "$NOTRUN" -eq 0 ]; then
    printf 'REPRODUCE: ALL GREEN (%s steps)\n' "$RUN_STEPS"
elif [ "$FAILED" -eq 0 ]; then
    printf 'REPRODUCE: %s STEP(S) NOT RUN, 0 failed (%s steps)\n' "$NOTRUN" "$RUN_STEPS"
else
    printf 'REPRODUCE: %s STEP(S) FAILED, %s NOT RUN (%s steps)\n' "$FAILED" "$NOTRUN" "$RUN_STEPS"
fi
exit "$FAILED"
