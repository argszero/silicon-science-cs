# Reference authenticity report -- issue #93

Every reference in `manuscript.md` was checked against a real external record: a DOI through Crossref, an
arXiv key through the arXiv API. The method, the record found and the title agreement are recorded per
entry, in the manuscript's citation order (the `[n]` the bibliography renders in). The network half is
regenerated with `python3 refs/reference_check.py --query`; `reproduce.sh` re-reads the committed answers
offline and refuses a report that has drifted from them.

| | |
|---|---|
| entries checked | 121 |
| verified | 121 |
| mismatch | 0 |
| unverified | 0 |
| title-agreement threshold | 0.80 (normalized token overlap; below it an entry is a MISMATCH) |

## Method

* **Has a DOI ->** `https://api.crossref.org/works/<doi>`; the returned title must agree with the
  manuscript's entry (normalized token overlap >= 0.80). The DOI and container returned are printed, so a
  reader can see what was matched; a year difference is printed rather than failed, because an arXiv
  preprint and its published version legitimately carry different years.
* **No DOI ->** `http://export.arxiv.org/api/query?id_list=<id>,...`; the returned title must agree and
  the arXiv id is printed.

## Entries

**[1] wang2026** (arxiv) -- VERIFIED

> manuscript: *Reframing LLM Agent Security as an Agent-Human Interaction Problem*
>
> arXiv API id_list -> found *Reframing LLM Agent Security as an Agent-Human Interaction Problem*  (title overlap 1.00)
>
> query: 2605.24309; arXiv 2605.24309; year 2026 (manuscript: 2026)

**[2] irshad2026** (arxiv) -- VERIFIED

> manuscript: *The Verifiable Action Card: Trustworthy Human-In-The-Loop Control for Secure Autonomous Agents*
>
> arXiv API id_list -> found *The Verifiable Action Card: Trustworthy Human-in-the-Loop Control for Secure Autonomous Agents*  (title overlap 1.00)
>
> query: 2609.18411; arXiv 2609.18411; year 2026 (manuscript: 2026)

**[3] kumar2026** (arxiv) -- VERIFIED

> manuscript: *Loopjacking: Hijacking Human-In-The-Loop Approval*
>
> arXiv API id_list -> found *Loopjacking: Hijacking Human-in-the-Loop Approval*  (title overlap 1.00)
>
> query: 2609.21081; arXiv 2609.21081; year 2026 (manuscript: 2026)

**[4] surapani2026** (arxiv) -- VERIFIED

> manuscript: *Authorization Architectures for Tool-Using AI Agents*
>
> arXiv API id_list -> found *Authorization Architectures for Tool-Using AI Agents*  (title overlap 1.00)
>
> query: 2609.15906; arXiv 2609.15906; year 2026 (manuscript: 2026)

**[5] sun2026** (arxiv) -- VERIFIED

> manuscript: *When "Must" Becomes "Maybe": Constraint Weakening in LLM Agent Workflows*
>
> arXiv API id_list -> found *When "Must" Becomes "Maybe": Constraint Weakening in LLM Agent Workflows*  (title overlap 1.00)
>
> query: 2608.24569; arXiv 2608.24569; year 2026 (manuscript: 2026)

**[6] alpay2026** (arxiv) -- VERIFIED

> manuscript: *Approval Integrity and Recovery in LLM Answer Publication*
>
> arXiv API id_list -> found *Approval Integrity and Recovery in LLM Answer Publication*  (title overlap 1.00)
>
> query: 2609.15576; arXiv 2609.15576; year 2026 (manuscript: 2026)

**[7] li2026** (arxiv) -- VERIFIED

> manuscript: *When Agents See Differently: Exposing UI Desynchronization Threats in Mobile Agents*
>
> arXiv API id_list -> found *When Agents See Differently: Exposing UI Desynchronization Threats in Mobile Agents*  (title overlap 1.00)
>
> query: 2609.16732; arXiv 2609.16732; year 2026 (manuscript: 2026)

**[8] shraga2026** (arxiv) -- VERIFIED

> manuscript: *Approved Too Late: Verdict Staleness in LLM-Guarded Self-Adaptive Systems*
>
> arXiv API id_list -> found *Approved Too Late: Verdict Staleness in LLM-Guarded Self-Adaptive Systems*  (title overlap 1.00)
>
> query: 2608.26306; arXiv 2608.26306; year 2026 (manuscript: 2026)

**[9] hardy1988** (crossref) -- VERIFIED

> manuscript: *The Confused Deputy*
>
> Crossref /works/<doi> -> found *The Confused Deputy*  (title overlap 1.00)
>
> query: 10.1145/54289.871709; DOI 10.1145/54289.871709; ACM SIGOPS Operating Systems Review; year 1988 (manuscript: 1988)

**[10] dennis1983** (crossref) -- VERIFIED

> manuscript: *Programming Semantics for Multiprogrammed Computations*
>
> Crossref /works/<doi> -> found *Programming semantics for multiprogrammed computations*  (title overlap 1.00)
>
> query: 10.1145/357980.357993; DOI 10.1145/357980.357993; Communications of the ACM; year 1983 (manuscript: 1983)

**[11] lampson1973** (crossref) -- VERIFIED

> manuscript: *A Note on the Confinement Problem*
>
> Crossref /works/<doi> -> found *A note on the confinement problem*  (title overlap 1.00)
>
> query: 10.1145/362375.362389; DOI 10.1145/362375.362389; Communications of the ACM; year 1973 (manuscript: 1973)

**[12] katkar2026** (arxiv) -- VERIFIED

> manuscript: *NiyamAI - an Intent-Bound AI Agent with Cryptographically Verifiable Guardrails Using Zero-Knowledge Proofs*
>
> arXiv API id_list -> found *NiyamAI - An Intent-Bound AI Agent with Cryptographically Verifiable Guardrails using Zero-Knowledge Proofs*  (title overlap 1.00)
>
> query: 2608.07167; arXiv 2608.07167; year 2026 (manuscript: 2026)

**[13] qi2026** (arxiv) -- VERIFIED

> manuscript: *SILK: Closing the Time-Of-Check-To-Time-Of-Use Gap in RoT-Protected AI Systems*
>
> arXiv API id_list -> found *SILK: Closing the Time-of-Check-to-Time-of-Use Gap in RoT-Protected AI Systems*  (title overlap 1.00)
>
> query: 2608.26402; arXiv 2608.26402; year 2026 (manuscript: 2026)

**[14] kurady2026** (arxiv) -- VERIFIED

> manuscript: *Compositional Policy Violations: When Step-Level Compliance Fails in Agentic AI Workflows*
>
> arXiv API id_list -> found *Compositional Policy Violations: When Step-Level Compliance Fails In Agentic AI Workflows*  (title overlap 1.00)
>
> query: 2609.18820; arXiv 2609.18820; year 2026 (manuscript: 2026)

