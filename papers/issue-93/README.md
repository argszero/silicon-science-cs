# Issue #93 — When Does a Human Approval Gate Pay?

**Binding fidelity sets the net value of human-in-the-loop control for tool-using agents.**

This directory is the submission package: `manuscript.md` is the paper, and everything beside it is the apparatus
that produced and checks the paper's numbers. Contribution level: **theory + empirics** (a closed-form model with
ground truth by construction, plus instruments that enumerate it).

## One command

```bash
bash reproduce.sh
```

Expected output (the transcript of a run on the declared build, 2026-10-01):

```
== #93 reproduction ==
build          /usr/bin/python3 3.9.6 | numpy 2.0.2
instruments    7 instrument(s) ran, all exit 0 (report id(s) where printed: 96068d33 26061af1 2a4d41ce a124060c )
byte-identity  all 7 instrument reports byte-identical over two runs
digests        v0..v6 sha256(16): f1f17eecd45e136d a9855aff6f29e3dd fe9fc6cc35818fa7 8501a5956416acf8 8042cfd48b0e8272 b4df803b76b6e72e 4e9e8e1e200a99ac 
batteries      fired on every plant -- v0:20/20 alarms fired v1:12/12 alarms fired v2:15/15 alarms fired v3:7/7 alarms fired v4:caught: 13/13 v5:14/14 case(s) fired v6:18/18 case(s) fired
outcomes       OUTCOME CHECK BATTERY -- 24 case(s), 24 caught
section 5      SECTION 5 NUMBERS: PASS -- 52 claim(s), 0 missing
  batteries    BATTERY: 52 of 52 claim(s) fired when every token stating them was removed
references     stage 1: 24 checks, 0 failed | stage 2: 15/15 PASS with 22/22 mutations caught | stage 3: 8/8 PASS, 19-case battery
authenticity   REFERENCE CHECK: PASS -- 14 check(s), 0 failed | BATTERY: 11 of 11 case(s) fired
counts         the manuscript states the authenticity checker's count (14 checks, 0 failed)
counts         the manuscript states the authenticity battery (11-case battery, 11 fired)
citations      the product manuscript.md | citations 211 | distinct keys 121 of 121 built records
counts         the manuscript states the run's citation count (211 citations)
counts         the manuscript states the run's §5 claim count (52 claim)
counts         the manuscript states the built-record count (121 distinct keys of 121)
counts         the manuscript states the authenticity count (121 of 121 verified)
figures        CURRENT -- fig1_sign_law_and_cost_ratio.png is byte-identical to a fresh draw (sha256 87b55876492a8e93)
links          LINK CHECK: PASS -- 1 link(s), 1 local, 0 broken | BATTERY: 4 of 4 case(s) fired
bar            SUBMISSION CHECK: PASS -- 18 item(s), 0 failed, 2 declared | BATTERY: 8 of 8 case(s) fired
counts         the manuscript states the bar's own item count (18 item(s), 0 failed)
product        manuscript.md 130628 bytes, sha256 9872c7243e9e9c5c
counts         the README states the product digest this run produced (9872c7243e9e9c5c)

REPRODUCE: ALL GREEN
```

`REPRODUCE: ALL GREEN` and exit 0 mean every step's own reading passed. Every step runs a checker that exits
**non-zero when its own reading fails**, so a green line is never produced by a step that could not run: an
unreadable input, a missing artefact or a raised guard stops the step with `FAILED`.

## Tolerance, and the build

* **Tree form: the package alone.** `reproduce.sh` and every file it runs are self-contained in `papers/issue-93/` —
  the command needs **no working tree** and **no `research/`** (which is git-ignored and absent from any export of
  the branch). Every source a check reads is resolved relative to the package, never by an absolute path.

* **Tolerance: byte-identity.** The seven instrument reports (`gate_v*_results.json`) are deterministic — the model
  is enumerated, not sampled for the quantities the paper reports — and the run *measures* this by hashing them,
  running the instruments a second time and comparing. Any change is a failure.
* **The crc32 `report id` is a digest of a report, not a measurement.** A different interpreter or NumPy may move
  it, which is why the digests are printed for comparison instead of being asserted. The numbers the paper's
  claims rest on are compared exactly.
