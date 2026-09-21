# The reference pipeline (stage 1): the search, and what it measured

This directory holds the instrument that produced the manuscript's bibliography. Stage 1 (this commit)
establishes the **search form** and measures the two limbs; the selection of the entries and their
one-line differences is `../references.json` and the report is `../../reference-check.md`.

## The form (a window is a coordinate, not a word)

| limb | index | date field | window (both endpoints written) | terms |
|---|---|---|---|---|
| pass 1 | arXiv API (`export.arxiv.org`) | `submittedDate` | `[2026-01-01, 2026-09-21]` (W1, "hot") and `[2018-01-01, 2025-12-31]` (W2, "classic") | 18 queries (`refs_harvest.py` lists them verbatim) |
| pass 2 | arXiv API | `submittedDate` | `[2015-01-01, 2026-09-21]` (one wide window) | 20 narrow queries, relevance-sorted (`refs_harvest2.py`) |
| classical limb | Crossref REST API | `query.bibliographic` (a *title* search; no window — the records are named works) | n/a | 57 titled works (`refs_classic.py`) |

**Scan date: 2026-09-21.** The window is read against the work it bounds: the newest related work the
manuscript cites is inside it.

**A coordinate arXiv does not offer, stated as unavailable:** arXiv exposes one date filter (the submission
date) and **no filter on a paper's latest version**, so a paper revised into relevance after its original
posting is invisible to a window that reaches only the posting. The Crossref limb reads one of Crossref's four
date fields (`published`); `created`, `published-online` and `print-publication` are **not read** here.

## What the search measured

```
pass 1   18 queries, window `submittedDate`   ->  412 unique arXiv records
pass 2   20 queries, one wide window          ->  589 unique arXiv records
classical  57 titled works, Crossref          ->   25 matched, 32 NOT FOUND
```

## Two limbs, and the reason the second replaced the first

**The recalled-DOI limb was retired, and its failure is measured here.** The first version of the classical
limb queried **40 DOIs recalled from memory**. **8 returned no record at all**, and several that returned one
named **a different work than the entry claimed** — recorded in `refs_form.json` →
`recalled_doi_limb.substitutions`:

| DOI queried | the entry it was meant to carry | the record the registry returned |
|---|---|---|
| `10.1214/aos/1013699998` | random features | *The control of the false discovery rate in multiple testing under dependency* |
| `10.1162/089976698300017746` | kernel regression | *Natural Gradient Works Efficiently in Learning* |
| `10.1103/RevModPhys.75.715` | quantum information and computation | *Decoherence, einselection, and the quantum origins of the classical* |
| `10.1103/RevModPhys.74.1` | quantum computation and information | *Optical simulations of electron diffraction by carbon nanotubes* |
| `10.1126/science.1058040` | quantum algorithms | *The Sequence of the Human Genome* |
| `10.1103/PhysRevLett.80.4811` | quantum computation with few qubits | *Breakup of Spiral Waves into Chemical Turbulence* |

A DOI recalled from memory is therefore **a claim the registry refutes**, and the classical limb was rebuilt
the other way round: **the title is the query, the record is the answer, and the entry is written from the
record the search returned**. A resolved DOI is never taken on the entry's word for what it names.

**The identity test is strict, and the strictness is measured.** The first title limb accepted a hit on
three shared words; it substituted, among others, *Quantum-Efficient Kernel Target Alignment* for
*On Kernel-Target Alignment*, and *Kernel Matrix Completion by Semidefinite Programming* for
*Learning the Kernel Matrix with Semidefinite Programming*. The committed rule is a **stopword-free
title-token Jaccard ≥ 0.85** (`refs_classic.py` → `jaccard`), and every query's verdict — with the top hit's
score and the near-misses the loose rule would have taken — is recorded in `refs_form.json` →
`classical_limb`. The 32 NOT FOUND verdicts are the honest output of a strict test, not a failure to search:
those works are simply not in the bibliography (a work that cannot be identified is not cited).

