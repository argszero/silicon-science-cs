# Issue #71 — WebGPU signal dictionary v1 (classifier channels)

2026-09-02, R147. Mirrors #68 mcp_signal_dict_v1.md / #65 bpf dict structure. **Population =
web-runtime software** (JS/TS web-tech); adoption evidence lives in SOURCE (WebGPU is a
browser API, no server-side binary dep). Channels ordered by evidential strength.

## Channel 1 — raw API source usage (primary, unambiguous)

| signal | pattern (exact-ish, NO short bare words) | evidence |
|---|---|---|
| browser entry point | `navigator.gpu` (the ONLY browser WebGPU entry — unambiguous) | L2 core |
| adapter request | `requestAdapter` (always follows navigator.gpu) | L2 core |
| device request | `requestDevice` | L2 |
| device/adapter ids | `GPUDevice`, `GPUAdapter`, `new WebGPUDevice` | L2 (contextual) |
| pipeline creation | `createShaderModule`, `createComputePipeline`, `createRenderPipeline`, `createComputePipelineAsync` | L2 |
| compute submit | `dispatchWorkgroups`, `dispatchWorkgroupsIndirect` | L2 (compute role) |
| render submit | `beginRenderPass`, `beginComputePass`, `GPURenderPassEncoder` | L2 (render role) |
| WGSL shader modules | `*.wgsl` files / `wgsl:` strings / `@compute`, `@vertex`, `@fragment` entry attrs | L2 (must feed createShaderModule) |
| buffer/texture | `GPUBuffer`, `createBuffer`, `createTexture`, `queue.submit` | contextual |
| type pkg import | `import ... from '@webgpu/types'` (ambient types) | L1 (types-only possible) |

`navigator.gpu` alone is decisive (WebGPU-only API; WebGL has no navigator.gpu).
`requestAdapter`/`requestDevice` never appear outside WebGPU code.
WGSL strings alone (e.g. `.wgsl` asset) without createShaderModule → weak.

## Channel 2 — engine-mediated adoption (carrier, H2 core)

WebGPU reached THROUGH an engine abstraction. The APP does not call navigator.gpu; the
engine does. Carrier evidence = engine renderer-selection API for WebGPU:

| carrier | signal |
|---|---|
| three.js | `WebGPURenderer` (import from `three/webgpu` or `THREE.WebGPURenderer`) |
| Babylon.js | `WebGPUEngine` (`@babylonjs/core/Engines/webgpuEngine`, `new WebGPUEngine(canvas)`), `engine.setWebGPU` |
| pixi.js v8 | `autoDetectRenderer` w/ `preference: 'webgpu'`, `PIXI.WebGPURenderer`, `WebGPURenderer` |
| PlayCanvas | `WebglGraphicsDevice` vs `WebGPU` graphics device option, `graphicsDevice` type gpu |
| generic | `isWebGPUAvailable()`, `webgpu: true` config, `.webgpu` renderer key, `WebGPU` engine-string option |
| engine package | `three`, `@babylonjs/core`, `pixi.js` (v8+), `playcanvas` — as *carriers* only when combined w/ C2 selection signals |

Carrier signal WITHOUT raw-API hit = **engine-mediated adoption (H2 carrier path)**.
App dep on three + only `WebGLRenderer` usage = NOT WebGPU (WebGL baseline row).

## Channel 3 — dependency / type manifests (weak, prescreen)

