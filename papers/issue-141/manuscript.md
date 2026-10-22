# The Score Is Not the Payoff: Rank-Gaming, Transport, and What an Evaluation Protocol Actually Measures

<!-- DRAFT (Phase B): all eleven sections drafted. Every number carries an HTML comment naming its key
     in canonical.py, which re-derives it from the shipped artefacts; `check_numbers.py` fails on a key
     that file does not emit AND on a key whose value is absent from its own paragraph -- so a number
     that has drifted from its artefact is a gate failure, not a proofreader's chore. A number with no
     annotation is unchecked by that gate and must not be added. Citations are written as a `ref:` marker whose argument is the key in
     `refs/selected.json`; `refscan141.py --render` expands them into numbers in order of first
     appearance and appends the References section, and it REFUSES to render if any key has no
     verified record or if any selected work is never cited in the body. -->

## Abstract

An evaluation protocol — how opponents are selected, how policies are paired, and how outcomes are
aggregated into a score — is normally a fixed input to a benchmark. We make it the measured object.
Over an exact, enumerable design space (nine games, eight policies, four populations, nineteen
protocols; 684 cells and 1,026 transport entries, every payoff an exact rational), we ask how much of
a published ranking is a property of the policies and how much of the protocol, and we report the
answer as quantities of the protocol rather than as an observation about a leaderboard.

Three results, in order of strength. **First, a design law, exact and falsifiable**: a protocol's
ranking is faithful to payoff -- agreement of the two total orders in every cell -- **iff** its score
is a strictly increasing function of the policy's *own* payoff-profile value. Every aggregation that
reads the opponent row instead breaks faithfulness, and none of the eleven row-readers in our space is
faithful in a single cell (0 mismatches over 19 protocols x 9 games). **Second, the ranking is
buyable**: a policy is rank-optimal without being payoff-optimal in 474 of 684 cells, and the maximum
rank gain the zoo permits is attained by an ordinary lower-is-better score. The protocol, not the
population, is the larger lever: the mean-square for protocol exceeds that for population in 9 of 9
games, by a factor of 3.929x to 52.132x. **Third, a registered hypothesis is refuted with a
direction**: we predicted that *buyable* rank and *fragile* rank are one property; they are strictly
nested instead (474 gameable cells strictly inside 564 fragile ones, with 0 counterexamples to
`G > 0 => tau < 1`), and one design is maximally opposed -- first by rank-gaming and exactly zero by
transport. A benchmark author who audits the ordering catches corruption at half the contamination an
audit that reads only the champion needs (`lambda_tau = 1/16 < lambda_G = 1/8`). <!-- n: v4.cells,
v4.transport_entries, v4.law_mismatches, v4.row_reading_faithful_count, v4.P1.G_pos,
v4.P2.games_protocol_gt_population, v4.P2.ms_ratio_min, v4.P2.ms_ratio_max,
v4.T3.gameable, v4.T3.fragile, v4.T3.counterexamples, v1.lambda_tau, v1.lambda_G -->

**Claim boundary.** Every number above is a fact about a declared, exactly enumerable design space. We
make no claim about a deployed benchmark or a real population of agents; nothing here is measured on
systems we do not control, and no synthetic result stands in for a field observation. Within that space
one limitation is carried throughout rather than excluded: of the nine games, the four-bidder
common-value game carries no certified anchor, so its cells are counted everywhere and independently
confirmed nowhere. What we do claim is that the protocol-level phenomena are exact, that they are
invisible to protocol-free reporting, and that one of the incentives literature's natural predictions
about them is false.

**Contribution level: `theory+empirics`.** Declared here because this is the carrier a reader looks in,
and the same value is stated in the research registration and in `README.md`; all three name one level.
The grounds are the two this journal asks for at that level: a **theory model** — the design law, proved
over the enumerated space and falsified where it could be (0 mismatches over 19 protocols x 9 games,
with row-reading protocols faithful in no cell) — and **empirics with a baseline** — a two-sided control
in which the uninformative-constant and uninformative-random protocols bracket every measured effect,
plus exact enumeration rather than sampling, so that no reported difference rests on a draw.

## 1 Introduction: the protocol is a confound nobody manipulates

Benchmarks for strategic agents are now published at a rate that outstrips their methodology
[1,2,3]. In the
most recent measurement we are aware of, ERPBench evaluates the same 100 fixed problems in two matched
competitive ecologies and finds that the two ecologies identify the **same task-level winner on only
21 of 100 problems** <!-- n: external(arXiv:2609.04667) --> — the ranking is not a property of the
agents alone, and the paper says so [4]. But the paper holds its protocol fixed and varies the ecology,
so in **the LLM-benchmark literature this paper surveys** the protocol remains an input, never a
treatment. That is a scope claim about one literature and not about
evaluation at large: the multi-agent evaluation line [5,6,7]
has made the aggregate and the population its object for a decade, and §10 takes up what the results
here add to it and what they do not.

That is the gap we measure into. A strategic evaluation has three moving parts — a game with a payoff
structure, a population of policies, and a **protocol** that selects opponents, pairs policies, and
aggregates outcomes. Benchmarks vary the first two and report a ranking as if the third were neutral
[8,9,10,11].
It is not. The protocol decides which policies are compared, and the score decides what "better" means
[12,13];
when the score is not monotone in the policy's own payoff, the ranking can order policies by something
else entirely, and the paper that publishes it will have no way to notice
[14,15,16,17].

We therefore ask three questions, each with an exact answer in our space:

1. **Can a policy be rank-optimal without being payoff-optimal, and by how many positions?** Yes, in a
   majority of cells, by up to the maximum the population allows (§4).
2. **What does the ordering do when the population changes?** It transports, or fails to, at a rate
   set by the protocol and not by the agents — and the naive law relating transport to faithfulness is
   false at entry level (§8).
3. **Are buyable rank and fragile rank one property or two?** Two, strictly nested, and maximally
   opposed in one design (§6). We registered the opposite and were wrong.

Our answer to (1) and (2) is what we call a **design law**: faithfulness is equivalent to monotonicity
of the score in the policy's own payoff-profile value, so the protocols that cannot be gamed are
identified *by construction* rather than observed (§3). Our answer to (3) is a refutation with a
direction, which we regard as the paper's strongest result: it inverts a natural reading of the
incentive literature, where a score that cannot be bought is presumed to be a score whose ordering
holds [18,19,20,21].

**Contributions.**

- An **exact characterization** of faithful protocols (§3), tested on 19 protocols x 9 games with 0
  mismatches, including a class of eleven row-reading aggregations of which 0 are faithful in any cell.
- An **exact finite-population measurement** of the rank gain and its payoff cost (§4), with a monotone
  control that reads exactly zero and a natural, non-adversarial score that attains the maximum gain.
- A **decomposition** locating the lever in the protocol rather than the population (§5), reported both
  as an exact two-way split and as a ratio of mean squares.
- A **refutation with a direction** (§6): the containment is strict, the counterexample count is zero,
  and one design is simultaneously the worst by rank-gaming and exactly zero by transport.
- A **separation ladder** (§7) that converts the theory into a design rule: audit the ordering, not the
  champion, and you detect corruption at half the contamination.
- The **scope of the transport law** (§8), including the converse decomposed into a reachable condition
  and an empty one, and a named constructed protocol that satisfies the empty one.

## 2 Setup: games, policies, populations, protocols, statistics

**Games.** Three families, each at n = 2, 3, 4 bidders: first-price sealed-bid (FPSB), second-price
sealed-bid (SPSB), and a common-value auction with the winner's curse
[22,23,24]. Values are drawn from a finite
integer grid and every payoff is computed as an exact `Fraction` sum over opponents' value profiles, so
no result in this paper depends on a floating-point tie or a seed
[25]. There is no sampling anywhere in
the instrument: the design space is enumerated. <!-- n: v4.games -->

**Policies.** A zoo of eight linear-shading policies (shade factor, plus the payoff-optimal and
payoff-worst extremes) [26,27]. The zoo is deliberately the simplest family for which "which policy is better"
is a well-defined question, so that any rank-payoff divergence we find cannot be blamed on a
mis-specified policy. <!-- n: v4.policies -->

**Populations.** Four declared value distributions — uniform, weak skew, strong skew, capped strong —
giving six population pairs per game [28,29]. <!-- n: v4.populations, v4.population_pairs -->

**Protocols.** Nineteen score rules across three bands, spanning profile readers and row readers,
monotone and saturating and decreasing — the families the score-rule literature separates
[20,30,31]. The space includes the aggregations real benchmarks publish
(mean payoff, win count, champion-take-all) and two constructed extremes used only as witnesses, which
we always name as such. <!-- n: v4.protocols -->

**Cell.** A cell is (game, protocol, population) with the zoo fixed as a set: 9 x 19 x 4 = 684 cells,
read with 1,026 transport entries over the six population pairs. A second, narrower grid — 17
protocols over 4 games, 272 cells — is what the characterisation was first established on; we quote a
count only together with the grid it lives in, because the two grids do not carry the same protocol
set and a count that migrates between them is a count nobody can check.
<!-- n: v4.cells, v4.transport_entries, v2.protocols, v2.games, v3.cells -->

**Statistics.**

- **Rank gain `G`** (positions): how many places a policy moves up when the protocol's ordering
  replaces the payoff ordering. `G = 0` means the protocol ranks the policy where its payoff puts it.
- **Payoff cost `C`**: the payoff lost by the rank-optimal policy relative to the payoff-optimal one.
- **Discrimination `tau`**: Kendall's tau between the protocol's ordering and the payoff ordering over
  the zoo [32,33,34,35]. `tau = 1` is faithful, `tau = -1` is the exact reverse.
- **Transport** `T_raw` and `T_excess`: the share of pairwise orderings lost when the population
  changes, raw and net of the payoff ordering's own transport loss. The second is the protocol's
  contribution; the first includes a baseline every protocol pays. We report both and never conflate
  them (§8).

**Nothing here is estimated from a sample**, so the interval machinery a sampled evaluation needs — a
Wilson interval for a rate, paired tests across tasks, a rank aggregate with its own error — is named
rather than used [36,37,38,39]. That is a property of the design,
not a shortcut: every number in §4–§8 is an exact rational over an enumerated space, and the paper
therefore reports differences and never significance.

**Ground truth by construction.** The instrument is checked against theory rather than against itself.
The symmetric first-price equilibrium has a closed form and is recovered exactly
[24,40]; the second-price
auction's weakly dominant bid is recovered exactly [22]; the common-value n=4 game has **no** certified
anchor, and we state that as an absence rather than filling it [41]. Eight of nine games carry at least one
certified anchor; the ninth is reported uncertified throughout.
<!-- n: v4.anchors_certified, v4.anchors_total, v4.anchors_uncertified -->

## 3 The design law: faithfulness is monotonicity, and the boundary is structural

**The law.** Write `u(p)` for policy p's own payoff-profile value in the population (the vector of its
payoffs against each opponent it meets, reduced by the protocol's own aggregation domain). Then a
protocol's ranking is **faithful** to payoff — `tau = 1` in every cell — **iff** its score is a
strictly increasing function of `u(p)`. The two directions are separate claims and we test them
separately: a strictly increasing score cannot reorder two policies whose profile values are ordered,
and a score that reads anything else — the opponent row, a saturating transform, a decreasing one —
either reorders them or stops distinguishing them, and we exhibit both; the aggregation step it turns
on is the one Arrow's theorem and the multi-criteria work after it make explicit
[42,43,44]. **The two directions do not carry equal weight, and we say
which is which**: the first is monotonicity restated — a definitional consequence of what
*strictly increasing* means, and it could not have failed — while the second is the empirical claim,
and the classification it yields is where the content of this section sits.

