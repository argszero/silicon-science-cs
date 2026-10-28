# Reference verification report — issue #149

**DERIVED FILE — do not edit.** Regenerate with `python3 place_references.py --report reference-check.md`. It is a pure function of two inputs: the stored verification state in `refs/references.json` and the authored placement in `placements.py`. It reads no network and writes no timestamp, so regenerating it reproduces it byte for byte.

## What was searched, and how

| item | value |
|---|---|
| index | Crossref REST API, `works` endpoint (`query.bibliographic` for discovery, `works/{doi}` for verification) |
| window | **none imposed** — Crossref's bibliographic query takes no date filter in this call, so records of any year may return. The search window is therefore not a claim this report can make; the scan date is. |
| scan date | 2026-10-23 |
| rows per query | 16 |
| queries issued | 81 |
| queries that returned nothing usable | 13 (listed below, not dropped) |
| verification method | DOI → `works/{doi}`, then corroboration by a field that is **not the title**: the first-author family, or the year when no author is asserted. Author mismatch is fatal. |

**Queries whose whole yield was refused on relevance** (13): `apibreakage`, `condaenv`, `declarative`, `determinism`, `featuremodel`, `monorepo`, `pkgversion`, `presolve`, `rangeapi`, `smtconfig`, `tagmut`, `typosquat`, `versiondrift`.

## Counts

| quantity | value |
|---|---|
| records harvested mechanically | 270 |
| refused in pass 1 (salience: another field entirely) | 56 |
| refused in pass 2 (criterion: adjacent construct) | 46 |
| **pruned at placement** (real records supporting no claim here) | **64** |
| **placed and cited** | **102** |
| verification floor | ≥ 100 |
| state | PASS |

The two pruning stages answer different questions and are counted separately. Passes 1 and 2 ask whether a record is about this subject at all; placement asks whether it supports a claim this paper makes. A record can pass both review passes and still be unplaceable, and that is the failure mode a word-level gate cannot see: *Agile Software Assurance: An Empirical Study* is about software engineering and about measurement, and still has nothing to say here.

## Works this paper is measured against

Each states a competing object or a competing answer. The difference, not the citation, is the content.

### Package managers à la carte: A Formal Model of Dependency Resolution

*Gibb, 2026. DOI `10.59350/rk9s4-43g76`.*

Difference: A formal model of dependency RESOLUTION: given declarations, it defines which solution a solver returns. We do not model the solver; we count what the solver may choose among, so the two results are about different objects and neither subsumes the other.

What was read, at the time this report was generated: registry abstract read this round: it states that managers differ in their resolution SEMANTICS, which is the object our measure does not touch.

### Solving Package Management via Hypergraph Dependency Resolution

*Gibb, 2025. DOI `10.59350/nrbbt-e7k85`.*

Difference: Hypergraph dependency resolution: a new encoding that makes solving faster. It is a contribution to the cost of choosing, and is silent on how many admissible choices a declaration leaves; our construction is the input it would have to run on.

What was read, at the time this report was generated: registry abstract read this round: it is about interoperability and implicit system dependencies between managers, i.e. the encoding of a resolution problem.

### Flexible and Optimal Dependency Management via Max-SMT

*Pinckney, 2023. DOI `10.1109/icse48619.2023.00124`.*

Difference: Max-SMT optimal dependency management: selects an optimal assignment under stated costs. Optimality is defined over the admissible set, which is exactly the set whose size we measure; the paper needs our quantity as a precondition and does not measure it.

What was read, at the time this report was generated: publisher record and metadata only: no abstract in the registry and no abstract obtainable. Cited in the adjacent-but-different group, where no claim of this paper depends on it.

### Byam: Fixing Breaking Dependency Updates with Large Language Models

*Reyes, 2026. DOI `10.1007/s10664-026-10835-1`.*

Difference: LLM repair of breaking dependency updates: repairs a build after an update breaks it. This is post-hoc and per-update; we ask beforehand how much of the update space the declaration left open, so the remedy and the measurement are complementary rather than competing.

What was read, at the time this report was generated: publisher record and metadata only: no abstract obtainable. Cited in the adjacent-but-different group, where no claim of this paper depends on it.

### Maven-Lockfile: High Integrity Rebuild of Past Java Releases

*Schmid, 2026. DOI `10.1145/3774748.3787615`.*

Difference: Maven-Lockfile: high-integrity rebuild of past releases by recording resolved state. It is the strongest form of the alternative we compare against -- pin the resolution rather than bound the range -- and it prices the cost side of that alternative, not its necessity.

What was read, at the time this report was generated: title and venue only -- no abstract in the registry and arXiv timed out this round; confirm against the full text.

### What Do Package Dependencies Tell Us About Semantic Versioning?

*Decan, 2021. DOI `10.1109/tse.2019.2918315`.*

Difference: Semantic versioning read as a compatibility promise. That reading is the belief our dialect measure tests: if a bounded range really did promise compatibility, ambiguity inside the range would carry no risk, and the decay curve would be flat in every stratum. It is not.

What was read, at the time this report was generated: publisher record and metadata only: no abstract obtainable. The paper's dialect reading is tested indirectly by the decay curve, and this work is cited as the adjacent statement of that reading rather than as a premise.

## Verification, one line per placed entry

Method is `doi` (record fetched by DOI) unless stated. `result` is what the stored state says, not what a re-run would say now.

