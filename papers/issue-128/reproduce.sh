#!/usr/bin/env bash
# =============================================================================
# reproduce.sh -- issue #128: one command for the core results.
#
#   "How Much Fairness Is Free? The Zero-Cost Region of Group Quotas"
#
#   bash reproduce.sh            fast  -> corpus pins + every certificate + canonical re-derivation
#   bash reproduce.sh --full     adds  -> the instruments re-run, and their artefacts must come back
#                                        BYTE-IDENTICAL to the committed ones (~11 min)
#
# Expected last line, for each tier:
#
#     REPRODUCE: ALL GREEN (10 steps)      # default
#     REPRODUCE: ALL GREEN (13 steps)      # --full
#
# WHAT THE STEPS ARE
#
#   [01]      corpus SHA-256 pins (3 public datasets, re-hashed before every read)
#   [02]-[06] the certificate suites of the five instruments/analysers, each exercised on a HEALTHY
#             and a MUTATED object, so a check that cannot fire is caught rather than trusted
#   [07]      check_one_statistic.py: the package holds ONE rank statistic -- static (no module but
#             canonical.py defines it), dynamic (importers hold it by identity) and plant (a copy
#             must be refused, an import accepted)
#   [08]      make_figures --selftest-title: the title-fitting certificate, plant included
#   [09]      canonical.py --check: every headline number re-derived from the artefacts and asserted
#   [10]      make_figures --check: the statistic the FIGURE prints equals the one the ARTEFACT
#             states -- two independent paths to one number, which byte-identity cannot compare
#
#   --full adds three byte-identity steps:
#   [11]      spike_v3/v4/v5 re-run      -> the three *_results.json must be byte-identical
#   [12]      canonical.py re-run        -> canonical_results.json must be byte-identical
#   [13]      make_figures + build_refs  -> the three PNGs, references.md and manuscript.md must be
#                                           byte-identical
#
# The re-runs are made in place and then RESTORED from a snapshot taken before them, so the package is
# left exactly as committed whether the step passes or fails: a reproduction run must not be a way to
# modify the artefact a reviewer is about to read.
#
# ENVIRONMENT (see README.md): Python 3.9 (/usr/bin/python3) with numpy and scipy -- spike_v3.py imports
# scipy.optimize.milp for the integer-program cross-check, and spike_v4/spike_v5/analyse_v3 reach scipy
# through it; the --full tier's figures step additionally needs matplotlib.  No network is needed: the
# corpora are committed and pinned, and the reference authenticity pass (refscan128.py --verify) is a
# separate, networked step -- the committed pool and its pass log are what this script reads.
#
# THREE VERDICTS, ONE PER STATE: exit 0 = ALL GREEN (every step taken on this build), exit 1 = a
# difference the run MEASURED, exit 2 = a step this build COULD NOT TAKE, with its reason named.  A
# declared dependency that is absent is the third state, never the second: the two dependencies are
# checked and printed at the top, a step whose dependency is missing is reported NOT RUN, and NOT RUN is
# not a pass -- it verified nothing.  This is the difference between "your package is broken" and "your
# interpreter lacks the library the package declares".
# =============================================================================
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || { echo "cannot enter $HERE"; exit 1; }

FULL=0
[ "${1:-}" = "--full" ] && FULL=1
STEPS=0
FAILS=0
NOTRUNS=0
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "reproduce.sh -- issue #128"
echo "working directory: $HERE"

# --- the interpreter: any python3 that can import numpy, printed so the reader knows which one -----
PY="${PY:-}"
if [ -z "$PY" ]; then
    for c in python3 /usr/bin/python3; do
        if command -v "$c" >/dev/null 2>&1 && "$c" -c "import numpy" >/dev/null 2>&1; then PY="$c"; break; fi
    done
fi
if [ -z "$PY" ]; then
    echo "FATAL: no python3 with numpy found; set PY=/path/to/python3" >&2
    exit 1
fi
echo "interpreter: $PY  ($("$PY" -V 2>&1), numpy $("$PY" -c 'import numpy; print(numpy.__version__)' 2>/dev/null))"

# The DECLARED dependencies, read here and printed, because the environment decides which steps this build
# can take at all (README.md -> Environment).  A missing one is NOT RUN -- a coordinate of this run -- and
# never a failure of the package: the two states are one code apart and are not merged (see the header).
declare -a MISSING=()
for m in numpy scipy matplotlib; do
    if ! "$PY" -c "import $m" >/dev/null 2>&1; then MISSING+=("$m"); fi
