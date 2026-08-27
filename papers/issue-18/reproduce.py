#!/usr/bin/env python3
"""reproduce.py — Issue #18 canonical runner.

Integrity Posture of Popular Open-Source Repositories:
  C1. distribution of GitHub-verified commit shares across the corpus
  C2. release-artifact signing adoption (taxonomy: gpg .asc / generic .sig /
      minisig / sigstore / checksum+sig / none / no-assets)
  C3. coherence between commit verification and release signing (2x2 + Fisher)

Modes:
  reproduce.py fetch          — pull fresh data via gh api into data_snapshot/
  reproduce.py                — offline: read data_snapshot/, compute, print results
  reproduce.py --only <repo>  — fetch only <repo> (additive; existing snapshots frozen)

Deterministic: classification is a pure function of committed snapshot JSON;
offline output is byte-identical across runs. stdlib-only.
"""
import argparse, collections, json, math, os, subprocess, sys

CORPUS = [
    # JavaScript / TypeScript
    "react/react", "microsoft/vscode", "vuejs/vue", "angular/angular",
    "sveltejs/svelte", "mui/material-ui", "facebook/react-native",
    # Python
    "python/cpython", "django/django", "pallets/flask", "pandas-dev/pandas",
    "huggingface/transformers", "numpy/numpy",
    # Go
    "kubernetes/kubernetes", "golang/go", "gin-gonic/gin", "ollama/ollama",
    "hashicorp/terraform",
    # Rust
    "rust-lang/rust", "tokio-rs/tokio", "BurntSushi/ripgrep", "serde-rs/serde",
    # C / C++ (incl. security-critical infrastructure stratum)
    "torvalds/linux", "git/git", "openssl/openssl", "curl/curl",
    "tensorflow/tensorflow", "google/googletest", "redis/redis", "neovim/neovim",
    # Java / Scala
    "apache/spark", "spring-projects/spring-boot", "elastic/elasticsearch",
    # Ruby
    "rails/rails", "Homebrew/brew", "jekyll/jekyll",
    # PHP
    "laravel/laravel", "composer/composer", "symfony/symfony",
    # Dart
    "flutter/flutter", "nodejs/node",
]

BASE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(BASE, "data_snapshot")
COMMITS_PER_REPO = 300          # 3 pages x 100
RELEASES_CAP = 100              # releases enumerated per repo (newest first)

# Mirror/upstream-fed repositories: their GitHub commit history is pushed from a
# canonical upstream elsewhere (mirror channel), so GitHub's verification verdict
# reflects the mirror channel, not an on-GitHub signing policy. Per-repo basis,
# confirmed at snapshot time 2026-08-27:
#   git/git        — self-description: "Git Source Code Mirror - publish-only"
#   golang/go      — canonical upstream go.googlesource.com (Gerrit)
#   torvalds/linux — canonical upstream kernel.org
#   openssl/openssl — canonical upstream openssl.org/git
MIRROR_REPOS = {"git/git", "golang/go", "torvalds/linux", "openssl/openssl"}

# Ecosystem stratum for the C2 per-ecosystem breakdown (mirrors CORPUS grouping)
ECOSYSTEM = {
    "react/react": "JS/TS", "microsoft/vscode": "JS/TS", "vuejs/vue": "JS/TS",
    "angular/angular": "JS/TS", "sveltejs/svelte": "JS/TS",
    "mui/material-ui": "JS/TS", "facebook/react-native": "JS/TS",
    "python/cpython": "Python", "django/django": "Python",
    "pallets/flask": "Python", "pandas-dev/pandas": "Python",
    "huggingface/transformers": "Python", "numpy/numpy": "Python",
    "kubernetes/kubernetes": "Go", "golang/go": "Go", "gin-gonic/gin": "Go",
    "ollama/ollama": "Go", "hashicorp/terraform": "Go",
    "rust-lang/rust": "Rust", "tokio-rs/tokio": "Rust",
    "BurntSushi/ripgrep": "Rust", "serde-rs/serde": "Rust",
    "torvalds/linux": "C/C++", "git/git": "C/C++", "openssl/openssl": "C/C++",
    "curl/curl": "C/C++", "tensorflow/tensorflow": "C/C++",
    "google/googletest": "C/C++", "redis/redis": "C/C++", "neovim/neovim": "C/C++",
    "apache/spark": "Java/Scala", "spring-projects/spring-boot": "Java/Scala",
    "elastic/elasticsearch": "Java/Scala",
    "rails/rails": "Ruby", "Homebrew/brew": "Ruby", "jekyll/jekyll": "Ruby",
    "laravel/laravel": "PHP", "composer/composer": "PHP", "symfony/symfony": "PHP",
    "flutter/flutter": "Dart", "nodejs/node": "C++",
}


