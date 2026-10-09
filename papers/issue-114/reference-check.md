# Reference check -- authenticity and support

Every citation key used by the manuscript is verified below against a real external record before submission; `refs/verify_refs.py` re-runs these lookups and rewrites this file.  **102 of 102 entries verified.**

`Exists` asks whether the identifier resolves; `Support` asks whether the record found is the work the manuscript means -- two separate questions, because a DOI can resolve to a real paper that is not the declared one.

The instrument is the endpoint named in the `Method` column (`api.crossref.org/works/<doi>` for `doi`; `export.arxiv.org/api/query?id_list=<id>` for `arxiv`), and its known-present control is entry `[6]` (`10.1093/comjnl/25.4.465`, Weyuker 1982): a run in which the control does not resolve has read nothing and takes no verdict about the others.

| # | Key | Method | Exists | Support | Record found |
|---|---|---|---|---|---|
| 1 | `modularity` | doi | yes | OK | On the Criteria to Be Used in Decomposing Systems into Modules -- 10.21236/ad0773837 |
| 2 | `guarded` | doi | yes | OK | Guarded Commands, Nondeterminacy, and Formal Derivation of Programs -- 10.1007/978-1-4612-6315-9_14 |
| 3 | `hints` | doi | yes | OK | Hints on Test Data Selection: Help for the Practicing Programmer -- 10.1109/c-m.1978.218136 |
| 4 | `hoare` | doi | yes | OK | An Axiomatic Basis for Computer Programming -- 10.1007/978-1-4612-6315-9_9 |
| 5 | `lehman` | doi | yes | OK | Programs, life cycles, and laws of software evolution -- 10.1109/proc.1980.11805 |
| 6 | `non-testable` | doi | yes | OK | On Testing Non-Testable Programs -- 10.1093/comjnl/25.4.465 |
| 7 | `silverbullet` | doi | yes | OK | No Silver Bullet Essence and Accidents of Software Engineering -- 10.1109/mc.1987.1663532 |
| 8 | `wing` | doi | yes | OK | A specifier's introduction to formal methods -- 10.1109/2.58215 |
| 9 | `ckmetrics` | doi | yes | OK | Towards a metrics suite for object oriented design -- 10.1145/117954.117970 |
| 10 | `designbycontract` | doi | yes | OK | Applying 'design by contract' -- 10.1109/2.161279 |
| 11 | `equivmutants` | doi | yes | OK | Using compiler optimization techniques to detect equivalent mutants -- 10.1002/stvr.4370040303 |
| 12 | `metricsvalidation` | doi | yes | OK | A validation of object-oriented design metrics as quality indicators -- 10.1109/32.544352 |
| 13 | `rtssurvey` | doi | yes | OK | Analyzing regression test selection techniques -- 10.1109/32.536955 |
| 14 | `tichy` | doi | yes | OK | Should computer scientists experiment more? -- 10.1109/2.675631 |
| 15 | `daikon` | doi | yes | OK | Dynamically discovering likely program invariants to support program evolution -- 10.1145/302405.302467 |
| 16 | `jml` | doi | yes | OK | JML: A Notation for Detailed Design -- 10.1007/978-1-4615-5229-1_12 |
| 17 | `translatevalid` | doi | yes | OK | Translation validation for an optimizing compiler -- 10.1145/358438.349314 |
| 18 | `expguidelines` | doi | yes | OK | Preliminary guidelines for empirical research in software engineering -- 10.1109/tse.2002.1027796 |
| 19 | `prioritization` | doi | yes | OK | Test case prioritization: a family of empirical studies -- 10.1109/32.988497 |
| 20 | `tla` | doi | yes | OK | Specifying and verifying systems with TLA+ -- 10.1145/1133373.1133382 |
| 21 | `abstractionrefinement` | doi | yes | OK | Abstraction Refinement for Large Scale Model Checking -- 10.1007/0-387-34600-7 |
| 22 | `changedistilling` | doi | yes | OK | Change Distilling:Tree Differencing for Fine-Grained Source Code Change Extraction -- 10.1109/tse.2007.70731 |
| 23 | `daikonsystem` | doi | yes | OK | The Daikon system for dynamic detection of likely invariants -- 10.1016/j.scico.2007.01.015 |
| 24 | `feedbackrandom` | doi | yes | OK | Feedback-Directed Random Test Generation -- 10.1109/icse.2007.37 |
| 25 | `fourcolor` | doi | yes | OK | The Four Colour Theorem: Engineering of a Formal Proof -- 10.1007/978-3-540-87827-8_28 |
| 26 | `verificationcost` | doi | yes | OK | A Survey of Automated Techniques for Formal Software Verification -- 10.1109/tcad.2008.923410 |
| 27 | `blame` | doi | yes | OK | Well-Typed Programs Can’t Be Blamed -- 10.1007/978-3-642-00590-9_1 |
| 28 | `compcert` | doi | yes | OK | Formal verification of a realistic compiler -- 10.1145/1538788.1538814 |
| 29 | `complexityfaults` | doi | yes | OK | Predicting faults using the complexity of code changes -- 10.1109/icse.2009.5070510 |
| 30 | `impactequiv` | doi | yes | OK | The Impact of Equivalent Mutants -- 10.1109/icstw.2009.37 |
| 31 | `swnodechecking` | doi | yes | OK | Software model checking -- 10.1145/1592434.1592438 |
| 32 | `dafny` | doi | yes | OK | Dafny: An Automatic Program Verifier for Functional Correctness -- 10.1007/978-3-642-17511-4_20 |
| 33 | `assertmining` | doi | yes | OK | Mining API Usage Specifications via Searching Source Code from the Web -- 10.1201/b10928-11 |
| 34 | `dart` | doi | yes | OK | DART: Directed Automated Random Testing -- 10.1007/978-3-642-19237-1_4 |
| 35 | `mutationsurvey` | doi | yes | OK | An Analysis and Survey of the Development of Mutation Testing -- 10.1109/tse.2010.62 |
| 36 | `slamsdecade` | doi | yes | OK | A decade of software model checking with SLAM -- 10.1145/1965724.1965743 |
| 37 | `findingbugs` | doi | yes | OK | Finding and understanding bugs in C compilers -- 10.1145/2345156.1993532 |
| 38 | `genprog` | doi | yes | OK | GenProg: A Generic Method for Automatic Software Repair -- 10.1109/tse.2011.104 |
| 39 | `regressionsurvey` | doi | yes | OK | Regression testing minimization, selection and prioritization: a survey -- 10.1002/stv.430 |
| 40 | `secondorder` | doi | yes | OK | Isolating First Order Equivalent Mutants via Second Order Mutation -- 10.1109/icst.2012.160 |
| 41 | `valuegraph` | doi | yes | OK | Evaluating value-graph translation validation for LLVM -- 10.1145/2345156.1993533 |
| 42 | `tamingfuzzers` | doi | yes | OK | Taming compiler fuzzers -- 10.1145/2499370.2462173 |
| 43 | `tangled` | doi | yes | OK | The impact of tangled code changes -- 10.1109/msr.2013.6624018 |
| 44 | `why3` | doi | yes | OK | Why3 — Where Programs Meet Provers -- 10.1007/978-3-642-37036-6_8 |
| 45 | `aremutants` | doi | yes | OK | Are mutants a valid substitute for real faults in software testing? -- 10.1145/2635868.2635929 |
| 46 | `flakysurvey` | doi | yes | OK | An empirical analysis of flaky tests -- 10.1145/2635868.2635920 |
| 47 | `refinementtypes` | doi | yes | OK | Refinement types for Haskell -- 10.1145/2692915.2628161 |
| 48 | `awsformal` | doi | yes | OK | How Amazon web services uses formal methods -- 10.1145/2699417 |
| 49 | `frama-c` | doi | yes | OK | Frama-C: A software analysis perspective -- 10.1007/s00165-014-0326-7 |
| 50 | `oraclesurvey` | doi | yes | OK | The Oracle Problem in Software Testing: A Survey -- 10.1109/tse.2014.2372785 |
| 51 | `trivialequiv` | doi | yes | OK | Trivial Compiler Equivalence: A Large Scale Empirical Study of a Simple, Fast and Effective Equivalent Mutant Detection Technique -- 10.1109/icse.2015.103 |
| 52 | `metasurvey` | doi | yes | OK | A Survey on Metamorphic Testing -- 10.1109/tse.2016.2532875 |
| 53 | `threatsvalidity` | doi | yes | OK | Threats to the validity of mutation-based test assessment -- 10.1145/2931037.2931040 |
| 54 | `googleci` | doi | yes | OK | Taming Google-scale continuous testing -- 10.1109/icse-seip.2017.16 |
| 55 | `kepler` | doi | yes | OK | A FORMAL PROOF OF THE KEPLER CONJECTURE -- 10.1017/fmp.2017.1 |
| 56 | `mltestscore` | doi | yes | OK | The ML test score: A rubric for ML production readiness and technical debt reduction -- 10.1109/bigdata.2017.8258038 |
| 57 | `adaptingproof` | doi | yes | OK | Adapting proof automation to adapt proofs -- 10.1145/3167094 |
| 58 | `aprsurvey` | doi | yes | OK | Automatic Software Repair: A Survey -- 10.1109/tse.2017.2755013 |
| 59 | `mutationadvances` | doi | yes | OK | Mutation Testing Advances: An Analysis and Survey -- 10.1016/bs.adcom.2018.03.015 |
| 60 | `qedatlarge` | doi | yes | OK | QED at Large: A Survey of Engineering of Formally Verified Software -- 10.1561/9781680835953 |
| 61 | `rvmonitor` | doi | yes | OK | A survey of challenges for runtime verification from advanced application domains (beyond software) -- 10.1007/s10703-019-00337-w |
| 62 | `lean` | doi | yes | OK | The lean mathematical library -- 10.1145/3372885.3373824 |
| 63 | `flakypython` | doi | yes | OK | An Empirical Study of Flaky Tests in Python -- 10.1109/icst49551.2021.00026 |
| 64 | `hiddendebt` | doi | yes | OK | Technical Debt in Machine Learning Systems -- 10.7551/mitpress/12440.003.0011 |
| 65 | `mldeploysurvey` | doi | yes | OK | Challenges in Deploying Machine Learning: A Survey of Case Studies -- 10.1145/3533378 |
| 66 | `mltestingsurvey` | doi | yes | OK | Machine Learning Testing: Survey, Landscapes and Horizons -- 10.1109/tse.2019.2962027 |
| 67 | `samplingse` | doi | yes | OK | Sampling in software engineering research: a critical review and guidelines -- 10.1007/s10664-021-10072-8 |
| 68 | `experimentation` | doi | yes | OK | Experimentation in Software Engineering -- 10.1007/978-3-662-69306-3 |
| 69 | `aletheia` | arxiv | yes | OK | Aletheia: Permission-Minimality Testing for Coding-Agent Rules -- arXiv:2609.39678 |
| 70 | `assurancecases` | arxiv | yes | OK | Automatically Building Machine-Checked Assurance Cases from C Codebases to Requirements -- arXiv:2609.40119 |
| 71 | `c11semantics` | arxiv | yes | OK | Episodic Loops: Finitary Event Structures and Operational Semantics for C11 Programs with Retries -- arXiv:2609.34646 |
| 72 | `certporting` | arxiv | yes | OK | Towards Certificate-Driven Software Porting: A Self-Improving Agentic Harness for Scientific Program Optimization -- arXiv:2609.34069 |
| 73 | `compasspatches` | arxiv | yes | OK | COMPASS: Predicting the Relationship of Multiple Patches for Vulnerabilities with LLMs -- arXiv:2609.39783 |
| 74 | `contractaudit` | arxiv | yes | OK | Do Agent Benchmarks Do What They Say? An Executable-Contract Audit of Tool-Using Agent Environments -- arXiv:2609.37315 |
| 75 | `culpritsearch` | arxiv | yes | OK | From Codebase to Culprit (C2C): Reducing the Search Space for Bugs with Semantic Retrieval and Hierarchical Reinforcement Learning -- arXiv:2609.38402 |
| 76 | `dafnymodels` | arxiv | yes | OK | The Formalization of two Computational Models in Dafny -- arXiv:2609.34883 |
| 77 | `errhealing` | arxiv | yes | OK | Trustworthy Runtime Error Healing in Real-World Repositories: A Benchmark and Guardrail -- arXiv:2609.39086 |
| 78 | `faultless` | arxiv | yes | OK | Faultless: A Program Equivalence Technique for Validating and Evaluating Neural Decompilers -- arXiv:2609.34089 |
| 79 | `forte` | arxiv | yes | OK | Forte: A sensitivity type system for imperative Rust -- arXiv:2609.30254 |
| 80 | `gradertl` | arxiv | yes | OK | GRADE-RTL: Evaluating LLM-Generated RTL Beyond Compilation -- arXiv:2609.25335 |
| 81 | `leangroups` | arxiv | yes | OK | Machine-Checked Computational Group Theory in Lean 4: Operational Schreier-Sims Stabilizer Chains, BSGS Sifting, and Backtrack Ordered Partitions -- arXiv:2609.38492 |
| 82 | `manualopt` | arxiv | yes | OK | Is manual software optimization a thing of the past? -- arXiv:2609.37849 |
| 83 | `matchedcomposition` | arxiv | yes | OK | Dependently Typed Model Composition for Matching Logic -- arXiv:2609.34892 |
| 84 | `mcrl2coordination` | arxiv | yes | OK | Modelling Shared-Space Coordination in mCRL2: a Bach-to-mCRL2 Translation Framework -- arXiv:2609.37726 |
| 85 | `mergednotmeasured` | arxiv | yes | OK | Merged, Not Measured: An Empirical Study of Performance Issues Fixed by Coding Agents -- arXiv:2609.37985 |
| 86 | `mubric` | arxiv | yes | OK | Mubric: Mutation Testing-Guided Rubric Generation for LLM Evaluation -- arXiv:2609.37322 |
| 87 | `multilanglogics` | arxiv | yes | OK | Multi-language Program Logics -- arXiv:2609.32877 |
| 88 | `nominalproofs` | arxiv | yes | OK | Proofs Without Nominals: Gödel's Ontological Argument, its Shallow Embedding, and the Open Questions of the Monatshefte Notes -- arXiv:2609.36279 |
| 89 | `omegatest` | arxiv | yes | OK | Formalizing the Omega Test in Dafny -- arXiv:2609.34882 |
| 90 | `oxidize` | arxiv | yes | OK | Lifting the Preprocessor with Oxidize: Structure-Preserving C-to-Rust Translation (Technical Report) -- arXiv:2609.30062 |
| 91 | `patiencesort` | arxiv | yes | OK | Certification of Bilateral Patience Sort in Theorema and Rocq -- arXiv:2609.34889 |
| 92 | `perfmodels` | arxiv | yes | OK | Formal Reasoning about Performance Models -- arXiv:2609.37728 |
| 93 | `prefixoracles` | arxiv | yes | OK | Semantic Prefix Oracles for LLM Decoding: Contracts and Differential Validation -- arXiv:2609.35425 |
| 94 | `quantumequiv` | arxiv | yes | OK | Irene: Equivalence Checking of Hybrid Quantum Programs via Structure-Preserving Symbolic Reduction -- arXiv:2609.36065 |
| 95 | `refinedstream` | arxiv | yes | OK | Designing a Producer-driven Stream Protocol by Formal Refinement -- arXiv:2609.33813 |
| 96 | `safellmse` | arxiv | yes | OK | SafeLLM4SE: Statistical Evaluation and Reporting for LLM-based Software Engineering Systems -- arXiv:2609.37294 |
| 97 | `selfspec` | arxiv | yes | OK | Self-Spec Verifiable Code Generation -- arXiv:2609.39568 |
| 98 | `sessionlattices` | arxiv | yes | OK | Session Type State Spaces Form Lattices -- arXiv:2609.34927 |
| 99 | `tristate` | arxiv | yes | OK | Improved Tristate Multiplication With Formalization in Rocq -- arXiv:2609.39009 |
| 100 | `trustledger` | arxiv | yes | OK | A Trust Ledger and an Execution Check for CPG-Based C-to-Lean 4 Autoformalization: Separating Declined from Silently Incorrect Translations -- arXiv:2609.38237 |
| 101 | `verifguidance` | arxiv | yes | OK | From Verification Failures to Reusable Guidance for Coding Agents -- arXiv:2609.39022 |
| 102 | `vosti` | arxiv | yes | OK | Vosti: Specifying, Implementing, and Verifying Deterministic LLM Inference -- arXiv:2609.38981 |

