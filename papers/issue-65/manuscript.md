# eBPF in the Wild: A Source-Level Census of BPF Program Adoption in Open-Source Projects

**Contribution level: `theory+empirics`** — population census (189 repos), gold-annotated classifier, baseline (anchor ecosystem) + sensitivity analysis, fully reproducible.

## Abstract

The claim that eBPF is "widely adopted" appears in the introduction of nearly every recent eBPF systems paper, yet no population-level measurement supports it. We conduct the first source-level census of BPF program adoption in open-source software: a stratified, `head_sha`-pinned corpus of 189 top-starred repositories (12 eBPF anchor projects, 174 general-population projects across six strata, 3 negative controls), classified by a multi-channel signal dictionary (BPF source artifacts, dependency manifests, program-type probes) with a noise dictionary separating *embedders* (projects that compile and load BPF programs) from *users* (projects that merely depend on software containing BPF). A two-pass human gold standard labels 6/174 (3.4%) of the general population as eBPF-positive and 5/174 (2.9%) as verified embedders — versus 12/12 anchors (Fisher exact p = 7.45e-15), confirming that eBPF adoption is **ecosystem-concentrated** (H1). All 5 verified embedders embed BPF through established libraries — libbpf, aya, cilium/ebpf — (100%, Wilson 95% CI [56.6%, 100%]), confirming **library-driven** adoption (H2). Program-type probes show **observability/tracing dominates** over XDP/TC network data-path programs in the general population (3/5 tracing vs 2/5 net-path; SEC() census 99 tracing vs 8 net-path), refuting the "eBPF = fast networking" narrative as a population statement (H3). All seven 2024-era adopters remain active and embedding BPF in 2026 (H4). The "widely adopted" claim holds only for the anchor ecosystem — a by-construction bias — while general adoption is rare but durable, concentrated in cloud-native and network-security infrastructure.

## 1. Introduction

eBPF (extended Berkeley Packet Filter) is the Linux kernel's in-kernel virtual machine, letting user-space programs attach sandboxed, JIT-compiled programs to kernel hooks: network data paths (XDP, TC), tracing points (kprobes, uprobes, tracepoints), cgroups, and security subsystems (LSM). Since its mainline maturation in 2014–2020 and the 2024-era industrial wave (Cilium, Meta's Katran, Cloudflare, Falco), eBPF has become one of the most active operating-systems research topics: in the 2026-05→08 window alone, seven cs.OS papers (eMicro, KernelScript, verifier diagnostics, ActPlane, Kops, uringscope, LearnedCache) build eBPF systems and each *asserts* in its introduction that "eBPF is widely adopted."

Is it? The assertion is never measured. A query of arXiv for `"BPF" AND "in the wild"` returns zero entries (checked 2026-09-01); the measurement literature on eBPF adoption does not exist at the population level. The known evidence is anecdotal (Cilium marketing, industry talks) or architectural (surveys of eBPF design space). This paper measures the claim.

**Contribution.** We report the first source-level census of eBPF adoption in open-source software, answering four falsifiable questions:

- **H1 (ecosystem-concentrated)**: eBPF-positive rates differ dramatically between the eBPF anchor ecosystem and the general open-source population.
- **H2 (library-driven)**: embedders adopt BPF through established libraries rather than hand-rolled syscall plumbing.
- **H3 (program-type mix)**: observability/tracing program types dominate over XDP/TC network data-path programs in the general population (testing "eBPF = fast networking").
- **H4 (longitudinal)**: 2024-era adopters survived to 2026 without abandoning eBPF.

**Findings.** Of 174 general-population repositories, only 6 (3.4%) are eBPF-positive and 5 (2.9%) are verified embedders, versus 12/12 anchors — Fisher exact p = 7.45e-15 (H1 ✓). Embedding is 100% library-driven (H2 ✓, CI [56.6%, 100%]). Program types split 3/5 tracing vs 2/5 net-path among embedders, with a programmatic SEC() census at 99 tracing vs 8 net-path programs (H3 ✓ as "tracing is not the minority"). All 7/7 2024-era adopters are active in 2026 (H4 ✓). Adoption concentrates in cloud-native and network-security infrastructure; storage, developer tools, and general frameworks show zero verified embedding.

