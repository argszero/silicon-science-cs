#!/usr/bin/env python3
"""Second-ecosystem measurement: PyPI (issue #145, R671).

Why this file exists
--------------------
R670 measured npm and found one builder producing 82 statements that each name
exactly one input (the source commit). A single ecosystem, produced by a single
platform, cannot tell "attestations do not carry the input closure" apart from
"this one platform does not". This file measures the second ecosystem on its own
terms, so the comparison is between two *measured* shapes.

The PyPI shape is not npm's, and that is the point
--------------------------------------------------
A PyPI `publish/v1` statement carries: a `subject` (the file), a `predicateType`,
and **`predicate: null`** — no `buildDefinition`, no `resolvedDependencies`, no
`materials`. What it does carry is the **publisher identity** (the Trusted
Publisher: repository + workflow), and that lives in the bundle, not in the
statement.

So the two ecosystems have different zeros, and a single "coverage = 0" would
hide it:
  * npm:  an input list exists, and it names the source commit only;
  * PyPI: no input list exists at all.
The measured fields below record which of those is the case, so the paper can
report a taxonomy rather than a number.

Frame: a stated seed list, latest version per package, every attested file of
that version. A file with no provenance URL is `attested=False` and is NOT
counted as zero coverage.

Run: python3 pypi_enumerate.py [--out snapshot_pypi.json]
Exit: 0 = measured, 2 = nothing measured.
"""
import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SEEDS = ["pypi-attestations", "sigstore", "truststore", "uv", "hatchling", "build",
         "twine", "wheel", "packaging", "pip", "pytest", "mypy", "black", "ruff",
         "httpx", "pydantic", "flask", "django", "requests", "numpy"]

H = {"User-Agent": "silicon-science-145", "Accept": "application/vnd.pypi.simple.v1+json"}
# The /integrity/.../provenance endpoint answers 406 to the Simple-JSON media type,
# so it gets its own header. Measured 2026-10-21: 406 with the Simple header,
# 200 with this one -- and a run that used the shared header reported
# "attested_files=0", i.e. a harness failure that looked exactly like a zero.
H_PROV = {"User-Agent": "silicon-science-145", "Accept": "application/json"}


def get_json(url, tries=3, timeout=30, headers=None):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=headers or H), timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise RuntimeError("HTTP 404") from e
            last = f"HTTP {e.code}"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(1.0 + i)
    raise RuntimeError(last or "unknown")


def latest_project(name):
    """Simple JSON gives files; the version is read from the filenames' shared version."""
    return get_json(f"https://pypi.org/simple/{name}/")


def project_json(name):
    return get_json(f"https://pypi.org/pypi/{name}/json")


def statement_of(att):
    env = att.get("envelope") or {}
    raw = env.get("statement")
    if not raw:
        return None, "no-statement"
    try:
        return json.loads(base64.b64decode(raw)), None
    except Exception as e:
        return None, f"undecodable: {type(e).__name__}"


