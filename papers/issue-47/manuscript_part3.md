
## 5. The limits, each with the measurement that establishes it

A limit is stated here as a measurement rather than an apology. Each was found by running the
instrument, and each was declared before this manuscript was written.

**L1 — the paging attachment is model-dependent.** Two attachments are possible, and they are not the
same experiment (Section 3.3). The step-common attachment is blind to positive errors and reproduces
the zero-error cost exactly, while the per-page attachment differs on the same information. Both
relations are measured, and the third is the trap: a positive *bias* is not a non-negative
*multiplier*. **Consequence:** every statement this paper makes about positive-bias predictions in
paging is a statement about the per-page attachment. **Why it does not sink the paper:** the
attachment is declared, the alternative is measured against it, and the paging result is reported as
unresolved anyway — so no claim in this paper rests on the attachment being canonical.

**L2 — the null of the object-level design is shifted, so negative verdicts are uninterpretable.**
Under a synthetic even target with no sign dependence, the odd parameter is penalised by
`{{X:facts.limit.L2_null_shift.ski.value|2f}}` / `{{X:facts.limit.L2_null_shift.sched.value|2f}}` /
`{{X:facts.limit.L2_null_shift.paging.value|2f}}` cluster MDEs (ski / sched / paging). A design that
punishes its own odd term under a sign-free target cannot read a negative as evidence. **Consequence:
only the positive resolutions are reported as evidence, and the unmatched-form reading is retired.
Why it does not sink the paper:** the surviving verdicts are the conservative ones — a positive result
obtained against a null that is shifted *against* it is a lower bound on the effect, and the paper
says so in the result itself rather than in a footnote.

**L3 — unit reach is uneven, and the external cell says where.** Against the published robustness
scale (a 0.8–8.8% worst-trace degradation), the harness reaches that scale in ski rental
(`{{X:facts.limit.L3_reach_at_or_above_0.8pct.ski.value}}` of
`{{X:facts.limit.L3_reach_profiles.ski.value}}` profiles at or above 0.8%,
`{{X:facts.limit.L3_reach_at_or_above_8.8pct.ski.value}}` at or above 8.8%) and in **neither** paging
nor scheduling (`{{X:facts.limit.L3_reach_at_or_above_0.8pct.paging.value}}` and
`{{X:facts.limit.L3_reach_at_or_above_0.8pct.sched.value}}` of 13; the harness's worst unit is better
than the non-learned baseline at every profile there, minima
`{{X:facts.limit.L3_reach_min_worst_unit_degradation.paging.value|4f}}` and
`{{X:facts.limit.L3_reach_min_worst_unit_degradation.sched.value|4f}}`). **Consequence:** the cell
supports a claim about ordering in all three problems and about magnitude in one. **Why it does not
sink the paper:** the reach row is reported as a measurement rather than gated, so a reader knows
exactly which of the two claims each problem carries; and the asymmetry itself is informative — it
locates the interface between an error generator and predictor-like errors.

**L4 — concordance is rank agreement, not a magnitude match.** No unit conversion between the
harness's ratios and the published cache's miss ratios is attempted or claimed. **Consequence:** the
external cell is a sign-level anchor. **Why it does not sink the paper:** the claim made from it is
the one the measurement supports — the *ordering* — and the derived comparison figure (`1.26/1.08-1`)
is written into the artefact as a derivation rather than presented as a transcription.

**L5 — the generalising unit is the profile, not the repeated measurement.** Measured: an MDE computed
over paired units that share the error generator, implementation and fit was optimistic by 3.7–6.3×.
**Consequence:** every resolution verdict quotes the cluster unit `(profile, replicate)`, and the
tightest resolution quoted anywhere in this paper is `{{X:facts.claim1.worst_block_mde.value|4f}}`.
**Why it does not sink the paper:** the correction moves the verdicts in the conservative direction
and is itself one of the paper's method contributions (Section 1.3, C5) — the instrument was corrected
by its own controls.

**L6 — a synthetic harness with one real anchor.** All losses come from this paper's generators; the
external cell anchors ordering against a published system and is not a reproduction of it.
**Consequence:** the paper's claims are about the relationship between prediction-error structure and
realized loss *in this harness*, with the published anchor carrying the sign of that relationship into
the literature. **Why it does not sink the paper:** the counterfactual is exact by construction — the
offline optimum is computable for every instance — which is precisely what a measured-live-system
study cannot have; the harness buys ground truth at the price of realism, and the price is stated.

