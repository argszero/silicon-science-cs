#!/usr/bin/env python3
"""Issue #25 C3 content classifier — rollback support + destructive ops.

Reads data_snapshot/ discovery snapshots, samples migration files per repo
(min(25, n), evenly spaced), fetches their content via the contents API,
and classifies:
  C3a. rollback support: does the migration file (or its pair) provide a
       reverse mechanism?
       - .down.sql sibling file (mattermost, Diesel-style up/down pairs)
       - def down / function down / down() (Rails, Laravel)
       - def reverse / RunPython(forward, reverse) (Django)
       - exports.down (Knex/Bookshelf)
       - <rollback ...> XML tag (Liquibase)
       - db-migrate down() (Node db-migrate)
  C3b. destructive operations: DROP TABLE/COLUMN/INDEX/... or TRUNCATE in the
       migration body.

Modes:
  reproduce.py content        — fetch sampled file contents into snapshots
  reproduce.py                — offline: classify from committed content

Deterministic: classification is a pure function of committed snapshot JSON.
"""
import argparse, base64, collections, json, os, re, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(BASE, "data_snapshot")
SAMPLE_CAP = 25

ROLLBACK_PATTERNS = [
    ("down-method", re.compile(r"^\s*(?:public\s+)?function\s+down\b|def\s+down\b|"
                               r"^\s*down\s*[:=]\s*\(|exports\.down\b", re.M)),
    ("reverse-method", re.compile(r"def\s+reverse\b|RunPython\([^)]*,\s*[a-z_]+\)",
                                  re.I | re.M)),
    ("liquibase-rollback", re.compile(r"<rollback\b", re.I)),
    ("downgrade-method", re.compile(r"def\s+downgrade\b", re.M)),
    ("undo-method", re.compile(r"function\s+undo\b|def\s+undo\b", re.M)),
]

DESTRUCTIVE_PATTERNS = [
    ("drop-table", re.compile(r"\bdrop\s+table\b", re.I)),
    ("drop-column", re.compile(r"\bdrop\s+column\b", re.I)),
    ("drop-index", re.compile(r"\bdrop\s+index\b", re.I)),
    ("drop-other", re.compile(r"\bdrop\s+(?:view|schema|database|constraint|trigger|"
                              r"function|procedure|type|sequence)\b", re.I)),
    ("truncate", re.compile(r"\btruncate\s+table\b", re.I)),
]


def gh_json(url):
    out = subprocess.run(["gh", "api", url], capture_output=True, text=True,
                         timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"gh api {url}: {out.stderr.strip()[:120]}")
    return json.loads(out.stdout)


def fetch_file(repo, path):
    data = gh_json(f"repos/{repo}/contents/{path}")
    if isinstance(data, list):
        return None
    content = base64.b64decode(data.get("content", "")).decode("utf-8",
                                                               errors="replace")
    return content


def has_down_sibling(path, files):
    """Diesel/mattermost-style up/down pairs.
    - mattermost: 000001_create_teams.up.sql -> .down.sql sibling
    - Diesel:     migrations/<ts>/up.sql    -> down.sql in same dir
    """
    if path.endswith(".up.sql"):
        return path[:-len(".up.sql")] + ".down.sql" in files
    if path.endswith(".down.sql"):
        return path[:-len(".down.sql")] + ".up.sql" in files
    base = path.rsplit("/", 1)[-1]
    if base == "up.sql":
        return path.rsplit("/", 1)[0] + "/down.sql" in files
    if base == "down.sql":
        return path.rsplit("/", 1)[0] + "/up.sql" in files
    return False


