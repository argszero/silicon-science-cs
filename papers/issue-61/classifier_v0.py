#!/usr/bin/env python3
"""Issue #61 — classifier v0: merge 3-channel signals into L0-L3 repo status.

Levels (cumulative, from pqc_signal_dict_v1.md):
  L0 NONE     — no PQC signal anywhere
  L1 CAPABLE  — PQC-capable dependency present (manifest Channel 1) OR vendored
                PQC in tree (path Channel 2 under vendor/third_party/ext)
  L2 DIRECT   — own source code references PQC algorithms (path/content Channel 2)
  L3 ACTIVE   — PQC actually invoked (API-usage Channel 3 probes)

Caveats (v1, will calibrate with annotation):
  - version thresholds not yet parsed (BouncyCastle >=1.78, openssl >=3.5, ...) —
    L1 currently = any PQC-capable dep name; may overcount L1
  - falcon excluded bare (v1.1 rule); hybrids need content (present)
  - vendored PQC (kubernetes/moby x/crypto mlkem.go) counted as L1 (vendored=CAPABLE)

Outputs:
  snapshots/classifier_v0_labels.json  — per repo: {level, signals, evidence_keys}
  snapshots/classifier_v0_stats.txt
"""
import json
import os
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
TREES = SNAP / "trees"

VENDOR_DIR_RE = re.compile(r"(^|/)(vendor|third_party|thirdparty|3rdparty|ext|deps|external)/")

# channel 2 path regexes (falcon excluded bare per v1.1)
CH2_PATH = {
    "ML-KEM": re.compile(r"mlkem|ml[\s_-]?kem|kyber", re.I),
    "ML-DSA": re.compile(r"mldsa|ml[\s_-]?dsa|dilithium", re.I),
    "SLH-DSA": re.compile(r"slhdsa|slh[\s_-]?dsa|sphincs", re.I),
    "FN-DSA": re.compile(r"fn[\s_-]?dsa|fn_dsa", re.I),
    "Hybrid": re.compile(r"x25519mlkem|x25519_mlkem|p256mlkem|mlkem768x25519", re.I),
    "generic-pq": re.compile(r"post[\s_-]?quantum|quantum[\s_-]?safe|pqclean|\boqs\b|liboqs", re.I),
}


def classify(repo):
    signals = {"dep": set(), "path": set(), "content": set(), "api": set()}
    evidence = []

    # Channel 1: manifest deps
    dep_evidence = json.load(open(SNAP / "pqc_dep_evidence.json"))
    deps = dep_evidence.get(repo, {}).get("pqc_deps", [])
    signals["dep"].update(deps)

    # Channel 2: path signals (with vendor awareness)
    fname = repo.replace("/", "__") + ".json"
    fpath = TREES / fname
    vendored_pqc = []
    own_pqc_paths = []
    if fpath.exists():
        data = json.load(open(fpath))
        for e in data.get("tree", []):
            p = e.get("path", "")
            hit = next((n for n, pat in CH2_PATH.items() if pat.search(p)), None)
            if not hit:
                continue
            if VENDOR_DIR_RE.search(p):
                vendored_pqc.append((p, hit))
            else:
                own_pqc_paths.append((p, hit))
        for p, h in own_pqc_paths:
            signals["path"].add(h)
        for p, h in vendored_pqc:
            signals["path"].add(f"VENDORED-{h}")

    # Channel 2/3: content probes
    probes = json.load(open(SNAP / "content_probe_evidence.json"))
    pr = probes.get(repo, {})
    signals["content"].update(pr.get("path_content_hits", []))
    signals["api"].update(pr.get("api_hits", []))
    signals["readme"] = pr.get("readme_hits", [])

    # ---- level assignment ----
    has_dep = bool(signals["dep"])
    has_vendored = any(s.startswith("VENDORED-") for s in signals["path"])
    has_own_path = any(not s.startswith("VENDORED-") for s in signals["path"])
    has_content = bool(signals["content"])
    has_api = bool(signals["api"])
    has_readme_only = bool(signals["readme"]) and not (has_dep or has_own_path or has_content or has_api)

    if has_api:
        level = "L3_ACTIVE"
    elif has_content or has_own_path:
        level = "L2_DIRECT"
    elif has_dep or has_vendored:
        level = "L1_CAPABLE"
    else:
        level = "L0_NONE"

    if has_readme_only:
        evidence.append("README-mention-only (docs; check implementation)")

    summary = {
        "level": level,
        "deps": sorted(signals["dep"]),
        "own_path_sigs": sorted(s for s in signals["path"] if not s.startswith("VENDORED-")),
        "vendored": sorted(s for s in signals["path"] if s.startswith("VENDORED-")),
        "content_sigs": sorted(signals["content"]),
        "api": sorted(signals["api"]),
        "readme": sorted(signals["readme"]),
        "notes": evidence,
    }
    return summary


def main():
    corpus = json.load(open(SNAP / "tier_ab_corpus.json"))
    labels = {}
    for repo in sorted(corpus.keys()):
        labels[repo] = classify(repo)

    json.dump(labels, open(SNAP / "classifier_v0_labels.json", "w"), indent=1, sort_keys=True)

    # stats
    by_level = defaultdict(list)
    for repo, s in labels.items():
        by_level[s["level"]].append(repo)
    lines = ["classifier v0 — L0-L3 distribution (n=%d)" % len(labels), ""]
    for lv in ["L0_NONE", "L1_CAPABLE", "L2_DIRECT", "L3_ACTIVE"]:
        rows = by_level.get(lv, [])
        lines.append(f"{lv}: {len(rows)}")
        lines.append("  " + ", ".join(rows))
        lines.append("")
    # Tier A vs Tier B split
    ta = [r for r, v in corpus.items() if v.get("is_anchor")]
    tb = [r for r, v in corpus.items() if v.get("tier") == "B" and not v.get("is_anchor")]
    lines.append("Tier A anchors (is_anchor): %d — levels:" % len(ta))
    for r in sorted(ta, key=lambda x: corpus[x].get("stars", 0), reverse=True):
        lines.append(f"  {labels[r]['level']:<12} {r}")
    lines.append("")
    lines.append("Tier B non-anchor: %d — L1+ count: %d" % (
        len(tb), sum(1 for r in tb if labels[r]["level"] != "L0_NONE")))
    lines.append("")
    lines.append("Tier B L1+ repos (annotation candidates):")
    for r in sorted(tb, key=lambda x: corpus[x].get("stars", 0), reverse=True):
        if labels[r]["level"] != "L0_NONE":
            lines.append(f"  {corpus[r]['stars']:>8}  {r:<45} {labels[r]['level']:<12} deps={labels[r]['deps']} vendored={labels[r]['vendored']}")
    with open(SNAP / "classifier_v0_stats.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
