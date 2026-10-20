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

## 1 Introduction: the protocol is a confound nobody manipulates

Benchmarks for strategic agents are now published at a rate that outstrips their methodology
[1,2,3]. In the
most recent measurement we are aware of, ERPBench evaluates the same 100 fixed problems in two matched
competitive ecologies and finds that the two ecologies identify the **same task-level winner on only
21 of 100 problems** <!-- n: external(arXiv:2609.04667) --> — the ranking is not a property of the
agents alone, and the paper says so [4]. But the paper holds its protocol fixed and varies the ecology, so
the protocol remains what it has always been in this literature: an input, never a treatment.

That is the gap we measure into. A strategic evaluation has three moving parts — a game with a payoff
structure, a population of policies, and a **protocol** that selects opponents, pairs policies, and
aggregates outcomes. Benchmarks vary the first two and report a ranking as if the third were neutral
[5,6,7,8].
It is not. The protocol decides which policies are compared, and the score decides what "better" means
[9,10];
when the score is not monotone in the policy's own payoff, the ranking can order policies by something
else entirely, and the paper that publishes it will have no way to notice
[11,12,13,14].

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
holds [15,16,17,18].

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
[19,20,21]. Values are drawn from a finite
integer grid and every payoff is computed as an exact `Fraction` sum over opponents' value profiles, so
no result in this paper depends on a floating-point tie or a seed
[22]. There is no sampling anywhere in
the instrument: the design space is enumerated. <!-- n: v4.games -->

**Policies.** A zoo of eight linear-shading policies (shade factor, plus the payoff-optimal and
payoff-worst extremes) [23,24]. The zoo is deliberately the simplest family for which "which policy is better"
is a well-defined question, so that any rank-payoff divergence we find cannot be blamed on a
mis-specified policy. <!-- n: v4.policies -->

**Populations.** Four declared value distributions — uniform, weak skew, strong skew, capped strong —
giving six population pairs per game [25,26]. <!-- n: v4.populations, v4.population_pairs -->

**Protocols.** Nineteen score rules across three bands, spanning profile readers and row readers,
monotone and saturating and decreasing — the families the score-rule literature separates
[17,27,28]. The space includes the aggregations real benchmarks publish
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
  the zoo [29,30,31,32]. `tau = 1` is faithful, `tau = -1` is the exact reverse.
- **Transport** `T_raw` and `T_excess`: the share of pairwise orderings lost when the population
  changes, raw and net of the payoff ordering's own transport loss. The second is the protocol's
  contribution; the first includes a baseline every protocol pays. We report both and never conflate
  them (§8).

**Nothing here is estimated from a sample**, so the interval machinery a sampled evaluation needs — a
Wilson interval for a rate, paired tests across tasks, a rank aggregate with its own error — is named
rather than used [33,34,35,36]. That is a property of the design,
not a shortcut: every number in §4–§8 is an exact rational over an enumerated space, and the paper
therefore reports differences and never significance.

**Ground truth by construction.** The instrument is checked against theory rather than against itself.
The symmetric first-price equilibrium has a closed form and is recovered exactly
[21,37]; the second-price
auction's weakly dominant bid is recovered exactly [19]; the common-value n=4 game has **no** certified
anchor, and we state that as an absence rather than filling it [38]. Eight of nine games carry at least one
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
[39,40,41].

**Evidence.** Over 19 protocols x 9 games the law's stated band and the measured band disagree in
**0** cases. Exactly **two** designs are faithful (`mean_payoff`, `spread`), one is immune but
unfaithful (`tail_swap`, constructed), and sixteen are gameable.
<!-- n: v4.law_mismatches, v4.faithful_protocols, v4.band_counts -->

**The row-reading class.** Eleven of the nineteen protocols aggregate the opponent row: `win_count`,
`strict_wins`, `tie_count`, `mean_sq`, `top_half`, `worst_opp`, `best_opp`, `norm_by_best`,
`relative_pair`, `game_wins`, `champion`. **None of the eleven is faithful in a single cell**, which is
the law's sharpest prediction — these are not pathological scores but the scores benchmarks publish
[42,43,44].
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
ranking can be trusted [45].

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
paper measures [46,47]. <!-- n: v4.neg_mean.G_max, v4.neg_mean.gameable, v4.neg_mean.cells -->

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
records at the level of a single training run [48,49,50,51].
<!-- n: v0.game_wins.G_pos, v0.game_wins.cells, v0.game_wins.tau_mean_exact, v0.game_wins.tau_mean_3dp -->

![Distribution of the rank gain over all 684 cells, and its share with a positive gain in each of the nine games](figures/fig1_p1_gain.png)

*P1: the ranking can be bought. (a) the distribution of the rank gain $G$ over all 684 cells — $G=0$ (the protocol ranks the policy where its payoff puts it) in 210, $G>0$ in 474. (b) the same reading per game: the share of each game's 76 cells with $G>0$ stays between 50 and 55, so the effect is not an artefact of bidder count or auction family.*

## 5 P2: the protocol is the lever, not the population

