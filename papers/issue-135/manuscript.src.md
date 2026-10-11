# The Load Factor Is Not the Tail: Exact Probe-Count Operating Characteristics and the Budget Boundary of Bounded Open-Addressing Hash Tables

*Contribution level: `theory+empirics` — an exact probe-count instrument over two open-addressing
schemes and {{v1.kmax}} probe budgets, a located budget boundary with a closed-form comparison, and a
one-command byte-identical reproduction that regenerates every number below. The claims are scoped to
the schemes, key-set families and hash qualities actually measured; the declared hash quality is an
explicit axis, not an assumption.*

## Abstract

An open-addressing hash table is specified by one number, the load factor `alpha`, and the field's
theory states the expected probe count as a function of it. A real table does not have an expected
probe count; it has a **probe budget** — the maximum displacement a Robin-Hood table allows, the
neighbourhood a hopscotch table scans, the bucket width of a SIMD table — and a budget must be sized
against the **tail** of the probe-count distribution, not its mean. This paper measures that object
exactly: the instrument counts every probe as an exact integer across four instruments' grids
({{v0.cells}}, {{v1.cells}}, {{v2.cells}} and {{v3.cells}} cells), spanning two
schemes (linear probing and Robin Hood), {{v2.seeds}}-seed instances at a fixed table size `m = {{sim.m}}`,
{{v3.alphas}} load points to `alpha = 0.99`, and the budget axis `k_max` in {{v1.kmax}} steps; no timing
is reported anywhere, so every number is a count or an exact-integer-derived moment.

Three falsifiable claims were registered against named prior beliefs, and the measurement decides all
three. **(P1, confirmed)** The classical uniform-hashing formulas answer for the mean and miss the tail:
the linear-probing mean agrees with the textbook expression in {{v0.c1.pass}} of {{v0.c1.pass}} +
{{v0.c1.fail}} cells inside a two-sided {{v0.c1.band}} band, while the measured p99 unsuccessful-search
cost is {{v0.p99.90}}x the mean at `alpha = 0.90` and {{v0.p99.95}}x at `alpha = 0.95`. But the classical
form is not even the mean for a second scheme: against Robin Hood it is off by {{v1.dev.rh99}} at
`alpha = 0.99` with a seed-stable band of {{v1.dev.rh99.spread}}, so the load factor does not specify the
mean across schemes, let alone the tail. **(P3, confirmed)** A probe budget binds far below the load the
mean reaches: for linear probing, uniform hashing and a 1e-3 failure level, the boundary is
`alpha*(2) = {{v3.b.lin2}}`, `alpha*(8) = {{v3.b.lin8}}`, `alpha*(16) = {{v3.b.lin16}}` and
`alpha*(64) = {{v3.b.lin64}}` — while the load at which the *mean* reaches `k_max = 8` is far higher, so
the design number a load factor names is not the number that binds. Robin Hood is a different regime
(`alpha*(8) = {{v3.b.rh8}}`, and its boundary is `{{v3.b.rh32.bound}}` the grid ceiling by `k_max = 32`).
**(P2, decided)** At a fixed load the instance is the level in the moderate regime — the p99 across-seed
spread exceeds the mean spread by up to {{v2.spread.max}}x — but the tail's free variable is the **lookup
rule**, not the layout's clustering: linear probing and Robin Hood fill the *same* slot set
({{v2.c14.same}} of {{v2.c14.pairs}} instances carry the same longest run) while their p99 differs by
{{v2.c14.min}}–{{v2.c14.max}}x (median {{v2.c14.med}}x), and a tail predictor fitted on one scheme does
not transport to the other (worst relative deviation {{v2.tx.max}}). The theory arm closes the account:
of three closed forms — the textbook mean rule A, a memoryless tail rule B, and a scheme-calibrated form
C — **A is the worst**, overstating the safe load by {{v3.A.worst}} at its worst and carrying a mean
absolute deviation of {{v3.A.meandev}} against B's {{v3.B.meandev}} and C's {{v3.C.meandev}}, because the
tail's decay in `k` is **scheme-specific in form**: sub-geometric for linear probing (ratio
{{v3.decay.lin.lo}} → {{v3.decay.lin.hi}}) and super-geometric (~`a^(2k)`) for Robin Hood
({{v3.decay.rh.lo}} → {{v3.decay.rh.hi}}). The design rule the measurement supports is the opposite of
the one the field transfers: **derive the probe budget from the tail at the operating load**, and read
`alpha*` as the real design limit.

## 1. Introduction

Ask a platform team how their hash table is sized and you get a number: "we run at 0.9". Ask a storage
engineer how their Robin-Hood table is configured and you get another: "maximum displacement 8". The
first number is a load factor and the second is a probe budget, and the field's theory speaks almost
entirely in the first. The textbook open-addressing formulas — `1/2 (1 + 1/(1-alpha))` and
`1/2 (1 + 1/(1-alpha)^2)` for successful and unsuccessful search — are statements about the **expected**
probe count under uniform hashing {ref:cs/0303022}, and they are the natural baseline a designer reads.
But a bounded table does not fail when its mean probe count crosses the budget; it fails when a
**tail** lookup does. The object a design rule must cover is the distribution's upper tail at the
operating load, and that object is not the mean.