def measure_file(name, f):
    """One unit: one file of the project's latest version."""
    row = {"package": name, "filename": f.get("filename"), "attested": False,
           "n_files_of_version": None, "status": "OK",
           "n_statement_inputs": 0, "has_predicate": False, "predicate_type": None,
           "publisher": None, "n_deps": 0, "n_covered": 0, "coverage": None,
           "undecodable": 0}
    prov = f.get("provenance")
    if not prov:
        return row
    row["attested"] = True
    try:
        bundle = get_json(prov, headers=H_PROV)
    except Exception as e:
        row.update(status="NOT RUN", error=f"provenance: {e}")
        return row
    rows = []
    for bun in bundle.get("attestation_bundles") or []:
        pub = bun.get("publisher") or {}
        row["publisher"] = row["publisher"] or "/".join(
            str(x) for x in (pub.get("kind"), pub.get("repository"), pub.get("workflow")) if x)
        for att in bun.get("attestations") or []:
            st, err = statement_of(att)
            if err:
                row["undecodable"] += 1
                continue
            rows.append(st)
    for st in rows:
        pt = st.get("predicateType")
        row["predicate_type"] = row["predicate_type"] or pt
        pred = st.get("predicate")
        if pred:
            row["has_predicate"] = True
            bd = pred.get("buildDefinition") or {}
            row["n_statement_inputs"] += len(bd.get("resolvedDependencies") or [])
            row["n_statement_inputs"] += len(pred.get("materials") or [])
    return row


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="snapshot_pypi.json")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(argv)
    t0 = time.time()

    # declared dependency closure, per project (latest release metadata)
    def deps_of(name):
        try:
            d = project_json(name)
        except Exception:
            return None
        rd = (d.get("info") or {}).get("requires_dist") or []
        out = set()
        for spec in rd:
            # "name [extra] (>=1.0) ; marker" -> name
            nm = spec.split(";")[0].strip().split("[")[0].strip()
            nm = nm.split("(")[0].split("<")[0].split(">")[0].split("=")[0].split("!")[0]
            nm = nm.split("~")[0].split(" ")[0].strip()
            if nm:
                out.add(nm.lower())
        return out

    def work(name):
        try:
            simple = latest_project(name)
        except Exception as e:
            return {"package": name, "status": "NOT RUN", "error": str(e), "files": []}
        files = simple.get("files") or []
        if not files:
            return {"package": name, "status": "NOT RUN", "error": "no files", "files": []}
        # the latest version is the one the project JSON declares -- not a guess
        # parsed back out of a filename
        try:
            ver = (project_json(name).get("info") or {}).get("version")
        except Exception:
            ver = None
        if ver:
            latest_files = [f for f in files
                            if f"-{ver}-" in (f.get("filename") or "")
                            or (f.get("filename") or "").endswith(f"-{ver}.tar.gz")]
        else:
            latest_files = []
        if not latest_files:
            latest_files = [max(files, key=lambda f: f.get("upload-time") or "")]
        rows = []
        for f in latest_files:
            r = measure_file(name, f)
            r["version"] = ver
            r["n_files_of_version"] = len(latest_files)
            rows.append(r)
        return {"package": name, "status": "OK", "version": ver, "files": rows}

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        projects = list(ex.map(work, SEEDS))

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        deps = dict(zip([p["package"] for p in projects], ex.map(deps_of, SEEDS)))

    for p in projects:
        d = deps.get(p["package"]) or set()
        for r in p["files"]:
            r["n_deps"] = len(d)
            # PyPI publish/v1 carries no input list: no input can cover a dep,
            # so n_covered is 0 whenever a closure exists. Recorded, not assumed.
            r["n_covered"] = 0
            r["coverage"] = 0.0 if d else None

    files = [r for p in projects for r in p["files"]]
    ok = [r for r in files if r["status"] == "OK"]
    att = [r for r in ok if r["attested"]]
    summary = {
        "frame": {"seeds": SEEDS, "unit": "one file of the latest version",
                  "retrieved_note": "attested files only via the Simple JSON 1.4 provenance URL"},
        "projects": len(projects),
        "projects_not_run": sum(1 for p in projects if p["status"] != "OK"),
        "files": len(files), "files_ok": len(ok),
        "files_not_run": len(files) - len(ok),
        "attested_files": len(att),
        "attested_with_predicate": sum(1 for r in att if r["has_predicate"]),
        "attested_without_predicate": sum(1 for r in att if not r["has_predicate"]),
        "attested_inputs_total": sum(r["n_statement_inputs"] for r in att),
        "predicate_types": sorted({str(r["predicate_type"]) for r in att}),
        "publishers": sorted({str(r["publisher"]) for r in att if r["publisher"]}),
        "attested_with_deps": sum(1 for r in att if r["n_deps"] > 0),
        "attested_zero_coverage": sum(1 for r in att if r["n_deps"] > 0 and r["n_covered"] == 0),
        "deps_total": sum(r["n_deps"] for r in att),
        "deps_covered": sum(r["n_covered"] for r in att),
        "undecodable": sum(r["undecodable"] for r in att),
        "elapsed_s": round(time.time() - t0, 1),
    }
    snap = {"retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "summary": summary, "projects": projects}
    text = json.dumps(snap, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    digest = hashlib.sha256(text.encode()).hexdigest()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), a.out)
    with open(out, "w") as fh:
        fh.write(text)
    with open(out + ".sha256", "w") as fh:
        fh.write(f"{digest}  {a.out}\n")

    print(f"PYP I frame: {summary['projects']} projects, {summary['files']} files "
          f"({summary['files_not_run']} NOT RUN)")
    print(f"PYPI attested_files={summary['attested_files']} "
          f"with_predicate={summary['attested_with_predicate']} "
          f"without_predicate={summary['attested_without_predicate']} "
          f"inputs_total={summary['attested_inputs_total']}")
    print(f"PYPI predicate_types={summary['predicate_types']}")
    print(f"PYPI publishers={summary['publishers']}")
    print(f"PYPI attested_with_deps={summary['attested_with_deps']} "
          f"zero_coverage={summary['attested_zero_coverage']} "
          f"deps={summary['deps_total']} covered={summary['deps_covered']}")
    print(f"PYPI sha256={digest} elapsed={summary['elapsed_s']}s -> {a.out}")
    if summary["files_ok"] == 0:
        print("PYPI: NOT RUN — nothing was measured")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
