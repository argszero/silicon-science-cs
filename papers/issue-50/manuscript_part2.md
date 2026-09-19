## 3. The instrument and the design

### 3.1 What is measured

The unit of the model is one *step* of one agent loop: a think phase of mean `mT` = {{think_mean}},
followed by one tool call served by a shared pool of identical workers, of mean service
`mS` = {{service_mean}}. Latency is measured per step, from the start of its think phase to the
completion of that step's real call.

Speculative execution issues the call at the *start* of the think phase. With probability `h` the guess
is the call the step really needs and its service proceeds, overlapping the thinking; with probability
`1 - h` the guess is discarded, having occupied a worker for its service time, and the real call is
issued at the end of the think phase. When the discarded call would have had an external effect, the
discard pays a compensating cost: with probability `q` it consumes `comp` further units of worker time
that no step waits for. That work is *charged to the pool and invisible to the latency of the step that
caused it*, which is the asymmetry a domain rule keyed to tool semantics cannot see
[@mehan2026;@idempotency2025].

Contention is not a setting of the model. `rho` is measured as total worker-busy time divided by
`c x makespan`. What is set is the pool size and the number of agent loops; `rho` is what the run then
exhibits. That is what lets the boundary be a statement about a system under a load rather than about a
knob: no cell is assigned the contention it is supposed to have.

The object of the study is `rho*(A, h)`: the utilisation at which the mean per-step benefit of
speculation -- serial latency minus speculative latency, per step, paired by seed -- crosses zero,
indexed by the pool size `A` and the speculation rate `h`. Two properties travel with it. First,
whether it is a crossing at all: a cell whose interval straddles zero is reported `ambiguous` and is
never smoothed into a location. Second, its sharpness, the `rho`-width of the fall from +5% to -5% of
the serial latency, which is what distinguishes a boundary from a gentle slope.

### 3.2 A deterministic simulator, and why determinism is part of the design

The instrument is a discrete-event simulator, CPU-only and standard library only, with service times
drawn from closed-form distributions and every seed declared. Its structure is unremarkable. Its *draw
discipline* is not: every random quantity a step needs -- its think time, its service time, the
realisation of its guess, and the realisation of its side-effect channel -- is drawn **once per
(agent, step) before scheduling**, and the schedule is then a pure function of those draws. A change of
policy therefore changes the schedule and never the draws.

Three consequences carry through the paper. The no-speculation limit (`h = 0`) is an *identity* rather
than a statistical comparison: the committed check compares event traces, not means. Every
serial-versus-speculative difference is a difference of schedules alone, which is what makes the
pairing by seed legitimate. And the two ends of the `h` axis are both defined inside the instrument --
`h = 0` is the serial schedule, `h = {{h_oracle_value}}` is an oracle in which every guess is correct --
so the quantity that §4 reports is a property of the model rather than a curve fitted to it.

The discipline is checked, not assumed. Each sweep carries a `draw_prefix` block that re-derives the
draws of a configuration and compares them with the ones the run actually used:
{{draw_prefix_validated}} of {{draw_prefix_checked}} checked configurations reproduce their draws
within the declared arithmetic tolerance {{draw_prefix_tol|.1e}}, and the block reports the largest
observed difference rather than a pass/fail alone.

The two latency classes are matched on the mean by construction: exponential (coefficient of variation
1) and Pareto with tail index {{pareto_alpha}}, scaled to the same mean. The index is above 2 so that
the variance exists; a heavier index would make the measured mean a statement about the tail
realisation rather than about the workload, and the whole point of the matched pair is that only the
tail weight differs [@whitt2000;@sigman1999].

### 3.3 Anchors before measurement

A boundary measured on an instrument that does not reproduce its own classical limits is a number about
the instrument. So the first step measured only quantities with closed forms, and the instrument was
not used to claim anything until they reproduced. {{n_anchors}} anchors were declared; {{n_anchors_ok}}
of {{n_anchors}} reproduce their closed forms. Each anchor also has a `--selftest` arm that plants a
defect into the instrument and requires exactly *that* anchor to fail, so that an anchor which cannot
fail is visible as such.

* **A1, the queueing layer alone.** Mean sojourn time against the M/M/1 closed form
  `1/(mu - lambda)`, at {{a1_levels_n}} utilisation levels with {{a1_n}} arrivals each. The largest
  relative error over the levels is {{a1_max_rel_error|.4g}}, inside the declared tolerance
  {{a1_tol}}. Each level's closed form lies inside a *batch-means* interval, because the samples are
  autocorrelated and an i.i.d. interval would be narrower than the truth -- which matters here,
  since every claim in this paper is comparative [@finch2019].
* **A2, the no-speculation limit.** At `h = 0` the schedule must be the serial schedule exactly: the
  check is an identical event trace. This is the check the draw discipline above exists to make
  possible.
* **A3, the hiding limit with no contention.** At `h = 1` and no contention, the benefit must equal
  `E[min(T, S)] = mT*mS/(mT+mS)` = {{hiding_limit}}, the share of the call the thinking can absorb.
  Measured: {{a3_measured}}, a relative error of {{a3_rel_error|.4g}}.
