#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""placements.py -- which record supports which claim in issue #162's manuscript.

AUTHORED FILE. Everything here is a decision, not a derivation: a verified record becomes a citation
only because a sentence in the manuscript needs it, and the sentence is named. The #149 lesson is the
reason this is a file of claims rather than a list of keys — a corpus matched to a manuscript by
vocabulary produces references nothing supports, and a reference list assembled that way reads as
padding because it is padding.

Each claim is `(id, section, sentence, keys)`. The manuscript cites a claim by id (`{{c:id}}`), never
by key, so a citation cannot be added without a claim that owns it and a claim cannot be dropped
without the manuscript's marker going unresolved. Two directions, one comparison.

The records that are NOT placed are not hidden: `harvest_refs.py` keeps every verified record, and the
report names the count and the reason each group's surplus is not cited.
"""
from __future__ import annotations

CLAIMS = [
    # ------------------------------------------------------------------------------------------
    # §2 — the object: a joint probability given its marginals
    # ------------------------------------------------------------------------------------------
    dict(
        id="frechet-class",
        difference="states the class and its extremes for a given joint problem; this paper locates a published durability figure inside it",
        section="2",
        claim=("Given the marginals and nothing else, the object is the Fréchet class: the set of "
               "joint laws with those marginals, whose extremes are the classical bounds."),
        keys=["dallaglio1991frechet", "rschendorf1991frechet", "walter1988marginal",
              "tiit2002existence", "schay1979optimal", "leblanc1984probability"],
    ),
    dict(
        id="bonferroni-lower",
        difference="sharpens the intersection bound as a tool; this paper reads a quoted number against it and reports the distance in nines",
        section="2",
        claim=("The lower end of that set for an intersection of r events is the inclusion-exclusion "
               "bound, and the literature's business has been improving it, not questioning it."),
        keys=["galambos1977bonferroni", "hoppe1985iterating", "kounias1989bonferroni",
              "recsei1987bonferroni", "samuels1989bonferroni", "sibuya1992sharp",
              "spencer1994generalized", "tan1989some", "walker1981classical",
              "chen1996multivariate", "dohmen2002improved", "dohmen2003bonferroni",
              "dohmen2003improved", "naiman1992inclusion", "lee1997improved",
              "b2016bivariate", "b2016bivariate-2a76e", "b2016multivariate", "b2016multivariate-547ac",
              "liu1994strong"],
    ),
    dict(
        id="bounds-stated-not-attained",
        difference="optimises under the bound for dependent risks; this paper asks which end of the bound the quoted figure sits at",
        section="2",
        claim=("The literature states these bounds for dependent risks and optimises under them; what "
               "it does not do is take the quote's own figure and ask which end of the set it is."),
        keys=["anastassiou1997optimal", "butucea2018maximum", "cicalese2017find", "tonon2009bounds",
              "mller2001bounds", "durante2008bounds", "cossette2014note", "embrechts2010bounds",
              "mesfioui2005bounds", "wang2013bounds", "kaas2002simple", "cheung2010characterizi",
              "denuit2007comonotonic", "ekeland2008comonotonic", "demeyer2007transitivity",
              "yin2016sharp", "loper2026worst"],
    ),

    # ------------------------------------------------------------------------------------------
    # §3 — correlated failure is measured, and it defeats redundancy
    # ------------------------------------------------------------------------------------------
    dict(
        id="correlation-measured",
        difference="measures correlated failure in production systems; this paper asks what a quote computed without that measurement identifies",
        section="3",
        claim=("Correlated failure is a measured property of production systems, in disks, in racks, "
               "in networks and in power, not a hypothetical."),
        keys=["bairavasundaram2007analysis", "bairavasundaram2008analysis", "xian2024examining",
              "yigitbasi2010analysis", "ali2018fault", "ekisheva2015north-08bb8", "ekisheva2017outage",
              "pijarski2025outage", "peidong2018cascading", "qi2021utility", "she2025descriptor",
              "neumayer2010network", "jimenez2023resilience", "barrera2023communicatio",
              "kim2010assessing", "medina2020impact", "xu2010characterizi",
              "franklin2017predicting"],
    ),
    dict(
        id="redundancy-defeated",
        difference="models common-cause failure to compute system reliability; this paper prices what an unstated dependence leaves open in the quote's unit",
        section="3",
        claim=("Adding replicas under dependence is not a monotone improvement, and the failure-mode "
               "literature has said so for decades: common-cause models are the standard repair."),
        keys=["jones2025common", "anon1988correlated", "fiondella2010estimating",
              "fiondella2014recovery", "fiondella2014reliability", "nikolov1986out",
              "nikolov1986unit", "goel1992warm", "goel1993two", "goel1994inspection",
              "bhattacharya1991redundancy", "anon1992redundancy", "anon1983linearly",
              "anon1988reliability", "anon1964much", "anon1964optimum", "anon1990redundancy",
              "rosenhaus2004calculation", "yeh2017cost", "yeh2017optimal", "harada1994probability",
              "hughes1987new", "anon1998betaplus", "martin1987practical", "kanev2012new",
              "kulkarni1994modelling", "anon1979common"],
    ),
    dict(
        id="placement-under-correlation",
        difference="assumes a dependence and constrains placement; this paper assumes none and reports what that leaves unidentified",
        section="3",
        claim=("The copyset line answers the same worry from the design side: assume the dependence, "
               "constrain which replicas may fail together, and compute the resulting loss rate."),
        keys=["huo2021optimal", "li2022random", "mills2015replica", "mills2016erratum",
              "mills2020algorithms", "bansal2011dynamic", "benoit2012optimal", "amjad2010application",
              "chang2012optimal", "jingsun2010new", "lin2008list", "chaubey2015replicated"],
    ),
    dict(
        id="quorum-availability",
        difference="designs quorums whose availability depends on correlated node failure; this paper asks what the availability figure identifies given only marginals",
        section="3",
        claim=("Quorum systems make the same trade in the availability direction, and their "
               "probabilistic variants exist precisely because a fixed quorum's availability is a "
               "function of which nodes fail together."),
        keys=["peleg1995availability", "amir1998optimal", "tsuchiya2002byzantine",
              "vukoli2012byzantine", "vukoli2012classical-20779", "vukoli2012probabilisti",
              "vukoli2012latency", "kumar2011multi", "kumar2015circular",
              "lin2003delay", "dong2024asynchronous", "basmadjian2026availability"],
    ),

    # ------------------------------------------------------------------------------------------
    # §4 — where the quoted figure comes from
    # ------------------------------------------------------------------------------------------
    dict(
        id="durability-models",
        difference="computes the durability figure from per-device rates under independence; this paper prices the independence step itself",
        section="4",
        claim=("A durability figure is produced by an MtTDL-style model whose inputs are per-device "
               "rates and whose arithmetic is the independence product the quote repeats."),
        keys=["ramabhadran2008durability", "rahman2017analysis", "rahman2018analysis",
              "luo2009impact", "li2011reliability", "iliadis2023reliability",
              "iliadis2008reliability", "chanikpark1995efficient", "smith2016reliability",
              "smith2016reliability-02f24", "vanrenesse2010replication", "zhong2007object",
              "zhong2008replication", "liu2016popularity", "aguilera2017multi", "anon2019multi"],
    ),
    dict(
        id="erasure-arithmetic",
        difference="changes the redundancy arithmetic of the same model; this paper shows the identified set is unchanged by it",
        section="4",
        claim=("Erasure coding changes the arithmetic and the engineering of that model — it does not "
               "change what the marginals identify."),
        keys=["fu2015frm", "zhou2020fast", "uezato2021accelerating", "sakif2024towards",
              "heide2016composite", "kim2021erasure", "gan2024erasure", "shi2020inec",
              "albano2009distributed", "charles2009hierarchical", "li2006adaptive",
              "moghadamfarid2025secure", "djouama2026mobicloud"],
    ),
    dict(
        id="sla-promise",
        difference="publishes the figure as a commitment to a customer; this paper states what the commitment asserts about an unmeasured quantity",
        section="4",
        claim=("The number is then published as a promise, in a service-level objective or a "
               "durability claim, where the reader is a customer and not a reviewer."),
        keys=["anon2020azure", "bosse2015optimizing", "perez2023service", "pbtee2003appendix",
              "aubineau2012cloud", "sharaf2014enabling", "tang2017quantitative",
              "talapko2012telecom", "achary2021reliability", "anon2017continuous",
              "deguise2020continuous", "osrael2006replication", "osrael2007availability"],
    ),

    # ------------------------------------------------------------------------------------------
    # §5 — why the far tail is not estimated here
    # ------------------------------------------------------------------------------------------
    dict(
        id="rare-event-cost",
        difference="estimates far-tail probabilities by simulation or extrapolation; this paper declines to estimate and bounds instead",
        section="5",
        claim=("Estimating a probability at the far tail is a research programme of its own: the "
               "standard answer is importance sampling or extreme-value extrapolation, each with its "
               "own assumption about the tail it is extrapolating into."),
        keys=["asmussen2006improved", "botev2016estimator", "gudmundsson2014markov", "chan2012rare",
              "balesdent2014rare", "morio2016introduction", "morio2016formalism", "morio2016synthesis",
              "huang2019impacts", "sakalauskas2013multidimensi", "jiang2026likelihood",
              "zuk2014rare", "galambos1988failure", "galambos1988inequalities",
              "leadbetter1979dependent", "haiman2003extremes", "anon2006estimation",
              "mller2019refining", "melchers2011application", "gomes1996extreme"],
    ),
    dict(
        id="assumption-sensitivity",
        difference="treats a quoted probability's assumptions as a sensitivity question inside a study; this paper makes the quoted number the object",
        section="5",
        claim=("The reliability-reporting literature already knows that a quoted failure probability "
               "inherits its assumptions, and treats that as a sensitivity question rather than a "
               "reporting one."),
        keys=["flage2020assumptions", "berner2016strengthenin", "anon2003concepts",
              "connors1984variability", "ichikawa1983new", "ichikawa1984confidence",
              "ichikawa1984general", "reiser1985remark", "yarimer1983statistical",
              "nieuwhof1985matching", "scheu2017influence", "gu2015ccf", "helton1996probability",
              "barros2000independence", "manne1952strong", "saigo2021independence",
              "huber2015test", "cronvall2012study", "phelps2010reporting", "knaeble2026sensitivity"],
    ),
    dict(
        id="diversification-fallacy",
        difference="names the same arithmetic as a fallacy in risk aggregation; this paper supplies the identified set that the fallacy is a misreading of",
        section="5",
        claim=("The same arithmetic is a named fallacy elsewhere: zero correlation is not "
               "independence, and diversification computed under one coupling fails under another."),
        keys=["brgi2009risk", "bush2019fallacy", "russell1998internationa", "zhou2009dependence",
              "rschendorf2012optimal", "chichilnisky2009catastrophic", "peng2013decentralize",
              "belak2014worst", "menkens2014worst", "bernard2013bounds", "badikov2016arbitrage",
              "galichon2011stochastic"],
    ),
]

# Records whose subject is adjacent rather than the same: named here so the exclusion is a decision
# with a reason, not a silent drop. Any other unplaced record is on-topic but supports no sentence
# above, which the report also states.
PRUNED = {
    "abdullahi2020internationa": "financial reporting quality — 'quoted' and 'reporting' matched a query, not this paper",
    "aduwo2023internationa": "financial reporting quality — 'quoted' matched a query, not this paper",
    "amahalu2018effect": "financial reporting of quoted firms — adjacent construct, different object",
    "firdaus2025audit": "audit quality and financial reporting — adjacent construct",
    "rjfa2019financial": "financial reporting quality of quoted banks — adjacent construct",
    "rjfa2022financial": "financial reporting quality and share values — adjacent construct",
    "watchman2019financial": "financial reporting by quoted SMEs — adjacent construct",
    "yusuf2021internationa": "financial reporting standards — adjacent construct",
    "gorodnichenko2006public": "public-sector corruption — 'corruption' matched a query, not storage",
    "lee2006business": "public-sector corruption and growth — 'corruption' matched a query",
    "martinezvazquez2007fighting": "public-sector corruption — adjacent construct",
    "lei2026cleanstack": "stack memory corruption attacks — 'corruption' matched a query, not storage",
    "baibussinov2025logical": "UAV storage forensics — same words, different instrument",
    "anon2015complete": "DNA replication — 'replication' matched a query, not data replication",
    "branzei2007interplay": "DNA replication checkpoints — adjacent construct",
    "cowan2001new": "DNA replication probability model — adjacent construct",
    "ahmad2021catastrophic": "agricultural catastrophic risk — 'catastrophic' matched a query",
    "ahmad2021synchronized": "agricultural credit and catastrophic risk — adjacent construct",
    "ullah2015managing": "catastrophic risk in agriculture — adjacent construct",
    "martel2013catastrophic": "opioid misuse risk — 'catastrophic' matched a query",
    "phoenix2008nanotechnolo": "nanotechnology as global catastrophic risk — different object",
    "kutch2011muscle": "muscle redundancy — 'redundancy does not imply robustness' is the right shape, wrong system",
    "paatero2023modeling": "zebrafish housing temperatures — 'power outage' matched a query",
    "limsoyamamoto2026orchestratio": "bacterial EV biogenesis — 'quota/availability' matched a query",
    "leilei2025beyond": "hedge-fund liquidations — correlated failure in finance, cited nowhere here",
    "leilei2026beyond": "hedge-fund liquidations — duplicate of the above in another venue",
    "poulsen2025practical": "replication crisis in finance — 'replication' is the other sense",
    "youyou2026are": "replication failures in public knowledge — 'replication' is the other sense",
    "krhmer2026update": "availability of replication materials — 'replication' is the other sense",
}

FLOOR = 100


def placed_keys():
    seen, out = set(), []
    for cl in CLAIMS:
        for k in cl["keys"]:
            if k not in seen:
                seen.add(k)
                out.append(k)
    return out


def claim_of(key):
    return [cl["id"] for cl in CLAIMS if key in cl["keys"]]
