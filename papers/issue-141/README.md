# Issue #141 — The Score Is Not the Payoff: Rank-Gaming, Transport, and What an Evaluation Protocol Actually Measures

**Contribution level: `theory+empirics`.** One theory law with both directions argued and one
enumerated measurement: a protocol's ranking is faithful to payoff **iff** its score is a strictly
increasing function of the policy's own payoff-profile value — **0 mismatches** over 19 protocols ×
9 games — plus the exact finite-population measurement of what a violation costs (rank gain, transport
loss) over **684 cells** and **1,026 transport entries**. Ground truth is **exact by construction**:
every payoff is a `Fraction`, every statistic is an exact count or an exact rational, and the space is
**enumerated rather than sampled** — there is no seed, no draw and no timing anywhere in the package.

**What this evidence is not.** The space is in-silico and declared. It establishes what protocols
*can* do; it is **not** evidence about what any deployed benchmark *is* doing. The journal's
synthetic-data rule (issue #2318) is met by claiming no more than that, and §9 of the manuscript says
so before §4–§8 report anything: there is no real-leaderboard arm, and none is claimed. One game
(`cv_n4`, the four-bidder common-value auction) carries **no certified anchor** and its cells are
in the counts without independent confirmation — carried in the abstract's claim boundary, not
buried.

## Reproduction

```
cd papers/issue-141 && bash reproduce.sh
```

* **Expected output**: `REPRODUCE: ALL GREEN`, preceded by one line per step. Measured
  2026-10-20: 28 steps green, **0 legs NOT RUN**, about 5 minutes.
* **What it recomputes** — it is not a checksum check over committed outputs:
  * **The five research instruments.** `spike_v0.py … spike_v4.py` are re-run **from their own code**
    in an isolated copy of the package, and each fresh artefact and each fresh report text is compared
    **byte-for-byte** (`Tolerance: exact`) against the one this package ships. Which artefact an
    instrument writes, and through which flag, is stated per row in the script: `v0`/`v3`/`v4` write
    `*_results.json` through `--out`; **`v1` and `v2` ship a differently-named side artefact**
    (`spike_v1_theory.json`, `spike_v2_design.json`) and write it the same way; the report texts come
    from **stdout** for `v0`–`v2` and through `--report` for `v3`–`v4`.
  * **Seven plant batteries**, each read from what it **prints** and never from the exit code alone.
    Three printed verdict forms exist in this package — `SELFTEST 23/23`, `35/35 certificate items`,
    and a named `SELFTEST: ALL PASS` / `REFSCAN: ALL PASS` / `FIGURES-SELFTEST: ALL PASS` — and the
    reader accepts only positive evidence: a battery that prints **none** of them fails rather than
    passing by silence, and one whose two counts disagree fails too. When a battery prints a named
    verdict without a count, the count reported upward is the number of `] ok` lines it actually
    printed, **read off the output**: a reader that maps `ALL PASS` to a hard-coded `1/1` reports the
    same figure for a 9-check battery and a 29-check one, which is the defect it is meant to catch.
  * **The two censuses** (`census_excess_entries.py`, `census_converse_scope.py`), artefact and report
    text, plus each one's printed `certificate n/n` line.
  * **The figure set.** `figures.py --check` re-renders all three PNGs **from the JSON alone** and
    compares them byte-for-byte; `figures.py --selftest` runs its own invariant battery.
  * **The numeric gate.** `canonical.py --selftest` re-derives all **103** canonical numbers from the
    shipped artefacts (26 checks including plants); `check_numbers.py` then proves that **every number
    the manuscript quotes is annotated with a key that file emits AND that the value appears in the
    paragraph that quotes it** — 36 annotation blocks, 111 keys.
  * **The manuscript.** `refscan141.py --render` numbers the citations in order of first appearance and
    rebuilds `manuscript.md` from `manuscript.src.md`; the shipped file must be exactly what its own
    source renders to. The same step is the citation-integrity gate (see *Reference layer*).
  * **The reference layer, offline.** `--select` requires every chosen work to resolve to a verified
    record in the store; `--reaudit` re-derives every canon verdict from those records; `--selftest`
  runs 32 checks including 12 plants. Then the **journal's own
  gate** (`.github/tools/refgate.py`, run from the repository root exactly as the citation item
  names it) reads `manuscript.md`; it is not vendored here, so outside the repository that leg is
  `NOT RUN` with that reason rather than a silent pass.
* **Exit status**: `0` = `REPRODUCE: ALL GREEN`; `1` = at least one step FAILED (the count is printed).
  A missing dependency aborts with a named message rather than a traceback.
  **`NOT RUN` is never a pass**: a leg that could not run is named with its reason and counted in the
  verdict line, so `ALL GREEN (1 leg(s) NOT RUN …)` cannot be read as "everything was measured".
  `DIFFERS` is reserved for a run that **completed** and produced different bytes.
* **Environment**: CPython **3.9.6** with **numpy 2.0.2** and **matplotlib 3.9.4** (macOS, measured
  2026-10-20). That is the whole third-party set and it is an **import census**, not a memory: over the
  package's twelve scripts `import numpy` and `import matplotlib` appear in exactly two
  (`census_converse_scope.py`, `figures.py`); everything else is standard library — `fractions`,
  `json`, `hashlib`, `itertools`, `subprocess`, `urllib`, `xml`, `unicodedata`, `collections`.
  **Nothing imports scipy.** The script's opening probe imports the whole declared set, so a missing
  package is named before any instrument runs. Override with `PYTHON=/path/to/python3`.
* **Inputs**: none, and **no network on any step whose verdict is reported**. Every grid is enumerated
  from constants inside the instruments; there is no seed anywhere, because there is no sampling
  anywhere. The one networked stage (`--discover`) is described under *Reference layer* and is not
  part of the reproduction verdict.
* **Writes nothing inside the package**: all scripts run against a private copy that is removed on
  exit, so a reproduction run cannot repair the artefact it is testing. (Verified after the run:
  `find . -newermt '-10 minutes'` returns only `reproduce.sh` itself.)
* **Cost**: about five minutes (measured 4m43s). Instrument `v4`'s certificate dominates — it
  re-derives the headline from the artefact **read off disk** and runs a second process for its
  determinism check.
* **Plant tier (opt-in)**: `PLANT=1 bash reproduce.sh` fires each reader on **the defect it names** and
  requires it to fire — the verdict reader on a disagreeing pair of counts and on silence, the artefact
  comparison on a one-byte change, the render on a citation with no record, the figure comparison on a
  one-byte change in a PNG. Measured 2026-10-20: **7 of 7 fired**. Costs about 15 s.

## Prior beliefs, and what happened to them

Registered before the study ran (`heilmeier.md`, and the issue body); each is reported in the
manuscript as the section that tests it.

| Prior | Registered prediction | Outcome |
|---|---|---|
| **P1** | the rank gain is positive in a majority of cells | **confirmed** — 474 of 684 cells (69.3 %), flat along the `n` ladder (50–55 of each game's 76) |
| **P2** | the spread across protocols exceeds the spread across populations | **confirmed, and more strongly than registered** — the protocol's mean square exceeds the population's in 9 of 9 games, from 3.929× (`cv_n4`) to 52.132× (`spsb_n2`) |
| **P3** | the protocols that let rank be bought are the same protocols whose ordering fails to transport | **refuted, with a direction** — the two are strictly nested (474 gameable strictly inside 564 fragile, **0** counterexamples to `G > 0 ⇒ τ < 1`), and one constructed design is the worst in the space by rank-gaming and **exactly zero** by transport |

P3 is the paper's strongest result and it is a contradiction of our own registered, theory-anchored
prior. It is reported as such in §6, where the band that carries it (90 cells fragile with nothing
buyable) is stated as the reason a gaming audit is the smaller of two audits.

**What the study can detect** (issue #2318, item 14). This is an enumeration, not an estimate: every
count here is exact and its sensitivity is its own domain — "0 mismatches over 19 protocols × 9 games"
means no counterexample **in this space**, and the manuscript says exactly that, with the universality
of the law beyond the space labelled a conjecture carrying evidence rather than a theorem (§9.2). No
result in the paper sits below a noise floor, because there is no noise to sit below; the limitation is
**scope**, not sensitivity, and the threats section spends its words on scope.

## What seals each receipt, and where that authority is pinned

| Receipt | The claim | The sealing key | Where the authority is pinned |
|---|---|---|---|
| `spike_v*_results.json`, `*_report.txt` | this output is what this code computes | re-run **from its own code** in an isolated copy, compare bytes | **The build** (CPython + numpy) and the code's own prerequisites — see below. Not provenance: byte equality is a claim about the output, so any producer of these bytes passes |
| `figures/*.png` | the figures follow from the committed artefacts | re-render from the JSON and compare bytes | the build (CPython + matplotlib) |
| `manuscript.md` | exactly what `manuscript.src.md` renders to | `refscan141.py --render` (byte equality) | build-independent — standard library only |
| `canonical.py`'s numbers | every quoted number is re-derivable from the artefact that holds it | `canonical.py --selftest`, 26 checks with plants | the artefacts themselves |
| `check_numbers.py`'s verdict | each number's **annotation** points at an emitted key **and** the value is in its own paragraph | `check_numbers.py` | build-independent |
| each plant battery (`23/23`, `ALL PASS`, …) | the checks can still **fail** | the instrument, read from what it prints | the instrument's own build |
| `refs/canonical-status.json` + `refs/selected-status.json` | each cited work resolved to a real record, by a named route | `refscan141.py --select` (+ the report generated by `--checkdoc`) | the two APIs named in the report |
| `refs/differences.json` | every one of the cited works states, in its own line, what it says that this paper does not | `refscan141.py --render`, which **refuses** a cited work with no stated difference | the recorded keys; the file is an input to the seal above, so it is committed with it |

**The build each byte-equality seal is scoped to.** A byte-equality seal answers *"who?"* with
*"anyone who writes these bytes"* — a claim about the output, never about the producer — so its
authority is the build that produced the bytes. Two interpreters that round differently produce two
different "correct" answers that a same-machine second run cannot tell apart. Here the risk is small
and stated rather than denied: **every quantity in this package is an exact `Fraction` or an integer**
(`fractions.Fraction`, `collections.Counter`), so floating point enters only in the *reported
decimals* of the two censuses, and those are compared as bytes on the pinned build. A second
interpreter carrying numpy/matplotlib is **not available on this machine** — four CPython builds are
reachable here (3.9.6 at `/usr/bin/python3`, 3.12 and 3.13 under `~/.local/bin`, the daemon's own
`~/.emrg/install/bin/python3`) and **only 3.9.6 carries the libraries**: measured 2026-10-20, the other
three fail on `import numpy`. So `reproduce.sh` does **not** claim a cross-build seal; the leg would be
`NOT RUN`, and the claim is scoped to `CPython 3.9.6 / numpy 2.0.2 / matplotlib 3.9.4`.

**The code's own prerequisites are part of the seal.** `spike_v3.py` imports `spike_v0` and
`spike_v2`; `spike_v4.py` imports `spike_v3`, `spike_v2` and `spike_v0`; `check_numbers.py` imports
`canonical`; those imports resolve through
`sys.path[0]`, the *script's own directory*. The copy `reproduce.sh` makes is therefore of the **whole
package**, not of the scripts alone: an instrument run from a one-file copy would fail on a missing
sibling, and — worse — a copy without `spike_v4_results.json` would break `v4`'s certificate, which
re-derives its headline from that file **read off disk**.

## Reference layer

132 works are cited in the manuscript, each of them verified against a real record. The report is
`reference-check.md`, **generated** by `refscan141.py --checkdoc` — never hand-edited, and written at
the **package root** because that is the path the journal's completeness bar names.

* **Two independent tests per entry, never one.** A title score alone is not a match. Measured on this
  very list (2026-10-20): `Optimal Multi-unit Auctions` (Maskin & Riley, 1989) scores **0.80** against
  `Optimal multi-unit combinatorial auctions` (2011) — a **different paper**; and `Equilibrium Points in
  N-Person Games` scores **1.00** against a **2020 JSTOR reprint** of the 1950 paper — the right work in
  the wrong edition, which a score cannot see either. So the year is a **second, independent** test, and
  the report carries three states: `matched`, `matched-edition` (a reprint is sometimes the only
  registered record — the citation then prints the **original's** year and names the record verified),
  and `unresolved` (listed with its nearest miss and why it was not entered). A **third** test
  decides the edition state: where the years disagree, the title is exactly what cannot confirm the
  work, so the record must carry an **author** to corroborate it. That test is not decoration — it
  removed a real false citation from this bibliography: `Auction Theory` (declared 2002, Krishna)
  scored **1.00** against a chapter of the 2021 Cambridge Element *Economics of Visual Art*, a chapter
  whose record carries no author and whose subject this paper never touches. It is `unresolved` now,
  and the sentences it was cited for cite Klemperer's verified literature guide instead.
* **The canon, by title.** 39 works a referee would expect the paper to know, searched by title against
  two Crossref routes and one arXiv title route: **24 matched** (4 of them another edition), **15
  unresolved**. A work that cannot be found is reported unresolved, **never** entered on a remembered
  DOI.
* **The bibliography, by identifier and by discovery.** `refs/raw.json` holds **1,985** records: the
  works the canon pass verified, four verified **by the identifier the text prints** (`--byid`: three
  `arXiv:` ids and one DOI, each fetched from the API that owns it), and **1,978** returned by a
  40-query arXiv subject scan (`--discover`, checkpointed after every query so a later failure cannot
  discard the expensive part). A pool of the **1,840** that survive the declared off-domain filter
  (28 canonical, 1,812 discovered) is derived by `--pool`; it is **not shipped**, because it is a
  filter over `raw.json` that no offline step reads, and a derived duplicate in the tree is a second
  carrier to go stale. `refs/selected.json` is the **declared** bibliography — each entry with its
  section and its role in the argument — and `--select` refuses a key that resolves to no record.
* **A citation must be used.** `--render` refuses to write when a cited key has no verified record,
  when a chosen work is **never cited in the body**, or when fewer than **100** works are cited. That
  is the journal's item 13 as a mechanical check rather than a count someone retypes: the bibliography
  is the list of what the prose cites, in the order the prose first cites it.
* **The entry form.** Every entry is one line in the journal's order: the marker `[n] `; the authors
  as `Family, I.` (family name first, `et al.` for four or more); the year in parentheses; the title
  in title case; the venue or the identifier; a resolvable URL; and the entry **closing with its
  one-line `-- Difference:`**. A record whose author field is empty does not print `n.a.` and does not
  print its container in the author position: it prints the absence **by naming the record that was
  read** (`author not established on Crossref for the DOI 10.1017/…`), and the same line appears in
  `reference-check.md`. `--render` refuses — writing nothing — when any cited work has no stated
  difference (`refs/differences.json`), so no entry can ship with a hole where that claim goes.
  A **blank line separates consecutive entries** and it is load-bearing rather than cosmetic: `[n] `
  markers are not an ordered list, so without it a CommonMark renderer reads the whole set as one
  paragraph and the entry boundaries disappear on the rendered page.
* **What is offline and what is not.** `--select`, `--render`, `--reaudit` and `--selftest` are
  offline and are in
  the reproduction verdict. `--discover`, `--canonical`, `--byid` and `--checkdoc` **touch the network**
  and are *not* part of it: they are the live verification pass, run when the bibliography changes.
  A route that could not run is named in the generated report (`NOT RUN: THROTTLED (HTTP 429)` is a
  distinct state from unreachable), and a 429 is **never retried in the same round** — retrying the
  throttle is what produced a 30-minute stall that wrote nothing on 2026-10-20.

## Layout

| Path | What it is |
|---|---|
| `manuscript.md` | The rendered paper (do not edit — edit the source and re-render) |
| `manuscript.src.md` | The source: prose, numbers annotated by `canonical.py` key, and `{{ref:key}}` citation seats |
| `reproduce.sh` | The one command above |
| `canonical.py` | The single source of truth for **103** numbers, each re-derived from the artefact that holds it, with 26 self-checks including plants |
| `check_numbers.py` | The gate over the manuscript's number annotations **and** its figure embeds (embedded, on disk, sha256 match) |
| `figures.py` | Renders the three figures from the JSON alone; `--check` rebuilds and compares; 9 invariants + 4 plants |
| `figures/` | The three PNGs and `captions.json` (filename → caption / file / sha256) |
| `spike_v0.py` | The v0 control: 7 protocols × 4 games × 4 populations, 112 cells — the instrument's two-sided control, where the faithful score reads exactly zero |
| `spike_v1.py` | The separation ladder: the threshold `λ_τ = 1/16 < λ_G = 1/8` |
| `spike_v2.py` | The 17-protocol design space of record and its nesting (`spike_v2_design.json`) |
| `spike_v3.py` | The transport arm on the narrow grid: 272 cells, 408 entries (P1 confirmed) |
| `spike_v4.py` | The wide grid: 684 cells, 1,026 entries, the design law, P1/P2/P3, the anchors |
| `census_excess_entries.py` | Census of transport-excess entries: 367 violators over the full domain, 262 in the record space (certificate 8/8) |
| `census_converse_scope.py` | Census of the converse's availability: reachable discordance 18 of 28, target 14 of 28 attained in exactly 3 games (certificate 16/16) |
| `analysis_transitivity_vs_transport.py` | The required-change-1 analysis: the transitivity coordinate of each game (7 of 9 at zero cyclic triples, 22 of 36 game pairs tied) against the transport excess, which takes up to 8 distinct values at a fixed game and population pair in **9 of 9** games — the reduction test, answered `no_reduction` |
| `refscan141.py` | Reference discovery, by-identifier verification, canon verdicts (`--reaudit`), selection, render, report, plant battery |
| `refs/selected.json` | The **declared** bibliography: 132 keys, each with its section and its role |
| `refs/raw.json` | 1,988 verified records as the APIs returned them — the discovery output itself, not a trimmed copy |
| `refs/canonical-status.json` | The canon pass's own record, re-derived under the current rules by `--reaudit`: 24 matched (4 editions), 15 unresolved — carried, because its absence would print `0 unresolved`, a read of nothing |
| `refs/selected-status.json` | `--select`'s verdict over the declared bibliography: 132 chosen, 132 with a record, 132 cited, 0 missing |
| `refs/differences.json` | The stated-difference input of the render: one line per cited key, 132 of 132 cited. The render **refuses** rather than print an entry with a hole where that line goes |
| `reference-check.md` | The citation authenticity report (journal bar item 12), **generated** by `--checkdoc` |
| `heilmeier.md` | The registered direction: six Heilmeier answers, adversarial checks, prior beliefs and the direction each was expected to take |

## Reading order for a reviewer

1. `manuscript.md` §2 (setup), §3 (the law), §6 (the refutation) — the three results.
2. §9 (threats) to see what is claimed about the world, which is deliberately little.
3. `reproduce.sh` green, then `PLANT=1` to see the checks fail on their own defects.
4. `reference-check.md` for the citation layer, `canonical.py` for any number that looks wrong.
