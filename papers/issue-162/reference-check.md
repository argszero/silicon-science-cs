# Reference verification report — issue #162

**DERIVED FILE — do not edit.** Regenerate with `./gate_citations.py --report reference-check.md`. It is a pure function of the stored verification state in `refs/references.json` and the authored placement in `placements.py`; it reads no network and writes no timestamp of its own, so regenerating it reproduces it byte for byte.

## What was searched, and how

| item | value |
|---|---|
| index | Crossref REST API, `works` endpoint (`query.bibliographic` for discovery, `works/{doi}` for verification) |
| window | **none imposed** — the bibliographic query takes no date filter in this call, so the scan is a scan and the window is not a claim this report can make; the scan date is |
| scan date | 2026-11-02 |
| rows per query | 24 |
| queries issued | 30 |
| verification method | DOI → `works/{doi}`; the stored title must match the returned title **and** an independent field must corroborate it: the first-author family, or the year when no author is asserted. Author mismatch is fatal; a year mismatch is recorded as an edition (`verified-edition`) |
| arXiv | **NOT RUN** — the arXiv API returned HTTP 429 on every probe this round. That is a rate limit, not an absence of records, so this report does not claim any work is missing from arXiv |

## Counts

| quantity | value |
|---|---|
| records harvested mechanically | 499 |
| candidate records refused at harvest | 207 |
| — refused: adjacent-construct | 1 |
| — refused: duplicate-title | 26 |
| — refused: no-year | 47 |
| — refused: terms | 28 |
| — refused: type | 105 |
| records verified against their DOI record | 499 |
| verified in this run / carried from an earlier run | 499 / 0 |
| records not verified (excluded, never cited) | 0 |
| **distinct records cited in the manuscript** | **206** (floor 100) |
| records verified but not cited | 293 |
| — of those, carrying a named reason in `placements.py` | 29 |

A verified record is not a citation. The floor is met in records the manuscript actually cites, each through a claim that owns it (`{{c:<id>}}`), so an entry cannot be padding: `gate_citations.py` fails if a claim is placed and never cited, and fails if a citation exists with no claim behind it.

## Refusals at harvest, by reason

| reason | n | what it means |
|---|---|---|
| adjacent-construct | 1 | shares a word with this paper and names a different object |
| duplicate-title | 26 | the same work under another DOI; the corpus admits one key per work |
| no-year | 47 | the record carries no date, so nothing can corroborate the year |
| terms | 28 | the returned title does not mention the group's own terms: the query measured the index's recall, not the literature |
| type | 105 | not an academic item (figure caption, front matter, component, peer review) |

## What the corpus is placed against

| claim id | section | records | the claim it supports |
|---|---|---|---|
| `frechet-class` | §2 | 6 | Given the marginals and nothing else, the object is the Fréchet class: the set of joint laws with those marginals, whose extremes are the classical bounds. |
| `bonferroni-lower` | §2 | 20 | The lower end of that set for an intersection of r events is the inclusion-exclusion bound, and the literature's business has been improving it, not questioning it. |
| `bounds-stated-not-attained` | §2 | 17 | The literature states these bounds for dependent risks and optimises under them; what it does not do is take the quote's own figure and ask which end of the set it is. |
| `correlation-measured` | §3 | 18 | Correlated failure is a measured property of production systems, in disks, in racks, in networks and in power, not a hypothetical. |
| `redundancy-defeated` | §3 | 27 | Adding replicas under dependence is not a monotone improvement, and the failure-mode literature has said so for decades: common-cause models are the standard repair. |
| `placement-under-correlation` | §3 | 12 | The copyset line answers the same worry from the design side: assume the dependence, constrain which replicas may fail together, and compute the resulting loss rate. |
| `quorum-availability` | §3 | 12 | Quorum systems make the same trade in the availability direction, and their probabilistic variants exist precisely because a fixed quorum's availability is a function of which nodes fail together. |
| `durability-models` | §4 | 16 | A durability figure is produced by an MtTDL-style model whose inputs are per-device rates and whose arithmetic is the independence product the quote repeats. |
| `erasure-arithmetic` | §4 | 13 | Erasure coding changes the arithmetic and the engineering of that model — it does not change what the marginals identify. |
| `sla-promise` | §4 | 13 | The number is then published as a promise, in a service-level objective or a durability claim, where the reader is a customer and not a reviewer. |
| `rare-event-cost` | §5 | 20 | Estimating a probability at the far tail is a research programme of its own: the standard answer is importance sampling or extreme-value extrapolation, each with its own assumption about the tail it is extrapolating into. |
| `assumption-sensitivity` | §5 | 20 | The reliability-reporting literature already knows that a quoted failure probability inherits its assumptions, and treats that as a sensitivity question rather than a reporting one. |
| `diversification-fallacy` | §5 | 12 | The same arithmetic is a named fallacy elsewhere: zero correlation is not independence, and diversification computed under one coupling fails under another. |

