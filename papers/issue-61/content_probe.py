#!/usr/bin/env python3
"""Issue #61 — content probes: README head + crypto-dir content (Channel 2/3).

For every corpus repo: fetch README head (45 lines, badges/HTML stripped) and probe
key crypto-related paths from the tree for PQC identifiers (Channel 2) + API usage
(Channel 3). Bounded: README always; crypto-path content only for repos that already
showed path or manifest signals (candidate positives).

Outputs:
  snapshots/content_probe_evidence.json — per repo: {readme_hits, path_hits, api_hits}
  snapshots/content_probe_stats.txt
"""
import json
import os
import re
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
TREES = SNAP / "trees"

# Channel 2 source identifiers (dictionary v1.1 — falcon excluded bare)
CH2 = {
    "ML-KEM": re.compile(r"ml[\s_-]?kem|mlkem(?:768|1024|512)?\b|kyber(?:512|768|1024)?\b", re.I),
    "ML-DSA": re.compile(r"ml[\s_-]?dsa|mldsa(?:44|65|87)?\b|dilithium\d?\b", re.I),
    "SLH-DSA": re.compile(r"slh[\s_-]?dsa|slhdsa|sphincs\+?|sphincs(?:256)?\b", re.I),
    "FN-DSA/Falcon": re.compile(r"fn[\s_-]?dsa|fn_dsa|falcon(?:512|1024)?(?=.*(?:sign|sig|pq|kem))", re.I),
    "Hybrid": re.compile(r"x25519mlkem|x25519_mlkem|x25519mlkem768|p256mlkem|mlkem768x25519|x25519.?kyber", re.I),
    "generic-pq": re.compile(r"post[\s_-]?quantum|quantum[\s_-]?safe|quantum[\s_-]?resist|\bPQClean\b|\bpqclean\b", re.I),
    "NIST-schemes": re.compile(r"\bBIKE\b|\bHQC\b|mceliece|ntruprime|sntrup(?:761|1277)|frodo", re.I),
}
# Channel 3 API usage probes (L3 evidence)
CH3 = {
    "OpenSSL-EVP_KEM": re.compile(r"EVP_KEM|EVP_PKEY_Q_keygen|OSSL_KEM"),
    "BC-MLKEM": re.compile(r"MLKEMKeyPairGenerator|MLDSAKeyPairGenerator|SLHDSAKeyPairGenerator|MLKEMParameterSpec|KyberKeyPairGenerator"),
    "Go-mlkem": re.compile(r"circl/kem/mlkem|mlkem768\.NewKey|circl/sign/dilithium|circl/sign/slhdsa"),
    "Rust-pqcrypto": re.compile(r"pqcrypto_(?:ml_kem|mlkem|dilithium|sphincsplus)::"),
    "liboqs-API": re.compile(r"OQS_KEM_new|OQS_SIG_new|OQS_KEM_alg_ml_kem"),
    "wolfSSL-API": re.compile(r"wolfSSL_Use_ML_KEM|wc_MlKemKey|WOLFSSL_MLKEM"),
    "JDK-ML-KEM": re.compile(r"KeyPairGenerator\.getInstance\(\s*[\"']ML[\s_-]?KEM|jdk\.crypto\.mlkem"),
    "TLS-group": re.compile(r"x25519_mlkem768|x25519mlkem768|MLKEM768"),
}
README_CANDIDATES = ["README.md", "README.rst", "readme.md", "README", "Readme.md", "readme.rst"]
CRYPTO_DIR_RE = re.compile(r"(^|/)(crypto|src/crypto|cryptography|pqcrypto|oqs|liboqs|pqclean|ml_kem|mlkem|dilithium|sphincs|kyber|third_party|vendor|ext)/")


def raw_fetch(repo, branch, path):
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", "12", "-o", "-", "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=18,
        )
        code = out.stdout.strip()[-3:] if out.stdout else "000"
        body = out.stdout[:-3] if len(out.stdout) > 3 else ""
        if code == "200":
            return body
    except subprocess.TimeoutExpired:
        pass
    return ""


def strip_md(content, limit=4500):
    """Keep first `limit` chars, strip badges/images/html/links."""
    content = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", content)   # images
    content = re.sub(r"<[^>]+>", "", content)                # html tags
    content = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", content)  # links -> text
    return content[:limit]


def scan(content, patterns):
    hits = set()
    for name, pat in patterns.items():
        if pat.search(content):
            hits.add(name)
    return hits


