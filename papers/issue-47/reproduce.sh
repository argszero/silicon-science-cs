#!/usr/bin/env bash
# Issue #47 -- one command reproduces every number this package claims.
#
#   bash reproduce.sh
#
# Steps, and what each one is for:
#   1. the nine stages (eight frozen, plus the certificate stage added by the F0b amendment),
#      then the canonical aggregate (canonical_runner.py), which RECOMPUTES
#      every cited number from the stage artefacts' primitives and cross-checks it against the value
#      the stage recorded about itself;
#   2. the liveness control -- each recomputation is corrupted in a throwaway copy and must notice;
#   3. the external cell's own check-liveness -- 13 mutations of the cell script, one per named check,
#      each of which must make exactly that check fail;
#   4. the design-freeze document against the artefacts -- 46 checks, including the digest table;
#   5. the manuscript assembly -- every measurement in the prose is a placeholder resolved out of the
#      artefacts (a placeholder that cannot be resolved, or a citation key with no reference entry,
#      fails the step), including the design table, which is rendered from the instrument artefact
#      rather than typed;
#   6. the SUPPORT limb of citation integrity -- every citation occurrence read against the sentence
#      it sits in, offline (the IDENTITY limb needs the network and is reported in reference-check.md);
#   7. the sha256 of every artefact this package ships, printed as a block to copy.
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

printf '\n== 7. digests of the artefacts this package ships (copy this block, never type it) ==\n'
SHIPPED="canonical_results.json run.log anchor_smoke_results.json instrument_v0_results.json \
scorer_v0_results.json mechanism_v0_results.json paging_v1_results.json \
sufficiency_v1_results.json external_cell_v1_results.json \
external_cell_mutation_v1_results.json lambda_cert_v1_results.json canonical_runner.py \
assemble.py manuscript_part1.md manuscript_part2.md manuscript.md \
support_read_v1.py support_verdicts_v1.json support_read_v1.json support-read.md"
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
