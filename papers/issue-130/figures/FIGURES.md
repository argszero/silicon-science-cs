# The figure set of issue #130

Five figures, all **generated** from the package's own reports by `../make_figures.py`:

```
python3 make_figures.py            # -> figures/*.svg + manifest.json + CAPTIONS.md
python3 make_figures.py --selftest # the certificate battery below
```

Nothing in a figure is typed by hand. Each figure reads the shipped `*_results.json` of the
instrument(s) listed below, and every number a figure **annotates** — the fitted slopes, the
censored-cell list, the inflation factor, the two rank correlations — is read from that report, so a
figure cannot silently drift from the number the manuscript quotes. `figures/CAPTIONS.md` is
generated the same way and is what the manuscript embeds, so the caption carries no number the
figure does not.

| figure | source report(s) | the claim it carries |
|---|---|---|
| `fig1_null_vs_length.svg` | `spike_v2_results.json` | the unrelated-pair null is length-dependent, and its shape splits the four statistics into two classes |
| `fig2_boundary_power_law.svg` | `spike_v2_results.json` | at the FPR-matched point the boundary `eps*` falls as a power law for char-bigram Dice and is flat for word-3 Jaccard |
| `fig3_certification_floor.svg` | `floor_v2_results.json`, `floor_v3_results.json` | below `L*(alpha)` the threshold is 0 and the false-positive rate is 1.0 — a hole, not a reading |
| `fig4_stratum_weights.svg` | `spike_v8_results.json` | the operating point is stratified: a mismatched scan inflates the rate and the repair restores it, while the natural diagnostic does not rank the damage |
| `fig5_fusion_recovery.svg` | `spike_v4_results.json` | OR recovers the robust member's boundary and AND inherits the brittle member's |

`manifest.json` lists each figure's `sha256`, its byte size and its source reports; it is generated,
never typed.

## Certificate (`--selftest`)

| item | what it asserts | how it can fail |
|---|---|---|
| F1 | every source report parses and carries the keys the figures read | a renamed or missing key |
| F2a | the character statistics' null p95 rises with `L`; the shingle statistics' stays ≤ 0.01 | a non-monotone or drifting null |
| F2b | `eps*(OR) ≥ max(members)` and `eps*(AND) ≤ min(members)` in `spike_v4` | a fusion that breaks the bound |
| F2c | the stratum mismatch inflates the rate and the reweighting restores `alpha ± 0.05` | a repair that does not repair |
| F2d | `share(L)` reaches alpha first at the recorded `L*` | a floor recorded at the wrong length |
| F3 | no censored value reaches a coordinate | a censored cell plotted as 0 |
| F4 | every drawn element lies inside its canvas | a clipped or overflowing label |
| F4b | the F4 check **catches** a planted out-of-canvas element | a check that cannot fail |

## Why SVG and no plotting library

The package's rule is that every script imports the standard library only, so that no third-party
version's arithmetic can enter a comparison and the reproduction needs no dependency pin (README,
*Tolerance*). A figure generator is part of that: `make_figures.py` writes SVG directly, so the
figures reproduce byte-for-byte like everything else, and `reproduce.sh` compares them the same way.