* **A4, the direction across the saturated half.** Benefit must not increase as contention grows. The
  strict form first written was **refuted by the instrument's own data** -- benefit *rises* slightly
  before it falls (at `rho` = {{a4_rise_rho}}) -- so the anchor was restated as the saturated-half
  fall, which holds. The refutation is kept in the record because it is the reason §4 reports
  direction as an interval statement rather than as a monotonicity claim.

### 3.4 Cells, grids and seeds

Every sweep declares its grid, its seeds and its arithmetic tolerance, and each declaration is a
committed file rather than a paragraph:

| study | what varies | seeds |
|---|---|---|
| boundary sweep | pool sizes {{{boundary_pool_list}}}, at `h` = {{{boundary_h_values}}} | {{boundary_seeds}} per family |
| variant split | `h` x `c` over {{{variant_h_values}}} x {{{variant_c_values}}} ({{variant_cells}} cells) | {{variant_seeds}} |
| load decomposition | {{decompose_cells}} cells | {{decompose_seeds}} |
| tail pair | {{tail_families}} mean-matched latency classes | {{tail_seeds}} |
| prediction split | the two tail classes | {{predsplit_seeds}} |
| side-effect study | {{sideeffect_families}} families, {{sideeffect_shrink_rows}} paired shrinkage rows ({{sideeffect_not_located}} not located) | {{sideeffect_seeds}} |
| mechanism study | {{mechanism_groups}} groups | {{mechanism_seeds}} |
| closed-form comparison | {{fixedpoint_cells}} same-cell rows, {{fixedpoint_excluded}} excluded | 16 |
| external cell | {{external_cells}} published cells | declared |

Two coordinates are worth stating because they make later numbers comparable rather than merely
precise. *Contention is measured, and pairing across pool sizes is done on the measured value.* Cells
from different pool sizes may be paired only when their measured `rho` differs by no more than the
declared tolerance {{boundary_tol}}; the tolerance is a coordinate, and a pairing tolerance wider
than the effects it reads would prove nothing. That test finds {{boundary_matched_pairs}} such pairs
across pool sizes, of which {{boundary_matched_disagreeing}} disagree in sign -- the direct test of
whether contention alone determines the outcome. *The closed-form comparison uses a declared
tolerance of {{fixedpoint_tol}} and a declared minimum fraction of cells of {{fixedpoint_min_fraction}},*
and it reports the cells it could not compare as exclusions with their kinds, rather than dropping
them.

### 3.5 Baselines and controls

A speedup number is only interpretable against what it was measured against, so the design fixes four
comparisons before any of them is run.

1. **The serial baseline is the same instrument with speculation off.** Because of the draw discipline,
   this is an identity rather than a re-implementation: the baseline cannot drift from the treatment,
   and it is not under the authors' control to make look slow.
2. **The oracle is the other endpoint, also inside the instrument.** Every guess correct, no discard:
   it bounds what *any* prediction-based policy could buy in this model, and it is what the external
   cell's sensitivity study varies in §4.6.
3. **The matched-parallelism control is the decisive one.** It issues the same number of calls of the
   same width against the same pool, but chooses them *blindly* -- the speculation width is matched and
   the information is removed. The share of the informed gain that a blind schedule of the same width
   already buys is reported as one minus the prediction-attributable fraction `F`. This control is what
   separates "prediction" from "concurrency the serial baseline never had", and its result is the one
   §4 reports as the paper's largest single revision of the folklore [@aktas2017;@schol2019].
4. **The external cell compares against a published number, not against a re-run of its system.** A
   published result in this area reports an operating region and a magnitude; the model is asked for
   its sign there, for whether the reported magnitude is reachable inside the model's own band, and --
   when it is not -- for the shortfall, reported as such rather than smoothed into an agreement.

### 3.6 The registered criteria are the contract of §4

The study registered six success criteria before the deciding runs, and §4 reports each of them as met
or as **unmet with the reason**, in the registered order: (i) `rho*` per cell with a bootstrap interval,
plus the sharpness statistic; (ii) the tail separation test -- `|delta rho*| >= 0.15` with disjoint
intervals -- on mean-matched distributions; (iii) the prediction-attributable fraction `F` per cell
against its threshold; (iv) the side-effect shrinkage and the count of states that a domain
admissibility rule permits but that have negative benefit; (v) the closed-form fixed point within
`+/- 0.05` of the simulated `rho*` in at least 80% of cells; (vi) the external cell reproducing the
published result's sign in its reported operating region.

Registration is a promise about *reporting*, and it is kept literally: the outcomes of the four
registered prior beliefs and of these six criteria are stated again in §7 in the same words as here, so
that a reader can check the results section against the registration without leaving the paper.

### 3.7 What this instrument cannot show

The instrument is a model, and three of its properties bound every claim that follows. It reports
*model* latency under a *modelled* contention; it does not measure a deployed tool server, and it makes
no claim about wall-clock behaviour of any real system. Prediction enters as a scalar hit rate `h`,
not as a learned predictor, so nothing here is a statement about predictor accuracy -- only about what a
given accuracy buys at a given load. And the side-effect channel is modelled as a compensating cost that
is charged to the pool, not as a semantics: the paper's side-effect result is about *where the cost
lands*, not about what a non-idempotent call does. Section 5 states these as limitations and states what
would be required to remove each; §8 argues why the boundary is worth having anyway.
