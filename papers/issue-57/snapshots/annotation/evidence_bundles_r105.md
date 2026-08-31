# Ground-truth annotation bundles — issue #57 (R105 extension, +20 repos)

FRESH held-out set: annotated AFTER v2 was fixed (R104 calibration set untouched).
Stratified over v2 Tier B distribution; includes both remaining JUDGE positives,
all v2-UNKNOWN cases, the R104 held-out boundary miss (langflow), and two
semi-seen gate entries (OpenViking, AgentStack) for table verification.

Annotation set: 20 repos × 3 axes = 60 cells

---
## langflow-ai/langflow  (★153961, boundary ii — R104 sole held-out miss (PIPELINE DAG vs ORCH-WORKER supervisor))
frameworks: ['autogen/ag2', 'crewai', 'langchain', 'langgraph', 'smolagents'] | v1: i=MULTI ii=pipeline iii=JUDGE | v2: i=MULTI ii=ORCH-WORKER iii=NO | probed=8 | tree=11741
agent-ish top dirs: ['.agents', 'AGENTS-example.md', 'AGENTS.md']

### README (head)
```
<!-- markdownlint-disable MD030 -->

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./docs/static/img/langflow-logo-color-blue-bg.svg">
  <img src="./docs/static/img/langflow-logo-color-black-solid.svg" alt="Langflow logo">
</picture>

[![Release Notes](https://img.shields.io/github/release/langflow-ai/langflow?style=flat-square)](https://github.com/langflow-ai/langflow/releases)
[![PyPI - License](https://img.shields.io/badge/license-MIT-orange)](https://opensource.org/licenses/MIT)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/langflow?style=flat-square)](https://pypistats.org/packages/langflow)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/langflow-ai.svg?style=social&label=Follow%20%40Langflow)](https://twitter.com/langflow_ai)
[![YouTube Channel](https://img.shields.io/youtube/channel/subscribers/UCn2bInQrjdDYKEEmbpwblLQ?label=Subscribe)](https://www.youtube.com/@Langflow)
[![Discord Server](https://img.shields.io/discord/1116803230643527710?logo=discord&style=social&label=Join)](https://discord.gg/EqksyE2EX9)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/langflow-ai/langflow)

[Langflow](https://langflow.org) is a powerful platform for building and deploying AI-powered agents and workflows. It provides developers with both a visual authoring experience and built-in API and MCP servers that turn every workflow into a tool that can be integrated into applications built on any framework or stack. Langflow comes with batteries included and supports all major LLMs, vector databases and a growing library of AI tools.

## ✨ Highlight features

- **Visual builder interface** to quickly get started and iterate.
- **Source code access** lets you customize any component using Python.
- **Interactive playground** to immediately test and refine your flows with step-by-step control.
- **Multi-agent orchestration** with conversation management and retrieval.
- **Deploy as an API** or export as JSON for Python apps.
- **Deploy as an MCP server** and turn your flows into tools for MCP clients.
- **Observability** with LangSmith, LangFuse and other integrations.
- **Enterprise-ready** security and scalability.

## 🖥️  Langflow Desktop

Langflow Desktop is the easiest way to get started with Langflow. All dependencies are included, so you don't need to manage Python environments or install packages manually.
Available for Windows and macOS.

[📥 Download Langflow Desktop](https://www.langflow.org/desktop)

## ⚡️ Quickstart

### Install locally (recommended)

Requires Python 3.10–3.14 and [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended package manager).

#### Install

From a fresh directory, run:
```shell
uv pip install langflow -U
```

The latest Langflow package is installed.
For more information, see [Install and run the Langflow OSS Python package](https://docs.langflow.org/get-started-installation#install-and-run-the-langflow-oss-python-package).

#### Run

To start Langflow, run:
```shell
uv run langflow run
```

Langflow starts at http://127.0.0.1:7860.

```

---
## karpathy/autoresearch  (★94985, gap anchor — famous single research agent, zero framework deps)
frameworks: [] | v1: i=SINGLE ii=UNKNOWN iii=UNKNOWN | v2: i=SINGLE ii=SINGLE iii=NO | probed=0 | tree=10
agent-ish top dirs: []

### README (head)
```
# autoresearch

![teaser](progress.png)

*One day, frontier AI research used to be done by meat computers in between eating, sleeping, having other fun, and synchronizing once in a while using sound wave interconnect in the ritual of "group meeting". That era is long gone. Research is now entirely the domain of autonomous swarms of AI agents running across compute cluster megastructures in the skies. The agents claim that we are now in the 10,205th generation of the code base, in any case no one could tell if that's right or wrong as the "code" is now a self-modifying binary that has grown beyond human comprehension. This repo is the story of how it all began. -@karpathy, March 2026*.

The idea: give an AI agent a small but real LLM training setup and let it experiment autonomously overnight. It modifies the code, trains for 5 minutes, checks if the result improved, keeps or discards, and repeats. You wake up in the morning to a log of experiments and (hopefully) a better model. The training code here is a simplified single-GPU implementation of [nanochat](https://github.com/karpathy/nanochat). The core idea is that you're not touching any of the Python files like you normally would as a researcher. Instead, you are programming the `program.md` Markdown files that provide context to the AI agents and set up your autonomous research org. The default `program.md` in this repo is intentionally kept as a bare bones baseline, though it's obvious how one would iterate on it over time to find the "research org code" that achieves the fastest research progress, how you'd add more agents to the mix, etc. A bit more context on this project is here in this [tweet](https://x.com/karpathy/status/2029701092347630069) and [this tweet](https://x.com/karpathy/status/2031135152349524125).

## How it works

The repo is deliberately kept small and only really has three files that matter:

- **`prepare.py`** — fixed constants, one-time data prep (downloads training data, trains a BPE tokenizer), and runtime utilities (dataloader, evaluation). Not modified.
- **`train.py`** — the single file the agent edits. Contains the full GPT model, optimizer (Muon + AdamW), and training loop. Everything is fair game: architecture, hyperparameters, optimizer, batch size, etc. **This file is edited and iterated on by the agent**.
- **`program.md`** — baseline instructions for one agent. Point your agent here and let it go. **This file is edited and iterated on by the human**.

By design, training runs for a **fixed 5-minute time budget** (wall clock, excluding startup/compilation), regardless of the details of your compute. The metric is **val_bpb** (validation bits per byte) — lower is better, and vocab-size-independent so architectural changes are fairly compared.

If you are new to neural networks, this ["Dummy's Guide"](https://x.com/hooeem/status/2030720614752039185) looks pretty good for a lot more context.

## Quick start

**Requirements:** A single NVIDIA GPU (tested on H100), Python 3.10+, [uv](https://docs.astral.sh/uv/).

```bash

# 1. Install uv project manager (if you don't already have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync

# 3. Download data and train tokenizer (one-time, ~2 min)
uv run prepare.py

# 4. Manually run a single training experiment (~5 min)
uv run train.py
```

If the above commands all work ok, your setup is working and you can go into autonomous research mode.

## Running the agent

Simply spin up your Claude/Codex or whatever you want in this repo (and disable all permissions), then you can prompt something like:

```
Hi have a look at program.md and let's kick off a new experiment! let's do the setup first.
```

The `program.md` file is essentially a super lightweight "skill".

## Project structure

```
prepare.py      — constants, data prep + runtime utilities (do not modify)
train.py        — model, optimizer, training loop (agent modifies this)
program.md      — agent instructions
pyproject.toml  — dependencies
```

```

---
## ruvnet/ruflo  (★69920, boundary — swarm self-description, openai-swarm dep (TEAM))
frameworks: ['openai-swarm'] | v1: i=MULTI ii=pipeline iii=JUDGE | v2: i=MULTI ii=TEAM iii=NO | probed=8 | tree=7203
agent-ish top dirs: ['.agents', 'AGENTS.md', 'agentdb.rvf', 'agentdb.rvf.lock']