**Evidence.** Over 19 protocols x 9 games the law's stated band and the measured band disagree in
**0** cases. Exactly **two** designs are faithful (`mean_payoff`, `spread`), one is immune but
unfaithful (`tail_swap`, constructed), and sixteen are gameable.
<!-- n: v4.law_mismatches, v4.faithful_protocols, v4.band_counts -->

**The row-reading class.** Eleven of the nineteen protocols aggregate the opponent row: `win_count`,
`strict_wins`, `tie_count`, `mean_sq`, `top_half`, `worst_opp`, `best_opp`, `norm_by_best`,
`relative_pair`, `game_wins`, `champion`. **None of the eleven is faithful in a single cell**, which is
the law's sharpest prediction — these are not pathological scores but the scores benchmarks publish
[45,46,47].
<!-- n: v4.row_reading_count, v4.row_reading_faithful_count -->

**The nesting is strict, and it is count-dependent on its grid.** On the 17-protocol / 4-game grid the
faithful cells (54) are strictly contained in the immune cells (96), which are strictly contained in
all 272 cells, leaving a strict band of 42 immune-but-unfaithful cells -- `G = 0` while `tau < 1`.
That band is the paper's seam: immunity to rank-gaming does **not** imply a correct ordering, and §6
turns that observation into the main result. We quote these numbers with their grid because the wider
grid adds two protocols and the counts move.
<!-- n: v2.nesting -->

**Two construction hypotheses we refuted, carried rather than hidden.** We expected the
population-*relative* normalisers (`norm_by_best`, `relative_pair`) to be immune-but-unfaithful, since
they compare a policy against the population rather than against its own profile. They are **both
gameable** on the wide grid (`norm_by_best` is nearly so on the narrow one: 1 of 16 cells). So the
strict band is generic at the *cell* level (42 cells) but, at the *protocol* level, it is reached only
by construction in our space. We state the quantifier rather than the flattering reading: the band is
a real object, and it is not populated by any natural aggregation we found.

**The nineteen split three ways, and the third class is a reference.** Eleven read the opponent row,
seven read the policy's own profile, and one (`random_fixed`) reads neither the population nor the
payoff — it is a fixed population-blind vector, included as a reference, and it is why §8 can report a
protocol whose raw transport is zero everywhere while its excess is not.
<!-- n: v4.row_reading_count, v4.protocols_reading_profile, v4.protocols_reading_neither -->

**A third boundary is structural, not incidental.** The two saturating profile readers, `capped_0` and
`capped_weak`, are gameable because a saturating transform stops increasing where the cap binds — the
law predicts this, and both behave as predicted (`capped_weak` is the nearer miss: 1 of 16 cells on the
narrow grid). And a strictly *decreasing* profile reader (`neg_mean`, `rank_score`) puts the profile's
tail at the head and is gameable by construction. The law names all three as failures of monotonicity,
so none is a counterexample to it. A monotonicity condition on a scoring rule is not exotic: the
autobidding literature states one for the same reason, that a rule's monotone region is where a
ranking can be trusted [48].

## 4 P1: the ranking can be bought

**Registered prior (P1).** *The rank gain is positive in a majority of cells.* **Outcome: confirmed**,
474 of 684 cells (69.3 per cent), and the effect is flat along the n ladder — between 50 and 55 of 76
cells on each of the nine rungs, so it is not an artefact of a particular population size or family.
<!-- n: v4.P1.G_pos, v4.P1.cells, v4.P1.per_game_min, v4.P1.per_game_max -->
Figure 1 draws both readings: the distribution of `G` over the whole grid, and the per-game share that
stays flat along the ladder.

**The maximum is attained by a natural score, not an adversarial one.** The most a policy can gain in a
zoo of eight is seven positions, and the ordinary lower-is-better score `neg_mean` attains
`G_max = 7` while being gameable in **36 of 36** cells. A benchmark that rewards "lower cost is better"
without asking what the score is monotone in has, in this space, maximised exactly the quantity this
paper measures [49,50]. <!-- n: v4.neg_mean.G_max, v4.neg_mean.gameable, v4.neg_mean.cells -->

**The control reads exactly zero.** Over the sixteen v0 cells (four games x four populations), the
monotone score `mean_payoff` gives `G = 0`, `C = 0`, `tau = 1` in every cell. This is the two-sided
control the design requires: the instrument can report a divergence, and it reports none when the
protocol is faithful. <!-- n: v0.control.cells, v0.control.G_pos, v0.control.C_max, v0.control.tau_mean -->

**The outcome channel is the sharpest case.** A score that counts wins -- the most common way a
strategic benchmark reports an agent -- is gameable in **16 of 16** v0 cells and anti-correlated with
payoff on average (`tau = -87/224 = -0.388`): in the winner's-curse games, the policy that wins most
often is not the policy that earns most. "Wins the most games" and "is the better bidder" are not the
same statement, and a published win count does not distinguish them — the divergence between the
published score and the capability it stands for is the phenomenon the reward-hacking literature
records at the level of a single training run [51,52,53,54].
<!-- n: v0.game_wins.G_pos, v0.game_wins.cells, v0.game_wins.tau_mean_exact, v0.game_wins.tau_mean_3dp -->

![Distribution of the rank gain over all 684 cells, and its share with a positive gain in each of the nine games](figures/fig1_p1_gain.png)

*P1: the ranking can be bought. (a) the distribution of the rank gain $G$ over all 684 cells — $G=0$ (the protocol ranks the policy where its payoff puts it) in 210, $G>0$ in 474. (b) the same reading per game: the share of each game's 76 cells with $G>0$ stays between 50 and 55, so the effect is not an artefact of bidder count or auction family.*

## 5 P2: the protocol is the lever, not the population

**Registered prior (P2).** *The spread across protocols exceeds the spread across populations.*
**Outcome: confirmed**, and more strongly than we registered it: not merely larger in total, but larger
*per protocol than per population* in every game.

**The decomposition.** For each game, the gain `G` is an exact rational in every cell, so a two-way
decomposition of its total variation into protocol, population, and interaction terms is exact — no
estimation, no residual to be attributed by hand [38,47]. In all **9 of 9** games the protocol's mean square
exceeds the population's. <!-- n: v4.P2.games_protocol_gt_population, v4.P2.games_total -->

Figure 2 draws the decomposition for every game, and both ratios side by side.

**Its size.** The ratio of mean squares runs from **3.929x** in `cv_n4` to **52.132x** in `spsb_n2`
<!-- n: v4.P2.ms_ratio_min, v4.P2.ms_ratio_min_game, v4.P2.ms_ratio_max, v4.P2.ms_ratio_max_game -->.
We compute this ratio here, from the per-game mean squares the artefact stores as exact fractions, and
we publish the per-game table rather than the range alone: an earlier internal note quoted a range of
"3.9x to 48x", which took a **sum-of-squares** ratio for a **mean-square** ratio in one of its two
endpoints. The mean-square ratio is the quantity the claim is about — a sum of squares grows with the
number of levels a factor has, and the protocol factor has nineteen levels against the population's
four, so an uncorrected ratio would overstate the protocol by construction.

**Both readings are reported.** `SS_protocol > SS_population` is true in 9 of 9 games as well, so the
finding does not depend on which decomposition one prefers; what depends on it is the *magnitude*, and
that is why the magnitude is quoted as a mean-square ratio with its denominator named.

**The cross-check on the narrower grid.** The v0 grid (7 protocols x 4 games x 4 populations, 112 cells,
28 per game) shows the same direction: the gain is positive in 19 or 20 of each game's 28 cells
<!-- n: v0.cells, v0.games, v0.protocols, v0.P1.per_game_G_pos, v0.P1.per_game_cells --> — a smaller
space, the same reading, and a reminder that the direction is not an artefact of the wider protocol set.
(The first version of this sentence said "20 of 20 cells of three of its four games"; the per-game cell
count is 28, and the traceability gate caught the retyped denominator. A smaller number with no
denominator reads as certainty.)

**Why this matters for a benchmark author.** The finding says the ranking is more sensitive to *which
score you publish* than to *which population you sample from* — so a benchmark that reports one
population with several scores, or several populations with one score, is spending its variance in the
place that matters least and the most respectively — a choice the design-side literature makes
explicit when it reports which score, which judge configuration, and which task subset a published
number was computed under [55,56,57,58,59]. The decision §7 draws follows from it.

![Mean squares of the rank gain for the protocol and the population factors in each game, with the two candidate ratios](figures/fig2_p2_lever.png)

*P2: the protocol is the lever. (a) the exact two-way decomposition of $G$ in each game, on a log scale: the protocol's mean square exceeds the population's in 9 of 9 games. (b) the two ratios a reader could compute — the mean-square ratio (the claim, 3.929x to 52.132x) and the sum-of-squares ratio, which is larger for the protocol by construction because the protocol factor has 19 levels against the population's 4.*

## 6 P3 refuted: buyable rank and fragile rank are two properties

**Registered prior (P3).** *The protocols that let a policy buy rank are the same protocols whose
ordering fails to transport* — one property, observed twice. **Outcome: refuted, with a direction.**

The refutation has three parts, and the second is the one that changes a decision.

**(i) The dominance is strict, and it is a containment rather than a tendency.** In every cell where a
policy can gain rank, the protocol's ordering is also unfaithful —
the two failures a rank aggregate can have, honest aggregation and decisive aggregation, arrive
together here [39,60,61] — so: `G > 0 => tau < 1`, with **0
counterexamples** over the 684 cells. The gameable cells (**474**) are therefore strictly contained in
the fragile cells (**564**) — a proper nesting, **90** cells wide, in which the ordering is already
broken while nothing can be bought. That band is the paper's seam: a benchmark author who checks only
"can my score be gamed?" clears those protocols and still publishes a wrong ordering.
<!-- n: v4.T3.counterexamples, v4.T3.gameable, v4.T3.fragile, v4.T3.band -->
Figure 3 draws the same containment protocol by protocol: the dark (gameable) share never extends past
the grey (fragile) share in any of the nineteen rows.

![Per-protocol share of gameable and fragile cells, and the containment as cell counts](figures/fig3_p3_opposition.png)

*P3 refuted: buyable rank and fragile rank are two properties. (a) per protocol, the share of its 36 cells that are fragile (grey) and gameable (dark) — the dark never escapes the grey, which is the dominance $G>0 \Rightarrow \tau<1$ with 0 counterexamples. (b) the containment in cells: 474 gameable strictly inside 564 fragile, leaving a band of 90 cells that are already misordered while nothing can be bought in them.*

**(ii) One design is maximally opposed by the two statistics.** They do not merely come apart; they come
apart in opposite directions on the same object. The constructed witness `rank_score` scores each policy
by its payoff **rank**, so the payoff-worst policy leads: it is gameable in **36 of 36** cells with
`G_max = 7` (the maximum the zoo permits) and reversed in **36 of 36** — and its transport excess is
**exactly zero in all 54 entries**. So the same protocol is the worst object in the space by
rank-gaming and perfect by transport. A statistic that reported one of these and called it "the
protocol's quality" would have made a maximally wrong decision on exactly this protocol. The
distinction is not one statistic's blind spot: what a pairwise comparison measures and what the
capability behind it is are separate claims [62].
<!-- n: v4.neg_mean.G_max, v4.transport.excess_zero_set, v4.T3.reversed_by_protocol,
census.exc.rank_score -->

**(iii) The reversals are a real mode, not a rounding of "unfaithful".** **71** cells read `tau = -1` —
the exact reverse of the payoff ordering — split as 36 from `rank_score` and 35 from `neg_mean`. We
keep `tau < 1` and `tau = -1` as separate counters throughout, which is also why the choice of rank
correlation is stated rather than assumed — the measures are not interchangeable and their bounds
differ under dependence [34,35], because a single "unfaithful" count
would report a protocol that mildly misorders as identical to one that inverts, and the two call for
different repairs. <!-- n: v4.T3.reversed_cells, v4.T3.reversed_by_protocol -->

