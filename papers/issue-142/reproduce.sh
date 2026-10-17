#!/usr/bin/env bash
# reproduce.sh -- issue #142, "The Knob Is Not the Curve"
#
# WHAT THIS RECOMPUTES (not a checksum check over committed outputs): it re-runs each research
# instrument from its own code in an ISOLATED COPY of the package and compares the fresh report
# BYTE-FOR-BYTE against the report this package ships; it runs each instrument's own plant battery
# and reads the VERDICT LINE it prints; it regenerates the FIGURE SET and compares the PNGs
# byte-for-byte; and it re-checks the REFERENCE LAYER offline (the pool gate binds the committed
# verification receipt to the shipped pool by sha256) and the MANUSCRIPT build.  Every number the
# manuscript prints is read off one of these reports, every figure from them, and every reference
# from the verified pool.
#
# RUN IT FROM THE PACKAGE DIRECTORY:   cd papers/issue-142 && bash reproduce.sh
# ENVIRONMENT: CPython 3.9.6 with numpy 2.0.2 and matplotlib 3.9.4 (macOS, measured 2026-10-16).
#   The research instruments need numpy and the figure step needs matplotlib; the reference layer
#   and the manuscript build are standard library only.  Override with PYTHON=/path/to/python3.
#   The interpreter PATH is deliberately NOT recorded in any report: `sys.executable` is an
#   INVOCATION coordinate, so an artefact carrying it reproduces only under the exact invocation
#   that wrote it -- measured 2026-10-16, when v3/v4/v5 did not all reproduce under one command and
#   v3's shipped copy recorded a different interpreter than v4/v5's (see README -> Environment).
# INPUTS: none, and no network.  Every key set is generated from the seeds committed inside the
#   instruments.  (The reference layer's LIVE verification is a separate network pass -- see README;
#   the offline gate re-checks its committed receipt without touching the network.)
# TOLERANCE: exact -- byte equality against the shipped reports and figures.
# THE BUILD: `Tolerance: exact` is a claim about BYTES, and a byte-equality seal is only as strong as
#   the BUILD that produced the bytes, so step 6 re-checks every seal it can under a SECOND
#   interpreter (PYTHON2=... overrides the search).  A leg that cannot be run -- this machine has
#   numpy under one interpreter only -- is reported NOT RUN, BY NAME, with the build the seal is
#   scoped to, and the verdict counts those lines: a skip is never a pass.
# EXIT STATUS: 0 = `REPRODUCE: ALL GREEN`; 1 = at least one step FAILED (the count is printed).
# WRITES NOTHING INSIDE THE PACKAGE: the instruments run in a private temp copy that is removed.
# COST: about five minutes (the v0 grid dominates at ~4 min; every other step is seconds).
# SECOND TIER (opt-in): REPRO_FULL=1 bash reproduce.sh re-runs each instrument a SECOND time in a
#   fresh temp copy and compares the two fresh artefacts -- the determinism certificate.

set -u
PY="${PYTHON:-/usr/bin/python3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
FAILS=0
SKIPS=0   # legs that could not be RUN and are named as such -- never counted as passes
step() { printf '%-48s' "$1"; }
ok()   { echo "OK${1:+ ($1)}"; }
bad()  { echo "FAILED${1:+ ($1)}"; FAILS=$((FAILS+1)); }

# ---------------------------------------------------------------- 0. the interpreter
step "interpreter carries the dependencies"
if DEPS=$("$PY" -c 'import sys,numpy;print("python %s / numpy %s" % (sys.version.split()[0], numpy.__version__))' 2>&1); then
  ok "$DEPS"
else
  bad "$PY cannot import numpy -- set PYTHON=/path/to/python3"
  echo; echo "REPRODUCE: ABORTED"; exit 1
fi

WORK="$(mktemp -d "${TMPDIR:-/tmp}/issue142-repro.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
cp "$HERE"/spike_ident_v*.py "$HERE"/spike_ident_v*_results.json "$WORK"/ 2>/dev/null

# ---------------------------------------------------------------- 1. no invocation coordinate in an artefact
step "no report records an interpreter PATH"
if "$PY" - "$HERE" >"$WORK/paths.txt" 2>&1 <<'PYX'
import glob, json, os, re, sys
bad = []
for p in sorted(glob.glob(os.path.join(sys.argv[1], "spike_ident_v*_results.json"))):
    b = json.load(open(p, encoding="utf-8")).get("build", "")
    # the recorded build must be exactly `python <version> / numpy <version>`: a strict shape, so a
    # future edit that slips a path back in fails here rather than at someone else's reproduction
    if not re.match(r"^python \S+ / numpy \S+$", b):
        bad.append((os.path.basename(p), b))
for n, b in bad:
    print("      %s records %r" % (n, b))
