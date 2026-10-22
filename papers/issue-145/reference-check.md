# Reference check -- issue #145

**DERIVED FILE -- do not edit.** Regenerate with `python3 build_refs.py` from `refs_pool.json`.

| | |
|---|---|
| pool | `refs_pool.json`, 130 entries, cut from `papers/issue-145/research/references.json` |
| pool source content sha256 | `30e42378b486724f8ef280597059839b1ed0791453478261e1e33b92bd039468` |
| corpus considered | 210 entries |
| excluded after review | 80 (kept in the corpus with a stated reason) |
| verified / harvested | 12 / 118 |
| **cited in the manuscript** | **130** (bar: >= 100) |
| uncited entries | 0 -- C2 refuses to build otherwise |

## How the pool was built

grown from Crossref returns for topic queries, then reviewed twice: a salience pass (a title obviously in another field) and a criterion pass organised by this paper's constructs (does the record name a mechanism, population or method the paper uses?). Every kept entry carries the query that produced it; refusals stay in the corpus with a reason and are counted, not deleted.

## Per-entry check

Method: `verified` = an *asserted* citation (title + author + year written first) matched a Crossref record under two independent criteria; `harvested` = a record Crossref returned for a topic query, then read by a person and kept. Every entry was re-checked against Crossref by DOI (`build_references.py --check`): 0 stale, 0 NOT RUN.