| # | key | result | title match | record found | DOI | checked |
|---|---|---|---|---|---|---|
| 1 | `alharbi2026enhancingtransparencyhugging` | verified | 1.000 | Enhancing AI Transparency on Hugging Face: An Automated Pipeline for M | `10.1109/access.2026.3723027` | 2026-10-23 |
| 2 | `almendraarao2020adjustedwaldconfidence` | verified | 1.000 | USING ADJUSTED WALD CONFIDENCE INTERVAL FOR A BINOMIAL PROPORTION | `10.17654/bs017020415` | 2026-10-23 |
| 3 | `almishev2025dependencymanagementstrategies` | verified | 1.000 | Dependency Management Strategies in Scalable Monorepositories: Analysi | `10.30574/wjarr.2025.28.1.3468` | 2026-10-23 |
| 4 | `alnoamany2018computationalreproducibilityresearcher` | verified | 1.000 | Towards computational reproducibility: researcher perspectives on the  | `10.7287/peerj.preprints.26727v1` | 2026-10-23 |
| 5 | `amir2018thererandomsampling` | verified | 1.000 | There is no random sampling in software engineering research | `10.1145/3183440.3195001` | 2026-10-23 |
| 6 | `anon1976numberingschemecomputer` | verified | 1.000 | A numbering scheme for a computer programming library | `10.1002/spe.4380060317` | 2026-10-23 |
| 7 | `aranguren2015enhancedreproducibilitysadi` | verified | 1.000 | Enhanced reproducibility of SADI web service workflows with Galaxy and | `10.1186/s13742-015-0092-3` | 2026-10-23 |
| 8 | `ayres2021continuousautomotivesoftware` | verified | 1.000 | Continuous Automotive Software Updates through Container Image Layers | `10.3390/electronics10060739` | 2026-10-23 |
| 9 | `b2024exploringlargescale` | verified | 1.000 | Exploring Large Scale Docker Image Vulnerability and Storage Performan | `10.1109/icscan62807.2024.10894527` | 2026-10-23 |
| 10 | `baltes2022samplingsoftwareengineering` | verified | 1.000 | Sampling in software engineering research: a critical review and guide | `10.1007/s10664-021-10072-8` | 2026-10-23 |
| 11 | `begoug2024howinfrastructurecode` | verified | 1.000 | How Do Infrastructure-as-Code Practitioners Update their Provider Depe | `10.1007/978-981-96-0808-9_28` | 2026-10-23 |
| 12 | `begoug2025understandingawsprovider` | verified | 1.000 | Understanding AWS Provider Dependency Updates in Infrastructure-As-Cod | `10.1109/tsc.2025.3601051` | 2026-10-23 |
| 13 | `bhatt2020reproduciblesoftwareenvironment` | verified | 1.000 | Reproducible Software Environment: a tool enabling computational repro | `10.1051/swsc/2020011` | 2026-10-23 |
| 14 | `bommarito2019empiricalanalysispython` | verified | 1.000 | An Empirical Analysis of the Python Package Index (PyPI) | `10.2139/ssrn.3426281` | 2026-10-23 |
| 15 | `bottotobar2026dependencydateexploring` | verified | 1.000 | Is my dependency up-to-date? Exploring challenges with automated depen | `10.21203/rs.3.rs-9390837/v1` | 2026-10-23 |
| 16 | `bruccoleri2025dockerimagebuilder` | verified | 1.000 | Docker Image Builder: A Robust Method for Constructing Docker Images f | `10.31219/osf.io/8pgd7_v1` | 2026-10-23 |
| 17 | `bzeznik2017nixhpcpackage` | verified | 1.000 | Nix as HPC package management system | `10.1145/3152493.3152556` | 2026-10-23 |
| 18 | `carbonnel2015tractabilityconstraintsatisfaction` | verified | 1.000 | Tractability in constraint satisfaction problems: a survey | `10.1007/s10601-015-9198-6` | 2026-10-23 |
| 19 | `carbonnelndharnessingtractabilityconstraint` | verified | 1.000 | Harnessing tractability in constraint satisfaction problems | `10.70675/25f2c2c6zc9f2z4828z8530z8d66a557d24e` | 2026-10-23 |
| 20 | `cavezza2014reproducibilityenvironmentdependent` | verified | 1.000 | Reproducibility of Environment-Dependent Software Failures: An Experie | `10.1109/issre.2014.19` | 2026-10-23 |
| 21 | `cervera2026reproducibilitylegacyros` | verified | 1.000 | Reproducibility of Legacy ROS-Based Research Code Through Transparent  | `10.1109/rap.2026.3686662` | 2026-10-23 |
| 22 | `chodorowski2021comparativeanalysisjavascript` | verified | 1.000 | Comparative analysis of JavaScript package managers - yarn and npm | `10.35784/jcsi.2460` | 2026-10-23 |
| 23 | `claes2015historicalanalysisdebian` | verified | 1.000 | A Historical Analysis of Debian Package Incompatibilities | `10.1109/msr.2015.27` | 2026-10-23 |
| 24 | `cogo2021empiricalstudydependency` | verified | 1.000 | An Empirical Study of Dependency Downgrades in the npm Ecosystem | `10.1109/tse.2019.2952130` | 2026-10-23 |
| 25 | `cooper2010generalizingconstraintsatisfaction` | verified | 1.000 | Generalizing constraint satisfaction on trees: Hybrid tractability and | `10.1016/j.artint.2010.03.002` | 2026-10-23 |
| 26 | `decan2016topologypackagedependency` | verified | 1.000 | On the topology of package dependency networks | `10.1145/2993412.3003382` | 2026-10-23 |
| 27 | `decan2018evolutiontechnicallag` | verified | 1.000 | On the Evolution of Technical Lag in the npm Package Dependency Networ | `10.1109/icsme.2018.00050` | 2026-10-23 |
| 28 | `decan2021whatpackagedependencies` | verified | 1.000 | What Do Package Dependencies Tell Us About Semantic Versioning? | `10.1109/tse.2019.2918315` | 2026-10-23 |
| 29 | `ding2024scalablerobustmodel` | verified | 1.000 | Towards Scalable and Robust Model Versioning | `10.1109/satml59370.2024.00036` | 2026-10-23 |
| 30 | `doan2022davsdockerfileanalysis` | verified | 1.000 | DAVS: Dockerfile Analysis for Container Image Vulnerability Scanning | `10.32604/cmc.2022.025096` | 2026-10-23 |
| 31 | `duttandsurveyapproximationalgorithms` | verified | 1.000 | Survey of Approximation Algorithms for Set Cover Problem | `10.12794/metadc12118` | 2026-10-23 |
| 32 | `exman2019softwaremodularitycoupling` | verified | 1.000 | Software Modularity Coupling Resolution by the Laplacian of a Bipartit | `10.5220/0007955802980305` | 2026-10-23 |
| 33 | `ferreira2026persistenciavulnerabilidadesdependencia` | verified | 1.000 | PERSISTÊNCIA DE VULNERABILIDADES DE DEPENDÊNCIA POR TIPO EM PROJETOS N | `10.56238/rcsv16n8-001` | 2026-10-23 |
| 34 | `foote2013rolesresponsibilitiespackage` | verified | 1.000 | Roles and Responsibilities of a Package Maintainer | `10.36288/roscon2013-900674` | 2026-10-23 |
| 35 | `ganian2015discoveringarchipelagostractability` | verified | 1.000 | Discovering Archipelagos of Tractability for Constraint Satisfaction a | `10.1137/1.9781611974331.ch114` | 2026-10-23 |
| 36 | `garthwaite2023locallycorrectconfidence` | verified | 1.000 | Locally correct confidence intervals for a binomial proportion: A new  | `10.1111/sjos.12672` | 2026-10-23 |
| 37 | `gibb2025solvingpackagemanagement` | verified | 1.000 | Solving Package Management via Hypergraph Dependency Resolution | `10.59350/nrbbt-e7k85` | 2026-10-23 |
| 38 | `gibb2026packagemanagerscarte` | verified | 1.000 | Package managers à la carte: A Formal Model of Dependency Resolution | `10.59350/rk9s4-43g76` | 2026-10-23 |
| 39 | `gonzalez2026sklearnmigratorcross` | verified | 1.000 | sklearn-migrator: Cross-version migration of scikit-learn models for r | `10.21105/joss.10374` | 2026-10-23 |
| 40 | `goswami2024reproduciblehighperformance` | verified | 1.000 | Reproducible High Performance Computing without Redundancy with Nix | `10.31219/osf.io/3fp2v` | 2026-10-23 |
| 41 | `gu2022pkgndeptoolheaviness` | verified | 1.000 | <i>pkgndep</i>
                  : a tool for heaviness analysis on R  | `10.1101/2022.02.11.480073` | 2026-10-23 |
