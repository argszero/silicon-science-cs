#!/usr/bin/env python3
"""Third-builder probe: does an OCI image provenance name its package closure?

The point of this measurement (issue #145, R675) is the axis the two package registries
cannot supply: npm and PyPI attestations are BOTH produced by GitHub Actions, so a claim
about "published provenance" measured only there is scoped to one builder class. OCI
images are built by other builders (apko / melange / buildx / Cloud Build), and their
attestations sit next to the image as `.att` / `.sbom` tags in the registry.

Per image, in the Chainguard registry:

  latest manifest -> amd64 digest -> <sha256-...>.att manifest -> DSSE envelopes
  each envelope -> in-toto statement -> predicateType + resolvedDependencies

The unit of analysis is the STATEMENT. For each statement we record:
  - predicateType
  - whether it is SLSA provenance, and if so its buildType and builder id
  - how many resolvedDependencies it declares at the SLSA v1 path
    (predicate.buildDefinition.resolvedDependencies) and at the older v0.2 path
    (predicate.materials / predicate.invocation)
  - for non-provenance predicates, whether the payload carries a package list

Every unreachable unit is NOT RUN with its reason — never a zero.

Usage: python3 oci_enumerate.py [--images n] [--out FILE]
"""
import argparse
import base64
import json
import subprocess
import sys
import time
import hashlib
from urllib.parse import unquote

REG = "https://cgr.dev"
REPO = "chainguard/%s"
UA = "emrg-silicon-science/1.0 (research; issue-145)"

CANDIDATES = [
    "static", "busybox", "bash", "curl", "git", "nginx",
    "python", "node", "go", "openjdk", "redis", "postgresql",
]


def curl(url, accept=None, max_time=30):
    """One GET, following redirects. Returns (http_code, body_bytes)."""
    cmd = ["curl", "-sL", "--max-time", str(max_time), "-A", UA,
           "-w", "\n%{http_code}", url]
    if accept:
        cmd[1:1] = ["-H", "Accept: " + accept]
    p = subprocess.run(cmd, capture_output=True)
    body = p.stdout
    code = 0
    if b"\n" in body:
        head, _, tail = body.rpartition(b"\n")
        try:
            code = int(tail.strip())
            body = head
        except ValueError:
            pass
    return code, body


def token(repo, max_time=30):
    code, body = curl("%s/token?scope=repository:%s:pull&service=registry.cgr.dev"
                      % (REG, repo), max_time=max_time)
    if code != 200:
        return None
    try:
        return json.loads(body)["token"]
    except Exception:
        return None


def get_json(url, tok, accept, max_time=30):
    cmd = ["curl", "-sL", "--max-time", str(max_time), "-A", UA,
           "-H", "Authorization: Bearer " + tok, "-w", "\n%{http_code}", url]
    if accept:
        cmd[1:1] = ["-H", "Accept: " + accept]
    p = subprocess.run(cmd, capture_output=True)
    raw = p.stdout
    head, _, tail = raw.rpartition(b"\n")
    try:
        code = int(tail.strip())
    except ValueError:
        return 0, None
    if code != 200:
        return code, None
    try:
        return code, json.loads(head)
    except Exception:
        return code, None


MAN_ACCEPT = ("application/vnd.oci.image.index.v1+json, "
              "application/vnd.oci.image.manifest.v1+json, "
              "application/vnd.docker.distribution.manifest.list.v2+json, "
              "application/vnd.docker.distribution.manifest.v2+json")


def dsse_statement(blob):
    env = json.loads(blob)
    payload = env.get("payload")
    if payload is None:
        return None
    padded = payload + "=" * (-len(payload) % 4)
    st = json.loads(base64.b64decode(padded))
    return st


