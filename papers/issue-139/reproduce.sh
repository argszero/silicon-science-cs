#!/usr/bin/env bash
# reproduce.sh -- issue #139, "Proving Is Not Paying: the Success-vs-Cost Frontier of
#                Interdependent Proof Obligations"
#
# WHAT THIS RECOMPUTES (not a checksum check over committed outputs): it re-runs the FOUR
# instruments from their own code and compares each fresh report BYTE-FOR-BYTE against the
# report this package ships; it asserts the headline numbers the manuscript quotes are the ones
# the FRESH reports carry; and it runs FIVE PLANTS that must fire (a perturbed instrument must
# produce a different report; a broken uncoupled recursion must fail its battery; a broken coupled
# recursion must change the report; a planted number must make the claims leg fail; and a README
# quoting a stale manuscript size must fail the `readme` leg).
#
# RUN IT FROM THE PACKAGE DIRECTORY:   cd papers/issue-139 && bash reproduce.sh
# ENVIRONMENT: CPython 3, standard library only (json/math/os/sys/random/itertools/argparse) --
#   NO third-party import appears anywhere in this package, so no library version enters a
#   comparison.  Every shipped report is measured byte-identical under 3.9.6 and 3.13.9 (this
#   package's cross-build run, `REPRO_BUILDS` below) -- a pair ACROSS the CPython 3.12 `sum()`
#   change, which is the boundary a version-scoped defect would sit on: `sum()` over floats became
#   Neumaier-compensated in 3.12, so a `sum()`-reduced quantity can differ between the two sides and
#   cannot differ within one.  Set PYTHON=... to select the build the default legs run under.  Which
#   interpreters exist is a property of the machine, not of this package, so the leg reads its list
#   from REPRO_BUILDS rather than naming interpreters -- here 3.9.6 is `/usr/bin/python3`, which is
#   how a pre-3.12 build is reachable on this machine.
# INPUTS: none, and no network.  Every graph, difficulty vector, coupling level and schedule is
#   declared in the instruments, and the only randomness is drawn from the committed seeds, so a
#   run touches nothing outside its own directory.
# TOLERANCE: exact -- the comparison is byte equality against the shipped reports.
# EXIT STATUS: 0 = `REPRODUCE: ALL GREEN`; 1 = at least one step FAILED; 2 = no step failed but a
#   journal gate could not read its window and said so (`NOT RUN`) -- a COORDINATE of the run, not
#   a finding about the work.
# WHAT IT WRITES: nothing inside the package.  Every instrument runs with stdout redirected into a
#   private temp directory this script creates and removes.
# COST: about two minutes for the default set (four instruments re-run over their full grids, the
#   batteries, the plants, the figure set, the offline reference layer and the manuscript re-render).
# CROSS-BUILD: an `exact` tolerance is a claim about a BUILD, not only about a run, so the leg that
#   can see a version-scoped defect is the one that re-runs every report under a second interpreter
#   and compares the two -- and the pair has to STRADDLE the 3.12 `sum()` boundary, since two builds
#   on the same side of it are one reading taken twice.  It takes its interpreter list from
#   `REPRO_BUILDS`, because which interpreters exist is a property of the machine, not of this
#   package:
#       REPRO_BUILDS="/usr/bin/python3 python3.13" bash reproduce.sh
#   (measured here: every shipped report byte-identical under 3.9.6 and 3.13.9.)

set -u
PY="${PYTHON:-python3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/issue139-repro.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
FAILED=0
NOTRUN=0