**Registered prior (P2).** *The spread across protocols exceeds the spread across populations.*
**Outcome: confirmed**, and more strongly than we registered it: not merely larger in total, but larger
*per protocol than per population* in every game.

**The decomposition.** For each game, the gain `G` is an exact rational in every cell, so a two-way
decomposition of its total variation into protocol, population, and interaction terms is exact — no
estimation, no residual to be attributed by hand [35,44]. In all **9 of 9** games the protocol's mean square
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
number was computed under [52,53,54,55,56]. The decision §7 draws follows from it.

![Mean squares of the rank gain for the protocol and the population factors in each game, with the two candidate ratios](figures/fig2_p2_lever.png)

*P2: the protocol is the lever. (a) the exact two-way decomposition of $G$ in each game, on a log scale: the protocol's mean square exceeds the population's in 9 of 9 games. (b) the two ratios a reader could compute — the mean-square ratio (the claim, 3.929x to 52.132x) and the sum-of-squares ratio, which is larger for the protocol by construction because the protocol factor has 19 levels against the population's 4.*

## 6 P3 refuted: buyable rank and fragile rank are two properties

**Registered prior (P3).** *The protocols that let a policy buy rank are the same protocols whose
ordering fails to transport* — one property, observed twice. **Outcome: refuted, with a direction.**

The refutation has three parts, and the second is the one that changes a decision.

**(i) The dominance is strict, and it is a containment rather than a tendency.** In every cell where a
policy can gain rank, the protocol's ordering is also unfaithful —
the two failures a rank aggregate can have, honest aggregation and decisive aggregation, arrive
together here [36,57,58] — so: `G > 0 => tau < 1`, with **0
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
capability behind it is are separate claims [59].
<!-- n: v4.neg_mean.G_max, v4.transport.excess_zero_set, v4.T3.reversed_by_protocol,
census.exc.rank_score -->

**(iii) The reversals are a real mode, not a rounding of "unfaithful".** **71** cells read `tau = -1` —
the exact reverse of the payoff ordering — split as 36 from `rank_score` and 35 from `neg_mean`. We
keep `tau < 1` and `tau = -1` as separate counters throughout, which is also why the choice of rank
correlation is stated rather than assumed — the measures are not interchangeable and their bounds
differ under dependence [31,32], because a single "unfaithful" count
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
runs is not the same instrument as a fresh one [60,61,62].

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
ordering is what a reader can check [8,63,64,65,43].

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
[44,25]. The question has been asked in other vocabularies — whether a measured
capability transfers across encounters, whether an adapted model survives a shift in its clinical
population, whether a transferability estimate predicts the ordering on a new corpus, and what a
convenience sample can say about the population it was drawn from
[66,67,68,26]. So the second
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
here as finite counts for that reason [69,70,71].

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
[72,73] —: the design law is a statement about
what a score must be monotone in, and that statement has no game-specific content.

**(2) `n <= 4` and a linear-shading zoo.** Four bidders and eight shade factors is a small world, chosen
because it is the smallest one in which "which policy is better" is well defined and the payoff
ordering can be computed exactly. A richer policy space could host a protocol that is faithful in our
space and not in a larger one [74,37]; the law predicts it cannot, and that prediction is testable — but we have
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

**(4) The transport arm reports one statistic per entry.** Transport is computed at the entry level
(protocol, ordered population pair), not per policy, so a protocol could pass while a particular policy
changes order. We did not measure policy-level transport; a suite that publishes per-policy comparisons
would want it, and §8's orientation theorem carries over only to the entry level as stated.

**(5) There is no real-leaderboard arm.** The natural next step — take a published leaderboard, recover
its protocol exactly, and test whether the divergence predicted here appears in its data — is not done.
It is the direction we would most like to see contested, and its absence means the paper's contribution
is a theory with an exact in-silico measurement rather than a field observation. The three works that
come closest to that arm all measure a different object with a protocol they hold fixed
[4,75,76]. The journal's
synthetic-data rule is satisfied precisely because we claim no more than that: the in-silico results
establish what protocols *can* do, and nothing about what any deployed benchmark *is* doing.

**A validity claim we deliberately do not make.** The construct-validity literature asks whether a
benchmark measures the capability it names, and answers with nomological networks, structural tests,
psychometric fits and audits of the readout rather than with a single number
[2,77,78,79,80,81,82,83,84,85,86].
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
Stackelberg game over training resources and latent quality [75]. It asks how an agent
should invest to score well; it does not model the score's aggregation, the opponent row, or what
happens to the ordering when the population changes. Our object — an in-episode policy facing a
declared score rule — is disjoint from it, and the two results are complementary rather than competing:
theirs prices the incentive to improve, ours prices the incentive to be ranked. The same distinction
runs through the auto-bidding literature, where incentive compatibility is a property of the allocation
and payment rule and the bidder's best response is the object
[87,88,24], through the payment rules a platform actually runs
[89,90,91], and through auction theory adapted to deployed formats
[92,93], and through settings in which the bidder is itself a language model
[94]. In all of it the score is a design choice whose incentive properties are
analysed; in none of it is the *published ordering* what the score is analysed for.