* **Build.** Read on Python 3.9.6 with NumPy 2.0.2 (macOS). `gate_v0`, `gate_v1`, `gate_v2`, `gate_v3` and
  `gate_v5` import NumPy (the Monte-Carlo route and the interval); the rest are pure Python. Override the
  interpreter with `PYTHON=/path/to/python3 bash reproduce.sh`; the script **exports** that choice, so the
  mutation batteries spawn the SAME interpreter rather than a hardcoded one (a battery that ignores `PYTHON`
  silently splits the run across two interpreters: a numpy-less default fails the gates while the batteries
  still pass). Full digests (sha256) of the reports on this
  build:

  | report | sha256 |
  |---|---|
  | `gate_v0_results.json` | `f1f17eecd45e136d98de09b5a9b1177f9b7a279e7b4cacf4939c84625d4a1164` |
  | `gate_v1_results.json` | `a9855aff6f29e3dd6dfc759323dd21a84aea889765214ef801497dc20ec76316` |
  | `gate_v2_results.json` | `fe9fc6cc35818fa7044be19817a7c003580e6a02fa124b6cb91d7994d7a15485` |
  | `gate_v3_results.json` | `8501a5956416acf82f03c5fd7b1eb5be8b744faa47159eb860887177287e57bd` |
  | `gate_v4_results.json` | `8042cfd48b0e82722f38ed84607ccfc12f08ee62a73fb2c032a27302e62c0617` |
  | `gate_v5_results.json` | `b4df803b76b6e72e7c8c5ebbf33ef348aa26532fae1b1e65ad296d1bc2be9ee3` |
  | `gate_v6_results.json` | `4e9e8e1e200a99ac0e98cced48ae6831ce63ec189ad22d8bd992079c4402f30b` |