say()  { printf '%-18s %s\n' "$1" "$2"; }
bad()  { printf '%-18s FAILED -- %s\n' "$1" "$2"; FAILED=$((FAILED+1)); }
# A CARRIER THAT QUOTES A RUN IS A CLAIM ABOUT IT: the README prints the manuscript leg's own line,
# byte count included, so that copy is read back against the line THIS run printed rather than
# trusted.  It is a function taking the file as its argument, so the plant below can point it at a
# copy whose quoted size has been altered -- a comparison whose fixture cannot fail is decoration
# (Class 189: the plant's INPUT is part of the plant).  The defect it exists for was found at round
# 2: the round-1 revision grew the manuscript by 1684 bytes and the README went on quoting the
# pre-revision size, which every other leg here passes because nothing else reads the README.
readme_quotes() {                       # $1 = readme, $2 = the line the run printed
  # Whitespace runs are collapsed on BOTH sides before the comparison: the README hard-wraps, so a
  # line of the run straddles a line break there, and a raw `grep -F` would report a defect for the
  # way a paragraph was wrapped rather than for what it says (Classes 178(b)/190 -- the same rule
  # `papers/issue-126/check_numbers.py` applies).
  [ -f "$1" ] || return 1
  local hay needle
  hay="$(tr -s '[:space:]' ' ' < "$1")"
  needle="$(printf '%s' "$2" | tr -s '[:space:]' ' ')"
  case "$hay" in *"$needle"*) return 0 ;; esac
  return 1
}
# The journal gates take their own exit status from their contract -- 0 PASS, 1 FAIL, 2 NOT RUN --
# so a gate that could not read its window is reported as ITS verdict and does not count as a
# failure.  Swallowing that status and calling exit 2 a `FAILED` would report a coordinate of the
# run as a finding about the work (Class 236).
classify() {
  local line
  case "$2" in
    0) line="$(printf '%s' "$3" | grep -E 'GATE:|broken=|pointers=' | tail -1)"
       [ -n "$line" ] || line="$(printf '%s' "$3" | grep -v '^[[:space:]]*$' | tail -1)"
       say "$1" "$line" ;;
    2) NOTRUN=$((NOTRUN+1))
       say "$1" "NOT RUN -- $(printf '%s' "$3" | grep -E 'NOT RUN' | tail -1)" ;;
    *) bad "$1" "the journal gate failed (exit $2)"
       printf '%s\n' "$3" | sed 's/^/                   /' ;;
  esac
}

echo "== #139 reproduction =="

# ---- 0. the build ------------------------------------------------------------------------------
BUILD=$("$PY" -c 'import sys;print(sys.executable, sys.version.split()[0])' 2>/dev/null) \
  || { echo "no interpreter at '$PY' -- set PYTHON=/path/to/python3"; exit 2; }
say "build" "$BUILD | stdlib only (no third-party import anywhere in the package)"

# ---- 1. the plant batteries (v1, v2, v3) -------------------------------------------------------
# v0 ships no --selftest: it predates that convention here and is kept FROZEN so that the hash its
# registration comment published stays true of the shipped bytes.  Its certificate is the
# `exact_checks` block in its own report, asserted in section 4, and its plant is in section 5.
for n in 1 2 3; do
  S="spike_v${n}.py"
  if OUT=$("$PY" "$HERE/$S" --selftest 2>&1); then
    say "$S selftest" "$(printf '%s' "$OUT" | tail -1)"
  else
    bad "$S selftest" "the plant battery failed"
    printf '%s\n' "$OUT" | sed 's/^/                   /'
  fi
done

# ---- 2. each instrument: byte-for-byte reproduction of every shipped artefact --------------------
# The command matters: the arguments ARE part of the artefact (a different --steps or --Bmax is a
# different grid), so each entry below is the command the shipped file was produced by -- and the
# output is taken from stdout, which is how those files were made.  (The instruments also accept
# SPIKE_OUT, whose atomic write omits the trailing newline `print` adds; the two differ by that
# byte, which is why the shipped files are reproduced through stdout.)
repro() {   # script  outfile  args...
  local S="$1" out="$2"; shift 2
  ( cd "$WORK" && "$PY" "$HERE/$S" "$@" > "$WORK/$out" 2>"$WORK/err" ) \
    || { bad "$S run" "the instrument did not complete"; return 1; }
  if cmp -s "$WORK/$out" "$HERE/$out"; then
    say "$S report" "byte-identical to the shipped $out ($(shasum -a 256 "$HERE/$out" | cut -c1-16))"
  else
    bad "$S report" "$out differs from the shipped report"
  fi
}
repro spike_v0.py spike_v0_results.json --json
repro spike_v1.py spike_v1_results.json --json
repro spike_v2.py spike_v2_results.json --json --steps 40
repro spike_v3.py spike_v3_results.json --json --Bmax 100
# the text artefacts: v3's report and the two second-tier legs
for spec in "spike_v3.py spike_v3_report.txt --Bmax 100" \
            "spike_v1.py spike_v1_robust.txt --robust" \
            "spike_v2.py spike_v2_reliability.txt --reliable"; do
  set -- $spec; S="$1"; OUT_F="$2"; shift 2
  if ( cd "$WORK" && "$PY" "$HERE/$S" "$@" > "$WORK/$OUT_F" 2>/dev/null ); then
    if cmp -s "$WORK/$OUT_F" "$HERE/$OUT_F"; then
      say "$S text" "byte-identical to the shipped $OUT_F"
    else
      bad "$S text" "$OUT_F differs from the shipped file"
    fi
  else
    bad "$S text" "$S did not complete"
  fi