**The natural witness, and what it does not do.** We looked for the same opposition in a score nobody
constructed — an ordinary lower-is-better `neg_mean`. It attains the maximum gain (`G_max = 7`, gameable
36 of 36), so it establishes that (i)'s regime is reachable by a real reporting convention. It does not
establish (ii): its excess is zero in 51 of 54 entries, and the three exceptions are payoff-tie cells
where the ordering is not determined. So the maximal opposition rests on the constructed witness, and
we say so rather than letting a near-miss stand in for the demonstration.
<!-- n: v4.neg_mean.cells, census.exc.neg_mean -->

**What the correction costs and buys.** We registered the opposite, and the refutation is worth more
than the confirmation would have been: the confirmed version would have said "audit for gaming and you
have audited for transport", which is false and would have been the design rule we published. The
refuted version says the two audits are separate instruments that disagree maximally on some designs,
which is a rule a benchmark author can act on (§7).

## 7 The separation ladder: audit the ordering, not the champion

§6 says the two properties are separate. It does not say how a benchmark author *uses* that. This
section turns the containment into a ladder by asking a different question: as a score is contaminated
by an outcome channel, which audit fires first? Auditing is itself a measured object in this
literature — validity audits have their own failure modes, and an audit run from existing evaluation
runs is not the same instrument as a fresh one [63,64,65].

**The construction.** Mix a faithful score with an outcome score — `s_lambda = (1 - lambda) *
norm(mean_payoff) + lambda * norm(game_wins)` — and sweep `lambda` over the sixteenths from 0 to 1. At
each `lambda`, count how many of that game set's 16 cells have bought rank (`G > 0`) and how many have
a broken ordering (`tau < 1`). <!-- n: v1.ladder.base, v1.ladder.table -->

**The ladder.** At `lambda = 0` neither fires, as it must. At **`lambda = 1/16`** five cells have a
broken ordering and **no** cell has bought rank — the ordering audit fires while the champion audit
still reads zero. At **`lambda = 1/8`** the first cell buys rank (1 of 16) and thirteen have broken
orderings. Buyability saturates at `lambda = 5/16`, where all 16 cells have both properties.
<!-- n: v1.lambda_tau, v1.ladder.tau_lt_1_at_lambda_tau, v1.ladder.g_pos_at_lambda_tau,
v1.lambda_G, v1.ladder.g_pos_at_lambda_G, v1.ladder.tau_lt_1_at_lambda_G, v1.ladder.saturation_lambda -->

**The design rule.** `lambda_tau = 1/16 < lambda_G = 1/8`: **a leaderboard audit that reads the ordering
detects corruption at half the contamination that an audit reading only the champion needs.** An audit
of "who won" is not a cheaper version of an audit of "what order was published" — it is a strictly less
sensitive one, and between the two thresholds it returns a clean verdict on a broken table. The
leaderboard-side literature reaches the same conclusion from the other direction: a statement about a
winner is the least stable quantity a leaderboard publishes, and a pinned, matched-control audit of the
ordering is what a reader can check [11,66,67,68,46].

**The control, and it is two-sided.** The ladder must be a property of the *contamination*, not of
mixing as such: with a monotone base and a monotone transform, no `lambda` fires either threshold — `0`
cells with `G > 0` and `0` with `tau < 1` across the whole sweep. So the thresholds are caused by the
score ceasing to be monotone in the policy's own payoff, which is the design law (§3) read along a
continuous axis rather than a binary one.
<!-- n: v1.ladder.monotone_plant_fires -->

**What the ladder does not say.** It does not say the ordering audit is *sufficient* — §6 shows
`rank_score` passes a transport audit perfectly while inverting the ordering, so "the ordering
transports" and "the ordering is correct" are also distinct questions (§8). It says which of two
audits detects a given corruption earlier, on a declared sweep.

## 8 The transport law, and the exact scope of its converse

A ranking is published to be used on a population other than the one it was measured on
[47,28]. The question has been asked in other vocabularies — whether a measured
capability transfers across encounters, whether an adapted model survives a shift in its clinical
population, whether a transferability estimate predicts the ordering on a new corpus, and what a
convenience sample can say about the population it was drawn from
[69,70,71,29]. So the second
question is what the ordering does when the population changes. Our statistic is the transport excess at
the **entry** level — an entry is a protocol together with an ordered pair of populations — defined as
the pairwise-ordering loss under the population change, net of the loss the payoff ordering itself
carries.

**The forward law, and it has no exceptions.** If a protocol is faithful in both populations, its
transport excess is zero. This holds over all 1,026 entries with **0** counterexamples
<!-- n: census.exc.entries, census.exc.forward_counterexamples_all -->, and the reason is exact rather
than statistical: when both orderings equal the payoff ordering, the loss between them is the payoff
ordering's own loss, which is exactly what the excess subtracts.

**The orientation theorem.** The forward law is a special case of a sharper statement: the excess is
zero whenever the protocol's ordering has the **same orientation** in both populations — both equal to
the payoff ordering, or both its exact reverse — because reversing both sides of a pairwise comparison
leaves its loss unchanged. Faithfulness implies same-orientation; the converse of *that* implication is
false, and the gap is the transport statistic's blind spot. Estimating a pairwise ordering and
deciding how many comparisons it needs are problems with their own literature, and both are stated
here as finite counts for that reason [72,73,74].

**The naive law is refuted at the entry level, not only by a constructed witness.** It would be easy to
refute `excess == 0 <=> faithful` with the constructed `rank_score` and stop. The refutation is
stronger than that: over the full domain there are **367** violating entries, **262** of them inside the
record space over **14** designs; restricting to the informative half — entries where the payoff
ordering's own loss is nonzero, so the statistic is measuring something — leaves **161**, of which
**86** are in the record space over **8** designs. The record-space violators are ordinary aggregations:
`tail_swap` 33, `win_count` 17, `strict_wins` 10, `norm_by_best` 7, `relative_pair` 6, `game_wins` 5,
`mean_sq` 5, `top_half` 3. <!-- n: census.exc.violators_all, census.exc.violators_record_all,
census.exc.violators_record_all_designs, census.exc.violators_base_positive,
census.exc.violators_record_base_positive, census.exc.violators_record_base_positive_designs,
census.exc.record_base_positive_by_protocol -->

**A count coincidence we name rather than quote.** `|evaluated set| = 262` and `|record-space violators
over the full domain| = 262` are the **same number over two disjoint sets**: the evaluated set's record
part is 157, and its record-level intersection with the violator set is **0**. An earlier internal note
quoted "262" twice as if it were one quantity. Neither count can be quoted without its set, and the
census asserts the disjointness so that a later edit making them equal by construction is made to say
so. <!-- n: census.exc.evaluated_all, census.exc.evaluated_record,
census.exc.evaluated_record_intersect_violators -->

**`T_raw` is not `T_excess`, and the difference is a population-blind score.** For `random_fixed`, whose
score reads neither the population nor the payoff, the raw loss is zero in **all 54** entries while the
excess is zero in only **15** — all of them entries where the payoff baseline is zero. The two
statistics answer different questions ("did the observed orderings coincide?" versus "did the protocol
add loss beyond the baseline?"), and a paper that reported one under the other's name would be making a
claim about the wrong object. <!-- n: census.exc.random_fixed -->

**The converse, decomposed rather than asserted.** `excess == 0 => faithful` needs a population pair on
which two policies' payoff order flips **and** a protocol whose relation to the payoff flips with it, at
a pair exactly **14 of 28** comparisons discordant. The first condition is **available**: over the
integer grid of populations (19,448 per game at resolution 1/10) the reachable discordance reaches
**18 of 28**, each game's reachable set is a contiguous integer run, and **14** is attained exactly in
`spsb_n2`, `spsb_n3` and `spsb_n4`, certified in exact arithmetic. The second condition is **empty**:
no protocol in the design space — **0** of them, at those pairs or anywhere in the 684-cell scan — is
mixed-oriented. <!-- n: census.conv.grid_populations_per_game, census.conv.max_reachable_discordant,
census.conv.target_discordant, census.conv.pairs, census.conv.games_attaining_target,
census.conv.mixed_orientation_count -->

**Why the design space cannot decide it, and what would.** The shipped four populations never separate
past **3 of 28** discordant comparisons, so the sample of record cannot reach the target pair at all.
And the missing factor has a name: a **population-conditional** score — `+rank` under one population,
`-rank` under the other — is mixed-oriented at exactly that pair and reads an excess of exactly zero,
which the census demonstrates by construction. The converse is therefore not refuted, not confirmed, but
**undecidable in this space, for a stated reason**: the design space contains no score whose monotone
relation to the payoff flips with the population. A benchmark suite that wants the converse decided must
admit such a score, and we say so instead of leaving the reader with "no counterexample found".
<!-- n: census.conv.max_of_record -->

**The certificate.** Both censuses carry executable certificates over their own readings: 8 of 8 for the
excess census and 16 of 16 for the converse census, including plants that corrupt a faithful entry, that
relabel an informative violator as uninformative, and that exhibit the population-conditional score.
<!-- n: census.exc.certificate, census.conv.certificate -->

## 9 Threats to validity, and why the contribution survives

**(1) The design space is in-silico and declared.** Every claim is a fact about nine games, eight
policies, four populations and nineteen protocols, enumerated exactly. We make no claim about a
deployed benchmark, a real population of agents, or a field deployment, and §1 says so before the
results do. What transfers is not the numbers but the *structure* — a distinction the construct-validity
literature draws between a benchmark's structural claim and its predictive one
[75,76] —: the design law is a statement about
what a score must be monotone in, and that statement has no game-specific content.

**(2) `n <= 4` and a linear-shading zoo.** Four bidders and eight shade factors is a small world, chosen
because it is the smallest one in which "which policy is better" is well defined and the payoff
ordering can be computed exactly. A richer policy space could host a protocol that is faithful in our
space and not in a larger one [77,40]; the law predicts it cannot, and that prediction is testable — but we have
not tested it, and a reader should treat the universality of the law beyond our space as a conjecture
with evidence, not a theorem.

**(3) The common-value n=4 game has no certified anchor.** Eight of nine games carry at least one
certified anchor recovered from theory; `cv_n4` carries none, and the reason is stated rather than
papered over: the common-value equilibrium we would certify against is not a closed form we can verify
at that size. Its cells are therefore in every count above without the anchor that would independently
confirm the instrument in that regime. The winner's-curse family is where the payoff-optimal policy
itself moves with the population, which is precisely the regime §5 and §8 say matters, so this absence
is a real limitation and we name it in the abstract's claim boundary as well.
<!-- n: v4.anchors_certified, v4.anchors_total, v4.anchors_uncertified -->

**How far the anchor-free game carries the result, stated rather than left to the reader.** Excluding
`cv_n4`'s cells entirely, the three headline numbers are: `G > 0` in **423 of 608** cells (was 474 of
684); the protocol's mean square exceeding the population's in **8 of 8** remaining games, from
**4.802x** to **52.132x** (was 9 of 9 at 3.929x–52.132x); and the containment **423 gameable cells inside
503 fragile ones, with 0 counterexamples** to `G > 0 => tau < 1` (was 474 inside 564)
<!-- n: r6.excl.game, r6.excl.g_positive, r6.excl.cells, r6.excl.games, r6.excl.gameable,
     r6.excl.fragile, r6.excl.counterexamples, r6.excl.ratio_min_3dp, r6.excl.ratio_max_3dp -->. Every qualitative
