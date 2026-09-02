# WebGPU in the Wild: A Source-Level Census of WebGPU Adoption in Web Open-Source Software

**Contribution level**: `theory+empirics` — 182-repo stratified population census of a web-platform
API with a gold-annotated 2-pass classifier, a within-corpus WebGL migration baseline, a
role (render/compute) × stratum matrix, a fallback/progressive-enhancement morphology instrument,
and flip-sensitivity analysis; every headline number traceable to a committed artifact.

## Abstract

WebGPU — the web platform's GPU API (compute + render), shipped by Chrome/Edge since 2023 and by
Firefox (141, 2025) and Safari (26, 2025) — is described by browser vendors, game-engine teams, and the
in-browser-AI community as the production standard that will replace WebGL, with WebGPU-powered LLM
inference engines (web-llm, transformers.js) and engine-level renderers (three.js WebGPURenderer,
Babylon.js WebGPUEngine). Yet no population-level measurement supports the adoption claim: the 2026
measurement wave quantifies WebGPU *performance* (dispatch overhead), *privacy* (shader
fingerprinting), and *robustness* (shader-translator fuzzing) — all on workloads or live sites chosen
by the authors — and zero works census the *integration side*: which top web open-source projects
verifiably adopt WebGPU in production source. We present the first source-level adoption census of
WebGPU in web open-source software: a stratified corpus of 182 repositories (5 WebGPU-ecosystem Tier
A anchors by name, 3 negative controls, 174 general-population Tier B across 6 web-software strata),
each head-SHA-pinned at census time and classified with a four-channel signal dictionary (raw
`navigator.gpu` API usage, engine-mediated WebGPU renderer selection, `@webgpu/*` manifest types, and a
**WebGL baseline channel** that gives every repository a GPU-API state: WebGL-only, WebGPU, or dual)
and a ten-rule noise dictionary separating *integrated* WebGPU from *demo/spec/type-only/WebGL-only*
GPU code. Gold-standard adjudication ran in two independent passes (single annotator, disclosed).
Findings: (H1) WebGPU adoption in top web OSS is low and concentrated — 14/174 Tier B repositories
(8.0%, Wilson 95% CI [4.9%, 13.1%]) verifiably ship WebGPU, versus 48 (27.6%) that ship WebGL; among
the 51 GPU-API-using repositories, WebGPU holds only 27.5% (WebGL retains a 72.5% majority), and the
rate is up to 8x higher in the web-3D-graphics stratum (7/29 = 24%, vs 10% in the AI-web stratum and
3% in the other four; Fisher S1-vs-rest p = 0.0021); (H2) raw-API adoption is an **engine/toolchain
phenomenon** — 11/14 Tier B adopters call `navigator.gpu` because they *implement* a WebGPU backend
or toolchain themselves (pixi.js, PlayCanvas, Orillusion, p5.js, melonJS, tfjs-backend-webgpu, gpu.js,
vscode's GPU-accelerated viewport, …), while app-level adopters reach WebGPU *mediated* through an
engine's renderer selection (A-Frame, the architectural editor) or an execution-provider string (web-llm
via a WASM runtime that contains the entire WebGPU path — **zero `navigator.gpu` in its TypeScript
source**; transformers.js via the ONNX Runtime `webgpu` EP); (H3) roles split by stratum — compute
usage is confined to AI/ML toolchain adopters (tfjs, gpu.js) while render usage dominates
graphics/game strata, and **11/14 (79%) of WebGPU adopters also ship a WebGL renderer path**, making
progressive-enhancement fallback (feature-detect WebGPU, degrade to WebGL) the dominant production
structure — an adoption morphology unique to web-platform APIs, which server-side technologies never
exhibit; (H4) all adopters were live at the census snapshot (cross-sectional; longitudinal limits
disclosed). Contrasted with this journal's MCP census (#68), where adoption was AI-ecosystem-elevated
(AI strata 31.9% vs general 6.9%, p = 1.35e-4), WebGPU adoption is *graphics*-elevated and
AI-agnostic (AI-web stratum 10% vs rest 8%, p = 0.46) — a protocol-vs-API contrast: protocols diffuse
through the ecosystems that speak them, platform GPU APIs diffuse through the toolchains that
implement them.