done

# ---- 3. the cross-build leg (a version-scoped defect is invisible to a two-run certificate) ------
# Class 231 / R599: a same-build two-run check cannot see a defect scoped to an interpreter
# version, so an `exact` tolerance owes a second BUILD.  This leg re-runs every report under each
# interpreter named in REPRO_BUILDS and compares the results to each other and to the shipped file.
if [ -n "${REPRO_BUILDS:-}" ]; then
  for c in $REPRO_BUILDS; do
    command -v "$c" >/dev/null 2>&1 || { NOTRUN=$((NOTRUN+1)); say "build $c" "NOT RUN -- not on PATH"; continue; }
    ok=1
    for spec in "spike_v0.py spike_v0_results.json --json" \
                "spike_v1.py spike_v1_results.json --json" \
                "spike_v2.py spike_v2_results.json --json --steps 40" \
                "spike_v3.py spike_v3_results.json --json --Bmax 100"; do
      set -- $spec; S="$1"; OUT_F="$2"; shift 2
      ( cd "$WORK" && "$c" "$HERE/$S" "$@" > "$WORK/x_$OUT_F" 2>/dev/null ) || { ok=0; break; }
      cmp -s "$WORK/x_$OUT_F" "$HERE/$OUT_F" || { ok=0; break; }
    done
    if [ "$ok" = "1" ]; then
      say "build $c" "every shipped report byte-identical under $("$c" -c 'import sys;print(sys.version.split()[0])' 2>/dev/null)"
    else
      bad "build $c" "a shipped report is NOT reproduced under this build (a version-scoped defect)"
    fi
  done
fi

# ---- 4. the headline numbers, asserted from the FRESH reports -----------------------------------
# The manuscript quotes these.  Asserting them here is what makes the shipped report and the claim
# in the prose the same object: a number that moves in the instrument but not in the prose fails
# this leg rather than passing unnoticed.  Written as a file so section 5 can plant on it.
cat > "$WORK/claims.py" <<'PY'
import json, sys
v0, v1, v2, v3 = (json.load(open(p)) for p in sys.argv[1:5])
bad = []
def want(name, got, op, val):
    ok = op(got, val)
    print("  %-52s %s  %s" % (name, got, "OK" if ok else "!! EXPECTED %s" % (val,)))
    if not ok:
        bad.append(name)
