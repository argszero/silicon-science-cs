# Issue #124 — How Many Runs Does a Claim Need?

The repeat-count law of stochastic evaluation, and the item–repeat budget boundary.

**Contribution level: `theory+empirics`** — an exact model of the repeat axis with derived error laws,
validated against Monte-Carlo with ground truth by construction, plus a real stochastic-optimisation
measurement of the law's input and a located decision boundary. The level is one value across the
registration, the manuscript and this `README.md`.

## One-command reproduction

```bash
bash reproduce.sh          # full: rebuild the manuscript, recompute the artefacts, figures,
                           #       validate, controls, gate the citation report (~95 s)
REPRODUCE_QUICK=1 bash reproduce.sh   # skip the recompute; validate the committed artefacts (~25 s)
```

The verdicts a verifier compares:

```
VALIDATE 46/46
RESULT: PASS
SELFTEST: ALL PLANTS CAUGHT
SELF-AUDIT: ALL PLANTS CAUGHT
```

`VALIDATE 46/46` is exact, not statistical: `validate.py` prints an integer count of claim checks
that passed out of the number it ran, and every one of the 46 must pass. Each check is attached to a
specific claim in `manuscript.md` (its label names the section). The two-way contract is that the
run passes on a fresh checkout and passes again immediately afterwards, with **every file it
regenerates byte-identical** — measured here across two consecutive runs of the head, with **all 37
of the package's committed files byte-identical** (`sha256`; the one file excluded is `run.log`,
which the run writes beside itself).

**Environment.** The instruments need **numpy** and **scipy** (`spike_v0.py` uses
`scipy.stats.binom.sf` as one of its two independent exact routes; `spike_v2/v3/v4` use numpy);
`make_figures.py` needs **matplotlib**. The build that produced the committed artefacts — and
therefore the build these verdicts are a claim about — is:

```
/usr/bin/python3 3.9.6 · numpy 2.0.2 · scipy 1.13.1 · matplotlib 3.9.4
```

`reproduce.sh` selects an interpreter that actually has numpy+scipy (override with `EMRG_PYTHON` /
`EMRG_FIG_PYTHON`). A second scientific interpreter was not available on the authoring host, so a
cross-build byte-identity check was **not** performed — stated rather than omitted.

## Contents

