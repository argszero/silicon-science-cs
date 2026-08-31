#!/usr/bin/env python3
"""Build corpus.json for issue #52 (Rust in the Wild — C/C++ -> Rust rewrites census).

Era-paired corpus: for each domain, the canonical C/C++ project and its Rust
counterpart/successor (role-coverage rule; no star threshold, no activity filter).
Pins default_branch, head_sha, stars, language, description, size via GitHub API.

Tier A system utilities: coreutils/uutils, sudo/sudo-rs, ag/ripgrep, git/gitoxide
Tier B network/async:    OpenSSL/rustls, zlib/miniz_oxide, libuv/tokio, ngtcp2/quiche
Tier C CLI/data tools:   vim/helix, tmux/zellij, htop/bottom, jq/jaq
Tier D security/crypto:  GnuPG/rpgp, BoringSSL/ring, OpenSSH/russh, libsodium/sodiumoxide
"""
import json, subprocess, sys, time

PAIRS = [
    # (c_repo, rust_repo, tier, c_role, rust_role)
    ("coreutils/coreutils", "uutils/coreutils", "Tier A system utilities",
     "GNU coreutils (C)", "uutils — Rust reimplementation of coreutils"),
    ("sudo-project/sudo", "trifectatechfoundation/sudo-rs", "Tier A system utilities",
     "sudo (C)", "sudo-rs — memory-safe reimplementation of sudo/su"),
    ("ggreer/the_silver_searcher", "BurntSushi/ripgrep", "Tier A system utilities",
     "the_silver_searcher ag (C)", "ripgrep — Rust successor search tool"),
    ("git/git", "GitoxideLabs/gitoxide", "Tier A system utilities",
     "git (C)", "gitoxide — pure-Rust implementation of git"),
    ("openssl/openssl", "rustls/rustls", "Tier B network/async",
     "OpenSSL (C)", "rustls — Rust TLS implementation"),
    ("madler/zlib", "Frommi/miniz_oxide", "Tier B network/async",
     "zlib (C)", "miniz_oxide — Rust replacement for miniz/zlib"),
    ("libuv/libuv", "tokio-rs/tokio", "Tier B network/async",
     "libuv (C event loop)", "tokio — Rust async runtime"),
    ("ngtcp2/ngtcp2", "cloudflare/quiche", "Tier B network/async",
     "ngtcp2 (C QUIC)", "quiche — Rust QUIC implementation"),
    ("vim/vim", "helix-editor/helix", "Tier C CLI/data tools",
     "vim (C)", "helix — Rust modal editor"),
    ("tmux/tmux", "zellij-org/zellij", "Tier C CLI/data tools",
     "tmux (C)", "zellij — Rust terminal multiplexer"),
    ("htop-dev/htop", "ClementTsang/bottom", "Tier C CLI/data tools",
     "htop (C)", "bottom — Rust system monitor"),
    ("jqlang/jq", "01mf02/jaq", "Tier C CLI/data tools",
     "jq (C)", "jaq — Rust clone of jq"),
    ("gpg/gnupg", "rpgp/rpgp", "Tier D security/crypto",
     "GnuPG (C)", "rpgp — pure-Rust OpenPGP implementation"),
    ("google/boringssl", "briansmith/ring", "Tier D security/crypto",
     "BoringSSL (C++)", "ring — Rust crypto primitives library"),
    ("openssh/openssh-portable", "warp-tech/russh", "Tier D security/crypto",
     "OpenSSH (C)", "russh — Rust SSH implementation"),
    ("jedisct1/libsodium", "sodiumoxide/sodiumoxide", "Tier D security/crypto",
     "libsodium (C)", "sodiumoxide — Rust FFI binding (NOT a rewrite — signal contrast)"),
]

def gh_json(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ! gh api {path} failed: {r.stderr[:100]}", file=sys.stderr)
        return None
    return json.loads(r.stdout)

def main():
    out = {
        "title": "Rust in the Wild: A Corpus-Scale Census of C/C++ -> Rust Rewrites in Open-Source Software",
        "issue": 52,
        "snapshot": "2026-08-31",
        "tiers": {"pairs": []},
    }
    for c_repo, r_repo, tier, c_role, r_role in PAIRS:
        pair = {"tier": tier, "c_side": None, "rust_side": None}
        for side, repo, role in (("c_side", c_repo, c_role), ("rust_side", r_repo, r_role)):
            meta = gh_json(f"repos/{repo}")
            if meta is None:
                print(f"  SKIP {repo} (API fail)", file=sys.stderr)
                continue
            db = meta.get("default_branch", "main")
            ref = gh_json(f"repos/{repo}/git/ref/heads/{db}")
            sha = ref["object"]["sha"] if ref else None
            rec = {
                "repo": repo, "tier": tier, "role": role, "side": side,
                "lang": meta.get("language"), "stars": meta.get("stargazers_count"),
                "size_kb": meta.get("size"), "default_branch": db, "head_sha": sha,
                "description": (meta.get("description") or "")[:120],
            }
            pair[side] = rec
            print(f"  {repo:42s} {str(meta.get('stargazers_count')):>7s}* {db:12s} {str(sha)[:10]}", flush=True)
            time.sleep(0.3)
        out["tiers"]["pairs"].append(pair)
    json.dump(out, open("corpus.json", "w"), indent=2)
    n = len(out["tiers"]["pairs"])
    print(f"corpus.json: {n} pairs ({n*2} repos) written")

if __name__ == "__main__":
    main()
