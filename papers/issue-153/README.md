# Issue #153 — reproduction

**One command, offline, deterministic:**

```sh
./reproduce.sh
```

**Expected final line:** `REPRODUCE: ALL GREEN (9 steps)`. **Exit status:** the number of failed
steps (0 on success) — failures accumulate, so no later step can mask an earlier one. Requires
CPython 3.8+ and, for one step, `matplotlib` (**3.9.4** was used; any 3.x with `Patch` and
`Line2D` legends will do); everything else is the standard library. The default interpreter is
`/usr/bin/python3` and can be overridden with `PY=...`; `MPLCONFIGDIR` defaults to `/tmp/mplcfg`
so the plot cache needs no writable `HOME`.

**Tolerance:** none. Every step is exhaustive enumeration with no sampling and no random seeds,
so the outputs are exact counts and are expected to be reproduced byte-for-byte. The one
byte-comparison the script relies on is that `place_refs.py --render-only` regenerates
`reference-check.md` from `placement.json` identically.

## What each step establishes

| step | program | establishes |
|---|---|---|
| 1 | `certificate.py` | the dynamic program used as the optimum agrees with an independently written brute-force traversal on every instance of six cells (9008 of 9008) |
| 2 | `characterise.py` | per-cell losses and worst excess, the horizon `w*`, and the cheapest-overlap control in every cell |
| 3 | `lemma.py` | the non-locality proposition, with a two-trace witness checkable by hand |
| 4 | `lemma_scale.py` | the falsifier over larger cells, the `K=2` no-choice control, and the exact rule in `w*=0` cells (both directions asserted) |
| 5 | `emit_results.py` | `results.json` — every number the manuscript states, emitted by the programs above |
| 6 | `make_figure.py --check` | `figures/deployed-rule-vs-optimum.{svg,png}` redrawn from `results.json` and compared byte for byte, after four invariants hold: the plotted maximum is the stored `max_worst`, every bar's fraction recomputes from `greedy_loss / traces`, the `K = 2` cells are exactly the ones with no legal choice, and `w* = 0` coincides with the zero-lookahead rule being exact. It refuses to draw when one fails, and `--check` compares rather than writes, so the committed bytes are not replaced by the run that checks them. |
| 7 | `make_manuscript.py` | `manuscript.md` from `manuscript_prose.md` + `results.json` + `placement.json` |
| 8 | `check_reference_report.sh` | `reference-check.md` regenerates byte-identically from the stored verification state |
| 9 | `check_steps.py` | the step count this package **states** equals the count this script **runs**: the `N/M` labels, the literal `(N steps)` in `reproduce.sh`, `README.md` and `manuscript.md`, and — the shape the journal's own `stepgate.py` is blind to — a count spelled out as a number word before an enumeration, whose items are counted too. A carrier that states nothing fails; silence is not agreement. |

Step 7 is a gate, not a convenience. Every figure in the manuscript is a `{{n:key}}` marker
resolved from `results.json`; after substitution the generator scans the body for multi-digit
numbers and refuses to write the paper if it finds one it cannot bind to an artifact. A number
typed into the prose therefore fails the build instead of reaching the paper. The scan ignores
section numbers, `code`-spanned identifiers and traces, and four-digit years.

Step 6 is the same discipline for the one figure: it is drawn from `results.json` and its caption
claims are asserted as invariants before the file is written, so a figure whose bars disagree with
the table cannot be produced. Both guards were seen to fail on a planted defect — a stored
`max_worst` set to a value no cell attains, and a `w* = 0` cell given losses it cannot have, each
exit 1 with the disagreement named — and restoring the artifact returns them to 0.

## Files

| file | role |
|---|---|
| `manuscript_prose.md` | the prose, with markers — this is what a human edits |
| `manuscript.md` | generated; do not hand-edit, it is overwritten by step 6 |
| `results.json` | every stated number, emitted by step 5 |
| `pool.json` | the harvested reference pool **with its search form** (registry, field, queries, window, scan date, screening word sets) |
| `screen_tally.txt` | the harvest screen: rows fetched, kept, and every rejection counted by reason |
| `placement.json` | stored Crossref verification state + the section and claim each placed entry supports |
| `placement_pruned.json` | entries pruned at placement, each with its reason |
| `reference-check.md` | generated authenticity report: one line per placed reference with the record Crossref returned |
| `comparison_set.md` | the works read in full, with what each bounds, its adversary, what it does not model, and the specific difference |

## What needs network (and is therefore not in `reproduce.sh`)

Refreshing the pool is a separate, explicitly-network step:

```sh
/usr/bin/python3 build_refs.py      # Crossref harvest + screen  -> pool.json, screen_tally.txt
/usr/bin/python3 place_refs.py      # Crossref verification + placement -> placement.json, reference-check.md
```

Reproduction of the committed figures needs neither: `place_refs.py --render-only` rebuilds
`reference-check.md` from the stored verification state, and step 6 exercises it. If the network
step is re-run on a later date, `pool.json`'s recorded `scan_date` and window move with it, and
`reference-check.md` will record the new date rather than the old one.

## Scope

The model is `K` capacity slots over `R` key ranges with run sizes frozen at creation; it is not
a deployment and replays no production trace. See the manuscript's §2.2 for how the modelled
rule corresponds to leveled compaction and §5 for what the results do not cover.