**Leaderboard inference.** A distinct line fixes the *statistical* reuse problem: given a published
leaderboard, what can be inferred about unseen comparisons
[76,7,58]. That work treats the published ordering as the datum. We ask
the prior question — what does the published ordering *measure* — and a result that the ordering is
partly an artefact of the score would bound what that literature's inferences can carry, which is the
sense in which §6's refutation has a consumer outside this paper. A related line models the rating
itself as an estimator with a noise floor and a misspecification risk
[95,96,97,98], and asks what a leaderboard can certify and how a
judge's own extraction can move the verdict [64,99].

**Measurement gaming in economics.** The principal's choice of measure, and the agent's response to it,
is a classical problem [100]. It supplies the intuition that a score can be gamed and
the vocabulary of distortion, but it carries no population axis: the measure is a function of the
agent's action, and the question of whether the induced ordering survives a change in the population
the measure is evaluated on does not arise in that framing. Our transport statistic is that missing
axis, and §8 shows that the classical intuition (a score that cannot be bought is a score whose
ordering holds) is false in a family of ordinary aggregations. The modern formalisations of the same
intuition are the closest neighbours to §4 and §6, and they too are stated without a population axis:
Goodhart's law given a formal statement [13,14], a proxy measured against the
goal it stands for in one instrument [101,102], a sealed audit designed to resist
gaming [103], and the reward-hacking family in which the score is a verifier and the
policy learns to satisfy the verifier instead [104,105,106,107].

**Scoring rules and aggregation as the instrument.** That a score is a designed object with declared
incentive properties is the scoring-rule literature's premise, from proper scoring rules and their
surrogates [17,27,28] through second-order and joint rules
[108,109], honest performative prediction [110] and forecasting
competitions [111] to the observation that a scoring rule shapes what a model reports
[112]. The aggregation of many such scores into one ordering is social-choice territory,
where Arrow's theorem is the boundary condition [39,113] and the responses are to
choose an aggregate deliberately — utilitarian, representative, or relative-judgement based
[114,115,41] — and where the aggregation of partial rankings is a problem
with its own methods and its own impossibility results
[116,117,57]. Our §3 law is the special case of this in which the objects
being aggregated are the rows of a payoff matrix rather than a profile of preferences.

**Benchmark design and construct validity.** The broader methodological literature on what a benchmark
measures — construct validity, contamination, and the difference between a score and the capability it
is supposed to index — motivates the enterprise; we do not claim to extend it
[118,119,120,121,122,123,124]. What we add is a
*protocol-level* quantity: not "is this benchmark valid?" but "which of this benchmark's design
decisions carries the divergence, and by how much". One strand of that literature is closer to our
result than to a validity verdict: the observation that a published ordering can be pluralistic, that
its intervals can be reported, and that a contamination that inflates every score need not reorder them
[125,42] — the last is the empirical face of §6's claim that a corruption and a
reordering are two properties.

**The auction canon, named because a referee will look for it.** The game families are textbook objects
[19,126,127] and the equilibrium concepts the anchors are checked against
are the ones the canon defines [21,128,129]. We use them the way a
measurement paper uses a ruler: nothing here extends auction theory, and none of our claims is about
auction theory rather than about what a protocol built on an auction measures. A design whose
tie-breaking is declared rather than inherited [130] is part of the same discipline.

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

