#!/usr/bin/env bash
# reproduce.sh -- issue #130, "A Threshold Is Not a Measurement"
#
# WHAT THIS RECOMPUTES (not a checksum check over committed outputs): it re-runs the eleven experiments
# from their own code over the committed corpus and compares each fresh report BYTE-FOR-BYTE against
# the report the package ships, then re-runs the analysis that derives the paper's tables from those
# reports, then runs the determinism certificate's own battery. Every number in the manuscript is read
# off one of these artefacts.
#
# RUN IT FROM THE PACKAGE DIRECTORY:   cd papers/issue-130 && bash reproduce.sh
# ENVIRONMENT: CPython 3.9+ (measured on 3.9.6 and 3.13.9, macOS; the eleven reports are byte-identical
#   on both) -- the instruments are pure standard library plus `math`/`random`/`hashlib`; NO third-party
#   dependency is imported, so there is no library version whose arithmetic enters a comparison. The
#   reductions are `math.fsum`, which is exactly rounded in every CPython, so the reported means and sd
#   do not move with the build (the builtin `sum()` was Neumaier-compensated in 3.12, which did move
#   them -- see spike_v8.py's `mean_sd`). Override the interpreter with PYTHON=/path/to/python3.
#   THE REFERENCE GATE IS THE ONE EXCEPTION: `.github/tools/refgate.py` is journal infrastructure and
#   needs CPython >= 3.12 (its f-strings carry backslashes). It therefore takes its OWN interpreter,
#   selected by `GATE_PYTHON` (default: the first of python3.13 / python3.12 / python3 that reports
#   >= 3.12); with none reachable that step prints NOT RUN and the rest of the run is unaffected.
# INPUTS: corpus/pg*.txt, committed in the package (8 Project Gutenberg texts, 5.6 MB), verified against
#   corpus/SHA256SUMS at the start of every run. corpus/fetch_corpus.sh re-obtains them from the network;
#   it is NOT needed to reproduce, and this run never touches the network.
# TOLERANCE: exact -- the comparison is sha256 equality against the shipped reports. (A second machine
#   under another build of the same interpreter can differ in set-iteration order or rounding; that is
#   what the value is, so it is stated rather than widened.)
# WHAT IT WRITES: nothing inside the package. The instruments emit their reports into a private temp
#   directory this script creates and removes. (`spike_v7.py` reads the package's
#   `spike_v4_results.json` on purpose -- its certificate X1 asserts its pools ARE that report's pools.)
# COST: about 5.5 minutes (the eleven instruments x2 -- they are compared, then spike_v8 is re-run for
#   its own certificate battery; spike_v4 ~95 s, spike_v5 ~89 s, spike_v8 ~50 s x2; the figures add
#   under a second -- they are drawn from the shipped reports, not measured.)
#
# SECOND TIER (opt-in, about 13 minutes more):  REPRO_FULL=1 bash reproduce.sh
#   runs repro_check.py again, which re-runs every instrument TWICE in separate processes and compares the two
#   artefacts -- the determinism certificate. It rewrites `artefact_hashes.json` in place (the one file
#   this package's run may write); the last step then compares the regenerated table against the shipped
#   one and restores the shipped copy, so the committed file is what stays on disk.

set -u
PY="${PYTHON:-python3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/issue130-repro.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
FAILED=0

say()  { printf '%-14s %s\n' "$1" "$2"; }
bad()  { printf '%-14s FAILED -- %s\n' "$1" "$2"; FAILED=$((FAILED+1)); }
run()  { local s="$1"; shift; ( cd "$WORK" && "$PY" "$HERE/$s" "$@" ); }
need() { if printf '%s' "$2" | grep -qE "$3"; then say "$1" "$4"; else bad "$1" "$4 (expected /$3/)"; fi; }

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "== #130 reproduction =="

# ---- 0. the build -----------------------------------------------------------------------------------------
BUILD=$("$PY" -c 'import sys;print(sys.executable, sys.version.split()[0])' 2>/dev/null) \
  || { echo "no interpreter at '$PY' -- set PYTHON=/path/to/python3"; exit 2; }
say "build" "$BUILD | stdlib only (no third-party import anywhere in the package)"

# ---- 1. the corpus is the pinned one ----------------------------------------------------------------------
if command -v shasum >/dev/null 2>&1; then SUMS=$(cd corpus && shasum -a 256 -c SHA256SUMS 2>&1); else
  SUMS=$(cd corpus && sha256sum -c SHA256SUMS 2>&1); fi
NOK=$(printf '%s' "$SUMS" | grep -c 'OK$'); NFAIL=$(printf '%s' "$SUMS" | grep -c 'FAILED')
if [ "$NOK" = "8" ] && [ "$NFAIL" = "0" ]; then say "corpus" "8 file(s) verified against corpus/SHA256SUMS"
else bad "corpus" "$NOK file(s) OK, $NFAIL FAILED -- the pinned corpus is not the one this package was measured on"; fi