def one_image(name, budget_s=40):
    """Measure one image. Returns a record; status is OK / NOT RUN with a reason."""
    rec = {"image": name, "status": "NOT RUN", "reason": None,
           "digest": None, "n_statements": 0, "statements": [],
           "packages_in_any_statement": None}
    t0 = time.time()
    repo = REPO % name
    tok = token(repo)
    if not tok:
        rec["reason"] = "no pull token (repository not anonymously readable)"
        rec["elapsed_s"] = round(time.time() - t0, 1)
        return rec

    code, idx = get_json("%s/v2/%s/manifests/latest" % (REG, repo), tok, MAN_ACCEPT)
    if code != 200 or not idx:
        rec["reason"] = "no manifest for tag latest (http %s)" % code
        rec["elapsed_s"] = round(time.time() - t0, 1)
        return rec
    digest = None
    if "manifests" in idx:
        for m in idx["manifests"]:
            if (m.get("platform") or {}).get("architecture") == "amd64":
                digest = m["digest"]
                break
        if digest is None and idx["manifests"]:
            digest = idx["manifests"][0]["digest"]
    else:
        rec["reason"] = "single-arch manifest, no platform child to key attestations on"
        rec["elapsed_s"] = round(time.time() - t0, 1)
        return rec
    rec["digest"] = digest

    tag = digest.replace(":", "-") + ".att"
    code, am = get_json("%s/v2/%s/manifests/%s" % (REG, repo, tag), tok, MAN_ACCEPT)
    if code != 200 or not am:
        rec["reason"] = "no .att manifest at %s (http %s)" % (tag[:24], code)
        rec["elapsed_s"] = round(time.time() - t0, 1)
        return rec

    stmts = []
    for layer in am.get("layers", []):
        if time.time() - t0 > budget_s:
            rec["reason"] = "budget exhausted mid-image"
            rec["elapsed_s"] = round(time.time() - t0, 1)
            return rec
        code, blob = None, None
        cmd = ["curl", "-sL", "--max-time", "30", "-A", UA,
               "-H", "Authorization: Bearer " + tok,
               "%s/v2/%s/blobs/%s" % (REG, repo, layer["digest"])]
        p = subprocess.run(cmd, capture_output=True)
        if not p.stdout:
            stmts.append({"predicateType": None, "undecodable": True})
            continue
        try:
            st = dsse_statement(p.stdout)
        except Exception:
            st = None
        if st is None:
            stmts.append({"predicateType": None, "undecodable": True})
            continue
        pred = st.get("predicate") or {}
        pt = st.get("predicateType")
        s = {"predicateType": pt, "undecodable": False,
             "predicate_keys": sorted(pred.keys())[:12]}
        if pt and "slsa.dev/provenance" in pt:
            bd = pred.get("buildDefinition") or {}
            rd_v1 = bd.get("resolvedDependencies")
            rd_v02 = pred.get("materials")
            run = pred.get("runDetails") or {}
            builder = (run.get("builder") or {}).get("id")
            s["is_provenance"] = True
            s["buildType"] = bd.get("buildType") or pred.get("buildType")
            s["builder_id"] = builder
            s["resolvedDeps_v1"] = None if rd_v1 is None else len(rd_v1)
            s["materials_v02"] = None if rd_v02 is None else len(rd_v02)
            s["resolvedDeps_sample"] = json.dumps((rd_v1 or [])[:3])[:400]
            # locators the provenance actually names (empty list when the field is absent)
            s["prov_locators"] = [d.get("uri") or d.get("digest") or d.get("name")
                                  for d in (rd_v1 or [])]
        else:
            s["is_provenance"] = False
            # a non-provenance predicate may still carry the package list
            pk = pred.get("packages")
            s["has_packages_key"] = pk is not None
            s["n_packages"] = None if pk is None else len(pk)
            if isinstance(pk, list) and pk:
                s["packages_sample"] = json.dumps(pk[0])[:300]
            # apko image-configuration: the builder's DECLARED package list
            contents = pred.get("contents") or {}
            if isinstance(contents, dict) and contents.get("packages"):
                s["declared_packages"] = list(contents["packages"])
            # SPDX: the INSTALLED closure, as purl locators
            locs = []
            if isinstance(pk, list):
                for pkg in pk:
                    for ref in (pkg.get("externalRefs") or []):
                        if "purl" in (ref.get("referenceType") or ""):
                            locs.append(unquote(ref.get("referenceLocator") or ""))
            if locs:
                s["purl_locators"] = locs
        stmts.append(s)

    rec["statements"] = stmts
    rec["n_statements"] = len(stmts)

    # ---- coverage, per edge, from the locators the statements name -----------------
    def names(stmt_list, key):
        out = []
        for x in stmt_list:
            out.extend(x.get(key) or [])
        return out

    declared = names(stmts, "declared_packages")            # builder-declared, "name=version"
    _apk = [u for u in names(stmts, "purl_locators")
            if u and u.startswith("pkg:apk/")]             # installed apk closure
    _seen, installed = set(), []
    for u in _apk:
        nm = u.split("@")[0].rsplit("/", 1)[-1]
        if nm not in _seen:                                # one entry per package, not per purl
            _seen.add(nm)
            installed.append(u)
    prov = names(stmts, "prov_locators")                    # provenance's resolvedDependencies

    def covered_by(targets, named):
        """Count targets with at least one naming locator (purl form or name@version)."""
        hit = 0
        for t in targets:
            base = t.split("=")[0]
            for u in named:
                ub = u.split("@")[0].split("?")[0]
                if base and (base == ub.rsplit("/", 1)[-1] or base in u):
                    hit += 1
                    break
        return hit

    rec["closure"] = {
        "declared_n": len(declared),
        "installed_n": len(installed),
        "installed_locators_raw_n": len(_apk),
        "provenance_named_n": len(prov),
        "declared_covered_by_provenance": covered_by(declared, prov),
        "installed_covered_by_provenance": covered_by(installed, prov),
        "declared_covered_by_spdx": covered_by(declared, installed),
    }
    n_pk = [s.get("n_packages") for s in stmts if s.get("n_packages")]
    rec["packages_in_any_statement"] = max(n_pk) if n_pk else 0
    rec["status"] = "OK"
    rec["elapsed_s"] = round(time.time() - t0, 1)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=12)
    ap.add_argument("--out", default="snapshot_oci.json")
    a = ap.parse_args()

    t0 = time.time()
    rows = []
    for name in CANDIDATES[: a.images]:
        r = one_image(name)
        rows.append(r)
        print("%-12s %-8s %s" % (name, r["status"],
                                 r["reason"] or "stmts=%d" % r["n_statements"]),
              flush=True)

    ok = [r for r in rows if r["status"] == "OK"]
    prov = [s for r in ok for s in r["statements"] if s.get("is_provenance")]
    other = [s for r in ok for s in r["statements"] if s.get("undecodable") is False
             and not s.get("is_provenance")]
    builders = sorted({(s.get("buildType") or "?") for s in prov})
    builder_ids = sorted({(s.get("builder_id") or "?") for s in prov})
    with_rd = [s for s in prov if (s.get("resolvedDeps_v1") or 0) > 0
               or (s.get("materials_v02") or 0) > 0]

    summary = {
        "frame": {"registry": REG, "tag": "latest", "arch": "amd64",
                  "attestation_tag_scheme": "<sha256-digest>.att",
                  "enumeration_rule": "%d named images, latest amd64 image, every DSSE "
                                      "envelope in its .att manifest" % len(CANDIDATES[:a.images]),
                  "candidates": CANDIDATES[: a.images]},
        "images": len(rows),
        "images_ok": len(ok),
        "images_not_run": len(rows) - len(ok),
        "not_run_detail": [{"image": r["image"], "reason": r["reason"]}
                           for r in rows if r["status"] != "OK"],
        "statements": sum(r["n_statements"] for r in ok),
        "provenance_statements": len(prov),
        "provenance_with_positive_resolvedDependencies": len(with_rd),
        "non_provenance_statements": len(other),
        "non_provenance_with_packages": len([s for s in other if (s.get("n_packages") or 0) > 0]),
        "build_types": builders,
        "builder_ids": builder_ids,
        "elapsed_s": round(time.time() - t0, 1),
    }
    out = {"retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "summary": summary, "rows": rows}
    blob = json.dumps(out, indent=1, sort_keys=True)
    open(a.out, "w").write(blob + "\n")
    open(a.out + ".sha256", "w").write(
        hashlib.sha256(blob.encode()).hexdigest() + "  " + a.out + "\n")
    print("\n" + json.dumps(summary, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
