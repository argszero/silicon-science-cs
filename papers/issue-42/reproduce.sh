#!/usr/bin/env bash
# One-command reproduction for issue #42.
#
#   bash reproduce.sh
#
# Runs the four instruments in an isolated build directory, compares their output with the
# committed artefacts, verifies every calibration quote against the committed evidence, and
# asserts every number quoted in the manuscript against the artefact that produced it.
#
# Expected final line: "REPRODUCE: ALL GREEN".
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
BUILD="$(mktemp -d)"

# Preflight: the instruments import numpy (derived from the source, not from memory).
# Pick an interpreter that has it; fail with the requirement if none does.
pick_python() {
  for c in "${PYTHON:-}" python3 /usr/bin/python3; do
    [ -n "$c" ] || continue
    if command -v "$c" > /dev/null 2>&1 && "$c" -c "import numpy" > /dev/null 2>&1; then
      echo "$c"; return 0
    fi
  done
  return 1
}
PY="$(pick_python)" || {
  echo "FATAL: no interpreter with numpy found."
  echo "Required: python3 with numpy (the instruments); matplotlib is needed only for figures."
  echo "Hint: python3 -m pip install --user numpy   or set PYTHON=/path/to/python3"
  exit 1
}
echo "interpreter: $PY ($("$PY" -c 'import sys; print(sys.version.split()[0])'))"
trap 'rm -rf "$BUILD"' EXIT

echo "== 1. instruments (isolated build dir) =="
cp instruments/instrument_v*.py "$BUILD/"
cp artefacts/calibration_dossier.json "$BUILD/"
cp -R evidence "$BUILD/"
( cd "$BUILD" && for v in 0 1 2 3; do
    printf '   instrument_v%s ... ' "$v"
    "$PY" "instrument_v$v.py" > /dev/null
    echo "ran"
  done )

echo "== 2. compare produced artefacts with committed ones =="
"$PY" - "$BUILD" "$ROOT" <<'PYEOF'
import hashlib, json, os, sys
build, root = sys.argv[1], sys.argv[2]
def canon(p):
    return hashlib.sha256(json.dumps(json.load(open(p, encoding="utf-8")),
                                     sort_keys=True).encode()).hexdigest()
ok = True
for v in "0123":
    name = "results_v%s.json" % v
    a = canon(os.path.join(build, name))
    b = canon(os.path.join(root, "artefacts", name))
    same = a == b
    ok &= same
    print("   %-18s %s  %s" % (name, "IDENTICAL" if same else "DIFFERS", b[:20]))
sys.exit(0 if ok else 1)
PYEOF

echo "== 3. calibration quotes vs committed evidence =="
"$PY" verify_quotes.py

echo "== 4. manuscript numbers vs artefacts =="
"$PY" assemble.py > /dev/null
"$PY" trace_check.py
"$PY" validate.py | tail -2

echo
echo "REPRODUCE: ALL GREEN"