# ---- 2. the ten instruments reproduce the shipped reports -------------------------------------------------
NM=0; NT=0
for name in spike_v0 spike_v1 spike_v2 spike_v3 spike_v4 spike_v5 spike_v6 spike_v7 spike_v8 floor_v2 floor_v3; do
  NT=$((NT+1))
  if ! run "$name.py" > "$WORK/$name.stdout" 2>&1; then
    bad "instruments" "$name.py exited non-zero -- $(tail -1 "$WORK/$name.stdout")"; continue
  fi
  GOT=$("$PY" -c 'import hashlib,sys,io;print(hashlib.sha256(io.open(sys.argv[1],"rb").read()).hexdigest())' "$WORK/${name}_results.json")
  WANT=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["instrument_hashes"][sys.argv[2]]["sha256"])' artefact_hashes.json "$name")
  if [ "$GOT" = "$WANT" ]; then NM=$((NM+1)); printf '  %-9s MATCH  %s\n' "$name" "$(printf '%s' "$GOT" | cut -c1-16)"
  else bad "instruments" "$name produced $(printf '%s' "$GOT" | cut -c1-16) but the package ships $(printf '%s' "$WANT" | cut -c1-16)"; fi
done
if [ "$NM" = "11" ] && [ "$NT" = "11" ]; then say "instruments" "$NM of $NT reports re-run byte-identically"; else bad "instruments" "$NM of $NT reports matched"; fi

# ---- 3. the analysis, and its certificate -----------------------------------------------------------------
A2=$(run analyse_v2.py); rc=$?
if [ "$rc" != "0" ]; then bad "analysis" "analyse_v2.py exited $rc"; else
  NTB=$(printf '%s' "$A2" | grep -c '^TABLE ')
  need analysis "$A2" "^TABLE 1 -- the null population is LENGTH-DEPENDENT" "re-derived its tables ($NTB of 6 printed)"
  need analysis "$A2" "certificate: 21 cells, worst \|diff\| = 0.035" "the mechanism certificate (predicted vs measured eps*)"
  need analysis "$A2" "dice2c  rate   slope=-0.230  \(n=7, R2=0.950\)" "the boundary power law (slope -0.230, R2 0.950)"
fi