| 42 | `guan2012generalizedscoreconfidence` | verified | 1.000 | A generalized score confidence interval for a binomial proportion | `10.1016/j.jspi.2011.09.010` | 2026-10-23 |
| 43 | `habtzghi2014modifiedclopperpearson` | verified | 1.000 | Modified Clopper-Pearson Confidence Interval for Binomial Proportion | `10.2991/jsta.2014.13.4.3` | 2026-10-23 |
| 44 | `hatton2019computationalreproducibilityelephant` | verified | 1.000 | Computational Reproducibility: The Elephant in the Room | `10.1109/ms.2018.2883805` | 2026-10-23 |
| 45 | `heroux2011improvingcsesoftware` | verified | 1.000 | Improving CSE software through reproducibility requirements | `10.1145/1985782.1985787` | 2026-10-23 |
| 46 | `hinsen2012nixpackagemanager` | verified | 1.000 | The Nix package manager in computational science | `10.59350/c4wzx-s6q80` | 2026-10-23 |
| 47 | `hochbaum2008multiintegerset` | verified | 1.000 | The multi‐integer set cover and the facility terminal cover problem | `10.1002/net.20265` | 2026-10-23 |
| 48 | `hrtel2023operationalizingvalidityempirical` | verified | 1.000 | Operationalizing validity of empirical software engineering studies | `10.1007/s10664-023-10370-3` | 2026-10-23 |
| 49 | `kechagia2010opensourcelicensing` | verified | 1.000 | Open Source Licensing Across Package Dependencies | `10.1109/pci.2010.28` | 2026-10-23 |
| 50 | `kellerndversionnumberingscheme` | verified | 1.000 | A version numbering scheme with a useful lexicographical order | `10.1109/icde.1995.380387` | 2026-10-23 |
| 51 | `kim2021generalizedagresticoull` | verified | 1.000 | A generalized Agresti–Coull type confidence interval for a binomial pr | `10.1007/s42952-021-00143-3` | 2026-10-23 |
| 52 | `kim2025robustframeworkcomprehensive` | verified | 1.000 | A Robust Framework for Comprehensive Container Image Vulnerability Ass | `10.1109/access.2025.3545124` | 2026-10-23 |
| 53 | `kowalewski2021sustainablepackagingquantum` | verified | 1.000 | Sustainable Packaging of Quantum Chemistry Software with the Nix Packa | `10.22541/au.163462780.05778677/v1` | 2026-10-23 |
| 54 | `kula2023promisesperilsmining` | verified | 1.000 | Promises and Perils of Mining Software Package Ecosystem Data | `10.1007/978-3-031-36060-2_3` | 2026-10-23 |
| 55 | `kunstmann2024scientificworkflowdeployment` | verified | 1.000 | Scientific Workflow Deployment: Container Provenance in High-Performan | `10.5753/sbbd.2024.240194` | 2026-10-23 |
| 56 | `lake2025analyzingdependencyclusters` | verified | 1.000 | Analyzing Dependency Clusters and Security Risks in the Maven Central  | `10.1109/msr66628.2025.00046` | 2026-10-23 |
| 57 | `lavalndpackagedependenciesanalysis` | verified | 1.000 | Package Dependencies Analysis and Remediation in Object-Oriented Syste | `10.70675/950f31fczd7a0z427dza2a9zf55aa8caf63f` | 2026-10-23 |
| 58 | `li2023empiricalstudyyanked` | verified | 1.000 | An Empirical Study of Yanked Releases in the Rust Package Registry | `10.1109/tse.2022.3152148` | 2026-10-23 |
| 59 | `li2023largescaleempirical` | verified | 1.000 | A Large-Scale Empirical Study on Semantic Versioning in Golang Ecosyst | `10.1109/ase56229.2023.00140` | 2026-10-23 |
| 60 | `lyu2025detectingbuilddependency` | verified | 1.000 | Detecting Build Dependency Errors by Dynamic Analysis of Build Executi | `10.1109/tse.2025.3566225` | 2026-10-23 |
| 61 | `malka2024increasingtrustopen` | verified | 1.000 | Increasing trust in the open source supply chain with reproducible bui | `10.1145/3639478.3639806` | 2026-10-23 |
| 62 | `malka2025doesfunctionalpackage` | verified | 1.000 | Does Functional Package Management Enable Reproducible Builds at Scale | `10.1109/msr66628.2025.00115` | 2026-10-23 |
| 63 | `mecheo2026dependafixgithubapp` | verified | 1.000 | DependaFix: A GitHub App for Fixing Breaking Dependency Updates in CI  | `10.1145/3803437.3806404` | 2026-10-23 |
| 64 | `miguel2004constraintsatisfactionproblem` | verified | 1.000 | The Constraint Satisfaction Problem | `10.1007/978-0-85729-378-7_2` | 2026-10-23 |
| 65 | `milewicz2023evidencebasedsoftware` | verified | 1.000 | Towards Evidence-Based Software Quality Practices for Reproducibility: | `10.1145/3589806.3600040` | 2026-10-23 |
| 66 | `miller2025understandingresponseopen` | verified | 1.000 | Understanding the Response to Open-Source Dependency Abandonment in th | `10.1109/icse55347.2025.00004` | 2026-10-23 |
| 67 | `mitrabehura2022singularitycontainersimprove` | verified | 1.000 | Singularity Containers Improve Reproducibility and Ease of Use in Comp | `10.3389/fbinf.2021.757291` | 2026-10-23 |
| 68 | `mittal2025evaluatingcontainersecurity` | verified | 1.000 | Evaluating Container Security and Reproducibility in Research Software | `10.36227/techrxiv.175459769.96908041/v1` | 2026-10-23 |
| 69 | `montaruli2026sourcebrokenlargescale` | verified | 1.000 | SourceBroken: A large-scale analysis on the (un)reliability of SourceR | `10.1145/3748522.3779992` | 2026-10-23 |
| 70 | `moracantallops2020evolutionprospectscomprehensive` | verified | 1.000 | Evolution and prospects of the Comprehensive R Archive Network (CRAN)  | `10.1002/smr.2270` | 2026-10-23 |
| 71 | `nakanishindmetricevaluatingclass` | verified | 1.000 | A metric for evaluating class library interfaces and its application t | `10.1109/icsm.1995.526523` | 2026-10-23 |
| 72 | `nakata2021evaluationvulnerabilityreproducibility` | verified | 1.000 | Evaluation of Vulnerability Reproducibility in Container-based Cyber R | `10.5220/0010324606350642` | 2026-10-23 |
| 73 | `nascimento2022exploringapideprecation` | verified | 1.000 | Exploring API Deprecation Evolution in JavaScript | `10.1109/saner53432.2022.00031` | 2026-10-23 |
| 74 | `opdebeeck2021practicesemanticversioning` | verified | 1.000 | On the practice of semantic versioning for Ansible galaxy roles: An em | `10.1016/j.jss.2021.111059` | 2026-10-23 |
| 75 | `pan2020researchdynamicdetection` | verified | 1.000 | Research on Dynamic Detection of Java Dependency Conflict | `10.1109/aeeca49918.2020.9213605` | 2026-10-23 |
| 76 | `peer2020activemaintenanceproposal` | verified | 1.000 | Active Maintenance: A Proposal for the Long-term Computational Reprodu | `10.31235/osf.io/8jwhk` | 2026-10-23 |
| 77 | `petersen2013worldviewsresearchmethods` | verified | 1.000 | Worldviews, Research Methods, and their Relationship to Validity in Em | `10.1109/iwsm-mensura.2013.22` | 2026-10-23 |
| 78 | `pinckney2023flexibleoptimaldependency` | verified | 1.000 | Flexible and Optimal Dependency Management via Max-SMT | `10.1109/icse48619.2023.00124` | 2026-10-23 |
| 79 | `pulicharla2024dataversioningimpact` | verified | 1.000 | Data Versioning and Its Impact on Machine Learning Models | `10.55662/jst.2024.5101` | 2026-10-23 |
| 80 | `qi2024empiricalstudydownstream` | verified | 1.000 | An Empirical Study on Downstream Dependency Package Groups in Software | `10.1049/2024/4488412` | 2026-10-23 |
| 81 | `raatikainen2025machinelearninglineage` | verified | 1.000 | Machine Learning Lineage for Trustworthy Machine Learning Systems: Inf | `10.1109/ms.2024.3414317` | 2026-10-23 |
| 82 | `rajendran2025primitivaalgebraicdecomposition` | verified | 1.000 | PRIMITIVA: Algebraic Decomposition for Zero-Conflict Package Managemen | `10.2139/ssrn.5753502` | 2026-10-23 |
| 83 | `randrianainandincrementalreproduciblebuilds` | verified | 1.000 | Incremental, reproducible builds of software variants | `10.70675/e95564c6zca79z417aza37ez10821a9a0a48` | 2026-10-23 |
| 84 | `reyes2024breakinggoodexplaining` | verified | 1.000 | Breaking-Good: Explaining Breaking Dependency Updates with Build Analy | `10.1109/scam63643.2024.00014` | 2026-10-23 |
| 85 | `reyes2026byamfixingbreaking` | verified | 1.000 | Byam: Fixing Breaking Dependency Updates with Large Language Models | `10.1007/s10664-026-10835-1` | 2026-10-23 |
| 86 | `sandelius1952confidenceintervalsmallest` | verified | 1.000 | A Confidence Interval for the Smallest Proportion of a Binomial Popula | `10.1111/j.2517-6161.1952.tb00105.x` | 2026-10-23 |
| 87 | `schmid2026mavenlockfilehigh` | verified | 1.000 | Maven-Lockfile: High Integrity Rebuild of Past Java Releases | `10.1145/3774748.3787615` | 2026-10-23 |
| 88 | `serbout2023interactivelyexploringapi` | verified | 1.000 | Interactively Exploring API Changes and Versioning Consistency | `10.1109/vissoft60811.2023.00013` | 2026-10-23 |
| 89 | `shaffer2021empiricalstudypackage` | verified | 1.000 | An Empirical Study of Package Dependencies and Lifetimes in Binder Pyt | `10.1109/escience51609.2021.00032` | 2026-10-23 |
| 90 | `solarin2026justtimestampsstudy` | verified | 1.000 | It’s Not Just Timestamps: A Study on Docker Reproducibility | `10.1145/3803437.3804434` | 2026-10-23 |
| 91 | `sousa2009analysispackagedependency` | verified | 1.000 | Analysis of the package dependency on Debian GNU/Linux | `10.6062/jcis.2009.01.02.0015` | 2026-10-23 |
| 92 | `tekin2026deathendlongitudinal` | verified | 1.000 | Death Is Not the End: a Longitudinal Study on the Impact of Automatic  | `10.1109/sp63933.2026.00227` | 2026-10-23 |
| 93 | `termphaiboon2025exploringsecuritydependency` | verified | 1.000 | Exploring the SECURITY.md in the Dependency Chain: Preliminary Analysi | `10.1109/asew67777.2025.00055` | 2026-10-23 |
| 94 | `thirumalaisamy2025assistedverificationsbom` | verified | 1.000 | AI-Assisted Verification of SBOM Accuracy and Drift in Software Supply | `10.14445/22312803/ijctt-v73i12p103` | 2026-10-23 |
| 95 | `turner2025makeyourdevelopment` | verified | 1.000 | Make your development environment portable and reproducible | `10.59350/gavxb-3e465` | 2026-10-23 |
| 96 | `varanasi2019mavendependencymanagement` | verified | 1.000 | Maven Dependency Management | `10.1007/978-1-4842-5410-3_3` | 2026-10-23 |
| 97 | `wang2025understandingdetectingpeer` | verified | 1.000 | Understanding and Detecting Peer Dependency Resolving Loop in npm Ecos | `10.1109/icse55347.2025.00054` | 2026-10-23 |
| 98 | `wittern2016lookdynamicsjavascript` | verified | 1.000 | A look at the dynamics of the JavaScript package ecosystem | `10.1145/2901739.2901743` | 2026-10-23 |
| 99 | `wonsil2023integratedreproducibilityself` | verified | 1.000 | Integrated Reproducibility with Self-describing Machine Learning Model | `10.1145/3589806.3600039` | 2026-10-23 |
| 100 | `wynnjr2007assessinghealthopen` | verified | 1.000 | Assessing the Health of an Open Source Ecosystem | `10.4018/978-1-59904-210-7.ch011` | 2026-10-23 |
| 101 | `yang2026reproduciblellmbased` | verified | 1.000 | Reproducible LLM-Based Measurement Depends on the Serving Stack | `10.2139/ssrn.7083993` | 2026-10-23 |
| 102 | `zhu2026versionedtransitivedependency` | verified | 1.000 | Versioned Transitive Dependency-Closure Binding and Operation-Time Eff | `10.2139/ssrn.7456458` | 2026-10-23 |