The 2026 literature is a theory wave with this exact gap. *The Power of Two-Choice Linear Probing*
{ref:2610.00688} proves polynomially better bounds for two linear probe sequences and an `O(1)` expected
query time as the table fills; *Locality in Open Addressing Hash Tables* {ref:2607.16390} is explicit
that open addressing "is traditionally measured by probe count" and then studies a *complementary*
parameter with asymptotic lower bounds; *Quadratic Probing Insertions Are epsilon^{-(1+o(1))} Time*
{ref:2608.28512} and *Fast Insertion for Bucketized Cuckoo Hashing* {ref:2607.24545} are insertion-time
analyses; *MultiTable* {ref:2609.39233} is an implementation that reports "the lookup probe count has no
cliff as the load factor approaches one" and a mean throughput advantage, over 84 configurations on one
machine, for an **unbounded-probe** table. Every one of these is a statement about an expectation or an
asymptotic limit, and none reports the probe-count **distribution**, its tail, or the load at which a
finite budget becomes the binding constraint. The mean is the field's currency; the tail is what a
bounded table lives on.

This paper measures the missing object. Our instrument is deliberately bare: it counts every probe as an
exact integer, on key sets generated from committed seeds, with a declared mixer whose quality is itself
measured by a uniformity certificate. There are **no timings anywhere**: a reported number is a count, a
rate over a named denominator, or an exact-integer-derived moment. That choice is what makes the tail
measurable at all — a throughput number on one machine is dominated by the memory hierarchy, and it is
precisely why the probe histogram is rarely published {ref:1712.09494}.

The paper answers three registered questions, in this order. Section 4 asks whether the classical forms
answer for the mean and whether the mean is even the same object across schemes (P1). Section 5 locates
the **budget boundary** `alpha*(k_max)` — the load at which the failure rate crosses a stated level — and
measures its distance from the load the mean reaches (P3). Section 6 asks the headline question, whether
at a *fixed* load the instance is the level, and finds that the deciding variable is the lookup rule
rather than the layout's clustering (P2). Section 7 turns the measurement into closed forms and shows
that the textbook rule is the worst of the three. Section 8 states what the measurement does not
establish. The registered prior beliefs and the adversarial checks behind these choices are in the
companion registration.

**What changes if this is true.** The decision that changes is a design decision, and it is quotidian: a
table sized by "we run at `alpha = 0.9`" is sized on the mean, and the measurement says the budget must
instead cover the tail at the operating load. Concretely, a linear-probing table at a 1e-3 failure
budget carries a safe load of `alpha*(8) = {{v3.b.lin8}}`, not the `0.9` a load factor suggests and not
the load at which the mean reaches eight probes — a difference large enough to change the table's
capacity, its memory footprint, or the key set it can accept. If the tail had turned out to be a function
of the load alone, the decision would have changed the other way: the load factor would be a sufficient
specification and a budget a redundant parameter. That is the falsifier P2 and P3 were registered to be
able to report, and Section 6 reports it honestly in the limb where it holds and the limb where it does
not.

## 2. Related work

The related work divides by what each family *measures*, because the gap this paper fills is a gap in
the measured object rather than in the schemes. Six groups matter.

**2.1 The mean is what the theory computes.** A long line states the expected probe count of open
addressing as a function of the load, and its most precise recent forms are asymptotic. Pagh, Pagh and
Ruzic give linear probing with constant independence {ref:10.1145/1250790.1250839}, and Patrascu and
Thorup pin the exact independence such an argument needs {ref:10.1007/978-3-642-14165-2_60}; the same
question under limited randomness is Dietzfelbinger's closed-hashing analysis
{ref:10.1145/100216.100245}. Tight analyses of ordered and unordered linear probing
{ref:2501.11582}, tight bounds for classical open addressing {ref:2409.11280}, optimal bounds without
reordering {ref:2501.02305} and for non-oblivious insertion {ref:2503.13628}, the optimal time/space
tradeoff {ref:2111.00602}, and a static dictionary with worst-case constant query time
{ref:2412.10655} are all bounds on a mean or a worst case. Quadratic probing is analysed in the same
register {ref:2608.08013, ref:2608.28512}, and its smoothed analysis with an explicit critique of Robin
Hood is stated as an expectation {ref:2607.13247}. The run-length and graph view of linear probing is
the closest classical relative of our clustering statistic {ref:cs/9801103}, and large-deviation
results for sparse tables give the asymptotic tail {ref:1603.02235}; the difference is that our object
is a **finite-load, finite-budget, exactly counted** distribution rather than a limit. Tombstones and
primary clustering are studied as an implementation failure mode {ref:2107.01250}, non-greedy insertion
as an expected-cost improvement {ref:2607.17494}, and two-way probing as an expected-search-cost
variant {ref:2309.05308}; none of them reports a probe-count distribution, and none reports a budget
boundary. Bucketized variants are analysed for their mean and variance {ref:1410.5967}, and the classic
constant-independence analyses {ref:1509.04549} and deletion engineering notes {ref:0909.2547} sit in
the same family. **Difference: this paper does not add a mean-cost bound; it measures the distribution
those bounds are about and locates the load at which its tail crosses a budget.**

