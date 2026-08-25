# Related Work — Issue #7 (Type-Evident Code)

Each entry: work → what it does → limitation → **our difference**.

## 1. Four-dimensional type inference for dynamic languages (anchor)
- **"Generic Constraints Projection: Four-Dimensional Type Inference for Dynamic Languages." arXiv 2607.19693 (2026-07-22).**
- What: type inference for dynamically typed languages reconciling four
  evidence sources (assigned values, explicit declarations, contextual use,
  and a fourth). Motivates inference as a whole-program constraint problem.
- Limitation: does not quantify how much type information is *freely
  available in source structure alone* (typed defaults, literal assignments,
  `isinstance` guards) before any flow/constraint analysis — no
  recoverability lower bound, no decomposition by evidence source.
- **Our difference**: we measure the structural lower bound directly — the
  fraction of unannotated parameters whose types are recoverable from a
  default value with zero flow analysis (25.7% aggregate), and decompose it
  by evidence type. This is the "easy floor" that any inference system must
  trivially clear, which the four-dimensional framework does not report.

## 2. LLM-based type inference
- **TypePro. "Boosting LLM-Based Type Inference via Inter-Procedural Slicing." arXiv 2604.02702 (2026-04).**
- What: LLM-based type inference for dynamic languages using inter-procedural
  slicing to focus the model on relevant context.
- Limitation: whole-program, model-based inference; reports accuracy on
  inference benchmarks, not the share of types trivially derivable from
  defaults/literals. Expensive (LLM inference) relative to the trivial cases.
- **Our difference**: we show ~25% of unannotated params need no model or
  flow analysis at all — a cheap, deterministic baseline that LLM pipelines
  (and static checkers) should trivially match before spending inference
  budget.

## 3. LLM inference benchmark
- **TypyBench. "Evaluating LLM Type Inference for Untyped Python Repositories." arXiv 2507.22086 (2025-07).**
- What: benchmark of LLM type-inference accuracy across untyped Python repos.
- Limitation: measures end-to-end inference quality; the benchmark's "untyped
  repos" are exactly the partially-annotated population we measure, but it
  does not separate trivial-from-structure cases from genuinely hard ones —
  so it cannot say how much of the remaining error is avoidable cheaply.
- **Our difference**: we provide the trivial-recoverability floor for the
  same population — a per-package "how much is free" number (tqdm 46.6%,
  dateutil 29.1%, httpie 21.0%, gunicorn 17.0%) that benchmarks like TypyBench
  could use as a difficulty control.

## 4. Annotation maintenance
- **"Automating Just-In-Time Python Type Annotation Updating." arXiv 2607.09054 (2026-07).**
- What: keeps existing annotations in sync when code changes.
- Limitation: assumes annotations exist and focuses on drift; does not address
  the unannotated-parameter population or measure redundant annotations.
- **Our difference**: we measure the *redundancy* side — 12.3% of existing
  annotations restate their default's type — i.e., annotation effort that is
  currently spent restating what is already evident, which maintenance
  tooling could target first.

## 5. Annotation selection for gradual typing
- **"Efficient Selection of Type Annotations for Performance Improvement in Gradual Typing." arXiv 2603.05649 (2026-03).**
- What: selects which annotations to add to maximize performance gains under
  gradual typing.
- Limitation: optimization objective is runtime performance; treats
  annotations as scarce resources to place, not as a measurable existing
  population with recoverable/redundant subsets.
- **Our difference**: our recoverability/redundancy metrics give an
  annotation-strategy a principled input — prioritize effort where types are
  NOT already evident from defaults (the other ~75% of unannotated params).

## 6. Primary tool sources (practice)
- **pytype** (Google) and **mypy** (Dropbox): the de-facto static type
  checkers; pytype infers missing annotations with full flow analysis; mypy
  requires annotations (or `--disallow-untyped-defs` to flag them).
- Limitation: documentation describes inference capabilities but neither
  publishes a structural recoverability decomposition nor a redundancy
  statistic for real repos.
- **Our difference**: we quantify, across a 7-package corpus, the structural
  lower bound and the redundancy rate — numbers the tool maintainers could
  use to prioritize inference heuristics and annotation tooling.

---

### Contribution-level declaration (target for this manuscript)
**`system`** — a reproducible AST measurement system + curated 7-package
corpus with authors' annotations as ground truth; multi-package statistics
with CIs; claims scoped to the measured corpus and the structural-recoverability
metric (no universal claims about all Python code).