### README (head)
```
<div align="center">

[![Ruflo Banner](ruflo/assets/ruflo-small.jpeg)](https://cognitum.one/agentic-engineering)

<!-- Try Ruflo — the 4 badges first-time visitors actually act on -->
[![Try the UI Beta — flo.ruv.io](https://img.shields.io/badge/_Try_the_UI_Beta-flo.ruv.io-6366f1?style=for-the-badge&logoColor=white&logo=svelte)](https://flo.ruv.io/)
[![npm version (ruflo)](https://img.shields.io/npm/v/ruflo?label=npx%20ruflo&style=for-the-badge&logo=npm&color=cb3837)](https://www.npmjs.com/package/ruflo)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Star on GitHub](https://img.shields.io/github/stars/ruvnet/claude-flow?style=for-the-badge&logo=github&color=gold)](https://github.com/ruvnet/claude-flow)

<!-- Ecosystem strip (collapsed visually with flat-square) -->
[![Goal Planner](https://img.shields.io/badge/_Goal_Planner-goal.ruv.io-8b5cf6?style=flat-square&logoColor=white&logo=react)](https://goal.ruv.io/)
[![Live Agents](https://img.shields.io/badge/_Live_Agents-goal.ruv.io%2Fagents-10b981?style=flat-square&logoColor=white&logo=react)](https://goal.ruv.io/agents)
[![🕸️ RuVector Agentic DB](https://img.shields.io/badge/RuVector_Agentic-DB-06b6d4?style=flat-square&logoColor=white&logo=graphql)](https://github.com/ruvnet/ruvector)
[![Ecosystem downloads](https://img.shields.io/badge/ecosystem%20downloads-8.1M%2B-blue?style=flat-square&logo=npm)](https://github.com/ruvnet/ruflo/blob/main/data/clone-data.proof.json)
[![Git clones (14d)](https://img.shields.io/badge/git%20clones%2014d-106k-blueviolet?style=flat-square&logo=github)](https://github.com/ruvnet/ruflo/blob/main/data/clone-data.ledger.json)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-D97757?style=flat-square&logoColor=white&logo=anthropic)](https://github.com/ruvnet/claude-flow)
[![Codex Plugin](https://img.shields.io/badge/Codex-Plugin-412991?style=flat-square&logoColor=white&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0yMi4yODIgOS44MjFhNS45ODUgNS45ODUgMCAwIDAtLjUxNi00LjkxIDYuMDQ2IDYuMDQ2IDAgMCAwLTYuNTEtMi45QTYuMDY1IDYuMDY1IDAgMCAwIDQuOTgxIDQuMThhNS45ODUgNS45ODUgMCAwIDAtMy45OTggMi45IDYuMDQ2IDYuMDQ2IDAgMCAwIC43NDMgNy4wOTcgNS45OCA1Ljk4IDAgMCAwIC41MSA0LjkxMSA2LjA1MSA2LjA1MSAwIDAgMCA2LjUxNSAyLjlBNS45ODUgNS45ODUgMCAwIDAgMTMuMjYgMjRhNi4wNTYgNi4wNTYgMCAwIDAgNS43NzItNC4yMDYgNS45OSA1Ljk5IDAgMCAwIDMuOTk4LTIuOSA2LjA1NiA2LjA1NiAwIDAgMC0uNzQ3LTcuMDczek0xMy4yNiAyMi40M2E0LjQ3NiA0LjQ3NiAwIDAgMS0yLjg3Ni0xLjA0bC4xNDItLjA4IDQuNzc4LTIuNzU4YS43OTUuNzk1IDAgMCAwIC4zOTMtLjY4MXYtNi43MzdsMi4wMiAxLjE2OGEuMDcxLjA3MSAwIDAgMSAuMDM4LjA1MnY1LjU4M2E0LjUwNCA0LjUwNCAwIDAgMS00LjQ5NSA0LjQ5NHpNMy42IDE4LjMwNGE0LjQ3IDQuNDcgMCAwIDEtLjUzNS0zLjAxNGwuMTQyLjA4NSA0Ljc4MyAyLjc1OWEuNzcxLjc3MSAwIDAgMCAuNzgxIDBsNS44NDMtMy4zNjl2Mi4zMzJhLjA4LjA4IDAgMCAxLS4wMzMuMDYyTDkuNzQgMTkuOTVhNC41IDQuNSAwIDAgMS02LjE0LTEuNjQ2ek0yLjM0IDcuODk2YTQuNDg1IDQuNDg1IDAgMCAxIDIuMzY2LTEuOTczVjExLjZhLjc2Ni43NjYgMCAwIDAgLjM4OC42NzdsNS44MTUgMy4zNTQtMi4wMiAxLjE2OGEuMDc2LjA3NiAwIDAgMS0uMDcyIDBsLTQuODMtMi43ODZBNC41MDQgNC41MDQgMCAwIDEgMi4zNCA3Ljg3MnptMTYuNTk3IDMuODU1LTUuODMzLTMuMzg3IDIuMDE2LTEuMTY1YS4wNzYuMDc2IDAgMCAxIC4wNzEgMGw0LjgzIDIuNzkxYTQuNDk0IDQuNDk0IDAgMCAxLS42NzYgOC4xMDR2LTUuNjc3YS43OS43OSAwIDAgMC0uNDA3LS42Njd6bTIuMDEtMy4wMjMtLjE0MS0uMDg1LTQuNzc0LTIuNzgyYS43NzYuNzc2IDAgMCAwLS43ODUgMEw5LjQwOSA5LjIzVjYuODk3YS4wNjYuMDY2IDAgMCAxIC4wMjgtLjA2Mmw0LjgzLTIuNzg3YTQuNDk5IDQuNDk5IDAgMCAxIDYuNjggNC42NnpNOC4zMDcgMTIuODYzbC0yLjAyLTEuMTY0YS4wOC4wOCAwIDAgMS0uMDM4LS4wNTdWNi4wNzRhNC40OTkgNC40OTkgMCAwIDEgNy4zNzYtMy40NTRsLS4xNDIuMDgtNC43NzggMi43NThhLjc5NS43OTUgMCAwIDAtLjM5My42ODJ6bTEuMDk3LTIuMzY2IDIuNjAyLTEuNSAyLjYwNyAxLjV2Mi45OTlsLTIuNTk3IDEuNS0yLjYwNy0xLjVaIi8%2BPC9zdmc%2B)](https://www.npmjs.com/package/@claude-flow/codex)

# Ruflo

**An agent meta-harness for Claude Code and Codex.**

</div>

> **Agent = Model + Harness.** The model writes; the harness gives it tools, memory, loops, sandboxes, and controls so it can actually work. **Ruflo is the harness** — the execution layer around Claude Code and Codex that adds 100+ specialized agents, coordinated swarms, self-learning memory, federated comms across machines, and enterprise security guardrails. So agents don't just run, they collaborate.

One `npx ruflo init` gives Claude Code a nervous system: agents self-organize into swarms, learn from every task, remember across sessions, and — with federation — securely talk to agents on other machines without leaking data. You keep writing code. Ruflo handles the coordination.

```
Self-Learning / Self-Optimizing Agent Architecture

User --> Ruflo (CLI/MCP) --> Router --> Swarm --> Agents --> Memory --> LLM Providers
                          ^                           |
                          +---- Learning Loop <-------+
```

> **New to Ruflo?** You don't need to learn 314 MCP tools or 26 CLI commands. After `init`, just use Claude Code normally — the hooks system automatically routes tasks, learns from successful patterns, and coordinates agents in the background.

<details>
<summary><strong>📖 Background — where the name comes from</strong></summary>

> Claude Flow is now Ruflo — named by [`rUv`](https://ruv.io), who loves Rust, flow states, and building things that feel inevitable. The "Ru" is the rUv. The "flo" is working until 3am. Underneath, powered by [`Cognitum.One`](https://cognitum.one/?RuFlo) agentic architecture, running a supercharged Rust-based AI engine, embeddings, memory, and plugin system.

</details>

---

![Ruflo Plugins](./ruflo-plugins.gif)

## Quick Start

There are **two different install paths** with very different surface areas. Pick based on what you need (#1744):

| | **Claude Code Plugin** | **CLI install (`npx ruflo init`)** |
|---|---|---|
| What it gives you | Slash commands + a few skills + agent definitions per-plugin | Full Ruflo loop — 98 agents, 60+ commands, 30 skills, MCP server, hooks, daemon |
| Files in your workspace | **Zero** | `.claude/`, `.claude-flow/`, `CLAUDE.md`, helpers, settings |
| MCP server registered | Only if `ruflo-core` is installed (it ships its own `.mcp.json`) — most other plugins don't | Yes |
| Hooks installed | No | Yes |
```

---
## siyuan-note/siyuan  (★46070, gap anchor — knowledge workspace app in headline SINGLE list)
frameworks: [] | v1: i=MULTI ii=pipeline iii=UNKNOWN | v2: i=SINGLE ii=SINGLE iii=NO | probed=8 | tree=3740
agent-ish top dirs: ['AGENTS.md']

### README (head)
```
<p align="center">
<img alt="SiYuan" src="https://b3log.org/images/brand/siyuan-128.png">
<br>
<em>From thought to insight, with agents</em>
<br><br>
<a title="Build Status" target="_blank" href="https://github.com/siyuan-note/siyuan/actions/workflows/cd.yml"><img src="https://img.shields.io/github/actions/workflow/status/siyuan-note/siyuan/cd.yml?style=flat-square"></a>
<a title="Releases" target="_blank" href="https://github.com/siyuan-note/siyuan/releases"><img src="https://img.shields.io/github/release/siyuan-note/siyuan.svg?style=flat-square&color=9CF"></a>
<a title="Downloads" target="_blank" href="https://github.com/siyuan-note/siyuan/releases"><img src="https://img.shields.io/github/downloads/siyuan-note/siyuan/total.svg?style=flat-square&color=blueviolet"></a>
<br>
<a title="Docker Pulls" target="_blank" href="https://hub.docker.com/r/b3log/siyuan"><img src="https://img.shields.io/docker/pulls/b3log/siyuan.svg?style=flat-square&color=green"></a>
<a title="Docker Image Size" target="_blank" href="https://hub.docker.com/r/b3log/siyuan"><img src="https://img.shields.io/docker/image-size/b3log/siyuan.svg?style=flat-square&color=ff96b4"></a>
<a title="Hits" target="_blank" href="https://github.com/siyuan-note/siyuan"><img src="https://hits.b3log.org/siyuan-note/siyuan.svg"></a>
<br>
<a title="AGPLv3" target="_blank" href="https://www.gnu.org/licenses/agpl-3.0.txt"><img src="http://img.shields.io/badge/license-AGPLv3-orange.svg?style=flat-square"></a>
<a title="Code Size" target="_blank" href="https://github.com/siyuan-note/siyuan"><img src="https://img.shields.io/github/languages/code-size/siyuan-note/siyuan.svg?style=flat-square&color=yellow"></a>
<a title="GitHub Pull Requests" target="_blank" href="https://github.com/siyuan-note/siyuan/pulls"><img src="https://img.shields.io/github/issues-pr-closed/siyuan-note/siyuan.svg?style=flat-square&color=FF9966"></a>
<br>
<a title="GitHub Commits" target="_blank" href="https://github.com/siyuan-note/siyuan/commits/master"><img src="https://img.shields.io/github/commit-activity/m/siyuan-note/siyuan.svg?style=flat-square"></a>
<a title="Last Commit" target="_blank" href="https://github.com/siyuan-note/siyuan/commits/master"><img src="https://img.shields.io/github/last-commit/siyuan-note/siyuan.svg?style=flat-square&color=FF9900"></a>
<br><br>
<a title="X" target="_blank" href="https://x.com/b3logos"><img alt="X Follow" src="https://img.shields.io/twitter/follow/b3logos?label=Follow&style=social"></a>
<br><br>
<a href="https://trendshift.io/repositories/3949" target="_blank"><img src="https://trendshift.io/api/badge/repositories/3949" alt="siyuan-note%2Fsiyuan | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

<p align="center">
<b>English</b>
| <a href="README.zh-CN.md">中文</a>
| <a href="README.ja.md">日本語</a>
| <a href="README.tr.md">Türkçe</a>
</p>

---

## Table of Contents

- [💡 Introduction](#-introduction)
- [🔮 Features](#-features)
- [🏗️ Architecture and Ecosystem](#-architecture-and-ecosystem)
- [🗺️ Roadmap](#️-roadmap)
- [🚀 Download Setup](#-download-setup)
  - [App Market](#app-market)
  - [Installation Package](#installation-package)
  - [Package Manager](#package-manager)
  - [Docker Hosting](#docker-hosting)
  - [Unraid Hosting](#unraid-hosting)
  - [TrueNAS Hosting](#truenas-hosting)
  - [Test Channels](#test-channels)
- [⌨️ Command-line Interface](#-command-line-interface)
- [🏘️ Community](#️-community)
- [🛠️ Development Guide](#️-development-guide)
- [❓ FAQ](#-faq)
  - [How does SiYuan store data?](#how-does-siyuan-store-data)
  - [Does it support data synchronization through a third-party sync disk?](#does-it-support-data-synchronization-through-a-third-party-sync-disk)
  - [Is SiYuan open source?](#is-siyuan-open-source)
  - [How to upgrade to a new version?](#how-to-upgrade-to-a-new-version)
  - [What if some blocks (such as paragraph blocks in list items) cannot find the block icon?](#what-if-some-blocks-such-as-paragraph-blocks-in-list-items-cannot-find-the-block-icon)
  - [What should I do if the data repo key is lost?](#what-should-i-do-if-the-data-repo-key-is-lost)
  - [Do I need to pay for it?](#do-i-need-to-pay-for-it)
- [🙏 Acknowledgement](#-acknowledgement)
```

