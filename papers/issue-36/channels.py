#!/usr/bin/env python3
"""Issue #36 — full channel measurement (C1a/C1b + C2 + C3) for SWE-bench_Verified.

Channels (pre-registered, refined post-pilot):
  C1a  issue public availability        — issue exists, created_at (training exposure vector)
  C1b  issue-text verbatim recoverable  — token Jaccard(body, problem_statement) >= 0.8
  C2   test-first leakage               — test_patch's primary file exists in tree at base_commit
  C3   fix-issue linkage                — issue events contain a 'closed' event with commit_id
                                        (gold fix publicly linked to the issue; models could
                                        recover issue->fix via public data)

Deterministic: per-instance JSON -> data_snapshot_c236/<instance_id>.json, fetch-time pinned.
"""
import json, re, subprocess, sys, datetime
from pathlib import Path

RAW = Path(__file__).resolve().parent / "raw"
SNAP = Path(__file__).resolve().parent / "data_snapshot_c236"
JACCARD_THRESHOLD = 0.8

def tokenize(s):
    return set(re.findall(r"[a-z0-9_]+", s.lower()))

def token_jaccard(a, b):
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

def parse_instance_id(iid):
    # e.g. scikit-learn__scikit-learn-10297 (repo may contain hyphens):
    # org part is up to the first '__', the rest before the final -<digits> is repo.
    if "__" not in iid:
        return None, None, None
    org, rest = iid.split("__", 1)
    m = re.match(r"(.+)-(\d+)$", rest)
    if not m:
        return None, None, None
    return f"{org}/{m.group(1)}", m.group(1), int(m.group(2))

def gh(path, ref=None):
    cmd = ["gh", "api", path]
    if ref:
        cmd += ["-H", f"Accept: application/vnd.github.raw+json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return r.stdout

def first_test_file(test_patch):
    """First file path touched by test_patch (prefixed a/ or b/)."""
    m = re.search(r"^\+\+\+ b/(\S+)", test_patch, re.M)
    return m.group(1) if m else None

def main():
    offset = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    SNAP.mkdir(exist_ok=True)
    lines = RAW.joinpath("swe_bench_verified.jsonl").read_text().splitlines()
    rows = [json.loads(l) for l in lines][offset:offset + limit]
    for row in rows:
        iid = row["instance_id"]
        repo, rname, issue = parse_instance_id(iid)
        if repo is None:
            print(f"{iid}: UNPARSEABLE", flush=True)
            continue
        rec = {"instance_id": iid, "repo": repo, "issue": issue,
               "base_commit": row.get("base_commit")}
        # C1a + C1b
        iss = gh(f"repos/{repo}/issues/{issue}")
        if iss is None:
            print(f"{iid}: issue fetch FAIL", flush=True)
            continue
        body = (iss.get("body") or "") + "\n" + (iss.get("title") or "")
        rec["c1a_issue_available"] = True
        rec["c1a_issue_created_at"] = iss.get("created_at")
        rec["c1b_jaccard"] = round(token_jaccard(body, row["problem_statement"]), 4)
        rec["c1b_hit"] = rec["c1b_jaccard"] >= JACCARD_THRESHOLD
        # C3: fix-issue linkage via commit search (issue number in commit message:
        # any model trained on public git data can discover issue->fix).
        cs = gh(f"search/commits?q=repo:{repo}+{issue}&sort=committer-date&order=asc")
        fix_commits = []
        if isinstance(cs, dict) and cs.get("items"):
            for it in cs["items"][:3]:
                fix_commits.append({
                    "sha": it["sha"][:10],
                    "date": (it.get("commit", {}).get("committer", {}).get("date") or "")[:10],
                    "msg": (it.get("commit", {}).get("message") or "")[:60],
                })
        rec["c3_fix_commits"] = fix_commits
        rec["c3_hit"] = len(fix_commits) > 0
        # C2: test file present at base_commit
        tfile = first_test_file(row.get("test_patch") or "")
        rec["c2_test_file"] = tfile
        if tfile:
            c2 = gh(f"repos/{repo}/contents/{tfile}?ref={rec['base_commit']}")
            rec["c2_present_at_base"] = c2 is not None
        else:
            rec["c2_present_at_base"] = None
        rec["fetched_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (SNAP / f"{iid}.json").write_text(json.dumps(rec, indent=1))
        print(f"{iid}: c1a={rec['c1a_issue_created_at'][:10]} "
              f"c1b={rec['c1b_jaccard']:.3f} c2={rec['c2_present_at_base']} "
              f"c3={'Y' if rec['c3_hit'] else 'N'}", flush=True)

if __name__ == "__main__":
    main()
