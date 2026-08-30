#!/usr/bin/env python3
"""Issue #50 — model-card documentation-signal extraction.

Reads snapshots/cards/*.json (HF API cardData) + snapshots/readmes/*.md (raw
model cards) and emits per-model signals into snapshots/signals.json.

Signals (8 documentation dimensions, EU-AI-Act-Art.53 / Mitchell-2019 aligned):
  1. license        : cardData.license or README frontmatter license:
  2. training_data  : cardData.datasets or README frontmatter datasets: /
                      free-text training-data mention
  3. eval_results   : benchmark/eval metrics in README (mmlu, humaneval, bleu,
                      accuracy, benchmark, eval, F1, ...)
  4. bias_limitations: README has an explicit section marker naming bias/
                      limitations/risks/safety/ethical topics (ATX heading,
                      bullet-bold heading, or standalone bold line); free-text
                      technical mentions ("Attention QKV bias") excluded
  5. intended_use   : README intended-use / use-cases / applications section
  6. base_model     : cardData.base_model or README 'based on'/'fine-tuned from'
  7. technical      : architecture/params/context-length/quantization in README
  8. citations      : cardData.citation or README citation/reference section

Completeness = fraction of the 8 signals present. Deterministic, offline.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
CARDS = SNAP / "cards"
READMES = SNAP / "readmes"
OUT = SNAP / "signals.json"

MODELS = json.load(open(ROOT / "corpus.json"))["models"]

# ---- README keyword patterns (word-boundary, case-insensitive) ----
SEC_HEADING = re.compile(r"^#{1,4}\s+(.*)$", re.M)
# training-data keywords (frontmatter datasets + free text)
DATASETS_FM = re.compile(r"^datasets\s*:\s*(.+)$", re.M | re.I)
# R85 fix: drop bare `trained with` (batch size / multi-steps / bf16 / pipeline
# names are PROCEDURE, not data) and bare `dataset|corpus` (fires on model-index
# eval-YAML "dataset:" entries and load_dataset() code). Require data-attached
# phrases: "trained on/using", "training data", "fine-tuning data", ...
TRAINING_KW = re.compile(
    r"\b(trained on|trained using|trained over|training data|pre-trained on|"
    r"pre-trained using|fine-tuned on|fine-tuned using)\b|"
    r"\b(training|fine-tuning|finetuning|pretraining|pre-training|instruction|sft)"
    r"\s+(data|dataset|datasets|corpus)\b", re.I)
# eval keywords (R85 fix: `eval[^a-z]` fired on model.eval() code — dropped)
EVAL_KW = re.compile(
    r"\b(mmlu|humaneval|human_eval|gsm8k|truthfulqa|benchmarks?|bleu|rouge|"
    r"f1[^a-z]|accuracy|perplexity|performance on|results? on)\b", re.I)
# bias/limitations: SECTION-BASED rule (R85 decision 2026-08-30).
# A card documents bias/limitations iff its README contains an explicit
# section marker naming the topic: an ATX heading (#..####) that CONTAINS the
# keyword anywhere in the heading line (catches "## Intended Use and
# Limitations"), a markdown bullet whose BOLD span contains the keyword
# ("* **Bias and Fairness**", "- **Confident falsehoods & bias** —"), or a
# standalone bold line ("**Limitations**").
# Deliberately EXCLUDES free-text mentions that are technical terms or code:
# "Attention QKV bias" (architecture), 'bias="none"' (code), "The bias was
# set to [1000,-1000,0]" (weight init), "training bias" (cause mention).
BIAS_HEAD = re.compile(
    r"^#{1,4}\s+[^\n]{0,100}\b(?:bias|limitations?|risks?|safety|ethical|"
    r"misuse|failure modes?|known issues|caveats?|harmful|concerns?)\b[^\n]*$",
    re.M | re.I)
BIAS_BULLET = re.compile(
    r"^\s*[-*+]\s*\*{1,2}\s*[^*\n]{0,80}\b(?:bias|limitations?|risks?|safety|"
    r"ethical|misuse|failure modes?|harmful|unsafe)\b[^*\n]*\*{1,2}",
    re.M | re.I)
BIAS_BOLD = re.compile(
    r"^\s*\*{1,2}\s*[^*\n]{0,80}\b(?:bias|limitations?|risks?|safety|ethical|"
    r"misuse|failure modes?|harmful)\b[^*\n]*\*{1,2}\s*$",
    re.M | re.I)
# intended-use keywords
USE_KW = re.compile(
    r"\b(intended use|intended uses|use cases?|applications?|usage|"
    r"how to use|what is this)\b", re.I)
# base-model keywords
BASE_KW = re.compile(
    r"\b(based on|fine-tuned from|fine tuned from|built on top of|"
    r"derived from|checkpoint of|initialized from)\b|"
    r"\bfoundation model\b", re.I)
# technical keywords
TECH_KW = re.compile(
    r"\b(parameters?|params|architecture|context length|context window|"
    r"layers?|hidden size|quantiz|tokens|model size|num_|vocab)\b", re.I)
# citation keywords
CITE_KW = re.compile(
    r"^#{1,4}\s*(citation|cite|reference|references|how to cite|bibtex)\b",
    re.M | re.I)
CITE_AT = re.compile(r"@article|@inproceedings|@misc|doi:|arXiv:")

def strip_frontmatter(txt):
    """Split YAML frontmatter from body; return (frontmatter, body)."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", txt, re.S)
    if m:
        return m.group(1), txt[m.end():]
    return "", txt

