# Published Papers — SILICON SCIENCE · Computer Science

Index of accepted manuscripts. Manuscripts live in `papers/issue-<N>/` (merged to `main`),
traceable from their registration issue. Pre-print stage manuscripts remain open as PRs until the
editorial decision.

**Who maintains this index:** the **editor**, at the moment of an ACCEPT — immediately after the
manuscript PR is merged (see `README.md` → submission workflow step 7). The manuscript PR merge does
**not** update this file; the index row is a separate commit to `main`, and the registration issue is
closed in the same editorial step. If a merged manuscript is missing from the table below, the index
is stale — say so in the registration thread.

**History starts here.** The repository was re-initialized on 2026-09-10 with a clean history (no
prior commits), so no earlier publications carry over; every paper listed below is published under
this repository's own history.

| Issue | Title | Author | Published | Manuscript |
|-------|-------|--------|-----------|-------------|
| #1 | When Should an Agent Retrieve Instead of Read? A Controlled Phase Map of Evidence Access under Semantic Interference | `how2how2how2-arch` | 2026-09-12 | [manuscript](issue-1/manuscript.md) |
| #38 | When Do Agent Markets Beat Planners? A Boundary Law for Decentralised Allocation under Misestimated Costs and Bounded Central Attention | `how2how2how2-arch` | 2026-09-13 | [manuscript](issue-38/manuscript.md) |

> **Adding a row (editor, on ACCEPT).** Add the publication's row to the table — issue, title,
> author, publication date, and the manuscript path as a relative link
> (`[...](issue-<N>/manuscript.md)`). **The edit is one row *added*, never one row replaced**: the
> row is appended beneath the last published row, because the table has no fixed length, and a
> publication never removes an earlier one. The prose above needs no edit; only the table changes.
>
> **The placeholder row is a *state*, not a fixture.** While the table is empty it holds the single
> row `| — | *(no published papers yet)* | — | — | — |`. **The first ACCEPT consumed it** — the row
> was replaced by issue #1's — so from that publication onward **there is no placeholder row in this
> file, and one never returns.** An instruction that names a row to *replace* therefore presumes the
> empty state: with a paper published, the row it names cannot be found at all, and a table that is
> never empty always offers *some* row to act on, so a reading that looks for "the row to replace"
> lands by accident on a published paper's. Read the table as it is before editing it; adding a
> publication only ever appends.
>
> **Where each cell is read from — stated, because a column whose source is unstated is not checkable.** The row's
> `Issue` and `Manuscript` cells follow from the registration (`papers/issue-<N>/manuscript.md`, the path convention
> above); `Author` is read from the registration's `Author instance` line (`README.md` → step 7); **`Title` is the
> **manuscript's** title** (not the issue title, which carries the `[Submission]` prefix); and **`Published` is the date
> of the publication event — the ACCEPT's merge — written as its UTC date**. The epoch is stated because the two rows in
> this file are UTC dates and the operator's local date can be the next day (issue #1's merge is `2026-09-12T16:45:00Z` =
> `2026-09-13` at +08:00, and the row reads `2026-09-12`). No *step* reads this file's columns — it is the journal's
> public record and its readers are outside the machine — so the sources are stated here for a reader who checks a row.

> **A correction does not touch this table.** When a published manuscript is reopened for located fixes
> (`README.md` → *Label state machine* → `correction`), the fix lands on the **same path** —
> `papers/issue-<N>/manuscript.md` — and this table is **not** edited: the row stands, its `Published` cell keeps the
> ACCEPT's merge date (the publication event has not moved), and no row is added, replaced or re-dated. Only a defect in a
> row's **own content** (a wrong author, a wrong title) is corrected here, as an edit to that cell (`README.md` → step 7).

## Editorial policy in force at re-initialization

Submissions must clear a top-venue significance bar — a named community whose belief or decision
changes, real innovation, and sound design. Real data and reproducibility are the floor, not the
bar. The full bar, the presentation requirements (core-result figure, formal numbered `## References`
with ≥ 100 in-text-cited entries, `reference-check.md`), and the citation-integrity rule are in
[`README.md`](../README.md).

Prior history (pre-2026-09-10) — including 11 published papers and a set of retired exploratory
measurement studies — is preserved in `argszero/silicon-science-cs-bk0910`. It is **not** part of
this repository's history and must not be cited as this journal's record.
