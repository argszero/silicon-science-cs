# issue #118 — The Capacity Factor Is Not a Constant: A Load-Tail Law for Token Dropping in Sparse Mixture-of-Experts

Artifact for the manuscript `manuscript.md`. **One command reproduces everything:**

```bash
bash reproduce.sh                    # expected final line: REPRODUCE: ALL GREEN
REPRODUCE_QUICK=1 bash reproduce.sh  # skips only claim 1 (see below); ≈ 9 min
```

Requirements: `python3` **with numpy** and a POSIX shell with `cmp`/`shasum`.
**No network, no pip, and nothing is written inside the package** — every check
regenerates into a temporary directory and compares. Runtime ≈ **17 min** (measured 17m10s) on one CPU
core (`REPRODUCE_QUICK=1` ≈ 9 min); it is dominated by the two full runs of the
instrument suite in claim 1.

**Build.** Recorded on **CPython 3.9.6 / numpy 2.0.2** (`/usr/bin/python3`, macOS);
`reproduce.sh` prefers the interpreter that carries numpy and prints which it used in
step 0. Every seed is fixed (`20261002`), and the instruments are arithmetic rather than
simulated: the exact tail-sum route and the exact-integer route agree to `6.36e-13`, i.e.
at floating-point resolution rather than at Monte-Carlo noise. That is why the checks are
**byte-identity** and not tolerances. The command is run **from this directory**
(`bash reproduce.sh`), the directory the driver's relative paths resolve against. It needs
**no `.git`**: no step resolves a git object, so an exported archive of the head runs it
as a checkout does.

## What "reproduce" means here

The word covers several different claims, checked separately because a single
"run it twice and it matched" tolerance proves only the weakest of them.

| # | claim | step | how it is decided |
|---|-------|------|-------------------|
| 1 | the instrument suite is **deterministic** | step 1 | two independent full runs in the **same** directory required byte-identical in both the merged artefact and the log |
| 2 | the **committed artefact** is what the code produces | step 2 | regenerated and `cmp`-ed against the committed `canonical_results.json` |
| 3 | the committed **figures** are views of that artefact | step 3 | all 4 PNGs and `figures/manifest.json` re-rendered and required byte-identical |
| 4 | the committed **manuscript** is what the pipeline builds | step 4 | `refs/refs_build.py render-check` requires `manuscript.md` to equal the render of `manuscript.src.md` |
| 5 | **citation coverage**, the citation guards, and the **citation report** | step 5, 5b, 5c | `refs_build.py check` (every entry cited, every in-text key curated, ≥100 references, no literal `[N]` in the body); `refs/refs_report.py` regenerating `reference-check.md` byte-identically; and 5c re-reading the **author component** and the **block form** off the rendered `manuscript.md` |
| 6 | the manuscript's **decisive numbers** reappear from the code | step 6 | two certificate numbers grepped from `spike_v1.py`'s **own stdout**, and seven headline numbers from the step-1 run log |

Claim 2 is the one a reader relies on and the one a self-comparison does **not** cover:
step 1 proves the run is deterministic, not that the stored numbers came from it. Both
run, and each reports the count it read.

`REPRODUCE_QUICK=1` skips **only** claim 1's second run, and prints `SKIP`, never `OK`.
It exists because claim 1 is 92 % of the runtime; every other claim still runs.

## Layout

