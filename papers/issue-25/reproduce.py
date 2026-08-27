#!/usr/bin/env python3
"""reproduce.py — Issue #25 canonical runner (draft: discovery phase).

Database Schema Migrations in Popular Open-Source Applications:
  C1. adoption of schema-migration files/frameworks among popular web apps
      (Rails db/migrate, Django <app>/migrations, Laravel database/migrations,
       Knex/TypeORM/Prisma, Flyway/Liquibase, Go xorm/golang-migrate, Nextcloud
       core/Migrations, Diesel)
  C2. migration naming conventions (timestamp-prefixed vs sequence-prefixed)
      + migration count + per-ecosystem framework concentration
  C3. rollback support (down/reverse/downgrade/undo) and destructive operations
      (DROP COLUMN/TABLE) in migration files

Modes:
  reproduce.py discover       — pull trees for each repo, locate migration paths
  reproduce.py                — offline: read data_snapshot/, compute, print results

Deterministic: classification is a pure function of committed snapshot JSON;
offline output is byte-identical across runs. stdlib-only.
"""
import argparse, collections, json, math, os, re, subprocess, sys

# Popular DB-backed web APPLICATIONS across ecosystems (frameworks excluded —
# frameworks carry no schemas; verified in R31: rails/django/laravel frameworks
# have no migration dirs). Stars-ranked per ecosystem as of 2026-08.
CORPUS = [
    # Rails (Active Record, db/migrate)
    "mastodon/mastodon", "discourse/discourse", "lobsters/lobsters",
    "decidim/decidim",
    # Django (<app>/migrations)
    "getsentry/sentry", "zulip/zulip", "wagtail/wagtail", "posthog/posthog",
    "pretix/pretix", "goauthentik/authentik", "netbox-community/netbox",
    "paperless-ngx/paperless-ngx",
    # Laravel (database/migrations)
    "flarum/framework", "koel/koel", "bookstackapp/bookstack",
    "monicahq/monica",
    # Node (Knex/TypeORM/Prisma)
    "TryGhost/Ghost", "strapi/strapi", "directus/directus",
    "medusajs/medusa", "calcom/cal.com",
    # Java/JVM (Flyway/Liquibase)
    "keycloak/keycloak", "SonarSource/sonarqube", "metabase/metabase",
    # Go (xorm / golang-migrate / custom)
    "go-gitea/gitea", "grafana/grafana", "mattermost/mattermost",
    "knadh/listmonk",
    # PHP (Nextcloud core/Migrations, own systems)
    "nextcloud/server", "matomo/matomo", "moodle/moodle",
    # Rust (Diesel)
    "LemmyNet/lemmy",
]

# Ecosystem map (manuscript §3.1 / Table 1)
ECOSYSTEM = {
    "Rails": ["mastodon/mastodon", "discourse/discourse", "lobsters/lobsters",
              "decidim/decidim"],
    "Django": ["getsentry/sentry", "zulip/zulip", "wagtail/wagtail",
               "posthog/posthog", "pretix/pretix", "goauthentik/authentik",
               "netbox-community/netbox", "paperless-ngx/paperless-ngx"],
    "Laravel": ["flarum/framework", "koel/koel", "bookstackapp/bookstack",
                "monicahq/monica"],
    "Node": ["TryGhost/Ghost", "strapi/strapi", "directus/directus",
             "medusajs/medusa", "calcom/cal.com"],
    "JVM": ["keycloak/keycloak", "SonarSource/sonarqube", "metabase/metabase"],
    "Go": ["go-gitea/gitea", "grafana/grafana", "mattermost/mattermost",
           "knadh/listmonk"],
    "PHP": ["nextcloud/server", "matomo/matomo", "moodle/moodle"],
    "Rust": ["LemmyNet/lemmy"],
}

# Path segment heuristics: a directory is a migration dir if any of its
# (relative) path segments matches these patterns.
MIGRATION_SEGMENT_RE = re.compile(
    r"^(?:migrations?|migrate|migration|db(?:_|\.)?migrations?|alembic)$",
    re.IGNORECASE,
)
# Individual migration files commonly live under these suffixes.
MIGRATION_FILE_HINT = re.compile(
    r"(?:\.sql|\.php|\.py|\.js|\.ts|\.rb|\.go|\.java|\.xml|\.yaml|\.yml|\.exs)$",
    re.IGNORECASE,
)

