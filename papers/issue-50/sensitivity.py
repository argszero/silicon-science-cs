#!/usr/bin/env python3
"""Issue #50 — rule-set sensitivity analysis (appendix, NOT canonical).

Runs the 8-signal aggregation under two bias/limitations rule variants and
reports how H1 (completeness distribution) and H3 (field-coverage ranking)
shift. This is a separate, committed appendix run: it READS the canonical
snapshots/signals.json and writes sensitivity_report.txt — it never modifies
expected_output/ (canonical outputs are unchanged by construction).

Variants:
  lenient  — count the 4 borderline prose disclosures as bias_limitations
             (Breeze-TTS-2 acceptable-use clause, Kimi-K3 safety-eval
             disclosure, Solar-Preview language-coverage limitation,
             froggeric 'training bias' cause-mention)
  strict   — drop the known technical-heading false positive
             (froggeric '### KV Cache Safety' -> bias_limitations)
Canonical (68 bias positives) is the reference row.
"""
import json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
SIGS = ["license", "training_data", "eval_results", "bias_limitations",
        "intended_use", "base_model", "technical", "citations"]

LENIENT_BIAS = {  # borderline prose disclosures -> bias_limitations True
    "BreezeBlue/Breeze-TTS-2", "moonshotai/Kimi-K3",
    "upstage/solar-pro-preview-instruct", "froggeric/Qwen-Fixed-Chat-Templates",
}
STRICT_BIAS = {  # technical-heading false positive -> bias_limitations False
    "froggeric/Qwen-Fixed-Chat-Templates",
}

def stats(records):
    comp = [r["completeness"] for r in records]
    low25 = sum(1 for c in comp if c <= 0.25)
    high75 = sum(1 for c in comp if c >= 0.75)
    return (len(records), statistics.mean(comp), statistics.median(comp),
            low25, high75, sum(1 for c in comp if c == 0.0))

def coverage_ranking(records):
    cov = {s: sum(1 for r in records if r["signals"][s]) for s in SIGS}
    return " > ".join(f"{s} {cov[s]}" for s in sorted(cov, key=lambda s: (-cov[s], SIGS.index(s))))

def main():
    records = json.load(open(SNAP / "signals.json"))
    out = []
    out.append("ISSUE #50 — RULE-SET SENSITIVITY REPORT (appendix; canonical unchanged)")
    out.append("")
    variants = {
        "canonical": {},
        "lenient-bias": LENIENT_BIAS,
        "strict-bias": STRICT_BIAS,
    }
    for name, flips in variants.items():
        recs = [dict(r, signals=dict(r["signals"])) for r in records]
        for r in recs:
            if name == "lenient-bias" and r["id"] in LENIENT_BIAS:
                r["signals"]["bias_limitations"] = True
            if name == "strict-bias" and r["id"] in STRICT_BIAS:
                r["signals"]["bias_limitations"] = False
            r["completeness"] = sum(r["signals"].values()) / 8
        n, mean, med, low25, high75, zeros = stats(recs)
        bias = sum(1 for r in recs if r["signals"]["bias_limitations"])
        out.append(f"== {name} ==")
        out.append(f"  bias_limitations positives: {bias}/187 = {bias/187*100:.1f}%")
        out.append(f"  completeness: mean {mean:.3f} / median {med:.3f}; "
                   f"<=0.25: {low25}/187 ({low25/187*100:.1f}%); "
                   f">=0.75: {high75}/187 ({high75/187*100:.1f}%); zero: {zeros}")
        out.append(f"  H3 ranking: {coverage_ranking(recs)}")
        out.append("")
    # delta summary
    out.append("== DELTAS vs canonical ==")
    out.append("  lenient: 68 -> 71 bias positives (+3; froggeric already True "
               "via the KV-Cache heading, so 4 candidates add 3 net)")
    out.append("  strict:  68 -> 67 bias positives (-1; KV-Cache technical heading)")
    out.append("  H1 (<=0.25 count) and H3 (ranking) re-derived under both; "
               "see rows above")
    text = "\n".join(out)
    print(text)
    (ROOT / "sensitivity_report.txt").write_text(text + "\n", encoding="utf-8")
    print("\nwrote sensitivity_report.txt (canonical outputs untouched)")

if __name__ == "__main__":
    main()
