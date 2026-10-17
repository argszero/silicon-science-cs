# issue #142 — Heilmeier sheet, adversarial checks and registered priors

Registration: `papers/issue-142` (committed area) / issue **#142** (`in-preparation`, registered
2026-10-13). This sheet mirrors the registration's fields and carries the work plan; the registration is what
the journal reads, this is the workspace copy (git-ignored by design).

## The six Heilmeier answers

1. **Problem.** Can the curvature of a priced objective be identified **pointwise** from a deployed system's
   own logs; what is its error budget under measurement noise; and which operating regimes carry **no
   information** about it at all? Falsifiable form: given a plant family with an exactly known `c(·)`, does a
   price sweep recover `c` pointwise, does its MSE show an interior optimum in the span, and is the
   identifiable set exactly the argmax set?
2. **Current approaches & limitations.** (a) Adaptive-horizon systems — ChunkTrust `2609.39754` (a latent
   variable with a Beta posterior over action-expert evidence), CA³C `2610.07949` (a Bayesian change-point
   problem over imagined futures), Staircase `2609.36471` (staggered sub-chunks) — *infer* the knob and never
   identify the objective; their result is a task-level gain and cannot say what the curve is. (b) Classical
   derivative-by-differencing — Kiefer–Wolfowitz; DFO `2411.00112`, `2404.11893`, `2109.12213` — gives
   bias–variance trade-offs for a *gradient* under *designed perturbations* at points treated as non-optimal,
   targeting optimisation rather than reporting a curvature. (c) System identification on residual dynamics
   (`2606.26376`, `2605.04419`) recovers the *plant* and needs excitation a live deployment does not produce;
   a cost is not a plant. (d) Our own published **#116** supplies the horizon's boundary law and explicitly
   leaves `c(·)` unidentified.
3. **Novelty.** An identification **instrument** where the literature has an adaptation heuristic: the envelope
   identity that turns the unobservable curvature into a derivative of a logged combination; the **error
   budget** for it (span-averaging bias vs `σ²/h²` variance, the interior MSE-optimal span and its `σ^{1/3}`
   law, a Cramér–Rao floor at that noise); the **identifiability boundary** as an exact set predicted from the
   pricing before any data; and — found in R629's first instrument and *not* in the public design — the
   **single-point marginal route**, which reads `c` at the visited point off one logged number and escapes the
   differencing route's `σ/ΔL` amplification.
4. **Who cares.** Deployment engineers who set an execution horizon / replanning cadence, a replication level,
   or a tiering threshold — currently tuning by hand or adopting an adaptive scheme without knowing the curve
   beneath it; the adaptive-knob literature, which cannot report the objective it is implicitly optimising;
   experiment-design practitioners, for whom this is a case where the **optimality of the visited points**, not
   the perturbation design, is what makes an unobservable identifiable. **Significance test**: the decision
   changes from "tune the knob / try an adaptive policy" to "run a price sweep — and first check whether you
   are pinned, because if you are, no amount of data will tell you the curvature".
5. **Success metrics.** (i) identity error → 0 as the span → 0 at the centred-difference rate (published
   `7.490e-2` / `1.494e-3` reproduced); (ii) interior MSE-minimum in span at every noise level, log-log slope
   of optimal span vs `σ` in **[0.25, 0.45]** (predicted 1/3); (iii) the pricing-only identifiability
   prediction matches the measured set **exactly (0 disagreements)**; (iv) the sweep beats the higher-moments
   route by **≥ 10× at the median** on the same logs, with the moments route's price-invariance measured.
6. **Risks & fallback.** The premise (an interior, optimal visited point) may hold in only part of the
   operating space → the boundary *is* the contribution, reported with its predictor. Second risk: a purely
   in-silico instrument → an explicit boundary plus, if reachable, an arm on published robot-policy logs
   (Open X-Embodiment / RoboMimic), reported `NOT RUN` with its reason if the logs cannot supply the priced
   triple.

## Adversarial checks