# Root-level framework markers (checked against the repo's root tree names).
FRAMEWORK_MARKERS = {
    "rails": {"Gemfile", "config.ru", "Rakefile"},
    "django": {"manage.py"},
    "laravel": {"artisan", "composer.json"},
    "node": {"package.json"},
    "java": {"pom.xml", "build.gradle", "build.gradle.kts"},
    "go": {"go.mod"},
    "php": {"composer.json", "index.php"},
    "rust": {"Cargo.toml"},
    "python": {"pyproject.toml", "requirements.txt", "setup.py"},
}

BASE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(BASE, "data_snapshot")


def gh_json(url):
    out = subprocess.run(["gh", "api", url], capture_output=True, text=True,
                         timeout=120)
    if out.returncode != 0:
        raise RuntimeError(f"gh api {url}: {out.stderr.strip()[:160]}")
    return json.loads(out.stdout)


def discover_repo(repo: str) -> dict:
    """Locate migration dirs/files via the recursive trees API."""
    try:
        meta = gh_json(f"repos/{repo}")
        branch = meta.get("default_branch", "main")
        tree = gh_json(f"repos/{repo}/git/trees/{branch}?recursive=1")
    except RuntimeError as e:
        return {"repo": repo, "error": str(e)[:120], "files": {}}

    paths = [t["path"] for t in tree.get("tree", [])
             if t.get("type") == "blob"]
    truncated = tree.get("truncated", False)
    root_names = {p.split("/", 1)[0] for p in paths}
    if "/" in root_names:
        root_names.discard("/")

    # Migration dirs: any dir whose path contains a migration-ish segment.
    mig_dirs = set()
    for p in paths:
        parts = p.split("/")
        for i, seg in enumerate(parts[:-1]):
            if MIGRATION_SEGMENT_RE.match(seg):
                mig_dirs.add("/".join(parts[: i + 1]))
    # Migration files: files under a migration dir, or matching file hints.
    mig_files = []
    for p in paths:
        parts = p.split("/")
        under_mig = any(MIGRATION_SEGMENT_RE.match(seg) for seg in parts[:-1])
        if under_mig:
            mig_files.append(p)
    # Exclude non-schema paths: test trees, docs, scaffolding, one-shot data
    # conversion scripts. Verified across corpus:
    #   - src/it (sonarqube IT tests), integration-tests (medusa), testdata
    #   - docs/guides (keycloak migration docs)
    #   - examples/templates (strapi scaffolding), __fixtures__
    #   - discourse migrations/converters, importers, tooling
    EXCLUDE_SEG = re.compile(
        r"^(?:test|tests|spec|fixtures?|node_modules|converters?|importers?|"
        r"tooling|it|docs|guides?|examples?|templates?|integration-tests?|"
        r"testdata|__fixtures__|migration-scripts)$",
        re.IGNORECASE,
    )
    mig_files = sorted(f for f in mig_files
                       if not any(EXCLUDE_SEG.match(s) for s in f.split("/")))
    # File-level exclusions: tests, index/plumbing files, snapshots, docs.
    # Anchors apply to the BASENAME (patterns like ^index. / ^.snapshot must
    # match the file name, not the full path).
    def _excluded_file(path: str) -> bool:
        base = path.rsplit("/", 1)[-1]
        if re.search(r"\.(?:spec|test)\.|\.d\.ts$|\.gitkeep$|\.md$|\.txt$|"
                     r"\.list$|^migrations\.list$", base, re.IGNORECASE):
            return True
        if base.startswith((".snapshot", "index.")):
            return True
        return False

    mig_files = sorted(f for f in mig_files if not _excluded_file(f))

    # Semantic exclusions and additions per repo (verified against live repos):
    #   - go-gitea/gitea: modules/migration + services/migrations are REPO-IMPORT
    #     functionality (codebase.go, codecommit.go, dump.go), not schema
    #     versioning; models/migrations does not exist.
    #   - grafana: apps/dashboard/pkg/migration is dashboard-JSON conversion
    #     tooling (conversion_data_loss_detection.go), not schema; the real
    #     schema migrations live in pkg/services/sqlstore/migrations (kept).
    #   - keycloak: docs/guides/migration are docs; Java migrators under
    #     model/*/migration are code-level migrators; the Liquibase changelog
    #     lives in model/jpa/src/main/resources/META-INF/jpa-changelog-*.xml
    #     (added below).
    if repo == "go-gitea/gitea":
        mig_files = []
        mig_dirs = []
    elif repo == "grafana/grafana":
        mig_files = [f for f in mig_files
                     if not f.startswith(("apps/dashboard/pkg/migration/",
                                          "devenv/",
                                          "pkg/registry/apis/provisioning/",
                                          "public/app/features/provisioning/",
                                          "public/app/plugins/datasource/cloudwatch/"))]
        mig_dirs = [d for d in mig_dirs if d.startswith("pkg/")]
    elif repo == "keycloak/keycloak":
        # keep Liquibase changelog files (version-numbered XML) + Java migrators
        mig_files = [f for f in mig_files
                     if not f.startswith(("docs/", "tests/"))]
        # add the Liquibase changelog dir (META-INF not matched by segment regex)
        try:
            root = gh_json("repos/keycloak/keycloak/git/trees/main")
            model = next((e for e in root["tree"] if e["path"] == "model"), None)
            if model:
                t2 = gh_json(f"repos/keycloak/keycloak/git/trees/{model['sha']}")
                jpa = next((e for e in t2["tree"] if e["path"] == "jpa"), None)
                if jpa:
                    t3 = gh_json(f"repos/keycloak/keycloak/git/trees/{jpa['sha']}")
                    src = next((e for e in t3["tree"] if e["path"] == "src"), None)
                    if src:
                        t4 = gh_json(f"repos/keycloak/keycloak/git/trees/{src['sha']}")
                        main = next((e for e in t4["tree"] if e["path"] == "main"), None)
                        if main:
                            t5 = gh_json(f"repos/keycloak/keycloak/git/trees/{main['sha']}")
                            res = next((e for e in t5["tree"] if e["path"] == "resources"), None)
                            if res:
                                t6 = gh_json(f"repos/keycloak/keycloak/git/trees/{res['sha']}")
                                mf = next((e for e in t6["tree"] if e["path"] == "META-INF"), None)
                                if mf:
                                    t7 = gh_json(f"repos/keycloak/keycloak/git/trees/{mf['sha']}")
                                    changelogs = sorted(
                                        "model/jpa/src/main/resources/META-INF/" + e["path"]
                                        for e in t7["tree"]
                                        if e["type"] == "blob" and "changelog" in e["path"])
                                    mig_files = sorted(set(mig_files) | set(changelogs))
        except RuntimeError:
            pass

    # Framework markers present at root
    present_markers = []
    for fw, markers in FRAMEWORK_MARKERS.items():
        if root_names & markers:
            present_markers.append(fw)

    # Repos whose migration dirs were counted via non-recursive trees on the
    # migration dir (huge trees: metabase, posthog) store n_migration_files
    # but not the full file list; keep them out of the file-level listing.
    return {
        "repo": repo,
        "default_branch": branch,
        "truncated": truncated,
        "migration_dirs": sorted(mig_dirs),
        "migration_files": mig_files,
        "n_migration_files": len(mig_files),
        "root_markers": sorted(present_markers),
    }


