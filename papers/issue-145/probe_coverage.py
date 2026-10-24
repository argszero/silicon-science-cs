#!/usr/bin/env python3
"""Pilot instrument for issue #145 — input coverage of published provenance.

For one npm package version, fetch the published attestation bundle and the release's
declared direct dependencies, then compute:

    coverage c = |{attested inputs that identify a declared dependency}| / |declared deps|

An attested input is a resolvedDependency (SLSA v1) or material (SLSA v0.2) URI. It counts as
covering a dependency only when its URI *identifies* that dependency — a purl
(pkg:npm/<name>@<ver>) or a registry URL naming it. A git URL of the source repository is the
build's source input, NOT a dependency, and it therefore never covers a closure member; that
distinction is the whole construct, so it is enforced explicitly rather than by string luck.

PILOT ONLY: the seed list is hand-picked and small. No population claim is made from it.
"""
import json
import sys
import time
import urllib.request

H = {"User-Agent": "silicon-science-145-pilot", "Accept": "application/vnd.npm.install-v1+json"}
ATT_H = {"User-Agent": "silicon-science-145-pilot"}


def get(url, headers=H, tries=3, timeout=25):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
                return json.load(r)
        except Exception as e:  # network flake is a NOT RUN, never a zero
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"NOT RUN: {url}: {last}")


def decode_statements(bundle):
    import base64
    out = []
    for att in bundle.get("attestations", []):
        b = att.get("bundle", {})
        env = b.get("dsseEnvelope", {})
        payload = env.get("payload")
        if not payload:
            continue
        try:
            st = json.loads(base64.b64decode(payload))
        except Exception:
            continue
        out.append({
            "predicateType": att.get("predicateType"),
            "statement": st,
            "certificate": bool(b.get("verificationMaterial", {}).get("certificate")),
        })
    return out


def attested_inputs(statements):
    """Resolved dependency URIs named by each statement (SLSA v1) / materials (v0.2)."""
    uris = []
    for s in statements:
        st = s["statement"]
        pred = st.get("predicate") or {}
        bd = pred.get("buildDefinition") or {}
        for m in bd.get("resolvedDependencies") or []:
            if m.get("uri"):
                uris.append(m["uri"])
        for m in pred.get("materials") or []:
            if m.get("uri"):
                uris.append(m["uri"])
    return uris


def covers(uri, dep_name):
    """Does this attested input URI identify the dependency `dep_name`?"""
    u = uri.lower()
    if u.startswith("pkg:npm/") or u.startswith("pkg:npm%2f"):
        rest = u.split("pkg:npm/", 1)[-1].split("@")[0]
        return rest.split("/")[-1] == dep_name.lower()
    if "registry.npmjs.org" in u:
        tail = u.split("registry.npmjs.org/", 1)[-1]
        return tail.startswith(dep_name.lower() + "/") or tail.startswith(dep_name.lower() + "@")
    return False  # source repos, container images, and anything else: not a closure member


def probe(pkg):
    pack = get("https://registry.npmjs.org/" + pkg.replace("/", "%2f"))
    ver = (pack.get("dist-tags") or {}).get("latest")
    meta = (pack.get("versions") or {}).get(ver) or {}
    deps = sorted((meta.get("dependencies") or {}).keys())
    att = (meta.get("dist") or {}).get("attestations")
    row = {"package": pkg, "version": ver, "n_deps": len(deps), "attested": bool(att),
           "n_stmt": 0, "n_inputs": 0, "n_covered": 0, "coverage": None,
           "predicates": [], "inputs": [], "certificate": False}
    if not att:
        return row
    url = att.get("url") if isinstance(att, dict) else att
    bundle = get(url, headers=ATT_H)
    sts = decode_statements(bundle)
    uris = attested_inputs(sts)
    covered = [d for d in deps if any(covers(u, d) for u in uris)]
    row.update({
        "n_stmt": len(sts),
        "n_inputs": len(uris),
        "n_covered": len(covered),
        "coverage": (len(covered) / len(deps)) if deps else None,
        "predicates": [s["predicateType"] for s in sts],
        "inputs": uris,
        "certificate": any(s["certificate"] for s in sts),
    })
    return row


def main(argv):
    pkgs = argv[1:] or ["sigstore", "zod", "axios", "undici", "vitest", "playwright-core"]
    rows = []
    for p in pkgs:
        try:
            r = probe(p)
        except Exception as e:
            print(f"{p}: {e}")
            continue
        rows.append(r)
        cov = "n/a" if r["coverage"] is None else f'{r["coverage"]:.3f}'
        print(f'{r["package"]:18s} v{r["version"]:<10s} deps={r["n_deps"]:<3d} '
              f'attested={str(r["attested"]):<5s} stmt={r["n_stmt"]} inputs={r["n_inputs"]} '
              f'covered={r["n_covered"]} c={cov}')
        for u in r["inputs"][:4]:
            print(f'      input: {u}')
    att = [r for r in rows if r["attested"]]
    zero = [r for r in att if r["n_covered"] == 0]
    print()
    print(f"PILOT (not a population claim): attested={len(att)}/{len(rows)} "
          f"zero_coverage={len(zero)}/{len(att) if att else 0} "
          f"total_declared_deps={sum(r['n_deps'] for r in att)} "
          f"total_covered={sum(r['n_covered'] for r in att)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