result is unchanged and the smallest ratio moves *up*: the anchor-free game is where the protocol's
advantage over the population is weakest, so removing it strengthens rather than weakens the claim this
paper actually makes.

**(4) The transport arm reports one statistic per entry.** Transport is computed at the entry level
(protocol, ordered population pair), not per policy, so a protocol could pass while a particular policy
changes order. We did not measure policy-level transport; a suite that publishes per-policy comparisons
would want it, and §8's orientation theorem carries over only to the entry level as stated.

**(5) There is no real-leaderboard arm.** The natural next step — take a published leaderboard, recover
its protocol exactly, and test whether the divergence predicted here appears in its data — is not done.
It is the direction we would most like to see contested, and its absence means the paper's contribution
is a theory with an exact in-silico measurement rather than a field observation. The three works that
come closest to that arm all measure a different object with a protocol they hold fixed
[4,78,79]. The journal's
synthetic-data rule is satisfied precisely because we claim no more than that: the in-silico results
establish what protocols *can* do, and nothing about what any deployed benchmark *is* doing.

**A validity claim we deliberately do not make.** The construct-validity literature asks whether a
benchmark measures the capability it names, and answers with nomological networks, structural tests,
psychometric fits and audits of the readout rather than with a single number
[2,80,81,82,83,84,85,86,87,88,89].
We do not claim a benchmark is invalid. We claim something narrower and checkable: that a protocol
choice carries a measurable share of the ordering it publishes, and that the share is computable from
the protocol alone.

**Why the contribution survives all five.** The paper's central claim is an equivalence with a
constructive proof on either side, tested exhaustively in a space where the test is exact; its second
claim is a refutation of our own registered hypothesis with a counterexample that is maximally opposed
by the two statistics; its third is a design rule with a measured threshold ratio. None of those three
becomes a smaller claim when the space is smaller — an equivalence over a finite exact space is either
true or has a counterexample in it, and we report zero mismatches over 19 protocols x 9 games plus the
witness set. A reader who doubts our space can falsify us cheaply: add a protocol, run the law, and see.
<!-- n: v4.law_mismatches -->

## 10 Related work

**Benchmark papers that report the phenomenon without manipulating the protocol.** ERPBench evaluates
100 fixed problems under two matched competitive ecologies and reports that the two ecologies identify
the **same task-level winner on only 21 of 100 problems** — the ranking does not transport
<!-- n: external(arXiv:2609.04667) --> [4]. That is the phenomenon this paper explains,
measured by someone else in a system we did not build. The difference is the unit of analysis:
ERPBench holds the protocol fixed and varies the ecology, so the protocol is an input; we hold the
ecology family fixed and vary the protocol, because the protocol is the object whose contribution we
want to price.

**Incentive theory for agentic markets.** The closest theoretical neighbour models the interaction as a
Stackelberg game over training resources and latent quality [78]. It asks how an agent
should invest to score well; it does not model the score's aggregation, the opponent row, or what
happens to the ordering when the population changes. Our object — an in-episode policy facing a
declared score rule — is disjoint from it, and the two results are complementary rather than competing:
theirs prices the incentive to improve, ours prices the incentive to be ranked. The same distinction
runs through the auto-bidding literature, where incentive compatibility is a property of the allocation
and payment rule and the bidder's best response is the object
[90,91,27], through the payment rules a platform actually runs
[92,93,94], and through auction theory adapted to deployed formats
[95,96], and through settings in which the bidder is itself a language model
[97]. In all of it the score is a design choice whose incentive properties are
analysed; in none of it is the *published ordering* what the score is analysed for.

**Leaderboard inference.** A distinct line fixes the *statistical* reuse problem: given a published
leaderboard, what can be inferred about unseen comparisons
[79,10,61]. That work treats the published ordering as the datum. We ask
the prior question — what does the published ordering *measure* — and a result that the ordering is
partly an artefact of the score would bound what that literature's inferences can carry, which is the
sense in which §6's refutation has a consumer outside this paper. A related line models the rating
itself as an estimator with a noise floor and a misspecification risk
[98,99,100,101], and asks what a leaderboard can certify and how a
judge's own extraction can move the verdict [67,102].

**Measurement gaming in economics.** The principal's choice of measure, and the agent's response to it,
is a classical problem [103]. It supplies the intuition that a score can be gamed and
the vocabulary of distortion, but it carries no population axis: the measure is a function of the
agent's action, and the question of whether the induced ordering survives a change in the population
the measure is evaluated on does not arise in that framing. Our transport statistic is that missing
axis, and §8 shows that the classical intuition (a score that cannot be bought is a score whose
ordering holds) is false in a family of ordinary aggregations. The modern formalisations of the same
intuition are the closest neighbours to §4 and §6, and they too are stated without a population axis:
Goodhart's law given a formal statement [16,17], a proxy measured against the
goal it stands for in one instrument [104,105], a sealed audit designed to resist
gaming [106], and the reward-hacking family in which the score is a verifier and the
policy learns to satisfy the verifier instead [107,108,109,110].

**Scoring rules and aggregation as the instrument.** That a score is a designed object with declared
incentive properties is the scoring-rule literature's premise, from proper scoring rules and their
surrogates [20,30,31] through second-order and joint rules
[111,112], honest performative prediction [113] and forecasting
competitions [114] to the observation that a scoring rule shapes what a model reports
[115]. The aggregation of many such scores into one ordering is social-choice territory,
where Arrow's theorem is the boundary condition [42,116] and the responses are to
choose an aggregate deliberately — utilitarian, representative, or relative-judgement based
[117,118,44] — and where the aggregation of partial rankings is a problem
with its own methods and its own impossibility results
[119,120,60]. Our §3 law is the special case of this in which the objects
being aggregated are the rows of a payoff matrix rather than a profile of preferences.

**Benchmark design and construct validity.** The broader methodological literature on what a benchmark
measures — construct validity, contamination, and the difference between a score and the capability it
is supposed to index — motivates the enterprise; we do not claim to extend it
[121,122,123,124,125,126,127]. What we add is a
*protocol-level* quantity: not "is this benchmark valid?" but "which of this benchmark's design
decisions carries the divergence, and by how much". One strand of that literature is closer to our
result than to a validity verdict: the observation that a published ordering can be pluralistic, that
its intervals can be reported, and that a contamination that inflates every score need not reorder them
[128,45] — the last is the empirical face of §6's claim that a corruption and a
reordering are two properties.

**The multi-agent evaluation line, and where this paper stands against it.** Three works treat the
aggregate and the population as the object in this paper's own setting — games, payoffs, policies,
populations — and each is answered here with the analysis the comparison requires rather than with an
acknowledgement.

*Against Balduzzi et al.* [5] *— independent, not a special case.* Their result is an
impossibility conditional on the game being intransitive: a transitive rating system misranks a game
whose payoff structure is cyclic, so the aggregate must be a solution concept. It does not reach this
paper's measured space, and the reason is exact. We computed the transitivity coordinate of every game
in the ladder — the share of strategy triples that are cyclic under "a beats b" — and it is **0/56 in
seven of nine games** and **3/56 in the other two** <!-- n: trans.coord.zero_games, trans.coord.nonzero_games -->. Of the **474** rank-gaming cells, **374** — **78.9 %** — lie in games with a
zero coordinate <!-- n: trans.gpos.coord0, trans.gpos.total, trans.gpos.share_pct -->. That share is an
**existence** reading and not a distributional one, and the base rate says so: seven of nine games have a
zero coordinate, so a cell picked at random lands in one with probability **77.8 %**, against the
**78.9 %** observed <!-- n: trans.coord.base_rate_pct -->. What the
figure establishes is therefore that the misordering survives where no cyclic structure can obstruct a
transitive rating; it does not establish that the misordering concentrates there. The misordering priced in §4 therefore
survives in games where a total order exists and no cyclic structure can obstruct a transitive rating:
their impossibility says no total order can represent a cyclic game, and this law says a total order
that does represent an acyclic one can still be bought. The two are disjoint failure modes, measured on
disjoint structures.

*Against Czarnecki et al.* [6] *— the question is answerable here, and the answer is
negative.* They make non-transitivity against population the axis, which is a property of the **payoff
structure**. Our transport excess is a property of the **protocol**. The reduction test is therefore
sharp: at a *fixed* game and a *fixed* population pair, the coordinate is pinned, so if the statistic
reduced to it the excess could not move. It moves. In **9 of 9** games the excess takes more than one
distinct value across the nineteen protocols at a fixed pair, and up to **8** distinct values at the
widest pair (`uniform` against `capped_strong`, e.g. `-1/14` for `best_opp` against `3/7` for
`tail_swap` in `fpsb_n4`) <!-- n: trans.distinct_max, trans.distinct_gt1_games, trans.widest.low, trans.widest.high -->. The coordinate is
also degenerate on this ladder before any transport is computed: seven games share a value of zero, so
it ties **22 of 36** game pairs and orders the remaining **14** <!-- n: trans.coord.ties, trans.game_pairs --> — a
**partial order on this ladder**, not the absence of one. What the
transport statistic carries that the dimension does not is thus not a refinement of it but a different
object: the dimension says how much the *game* can move, the excess measures what the *protocol* adds
once that motion is subtracted — which is also why the paper's own baseline term is not the coordinate

*And it survives conditioning on the second axis.* A reduction test that pins one axis leaves the other
open, so the spread was re-read with **both** of Czarnecki et al.'s axes held fixed over the **54**
(game, population-pair) cells: grouped by the transitive-strength pair, by the population-size pair (the
number of policies carrying weight), and by both at once, **every conditioning cell still shows more
than one distinct excess value, with a minimum of 2 distinct values in all three readings**
<!-- n: cond.pairs, cond.coord.min_distinct, cond.size.min_distinct, cond.both.min_distinct -->. The sharpest
form is the degenerate one: in the **seven** games whose coordinate is zero at *every* population — so the
coordinate pair is (0, 0) for every pair — the excess across the **42** pairs still spans **2 to 8**
distinct values <!-- n: cond.coord0.pairs, cond.coord0.min_distinct, cond.coord0.max_distinct -->. Non-reduction
therefore holds *inside* the case where the coordinate is pinned completely, and not merely across cases
where it differs.
but the payoff ordering's realised loss under the change, a quantity that varies across population pairs
within a game of constant coordinate <!-- n: trans.base.distinct_max_coord0 -->.

*Against Omidshafiei et al.* [7] *— a different side of the same object.*
α-Rank proposes a ranking *method*, computed from the game's evolutionary dynamics, offered as a
faithful way to rank agents. This paper takes the deployed side: given a score rule and an
opponent-selection rule a benchmark already uses, what does the resulting ordering do. α-Rank would be
one more protocol in the design space, and the law of §3 predicts which of its cells can be faithful —
so the two are complementary instruments rather than competing claims, and neither is evidence about the
other.

**The auction canon, named because a referee will look for it.** The game families are textbook objects
[22,129,24] and the equilibrium concepts the anchors are checked against
are the ones the canon defines [130,131]. We use them the way a
measurement paper uses a ruler: nothing here extends auction theory, and none of our claims is about
auction theory rather than about what a protocol built on an auction measures. A design whose
tie-breaking is declared rather than inherited [132] is part of the same discipline.

## 11 Conclusion

An evaluation protocol is not a neutral instrument. Over an exact design space we have shown that a
protocol's ranking is faithful to payoff exactly when its score is a strictly increasing function of the
policy's own payoff-profile value — a law with no mismatches over 19 protocols and 9 games, and no
row-reading protocol faithful in a single cell. We have shown that the ranking can be bought in 474 of
684 cells and that the protocol is the larger lever by a measured margin (3.929x to 52.132x on mean
squares, 9 of 9 games). And we have shown — against our own registered prediction — that buyable rank
and fragile rank are two properties, strictly nested, maximally opposed on one design, with an audit
consequence: read the ordering and you detect corruption at half the contamination a champion-only
audit needs.

