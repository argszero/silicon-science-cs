#!/usr/bin/env python3
"""Plant battery for the coverage instrument (issue #145).

Why this file exists
--------------------
The pilot measured coverage 0 on 6 of 6 packages. That is exactly the answer a
**broken** instrument also gives, so the number carries no weight until the
instrument is demonstrated to report a *non-zero* coverage when one exists, and
to refuse the two near-miss matches that would manufacture one:

  * counting the build's **source repository** URI as a covered dependency — the
    one input every npm statement actually carries, so a match that accepts it
    turns "0 of 23" into "3 of 3" while looking like a stricter reading;
  * accepting a **substring/family** match (`react` covered by `react-dom`),
    which would inflate coverage wherever a package's sibling is named.

Each plant therefore has three readings: the correct instrument must produce the
expected value, and each deliberately wrong variant must be **caught** by the
plant aimed at it. A battery in which nothing fails has measured nothing.

Run: python3 plant_coverage.py     (exit 0 = every plant fired and the
                                    instrument answers correctly on all of them)
"""
import json
import sys

import coverage as cov

FAILS = []
CHECKS = []


def check(name, got, want):
    ok = got == want
    CHECKS.append(ok)
    print(f"  [{'ok' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")
    if not ok:
        FAILS.append(name)


# --------------------------------------------------------------------------
# deliberately wrong implementations — each must be caught by its own plant
# --------------------------------------------------------------------------

def wrong_any_input_counts(deps, uris, ecosystem="npm"):
    """Defect: any named input covers the closure (the source repo counts)."""
    d = {x.lower() for x in deps}
    return (min(len(d), len(uris)), len(d), (min(len(d), len(uris)) / len(d)) if d else None)


def wrong_substring(deps, uris, ecosystem="npm"):
    """Defect: a dependency is covered if any input URI contains its name."""
    d = {x.lower() for x in deps}
    hit = {x for x in d if any(x in u.lower() for u in uris)}
    return (len(hit), len(d), (len(hit) / len(d)) if d else None)


def wrong_empty_is_zero(deps, uris, ecosystem="npm"):
    """Defect: an empty closure is reported as coverage 0.0, not as n/a."""
    n, m, c = cov.coverage(deps, uris, ecosystem)
    return (n, m, 0.0 if c is None else c)


def wrong_last_path_token(deps, uris, ecosystem="npm"):
    """Defect: the last path token of any URI is read as a package name.

    This is the most seductive of the four, because it *looks* like a parser:
    for `github.com/facebook/react` it yields `react`, which is a real package
    and, in the common case, the packaged project's own name.  It covers the
    closure with the build's **source repository**, which is the very confusion
    the construct exists to measure.
    """
    d = {x.lower() for x in deps}
    hit = set()
    for u in uris:
        tok = u.rstrip("/").rsplit("/", 1)[-1].split("@")[0].split("?")[0].lower()
        if tok in d:
            hit.add(tok)
    return (len(hit), len(d), (len(hit) / len(d)) if d else None)


WRONG = {
    "any_input_counts": wrong_any_input_counts,
    "substring_match": wrong_substring,
    "empty_closure_is_zero": wrong_empty_is_zero,
    "last_path_token": wrong_last_path_token,
}

PLANTS = []


def plant(pid, deps, uris, want, catches):
    PLANTS.append({"id": pid, "deps": deps, "uris": uris, "want": want, "catches": catches})


# --------------------------------------------------------------------------
# the plants
# --------------------------------------------------------------------------

# A1 — the source repository is named, the closure is not. This is the real
# npm shape measured on 2026-10-21, and the plant that keeps it from counting.
plant("A1 source-only statement, 3 declared deps",
      ["react", "react-dom", "scheduler"],
      ["git+https://github.com/facebook/react@refs/heads/main"],
      (0, 3, 0.0),
      ["any_input_counts"])

# A2 — a sibling in the same family is named; the dependency itself is not.
plant("A2 sibling package named, dep not covered",
      ["react"],
      ["pkg:npm/react-dom@18.2.0"],
      (0, 1, 0.0),
      ["substring_match"])

# A3 — empty closure: n/a, never 0.0.
plant("A3 empty closure reports n/a",
      [],
      ["pkg:npm/anything@1.0.0"],
      (0, 0, None),
      ["empty_closure_is_zero"])