**[15] dixon2026** (arxiv) -- VERIFIED

> manuscript: *Adaptive AI Delegation under Uncertainty: A Bayesian Governance Policy for Sequential Decision Authority*
>
> arXiv API id_list -> found *Adaptive AI Delegation under Uncertainty: A Bayesian Governance Policy for Sequential Decision Authority*  (title overlap 1.00)
>
> query: 2606.29406; arXiv 2606.29406; year 2026 (manuscript: 2026)

**[16] hanley1982** (crossref) -- VERIFIED

> manuscript: *The Meaning and Use of the Area under a Receiver Operating Characteristic (ROC) Curve.*
>
> Crossref /works/<doi> -> found *The meaning and use of the area under a receiver operating characteristic (ROC) curve.*  (title overlap 1.00)
>
> query: 10.1148/radiology.143.1.7063747; DOI 10.1148/radiology.143.1.7063747; Radiology; year 1982 (manuscript: 1982)

**[17] metz1978** (crossref) -- VERIFIED

> manuscript: *Basic Principles of ROC Analysis*
>
> Crossref /works/<doi> -> found *Basic principles of ROC analysis*  (title overlap 1.00)
>
> query: 10.1016/s0001-2998(78)80014-2; DOI 10.1016/s0001-2998(78)80014-2; Seminars in Nuclear Medicine; year 1978 (manuscript: 1978)

**[18] swets1973** (crossref) -- VERIFIED

> manuscript: *The Relative Operating Characteristic in Psychology*
>
> Crossref /works/<doi> -> found *The Relative Operating Characteristic in Psychology*  (title overlap 1.00)
>
> query: 10.1126/science.182.4116.990; DOI 10.1126/science.182.4116.990; Science; year 1973 (manuscript: 1973)

**[19] parasuraman1997** (crossref) -- VERIFIED

> manuscript: *Humans and Automation: Use, Misuse, Disuse, Abuse*
>
> Crossref /works/<doi> -> found *Humans and Automation: Use, Misuse, Disuse, Abuse*  (title overlap 1.00)
>
> query: 10.1518/001872097778543886; DOI 10.1518/001872097778543886; Human Factors: The Journal of the Human Factors and Ergonomics Society; year 1997 (manuscript: 1997)

**[20] youden1950** (crossref) -- VERIFIED

> manuscript: *Index for Rating Diagnostic Tests*
>
> Crossref /works/<doi> -> found *Index for rating diagnostic tests*  (title overlap 1.00)
>
> query: 10.1002/1097-0142(1950)3:1<32::aid-cncr2820030106>3.0.co;2-3; DOI 10.1002/1097-0142(1950)3:1<32::aid-cncr2820030106>3.0.co;2-3; Cancer; year 1950 (manuscript: 1950)

**[21] paul2026** (arxiv) -- VERIFIED

> manuscript: *Governance-As-Code: Translating EU AI Act Technical Requirements into Executable Compliance Pipelines for Generative AI Systems*
>
> arXiv API id_list -> found *Governance-as-Code: Translating EU AI Act Technical Requirements into Executable Compliance Pipelines for Generative AI Systems*  (title overlap 1.00)
>
> query: 2609.20016; arXiv 2609.20016; year 2026 (manuscript: 2026)

**[22] santonidesio2018** (crossref) -- VERIFIED

> manuscript: *Meaningful Human Control over Autonomous Systems: A Philosophical Account*
>
> Crossref /works/<doi> -> found *Meaningful Human Control over Autonomous Systems: A Philosophical Account*  (title overlap 1.00)
>
> query: 10.3389/frobt.2018.00015; DOI 10.3389/frobt.2018.00015; Frontiers in Robotics and AI; year 2018 (manuscript: 2018)

**[23] elish2025** (crossref) -- VERIFIED

> manuscript: *Moral Crumple Zones: Cautionary Tales in Human–robot Interaction*
>
> Crossref /works/<doi> -> found *Moral crumple zones: cautionary tales in human–robot interaction*  (title overlap 1.00)
>
> query: 10.4337/9781800887305.00010; DOI 10.4337/9781800887305.00010; Robot Law: Volume II; year 2025 (manuscript: 2025)

**[24] raghav2026** (arxiv) -- VERIFIED

> manuscript: *A Unified Policy Architecture (UPA): The Governance Kernel for Enterprise AI Operating Systems*
>
> arXiv API id_list -> found *A Unified Policy Architecture (UPA): The Governance Kernel for Enterprise AI Operating Systems*  (title overlap 1.00)
>
> query: 2609.06543; arXiv 2609.06543; year 2026 (manuscript: 2026)

**[25] ferreira2026** (arxiv) -- VERIFIED

> manuscript: *When Intelligence Becomes Agency: A Theory of Governed, Proactive Agency for Symbiotic AI Systems*
>
> arXiv API id_list -> found *When Intelligence Becomes Agency: A Theory of Governed, Proactive Agency for Symbiotic AI Systems*  (title overlap 1.00)
>
> query: 2609.07741; arXiv 2609.07741; year 2026 (manuscript: 2026)

**[26] nijkamp2026** (arxiv) -- VERIFIED

> manuscript: *An Architecture for Long-Horizon Agents: Levels, Ticks and Cascaded Intelligence*
>
> arXiv API id_list -> found *An Architecture for Long-Horizon Agents: Levels, Ticks and Cascaded Intelligence*  (title overlap 1.00)
>
> query: 2609.19519; arXiv 2609.19519; year 2026 (manuscript: 2026)

**[27] chidambaram2026** (arxiv) -- VERIFIED

> manuscript: *A Two-Dimensional Study of the Model Context Protocol: Publication and Adoption*
>
> arXiv API id_list -> found *A Two-Dimensional Study of the Model Context Protocol: Publication and Adoption*  (title overlap 1.00)
>
> query: 2609.14721; arXiv 2609.14721; year 2026 (manuscript: 2026)

**[28] sohail2026** (arxiv) -- VERIFIED

> manuscript: *Characterizing Network Centralization and Observability in the Remote MCP Ecosystem*
>
> arXiv API id_list -> found *Characterizing Network Centralization and Observability in the Remote MCP Ecosystem*  (title overlap 1.00)
>
> query: 2609.19100; arXiv 2609.19100; year 2026 (manuscript: 2026)

**[29] ming2026** (arxiv) -- VERIFIED

> manuscript: *Human Capital, Not Model Benchmarks, Predicts Hybrid Intelligence in Forecasting*
>
> arXiv API id_list -> found *Human Capital, Not Model Benchmarks, Predicts Hybrid Intelligence in Forecasting*  (title overlap 1.00)
>
> query: 2607.02467; arXiv 2607.02467; year 2026 (manuscript: 2026)

**[30] vallabhaneni2026** (arxiv) -- VERIFIED

