# Issue #142 — The Knob Is Not the Curve

**Contribution level: `theory+empirics`.** This package is the evidence layer for the manuscript: one
theory model (an envelope identity, an error budget with a derived span law, and an identifiability
set) validated on **two mechanically different priced systems**, with **ground truth exact by
construction** — every reported quantity is a closed form or an exact evaluation of one, and the only
sampling anywhere is the Monte-Carlo certificate that the closed forms describe the simulated system
plus the draws of the noise ladder. There are no timings anywhere in the package.

## Reproduction

```
cd papers/issue-142 && bash reproduce.sh
```

* **Expected output**: `REPRODUCE: ALL GREEN`, preceded by one line per step.
* **What it recomputes** (it is not a checksum check over committed outputs):
  * **The research instruments.** Each of `spike_ident_v0.py … spike_ident_v6.py` is re-run **from its
    own code** in an isolated temp copy of the package, and the fresh report is compared
    **byte-for-byte** (`Tolerance: exact`) against the report this package ships. Each instrument's
    **plant battery** runs first and its verdict is read from what it **prints** — `v1` prints
    `SELFTEST: ALL PASS`, `v2–v6` print a JSON summary (`passed` / `total`, required equal and
    non-zero). **`v0` has no plant battery** and the script says so rather than implying one.
  * **The figure set.** `make_figures.py --check` re-renders all four PNGs from the committed reports
    and compares them byte-for-byte.
  * **The reference layer, offline.** `refscan142.py --gate` (12 checks) binds the committed
    verification receipt to the shipped pool **by sha256**, requires the network-written
    `refs/canonical-status.json` carrier to be present (a report built without it states `0
    unresolved`, which is a read of nothing), and requires the pool's digest to be quoted **only** by
    the two generated carriers -- a digest written into prose is a value no generator maintains.
    `refscan142.py --selftest` re-runs its 21-check matching battery, and `refscan142.py
    --gateselftest` **fires every gate check on a throwaway copy of the package** (10 plants: one
    healthy control plus a planted defect per check), because a check that has never failed is
    decoration and this gate reads the package in place.
  * **The manuscript.** `build_manuscript.py --check` proves the shipped `manuscript.md` is exactly
    what `manuscript.src.md` builds, and `--selftest` runs its 13-check plant battery.
  * **The build the seals are scoped to.** Step 6 re-checks every seal it can under a **second
    interpreter** (`PYTHON2=…` overrides the search) and names each leg it cannot run — see
    *What seals each receipt*.
* **Exit status**: `0` = `REPRODUCE: ALL GREEN`; `1` = at least one step FAILED (the count is printed).
  A missing dependency aborts with a named message rather than a traceback.
  **A `NOT RUN` leg is never a pass**: step 6 re-checks every seal it *can* under a second interpreter,
  names each leg it cannot run together with the build that seal is scoped to, and the verdict prints
  the count — so `ALL GREEN (1 leg(s) NOT RUN …)` cannot be read as "everything was measured".
* **Environment**: CPython **3.9.6** with **numpy 2.0.2** and **matplotlib 3.9.4** (macOS, measured
  2026-10-16). The research instruments need numpy, the figure step needs matplotlib; the reference
  layer and the manuscript build are standard library only. Override with `PYTHON=/path/to/python3`.
  **The interpreter's PATH is deliberately not recorded in any report**: `sys.executable` is an
  *invocation* coordinate — it changes with how the interpreter was reached — so an artefact carrying
  it reproduces only under the exact invocation that wrote it. That was measured: `v3`, `v4` and `v5`
  did not all reproduce under one command, and `v3`'s shipped copy recorded a different interpreter
  than `v4`/`v5`'s. The build string is now exactly `python <version> / numpy <version>` and
  `reproduce.sh` **checks that shape** (a strict regex, so a path cannot slip back in unnoticed).
* **Inputs**: none, and no network. Every key set is generated from the seeds committed inside the
  instruments. The reference layer's **live** verification is a separate, documented network pass
  (`refscan142.py --verify`, see *Reference layer*); the offline gate re-checks the committed receipt
  without touching the network.
* **Cost**: about **four and a half minutes** (the `v0` grid dominates at ~4 min; every other step is
  seconds).
* **Writes nothing inside the package**: the instruments run in a private temp directory that the
  script removes.
* **Second tier**: `REPRO_FULL=1 bash reproduce.sh` re-runs every instrument a **second** time in a
  fresh temp copy and compares the two fresh artefacts — the determinism certificate.

## What seals each receipt, and where that authority is pinned