c = v0["exact_checks"]
want("v0 anchor (fixed order) vs closed form <= 1e-12", c["anchor_fixed_order"], lambda a, b: a <= b, 1e-12)
want("v0 anchor (easiest first) vs closed form <= 1e-12", c["anchor_easiest_first"], lambda a, b: a <= b, 1e-12)
want("v0 c=0 carries no value <= 1e-12", c["zero_coupling_carries_no_value"], lambda a, b: a <= b, 1e-12)
want("v0 rerun determinism == 0", c["determinism_rerun"], lambda a, b: a == b, 0.0)
cert = v1["certificate"]
want("v1 certificate cells (c=0) >= 140", cert["c0_cells"], lambda a, b: a >= b, 140)
want("v1 certificate max abs vs closed form <= 1e-12", cert["max_abs_vs_closed_form"], lambda a, b: a <= b, 1e-12)
f = v1["findings"]
want("v1 P1 cells >= 480", f["P1_cells"], lambda a, b: a >= b, 480)
want("v1 P1 ratio >= 1.5 in all cells", f["P1_ratio_ge_1.5"], lambda a, b: a >= b, 480)
want("v1 concavity defect max > 0 (P1 concavity REFUTED)", f["P1_max_concavity_defect"], lambda a, b: a > b, 0.0)
want("v1 P2 coupled cells >= 360", f["P2_coupled_cells"], lambda a, b: a >= b, 360)
want("v1 P2 coupled gain strictly positive in >= 327", f["P2_positive_gain_cells"], lambda a, b: a >= b, 327)
want("v1 P2 gain at c=0 == 0", f["P2_gain_at_c0_maxabs"], lambda a, b: a == b, 0.0)
want("v1 P3 always-positive cells == 0 (P3 REFUTED)", f["P3_always_positive"], lambda a, b: a == b, 0)
want("v1 P3 control max abs == 0", f["P3_control_maxabs"], lambda a, b: a == b, 0.0)
law = v2["law"]
want("v2 n=2 law grid cells >= 1600", law["cells"], lambda a, b: a >= b, 1600)
want("v2 rule (p2 > p1) agrees on 100.0% of the grid", law["candidate_rules"]["p2 > p1"]["pct"], lambda a, b: a == b, 100.0)
rows = [r for r in v2["planner_rows"] if r["graph"] != "empty" and r["ratio"] is not None]
under = [r for r in rows if r["ratio"] < 1.0]
want("v2 planner cells (treatment) >= 1440", len(rows), lambda a, b: a >= b, 1440)
want("v2 pass-rate rule UNDER-budgets in >= 1110 cells", len(under), lambda a, b: a >= b, 1110)
t = v3["totals"]
want("v3 permutations tested >= 11923", t["permutations"], lambda a, b: a >= b, 11923)
want("v3 GUARANTEE violations == 0", t["guarantee_violations"], lambda a, b: a == b, 0)
want("v3 converse exceptions > 0 (the converse fails)", t["converse_exceptions"], lambda a, b: a > b, 0)
want("v3 coupled-breakdown cells > 0", t["coupled_breakdown_cells"], lambda a, b: a > b, 0)
want("v3 breakdowns explained by the coupling == all of them", t["explained_by_coupling"], lambda a, b: a == b, t["coupled_breakdown_cells"])
want("v3 coupling-boundary violations > 0 (the theorem is a c=0 theorem)", t["coupling_boundary_violations"], lambda a, b: a > b, 0)
print("CLAIMS: %d checked, %d wrong" % (27, len(bad)))
sys.exit(1 if bad else 0)
PY
if "$PY" "$WORK/claims.py" "$WORK/spike_v0_results.json" "$WORK/spike_v1_results.json" \
                        "$WORK/spike_v2_results.json" "$WORK/spike_v3_results.json" > "$WORK/claims.txt" 2>&1; then
  sed 's/^/                   /' "$WORK/claims.txt"
  say "claims" "all 27 headline numbers match the fresh reports"
else
  sed 's/^/                   /' "$WORK/claims.txt" | grep -E '!!|CLAIMS' || true
  bad "claims" "a headline number does not match the fresh reports"
fi

# ---- 5. THE PLANTS: each leg above must be able to fail ------------------------------------------
# Without these, a byte comparison between two files that are the same file would pass, and a
# claims table that no perturbation can break proves nothing about the reports it reads.
#
# The instruments are a MODULE SET (`spike_v3.py` imports `spike_v1`), so a planted copy must run
# beside its siblings -- otherwise it dies on ImportError, writes no report, and every `cmp` against
# the shipped file then "differs": a plant that fires for the WRONG reason.  Copy the whole set into
# the work directory first, and run every planted copy from there.
cp "$HERE"/spike_v*.py "$WORK/"
sed 's/"c": 0.35/"c": 0.36/' "$HERE/spike_v0.py" > "$WORK/spike_v0_plant.py"
if cmp -s "$WORK/spike_v0_plant.py" "$HERE/spike_v0.py"; then
  bad "plant v0" "the perturbation did not land (the coupling constant moved?)"
