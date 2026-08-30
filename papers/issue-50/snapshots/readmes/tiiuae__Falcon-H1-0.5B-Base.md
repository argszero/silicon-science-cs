---
library_name: transformers
tags:
- falcon-h1
license: other
license_name: falcon-llm-license
license_link: https://falconllm.tii.ae/falcon-terms-and-conditions.html
language:
- en
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
- **Language(s) (NLP):** English
- **License:** Falcon-LLM License

# Training details

For more details about the training protocol of this model, please refer to the [Falcon-H1 technical blogpost](https://falcon-lm.github.io/blog/falcon-h1/) and [Technical Report](https://arxiv.org/abs/2507.22448).

# Usage

Currently to use this model you can either rely on Hugging Face `transformers`, `vLLM` or `llama.cpp` library.

## Inference

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

| Tasks | Falcon-H1-0.5B | Qwen3-0.6B | Qwen2.5-0.5B | Gemma3-1B | Llama3.2-1B | Falcon3-1B |
| --- | --- | --- | --- | --- | --- | --- |
| **General**  | | | | | |
| BBH | **40.22** | 36.07 | 32.62 | 30.26 | 30.72 | 35.24 |
| MMLU | **55.04** | 52.64 | 47.61 | 26.33 | 32.39 | 45.14 |
| ARC-C | 46.93 | 44.8 | 35.32 | 39.33 | 39.42 | **47.87** |
| HellaSwag | 56.3 | 53.51 | 51.79 | 62.94 | **65.73** | 62.3 |
| Winogrande | 59.43 | 60.54 | 56.83 | 62.59 | **62.75** | 61.17 |
| **Math**  | | | | | |
| GSM8k | **60.2** | 50.04 | 34.8 | 2.2 | 7.05 | 34.95 |
| MATH lvl5 | **15.18** | 9.29 | 4.23 | 1.21 | 0.98 | 3.4 |
| **Science**  | | | | | |
| GPQA | **29.7** | 29.11 | 27.94 | 24.66 | 23.57 | 27.85 |
| MMLU-Pro | **30.04** | 22.99 | 18.98 | 11.31 | 11.8 | 16.11 |
| MMLU-stem | **57.12** | 50.11 | 43.74 | 27.59 | 30.19 | 40.06 |
| **Code**  | | | | | |
| HumanEval | **35.98** | 31.71 | 29.27 | 6.71 | 18.9 | 10.37 |
| HumanEval+ | **31.1** | 27.44 | 25.0 | 5.49 | 16.46 | 9.15 |
| MBPP | **52.12** | 51.06 | 40.74 | 12.7 | 35.98 | 12.43 |
| MBPP+ | **43.39** | 42.33 | 34.66 | 9.52 | 29.89 | 9.52 |

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