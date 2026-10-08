# Issue #130 — A Threshold Is Not a Measurement

**A Threshold Is Not a Measurement: The Operating Characteristic and Certification Floor of
Artefact-Similarity Checks**

**Contribution level: `theory+empirics`** — a statistical model of the check (the operating
characteristic `R(eps; tau, L)` and its length scaling) plus measurements on real text with ground
truth by construction, four baseline statistics, multi-seed reproduction and a one-command
reproduction. The registration (`issue #130`), this file and the manuscript state the same value.

This directory is the reproducible package. The manuscript (`manuscript.md`) and the figure set are
added to it in later revisions of this branch; the evidence layer below is what every number in it
is read from, and it is complete and runnable now.

## Reproduction

```
cd papers/issue-130 && bash reproduce.sh
```

* **Directory**: run from the package directory, `papers/issue-130/`. The script resolves its own
  directory, so the relative paths it reads (`corpus/SHA256SUMS`, `artefact_hashes.json`) are its
  own.
* **Environment**: CPython 3.9 (measured on **3.9.6**, macOS). Every script imports the standard
  library only — `math`, `random`, `hashlib`, `re`, `json`, `io`, `os`, `sys`, `subprocess`,
  `tempfile`, `collections`, `itertools` — and **no third-party package**, so there is no library
  version whose arithmetic enters a comparison. Override the interpreter with
  `PYTHON=/path/to/python3`.
* **Inputs**: `corpus/pg*.txt` — eight Project Gutenberg books, 5.6 MB, **committed in this
  package** and verified against `corpus/SHA256SUMS` at the start of every run. Nothing is fetched:
  the run never touches the network. `corpus/fetch_corpus.sh` re-obtains the same eight files from
  `gutenberg.org` and rewrites the sums; it is needed only to rebuild the input, never to reproduce.
* **What it recomputes** (it is not a checksum check over committed outputs): it re-runs the ten
  experiments **from their own code**, each over the committed corpus, and compares each fresh report
  byte-for-byte against the report this package ships; then it re-runs the analysis that derives the
  paper's tables from those reports; then it runs the determinism certificate's own battery.
* **Expected output** (this machine, 3.9.6 — the `build` line names the interpreter you ran):
  ```
  build          /usr/bin/python3 3.9.6 | stdlib only (no third-party import anywhere in the package)
  corpus         8 file(s) verified against corpus/SHA256SUMS
    spike_v0  MATCH  e828ae4db8878d34
    ... one MATCH line per instrument, ten in all ...
  instruments    10 of 10 reports re-run byte-identically
  analysis       re-derived its tables (6 of 6 printed)
  analysis       the mechanism certificate (predicted vs measured eps*)
  analysis       the boundary power law (slope -0.230, R2 0.950)
  certificate    plant 1: identical objects must NOT fire
  certificate    plant 2: a one-byte change MUST fire
  certificate    plant 3: the real cross-process defect MUST fire
  determinism    skipped -- REPRO_FULL=1 adds the two-run certificate (~13 min)

  REPRODUCE: ALL GREEN
  ```
* **Tolerance: `exact`** — the comparison is sha256 equality against the shipped reports, not a
  numeric band. The value was read against **two builds**: the whole package was run under CPython
  **3.9.6** (`/usr/bin/python3`, 4m58s) and under CPython **3.13.9** (3m58s), and all ten reports are
  **byte-identical in both** — the same ten sha256, with no version pin needed, because the
  instruments import no third-party library. A different machine's floating-point reduction order is
  the residual freedom, which is what the tier below measures rather than a widened band.
* **Cost**: about **4 minutes** (the ten instruments; `spike_v4` ≈ 95 s and `spike_v5` ≈ 89 s are
  most of it).
* **What the run writes**: **nothing inside the package.** The instruments emit their reports into a
  private temporary directory the script creates and removes, so the ten `*_results.json` files this
  package ships are left exactly as committed. (`spike_v7.py` reads the package's
  `spike_v4_results.json` on purpose: its certificate X1 asserts its pools *are* that report's
  pools.)

### The second tier: `REPRO_FULL=1 bash reproduce.sh`

