#!/usr/bin/env bash
# Issue #118 -- one-command reproduction.
#
#   bash reproduce.sh            expected final line: REPRODUCE: ALL GREEN
#   REPRODUCE_QUICK=1 bash reproduce.sh   skips only claim 1 (see the README)
#
# Network-free. Writes NOTHING inside this package: every check regenerates into a
# temporary directory and compares.
set -u
cd "$(dirname "$0")" || exit 1
if [ -z "${PY:-}" ]; then
  if /usr/bin/python3 -c "import numpy" 2>/dev/null; then PY=/usr/bin/python3
  else PY=python3; fi
fi
TMP="$(mktemp -d)"
FAIL=0
trap 'rm -rf "$TMP"' EXIT

step() { printf '\n== %s\n' "$1"; }
ok()   { printf '   OK   %s\n' "$1"; }
bad()  { printf '   FAIL %s\n' "$1"; FAIL=1; }
skip() { printf '   SKIP %s\n' "$1"; }

INSTR="spike_v0.py spike_v1.py model_v2.py model_v3.py probe_uniform.py canonical_runner.py"

step "0. build"
"$PY" -c "import sys, numpy; print('python', sys.version.split()[0], '/ numpy', numpy.__version__)" || exit 1
echo "   (recorded build: python 3.9.6 / numpy 2.0.2)"

# ---------------------------------------------------------------- claim 1
# The instrument suite is DETERMINISTIC: two independent full runs must be
# byte-identical in the merged artefact AND in the log. Both passes run in the SAME
# directory (a warning that prints its own path would otherwise differ by directory
# name -- a comparison artefact, not non-determinism).
mkdir -p "$TMP/run"
for f in $INSTR; do cp "$f" "$TMP/run/"; done
step "1. determinism: two independent runs of the instrument suite"
( cd "$TMP/run" && "$PY" canonical_runner.py > run1.log 2>&1 ) || bad "run 1 failed"
if [ ! -f "$TMP/run/canonical_results.json" ]; then bad "run 1 produced no artefact"; fi
cp "$TMP/run/canonical_results.json" "$TMP/art1.json"
cp "$TMP/run/run1.log" "$TMP/log1.txt"
if [ "${REPRODUCE_QUICK:-0}" = "1" ]; then
  skip "the second run (REPRODUCE_QUICK=1) -- claim 2 below still runs"
else
  ( cd "$TMP/run" && "$PY" canonical_runner.py > run2.log 2>&1 ) || bad "run 2 failed"
  if cmp -s "$TMP/art1.json" "$TMP/run/canonical_results.json"; then
    ok "canonical_results.json byte-identical across two independent runs"
  else bad "canonical_results.json is NOT deterministic"; fi
  if cmp -s "$TMP/log1.txt" "$TMP/run/run2.log"; then
    ok "run log byte-identical across two independent runs (same directory)"
  else bad "the run log differs between runs"; fi
fi

# ---------------------------------------------------------------- claim 2
# The COMMITTED artefact is what the code produces. A determinism check does not
# prove this: it compares a run against another run, not against the file shipped.
step "2. the committed artefact is what the code produces"
if cmp -s "$TMP/art1.json" canonical_results.json; then
  ok "committed canonical_results.json equals the regenerated artefact"
  echo "        sha256 $(shasum -a 256 canonical_results.json | cut -d' ' -f1)"
else
  bad "committed canonical_results.json differs from the regenerated artefact"
  diff <(head -40 canonical_results.json) <(head -40 "$TMP/art1.json") | head -10
fi

# ---------------------------------------------------------------- claim 3
step "3. the committed figures are views of the committed artefact"
mkdir -p "$TMP/fig"
cp make_figures.py plotlib.py canonical_results.json "$TMP/fig/"
( cd "$TMP/fig" && "$PY" make_figures.py > fig.log 2>&1 ) || bad "figure render failed"
for p in fig1_frontier fig2_ceiling fig3_inversion fig4_composition; do
  if cmp -s "figures/$p.png" "$TMP/fig/figures_draft/$p.png"; then
    ok "figures/$p.png byte-identical to the regenerated figure"
  else bad "figures/$p.png differs from the regenerated figure"; fi