> manuscript: *SENTINEL-RL: Offloading Topological Reasoning from LLM Agents in the Security Operations Center*
>
> arXiv API id_list -> found *SENTINEL-RL: Offloading Topological Reasoning from LLM Agents in the Security Operations Center*  (title overlap 1.00)
>
> query: 2609.04159; arXiv 2609.04159; year 2026 (manuscript: 2026)

**[31] turan2026** (arxiv) -- VERIFIED

> manuscript: *Oversight Has a Capacity: Calibrating Agent Guards to a Subjective, Fatiguing Human*
>
> arXiv API id_list -> found *Oversight Has a Capacity: Calibrating Agent Guards to a Subjective, Fatiguing Human*  (title overlap 1.00)
>
> query: 2606.08919; arXiv 2606.08919; year 2026 (manuscript: 2026)

**[32] wang2026b** (arxiv) -- VERIFIED

> manuscript: *Approval Laundering: Systematizing Approval--Execution Binding Failures in AI Coding-Agent Harnesses*
>
> arXiv API id_list -> found *Approval Laundering: Systematizing Approval--Execution Binding Failures in AI Coding-Agent Harnesses*  (title overlap 1.00)
>
> query: 2609.38983; arXiv 2609.38983; year 2026 (manuscript: 2026)

**[33] lyu2026** (arxiv) -- VERIFIED

> manuscript: *From Version Conflicts to Decision Conflicts: Selective Revalidation for Long-Running AI Agents*
>
> arXiv API id_list -> found *From Version Conflicts to Decision Conflicts: Selective Revalidation for Long-Running AI Agents*  (title overlap 1.00)
>
> query: 2609.08015; arXiv 2609.08015; year 2026 (manuscript: 2026)

**[34] li2026a** (arxiv) -- VERIFIED

> manuscript: *From Evidence to Effect: Authority Semantics and Runtime Infrastructure for Stateful Agents*
>
> arXiv API id_list -> found *From Evidence to Effect: Authority Semantics and Runtime Infrastructure for Stateful Agents*  (title overlap 1.00)
>
> query: 2609.08472; arXiv 2609.08472; year 2026 (manuscript: 2026)

**[35] safin2026** (arxiv) -- VERIFIED

> manuscript: *Trust Propagation and Structural Containment in Multi-Agent LLM Pipelines*
>
> arXiv API id_list -> found *Trust propagation and structural containment in Multi-agent LLM pipelines*  (title overlap 1.00)
>
> query: 2609.17648; arXiv 2609.17648; year 2026 (manuscript: 2026)

**[36] huang2026** (arxiv) -- VERIFIED

> manuscript: *When Malicious Instructions Persist: Persistent Memory Poisoning Attack on Harness-Based Agents*
>
> arXiv API id_list -> found *When Malicious Instructions Persist: Persistent Memory Poisoning Attack on Harness-Based Agents*  (title overlap 1.00)
>
> query: 2609.13889; arXiv 2609.13889; year 2026 (manuscript: 2026)

**[37] wang2026a** (arxiv) -- VERIFIED

> manuscript: *ActGuard: Pre-Execution Action Auditing Against Indirect Prompt Injection in LLM Agents*
>
> arXiv API id_list -> found *ActGuard: Pre-execution Action Auditing against Indirect Prompt Injection in LLM Agents*  (title overlap 1.00)
>
> query: 2609.14987; arXiv 2609.14987; year 2026 (manuscript: 2026)

**[38] li2026b** (arxiv) -- VERIFIED

> manuscript: *Universal Defenses for Tool-Integrated LLM Agents Against Adversarial Attacks*
>
> arXiv API id_list -> found *Universal Defenses for Tool-Integrated LLM Agents Against Adversarial Attacks*  (title overlap 1.00)
>
> query: 2609.16098; arXiv 2609.16098; year 2026 (manuscript: 2026)

**[39] zhang2026** (arxiv) -- VERIFIED

> manuscript: *Origin Is All You Need: Provenance-Aware Transformers for Structural Trust-Boundary Separation*
>
> arXiv API id_list -> found *Origin Is All You Need: Provenance-Aware Transformers for Structural Trust-Boundary Separation*  (title overlap 1.00)
>
> query: 2609.21088; arXiv 2609.21088; year 2026 (manuscript: 2026)

**[40] ediga2026** (arxiv) -- VERIFIED

> manuscript: *Measuring and Exploiting Implicit Trust in LLM Tool-Calling Pipelines*
>
> arXiv API id_list -> found *Measuring and Exploiting Implicit Trust in LLM Tool-Calling Pipelines*  (title overlap 1.00)
>
> query: 2609.18217; arXiv 2609.18217; year 2026 (manuscript: 2026)

**[41] leong2026** (arxiv) -- VERIFIED

> manuscript: *Recognition Without Enforcement: Configuration-Dependent Failures in LLM Agent Instruction Arbitration and External Control*
>
> arXiv API id_list -> found *Recognition Without Enforcement: Configuration-Dependent Failures in LLM Agent Instruction Arbitration and External Control*  (title overlap 1.00)
>
> query: 2608.28502; arXiv 2608.28502; year 2026 (manuscript: 2026)

**[42] iyer2026** (arxiv) -- VERIFIED

> manuscript: *Closed-World Resolution Against Tool Hallucination in LLM Agents*
>
> arXiv API id_list -> found *Closed-World Resolution Against Tool Hallucination in LLM Agents*  (title overlap 1.00)
>
> query: 2609.19425; arXiv 2609.19425; year 2026 (manuscript: 2026)

**[43] ma2024** (arxiv) -- VERIFIED

> manuscript: *Caution for the Environment: Multimodal LLM Agents Are Susceptible to Environmental Distractions*
>
> arXiv API id_list -> found *Caution for the Environment: Multimodal LLM Agents are Susceptible to Environmental Distractions*  (title overlap 1.00)
>
> query: 2408.02544; arXiv 2408.02544; year 2024 (manuscript: 2024)

**[44] hu2026** (arxiv) -- VERIFIED

> manuscript: *Faithful Mobile GUI Agents with Guided Advantage Estimator*
>
> arXiv API id_list -> found *Faithful Mobile GUI Agents with Guided Advantage Estimator*  (title overlap 1.00)
>
> query: 2605.01208; arXiv 2605.01208; year 2026 (manuscript: 2026)

**[45] akkil2026** (arxiv) -- VERIFIED

> manuscript: *Emergence World: Adversarial Stress-Testing of Long-Horizon Multi-Agent Systems*
>
> arXiv API id_list -> found *Emergence World: Adversarial Stress-Testing of Long-Horizon Multi-Agent Systems*  (title overlap 1.00)
>
> query: 2609.17320; arXiv 2609.17320; year 2026 (manuscript: 2026)

**[46] xiong2026** (arxiv) -- VERIFIED

