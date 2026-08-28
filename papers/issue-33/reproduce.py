#!/usr/bin/env python3
"""reproduce.py — issue #33: Do Trust Signals Predict Supply-Chain Health?

Modes:
  fetch [repo...] : fetch GitHub signals for corpus repos -> data_snapshot/<repo>.json
                    (requires `gh` authenticated; writes manifest.json with timestamps)
  offline         : aggregate data_snapshot/ -> expected_output/discovery_results.txt
                    (byte-identical, fully offline, stdlib only)
  summary         : print per-repo signals table from data_snapshot/

Signals (cheap trust signals, GitHub REST):
  stars, forks, open_issues, subscribers, license, pushed_at, created_at,
  contributors (count via Link header), releases (count via Link header),
  ci_presence (.github/workflows exists), manifest (ecosystem membership evidence)
Outcomes (to be added R46): OSV vuln records, OpenSSF Scorecard total.
"""
import json, os, re, subprocess, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "data_snapshot"
OUT = ROOT / "expected_output"
CORPUS = ROOT / "corpus.json"

MANIFESTS = {
    "Python": ["pyproject.toml", "setup.py", "setup.cfg"],
    "JavaScript": ["package.json"],
    "Java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "Go": ["go.mod"],
    "Rust": ["Cargo.toml"],
}

def corpus_repos():
    d = json.load(open(CORPUS))
    return d["repos"], d.get("_meta", {})

def gh_api(path, params=None):
    url = f"repos/{path}" if not path.startswith("search") else path
    cmd = ["gh", "api", url]
    if params:
        cmd += ["-f", params]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None, None
    return json.loads(r.stdout), r.stdout

def count_via_link(path, per_page=1):
    """Count paginated collection items via Link header (last page number)."""
    r = subprocess.run(["gh", "api", "-i", f"{path}?per_page={per_page}"],
                       capture_output=True, text=True)
    parts = re.split(r"\r?\n\r?\n", r.stdout or "", maxsplit=1)
    hdr = parts[0]
    body = parts[1] if len(parts) > 1 else ""
    m = re.search(r"<([^>]+)>;\s*rel=\"last\"", hdr)
    if m:
        pm = re.search(r"[?&]page=(\d+)", m.group(1))
        if pm:
            return int(pm.group(1)) * per_page
    try:
        return len(json.loads(body))
    except Exception:
        return 0

