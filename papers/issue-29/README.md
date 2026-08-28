# Issue #29 — RISC-V ISA Extensions in the Wild: Reproduction

Manuscript: [`manuscript.md`](./manuscript.md) — Issue #29 — Author: `how2how2how2-arch`

**Contribution level**: `system` — a deterministic measurement pipeline (five detection
channels, C1–C5 + cross-ISA X1/X2) over a 20-repo corpus, evaluated by byte-identical
offline reproduction and Wilson 95% confidence intervals; baseline = cross-ISA
(x86 AVX / ARM NEON-SVE) coverage comparison within the same multi-ISA ML engines.

## One-command reproduction

```bash
bash reproduce.sh
```

- **Requires**: Python 3 (stdlib only), network NOT required (fully offline).
- **Input**: committed `data_snapshot/` (20 per-repository JSON snapshots + manifest,
  fetched 2026-08-28 from the GitHub API, no cloning; each snapshot pins the fetch date
  and records channel hits per file).
  **Manifest coverage**: `manifest.json` pins branch/head-SHA/fetch time for the 3
  cross-ISA repos (ncnn, ggml, XNNPACK — full-tree scans); the other 17 snapshots
  self-pin the same fields in their own headers (riscv-scoped scans). Traceability is
  uniform either way; the split is a fetch-optimization artifact.
- **Expected output**: `expected_output/discovery_results.txt` (canonical results,
  committed).
- **Tolerance**: **byte-identical** — `reproduce.sh` regenerates the canonical output
  from the snapshots and exits 0 iff `diff` reports no difference. Any deviation is a
  reproduction failure.

## Refresh (optional, network required)

```bash
python3 reproduce.py fetch        # re-pull all 20 snapshots from GitHub (codeload tarballs)
python3 reproduce.py fetch <repo> # single repo, e.g. torch/... (see corpus.json)
python3 reproduce.py summary      # per-repo extension groups from data_snapshot/
```

Fresh fetches write into `data_snapshot/` and re-derive the canonical output;
`reproduce.sh` then verifies byte-identity against the committed expected output.
Note: fresh fetches may drift from the 2026-08-28 snapshots as upstream moves
(snapshot-drift threat, §5 of the manuscript) — the committed snapshots are the
pinned evidence for all numbers in the manuscript.

## File layout

```
papers/issue-29/
├── manuscript.md            # full paper (all numbers traceable to expected_output/)
├── README.md                # this file
├── reproduce.sh             # one-command offline reproduction (exit 0 iff byte-identical)
├── reproduce.py             # pipeline: fetch / summary / offline modes
├── corpus.json              # corpus definition (20 repos, domain, selection evidence)
├── data_snapshot/           # 20 repo snapshots + manifest (committed evidence, 2.7 MB)
└── expected_output/         # canonical discovery_results.txt (frozen)
```

## Traceability statement

Every number in the manuscript (adoption table, Wilson CIs, cross-ISA file/macro
counts, T-Head custom-extension finding) derives from `data_snapshot/` via
`reproduce.py offline` and is frozen in `expected_output/discovery_results.txt`.
The narrative and the canonical run tell the same story.

**Cross-ISA rvv semantics**: the `rvv` file/macro columns count *real* RISC-V
markers only — the C3 macro channel is filtered for pseudo-macros
(`__riscv_xlen`/`__riscv_flen`/`__riscv_vlen`/…); a file counts as rvv only if it
carries a non-pseudo `__riscv_*` extension macro or an RVV intrinsics header
(`riscv_vector.h` etc.). Repos whose only marker is a pseudo-macro (openssl,
oneDNN, zephyr) therefore report `rvv=0`, consistent with their zero-vector status
in the adoption table (§4.1–4.2). H3's headline numbers (XNNPACK 656, ncnn 125,
ggml 17) are unaffected by this filter.
