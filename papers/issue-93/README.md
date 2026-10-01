# Issue #93 — When Does a Human Approval Gate Pay?

**Binding fidelity sets the net value of human-in-the-loop control for tool-using agents.**

This directory is the submission package: `manuscript.md` is the paper, and everything beside it is the apparatus
that produced and checks the paper's numbers. Contribution level: **theory + empirics** (a closed-form model with
ground truth by construction, plus instruments that enumerate it).

## One command

```bash
bash reproduce.sh
```

Expected output (the transcript of a run on the declared build, 2026-09-22):

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
authenticity   REFERENCE CHECK: PASS -- 12 check(s), 0 failed | BATTERY: 9 of 9 case(s) fired
citations      the product manuscript.md | citations 210 | distinct keys 120 of 120 built records
counts         the manuscript states the run's citation count (210 citations)
counts         the manuscript states the run's §5 claim count (52 claim)
counts         the manuscript states the built-record count (120 distinct keys of 120)
counts         the manuscript states the authenticity count (120 of 120 verified)
figures        CURRENT -- fig1_sign_law_and_cost_ratio.png is byte-identical to a fresh draw (sha256 87b55876492a8e93)
links          LINK CHECK: PASS -- 1 link(s), 1 local, 0 broken | BATTERY: 4 of 4 case(s) fired
bar            SUBMISSION CHECK: PASS -- 17 item(s), 0 failed, 2 declared | BATTERY: 8 of 8 case(s) fired
product        manuscript.md 129968 bytes, sha256 c8dc3b99a8cfe2c5

REPRODUCE: ALL GREEN
```

`REPRODUCE: ALL GREEN` and exit 0 mean every step's own reading passed. Every step runs a checker that exits
**non-zero when its own reading fails**, so a green line is never produced by a step that could not run: an
unreadable input, a missing artefact or a raised guard stops the step with `FAILED`.

## Tolerance, and the build

* **Tolerance: byte-identity.** The seven instrument reports (`gate_v*_results.json`) are deterministic — the model
  is enumerated, not sampled for the quantities the paper reports — and the run *measures* this by hashing them,
  running the instruments a second time and comparing. Any change is a failure.
* **The crc32 `report id` is a digest of a report, not a measurement.** A different interpreter or NumPy may move
  it, which is why the digests are printed for comparison instead of being asserted. The numbers the paper's
  claims rest on are compared exactly.
* **Build.** Read on Python 3.9.6 with NumPy 2.0.2 (macOS). `gate_v0`, `gate_v1`, `gate_v2`, `gate_v3` and
  `gate_v5` import NumPy (the Monte-Carlo route and the interval); the rest are pure Python. Override the
  interpreter with `PYTHON=/path/to/python3 bash reproduce.sh`. Full digests (sha256) of the reports on this
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
| `cite_check.py` | resolves every in-text citation key, counts citations, and fails on a citation-shaped token no well-formed bracket consumes |
| `refs/reference_check.py` | the citation authenticity report: `--query` asks Crossref/arXiv about every entry, the default mode re-reads the committed answers offline and refuses a report that drifted from them |
| `reference-check.md` + `.json` | the report (one block per entry, in citation order) and the raw answers it is rendered from |
| `figures/make_figures.py` | draws Figure 1 from the instruments; `--check` refuses a PNG that is not what this run draws |
| `check_links.py` | every link and image in `manuscript.md` resolves at the product's own base |
| `submission_check.py` | the journal's submission bar (13 items + the presentation bar), read rather than asserted — it reports `CHECKS` vs `DECLARED` and fails the rest |
| `refs/` | the reference pipeline: selection, three check stages (24 / 15+22 / 8+19), the built records and the harvest log |
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

## What the bar items are

`submission_check.py` answers the journal's submission quality bar item by item, and `reproduce.sh` runs it last so
a green run means the bar was read on the package as shipped. Two verdicts are kept apart on purpose: **CHECKS**
(the item is decided by a reading of the objects) and **DECLARED** (a statement only the author can make — item 10's
positioning of the contribution, and item 1's naming of the level's evidence — quoted rather than pretended to be
verified).

## References

The citation-volume bar is 100; this manuscript carries 120 records and cites all of them in the body
(`uncited records 0 of 120`), numbered `[1]`–`[120]` in first-citation order. `reference-check.md` is the
authenticity report — one block per entry: the manuscript's title, the method, the record found, and the title
agreement — and it reads **120 of 120 verified, 0 mismatch, 0 unverified** (46 queries to Crossref, 74 to the arXiv
API, batched). Regenerate its network half with:

```bash
python3 refs/reference_check.py --query     # writes reference-check.json + reference-check.md
python3 refs/reference_check.py --selftest  # 12 checks + a 9-case battery, offline
```

`refs/` is the pipeline the bibliography is derived from (`refs_check*.py`: 24 checks, 15+22 mutations, 8+19
cases).
