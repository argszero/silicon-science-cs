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

## A prior-art line this report does not cite, and why

The copyset placement discipline — constrain which replicas may fail together, then compute the loss rate — originates in a USENIX ATC paper that carries **no DOI** and therefore has no Crossref record. The arXiv probe that could have corroborated it returned HTTP 429 (NOT RUN) on every attempt this round. It is consequently **not cited**: an unverifiable citation is not admissible here, and a rate limit does not establish that the record does not exist. What the manuscript does cite is the copyset placement literature that *is* indexed (see the `placement-under-correlation` claim), which makes the same design argument on the record.

