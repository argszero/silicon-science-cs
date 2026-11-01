#!/bin/sh
# The committed reference-check.md must be exactly what the stored verification state renders.
# If this fails, the report has drifted from the state it claims to be a function of.
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE" || exit 1
PY=${PY:-/usr/bin/python3}
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
cp reference-check.md "$TMP" || exit 1
"$PY" place_refs.py --render-only >/dev/null || exit 1
if cmp -s reference-check.md "$TMP"; then
    echo "   reference-check.md regenerates byte-identically"
    exit 0
fi
echo "   MISMATCH: reference-check.md is not what placement.json renders"
exit 1
