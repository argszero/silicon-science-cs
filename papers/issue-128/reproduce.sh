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
#     REPRODUCE: ALL GREEN (7 steps)      # default
#     REPRODUCE: ALL GREEN (10 steps)     # --full
#
# WHAT THE STEPS ARE
#
#   [01]      corpus SHA-256 pins (3 public datasets, re-hashed before every read)
#   [02]-[06] the certificate suites of the five instruments/analysers, each exercised on a HEALTHY
#             and a MUTATED object, so a check that cannot fire is caught rather than trusted
#   [07]      canonical.py --check: every headline number re-derived from the artefacts and asserted
#
#   --full adds three byte-identity steps:
#   [08]      spike_v3/v4/v5 re-run      -> the three *_results.json must be byte-identical
#   [09]      canonical.py re-run        -> canonical_results.json must be byte-identical
#   [10]      make_figures + build_refs  -> the three PNGs, references.md and manuscript.md must be
#                                           byte-identical
#
# The re-runs are made in place and then RESTORED from a snapshot taken before them, so the package is
# left exactly as committed whether the step passes or fails: a reproduction run must not be a way to
# modify the artefact a reviewer is about to read.
#
# ENVIRONMENT (see README.md): Python 3.9 (/usr/bin/python3) with numpy; the --full tier's figures
# step additionally needs matplotlib.  No network is needed: the corpora are committed and pinned, and
# the reference authenticity pass (refscan128.py --verify) is a separate, networked step -- the
# committed pool and its pass log are what this script reads.
# =============================================================================
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || { echo "cannot enter $HERE"; exit 1; }

FULL=0
[ "${1:-}" = "--full" ] && FULL=1
STEPS=0
FAILS=0
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
for s in spike_v3 spike_v4 spike_v5 analyse_v3 analyse_v5; do
    step "certificates: $s" "$PY" "$s.py" --selftest
done

echo
echo "== 3. the paper's numbers, re-derived and asserted ======================="
step "canonical.py --check" "$PY" canonical.py --check

if [ "$FULL" = "1" ]; then
    echo
    echo "== 4. the artefacts, byte for byte (--full) =============================="

    # [08] the three instruments
    snapshot spike_v3_results.json spike_v4_results.json spike_v5_results.json
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

echo
if [ "$FAILS" -eq 0 ]; then
    echo "REPRODUCE: ALL GREEN ($STEPS steps)"
    exit 0
fi
echo "REPRODUCE: $FAILS of $STEPS steps FAILED"
exit 1