---
## bytedance/UI-TARS-desktop  (★38769, gap anchor — single GUI agent (headline list))
frameworks: [] | v1: i=MULTI ii=worker iii=JUDGE | v2: i=SINGLE ii=SINGLE iii=NO | probed=8 | tree=3175
agent-ish top dirs: []

### README (head)
```
<picture>
  <img alt="Agent TARS Banner" src="./images/tars.png">
</picture>

<br/>

## Introduction

English | [简体中文](./README.zh-CN.md)

[![](https://trendshift.io/api/badge/repositories/13584)](https://trendshift.io/repositories/13584)

<b>TARS<sup>\*</sup></b> is a Multimodal AI Agent stack, currently shipping two projects: [Agent TARS](#agent-tars) and [UI-TARS-desktop](#ui-tars-desktop):

<table>
  <thead>
    <tr>
      <th width="50%" align="center"><a href="#agent-tars">Agent TARS</a></th>
      <th width="50%" align="center"><a href="#ui-tars-desktop">UI-TARS-desktop</a></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center">
        <video src="https://github.com/user-attachments/assets/c9489936-afdc-4d12-adda-d4b90d2a869d" width="50%"></video>
      </td>
      <td align="center">
        <video src="https://github.com/user-attachments/assets/e0914ce9-ad33-494b-bdec-0c25c1b01a27" width="50%"></video>
      </td>
    </tr>
    <tr>
      <td align="left">
        <b>Agent TARS</b> is a general multimodal AI Agent stack, it brings the power of GUI Agent and Vision into your terminal, computer, browser and product.
        <br>
        <br>
        It primarily ships with a <a href="https://agent-tars.com/guide/basic/cli.html" target="_blank">CLI</a> and <a href="https://agent-tars.com/guide/basic/web-ui.html" target="_blank">Web UI</a> for usage.
        It aims to provide a workflow that is closer to human-like task completion through cutting-edge multimodal LLMs and seamless integration with various real-world <a href="https://agent-tars.com/guide/basic/mcp.html" target="_blank">MCP</a> tools.
      </td>
      <td align="left">
        <b>UI-TARS Desktop</b> is a desktop application that provides a native GUI Agent based on the <a href="https://github.com/bytedance/UI-TARS" target="_blank">UI-TARS</a> model.
        <br>
        <br>
        It primarily ships a
        <a href="https://github.com/bytedance/UI-TARS-desktop/blob/main/docs/quick-start.md#get-model-and-run-local-operator" target="_blank">local</a> and 
        <a href="https://github.com/bytedance/UI-TARS-desktop/blob/main/docs/quick-start.md#run-remote-operator" target="_blank">remote</a> computer as well as browser operators.
      </td>
    </tr>
  </tbody>
</table>

## Table of Contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [News](#news)
- [Agent TARS](#agent-tars)
  - [Showcase](#showcase)
  - [Core Features](#core-features)
  - [Quick Start](#quick-start)
```

---
## musistudio/claude-code-router  (★36985, gap anchor — router, not MAS (headline list))
frameworks: [] | v1: i=MULTI ii=worker iii=NO | v2: i=SINGLE ii=SINGLE iii=NO | probed=8 | tree=985
agent-ish top dirs: []

### README (head)
```
<div align="center">

<table width="100%">
  <tr>
    <td align="center">
      <a href="https://www.kimi.com/code?aff=ccr">
        <img src="https://gcdn.moonshot.cn/growth-cdn/sponsor/kimi-en.png" width="960" alt="Kimi K2.7 Code sponsor banner" />
      </a>
      <br />
      <sub>
        <a href="https://www.kimi.com/code?aff=ccr"><strong>Kimi Code Subscription</strong></a>
        &nbsp;·&nbsp;
        <a href="https://platform.kimi.ai?aff=ccr"><strong>API Global</strong></a>
        &nbsp;·&nbsp;
        <a href="https://platform.kimi.com?aff=ccr">API China</a>
      </sub>
    </td>
  </tr>
  <tr>
    <td align="left">
      <p>
        <strong>Thanks to Kimi for sponsoring this project!</strong> Kimi K3 is Moonshot AI's most capable model and the world's first open 3T-class model. With 2.8 trillion parameters, native vision, and a 1-million-token context window, K3 delivers frontier performance across long-horizon coding, knowledge work, and reasoning. Inside CCR, Kimi ships as a built-in provider preset: import the pay-as-you-go API or Kimi Code subscription in one click and route your coding agent's requests to Kimi. The subscription endpoint passes through natively without protocol conversion, API endpoints are adapted automatically, and account balance and subscription usage are visible in the CCR dashboard.
      </p>
      <p align="center">
        CCR already includes Kimi provider presets. Visit the Kimi Open Platform (<a href="https://platform.kimi.com?aff=ccr">中文站</a> | <a href="https://platform.kimi.ai?aff=ccr">Global</a>) to try the API, or explore the <a href="https://www.kimi.com/code?aff=ccr">Kimi Code subscription</a>.
      </p>
    </td>
  </tr>
</table>

</div>

<div align="center">

# Claude Code Router

### Manage every agent and provider from one place.

Connect Claude Code, Claude Design, Codex, Grok CLI, Kimi CLI, Kilo Code, OpenCode, Pi, ZCode, WorkBuddy, and compatible API clients to the providers you choose—then route, fail over, extend, and observe every request from one app.

<p>
  <a href="https://github.com/musistudio/claude-code-router/releases"><img alt="Download Desktop" src="https://img.shields.io/badge/Download-Desktop_App-2563EB?style=for-the-badge&logo=github&logoColor=white" /></a>
  <a href="#quick-start"><img alt="Quick Start" src="https://img.shields.io/badge/Get_Started-Quick_Start-16A34A?style=for-the-badge&logo=rocket&logoColor=white" /></a>
  <a href="https://ccrdesk.top/"><img alt="Read the Docs" src="https://img.shields.io/badge/Explore-Documentation-0F172A?style=for-the-badge&logo=readthedocs&logoColor=white" /></a>
</p>

<p>
  <a href="README_zh.md"><img alt="Chinese README" src="https://img.shields.io/badge/%F0%9F%87%A8%F0%9F%87%B3-%E4%B8%AD%E6%96%87%E7%89%88-ff0000?style=flat" /></a>
  <a href="https://discord.gg/rdftVMaUcS"><img alt="Discord" src="https://img.shields.io/badge/Discord-%235865F2.svg?&logo=discord&logoColor=white" /></a>
  <a href="https://x.com/musistudio2026"><img alt="X" src="https://img.shields.io/badge/X-@musistudio2026-000000?logo=x&logoColor=white" /></a>
  <a href="https://github.com/musistudio/claude-code-router/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/musistudio/claude-code-router" /></a>
</p>

<br />

<img src="blog/images/claude-code-router.png" width="820" alt="Claude Code Router Desktop dashboard" />

</div>

## Why use Claude Code Router?
```

---
## volcengine/OpenViking  (★34601, gate verify — agent context/memory DB (semi-seen: held-out catch))
frameworks: ['langchain', 'langgraph'] | v1: i=MULTI ii=worker iii=JUDGE | v2: i=SINGLE ii=SINGLE iii=NO | probed=8 | tree=4696
agent-ish top dirs: ['agent-plugins', '.agents', '.pr_agent.toml']

### README (head)
```
<div align="center">

<a href="https://openviking.ai/" target="_blank">
  <picture>
    <img alt="OpenViking" src="docs/images/ov-logo.png" width="200px" height="auto">
  </picture>
</a>

### OpenViking: The Context Database for AI Agents

English / [中文](README_CN.md) / [日本語](README_JA.md)

<a href="https://www.openviking.ai">Website</a> · <a href="https://openviking.ai/studio">Live Demo</a> · <a href="https://github.com/volcengine/OpenViking">GitHub</a> · <a href="https://github.com/volcengine/OpenViking/issues">Issues</a> · <a href="https://docs.openviking.ai/">Docs</a>

[![](https://img.shields.io/github/v/release/volcengine/OpenViking?color=369eff\&labelColor=black\&logo=github\&style=flat-square)](https://github.com/volcengine/OpenViking/releases)
[![](https://img.shields.io/github/stars/volcengine/OpenViking?labelColor\&style=flat-square\&color=ffcb47)](https://github.com/volcengine/OpenViking)
[![](https://img.shields.io/github/issues/volcengine/OpenViking?labelColor=black\&style=flat-square\&color=ff80eb)](https://github.com/volcengine/OpenViking/issues)
[![](https://img.shields.io/github/contributors/volcengine/OpenViking?color=c4f042\&labelColor=black\&style=flat-square)](https://github.com/volcengine/OpenViking/graphs/contributors)
[![](https://img.shields.io/badge/license-AGPLv3-white?labelColor=black\&style=flat-square)](https://github.com/volcengine/OpenViking/blob/main/LICENSE)
[![](https://img.shields.io/github/last-commit/volcengine/OpenViking?color=c4f042\&labelColor=black\&style=flat-square)](https://github.com/volcengine/OpenViking/commits/main)

👋 Join our Community

📱 <a href="https://docs.openviking.ai/en/about/01-about-us#lark-group">Lark Group</a> · <a href="https://docs.openviking.ai/en/about/01-about-us#wechat-group">WeChat</a> · <a href="https://discord.com/invite/eHvx8E9XF3">Discord</a> · <a href="https://x.com/openvikingai">X</a>

<a href="https://trendshift.io/repositories/19668" target="_blank"><img src="https://trendshift.io/api/badge/repositories/19668" alt="volcengine%2FOpenViking | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

</div>

***

## What is OpenViking

OpenViking is an open-source context database for AI agents. It stores memories, resources, and skills as one virtual filesystem under the `viking://` protocol, so an agent browses its own context with `ls`, `tree`, and `find` instead of querying a black-box vector store. Content is processed into three tiers — L0 abstract, L1 overview, L2 details — and loaded on demand. Every retrieval leaves a trajectory you can watch and debug. Full introduction: [Getting started](https://docs.openviking.ai/en/getting-started/01-introduction).

