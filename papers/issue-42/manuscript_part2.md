## 3. Prior beliefs (registered before the deciding runs)

The following priors were fixed in the research registration before the adjudicating experiments,
with the grounds for each prediction. They are reported here with their outcomes; Section 8 returns
to what the refutations do and do not license.

**P1.** *Realistic supervision layers are strongly aligned with the layer beneath them, so residual*
*catch is substantially below standalone catch.* Grounds: N-version and multiversion studies found
coincident failures to be the norm rather than the exception **[@{knight1986nversion};
@{littlewood1989coincident}]**, and self-critique methods reuse the same model that produced the
output **[@{madaan2023selfrefine}; @{huang2023selfcorrect}]**. **Outcome: CONFIRMED in the
calibration.** The published systems we could read report between-layer agreement far above the
independence benchmark: two formalisation pipelines agree on 31.0 percent of their overlap where
independence predicts 100 percent **[@{specgen2026}]**; an uncoordinated three-layer ECC stack
duplicates redundancy by design **[@{cerberus2026}]**; a verification tool's headline finding is
independently re-found by a human-filed report **[@{bmc2026}]**. Betas in the calibrated set run
from 0.00 to 0.80 with a majority above 0.3.

**P2.** *Accuracy ranking overstates marginal value: there is a non-corner inversion region in which*
*a lower-accuracy but decorrelated layer dominates a higher-accuracy fully aligned one.* Grounds:
the marginal quantity does not contain the layer's accuracy **[@{mozannar2020defer}]**; ensemble
theory separates individual from combined accuracy **[@{kuncheva2003diversity}]**. **Outcome: MET,
with a caveat we flag rather than bank.** 32 percent of equal-cost strictly-lower-accuracy pairs are
inversions, 66.7 percent when both alignments are interior — but the identical figure appears in all
four families because the condition is scale-free in p0, so the registered three-of-four-families
clause is satisfied **trivially** and is not counted as four independent confirmations. The inversion
additionally requires the layer to be cheaper per unit of hazard.

**P3.** *A one-scalar threshold law predicts the layer-addition decision out of sample.* Grounds:
cost-sensitive thresholds are typically stated as scalars **[@{fawcett2006roc}]**. **Outcome:
UNMET in the registered one-scalar form.** Out-of-sample median relative error for a constant on the
residual product is 38.0 percent, against the registered 25 percent limit. The registered fallback
applies: the **driver** is confirmed (the residual product), the **one-scalar threshold** is false.

## 4. The construct: residual catch and the redundancy dial

Consider two supervision layers in sequence. The primary catches a fraction f of the items that need
supervision; a population fraction p0 of items are hazardous. A candidate second layer has a
standalone catch rate C2. What matters for the decision to add it is **where its catches fall**.
Define the **residual catch**

    q_res = P(layer catches | primary missed)
    q_red = P(layer catches | primary caught)

and the alignment **alpha = q_red - q_res**. Equal accuracy does not imply equal alpha, and alpha is
what the layer's marginal value depends on. To make this testable we introduce a dial that moves the
layer's catches between the two populations while holding its accuracy **exactly** fixed:

    q_red = beta * C2 / f
    q_res = (1 - beta) * C2 / (1 - f)

so that f * q_red + (1 - f) * q_res = C2 for every beta. The dial has three interpretable values.
At **beta = 1** the layer is perfectly aligned: every catch lands on an item the primary already
caught, and the marginal catch is exactly zero. At **beta = 0** the layer is perfectly
complementary. At **beta = f** we recover q_res = q_red = C2 — which is precisely the classical
**independence** assumption **[@{breiman1996bagging}; @{dietterich2000ensemble}]**. Independence is
therefore a single point on this dial, not a regime, and the single point at which a practitioner
who never measures alignment implicitly operates.

Two consequences follow immediately and are used throughout. First, the marginal contribution of the
layer is

    marginal_catch = p0 * (1 - beta) * C2,

because the residual pool is p0 (1 - f) and q_res = (1 - beta) C2 / (1 - f), so f cancels. The
marginal value is therefore **free of the primary's accuracy** — a fact that contradicts the natural
intuition that a stronger primary makes a second layer worth less. Second, the estimand is directly
observable from logs: q_res is a conditional rate, so a deployer need not estimate beta to apply the
rule. This matters because beta is a latent construct; q_res is not.

## 5. Theory: when does adding the layer beat spending on the primary?

Adding the layer is a choice against the alternative of giving the layer's budget to the primary.
Let the primary's catch rate respond to budget, and let r = kappa2 / kappa1 be the cost ratio of a
unit of layer capacity to a unit of primary capacity. If the primary received one unit of layer
capacity it would reach f2. Adding the layer is optimal exactly when

    (1 - beta) * C2  exceeds  T(f, r, C2) = f2 - f .          (1)

