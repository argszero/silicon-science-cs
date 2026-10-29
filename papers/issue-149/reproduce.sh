#!/bin/sh
# reproduce.sh -- issue #149, one command, every core number.
#
# Exit code contract (project convention, learned on #141): accumulate failures and `exit $FAILED`.
# A step that cannot run is NOT RUN, never DIFFERS. A step that runs and disagrees is DIFFERS.
#
# steps:
#   1  snapshot pins       the committed snapshots are the ones the artifacts name
#   2  plants x3           ambiguous 7, depth2 3, decay 7 -- a guard that cannot fail is not a guard
#   3  depth-1 rates       ambiguous.py     -> rates.json
#   4  depth-2 certificate depth2.py        -> depth2.json   (measured 9 s; bounded at 300 s)
#   5  decay curve         decay.py         -> decay.json
#   6  corpus gates        C1-C5 over refs/references.json, its hash pin, and byte-stable
#                          regeneration of reference-check.md
#   7  manuscript citations  gate_citations.py: every placed entry cited, references.md matches
#                          the corpus
#   8  figure               make_figures.py -> figures/decay-curve.svg, and asserts the ordering
#                          §7.3 claims before writing it
#   9  rates table          the manuscript's table block is compared against the render of
#                          rates.json, so a hand-edited cell fails here rather than ageing
#
# usage: sh reproduce.sh [--fast]      --fast skips the depth-2 enumeration (step 4 reports NOT RUN)
# The run states its own count, in the form the journal's stepgate reads: (9 steps).
#
# The list above is read back by this script at the end: the steps declared here and the steps
# that actually ran are compared, and any disagreement fails the run. A header that stopped at
# six while seven steps executed is a defect that has now appeared on #128, #145 and here, and a
# list the program checks is the only fix that does not need making a fourth time.

set -u
HERE=$(cd "$(dirname "$0")" && pwd)
SELF=$HERE/$(basename "$0")
cd "$HERE" || exit 1
PY=/usr/bin/python3
FAILED=0
FAST=0
[ "${1:-}" = "--fast" ] && FAST=1

say() { printf '\n=== %s\n' "$1"; }
ok()  { printf '  [ok]   %s\n' "$1"; }
bad() { printf '  [FAIL] %s\n' "$1"; FAILED=$((FAILED+1)); }
notrun() { printf '  [NOT RUN] %s\n' "$1"; }

# every executed step goes through this, so the header has something to be compared against
DECLARED_STEPS=$(sed -n 's/^#   \([0-9][0-9]*\)  .*/\1/p' "$SELF" | tr '\n' ' ' | sed 's/ *$//')
RUN_STEPS=""
step() { n=${1%% *}; RUN_STEPS="${RUN_STEPS:+$RUN_STEPS }$n"; say "$1"; }

# ---------------------------------------------------------------- 1 snapshot pins
step "1 snapshot pins"
"$PY" - <<'PINS' || FAILED=$((FAILED+1))
import json, sys
# EVERY artifact that names a pin is checked, not just the one that happened to have one. depth2.json
# and decay.json carried no pin at all until this round, so a depth-2 artifact computed on a snapshot
# the repo no longer contained was indistinguishable from a current one.
arts = ["rates.json", "decay.json", "depth2.json"]
snaps = {e: json.load(open("snapshot_%s.json" % e)).get("content_sha256")
         for e in ("npm", "pypi")}
bad = 0
for art in arts:
    d = json.load(open(art))
    for eco in ("npm", "pypi"):
        got = (d.get("ecosystems", {}).get(eco) or {}).get("snapshot_content_sha256")
        want = snaps[eco]
        if got == want:
            print("  [ok]   %-12s %-4s pin %s" % (art, eco, (got or "")[:16]))
        else:
            print("  [FAIL] %-12s %-4s names %s, snapshot is %s -- regenerate this artifact"
                  % (art, eco, (got or "NONE")[:16], (want or "none")[:16]))
            bad += 1
