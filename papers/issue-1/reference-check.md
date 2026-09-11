# Citation report - issue #1

Companion to `manuscript.md`. Two duties: (i) authenticity of every reference, and (ii) coverage and
ambiguity of the in-text citation keys. This report is a declaration; reviewers verify independently.

## (i) Authenticity - how each entry was verified

**Method.** Every entry is verified by re-fetching it **by its own identifier** and comparing the returned
title against the title recorded in the selection, after normalisation (case, punctuation and whitespace
folded). The tool is committed and re-runnable:

```
python3 refs_tool.py verify        # from papers/issue-1/
```

- **DOI entries** are fetched from `https://api.crossref.org/works/<doi>` (Crossref).
- **arXiv entries** are fetched from `https://export.arxiv.org/api/query?id_list=<id>` (arXiv API, https).
- Curation used Crossref *bibliographic* search only to discover candidates, never as an authority: that
  endpoint returns heavy noise (duplicate same-title rows, and non-existent venues attached to real titles),
  so DOI-less entries are taken from arXiv and every Crossref entry is a fixed, authoritative DOI.

**Result: 115/115 entries resolved to their recorded title, 0 unresolved.** Run log: `refs_verify.log`
(`verified 115/115, entries=115, problems=0`). The verification command exits non-zero if any entry fails,
so this is a check rather than a statement.

**Three independent spot-checks were performed outside the tool** (plain `curl`, not via `refs_tool.py`):

| key | identifier | fetched title | verdict |
|---|---|---|---|
| 105 | arXiv:2502.02737 (DOI-less) | SmolLM2: When Smol Goes Big -- Data-Centric Training of a Small Language Model | matches |
| 110 | 10.1561/1500000019 | The Probabilistic Relevance Framework: BM25 and Beyond | matches |
| 114 | 10.1017/cbo9780511844744.008 | Instructional Control of Cognitive Load in the Design of Complex Learning Environments | matches |

**Duplicate works were removed.** Three entries in an earlier build were the published (ACL/EMNLP) versions
of works already listed from arXiv - BERT, Sentence-BERT and Dense Passage Retrieval. Listing the same work
twice would inflate the count with a duplicate rather than a distinct reference, so the arXiv records were
kept and the duplicates deleted; the selection was then renumbered 1..115 and re-verified in full.

## Per-entry record

One line per entry: key, verification method, resolved identifier, and the resolved title.