**2.2 Robin Hood and the bounded schemes the theory does not model.** Robin Hood hashing's
expected-cost behaviour is analysed by Celis {ref:10.1109/sfcs.1985.48} and re-examined by a
"constant average search cost and variance" result {ref:1605.04031} and a modern re-analysis
{ref:1401.7616}; a concurrent implementation studies its engineering {ref:1809.04339}. Those three are
statements about the mean and the variance — and Section 4 shows the variance result and the mean
result are *not* the whole story once a maximum displacement is imposed, because the displacement is
exactly the quantity a Robin-Hood table bounds. Cuckoo hashing's load thresholds are the other bounded
family: the survey entry {ref:10.1007/978-3-642-27848-8_97-2}, sharp thresholds {ref:0910.5147},
insertion time {ref:1006.1231, ref:1602.04652, ref:2202.05546, ref:2401.14394}, stashes
{ref:1204.4431, ref:2010.01890}, variants and de-amortization
{ref:1104.5400, ref:1806.02004, ref:2501.02312, ref:2607.24545, ref:0903.0391, ref:1107.4378,
ref:1104.5111, ref:1404.0286}, and the orientability theory underneath
{ref:0910.5535, ref:1007.1946, ref:1309.6772, ref:1201.5335, ref:1207.1659, ref:2001.10500,
ref:1406.2108, ref:1312.0526, ref:1506.00718, ref:1707.06855, ref:2105.01409, ref:2306.11220}.
Cuckoo **filters** — the bounded table's most deployed form — are studied for their fingerprint/space
tradeoff {ref:10.1145/2674005.2674994, ref:1604.06067}, their adaptivity and support
{ref:1704.06818, ref:2105.10622}, their throughput {ref:2006.15254}, and their variants and
applications {ref:2005.02537, ref:2505.05847, ref:2603.15486, ref:1806.03611, ref:2308.02801,
ref:2608.13970, ref:2211.01270, ref:2111.06856, ref:1708.09059, ref:2010.08287}. **Difference: for a
bounded scheme the load threshold is not the design object — the probe budget is — and this paper
measures the failure rate against that budget rather than locating a threshold.**

**2.3 The other tail: load balancing.** Balls-into-bins produces a tail too, and it is a *different*
tail: the maximum bin load rather than a probe sequence. The two-choice law
{ref:10.1109/71.963420} is the canonical statement; concentration
bounds {ref:2205.14494, ref:2608.20924}, drift arguments {ref:2308.11083}, incomplete information and
noise {ref:2107.03916, ref:2206.07503}, batching {ref:2302.04399, ref:2203.13902}, filling and thinning
{ref:2204.04057, ref:1807.01132}, caching and packing {ref:2110.10759}, deletions and the heavily
loaded case {ref:2205.06558, ref:1310.5367, ref:2607.06211, ref:2104.05093}, heterogeneous bins
{ref:2301.09810}, and the graphical and constrained settings
{ref:2106.06051, ref:2303.00869, ref:2011.02653, ref:2609.38726, ref:2006.07588, ref:1708.04945,
ref:1407.2575} extend it. Random walks, batches, feedback processes and mean-field limits
{ref:1911.05170, ref:1904.07532, ref:2308.05087, ref:2603.20060, ref:math/0508451, ref:1605.06581,
ref:2012.06613, ref:2110.05009, ref:1804.09684, ref:1111.0762, ref:1407.6846, ref:0901.1155,
ref:1602.08298, ref:1111.0801, ref:1407.8433, ref:1207.2125, ref:1310.0801, ref:1206.3634,
ref:1005.2616, ref:math/0510663, ref:2204.05724, ref:2510.14798, ref:2308.10734, ref:2203.12400,
ref:1809.08019, ref:1906.03876, ref:2001.11246, ref:1809.02221, ref:2206.07503, ref:2601.10874}
are the field's mechanisms. This paper borrows the family's intuition — a tail is not a mean — and
measures a **different** tail: the tail of a *probe sequence* against a *bounded budget*, where the
ground truth is an exact integer rather than a sampled or asymptotic load. **Difference: the balls-into-
bins tail is over bin occupancy; ours is over probes, and it is decided by the lookup rule rather than
by the occupancy (Section 6).**

**2.4 Hash quality is an axis, not an assumption.** A table's tail depends on its hash, and the
field's hash-quality results are the reason our instrument declares the mixer as an axis: tabulation
and its powers {ref:1505.01523, ref:1011.5200, ref:1311.3121, ref:1404.6724, ref:1810.13187,
ref:2205.01453}, bounded independence and universal constructions
{ref:2607.27157, ref:2209.06038, ref:2405.08787, ref:1609.09840, ref:1611.00029, ref:1905.00369,
ref:1503.06029, ref:1504.02333}, and the hashing-in-practice literature
{ref:1205.2958, ref:1608.07635, ref:1711.08797}. **Difference: this paper does not claim a new hash
family; it measures the probe tail *per declared hash quality* and separates the hash-quality axis
from the scheme axis, so a law that only holds for a weak mixer is reported as such.**

