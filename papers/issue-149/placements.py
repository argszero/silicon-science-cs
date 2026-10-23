"""Authored placement of every kept corpus entry: which section it serves, which claim it supports.

Why this is authored and not derived: a word-level relevance gate cannot tell a term the paper
uses from a term that merely appears. The gate that built the corpus kept "Agile Software
Assurance: An Empirical Study" under the word `empirical`, retail-channel conflict resolution
under `conflict`, and an acoustic-sensing Python ecosystem under `ecosystem`. No title predicate
catches that class, because the title is not wrong -- the word is a homonym. Only the question
"which claim does this sentence support?" catches it, and that question has a human answer.

So the pool is decided here, in two buckets, and `place_references.py` enforces the whole
correspondence: every kept entry is placed exactly once or pruned with a reason, every key named
here resolves to exactly one kept entry, and the placed count is the number the manuscript may
draw on. A citation that cannot be placed is padding even when the record is real.
"""

# The manuscript's structure, declared once. Placement names one of these; the gate refuses a
# section that is not declared here, so a section cannot quietly appear in the corpus report.
SECTIONS = {
    "S1": "Introduction and motivation: why an unpinned declaration costs reproducibility",
    "S2": "Setting: what one declaration admits (the depth-1 construct)",
    "S3": "Coupling: solution-set dispersion at depth 2",
    "S4": "The dialect: bounded versus unbounded ranges (the headline mechanism)",
    "S5": "Ecosystem practice: npm, PyPI and their conventions",
    "S6": "Evidence practice: registries as data, and what a registry metric measures",
    "S7": "Alternatives: exact pins, lockfiles, functional package management, containers, model registries",
    "S8": "Theory setting: constraint classes and cover problems",
    "S9": "Method: interval estimation for a proportion",
    "S10": "Threats to validity",
}

