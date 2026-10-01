#!/usr/bin/env python3
"""#93 R416 -- the bibliography's selection: which record carries which claim, and the one-line difference.

This file is the AUTHORED part.  One entry per work, keyed by its record identifier (arXiv id, or DOI for the
classical limb), with the one-line stated difference the journal's presentation rules require.  Nothing here is
generated: the record's own fields (authors, year, title, venue, URL) are resolved by `refs_build_v93.py` from
the committed pools, and an identifier that is not in a pool is an ERROR -- which is how this journal caught
two hand-typed identifiers in its previous bibliography (R404).

Buckets, which are also the manuscript's order of first citation:
  A  the deployed regime, and the question            G  verifying the artifact: provenance, attestation, audit
  B  the reviewed object is not the executed one      H  what a programmatic monitor can and cannot do
  C  authorization, capability, and the artifact      I  the classical screening and warning literature (DOI),
  D  the human's signal: detect, defer, escalate         including the statistics of comparison (ROC pairing,
  E  the human's limits: fatigue, bias, warnings         Youden's index) -- there is no K block; R425 found the
  F  the cost of the gate                                legend naming one that the table does not have
  J  the economics of an oversight decision (DOI)

The tables below are the SELECTED works.  A work that was harvested and refused lives in `NOT_SELECTED`, with its
reason -- selection is a field, never a sentence inside a `difference` line (R424).
"""

