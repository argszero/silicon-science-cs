#!/usr/bin/env python3
"""issue-165 -- attach the EXPECTED TITLE to every slot.

Why this is a separate step: the search query is not the hypothesis. A query carries author surnames
and stopwords because that is what makes a registry find the work; the title is what the work must
actually be. Comparing the query to a returned title (which is what `verify()` did first) measures
string luck, not identity -- and it silently rejected 65 of 120 slots, among them works whose DOI is
unambiguous.

So each slot gets `want_title`: the title this study believes the work has. That belief is RECALL, and
it is exactly what the registry is asked to falsify: `build_refs.py` accepts a record only if the
returned title matches this one under two-way content-word containment AND the year agrees, and a
miss is printed as a refusal. A slot whose want_title the registry cannot find is not silently
dropped; it is reported, and the tally is a result.

Usage:  python3 add_want_titles.py        -> rewrites refs/slots.json in place (idempotent)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLOTS = os.path.join(HERE, "refs", "slots.json")

WANT = {
    "kessler1963": "Bibliographic coupling between scientific papers",
    "small1973": "Co-citation in the scientific literature: A new measure of the relationship between two documents",
    "price1965": "Networks of scientific papers",
    "garfield1979": "Citation indexing: its theory and application in science, technology, and humanities",
    "newman2001": "Scientific collaboration networks. I. Network construction and fundamental results",
    "redner1998": "How popular is your paper? An empirical study of the citation distribution",
    "evans2008": "Electronic publication and the narrowing of science and scholarship",
    "larsen2010": "The rate of growth in scientific publication and the decline in coverage provided by Science Citation Index",
    "cohen1960": "A coefficient of agreement for nominal scales",
    "wilson1927": "Probable inference, the law of succession, and statistical inference",
    "efron1979": "Bootstrap methods: another look at the jackknife",
    "efron1993": "An introduction to the bootstrap",
    "priem2022": "OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts",
    "hendricks2020": "Crossref: documenting and sharing research metadata",
    "martin2021": "The coverage of forty million scholarly documents by Microsoft Academic Graph, Dimensions, Scopus, OpenAlex, and Crossref",
    "visser2021": "Large-scale comparison of bibliographic data sources: Scopus, Web of Science, Dimensions, Crossref, and Microsoft Academic",
    "mongeon2016": "The journal coverage of Web of Science and Scopus: a comparative analysis",
    "waltman2012": "A new methodology for constructing a publication-level classification system of science",
    "wohlin2014": "Guidelines for snowballing in systematic literature studies and a replication in software engineering",
    "jalali2012": "Systematic literature studies: database searches vs. backward snowballing",
    "kitchenham2004": "Procedures for performing systematic reviews",
    "petersen2015": "Guidelines for conducting systematic mapping studies in software engineering: An update",
    "marshall2019": "Toward systematic review automation: a practical guide to using machine learning tools in research synthesis",
    "swanson1986": "Undiscovered public knowledge",
    "salton1988": "Term-weighting approaches in automatic text retrieval",
    "robertson2009": "The probabilistic relevance framework: BM25 and beyond",
    "manning2008": "Introduction to information retrieval",
    "brin1998": "The anatomy of a large-scale hypertextual web search engine",
    "kleinberg1999": "Authoritative sources in a hyperlinked environment",
    "jeh2002": "SimRank: a measure of structural-context similarity",
    "tong2006": "Fast random walk with restart and its applications",
    "wang2013": "Quantifying the evolution of individual scientific impact",
    "parolo2015": "Attention decay in science",
    "hicks2015": "The Leiden Manifesto for research metrics",
    "wilsdon2015": "The metric tide: report of the independent review of the role of metrics in research assessment and management",
    "ioannidis2005": "Why most published research findings are false",
    "munafo2017": "A manifesto for reproducible science",
    "nosek2015": "Promoting an open research culture",
    "cohen1988": "Statistical power analysis for the behavioral sciences",
    "lakens2017": "Equivalence tests: a practical primer for t tests, correlations, and meta-analyses",
    "altman1995": "Absence of evidence is not evidence of absence",
    "simmons2011": "False-positive psychology: undisclosed flexibility in data collection and analysis allows presenting anything as significant",
    "gelman2014": "The statistical crisis in science",
    "nosek2018": "The preregistration revolution",
    "hardwicke2020": "Patterns of preregistration in scientific research",
    "chambers2013": "Registered reports: a new publishing initiative at Cortex",
    "fisher1925": "Statistical methods for research workers",
    "goodman2008": "A dirty dozen: twelve p-value misconceptions",
    "wasserman2004": "All of statistics: a concise course in statistical inference",
    "hastie2009": "The elements of statistical learning: data mining, inference, and prediction",
    "stuart2011": "Matching methods for causal inference: a review and a look forward",
    "rosenbaum1983": "The central role of the propensity score in observational studies for causal effects",
    "rubin1974": "Estimating causal effects of treatments in randomized and nonrandomized studies",
    "cochran1968": "The effectiveness of adjustment by subclassification in removing bias in observational studies",
    "shimodaira2000": "Improving predictive inference under covariate shift by weighting the log-likelihood function",
    "heckman1979": "Sample selection bias as a specification error",
    "moed2005": "Citation analysis in research evaluation",
    "schubert1996": "Cross-field normalization of scientometric indicators",
    "fanelli2010": "Positive results increase down the hierarchy of the sciences",
    "bollen2009": "A principal component analysis of 39 scientific impact measures",
    "bornmann2014": "Do altmetrics correlate with citations? A meta-analysis on forty-three million individual records",
    "lipton2018": "Troubling trends in machine learning scholarship",
    "sculley2015": "Hidden technical debt in machine learning systems",
    "wagstaff2020": "On the proven pitfalls of machine learning for computational biology",
    "kitchenham2009": "Empirical research methods in software engineering",
    "wohlin2012": "Experimentation in software engineering",
    "buckley2004": "Retrieval evaluation with incomplete information",
    "zobel2006": "Incomplete and biased relevance judgments in IR evaluation",
    "sanderson2010": "Test collection based evaluation of information retrieval systems",
    "sakai2016": "Statistical reform in information retrieval",
    "ferro2017": "Reproducibility of statistical tests based on IR evaluation measures",
    "fagin2003": "Comparing top k lists",
    "webber2010": "A similarity measure for indefinite rankings",
    "jarvelin2002": "Cumulated gain-based evaluation of IR techniques",
    "thompson1933": "On the likelihood that one unknown probability exceeds another in view of the evidence of two samples",
    "auer2002": "Finite-time analysis of the multiarmed bandit problem",
    "lattimore2020": "Bandit algorithms",
    "sutton1999": "Between MDPs and semi-MDPs: a framework for temporal abstraction in reinforcement learning",
    "tversky1974": "Judgment under uncertainty: heuristics and biases",
    "kahneman2011": "Thinking, fast and slow",
    "stroop1935": "Studies of interference in serial verbal reactions",
    "shannon1948": "A mathematical theory of communication",
    "zipf1949": "Human behavior and the principle of least effort",
    "lotka1926": "The frequency distribution of scientific productivity",
    "bradford1934": "Sources of information on specific subjects",
    "hirsch2005": "An index to quantify an individual's scientific research output",
    "egghe2006": "Theory and practise of the g-index",
    "waltman2012b": "Towards a new crown indicator: an empirical analysis",
    "ruiz2013": "Interpreting bibliometric data: a guide for the evaluation of research",
    "narin1976": "Evaluative bibliometrics: the use of publication and citation analysis in the evaluation of scientific activity",
    "peritz1983": "A classification of citation roles for the social sciences and related fields",
    "moravcsik1975": "Some results on the function and quality of citations",
    "gilbert1977": "Referencing as persuasion",
    "merton1968": "The Matthew effect in science",
    "cole1973": "Citation and the evaluation of scientific output",
    "mccain1989": "Descriptor and citation scattering in the development of a scientific specialty",
    "white1998": "On the use of informetric models in online bibliographic retrieval",
    "lawani1982": "On the heterogeneity and classification of author self-citations",
    "schubert1987": "Cross-field comparison of scientometric indicators",
    "glanzel1996": "A bibliometric approach to social sciences: national research performances in border fields",
    "hicks1999": "The difficulty of achieving full coverage of international social science literature and some consequences",
    "vanleeuwen2001": "Bibliometric analysis of the Dutch research performance in an international context",
    "anderson2004": "The metric tide reconsidered",
    "osterloh2004": "Co-authorship and collaboration in scientific publishing",
    "wuchty2007": "The increasing dominance of teams in production of knowledge",
    "jones2009": "Multi-university research teams: shifting impact, geography, and stratification in science",
    "fortunato2018": "Science of science",
    "zeng2017": "The science of science: big data and the science of citation",
    "ioannidis2014b": "How to make more published research true",
    "nosek2012": "Scientific utopia: I. Opening scientific communication",
    "miguel2014": "Promoting transparency in social science research",
    "christensen2019": "A study of the reproducibility of research in the social and behavioral sciences",
    "hardwicke2018": "Data availability, data reuse, and data citation in social science research",
    "stodden2016": "Enhancing reproducibility for computational methods",
    "donoho2009": "Reproducible research: computing and the scientific method",
    "peng2011": "Reproducible research in computational science",
    "kowalczyk2013": "The scientific method in practice: reproducibility in the computational sciences",
    "hutson2018": "Artificial intelligence faces reproducibility crisis",
    "haibe2012": "Independent component analysis uncovers the landscape of activity of the mitotic spindle",
    "raghavan2019": "On the reproducibility of neural network hyperparameter studies",
}


def main():
    doc = json.load(open(SLOTS))
    missing, extra = [], []
    for slot in doc["slots"]:
        want = WANT.get(slot["key"], slot.get("want_title"))
        if want is None:
            missing.append(slot["key"])       # no expected title from either source: a real gap
        else:
            slot["want_title"] = want
    for k in WANT:
        if not any(s["key"] == k for s in doc["slots"]):
            extra.append(k)                   # an expected title with no slot is a stale belief
    if missing:
        print("no want_title for: %s" % ", ".join(missing), file=sys.stderr)
    if extra:
        print("want_title for absent slot: %s" % ", ".join(extra), file=sys.stderr)
    if missing or extra:
        return 1
    doc["_want_title_rule"] = ("`want_title` is the title this study BELIEVES the work has; the registry "
                              "is asked to falsify it. A record is accepted only if the returned title "
                              "matches this one under two-way content-word containment (exact equality "
                              "when either title has three or fewer content words) AND the year agrees.")
    with open(SLOTS, "w") as fh:
        fh.write(json.dumps(doc, indent=1, sort_keys=False) + "\n")
    print("attached want_title to %d slot(s)" % len(doc["slots"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
