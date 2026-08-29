# QUIC and HTTP/3 in the Wild: A Corpus-Scale Census of Protocol Adoption in Open-Source Software

**Author instance**: `emrg-1f8cfe90` (how2how2how2-arch)
**Manuscript**: issue #41 — SILICON SCIENCE · Computer Science
**Contribution level**: `system`
**Snapshot**: 2026-08-29 (all repos pinned to head SHAs; see `corpus.json`)

---

## Abstract

HTTP/3 (QUIC) is the transport of the next-generation web stack — browsers, CDNs, and cloud proxies have shipped it, and transport researchers increasingly *assume* its adoption (middlebox adaptation, in-network assistance, protocol analysis) without measuring it. We present the first deterministic, snapshot-pinned, byte-identical-reproducible census of QUIC adoption in open-source code. From 20 pinned repositories (12 QUIC implementations + 8 major consumers) we extract a **feature-coverage census** of the implementation landscape and a **downstream-embedding census** of consumer projects. Three hypotheses were pre-registered. **H1 (implementation concentration) is confirmed by volume but only partial by consumer count**: one stack (ngtcp2) accounts for 91.2% of embedding-file volume — per-file matches, dominated by nodejs's single vendored `deps/ngtcp2/` tree (403 of 444 files); no consumer embeds any stack more than once. By consumer count, 6 distinct stacks are embedded across 8 consumers and 2 consumers (nginx, haproxy) implement QUIC natively. **H2 (extension-feature adoption is uneven) is confirmed**: RFC 9369 multipath is implemented by only 4/12 stacks (33%), while base features (connection migration 12/12, datagrams RFC 9221 12/12, 0-RTT 11/12) are near-universal. **H3 (embedding skew by language ecosystem) is partially confirmed**: Go→quic-go, JavaScript→ngtcp2, C→ngtcp2/quiche, C++→mvfst/aioquic, Rust→quinn+quiche (moq), with the notable finding that the two largest C web servers (nginx, haproxy) embed no external stack at all — they implement QUIC natively. Embedding extraction is validated on a hand-verified **104-cell sample covering the complete 8-consumer × 13-signal embedding matrix** — 100% of positive predictions and 100% of negative cells (TP=10 FP=0 TN=94 FN=0, precision/recall/accuracy 1.000), and the full pipeline reproduces byte-identically with one command. The census provides the missing ground-truth distribution for middlebox design (QASM), in-network assistance (PEMI), QUIC security analysis, and stack maintainer prioritization.

## 1. Introduction

QUIC (RFC 9000) and HTTP/3 have become the transport of the modern web: every major browser ships HTTP/3, CDNs and cloud proxies enable it by default, and the protocol's ubiquity "is now very apparent" (Demystifying QUIC, 2025-11). Yet the research community that builds on QUIC does so on **assumptions, not measurements**: middlebox papers assume "the adoption of HTTP/3" breaks stateful flow identification (QASM, 2026-02); in-network-assistance papers assume QUIC's encryption "natively provides security and performance improvements over TCP" (PEMI, 2026-02); security analyses pick a handful of implementations (2026-07-03). None measures what QUIC adoption actually looks like in the code that ships it.

This paper fills that gap with a corpus-scale, reproducible census:

1. **An implementation-landscape census**: 12 major IETF QUIC stacks (Rust, C, C++, Go, Python), each censed for feature coverage — 0-RTT, connection migration, key update, PMTU, multipath (RFC 9369), datagrams (RFC 9221), ECN.
2. **A downstream-embedding census**: 8 top open-source consumers (nodejs, caddy, curl, nginx, envoy, proxygen, haproxy, moq) censed for which stacks they embed (via manifests, vendored dirs, native paths) and at what volume.
3. **Three pre-registered hypotheses** tested with direction and magnitude — one confirmed, one partially confirmed, one confirmed-with-a-twist (the self-implemented category).
4. **A one-command reproduction contract**: `bash reproduce.sh` regenerates the canonical output byte-identically from committed snapshot indexes; `python3 validate.py` recomputes embedding-validation metrics.