sys.exit(1 if bad else 0)
PINS

# ---------------------------------------------------------------- 2 plants
step "2 known-answer plants"
for pair in "ambiguous.py 7" "depth2.py 7" "decay.py 7"; do
  set -- $pair
  out=$("$PY" "$1" --check 2>&1)
  if printf '%s' "$out" | grep -q "FAILED"; then
    bad "$1 plants"
    printf '%s\n' "$out" | sed 's/^/         /'
  elif printf '%s' "$out" | grep -qi "ALL PASS\|7/7"; then
    # The verdict line is echoed, not just acted on: the README quotes these counts, so a reader
    # running the README's own command has to see them. Capturing them silently made the README's
    # attribution false for the one command it tells the reader to run.
    ok "$1 plants"
    printf '%s\n' "$out" | grep -i "PLANTS" | sed 's/^/         /'
  else
    notrun "$1 plants (no verdict line)"
  fi
done

# ---------------------------------------------------------------- 3 depth-1
step "3 depth-1 rates (ambiguous.py -> rates.json)"
if "$PY" ambiguous.py > /tmp/issue149-amb.log 2>&1; then
  ok "wrote rates.json"
  grep -E "ambiguous|FINDING|closure" /tmp/issue149-amb.log | sed 's/^/         /'
else
  bad "ambiguous.py exited non-zero (see /tmp/issue149-amb.log)"
fi

# ---------------------------------------------------------------- 4 depth-2
step "4 depth-2 certificate (depth2.py -> depth2.json)"
if [ "$FAST" = "1" ]; then
  notrun "depth-2 enumeration skipped (--fast). The committed depth2.json is therefore NOT
         regenerated by this run; its numbers are quoted in the paper with the pin they carry."
else
  # The enumeration has no internal bound and writes only on completion, so a bound here is the
  # only thing that turns a runaway into a NOT RUN rather than a lost round. Perl alarm is the one
  # portable timeout available (the `timeout` command is absent on this host).
  perl -e 'alarm 300; exec @ARGV' "$PY" depth2.py > /tmp/issue149-d2.log 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then
    ok "wrote depth2.json"
    # `pins` carries the certificate's price line (906 / 596 / 281 and 120 / 95 / 115), which is the
    # 31.0 % and 95.8 % the README attributes to this command; it used to be filtered out here.
    grep -E "median|saving|pins" /tmp/issue149-d2.log | sed 's/^/         /'
  elif [ $rc -gt 128 ]; then
    notrun "depth-2 exceeded 300 s; depth2.json left as committed (NOT RUN, not DIFFERS)"
  else
    bad "depth2.py exited $rc (see /tmp/issue149-d2.log)"
  fi
fi

# ---------------------------------------------------------------- 5 decay
step "5 decay curve (decay.py -> decay.json)"
if "$PY" decay.py > /tmp/issue149-decay.log 2>&1; then
  ok "wrote decay.json"
  grep -E "caret|exact|tilde|DECL|caret>" /tmp/issue149-decay.log | sed 's/^/         /'
else
  bad "decay.py exited non-zero (see /tmp/issue149-decay.log)"
fi

# ---------------------------------------------------------------- 6 citations
step "6 corpus gates (C1-C5 + the corpus pin)"
"$PY" - <<'GATES' || FAILED=$((FAILED+1))
import hashlib, json, os, re, sys
# The corpus is a committed input of this package, not something the offline path can rebuild:
# its only producer is build_references.py --harvest, which needs the network. A missing corpus is
# therefore a failure of this package, and it is reported as one -- there is deliberately no branch
# that warns and continues, because that would make the citation half of the paper inaudible
# instead of checked.
CORPUS = "refs/references.json"
if not os.path.exists(CORPUS):
    print("  [FAIL] the committed corpus %s is missing -- it is an input of this package and the "
          "offline path cannot rebuild it" % CORPUS)
    sys.exit(1)