# key -> (section id, the claim this entry supports in that section)
PLACEMENTS = {
    # ---- S1 motivation -------------------------------------------------------------------
    "alnoamany2018computationalreproducibilityres": ("S1", "researchers' own sharing practice is treated as the reproducibility lever, which leaves the declaration unexamined"),
    "bhatt2020reproduciblesoftwareenvironment": ("S1", "a tool that makes the environment, not the manifest, the unit of reproduction"),
    "cavezza2014reproducibilityenvironmentdepende": ("S1", "environment-dependent failures reproduce differently in different environments: the failure mode an over-wide range admits"),
    "hatton2019computationalreproducibilityelepha": ("S1", "the reproducibility gap stated as a field-level problem rather than a tooling defect"),
    "heroux2011improvingcsesoftware": ("S1", "reproducibility treated as an engineering requirement with acceptance criteria"),
    "milewicz2023evidencebasedsoftware": ("S1", "evidence-based quality practices for reproducibility: what evidence a reproducibility claim needs"),
    "ferreira2026persistenciavulnerabilidadesdepe": ("S1", "vulnerability persistence by dependency class in npm projects: an over-wide range keeps a vulnerable version admissible over time"),

    # ---- S2 the depth-1 construct --------------------------------------------------------
    "claes2015historicalanalysisdebian": ("S2", "incompatibilities are studied as historical events; the declaration that admitted them is not the unit of analysis"),
    "decan2016topologypackagedependency": ("S2", "dependency-network topology is measured on one declared version per package, which presumes the declaration names one"),
    "lyu2025detectingbuilddependency": ("S2", "build-dependency errors are found by executing the build, which presumes the declaration resolves to a single state"),
    "reyes2024breakinggoodexplaining": ("S2", "breaking updates are diagnosed from build output afterwards; the admissible set is never consulted beforehand"),
    "gu2022pkgndeptoolheaviness": ("S2", "dependency cost is measured per declared dependency, taking the declaration as one object"),
    "lavalndpackagedependenciesanalysis": ("S2", "remediation presumes a single resolved state to repair"),
    "shaffer2021empiricalstudypackage": ("S2", "which declared dependencies survive is measured per declaration, not per admissible version"),

    # ---- S3 coupling at depth 2 ----------------------------------------------------------
    "qi2024empiricalstudydownstream": ("S3", "downstream dependency groups are the closest prior question to our coupling measure, but the analysis fixes one version per package"),
    "gibb2026packagemanagerscarte": ("S3", "a formal model of dependency resolution answers which solution exists, not how many the declaration admits"),
    "rajendran2025primitivaalgebraicdecomposition": ("S3", "algebraic decomposition for zero-conflict resolution is a solver-side contribution"),
    "gibb2025solvingpackagemanagement": ("S3", "the hypergraph formulation of resolution addresses the same object whose admissible-set size we count"),
    "pinckney2023flexibleoptimaldependency": ("S3", "optimal selection given constraints: optimality is defined over the set of admissible solutions"),
    "pan2020researchdynamicdetection": ("S3", "conflicts are detected dynamically at build time, i.e. after a choice has already been made"),
    "wang2025understandingdetectingpeer": ("S3", "peer-dependency resolving loops: a second, harder resolution mode in the same ecosystem"),
    "lake2025analyzingdependencyclusters": ("S3", "dependency clusters in Maven Central: structure of the resolved graph, not of the declaration"),
    "li2023empiricalstudyyanked": ("S3", "yanked releases are the impossibility argument's own exception; they are counted here rather than assumed away"),
    "zhu2026versionedtransitivedependency": ("S3", "the transitive closure treated as a versioned object, without counting how many closures a declaration admits"),

    # ---- S4 the dialect ------------------------------------------------------------------
    "decan2021whatpackagedependencies": ("S4", "declared constraints are read as compatibility promises: exactly the reading the dialect measure tests"),
    "li2023largescaleempirical": ("S4", "semantic-versioning compliance in Go: a convention stated but not enforced"),
    "opdebeeck2021practicesemanticversioning": ("S4", "semver practice for Ansible roles: a third dialect with its own boundedness"),
    "anon1976numberingschemecomputer": ("S4", "a 1976 numbering scheme for a program library: version numbering is a design decision with consequences"),
    "kellerndversionnumberingscheme": ("S4", "lexicographic ordering of version numbers: ordering is a convention, not a property of the artifact"),

    # ---- S5 ecosystem practice -----------------------------------------------------------
    "serbout2023interactivelyexploringapi": ("S5", "API-change and versioning consistency in practice: a declared version is not a proxy for change"),
    "sousa2009analysispackagedependency": ("S5", "Debian dependency structure analysed as a distribution-level graph"),
    "nascimento2022exploringapideprecation": ("S5", "API deprecation practice in JavaScript: deprecation is announced, removal still breaks unpinned ranges"),
    "foote2013rolesresponsibilitiespackage": ("S5", "the maintainer's role: who authors the declaration, and on what evidence"),
    "chodorowski2021comparativeanalysisjavascript": ("S5", "npm versus yarn: two managers resolve the same declarations differently"),
    "cogo2021empiricalstudydependency": ("S5", "dependency downgrades in npm: the resolved version moves independently of the declaration"),
    "decan2018evolutiontechnicallag": ("S5", "technical lag: how far behind a declaration leaves an install"),
    "miller2025understandingresponseopen": ("S5", "ecosystem response to abandonment: what happens when an admissible version disappears"),
    "bommarito2019empiricalanalysispython": ("S5", "PyPI as an ecosystem object: size, growth, and what registry data can show"),
    "termphaiboon2025exploringsecuritydependency": ("S5", "PyPI dependency chains and security-disclosure practice"),
    "moracantallops2020evolutionprospectscomprehe": ("S5", "CRAN evolution: a third ecosystem with its own versioning conventions"),
    "wittern2016lookdynamicsjavascript": ("S5", "the JavaScript ecosystem's dynamics measured from registry metadata"),

    # ---- S6 evidence practice ------------------------------------------------------------
    "montaruli2026sourcebrokenlargescale": ("S6", "SourceRank reliability: a registry-derived metric that does not measure what its name says, which is why our rates carry an explicit denominator"),
    "kula2023promisesperilsmining": ("S6", "promises and perils of mining package-ecosystem data: the methodological warrant for a pinned snapshot"),
    "thirumalaisamy2025assistedverificationsbom": ("S6", "SBOM accuracy and drift: a dependency record that goes stale in place"),

    # ---- S7 alternatives -----------------------------------------------------------------
    "begoug2025understandingawsprovider": ("S7", "infrastructure-as-code providers are version-constrained artifacts with their own upgrade discipline"),
    "bottotobar2026dependencydateexploring": ("S7", "practitioner difficulty with automated dependency updates motivates measuring what the declaration permits"),
    "mecheo2026dependafixgithubapp": ("S7", "automation repairs breaking updates after the fact, treating the update rather than the declaration as the unit"),
    "reyes2026byamfixingbreaking": ("S7", "LLM-based repair of breaking updates: a post-hoc remedy, complementary to measuring admissibility"),
    "mittal2025evaluatingcontainersecurity": ("S7", "container images as an alternative pinning mechanism, evaluated for security and reproducibility"),
    "nakata2021evaluationvulnerabilityreproducibi": ("S7", "container-based environments: reproducibility of a vulnerability depends on the pinned base image"),
    "peer2020activemaintenanceproposal": ("S7", "long-term reproducibility needs maintenance over time, not a one-off pin"),
    "begoug2024howinfrastructurecode": ("S7", "IaC practitioners' provider-upgrade behaviour: the same declaration-versus-install tension in another ecosystem"),
    "schmid2026mavenlockfilehigh": ("S7", "Maven-Lockfile: high-integrity rebuild of past Java releases, i.e. the lockfile as the alternative to a range"),
    "varanasi2019mavendependencymanagement": ("S7", "Maven's mediation rule (nearest wins) as a range dialect with its own resolution semantics"),
    "almishev2025dependencymanagementstrategies": ("S7", "monorepo dependency-management strategies: resolution policy varies by build system, which is the dialect argument in another setting"),
    "gonzalez2026sklearnmigratorcross": ("S7", "cross-version migration of fitted models: a version bound that is not about code compatibility"),
    "raatikainen2025machinelearninglineage": ("S7", "lineage as the record of what a model was built against"),
    "ding2024scalablerobustmodel": ("S7", "model versioning as an artifact-identity problem distinct from code versioning"),
    "pulicharla2024dataversioningimpact": ("S7", "data versioning changes model behaviour: one declaration can admit different behaviour"),
    "wonsil2023integratedreproducibilityself": ("S7", "self-describing models carry their dependency identity instead of leaving it to be inferred from a range"),
    "bzeznik2017nixhpcpackage": ("S7", "Nix as an HPC package manager: derivation-level pinning"),
    "goswami2024reproduciblehighperformance": ("S7", "reproducible HPC without redundancy under Nix"),
    "hinsen2012nixpackagemanager": ("S7", "Nix in computational science: the store path as the identity"),
    "kowalewski2021sustainablepackagingquantum": ("S7", "domain packaging with Nix: the pin is the derivation, not a range"),
    "turner2025makeyourdevelopment": ("S7", "portable development environments as a reproducibility practice"),
    "yang2026reproduciblellmbased": ("S7", "reproducibility of a measurement depends on the serving stack, a version range that is not a code range"),
    "malka2024increasingtrustopen": ("S7", "reproducible builds as supply-chain trust"),
    "malka2025doesfunctionalpackage": ("S7", "functional package management does enable reproducible builds at scale: the strongest evidence for the alternative we compare against"),
    "randrianainandincrementalreproduciblebuilds": ("S7", "incremental reproducible builds of variants: the cost side of pinning"),

    # ---- S7, widening round: container-image tags ----------------------------------------
    # An image tag is a declaration with the same degree of freedom as a version range: it names
    # a set that can move. These are the works that already treat it as a problem.
    "ayres2021continuousautomotivesoftware": ("S7", "continuous updates delivered as container layers: the image, not the manifest, is the unit of change"),
    "b2024exploringlargescale": ("S7", "large-scale Docker image analysis: images are studied as artifacts with vulnerabilities and drift of their own"),
    "doan2022davsdockerfileanalysis": ("S7", "the Dockerfile is read as a declaration and its image scanned: the nearest container analogue of what we do to a manifest"),
    "kim2025robustframeworkcomprehensive": ("S7", "container image vulnerability assessment as an ongoing obligation rather than a one-off check"),
    "tekin2026deathendlongitudinal": ("S7", "a longitudinal study of automatic updates on containers: a mutable tag makes a published environment change under the reader"),
    "solarin2026justtimestampsstudy": ("S7", "Docker rebuilds are not reproducible even from the same inputs, so the tag is not the only source of drift, but it is the one the author controls"),
    "aranguren2015enhancedreproducibilitysadi": ("S7", "containerised workflows as the reproducibility mechanism in a domain science"),
    "bruccoleri2025dockerimagebuilder": ("S7", "a construction method for reproducible images: pinning at build time rather than at declaration time"),
    "cervera2026reproducibilitylegacyros": ("S7", "legacy research code made reproducible by pinning the image: the practitioner's alternative to pinning versions"),
    "kunstmann2024scientificworkflowdeployment": ("S7", "container provenance in HPC: the image's identity recorded as evidence, which is exactly what a tag does not do"),
    "mitrabehura2022singularitycontainersimprove": ("S7", "Singularity containers improve reproducibility: a second container dialect with a different pinning convention"),

    # ---- S7, widening round: model registries -------------------------------------------
    "alharbi2026enhancingtransparencyhugging": ("S7", "model-card generation on a public model hub: a registry where the declaration is prose and the artifact moves under it"),

    # ---- S8 theory setting ---------------------------------------------------------------
    "miguel2004constraintsatisfactionproblem": ("S8", "the standard CSP formulation, cited for stating a declaration as a constraint"),
    "carbonnel2015tractabilityconstraintsatisfact": ("S8", "tractability of constraint classes: the vocabulary in which our admissible-set problem is stated"),
    "carbonnelndharnessingtractabilityconstraint": ("S8", "harnessing tractability: restricted constraint languages are where structure becomes exploitable"),
    "cooper2010generalizingconstraintsatisfaction": ("S8", "hybrid tractability via variable elimination: the structural condition behind the closure result"),
    "ganian2015discoveringarchipelagostractabilit": ("S8", "islands of tractability: structure, not arity, decides the cost"),
    "duttandsurveyapproximationalgorithms": ("S8", "approximation bounds for cover: the source of the log-factor statement we test and find unattained"),
    "hochbaum2008multiintegerset": ("S8", "weighted and multi-integer cover: the general form our unit-cost instance degenerates from"),

    # ---- S9 method -----------------------------------------------------------------------
    "guan2012generalizedscoreconfidence": ("S9", "score intervals: the family the Wilson interval belongs to"),
    "habtzghi2014modifiedclopperpearson": ("S9", "conservative exact intervals: the coverage-versus-shortness trade-off we choose against"),
    "kim2021generalizedagresticoull": ("S9", "Agresti-Coull generalization and behaviour at small proportions, where several of our rates sit"),
    "garthwaite2023locallycorrectconfidence": ("S9", "criteria for judging an interval's correctness: why we report the interval we do"),
    "sandelius1952confidenceintervalsmallest": ("S9", "the smallest-proportion case treated historically: our lowest rates are of this kind"),

    # ---- five entries re-read when the widening fell short -------------------------------
    # These were first pruned, then re-read against the section they could serve. The test each
    # had to pass was not "is it relevant?" (they always were) but "does this paper make this
    # sentence?". Each now names a sentence the manuscript will actually contain. Recording the
    # move here rather than silently editing the bucket above: a placement decided under a
    # shortfall is exactly the kind that needs its reason written down.
    "nakanishindmetricevaluatingclass": ("S2", "upgrade risk is measured at the interface level in prior work; the declaration's admissible set is a different object"),
    "exman2019softwaremodularitycoupling": ("S5", "dependency structure represented as a bipartite graph: the representation our admissible-set object shares"),
    "kechagia2010opensourcelicensing": ("S5", "other properties of the same dependency edges are studied across the graph (licensing); the number of resolutions is not"),
    "wynnjr2007assessinghealthopen": ("S5", "ecosystem health is assessed at ecosystem level, which is orthogonal to whether one declaration admits one install"),
    "almendraarao2020adjustedwaldconfidence": ("S9", "adjusted Wald intervals: a variant we choose against, since Wald-type intervals misbehave where our smallest rates sit"),

    # ---- S5 (rescued) --------------------------------------------------------------------

    # ---- S9 (rescued) --------------------------------------------------------------------

    # ---- S10 threats ---------------------------------------------------------------------
    "hrtel2023operationalizingvalidityempirical": ("S10", "operationalizing validity claims: the frame in which our threats are stated"),
    "petersen2013worldviewsresearchmethods": ("S10", "worldview, method and validity are coupled: a rate here is a design-dependent statement"),
    "amir2018thererandomsampling": ("S10", "there is no random sampling in SE research: our population is a frame, and is described as one"),
    "baltes2022samplingsoftwareengineering": ("S10", "sampling guidelines: how a frame must be described for a rate to be interpretable"),
}

