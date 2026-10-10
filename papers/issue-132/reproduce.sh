#!/usr/bin/env bash
# reproduce.sh -- issue #132, "The Frame Is a Level"
#
# WHAT THIS RECOMPUTES (not a checksum check over committed outputs): it re-runs the FOUR
# experiments from their own code over the committed, SHA256-pinned corpus and compares each fresh
# report BYTE-FOR-BYTE against the report this package ships, then runs each instrument's own plant
# battery.  Every number in the manuscript is read off one of these reports.
#
# RUN IT FROM THE PACKAGE DIRECTORY:   cd papers/issue-132 && bash reproduce.sh
# ENVIRONMENT: CPython 3 (measured on 3.9.6 and 3.13.9, macOS) -- the instruments are pure standard
#   library (`hashlib`/`json`/`os`/`random`/`re`/`sys`); NO third-party dependency is imported, so no
#   library version enters a comparison. Override the interpreter with PYTHON=/path/to/python3.
# INPUTS: corpus/pg*.txt (8 English) and corpus_i18n/pg*_<lang>.txt (12 non-English), both committed
#   in the package, each verified against its own SHA256SUMS at the start of every run. The corpus
#   fetch scripts re-obtain them from the network; they are NOT needed to reproduce, and this run
#   never touches the network.
# TOLERANCE: exact -- the comparison is sha256 equality against the shipped reports.
# WHAT IT WRITES: nothing inside the package. Each instrument is run with SPIKE_OUT pointing into a
#   private temp directory this script creates and removes.
# COST: about 25 seconds (four instruments, each re-run once).
#
# SECOND TIER (opt-in):  REPRO_FULL=1 bash reproduce.sh
#   re-runs every instrument a SECOND time in a fresh process and compares the two fresh artefacts,
#   then asserts both equal the shipped report -- the determinism certificate.

set -u
PY="${PYTHON:-python3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/issue132-repro.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
FAILED=0

say()  { printf '%-16s %s\n' "$1" "$2"; }
bad()  { printf '%-16s FAILED -- %s\n' "$1" "$2"; FAILED=$((FAILED+1)); }

echo "== #132 reproduction =="

# ---- 0. the build ------------------------------------------------------------------------------
BUILD=$("$PY" -c 'import sys;print(sys.executable, sys.version.split()[0])' 2>/dev/null) \
  || { echo "no interpreter at '$PY' -- set PYTHON=/path/to/python3"; exit 2; }
say "build" "$BUILD | stdlib only (no third-party import anywhere in the package)"

# ---- 1. both corpora are the pinned ones -------------------------------------------------------
for d in corpus corpus_i18n; do
  if command -v shasum >/dev/null 2>&1; then SUMS=$(cd "$d" && shasum -a 256 -c SHA256SUMS 2>&1); else
    SUMS=$(cd "$d" && sha256sum -c SHA256SUMS 2>&1); fi
  NOK=$(printf '%s' "$SUMS" | grep -c 'OK$'); NFAIL=$(printf '%s' "$SUMS" | grep -c 'FAILED')
  WANT=$(grep -c . "$d/SHA256SUMS")
  if [ "$NOK" = "$WANT" ] && [ "$NFAIL" = "0" ]; then
    say "corpus" "$d: $NOK file(s) verified against $d/SHA256SUMS"
  else
    bad "corpus" "$d: $NOK/$WANT OK, $NFAIL FAILED -- not the corpus this package was measured on"
  fi
done

# ---- 2. each instrument: plants, then a byte-for-byte reproduction -----------------------------
for n in 0 1 2 3; do
  S="spike_v${n}.py"; R="spike_v${n}_results.json"
  # plants first: they must fail loudly rather than pass silently
  if OUT=$("$PY" "$HERE/$S" --selftest 2>&1); then
    say "$S selftest" "$(printf '%s' "$OUT" | tail -1)"
  else
    bad "$S selftest" "the plant battery failed"
  fi
  # the report: written into $WORK, compared against the shipped one
  ( cd "$WORK" && SPIKE_OUT="$WORK/$R" "$PY" "$HERE/$S" >/dev/null 2>&1 ) \
    || { bad "$S run" "the instrument did not complete"; continue; }
  if cmp -s "$WORK/$R" "$HERE/$R"; then
    say "$S report" "byte-identical to the shipped $R ($(shasum -a 256 "$HERE/$R" | cut -c1-16))"
  else
    bad "$S report" "$R differs from the shipped report"
  fi
done

# ---- 2b. the reference layer: OFFLINE gate (the live verification is a separate, documented pass) --
if [ -f refscan132.py ] && [ -f refs/pool.json ]; then
  if OUT=$("$PY" "$HERE/refscan132.py" --gate 2>&1); then
    say "references" "$(printf '%s' "$OUT" | tail -1) -- live verification is in reference-check.md"
  else
    bad "references" "the offline reference pool gate failed"
  fi
fi

