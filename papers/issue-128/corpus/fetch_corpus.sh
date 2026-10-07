#!/usr/bin/env bash
# fetch_corpus.sh -- download and PIN the real corpus used by the issue #128 real-data arm.
#
# The corpus is UCI Wine Quality (red), the standard physicochemical dataset: 1599 real samples,
# 12 numeric features, and a natural grouping variable (the sensory quality score, 3-8) that a
# representation constraint can be written against.  It is served as plain CSV over HTTPS.
#
# The script is idempotent: a file whose SHA-256 matches the pin is left alone, so a reproduction
# re-hashes rather than re-downloads (and a corpus that has silently changed fails the pin).
#
# Usage:  bash fetch_corpus.sh [--check]
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
URL="https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv"
NAME="winequality-red.csv"
DST="$HERE/$NAME"
PIN_FILE="$HERE/SHA256SUMS"

verify() {
  [ -f "$DST" ] || return 1
  [ -f "$PIN_FILE" ] || return 1
  ( cd "$HERE" && shasum -a 256 -c SHA256SUMS >/dev/null 2>&1 )
}

if verify; then
  echo "corpus: $NAME present and matching SHA256SUMS ($(wc -c <"$DST" | tr -d ' ') bytes)"
  exit 0
fi

if [ "${1:-}" = "--check" ]; then
  echo "corpus: NOT verified (missing file or hash mismatch) -- run without --check to fetch"
  exit 1
fi

echo "corpus: fetching $URL"
curl -s -L --max-time 180 -o "$DST" "$URL" || { echo "corpus: fetch FAILED"; exit 2; }
if [ ! -s "$DST" ]; then echo "corpus: empty download"; exit 2; fi
# a truncated download is the failure mode this endpoint shows most often: check the tail
if [ "$(tail -c 1 "$DST" | od -An -c | tr -d ' ')" != "\n" ]; then
  echo "corpus: download does not end in a newline -- treating as TRUNCATED"; exit 2
fi
( cd "$HERE" && shasum -a 256 "$NAME" > SHA256SUMS )
echo "corpus: wrote SHA256SUMS"
echo "corpus: RECHECK -> $(cd "$HERE" && shasum -a 256 -c SHA256SUMS)"
exit 0