[![OpenViking Studio playground](docs/images/studio-playground.png)](https://openviking.ai/studio)

*The [OpenViking Studio](https://openviking.ai/studio) playground — a live demo you can open in the browser, no installation required.*

## Why OpenViking

- **One filesystem for all context.** Memories, resources, and skills each get a `viking://` URI. Agents locate and manipulate context deterministically, like a developer working with files. → [Viking URI](https://docs.openviking.ai/en/concepts/04-viking-uri) · [Context types](https://docs.openviking.ai/en/concepts/02-context-types)
- **Tiered loading cuts token spend.** Every entry is processed into L0 (abstract), L1 (overview), and L2 (details) on write, then loaded only as deep as the task requires. → [Context layers](https://docs.openviking.ai/en/concepts/03-context-layers)
- **Directory recursive retrieval.** Vector search first locates the highest-scoring directory, then drills down layer by layer, so results arrive with their surrounding context intact. → [Retrieval](https://docs.openviking.ai/en/concepts/07-retrieval)
- **Observable retrieval.** Each query preserves its directory-browsing trajectory. When a result looks wrong, you can see exactly which path produced it. → [Retrieval](https://docs.openviking.ai/en/concepts/07-retrieval)
- **Sessions become memory.** After a session commits, OpenViking asynchronously extracts user preferences and agent experience into long-term memory. → [Session](https://docs.openviking.ai/en/concepts/08-session)

How the pieces fit together: [Architecture](https://docs.openviking.ai/en/concepts/01-architecture). The thinking behind the design: [The Database Paradigm for Context Engineering](https://blog.openviking.ai/post/openviking-context-database/).

```
viking://
├── resources/              # Resources: project docs, repos, web pages, etc.
│   └── my_project/
│       ├── docs/
│       │   ├── api/
│       │   └── tutorials/
│       └── src/
└── user/
    └── {user_id}/
        ├── memories/
```

---
## rohitg00/agentmemory  (★27834, gap anchor — memory layer for agents (infra))
frameworks: [] | v1: i=MULTI ii=worker iii=JUDGE | v2: i=SINGLE ii=SINGLE iii=NO | probed=8 | tree=767
agent-ish top dirs: ['AGENTS.md', 'INSTALL_FOR_AGENTS.md']

### README (head)
```
<p align="center">
  <img src="assets/banner.png" alt="agentmemory: persistent memory for AI coding agents" width="720" />
</p>

<p align="center">
  <strong>
    Your coding agent remembers everything. No more re-explaining.
    Built on <a href="https://github.com/iii-hq/iii">iii engine</a>
  </strong><br/>
  Persistent memory for Claude Code, GitHub Copilot CLI, Cursor, Gemini CLI, Codex CLI, Hermes, OpenClaw, pi, OpenCode, and any MCP client.
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="READMEs/README.zh-CN.md">简体中文</a> |
  <a href="READMEs/README.zh-TW.md">繁體中文</a> |
  <a href="READMEs/README.ja-JP.md">日本語</a> |
  <a href="READMEs/README.ko-KR.md">한국어</a> |
  <a href="READMEs/README.es-ES.md">Español</a> |
  <a href="READMEs/README.tr-TR.md">Türkçe</a> |
  <a href="READMEs/README.ru-RU.md">Русский</a> |
  <a href="READMEs/README.hi-IN.md">हिन्दी</a> |
  <a href="READMEs/README.pt-BR.md">Português</a> |
  <a href="READMEs/README.fr-FR.md">Français</a> |
  <a href="READMEs/README.de-DE.md">Deutsch</a>
</p>

<p align="center">
  <a href="https://trendshift.io/repositories/25123" target="_blank"><img src="https://trendshift.io/api/badge/repositories/25123" alt="rohitg00/agentmemory | Trendshift" width="250" height="55"/></a>
</p>

<p align="center">
  <a href="https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2"><img src="https://img.shields.io/badge/Viral%20GitHub%20Gist-1.6k%20stars%20%2F%20230%20forks-FF6B35?style=for-the-badge&logo=github&logoColor=white&labelColor=1a1a1a" alt="Design doc: 1.6k stars / 230 forks on the gist" /></a>
</p>

<p align="center">
  <em>The gist extends Karpathy's LLM Wiki pattern with confidence scoring, lifecycle, knowledge graphs, and hybrid search: agentmemory is the implementation.</em>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/@agentmemory/agentmemory"><img src="https://img.shields.io/npm/v/@agentmemory/agentmemory?color=CB3837&label=npm&style=for-the-badge&logo=npm" alt="npm version" /></a>
  <a href="https://github.com/rohitg00/agentmemory/actions"><img src="https://img.shields.io/github/actions/workflow/status/rohitg00/agentmemory/ci.yml?label=tests&style=for-the-badge&logo=github" alt="CI" /></a>
  <a href="https://github.com/rohitg00/agentmemory/blob/main/LICENSE"><img src="https://img.shields.io/github/license/rohitg00/agentmemory?color=blue&style=for-the-badge" alt="License" /></a>
  <a href="https://github.com/rohitg00/agentmemory/stargazers"><img src="https://img.shields.io/github/stars/rohitg00/agentmemory?style=for-the-badge&color=yellow&logo=github" alt="Stars" /></a>
</p>

<p align="center">
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/tags/light/stat-recall.svg"><img src="assets/tags/stat-recall.svg" alt="95.2% retrieval R@5" height="38" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/tags/light/stat-tokens.svg"><img src="assets/tags/stat-tokens.svg" alt="92% fewer tokens" height="38" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/tags/light/stat-tools.svg"><img src="assets/tags/stat-tools.svg" alt="54 MCP tools" height="38" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/tags/light/stat-hooks.svg"><img src="assets/tags/stat-hooks.svg" alt="12 auto hooks" height="38" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/tags/light/stat-deps.svg"><img src="assets/tags/stat-deps.svg" alt="0 external DBs" height="38" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/tags/light/stat-tests.svg"><img src="assets/tags/stat-tests.svg" alt="1,674+ tests passing" height="38" /></picture>
</p>

<p align="center">
  <img src="assets/demo.gif" alt="agentmemory demo" width="720" />
</p>

<p align="center">
```

---
## QwenLM/qwen-code  (★27518, gap anchor — single coding agent (IDE))
frameworks: [] | v1: i=MULTI ii=worker iii=JUDGE | v2: i=SINGLE ii=SINGLE iii=NO | probed=7 | tree=8281
agent-ish top dirs: ['AGENTS.md']

### README (head)
```
<div align="center">

[![npm version](https://img.shields.io/npm/v/@qwen-code/qwen-code.svg)](https://www.npmjs.com/package/@qwen-code/qwen-code)
[![License](https://img.shields.io/github/license/QwenLM/qwen-code.svg)](./LICENSE)
[![Node.js Version](https://img.shields.io/badge/node-%3E%3D22.0.0-brightgreen.svg)](https://nodejs.org/)
[![Downloads](https://img.shields.io/npm/dm/@qwen-code/qwen-code.svg)](https://www.npmjs.com/package/@qwen-code/qwen-code)

<a href="https://trendshift.io/repositories/15287" target="_blank"><img src="https://trendshift.io/api/badge/repositories/15287" alt="QwenLM%2Fqwen-code | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

**The open-source AI coding agent that lives in your terminal.**

<a href="https://qwenlm.github.io/qwen-code-docs/zh/users/overview">中文</a> |
<a href="https://qwenlm.github.io/qwen-code-docs/de/users/overview">Deutsch</a> |
<a href="https://qwenlm.github.io/qwen-code-docs/fr/users/overview">français</a> |
<a href="https://qwenlm.github.io/qwen-code-docs/ja/users/overview">日本語</a> |
<a href="https://qwenlm.github.io/qwen-code-docs/ru/users/overview">Русский</a> |
<a href="https://qwenlm.github.io/qwen-code-docs/pt-BR/users/overview">Português (Brasil)</a> |
<a href="https://qwenlm.github.io/qwen-code-docs/ko/users/overview">한국어</a>

</div>

## Why Qwen Code?

- **Agentic out of the box** — Auto-Memory, Auto-Skills, SubAgents, Agent Teams, and MCP. Dynamic workflows, zero setup.
- **Open-source, inside and out** — The framework and the Qwen models are open-source. They evolve together. No vendor lock-in.
- **Multi-protocol** — Supports OpenAI, Anthropic, Gemini, and Qwen APIs. Any third-party provider or local model (Ollama / vLLM). Switch at runtime.
- **Beyond the terminal** — IDE plugins, Desktop app, daemon mode, SDKs, and IM bots (Telegram / DingTalk / WeChat / Feishu).

> [!TIP]
> Qwen Code is actively iterating on itself — using its own agent and models to file issues, submit PRs, review code, and run tests. Powered by the community, driven by AI.

## Installation

**Linux / macOS:**

```bash
curl -fsSL https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen-standalone.sh | bash
```

**Windows:**

```powershell
irm https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen-standalone.ps1 | iex
```

> Restart your terminal after installation to ensure environment variables take effect.

<details>
<summary>NPM / Homebrew</summary>

**NPM** (requires [Node.js 22+](https://nodejs.org/)):

```bash
npm install -g @qwen-code/qwen-code@latest
```

**Homebrew** (macOS / Linux):

```bash
brew install qwen-code
```

---
## emcie-co/parlant  (★18269, boundary i/ii — langchain dep, v2 UNKNOWN)
frameworks: ['langchain'] | v1: i=SINGLE ii=pipeline iii=JUDGE | v2: i=MULTI ii=UNKNOWN iii=NO | probed=8 | tree=919
agent-ish top dirs: []

### README (head)
```
<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/emcie-co/parlant/blob/develop/docs/LogoTransparentLight.png?raw=true">
  <img alt="Parlant" src="https://github.com/emcie-co/parlant/blob/develop/docs/LogoTransparentDark.png?raw=true" width=400 />
</picture>

### The interaction control harness for customer-facing AI agents

<p>
  <a href="https://pypi.org/project/parlant/"><img alt="PyPI" src="https://img.shields.io/pypi/v/parlant?color=blue"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10+-blue">
  <a href="https://opensource.org/licenses/Apache-2.0"><img alt="License" src="https://img.shields.io/badge/license-Apache%202.0-green"></a>
  <a href="https://discord.gg/duxWqxKk6J"><img alt="Discord" src="https://img.shields.io/discord/1312378700993663007?color=7289da&logo=discord&logoColor=white"></a>
  <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/emcie-co/parlant?style=social">
</p>

<p>
  <a href="https://www.parlant.io/" target="_blank">Website</a> &bull;
  <a href="https://www.parlant.io/docs/quickstart/installation" target="_blank">Quick Start</a> &bull;
  <a href="https://www.parlant.io/docs/quickstart/examples" target="_blank">Examples</a> &bull;
  <a href="https://discord.gg/duxWqxKk6J" target="_blank">Discord</a>
</p>

<p>
  <a href="https://zdoc.app/de/emcie-co/parlant">Deutsch</a> |
  <a href="https://zdoc.app/es/emcie-co/parlant">Español</a> |
  <a href="https://zdoc.app/fr/emcie-co/parlant">français</a> |
  <a href="https://zdoc.app/ja/emcie-co/parlant">日本語</a> |
  <a href="https://zdoc.app/ko/emcie-co/parlant">한국어</a> |
  <a href="https://zdoc.app/pt/emcie-co/parlant">Português</a> |
  <a href="https://zdoc.app/ru/emcie-co/parlant">Русский</a> |
  <a href="https://zdoc.app/zh/emcie-co/parlant">中文</a>
</p>

<a href="https://trendshift.io/repositories/12768" target="_blank">
  <img src="https://trendshift.io/api/badge/repositories/12768" alt="Trending" style="width: 250px; height: 55px;" width="250" height="55"/>
</a>

</div>

&nbsp;

> **Looking for an open-source alternative to Ada, Decagon, or Sierra?**

**Parlant is production-ready. It streamlines the development and maintenance of enterprise-grade B2C (business-to-consumer) and sensitive B2B interactions that need to be consistent, compliant, on-brand, and comprehensively traceable.**

## Why Parlant?

Conversational context engineering is hard because real-world interactions are diverse, nuanced, and non-linear.

### ❌ The Problem: What you've probably tried and couldn't get to work at scale
**System prompts** work until production complexity kicks in. The more instructions you add to a prompt, the faster your agent stops paying attention to any of them.

**Routed graphs** solve the prompt-overload problem, but the more routing you add, the more fragile it becomes when faced with the chaos of natural interactions.

### 🔑 The Solution: Context engineering, optimized for conversational control
Parlant is an agentic harness offering optimized [context engineering](https://www.gartner.com/en/articles/context-engineering) for conversational use cases: getting the right context, no more and no less, into the prompt at the right time. You define rules, knowledge, and tools once, while the engine narrows the context down in real-time to what's immediately relevant to each turn of the conversation.

<img alt="Parlant Demo" src="https://github.com/emcie-co/parlant/blob/develop/docs/demo.gif?raw=true" width="100%" />
```

---
## NVIDIA/SkillSpector  (★15374, real-MAS — langchain+langgraph, v2 ORCH-WORKER)
frameworks: ['langchain', 'langgraph'] | v1: i=MULTI ii=pipeline iii=JUDGE | v2: i=MULTI ii=ORCH-WORKER iii=NO | probed=6 | tree=411
agent-ish top dirs: []

### README (head)
```
# SkillSpector

**Security scanner for AI agent skills.** Detect vulnerabilities, malicious patterns, and security risks before installing agent skills.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/NVIDIA/SkillSpector/badge)](https://scorecard.dev/viewer/?uri=github.com/NVIDIA/SkillSpector)

## Overview

AI agent skills (used by Claude Code, Codex CLI, Gemini CLI, etc.) execute with implicit trust and minimal vetting. Research shows that **26.1% of skills contain vulnerabilities** and **5.2% show likely malicious intent**.

SkillSpector helps you answer: **"Is this skill safe to install?"**

SkillSpector is part of the [NVIDIA Verified Skills pipeline](https://docs.nvidia.com/skills/), which scans, evaluates, and signs agent skills before publication. Skills that pass are published to the [NVIDIA skills catalog](https://github.com/NVIDIA/skills).

## Documentation

- **[Scan agent skills before installation](https://docs.nvidia.com/skills/scanning-agent-skills)** — Hosted guide: when to scan, how to read a report, and how to gate installs.
- **[Development guide](docs/DEVELOPMENT.md)** — Architecture, package layout, and how to extend the analyzer pipeline.
- **[Analysis resource bounds](docs/ANALYSIS_RESOURCE_BOUNDS.md)** — Fail-closed bundle, parser, nested-artifact, ledger, and finding ceilings.
- **[Pi extension](docs/PI_EXTENSION.md)** — Install SkillSpector as a Pi tool for scanning skills from inside agent sessions.

## Features

- **Multi-format input**: Scan Git repos, URLs, zip files, directories, or single files
- **71 vulnerability patterns** across 17 categories: prompt injection, data exfiltration, privilege escalation, supply chain, excessive agency, output handling, system prompt leakage, memory poisoning, tool misuse, rogue agent, anti-refusal, trigger abuse, dangerous code (AST), taint tracking, YARA signatures, MCP least privilege, and MCP tool poisoning
- **Two-stage analysis**: Fast static analysis + optional LLM semantic evaluation
- **Live vulnerability lookups**: SC4 queries [OSV.dev](https://osv.dev) for real-time CVE data with automatic offline fallback
- **Multiple output formats**: Terminal, JSON, Markdown, and SARIF reports
- **Risk scoring**: 0-100 score with severity labels and clear recommendations
- **Baseline / false-positive suppression**: Accept known findings via a glob-rule or fingerprint baseline so re-scans surface only *new* issues ([docs](docs/SUPPRESSION.md))

## Quick Start

### Installation

> **Open-source software notice:** This project will download and install additional third-party open source software projects. Review the license terms of these open source projects before use.

Create and activate a virtual environment first (all `make` targets assume the venv is active). Use **uv** or **pip**; the Makefile uses `uv` if available, otherwise `pip`.

**Quick install with uv (CLI-only):**

```bash
uv tool install git+https://github.com/NVIDIA/skillspector.git
# Update later: uv tool update skillspector
```

If you plan to run `skillspector mcp`, install the MCP extra at install time:

```bash
uv tool install 'skillspector[mcp] @ git+https://github.com/NVIDIA/skillspector.git'
```

**From source:**

```bash
# Clone the repository
git clone https://github.com/NVIDIA/skillspector.git
cd skillspector
```

---
## microsoft/RD-Agent  (★14382, boundary — langchain dep, v2 UNKNOWN (research dev agent))
frameworks: ['langchain'] | v1: i=MULTI ii=worker iii=JUDGE | v2: i=MULTI ii=UNKNOWN iii=NO | probed=8 | tree=1189
agent-ish top dirs: ['rdagent']

### README (head)
```
<h4 align="center">
  <img src="docs/_static/logo.png" alt="RA-Agent logo" style="width:70%; ">
  
  <a href="https://rdagent.azurewebsites.net" target="_blank">🖥️ Live Demo</a> |
  <a href="https://rdagent.azurewebsites.net/factor_loop" target="_blank">🎥 Demo Video</a> <a href="https://www.youtube.com/watch?v=JJ4JYO3HscM&list=PLALmKB0_N3_i52fhUmPQiL4jsO354uopR" target="_blank">▶️YouTube</a>   |
  <a href="https://rdagent.readthedocs.io/en/latest/index.html" target="_blank">📖 Documentation</a> |
  <a href="https://aka.ms/RD-Agent-Tech-Report" target="_blank">📄 Tech Report</a> |
  <a href="#-paperwork-list"> 📃 Papers </a>
</h3>


[![CI](https://github.com/microsoft/RD-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/microsoft/RD-Agent/actions/workflows/ci.yml)
[![CodeQL](https://github.com/microsoft/RD-Agent/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/microsoft/RD-Agent/actions/workflows/github-code-scanning/codeql)
[![Dependabot Updates](https://github.com/microsoft/RD-Agent/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/microsoft/RD-Agent/actions/workflows/dependabot/dependabot-updates)
[![Lint PR Title](https://github.com/microsoft/RD-Agent/actions/workflows/pr.yml/badge.svg)](https://github.com/microsoft/RD-Agent/actions/workflows/pr.yml)
[![Release.yml](https://github.com/microsoft/RD-Agent/actions/workflows/release.yml/badge.svg)](https://github.com/microsoft/RD-Agent/actions/workflows/release.yml)
[![Platform](https://img.shields.io/badge/platform-Linux-blue)](https://pypi.org/project/rdagent/#files)
[![PyPI](https://img.shields.io/pypi/v/rdagent)](https://pypi.org/project/rdagent/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rdagent)](https://pypi.org/project/rdagent/)
[![Release](https://img.shields.io/github/v/release/microsoft/RD-Agent)](https://github.com/microsoft/RD-Agent/releases)
[![GitHub](https://img.shields.io/github/license/microsoft/RD-Agent)](https://github.com/microsoft/RD-Agent/blob/main/LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Chat](https://img.shields.io/badge/chat-discord-blue)](https://discord.gg/ybQ97B6Jjy)
[![Documentation Status](https://readthedocs.org/projects/rdagent/badge/?version=latest)](https://rdagent.readthedocs.io/en/latest/?badge=latest)
[![Readthedocs Preview](https://github.com/microsoft/RD-Agent/actions/workflows/readthedocs-preview.yml/badge.svg)](https://github.com/microsoft/RD-Agent/actions/workflows/readthedocs-preview.yml) <!-- this badge is too long, please place it in the last one to make it pretty --> 
[![arXiv](https://img.shields.io/badge/arXiv-2505.14738-00ff00.svg)](https://arxiv.org/abs/2505.14738)


# 📰 News
| 🗞️ News        | 📝 Description                 |
| --            | ------      |
| [Agent² RL-Bench Preprint](https://arxiv.org/abs/2604.10547) | A benchmark for evaluating LLM agents on end-to-end post-training engineering. See the [project page](https://wanyichen06.github.io/agent2-rlbench/) and [code](rdagent/scenarios/rl/autorl_bench/README.md). |
| ICML 2026 Acceptance | We are thrilled to announce that our paper [FT-Dojo: Towards Autonomous LLM Fine-Tuning with Language Agents](https://arxiv.org/abs/2603.01712) has been accepted to ICML 2026. The FT-Agent implementation is available in the [LLM fine-tuning guide](rdagent/app/finetune/llm/README.md). |
| ACL 2026 Findings Acceptance | We are thrilled to announce that our paper [Reasoning as Gradient](https://arxiv.org/abs/2603.01692) has been accepted to ACL 2026 Findings. Execution traces are available at [Gome GPT-5 Traces](https://huggingface.co/datasets/amstrongzyf/Gome-GPT5-Traces) |
| Web UI Release | We release a new frontend that can be built and served by `rdagent server_ui` for real-time interaction and trace viewing, currently excluding the `data_science` scenario. |
| NeurIPS 2025 Acceptance | We are thrilled to announce that our paper [R&D-Agent-Quant](https://arxiv.org/abs/2505.15155) has been accepted to NeurIPS 2025 | 
| [Technical Report Release](#overall-technical-report) | Overall framework description and results on MLE-bench | 
| [R&D-Agent-Quant Release](#deep-application-in-diverse-scenarios) | Apply R&D-Agent to quant trading | 
| MLE-Bench Results Released | R&D-Agent currently leads as the [top-performing machine learning engineering agent](#-the-best-machine-learning-engineering-agent) on MLE-bench |
| Support LiteLLM Backend | We now fully support **[LiteLLM](https://github.com/BerriAI/litellm)** as our default backend for integration with multiple LLM providers. |
| General Data Science Agent | [Data Science Agent](https://rdagent.readthedocs.io/en/latest/scens/data_science.html) |
| Kaggle Scenario release | We release **[Kaggle Agent](https://rdagent.readthedocs.io/en/latest/scens/data_science.html)**, try the new features!                  |
| Official WeChat group release  | We created a WeChat group, welcome to join! (🗪[QR Code](https://github.com/microsoft/RD-Agent/issues/880)) |
| Official Discord release  | We launch our first chatting channel in Discord (🗪[![Chat](https://img.shields.io/badge/chat-discord-blue)](https://discord.gg/ybQ97B6Jjy)) |
| First release | **R&D-Agent** is released on GitHub |


# 🧪 Agent² RL-Bench

<p align="center">
  <a href="https://wanyichen06.github.io/agent2-rlbench/"><b>Project Page</b></a> ·
  <a href="https://arxiv.org/abs/2604.10547"><b>Paper</b></a> ·
  <a href="rdagent/scenarios/rl/autorl_bench/README.md"><b>Code & Quick Start</b></a> ·
  <a href="https://www.microsoft.com/en-us/research/publication/agent2-rl-bench-can-llm-agents-engineer-agentic-rl-post-training/"><b>Microsoft Research</b></a>
</p>

**Agent² RL-Bench** evaluates whether LLM agents can autonomously engineer end-to-end post-training pipelines, spanning static optimization and stateful online RL.

```

---
## nanobrowser/nanobrowser  (★13703, boundary — langchain dep, v2 UNKNOWN (browser agent))
frameworks: ['langchain'] | v1: i=MULTI ii=worker iii=JUDGE | v2: i=MULTI ii=UNKNOWN iii=NO | probed=8 | tree=319
agent-ish top dirs: ['AGENTS.md']

### README (head)
```
<h1 align="center">
    <img src="https://github.com/user-attachments/assets/ec60b0c4-87ba-48f4-981a-c55ed0e8497b" height="100" width="375" alt="banner" /><br>
</h1>


<div align="center">

[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/nanobrowser)
[![Twitter](https://img.shields.io/badge/Twitter-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/nanobrowser_ai)
[![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/NN3ABHggMK)
[<img src="https://deepwiki.com/badge.svg" height="28" alt="Ask DeepWiki">](https://deepwiki.com/nanobrowser/nanobrowser)
[![Sponsor](https://img.shields.io/badge/Sponsor-ff69b4?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/alexchenzl)

</div>

## 🌐 Nanobrowser

Nanobrowser is an open-source AI web automation tool that runs in your browser. A free alternative to OpenAI Operator with flexible LLM options and multi-agent system.

⬇️ Get [Nanobrowser from Chrome Web Store](https://chromewebstore.google.com/detail/nanobrowser/imbddededgmcgfhfpcjmijokokekbkal) for free

👏 Join the community in [Discord](https://discord.gg/NN3ABHggMK) | [X](https://x.com/nanobrowser_ai)

🌟 Loving Nanobrowser? Give us a star  and help spread the word!

❤️ Support the project by [sponsoring us](https://github.com/sponsors/alexchenzl) - every contribution helps keep Nanobrowser free and open source!

<div align="center">
<img src="https://github.com/user-attachments/assets/112c4385-7b03-4b81-a352-4f348093351b" width="600" alt="Nanobrowser Demo GIF" />
<p><em>Nanobrowser's multi-agent system analyzing HuggingFace in real-time, with the Planner intelligently self-correcting when encountering obstacles and dynamically instructing the Navigator to adjust its approach—all running locally in your browser.</em></p>
</div>

## 🔥Why Nanobrowser?

Looking for a powerful AI browser agent without the $200/month price tag of OpenAI Operator? **Nanobrowser** , as a chrome extension, delivers premium web automation capabilities while keeping you in complete control:

- **100% Free** - No subscription fees or hidden costs. Just install and use your own API keys, and you only pay what you use with your own API keys.
- **Privacy-Focused** - Everything runs in your local browser. Your credentials stay with you, never shared with any cloud service.
- **Flexible LLM Options** - Connect to your preferred LLM providers with the freedom to choose different models for different agents.
- **Fully Open Source** - Complete transparency in how your browser is automated. No black boxes or hidden processes.

> **Note:** We currently support OpenAI, Anthropic, Gemini, Ollama, Groq, Cerebras, Llama and custom OpenAI-Compatible providers, more providers will be supported.


## 📊 Key Features

- **Multi-agent System**: Specialized AI agents collaborate to accomplish complex web workflows
- **Interactive Side Panel**: Intuitive chat interface with real-time status updates
- **Task Automation**: Seamlessly automate repetitive web automation tasks across websites
- **Follow-up Questions**: Ask contextual follow-up questions about completed tasks
- **Conversation History**: Easily access and manage your AI agent interaction history
- **Multiple LLM Support**: Connect your preferred LLM providers and assign different models to different agents


## 🌐 Browser Support

**Officially Supported:**
- **Chrome** - Full support with all features
- **Edge** - Full support with all features

```

---
## MemTensor/MemOS  (★11107, JUDGE positive — langchain+langgraph+openai-agents, v2 ORCH-WORKER+JUDGE)
frameworks: ['langchain', 'langgraph', 'openai-agents'] | v1: i=MULTI ii=pipeline iii=JUDGE | v2: i=MULTI ii=ORCH-WORKER iii=JUDGE | probed=6 | tree=2418
agent-ish top dirs: ['evaluation', 'AGENTS.md']

### README (head)
```
<div align="center">
  <h1 align="center">
    <a href="https://memos.openmem.net/">
      <img src="https://statics.memtensor.com.cn/logo/memos_color_m.png" alt="MemOS Logo" width="48"/>
    </a>&nbsp;
    MemOS 2.0&ensp;Stardust（星尘）
  </h1>

  <p align="center">
    <a href="https://memos-docs.openmem.net/home/overview/"><img src="https://img.shields.io/badge/Docs-Get--Start-002FA7?labelColor=gray&style=for-the-badge&logo=googledocs&logoColor=white" alt="Docs"></a>
    <a href="https://arxiv.org/abs/2507.03724"><img src="https://img.shields.io/badge/ArXiv-2507.03724-B31B1B?labelColor=gray&style=for-the-badge&logo=arxiv&logoColor=white" alt="ArXiv"></a>
    <a href="https://x.com/MemOS_dev"><img src="https://img.shields.io/badge/Follow-MemOS-000000?labelColor=gray&style=for-the-badge&logo=x&logoColor=white" alt="X"></a>
    <a href="https://discord.gg/Txbx3gebZR"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fdiscord.com%2Fapi%2Fv10%2Finvites%2FTxbx3gebZR%3Fwith_counts%3Dtrue&query=%24.approximate_presence_count&suffix=%20online&label=Discord&color=404EED&labelColor=gray&style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
    <br>
    <a href="https://github.com/IAAR-Shanghai/Awesome-AI-Memory"><img src="https://img.shields.io/badge/Resources-Awesome--AI--Memory-8A2BE2?labelColor=gray&style=for-the-badge&logo=awesomelists&logoColor=white" alt="Resources"></a>
  </p>

  <p align="center">
    <strong>Give your Agent persistent memory and the ability to grow.</strong><br/>
  </p>

  <p align="center">
    <strong>English</strong> | <a href="README_ZH.md">中文</a>
  </p>
</div>


<div align="center">
  <img width="1660" alt="MemOS agent ecosystem: OpenClaw, Hermes, and DeepSeek Harness" src="./assets/readme/memos-agent-ecosystem.png" />
</div>

> [!TIP]
> **New: Connect MemOS to DeepSeek Harness (`dsh`)**
>
> Add automatic recall, background capture, hybrid retrieval, and a local Memory Viewer to DeepSeek Harness—powered by the same MemOS core used across agent ecosystems.
>
> **[Get started →](#memos-plugin)**

---

## 👾 MemOS: Memory Operating System for LLM & AI Agents

**MemOS** is a Memory Operating System for LLMs and AI agents that unifies **store / retrieve / manage** for long-term memory, enabling **context-aware and personalized** interactions with **KB**, **multi-modal**, **tool memory**, and **enterprise-grade** optimizations built in.

### Key Features

- **Unified Memory API**: A single API to add, retrieve, edit, and delete memory—structured as a graph, inspectable and editable by design, not a black-box embedding store.
- **Multi-Modal Memory**: Natively supports text, images, tool traces, and personas, retrieved and reasoned together in one memory system.
- **Multi-Cube Knowledge Base Management**: Manage multiple knowledge bases as composable memory cubes, enabling isolation, controlled sharing, and dynamic composition across users, projects, and agents.
- **Asynchronous Ingestion via MemScheduler**: Run memory operations asynchronously with millisecond-level latency for production stability under high concurrency.
- **Memory Feedback & Correction**: Refine memory with natural-language feedback—correcting, supplementing, or replacing existing memories over time.


### News

- **2026-08-17** · 🐋 **MemOS Connects with DeepSeek Harness**
  MemOS now brings persistent memory to **DeepSeek Harness** through both local and cloud plugins. DSH can automatically recall relevant context before a task and retain new experience after a successful turn, without modifying its core.

- **2026-07-02** · 🏆 **MemOS Advances Agent and User Memory Benchmarks**
  With MemOS, **OpenClaw** improves average task completion from **36.63% to 50.87%** across five agent tasks. MemOS also achieves **88.83 on LoCoMo** and **89.20 on LongMemEval**, and leads in **OmniMemEval**, a unified evaluation of 14 commercial memory products across ten datasets.
```

---
## GetBindu/Bindu  (★9468, real-MAS — autogen+langchain+langgraph, v2 ORCH-WORKER)
frameworks: ['autogen/ag2', 'langchain', 'langgraph'] | v1: i=MULTI ii=worker iii=JUDGE | v2: i=MULTI ii=ORCH-WORKER iii=NO | probed=8 | tree=1015
agent-ish top dirs: ['.agents', 'AGENTS.md']

### README (head)
```
<p align="center">
  <img src="./assets/bindu_logo.png" alt="Bindu" width="120" />
</p>

<h1 align="center">Bindu</h1>

<p align="center">
    <a href="https://www.python.org/downloads/"><img alt="Python Version" src="https://img.shields.io/badge/python-3.12+-blue.svg"></a>
    <a href="https://pypi.org/project/bindu/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/bindu.svg"></a>
    <a href="https://coveralls.io/github/Saptha-me/Bindu?branch=v0.3.18"><img alt="Coverage" src="https://coveralls.io/repos/github/Saptha-me/Bindu/badge.svg?branch=v0.3.18"></a>
    <a href="https://github.com/getbindu/Bindu/actions/workflows/release.yml"><img alt="Tests" src="https://github.com/getbindu/Bindu/actions/workflows/release.yml/badge.svg"></a>
    <a href="https://discord.gg/3w5zuYUuwt"><img alt="Discord" src="https://img.shields.io/badge/Discord-7289DA?logo=discord&logoColor=white"></a>
    <a href="https://github.com/getbindu/Bindu/graphs/contributors"><img alt="Contributors" src="https://img.shields.io/github/contributors/getbindu/Bindu"></a>
    <a href="https://hits.sh/github.com/Saptha-me/Bindu.svg"><img alt="Hits" src="https://hits.sh/github.com/Saptha-me/Bindu.svg"></a>
    <a href="https://www.star-history.com/getbindu/bindu">
        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/badge?repo=GetBindu/Bindu&theme=dark" />
            <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/badge?repo=GetBindu/Bindu" />
            <img alt="Star History Rank" src="https://api.star-history.com/badge?repo=GetBindu/Bindu" />
        </picture>
    </a>
</p>

<h4 align="center">
    <p>
        <b>English</b> |
        <a href="i18n/README.de.md">Deutsch</a> |
        <a href="i18n/README.es.md">Español</a> |
        <a href="i18n/README.fr.md">Français</a> |
        <a href="i18n/README.hi.md">हिंदी</a> |
        <a href="i18n/README.bn.md">বাংলা</a> |
        <a href="i18n/README.zh.md">中文</a> |
        <a href="i18n/README.nl.md">Nederlands</a> |
        <a href="i18n/README.id.md">Bahasa Indonesia</a> |
        <a href="i18n/README.ta.md">தமிழ்</a>
    </p>
</h4>

<h3 align="center">The identity, communication, and payments layer for AI agents.</h3>

<br/>

<p align="center">
  <em>A Gmail-shaped inbox for the agent internet. Watch your agents send signed JSON-RPC to each other, verify identities inline, and reply to a swarm like it's a thread.</em>
</p>

<p align="center">
  <a href="inbox/README.md"><img src="./assets/inbox.png" alt="Bindu inbox — agents talking to agents, signatures verified inline" width="880" /></a>
</p>

<p align="center">
  <a href="inbox/README.md"><strong>→ Open the inbox walkthrough</strong></a>
</p>

<br/>

Here's the situation. You built an agent. It works. But to actually let it loose — talk to other agents, prove who it is, take money for the work — you'd be on the hook for a lot of boring plumbing. A DID library to integrate. An OAuth flow to set up. Payment middleware. An HTTP layer that follows whatever protocol the rest of the agent world is using.

Bindu is all of that plumbing, behind one function call. You wrap your handler with `bindufy()`, and a few seconds later your agent is online with its own cryptographic identity, speaking [A2A](https://github.com/a2aproject/A2A) (the protocol other agents already use), and ready to demand USDC on any EVM chain before it does any work ([x402](https://github.com/coinbase/x402)). Your handler stays as small as `(messages) -> response`. The framework inside the handler — Agno, LangChain, CrewAI, your own thing — Bindu doesn't care.

```

---
## lastmile-ai/mcp-agent  (★8524, real-MAS — crewai+langchain, v2 TEAM)
frameworks: ['crewai', 'langchain'] | v1: i=MULTI ii=worker iii=JUDGE | v2: i=MULTI ii=TEAM iii=NO | probed=7 | tree=1451
agent-ish top dirs: []

### README (head)
```
<p align="center">
  <a href="https://docs.mcp-agent.com"><img src="https://github.com/user-attachments/assets/c8d059e5-bd56-4ea2-a72d-807fb4897bde" alt="Logo" width="300" /></a>
</p>

<p align="center">
  <em>Build effective agents with Model Context Protocol using simple, composable patterns.</em>

<p align="center">
  <a href="https://github.com/lastmile-ai/mcp-agent/tree/main/examples" target="_blank"><strong>Examples</strong></a>
  |
  <a href="https://docs.mcp-agent.com/mcp-agent-sdk/effective-patterns/overview" target="_blank"><strong>Building Effective Agents</strong></a>
  |
  <a href="https://modelcontextprotocol.io/introduction" target="_blank"><strong>MCP</strong></a>
</p>

<p align="center">
<a href="https://docs.mcp-agent.com"><img src="https://img.shields.io/badge/docs-8F?style=flat&link=https%3A%2F%2Fdocs.mcp-agent.com%2F" /><a/>
<a href="https://pypi.org/project/mcp-agent/"><img src="https://img.shields.io/pypi/v/mcp-agent?color=%2334D058&label=pypi" /></a>
<img alt="Pepy Total Downloads" src="https://img.shields.io/pepy/dt/mcp-agent?label=pypi%20%7C%20downloads"/>
<a href="https://github.com/lastmile-ai/mcp-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg"/></a>
<a href="https://lmai.link/discord/mcp-agent"><img src="https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white" alt="discord"/></a>
</p>

<p align="center">
<a href="https://trendshift.io/repositories/13216" target="_blank"><img src="https://trendshift.io/api/badge/repositories/13216" alt="lastmile-ai%2Fmcp-agent | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

## Overview

**`mcp-agent`** is a simple, composable framework to build effective agents using [Model Context Protocol](https://modelcontextprotocol.io/introduction).

> [!Note]
> mcp-agent's vision is that _MCP is all you need to build agents, and that simple patterns are more robust than complex architectures for shipping high-quality agents_.

`mcp-agent` gives you the following:

1. **Full MCP support**: It _fully_ implements MCP, and handles the pesky business of managing the lifecycle of MCP server connections so you don't have to.
2. **Effective agent patterns**: It implements every pattern described in Anthropic's [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) in a _composable_ way, allowing you to chain these patterns together.
3. **Durable agents**: It works for simple agents and scales to sophisticated workflows built on [Temporal](https://temporal.io/) so you can pause, resume, and recover without any API changes to your agent.

<u>Altogether, this is the simplest and easiest way to build robust agent applications</u>.

We welcome all kinds of [contributions](/CONTRIBUTING.md), feedback and your help in improving this project.

<a id="minimal-example"></a>
**Minimal example**

```python
import asyncio

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

app = MCPApp(name="hello_world")

async def main():
    async with app.run():
        agent = Agent(
            name="finder",
```

---
## openJiuwen-ai/jiuwenswarm  (★6308, swarm TEAM — google-adk dep, reverse-gap from R103)
frameworks: ['google-adk'] | v1: i=MULTI ii=team iii=JUDGE | v2: i=MULTI ii=TEAM iii=NO | probed=7 | tree=4101
agent-ish top dirs: ['jiuwenswarm']

### README (head)
```
<p align="center">
  <img src="docs/assets/images/logo.svg" alt="JiuwenSwarm Logo" width="160" />
</p>

<h1 align="center">JiuwenSwarm</h1>

<p align="center">
  <strong>Understands Your Intent, Evolves Autonomously — Swarm Collaboration for Complex Tasks</strong>
</p>
<p align="center">
  <a href="README.md">English</a>
  ·
  <a href="README_CN.md">Chinese</a>
  ·
  <a href="docs/README_EN.md">Docs (EN)</a>
  ·
  <a href="docs/README.md">Docs</a>
  ·
  <a href="https://openjiuwen.com/en/">Website</a>
  ·
  <a href="https://swarmskills.openjiuwen.com/">Swarm Skills Hub</a>
  · 
  <a href="https://gitcode.com/openJiuwen/jiuwenswarm">GitCode</a>
</p>

<p align="center">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-Apache--2.0-green.svg" alt="License" />
  </a>
  <a href="https://github.com/openJiuwen-ai/jiuwenswarm/releases">
    <img src="https://img.shields.io/pypi/v/jiuwenswarm.svg" alt="Release" />
  </a>
  <img src="https://img.shields.io/badge/python-%E2%89%A53.11-blue.svg" alt="Python Version" />
  <img src="https://img.shields.io/badge/os-Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20HarmonyOS-lightgrey.svg" alt="OS Support" />
</p>

[JiuwenSwarm_Introduction.mp4](docs/assets/videos/JiuwenSwarm_Introduction.mp4)

**JiuwenSwarm** is an Agent system that makes multi-agent collaboration truly work. Designed for developers and teams who need to automate complex tasks, it helps users drive multi-agent collaboration, Skill self-evolution, and tool invocation through natural language — delivering end-to-end from intent to result. It runs on a single machine or across a cluster, and you can reach it from a browser, a terminal, or the chat apps you already use.

### Why JiuwenSwarm

| Capability                      | Value                                                                                                                                                     |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Multi-Agent Collaboration       | The Leader decomposes a complex task and assembles teams, multi agents specialize and negotiate dynamically.                                              |
| Distributed Agent Swarm         | Leader and Teammates deploy across processes and machines, coordinating at scale.                                                                         |
| Swarmflow                       | Deterministic multi-stage workflows via Python scripts: the Leader hands off between stage agents; supports **HITL** (`human` / `human_session`), **team token budget**, and TUI **`/swarmflows`** run-tree monitoring. |
| Skill Self-Evolution            | Automatically detects error signals and user dissatisfaction, then optimizes Skill definitions                                                            |
| Skill Hub Sharing               | Capability assets are built once and reused everywhere, search, install, remix, and publish Skills through the Swarm Skills Hub                           |
| Auto Harness                    | Evaluation drive end-to-end optimization of the Harness itself, which learns and improves in practice with no model-weight training                       |
| AI Infrastructure Compatibility | Compatible with Huawei Cloud MaaS and other mainstream platforms, OpenAI-compatible APIs, and local models                                                |
| Tool Permissions & Security     | Every step is under your control, tools require approval before execution, file access goes through a whitelist, and sensitive operations are intercepted |

## Install

### Desktop

One-click install, no environment setup — the quickest way to try JiuwenSwarm.

| Platform  | Download                                                          | Notes                                         |
```

---
## business-science/ai-data-science-team  (★5394, real-MAS — langchain+langgraph, v2 ORCH-WORKER)
frameworks: ['langchain', 'langgraph'] | v1: i=SINGLE ii=team iii=JUDGE | v2: i=MULTI ii=ORCH-WORKER iii=NO | probed=8 | tree=151
agent-ish top dirs: []

### README (head)
```
<div align="center">
  <a href="https://github.com/business-science/ai-data-science-team">
    <picture>
      <img src="./img/ai_data_science_logo.png" alt="AI Data Science Team" width="360">
    </picture>
  </a>
</div>
<div align="center">
  <em>AI Data Science Team + AI Pipeline Studio</em>
</div>
<div align="center">
  <a href="https://pypi.python.org/pypi/ai-data-science-team"><img src="https://img.shields.io/pypi/v/ai-data-science-team.svg?style=for-the-badge" alt="PyPI"></a>
  <a href="https://github.com/business-science/ai-data-science-team"><img src="https://img.shields.io/pypi/pyversions/ai-data-science-team.svg?style=for-the-badge" alt="versions"></a>
  <a href="https://github.com/business-science/ai-data-science-team/blob/main/LICENSE"><img src="https://img.shields.io/github/license/business-science/ai-data-science-team.svg?style=for-the-badge" alt="license"></a>
  <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/business-science/ai-data-science-team?style=for-the-badge">
</div>

# AI Data Science Team

AI Data Science Team is a Python library of specialized agents for common data science workflows, plus a flagship app: **AI Pipeline Studio**. The Studio turns your work into a visual, reproducible pipeline, while the AI team handles data loading, cleaning, visualization, and modeling.

**Status:** Beta. Breaking changes may occur until 0.1.0.

[**Please ⭐ us on GitHub (it takes 2 seconds and means a lot).**](https://github.com/business-science/ai-data-science-team)

## AI Pipeline Studio (Flagship App)

AI Pipeline Studio is the main example of the AI Data Science Team in action.

![AI Pipeline Studio](/img/apps/ai_pipeline_studio_app.jpg)

Highlights:
- Pipeline-first workspace: Visual Editor, Table, Chart, EDA, Code, Model, Predictions, MLflow
- Manual + AI steps with lineage and reproducible scripts
- Multi-dataset handling and merge workflows
- Project saves: metadata-only or full-data
- Storage footprint controls and rehydrate workflows

Run it:
```bash
streamlit run apps/ai-pipeline-studio-app/app.py
```

Full app docs: `apps/ai-pipeline-studio-app/README.md`

## Quickstart

### Requirements
- Python 3.10+
- OpenAI API key (or Ollama for local models)

### Install the app and library
Clone the repo and install in editable mode:
```bash
pip install -e .
```

### Run the AI Pipeline Studio app
```bash
streamlit run apps/ai-pipeline-studio-app/app.py
```

---
## Mirix-AI/MIRIX  (★3437, JUDGE positive — langchain+langgraph+openai-agents, v2 ORCH-WORKER+JUDGE)
frameworks: ['langchain', 'langgraph', 'openai-agents'] | v1: i=MULTI ii=worker iii=JUDGE | v2: i=MULTI ii=ORCH-WORKER iii=JUDGE | probed=8 | tree=559
agent-ish top dirs: []

### README (head)
```
![Mirix Logo](https://github.com/RenKoya1/MIRIX/raw/main/assets/logo.png)

## MIRIX - Multi-Agent Personal Assistant with an Advanced Memory System

Your personal AI that builds memory through screen observation and natural conversation

| 🌐 [Website](https://mirix.io) | 📚 [Documentation](https://docs.mirix.io) | 📄 [Paper](https://arxiv.org/abs/2507.07957) | 💬 [Discord](https://discord.gg/S6CeHNrJ)
<!-- | [Twitter/X](https://twitter.com/mirix_ai) | [Discord](https://discord.gg/S6CeHNrJ) | -->

---

### Key Features 🔥

- **Multi-Agent Memory System:** Six specialized memory components (Core, Episodic, Semantic, Procedural, Resource, Knowledge Vault) managed by dedicated agents
- **Screen Activity Tracking:** Continuous visual data capture and intelligent consolidation into structured memories
- **Privacy-First Design:** All long-term data stored locally with user-controlled privacy settings
- **Advanced Search:** PostgreSQL-native BM25 full-text search with vector similarity support
- **Multi-Modal Input:** Text, images, voice, and screen captures processed seamlessly

### Quick Start
**Step 1: Backend & Dashboard (Docker):**
```
docker compose up -d --pull always
```
- Dashboard: http://localhost:5173
- API: http://localhost:8531

**Step 2: Create an API key in the dashboard (http://localhost:5173) and set as the environmental variable `MIRIX_API_KEY`.**

**Step 3: Client (Python, `mirix-client`, https://pypi.org/project/mirix-client/):**
```
pip install mirix-client
```

Now you are ready to go! See the example below:
```python
from mirix import MirixClient

client = MirixClient(
    api_key="your-api-key",
    base_url="http://localhost:8531",
)

client.initialize_meta_agent(
    config={
        "llm_config": {
            "model": "gemini-2.0-flash",
            "model_endpoint_type": "google_ai",
            "api_key": "your-api-key-here",
            "model_endpoint": "https://generativelanguage.googleapis.com",
            "context_window": 1_000_000,
        },
        "embedding_config": {
            "embedding_model": "text-embedding-004",
            "embedding_endpoint_type": "google_ai",
            "api_key": "your-api-key-here",
            "embedding_endpoint": "https://generativelanguage.googleapis.com",
            "embedding_dim": 768,
        },
        "meta_agent_config": {
```

---
## agentstack-ai/AgentStack  (★2189, gate verify — scaffolding CLI (semi-seen: held-out catch))
frameworks: ['crewai', 'langchain', 'langgraph', 'openai-swarm'] | v1: i=MULTI ii=worker iii=UNKNOWN | v2: i=SINGLE ii=SINGLE iii=NO | probed=8 | tree=534
agent-ish top dirs: ['agentstack', 'agentstack_banner.png']

### README (head)
```
# AgentStack

 [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) ![python-testing](https://github.com/agentops-ai/agentstack/actions/workflows/python-testing.yml/badge.svg) ![mypy](https://github.com/agentops-ai/agentstack/actions/workflows/mypy.yml/badge.svg) [![codecov.io](https://codecov.io/github/agentops-ai/agentstack/coverage.svg?branch=master)](https://codecov.io/github/agentops-ai/agentstack>?branch=master)


AgentStack scaffolds your _agent stack_ - The tech stack that collectively is your agent

<p align='center'>
<img src='./docs/images/the_agent_stack.png' width='600' alt='AgentStack items'>
</p>

### Install AgentStack

```sh
curl --proto '=https' --tlsv1.2 -LsSf https://install.agentstack.sh | sh
```

or python [other install methods](https://docs.agentstack.sh/installation)

### Start your agent!

Create AI agent projects from the command line.

- [Quickstart Guide](https://docs.agentstack.sh/quickstart) – How to create a new agent project.
- [Video Tutorial](https://www.loom.com/share/68d796b13cd94647bd1d7fae12b2358e?sid=7fdf595b-de84-4d51-9a81-ef1e9c8ac71c) – Follow along and build a web scrape agent with AgentStack

AgentStack works on macOS, Windows, and Linux.<br>
If something doesn't work, please [file an issue](https://github.com/agentops-ai/agentstack/issues/new).<br>
If you have questions or need help, please ask in our [Discord community](https://discord.gg/JdWkh9tgTQ).

> 🛠️🏃🏼‍♀️ The quickest way to build your powerful agent project

AgentStack serves as a great tool for starting your agent project and offers many CLI utilities for easy code-gen throughout the development process.

AgentStack is _not_ a low-code alternative to development. Developers will still need an understanding of how to build with their selected agent framework.

### Currently Supported Providers
- **LLMs**: Most all notable LLMs and providers are supported via LiteLLM or LangChain
- **Framework**: Currently supported frameworks include CrewAI, LangGraph, OpenAI Swarms and LlamaStack
  - Roadmap: Pydantic AI, Eliza, AG2 and Autogen
- **Tools**: Maintaining the largest repository of framework-agnostic tools! All tools listed [here](https://docs.agentstack.sh/tools/community)
- **Observability**: AgentOps baked in by default with first-tier support

### Get Started Immediately

You **don't** need to install or configure tools like LangChain or LlamaIndex.<br>
They are preconfigured and hidden so that you can focus on the code.

Create a project, and you're good to go.

## Creating an Agent Project

**You'll need to have Python 3.10+ on your local development machine**. We recommend using the latest version. You can use [pyenv](https://github.com/pyenv/pyenv) to switch Python versions between different projects.

To create a new agent project, run:

```sh
uv pip install agentstack # or other install method
agentstack init <project_name>
```
```