# The works this paper is measured AGAINST -- the "at least three real comparisons" bar. These
# are not context: each states a competing object or a competing answer, and the difference is
# what the paper must argue. Naming them here makes the report carry the argument rather than the
# count, because 100 verified entries do not satisfy this bar and this list does.
COMPARISON_KEYS = [
    ("gibb2026packagemanagerscarte",
     "A formal model of dependency RESOLUTION: given declarations, it defines which solution a "
     "solver returns. We do not model the solver; we count what the solver may choose among, so "
     "the two results are about different objects and neither subsumes the other."),
    ("gibb2025solvingpackagemanagement",
     "Hypergraph dependency resolution: a new encoding that makes solving faster. It is a "
     "contribution to the cost of choosing, and is silent on how many admissible choices a "
     "declaration leaves; our construction is the input it would have to run on."),
    ("pinckney2023flexibleoptimaldependency",
     "Max-SMT optimal dependency management: selects an optimal assignment under stated costs. "
     "Optimality is defined over the admissible set, which is exactly the set whose size we "
     "measure; the paper needs our quantity as a precondition and does not measure it."),
    ("reyes2026byamfixingbreaking",
     "LLM repair of breaking dependency updates: repairs a build after an update breaks it. This "
     "is post-hoc and per-update; we ask beforehand how much of the update space the declaration "
     "left open, so the remedy and the measurement are complementary rather than competing."),
    ("schmid2026mavenlockfilehigh",
     "Maven-Lockfile: high-integrity rebuild of past releases by recording resolved state. It is "
     "the strongest form of the alternative we compare against -- pin the resolution rather than "
     "bound the range -- and it prices the cost side of that alternative, not its necessity."),
    ("decan2021whatpackagedependencies",
     "Semantic versioning read as a compatibility promise. That reading is the belief our dialect "
     "measure tests: if a bounded range really did promise compatibility, ambiguity inside the "
     "range would carry no risk, and the decay curve would be flat in every stratum. It is not."),
]

