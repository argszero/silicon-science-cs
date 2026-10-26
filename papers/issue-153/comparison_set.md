# Comparison set — issue #153

The paper's claim is that a local rule over visible state cannot be exact on this model, and
that the minimal exact horizon is `w* = T − 1 − i_first`, i.e. it grows with the trace, while
a lookahead of 1 is worse than none. That is a statement in the vocabulary of *online
algorithms with lookahead*, not of LSM engineering. This file records, for each neighbouring
work actually read, **what it bounds, what it assumes about the adversary, what it does not
model, and the specific difference** — the paper's defence against "this is already known".

Read on 2026-10-26. A work whose abstract could not be obtained is **not** listed with a
difference; a title-level difference is not evidence and will not appear in the manuscript.

## 1. On Competitive On-Line Paging with Lookahead (BRICS report, 1995; journal version 1997, DOI 10.1016/s0304-3975(98)00118-2)

*Read via:* the 1995 BRICS record (DOI 10.7146/brics.v2i50.19951) — same line of work, full
abstract available. The 1997 journal version exposes no abstract in Crossref and Semantic
Scholar returned HTTP 429 (not retried).

- **What it bounds:** two ways of strengthening an online paging algorithm — extra pages `k`,
  or lookahead `l` — under a new measure of lookahead size and under Young's resource-bounded
  lookahead. Result: competitive efficiency depends on `k + l`, so *one extra page and one
  extra bit of the future are worth the same*.
- **Adversary:** the standard competitive-analysis adversary, unconstrained and unrestricted
  in the request sequence, with the comparison made against the offline optimum.
- **What it does not model:** a cost paid *at the moment of a decision* for the decision
  itself. Paging charges on the miss; compaction charges when two runs are merged, and the
  bytes it pays depend on how much live data the merged runs cover.
- **Specific difference:** this work makes foresight **tradeable against capacity** — the
  quantity that matters is `k + l`. In this paper's model foresight is not tradeable against
  anything: the exact horizon is `w* = T − 1 − i_first` and grows with the trace, so no
  constant `l` is exact for any `k`, and increasing `l` by one can make the rule *worse*
  (measured: w=1 loses 324 traces against w=0's 228 at R=3 K=3 T=7). "One more bit of the
  future is worth one more page" fails here not in its constant but in its form.

## 2. Semi-Online Scheduling on Two Identical Parallel Machines with Initial-Lookahead Information (2023, DOI 10.1142/s0217595923500033)

- **What it bounds:** makespan-optimality of deterministic online algorithms that know the
  first `k` jobs in advance. It proves the classical LIST algorithm optimal in one regime,
  shows that in another regime **any** online algorithm has ratio ≥ 3/2 — so initial
  lookahead is *powerless* there — and gives LPT-LIST for a third.
- **Adversary:** over-list arrival, remaining jobs released one by one; deterministic
  algorithms; comparison against the offline optimum.
- **What it does not model:** a lookahead whose value is a *suffix* of the same stream. Their
  knowledge is a **prefix fixed at the start**; nothing later is ever revealed.
- **Specific difference:** this is the nearest work in spirit and the one a reviewer will
  raise, because it too reports that lookahead can be worthless. The difference is the
  object quantified: they give a **competitive ratio per regime** for a prefix of known
  jobs; this paper gives the **exact horizon at which optimality becomes possible**, and
  shows that horizon is the entire remainder after the first genuine choice. "Lookahead is
  powerless" and "lookahead must be total" are different statements: the first is about
  ratio, the second about existence of any exact rule.

## 3. Semi-online scheduling on two uniform parallel machines with initial lookahead (2024, DOI 10.1051/ro/2024042)

- **What it bounds:** a lower bound `(s²+s+1)/(s²+s)` and a deterministic semi-online
  algorithm with ratio `(s+1)²/(s²+s+1)`, at most 9/7, against 1.618 without initial
  lookahead, for machines of speeds `1` and `s`.
- **Adversary:** over-list arrival after the first `k` jobs; the case analysed assumes the
  first `k` jobs have total length at least `(s+1)Δ`.
- **What it does not model:** local decisions with a merge cost; there is no capacity
  structure whose state a rule can read.
- **Specific difference:** the result is that **finite** initial lookahead "can greatly
  improve" competitiveness. This paper's result is the opposite shape for a different
  decision: finite lookahead of any fixed size never reaches optimality, and a finite
  increase can hurt. Both are about the value of foresight; they disagree on whether the
  value is monotone.

## 4. Disk scheduling policies with lookahead (2002, DOI 10.1145/588160.588165)

- **What it bounds:** nothing in the optimality sense — it re-evaluates known disk-scheduling
  policies and proposes windowed extensions (CSCAN with rotational latency, SATF over several
  successive requests, conditional write prioritisation), then evaluates them.
- **Adversary:** none; the evaluation is over workloads, not over an adversary.
- **What it does not model:** an exact optimum, and therefore any gap to it.
- **Specific difference:** this is the systems-side use of a lookahead window — a heuristic
  with a tunable window, scored empirically. This paper says what the window would have to be
  for exactness in a compaction model, and that the answer is the whole remaining trace. The
  two meet only in vocabulary; citing it as prior characterisation would be a category error.

## 5. An optimal on-line algorithm for metrical task systems (1992, DOI 10.1145/146585.146588)

- **What it bounds:** a general model for processing a sequence of tasks, and an online
  decision algorithm optimal for an important class of special cases.
- **Adversary:** the standard task-sequence adversary; the framework scores a rule against
  the offline optimum.
- **What it does not model:** the compaction structure — `K` slots, `R` ranges, run sizes
  frozen at creation, and a merge cost equal to the bytes covered.
- **Specific difference:** this supplies the framework this paper works inside, and it is
  cited for that. It does not answer how much of the sequence a decision rule must see, which
  is the question here.

## What the manuscript may and may not claim

- **May:** the horizon result is new in this model, and differs from the nearest lookahead
  results in form (not merely in constant) — foresight is not tradeable against capacity
  here, and partial lookahead is non-monotone.
- **May not:** that lookahead in online algorithms has not been studied (it has, extensively);
  that no one has shown lookahead can be worthless (semi-online scheduling shows exactly
  that); or that a title-level resemblance to any entry in the pool constitutes prior work.
- **Not read, therefore not cited as comparison:** *How much can lookahead help in online
  single machine scheduling* (2008, DOI 10.1016/j.ipl.2007.10.008) — no abstract reachable
  from Crossref and Semantic Scholar was rate-limited (HTTP 429, not retried). It stays in the
  pool as a placeable §7 entry; it may not carry a stated difference until it is read.