# A4 — exact partial coverage: 2 of 5.
plant("A4 partial coverage is exact 2/5",
      ["a", "b", "c", "d", "e"],
      ["pkg:npm/a@1.0.0", "pkg:npm/b@2.0.0",
       "git+https://github.com/x/y@refs/tags/v1"],
      (2, 5, 0.4),
      ["any_input_counts"])

# A5 — a scoped purl in canonical percent-encoded form covers a scoped name.
plant("A5 scoped purl covers scoped dep",
      ["@sentry/node"],
      ["pkg:npm/%40sentry/node@7.10.0"],
      (1, 1, 1.0),
      [])

# A6 — a registry tarball URL identifies the package it ships.
plant("A6 registry tarball URL covers dep",
      ["lodash"],
      ["https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz"],
      (1, 1, 1.0),
      ["substring_match"])

# A7 — a purl with qualifiers/subpath still resolves to the name.
plant("A7 purl with qualifiers and subpath",
      ["left-pad"],
      ["pkg:npm/left-pad@1.3.0?repository_url=https://r.example#sub/path"],
      (1, 1, 1.0),
      [])

# A8 — a container image, a build config, and a bare string identify no package.
plant("A8 non-package inputs cover nothing",
      ["webpack"],
      ["docker.io/library/node:20", "https://github.com/x/y/blob/main/.github/workflows/ci.yml",
       "unparseable"],
      (0, 1, 0.0),
      ["any_input_counts"])

# A9 — the source repository is *named after the package* (github.com/facebook/react).
# The common case: a naive last-path-token reader calls this a covered dependency.
plant("A9 source repo named like the dep covers nothing",
      ["react", "scheduler"],
      ["git+https://github.com/facebook/react"],
      (0, 2, 0.0),
      ["last_path_token", "any_input_counts"])


def run_plants():
    print("plants — correct instrument")
    for p in PLANTS:
        check(p["id"], cov.coverage(p["deps"], p["uris"]), p["want"])

    print("\nplants — wrong variants must be CAUGHT")
    caught_by = {k: [] for k in WRONG}
    for p in PLANTS:
        for wid in p["catches"]:
            got = WRONG[wid](p["deps"], p["uris"])
            if got != p["want"]:
                caught_by[wid].append(p["id"])
    for wid, ids in caught_by.items():
        ok = bool(ids)
        CHECKS.append(ok)
        _ids = ids if ids else "NOTHING -- the plant does not reach this defect"
        print("  [%s] %s caught by %s" % ("ok" if ok else "FAIL", wid, _ids))
        if not ok:
            FAILS.append(f"{wid} not caught")


def run_decoder_plants():
    """An undecodable payload must be counted, not silently dropped."""
    import base64
    good = base64.b64encode(json.dumps({
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {"buildDefinition": {
            "buildType": "https://example/bt",
            "resolvedDependencies": [{"uri": "pkg:npm/react@18.2.0"}]}},
    }).encode()).decode()
    bundle = {"attestations": [
        {"predicateType": "https://slsa.dev/provenance/v1",
         "bundle": {"dsseEnvelope": {"payload": good}}},
        {"predicateType": "https://slsa.dev/provenance/v1",
         "bundle": {"dsseEnvelope": {"payload": "!!!not-base64!!!"}}},
    ]}
    print("\nplants — decoder")
    sts, bad = cov.decode_statements(bundle)
    check("decoder keeps the good statement", len(sts), 1)
    check("decoder counts the undecodable payload", bad, 1)
    check("buildType read from the good statement", cov.build_type(sts), "https://example/bt")
    check("inputs read from the good statement", cov.attested_inputs(sts), ["pkg:npm/react@18.2.0"])


def main():
    run_plants()
    run_decoder_plants()
    total, failed = len(CHECKS), len(FAILS)
    print()
    if failed:
        print(f"PLANT BATTERY: {total - failed}/{total} ok — {failed} FAILED: {FAILS}")
        return 1
    print(f"PLANT BATTERY: ALL {total} CHECKS FIRED ({len(PLANTS)} plants, "
          f"{len(WRONG)} wrong variants caught)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
