---
pipeline_tag: text-generation
base_model:
- google/gemma-4-26B-A4B-it
license: apache-2.0
license_name: apache-license-2.0 
license_link: https://ai.google.dev/gemma/apache_2
library_name: Model Optimizer
tags:
- nvidia
- ModelOpt
- quantized
- NVFP4
- nvfp4
- gemma4
- gemma4-26b-A4B-it
---

# Model Overview

## Description:
Gemma 4 26B IT is an open multimodal model built by Google DeepMind that handles text and image inputs, can process video as sequences of frames, and generates text output. It is designed to deliver frontier-level performance for reasoning, agentic workflows, coding, and multimodal understanding on consumer GPUs and workstations, with a 256K-token context window and support for over 140 languages. The model uses a hybrid attention mechanism that interleaves local sliding-window and full global attention, with unified Keys and Values in global layers and Proportional RoPE (p-RoPE) to support long-context performance. The NVIDIA Gemma 4 26B IT NVFP4 model is quantized with [NVIDIA Model Optimizer](https://github.com/NVIDIA/TensorRT-Model-Optimizer).

This model is ready for commercial/non-commercial use.  <br> 

# Third-Party Community Consideration
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [Gemma 4 26B IT Model Card](https://huggingface.co/google/gemma-4-26B-A4B-it)

## License and Terms of Use:
[Apache License 2.0  |  Gemma  |  Google AI for Developers](https://ai.google.dev/gemma/apache_2)

## Deployment Geography:
Global

## Use Case:
**Use Case:** Designed for text generation, chatbots and conversational AI, text summarization, image data extraction, reasoning, coding, multimodal understanding, function calling, and research or educational use.

## Release Date:
Hugging Face [04/30/2026] via https://huggingface.co/nvidia/Gemma-4-26B-A4B-NVFP4

## Model Architecture:
| Property | 26B A4B MoE |
| :---- | :---- |
| **Architecture Type:**| Transformers |
| **Total Parameters** | 25.2B |
| **Active Parameters** | 3.8B |
| **Layers** | 30 |
| **Sliding Window** | 1024 tokens |
| **Context Length** | 256K tokens |
| **Vocabulary Size** | 262K |
| **Expert Count** | 8 active / 128 total and 1 shared |
| **Supported Modalities** | Text, Image |
| **Vision Encoder Parameters** | *~550M* |

The "A" in 26B A4B stands for "active parameters" in contrast to the total number of parameters the model contains. 


## Input:
**Input Type(s):** Processes Text, Image with variable aspect ratio and resolution support (all models), Video, and Audio (featured natively on the E2B and E4B models). <br>
**Input Format(s):** String, Red, Green, Blue (RGB), Video (MP4/WebM) <br>
**Input Parameters:** One-Dimensional (1D), Two-Dimensional (2D), Three-Dimensional (3D)<br>
**Other Properties Related to Input:** Supports variable image aspect ratios and resolutions, configurable visual token budgets of 70, 140, 280, 560, and 1120, and video inputs up to 60 seconds at one frame per second. <br>
**Input Context Length (ISL):** 256K


## Output:
**Output Type(s):** Text <br>
**Output Format:** String <br>
**Output Parameters:** 1D (One Dimensional): Sequences <br>
**Other Properties Related to Output:** Generates text responses for chat, reasoning, coding, multimodal understanding, and function-calling workflows. When thinking is enabled, model outputs reasoning tokens as well.

__Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.__

## Software Integration:
**Supported Runtime Engine(s):** <br>
* vLLM <br>

**Supported Hardware Microarchitecture Compatibility:** <br>
NVIDIA Blackwell <br>

**Preferred Operating System(s):** <br>
* Linux <br>

## Model Version(s):
The model version is v1.0 which NVFP4 quantized with nvidia-modelopt **v0.43.0**  <br>

## Training, Testing, and Evaluation Datasets:

We calibrated the model using the dataset noted below, and performed evaluation using the benchmarks noted under Evaluation Datasets.
We did not perform training or testing for this Model Optimizer release. The methods noted under Training and Testing Datasets below represent the data collection and labeling methods used by the third-party to train and test the underlying Gemma 4 26B IT model.<br>

## Calibration Dataset:
**Link:** [cnn_dailymail](https://huggingface.co/datasets/abisee/cnn_dailymail), [Nemotron-Post-Training-Dataset-v2](https://huggingface.co/datasets/nvidia/Nemotron-Post-Training-Dataset-v2)  
**Data Collection Method by dataset:** Automated.  
**Labeling Method by dataset:** Automated.  
**Properties:** The `cnn_dailymail` dataset contains English-language news articles and summaries. `Nemotron-Post-Training-Dataset-v2` is a post-training dataset curated by NVIDIA containing multi-turn conversations across diverse topics.

**Training Dataset**
**Data Modality:** Text, Image, Audio, Other (Code)<br>
**Training Data Collection:** Automated<br>
**Training Labeling:** Undisclosed<br>
**Training Properties:** Large-scale multimodal pre-training data spanning web documents, code, images, and audio, with a cutoff date of January 2025 and coverage in over 140 languages. Data was filtered for CSAM, sensitive data, quality, and safety.<br>

**Testing Dataset**
**Testing Data Collection:** Undisclosed<br>
**Testing Labeling:** Undisclosed<br>
**Testing Properties:** Undisclosed<br>

## Evaluation Dataset:
**Data Collection Method by dataset:** Hybrid: Human, Automated <br>
**Labeling Method by dataset: Hybrid:** Human, Automated <br>
**Properties:** We evaluated the model on text-based reasoning and coding benchmarks: MMLU Pro is a multi-task language understanding benchmark with challenging multiple-choice questions across diverse academic domains; LiveCodeBench V6 contains competitive programming problems; SciCode evaluates scientific coding capabilities; IFEval is a benchmark that tests whether language models can follow explicit, verifiable formatting and structural constraints layered on top of content generation prompts; GPQA Diamond contains 448 graduate-level multiple-choice questions written by domain experts in biology, physics, and chemistry; AIME 2025 contains problems from the American Invitational Mathematics Examination; IFBench is a benchmark for evaluating instruction-following capabilities across diverse and structured task constraints.


## Inference:
**Engine:** vLLM <br>
**Test Hardware:** B200 <br>

## Post Training Quantization
This model was obtained by quantizing the weights and activations of Gemma-4-26B-IT-NVFP4 to NVFP4 data type (using the nvfp4_experts_only recipe), ready for inference with vLLM.  

## Usage

Currently for this model, vllm works with TP=1 only, it does support EP,there is an open issue in [vLLM](https://github.com/vllm-project/vllm/issues/39595) and [Flashinfer](https://github.com/flashinfer-ai/flashinfer/issues/3206). 
Additionally, the current MoE backend is either VLLM_CUTLASS or Marlin, to use the Flashinfer-TRTLLM there is an [open PR](https://github.com/vllm-project/vllm/pull/41050) in vLLM.

To serve this checkpoint with [vLLM](https://hub.docker.com/layers/vllm/vllm-openai/v0.20.0/images/sha256-77797441eae630c2e79eefa03957b3d61a278670f2a9928d64ce102e7a0790cc) and run the sample command below.

```
vllm serve nvidia/Gemma-4-26B-A4B-NVFP4 \
  --tool-call-parser gemma4 \
  --reasoning-parser gemma4 \
  --enable-auto-tool-choice \
  --trust-remote-code
```


## Evaluation Results:

| Benchmark | Baseline (Full Precision) | NVFP4 |
|---|---|---|
| GPQA Diamond | 80.30% | 79.90% |
| AIME 2025 | 88.95% | 90.00% |
| MMLU Pro | 85.00% | 84.80% |
| LiveCodeBench (pass@1) | 80.50% | 79.80% |
| IFBench | 77.77% | 78.1% |
| IFEval | 96.60% | 96.40% |
> Baseline: [Gemma-4-26B-A4B-it-bf16](https://huggingface.co/google/gemma-4-26B-A4B-it)<br>
> Benchmarked with temperature=1.0, top_p=0.95, max_new_tokens= 131072

## Model Limitations:
The base model was trained on data that contains toxic language and societal biases originally crawled from the internet. Therefore, the model may amplify those biases and return toxic responses especially when prompted with toxic prompts. The model may generate answers that may be inaccurate, omit key information, or include irrelevant or redundant text producing socially unacceptable or undesirable text, even if the prompt itself does not include anything explicitly offensive.

## Ethical Considerations

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications.  When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please make sure you have proper rights and permissions for all input image and video content; if image or video includes people, personal health information, or intellectual property, the image or video generated will not blur or maintain proportions of image subjects included.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).