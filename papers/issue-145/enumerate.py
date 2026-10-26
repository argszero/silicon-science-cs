#!/usr/bin/env python3
"""Enumerate attested npm releases and measure their input coverage (issue #145).

The frame, stated so a reader can re-derive n
---------------------------------------------
    seeds                          a fixed, published list (SEEDS below)
    closure                        every package reachable from the seeds through
                                   declared `dependencies`, to depth DEPTH
    unit of measurement            one (package, latest-version) pair
    attested set                   units whose version carries dist.attestations

The frame is a *closure of a stated seed set*, not "all of npm": the registry has
no enumerable global ranking, and a relevance-ranked search is not a population.
The seeds and the expansion rule are the frame; both are printed with the run.

What is recorded per unit, and why each field is here
-----------------------------------------------------
  * n_deps / n_covered / coverage        the construct (see coverage.py)
  * attested / n_stmt / undecodable      the presence indicator and its failures;
                                         a decode failure is counted, never dropped
  * input_families                       git / purl / tarball / image / other --
                                         this is the field that answers "does any
                                         real statement name a package at all?"
  * build_type / oidc_issuer             the P2 grouping variable

Exit codes: 0 = run complete (any number of units), 2 = the run could not be taken
(nothing measured). A package that cannot be fetched is recorded with status
"NOT RUN" and its reason -- it is never silently treated as unattested.
"""
import argparse
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import coverage as cov

SEEDS = ["express", "react", "next", "vite", "typescript", "eslint", "jest",
         "webpack", "axios", "lodash", "vitest", "playwright-core", "zod",
         "prisma", "tailwindcss", "socket.io", "mongoose", "fastify", "undici",
         "sigstore"]

PACK_H = {"User-Agent": "silicon-science-145", "Accept": "application/vnd.npm.install-v1+json"}
ATT_H = {"User-Agent": "silicon-science-145"}
LOCK = threading.Lock()


def get_json(url, headers, tries=3, timeout=30):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (404, 401, 403):
                raise RuntimeError(f"HTTP {e.code}") from e
            last = f"HTTP {e.code}"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(1.0 + i)
    raise RuntimeError(last or "unknown")


def packument(name):
    return get_json("https://registry.npmjs.org/" + name.replace("/", "%2f"), PACK_H)


def uri_family(uri):
    u = uri.lower()
    if u.startswith("pkg:"):
        return "purl:" + u.split("/", 1)[0].split(":")[1]
    if u.startswith("git+") or u.startswith("git:"):
        return "git"
    if "registry.npmjs.org" in u:
        return "tarball:npm"
    if any(h in u for h in ("docker.io", "gcr.io", "ghcr.io", "index.docker.io")):
        return "image"
    if u.startswith("https://github.com/") or u.startswith("https://gitlab.com/"):
        return "vcs-https"
    return "other"


def closure(seeds, depth, log):
    seen, frontier = set(), []
    for s in seeds:
        if s not in seen:
            seen.add(s)
            frontier.append(s)
    pages = {}
    for d in range(depth):
        nxt = []
        for name in frontier:
            try:
                p = packument(name)
            except Exception as e:
                log.append({"stage": "closure", "package": name, "error": str(e)})
                continue
            pages[name] = p
            ver = (p.get("dist-tags") or {}).get("latest")
            meta = (p.get("versions") or {}).get(ver) or {}
            for dep in sorted((meta.get("dependencies") or {}).keys()):
                if dep not in seen:
                    seen.add(dep)
                    nxt.append(dep)
        frontier = nxt
    return sorted(seen), pages


