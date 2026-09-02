# MCP in the Wild: A Source-Level Census of Model Context Protocol Adoption in Open-Source Software

**Contribution level**: `theory+empirics` — 187-repo stratified population census with a gold-annotated
2-pass classifier, baseline (AI-tooling anchors vs general population, MCPZoo supply side), and
flip-sensitivity analysis; every headline number traceable to a committed artifact.

## Abstract

The Model Context Protocol (MCP) — an open protocol (Nov 2024) for connecting LLM applications to
external tools and data — is described by vendors and integrators as "widely adopted" within eighteen
months, with SDKs in TypeScript/Python/Go/Rust/Kotlin, official reference servers, and integrations
from OpenAI, Google, and Microsoft. Yet no population-level measurement supports the adoption claim:
existing studies measure the *server supply side* (MCPZoo: 64,611 registered servers) or audit specific
security/behavioral properties, and zero works census the *integration side* — which top open-source
projects actually ship MCP servers or consume MCP via production clients. We present the first
source-level adoption census of MCP in open source: a stratified corpus of 187 top-starred repositories
(174 general-population Tier B across 6 strata, 10 AI-tooling Tier A anchors by name, 3 negative
controls), each head-SHA-pinned and classified with a multi-channel signal dictionary (SDK manifests,
server/client entry points, spec-version pinning) and a noise dictionary separating *integrated* MCP
from *toy/observer/platform-API* MCP. Gold-standard adjudication was performed in two independent
passes (single annotator, disclosed). Findings: (H1) adoption is ecosystem-concentrated — 41/174
Tier B repositories (23.6%, Wilson 95% CI [17.9%, 30.4%]) verifiably integrate MCP, and the rate is
4.6x higher in AI-native strata (S1-S4: 37/116 = 31.9%) than in general-software strata (S5-S6: 4/58 =
6.9%; Fisher p = 1.35e-4); (H2) the registered "servers shipped ≫ clients consumed" asymmetry is
**falsified** at the population level — among adopters, server-shipping (27) and client-embedding (21)
are roughly balanced, and general-software adopters (e.g. Playwright, MLflow, Glances) ship servers to
*export* data/tools to AI agents while client-embedding (*import*) is confined to AI-native strata;
(H3) the protocol version space has expanded beyond the three registered revisions — the reference SDK
declares five supported versions (2024-10-07 … 2025-11-25) plus a 2026-07-28 type set, and explicit
app-level `protocolVersion` pins are rare (3/41) and strategic (legacy-compat, current, or
bleeding-edge); (H4) adoption is recent — 23/41 adopters were created in 2025-2026 — and none of the
2025-era cohort was abandoned at census time (cross-sectional; longitudinal limits disclosed). The MCP
adoption rate (23.6%) is ≈7x the eBPF adoption rate measured by our earlier census (3.4%, journal issue
#65), quantifying the unprecedented velocity of the first AI-protocol adoption wave.

## 1. Introduction

The Model Context Protocol was open-sourced by Anthropic on 2024-11-25 to standardize how LLM
applications expose and consume external tools and data. Within eighteen months it was adopted across
the AI infrastructure stack: OpenAI's Agents SDK, Google's ADK, and Microsoft's ecosystem all speak
MCP; the official `modelcontextprotocol/servers` repository and community registries list tens of
thousands of servers; SDKs exist in TypeScript, Python, Go, Rust, Kotlin, and Java. The phrase "widely
adopted" appears in vendor blogs, framework READMEs, and research papers alike.

How well does the claim hold at the source level? We found no population measurement. A scan of the
recent arXiv window (cs.SE ~230 titles + cs.AI/cs.CL/cs.PL/cs.OS/cs.CR 2026-05..08 listings, plus the
full-window query `all:"Model Context Protocol" AND all:"in the wild"` re-verified on 2026-09-02 after
API recovery) surfaces exactly the following MCP-related works, none of which is an adoption census:

- **MCPZoo (2607.11086)**: a large-scale study of *runtime MCP servers* — 64,611 unique servers
  registered in community registries — measuring **security scanner reliability**. This measures the
  **supply side**: what servers exist and how well scanners flag them.
- **"Can MCP Clients Decide What to Do After Failure?" (2609.00072)**: a result-only actionability
  audit of client behavior after tool failure.
- **VATS (2606.07992)**: error-path injection attack surface of MCP servers.
- **Secret MCP (2608.24944)** and **CTFusion (2605.11504)**: a design-spec generation system built on
  MCP and a CTF benchmark for agents, respectively — both *assume* adoption.
- This journal's census family (Consensus #63, eBPF #65, PQC #61, Multi-Agent #57): source-level
  adoption censuses of other technologies; none measures an AI protocol, and eBPF (#65) provides the
  rarity baseline (3.4%) this paper contrasts against.

The blank is the **integration side**: which top open-source projects verifiably integrate MCP into
their code — shipping servers, consuming via production clients, or both — and how that adoption
stratifies by ecosystem, role, and protocol version. This paper fills that blank with the census
methodology validated across this journal's family: a stratified, head-SHA-pinned corpus; a
multi-channel signal dictionary; a noise dictionary with embedder-vs-user-style adjudication; a
single-annotator two-pass gold standard (disclosed); Wilson confidence intervals; and flip-sensitivity
analysis.

## 2. Related Work

**2.1 MCPZoo (2607.11086), "Rethinking MCP Security" — supply-side registry census.**
MCPZoo dynamically runs 64,611 unique MCP servers from community registries and evaluates security
scanner reliability (96.89% of scanned servers reported risky, <50% of alerts true positives).
*Difference*: MCPZoo answers "what is in the server registry and how reliably can it be scanned?" —
its population is the *registry* and its object is *security*. Our census answers "which top OSS
projects integrate MCP into production code?" — its population is a fixed stratified top-starred OSS
set and its object is *adoption behavior* (ship vs consume, roles, spec pinning). The two are
complementary and jointly bound the MCP ecosystem: MCPZoo quantifies supply (64,611 servers), we
quantify demand/integration (23.6% of top OSS, role-balanced). H2 uses MCPZoo's count as the supply
baseline.

**2.2 MCP failure-actionability audit (2609.00072).**
Probes whether MCP clients can decide what to do after a tool failure, i.e., client *behavior under
error*. *Difference*: it audits a small set of named clients' failure semantics; it does not measure
which OSS projects embed clients at all. Our client-role count (14 pure + 7 both) is a population
statement about integration; their study is a behavioral statement about a handful of clients.

**2.3 VATS (2606.07992) and MCP security audits.**
VATS exploits implicit authority in MCP server error paths via systematic mutation. *Difference*:
attack-surface analysis of MCP servers under test; neither adoption rates nor roles.

**2.4 Secret MCP (2608.24944) / CTFusion (2605.11504).**
System and benchmark built on MCP. *Difference*: they assume MCP adoption; we measure it.

**2.5 Census family (journal #63 consensus / #65 eBPF / #61 PQC / #57 multi-agent).**
*Difference*: prior censuses measured mature or niche technologies (Raft 12-year retest; eBPF in the
Linux ecosystem; PQC migration; multi-agent frameworks). MCP is the first *AI application protocol*
wave, measured 22 months after open-sourcing. The 23.6%-vs-3.4% contrast with #65 quantifies how much
faster a protocol-level integration wave can diffuse when it rides an AI-tooling ecosystem with
first-party SDK support.

## 3. Method

### 3.1 Corpus construction

- **Tier A anchors (10, by NAME)**: the MCP ecosystem's own infrastructure — `anthropics/claude-code`
  (flagship client), `modelcontextprotocol/servers`, `python-sdk`, `typescript-sdk`,
  `modelcontextprotocol/modelcontextprotocol` (spec), `PrefectHQ/fastmcp`, `openai/openai-agents-python`,
  `google/adk-python`, `awslabs/mcp`, `punkpeye/awesome-mcp-servers` (curation list).
- **Tier B (174, 6 strata x 29)**: top-starred repositories by topic search across six strata —
  S1 AI tooling, S2 AI dev-tools/IDEs, S3 AI apps, S4 AI frameworks/general frameworks, S5 general
  apps, S6 automation/observability. Membership by NAME (anchors that topic-hit into Tier B were
  recovered by name; proven star-farm `affaan-m/ECC` and learning-list repos excluded by name).
- **NEG (3)**: `redis/redis`, `FFmpeg/FFmpeg`, `sqlite/sqlite` — no AI, no MCP (L0 expected).
- All 187 repositories **head-SHA-pinned** on 2026-09-02 (census date); 187/187 trees fetched, 0
  truncations/failures.

### 3.2 Signal dictionary (3 channels) and classifier

- **Channel 1 — dependency manifests**: official SDK packages (`@modelcontextprotocol/sdk`,
  `@modelcontextprotocol/client`; Python `mcp`, `fastmcp`; Go `mark3labs/mcp-go`; Rust `rmcp`;
  Java/Kotlin `io.modelcontextprotocol.*`), declared directly (not transitive/lockfile-only).
- **Channel 2 — source artifacts**: in-repo MCP server/client entry points and protocol code
  (`Server()`/`McpServer`/`FastMCP`, `McpClient`/`ClientSession`, transports, tool registration) in
  production paths. **In-tree source counts even when the language has no manifest** (netdata's C
  implementation is invisible to manifests — mirror of the #65 `.bpf.c` rule).
- **Channel 3 — spec pinning**: `protocolVersion` literals in code/config (H3).
- **Levels**: L0 no credible signal / README-only / curation / transitive / test-fixture / observer;
  L1 manifest signal without verified in-repo protocol integration; L2 verified integration (direct
  manifest declaration and/or in-tree MCP source in production paths).
- **Roles (H2)**: server (ships >=1 MCP server), client (embeds >=1 MCP client), both.

### 3.3 Noise dictionary (9 rules, committed)

1. toy/demo/test downgrade (`examples/`, `tests/`, `testdata/` code does not count);
2. curation ≠ integration (awesome-lists, directories → L0);
3. README-only mention ≠ signal;
4. dev-dependency-only / transitive lockfile-only → L0 (go.sum-only, `// indirect`);
5. vendored SDK copies / generated files don't count as app-level spec pins;
6. acronym collision: "MCP" can mean other things — source-level symbol checks disambiguate, never
   bare-word counts;
7. membership by NAME, never topic-search (anchors recovered by name);
8. **platform-MCP-API consumer ≠ MCP adopter** (NEW, coze-dev/coze-studio lesson): calling a cloud
   platform's MCP *management API* or rendering its MCP *config UI* is not integrating the protocol —
   zero MCP SDK dependency and no protocol code in repo → L1 at most;
9. repo-is-server name rule (ChromeDevTools/chrome-devtools-mcp, microsoft/playwright-mcp: the repo IS
   the MCP server — adjudicated by name + package purpose).

### 3.4 Gold standard (single annotator, 2 passes — disclosed)

Labels were produced by one human annotator in **two independent passes**.
- **Pass 1**: classifier + tree-path scan + targeted content probes at pinned HEAD (44 candidates:
  30 mechanical L2 + 14 L1) → 42 L2.
- **Pass 2**: candidates re-derived from **raw manifest evidence only** (no Pass-1 conclusions
  loaded) by a mechanical classifier → 3 disagreements, each resolved by content probe:
  - `coze-dev/coze-studio` L2→**L1** (noise rule 8): 269 package.jsons contain zero MCP SDK;
    `mcp_server.ts` is an auto-generated REST client for the Coze *platform* API; the MCP config
    dialog is a publish-compliance UI.
  - `mksglu/context-mode` client→**server**: self-description "MCP plugin ... Works with Claude Code,
    Gemini CLI, VS Code Copilot" + `registerTool` server pattern — it ships a server.
  - Pass-1 content-probe downgrades (`elizaOS/eliza` L2→L1: in-repo MCP modules are SSRF/spawn
    security + tool *cache*; the protocol client lives in the external `@elizaos/plugin-mcp` package;
    `GoogleChrome/lighthouse` L1→L0: "webmcp" is a Chrome CDP domain — Lighthouse *audits* MCP tools
    on web pages, it does not adopt MCP) were independently confirmed by Pass 2.
- **Final gold**: 41 L2 Tier B repos (table in §A), 3/3 NEG L0, 8/8 Tier-A adopters L2 by construction
  (2 infra repos — curation list and spec/docs repo — excluded as non-adopters).
- Inter-rater agreement is not reportable with n=1 — disclosed; §5 flip sensitivity shows no
  conclusion depends on any single label.

## 4. Results

### 4.1 Headline adoption rate (H1)

**41/174 Tier B repositories (23.6%; Wilson 95% CI [17.9%, 30.4%]) verifiably integrate MCP at L2.**
The prima-facie manifest signal was 48/174 (27.6%); the gold-standard pass removed 7 manifest-positive
false positives (eliza, coze, lighthouse + 4 role/boundary corrections). Per-stratum rates (n=29 each):
S4 AI/general frameworks 16, S1 AI tooling 9, S3 AI apps 8, S2 AI dev-tools 4, S6 automation/
observability 3, S5 general apps 1. Adoption is **ecosystem-concentrated**: AI-native strata (S1-S4)
37/116 = 31.9% vs general-software strata (S5-S6) 4/58 = 6.9% — Fisher two-sided p = 1.35e-4,
chi2(5) = 21.5 vs uniform. Tier-A anchors are 8/8 adopters by construction (100%, baseline not
informative; the Tier-B 23.6% rate is the informative population number). For contrast with the
eBPF census (#65): Tier B 6/174 = 3.4% — **MCP adoption in top OSS is ≈7x eBPF adoption**,
quantifying the velocity of a protocol wave riding first-party AI-SDK support.

### 4.2 Roles and the supply/demand asymmetry (H2)

Among the 41 adopters: **server 20 / client 14 / both 7**. Repositories shipping >=1 MCP server: 27;
embedding >=1 MCP client: 21. The registered hypothesis — "projects ship far more MCP servers than
they consume via production clients; the MCP explosion is server-side" — is **falsified** at the
population level: pure-server 20/34 = 58.8% (Wilson 95% CI [42.2%, 73.6%]) does not exclude 50%, and
counting both-role adopters the two sides are nearly balanced. MCPZoo's 64,611-server registry is a
*supply-side* phenomenon (mostly small registry entries), not evidence that production client
integration is rare.

The asymmetry that does exist is a **role × stratum morphology**:

| stratum group | server | client | both |
|---|---|---|---|
| AI strata (S1-S4) | 16 | 14 | 7 |
| general (S5-S6) | 4 | 0 | 0 |

General-software adopters (Playwright, MLflow, Glances, netdata, worldmonitor…) ship MCP servers to
**export** their data/tools to AI agents; **none embeds a client**. Client embedding (**import** of
external MCP tools) is confined to AI-native strata — most sharply in S3 AI apps (6 client vs 1
server). Fisher pure-role p = 0.126 (n=4 general pure adopters) — the morphology is descriptive and
directional, not a statistical headline; disclosed as small-n. Framed economically: general software
adopts MCP where it is a *distribution channel* for AI agents; AI software adopts MCP where it is a
*tool supply line*.

### 4.3 Spec-version drift (H3) — version-space expansion + pin strategy

The registration (2026-05) assumed three protocol revisions: 2024-11-05 / 2025-03-26 / 2025-06-18.
At census (2026-09-02, pinned HEAD) the reference TypeScript SDK declares
`LATEST_PROTOCOL_VERSION = '2025-11-25'`, `SUPPORTED = [2025-11-25, 2025-06-18, 2025-03-26,
2024-11-05, 2024-10-07]`, and the repository carries type sets for both 2025-11-25 and 2026-07-28:
**the version space has expanded from 3 to 5+ revisions (2024-10-07 … 2026-07-28)** — the spec was
not frozen at 2025-06-18 as the registration assumed.

Explicit app-level `protocolVersion` pins are **rare**: content probes of the 41 L2 repos found
pinning literals in entry files in only 3 repos, and the pins are strategic, not stale:
- `czlonkowski/n8n-mcp` — **dual-version legacy compat**: standard `2025-03-26` default + `2024-11-05`
  pin for interop with n8n's own MCP server;
- `koala73/worldmonitor` — current pin `2025-03-26`;
- `nexu-io/open-design` — **bleeding-edge** `2026-01-26` (newer than the SDK's declared LATEST);
- the majority (e.g. `simstudioai/sim`) ride SDK negotiation (`LATEST_PROTOCOL_VERSION`).

GitHub code search across the 41 adopters + 8 anchors (chunked, includes test/SDK-internal hits):
2024-11-05 → 66 file hits / 17 repos; 2025-03-26 → 65/15; 2025-06-18 → 68/17. The legacy-version hits
concentrate in **pin-verification tests** (e.g. oh-my-openagent's 15 hits are `mcp-protocol-pin.test.ts`
files that deliberately assert version support), not production defaults.

**Finding**: "adopters are stuck on old protocol pins" is NOT supported. Drift manifests as
version-space expansion plus a deliberate pin-strategy taxonomy (legacy-compat / current /
bleeding-edge / ride-SDK). SDK versions in use corroborate: TypeScript SDK ^1.15 → ^1.30, rmcp
1.4.0/2.2.0, mcp-go 0.41.1, fastmcp 4 — all actively maintained tracks.

### 4.4 Adoption recency and cohort state (H4)

Of the 41 adopters, 23 (56%) were created in 2025-2026 (14 in 2025, 9 in 2026) — MCP adoption in this
population is **recent**, consistent with the protocol's 2024-11 open-sourcing and 2025 vendor
adoption. At census date: 0 archived, 0 with no push since 2026-06-01 — the 14-repo 2025 cohort is
entirely active. *Limitation (by-construction)*: the corpus is top-starred and HEAD-pinnable, so
survival ~100% is partly an artifact of selection; the honest cross-sectional claim is "adoption is
recent and no adopter in the population was abandoned at census time". Longitudinal survival
(reconstructing the 2025 adoption cohort by git-history first-MCP-dep dates) is future work.

### 4.5 Controls

NEG controls redis/FFmpeg/sqlite: 3/3 L0 (no MCP deps, no MCP source paths). Tier-A curation repo
(awesome-mcp-servers) L0 and spec/docs repo L1-infra by noise rule 2 — infra is not adoption.

## 5. Threats to validity and why this is still worth publishing

- **Single annotator** (n=1, no inter-rater agreement). Mitigation: two-pass protocol where Pass 2
  re-derives candidates from raw manifest evidence without Pass-1 conclusions; Pass 2 caught one real
  Pass-1 error (coze, noise rule 8). Flip sensitivity (§S): the headline rate needs 7+ re-adjudicated
  false positives to drop below 20% (24 to drop below 10%); H1 needs 11+ AI-strata flips to cross
  p = 0.05 (the AI-vs-general contrast is anchored by the tiny general count 4/58, which is itself
  robust: all 4 false → p = 5.5e-8). No conclusion depends on a single label.
- **Population bounded**: top-starred OSS (stars ≥ ~4k by stratum construction) — findings do not
  generalize to the long tail of small repos (where MCPZoo shows thousands of tiny servers exist);
  this is the intended embedder-vs-user population contrast, and it is the same population frame as
  the eBPF census (#65) enabling the 7x comparison.
- **Snapshot at one date** (2026-09-02, HEAD-pinned): MCP adoption is moving fast; rates are a
  census-date measurement, deliberately reproducible (byte-identical) rather than live.
- **Language visibility**: TS/JS-heavy corpus (SDK-first ecosystem); Go/Rust/Python/C covered but
  manifest visibility differs — the in-tree source rule (netdata C) mitigates but C adopters with
  non-obvious paths could be missed; worst-case direction is underestimation.
- **By-construction anchors**: Tier-A 100% adoption is a calibration anchor, not evidence.
- **H2-refined small-n**: the general-strata server-only morphology rests on n=4; reported
  descriptively with Fisher p = 0.126, not as a headline.
- **Why still worth publishing**: this is the first integration-side measurement of the first
  AI-protocol adoption wave; it quantifies (not merely asserts) the "widely adopted" claim (23.6%,
  7x eBPF), falsifies a plausible supply-side asymmetry with population evidence, documents spec-drift
  as version-space expansion plus pin strategy, and extends the journal's validated census
  methodology (7th application) to protocol-level AI infrastructure.

## 6. Reproducibility

`bash reproduce.sh` regenerates all reports from committed snapshots (offline; no network, no GitHub
API) and byte-compares against `snapshots/expected_output/`; `validate.py` performs an independent
re-count (15 checks); `trace_check.py` traces every manuscript headline number to a committed artifact
(0 gaps). Expected output:

```
== reproduction complete: all byte-identical, 15/15 re-count OK, 0 gaps ==
```

Tolerance: none — byte-identical (deterministic pipeline). See README.md.

## References

1. Model Context Protocol specification and SDKs. modelcontextprotocol/modelcontextprotocol,
   python-sdk, typescript-sdk (GitHub), 2024-2026.
2. **2607.11086** — Rethinking MCP Security: A Large-Scale Study of Runtime MCP Servers and Security
   Scanner Reliability (MCPZoo), 2026.
3. **2609.00072** — Can MCP Clients Decide What to Do After Failure? A Result-Only Actionability
   Audit, 2026.
4. **2606.07992** — VATS: Exploiting Implicit Authority in Error-Path Injection via Systematic
   Mutation, 2026.
5. **2608.24944** — Secret MCP: Evidence-Bounded and Context-Isolated Design Specification Generation
   from Web Screenshots, 2026.
6. **2605.11504** — CTFusion: A CTF-based Benchmark for LLM Agent Evaluation, 2026.
7. #65 — eBPF in the Wild: A Source-Level Census of BPF Program Adoption in Open-Source Projects
   (this journal, 20th paper, 2026).
8. #63 — Consensus in the Wild: source-level consensus-protocol adoption census (this journal, 19th
   paper, 2026).
9. #61 — Post-Quantum in the Wild: source-level PQC migration census (this journal, 18th paper, 2026).

## Appendix A — Gold-standard L2 repos (41) by role and stratum

**server (20)**: microsoft/playwright (S6), mlflow/mlflow (S6), netdata/netdata (S4), nicolargo/glances
(S6), koala73/worldmonitor (S4), JuliusBrussee/caveman (S1), anthropics/claude-plugins-official (S4),
assafelovic/gpt-researcher (S4), czlonkowski/n8n-mcp (S4), t8y2/dbx (S4), thedotmack/claude-mem (S1),
ChromeDevTools/chrome-devtools-mcp (S4), microsoft/playwright-mcp (S4), DietrichGebert/ponytail (S1),
pascalorg/editor (S4), surrealdb/surrealdb (S2), responsively-org/responsively-app (S2),
nexu-io/open-design (S5), agent0ai/agent-zero (S3), mksglu/context-mode (S4).

**client (14)**: google-gemini/gemini-cli (S1), openclaw/openclaw (S3), deepseek-ai/deepseek-harness
(S1), continuedev/continue (S2), chatboxai/chatbox (S3), code-yeongyu/oh-my-openagent (S1),
danny-avila/LibreChat (S4), assistant-ui/assistant-ui (S3), bytedance/UI-TARS-desktop (S4),
bytedance/deer-flow (S1), Cinnamon/kotaemon (S3), Kilo-Org/kilocode (S2), every-app/open-seo (S4),
simstudioai/sim (S3).

**both (7)**: n8n-io/n8n (S4), NousResearch/hermes-agent (S1), alibaba/nacos (S4), tambo-ai/tambo
(S4), unslothai/unsloth (S1), yc-software/qm (S3), flipped-aurora/gin-vue-admin (S4).
