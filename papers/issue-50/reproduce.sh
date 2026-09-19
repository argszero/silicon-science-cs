#!/usr/bin/env bash
# Issue #50 -- one command reproduces every number, figure and claim this package makes.
#
#   bash reproduce.sh          # every step: the twelve sweeps, then the manuscript layer
#   bash reproduce.sh fast     # the four sweeps that finish in seconds (a quick verdict, declared as
#                              # a partial run -- it is NOT the reproduction claim of section 6.1)
#
# The steps, and what each one is for:
#   1. the twelve sweeps REBUILT from the command each artefact's own recorded parameters imply
#      (rebuild_artefacts_v1.py), each compared byte for byte with the committed artefact -- the
#      package's strongest claim, so it is the first step;
#   2. the liveness of that comparison: a rebuilt file must be reported identical and a file whose
#      bytes have moved must be reported different (a comparison that can only say "same" has never
#      been tested);
#   3. the assembly: every measurement in the prose is a placeholder resolved out of the artefacts,
#      and a placeholder that cannot be resolved fails the step.  The collector that reads QUANTIFIED
#      sentences -- a ratio must rest on two independent bindings of one declared domain, and a
#      declared count may not sit unquoted while the sentence types its numeral -- is part of this
#      step's build, so its three branches get the same liveness control as every other check here;
#   4. the two bibliography writers, each against its own object (display fields, and the rendered
#      `## References` section), plus refs_order.json against the body's first-use numbering;
#   5. the reference-check report, re-rendered from the committed verification artefact: byte for byte
#      the committed report, which is what makes that report a rendering rather than a copy.  One line
#      of it is a coordinate and not a property -- the date the verification was taken -- and the
#      renderer takes that as an argument; this step supplies the coordinate the committed report
#      declares, so the comparison is about the rendering rather than about the day it is read.  Every
#      other line must match, including the gate's window, which is read live from the manuscript;
#   6. the journal's own citation gate (`.github/tools/refgate.py`) -- SKIPPED WITH A REASON where
#      this package is read as a path-limited export that carries no `.github/`, never silently;
#   7. the journal's link gate over the tracked markdown carriers (broken=0), same skip rule;
#   8. the four figures, regenerated from the artefacts and compared byte for byte, with the liveness
#      control that plants one change per figure;
#   9. the manuscript's own claims -- the registered verdicts against the artefacts that decided them,
#      the section references, the figures' reachability and the headline measurements that must not
#      be typed into the prose -- plus its own liveness control;
#  10. the README's own numbers, each read against the object that owns it (the evidence's file count,
#      the instrument's module count, the reference layer, the figures, the sweeps), with one planted
#      defect per claim as its liveness control;
#  11. the sha256 of every file this package ships, printed as a block to copy rather than to type.
#
# Exit status carries the verdict: 0 only when every step passes.  Steps 1-2 are CPU-only and need no
# network; step 5 re-renders an offline report; steps 6-7 read the journal's tools from this tree.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
cd "$HERE" || exit 2

SCRATCH=".repro-scratch"
fail=0
skip=0
verdict() {   # verdict <label> <rc>
  if [ "$2" -eq 0 ]; then printf '  %s: OK\n' "$1"; else printf '  %s: FAILED (exit %s)\n' "$1" "$2"; fail=1; fi
}

printf 'interpreter: %s (%s)\n' "$(command -v "$PY")" "$("$PY" -c 'import sys; print(sys.version.split()[0])')"
printf 'package: %s\n' "$HERE"

rm -rf "$SCRATCH"; mkdir -p "$SCRATCH"

printf '\n== 1. the sweeps, rebuilt from the command each artefact implies, and byte-compared ==\n'
if [ "${1:-}" = "fast" ]; then
  PARTIAL="--only $("$PY" -c 'import rebuild_artefacts_v1 as r; print(",".join(r.FAST))')"
  printf '  PARTIAL RUN: the four sweeps that finish in seconds (%s)\n' "${PARTIAL#--only }"
  # shellcheck disable=SC2086
  "$PY" rebuild_artefacts_v1.py --rebuild "$SCRATCH/rebuild" $PARTIAL
else
  "$PY" rebuild_artefacts_v1.py --rebuild "$SCRATCH/rebuild"
fi
rc1=$?
verdict "instrument sweeps" "$rc1"

printf '\n== 2. liveness: the comparison must be able to report a difference ==\n'
"$PY" rebuild_artefacts_v1.py --selftest | tail -3
rc2=${PIPESTATUS[0]}
verdict "sweep-comparison liveness" "$rc2"

printf '\n== 3. the manuscript assembles from the artefacts ==\n'
"$PY" assemble.py --check | tail -4
rc3a=${PIPESTATUS[0]}
"$PY" assemble.py --selftest | tail -1
rc3b=${PIPESTATUS[0]}
rc3=$(( rc3a + rc3b ))
verdict "manuscript assembly and liveness" "$rc3"

printf '\n== 4. the bibliography: both writers against their own object, and the citation order ==\n'
"$PY" refs_build_display.py --check | tail -2
rc4a=${PIPESTATUS[0]}
"$PY" refs_render.py --check | tail -2
rc4b=${PIPESTATUS[0]}
rc4=$(( rc4a + rc4b ))
verdict "bibliography writers" "$rc4"