## Where each author component came from

The house form is `Family, I.`, and it is formed from a record rather than from the field a harvest stored. Three routes, and every entry is on one of them:

| route | how the component is formed |
|---|---|
| `crossref` | the record's own structured `family`/`given` |
| `openalex` | the record carries no author in Crossref, so OpenAlex is asked by DOI |
| `arxiv-name` | the only form available is one string per author; the family name is the LAST token, and a name whose last token is an initial is not split |
| `absent` | no record read carries an author; the entry says so and names the record it read |

Entries whose component did not come from a structured record, with the form printed:

| # | Key | Route | Printed component |
|---|---|---|---|
| 64 | `hiddendebt` | absent | author not established on Crossref or OpenAlex for DOI 10.7551/mitpress/12440.003.0011 |
| 69 | `aletheia` | arxiv-name | Shi, J.; Chen, Y.; He, J.; et al. |
| 70 | `assurancecases` | arxiv-name | Li, H.; Wang, Z.; Li, G.; et al. |
| 71 | `c11semantics` | arxiv-name | Kissig, C.; Richards, J.; Batty, M. |
| 72 | `certporting` | arxiv-name | Jha, P.; Ghosh, A.; Ganesh, V. |
| 73 | `compasspatches` | arxiv-name | Song, Y.; Xie, D.; Xie, X.; et al. |
| 74 | `contractaudit` | arxiv-name | Bellibatlu, R. R.; Wang, Z.; Zhang, W. |
| 75 | `culpritsearch` | arxiv-name | Garg, A.; Yang-Smith, C.; Rishav, R.; et al. |
| 76 | `dafnymodels` | arxiv-name | Ciobâcă, Ş.; Gratie, D. E.; Rotariu, D. I. |
| 77 | `errhealing` | arxiv-name | Tan, G.; Chen, P.; Sun, Z.; et al. |
| 78 | `faultless` | arxiv-name | Dramko, L.; Le Goues, C.; Schwartz, E. |
| 79 | `forte` | arxiv-name | Abuah, C. |
| 80 | `gradertl` | arxiv-name | Susan, H.; Shivaranjani G. R.; Imran, M.; et al. |
| 81 | `leangroups` | arxiv-name | Dağlı, V.; Dağlı, Z.; Dağlı, D. |
| 82 | `manualopt` | arxiv-name | Poličar, P. G.; Špendl, M.; Hočevar, T. |
| 83 | `matchedcomposition` | arxiv-name | Kurucz, Á.; Bereczky, P.; Horpácsi, D. |
| 84 | `mcrl2coordination` | arxiv-name | Reuther, C.; Jacquet, J. M. |
| 85 | `mergednotmeasured` | arxiv-name | Qi, Z.; Li, H.; Chen, J.; et al. |
| 86 | `mubric` | arxiv-name | Yang, J.; Zhang, J. M.; Lou, Y.; et al. |
| 87 | `multilanglogics` | arxiv-name | Loitzl, A.; Mück, N.; Sammler, M. |
| 88 | `nominalproofs` | arxiv-name | Benzmüller, C. |
| 89 | `omegatest` | arxiv-name | Brănici-Faraon, A.; Ciobâcă, Ş.; Gratie, D. E. |
| 90 | `oxidize` | arxiv-name | De Greef, R.; Engels, T.; Van den Broucke, F.; et al. |
| 91 | `patiencesort` | arxiv-name | Drǎmnesc, I.; Jebelean, T.; Stratulat, S. |
| 92 | `perfmodels` | arxiv-name | Labbadi, M.; Majumdar, R.; Sathiyanarayana, V. R.; et al. |
| 93 | `prefixoracles` | arxiv-name | Kronlund-Drouault, P. |
| 94 | `quantumequiv` | arxiv-name | Ke, J.; Li, J.; Li, G. |
| 95 | `refinedstream` | arxiv-name | Lavoie, E. |
| 96 | `safellmse` | arxiv-name | Ortin, F. |
| 97 | `selfspec` | arxiv-name | Qian, J.; Dong, Y.; Li, Y.; et al. |
| 98 | `sessionlattices` | arxiv-name | Caldeira, A. Z. |
| 99 | `tristate` | arxiv-name | Edamana, N.; Kurur, P. P.; Cheramangalath, U. |
| 100 | `trustledger` | arxiv-name | Singavarapu, I. K.; Bhatt, M. |
| 101 | `verifguidance` | arxiv-name | Zhai, Y.; Chen, X.; Zhang, L.; et al. |
| 102 | `vosti` | arxiv-name | Qin, J.; Du, A.; Zhang, D.; et al. |

