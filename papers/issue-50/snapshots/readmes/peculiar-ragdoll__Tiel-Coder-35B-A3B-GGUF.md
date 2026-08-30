---
license: mit
base_model: ornith-ai/Ornith-1.5-35B-A3B
base_model_relation: quantized
pipeline_tag: image-text-to-text
library_name: gguf
language:
  - en
  - zh
tags:
  - gguf
  - llama.cpp
  - qwen35moe
  - moe
  - imatrix
  - unsloth-dynamic
  - agentic-coding
  - token-efficient
  - vision
---

<div align="center">
  <img src="assets/tiel_banner_eyebrow.png" alt="TielCoder — Ornith-1.5 35B-A3B, sharpened, dynamically quantized" width="100%">
</div>

<div align="center">
  <img src="assets/card_tiel_swe.png" alt="SWE-bench-Live: Tiel solves 12 of 25, level with Opus 4.6 and ahead of KAT-Coder, Nail, stock Qwen3.6-35B-A3B and Ornith" width="100%">
</div>

# Straight to the point

*Tiel* is the fast coder of the arsenal. At 4-bit quantization and 22 GB it fixes real codebase issues at the rate (and speed, with
the right GPU) of Opus 4.6 medium, while holding the best multi-turn conversation of any local model we
have measured. It is also cheerfully bad at trivia.

Pick it for work. Pick something else for exams.