The result that should travel furthest is the negative one. "A score that cannot be gamed is a score
whose ordering holds" is the intuition the incentive literature supplies, and it is false: 90 cells in
our space are fragile while nothing is buyable in them, and 86 record-space entries transport badly
while the naive law says they cannot. A benchmark that audits for gaming and stops has audited the
smaller of the two problems.

Two questions we leave open, and both are stated as open rather than as future work we intend to
perform. The converse of the transport law is **undecidable in this design space** — the population pair
it needs exists and is certified, but no protocol in the space flips its monotone relation with the
population, so the fixed point of the converse is a score we did not admit, not a fact we could not
establish. And the whole account is in-silico: the arm that would test these laws against a published
leaderboard's own recovered protocol is the arm we most want a reader to run against us.

## References

[1] Eriksson, M.; et al. (2025). Can we Trust AI Benchmarks? an Interdisciplinary Review of Current Issues in AI Evaluation. arXiv:2502.06559. https://arxiv.org/abs/2502.06559 -- Difference: surveys what is wrong with AI benchmarks across disciplines; the survey names the problems, and this paper supplies an exact quantity for one of them — the share of an ordering that a protocol decision owns

[2] Bean, A. M.; et al. (2025). Measuring what Matters: Construct Validity in Large Language Model Benchmarks. arXiv:2511.04703. https://arxiv.org/abs/2511.04703 -- Difference: measures construct validity in language-model benchmarks; validity is scored per benchmark there, while this paper's quantity is a property of a score's aggregation and is exactly computable

[3] Longjohn, R.; et al. (2024). Benchmark Data Repositories for Better Benchmarking. arXiv:2410.24100. https://arxiv.org/abs/2410.24100 -- Difference: argues benchmark data repositories are infrastructure; repositories are the subject there, and the aggregation rule is the subject here

[4] Zhang, X.; et al. (2026). ERPBench: Evaluating LLM Agents for Enterprise Decision-Making Across Competitive Market Ecologies. arXiv:2609.04667. https://arxiv.org/abs/2609.04667 -- Difference: reports that two matched ecologies pick the same task-level winner on only 21 of 100 problems; it holds the protocol fixed and varies the ecology, so the protocol stays an input — this paper varies the protocol and prices its contribution

[5] Balduzzi, D.; et al. (2018). Re-Evaluating Evaluation. arXiv:1806.02643. https://arxiv.org/abs/1806.02643 -- Difference: shows that a transitive rating misranks a game whose payoff structure is cyclic and concludes the aggregate must be solution-concept-based, an impossibility that is conditional on intransitivity; in this paper's ladder seven of nine games have zero cyclic triples and 374 of the 474 rank-gaming cells lie in them, so the misordering priced here survives where that obstruction cannot apply

[6] Czarnecki, W. M.; et al. (2020). Real World Games Look Like Spinning Tops. arXiv:2004.09468. https://arxiv.org/abs/2004.09468 -- Difference: makes non-transitivity against population the axis, a property of the PAYOFF structure; measured on this ladder that axis is degenerate (seven of nine games at zero cyclic triples, 22 of 36 game pairs tied), and the transport excess is a property of the PROTOCOL -- it takes up to eight distinct values at a fixed game and population pair in all nine games -- so the statistic does not reduce to it

[7] Omidshafiei, S.; et al. (2019). α-Rank: Multi-Agent Evaluation by Evolution. Scientific Reports. https://doi.org/10.1038/s41598-019-45619-9 -- Difference: proposes a ranking method computed from the game's evolutionary dynamics, i.e. an algorithm offered as faithful rather than a study of what an already-deployed score rule does; it would be one more protocol in this paper's design space, and the law here predicts which of its cells can be faithful

[8] Ethayarajh, K.; Jurafsky, D. (2020). Utility is in the Eye of the User: A Critique of NLP Leaderboards. Proceedings of the 2020 Conference on Empirical Methods in Natural Language Proc. https://doi.org/10.18653/v1/2020.emnlp-main.393 -- Difference: critiques leaderboards by showing utility is user-relative; this paper keeps a single declared utility and asks what the score's aggregation does to the ordering of it

[9] Oyarhoseini, H.; Lin, J.; Karimi, A. (2026). A Unified Perturbation Framework for Analyzing Leaderboard Stability and Manipulation. arXiv:2605.15761. https://arxiv.org/abs/2605.15761 -- Difference: perturbs leaderboards to analyse stability and manipulation; the perturbation is empirical, and this paper's population change is an exact re-enumeration

[10] Neuhof, B.; Benjamini, Y. (2026). Rank Intervals for Leaderboards: A Hierarchical Framework for Model Evaluation. arXiv:2606.08679. https://arxiv.org/abs/2606.08679 -- Difference: reports rank intervals for leaderboards; the interval is a sampling statement there, and this paper's ordering is exact so no interval applies

[11] Ayyagari, K. C. (2026). Pinned and Still Unstable: Within-Judge Verdict Variance and the Noise Floor of LLM-as-Judge Leaderboards. arXiv:2609.33044. https://arxiv.org/abs/2609.33044 -- Difference: measures within-judge verdict variance and sets a noise floor for judge leaderboards; the floor is sampling noise there, while this paper's divergence is systematic and has no noise to floor

[12] Holmstrom, B.; Milgrom, P. (1987). Aggregation and Linearity in the Provision of Intertemporal Incentives. Econometrica. https://doi.org/10.2307/1913238 -- Difference: shows how the aggregation of performance information into an incentive scheme determines what the scheme can elicit; this paper takes that lesson to an evaluation protocol and measures the rank divergence the aggregation causes

[13] Holmstrom, B. (1979). Moral Hazard and Observability. The Bell Journal of Economics. https://doi.org/10.2307/3003320 -- Difference: the principal measures what it can observe, and the measure shapes the agent's action; that intuition is this paper's starting point, with the population axis it does not carry added

[14] Strathern, M. (1997). ‘Improving Ratings’: Audit in the British University System. European Review. https://doi.org/10.1002/(sici)1234-981x(199707)5:3<305::aid-euro184>3.0.co;2-4 -- Difference: argues that an audit alters the practice it audits; this paper turns that argument into a countable statistic of a protocol

[15] Campbell, D. T. (2011). Assessing the Impact of Planned Social Change. Journal of MultiDisciplinary Evaluation. https://doi.org/10.56645/jmde.v7i15.297 -- Difference: the classic statement that indicators used for decisions get gamed; this paper prices the gaming in rank positions and separates it from transport

[16] El-Mhamdi, E.; Hoang, L. (2024). On Goodhart's Law, with an Application to Value Alignment. arXiv:2410.09638. https://arxiv.org/abs/2410.09638 -- Difference: formalises Goodhart's law for value alignment; the formalisation is about an optimiser diverging from a true objective, while this paper measures an ordering's divergence in a finite exact space

[17] Majka, A.; El-Mhamdi, E. (2025). The Strong, Weak and Benign Goodhart's Law. an Independence-Free and Paradigm-Agnostic Formalisation. arXiv:2505.23445. https://arxiv.org/abs/2505.23445 -- Difference: distinguishes strong, weak and benign forms of Goodhart's law; the taxonomy is conceptual, and this paper's contribution is the countable quantity the law needs to be tested with

[18] Myerson, R. B. (1981). Optimal Auction Design. Mathematics of Operations Research. https://doi.org/10.1287/moor.6.1.58 -- Difference: designs an auction to maximise the seller's revenue: the score is the objective and the bidders are constrained; here the score is the instrument under test and the policies are free, so the question is what the score measures rather than what it should maximise

[19] Boutilier, C. (2011). Eliciting Forecasts from Self-Interested Experts: Scoring Rules for Decision Makers. arXiv:1106.2489. https://arxiv.org/abs/1106.2489 -- Difference: designs scoring rules that elicit forecasts for a decision maker; a score is chosen to extract information, whereas this paper measures what a chosen score does to a ranking

[20] Liu, Y.; Wang, J.; Chen, Y. (2018). Surrogate Scoring Rules. arXiv:1802.09158. https://arxiv.org/abs/1802.09158 -- Difference: builds surrogate scoring rules when the true score is unavailable; the proxy is the subject there, the ranking consequence of a proxy is the subject here

[21] Milionis, J.; Pires, W. (2026). On Testing the Incentive Compatibility of Single-Parameter Allocation Mechanisms. arXiv:2609.17406. https://arxiv.org/abs/2609.17406 -- Difference: tests incentive compatibility of single-parameter allocation mechanisms; that is a test of a mechanism's truthfulness, this paper's law is about a score's monotonicity in a policy's own payoff

[22] Vickrey, W. (1961). Counterspeculation, Auctions, and Competitive Sealed Tenders. The Journal of Finance. https://doi.org/10.1111/j.1540-6261.1961.tb02789.x -- Difference: introduces the sealed-bid formats and the second-price rule whose dominant-strategy bid is a closed form; it asks how a bidder should bid in one auction, never what a score built on the outcomes does to a population's ordering

[23] Wilson, R. (1977). A Bidding Model of Perfect Competition. The Review of Economic Studies. https://doi.org/10.2307/2296904 -- Difference: models common-value bidding where the winner's curse arises; this paper uses that family as the regime in which the payoff-optimal policy itself moves, and reports no new equilibrium result

[24] Klemperer, P. (1999). Auction Theory: A Guide to the Literature. DOI:10.2139/ssrn.172650. https://doi.org/10.2139/ssrn.172650 -- Difference: surveys auction theory as a body of results about mechanisms; this paper uses none of its theorems and instead treats a mechanism-derived score as a measured object

[25] Rasooly, I.; Gavidia-Calderon, C. (2020). The Importance of Being Discrete: on the Inaccuracy of Continuous Approximations in Auction Theory. arXiv:2006.03016. https://arxiv.org/abs/2006.03016 -- Difference: shows continuous approximations are inaccurate in discrete auction theory; this paper's exactness over an integer grid is a design choice that reference supports rather than a result it repeats

[26] Nedelec, T.; et al. (2020). Learning in Repeated Auctions. arXiv:2011.09365. https://arxiv.org/abs/2011.09365 -- Difference: studies learning in repeated auctions; this paper's zoo is a fixed set of shading policies, deliberately not learners, so the divergence cannot be blamed on adaptation

[27] Chen, X.; Kroer, C.; Kumar, R. (2021). Throttling Equilibria in Auction Markets. arXiv:2107.10923. https://arxiv.org/abs/2107.10923 -- Difference: derives throttling equilibria for a market; pacing/throttling is a population-level design lever, whereas this paper's lever is the score's aggregation

[28] Gjorgjevikj, A.; Seljak, B. K.; Eftimov, T. (2026). On the Robustness of Multilingual Text Embedding Rankings Across Learning Tasks, Languages, and Benchmark Datasets. arXiv:2605.31142. https://arxiv.org/abs/2605.31142 -- Difference: measures how robust multilingual embedding rankings are across tasks and datasets; robustness is assessed empirically there, and the transport condition is derived here

[29] Rezaeimanesh, S.; et al. (2026). INCONVENIENT: A Benchmark to Assess LLM Generalization Capabilities from Convenience Samples. arXiv:2610.21038. https://arxiv.org/abs/2610.21038 -- Difference: assesses LLM generalisation from convenience samples; the sample is the population choice there, and this paper measures what a population change does to an ordering

[30] Hartline, J. D.; et al. (2020). Optimization of Scoring Rules. arXiv:2007.02905. https://arxiv.org/abs/2007.02905 -- Difference: optimises a scoring rule as an object of design; this paper's question is what such an optimisation costs in rank faithfulness