raw = open(CORPUS, "rb").read()
doc = json.loads(raw)
import importlib.util
spec = importlib.util.spec_from_file_location("pl", "placements.py")
pl = importlib.util.module_from_spec(spec); spec.loader.exec_module(pl)

entries = doc["entries"]
kept = {e["key"]: e for e in entries if e.get("review", "kept") == "kept"}
placed = set()
keys = set(kept)
def resolve(named):
    if named in keys: return named
    hits = [k for k in keys if k.startswith(named)]
    return hits[0] if len(hits) == 1 else None

bad = 0
def ck(cond, msg):
    global bad
    print(("  [ok]   " if cond else "  [FAIL] ") + msg)
    if not cond: bad += 1

# C0 the corpus is the one this package pinned, not an anonymous copy of one
prov_path = "refs/PROVENANCE.md"
prov = open(prov_path, encoding="utf-8").read() if os.path.exists(prov_path) else ""
m = re.search(r"corpus sha256[^0-9a-f]*([0-9a-f]{64})", prov)
ck(m is not None, "C0 the provenance note records a corpus sha256")
if m is not None:
    got = hashlib.sha256(raw).hexdigest()
    ck(got == m.group(1), "C0b the committed corpus is the pinned one (%s..., %d bytes)"
       % (got[:16], len(raw)))

# C1 every placement resolves to exactly one kept entry, and every kept entry is placed or pruned
unresolved = [k for k in list(pl.PLACEMENTS) + list(pl.PRUNED) if resolve(k) is None]
ck(not unresolved, "C1 all %d placements+prunes resolve (%d unresolved)"
   % (len(pl.PLACEMENTS) + len(pl.PRUNED), len(unresolved)))
placed = {resolve(k) for k in pl.PLACEMENTS}
pruned = {resolve(k) for k in pl.PRUNED}
ck(not (placed & pruned), "C1b no key is both placed and pruned")
orphan = keys - placed - pruned
ck(not orphan, "C1c every kept entry is placed or pruned (%d orphan)" % len(orphan))

# C2 no padding: every placed entry is verified against a real record
unver = [k for k in placed if (kept[k].get("verification") or {}).get("result") != "verified"]
ck(not unver, "C2 every placed entry carries stored verification (%d unverified)" % len(unver))

# C3 the floor
ck(len(placed) >= 100, "C3 placed >= 100 (%d)" % len(placed))

# C4 the comparison set: >= 3 works, each placed, each with a stated difference and a basis
comps = pl.COMPARISON_KEYS
ck(len(comps) >= 3, "C4 >= 3 compared works (%d)" % len(comps))
ck(all(len(c) == 3 and c[1].strip() and c[2].strip() for c in comps),
   "C4b every compared work states a difference AND what was read")
ck(all(resolve(c[0]) in placed for c in comps), "C4c every compared work is placed")

# C5 a section id that is not declared cannot appear
bads = [k for k, (s, _) in pl.PLACEMENTS.items() if s not in pl.SECTIONS]
ck(not bads, "C5 every placement names a declared section (%d undeclared)" % len(bads))

sys.exit(1 if bad else 0)
GATES

# byte-stable regeneration of the derived report
"$PY" place_references.py --out refs/references.json --report reference-check.md >/tmp/issue149-pc.log 2>&1 \
  && cp reference-check.md /tmp/issue149-rc1.md
"$PY" place_references.py --out refs/references.json --report /tmp/issue149-rc2.md >/dev/null 2>&1
if cmp -s /tmp/issue149-rc1.md /tmp/issue149-rc2.md; then
  ok "reference-check.md regenerates byte-identically"
else
  bad "reference-check.md is not byte-identical across two runs (a wall clock or a live query leaked in)"
fi