Total placed and verified: **102**.

## Placement: entry, section, and the claim it supports

### S1 — Introduction and motivation: why an unpinned declaration costs reproducibility (7)

| key | title | claim supported |
|---|---|---|
| `alnoamany2018computationalreproducibilityresearcher` | Towards computational reproducibility: researcher perspectives on the  | researchers' own sharing practice is treated as the reproducibility lever, which leaves the declaration unexamined |
| `bhatt2020reproduciblesoftwareenvironment` | Reproducible Software Environment: a tool enabling computational repro | a tool that makes the environment, not the manifest, the unit of reproduction |
| `cavezza2014reproducibilityenvironmentdependent` | Reproducibility of Environment-Dependent Software Failures: An Experie | environment-dependent failures reproduce differently in different environments: the failure mode an over-wide range admits |
| `ferreira2026persistenciavulnerabilidadesdependencia` | PERSISTÊNCIA DE VULNERABILIDADES DE DEPENDÊNCIA POR TIPO EM PROJETOS N | vulnerability persistence by dependency class in npm projects: an over-wide range keeps a vulnerable version admissible over time |
| `hatton2019computationalreproducibilityelephant` | Computational Reproducibility: The Elephant in the Room | the reproducibility gap stated as a field-level problem rather than a tooling defect |
| `heroux2011improvingcsesoftware` | Improving CSE software through reproducibility requirements | reproducibility treated as an engineering requirement with acceptance criteria |
| `milewicz2023evidencebasedsoftware` | Towards Evidence-Based Software Quality Practices for Reproducibility: | evidence-based quality practices for reproducibility: what evidence a reproducibility claim needs |

### S10 — Threats to validity (4)

| key | title | claim supported |
|---|---|---|
| `amir2018thererandomsampling` | There is no random sampling in software engineering research | there is no random sampling in SE research: our population is a frame, and is described as one |
| `baltes2022samplingsoftwareengineering` | Sampling in software engineering research: a critical review and guide | sampling guidelines: how a frame must be described for a rate to be interpretable |
| `hrtel2023operationalizingvalidityempirical` | Operationalizing validity of empirical software engineering studies | operationalizing validity claims: the frame in which our threats are stated |
| `petersen2013worldviewsresearchmethods` | Worldviews, Research Methods, and their Relationship to Validity in Em | worldview, method and validity are coupled: a rate here is a design-dependent statement |