- **[1]** - arXiv id_list lookup - `arXiv:2307.03172` - resolved: *Lost in the Middle: How Language Models Use Long Contexts* - status **exact**
- **[2]** - arXiv id_list lookup - `arXiv:2407.01100` - resolved: *Eliminating Position Bias of Language Models: A Mechanistic Approach* - status **exact**
- **[3]** - arXiv id_list lookup - `arXiv:2406.02536` - resolved: *Mitigate Position Bias in Large Language Models via Scaling a Single Dimension* - status **exact**
- **[4]** - arXiv id_list lookup - `arXiv:2603.10123` - resolved: *Lost in the Middle at Birth: An Exact Theory of Transformer Position Bias* - status **exact**
- **[5]** - arXiv id_list lookup - `arXiv:2605.09213` - resolved: *Kinetic theory for Transformers and the lost-in-the-middle phenomenon* - status **exact**
- **[6]** - arXiv id_list lookup - `arXiv:2607.17696` - resolved: *An Adjoint-Sensitivity Framework for Lost-in-the-Middle Phenomena in Causal Residual Transformers* - status **exact**
- **[7]** - arXiv id_list lookup - `arXiv:2510.10276` - resolved: *Lost in the Middle: An Emergent Property from Information Retrieval Demands in LLMs* - status **exact**
- **[8]** - arXiv id_list lookup - `arXiv:2503.06868` - resolved: *Lost-in-the-Middle in Long-Text Generation: Synthetic Dataset, Evaluation Framework, and Mitigation* - status **exact**
- **[9]** - arXiv id_list lookup - `arXiv:2412.10079` - resolved: *Lost in the Middle, and In-Between: Enhancing Language Models' Ability to Reason Over Long Contexts in Multi-Hop QA* - status **exact**
- **[10]** - arXiv id_list lookup - `arXiv:2508.02020` - resolved: *Evaluating Position Bias in Large Language Model Recommendations* - status **exact**
- **[11]** - arXiv id_list lookup - `arXiv:2606.27793` - resolved: *Position Bias Correction is Insufficient for One-Pass Attention Sorting* - status **exact**
- **[12]** - arXiv id_list lookup - `arXiv:2608.20348` - resolved: *Inhibitory Attention for Clinical Long-Context Reasoning: Characterizing and Mitigating Lost-in-the-Middle Effects in EHR Processing* - status **exact**
- **[13]** - arXiv id_list lookup - `arXiv:2603.22608` - resolved: *Understanding LLM Performance Degradation in Multi-Instance Processing: The Roles of Instance Count and Context Length* - status **exact**
- **[14]** - arXiv id_list lookup - `arXiv:2402.14848` - resolved: *Same Task, More Tokens: the Impact of Input Length on the Reasoning Performance of Large Language Models* - status **exact**
- **[15]** - arXiv id_list lookup - `arXiv:2608.03297` - resolved: *Distractor-Aware Truncation: Disentangling Context-Length Effects from Signal Loss in Long-Context LLM Benchmarks* - status **exact**
- **[16]** - arXiv id_list lookup - `arXiv:2506.02921` - resolved: *A Controllable Examination for Long-Context Language Models* - status **exact**
- **[17]** - arXiv id_list lookup - `arXiv:2410.04422` - resolved: *Long-context Language Models Fail in Basic Retrieval Tasks Without Sufficient Reasoning Steps* - status **exact**
- **[18]** - arXiv id_list lookup - `arXiv:2308.14508` - resolved: *LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding* - status **exact**
- **[19]** - arXiv id_list lookup - `arXiv:2309.13345` - resolved: *BAMBOO: A Comprehensive Benchmark for Evaluating Long Text Modeling Capacities of Large Language Models* - status **exact**
- **[20]** - arXiv id_list lookup - `arXiv:2410.04199` - resolved: *LongGenBench: Long-context Generation Benchmark* - status **exact**
- **[21]** - arXiv id_list lookup - `arXiv:2406.06025` - resolved: *RepoQA: Evaluating Long Context Code Understanding* - status **exact**
- **[22]** - arXiv id_list lookup - `arXiv:2510.17725` - resolved: *AcademicEval: Live Long-Context LLM Benchmark* - status **exact**
- **[23]** - arXiv id_list lookup - `arXiv:2602.14200` - resolved: *TS-Haystack: A Multi-Task Retrieval Benchmark for Long-Context Time-Series Reasoning* - status **exact**
- **[24]** - arXiv id_list lookup - `arXiv:2503.00353` - resolved: *U-NIAH: Unified RAG and LLM Evaluation for Long Context Needle-In-A-Haystack* - status **exact**
- **[25]** - arXiv id_list lookup - `arXiv:2502.05167` - resolved: *NoLiMa: Long-Context Evaluation Beyond Literal Matching* - status **exact**
- **[26]** - arXiv id_list lookup - `arXiv:2406.11230` - resolved: *Multimodal Needle in a Haystack: Benchmarking Long-Context Capability of Multimodal Large Language Models* - status **exact**
- **[27]** - arXiv id_list lookup - `arXiv:2504.04150` - resolved: *Reasoning on Multiple Needles In A Haystack* - status **exact**
- **[28]** - arXiv id_list lookup - `arXiv:2407.01437` - resolved: *Needle in the Haystack for Memory Based Large Language Models* - status **exact**
- **[29]** - arXiv id_list lookup - `arXiv:2408.10151` - resolved: *Multilingual Needle in a Haystack: Investigating Long-Context Behavior of Multilingual Large Language Models* - status **exact**
- **[30]** - arXiv id_list lookup - `arXiv:2505.10570` - resolved: *LongFuncEval: Measuring the effectiveness of long context models for function calling* - status **exact**
- **[31]** - arXiv id_list lookup - `arXiv:2505.21439` - resolved: *Towards Better Instruction Following Retrieval Models* - status **exact**
- **[32]** - arXiv id_list lookup - `arXiv:2302.00093` - resolved: *Large Language Models Can Be Easily Distracted by Irrelevant Context* - status **exact**
- **[33]** - arXiv id_list lookup - `arXiv:2505.18761` - resolved: *How Is LLM Reasoning Distracted by Irrelevant Context? An Analysis Using a Controlled Benchmark* - status **exact**
- **[34]** - arXiv id_list lookup - `arXiv:2310.01558` - resolved: *Making Retrieval-Augmented Language Models Robust to Irrelevant Context* - status **exact**
- **[35]** - arXiv id_list lookup - `arXiv:2505.22630` - resolved: *Stochastic Chameleons: Irrelevant Context Hallucinations Reveal Class-Based (Mis)Generalization in LLMs* - status **exact**
- **[36]** - arXiv id_list lookup - `arXiv:2604.01161` - resolved: *Reasoning Shift: How Context Silently Shortens LLM Reasoning* - status **exact**
- **[37]** - arXiv id_list lookup - `arXiv:2512.14313` - resolved: *Dynamic Context Selection for Retrieval-Augmented Generation: Mitigating Distractors and Positional Bias* - status **exact**
- **[38]** - arXiv id_list lookup - `arXiv:2602.02983` - resolved: *Do LLMs Share Human-Like Biases? Causal Reasoning Under Prior Knowledge, Irrelevant Context, and Varying Compute Budgets* - status **exact**
- **[39]** - arXiv id_list lookup - `arXiv:2509.21865` - resolved: *Beyond RAG vs. Long-Context: Learning Distraction-Aware Retrieval for Efficient Knowledge Grounding* - status **exact**
- **[40]** - arXiv id_list lookup - `arXiv:2605.18760` - resolved: *DOTRAG: Retrieval-Time Reasoning Along Paths* - status **exact**
- **[41]** - arXiv id_list lookup - `arXiv:2504.02111` - resolved: *Exploring LLM Reasoning Through Controlled Prompt Variations* - status **exact**
- **[42]** - arXiv id_list lookup - `arXiv:2407.16695` - resolved: *Stress-Testing Long-Context Language Models with Lifelong ICL and Task Haystack* - status **exact**
- **[43]** - arXiv id_list lookup - `arXiv:2407.16833` - resolved: *Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study and Hybrid Approach* - status **exact**
- **[44]** - arXiv id_list lookup - `arXiv:2410.04343` - resolved: *Inference Scaling for Long-Context Retrieval Augmented Generation* - status **exact**
- **[45]** - arXiv id_list lookup - `arXiv:2506.03989` - resolved: *Stronger Baselines for Retrieval-Augmented Generation with Long-Context Language Models* - status **exact**
- **[46]** - arXiv id_list lookup - `arXiv:2406.13121` - resolved: *Can Long-Context Language Models Subsume Retrieval, RAG, SQL, and More?* - status **exact**
- **[47]** - arXiv id_list lookup - `arXiv:2607.26497` - resolved: *BM25 Wins at Scale: A Scaling Study of Retrieval-Augmented Generation Paradigms* - status **exact**
- **[48]** - arXiv id_list lookup - `arXiv:2512.17220` - resolved: *Mindscape-Aware Retrieval Augmented Generation for Improved Long Context Understanding* - status **exact**
- **[49]** - arXiv id_list lookup - `arXiv:2607.24767` - resolved: *The Effect of Text Chunk Size on Retrieval-Augmented Generation Performance* - status **exact**
- **[50]** - arXiv id_list lookup - `arXiv:2607.01852` - resolved: *Evaluating Chunking Strategies for Retrieval-Augmented Generation on Academic Texts* - status **exact**
- **[51]** - arXiv id_list lookup - `arXiv:2504.19754` - resolved: *Reconstructing Context: Evaluating Advanced Chunking Strategies for Retrieval-Augmented Generation* - status **exact**
- **[52]** - arXiv id_list lookup - `arXiv:2602.16974` - resolved: *Beyond Chunk-Then-Embed: A Comprehensive Taxonomy and Evaluation of Document Chunking Strategies for Information Retrieval* - status **exact**
- **[53]** - arXiv id_list lookup - `arXiv:1706.03762` - resolved: *Attention Is All You Need* - status **exact**
- **[54]** - arXiv id_list lookup - `arXiv:1810.04805` - resolved: *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding* - status **exact**
- **[55]** - arXiv id_list lookup - `arXiv:2005.11401` - resolved: *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* - status **exact**
- **[56]** - arXiv id_list lookup - `arXiv:2004.04906` - resolved: *Dense Passage Retrieval for Open-Domain Question Answering* - status **exact**
- **[57]** - arXiv id_list lookup - `arXiv:1908.10084` - resolved: *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks* - status **exact**
- **[58]** - arXiv id_list lookup - `arXiv:2104.08663` - resolved: *BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models* - status **exact**
- **[59]** - arXiv id_list lookup - `arXiv:2210.07316` - resolved: *MTEB: Massive Text Embedding Benchmark* - status **exact**
- **[60]** - arXiv id_list lookup - `arXiv:2112.01488` - resolved: *ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction* - status **exact**
- **[61]** - arXiv id_list lookup - `arXiv:2402.03216` - resolved: *M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation* - status **exact**
- **[62]** - arXiv id_list lookup - `arXiv:2403.18684` - resolved: *Scaling Laws For Dense Retrieval* - status **exact**
- **[63]** - arXiv id_list lookup - `arXiv:2306.11397` - resolved: *Generative Retrieval as Dense Retrieval* - status **exact**
- **[64]** - arXiv id_list lookup - `arXiv:2203.05765` - resolved: *Tevatron: An Efficient and Flexible Toolkit for Dense Retrieval* - status **exact**
- **[65]** - arXiv id_list lookup - `arXiv:2407.03618` - resolved: *BM25S: Orders of magnitude faster lexical search via eager sparse scoring* - status **exact**
- **[66]** - arXiv id_list lookup - `arXiv:0911.5046` - resolved: *Integrating the Probabilistic Models BM25/BM25F into Lucene* - status **exact**
- **[67]** - arXiv id_list lookup - `arXiv:2505.21700` - resolved: *Rethinking Chunk Size For Long-Document Retrieval: A Multi-Dataset Analysis* - status **exact**
- **[68]** - arXiv id_list lookup - `arXiv:2410.12388` - resolved: *Prompt Compression for Large Language Models: A Survey* - status **exact**
- **[69]** - arXiv id_list lookup - `arXiv:2403.12968` - resolved: *LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression* - status **exact**
- **[70]** - arXiv id_list lookup - `arXiv:2403.17411` - resolved: *PCToolkit: A Unified Plug-and-Play Prompt Compression Toolkit of Large Language Models* - status **exact**
- **[71]** - arXiv id_list lookup - `arXiv:2501.06730` - resolved: *Better Prompt Compression Without Multi-Layer Perceptrons* - status **exact**
- **[72]** - arXiv id_list lookup - `arXiv:2505.00019` - resolved: *An Empirical Study on Prompt Compression for Large Language Models* - status **exact**
- **[73]** - arXiv id_list lookup - `arXiv:2508.15813` - resolved: *SCOPE: A Generative Approach for LLM Prompt Compression* - status **exact**
- **[74]** - arXiv id_list lookup - `arXiv:2309.17453` - resolved: *Efficient Streaming Language Models with Attention Sinks* - status **exact**
- **[75]** - arXiv id_list lookup - `arXiv:2410.10781` - resolved: *When Attention Sink Emerges in Language Models: An Empirical View* - status **exact**
- **[76]** - arXiv id_list lookup - `arXiv:2510.00231` - resolved: *The Pitfalls of KV Cache Compression* - status **exact**
- **[77]** - arXiv id_list lookup - `arXiv:2607.01520` - resolved: *The risk of KV cache compression* - status **exact**
- **[78]** - arXiv id_list lookup - `arXiv:2410.15252` - resolved: *Lossless KV Cache Compression to 2%* - status **exact**
- **[79]** - arXiv id_list lookup - `arXiv:2505.24133` - resolved: *R-KV: Redundancy-aware KV Cache Compression for Reasoning Models* - status **exact**
- **[80]** - arXiv id_list lookup - `arXiv:2306.15595` - resolved: *Extending Context Window of Large Language Models via Positional Interpolation* - status **exact**
- **[81]** - arXiv id_list lookup - `arXiv:2309.10400` - resolved: *PoSE: Efficient Context Window Extension of LLMs via Positional Skip-wise Training* - status **exact**
- **[82]** - arXiv id_list lookup - `arXiv:2502.20082` - resolved: *LongRoPE2: Near-Lossless LLM Context Window Scaling* - status **exact**
- **[83]** - arXiv id_list lookup - `arXiv:2410.01490` - resolved: *Extending Context Window of Large Language Models from a Distributional Perspective* - status **exact**
- **[84]** - arXiv id_list lookup - `arXiv:2401.07004` - resolved: *Extending LLMs' Context Window with 100 Samples* - status **exact**
- **[85]** - arXiv id_list lookup - `arXiv:2502.06975` - resolved: *Position: Episodic Memory is the Missing Piece for Long-Term LLM Agents* - status **exact**
- **[86]** - arXiv id_list lookup - `arXiv:2604.08224` - resolved: *Externalization in LLM Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering* - status **exact**
- **[87]** - arXiv id_list lookup - `arXiv:2503.21760` - resolved: *MemInsight: Autonomous Memory Augmentation for LLM Agents* - status **exact**
- **[88]** - arXiv id_list lookup - `arXiv:2606.29178` - resolved: *Selective Memory Retention for Long-Horizon LLM Agents* - status **exact**
- **[89]** - arXiv id_list lookup - `arXiv:2603.13110` - resolved: *AgentRM: An OS-Inspired Resource Manager for LLM Agent Systems* - status **exact**
- **[90]** - arXiv id_list lookup - `arXiv:2603.07379` - resolved: *SoK: Agentic Retrieval-Augmented Generation (RAG): Taxonomy, Architectures, Evaluation, and Research Directions* - status **exact**
- **[91]** - arXiv id_list lookup - `arXiv:2510.14278` - resolved: *PRISM: Agentic Retrieval with LLMs for Multi-Hop Question Answering* - status **exact**
- **[92]** - arXiv id_list lookup - `arXiv:2606.06708` - resolved: *Signal-Driven Observation for Long-Horizon Web Agents* - status **exact**
- **[93]** - arXiv id_list lookup - `arXiv:2408.04259` - resolved: *EfficientRAG: Efficient Retriever for Multi-Hop Question Answering* - status **exact**
- **[94]** - arXiv id_list lookup - `arXiv:2404.14464` - resolved: *Tree of Reviews: A Tree-based Dynamic Iterative Retrieval Framework for Multi-hop Question Answering* - status **exact**
- **[95]** - arXiv id_list lookup - `arXiv:2406.14891` - resolved: *Generate-then-Ground in Retrieval-Augmented Generation for Multi-hop Question Answering* - status **exact**
- **[96]** - arXiv id_list lookup - `arXiv:1909.07598` - resolved: *Multi-step Entity-centric Information Retrieval for Multi-Hop Question Answering* - status **exact**
- **[97]** - arXiv id_list lookup - `arXiv:2410.12311` - resolved: *Open Domain Question Answering with Conflicting Contexts* - status **exact**
- **[98]** - arXiv id_list lookup - `arXiv:2402.07483` - resolved: *T-RAG: Lessons from the LLM Trenches* - status **exact**
- **[99]** - arXiv id_list lookup - `arXiv:2604.01432` - resolved: *Are Finer Citations Always Better? Rethinking Granularity for Attributed Generation* - status **exact**
- **[100]** - arXiv id_list lookup - `arXiv:2510.17853` - resolved: *CiteGuard: Faithful Citation Attribution for LLMs via Retrieval-Augmented Validation* - status **exact**
- **[101]** - arXiv id_list lookup - `arXiv:2602.00004` - resolved: *C$^2$-Cite: Contextual-Aware Citation Generation for Attributed Large Language Models* - status **exact**
- **[102]** - arXiv id_list lookup - `arXiv:2606.03728` - resolved: *Re-Ranking Through an Attribution Lens for Citation Quality in Legal QA* - status **exact**
- **[103]** - arXiv id_list lookup - `arXiv:2504.19457` - resolved: *Towards Long Context Hallucination Detection* - status **exact**
- **[104]** - arXiv id_list lookup - `arXiv:2608.18082` - resolved: *LongNovel: A Multi-Scale Benchmark for Hallucination Detection in Long-Context Novel Summarization* - status **exact**
- **[105]** - arXiv id_list lookup - `arXiv:2502.02737` - resolved: *SmolLM2: When Smol Goes Big -- Data-Centric Training of a Small Language Model* - status **exact**
- **[106]** - arXiv id_list lookup - `arXiv:2005.14165` - resolved: *Language Models are Few-Shot Learners* - status **exact**
- **[107]** - arXiv id_list lookup - `arXiv:2303.08774` - resolved: *GPT-4 Technical Report* - status **exact**
- **[108]** - arXiv id_list lookup - `arXiv:2205.14135` - resolved: *FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness* - status **exact**
- **[109]** - arXiv id_list lookup - `arXiv:2412.13663` - resolved: *Smarter, Better, Faster, Longer: A Modern Bidirectional Encoder for Fast, Memory Efficient, and Long Context Finetuning and Inference* - status **exact**
- **[110]** - Crossref DOI lookup - `DOI 10.1561/1500000019` - resolved: *The Probabilistic Relevance Framework: BM25 and Beyond* - status **exact**
- **[111]** - Crossref DOI lookup - `DOI 10.6028/nist.sp.500-240.interactive-city` - resolved: *Interactive Okapi at TREC-6* - status **exact**
- **[112]** - Crossref DOI lookup - `DOI 10.18653/v1/d16-1264` - resolved: *SQuAD: 100,000+ Questions for Machine Comprehension of Text* - status **exact**
- **[113]** - Crossref DOI lookup - `DOI 10.1145/3539618.3591796` - resolved: *Dense Passage Retrieval: Architectures and Augmentation Methods* - status **exact**
- **[114]** - Crossref DOI lookup - `DOI 10.1017/cbo9780511844744.008` - resolved: *Instructional Control of Cognitive Load in the Design of Complex Learning Environments* - status **exact**
- **[115]** - Crossref DOI lookup - `DOI 10.4018/978-1-60960-503-2.ch707` - resolved: *Instructional Game Design Using Cognitive Load Theory* - status **exact**