def fetch_content():
    snaps = []
    for fn in sorted(os.listdir(SNAP_DIR)):
        if not fn.endswith(".json") or fn == "manifest.json":
            continue
        with open(os.path.join(SNAP_DIR, fn)) as f:
            snaps.append(json.load(f))
    for s in snaps:
        repo = s["repo"]
        files = s.get("migration_files", [])
        if not files:
            s["sampled"] = []
            continue
        step = max(1, len(files) // SAMPLE_CAP)
        sample = sorted(files)[::step][:SAMPLE_CAP]
        s["sampled"] = []
        for p in sample:
            try:
                content = fetch_file(repo, p)
                if content is None:
                    continue
                s["sampled"].append({
                    "path": p,
                    "content": content,
                    "size": len(content.encode("utf-8")),
                })
                print(f"  {repo}: {p} ({len(content)} ch)")
            except RuntimeError as e:
                print(f"  ERR {repo} {p}: {str(e)[:60]}")
        with open(os.path.join(SNAP_DIR, fn), "w") as f:
            json.dump(s, f, indent=1, sort_keys=True)
    print("content fetch complete")


def classify_file(path, content, all_files):
    rollback = []
    destructive = []
    if has_down_sibling(path, all_files):
        rollback.append("down-sibling")
    for name, pat in ROLLBACK_PATTERNS:
        if pat.search(content or ""):
            rollback.append(name)
    for name, pat in DESTRUCTIVE_PATTERNS:
        if pat.search(content or ""):
            destructive.append(name)
    return sorted(set(rollback)), sorted(set(destructive))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="offline")
    a = ap.parse_args()
    if a.mode == "content":
        fetch_content()
        return
    snaps = []
    manifest = {}
    mp = os.path.join(SNAP_DIR, "manifest.json")
    if os.path.exists(mp):
        manifest = json.load(open(mp))
    for fn in sorted(os.listdir(SNAP_DIR)):
        if not fn.endswith(".json") or fn == "manifest.json":
            continue
        snaps.append(json.load(open(os.path.join(SNAP_DIR, fn))))

    out = []
    out.append("C3 rollback support and destructive operations in sampled "
               "migration files")
    out.append(f"snapshot date: {manifest.get('fetched_at', 'not pinned')}")
    out.append("")
    per_repo = []
    for s in snaps:
        repo = s["repo"]
        all_files = set(s.get("migration_files", []))
        sampled = s.get("sampled", [])
        if not sampled:
            per_repo.append((repo, 0, 0, 0, collections.Counter(),
                             collections.Counter(), []))
            continue
        n = len(sampled)
        rb = 0
        dest = 0
        rb_reasons = collections.Counter()
        dest_kinds = collections.Counter()
        for item in sampled:
            path = item["path"]
            content = item.get("content", "")
            rbs, dst = classify_file(path, content, all_files)
            if rbs:
                rb += 1
                rb_reasons.update(rbs)
            if dst:
                dest += 1
                dest_kinds.update(dst)
        per_repo.append((repo, n, rb, dest, rb_reasons, dest_kinds, sampled))    # header
    out.append(f"{'repo':32s} {'sampled':>7s} {'rollback':>8s} {'destr':>5s}  "
               f"rollback reasons / destructive kinds")
    for repo, n, rb, dest, rbr, dk, sampled in per_repo:
        rbs = ",".join(f"{k}:{v}" for k, v in rbr.most_common(4)) or "-"
        dks = ",".join(f"{k}:{v}" for k, v in dk.most_common(4)) or "-"
        out.append(f"{repo:32s} {n:7d} {rb:8d} {dest:5d}  {rbs} | {dks}")
    # compact per-repo rows for manuscript traceability (x/y notation)
    out.append("")
    out.append("compact per-repo (destructive x/25, rollback y/25):")
    for repo, n, rb, dest, rbr, dk, sampled in per_repo:
        if n == 0:
            continue
        out.append(f"  {repo:32s} destructive={dest}/{n} ({dest/n:.0%}) "
                   f"rollback={rb}/{n} ({rb/n:.0%})")
    # aggregates
    total_sampled = sum(x[1] for x in per_repo)
    total_rb = sum(x[2] for x in per_repo)
    total_dest = sum(x[3] for x in per_repo)
    out.append("")
    out.append(f"aggregate: {total_rb}/{total_sampled} sampled files have "
               f"rollback support ({total_rb/total_sampled:.1%}); "
               f"{total_dest}/{total_sampled} contain destructive operations "
               f"({total_dest/total_sampled:.1%})")
    # all-others aggregate (repos not in the manuscript's headline table)
    TABLE9 = {"medusajs/medusa", "metabase/metabase", "LemmyNet/lemmy",
              "mattermost/mattermost", "bookstackapp/bookstack",
              "monicahq/monica", "discourse/discourse", "mastodon/mastodon",
              "zulip/zulip"}
    o_n = o_rb = o_d = 0
    for repo, n, rb, dest, rbr, dk, sampled in per_repo:
        if repo not in TABLE9:
            o_n += n; o_rb += rb; o_d += dest
    out.append(f"all-others ({len(per_repo)-len(TABLE9)} repos): "
               f"destructive={o_d}/{o_n} ({o_d/o_n:.0%}) "
               f"rollback={o_rb}/{o_n} ({o_rb/o_n:.0%})")
    out.append("")
    out.append("per-file detail (rollback=[...] destructive=[...]):")
    for repo, n, rb, dest, rbr, dk, sampled in per_repo:
        if not sampled:
            out.append(f"  {repo:32s} (no migration files sampled)")
            continue
        out.append(f"  -- {repo} --")
        for item in sampled:
            rbs, dst = classify_file(item["path"], item.get("content", ""),
                                     set(s.get("migration_files", [])))
            out.append(f"      {item['path']:70s} "
                       f"rb={'Y' if rbs else '-'} "
                       f"destr={'Y' if dst else '-'} "
                       f"{','.join(rbs)}{','.join(dst)}")
    out.append("")
    out.append("canonical-run key: every number above derives from "
               "data_snapshot/ via deterministic classification.")
    print("\n".join(out))


if __name__ == "__main__":
    main()
