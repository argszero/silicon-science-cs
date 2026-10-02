# issue #116 — How Long Should a Robot Commit? A Staleness–Amortization Boundary Law for the Action-Chunk Execution Horizon

Artifact for the manuscript `manuscript.md`. **One command reproduces everything:**

```bash
bash reproduce.sh          # expected final line: REPRODUCE: ALL GREEN
```

Requirements: `python3` **with numpy** and a POSIX shell with `cmp`/`shasum`.
**No network, no pip, and nothing is written inside the package** — every check
regenerates into a temporary directory and compares. Runtime ≈ 55 s on one CPU core.

**Build.** Recorded on **CPython 3.9.6 / numpy 2.0.2** (`/usr/bin/python3`, macOS);
`reproduce.sh` prefers the interpreter that carries numpy and prints which it used in
step 0. The instrument is a linear plant family with an **exact** closed loop, so every
number the manuscript prints is a deterministic function of the code (fixed seeds
throughout): the two exact cost routes agree to `1.52e-14`, i.e. at floating-point
resolution rather than at simulation noise, which is why the checks are
**byte-identity** and not tolerances. The command is run **from this directory**
(`bash reproduce.sh`), the directory the driver's relative paths resolve against. It
needs **no `.git`**: no step resolves a git object, so an exported archive of the head
runs it as a checkout does.

## What "reproduce" means here

The word covers several different claims, checked separately because a single
"run it twice and it matched" tolerance proves only the weakest of them.

| # | claim | step | how it is decided |
|---|-------|------|-------------------|
| 1 | the instrument is **deterministic** | `reproduce.sh` step 1 | two independent runs in the **same** directory required byte-identical in both the artefact and the log |
| 2 | the **committed artefact** is what the code produces | step 2 | regenerated and `cmp`-ed against the committed `canonical_results.json` |
| 3 | the committed **figures** are views of that artefact | step 3 | all 4 PNGs re-rendered and required byte-identical |
| 4 | the committed **manuscript** is what the pipeline builds | step 4 | `refs/refs_build.py render-check` requires `manuscript.md` to equal the render of `manuscript.src.md` |
| 5 | **citation coverage** and the citation guards hold | step 5 | `refs/refs_build.py check`: every entry cited, every in-text key curated, ≥100 references, and no literal `[N]` in the body |
| 6 | the manuscript's **decisive numbers** reappear | step 6 | each re-derived from a real run and matched against the string the paper prints |

Claim 2 is the one a reader relies on and the one a self-comparison does **not**
cover: step 1 proves the run is deterministic, not that the stored numbers came from
it. Both run, and each reports the count it read.

**Claim 1's note on warnings.** The run log carries six numpy `RuntimeWarning`s from
`matmul`. They are **expected and asserted**: the sweep probes delays *beyond* the
plant's stability margin, where the closed loop is unstable by construction and the
cost is `+inf`; that region is exactly the **ceiling** the paper's feasible window
`[τ, d_max − τ]` excludes. The warnings are stable across runs and are not a defect —
the artefact is byte-identical with them present.

## Layout

| file | what it is |
|---|---|
| `manuscript.md` | the paper; citations numbered, references generated |
| `manuscript.src.md` | the **source** of the paper: the same text with `[[identifier]]` citation tokens and a `<!-- REFERENCES -->` marker where the bibliography goes |
| `canonical_results.json` | the single artefact every figure and every number in the paper reads |
| `model_v1.py` | plant/disturbance algebra, the LQR gain, the augmented-Lyapunov route and the covariance-recursion route (their agreement is criterion 1) |
| `model_v2.py` | the two channels: the mean response, the impulse families, the moment-matched scale-mixture family |
| `model_v3.py` | validates the objective: the quasi-static proxy against the **exact periodic** chunked cost |
| `model_v3b_shape.py` | the shape channel on the saturating arm |
| `model_v4_sweep.py` | the manuscript-grade sweep; **writes `canonical_results.json`** |
| `model_v5_exponent.py` | the stationarity (FOC) identity and the test of the candidate closed form for the exponent |
| `make_figures.py`, `plotlib.py` | the stdlib-only figure pipeline (raster canvas, 3×5 font, zlib PNG writer) |
| `figures/` | the four figures, plus `manifest.json` (bytes + sha256 per figure) |
| `refs/` | the citation pipeline: discover → curate → verify → number/coverage |

### The citation pipeline is three different acts, in three files

| file | the question it answers | the question it does **not** answer |
|---|---|---|
| `refs/refs_discover.py` | what did the arXiv index return for this phrase? | is any of it relevant? |
| `refs/refs_curate.py` | which entries does the paper cite, and in what role? | do they exist? |
| `refs/refs_tool.py` | does each entry exist as the paper we say it is? | is it relevant? |
| `refs/refs_build.py` | is every entry cited and every in-text key curated? | is it authentic? |

`refs/refs_keys.json` is the key→role map **including the verified title** the
verifier wrote; `refs/refs_verify.log` is the verifier's own output; and the report
`reference-check.md` is written from those two files rather than from prose.

**Verification is the one networked part** and it is *not* part of `reproduce.sh`:

```bash
python3 refs/refs_tool.py verify      # every arXiv entry, by identifier
python3 refs/refs_tool.py doi         # the DOI entry, via Crossref
python3 refs/refs_tool.py fromlog     # rebuild the verified titles from the log
```

`verify` fetches each entry **by its own identifier** from the arXiv API and compares
the returned title to the recorded one; when the API is throttled (HTTP 429) it falls
back to each entry's **abstract page** and reads its `citation_title` meta tag — a
different service carrying the same record — and marks those entries in the log as
`+abs-page`. It exits non-zero if any entry fails, so it is a check rather than a
statement. The committed `refs/refs_verify.log` records **134/134 resolved, 0
problems**. Two-sided controls (a swapped title, an invented identifier) were run
against a throwaway copy of the keys file and both exit 1.

## Headline results (all re-derived by `reproduce.sh`)

- **The boundary law is the stationarity condition** `λ_c = L·[c(τ+L) − C(L)]`, and it
  reproduces the discrete sweep's optimum **exactly** (worst `0.0000` at grid step
  `0.02`) over 4 plants × 7 latencies × 22 prices.
- The feasible set is **`[τ, d_max − τ]`**, closing at both ends and collapsing at the
  **latency wall** `τ = d_max/2`.
- The registered square-root law is **refuted** (19 fits, exponent in
  `[+0.184, +0.635]`, 14 of 19 intervals entirely below 0.500), and the natural
  replacement `1/(p+1)` is **also refuted** (corr `+0.773`), because the delay-cost
  curve is not a power law over the swept window.
- The two disturbance channels act on different quantities: a mean adds a
  **delay-invariant** term (`399.96 %` of the covariance part, spread `0.0` over the
  delay) that moves the optimum by nothing; a shape moves the optimum and grows with
  staleness.
