#!/usr/bin/env bash
#
# Re-verify every citation in `references.md` against an external record.
#
#     bash verify_refs.sh
#
# Needs network access, so it is run deliberately rather than on every reproduction.
# For each key in `refs_to_verify.tsv`:
#
#   doi    -> Crossref `api.crossref.org/works/<doi>`; the returned title decides.
#   arxiv  -> the paper's own abstract page (`arxiv.org/abs/<id>`), read from its
#             citation_* metadata.
#   title  -> Crossref bibliographic search; accepted only if the best hit's title
#             normalises to the candidate, otherwise the key is UNVERIFIED.
#
# It rewrites `references.md` (one entry per verified key, rendered from the record that
# was returned) and `reference-check.md` (one row per key: method, result, record found).
# A key that cannot be verified is dropped from `references.md`, which makes the manuscript
# check fail on "every cited key has an entry" -- deliberately: an unverifiable citation
# must never reach the manuscript silently.
#
# EXIT STATUS: 0 only if every key verified.

set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here"
PY="${PYTHON:-python3}"
echo "reference check via $PY (network required: api.crossref.org, arxiv.org)"
"$PY" verify_refs.py