## (ii) Coverage and ambiguity

**Exactly one** `## References` section, numbered `[1]`-`[115]`, in the same bracket style the body uses.

Gate output, run from the repository root exactly as the presentation requirements specify:

```
$ python3 .github/tools/refgate.py papers/issue-1/manuscript.md
=== papers/issue-1/manuscript.md
  entries=115  numbering=[n]
  in-text cited numbers=115  covered=115/115  coverage=100.0%
  GATE: PASS
```

No uncited entries and no unmatched bracket numbers were reported. Every entry carries an in-text key,
so there is no padding to discount.

### Bracketed groups in the text that are NOT citations

The gate reported **no** unmatched bracket numbers, so every bracketed group it recognises as a citation
resolves to a bibliography entry. Three kinds of bracketed construct appear in the text that are **not**
citations; stating them here is the point of this subsection, because the syntax is not self-evident:

1. **Wilson confidence intervals in Table 1** - `[0.676, 1.000]`, `[0.000, 0.324]`, `[0.022, 0.471]`,
   `[0.137, 0.694]`, `[0.215, 0.785]`, `[0.071, 0.591]`, `[0.022, 0.471]`. These are interval bounds, i.e.
   decimal numbers, not entry numbers. They are also the reason the gate cannot mis-read them: its citation
   pattern requires a group to begin with an integer followed by `,`, `-` or `]`, and a decimal-leading group
   like `0.676,` fails that test, so these are never counted as citations nor reported as unmatched.
2. **Mathematical set notation** - `k in {1, 2, 4, 8}` in Sections 3.1-3.3 and in Table 1's caption. Braces,
   not brackets; a set of retrieval budgets.
3. **Illustrative notation in this report** - backticked forms such as `[n]`, `[1]`-`[115]`, `[12,14]` and
   `[12-14]` used here to *describe* the citation syntax. `[n]` contains no digit and is not matched by the
   gate at all. (Note that the gate strips fenced code blocks but not inline code spans, so this paragraph
   deliberately places these examples inside backticks where they are unambiguous to a human reader; the
   authoritative check is the gate output above, which was produced on the manuscript, not on this report.)

There are **no numeric ranges in the prose** of this manuscript written in bracket notation - no latency
spans of the form `[25,30] ms`, and no bracket groups containing a decimal other than the intervals in
item 1. A scan of the body confirms it: 108 distinct bracket groups appear, all of them integer-only
citation clusters with no ranges and no decimal points, and the gate finds all 115 entries covered.

