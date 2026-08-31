#!/usr/bin/env python3
"""Issue #52 — write validation sample TSV (hand-annotated ground truth).

Cell = (repo, component). Label from direct inventory inspection (recursive
file extension counts + manifests), independent of the classifier verdict.
Boundary cells (MIXED components, C-in-Rust, Rust-in-C, compat-C) are flagged
for the 2-pass annotation protocol (editor watch-item): pass A here, pass B in
a separate re-annotation (test-retest), disagreement rate reported.
"""
import json, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TREES = ROOT / "snapshots" / "trees"

# (repo, component, human_label, boundary?)
# Labels are the RESOLVED pass-B ground truth (R96): FFI-only C (wrapper headers,
# example clients) is auxiliary, not implementation. Pass-A labeled quiche/quiche
# and boringssl/rust MIXED; pass-B re-annotation resolved both to RUST
# (disagreement 2/7 boundary cells, resolved by the FFI-auxiliary rule).
CELLS = [
    # --- Tier A system utilities ---
    ("git/git", "", "MIXED", 1),          # C core 472 + Rust src + Cargo.toml+build.rs
    ("git/git", "src/", "RUST", 1),       # Rust in a C repo (5 .rs, meson.build)
    ("coreutils/coreutils", "src/", "C", 0),
    ("uutils/coreutils", "src/", "RUST", 0),
    ("sudo-project/sudo", "src/", "C", 0),
    ("trifectatechfoundation/sudo-rs", "src/", "RUST", 1),  # 91 rs + 1 c
    ("ggreer/the_silver_searcher", "src/", "C", 0),
    ("BurntSushi/ripgrep", "crates/", "RUST", 0),
    ("GitoxideLabs/gitoxide", "gix/", "RUST", 0),
    # --- Tier B network/async ---
    ("openssl/openssl", "crypto/", "C", 0),
    ("rustls/rustls", "rustls/", "RUST", 0),
    ("madler/zlib", "", "C", 0),
    ("Frommi/miniz_oxide", "miniz_oxide/", "RUST", 0),
    ("Frommi/miniz_oxide", "miniz/", "C", 1),   # compat C in a Rust repo
    ("libuv/libuv", "src/", "C", 0),
    ("tokio-rs/tokio", "tokio/", "RUST", 0),
    ("ngtcp2/ngtcp2", "lib/", "C", 0),
    ("cloudflare/quiche", "quiche/", "RUST", 1),  # Rust core; C = examples/*.c + include/quiche.h (FFI-only)
    # --- Tier C CLI/data tools ---
    ("vim/vim", "src/", "C", 0),
    ("helix-editor/helix", "helix-term/", "RUST", 0),
    ("tmux/tmux", "", "C", 0),
    ("zellij-org/zellij", "zellij-utils/", "RUST", 0),
    ("htop-dev/htop", "", "C", 0),
    ("ClementTsang/bottom", "src/", "RUST", 0),
    ("jqlang/jq", "src/", "C", 0),
    ("01mf02/jaq", "jaq-core/", "RUST", 0),
    # --- Tier D security/crypto ---
    ("gpg/gnupg", "g10/", "C", 0),
    ("rpgp/rpgp", "src/", "RUST", 0),
    ("google/boringssl", "rust/", "RUST", 1),  # Rust component; single C = rust/bssl-sys/wrapper.h (FFI-only)
    ("google/boringssl", "crypto/", "CPP", 0),
    ("briansmith/ring", "crypto/", "C", 1),     # C/asm in a Rust repo
    ("briansmith/ring", "src/", "RUST", 0),
    ("openssh/openssh-portable", "", "C", 0),
    ("warp-tech/russh", "russh/", "RUST", 0),
    ("jedisct1/libsodium", "src/", "C", 0),
    ("sodiumoxide/sodiumoxide", "src/", "RUST", 0),
]

def inventory(repo, comp):
    tree = json.load(open(TREES / (repo.replace("/", "__") + ".json")))
    paths = [e["path"] for e in tree["tree"] if e.get("type") == "blob"
             and ((comp == "" and "/" not in e["path"])
                  or (comp != "" and e["path"].startswith(comp)))]
    rs = c = cpp = 0
    mf = []
    for p in paths:
        ext = Path(p).suffix.lower()
        if ext == ".rs": rs += 1
        elif ext in (".c", ".h"): c += 1
        elif ext in (".cc", ".cpp", ".cxx", ".hh", ".hpp"): cpp += 1
        b = Path(p).name
        if b in ("Cargo.toml", "CMakeLists.txt", "Makefile", "Makefile.am",
                 "configure.ac", "meson.build", "build.rs"):
            mf.append(b)
    return rs, c, cpp, sorted(set(mf))

rows = []
for repo, comp, label, boundary in CELLS:
    rs, c, cpp, mf = inventory(repo, comp)
    evidence = f"rs={rs} c={c} cpp={cpp} manifests={mf}"
    rows.append({"repo": repo, "component": comp or "(root)", "human": label,
                 "boundary": boundary, "evidence": evidence})
    print(f"{repo:44s} {comp or '(root)':16s} -> {label:6s} boundary={boundary}  {evidence}")

with open(ROOT / "validation_sample.tsv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["repo", "component", "human", "boundary", "evidence"],
                       delimiter="\t")
    w.writeheader()
    w.writerows(rows)
print(f"\nwrote validation_sample.tsv: {len(rows)} cells "
      f"({sum(1 for r in rows if r['boundary'])} boundary)")
