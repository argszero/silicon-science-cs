# Issue #153 — reproduction

**One command, offline, deterministic:**

```sh
./reproduce.sh
```

**Expected final line:** `REPRODUCE: ALL GREEN (9 steps)`. **Exit status:** the number of failed
steps (0 on success) — failures accumulate, so no later step can mask an earlier one. A step whose
declared dependency is absent is **not** a failure: step 6 declares `matplotlib`, and if that import
fails the step prints `NOT RUN` and the verdict line says so (`REPRODUCE: 1 STEP(S) NOT RUN`) while
the exit status stays 0. A run that did not take a step is reported as a run that did not take it.

Requires **CPython 3.9.6** and, for step 6, **matplotlib 3.9.4**; everything else is the standard
library. Those are pins, not floors: the declared tolerance below is byte-for-byte, so the versions
are part of the claim and a run on another build is a run on another instrument. The default
interpreter is `/usr/bin/python3` and can be overridden with `PY=...`; `MPLCONFIGDIR` defaults to
`/tmp/mplcfg` so the plot cache needs no writable `HOME`.

**Tolerance:** none. Every step is exhaustive enumeration with no sampling and no random seeds,
so the outputs are exact counts and are expected to be reproduced byte-for-byte. Two of the nine
steps compare bytes: step 6 (`make_figure.py --check` redraws the figure and compares it with the
committed one) and step 8 (`place_refs.py --render-only` regenerates `reference-check.md` from
`placement.json`). Both comparisons were verified on **matplotlib 3.9.4**; on another build the
figure's bytes may differ in ways that say nothing about this paper, which is why the version is
pinned here rather than licensed as "any 3.x".

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

**Contribution level: `case study`.** One model of one merge decision, measured exhaustively over 17
cells. The manuscript's abstract declares the same level in the same words, and §4.4's proposition is
stated as a proposition *of this model* -- proved inside it, not generalised beyond it.

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

Two more of that kind exist because the review found defects the stray scan is blind to by
construction. A marker whose value is a count of **table rows** is now applied to the table the
generator has just emitted and must agree with it — the defect it was built for printed a one-digit
count, and the scan polices multi-digit tokens and decimals, so it was green over exactly the class
where that defect lived. And the **contribution level** is read off the abstract and off this file
and must be one claim stated in both: a carrier that states none fails, because the silent carrier
is the one a reader has to reconstruct by hand. Each was planted — a row count bound to the
complement of the predicate its sentence asserts, and this file declaring a different level and
then none at all — and each exits 1 naming the disagreement.

A third binds the census to the prose in **both** directions, and it exists because a statistic
that cannot vary hid a false sentence in the abstract. The package used to say the fan-in
correspondence held "in all 17 of the 17" cells; that number counted cells whose `fanin_gap_max`
was 0, and that gap is ≤ 0 by construction, so the count was 17 for any input at all. The side
that can move said **16** cells, with 120 decisions failing in one of them. The guard now reads:
if the census holds failures the prose must carry the failure count, and if the prose carries one
the census must hold it, and the cells that agree plus the cells that fail must add up to the
grid. Planted by deleting the marker (exit 1, naming the 120), and by handing it a census with no
failures while the prose still cites one.

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
