# Ground-truth annotation bundles — issue #57 (R104)

Annotation set: 20 repos × 3 axes = 60 cells
Axes: i = model-instance structure (SINGLE|MULTI|UNKNOWN), ii = topology (ORCH-WORKER|TEAM|PIPELINE|SINGLE|UNKNOWN), iii = judge presence (JUDGE|NO|UNKNOWN)

---
## microsoft/autogen  (★60717, tier_a framework — groupchat orchestration)
frameworks: ['autogen/ag2', 'langchain', 'langgraph'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=2319
agent-ish top dirs: []

### README (head)
```
<a name="readme-top"></a>

<div align="center">
<img src="https://microsoft.github.io/autogen/0.2/img/ag.svg" alt="AutoGen Logo" width="100">

[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/cloudposse.svg?style=social&label=Follow%20%40pyautogen)](https://twitter.com/pyautogen)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Company?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/company/105812540)
[![Discord](https://img.shields.io/badge/discord-chat-green?logo=discord)](https://aka.ms/autogen-discord)
[![Documentation](https://img.shields.io/badge/Documentation-AutoGen-blue?logo=read-the-docs)](https://microsoft.github.io/autogen/)
[![Blog](https://img.shields.io/badge/Blog-AutoGen-blue?logo=blogger)](https://devblogs.microsoft.com/autogen/)

</div>

# AutoGen [![Maintenance Mode](https://img.shields.io/badge/status-maintenance%20mode-orange)](https://github.com/microsoft/agent-framework)

**AutoGen** is a framework for creating multi-agent AI applications that can act autonomously or work alongside humans.

> [!CAUTION]
> **⚠️ Maintenance Mode**
>
> AutoGen is now in maintenance mode. It will not receive new features or enhancements and is community managed going forward.
>
> New users should start with [Microsoft Agent Framework](https://github.com/microsoft/agent-framework). Existing users are encouraged to migrate using the [AutoGen → Microsoft Agent Framework migration guide](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/).
>
> Microsoft Agent Framework (MAF) is the enterprise‑ready successor to AutoGen. Microsoft Agent FrameworkAF in now available as a production-ready release: stable APIs, and a commitment to long-term support. Whether you're building a single assistant or orchestrating a fleet of specialized agents, Microsoft Agent Framework 1.0 gives you enterprise-grade multi-agent orchestration, multi-provider model support, and cross-runtime interoperability via A2A and MCP.

## Installation

AutoGen requires **Python 3.10 or later**.

```bash
# Install AgentChat and OpenAI client from Extensions
pip install -U "autogen-agentchat" "autogen-ext[openai]"
```

The current stable version can be found in the [releases](https://github.com/microsoft/autogen/releases). If you are upgrading from AutoGen v0.2, please refer to the [Migration Guide](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/migration-guide.html) for detailed instructions on how to update your code and configurations.

```bash
# Install AutoGen Studio for no-code GUI
pip install -U "autogenstudio"
```

## Quickstart

The following samples call OpenAI API, so you first need to create an account and export your key as `export OPENAI_API_KEY="sk-..."`.

### Hello World

Create an assistant agent using OpenAI's GPT-4o model. See [other supported models](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/models.html).

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main() -> None:
    model_client = OpenAIChatCompletionClient(model="gpt-4.1")
    agent = AssistantAgent("assistant", model_client=model_client)
    print(await agent.run(task="Say 'Hello World!'"))
    await model_client.close()
```

---
## crewAIInc/crewAI  (★57865, tier_a framework — crew/process)
frameworks: ['crewai', 'langchain'] | v1: i=MULTI ii=team iii=JUDGE | probed=8 | tree=32106
agent-ish top dirs: ['AGENTS.md']

### README (head)
```
<p align="center">
  <a href="https://github.com/crewAIInc/crewAI">
    <img src="docs/images/crewai_logo.png" width="600px" alt="Open source Multi-AI Agent orchestration framework">
  </a>
</p>
<p align="center" style="display: flex; justify-content: center; gap: 20px; align-items: center;">
  <a href="https://trendshift.io/repositories/11239" target="_blank">
    <img src="https://trendshift.io/api/badge/repositories/11239" alt="crewAIInc%2FcrewAI | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/>
  </a>
</p>

<p align="center">
  <a href="https://crewai.com">Homepage</a>
  ·
  <a href="https://crewai.com/open-source">Open Source</a>
  ·
  <a href="https://docs.crewai.com">Docs</a>
  ·
  <a href="https://app.crewai.com">Start Cloud Trial</a>
  ·
  <a href="https://blog.crewai.com">Blog</a>
  ·
  <a href="https://community.crewai.com">Forum</a>
</p>

<p align="center">
  <a href="https://github.com/crewAIInc/crewAI">
    <img src="https://img.shields.io/github/stars/crewAIInc/crewAI" alt="GitHub Repo stars">
  </a>
  <a href="https://github.com/crewAIInc/crewAI/network/members">
    <img src="https://img.shields.io/github/forks/crewAIInc/crewAI" alt="GitHub forks">
  </a>
  <a href="https://github.com/crewAIInc/crewAI/issues">
    <img src="https://img.shields.io/github/issues/crewAIInc/crewAI" alt="GitHub issues">
  </a>
  <a href="https://github.com/crewAIInc/crewAI/pulls">
    <img src="https://img.shields.io/github/issues-pr/crewAIInc/crewAI" alt="GitHub pull requests">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT">
  </a>
</p>

<p align="center">
  <a href="https://pypi.org/project/crewai/">
    <img src="https://img.shields.io/pypi/v/crewai" alt="PyPI version">
  </a>
  <a href="https://pypi.org/project/crewai/">
    <img src="https://img.shields.io/pypi/dm/crewai" alt="PyPI downloads">
  </a>
  <a href="https://twitter.com/crewAIInc">
    <img src="https://img.shields.io/twitter/follow/crewAIInc?style=social" alt="Twitter Follow">
  </a>
</p>

### Fast and Flexible Multi-Agent Automation Framework

> CrewAI is an open-source Python framework with high-level abstractions and low-level APIs for building production-ready multi-agent workflows.
> It gives developers autonomous agent collaboration through Crews and precise, event-driven control through Flows.

```

---
## langchain-ai/langgraph  (★40772, tier_a framework — graph topology)
frameworks: ['langchain', 'langgraph'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=832
agent-ish top dirs: ['AGENTS.md']

### README (head)
```
<div align="center">
  <a href="https://www.langchain.com/langgraph">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset=".github/images/logo-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset=".github/images/logo-light.svg">
      <img alt="LangGraph Logo" src=".github/images/logo-dark.svg" width="50%">
    </picture>
  </a>
</div>

<div align="center">
  <h3>Low-level orchestration framework for building stateful agents.</h3>
</div>

<div align="center">
  <a href="https://opensource.org/licenses/MIT" target="_blank"><img src="https://img.shields.io/pypi/l/langgraph" alt="PyPI - License"></a>
  <a href="https://pypistats.org/packages/langgraph" target="_blank"><img src="https://img.shields.io/pepy/dt/langgraph" alt="PyPI - Downloads"></a>
  <a href="https://pypi.org/project/langgraph/" target="_blank"><img src="https://img.shields.io/pypi/v/langgraph.svg?label=%20" alt="Version"></a>
  <a href="https://x.com/langchain_oss" target="_blank"><img src="https://img.shields.io/twitter/url/https/twitter.com/langchain_oss.svg?style=social&label=Follow%20%40LangChain" alt="Twitter / X"></a>
</div>

<br>

Trusted by companies shaping the future of agents – including Klarna, Replit, Elastic, and more – LangGraph is a low-level orchestration framework for building, managing, and deploying long-running, stateful agents.

```bash
pip install -U langgraph
```

> [!TIP]
> If you're looking to quickly build agents, check out **[Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview)** — a higher-level package built on LangGraph for agents that can plan, use subagents, and leverage file systems for complex tasks.

For an equivalent JS/TS library, check out [LangGraph.js](https://github.com/langchain-ai/langgraphjs) and the [JS docs](https://docs.langchain.com/oss/javascript/langgraph/overview).

## Why use LangGraph?

LangGraph provides low-level supporting infrastructure for *any* long-running, stateful workflow or agent:

- **[Durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution)** — Build agents that persist through failures and can run for extended periods, automatically resuming from exactly where they left off.
- **[Human-in-the-loop](https://docs.langchain.com/oss/python/langgraph/interrupts)** — Seamlessly incorporate human oversight by inspecting and modifying agent state at any point during execution.
- **[Comprehensive memory](https://docs.langchain.com/oss/python/langgraph/memory)** — Create truly stateful agents with both short-term working memory for ongoing reasoning and long-term persistent memory across sessions.
- **[Debugging with LangSmith](https://www.langchain.com/langsmith)** — Gain deep visibility into complex agent behavior with visualization tools that trace execution paths, capture state transitions, and provide detailed runtime metrics.
- **[Production-ready deployment](https://docs.langchain.com/langsmith/deployments)** — Deploy sophisticated agent systems confidently with scalable infrastructure designed to handle the unique challenges of stateful, long-running workflows.

> [!TIP]
> For developing, debugging, and deploying AI agents and LLM applications, see [LangSmith](https://docs.langchain.com/langsmith/home).

## LangGraph ecosystem

While LangGraph can be used standalone, it also integrates seamlessly with any LangChain product, giving developers a full suite of tools for building agents.

To improve your LLM application development, pair LangGraph with:

- [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) – Build agents that can plan, use subagents, and leverage file systems for complex tasks.
- [LangChain](https://docs.langchain.com/oss/python/langchain/overview) – Provides integrations and composable components to streamline LLM application development.
- [LangSmith](https://www.langchain.com/langsmith) – Helpful for agent evals and observability. Debug poor-performing LLM app runs, evaluate agent trajectories, gain visibility in production, and improve performance over time.
- [LangSmith Deployment](https://docs.langchain.com/langsmith/deployments) – Deploy and scale agents effortlessly with a purpose-built deployment platform for long-running, stateful workflows. Discover, reuse, configure, and share agents across teams – and iterate quickly with visual prototyping in [LangSmith Studio](https://docs.langchain.com/langsmith/studio).

---

```

---
## FoundationAgents/MetaGPT  (★70117, tier_a framework — SOP roles)
frameworks: ['metagpt'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=1515
agent-ish top dirs: []

### README (head)
```

# MetaGPT: The Multi-Agent Framework

<p align="center">
<a href=""><img src="docs/resources/MetaGPT-new-log.png" alt="MetaGPT logo: Enable GPT to work in a software company, collaborating to tackle more complex tasks." width="150px"></a>
</p>

<p align="center">
[ <b>En</b> |
<a href="docs/README_CN.md">中</a> |
<a href="docs/README_FR.md">Fr</a> |
<a href="docs/README_JA.md">日</a> ]
<b>Assign different roles to GPTs to form a collaborative entity for complex tasks.</b>
</p>

<p align="center">
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
<a href="https://discord.gg/DYn29wFk9z"><img src="https://img.shields.io/badge/Join-Discord-gGnrXvVz7a?logo=discord" alt="Discord Follow"></a>
<a href="https://twitter.com/MetaGPT_"><img src="https://img.shields.io/twitter/follow/MetaGPT?style=social" alt="Twitter Follow"></a>
</p>

<h4 align="center">
    
</h4>

## News

🚀 Mar. 10, 2025: 🎉 [mgx.dev](https://mgx.dev/) is the #1 Product of the Week on @ProductHunt! 🏆

🚀 Mar. &nbsp; 4, 2025: 🎉 [mgx.dev](https://mgx.dev/) is the #1 Product of the Day on @ProductHunt! 🏆

🚀 Feb. 19, 2025: Today we are officially launching our natural language programming product: [MGX (MetaGPT X)](https://mgx.dev/) - the world's first AI agent development team. More details on [Twitter](https://x.com/MetaGPT_/status/1892199535130329356).

🚀 Feb. 17, 2025: We introduced two papers: [SPO](https://arxiv.org/pdf/2502.06855) and [AOT](https://arxiv.org/pdf/2502.12018), check the [code](examples)!

🚀 Jan. 22, 2025: Our paper [AFlow: Automating Agentic Workflow Generation](https://openreview.net/forum?id=z5uVAKwmjf) accepted for **oral presentation (top 1.8%)** at ICLR 2025, **ranking #2** in the LLM-based Agent category.

👉👉 [Earlier news](docs/NEWS.md) 

## Software Company as Multi-Agent System

1. MetaGPT takes a **one line requirement** as input and outputs **user stories / competitive analysis / requirements / data structures / APIs / documents, etc.**
2. Internally, MetaGPT includes **product managers / architects / project managers / engineers.** It provides the entire process of a **software company along with carefully orchestrated SOPs.**
   1. `Code = SOP(Team)` is the core philosophy. We materialize SOP and apply it to teams composed of LLMs.

![A software company consists of LLM-based roles](docs/resources/software_company_cd.jpeg)

<p align="center">Software Company Multi-Agent Schematic (Gradually Implementing)</p>

## Get Started

### Installation

> Ensure that Python 3.9 or later, but less than 3.12, is installed on your system. You can check this by using: `python --version`.  
> You can use conda like this: `conda create -n metagpt python=3.9 && conda activate metagpt`

```bash
pip install --upgrade metagpt
# or `pip install --upgrade git+https://github.com/geekan/MetaGPT.git`
# or `git clone https://github.com/geekan/MetaGPT && cd MetaGPT && pip install --upgrade -e .`
```

---
## OpenBMB/AgentVerse  (★5117, tier_a framework — environment/simulation)
frameworks: ['langchain'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=5408
agent-ish top dirs: ['agentverse', 'agentverse_command', 'README_tasksolving_cases.md']

### README (head)
```
<h1 align="center"> 🤖 AgentVerse 🪐 </h1>

<!--
<h3 align="center">
    <p>A Framework for Multi-LLM Environment Simulation</p>
</h3>
-->

<p align="center">
    <a href="https://github.com/OpenBMB/AgentVerse/blob/main/LICENSE">
        <img alt="License: Apache2" src="https://img.shields.io/badge/License-Apache_2.0-green.svg">
    </a>
    <a href="https://www.python.org/downloads/release/python-3916/">
        <img alt="Python Version" src="https://img.shields.io/badge/python-3.9+-blue.svg">
    </a>
    <a href="https://github.com/OpenBMB/AgentVerse/actions/">
        <img alt="Build" src="https://img.shields.io/github/actions/workflow/status/OpenBMB/AgentVerse/test.yml">
    </a>
    <a href="https://github.com/psf/black">
        <img alt="Code Style: Black" src="https://img.shields.io/badge/code%20style-black-black">
<!--     </a>
    <a href="https://github.com/OpenBMB/AgentVerse/issues">
        <img alt="Contributions: Welcome" src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat">
    </a> -->
    <a href="https://huggingface.co/AgentVerse">
        <img alt="HuggingFace" src="https://img.shields.io/badge/hugging_face-play-yellow">
    </a>
    <a href="https://discord.gg/gDAXfjMw">
        <img alt="Discord" src="https://img.shields.io/badge/AgentVerse-Discord-purple?style=flat">
    </a>
    
    
</p>

<p align="center">
<img src="./imgs/title.png" width="512">
</p>

<p align="center">
    【<a href="https://arxiv.org/abs/2308.10848">Paper</a>】 
</p>

<p align="center">
    【English | <a href="README_zh.md">Chinese</a>】 
</p>

**AgentVerse** is designed to facilitate the deployment of multiple LLM-based agents in various applications. AgentVerse primarily provides two frameworks: **task-solving** and **simulation**. 

- Task-solving: This framework assembles multiple agents as an automatic multi-agent system ([AgentVerse-Tasksolving](https://arxiv.org/pdf/2308.10848.pdf), [Multi-agent as system](https://arxiv.org/abs/2309.02427)) to collaboratively accomplish the corresponding tasks. 
Applications: software development system, consulting system, etc. 

<p align="center">
<img width="616" alt="Screen Shot 2023-09-01 at 12 08 57 PM" src="https://github.com/OpenBMB/AgentVerse/assets/11704492/6db1c907-b7fc-42f9-946c-89853a28f386">
</p>

- Simulation: This framework allows users to set up custom environments to observe behaviors among, or interact with, multiple agents. ⚠️⚠️⚠️ We're refactoring the code. If you require a stable version that exclusively supports simulation framework, you can use [`release-0.1`](https://github.com/OpenBMB/AgentVerse/tree/release-0.1) branch. Applications: game, social behavior research of LLM-based agents, etc.

<p align="center">
<img width="616" alt="Screen Shot 2023-10-16 at 10 53 49 PM" src="https://github.com/OpenBMB/AgentVerse/assets/11704492/4102d1e2-3fe7-4656-aa2c-a218ce1f2c95">
</p>
```

---
## camel-ai/camel  (★17656, tier_a framework — role-play agents)
frameworks: ['camel'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=2502
agent-ish top dirs: []

### README (head)
```
<div align="center">
  <a href="https://www.camel-ai.org/">
    <img src="docs/images/banner.png" alt="Banner">
  </a>
</div>

</br>

<div align="center">

[![Documentation][docs-image]][docs-url]
[![Discord][discord-image]][discord-url]
[![X][x-image]][x-url]
[![Reddit][reddit-image]][reddit-url]
[![Wechat][wechat-image]][wechat-url]
[![Hugging Face][huggingface-image]][huggingface-url]
[![Star][star-image]][star-url]
[![Package License][package-license-image]][package-license-url]
[![PyPI Download][package-download-image]][package-download-url]
[![][join-us-image]][join-us]

<a href="https://trendshift.io/repositories/649" target="_blank"><img src="https://trendshift.io/api/badge/repositories/649" alt="camel-ai/camel | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[English](README.md) |
[简体中文](README.zh.md) |
[日本語](README.ja.md)

</div>


<hr>

<div align="center">
<h4 align="center">

[Community](https://github.com/camel-ai/camel#community) |
[Installation](https://github.com/camel-ai/camel#installation) |
[Examples](https://github.com/camel-ai/camel/tree/HEAD/examples) |
[Paper](https://arxiv.org/abs/2303.17760) |
[Citation](https://github.com/camel-ai/camel#citation) |
[Contributing](https://github.com/camel-ai/camel#contributing-to-camel-) |
[CAMEL-AI](https://www.camel-ai.org/)

</h4>

<p style="line-height: 1.5; text-align: center;"> 🐫 CAMEL is an open-source community dedicated to finding the scaling laws of agents. We believe that studying these agents on a large scale offers valuable insights into their behaviors, capabilities, and potential risks. To facilitate research in this field, we implement and support various types of agents, tasks, prompts, models, and simulated environments.</p>


<br>


Join us ([*Discord*](https://discord.camel-ai.org/) or [*WeChat*](https://ghli.org/camel/wechat.png)) in pushing the boundaries of finding the scaling laws of agents.

🌟 Star CAMEL on GitHub and be instantly notified of new releases.

</div>

<div align="center">
    <img src="docs/images/stars.gif" alt="Star">
  </a>
```

---
## openai/openai-agents-python  (★29094, tier_a framework — handoffs)
frameworks: ['openai-agents'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=1826
agent-ish top dirs: ['.agents', 'AGENTS.md']

### README (head)
```
# OpenAI Agents SDK [![PyPI](https://img.shields.io/pypi/v/openai-agents?label=pypi%20package)](https://pypi.org/project/openai-agents/)

The OpenAI Agents SDK is a lightweight yet powerful framework for building multi-agent workflows. It is provider-agnostic, supporting the OpenAI Responses and Chat Completions APIs, as well as 100+ other LLMs.

<img src="https://cdn.openai.com/API/docs/images/orchestration.png" alt="Image of the Agents Tracing UI" style="max-height: 803px;">

> [!NOTE]
> Looking for the JavaScript/TypeScript version? Check out [Agents SDK JS/TS](https://github.com/openai/openai-agents-js).

### Core concepts:

1. [**Agents**](https://openai.github.io/openai-agents-python/agents): LLMs configured with instructions, tools, guardrails, and handoffs
1. [**Sandbox agents**](https://openai.github.io/openai-agents-python/sandbox_agents): Agents preconfigured to work with a container to perform work over long time horizons.
1. [**Realtime agents**](https://openai.github.io/openai-agents-python/realtime/quickstart/): Build powerful voice agents with `gpt-realtime-2.1` and full agent features
1. [**Voice agents**](https://openai.github.io/openai-agents-python/voice/quickstart/): Build voice pipelines that combine speech-to-text, an agent workflow, and text-to-speech
1. **[Agents as tools](https://openai.github.io/openai-agents-python/tools/#agents-as-tools) / [Handoffs](https://openai.github.io/openai-agents-python/handoffs/)**: Delegating to other agents for specific tasks
1. [**Tools**](https://openai.github.io/openai-agents-python/tools/): Various Tools let agents take actions (functions, MCP, hosted tools)
1. [**Guardrails**](https://openai.github.io/openai-agents-python/guardrails/): Configurable safety checks for input and output validation
1. [**Human in the loop**](https://openai.github.io/openai-agents-python/human_in_the_loop/): Built-in mechanisms for involving humans across agent runs
1. [**Sessions**](https://openai.github.io/openai-agents-python/sessions/): Automatic conversation history management across agent runs
1. [**Tracing**](https://openai.github.io/openai-agents-python/tracing/): Built-in tracking of agent runs, allowing you to view, debug and optimize your workflows

Explore the [examples](https://github.com/openai/openai-agents-python/tree/main/examples) directory to see the SDK in action, and read our [documentation](https://openai.github.io/openai-agents-python/) for more details.

## Get started

To get started, set up your Python environment (Python 3.10 or newer required), and then install OpenAI Agents SDK package.

### venv

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install openai-agents
```

For voice support, install with the optional `voice` group: `pip install 'openai-agents[voice]'`. For Redis session support, install with the optional `redis` group: `pip install 'openai-agents[redis]'`.

### uv

If you're familiar with [uv](https://docs.astral.sh/uv/), installing the package would be even easier:

```bash
uv init
uv add openai-agents
```

For voice support, install with the optional `voice` group: `uv add 'openai-agents[voice]'`. For Redis session support, install with the optional `redis` group: `uv add 'openai-agents[redis]'`.

## Run your first agents

The SDK supports four primary ways to run agents. Set the `OPENAI_API_KEY` environment variable before running any of these examples.

### Run a text agent

Use a text `Agent` for workflows that do not need a persistent realtime connection or a sandbox workspace.

```python
from agents import Agent, Runner

```

---
## huggingface/smolagents  (★29070, tier_a framework — code agents)
frameworks: ['smolagents'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=225
agent-ish top dirs: ['AGENTS.md']

### README (head)
```
<!---
Copyright 2024 The HuggingFace Team. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<p align="center">
    <!-- Uncomment when CircleCI is set up
    <a href="https://circleci.com/gh/huggingface/accelerate"><img alt="Build" src="https://img.shields.io/circleci/build/github/huggingface/transformers/master"></a>
    -->
    <a href="https://github.com/huggingface/smolagents/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/huggingface/smolagents.svg?color=blue"></a>
    <a href="https://huggingface.co/docs/smolagents"><img alt="Documentation" src="https://img.shields.io/website/http/huggingface.co/docs/smolagents/index.html.svg?down_color=red&down_message=offline&up_message=online"></a>
    <a href="https://github.com/huggingface/smolagents/releases"><img alt="GitHub release" src="https://img.shields.io/github/release/huggingface/smolagents.svg"></a>
    <a href="https://github.com/huggingface/smolagents/blob/main/CODE_OF_CONDUCT.md"><img alt="Contributor Covenant" src="https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg"></a>
    <a href="https://deepwiki.com/huggingface/smolagents"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>

<h3 align="center">
  <div style="display:flex;flex-direction:row;">
    <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/smolagents/smolagents.png" alt="Hugging Face mascot as James Bond" width=400px>
    <p>Agents that think in code!</p>
  </div>
</h3>

`smolagents` is a library that enables you to run powerful agents in a few lines of code. It offers:

✨ **Simplicity**: the logic for agents fits in ~1,000 lines of code (see [agents.py](https://github.com/huggingface/smolagents/blob/main/src/smolagents/agents.py)). We kept abstractions to their minimal shape above raw code!

🧑‍💻 **First-class support for Code Agents**. Our [`CodeAgent`](https://huggingface.co/docs/smolagents/reference/agents#smolagents.CodeAgent) writes its actions in code (as opposed to "agents being used to write code"). To make it secure, we support executing in sandboxed environments via [Blaxel](https://blaxel.ai), [E2B](https://e2b.dev/), [Modal](https://modal.com/), or Docker.

🤗 **Hub integrations**: you can [share/pull tools or agents to/from the Hub](https://huggingface.co/docs/smolagents/reference/tools#smolagents.Tool.from_hub) for instant sharing of the most efficient agents!

🌐 **Model-agnostic**: smolagents supports any LLM. It can be a local `transformers` or `ollama` model, one of [many providers on the Hub](https://huggingface.co/blog/inference-providers), or any model from OpenAI, Anthropic and many others via our [LiteLLM](https://www.litellm.ai/) integration.

👁️ **Modality-agnostic**: Agents support text, vision, video, even audio inputs! Cf [this tutorial](https://huggingface.co/docs/smolagents/examples/web_browser) for vision.

🛠️ **Tool-agnostic**: you can use tools from any [MCP server](https://huggingface.co/docs/smolagents/reference/tools#smolagents.ToolCollection.from_mcp), from [LangChain](https://huggingface.co/docs/smolagents/reference/tools#smolagents.Tool.from_langchain), you can even use a [Hub Space](https://huggingface.co/docs/smolagents/reference/tools#smolagents.Tool.from_space) as a tool.

Full documentation can be found [here](https://huggingface.co/docs/smolagents/index).

> [!NOTE]
> Check out our [launch blog post](https://huggingface.co/blog/smolagents) to learn more about `smolagents`!

## Quick demo

First install the package with a default set of tools:
```bash
pip install "smolagents[toolkit]"
```
Then define your agent, give it the tools it needs and run it!
```py
```

---
## Significant-Gravitas/AutoGPT  (★187027, tier_b app — self-described agent platform)
frameworks: ['autogpt', 'google-adk', 'langchain', 'langgraph', 'openai-agents'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=7417
agent-ish top dirs: ['.agents', '.pr_agent.toml', 'AGENTS.md']

### README (head)
```
<p align="center">
  <a href="https://platform.agpt.co/signup?utm_source=github&amp;utm_medium=referral&amp;utm_campaign=autogpt_readme&amp;utm_content=hero_banner">
    <img src="docs/home/.gitbook/assets/Banner_image.png" alt="AutoGPT" width="100%" />
  </a>
</p>

<h1 align="center">AutoGPT — AI agents that finish the work</h1>

<p align="center">
  <strong>Get 10 hours back every week.</strong><br />
  Describe what you want done. AutoGPT builds the agent, runs it, and reports back.
</p>

<p align="center">
  <a href="https://platform.agpt.co/signup?utm_source=github&amp;utm_medium=referral&amp;utm_campaign=autogpt_readme&amp;utm_content=header_get_started"><strong>Get started</strong></a>
  ·
  <a href="https://platform.agpt.co/tour?utm_source=github&amp;utm_medium=referral&amp;utm_campaign=autogpt_readme&amp;utm_content=tour_header">Tour</a>
  ·
  <a href="https://agpt.co/pricing?utm_source=github&amp;utm_medium=referral&amp;utm_campaign=autogpt_readme&amp;utm_content=header_pricing">Pricing</a>
  ·
  <a href="https://docs.agpt.co">Docs</a>
  ·
  <a href="https://discord.gg/autogpt">Discord</a>
  ·
  <a href="#self-host-autogpt">Self-host</a>
</p>

<p align="center">
  <a href="https://discord.gg/autogpt">
    <img src="https://img.shields.io/badge/Discord-join-5865F2?logo=discord&logoColor=white" alt="Join Discord" />
  </a>
  <a href="https://docs.agpt.co">
    <img src="https://img.shields.io/badge/Docs-read-0A7AFF?logo=gitbook&logoColor=white" alt="Read the docs" />
  </a>
</p>

---

## The open-source platform for AI agents

AutoGPT lets you build, deploy, and run AI agents that carry out complete workflows. Describe an outcome in plain English or shape every step in the visual builder, then run the agent on demand, on a schedule, or from a trigger.

**185,000+ GitHub stars. Cited by:**

| | |
|---|---|
| “Next frontier of prompt engineering imo: ‘AutoGPTs’.” | **Andrej Karpathy**, founding member of OpenAI |
| “If you have a phone you can run AutoGPT. You don't even need to learn how to code.” | **Amjad Masad**, co-founder & CEO of Replit |
| “AutoGPT might be the next big step in AI.” | **Lior Alexander**, CEO of AlphaSignal |

---

## Four surfaces, one platform

<table>
  <tr>
    <td width="50%" align="center" valign="top">
      <a href="https://agpt.co/product/autopilot/?utm_source=github&amp;utm_medium=referral&amp;utm_campaign=autogpt_readme&amp;utm_content=autopilot">
        <img src="docs/content/imgs/readme/autogpt_autopilot_chat.jpg" alt="AutoPilot chat creating an AutoGPT agent" />
      </a>
```

---
## assafelovic/gpt-researcher  (★29214, tier_b app — research agents (langgraph))
frameworks: ['autogen/ag2', 'langchain', 'langgraph'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=999
agent-ish top dirs: ['deep_agents', 'multi_agents']

### README (head)
```
<div align="center" id="top">

<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">

####

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev)
[![Discord](https://img.shields.io/discord/1127851779011391548?logo=discord&logoColor=white&label=Discord&color=34b76a&style=for-the-badge)](https://discord.gg/QgZXvJAccX)


[![PyPI version](https://img.shields.io/pypi/v/gpt-researcher?logo=pypi&logoColor=white&style=flat)](https://badge.fury.io/py/gpt-researcher)
![GitHub Release](https://img.shields.io/github/v/release/assafelovic/gpt-researcher?style=flat&logo=github)
[![Open In Colab](https://img.shields.io/static/v1?message=Open%20in%20Colab&logo=googlecolab&labelColor=grey&color=yellow&label=%20&style=flat&logoSize=40)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)
[![Docker Image Version](https://img.shields.io/docker/v/elestio/gpt-researcher/latest?arch=amd64&style=flat&logo=docker&logoColor=white&color=1D63ED)](https://hub.docker.com/r/gptresearcher/gpt-researcher)
[![Skill](https://img.shields.io/badge/Claude%20Skill-skills.sh-blueviolet?style=flat&logo=anthropic&logoColor=white)](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)

[English](README.md) | [中文](README-zh_CN.md) | [日本語](README-ja_JP.md) | [한국어](README-ko_KR.md)

</div>

# 🔎 GPT Researcher

**GPT Researcher the first open deep research agent designed for both web and local research on any given task.** 

The agent produces detailed, factual, and unbiased research reports with citations. GPT Researcher provides a full suite of customization options to create tailor made and domain specific research agents. Inspired by the recent [Plan-and-Solve](https://arxiv.org/abs/2305.04091) and [RAG](https://arxiv.org/abs/2005.11401) papers, GPT Researcher addresses misinformation, speed, determinism, and reliability by offering stable performance and increased speed through parallelized agent work.

**Our mission is to empower individuals and organizations with accurate, unbiased, and factual information through AI.**

## Why GPT Researcher?

- Objective conclusions for manual research can take weeks, requiring vast resources and time.
- LLMs trained on outdated information can hallucinate, becoming irrelevant for current research tasks.
- Current LLMs have token limitations, insufficient for generating long research reports.
- Limited web sources in existing services lead to misinformation and shallow results.
- Selective web sources can introduce bias into research tasks.

## Demo
<a href="https://www.youtube.com/watch?v=f60rlc_QCxE" target="_blank" rel="noopener">
  <img src="https://github.com/user-attachments/assets/ac2ec55f-b487-4b3f-ae6f-b8743ad296e4" alt="Demo video" width="800" target="_blank" />
</a>

## Install as Claude Skill

Extend Claude's deep research capabilities by installing GPT Researcher as a [Claude Skill](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher):

```bash
npx skills add assafelovic/gpt-researcher
```

Once installed, Claude can leverage GPT Researcher's deep research capabilities directly within your conversations.

## Architecture

The core idea is to utilize 'planner' and 'execution' agents. The planner generates research questions, while the execution agents gather relevant information. The publisher then aggregates all findings into a comprehensive report.

<div align="center">
<img align="center" height="600" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/4ac896fd-63ab-4b77-9688-ff62aafcc527">
</div>
```

---
## mem0ai/mem0  (★64416, tier_b app — agent memory layer)
frameworks: ['langchain', 'openai-agents'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=2083
agent-ish top dirs: ['.agents', 'AGENTS.md', 'evaluation']

### README (head)
```
<p align="center">
  <a href="https://github.com/mem0ai/mem0">
    <img src="docs/images/banner-sm.png" width="800px" alt="Mem0 - The Memory Layer for Personalized AI">
  </a>
</p>
<p align="center" style="display: flex; justify-content: center; gap: 20px; align-items: center;">
  <a href="https://trendshift.io/repositories/11194" target="blank">
    <img src="https://trendshift.io/api/badge/repositories/11194" alt="mem0ai%2Fmem0 | Trendshift" width="250" height="55"/>
  </a>
</p>

<p align="center">
  <a href="https://mem0.ai">Learn more</a>
  ·
  <a href="https://mem0.dev/DiG">Join Discord</a>
  ·
  <a href="https://mem0.dev/demo">Demo</a>
</p>

<p align="center">
  <a href="https://mem0.dev/DiG">
    <img src="https://img.shields.io/badge/Discord-%235865F2.svg?&logo=discord&logoColor=white" alt="Mem0 Discord">
  </a>
  <a href="https://pepy.tech/project/mem0ai">
    <img src="https://img.shields.io/pypi/dm/mem0ai" alt="Mem0 PyPI - Downloads">
  </a>
  <a href="https://github.com/mem0ai/mem0">
    <img src="https://img.shields.io/github/commit-activity/m/mem0ai/mem0?style=flat-square" alt="GitHub commit activity">
  </a>
  <a href="https://pypi.org/project/mem0ai" target="blank">
    <img src="https://img.shields.io/pypi/v/mem0ai?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://www.npmjs.com/package/mem0ai" target="blank">
    <img src="https://img.shields.io/npm/v/mem0ai" alt="Npm package">
  </a>
  <a href="https://www.ycombinator.com/companies/mem0">
    <img src="https://img.shields.io/badge/Y%20Combinator-S24-orange?style=flat-square" alt="Y Combinator S24">
  </a>
</p>

<p align="center">
  <a href="https://mem0.ai/research"><strong>📄 Benchmarking Mem0's token-efficient memory algorithm →</strong></a>
</p>

## New Memory Algorithm (April 2026)

| Benchmark | Old | New  | Tokens  | Latency p50  |
| --- | --- | --- | --- | --- |
| **LoCoMo** | 71.4 | **92.5** | 7.0K  | 0.88s  |
| **LongMemEval** | 67.8 | **94.4** | 6.8K  | 1.09s  |
| **BEAM (1M)** | — | **64.1** | 6.7K  | 1.00s  |
| **BEAM (10M)** | — | **48.6** | 6.9K  | 1.05s  |

All benchmarks run on the same production-representative model stack. Single-pass retrieval (one call, no agentic loops) at a top_200 retrieval budget. Scores reflect Mem0's managed platform, which includes proprietary optimizations not available in the open-source SDK; open-source users should expect directionally similar gains but not identical numbers.

**What changed:**
- **Single-pass ADD-only extraction** -- one LLM call, no UPDATE/DELETE. Memories accumulate; nothing is overwritten.
- **Agent-generated facts are first-class** -- when an agent confirms an action, that information is now stored with equal weight.
- **Entity linking** -- entities are extracted, embedded, and linked across memories for retrieval boosting.
- **Multi-signal retrieval** -- semantic, BM25 keyword, and entity matching scored in parallel and fused.
```

---
## camel-ai/owl  (★20116, tier_b app — multi-agent workforce (camel))
frameworks: ['camel'] | v1: i=MULTI ii=worker iii=NO | probed=6 | tree=192
agent-ish top dirs: []

### README (head)
```
<div align="center">

</div>

<h1 align="center">
	🦉 OWL: Optimized Workforce Learning for General Multi-Agent Assistance in Real-World Task Automation
</h1>

<div align="center">

[![Documentation][docs-image]][docs-url]
[![Discord][discord-image]][discord-url]
[![X][x-image]][x-url]
[![Reddit][reddit-image]][reddit-url]
[![Wechat][wechat-image]][wechat-url]
[![Wechat][owl-image]][owl-url]
[![Hugging Face][huggingface-image]][huggingface-url]
[![Star][star-image]][star-url]
[![Package License][package-license-image]][package-license-url]
[![Citation](https://img.shields.io/badge/Citation-arXiv%3A2505.23885-purple)](https://arxiv.org/abs/2505.23885)

</div>

<hr>

<div align="center">
<h4 align="center">

[中文阅读](https://github.com/camel-ai/owl/tree/main/README_zh.md) |
[Community](https://github.com/camel-ai/owl#community) |
[Installation](#️-installation) |
[Examples](https://github.com/camel-ai/owl/tree/main/owl) |
[Paper](https://arxiv.org/abs/2505.23885) |
[Citation](https://github.com/camel-ai/owl#citation) |
[Contributing](https://github.com/camel-ai/owl/graphs/contributors) |
[CAMEL-AI](https://www.camel-ai.org/) |

</h4>

<div align="center" style="background-color: #f0f7ff; padding: 10px; border-radius: 5px; margin: 15px 0;">
  <h3 style="color: #1e88e5; margin: 0;">
    🏆 OWL achieves <span style="color: #d81b60; font-weight: bold; font-size: 1.2em;">69.09</span> average score on GAIA benchmark and ranks <span style="color: #d81b60; font-weight: bold; font-size: 1.2em;">🏅️ #1</span> among open-source frameworks! 🏆
  </h3>
</div>

<div align="center">

🦉 OWL is a cutting-edge framework for multi-agent collaboration that pushes the boundaries of task automation, built on top of the [CAMEL-AI Framework](https://github.com/camel-ai/camel).

Our vision is to revolutionize how AI agents collaborate to solve real-world tasks. By leveraging dynamic agent interactions, OWL enables more natural, efficient, and robust task automation across diverse domains.

If you find this repo useful, please consider citing our work ([citation](#-cite)).
</div>

![](./assets/owl_architecture.png)

<br>

</div>

```

---
## THU-MAIC/OpenMAIC  (★25605, tier_b app — multi-agent classroom)
frameworks: ['langchain', 'langgraph'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=3357
agent-ish top dirs: []

### README (head)
```
<!-- <p align="center">
  <img src="assets/logo-horizontal.png" alt="OpenMAIC" width="420"/>
</p> -->

<p align="center">
  <img src="assets/banner.png" alt="OpenMAIC Banner" width="680"/>
</p>

<p align="center">
  Get an immersive, multi-agent learning experience in just one click
</p>

<p align="center">
  <a href="https://my.feishu.cn/wiki/UIfKw9Knti0LcKkTxDNcqlUrnzh"><img src="https://img.shields.io/badge/%F0%9F%93%98%20User%20Guide-v1.0.0%20%C2%B7%20English-4F8EF7?style=for-the-badge" alt="v1.0.0 User Guide (English)"/></a>
  &nbsp;&nbsp;
  <a href="https://lcn6dqn3m0yr.feishu.cn/wiki/CkQSwHFdzibQFvkGzwPcmUOfnXg"><img src="https://img.shields.io/badge/%F0%9F%93%99%20%E4%BD%93%E9%AA%8C%E6%8C%87%E5%8D%97-v1.0.0%20%C2%B7%20%E4%B8%AD%E6%96%87-FF6B35?style=for-the-badge" alt="v1.0.0 体验指南（中文）"/></a>
</p>

<p align="center">
  <a href="https://jcst.ict.ac.cn/en/article/doi/10.1007/s11390-025-6000-0"><img src="https://img.shields.io/badge/Paper-JCST'26-blue?style=flat-square" alt="Paper"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License: MIT"/></a>
  <a href="https://open.maic.chat/"><img src="https://img.shields.io/badge/Demo-Live-brightgreen?style=flat-square" alt="Live Demo"/></a>
  <a href="https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FTHU-MAIC%2FOpenMAIC&envDescription=Configure%20at%20least%20one%20LLM%20provider%20API%20key%20(e.g.%20OPENAI_API_KEY%2C%20ANTHROPIC_API_KEY).%20All%20providers%20are%20optional.&envLink=https%3A%2F%2Fgithub.com%2FTHU-MAIC%2FOpenMAIC%2Fblob%2Fmain%2F.env.example&project-name=openmaic&framework=nextjs"><img src="https://vercel.com/button" alt="Deploy with Vercel" height="20"/></a>
  <a href="#-openclaw-integration"><img src="https://img.shields.io/badge/OpenClaw-Integration-F4511E?style=flat-square" alt="OpenClaw Integration"/></a>
  <a href="#lemonade-local-ai"><img src="https://img.shields.io/badge/Lemonade-Local_AI-FFD43B?style=flat-square" alt="Lemonade Local AI"/></a>
  <a href="https://github.com/THU-MAIC/OpenMAIC/stargazers"><img src="https://img.shields.io/github/stars/THU-MAIC/OpenMAIC?style=flat-square" alt="Stars"/></a>
  <br/>
  <a href="https://discord.gg/p8Pf2r3SaG"><img src="https://img.shields.io/badge/Discord-Join_Community-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"/></a>
  &nbsp;
  <a href="community/feishu.md"><img src="https://img.shields.io/badge/Feishu-Community-00D6B9?style=for-the-badge&logo=bytedance&logoColor=white" alt="Feishu Community"/></a>
  <br/>
  <img src="https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js" alt="Next.js"/>
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React"/>
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/LangGraph-1.1-purple?style=flat-square" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind CSS"/>
</p>

<p align="center">
  <a href="./README.md">English</a> | <a href="./README-zh.md">Simplified Chinese</a>
  <br/>
  <a href="https://open.maic.chat/">Live Demo</a> · <a href="#-quick-start">Quick Start</a> · <a href="#lemonade-local-ai">Lemonade</a> · <a href="#funasr-local-asr">FunASR</a> · <a href="#-features">Features</a> · <a href="#-use-cases">Use Cases</a> · <a href="#-openclaw-integration">OpenClaw</a>
</p>

## 🎉 OpenMAIC v1.0.0 — Build courses with an agent

**One prompt in, a whole course out — and now you can steer.** Released August 27, 2026, OpenMAIC v1.0.0 adds a **Pro workbench** alongside the classic one-click generator: chat with an agent that plans your curriculum, builds and revises every page, and works straight from your materials.

- 🤖 **Agent workbench** — a chat-first workspace that plans, builds, and revises whole courses
- 💾 **Durable sessions** — server-backed runs survive restarts; cancel, resume, and steer anytime
- 📎 **Session materials** — upload documents, audio, and video, or pull from web search; the agent builds from them
- 🧰 **Course tools + 20 built-in skills** — slides, quizzes, interactives, PBL, images, video, voices, `.pptx` import
- 🔌 **Neutral by design** — bring your own models, media, search providers, and storage backend

Take the full tour in [Features](#-features), then set it up with [Agent workbench and runtime](#optional-agent-workbench-and-runtime).


## 🗞️ News

- **2026-08-27** — **OpenMAIC v1.0.0:** an agent workbench, durable course-building sessions, reusable skills, session materials, provider-neutral server capabilities, and a pluggable persistence stack.
```

---
## pydantic/pydantic-ai  (★19608, tier_b app — agent framework-lite)
frameworks: ['langchain'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=2807
agent-ish top dirs: ['.agents', 'agent_docs', 'AGENTS.md']

### README (head)
```
<div align="center">
  <a href="https://pydantic.dev/docs/ai/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://pydantic.dev/docs/ai/img/pydantic-ai-dark.svg">
      <img src="https://pydantic.dev/docs/ai/img/pydantic-ai-light.svg" alt="Pydantic AI">
    </picture>
  </a>
</div>
<div align="center">
  <h3>How Python does AI</h3>
</div>
<div align="center">
  <a href="https://github.com/pydantic/pydantic-ai/actions/workflows/ci.yml?query=branch%3Amain"><img src="https://github.com/pydantic/pydantic-ai/actions/workflows/ci.yml/badge.svg?event=push" alt="CI"></a>
  <a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/pydantic/pydantic-ai"><img src="https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic-ai.svg" alt="Coverage"></a>
  <a href="https://pypi.python.org/pypi/pydantic-ai"><img src="https://img.shields.io/pypi/v/pydantic-ai.svg" alt="PyPI"></a>
  <a href="https://github.com/pydantic/pydantic-ai"><img src="https://img.shields.io/pypi/pyversions/pydantic-ai.svg" alt="versions"></a>
  <a href="https://github.com/pydantic/pydantic-ai/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pydantic/pydantic-ai.svg?v" alt="license"></a>
  <a href="https://logfire.pydantic.dev/docs/join-slack/"><img src="https://img.shields.io/badge/Slack-Join%20Slack-4A154B?logo=slack" alt="Join Slack" /></a>
</div>
<p align="center">
  Agents, realtime voice, image generation, embeddings. Every model, every interface, typed end to end.
</p>

---

**Pydantic AI** is the Python AI SDK: a typed, [extensible](https://pydantic.dev/docs/ai/guides/extensibility/) agent loop with [every model](https://pydantic.dev/docs/ai/models/overview/) a string swap away. The same agent [runs everywhere you need it](https://pydantic.dev/docs/ai/overview/interfaces/): behind a [web frontend](https://pydantic.dev/docs/ai/integrations/ui/overview/), in the [terminal](https://pydantic.dev/docs/ai/integrations/cli/), on a [voice call](https://pydantic.dev/docs/ai/realtime/overview/), on a [durable background queue](https://pydantic.dev/docs/ai/capabilities/durable_execution/overview/), or as a plain object you call [`run()`](https://pydantic.dev/docs/ai/core-concepts/agent/#running-agents) on. [Image generation](https://pydantic.dev/docs/ai/capabilities/image-generation/) and [embeddings](https://pydantic.dev/docs/ai/guides/embeddings/) come in the same box.

**[Pydantic AI Harness](https://github.com/pydantic/pydantic-ai-harness)** has everything an agent needs for complex, long-running work, snapped on as [capabilities](https://pydantic.dev/docs/ai/capabilities/overview/), from [memory](https://pydantic.dev/docs/ai/harness/memory/), [sub-agents](https://pydantic.dev/docs/ai/harness/subagents/), and [context management](https://pydantic.dev/docs/ai/harness/compaction/) to a complete [coding agent](https://pydantic.dev/docs/ai/harness/coder/).

View the complete documentation at [pydantic.dev/docs/ai](https://pydantic.dev/docs/ai/).

## What are you building?

From simple typed data extraction to complex, long-running multi-agent collaboration, Pydantic AI and [Pydantic AI Harness](https://github.com/pydantic/pydantic-ai-harness) have got you covered.

### Coding agent

A complete coding agent in your terminal: workspace-rooted [file access](https://pydantic.dev/docs/ai/harness/filesystem/), allowlisted [shell](https://pydantic.dev/docs/ai/harness/shell/), [repo orientation](https://pydantic.dev/docs/ai/harness/repo-context/), [planning](https://pydantic.dev/docs/ai/harness/planning/), and [context management](https://pydantic.dev/docs/ai/harness/compaction/) that survives long sessions. Here with [web search](https://pydantic.dev/docs/ai/capabilities/web-search/) and a second-opinion [advisor](https://pydantic.dev/docs/ai/harness/advisor/) snapped on alongside:

```bash
uv add pydantic-ai pydantic-ai-harness
```

```python
from pydantic_ai import Agent
from pydantic_ai.capabilities import WebSearch
from pydantic_ai_harness import Advisor, Coder

agent = Agent(
    'anthropic:claude-fable-5',
    capabilities=[
        Coder(),  # files, shell, repo context, planning, sub-agents, context management
        WebSearch(),  # look up docs and error messages on the web
        Advisor('openai:gpt-5.6-sol'),  # a second opinion from another model when stuck
    ],
)
agent.to_cli_sync()
```

[`Coder`](https://pydantic.dev/docs/ai/harness/coder/) is a regular [combined capability](https://pydantic.dev/docs/ai/capabilities/custom/#composition-and-middleware-semantics), not a black box: use it whole, or use the blocks it bundles directly; the two are equivalent:
```

---
## danny-avila/LibreChat  (★42641, tier_b app — chat + agents)
frameworks: ['langchain', 'langgraph'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=5385
agent-ish top dirs: ['AGENTS.md']

### README (head)
```
<p align="center">
  <a href="https://librechat.ai">
    <img src="client/public/assets/logo.svg" height="256">
  </a>
  <h1 align="center">
    <a href="https://librechat.ai">LibreChat</a>
  </h1>
</p>

<p align="center">
  <strong>English</strong> ·
  <a href="README.zh.md">中文</a>
</p>

<p align="center">
  <a href="https://discord.librechat.ai"> 
    <img
      src="https://img.shields.io/discord/1086345563026489514?label=&logo=discord&style=for-the-badge&logoWidth=20&logoColor=white&labelColor=000000&color=blueviolet">
  </a>
  <a href="https://www.youtube.com/@LibreChat"> 
    <img
      src="https://img.shields.io/badge/YOUTUBE-red.svg?style=for-the-badge&logo=youtube&logoColor=white&labelColor=000000&logoWidth=20">
  </a>
  <a href="https://docs.librechat.ai"> 
    <img
      src="https://img.shields.io/badge/DOCS-blue.svg?style=for-the-badge&logo=read-the-docs&logoColor=white&labelColor=000000&logoWidth=20">
  </a>
  <a aria-label="Sponsors" href="https://github.com/sponsors/danny-avila">
    <img
      src="https://img.shields.io/badge/SPONSORS-brightgreen.svg?style=for-the-badge&logo=github-sponsors&logoColor=white&labelColor=000000&logoWidth=20">
  </a>
</p>

<p align="center">
<a href="https://railway.com/deploy/librechat-official?referralCode=HI9hWz&utm_medium=integration&utm_source=readme&utm_campaign=librechat">
  <img src="https://railway.com/button.svg" alt="Deploy on Railway" height="30">
</a>
<a href="https://zeabur.com/templates/0X2ZY8">
  <img src="https://zeabur.com/button.svg" alt="Deploy on Zeabur" height="30"/>
</a>
<a href="https://template.cloud.sealos.io/deploy?templateName=librechat">
  <img src="https://raw.githubusercontent.com/labring-actions/templates/main/Deploy-on-Sealos.svg" alt="Deploy on Sealos" height="30">
</a>
</p>

<p align="center">
  <a href="https://www.librechat.ai/docs/translation">
    <img 
      src="https://img.shields.io/badge/dynamic/json.svg?style=for-the-badge&color=2096F3&label=locize&query=%24.translatedPercentage&url=https://api.locize.app/badgedata/4cb2598b-ed4d-469c-9b04-2ed531a8cb45&suffix=%+translated" 
      alt="Translation Progress">
  </a>
</p>

## 🚀 What's New in v0.8.8-rc1

- **Agent run control:** Interrupt or steer an Agent mid-run, queue follow-up messages, and reclaim, edit, or escalate pending steers.
- **Human-in-the-loop Agents:** Agents stream question progress, ask up to four related questions in one form, pause for input or tool approval, and resume.
- **Unified Agent Builder:** A redesigned Tools marketplace brings together Skills, MCP, Code Interpreter, orchestration, Programmatic Tool Calling, model-spec controls, and per-tool background and intent settings.
- **Readable Agent activity:** Generated activity-group headers, parent phase summaries, and live tool intent labels make long reasoning and tool runs easier to scan.
- **Code Interpreter workflows:** Code and shell tools can run in the background, sandbox images return as viewable artifacts, and highly experimental stateful sessions can reuse prewarmed conversation workspaces.
```

---
## OpenHands/OpenHands  (★0, tier_b app — coding agent)
frameworks: [] | v1: i=None ii=None iii=None | probed=0 | tree=0
agent-ish top dirs: []

### README (head)
```
<a name="readme-top"></a>

<div align="center">
  <img src="https://assets.openhands.dev/logo-whitebackground.png" alt="OpenHands logo" width="340">
  <h1 align="center" style="border-bottom: none">Agent Canvas</h1>
  <p align="center">
    <strong>The self-hosted developer control center for coding agents and automations.</strong>
  </p>
  <p align="center">
    Run OpenHands, Claude Code, Codex, Gemini, or any ACP-compatible agent across local, remote, and cloud backends.
  </p>
</div>
<div align="center">
  <a href="https://github.com/OpenHands/incubator-program"><img src="https://img.shields.io/badge/status-beta-blue?style=for-the-badge" alt="Project status beta"></a>
  <a href="https://github.com/OpenHands/OpenHands/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/OpenHands/OpenHands/ci.yml?branch=main&style=for-the-badge" alt="CI status"></a>
  <a href="https://www.npmjs.com/package/@openhands/agent-canvas"><img src="https://img.shields.io/npm/v/%40openhands%2Fagent-canvas?style=for-the-badge&logo=npm" alt="npm version"></a>
  <a href="https://docs.openhands.dev/openhands/usage/agent-canvas/backends"><img src="https://img.shields.io/badge/Documentation-000?logo=googledocs&logoColor=FFE165&style=for-the-badge" alt="Documentation"></a>
  <a href="https://go.openhands.dev/slack"><img src="https://img.shields.io/badge/Slack-Join%20the%20community-611f69?logo=slack&logoColor=white&style=for-the-badge" alt="Join us on Slack"></a>
</div>
<div align="center">
  <a href="#quickstart">Quickstart</a> |
  <a href="./docs/README.md">Docs</a> |
  <a href="./docs/SELF_HOSTING.md">Self-Hosting</a> |
  <a href="https://docs.openhands.dev/openhands/usage/agent-canvas/acp-agents">ACP Agents</a> |
  <a href="https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt-automations">Automations</a> |
  <a href="https://go.openhands.dev/slack">Slack</a>
</div>
<p align="center">
  <img src="https://assets.openhands.dev/screenshot/automation-preview.png" alt="Agent Canvas automation preview" width="100%">
</p>
<hr>

OpenHands Agent Canvas turns your coding agents into a self-hosted, always-on engineering team. It's a developer control center for starting conversations and automating everyday tasks — like generating reports that publish to Slack or automatically decomposing GitHub issues into tasks.

It runs locally on your machine by default, but can connect to multiple “agent backends”, e.g. running agents in Docker containers, on VMs, or within your company infrastructure. You can optionally choose to run agents on OpenHands Cloud or OpenHands Enterprise infrastructure.

Agent Canvas runs the open source OpenHands agent out-of-the-box, but can use any third-party agent like Claude Code and Codex.

|                                                                                                                      |                                                                                                                                          |
| -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| [**Self-host your way**](https://docs.openhands.dev/openhands/usage/agent-canvas/backend-setup/vm)                   | Run agents locally, in Docker, on VMs, or anywhere you can run an agent server backend                                                   |
| [**Switch between different backends**](https://docs.openhands.dev/openhands/usage/agent-canvas/backends)            | Switch between local, remote, and cloud agents without losing focus                                                                      |
| [**Create automations**](https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt-automations)               | Create automations and workflows that integrate with Slack, GitHub, Linear, and more. Run on a schedule or in response to webhook events |
| [**Integrate with the tools you use**](https://docs.openhands.dev/openhands/usage/agent-canvas/prebuilt-automations) | Connect your automations with third-party services like Slack, GitHub, Notion, and more to automate workflows                            |
| [**Bring your own model**](https://docs.openhands.dev/openhands/usage/settings/llm-settings#llm-profiles)            | Use with any LLM                                                                                                                         |
| [**Use with any agent**](https://docs.openhands.dev/openhands/usage/agent-canvas/acp-agents)                         | Use with OpenHands, Claude Code, Codex, Gemini, or any agent with Agent-Client Protocol (ACP).                                           |

If you have questions or feedback, please open a GitHub issue or join the [#proj-agent-canvas channel in Slack](https://openhands.dev/joinslack).

## Quickstart

You can install OpenHands to run agents on any machine: on your laptop, on a dedicated computer like a Mac Mini,
or on a server in the cloud.

The most powerful way to run OpenHands is on a server in the cloud. This allows your agents to continue running
even when your laptop is shut, and makes it easier to trigger your agents through third-party services
like Slack, GitHub, and Datadog. See [SELF_HOSTING.md](docs/SELF_HOSTING.md) for details, especially with respect to security hardening.

Notably, you can run the backend in _multiple different environments_, and switch between
them from the same Agent Canvas frontend. E.g. you can share an Agent Server with your team for agents doing
```

---
## KnockOutEZ/wigolo  (★4794, reverse-gap — crewai dep, no multi-agent self-description)
frameworks: ['crewai', 'langchain'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=1908
agent-ish top dirs: []

### README (head)
```
<div align="center">

<img alt="wigolo — the go-to web for your agent" src="assets/brand/wigolo-banner.png" width="640">

Local-first web intelligence for AI agents — **no keys, no cloud, no metered bill.**

<sub>works with&nbsp;&nbsp;**Claude Code · Cursor · Codex · Gemini CLI · OpenCode · VS Code · Windsurf · Zed · Antigravity**</sub>
<br>
<sub>and beyond&nbsp;&nbsp;**LangChain · CrewAI · LlamaIndex · Vercel AI SDK · n8n & self-hosted agents · any MCP client · plain REST**</sub>

[![npm](https://img.shields.io/npm/v/wigolo?color=cb3837&logo=npm)](https://www.npmjs.com/package/wigolo)
[![npm downloads](https://img.shields.io/npm/dm/wigolo?color=cb3837&logo=npm&label=downloads)](https://www.npmjs.com/package/wigolo)
[![GitHub stars](https://img.shields.io/github/stars/KnockOutEZ/wigolo?style=flat&logo=github&color=e3b341)](https://github.com/KnockOutEZ/wigolo/stargazers)
[![CI](https://img.shields.io/github/actions/workflow/status/KnockOutEZ/wigolo/ci.yml?branch=main&logo=github&label=CI)](https://github.com/KnockOutEZ/wigolo/actions/workflows/ci.yml)
[![node](https://img.shields.io/badge/node-%E2%89%A520-339933?logo=node.js&logoColor=white)](https://nodejs.org)
[![MCP](https://img.shields.io/badge/MCP-server-7c3aed)](https://modelcontextprotocol.io)
[![license](https://img.shields.io/badge/license-AGPL--3.0-2563eb)](#license)
[![status](https://img.shields.io/badge/status-public%20beta-b7791f)](#beta--feedback)
[![follow on X](https://img.shields.io/badge/follow-%40yourtowhid-000000?logo=x&logoColor=white)](https://x.com/yourtowhid)

<a href="https://trendshift.io/repositories/79424?utm_source=repository-badge&utm_medium=badge&utm_campaign=badge-repository-79424" target="_blank"><img src="https://trendshift.io/api/badge/repositories/79424" alt="wigolo on Trendshift" width="250" height="55"/></a>
<a href="https://trendshift.io/repositories/79424?utm_source=trendshift-badge&utm_medium=badge&utm_campaign=badge-trendshift-79424" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/trendshift/repositories/79424/daily?language=TypeScript" alt="KnockOutEZ%2Fwigolo | Trendshift" width="250" height="55"/></a>

[Quickstart](#quickstart) · [Tools](#tools) · [Why wigolo](#why-its-different) · [Sponsors](#sponsors) · [Benchmark](#benchmark) · [Docs](docs/README.md) · [Examples](examples/README.md) · [Feedback](#beta--feedback) · [FAQ](#faq)

New features and updates ship steadily. Follow <a href="https://x.com/yourtowhid"><b>@yourtowhid on X</b></a> for all of it and new ways to use wigolo, and reach out there for collaborations or feedback · also on <a href="https://www.linkedin.com/in/yourtowhid/">LinkedIn</a>

</div>

---

wigolo gives an AI agent one surface for everything web-related: **search, fetch, crawl, extract, cache, find-similar, research,** and autonomous gather loops. It runs wherever your agent runs — as an MCP server next to your coding agent, as a REST/MCP endpoint on the box where your self-hosted agents live, or embedded through an SDK inside your own app. The core tools need no API keys, nothing it touches leaves `~/.wigolo/`, and no bill grows with how much your agent thinks.

<div align="center">

<img alt="wigolo demo — Claude Code answering a live web question through wigolo, no API keys" src="assets/wigolo-demo.gif" width="800">

</div>

## Quickstart

```bash
npx wigolo init                              # set up the local engine — any system
npx wigolo init --agents=claude-code,cursor  # …or set up + wire your day-to-day agents in one command
```

Requires **Node ≥ 20** and ~1.5 GB of free disk on macOS, Linux, or Windows. Bare `init` sets up the local engine: it downloads the browser engine and on-device models, runs a health check, and reports each component. Adding `--agents` wires the named agents in the same run, so a coding agent you use daily is ready in one command.

- **Supported agents** — `--agents` takes any of `claude-code` · `cursor` · `codex` · `gemini-cli` · `opencode` · `vscode` · `windsurf` · `zed` · `antigravity` (comma-separated); wigolo writes the MCP config and, where supported, instructions for each.
- **Any other setup** — any MCP client, agent framework, or self-hosted agent registers `npx -y wigolo` in its own MCP config. The [installation guide](docs/installation.md) has the exact config block for every client, plus Docker, Homebrew, and single-file-binary channels.
- **More on the way** — the supported list keeps growing, and a PR to add your agent is welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).
- **Interactive setup** — `--interactive` is a plain-text flow; `--wizard` is the full terminal TUI.
- **Defer downloads** — `--no-warmup` waits until first use. A failed component download never fails setup; init reports what's not ready with the exact fix and still completes.

`init` is unattended by default, so it's safe in scripts and CI, and any setup problem surfaces right here in the per-component report, before your agent's first call. **Search, fetch, crawl, extract, cache, and find-similar work with no API key.** Check it's healthy anytime:

```bash
npx wigolo doctor
```

```

---
## Lumiwealth/lumibot  (★2016, reverse-gap — google-adk dep (trading))
frameworks: ['google-adk'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=1351
agent-ish top dirs: ['agent_eval_cases', 'workers', 'agent_eval_baselines', 'AGENTS.md']

### README (head)
```
[![CI Status](https://github.com/Lumiwealth/lumibot/actions/workflows/cicd.yaml/badge.svg?branch=dev)](https://github.com/Lumiwealth/lumibot/actions/workflows/cicd.yaml)
[![Coverage](https://raw.githubusercontent.com/Lumiwealth/lumibot/badge/coverage.svg)](https://github.com/Lumiwealth/lumibot/actions/workflows/cicd.yaml)
[![PyPI](https://img.shields.io/pypi/v/lumibot)](https://pypi.org/project/lumibot/)
[![Python](https://img.shields.io/pypi/pyversions/lumibot)](https://pypi.org/project/lumibot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

# Lumibot

**Build, backtest, and run algorithmic trading strategies and AI agents in Python.**

**Full docs:** [lumibot.lumiwealth.com](https://lumibot.lumiwealth.com/) · **Managed cloud:** [BotSpot.trade](https://botspot.trade/sales?showLogin=1&utm_source=github&utm_medium=readme&utm_campaign=lumibot&utm_content=top_text_link&sample=lumibot_readme_deploy) · **MCP:** [BotSpot for AI coding agents](https://botspot.trade/agents?utm_source=github&utm_medium=readme&utm_campaign=lumibot&utm_content=top_mcp_link)

<p align="center">
  <strong>🌐 Community</strong><br><br>
  <a href="https://www.reddit.com/r/BotSpotTrade/"><img src="docs/assets/community/reddit.svg" alt="Reddit" width="20" height="20"> Reddit Community</a>
  &nbsp;&nbsp;&nbsp;
  <a href="https://discord.gg/4R9j6T3PN8"><img src="docs/assets/community/discord.svg" alt="Discord" width="20" height="20"> Discord Community</a>
</p>

<p align="center">
  <img src="docs/assets/readme/lumibot_ai_trading_agents_overview.png" alt="Lumibot AI trading agents overview" width="100%">
</p>

## What You Can Build

- **Deterministic strategies:** normal Python logic, indicators, if statements, scheduled rules, position sizing, and risk controls.
- **AI-agent strategies:** one or more agents that reason through evidence, call tools, write memory, and optionally place orders.
- **Backtests:** replay historical data and simulated orders with artifacts you can inspect.
- **Paper or live trading:** reuse the same strategy code with real broker state and real order routing.

Start with the open-source docs, then deploy when you are ready: [Lumibot documentation](https://lumibot.lumiwealth.com/?utm_source=github&utm_medium=readme&utm_campaign=lumibot&utm_content=what_you_can_build_docs) · [Try a sample Lumibot strategy on BotSpot](https://botspot.trade/sales?showLogin=1&utm_source=github&utm_medium=readme&utm_campaign=lumibot&utm_content=what_you_can_build_botspot&sample=lumibot_readme_deploy)

## Quick Start

### Backtest a strategy

```bash
pip install lumibot
```

Save this as `my_strategy.py`:

```python
from datetime import datetime
from lumibot.strategies import Strategy
from lumibot.backtesting import YahooDataBacktesting

class MyStrategy(Strategy):
    def on_trading_iteration(self):
        if self.first_iteration:
            aapl = self.create_order("AAPL", 10, "buy")
            self.submit_order(aapl)

MyStrategy.backtest(
    YahooDataBacktesting,
    datetime(2023, 1, 1),
    datetime(2024, 1, 1),
)
```

```

---
## langroid/langroid  (★4101, reverse-gap — camel dep)
frameworks: ['camel'] | v1: i=MULTI ii=worker iii=JUDGE | probed=8 | tree=851
agent-ish top dirs: []

### README (head)
```
<div align="center">
  <img src="https://raw.githubusercontent.com/langroid/langroid/main/docs/assets/langroid-card-lambda-ossem-rust-1200-630.png" alt="Logo"
        width="400" align="center">
</div>

<div align="center">

[![PyPI - Version](https://img.shields.io/pypi/v/langroid)](https://pypi.org/project/langroid/)
[![Downloads](https://img.shields.io/pypi/dm/langroid)](https://pypi.org/project/langroid/)
[![Pytest](https://github.com/langroid/langroid/actions/workflows/pytest.yml/badge.svg)](https://github.com/langroid/langroid/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/langroid/langroid/graph/badge.svg)](https://codecov.io/gh/langroid/langroid)
[![Multi-Architecture DockerHub](https://github.com/langroid/langroid/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/langroid/langroid/actions/workflows/docker-publish.yml)

[![Static Badge](https://img.shields.io/badge/Documentation-blue?link=https%3A%2F%2Flangroid.github.io%2Flangroid%2F&link=https%3A%2F%2Flangroid.github.io%2Flangroid%2F)](https://langroid.github.io/langroid)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/langroid/langroid/blob/main/examples/Langroid_quick_start.ipynb)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=flat&logo=discord&logoColor=white)](https://discord.gg/ZU36McDgDs)
[![Substack](https://img.shields.io/badge/Substack-%23006f5c.svg?style=flat&logo=substack&logoColor=FF6719)](https://langroid.substack.com/p/langroid-harness-llms-with-multi-agent-programming)

</div>

<h3 align="center">
  <a target="_blank" 
    href="https://langroid.github.io/langroid/" rel="dofollow">
      <strong>Documentation</strong></a>
  &middot;
  <a target="_blank" href="https://github.com/langroid/langroid-examples" rel="dofollow">
      <strong>Examples Repo</strong></a>
  &middot;
  <a target="_blank" href="https://discord.gg/ZU36McDgDs" rel="dofollow">
      <strong>Discord</strong></a>
  &middot;
  <a target="_blank" href="https://github.com/langroid/langroid/blob/main/CONTRIBUTING.md" rel="dofollow">
      <strong>Contributing</strong></a>

  <br />
</h3>

`Langroid` is an intuitive, lightweight, extensible and principled
Python framework to easily build LLM-powered applications, from CMU and UW-Madison researchers. 
You set up Agents, equip them with optional components (LLM, 
vector-store and tools/functions), assign them tasks, and have them 
collaboratively solve a problem by exchanging messages. 
This Multi-Agent paradigm is inspired by the
[Actor Framework](https://en.wikipedia.org/wiki/Actor_model)
(but you do not need to know anything about this!). 

`Langroid` is a fresh take on LLM app-development, where considerable thought has gone 
into simplifying the developer experience; 
it does not use `Langchain`, or any other LLM framework, 
and works with [practically any LLM](https://langroid.github.io/langroid/tutorials/supported-models/).

🔥 ✨ A Claude Code [plugin](#claude-code-plugin-optional) is available to
accelerate Langroid development with built-in patterns and best practices.


🔥 Read the (WIP) [overview of the langroid architecture](https://langroid.github.io/langroid/blog/2024/08/15/overview-of-langroids-multi-agent-architecture-prelim/), 
 and a [quick tour of Langroid](https://langroid.github.io/langroid/tutorials/langroid-tour/).

🔥 MCP Support: Allow any LLM-Agent to leverage MCP Servers via Langroid's simple
[MCP tool adapter](https://langroid.github.io/langroid/notes/mcp-tools/) that converts 
```

---
## minitap-ai/mobile-use  (★2792, reverse-gap — langgraph dep (mobile agent))
frameworks: ['langchain', 'langgraph'] | v1: i=MULTI ii=worker iii=NO | probed=8 | tree=205
agent-ish top dirs: []

### README (head)
```
# mobile-use: automate your phone with natural language

<div align="center">

![mobile-use in Action](./doc/banner-v2.png)

</div>

<div align="center">

[![Discord](https://img.shields.io/discord/1403058278342201394?color=7289DA&label=Discord&logo=discord&logoColor=white&style=for-the-badge)](https://discord.gg/6nSqmQ9pQs)
[![GitHub stars](https://img.shields.io/github/stars/minitap-ai/mobile-use?style=for-the-badge&color=e0a8dd)](https://github.com/minitap-ai/mobile-use/stargazers)

<h3>
    <a href="https://docs.minitap.ai/v2/mcp-server/introduction"><b>📚 Documentation</b></a> •
    <a href="https://arxiv.org/abs/2602.07787"><b>📃 Paper</b></a>

</h3>
<p align="center">
    <a href="https://discord.gg/6nSqmQ9pQs"><b>Discord</b></a> •
    <a href="https://x.com/minitap_ai?t=iRWtI497UhRGLeCKYQekig&s=09"><b>Twitter / X</b></a>
</p>

[![PyPI version](https://img.shields.io/pypi/v/minitap-mobile-use.svg?color=blue)](https://pypi.org/project/minitap-mobile-use/)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](https://github.com/minitap-ai/mobile-use/blob/main/LICENSE)

</div>

Mobile-use is a powerful, open-source AI agent that controls your Android or IOS device using natural language. It understands your commands and interacts with the UI to perform tasks, from sending messages to navigating complex apps.

> Mobile-use is quickly evolving. Your suggestions, ideas, and reported bugs will shape this project. Do not hesitate to join in the conversation on [Discord](https://discord.gg/6nSqmQ9pQs) or contribute directly, we will reply to everyone! ❤️

## ✨ Features

- 🗣️ **Natural Language Control**: Interact with your phone using your native language.
- 📱 **UI-Aware Automation**: Intelligently navigates through app interfaces (note: currently has limited effectiveness with games as they don't provide accessibility tree data).
- 📊 **Data Scraping**: Extract information from any app and structure it into your desired format (e.g., JSON) using a natural language description.
- 🔧 **Extensible & Customizable**: Easily configure different LLMs to power the agents that power mobile-use. Supports OpenAI, Google, xAI, OpenRouter, MiniMax, and more.

## Benchmarks

<p align="center">
  <a href="https://minitap.ai/benchmark">
    <img src="https://files.peachworlds.com/website/2b590171-669d-42ce-b4b5-ce6eae83a9d8/scorerank-140126.webp" alt="Project banner" />
  </a>
</p>

We stand as the top performers and the first to have completed 100% of the AndroidWorld benchmark.

Get more info about how we reached this milestone here: [Minitap Benchmark](https://minitap.ai/benchmark).

The official leaderboard is available [here](https://docs.google.com/spreadsheets/d/1cchzP9dlTZ3WXQTfYNhh3avxoLipqHN75v1Tb86uhHo/edit?pli=1&gid=0#gid=0).

Check out our research paper [here](https://arxiv.org/abs/2602.07787).

## 🚀 Getting Started

Ready to automate your mobile experience? Follow these steps to get mobile-use up and running.

```