# ---- 3. the figures: re-generate and compare byte-for-byte -------------------------------------
if [ -f make_figures.py ]; then
  if OUT=$("$PY" "$HERE/make_figures.py" --selftest 2>&1); then
    say "make_figures" "$(printf '%s' "$OUT" | tail -1)"
  else
    bad "make_figures" "the figure certificate failed"
  fi
  mkdir -p "$WORK/figures"
  ( cd "$WORK" && "$PY" "$HERE/make_figures.py" "$WORK/figures" >/dev/null 2>&1 )
  DIFF=0
  for f in fig1_dilution_law.svg fig2_level_ladder.svg fig3_critical_share.svg            fig4_r_boundary.svg fig5_eligible_rate.svg CAPTIONS.md manifest.json; do
    cmp -s "$WORK/figures/$f" "$HERE/figures/$f" || { DIFF=$((DIFF+1)); }
  done
  if [ "$DIFF" = "0" ]; then say "figures" "7 of 7 regenerated byte-identically"
  else bad "figures" "$DIFF of 7 differ from the shipped set"; fi
fi

# ---- 4. the manuscript: re-render and compare, then gate it ------------------------------------
# build_manuscript.py resolves every number out of the reports and every citation out of the
# verified pool, and writes NOTHING (it renders into memory and compares against the committed
# manuscript.md).  Its own plants must fire.  The JOURNAL reference gate is `.github/tools/refgate.py`
# -- editor-side infrastructure that is not part of this package -- so it is read from the repository
# root when present and reported as a named NOT RUN when this is not a checkout of the journal.
if [ -f build_manuscript.py ] && [ -f manuscript.md ]; then
  if OUT=$("$PY" "$HERE/build_manuscript.py" --check 2>&1); then
    say "manuscript" "$(printf '%s' "$OUT" | tail -1)"
  else
    bad "manuscript" "$(printf '%s' "$OUT" | tail -1)"
  fi
  if OUT=$("$PY" "$HERE/build_manuscript.py" --selftest 2>&1); then
    say "build plants" "$(printf '%s' "$OUT" | tail -1)"
  else
    bad "build plants" "$(printf '%s' "$OUT" | tail -1)"
  fi
  if OUT=$("$PY" "$HERE/make_reference_check.py" --check 2>&1); then
    say "reference-check" "$(printf '%s' "$OUT" | tail -1)"
  else
    bad "reference-check" "$(printf '%s' "$OUT" | tail -1)"
  fi
  ROOT="$(cd "$HERE/../.." && pwd)"
  RG="$ROOT/.github/tools/refgate.py"
  if [ -f "$RG" ]; then
    # The gate is editor-side tooling and its f-strings carry backslashes, so it needs >= 3.12
    # independently of the package's own build.  GATE_PYTHON overrides; with no reachable >= 3.12
    # the step reports a NAMED NOT RUN rather than a pass.
    GP=""
    for c in "${GATE_PYTHON:-}" python3.13 python3.12 python3; do
      [ -n "$c" ] || continue
      command -v "$c" >/dev/null 2>&1 || continue
      v=$("$c" -c 'import sys;print(sys.version_info>=(3,12))' 2>/dev/null) || continue
      [ "$v" = "True" ] && { GP="$c"; break; }
    done
    if [ -n "$GP" ]; then
      if OUT=$(cd "$ROOT" && "$GP" .github/tools/refgate.py "papers/issue-132/manuscript.md" 2>&1); then
        say "refgate" "$(printf '%s' "$OUT" | grep -E 'entries=|coverage=' | tr '\n' ' ')"
      else
        bad "refgate" "the reference gate failed ($GP)"
      fi
    else
      say "refgate" "NOT RUN -- no interpreter >= 3.12 on this host; set GATE_PYTHON=<path>"
    fi
  else
    say "refgate" "NOT RUN -- the tool lives in .github/tools/ of the journal repo"
  fi
fi

# ---- 5. optional second tier: the determinism certificate --------------------------------------
if [ "${REPRO_FULL:-0}" = "1" ]; then
  echo "-- second tier: determinism (two fresh runs per instrument) --"
  for n in 0 1 2 3; do
    S="spike_v${n}.py"; R="spike_v${n}_results.json"
    ( cd "$WORK" && SPIKE_OUT="$WORK/a_$R" "$PY" "$HERE/$S" >/dev/null 2>&1 )
    ( cd "$WORK" && SPIKE_OUT="$WORK/b_$R" "$PY" "$HERE/$S" >/dev/null 2>&1 )
    if cmp -s "$WORK/a_$R" "$WORK/b_$R" && cmp -s "$WORK/a_$R" "$HERE/$R"; then
      say "$S det" "two fresh runs identical, and equal to the shipped report"
    else
      bad "$S det" "the two fresh runs differ, or differ from the shipped report"
    fi
  done
fi

echo
if [ "$FAILED" = "0" ]; then echo "REPRODUCE: ALL GREEN"; else echo "REPRODUCE: $FAILED CHECK(S) FAILED"; fi
exit $(( FAILED > 0 ))