> manuscript: *Reachability-Based Capability Confinement for LLM Agents under Indirect Prompt Injection*
>
> arXiv API id_list -> found *Reachability-Based Capability Confinement for LLM Agents under Indirect Prompt Injection*  (title overlap 1.00)
>
> query: 2608.30041; arXiv 2608.30041; year 2026 (manuscript: 2026)

**[47] veski2026** (arxiv) -- VERIFIED

> manuscript: *CAPMAS: Capability-Based Delegation of Privileges in Multi-Agent Systems*
>
> arXiv API id_list -> found *CAPMAS: Capability-Based Delegation of Privileges in Multi-Agent Systems*  (title overlap 1.00)
>
> query: 2609.06500; arXiv 2609.06500; year 2026 (manuscript: 2026)

**[48] gong2026** (arxiv) -- VERIFIED

> manuscript: *Authority-Inference Separation in Agentic Finance: First-Line Control, Blockchain Enforcement, and Replayable Assurance*
>
> arXiv API id_list -> found *Authority-Inference Separation in Agentic Finance: First-Line Control, Blockchain Enforcement, and Replayable Assurance*  (title overlap 1.00)
>
> query: 2608.30519; arXiv 2608.30519; year 2026 (manuscript: 2026)

**[49] collina2026** (arxiv) -- VERIFIED

> manuscript: *Delegating Authorization to Misaligned Agents: Coalitional Alignment and Safe Control*
>
> arXiv API id_list -> found *Delegating Authorization to Misaligned Agents: Coalitional Alignment and Safe Control*  (title overlap 1.00)
>
> query: 2609.15803; arXiv 2609.15803; year 2026 (manuscript: 2026)

**[50] zhu2026** (arxiv) -- VERIFIED

> manuscript: *Runtime Authorization for Resources Acquired by AI Agents*
>
> arXiv API id_list -> found *Runtime Authorization for Resources Acquired by AI Agents*  (title overlap 1.00)
>
> query: 2609.14744; arXiv 2609.14744; year 2026 (manuscript: 2026)

**[51] zhu2026a** (arxiv) -- VERIFIED

> manuscript: *Versioned Transitive Dependency-Closure Binding and Operation-Time Effect Governance for Agent Skills: ClosureBound*
>
> arXiv API id_list -> found *Versioned Transitive Dependency-Closure Binding and Operation-Time Effect Governance for Agent Skills: ClosureBound*  (title overlap 1.00)
>
> query: 2609.05920; arXiv 2609.05920; year 2026 (manuscript: 2026)

**[52] hu2026a** (arxiv) -- VERIFIED

> manuscript: *Don't Trust the Code, Check Its Effects: Runtime Refinement for Regenerated Systems Code under an Adversarial Generator*
>
> arXiv API id_list -> found *Don't Trust the Code, Check Its Effects: Runtime Refinement for Regenerated Systems Code Under an Adversarial Generator*  (title overlap 1.00)
>
> query: 2609.00430; arXiv 2609.00430; year 2026 (manuscript: 2026)

**[53] zheng2026** (arxiv) -- VERIFIED

> manuscript: *LLM Agent Capabilities Should Follow Task Intent and Context Source*
>
> arXiv API id_list -> found *LLM Agent Capabilities Should Follow Task Intent and Context Source*  (title overlap 1.00)
>
> query: 2609.14631; arXiv 2609.14631; year 2026 (manuscript: 2026)

**[54] chernov2026** (arxiv) -- VERIFIED

> manuscript: *Brain API: An Intent-Aware Control Plane for Policy-Governed Agentic Systems*
>
> arXiv API id_list -> found *Brain API: An Intent-Aware Control Plane for Policy-Governed Agentic Systems*  (title overlap 1.00)
>
> query: 2609.21299; arXiv 2609.21299; year 2026 (manuscript: 2026)

**[55] wu2026** (arxiv) -- VERIFIED

> manuscript: *SkillShield: Prompt-Space Security Skills for LLM Coding Agents*
>
> arXiv API id_list -> found *SkillShield: Prompt-Space Security Skills for LLM Coding Agents*  (title overlap 1.00)
>
> query: 2608.25817; arXiv 2608.25817; year 2026 (manuscript: 2026)

**[56] bromme2026** (arxiv) -- VERIFIED

> manuscript: *A Black Box for Agentic Processes: Blockchain-Anchored Evidence for AI Agent Communication, Human Oversight, and GRC Audits*
>
> arXiv API id_list -> found *A Black Box for Agentic Processes: Blockchain-Anchored Evidence for AI Agent Communication, Human Oversight, and GRC Audits*  (title overlap 1.00)
>
> query: 2609.04017; arXiv 2609.04017; year 2026 (manuscript: 2026)

**[57] strong2026** (arxiv) -- VERIFIED

> manuscript: *RACER: Role-Aligned Competence Estimation for Human-AI Routing*
>
> arXiv API id_list -> found *RACER: Role-Aligned Competence Estimation for Human-AI Routing*  (title overlap 1.00)
>
> query: 2609.21953; arXiv 2609.21953; year 2026 (manuscript: 2026)

**[58] pesenti2026** (arxiv) -- VERIFIED

> manuscript: *Too Much of the Same: From Algorithmic to Human Bias in Learning to Defer*
>
> arXiv API id_list -> found *Too Much of the Same: From Algorithmic to Human Bias in Learning to Defer*  (title overlap 1.00)
>
> query: 2608.28050; arXiv 2608.28050; year 2026 (manuscript: 2026)

**[59] franc2025** (arxiv) -- VERIFIED

> manuscript: *Epistemic Reject Option Prediction*
>
> arXiv API id_list -> found *Epistemic Reject Option Prediction*  (title overlap 1.00)
>
> query: 2511.04855; arXiv 2511.04855; year 2025 (manuscript: 2025)

**[60] szabadvary2025** (arxiv) -- VERIFIED

> manuscript: *Classification with Reject Option: Distribution-Free Error Guarantees via Conformal Prediction*
>
> arXiv API id_list -> found *Classification with Reject Option: Distribution-free Error Guarantees via Conformal Prediction*  (title overlap 1.00)
>
> query: 2506.21802; arXiv 2506.21802; year 2025 (manuscript: 2025)

**[61] zaoui2025** (arxiv) -- VERIFIED

> manuscript: *Distributional Regression with Reject Option*
>
> arXiv API id_list -> found *Distributional regression with reject option*  (title overlap 1.00)
>
> query: 2503.23782; arXiv 2503.23782; year 2025 (manuscript: 2025)

**[62] rabanser2025** (arxiv) -- VERIFIED

> manuscript: *What Does It Take to Build a Performant Selective Classifier?*
>
> arXiv API id_list -> found *What Does It Take to Build a Performant Selective Classifier?*  (title overlap 1.00)
>
> query: 2510.20242; arXiv 2510.20242; year 2025 (manuscript: 2025)