def main():
    corpus = json.load(open(SNAP / "tier_ab_corpus.json"))
    dep_evidence = json.load(open(SNAP / "pqc_dep_evidence.json"))
    repos = sorted(corpus.keys())

    # candidate positives: path-signal repos (from R112 scan re-derived here) or dep-signal
    path_signal = set()
    for repo in repos:
        fname = repo.replace("/", "__") + ".json"
        fpath = TREES / fname
        if not fpath.exists():
            continue
        data = json.load(open(fpath))
        for e in data.get("tree", []):
            p = e.get("path", "")
            if CH2["ML-KEM"].search(p) or CH2["ML-DSA"].search(p) or CH2["SLH-DSA"].search(p) or CH2["generic-pq"].search(p):
                path_signal.add(repo)
                break
    dep_signal = {r for r, v in dep_evidence.items() if v["pqc_deps"]}
    candidates = path_signal | dep_signal | {r for r, v in corpus.items() if v.get("is_anchor")}
    print(f"candidate positives (path ∪ dep ∪ anchor): {len(candidates)} / {len(repos)}", flush=True)

    tasks = []
    for repo in repos:
        branch = corpus[repo].get("default_branch", "main")
        tasks.append((repo, branch, repo in candidates))
    print(f"fetching README heads for {len(tasks)} repos + crypto-dir content for candidates (parallel 12)...", flush=True)

    def work(t):
        repo, branch, is_cand = t
        result = {"readme_hits": [], "path_content_hits": [], "api_hits": [], "notes": []}
        # README head
        readme_path = None
        data = None
        fname = repo.replace("/", "__") + ".json"
        fpath = TREES / fname
        if fpath.exists():
            data = json.load(open(fpath))
            for e in data.get("tree", []):
                p = e.get("path", "")
                if os.path.basename(p) in README_CANDIDATES and p.count("/") <= 1:
                    readme_path = p
                    break
        if readme_path:
            body = raw_fetch(repo, branch, readme_path)
            if body:
                result["readme_hits"] = sorted(scan(strip_md(body), CH2))
        # crypto-dir content for candidates (bounded: up to 12 files)
        if is_cand and data:
            crypto_files = [e["path"] for e in data.get("tree", [])
                            if e.get("type") == "blob" and CRYPTO_DIR_RE.search(e["path"])]
            crypto_files = sorted(crypto_files, key=lambda p: (p.count("/"), len(p)))[:12]
            combined = ""
            for p in crypto_files:
                body = raw_fetch(repo, branch, p)
                if body:
                    combined += "\n" + body[:4000]
                    result["notes"].append(p)
            if combined:
                result["path_content_hits"] = sorted(scan(combined, CH2))
                result["api_hits"] = sorted(scan(combined, CH3))
        return repo, result

    results = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        for i, (repo, r) in enumerate(pool.map(work, tasks)):
            results[repo] = r
            if (i + 1) % 40 == 0 or i == len(tasks) - 1:
                print(f"  [{i+1}/{len(tasks)}]", flush=True)

    json.dump(results, open(SNAP / "content_probe_evidence.json", "w"), indent=1)

    # stats
    with_readme_hits = {r: v["readme_hits"] for r, v in results.items() if v["readme_hits"]}
    with_path_hits = {r: v["path_content_hits"] for r, v in results.items() if v["path_content_hits"]}
    with_api = {r: v["api_hits"] for r, v in results.items() if v["api_hits"]}
    lines = [
        f"repos with README-head PQC mention: {len(with_readme_hits)}",
        f"repos with crypto-dir content PQC hit: {len(with_path_hits)}",
        f"repos with API-usage (L3) evidence: {len(with_api)}",
        "",
        "README-mention repos (docs/marketing vs implementation — annotate):",
    ]
    for repo, hits in sorted(with_readme_hits.items(), key=lambda kv: -corpus[kv[0]].get("stars", 0)):
        lines.append(f"  {corpus[repo]['stars']:>8}  {repo:<45} {hits}")
    lines.append("")
    lines.append("API-usage (L3) repos:")
    for repo, hits in sorted(with_api.items(), key=lambda kv: -corpus[kv[0]].get("stars", 0)):
        lines.append(f"  {corpus[repo]['stars']:>8}  {repo:<45} {hits}")
    with open(SNAP / "content_probe_stats.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
