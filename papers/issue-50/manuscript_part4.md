## 5. Limitations

The study's claims are claims about a model, and five properties of that model bound them. Each is
stated with what would remove it, because a limitation with no route out is a disclaimer rather than a
limitation.

**5.1 It is a simulation, and it makes no wall-clock claim about any real system.** The instrument
reproduces its classical limits (3.3) and its draw discipline makes its comparisons exact, but a
`rho*(A, h)` measured here is a boundary of *this* queueing model under *these* assumptions: identical
workers, exponential thinking, one call per step, a measured contention. Nothing in this paper licenses
the sentence "speculation stops paying at 97% utilisation in production". What would remove the
limitation is not a bigger grid but a different experiment: instrumenting a deployed agent loop, reading
its actual tool-wait share and its actual pool contention, and asking whether the boundary appears where
the model puts it. That experiment is stated as the first item of future work (9.2) rather than
attempted here, because the model's job in this paper is to *locate* the boundary, not to certify one
deployment.

**5.2 Prediction enters as a scalar hit rate.** `h` is the probability that a step's early call is the
call it needs. No predictor is trained, no probe accuracy distribution is modelled, and the instrument
therefore cannot say anything about how a particular predictor's errors are correlated across steps --
and correlated errors would shift the boundary, since their whole effect is on worker occupancy. The
external cell varies `h` between the accuracy a published probe reports and an oracle (4.8), which is
the closest the paper comes to this question.

**5.3 The side-effect channel is a charge, not a semantics.** A discarded non-idempotent call pays
`comp` units of worker time. That models the *cost landing* on the shared pool; it does not model what a
non-idempotent effect does to the world (duplicate writes, partial application, compensation logic). The
paper's side-effect result is therefore about where the cost lands and who waits for it -- which is
enough to falsify the belief that an idempotency precondition bounds harm, and not enough to say
anything about correctness.

**5.4 One registered statistic was not measured, and one comparison could not be made.** The sharpness
statistic is unmet (4.2) because the committed windows bracket the zero crossing rather than the
`+/-5%` band; the fix is a sweep designed for the band, which is a different grid rather than more
seeds. The closed-form comparison is unmet (4.7) because the closed-form model has no boundary in the
same window; the fix is a closed form whose benefit changes sign, or a window extended to where it does.
Both are reported as unmet with their reasons rather than replaced by nearby quantities, which is the
honest reading and also the weaker paper -- a reader comparing this study's registration to its results
should see both.

**5.5 The pools are homogeneous and the rates are fixed.** Workers are identical, so the boundary is
indexed by a pool size and not by a *composition*; a fleet with per-tier service rates would have a
different boundary per tier and is out of scope. The speculation rate is a constant of the run rather
than the output of a controller, so the paper describes a region and not a policy -- the controller that
would use it is future work (9.2).

**5.6 The external cell is three published cells, read at abstract level.** The three systems were
chosen because they state a number in a stated operating region; the sign test is therefore a test of
three cells and not of the literature. Where a paper reports no tool-wait share the model *inverts* its
own ceiling to ask which shares could produce the reported reduction (4.8) -- a comparison the paper's
authors never made and one that a differently parameterised instrument could resolve differently.

## 6. Reproduction

**6.1 One command, and what it must produce.** The package is reproduced by a single command from the
package directory:

```
bash reproduce.sh
```

It must rebuild every artefact the paper's numbers come from, re-render the manuscript from those
artefacts, and re-run the journal-side checks. The declared expectation is the strongest one available
for a deterministic instrument: **byte-identical output**, not "close enough". The command reports, and
the manuscript is only reproducible if, the following all hold:

| step | object it reads | expected result |
|---|---|---|
| instrument sweeps | `artefacts/*.py` | each sweep is re-run from the command its own artefact records (`rebuild_artefacts_v1.py`), and every artefact comes back byte-identical |
| assembly | the rebuilt artefacts | `assemble.py --check` exits 0: the committed manuscript is the one the evidence produces |
| bibliography | `references.json`, `refs_order.json` | the two writers' `--check`s exit 0 and the order matches the body's first-use numbering |
| reference verification | `refs_verification` artefact | `reference-check.md` re-renders, differing from the committed copy in nothing but its own run coordinates |
| citation gate | `manuscript.md` | `refgate.py` reports `GATE: PASS` |
| link gate | every tracked markdown carrier | `linkgate.py --check` reports `broken=0` |
| figures | `artefacts/*.json` | `figures/make_figures_v1.py --check` reports the four figures regenerated byte-identically |
| the paper's own claims | the parts, the artefacts, the figures | `manuscript_check_v1.py` reports no unbound claim: each registered verdict is the one its artefact decided, every section reference resolves, every figure is reachable and pointed at, and no headline measurement is typed into the prose |