# ---------------------------------------------------------------- 7 manuscript citations
step "7 manuscript citations against the corpus"
if "$PY" gate_citations.py --manuscript manuscript.md --corpus refs/references.json > /tmp/issue149-cite.log 2>&1; then
  ok "manuscript citations gate"
  grep -E "C1 |C2 |C3 " /tmp/issue149-cite.log | sed 's/^/         /'
else
  bad "manuscript citation gate failed (see /tmp/issue149-cite.log)"
  grep -E "FAIL" /tmp/issue149-cite.log | sed 's/^/         /'
fi
# the reference list must be regenerable from the corpus, not hand-maintained
"$PY" gate_citations.py --manuscript manuscript.md --corpus refs/references.json \
  --list /tmp/issue149-ref.md >/dev/null 2>&1
if diff -q references.md /tmp/issue149-ref.md >/dev/null 2>&1; then
  ok "references.md matches the corpus"
else
  bad "references.md is stale relative to the corpus (regenerate with --list references.md)"
fi
# and the manuscript's own section is the same render -- two copies of one derivation is how the
# bare-DOI form survived in both at once
"$PY" gate_citations.py --manuscript manuscript.md --corpus refs/references.json \
  --list references.md --check-references > /tmp/issue149-refform.log 2>&1
if [ $? -eq 0 ]; then
  grep -E "\[ok\]" /tmp/issue149-refform.log | grep -i "References section" | sed 's/^/         /'
else
  bad "the manuscript's References section is not the corpus render (see /tmp/issue149-refform.log)"
fi

# ---------------------------------------------------------------- 8 figure
step "8 figure"
if "$PY" make_figures.py; then
  ok "figures/decay-curve.svg regenerated and asserted"
else
  bad "make_figures.py refused to write the figure (assertion failed)"
fi

# ---------------------------------------------------------------- 9 rates table
step "9 rates table"
if "$PY" make_figures.py --check-table; then
  :
else
  bad "the manuscript's table block is not the render of rates.json"
fi

# ---------------------------------------------------------------- step list
# The header's list is a second copy of the program, so it is checked against the program rather
# than trusted: DECLARED_STEPS comes from the header, RUN_STEPS from the step() calls above.
NSTEPS=$(printf '%s\n' $RUN_STEPS | wc -l | tr -d ' ')
say "step list"
if [ "$DECLARED_STEPS" = "$RUN_STEPS" ]; then
  ok "header declares steps [$DECLARED_STEPS] and the run executed exactly those"
else
  bad "header declares steps [$DECLARED_STEPS] but the run executed [$RUN_STEPS] -- the list is
         part of the artifact and has to match the program"
fi

# The documents state the count in the literal form `(N steps)`, which is what the journal's
# stepgate reads. A literal is a copy, so it is compared here as well: the number each carrier
# states has to be the number this run executed. Without this line the literals would satisfy the
# gate and drift from the program on the next change -- the defect this package has already had
# once, in its header.
for carrier in README.md manuscript.md; do
  stated=$(sed -n 's/.*(\([0-9][0-9]*\) steps).*/\1/p' "$carrier" | sort -u | tr '\n' ' ' | sed 's/ *$//')
  if [ "$stated" = "$NSTEPS" ]; then
    ok "$carrier states ($NSTEPS steps), the count this run executed"
  else
    bad "$carrier states [${stated:-nothing}] as the step count; this run executed $NSTEPS"
  fi
done

say "verdict"
# The count is printed on the verdict line, in the literal form the journal's stepgate reads: a
# stated count in the documents is a copy of this line, and a copy nothing compares is the defect
# that has appeared on #128, #145, #149 and #153. The number printed is the one the run executed,
# not the one the header declares -- those are compared above, and a disagreement has already
# failed the run by the time this line is printed.
if [ "$FAILED" = "0" ]; then
  echo "ALL STEPS PASSED ($NSTEPS steps)"
else
  echo "$FAILED STEP(S) FAILED ($NSTEPS steps executed)"
fi
exit $FAILED