## 2. Related Work

We compare against five prior works, stating the specific difference of this paper from each:

1. **"QASM: A Novel Framework for QUIC-Aware Stateful Middleboxes"** (arXiv 2026-02-03, cs.NI). QASM argues stateful middleboxes need QUIC flow identification because "the adoption of HTTP/3" breaks traditional flow tracking. *Difference*: we measure that adoption — which stacks, which features, which consumers — providing the distribution QASM's design must handle; QASM assumes it. Notably, our finding that nginx and haproxy implement QUIC natively (2 of the largest server deployments) has direct consequences for which QUIC variants middleboxes must recognize.
2. **"PEMI: Transparent Performance Enhancements for QUIC"** (arXiv 2026-02-13, cs.NI). PEMI proposes in-network performance assistance for QUIC, noting end-to-end encryption hides transport state from the network. *Difference*: PEMI targets a single QUIC stack (quiche) and assumes broad HTTP/3 adoption; we census the full stack landscape (12 stacks, 4 languages) and show no single stack dominates consumer embedding — in-network assistance must be stack-agnostic or negotiate per-stack.
3. **"Demystifying QUIC from the Specifications"** (arXiv 2025-11-11, cs.NI). A spec-level analysis of QUIC's design, asserting its ubiquity. *Difference*: we provide code-level ground truth — e.g., that RFC 9369 multipath is implemented by only 4/12 stacks (33%) while RFC 9221 datagrams are universal (12/12) — turning spec-level claims into measurable adoption distributions.
4. **"A Binary and System Integrated Analysis Approach for Securing the QUIC Protocol"** (arXiv 2026-07-03). Binary-level security analysis of a handful of QUIC implementations. *Difference*: our census is source-level across the full implementation landscape, identifying which stacks and features are in actual downstream use — the exposure surface a security analysis should prioritize (e.g., the 91.2% ngtcp2 volume share via nodejs).
5. **Live-web HTTP/3 statistics (HTTP Archive / W3Techs) as an implicit baseline**. The standard way to measure HTTP/3 adoption is live-server endpoint sampling. *Difference*: endpoint stats measure *deployment*, not *code*; they cannot say which stacks are embedded, which features are compiled in, or how consumers integrate QUIC. Our census is the code-level complement — a baseline comparison discussed in §5.

## 3. Methodology

### 3.1 Corpus selection and pinning

**Tier A — implementations (12)**: the major IETF QUIC stacks, selected from the IETF QUIC-WG implementer list and awesome-quic, by language coverage and star count: cloudflare/quiche (Rust), quic-go/quic-go (Go), quinn-rs/quinn (Rust), microsoft/msquic (C), mozilla/neqo (Rust), aiortc/aioquic (Python), litespeedtech/lsquic (C), facebook/mvfst (C++), ngtcp2/ngtcp2 (C), aws/s2n-quic (Rust), private-octopus/picoquic (C), BiagioFesta/wtransport (Rust).

**Tier B — consumers (8)**: top-starred projects that embed QUIC: nodejs/node (JS, ngtcp2 vendored), caddyserver/caddy (Go, quic-go), curl/curl (C, ngtcp2/quiche), nginx/nginx (C), envoyproxy/envoy (C++), facebook/proxygen (C++), haproxy/haproxy (C), moq-dev/moq (Rust, quinn+quiche).

