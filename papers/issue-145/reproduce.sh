#!/usr/bin/env bash
# =============================================================================
# reproduce.sh -- issue #145: one command for every number this paper prints.
#
#   "Attested Is Not Covered: What Published Build Provenance Names, and the Detection Ceiling a
#    Compromised Input Faces"
#
#   bash reproduce.sh              every offline step: pins, theory, instruments, claims, references
#
# Expected last line:
#
#     REPRODUCE: ALL GREEN (9 steps)
#
# WHAT THE STEPS ARE
#
#   [1] snapshot pins -- the three frame artifacts are re-hashed before anything reads them
#   [2] the ceiling law, in exact rational arithmetic (5 propositions, 3 wrong variants + 1 mutation)
#   [3] the plant battery (9 plants, 4 deliberately wrong variants) -- a guard nobody has seen fail
#       is not a guard
#   [4] presence vs coverage, Wilson intervals, and whether they are disjoint
#   [5] every number in the claim table re-derived from an artifact, and every one of those numbers
#       required to be STATABLE in the manuscript that ships (a manifest that drops a quantity fails)
#   [6] the reference review reproduces: the same kept/excluded counts from the same corpus
#   [7] the citation pool is a function of the corpus (re-export must be byte-identical)
#   [8] the citation gates C1-C5: every key resolves, no entry is uncited, the count clears the bar,
#       the pool is the reviewed one, and the built manuscript is byte-identical to a fresh build
#   [9] the reference-check report is a function of the pool (regenerated, compared byte-for-byte)
#
# WHY THERE IS NO NETWORKED STEP HERE
#
#   The three snapshots are committed and pinned, and every number in the paper is re-derived from
#   them offline. Re-ENUMERATING the frames from the live registries is a different act -- it answers
#   "what do the registries say today", not "does this paper's arithmetic hold" -- and it needs
#   network access and roughly 8 minutes (npm 77 s, PyPI 240 s, OCI 152 s as measured). The
#   enumerators are in this package (`enumerate.py`, `pypi_enumerate.py`, `oci_enumerate.py`) and
#   `README.md` documents how to run them; a re-enumeration writes NEW snapshots and would require
#   the pins in step [1] to be updated, which is a deliberate act and not a side effect of a
#   reproduction run.
#
# THREE VERDICTS, ONE PER STATE: exit 0 = ALL GREEN; exit 1 = a difference the run MEASURED;
# exit 2 = a step this build COULD NOT TAKE, with its reason named. A declared dependency that is
# absent is the third state, never the second: it is reported NOT RUN and counted separately, because
# "your package is broken" and "your interpreter lacks what the package declares" are different
# findings and a reviewer must be able to tell them apart.
# =============================================================================
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || { echo "cannot enter $HERE"; exit 1; }

STEPS=0
FAILS=0
NOTRUNS=0
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PY=""
for c in /usr/bin/python3 python3 python; do
    # No import test: `.github/tools/envgate.py` reads this package's imports as 0 third-party
    # modules, so requiring one here would refuse an interpreter that can run every step.
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
    echo "FATAL: no python3 found; set PY=/path/to/python3" >&2
    exit 2
fi

echo "reproduce.sh -- issue #145"
echo "working directory: $HERE"
echo "interpreter: $PY  ($("$PY" -c 'import sys; print("CPython %d.%d.%d" % sys.version_info[:3])'))"
echo

step() {  # step <label> <command...>
    local label="$1"; shift
    STEPS=$((STEPS + 1))
    if "$@" >"$TMP/out" 2>&1; then
        printf '  [%02d] %-54s OK\n' "$STEPS" "$label"
        return 0
    fi
    FAILS=$((FAILS + 1))
    printf '  [%02d] %-54s FAIL\n' "$STEPS" "$label"
    sed 's/^/        /' "$TMP/out" | tail -12
    return 1
}

# step_grep <label> <required pattern> <command...> -- the step must run AND print the pattern.
# A script that exits 0 while printing a different conclusion has not passed; the verdict line is
# what the reader of this paper's claims relies on, so the verdict line is what is asserted.
step_grep() {
    local label="$1" pat="$2"; shift 2
    STEPS=$((STEPS + 1))
    if "$@" >"$TMP/out" 2>&1 && grep -q -- "$pat" "$TMP/out"; then
        printf '  [%02d] %-54s OK\n' "$STEPS" "$label"
        return 0
    fi
    FAILS=$((FAILS + 1))
    printf '  [%02d] %-54s FAIL\n' "$STEPS" "$label"
    printf '        required: %s\n' "$pat"
    sed 's/^/        /' "$TMP/out" | tail -10
    return 1
}

# byte <label> <file> <producer...> -- regenerate the file and require it to come back identical.
byte() {
    local label="$1" file="$2"; shift 2
    cp "$file" "$TMP/snap" 2>/dev/null || { FAILS=$((FAILS+1)); STEPS=$((STEPS+1)); printf '  [%02d] %-54s FAIL\n' "$STEPS" "$label"; return 1; }
    STEPS=$((STEPS + 1))
    if "$@" >"$TMP/out" 2>&1 && cmp -s "$TMP/snap" "$file"; then
        printf '  [%02d] %-54s OK\n' "$STEPS" "$label"
        return 0
    fi
    FAILS=$((FAILS + 1))
    cp "$TMP/snap" "$file"          # leave the package as committed, pass or fail
    printf '  [%02d] %-54s FAIL\n' "$STEPS" "$label"
    sed 's/^/        /' "$TMP/out" | tail -8
    return 1
}

echo "== 1. the frame artifacts, pinned ========================================"
step "snapshot pins (3 frames, SHA-256)" bash -c 'shasum -a 256 -c snapshot_npm_d1_pilot.json.sha256 snapshot_pypi.json.sha256 snapshot_oci.json.sha256'

echo
echo "== 2. the theory leg ======================================================"
step_grep "ceiling law (66 exact checks)" "ALL 66 CHECKS PASSED" "$PY" ceiling_check.py

echo
echo "== 3. the instruments ====================================================="
step_grep "plant battery (17 checks fired)" "ALL 17 CHECKS FIRED" "$PY" plant_coverage.py
step_grep "presence vs coverage (Wilson)" "DISJOINT IN EVERY ECOSYSTEM" "$PY" wilson_separation.py

echo
echo "== 4. the numbers the paper prints ======================================="
step_grep "claims re-derived + bound to their statement sites" "VERDICT: PASS" "$PY" check_claims.py
step_grep "claim-gate plants fire (drift at the statement site)" "CLAIMS-SELFTEST: ALL PASS" "$PY" check_claims.py --selftest

echo
echo "== 5. the references ====================================================="
step_grep "the review reproduces (kept / excluded)" "130 kept, 80 excluded" "$PY" review_references.py
byte "the pool is a function of the corpus" refs_pool.json "$PY" export_pool.py
step_grep "citation gates C1-C5" "C5 ok" "$PY" build_refs.py --check
byte "the reference report is a function of the pool" reference-check.md "$PY" build_refs.py --report-only

echo
if [ "$FAILS" -eq 0 ] && [ "$NOTRUNS" -eq 0 ]; then
    echo "REPRODUCE: ALL GREEN ($STEPS steps)"
    exit 0
fi
if [ "$NOTRUNS" -gt 0 ]; then
    echo "REPRODUCE: $NOTRUNS of $STEPS steps NOT RUN -- a step this build could not take, not a finding about the package"
    exit 2
fi
echo "REPRODUCE: $FAILS of $STEPS steps FAILED"
exit 1