def has_card(key):
    return (CARDS / f"{key}.json").exists()

def get_card(key):
    try:
        return json.load(open(CARDS / f"{key}.json"))
    except Exception:
        return {}

def get_readme(key):
    p = READMES / f"{key}.md"
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

def extract_signal(card, fm, body):
    """Return dict of the 8 binary signals."""
    cd = card.get("cardData") or {}
    sig = {}
    # 1. license
    lic = cd.get("license")
    fm_lic = re.search(r"^license\s*:\s*(.+)$", fm, re.M | re.I)
    sig["license"] = bool(lic) or bool(fm_lic)
    # 2. training_data
    if DATASETS_FM.search(fm) or cd.get("datasets"):
        sig["training_data"] = True
    elif TRAINING_KW.search(body):
        sig["training_data"] = True
    else:
        sig["training_data"] = False
    # 3. eval_results
    sig["eval_results"] = bool(EVAL_KW.search(body))
    # 4. bias_limitations (section-based, see BIAS_* patterns above)
    sig["bias_limitations"] = bool(
        BIAS_HEAD.search(body) or BIAS_BULLET.search(body)
        or BIAS_BOLD.search(body))
    # 5. intended_use
    sig["intended_use"] = bool(USE_KW.search(body))
    # 6. base_model
    bm = cd.get("base_model")
    sig["base_model"] = bool(bm) or bool(BASE_KW.search(body))
    # 7. technical
    sig["technical"] = bool(TECH_KW.search(body))
    # 8. citations
    sig["citations"] = bool(CITE_AT.search(body)) or bool(CITE_KW.search(body))
    return sig

def main():
    records = []
    for m in MODELS:
        key = m["id"].replace("/", "__")
        card = get_card(key)
        cd = card.get("cardData") or {}
        readme = get_readme(key)
        if readme is not None:
            fm, body = strip_frontmatter(readme)
            gated = False
        else:
            fm, body = "", ""
            gated = True
        sig = extract_signal(card, fm, body)
        present = sum(1 for v in sig.values() if v)
        records.append({
            "id": m["id"],
            "org": m["org"],
            "downloads": m.get("downloads"),
            "likes": m.get("likes"),
            "pipeline_tag": m.get("pipeline_tag"),
            "gated_readme": gated,
            "card_fields": sorted(cd.keys()),
            "signals": sig,
            "completeness": present / 8,
        })
    json.dump(records, open(OUT, "w"), indent=1)
    # summary
    n = len(records)
    from collections import Counter
    c = Counter()
    for r in records:
        for k, v in r["signals"].items():
            if v:
                c[k] += 1
    print(f"models: {n}")
    for k in sorted(c):
        print(f"  {k:16s} {c[k]:3d}/{n} = {c[k]/n*100:.1f}%")
    comp = [r["completeness"] for r in records]
    import statistics
    print(f"completeness: mean {statistics.mean(comp):.3f} median {statistics.median(comp):.3f} "
          f"min {min(comp):.2f} max {max(comp):.2f}")
    print(f"wrote {OUT.name}")

if __name__ == "__main__":
    main()