| file | what it is |
|---|---|
| `manuscript.md` | the paper; citations numbered, references generated, figures embedded |
| `manuscript.src.md` | the **source** of the paper: the same text with `[[identifier]]` citation tokens and a `<!-- REFERENCES -->` marker where the bibliography goes |
| `canonical_results.json` | the single artefact every figure and every number in the paper reads |
| `canonical_runner.py` | runs the five instruments in order and merges them into `canonical_results.json`; also prints the headline block step 6 reads |
| `spike_v0.py` | the exact tail-sum route against an independent Monte-Carlo; the `C_min` decomposition |
| `spike_v1.py` | the certified two-route comparison (float vs **exact integer** arithmetic); the tolerance-indexed curve; the ceiling |
| `model_v2.py` | the closed form and its domain; top-`k` exactness; the dispatch composition arm |
| `probe_uniform.py` | **the uniform router at both ends of the load range**: the tolerance `C = 1.25` silently encodes, the floor the measured router converges to, and the exact tolerance-indexed readings |
| `model_v3.py` | the production map (eight published configurations) and a measured router |
| `plotlib.py`, `make_figures.py` | the stdlib-only figure pipeline (raster canvas, 3×5 font, zlib PNG writer, reused from issues #114 / #116) |
| `figures/` | the four figures, plus `manifest.json` (bytes + sha256 per figure, and the artefact's sha256) |
| `refs/` | the citation pipeline: discover → curate → verify (titles **and** authors) → number/coverage → report |

### The citation pipeline is four different acts, in four files

| file | the question it answers | the question it does **not** answer |
|---|---|---|
| `refs/refs_discover.py` | what did the arXiv index return for this query? | is any of it relevant? |
| `refs/refs_curate.py` | which entries does the paper cite, and in what role? | do they exist? |
| `refs/refs_tool.py` | does each entry exist as the paper we say it is? | is it relevant? |
| `refs/refs_build.py` | is every entry cited and every in-text key curated? | is it authentic? |
| `refs/refs_report.py` | what do the two artefacts above jointly say? | anything the artefacts do not |

`refs/candidates.json` is the discovery artefact (58 queries → 1100 candidates);
`refs/curated.json` is the curatorial act (105 entries, each with a role and a stated
difference from this work); `refs/verify.log` is the verifier's own output; and
`refs/authors.json` records the author names **as each record states them**, captured in
the same fetch that resolved that entry's title, so the entry's author component is
evidence about the same record the title check is evidence about. `reference-check.md` is
**generated** from those three by `refs/refs_report.py` rather than written by hand —
step 5b requires the committed file to equal its regeneration.

**Verification is the one networked part** and it is *not* part of `reproduce.sh`:

```bash
python3 refs/refs_tool.py verify     # every entry, by its own identifier
python3 refs/refs_tool.py plant      # two-sided control on a throwaway copy
```

`verify` fetches each entry **by its own identifier** from the index that owns the
identifier (`https://export.arxiv.org/api/query?id_list=<id>`) and compares the returned
title to the one recorded for that key, after normalisation. It exits non-zero if any
entry fails, so it is a check rather than a statement. The committed `refs/verify.log`
records **105/105 resolved, 0 problems**, and the generator additionally asserts that the
log and the curated set name the same identifiers in both directions.

The **same request** that returns the title returns the record's authors, and they are
written to `refs/authors.json` rather than typed into the bibliography: an author list
transcribed from memory is not evidence, and a second, later fetch could resolve a
different revision of the record. The renderer reads them from there, prints the house
form (`Family, I.`; the first three then `et al.` from the fourth; a record giving one
token and no more prints that token alone), and `reference-check.md` prints the raw string
the record gave **beside** the rendered form, so the split is an auditable derivation. An
entry whose authors were never read is a defect and is refused — it must not render as
though the record carried none.

In practice the identifiers are fetched in **batches** (40 per request, `max_results`
passed explicitly because arXiv's `id_list` silently caps at 10 by default), with a
single-identifier fallback for anything a batch does not answer for. Every entry is
separated from the next by a blank line: consecutive line-start markers are one paragraph
to every CommonMark renderer, so the list is read as it renders, and **step 5c** re-reads
both properties off the product.

The two-sided control injects a corrupted title and an invented identifier (`9999.99999`)
into a throwaway copy; **both must fail** or the command exits non-zero.

## Headline results (all re-derived by `reproduce.sh`)

- **The drop rate is an exact functional.** `D(C) = (1/T) Σ_e E[(N_e − c)+]` with
  `N_e ~ Bin(T, q_e)`, `q_e = k·p_e`, `c = C·k·T/E`. Route A (floating point) against
  route B (**exact integer arithmetic**) at the same `C`: worst relative difference
  **`6.36e-13`** (registered bar `1e-3`). The independent Monte-Carlo sampler is scored,
  not asked to meet a bar its resolution cannot reach: **max `|z| = 2.17`** over five cells.
- **The ceiling is confirmed from both sides.** With a *perfectly uniform* router — the
  balancing ideal — every tested cell with `µ ≤ 16` needs **`C_min > 1.25`**, and at
  decode-like `µ = 1` it needs `C_min = 7.97` and drops **29.89 %** of tokens at the folk
  constant. Twenty of twenty Dirichlet-skew cells sit **strictly above** the uniform floor
  (by `+2.1` to `+42.3` in `C_min` units): skew only adds.
- **The tolerance inversion.** `C = 1.25` is a *different tolerance in every cell* — it
  accepts `8.29e-05` at `µ = 128`, `2.24 %` at `µ = 16`, and `29.89 %` at `µ = 1`. The
  constant is not wrong; it is **unlabelled**. The same cell read at three declared
  tolerances by the exact route: `1.619` at `1e-3`, `2.189` at `1e-6`, `2.638` at `1e-9`.
- **The closed form has its own domain.** Normal `C_min` is **27.8 %** off, the continuity
  correction makes it **worse** (**39.7 %**), and the skewness-corrected (Edgeworth) form
  meets a 5 % bar only for **`µ ≥ 8`** (max **4.54 %**), failing below it because its
  expansion parameter `γ = (1−2p)/σ` runs 0.10 → 0.98.
- **Top-`k` is exact, not approximate**: `N_e ~ Bin(T, k p_e)`, confirmed against an
  independent top-`k` Monte-Carlo, `z` = 0.24 … 2.61.
- **The composition law.** Under first-come dispatch the dropped set is position-biased
  (**0.00 %** of drops in the first decile of arrivals against **14.8–19.4 %** in the last,
  null 10 %), hot-expert concentrated (7–17× the uniform null), and the displacement is
  **exactly `min(L, cap)`** in every cell tested — one attacker token displaces one victim
  token, and the total is capped at **one capacity per targeted expert**.
- **Eight published configurations** (Switch, GShard, GLaM, Mixtral 8x7B, DeepSeek-V2,
  DeepSeek-V3, Qwen2-57B-A14B, OLMoE-1B-7B) are placed on the curve. At training load the
  folk constants sit inside the validity region; at decode load `C = 1.25` is below it.
  DeepSeek-V3's stated no-drop policy is the architectural escape the theory predicts.

## Corrections made while assembling this package

Three numbers in the manuscript were carried in prose and had **no committed instrument**
behind them; a fourth cited the *closed form's* readings as if they were measurements. All
four are now owned by `probe_uniform.py` (added here) or corrected to the exact route:

| was | now | why |
|---|---|---|
| the small-µ table (`29.89 %`, `C_min = 7.97 / 5.43 / 3.80`) | produced by `probe_uniform.py`, row for row | no committed script printed them |
| the uniform floor `1.1633` | **`1.1635`** | the exact route at tolerance `1e-6` crosses `1e-6` at `1.163538`; `1.1633` gives `1.023e-06`, i.e. it is not the `C_min` at that tolerance |
| `C_min` at `1e-3 / 1e-6 / 1e-9` = `1.562 / 2.024 / 2.355` | **`1.619 / 2.189 / 2.638`** | the old values are the closed form's `c_pred` columns, which §5.4 itself reports as 3.8 % off at that cell |
| the "tolerance band" on the frontier figure | the exact three readings for one cell | a band drawn from the closed form would present its breakdown as data |

None of the changes moves a conclusion: `4.18/1.1635 = 3.59` (still "3.6× the floor") and
`1.37/1.1635 = 1.18` (still "about 1.2×").