| # | key | method | result | record found |
|---|---|---|---|---|
| 1 | `ladisa2023sok` | crossref | verified against Crossref by DOI | SoK: Taxonomy of Attacks on Open-Source Software Supply Chains (DOI `10.1109/sp46215.2023.10179304`) |
| 2 | `samaana2025opportunitiessecurityrisks` | discover-crossref | verified against Crossref by DOI | Opportunities and security risks of technical leverage: A replication  (DOI `10.1007/s10664-025-10648-8`) |
| 3 | `goncalves2022oidctcioidc` | discover-crossref | verified against Crossref by DOI | OIDC-TCI: OIDC with Trust Context Information (DOI `10.23919/wmnc56391.2022.9954295`) |
| 4 | `prnster2019fidesunleashingfull` | discover-crossref | verified against Crossref by DOI | Fides: Unleashing the Full Potential of Remote Attestation (DOI `10.5220/0008121003140321`) |
| 5 | `laurie2014certificate` | crossref | verified against Crossref by DOI | Certificate Transparency (DOI `10.17487/rfc6962`) |
| 6 | `ryan2014enhanced` | crossref | verified against Crossref by DOI | Enhanced Certificate Transparency and End-to-End Encrypted Mail (DOI `10.14722/ndss.2014.23379`) |
| 7 | `samuel2010survivable` | crossref | verified against Crossref by DOI | Survivable key compromise in software update systems (DOI `10.1145/1866307.1866315`) |
| 8 | `lamb2022reproducible` | crossref | verified against Crossref by DOI | Reproducible Builds: Increasing the Integrity of Software Supply Chain (DOI `10.1109/ms.2021.3073045`) |
| 9 | `buneman2001why` | crossref | verified against Crossref by DOI | Why and Where: A Characterization of Data Provenance (DOI `10.1007/3-540-44503-x_20`) |
| 10 | `cheney2009provenance` | crossref | verified against Crossref by DOI | Provenance in Databases: Why, How, and Where (DOI `10.1561/9781601982339`) |
| 11 | `muller2022howwherewhy` | discover-crossref | verified against Crossref by DOI | How, Where, and Why Data Provenance Improves Query Debugging: A Visual (DOI `10.1109/icde53745.2022.00292`) |
| 12 | `godfrey2015understandingsoftwareartifact` | discover-crossref | verified against Crossref by DOI | Understanding software artifact provenance (DOI `10.1016/j.scico.2013.11.021`) |
| 13 | `cronbach1955construct` | crossref | verified against Crossref by DOI | Construct validity in psychological tests. (DOI `10.1037/h0040957`) |
| 14 | `berry2000instrumentassessingsoftware` | discover-crossref | verified against Crossref by DOI | An Instrument for Assessing Software Measurement Programs (DOI `10.1023/a:1026534430984`) |
| 15 | `schneidewind2001knowledgerequirementssoftware` | discover-crossref | verified against Crossref by DOI | Knowledge Requirements for Software Quality Measurement (DOI `10.1023/a:1011435315749`) |
| 16 | `hoess2025doestoolmatter` | discover-crossref | verified against Crossref by DOI | Does the Tool Matter? Exploring Some Causes of Threats to Validity in  (DOI `10.1109/saner64311.2025.00067`) |
| 17 | `mockus2014miningsoftwarerepositories` | discover-crossref | verified against Crossref by DOI | Is mining software repositories data science? (keynote) (DOI `10.1145/2597073.2600728`) |
| 18 | `voinea2006miningsoftwarerepositories` | discover-crossref | verified against Crossref by DOI | Mining software repositories with CVSgrab (DOI `10.1145/1137983.1138024`) |
| 19 | `baltes2022samplingsoftwareengineering` | discover-crossref | verified against Crossref by DOI | Sampling in software engineering research: a critical review and guide (DOI `10.1007/s10664-021-10072-8`) |
| 20 | `small2017empiricalgeneralizability` | discover-crossref | verified against Crossref by DOI | Empirical Generalizability (DOI `10.1093/oso/9780190661427.003.0008`) |
| 21 | `demello2014samplingimprovementsoftware` | discover-crossref | verified against Crossref by DOI | Sampling improvement in software engineering surveys (DOI `10.1145/2652524.2652566`) |
| 22 | `nunkesser2026assessinggeneralizabilitymobile` | discover-crossref | verified against Crossref by DOI | Assessing the Generalizability of Mobile Software Engineering Research (DOI `10.3390/software5010012`) |
| 23 | `runesonndcasestudysampling` | discover-crossref | verified against Crossref by DOI | A case study using sampling to improve software inspection effectivene (DOI `10.1109/isese.2003.1237985`) |
| 24 | `gonzlezbarahona2011reproducibilityempiricalsoftware` | discover-crossref | verified against Crossref by DOI | On the reproducibility of empirical software engineering studies based (DOI `10.1007/s10664-011-9181-9`) |
| 25 | `juristo2013understandingreplicationsoftware` | discover-crossref | verified against Crossref by DOI | Towards understanding replication of software engineering experiments (DOI `10.1109/esem.2013.64`) |
| 26 | `brooks2013partialreplicationsample` | discover-crossref | verified against Crossref by DOI | A Partial Replication with a Sample Size of One: A Smoke Test for Empi (DOI `10.1109/reser.2013.7`) |
| 27 | `porter1998comparingdetectionmethods` | discover-crossref | verified against Crossref by DOI | Comparing Detection Methods For Software Requirements Inspections: A R (DOI `10.1023/a:1009776104355`) |
| 28 | `decan2019evolution` | crossref | verified against Crossref by DOI | An empirical comparison of dependency issues in OSS packaging ecosyste (DOI `10.1109/saner.2017.7884604`) |
| 29 | `kikas2020structure` | crossref | verified against Crossref by DOI | Structure and Evolution of Package Dependency Networks (DOI `10.1109/msr.2017.55`) |
| 30 | `cogo2021empiricalstudysame` | discover-crossref | verified against Crossref by DOI | An empirical study of same-day releases of popular packages in the npm (DOI `10.1007/s10664-021-09980-6`) |
| 31 | `cogo2021empiricalstudydependency` | discover-crossref | verified against Crossref by DOI | An Empirical Study of Dependency Downgrades in the npm Ecosystem (DOI `10.1109/tse.2019.2952130`) |
| 32 | `chowdhury2022untrivialitytrivialpackages` | discover-crossref | verified against Crossref by DOI | On the Untriviality of Trivial Packages: An Empirical Study of npm Jav (DOI `10.1109/tse.2021.3068901`) |
| 33 | `zerouali2019diversitysoftwarepackage` | discover-crossref | verified against Crossref by DOI | On the Diversity of Software Package Popularity Metrics: An Empirical  (DOI `10.1109/saner.2019.8667997`) |
| 34 | `chodorowski2021comparativeanalysisjavascript` | discover-crossref | verified against Crossref by DOI | Comparative analysis of JavaScript package managers - yarn and npm (DOI `10.35784/jcsi.2460`) |
| 35 | `saeidi2025whataboutour` | discover-crossref | verified against Crossref by DOI | What About Our Bug? A Study on the Responsiveness of NPM Package Maint (DOI `10.1109/esem64174.2025.00071`) |
| 36 | `islam2023empiricalstudynpm` | discover-crossref | verified against Crossref by DOI | An Empirical Study of npm Ecosystem Related Tweets by Core Software De (DOI `10.21203/rs.3.rs-2560509/v1`) |
| 37 | `rayarao2025shaihuludnpm` | discover-crossref | verified against Crossref by DOI | The Shai-Hulud NPM Supply Chain Attack: A Comprehensive Analysis of Se (DOI `10.22541/au.175830854.42750868/v1`) |
| 38 | `bommarito2019empiricalanalysispython` | discover-crossref | verified against Crossref by DOI | An Empirical Analysis of the Python Package Index (PyPI) (DOI `10.2139/ssrn.3426281`) |
| 39 | `guo2023empiricalstudymalicious` | discover-crossref | verified against Crossref by DOI | An Empirical Study of Malicious Code In PyPI Ecosystem (DOI `10.1109/ase56229.2023.00135`) |
| 40 | `ruohonen2021largescalesecurity` | discover-crossref | verified against Crossref by DOI | A Large-Scale Security-Oriented Static Analysis of Python Packages in  (DOI `10.1109/pst52912.2021.9647791`) |
| 41 | `peng2024lessmoreempirical` | discover-crossref | verified against Crossref by DOI | Less is More? An Empirical Study on Configuration Issues in Python PyP (DOI `10.1145/3597503.3639077`) |
| 42 | `vu2021typosquatting` | crossref | verified against Crossref by DOI | Typosquatting and Combosquatting Attacks on the Python Ecosystem (DOI `10.1109/eurospw51379.2020.00074`) |
| 43 | `ladisa2023feasibilitycrosslanguage` | discover-crossref | verified against Crossref by DOI | On the Feasibility of Cross-Language Detection of Malicious Packages i (DOI `10.1145/3627106.3627138`) |
| 44 | `gandhi2024automateddetectionmitigation` | discover-crossref | verified against Crossref by DOI | Automated Detection and Mitigation of Malicious Packages in the PyPI E (DOI `10.1109/incowoco64194.2024.10863220`) |
| 45 | `montaruli2025onedetectorfits` | discover-crossref | verified against Crossref by DOI | One Detector Fits All: Robust and Adaptive Detection of Malicious Pack (DOI `10.1109/acsac67867.2025.00053`) |
| 46 | `raszka2026maliciouspackagespublic` | discover-crossref | verified against Crossref by DOI | Malicious packages in public registries: reporting bias, detection cov (DOI `10.2139/ssrn.7592667`) |
| 47 | `lim2026bridgingregistryfragmentation` | discover-crossref | verified against Crossref by DOI | Bridging Registry Fragmentation: SBOM-Based Metadata for Generalized M (DOI `10.1109/access.2026.3743923`) |
| 48 | `zhang2025killingtwobirds` | discover-crossref | verified against Crossref by DOI | Killing Two Birds with One Stone: Malicious Package Detection in NPM a (DOI `10.1145/3705304`) |
| 49 | `liang2026detectingmaliciouspackages` | discover-crossref | verified against Crossref by DOI | Detecting Malicious Packages in PyPI and NPM by Clustering Installatio (DOI `10.1109/tse.2025.3618952`) |
| 50 | `liu2026seeingforesttaxonomy` | discover-crossref | verified against Crossref by DOI | Seeing the Forest: A Taxonomy-Guided Analysis and Improvement of Malic (DOI `10.1145/3844178.3844648`) |
| 51 | `wang2026decodingmaliciousnessscalable` | discover-crossref | verified against Crossref by DOI | Decoding Maliciousness: A Scalable Framework for Malicious PyPI Packag (DOI `10.2139/ssrn.6727185`) |
| 52 | `yan2026pypimaldetmaliciouspypi` | discover-crossref | verified against Crossref by DOI | PyPIMalDet: A malicious PyPI package detection method combining code f (DOI `10.1016/j.neunet.2025.108487`) |
| 53 | `iqbal2025pypiguardnovelmeta` | discover-crossref | verified against Crossref by DOI | PypiGuard: A novel meta-learning approach for enhanced malicious packa (DOI `10.1016/j.jisa.2025.104032`) |
| 54 | `iqbal2026clampdnetcross` | discover-crossref | verified against Crossref by DOI | CLAMPD-Net: Cross-language malicious package detection across PyPI and (DOI `10.1016/j.infsof.2026.108129`) |
| 55 | `jobu2026pypiguardlightweightexplainable` | discover-crossref | verified against Crossref by DOI | PyPIGuard: A Lightweight, Explainable Machine Learning Tool for Pre-In (DOI `10.2139/ssrn.7233262`) |
| 56 | `wyss2025evaluatingllmbased` | discover-crossref | verified against Crossref by DOI | Evaluating LLM-Based Detection of Malicious Package Updates in npm (DOI `10.1109/raid67961.2025.00047`) |
| 57 | `moufid2026metadatacompressibilityevaluation` | discover-crossref | verified against Crossref by DOI | Metadata Compressibility and Evaluation Bias in Malicious Package Dete (DOI `10.3390/jcp6050160`) |
| 58 | `sun2024integratingdeepcode` | discover-crossref | verified against Crossref by DOI | 1+1&gt;2: Integrating Deep Code Behaviors with Metadata Features for M (DOI `10.1145/3691620.3695493`) |
| 59 | `draz2026versioncontextcontrol` | discover-crossref | verified against Crossref by DOI | Version context and control construction in machine learning detection (DOI `10.1038/s41598-026-71750-5`) |
| 60 | `sehgal2024taxonomysurveysoftware` | discover-crossref | verified against Crossref by DOI | A Taxonomy and Survey of Software Bill of Materials (SBOM) Generation  (DOI `10.1007/978-3-031-50815-8_3`) |
| 61 | `kishimoto2025datasetsoftwarebill` | discover-crossref | verified against Crossref by DOI | A Dataset of Software Bill of Materials for Evaluating SBOM Consumptio (DOI `10.1109/msr66628.2025.00090`) |
| 62 | `nyambe2025reframingsoftwarebill` | discover-crossref | verified against Crossref by DOI | Reframing Software Bill of Materials (SBOM) Security Evaluation Using  (DOI `10.1109/isse65546.2025.11370101`) |
| 63 | `oberhauser2025sbomvisualizationsoftware` | discover-crossref | verified against Crossref by DOI | VR-SBOM: Visualization of Software Bill of Materials and Software Supp (DOI `10.1007/978-3-031-98033-6_4`) |
| 64 | `hendrick2022softwarebillmaterials` | discover-crossref | verified against Crossref by DOI | Software Bill of Materials (SBOM) and Cybersecurity Readiness (DOI `10.70828/rytl5793`) |
| 65 | `odonoghue2023impactssoftwarebill` | discover-crossref | verified against Crossref by DOI | Impacts of Software Bill of Materials (SBOM) Generation on Vulnerabili (DOI `10.1145/3689944.3696164`) |
| 66 | `lee2025softwarebillmaterials` | discover-crossref | verified against Crossref by DOI | Software Bill of Materials(SBOM) Implementation and Evaluation of AI-b (DOI `10.5762/kais.2025.26.4.268`) |
| 67 | `seknametla2025securesupplychain` | discover-crossref | verified against Crossref by DOI | Secure Supply Chain Management in DevOps: Addressing Software Bill of  (DOI `10.63282/3050-922x.ijeret-v6i2p115`) |
| 68 | `bamidelesamueladelusi2023blockchainintegratedsoftware` | discover-crossref | verified against Crossref by DOI | Blockchain-Integrated Software Bill of Materials (SBOM) for Real-Time  (DOI `10.32628/ijsrce237314`) |
| 69 | `beninger2024ers0enhancingmilitary` | discover-crossref | verified against Crossref by DOI | ERS0: Enhancing Military Cybersecurity with AI-Driven SBOM for Firmwar (DOI `10.23919/cycon62501.2024.10685598`) |
| 70 | `dalia2025cometogethersbom` | discover-crossref | verified against Crossref by DOI | Come Together: Sbom-Enhanced Vulnerability Assessment in Safety-Critic (DOI `10.2139/ssrn.5362510`) |
| 71 | `jang2026machinelearningbased` | discover-crossref | verified against Crossref by DOI | A Machine Learning-Based Vulnerability Prediction System Using SBOM Me (DOI `10.7840/kics.2026.51.4.792`) |
| 72 | `kawai2026missionawaresbom` | discover-crossref | verified against Crossref by DOI | Mission-Aware SBOM Vulnerability Triage with KEV/EPSS and LLM-Based VE (DOI `10.1109/jcsse68839.2026.11597025`) |
| 73 | `mydin2026sbomtoolingecosystem` | discover-crossref | verified against Crossref by DOI | SBOM Tooling Ecosystem: A Systematic Literature Review (DOI `10.1002/appl.70209`) |
| 74 | `shtoma2025sbombasedvulnerability` | discover-crossref | verified against Crossref by DOI | SBOM-BASED VULNERABILITY PRIORITIZATION IN SOFTWARE SUPPLY CHAIN USING (DOI `10.17721/ait.2025.2.04`) |
| 75 | `radanliev2023softwarevulnerabilitymanagement` | discover-crossref | verified against Crossref by DOI | ML) in Software Vulnerability Management: automations in the Software  (DOI `10.36227/techrxiv.23706684.v1`) |
| 76 | `rschendorf1991frechetboundstheir` | discover-crossref | verified against Crossref by DOI | FréChet-Bounds and Their Applications (DOI `10.1007/978-94-011-3466-8_9`) |
| 77 | `rschendorf1996developmentsfrechetbounds` | discover-crossref | verified against Crossref by DOI | Developments on Fréchet-bounds (DOI `10.1214/lnms/1215452625`) |
| 78 | `scarsini1997frechetclassesnonmonotone` | discover-crossref | verified against Crossref by DOI | Fréchet Classes and Nonmonotone Dependence (DOI `10.1007/978-94-011-5532-8_7`) |
| 79 | `skivnek2014basicboundsfrechet` | discover-crossref | verified against Crossref by DOI | Basic bounds of Fréchet classes (DOI `10.14736/kyb-2014-1-0095`) |
| 80 | `anon2020microeconometricspartialidentification` | discover-crossref | verified against Crossref by DOI | Microeconometrics with partial identification (DOI `10.1016/bs.hoe.2020.05.002`) |
| 81 | `molinari2019econometricspartialidentification` | discover-crossref | verified against Crossref by DOI | Econometrics with Partial Identification (DOI `10.1920/wp.cem.2019.2519`) |
| 82 | `molinari2008partialidentificationprobability` | discover-crossref | verified against Crossref by DOI | Partial identification of probability distributions with misclassified (DOI `10.1016/j.jeconom.2007.12.003`) |
| 83 | `mcadams2008partialidentificationtestable` | discover-crossref | verified against Crossref by DOI | Partial identification and testable restrictions in multi-unit auction (DOI `10.1016/j.jeconom.2008.07.003`) |
| 84 | `hong2017inferencesemiparametricconditional` | discover-crossref | verified against Crossref by DOI | Inference in semiparametric conditional moment models with partial ide (DOI `10.1016/j.jeconom.2016.09.014`) |
| 85 | `jiang2017limitingdistributionquasi` | discover-crossref | verified against Crossref by DOI | On limiting distribution of quasi-posteriors under partial identificat (DOI `10.1016/j.ecosta.2017.03.006`) |
| 86 | `fan2018partialidentificationinference` | discover-crossref | verified against Crossref by DOI | Partial identification and inference in censored quantile regression (DOI `10.1016/j.jeconom.2018.04.002`) |
| 87 | `beresteanu2012partialidentificationrandom` | discover-crossref | verified against Crossref by DOI | Partial identification using random set theory (DOI `10.1016/j.jeconom.2011.06.003`) |
| 88 | `obradovi2024measuringdiagnostictest` | discover-crossref | verified against Crossref by DOI | Measuring diagnostic test performance using imperfect reference tests: (DOI `10.1016/j.jeconom.2024.105842`) |
| 89 | `base_rate_fallacy` | crossref | verified against Crossref by DOI | The Base-Rate Fallacy in Probability Judgments (DOI `10.21236/ada045772`) |
| 90 | `ghanshyambhaipatel2025softwaresupplychain` | discover-crossref | verified against Crossref by DOI | Software Supply Chain Security: Implementing SLSA Compliance in CI/CD  (DOI `10.56975/ijrti.v10i7.205129`) |
| 91 | `mohomed2025argoslsasoftware` | discover-crossref | verified against Crossref by DOI | ARGO-SLSA: Software Supply Chain Security in Argo Workflows (DOI `10.1109/mercon67903.2025.11217128`) |
| 92 | `tamanna2025unravelingchallengessupply` | discover-crossref | verified against Crossref by DOI | Unraveling Challenges with Supply-Chain Levels for Software Artifacts  (DOI `10.2139/ssrn.5119626`) |
| 93 | `cesarano2023gosurfidentifyingsoftware` | discover-crossref | verified against Crossref by DOI | GoSurf: Identifying Software Supply Chain Attack Vectors in Go (DOI `10.1145/3689944.3696166`) |
| 94 | `reyes2025mavenhijacksoftware` | discover-crossref | verified against Crossref by DOI | Maven-Hijack: Software Supply Chain Attack Exploiting Packaging Order (DOI `10.1145/3733827.3765523`) |
| 95 | `chen2023runtimeverificationsoftware` | discover-crossref | verified against Crossref by DOI | Runtime Verification for Software Supply Chain Security using Confiden (DOI `10.1145/3689944.3696350`) |
| 96 | `williams2024narrowingsoftwaresupply` | discover-crossref | verified against Crossref by DOI | Narrowing the Software Supply Chain Attack Vectors: The SSDF Is Wonder (DOI `10.1109/msec.2024.3359798`) |
| 97 | `kerman2025softwaresupplychain` | discover-crossref | verified against Crossref by DOI | Software Supply Chain and DevOps Security Practices (DOI `10.6028/nist.sp.1800-44`) |
| 98 | `soeirondassessingsecuritysoftware` | discover-crossref | verified against Crossref by DOI | Assessing the Security of Software Supply Chains: Software Bill of Mat (DOI `10.70675/6dd72cb7z7135z4d1dza942z3f6c57308033`) |
| 99 | `gibb2025solvingpackagemanagement` | discover-crossref | verified against Crossref by DOI | Solving Package Management via Hypergraph Dependency Resolution (DOI `10.59350/nrbbt-e7k85`) |
| 100 | `gibb2026packagemanagerscarte` | discover-crossref | verified against Crossref by DOI | Package managers à la carte: A Formal Model of Dependency Resolution (DOI `10.59350/rk9s4-43g76`) |
| 101 | `zhu2026versionedtransitivedependency` | discover-crossref | verified against Crossref by DOI | Versioned Transitive Dependency-Closure Binding and Operation-Time Eff (DOI `10.2139/ssrn.7456458`) |
| 102 | `teng2026supplychainsoftware` | discover-crossref | verified against Crossref by DOI | Supply Chain Software Package Risk Scoring TD3-MPC Model Based on Depe (DOI `10.64972/jaat.2026v4.386p31e:413-425`) |
| 103 | `liu2022demystifyingvulnerabilitypropagation` | discover-crossref | verified against Crossref by DOI | Demystifying the vulnerability propagation and its evolution via depen (DOI `10.1145/3510003.3510142`) |
| 104 | `gao2026llmenhancedevolutionary` | discover-crossref | verified against Crossref by DOI | LLM-Enhanced Evolutionary Dependency Graphs: A System Approach to Prec (DOI `10.3390/math14142593`) |
| 105 | `abdalkareem2022machinelearningapproach` | discover-crossref | verified against Crossref by DOI | A Machine Learning Approach to Determine the Semantic Versioning Type  (DOI `10.2139/ssrn.4082606`) |
| 106 | `decan2021whatpackagedependencies` | discover-crossref | verified against Crossref by DOI | What Do Package Dependencies Tell Us About Semantic Versioning? (DOI `10.1109/tse.2019.2918315`) |
| 107 | `panter2025pvacpackageversion` | discover-crossref | verified against Crossref by DOI | PVAC: package version activity categorizer, leveraging semantic versio (DOI `10.1007/s10664-025-10678-2`) |
| 108 | `tang2026packageselectionversioning` | discover-crossref | verified against Crossref by DOI | Package selection and versioning matter (DOI `10.1038/s41592-026-03108-8`) |
| 109 | `newman2022sigstore` | discover-crossref | verified against Crossref by DOI | Sigstore (DOI `10.1145/3548606.3560596`) |
| 110 | `dias2021whatmakesgreat` | discover-crossref | verified against Crossref by DOI | What Makes a Great Maintainer of Open Source Projects? (DOI `10.1109/icse43902.2021.00093`) |
| 111 | `hendrick2023maintainerperspectivesopen` | discover-crossref | verified against Crossref by DOI | Maintainer Perspectives on Open Source Software Security: Survey-based (DOI `10.70828/pvsn3075`) |
| 112 | `linker2024sustainingmaintenancelabor` | discover-crossref | verified against Crossref by DOI | Sustaining Maintenance Labor for Healthy Open Source Software Projects (DOI `10.1145/3674805.3686667`) |
| 113 | `salmon2026howrecruitnew` | discover-crossref | verified against Crossref by DOI | How to Recruit a New Maintainer for Your Package (DOI `10.59350/qgdfk-ce602`) |
| 114 | `randrianainandincrementalreproduciblebuilds` | discover-crossref | verified against Crossref by DOI | Incremental, reproducible builds of software variants (DOI `10.70675/e95564c6zca79z417aza37ez10821a9a0a48`) |
| 115 | `goswami2024reproduciblehighperformance` | discover-crossref | verified against Crossref by DOI | Reproducible High Performance Computing without Redundancy with Nix (DOI `10.31219/osf.io/3fp2v`) |
| 116 | `anon2017workflowreadybioinformatics` | discover-crossref | verified against Crossref by DOI | Workflow-ready bioinformatics packages and Debian’s infrastructure for (DOI `10.7490/f1000research.1114468.1`) |
| 117 | `afshartous2008samplesizedetermination` | discover-crossref | verified against Crossref by DOI | Sample Size Determination for Binomial Proportion Confidence Intervals (DOI `10.1198/000313008x271474`) |
| 118 | `balayla2024gaussiandistributionconfidence` | discover-crossref | verified against Crossref by DOI | Gaussian Distribution, Confidence Intervals, Binomial (Wald) Proportio (DOI `10.1007/978-3-031-71452-8_13`) |
| 119 | `garthwaite2023locallycorrectconfidence` | discover-crossref | verified against Crossref by DOI | Locally correct confidence intervals for a binomial proportion: A new  (DOI `10.1111/sjos.12672`) |
| 120 | `guan2012generalizedscoreconfidence` | discover-crossref | verified against Crossref by DOI | A generalized score confidence interval for a binomial proportion (DOI `10.1016/j.jspi.2011.09.010`) |
| 121 | `habtzghi2014modifiedclopperpearson` | discover-crossref | verified against Crossref by DOI | Modified Clopper-Pearson Confidence Interval for Binomial Proportion (DOI `10.2991/jsta.2014.13.4.3`) |
| 122 | `kim2021generalizedagresticoull` | discover-crossref | verified against Crossref by DOI | A generalized Agresti–Coull type confidence interval for a binomial pr (DOI `10.1007/s42952-021-00143-3`) |
| 123 | `nawa2022weightedscoreconfidence` | discover-crossref | verified against Crossref by DOI | A weighted score confidence interval for a binomial proportion (DOI `10.1007/s42081-022-00146-2`) |
| 124 | `sandelius1952confidenceintervalsmallest` | discover-crossref | verified against Crossref by DOI | A Confidence Interval for the Smallest Proportion of a Binomial Popula (DOI `10.1111/j.2517-6161.1952.tb00105.x`) |
| 125 | `tang2005confidenceintervalconstruction` | discover-crossref | verified against Crossref by DOI | Confidence interval construction for proportion difference in small‐sa (DOI `10.1002/sim.2216`) |
| 126 | `anon2015powercalculationcausal` | discover-crossref | verified against Crossref by DOI | Power calculation for causal inference in social science: sample size  (DOI `10.23846/wp0026`) |
| 127 | `brydges2019effectsizeinterpretation` | discover-crossref | verified against Crossref by DOI | Effect Size Interpretation, Sample Size Calculation, and Statistical P (DOI `10.31234/osf.io/u2jbm`) |
| 128 | `dalgaard2023whatminimaldetectable` | discover-crossref | verified against Crossref by DOI | What minimal detectable effect size is in your power – An inverted sam (DOI `10.1192/j.eurpsy.2023.1139`) |
| 129 | `greenland1985powersamplesize` | discover-crossref | verified against Crossref by DOI | Power, sample size and smallest detectable effect determination for mu (DOI `10.1002/sim.4780040203`) |
| 130 | `hunter2024pumpestimatingpower` | discover-crossref | verified against Crossref by DOI | PUMP: Estimating Power, Minimum Detectable Effect Size, and Sample Siz (DOI `10.18637/jss.v108.i06`) |

## Notes a reader should have

* The pool stores the **first author only** (the registry field the corpus kept); the list says so rather than presenting a truncated author list as a complete one.
* Three entries carry no year and three no author in the registry record; they are listed with `n.d.` / a stated absence rather than an invented value.
* Excluded records stay in the research corpus with their reason. They are not listed here because they are not part of this work's citations, but the count above is reported so the pool's size is not mistaken for everything that was considered.
