# Database Schema Migrations in Popular Open-Source Applications

**Issue**: #25 — **Author**: how2how2how2-arch — **Contribution level**: `system`

An empirical measurement of the schema-migration practice layer on 32 popular
open-source web applications across nine ecosystems (Rails, Django, Laravel,
Node/Prisma/TypeORM/Knex, JVM/Liquibase, Go, PHP, Rust/Diesel), using the GitHub
trees API with no cloning. Three findings: C1 adoption (29/32, 90.6%), C2 naming
conventions as ecosystem fingerprints, C3 rollback support (20.6%) vs destructive
operations (12.0%) with the highest-risk concentration in TypeORM/Liquibase.

## One-command reproduction (offline)

```bash
bash reproduce.sh
```

Reads the committed `data_snapshot/` (32 per-repository JSON snapshots with
migration file lists and sampled file contents, plus `manifest.json` pinning the
fetch date), recomputes every statistic, and diffs against
`expected_output/discovery_results.txt` (C1/C2) and
`expected_output/c3_results.txt` (C3). **Exit 0 iff byte-identical.** The pipeline
is fully deterministic (classification is a pure function of the snapshot), so no
tolerance band is needed.

## Re-fetching fresh data (optional, requires `gh` + network)

```bash
python3 reproduce.py discover        # re-discover migration files for all 32 repos
python3 c3_classify.py content       # re-fetch sampled file contents
```

## Corpus (n=32)

| Ecosystem | Repositories | With migrations |
|-----------|---|-----------------|
| Rails | mastodon, discourse, lobsters, decidim | 4/4 |
| Django | sentry, zulip, wagtail, posthog, pretix, authentik, netbox, paperless-ngx | 8/8 |
| Laravel | flarum, koel, bookstack, monica | 4/4 |
| Node | Ghost, strapi, directus, medusa, cal.com | 5/5 |
| JVM | keycloak, sonarqube, metabase | 3/3 |
| Go | gitea, grafana, mattermost, listmonk | 3/4 |
| PHP | nextcloud, matomo, moodle | 1/3 |
| Rust | lemmy | 1/1 |

Frameworks are excluded deliberately (they carry no schemas); the corpus targets
applications that actually run databases.

## Key results (see expected_output for the full canonical run)

- **C1** — 29/32 (90.6%, Wilson95 75.8%-96.8%) apps version their schema via
  migration files; no-migration: gitea, matomo, moodle. Framework choice is
  ecosystem-deterministic.
- **C2** — Naming: timestamp 3704 files/4 repos (Rails 100%), sequence 3824/16
  (Django/Laravel/Node), up-down pairs 682/1 (Diesel), Prisma dir-timestamp
  597/2, plus 6 minor classes.
- **C3** (684 sampled files) — Rollback 141/684 (20.6%); destructive
  82/684 (12.0%). Highest risk: medusa (TypeORM) 21/25 destructive with 0
  rollback; metabase (Liquibase) 14/25 destructive with 0 rollback. Counterexample:
  lemmy (Diesel) 17/25 destructive with 100% rollback; mattermost 15/25 with 100%.

## Data availability

- `data_snapshot/` — 32 per-repository JSON snapshots (migration file lists,
  root markers, sampled file contents for C3) + `manifest.json`; the ground
  truth for all results.
- `expected_output/discovery_results.txt` — frozen C1/C2 canonical output.
- `expected_output/c3_results.txt` — frozen C3 canonical output (incl. per-file
  detail).
- `reproduce.py` — discovery + C1/C2 classifier (`discover` / offline modes).
- `c3_classify.py` — C3 content classifier (`content` fetch / offline modes).
- `reproduce.sh` — one-command offline reproduction + diff gate.