- `@webgpu/types` in package.json — devDep/type-only → L1 at most unless C1 raw hit
  (mirrors #61 types-only rule)
- `@webgpu/glslang`, `@webgpu/shader-preprocessor`, `wgpu-matrix`, `webgpu-utils`
  (adjacent libs — presence suggests WGSL work)
- no engine package alone = adoption (carriers need C2 selection signal)

## Channel 4 — WebGL BASELINE (H1/H3 within-corpus comparison — NOT adoption)

- three.js `WebGLRenderer` (import `three` + `new WebGLRenderer`)
- `canvas.getContext('webgl')` / `('webgl2')`, `WebGLRenderingContext`, `WebGL2RenderingContext`
- pixi v7/v8 WebGL renderer, Babylon `Engine` (default WebGL), engine `webgl` option
- WebGL usage counts = baseline denominator for H1 migration question
  (within-corpus WebGL vs WebGPU share; #68 camera-ready lesson: composition-explicit)

## Classifier levels

- **L0**: no credible signal; README/spec-text-only mention; dep only in devDeps/types;
  demo/example/test code only; WebGL-only; spec/defines-the-API (gpuweb).
- **L1**: manifest/weak signal without verified source integration (e.g. @webgpu/types
  devDep, engine dep present but no WebGPU renderer selection found, feature-detect only).
- **L2**: verified integration — raw `navigator.gpu` usage chain in production source,
  OR engine-mediated renderer selection (WebGPURenderer/WebGPUEngine/webgpu preference)
  in production code. Role-subtyped (below).

## Role classes (H3) — per L2 repo

- **render**: pipeline/rendering usage (createRenderPipeline, render passes, engine
  WebGPURenderer/WebGPUEngine, render-target usage)
- **compute**: compute-only usage (createComputePipeline, dispatchWorkgroups, ML
  inference, GPGPU — e.g. web-llm/transformers.js)
- **both**: render + compute present
- H3 tests: compute clusters in AI strata (S3) via raw API; render clusters in
  graphics/games strata via engine mediation (S1/S5); role × stratum matrix.

## Fallback / progressive-enhancement morphology (web-unique, H3)

- `navigator.gpu === undefined` check, `isWebGPUAvailable()`, try/catch around
  requestAdapter, feature-detect then **fallback to WebGL renderer** — classify:
  - WebGPU feature-detect + WebGPU path used = adopter w/ fallback (dominant pattern?)
  - WebGPU feature-detect ONLY, always WebGL = NOT adopter (L0) — WebGL-dominant
  - no detect, direct navigator.gpu = adopter, no fallback (rare, risky)
- capture `WebGLRenderer` fallback co-occurrence in L2 repos (H3 fallback-dominance claim)

## Noise rules

1. **demo/toy downgrade**: examples/, playground, sandbox, .gallery, storybook, docs/,
   tutorial code using WebGPU → not app integration (mirror #65/#68 fixture rule).
2. **spec/defines ≠ adopts**: gpuweb/gpuweb (W3C spec + WPT tests) mentions the API
   everywhere by definition → L0 as adopter (observer rule from #68 lighthouse/CDP).
   Calibrates "text hit ≠ integration".
3. **WebGL-only ≠ WebGPU**: getContext('webgl'), WebGLRenderer alone → baseline row, L0
   for WebGPU.
4. **type-only devDep**: @webgpu/types in devDependencies only (ambient TS types), no
   raw usage → L1 max (mirror #61).
5. **test-only**: *.test.*, *.spec.*, WPT, __tests__, mocking GPU → not adoption.
6. **vendored/3rd-party**: GPU code under vendor/, third_party/ → verify ownership.
7. **engine dep ≠ engine choice**: three/Babylon dep alone without C2 selection → L0/L1.
8. **README/marketing**: bare WebGPU mention in README → not a signal.
9. **star-farm/name rule** (family): membership by NAME list; anchors by NAME.
10. **codegen/wasm wrapper**: wasm-bindgen GPU glue / prebuilt wasm shader packs — the
    web app uses the wasm, not the API → verify who calls navigator.gpu.

## Calibration anchors (Tier A) — expectations

- mrdoob/three.js — **L2 render** (WebGPURenderer in src; but note: engine repo ships
  BOTH WebGLRenderer + WebGPURenderer → three itself uses raw API for its WebGPU path;
  for an *engine* repo, its renderers are its product. Classify three.js L2 by raw API
  usage inside its WebGPU renderer implementation.)
- BabylonJS/Babylon.js — **L2 render** (WebGPUEngine in packages/dev/core/src/Engines)
- mlc-ai/web-llm — **L2 compute** (raw navigator.gpu for LLM inference)
- huggingface/transformers.js — **L2 compute** (WebGPU backend for ML ops)
- gpuweb/gpuweb — **L0-as-adopter** (defines the API + WPT tests; noise rule 2 calibrator)
- NEG react/axios/prettier — **L0** (zero GPU surface)

## Notes for scan implementation

- Corpus = 182 web repos (TS 101/JS 70), all head_sha-pinned (R146).
- Path prescreen from recursive trees (webgpu-ish paths, .wgsl files, engine webgpu
  files, manifest paths) + content probes at pinned HEAD; code-search API as optional
  confirm step (chunk 12 + sleep 8s per #68 H3 lesson).
- Manifest fetch: package.json nested (monorepos) for @webgpu/*, three, @babylonjs/*,
  pixi.js, playcanvas, engine deps (mirror #68 MAX_MANIFESTS root-first).
- engines that carry WebGPU (three/Babylon/pixi/playcanvas/galacean/orillusion) appear
  IN Tier B too (pixi S1, galacean S1...) — their own adoption judged like anchors;
  but apps USING them judged by C2 selection signals only.