done
if [ "${#MISSING[@]}" -eq 0 ]; then
    echo "declared deps: numpy scipy matplotlib -- all present"
else
    echo "declared deps: ABSENT -> ${MISSING[*]}"
fi
have() { "$PY" -c "import $1" >/dev/null 2>&1; }

step() {  # step <label> <command...>
    local label="$1"; shift
    STEPS=$((STEPS + 1))
    if "$@" >"$TMP/out" 2>&1; then
        printf '  [%02d] %-52s OK\n' "$STEPS" "$label"
        return 0
    fi
    FAILS=$((FAILS + 1))
    printf '  [%02d] %-52s FAIL\n' "$STEPS" "$label"
    sed 's/^/        /' "$TMP/out" | tail -12
    return 1
}

# notrun <label> <why> -- a step this build cannot take at all.  Not a pass and not a failure: it is
# counted separately and the run exits 2, so a verifier can tell a missing dependency from a broken package.
notrun() {
    STEPS=$((STEPS + 1)); NOTRUNS=$((NOTRUNS + 1))
    printf '  [%02d] %-52s NOT RUN\n' "$STEPS" "$1"
    printf '        %s\n' "$2"
}

# step_dep <label> <module> <command...> -- run the step if its declared dependency is importable,
# otherwise report it NOT RUN with the reason.
step_dep() {
    local label="$1" mod="$2"; shift 2
    if have "$mod"; then step "$label" "$@"
    else notrun "$label" "needs $mod, which is not installed on this interpreter (declared in README.md -> Environment)"; fi
}

# byte <label> <files...> -- the files must be byte-identical to the snapshot taken before the
# re-run, and are RESTORED from that snapshot afterwards (see the header).
snapshot() { local d="$TMP/snap"; mkdir -p "$d"; for f in "$@"; do cp "$f" "$d/"; done; }
byte() {
    local label="$1"; shift
    STEPS=$((STEPS + 1))
    local bad=""
    for f in "$@"; do
        cmp -s "$f" "$TMP/snap/$(basename "$f")" || bad="$bad $f"
    done
    for f in "$@"; do cp "$TMP/snap/$(basename "$f")" "$f"; done     # leave the package as committed
    if [ -z "$bad" ]; then
        printf '  [%02d] %-52s OK\n' "$STEPS" "$label"
    else
        FAILS=$((FAILS + 1))
        printf '  [%02d] %-52s FAIL  (differs:%s)\n' "$STEPS" "$label" "$bad"
    fi
}

snapshot_exists() { [ -f "$TMP/snap/$1" ]; }

echo
echo "== 1. the corpus pins ====================================================="
# `corpus/SHA256SUMS` lists bare file names, so the check runs from INSIDE `corpus/`: a checksum file
# is read against the directory its names are relative to, and running it from the package root asks
# for `winequality-red.csv` beside `manuscript.md`, which is a different (and empty) question.
step "corpus pins (3 datasets, SHA-256)" bash -c 'cd corpus && shasum -a 256 -c SHA256SUMS'

echo
echo "== 2. the certificates (healthy object AND mutated object) ================"
# spike_v4/v5 and analyse_v3 reach scipy through spike_v3, so their certificate step is declared against
# scipy: on an interpreter without it the step is NOT RUN and says so (README.md -> Environment).
step_dep "certificates: spike_v3"    scipy "$PY" spike_v3.py   --selftest
step_dep "certificates: spike_v4"    scipy "$PY" spike_v4.py   --selftest
step_dep "certificates: spike_v5"    scipy "$PY" spike_v5.py   --selftest
step_dep "certificates: analyse_v3"  scipy "$PY" analyse_v3.py --selftest
step "certificates: analyse_v5" "$PY" analyse_v5.py --selftest

# [07] ONE rank statistic (issue #128, correction round): the package held five implementations of one
# statistic and four of them were wrong.  The certificate checks the static form (no copy anywhere, on
# any interpreter), the dynamic form (importers hold canonical.py's object by identity) and a plant.
step "certificates: one rank statistic" "$PY" check_one_statistic.py