**One further item, owed rather than measured.** The registration's fourth success criterion names a
flip-count bound per headline number, and no stage of this package computes it (Section 4.6). It is
listed here as owed: this paper does not claim a sensitivity margin it has not measured.

## 6. Methodology, and how to reproduce it

### 6.1 The methodological stance, and what this paper takes from the evaluation literature

The instrument is built on four methodological commitments, each borrowed from a literature that
already argues for it, and each applied here to a simulation rather than to a deployed system.

* **A simulation is designed, not repeated arbitrarily.** The profile grid is declared before any run
  and used unchanged by every result, so a cell's meaning is fixed by construction [@soutosimulation]
  — versus growing the number of replicates until a verdict appears — and where replication is carried
  out at scale it needs a framework of its own rather than more repetitions [@gardnermorf].
* **A resolution is quoted, not assumed.** Every verdict is stated in cluster-unit minimum detectable
  effects [@bulusmde] [@burstynmde] [@hunterpump], so "the design can see this" is a number rather
  than a hope.
* **Reproducibility is a reading, not an intention.** The apparatus is checked rather than promised:
  one command, byte-identical output, and a published digest block [@fehrbestpractices]
  [@flittnerartefact] [@thorpereprorubric]; and what an independent re-run can and cannot establish is
  part of the claim [@zilberman] [@brookssmoke].
* **A replication's result is not self-authenticating.** The literature on replications is a warning
  that a repeated measurement can misread its own remit [@shepperd] [@santoscomparing]
  [@penzenstadler] [@liureproducibility], and the same field argues that reproducibility and
  benchmarking practice need explicit machinery rather than good intentions [@fundcurriculum]
  [@gengptopno], which is why every stage of this package recomputes its numbers from the primitives
  and a liveness control requires each recomputation to be able to fail (below).

**Specific difference.** That literature studies replications of *published* systems and analyses,
usually in software engineering; this paper applies the same disciplines to a measurement instrument
it builds itself, on a theory problem, and it publishes the two things that literature asks for and
rarely gets — a resolution unit and a liveness control — as committed machinery rather than as
guidance.

### 6.2 The package: one command, and what it recomputes

`bash reproduce.sh` runs the whole package on one CPU core with the Python standard library and **no
network**, and exits non-zero unless every step passes. It has seven steps: (1) `{{S:n_stages}}`
stages plus the canonical aggregate, which **recomputes** every cited number from the stage artefacts'
primitives and cross-checks it against the value each stage recorded about itself
(`{{S:n_facts}}` facts, 0 disagreements when this was written); (2) the aggregate's liveness control,
which corrupts each recomputation in a throwaway copy and requires it to notice; (3) the external
cell's own check-liveness, 13 mutations, one per named check, each of which must make exactly that
check fail; (4) the design-freeze document checked against the artefacts, 46 checks including the
digest table; (5) the manuscript assembly, which resolves every measurement placeholder out of the
artefacts and fails on an unresolvable one or a citation key with no reference entry; (6) the
**support limb** of citation integrity (Section 6.3); and (7) the digest block.

Two further properties are reported rather than assumed. The **coordinate census** scans the package
for hidden inputs the authoring machine supplies silently: it reports
`{{X:coordinate_census.violations}}` violations over the classes it declares, with 8 of 8 detectors
firing on a planted instance — and it reports the classes where the package *does* read the outside
world (its own directory, the manuscript parts one level above the package, and the interpreter),
because a census that printed only its zeroes would be a census of one direction. The **run
environment** is recorded with the run: the package is deterministic (no clock, no entropy, no
socket), and two full runs to byte-identical logs are the check.

### 6.3 The two relations of a citation, and the one this paper had to build

A citation owes two relations, and they are read in different places. **Identity** — the record is the
work the entry names — is read in the list, by comparing the returned year, venue and authors against
the entry's own line; every entry's record was resolved against Crossref or arXiv and the report is
`reference-check.md`. **Support** — that work is the work the claim at the key needs — is read in the
text, and no step of this pipeline read it until this paper built one.

