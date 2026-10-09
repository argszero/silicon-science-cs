# Issue #132 — The Frame Is a Level

**The Frame Is a Level: Background-Frame Level as a Declared Parameter of Similarity Guards, and
the Systematic Misclassification a Corpus-Wide Frame Leaves**

**Contribution level: `theory+empirics`** — a formal dilution law for a DF-thresholded background
frame (with its exact critical prevalence and residue boundary) plus measurements on real,
SHA256-pinned text in five languages with ground truth by construction, two statistics, four
baseline levels and a one-command byte-identical reproduction. The registration (`issue #132`), this
file and the manuscript state the same value.

This directory is the reproducible package: the evidence layer every number is read from. The
manuscript, the figure set and the verified reference layer are added in the submission round; this
round establishes the layer they read from.

## Reproduction

```
cd papers/issue-132 && bash reproduce.sh
```

* **Directory**: run from the package directory, `papers/issue-132/`. The script resolves its own
  directory, so the relative paths it reads are its own.
* **Build**: CPython 3, standard library only — no third-party import anywhere in the package, so no
  library version enters a comparison. Measured under **3.9.6** and **3.13.9**; override with
  `PYTHON=/path/to/python3`.
* **Expected output**: `REPRODUCE: ALL GREEN`, preceded by one line per check. Each instrument is
  re-run and its fresh report is compared **byte-for-byte** (sha256 equality, `Tolerance: exact`)
  against the report this package ships, after its own plant battery prints `SELFTEST n/n`; the
  figure set is then re-generated and its **7 of 7** files are compared the same way.
* **Cost**: about 10 seconds. `REPRO_FULL=1 bash reproduce.sh` adds the determinism tier (two fresh
  runs per instrument).
* **Writes nothing inside the package**: each instrument is run with `SPIKE_OUT` pointing into a
  private temp directory the script creates and removes.

## Layout

| Path | What it is |
|---|---|
| `spike_v0.py` | The de-risk spike: tests the registration's set-containment identity and finds the dilution law |
| `spike_v1.py` | The frame-level ladder on the language axis: the register construct, P1 and P2 |
| `spike_v2.py` | The `(theta, tau, r)` grid and the eligible-subset rate |
| `spike_v*_results.json` | The report each instrument emits; every manuscript number is read from one |
| `make_figures.py` | The figure generator: deterministic SVG read from the reports, with a certificate |
| `figures/` | 5 SVGs + `CAPTIONS.md` + `FIGURES.md` + `manifest.json`, all generated |
| `corpus/` | 8 English Project Gutenberg texts + `SHA256SUMS` + `fetch_corpus.sh` |
| `corpus_i18n/` | 12 non-English texts (IT/ES/FR/DE) + `SHA256SUMS` + `fetch_corpus_i18n.sh` |
| `heilmeier.md` | The six Heilmeier answers, the adversarial checks, the registered priors and the round log |

## The claim in one paragraph

A near-duplicate guard that fires on `sim(a,b) >= tau AND |shared(a,b) \ F| >= r` takes its
background frame `F` from a population. When that population is the whole corpus, the frame is blind
to a **register** — a recurring block a community shares — exactly when the register's corpus
prevalence falls below the cutoff: `s * phi < theta`, i.e. below the **critical prevalence**
`phi* = theta / s`, where `s` is that community's share of the corpus. The misclassification is
therefore not random but concentrated in small-share communities, and both `phi*` and the residue
boundary `r <= register_units` are measured with two-sided controls.

## Provenance

The corpus is public-domain Project Gutenberg plain text, pinned by sha256 in each directory and
re-verified on every read; both instruments refuse to measure an unverified corpus. `research/` is
the git-ignored working area and is not part of the package.