printf '\n== 5. the reference-check report, re-rendered from the verification artefact ==\n'
# The committed bytes are held in the scratch copy FIRST, and compared with the render afterwards:
# `git status` cannot answer this question, because the whole package is untracked in this tree until
# it is committed, so "untracked" would have read as "changed" whatever the render produced.
cp reference-check.md "$SCRATCH/reference-check.before.md"
TAKEN="$(sed -n 's/^- verification taken: \([0-9][0-9-]*\).*$/\1/p' "$SCRATCH/reference-check.before.md" | head -1)"
printf '  the committed report declares its verification coordinate: %s (supplied back to the renderer)\n' "${TAKEN:-MISSING}"
"$PY" artefacts/refs_verify_v50.py --report --taken "$TAKEN" | tail -1
rc5=$?
if [ "$rc5" -eq 0 ]; then
  if cmp -s "$SCRATCH/reference-check.before.md" reference-check.md; then
    printf '  the re-rendered report is byte-identical to the committed copy\n'
  else
    printf '  the re-rendered report DIFFERS from the committed copy:\n'
    diff "$SCRATCH/reference-check.before.md" reference-check.md | head -12
    rc5=1
  fi
fi
verdict "reference-check report" "$rc5"

GATE="../../.github/tools/refgate.py"
LINKGATE="../../.github/tools/linkgate.py"

printf '\n== 6. the journal citation gate (>=100 entries in one section, every entry cited) ==\n'
if [ -f "$GATE" ]; then
  # WHICH COPY runs is a property of the reader's tree: the branch never touches `.github/`, so an
  # archive of it carries the base's copy.  The copy is announced with its digest before it runs.
  printf '  the copy this tree carries: %s sha256 %s\n' "$GATE" \
    "$("$PY" -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest()[:16])' "$GATE")"
  ( cd ../.. && "$PY" .github/tools/refgate.py papers/issue-50/manuscript.md ) | tail -3
  rc6=${PIPESTATUS[0]}
  verdict "journal reference gate" "$rc6"
else
  printf '  NOT RUN -- %s is not in this tree.  A path-limited export carries no `.github/`, so the\n' "$GATE"
  printf '  gate cannot be run from here; its verdict in the tree this package was submitted from is\n'
  printf '  recorded in reference-check.md, and the copy that ran there is named there too.\n'
  skip=$(( skip + 1 ))
fi

printf '\n== 7. the journal link gate over the tracked markdown carriers ==\n'
if [ -f "$LINKGATE" ]; then
  ( cd ../.. && "$PY" .github/tools/linkgate.py --check )
  rc7=$?
  verdict "journal link gate" "$rc7"
else
  printf '  NOT RUN -- %s is not in this tree (same reason as step 6)\n' "$LINKGATE"
  skip=$(( skip + 1 ))
fi

printf '\n== 8. the four figures, regenerated from the artefacts and compared byte for byte ==\n'
"$PY" figures/make_figures_v1.py --check | tail -2
rc8a=${PIPESTATUS[0]}
"$PY" figures/make_figures_v1.py --selftest | tail -1
rc8b=${PIPESTATUS[0]}
rc8=$(( rc8a + rc8b ))
verdict "figure bytes and liveness" "$rc8"

printf '\n== 9. the manuscript\x27s own claims, against the objects that own them ==\n'
"$PY" manuscript_check_v1.py | tail -1
rc9a=${PIPESTATUS[0]}
"$PY" manuscript_check_v1.py --selftest | tail -1
rc9b=${PIPESTATUS[0]}
rc9=$(( rc9a + rc9b ))
verdict "manuscript claims and liveness" "$rc9"

printf '\n== 10. the README\x27s own numbers, against the objects that own them ==\n'
"$PY" readme_check_v1.py | tail -1
rc10a=${PIPESTATUS[0]}
"$PY" readme_check_v1.py --selftest | tail -1
rc10b=${PIPESTATUS[0]}
rc10=$(( rc10a + rc10b ))
verdict "README claims and liveness" "$rc10"

printf '\n== 11. digests of the files this package ships (copy this block, never type it) ==\n'
SHIPPED="manuscript.md manuscript_part1.md manuscript_part2.md manuscript_part3.md manuscript_part4.md \
assemble.py refs_build_display.py refs_render.py refs_order.json references.json refs_display.json \
reference-check.md rebuild_artefacts_v1.py manuscript_check_v1.py readme_check_v1.py README.md \
reproduce.sh \
figures/make_figures_v1.py figures/fig1_boundary.svg figures/fig2_tail.svg \
figures/fig3_prediction.svg figures/fig4_mixture.svg"
for f in $SHIPPED; do
  if [ -f "$f" ]; then
    printf '%-32s sha256 %s\n' "$f" "$("$PY" -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$f")"
  else
    printf '%-32s MISSING\n' "$f"
    fail=1
  fi
done

rm -rf "$SCRATCH"
printf '\nverdict: %s\n' "$([ "$fail" -eq 0 ] && echo OK || echo NOT READY)"
if [ "$skip" -gt 0 ]; then
  printf 'steps NOT RUN: %d (each printed its reason above; they are not counted as passes)\n' "$skip"
fi
if [ "$fail" -eq 0 ]; then
  printf 'REPRODUCE: ALL GREEN\n'
else
  printf 'REPRODUCE: FAILED\n'
fi
exit "$fail"
