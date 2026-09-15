#!/usr/bin/env python3
"""Build the issue #42 bibliography with HARD title verification.

Protocol (rant 2026-09-10T11:28:43):
  DOI            -> Crossref  https://api.crossref.org/works/<doi>
  arXiv-only     -> DataCite  https://api.datacite.org/dois/10.48550/arXiv.<id>
A fetch returning HTTP 200 is NOT verification: the record's TITLE must match the
title the manuscript claims.  Three candidates resolved to a different paper while
returning 200 (2001.08049 -> "On Last-Layer Algorithms", ...), which is exactly why
title matching is the gate and reachability is not.
"""
import io, json, os, re, time, urllib.request, urllib.parse

UA = {"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}
CACHE = "refcache.json"
cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def title_match(claimed, actual):
    a, b = norm(claimed), norm(actual)
    if len(a) < 12 or len(b) < 12:
        return False
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    return short[:72] in long


def fetch(kind, ident):
    ck = kind + ":" + ident
    if ck in cache:
        return cache[ck]
    try:
        if kind == "doi":
            url = "https://api.crossref.org/works/" + urllib.parse.quote(ident)
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                m = json.loads(r.read().decode("utf-8", "replace"))["message"]
            rec = {"ok": True, "title": (m.get("title") or [""])[0],
                   "year": (m.get("issued", {}).get("date-parts", [[None]])[0] or [None])[0],
                   "authors": [(("%s %s" % (a.get("given", ""), a.get("family", ""))).strip())
                               for a in (m.get("author") or [])],
                   "venue": (m.get("container-title") or [""])[0],
                   "doi": m.get("DOI"), "registry": "Crossref"}
        else:
            url = "https://api.datacite.org/dois/10.48550/arXiv." + ident
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                a = json.loads(r.read().decode("utf-8", "replace"))["data"]["attributes"]
            rec = {"ok": True, "title": a["titles"][0]["title"], "year": a.get("publicationYear"),
                   "authors": [c.get("name", "") for c in (a.get("creators") or [])],
                   "venue": "arXiv preprint", "doi": "10.48550/arXiv." + ident,
                   "registry": "DataCite"}
    except Exception as e:
        rec = {"ok": False, "err": "%s:%s" % (type(e).__name__, str(e)[:38])}
    cache[ck] = rec
    time.sleep(1.0)
    return rec


# (key, kind, ident, claimed title, topic-group)
WANT = [
 # ---- foundations: reject option / selective prediction / deferral ----
 ("chow1970reject","doi","10.1109/TIT.1970.1054406","On optimum recognition error and reject tradeoff","deferral"),
 ("fawcett2006roc","doi","10.1016/j.patrec.2005.10.010","An introduction to ROC analysis","deferral"),
 ("selectivegeifman2017","arxiv","1705.08500","Selective Classification for Deep Neural Networks","deferral"),
 ("selectivenet2019","arxiv","1901.09192","SelectiveNet: A Deep Neural Network with an Integrated Reject Option","deferral"),
 ("jiang2018trust","arxiv","1805.11783","To Trust Or Not To Trust A Classifier","deferral"),
 ("mozannar2020defer","arxiv","2006.01862","Consistent Estimators for Learning to Defer to an Expert","deferral"),
 ("unbiaseddeferral2021","arxiv","2102.13004","Towards Unbiased and Accurate Deferral to Multiple Experts","deferral"),
 ("triage2021","arxiv","2103.08902","Differentiable Learning Under Triage","deferral"),
 ("uncertaintydefer2021","arxiv","2108.07392","Incorporating Uncertainty in Learning to Defer Algorithms","deferral"),
 ("seqdefer2021","arxiv","2109.06312","Learning-to-defer for sequential medical decision-making under uncertainty","deferral"),
 ("exemplars2021","arxiv","2111.11297","Teaching Humans When To Defer to a Classifier via Exemplars","deferral"),
 ("calibrateddefer2022","arxiv","2202.03673","Calibrated Learning to Defer with One-vs-All Classifiers","deferral"),
 ("closedloop2022","arxiv","2202.04718","Designing Closed Human-in-the-loop Deferral Pipelines","deferral"),
 ("complement2022","arxiv","2206.07948","Forming Effective Human-AI Teams: Building Machine Learning Models that Complement","deferral"),
 ("sampleefficient2022","arxiv","2207.09584","Sample Efficient Learning of Predictors that Complement Humans","deferral"),
 ("limitedexpert2023","arxiv","2304.07306","Learning to Defer with Limited Expert Predictions","deferral"),
 ("guideexperts2023","arxiv","2308.06039","Learning to Guide Human Experts via Personalized Large Language Models","deferral"),
 ("fifar2023","arxiv","2312.13218","FiFAR: A Fraud Detection Dataset for Learning to Defer","deferral"),
 ("a2c2024","arxiv","2401.14432","A2C: A Modular Multi-stage Collaborative Decision Framework for Human-AI Teams","deferral"),
 ("deferpopulation2024","arxiv","2403.02683","Learning to Defer to a Population: A Meta-Learning Approach","deferral"),
 ("workload2024","arxiv","2403.06906","Cost-Sensitive Learning to Defer to Multiple Experts with Workload Constraints","deferral"),
 ("causaldefer2024","arxiv","2405.18902","A Causal Framework for Evaluating Deferring Systems","deferral"),
 ("multidefer2024","arxiv","2407.12710","A Unifying Post-Processing Framework for Multi-Objective Learn-to-Defer","deferral"),
 ("coverage2024","arxiv","2411.11976","Coverage-Constrained Human-AI Cooperation with Multiple Experts","deferral"),
 ("partialdefer2025","arxiv","2502.01459","Learning to Partially Defer for Sequences","deferral"),
 ("identityfree2025","arxiv","2502.10533","Identity-Free Deferral For Unseen Experts","deferral"),
 ("abstainrank2025","arxiv","2505.23437","Bounded-Abstention Pairwise Learning to Rank","deferral"),
 ("socdefer2025","arxiv","2506.18462","Adaptive alert prioritisation in security operations centres via learning to defer","deferral"),
 ("failfast2025","arxiv","2507.14406","Fail Fast, or Ask: Mitigating the Deficiencies of Reasoning LLMs with Human-in-the-Loop","deferral"),
 ("uqvsdefer2025","arxiv","2508.02319","Is Uncertainty Quantification a Viable Alternative to Learned Deferral?","deferral"),
 ("nodefer2025","arxiv","2509.12573","No Need for Learning to Defer? A Training Free Deferral Framework","deferral"),
 ("knowdefer2025","arxiv","2509.21514","Knowing When to Defer: Selective Prediction for Responsible Knowledge Tracing","deferral"),
 ("ask2025","arxiv","2510.08314","To Ask or Not to Ask: Learning to Require Human Feedback","deferral"),
 ("popdemos2025","arxiv","2510.19351","Learning To Defer To A Population With Limited Demonstrations","deferral"),
 ("fatigue2026","arxiv","2604.00904","Fatigue-Aware Learning to Defer via Constrained Optimisation","deferral"),
 ("deferredseg2026","arxiv","2604.12411","DeferredSeg: A Multi-Expert Deferral Framework for Medical Image Segmentation","deferral"),
 ("l2dclinical2026","arxiv","2604.13285","L2D-Clinical: Learning to Defer for Adaptive Model Selection","deferral"),
 ("faircoop2026","arxiv","2604.26991","People-Centred Medical Image Analysis via Fairness-Aware Human-AI Cooperation","deferral"),
 ("abstainfair2023","arxiv","2310.06205","Fair Classifiers that Abstain without Harm","deferral"),
 ("vqaabstain2022","arxiv","2204.13631","Reliable Visual Question Answering: Abstain Rather Than Answer Incorrectly","deferral"),
 ("querycontrol2025","arxiv","2512.00453","Sample-Efficient Expert Query Control in Active Imitation Learning via Conformal Prediction","deferral"),
 # ---- ensembles, diversity, correlated errors ----
 ("breiman1996bagging","doi","10.1007/BF00058655","Bagging predictors","ensemble"),
 ("breiman2001forests","doi","10.1023/A:1010933404324","Random Forests","ensemble"),
 ("freund1997boosting","doi","10.1006/jcss.1997.1504","A Decision-Theoretic Generalization of On-Line Learning","ensemble"),
 ("dietterich2000ensemble","doi","10.1007/3-540-45014-9_1","Ensemble Methods in Machine Learning","ensemble"),
 ("kuncheva2003diversity","doi","10.1023/A:1022859003006","Measures of Diversity in Classifier Ensembles","ensemble"),
 ("wolpert1992stacked","doi","10.1016/s0893-6080(05)80023-1","Stacked generalization","ensemble"),
 ("hinton1999product","doi","10.1049/cp:19991075","Products of experts","ensemble"),
 ("deepensembles2016","arxiv","1612.01474","Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles","ensemble"),
 ("deceptionensembles2019","arxiv","1908.11091","Deep Neural Network Ensembles against Deception","ensemble"),
 ("negcorr2020","arxiv","2011.02952","Generalized Negative Correlation Learning for Deep Ensembling","ensemble"),
 ("dexdeepfm2021","arxiv","2104.01924","DexDeepFM: Ensemble Diversity Enhanced Extreme Deep Factorization Machine","ensemble"),
 ("gnnensembles2023","arxiv","2305.16325","Graph Neural Network Interatomic Potential Ensembles","ensemble"),
 ("ltauf2024","arxiv","2402.00853","LTAU-FF: Loss Trajectory Analysis for Uncertainty in Atomistic Force Fields","ensemble"),
 ("heteroens2025","arxiv","2507.21297","Heterogeneous Ensemble Enables a Universal Uncertainty Metric","ensemble"),
 ("rashomon2025","arxiv","2511.19636","Exploring the Rashomon Set for Concept-Based Models","ensemble"),
 # ---- verification layers, critics, judges, cascades ----
 ("vaswani2017attention","arxiv","1706.03762","Attention Is All You Need","verify"),
 ("wei2022cot","arxiv","2201.11903","Chain-of-Thought Prompting Elicits Reasoning in Large Language Models","verify"),
 ("wang2023selfconsistency","arxiv","2203.11171","Self-Consistency Improves Chain of Thought Reasoning in Language Models","verify"),
 ("lightman2023verify","arxiv","2305.20050","Let's Verify Step by Step","verify"),
 ("bai2022constitutional","arxiv","2212.08073","Constitutional AI: Harmlessness from AI Feedback","verify"),
 ("madaan2023selfrefine","arxiv","2303.17651","Self-Refine: Iterative Refinement with Self-Feedback","verify"),
 ("shinn2023reflexion","arxiv","2303.11366","Reflexion: Language Agents with Verbal Reinforcement Learning","verify"),
 ("zheng2023judge","arxiv","2306.05685","Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena","verify"),
 ("yao2023tree","arxiv","2305.10601","Tree of Thoughts: Deliberate Problem Solving","verify"),
 ("yao2022react","arxiv","2210.03629","ReAct: Synergizing Reasoning and Acting in Language Models","verify"),
 ("cobbe2021verifiers","arxiv","2110.14168","Training Verifiers to Solve Math Word Problems","verify"),
 ("huang2023selfcorrect","arxiv","2310.01798","Large Language Models Cannot Self-Correct Reasoning Yet","verify"),
 ("opv2025","arxiv","2512.10756","OPV: Outcome-based Process Verifier for Efficient Long Chain-of-Thought Verification","verify"),
 ("vlgenrm2025","arxiv","2506.13888","VL-GenRM: Enhancing Vision-Language Verification via Vision Experts","verify"),
 ("neuroformal2026","arxiv","2603.13414","Neuro-Symbolic Generation and Validation of Memory-Aware Formal Function Specifications","verify"),
 ("uqsurvey2023","arxiv","2304.04906","Survey on Leveraging Uncertainty Estimation Towards Trustworthy Deep Neural Networks","verify"),
 ("liu2023lostmiddle","arxiv","2307.03172","Lost in the Middle: How Language Models Use Long Contexts","verify"),
 ("confidadptive2022","doi","10.52202/068431-1269","Confident Adaptive Language Modeling","verify"),
 ("branchynet2016","doi","10.1109/icpr.2016.7900006","BranchyNet: Fast inference via early exiting from deep neural networks","verify"),
 ("viola2001cascade","doi","10.1109/CVPR.2001.990517","Rapid Object Detection using a Boosted Cascade","verify"),
 ("shazeer2017moe","arxiv","1701.06538","Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer","verify"),
 ("jacobs1991mixture","doi","10.1162/neco.1991.3.1.79","Adaptive Mixtures of Local Experts","verify"),
 # ---- human oversight, automation bias, AI-assisted SE ----
 ("bacchelli2013codereview","doi","10.1109/ICSE.2013.6606617","Expectations, outcomes, and challenges of modern code review","oversight"),
 ("sadowski2018googlereview","doi","10.1145/3183519.3183525","Modern code review","oversight"),
 ("peng2023copilot","arxiv","2302.06590","The Impact of AI on Developer Productivity: Evidence from GitHub Copilot","oversight"),
 ("dietvorst2015aversion","doi","10.1037/xge0000033","Algorithm aversion: People erroneously avoid algorithms after seeing them err","oversight"),
 ("parasuraman1997automationbias","doi","10.1518/001872097778543886","Humans and Automation: Use, Misuse, Disuse, Abuse","oversight"),
 ("bainbridge1983ironies","doi","10.1016/0005-1098(83)90046-8","Ironies of automation","oversight"),
 ("leesee2004trust","doi","10.1518/hfes.46.1.50_30392","Trust in Automation: Designing for Appropriate Reliance","oversight"),
 ("psychmachines2026","arxiv","2601.06172","The Psychology of Learning from Machines: Anthropomorphic AI and the Paradox of Automation","oversight"),
 ("reviewerconfidence2025","arxiv","2505.15031","Are the confidence scores of reviewers consistent with the review content?","oversight"),
 ("chilgrader2026","arxiv","2603.11957","CHiL(L)Grader: Calibrated Human-in-the-Loop Short-Answer Grading","oversight"),
 ("metacog2026","arxiv","2603.07972","Adaptive Collaboration with Humans: Metacognitive Policy Optimization","oversight"),
 ("causalperception2024","arxiv","2401.13408","Toward A Causal Framework for Modeling Perception","oversight"),
 ("unequalunc2025","arxiv","2508.07872","Unequal Uncertainty: Rethinking Algorithmic Interventions","oversight"),
 ("oodunc2024","arxiv","2403.10642","Using Uncertainty Quantification to Characterize and Improve Out-of-Domain Learning","oversight"),
 # ---- redundancy, fault tolerance, replication ----
 ("knight1986nversion","doi","10.1109/TSE.1986.6312924","An experimental evaluation of the assumption of independence in multiversion programming","faulttolerance"),
 ("avizienis1985nversion","doi","10.1109/tse.1985.231893","The N-Version Approach to Fault-Tolerant Software","faulttolerance"),
 ("randell1975faulttolerance","doi","10.1145/800027.808467","System structure for software fault tolerance","faulttolerance"),
 ("littlewood1989coincident","doi","10.1109/32.58771","Conceptual modeling of coincident failures in multiversion software","faulttolerance"),
 ("eckhardt1985coincident","doi","10.1109/tse.1985.231895","A Theoretical Basis for the Analysis of Multiversion Software Subject to Coincident Errors","faulttolerance"),
 ("lyons1962tmr","doi","10.1147/rd.62.0200","The Use of Triple-Modular Redundancy to Improve Computer Reliability","faulttolerance"),
 ("recoveryblocks1985","doi","10.1007/978-3-642-82470-8_9","Recovery Blocks in Action: A System Supporting High Reliability","faulttolerance"),
 ("lamport1982byzantine","doi","10.1145/357172.357176","The Byzantine Generals Problem","faulttolerance"),
 ("castro1999pbft","doi","10.1145/571637.571640","Practical byzantine fault tolerance and proactive recovery","faulttolerance"),
 # ---- decision theory, metareasoning, statistics ----
 ("russell1991metareasoning","doi","10.1016/0004-3702(91)90015-c","Principles of metareasoning","decision"),
 ("howard1966valueinfo","doi","10.1109/tssc.1966.300074","Information Value Theory","decision"),
 ("efron1979bootstrap","doi","10.1214/aos/1176344552","Bootstrap Methods: Another Look at the Jackknife","decision"),
 ("wilson1927probable","doi","10.1080/01621459.1927.10502953","Probable Inference, the Law of Succession, and Statistical Inference","decision"),
 ("benjamini1995fdr","doi","10.1111/j.2517-6161.1995.tb02031.x","Controlling the False Discovery Rate","decision"),
 ("lecun2015deeplearning","doi","10.1038/nature14539","Deep learning","decision"),
 # ---- the calibrated systems (external anchors) ----
 ("layered2026","arxiv","2608.26316","When Review Alone No Longer Scales: Layered Supervision in AI-Assisted Software Engineering","calibrated"),
 ("cerberus2026","arxiv","2605.02220","Cerberus: Cross-Layer ECC Co-Design for Robust and Efficient Memory Protection","calibrated"),
 ("bmc2026","arxiv","2605.21434","","calibrated"),
 ("helios2026","arxiv","2607.24051","HELIOS: An LLM-Driven Autonomous Indirect Trajectory Optimization Agent","calibrated"),
 ("specgen2026","arxiv","2608.13077","How Powerful are LLMs in Generating Formal Program Specifications","calibrated"),
 ("ltd2026","arxiv","2608.28050","Too Much of the Same: From Algorithmic to Human Bias in Learning to Defer","calibrated"),
 ("flowbyflow2026","arxiv","2608.07474","Flow-by-Flow: Content-Judgment Bypass for Governing AI Output in High-Loss Domains","calibrated"),
 ("aniso2026","arxiv","2604.05077","Feature-Aware Anisotropic Local Differential Privacy","calibrated"),
 ("mllmunc2026","arxiv","2608.17084","Uncertainty-Aware Decision Making in Multimodal Large Language Models","calibrated"),
 ("feat2025","arxiv","2508.07950","FEAT: A Multi-Agent Forensic AI System","calibrated"),
]

out, bad = [], []
for key, kind, ident, claimed, topic in WANT:
    r = fetch(kind, ident)
    rec = dict(r, key=key, kind=kind, ident=ident, claimed=claimed, topic=topic)
    if not r.get("ok"):
        rec["verdict"] = "unreachable"
        bad.append(key)
    elif claimed and not title_match(claimed, r.get("title", "")):
        rec["verdict"] = "TITLE-MISMATCH"
        bad.append(key)
    else:
        rec["verdict"] = "verified"
    out.append(rec)

json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), indent=1)
json.dump(out, io.open("refs_final.json", "w", encoding="utf-8"), indent=1)
v = sum(1 for r in out if r["verdict"] == "verified")
print("total %d  verified %d  problems %d" % (len(out), v, len(bad)))
if bad:
    print("PROBLEMS:")
    for r in out:
        if r["verdict"] != "verified":
            print("  %-22s %-14s %s  <- %s" % (r["key"], r["verdict"], r["ident"], (r.get("title") or r.get("err"))[:64]))
by = {}
for r in out:
    by[r["topic"]] = by.get(r["topic"], 0) + 1
print("by topic:", by)