**[63] ravikiran2026** (arxiv) -- VERIFIED

> manuscript: *When Models Defer to Wrong Answers: A Robustness Audit of Source-Attributed Cues in Multiple-Choice QA*
>
> arXiv API id_list -> found *When Models Defer to Wrong Answers: A Robustness Audit of Source-Attributed Cues in Multiple-Choice QA*  (title overlap 1.00)
>
> query: 2609.08934; arXiv 2609.08934; year 2026 (manuscript: 2026)

**[64] zhang2026a** (arxiv) -- VERIFIED

> manuscript: *Confidence Comes from Experience: Experiential Confidence Estimation from Reasoning to Agents*
>
> arXiv API id_list -> found *Confidence Comes from Experience: Experiential Confidence Estimation from Reasoning to Agents*  (title overlap 1.00)
>
> query: 2609.17708; arXiv 2609.17708; year 2026 (manuscript: 2026)

**[65] udayagiri2026** (arxiv) -- VERIFIED

> manuscript: *When to Call an LLM: A Confidence-Gated Hybrid for Cost-Effective Emotion Recognition in Conversational AI*
>
> arXiv API id_list -> found *When to Call an LLM: A Confidence-Gated Hybrid for Cost-Effective Emotion Recognition in Conversational AI*  (title overlap 1.00)
>
> query: 2609.17977; arXiv 2609.17977; year 2026 (manuscript: 2026)

**[66] pathak2026** (arxiv) -- VERIFIED

> manuscript: *When Should a Failing Robot Ask? Initiating Corrective Human-Robot Dialogue from Audited Sensor Evidence*
>
> arXiv API id_list -> found *When Should a Failing Robot Ask? Initiating Corrective Human-Robot Dialogue from Audited Sensor Evidence*  (title overlap 1.00)
>
> query: 2609.21942; arXiv 2609.21942; year 2026 (manuscript: 2026)

**[67] li2026c** (arxiv) -- VERIFIED

> manuscript: *A Scenario-Knowledge-Driven Pipeline for Just-In-Time Assistance*
>
> arXiv API id_list -> found *A Scenario-Knowledge-Driven Pipeline for Just-in-Time Assistance*  (title overlap 1.00)
>
> query: 2609.17132; arXiv 2609.17132; year 2026 (manuscript: 2026)

**[68] dietz2026** (arxiv) -- VERIFIED

> manuscript: *Human-In-The-Loop Nugget Annotation for Accountable LLM-as-a-Judge Evaluations*
>
> arXiv API id_list -> found *Human-in-the-Loop Nugget Annotation for Accountable LLM-as-a-Judge Evaluations*  (title overlap 1.00)
>
> query: 2606.29033; arXiv 2606.29033; year 2026 (manuscript: 2026)

**[69] parasuraman2010** (crossref) -- VERIFIED

> manuscript: *Complacency and Bias in Human Use of Automation: An Attentional Integration*
>
> Crossref /works/<doi> -> found *Complacency and Bias in Human Use of Automation: An Attentional Integration*  (title overlap 1.00)
>
> query: 10.1177/0018720810376055; DOI 10.1177/0018720810376055; Human Factors: The Journal of the Human Factors and Ergonomics Society; year 2010 (manuscript: 2010)

**[70] bainbridge1983** (crossref) -- VERIFIED

> manuscript: *Ironies of Automation*
>
> Crossref /works/<doi> -> found *Ironies of automation*  (title overlap 1.00)
>
> query: 10.1016/0005-1098(83)90046-8; DOI 10.1016/0005-1098(83)90046-8; Automatica; year 1983 (manuscript: 1983)

**[71] endsley1995** (crossref) -- VERIFIED

> manuscript: *The Out-Of-The-Loop Performance Problem and Level of Control in Automation*
>
> Crossref /works/<doi> -> found *The Out-of-the-Loop Performance Problem and Level of Control in Automation*  (title overlap 1.00)
>
> query: 10.1518/001872095779064555; DOI 10.1518/001872095779064555; Human Factors: The Journal of the Human Factors and Ergonomics Society; year 1995 (manuscript: 1995)

**[72] lee2004** (crossref) -- VERIFIED

> manuscript: *Trust in Automation: Designing for Appropriate Reliance*
>
> Crossref /works/<doi> -> found *Trust in Automation: Designing for Appropriate Reliance*  (title overlap 1.00)
>
> query: 10.1518/hfes.46.1.50.30392; DOI 10.1518/hfes.46.1.50.30392; Human Factors: The Journal of the Human Factors and Ergonomics Society; year 2004 (manuscript: 2004)

**[73] felt2015** (crossref) -- VERIFIED

> manuscript: *Improving SSL Warnings*
>
> Crossref /works/<doi> -> found *Improving SSL Warnings*  (title overlap 1.00)
>
> query: 10.1145/2702123.2702442; DOI 10.1145/2702123.2702442; Proceedings of the 33rd Annual ACM Conference on Human Factors in Computing Systems; year 2015 (manuscript: 2015)

**[74] bravolillo2011** (crossref) -- VERIFIED

> manuscript: *Improving Computer Security Dialogs*
>
> Crossref /works/<doi> -> found *Improving Computer Security Dialogs*  (title overlap 1.00)
>
> query: 10.1007/978-3-642-23768-3_2; DOI 10.1007/978-3-642-23768-3_2; Lecture Notes in Computer Science; year 2011 (manuscript: 2011)

**[75] bravolillo2013** (crossref) -- VERIFIED

> manuscript: *Your Attention Please*
>
> Crossref /works/<doi> -> found *Your attention please*  (title overlap 1.00)
>
> query: 10.1145/2501604.2501610; DOI 10.1145/2501604.2501610; Proceedings of the Ninth Symposium on Usable Privacy and Security; year 2013 (manuscript: 2013)

**[76] modic2014** (crossref) -- VERIFIED

> manuscript: *Reading This May Harm Your Computer: The Psychology of Malware Warnings*
>
> Crossref /works/<doi> -> found *Reading this May Harm Your Computer: The Psychology of Malware Warnings*  (title overlap 1.00)
>
> query: 10.2139/ssrn.2374379; DOI 10.2139/ssrn.2374379; SSRN Electronic Journal; year 2014 (manuscript: 2014)

**[77] anderson2015** (crossref) -- VERIFIED

> manuscript: *How Polymorphic Warnings Reduce Habituation in the Brain*
>
> Crossref /works/<doi> -> found *How Polymorphic Warnings Reduce Habituation in the Brain*  (title overlap 1.00)
>
> query: 10.1145/2702123.2702322; DOI 10.1145/2702123.2702322; Proceedings of the 33rd Annual ACM Conference on Human Factors in Computing Systems; year 2015 (manuscript: 2015)

**[78] egelman2008** (crossref) -- VERIFIED

