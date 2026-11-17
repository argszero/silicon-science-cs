#!/bin/sh
# fetch_corpus.sh -- retrieve the 1M corpus tier B needs, and verify it.
#
# The corpus is 501 MB and cannot be committed; the committed fixture (1.8 MB) covers tier A.
# The URL, the byte count and the sha256 are pinned here so that "the data changed" and "the code
# is wrong" cannot be confused with one another. A byte-count mismatch or a hash mismatch is a
# hard failure: a corpus that does not match the pin is not the corpus this package measured.
#
#   ./fetch_corpus.sh            # download into corpus/ if absent, then verify
#   ./fetch_corpus.sh --check    # verify only (no download); exit 1 if absent or wrong
set -eu

URL="http://ann-benchmarks.com/sift-128-euclidean.hdf5"
SHA="dd6f0a6ed6b7ebb8934680f861a33ed01ff33991eaee4fd60914d854a0ca5984"
BYTES=525128288
DEST_DIR="corpus"
DEST="$DEST_DIR/sift-128-euclidean.hdf5"

verify() {
    [ -f "$DEST" ] || { echo "ABSENT: $DEST"; return 1; }
    got_bytes=$(wc -c < "$DEST" | tr -d ' ')
    if [ "$got_bytes" != "$BYTES" ]; then
        echo "SIZE MISMATCH: $DEST is $got_bytes bytes, pinned $BYTES"
        return 1
    fi
    got_sha=$(shasum -a 256 "$DEST" | cut -d' ' -f1)
    if [ "$got_sha" != "$SHA" ]; then
        echo "SHA256 MISMATCH: $DEST has $got_sha, pinned $SHA"
        return 1
    fi
    echo "OK: $DEST ($BYTES bytes, sha256 verified)"
    return 0
}

if [ "${1:-}" = "--check" ]; then
    verify
    exit $?
fi

if verify; then
    exit 0
fi

mkdir -p "$DEST_DIR"
echo "fetching $URL"
echo "  -> $DEST ($BYTES bytes)"
# A failed or truncated transfer must not leave a file that looks like a corpus: fetch to a
# temporary name and move it into place only after the hash matches.
curl -fL --retry 3 -o "$DEST.part" "$URL"
mv "$DEST.part" "$DEST"
verify