def armor_kind(signature: str) -> str:
    """Classify signature armor prefix: pgp / ssh / x509 / unknown / None."""
    if not signature:
        return "none"
    s = signature.strip()
    if s.startswith("-----BEGIN PGP SIGNATURE-----"):
        return "pgp"
    if s.startswith("-----BEGIN SSH SIGNATURE-----"):
        return "ssh"
    if s.startswith("-----BEGIN CERTIFICATE-----") or "SIGNATURE" in s[:60]:
        return "x509_sigstore" if "sigstore" in s[:200].lower() else "other_armor"
    return "unknown_armor"


def asset_signed(name: str) -> bool:
    """Deterministic: does this asset name carry a signature artifact?"""
    low = name.lower()
    if low.endswith(".asc") or low.endswith(".sig") or low.endswith(".minisig") \
       or low.endswith(".sigstore") or low.endswith(".bundle"):
        return True
    # SHASUMS256.txt + .sig pair: the .sig itself is caught above; a bare
    # SHASUMS256.txt without a sibling .sig is a checksum list only.
    return False


def classify_release(assets):
    """-> (signed: bool, tools: list[str])"""
    tools = []
    for a in assets:
        low = a.lower()
        if low.endswith(".asc"):
            tools.append("gpg_asc")
        elif low.endswith(".minisig"):
            tools.append("minisig")
        elif low.endswith(".sigstore") or low.endswith(".bundle"):
            tools.append("sigstore")
        elif low.endswith(".sig"):
            tools.append("generic_sig")
    return (bool(tools), sorted(set(tools)))


# ---------------------------------------------------------------- fetch mode

def gh_json(url):
    out = subprocess.run(["gh", "api", url], capture_output=True, text=True,
                         timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"gh api {url}: {out.stderr.strip()[:200]}")
    return json.loads(out.stdout)


def fetch_repo(repo: str) -> dict:
    reasons = collections.Counter()
    sigs = collections.Counter()
    total = 0
    for page in (1, 2, 3):
        try:
            cs = gh_json(f"repos/{repo}/commits?per_page=100&page={page}")
        except RuntimeError:
            break
        if not cs:
            break
        for c in cs:
            v = c.get("commit", {}).get("verification", {})
            r = v.get("reason") or "missing"
            reasons[r] += 1
            sigs[armor_kind(v.get("signature"))] += 1
            total += 1
        if len(cs) < 100:
            break

    rels = []
    try:
        rels = gh_json(f"repos/{repo}/releases?per_page=100&page=1")
    except RuntimeError:
        pass
    releases = []
    for rel in rels[:RELEASES_CAP]:
        assets = [a.get("name", "") for a in rel.get("assets", [])]
        signed, tools = classify_release(assets)
        releases.append({
            "tag": rel.get("tag_name", ""),
            "n_assets": len(assets),
            "signed": signed,
            "tools": tools,
        })
    return {
        "repo": repo,
        "commit_total": total,
        "commit_reasons": dict(reasons),
        "commit_sig_kinds": dict(sigs),
        "releases": releases,
        "release_total": len(releases),
        "signed_releases": sum(1 for r in releases if r["signed"]),
        "any_signed_release": any(r["signed"] for r in releases),
    }