> manuscript: *You've Been Warned*
>
> Crossref /works/<doi> -> found *You've been warned*  (title overlap 1.00)
>
> query: 10.1145/1357054.1357219; DOI 10.1145/1357054.1357219; Proceedings of the SIGCHI Conference on Human Factors in Computing Systems; year 2008 (manuscript: 2008)

**[79] dhamija2006** (crossref) -- VERIFIED

> manuscript: *Why Phishing Works*
>
> Crossref /works/<doi> -> found *Why phishing works*  (title overlap 1.00)
>
> query: 10.1145/1124772.1124861; DOI 10.1145/1124772.1124861; Proceedings of the SIGCHI Conference on Human Factors in Computing Systems; year 2006 (manuscript: 2006)

**[80] herley2009** (crossref) -- VERIFIED

> manuscript: *So Long, and No Thanks for the Externalities*
>
> Crossref /works/<doi> -> found *So long, and no thanks for the externalities*  (title overlap 1.00)
>
> query: 10.1145/1719030.1719050; DOI 10.1145/1719030.1719050; Proceedings of the 2009 workshop on New security paradigms workshop; year 2009 (manuscript: 2009)

**[81] vandersijs2006** (crossref) -- VERIFIED

> manuscript: *Overriding of Drug Safety Alerts in Computerized Physician Order Entry*
>
> Crossref /works/<doi> -> found *Overriding of Drug Safety Alerts in Computerized Physician Order Entry*  (title overlap 1.00)
>
> query: 10.1197/jamia.m1809; DOI 10.1197/jamia.m1809; Journal of the American Medical Informatics Association; year 2006 (manuscript: 2006)

**[82] weingart2003** (crossref) -- VERIFIED

> manuscript: *Physicians' Decisions to Override Computerized Drug Alerts in Primary Care*
>
> Crossref /works/<doi> -> found *Physicians' Decisions to Override Computerized Drug Alerts in Primary Care*  (title overlap 1.00)
>
> query: 10.1001/archinte.163.21.2625; DOI 10.1001/archinte.163.21.2625; Archives of Internal Medicine; year 2003 (manuscript: 2003)

**[83] kaushal2003** (crossref) -- VERIFIED

> manuscript: *Effects of Computerized Physician Order Entry and Clinical Decision Support Systems on Medication Safety*
>
> Crossref /works/<doi> -> found *Effects of Computerized Physician Order Entry and Clinical Decision Support Systems on Medication Safety*  (title overlap 1.00)
>
> query: 10.1001/archinte.163.12.1409; DOI 10.1001/archinte.163.12.1409; Archives of Internal Medicine; year 2003 (manuscript: 2003)

**[84] maxeyjones2018** (crossref) -- VERIFIED

> manuscript: *An Intervention to Decrease Catheter-Related Bloodstream Infections in the ICU*
>
> Crossref /works/<doi> -> found *An Intervention to Decrease Catheter-Related Bloodstream Infections in the ICU*  (title overlap 1.00)
>
> query: 10.1093/med/9780190467654.003.0047; DOI 10.1093/med/9780190467654.003.0047; 50 Studies Every Intensivist Should Know; year 2018 (manuscript: 2018)

**[85] mazaheri2026** (arxiv) -- VERIFIED

> manuscript: *Prior Audit-Repair Context Shifts LLM Verifier Thresholds Toward Leniency*
>
> arXiv API id_list -> found *Prior Audit-Repair Context Shifts LLM Verifier Thresholds Toward Leniency*  (title overlap 1.00)
>
> query: 2608.16003; arXiv 2608.16003; year 2026 (manuscript: 2026)

**[86] singh2026** (arxiv) -- VERIFIED

> manuscript: *Not All Attacks Are Learned Equally in Speech Deepfake Detection*
>
> arXiv API id_list -> found *Not All Attacks Are Learned Equally in Speech Deepfake Detection*  (title overlap 1.00)
>
> query: 2609.11763; arXiv 2609.11763; year 2026 (manuscript: 2026)

**[87] kasundra2025** (arxiv) -- VERIFIED

> manuscript: *AprielGuard*
>
> arXiv API id_list -> found *AprielGuard*  (title overlap 1.00)
>
> query: 2512.20293; arXiv 2512.20293; year 2025 (manuscript: 2025)

**[88] kim2026** (arxiv) -- VERIFIED

> manuscript: *Addressing Over-Refusal in LLMs with Competing Rewards*
>
> arXiv API id_list -> found *Addressing Over-Refusal in LLMs with Competing Rewards*  (title overlap 1.00)
>
> query: 2606.31748; arXiv 2606.31748; year 2026 (manuscript: 2026)

**[89] lim2026** (arxiv) -- VERIFIED

> manuscript: *Do Reasoning Representations Help Humans Evaluate LLM Outputs?*
>
> arXiv API id_list -> found *Do Reasoning Representations Help Humans Evaluate LLM Outputs?*  (title overlap 1.00)
>
> query: 2609.09038; arXiv 2609.09038; year 2026 (manuscript: 2026)

**[90] pawar2026** (arxiv) -- VERIFIED

> manuscript: *From Tokens to Semantics: Leveraging Complementary Signals for Hallucination Detection in Black-Box LLMs*
>
> arXiv API id_list -> found *From Tokens to Semantics: Leveraging Complementary Signals for Hallucination Detection in Black-Box LLMs*  (title overlap 1.00)
>
> query: 2609.02679; arXiv 2609.02679; year 2026 (manuscript: 2026)

**[91] heinrich2021** (arxiv) -- VERIFIED

> manuscript: *Human Factors Considerations in Satellite Operation's Human-Computer Interaction Technologies: A Review of Current Applications and Theory*
>
> arXiv API id_list -> found *Human Factors Considerations in Satellite Operation's Human-Computer Interaction Technologies: A Review of Current Applications and Theory*  (title overlap 1.00)
>
> query: 2110.04880; arXiv 2110.04880; year 2021 (manuscript: 2021)

**[92] casadomansilla2019** (arxiv) -- VERIFIED

> manuscript: *On the Side Effects of Automation in IoT: Complacency and Comfort vs. Relapse and Distrust*
>
> arXiv API id_list -> found *On the Side Effects of Automation in IoT: Complacency and Comfort vs. Relapse and Distrust*  (title overlap 1.00)
>
> query: 1911.08657; arXiv 1911.08657; year 2019 (manuscript: 2019)

**[93] qian2024** (arxiv) -- VERIFIED

> manuscript: *Take It, Leave It, or Fix It: Measuring Productivity and Trust in Human-AI Collaboration*
>
> arXiv API id_list -> found *Take It, Leave It, or Fix It: Measuring Productivity and Trust in Human-AI Collaboration*  (title overlap 1.00)
>
> query: 2402.18498; arXiv 2402.18498; year 2024 (manuscript: 2024)