"Verified", "sealed" and "reproduced" are claims about **who** did the sealing, so each receipt this
package ships names the key that seals it and where that key's authority comes from — a value moved
into a sealed artifact has only moved the question one layer down unless the sealing authority is
itself resolved. The reference layer's field-level seals are tabulated under *Reference layer*; this is
the rest of the package.

| Receipt | The claim | The sealing key | Where the authority is pinned |
|---|---|---|---|
| `spike_ident_v*.py` / `_results.json` | this output is what this code computes | re-run **from its own code** in an isolated copy, compare bytes | **The BUILD, and the code's own prerequisites** — see below. Not provenance: byte-equality is a claim about the output, so any producer of these bytes passes |
| `figures/*.png` | the figures follow from the committed reports | re-render and compare bytes | **The BUILD** (CPython + matplotlib versions) |
| `manuscript.md` | exactly what `manuscript.src.md` builds | `build_manuscript.py --check` (byte equality) | **Build-independent** — measured under 3.9.6 *and* 3.13.9 |
| the pool gate's verdicts (`GATE n/n`) | the shipped pool is complete and internally consistent | `refscan142.py --gate`, read from what it prints | **Build-independent** — measured under 3.9.6 *and* 3.13.9 |
| each instrument's plant battery (`SELFTEST: ALL PASS`, `passed/total`) | the checks can still fail | the instrument, read from what it **prints** (never from the exit code alone) | the instrument's own build |

**The build each byte-equality seal is scoped to, and what `reproduce.sh` does about it.** A
byte-equality seal answers *"who?"* with *"anyone who writes these bytes"* — it is a claim about the
**output**, never about the producer — so its sealing authority is the build that produced the bytes.
Two interpreters that disagree produce two different "correct" answers, and a same-machine second run
cannot tell one from a defect. `reproduce.sh` therefore carries a **build-independence leg** (step 6):
it re-checks every seal it can under a second interpreter, and names every leg it cannot run.

* **Measured on this machine** (2026-10-17): `python 3.13.9` agrees with the pinned `python 3.9.6 /
  numpy 2.0.2` build on the **stdlib seals** — the manuscript build and the reference gate.
* **Not run here**: the instrument reports and the figures. Three interpreter builds are reachable on
  this machine (3.9.6, 3.12.12, 3.13.9) but **only one of them carries numpy/matplotlib**, so those
  legs are reported `NOT RUN` and the seal stays scoped to the pinned build. On a machine with a second
  build that has the libraries, the leg runs `v6` and the figure re-render across the two builds; where
  it cannot, the line says so rather than passing quietly.
* **The code's own prerequisites are named because they are part of the seal**: the instruments import
  each other by **name** (`v6` imports `v1`), and that import resolves through `sys.path[0]` — the
  *script's own directory*, not the working directory. An instrument is therefore runnable only when
  its siblings sit beside it; `reproduce.sh` copies the whole set into the isolated directory for
  exactly this reason, and an isolated one-file copy fails with `ModuleNotFoundError` rather than
  silently measuring something else.

## Layout