**6.2 The evidence is in the package, and the package is closed.** {{n_evidence_files}} files
({{evidence_mb}} MB) sit under `artefacts/`, including {{n_instrument_scripts}} scripts. The scripts
import {{n_import_modules}} distinct modules in total, of which **{{n_imports_outside}} are outside the
standard library and outside the package itself**: the instrument is stdlib-only, and each script that
imports a sibling imports a file the package ships. That property is not a claim about good intentions;
it was read from the sources by the assembly step, by *parsing* them, and it is the check that found
four modules the package imported but, in its first assembled form, did not ship.

**6.3 Seeds, and why the numbers are stable.** Every sweep declares its seeds. The deciding sweeps use
up to {{n_deciding_seeds}} seeds per cell over {{n_deciding_cells}} cells (plus
{{n_deciding_groups}} mechanism groups, counted
separately because a group is a family and not a cell), and the specification is
sampling by declared seed rather than by a clock or a process id: two runs of the same sweep on different
days produce byte-identical artefacts, which is what makes 6.1's byte-identical expectation reasonable
rather than aspirational.

**6.4 Failure is attributable, and output paths are declared.** Each step exits non-zero with a message
naming the object it read and the property that failed -- an unresolved placeholder names the fact
(4.2's controls: a perturbed value in one artefact moves the paper and fails the check, and the failure
prints which file moved). The declared outputs are `artefacts/*.json` (per-sweep results),
`manuscript.md` (assembled body plus the rendered bibliography), `refs_order.json`, `references.json`,
`refs_display.json` and `reference-check.md`. No step writes outside the package directory, and no step
mutates the evidence it reads.

**6.5 Environment.** The instrument needs a Python 3 interpreter and nothing else: no packages, no
compiled extensions, no network access except the reference-verification step (which is the one step
that reads external records, and which the committed `reference-check.md` is the record of). The paper's
sweeps are CPU-only and finish in minutes on one laptop; the environment is stated in the package's
`README.md` together with the one command and its expected output.

## 7. The registered prior beliefs, in full

This section restates the registration's "Prior beliefs" paragraph, one entry per belief, and states for
each whether the results confirm it, contradict it, or leave it unresolved. The point of the exercise is
that a reader can see the registration and the result side by side.

**P1 -- "a sharp boundary exists, and it moves with the speculation rate".** *Registered:* for fixed
`h`, speculation's benefit crosses zero at a utilisation `rho*(h)`; `rho*(h)` decreases in `h`; the
crossing is sharp rather than gradual. *Outcome:* **unresolved as registered**. A boundary exists and is
located in every cell (4.2) -- and the single-crossing property is what makes its *location*
well-defined. The sharpness half of this prior is **not measured**: the registration operationalised
"sharp rather than gradual" as the `rho`-width of the `+5%`-to-`-5%` fall, and the committed
windows bracket the zero crossing rather than that band, so the statistic is reported unmet with its
reason (4.2) instead of being replaced by a nearby quantity. The registered *variable* is also not
the one that indexes the boundary: the
boundary moves with the pool size, and the registered closed-form law for its movement deviates beyond
its own bound in {{hr_deviating}} of {{hr_groups}} groups, while the shift decomposition is consistent
in only {{hshift_consistent}} of {{hr_groups}}. Reporting this as a confirmation would be a
reinterpretation of the registered sentence; the honest report is that the prior was neither confirmed
nor refuted but mis-specified, and that what replaced it is indexed by `A` as well as `h`.

**P2 -- "the tail, not the mean, sets the boundary".** *Registered:* two latency distributions matched
on mean but differing in tail weight have different `rho*`; the heavier tail gives the **larger** `rho*`
and a **steeper** fall. *Outcome:* **contradicted, both halves** (4.4). Heavier tails do have larger
unloaded hiding limits -- the premise the belief rests on is true -- and yet the boundary moves *down*,
by an amount {{tail_shortfall_factor|.1f}} times smaller than the registered separation, and the fall past it is *shallower*.
This is the paper's clearest falsification: the belief is anchored in a real mechanism (tail events are
the thing being hidden) and the mechanism does not survive a queue.