elif ( cd "$WORK" && "$PY" "$WORK/spike_v0_plant.py" --json > "$WORK/plant_v0.json" 2>"$WORK/plant_v0.err" ); then
  if cmp -s "$WORK/plant_v0.json" "$HERE/spike_v0_results.json"; then
    bad "plant v0" "a perturbed instrument produced the SAME report -- section 2 cannot fail"
  else
    say "plant v0" "a perturbed coupling changes the report (the byte comparison is live)"
  fi
elif grep -qE 'ImportError|ModuleNotFoundError|Traceback' "$WORK/plant_v0.err"; then
  bad "plant v0" "the planted copy could not import its siblings -- the plant proves nothing"
else
  bad "plant v0" "the perturbed instrument did not run"
fi
# PLANT A -- aimed at the BATTERY, at the recursion the battery actually calls.  v3 has TWO
# recursions: `fixed_order_frontier` (uncoupled, the one `selftest()` compares against the 2^n DP)
# and `fixed_order_frontier_coupled` (the coupling boundary, which the battery never calls).  A
# plant aimed at the coupled line survived this leg when this script was first written -- the
# perturbation landed outside the check's jurisdiction (Class 238) -- so the battery plant now
# targets the uncoupled line and PLANT B below covers the coupled one against the REPORT.
sed 's/V\[k\]\[b\] = pk \* (1.0 + V\[k + 1\]\[b - 1\])/V[k][b] = pk * (0.0 + V[k + 1][b - 1])/' \
    "$HERE/spike_v3.py" > "$WORK/spike_v3_broken.py"
if cmp -s "$WORK/spike_v3_broken.py" "$HERE/spike_v3.py"; then
  bad "plant v3 battery" "the perturbation did not land (the uncoupled recursion moved?)"
elif ( cd "$WORK" && "$PY" "$WORK/spike_v3_broken.py" --selftest >"$WORK/plantA.out" 2>&1 ) \
     && grep -q 'SELFTEST' "$WORK/plantA.out"; then
  bad "plant v3 battery" "a BROKEN recursion still passed the battery -- the battery cannot fail"
elif grep -qE 'ImportError|ModuleNotFoundError|Traceback' "$WORK/plantA.out"; then
  bad "plant v3 battery" "the planted copy could not import its siblings -- the plant proves nothing"
else
  say "plant v3 battery" "a broken uncoupled recursion FAILS the battery (the battery is not decoration)"
fi
# PLANT B -- aimed at the REPORT, at the coupled recursion the battery does not reach.
sed 's/V\[k\]\[b\] = q\[k\] \* (1.0 + V\[k + 1\]\[b - 1\])/V[k][b] = q[k] * (0.0 + V[k + 1][b - 1])/' \
    "$HERE/spike_v3.py" > "$WORK/spike_v3_coupledplant.py"
if cmp -s "$WORK/spike_v3_coupledplant.py" "$HERE/spike_v3.py"; then
  bad "plant v3 coupled" "the perturbation did not land (the coupled recursion moved?)"
elif ! ( cd "$WORK" && "$PY" "$WORK/spike_v3_coupledplant.py" --json --Bmax 100 > "$WORK/plant_v3c.json" 2>"$WORK/plantB.err" ); then
  bad "plant v3 coupled" "the perturbed instrument did not run"
elif [ ! -s "$WORK/plant_v3c.json" ]; then
  bad "plant v3 coupled" "the perturbed instrument wrote no report -- the plant proves nothing"
elif cmp -s "$WORK/plant_v3c.json" "$HERE/spike_v3_results.json"; then
  bad "plant v3 coupled" "the coupled path is NOT exercised by the report -- a dead line in a live artefact"
else
  say "plant v3 coupled" "a broken coupled recursion changes the report (every shipped line is live)"
fi
"$PY" - "$WORK/spike_v3_results.json" "$WORK/planted_v3.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d["totals"]["guarantee_violations"] = 1          # the claim the theory arm rests on
json.dump(d, open(sys.argv[2], "w"))
PY
if "$PY" "$WORK/claims.py" "$WORK/spike_v0_results.json" "$WORK/spike_v1_results.json" \
                         "$WORK/spike_v2_results.json" "$WORK/planted_v3.json" >/dev/null 2>&1; then
  bad "plant claims" "a planted number did NOT make the claims leg fail -- the leg cannot fail"