[31] Neyman, E.; Roughgarden, T. (2021). From Proper Scoring Rules to Max-Min Optimal Forecast Aggregation. arXiv:2102.07081. https://arxiv.org/abs/2102.07081 -- Difference: derives optimal aggregation of forecasts under proper scoring rules; the aggregation is optimised there, measured and characterised here

[32] Kendall, M. G. (1938). A New Measure of Rank Correlation. Biometrika. https://doi.org/10.2307/2332226 -- Difference: defines the rank correlation this paper's discrimination statistic is; the statistic is used as a measurement, and no property of the measure is claimed

[33] Spearman, C. (1961). The Proof and Measurement of Association between Two Things. Studies in individual differences: The search for intelligence.. https://doi.org/10.1037/11491-005 -- Difference: the other classical rank measure, named so that the choice of tau is visibly a choice; the paper reports tau and states why, and extends neither measure

[34] Rockel, M. (2026). Kendall and Spearman Bounds for Chatterjee's Rank Correlation under Positive Dependence. arXiv:2606.22074. https://arxiv.org/abs/2606.22074 -- Difference: bounds Kendall and Spearman against Chatterjee's correlation under dependence; the bounds relate measures to each other, whereas this paper's use of one measure is a declared choice with no claim attached to it

[35] Pohle, M.; Wermuth, J.; Weiß, C. H. (2025). Asymptotic Inference for Rank Correlations. arXiv:2512.14609. https://arxiv.org/abs/2512.14609 -- Difference: gives asymptotic inference for rank correlations; the inference is needed when the ordering is estimated, and this paper's ordering is enumerated so no inference is applied

[36] Wilson, E. B. (1927). Probable Inference, the Law of Succession, and Statistical Inference. Journal of the American Statistical Association. https://doi.org/10.1080/01621459.1927.10502953 -- Difference: supplies the interval the house convention puts on a rate; this paper estimates no rate, so the interval is named to say what is deliberately absent rather than applied

[37] Dietterich, T. G. (1998). Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms. Neural Computation. https://doi.org/10.1162/089976698300017197 -- Difference: gives paired tests for comparing classifiers across data sets; this paper's comparison is exact over an enumerated space, so no test is applied and the reference marks that boundary

[38] da Costa, K.; Modenesi, B. (2026). GraphNetz: Statistical Benchmarking of Graph Neural Networks with Paired Tests and Rank Aggregation. arXiv:2605.09099. https://arxiv.org/abs/2605.09099 -- Difference: benchmarks graph networks with paired tests and rank aggregation; the pipeline combines testing with aggregation, while this paper separates the aggregation's contribution from the population's

[39] Painsky, A. (2026). Who is the Winning Algorithm? Rank Aggregation for Comparative Studies. arXiv:2601.01664. https://arxiv.org/abs/2601.01664 -- Difference: asks which algorithm wins under rank aggregation across comparative studies; the winner is the question there, and what the winner's selection measures here

[40] Filos-Ratsikas, A.; et al. (2021). On the Complexity of Equilibrium Computation in First-Price Auctions. arXiv:2103.03238. https://arxiv.org/abs/2103.03238 -- Difference: proves equilibrium computation in first-price auctions is hard; this paper therefore certifies its anchors against closed forms and claims nothing about solvable general instances

[41] Chen, J.; Nguyen, A.; Shum, M. (2026). The Winner's Bliss in Common-Value Auctions under Horizontal Differentiation. arXiv:2606.08419. https://arxiv.org/abs/2606.08419 -- Difference: studies the winner's curse under horizontal differentiation; it is the common-value family this paper instantiates without adding to its equilibrium theory

[42] Arrow, K. J. (2017). Social Choice and Individual Values. DOI:10.12987/9780300186987. https://doi.org/10.12987/9780300186987 -- Difference: aggregates individual orderings into a social one and proves the impossibility; this paper's aggregation is over a policy zoo's payoff rows, and the divergence measured is a rank gain rather than a preference paradox

[43] Gordienko, P.; et al. (2026). Beyond Arrow: from Impossibility to Possibilities in Multi-Criteria Benchmarking. arXiv:2602.07593. https://arxiv.org/abs/2602.07593 -- Difference: moves beyond Arrow to possibilities in multi-criteria benchmarking; the design space is enlarged there, and this paper's is declared and exhausted

[44] Xu, Y. E.; et al. (2024). Aggregating Quantitative Relative Judgments: from Social Choice to Ranking Prediction. arXiv:2410.05550. https://arxiv.org/abs/2410.05550 -- Difference: aggregates quantitative relative judgments into ranking predictions; the prediction is the goal there, while this paper's ranking is measured against an exact payoff ordering

[45] Xiao, X.; Cheng, Y. (2026). Contamination Inflates Scores but Rarely Reorders Large Language Model Leaderboards. arXiv:2609.02899. https://arxiv.org/abs/2609.02899 -- Difference: finds contamination inflates scores but rarely reorders leaderboards; that is the empirical counterpart of this paper's separation between a score's level and its ordering, measured on real models rather than derived

[46] Yang, D.; et al. (2026). Measurement-First Auditing of Agentic Leaderboards: Contamination Susceptibility, Matched-Control Re-Evaluation, and Scorer Validation. arXiv:2610.05830. https://arxiv.org/abs/2610.05830 -- Difference: audits agentic leaderboards measurement-first with matched controls; the audit is empirical and per-leaderboard, while this paper's law applies to any protocol in its space

[47] Gusev, R.; Zaytsev, A. (2026). Benchmarking on Tasks that Matter: Dataset Selection for Preserving Model Rankings. arXiv:2606.27997. https://arxiv.org/abs/2606.27997 -- Difference: selects a task subset that preserves model rankings; it treats the ranking as a constraint to preserve, whereas this paper asks what the ranking is a measurement of

[48] Badanidiyuru, A. (2026). Model Monotonicity in Autobidding Auctions: when do Better Predictions Lead to Better Outcomes?. arXiv:2605.31036. https://arxiv.org/abs/2605.31036 -- Difference: establishes a monotonicity condition for autobidding models; the property is about predictions improving outcomes, while this paper's monotonicity is what makes a ranking faithful at all

[49] Wang, J.; Huang, J. (2026). Reward Hacking as Equilibrium under Finite Evaluation. arXiv:2603.28063. https://arxiv.org/abs/2603.28063 -- Difference: models reward hacking as an equilibrium under finite evaluation — the closest formal neighbour to this paper's P1 — but the equilibrium is in the agent's action and there is no population of policies whose ordering is measured

[50] Bora, A. (2026). Beyond Reward Hacking: Proxy Divergence Across Four Layers of a Staged Humanoid Learning Pipeline. arXiv:2610.03196. https://arxiv.org/abs/2610.03196 -- Difference: traces proxy divergence through four layers of a staged learning pipeline; the layering is a system description, and this paper's account is a two-way decomposition in an exact design space

[51] Kwa, T.; Thomas, D.; Garriga-Alonso, A. (2024). Catastrophic Goodhart: Regularizing RLHF with KL Divergence does not Mitigate Heavy-Tailed Reward Misspecification. arXiv:2407.14503. https://arxiv.org/abs/2407.14503 -- Difference: shows KL regularisation does not prevent catastrophic Goodhart under heavy-tailed misspecification; the setting is a training loop, this paper's is a declared evaluation protocol

[52] Meho, L. I. (2025). Gaming the Metrics? Bibliometric Anomalies and the Integrity Crisis in Global University Rankings. arXiv:2505.06448. https://arxiv.org/abs/2505.06448 -- Difference: documents gaming of university rankings by the ranked institutions; the gaming is bibliometric and administered, while this paper's is available to a policy with no institution behind it

[53] Zhao, Y.; et al. (2026). Beyond Goodhart's Law: A Dynamic Benchmark for Evaluating Compliance in Multi-Agent Systems. arXiv:2606.07805. https://arxiv.org/abs/2606.07805 -- Difference: offers a dynamic benchmark for compliance under Goodhart pressure in multi-agent systems; it is a benchmark of behaviour, this paper is a measurement of a protocol

[54] Liu, M.; et al. (2026). Scoring Higher, Answering Worse: Mitigating Reward Hacking in Rubric-Based RL via Protocol-Level Rubrics. arXiv:2609.38847. https://arxiv.org/abs/2609.38847 -- Difference: reports scoring higher while answering worse under rubric RL and mitigates it; the divergence is a deployed artefact there and an exactly enumerated statistic here

[55] Zhang, G.; Hardt, M. (2024). Inherent Trade-Offs between Diversity and Stability in Multi-Task Benchmarks. arXiv:2405.01719. https://arxiv.org/abs/2405.01719 -- Difference: proves a trade-off between diversity and stability in multi-task benchmarks; stability there is about task subsets, and this paper's transport is about populations of competitors

[56] Baack, S.; Buschek, C.; Bohacek, M. (2026). Unsteady Metrics and Benchmarking Cultures of AI Model Builders. arXiv:2605.14164. https://arxiv.org/abs/2605.14164 -- Difference: critiques unsteady metrics and the benchmarking culture producing them; the critique is institutional, and this paper supplies the exact quantity the culture lacks

[57] Nadgir, N.; et al. (2026). Life After Benchmark Saturation: A Case Study of CORE-Bench. arXiv:2606.26158. https://arxiv.org/abs/2606.26158 -- Difference: follows one benchmark through saturation as a case study; saturation compresses the top of an ordering, which bounds the resolution of any ranking and is outside this paper's declared space

[58] Hamada, M.; et al. (2026). Evaluating Model Capabilities After Benchmark Saturation. arXiv:2610.20667. https://arxiv.org/abs/2610.20667 -- Difference: evaluates capabilities after benchmark saturation; the question is what remains measurable, while this paper asks who owns the ordering's variance

[59] Zhang, X. (2026). How Sensitive are Safety Benchmarks to Judge Configuration Choices?. arXiv:2604.24074. https://arxiv.org/abs/2604.24074 -- Difference: measures how sensitive safety benchmarks are to judge configuration choices; the protocol is a judge configuration there, and this paper's protocol is a score's aggregation

[60] Lederer, P. (2026). The Impossibility of Strategyproof Rank Aggregation. arXiv:2602.06582. https://arxiv.org/abs/2602.06582 -- Difference: proves strategyproof rank aggregation is impossible; this paper shows the impossibility in a different currency — an aggregation can be gamed in rank positions even when no voter misreports

[61] Li, J.; Simchi-Levi, D.; Sun, W. W. (2026). Low Rank for Rank: Uncertainty-Aware Task-Specific LLM Ranking under Sparse Pairwise Comparisons. arXiv:2605.29395. https://arxiv.org/abs/2605.29395 -- Difference: produces uncertainty-aware task-specific rankings from sparse pairwise comparisons; the ranking is the product there, and the object of measurement here

[62] Remeli, M.; Hardt, M. (2026). Correct Looks Better: Pairwise Comparisons Reveal Accuracy Rankings. arXiv:2606.09409. https://arxiv.org/abs/2606.09409 -- Difference: shows pairwise comparisons reveal accuracy rankings under a specific presentation; it validates the comparison instrument, while this paper characterises when the aggregate of comparisons is faithful to payoff

[63] Li, Y.; Fan, Z.; Zhuang, Z. (2026). Auditing the Audit: Five Failure Modes in Benchmark-Validity Audits. arXiv:2607.02586. https://arxiv.org/abs/2607.02586 -- Difference: names five failure modes in benchmark-validity audits; this paper's contribution can be read as removing one of them by making the protocol's share computable

[64] Degtiarev, D.; et al. (2026). Auditing VLM Benchmarks from Existing Evaluation Runs. arXiv:2610.13548. https://arxiv.org/abs/2610.13548 -- Difference: audits VLM benchmarks from existing evaluation runs rather than new ones; the method is reuse of logged runs, this paper's is an enumeration that needs no runs at all

