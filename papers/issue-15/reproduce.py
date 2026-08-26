"""
reproduce.py — CANONICAL runner for issue #15 "Conventional Commits in the Wild".

One command reproduces every number in the manuscript:

    python3 reproduce.py            # online: fetch via gh api, analyze, print
    python3 reproduce.py --offline  # read from committed data_snapshot/

Deterministic: classification is a pure function of the fetched data; the
fetched commit/release data is snapshotted (data_snapshot/) so --offline
reproduces byte-identical output without network.

Claims reproduced here:
  C1: pooled + per-repo CC full-compliance fraction (95% t-CI, repos as
      sampling units); tier decomposition (full / partial / non).
  C2: compliance by tooling presence — group means, Welch t-test, odds ratio.
  C3: correlation between compliance and release-cadence regularity
      (Spearman rho of full% vs CV of inter-release intervals).

Data sources (GitHub REST API via gh auth):
  - commits:  repos/{repo}/commits?per_page=100  (last ~300 per repo)
  - releases: repos/{repo}/releases?per_page=100  (all)
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import time
from collections import Counter

# --------------------------------------------------------------------------
# Corpus manifest: (repo, tooling, ecosystem)
# Tooling group assigned by deterministic multi-signal detection (see
# detect_tooling.py / README): root config | package.json deps | topic.
# --------------------------------------------------------------------------
CORPUS = [
    # --- tooling-present (8) ---
    ("commitizen/cz-cli",                       True,  "js"),
    ("semantic-release/semantic-release",       True,  "js"),
    ("conventional-changelog/conventional-changelog", True, "js"),
    ("googleapis/release-please",               True,  "js"),
    ("googleapis/google-cloud-python",          True,  "py"),
    ("google/zx",                               True,  "js"),
    ("conventional-changelog/commitlint",       True,  "js"),
    ("nestjs/nest",                             True,  "js"),
    # --- tooling-absent (8) ---
    ("pallets/click",                           False, "py"),
    ("pallets/flask",                           False, "py"),
    ("fastapi/typer",                           False, "py"),
    ("tqdm/tqdm",                               False, "py"),
    ("dateutil/dateutil",                       False, "py"),
    ("jakubroztocil/httpie",                    False, "py"),
    ("psf/requests",                            False, "py"),
    ("numpy/numpy",                             False, "py"),
]
MAX_COMMITS = 300
SNAPSHOT_DIR = "data_snapshot"

CANONICAL_TYPES = {"feat", "fix", "docs", "style", "refactor", "perf", "test",
                   "build", "ci", "chore", "revert"}
RE_FULL = re.compile(
    r"^(?P<type>" + "|".join(sorted(CANONICAL_TYPES)) +
    r")(\((?P<scope>[^()]*)\))?(?P<bang>!)?:\s(?P<desc>\S.*)$")
RE_PREFIX = re.compile(r"^(?P<word>[A-Za-z][A-Za-z0-9_-]*)(\([^()]*\))?!?:(\s|$)")


def tier(subject: str) -> str:
    subject = subject.split("\n", 1)[0].strip()
    if not subject:
        return "non"
    if RE_FULL.match(subject):
        return "full"
    if RE_PREFIX.match(subject):
        return "partial"
    return "non"


def breaking(message: str) -> bool:
    first = message.split("\n", 1)[0]
    if re.search(r"!:", first):
        return True
    for line in message.split("\n")[1:]:
        s = line.strip()
        if s.startswith("BREAKING CHANGE:") or s.startswith("BREAKING-CHANGE:"):
            return True
    return False


# ---------------- data acquisition (gh api) ----------------

def gh_json(url, tries=3):
    for i in range(tries):
        out = subprocess.run(["gh", "api", url], capture_output=True, text=True)
        if out.returncode == 0:
            try:
                return json.loads(out.stdout)
            except Exception:
                return None
        time.sleep(2 * (i + 1))
    return None


def fetch_commits(repo):
    """Last ~MAX_COMMITS commit messages (newest first)."""
    msgs = []
    page = 1
    while len(msgs) < MAX_COMMITS:
        batch = gh_json(f"repos/{repo}/commits?per_page=100&page={page}")
        if not batch:
            break
        for c in batch:
            m = (c.get("commit") or {}).get("message", "")
            if m.strip():
                msgs.append(m)
        if len(batch) < 100:
            break
        page += 1
    return msgs[:MAX_COMMITS]


def fetch_releases(repo):
    """All release dates (ISO)."""
    dates = []
    page = 1
    while True:
        batch = gh_json(f"repos/{repo}/releases?per_page=100&page={page}")
        if not batch:
            break
        for r in batch:
            if r.get("published_at"):
                dates.append(r["published_at"])
        if len(batch) < 100:
            break
        page += 1
    return dates


# ---------------- stats ----------------

def pct(p, w):
    return 100.0 * p / w if w else 0.0


def t_ci(values):
    """95% two-sided t-CI: mean ± t*sd/sqrt(n)."""
    n = len(values)
    if n == 0:
        return float("nan"), float("nan"), 0
    if n == 1:
        return values[0], float("nan"), 1
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    sd = math.sqrt(var)
    t_table = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571,
               7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 11: 2.228,
               12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120}
    t = t_table.get(n, 2.0)
    return mean, t * sd / math.sqrt(n), n


def welch_t(a, b):
    """Welch's t-test (unequal variances): (t, df, p two-tailed approx)."""
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan"), float("nan")
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    se = math.sqrt(va / len(a) + vb / len(b))
    if se == 0:
        return float("nan"), float("nan"), float("nan")
    t = (ma - mb) / se
    df = (va / len(a) + vb / len(b)) ** 2 / (
        (va / len(a)) ** 2 / (len(a) - 1) + (vb / len(b)) ** 2 / (len(b) - 1))
    # two-tailed p via normal approx (large df)
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
    return t, df, p