The support limb is read per **occurrence**, not per key: the `{{S:n_facts}}`-fact aggregate is not a
citation, and the manuscript's {{X:facts.claim1.blocks_total.value}} blocks are not references either,
but of the cited keys 51 appear in more than one sentence, and a per-key read would hide the
occurrence that fails. Each occurrence is recorded against the sentence it sits in, with the role the
key plays there (a bound source, a survey, an instance of the enumerated class, the published anchor,
…), and the check fails on a missing read, on an edit that leaves a recorded sentence no longer in the
text, and on an occurrence marked unsupported. The read found four occurrences in this manuscript's
own draft where the work could not carry its sentence — a source for the exactness of an offline
optimum that was three competitive analyses; a structural-equation sample-size app cited for
cluster-level resolution; five asymmetric-loss papers cited for a claim about guarantees; and a
theory bound listed among systems measurements. All four were corrected, and all four are kept on the
record in `support-read.md`: a corrected finding that leaves no trace is indistinguishable from one
that was never made.

**Specific difference.** The citation-integrity literature and the journal's own bar both read the
list; the relation that a *sentence* depends on is usually left to the author's judgement with no
record of what was judged. This paper makes the second relation a mechanism: the quote is what binds
a verdict to a sentence, so an edit anywhere in the text either moves nothing (if it is not a cited
sentence) or is reported as the pair it is.

### 6.4 Threats to validity, and why this is still worth publishing

Four things could make the paper wrong, and each is bounded rather than waved away.

1. **The harness is synthetic (L6).** Its realism is anchored at one point — the sign of a published
   system's ordering — and the anchor's own reach is measured and reported as uneven (L3). The
   counterfactual is exact by construction, which no live measurement of this quantity has. A reader
   who wants live numbers gets none here; a reader who wants the *structure* of the loss gets a
   ground-truth instrument, and the two are complements rather than substitutes.
2. **The object-level design is weak by construction (L2, L5).** Its null is shifted against the
   hypothesis, and the resolution unit was corrected upward by 3.7–6.3×. Both move the paper's
   verdicts in the conservative direction: the reported resolutions are what survived a design that
   is biased *against* reporting them. That is also why the headline does not rest on the object-level
   test — it rests on a constructive identity (Section 4.1), which no test resolution can overturn.
3. **The scope is three problems and one profile family.** The profile grid moves mean, spread and
   tail independently, but the real predictor-error structures of deployed systems are not enumerated
   here. The claims are stated per problem throughout and never pooled, so a reader can see which of
   them rests on one problem's cell and which on three.
4. **One anchor, one derived comparison figure (L4).** The external cell reproduces the *ordering* of
   one published pair. The concordance could be a property of the harness rather than of caching; the
   paper's response is to make the reach row a measurement and to report the rank agreement without a
   magnitude claim.

Against these: the paper's first claim is not a statistical result but an identity — two arms with the
same multiset of `|error|` whose realized losses differ by up to
`{{X:facts.claim1.worst_loss_gap.value|3f}}` competitive-ratio units — and its fourth claim prices the
field's standard calibration rule in the currency a deployer uses, with a between-stream interval and
an out-of-sample check on the parameter it accuses. Both survive the limits above, and neither was
available before this instrument.

## 7. The registered priors, and what happened to each

The registration stated three prior beliefs, with directions and justifications, before any deciding
run. Each is reported here with its outcome, and the criteria the registration fixed are reported in
Section 4.5.

**P1 — the realized loss is signed-asymmetric, so `|error|` is not a sufficient statistic.
Outcome: confirmed, and more strongly than predicted.** The registration's falsification condition was
that the scalar regression match the decomposition on held-out cells. It does not: the constructive
witness (§4.1) is an identity, not a comparison — identical scalar features by construction, losses
that differ by up to `{{X:facts.claim1.worst_loss_gap.value|3f}}` competitive-ratio units against a
cluster MDE of `{{X:facts.claim1.worst_block_mde.value|4f}}`. The registered *predictive* clause — that
the decomposition explains held-out loss better — resolved in one of three problems at the clean
object-level design (§4.2), which is weaker than the witness and is reported as such.

