#!/usr/bin/env python3
"""refs_seeds.py -- the candidate pool that build_refs.py tries to resolve.

Each row is `slug: (title as I believe it to be, year)`. Nothing here is a reference: a seed is
a *proposal* to the registry, and only a record the registry returns becomes a reference. A seed
the registry refuses is printed with its reason and never enters refs.json, so a wrong guess
costs a query rather than a fabricated citation.

The pool is grouped by the role the work plays in this paper, because a reference earns its place
by the sentence it supports, not by sharing vocabulary with a title.
"""
# slug -> (query title, expected year or None)
SEEDS = {
    # ---- censoring and survival analysis: what an incomplete observation leaves -------------
    "kaplan-meier-1958": ("Nonparametric estimation from incomplete observations", 1958),
    "cox-1972": ("Regression models and life-tables", 1972),
    "turnbull-1976": ("The empirical distribution function with arbitrarily grouped, censored and truncated data", 1976),
    "efron-1967": ("The two sample problem with censored data", 1967),
    "andersen-gill-1982": ("Cox's regression model for counting processes: a large sample study", 1982),
    "fleming-harrington-1991": ("Counting Processes and Survival Analysis", 1991),
    "gentleman-geyer-1994": ("Maximum likelihood for interval censored data: consistency and computation", 1994),
    "lagakos-1979": ("General right censoring and its impact on the analysis of survival data", 1979),
    "lawless-2003": ("Statistical Models and Methods for Lifetime Data", 2003),
    "kalbfleisch-prentice-2002": ("The Statistical Analysis of Failure Time Data", 2002),
    "woodroofe-1985": ("Estimating a distribution function with truncated data", 1985),
    "turnbull-1974": ("Coloring the theory of survival analysis", 1974),

    # ---- missing data and coarsening: the same estimand, a different vocabulary ------------
    "rubin-1976": ("Inference and missing data", 1976),
    "little-rubin-2019": ("Statistical Analysis with Missing Data", 2019),
    "heitjan-rubin-1991": ("Ignorability and coarse data", 1991),
    "tsiatis-2006": ("Semiparametric Theory and Missing Data", 2006),
    "horowitz-manski-2000": ("Nonparametric analysis of randomized experiments with missing covariate and outcome data", 2000),

    # ---- partial identification: the identified set as the object -------------------------
    "manski-1990": ("Nonparametric bounds on treatment effects", 1990),
    "manski-2003": ("Partial Identification of Probability Distributions", 2003),
    "tamer-2010": ("Partial identification in econometrics", 2010),
    "molinari-2020": ("Microeconometrics with partial identification", 2020),
    "rosenbaum-2002": ("Observational Studies", 2002),

    # ---- quantiles, order statistics and what a sample can pin down -----------------------
    "bahadur-1966": ("A note on quantiles in large samples", 1966),
    "serfling-1980": ("Approximation Theorems of Mathematical Statistics", 1980),
    "david-nagaraja-2003": ("Order Statistics", 2003),
    "arnold-balakrishnan-nagaraja-2008": ("A First Course in Order Statistics", 2008),
    "reiss-1989": ("Approximate Distributions of Order Statistics", 1989),
    "wilks-1941": ("Determination of sample sizes for setting tolerance limits", 1941),
    "wilks-1942": ("Statistical prediction intervals", 1942),
    "wald-1943": ("An extension of Wilks' method for setting tolerance limits", 1943),
    "hahn-meeker-1991": ("Statistical Intervals: A Guide for Practitioners", 1991),
    "gumbel-1958": ("Statistics of Extremes", 1958),

    # ---- extreme value theory: the tail modelled, not merely observed ---------------------
    "fisher-tippett-1928": ("Limiting forms of the frequency distribution of the largest or smallest member of a sample", 1928),
    "gnedenko-1943": ("Sur la distribution limite du terme maximum d'une serie aleatoire", 1943),
    "balkema-dehaan-1974": ("Residual life time at great age", 1974),
    "pickands-1975": ("Statistical inference using extreme order statistics", 1975),
    "davison-smith-1990": ("Models for exceedances over high thresholds", 1990),
    "smith-1987": ("Estimating tails of probability distributions", 1987),
    "coles-2001": ("An Introduction to Statistical Modeling of Extreme Values", 2001),
    "embrechts-kluppelberg-mikosch-1997": ("Modelling Extremal Events for Insurance and Finance", 1997),
    "dehaan-ferreira-2006": ("Extreme Value Theory: An Introduction", 2006),
    "scarrott-macdonald-2012": ("A review of extreme value threshold estimation and uncertainty quantification", 2012),
    "mcneil-frey-2015": ("Quantitative Risk Management: Concepts, Techniques and Tools", 2015),
    "glasserman-2000": ("Variance reduction techniques for estimating value-at-risk", 2000),

    # ---- tail latency in real systems ------------------------------------------------------
    "dean-barroso-2013": ("The tail at scale", 2013),
    "barroso-holzle-2009": ("The Datacenter as a Computer: An Introduction to the Design of Warehouse-Scale Machines", 2009),
    "xu-bobtail-2013": ("Bobtail: avoiding long tails in the cloud", 2013),
    "li-tales-tail-2014": ("Tales of the tail: hardware, OS, and application-level sources of tail latency", 2014),
    "cidon-cliffhanger-2017": ("Cliffhanger: scaling performance cliffs in web memory caches", 2017),
    "wang-serverless-curtains-2018": ("Peeking behind the curtains of serverless platforms", 2018),
    "shahrad-serverless-wild-2020": ("Serverless in the wild: characterizing and optimizing the serverless workload at a large cloud provider", 2020),
    "hellerstein-serverless-2019": ("Serverless computing: one step forward, two steps back", 2019),
    "jonas-berkeley-serverless-2019": ("Cloud programming simplified: a Berkeley view on serverless computing", 2019),

    # ---- timeouts, retries and failure detection ------------------------------------------
    "gray-1985": ("Why do computers stop and what can be done about it", 1985),
    "huang-gray-failure-2017": ("Gray failure: the Achilles' heel of cloud-scale systems", 2017),
    "bronson-metastable-2021": ("Metastable failures in distributed systems", 2021),
    "maurer-fail-at-scale-2015": ("Fail at scale: reliability in the face of rapid change", 2015),
    "hayashibara-phi-2004": ("The phi accrual failure detector", 2004),
    "nygard-release-it-2018": ("Release It! Design and Deploy Production-Ready Software", 2018),

    # ---- queueing: where a tail comes from ------------------------------------------------
    "kingman-1961": ("The single server queue in heavy traffic", 1961),
    "kleinrock-1975": ("Queueing Systems, Volume 1: Theory", 1975),
    "whitt-2002": ("Stochastic-Process Limits: An Introduction to Stochastic-Process Limits and Their Application to Queues", 2002),
    "whitt-1993": ("Approximations for the GI/G/m queue", 1993),

    # ---- measurement methodology: is the number a measurement at all ----------------------
    "georges-2007": ("Statistically rigorous Java performance evaluation", 2007),
    "mytkowicz-2009": ("Producing wrong data without doing anything obviously wrong!", 2009),
    "curtsinger-stabilizer-2013": ("STABILIZER: statistically sound performance evaluation", 2013),
    "hoefler-belli-2015": ("Scientific benchmarking of parallel computing systems", 2015),
    "lilja-2000": ("Measuring Computer Performance: A Practitioner's Guide", 2000),
    "jain-1991": ("The Art of Computer Systems Performance Analysis", 1991),
    "schad-cloud-variance-2010": ("Runtime measurements in the cloud: observing, analyzing, and reducing variance", 2010),
    "lenk-iaas-2011": ("What are you paying for? Performance benchmarking for Infrastructure-as-a-Service offerings", 2011),
    "iosup-cloud-2011": ("Performance analysis of cloud computing services for many-tasks scientific computing", 2011),
    "leitner-chaos-2016": ("Patterns in the chaos: a study of performance variation and predictability in public IaaS clouds", 2016),

    # ---- controlled experiments and online measurement -----------------------------------
    "kohavi-online-2013": ("Online controlled experiments at large scale", 2013),
    "kohavi-trustworthy-2020": ("Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing", 2020),

    # ---- cluster and workload characterisation -------------------------------------------
    "reiss-google-traces-2011": ("Google cluster-usage traces: format and schema", 2011),
    "verma-borg-2015": ("Large-scale cluster management at Google with Borg", 2015),
    "tirmazi-borg-2020": ("Borg: the next generation", 2020),
    "cortez-resource-central-2017": ("Resource central: understanding and predicting workloads for improved resource management in large cloud platforms", 2017),
    "gandhi-autoscale-2014": ("Autoscale: dynamic, robust capacity management for multi-tier data centers", 2014),

    # ---- tracing and observability: where the measurement is taken ------------------------
    "sigelman-dapper-2010": ("Dapper, a large-scale distributed systems tracing infrastructure", 2010),
    "mace-pivot-2015": ("Pivot tracing: dynamic causal monitoring for distributed systems", 2015),

    # ---- statistics the argument leans on ------------------------------------------------
    "wilson-1927": ("Probable inference, the law of succession, and statistical inference", 1927),
    "clopper-pearson-1934": ("The use of confidence or fiducial limits illustrated in the case of the binomial", 1934),
    "hoeffding-1963": ("Probability inequalities for sums of bounded random variables", 1963),
    "efron-tibshirani-1993": ("An Introduction to the Bootstrap", 1993),
    "wasserman-2004": ("All of Statistics: A Concise Course in Statistical Inference", 2004),
    "casella-berger-2002": ("Statistical Inference", 2002),
    "lehmann-casella-1998": ("Theory of Point Estimation", 1998),
    "bickel-doksum-2015": ("Mathematical Statistics: Basic Ideas and Selected Topics", 2015),

    # ---- service level objectives and reliability practice -------------------------------
    "beyer-sre-2016": ("Site Reliability Engineering: How Google Runs Production Systems", 2016),
    "turnbull-sre-workbook-2018": ("The Site Reliability Workbook", 2018),

    # ---- sampling and estimation of rare events ------------------------------------------
    "neyman-1934": ("On the two different aspects of the representative method", 1934),
    "tille-2006": ("Sampling Algorithms", 2006),
    "thompson-1932": ("On the theory of apportionment", 1932),

    # ---- performance of distributed storage and caches (tail sources) ---------------------
    "ousterhout-ramcloud-2015": ("The RAMCloud storage system", 2015),
    "hunt-memcached-2020": ("Scaling memcache at Facebook", 2020),

    # ---- censoring in engineering reliability --------------------------------------------
    "meeker-escobar-1998": ("Statistical Methods for Reliability Data", 1998),
    "nelson-1990": ("Accelerated Testing: Statistical Models, Test Plans, and Data Analyses", 1990),

    # ---- interval estimation and coverage ------------------------------------------------
    "brown-cai-dasgupta-2001": ("Interval estimation for a binomial proportion", 2001),
    "agresti-coull-1998": ("Approximate is better than exact for interval estimation of binomial proportions", 1998),
    "newcombe-1998": ("Two-sided confidence intervals for the single proportion: comparison of seven methods", 1998),

    # ---- records, maxima and rare observations -------------------------------------------
    "arnold-balakrishnan-1998": ("Records", 1998),
    "neville-1911": ("On the frequency distribution of the greatest of a number of observations", 1911),

    # ---- load, capacity and the effect of retries ----------------------------------------
    "bodik-2005": ("A case for automatic system evaluation", 2005),
    "schroeder-2006": ("Web search for unstructured data", 2006),
    "welch-1983": ("The statistical analysis of simulation output data", 1983),
    "heidelberger-1981": ("A spectral method for confidence interval generation and run length control in simulations", 1981),

    # ---- quantile estimation specifically ------------------------------------------------
    "chen-hall-1993": ("Smoothed empirical likelihood confidence intervals for quantiles", 1993),
    "francisco-2001": ("Confidence intervals for quantiles", 2001),
    "zhang-2016": ("Confidence intervals for quantiles", 2016),

    # ---- decision theory: what a certification buys --------------------------------------
    "wald-1950": ("Statistical Decision Functions", 1950),
    "berger-1985": ("Statistical Decision Theory and Bayesian Analysis", 1985),

    # ---- software performance engineering in practice -------------------------------------
    "smith-1990": ("Software Performance Engineering", 1990),
    "woodside-2007": ("The future of software performance engineering", 2007),

    # ---- distributed systems monitoring ------------------------------------------------
    "rabkin-2012": ("Aggregation and decline in performance", 2012),
    "reynolds-2015": ("Pipeflow: a descriptive approach to data-parallel systems", 2015),

    # ---- more survival analysis, where the censoring vocabulary is standardised ----------
    "miller-survival-1981": ("Survival Analysis", 1981),
    "cox-oakes-1984": ("Analysis of Survival Data", 1984),
    "nelson-applied-life-1982": ("Applied Life Data Analysis", 1982),
    "andersen-borgan-gill-keiding-1993": ("Statistical Models Based on Counting Processes", 1993),
    "martinussen-scheike-2006": ("Dynamic Regression Models for Survival Data", 2006),
    "lin-wei-1989": ("The robust inference for the Cox proportional hazards model", 1989),
    "efron-1988": ("Logistic regression, survival analysis, and the Kaplan-Meier curve", 1988),

    # ---- empirical processes and the distribution-function tools the bounds rest on ------
    "rao-linear-inference-1973": ("Linear Statistical Inference and Its Applications", 1973),
    "cramer-1946": ("Mathematical Methods of Statistics", 1946),
    "dvoretzky-kiefer-wolfowitz-1956": ("Asymptotic minimax character of the sample distribution function and of the classical multinomial estimator", 1956),
    "massart-1990": ("The tight constant in the Dvoretzky-Kiefer-Wolfowitz inequality", 1990),
    "anderson-darling-1952": ("Asymptotic theory of certain goodness of fit criteria based on stochastic processes", 1952),
    "shorack-wellner-1986": ("Empirical Processes with Applications to Statistics", 1986),
    "vandervaart-wellner-1996": ("Weak Convergence and Empirical Processes", 1996),

    # ---- more extreme value estimation, and threshold choice ----------------------------
    "hosking-wallis-1987": ("Parameter and quantile estimation for the generalized Pareto distribution", 1987),
    "grimshaw-1993": ("Computing maximum likelihood estimates for the generalized Pareto distribution", 1993),
    "katz-2002": ("Statistics of extremes in hydrology", 2002),

    # ---- queueing and its approximations ------------------------------------------------
    "harchol-balter-2013": ("Performance Modeling and Design of Computer Systems", 2013),
    "abate-whitt-1992": ("The Fourier-series method for inverting transforms of probability distributions", 1992),

    # ---- measurement as a discipline ----------------------------------------------------
    "box-1976": ("Science and statistics", 1976),
    "tukey-1962": ("The future of data analysis", 1962),
    "tukey-1977": ("Exploratory Data Analysis", 1977),
    "box-hunter-hunter-2005": ("Statistics for Experimenters: Design, Innovation, and Discovery", 2005),
    "montgomery-2017": ("Design and Analysis of Experiments", 2017),
    "shewhart-1931": ("Economic Control of Quality of Manufactured Product", 1931),
    "rubino-rare-event-2009": ("Rare Event Simulation using Monte Carlo Methods", 2009),

    # ---- cloud and datacenter characterisation -----------------------------------------
    "benson-2010": ("Network traffic characteristics of data centers in the wild", 2010),
    "reiss-heterogeneity-2012": ("Heterogeneity and dynamicity of clouds at scale: Google trace analysis", 2012),
    "greenberg-vl2-2009": ("VL2: a scalable and flexible data center network", 2009),
    "ousterhout-ramcloud-case-2011": ("The case for RAMCloud", 2011),

    # ---- serverless performance and economics ------------------------------------------
    "mcgrath-2017": ("Serverless computing: design, implementation, and performance", 2017),
    "lloyd-2018": ("Serverless computing: an investigation of factors influencing microservice performance", 2018),
    "eivy-2017": ("Be wary of the economics of serverless cloud computing", 2017),

    # ---- partial identification and moment inequalities, in the journals that index well ---
    "imbens-manski-2004": ("Confidence intervals for partially identified parameters", 2004),
    "chernozhukov-hong-tamer-2007": ("Estimation and confidence regions for parameter sets in econometric models", 2007),
    "andrews-soares-2010": ("Inference for parameters defined by moment inequalities using generalized moment selection", 2010),
    "romano-shaikh-2008": ("Inference for identifiable parameters in partially identified econometric models", 2008),
    "bugni-2010": ("Bootstrap inference in partially identified models defined by moment inequalities", 2010),
    "newey-mcfadden-1994": ("Large sample estimation and hypothesis testing", 1994),
    "manski-2007": ("Partial identification of counterfactual choice probabilities", 2007),

    # ---- quantiles, the bootstrap and the accuracy of an interval -------------------------
    "koenker-bassett-1978": ("Regression quantiles", 1978),
    "efron-1979": ("Bootstrap methods: another look at the jackknife", 1979),
    "bickel-freedman-1981": ("Some asymptotic theory for the bootstrap", 1981),
    "singh-1981": ("On the asymptotic accuracy of Efron's bootstrap", 1981),
    "mosteller-1946": ("On some useful inefficient statistics", 1946),
    "beran-1982": ("Estimated sampling distributions: the bootstrap and competitors", 1982),
    "stigler-1973": ("The asymptotic distribution of the trimmed mean", 1973),
    "efron-1987": ("Better bootstrap confidence intervals", 1987),
    "diciccio-romano-1988": ("A review of bootstrap confidence intervals", 1988),
    "hall-1986": ("On the number of bootstrap simulations required to construct a confidence interval", 1986),
    "beran-1987": ("Prepivoting to reduce level error of confidence sets", 1987),
    "wilks-1948": ("Order statistics", 1948),

    # ---- censoring and competing risks in the journals -------------------------------
    "prentice-1978": ("The analysis of failure times in the presence of competing risks", 1978),
    "escobar-meeker-2006": ("A review of accelerated test models", 2006),

    # ---- queues, heavy traffic and the shape of a tail -------------------------------
    "kingman-1962": ("On queues in heavy traffic", 1962),
    "halfin-whitt-1981": ("Heavy-traffic limits for queues with many exponential servers", 1981),
    "reiman-1984": ("Open queueing networks in heavy traffic", 1984),

    # ---- extremes, estimated from few observations -----------------------------------
    "davison-1984": ("Modelling excesses over high thresholds, with an application", 1984),
    "hosking-1990": ("L-moments: analysis and estimation of distributions using linear combinations of order statistics", 1990),

    # ---- systems, as published in venues a registry indexes --------------------------
    "armbrust-2010": ("A view of cloud computing", 2010),
    "barroso-2003": ("Web search for a planet: the Google cluster architecture", 2003),
    "blackburn-2006": ("The DaCapo benchmarks: Java benchmarking development and analysis", 2006),
    "ferdman-2012": ("Clearing the clouds: a study of emerging scale-out workloads on modern hardware", 2012),
    "kanev-2015": ("Profiling a warehouse-scale computer", 2015),
    "ousterhout-sparrow-2013": ("Sparrow: distributed, low latency scheduling", 2013),
    "gunawi-2014": ("What bugs live in the cloud? A study of 3000+ issues in cloud systems", 2014),
    "calzarossa-2016": ("Workload characterization: a survey revisited", 2016),
    "calzarossa-1993": ("Workload characterization: a survey", 1993),
    "stephenson-2003": ("Mars code", 2003),
    "bodik-2010": ("Characterizing, modeling, and generating workload spikes for stateful services", 2010),
}