def spearman(xs, ys):
    """Spearman rho (rank correlation)."""
    def rank(v):
        idx = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[idx[j + 1]] == v[idx[i]]:
                j += 1
            rv = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[idx[k]] = rv
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    den = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)) *
                    sum((ry[i] - my) ** 2 for i in range(n)))
    return num / den if den else float("nan")


def release_cv(dates_iso):
    """Coefficient of variation of inter-release intervals (days)."""
    from datetime import datetime
    ds = sorted(datetime.fromisoformat(d.replace("Z", "+00:00")) for d in dates_iso)
    if len(ds) < 4:  # need >=3 intervals
        return None
    intervals = [(ds[i + 1] - ds[i]).days for i in range(len(ds) - 1)]
    intervals = [d for d in intervals if d > 0]
    if len(intervals) < 3:
        return None
    mean = sum(intervals) / len(intervals)
    if mean == 0:
        return None
    var = sum((x - mean) ** 2 for x in intervals) / len(intervals)
    return math.sqrt(var) / mean


# ---------------- main ----------------

def main():
    offline = "--offline" in sys.argv

    rows = []
    for repo, tooling, eco in CORPUS:
        tag = "T" if tooling else "N"
        if offline:
            with open(os.path.join(SNAPSHOT_DIR, repo.replace("/", "__") + ".json")) as f:
                snap = json.load(f)
            msgs, dates = snap["messages"], snap["release_dates"]
        else:
            print(f"[fetch] {repo} ({tag})...", file=sys.stderr)
            msgs = fetch_commits(repo)
            dates = fetch_releases(repo)
            os.makedirs(SNAPSHOT_DIR, exist_ok=True)
            with open(os.path.join(SNAPSHOT_DIR, repo.replace("/", "__") + ".json"), "w") as f:
                json.dump({"repo": repo, "messages": msgs, "release_dates": dates}, f)
        counts = Counter(tier(m) for m in msgs)
        n = len(msgs)
        full = counts["full"]
        breaking_n = sum(1 for m in msgs if breaking(m))
        cv = release_cv(dates)
        row = {"repo": repo, "tooling": tooling, "eco": eco, "n": n,
               "full": full, "full_pct": pct(full, n),
               "partial": counts["partial"], "non": counts["non"],
               "breaking": breaking_n, "n_releases": len(dates), "cv": cv}
        rows.append(row)

    # ---------------- output ----------------
    print("=== per-repo ===")
    print(f"{'repo':<40} {'grp':<2} {'n':>4} {'full%':>6} {'full':>4} "
          f"{'partial':>8} {'non':>5} {'brk':>4} {'rel':>4} {'CV':>6}")
    for r in rows:
        cv_s = f"{r['cv']:.3f}" if r['cv'] is not None else "-"
        print(f"{r['repo']:<40} {('T' if r['tooling'] else 'N'):<2} {r['n']:>4} "
              f"{r['full_pct']:>6.1f} {r['full']:>4} {r['partial']:>8} "
              f"{r['non']:>5} {r['breaking']:>4} {r['n_releases']:>4} "
              f"{cv_s:>6}")

    # C1 pooled + CI
    tot_commits = sum(r["n"] for r in rows)
    tot_full = sum(r["full"] for r in rows)
    per_repo_pcts = [r["full_pct"] for r in rows]
    m, hw, n = t_ci(per_repo_pcts)
    print("\n=== C1: compliance ===")
    print(f"pooled full: {tot_full}/{tot_commits} = {pct(tot_full, tot_commits):.1f}%")
    print(f"per-repo full% mean: {m:.1f}% ± {hw:.1f}% (95% t-CI, n={n})")
    print(f"repos: {len(rows)}")

    # C2 group comparison
    grp_t = [r["full_pct"] for r in rows if r["tooling"]]
    grp_n = [r["full_pct"] for r in rows if not r["tooling"]]
    mt, hwt, nt = t_ci(grp_t)
    mn, hwn, nn = t_ci(grp_n)
    tval, df, p = welch_t(grp_t, grp_n)
    full_t = sum(r["full"] for r in rows if r["tooling"])
    n_t = sum(r["n"] for r in rows if r["tooling"])
    full_n = sum(r["full"] for r in rows if not r["tooling"])
    n_n = sum(r["n"] for r in rows if not r["tooling"])
    odds = (full_t * (n_n - full_n)) / ((n_t - full_t) * full_n) if full_n and (n_t - full_t) else float("nan")
    print("\n=== C2: tooling vs no-tooling ===")
    print(f"tooling     : n_repos={nt} mean full% {mt:.1f} ± {hwt:.1f} | pooled {full_t}/{n_t} = {pct(full_t, n_t):.1f}%")
    print(f"no-tooling  : n_repos={nn} mean full% {mn:.1f} ± {hwn:.1f} | pooled {full_n}/{n_n} = {pct(full_n, n_n):.1f}%")
    print(f"Welch t={tval:.2f} df={df:.1f} p={p:.4f}")
    print(f"pooled odds ratio (tooling vs no-tooling) = {odds:.2f}")

    # C3 release cadence
    pairs = [(r["full_pct"], r["cv"]) for r in rows if r["cv"] is not None]
    if len(pairs) >= 4:
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        rho = spearman(xs, ys)
        print("\n=== C3: compliance vs release-cadence regularity ===")
        print(f"Spearman rho(full%, CV) = {rho:.3f} (n={len(pairs)} repos with >=4 releases)")
        for r in rows:
            if r["cv"] is not None:
                print(f"  {r['repo']:<40} full%={r['full_pct']:>6.1f}  CV={r['cv']:.3f}")
    else:
        print("\n=== C3: insufficient repos with >=4 releases ===")

    # tier decomposition pooled
    print("\n=== tier decomposition (pooled) ===")
    tf = sum(r["full"] for r in rows)
    tp = sum(r["partial"] for r in rows)
    tn = sum(r["non"] for r in rows)
    tt = tf + tp + tn
    print(f"full {tf} ({pct(tf, tt):.1f}%) | partial {tp} ({pct(tp, tt):.1f}%) | non {tn} ({pct(tn, tt):.1f}%)")


if __name__ == "__main__":
    main()