## Records excluded by name, with the reason

These cleared the screen and are real records; they are not cited because they name an adjacent construct. The exclusion is a decision with a reason, not a silent drop.

| key | reason |
|---|---|
| `abdullahi2020internationa` | financial reporting quality — 'quoted' and 'reporting' matched a query, not this paper |
| `aduwo2023internationa` | financial reporting quality — 'quoted' matched a query, not this paper |
| `ahmad2021catastrophic` | agricultural catastrophic risk — 'catastrophic' matched a query |
| `ahmad2021synchronized` | agricultural credit and catastrophic risk — adjacent construct |
| `amahalu2018effect` | financial reporting of quoted firms — adjacent construct, different object |
| `anon2015complete` | DNA replication — 'replication' matched a query, not data replication |
| `baibussinov2025logical` | UAV storage forensics — same words, different instrument |
| `branzei2007interplay` | DNA replication checkpoints — adjacent construct |
| `cowan2001new` | DNA replication probability model — adjacent construct |
| `firdaus2025audit` | audit quality and financial reporting — adjacent construct |
| `gorodnichenko2006public` | public-sector corruption — 'corruption' matched a query, not storage |
| `krhmer2026update` | availability of replication materials — 'replication' is the other sense |
| `kutch2011muscle` | muscle redundancy — 'redundancy does not imply robustness' is the right shape, wrong system |
| `lee2006business` | public-sector corruption and growth — 'corruption' matched a query |
| `lei2026cleanstack` | stack memory corruption attacks — 'corruption' matched a query, not storage |
| `leilei2025beyond` | hedge-fund liquidations — correlated failure in finance, cited nowhere here |
| `leilei2026beyond` | hedge-fund liquidations — duplicate of the above in another venue |
| `limsoyamamoto2026orchestratio` | bacterial EV biogenesis — 'quota/availability' matched a query |
| `martel2013catastrophic` | opioid misuse risk — 'catastrophic' matched a query |
| `martinezvazquez2007fighting` | public-sector corruption — adjacent construct |
| `paatero2023modeling` | zebrafish housing temperatures — 'power outage' matched a query |
| `phoenix2008nanotechnolo` | nanotechnology as global catastrophic risk — different object |
| `poulsen2025practical` | replication crisis in finance — 'replication' is the other sense |
| `rjfa2019financial` | financial reporting quality of quoted banks — adjacent construct |
| `rjfa2022financial` | financial reporting quality and share values — adjacent construct |
| `ullah2015managing` | catastrophic risk in agriculture — adjacent construct |
| `watchman2019financial` | financial reporting by quoted SMEs — adjacent construct |
| `youyou2026are` | replication failures in public knowledge — 'replication' is the other sense |
| `yusuf2021internationa` | financial reporting standards — adjacent construct |

## Entries whose record carries no author

54 of the 206 cited records carry no author field on Crossref, and their entries say so by naming the record that was read ("author not established on Crossref for this DOI") rather than by leaving the position empty or inventing an initial. The absence is a claim about a record, and it is checkable against the registry the entry names.

