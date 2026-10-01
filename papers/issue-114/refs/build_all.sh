#!/usr/bin/env bash
# The reference pipeline, in ORDER (each step's output is the next step's input):
#
#   harvest.py    -- topic queries against Crossref and arXiv, cached under refs/raw/
#   dump.py       -- flatten the caches into candidates.json (everything here EXISTS)
#   build_refs.py -- named candidates -> Crossref lookup -> screen by title overlap
#   select.py     -- the human decision: reject near-misses WITH A REASON
#   recent.py     -- merge the relevant harvested (arXiv) records by identifier
#   verify_refs.py-- re-query EVERY entry by its own identifier; write the two committed files
#
# `select.py` rebuilds selection.json from scratch, so `recent.py` must follow it.
set -eu
cd "$(dirname "$0")"
python3 dump.py >/dev/null
python3 build_refs.py >/dev/null
python3 select.py     | head -1
python3 recent.py     | head -1
python3 verify_refs.py | tail -3