**[94] ladapo2022** (crossref) -- VERIFIED

> manuscript: *Human-In-The-Loop Machine Learning: A State of the Art*
>
> Crossref /works/<doi> -> found *Human-in-the-Loop Machine Learning: A State of the Art*  (title overlap 1.00)
>
> query: 10.54660/.jfmr.2022.3.1.656-669; DOI 10.54660/.jfmr.2022.3.1.656-669; Journal of Frontiers in Multidisciplinary Research; year 2022 (manuscript: 2022)

**[95] holzinger2016** (crossref) -- VERIFIED

> manuscript: *Interactive Machine Learning for Health Informatics: When Do We Need the Human-In-The-Loop?*
>
> Crossref /works/<doi> -> found *Interactive machine learning for health informatics: when do we need the human-in-the-loop?*  (title overlap 1.00)
>
> query: 10.1007/s40708-016-0042-6; DOI 10.1007/s40708-016-0042-6; Brain Informatics; year 2016 (manuscript: 2016)

**[96] horvitz1999** (crossref) -- VERIFIED

> manuscript: *Principles of Mixed-Initiative User Interfaces*
>
> Crossref /works/<doi> -> found *Principles of mixed-initiative user interfaces*  (title overlap 1.00)
>
> query: 10.1145/302979.303030; DOI 10.1145/302979.303030; Proceedings of the SIGCHI conference on Human factors in computing systems the CHI is the limit - CHI '99; year 1999 (manuscript: 1999)

**[97] kamath2025** (arxiv) -- VERIFIED

> manuscript: *Enforcing Temporal Constraints for LLM Agents*
>
> arXiv API id_list -> found *Enforcing Temporal Constraints for LLM Agents*  (title overlap 1.00)
>
> query: 2512.23738; arXiv 2512.23738; year 2025 (manuscript: 2025)

**[98] shamis2025** (arxiv) -- VERIFIED

> manuscript: *TEE-BFT: Pricing the Security of Data Center Execution Assurance*
>
> arXiv API id_list -> found *TEE-BFT: Pricing the Security of Data Center Execution Assurance*  (title overlap 1.00)
>
> query: 2510.26091; arXiv 2510.26091; year 2025 (manuscript: 2025)

**[99] chen2026** (arxiv) -- VERIFIED

> manuscript: *Token Economics for LLM Agents: A Dual-View Study from Computing and Economics*
>
> arXiv API id_list -> found *Token Economics for LLM Agents: A Dual-View Study from Computing and Economics*  (title overlap 1.00)
>
> query: 2605.09104; arXiv 2605.09104; year 2026 (manuscript: 2026)

**[100] bars2025** (arxiv) -- VERIFIED

> manuscript: *Empirical Security Analysis of Software-Based Fault Isolation Through Controlled Fault Injection*
>
> arXiv API id_list -> found *Empirical Security Analysis of Software-based Fault Isolation through Controlled Fault Injection*  (title overlap 1.00)
>
> query: 2509.07757; arXiv 2509.07757; year 2025 (manuscript: 2025)

**[101] sotoudeh2025** (arxiv) -- VERIFIED

> manuscript: *Automated Formal Verification of a Software Fault Isolation System*
>
> arXiv API id_list -> found *Automated Formal Verification of a Software Fault Isolation System*  (title overlap 1.00)
>
> query: 2508.15898; arXiv 2508.15898; year 2025 (manuscript: 2025)

**[102] schwarz2025** (arxiv) -- VERIFIED

> manuscript: *Countermind: A Multi-Layered Security Architecture for Large Language Models*
>
> arXiv API id_list -> found *Countermind: A Multi-Layered Security Architecture for Large Language Models*  (title overlap 1.00)
>
> query: 2510.11837; arXiv 2510.11837; year 2025 (manuscript: 2025)

**[103] avina2025** (arxiv) -- VERIFIED

> manuscript: *PokiSEC: A Multi-Architecture, Containerized Ephemeral Malware Detonation Sandbox*
>
> arXiv API id_list -> found *pokiSEC: A Multi-Architecture, Containerized Ephemeral Malware Detonation Sandbox*  (title overlap 1.00)
>
> query: 2512.20860; arXiv 2512.20860; year 2025 (manuscript: 2025)

**[104] zhang2026b** (arxiv) -- VERIFIED

> manuscript: *Why Formal Monitors Fail: Attack Distribution Entropy as a Coverage Bound for LTL-Based LLM Agent Safety*
>
> arXiv API id_list -> found *Why Formal Monitors Fail: Attack Distribution Entropy as a Coverage Bound for LTL-Based LLM Agent Safety*  (title overlap 1.00)
>
> query: 2608.01388; arXiv 2608.01388; year 2026 (manuscript: 2026)

**[105] hanley1983** (crossref) -- VERIFIED

> manuscript: *A Method of Comparing the Areas under Receiver Operating Characteristic Curves Derived from the Same Cases.*
>
> Crossref /works/<doi> -> found *A method of comparing the areas under receiver operating characteristic curves derived from the same cases.*  (title overlap 1.00)
>
> query: 10.1148/radiology.148.3.6878708; DOI 10.1148/radiology.148.3.6878708; Radiology; year 1983 (manuscript: 1983)

**[106] brodersen2013** (crossref) -- VERIFIED

> manuscript: *Long-Term Psychosocial Consequences of False-Positive Screening Mammography*
>
> Crossref /works/<doi> -> found *Long-Term Psychosocial Consequences of False-Positive Screening Mammography*  (title overlap 1.00)
>
> query: 10.1370/afm.1466; DOI 10.1370/afm.1466; The Annals of Family Medicine; year 2013 (manuscript: 2013)

**[107] marteau1989** (crossref) -- VERIFIED

> manuscript: *Psychological Costs of Screening.*
>
> Crossref /works/<doi> -> found *Psychological costs of screening.*  (title overlap 1.00)
>
> query: 10.1136/bmj.299.6698.527; DOI 10.1136/bmj.299.6698.527; BMJ; year 1989 (manuscript: 1989)

**[108] bacchelli2013** (crossref) -- VERIFIED

> manuscript: *Expectations, Outcomes, and Challenges of Modern Code Review*
>
> Crossref /works/<doi> -> found *Expectations, outcomes, and challenges of modern code review*  (title overlap 1.00)
>
> query: 10.1109/icse.2013.6606617; DOI 10.1109/icse.2013.6606617; 2013 35th International Conference on Software Engineering (ICSE); year 2013 (manuscript: 2013)

**[109] bosu2015** (crossref) -- VERIFIED

> manuscript: *Characteristics of Useful Code Reviews: An Empirical Study at Microsoft*
>
> Crossref /works/<doi> -> found *Characteristics of Useful Code Reviews: An Empirical Study at Microsoft*  (title overlap 1.00)
>
> query: 10.1109/msr.2015.21; DOI 10.1109/msr.2015.21; 2015 IEEE/ACM 12th Working Conference on Mining Software Repositories; year 2015 (manuscript: 2015)