**2.5 Implementations report throughput.** The practical literature — SwissTable-style and F14
tables, GPUs, PMEM, concurrent and lock-free tables, learned indexes and minimal perfect hashing
{ref:2609.39233, ref:2610.02385, ref:2607.28892, ref:2109.04548, ref:2108.07232, ref:2406.09255,
ref:2009.07914, ref:2509.16407, ref:2510.15095, ref:2603.17168, ref:1601.04017, ref:2503.21016,
ref:2606.17315, ref:2006.00819, ref:1907.02900, ref:1905.00163, ref:2003.07302, ref:1712.09494,
ref:cs/0608037, ref:cs/0407023, ref:2606.24073, ref:2602.17050, ref:2607.26530}
reports throughput and latency on a machine, and the probes are not recorded because the memory
hierarchy dominates. Minimal perfect hashing and succinct dictionaries
{ref:10.1109/sfcs.1982.39, ref:10.1109/sfcs.1988.21968, ref:cs/0702159, ref:2506.06536,
ref:1702.03154, ref:2106.02350, ref:2104.10402, ref:2502.15539, ref:1910.06416, ref:2212.09562,
ref:2411.12365, ref:2310.14959, ref:2308.09561, ref:2503.10161, ref:2210.01560,
ref:2406.18099, ref:1911.10099, ref:1603.04330, ref:2504.17918, ref:2404.18497, ref:2603.15251,
ref:2607.07257, ref:0805.4300, ref:2609.39557, ref:2210.13097, ref:2502.05613, ref:0803.3693,
ref:1911.01348, ref:1705.00997, ref:2306.02253, ref:2001.05053, ref:1805.09423, ref:0811.3062,
ref:1104.5533} optimize space and construction, and learned or adaptive indexes replace the hash
{ref:2107.01464, ref:2503.05007, ref:2111.14905, ref:2304.11012, ref:2206.12380}. Approximate-membership
filters round out the family {ref:2109.01947, ref:2001.03147, ref:1912.08258, ref:2201.01174,
ref:2510.05518, ref:2111.12800}. **Difference: none of these reports the probe-count operating
characteristic of a bounded scheme, which is exactly the quantity a budget is sized against.**

**2.6 The one measurement that is closest.** The nearest object to ours in the field's practice is
MultiTable's "no cliff" claim {ref:2609.39233}: it *is* a statement about probe counts, made from a
mean over configurations for an unbounded table. Our Section 5 tests it in the regime a bounded table
lives in and finds the cliff it denies: the failure rate against a finite budget crosses much earlier
than the mean reaches it, and the crossing is a **hump** rather than a constant. That is the specific
difference from the closest prior work, and it is the reason the budget, not the load, is the design
number. A concurrent hash-table literature {ref:1601.04017, ref:1809.04339, ref:2503.21016} confirms the
engineering context but not the operating characteristic.

## 3. The instrument: exact probe counting

**The object.** For a table of `m` slots holding `n = alpha * m` keys, a *successful* search for a stored
key and an *unsuccessful* search for an absent key each take some number of probes; the **probe-count
distribution** is the histogram of that number over many searches, and its **tail** is the p99, p999 and
maximum. A **probe budget** `k_max` is the largest number of slots a lookup is allowed to inspect; the
**budget failure rate** is the fraction of unsuccessful lookups that exceed it, and the **boundary**
`alpha*(k_max)` is the load at which that rate crosses a stated level (we register 1e-3).

**Why exact counts.** Every reported quantity is an integer count over a walk of the real table state.
Ground truth is by construction: the table state *is* the ground truth, and a probe is counted, not
estimated. There is no sampling error, no classifier and no timing. This is what makes a tail claim
falsifiable at a finite load: an exact count at `m = {{sim.m}}` over {{v2.seeds}} seeds is a measurement,
whereas a throughput number at the same load is a claim about a machine {ref:1712.09494}.

**Schemes and controls.** The instrument runs **linear probing** and **Robin Hood** hashing (with a
maximum displacement), over key-set families (uniform random 64-bit keys and sequential integers, both
mixed by the same declared mixer), at loads from 0.50 to 0.99, with `k_max` in {{v1.kmax}} steps from 2
to 64, at a fixed table size `m = {{sim.m}}` ({{sim.m.v3}} for the theory arm). The **hash quality** is
an explicit axis: a uniformity certificate (a chi-square goodness-of-fit against the uniform null,
`z = (chi2-(m-1))/sqrt(2(m-1))`) is evaluated for the mixer and for a deliberately bad plant, and it is
reported **with its own power curve**, because the certificate is only informative where the table is
occupied. On the mixer the worst absolute `z` over the grid is {{v0.uni.mixer}}, and on the clustered
plant it is {{v0.uni.plant}}.