done
if cmp -s "figures/manifest.json" "$TMP/fig/figures_draft/manifest.json"; then
  ok "figures/manifest.json byte-identical (the hashes are computed, not typed)"
else bad "figures/manifest.json differs"; fi

step "4. the committed manuscript is what the pipeline builds"
if "$PY" refs/refs_build.py render-check; then :; else bad "manuscript render mismatch"; fi

step "5. citation coverage, the citation guards, and the citation report"
if "$PY" refs/refs_build.py check; then :; else bad "coverage check failed"; fi
# 5b: reference-check.md is GENERATED from refs/curated.json + refs/verify.log. If a
# number in it were typed by hand, regenerating would change the file.
mkdir -p "$TMP/rep"
cp -r refs "$TMP/rep/refs"; cp manuscript.src.md "$TMP/rep/"
( cd "$TMP/rep" && "$PY" refs/refs_report.py > rep.log 2>&1 ) || bad "the citation report did not regenerate"
if cmp -s "reference-check.md" "$TMP/rep/reference-check.md"; then
  ok "reference-check.md byte-identical to its regeneration from the artefacts"
else bad "reference-check.md differs from what the artefacts generate"; fi
# 5c: the three properties the editorial returns named, read off the PRODUCT (offline, from
# committed artefacts): every entry names an author, every entry is its own paragraph, and every
# entry prints the YEAR its record carries -- not a curation placeholder. The year limb was added
# after the return of 2026-10-10, where a placeholder reached the printed entry as `((aut).`.
# These are rendering properties, so they are measured on manuscript.md as rendered, not on the
# source, where the newlines already exist. The entry ORDER is refs_build's own (`import
# refs_build`), so the check cannot drift from the renderer's ordering by re-deriving it.
"$PY" - <<'PYCHECK' || bad "the author component, the block form or the year component is defective"
import re, sys
sys.path.insert(0, "refs")
import refs_build as B
# The author component's shape is the journal gate's OWN class, copied from `.github/tools/
# refgate.py` with its source named: a family token of two or more letters (Unicode letters,
# apostrophes and hyphens -- `DeepSeek-AI` is one), closed by a comma and an initial. Writing a
# NARROWER class here would fire on healthy entries: the first draft of this check rejected
# `[53] DeepSeek-AI; Liu, A.; ...` because it did not admit a trailing hyphen, i.e. the check was
# narrower than the rule it mirrors -- the same defect class as the one this block exists to catch.
FAMILY = r"[^\W\d_](?:[^\W\d_]|['\u2019-]){1,}"
COMPONENT = re.compile(r"(?<![\w'\u2019-])(" + FAMILY + r")\s*,\s*[A-Z]\.")
SOLO = re.compile(r"^(" + FAMILY + r")\.\s*\(")
YEAR = re.compile(r"\((\d{4})\)")
entries, order, num, authors = B.load()
txt = open("manuscript.md").read()
lines = txt.splitlines()
start = max(i for i, l in enumerate(lines) if l.startswith("## References"))
sec = lines[start + 1:]
ents = [(i, l) for i, l in enumerate(sec) if re.match(r"^\s*\[\d{1,3}\]\s", l)]
assert len(ents) == len(order), "read %d entries for %d curated" % (len(ents), len(order))
for pos, (i, l) in enumerate(ents):
    bare = order[pos]                              # the renderer emits entries in this order
    assert pos == 0 or sec[i - 1].strip() == "", \
        "entry %r is not separated from the one above by a blank line" % l[:40]
    assert l.lstrip().startswith("[%d]" % num[bare]), \
        "entry at position %d prints %r where the numbering gives [%d]" % (pos, l[:12], num[bare])
    body = l.split("] ", 1)[1]
    assert COMPONENT.search(body) or SOLO.match(body), \
        "no author component at the entry position: %r" % l[:60]
    pub = (entries[bare].get("published") or "").strip()
    want = re.match(r"^(\d{4})", pub) if pub else None
    got = YEAR.search(l)
    if want:
        assert got and got.group(1) == want.group(1), \
            "entry %s prints year %r where the record gives %s" % (
                bare, got.group(1) if got else None, want.group(1))
    else:
        assert not got, "entry %s prints a year its record does not carry" % bare