def measure(name, page=None):
    """One unit: the latest version of `name`."""
    row = {"package": name, "status": "OK", "version": None, "attested": False,
           "n_deps": 0, "n_covered": 0, "coverage": None, "n_stmt": 0,
           "undecodable": 0, "input_families": {}, "n_inputs": 0,
           "build_type": None, "oidc_issuer": None}
    try:
        p = page if page is not None else packument(name)
    except Exception as e:
        row.update(status="NOT RUN", error=str(e))
        return row
    ver = (p.get("dist-tags") or {}).get("latest")
    meta = (p.get("versions") or {}).get(ver) or {}
    deps = sorted((meta.get("dependencies") or {}).keys())
    row.update(version=ver, n_deps=len(deps))
    att = (meta.get("dist") or {}).get("attestations")
    if not att:
        return row                                   # coverage not asked of it
    row["attested"] = True
    url = att.get("url") if isinstance(att, dict) else att
    try:
        bundle = get_json(url, ATT_H)
    except Exception as e:
        row.update(status="NOT RUN", error=f"attestation: {e}")
        return row
    sts, bad = cov.decode_statements(bundle)
    uris = cov.attested_inputs(sts)
    n, m, c = cov.coverage(deps, uris)
    families = {}
    for u in uris:
        f = uri_family(u)
        families[f] = families.get(f, 0) + 1
    row.update(n_stmt=len(sts), undecodable=bad, n_inputs=len(uris),
               n_covered=n, coverage=c, input_families=families,
               build_type=cov.build_type(sts), oidc_issuer=cov.oidc_issuer(bundle))
    return row


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--limit", type=int, default=0, help="0 = the whole closure")
    ap.add_argument("--out", default="snapshot_npm.json")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(argv)

    log = []
    t0 = time.time()
    names, pages = closure(SEEDS, a.depth, log)
    if a.limit:
        names = names[:a.limit]
    print(f"frame: {len(SEEDS)} seeds, depth {a.depth} -> closure {len(names)} packages "
          f"measured of {(len(names))}")

    rows = []
    done = [0]

    def work(nm):
        r = measure(nm, pages.get(nm))
        with LOCK:
            done[0] += 1
            if done[0] % 25 == 0:
                print(f"  ... {done[0]}/{len(names)} ({time.time()-t0:.0f}s)", flush=True)
        return r

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        rows = list(ex.map(work, names))

    ok = [r for r in rows if r["status"] == "OK"]
    att = [r for r in ok if r["attested"]]
    withdeps = [r for r in att if r["n_deps"] > 0]
    fam = {}
    for r in att:
        for k, v in r["input_families"].items():
            fam[k] = fam.get(k, 0) + v
    summary = {
        "frame": {"seeds": SEEDS, "depth": a.depth, "closure_size": len(names),
                  "enumeration_rule": "declared `dependencies` of each latest version, "
                                      "expanded breadth-first to --depth"},
        "units": len(rows), "ok": len(ok),
        "not_run": sum(1 for r in rows if r["status"] != "OK"),
        "attested": len(att),
        "attested_with_deps": len(withdeps),
        "attested_zero_coverage": sum(1 for r in withdeps if r["n_covered"] == 0),
        "attested_positive_coverage": sum(1 for r in withdeps if r["n_covered"] > 0),
        "deps_total": sum(r["n_deps"] for r in withdeps),
        "deps_covered_total": sum(r["n_covered"] for r in withdeps),
        "input_families": fam,
        "undecodable_payloads": sum(r["undecodable"] for r in att),
        "build_types": {}, "oidc_issuers": {},
        "elapsed_s": round(time.time() - t0, 1),
        "not_run_detail": [r for r in rows if r["status"] != "OK"][:20],
        "closure_log": log[:20],
    }
    for r in att:
        if r["build_type"]:
            summary["build_types"][r["build_type"]] = summary["build_types"].get(r["build_type"], 0) + 1
        if r["oidc_issuer"]:
            summary["oidc_issuers"][r["oidc_issuer"]] = summary["oidc_issuers"].get(r["oidc_issuer"], 0) + 1

    snap = {"retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "summary": summary, "rows": rows}
    text = json.dumps(snap, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    digest = hashlib.sha256(text.encode()).hexdigest()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), a.out)
    with open(out, "w") as f:
        f.write(text)
    with open(out + ".sha256", "w") as f:
        f.write(f"{digest}  {a.out}\n")

    print()
    print(f"SNAPSHOT units={summary['units']} ok={summary['ok']} not_run={summary['not_run']} "
          f"attested={summary['attested']} with_deps={summary['attested_with_deps']}")
    print(f"SNAPSHOT zero_coverage={summary['attested_zero_coverage']} "
          f"positive_coverage={summary['attested_positive_coverage']} "
          f"deps={summary['deps_total']} covered={summary['deps_covered_total']}")
    print(f"SNAPSHOT input_families={summary['input_families']}")
    print(f"SNAPSHOT build_types={list(summary['build_types'].keys())}")
    print(f"SNAPSHOT issuers={list(summary['oidc_issuers'].keys())}")
    print(f"SNAPSHOT sha256={digest} elapsed={summary['elapsed_s']}s -> {a.out}")
    if summary["ok"] == 0:
        print("SNAPSHOT: NOT RUN — nothing was measured")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