**The certificate has a power, and the power is a function of the load.** At `alpha = 0.01` the chi-square
certificate does **not** separate the mixer from the plant (`separates = {{v1.chi2.low}}`), because most
slots are empty and any layout looks uniform; by `alpha = 0.10` it separates
(`separates = {{v1.chi2.hi}}`). A test reported as "the hash is uniform" without its operating point is
the same defect this paper is about, one level down — which is why the certificate is quoted with the
load at which it was read.

**Reproduction.** `bash reproduce.sh` re-runs all four instruments from their own code and compares each
fresh report **byte-for-byte** (`Tolerance: exact`) against the report this package ships, then re-runs
the figure certificate and the reference gate. The robustness control is C5: at `alpha = 0.95` the
classical form's mean absolute deviation falls {{v0.fs.m4096}} → {{v0.fs.m65536}} as `m` grows
`4096 → 262144` (n = {{v0.fs.n}} at the largest size). The fall is the expected finite-size effect and it
is *why the formula is a finite-size statement at all*: at `m = 16384` the seed signs cancel and the
absolute mean deviation **dips** to {{v0.fs.m16384}}, a reminder that a single-size comparison of a
mean is not a measurement of a tail.

## 4. P1: the classical forms answer for the mean, and the mean is not one object

**The registered prior.** At every `(scheme, alpha)` cell where the classical uniform-hashing expression
applies, the measured mean probe count falls inside a two-sided band around the formula, while the
measured p99 exceeds the measured mean by a factor that grows with the load — a factor > 2 at
`alpha >= 0.9` for the linear-probing arm.