**Two entries stand outside the author component by the rule's own statement and are right as printed** (`README.md` -> *Presentation requirements*): a work whose record carries no author at all is recorded by naming the record read, and a corporate or multi-author work whose responsible body is named is printed as it stands. Both are listed above rather than silently left out.

## Rejections (near-misses that were NOT cited)

A title-overlap screen cannot separate these from a hit, so each is recorded with the reason it is not the work the query named:

| Key | Reason rejected |
|---|---|
| `sel4` | matched 'Is Formal Verification of seL4 Adequate...', not the seL4 SOSP paper |
| `isabelle` | matched a program-logic paper about Isabelle, not the Isabelle/HOL book |
| `liquidtypes` | matched 'Liquid Crystals: Main Types and Classification' -- a chemistry paper |
| `fmstate` | matched a book titled '...State of the Art and New Directions', not the roadmap paper |
| `fmpractice` | matched a teaching-index record, not the practice-and-experience survey |
| `metacacm` | matched a metamorphic-testing-for-ML paper, not the CACM review |
| `mldatavalidation` | matched a geospatial cross-validation paper; the query was a topic phrase, not a title |
| `specificationpatterns` | matched an unrelated tools paper |
| `monitorlearning` | matched an artificial-pancreas verification paper; duplicates rvmonitor's query |
| `testoraclellm` | matched an LLM test-case-generation paper, not an oracle-generation one |
| `aprbiblio` | matched 'Automatic Software Repair' -- ambiguous with aprsurvey, not the bibliography |
| `softwareaging` | record carries no year and the title is a fragment ('Software aging') |
| `churndefects` | record carries no year; a citation needs one |
| `equivalencetesting` | matched a book on digital-circuit equivalence, not program equivalence |
| `propchecking` | matched a PropEr integration paper; cite that work, not a book by that name |
| `covolution` | matched 'Specification and Implementation' -- a different work entirely |
| `alloyfindbugs` | matched a copy-paste-detection paper |
| `theoryofbrittle` | matched a software-quality-measurement paper, not a brittleness study |
| `spin` | matched 'Parallelizing the Spin Model Checker', not Holzmann's SPIN paper |
| `null` | no such work |
| `ossdoc` | no such work |
| `metascience` | query was a placeholder; no such work |
| `fuzzing` | query was a placeholder; no such work |
| `behavioralequiv` | query was a placeholder; no such work |
| `specevolution` | matched an SOA maintenance paper |
| `coq` | the Coq manual is not a citable record in this index |
| `runtimeverification` | matched an introduction chapter; the survey is rvmonitor |