### S2 — Setting: what one declaration admits (the depth-1 construct) (8)

| key | title | claim supported |
|---|---|---|
| `claes2015historicalanalysisdebian` | A Historical Analysis of Debian Package Incompatibilities | incompatibilities are studied as historical events; the declaration that admitted them is not the unit of analysis |
| `decan2016topologypackagedependency` | On the topology of package dependency networks | dependency-network topology is measured on one declared version per package, which presumes the declaration names one |
| `gu2022pkgndeptoolheaviness` | <i>pkgndep</i> : a tool for heaviness analysis on R package dependenci | dependency cost is measured per declared dependency, taking the declaration as one object |
| `lavalndpackagedependenciesanalysis` | Package Dependencies Analysis and Remediation in Object-Oriented Syste | remediation presumes a single resolved state to repair |
| `lyu2025detectingbuilddependency` | Detecting Build Dependency Errors by Dynamic Analysis of Build Executi | build-dependency errors are found by executing the build, which presumes the declaration resolves to a single state |
| `nakanishindmetricevaluatingclass` | A metric for evaluating class library interfaces and its application t | upgrade risk is measured at the interface level in prior work; the declaration's admissible set is a different object |
| `reyes2024breakinggoodexplaining` | Breaking-Good: Explaining Breaking Dependency Updates with Build Analy | breaking updates are diagnosed from build output afterwards; the admissible set is never consulted beforehand |
| `shaffer2021empiricalstudypackage` | An Empirical Study of Package Dependencies and Lifetimes in Binder Pyt | which declared dependencies survive is measured per declaration, not per admissible version |

### S3 — Coupling: solution-set dispersion at depth 2 (10)

| key | title | claim supported |
|---|---|---|
| `gibb2025solvingpackagemanagement` | Solving Package Management via Hypergraph Dependency Resolution | the hypergraph formulation of resolution addresses the same object whose admissible-set size we count |
| `gibb2026packagemanagerscarte` | Package managers à la carte: A Formal Model of Dependency Resolution | a formal model of dependency resolution answers which solution exists, not how many the declaration admits |
| `lake2025analyzingdependencyclusters` | Analyzing Dependency Clusters and Security Risks in the Maven Central  | dependency clusters in Maven Central: structure of the resolved graph, not of the declaration |
| `li2023empiricalstudyyanked` | An Empirical Study of Yanked Releases in the Rust Package Registry | yanked releases are the impossibility argument's own exception; they are counted here rather than assumed away |
| `pan2020researchdynamicdetection` | Research on Dynamic Detection of Java Dependency Conflict | conflicts are detected dynamically at build time, i.e. after a choice has already been made |
| `pinckney2023flexibleoptimaldependency` | Flexible and Optimal Dependency Management via Max-SMT | optimal selection given constraints: optimality is defined over the set of admissible solutions |
| `qi2024empiricalstudydownstream` | An Empirical Study on Downstream Dependency Package Groups in Software | downstream dependency groups are the closest prior question to our coupling measure, but the analysis fixes one version per package |
| `rajendran2025primitivaalgebraicdecomposition` | PRIMITIVA: Algebraic Decomposition for Zero-Conflict Package Managemen | algebraic decomposition for zero-conflict resolution is a solver-side contribution |
| `wang2025understandingdetectingpeer` | Understanding and Detecting Peer Dependency Resolving Loop in npm Ecos | peer-dependency resolving loops: a second, harder resolution mode in the same ecosystem |
| `zhu2026versionedtransitivedependency` | Versioned Transitive Dependency-Closure Binding and Operation-Time Eff | the transitive closure treated as a versioned object, without counting how many closures a declaration admits |

### S4 — The dialect: bounded versus unbounded ranges (the headline mechanism) (5)

| key | title | claim supported |
|---|---|---|
| `anon1976numberingschemecomputer` | A numbering scheme for a computer programming library | a 1976 numbering scheme for a program library: version numbering is a design decision with consequences |
| `decan2021whatpackagedependencies` | What Do Package Dependencies Tell Us About Semantic Versioning? | declared constraints are read as compatibility promises: exactly the reading the dialect measure tests |
| `kellerndversionnumberingscheme` | A version numbering scheme with a useful lexicographical order | lexicographic ordering of version numbers: ordering is a convention, not a property of the artifact |
| `li2023largescaleempirical` | A Large-Scale Empirical Study on Semantic Versioning in Golang Ecosyst | semantic-versioning compliance in Go: a convention stated but not enforced |
| `opdebeeck2021practicesemanticversioning` | On the practice of semantic versioning for Ansible galaxy roles: An em | semver practice for Ansible roles: a third dialect with its own boundedness |

### S5 — Ecosystem practice: npm, PyPI and their conventions (15)

| key | title | claim supported |
|---|---|---|
| `bommarito2019empiricalanalysispython` | An Empirical Analysis of the Python Package Index (PyPI) | PyPI as an ecosystem object: size, growth, and what registry data can show |
| `chodorowski2021comparativeanalysisjavascript` | Comparative analysis of JavaScript package managers - yarn and npm | npm versus yarn: two managers resolve the same declarations differently |
| `cogo2021empiricalstudydependency` | An Empirical Study of Dependency Downgrades in the npm Ecosystem | dependency downgrades in npm: the resolved version moves independently of the declaration |
| `decan2018evolutiontechnicallag` | On the Evolution of Technical Lag in the npm Package Dependency Networ | technical lag: how far behind a declaration leaves an install |
| `exman2019softwaremodularitycoupling` | Software Modularity Coupling Resolution by the Laplacian of a Bipartit | dependency structure represented as a bipartite graph: the representation our admissible-set object shares |
| `foote2013rolesresponsibilitiespackage` | Roles and Responsibilities of a Package Maintainer | the maintainer's role: who authors the declaration, and on what evidence |
| `kechagia2010opensourcelicensing` | Open Source Licensing Across Package Dependencies | other properties of the same dependency edges are studied across the graph (licensing); the number of resolutions is not |
| `miller2025understandingresponseopen` | Understanding the Response to Open-Source Dependency Abandonment in th | ecosystem response to abandonment: what happens when an admissible version disappears |
| `moracantallops2020evolutionprospectscomprehensive` | Evolution and prospects of the Comprehensive R Archive Network (CRAN)  | CRAN evolution: a third ecosystem with its own versioning conventions |
| `nascimento2022exploringapideprecation` | Exploring API Deprecation Evolution in JavaScript | API deprecation practice in JavaScript: deprecation is announced, removal still breaks unpinned ranges |
| `serbout2023interactivelyexploringapi` | Interactively Exploring API Changes and Versioning Consistency | API-change and versioning consistency in practice: a declared version is not a proxy for change |
| `sousa2009analysispackagedependency` | Analysis of the package dependency on Debian GNU/Linux | Debian dependency structure analysed as a distribution-level graph |
| `termphaiboon2025exploringsecuritydependency` | Exploring the SECURITY.md in the Dependency Chain: Preliminary Analysi | PyPI dependency chains and security-disclosure practice |
| `wittern2016lookdynamicsjavascript` | A look at the dynamics of the JavaScript package ecosystem | the JavaScript ecosystem's dynamics measured from registry metadata |
| `wynnjr2007assessinghealthopen` | Assessing the Health of an Open Source Ecosystem | ecosystem health is assessed at ecosystem level, which is orthogonal to whether one declaration admits one install |