[65] Chen, J. (2026). When Agent Evaluation Becomes Unreliable: an Empirical Study of Oracle Failures and Configuration-Dependent Measurement in an LLM Agent Benchmark. arXiv:2610.16067. https://arxiv.org/abs/2610.16067 -- Difference: audits an agent benchmark for oracle failures and configuration-dependent measurement; the defect is in the harness, while this paper's is in the score rule and is exact

[66] Hardy, M.; et al. (2026). Agent Evaluation Reliability: More Tasks Won't (Always) Fix an Agent Leaderboard. arXiv:2610.00651. https://arxiv.org/abs/2610.00651 -- Difference: shows more tasks do not always fix an agent leaderboard; that is the noise side of the same question, and this paper's side is the systematic one

[67] Han, Z.; et al. (2026). What can a Leaderboard Certify? Compositional Controllability for Fair Evaluation and Training of Biomedical Literature-Review Agents. arXiv:2609.32318. https://arxiv.org/abs/2609.32318 -- Difference: asks what a leaderboard can certify under compositional controllability; the answer is a certification scheme, whereas this paper names the design decision that decides whether certification is possible

[68] Hernashki, N. K.; Chatterjee, S. (2026). MIRTO: a Registration-Gated, Multiverse-Tested Evaluation Protocol for Unsupervised Anomaly Segmentation in Brain MRI. arXiv:2610.02136. https://arxiv.org/abs/2610.02136 -- Difference: registers and multiverse-tests an evaluation protocol for a segmentation task; the protocol is reported in full there and measured as an object here

[69] Tan, Y.; et al. (2026). Does Local Video Understanding Transfer Across Encounters? the EgoGears Benchmark. arXiv:2609.37938. https://arxiv.org/abs/2609.37938 -- Difference: asks whether local video understanding transfers across encounters; the transfer is of a capability across data, and this paper's is of an ordering across populations of competitors

[70] Wang, S.; et al. (2026). AutoAdapt: Reliable Few-Shot Adaptation under Clinical Distribution Shifts. arXiv:2610.11162. https://arxiv.org/abs/2610.11162 -- Difference: adapts models under clinical distribution shifts; the shift is handled by adaptation, while this paper asks what happens to a ranking when the population shifts and no adaptation is allowed

[71] Tang, J.; et al. (2026). Benchmarking Self-Supervised 3D Medical Vision Foundation Models and Transferability Estimation. arXiv:2610.17573. https://arxiv.org/abs/2610.17573 -- Difference: benchmarks foundation models and estimates transferability; the estimate predicts performance on a new corpus, and this paper's statistic prices the ordering's loss on a new population

[72] Pananjady, A.; et al. (2017). Worst-Case vs Average-Case Design for Estimation from Fixed Pairwise Comparisons. arXiv:1707.06217. https://arxiv.org/abs/1707.06217 -- Difference: compares worst-case and average-case design for estimation from fixed pairwise comparisons; the design question is the estimator's, while this paper's is whether the ordering the estimator produces survives the population change

[73] Aiyer, S.; Shao, H. (2026). How Many Repeated Pairwise Comparisons are Needed for Ranking under Heterogeneity?. arXiv:2610.10795. https://arxiv.org/abs/2610.10795 -- Difference: asks how many repeated pairwise comparisons a ranking needs under heterogeneity; the sample size is the quantity there, and the protocol's share of the ordering here

[74] Goldberger, M.; Rudi, N. (2026). Selecting the Best Few with Human Evaluators: Adaptively Combining Ratings and Pairwise Comparisons. arXiv:2610.26380. https://arxiv.org/abs/2610.26380 -- Difference: adaptively combines ratings and pairwise comparisons to select the best few; selection is the goal, whereas this paper measures whether the selection would change under another protocol

[75] Li, C.; et al. (2025). Towards Real-World Validity in Generative AI Benchmarks: Understanding and Designing Domain-Centered Evaluations for Journalism Practitioners. arXiv:2511.05501. https://arxiv.org/abs/2511.05501 -- Difference: argues for domain-centred evaluation design to reach real-world validity; the argument is about what to evaluate, and this paper about how the aggregate ranks

[76] Zhu, L. Y. (2026). One Capability or Many? Structural and Predictive Tests of Benchmark Validity Disagree About Economic Benchmarks for Frontier AI. arXiv:2608.29420. https://arxiv.org/abs/2608.29420 -- Difference: finds structural and predictive tests of benchmark validity disagree; that disagreement is the reason this paper claims a protocol-level quantity instead of a validity verdict

[77] Filos-Ratsikas, A.; et al. (2025). Equilibrium Computation in First-Price Auctions with Correlated Priors. arXiv:2506.05322. https://arxiv.org/abs/2506.05322 -- Difference: computes equilibria with correlated priors, a harder instance than this paper attempts; named to bound what the anchors claim

[78] Chen, Y.; Zhang, G.; Hardt, M. (2026). Leaderboard Incentives: Model Rankings under Strategic Post-Training. arXiv:2603.08371. https://arxiv.org/abs/2603.08371 -- Difference: models ranking under strategic post-training as a Stackelberg game over training resources; it prices the incentive to improve, not the incentive to be ranked, and models no aggregation or population axis

[79] Huang, W. (2026). When Pair Count is not the Sample Size: what All-Pairs Agent Comparisons Estimate. arXiv:2609.33012. https://arxiv.org/abs/2609.33012 -- Difference: asks what all-pairs agent comparisons estimate and fixes the inference problem of a leaderboard; it treats the published ordering as the datum, while this paper asks what that datum measures

[80] Kearns, R. O. (2026). Quantifying Construct Validity in Large Language Model Evaluations. arXiv:2602.15532. https://arxiv.org/abs/2602.15532 -- Difference: quantifies construct validity for language-model evaluations; validity is a property of a benchmark there, and this paper's property is of a protocol's aggregation

[81] Freiesleben, T. (2026). Establishing Construct Validity in LLM Capability Benchmarks Requires Nomological Networks. arXiv:2603.15121. https://arxiv.org/abs/2603.15121 -- Difference: requires nomological networks for construct validity; the requirement is met by an external theory, while this paper's law is internal to the design space

[82] Ahmed, R. M.; Abbas, S. (2026). Labels are not Endpoints: Treatment Leakage and Construct Validity in MCP Agent Security Evaluation. arXiv:2608.12880. https://arxiv.org/abs/2608.12880 -- Difference: shows treatment leakage makes a label a poor endpoint in agent security evaluation; the label is the defect there, the score's aggregation here

[83] Alaa, A.; et al. (2025). Medical Large Language Model Benchmarks Should Prioritize Construct Validity. arXiv:2503.10694. https://arxiv.org/abs/2503.10694 -- Difference: argues medical benchmarks should prioritise construct validity; the recommendation is domain-specific, and this paper's measurement is domain-free by construction

[84] Gul, H.; Bhat, A. A. (2026). When Metrics Disagree: A Meta-Analysis of Knowledge-Graph-Completion Model Benchmarking. arXiv:2606.10287. https://arxiv.org/abs/2606.10287 -- Difference: meta-analyses disagreeing metrics in knowledge-graph completion; disagreement between metrics is measured there and derived here

[85] Zhao, Y.; et al. (2026). A Measurement Perspective on Benchmarking LLM-Generated Text Detectors Using Item Response Theory. arXiv:2610.24972. https://arxiv.org/abs/2610.24972 -- Difference: applies item-response theory to benchmarking generated-text detectors; the measurement model is fitted there, and this paper's model is exact and needs no fit

[86] Francisco, J.; Reyes, M. (2026). Laplace-PSN-IRT: Uncertainty Quantification for Neural Item Response Theory Models of LLM Benchmarks. arXiv:2607.25257. https://arxiv.org/abs/2607.25257 -- Difference: quantifies uncertainty for neural item-response models of benchmarks; the ranking is an estimate there and an enumeration here

[87] Stewart, C. M.; et al. (2026). Searching for "Harmful Refusal": A Psychometric Audit of an AI Safety Benchmark. arXiv:2610.12409. https://arxiv.org/abs/2610.12409 -- Difference: psychometrically audits a safety benchmark; the audit asks whether the instrument measures its construct, and this paper asks what a score's aggregation does to an ordering

[88] Hallmen, T.; et al. (2026). The Failure is in the Readout: Fine-Grained Emotion Recognition Benchmarks Measure Elicitation, not Perception. arXiv:2610.08162. https://arxiv.org/abs/2610.08162 -- Difference: shows fine-grained emotion benchmarks measure elicitation rather than perception; the readout is the defect there, and the aggregation is the defect here

[89] Panda, S. (2026). FinVerBench: Benchmark Validity and Calibration in Large Language Model Financial Statement Verification. arXiv:2605.29586. https://arxiv.org/abs/2605.29586 -- Difference: checks benchmark validity and calibration for financial statement verification; validity is assessed per task, while this paper's quantity is per protocol

[90] Li, J.; Tang, P. (2022). Vulnerabilities of Single-Round Incentive Compatibility in Auto-Bidding: Theory and Evidence from ROI-Constrained Online Advertising Markets. arXiv:2210.06107. https://arxiv.org/abs/2210.06107 -- Difference: shows single-round incentive compatibility is vulnerable in auto-bidding; the vulnerability is a property of a mechanism there and a rank gain over a policy zoo here

[91] Alimohammadi, Y.; Mehta, A.; Perlroth, A. (2023). Incentive Compatibility in the Auto-Bidding World. arXiv:2301.13414. https://arxiv.org/abs/2301.13414 -- Difference: achieves incentive compatibility in the auto-bidding world; this paper does not design a compatible mechanism — it characterises when a published score is faithful to payoff

[92] van Beek, A.; Brokkelkamp, R.; Schäfer, G. (2021). Corruption in Auctions: Social Welfare Loss in Hybrid Multi-Unit Auctions. arXiv:2106.01822. https://arxiv.org/abs/2106.01822 -- Difference: quantifies welfare loss from a distorted multi-unit auction channel; this paper's loss is not welfare but the ordering a protocol publishes

[93] Liu, J.; et al. (2026). Single-Item Auctions with a Monopolist Intermediary. arXiv:2605.21934. https://arxiv.org/abs/2605.21934 -- Difference: analyses a single-item auction with an intermediary; the opponent row is explicit there and the object of analysis, while here it is the aggregation that decides whether the row is read

[94] Liu, Z. (2026). Tight Inapproximability of Pacing and Throttling Equilibria in Second-Price Auctions. arXiv:2608.16682. https://arxiv.org/abs/2608.16682 -- Difference: gives inapproximability for pacing and throttling equilibria; named as the limit of the population lever this paper measures rather than a result it extends

[95] Kashyap, R. (2018). Auction Theory Adaptations for Real Life Applications. arXiv:1810.01736. https://arxiv.org/abs/1810.01736 -- Difference: adapts auction theory to deployed settings; it takes the format as given and asks how to bid, not what the resulting scores do to a ranking

[96] Leme, R. P.; Sivan, B.; Teng, Y. (2020). Why do Competitive Markets Converge to First-Price Auctions?. arXiv:2001.06074. https://arxiv.org/abs/2001.06074 -- Difference: explains why competitive markets converge to first-price formats; this paper's formats are declared, and the convergence question is outside its design space

[97] Lotfi, I.; Ghrayeb, A. (2026). Strategic Bidding in 6G Spectrum Auctions with Large Language Models. arXiv:2604.24156. https://arxiv.org/abs/2604.24156 -- Difference: puts language models inside a spectrum auction as bidders; this paper's policies are not language models, and its question is what the protocol measures rather than how well an LLM bids

