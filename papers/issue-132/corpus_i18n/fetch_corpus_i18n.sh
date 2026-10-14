#!/bin/bash
# Fetch the pinned non-English corpus: Project Gutenberg plain-text books (public domain),
# Italian / Spanish / French / German.  URLs are stable and each download is verified by
# sha256 at fetch time.  NOT needed to reproduce -- the texts ship in this directory.
set -e
cd "$(dirname "$0")"   # this script ships inside corpus_i18n/
# id:lang -- the language tag is only a name; the instrument reads the text, not the label.
BOOKS="1012:it 21425:it 47786:it 49626:it 2000:es 15532:es 29640:es 29731:es 67248:es 14155:fr 17989:fr 2229:de"
for entry in $BOOKS; do
  id="${entry%%:*}"; lang="${entry##*:}"
  f="pg${id}_${lang}.txt"
  if [ ! -f "$f" ]; then
    curl -sL --max-time 60 "https://www.gutenberg.org/cache/epub/${id}/pg${id}.txt" -o "$f"
  fi
  printf "%s  %s  %8d B\n" "$(shasum -a 256 "$f" | cut -c1-16)" "$f" "$(wc -c < "$f")"
done
# The sums are BARE filenames and are verified FROM THIS DIRECTORY:
#   ( cd corpus_i18n && shasum -a 256 -c SHA256SUMS )
shasum -a 256 pg*.txt > SHA256SUMS
