---
license: bsd-2-clause
license_link: LICENSE
base_model: nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16
base_model_relation: finetune
language:
  - en
library_name: transformers
pipeline_tag: text-generation
tags:
  - nemotron
  - mixture-of-experts
  - voice-agent
  - phone
  - tool-use
  - function-calling
  - conversational
  - pipecat
---

# Pipecat PhoneLLM Alpha 1

| | |
|---|---|
| **Model** | PhoneLLM Alpha 1 (`pipecat-ai/phonellm-alpha-1`) |
| **Base model** | [NVIDIA Nemotron 3 Nano 30B-A3B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16) |
| **Architecture** | Hybrid Mamba-Transformer mixture-of-experts; 30B total parameters, 3.5B active |
| **Training** | Full-parameter supervised fine-tuning with the NVIDIA NeMo framework |
| **Context length** | 262,144 tokens |
| **Precision** | bfloat16 safetensors |
| **Recommended inference settings** | `temperature=0`, thinking disabled (`chat_template_kwargs: {"enable_thinking": false}`) |
| **Serving** | vLLM or SGLang, Nemotron 3 Nano recipes; `trust_remote_code=True` |
| **Language** | English |
| **License** | [BSD 2-Clause](LICENSE); derivative of an [NVIDIA Nemotron Open Model License](LICENSE_NVIDIA.txt) work — see [License](#license) |
| **Developed by** | [Daily](https://www.daily.co/) / the [Pipecat](https://www.pipecat.ai/) team |


The Pipecat team is pleased to announce the release of [**PhoneLLM Alpha 1**](https://huggingface.co/pipecat-ai/phonellm-alpha-1), an open-weights model for voice agent use cases. 

This release is the result of our ongoing work training small, open-weights LLMs for low-latency and multi-turn agentic workloads.

When paired with transcription and text-to-speech models through a framework like [Pipecat](https://www.pipecat.ai/), PhoneLLM can handle incoming calls for financial services, healthcare, retail, and hospitality customer service, and perform common outbound calling agent tasks.

PhoneLLM runs at a fraction of the cost and latency of larger, general-purpose models, while delivering comparable performance for specific use cases. **For example, PhoneLLM performs on par with GPT 5.6 Terra, but 94% cheaper and with 1,300ms faster P95 time-to-first-token.**

PhoneLLM is an open model, so you can run it on your own infrastructure. The model is released under the BSD license, with no commercial restrictions.

We are also announcing **PhoneBench v1**, a benchmark which evaluates LLMs based on their suitability for phone agent use cases. In addition to accuracy and speaking style, we measure model latency and estimate per-minute runtime cost.

The unique combination of benchmark accuracy, low latency, and low cost makes PhoneLLM one of the most compelling options for building a voice agent.

## **Model specs**

PhoneLLM Alpha 1 is a full-parameter fine-tune of NVIDIA’s [Nemotron 3 Nano 30B-A3B model](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16), trained using the [NVIDIA NeMo](https://docs.nvidia.com/nemo-framework/index.html) framework.

Like Nemotron Nano, PhoneLLM is a mixture-of-experts (MoE) model, with 3.5B active parameters, allowing for high-speed inference at low cost.

In our PhoneBench benchmark, PhoneLLM achieves accuracy comparable to or better than most of the models commonly used for production voice agents, at lower latency and lower cost.

![PhoneBench v1 leaderboard: score, time-to-first-answer-token and cost per minute by model](images/01-phonebench-v1-leaderboard.png)
## **Why a model specifically for voice agents?**

In our work creating voice agents using Pipecat, we’ve found that there is a gap in the LLM space for models which (1) are low latency, and (2) invoke tools accurately.

The latest frontier models are optimized for use when thinking tokens are enabled. When a model reasons in this way, there is a long delay between the user’s query and the agent’s response.

We’ve also found that many models, large and small, struggle to accurately invoke tools in long, multi-turn conversations. This is especially true when thinking is disabled. LLMs will often say “Yes, I’ve booked that table for you” without actually doing it, which can lead to disastrous results and customer frustration.

PhoneLLM is specifically trained to call the right tools at the right time, without the need for thinking to be enabled.

![Before/after fine-tuning: Nemotron 3 Nano 30B vs PhoneLLM 30B Alpha 1 on the same caller turns](images/02-before-after-fine-tuning.png)

More broadly, we’re seeing a shift in the industry towards small open-weights models, fine-tuned for specific purposes, which outperform general-purpose frontier models in accuracy, inference speed, cost, and data privacy.

The Pipecat team works directly with enterprise customers to train models for specific use cases, using production agent traces and proprietary data. PhoneLLM is an example of what’s possible today, building on a strong, efficient base model like Nemotron 3 Nano.

## **PhoneBench**

When we train a new model, the first step is always to figure out how to evaluate it.

Voice agents, and LLM outputs in general, are difficult to evaluate, because the outputs are free-form and often not objectively verifiable. Speaking style, factual accuracy, and relevance to the user’s query are examples of things that can’t be checked programmatically.

Even the choice of tool calls has a subjective component: often benchmarks will expect a certain tool to be called with specific parameters at a certain time, but actually models have a high degree of flexibility about when and how they perform actions, and what information they look up.

To handle this subjectivity, PhoneBench uses a panel of LLM judges to grade model output, comparing the actions to high-quality reference samples. The judges are calibrated against human labels to ensure accuracy.

In this way, PhoneBench is able to measure detailed points of quality that would normally require human labeling: telephone speaking style, tool call accuracy, say/do consistency, factual grounding, conversation coherence, authentication and escalation discipline, and caller outcome.

The scenarios, tool lists, and system prompts in the benchmark are kept separate from the data we use to train models like PhoneLLM, so that PhoneLLM isn’t limited to the tasks it was trained on. And the benchmark verifies that the model generalizes across previously unseen scenarios, business use cases, tools lists, and prompts.

![PhoneBench: how a turn is judged (two example candidate pairs with judge rationale)](images/03-how-a-turn-is-judged.png)

### **Latency**

Accuracy is only one part of the equation. Building good agents is a full stack systems engineering challenge\! For voice agents, response latency is a critical attribute.

In general, people expect responses to happen quite quickly in voice conversations and have very low tolerance for slow responses. **“Voice-to-voice” latency needs to be around 1,500ms in most situations.** (Ideally, even faster. But we have lots of empirical data about voice agent success, and people are happy talking to an agent with a P95 voice-to-voice latency of 1,500ms.)

This voice-to-voice latency includes network overhead, audio processing, application logic, and all the inference from STT, LLM, and TTS models. 1,500ms is a fairly tight latency budget. The P95 time-to-first-token for GPT 5.6 Terra running in fast mode is about 1,900ms. So just the LLM part of a voice agent built with Terra already exceeds our latency target.

Here’s a [detailed breakdown](https://voiceaiandvoiceagents.com/#latency) of how the latency accumulates in a well-optimized voice agent that’s running on macOS and communicating via WebRTC with a voice agent server running in the cloud.

![Voice-to-voice latency budget by stage, totalling 1,293 ms](images/04-voice-to-voice-latency-budget.png)

You can see that our LLM time-to-first-token target is 650ms.

There’s a trade-off between aiming for very fast time-to-first-token, and running a model cost-effectively. Serving more concurrent inference requests lowers cost, but increases latency.

A big advantage of open weights models is that we can optimize our inference stack for voice agent use cases. We can pick optimal points on the cost-latency curve. And, because the inference servers we use are open source, we can *move* the curve by writing new code. (We write latency-optimized inference code both for LLMs and for [NVIDIA’s transcription models](https://github.com/kwindla/nemotron-voice-agent#production-streaming-asr-serving-rtx-5090--l40s-cluster).)

We chose [Nemotron 3 Nano](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16) as the base for PhoneLLM because the [Nemotron 3 architecture](https://research.nvidia.com/labs/nemotron/Nemotron-3/) scales very efficiently on modern NVIDIA hardware. We can pack quite a lot of concurrent generations on a single GPU while still maintaining excellent P95 latency.

We’ve worked with the team at [Modal](https://modal.com/) to develop optimized configurations for running PhoneLLM. More on that in the **Running the model** section, below.

### **Cost**

Estimating LLM cost for conversational agents is tricky.

Agents are long-running interactions that take place across multiple turns. Most LLM API services charge by the token, with different rates for input tokens and output tokens, cache writes, cache reads, service tiers (for example OpenAI’s “fast” mode), regional data fencing, and zero data retention.

“Cost per minute” is the natural way to model costs for production voice agents. So it’s useful to convert from estimated token costs to average cost per minute. The formula for this conversion depends on the length of conversations, size of system prompts, typical model language and thinking token patterns, cache use statistics, and a number of other elements that vary both across use cases and between individual sessions.

It’s a bit easier to calculate cost per minute if you are running the model on your own infrastructure. You’ll need to know what your target concurrency is and make assumptions about utilization.

We’ve built [a spreadsheet](https://docs.google.com/spreadsheets/d/1mj5cSV7oVY3vLToNEprCkQVVU1uofHZ-_6u779rXS7I/edit?usp=sharing) that shows the cost per minute for a number of LLMs, both APIs and self-hosted models, based on the inference patterns for each model in the PhoneBench benchmark.

![PhoneBench voice agent cost estimator spreadsheet: imputed cost per minute by model](images/05-cost-estimator-spreadsheet.png)

Feel free to copy this sheet and modify or extend it. It’s quite complicated, but both Codex and Claude are now very good at digging into large spreadsheets, explaining how they work, and adding to them.

You can see some broad patterns in these numbers. Bigger models are generally more expensive to run. Gemini 3.6 Flash is an outlier, because even with thinking set to minimal it produces a lot of thinking tokens. 

Self-hosting can be cheaper than using an API, but the large inference providers are good at what they do and operate at very large economies of scale. The path to saving money by self-hosting is model size arbitrage: use a smaller model that’s a perfect fit for your use case instead of a bigger, more general-purpose model.

Hosting a model cost-effectively requires utilizing each GPU cluster as much as possible, up to the point where performance degrades beyond our target metrics. For a voice agent, we want to pin each session to a single cluster so that caching is easier. And our most important metric is latency.

Here’s a summary of concurrency benchmarking sweeps for each of the models in the spreadsheet. We pick a “not to exceed” P95 time-to-first-answer-token target. Then we run simulations to find the maximum concurrency that stays below that target, for a specific agent workload.

![P95 TTFAT crossover at a 600 ms target: max concurrency per model and hardware](images/06-ttfat-crossover-600ms.png)

Nemotron 3 Nano (and PhoneLLM, which is the same architecture) scales very well. Our max concurrency here is 44 processes on each NVIDIA B200. The way this sweep is constructed, that translates to 88 agent processes pinned to each B200 node.

On Modal, the base cost of a B200 is $6.2496 per hour. Region pinning adds a 1.5× multiplier, bringing the cost to $9.3744/hour. We target 70% utilization (divide by 0.70), so we have an effective cost of $13.392/hour, or $0.2232/minute.

Dividing $0.2232/minute by 88 concurrent agents equals a per-minute agent cost of $0.00025.

We’re able to achieve this high level of efficiency partly because Nemotron 3 Nano is a very efficient Mamba-Transformer Mixture of Experts architecture. But also because the team at Modal developed workload-specific optimizations for PhoneLLM running on their B200 infrastructure. Which brings us to …

### **Weights and Deployment**

The weights for [PhoneLLM Alpha 1 are on HuggingFace here](https://huggingface.co/pipecat-ai/phonellm-alpha-1). You can run PhoneLLM anywhere you can run a 30B-parameter open weights model.

We use both SGLang and vLLM to serve models in production. PhoneLLM fits nicely and runs very fast on a single NVIDIA B200, with plenty of room for long contexts and context cache. Single-request TTFT P95 is below 100ms on a B200.

The standard Nemotron 3 Nano configurations are good starting points, if you’re experimenting with PhoneLLM:

* SGLang [Nemotron 3 Nano configuration](https://docs.sglang.io/cookbook/autoregressive/NVIDIA/Nemotron3-Nano)  
* vLLM [Nemotron 3 Nano configurations](https://recipes.vllm.ai/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16)

**Important: set temperature to 0 and disable thinking. These two settings align with how the model was trained.**

### **Deploying on Modal**

PhoneLLM is also available to deploy via [Modal AutoEndpoints](https://modal.com/docs/guide/endpoints). You can spin up a deployment in just a few clicks at your [Endpoints dashboard](https://modal.com/endpoints/) or by running this command with the Modal CLI.

```
modal endpoint create --model pipecat-ai/phonellm-alpha-1
```

Modal leveraged their Auto Endpoints system to optimize throughput while maintaining very low engine TTFAT for conversational voice workloads specifically using representative data provided by the Pipecat team. Compared to the generic configuration in the vLLM cookbook, this configuration approximately doubles the max agent concurrency at our target sub-600ms P95 TTFAT metric.


## **A few more things**
We created PhoneLLM using Daily’s end-to-end model training stack. Training a good model requires:

1. Collecting or synthetically generating good training data  
2. Building evaluation environments  
3. Running optimized training processes

We started building this tooling in 2024 to support our work [evaluating models](https://github.com/kwindla/aiewf-eval) for voice use cases, and training small native audio models like the [Pipecat Smart Turn](https://github.com/pipecat-ai/smart-turn) turn detection model.

This year, as open weights models have improved to the point where we can use these new small, open models for production voice use cases, we’ve accelerated our work on tooling for model training and customization.

PhoneLLM is a relatively general model, designed to be good at a variety of typical customer support tasks. We can also train models for specific use cases. Each individual training run is affordable enough that updating model weights every month (or even more often) is now a viable strategy.

We think that in the near future, most production agents will continually improve, using feedback loops built around targeted evals and production instrumentation. 

* Prompts and context engineering are easy to change and A/B test.  
* As the Modal team is demonstrating, inference optimization can significantly lower the cost of running agents in production.  
* We can now train small models to perform very well on tasks with well-defined conversation goals and tool definitions.

If you’re interested in building agents that benefit from continually improved performance metrics and cost curves, come talk to us.

If you want to explore building voice agents, the [Pipecat docs](https://www.pipecat.ai/) are a good starting point, and the [Voice AI Illustrated Primer](https://voiceaiandvoiceagents.com/) is a good deep dive.

Thanks to the fantastic teams at NVIDIA and Modal for the base models and infrastructure that made PhoneLLM possible.

## **License**

PhoneLLM Alpha 1 is released under the [BSD 2-Clause License](LICENSE).

PhoneLLM is a derivative work of [NVIDIA Nemotron 3 Nano 30B-A3B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16), which is licensed under the [NVIDIA Nemotron Open Model License](LICENSE_NVIDIA.txt). Under Section 3 (Redistribution) of that license, if you redistribute this model or your own derivatives of it, you must (a) include a copy of the NVIDIA Nemotron Open Model License, and (b) retain the NVIDIA copyright and attribution notices. Our BSD 2-Clause terms apply to our modifications and to the model as a whole, as Section 3 permits; the NVIDIA license continues to apply to the underlying Nemotron work. "Nemotron" and "NVIDIA" are trademarks of NVIDIA Corporation, used here only to describe the origin of the base model.