**P3 -- "part of the reported gain is parallelism, not prediction".** *Registered:* the
prediction-attributable fraction `F` against a serial baseline is **below 0.7** once the baseline may
spend the same capacity, and `F` **decreases in `rho`**. *Outcome:* **half confirmed, half
contradicted**. `F` is below 0.7 in every cell of the matched-parallelism control (4.5), and it does not
decrease in `rho`: at fixed width, the pool coordinate changes nothing at all once the pool is at least
the agent count, and what moves `F` is the width. The registered threshold was right and the registered
mechanism for its movement was wrong, which is a strong result reported as a partial one.

**P4a -- "the safe region shrinks".** *Registered:* with a non-idempotent fraction `q` and compensating
cost, the safe region shrinks by a measurable amount. *Outcome:* **confirmed** -- all
{{p4a_families}} load-bearing families have a paired shrinkage interval strictly above zero (4.6).

**P4b -- "the shrinkage is at least 0.05 in `rho*` at `q = 0.05`".** *Outcome:* **contradicted**, with a
shortfall factor of {{p4b_shortfall}} (measured {{p4b_lowest}} to {{p4b_highest}}). The channel is real
and an order of magnitude smaller than registered; a reader deciding whether to spend effort on
side-effect accounting should read this number rather than the prior.

**P4c -- "a domain admissibility rule leaves permitted-but-harmful states".** *Registered:* the field's
precondition (speculate only on side-effect-free, idempotent or stageable edges) leaves a **non-empty**
set of permitted states with negative benefit. *Outcome:* **confirmed**, and the confirmation is
carried by individual steps rather than by construction: of {{p4c_cells_located}} readable cells,
{{p4c_cells_losing}} contain losing steps, at a fraction between {{p4c_frac_lo}} and {{p4c_frac_hi}}
(4.6). The reading that *is* by construction ({{p4c_by_construction}} cells above a located crossing)
is reported separately and does not carry the claim.

**7.1 Why pre-registration changed the paper rather than decorating it.** Three of the six registered
beliefs were contradicted and one was left unresolved; two were confirmed. In each case the registered
sentence named the *quantity* and the *direction* in advance, which is what made the failures
interpretable: P2's refutation is informative because the prior specified both the sign and the ordering
and the data inverted both, and P3's partial result is informative because the prior separated "how
much" from "which way it moves". A study that had measured the same numbers without registering them
could have reported all of this as exploration; it would then have had no way to show that it was not
choosing the axis after seeing the data.

## 8. Threats to validity, and why this is worth publishing anyway

**8.1 What could be wrong.** *Internal validity:* the model's assumptions (5.1-5.3) are the largest
threat -- the boundary is exact for the instrument and approximate for the world. *Construct validity:*
`rho` is measured rather than assigned, which is the study's main defence, but it is still a model's
`rho`; and the claim "the boundary is indexed by the pool" is a claim about how `rho` is *realised*,
which a different workload could realise differently. *Statistical:* each family's crossing is carried
by a per-seed interval over up to {{n_deciding_seeds}} seeds, and the paper makes {{dec_contrast_cells}}
matched contrasts -- a reader should treat each contrast's interval as the unit of evidence and the
collection of them as a pattern rather than as a multiplicity-corrected family. The one test that does
not depend on intervals is the containment test at {{boundary_tol}}: of {{boundary_matched_pairs}} pairs
of cells from different pools whose measured contention agrees to that tolerance,
**{{boundary_matched_disagreeing}} disagree in sign**, which is not a small-sample artefact of a
location estimate -- it is a count. *External validity:* three published cells (5.6), one of which the
instrument cannot reach; the paper reports that cell as unreached rather than as evidence. *Publication
validity:* the criteria that could not be met as registered are stated in the abstract's own voice
(4.2, 4.4, 4.7), so a reader who only reads the summary sees them.

**8.2 Whose belief changes, and how.** Three decisions, three communities.