else
  say "plant claims" "a planted number makes the claims leg fail (the table reads the reports)"
fi

# ---- 6. the figure set (present once make_figures139.py is in the package) --------------------------
if [ -f "$HERE/make_figures139.py" ]; then
  if OUT=$("$PY" "$HERE/make_figures139.py" --selftest 2>&1); then
    say "make_figures" "$(printf '%s' "$OUT" | tail -1)"
  else
    bad "make_figures" "the figure certificate failed"
    printf '%s\n' "$OUT" | sed 's/^/                   /'
  fi
  mkdir -p "$WORK/figures"
  if "$PY" "$HERE/make_figures139.py" "$WORK/figures" >/dev/null 2>&1; then
    FIGOK=1
    for f in $(cd "$HERE/figures" && ls); do
      cmp -s "$WORK/figures/$f" "$HERE/figures/$f" || { FIGOK=0; bad "figure $f" "differs from the shipped file"; }
    done
    [ "$FIGOK" = "1" ] && say "figures" "$(ls "$HERE/figures" | wc -l | tr -d ' ') files byte-identical to the shipped figure set"
  else
    bad "make_figures run" "the generator did not complete (a figure left its axes?)"
  fi
else
  NOTRUN=$((NOTRUN+1))
  say "figures" "NOT RUN -- no make_figures139.py in the package yet"
fi

# ---- 7. the reference layer (present once refscan139.py is in the package) -----------------------
# The live network verification (`refscan139.py --verify`) is a separate, documented pass; its
# verbatim output is the committed receipt refs/verify-run.txt, which the offline gate binds to the
# shipped pool by sha256 -- so this step needs no network and still checks the receipt is current.
if [ -f "$HERE/refscan139.py" ]; then
  if OUT=$("$PY" "$HERE/refscan139.py" --selftest 2>&1); then
    say "refscan selftest" "$(printf '%s' "$OUT" | tail -1)"
  else
    bad "refscan selftest" "the plant battery failed"
  fi
  if OUT=$("$PY" "$HERE/refscan139.py" --gate 2>&1); then
    say "refscan gate" "$(printf '%s' "$OUT" | tail -1) -- live verification is in reference-check.md"
  else
    bad "refscan gate" "the offline reference-pool gate failed"
    printf '%s\n' "$OUT" | sed 's/^/                   /'
  fi
  if [ -f "$HERE/make_reference_check.py" ]; then
    if OUT=$("$PY" "$HERE/make_reference_check.py" --check 2>&1); then
      say "reference-check" "$(printf '%s' "$OUT" | tail -1)"
    else
      bad "reference-check" "$(printf '%s' "$OUT" | tail -1)"
    fi
  fi
else
  NOTRUN=$((NOTRUN+1))
  say "references" "NOT RUN -- no refscan139.py in the package yet"
fi

# ---- 8. the manuscript: re-render and compare, then the journal gates ---------------------------
if [ -f "$HERE/manuscript.md" ]; then
  if OUT=$("$PY" "$HERE/build_manuscript.py" --check 2>&1); then
    MSLINE="$(printf '%s' "$OUT" | grep -m1 '^MANUSCRIPT: MATCH')"
    say "manuscript" "$(printf '%s' "$OUT" | tail -1)"
    # the README's copy of this line, read back against the line this run printed
    if readme_quotes "$HERE/README.md" "$MSLINE"; then
      say "readme" "quotes this run's manuscript line ($(printf '%s' "$MSLINE" | sed 's/^MANUSCRIPT: MATCH -- //'))"
    else
      bad "readme" "README.md does not quote the line this run printed: '$MSLINE'"
    fi
    # and the plant that proves the comparison is live: a copy quoting a WRONG byte count must fail
    cp "$HERE/README.md" "$WORK/readme_plant.md"
    if "$PY" - "$WORK/readme_plant.md" <<'PY'