print("   %d entries: each names an author, each is its own paragraph, each prints its record's year"
      % len(ents))
PYCHECK

# 5d: every number the §5.5 top-`k` sentence states is the ARTEFACT's own -- the sentence counted
# five `z` values over four cells once (the editorial return of 2026-10-10), so the list is read
# back against `canonical_results.json` rather than trusted.
"$PY" - <<'PYZ' || bad "the section-5.5 top-k z list is not the artefact's"
import json, re
W = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
zs = sorted(round(c["z"], 2) for c in json.load(open("canonical_results.json"))["steps"]["model_v2"]["topk"])
m = re.search(r"\*\*`z` = ([0-9., ]+?)\*\* over the (\w+) `\(E, T, k\)` cells", open("manuscript.md").read())
assert m, "the section-5.5 z sentence was not found in manuscript.md"
got = sorted(float(x) for x in m.group(1).replace(" ", "").rstrip(",").split(","))
assert got == zs, "the manuscript lists z = %s of %d cells; the artefact holds %s of %d" % (
    got, len(got), zs, len(zs))
assert W[m.group(2)] == len(zs), "the sentence says %r cells but the artefact holds %d" % (m.group(2), len(zs))
print("   section 5.5: z = %s over %d cells, read back from model_v2.topk" % (got, len(zs)))
PYZ

step "6. the manuscript's decisive numbers reappear from the code"
# (a) the certificate numbers, from spike_v1's OWN stdout (48 s), not from a summary
mkdir -p "$TMP/v1"
cp spike_v0.py spike_v1.py "$TMP/v1/"
( cd "$TMP/v1" && "$PY" spike_v1.py > v1.log 2>&1 ) || bad "spike_v1 failed"
if grep -q "worst |A-B| relative = 6.36e-13" "$TMP/v1/v1.log"; then
  ok "the two exact routes agree to 6.36e-13 (registered bar 1e-3)"
else bad "the two-route certificate number was not found"; fi
if grep -q "max |z| over 5 cells = 2.17" "$TMP/v1/v1.log"; then
  ok "the sampler is scored: max |z| = 2.17 over 5 cells"
else bad "the Monte-Carlo z line was not found"; fi
# (b) the headline numbers, read from the run of the whole suite (step 1's log)
head_log="$TMP/log1.txt"
check_head() { if grep -qF "$1" "$head_log"; then ok "$2"; else bad "$2 (line not found: $1)"; fi; }
check_head "5 of the mu<=16 cells need C > 1.25 with a PERFECTLY UNIFORM router" \
           "the ceiling: 5 of 5 tested mu<=16 cells need C > 1.25 with the ideal router"
check_head "D(C=1.25) = 0.298928 at mu=1" "the constant accepts 29.8928% at decode-like mu=1"
check_head "8.28985e-05 at mu=128" "and 8.29e-05 at training load mu=128"
check_head "max 0.0454" "the closed form meets the 5% bar on mu>=8 (max 4.54%)"
check_head "first-decile share 0.0000, last-decile share 0.1941" \
           "the dropped set is position-biased (0.00% first decile, 19.41% last)"
check_head "8 production configurations placed on the curve" "8 production configurations placed"
check_head "uniform C_min floor 1.1635" "the uniform floor the measured router converges to"
check_head "minimum 1.37" "the measured router's best C_min under balancing"

printf '\n'
if [ "$FAIL" -eq 0 ]; then
  echo "REPRODUCE: ALL GREEN"
else
  echo "REPRODUCE: FAILED"
fi
exit "$FAIL"