# Seeds the registry DID resolve, and which are nonetheless not references for this paper. A seed
# that resolves is not a citation: `admissible()` compares titles, and a title match says nothing
# about whether the work supports a sentence. Each row below is a real record in the wrong field,
# found by reading the resolved titles (2026-10-31) rather than by trusting the verdict.
EXCLUDE = {
    "bodik-2005": "resolved to an optics paper ('automatic birefringence evaluation system'), not workload characterisation; the query's words matched and the subject did not",
    "hunt-memcached-2020": "resolved to a static-analysis paper ('Scaling static analyses at Facebook'), not the Memcached paper; 'memcache' vs 'static analyses' passed the folding rule",
    "schroeder-2006": "resolved to an information-retrieval paper about unstructured-data search; nothing in it speaks to censored latency, and the seed was a half-recalled title",
    "efron-1967": "resolved title differs materially from the work meant ('k-sample ... truncated and censored' vs 'two sample ... censored'); the censoring story is carried by other references",
    "hayashibara-phi-2004": "the record's title is mangled by IEEE metadata ('The /spl phi/ accrual failure detector') and would print garbled in the bibliography",
}

# Book seeds are held to a stricter rule by `admissible()`: a book review carries the book's title
# and a DOI, so title equality alone would admit the review as the book.
BOOK_SEEDS = {
    "fleming-harrington-1991", "lawless-2003", "kalbfleisch-prentice-2002", "little-rubin-2019",
    "tsiatis-2006", "manski-2003", "serfling-1980", "david-nagaraja-2003",
    "arnold-balakrishnan-nagaraja-2008", "reiss-1989", "hahn-meeker-1991", "gumbel-1958",
    "coles-2001", "embrechts-kluppelberg-mikosch-1997", "dehaan-ferreira-2006",
    "mcneil-frey-2015", "barroso-holzle-2009", "nygard-release-it-2018", "kleinrock-1975",
    "whitt-2002", "lilja-2000", "jain-1991", "kohavi-trustworthy-2020", "efron-tibshirani-1993",
    "wasserman-2004", "casella-berger-2002", "lehmann-casella-1998", "bickel-doksum-2015",
    "beyer-sre-2016", "turnbull-sre-workbook-2018", "tille-2006", "meeker-escobar-1998",
    "nelson-1990", "arnold-balakrishnan-1998", "wald-1950", "berger-1985", "rosenbaum-2002",
    "miller-survival-1981", "cox-oakes-1984", "nelson-applied-life-1982",
    "andersen-borgan-gill-keiding-1993", "martinussen-scheike-2006", "rao-linear-inference-1973",
    "cramer-1946", "shorack-wellner-1986", "vandervaart-wellner-1996", "harchol-balter-2013",
    "tukey-1977", "box-hunter-hunter-2005", "montgomery-2017", "shewhart-1931",
    "rubino-rare-event-2009",
}