## Files

| file | what it is |
|---|---|
| `refs_harvest.py` | pass 1: the two windows, the broad terms |
| `refs_harvest2.py` | pass 2: one wide window, the narrow terms (`-show` prints the pool) |
| `refs_classic.py` | the classical limb: title search + the strict identity test |
| `refs_select.py` | buckets the pools by the claim a work will carry (helps selection, asserts nothing) |
| `refs_prune.py` | writes the committed evidence (`refs_form.json`) without the raw bulk |
| `refs_form.json` | **the committed result of this stage**: the form, the counts, both limbs' verdicts |

The raw pools (~2.6 MB) are **not committed**: they are regenerable from the scripts above plus the stated
form (`python3 refs_harvest.py && python3 refs_harvest2.py && python3 refs_classic.py`), and every entry that
enters the manuscript is committed in `../references.json` with the record it was read from.

## Stage 2: selection, entry form, verification (`R404`)

Files: `refs_selection_v87.py` (the authored part — one entry per work, keyed by its identifier, each with the
one-line `Difference:`), `refs_build_v87.py` (resolves every record from the committed pools and formats the
house entry form), `refs_verify_v87.py` (reads every entry at the index that owns it and writes the report),
`refs_render_v87.py` (renders the block the manuscript embeds).

**169 entries** (125 arXiv, 44 DOI), of which **169 found and identity-matched** — the read returns the record
and compares its title with the pooled title the entry's difference line was written against.

### Controls (all pass; the instrument can report absence)

| control | item | reading |
|---|---|---|
| C1 | known-present arXiv id `2608.29422` | found |
| C1 | known-present DOI `10.1093/biomet/6.1.1` | found |
| C2 | known-absent arXiv id `2401.99999` | reported NOT FOUND |
| C2 | known-absent DOI `10.9999/definitely-not-a-record-r404` | reported NOT FOUND |
| C3 | a corrupted title fed to the same matcher | detected as a mismatch |

### What the controls caught in this round's own work

* **Two hand-transcribed identifiers were wrong** (`2505.24324` and `2509.15047`, both recalled from a listing
  whose year prefix was `2605`/`2609`). The pool lookup refused them: *"not found in the committed pools"*. The
  same failure mode at registry scale is the retired DOI limb's (see stage 1) — an identifier recalled by hand
  is a claim, not a citation.
* **One DOI was dropped rather than printed without a year** (`10.1201/9780429500459-11`): its Crossref record
  carries no publication date, and the house form requires a year.
* **The journal's own gate read the entry form back and found one entry outside its window**: the mononym
  `Student` needed the period the house form's second admitted shape carries (`Student. (1908). …`). With it,
  the gate reads `author form: 169/169`.
* **The gate needs Python >= 3.12** (its f-string fixtures fail on the system `/usr/bin/python3`, 3.9.6); the
  readings below were taken with `/Users/argszero/.local/bin/python3.12`.

### The journal's own instrument over the rendered block

```
window: the last `## References` heading (line 1) to the end of the file (line 339)
entries=169  numbering=[n]
block form: 169 entries, 0 of them not separated from the entry above by a blank line
author form: 169/169 entry(s) carry the read's window; 0 print the family name ALL-CAPS, 0 carry a character reference
in-text cited numbers=0  covered=0/169  coverage=0.0%
GATE: FAIL (uncited entries count as padding)
```

The coverage failure is the state of the work, not a defect of the list: the manuscript body that cites these
keys is the next stage, and the gate is to be re-run over the assembled manuscript where every key is reached.

### Counting rule the block satisfies

One `## References` section, numbered `[n]`, entries separated by a blank line, each entry on its own line,
`Family, I.` (or the lone-family-name form) · year in parentheses · title in title case · venue or identifier ·
resolvable URL · one-line `Difference:`. The raw pools (~2.6 MB) remain uncommitted and regenerable; the
committed record of what was read is `refs_built.json`, `refs_verified.json` and `../refs_form.json`.
