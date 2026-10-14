#!/bin/bash
# Fetch the pinned real-text corpus: Project Gutenberg plain-text books (public domain).
# URLs are stable and each download is verified by sha256 at fetch time.
set -e
cd "$(dirname "$0")"   # this script ships inside corpus/
IDS="${IDS:-2701 1342 98 1661 84 74 345 76}"
for id in $IDS; do
  f="pg$id.txt"
  if [ ! -f "$f" ]; then
    curl -sL --max-time 60 "https://www.gutenberg.org/cache/epub/$id/pg$id.txt" -o "$f"
  fi
  printf "%s  %s  %8d B\n" "$(shasum -a 256 "$f" | cut -c1-16)" "$f" "$(wc -c < "$f")"
done
# The sums are BARE filenames and are verified FROM THIS DIRECTORY:
#   ( cd corpus && shasum -a 256 -c SHA256SUMS )
shasum -a 256 pg*.txt > SHA256SUMS