import io, re, sys
p = sys.argv[1]
t = io.open(p, encoding="utf-8").read()
t2, n = re.subn(r"(MANUSCRIPT: MATCH -- \d+ references, \d+ numbers, )\d+( bytes)", r"\g<1>1\g<2>", t, count=1)
io.open(p, "w", encoding="utf-8").write(t2)
raise SystemExit(0 if n == 1 else 1)          # a plant that changed nothing is INERT, not passing
PY
    then
      if readme_quotes "$WORK/readme_plant.md" "$MSLINE"; then
        bad "plant readme" "a README quoting a WRONG size still passed the comparison (the leg is inert)"
      else
        say "plant readme" "a README quoting a wrong size FAILS the comparison (the leg is live)"
      fi
    else
      bad "plant readme" "the plant could not be applied -- README.md carries no line to perturb (Class 189)"
    fi
  else
    bad "manuscript" "$(printf '%s' "$OUT" | tail -1)"
  fi
  if OUT=$("$PY" "$HERE/build_manuscript.py" --selftest 2>&1); then
    say "build plants" "$(printf '%s' "$OUT" | tail -1)"
  else
    bad "build plants" "$(printf '%s' "$OUT" | tail -1)"
  fi
  ROOT="$(cd "$HERE/../.." && pwd)"
  # refgate numbers the manuscript's reference block; its f-strings carry backslashes, so it needs an
  # interpreter >= 3.12 independently of the package's own build.  GATE_PYTHON overrides.
  GP=""
  for c in "${GATE_PYTHON:-}" python3.13 python3.12 "$PY"; do
    [ -n "$c" ] || continue
    command -v "$c" >/dev/null 2>&1 || continue
    v=$("$c" -c 'import sys;print(sys.version_info>=(3,12))' 2>/dev/null) || continue
    [ "$v" = "True" ] && { GP="$c"; break; }
  done
  for g in numgate linkgate pointgate; do
    if [ -f "$ROOT/.github/tools/$g.py" ]; then
      OUT=$(cd "$ROOT" && "$PY" ".github/tools/$g.py" "papers/issue-139/manuscript.md" 2>&1); RC=$?
      classify "$g" "$RC" "$OUT"
    else
      NOTRUN=$((NOTRUN+1))
      say "$g" "NOT RUN -- the tool lives in .github/tools/ of the journal repo"
    fi
  done
  RG="$ROOT/.github/tools/refgate.py"
  if [ -f "$RG" ] && [ -n "$GP" ]; then
    OUT=$(cd "$ROOT" && "$GP" ".github/tools/refgate.py" "papers/issue-139/manuscript.md" 2>&1); RC=$?
    if [ "$RC" = "0" ]; then
      if [ -f "$HERE/refgate-journal.txt" ] && [ "$OUT" = "$(cat "$HERE/refgate-journal.txt")" ]; then
        say "refgate" "$(printf '%s' "$OUT" | grep -E 'entries=|coverage=' | tr '\n' ' ') -- matches the committed receipt"
      else
        say "refgate" "$(printf '%s' "$OUT" | grep -E 'entries=|coverage=' | tr '\n' ' ')"
      fi
    elif [ "$RC" = "2" ]; then
      NOTRUN=$((NOTRUN+1))
      say "refgate" "NOT RUN -- $(printf '%s' "$OUT" | grep -E 'NOT RUN' | tail -1)"
    else
      bad "refgate" "the reference gate failed (exit $RC, $GP)"
      printf '%s\n' "$OUT" | sed 's/^/                   /'
    fi
  else
    NOTRUN=$((NOTRUN+1))
    say "refgate" "NOT RUN -- the tool, or an interpreter >= 3.12, is unavailable here"
  fi
else
  NOTRUN=$((NOTRUN+1))
  say "manuscript" "NOT RUN -- no manuscript.md in the package yet (Phase B in progress)"
fi

echo
if [ "$FAILED" != "0" ]; then
  echo "REPRODUCE: $FAILED step(s) FAILED"
  exit "$FAILED"
fi
if [ "$NOTRUN" != "0" ]; then
  echo "REPRODUCE: $NOTRUN step(s) NOT RUN -- a coordinate of this run, not a finding about the work"
  echo "            (a journal gate needs a checkout: it takes its carrier set from \`git ls-files\`)"
  exit 2
fi
echo "REPRODUCE: ALL GREEN"
exit 0