* **A systems group that reports a speculation speedup.** Their reported gain is measured against a
  serial schedule, and this paper's matched-parallelism control shows that a blind schedule of the same
  width already buys a share of the informed gain that **grows past half as the width grows**:
  {{blind_share_h025}} of the gain at `h = 0.25`, {{blind_share_h050}} at `h = 0.50`. The informed
  share moves the other way ({{F_h025}} at `h = 0.25` to {{F_h050}} at `h = 0.50`), which is what
  "prediction buys less as width grows" means numerically. The changed decision is procedural and cheap: report the blind arm alongside the predictor. It
  costs one extra run and it separates "our predictor is good" from "we issued more calls early", which
  no published speculation system in this area currently separates.
* **A tooling team deciding when to enable speculative tool calls.** The folk guidance they inherit --
  hide the tool wait, the tail is what hurts, keep it idempotent -- is answered here in its own terms:
  the boundary is real and it is close ({{rho_star_A16}} to {{rho_star_A96}} across a six-fold pool
  range, and cells that share a measured utilisation to within {{boundary_tol}} on opposite sides of it),
  the tail ordering is the opposite of the folklore, and idempotency does not bound the harm because the
  harm is contention ({{p4c_cells_losing}} of {{p4c_cells_located}} readable cells contain losing steps
  under a rule that permits them). The changed decision is where to set the speculation rate as a
  function of observed load rather than as a function of perceived latency pain.
* **A reader of the 2026 speculation literature.** Each of the seven in-window systems cites a speedup
  measured in a window its authors chose. This paper supplies the missing axis -- and, with it, the
  question a reader can now ask of any such number: *at what pool size and at what measured contention
  was it obtained, and does the effect survive a blind arm of equal width?*

**8.3 Why the negative results are the contribution.** Two registered beliefs were refuted, one left
unresolved, one confirmed only in its threshold. A paper that reported only the boundary would be a
parameter study; what makes this one worth publishing is that the refutations are *about the field's
working assumptions* and are cheap to act on. The tail belief in particular is stated as mechanism in
several of the surveyed systems and is inverted here at matched means: a reader who believed it now has
a reason to re-check whether their workload's boundary moves the way they assumed, and the instrument to
do it is in the package, stdlib-only, in minutes.

## 9. Conclusion

**9.1 What was found.** Speculative tool execution stops paying at a boundary that is real and indexed
by the *pool* as well as by the speculation rate: `rho*(A, h)` falls from {{rho_star_A16}} at
`A = 16` to {{rho_star_A96}} at `A = 96`, a span {{rho_star_span}} -- about {{rho_span_over_interval}}
times the estimator's own interval width -- while cells from different pool sizes whose measured
contention agrees to within {{boundary_tol}} land on opposite sides of the boundary in
{{boundary_matched_disagreeing}} of {{boundary_matched_pairs}} pairs. What moves the boundary as the
pool grows is not how long a call takes but whether it is displaced at all ({{dec_carrying_overshoot}} of
{{dec_contrast_cells}} matched pairs are carried by the overshoot term rather than by the service term).
The tail does not index it: a mean-matched heavier tail moves the boundary *down*, and its fall is
*shallower*. The share of the gain that a blind schedule of equal width already buys grows with the width
({{blind_share_h025}} at `h = 0.25` to {{blind_share_h050}} at `h = 0.50`), while the
prediction-attributable share falls -- with the width, not with contention.
The side-effect channel shrinks the safe region by an order of magnitude less than expected and, more
importantly, leaves a non-empty set of states negative that a rule keyed to idempotency permits: at one
cell at the boundary, {{m4b_neg_steps}} of {{m4b_steps}} steps lose while the mean step still gains.

**9.2 What would follow.** Three upgrades are stated in the registration and remain open: a
disaggregated fleet with per-tier tails, where the boundary becomes a set of boundaries; an online
controller that estimates `(rho, tail)` and sets `h`, for which this paper supplies the region rather
than the policy; and branching tool graphs, where the speculatable set is chosen rather than given. The
first deployment-facing item is (5.1): read a real agent loop's tool-wait share and contention, and ask
whether the boundary arrives where the model puts it.

**9.3 The one-sentence version.** Speculative tool execution is a bet on contention, not on latency: it
pays below a boundary that the pool size, not the tail, locates, and at half width more than half of
what it buys is the parallelism its own baseline was denied.