| Path | What it is |
|---|---|
| `manuscript.md` | The built paper (do not edit — edit the source and re-run the build) |
| `manuscript.src.md` | The source: prose plus `{ref:KEY}` citation seats and `{{FIG:key}}` figure blocks |
| `heilmeier.md` | The registered direction: the six Heilmeier answers, the adversarial checks, and the prior beliefs with the direction each was expected to take |
| `build_manuscript.py` | Resolves every citation against the verified pool and every figure block against `figures/captions.json`; fails on an unknown key, a cited key with no stated difference, fewer than 100 cited references, a stray placeholder, a figure whose image is absent, or a declared figure the text never embeds |
| `make_figures.py` | Renders the four figures from the committed reports; every plotted value is read out of a report (never typed) and a missing key is a hard failure |
| `figures/` | The four PNGs, `CAPTIONS.md` (human) and `captions.json` (the build's single source for captions and alt text) |
| `reference-check.md` | Citation authenticity report (journal bar item 12), generated by `refscan142.py --checkdoc` |
| `reference-pool.md` | The verified pool as a readable table |
| `refs/pool.json` | The verified reference pool — 826 entries (803 arXiv, 23 Crossref) |
| `refs/canonical-status.json` | The network discovery step's own record of which canonical works were **matched** and which stayed **unresolved** (3) -- a carried artefact: `--checkdoc` refuses to generate the report without it, because its absence would print `0 unresolved`, a read of nothing |
| `refs/differences.json` | The one-line stated difference for each of the **152 cited** entries |
| `refs/verify-run.txt` | The verification receipt. Its first line binds the shipped pool by sha256 -- that file is where the digest lives, and it is **not** repeated here: a digest written into prose is a value no generator maintains, and an earlier draft of this table went stale when the pool changed. `refscan142.py --gate` enforces both halves (every quoting site must quote the shipped pool's digest, and no file outside the two generated carriers may quote it at all) |
| `refscan142.py` | Reference discovery, verification, gate, plant battery and report generator |
| `spike_ident_v0.py … v6.py` | The seven research instruments, each with its own report |
| `spike_ident_v*_results.json` | The reports every manuscript number is read from |
| `reproduce.sh` | The one command above |

## Reference layer

Discovery is **declarative and external**: 42 arXiv `search_query` queries derived from the paper's
subject (never from a system name) and 32 canonical works looked up in Crossref **by title**, plus an
arXiv-by-title route for works Crossref has no record for. Curation requires a **named subject object**
and excludes off-domain work by title. Every pool entry is then re-fetched from its live endpoint and
its **title** compared with the stored title (the smaller of the two coverage fractions, threshold
0.80) — a resolver that merely answers is not verification.

Live state at the last run: `VERIFIED 826 / 826 ; TITLE MISMATCH 0 ; TRANSPORT-UNKNOWN 0`. Three
canonical works are **reported unresolved rather than entered on a remembered identifier** (a
technical report, a book whose only Crossref record is a *review*, and a paper whose Crossref record
carries a different title); `reference-check.md` lists them with their best title score.

### The reference layer's own seals

"Sealed", "attested" and "verified" are claims about **who** did it, so each carrier below states the
key that seals it and whether that key's authority comes from **outside** the auditee. Naming these is
the point: a value moved into a sealed artifact has only moved the question one layer down unless the
sealing authority is itself resolved.

| Carrier (the seal) | The claim it seals | Who seals it | Where the authority is pinned |
|---|---|---|---|
| `refs/verify-run.txt` first line (it names the pool it verified, by sha256) | the receipt is about **these bytes** | `refscan142.py` computes the digest of `refs/pool.json` | **Self-declared, and stated as such.** The digest is over the pool's bytes, so a *different* producer writing the same bytes gets the same receipt: the claim is **byte-identity**, never provenance. `--gate` binds the receipt to the shipped pool and fires on a receipt from another pool |
| the 0.80 title comparison (one row per entry in the receipt) | the record at this identifier is the record we cite | the endpoint — Crossref by DOI / arXiv by id | **External.** The identifier is the entry's own, and the endpoint is outside the auditee. Measured strength of the bar: over all 340,725 wrong pairs the pool can form, **3** reach 0.80 (max 0.8889, an arXiv pair differing by one word), so the bar is wide enough to admit a wrong record in principle; the by-title route below is where a wrong entry could actually be *entered*, and its margin is checked |
| `matched_title` / `match_score` on a canonical entry | this record IS that canonical work | `refscan142.py`, by title match at the same 0.80 bar | **External, with the margin re-derived at gate time:** `--gate` re-computes the score from the shipped title and requires (i) it still clears 0.80, (ii) it equals the recorded value, and (iii) **no competing pool entry reaches the bar** against that canonical title. Live values: 23 matches, minimum intended margin **0.8889**, strongest competitor **0.5455**, minimum gap **0.4444** |
| `refs/canonical-status.json` | the matched / unresolved split of the canonical list | the Crossref and arXiv endpoints | **External.** Network-written; the gate asserts the carrier is shipped, because a report built without it states `0 unresolved` — a read of nothing |

**The harvest cache has a stated amendment path** (`merge_record`). A re-sighting (same id, same
compared fields) is a no-op that only accumulates provenance. A collision whose compared fields
**differ** is an amendment: the live fetch wins — the later fetch *is* the fresher record — and the
overruled values are kept on the entry under `superseded`, with the count printed per query as
`amended=N`. Order-dependence is inherent to a persisted cache and is stated rather than claimed away;
what is not acceptable, and what this replaced, is a first-write lookup that **stored the correction
and ignored it**, making a divergence both silent and unrepresentable. The store's bookkeeping never
reaches the pool (`curate` strips it), so the seal above is unaffected by it.

The **live** pass is a network operation and is not part of the offline `reproduce.sh`:

```
python3 refscan142.py --verify      # re-fetch every entry; writes refs/verify-run.txt
python3 refscan142.py --checkdoc    # regenerate reference-check.md from the pool + receipt
```

## Manuscript numbers

Every quantity in the paper is read from one of the committed reports, and `build_manuscript.py`
resolves the citations and figure blocks it prints. The registered prior beliefs and the adversarial
checks behind the direction are in `heilmeier.md`.
