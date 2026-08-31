#!/usr/bin/env python3
"""Issue #52 — repo-level signals + binding-vs-rewrite (signals.py).

Per-repo: component counts, Rust share (of source components), dominant class,
has_rust (any Rust component), mixed count.
Rust-side repos: binding_vs_rewrite verdict from Cargo.toml dependency analysis
(build.rs / cc / bindgen / -sys crates). Cargo.toml fetched via gh api at the
pinned SHA; verdict:
  BINDING — depends on a -sys crate OR uses build.rs with cc/bindgen (links C)
  REWRITE — no -sys dep, no C link path (pure Rust implementation)
  UNCLEAR — no Cargo.toml at root / unparseable

Emits snapshots/repo_signals.json + prints the summary table.
"""
import json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORPUS = json.load(open(ROOT / "corpus.json"))
CLASSES = json.load(open(ROOT / "snapshots" / "component_classes.json"))

SRC_CLASSES = {"RUST", "C", "CPP", "MIXED"}

def gh_content(repo, path, ref):
    r = subprocess.run(["gh", "api",
                        f"repos/{repo}/contents/{path}?ref={ref}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return r.stdout
    except Exception:
        return None

def fetch_cargo(repo, ref):
    out = gh_content(repo, "Cargo.toml", ref)
    if out is None:
        return None
    try:
        data = json.loads(out)
    except Exception:
        return None
    if "content" not in data:
        return None
    import base64
    return base64.b64decode(data["content"]).decode("utf-8", "replace")

def binding_verdict(cargo_toml):
    """BINDING iff an EXTERNAL -sys crate appears in the non-gated root
    [dependencies] (the crate wraps a system C library as its mechanism).
    windows-* family is Rust-native (excluded). Feature-/platform-gated -sys
    (openssl opt-in, fts-sys BSD-only) and build.rs+cc compiling own C/asm are
    NOT bindings — they are REWRITE with incidental native-C components."""
    if cargo_toml is None:
        return "UNCLEAR", "no Cargo.toml at root"
    WINDOWS_FAMILY = {"windows-sys", "windows-core", "windows-targets",
                      "windows-link", "windows-sys-link", "windows"}
    section = None
    root_sys = []
    gated_sys = []
    has_build_rs = False
    has_cc = False
    for raw in cargo_toml.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line
            continue
        if line.startswith("#") or line.startswith("//") or not line:
            continue
        m = re.match(r'^([\w\-]+)\s*=\s*', line)
        if not m:
            continue
        name = m.group(1)
        if name == "build":
            has_build_rs = True
            continue
        if name in ("cc", "bindgen"):
            has_cc = True
            continue
        if name.endswith("-sys"):
            if section == "[dependencies]" and name not in WINDOWS_FAMILY:
                root_sys.append(name)
            elif name not in WINDOWS_FAMILY:
                gated_sys.append(name)
    evidence = []
    if root_sys:
        evidence.append(f"root [dependencies] -sys: {', '.join(root_sys)}")
    if gated_sys:
        evidence.append(f"gated -sys (feature/platform): {', '.join(gated_sys)}")
    if has_build_rs and has_cc:
        evidence.append("build.rs + cc/bindgen (compiles own C/asm)")
    elif has_build_rs:
        evidence.append("build.rs (no cc)")
    if root_sys:
        return "BINDING", "; ".join(evidence) if evidence else "external -sys in root deps"
    return "REWRITE", "; ".join(evidence) if evidence else "no C link path"

def main():
    rows = []
    for p in CORPUS["tiers"]["pairs"]:
        for side in ("c_side", "rust_side"):
            r = p[side]
            repo = r["repo"]
            cc = CLASSES[repo]
            detail = cc["component_detail"]
            src = {k: v for k, v in detail.items() if v["class"] in SRC_CLASSES}
            n_src = len(src)
            n_rust = sum(1 for v in src.values() if v["class"] == "RUST")
            n_c = sum(1 for v in src.values() if v["class"] in ("C", "CPP"))
            n_mixed = sum(1 for v in src.values() if v["class"] == "MIXED")
            rust_share = (n_rust + n_mixed) / n_src if n_src else 0.0
            cnt = {}
            for v in src.values():
                cnt[v["class"]] = cnt.get(v["class"], 0) + 1
            rec = {
                "repo": repo, "tier": r["tier"], "side": side,
                "n_components": cc["components"], "n_source": n_src,
                "n_rust": n_rust, "n_c_cpp": n_c, "n_mixed": n_mixed,
                "rust_share": round(rust_share, 4), "classes": cnt,
                "has_rust": (n_rust + n_mixed) > 0,
            }
            if side == "rust_side":
                cargo = fetch_cargo(repo, r["head_sha"])
                rec["binding_verdict"], rec["binding_evidence"] = binding_verdict(cargo)
            rows.append(rec)
    # persist
    json.dump(rows, open(ROOT / "snapshots" / "repo_signals.json", "w"), indent=2)
    # summary table
    print(f"{'repo':44s} {'side':4s} {'src':>3s} {'R':>2s} {'C':>2s} {'M':>2s} {'RustShare':>9s} {'bind'}")
    for r in rows:
        b = r.get("binding_verdict", "")
        print(f"{r['repo']:44s} {r['side'][0]:4s} {r['n_source']:3d} {r['n_rust']:2d} "
              f"{r['n_c_cpp']:2d} {r['n_mixed']:2d} {r['rust_share']*100:8.1f}% {b}")
    print()
    # tier aggregates (Rust-side only = adoption)
    from collections import defaultdict
    tier_rust = defaultdict(lambda: [0, 0])  # [rust repos, total rust-side]
    for r in rows:
        if r["side"] == "rust_side":
            tier_rust[r["tier"]][1] += 1
            if r["rust_share"] >= 0.9:
                tier_rust[r["tier"]][0] += 1
    print("Tier (Rust-side repos ≥90% Rust):")
    for t, (n, tot) in sorted(tier_rust.items()):
        print(f"  {t}: {n}/{tot}")
    print()
    bind = [r for r in rows if r["side"] == "rust_side"]
    n_bind = sum(1 for r in bind if r["binding_verdict"] == "BINDING")
    n_rew = sum(1 for r in bind if r["binding_verdict"] == "REWRITE")
    n_unc = sum(1 for r in bind if r["binding_verdict"] == "UNCLEAR")
    print(f"binding_vs_rewrite: BINDING {n_bind}/16, REWRITE {n_rew}/16, UNCLEAR {n_unc}/16")
    mixed = [r for r in rows if r["n_mixed"] > 0]
    print(f"repos with MIXED components: {len(mixed)} — {[r['repo'] for r in mixed]}")

if __name__ == "__main__":
    main()
