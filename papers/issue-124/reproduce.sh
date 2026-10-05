#!/usr/bin/env bash
# =============================================================================
# One-command reproduction for issue #124
#
#   "How Many Runs Does a Claim Need? The Repeat-Count Law of Stochastic
#    Evaluation, and the Item-Repeat Budget Boundary"
#
# WORKING DIRECTORY: this script cd's to its own directory, the package root:
#
#     papers/issue-124/
#
# and every path it prints is relative to that directory.
#
# What it does, in order:
#
#   1. rebuild the manuscript from its sources and the committed artefacts
#        make_differences.py    each entry's one-line stated Difference, derived from the
#                               manuscript's own related-work clustering
#        build_manuscript.py    resolves every {{number}} out of the artefacts and every
#                               {ref:key} out of the verified pool; refuses to build on drift
#                               (+ its own plant control)
#   2. recompute the five artefacts from the instruments
#        spike_v0.py            the exact repeat-count law E(N,p,rule) by TWO routes, the
#                               Monte-Carlo agreement, the located estimate/decide crossover
#                               and the rule family (majority-strict/opt, unanimity, any-of, mean)
#        spike_v1.py            the item-repeat budget: N*, Var*B, the continuous vs discrete
#                               boundary (N*=1 vs sqrt(2)) and its domain
#        spike_v2.py            the MEASURED-input arm: p, sigma^2, tau^2 read from a real
#                               stochastic optimisation, the u=0 hygiene fix, the conditional
#                               crossing (solved, not gridded) and the mixture criterion (ii)
#        spike_v3.py            the item-SIZE axis: tau^2(T)=c_tau/T and sigma^2(T)=a+b/T over a
#                               128x span, with the interior optimum (T*, N*)
#        spike_v4_grounding.py  real UCI Concrete Compressive Strength (pinned csv, sha256
#                               checked): the same laws on foreign data and the FLAT-p refutation
#      then the manuscript is rebuilt ON the recomputed artefacts (the build reads them)
#   3. regenerate the six figures from those artefacts            (make_figures.py)
#   4. validate the manuscript's claims against the artefacts     (validate.py)
#   5. two-sided control on that validator itself                 (validate.py --selftest)
#   6. the core instrument's own plant harness                    (plant124.py)
#   7. regenerate and gate the citation-authenticity report       (make_reference_check.py)
#
# Expected output is stated in README.md.  The verdicts a verifier compares are:
#
#     VALIDATE 46/46
#     RESULT: PASS
#     SELFTEST: ALL PLANTS CAUGHT
#     SELF-AUDIT: ALL PLANTS CAUGHT
#
# plus, on the full tier, one `wrote <name>_results.json` line per instrument.
#
# TOLERANCE: exact, not statistical.  validate.py prints an integer count of checks that passed
# out of the number it ran; every one of the 46 must pass, and each is attached to a specific
# claim in manuscript.md (the check labels name the section).  A single failed check fails the run.
# The artefacts must also come back BYTE-IDENTICAL across two runs (the instruments are seeded).
# The two-way contract is: this script passes on a fresh checkout, and it passes again on the same
# checkout immediately afterwards (it rewrites only the artefacts and figures it owns).
#
# Environment:
#   EMRG_PYTHON       interpreter for the instruments and the validator.  CPython >= 3.8 with
#                     **numpy and scipy** (spike_v0 uses scipy.stats.binom.sf as one of its two
#                     independent exact routes; spike_v2/v3/v4 use numpy).  Verified on
#                     /usr/bin/python3 3.9.6 with numpy 2.0.2, scipy 1.13.1.
#   EMRG_FIG_PYTHON   interpreter with matplotlib, for step 2 only (3.9.4 here).
#   REPRODUCE_QUICK=1 skip step 2's recompute and validate the artefacts as committed (~20 s).
#
# The build that produced the committed artefacts is recorded in README.md; the verdicts below are
# a claim about THAT build.  A second scientific interpreter was not available on the authoring
# host, so a cross-build byte-identity check was NOT performed -- stated, not silently omitted.
#
# Measured wall-clock on the authoring machine (Apple silicon, /usr/bin/python3 3.9.6):
#   full (build + recompute + figures + validate + plants):  ~95 s
#   quick (build + figures + validate + plants):              ~25 s
# =============================================================================
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || { echo "cannot enter $HERE"; exit 1; }

echo "reproduce.sh -- issue #124 reproduction"
echo "working directory: $HERE"

QUICK="${REPRODUCE_QUICK:-0}"
START="$(date +%s)"

has_mod() { "$1" -c "import $2" >/dev/null 2>&1; }

pick_with() {  # pick_with "<modules>" <candidate...> -- first candidate that imports them all
    mods="$1"; shift
    for c in "$@"; do
        [ -n "$c" ] || continue
        command -v "$c" >/dev/null 2>&1 || continue
        ok=1
        for m in $mods; do has_mod "$c" "$m" || { ok=0; break; }; done
        [ "$ok" = "1" ] && { echo "$c"; return 0; }
    done
    return 1
}

PY="$(pick_with "numpy scipy" "${EMRG_PYTHON:-}" /usr/bin/python3 python3 /opt/homebrew/bin/python3 || true)"
if [ -z "$PY" ]; then
    echo "FATAL: no python3 with numpy+scipy found; set EMRG_PYTHON" >&2
    exit 1
fi
PY_FIG="$(pick_with "matplotlib numpy" "${EMRG_FIG_PYTHON:-}" "$PY" /usr/bin/python3 python3 || true)"

