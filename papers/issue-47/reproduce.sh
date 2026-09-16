#!/usr/bin/env bash
# Issue #47 -- one command reproduces every number this package claims.
#
#   bash reproduce.sh
#
# Steps, and what each one is for:
#   1. the eight stages (seven frozen, plus the certificate stage added by the F0b amendment),
#      then the canonical aggregate (canonical_runner.py), which RECOMPUTES
#      every cited number from the stage artefacts' primitives and cross-checks it against the value
#      the stage recorded about itself;
#   2. the liveness control -- each recomputation is corrupted in a throwaway copy and must notice;
#   3. the external cell's own check-liveness -- 13 mutations of the cell script, one per named check,
#      each of which must make exactly that check fail;
#   4. the design-freeze document against the artefacts -- 57 checks, including the digest table;
#   5. the manuscript assembly -- every measurement in the prose is a placeholder resolved out of the
#      artefacts (a placeholder that cannot be resolved, or a citation key with no reference entry,
#      fails the step), including the design table, which is rendered from the instrument artefact
#      rather than typed;
#   6. the SUPPORT limb of citation integrity -- every citation occurrence read against the sentence
#      it sits in, offline, and the shipped REPORT of that read checked against a fresh build of it
#      (the IDENTITY limb needs the network and is reported in reference-check.md);
#   7. the journal's own reference gate (`.github/tools/refgate.py`), run from the repository root,
#      where the tool exists -- SKIPPED WITH A REASON if this package is read outside the repository,
#      rather than silently omitted;
#   8. the flip bound per headline number (`.github/tools`-free, offline): the fewest unit inversions
#      that could reverse each verdict, plus the bounds that are NOT derivable, which are reported as
#      such rather than estimated into a number;
#   9. the README's own numbers, each read against the artefact that owns it (so a figure in the
#      prose cannot drift from the run), with a mutation per figure as its liveness control;
#  10. the MANUSCRIPT's own typed numbers, section references and roadmap, each read against the
#      artefact that owns it -- the carrier the README check did not reach, and the one whose drift
#      reached review twice; a mutation per claim is its liveness control;
#  11. the sha256 of every artefact this package ships, printed as a block to copy.
#
# Exit status carries the verdict: 0 only when every step passes.  No network, CPU only.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
cd "$HERE" || exit 2

fail=0
verdict() {   # verdict <label> <rc>
  if [ "$2" -eq 0 ]; then printf '  %s: OK\n' "$1"; else printf '  %s: FAILED (exit %s)\n' "$1" "$2"; fail=1; fi
}

printf 'interpreter: %s (%s)\n' "$PY" "$("$PY" -c 'import sys; print(sys.version.split()[0])')"

printf '\n== 1. the stages and the canonical aggregate ==\n'
"$PY" canonical_runner.py
rc1=$?
verdict "stages and aggregate" "$rc1"

printf '\n== 2. liveness: every recomputation is corrupted and must notice ==\n'
"$PY" canonical_runner.py --selftest
rc2=$?
verdict "aggregate liveness" "$rc2"

printf '\n== 3. the external cell: 13 mutations, one per named check ==\n'
"$PY" external_cell_mutation_v1.py
rc3=$?
verdict "external-cell check liveness" "$rc3"

printf '\n== 4. the design freeze against the artefacts ==\n'
"$PY" freeze_check_v1.py
rc4=$?
verdict "design freeze" "$rc4"

printf '\n== 5. the manuscript assembles: placeholders, tables and citation keys ==\n'
"$PY" assemble.py
rc5=$?
verdict "manuscript assembly" "$rc5"

printf '\n== 6. the support limb: every citation occurrence against the sentence it sits in ==\n'
"$PY" support_read_v1.py --check
rc6=$?
verdict "support limb" "$rc6"

printf '\n== 7. the journal reference gate (>=100 entries in one section, every entry cited) ==\n'
GATE="../../.github/tools/refgate.py"
if [ -f "$GATE" ]; then
  "$PY" "$GATE" manuscript.md
  rc7=$?
  verdict "journal reference gate" "$rc7"
else
  printf '  journal reference gate: skipped -- %s is not present (this package is being read\n' "$GATE"
  printf '  outside the journal repository, where the gate lives); the gate was PASS at the head this\n'
  printf '  package was committed, on this manuscript, and its output is quoted in reference-check.md\n'
fi

printf '\n== 8. the flip bound per headline number (fewest unit inversions that reverse it) ==\n'
"$PY" flip_bound_v1.py
rc8=$?
verdict "flip bound" "$rc8"
"$PY" flip_bound_v1.py --selftest >/dev/null
rc8b=$?
verdict "flip bound liveness" "$rc8b"

printf '\n== 9. the README against the artefacts that own its numbers ==\n'
"$PY" readme_check_v1.py
rc9=$?
verdict "README figures" "$rc9"
"$PY" readme_check_v1.py --selftest >/dev/null
rc9b=$?
verdict "README figure liveness" "$rc9b"

printf '\n== 10. the manuscript typed numbers, against the artefacts that own them ==\n'
"$PY" manuscript_check_v1.py
rc10=$?
verdict "manuscript typed counts" "$rc10"
"$PY" manuscript_check_v1.py --selftest >/dev/null
rc10b=$?
verdict "manuscript typed counts liveness" "$rc10b"

printf '\n== 11. digests of the artefacts this package ships (copy this block, never type it) ==\n'
SHIPPED="canonical_results.json run.log anchor_smoke_results.json instrument_v0_results.json \
scorer_v0_results.json mechanism_v0_results.json paging_v1_results.json \
sufficiency_v1_results.json external_cell_v1_results.json \
external_cell_mutation_v1_results.json lambda_cert_v1_results.json canonical_runner.py \
assemble.py manuscript_part1.md manuscript_part2.md manuscript.md \
support_read_v1.py support_verdicts_v1.json support_read_v1.json support-read.md \
manuscript_part3.md references.md reference-check.md \
flip_bound_v1.py flip_bound_v1_results.json readme_check_v1.py"
for f in $SHIPPED; do
  if [ -f "$f" ]; then
    printf '%-40s sha256 %s\n' "$f" "$("$PY" -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$f")"
  else
    printf '%-40s MISSING\n' "$f"
    fail=1
  fi
done

printf '\nverdict: %s\n' "$([ "$fail" -eq 0 ] && echo OK || echo NOT READY)"
if [ "$fail" -eq 0 ]; then
  printf 'REPRODUCE: ALL GREEN\n'
else
  printf 'REPRODUCE: FAILED\n'
fi
exit "$fail"