### S6 — Evidence practice: registries as data, and what a registry metric measures (3)

| key | title | claim supported |
|---|---|---|
| `kula2023promisesperilsmining` | Promises and Perils of Mining Software Package Ecosystem Data | promises and perils of mining package-ecosystem data: the methodological warrant for a pinned snapshot |
| `montaruli2026sourcebrokenlargescale` | SourceBroken: A large-scale analysis on the (un)reliability of SourceR | SourceRank reliability: a registry-derived metric that does not measure what its name says, which is why our rates carry an explicit denominator |
| `thirumalaisamy2025assistedverificationsbom` | AI-Assisted Verification of SBOM Accuracy and Drift in Software Supply | SBOM accuracy and drift: a dependency record that goes stale in place |

### S7 — Alternatives: exact pins, lockfiles, functional package management, containers, model registries (37)

| key | title | claim supported |
|---|---|---|
| `alharbi2026enhancingtransparencyhugging` | Enhancing AI Transparency on Hugging Face: An Automated Pipeline for M | model-card generation on a public model hub: a registry where the declaration is prose and the artifact moves under it |
| `almishev2025dependencymanagementstrategies` | Dependency Management Strategies in Scalable Monorepositories: Analysi | monorepo dependency-management strategies: resolution policy varies by build system, which is the dialect argument in another setting |
| `aranguren2015enhancedreproducibilitysadi` | Enhanced reproducibility of SADI web service workflows with Galaxy and | containerised workflows as the reproducibility mechanism in a domain science |
| `ayres2021continuousautomotivesoftware` | Continuous Automotive Software Updates through Container Image Layers | continuous updates delivered as container layers: the image, not the manifest, is the unit of change |
| `b2024exploringlargescale` | Exploring Large Scale Docker Image Vulnerability and Storage Performan | large-scale Docker image analysis: images are studied as artifacts with vulnerabilities and drift of their own |
| `begoug2024howinfrastructurecode` | How Do Infrastructure-as-Code Practitioners Update their Provider Depe | IaC practitioners' provider-upgrade behaviour: the same declaration-versus-install tension in another ecosystem |
| `begoug2025understandingawsprovider` | Understanding AWS Provider Dependency Updates in Infrastructure-As-Cod | infrastructure-as-code providers are version-constrained artifacts with their own upgrade discipline |
| `bottotobar2026dependencydateexploring` | Is my dependency up-to-date? Exploring challenges with automated depen | practitioner difficulty with automated dependency updates motivates measuring what the declaration permits |
| `bruccoleri2025dockerimagebuilder` | Docker Image Builder: A Robust Method for Constructing Docker Images f | a construction method for reproducible images: pinning at build time rather than at declaration time |
| `bzeznik2017nixhpcpackage` | Nix as HPC package management system | Nix as an HPC package manager: derivation-level pinning |
| `cervera2026reproducibilitylegacyros` | Reproducibility of Legacy ROS-Based Research Code Through Transparent  | legacy research code made reproducible by pinning the image: the practitioner's alternative to pinning versions |
| `ding2024scalablerobustmodel` | Towards Scalable and Robust Model Versioning | model versioning as an artifact-identity problem distinct from code versioning |
| `doan2022davsdockerfileanalysis` | DAVS: Dockerfile Analysis for Container Image Vulnerability Scanning | the Dockerfile is read as a declaration and its image scanned: the nearest container analogue of what we do to a manifest |
| `gonzalez2026sklearnmigratorcross` | sklearn-migrator: Cross-version migration of scikit-learn models for r | cross-version migration of fitted models: a version bound that is not about code compatibility |
| `goswami2024reproduciblehighperformance` | Reproducible High Performance Computing without Redundancy with Nix | reproducible HPC without redundancy under Nix |
| `hinsen2012nixpackagemanager` | The Nix package manager in computational science | Nix in computational science: the store path as the identity |
| `kim2025robustframeworkcomprehensive` | A Robust Framework for Comprehensive Container Image Vulnerability Ass | container image vulnerability assessment as an ongoing obligation rather than a one-off check |
| `kowalewski2021sustainablepackagingquantum` | Sustainable Packaging of Quantum Chemistry Software with the Nix Packa | domain packaging with Nix: the pin is the derivation, not a range |
| `kunstmann2024scientificworkflowdeployment` | Scientific Workflow Deployment: Container Provenance in High-Performan | container provenance in HPC: the image's identity recorded as evidence, which is exactly what a tag does not do |
| `malka2024increasingtrustopen` | Increasing trust in the open source supply chain with reproducible bui | reproducible builds as supply-chain trust |
| `malka2025doesfunctionalpackage` | Does Functional Package Management Enable Reproducible Builds at Scale | functional package management does enable reproducible builds at scale: the strongest evidence for the alternative we compare against |
| `mecheo2026dependafixgithubapp` | DependaFix: A GitHub App for Fixing Breaking Dependency Updates in CI  | automation repairs breaking updates after the fact, treating the update rather than the declaration as the unit |
| `mitrabehura2022singularitycontainersimprove` | Singularity Containers Improve Reproducibility and Ease of Use in Comp | Singularity containers improve reproducibility: a second container dialect with a different pinning convention |
| `mittal2025evaluatingcontainersecurity` | Evaluating Container Security and Reproducibility in Research Software | container images as an alternative pinning mechanism, evaluated for security and reproducibility |
| `nakata2021evaluationvulnerabilityreproducibility` | Evaluation of Vulnerability Reproducibility in Container-based Cyber R | container-based environments: reproducibility of a vulnerability depends on the pinned base image |
| `peer2020activemaintenanceproposal` | Active Maintenance: A Proposal for the Long-term Computational Reprodu | long-term reproducibility needs maintenance over time, not a one-off pin |
| `pulicharla2024dataversioningimpact` | Data Versioning and Its Impact on Machine Learning Models | data versioning changes model behaviour: one declaration can admit different behaviour |
| `raatikainen2025machinelearninglineage` | Machine Learning Lineage for Trustworthy Machine Learning Systems: Inf | lineage as the record of what a model was built against |
| `randrianainandincrementalreproduciblebuilds` | Incremental, reproducible builds of software variants | incremental reproducible builds of variants: the cost side of pinning |
| `reyes2026byamfixingbreaking` | Byam: Fixing Breaking Dependency Updates with Large Language Models | LLM-based repair of breaking updates: a post-hoc remedy, complementary to measuring admissibility |
| `schmid2026mavenlockfilehigh` | Maven-Lockfile: High Integrity Rebuild of Past Java Releases | Maven-Lockfile: high-integrity rebuild of past Java releases, i.e. the lockfile as the alternative to a range |
| `solarin2026justtimestampsstudy` | It’s Not Just Timestamps: A Study on Docker Reproducibility | Docker rebuilds are not reproducible even from the same inputs, so the tag is not the only source of drift, but it is the one the author controls |
| `tekin2026deathendlongitudinal` | Death Is Not the End: a Longitudinal Study on the Impact of Automatic  | a longitudinal study of automatic updates on containers: a mutable tag makes a published environment change under the reader |
| `turner2025makeyourdevelopment` | Make your development environment portable and reproducible | portable development environments as a reproducibility practice |
| `varanasi2019mavendependencymanagement` | Maven Dependency Management | Maven's mediation rule (nearest wins) as a range dialect with its own resolution semantics |
| `wonsil2023integratedreproducibilityself` | Integrated Reproducibility with Self-describing Machine Learning Model | self-describing models carry their dependency identity instead of leaving it to be inferred from a range |
| `yang2026reproduciblellmbased` | Reproducible LLM-Based Measurement Depends on the Serving Stack | reproducibility of a measurement depends on the serving stack, a version range that is not a code range |