1. Maria Eriksson et al. *Can We Trust AI Benchmarks? An Interdisciplinary Review of Current Issues in AI Evaluation*. arXiv:2502.06559, 2025. https://arxiv.org/abs/2502.06559
2. Andrew M. Bean et al. *Measuring what Matters: Construct Validity in Large Language Model Benchmarks*. arXiv:2511.04703, 2025. https://arxiv.org/abs/2511.04703
3. Rachel Longjohn et al. *Benchmark Data Repositories for Better Benchmarking*. arXiv:2410.24100, 2024. https://arxiv.org/abs/2410.24100
4. Xinran Zhang et al. *ERPBench: Evaluating LLM Agents for Enterprise Decision-Making Across Competitive Market Ecologies*. arXiv:2609.04667, 2026. https://arxiv.org/abs/2609.04667
5. Kawin Ethayarajh and Dan Jurafsky. *Utility is in the Eye of the User: A Critique of NLP Leaderboards*. Proceedings of the 2020 Conference on Empirical Methods in Natural Language Proc, 2020. https://doi.org/10.18653/v1/2020.emnlp-main.393
6. Hosna Oyarhoseini, Jimmy Lin and Amir-Hossein Karimi. *A Unified Perturbation Framework for Analyzing Leaderboard Stability and Manipulation*. arXiv:2605.15761, 2026. https://arxiv.org/abs/2605.15761
7. Bitya Neuhof and Yuval Benjamini. *Rank Intervals for Leaderboards: A Hierarchical Framework for Model Evaluation*. arXiv:2606.08679, 2026. https://arxiv.org/abs/2606.08679
8. Krishna Chytanya Ayyagari. *Pinned and Still Unstable: Within-Judge Verdict Variance and the Noise Floor of LLM-as-Judge Leaderboards*. arXiv:2609.33044, 2026. https://arxiv.org/abs/2609.33044
9. Bengt Holmstrom and Paul Milgrom. *Aggregation and Linearity in the Provision of Intertemporal Incentives*. Econometrica, 1987. https://doi.org/10.2307/1913238
10. Bengt Holmstrom. *Moral Hazard and Observability*. The Bell Journal of Economics, 1979. https://doi.org/10.2307/3003320
11. Marilyn Strathern. *‘Improving ratings’: audit in the British University system*. European Review, 1997. https://doi.org/10.1002/(sici)1234-981x(199707)5:3<305::aid-euro184>3.0.co;2-4
12. Donald T. Campbell. *Assessing the Impact of Planned Social Change*. Journal of MultiDisciplinary Evaluation, 2011. https://doi.org/10.56645/jmde.v7i15.297
13. El-Mahdi El-Mhamdi and Lê-Nguyên Hoang. *On Goodhart's law, with an application to value alignment*. arXiv:2410.09638, 2024. https://arxiv.org/abs/2410.09638
14. Adrien Majka and El-Mahdi El-Mhamdi. *The Strong, Weak and Benign Goodhart's law. An independence-free and paradigm-agnostic formalisation*. arXiv:2505.23445, 2025. https://arxiv.org/abs/2505.23445
15. Roger B. Myerson. *Optimal Auction Design*. Mathematics of Operations Research, 1981. https://doi.org/10.1287/moor.6.1.58
16. Craig Boutilier. *Eliciting Forecasts from Self-interested Experts: Scoring Rules for Decision Makers*. arXiv:1106.2489, 2011. https://arxiv.org/abs/1106.2489
17. Yang Liu, Juntao Wang and Yiling Chen. *Surrogate Scoring Rules*. arXiv:1802.09158, 2018. https://arxiv.org/abs/1802.09158
18. Jason Milionis and William Pires. *On testing the incentive compatibility of single-parameter allocation mechanisms*. arXiv:2609.17406, 2026. https://arxiv.org/abs/2609.17406
19. William Vickrey. *COUNTERSPECULATION, AUCTIONS, AND COMPETITIVE SEALED TENDERS*. The Journal of Finance, 1961. https://doi.org/10.1111/j.1540-6261.1961.tb02789.x
20. Robert Wilson. *A Bidding Model of Perfect Competition*. The Review of Economic Studies, 1977. https://doi.org/10.2307/2296904
21. n.a. *Auction Theory*. Economics of Visual Art, 2021. https://doi.org/10.1017/9781108649919.020
22. Itzhak Rasooly and Carlos Gavidia-Calderon. *The importance of being discrete: on the inaccuracy of continuous approximations in auction theory*. arXiv:2006.03016, 2020. https://arxiv.org/abs/2006.03016
23. Thomas Nedelec et al. *Learning in repeated auctions*. arXiv:2011.09365, 2020. https://arxiv.org/abs/2011.09365
24. Xi Chen, Christian Kroer and Rachitesh Kumar. *Throttling Equilibria in Auction Markets*. arXiv:2107.10923, 2021. https://arxiv.org/abs/2107.10923
25. Ana Gjorgjevikj, Barbara Koroušić Seljak and Tome Eftimov. *On the Robustness of Multilingual Text Embedding Rankings Across Learning Tasks, Languages, and Benchmark Datasets*. arXiv:2605.31142, 2026. https://arxiv.org/abs/2605.31142
26. Sara Rezaeimanesh et al. *INCONVENIENT: A Benchmark to Assess LLM Generalization Capabilities from Convenience Samples*. arXiv:2610.21038, 2026. https://arxiv.org/abs/2610.21038
27. Jason D. Hartline et al. *Optimization of Scoring Rules*. arXiv:2007.02905, 2020. https://arxiv.org/abs/2007.02905
28. Eric Neyman and Tim Roughgarden. *From Proper Scoring Rules to Max-Min Optimal Forecast Aggregation*. arXiv:2102.07081, 2021. https://arxiv.org/abs/2102.07081
29. M. G. Kendall. *A New Measure of Rank Correlation*. Biometrika, 1938. https://doi.org/10.2307/2332226
30. C. Spearman. *The Proof and Measurement of Association Between Two Things*. Studies in individual differences: The search for intelligence., 1961. https://doi.org/10.1037/11491-005
31. Marcus Rockel. *Kendall and Spearman bounds for Chatterjee's rank correlation under positive dependence*. arXiv:2606.22074, 2026. https://arxiv.org/abs/2606.22074
32. Marc-Oliver Pohle, Jan-Lukas Wermuth and Christian H. Weiß. *Asymptotic Inference for Rank Correlations*. arXiv:2512.14609, 2025. https://arxiv.org/abs/2512.14609
33. Edwin B. Wilson. *Probable Inference, the Law of Succession, and Statistical Inference*. Journal of the American Statistical Association, 1927. https://doi.org/10.1080/01621459.1927.10502953
34. Thomas G. Dietterich. *Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms*. Neural Computation, 1998. https://doi.org/10.1162/089976698300017197
35. Kleyton da Costa and Bernardo Modenesi. *GraphNetz: Statistical Benchmarking of Graph Neural Networks with Paired Tests and Rank Aggregation*. arXiv:2605.09099, 2026. https://arxiv.org/abs/2605.09099
36. Amichai Painsky. *Who is the Winning Algorithm? Rank Aggregation for Comparative Studies*. arXiv:2601.01664, 2026. https://arxiv.org/abs/2601.01664
37. Aris Filos-Ratsikas et al. *On the Complexity of Equilibrium Computation in First-Price Auctions*. arXiv:2103.03238, 2021. https://arxiv.org/abs/2103.03238
38. Jiawei Chen, Anh Nguyen and Matthew Shum. *The Winner's Bliss in Common-Value Auctions under Horizontal Differentiation*. arXiv:2606.08419, 2026. https://arxiv.org/abs/2606.08419
39. Kenneth J. Arrow. *Social Choice and Individual Values*. Crossref record, 2017. https://doi.org/10.12987/9780300186987
40. Polina Gordienko et al. *Beyond Arrow: From Impossibility to Possibilities in Multi-Criteria Benchmarking*. arXiv:2602.07593, 2026. https://arxiv.org/abs/2602.07593
41. Yixuan Even Xu et al. *Aggregating Quantitative Relative Judgments: From Social Choice to Ranking Prediction*. arXiv:2410.05550, 2024. https://arxiv.org/abs/2410.05550
42. Xingyao Xiao and Yihong Cheng. *Contamination Inflates Scores but Rarely Reorders Large Language Model Leaderboards*. arXiv:2609.02899, 2026. https://arxiv.org/abs/2609.02899
43. Dishu Yang et al. *Measurement-First Auditing of Agentic Leaderboards: Contamination Susceptibility, Matched-Control Re-evaluation, and Scorer Validation*. arXiv:2610.05830, 2026. https://arxiv.org/abs/2610.05830
44. Rostislav Gusev and Alexey Zaytsev. *Benchmarking on Tasks That Matter: Dataset Selection for Preserving Model Rankings*. arXiv:2606.27997, 2026. https://arxiv.org/abs/2606.27997
45. Ashwinkumar Badanidiyuru. *Model Monotonicity in Autobidding Auctions: When Do Better Predictions Lead to Better Outcomes?*. arXiv:2605.31036, 2026. https://arxiv.org/abs/2605.31036
46. Jiacheng Wang and Jinbin Huang. *Reward Hacking as Equilibrium under Finite Evaluation*. arXiv:2603.28063, 2026. https://arxiv.org/abs/2603.28063
47. Arunabh Bora. *Beyond Reward Hacking: Proxy Divergence Across Four Layers of a Staged Humanoid Learning Pipeline*. arXiv:2610.03196, 2026. https://arxiv.org/abs/2610.03196
48. Thomas Kwa, Drake Thomas and Adrià Garriga-Alonso. *Catastrophic Goodhart: regularizing RLHF with KL divergence does not mitigate heavy-tailed reward misspecification*. arXiv:2407.14503, 2024. https://arxiv.org/abs/2407.14503
49. Lokman I. Meho. *Gaming the Metrics? Bibliometric Anomalies and the Integrity Crisis in Global University Rankings*. arXiv:2505.06448, 2025. https://arxiv.org/abs/2505.06448
50. Yiyang Zhao et al. *Beyond Goodhart's Law: A Dynamic Benchmark for Evaluating Compliance in Multi-Agent Systems*. arXiv:2606.07805, 2026. https://arxiv.org/abs/2606.07805
51. Maoqi Liu et al. *Scoring Higher, Answering Worse: Mitigating Reward Hacking in Rubric-Based RL via Protocol-Level Rubrics*. arXiv:2609.38847, 2026. https://arxiv.org/abs/2609.38847
52. Guanhua Zhang and Moritz Hardt. *Inherent Trade-Offs between Diversity and Stability in Multi-Task Benchmarks*. arXiv:2405.01719, 2024. https://arxiv.org/abs/2405.01719
53. Stefan Baack, Christo Buschek and Maty Bohacek. *Unsteady Metrics and Benchmarking Cultures of AI Model Builders*. arXiv:2605.14164, 2026. https://arxiv.org/abs/2605.14164
54. Nitya Nadgir et al. *Life After Benchmark Saturation: A Case Study of CORE-Bench*. arXiv:2606.26158, 2026. https://arxiv.org/abs/2606.26158
55. Morio Hamada et al. *Evaluating Model Capabilities After Benchmark Saturation*. arXiv:2610.20667, 2026. https://arxiv.org/abs/2610.20667
56. Xinran Zhang. *How Sensitive Are Safety Benchmarks to Judge Configuration Choices?*. arXiv:2604.24074, 2026. https://arxiv.org/abs/2604.24074
57. Patrick Lederer. *The Impossibility of Strategyproof Rank Aggregation*. arXiv:2602.06582, 2026. https://arxiv.org/abs/2602.06582
58. Jiachun Li, David Simchi-Levi and Will Wei Sun. *Low Rank for Rank: Uncertainty-Aware Task-Specific LLM Ranking under Sparse Pairwise Comparisons*. arXiv:2605.29395, 2026. https://arxiv.org/abs/2605.29395
59. Mina Remeli and Moritz Hardt. *Correct Looks Better: Pairwise Comparisons Reveal Accuracy Rankings*. arXiv:2606.09409, 2026. https://arxiv.org/abs/2606.09409
60. Yanhang Li, Zhichao Fan and Zexin Zhuang. *Auditing the Audit: Five Failure Modes in Benchmark-Validity Audits*. arXiv:2607.02586, 2026. https://arxiv.org/abs/2607.02586
61. Denis Degtiarev et al. *Auditing VLM Benchmarks from Existing Evaluation Runs*. arXiv:2610.13548, 2026. https://arxiv.org/abs/2610.13548
62. Junjie Chen. *When Agent Evaluation Becomes Unreliable: An Empirical Study of Oracle Failures and Configuration-Dependent Measurement in an LLM Agent Benchmark*. arXiv:2610.16067, 2026. https://arxiv.org/abs/2610.16067
63. Michael Hardy et al. *Agent Evaluation Reliability: More Tasks Won't (Always) Fix An Agent Leaderboard*. arXiv:2610.00651, 2026. https://arxiv.org/abs/2610.00651
64. Zhaowei Han et al. *What Can a Leaderboard Certify? Compositional Controllability for Fair Evaluation and Training of Biomedical Literature-Review Agents*. arXiv:2609.32318, 2026. https://arxiv.org/abs/2609.32318
65. Negin Kafee Hernashki and Soumick Chatterjee. *MIRTO: a registration-gated, multiverse-tested evaluation protocol for unsupervised anomaly segmentation in brain MRI*. arXiv:2610.02136, 2026. https://arxiv.org/abs/2610.02136
66. Yuedong Tan et al. *Does Local Video Understanding Transfer Across Encounters? The EgoGears Benchmark*. arXiv:2609.37938, 2026. https://arxiv.org/abs/2609.37938
67. Song Wang et al. *AutoAdapt: Reliable Few-Shot Adaptation under Clinical Distribution Shifts*. arXiv:2610.11162, 2026. https://arxiv.org/abs/2610.11162
68. Jiaqi Tang et al. *Benchmarking Self-Supervised 3D Medical Vision Foundation Models and Transferability Estimation*. arXiv:2610.17573, 2026. https://arxiv.org/abs/2610.17573
69. Ashwin Pananjady et al. *Worst-case vs Average-case Design for Estimation from Fixed Pairwise Comparisons*. arXiv:1707.06217, 2017. https://arxiv.org/abs/1707.06217
70. Shashaank Aiyer and Han Shao. *How Many Repeated Pairwise Comparisons Are Needed for Ranking under Heterogeneity?*. arXiv:2610.10795, 2026. https://arxiv.org/abs/2610.10795
71. Motti Goldberger and Nils Rudi. *Selecting the Best Few with Human Evaluators: Adaptively Combining Ratings and Pairwise Comparisons*. arXiv:2610.26380, 2026. https://arxiv.org/abs/2610.26380
72. Charlotte Li et al. *Towards Real-World Validity in Generative AI Benchmarks: Understanding and Designing Domain-Centered Evaluations for Journalism Practitioners*. arXiv:2511.05501, 2025. https://arxiv.org/abs/2511.05501
73. Louis Yiven Zhu. *One Capability or Many? Structural and Predictive Tests of Benchmark Validity Disagree About Economic Benchmarks for Frontier AI*. arXiv:2608.29420, 2026. https://arxiv.org/abs/2608.29420
74. Aris Filos-Ratsikas et al. *Equilibrium Computation in First-Price Auctions with Correlated Priors*. arXiv:2506.05322, 2025. https://arxiv.org/abs/2506.05322
75. Yatong Chen, Guanhua Zhang and Moritz Hardt. *Leaderboard Incentives: Model Rankings under Strategic Post-Training*. arXiv:2603.08371, 2026. https://arxiv.org/abs/2603.08371
76. Wei-Jung Huang. *When Pair Count Is Not the Sample Size: What All-Pairs Agent Comparisons Estimate*. arXiv:2609.33012, 2026. https://arxiv.org/abs/2609.33012
77. Ryan Othniel Kearns. *Quantifying construct validity in large language model evaluations*. arXiv:2602.15532, 2026. https://arxiv.org/abs/2602.15532
78. Timo Freiesleben. *Establishing Construct Validity in LLM Capability Benchmarks Requires Nomological Networks*. arXiv:2603.15121, 2026. https://arxiv.org/abs/2603.15121
79. Rana Muhammad Ahmed and Sabahat Abbas. *Labels Are Not Endpoints: Treatment Leakage and Construct Validity in MCP Agent Security Evaluation*. arXiv:2608.12880, 2026. https://arxiv.org/abs/2608.12880
80. Ahmed Alaa et al. *Medical Large Language Model Benchmarks Should Prioritize Construct Validity*. arXiv:2503.10694, 2025. https://arxiv.org/abs/2503.10694
81. Haji Gul and Ajaz Ahmad Bhat. *When Metrics Disagree: A Meta-Analysis of Knowledge-Graph-Completion Model Benchmarking*. arXiv:2606.10287, 2026. https://arxiv.org/abs/2606.10287
82. Yanbin Zhao et al. *A Measurement Perspective on Benchmarking LLM-Generated Text Detectors using Item Response Theory*. arXiv:2610.24972, 2026. https://arxiv.org/abs/2610.24972
83. Juan Francisco and Mandujano Reyes. *Laplace-PSN-IRT: Uncertainty Quantification for Neural Item Response Theory Models of LLM Benchmarks*. arXiv:2607.25257, 2026. https://arxiv.org/abs/2607.25257
84. Christopher M. Stewart et al. *Searching for "Harmful Refusal": A Psychometric Audit of an AI Safety Benchmark*. arXiv:2610.12409, 2026. https://arxiv.org/abs/2610.12409
85. Tobias Hallmen et al. *The Failure Is in the Readout: Fine-Grained Emotion Recognition Benchmarks Measure Elicitation, Not Perception*. arXiv:2610.08162, 2026. https://arxiv.org/abs/2610.08162
86. Silu Panda. *FinVerBench: Benchmark Validity and Calibration in Large Language Model Financial Statement Verification*. arXiv:2605.29586, 2026. https://arxiv.org/abs/2605.29586
87. Juncheng Li and Pingzhong Tang. *Vulnerabilities of Single-Round Incentive Compatibility in Auto-bidding: Theory and Evidence from ROI-Constrained Online Advertising Markets*. arXiv:2210.06107, 2022. https://arxiv.org/abs/2210.06107
88. Yeganeh Alimohammadi, Aranyak Mehta and Andres Perlroth. *Incentive Compatibility in the Auto-bidding World*. arXiv:2301.13414, 2023. https://arxiv.org/abs/2301.13414
89. Andries van Beek, Ruben Brokkelkamp and Guido Schäfer. *Corruption in Auctions: Social Welfare Loss in Hybrid Multi-Unit Auctions*. arXiv:2106.01822, 2021. https://arxiv.org/abs/2106.01822
90. Jingyi Liu et al. *Single-Item Auctions with a Monopolist Intermediary*. arXiv:2605.21934, 2026. https://arxiv.org/abs/2605.21934
91. Zhengyang Liu. *Tight Inapproximability of Pacing and Throttling Equilibria in Second-Price Auctions*. arXiv:2608.16682, 2026. https://arxiv.org/abs/2608.16682
92. Ravi Kashyap. *Auction Theory Adaptations for Real Life Applications*. arXiv:1810.01736, 2018. https://arxiv.org/abs/1810.01736
93. Renato Paes Leme, Balasubramanian Sivan and Yifeng Teng. *Why Do Competitive Markets Converge to First-Price Auctions?*. arXiv:2001.06074, 2020. https://arxiv.org/abs/2001.06074
94. Ismail Lotfi and Ali Ghrayeb. *Strategic Bidding in 6G Spectrum Auctions with Large Language Models*. arXiv:2604.24156, 2026. https://arxiv.org/abs/2604.24156
95. Shange Tang, Yuanhao Wang and Chi Jin. *Is Elo Rating Reliable? A Study Under Model Misspecification*. arXiv:2502.10985, 2025. https://arxiv.org/abs/2502.10985
96. Sam Olesker-Taylor and Luca Zanetti. *An Analysis of Elo Rating Systems via Markov Chains*. arXiv:2406.05869, 2024. https://arxiv.org/abs/2406.05869
97. Andy Gray et al. *Using Elo Rating as a Metric for Comparative Judgement in Educational Assessment*. arXiv:2204.01805, 2022. https://arxiv.org/abs/2204.01805
98. Yuhan Song. *Analysis of ELO Rating Scheme in MOBA Games*. arXiv:2310.13719, 2023. https://arxiv.org/abs/2310.13719
99. Chen Chen et al. *JudgeStealer: Extracting LLM Judging Capabilities across Evaluation Protocols*. arXiv:2608.26982, 2026. https://arxiv.org/abs/2608.26982
100. George Baker, Robert Gibbons and Kevin Murphy. *Subjective Performance Measures in Optimal Incentive Contracts*. Crossref record, 1993. https://doi.org/10.3386/w4480
101. Danilo de Oliveira et al. *The PESQetarian: On the Relevance of Goodhart's Law for Speech Enhancement*. arXiv:2406.03460, 2024. https://arxiv.org/abs/2406.03460
102. Bastien Mallein et al. *Selection of the fittest or selection of the luckiest: the emergence of Goodhart's law in evolution*. arXiv:2503.21849, 2025. https://arxiv.org/abs/2503.21849
103. Ayush Mittal and Dhruv Gupta. *Signed Compression Progress on a Sealed Audit is Goodhart-Resistant*. arXiv:2606.11417, 2026. https://arxiv.org/abs/2606.11417
104. Christian Moya, Elliott Thornley and Guang Lin. *Verifier Errors in RLVR: Reward Hacking, Limits of Feedback, and Selective Control*. arXiv:2609.35677, 2026. https://arxiv.org/abs/2609.35677
105. Junwei Quan et al. *RH-Detect: A Unified Benchmark for Reward Hacking Detection*. arXiv:2610.10947, 2026. https://arxiv.org/abs/2610.10947
106. Yuepeng Hu et al. *Reward Hacking as a Transmissible Strategy in Multi-Agent Coding Systems*. arXiv:2610.12822, 2026. https://arxiv.org/abs/2610.12822
107. Yushu Li et al. *Multi-Reward Hacking: From Aggregation-Induced Drift to Trust-Anchored Defense*. arXiv:2610.21404, 2026. https://arxiv.org/abs/2610.21404
108. Viktor Bengs, Eyke Hüllermeier and Willem Waegeman. *On Second-Order Scoring Rules for Epistemic Uncertainty Quantification*. arXiv:2301.12736, 2023. https://arxiv.org/abs/2301.12736
109. Rubi Hudson. *Joint Scoring Rules: Zero-Sum Competition Avoids Performative Prediction*. arXiv:2412.20732, 2024. https://arxiv.org/abs/2412.20732
110. Caspar Oesterheld et al. *Incentivizing honest performative predictions with proper scoring rules*. arXiv:2305.17601, 2023. https://arxiv.org/abs/2305.17601
111. Jens Witkowski et al. *Incentive-Compatible Forecasting Competitions*. arXiv:2101.01816, 2021. https://arxiv.org/abs/2101.01816
112. Benjamin Turtel et al. *How Proper Scoring Rules Shape LLM Forecasting*. arXiv:2608.28482, 2026. https://arxiv.org/abs/2608.28482
113. Alex Hall. *Arrow's Impossibility Theorem: Computability in Social Choice Theory*. arXiv:2311.09789, 2023. https://arxiv.org/abs/2311.09789
114. Federico Echenique and Quitzé Valenzuela-Stookey. *Utilitarian Social Choice and Distributional Welfare Analysis*. arXiv:2411.01315, 2024. https://arxiv.org/abs/2411.01315
115. Tianyi Qiu. *Representative Social Choice: From Learning Theory to AI Alignment*. arXiv:2410.23953, 2024. https://arxiv.org/abs/2410.23953
116. Jiayi Wang, Juan C. Alfaro and Viktor Bengs. *A comparative analysis of rank aggregation methods for the partial label ranking problem*. arXiv:2502.17077, 2025. https://arxiv.org/abs/2502.17077
117. Dominik Peters. *Kemeny Rank Aggregation is NP-Hard for Three Voters*. arXiv:2607.25540, 2026. https://arxiv.org/abs/2607.25540
118. Samuel R. Bowman and George Dahl. *What Will it Take to Fix Benchmarking in Natural Language Understanding?*. Proceedings of the 2021 Conference of the North American Chapter of the Associat, 2021. https://doi.org/10.18653/v1/2021.naacl-main.385
119. Douwe Kiela et al. *Dynabench: Rethinking Benchmarking in NLP*. Proceedings of the 2021 Conference of the North American Chapter of the Associat, 2021. https://doi.org/10.18653/v1/2021.naacl-main.324
120. Rishi Bommasani, Percy Liang and Tony Lee. *Holistic Evaluation of Language Models*. Annals of the New York Academy of Sciences, 2023. https://doi.org/10.1111/nyas.15007
121. Q. Vera Liao and Ziang Xiao. *Rethinking Model Evaluation as Narrowing the Socio-Technical Gap*. arXiv:2306.03100, 2023. https://arxiv.org/abs/2306.03100
122. Stephen Casper et al. *Explore, Establish, Exploit: Red Teaming Language Models from Scratch*. arXiv:2306.09442, 2023. https://arxiv.org/abs/2306.09442
123. Ethan Perez et al. *Red Teaming Language Models with Language Models*. Proceedings of the 2022 Conference on Empirical Methods in Natural Language Proc, 2022. https://doi.org/10.18653/v1/2022.emnlp-main.225
124. Benjamin Recht et al. *Do ImageNet Classifiers Generalize to ImageNet?*. arXiv:1902.10811, 2019. https://arxiv.org/abs/1902.10811
125. Nika Haghtalab et al. *Pluralistic Leaderboards*. arXiv:2606.02547, 2026. https://arxiv.org/abs/2606.02547
126. Paul Milgrom. *Auctions and Bidding: A Primer*. Journal of Economic Perspectives, 1989. https://doi.org/10.1257/jep.3.3.3
127. Paul Klemperer. *Auction Theory: A Guide to the Literature*. Crossref record, 1999. https://doi.org/10.2139/ssrn.172650
128. John F. Nash. *EQUILIBRIUM POINTS IN 𝑛-PERSON GAMES*. Classics in Game Theory, 2020. https://doi.org/10.2307/j.ctv173f1fh.6
129. Paul R. Milgrom and Robert J. Weber. *A Theory of Auctions and Competitive Bidding*. Econometrica, 1982. https://doi.org/10.2307/1911865
130. Benjamin Heymann. *On the Role of Tie-Breaking Rules in the Convergence of Fictitious Play for Symmetric First-Price Auctions*. arXiv:2609.18848, 2026. https://arxiv.org/abs/2609.18848