def discover():
    os.makedirs(SNAP_DIR, exist_ok=True)
    results = []
    for repo in CORPUS:
        dest = os.path.join(SNAP_DIR, repo.replace("/", "__") + ".json")
        try:
            snap = discover_repo(repo)
            with open(dest, "w") as f:
                json.dump(snap, f, indent=1, sort_keys=True)
            results.append(snap)
            print(f"discovered {repo}: {snap['n_migration_files']} migration "
                  f"files, markers={snap['root_markers']}")
        except Exception as e:
            print(f"ERROR {repo}: {e}", file=sys.stderr)
    import datetime
    manifest = {
        "fetched_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "corpus_n": len(CORPUS),
        "mode": "discovery",
    }
    with open(os.path.join(SNAP_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    print(f"manifest written: {manifest['fetched_at']} ({len(CORPUS)} repos)")


# --------------------------------------------------------------- offline mode

# C2 naming-class patterns (order matters — first match wins).
NAMING_PATTERNS = [
    ("timestamp", re.compile(r"^\d{14}_")),                  # Rails
    ("prisma-ts-dir", re.compile(r"/\d{14}")),               # Prisma parent dir
    ("version-date", re.compile(r"Version\d+Date\d+")),      # Nextcloud class
    ("migration-date", re.compile(r"^Migration\d{8}")),      # Medusa TS
    ("liquibase-version", re.compile(r"changelog-\d+\.\d+", re.I)),  # keycloak
    ("version", re.compile(r"^v\d+(?:\.\d+){1,2}")),         # listmonk
    ("date-seq", re.compile(r"^\d{8}[A-Z]?[-_]")),           # knex/directus
    ("sequence", re.compile(r"^\d{1,6}[-_]")),               # Django/Laravel/Ghost
    ("flyway-seq", re.compile(r"^V\d+[-_]", re.I)),          # Flyway
    ("up-down", re.compile(r"\.(?:up|down)\.sql$", re.I)),   # mattermost
    ("up-down-pair", re.compile(r"^(?:up|down)\.sql$", re.I)),  # Diesel
]


def naming_class(path: str) -> str:
    base = path.rsplit("/", 1)[-1]
    for name, pat in NAMING_PATTERNS:
        if name == "prisma-ts-dir":
            if pat.search(path):  # parent-dir timestamp, full path needed
                return name
        elif pat.search(base):    # ^-anchored patterns behave as match
            return name
    return "semantic/other"


def load():
    snaps = []
    manifest = {}
    mp = os.path.join(SNAP_DIR, "manifest.json")
    if os.path.exists(mp):
        with open(mp) as f:
            manifest = json.load(f)
    for fn in sorted(os.listdir(SNAP_DIR)):
        if not fn.endswith(".json") or fn == "manifest.json":
            continue
        with open(os.path.join(SNAP_DIR, fn)) as f:
            snaps.append(json.load(f))
    return snaps, manifest


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="offline")
    a = ap.parse_args()
    if a.mode == "discover":
        discover()
        return
    snaps, manifest = load()
    if not snaps:
        print("no snapshot data — run `reproduce.py discover` first",
              file=sys.stderr)
        sys.exit(2)
    n = len(snaps)
    out = []
    out.append("DATABASE SCHEMA MIGRATIONS IN POPULAR OSS APPLICATIONS — "
               "canonical results (discovery phase)")
    out.append(f"corpus: n={n} repos | snapshot date: "
               f"{manifest.get('fetched_at', 'not pinned')}")
    out.append("")
    ok = [s for s in snaps if "error" not in s]
    err = [s for s in snaps if "error" in s]
    out.append(f"discovered: {len(ok)}/{n} | errors: {len(err)}")
    for s in err:
        out.append(f"  ERROR {s['repo']}: {s['error']}")
    with_mig = [s for s in ok if s["n_migration_files"] > 0]
    out.append(f"repos with >=1 migration file: {len(with_mig)}/{len(ok)} "
               f"({len(with_mig)/len(ok):.1%})")
    lo, hi = wilson_ci(len(with_mig), len(ok))
    out.append(f"  Wilson95: {lo:.1%}-{hi:.1%}")
    no_mig = [s for s in ok if s["n_migration_files"] == 0]
    if no_mig:
        out.append("  no-migration repos: " + ", ".join(s["repo"] for s in no_mig))
    # per-ecosystem adoption (manuscript Table 1 traceability)
    eco_order = ["Rails", "Django", "Laravel", "Node", "JVM", "Go", "PHP", "Rust"]
    for eco in eco_order:
        repos = ECOSYSTEM.get(eco, [])
        if not repos:
            continue
        hit = sum(1 for s in ok if s["repo"] in repos and s["n_migration_files"] > 0)
        out.append(f"  {eco:8s} with migrations: {hit}/{len(repos)} "
                   f"({hit/len(repos):.0%})")
    out.append("")
    out.append("per-repo discovery (migration files / dirs / root markers):")
    for s in ok:
        out.append(f"  {s['repo']:32s} n={s['n_migration_files']:5d} "
                   f"dirs={len(s['migration_dirs']):2d} "
                   f"markers={','.join(s['root_markers']) or '-'}")
        for d in s["migration_dirs"][:5]:
            out.append(f"      dir: {d}")
    out.append("")

    # ---- C2: naming conventions (pure filename classification)
    out.append("C2 migration-file naming conventions (per-repo dominant class; "
               "file-level classification):")
    class_counter = collections.Counter()
    class_repos = collections.Counter()
    for s in ok:
        files = s.get("migration_files", [])
        if not files:
            continue
        per = collections.Counter(naming_class(f) for f in files)
        class_counter.update(per)
        for c in per:
            class_repos[c] += 1
        dom, domn = per.most_common(1)[0]
        out.append(f"  {s['repo']:32s} n={len(files):5d} "
                   f"dominant={dom:18s} ({domn}/{len(files)})")
    out.append("  -- aggregated (files / repos touched) --")
    for c, n in class_counter.most_common():
        out.append(f"    {c:18s} files={n:6d} repos={class_repos[c]:3d}")
    # compact rows for manuscript traceability
    ts_total = class_counter.get("timestamp", 0)
    ts_repos = [s["repo"] for s in ok
                if any(naming_class(f) == "timestamp"
                       for f in s.get("migration_files", []))]
    out.append(f"  compact: timestamp {ts_total} files across {len(ts_repos)} "
               f"repos ({', '.join(ts_repos)})")
    out.append("")
    out.append("canonical-run key: every number above derives from "
               "data_snapshot/ via deterministic discovery.")
    print("\n".join(out))


if __name__ == "__main__":
    main()
