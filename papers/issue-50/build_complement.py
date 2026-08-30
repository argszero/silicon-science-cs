#!/usr/bin/env python3
"""Issue #50 — build the validation COMPLEMENT sample (8 models x 8 signals).

The complement is a download-quantile-spanning subset (247M -> 0 downloads),
NOT extreme morphologies: it estimates corpus-wide error rather than boundary
behavior. Rows are hand-annotated by the author (human column).
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
OUT = ROOT / "validation_complement.tsv"

RECS = {r["id"]: r for r in json.load(open(SNAP / "signals.json"))}

COMPLEMENT = [
    "sentence-transformers/all-MiniLM-L6-v2", "google-bert/bert-base-uncased",
    "google/gemma-4-26B-A4B-it", "FacebookAI/roberta-large",
    "ornith-ai/Ornith-1.5-35B-A3B", "orcarouter/Qwen3.8-27B-Uncensored-MLX",
    "FastVideo/FastVideo-FastH3-4-step-Preview-v1-VSA-DataFree",
    "froggeric/Qwen-Fixed-Chat-Templates",
]

SIGS = ["license", "training_data", "eval_results", "bias_limitations",
        "intended_use", "base_model", "technical", "citations"]

PATS = {
    "license": r"^license\s*:",
    "training_data": r"trained on|training data|datasets\s*:|fine-tuned on|pre-trained on",
    "eval_results": r"benchmarks?|mmlu|humaneval|accuracy|perplexity|results? on|performance on",
    "bias_limitations": r"^#{1,4}[^\n]*(?:bias|limitations?|risks?|safety|ethical|misuse|harmful)",
    "intended_use": r"intended use|use cases?|applications?|how to use|usage",
    "base_model": r"based on|fine-tuned from|built on|derived from|checkpoint of|initialized from|distilled",
    "technical": r"parameters?|params|architecture|context length|layers?|model size",
    "citations": r"@article|@inproceedings|@misc|citation|bibtex|arxiv",
}

def snip(mid, pat, ctx=60):
    p = SNAP / "readmes" / f"{mid.replace('/', '__')}.md"
    if not p.exists():
        return "[no readme / gated]"
    txt = p.read_text(encoding="utf-8", errors="replace")
    for m in list(re.finditer(pat, txt, re.I))[:1]:
        s = max(0, m.start() - ctx)
        e = min(len(txt), m.end() + ctx)
        return txt[s:e].replace("\n", " ")
    return "[no match]"

rows = []
for mid in COMPLEMENT:
    rec = RECS[mid]
    for sig in SIGS:
        rows.append(f"{mid}\t{sig}\t{int(rec['signals'][sig])}\t{int(rec['gated_readme'])}\t{snip(mid, PATS[sig])}\t\t")

OUT.write_text("model\tsignal\tpred\tgated\tevidence\thuman\tnotes\n" + "\n".join(rows) + "\n")
print(f"wrote {OUT} with {len(rows)} cells ({len(COMPLEMENT)} models x 8 signals)")
