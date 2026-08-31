# Ground-truth annotation bundles — issue #57 (R106, axis i only)

Remaining Tier B repos: 56 (of 86). Axis i = SINGLE|MULTI|UNKNOWN.
Evidence: README head 25 lines (self-description) + framework deps + agent-ish dirs.
v2_i column is the classifier snapshot for comparison, NOT for annotation.

---
## mvanhorn/last30days-skill  (★60743, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['.agents', 'AGENTS.md'] | tree=518

### README (head)
```
# /last30days

English | [Français](README.fr.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Português (Brasil)](README.pt-BR.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

<p align="center">
  <img src="media/pr-assets/last30days-ad.gif" width="720" alt="last30days - an AI agent-led search engine that searches people, not editors" />
</p>

<p align="center">
  <a href="https://github.com/mvanhorn/last30days-skill">
    <img src="https://img.shields.io/badge/%231-Repository%20Of%20The%20Day-6f42c1?style=for-the-badge&logo=github&label=GITHUB%20TRENDING" alt="GitHub Trending #1 Repository Of The Day" />
  </a>
  <br/>
  <a href="https://trendshift.io/repositories/21997" target="_blank">
    <img src="https://trendshift.io/api/badge/repositories/21997" alt="mvanhorn/last30days-skill | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/>
  </a>
</p>

**An AI agent-led search engine scored by upvotes, likes, and real money - not editors.**

This README tracks the current v3 pipeline. The runtime skill spec lives in [skills/last30days/SKILL.md](skills/last30days/SKILL.md), which is the source of truth for the latest command and setup behavior.

**Claude Code (recommended — auto-updates via marketplace):**
```
/plugin marketplace add mvanhorn/last30days-skill
/plugin install last30days
```

**Codex, Cursor, Copilot, Gemini CLI, or any of 50+ [Agent Skills](https://agentskills.io) hosts:**
```
npx skills add mvanhorn/last30days-skill -g
```
(`-g` installs globally for your user, available across all projects. Drop it to scope per-project.)

More install options (claude.ai web, OpenClaw, manual) in the [Install](#install) section below.

Zero config. Reddit, HN, Polymarket, and GitHub work immediately. Run it once and the setup wizard unlocks X, YouTube, TikTok, arXiv, Techmeme, and more in 30 seconds.

---

Reddit upvotes. X likes. YouTube transcripts. TikTok engagement. Polymarket odds backed by real money and insider information. That's millions of people voting with their attention and their wallets every day. /last30days searches all of it in parallel, scores it by what real people actually engage with, and an AI agent judge synthesizes it into one brief.

Google aggregates editors. /last30days searches people.

You can't get this search anywhere else because no single AI has access to all of it. Google search doesn't touch Reddit comments or X posts. ChatGPT has a deal with Reddit but can't search X or TikTok. Gemini has YouTube but not Reddit. Claude has none of them natively. Each platform is a walled garden with its own API, its own tokens, its own auth. But you can bring your own keys and browser sessions, and suddenly an AI agent can search all of them at once, score them against each other, and tell you what actually matters.
```

---
## calesthio/OpenMontage  (★54840, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['.agents', 'AGENTS.md', 'AGENT_GUIDE.md'] | tree=2571

### README (head)
```
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/monty-dark.svg">
    <img src="assets/monty-light.svg" alt="Monty the Clapper — the official mascot of OpenMontage" width="200">
  </picture>
</p>

<p align="center"><sub><em>Monty the Clapper — the official mascot of OpenMontage</em></sub></p>

<h1 align="center">OpenMontage</h1>

<p align="center"><strong>The first open-source, agentic video production system.</strong></p>

<p align="center">
  <a href="https://openmontage.video"><img src="https://img.shields.io/badge/Website-openmontage.video-d14a28?style=for-the-badge" alt="openmontage.video"></a>
</p>

<p align="center">
  <a href="#start-from-a-video-you-already-love">Paste A Video</a> &nbsp;·&nbsp;
  <a href="#quick-start">Quick Start</a> &nbsp;·&nbsp;
  <a href="#try-these-prompts">Try These Prompts</a> &nbsp;·&nbsp;
  <a href="#pipelines">Pipelines</a> &nbsp;·&nbsp;
  <a href="#how-it-works">How It Works</a> &nbsp;·&nbsp;
  <a href="#sponsors">Sponsors</a> &nbsp;·&nbsp;
  <a href="docs/PROVIDERS.md">Providers</a> &nbsp;·&nbsp;
  <a href="docs/PR_REVIEW_GUIDE.md">Review Guide</a> &nbsp;·&nbsp;
  <a href="AGENT_GUIDE.md">Agent Guide</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPLv3-blue.svg" alt="License"></a>
</p>

<p align="center">
  <a href="https://github.com/trending">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset=".github/assets/repo-of-the-day-dark.svg">
      <img alt="🏆 #1 Repository of the Day on GitHub Trending" src=".github/assets/repo-of-the-day-light.svg" height="60">
    </picture>
  </a>
</p>

<p align="center"><strong>Follow The Build</strong></p>

<p align="center">
```

---
## zhayujie/CowAgent  (★46735, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['agent'] | tree=1079

### README (head)
```
<p align="center"><img src="https://github.com/user-attachments/assets/eca9a9ec-8534-4615-9e0f-96c5ac1d10a3" alt="CowAgent" width="420" /></p>

<p align="center">
  <a href="https://github.com/zhayujie/CowAgent/releases/latest"><img src="https://img.shields.io/github/v/release/zhayujie/CowAgent?cacheSeconds=3600" alt="Latest release"></a>
  <a href="https://github.com/zhayujie/CowAgent/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://github.com/zhayujie/CowAgent"><img src="https://img.shields.io/github/stars/zhayujie/CowAgent?style=flat-square&cacheSeconds=3600" alt="Stars"></a>
  <a href="https://docs.cowagent.ai/"><img src="https://img.shields.io/badge/Docs-cowagent.ai-blue?style=flat&logo=readthedocs&logoColor=white" alt="Docs"></a>
  <a href="https://cdn.link-ai.tech/code/cow/cowagent-wechat-group.png"><img src="https://img.shields.io/badge/WeChat-Group-07C160?style=flat&logo=wechat&logoColor=white" alt="WeChat Group"></a>
  <a href="https://discord.gg/9U8eA8v9TR"><img src="https://img.shields.io/badge/Discord-Join-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord"></a>
</p>

<p align="center">
  <a href="https://trendshift.io/repositories/25763" target="_blank"><img src="https://trendshift.io/api/badge/repositories/25763" alt="zhayujie%2FCowAgent | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

<p align="center">
  [English] | [<a href="docs/zh/README.md">中文</a>] | [<a href="docs/zh/README-Hant.md">繁體中文</a>] | [<a href="docs/ja/README.md">日本語</a>]
</p>

**CowAgent** is an open-source super AI assistant that proactively plans tasks, controls your computer and external services, creates and runs Skills, builds a personal knowledge base and long-term memory, and grows alongside you through self-evolution — a reference implementation of Agent Harness engineering.

CowAgent is lightweight, easy to deploy, and built to extend. Plug in any major LLM provider and run it 24/7 on a personal computer or server, across the web and all major IM platforms.

<p align="center">
  <a href="https://cowagent.ai/">🌐 Website</a> &nbsp;·&nbsp;
  <a href="https://docs.cowagent.ai/intro/index">📖 Docs</a> &nbsp;·&nbsp;
  <a href="https://docs.cowagent.ai/guide/quick-start">🚀 Quick Start</a> &nbsp;·&nbsp;
  <a href="https://skills.cowagent.ai/">🧩 Skill Hub</a> &nbsp;·&nbsp;
  <a href="https://cowagent.ai/download/">💻 Download</a> &nbsp;·&nbsp;
  <a href="https://link-ai.tech/cowagent/create">☁️ Try Online</a>
</p>

<br/>

## 🎬 Demo

<p align="center">
  <video src="https://github.com/user-attachments/assets/8625a19f-615c-4343-8be8-3707ce4d4d4e" controls muted playsinline width="720">
    Your browser can't play this video.
    <a href="https://cowagent.ai/">Watch the demo on our website →</a>
  </video>
</p>

<br/>

```

---
## coreyhaines31/marketingskills  (★46235, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=622

### README (head)
```
# Marketing Skills for AI Agents

A collection of AI agent skills focused on marketing tasks. Built for technical marketers and founders who want AI coding agents to help with conversion optimization, copywriting, SEO, analytics, and growth engineering. Works with Claude Code, OpenAI Codex, Cursor, Windsurf, and any agent that supports the [Agent Skills spec](https://agentskills.io).

Built by [Corey Haines](https://corey.co?ref=marketingskills). Need hands-on help? Check out [Conversion Factory](https://conversionfactory.co?ref=marketingskills) — Corey's agency for conversion optimization, landing pages, and growth strategy. Want to learn more about marketing? Subscribe to [Swipe Files](https://swipefiles.com?ref=marketingskills). Want to get dangerously good at using AI for marketing? Check out [AI Marketing Training](https://conversionfactory.co/offers/ai-marketing-training?ref=marketingskills). Want an autonomous AI agent that uses these skills to be your CMO? Try [Magister](https://magistermarketing.com?ref=marketingskills).

New to the terminal and coding agents? Check out the companion guide [Coding for Marketers](https://codingformarketers.com?ref=marketingskills).

**Contributions welcome!** Found a way to improve a skill or have a new one to add? [Open a PR](#contributing).

Run into a problem or have a question? [Open an issue](https://github.com/coreyhaines31/marketingskills/issues) — we're happy to help.

## Partners

The library is free and MIT-licensed. [Verified Partners](tools/REGISTRY.md#verified-partners) fund the work — vetted, disclosed tool integrations, listed alongside the neutral options and never influencing what the core skills recommend. The full rules and boundaries are in [tools/PARTNERS.md](tools/PARTNERS.md). [Become a partner →](https://marketing-skills.com/sponsorship)

<!-- PARTNERS:START -->
_No active partners yet. [Become a partner →](https://marketing-skills.com/sponsorship)_
<!-- PARTNERS:END -->

<!-- The Partners block above is generated from partners.json — run `node scripts/sync-partners.mjs` after editing it. -->

## What are Skills?

Skills are markdown files that give AI agents specialized knowledge and workflows for specific tasks. When you add these to your project, your agent can recognize when you're working on a marketing task and apply the right frameworks and best practices.

## How Skills Work Together

Skills reference each other and build on shared context. The `product-marketing` skill is the foundation — every other skill checks it first to understand your product, audience, and positioning before doing anything.

```
                            ┌──────────────────────────────────────┐
                            │          product-marketing           │
                            │    (read by all other skills first)  │
                            └──────────────────┬───────────────────┘
                                               │
    ┌──────────────┬─────────────┬─────────────┼─────────────┬──────────────┬──────────────┐
    ▼              ▼             ▼             ▼             ▼              ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌─────────────┐ ┌───────────┐
│  SEO &   │ │   CRO    │ │Content & │ │  Paid &    │ │ Growth & │ │  Sales &    │ │ Strategy  │
│ Content  │ │          │ │   Copy   │ │Measurement │ │Retention │ │    GTM      │ │           │
├──────────┤ ├──────────┤ ├──────────┤ ├────────────┤ ├──────────┤ ├─────────────┤ ├───────────┤
│seo-audit │ │cro       │ │copywritng│ │ads         │ │referrals │ │revops       │ │mktg-ideas │
│ai-seo    │ │signup    │ │copy-edit │ │ad-creative │ │free-tools│ │sales-enable │ │mktg-psych │
│site-arch │ │onboarding│ │cold-email│ │ab-testing  │ │churn-    │ │launch       │ │customer-  │
```

---
## Yeachan-Heo/oh-my-claudecode  (★38913, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['agents', 'AGENTS.md'] | tree=7299

### README (head)
```
English | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Tiếng Việt](README.vi.md) | [Português](README.pt.md)

# oh-my-claudecode

