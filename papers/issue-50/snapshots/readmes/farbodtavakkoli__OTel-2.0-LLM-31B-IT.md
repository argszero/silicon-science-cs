---
license: apache-2.0
language:
- en
base_model:
- google/gemma-4-31B-it
tags:
- telecom
- telecommunications
- gsma
- at-t
- microsoft
- dell
- amd
- red-hat
- open-telco-ai
- rag
- instruction-following
- tool-calling
- domain-adaptation
- post-trained
- transformers
pipeline_tag: text-generation
---

# OTel-2.0-LLM-31B-IT

> **Checkpoint update notice:** The current checkpoint is expected to be updated within the next few hours. After that initial refresh, OTel 2.0 checkpoints are expected to continue receiving weekly weight updates. For reproducible evaluation or production deployment, pin a specific model revision, checkpoint hash, or release tag.

**OTel-2.0-LLM-31B-IT** is a telecom-specialized instruction model post-trained from **Gemma 4 31B-IT** on approximately **440 billion telecom training tokens**. It is the first release in the OTel 2.0 family and is designed to support telco-grade AI workflows across network operations, standards interpretation, product development, network configuration assistance, RAG, and telecom-specific question answering.

OTel 2.0 extends the original OTel effort from a RAG-oriented telecom fine-tuning release into a larger domain-adapted training program. The model was trained from a much larger standards and telecom corpus, with new data preparation coverage for direct telecom QnA, abstention, RAG, base-model-style telecom data, and general-purpose instruction-following and tool-calling examples. The current training mixture does not include telecommunications-specific MCP, tool-calling, or instruction-following examples.

## Release Status

OTel 2.0 models are expected to continue training after release, and weights may be updated weekly. For reproducible evaluation or production deployment, pin a specific model revision, checkpoint hash, or release tag rather than relying on the floating latest weights.

## Model Details

| Attribute | Value |
|---|---|
| Base model | Gemma 4 31B-IT |
| Parameters | 31B |
| Model family | OTel 2.0 |
| Training method | Telecom domain post-training / instruction tuning |
| Raw telecom corpus | ~15B tokens from GSMA through Open Telco AI |
| Processed data volume | >1T tokens processed using Red Hat's open-source Synthetic Data Generation Hub (SDG Hub) |
| Training tokens | ~440B |
| Compute for data processing | ~530 GPUs through Microsoft Azure Managed Compute, primarily AMD MI300X |
| Model training infrastructure | On-premises AMD MI355X GPUs with Dell Technologies infrastructure and servers |
| Day 0 inference availability | Microsoft Foundry, Featherless AI, and Red Hat |
| Supported interaction | English-language text only |


## Model Lineage

`Gemma 4 31B-IT` -> OTel 2.0 telecom data processing and post-training -> `OTel-2.0-LLM-31B-IT`

## What Changed From OTel 1.0

| Category | Metric | OTel 1.0 | OTel 2.0 |
|---|---|---:|---:|
| Tokens | Raw documents | ~600M | ~15B |
| Tokens | Training | ~1B | ~440B |
| Data preparation | General-purpose agentic tool calling | No | Yes |
| Data preparation | Knowledge / fact direct QnA | No | Yes |
| Data preparation | RAG | Yes | Yes |
| Data preparation | Abstention | Yes | Yes |
| Data preparation | General-purpose instruction following | No | Yes |
| Data preparation | Base model training set | No | Yes |

Relative to OTel 1.0, OTel 2.0 increases raw source coverage by roughly 25x and training-token volume by roughly 440x. More importantly, the data mixture is broader: OTel 1.0 focused primarily on context-grounded RAG and abstention, while OTel 2.0 adds direct telecom knowledge QnA, general-purpose instruction-following and tool-use-oriented examples, and base-model-style telecom training data. Telecommunications-specific MCP, tool-calling, and instruction-following examples are not part of the current training mixture.

## Training Data

The starting corpus contains approximately **15 billion raw tokens** provided by GSMA through Open Telco AI. The corpus includes telecom standards and technical material from seven standards development and industry organizations:

| Source family | Examples |
|---|---|
| Cellular standards | 3GPP |
| Telecom standards and specifications | ETSI, ITU |
| Industry and operator materials | GSMA |
| Network API specifications | CAMARA |
| Open RAN specifications | O-RAN |
| Telecom business and operations frameworks | TM Forum |

Dense technical specifications from these sources were converted into material suitable for model training. The raw corpus was processed into **over 1 trillion tokens** using **Red Hat's open-source Synthetic Data Generation Hub (SDG Hub)** on **Microsoft Azure Managed Compute**, using approximately **530 GPUs**, primarily **AMD MI300X**. From this processed pool, approximately **440 billion training tokens** were generated for OTel 2.0 post-training. Model training ran on **on-premises AMD MI355X GPUs** with **Dell Technologies infrastructure and servers**.

## Data Preparation Capabilities

OTel 2.0 includes a broader supervised and synthetic-data mixture than OTel 1.0:

| Capability | Description |
|---|---|
| RAG | Context-grounded telecom answer generation from retrieved standards and technical documents |
| Abstention | Training examples that teach the model to avoid answering when context is missing, irrelevant, or insufficient |
| Direct telecom QnA | Knowledge and factual question-answer pairs for standards, protocols, services, and network concepts |
| Instruction following | General-purpose instruction-following examples; the current mixture does not include telecommunications-specific instruction-following examples |
| Agentic tool calling | General-purpose tool-calling examples; the current mixture does not include telecommunications-specific MCP or tool-calling examples |

## Intended Use

OTel-2.0-LLM-31B-IT is intended for telecom-focused applications where domain knowledge, standards familiarity, and deployment control matter. Suitable use cases include:

