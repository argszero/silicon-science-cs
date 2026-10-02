#!/usr/bin/env bash
# Instrument driver for issue #114: every battery, every plant audit, every analysis.
#
# Exits nonzero if ANY step fails.  Deterministic, CPU-only, no network, no third-party
# dependency.  `reproduce.sh` calls this and then checks the committed artefacts.
set -u
cd "$(dirname "$0")"
fail=0
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP" __pycache__ _plant_scratch _plant_scratch_specs _plant_scratch_align _plant_scratch_decide' EXIT

run() {
  local name="$1"; shift
  echo "----- $name"
  if "$@" >"$TMP/$name.out" 2>&1; then
    tail -n 2 "$TMP/$name.out" | sed 's/^/    /'
  else
    echo "    FAILED (output follows)"; tail -n 15 "$TMP/$name.out" | sed 's/^/    /'; fail=1
  fi
}

# --- reference space, decisive run, and their audits --------------------------
run progspace      python3 progspace.py
run smoke_decide   python3 smoke_decide.py
run plant_decide   python3 plant_decide.py
run decide_a       python3 decide.py --json "$TMP/decide_a.json"
run decide_b       python3 decide.py --json "$TMP/decide_b.json"

echo "----- decide_determinism"
if cmp -s "$TMP/decide_a.json" "$TMP/decide_b.json"; then
  echo "    two runs byte-identical: $(shasum -a 256 "$TMP/decide_a.json" | cut -c1-16)…"
else
  echo "    RUNS DIFFER -- the decisive table is not deterministic"; fail=1
fi

# --- the Step 1-4 batteries, diagnoses and their own audits -------------------
run smoke_oracle  python3 smoke_oracle.py
run plant_audit   python3 plant_audit.py
run smoke_frontier python3 smoke_frontier.py
run plant_audit_specs python3 plant_audit_specs.py
run smoke_align   python3 smoke_align.py
run plant_audit_align python3 plant_audit_align.py
run diag_clauses  python3 diag_clauses.py
run region_mix    python3 region_mix.py
run alignment     python3 alignment.py

echo
if [ "$fail" -eq 0 ]; then echo "INSTRUMENT: ALL GREEN"; else echo "INSTRUMENT: FAILURES PRESENT"; fi
exit "$fail"