**P2 — the worst-case calibration costs a measurable factor, and the loss tracks the spread's tail
rather than its mean. Outcome: the first half confirmed, the second half only partially.**
The factor is measured: a median of `{{X:facts.claim4.lambda_loss_median.ski.value|3f}}` /
`{{X:facts.claim4.lambda_loss_median.sched.value|3f}}` /
`{{X:facts.claim4.lambda_loss_median.paging.value|3f}}` (ski / sched / paging), with the worst
profile's factor at `{{X:facts.claim4.lambda_loss_max.ski.value|3f}}` /
`{{X:facts.claim4.lambda_loss_max.sched.value|3f}}` / `{{X:facts.claim4.lambda_loss_max.paging.value|3f}}`
and a 95% between-stream interval that stays away from 1. The direction the prior predicted — the
tail, not the mean — is present in all three problems (the two tail profiles carry the higher mean
factor, `{{X:facts.claim4.lambda_mean_loss_tail.ski.value|2f}}` /
`{{X:facts.claim4.lambda_mean_loss_tail.sched.value|2f}}` /
`{{X:facts.claim4.lambda_mean_loss_tail.paging.value|2f}}` against
`{{X:facts.claim4.lambda_mean_loss_other.ski.value|2f}}` /
`{{X:facts.claim4.lambda_mean_loss_other.sched.value|2f}}` /
`{{X:facts.claim4.lambda_mean_loss_other.paging.value|2f}}`), and the *magnitude* the prior implied is
not: the correlations are `{{X:facts.claim4.lambda_corr_tail.ski.value|3f}}`,
`{{X:facts.claim4.lambda_corr_tail.sched.value|3f}}` and
`{{X:facts.claim4.lambda_corr_tail.paging.value|3f}}`, and the relation is non-monotone in spread —
in ski rental the extreme-spread profiles carry the *lowest* factor. Reported as **partially
confirmed**: the direction stands, the mechanism sentence does not.

**P3 — which sign is priced is problem-structured. Outcome: refuted, and the refutation is
informative.** The registration predicted that paging prices over-prediction and ski rental
under-prediction, stable across algorithms within a problem. Measured: **under-prediction is the worse
arm in all three problems** — the dominant sign is a property of the harness's cost structure, not of
the problem's decision direction. The prior was anchored on a mechanism (act early versus defer) that
would make the sign follow the problem; the measurement says the sign follows something the mechanism
did not name. That is a genuine contradiction of a theory-anchored prior, and it is reported as the
paper's most surprising single result rather than buried: it means a statement of the form "this
problem prices that sign" cannot be inferred from the shape of the decision alone.

**On reporting a refutation.** A prior whose falsification condition was met is the strongest
available evidence that the instrument can fail — the paper is not only confirming its own beliefs.
The refuted prior (P3) and the partially confirmed one (P2) are the two places where this work changed
what its author believed going in, and both are stated in the abstract.

## 8. Conclusion

The question this paper set out to answer was what a prediction buys — not what it guarantees in the
worst case, but what the loss actually is as a function of *which way* the prediction is wrong. The
answer has four parts, and the first is an identity rather than a statistic: two arms with the same
scalar error statistics, differing only in sign, realize losses that differ by up to
`{{X:facts.claim1.worst_loss_gap.value|3f}}` competitive-ratio units — above the resolution of their
own block in `{{X:facts.claim1.blocks_exceeding_own_mde.value}}` of
`{{X:facts.claim1.blocks_total.value}}` blocks. `|error|` is therefore not the object the field's
guarantees should be stated over; a decomposition into signed components is.

The second part is where the instrument can resolve and what happens there: the sign channel carries
information beyond the scalar when the design is matched in form, in
`{{X:criteria.a_signed_beats_scalar_on_held_out_cells.state}}` form for scheduling and as an
object-level contrast for ski rental, with paging reported unresolved rather than as a small effect.
The third is a published system ordering reproduced in sign, with the cell's own reach reported as a
limit instead of hidden as a success. The fourth prices the field's standard worst-case calibration:
a factor of `{{X:facts.claim4.lambda_loss_median.ski.value|2f}}`–`{{X:facts.claim4.lambda_loss_median.sched.value|2f}}`
per problem in the typical case, with the parameter the rule chooses differing from the profile's own
best on most profiles and the factor surviving an out-of-sample refit.

What a reader should take away is not a number but a change of object. A consistency bound written in
`eta` or `|error|` is a statement about the magnitude of an error; the measurement here says the loss
is governed by its direction, and that the direction is not the direction the literature's mechanism
arguments predict. A deployer's next unit of effort — spend it on the predictor or on the fallback —
is a question about a signed quantity, and this paper supplies the instrument that prices it, together
with the limits under which that price holds.

## References

<!-- REFERENCES -->