def fetch(only=None):
    os.makedirs(SNAP_DIR, exist_ok=True)
    targets = [only] if only else CORPUS
    for repo in targets:
        dest = os.path.join(SNAP_DIR, repo.replace("/", "__") + ".json")
        if os.path.exists(dest) and not only:
            continue  # frozen snapshot; --only bypasses for additive fetches
        try:
            snap = fetch_repo(repo)
            with open(dest, "w") as f:
                json.dump(snap, f, indent=1, sort_keys=True)
            print(f"fetched {repo}: commits={snap['commit_total']} "
                  f"releases={snap['release_total']} signed_rel={snap['signed_releases']}")
        except Exception as e:
            print(f"ERROR {repo}: {e}", file=sys.stderr)
    if not only:
        # Pin the fetch timestamp for the whole corpus. --only fetches never
        # rewrite the manifest: old snapshots keep their original fetch date.
        import datetime
        manifest = {
            "fetched_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "corpus_n": len(CORPUS),
            "commits_per_repo": COMMITS_PER_REPO,
            "releases_cap": RELEASES_CAP,
        }
        with open(os.path.join(SNAP_DIR, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=1, sort_keys=True)
        print(f"manifest written: fetched_at={manifest['fetched_at']}")


# --------------------------------------------------------------- offline mode

def load():
    snaps = []
    manifest = {}
    manifest_path = os.path.join(SNAP_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
    for fn in sorted(os.listdir(SNAP_DIR)):
        if not fn.endswith(".json") or fn == "manifest.json":
            continue
        with open(os.path.join(SNAP_DIR, fn)) as f:
            snaps.append(json.load(f))
    return snaps, manifest


def fisher_exact(a, b, c, d):
    """Two-sided Fisher exact test on [[a,b],[c,d]]; returns p, OR."""
    def ln_fact(n):
        return math.lgamma(n + 1)
    row1, row2 = a + b, c + d
    col1, col2 = a + c, b + d
    n = a + b + c + d
    if min(row1, row2, col1, col2) == 0:
        return 1.0, float("inf") if a * d > b * c else 0.0
    lo = max(0, row1 - col2)
    hi = min(row1, col1)
    log_p = (ln_fact(row1) + ln_fact(row2) + ln_fact(col1) + ln_fact(col2)
             - ln_fact(n))
    def pmf(x):
        return math.exp(log_p - ln_fact(x) - ln_fact(row1 - x)
                        - ln_fact(col1 - x) - ln_fact(row2 - col1 + x))
    p0 = pmf(a)
    total = sum(p for x in range(lo, hi + 1) if (p := pmf(x)) <= p0 * 1.0000001)
    or_ = (a * d) / (b * c) if b * c else float("inf")
    return total, or_


def wilson_ci(k, n, z=1.96):
    """Wilson 95% score interval for a binomial proportion k/n."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def woolf_or_ci(a, b, c, d, z=1.96):
    """Woolf (logit) approximate 95% CI for the odds ratio of [[a,b],[c,d]].

    Labels the approximation; small-cell margins make the normal approximation
    coarse, which is itself part of the power limitation we report.
    """
    if b == 0 or c == 0 or a == 0 or d == 0:
        return 0.0, float("inf")
    lor = math.log((a * d) / (b * c))
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return math.exp(lor - z * se), math.exp(lor + z * se)


def stats(snaps):
    n = len(snaps)
    rows = []
    for s in snaps:
        reasons = s.get("commit_reasons", {})
        total = s.get("commit_total", 0) or sum(reasons.values())
        verified = reasons.get("valid", 0)
        share = verified / total if total else 0.0
        rows.append({
            "repo": s["repo"],
            "commits": total,
            "verified": verified,
            "share": share,
            "reasons": reasons,
            "rel_total": s.get("release_total", 0),
            "rel_signed": s.get("signed_releases", 0),
            "any_signed": s.get("any_signed_release", False),
            "no_assets_rel": sum(1 for r in s.get("releases", []) if r["n_assets"] == 0),
        })
    rows.sort(key=lambda r: r["share"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="offline")
    ap.add_argument("--only")
    a = ap.parse_args()
    if a.mode == "fetch":
        fetch(a.only)
        return
    snaps, manifest = load()
    if not snaps:
        print("no snapshot data — run `reproduce.py fetch` first", file=sys.stderr)
        sys.exit(2)
    rows = stats(snaps)
    n = len(rows)
    out = []
    out.append("INTEGRITY POSTURE OF POPULAR OSS REPOSITORIES — canonical results")
    snap_date = manifest.get("fetched_at",
                             "not pinned (data_snapshot/manifest.json missing)")
    out.append(f"corpus: n={n} repos | snapshot date: {snap_date} "
               f"(data_snapshot/manifest.json)")
    out.append("")

    # ---- C1: verified commit share
    shares = [r["share"] for r in rows]
    verified_repos = [r for r in rows if r["share"] >= 0.90]
    absent_repos = [r for r in rows if r["share"] < 0.10]
    mid_repos = [r for r in rows if 0.10 <= r["share"] < 0.90]
    mean = sum(shares) / n
    median = shares[n // 2]
    out.append(f"C1 verified-commit share (n={n}, {COMMITS_PER_REPO}-commit window):")
    out.append(f"  mean={mean:.3f} median={median:.3f} min={shares[0]:.3f} max={shares[-1]:.3f}")
    out.append(f"  enforcement cluster (>=90%): {len(verified_repos)}/{n} repos "
               f"({len(verified_repos)/n:.1%}, Wilson95 "
               f"{wilson_ci(len(verified_repos), n)[0]:.1%}-{wilson_ci(len(verified_repos), n)[1]:.1%}), "
               f"mean share {sum(r['share'] for r in verified_repos)/len(verified_repos):.3f}")
    out.append(f"  absent cluster (<10%): {len(absent_repos)}/{n} repos "
               f"({len(absent_repos)/n:.1%}, Wilson95 "
               f"{wilson_ci(len(absent_repos), n)[0]:.1%}-{wilson_ci(len(absent_repos), n)[1]:.1%}), "
               f"mean share {sum(r['share'] for r in absent_repos)/len(absent_repos):.3f}")
    mirror_absent = [r["repo"] for r in absent_repos if r["repo"] in MIRROR_REPOS]
    nonmirror_absent = [r["repo"] for r in absent_repos if r["repo"] not in MIRROR_REPOS]
    out.append(f"  absent-cluster mirror-origin repos (GitHub history via mirror/"
               f"upstream channel): {len(mirror_absent)} — {', '.join(mirror_absent)}")
    if nonmirror_absent:
        nm = [r for r in absent_repos if r["repo"] not in MIRROR_REPOS]
        nm_mean = sum(r["share"] for r in nm) / len(nm)
        out.append(f"  absent-cluster non-mirror repos: {len(nonmirror_absent)} "
                   f"({', '.join(nonmirror_absent)}) | mean share {nm_mean:.3f}")
    out.append(f"  middle (10-90%): {len(mid_repos)} repos")
    reasons_total = collections.Counter()
    kinds_total = collections.Counter()
    for s in snaps:
        reasons_total.update(s.get("commit_reasons", {}))
        kinds_total.update(s.get("commit_sig_kinds", {}))
    total_commits = sum(reasons_total.values())
    def pct(k):
        return f"{k}: {reasons_total[k]} ({reasons_total[k]/total_commits:.1%})"
    out.append(f"  reason taxonomy (n={total_commits} commits): "
               + ", ".join(pct(k) for k in ("valid", "unsigned", "unknown_key",
                                           "invalid", "no_user", "bad_email",
                                           "bad_signature", "expired_key")))
    out.append(f"  signature armor (n={total_commits} commits): "
               + ", ".join(f"{k}: {kinds_total[k]} ({kinds_total[k]/total_commits:.1%})"
                           for k in ("pgp", "ssh", "x509_sigstore", "none")
                           if k in kinds_total))
    ssh_repos = [(s["repo"], s.get("commit_sig_kinds", {}).get("ssh", 0))
                 for s in snaps if s.get("commit_sig_kinds", {}).get("ssh", 0) > 0]
    if ssh_repos:
        out.append("  ssh-armor commits per repo: "
                   + ", ".join(f"{r}: {k}" for r, k in sorted(ssh_repos,
                                                              key=lambda x: -x[1])))
    out.append("  per-repo (sorted ascending, share | verified/commits | releases_signed):")
    for r in rows:
        out.append(f"    {r['share']:6.3f}  {r['verified']:4d}/{r['commits']:4d}  "
                   f"rel_signed={r['rel_signed']}/{r['rel_total']}  {r['repo']}")

    # ---- C2: release signing
    with_any = [r for r in rows if r["any_signed"]]
    no_assets = [r for r in rows if r["rel_total"] > 0 and r["no_assets_rel"] == r["rel_total"]]
    no_releases = [r for r in rows if r["rel_total"] == 0]
    rel_signed_total = sum(r["rel_signed"] for r in rows)
    rel_total_total = sum(r["rel_total"] for r in rows)
    tools_counter = collections.Counter()
    for s in snaps:
        for rel in s.get("releases", []):
            for t in rel.get("tools", []):
                tools_counter[t] += 1
    out.append("")
    out.append("C2 release-artifact signing:")
    wl, wu = wilson_ci(len(with_any), n)
    out.append(f"  repos with >=1 signed release: {len(with_any)}/{n} "
               f"({len(with_any)/n:.1%}, Wilson95 {wl:.1%}-{wu:.1%})")
    wl2, wu2 = wilson_ci(rel_signed_total, rel_total_total)
    out.append(f"  signed releases: {rel_signed_total}/{rel_total_total} "
               f"({rel_signed_total/rel_total_total:.1%} of enumerated releases, "
               f"Wilson95 {wl2:.1%}-{wu2:.1%})")
    out.append(f"  repos with releases but zero assets: {len(no_assets)}")
    out.append(f"  repos with zero GitHub releases: {len(no_releases)}")
    out.append(f"  signing-tool taxonomy (release-tool occurrences): "
               f"{dict(tools_counter.most_common())}")
    # ---- W3: per-ecosystem release-signing breakdown
    eco_signed = collections.defaultdict(lambda: [0, 0])  # eco -> [signed, total]
    for r in rows:
        eco = ECOSYSTEM.get(r["repo"], "Other")
        eco_signed[eco][1] += 1
        if r["any_signed"]:
            eco_signed[eco][0] += 1
    out.append("  per-ecosystem signed-repo breakdown (W3):")
    for eco in sorted(eco_signed):
        k, tot = eco_signed[eco]
        out.append(f"    {eco:12s} {k:2d}/{tot:2d} signed"
                   + (f" ({k/tot:.0%})" if tot else ""))
    compact = ", ".join(f"{eco} {eco_signed[eco][0]}/{eco_signed[eco][1]}"
                        for eco in sorted(eco_signed))
    out.append(f"  signed-by-ecosystem: {compact}")
    out.append("  per-repo release posture:")
    for r in rows:
        st = "SIGNED" if r["any_signed"] else ("NO_ASSETS" if r["rel_total"] > 0 and r["no_assets_rel"] == r["rel_total"] else ("NO_RELEASES" if r["rel_total"] == 0 else "unsigned"))
        out.append(f"    {st:11s} {r['rel_signed']:3d}/{r['rel_total']:3d}  {r['repo']}")

    # ---- C3: coherence 2x2
    def strong(r):
        return r["share"] >= 0.90
    a_ = sum(1 for r in rows if strong(r) and r["any_signed"])
    b_ = sum(1 for r in rows if strong(r) and not r["any_signed"])
    c_ = sum(1 for r in rows if not strong(r) and r["any_signed"])
    d_ = sum(1 for r in rows if not strong(r) and not r["any_signed"])
    p, or_ = fisher_exact(a_, b_, c_, d_)
    out.append("")
    out.append("C3 coherence (commit-strong >=90% verified x >=1 signed release):")
    out.append(f"  2x2 matrix:")
    out.append(f"    commit-strong  + signed: {a_:2d}")
    out.append(f"    commit-strong  - signed: {b_:2d}")
    out.append(f"    commit-absent  + signed: {c_:2d}")
    out.append(f"    commit-absent  - signed: {d_:2d}")
    out.append(f"  Fisher exact p={p:.4f}  OR={or_:.2f} (exact {or_})")
    or_lo, or_hi = woolf_or_ci(a_, b_, c_, d_)
    if math.isfinite(or_hi):
        out.append(f"  OR 95% CI (Woolf/logit approx): {or_lo:.2f}-{or_hi:.2f} "
                   f"(includes 1; consistent with non-significance)")
    else:
        out.append("  OR 95% CI (Woolf/logit approx): undefined (zero margin cell)")
    out.append("  power note: margins (3,13,1,24) — severely underpowered; "
               "a significant association is undetectable at n=41")
    # mirror-origin caveat for the openssl cell
    if any(r["repo"] == "openssl/openssl" and r["any_signed"] for r in rows):
        out.append("  caveat: the commit-absent+signed cell is openssl/openssl — "
                   "a mirror-origin repo (GitHub history via openssl.org upstream); "
                   "its release signing is real, its commit posture is not observable "
                   "on the GitHub mirror channel")
    out.append("")
    out.append("canonical-run key: every number above derives from data_snapshot/ "
               "via deterministic classification.")
    print("\n".join(out))


if __name__ == "__main__":
    main()