> **This is [Ornith-1.5-35B-A3B](https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B) re-quantized
> dynamically with our own imatrix and carrying the [Sharp chat template](https://huggingface.co/peculiar-ragdoll/Qwen-Sharp-Chat-Templates)**
> inside the GGUF. Find TielCoder MTP GGUFs [here](https://huggingface.co/peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF-MTP).

## The numbers

<div align="center">
  Where it sits against the other local builds
  <img src="assets/card_tiel_local.png" alt="SWE-bench-Live: Qwen3.8-27B solves 16 of 25 at 50.2 minutes per attempt, Dirk 15 at 20.1, TielCoder 12 at 8.6, stock Qwen3.6-35B-A3B 8 at 5.5" width="100%">
  Multi-turn conversation
  <img src="assets/card_tiel_claw.png" alt="Claw-Eval multi-turn: Tiel 67.2 overall against Ornith 65.3 and Nail 60.5, over 114 scored conversations each" width="100%">
  Reasoning and knowledge
  <img src="assets/card_tiel_mmlu.png" alt="MMLU-Pro: Tiel 73.7 against Nail 84.0, both at 4-bit, with the control arm isolating the template" width="100%">
</div>

**Where it stands.** On 25 SWE-bench-Live problems Tiel fixes 12 — the same as Opus 4.6 (medium),
four more than Ornith-1.5 itself, three more than Nail, and four more than Sonnet 5 (medium). Among
models of its own class it is first; the ones ahead are dense 27Bs and Opus 5. Its time per attempt
is also steadier than Nail's: an 8.6 minute median against 7.2, but a 12.3 minute mean against 15.7,
because it lacks Nail's tail of expensive attempts.

**How it talks.** On Claw-Eval's multi-turn tasks Tiel scores 67.2 against Nail's 60.5 and its own
base's 65.3, over 114 scored conversations each. It earns that by answering better rather than by
asking more: against the base it is 3.8 points up on answer quality and 5.1 down on clarifying
questions. The score weights answers four to one, so the trade pays — but if you want a model that
interrogates a vague request before acting, the base does that better.

**What it costs.** 73.7 on MMLU-Pro against Nail's 84.0, both at 4-bit. Most of that is inherited
rather than built: Ornith-1.5 scores 78.0 where stock Qwen3.6-35B-A3B scores 85.3. Our quantization
is not the cause — the same quant carrying Ornith's own template scores exactly what Ornith scores.
The remaining 4.3 points are the Sharp template buying shorter answers, which is the trade this
build exists to make.

**Which one.** Agentic coding, or long conversations that have to stay useful → Tiel. Exam-style
knowledge and hard reasoning → [Nail](https://huggingface.co/peculiar-ragdoll/Nail-Qwen3.6-35B-A3B-GGUF),
which is 10.3 points better on MMLU-Pro and 6.7 worse in conversation.
The most fixes per problem regardless of weight → [Dirk](https://huggingface.co/peculiar-ragdoll/Dirk-Qwen3.8-27B-GGUF),
the dense 27B that solves 15 of the same 25 — one behind stock Qwen3.8-27B, at 2.5x its speed.

## Run it

| file | size | fits | notes |
|---|--:|:--|---|
| `Tiel-Coder-35B-A3B-UD-Q2_K_XL.gguf` | 12.3 GB | 16 GB | smallest; 2-bit gives up real accuracy, so prefer IQ3_XXS wherever it fits |
| `Tiel-Coder-35B-A3B-UD-IQ3_XXS.gguf` | 13.2 GB | 16 GB | **the 16 GB pick** — better than Q2_K_XL for under a gigabyte more |
| `Tiel-Coder-35B-A3B-UD-Q3_K_XL.gguf` | 16.8 GB | 24 GB | 3-bit with plenty of context room; prefer IQ4_XS below unless you need the extra ~1 GB |
| `Tiel-Coder-35B-A3B-UD-IQ4_XS.gguf` | 17.7 GB | 24 GB | 4-bit quality with the most context headroom of any 4-bit tier |
| `Tiel-Coder-35B-A3B-UD-Q4_K_S.gguf` | 20.9 GB | 24 GB | tight 4-bit; useful when Q4_K_XL leaves too little room |
| `Tiel-Coder-35B-A3B-UD-Q4_K_XL.gguf` | 22.4 GB | 24 GB | **start here** — the benchmarked tier; snug on 24 GB, comfortable on 32 |
| `Tiel-Coder-35B-A3B-UD-Q5_K_XL.gguf` | 26.6 GB | 32 GB | the **32 GB** pick |
| `Tiel-Coder-35B-A3B-UD-Q6_K_XL.gguf` | 31.8 GB | 48 GB | near-lossless; will not leave usable context on 32 GB |
| `Tiel-Coder-35B-A3B-UD-Q8_K_XL.gguf` | 38.5 GB | 48 GB | reference |

The **fits** column is the smallest card that holds the weights *and* leaves room to work. Context is
cheaper here than the file size suggests: this is a hybrid SSM/attention mixture with only 2 KV heads,
so the growing cache is a fraction of what a dense model of the same footprint would need.

```bash
hf download peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF \
  Tiel-Coder-35B-A3B-UD-Q4_K_XL.gguf --local-dir Tiel
llama-server -m Tiel/Tiel-Coder-35B-A3B-UD-Q4_K_XL.gguf -ngl 99 --jinja
```

Sampling: `temperature 1.0`, `top_p 0.95`, `top_k 20`. For agentic coding we ran `temperature 0.6`.

**It can see.** Tiel-Coder inherits Ornith-1.5's vision tower — point it at a screenshot of a failing
test, a stack trace, a design mock. The projector is `mmproj-BF16.gguf`, one 903 MB file shared by
every tier, and it is Ornith's own, passed through unmodified. We changed the chat template, not the
weights, so the projector below them is theirs and a re-export of ours would be the same file.

```bash
hf download peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF \
  Tiel-Coder-35B-A3B-UD-Q4_K_XL.gguf mmproj-BF16.gguf --local-dir Tiel
llama-mtmd-cli -m Tiel/Tiel-Coder-35B-A3B-UD-Q4_K_XL.gguf --mmproj Tiel/mmproj-BF16.gguf \
  -ngl 99 --image screenshot.png -p "Why is this test failing?"
```

Vision is untouched by our quantization: the projector ships at its original BF16 precision on every
tier, so a 2-bit text model and an 8-bit one see equally well.

## No multi-token-prediction head

Ornith-1.5 ships an MTP (`nextn`) block and the tiers here do not carry it — for a reason that has
since expired, so here is the whole story rather than the conclusion.

When these tiers were baked that block was untrained. Every matrix in it sat at a standard deviation
of 0.020 with kurtosis 3.00 and a largest value of 5 standard deviations, which is a fresh random
initialization, against kurtosis between 4 and 39 with outliers past 14 in every trained layer of the
same file. Drafts from random weights are accepted at chance, so it was 2.4% of every file doing no
work, and removing it changed no output.

**Ornith fixed it on 2026-08-23**, re-uploading a single shard with a trained head. We measured the
replacement rather than take it on faith: kurtosis 25.1 with a 98-sigma outlier, and 825 on the
`nextn` projection. That is not fresh initialization by any reading. The head is real now, and it
ships in **[Tiel-Coder-35B-A3B-GGUF-MTP](https://huggingface.co/peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF-MTP)**.

**The tiers in this repo are current and were not rebuilt.** The re-upload touched only the MTP
tensors — `lm_head` is bit-identical across the fix and layer 39's experts have an identical value
multiset — so nothing else moved. Take the MTP repo if your runtime does multi-token speculative
decoding; take this one if it does not, and keep the 0.9 GB the head costs.

## How the imatrix was made

Every tier is quantized against an importance matrix we generated ourselves, rather than a
borrowed one. The calibration corpus is 49 M characters drawn from
[eaddario/imatrix-calibration](https://huggingface.co/datasets/eaddario/imatrix-calibration) (MIT):
about three quarters `code_medium` and one quarter `combined_all_large`, interleaved so the two
alternate throughout rather than sitting in separate halves. That mix is deliberate — Tiel is meant
for coding, so the corpus leans that way, while the combined slice keeps maths, tool-calling and
non-English text represented so those paths are not the ones that get quantized carelessly.

The matrix was measured on a Q8_0 of the original BF16 weights, over 3,000 chunks of 512 tokens
(~1.5 M tokens), which is enough for every expert to be exercised many times over — this is a
256-expert mixture that routes 8 per token, so a short corpus would leave some experts barely seen.
The shipped tiers are then quantized from the BF16 source using that matrix.

**The matrix itself ships here**, as `Tiel-Coder-35B-A3B.imatrix.gguf` (183 MiB, 510 tensors) — so a
tier we don't ship is one command away, without spending an hour and a half measuring your own:

```bash
hf download peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF Tiel-Coder-35B-A3B.imatrix.gguf --local-dir .
llama-quantize --imatrix Tiel-Coder-35B-A3B.imatrix.gguf Ornith-1.5-35B-BF16.gguf out.gguf IQ4_XS
```

Be clear about what that does *not* give you: the tiers in the table above are cut with per-tensor
Dynamic recipes layered on top of this matrix, and they carry the Sharp template. A plain
`llama-quantize` from the upstream BF16 reproduces neither.

eaddario's code slice is itself built from
[Open-Critic-GPT](https://huggingface.co/datasets/Vezora/Open-Critic-GPT),
[opc-sft-stage2](https://huggingface.co/datasets/OpenCoder-LLM/opc-sft-stage2),
[Magicoder-Evol-Instruct-110K](https://huggingface.co/datasets/ise-uiuc/Magicoder-Evol-Instruct-110K)
and [McEval-Instruct](https://huggingface.co/datasets/Multilingual-Multimodal-NLP/McEval-Instruct).

## Limitations

- **Exam scores are its weak axis.** If you are picking on MMLU-Pro, Nail is 10.3 points better.
- **It asks fewer clarifying questions than its base**, by 5.1 points. Terser is not always better;
  a vague request gets answered rather than questioned.
- Benchmarks are one run per problem on SWE-bench-Live and three seeds on MMLU-Pro. Treat small
  differences as noise.
- Chinese and English only, inherited from the base.

## Credits

- [**ornith-ai**](https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B) — the Ornith-1.5-35B-A3B weights (MIT).
- [**Unsloth**](https://huggingface.co/unsloth) — the Dynamic GGUF quantization method this reproduces.
- [**froggeric**](https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates) — the template lineage Sharp builds on.
- [**eaddario**](https://huggingface.co/datasets/eaddario/imatrix-calibration) — the calibration corpora the imatrix was measured on (MIT).
- [**llama.cpp**](https://github.com/ggml-org/llama.cpp) — `llama-quantize` / `llama-imatrix` / `llama-server`.

MIT, inheriting Ornith-1.5's license.