The threshold T is the object of study. Under the budget model used throughout, the primary's
response composes catch in the log-odds domain,

    f2 = 1 - exp( -( H(f) + r * H(C2) ) ),     H(x) = -log(1 - x),       (2)

so T depends jointly on f, on r, and on C2. Three structural facts follow, and each is checked
against simulation rather than asserted (Section 6):

**S1.** T is not a constant: it moves with all three arguments, so any rule that fits one number
will fail on the region that number does not cover.
**S2.** The decision rule is nevertheless writable in deployable variables, because q_res and f are
observable from a log while beta need not be. Recomputing T from the primary's own observed budget
response is the **operational** form.
**S3.** The classical independence reading (assume beta = f, therefore always add) predicts T = 0 for
every cell, i.e. it never declines to add a layer. It is the correct rule only at one dial value.

The final element is the capacity **allocation**. A layer distributes its capacity over strata, and
strata differ in how much hazard they hold. Writing u for the capacity allocation over strata, the
catch available to layer k is bounded by the remaining hazard in each stratum:

    marginal_k = sum_s min( capacity * u_s , remaining_hazard_s ).      (3)

Equation 3 is what makes the composition question of Section 7.4 non-trivial: two configurations
can share capacity and nominal alignment and still allocate differently, and the min() makes the
difference persistent rather than cosmetic.

## 6. Experimental setup

All experiments are deterministic given seeds and run on CPU. Four instruments were built in
sequence, each augmenting rather than replacing its predecessor; every headline number in this
paper is emitted by one of them and reproduced by a single command (Section 6.1).

- **v0** (`instrument_v0.py`) establishes the construct: 400,000 items per cell, f = 0.30, C2 = 0.15,
  p0 = 0.20. It checks accuracy invariance across the dial, the monotone decline of marginal catch,
  endpoint reproduction, layer inertness, and recovery of alpha including the independence control.
  **19/19 reductions.**
- **v1** (`instrument_v1.py`) measures the marginal-value surface over (beta, cost ratio) with four
  baselines, and locates the inversion region. **18/18 checks.**
- **v2** (`instrument_v2.py`) performs the out-of-sample law race required by the registration: fit
  on 4 families x 3 cost ratios x 5 layer accuracies x 5 dial values (300 cells), score on 3
  families, 4 cost ratios, 7 accuracies and 6 dial values **never fitted** (504 held-out cells,
  disjointness asserted on all four axes). The predicted quantity is T, the metric is **median
  relative error** as registered. **14/14 checks.**
- **v3** (`instrument_v3.py`) calibrates, composes and adversarially stresses the model. **24/25
  checks**, where the single failure is a registered prediction the instrument refuted (Section 7.5).

**Reproduction.** `bash reproduce.sh` runs all four instruments and validates the emitted artefacts
against committed expectations; `validate.py` asserts the numbers quoted in this manuscript against
the JSON they come from, and `trace_check.py` checks that every quoted figure has a producing cell.
Random seeds are fixed and recorded; the artefacts carry a content digest.

### 6.1 Calibration protocol

The v3 calibration required bounding the regime parameters from real systems. The arXiv export API
was unavailable for compound queries throughout (repeated timeouts and HTTP 429 across retries), so
the **declared fallback transport** was used: `arxiv.org/abs` abstract pages and `arxiv.org/html`
full texts, with the transport recorded per entry. Each calibration cell carries a verbatim quote,
the numbers the source reports, and the derivation from those numbers to (f, C2, beta, r). Every
quote is verified against a committed capture, and the verifier is **two-sided** (a mutated quote is
rejected). The resulting set is 12 cells drawn from 10 independent published systems, of which 7 are
quantitative and 5 are construct or mechanism anchors. The quantitative anchors are a compilation
repair loop that raises success from 36-55 percent to 64-100 percent, i.e. a near-zero alignment on
the failed population **[@{helios2026}]**; two formalisation pipelines that agree on 31.0 percent of
their overlap **[@{specgen2026}]**; a three-layer ECC stack whose layers evolved independently
**[@{cerberus2026}]**; a verification tool whose finding a human independently re-files
**[@{bmc2026}]**; a human layer that is anti-correlated with the primary **[@{ltd2026}]**; and an
allocation anchor whose noise is negatively correlated with feature importance at -0.81
**[@{aniso2026}]**. The mechanism anchors establish the direction of the cost ratio
**[@{flowbyflow2026}]**, that uncertainty sources are separable for analysis but "not independent in
practice" **[@{mllmunc2026}]**, that redundant-information elimination is a named advantage of
stacked agents across six independent cohorts **[@{feat2025}]**, and that guardrail artifacts can
contradict one another or evolve independently **[@{layered2026}]**.