ARXIV = [
    # ---- A  the deployed regime, and the question
    ("2605.24309", "Reframes agent security as an agent-human interaction problem and reports, from a survey of "
                   "production systems, that runtime approval is deployed while no criterion for when a gate pays "
                   "exists; it names the deployment and leaves the criterion open, which is this study's question."),
    ("2609.15906", "Surveys authorization architectures for tool-using agents and organises them by where the "
                   "check sits; it compares architectures as designs, and measures no value for a gate, so the "
                   "fidelity at which a gate's value turns negative is not a quantity in it."),
    ("2609.14721", "Measures publication and adoption of the Model Context Protocol across two dimensions; its "
                   "unit is a protocol's uptake, not the net value of a human approval step over a channel."),
    ("2609.19100", "Characterises centralization and observability of the remote MCP ecosystem by measurement; "
                   "observability of a tool transport is a different object from the fidelity of the artifact a "
                   "reviewer is shown."),
    ("2609.20016", "Translates EU AI Act obligations into executable compliance pipelines, i.e. a governance-as-"
                   "code reading of oversight; compliance is asserted by a pipeline, while this study asks "
                   "whether the human step it mandates has positive expected value."),
    ("2609.07741", "Proposes a theory of governed proactive agency with human control in the loop; it is a design "
                   "theory, and it fixes no parameter at which oversight stops paying."),
    ("2609.19519", "Gives an architecture for long-horizon agents built on levels and ticks, in which approval is "
                   "one scheduling event; scheduling an approval is not the same as pricing it."),
    ("2607.02467", "Finds that human capital rather than model benchmarks predicts hybrid human-AI forecasting "
                   "gain; it measures the human's contribution as a population property, and our construct is "
                   "whether the object the human is shown denotes the object that executes."),
    ("2609.06543", "Poses an enterprise governance kernel in which tool invocations are policy-mediated; a policy "
                   "kernel decides what is permitted, and the question here is what a gate is worth when the "
                   "object it reviews is not the object it authorises."),
    ("2609.04159", "Offloads topological reasoning from LLM agents in a security operations centre, where analyst "
                   "escalation is a routine step; escalation volume is treated as load to reduce rather than as "
                   "a cost term that can exceed the harm a gate prevents."),
    ("2606.08919", "Calibrates agent guards to a subjective, fatiguing human and shows oversight has a capacity; "
                   "it prices the reviewer's capacity, and our model keeps the reviewer fixed and varies the "
                   "channel's fidelity, so the two are complementary inputs to one value."),

    ("2608.24569", "Measures constraint weakening across 1,296 controlled episodes, where a normal handoff "
                   "transform deactivates binding state in 100.0% of them and 54.2% of downstream executions "
                   "perform a forbidden action; it measures that fidelity is below 1 in an ordinary pipeline, "
                   "which this study takes as the low end of its axis rather than as its question."),
    # ---- B  the reviewed object is not the executed one
    ("2609.21081", "Reproduces approval hijacking across agent frameworks and reports attack success without "
                   "binding versus with it; it establishes the failure exists and that binding removes it, and "
                   "does not give a value for the gate as a function of the fidelity that binds it."),
    ("2609.18411", "Binds an action to a verifiable card and reports 68-100% attack success unbound against 0% "
                   "bound with a 0% false-block rate; those are the endpoints of this study's fidelity axis, "
                   "read here as inputs to a value law rather than as a defence evaluation."),
    ("2608.26306", "Shows an LLM guardrail can approve correctly at check time and be stale by act time; staleness "
                   "is the time axis of the same defect this study writes as a substitution channel, and it "
                   "measures staleness rather than the value of the gate that suffers it."),
    ("2609.08015", "Identifies decision conflicts for long-running agents whose authorising state changes after "
                   "the check, and proposes selective revalidation; revalidation is a repair, and this study "
                   "gives the threshold on the fidelity axis at which a repair is worth its cost."),
    ("2609.16732", "Exposes UI desynchronization between what a mobile agent sees and what it acts on; that is a "
                   "representation mismatch measured as a vulnerability class, where our model makes it a "
                   "continuous fidelity parameter with a sign law."),
    ("2608.26402", "Closes the time-of-check-to-time-of-use gap in root-of-trust protected systems at the "
                   "hardware boundary; the mechanism is a trusted subsystem, whereas this study's subject is a "
                   "human reviewer whose view of the object can be unfaithful."),
    ("2609.08472", "Argues authority should be held by a substrate other than the agent's own context, with a "
                   "cross-substrate notion of authority; it settles where authority should live, not what an "
                   "approval step is worth once authority has been placed."),
    ("2609.17648", "Studies trust propagation and structural containment in multi-agent pipelines, where a "
                   "low-privilege agent can influence a high-privilege one; influence propagation across agents "
                   "is a different channel from the fidelity with which one approval denotes its action."),
    ("2609.13889", "Shows malicious instructions can persist in agent memory and re-enter later execution; "
                   "persistence is a temporal channel, and its harm is not modulated by the fidelity of any "
                   "single approval."),
    ("2609.14987", "Audits candidate actions before execution to block indirect-injection consequences; a "
                   "pre-execution audit is a programmatic check, which is one of the repairs this study prices "
                   "against a reviewer-mediated one."),
    ("2609.16098", "Gives defences for tool-integrated agents against adversarial tool outputs; it measures "
                   "blocking effectiveness, and this study measures when a human-mediated step is worth its own "
                   "cost, including when it is worth less than no step."),
    ("2609.21088", "Separates trust boundaries with provenance-aware transformers; provenance is a property the "
                   "model is trained to use, while this study treats the reviewer's information as a channel "
                   "whose fidelity is an experimental axis."),
    ("2609.18217", "Measures and exploits implicit trust in LLM tool-calling pipelines, including a protocol's "
                   "trust assumptions; the trust measured is the model's, not the reviewer's, and no approval "
                   "value is derived."),
    ("2608.28502", "Finds that instruction arbitration in agents is configuration-dependent and that recognition "
                   "does not imply enforcement; the gap between recognising and enforcing is the same family as "
                   "a mismatch channel, measured as a failure mode rather than as a fidelity parameter."),
    ("2609.19425", "Resolves tool names in a closed world to stop hallucinated calls; a hallucinated tool is not "
                   "an approved object that failed to denote its action, so the defect it repairs is upstream of "
                   "the approval channel."),
    ("2408.02544", "Shows multimodal GUI agents are distracted by environmental content; distraction is an input-"
                   "side effect on the agent, whereas this study's channel carries the object to a human."),
    ("2605.01208", "Trains GUI agents towards faithful behaviour rather than memorised shortcuts; it makes the "
                   "agent's action faithful to the task, and our fidelity is between the object a reviewer "
                   "approves and the object the system executes."),
    ("2609.17320", "Stress-tests long-horizon multi-agent systems adversarially so failures propagate through "
                   "memory and tools; it reports propagation, where this study gives a value law for one gate "
                   "at one fidelity."),
    ("2608.07167", "Binds an agent's intent with cryptographically verifiable guardrails; the binding is "
                   "verified cryptographically, which is the b = 1 end of this study's axis rather than a "
                   "quantity computed across it."),

    # ---- C  authorization, capability, and the artifact that authorises
    ("2608.30041", "Confines reachable capabilities for LLM agents under indirect injection, at the level of "
                   "what a compromised agent can reach; capability reach is a bound on harm, and the value of "
                   "an approval gate is a different quantity, which this study makes depend on fidelity."),
    ("2609.06500", "Delegates privileges among collaborating agents with a capability-based scheme; delegation "
                   "governs who may act, while the question here is whether the object presented for review "
                   "denotes the action taken."),
    ("2608.30519", "Separates inference from authority in agentic finance, so that a model's suggestion cannot "
                   "confer authorisation; that separation is a policy design, and this study quantifies the "
                   "step that implements it."),
    ("2609.14744", "Governs authority an agent acquires at runtime, for resources such as credentials and "
                   "accounts; acquired authority is a flow the policy must contain, and it is orthogonal to the "
                   "fidelity of an approval artifact."),
    ("2609.05920", "Binds a dependency closure and governs effects at operation time for agent skills; effect "
                   "governance is a check on the operation, which is the repair axis this study prices."),
    ("2609.00430", "Checks effects at runtime rather than trusting regenerated systems code; checking effects is "
                   "one of the two repairs in this study's design ladder, and its value is measured here as a "
                   "function of what the check can see."),
    ("2609.14631", "Argues agent capabilities should follow task intent and the source of context, so that "
                   "authority tracks provenance; the argument is normative, and the value of the approval step "
                   "it implies is what this study measures."),
    ("2609.21299", "Proposes an intent-aware control plane for policy-governed agentic systems; a control plane "
                   "enforces policy at a boundary, and this study's unit is a single reviewer-mediated decision "
                   "with a computable value."),
    ("2609.15803", "Studies delegating authorization to misaligned agents through coalitional alignment and safe "
                   "control; misalignment is a property of the agent's objective, and the laundering channel "
                   "here requires no misalignment, only an unfaithful artifact."),
    ("2608.25817", "Delivers prompt-space security skills to coding agents so that privilege use is mediated; it "
                   "mediates the agent's own requests, while this study asks when a human-mediated mediation "
                   "step has positive expected value."),
    ("2609.04017", "Anchors agent communication and human approvals in blockchain evidence for auditability; "
                   "auditability after the fact is a separate good from the expected value of the approval the "
                   "record attests."),

    # ---- D  the human's signal: detect, defer, escalate
    ("2609.21953", "Estimates whether a model should act or defer to a human expert, and adapts deferral across "
                   "experts; the deferral rule is the same structure as this study's escalation coverage, with "
                   "the channel's fidelity held fixed and no harm term from an unfaithful review."),
    ("2608.28050", "Shows learning-to-defer reproduces algorithmic bias in the human it defers to; bias in the "
                   "deferred-to label is a property of the reviewer's decisions, and our construct separates "
                   "reviewer accuracy from the fidelity of the object reviewed."),
    ("2511.04855", "Predicts with an explicit reject option and communicates uncertainty; the reject option is "
                   "escalation with no cost model, and this study's value is affine in coverage with a term for "
                   "the mismatch escalation itself can introduce."),
    ("2506.21802", "Gives distribution-free error guarantees for classification with a reject option via conformal "
                   "prediction; the guarantee is about the abstention rate, not about the net value of the "
                   "escalated cases, which is what this study computes."),
    ("2503.23782", "Extends selective prediction to distributional regression with a reject option; abstention "
                   "is placed on a distributional target, and no channel between the reviewer and the executed "
                   "object appears."),
    ("2510.20242", "Asks what it takes to build a performant selective classifier; it measures abstention "
                   "performance, where this study measures the value of the human who receives the abstentions "
                   "and the fidelity of what they are shown."),
    ("2609.08934", "Audits whether models defer to a source-attributed cue and can be led to wrong answers; the "
                   "cue's provenance affects the model, which is the mirror image of our reviewer trusting an "
                   "unfaithful rendering."),
    ("2609.17977", "Gates a call to an LLM on confidence to control cost in emotion recognition; a confidence "
                   "gate trades accuracy against cost, and this study's gate trades harm against the harm an "
                   "unfaithful review can authorise."),
    ("2609.21942", "Decides when a failing robot should ask a human, given audited sensor evidence; asking is "
                   "escalation, and the reviewed evidence is assumed faithful there, which is the assumption "
                   "this study varies."),
    ("2609.17132", "Decides whether, when and how to assist a user from scenario knowledge and thresholds; the "
                   "decision is an intervention policy, and the object of the study is a gate whose input can "
                   "misrepresent the action."),
    ("2609.17708", "Estimates confidence from experience so that a system can defer reliably; calibration of a "
                   "self-report is a different object from the fidelity with which an approval denotes an "
                   "action, and this study varies the latter."),
    ("2606.29033", "Places a human in the loop for nugget annotation and asks how the human is incorporated; "
                   "incorporation design is a protocol choice, and the net value of the step is not derived "
                   "there."),

    # ---- E  the human's limits: fatigue, bias, warnings
    ("2609.02679", "Detects hallucination from complementary signals and frames false alarms as consuming "
                   "limited human review capacity; that framing is this study's false-block cost, which enters "
                   "its value law as an explicit term rather than as a motivation."),
    ("2608.16003", "Finds that a prior audit-repair context shifts an LLM verifier's threshold towards leniency; "
                   "drift in a checker's operating point is the reviewer-accuracy axis, which this study holds "
                   "fixed while varying fidelity, and the two are complementary."),
    ("2609.09038", "Asks whether reasoning representations help humans evaluate model outputs; human evaluation "
                   "quality is measured against a representation, which is a fidelity-like input evaluated for "
                   "helpfulness rather than priced in a decision."),
    ("2606.31748", "Reduces over-refusal in LLMs with competing rewards, i.e. the false-block side of a filter; "
                   "it optimises the rate, while this study asks when the harm from the other error makes a "
                   "gate net-negative."),
    ("2609.11763", "Shows deepfake detectors learn some attack families less well than others; uneven detection "
                   "across attack families is the same shape as a reviewer's effective sensitivity falling "
                   "below its nominal one."),
    ("2512.20293", "Builds a guard model for unsafe or adversarial behaviour; a guard classifier is a "
                   "programmatic reviewer, whose value under a defective channel is bounded by what it can see."),
    ("2402.18498", "Measures productivity and trust when people take, leave or fix human-AI collaboration "
                   "outputs; the human's disposition is measured directly, and this study instead fixes the "
                   "human and varies whether their information is faithful."),
    ("1911.08657", "Discusses complacency, comfort, relapse and distrust as side effects of automation in IoT; "
                   "these are the dispositions that make a gate's value collapse, named qualitatively."),
    ("2110.04880", "Reviews human factors of satellite operations and interaction technologies; the domain is "
                   "remote operation, and the treatment of the human is descriptive rather than priced."),
    ("2512.23738", "Enforces temporal constraints on LLM agents through guardrails; temporal safety is a "
                   "constraint on the action, and this study's subject is a human step that may or may not "
                   "have positive value under such a constraint."),

    ("2609.15576", "Audits approval integrity and recovery in one publication mechanism and reports a "
                   "production response-act checker accepting 291 of 302 unsupported-labelled answers; that is "
                   "one system's false-accept rate, where this study asks for the boundary at which the rate "
                   "stops mattering."),
    # ---- F  the cost of the gate
    ("2510.26091", "Prices execution assurance for data-centre workloads in a BFT setting; pricing assurance is "
                   "the closest economics to this study, but the priced resource is hardware-backed execution, "
                   "not a human decision with a mismatch channel."),
    ("2605.09104", "Studies token economics for LLM agents from computing and economics views; it prices token "
                   "consumption, and this study prices a human decision, whose harm term is absent there."),

    # ---- G  verifying the artifact
    ("2509.07757", "Analyses software-based fault isolation empirically through controlled fault injection; "
                   "isolation boundaries are enforcement mechanisms, and the object verified is code rather "
                   "than an artifact a human approved."),
    ("2508.15898", "Formally verifies a software fault isolation system, including its verifier; a verifier "
                   "proved correct is a different claim from a reviewer shown a faithful object."),
    ("2510.11837", "Layers several defences for LLM applications against prompt injection and related attacks; "
                   "layering reduces attack success, and this study asks whether the human layer pays."),
    ("2512.20860", "Detonates malware in an ephemeral containerized sandbox; containment bounds the blast "
                   "radius, which is an alternative to a gate rather than a value for one."),

    # ---- H  what a programmatic monitor can and cannot do
    ("2608.01388", "Bounds the recall of a fixed-invariant FSA monitor by the entropy of the attack "
                   "distribution; that is the adjacent monitor law for a programmatic detector, and no "
                   "analogous bound is published for a human gate, which is what this study supplies."),
    ("2606.29406", "Formulates delegation authority as a POMDP and solves for a policy under uncertainty; the "
                   "channel between delegate and delegator is assumed faithful there, and this study makes "
                   "that channel its variable."),
    ("2609.18820", "Shows step-scoped monitors cannot detect compositional violations however accurate they "
                   "are; the statement is that accuracy is not the axis for a monitor, and this study's "
                   "statement is that fidelity, not accuracy, is the axis for a human gate."),
]