- Retrieval-Augmented Generation over telecom standards, specifications, and internal technical documentation.
- Standards interpretation and summarization for 3GPP, ETSI, GSMA, CAMARA, ITU, O-RAN, and TM Forum materials.
- Product development, network configuration assistance, and engineering support tasks.
- Telecom-specific direct QnA where the model has been separately evaluated for the target benchmark or application.
- Agentic workflows where a larger system provides verified tools, retrieval, validation, and audit logging.

For high-impact operational use, the model should be deployed with retrieval, source attribution, validation checks, and human review appropriate to the system risk.

## Limitations and Responsible Use

### Supported Language and Modality

OTel 2.0 currently supports **English-language, text-only interactions**. It has not been established as a multilingual or multimodal model and should not be assumed to support images, audio, video, or other non-text modalities.

### Tool Use and Instruction Following

The training data includes **general-purpose tool-calling and instruction-following examples**, but it does not currently include:

- Telecommunications-specific MCP examples.
- Telecommunications-specific tool-calling examples.
- Telecommunications-specific instruction-following examples.

General-purpose tool-use training should not be interpreted as readiness to operate telecommunications tools autonomously. Agentic deployment requires an external tool runtime, validated tool schemas, permission controls, audit logging, safeguards, and human review appropriate to the risk. The model alone does not guarantee correct or safe tool execution.

### Telecommunications Data Not Included in Training

The current training mixture does not include the following classes of operational telecommunications data:

- **Event data:** Elasticsearch records covering user activity, anomalies, failures, IMS events, and RADIUS authentication.
- **Network-performance data:** KPIs, 5G performance metrics, and Passive Intermodulation (PIM) interference data.
- **RF and spectral data:** Field-test results, antenna-port metrics, signal diagnostics, heatmaps, and noise or interference measurements.
- **5G core data:** Control-plane and inter-Network Function (NF) signaling data.

Standards knowledge should not be interpreted as experience with live operator telemetry, private network records, or these excluded operational datasets. Applications involving these data types require separate task-specific evaluation, grounding, and validation.

### General Reliability and Deployment Limitations

- OTel 2.0 is domain-specific to telecommunications and should not be treated as a general-purpose model for unrelated fields.
- Telecom standards evolve over time; answers should be checked against the relevant document version and release.
- RAG quality depends on document ingestion, chunking, retrieval, reranking, prompt design, and source freshness.
- Direct QnA behavior should be evaluated separately from RAG behavior; strong performance in one setting does not imply strong performance in the other.
- For high-impact operational use, deploy the model with retrieval, source attribution, validation checks, and human review appropriate to the system risk.

## Related Models

- [OTel LLM Collection](https://huggingface.co/collections/farbodtavakkoli/otel-llm)
- [OTel Embedding Collection](https://huggingface.co/collections/farbodtavakkoli/otel-embedding)
- [OTel Reranker Collection](https://huggingface.co/collections/farbodtavakkoli/otel-reranker)

## Project Resources

- Project page: https://huggingface.co/farbodtavakkoli
- Code: https://github.com/farbodtavakkoli/OTel
- Media coverage list: https://github.com/farbodtavakkoli/OTel/blob/main/docs/media_coverage.md

## Contributors and Organizations

Contributors to the OTel 2.0 release and supporting infrastructure include:

| Organization | Contributors |
|---|---|
| AT&T | Farbod Tavakkoli, Jorden Terrazas, Roderic Paulk, Sharath Japa, Tzvi Chumash, Miguel Armenta, Pavan Tagirisa, Kostikey Mustakas, Mark Austin, Andy Markus |
| MLCommons | Gregory Diamos, David Kanter, Kenneth Church |
| Microsoft | Chunyu Li, Gulsimo Osimi, Rick Lievano, Inayat Wali, Manoj Bableshwar, Marie-Louise Onga Nana, Naomi Moneypenny, Osi Otugo, Rahul Kumar, SeokJin Han, Steve Sweetman, Trinidad Salazar, Ven Kumar, Vivek Ramaswamy |
| AMD | Alexander Finn, Andy Allred, Andrey Ivannikov, Antti-Ville Suni, Mark van Heeswijk, Kumaran Siva, Curt Wortman, Mehrvash Poole, Eric Lynn |
| Dell | Brian Sweeney, Suzanne Randall, Patrick Allen, Matt Currie, Justin Wilson, Jason Kane, Keith Napoleon, Sarah Lake, Mike Hess, Randy Tornes |
| GSMA | Louis Powell, Zeinab Nezami, Enrique Molero |
| Red Hat | Aditi Saluja, William Caban, Shivchander Sudalairaj, Kai Xu, Ravi Sharma, Hanen Garcia, Joe Crispo, Eshwar Sivaramakrishnan |
| Pleias | Anastasia Stasenko, Pierre-Carl Langlais, Mohamed Chenene, Carlos Rosas, Yannick Detrois |

Organizations involved in the OTel 2.0 release and supporting infrastructure include AT&T, MLCommons, Microsoft, AMD, Dell, GSMA, Red Hat, and Pleias.

## Citation

```bibtex
@misc{otel_2_models_2026,
  title  = {OTel 2.0: Open Telco AI Datasets, Benchmarks, and Models},
  author = {Tavakkoli, Farbod and others},
  year   = {2026},
  note   = {Open Telco (OTel 2.0) model release},
  url    = {https://huggingface.co/farbodtavakkoli},
  organization = {AT\&T, MLCommons, Microsoft, AMD, Dell, GSMA, Red Hat, Pleias}
}
```

## Contact

For technical questions, contact farbod.tavakkoli@att.com or farbodtavakoli@gmail.com.
 