## 1. Introduction

WebGPU became the web's third-generation GPU API when it shipped in Chrome and Edge in 2023, in
Firefox 141 (2025), and in Safari 26 (2025) — the first GPU API to reach cross-browser parity within
two years of first availability. Its promise is a modern, explicit, compute-capable GPU API that
replaces the WebGL 1/2 stack (an OpenGL ES 2/3 wrapper from the early 2010s), enabling in-browser ML
inference, GPU-driven rendering, and compute-style workloads without plugins. The claim that WebGPU is
"the future of web graphics" and will replace WebGL is repeated in vendor blogs, engine changelogs
(three.js WebGPURenderer, Babylon.js WebGPU engine, pixi.js v8 GPU renderer), and the papers of the
2026 in-browser-AI wave.

How well does the claim hold at the source level — in 2026, after two years of cross-browser
availability? We found no population measurement. A scan of the recent arXiv window
(`WebGPU` submissions plus the phrase query `"WebGPU" "in the wild"` re-verified via arxiv.org HTML
search on 2026-09-02) surfaces the following WebGPU-related works, none of which is an adoption census:

- **"What Browsers Do in the Shaders: A Measurement Study of WebGPU Privacy" (2606.26412)**: measures
  shader-based fingerprinting on live sites that use WebGPU — a *runtime behavior* study of sites
  already using the API, not a census of which projects integrate it.
- **"Characterizing WebGPU Dispatch Overhead for LLM Inference …" (2604.02344) and follow-ups
  (2608.08730)**: microbenchmark WebGPU dispatch on chosen engines (web-llm-class workloads) across
  vendors/browsers — *performance* characterization, adoption assumed.
- **WebLLM (2412.15803)** and other WebGPU systems (Llamas-on-the-Web 2605.20706; Visionary
  2512.08478): *build on* WebGPU and assume it — system papers, not measurements.
- **DarthShader (fuzzing WebGPU shader translators)** and **WebGPU-SPY (GPU cache attacks)**:
  robustness/security studies of the browser implementation.
- This journal's census family (Consensus #63, eBPF #65, PQC #61, Multi-Agent #57, MCP #68):
  source-level adoption censuses of other technologies — none measures a web-platform API, and none
  can observe the web-unique *progressive-enhancement fallback* morphology this paper introduces.

The blank is the **integration side**: which top web open-source projects verifiably adopt WebGPU —
through the raw API, through an engine's WebGPU renderer, or through an execution-provider string —
and how that adoption stratifies by web-software domain, role (render vs compute), and fallback
structure. This paper fills that blank with the census methodology validated across this journal's
family, extended with three instruments the family has not needed before: (a) a **WebGL baseline
channel** giving every corpus repository a GPU-API state (WebGL-only / WebGPU / dual), so the
WebGL→WebGPU migration question is answered *within the same corpus* rather than by cross-census
comparison; (b) a **mediation stratification** separating raw-API adoption from engine-mediated and
execution-provider adoption (the carrier question, H2); and (c) a **fallback-morphology instrument**
counting WebGPU/WebGL dual-renderer structure (H3).

## 2. Related Work

We compare against the concrete works above plus two adjacent literatures:

1. **WebGPU measurement studies (2606.26412, 2604.02344, 2608.08730)** — measure behavior/perf of the
   API on author-chosen workloads/sites. *Difference*: we census the population of web OSS projects;
   our unit of analysis is a repository's integration decision at pinned HEAD, not a runtime trace.
2. **WebGPU system papers (WebLLM 2412.15803, Llamas-on-the-Web 2605.20706, Visionary 2512.08478)** —
   build applications/engines on WebGPU and thereby demonstrate it works. *Difference*: they are
   adopters, not measurements; we quantify how representative such adoption is (14/174 Tier B = 8.0% —
   and even the flagship web-LLM reaches WebGPU through a WASM runtime rather than the raw API).