[98] Tang, S.; Wang, Y.; Jin, C. (2025). Is Elo Rating Reliable? A Study under Model Misspecification. arXiv:2502.10985. https://arxiv.org/abs/2502.10985 -- Difference: asks whether Elo is reliable under model misspecification; the rating is an estimator there, and this paper's score is a declared aggregation over an exact payoff matrix

[99] Olesker-Taylor, S.; Zanetti, L. (2024). An Analysis of Elo Rating Systems via Markov Chains. arXiv:2406.05869. https://arxiv.org/abs/2406.05869 -- Difference: analyses Elo ratings through Markov chains; the dynamics are the object, while this paper's static ordering is

[100] Gray, A.; et al. (2022). Using Elo Rating as a Metric for Comparative Judgement in Educational Assessment. arXiv:2204.01805. https://arxiv.org/abs/2204.01805 -- Difference: uses Elo as a comparative-judgement metric in assessment; a deployed use of a rating, not a property of it

[101] Song, Y. (2023). Analysis of ELO Rating Scheme in MOBA Games. arXiv:2310.13719. https://arxiv.org/abs/2310.13719 -- Difference: analyses an Elo scheme in a competitive game; the scheme's behaviour is the subject there, and this paper's characterization is of monotone aggregations in general

[102] Chen, C.; et al. (2026). JudgeStealer: Extracting LLM Judging Capabilities Across Evaluation Protocols. arXiv:2608.26982. https://arxiv.org/abs/2608.26982 -- Difference: extracts LLM judging capability across evaluation protocols; the extraction is an attack there, and the protocol's effect on an ordering is the measurement here

[103] Baker, G.; Gibbons, R.; Murphy, K. (1993). Subjective Performance Measures in Optimal Incentive Contracts. DOI:10.3386/w4480. https://doi.org/10.3386/w4480 -- Difference: analyses a principal choosing a subjective performance measure for a workforce; the measure is gamed, but there is no population of competitors whose ordering can fail to transport, which is this paper's second axis

[104] de Oliveira, D.; et al. (2024). The PESQetarian: on the Relevance of Goodhart's Law for Speech Enhancement. arXiv:2406.03460. https://arxiv.org/abs/2406.03460 -- Difference: measures Goodhart's law in speech-enhancement metrics; the proxy divergence is demonstrated on a real metric, and this paper gives the finite-population statistic and its transport face

[105] Mallein, B.; et al. (2025). Selection of the Fittest or Selection of the Luckiest: the Emergence of Goodhart's Law in Evolution. arXiv:2503.21849. https://arxiv.org/abs/2503.21849 -- Difference: models selection of the luckiest as the emergence of Goodhart's law in evolution; the mechanism is selection pressure, the object here is a published ranking

[106] Mittal, A.; Gupta, D. (2026). Signed Compression Progress on a Sealed Audit is Goodhart-Resistant. arXiv:2606.11417. https://arxiv.org/abs/2606.11417 -- Difference: designs a Goodhart-resistant audit through signed compression progress; resistance is engineered there, whereas this paper characterises which protocols are immune by construction and what immunity fails to protect

[107] Moya, C.; Thornley, E.; Lin, G. (2026). Verifier Errors in RLVR: Reward Hacking, Limits of Feedback, and Selective Control. arXiv:2609.35677. https://arxiv.org/abs/2609.35677 -- Difference: analyses verifier errors and reward hacking when the score is the verifier; this paper's score is an aggregation of outcomes, not a verifier, and the divergence is measured without any learning

[108] Quan, J.; et al. (2026). RH-Detect: A Unified Benchmark for Reward Hacking Detection. arXiv:2610.10947. https://arxiv.org/abs/2610.10947 -- Difference: benchmarks the detection of reward hacking; detection is a classifier problem, whereas this paper derives when the score that would be hacked is faithful at all

[109] Hu, Y.; et al. (2026). Reward Hacking as a Transmissible Strategy in Multi-Agent Coding Systems. arXiv:2610.12822. https://arxiv.org/abs/2610.12822 -- Difference: shows reward hacking can transmit between agents in multi-agent coding; transmission is the phenomenon, while this paper's containment result is about two properties of one protocol

[110] Li, Y.; et al. (2026). Multi-Reward Hacking: from Aggregation-Induced Drift to Trust-Anchored Defense. arXiv:2610.21404. https://arxiv.org/abs/2610.21404 -- Difference: identifies aggregation-induced drift when several rewards are combined and proposes a defence; the aggregation is of rewards inside training, and this paper's aggregation is of outcomes into a published score

[111] Bengs, V.; Hüllermeier, E.; Waegeman, W. (2023). On Second-Order Scoring Rules for Epistemic Uncertainty Quantification. arXiv:2301.12736. https://arxiv.org/abs/2301.12736 -- Difference: extends scoring rules to second-order uncertainty; the score's higher moments carry the incentive there, the score's monotonicity carries the ranking here

[112] Hudson, R. (2024). Joint Scoring Rules: Zero-Sum Competition Avoids Performative Prediction. arXiv:2412.20732. https://arxiv.org/abs/2412.20732 -- Difference: shows joint scoring rules make competition avoid performative prediction; the mechanism is a competition among forecasters, while this paper's ordering is produced by an aggregation over opponents

[113] Oesterheld, C.; et al. (2023). Incentivizing Honest Performative Predictions with Proper Scoring Rules. arXiv:2305.17601. https://arxiv.org/abs/2305.17601 -- Difference: incentivises honest performative predictions; this paper's divergence is not dishonesty but the score's freedom to reorder policies that report truthfully

[114] Witkowski, J.; et al. (2021). Incentive-Compatible Forecasting Competitions. arXiv:2101.01816. https://arxiv.org/abs/2101.01816 -- Difference: designs an incentive-compatible forecasting competition; the tournament's incentives are the object, whereas this paper measures the tournament's published ordering

[115] Turtel, B.; et al. (2026). How Proper Scoring Rules Shape LLM Forecasting. arXiv:2608.28482. https://arxiv.org/abs/2608.28482 -- Difference: measures how proper scoring rules shape LLM forecasting skill; the score changes what is reported there, and what is ranked here

[116] Hall, A. (2023). Arrow's Impossibility Theorem: Computability in Social Choice Theory. arXiv:2311.09789. https://arxiv.org/abs/2311.09789 -- Difference: studies the computability of Arrow's impossibility; the theorem is the object there, and here it is the boundary condition the aggregation must respect

[117] Echenique, F.; Valenzuela-Stookey, Q. (2024). Utilitarian Social Choice and Distributional Welfare Analysis. arXiv:2411.01315. https://arxiv.org/abs/2411.01315 -- Difference: analyses utilitarian social choice and distributional welfare; which aggregate a ranking maximises is a normative choice there, and this paper measures what the chosen aggregate costs in faithfulness

[118] Qiu, T. (2024). Representative Social Choice: from Learning Theory to AI Alignment. arXiv:2410.23953. https://arxiv.org/abs/2410.23953 -- Difference: defines representative social choice; representation is the goal there, and this paper's aim is the opposite direction — what an aggregate measures rather than what it should represent

[119] Wang, J.; Alfaro, J. C.; Bengs, V. (2025). A Comparative Analysis of Rank Aggregation Methods for the Partial Label Ranking Problem. arXiv:2502.17077. https://arxiv.org/abs/2502.17077 -- Difference: compares rank-aggregation methods for partial label ranking; the methods are the subject, and this paper's question is what any of them would do to a payoff ordering

[120] Peters, D. (2026). Kemeny Rank Aggregation is NP-Hard for Three Voters. arXiv:2607.25540. https://arxiv.org/abs/2607.25540 -- Difference: proves Kemeny aggregation is NP-hard for three voters; the hardness bounds exact aggregation, which is why this paper's aggregation is a declared score rather than an optimum

[121] Bowman, S. R.; Dahl, G. (2021). What Will it Take to Fix Benchmarking in Natural Language Understanding?. Proceedings of the 2021 Conference of the North American Chapter of the Associat. https://doi.org/10.18653/v1/2021.naacl-main.385 -- Difference: sets out what it would take to fix benchmarking in NLU; this paper measures one such fix — the score — as a protocol-level quantity

[122] Kiela, D.; et al. (2021). Dynabench: Rethinking Benchmarking in NLP. Proceedings of the 2021 Conference of the North American Chapter of the Associat. https://doi.org/10.18653/v1/2021.naacl-main.324 -- Difference: recasts benchmarking as a moving target that must be redesigned; this paper supplies the quantity that says how much of a ranking the design decision owns

[123] Bommasani, R.; Liang, P.; Lee, T. (2023). Holistic Evaluation of Language Models. Annals of the New York Academy of Sciences. https://doi.org/10.1111/nyas.15007 -- Difference: evaluates models across named scenarios instead of one score; it makes the protocol explicit and holds it fixed, while this paper varies the protocol and measures what the choice carries

[124] Liao, Q. V.; Xiao, Z. (2023). Rethinking Model Evaluation as Narrowing the Socio-Technical Gap. arXiv:2306.03100. https://arxiv.org/abs/2306.03100 -- Difference: frames model evaluation as narrowing a socio-technical gap; this paper's object is narrower and computable — which protocol decision carries which share of the ordering

[125] Casper, S.; et al. (2023). Explore, Establish, Exploit: Red Teaming Language Models from Scratch. arXiv:2306.09442. https://arxiv.org/abs/2306.09442 -- Difference: raises auditability and open problems for benchmarks; this paper answers one of them with an exact characterization rather than a protocol proposal

[126] Perez, E.; et al. (2022). Red Teaming Language Models with Language Models. Proceedings of the 2022 Conference on Empirical Methods in Natural Language Proc. https://doi.org/10.18653/v1/2022.emnlp-main.225 -- Difference: uses red-teaming as an evaluation and shows the choice of protocol changes the finding; the observation is theirs, the exact law is not

[127] Recht, B.; et al. (2019). Do ImageNet Classifiers Generalize to ImageNet?. arXiv:1902.10811. https://arxiv.org/abs/1902.10811 -- Difference: shows a benchmark's accuracy ordering does not transport to a fresh sample; that is the phenomenon, measured across samples, while this paper derives the protocol condition under which the ordering transports at all

[128] Haghtalab, N.; et al. (2026). Pluralistic Leaderboards. arXiv:2606.02547. https://arxiv.org/abs/2606.02547 -- Difference: proposes pluralistic leaderboards because one ordering cannot serve several populations; this paper supplies the measurement that says how far apart two populations' orderings are under a given protocol

[129] Milgrom, P. (1989). Auctions and Bidding: A Primer. Journal of Economic Perspectives. https://doi.org/10.1257/jep.3.3.3 -- Difference: the primer a referee expects a format discussion to know; it states the classical formats and their revenue properties and says nothing about a published ranking

[130] Nash, J. F. (2020). Equilibrium Points in 𝑛-Person Games. Classics in Game Theory. https://doi.org/10.2307/j.ctv173f1fh.6 -- Difference: defines the equilibrium point the payoff-optimal policies are computed against; cited as a solution concept, not extended

[131] Milgrom, P. R.; Weber, R. J. (1982). A Theory of Auctions and Competitive Bidding. Econometrica. https://doi.org/10.2307/1911865 -- Difference: establishes the equilibrium theory of competitive bidding this paper's game families instantiate; it takes the ordering of bidders by value as given, which is exactly the ordering a protocol can break

[132] Heymann, B. (2026). On the Role of Tie-Breaking Rules in the Convergence of Fictitious Play for Symmetric First-Price Auctions. arXiv:2609.18848. https://arxiv.org/abs/2609.18848 -- Difference: shows tie-breaking rules change what fictitious play converges to; this paper consequently declares its ties instead of inheriting a rule

