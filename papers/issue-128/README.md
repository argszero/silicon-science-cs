# Issue #128 — How Much Fairness Is Free? The Zero-Cost Region of Group Quotas

Reproduction for the manuscript `manuscript.md`. Everything is deterministic: integer-valued
distances, no random state crosses a run boundary, and the instruments regenerate byte-identical.

## One command

```
bash reproduce.sh
```

Expected output (last line):

```
REPRODUCE: ALL GREEN (7 steps)
```

`reproduce.sh` runs, in order: (1) the corpus SHA-256 pins (read from inside `corpus/`, where the pinned
names are relative); (2–6) the certificate suites of the five instruments/analysers, each on a **healthy
and a mutated** object; (7) `canonical.py --check`, which re-derives every headline number from the
artefacts and asserts the paper's claims.

A fuller check re-runs the instruments, re-derives `canonical_results.json`, and rebuilds the figures and
the manuscript, requiring every regenerated artefact to be **byte-identical** to the committed one (adds
~11 minutes):

```
bash reproduce.sh --full        # -> REPRODUCE: ALL GREEN (10 steps)
```

The `--full` re-runs happen in place and are then restored from a snapshot taken before them, so the
package is left exactly as committed — on a pass and on a failure alike.

## Environment

- Python **3.9** (`/usr/bin/python3`) with **numpy** and **matplotlib**.
- No network is needed to reproduce: corpora are committed and SHA-256-pinned; the reference
  authenticity pass (`refscan128.py --verify`) is the only networked step and is not part of
  `reproduce.sh`.
- `matplotlib` needs a writable cache dir: `MPLCONFIGDIR=$(mktemp -d) python3 make_figures.py`.

## What is what

| file | role |
|---|---|
| `manuscript.md` | the paper (built; do not edit by hand) |
| `manuscript_source.md` | the paper's source, with citation **keys** `[@arxiv:…]`/`[@doi:…]` |
| `reproduce.sh` | **the one command**: pins, certificates, canonical re-derivation (`--full` adds the byte-identity re-runs) |
| `build_refs.py` | turns keys into numbers + the reference list (heading, one entry per paragraph, form and stated difference); asserts C1–C11 (`--selftest`) |
| `references.md` | the numbered reference list (126 entries, each closing with its role-class stated difference) |
| `reference-check.md` | citation-authenticity report: one line per cited entry |
| `refscan128.py` | discovery/curation/verification of the reference pool (`--selftest`) |
| `refs_pool.json`, `refs_raw.json`, `verify_log.txt` | the verified pool and its pass record |
| `canonical.py`, `canonical_results.json` | **the single source of the paper's numbers** (re-derived) |
| `spike_v3.py` … `spike_v5.py` | the instruments (synthetic; real corpus; real-row sweep) |
| `spike_v*_results.json` | their artefacts (the numbers the paper reports) |
| `analyse_v3.py`, `analyse_v5.py` | readers with their own certificates |
| `make_figures.py`, `figures/` | the three figures (byte-identical on re-run) |
| `corpus/` | SHA-256-pinned public datasets + `fetch_corpus.sh` |

## The corpus

Three public datasets, SHA-256-pinned in `corpus/SHA256SUMS` and re-hashed before every read:

- `winequality-red.csv` — UCI Wine Quality (red), 1599 rows (sha-256 `4a402cf0…`)
- `wine.data` — UCI Wine, 178 rows (sha-256 `6be6b120…`)
- `seeds_dataset.txt` — UCI Seeds, 210 rows (sha-256 `1f3f83c0…`)

## Numbers

Do not quote a number from this package by hand: `canonical_results.json` re-derives every headline
figure from the artefacts and is checked by `python3 canonical.py --check`. The verification certificate
for the citation list is `reference-check.md`; the verifier's own log line is in `verify_log.txt`.