### S8 — Theory setting: constraint classes and cover problems (7)

| key | title | claim supported |
|---|---|---|
| `carbonnel2015tractabilityconstraintsatisfaction` | Tractability in constraint satisfaction problems: a survey | tractability of constraint classes: the vocabulary in which our admissible-set problem is stated |
| `carbonnelndharnessingtractabilityconstraint` | Harnessing tractability in constraint satisfaction problems | harnessing tractability: restricted constraint languages are where structure becomes exploitable |
| `cooper2010generalizingconstraintsatisfaction` | Generalizing constraint satisfaction on trees: Hybrid tractability and | hybrid tractability via variable elimination: the structural condition behind the closure result |
| `duttandsurveyapproximationalgorithms` | Survey of Approximation Algorithms for Set Cover Problem | approximation bounds for cover: the source of the log-factor statement we test and find unattained |
| `ganian2015discoveringarchipelagostractability` | Discovering Archipelagos of Tractability for Constraint Satisfaction a | islands of tractability: structure, not arity, decides the cost |
| `hochbaum2008multiintegerset` | The multi‐integer set cover and the facility terminal cover problem | weighted and multi-integer cover: the general form our unit-cost instance degenerates from |
| `miguel2004constraintsatisfactionproblem` | The Constraint Satisfaction Problem | the standard CSP formulation, cited for stating a declaration as a constraint |

### S9 — Method: interval estimation for a proportion (6)

| key | title | claim supported |
|---|---|---|
| `almendraarao2020adjustedwaldconfidence` | USING ADJUSTED WALD CONFIDENCE INTERVAL FOR A BINOMIAL PROPORTION | adjusted Wald intervals: a variant we choose against, since Wald-type intervals misbehave where our smallest rates sit |
| `garthwaite2023locallycorrectconfidence` | Locally correct confidence intervals for a binomial proportion: A new  | criteria for judging an interval's correctness: why we report the interval we do |
| `guan2012generalizedscoreconfidence` | A generalized score confidence interval for a binomial proportion | score intervals: the family the Wilson interval belongs to |
| `habtzghi2014modifiedclopperpearson` | Modified Clopper-Pearson Confidence Interval for Binomial Proportion | conservative exact intervals: the coverage-versus-shortness trade-off we choose against |
| `kim2021generalizedagresticoull` | A generalized Agresti–Coull type confidence interval for a binomial pr | Agresti-Coull generalization and behaviour at small proportions, where several of our rates sit |
| `sandelius1952confidenceintervalsmallest` | A Confidence Interval for the Smallest Proportion of a Binomial Popula | the smallest-proportion case treated historically: our lowest rates are of this kind |

## Pruned at placement (64)

Recorded, not deleted. A record removed without a reason is a silent edit to the reference list; these are real records that support no claim in this paper.