def fetch_outcomes(repo, ecosystem):
    """Independent health outcomes: OpenSSF Scorecard (exact repo mapping) + OSV
    vulnerability records (package-name approximation, documented in threats)."""
    owner, name = repo.split("/", 1)
    out = {"scorecard": None, "scorecard_subscores": None, "osv": None,
           "osv_count": None, "osv_max_severity": None}
    # OpenSSF Scorecard public API (exact repo identity — primary outcome)
    try:
        import urllib.request
        req = urllib.request.Request(
            f"https://api.securityscorecards.dev/projects/github.com/{owner}/{name}",
            headers={"User-Agent": "silicon-science-cs/issue33"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            sc = json.load(resp)
        out["scorecard"] = sc.get("score")
        out["scorecard_subscores"] = {cs.get("name"): cs.get("score")
                                      for cs in sc.get("checks", [])}
    except Exception:
        pass
    # OSV (secondary; package name = repo name approximation)
    try:
        import urllib.request
        body = json.dumps({"package": {"ecosystem": OSV_ECOSYSTEMS.get(ecosystem, ecosystem),
                                       "name": name}}).encode()
        req = urllib.request.Request("https://api.osv.dev/v1/query", data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "silicon-science-cs/issue33"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            osv = json.load(resp)
        vulns = osv.get("vulns", [])
        out["osv_count"] = len(vulns)
        sev = []
        for v in vulns:
            for d in v.get("severity", []):
                sev.append(d.get("score"))
        out["osv_max_severity"] = max(sev) if sev else None
    except Exception:
        pass
    return out

OSV_ECOSYSTEMS = {"Python": "PyPI", "JavaScript": "npm", "Java": "Maven",
                  "Go": "Go", "Rust": "crates.io"}

def fetch_repo(repo):
    owner, name = repo.split("/", 1)
    data, _ = gh_api(f"{owner}/{name}")
    if data is None:
        return None
    sig = {
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "open_issues": data.get("open_issues_count"),
        "subscribers": data.get("subscribers_count"),
        "license": (data.get("license") or {}).get("spdx_id"),
        "pushed_at": data.get("pushed_at"),
        "created_at": data.get("created_at"),
        "language": data.get("language"),
        "size_kb": data.get("size"),
    }
    sig["contributors"] = count_via_link(f"repos/{owner}/{name}/contributors")
    sig["releases"] = count_via_link(f"repos/{owner}/{name}/releases")
    # CI presence + manifest evidence
    ci = False
    r = subprocess.run(["gh", "api", f"repos/{owner}/{name}/contents/.github/workflows"],
                       capture_output=True, text=True)
    ci = r.returncode == 0
    sig["ci_presence"] = ci
    r = subprocess.run(["gh", "api", f"repos/{owner}/{name}/contents/"],
                       capture_output=True, text=True)
    top = json.loads(r.stdout) if r.returncode == 0 else []
    names = {f["name"] for f in top}
    # ecosystem evidence: repo language vs corpus-assigned ecosystem
    sig["language"] = data.get("language")
    return {"repo": repo, "signals": sig, "manifest_present": sorted(names),
            "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "offline"
    repos, meta = corpus_repos()
    if mode == "fetch":
        want = set(sys.argv[2:]) or {r["repo"] for r in repos}
        SNAP.mkdir(exist_ok=True)
        manifest = {"fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "repos": []}
        for r in repos:
            if r["repo"] not in want:
                continue
            snap = fetch_repo(r["repo"])
            if snap:
                snap["outcomes"] = fetch_outcomes(r["repo"], r.get("ecosystem", ""))
                (SNAP / (r["repo"].replace("/", "__") + ".json")).write_text(json.dumps(snap, indent=1))
                manifest["repos"].append(r["repo"])
                print(f"fetched {r['repo']}: stars={snap['signals']['stars']} "
                      f"contribs={snap['signals']['contributors']} "
                      f"releases={snap['signals']['releases']} "
                      f"ci={snap['signals']['ci_presence']} "
                      f"scorecard={snap['outcomes']['scorecard']} "
                      f"osv={snap['outcomes']['osv_count']}", flush=True)
        (SNAP / "manifest.json").write_text(json.dumps(manifest, indent=1))
    elif mode == "summary":
        for f in sorted(SNAP.glob("*.json")):
            if f.name == "manifest.json":
                continue
            s = json.load(open(f))
            sig = s["signals"]
            print(f"{s['repo']:45s} stars={sig['stars']:>7d} forks={sig['forks']:>6d} "
                  f"open={sig['open_issues']:>5d} contribs={sig['contributors']:>5d} "
                  f"releases={sig['releases']:>4d} ci={sig['ci_presence']}")
    elif mode == "offline":
        snaps = []
        for f in sorted(SNAP.glob("*.json")):
            if f.name == "manifest.json":
                continue
            s = json.load(open(f))
            s["_eco"] = next((c.get("ecosystem") for c in repos
                              if c["repo"] == s["repo"]), "")
            snaps.append(s)
        out = []
        out.append("TRUST SIGNAL SNAPSHOT — issue #33 (canonical, offline)")
        out.append(f"corpus: {len(snaps)}/{len(repos)} repos fetched | "
                   f"meta: {meta.get('selection_rule','')[:70]}...")
        out.append("")
        out.append(f"{'repo':45s} {'eco':>10s} {'stars':>8s} {'contrib':>6s} {'rels':>4s} "
                   f"{'ci':>2s} {'score':>5s} {'osv':>3s}")
        for s in snaps:
            sig = s["signals"]; oc = s.get("outcomes", {})
            sc = oc.get("scorecard")
            sc_s = f"{sc:.1f}" if sc is not None else "n/a"
            osv = oc.get("osv_count")
            osv_s = f"{osv}" if osv is not None else "n/a"
            out.append(f"{s['repo']:45s} {s['_eco']:>10s} {sig['stars']:8d} "
                       f"{sig['contributors']:6d} {sig['releases']:4d} "
                       f"{1 if sig['ci_presence'] else 0:2d} {sc_s:>5s} {osv_s:>3s}")
        out.append("")
        # ---- signal→outcome association (H1/H2) ----
        def rank_avg(vals):
            """Standard average-rank (ties share the mean rank)."""
            s = sorted(vals)
            ranks = {}
            i, n = 0, len(s)
            while i < n:
                j = i
                while j + 1 < n and s[j + 1] == s[i]:
                    j += 1
                avg = (i + 1 + j + 1) / 2.0
                for k in range(i, j + 1):
                    ranks[s[k]] = avg
                i = j + 1
            return [ranks[v] for v in vals]

        def spearman(xs, ys):
            """Spearman rho with standard average ranks (review #33-1)."""
            n = len(xs)
            if n < 3:
                return None
            sx = rank_avg(xs); sy = rank_avg(ys)
            mx = sum(sx) / n; my = sum(sy) / n
            cov = sum((a - mx) * (b - my) for a, b in zip(sx, sy))
            vx = sum((a - mx) ** 2 for a in sx); vy = sum((b - my) ** 2 for b in sy)
            if vx == 0 or vy == 0:
                return None
            return cov / (vx * vy) ** 0.5

        def fisher_z_ci(rho, n, z=1.96):
            """Fisher-z 95% CI for Spearman rho (review #33-2)."""
            import math
            if rho is None or n < 4 or abs(rho) >= 1.0:
                return None
            zr = math.atanh(rho)
            se = 1.0 / math.sqrt(n - 3)
            return (math.tanh(zr - z * se), math.tanh(zr + z * se))

        pairs = [(s, s.get("outcomes", {})) for s in snaps]
        # 10 signals: 6 original + 4 added per review #33-3 (ci binary,
        # has_license binary, repo_age_days, days_since_push — derived from
        # snapshot-pinned timestamps, deterministic).
        fetch_ts = datetime.datetime.fromisoformat(
            json.load(open(SNAP / "manifest.json")).get("fetched_at",
            "2026-08-28T00:00:00+00:00"))
        for s in snaps:
            sig = s["signals"]
            sig["ci"] = 1 if sig.get("ci_presence") else 0
            sig["has_license"] = 1 if sig.get("license") else 0
            def _days(ts):
                if not ts:
                    return None
                try:
                    d = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    return max(0, (fetch_ts - d).days)
                except Exception:
                    return None
            sig["repo_age_days"] = _days(sig.get("created_at"))
            sig["days_since_push"] = _days(sig.get("pushed_at"))
        sig_keys = ["stars", "contributors", "forks", "open_issues", "releases",
                    "subscribers", "ci", "has_license", "repo_age_days",
                    "days_since_push"]
        for out_key, label in [("scorecard", "Scorecard"), ("osv_count", "OSV vulns")]:
            ys = [oc.get(out_key) for _, oc in pairs]
            if all(y is None for y in ys):
                continue
            out.append(f"Spearman rho (avg-rank, Fisher-z 95% CI) — signal vs {label}:")
            for k in sig_keys:
                idx = [i for i, (s, oc) in enumerate(pairs)
                       if oc.get(out_key) is not None and s["signals"].get(k) is not None]
                if len(idx) < 3:
                    out.append(f"  {k:16s} n<3")
                    continue
                xs = [pairs[i][0]["signals"][k] for i in idx]
                ys2 = [pairs[i][1][out_key] for i in idx]
                rho = spearman(xs, ys2)
                if rho is None:
                    out.append(f"  {k:16s} n/a")
                    continue
                ci = fisher_z_ci(rho, len(idx))
                if ci:
                    out.append(f"  {k:16s} rho={rho:+.3f} "
                               f"[{ci[0]:+.3f}, {ci[1]:+.3f}]  n={len(idx)}")
                else:
                    out.append(f"  {k:16s} rho={rho:+.3f}  n={len(idx)}")
            out.append("")
        # ---- ecosystem stratification (H2 context) ----
        out.append("per-ecosystem median scorecard / osv:")
        for eco in sorted({s["_eco"] for s in snaps}):
            ss = [s.get("outcomes", {}).get("scorecard") for s in snaps if s["_eco"] == eco]
            ss = [x for x in ss if x is not None]
            oo = [s.get("outcomes", {}).get("osv_count") for s in snaps if s["_eco"] == eco]
            oo = [x for x in oo if x is not None]
            med_sc = sorted(ss)[len(ss) // 2] if ss else None
            med_osv = sorted(oo)[len(oo) // 2] if oo else None
            out.append(f"  {eco:10s} n={len(ss):2d} median_scorecard={med_sc} "
                       f"median_osv={med_osv}")
        out.append("")
        # ---- H3 gameability: stars/contributor ratio outliers ----
        ratios = [(s, s["signals"]["stars"] / max(1, s["signals"]["contributors"]))
                  for s in snaps if s["signals"].get("contributors")]
        if len(ratios) >= 5:
            rs = sorted(r for _, r in ratios)
            med = rs[len(rs) // 2]
            mad = sorted(abs(r - med) for _, r in ratios)[len(rs) // 2]
            n_out = sum(1 for _, r in ratios if r > med + 5 * mad)
            out.append(f"H3 spike detection (stars/contributor ratio): "
                       f"median={med:.0f} MAD={mad:.0f}")
            out.append(f"H3 outlier fraction: {n_out}/{len(ratios)} "
                       f"({n_out/len(ratios):.1%}) above median+5xMAD")
            # threshold sensitivity (review #33-5): 5xMAD is the conservative
            # primary cutoff; 2.5x/3x shown for robustness.
            for mult in (2.5, 3.0, 5.0):
                k = sum(1 for _, r in ratios if r > med + mult * mad)
                out.append(f"  median+{mult:g}xMAD flags {k}/{len(ratios)} "
                           f"({k/len(ratios):.1%})")
            for s, r in sorted(ratios, key=lambda x: -x[1]):
                flag = " <<< outlier" if r > med + 5 * mad else ""
                out.append(f"  {s['repo']:45s} ratio={r:7.0f}{flag}")
        out.append("")
        # ---- derived coverage + H1-vs-H2 gap (traceability block) ----
        sc_n = sum(1 for s in snaps if s.get("outcomes", {}).get("scorecard") is not None)
        osv_n = sum(1 for s in snaps if s.get("outcomes", {}).get("osv_count") is not None)
        out.append(f"outcome coverage: scorecard {sc_n}/{len(snaps)} "
                   f"({sc_n/len(snaps):.0%}), osv {osv_n}/{len(snaps)} "
                   f"({osv_n/len(snaps):.0%})")
        # H1-vs-H2 gap: releases rho minus stars rho vs Scorecard (n=32)
        def rho_pair(key1, key2, out_key="scorecard"):
            idx = [i for i, (s, oc) in enumerate(pairs)
                   if oc.get(out_key) is not None
                   and s["signals"].get(key1) is not None
                   and s["signals"].get(key2) is not None]
            if len(idx) < 3:
                return None
            xs = [pairs[i][0]["signals"][key1] for i in idx]
            ys = [pairs[i][0]["signals"][key2] for i in idx]
            zs = [pairs[i][1][out_key] for i in idx]
            return spearman(xs, zs) - spearman(ys, zs)
        gap = rho_pair("releases", "stars")
        if gap is not None:
            out.append(f"signal gap (releases - stars vs Scorecard): {gap:+.3f}")
        out.append("")
        out.append("canonical-run key: every number derives from data_snapshot/ via deterministic fetch.")
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "discovery_results.txt").write_text("\n".join(out) + "\n")
        print("\n".join(out))
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