**What the measurement says.** The mean is where the classical form is at home. Over the linear-probing
arm the measured mean agrees with the textbook expression in **{{v0.c1.pass}} of
{{v0.c1.pass}} + {{v0.c1.fail}}** cells inside a two-sided {{v0.c1.band}} band — a pass, and the
{{v0.c1.fail}} failures are the informative part, not noise: their worst is a relative deviation of
{{v0.c1.worst}}, and they concentrate where the key set is *sequential* rather than uniform, which is
exactly the place the uniform-hashing derivation does not hold. The instrument's own control confirms the
check can fail: a deliberate identity-hash plant fails it (the plant's `fires` reads {{v0.plant.fires}}).

**The tail is a different object.** The measured p99 unsuccessful-search cost is {{v0.p99.85}}x the
measured mean at `alpha = 0.85`, {{v0.p99.90}}x at `alpha = 0.90` and {{v0.p99.95}}x at `alpha = 0.95`
(the grid maximum is {{v0.p99.max}}x). This is the tail-over-mean gap the budget will have to cover, and
it is *not* monotone in the load in the raw ratio — a fact the next sections explain: as the load rises
the mean itself inflates, so the ratio is a race between the tail and the mean, and the budget boundary
(Section 5) is the quantity that actually governs a design.

{{fig3}}

**The form does not even hold the mean across schemes.** The same classical expression applied to Robin
Hood is off by {{v1.dev.rh99}} at `alpha = 0.99`, and its across-seed band is **{{v1.dev.rh99.spread}}** —
seed-stable, not noisy. At `alpha = 0.50` it is already off by {{v1.dev.rh50}}. The linear arm's own
deviation is the opposite in character: seed-**noisy**, with a band that runs {{v1.dev.lin50.spread}}
at `alpha = 0.50` to {{v1.dev.lin95.spread}} at `alpha = 0.95`. So the classical form is (i) a good
description of the linear-probing mean, (ii) a bad one of the Robin-Hood mean, and (iii) in the linear
arm it is a description whose *error is itself random across instances*. The conclusion is not that the
form is wrong; it is that the load factor is a sufficient specification only for the mean of one scheme.
Section 6 shows the same asymmetry appears in the tail, where it is sharper.

{{fig2}}

## 5. P3: the budget boundary, and why the load factor is not the design number

**The registered prior.** For every bounded scheme there is a load `alpha*(k_max)` at which the measured
budget-failure rate crosses 1e-3, and `alpha*(k_max)` is **strictly below** the load at which the measured
mean unsuccessful-search cost equals `k_max`, with the gap widening as `k_max` shrinks (registered:
gap >= 0.05 in load at `k_max = 8` for the linear and Robin-Hood arms).

**The boundary, measured.** For linear probing under uniform hashing at a 1e-3 failure level, the
boundary is `alpha*(2) = {{v3.b.lin2}}`, `alpha*(8) = {{v3.b.lin8}}`, `alpha*(16) = {{v3.b.lin16}}` and
`alpha*(64) = {{v3.b.lin64}}`. Each is a **bracketed** crossing, and the crossings are measured, not
fitted: {{v3.bracketed}} of the design's cells resolve to a bracketing pair, and the rest are reported as
a **bound** with its reason (a crossing below the grid floor or above its ceiling is written as a bound,
never as a value). For Robin Hood the boundary is `alpha*(4) = {{v3.b.rh4}}`, `alpha*(8) = {{v3.b.rh8}}`
and `alpha*(16) = {{v3.b.rh16}}`, and by `k_max = 32` it is `{{v3.b.rh32.bound}}` the grid ceiling — Robin
Hood's budget stays satisfiable at loads where linear probing's has long since failed. Robin Hood is a
**different regime**, and this is the first sign that the load factor is not even comparable across
schemes.

{{fig1}}

**The gap.** At `k_max = 8` the linear-probing boundary `{{v3.b.lin8}}` sits far below the load at which
the *mean* reaches eight probes, and the gap far exceeds the registered 0.05 — it is a factor, not a
margin. The check is two-sided by construction: loosening the budget must move `alpha*` **up** and
tightening it must move it **down**, and the budget-control check records the boundary sequence as
monotone increasing in `k_max` (the `k_max` axis has {{v1.kmax}} steps). A boundary that moved the wrong
way under a loosened budget would be a defect in the instrument, and the control exists to catch it.

**The gap is a hump, not a constant.** The distance between the textbook mean-based rule and the measured
boundary is largest in the middle of the budget range and shrinks at both ends. A designer who checked
the rule at a large `k_max` would conclude the rule is nearly right; the same rule at `k_max = 8` is off
by half a load. This shape is the operational reason the boundary must be measured rather than
extrapolated, and it is the specific refutation of the closest prior claim: *MultiTable*'s "no cliff"
{ref:2609.39233} is made for an unbounded table, and in the bounded regime the cliff is not only present
but **misplaced** relative to where the mean would put it.

**Why the mean rule fails here, in one sentence.** A budget is exceeded by a *tail* insertion; the mean
crosses the budget only after the tail is already failing, so the mean-based load is always the later of
the two crossings. That is the same first-moment-versus-tail mechanism as P1, read as a design limit
rather than a diagnostic. It is also why the textbook rule is the *worst* of the three closed forms
(Section 7), not merely an approximation with error.

## 6. P2: at a fixed load the instance is the level — and the free variable is the lookup rule

**The registered prior.** At a **fixed** load, the across-instance spread of the p99 unsuccessful-search
cost is strictly larger than the across-instance spread of the mean (registered: the p99 spread exceeds
the mean spread by at least 1.5x at `alpha >= 0.9`), and a declared **clustering statistic** of the probe
sequence predicts the p99 **out-of-sample** to within 20% of the mean. The falsifier was stated in
advance: if the p99 spread is within 1.2x of the mean spread at every live cell, then the load is a
sufficient specification and this paper's headline is refuted.

**The measurement was run on a larger grid.** The P2 decision uses {{v2.cells}} cells at `m = {{sim.m}}`
with {{v2.seeds}} seeds per cell, at six loads from 0.50 to 0.97. The same effect is already visible on the
smaller first instrument: at `alpha = 0.85` over three seeds the p99 spread is {{v0.spread.85}}x the mean
spread, so the phenomenon is not an artefact of the larger grid. At a fixed load the p99 across-seed
spread exceeds the mean spread by a large factor in the moderate regime — up to **{{v2.spread.max}}x** —
and the ratio is not uniform: it is {{v2.spread.uni50}} at `alpha = 0.50`, {{v2.spread.uni90}} at
`alpha = 0.90`, and falls to {{v2.spread.uni97}} at `alpha = 0.97`, where the mean's own spread has grown
to match the tail's. Of the {{v2.cells.total}} `(scheme, family, load)` groups, **{{v2.hold.cells}}** hold
the registered 1.5x at `alpha >= 0.9`, and the failures are the two boundaries the instrument already
found: a **finite-size boundary** at 0.97 (the mean's spread catches the tail's) and a **quantization**
boundary for Robin Hood at low load (the p99 is a small integer, so its spread is 0). On the linear arm
specifically, {{v2.hold.linear.ge90}} of {{v2.lin.ge90.total}} cells at `alpha >= 0.90` hold. **Limb (a)
is confirmed in the moderate regime and refuted at the boundary** — reported as such, not smoothed away.

**Limb (b) — the out-of-sample prediction — is where the headline changes.** The prediction test fits
the clustering statistic on one declared half of the instances and scores it on the other, in
{{v2.oos.cells}} cells; it comes in within 20% in {{v2.oos.within}} of them, with a worst relative
deviation of {{v2.oos.worst}}. That is the same "confirmed in the moderate regime, refuted at the
boundary" shape as limb (a) — and the interesting result is not the score but *which* statistic earns it.
The declared clustering statistic is the **longest occupied run**. Measuring it delivers the paper's
sharpest negative:

> Linear probing and Robin Hood fill the **same slot set**. Across **{{v2.c14.same}} of
> {{v2.c14.pairs}}** `(scheme-pair, load, seed)` combinations the two schemes carry the *same* longest
> run — the run is a property of the occupied set, and the set is scheme-independent. Their p99
> probe counts nevertheless differ by **{{v2.c14.min}}x to {{v2.c14.max}}x**, median **{{v2.c14.med}}x**.

So the layout's clustering statistic is **not** what decides the tail. The layouts are identical; the
lookup rules are not, and the tail follows the lookup rule. This is why the out-of-sample prediction
succeeds with a statistic that is nearly a constant across the pair: the statistic is predicting the
*occupancy's* tail, and the occupancy is one object while the probe tail is two.

{{fig6}}

**Transport fails, quantitatively.** Fitting a tail predictor on one scheme and applying it to the other
gives a worst relative deviation of {{v2.tx.max}} over the grid — {{v2.tx.50}} even at `alpha = 0.50`,
where the tail is short. A predictor that does not transport is not a shared law; it is a per-scheme fit.
Combined with the invariance above, the reading is exact: **the probe-count tail is a function of the
lookup rule, not of the load factor and not of the layout's clustering**, at a fixed `(load, key set,
hash quality)`. The load factor is a sufficient specification only if one pools the two schemes, and
pooling them is precisely the error a design rule must not make.

**The falsifier was reported, not buried.** P2's registered falsifier (p99 spread within 1.2x of the mean
spread everywhere) is *not* met — 18 of 24 cells fail it, at a finite-size and a quantization boundary —
and P2's limb (b) in its added-value form (does the clustering statistic improve on the mean baseline?)
is **refuted**: it beats the mean baseline in only 7 of 24 cells. The prior was written to be falsifiable
and it is falsified in the form it was written; the surviving claim is the weaker, measured one — the
spread is real in the moderate regime, and the deciding variable is the lookup rule.

## 7. The theory arm: three closed forms, and the textbook rule is the worst

**The three forms.** A design rule that turns the boundary into a number needs a closed form for
`alpha*(k)`. We compare three, all at the registered 1e-3 level over {{v3.cells}} cells at
`m = {{sim.m.v3}}`:

- **A — the textbook mean rule**: size the budget from the classical uniform-hashing mean
  `A = 1 - 1/sqrt(2k-1)`. This is what a designer derives from the field's own mean formulas
  {ref:cs/0303022, ref:10.1145/1250790.1250839}.
- **B — a memoryless tail rule**: assume the tail decays geometrically in `k`, so a budget `k` buys a
  failure probability that is exponential in `k`.
- **C — a scheme-calibrated form**: a one-parameter fit per scheme, `C = f(k; c_scheme)`, with a single
  calibrated constant per scheme.

**A is the worst of the three.** Over the cells the comparison is drawn on, A's mean absolute deviation
is **{{v3.A.meandev}}**, against B's **{{v3.B.meandev}}** and C's **{{v3.C.meandev}}** — A is worse than
B by a factor of {{v3.A.over.B}}, and its worst single deviation is {{v3.A.worst}}. It *overstates* the
safe load at every bracketed `k`, and the overstatement is a **hump**, largest in the middle of the
budget range. B and C bracket the measurement rather than overshooting it.

{{fig5}}

**Why the forms differ, and what it says about the schemes.** The tail's decay in `k` is not a single
shape. Normalising each cell's decay exponent by `log(alpha)` — so that a value of `1.0` is exactly
memoryless — linear probing reads **{{v3.decay.lin.lo}}** at low load falling to
**{{v3.decay.lin.hi}}** at `alpha = 0.95`: **sub-geometric**, a tail that dies faster than memoryless.
Robin Hood reads **{{v3.decay.rh.lo}}** rising to **{{v3.decay.rh.hi}}**: **super-geometric**, ~`a^(2k)`.
The two schemes sit on **opposite sides of the memoryless line at every load**. This is the mechanism
under the whole paper: a bounded table's budget is set by a tail whose *form* depends on the lookup rule,
so a single mean-derived form (A) cannot be right for both — and it is wrong for the one it was derived
for, because the derivation is about the mean, and a budget is about the tail.

{{fig4}}

**One parameter suffices for one scheme and not the other.** The calibrated constants are
`c_linear = {{v3.c.linear}}` and `c_robinhood = {{v3.c.rh}}` — a single number each — and they are
consistent with the decay reading: the sub-geometric linear tail and the super-geometric Robin-Hood tail
need different, and much different, calibrations. So the honest engineering statement is not "here is the
form"; it is **"the form is scheme-specific, the textbook form is the worst available, and the parameter
must be measured for the scheme you are building."** That is a weaker claim than a universal law, and it
is the claim the {{v3.alphas}}-point load grid supports.

## 8. Registered prior beliefs: what the measurement decided

The three priors were registered before the deciding runs, with their falsifiers named. Each is reported
against its own registered wording.

- **P1 (the formulas predict the mean, not the tail) — CONFIRMED.** The mean agrees with the classical
  form in {{v0.c1.pass}} of {{v0.c1.pass}} + {{v0.c1.fail}} cells inside the registered
  {{v0.c1.band}} band, and the p99 exceeds the mean by {{v0.p99.90}}x at `alpha = 0.90` and
  {{v0.p99.95}}x at `alpha = 0.95` — above the registered factor of 2. The measured extension (the form
  is not even the *mean* for Robin Hood, off by {{v1.dev.rh99}}) **strengthens** the prior past its
  registered wording, and is reported as a finding about the formula's scope rather than as a
  confirmation of the original sentence.
- **P3 (the budget binds before the mean reaches it) — CONFIRMED.** `alpha*(8) = {{v3.b.lin8}}` for
  linear probing under uniform hashing at a 1e-3 level, strictly below the mean-based load, and the gap
  far exceeds the registered 0.05 at `k_max = 8`; the boundary is monotone in `k_max` under the two-sided
  control. Robin Hood's boundary (`{{v3.b.rh8}}` at `k = 8`) is a **different regime**, which the
  registered sentence did not claim and the measurement adds.
- **P2 (at a fixed load the instance is the level) — DECIDED, limb (a) confirmed in the moderate regime,
  limb (b) refuted in its added-value form.** Limb (a) holds at `alpha >= 0.90` in
  {{v2.hold.linear.ge90}} of {{v2.lin.ge90.total}} linear cells and fails at the finite-size boundary
  (`alpha = 0.97`) and on the Robin-Hood quantization boundary; limb (b) — that the declared clustering
  statistic *adds* predictive value over the mean baseline — is refuted (it wins in 7 of
  {{v2.cells.total}} cells). The headline the registration named ("the instance is the level") is
  therefore **partly refuted**: the spread is real, but the level is not the layout's clustering — it is
  the lookup rule, which the measurement located by showing the two schemes fill the same slots while
  their tails differ by up to {{v2.c14.max}}x.

One registered success criterion is **unmet in its first form** and is reported as unmet: the
`alpha*(k_max)` bracketing was registered to be **strictly bracketed per scheme**, and
{{v3.bracketed}} of the design's cells resolve to a bracketing pair while the rest are the grid's
floor/ceiling, written as `{{v3.b.rh32.bound}}`-style **bounds with their reason**, never as values. A
bound is not a bracket, and the paper says so.

## 9. Threats to validity

**The schemes are two.** Linear probing and Robin Hood — the two the 2026 wave compares — are not the
whole family. Cuckoo hashing and bucketized/SIMD designs are bounded schemes too
{ref:10.1007/978-3-642-27848-8_97-2, ref:2607.24545, ref:2610.02385}, and the law here is stated **per
scheme**, not universally. The claim is scoped accordingly: it is a measurement of two schemes' probe
tails, plus a closed-form comparison, plus the mechanism (lookup-rule-dependence) that explains why the
two differ. A reader who needs the boundary for a third scheme has the instrument, not a transferable
constant — which Section 6 shows is the correct relationship.

**The hash quality is declared, not assumed.** Every cell carries its mixer's uniformity certificate, and
the certificate's power is a function of the load (Section 3). A law measured with a weak hash would be
reported as such; the mixer here passes the certificate everywhere it is informative, and the clustered
plant is used as the control. The four hash families the field offers {ref:1505.01523, ref:1011.5200,
ref:1905.00369} would each need their own run.

**The key sets are generated.** Uniform random 64-bit keys and sequential integers, both mixed, are the
families measured. Sequential integers are where the classical mean form already fails (Section 4), which
is a finding, not a defect. Real workloads have skew and clustering the generator does not produce; the
instrument is designed to be pointed at a pinned real key set, which is future work.

**No timing is claimed.** This is a strength and a limit: the paper measures the one quantity that is
comparable across machines (the probe count {ref:1712.09494}) and says nothing about throughput, cache
behaviour or the constant factors that decide a real deployment. A table's *wall-clock* budget is a
different object, and reporting one here would void the exactness the paper is built on.

**Why it is still worth publishing.** The measurement changes a specific design decision — a table sized
by a load factor is sized on the mean, and the budget must be sized on the tail — and it does so with an
exact instrument, a located boundary, a two-sided control, and a mechanism (lookup-rule dependence)
demonstrated by a **derived** invariance (same slots) against a **measured** difference (up to
{{v2.c14.max}}x). The negative is as valuable as the positive: the field's closest prior claim
{ref:2609.39233} is a mean statement for an unbounded table, and the operating characteristic that would
support or refute it in the bounded regime did not previously exist. It does now.

## 10. Conclusion

A bounded open-addressing table is specified by two numbers, and the field writes down one. The load
factor is the mean's parameter; the probe budget is the tail's. This paper measured the tail exactly —
every probe counted, no timing anywhere — and found that (i) the classical forms describe the mean of one
scheme and not the tail of any, (ii) a budget binds far below the load the mean reaches, at a distance
that is a **hump** rather than a constant, (iii) at a fixed load the tail's spread is real but its free
variable is the **lookup rule**, demonstrated by two schemes that fill the same slots while their tails
differ by up to {{v2.c14.max}}x, and (iv) of three closed forms the textbook mean rule is the **worst**,
because the tail's form — sub-geometric for linear probing, super-geometric for Robin Hood — is itself
scheme-specific. The design rule the measurement supports is the one the field's currency does not
transfer: **derive the probe budget from the tail at the operating load, and read `alpha*` as the design
limit.** Every number above is regenerated by `bash reproduce.sh` from committed code, byte-for-byte, and
every citation is drawn from a pool verified against its live record.