sys.exit(1 if bad else 0)
PYX
then ok; else bad "a report records an invocation coordinate"; fi

# ---------------------------------------------------------------- 2. the research instruments
for v in 0 1 2 3 4 5 6; do
  step "instrument v$v"
  NOTE=""
  if grep -q -- "--selftest" "$WORK/spike_ident_v$v.py"; then
    # The verdict is read from what the instrument PRINTS, not from its exit code alone (a control
    # whose verdict is taken from its exit status is the recurring weak-reader defect).  Two printed
    # forms exist and BOTH are accepted only as positive evidence -- an instrument that prints
    # neither FAILS here rather than passing by silence.
    OUT=$(MPLCONFIGDIR="$WORK/.mpl" "$PY" "$WORK/spike_ident_v$v.py" --selftest 2>&1)
    RC=$?
    EVID=$(printf '%s' "$OUT" | grep -o 'SELFTEST: ALL PASS' | head -1)
    if [ -z "$EVID" ]; then
      EVID=$(printf '%s' "$OUT" | "$PY" -c '
import sys, re, json
t = sys.stdin.read()
blocks = re.findall(r"\{.*\}", t, re.S)
d = json.loads(blocks[-1]) if blocks else {}
p, n = d.get("passed", -1), d.get("total", -1)
print("%d/%d plants fired" % (p, n) if n > 0 and p == n else "")' 2>/dev/null)
    fi
    if [ "$RC" -ne 0 ] || [ -z "$EVID" ]; then
      bad "plant battery (rc=$RC, evidence: ${EVID:-none})"; continue
    fi
    NOTE="$EVID"
  else
    NOTE="no plant battery in this instrument"
  fi
  if MPLCONFIGDIR="$WORK/.mpl" "$PY" "$WORK/spike_ident_v$v.py" >"$WORK/run$v.log" 2>&1; then
    if cmp -s "$WORK/spike_ident_v$v""_results.json" "$HERE/spike_ident_v$v""_results.json"; then
      ok "$NOTE"
    else
      bad "${NOTE:+$NOTE, }report DIFFERS from the shipped one"
    fi
  else
    bad "the run failed"
  fi
done

if [ "${REPRO_FULL:-0}" = "1" ]; then
  W2="$(mktemp -d "${TMPDIR:-/tmp}/issue142-det.XXXXXX")"
  cp "$HERE"/spike_ident_v*.py "$HERE"/spike_ident_v*_results.json "$W2"/ 2>/dev/null
  step "determinism certificate (2nd fresh copy)"
  DET=1
  for v in 0 1 2 3 4 5 6; do
    MPLCONFIGDIR="$W2/.mpl" "$PY" "$W2/spike_ident_v$v.py" >/dev/null 2>&1 || DET=0
    cmp -s "$W2/spike_ident_v$v""_results.json" "$WORK/spike_ident_v$v""_results.json" || DET=0
  done
  rm -rf "$W2"
  if [ "$DET" = 1 ]; then ok "7/7 byte-identical across fresh processes"; else bad "two fresh runs disagree"; fi
fi

# ---------------------------------------------------------------- 3. the figure set
step "figures regenerate byte-identically"
if MPLCONFIGDIR="$WORK/.mpl" "$PY" "$HERE/make_figures.py" --check >"$WORK/fig.txt" 2>&1; then
  ok "$(tail -1 "$WORK/fig.txt")"
else
  bad "$(tail -1 "$WORK/fig.txt")"
fi

# ---------------------------------------------------------------- 4. the reference layer (offline)
step "reference layer: pool gate"
if "$PY" "$HERE/refscan142.py" --gate >"$WORK/gate.txt" 2>&1; then
  ok "$(grep '^GATE' "$WORK/gate.txt")"
else
  bad "$(grep '^GATE' "$WORK/gate.txt" || echo 'gate failed')"
fi
step "reference layer: plant battery"
if "$PY" "$HERE/refscan142.py" --selftest >"$WORK/rs.txt" 2>&1 &&
   grep -q "SELFTEST: ALL PASS" "$WORK/rs.txt"; then
  ok "$(grep -c '^\[.*\] ok' "$WORK/rs.txt") checks pass"
else
  bad "refscan plant battery"
fi
# The GATE reads the package in place, so its plants are throwaway COPIES: each check is fired on a
# copy of the shipped files and required to name its defect FAIL.  Without this the gate's checks
# are decoration -- nothing shows they can still fail after an edit.
step "reference layer: gate plant battery"
if "$PY" "$HERE/refscan142.py" --gateselftest >"$WORK/rgs.txt" 2>&1 &&
   grep -q "GATESELFTEST: ALL PASS" "$WORK/rgs.txt"; then
  ok "$(grep -c '\] ok' "$WORK/rgs.txt") plants fired"
else
  bad "$(tail -1 "$WORK/rgs.txt")"
fi

# ---------------------------------------------------------------- 5. the manuscript
step "manuscript rebuild"
if "$PY" "$HERE/build_manuscript.py" --check >"$WORK/ms.txt" 2>&1; then
  ok "$(tail -1 "$WORK/ms.txt")"
else
  bad "$(tail -1 "$WORK/ms.txt")"
fi
step "manuscript plant battery"
if "$PY" "$HERE/build_manuscript.py" --selftest >"$WORK/mss.txt" 2>&1 &&
   grep -q "SELFTEST: ALL PASS" "$WORK/mss.txt"; then
  ok "$(grep -c '\] ok' "$WORK/mss.txt") checks pass"
else
  bad "manuscript plant battery"
fi

# ---------------------------------------------------------------- 6. the BUILD the seals are scoped to
# A byte-equality seal ("re-run it from its own code and compare") answers WHO with "anyone who
# writes these bytes" -- it is a claim about the OUTPUT, never about the producer -- so its sealing
# authority is the BUILD: an interpreter or library that rounds differently produces a second
# "correct" answer that a same-machine second run cannot tell from a defect (the R599 lesson, from
# #130's gate).  This step re-checks every seal it CAN under a second interpreter; each leg it
# cannot run is named NOT RUN with the build the seal is scoped to, and the verdict counts them.
step "build independence of the seals"
PY2=""
for c in ${PYTHON2:-python3.13 python3.12 python3.11 python3.10}; do
  p="$(command -v "$c" 2>/dev/null || true)"
  [ -n "$p" ] || continue
  [ "$p" != "$PY" ] || continue
  PY2="$p"; break
done
if [ -z "$PY2" ]; then
  SKIPS=$((SKIPS + 1))
  ok "NOT RUN (no 2nd interpreter found; set PYTHON2=) -- seals scoped to $DEPS"
else
  B2="$("$PY2" -c 'import sys;print("python %s" % sys.version.split()[0])' 2>/dev/null || echo "$PY2")"
  RAN=""; NORUN=""
  # -- the stdlib seals: the manuscript build and the reference gate -----------------------------
  A1="$("$PY"  "$HERE/build_manuscript.py" --check 2>&1 | tail -1)"
  B1="$("$PY2" "$HERE/build_manuscript.py" --check 2>&1 | tail -1)"
  A2="$("$PY"  "$HERE/refscan142.py" --gate 2>&1 | grep '^GATE')"
  B2G="$("$PY2" "$HERE/refscan142.py" --gate 2>&1 | grep '^GATE')"
  if [ -n "$A1" ] && [ "$A1" = "$B1" ] && [ -n "$A2" ] && [ "$A2" = "$B2G" ]; then
    RAN="manuscript, refgate"
  else
    bad "$B2 DISAGREES on the stdlib seals (manuscript: '$A1' vs '$B1'; gate: '$A2' vs '$B2G')"
  fi
  # -- the numeric seal: one instrument, byte-compared across the two builds ----------------------
  if [ -n "$RAN" ] && "$PY2" -c 'import numpy' 2>/dev/null; then
    DET2=1
    "$PY2" "$WORK/spike_ident_v6.py" >/dev/null 2>&1 || DET2=0
    cmp -s "$WORK/spike_ident_v6_results.json" "$HERE/spike_ident_v6_results.json" || DET2=0
    if [ "$DET2" = 1 ]; then RAN="$RAN, v6"; else bad "v6's report DIFFERS under $B2"; fi
  else
    NORUN="$NORUN instrument reports (numpy)"
  fi
  # -- the figure seal ---------------------------------------------------------------------------
  if [ -n "$RAN" ] && "$PY2" -c 'import matplotlib' 2>/dev/null; then
    if MPLCONFIGDIR="$WORK/.mpl2" "$PY2" "$HERE/make_figures.py" --check >/dev/null 2>&1; then
      RAN="$RAN, figures"
    else
      bad "the figures DIFFER under $B2"
    fi
  else
    NORUN="$NORUN figures (matplotlib)"
  fi
  if [ -n "$NORUN" ]; then SKIPS=$((SKIPS + 1)); fi
  [ -n "$RAN" ] && ok "$B2 agrees ($RAN)${NORUN:+; NOT RUN:$NORUN -- scoped to $DEPS}"
fi

# ---------------------------------------------------------------- verdict
echo
if [ "$FAILS" = 0 ]; then
  echo "REPRODUCE: ALL GREEN${SKIPS:+ ($SKIPS leg(s) NOT RUN -- named above)}"
  exit 0
fi
echo "REPRODUCE: $FAILS STEP(S) FAILED"
exit 1