3. **This journal's census family (#68 MCP 23.6% AI-concentrated; #65 eBPF 3.4%; #61 PQC 2.0%;
   #63 Consensus 6.9%)** — source-level adoption censuses of protocols/libraries. *Difference*: none
   is a web-platform API; WebGPU is the family's first *capability-gated browser API*, which (i)
   requires feature-detect + graceful degradation (progressive enhancement) rather than plain
   dependency adoption, and (ii) concentrates in the *toolchains that implement it*, not in the
   ecosystems that *speak* it — the protocol-vs-API contrast in §4.2.
4. **Older web-GPU usage measurements (WebGL-era)** — predate WebGPU and measure live-site usage via
   instrumentation; none tracks source-level integration or the WebGL→WebGPU migration in code.
5. **Browser-platform adoption analyses by vendors** — anecdotal engine/changelog claims; not
   population statistics (the gap this paper fills).

## 3. Method

### 3.1 Corpus construction (182 repos, head-SHA-pinned)

Population: **web-runtime software** — browser/Electron/web-technology products (JavaScript/
TypeScript-first), web frameworks/libraries, and wasm/emscripten web targets. Server-hosted
applications, backends, CLIs, and native engines are **excluded**: a server/CLI/native binary cannot
adopt a browser-GPU API in its primary runtime (structurally-zero rows; mirrors the kernel-tree
exclusion of the family's eBPF census #65).

- **Tier A anchors (n=5, by name)**: three.js (115.0k★), Babylon.js (26.0k★), mlc-ai/web-llm (18.7k★),
  huggingface/transformers.js (16.3k★), gpuweb/gpuweb (W3C spec, 5.5k★) — ecosystem anchors expected
  to adopt by construction (used for classifier calibration and the H2 anchor baseline).
- **Negative controls (n=3, by name)**: facebook/react, axios/axios, prettier/prettier — web software
  with zero GPU surface (must classify L0 for both WebGPU and WebGL).
- **Tier B (n=174, 6 strata × 29)**: S1 web 3D graphics (pixi.js, react-three-fiber, PlayCanvas,
  A-Frame, Orillusion, …); S2 data-viz/creative (d3, echarts, p5.js, deck.gl, mapbox-gl, Cesium, …);
  S3 AI-in-web (CopilotKit, tfjs, gpu.js, tesseract.js, SillyTavern, …); S4 web apps/editors (vscode,
  excalidraw, tldraw, monaco-editor, quill, …); S5 web games (Phaser, GDevelop, Excalibur, kaplay,
  Biomes, …); S6 web infrastructure (react, vue, next.js, vite, antd, mui, zustand, …).

Strata were populated by **domain topic queries only** (e.g. `topic:3d-engine stars:>=2000`,
`topic:data-visualization …`) — never outcome-gated queries (no `topic:webgpu` population query:
sampling on the dependent variable would inflate adoption). Selection: archived and curated/
knowledge/demo/star-farm repos excluded; non-web languages require explicit web keywords (Rust is
admitted with web/wasm signals); cross-domain hits were remapped to their semantically-correct stratum
via a documented REMAP list (e.g. Phaser→S5, deck.gl/Mapbox→S2, tfjs→S3); anchors and negatives
assignable by name only (family rule). Full exclusion/remap log: `tierb_stats71.txt`. Every corpus
repo was pinned to its default-branch HEAD commit at census time (2026-09-02) — all 182 trees fetched
recursively at pinned HEAD (100% coverage; no truncation).

Language mix (all 182): TypeScript 102, JavaScript 70, Vue 4, HTML 2, Shell/Svelte/PureScript 1
each, and one unset (gpuweb — the spec repository); 94% are TypeScript or JavaScript. Star ranges
per stratum: S1 3.4k-48k, S2 7.2k-114k, S3 8.7k-44k, S4 16k-190k, S5 0.9k-40k (web games are
genuinely long-tail), S6 40k-211k.

### 3.2 Signal dictionary (4 channels) and classifier

WebGPU is a browser API: adoption evidence lives in **source** (unlike server protocols, there is no
"binary dependency" equivalent). The dictionary (`wg_signal_dict_v1.md`) defines four channels:

- **C1 — raw API usage (primary)**: `navigator.gpu` (the only browser WebGPU entry — decisive),
  `requestAdapter`, `requestDevice`, `GPUDevice`/`GPUAdapter`, pipeline creation
  (`createShaderModule`/`createComputePipeline`/`createRenderPipeline`), `dispatchWorkgroups`
  (compute role), `beginRenderPass` (render role), WGSL shader modules feeding `createShaderModule`.
- **C2 — engine-mediated adoption (carrier, H2)**: the app reaches WebGPU *through* an engine —
  three.js `WebGPURenderer`, Babylon.js `WebGPUEngine`, pixi.js v8 GPU renderer selection,
  engine `'webgpu'` preference/`webgpu` config strings, or an **execution-provider string**
  (`webgpu` EP of ONNX Runtime / transformers.js) / WASM-runtime GPU detection
  (web-llm `tvmjs.detectGPUDevice()`).
- **C3 — manifests (weak)**: `@webgpu/types` (ambient TS types), `@webgpu/glslang` etc. — type-only
  devDependency → L1 at most unless C1 usage is present (mirror of the family's types-only rule).
- **C4 — WebGL baseline (NOT adoption; the H1 denominator)**: three.js `WebGLRenderer`,
  `canvas.getContext('webgl'|'webgl2')`, `WebGLRenderingContext`/`WebGL2RenderingContext`, WebGL
  engine-default renderers. Every repo receives a GPU-API state from C4 ∪ {C1,C2}.

**Classifier levels**: **L0** no credible signal (README/spec text, type-only dep, demo/test code,
WebGL-only, gpuweb-as-spec); **L1** weak signal without verified source integration (engine dep
present but no WebGPU renderer selection; `@webgpu/types` only); **L2** verified integration — raw
`navigator.gpu` usage chain **or** engine/EP-mediated WebGPU selection in production source.

### 3.3 Noise dictionary (10 rules, committed)

1. **demo/toy downgrade**: examples/, playground, sandbox, storybook, tutorial code using WebGPU →
   not app integration (e.g. Tres.js lab demos, tldraw shader templates).
2. **spec/defines ≠ adopts**: gpuweb/gpuweb mentions the API everywhere by definition — L0-as-adopter
   (observer rule from #68 lighthouse/CDP; calibrates text-hit-vs-integration).
3. **WebGL-only ≠ WebGPU**: `getContext('webgl2')`, WebGLRenderer alone → baseline row, L0 for WebGPU.
4. **type-only devDep**: `@webgpu/types` in devDependencies only → L1 max.
5. **test-only**: *.test.*/*.spec.*/WPT/mocking GPU → not adoption.
6. **vendored/3rd-party**: GPU code under vendor/, third_party/ → verify ownership.
7. **engine dep ≠ engine choice**: three/Babylon dependency alone (or only in examples/) without C2
   selection → L0/L1 (zustand/boardgame.io/miniplex three-in-examples demoted).
8. **README/marketing**: bare WebGPU mention → not a signal.
9. **star-farm/name rule** (family): membership by NAME list; anchor/negative names never via search.
10. **codegen/wasm wrapper**: the app uses a WASM binary whose WebGPU path lives inside the runtime →
    adoption judged by the app's own API usage (web-llm: zero `navigator.gpu` in TS = mediated, not raw).

### 3.4 Gold standard (single annotator, 2 passes — disclosed)

Pass 1 (R147-R148): evidence gathered by path prescreen from recursive trees, manifest scans
(@webgpu/* 8 repos; WebGPU-capable engine deps 27 repos), and content probes at pinned HEAD — the
adjudicated classifier v1 found 13 Tier B L2. Pass 2 (R149, gold): every positive re-verified by
re-fetching decisive files at pinned HEAD and re-grepping; L1 repos and 6 L0 controls re-checked by
repo-scoped code search for `navigator.gpu` (expect 0 real hits). **Outcome: one substantive
correction** — microsoft/vscode moved L1→L2 after gold's code search found raw `navigator.gpu` in
`src/vs/editor/browser/gpu/` (GPU-accelerated editor viewport rendering: gpuDisposable.ts,
rectangleRenderer.ts, viewLinesGpu.ts — production code, not demo), missed by pass 1's single-file
probe (gpu.ts/atlas.ts had no raw usage). This is a genuine pass-2 discovery (single-annotator
2-pass protocol working as intended); all other positives re-confirmed; gpuweb/galacean/tres/deck.gl
kept L1; 6/6 L0 controls clean; NEG 3/3 dual-L0 (classifier not flag-happy); anchors 4/5 L2 (gpuweb =
spec). Classifier v2 incorporates the vscode correction.

## 4. Results

### 4.1 Headline adoption and the WebGL migration (H1) — CONFIRMED

**14/174 Tier B repositories (8.0%, Wilson 95% CI [4.9%, 13.1%]) verifiably adopt WebGPU.** WebGL is
still the majority GPU API: 48 Tier B repos (27.6%) ship WebGL renderers, of which 37 are WebGL-only;
among the 51 GPU-API-using Tier B repos, **WebGPU holds 27.5% and WebGL 72.5%** — two years after
cross-browser availability, the migration to WebGPU is far from complete at the source level.

Adoption is concentrated in the web-3D-graphics stratum: S1 7/29 = 24%, vs S3 (AI-web) 10% and
S2/S4/S5/S6 3% each (Fisher S1-vs-rest p = 0.0021; anchors-vs-TierB p = 3.5e-4). The graphics stratum
density (24%) is 3x the corpus average (8%) and up to 8x the non-graphics 3% strata — WebGPU adoption
tracks *where GPU work is the product*
(3D engines, renderers), not where web software generally lives. Notably, the AI-web stratum is *not*
elevated (10% vs 8% corpus, p = 0.46) — in sharp contrast to this journal's MCP census (#68), where
AI strata were 4.6x the general rate (p = 1.35e-4). Protocols diffuse through the ecosystems that
speak them; a platform GPU API diffuses through the toolchains that implement it (S1 engines) — the
protocol-vs-API adoption contrast (§4.2).

Flip sensitivity: the Tier B rate would need 36+ re-annotations to even reach 28.7%, and the Wilson
upper bound stays below 50% up to k=75 (i.e. the "WebGPU is not a majority of web OSS" claim is
robust to 61+ flips); GPU-user parity (WebGPU ≥ 50% of GPU users) would need ≥12 WebGL-only→dual
flips or ≥23 L0→WebGPU flips — all far beyond plausible adjudication error, since the gold pass
re-verified every positive at pinned HEAD. The S1 concentration survives ≥3 S1 L2→L0 flips (p stays
<0.05 through 2 flips, crosses at 3). If all 3 remaining Tier B L1 repos (deck.gl/galacean/tres —
gold-verified zero raw usage) were actually L2, the rate is 17/174 = 9.8% CI [6.2%, 15.1%] — same
conclusion.

### 4.2 Raw-API adoption is an engine/toolchain phenomenon; apps adopt mediated or stay WebGL (H2) — REFINED

The registered framing "apps will call navigator.gpu" does not describe 2026 adoption. Among the 14
Tier B adopters:

- **11 go raw**, in three shapes: engines/renderers that implement their own WebGPU backend
  (Orillusion, pixi.js, PlayCanvas engine, p5.js, melonJS); compute/ML toolchain backends
  (tensorflow.js tfjs-backend-webgpu, gpu.js); and raw feature-detect integrations by products whose
  GPU work is direct (PlayCanvas Supersplat's `navigator.gpu` probe, Rezmason/matrix, vscode's GPU
  viewport, fiftyone's WebGPU waveform viz + three.js pickers). Raw `navigator.gpu` usage is the
  signature of a repository whose *product is GPU infrastructure*.
- **3 go mediated** — A-Frame and the architectural editor select three.js `WebGPURenderer`;
  remotion ships a three-WebGPU canvas + whisper-webgpu (transformer-webgpu EP). These are the
  app-level adopters: they adopt *through* a carrier engine.
- **The flagship AI anchors are mediated too**: web-llm — the archetypal in-browser LLM — contains
  **zero `navigator.gpu` in its TypeScript source**; its entire WebGPU path lives inside a WASM
  runtime reached via `tvmjs.detectGPUDevice()` (noise rule 10). transformers.js selects the ONNX
  Runtime `webgpu` execution provider. The browser-AI wave's GPU usage is EP/WASM-mediated, not raw.
- **Of the 26 Tier B repos whose scanned manifests carry a WebGPU-capable engine dependency
  (three/@babylonjs/core/pixi.js/playcanvas — committed manifest scan), only 7 are WebGPU L2 — and
  2 of those (pixi.js, PlayCanvas engine) are the engines themselves**; among the 24 app-level
  dependents only 5 select WebGPU (A-Frame, the architectural editor, Supersplat, remotion,
  fiftyone's 3D views) while the rest (blockbench, model-viewer, Biomes, git-city, 3d-force-graph,
  chili3d, Online3DViewer, CubeCity, react-three-fiber …) ship the engine and stay WebGL-default.
  Most applications — even 3D ones — either have not chosen WebGPU or reach it only when their
  engine offers it as an option.

The registered H2 "raw API is rare outside compute/AI tooling" is refined: raw usage is rare outside
**engine-implementers**, and even AI tooling reaches WebGPU mediated (EP/WASM). The carrier hypothesis
holds in the strong sense: WebGPU diffuses as an engine/EP capability, not as an app-level API.

### 4.3 Roles, stratum split, and the fallback morphology (H3) — DIRECTIONAL

Roles among the 14 adopters: render 10, compute 2 (tfjs, gpu.js — AI-toolchain compute-only),
both 2 (Rezmason/matrix, remotion). Compute usage is confined to ML/creative toolchain adopters in S3
+ S1 showcase; render usage dominates graphics/games/editors strata — consistent with the registered
role-by-stratum split (sample too small for a formal test; directional, disclosed).

**The morphology finding is the strongest H3 result: 11/14 (79%) of WebGPU adopters also ship a
WebGL renderer path.** Dual-renderer structure — feature-detect WebGPU, degrade to WebGL — is the
dominant production pattern (e.g. A-Frame's scene switches between three.js WebGPURenderer and
WebGLRenderer; pixi/PlayCanvas/p5/melonJS maintain both backends). This is the web-platform adoption
morphology no server-side census can observe: no kernel/protocol technology degrades gracefully, so
every prior family census (eBPF, MCP, consensus, PQC) measures binary adoption; WebGPU adoption is
structured as *progressive enhancement*, with even the adopters keeping their WebGL fallback live.

### 4.4 Cohort state (H4) — cross-sectional, disclosed

All 14 Tier B adopters and all 5 anchors were live (archived=false) at the census snapshot
(2026-09-02). Survival/longitudinal analysis is future work (see §5); consistent with the family's
practice, H4 is reported cross-sectionally only.

### 4.5 Controls

- **NEG 3/3 dual-L0**: react/axios/prettier show zero WebGPU and zero WebGL (classifier not
  flag-happy; WebGL channel not over-firing).
- **Anchor calibration 4/5 L2**: three.js/Babylon raw (they implement WebGPU backends), web-llm/
  transformers.js mediated (EP/WASM) — anchors behave as expected and are themselves the H2 carriers.
  gpuweb = spec = L0-as-adopter (noise rule 2).
- **L0 controls 6/6 clean** (vue, antd, d3, chartjs, excalidraw, marktext: zero `navigator.gpu`).

## 5. Threats to validity and why this is still worth publishing

1. **Population definition**: web-runtime software excludes server/CLI/native — a browser-GPU API
   cannot be adopted there, but the exclusion is judgment-based at the margins (e.g. Electron apps
   counted as web-tech: vscode's inclusion is deliberate — it is a web-tech product with a real
   WebGPU path). The exclusion log is committed and auditable.
2. **Snapshot single-point-in-time**: head-SHA pinning (2026-09-02) gives a reproducible but
   cross-sectional census; adoption trajectories (H4) are future work. This is disclosed rather than
   implied longitudinal.
3. **Single annotator**: two passes with one annotator, disclosed; the pass-2 vscode discovery shows
   the protocol finds its own errors, but inter-annotator reliability was not measured.
4. **Code-search completeness**: some repos' evidence came from repo-scoped code search, which is
   rate-limited and may miss matches in files GitHub does not index; mitigated by recursive-tree path
   prescreen (100% tree coverage) + manifest scans + content probes of every positive at pinned HEAD.
5. **Engine-mediated detection**: an app adopting WebGPU through an engine's *runtime default*
   (no explicit 'webgpu' string) would be classified L1 (weak) or L0 — we count *visible* renderer
   selection only; the mediated rate (3) is a lower bound on app-level adoption. Disclosed.
6. **Young API**: WebGPU cross-browser only since 2025 — the 8.0% rate is a 2026 snapshot of an API in
   its second cross-browser year; the paper's value is precisely that it measures this early phase with
   a reproducible instrument (the migration baseline + morphology instruments remain reusable as the
   API matures).
7. **Why still worth publishing**: (i) it is the first census of the WebGL→WebGPU migration at the
   source level, giving the platform/engine/AI-in-browser community the population statistics the
   "WebGPU replaces WebGL" claim has lacked; (ii) it introduces constructs the family (and the web
   measurement literature) lacks — the within-corpus WebGL baseline, the mediation stratification, and
   the fallback-morphology instrument; (iii) the protocol-vs-API contrast against #68 (AI-elevated vs
   graphics-elevated adoption) is a cross-census regularity no single-domain study can establish.

## 6. Reproducibility

`bash reproduce.sh` (committed in papers/issue-71/) rebuilds all headline numbers offline from
committed snapshots (corpus JSON + trees + evidence + gold), byte-identical to `expected_output/`.
`validate.py` runs cross-file consistency checks (corpus↔classifier↔gold; strata quotas; NEG/anchor
purity). `trace_check.py` traces every headline number to its committed artifact (0 gaps). Corpus
pinning, evidence probes, and classification used the GitHub API at census time; the committed
snapshots freeze their outputs so reproduction is network-free and deterministic.

## References

1. 2606.26412 — "What Browsers Do in the Shaders: A Measurement Study of WebGPU Privacy" (privacy
   measurement of live WebGPU sites; difference: no population census).
2. 2604.02344 / 2608.08730 — "Characterizing WebGPU Dispatch Overhead for LLM Inference …" (perf
   microbenchmarks; difference: adoption assumed, not measured).
3. 2412.15803 — WebLLM (system built on WebGPU; difference: an adopter; we measure adoption
   population-wide and find even WebLLM-class AI tooling is EP/WASM-mediated).
4. 2605.20706 — Llamas-on-the-Web (WebGPU LLM system; difference: system, not census).
5. 2512.08478 — Visionary (WebGPU Gaussian splatting; difference: system, not census).
6. This journal's family: #68 MCP in the Wild (23.6% AI-concentrated adoption), #65 eBPF in the Wild
   (3.4%), #61 PQC (2.0%), #63 Consensus (6.9%), #57 Multi-Agent — source-level census methodology +
   the cross-census baselines this paper contrasts against.

## Appendix A — Gold-standard Tier B L2 repos (14) by stratum, role, and evidence

| repo | stratum | role | evidence | WebGL path |
|---|---|---|---|---|
| Orillusion/orillusion | S1 | render | raw (Context3D.ts) | yes |
| pixijs/pixijs | S1 | render | raw (GpuDeviceSystem) | yes |
| playcanvas/engine | S1 | render | raw (webgpu-graphics-device) | yes |
| playcanvas/supersplat | S1 | render | raw (index.ts) | yes |
| Rezmason/matrix | S1 | both | raw (main.js) | — |
| aframevr/aframe | S1 | render | mediated three WebGPURenderer | yes |
| pascalorg/editor | S1 | render | mediated three WebGPURenderer | yes |
| processing/p5.js | S2 | render | raw (p5.RendererWebGPU) | yes |
| tensorflow/tfjs | S3 | compute | raw (tfjs-backend-webgpu) | yes |
| gpujs/gpu.js | S3 | compute | raw (web-gpu kernel) | yes |
| voxel51/fiftyone | S3 | render | raw (waveform-gpu + three pickers) | yes |
| microsoft/vscode | S4 | render | raw (editor/browser/gpu) | — |
| melonjs/melonJS | S5 | render | raw (webgpu_renderer.js) | yes |
| remotion-dev/remotion | S6 | both | mediated (three webgpu + whisper EP) | yes |

(dual-renderer: 11/14 = 79%; WebGL path = WebGLRenderer/getContext('webgl') present in repo.)