| key | title | reason |
|---|---|---|
| `abbas2007agilesoftwareassurance` | Agile Software Assurance: An Empirical Study | kept by the word 'empirical'; an agile-assurance study with no measurement instrument we share |
| `abidha2022redblueset` | Red Blue Set Cover Problem on Axis-Parallel Hyperplanes and Other Obje | geometric variant on axis-parallel hyperplanes; no bearing on the cover instance we construct |
| `advanceinteractioninc1994contentaddressablevideo` | Content addressable video system for image display | a 1994 content-addressable video system: storage media, not artifact identity |
| `anon1999debianlinuxsuper` | Debian Linux ‘Super’ package buffer overflow | a buffer-overflow vulnerability report, not a study of dependency resolution |
| `anon2001rewritingdatadependency` | Rewriting and Data Dependency, Control Flow Analysis of a Logic-Based  | data dependency in logic-based specification rewriting; homonym |
| `anon2007firstinternationalsymposium2` | First International Symposium on Empirical Software Engineering and Me | front matter of a symposium, recorded by Crossref as a work |
| `anon2007firstinternationalsymposium3` | First International Symposium on Empirical Software Engineering and Me | front matter of the same symposium, second record |
| `anon2012confidenceintervalssimple` | - Confidence Intervals for a Simple Binomial Proportion | textbook chapter on binomial intervals, superseded by the primary sources kept |
| `anon2013tourismdependencydevelopment` | Tourism, Dependency and Development: A mode of analysis | dependency as a development-studies concept; homonym |
| `anon2018appendixdefinitioncontainer` | Appendix D: Definition: “Container” | an appendix definition of the word 'container'; a reference entry, not a work |
| `anon2020fasterscalablemodel` | Faster Scalable ML Model Deployment Using ONNX and Open Source Tools | model deployment tooling (ONNX); not version admissibility |
| `anon2020reportjointoffice` | Report of the Joint US Office of Naval Research, International Whaling | a whaling-commission report: the query's words appear, the subject does not |
| `anon2024enhancingmobileapp` | Enhancing Mobile App Performance with Dependency Management and Swift  | Swift Package Manager mobile-app performance; 'dependency management' there means build performance |
| `baker2009upgradesopenlibrary` | Upgrades to Open Library | a 2009 posted-content item titled 'Upgrades to Open Library', with no venue and no abstract: nothing in it can be cited for a claim |
| `balayla2024gaussiandistributionconfidence` | Gaussian Distribution, Confidence Intervals, Binomial (Wald) Proportio | textbook exposition of the Wald interval |
| `bikel2008eventmatchingtransitive` | Event matching using the transitive closure of dependency relations | transitive closure of dependency relations for event matching in NLP; homonym |
| `breiter2019newserializationlibrary` | The new C++ serialization library supporting backward and forward comp | binary/serialization backward compatibility, a different construct from range-bounded admissibility |
| `chambers2026opensourcedas` | The Open-Source DAS Python Ecosystem | 'DAS' is distributed acoustic sensing: a domain ecosystem, not a package registry |
| `chang2003solvingsetcover` | Solving the set cover problem and the problem of exact cover by 3-sets | DNA-computing solution to set cover; not a bound we use |
| `delater2013tracingrequirementssource` | Tracing Requirements and Source Code during Software Development: An E | requirements-to-code traceability |
| `dilts1998perceivedchanneldependency` | Perceived Channel Dependency and Conflict Resolution: Methods Employed | retail channel conflict resolution: homonym on both 'dependency' and 'conflict' |
| `diskin2009modelversioninglarge` | Model-versioning-in-the-large: Algebraic foundations and the tile nota | 'model versioning' in model-driven engineering: metamodel evolution, not artifact versions |
| `fahle2007fasterbranchbound` | A faster branch-and-bound algorithm for the test-cover problem based o | test-cover (program testing) instance: a different cover problem |
| `franca2009empiricalstudysoftware` | An empirical study on software engineers motivational factors | developer motivation factors |
| `haeusler2017combiningversioningmetamodel` | Combining Versioning and Metamodel Evolution in the ChronoSphere Model | model repository for metamodel evolution (ChronoSphere); the same MDE homonym |
| `haimfaridianndhowyoungfirms` | How young firms choose an early-stage open source ecosystem | firm-level adoption decisions; management literature with no resolution construct |
| `hatta2026reproducibilitynewcopyleft` | Reproducibility is the New Copyleft: Defining AGI-oriented Reproducibl | advocacy framing ('reproducibility is the new copyleft') with no measurement to cite |
| `hibbard2026asmincorpororatesimagetwin` | ASM Incorpororates ImageTwin Workflow Integration to Detect Image Dupl | biomedical image-duplication screening: 'image' here is a micrograph |
| `hyderjr2026drivenfailureanalysis` | AI-Driven Failure Analysis in Engineering Systems: LSTM-Based Failure  | LSTM failure prediction; 'dependency' in the title is not package dependency |
| `iswari2014improvementadaptablemodel` | Improvement of Adaptable Model Versioning (AMOR) framework for softwar | adaptable model versioning (AMOR) in MDE; the same homonym |
| `jingqiu2008addtemporalinformation` | Add temporal information to dependency structure language model for to | dependency grammar in a language model; homonym |
| `kalakoti2025provideragnosticinfrastructure` | Provider-Agnostic Infrastructure As Code: A Modular Framework For Secu | record carries a venue mismatch (Journal of International Crisis and Risk Communication Research) for an IaC framework paper; the record cannot be relied on |
| `kasradze2025subsidiesfostergrowth` | Do Subsidies Foster Growth or Dependency? An Empirical Analysis of Geo | subsidy dependence of firms; homonym on 'dependency' |
| `knoth2017reproducibilitypracticaladoption` | Reproducibility and Practical Adoption of GEOBIA with Open-Source Soft | a fifth domain instance of the container claim already placed four times; the record is real but citing it would pad the list rather than add a sentence |
| `lambers2018multigranularconflict` | Multi-granular conflict and dependency analysis in software engineerin | conflict analysis in graph transformation systems; 'conflict' names a different mechanism |
| `li2023understandingresolutionmulti` | Understanding Resolution of Multi-Language Bugs: An Empirical Study on | 'resolution of multi-language bugs' means bug fixing in polyglot projects; homonym on 'resolution' |
| `mizera2026machinelearningbased` | Machine-learning-based Tracking for MUonE Experiment | physics-experiment tracking: ML tracking of detector data, not artifact versions |
| `mu2026modelbuildmanifest` | The Model-Build-Manifest: A Dependency Injection pattern for Structura | sector-coupled energy systems: 'dependency injection' names a modelling pattern, not package resolution |
| `nawa2022weightedscoreconfidence` | A weighted score confidence interval for a binomial proportion | weighted score interval for a variant problem |
| `odzaly2009softwareriskmanagement` | Software risk management barriers: An empirical study | barriers to software risk management |
| `ogura2018improvementbayesiancredible` | Improvement of Bayesian Credible Interval for a Small Binomial Proport | Bayesian credible interval: a different inferential frame |
| `ohta2015containerbasedsequence` | Container-based sequence data analysis workflow for reproducible resea | another domain instance of the placed container claim; no distinct sentence to support |
| `oladunni2016spatialdependencyhedonic` | Spatial Dependency and Hedonic Housing Regression Model | spatial dependence in an econometric housing model; homonym |
| `onagh2024extensiondecisionsopen` | Extension Decisions in Open Source Software Ecosystem | plugin-extension adoption decisions; adjacent construct, no version admissibility |
| `pagourtzis2001pvmcomputationtransitive` | PVM Computation of the Transitive Closure: The Dependency Graph Approa | parallel transitive-closure computation algorithm; homonym |
| `panchanathan1989contentaddressablememory` | Content-Addressable Memory Architecture For Image Coding Using Vector  | content-addressable memory hardware: 'content addressable' is a circuit technique |
| `pazmioortiz2026mappingwebprivacy` | Mapping Web Privacy in Ecuador: A Reproducible Repeated-Measurement St | web-privacy measurement in Ecuador; kept only by the words 'reproducible' and 'measurement study' |
| `ren2011notealgorithmsconnected` | A note on ‘Algorithms for connected set cover problem and fault-tolera | connected set cover: a connectivity constraint we do not impose |
| `rodriguez2017empiricalstudyopen` | An Empirical Study of Open Source Virtual Reality Software Projects | open-source virtual-reality projects |
| `salmon2026howrecruitnew` | How to Recruit a New Maintainer for Your Package | maintainer recruitment; no declaration or resolution construct |
| `savidis2022softwarearchitecturemining` | Software Architecture Mining from Source Code with Dependency Graph Cl | architecture recovery from source-code dependencies; not registry declarations |
| `schneidewind2001knowledgerequirementssoftware` | Knowledge Requirements for Software Quality Measurement | knowledge requirements for quality measurement |
| `schnell2026signalsmeasurandsmeasurement` | From Signals to Measurands: A Measurement-Science Roadmap for Reproduc | measurement-science roadmap for analytical biology; other field |
| `song2022csscontainerresource` | CSS: Container Resource Manager Using System Call Pattern for Scientif | container scheduling and resource management, not version identity |
| `suber2008visualizingrepositorymetadata` | Visualizing repository metadata | 'repository' here is an open-access scholarly repository, not a package registry; a 2008 posted-content item with no venue |
| `syed2021reproducibilitydiversitycrisis` | Reproducibility, Diversity, and the Crisis of Inference in Psychology | psychology's reproducibility crisis: a different failure mode, not a declaration failing |
| `taber2014empiricalfacevalidity` | Empirical and face validity of software maintenance defect models used | validity of defect models at one laboratory |
| `tan2016setcoverbased` | A set-cover-based approach for the test-cost-sensitive attribute reduc | attribute reduction via set cover; other field |
| `wang2017aspectorientedintegration` | Aspect Oriented Integration Testing Method Based on Module Dependency  | aspect-oriented integration testing over a module dependency graph; not registry resolution |
| `wang2022staticanalysismethod` | A static analysis method of incremental codes using value dependency g | value-dependency graph for incremental code analysis; not package versions |
| `wang2024approximationalgorithmspartition` | Approximation Algorithms for the Partition Set Cover Problem with Pena | partition set cover with penalties: a variant we do not instantiate |
| `yang2024discriminatingcodeset` | Discriminating Code And Set Cover with K-Bend Paths | discriminating codes with k-bend paths; combinatorial variant with no bearing |
| `zhang2009algorithmsconnectedset` | Algorithms for connected set cover problem and fault-tolerant connecte | connected set cover; connectivity is not imposed here |
| `zimelewiczndenabledsystemsmodel` | ML-ENABLED SYSTEMS MODEL DEPLOYMENT AND MONITORING: STATUS QUO AND PRO | deployment monitoring of ML systems, not what a declaration admits |

## Against the submission bar

| gate | required | this corpus | state |
|---|---|---|---|
| references, each genuinely cited | ≥ 100 | 102 placed, each with a named section and claim | PASS |
| every entry verified against a real record | all | 102 of 102 placed | PASS |
| entries pruned with a stated reason | all prunes | 64 of 64 | PASS |
| ≥ 3 works compared with a stated difference | 3 | 6 | PASS |

A placement is a promise about the manuscript, not a count. The gate here checks that every placement names a section and a claim; it cannot check that the manuscript later makes good on the claim, because that text does not exist yet. That check belongs to the manuscript round, and it is the one that can still fail.