# key -> why it is out of the pool. Every kept entry is placed or pruned; nothing is dropped
# silently, and the count of prunes is reported beside the count of placements.
PRUNED = {
    # homonyms: the word appears, the construct does not
    "suber2008visualizingrepositorymetadata": "'repository' here is an open-access scholarly repository, not a package registry; a 2008 posted-content item with no venue",
    "dilts1998perceivedchanneldependency": "retail channel conflict resolution: homonym on both 'dependency' and 'conflict'",
    "anon2001rewritingdatadependency": "data dependency in logic-based specification rewriting; homonym",
    "anon2013tourismdependencydevelopment": "dependency as a development-studies concept; homonym",
    "kasradze2025subsidiesfostergrowth": "subsidy dependence of firms; homonym on 'dependency'",
    "chambers2026opensourcedas": "'DAS' is distributed acoustic sensing: a domain ecosystem, not a package registry",
    "bikel2008eventmatchingtransitive": "transitive closure of dependency relations for event matching in NLP; homonym",
    "hyderjr2026drivenfailureanalysis": "LSTM failure prediction; 'dependency' in the title is not package dependency",
    "pagourtzis2001pvmcomputationtransitive": "parallel transitive-closure computation algorithm; homonym",
    "li2023understandingresolutionmulti": "'resolution of multi-language bugs' means bug fixing in polyglot projects; homonym on 'resolution'",
    "mu2026modelbuildmanifest": "sector-coupled energy systems: 'dependency injection' names a modelling pattern, not package resolution",
    "anon2024enhancingmobileapp": "Swift Package Manager mobile-app performance; 'dependency management' there means build performance",
    "wang2017aspectorientedintegration": "aspect-oriented integration testing over a module dependency graph; not registry resolution",
    "kalakoti2025provideragnosticinfrastructure": "record carries a venue mismatch (Journal of International Crisis and Risk Communication Research) for an IaC framework paper; the record cannot be relied on",
    "pazmioortiz2026mappingwebprivacy": "web-privacy measurement in Ecuador; kept only by the words 'reproducible' and 'measurement study'",
    "schnell2026signalsmeasurandsmeasurement": "measurement-science roadmap for analytical biology; other field",

    # adjacent construct: real work, wrong object
    "breiter2019newserializationlibrary": "binary/serialization backward compatibility, a different construct from range-bounded admissibility",
    "lambers2018multigranularconflict": "conflict analysis in graph transformation systems; 'conflict' names a different mechanism",
    "savidis2022softwarearchitecturemining": "architecture recovery from source-code dependencies; not registry declarations",
    "wang2022staticanalysismethod": "value-dependency graph for incremental code analysis; not package versions",
    "onagh2024extensiondecisionsopen": "plugin-extension adoption decisions; adjacent construct, no version admissibility",
    "haimfaridianndhowyoungfirms": "firm-level adoption decisions; management literature with no resolution construct",
    "salmon2026howrecruitnew": "maintainer recruitment; no declaration or resolution construct",
    "anon1999debianlinuxsuper": "a buffer-overflow vulnerability report, not a study of dependency resolution",
    "hatta2026reproducibilitynewcopyleft": "advocacy framing ('reproducibility is the new copyleft') with no measurement to cite",
    "baker2009upgradesopenlibrary": "a 2009 posted-content item titled 'Upgrades to Open Library', with no venue and no abstract: nothing in it can be cited for a claim",

    # the relevance gate's own signature failures
    "abbas2007agilesoftwareassurance": "kept by the word 'empirical'; an agile-assurance study with no measurement instrument we share",
    "anon2007firstinternationalsymposium2": "front matter of a symposium, recorded by Crossref as a work",
    "anon2007firstinternationalsymposium3": "front matter of the same symposium, second record",
    "delater2013tracingrequirementssource": "requirements-to-code traceability",
    "franca2009empiricalstudysoftware": "developer motivation factors",
    "odzaly2009softwareriskmanagement": "barriers to software risk management",
    "rodriguez2017empiricalstudyopen": "open-source virtual-reality projects",
    "schneidewind2001knowledgerequirements": "knowledge requirements for quality measurement",
    "taber2014empiricalfacevalidity": "validity of defect models at one laboratory",

    # cover-problem variants we do not instantiate
    "abidha2022redblueset": "geometric variant on axis-parallel hyperplanes; no bearing on the cover instance we construct",
    "chang2003solving": "DNA-computing solution to set cover; not a bound we use",
    "fahle2007fasterbranchbound": "test-cover (program testing) instance: a different cover problem",
    "ren2011notealgorithmsconnected": "connected set cover: a connectivity constraint we do not impose",
    "tan2016setcoverbased": "attribute reduction via set cover; other field",
    "wang2024approximationalgorithmspartition": "partition set cover with penalties: a variant we do not instantiate",
    "yang2024discriminatingcodeset": "discriminating codes with k-bend paths; combinatorial variant with no bearing",
    "zhang2009algorithmsconnected": "connected set cover; connectivity is not imposed here",

    # interval variants we neither use nor argue against
    "anon2012confidenceintervalssimple": "textbook chapter on binomial intervals, superseded by the primary sources kept",
    "balayla2024gaussiandistributionconfidence": "textbook exposition of the Wald interval",
    "nawa2022weightedscoreconfidence": "weighted score interval for a variant problem",
    "ogura2018improvementbayesiancredible": "Bayesian credible interval: a different inferential frame",

    # ---- pruned from the widening batches (container images and model registries) ----------
    # The widening proved that these two families are full of records that use the words and not
    # the construct. Listed one by one because a batch prune with one reason would hide which
    # homonym each one was.
    "anon2018appendixdefinitioncontainer": "an appendix definition of the word 'container'; a reference entry, not a work",
    "anon2020reportjointoffice": "a whaling-commission report: the query's words appear, the subject does not",
    "anon2020fasterscalablemodel": "model deployment tooling (ONNX); not version admissibility",
    "syed2021reproducibilitydiversitycrisis": "psychology's reproducibility crisis: a different failure mode, not a declaration failing",
    "zimelewiczndenabledsystemsmodel": "deployment monitoring of ML systems, not what a declaration admits",
    "diskin2009modelversioninglarge": "'model versioning' in model-driven engineering: metamodel evolution, not artifact versions",
    "haeusler2017combiningversioningmetamodel": "model repository for metamodel evolution (ChronoSphere); the same MDE homonym",
    "iswari2014improvementadaptablemodel": "adaptable model versioning (AMOR) in MDE; the same homonym",
    "hibbard2026asmincorpororatesimagetwin": "biomedical image-duplication screening: 'image' here is a micrograph",
    "jingqiu2008addtemporalinformation": "dependency grammar in a language model; homonym",
    "oladunni2016spatialdependencyhedonic": "spatial dependence in an econometric housing model; homonym",
    "panchanathan1989contentaddressablememory": "content-addressable memory hardware: 'content addressable' is a circuit technique",
    "advanceinteractioninc1994contentaddressablevideo": "a 1994 content-addressable video system: storage media, not artifact identity",
    "song2022csscontainerresource": "container scheduling and resource management, not version identity",
    "knoth2017reproducibilitypracticaladoption": "a fifth domain instance of the container claim already placed four times; the record is real but citing it would pad the list rather than add a sentence",
    "ohta2015containerbasedsequence": "another domain instance of the placed container claim; no distinct sentence to support",
    "mizera2026machinelearningbased": "physics-experiment tracking: ML tracking of detector data, not artifact versions",
}