Adds `repro_check.py`, which re-runs every instrument **twice** in separate processes and compares
the two artefacts — the determinism certificate (about **13 minutes** more). It also compares the
regenerated hash table against the shipped `artefact_hashes.json` and restores the shipped copy, so
the committed file is what stays on disk; that file is the **only** path in the package this run may
write. Run in full, the tier prints:

```
  determinism    10 of 10 instruments reproduce byte-for-byte over two runs
  determinism    the regenerated table equals the shipped artefact_hashes.json
```

## The tree this package needs

Everything the reproduction reads is a **tracked file of the package**: the ten instruments, the
analysis, the certificate, the corpus and the hash table. No step resolves a git object, reads a
file outside the package, or needs a checkout — so the package runs over an **export of its head**
(the form triage uses), which carries the tracked files only and neither `.git` nor any ignored
path. `papers/issue-130/research/` is a git-ignored workspace and is **not** part of the package.

## Other documented commands

Each of these prints a verdict of its own; run them from the package directory.

| command | expected output |
|---|---|
| `python3 repro_check.py --selftest` | `SELFTEST ALL PASS` — the comparator **accepts** identical objects **and fires** on a one-byte change and on a pair of `hash(str)`-seeded processes (the real cross-process defect this family once had). Exits non-zero if any plant is missed. |
| `PYTHON=/path/to/python3 bash reproduce.sh` | the same transcript with that interpreter on the `build` line. Every instrument is pure standard library, so any 3.9+ interpreter reaches the same verdicts. |

## What is in the package

| file | what it is |
|---|---|
| `corpus/` | the pinned real-text corpus (8 Gutenberg books + `SHA256SUMS`) and `fetch_corpus.sh` |
| `spike_v0.py` | the **calibrated** design: two calibration populations (unrelated / benign) fix `tau` per length, and the length axis enters (`L = 25 … 400`) |
| `spike_v1.py` | the **decisive** design: `tau` held **fixed** over `tau = 0.9 … 0.2` and `eps = 0 … 0.5` (what a deployer actually does) |
| `spike_v2.py` | the **FPR-matched** operating point: `tau(L, stat)` = the statistic's own null p95 over `L = 40 … 3000`, with the size sweep and the sanity controls |
| `spike_v3.py` | the **edit-operator** axis: token substitution vs character substitution at the same nominal rate |
| `spike_v4.py` | the **fusion** axis: two statistics combined by OR / AND at FPR-matched operating points — the calibration arm (joint null, indicator covariance, the `excess = ±Cov` identity) and the boundary arm |
| `spike_v5.py` | the **null-key** axis: the null matched per side vs drawn at the longer length, with the key's effect measured as a function of the length ratio |
| `spike_v6.py` | the **(statistic × band)** operating-point table and the cross-over, separated into a floor cause and a robustness cause |
| `spike_v7.py` | the **third operator** on the fusion, and the transfer law's operator-independence (certificates X1–X4) |
| `floor_v2.py`, `floor_v3.py` | the **certification floor** `L*`: where a statistic's null p95 reaches the floor (so no threshold at that length can certify anything) and how the floor moves with the level |
| `analyse_v2.py` | the analysis that derives the paper's tables from `spike_v2_results.json`, including the **mechanism certificate** (predicts `eps*` from the measured decay curve and the measured threshold, then compares with the measured `eps*`) |
| `repro_check.py` | the **determinism certificate**: two-run byte identity for every instrument, with its own three-plant battery |
| `artefact_hashes.json` | the sha256 of each shipped report, **generated** by `repro_check.py` (never typed into prose) |
| `heilmeier.md` | the six Heilmeier answers and the adversarial checks the direction was registered with |

## Where the manuscript's numbers come from

Every claim in the manuscript is read off one of the shipped reports or off the reproduction's own
transcript: the boundary `eps*` and its spread per statistic and length from `spike_v2`/`analyse_v2`
(*Table 3*), the mechanism certificate's 21 cells and its worst deviation from *Table 4*, the
boundary power law's slope and `R²` from *Table 5*, the fusion's recovery-and-price law and its
certificates from `spike_v4`/`spike_v7`, the key's blind/leaky split from `spike_v5`, the band table
and the cross-over from `spike_v6`, and the floor `L*` from `floor_v2`/`floor_v3`.