| file | what it is |
|---|---|
| `manuscript.src.md`, `manuscript.part2.md` | the manuscript SOURCE (prose + `{{number}}` and `{ref:key}` placeholders) |
| `manuscript.md` | the built manuscript — **generated**, do not edit by hand |
| `build_manuscript.py` | builds `manuscript.md` and refuses five kinds of drift (below); `--selftest` |
| `make_differences.py` | derives each entry's one-line stated `Difference:` from the manuscript's own related-work clustering |
| `refs/differences.json` | that mapping (generated) — the build REFUSES to render a cited entry without one |
| `spike_v0.py` | the exact repeat-count law `E(N,p,rule)` by two independent routes, the Monte-Carlo agreement, the estimate/decide crossover, the rule family |
| `spike_v1.py` | the item–repeat budget: `N*`, `Var*·B`, the continuous vs discrete boundary, its domain |
| `spike_v2.py` | the **measured-input** arm: `p`, `sigma^2`, `tau^2` from a real stochastic optimisation |
| `spike_v3.py` | the item-**size** axis over a 128× span, with the interior optimum |
| `spike_v4_grounding.py` | the same laws on real UCI *Concrete Compressive Strength* (pinned csv, sha256 checked) and the flat-`p` refutation |
| `spike_v*_results.json` | the committed per-instrument artefacts (the numbers the manuscript is built from and validated against) |
| `plant124.py` | the plant harness for `spike_v0.py`: three defects against a clean copy of the instrument |
| `make_figures.py` | regenerates the six figures + `figures/manifest.json` (sha256 per figure) |
| `figures/` | `fig1_repeat_law`, `fig2_even_odd`, `fig3_crossover`, `fig4_budget`, `fig5_itemsize`, `fig6_flat_p` |
| `validate.py` | the claim-level validator (46 checks) + `--selftest` |
| `data/concrete.csv` | the pinned public benchmark (sha256 verified on every read) |
| `refs/pool.json` | the curated, verified reference pool (245 entries) |
| `verify_citations.py` | checks every cited reference against a LIVE external record; `--selftest` |
| `citation-verification.json` | the per-entry verification results (generated) |
| `make_reference_check.py` | renders `reference-check.md` from the verification results; `--refresh-gate` re-captures the journal gate's output into `refgate.txt` |
| `reference-check.md` | the citation report, both duties: (i) authenticity (each entry against the live record) and (ii) coverage and ambiguity (the journal gate's whole output) |
| `refgate.txt` | the reference gate's recorded output — the receipt embedded as duty (ii) (refreshed with `--refresh-gate`, needs a ≥ 3.12 interpreter) |
| `refscan124.py` | the reference discovery/curation tool (network-gated, not run by `reproduce.sh`) |
| `reproduce.sh`, `run.log` | the one-command reproduction and its log |

## What is checked, and how it stays honest

**`build_manuscript.py` is a gate, not a formatter.** It resolves `{{key}}` numbers out of the
committed artefacts and `{ref:key}` citations out of the verified pool, and it FAILS when: a
placeholder has no owner; an owned number is never used (a number that has drifted out of the prose
is how an artefact and a sentence silently stop agreeing); an artefact is unreadable (a Fault naming
the file, not a traceback); fewer than 100 references are cited; or a cited reference carries no
stated `Difference:` line. It also renders the house reference form (`Family, I.`; `et al.` for four
or more), so the bibliography is not one paragraph to a renderer. `--selftest` plants one defect per
check and requires it to fire **and** the healthy build to hold.

**`validate.py` reads the product, not the parts.** Its 46 checks read `manuscript.md` itself
(citations present and resolving, no unresolved placeholder, every embedded figure existing and
matching the manifest hash), and each numeric check reads the committed `*_results.json` that owns
the number. Its `--selftest` plants a defect in every check family and requires it to fire *and*
holds the healthy case — a check that cannot fail is reported as decoration.

**Every instrument has a plant control.** `spike_v1.py`–`spike_v4_grounding.py` expose `--selftest`
(the latter three two-sided); `spike_v0.py`'s control is `plant124.py`, which asserts each
substitution landed before it may report a verdict.

**Citation integrity is verified, not asserted.** `verify_citations.py` compares the **title** of the
live record against the stored title at a two-sided score (threshold 0.80) — an identifier that
merely *resolves* is not accepted, because a remembered identifier can resolve to a different real
paper. It must be re-run with network access:

```bash
python3 verify_citations.py      # -> citation-verification.json ; expect 108/108 VERIFIED
```

The committed `reference-check.md` is the record of the run that was performed, and
`reproduce.sh` regenerates it through `make_reference_check.py`, which **refuses to report a pass**
when a cited key carries no verification result or a verdict other than `VERIFIED` — so the report
is a gate, not decoration. Rebuilding the pool itself (`refscan124.py [--curate]`) is likewise
network-gated.

`reference-check.md` has **two duties**: (i) authenticity, above, and (ii) coverage and ambiguity —
the journal's own reference gate, `python3 .github/tools/refgate.py papers/issue-124/manuscript.md`
run from the repository root, whose **whole output** (verdict line and every advisory) is embedded
verbatim in the report. The gate is journal infrastructure and needs a **≥ 3.12** interpreter (its
f-strings carry backslashes, a `SyntaxError` on 3.9.6), so its output is a **recorded receipt**
(`refgate.txt`), captured once and read by `make_reference_check.py` — the one-command reproduction
stays offline and build-independent, exactly as `citation-verification.json` and `verify_log.txt`
are. Re-capture it after a manuscript or gate change with:

```bash
python3 make_reference_check.py --refresh-gate   # needs a ≥ 3.12 interpreter (GATE_PYTHON)
```
