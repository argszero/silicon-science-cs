#!/usr/bin/env python3
"""Issue #50 — corpus ↔ snapshots ↔ signals traceability check.

Cross-checks that the committed raw snapshots and the canonical outputs tell a
consistent story:
  1. corpus.json models ↔ snapshots/cards/*.json (187, no orphans)
  2. corpus.json models ↔ snapshots/readmes/*.md (172 public + 15 gated)
  3. signals.json records ↔ corpus.json (187, schema valid, completeness = sum/8)
  4. gated_readme flag ⟺ readme file absence
  5. cardData license ⟹ license signal True (no false negatives at the source)
  6. canonical needles: key hypothesis statements appear verbatim in
     expected_output/hypotheses.txt
Deterministic, offline, exit 0 iff all checks pass.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
CORPUS = json.load(open(ROOT / "corpus.json"))["models"]
SIGS = ["license", "training_data", "eval_results", "bias_limitations",
        "intended_use", "base_model", "technical", "citations"]

failed = 0

def check(name, ok, detail=""):
    global failed
    print(f"  {'OK' if ok else 'FAIL'}  {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        failed += 1

# ---- 1. cards ----
cards_dir = SNAP / "cards"
readmes_dir = SNAP / "readmes"
model_keys = [m["id"].replace("/", "__") for m in CORPUS]
card_keys = sorted(p.stem for p in cards_dir.glob("*.json"))
check("corpus→cards: every model has a card",
      set(model_keys) <= set(card_keys),
      f"{len(set(model_keys) & set(card_keys))}/{len(model_keys)}")
check("cards→corpus: no orphan cards",
      set(card_keys) <= set(model_keys),
      f"{len(set(card_keys) - set(model_keys))} orphans")
check("cards count = corpus count", len(card_keys) == len(CORPUS),
      f"{len(card_keys)} vs {len(CORPUS)}")

# ---- 2. readmes ----
readme_keys = sorted(p.stem for p in readmes_dir.glob("*.md"))
public = [k for k in model_keys if k in readme_keys]
gated = [k for k in model_keys if k not in readme_keys]
check("readmes: 172 public / 15 gated (no other missing)",
      len(public) == 172 and len(gated) == 15,
      f"public {len(public)} gated {len(gated)}")
check("readme keys ⊆ corpus keys",
      set(readme_keys) <= set(model_keys),
      f"{len(set(readme_keys) - set(model_keys))} orphans")

# ---- 3. signals.json ----
recs = {r["id"]: r for r in json.load(open(SNAP / "signals.json"))}
check("signals: 187 records == corpus", len(recs) == len(CORPUS),
      f"{len(recs)} vs {len(CORPUS)}")
schema_ok = True
for mid in CORPUS:
    r = recs.get(mid["id"])
    if r is None:
        schema_ok = False
        break
    if set(r["signals"].keys()) != set(SIGS):
        schema_ok = False
        break
    if not all(isinstance(v, bool) for v in r["signals"].values()):
        schema_ok = False
        break
    if abs(r["completeness"] - sum(r["signals"].values()) / 8) > 1e-9:
        schema_ok = False
        break
check("signals schema: 8 bools + completeness=sum/8", schema_ok)

# ---- 4. gated flag consistency ----
flag_ok = all(
    recs[mid["id"]]["gated_readme"] == (mid["id"].replace("/", "__") not in readme_keys)
    for mid in CORPUS)
check("gated_readme ⟺ readme absent", flag_ok)

# ---- 5. cardData license ⟹ license signal ----
lic_ok = True
misses = []
for mid in CORPUS:
    key = mid["id"].replace("/", "__")
    try:
        cd = json.load(open(cards_dir / f"{key}.json")).get("cardData") or {}
    except Exception:
        continue
    if cd.get("license") and not recs[mid["id"]]["signals"]["license"]:
        lic_ok = False
        misses.append(mid["id"])
check("cardData license ⟹ license signal True", lic_ok,
      ", ".join(misses[:5]))

# ---- 6. canonical needles in expected_output/hypotheses.txt ----
hyp = (ROOT / "expected_output" / "hypotheses.txt").read_text(encoding="utf-8")
needles = {
    "H1 verdict": "VERDICT: CONFIRMED",
    "H2 verdict": "org-type/popularity FALSIFIED; access-control (gating) CONFIRMED",
    "H3 verdict": "VERDICT: CONFIRMED",
    "validation 128 cells": "cells: 128 (16 models x 8 signals)",
    "validation accuracy 100%": "accuracy 100.0% (128/128)",
    "precision 1.000": "precision 1.000 (71/71)",
    "recall 1.000": "recall 1.000 (71/71)",
    "gated vs non-gated gap": "access: gated 0.167 (n=15) vs non-gated 0.649 (n=172)",
    "Mann-Whitney U=132": "Mann-Whitney U(gated, non-gated) = 132",
    "license top coverage": "176/187 = 94.1%",
    "bias_limitations last": "68/187 = 36.4%",
    "training_data 96": "96/187 = 51.3%",
}
for name, needle in sorted(needles.items()):
    check(f"needle[{name}]", needle in hyp, f"'{needle[:50]}…'")

print(f"traceability: {'ALL ' + str(9 + len(needles)) + ' checks OK' if failed == 0 else str(failed) + ' FAILED'}")
raise SystemExit(1 if failed else 0)