# ---- 3b. the figures re-generate byte-for-byte ----------------------------------------------------------
# make_figures.py reads the SHIPPED reports and writes SVG; nothing here is typed into a figure, so the
# check is the same one the instruments get: regenerate and compare bytes.
FIG=$(run make_figures.py "$WORK/figures" 2>&1); rc=$?
if [ "$rc" != "0" ]; then bad "figures" "make_figures.py exited $rc -- $(printf '%s' "$FIG" | tail -1)"; else
  NF=0; NFT=0
  for f in figures/*.svg figures/manifest.json figures/CAPTIONS.md; do
    NFT=$((NFT+1))
    if cmp -s "$f" "$WORK/$f"; then NF=$((NF+1)); else bad "figures" "$(basename "$f") differs from the shipped figure"; fi
  done
  if [ "$NF" = "$NFT" ]; then say "figures" "$NF of $NFT figure file(s) re-generated byte-identically"
  else bad "figures" "$NF of $NFT figure file(s) matched"; fi
  FS=$(run make_figures.py --selftest); rc=$?
  if [ "$rc" != "0" ]; then bad "figures" "make_figures.py --selftest exited $rc"; else
    need figures "$FS" "F4 every drawn element lies inside its canvas" "the canvas-bounds check (no clipped label)"
    need figures "$FS" "F4b the bounds check CATCHES a planted out-of-canvas element" "and its plant (the check can fail)"
    need figures "$FS" "SELFTEST ALL PASS" "the figure certificate battery (F1-F4b)"
  fi
fi

# ---- 4. the determinism certificate can fail --------------------------------------------------------------
RS=$(run repro_check.py --selftest); rc=$?
if [ "$rc" != "0" ]; then bad "certificate" "repro_check.py --selftest exited $rc"; else
  need certificate "$RS" "P1 identical objects -> PASS" "plant 1: identical objects must NOT fire"
  need certificate "$RS" "P2 one byte differs -> FAIL" "plant 2: a one-byte change MUST fire"
  need certificate "$RS" "P3 hash\(str\)-seeded processes -> FAIL" "plant 3: the real cross-process defect MUST fire"
fi

# ---- 5. the stratum-weights certificate (host rant item 13) ------------------------------------------------
W8=$(run spike_v8.py --selftest); rc=$?
if [ "$rc" != "0" ]; then bad "stratum" "spike_v8.py --selftest exited $rc"; else
  need stratum "$W8" "W1 the uniform reweighting IS the identity .*PASS" "the repair is the identity when there is nothing to fix"
  need stratum "$W8" "the reweighted read returns to alpha\+-0.05 in [0-9]+ of [0-9]+ LIVE" "the repair restores alpha on every live cell"
  need stratum "$W8" "on the PLANT      W3\(b\) flags [0-9]+ of the [0-9]+ MATERIAL" "the plant fires on the material cells"
  need stratum "$W8" "on the REAL data  W3\(b\) flags 0 of the" "and does NOT fire on the real data"
  need stratum "$W8" "SELFTEST ALL PASS" "the certificate battery"
fi

# ---- 6. opt-in: the two-run determinism certificate --------------------------------------------------------
if [ "${REPRO_FULL:-0}" = "1" ]; then
  cp artefact_hashes.json "$WORK/shipped_hashes.json"
  RF=$(run repro_check.py); rc=$?
  if [ "$rc" != "0" ]; then bad "determinism" "repro_check.py exited $rc"; else
    need determinism "$RF" "DETERMINISM CERTIFICATE: ALL PASS  \(11/11" "11 of 11 instruments reproduce byte-for-byte over two runs"
  fi
  if "$PY" -c 'import json,sys
a=json.load(open(sys.argv[1]))["instrument_hashes"]; b=json.load(open(sys.argv[2]))["instrument_hashes"]
sys.exit(0 if a==b else 1)' artefact_hashes.json "$WORK/shipped_hashes.json"; then
    say determinism "the regenerated table equals the shipped artefact_hashes.json"
  else bad "determinism" "the regenerated artefact_hashes.json differs from the shipped one"; fi
  cp "$WORK/shipped_hashes.json" artefact_hashes.json   # leave the committed file as committed
else
  say "determinism" "skipped -- REPRO_FULL=1 adds the two-run certificate (~13 min)"
fi

# ---- 7. the manuscript: re-render and compare, then gate it --------------------------------------------
# The build resolves every number from the shipped reports and every citation from the verified pool,
# and writes nothing (it renders into memory and compares against the committed manuscript.md).  The
# reference gate is run from the REPOSITORY ROOT, the path the spec names, over this package's manuscript.
MS=$(run build_manuscript.py --check); rc=$?
if [ "$rc" != "0" ]; then bad "manuscript" "build_manuscript.py --check exited $rc"; else
  need manuscript "$MS" "MANUSCRIPT: MATCH" "the manuscript is exactly what the build renders from the reports"
fi
RC=$(run make_reference_check.py --check); rc=$?
if [ "$rc" != "0" ]; then bad "manuscript" "make_reference_check.py --check exited $rc"; else
  need manuscript "$RC" "REFERENCE-CHECK: MATCH" "and the citation report is exactly what it renders"
fi
BS=$(run build_manuscript.py --selftest); rc=$?
if [ "$rc" != "0" ]; then bad "manuscript" "build_manuscript.py --selftest exited $rc"; else
  need manuscript "$BS" "SELFTEST: ALL PLANTS CAUGHT" "the build's own plants: an unowned number, a bad path, an off-pool citation"
fi
if [ -f "../..//.github/tools/refgate.py" ] || [ -f "$ROOT/.github/tools/refgate.py" ]; then
  # The gate is JOURNAL INFRASTRUCTURE and needs an interpreter the package's own build is not: its
  # f-strings carry backslashes, a SyntaxError before CPython 3.12.  It therefore takes its OWN
  # interpreter (the same convention `papers/issue-126/reproduce.sh` uses), so that the one command a
  # verifier runs matches the environment the README names -- the package's `$PY` is not required to
  # be the gate's.  `GATE_PYTHON` overrides; if no >= 3.12 interpreter is reachable, the step reports
  # NOT RUN naming the window it could not read -- never a verdict for a check that did not run.
  GP=""
  for c in "${GATE_PYTHON:-}" python3.13 python3.12 python3; do
    [ -n "$c" ] || continue
    command -v "$c" >/dev/null 2>&1 || continue
    if "$c" -c 'import sys;raise SystemExit(0 if sys.version_info>=(3,12) else 1)' 2>/dev/null; then GP="$c"; break; fi
  done
  if [ -n "$GP" ]; then
    RG=$(cd "$ROOT" && "$GP" .github/tools/refgate.py papers/issue-130/manuscript.md 2>&1)
    need manuscript "$RG" "GATE: PASS" "refgate (via $GP): >=100 entries, every one cited in the body, one entry per paragraph"
    echo "$RG" | grep -E "entries=|coverage=" | sed 's/^/  refgate  /'
  else
    say manuscript "refgate NOT RUN -- no interpreter >= 3.12 on this host (the gate's f-strings carry backslashes); set GATE_PYTHON=<path>, or read the gate's recorded output in reference-check.md"
  fi
else
  say manuscript "refgate skipped -- run from a checkout of this journal (the tool lives in .github/tools/)"
fi

echo
if [ "$FAILED" = "0" ]; then echo "REPRODUCE: ALL GREEN"; exit 0; fi
echo "REPRODUCE: $FAILED CHECK(S) FAILED"; exit 1
