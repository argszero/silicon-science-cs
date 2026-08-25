# Issue #7 — Type-Evident Code

**Title**: *Type-Evident Code: How Much of Python's Missing Type-Annotation
Burden Is Trivially Recoverable from Source Structure?*

Empirical study (pure-AST, stdlib-only) of 7 popular open-source Python
packages: how much of the missing-annotation burden is recoverable from
source structure alone, and how much of existing annotation effort is
redundant with defaults.

- `manuscript.md` — full manuscript (falsifiable claims C1–C3, method,
  results with 95% t-CIs, threats, conclusion)
- `reproduce.py` — canonical analyzer (deterministic, stdlib `ast` only)
- `reproduce.sh` — one-command reproduction
- `expected_output/manuscript_results.txt` — committed expected output
  (canonical-run traceability: every number in the manuscript appears in
  this file)

## One-command reproduction

```bash
bash reproduce.sh
```

This script:
1. clones the 7 corpus packages at their pinned commits into `./.corpus/`;
2. runs the canonical analyzer and verifies each clone is at its pinned
   commit (`--check-commits`);
3. diffs the fresh output against `expected_output/manuscript_results.txt`
   and exits 0 iff byte-identical.

**Requirements**: `bash`, `git`, `python3 ≥ 3.10` (standard library only —
no pip packages, no network beyond the initial clone).

## Corpus manifest (pinned commits)

| package  | domain           | pinned commit | analyzed subtree      |
|----------|------------------|---------------|-----------------------|
| click    | CLI framework    | `2c8cd3ac958a`| `click/src/click`     |
| dateutil | date parsing     | `48bd1af97e71`| `dateutil/src/dateutil`|
| flask    | web framework    | `d318b6834711`| `flask/src/flask`     |
| gunicorn | web server       | `36f2a3c1b80d`| `gunicorn/gunicorn`   |
| httpie   | CLI              | `5b604c37c6c6`| `httpie/httpie`       |
| tqdm     | CLI/progress     | `96f2e60e4584`| `tqdm/tqdm`           |
| typer    | CLI framework    | `9a7b2e83f6b6`| `typer/typer`         |

Test files are excluded; the analysis covers package source only. The same
manifest lives inside `reproduce.py` (single source of truth).

## Expected output (key numbers)

```
C1  default-evident: 651/2533 = 25.7% of unannotated
C1  strong(typed):   301/2533 = 11.9% of unannotated
C1  None-only:       350/2533 = 13.8% of unannotated
C3  redundant:       530/4309 = 12.3% of annotated
C1 strong per-package mean 13.1% ± 10.9% (95% t-CI, n=4)
C3 per-package mean        10.8% ±  6.2% (95% t-CI, n=5)
```

Full per-package tables and the evidence decomposition are in
`expected_output/manuscript_results.txt`.