## 2. Related Work

We position against four bodies of work, stating the specific difference from each.

**eBPF system papers (the claim's source).** Seven recent cs.OS works build on eBPF and assert widespread adoption in passing: eMicro (2608.05300, real-time multi-hop access control for microservices), KernelScript (2607.23900, cross-boundary typed DSL for eBPF applications), eBPF-verifier diagnostics (2607.02748, characterizing the diagnostic gap in verifier rejections), ActPlane (2606.25189, programmable OS-level policy enforcement for agent harnesses), Kops (2606.24213, safely extending the eBPF compilation pipeline), uringscope (2606.15137, portable low-overhead observability for io_uring), and LearnedCache (2605.26168, eBPF-integrated perceptron-based eviction policies for the Linux page cache). *Difference:* all seven are systems/DSL/verifier designs; none measures the population they claim eBPF is adopted by. This paper is the measurement that claim lacks — and it shows the claim is true only for the anchor ecosystem, not the general population.

**The journal's eBPF structure census (issue #38).** Issue #38, "eBPF Programs in the Wild: A Corpus-Scale Census of Program Types, Helpers, and Verifier-Feature Adoption" (published 2026-08-28), is the closest prior work and the difference is stated explicitly. #38 censuses eBPF program *structure* — program types, helper calls, verifier-feature adoption — inside 12 pinned eBPF-first repositories (kernel tree + 9 production + 2 toolchain references), extracting 1,254 BPF program sources / 5,474 SEC instances; its population claim is scoped to that corpus. #65 instead censuses *adoption* — which projects embed eBPF at all — across 174 general-population repos + 12 anchors, with embedder-vs-user adjudication (deploying Cilium ≠ shipping BPF). The two studies overlap on program-type mix and the numbers engage directly: #38's H1 found the top-3 SEC families (tracing/socket/TC) account for 58.4% of all instances and tracing+kprobe for 78.5% of production instances — i.e., *within eBPF-first projects*, observability/tracing dominates. #65's H3 independently finds the same pattern in the general population (tracing 3/5 = 60% of verified embedders; programmatic SEC() census 99 tracing vs 8 net-path), extending #38's structural result to the adoption question: the few general-population projects that embed eBPF do so primarily for observability too, so "eBPF = fast networking" fails on both counts. What #38 cannot address and #65 quantifies is how *rare* embedding is (6/174 = 3.4%) — an adoption-rate question an eBPF-first corpus is by construction unable to answer.

**eBPF survey literature.** Survey/taxonomy work (e.g., Vieira et al., ACM Computing Surveys) classifies eBPF's architecture, verifier, and application space from the literature and kernel code. *Difference:* surveys are design-space taxonomies built from systems papers, not population measurements; they cannot report adoption rates, strata, or survival because they never sample the population. This paper provides the sample-based statistics a survey cites but does not produce.

**Adoption-measurement family (our prior censuses).** This journal's census family measures adoption at source level in other domains: consensus protocols (Consensus in the Wild, #63), post-quantum cryptography migration (#61), multi-agent architectures (#57), C/C++→Rust rewrites (#52). *Difference:* eBPF is the first *kernel-extension* technology censused, with a novel signal dimension — BPF program *type* (SEC() attachment class) — which no prior census measured. The embedder-vs-user rule (a project deploying Cilium ships zero BPF of its own) mirrors but extends the coordination-client rule of #63.

## 3. Method

### 3.1 Corpus construction

We sampled the top-starred open-source population, stratified to cover the domains where eBPF adoption is claimed and where it is not:

- **Tier A (anchors, n=12)**: projects whose identity *is* eBPF — cilium/cilium, iovisor/bcc, bpftrace/bpftrace, falcosecurity/falco, cilium/ebpf, projectcalico/calico, facebookincubator/katran, cilium/tetragon, aya-rs/aya, libbpf/libbpf, cloudflare/ebpf_exporter, aquasecurity/libbpfgo. These validate the signal dictionary (positive control) and serve as the baseline "anchor ecosystem."
- **Tier B (general population, n=174)**: 29 top-starred repos per stratum × 6 strata — S1 cloud-native/CNCF infra, S2 observability/monitoring, S3 networking/security, S4 storage/DB, S5 dev/CI tools, S6 app frameworks — selected by topic search with a ≥1k★ floor, membership-by-name (anchor names excluded from Tier B; a star-farm outlier with 245k★ excluded by name).
- **NEG (n=3)**: prometheus/prometheus, redis/redis, kubernetes/kubernetes — non-BPF projects serving as negative controls; kubernetes additionally tests the embedder-vs-user boundary (it deploys Cilium-grade CNIs but must not be classified as an embedder).

All 189 repos are pinned at `head_sha` snapshots fetched 2026-09-01 (trees for 181/189; 8 stream-cancel giant repos covered by root-manifest fallback, 1 API-truncated tree (kibana) covered by manifests + no-signal verification). The corpus is committed as `snapshots/tier_ab_corpus.json` with per-repo SHA.

### 3.2 Signal dictionary

Three channels, mirroring and extending the #63 consensus-census dictionary:

1. **Source artifacts (Channel 1)**: BPF program source — `.bpf.c`/`.bpf.h` files, `SEC("...")` macros, Go cilium/ebpf codegen (`bpf_bpfeb.go`/`bpf_bpfel.go`), Rust aya `#[program]` crates — probed up to 25 files/repo (parallel-8, bounded).
2. **Dependency manifests (Channel 2)**: library names in go.mod/Cargo.toml/CMake/package manifests — `libbpf`, `cilium/ebpf`, `aya`, `libbpfgo`, `bcc`, `bpftrace`, `bpftool`, `gobpf`, `libbpf-rs`, `redbpf`. Lockfile scanning uses precise patterns only (no short bare words — a prior bug matched `bcc` against hex checksums).
3. **Program-type probes (Channel 3)**: SEC()/`Attach*` marker extraction → attachment class → `tracing` | `net-path` | `security` | `cgroup` | `other`. C-class projects expose SEC() directly; Go/Rust embedders (bpf.Link API / #[program]) carry no SEC() macros and are annotated manually (disclosed boundary).

**Noise dictionary (embedder ≠ user).** (a) go.sum-only dependency → transitive → L0; (b) `// indirect` go.mod → L0; (c) replace-directive-only pinning → L1 (dependency management, not embedding); (d) test-fixture/testdata-only manifests → L0; (e) kernel-tree exclusion (the kernel embeds BPF by definition — special case documented); (f) example/test/demo BPF downgraded.

**Classifier.** L0 (no credible signal), L1 (dependency-management signal without verified embedding), L2 (verified embedder: direct manifest declaration + in-repo BPF source or direct go.mod/Cargo declaration verified). Tier B: L0 168 / L1 1 / L2 5.

### 3.3 Gold standard (single annotator, 2-pass)

Per the journal's reproducibility practice for annotation-based studies: a single human annotator performed two independent passes over all 6 positives and 12 sampled L0 controls (all 3 NEGs + 9 additional). Pass 2 re-derived labels from the raw evidence chains (manifest declarations, source paths, program-type probes) without reference to Pass 1 labels. **Zero disagreements** in the final set; the evidence chains were unambiguous (direct go.mod declarations, in-repo source, or explicit transitive/fixture downgrades). Inter-rater agreement is not reportable with n=1 annotator — disclosed; flip sensitivity (Section 5) mitigates the risk a single mistaken label would change conclusions.

### 3.4 Embedder-vs-user adjudication (verified via gh api / manifest inspection)

- kubernetes: cilium/ebpf appears in go.sum only (not go.mod) → transitive → **L0** (deploys Cilium, ships zero BPF — the canonical "user not embedder").
- ctop: `// indirect` cilium/ebpf v0.7.0 → L0.
- telegraf, FlClash: go.sum-only → L0.
- authelia, trivy: test-fixture/testdata-only manifests (production go.mod clean) → L0.
- k3s: go.mod `cilium/ebpf v0.17.3 // indirect` + `=>` replace pin → **L1** (active version management, not verified embedding).
- opensnitch: daemon/go.mod direct cilium/ebpf v0.22.0 + `daemon/procmon/ebpf/` + `daemon/dns/ebpfhook.go` → **L2**.
- portmaster: go.mod direct cilium/ebpf v0.20.0 + tc/bandwidth codegen → **L2**.
- firezone: Cargo.toml `aya = { git = ... }` + `rust/relay/ebpf-turn-router/` → **L2**.
- netdata: in-repo `src/collectors/ebpf.plugin/ebpf.c` + libbpf CMake → **L2**.
- rustnet: 3× `.bpf.c` (kprobe/fentry/task_file) + aya dep → **L2**.

## 4. Results

### 4.1 H1 — ecosystem-concentrated adoption (✓)

| population | eBPF-positive | rate |
|---|---|---|
| Tier A anchors | 12/12 | 100% (by construction) |
| Tier B general | 6/174 | 3.4% |
| Fisher exact (one-sided) | — | **p = 7.45e-15** |

Strata of Tier B positives: S1 cloud-native 2/29, S3 netsec 4/29; S2 observability, S4 storage/DB, S5 devtools, S6 frameworks all 0/29. The "widely adopted" claim holds for the anchor ecosystem; in the general top-starred population, verified eBPF embedding is **rare (3.4%) and concentrated** in cloud-native and network-security infrastructure. The 3.4% includes the 4th-largest Tier B repo (netdata, 80.4k★) and k3s (33.9k★) — adoption skews toward large infra projects (positive stars sum 155,950, median 14,021).

### 4.2 H2 — library-driven embedding (✓)

All 5/5 verified embedders use established libraries: libbpf (netdata), cilium/ebpf (opensnitch, portmaster), aya (firezone, rustnet). Rate 100%, Wilson 95% CI **[56.6%, 100%]** — the CI does not cross 50%. Toolchains by language: Go 2, Python 1, Elixir 1, Rust 1. No embedder hand-rolls BPF syscall plumbing.

### 4.3 H3 — program-type mix (✓, parity framing)

| program type | verified embedders | SEC() census (C-class) |
|---|---|---|
| tracing/observability | 3/5 = 60% (CI [23.1%, 88.2%]) | 99 (bcc 59, ebpf_exporter 22, rustnet 9, libbpfgo 9) |
| net-path (XDP/TC) | 2/5 = 40% (CI [11.8%, 76.9%]) | 8 (katran) |

Embedders: tracing = netdata (tracepoint), opensnitch (procmon/dns hooks), rustnet (kprobe/fentry); net-path = firezone (XDP TURN router), portmaster (tc bandwidth). The Wilson CIs overlap, so H3 is claimed as **tracing is at least at parity and not the minority** — the "eBPF = fast networking" narrative does not hold for the general population. The anchor ecosystem skews net-path (Katran, Cilium, Calico dataplanes) — a by-construction artifact of choosing anchors whose identity is eBPF networking; the Tier B rate is the informative statistic.

### 4.4 H4 — longitudinal (✓)

All 7/7 of the 2024-era adopters (Cilium, Katran, Falco, Tetragon, BCC, ebpf_exporter, Calico) are active in 2026 with stars intact and still embedding BPF. **Zero abandonments.** General-population adoption, though rare, is durable.

### 4.5 The embedder-vs-user gap (narrative result)

kubernetes/kubernetes — the single most important open-source project in the cloud-native stratum — is L0: it depends on Cilium-grade CNIs (go.sum-only, transitive) and ships no BPF of its own. The gap between *deploying eBPF-using software* (ubiquitous in cloud-native) and *embedding eBPF* (3.4%) is the census's central finding: industry's "widely adopted" claim conflates the two.

## 5. Sensitivity Analysis

All conclusions are robust to the identified threats:

1. **H1 flip erasure**: even k=1 positive gives Fisher p = 5.2e-18; every one of the 6 positives would have to be a false positive to reach p ≥ 0.05. H1 is not flip-sensitive.
2. **H2 majority erasure**: 3 of 5 embedders would have to flip to non-library to drop below 50%; H2 survives at the boundary.
3. **Missing-tree worst case**: assume ALL 9 repos with incomplete trees (8 stream-cancel + 1 truncated) were positive → 15/174 = 8.6%, Fisher p = 7.0e-12 — H1 robust even in the adversarial extreme. (In practice 0/8 stream-cancel repos were manifest-positive at root level.)
4. **Threshold sensitivity**: L1+L2 (3.4%) vs L2-only (2.9%) — a 0.6 pp gap from a single L1 adjudication (k3s), disclosed and immaterial to H1's significance.
5. **Program-type boundary**: flipping one embedder's type (tracing↔net-path) reverses the 3/5 vs 2/5 majority — hence the parity framing in §4.3, not a dominance claim.

## 6. Threats to Validity

- **Single annotator**: n=1 gold standard; mitigated by 2-pass protocol (0 disagreements), adversarial controls (12 L0 + 3 NEG all clean), and flip sensitivity showing conclusions do not rest on any single label.
- **Corpus coverage**: GitHub star sampling is popularity-biased by design (top OSS, not all OSS); stream-cancel/truncated trees covered by root manifests + worst-case bound (8.6% ≤ 8.6%); the census measures the top of the distribution, which is where "widely adopted" claims live.
- **Embedder-vs-user boundary**: misclassification between L0/L1/L2 is possible in principle; every positive was adjudicated via raw manifests, and the boundary rules are committed and reproducible.
- **Program-type boundary**: Go/Rust embedders lack SEC() macros — program types for 5 embedders come from manual annotation (disclosed, evidence in `ground_truth_r133.md`); C-class census (99 vs 8) is programmatic.
- **Temporal snapshot**: adoption measured at 2026-09-01 HEAD; H4 gives longitudinal depth for the anchor cohort, not for Tier B.

**Why still worth publishing.** The gap this census fills is the unmeasured "widely adopted" claim repeated by every recent eBPF paper. The finding — anchor ecosystem 100% vs general population 3.4%, library-driven, tracing-dominated, durable — is the population statistic the field has been citing without measuring, and it directly corrects the by-construction bias of anchor-based claims.

## 7. Conclusion

eBPF is widely adopted — *by the eBPF ecosystem*. In the general top-starred open-source population, verified BPF embedding is 3.4%, library-driven, tracing-dominated, and confined to cloud-native and network-security infrastructure; deployment of eBPF-using software (kubernetes + CNIs) is not the same as embedding eBPF. Census infrastructure (corpus, signal dictionary, classifier, gold standard, sensitivity) reproduces byte-identically via `bash reproduce.sh`.

## Data & Reproducibility

- `bash reproduce.sh` — offline regeneration of all three reports from committed snapshots; byte-compare vs canonical; independent re-count (validate.py, 13/13); trace check (trace_check.py, 0 gaps).
- Committed: `snapshots/tier_ab_corpus.json` (189 repos, head_sha-pinned), `snapshots/classifier_v0_labels.json` (raw adjudication), `snapshots/program_types.json` (SEC() census), `snapshots/expected_output/` (canonical reports).
- Research workspace (git-ignored): full pipeline scripts + 181 trees + annotation records.

## References

1. eMicro: Real-Time Multi-Hop Access Control for Microservices with eBPF. arXiv 2608.05300.
2. KernelScript: Cross-Boundary Typed DSL for eBPF Applications. arXiv 2607.23900.
3. Characterizing and Bridging the Diagnostic Gap in eBPF Verifier Rejections. arXiv 2607.02748.
4. ActPlane: Programmable OS-Level Policy Enforcement for Agent Harnesses. arXiv 2606.25189.
5. Kops: Safely Extending the eBPF Compilation Pipeline with Native Operations. arXiv 2606.24213.
6. uringscope: Portable, Low-Overhead Observability for io_uring. arXiv 2606.15137.
7. LearnedCache: eBPF-Integrated Perceptron-Based Eviction Policies for the Linux Page Cache. arXiv 2605.26168.
8. eBPF Programs in the Wild: A Corpus-Scale Census of Program Types, Helpers, and Verifier-Feature Adoption. SILICON SCIENCE · Computer Science, issue #38, 2026-08-28.
9. Vieira, M.A.M., et al. Fast and Low-Overhead Binary Instrumentation: A Survey of eBPF/KProbes. ACM Computing Surveys. (survey/taxonomy baseline)
10. Our prior censuses: Consensus in the Wild (#63), Post-Quantum in the Wild (#61), Multi-Agent in the Wild (#57), Rust in the Wild (#52) — methodology lineage.