DOI = [
    # ---- I  the classical spine: a human gate in deployment, the reviewer's own limits, and their instruments
    ("10.1093/med/9780190467654.003.0047", "Reports that a checklist and a human-checked protocol reduced "
     "catheter-related bloodstream infections; a human verification step with a measured field benefit, which "
     "this study turns into a value that depends on the fidelity of what the checker sees."),
    ("10.1148/radiology.143.1.7063747", "The meaning and use of the area under an ROC curve; the classical "
     "statement of what a reviewer's accuracy is, which this study holds fixed while varying the fidelity of the "
     "object reviewed."),
    ("10.1148/radiology.148.3.6878708", "Compares ROC areas estimated from the same cases with a paired "
     "procedure; the paired-comparison tradition this study's per-stream pairing follows."),
    ("10.1016/s0001-2998(78)80014-2", "Basic principles of ROC analysis; the reviewer's operating point as a "
     "curve, coupled here to a harm term so that an operating point becomes a value."),
    ("10.1126/science.182.4116.990", "The relative operating characteristic in psychology; the origin of the "
     "signal-detection reading of a human decision that this study imports into an approval gate."),
    ("10.1002/1097-0142(1950)3:1<32::aid-cncr2820030106>3.0.co;2-3", "Youden's index for rating diagnostic "
     "tests; a one-number summary of a detector's operating point, used here as a reviewer-accuracy summary "
     "rather than as a value."),
    ("10.1197/jamia.m1809", "Documents how often clinicians override drug-safety alerts and why; the reviewer "
     "disagreeing with the checker, measured in deployment rather than derived from a channel."),
    ("10.1001/archinte.163.21.2625", "Reports physicians' decisions to override computerised drug alerts in "
     "primary care; override behaviour is the human step's cost side, measured with no artifact-fidelity axis."),
    ("10.1001/archinte.163.12.1409", "Measures the effect of computerised order entry with decision support on "
     "adverse drug events; the outcome of adding a check, where this study asks when adding one is worth more "
     "than adding nothing."),
    ("10.1145/1357054.1357219", "Finds phishing warnings are often ignored; a warning that arrives unfaithfully "
     "or too often loses its force, which is the fatigue mechanism this study writes as an explicit cost term."),
    ("10.1145/2501604.2501610", "Designs security-decision interfaces so genuine risks are harder to ignore; the "
     "design improves the reviewer's attention, whereas this study varies whether the artifact is faithful at "
     "all."),
    ("10.1145/2702123.2702322", "Shows polymorphic warnings reduce habituation measured in the brain; habituation "
     "is the fatigue coupling this study names as the mechanism a registered interior optimum would require."),
    ("10.1145/2702123.2702442", "Improves SSL warnings for comprehension and adherence; comprehension is the "
     "reviewer-side property, while this study's channel property is whether the object reviewed is the object "
     "executed."),
    ("10.1007/978-3-642-23768-3_2", "Improves computer security dialogs; a dialog is the artifact a human reads, "
     "and this study prices the decision that dialog mediates."),
    ("10.2139/ssrn.2374379", "The psychology of malware warnings, including the cost of false positives to the "
     "user who receives them; that cost is this study's false-block term."),
    ("10.1145/1124772.1124861", "Explains why phishing works by defeating the user's judgement rather than the "
     "system's; the human is the deceived party, which this study formalises as an unfaithful review."),
    ("10.1145/1719030.1719050", "Argues users rationally reject security advice given its externalities; the "
     "rational-rejection argument is the reviewer's side of why a gate's cost can exceed its benefit."),
    ("10.1518/001872097778543886", "Humans' use, misuse, disuse and abuse of automation; the canonical typology "
     "of how a human step fails, cited for the dispositions rather than for a value."),
    ("10.1518/hfes.46.1.50.30392", "Trust in automation and designing for appropriate reliance; reliance is the "
     "reviewer's disposition toward a checker, whereas this study's failure lives in the artifact's fidelity."),
    ("10.1177/0018720810376055", "An attentional integration of complacency and bias in human use of automation; "
     "the mechanism by which a human stop becomes a rubber stamp."),
    ("10.1016/0005-1098(83)90046-8", "Ironies of automation: the operator left to supervise is least able to "
     "intervene; the founding statement of why a human gate can be worse than none, stated without a model."),
    ("10.1518/001872095779064555", "The out-of-the-loop performance problem and level of control in automation; "
     "the human's degraded state, held fixed here so that the channel can be varied alone."),
    ("10.3389/frobt.2018.00015", "A philosophical account of meaningful human control over autonomous systems; a "
     "criterion for when control is meaningful, which this study replaces with a quantity that can be computed."),
    ("10.4337/9781800887305.00010", "Moral crumple zones: humans absorb blame for systems they cannot "
     "meaningfully control; the accountability reading of the same failure this study prices."),
    ("10.1145/302979.303030", "Principles of mixed-initiative user interfaces: when a system should ask the "
     "user, which is this study's escalation decision with a cost model attached."),
    ("10.1007/s40708-016-0042-6", "Argues interactive machine learning needs a human in the loop for health "
     "informatics; the case for the human is capability-based, and no channel between reviewer and object is "
     "modelled."),
    ("10.54660/.jfmr.2022.3.1.656-669", "Surveys human-in-the-loop machine learning as a field; a taxonomy of "
     "where the human acts, with the value of the human step itself not a quantity in the survey."),
    ("10.1370/afm.1466", "Long-term psychosocial consequences of false-positive screening mammography; the harm "
     "of a false positive measured in the field, which is why this study carries a false-block term rather than "
     "treating the gate as free."),
    ("10.1136/bmj.299.6698.527", "The psychological costs of screening; screening harms borne by those screened, "
     "the empirical backing for pricing the gate's own errors."),
    ("10.1109/icse.2013.6606617", "Reports expectations, outcomes and challenges of modern code review in "
     "industry; a deployed human review step studied as a practice, without a value for the step."),
    ("10.1109/msr.2015.21", "Measures what makes a code review useful; usefulness is judged by the reviewed "
     "person rather than derived from whether the reviewer's object denoted the change."),
    ("10.1145/3183519.3183525", "Describes modern code review as practised at Google, including reviewer "
     "assignment and tooling; a large deployed review process whose benefit is reported as practice."),

    # ---- J  the economics of oversight, and the authorization artifact
    ("10.1016/0304-3932(86)90074-7", "Costly monitoring and equilibrium credit rationing; monitoring is costly "
     "and worth only the difference it makes, the economic structure this study instantiates with a fidelity "
     "parameter."),
    ("10.2307/3003320", "Moral hazard and observability: effort is unobservable and the contract prices what can "
     "be seen; the reason an unfaithful observation is worth less than a faithful one."),
    ("10.21034/sr.45", "Optimal contracts with costly state verification; verification is itself costly and is "
     "used only when it pays, which is the decision rule this study derives for a human gate."),
    ("10.1007/978-1-349-62853-7_2", "Crime and punishment: an economic approach; enforcement is priced against "
     "the harm it deters, the framing this study applies to a single approval decision."),
    ("10.3386/w6993", "The economic theory of public enforcement of law; enforcement intensity against the harm "
     "avoided, a policy-level analogue of this study's per-decision value."),
    ("10.2139/ssrn.94043", "Theory of the firm, agency costs and ownership structure; the principal-agent "
     "structure in which a check on an agent's action is priced."),
    ("10.1080/21670811.2014.976411", "Investigates algorithmic accountability journalistically; accountability "
     "as a practice, cited for the governance context in which approval gates are justified."),
    ("10.1177/2053951716679679", "Maps the ethics debate around algorithms; the normative frame in which a human "
     "gate is usually argued for, and which this study asks to be traded against its cost."),
    ("10.1145/357980.357993", "Programming semantics for multiprogrammed computations, including the capability "
     "model; the origin of capability-based authorization, which is the b = 1 end of this study's axis."),
    ("10.1145/54289.871709", "The confused deputy: an authorized party can be induced to misuse its authority; "
     "the canonical statement that authority flows through the artifact, not through intent."),
    ("10.1145/362375.362389", "A note on the confinement problem; confinement of what a program may affect, the "
     "boundary an approval gate is placed on."),
    ("10.1145/1283920.1283940", "Reflections on trusting trust: trust in a chain is trust in whatever wrote it; "
     "the reason an approval artifact's provenance matters independently of its content."),
    ("10.6028/nist.sp.800-207-draft", "Zero trust architecture: no implicit trust from network position; the "
     "architectural claim that every step must be verified, whose value this study asks about."),
    ("10.1002/9781119644682", "Security engineering as a discipline of building dependable systems; the "
     "reference for the engineering frame in which an approval step is one control among several."),
]

# NOT SELECTED -- a work the harvest returned and this study CONSIDERED and refused, with the reason.  It is a
# separate table because the distinction has to be a FIELD, not a sentence: R416 wrote the refusal INTO the
# difference line of a row that sat in `ARXIV`, and R424 found that the build takes every row of a selection
# table as selected, so the refusal was carried by prose the pipeline never read and the work entered the
# bibliography -- where the submission bar ("every entry genuinely cited") would have forced a citation to a
# robotics packing paper.  `refs_build_v93.py` now refuses a not-selected id in a selected table, refuses a
# selected id here, and `refs_check3.py` reads both properties two-sided; a `difference` line may not carry its
# own exclusion again (that scan is C3 there).
NOT_SELECTED = [
    ("2609.22062", "Gripper-Aware Automatic Dense Packing of Irregular Objects (cs.RO).  Returned by the W3 "
                   "'monitorability' keyword window and unrelated to this study: it plans robot grasps, and no "
                   "reviewer, artifact or gate appears in it.  Retained here so the register of considered works "
                   "stays complete, never in the bibliography."),
]
