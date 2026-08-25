#!/usr/bin/env bash
# One-command reproduction — issue #7 "Type-Evident Code".
#
#   bash reproduce.sh
#
# 1. clones the 7 corpus packages at their pinned commits into ./.corpus/
# 2. runs the canonical analyzer (reproduce.py, stdlib-only, deterministic)
# 3. diffs the fresh output against the committed expected output
#    (expected_output/manuscript_results.txt) — exit 0 iff identical.
#
# Requires: bash, git, python3 >= 3.10 (stdlib only, no pip packages).
set -euo pipefail
cd "$(dirname "$0")"

CORPUS_DIR="${CORPUS_DIR:-.corpus}"
OUT_TMP=".repro_out.txt"

rm -rf "$CORPUS_DIR" "$OUT_TMP"
mkdir -p "$CORPUS_DIR"

clone() {
  local pkg="$1" url="$2" commit="$3"
  echo "  cloning $pkg @ $commit"
  git clone --quiet "$url" "$CORPUS_DIR/$pkg"
  git -C "$CORPUS_DIR/$pkg" checkout --quiet "$commit"
}

echo "== [1/3] fetching corpus at pinned commits =="
clone click     https://github.com/pallets/click.git         2c8cd3ac958a
clone dateutil  https://github.com/dateutil/dateutil.git     48bd1af97e71
clone flask     https://github.com/pallets/flask.git         d318b6834711
clone gunicorn  https://github.com/benoitc/gunicorn.git      36f2a3c1b80d
clone httpie    https://github.com/jakubroztocil/httpie.git  5b604c37c6c6
clone tqdm      https://github.com/tqdm/tqdm.git             96f2e60e4584
clone typer     https://github.com/fastapi/typer.git         9a7b2e83f6b6

echo "== [2/3] running canonical analyzer =="
python3 reproduce.py --corpus "$CORPUS_DIR" --check-commits > "$OUT_TMP" 2>&1

echo "== [3/3] diffing against expected output =="
if diff -u expected_output/manuscript_results.txt "$OUT_TMP"; then
  echo "REPRODUCTION OK: fresh output identical to expected_output/manuscript_results.txt"
  rm -f "$OUT_TMP"
else
  echo "REPRODUCTION MISMATCH — fresh output saved to $OUT_TMP; diff above."
  exit 1
fi
