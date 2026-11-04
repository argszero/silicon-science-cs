# issue-165 — Breadth Is Not Depth

The per-request yield of citation expansion, and the price at which allocation would change.

**Status: package core complete and reproducible; the reference list is not yet assembled, so this is
not a submittable manuscript.** `manuscript.md` says so in its own header and its §References.

## Reproduce in one command

```bash
./reproduce.sh
```

Expected output on a machine with `bash` and a `python3` (matplotlib is needed only for the figures,
and the script finds an interpreter that has it):

```
[1] committed arm digests                        ok
[2] results.json recomputed                      ok
[3] manuscript.md re-rendered                    ok
[4] figures redrawn                              ok
[5] printed numbers all derivable                ok
[6] reference report matches corpus              ok

REPRODUCE: ALL GREEN (6 steps)
```

Exit codes: `0` all six steps ran and agreed · `3` nothing failed but a step could not run here (a
declared NOT RUN, never to be read as a pass) · `N` N steps disagreed.

**Tolerance: none.** Steps 2–6 compare bytes, not values: `results.json` and `manuscript.md` are
regenerated from the committed arms and the committed template and must match the committed copies
exactly; the two PNGs are redrawn into a temporary directory and compared byte for byte. A reader on a
different matplotlib version may get a different PNG *encoding* (same numbers, same picture) — that is
the one place bytes are not portable, and step 4 will say so loudly rather than pass quietly. The
numbers themselves have no version dependence: `analysis.py`, `make_manuscript.py` and
`check_numbers.py` import nothing outside the Python standard library.

## What each step proves

| step | proves |
|---|---|
| 1 | the two committed arms are the bytes we measured (sha256 over the **decompressed** payload, `refs/DIGESTS.json`) |
| 2 | every published number recomputes from those bytes — `results.json` byte-identical |
| 3 | the manuscript is *generated*: every quantity in it resolves from `results.json`, and re-rendering reproduces the committed prose byte for byte |
| 4 | the two figures redraw identically, each one carrying a numeric invariant it is checked against before it is drawn |
| 5 | every number printed in the manuscript is a form the artefact can produce at that precision — a hand-rounded or hand-typed number fails here |
| 6 | `reference-check.md` still describes `refs/records.json`: the report is regenerated and compared byte for byte, so it cannot certify a corpus that has moved |

## Files

| file | role |
|---|---|
| `refs/cs_arm.json.gz`, `refs/social_sciences_arm.json.gz` | the measurement: two field arms, 30 seeds each |
| `refs/DIGESTS.json` | sha256 of each arm's decompressed bytes |
| `analysis.py` | the only producer of `results.json`; standard library only |
| `results.json` | every published quantity, one key each |
| `manuscript_template.md` | the paper with `{{...}}` markers where quantities go; a bare multi-digit number in it is refused |
| `make_manuscript.py` | renders the template into `manuscript.md`, refusing hand-typed numbers |
| `check_numbers.py` | reads the *prose* (the renderer with citations and bibliography removed) and refuses any number the artefact cannot produce; the renderer's own ordinals and DOI digits are never the object of the scan |
| `refs/records.json`, `refs/slots.json` | the reference corpus: 102 verified registry returns and every refusal with its reason |
| `build_refs.py` | asks a registry for each declared slot and verifies the answer; a refused slot stays refused |
| `ref_check.py` | writes `reference-check.md` from the corpus, and `--check` proves the report still matches it |
| `reference-check.md` | one line per entry: key, method, result, the record found |
| `make_figures.py` | draws the two figures, each guarded by an invariant that would refuse a contradictory picture |
| `manuscript.md` | the generated paper — do not edit it; edit the template |
| `figures/` | `fig1_decay.png`, `fig2_price_bound.png` |

## What this package does *not* reproduce

The **data collection** was live: the two arms were fetched from the OpenAlex API under a pinned seed
frame (field, year window, citation band, sample size, sampling seed — recorded under
`arms.*.seed_frame` in `results.json`). `reproduce.sh` re-derives the analysis from the collected arms,
not the arms from the API: re-fetching would test the API's state today, not our result. The API's own
request caps that the cost model rests on — a breadth page returns at most 200 works, an id filter
accepts at most 100 values — are recorded as data in `results.json` (`arms.*.cost_constants`) and are
not re-probed.

The **reference list** is not yet assembled; `manuscript.md` carries a placeholder section and the
paper is marked non-submittable for that reason. When it lands, `reference-check.md` will record, per
entry, the verification method and the real record found.