* **Cost:** about three minutes (the instruments take ~11 s; the batteries, which re-run each instrument with one
  mutation per guard, ~82 s; the bar's own battery copies the package once per case).

## What each step is

| file | what it is |
|---|---|
| `manuscript.md` | the paper (Sections 1–7 + the numbered reference list, in first-citation order) |
| `figures/fig1_sign_law_and_cost_ratio.png` | Figure 1: the sign law and the boundary's dependence on the cost ratio |
| `gate_v0.py` … `gate_v6.py` | the seven instruments; each answers one question and carries its own guards |
| `v0_battery.py` … `v6_battery.py` | one plant per guard, with a plant that reaches no guard reported as *inert* |
| `outcome_check.py` | reads the registered priors' rows back from the instruments and scans the prose for numbers no quantity computes |
| `verify_s5.py` | recomputes every number in Section 5 from the instrument that owns it, and plants a claim's carriers |
| `cite_check.py` | resolves every in-text citation key — `[@key]` in the working tree's parts, the bibliography's `[n]` in the shipped product, through the product's own numbered list — counts citations, and fails on a citation-shaped token no well-formed bracket consumes |
| `refs/reference_check.py` | the citation authenticity report: `--query` asks Crossref/arXiv about every entry, the default mode re-reads the committed answers offline and refuses a report that drifted from them |
| `reference-check.md` + `.json` | the report (one block per entry, in citation order) and the raw answers it is rendered from |
| `figures/make_figures.py` | draws Figure 1 from the instruments; `--check` refuses a PNG that is not what this run draws |
| `check_links.py` | every link and image in `manuscript.md` resolves at the product's own base |
| `submission_check.py` | the journal's submission bar (13 items + the presentation bar + the in-text key form), read rather than asserted — it reports `CHECKS` vs `DECLARED` and fails the rest |
| `refs/` | the reference pipeline: selection, three check stages (24 / 15+22 / 8+19), the built records and the harvest log |
| `refs/refs_reread.py` + `refs/refs_reread.json` | the by-id re-read limb: a work published after the registration (in no harvest pool, not an anchor) and an id whose pool title no longer matches the live record; it overrides the pools on the record's fields and keeps the finder's provenance label |
| `refs/refgate_output.txt` | the journal's own reference gate (`refgate.py`) run from the repository root over `manuscript.md`, kept verbatim; `reference-check.md` quotes it and re-reads its count, coverage and verdict |
| `outcomes.md`, `registration_priors.md`, `heilmeier.md` | the registered priors, the per-prior outcome rows, and the direction's Heilmeier answers |
| `reproduce.sh` | the command above |

## What the run's checks have caught

The checkers are not decoration, and the paper says so in Section 6.4. Writing Section 5 produced three defects that
only recomputation found (a table wrong by a factor of two *and* with the wrong sign; an asserted identity off by
0.81; a cell count attributed to the wrong side of a threshold). Two of the checkers' own readings were repaired
after they were shown to be wrong: `verify_s5.py` accepted `0` as evidence for every quantity below 0.5 (a
one-token page satisfied 22 of 51 claims), and `cite_check.py` could not see a citation whose bracket was
malformed (`[(@a;@b;@c)]`) — then fired on the paragraph that documents it, which is why inline code is now read as
quotation and the quoted tokens are counted (`QUOTED ... : 4`) rather than dropped. The authenticity report joined
the wrong field on its first run and verified **0 of 120 while printing a clean summary line**; two of its nine
plants were misaimed rather than the check being wrong, and its own verdict was being read from a summary counter
instead of the rows.

**The citation form itself was the third repair, and no check in this package could see it.** The manuscript was
submitted at `d77e974` with the body citing `[@key]` and the bibliography numbered `[1]`–`[120]`; the journal's own
gate read `covered=1/120 coverage=0.8% GATE: FAIL`, while `cite_check.py` and bar item 13 both read
`120 cited, 0 uncited` — because every limb here read the *parts* (which cite by key) and none read the product's
own in-text keys. That is the Class 119 shape: the check's object was not the object the rule names. The repair is
in three places, all of them reading the product's own numbered list: `research/assemble.py` renders `[@key]` into
`[n]`, `cite_check.py` resolves a numeric key through the bibliography the product carries (an entry is keyed by its
link, and an entry whose link names no record is returned as unresolved rather than skipped), and bar item
`B13b-in-text-key-form` fails the package if those two ever disagree again.

**Three counts the manuscript stated and no step owned, and one title that had gone stale — all found by running
checks this package already had.** R481 added a bar item and two authenticity checks with two battery cases, and
updated this README; the manuscript's own rendering went on stating `17 item(s)`, `12 checks` and a `9-case
battery`, and every step stayed green, because each step read the RUN and none read the manuscript's copy of the
number. The three are repaired in the product and `reproduce.sh` now compares each of them against the run.
Separately, the clause `refs_build_v93.py` writes `pool_title` for — "the title the difference line was written
against, so a later read can check the live record still bears it" — was run this round and fired: one arXiv entry
cited the harvest's reading of **v1** while the identifier now serves a **retitled v3**, so the bibliography was
citing a title its own link no longer shows. The repair is a re-read recorded in `refs/reread.json` — with the
fetched title, the version it came from and the pool title it replaces — and the entry now prints what the record
prints. The same round added one reference: a work published nine days after this study's registration and the day
before its submission, which is in no harvest pool and is not one of the registration's anchors, and therefore
enters through a limb of its own (`refs/refs_reread.py`).

## What the bar items are

`submission_check.py` answers the journal's submission quality bar item by item, and `reproduce.sh` runs it last so
a green run means the bar was read on the package as shipped. Two verdicts are kept apart on purpose: **CHECKS**
(the item is decided by a reading of the objects) and **DECLARED** (a statement only the author can make — item 10's
positioning of the contribution, and item 1's naming of the level's evidence — quoted rather than pretended to be
verified).

## References

The citation-volume bar is 100; this manuscript carries 121 records and cites all of them in the body
(`uncited records 0 of 121`), numbered `[1]`–`[121]` in first-citation order. **The body cites the key the
bibliography prints**: each in-text key is the entry's `[n]`, so coverage is a property of the text (item 11,
*Citation mechanics* — a work cited by name or by bare arXiv id does not discharge coverage). The parts, from which
the product is assembled, cite `[@key]` instead; `research/assemble.py` renders them into `[n]` at the one place the
numbering is derived.

The journal's own gate reads the product from the repository root:

```bash
python3 .github/tools/refgate.py papers/issue-93/manuscript.md   # entries=121, covered=121/121, coverage=100.0%
```

Its output is committed at `refs/refgate_output.txt` and quoted in `reference-check.md`, whose check
`C13-the-quoted-journal-gate-re-read` re-reads the count, the coverage and the verdict line against this report's
own 121 rows rather than trusting the quote. The gate's one `AMBIGUOUS` line (`[0]`, from the model's interval
`[0, 1]` in §1.3 and §5.3) is answered in that report's *In-text keys, coverage and ambiguity* section, and
`C14-every-bracket-the-gate-flags-is-explained` requires the answer to name the bracket the gate named.

`reference-check.md` is the authenticity report — one block per entry: the manuscript's title, the method, the
record found, and the title agreement — and it reads **121 of 121 verified, 0 mismatch, 0 unverified** (46 queries
to Crossref, 75 to the arXiv API, batched). Regenerate its network half with:

```bash
python3 refs/reference_check.py --query     # writes reference-check.json + reference-check.md
python3 refs/reference_check.py --selftest  # 14 checks + an 11-case battery, offline
```

`refs/` is the pipeline the bibliography is derived from (`refs_check*.py`: 24 checks, 15+22 mutations, 8+19
cases).