[![npm version](https://img.shields.io/npm/v/oh-my-claude-sisyphus?color=cb3837)](https://www.npmjs.com/package/oh-my-claude-sisyphus)
[![npm downloads](https://img.shields.io/npm/dm/oh-my-claude-sisyphus?color=blue)](https://www.npmjs.com/package/oh-my-claude-sisyphus)
[![GitHub stars](https://img.shields.io/github/stars/Yeachan-Heo/oh-my-claudecode?style=flat&color=yellow)](https://github.com/Yeachan-Heo/oh-my-claudecode/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Sponsor](https://img.shields.io/badge/Sponsor-❤️-red?style=flat&logo=github)](https://github.com/sponsors/Yeachan-Heo)
[![Discord](https://img.shields.io/discord/1452487457085063218?color=5865F2&logo=discord&logoColor=white&label=Discord)](https://discord.gg/wSyUQYfhAw)

> **For Codex users:** Check out [oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex) — the same orchestration experience for OpenAI Codex CLI.

> **Liked OmC but found it a bit overkill? Try [gajae-code](https://github.com/Yeachan-Heo/gajae-code).**
> Keeps Claude OAuth as-is while being faster, cheaper, simpler, and more powerful — with an SDK-based integration path built for OpenClaw, Hermes, Grokbot, and similar agent runtimes.

**Multi-agent orchestration for Claude Code. Zero learning curve.**

_Don't learn Claude Code. Just use OMC._

[Get Started](#quick-start) • [Documentation](https://yeachan-heo.github.io/oh-my-claudecode-website) • [CLI Reference](https://yeachan-heo.github.io/oh-my-claudecode-website/docs/#cli-reference) • [Workflows](https://yeachan-heo.github.io/oh-my-claudecode-website/docs/#workflows) • [Migration Guide](docs/MIGRATION.md) • [Discord](https://discord.gg/wSyUQYfhAw)

---

## Core Maintainers

| Role           | Name        | GitHub                                         |
| -------------- | ----------- | ---------------------------------------------- |
| Creator & Lead | Yeachan Heo | [@Yeachan-Heo](https://github.com/Yeachan-Heo) |

## Ambassadors

| Name       | GitHub                                           |
| ---------- | ------------------------------------------------ |
| Sigrid Jin | [@sigridjineth](https://github.com/sigridjineth) |

## Document Specialists

| Name    | GitHub                                 |
| ------- | -------------------------------------- |
| devswha | [@devswha](https://github.com/devswha) |

## Top Collaborators

| Name           | GitHub                                         | Commits |
```

---
## TencentCloud/TencentDB-Agent-Memory  (★25364, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['agents'] | tree=1228

### README (head)
```

<div align="center">

<img src="./assets/images/logo.png" alt="TencentDB Agent Memory" width="880" />

### Agents remember. Humans innovate.

<a href="https://trendshift.io/repositories/29310?utm_source=repository-badge&amp;utm_medium=badge&amp;utm_campaign=badge-repository-29310" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/repositories/29310" alt="TencentCloud%2FTencentDB-Agent-Memory | Trendshift" width="250" height="55"/></a>

[![npm](https://img.shields.io/npm/v/@tencentdb-agent-memory/memory-tencentdb?color=blue)](https://www.npmjs.com/package/@tencentdb-agent-memory/memory-tencentdb)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Node](https://img.shields.io/badge/node-%3E=22.16-brightgreen)](https://nodejs.org/)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-%3E=2026.3.13-orange)](https://github.com/openclaw/openclaw)
[![Hermes](https://img.shields.io/badge/Hermes-Gateway-7B61FF)](https://hermes-agent.nousresearch.com/docs/)
[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/dJQM6mKMF)

[Installation](#installation) · [Supported Agents](#all-agents-share-the-same-memory-server) · [What is it?](#what-is-tencentdb-agent-memory) · [Team Play](#one-play-style-build-a-growing-agent-team-for-a-one-person-company) · [Technical Implementation](#technical-implementation) · [Benchmark](#benchmark) · [Roadmap](#roadmap)

[**English**](./README.md) · [简体中文](./README_CN.md)

</div>

---

> **Latest:** Team Memory Beta is evolving quickly — install it and start exploring in minutes.

<td>
   <video src="https://github.com/user-attachments/assets/efb1a808-1f86-4cfe-802c-f7453f7ca938" width="100%" controls autoplay loop muted playsinline></video>
</td>

# Installation

Start all three services in one go (`memory-core` + `memory-hub` + `proxy`):

```bash
git clone https://github.com/Tencent/TencentDB-Agent-Memory.git
cd TencentDB-Agent-Memory/deploy/global-images
cp .env.example .env
$EDITOR .env       # Fill in two sets of LLM parameters (memory group + proxy group)
./start-all.sh     # Launch everything with one command; when finished, it prints a one-liner you can paste directly into Claude
```

Open the panel: [http://localhost:8125](http://localhost:8125).

Complete installation documentation (standalone Memory Hub deployment, Proxy + Claude Code / CodeBuddy usage, stop and cleanup, port reference, etc.) is available in [**INSTALL.md**](./INSTALL.md) (中文: [INSTALL_CN.md](./INSTALL_CN.md)).
```

---
## mksglu/context-mode  (★20270, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['.agents'] | tree=714

### README (head)
```
# Context Mode

**The other half of the context problem.**

[![users](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Fmksglu%2Fcontext-mode%40main%2Fstats.json&query=%24.message&label=users&color=brightgreen)](https://www.npmjs.com/package/context-mode) [![npm](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Fmksglu%2Fcontext-mode%40main%2Fstats.json&query=%24.npm&label=npm&color=blue)](https://www.npmjs.com/package/context-mode) [![marketplace](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Fmksglu%2Fcontext-mode%40main%2Fstats.json&query=%24.marketplace&label=marketplace&color=blue)](https://github.com/mksglu/context-mode) [![GitHub stars](https://img.shields.io/github/stars/mksglu/context-mode?style=flat&color=yellow)](https://github.com/mksglu/context-mode/stargazers) [![GitHub forks](https://img.shields.io/github/forks/mksglu/context-mode?style=flat&color=blue)](https://github.com/mksglu/context-mode/network/members) [![Last commit](https://img.shields.io/github/last-commit/mksglu/context-mode?color=green)](https://github.com/mksglu/context-mode/commits) [![License: ELv2](https://img.shields.io/badge/License-ELv2-blue.svg)](LICENSE)
[![Discord](https://img.shields.io/discord/1478479412700909750?label=Discord&logo=discord&color=5865f2)](https://discord.gg/DCN9jUgN5v)
[![Hacker News #1](https://img.shields.io/badge/Hacker%20News-%231%20%E2%80%A2%20570%2B%20points-ff6600?logo=ycombinator&logoColor=white)](https://news.ycombinator.com/item?id=47193064)

<p align="center">
<sub>Used across teams at</sub>
<br><br>
<a href="#"><img src="https://img.shields.io/badge/Microsoft-141414?style=flat" alt="Microsoft" /></a>
<a href="#"><img src="https://img.shields.io/badge/Google-141414?style=flat&logo=google&logoColor=white" alt="Google" /></a>
<a href="#"><img src="https://img.shields.io/badge/Meta-141414?style=flat&logo=meta&logoColor=white" alt="Meta" /></a>
<a href="#"><img src="https://img.shields.io/badge/Amazon-141414?style=flat" alt="Amazon" /></a>
<a href="#"><img src="https://img.shields.io/badge/IBM-141414?style=flat" alt="IBM" /></a>
<a href="#"><img src="https://img.shields.io/badge/NVIDIA-141414?style=flat&logo=nvidia&logoColor=white" alt="NVIDIA" /></a>
<a href="#"><img src="https://img.shields.io/badge/ByteDance-141414?style=flat&logo=bytedance&logoColor=white" alt="ByteDance" /></a>
<a href="#"><img src="https://img.shields.io/badge/Stripe-141414?style=flat&logo=stripe&logoColor=white" alt="Stripe" /></a>
<a href="#"><img src="https://img.shields.io/badge/Datadog-141414?style=flat&logo=datadog&logoColor=white" alt="Datadog" /></a>
<a href="#"><img src="https://img.shields.io/badge/Salesforce-141414?style=flat" alt="Salesforce" /></a>
<a href="#"><img src="https://img.shields.io/badge/GitHub-141414?style=flat&logo=github&logoColor=white" alt="GitHub" /></a>
<a href="#"><img src="https://img.shields.io/badge/Red%20Hat-141414?style=flat&logo=redhat&logoColor=white" alt="Red Hat" /></a>
<a href="#"><img src="https://img.shields.io/badge/Supabase-141414?style=flat&logo=supabase&logoColor=white" alt="Supabase" /></a>
<a href="#"><img src="https://img.shields.io/badge/Canva-141414?style=flat" alt="Canva" /></a>
<a href="#"><img src="https://img.shields.io/badge/Notion-141414?style=flat&logo=notion&logoColor=white" alt="Notion" /></a>
<a href="#"><img src="https://img.shields.io/badge/Hasura-141414?style=flat&logo=hasura&logoColor=white" alt="Hasura" /></a>
<a href="#"><img src="https://img.shields.io/badge/Framer-141414?style=flat&logo=framer&logoColor=white" alt="Framer" /></a>
<a href="#"><img src="https://img.shields.io/badge/Cursor-141414?style=flat&logo=cursor&logoColor=white" alt="Cursor" /></a>
</p>

## The Problem

Every MCP tool call dumps raw data into your context window. A Playwright snapshot costs 56 KB. Twenty GitHub issues cost 59 KB. One access log — 45 KB. After 30 minutes, 40% of your context is gone. And when the agent compacts the conversation to free space, it forgets which files it was editing, what tasks are in progress, and what you last asked for. On top of that, the agent wastes output tokens on filler, pleasantries, and verbose explanations — burning context from both sides.

### How Context Mode Solves It

Context Mode is an MCP server that solves all four sides of this problem:

1. **Context Saving** — Sandbox tools keep raw data out of the context window. 315 KB becomes 5.4 KB. 98% reduction.
2. **Session Continuity** — Every file edit, git operation, task, error, and user decision is tracked in SQLite. When the conversation compacts, context-mode doesn't dump this data back into context — it indexes events into FTS5 and retrieves only what's relevant via BM25 search. The model picks up exactly where you left off. If you don't `--continue`, previous session data is deleted immediately — a fresh session means a clean slate.
3. **Think in Code** — The LLM should program the analysis, not compute it. Instead of reading 50 files into context to count functions, the agent writes a script that does the counting and `console.log()`s only the result. One script replaces ten tool calls and saves 100x context. This is a mandatory paradigm across all 17 supported clients, plus the OpenClaw gateway integration: stop treating the LLM as a data processor, treat it as a code generator.

   ```js
   // Before: 47 × Read() = 700 KB.  After: 1 × ctx_execute() = 3.6 KB.
```

---
## microsoft/agent-lightning  (★17934, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['agentlightning', '.agents'] | tree=274

### README (head)
```
<p align="center">
  <img src="docs/images/agl-v1.0.svg" alt="Agent Lightning v1.0" width="500">
</p>

<p align="center"><em>3,500-Line Lightweight Agentic RL Framework for Training Agents with Real Harnesses!</em></p>

<p align="center">
  <a href="https://microsoft.github.io/agent-lightning/stable/">Documentation</a> &nbsp;·&nbsp; <a href="https://arxiv.org/pdf/2608.17528">Technical Report</a> &nbsp;·&nbsp; <a href="LICENSE">MIT License</a>
</p>

> Agent Lightning was completely refactored in v1.0. For legacy releases earlier than v1.0, see [this branch](https://github.com/microsoft/agent-lightning/tree/v0.x).

## ⚡ Key Features

- 🪶 **~3,500 lines of code:** We treat simplicity as the first principle.
- 🧩 **Train with real agent harnesses:** Agents interact with the model through the Agent Lightning v1.0 proxy with **ZERO changes**, while keeping tools, context, control flow, and environments in the loop.
- ☸️ **Native Kubernetes support:** Run agents directly as Kubernetes Jobs without relying on external sandbox services.
- 💻 **Full coding agent training example:** Using only **6K training samples**, an end-to-end Qwen3.5-9B workflow improves SWE-bench Verified from **41.8% to 56.4%**, a gain of **14.6 percentage points**. We release the full pipeline, including data cleaning, reward-hacking prevention, and training scripts.

## ⚡ Installation

The following is an example installation on a CUDA 13.0 machine:

```bash
cd <this-repo>
uv sync
bash scripts/setup_verl.sh 0.8.0 cu130
```

See the [Installation Guide](https://microsoft.github.io/agent-lightning/stable/00-installation/) for details.


## ⚡ Architecture

<p align="center">
  <img src="docs/images/architecture.jpg" alt="Agent Lightning v1.0 architecture" width="800">
</p>

Agent Lightning v1.0 keeps the training architecture simple with three lightweight components:

- **Trainer:** Runs `verl` and vLLM, builds training samples, and updates the policy.
- **API Gateway:** Proxies model requests and captures training data.
- **Rollout Controller:** Runs agents locally or as Kubernetes Jobs.

The Trainer creates rollouts, the Controller launches agents, and the Gateway turns interactions into training data, while agents continue to run with their real harnesses.
```

---
## cft0808/edict  (★16758, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['agents', 'agents.json', 'edict_agent_architecture.md'] | tree=266

### README (head)
```
<h1 align="center">⚔️ 三省六部 · Edict</h1>

<p align="center">
  <strong>我用 1300 年前的帝国制度，重新设计了 AI 多 Agent 协作架构。<br>结果发现，古人比现代 AI 框架更懂分权制衡。</strong>
</p>

<p align="center">
  <sub>12 个 AI Agent（11 个业务角色 + 1 个兼容角色）组成三省六部：太子分拣、中书省规划、门下省审核封驳、尚书省派发、六部+吏部并行执行。<br>比 CrewAI 多一层<b>制度性审核</b>，比 AutoGen 多一个<b>实时看板</b>。</sub>
</p>

<p align="center">
  <a href="#-demo">🎬 看 Demo</a> ·
  <a href="#-30-秒快速体验">🚀 30 秒体验</a> ·
  <a href="#-架构">🏛️ 架构</a> ·
  <a href="#-功能全景">📋 看板功能</a> ·
  <a href="docs/task-dispatch-architecture.md">📚 架构文档</a> ·
  <a href="README_EN.md">English</a> ·
  <a href="README_JA.md">日本語</a> ·
  <a href="CONTRIBUTING.md">参与贡献</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/OpenClaw-Required-blue?style=flat-square" alt="OpenClaw">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Agents-12_Specialized-8B5CF6?style=flat-square" alt="Agents">
  <img src="https://img.shields.io/badge/Dashboard-Real--time-F59E0B?style=flat-square" alt="Dashboard">
  <img src="https://img.shields.io/badge/License-MIT-22C55E?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Frontend-React_18-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React">
  <img src="https://img.shields.io/badge/Backend-stdlib_only-EC4899?style=flat-square" alt="Zero Backend Dependencies">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/公众号-cft0808-07C160?style=for-the-badge&logo=wechat&logoColor=white" alt="WeChat">
</p>

---

## 🎬 Demo

<p align="center">
  <video src="docs/Agent_video_Pippit_20260225121727.mp4" width="100%" autoplay muted loop playsinline controls>
    您的浏览器不支持视频播放，请查看下方 GIF 或 <a href="docs/Agent_video_Pippit_20260225121727.mp4">下载视频</a>。
  </video>
  <br>
  <sub>🎥 三省六部 AI 多 Agent 协作全流程演示</sub>
```

---
## microsoft/SkillOpt  (★16527, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=563

### README (head)
```
# SkillOpt: Executive Strategy for Self-Evolving Agent Skills

*Train agent skills like you train neural networks — with epochs, (mini-)batchsize, learning rates, and validation gates — but without touching model weights.*

[![Project Page](https://img.shields.io/badge/Project%20Page-SkillOpt-8dbb3c)](https://microsoft.github.io/SkillOpt/) [![Paper](https://img.shields.io/badge/Paper-arXiv-b31b1b)](https://arxiv.org/abs/2605.23904) [![Project Video](https://img.shields.io/badge/Project%20Video-Watch%20Demo-ff0000)](https://youtu.be/JUBMDTCiM0M) [![PyPI](https://img.shields.io/badge/PyPI-skillopt-green.svg)](https://pypi.org/project/skillopt/) [![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<p align="center">
  <a href="https://trendshift.io/repositories/38498?utm_source=repository-badge&amp;utm_medium=badge&amp;utm_campaign=badge-repository-38498" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/repositories/38498" alt="microsoft%2FSkillOpt | Trendshift" width="250" height="55"/></a>
  <a href="https://trendshift.io/repositories/38498?utm_source=trendshift-badge&utm_medium=badge&utm_campaign=badge-trendshift-38498" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/trendshift/repositories/38498/weekly?language=Python" alt="microsoft%2FSkillOpt | Trendshift" width="250" height="55"/></a>
</p>

> 📖 **For installation, data preparation, training/eval commands, configuration, and framework internals, start with the versioned [SkillOpt documentation](https://github.com/microsoft/SkillOpt/blob/main/docs/index.md). A concise rendered overview is available in the [Documentation & Reproduction Guide](https://microsoft.github.io/SkillOpt/docs/guideline.html), and longer-form engineering analysis appears on the [Technical Blog](https://microsoft.github.io/SkillOpt/blog/). We also maintain a [Changelog](CHANGELOG.md) for released and unreleased changes.**

---

## News 🔥🔥🔥
- **[2026-07-24]** 📰 **SkillOpt in the news.** Read the official [Microsoft Research feature](https://www.microsoft.com/en-us/research/blog/skillopt-agent-skills-as-trainable-parameters/), along with recent coverage from [VentureBeat](https://venturebeat.com/orchestration/microsofts-open-source-skillopt-automatically-upgrades-ai-agent-skills-without-touching-model-weights), [Synced (机器之心)](https://mp.weixin.qq.com/s/pMlyj3a3KOh8L7cIHClRXA), [Flowtivity](https://flowtivity.ai/blog/microsoft-skillopt-train-ai-agent-skills/), and [The Decoder](https://the-decoder.com/microsofts-skillopt-boosts-gpt-5-5-by-using-nothing-but-a-trained-markdown-file/).
- **[2026-07-02]** 🚀 **SkillOpt [v0.2.0](https://github.com/microsoft/SkillOpt/releases/tag/v0.2.0) is out on [PyPI](https://pypi.org/project/skillopt/)!** Headline feature: **SkillOpt-Sleep**, a nightly offline self-evolution engine (harvest → mine → replay → consolidate behind a held-out validation gate), now shipped as the `skillopt-sleep` CLI. It also includes experimental multi-objective, replay, and dream-rollout controls; the main CLI keeps conservative defaults and does not expose every experiment-harness control as a flag. The release source adds integration shells for **Claude Code, Codex, Copilot, and Devin**, plus an **OpenClaw reference adaptation**; these plugin/MCP files live in the repository rather than the PyPI wheel. It also adds SearchQA split materialization, Windows robustness, and hardened JSON parsing. See the [release notes](https://github.com/microsoft/SkillOpt/releases/tag/v0.2.0) for full release details and contributor acknowledgements.
- **[2026-06-15]** 😴 **SkillOpt-Sleep (preview)** — a nightly offline self-evolution companion for local coding agents (Claude Code / Codex / Copilot): review past sessions, replay recurring tasks, and consolidate validated skills behind a held-out gate. See **[`docs/sleep/README.md`](docs/sleep/README.md)** for what it is, how to use it, and results.
- **[2026-06-03]** 🎉 **[gbrain](https://github.com/garrytan/gbrain), [gbrain-evals](https://github.com/garrytan/gbrain-evals/blob/main/docs/benchmarks/2026-06-03-skillopt.md), and [darwin-skill](https://github.com/alchaincyf/darwin-skill) have all integrated SkillOpt.**
- **[2026-06-02]** 🎉 **SkillOpt [v0.1.0](https://github.com/microsoft/SkillOpt/releases/tag/v0.1.0) is now available on [PyPI](https://pypi.org/project/skillopt/)!** Install with `pip install skillopt`. This initial release includes the full training loop (rollout → reflect → aggregate → select → update → evaluate), multi-backend support (OpenAI / Azure / Claude / Qwen / MiniMax), six built-in benchmarks, and WebUI dashboard.

---

## Overview

Modern agent skills are usually hand-crafted, generated one-shot by a strong
LLM, or evolved through loosely controlled self-revision — none of which
behaves like a deep-learning optimizer for the skill itself, and none of
which reliably improves over its starting point under feedback.

**SkillOpt treats the skill document as the trainable state of a frozen
agent**, and trains it with the discipline that makes weight-space
optimization reproducible. A separate optimizer model turns scored rollouts
into bounded add / delete / replace edits on a single skill document; in the
default paper-style path, a candidate edit is accepted only when it strictly
improves a held-out validation score. A textual learning-rate budget, a rejected-edit buffer,
and an epoch-wise slow / meta update make skill training stable while
adding **zero inference-time model calls** at deployment.

The deployed artifact is a compact `best_skill.md` (typically 300–2,000
tokens) that runs against the unchanged target model. Across **six
benchmarks, seven target models, and three execution harnesses** (direct
chat, Codex CLI, Claude Code CLI), SkillOpt is best or tied-best on **all
52 evaluated (model, benchmark, harness) cells** and on GPT-5.5 lifts the
```

---
## HKUDS/DeepCode  (★16456, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=1035

### README (head)
```
<div align="center">

<table style="border: none; margin: 0 auto; padding: 0; border-collapse: collapse;">
<tr>
<td align="center" style="vertical-align: middle; padding: 10px; border: none; width: 250px;">
  <img src="assets/logo.png" alt="DeepCode Logo" width="200" style="margin: 0; padding: 0; display: block;"/>
</td>
<td align="left" style="vertical-align: middle; padding: 10px 0 10px 30px; border: none;">
  <pre style="font-family: 'Courier New', monospace; font-size: 16px; color: #0EA5E9; margin: 0; padding: 0; text-shadow: 0 0 10px #0EA5E9, 0 0 20px rgba(14,165,233,0.5); line-height: 1.2; transform: skew(-1deg, 0deg); display: block;">    ██████╗ ███████╗███████╗██████╗  ██████╗ ██████╗ ██████╗ ███████╗
    ██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║  ██║█████╗  █████╗  ██████╔╝██║     ██║   ██║██║  ██║█████╗
    ██║  ██║██╔══╝  ██╔══╝  ██╔═══╝ ██║     ██║   ██║██║  ██║██╔══╝
    ██████╔╝███████╗███████╗██║     ╚██████╗╚██████╔╝██████╔╝███████╗
    ╚═════╝ ╚══════╝╚══════╝╚═╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝</pre>
</td>
</tr>
</table>

<div align="center">
<a href="https://trendshift.io/repositories/14665?utm_source=repository-badge&amp;utm_medium=badge&amp;utm_campaign=badge-repository-14665" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/repositories/14665" alt="HKUDS%2FDeepCode | Trendshift" width="250" height="55"/></a>
<a href="https://trendshift.io/repositories/14665?utm_source=trendshift-badge&amp;utm_medium=badge&amp;utm_campaign=badge-trendshift-14665" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/trendshift/repositories/14665/daily?language=Python" alt="HKUDS%2FDeepCode | Trendshift" width="250" height="55"/></a>
</div>

<!-- <img src="https://readme-typing-svg.herokuapp.com?font=Russo+One&size=28&duration=2000&pause=800&color=06B6D4&background=00000000&center=true&vCenter=true&width=800&height=50&lines=%E2%9A%A1+OPEN+AGENTIC+CODING+%E2%9A%A1" alt="DeepCode Tech Subtitle" style="margin-top: 5px; filter: drop-shadow(0 0 12px #06B6D4) drop-shadow(0 0 24px rgba(6,182,212,0.4));"/> -->

# <img src="https://github.com/Zongwei9888/Experiment_Images/raw/43c585dca3d21b8e4b6390d835cdd34dc4b4b23d/DeepCode_images/title_logo.svg" alt="DeepCode Logo" width="32" height="32" style="vertical-align: middle; margin-right: 8px;"/> DeepCode: Open Agentic Coding

### *Advancing Code Generation with Multi-Agent Systems*

<p align="center">
  <a href="https://hkuds.github.io/DeepCode/" target="_blank"><img alt="Website — hkuds.github.io/DeepCode" src="https://img.shields.io/badge/Website-hkuds.github.io%2FDeepCode%20%E2%86%97-06B6D4?style=for-the-badge&labelColor=0B1116" height="36"></a>
</p>

<!-- <p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-00d4ff?style=for-the-badge&logo=rocket&logoColor=white" alt="Version">

  <img src="https://img.shields.io/badge/License-MIT-4ecdc4?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License">
  <img src="https://img.shields.io/badge/AI-Multi--Agent-9b59b6?style=for-the-badge&logo=brain&logoColor=white" alt="AI">
  <img src="https://img.shields.io/badge/HKU-Data_Intelligence_Lab-f39c12?style=for-the-badge&logo=university&logoColor=white" alt="HKU">
</p> -->
<p>
  <a href="https://github.com/HKUDS/DeepCode/stargazers"><img src='https://img.shields.io/github/stars/HKUDS/DeepCode?color=00d9ff&style=for-the-badge&logo=star&logoColor=white&labelColor=1a1a2e' /></a>
  <a href='https://arxiv.org/abs/2512.07921'><img src="https://img.shields.io/badge/Paper-arXiv-orange?style=for-the-badge&logo=arxiv&logoColor=white&labelColor=1a1a2e"></a>
  <img src="https://img.shields.io/badge/🐍Python-3.12%2B-4ecdc4?style=for-the-badge&logo=python&logoColor=white&labelColor=1a1a2e">
  <!-- <a href="https://pypi.org/project/deepcode-hku/"><img src="https://img.shields.io/pypi/v/deepcode-hku.svg?style=for-the-badge&logo=pypi&logoColor=white&labelColor=1a1a2e&color=ff6b6b"></a> -->
```

---
## EverMind-AI/EverOS  (★12584, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=1032

### README (head)
```
<div align="center" id="readme-top">

![EverOS banner](https://github.com/user-attachments/assets/806e9d7f-c861-4b89-9141-11e38f8753e3)

<p align="center">
  <a href="https://x.com/evermind"><img src="https://img.shields.io/badge/EverMind-000000?labelColor=gray&style=for-the-badge&logo=x&logoColor=white" alt="X"></a>
  <a href="https://huggingface.co/EverMind-AI"><img src="https://img.shields.io/badge/🤗_HuggingFace-EverMind-F5C842?labelColor=gray&style=for-the-badge" alt="HuggingFace"></a>
  <a href="https://discord.gg/gYep5nQRZJ"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fdiscord.com%2Fapi%2Fv10%2Finvites%2FgYep5nQRZJ%3Fwith_counts%3Dtrue&query=%24.approximate_presence_count&suffix=%20online&label=Discord&color=404EED&labelColor=gray&style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/EverMind-AI/EverOS/discussions/67"><img src="https://img.shields.io/badge/WeCom-EverMind_社区-07C160?labelColor=gray&style=for-the-badge&logo=wechat&logoColor=white" alt="WeChat"></a>
</p>

[Website](https://evermind.ai) · [Documentation](https://docs.evermind.ai) · [Blog](https://evermind.ai/blogs) · [中文](README.zh-CN.md)

</div>


<br>

<details>
  <summary><kbd>Table of Contents</kbd></summary>

<br>

- [Why Ever OS](#why-ever-os)
- [Quick Start](#quick-start)
- [Use Cases](#use-cases)
- [Documentation](#documentation)
- [EverMind Ecosystem](#evermind-ecosystem)
- [Contributing](#contributing)

<br>

</details>


## Why Ever OS

EverOS is a Python library and local-first memory runtime for agents and
makers. It gives one portable memory layer across coding assistants, apps,
devices, and workflows from day one. It stores conversations, files, and agent
trajectories as readable Markdown, then syncs local SQLite and LanceDB indexes
for fast retrieval and self-evolving reuse.

<table>
<tr>
```

---
## bytedance/trae-agent  (★12062, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['trae_agent', 'evaluation'] | tree=134

### README (head)
```
# Trae Agent

[![arXiv:2507.23370](https://img.shields.io/badge/TechReport-arXiv%3A2507.23370-b31a1b)](https://arxiv.org/abs/2507.23370)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Pre-commit](https://github.com/bytedance/trae-agent/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/bytedance/trae-agent/actions/workflows/pre-commit.yml)
[![Unit Tests](https://github.com/bytedance/trae-agent/actions/workflows/unit-test.yml/badge.svg)](https://github.com/bytedance/trae-agent/actions/workflows/unit-test.yml)
[![Discord](https://img.shields.io/discord/1320998163615846420?label=Join%20Discord&color=7289DA)](https://discord.gg/VwaQ4ZBHvC)

**Trae Agent** is an LLM-based agent for general purpose software engineering tasks. It provides a powerful CLI interface that can understand natural language instructions and execute complex software engineering workflows using various tools and LLM providers.

For technical details please refer to [our technical report](https://arxiv.org/abs/2507.23370).

**Project Status:** The project is still being actively developed. Please refer to [docs/roadmap.md](docs/roadmap.md) and [CONTRIBUTING](CONTRIBUTING.md) if you are willing to help us improve Trae Agent.

**Difference with Other CLI Agents:** Trae Agent offers a transparent, modular architecture that researchers and developers can easily modify, extend, and analyze, making it an ideal platform for **studying AI agent architectures, conducting ablation studies, and developing novel agent capabilities**. This **_research-friendly design_** enables the academic and open-source communities to contribute to and build upon the foundational agent framework, fostering innovation in the rapidly evolving field of AI agents.

## ✨ Features

- 🌊 **Lakeview**: Provides short and concise summarisation for agent steps
- 🤖 **Multi-LLM Support**: Works with OpenAI, Anthropic, Doubao, Azure, OpenRouter, Ollama and Google Gemini APIs
- 🛠️ **Rich Tool Ecosystem**: File editing, bash execution, sequential thinking, and more
- 🎯 **Interactive Mode**: Conversational interface for iterative development
- 📊 **Trajectory Recording**: Detailed logging of all agent actions for debugging and analysis
- ⚙️ **Flexible Configuration**: YAML-based configuration with environment variable support
- 🚀 **Easy Installation**: Simple pip-based installation

## 🚀 Installation

### Requirements
- UV (https://docs.astral.sh/uv/)
- API key for your chosen provider (OpenAI, Anthropic, Google Gemini, OpenRouter, etc.)

### Setup

```bash
git clone https://github.com/bytedance/trae-agent.git
cd trae-agent
uv sync --all-extras
source .venv/bin/activate
```

## ⚙️ Configuration

### YAML Configuration (Recommended)

```

---
## ifixai-ai/iFixAi  (★11872, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['.agents'] | tree=502

### README (head)
```
<p align="center">
  <img src="docs/assets/ifixai-banner.png" alt="iFixAi" width="200" />
</p>

<h1 align="center">iFixAi</h1>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.ko.md">한국어</a>
</p>

<p align="center"><strong> Independent Auditing of AI Agents </strong></p>
<p align="center">Catch your agent's mistakes and blind spots before the shit hits the fan.</p>

<p align="center">
  <a href="https://trendshift.io/repositories/29638" target="_blank"><img src="https://trendshift.io/api/badge/trendshift/repositories/29638/weekly?language=Python" alt="iFixAi — #1 Python repository of the week on Trendshift" width="250" height="55" /></a>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> •
  <a href="#three-ways-to-run">Three ways to run</a> •
  <a href="#test-your-own-agent">Test your agent</a> •
  <a href="#what-you-get-back">Scoring</a> •
  <a href="docs/">Docs</a> •
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="license: Apache 2.0" /></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="python 3.10+" /></a>
  <a href="https://github.com/ifixai-ai/iFixAi/actions/workflows/ci.yml"><img src="https://github.com/ifixai-ai/iFixAi/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/inspections-50-orange.svg" alt="50 inspections" />
  <a href="https://github.com/ifixai-ai/iFixAi/issues?q=is%3Aopen+label%3A%22good+first+issue%22"><img src="https://img.shields.io/github/issues/ifixai-ai/iFixAi/good%20first%20issue?label=good%20first%20issues&color=7057ff" alt="good first issues" /></a>
</p>

<p align="center">
  <img src="docs/assets/scorecard-screenshot.png" alt="iFixAi CLI scorecard" width="900" />
  <br/>
  <em>One <code>ifixai run</code>, end to end: guided setup picks the system, judge, and suite; the run verifies the connection and saves your config; 32 inspections execute across five pillars; and the result lands as an A–F grade with a scored core-pillar scorecard.</em>
</p>

---

## What it is

The existing Eval, Red-teaming, and Observability Tools are evaluating the agent mainly based on tech capability (token efficiency, latency, prompt injections). They cannot answer the most crucial question.
```

---
## 0x4m4/hexstrike-ai  (★11462, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=15

### README (head)
```
<div align="center">

<img src="assets/hexstrike-logo.png" alt="HexStrike AI Logo" width="220" style="margin-bottom: 20px;"/>

# HexStrike AI MCP Agents v6.0
### AI-Powered MCP Cybersecurity Automation Platform

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Penetration%20Testing-red.svg)](https://github.com/0x4m4/hexstrike-ai)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://github.com/0x4m4/hexstrike-ai)
[![Version](https://img.shields.io/badge/Version-6.0.0-orange.svg)](https://github.com/0x4m4/hexstrike-ai/releases)
[![Tools](https://img.shields.io/badge/Security%20Tools-150%2B-brightgreen.svg)](https://github.com/0x4m4/hexstrike-ai)
[![Agents](https://img.shields.io/badge/AI%20Agents-12%2B-purple.svg)](https://github.com/0x4m4/hexstrike-ai)
[![Stars](https://img.shields.io/github/stars/0x4m4/hexstrike-ai?style=social)](https://github.com/0x4m4/hexstrike-ai)

**Advanced AI-powered penetration testing MCP framework with 150+ security tools and 12+ autonomous AI agents**

**Owned & developed by [OTT Cybersecurity LLC](https://overthetop.ae/)**

[📋 What's New](#whats-new-in-v60) • [🏗️ Architecture](#architecture-overview) • [🚀 Installation](#installation) • [🛠️ Features](#features) • [🤖 AI Agents](#ai-agents) • [📡 API Reference](#api-reference)

</div>

---

<div align="center">

## Follow Our Social Accounts

<p align="center">
  <a href="https://discord.gg/BWnmrrSHbA">
    <img src="https://img.shields.io/badge/Discord-Join-7289DA?logo=discord&logoColor=white&style=for-the-badge" alt="Join our Discord" />
  </a>
  &nbsp;&nbsp;
  <a href="https://www.linkedin.com/company/hexstrike-ai">
    <img src="https://img.shields.io/badge/LinkedIn-Follow%20us-0A66C2?logo=linkedin&logoColor=white&style=for-the-badge" alt="Follow us on LinkedIn" />
  </a>
</p>



</div>

---
```

---
## yizhiyanhua-ai/fireworks-tech-graph  (★11007, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['agents', 'agentloop-core.svg'] | tree=310

### README (head)
```
[English](README.md) | [中文](README.zh.md)

[Release history](docs/releases/README.md) · [Changelog](CHANGELOG.md)

# fireworks-tech-graph

> **Stop drawing diagrams by hand.** Describe your system in English or Chinese — get geometry-safe SVG, PNG, focused SVG-to-GIF motion, and offline interactive technical diagrams.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/yizhiyanhua-ai/fireworks-tech-graph)](https://github.com/yizhiyanhua-ai/fireworks-tech-graph/releases)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-10a37f)](https://learn.chatgpt.com/docs/build-skills)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-d97757)](https://code.claude.com/docs/en/skills)
[![12 Visual Styles](https://img.shields.io/badge/Styles-12-purple)]()
[![14 Diagram Types](https://img.shields.io/badge/Diagram%20Types-14-green)]()
[![UML Support](https://img.shields.io/badge/UML-Full%20Support-orange)]()

---

## Overview

`fireworks-tech-graph` is one Agent Skill that works unchanged in **Codex and Claude Code**. It turns natural language descriptions into polished, geometry-checked SVG diagrams, high-resolution PNGs, validated SVG-to-GIF semantic motion, and offline interactive HTML. The focused animation path accepts a generated semantic SVG and emits one compact, probed GIF. It ships with **11 generator-backed styles** and **1 AI-authored style (Dark Luxury)**. Four engineering-first styles add executable contracts for C4 reviews, cloud deployments, event streams, and reliability investigations, alongside deep AI/Agent domain patterns and all 14 UML diagram types.

```
User: "Generate a Mem0 memory architecture diagram, dark style"
  → Skill classifies: Memory Architecture Diagram, Style 2
  → Generates SVG with swim lanes, cylinders, semantic arrows
  → Exports 1920px PNG
  → Reports: mem0-architecture.svg / mem0-architecture.png
```

---

## Sponsors

<table>
  <tr>
    <td width="200" align="center"><a href="https://aigocode.app/invite/yizhiyanhua"><img src="assets/sponsors/aigocode.png" alt="AIGoCode" width="160" /></a></td>
    <td>Thanks to <strong>AIGoCode</strong> for sponsoring this project! AIGoCode is an all-in-one platform that integrates Claude Code, Codex, and the latest Gemini models, providing you with stable, efficient, and highly cost-effective AI coding services. The platform offers flexible subscription plans, zero risk of account suspension, direct access with no VPN required, and lightning-fast responses. AIGoCode has prepared a special benefit for <strong>fireworks-tech-graph</strong> users: if you register via <a href="https://aigocode.app/invite/yizhiyanhua">this link</a>, you'll receive an extra <strong>10% bonus credit</strong> on your first top-up!</td>
  </tr>
  <tr>
    <td width="200" align="center"><a href="https://go.apimart.ai/gh-fireworks-tech-graph"><img src="assets/sponsors/apimart.png" alt="APIMart" width="160" /></a></td>
    <td>Thanks to <strong>APIMart</strong> for sponsoring this project! APIMart is a low-cost API platform for AI image &amp; video generation — GPT-Image-2 from <strong>$0.006/image</strong>, 160+ images per dollar. One async API covers both image and video: submit a task, get an ID, fetch results via polling or callback. Batch tens of thousands of images without timeouts, switch models without changing code. Pay-as-you-go with no monthly fee — <a href="https://go.apimart.ai/gh-fireworks-tech-graph">sign up here</a> to get started.</td>
  </tr>
</table>

```

---
## BigBodyCobain/Shadowbroker  (★11004, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=1304

### README (head)
```
<p align="center">
  <h1 align="center">🛰️ S H A D O W B R O K E R</h1>
  <p align="center"><strong>Global Threat Intercept — Real-Time Geospatial Intelligence Platform</strong></p>
  <p align="center">

  </p>
</p>

---




[![ShadowBroker](/uploads/46f99d19fa141a2efba37feee9de8aab/Title.jpg)](https://github.com/user-attachments/assets/248208ec-62f7-49d1-831d-4bd0a1fa6852)





**ShadowBroker** is a decentralized intelligence platform that aggregates real-time, multi-domain OSINT telemetry from 60+ live intelligence feeds into a single dark-ops map interface. Aircraft, ships, satellites, conflict zones, CCTV networks, GPS jamming, internet-connected devices, police scanners, mesh radio nodes, and breaking geopolitical events — all updating in real time on one screen as well as an obfuscated communications protocol and information exchange infrastructure.

<details>
<summary>🛰️ Project Description</summary>

Built with **Next.js**, **MapLibre GL**, **FastAPI**, and **Python**. 40+ toggleable data layers, including SAR ground-change detection, **Telegram OSINT** (public channel previews geoparsed onto the map), a **server-side recon toolkit** (DNS, WHOIS, sanctions, BGP, IP sweep, and more), supply-chain risk overlays, and malware/C2 + CISA KEV cyber threat feeds. Multiple visual modes (DEFAULT / SATELLITE / FLIR / NVG / CRT). Right-click any point on Earth for a country dossier, head-of-state lookup, entity-graph expansion, and the latest Sentinel-2 satellite photo. ShadowBroker has no accounts, product telemetry, or analytics; the dashboard talks to your self-hosted backend. Sensitive recon and Shodan queries never hit third-party APIs from the browser — they are proxied through the backend with SSRF guards and local-operator auth. The **OpenClaw / agent command channel** exposes the same recon backends plus full telemetry search — no separate API integration required.

Designed for analysts, researchers, radio operators, and anyone who wants to see what the world looks like when every public signal is on the same map.
</details>

---

<details>
<summary>🌍 Why This Exists</summary>

A surprising amount of global telemetry is already public — aircraft ADS-B broadcasts, maritime AIS signals, satellite orbital data, earthquake sensors, mesh radio networks, police scanner feeds, environmental monitoring stations, internet infrastructure telemetry, and more. This data is scattered across dozens of tools and APIs. ShadowBroker combines all of it into a single interface.

The project does not introduce new surveillance capabilities — it aggregates and visualizes existing public datasets. It is fully open-source so anyone can audit exactly what data is accessed and how. ShadowBroker does not include product telemetry, analytics, or accounts. Operator-supplied keys stay in your local deployment, but live OSINT features necessarily make outbound requests to the public data providers you enable or query.

</details>

---


<details>
<summary>📡 Shodan & Recon (security-first)</summary>
```

---
## aden-hive/hive  (★10989, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=2800

### README (head)
```
<p align="center">
  <img width="100%" alt="Hive Banner" src="https://asset.acho.io/github/img/banner.gif" />
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="docs/i18n/zh-CN.md">简体中文</a> |
  <a href="docs/i18n/es.md">Español</a> |
  <a href="docs/i18n/hi.md">हिन्दी</a> |
  <a href="docs/i18n/pt.md">Português</a> |
  <a href="docs/i18n/ja.md">日本語</a> |
  <a href="docs/i18n/ru.md">Русский</a> |
  <a href="docs/i18n/ko.md">한국어</a>
</p>

<p align="center">
  <a href="https://github.com/aden-hive/hive/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Apache 2.0 License" /></a>
  <a href="https://www.ycombinator.com/companies/aden"><img src="https://img.shields.io/badge/Y%20Combinator-Aden-orange" alt="Y Combinator" /></a>
  <a href="https://discord.com/invite/MXE49hrKDk"><img src="https://img.shields.io/discord/1172610340073242735?logo=discord&labelColor=%235462eb&logoColor=%23f5f5f5&color=%235462eb" alt="Discord" /></a>
  <a href="https://x.com/aden_hq"><img src="https://img.shields.io/twitter/follow/teamaden?logo=X&color=%23f5f5f5" alt="Twitter Follow" /></a>
  <a href="https://www.linkedin.com/company/teamaden/"><img src="https://custom-icon-badges.demolab.com/badge/LinkedIn-0A66C2?logo=linkedin-white&logoColor=fff" alt="LinkedIn" /></a>
  <img src="https://img.shields.io/badge/MCP-102_Tools-00ADD8?style=flat-square" alt="MCP" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Agent_Harness-Runtime_Layer-ff6600?style=flat-square" alt="Agent Harness" />
  <img src="https://img.shields.io/badge/AI_Agents-Self--Improving-brightgreen?style=flat-square" alt="AI Agents" />
  <img src="https://img.shields.io/badge/Multi--Agent-Systems-blue?style=flat-square" alt="Multi-Agent" />
  <img src="https://img.shields.io/badge/Headless-Development-purple?style=flat-square" alt="Headless" />
  <img src="https://img.shields.io/badge/Human--in--the--Loop-orange?style=flat-square" alt="HITL" />
  <img src="https://img.shields.io/badge/Browser-Use-red?style=flat-square" alt="Browser Use" />
</p>
<p align="center">
  <img src="https://img.shields.io/badge/OpenAI-supported-412991?style=flat-square&logo=openai" alt="OpenAI" />
  <img src="https://img.shields.io/badge/Anthropic-supported-d4a574?style=flat-square" alt="Anthropic" />
  <img src="https://img.shields.io/badge/Google_Gemini-supported-4285F4?style=flat-square&logo=google" alt="Gemini" />
</p>

<p align="center"><em>The agent harness for production workloads — state management, failure recovery, observability, and human oversight so your agents actually run.</em></p>

## Overview

OpenHive is a zero-setup, model-agnostic runtime for **colonies of agents**. A colony is a group of specialized agents that work together to run one business process: a **Queen** — the persistent, client-facing lead — plus however many **worker** agents the job needs. You describe the outcome; the Queen does the work, then grows a colony around it to run that work reliably and at scale.

The mechanism underneath is **one loop controlling many loops**. Hive has a single execution primitive: the Queen *is* an agent loop, and every worker is a **clone** of it — same tools, same model, its own task. There is no graph to compile and no orchestration boilerplate to write. The colony coordinates through a shared ledger and a persistent plan, with crash-safe state, deep observability, and human oversight built into the one primitive every agent shares. See the **[Architecture Overview](docs/architecture/README.md)** for how it works.
```

---
## numman-ali/openskills  (★10725, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=116

### README (head)
```
<div align="center">

<img src="./assets/logo.svg" alt="OpenSkills" width="420" />

<br/>
<br/>

**Universal skills loader for AI coding agents**

One CLI. Every agent. Same format as Claude Code.

[![npm version](https://img.shields.io/npm/v/openskills.svg)](https://www.npmjs.com/package/openskills)
[![npm downloads](https://img.shields.io/npm/dm/openskills.svg)](https://www.npmjs.com/package/openskills)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

[Quick Start](#-quick-start) · [How It Works](#-how-it-works) · [Commands](#-commands) · [Create Skills](#-creating-your-own-skills) · [FAQ](#-faq)

</div>

---

## ✨ What Is OpenSkills?

OpenSkills brings **Anthropic's skills system** to every AI coding agent — Claude Code, Cursor, Windsurf, Aider, Codex, and anything that can read `AGENTS.md`.

**Think of it as the universal installer for SKILL.md.**

---

## 🚀 Quick Start

```bash
npx openskills install anthropics/skills
npx openskills sync
```

By default, installs are project-local (`./.claude/skills`, or `./.agent/skills` with `--universal`). Use `--global` for `~/.claude/skills`.

---

## ✅ Why OpenSkills

- **Exact Claude Code compatibility** — same prompt format, same marketplace, same folder structure
- **Universal** — works with Claude Code, Cursor, Windsurf, Aider, Codex, and more
- **Progressive disclosure** — load skills only when needed (keeps context clean)
```

---
## openchamber/openchamber  (★9410, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['.agents', 'AGENTS.md'] | tree=4495

### README (head)
```
# <picture><source media="(prefers-color-scheme: dark)" srcset="docs/references/badges/openchamber-logo-dark.svg"><img src="docs/references/badges/openchamber-logo-light.svg" width="32" height="32" align="absmiddle" /></picture> OpenChamber

[![GitHub stars](https://img.shields.io/github/stars/openchamber/openchamber?style=flat&labelColor=100F0F&color=66800B)](https://github.com/openchamber/openchamber/stargazers)
[![GitHub release](https://img.shields.io/github/v/release/openchamber/openchamber?style=flat&labelColor=100F0F&color=205EA6)](https://github.com/openchamber/openchamber/releases/latest)
[![Discord](https://img.shields.io/badge/Discord-join.svg?style=flat&labelColor=100F0F&color=8B7EC8&logo=discord&logoColor=FFFCF0)](https://discord.gg/ZYRSdnwwKA)
[![Support the project](https://img.shields.io/badge/Support-Project-black?style=flat&labelColor=100F0F&color=EC8B49&logo=patreon&logoColor=FFFCF0)](https://www.patreon.com/openchamber)

> [!IMPORTANT]
> 🏖️ I'm on vacation from 31 Aug to 4 Sep. I'll review issues and PRs when I'm back. Thanks for your patience.

## Run agent work. Keep control. Ship from anywhere.

**OpenChamber is an open-source workspace for running, supervising, and reviewing AI coding work across desktop, browser, editor, and mobile.**

OpenChamber gives you one place to direct agent work, understand the changes, and move them toward release. Your projects stay available when you switch devices or step away.

![OpenChamber Chat](docs/references/chat_example.png)

<details>
<summary>More screenshots</summary>

![VS Code Extension](packages/vscode/extension.jpg)

<p>
<img src="docs/references/pwa_chat_example.png" width="45%" alt="OpenChamber PWA chat">
<img src="docs/references/pwa_diff_example.png" width="45%" alt="OpenChamber PWA diff review">
</p>

</details>

## What you can do with OpenChamber

### Goals that continue on their own

Give a session a finish line with **Session Goals**. OpenChamber checks the result after every turn and keeps the agent working until the goal is complete, blocked, or reaches the limit you set — even after you close the app.

### Compare and combine runs

Use **Multi-run** to give the same task to up to five models, each in its own session and optionally its own worktree. See what each one actually built, choose the best result, or use **Fusion** to combine the strongest parts into a new session.

### Guided changes walkthroughs

**Changes Walkthrough** turns a large diff into an AI-guided tour of the change. It groups related edits into steps, puts them in the order the change makes sense, and explains how the pieces fit together.

### Inspect a running app
```

---
## ValueCell-ai/ClawX  (★7600, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=1076

### README (head)
```

<p align="center">
  <img src="src/assets/logo.svg" width="128" height="128" alt="ClawX Logo" />
</p>

<h1 align="center">ClawX</h1>

<p align="center">
  <strong>The Desktop Interface for OpenClaw AI Agents</strong>
</p>

<p align="center">
  <a href="#why-clawx">Why ClawX</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#development">Development</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-MacOS%20%7C%20Windows%20%7C%20Linux-blue" alt="Platform" />
  <img src="https://img.shields.io/badge/electron-40+-47848F?logo=electron" alt="Electron" />
  <img src="https://img.shields.io/badge/react-19-61DAFB?logo=react" alt="React" />
  <a href="https://discord.com/invite/84Kex3GGAh" target="_blank">
  <img src="https://img.shields.io/discord/1399603591471435907?logo=discord&labelColor=%20%235462eb&logoColor=%20%23f5f5f5&color=%20%235462eb" alt="chat on Discord" />
  </a>
  <img src="https://img.shields.io/github/downloads/ValueCell-ai/ClawX/total?color=%23027DEB" alt="Downloads" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License" />
</p>

<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a> | <a href="README.ja-JP.md">日本語</a> | <a href="README.ru-RU.md">Русский</a>
</p>

---

## Overview

**ClawX** bridges the gap between powerful AI agents and everyday users. Built on top of [OpenClaw](https://github.com/OpenClaw), it transforms command-line AI orchestration into an accessible, beautiful desktop experience - no terminal required.

Whether you're automating workflows, managing AI-powered channels, or scheduling intelligent tasks, ClawX provides the interface you need to harness AI agents effectively.

ClawX comes pre-configured with best-practice model providers and natively supports Windows as well as multi-language settings. Compaction reserves use 25% of an explicitly configured model context window, or a conservative 50000-token fallback when that metadata is absent; completed turns continue through the summary instead of being replayed verbatim after compaction. Developer Mode shows the applied reserve value. You can also fine-tune advanced configurations via **Settings -> Advanced -> Developer Mode**.

<p align="center"><strong style="font-size:1.1em; text-decoration: underline;">For a full enterprise edition, dedicated service support, or tailored deployment guidance for your business scenario, contact us at <a href="mailto:public@valuecell.ai">public@valuecell.ai</a>.</strong></p>
```

---
## MrLesk/Backlog.md  (★6587, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=1369

### README (head)
```
<p align="center">
  <img src="./.github/backlog-logo.png" alt="Backlog.md logo" width="120">
</p>

<h1 align="center">Backlog.md</h1>
<p align="center"><strong>Markdown‑native Task Manager &amp; Kanban visualizer for any Git repository</strong></p>
<p align="center">AI agents write the code. You review the tasks: before, during, and after.</p>

<p align="center">
  <a href="https://www.npmjs.com/package/backlog.md"><img src="https://img.shields.io/npm/v/backlog.md?color=brightgreen" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/backlog.md"><img src="https://img.shields.io/npm/dm/backlog.md" alt="npm downloads"></a>
  <a href="https://github.com/MrLesk/Backlog.md/blob/main/LICENSE"><img src="https://img.shields.io/github/license/MrLesk/Backlog.md" alt="MIT license"></a>
  <a href="https://github.com/MrLesk/Backlog.md"><img src="https://img.shields.io/github/stars/MrLesk/Backlog.md?style=social" alt="GitHub stars"></a>
</p>

<p align="center">
<code>npm i -g backlog.md</code>
</p>

![Backlog demo GIF using: backlog board](./.github/backlog-v1.40.gif)


---

> **Backlog.md** turns any folder into a **self‑contained project board**
> powered by plain Markdown files and a zero‑config CLI.

## Why Backlog.md in the AI era

AI agents can now produce more plausible code in an hour than you can carefully read in a day.
The bottleneck is no longer writing code. It's your attention. You can't meaningfully review
15,000 generated lines in one sitting, but you can read a screenful of task specs with acceptance
criteria before any code exists, and push back while a misunderstanding is still one sentence,
not a rebuilt feature.

Backlog.md structures agent work around **three review checkpoints**:

1. **Review the spec:** the agent decomposes your idea into tasks with descriptions, acceptance
   criteria, and milestones before implementation starts.
2. **Review the plan:** the agent researches your codebase and writes its implementation plan
   into the task. Approve it or steer before any code is written.
3. **Review the code:** one task = one context window = one PR. Diffs stay a size a human can
   actually read.

Afterwards, the completed tasks remain in Git as a permanent record of what was attempted and why,
```

---
## op7418/CodePilot  (★6437, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=3279

### README (head)
```
<img src="docs/icon-readme.png" width="32" height="32" alt="CodePilot" style="vertical-align: middle; margin-right: 8px;" /> CodePilot
===

**A multi-model AI agent desktop client** -- connect any AI provider, extend with MCP & skills, control from your phone, and let your assistant learn your workflow.

[![GitHub release](https://img.shields.io/github/v/release/op7418/CodePilot)](https://github.com/op7418/CodePilot/releases)
[![Downloads](https://img.shields.io/github/downloads/op7418/CodePilot/total)](https://github.com/op7418/CodePilot/releases)
[![GitHub stars](https://img.shields.io/github/stars/op7418/CodePilot)](https://github.com/op7418/CodePilot/stargazers)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)](https://github.com/op7418/CodePilot/releases)
[![License](https://img.shields.io/badge/license-BSL--1.1-orange)](LICENSE)

[中文文档](./README_CN.md) | [日本語](./README_JA.md)

---

![CodePilot](https://github.com/user-attachments/assets/9750450a-9f6f-49ce-acd4-c623a4e24281)

---

[Download](#download) | [Quick Start](#quick-start) | [Documentation](#documentation) | [Contributing](#contributing) | [Community](#community)

---

## Download

| Platform | Download | Architecture |
|---|---|---|
| macOS | [Apple Silicon (.dmg)](https://github.com/op7418/CodePilot/releases/latest) · [Intel (.dmg)](https://github.com/op7418/CodePilot/releases/latest) | arm64 / x64 |
| Windows | [Installer (.exe)](https://github.com/op7418/CodePilot/releases/latest) | x64 |
| Linux | [AppImage / deb / rpm](https://github.com/op7418/CodePilot/releases/latest) | x64 / arm64 |

Official macOS stable builds can check, download, and install signed updates in the app. After manually installing the first supported Windows version, later Windows releases can update in the app using unsigned packages from the official GitHub Release; Linux releases remain manual downloads.

Or visit the [Releases](https://github.com/op7418/CodePilot/releases) page for all versions.

---

## Why CodePilot

### Multi-provider, one interface

Connect to **17+ AI providers** out of the box. Switch providers and models mid-conversation without losing context.

| Category | Providers |
|---|---|
```

---
## Eigenwise/atomic-agents  (★6215, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['atomic-agents', 'AGENTS.md'] | tree=568

### README (head)
```
# Atomic Agents

<img src="./.assets/logo.png" alt="Atomic Agents" width="350"/>

[![PyPI version](https://badge.fury.io/py/atomic-agents.svg)](https://badge.fury.io/py/atomic-agents)
[![Documentation](https://img.shields.io/badge/docs-read%20the%20docs-blue?logo=readthedocs&style=flat-square)](https://eigenwise.github.io/atomic-agents/)
[![Build Docs](https://github.com/eigenwise/atomic-agents/actions/workflows/docs.yml/badge.svg)](https://github.com/eigenwise/atomic-agents/actions/workflows/docs.yml)
[![Code Quality](https://github.com/eigenwise/atomic-agents/actions/workflows/code-quality.yml/badge.svg)](https://github.com/eigenwise/atomic-agents/actions/workflows/code-quality.yml)
[![Discord](https://img.shields.io/badge/chat-on%20discord-7289DA?logo=discord&style=flat-square)](https://discord.gg/J3W9b5AZJR)
[![PyPI downloads](https://img.shields.io/pypi/dm/atomic-agents?style=flat-square)](https://pypi.org/project/atomic-agents/)
[![Python Versions](https://img.shields.io/pypi/pyversions/atomic-agents?style=flat-square)](https://pypi.org/project/atomic-agents/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/eigenwise/atomic-agents?style=social)](https://github.com/eigenwise/atomic-agents/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/eigenwise/atomic-agents?style=social)](https://github.com/eigenwise/atomic-agents/network/members)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/eigenwise/atomic-agents)

## What is Atomic Agents?

The Atomic Agents framework is designed around the concept of atomicity to be an extremely lightweight and modular framework for building Agentic AI pipelines and applications without sacrificing developer experience and maintainability.

Think of it like building AI applications with LEGO blocks - each component (agent, tool, context provider) is:
- **Single-purpose**: Does one thing well
- **Reusable**: Can be used in multiple pipelines
- **Composable**: Easily combines with other components
- **Predictable**: Produces consistent, reliable outputs

Built on [Instructor](https://github.com/jxnl/instructor) and [Pydantic](https://docs.pydantic.dev/latest/), it enables you to create AI applications with the same software engineering principles you already know and love.

**NEW: Join our community on Discord at [discord.gg/J3W9b5AZJR](https://discord.gg/J3W9b5AZJR) and our official subreddit at [/r/AtomicAgents](https://www.reddit.com/r/AtomicAgents/)!**

## Table of Contents

- [Atomic Agents](#atomic-agents)
  - [What is Atomic Agents?](#what-is-atomic-agents)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
    - [Installation](#installation)
    - [Quick Example](#quick-example)
  - [Why Atomic Agents?](#why-atomic-agents)
  - [Core Concepts](#core-concepts)
    - [Anatomy of an Agent](#anatomy-of-an-agent)
    - [Context Providers](#context-providers)
    - [Chaining Schemas and Agents](#chaining-schemas-and-agents)
  - [Examples \& Documentation](#examples--documentation)
    - [Quickstart Examples](#quickstart-examples)
```

---
## epiral/bb-browser  (★6158, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=124

### README (head)
```
<div align="center">

# bb-browser

### BadBoy Browser

**Your browser is the API. No keys. No bots. No scrapers.**

[![npm](https://img.shields.io/npm/v/bb-browser?color=CB3837&logo=npm&logoColor=white)](https://www.npmjs.com/package/bb-browser)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?logo=node.js&logoColor=white)](https://nodejs.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[English](README.md) · [中文](README.zh-CN.md)

</div>

---

You're already logged into Twitter, Reddit, YouTube, Zhihu, Bilibili, LinkedIn, GitHub — bb-browser lets AI agents **use that directly**.

```bash
bb-browser site twitter/search "AI agent"       # search tweets
bb-browser site zhihu/hot                        # trending on Zhihu
bb-browser site arxiv/search "transformer"       # search papers
bb-browser site eastmoney/stock "茅台"            # real-time stock quote
bb-browser site boss/search "AI engineer"        # search jobs
bb-browser site wikipedia/summary "Python"       # Wikipedia summary
bb-browser site youtube/transcript VIDEO_ID      # full transcript
bb-browser site stackoverflow/search "async"     # search SO questions
```

**103 commands across 36 platforms.** All using your real browser's login state. [Full list →](https://github.com/epiral/bb-sites)

## The idea

The internet was built for browsers. AI agents have been trying to access it through APIs — but 99% of websites don't offer one.

bb-browser flips this: **instead of forcing websites to provide machine interfaces, let machines use the human interface directly.** The adapter runs `eval` inside your browser tab, calls `fetch()` with your cookies, or invokes the page's own webpack modules. The website thinks it's you. Because it **is** you.

| | Playwright / Selenium | Scraping libs | bb-browser |
|---|---|---|---|
| Browser | Headless, isolated | No browser | Your real Chrome |
| Login state | None, must re-login | Cookie extraction | Already there |
| Anti-bot | Detected easily | Cat-and-mouse | Invisible — it IS the user |
| Complex auth | Can't replicate | Reverse engineer | Page handles it itself |
```

---
## builderz-labs/mission-control  (★6146, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=1033

### README (head)
```
<div align="center">

# Mission Control

Self-hosted control plane for operating AI agents.

Dispatch tasks, inspect runs, review failures, track spend, and coordinate agent runtimes
from one local dashboard backed by SQLite.

An open-source project by [Builderz Labs](https://builderz.dev), created and maintained by [nyk](https://nyk.dev).
It works with OpenClaw, Claude Code, Codex, and other runtimes - it is not part of any one of them.

[![Quality Gate](https://github.com/builderz-labs/mission-control/actions/workflows/quality-gate.yml/badge.svg)](https://github.com/builderz-labs/mission-control/actions/workflows/quality-gate.yml)
[![Release](https://img.shields.io/github/v/release/builderz-labs/mission-control)](https://github.com/builderz-labs/mission-control/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Sponsor](https://img.shields.io/github/sponsors/builderz-labs?label=Sponsor)](https://github.com/sponsors/builderz-labs)

<img src="docs/mission-control-overview.png" alt="Mission Control overview dashboard with active sessions, live activity, fleet status per runtime, and the task pipeline" width="900">

</div>

> [!WARNING]
> Mission Control is alpha software. APIs, schemas, and configuration may change between
> releases. Read the [security guidance](#security-boundary) before exposing it to a network.

## Start locally

Node.js 22 or newer and pnpm are required for a source install.

```bash
git clone https://github.com/builderz-labs/mission-control.git
cd mission-control
bash install.sh --local
```

Open `http://localhost:3000/setup`, create the first admin account, then copy the API key
from Settings if an agent or script needs headless access.

The manual path is useful when you already manage Node and pnpm:

```bash
nvm use 22
pnpm install
pnpm dev
```
```

---
## PawanOsman/OpenCursor  (★6006, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=134

### README (head)
```
<div align="center">

<img src="media/readme/hero.png" alt="OpenCursor — the open-source AI coding agent for VS Code" width="900"/>

<br/>

**The open-source AI coding agent for VS Code — built local-first.**

Chat with an agent that reads your workspace, edits files, runs commands, and searches your codebase semantically. Use your Claude / ChatGPT / Gemini subscription, any API key, or run **completely offline** with llama.cpp and Ollama.

[Install](#installation) · [Local AI](#-100-local-ai) · [Providers](#-providers) · [Features](#-what-it-does) · [Contributing](#contributing)

</div>

---

## 🔌 100% Local AI

<img src="media/readme/local-stack.png" alt="OpenCursor local stack: llama.cpp, Ollama, local embeddings — works offline" width="900"/>

OpenCursor is designed to work **without internet** once set up:

- **🦙 llama.cpp built in** — search Hugging Face for GGUF models, pick a quantization, download, and OpenCursor spawns and manages `llama-server` for you. Full launch control: context size, GPU layers, flash attention, KV cache types, speculative decoding, vision (`--mmproj`), and more.
- **🐋 Ollama** — pull, manage, and chat with models from the Ollama library, zero config.
- **🧠 Local embeddings** — semantic codebase search powered by an on-device ONNX MiniLM model. No embedding API, no key, no code leaving your machine.
- **✈️ Airplane-mode coding** — local model + local index = a fully working AI agent, offline.

## 🔍 Semantic search, no cloud

<img src="media/readme/semantic-search.png" alt="Local semantic search pipeline" width="900"/>

Ask questions in plain language — *"where do we refresh the auth token?"* — and the agent automatically finds code by *meaning*, not keywords. The index builds automatically, updates incrementally, and is stored locally. Prefer a hosted embedding model? Point it at any OpenAI-compatible `/embeddings` endpoint instead.

## 🌐 Providers

<img src="media/readme/providers.png" alt="Supported providers: OAuth sign-in and API/local providers" width="900"/>

- **OAuth sign-in** — connect your existing **Claude Code**, **OpenAI Codex**, or **Google Antigravity** account and use your subscription's models directly in VS Code.
- **API keys** — OpenAI, Anthropic, Gemini, OpenRouter presets out of the box.
- **Custom providers** — add any OpenAI-compatible or Anthropic-style endpoint (base URL + key). Run multiple providers at once; models are fetched live and mixable in the picker.
- **Auto mode** — a judge model routes each task to the best enabled model. Per-model reasoning effort, thinking mode, and context-size options.

## ⚡ What it does

| | |
```

---
## netease-youdao/LobsterAI  (★5965, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=2567

### README (head)
```
<h1 align="center">
  <img src="public/logo.png" alt="LobsterAI" width="96"><br>
  LobsterAI
</h1>

<p align="center">
  <a href="https://github.com/netease-youdao/LobsterAI/stargazers"><img src="https://badgen.net/github/stars/netease-youdao/LobsterAI?label=%E2%98%85" alt="GitHub stars" /></a>
  <a href="LICENSE"><img src="https://badgen.net/github/license/netease-youdao/LobsterAI" alt="License" /></a>
  <a href="https://x.com/LobsterAIYoudao"><img src="https://img.shields.io/badge/-000000?logo=x&logoColor=white" alt="Follow LobsterAI on X" /></a>
  <a href="https://shared.ydstatic.com/market/souti/fihserChatWeb/online/2.0.7/dist/assets/wechat_group-B34qRm1G.png"><img src="https://img.shields.io/badge/-000000?logo=wechat&logoColor=white" alt="Follow LobsterAI on X" /></a>
  <br>
  <img src="https://img.shields.io/badge/macOS%20%7C%20Windows-4493F8?style=flat-square" alt="Supported platforms: macOS and Windows" />
  <img src="https://img.shields.io/badge/Electron-40-47848F?style=flat-square&logo=electron&logoColor=white" alt="Electron 40" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React 18" />
</p>

<p align="center">
  English · <a href="README_zh.md">中文</a>
</p>

<p align="center">
  <strong>All-scenario office assistant Agent.</strong><br/>
  The first open-source desktop-grade Agent among major Chinese tech companies, built by NetEase Youdao.
</p>

<p align="center">
  <a href="#features"><strong>Features</strong></a>
  &nbsp;·&nbsp;
  <a href="#developing"><strong>Developing</strong></a>
  &nbsp;·&nbsp;
  <a href="#community--support"><strong>Community</strong></a>
</p>

<h3 align="center"><a href="https://lobsterai.youdao.com/#/download-list"><ins>Download LobsterAI</ins></a></h3>

<p align="center">
  <img src="docs/res/mainpage_en.png" alt="main page" />
</p>

LobsterAI is a desktop Agent that can operate in your real working environment: local files, terminal commands, browser workflows, documents, spreadsheets, slides, IM channels, scheduled jobs, and project workspaces.

Cowork is the LobsterAI product/session layer. OpenClaw is the runtime and gateway underneath it. That split lets LobsterAI keep local persistence, permissions, UI state, artifacts, agents, memory, and IM bindings in the desktop app while using OpenClaw for agent execution.

## Features

```

---
## browser-act/skills  (★5529, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=485

### README (head)
```
<div align="center">
  <a href="https://www.browseract.com/?co-from=github" style="text-decoration: none;">
    <img src="https://browseract-prod.browseract.com/prod/tools/20260205-154549.png" alt="BrowserAct Logo" width="220">
  </a>
  <br><br>
  <p>
    <a href="https://discord.com/invite/UpnCKd7GaU"><img src="https://img.shields.io/discord/1234567890?label=Discord&logo=discord&color=7289DA" alt="Discord"></a>
    <a href="https://github.com/browser-act/skills/stargazers"><img src="https://img.shields.io/github/stars/browser-act/skills?style=social" alt="GitHub Stars"></a>
    <a href="https://github.com/browser-act/skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
    <br><br>
    <a href="https://www.browseract.com/?co-from=github"><img src="https://img.shields.io/badge/Website-BrowserAct.com-success" alt="Website"></a>
    <a href="https://x.com/browseract"><img src="https://img.shields.io/badge/X-browseract-000000?style=flat&logo=x&logoColor=white" alt="X (Twitter)"></a>
    <a href="https://www.linkedin.com/company/browseract/"><img src="https://img.shields.io/badge/LinkedIn-BrowserAct-0A66C2?style=flat&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
    <a href="https://www.youtube.com/@browseract"><img src="https://img.shields.io/badge/YouTube-@browseract-FF0000?style=flat&logo=youtube&logoColor=white" alt="YouTube"></a>
  </p>
</div>

---

## What can BrowserAct be used for?

BrowserAct enables AI agents and teams to perform real-browser automation, web data extraction, and account-based workflows.

It helps agents get past anti-bot walls, hand off to humans across platforms when stuck, run parallel tasks without cross-contamination, and isolate multiple accounts in independent browsers, backed by stealth fingerprints, TLS rotation, residential proxies, CAPTCHA solving, and stable fingerprint-proxy setups for authenticated sessions.

Two usage modes are available: fully cloud-managed execution, or local browser control driven by your own agent workflow.

### Use [BrowserAct](https://www.browseract.com/?co-from=github) in the cloud

**No agent setup required, with lower operating cost.** Describe the website, filters, and fields you need. BrowserAct builds and tests a reusable scraping Bot in a real cloud browser, then runs it from the cloud. **Build once. Run reliably. Improve continuously.**

<a href="https://www.browseract.com/?co-from=github">
  <img src="assets/readme/browseract-cloud-lower-cost-demo.png" alt="BrowserAct Cloud extracts data from any website with one prompt at a lower cost per run">
</a>

[Start from BrowserAct Cloud →](https://www.browseract.com/?co-from=github)

**Watch demo:** [Build a Web Scraper from One Prompt | BrowserAct →](https://www.youtube.com/watch?v=1M11lfNW7rE)

### Use BrowserAct locally with Skills

Use BrowserAct Skills when you want local browser control, local Chrome login-state reuse, or direct integration into your own AI agent workflow.

Your agent can load the BrowserAct Skill, discover browser state with `get-skills`, and run browser automation commands directly from your local environment.

```

---
## cloudflare/agents  (★5502, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['agent-think', 'AGENTS.md'] | tree=2937

### README (head)
```
# Cloudflare Agents

[![npm version](https://img.shields.io/npm/v/agents)](https://www.npmjs.com/package/agents)
[![npm downloads](https://img.shields.io/npm/dw/agents)](https://www.npmjs.com/package/agents)

![npm install agents](assets/npm-install-agents.svg)

Agents are persistent, stateful execution environments for agentic workloads, powered by Cloudflare [Durable Objects](https://developers.cloudflare.com/durable-objects/). Each agent has its own state, storage, and lifecycle — with built-in support for real-time communication, scheduling, AI model calls, MCP, workflows, and more.

Agents hibernate when idle and wake on demand. You can run millions of them — one per user, per session, per game room — each costs nothing when inactive.

```sh
npm create cloudflare@latest -- --template cloudflare/agents-starter
```

Or add to an existing project:

```sh
npm install agents
```

**[Read the docs](https://developers.cloudflare.com/agents/)** — getting started, API reference, guides, and more.

## Quick Example

A counter agent with persistent state, callable methods, and real-time sync to a React frontend:

```typescript
// server.ts
import { Agent, routeAgentRequest, callable } from "agents";

export type CounterState = { count: number };

export class CounterAgent extends Agent<Env, CounterState> {
  initialState = { count: 0 };

  @callable()
  increment() {
    this.setState({ count: this.state.count + 1 });
    return this.state.count;
  }

  @callable()
  decrement() {
    this.setState({ count: this.state.count - 1 });
```

---
## campfirein/byterover-cli  (★4954, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=2673

### README (head)
```
# ByteRover CLI

<div align="center">

<img src="./assets/images/logo/byterover-logo.svg" alt="ByteRover Logo" width="280" />

<p align="center">
<em>Interactive REPL CLI for AI-powered context memory</em>
</p>

<p align="center">
<a href="LICENSE"><img src="https://img.shields.io/badge/License-Elastic%202.0-blue.svg" alt="License" /></a>
<a href="https://npmjs.org/package/byterover-cli"><img src="https://img.shields.io/npm/v/byterover-cli.svg" alt="Version" /></a>
<a href="https://npmjs.org/package/byterover-cli"><img src="https://img.shields.io/npm/dw/byterover-cli.svg" alt="Downloads" /></a>
<a href="https://docs.byterover.dev"><img src="https://img.shields.io/badge/Docs-Documentation-green.svg" alt="Documentation" /></a>
<a href="https://discord.com/invite/UMRrpNjh5W"><img src="https://img.shields.io/badge/Discord-Join%20Community-7289da" alt="Discord" /></a>
</p>

</div>

## Overview

ByteRover CLI (`brv`) gives AI coding agents persistent, structured memory. It lets developers curate project knowledge into a context tree, sync it to the cloud, and share it across tools and teammates.

Run `brv` in any project directory to start an interactive REPL powered by your choice of LLM. The agent understands your codebase through an agentic map, can read and write files, execute code, and store knowledge for future sessions.

📄 Read the [paper](https://arxiv.org/abs/2604.01599) for the full technical details.

Or download our self-hosted PDF version of the paper [here](https://byterover.dev/paper).

**Key Features:**

- 🌐 Web dashboard for curating and querying context (`brv webui`)
- 🖥️ Interactive TUI with REPL interface (React/Ink)
- 🧠 Context tree and knowledge storage management
- 🔀 Git-like version control for the context tree (branch, commit, merge, push/pull)
- 🤖 20 LLM providers (Anthropic, OpenAI, Google, Groq, Mistral, xAI, DeepSeek, and more)
- 🛠️ 24 built-in agent tools (code exec, file ops, knowledge search, memory management)
- 🔄 Cloud sync with push/pull
- 👀 Review workflow for curate operations (approve/reject pending changes)
- 🔌 MCP (Model Context Protocol) integration
- 📦 Hub and connectors ecosystem for skills and bundles
- 🤝 Works with 22+ AI coding agents (Cursor, Claude Code, Windsurf, Cline, and more)
- 🏢 Enterprise proxy support

```

---
## alchaincyf/hermes-agent-orange-book  (★4892, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['Hermes-Agent-The-Complete-Guide-v260607.pdf', 'Hermes-Agent橙皮书2.0-v260607.pdf'] | tree=17

### README (head)
```
**English** | [中文版 README](README_zh.md)

<p align="center">
  <img src="assets/hero.gif" alt="hermes-agent-orange-book Hero Animation" />
  <br/>
  <sub>Animated with <a href="https://github.com/alchaincyf/huashu-design">huashu-design</a> skill</sub>
</p>

# Hermes Agent 2.0: The Complete Guide

> 橙皮书 (Orange Book) Series · by HuaShu (花叔)

A hands-on guide to [Hermes Agent](https://github.com/NousResearch/hermes-agent), the open-source AI Agent framework by [Nous Research](https://hermes-agent.nousresearch.com/) — the first agent that ships with its "reins" built in, and the reins grow themselves.

**This is a from-scratch rewrite.** The first edition was based on Hermes v0.7.0. Two months and nine releases later, the product had grown a whole new face — a native desktop app, a full browser dashboard, 23 messaging platforms — so the book is rebuilt around v0.16.0 ("The Surface Release").

<p align="center">
  <img src="screenshots/page-cover.png" width="45%" />
  <img src="screenshots/page-toc.png" width="45%" />
</p>

## Download

| Version | PDF |
|---------|-----|
| 中文版 (Chinese) | **[PDF Download](https://github.com/alchaincyf/hermes-agent-orange-book/raw/main/Hermes-Agent橙皮书2.0-v260607.pdf)** |
| English | **[PDF Download](https://github.com/alchaincyf/hermes-agent-orange-book/raw/main/Hermes-Agent-The-Complete-Guide-v260607.pdf)** |

## Errata

**The data-collection inference in §03 ("Why Nous Built It") is wrong.** Thanks to [@lishaogang](https://github.com/lishaogang) for pointing this out in [issue #7](https://github.com/alchaincyf/hermes-agent-orange-book/issues/7).

Under "Motive one," the book claims that "Hermes Agent isn't just a product, it's also a massive-scale harvester that collects real-world data for Nous's own models," and draws a chain from "users' real usage → tool-call trajectories → compressed into training data → next-gen models." That chain breaks at its very first link:

- The official [FAQ](https://hermes-agent.nousresearch.com/docs/reference/faq) states plainly: API calls go only to the LLM provider you configure; Hermes Agent does not collect telemetry, usage data, or analytics; your conversations, memory, and skills are stored locally in `~/.hermes/`.
- The official [AGENTS.md](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md) goes further, listing "outbound telemetry / usage attribution without opt-in gating" as a contribution that gets "rejected even when well-built" — code that would report data home is refused by the project itself.

In other words, your usage trajectories stay on your own machine; there is no channel feeding them back to Nous. The things the book cites — batch_runner.py, trajectory_compressor.py, the "Research-ready" section — are all real, but they are research infrastructure for Nous and researchers to batch-generate trajectories in their own environments, not a pipeline collecting data from users. I stretched "they have trajectory-generating infrastructure" into "they are harvesting your trajectories," and that step went too far. The original text did flag it as "my inference, not an official Nous statement" — but an inference directly contradicted by the official docs is still wrong, flag or no flag.

Accordingly, the "data flywheel" argument at the end of §03 doesn't hold either. Of the motives the book attributes to Nous, "monetizing through Portal" and "poaching OpenClaw's users" still stand; "users feeding it training data" should be struck.

The PDFs are build artifacts and have not been regenerated yet; this erratum stands here until the next revision corrects the body text. For product facts, trust the [official docs](https://hermes-agent.nousresearch.com/docs/).

## What This Book Covers

```

---
## eastlondoner/vibe-tools  (★4828, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=280

### README (head)
```
<div align="center">
  <img height="72" src="https://github.com/user-attachments/assets/45eff178-242f-4d84-863e-247b080cc6f5" />
</div>

<div align=center><h1>Give AI Agents an AI team and advanced skills</h1></div>


| Summary | Prompt it |
|---------|-----------|
| Essential information to understand what vibe-tools is and how to get started using it | [![](https://b.lmpify.com/getting_started)](https://lmpify.com?q=https%3A%2F%2Fuuithub.com%2Feastlondoner%2Fcursor-tools%2Ftree%2Fmain%3FpathPatterns%3DREADME.md%26pathPatterns%3DCONFIGURATION.md%26pathPatterns%3Dpackage.json%26pathPatterns%3Dvibe-tools.config.json%26pathPatterns%3D.cursor-tools.env.example%26pathPatterns%3Dsrc%252Fvibe-rules.ts%0A%0AI'm%20new%20to%20vibe-tools.%20Can%20you%20explain%20what%20it%20is%2C%20how%20to%20install%20it%2C%20and%20how%20to%20get%20started%20with%20basic%20commands%3F) |
| Overview of available commands and their basic functionality | [![](https://b.lmpify.com/command_overview)](https://lmpify.com?q=https%3A%2F%2Fuuithub.com%2Feastlondoner%2Fcursor-tools%2Ftree%2Fmain%3FpathPatterns%3Dsrc%252Fcommands%252Findex.ts%26pathPatterns%3Dsrc%252Ftypes.ts%26pathPatterns%3Dsrc%252Fvibe-rules.ts%26pathPatterns%3DREADME.md%0A%0AWhat%20commands%20are%20available%20in%20vibe-tools%20and%20what%20does%20each%20one%20do%3F) |
| Browser automation commands and capabilities | [![](https://b.lmpify.com/browser_commands)](https://lmpify.com?q=https%3A%2F%2Fuuithub.com%2Feastlondoner%2Fcursor-tools%2Ftree%2Fmain%3FpathPatterns%3Dsrc%252Fcommands%252Fbrowser%252F**%252F*.ts%26pathPatterns%3Dtests%252Fcommands%252Fbrowser%252F*.html%26excludePathPatterns%3Dsrc%252Fcommands%252Fbrowser%252Fstagehand%252FstagehandScript.ts%0A%0AHow%20do%20I%20use%20the%20browser%20commands%20in%20vibe-tools%3F%20What%20browser%20automation%20capabilities%20are%20available%3F) |
| LLM provider integration and configuration | [![](https://b.lmpify.com/llm_integration)](https://lmpify.com?q=https%3A%2F%2Fuuithub.com%2Feastlondoner%2Fcursor-tools%2Ftree%2Fmain%3FpathPatterns%3Dsrc%252Futils%252Ftool-enabled-llm%252F**%26pathPatterns%3Dsrc%252Fproviders%252F**%26pathPatterns%3Dsrc%252Fllms%252F**%26pathPatterns%3D.cursor-tools.env.example%0A%0AHow%20do%20I%20configure%20different%20LLM%20providers%20with%20vibe-tools%3F%20What%20providers%20are%20supported%3F) |
| Model Context Protocol (MCP) commands and tools | [![](https://b.lmpify.com/mcp_commands)](https://lmpify.com?q=https%3A%2F%2Fuuithub.com%2Feastlondoner%2Fcursor-tools%2Ftree%2Fmain%3FpathPatterns%3Dsrc%252Fcommands%252Fmcp%252F**%252F*.ts%0A%0AHow%20do%20I%20use%20the%20MCP%20commands%20in%20vibe-tools%3F%20What%20is%20MCP%20and%20how%20does%20it%20work%3F) |
| Testing framework and capabilities | [![](https://b.lmpify.com/testing)](https://lmpify.com?q=https%3A%2F%2Fuuithub.com%2Feastlondoner%2Fcursor-tools%2Ftree%2Fmain%3FpathPatterns%3Dsrc%252Fcommands%252Ftest%252F**%252F*.ts%26pathPatterns%3Dtests%252Ffeature-behaviors%252F**%252F*.md%26pathPatterns%3DTESTING.md%0A%0AHow%20do%20I%20use%20the%20testing%20capabilities%20in%20vibe-tools%3F%20How%20can%20I%20create%20and%20run%20tests%3F) |
| Configuration options and customization | [![](https://b.lmpify.com/configuration)](https://lmpify.com?q=https%3A%2F%2Fuuithub.com%2Feastlondoner%2Fcursor-tools%2Ftree%2Fmain%3FpathPatterns%3Dsrc%252Fconfig.ts%26pathPatterns%3Dvibe-tools.config.json%26pathPatterns%3D.cursor-tools.env.example%26pathPatterns%3DCONFIGURATION.md%26pathPatterns%3Dsrc%252Fvibe-rules.ts%0A%0AHow%20do%20I%20configure%20vibe-tools%3F%20What%20configuration%20options%20are%20available%3F) |
| Telemetry implementation and infrastructure | [![](https://b.lmpify.com/telemetry)](https://lmpify.com?q=https%3A%2F%2Fuuithub.com%2Feastlondoner%2Fcursor-tools%2Ftree%2Fmain%3FpathPatterns%3Dsrc%252Ftelemetry%252F**%26pathPatterns%3Dinfra%252F**%26pathPatterns%3DTELEMETRY.md%0A%0AHow%20does%20telemetry%20work%20in%20vibe-tools%3F%20What%20data%20is%20collected%20and%20how%20is%20it%20used%3F) |
| Example usage | [![](https://b.lmpify.com/examples)](https://lmpify.com?q=https%3A%2F%2Fuuithub.com%2Feastlondoner%2Fcursor-tools%2Ftree%2Fmain%3FpathPatterns%3Dsrc%252Fvibe-rules.ts%26pathPatterns%3DREADME.md%26pathPatterns%3DCONFIGURATION.md%0A%0ACan%20you%20show%20me%20some%20examples%20of%20how%20to%20use%20vibe-tools%20commands%20effectively%3F) |


## Table of Contents

- [The AI Team](#the-ai-team)
- [New Skills](#new-skills-for-your-existing-agent)
- [How to Use](#how-do-i-use-it)
  - [Example: Using Perplexity](#asking-perplexity-to-carry-out-web-research)
  - [Example: Using Gemini](#asking-gemini-for-a-plan)
- [What is vibe-tools](#what-is-vibe-tools)
- [Installation](#installation)
- [Requirements](#requirements)
- [Telemetry & Privacy](#telemetry--privacy)
- [Tips](#tips)
- [Additional Examples](#additional-examples)
  - [GitHub Skills](#github-skills)
  - [Gemini Code Review](#gemini-code-review)
- [Detailed Cursor Usage](#detailed-cursor-usage)
  - [Tool Recommendations](#tool-recommendations)
  - [Command Nicknames](#command-nicknames)
  - [Web Search](#use-web-search)
  - [Repository Search](#use-repo-search)
  - [Documentation Generation](#use-doc-generation)
  - [GitHub Integration](#use-github-integration)
  - [Browser Automation](#use-browser-automation)
  - [Direct Model Queries](#use-direct-model-queries)
- [Authentication and API Keys](#authentication-and-api-keys)
```

---
## breferrari/obsidian-mind  (★4580, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=287

### README (head)
```
🌐 **English** | [日本語](README.ja.md) | [中文](README.zh-CN.md) | [한국어](README.ko.md)

<p align="center">
  <img src="obsidian-mind-logo.png" alt="Obsidian Mind" width="120">
</p>

<h1 align="center">Obsidian Mind</h1>

[![Claude Code](https://img.shields.io/badge/claude%20code-full%20support-D97706)](https://docs.anthropic.com/en/docs/claude-code)
[![Codex CLI](https://img.shields.io/badge/codex%20cli-hooks%20%2B%20commands-10A37F)](https://github.com/openai/codex)
[![Gemini CLI](https://img.shields.io/badge/gemini%20cli-hooks%20%2B%20commands-4285F4)](https://github.com/google-gemini/gemini-cli)
[![Obsidian](https://img.shields.io/badge/obsidian-1.12%2B-7C3AED)](https://obsidian.md)
[![Obsidian CLI](https://img.shields.io/badge/obsidian--cli-integrated-E6E6E6)](https://github.com/kepano/obsidian-cli)
[![Obsidian Skills](https://img.shields.io/badge/obsidian--skills-integrated-8B5CF6)](https://github.com/kepano/obsidian-skills)
[![QMD](https://img.shields.io/badge/qmd-semantic%20search-FF6B6B)](https://github.com/tobi/qmd)
[![Node](https://img.shields.io/badge/node-22%2B-339933)](https://nodejs.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **An Obsidian vault that gives AI coding agents persistent memory.** Built for Claude Code, with working hooks for Codex CLI and Gemini CLI. Start a session, talk about your day, and the agent handles the rest — notes, links, indexes, performance tracking. Every conversation builds on the last.

---

## 🔴 The Problem

AI coding agents are powerful, but they forget. Every session starts from zero — no context on your goals, your team, your patterns, your wins. You re-explain the same things. You lose decisions made three conversations ago. The knowledge never compounds.

## 🟢 The Solution

Give your agent a brain.

```
You: "start session"
Agent: *reads North Star, checks active projects, scans recent memories*
Agent: "You're working on Project Alpha, blocked on the BE contract.
        Last session you decided to split the coordinator. Your 1:1
        with your manager is tomorrow — review brief is ready."
```

Works with **Claude Code** (full support), **Codex CLI**, and **Gemini CLI** — same hooks, same commands, same vault.

Install via `shardmind install` or `git clone` — same vault either way.

---

## ⚡ See It In Action
```

---
## dimensionalOS/dimos  (★4444, v2.i=MULTI)
frameworks: ['langchain', 'langgraph'] | agent-ish dirs: ['.agents', 'AGENTS.md'] | tree=2938

### README (head)
```
<div align="center">

<img width="1000" alt="banner_bordered_trimmed" src="https://github.com/user-attachments/assets/64f13b39-da06-4f58-add0-cfc44f04db4e" />

<h2>The Agentive Operating System for Physical Space</h2>

[![Discord](https://img.shields.io/discord/1341146487186391173?style=flat-square&logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/dimos)
[![Stars](https://img.shields.io/github/stars/dimensionalOS/dimos?style=flat-square)](https://github.com/dimensionalOS/dimos/stargazers)
[![Forks](https://img.shields.io/github/forks/dimensionalOS/dimos?style=flat-square)](https://github.com/dimensionalOS/dimos/fork)
[![Contributors](https://img.shields.io/github/contributors/dimensionalOS/dimos?style=flat-square)](https://github.com/dimensionalOS/dimos/graphs/contributors)
[![Docs](https://img.shields.io/badge/Docs-docs.dimensionalos.com-1682a3?style=flat-square&logo=readthedocs&logoColor=white)](https://docs.dimensionalos.com)
![Nix](https://img.shields.io/badge/Nix-flakes-5277C3?style=flat-square&logo=NixOS&logoColor=white)
![NixOS](https://img.shields.io/badge/NixOS-supported-5277C3?style=flat-square&logo=NixOS&logoColor=white)
![CUDA](https://img.shields.io/badge/CUDA-supported-76B900?style=flat-square&logo=nvidia&logoColor=white)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

<a href="https://trendshift.io/repositories/23169" target="_blank"><img src="https://trendshift.io/api/badge/repositories/23169" alt="dimensionalOS%2Fdimos | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

<big><big>

[Docs](https://docs.dimensionalos.com) •
[Hardware](#hardware) •
[Installation](#installation) •
[Agent CLI & MCP](#agent-cli-and-mcp) •
[Blueprints](#blueprints) •
[dimTELE: Remote Teleop](#dimtele-remote-teleop) •
[Development](#development)

⚠️ **Pre-Release Beta** ⚠️

</big></big>

</div>

# About

Dimensional is the modern operating system for generalist robotics. We are setting the next-generation SDK standard, integrating with the majority of robot manufacturers.

With a simple install and no ROS required, build physical applications entirely in python that run on any humanoid, quadruped, or drone.

Dimensional is agent native -- "vibecode" your robots in natural language and build (local & hosted) multi-agent systems that work seamlessly with your hardware. Agents run as native modules — subscribing to any embedded stream, from perception (lidar, camera) and spatial memory down to control loops and motor drivers.
<table>
  <tr>
    <td align="center" width="50%">
      <a href="docs/capabilities/navigation/index.md"><img src="assets/readme/navigation.gif" alt="Navigation" width="100%"></a>
```

---
## gptme/gptme  (★4403, v2.i=MULTI)
frameworks: ['langchain'] | agent-ish dirs: ['AGENTS.md'] | tree=1723

### README (head)
```
<p align="center">
  <img src="https://gptme.org/media/logo.png" width=150 />
</p>

<h1 align="center">gptme</h1>

<p align="center">
<i>/ʤiː piː tiː miː/</i>
<br>
<sub><a href="https://gptme.org/docs/misc/acronyms.html">what does it stand for?</a></sub>
</p>

<!-- Links -->
<p align="center">
  <a href="https://gptme.org/docs/getting-started.html">Getting Started</a>
  •
  <a href="https://gptme.org/downloads/">Downloads</a>
  •
  <a href="https://gptme.org/">Website</a>
  •
  <a href="https://gptme.org/docs/">Documentation</a>
</p>

<!-- Badges -->
<p align="center">
  <a href="https://github.com/gptme/gptme/actions/workflows/build.yml">
    <img src="https://github.com/gptme/gptme/actions/workflows/build.yml/badge.svg" alt="Build Status" />
  </a>
  <a href="https://github.com/gptme/gptme/actions/workflows/docs.yml">
    <img src="https://github.com/gptme/gptme/actions/workflows/docs.yml/badge.svg" alt="Docs Build Status" />
  </a>
  <a href="https://codecov.io/gh/gptme/gptme">
    <img src="https://codecov.io/gh/gptme/gptme/graph/badge.svg?token=DYAYJ8EF41" alt="Codecov" />
  </a>
  <br>
  <a href="https://pypi.org/project/gptme/">
    <img src="https://img.shields.io/pypi/v/gptme" alt="PyPI version" />
  </a>
  <a href="https://pepy.tech/project/gptme">
    <img src="https://img.shields.io/pepy/dt/gptme" alt="PyPI - Downloads all-time" />
  </a>
  <a href="https://pypistats.org/packages/gptme">
    <img src="https://img.shields.io/pypi/dd/gptme?color=success" alt="PyPI - Downloads per day" />
  </a>
  <br>
```

---
## BuilderIO/micro-agent  (★4329, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=106

### README (head)
```
<br>
<div align="center">
   <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://cdn.builder.io/api/v1/image/assets%2FYJIGb4i01jvw0SRdL5Bt%2F4d36bc052c4340f997dd61eb19c1c64b">
      <img width="400" alt="AI Shell logo" src="https://cdn.builder.io/api/v1/image/assets%2FYJIGb4i01jvw0SRdL5Bt%2F1a718d297d644fce90f33e93b7e4061f">
    </picture>
</div>

<p align="center">
   An AI agent that writes and fixes code for you.
</p>

<p align="center">
   <a href="https://www.npmjs.com/package/@builder.io/micro-agent"><img src="https://img.shields.io/npm/v/@builder.io/micro-agent" alt="Current version"></a>
</p>
<br>

![Demo](https://cdn.builder.io/api/v1/file/assets%2FYJIGb4i01jvw0SRdL5Bt%2F3306a1cff57b4be69df65492a72ae8e5)

# Micro Agent

Just run `micro-agent`, give it a prompt, and it'll generate a test and then iterate on code until all test cases pass.

## Why?

LLMs are great at giving you broken code, and it can take repeat iteration to get that code to work as expected.

So why do this manually when AI can handle not just the generation but also the iteration and fixing?

### Why a "micro" agent?

AI agents are cool, but general-purpose coding agents rarely work as hoped or promised. They tend to go haywire with compounding errors. Think of your Roomba getting stuck under a table, x1000.

The idea of a micro agent is to

1. Create a definitive test case that can give clear feedback if the code works as intended or not, and
2. Iterate on code until all test cases pass

Read more on [why Micro Agent exists](https://www.builder.io/blog/micro-agent).

<img width="1270" alt="Micro Agent Diagram" src="https://github.com/BuilderIO/micro-agent/assets/844291/406496dd-3be8-491b-a5f0-2960dd924013">

### What this project is not

This project is not trying to be an end-to-end developer. AI agents are not capable enough to reliably try to be that yet (or probably very soon). This project won't install modules, read and write multiple files, or do anything else that is highly likely to cause havoc when it inevitably fails.
```

---
## The-Swarm-Corporation/AutoHedge  (★4325, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=58

### README (head)
```
# AutoHedge

[![Join our Discord](https://img.shields.io/badge/Discord-Join%20our%20server-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/VapjxpSyHC3) [![Subscribe on YouTube](https://img.shields.io/badge/YouTube-Subscribe-red?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@kyegomez3242) [![Connect on LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/kye-g-38759a207/) [![Follow on X.com](https://img.shields.io/badge/X.com-Follow-1DA1F2?style=for-the-badge&logo=x&logoColor=white)](https://x.com/swarms_corp)


AutoHedge is an enterprise-grade autonomous agent hedge fund that trades on your behalf. It combines swarm intelligence and specialized AI agents to perform end-to-end market analysis, risk management, and execution with minimal human intervention.

**Current support:** Full autonomous trading on Solana. **Coming soon:** Coinbase and additional exchanges.

---

## Overview

AutoHedge is built to be the world's most powerful autonomous agent hedge fund. It runs continuous analysis, generates and validates trading theses, sizes risk, and executes orders across supported venues. The system is designed for institutional reliability: structured outputs, comprehensive logging, and a risk-first architecture that scales from single strategies to multi-venue, multi-asset deployment.

---

## Features

- **Multi-Agent Architecture**: Specialized agents for each stage of the trading pipeline
  - Director Agent: strategy and thesis generation
  - Quant Agent: technical and statistical analysis
  - Risk Management Agent: position sizing and risk assessment
  - Execution Agent: order generation and execution

- **Real-Time Market Analysis**: Integration with live market data for analysis and execution
- **Risk-First Design**: Built-in risk management and position sizing before any execution
- **Structured Output**: JSON-formatted recommendations and analysis for downstream systems
- **Enterprise Logging**: Detailed, configurable logging for audit and debugging
- **Extensible Framework**: Modular design for custom strategies and new venues

---

## Supported Venues

| Venue      | Status        | Notes                    |
|-----------|----------------|--------------------------|
| Solana    | Supported      | Full autonomous trading  |
| Coinbase  | Coming soon    | In development           |
| Other CEX | Roadmap        | Planned expansion        |

---

## Quick Start

```

---
## apache/maka  (★4272, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['.pr_agent.toml'] | tree=3526

### README (head)
```
<!--
  Licensed to the Apache Software Foundation (ASF) under one
  or more contributor license agreements.  See the NOTICE file
  distributed with this work for additional information
  regarding copyright ownership.  The ASF licenses this file
  to you under the Apache License, Version 2.0 (the
  "License"); you may not use this file except in compliance
  with the License.  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing,
  software distributed under the License is distributed on an
  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
  KIND, either express or implied.  See the License for the
  specific language governing permissions and limitations
  under the License.
-->

<h1 align="center">
  <img src="apps/desktop/assets/app-icons/sky.png" alt="Maka" width="72" valign="middle" /> Apache Maka (Incubating)
</h1>

<p align="center"><sub>Incubating at The Apache Software Foundation</sub></p>

<p align="center">
  <a href="https://github.com/apache/maka/stargazers"><img src="https://img.shields.io/github/stars/apache/maka?style=flat&label=%E2%98%85&color=4C8DFF" alt="GitHub stars" /></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-4C8DFF?style=flat" alt="License: Apache 2.0" /></a>
  <img src="https://img.shields.io/badge/macOS-arm64-4C8DFF?style=flat&logo=apple&logoColor=white" alt="macOS Apple Silicon" />
  <img src="https://img.shields.io/badge/Windows-preview-9BB8F0?style=flat&logo=windows&logoColor=white" alt="Windows unsigned preview" />
  <img src="https://img.shields.io/badge/Linux-soon-D0D4DA?style=flat&logo=linux&logoColor=6B7280" alt="Linux not yet supported" />
  <a href="https://deepwiki.com/apache/maka"><img src="https://img.shields.io/badge/DeepWiki-third--party%20AI%20docs-9BB8F0?style=flat" alt="DeepWiki: third-party AI-generated docs" /></a>
  <a href="./README.zh-CN.md"><img src="https://img.shields.io/badge/%E4%B8%AD%E6%96%87%E6%96%87%E6%A1%A3-4C8DFF?style=flat" alt="中文文档" /></a>
</p>

<p align="center">
  <strong>A local-first Agent workspace built for real work.</strong><br/>
  Maka inspects projects, runs tools under a sandbox boundary, and records
  model messages and tool calls as recoverable execution facts — on your
  machine, through one Runtime Host.
</p>

<p align="center">
  <a href="https://github.com/apache/maka/releases"><img src="https://img.shields.io/badge/Download%20Desktop%20Nightly-1F6FEB?style=for-the-badge" alt="Download Desktop Nightly" /></a><br/>
  Daily builds from <code>main</code> for developers and testers. Not an ASF release, not intended for production use.
```

---
## dmno-dev/varlock  (★4239, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=1677

### README (head)
```
<p align="center">
  <a href="https://varlock.dev" target="_blank" rel="noopener noreferrer">
    <img src="/packages/varlock-website/src/assets/logos/wordmark.png" alt="Varlock banner">
  </a>
</p>
<br/>
<p align="center">
  <a href="https://npmx.dev/package/varlock"><img src="https://img.shields.io/npm/v/varlock.svg" alt="npm package"></a>
  <a href="/LICENSE.md"><img src="https://img.shields.io/npm/l/varlock.svg" alt="license"></a>
  <a href="https://nodejs.org/en/about/previous-releases"><img src="https://img.shields.io/node/v/varlock.svg" alt="node compatibility"></a>
  <a href="https://github.com/dmno-dev/varlock/actions/workflows/test.yaml"><img src="https://img.shields.io/github/actions/workflow/status/dmno-dev/varlock/test.yaml?style=flat&logo=github&label=CI" alt="build status"></a>
  <a href="https://chat.dmno.dev"><img src="https://img.shields.io/badge/chat-discord-5865F2?style=flat&logo=discord" alt="discord chat"></a>
</p>
<br/>

## Varlock
> AI-safe .env files: Schemas for agents, Secrets for humans.

- 🤖 AI-safe config — agents read your schema, never your secrets
- 🔍 proactive leak scanning via `varlock scan` + git hooks
- 🔏 runtime protection — log redaction and leak prevention
- 🛡️ validation, coercion, type safety w/ IntelliSense
- 🌐 flexible multi-environment management — auto .env.* loading and explicit import
- 🔌 [plugins](https://varlock.dev/plugins/overview/) to pull data from various backends (1Password, Infisical, AWS, Azure, GCP, HCP Vault, more!)

Unlike .env.example, **your .env.schema is a single source of truth**, built for collaboration, that will never be out of sync.

```bash
# @defaultSensitive=false @defaultRequired=infer @currentEnv=$APP_ENV
# ---
# our environment flag, will control automatic loading of `.env.xxx` files
# @type=enum(development, preview, production, test)
APP_ENV=development # default value, can override

# @type=port
API_PORT=8080 # non-sensitive values can be set directly

# API url including _expansion_ referencing another env var
# @type=url
API_URL=http://localhost:${API_PORT}

# sensitive api key, with extra validation
# @required @sensitive @type=string(startsWith=sk-)
OPENAI_API_KEY=
```
```

---
## dataelement/Clawith  (★4137, v2.i=MULTI)
frameworks: ['langgraph'] | agent-ish dirs: ['AGENTS.md'] | tree=1026

### README (head)
```
<p align="center">
  <img src="assets/slogan.png" alt="Clawith — OpenClaw for Teams" width="800" />
</p>

<p align="center">
  <a href="https://www.clawith.ai/blog/clawith-technical-whitepaper"><img src="https://img.shields.io/badge/Technical%20Whitepaper-Read-8A2BE2" alt="Technical Whitepaper" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Apache 2.0 License" /></a>
  <a href="https://github.com/dataelement/Clawith/stargazers"><img src="https://img.shields.io/github/stars/dataelement/Clawith?style=flat&color=gold" alt="GitHub Stars" /></a>
  <a href="https://github.com/dataelement/Clawith/network/members"><img src="https://img.shields.io/github/forks/dataelement/Clawith?style=flat&color=slateblue" alt="GitHub Forks" /></a>
  <a href="https://github.com/dataelement/Clawith/commits/main"><img src="https://img.shields.io/github/last-commit/dataelement/Clawith?style=flat&color=green" alt="Last Commit" /></a>
  <a href="https://github.com/dataelement/Clawith/graphs/contributors"><img src="https://img.shields.io/github/contributors/dataelement/Clawith?style=flat&color=orange" alt="Contributors" /></a>
  <a href="https://github.com/dataelement/Clawith/issues"><img src="https://img.shields.io/github/issues/dataelement/Clawith?style=flat" alt="Issues" /></a>
  <a href="https://x.com/ClawithHQ"><img src="https://img.shields.io/badge/𝕏-Follow-000000?logo=x&logoColor=white" alt="Follow on X" /></a>
  <a href="https://discord.gg/NRNHZkyDcG"><img src="https://img.shields.io/badge/Discord-Join%20Us-5865F2?logo=discord&logoColor=white" alt="Discord" /></a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README_zh-CN.md">中文</a> ·
  <a href="README_ja.md">日本語</a> ·
  <a href="README_ko.md">한국어</a> ·
  <a href="README_es.md">Español</a> ·
  <a href="README_ar.md">العربية</a>
</p>

<p align="center">
  <strong>Live Demo:</strong> <a href="https://try.clawith.ai">try.clawith.ai</a>
  — open-source feature preview; shared demo environment, not guaranteed stable.
  <br />
  <strong>Clawith Cloud:</strong> <a href="https://cloud.clawith.ai">cloud.clawith.ai</a>
  — hosted production service.
</p>

---

Clawith is an open-source multi-agent collaboration platform. Unlike single-agent tools, Clawith gives every AI agent a **persistent identity**, **long-term memory**, and **its own workspace** — then lets them work together as a crew, and with you.

## 🌟 What Makes Clawith Different

### 🧠 Aware — Adaptive Autonomous Consciousness
Aware is the agent's autonomous awareness system. Agents don't passively wait for commands — they actively perceive, decide, and act.

- **Focus Items** — Agents maintain a structured working memory of what they're currently tracking, with status markers (`[ ]` pending, `[/]` in progress, `[x]` completed).
- **Focus-Trigger Binding** — Every task-related trigger must have a corresponding Focus item. Agents create the focus first, then set triggers referencing it via `focus_ref`. When a focus is completed, the agent cancels its triggers.
- **Self-Adaptive Triggering** — Agents don't just execute pre-set schedules — they dynamically create, adjust, and remove their own triggers as tasks evolve. The human assigns the goal; the agent manages the schedule.
```

---
## Paper2Poster/Paper2Poster  (★3928, v2.i=MULTI)
frameworks: ['autogen/ag2', 'camel', 'langchain'] | agent-ish dirs: ['PosterAgent'] | tree=2070

### README (head)
```
# 🎓Paper2Poster: Multimodal Poster Automation from Scientific Papers
# 从学术论文自动生成学术海报

<p align="center">
  <a href="https://arxiv.org/abs/2505.21497" target="_blank"><img src="https://img.shields.io/badge/arXiv-2505.21497-red"></a>
  <a href="https://paper2poster.github.io/" target="_blank"><img src="https://img.shields.io/badge/Project-Page-brightgreen"></a>
  <a href="https://huggingface.co/datasets/Paper2Poster/Paper2Poster" target="_blank"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Dataset-orange"></a>
  <a href="https://huggingface.co/papers/2505.21497" target="_blank"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Daily Papers-red"></a>
  <a href="https://x.com/_akhaliq/status/1927721150584390129" target="_blank"><img alt="X (formerly Twitter) URL" src="https://img.shields.io/twitter/url?url=https%3A%2F%2Fx.com%2F_akhaliq%2Fstatus%2F1927721150584390129"></a>
  <a href="https://huggingface.co/spaces/camel-ai/Paper2Poster" target="_blank"> <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces%20Demo-blue"> </a>
</p>

We address **How to create a poster from a paper** and **How to evaluate poster.**

![Overview](./assets/overall.png)


## 🤩 Paper2Poster for Paper2Poster

![Overview](./assets/teaser.jpeg)

## 🔥 Update
- [x] [2026.6.6] We introduce lightweight [Paper2Poster SKILL](https://github.com/Paper2Poster/Paper2Poster/tree/main/skills).
- [x] [2025.10.7] Check out follow-up **[Paper2Video](https://github.com/showlab/Paper2Video)**.
- [x] [2025.11.3] Added **Gradio demo** support.
- [x] [2025.10.18] Added **Docker** support.
- [x] [2025.10.13] Added automatic **logo support** for conferences and institutions, **YAML-based style customization**, a new default theme.
- [x] [2025.9.18] Paper2Poster has been accepted to **NeurIPS 2025 Dataset and Benchmark Track**.
- [x] [2025.9.3]  We now support generate per section content in **parallel** for faster generation, by simply specifying `--max_workers`.
- [x] [2025.5.27] We release the [arXiv](https://arxiv.org/abs/2505.21497), [code](https://github.com/Paper2Poster/Paper2Poster) and [`dataset`](https://huggingface.co/datasets/Paper2Poster/Paper2Poster)

<!--## 📚 Introduction-->

**PosterAgent** is a top-down, visual-in-the-loop multi-agent system from `paper.pdf` to **editable** `poster.pptx`.

![PosterAgent Overview](./assets/posteragent.png)

<!--A Top-down, visual-in-the-loop, efficient multi-agent pipeline, which includes (a) Parser distills the paper into a structured asset library; the (b) Planner aligns text–visual pairs into a binary‐tree layout that preserves reading order and spatial balance; and the (c) Painter-Commentor loop refines each panel by executing rendering code and using VLM feedback to eliminate overflow and ensure alignment.-->

<!--![Paper2Poster Overview](./assets/paperquiz.png)-->

<!--**Paper2Poster:** A benchmark for paper to poster generation, paired with human generated poster, with a comprehensive evaluation suite, including metrics like **Visual Quality**, **Textual Coherence**, **VLM-as-Judge** and **PaperQuiz**. Notably, PaperQuiz is a novel evaluation which assume A Good poster should convey core paper content visually.-->

## 📋 Table of Contents

```

---
## LazyAGI/LazyLLM  (★3879, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=1421

### README (head)
```
<div align="center">
  <img src="https://raw.githubusercontent.com/LazyAGI/LazyLLM/main/docs/assets/LazyLLM-logo.png" width="100%"/>
</div>

# LazyLLM: A  Low-code Development Tool For Building Multi-agent LLMs Applications.
[中文](README.CN.md) |  [EN](README.md)

[![CI](https://github.com/LazyAGI/LazyLLM/actions/workflows/main.yml/badge.svg)](https://github.com/LazyAGI/LazyLLM/actions/workflows/main.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-yellow.svg)](https://opensource.org/license/apache-2-0)
[![GitHub star chart](https://img.shields.io/github/stars/LazyAGI/LazyLLM?style=flat-square)](https://star-history.com/#LazyAGI/LazyLLM)
[![](https://dcbadge.vercel.app/api/server/cDSrRycuM6?compact=true&style=flat)](https://discord.gg/cDSrRycuM6)

## What is LazyLLM?

LazyLLM is a low-code development tool for building **multi-agent** large language model applications. It assists developers in creating complex AI applications at very low costs and enables continuous iterative optimization. LazyLLM offers a convenient workflow for application building and provides numerous standard processes and tools for various stages of the application development process.<br>
The AI application development process based on LazyLLM follows **prototype building -> data feedback -> iterative optimization**, which means you can quickly build a prototype application using LazyLLM, then analyze bad cases using task-specific data, and subsequently iterate on algorithms and fine-tune models at critical stages of the application to gradually improve the overall application performance.<br>
LazyLLM is committed to the unity of agility and efficiency. Developers can efficiently iterate algorithms and then apply the iterated algorithms to industrial production, supporting multiple users, fault tolerance, and high concurrency.
**User Documentation**： https://docs.lazyllm.ai/ <br>
Scan the QR code below with WeChat to join the group chat(left) or learn more by watching a video(right)<br>
<p align="center">
<img src="https://github.com/user-attachments/assets/8ad8fd14-b218-48b3-80a4-7334b2a32c5a" width=250/>
<img src="https://github.com/user-attachments/assets/7a042a97-1339-459e-a451-4bcd6cf64c12" width=250/>
</p>


## Features

**Convenient AI Application Assembly Process**: Even if you are not familiar with large models, you can still easily assemble AI applications with multiple agents using our built-in data flow and functional modules, just like Lego building.

**One-Click Deployment of Complex Applications**: We offer the capability to deploy all modules with a single click. Specifically, during the POC (Proof of Concept) phase, LazyLLM simplifies the deployment process of multi-agent applications through a lightweight gateway mechanism, solving the problem of sequentially starting each submodule service (such as LLM, Embedding, etc.) and configuring URLs, making the entire process smoother and more efficient. In the application release phase, LazyLLM provides the ability to package images with one click, making it easy to utilize Kubernetes' gateway, load balancing, and fault tolerance capabilities.

**Cross-Platform Compatibility**: Switch IaaS platforms with one click without modifying code, compatible with bare-metal servers, development machines, Slurm clusters, public clouds, etc. This allows developed applications to be seamlessly migrated to other IaaS platforms, greatly reducing the workload of code modification.<br>

**Unified User Experience for Different Technical Choices**: We provide a unified user experience for online models from different service providers and locally deployed models, allowing developers to freely switch and upgrade their models for experimentation. In addition, we also unify the user experience for mainstream inference frameworks, fine-tuning frameworks, relational databases, vector databases, and document databases.<br>

**Efficient Model Fine-Tuning**: Support fine-tuning models within applications to continuously improve application performance. Automatically select the best fine-tuning framework and model splitting strategy based on the fine-tuning scenario. This not only simplifies the maintenance of model iterations but also allows algorithm researchers to focus more on algorithm and data iteration, without handling tedious engineering tasks.<br>


## What can you build with Lazyllm

LazyLLM can be used to build common artificial intelligence applications. Here are some examples.

### 3.1 ChatBots

**This is a simple example of a chat bot.**
```

---
## EverMind-AI/Raven  (★3702, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=1694

### README (head)
```
<div align="center" id="readme-top">

![Raven banner](https://github.com/user-attachments/assets/d56804e5-5d4b-4493-bc70-71bd38833806)

<p align="center"><strong>Coming next:</strong> The Harness of Harnesses is Raven's next-version direction, not a capability of the current public release.</p>

<p align="center">
  <a href="https://x.com/evermind"><img src="https://img.shields.io/badge/EverMind-000000?labelColor=gray&style=for-the-badge&logo=x&logoColor=white" alt="X"></a>
  <a href="https://huggingface.co/EverMind-AI"><img src="https://img.shields.io/badge/HuggingFace-EverMind-F5C842?labelColor=gray&style=for-the-badge&logo=huggingface&logoColor=white" alt="Hugging Face"></a>
  <a href="https://discord.gg/gYep5nQRZJ"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fdiscord.com%2Fapi%2Fv10%2Finvites%2FgYep5nQRZJ%3Fwith_counts%3Dtrue&query=%24.approximate_presence_count&suffix=%20online&label=Discord&color=404EED&labelColor=gray&style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/EverMind-AI/EverOS/discussions/67"><img src="https://img.shields.io/badge/WeCom-EverMind_Community-07C160?labelColor=gray&style=for-the-badge&logo=wechat&logoColor=white" alt="WeCom"></a>
</p>

[Website](https://raven.evermind.ai) · [中文](README.zh-CN.md)

</div>

<br>

# Raven

The current public release of Raven is the open-source, **self-improving Agent Harness** you can run today. It brings terminal-first execution, local tracing, long-term memory, skills, evaluation, and reusable workflows into one system for long-running AI work.

## Coming Next: The Harness of Harnesses

As AI agents move from narrow tasks toward long-running, cross-domain work, manually designing a single, ever-larger harness stops scaling. A harness optimized for one model or domain also cannot provide every capability needed for general intelligence.

Raven's next version will move toward **The Harness of Harnesses**: a continuously evolving multi-agent ecosystem built for autonomous collaboration and open co-creation. It is designed to build and improve Agent Harnesses for specific models and domains, then compose their heterogeneous execution capabilities into an **All-Domain Collaboration Network**.

| **Trusted** | **Persistent** | **Evolving** |
| --- | --- | --- |
| Harness capabilities will be scored based on verified performance, not self-declared labels. | The network is designed to carry verified results, task state, and long-term memory across executors. | Each verified run will feed experience back into capability profiles, skills, routing, and the wider network. |

This next-version architecture is designed to move beyond fixed model-harness pairs. Through a continuous **evaluation -> execution -> verification -> memory -> feedback** loop, it will discover, compose, and improve the right capabilities for each task. Validated work will become reusable experience, allowing both individual agents and the wider capability network to evolve.

The internal research prototype behind this direction has been evaluated across **22 Agent benchmark tasks** covering task performance, cost, and key mechanism gains. The reported results show comprehensive performance and efficiency improvements over existing agent systems while advancing the **quality-cost Pareto frontier**.

> The current public Raven release does not yet implement The Harness of Harnesses. Raven today is the runnable self-improving Agent Harness described in this repository; the section above describes the next version we are building toward.

> Raven is pre-alpha. Interfaces and configuration may change quickly.

## Next-Version Research Benchmarks

| Benchmark | Research Prototype Result | Comparison |
| --- | --- | --- |
```

---
## ANative-Lab/EvoAgentX  (★3280, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['evoagentx', 'EvoAgentX_Weekly_Meeting.ics'] | tree=686

### README (head)
```
<!-- Add logo here -->
<div align="center">
  <a href="https://github.com/EvoAgentX/EvoAgentX">
    <img src="./assets/EAXLoGo.svg" alt="EvoAgentX" width="50%">
  </a>
</div>

<h2 align="center">
    Building a Self-Evolving Ecosystem of AI Agents
</h2>

<div align="center">

[![EvoAgentX Homepage](https://img.shields.io/badge/EvoAgentX-Homepage-blue?logo=homebridge)](https://evoagentx.org/)
[![Docs](https://img.shields.io/badge/-Documentation-0A66C2?logo=readthedocs&logoColor=white&color=7289DA&labelColor=grey)](https://EvoAgentX.github.io/EvoAgentX/)
[![Discord](https://img.shields.io/badge/Chat-Discord-5865F2?&logo=discord&logoColor=white)](https://discord.gg/XWBZUJFwKe)
[![Twitter](https://img.shields.io/badge/Follow-@EvoAgentX-e3dee5?&logo=x&logoColor=white)](https://x.com/EvoAgentX)
[![Wechat](https://img.shields.io/badge/WeChat-EvoAgentX-brightgreen?logo=wechat&logoColor=white)](./assets/wechat_info.md)
[![GitHub star chart](https://img.shields.io/github/stars/EvoAgentX/EvoAgentX?style=social)](https://star-history.com/#EvoAgentX/EvoAgentX)
[![GitHub fork](https://img.shields.io/github/forks/EvoAgentX/EvoAgentX?style=social)](https://github.com/EvoAgentX/EvoAgentX/fork)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?)](https://github.com/EvoAgentX/EvoAgentX/blob/main/LICENSE)
<!-- [![EvoAgentX Homepage](https://img.shields.io/badge/EvoAgentX-Homepage-blue?logo=homebridge)](https://EvoAgentX.github.io/EvoAgentX/) -->
<!-- [![hf_space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-EvoAgentX-ffc107?color=ffc107&logoColor=white)](https://huggingface.co/EvoAgentX) -->
</div>

<div align="center">

<h3 align="center">

<a href="./README.md" style="text-decoration: underline;">English</a> | <a href="./README-zh.md">简体中文</a>

</h3>

</div>



## What is EvoAgentX
EvoAgentX is an open-source framework for building, evaluating, and evolving LLM-based agents or agentic workflows in an automated, modular, and goal-driven manner. At its core, EvoAgentX enables developers and researchers to move beyond static prompt chaining or manual workflow orchestration. It introduces a self-evolving agent ecosystem, where AI agents can be constructed, assessed, and optimized through iterative feedback loops—much like how software is continuously tested and improved.

### ✨ Key Features

- 🧱 **Agent Workflow Autoconstruction**
  
  From a single prompt, EvoAgentX builds structured, multi-agent workflows tailored to the task.
```

---
## MemMachine/MemMachine  (★3203, v2.i=MULTI)
frameworks: ['langchain'] | agent-ish dirs: ['evaluation', 'AGENTS.md'] | tree=1041

### README (head)
```
# MemMachine

<div align="center">

![MemMachine: Long Term Memory for AI Agents](https://raw.githubusercontent.com/MemMachine/MemMachine/main/assets/img/MemMachine_Hero_Banner.png)

**The open-source memory layer for AI agents.**

*Stop building stateless agents. Give your AI persistent memory with just 5 lines of code.*

<br/>

![GitHub Release Version](https://img.shields.io/github/v/release/memmachine/memmachine?display_name=release)
![GitHub License](https://img.shields.io/github/license/MemMachine/MemMachine)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/MemMachine/MemMachine)
![Discord](https://img.shields.io/discord/1412878659479666810)
<br/>
![Docker Pulls](https://img.shields.io/docker/pulls/memmachine/memmachine)
![GitHub Downloads](https://img.shields.io/github/downloads/memmachine/memmachine/total?label=GitHub%20Downloads)
<br/>
![PyPI Downloads - memmachine-client](https://img.shields.io/pypi/dm/memmachine-client?label=PyPI%20Downloads%3A%20memmachine-client)
![PyPI Downloads - memmachine-server](https://img.shields.io/pypi/dm/memmachine-server?label=PyPI%20Downloads%3A%20memmachine-server)

</div>

## What is MemMachine?

MemMachine is an open-source **long-term memory layer** for AI agents and LLM-powered applications. It enables your AI to **learn, store, and recall** information from past sessions—transforming stateless chatbots into personalized, context-aware assistants.

### Key Capabilities

- **Episodic Memory**: Graph-based conversational context that persists across sessions
- **Profile Memory**: Long-term user facts and preferences stored in SQL
- **Working Memory**: Short-term context for the current session
- **Agent Memory Persistence**: Memory that survives restarts, sessions, and even model changes

## Quick Start

Get up and running in under 5 minutes:

> **Prerequisites:** This code requires a running MemMachine Server.
> [Start a server locally](https://docs.memmachine.ai/getting_started/quickstart) or create a free account on the [MemMachine Platform](https://console.memmachine.ai/).

```bash
pip install memmachine-client
```

---
## SenteLabsAI/OpenExecutive  (★3089, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=1047

### README (head)
```
# Open Executive

[![CI](https://github.com/SenteLabsAI/OpenExecutive/actions/workflows/ci.yml/badge.svg)](https://github.com/SenteLabsAI/OpenExecutive/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)

An AI system that acts as your company's virtual executive team — a senior advisor with Harvard MBA-level knowledge, customized for your specific business.

## Demo

[![Open Executive demo video](https://img.youtube.com/vi/O_g97xxVTMk/maxresdefault.jpg)](https://youtu.be/O_g97xxVTMk)

A walkthrough of Open Executive in action — [watch on YouTube](https://youtu.be/O_g97xxVTMk).

## What It Does

Developed by [sentelabs.ai](https://sentelabs.ai) Open Executive provides a single coherent executive voice backed by eight specialist AI agents:

- **Chief Strategy Officer** — competitive analysis, M&A, market positioning, OKRs
- **Chief Financial Officer** — financial modeling, fundraising, unit economics, cash flow
- **Chief HR/People Officer** — hiring, compensation, performance, culture
- **General Counsel** — contracts, IP, employment law basics, compliance
- **Chief Operating Officer** — process design, vendor management, operational scaling
- **Chief Marketing Officer** — GTM strategy, brand, communications, PR
- **Chief Product Officer** — roadmap, prioritization, product strategy
- **Board Communications Director** — board decks, investor relations, governance

All responses come from one consistent executive voice. The internal agent architecture is never exposed to the user. Beyond Q&A, the system maintains episodic memory of past decisions and initiatives across sessions, and a built-in scheduler can proactively surface follow-ups and time-sensitive actions.

## Architecture

```
User message
    ↓
Executive Orchestrator (claude-sonnet-4-6)
    ↓ tool use → parallel specialist calls
CSO / CFO / CHRO / GC / COO / CMO / CPO / Board
    ↓ each specialist retrieves relevant context from ChromaDB
Built-in MBA knowledge + Your company documents
    ↓
Synthesized executive response
```

**Knowledge** — Two retrieval layers per specialist call: (1) built-in MBA-level Markdown (`knowledge/builtin/`, git-tracked) seeded into ChromaDB at startup, and (2) your uploaded company documents chunked and stored in a separate `company_docs` collection. RAG context is injected into the user turn, never the cached system prompt.
```

---
## fuxicodex/Fuxi  (★3073, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=309

### README (head)
```
# FuXi

[English](README.md) | [简体中文](README.zh-CN.md)

[![GitHub stars](https://img.shields.io/github/stars/fuxicodex/Fuxi?style=flat-square&color=0a6fe7&label=stars)](https://github.com/fuxicodex/Fuxi/stargazers)
[![Release](https://img.shields.io/github/v/release/fuxicodex/Fuxi?style=flat-square&color=0a6fe7&label=release)](https://github.com/fuxicodex/Fuxi/releases)
[![Last commit](https://img.shields.io/github/last-commit/fuxicodex/Fuxi?style=flat-square&color=0a6fe7)](https://github.com/fuxicodex/Fuxi/commits/main)
[![License](https://img.shields.io/badge/license-Proprietary-0a6fe7?style=flat-square)](LICENSE)

> **An AI coding agent that lives in your terminal.**

FuXi is a fast, self-contained **terminal AI coding agent** — read code, edit
files, run commands, and drive tools from a rich TUI, with cost-aware routing
across LLM providers and automatic failover. Built in Go, it ships as one
static binary with no runtime dependencies. Think of it as a provider-agnostic
alternative to Claude Code: bring any OpenAI-compatible model and get an
agentic Think → Act → Verify loop on top of it.

**Terminal-first** · **Provider-agnostic** · **Bring your own key** · **MCP client** · **Self-updating**

Homepage: **https://www.fuxicode.com**

```bash
curl -fsSL https://releases.fuxicode.com/bootstrap.sh | bash   # install
fuxi                                                        # start
```

![FuXi in action](docs/fuxi-demo.gif)

---

### What FuXi does

Its agentic **Think → Act → Verify** loop and intelligent routing let any
OpenAPI-compatible model perform above its raw benchmark — verified against
another coding agent on a reproducible task set (see
[benchmark](benchmark/REPORT.md)).

---
## Contents

- [Highlights](#highlights)
- [How FuXi compares](#how-fuxi-compares)
- [Evaluation & benchmarks](#evaluation--benchmarks)
- [Install](#install)
```

---
## wang2122/sprix-sage-router  (★2791, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['benchmark_dynamic_evaluator.py', 'benchmark_evaluator.py'] | tree=53

### README (head)
```
<div align="center">

# Sprix SAGE Router

### Checkpoint-aware mid-execution rerouting for open A2A networks

[![Tests](https://github.com/wang2122/sprix-sage-router/actions/workflows/tests.yml/badge.svg)](https://github.com/wang2122/sprix-sage-router/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-0F766E.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Research%20Preview-D97706.svg)](#project-status)

**An open-source research output of [Sprix AI](#about-sprix-ai) at 屿智同行.**

Choose whether an in-flight task should **continue**, **recruit collaborators**, or **hand off** after accounting for completed DAG nodes, reusable artifacts, observed partial quality, remaining work, failures, budget, and deadline.

[Quick start](#quick-start) · [Algorithm](ALGORITHM.md) · [Related work](RELATED_WORK.md) · [A2A integration](docs/INTEGRATION.md) · [Operations](docs/OPERATIONS.md) · [Benchmark](#benchmark) · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md)

</div>

---

## Why SAGE?

Agent discovery tells a system which agents exist. It does not answer the harder runtime question: **who should work with whom after execution has already begun?**

SAGE—**State-Aware Graph Exchange**—is the decision layer between A2A discovery and task execution. It evaluates three routes in one auditable objective:

| Route | Ownership | Best used when |
|---|---|---|
| **SELF** | Incumbent agent | Existing capability and accumulated context are sufficient |
| **COLLABORATE** | Incumbent retains ownership | A small complementary team covers missing requirements |
| **HANDOFF** | A peer takes full ownership | Specialist advantage exceeds context-transfer loss |

SAGE is designed to sit above the [Agent2Agent (A2A) protocol](https://a2a-protocol.org/latest/). A2A provides Agent Cards, messages, tasks, artifacts, authentication, and transport. SAGE decides **which feasible agent configuration should execute the task, in which mode, and why**.

![SAGE routing pipeline and evidence loop](docs/assets/fig01-system-overview.svg)

<p align="center"><sub><b>Figure 1.</b> SAGE filters candidates, compares all three routing modes, jointly searches assignments and schedules, ranks feasible plans, and learns from execution evidence.</sub></p>

## Research focus

SAGE is deliberately narrow: **checkpoint-aware reconfiguration after execution has begun**.

- **Concrete continuation value.** The router preserves completed requirements and combines in-flight completion, observed partial quality, current ownership, and artifact portability to estimate how much work each candidate must actually redo.
- **Comparable runtime actions.** SELF, COLLABORATE, and HANDOFF share one permission-, budget-, and deadline-constrained action space. Progress-masked and static-coalition baselines receive the same registry and limits.
```

---
## alejandrobalderas/claude-code-from-source  (★2778, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=101

### README (head)
```
# Claude Code from Source

**Architecture, Patterns & Internals of Anthropic's AI Coding Agent**

<p align="center">
  <img src="./web/public/cover.jpg" alt="Claude Code from Source — Book Cover" width="400" />
  <br/><br/>
  <a href="https://claude-code-from-source.com"><strong>Read online at claude-code-from-source.com</strong></a>
</p>

---

> **This repository is purely educational.** It contains no source code from Claude Code — not a single line. Every code block is original pseudocode written to illustrate architectural patterns. The goal is to help engineers understand how production AI agents are built, not to reproduce or redistribute proprietary software.

---

When Anthropic shipped Claude Code on npm, the `.js.map` source maps contained a `sourcesContent` field with the full original TypeScript. This book is the result of studying that architecture and distilling the patterns, trade-offs, and design decisions into a technical narrative that any engineer can learn from.

**18 chapters across 7 parts.** ~400 pages in print equivalent.

Every chapter has layered depth: a narrative flow for technical leaders, deep-dive sections for implementers, and an **"Apply This"** closing that extracts transferable patterns you can steal for your own systems. Diagrams use [Mermaid](https://mermaid.js.org/) and render natively on GitHub.

---

## Who This Is For

- **Senior engineers building agentic systems** — steal the patterns, understand the trade-offs, implement in your own stack
- **Technical leaders evaluating architectures** — follow the narrative without reading every code block
- **Anyone curious about how production AI tools actually work** under the hood

---

## Table of Contents

### Part I: Foundations
*Before the agent can think, the process must exist.*

| # | Chapter | What You'll Learn |
|---|---------|-------------------|
| 1 | [The Architecture of an AI Agent](./book/ch01-architecture.md) | The 6 key abstractions, data flow, permission system, build system |
| 2 | [Starting Fast — The Bootstrap Pipeline](./book/ch02-bootstrap.md) | 5-phase init, module-level I/O parallelism, trust boundary |
| 3 | [State — The Two-Tier Architecture](./book/ch03-state.md) | Bootstrap singleton, AppState store, sticky latches, cost tracking |
| 4 | [Talking to Claude — The API Layer](./book/ch04-api-layer.md) | Multi-provider client, prompt cache, streaming, error recovery |

### Part II: The Core Loop
```

---
## AGI-Edgerunners/LLM-Agents-Papers  (★2341, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=12

### README (head)
```
(no README)
```

---
## langfengQ/verl-agent  (★2265, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['agent_system'] | tree=1548

### README (head)
```
<p align="center">
    <img src="./docs/gigpo/logo-verl-agent.png" alt="logo" width="55%">
</p>


<h3 align="center">
<b>Group-in-Group Policy Optimization for LLM Agent Training</b>
<br>
<b>NeurIPS 2025</b>
</h3>


<p align="center">
  <a href="https://arxiv.org/abs/2505.10978">
    <img src="https://img.shields.io/badge/arXiv-Paper-red?style=flat-square&logo=arxiv" alt="arXiv Paper"></a>
  &nbsp;
  <a href="https://github.com/langfengQ/verl-agent">
    <img src="https://img.shields.io/badge/GitHub-Project-181717?style=flat-square&logo=github" alt="GitHub Project"></a>
  &nbsp;
  <a href="https://huggingface.co/collections/langfeng01/verl-agent-684970e8f51babe2a6d98554">
    <img src="https://img.shields.io/badge/HuggingFace-Models-yellow?style=flat-square&logo=huggingface" alt="HuggingFace Models"></a>
  &nbsp;
  <a href="https://x.com/langfengq/status/1930848580505620677">
    <img src="https://img.shields.io/badge/Twitter-Channel-000000?style=flat-square&logo=x" alt="X Channel"></a>
  &nbsp;
  <a href="https://github.com/langfengQ/verl-agent/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg?style=flat-square" alt="License"></a>
  &nbsp;
  <a href="https://github.com/langfengQ/verl-agent/issues">
    <img src="https://img.shields.io/github/issues/langfengQ/verl-agent?style=flat-square&color=green" alt="GitHub issues"></a>
  &nbsp;
  <a href="https://github.com/langfengQ/verl-agent/stargazers">
    <img src="https://img.shields.io/github/stars/langfengQ/verl-agent?style=social" alt="Repo stars"></a>
  &nbsp;
</p>

`verl-agent` is an extension of [veRL](https://github.com/volcengine/verl), specifically designed for training **large language model (LLM) agents via reinforcement learning (RL)**. 

Unlike prior approaches that simply concatenate full interaction histories, `verl-agent` proposes **step-independent multi-turn rollout mechanism**, which allows for **fully customizable** per-step input structures, history management, and memory modules. This design makes `verl-agent` **highly scalable for very long-horizon, multi-turn RL training** (e.g., tasks in ALFWorld can require up to 50 steps to complete).

`verl-agent` provides a **diverse set of RL algorithms** (including our new algorithm GiGPO) and a **rich suite of agent environments**, enabling the development of reasoning agents in both visual and text-based tasks.

# News
- [2026.05] `GraphGPO` accepted at [ICML 2026](https://icml.cc/)! 🎉🎉🎉 [[Paper](https://arxiv.org/abs/2605.26684)] [[Code](https://github.com/langfengQ/verl-agent/tree/master/recipe/GraphGPO)]
- [2026.02] `HGPO` accepted at [ICLR 2026](https://iclr.cc/)! 🎉🎉🎉 [[Paper](https://openreview.net/forum?id=T8Dev99qnz)] [[Code](https://github.com/langfengQ/verl-agent/tree/master/recipe/hgpo)]
```

---
## satellitecomponent/Neurite  (★2124, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=188

### README (head)
```

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/discord/1093603405609582755?style=flat&logo=discord&logoColor=white&label=Discord&color=%237289da)](https://discord.gg/NymeSwK9TH)


# 🌐 **[neurite.network](https://neurite.network/)** 🌐

⚠️ `Warning:` Contains flashing lights and colors which may affect those with photosensitive epilepsy.

> <a href="https://www.youtube.com/watch?v=1BiUblUAd7s&list=PLnwfKwpTq3vDlXDrLParmQ_3waM1g-ehf"><strong>Check out our newly released series of demo videos!</strong></a>

🌱 This is an open-source project in active development.
<table>
  <tr>
    <td>
      <h2>Table of Contents</h2>
      <ol>
        <li><a href="#introduction">Introduction</a></li>
        <li><a href="#key-features">Key Features</a></li>
        <li><a href="#how-to-use-neurite">How to Use Neurite</a></li>
        <li><a href="#synchronized-knowledge-management">Synchronized Knowledge Management</a></li>
        <li><a href="#fractalgpt">FractalGPT</a></li>
        <li><a href="#multi-agent-ui">Multi-Agent UI</a></li>
        <li><a href="#neurite-desktop">Neurite Desktop</a></li>
        <li><a href="#neural-api">Neural API</a></li>
        <li><a href="#join-the-conversation">Join the Conversation</a></li>
        <li><a href="#gallery">Gallery</a></li>
      </ol>
    </td>
    <td style="width: 35%; text-align: center;">
      <div>
        <a href="https://www.youtube.com/watch?v=1BiUblUAd7s"><strong>Welcome to Neurite | Getting Started</strong></a>
        <h2><strong></strong></h2>
        <a href="https://www.youtube.com/watch?v=1BiUblUAd7s">
          <img src="https://img.youtube.com/vi/1BiUblUAd7s/mqdefault.jpg" width="100%" title="Click to watch" alt="Welcome to Neurite"/>
        </a>
      </div>
    </td>
  </tr>
</table>

## `Introduction`

## Bridging Fractals and Thought

```

---
## Dicklesworthstone/mcp_agent_mail  (★2117, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: ['AGENTS.md'] | tree=333

### README (head)
```
# MCP Agent Mail

![Agent Mail Showcase](screenshots/output/agent_mail_showcase.gif)

> "It's like gmail for your coding agents!"

A mail-like coordination layer for coding agents, exposed as an HTTP-only FastMCP server. It gives agents memorable identities, an inbox/outbox, searchable message history, and voluntary file reservation "leases" to avoid stepping on each other.

Think of it as asynchronous email + directory + change-intent signaling for your agents, backed by Git (for human-auditable artifacts) and SQLite (for indexing and queries).

Status: Under active development. The design is captured in detail in `docs/planning/project_idea_and_guide.md` (start with the original prompt at the top of that file).

## Why this exists

Modern projects often run multiple coding agents at once (backend, frontend, scripts, infra). Without a shared coordination fabric, agents:

- Overwrite each other's edits or panic on unexpected diffs
- Miss critical context from parallel workstreams
- Require humans to "liaison" messages across tools and teams

This project provides a lightweight, interoperable layer so agents can:

- Register a temporary-but-persistent identity (e.g., GreenCastle)
- Send/receive GitHub-Flavored Markdown messages with images
- Search, summarize, and thread conversations
- Declare advisory file reservations (leases) on files/globs to signal intent
- Inspect a directory of active agents, programs/models, and activity

It's designed for: FastMCP clients and CLI tools (Claude Code, Codex, Gemini CLI, Factory Droid, etc.) coordinating across one or more codebases.

## From Idea Spark to Shipping Swarm

If a blank repo feels daunting, follow the field-tested workflow we documented in `docs/planning/project_idea_and_guide.md` (“Appendix: From Blank Repo to Coordinated Swarm”):

- **Ideate fast:** Write a scrappy email-style blurb about the problem, desired UX, and any must-have stack picks (≈15 minutes).
- **Promote it to a plan:** Feed that blurb to GPT-5 Pro (and optionally Grok4 Heavy / Opus 4.1) until you get a granular Markdown plan, then iterate on the plan file while it’s still cheap to change. The Markdown Web Browser sample plan shows the level of detail to aim for.
- **Codify the rules:** Clone a tuned `AGENTS.md`, add any tech-specific best-practice guides, and let Codex scaffold the repo plus Beads tasks straight from the plan.
- **Spin up the swarm:** Launch multiple Codex panes (or any agent mix), register each identity with Agent Mail, and have them acknowledge `AGENTS.md`, the plan document, and the Beads backlog before touching code.
- **Keep everyone fed:** Reuse the canned instruction cadence from the tweet thread or, better yet, let the commercial Companion app’s Message Stacks broadcast those prompts automatically so you never hand-feed panes again.

Watch the full 23-minute walkthrough (https://youtu.be/68VVcqMEDrs?si=pCm6AiJAndtZ6u7q) to see the loop in action.

## Productivity Math & Automation Loop

One disciplined hour of GPT-5 Codex—when it isn’t waiting on human prompts—often produces 10–20 “human hours” of work because the agents reason and type at machine speed. Agent Mail multiplies that advantage in two layers:
```

---
## chrisworsey55/atlas-gic  (★2090, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=26

### README (head)
```
🚀 ATLAS Agents is Live

To the 1,000 people who joined our waitlist — thank you.
Your early belief in what we were building means everything to us. Today is the day. ATLAS Agents is officially live and you can now sign up.
Here's a reminder of what you get on each plan:

🆓 Free

Agent leaderboard (top 5)
Delayed signals (24h)
Dashboard
Live signals
Copy trading
Agent builder


⭐ Pro — $49/month (Most Popular)

All 25 agents
Live signals + reasoning
Equities copy-trading via Alpaca
Kalshi prediction market copy
Agent builder beta
Darwin history
Full API

👉 Sign up for Pro: https://buy.stripe.com/8x29AL67A68R1vycY36EU00
🎟 Use code GITHUB20 for 20% off

🛠 Builder — $499/month

Everything in Pro
Full API
Unlimited agent builds
18-month backtest dataset
Marketplace publishing
Priority Darwin compute

👉 Sign up for Builder: https://buy.stripe.com/4gM14f8fI1SB5LOcY36EU01
🎟 Use code GITHUB20 for 20% off


See you on the other side. Let's go. 🤖📈

---
```

---
## jd-opensource/OxyGent  (★2066, v2.i=SINGLE)
frameworks: [] | agent-ish dirs: [] | tree=1150

### README (head)
```
<!-- Copyright 2022 JD Co.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this project except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. -->

[English](./README.md) | [中文](./README_zh.md)


<p align="center">
  <a href="https://github.com/jd-opensource/OxyGent/pulls">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome">
  </a>
  <a href="https://github.com/jd-opensource/OxyGent/blob/v4/LICENSE">
    <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="license"/>
  </a>
  <a href="https://pypi.org/project/oxygent/">
    <img src="https://img.shields.io/pypi/v/oxygent.svg?logo=pypi&logoColor=white" alt="pip"/>
  </a>
  <a href="https://arxiv.org/abs/2604.25602">
    <img src="https://img.shields.io/badge/Paper-ACL%202026-orange" alt="paper"/>
  </a>

<html>
    <h2 align="center">
      <img src="https://storage.jd.com/ai-gateway-routing/prod_data/oxygent_github_images/banner.jpg" width="1256"/>
    </h2>
    <h3 align="center">
      An advanced Python framework that empowers developers to quickly build production-ready intelligent systems. 
    </h3>
    <h3 align="center">
      Visit our website:
      <a href="http://oxygent.jd.com">OxyGent</a>
      ｜Open Source:
      <a href="https://github.com/jd-opensource/OxyGent">Python</a>
      or
      <a href="https://github.com/jd-opensource/JDOxyGent4J">Java</a>
```