**[110] sadowski2018** (crossref) -- VERIFIED

> manuscript: *Modern Code Review*
>
> Crossref /works/<doi> -> found *Modern code review*  (title overlap 1.00)
>
> query: 10.1145/3183519.3183525; DOI 10.1145/3183519.3183525; Proceedings of the 40th International Conference on Software Engineering: Software Engineering in Practice; year 2018 (manuscript: 2018)

**[111] townsend1979** (crossref) -- VERIFIED

> manuscript: *Optimal Contracts and Competitive Markets with Costly State Verification*
>
> Crossref /works/<doi> -> found *Optimal Contracts and Competitive Markets With Costly State Verification*  (title overlap 1.00)
>
> query: 10.21034/sr.45; DOI 10.21034/sr.45; year 1979 (manuscript: 1979)

**[112] williamson1986** (crossref) -- VERIFIED

> manuscript: *Costly Monitoring, Financial Intermediation, and Equilibrium Credit Rationing*
>
> Crossref /works/<doi> -> found *Costly monitoring, financial intermediation, and equilibrium credit rationing*  (title overlap 1.00)
>
> query: 10.1016/0304-3932(86)90074-7; DOI 10.1016/0304-3932(86)90074-7; Journal of Monetary Economics; year 1986 (manuscript: 1986)

**[113] holmstrom1979** (crossref) -- VERIFIED

> manuscript: *Moral Hazard and Observability*
>
> Crossref /works/<doi> -> found *Moral Hazard and Observability*  (title overlap 1.00)
>
> query: 10.2307/3003320; DOI 10.2307/3003320; The Bell Journal of Economics; year 1979 (manuscript: 1979)

**[114] becker1968** (crossref) -- VERIFIED

> manuscript: *Crime and Punishment: An Economic Approach*
>
> Crossref /works/<doi> -> found *Crime and Punishment: an Economic Approach*  (title overlap 1.00)
>
> query: 10.1007/978-1-349-62853-7_2; DOI 10.1007/978-1-349-62853-7_2; The Economic Dimensions of Crime; year 1968 (manuscript: 1968)

**[115] polinsky1999** (crossref) -- VERIFIED

> manuscript: *The Economic Theory of Public Enforcement of Law*
>
> Crossref /works/<doi> -> found *The Economic Theory of Public Enforcement of Law*  (title overlap 1.00)
>
> query: 10.3386/w6993; DOI 10.3386/w6993; year 1999 (manuscript: 1999)

**[116] jensendeceased1998** (crossref) -- VERIFIED

> manuscript: *Theory of the Firm: Managerial Behavior, Agency Costs and Ownership Structure*
>
> Crossref /works/<doi> -> found *Theory of the Firm: Managerial Behavior, Agency Costs and Ownership Structure*  (title overlap 1.00)
>
> query: 10.2139/ssrn.94043; DOI 10.2139/ssrn.94043; year 1998 (manuscript: 1998)

**[117] thompson2007** (crossref) -- VERIFIED

> manuscript: *Reflections on Trusting Trust*
>
> Crossref /works/<doi> -> found *Reflections on trusting trust*  (title overlap 1.00)
>
> query: 10.1145/1283920.1283940; DOI 10.1145/1283920.1283940; ACM Turing award lectures; year 2007 (manuscript: 2007)

**[118] rose2019** (crossref) -- VERIFIED

> manuscript: *Zero Trust Architecture*
>
> Crossref /works/<doi> -> found *Zero Trust Architecture*  (title overlap 1.00)
>
> query: 10.6028/nist.sp.800-207-draft; DOI 10.6028/nist.sp.800-207-draft; year 2019 (manuscript: 2019)

**[119] anderson2020** (crossref) -- VERIFIED

> manuscript: *Security Engineering*
>
> Crossref /works/<doi> -> found *Security Engineering*  (title overlap 1.00)
>
> query: 10.1002/9781119644682; DOI 10.1002/9781119644682; year 2020 (manuscript: 2020)

**[120] diakopoulos2014** (crossref) -- VERIFIED

> manuscript: *Algorithmic Accountability*
>
> Crossref /works/<doi> -> found *Algorithmic Accountability*  (title overlap 1.00)
>
> query: 10.1080/21670811.2014.976411; DOI 10.1080/21670811.2014.976411; Digital Journalism; year 2015 (manuscript: 2014)

**[121] mittelstadt2016** (crossref) -- VERIFIED

> manuscript: *The Ethics of Algorithms: Mapping the Debate*
>
> Crossref /works/<doi> -> found *The ethics of algorithms: Mapping the debate*  (title overlap 1.00)
>
> query: 10.1177/2053951716679679; DOI 10.1177/2053951716679679; Big Data &amp; Society; year 2016 (manuscript: 2016)

## In-text keys, coverage and ambiguity

Every entry carries an in-text key matching the bibliography: the body cites `[n]` and the list is
numbered `[n]`, so the key in the text IS the key the list prints (quality-bar item 11,
*Citation mechanics*) -- `python3 cite_check.py` reads `citations 210 | distinct keys 120 of 120` and
`uncited records 0 of 120`, and it resolves each `[n]` through this package's own numbered list rather
than through the parts, which cite by key.

Bracketed groups in the prose that are NOT citations: the gate reports 1 bracket number(s)
matching no entry -- `[0]`. These are the model's interval `[0, 1]` (§1.3 and §5.3), where the ratio's
predicted crossing is said to lie outside it: a numeric range in prose, written in inline code,
not a citation. Its second element is entry [1] and no entry is left uncited by the reading.

## Journal reference gate (`refgate.py`, run from the repository root)

```text
=== papers/issue-93/manuscript.md
  window: the last `## References` heading (line 1094) to the end of the file (line 1336)
          — its numbered lines are read as entries
  entries=121  numbering=[n]
  block form: 121 entries, 0 of them not separated from the entry above by a blank line — consecutive entry lines are ONE paragraph to a CommonMark renderer (GitHub's preview included); read the page, not the source
  author form: 121/121 entry(s) carry the read's window (a family name, a comma, an initial — or a lone family name before the year); 0 print the family name ALL-CAPS, 1 carry a character reference (&…;) — a record's stored field is not the form an entry prints
  in-text cited numbers=122  covered=121/121  coverage=100.0%
  AMBIGUOUS: bracket numbers matching no entry (1) [0] — could be numeric ranges in prose, or a missing entry; verify manually (reference-check.md)
  GATE: PASS
```

## Verdict

**121 of 121 references verified against a real external record; 0 mismatch; 0 unverified.**

No entry is retained on the strength of its own text: each is either matched to a record fetched from
Crossref or arXiv, or it is reported as unverified and removed before submission.
