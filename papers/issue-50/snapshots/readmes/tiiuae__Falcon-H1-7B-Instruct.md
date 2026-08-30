---
library_name: transformers
language:
- ar
- cs
- de
- en
- es
- fr
- hi
- it
- ja
- ko
- nl
- pl
- pt
- ro
- ru
- sv
- ur
- zh
tags:
- falcon-h1
license: other
license_name: falcon-llm-license
license_link: https://falconllm.tii.ae/falcon-terms-and-conditions.html
base_model: tiiuae/Falcon-H1-7B-Base
inference: true
---

<img src="https://huggingface.co/datasets/tiiuae/documentation-images/resolve/main/falcon_mamba/falcon-h1-logo.png" alt="drawing" width="800"/>

#  Table of Contents

0. [TL;DR](#TL;DR)
1. [Model Details](#model-details)
2. [Training Details](#training-details)
3. [Usage](#usage)
4. [Evaluation](#evaluation)
5. [Citation](#citation)

# TL;DR

# Model Details

## Model Description

- **Developed by:** [https://www.tii.ae](https://www.tii.ae)
- **Model type:** Causal decoder-only
- **Architecture:** Hybrid Transformers + Mamba architecture
- **Language(s) (NLP):** English, Multilingual
- **License:** Falcon-LLM License

# Training details

For more details about the training protocol of this model, please refer to the [Falcon-H1 technical blogpost](https://falcon-lm.github.io/blog/falcon-h1/) and [Technical Report](https://arxiv.org/abs/2507.22448).

# Usage

Currently to use this model you can either rely on Hugging Face `transformers`, `vLLM` or `llama.cpp` library.

## Inference

Make sure to install the latest version of `transformers` or `vllm`, eventually install these packages from source:

```bash
pip install git+https://github.com/huggingface/transformers.git
```

For vLLM, make sure to install `vllm>=0.9.0`:

```bash
pip install "vllm>=0.9.0"
```

### 🤗 transformers

Refer to the snippet below to run H1 models using 🤗 transformers:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "tiiuae/Falcon-H1-1B-Base"

model = AutoModelForCausalLM.from_pretrained(
  model_id,
  torch_dtype=torch.bfloat16,
  device_map="auto"
)

# Perform text generation
```

### vLLM

For vLLM, simply start a server by executing the command below:

```
# pip install vllm>=0.9.0
vllm serve tiiuae/Falcon-H1-1B-Instruct --tensor-parallel-size 2 --data-parallel-size 1
```

### `llama.cpp`

You can find all GGUF files under [our official collection](https://huggingface.co/collections/tiiuae/falcon-h1-6819f2795bc406da60fab8df)

# Evaluation

Falcon-H1 series perform very well on a variety of tasks, including reasoning tasks. 

| Tasks | Falcon-H1-7B | Qwen3-8B | Qwen2.5-7B | Gemma3-12B | Llama3.1-8B | Falcon3-7B | Falcon3-10B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **General**  | | | | | | |
| BBH | 62.28 | 47.47 | 53.76 | **63.36** | 48.58 | 52.12 | 58.09 |
| ARC-C | **59.98** | 42.06 | 41.38 | 51.96 | 52.39 | 54.35 | 54.44 |
| TruthfulQA | 59.91 | 53.19 | **62.41** | 61.02 | 52.99 | 55.58 | 55.05 |
| HellaSwag | **75.92** | 60.56 | 63.4 | 55.63 | 71.28 | 71.81 | 75.57 |
| MMLU | **76.83** | 71.56 | 73.64 | 72.5 | 68.67 | 70.81 | 74.01 |
| **Math**  | | | | | | |
| GSM8k | 81.65 | 78.92 | 71.95 | **87.49** | 82.49 | 81.05 | 85.06 |
| MATH-500 | 73.4 | 83.8 | 75.8 | **86.2** | 45.8 | 69.0 | 68.6 |
| AMC-23 | 56.72 | **70.78** | 53.91 | 66.88 | 22.81 | 40.0 | 45.78 |
| AIME-24 | 16.04 | **28.33** | 12.29 | 22.5 | 5.42 | 8.75 | 9.79 |
| AIME-25 | 13.96 | **19.17** | 9.58 | 18.75 | 0.42 | 6.25 | 5.42 |
| **Science**  | | | | | | |
| GPQA | **36.33** | 25.84 | 31.79 | 33.98 | 32.72 | 31.21 | 33.39 |
| GPQA_Diamond | **56.9** | 43.1 | 33.0 | 37.71 | 31.31 | 37.21 | 34.68 |
| MMLU-Pro | **51.75** | 34.64 | 43.23 | 39.88 | 36.42 | 40.73 | 44.05 |
| MMLU-stem | **77.61** | 66.89 | 69.36 | 66.54 | 59.31 | 67.43 | 70.57 |
| **Code**  | | | | | | |
| HumanEval | **86.59** | 84.75 | 82.32 | 84.76 | 68.29 | 71.95 | 82.32 |
| HumanEval+ | **81.1** | 79.27 | 73.78 | 75.61 | 61.59 | 65.85 | 75.0 |
| MBPP | 80.69 | 71.96 | 79.63 | **85.71** | 68.25 | 77.25 | 73.28 |
| MBPP+ | 68.78 | 62.7 | 68.25 | **72.22** | 55.03 | 65.87 | 64.02 |
| LiveCodeBench | 35.03 | **45.6** | 32.68 | 30.92 | 15.85 | 12.72 | 19.77 |
| CRUXEval | 66.51 | **72.7** | 56.9 | 67.67 | 21.57 | 55.0 | 59.57 |
| **Instruction Following**  | | | | | | |
| IFEval | **85.35** | 83.43 | 75.25 | 81.51 | 77.04 | 76.59 | 78.84 |
| Alpaca-Eval | 40.23 | **46.13** | 29.48 | 43.55 | 25.48 | 27.56 | 24.31 |
| MTBench | **8.85** | 8.74 | 8.45 | 8.69 | 8.29 | 8.73 | 8.46 |
| LiveBench | 45.74 | **56.19** | 37.13 | 49.23 | 31.73 | 32.35 | 34.3 |

You can check more in detail on our [our release blogpost](https://falcon-lm.github.io/blog/falcon-h1/), detailed benchmarks.

# Useful links

- View [our release blogpost](https://falcon-lm.github.io/blog/falcon-h1/).
- View [our technical report](https://arxiv.org/abs/2507.22448).
- Feel free to join [our discord server](https://discord.gg/trwMYP9PYm) if you have any questions or to interact with our researchers and developers.

# Citation

If the Falcon-H1 family of models were helpful to your work, feel free to give us a cite.

```
@article{falconh1,
    title={Falcon-H1: A Family of Hybrid-Head Language Models Redefining Efficiency and Performance},
    author={Jingwei Zuo and Maksim Velikanov and Ilyas Chahed and Younes Belkada and Dhia Eddine Rhayem and Guillaume Kunsch and Hakim Hacid and Hamza Yous and Brahim Farhat and Ibrahim Khadraoui and Mugariya Farooq and Giulia Campesan and Ruxandra Cojocaru and Yasser Djilali and Shi Hu and Iheb Chaabane and Puneesh Khanna and Mohamed El Amine Seddik and Ngoc Dung Huynh and Phuc Le Khac and Leen AlQadi and Billel Mokeddem and Mohamed Chami and Abdalgader Abubaker and Mikhail Lubinets and Kacper Piskorski and Slim Frikha},
    journal = {arXiv preprint arXiv:2507.22448},
    year={2025}
}
```