# [08] the title-fitting certificate.  Declared against matplotlib because it draws; on an interpreter
# without it the step is NOT RUN and says so, rather than being scored as a defect.
step_dep "certificates: figure titles" matplotlib "$PY" make_figures.py --selftest-title

echo
echo "== 3. the paper's numbers, re-derived and asserted ======================="
step "canonical.py --check" "$PY" canonical.py --check

# [10] the figure's printed number against the artefact that owns it.  Needs matplotlib for the same
# reason, and a writable cache dir, which matplotlib insists on even for a headless Agg run.
export MPLCONFIGDIR="${MPLCONFIGDIR:-$TMP/mpl}"
mkdir -p "$MPLCONFIGDIR"
step_dep "figure vs artefact: the printed statistic" matplotlib "$PY" make_figures.py --check

if [ "$FULL" = "1" ]; then
    echo
    echo "== 4. the artefacts, byte for byte (--full) =============================="

    # [08] the three instruments
    snapshot spike_v3_results.json spike_v4_results.json spike_v5_results.json
    if ! have scipy; then
        notrun "instruments re-run: spike_v3/v4/v5 (3 artefacts)" \
               "needs scipy, which is not installed on this interpreter (declared in README.md -> Environment)"
    else
    ok=1
    for s in spike_v3 spike_v4 spike_v5; do
        "$PY" "$s.py" >"$TMP/out" 2>&1 || ok=0
    done
    if [ $ok -eq 1 ]; then
        byte "instruments re-run: spike_v3/v4/v5 (3 artefacts)" \
             spike_v3_results.json spike_v4_results.json spike_v5_results.json
    else
        STEPS=$((STEPS + 1)); FAILS=$((FAILS + 1))
        printf '  [%02d] %-52s FAIL\n' "$STEPS" "instruments re-run: spike_v3/v4/v5 (3 artefacts)"
        sed 's/^/        /' "$TMP/out" | tail -12
    fi
    fi

    # [09] canonical, re-derived from the (now restored) committed instruments
    snapshot canonical_results.json
    if "$PY" canonical.py >"$TMP/out" 2>&1; then
        byte "canonical re-derived: canonical_results.json" canonical_results.json
    else
        STEPS=$((STEPS + 1)); FAILS=$((FAILS + 1))
        printf '  [%02d] %-52s FAIL\n' "$STEPS" "canonical re-derived: canonical_results.json"
        sed 's/^/        /' "$TMP/out" | tail -12
    fi

    # [10] the figures and the built manuscript
    export MPLCONFIGDIR="${MPLCONFIGDIR:-$TMP/mpl}"
    mkdir -p "$MPLCONFIGDIR"
    snapshot references.md manuscript.md \
           figures/fig1_cost_curves.png figures/fig2_free_width.png figures/fig3_alignment.png
    if ! have matplotlib; then
        notrun "rebuilt: 3 figures + references.md + manuscript.md" \
               "needs matplotlib, which is not installed on this interpreter (declared in README.md -> Environment)"
    else
    ok=1
    "$PY" make_figures.py >"$TMP/out" 2>&1 || ok=0
    "$PY" build_refs.py >"$TMP/out2" 2>&1 || ok=0
    if [ $ok -eq 1 ]; then
        byte "rebuilt: 3 figures + references.md + manuscript.md" \
             references.md manuscript.md \
             figures/fig1_cost_curves.png figures/fig2_free_width.png figures/fig3_alignment.png
    else
        STEPS=$((STEPS + 1)); FAILS=$((FAILS + 1))
        printf '  [%02d] %-52s FAIL\n' "$STEPS" "rebuilt: 3 figures + references.md + manuscript.md"
        { tail -8 "$TMP/out"; tail -8 "$TMP/out2"; } | sed 's/^/        /'
    fi
    fi
fi

echo
if [ "$FAILS" -eq 0 ] && [ "$NOTRUNS" -eq 0 ]; then
    echo "REPRODUCE: ALL GREEN ($STEPS steps)"
    exit 0
fi
if [ "$FAILS" -gt 0 ]; then
    echo "REPRODUCE: $FAILS of $STEPS steps FAILED"
    [ "$NOTRUNS" -gt 0 ] && echo "  (and $NOTRUNS step(s) NOT RUN -- a coordinate of this build, not a finding)"
    exit 1
fi
echo "REPRODUCE: $NOTRUNS of $STEPS steps NOT RUN -- a step this build could not take, not a finding about the package"
exit 2
