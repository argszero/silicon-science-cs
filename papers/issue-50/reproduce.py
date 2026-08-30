#!/usr/bin/env python3
"""Issue #50 — offline reproduction of the canonical census outputs.

Contract: `bash reproduce.sh` regenerates both canonical outputs from the
committed raw snapshots (snapshots/cards/*.json + snapshots/readmes/*.md +
corpus.json) and verifies byte-identical against expected_output/.

Canonical outputs:
  expected_output/signals.json    — per-model 8-signal records (187)
  expected_output/hypotheses.txt  — H1/H2/H3 + validation tables

Commands:
  reproduce.py offline  -> regenerate + diff vs expected_output/ (exit 0 iff identical)
  reproduce.py freeze   -> regenerate + write expected_output/ (publish new canonical)
No network access required. Deterministic.
"""
import json, sys, tempfile
from pathlib import Path

import extract as X
import hypotheses as H

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
EXP = ROOT / "expected_output"

def build_records():
    """Rebuild the 187 per-model signal records from raw snapshots."""
    records = []
    for m in X.MODELS:
        key = m["id"].replace("/", "__")
        card = X.get_card(key)
        cd = card.get("cardData") or {}
        readme = X.get_readme(key)
        if readme is not None:
            fm, body = X.strip_frontmatter(readme)
            gated = False
        else:
            fm, body = "", ""
            gated = True
        sig = X.extract_signal(card, fm, body)
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
    return records

def render_signals(records):
    return json.dumps(records, indent=1) + "\n"

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "offline"
    records = build_records()
    sig_text = render_signals(records)
    hyp_text = H.compute(records, ROOT / "validation_sample.tsv")
    if mode == "freeze":
        EXP.mkdir(exist_ok=True)
        (EXP / "signals.json").write_text(sig_text, encoding="utf-8")
        (EXP / "hypotheses.txt").write_text(hyp_text, encoding="utf-8")
        print(f"froze expected_output/signals.json "
              f"({len(records)} records) + hypotheses.txt")
        return
    # offline: diff vs frozen canonical
    failed = 0
    for name, rendered, path in [
        ("signals.json", sig_text, EXP / "signals.json"),
        ("hypotheses.txt", hyp_text, EXP / "hypotheses.txt"),
    ]:
        if not path.exists():
            print(f"FAIL: {name} — expected_output/{name} missing "
                  f"(run `python3 reproduce.py freeze` first)")
            failed = 1
            continue
        if path.read_text(encoding="utf-8") == rendered:
            print(f"OK: {name} byte-identical")
        else:
            print(f"FAIL: {name} deviates")
            failed = 1
    raise SystemExit(failed)

if __name__ == "__main__":
    main()