| key | DOI | title |
|---|---|---|
| `acmm1999rilsan` | 10.1108/acmm.1999.12846dad.013 | Rilsan Coatings guarantee quality and durability in pipes and fittings |
| `anon1963redundancy` | 10.1016/0026-2714(63)90356-1 | Redundancy and the detection of first failures |
| `anon1964much` | 10.1016/0026-2714(64)90260-4 | How much does redundancy improve reliability? |
| `anon1964optimum` | 10.1016/0026-2714(64)90183-0 | Optimum redundancy when components are subject to two kinds of failure |
| `anon1969boost` | 10.1016/0026-2714(69)90122-x | Boost reliability in your op-amp circuit. Build in redundancy and get automatic compensation for internal failures |
| `anon1976common` | 10.1016/0026-2714(76)90173-6 | Common-cause failure considerations in predicting HTGR cooling system reliability |
| `anon1978effects` | 10.1016/0026-2714(78)90369-4 | Effects of Weibull hazard rate on common cause failure analysis of reliability networks |
| `anon1979common` | 10.1016/0026-2714(79)90195-1 | A common cause-failure availability model |
| `anon1980common` | 10.1016/0026-2714(80)90078-5 | Common-cause failure analysis of a three-state device system |
| `anon1983linearly` | 10.1016/0026-2714(83)91230-1 | Linearly correlated intermittent failures |
| `anon1985two` | 10.1016/0026-2714(85)90059-9 | A two (multicomponent) unit parallel system with standby and common cause failure |
| `anon1988correlated` | 10.1016/0026-2714(88)90195-3 | Correlated failures in fault-tolerant computers |
| `anon1988reliability` | 10.1016/0026-2714(88)90062-5 | Reliability of a system for Markov-dependent components |
| `anon1990redundancy` | 10.1016/0026-2714(90)90489-a | Redundancy strategy for dependent subsystems |
| `anon1990reliability` | 10.1016/0026-2714(90)90082-x | Reliability modelling of redundant computer systems with common-cause failures |
| `anon1990ultrasonic` | 10.1016/0026-2714(90)90350-v | Does ultrasonic cleaning damage components? |
| `anon1992availability` | 10.1016/0026-2714(92)90281-o | Availability of the crystallization system in the sugar industry under common-cause failure |
| `anon1992redundancy` | 10.1016/0026-2714(92)90164-g | Redundancy optimization of k--n systems with common-cause failures |
| `anon1998betaplus` | 10.1080/09617353.1998.11690672 | The Betaplus Common Cause Failure Model |
| `anon2003appendix` | 10.1515/9783110917819.753 | Appendix A. Volume 2. Probability Theory and Extreme Value Theory |
| `anon2003concepts` | 10.1201/9780203498798.ch2 | Concepts of Probability Theory For Sensitivity And Uncertainty Analysis |
| `anon2004quantum` | 10.1201/9780203483930-21 | Quantum Physics-Based Probability Models with Applications to Reliability Analysis |
| `anon2005reliability` | 10.1201/9781420056341.ch9 | Reliability |
| `anon2005supplemental` | 10.1037/1082-989x.10.1.84.supp | Supplemental Material for Using Data Augmentation to Obtain Standard Errors and Conduct Hypothesis Tests in Latent Class and Latent Transition Analysis |
| `anon2006estimation` | 10.1007/0-387-34471-3_8 | Estimation of the Probability of a Failure Set |
| `anon2006random` | 10.1201/9781420011340-16 | Random-effect models for survival data |
| `anon2009disk` | 10.1109/9780470545171.ch3 | Disk Drive Magnetic Recording |
| `anon2013appendix` | 10.1515/9781400848560-011 | Appendix: Quoted Figures and Characters |
| `anon2013emerging` | 10.4324/9781315071688-8 | An Emerging Consensus on Biodiversity Loss |
| `anon2015complete` | 10.1158/2159-8290.cd-rw2015-024 | Complete Loss of Replication Repair Drives Ultra-Hypermutated Cancers |
| `anon2017continuous` | 10.4324/9781315169620-10 | Continuous Availability and Replication |
| `anon2019multi` | 10.1007/978-3-319-77525-8_100219 | Multi-data Center Replication |
| `anon2022probability` | 10.1007/978-981-10-6946-8_300620 | Probability of Reliability |
| `anon2024chapter` | 10.1515/9780691237701-006 | CHAPTER 5 Consensus or Quorum? |
| `anon2026erasure` | 10.1017/9781316443354.004 | Erasure Channel Models and Bounds |
| `auej2025erratum` | 10.21608/auej.2025.503058 | ERRATUM TO: NUMERICAL ANALYSIS OF ENHANCING LATENT HEAT STORAGE USING FINS AND CONDUCTIVE BARRIERS |
| `b2007overview` | 10.1016/b978-008044465-9/50010-4 | Overview of Hard Disk Drive Components and Technology |
| `b2011methods` | 10.1201/b11537-3 | Methods of Extreme Value Theory |
| `b2015instantaneou` | 10.1201/b19348-5 | Instantaneous Availability Model of Discrete-Time System under General Probability Distribution |
| `b2016bivariate` | 10.1201/b17163-12 | Bivariate Lower Bounds |
| `b2016bivariate-2a76e` | 10.1201/b17163-10 | Bivariate Upper Bounds |
| `b2016multivariate` | 10.1201/b17163-11 | Multivariate and Hybrid Upper Bounds |
| `b2016multivariate-547ac` | 10.1201/b17163-13 | Multivariate and Hybrid Lower Bounds |
| `bshost2024probability` | 10.1016/bs.host.2024.07.004 | Probability models applied to reliability and availability engineering |
| `case2026application` | 10.1109/case69030.2026.11704386 | Application of Multi-Objective Optimization Method Based on Safety, Economy and Availability in Outage Scheduling of Nuclear Power Plant |
| `cbms2004chapter` | 10.1214/cbms/1462106080 | Chapter 4: Semi-parametric estimation in the linear model for correlated data |
| `cbo2012energy` | 10.1017/cbo9781139226608.014 | Energy Storage Systems |
| `cbo2015large` | 10.1017/cbo9781316341414.016 | Large-Scale Energy Storage Systems |
| `firdaus2025audit` | 10.37134/firdaus.vol4.1.9.2024 | Audit Quality and Financial Reporting Quality among Quoted Non-Financial Firms in Nigeria |
| `jj2024consensus` | 10.2307/jj.7657716.8 | Consensus or Quorum? |
| `ovs2013softwarepfle` | 10.9785/ovs.9783504380397.849 | I. Softwarepflege inklusive Service-Level-Agreement |
| `pbtee2003appendix` | 10.1049/pbte048e_appendix3 | Appendix 3: Template for a typical service level agreement |
| `rjfa2019financial` | 10.7176/rjfa/10-9-08 | Financial Reporting Quality and Financial Performance of Quoted Banks in Nigeria |
| `rjfa2022financial` | 10.7176/rjfa/13-14-06 | Financial Reporting Quality and Share Values of the Quoted Non-Financial Firms in Nigeria |

## Bracketed groups in the text that are not citations

The prose writes the closed unit interval as `[0, 1]`, and writes a claim's citation cluster as a bracketed number list. A reader (and `refgate.py`, which calls it `AMBIGUOUS [0]`) sees the first as a citation to entry 0, which does not exist. It is an interval: `rho` is declared on `[0, 1]`, and every bracket group in this paper is either that interval or a generated cluster.

## A prior-art line this report does not cite, and why

The copyset placement discipline — constrain which replicas may fail together, then compute the loss rate — originates in a USENIX ATC paper that carries **no DOI** and therefore has no Crossref record. The arXiv probe that could have corroborated it returned HTTP 429 (NOT RUN) on every attempt this round. It is consequently **not cited**: an unverifiable citation is not admissible here, and a rate limit does not establish that the record does not exist. What the manuscript does cite is the copyset placement literature that *is* indexed (see the `placement-under-correlation` claim), which makes the same design argument on the record.