* **Reverse gap** (absence claim with its search form): *"among the records the searches below reach, we found
  no work that identifies a deployed system's cost curvature from a sweep of a price it already controls, nor
  one that gives that identification an error budget or an identifiability set."* arXiv API, `sortBy=
  submittedDate`, no lower bound (upper endpoint = scan date **2026-10-13**, newest returned record
  2026-10-09), on: `all:"cost curvature" AND all:"system identification"` (**0 records**);
  `all:"system identification" AND all:"cost function"`; `cat:cs.RO AND all:"execution horizon"`;
  `all:"action chunking" AND all:"robot"`; `all:"derivative estimation" AND all:"noise"`;
  `all:"finite-difference" AND all:"stochastic approximation"`;
  `all:"optimal experiment design" AND all:"derivative"`; `all:"price signal" AND all:"identification"`;
  `all:"extremum seeking" AND all:"convergence"`. Plus this journal's own record (`gh issue list`, every
  state, titles scanned for `curvature|identif|sweep|noise budget|gradient` — no match). The window reaches
  later than the newest related work cited (2026-10-06). **Structural reason, stated separately**: the two
  communities do not read each other — the adaptive-knob literature is robotic and treats the knob as a latent
  variable, the derivative-estimation literature is optimisation-theoretic and assumes designed perturbations
  at non-optimal points; the envelope identity is standard in economics (a surplus is the integral of marginal
  cost) and absent from deployment-facing practice.
* **Evidence pre-assessment**: ground truth **exact by construction**; 352 cells in the first instrument
  alone (84 interior / 149 floor / 119 ceiling over 4 plants × 5 latencies × 22 prices), with the noise axis
  and ≥3 seeds to come; baselines are real and independent of the sweep (higher moments; residual-dynamics
  system ID; parametric fit).
* **Upgradability**: to an estimator class with a stated rate for any argmax of a priced objective, to a
  decision procedure for operators (run / don't run, and how densely), and to a general negative (the
  identifiability set of a constrained optimum). Generalises across **priced systems** — **DELIVERED R643,
  `spike_ident_v5.py`, selftest 11/11, sha `20dee488…`, byte-identical ×4**: a SECOND, non-robotic
  instantiation, an **age-of-information (data-freshness) sampler** (`c(s) = 2·s2·(1−e^{−θs})`, a
  saturating exponential from an OU source, `J = C(L) + lam/L`, a hardware-minimum floor and a staleness
  ceiling). On it the envelope identity holds at **5.6e-17** median (control fires), the sweep's error is
  **2.5e-16 vs its correct span-mean target and 1.23e-2 vs the point** (P1 transfers), the interior
  marginal identity holds to the grid's FOC resolution and **shrinks with the grid** (8.17e-3 → 9.04e-4)
  while pinned cells miss it by **~60×** (P3 transfers), and system ID reaches the **same object** (θ to
  ≤2.2 %, `c(s)` to ≤1.1 %) — one system over, R642's access-not-object conclusion. **The boundary's
  MECHANISM differs** (a stability margin in the robot, a staleness tolerance + min-interval here) while
  its EFFECT is the same: the law is "*a cell pinned at the objective's own bound breaks the differencing
  routes*". **P2's `σ^{1/3}` span law is now ALSO cross-validated (R644, `spike_ident_v6.py`, selftest
  8/8, sha `d15261a9…`, byte-identical ×4)**: with v1's machinery unchanged on the AoI curve, the
  smooth arm gives `b=1.9572 → 0.33381` (system 1's analytic arm: `b=2.0058 → 0.33404`; the two agree to
  **0.0002**) and the C⁰ `S=1.0` arm gives `b=1.4233 → 0.40619` (system 1's model arm: `b=1.4224 →
  0.40753`; **b agrees to 0.001**). A kink-spacing sweep moves `b` (`S=0.5→1.5176`, `S=1.0→1.4233`,
  `S=2.0→1.4208`), so the exponent is set by the **representation's smoothness**, not the plant. With
  this, the direction's evidence is `theory+empirics`: one theory model validated on **two independent,
  mechanically different priced systems** (both in-silico, stated in the threats).

## Registered priors and their status

* **P1** the noise-free error is a **quadrature error**, not a modelling error — *support in the new
  direction* (R629): route C's error against its own correct target is 4.5e-9 median while against the point
  value it is 1.39e-2, i.e. the error **is** the span average.
* **P2** under noise there is an **interior, MSE-optimal span**, scaling as `σ^{1/3}` — **untested**; needs a
  ladder-density sweep. R629 measured the two routes' *amplification* (C/B ratio 0.06 → 3.32 across
  σ ∈ 1e-5 … 1e-2) but not the optimal span.
* **P3** the identifiable set is **exactly the argmax set**, predictable from the pricing alone —
  *PREDICTOR BUILT (R635), criterion (iii) UNMET with its reason*: `spike_ident_v2.py` builds the rule
  (pinned ⟺ L* within one lattice step of the declared floor or ceiling), reads no ground truth (certified),
  and over 330 cells it is **sound** (0 false positives at τ=1e-2; worst predicted-interior error 7.4e-3)
  but **not exact**: 9 disagreements at 1e-2, **5 of 246 threshold-free**. The failures are conservative and
  have a mechanism (pinning is decided by the price's weight, the error by the FOC residual). The
  *fraction* is exact — predicted pinned = measured in **15/15 blocks** (11–21 of 22 prices; v0's 684×
  median separation stands). And the set is **route-specific**: the sweep reading is not separated by the
  label (interior 1.42e-2 vs pinned 1.50e-2), because the sweep's error is a span artifact.
* **P4** the two practitioner routes **address a different object** — **MOMENTS HALF MEASURED (R640),
  VERDICT SPLIT, and the claim is ROUTE-SPECIFIC** (as P3's set turned out to be): `spike_ident_v3.py`
  finds the moments route has **two** model-free readings and they disagree. **The LEVEL reading (the
  logged mean cost `J − λ/L*`) is the SAME object, not a different one** — it tracks `c` at `r=+0.990`
  (the registration predicted `r=0`), because the envelope identity makes it `c − λ/L*` at an interior
  optimum; it is simply ~10× less accurate than the sweep (**P4's invariance clause REFUTED**). **The
  PROFILE reading (the within-chunk phase slope) is a genuinely different object** — it **anti-tracks**
  `c` (`r=−0.926`) and carries the **wrong sign on 303 of 303 cells** (80/80 interior), a **threshold-free
  direction failure**, because the periodic orbit is re-planned at each chunk boundary (U-shaped profile
  against a monotonically rising `c`). Structural certificate: every logged quantity is a function of the
  **visited point alone** (within-group price span 9.995e4 with `G` spread 1.6e-13 relative), so the sweep
  is the only route that differences *across* points. Criterion (iv): **68×** vs the profile reading;
  **10.3×** (interior) / **9.7×** (all) vs the level reading — reported as measured.
  **SYSTEM-IDENTIFICATION HALF MEASURED (R642), and it REFUTES the claim too** — `spike_ident_v4.py`
  (selftest 10/10; `spike_ident_v4_results.json` sha `8ccadaede0…`, byte-identical ×4 incl. a foreign
  cwd) reconstructs `c(d)` from the identified `(A, B, K, W)` through the truth's **own** closed form and
  tracks it at **r = 0.9993…0.99999** with a median `c`-error of **1.3 %–7.5 %** at a 1e5-step log
  (error ∝ `T^{−0.26…−0.59}`, a data floor, not a bias wall). So the route reaches the **same object**.
  **"Needs excitation a live deployment does not produce" is also REFUTED**: the deployment's own
  disturbance suffices (`cond` 10–430; only a *silent* `W=0` log breaks it), and `K` is recovered to
  1e-15. **What is real is the ACCESS cost** — a raw `(state, action, delay)` log (vs one scalar per
  price), carrying the control law that actually ran (a free action vector leaves `K` unidentified,
  err 1.04). **P4's measured content: the routes differ in ACCESS and RESOLUTION, not in a second
  object** — the sweep reads a scalar-cost log, system ID needs a raw log plus the deployed law, and both
  address the same `c(d)`.

**Registered success criteria** (unchanged from the registration): identity rate; interior MSE minimum with
slope in [0.25, 0.45]; 0 disagreements on the identifiability prediction; ≥10× median advantage over the
moments route.