# matplotlib wants a writable cache directory; on a host whose default (~/.matplotlib) is not
# writable it otherwise emits a warning and falls back anyway.  The cache holds fonts only, so this
# does not affect the figure bytes.
export MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/emrg_mpl_cache}"

echo "interpreter (instruments): ${PY}"
echo "interpreter (matplotlib):  ${PY_FIG:-none found}"
echo "python version:            $("$PY" -V 2>&1)"
echo "numpy / scipy:             $("$PY" -c 'import numpy,scipy;print(numpy.__version__,"/",scipy.__version__)' 2>&1)"
[ -n "$PY_FIG" ] && echo "matplotlib:                $("$PY_FIG" -c 'import matplotlib;print(matplotlib.__version__)' 2>&1 | tail -1)"
[ "$QUICK" = "1" ] && echo "mode: QUICK -- validating the committed artefacts without recomputing"

RUNLOG="run.log"
: > "$RUNLOG"
{
    echo "# issue #124 reproduction run"
    echo "# interpreter:    $PY  ($("$PY" -V 2>&1))"
    echo "# matplotlib:     ${PY_FIG:-none}"
    echo "# mode:           $([ "$QUICK" = "1" ] && echo quick || echo full)"
    echo "#"
} >> "$RUNLOG"

step() {  # step <label> <command...>
    label="$1"; shift
    t0="$(date +%s)"
    if "$@" >> "$RUNLOG" 2>&1; then
        echo "   $(printf '%-34s' "$label") ok   $(( $(date +%s) - t0 )) s"
    else
        echo "   $(printf '%-34s' "$label") FAIL $(( $(date +%s) - t0 )) s" >&2
        tail -25 "$RUNLOG" >&2
        exit 1
    fi
}

# ----------------------------------------------------------------- step 1: the manuscript
echo
echo "== 1. the manuscript, rebuilt from its sources and the committed artefacts =="
# make_differences.py derives every entry's stated Difference from the manuscript's own related-work
# clustering; build_manuscript.py resolves every {{number}} out of the artefacts and every {ref:key}
# out of the verified pool, and refuses to build on drift.  Its own plant control runs beside it.
step "make_differences.py" "$PY" make_differences.py
tail -2 "$RUNLOG"
step "build_manuscript.py" "$PY" build_manuscript.py
tail -3 "$RUNLOG"
step "build_manuscript.py --selftest" "$PY" build_manuscript.py --selftest
tail -1 "$RUNLOG"

# ----------------------------------------------------------------- step 2: instruments
if [ "$QUICK" != "1" ]; then
    echo
    echo "== 2. instruments =========================================================="
    for s in spike_v0 spike_v1 spike_v2 spike_v3 spike_v4_grounding; do
        step "$s.py" "$PY" "$s.py"
        tail -1 "$RUNLOG"
    done
    # the build reads the artefacts, so it runs a second time now that they have been recomputed
    step "rebuild the manuscript on the new artefacts" "$PY" build_manuscript.py
fi

# ----------------------------------------------------------------- step 3: figures
echo
echo "== 3. figures ============================================================="
if [ -n "$PY_FIG" ]; then
    step "make_figures.py" "$PY_FIG" make_figures.py
    sed -n '/figures from the committed/,$p' "$RUNLOG" | sed 's/^/   /' | tail -7
else
    echo "SKIP: no matplotlib interpreter found (figures left as committed; this is stated, not"
    echo "      silently treated as a pass -- the manifest check in step 4 still reads them)"
fi

# ----------------------------------------------------------------- step 4: validation
echo
echo "== 4. validation of the manuscript's claims ================================"
"$PY" validate.py || { echo "FATAL: validation failed" >&2; exit 1; }
"$PY" validate.py >> "$RUNLOG" 2>&1

# ----------------------------------------------------------------- step 5: the suite's own control
echo
echo "== 5. two-sided control on the validation suite itself ===================="
"$PY" validate.py --selftest || { echo "FATAL: the suite's plant control did not fire" >&2; exit 1; }
"$PY" validate.py --selftest >> "$RUNLOG" 2>&1

# ----------------------------------------------------------------- step 6: the instrument's plant harness
echo
echo "== 6. plant harness on the core instrument (spike_v0) ======================"
"$PY" plant124.py || { echo "FATAL: the instrument's plant harness did not fire" >&2; exit 1; }
"$PY" plant124.py >> "$RUNLOG" 2>&1

# ----------------------------------------------------------------- step 7: reference layer
echo
echo "== 7. reference layer (regenerate and gate the authenticity report) ========"
# make_reference_check.py REFUSES to report a pass when a cited key has no live verification result
# or a verdict other than VERIFIED, so the report is a gate and not decoration.  It is offline: it
# reads the committed manuscript, the verified pool and the verification results.
step "make_reference_check.py" "$PY" make_reference_check.py
tail -1 "$RUNLOG"
echo "committed report: reference-check.md ($(grep -c '^| [0-9]' reference-check.md) cited entries)"
echo "NOTE: re-checking the citations against the LIVE external records re-fetches every identifier"
echo "      from arXiv/Crossref and needs network reachability; run it when the network allows:"
echo "          python3 verify_citations.py       # -> citation-verification.json (108/108 VERIFIED)"
echo "      On a host where arXiv's API endpoint is unreachable this step cannot run; the committed"
echo "      report is the record of the run that was performed, and step 7 gates it."
echo "      Rebuilding the pool itself is likewise network-gated: refscan124.py [--curate]."

END="$(date +%s)"
{
    echo "#"
    echo "# wall-clock: $((END - START)) s"
    echo "RESULT: PASS"
} >> "$RUNLOG"
echo
echo "wall-clock: $((END - START)) s"
echo "RESULT: PASS"
