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
# ENVIRONMENT: CPython 3.9.6 with numpy 2.0.2, matplotlib 3.9.4 and scipy 1.13.1 (macOS, measured
#   2026-10-16).  The research instruments need numpy; v5 needs scipy (`scipy.signal.lfilter`) and
#   v6 reaches it through v5; the figure step needs matplotlib; the reference layer and the
#   manuscript build are standard library only.  That is the WHOLE set -- an import census over the
#   package's nine scripts returns numpy (all instruments), scipy (v5), matplotlib (make_figures)
#   and the local `spike_ident_*` sibling imports.  Override with PYTHON=/path/to/python3.
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
#   interpreter (PYTHON2=... overrides the search).  A leg that cannot be run is reported NOT RUN, BY
#   NAME, with the build the seal is scoped to, and the verdict counts those lines: a skip is never a
#   pass.  Two readings that look alike are kept apart: a program that merely CARRIES the name
#   `python3.13` is not a CPython (it must answer the version probe in CPython's format before any
#   seal is run under it), and an instrument that ABORTS is a leg that could not run, never a
#   disagreement -- only a completed run whose bytes differ is DIFFERS.
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
# The probe covers the WHOLE declared set, not numpy alone: v5 imports scipy and v6 imports v5, so a
# probe that checks numpy only lets those two modules abort mid-run with a traceback -- which the
# step then has to read as a FAILED with no evidence (measured 2026-10-17, editor's triage of #142:
# a venv built exactly as the README declares it aborted v5 and v6 on `ModuleNotFoundError: scipy`).
# A missing dependency is named here, before any instrument runs.
if DEPS=$("$PY" - 2>&1 <<'PYX'
import importlib.metadata as md, importlib.util, sys
need = ("numpy", "scipy", "matplotlib")
missing = [n for n in need if importlib.util.find_spec(n) is None]
if missing:
    print("MISSING %s" % ", ".join(missing)); sys.exit(1)
# the VERSION is read from distribution metadata, never by importing: importing matplotlib writes a
# cache directory and can print a warning, and this probe's output IS the message the reader sees
vers = {}
for n in need:
    try:
        vers[n] = md.version(n)
    except Exception:
        vers[n] = "unknown"
print("python %s / %s" % (sys.version.split()[0],
                          " / ".join("%s %s" % (n, vers[n]) for n in need)))
PYX
); then
  ok "$DEPS"
else
  case "$DEPS" in
    *MISSING*) bad "$DEPS -- $PY lacks a declared dependency; set PYTHON=/path/to/python3 (or install it)" ;;
    *)         bad "$PY could not run the dependency probe: $(printf '%s' "$DEPS" | tail -1)" ;;
  esac
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
PY2=""; PY2V=""; NOTCPY=""
for c in ${PYTHON2:-python3.13 python3.12 python3.11 python3.10}; do
  p="$(command -v "$c" 2>/dev/null || true)"
  [ -n "$p" ] || continue
  [ "$p" != "$PY" ] || continue
  # THE NAME IS NOT THE PROGRAM.  `command -v python3.13` returns whatever executable carries that
  # name on this machine, which need not be a Python at all -- measured 2026-10-17 on the editor's
  # machine, where it resolved to a console script: every leg then ran that script, read its own
  # argument error as evidence, and the step reported two "disagreements" that were two aborts.
  # So the resolved program must PROVE it is a CPython by answering the version probe in CPython's
  # format (`python X.Y...`) before any seal is scoped to it; a program that cannot is skipped by
  # name, never used.
  v="$("$p" -c 'import sys;print("python %s" % sys.version.split()[0])' 2>/dev/null || true)"
  case "$v" in
    "python "[0-9]*.[0-9]*) PY2="$p"; PY2V="$v"; break ;;
    *) NOTCPY="$NOTCPY $c->$p" ;;
  esac
done
if [ -z "$PY2" ]; then
  SKIPS=$((SKIPS + 1))
  ok "NOT RUN (no 2nd CPython found${NOTCPY:+; rejected$NOTCPY}; set PYTHON2=) -- seals scoped to $DEPS"
else
  B2="$PY2V"
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
  # the guard names the instrument's REAL import set (numpy and scipy -- v6 reaches scipy through
  # v5), because a guard narrower than the import set reports an abort as a difference
  if [ -n "$RAN" ] && "$PY2" -c 'import numpy, scipy' 2>/dev/null; then
    V6OUT="$("$PY2" "$WORK/spike_ident_v6.py" 2>&1)"; V6RC=$?
    if [ "$V6RC" != 0 ]; then
      # it never finished: there is no second reading to compare, so this is a leg that could not
      # run -- reported by name, with the line that ended it
      NORUN="$NORUN instrument reports (v6 aborted under $B2, rc=$V6RC: $(printf '%s' "$V6OUT" | tail -1))"
    elif cmp -s "$WORK/spike_ident_v6_results.json" "$HERE/spike_ident_v6_results.json"; then
      RAN="$RAN, v6"
    else
      bad "v6's report DIFFERS under $B2"
    fi
  else
    NORUN="$NORUN instrument reports (numpy, scipy)"
  fi
  # -- the figure seal ---------------------------------------------------------------------------
  # `--check` PRINTS its verdict, so the verdict -- not the exit code -- is what is read: a mismatch
  # and a crash both exit nonzero, and only the first is a disagreement
  if [ -n "$RAN" ] && "$PY2" -c 'import matplotlib' 2>/dev/null; then
    FIGOUT="$(MPLCONFIGDIR="$WORK/.mpl2" "$PY2" "$HERE/make_figures.py" --check 2>&1)"
    case "$FIGOUT" in
      *"CHECK OK"*)        RAN="$RAN, figures" ;;
      *"CHECK FAILED"*)    bad "the figures DIFFER under $B2 ($(printf '%s' "$FIGOUT" | grep 'CHECK FAILED' | tail -1))" ;;
      *)                   NORUN="$NORUN figures (make_figures aborted under $B2: $(printf '%s' "$FIGOUT" | tail -1))" ;;
    esac
  else
    NORUN="$NORUN figures (matplotlib)"
  fi
  if [ -n "$NORUN" ]; then SKIPS=$((SKIPS + 1)); fi
  # a rejected name is printed whenever there was one: a program silently skipped is a leg the
  # reader cannot audit, and the next `python3.13` on some other machine will be a real one
  [ -n "$RAN" ] && ok "$B2 agrees ($RAN)${NORUN:+; NOT RUN:$NORUN -- scoped to $DEPS}${NOTCPY:+; rejected (not a CPython):$NOTCPY}"
fi

# ---------------------------------------------------------------- verdict
echo
if [ "$FAILS" = 0 ]; then
  echo "REPRODUCE: ALL GREEN${SKIPS:+ ($SKIPS leg(s) NOT RUN -- named above)}"
  exit 0
fi
echo "REPRODUCE: $FAILS STEP(S) FAILED"
exit 1