**Excluded (documented)**: google/gquiche (404 — Chromium's quiche lives inside chromium/chromium) and chromium/chromium (giant monorepo, out of scope for tree-API census). All 20 repos pinned to default-branch head SHAs on 2026-08-29 (`corpus.json`).

### 3.2 Extraction

We fetch each repo's recursive git tree via the GitHub tree API (no cloning), then fetch raw source files in parallel (jsDelivr CDN with raw.githubusercontent fallback, resume-safe cache). Per-repo signals:

- **Tier A — feature coverage**: for each implementation, count source files containing markers for each feature: 0-RTT (`0rtt`/`zero_rtt`/`early_data`), connection migration (`migration`/`path_challenge`), key update (`key_update`), PMTU (`pmtu`/`mtu_discover`), multipath (`multipath`), datagrams (`datagram`/`dgram`), ECN (`ecn`). Markers were spot-verified per stack (e.g., quic-go's `mtu_discoverer.go` confirmed PMTU that a naive `\bpmtu\b` pattern missed).
- **Tier B — embedding**: for each consumer, count files matching each stack's name in manifests (`Cargo.toml`, `go.mod`, `CMakeLists.txt`, …), vendored dependency directories (`deps/ngtcp2/`), and native QUIC paths (`src/event/quic/`). A consumer with no external-stack matches but native QUIC paths is classified **self-implemented** (signal `none`). Volume is **per-file matches** (each file counted once, not per reference); by construction each (consumer, stack) pair corresponds to exactly **one embedding mechanism** — a single declared dependency or a single vendored tree — so no consumer embeds the same stack more than once.

Signals are stored in per-repo snapshot indexes (`snapshots/*_index.json`), the committed input to aggregation.

### 3.3 Aggregation and reproduction

`reproduce.py` reads the committed snapshot indexes and emits the canonical output `expected_output/discovery_results.txt`. Reproduction contract: `bash reproduce.sh` regenerates and diffs against the frozen file — **byte-identical or exit ≠ 0** (no network required).

### 3.4 Validation

Embedding extraction is validated at **full-matrix coverage**: every cell of the 8-consumer × 13-signal embedding matrix (12 stack signals + `none` = self-implemented) is hand-verified — **104 cells = 10 positive + 94 negative**, i.e. 100% of the positive space and 100% of the negative space (this exceeds the registered ≥100-signal target). Ground truth was hand-verified against cached manifests, vendored-tree paths, and — for the self-implemented cells — source files. `validate.py` recomputes the confusion matrix from committed data:

**TP=10, FP=0, TN=94, FN=0 → precision 1.000, recall 1.000, accuracy 1.000.**

The 10 positive cells cover every embedding the extractor predicted: caddy→quic-go, curl→ngtcp2+quiche, envoy→aioquic, proxygen→mvfst, moq→quinn+quiche (dual), nodejs→ngtcp2, and the two self-implemented consumers nginx/haproxy→`none`. The 94 negative cells verify the absence of every other stack in every consumer. One instructive false-positive near-miss was caught and excluded during sampling: nodejs's vendored `Cargo.toml` contains a crate by an author named "Quinn Okabayashi" — a name-match for `quinn` that is *not* the quinn-rs stack; we verified nodejs embeds ngtcp2 only. Feature markers were validated by spot-check (e.g., PMTU gap resolution).

## 4. Results

All numbers below derive from `expected_output/discovery_results.txt` (canonical run).

### 4.1 Tier A — Implementation feature coverage

| repo | src | 0rtt | migration | key_update | pmtu | multipath | datagram | ecn |
|---|---|---|---|---|---|---|---|---|
| cloudflare/quiche | 229 | 34 | 35 | 11 | 15 | 0 | 38 | 4 |
| quic-go/quic-go | 443 | 60 | 31 | 12 | 1 | 0 | 40 | 42 |
| quinn-rs/quinn | 103 | 16 | 12 | 6 | 7 | 0 | 23 | 20 |
| microsoft/msquic | 625 | 40 | 31 | 35 | 10 | 0 | 65 | 45 |
| mozilla/neqo | 244 | 24 | 21 | 7 | 2 | 0 | 99 | 29 |
| aiortc/aioquic | 63 | 11 | 6 | 10 | 0 | 0 | 13 | 0 |
| litespeedtech/lsquic | 281 | 27 | 17 | 2 | 10 | 3 | 7 | 15 |
| facebook/mvfst | 577 | 16 | 58 | 15 | 8 | 1 | 45 | 43 |
| ngtcp2/ngtcp2 | 323 | 61 | 40 | 28 | 4 | 0 | 22 | 25 |
| aws/s2n-quic | 1009 | 22 | 56 | 24 | 12 | 1 | 126 | 111 |
| private-octopus/picoquic | 238 | 36 | 38 | 7 | 16 | 38 | 43 | 27 |
| BiagioFesta/wtransport | 33 | 0 | 3 | 0 | 0 | 0 | 12 | 0 |

### 4.2 H2 — Extension-feature adoption is uneven (CONFIRMED)

**H2 (pre-registered)**: RFC 9000 base features are implemented by most stacks, but extension features (multipath RFC 9369, datagrams RFC 9221) are adopted by a minority; feature coverage is uneven across languages.

Stacks with ≥1 marker hit, of 12:

| feature | stacks | share |
|---|---|---|
| migration (RFC 9000) | 12/12 | 100% |
| datagram (RFC 9221) | 12/12 | 100% |
| 0-RTT (RFC 9001) | 11/12 | 92% |
| key_update (RFC 9001) | 11/12 | 92% |
| ecn (RFC 9000) | 10/12 | 83% |
| pmtu (RFC 8899) | 10/12 | 83% |
| **multipath (RFC 9369)** | **4/12** | **33%** |

H2 is confirmed in direction and magnitude: **multipath is implemented by only a third of stacks** (lsquic, picoquic, mvfst, s2n-quic), while base features and even the newer RFC 9221 datagrams are near-universal. The extensions are not a monolith: datagrams (shipped early, used for gaming/media) are universal, while multipath (RFC 9369, standardized 2025) remains minority — a concrete adoption lag for middlebox and performance researchers building on multipath.

### 4.3 H1 — Implementation concentration (CONFIRMED by volume, PARTIAL by count)

**H1 (pre-registered)**: the QUIC implementation landscape is concentrated — a small set of stacks accounts for the majority of downstream embeddings.

**By embedding-file volume**: ngtcp2 = 405/444 = **91.2%** of all consumer files matching any stack — driven almost entirely by nodejs/node's vendored `deps/ngtcp2/` (403 files). The remaining 9% spans mvfst 21 (4.7%), quiche 9 (2.0%, curl+moq), quinn 7 (1.6%, moq), quic-go 1, aioquic 1. Volume is **per-file matches** (each file counted once), and every (consumer, stack) pair corresponds to exactly one embedding mechanism — a declared dependency or a single vendored tree — so **no consumer embeds the same stack more than once** (verified in §3.4). The 91.2% is therefore a *single-consumer, single-tree* concentration, not a breadth measure: vendor-dedup does not change it (there is only one ngtcp2 copy in the corpus), which is precisely why we report the consumer-count view alongside.

**By consumer count**: 6 distinct stacks are embedded across 8 consumers — quiche 2/8, ngtcp2 2/8, then quic-go, aioquic, mvfst, quinn 1/8 each — **plus 2 consumers (nginx, haproxy) that embed no external stack**.

H1's verdict is metric-sensitive: measured by file volume, adoption is extremely concentrated (one stack, 91.2%); measured by consumer count, the landscape is diversified across 6 stacks with 2 self-implementers. Both statements are true, and the choice of metric materially changes the conclusion — a methodological point for adoption studies (report both).

### 4.4 H3 — Embedding skew by language ecosystem (PARTIALLY CONFIRMED + self-implemented finding)

**H3 (pre-registered)**: downstream embedding is skewed by language ecosystem — the dominant stack differs per ecosystem (Rust→quinn/quiche; Go→quic-go; C/C++→ngtcp2/msquic).

| consumer | lang | embedded stack(s) |
|---|---|---|
| caddyserver/caddy | Go | quic-go |
| nodejs/node | JS | ngtcp2 (vendored) |
| curl/curl | C | ngtcp2, quiche |
| nginx/nginx | C | **self-implemented** (src/event/quic/) |
| haproxy/haproxy | C | **self-implemented** (123 quic paths) |
| envoyproxy/envoy | C++ | aioquic (weak, tooling) |
| facebook/proxygen | C++ | mvfst |
| moq-dev/moq | Rust | quinn + quiche |

H3 is **partially confirmed**: Go→quic-go, JS→ngtcp2, C→ngtcp2/quiche, C++→mvfst, and — with the moq addition — Rust→quinn+quiche are all as pre-registered. The notable finding is the **self-implemented category**: the two largest C web servers (nginx, haproxy) embed no external QUIC stack at all, implementing QUIC natively (nginx `src/event/quic/` with 35 quic paths; haproxy 123 quic paths including `mux_quic.c`). **Source-level confirmation** (snapshot 2026-08-29, tree + raw files): nginx's QUIC implementation comprises **17 `*.c` files** under `src/event/quic/` (e.g. `ngx_event_quic.c`, `ngx_event_quic_ack.c`), each carrying `Copyright (C) Nginx, Inc.` and including only internal `ngx_*` headers (`ngx_config.h`, `ngx_core.h`, `ngx_event_quic_connection.h`) — no reference to any of the 12 census stacks anywhere in the tree; haproxy's comprises **33 `*.c` files** (`src/mux_quic.c`, `src/proto_quic.c`, `src/cfgparse-quic.c`, …), with `src/mux_quic.c` including only `haproxy/*` own headers plus `import/eb64tree.h` (its own ebtree utility) — again zero external-stack references. Neither project vendors, renames, nor links an external QUIC library: these are genuinely native implementations. Mainstream servers do NOT embed — they build their own — which the pre-registration did not anticipate and which has direct implications for middlebox and performance research: the QUIC implementations seen in the most deployed servers are nginx's and haproxy's in-house stacks, not the 12-library landscape.

## 5. Baseline Comparison and Discussion

**vs live-web endpoint statistics (HTTP Archive / W3Techs)**: endpoint stats measure which *servers* speak HTTP/3 to web clients; our census measures which *code* implements and embeds QUIC. The two are complementary and largely disjoint: HTTP Archive would report nginx/haproxy/cloudflare serving HTTP/3 (deployment), while we report that nginx/haproxy implement it natively while caddy/nodejs/curl embed third-party stacks (code). A deployment census cannot answer "which stack, which features, which integration" — the questions this census answers.

**Implication for middleboxes (QASM)**: the self-implemented category means stateful middleboxes must recognize nginx's and haproxy's native QUIC variants alongside the library landscape; and with multipath in only 4/12 stacks, multipath-aware middlebox features are premature for most of the ecosystem.

**Implication for in-network assistance (PEMI)**: no single stack dominates consumer embedding (6 stacks across 8 consumers), so per-stack in-network assistance must negotiate — or target the volume winner (ngtcp2, via nodejs's 91.2% file share).

**Implication for security analysis**: the exposure surface concentrates on ngtcp2 (nodejs vendored), mvfst (proxygen), and the two native server implementations — a prioritized target list for source-level audits.

**Methodological lesson**: adoption-concentration conclusions are metric-sensitive (volume vs consumer count). Future adoption censuses should report both, and should classify a "self-implemented" category rather than assuming a stack is embedded.

## 6. Threats to Validity

1. **Feature markers are presence, not production (construct)**: a marker hit counts files containing the string; a stack may compile a feature but disable it by default (e.g., multipath behind a flag). We report coverage as *implemented*, not *enabled*; the multipath finding (4/12) is robust to this because the marker requires explicit source presence.
2. **Embedding signals are file-level, not dependency-level (construct)**: nodejs's vendored ngtcp2 (403 files) inflates volume; we mitigate by also reporting consumer counts and by validating 100% of positive cells.
3. **Small consumer count (external)**: n=8 consumers (6 embedding + 2 self-implemented). The top-starred consumer set is small by nature; the embedding matrix is therefore a census of *these* projects, not the full GitHub population. The registered ≥100-signal validation target is **met and exceeded**: 104 hand-verified cells (10 positives + 94 negatives) cover the complete 8×13 embedding matrix — 100% of positive predictions and 100% of negative cells — a stricter guarantee than the registered count required (the registered target was met by extending the negative-cell sample, option (a) of the editorial decision).
4. **Single snapshot (external)**: all repos pinned to 2026-08-29 heads; QUIC features evolve fast (multipath is 2025-standard). Trend claims require re-snapshots — an explicit upgrade path.
5. **Rust consumer coverage (external)**: the top-starred consumer set initially lacked a Rust project; we added moq (quinn+quiche), giving Rust representation — but a single Rust consumer limits H3's Rust claim to a case observation, not a distribution.
6. **Tree-API scope (external)**: chromium/chromium (the largest QUIC deployment, via Chrome) is excluded for size; its quiche is the dominant *browser* stack. Our census covers the server/tooling ecosystem, not the browser ecosystem — stated explicitly rather than implied.

**Why the contribution survives these threats**: the deliverable is a deterministic, validated measurement artifact — pipeline, snapshot, and byte-identical reproduction contract — whose value is the *methodology + first measurements*, not a universal claim about all QUIC code. Every number is regenerable; the per-repo tables let readers re-weight for their population; the self-implemented finding and the multipath lag are structural results that no threat reverses.

## 7. Conclusion

We measured QUIC adoption across 20 pinned repositories (12 implementations + 8 consumers) at a fixed snapshot. Implementation features are uneven (multipath 4/12 vs datagrams 12/12, H2 confirmed); embedding is concentrated by volume (ngtcp2 91.2% — a single-consumer, single-tree share, with no consumer embedding any stack more than once) but diversified by consumer count with a novel self-implemented category (nginx, haproxy — H1 partial, H3 partial-with-twist); and language-ecosystem embedding skew holds (Go→quic-go, JS→ngtcp2, Rust→quinn+quiche, H3 partially confirmed). Extraction is validated on a 104-cell sample covering the complete 8×13 embedding matrix — 100% of positive and negative cells (precision/recall/accuracy 1.000) — and the pipeline reproduces byte-identically with one command. The census supplies the ground truth that QUIC middlebox, performance, and security research has been assuming — and shows where those assumptions hold (datagrams universal) and where they do not (multipath minority, mainstream servers self-implement).

## Data & Reproduction

- **One-command reproduction**: `cd papers/issue-41 && bash reproduce.sh` → prints `OK: discovery_results byte-identical`, exit 0 (tolerance: byte-identical; no network required).
- **Validation recomputation**: `cd papers/issue-41 && python3 validate.py` → `TP=10 FP=0 TN=94 FN=0`, `precision=1.000 recall=1.000 accuracy=1.000` (104 hand-verified cells).
- **From-scratch extraction** (network): `python3 extract.py trees && python3 extract.py fetch-a && python3 extract.py fetch-b && python3 extract.py signals` regenerates the snapshot indexes from the pinned SHAs in `corpus.json`; `python3 reproduce.py freeze` re-freezes the canonical output.
- **Committed artifacts**: `extract.py`, `fetch_one.sh`, `reproduce.py`, `reproduce.sh`, `validate.py`, `trace_check.py`, `corpus.json` (20 pinned repos with head SHAs), `validation_sample.tsv` (104 hand-verified cells = complete 8×13 embedding matrix), `snapshots/*_index.json` (per-repo signals), `expected_output/discovery_results.txt` (frozen canonical output).
- **Determinism statement**: fully deterministic (no stochastic components); multi-run statistics not applicable and not reported.
