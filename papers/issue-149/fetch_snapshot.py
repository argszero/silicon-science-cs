#!/usr/bin/env python3
"""fetch_snapshot.py -- issue #149: pin the registries' state that every number is computed from.

WHY THIS EXISTS.  The study asks what a declaration leaves open AS OF THE INSTANT IT WAS PUBLISHED,
which means the number depends on the registry's state at a past time.  A rate computed by querying
the live registry cannot be re-run: registries publish continuously, so the same script returns a
different number tomorrow and the paper's first digit is unreproducible.  So the state is fetched
ONCE and committed, and every number is derived from that artifact by a script that touches no
network at all.

THE FRAME, stated as a rule and not as convenience.  Declaring versions are:
  * the 5 most recently published releases of each named seed, and
  * the 2 most recently published releases of each package those seeds declare.
That is "the declarations of the seed set, and of everything they declare" -- a generative rule over
a named seed list, whose every member is reproducible by re-running this file.

WHAT IS RECORDED PER PACKAGE, and why each field is needed:
  * publish time per version  -> the admissible set AS OF a past instant, and the monotonicity test;
  * declared ranges per version -> the declarations under study, and the closure-difference measure;
  * yanked / prerelease flags -> the monotonicity lemma's own exception, counted not assumed away.

Usage: python3 fetch_snapshot.py npm|pypi [--out ../snapshot_<eco>.json]
Network is needed HERE and nowhere else.  Cache under research/raw/ makes a re-run resume.
"""
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
PKG = os.path.abspath(os.path.join(HERE, os.pardir))
UA = {"User-Agent": "silicon-science-cs/issue-149 (research; reproducible snapshot)"}

# The named seeds.  Chosen for ubiquity in their ecosystem and for spanning application, tooling and
# data/ML roles, so the closure is not one kind of package.  A seed list is a CHOICE and is stated as
# one: the study's claim is about the shape of declarations, and a different seed list is a different
# sample of the same population, not a different population.
SEEDS_NPM = ["express", "react", "webpack", "eslint", "jest", "axios"]
SEEDS_PYPI = ["requests", "flask", "django", "pandas", "pytest", "numpy"]

SEED_VERSIONS = 5      # declaring versions taken from each seed
DEP_VERSIONS = 6       # declaring versions taken from each package a seed declares
MAX_DEPTH1 = 120       # guard: never follow more than this many declared packages


def cached(key, fetch):
    """One network read per key, ever.  The cache is what makes a killed run resumable."""
    if not os.path.isdir(RAW):
        os.makedirs(RAW)
    path = os.path.join(RAW, re.sub(r"[^A-Za-z0-9_.-]", "_", key)[:180] + ".json")
    if os.path.exists(path):
        try:
            return json.loads(io.open(path, encoding="utf-8").read()), True
        except ValueError:
            os.remove(path)
    d = fetch()
    io.open(path, "w", encoding="utf-8").write(json.dumps(d))
    return d, False


def get_json(url, accept=None, tries=3):
    h = dict(UA)
    if accept:
        h["Accept"] = accept
    last = None
    for i in range(tries):
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(url, headers=h), timeout=90).read())
        except Exception as e:            # 429 / 5xx / timeout: back off, then give up naming it
            last = e
            time.sleep(2 + 3 * i)
    raise RuntimeError("fetch failed %s: %s" % (url, last))


# ---------------------------------------------------------------- version forms

_PRERELEASE = re.compile(r"[-+](alpha|beta|rc|dev|pre|preview|next|canary|snapshot|a|b)\b|[-+]\d",
                         re.I)


def vtuple(s):
    """(major, minor, patch) from a version string, or None.  The numeric prefix is the contract
    both ecosystems share; anything the prefix does not carry is recorded as a prerelease flag."""
    m = re.match(r"^\s*[vV]?(\d+)(?:\.(\d+))?(?:\.(\d+))?", s or "")
    if not m:
        return None
    return tuple(int(x) if x is not None else 0 for x in m.groups())


def is_prerelease(s):
    return bool(_PRERELEASE.search(s or ""))


def parse_spec(spec, pep440=False):
    """A range spec -> list of alternatives, each a list of (op, tuple).  None if not understood.

    An unparsed form is NOT guessed at: the caller counts it and reports it, because a guess here
    silently changes the admissible set, which is the study's dependent variable.
    """
    s = (spec or "").strip()
    if not s:
        return None
    low = s.lower()
    for bad in ("npm:", "file:", "git", "http", "workspace:", "link:", "portal:", "patch:",
                "catalog:", "github:"):
        if low.startswith(bad):
            return None
    if s in ("*", "x", "X", "latest", ""):
        return None
    alts = []
    for part in s.split("||"):
        part = part.strip().replace(",", " ") if pep440 else part.strip()
        toks = [t for t in re.split(r"[\s]+", part) if t]
        cons = []
        for tok in toks:
            m = re.match(r"^(\^|~=|~|>=|<=|==|=|>|<)?\s*[vV]?(\d+(?:\.\d+){0,2})(?:\.\*)?$", tok)
            if not m:
                return None
            op = m.group(1) or "="
            v = vtuple(m.group(2))
            if v is None:
                return None
            if op == "~=":                      # PEP 440 compatible release
                cons.append((">=", v))
                cons.append(("<", (v[0], v[1] + 1, 0) if v[1] is not None else (v[0] + 1, 0, 0)))
            elif op == "^":                     # semver: leftmost nonzero field may not change
                if v[0] > 0:
                    cons.append((">=", v))
                    cons.append(("<", (v[0] + 1, 0, 0)))
                elif v[1] > 0:
                    cons.append((">=", v))
                    cons.append(("<", (0, v[1] + 1, 0)))
                else:
                    cons.append((">=", v))
                    cons.append(("<", (0, 0, v[2] + 1)))
            elif op == "~":
                cons.append((">=", v))
                cons.append(("<", (v[0], v[1] + 1, 0)))
            else:
                cons.append((op, v))
        alts.append(cons)
    return alts or None


def satisfies(version, alts):
    v = vtuple(version)
    if v is None:
        return False
    for cons in alts:
        ok = True
        for op, bound in cons:
            if op == "=" and v != bound:
                ok = False
            elif op == ">=" and v < bound:
                ok = False
            elif op == "<=" and v > bound:
                ok = False
            elif op == ">" and v <= bound:
                ok = False
            elif op == "<" and v >= bound:
                ok = False
            elif op == "!=" and v == bound:
                ok = False
            if not ok:
                break
        if ok:
            return True
    return False


# ---------------------------------------------------------------- npm

def npm_packument(name):
    return cached("npm_" + name, lambda: get_json("https://registry.npmjs.org/" +
                                                  urllib.parse.quote(name, safe="")))


def npm_package(name):
    """One package's population of versions: time, declared ranges, flags."""
    d, was_cached = npm_packument(name)
    times = d.get("time") or {}
    out = {}
    for v, meta in (d.get("versions") or {}).items():
        t = times.get(v)
        if not t:
            continue
        deps = meta.get("dependencies") or {}
        out[v] = {"published_at": t,
                  "deps": dict((k, v2 if isinstance(v2, str) else "") for k, v2 in deps.items()),
                  "prerelease": is_prerelease(v),
                  "yanked": bool(meta.get("deprecated"))}
    return {"versions": out, "cached": was_cached}


def latest_stable(pkg, k):
    vs = [(m["published_at"], v) for v, m in pkg["versions"].items()
          if not m["prerelease"] and "@" not in v]
    vs.sort()
    return [v for _, v in vs[-k:]]


def build_npm():
    packages, errors = {}, []
    t0 = time.time()
    for seed in SEEDS_NPM:
        try:
            packages[seed] = npm_package(seed)
        except Exception as e:
            errors.append("%s: %s" % (seed, e))
            continue
        print("  seed %-12s %3d versions (%s)  %.0fs"
              % (seed, len(packages[seed]["versions"]),
                 "cache" if packages[seed]["cached"] else "net", time.time() - t0))
    # depth-1: everything the seed declaring-versions declare
    depth1 = set()
    for seed in SEEDS_NPM:
        if seed not in packages:
            continue
        for v in latest_stable(packages[seed], SEED_VERSIONS):
            depth1 |= set(packages[seed]["versions"][v]["deps"])
    depth1 = sorted(depth1)[:MAX_DEPTH1]
    print("  depth-1 declared packages: %d" % len(depth1))
    for i, name in enumerate(depth1):
        try:
            packages[name] = npm_package(name)
        except Exception as e:
            errors.append("%s: %s" % (name, e))
            continue
        if i % 20 == 0:
            print("    %3d/%d %-24s %.0fs" % (i + 1, len(depth1), name[:24], time.time() - t0))
    declaring = []
    for seed in SEEDS_NPM:
        if seed in packages:
            for v in latest_stable(packages[seed], SEED_VERSIONS):
                declaring.append({"package": seed, "version": v, "role": "seed"})
    for name in depth1:
        if name in packages:
            for v in latest_stable(packages[name], DEP_VERSIONS):
                declaring.append({"package": name, "version": v, "role": "declared"})
    return {"ecosystem": "npm", "seeds": SEEDS_NPM, "frame": {
        "seed_versions": SEED_VERSIONS, "dep_versions": DEP_VERSIONS,
        "rule": "5 latest stable releases per seed + 6 latest stable releases per package a seed declares"},
        "declaring": declaring, "packages": packages, "errors": errors}


# ---------------------------------------------------------------- PyPI

def pypi_simple(name):
    """PEP 700 Simple JSON: every file with its upload-time and yanked flag, per version."""
    return cached("pypi_simple_" + name, lambda: get_json(
        "https://pypi.org/simple/%s/" % urllib.parse.quote(name.lower(), safe=""),
        accept="application/vnd.pypi.simple.v1+json"))


def pypi_version_meta(name, version):
    # cached() returns (payload, was_cached); the payload is what the caller wants here.  Returning
    # the pair made every declaration lookup raise "'tuple' object has no attribute 'get'" -- 30
    # errors that named the bug rather than passing silently, which is why the count is printed.
    payload, _ = cached("pypi_%s_%s" % (name, version), lambda: get_json(
        "https://pypi.org/pypi/%s/%s/json" % (urllib.parse.quote(name.lower(), safe=""),
                                              urllib.parse.quote(version, safe=""))))
    return payload


def norm_pypi(name):
    return re.sub(r"[-_.]+", "-", (name or "").strip().lower())


def pypi_package(name):
    """Version population from the Simple API; declarations fetched only for the versions studied."""
    d, was_cached = pypi_simple(name)
    versions = {}
    for f in d.get("files") or []:
        fn, t = f.get("filename") or "", f.get("upload-time")
        if not t or not fn.endswith((".whl", ".tar.gz", ".zip")):
            continue
        m = re.match(r"^(.+?)-(\d[^-]*?)(?:\.tar\.gz|\.zip|-py|\.)"
                     , fn) if fn.endswith((".tar.gz", ".zip")) else \
            re.match(r"^(.+?)-(\d[^-]+)-", fn)
        if not m:
            continue
        ver = m.group(2)
        cur = versions.get(ver)
        if cur is None or t < cur["published_at"]:
            versions[ver] = {"published_at": t, "prerelease": is_prerelease(ver),
                             "yanked": bool(f.get("yanked")), "deps": {}}
    return {"versions": versions, "cached": was_cached}


def pypi_declared(name, version):
    """Runtime requires_dist -> {normalised name: spec}.  Extras and markers are dropped and COUNTED."""
    d = pypi_version_meta(name, version)
    info = d.get("info") or {}
    reqs = info.get("requires_dist") or []
    deps, extra_only, marked = {}, 0, 0
    for r in reqs:
        if ";" in r:
            marked += 1
            if "extra ==" in r.replace("extra==", "extra =="):
                extra_only += 1
                continue
        m = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*(.*)$", r)
        if not m:
            continue
        nm, spec = norm_pypi(m.group(1)), (m.group(3) or "").strip()
        spec = re.sub(r";.*$", "", spec).strip()
        deps[nm] = spec
    return {"deps": deps, "requirements": len(reqs), "marked": marked, "extra_only": extra_only}


def build_pypi():
    packages, errors, meta = {}, [], {}
    t0 = time.time()
    for seed in SEEDS_PYPI:
        try:
            packages[seed] = pypi_package(seed)
        except Exception as e:
            errors.append("%s: %s" % (seed, e))
            continue
        print("  seed %-10s %3d versions (%s)  %.0fs"
              % (seed, len(packages[seed]["versions"]),
                 "cache" if packages[seed]["cached"] else "net", time.time() - t0))
    declaring = []
    depth1 = set()
    for seed in SEEDS_PYPI:
        if seed not in packages:
            continue
        for v in latest_stable(packages[seed], SEED_VERSIONS):
            try:
                info = pypi_declared(seed, v)
            except Exception as e:
                errors.append("%s==%s: %s" % (seed, v, e))
                continue
            meta["%s==%s" % (seed, v)] = info
            depth1 |= set(info["deps"])
            declaring.append({"package": seed, "version": v, "role": "seed"})
    depth1 = sorted(depth1)[:MAX_DEPTH1]
    print("  depth-1 declared packages: %d" % len(depth1))
    for i, name in enumerate(depth1):
        try:
            packages[name] = pypi_package(name)
        except Exception as e:
            errors.append("%s: %s" % (name, e))
            continue
        for v in latest_stable(packages[name], DEP_VERSIONS):
            try:
                info = pypi_declared(name, v)
            except Exception as e:
                errors.append("%s==%s: %s" % (name, v, e))
                continue
            meta["%s==%s" % (name, v)] = info
            declaring.append({"package": name, "version": v, "role": "declared"})
        if i % 15 == 0:
            print("    %3d/%d %-22s %.0fs" % (i + 1, len(depth1), name[:22], time.time() - t0))
    for key, info in meta.items():
        nm, ver = key.split("==", 1)
        if nm in packages and ver in packages[nm]["versions"]:
            packages[nm]["versions"][ver]["deps"] = info["deps"]
    return {"ecosystem": "pypi", "seeds": SEEDS_PYPI, "frame": {
        "seed_versions": SEED_VERSIONS, "dep_versions": DEP_VERSIONS,
        "rule": "5 latest stable releases per seed + 6 latest stable releases per package a seed declares"},
        "declaring": declaring, "packages": packages, "errors": errors, "requirement_scan": meta}



# ---------------------------------------------------------------- depth 2 (the coupling test)

BUDGET = 200000     # an instance is enumerable only if its product of domains is within this
MAXPKG = 12         # ... and it carries at most this many packages


def depth2_instances(snap, pep440):
    """Which declaring versions have an ENUMERABLE closure, and what depth-2 material each needs.

    The selection rule is stated before the fetch and is a function of SIZE ONLY -- never of the
    outcome -- because a size cap that read the answer would be a cherry-pick.  An instance enters
    the depth-2 test when its product of per-edge domains is <= BUDGET and it names <= MAXPKG
    packages; everything else is COUNTED as intractable, which is the falsifier's F2 limb measured
    rather than argued.
    """
    PK = snap["packages"]
    inst, names, metas = [], set(), set()
    for dv in snap["declaring"]:
        name, ver = dv["package"], dv["version"]
        rec = (PK.get(name) or {}).get("versions", {}).get(ver)
        if not rec:
            continue
        doms = {}
        for dep, spec in (rec.get("deps") or {}).items():
            p = PK.get(dep)
            if not p:
                continue
            alts = parse_spec(spec, pep440=pep440)
            if alts is None:
                continue
            avail = sorted(v for v, m in p["versions"].items()
                           if not m["prerelease"] and not m["yanked"] and satisfies(v, alts))
            if avail:
                doms[dep] = avail
        if not doms:
            continue
        prod = 1
        for a in doms.values():
            prod *= len(a)
        if prod > BUDGET or len(doms) > MAXPKG:
            continue                      # counted as intractable, not silently dropped
        inst.append({"package": name, "version": ver, "edges": doms})
        for dep, avail in doms.items():
            for v in avail:
                if dep not in PK:
                    continue
                vd = (PK[dep]["versions"].get(v) or {}).get("deps") or {}
                for d2 in vd:
                    if d2 not in PK:
                        if pep440:
                            metas.add((d2, v))   # just a name here; the pypi pass re-resolves
                        names.add(d2)
    return inst, sorted(names), sorted(metas)


def extend_npm():
    path = os.path.join(PKG, "snapshot_npm.json")
    snap = json.load(io.open(path, encoding="utf-8"))
    inst, names, _ = depth2_instances(snap, False)
    todo = [n for n in names if n not in snap["packages"]][:300]
    print("  enumerable declaring versions: %d | depth-2 names to fetch: %d" % (len(inst), len(todo)))
    t0 = time.time()
    for i, n in enumerate(todo):
        try:
            snap["packages"][n] = npm_package(n)
        except Exception as e:
            snap["errors"].append("%s: %s" % (n, e))
        if i % 20 == 0:
            print("    %3d/%d %-26s %.0fs" % (i + 1, len(todo), n[:26], time.time() - t0))
    return snap, path


def extend_pypi():
    path = os.path.join(PKG, "snapshot_pypi.json")
    snap = json.load(io.open(path, encoding="utf-8"))
    inst, names, _ = depth2_instances(snap, True)
    PK = snap["packages"]
    todo = [n for n in names if n not in PK][:300]
    print("  enumerable declaring versions: %d | depth-2 packages to add: %d"
          % (len(inst), len(todo)))
    t0 = time.time()
    for i, n in enumerate(todo):
        try:
            PK[n] = pypi_package(n)
        except Exception as e:
            snap["errors"].append("%s: %s" % (n, e))
        if i % 10 == 0:
            print("    %3d/%d %-22s %.0fs" % (i + 1, len(todo), n[:22], time.time() - t0))
    # the alternatives' own declarations, which is what makes coupling exist at all
    wanted = {}
    for it in inst:
        for dep, avail in it["edges"].items():
            if dep not in PK:
                continue
            for v in avail:
                if (PK[dep]["versions"].get(v) or {}).get("deps") in (None, {}):
                    wanted["%s==%s" % (dep, v)] = (dep, v)
    print("  alternative-version declarations to fetch: %d" % len(wanted))
    for i, key in enumerate(sorted(wanted)):
        dep, v = wanted[key]
        try:
            info = pypi_declared(dep, v)
        except Exception as e:
            snap["errors"].append("%s: %s" % (key, e))
            continue
        snap.setdefault("requirement_scan", {})[key] = info
        if v in PK.get(dep, {}).get("versions", {}):
            PK[dep]["versions"][v]["deps"] = info["deps"]
        if i % 25 == 0:
            print("    %3d/%d %-26s %.0fs" % (i + 1, len(wanted), key[:26], time.time() - t0))
    return snap, path


def reseal(snap, path):
    """Recompute the content hash over what the numbers are computed from -- no wall clock."""
    body = json.dumps({k: snap[k] for k in ("ecosystem", "frame", "declaring")},
                      sort_keys=True, ensure_ascii=False)
    pkgs = json.dumps({n: {"versions": {v: {"t": m["published_at"], "d": m["deps"],
                                             "p": m["prerelease"], "y": m["yanked"]}
                                       for v, m in p["versions"].items()}}
                       for n, p in snap["packages"].items()},
                      sort_keys=True, ensure_ascii=False)
    snap["content_sha256"] = hashlib.sha256((body + pkgs).encode("utf-8")).hexdigest()
    snap["packages_count"] = len(snap["packages"])
    snap["declaring_count"] = len(snap["declaring"])
    io.open(path, "w", encoding="utf-8").write(json.dumps(snap, indent=1, sort_keys=True) + "\n")
    print("resealed %s | packages %d | errors %d | content_sha256 %s"
          % (path, snap["packages_count"], len(snap["errors"]), snap["content_sha256"][:32]))



# ---------------------------------------------------------------- the decay panel (P2)

PANEL_PER_PKG = 5          # declaring versions taken per package for the longitudinal panel
PANEL_MIN_AGE_DAYS = 365   # a panel declaration must have at least 12 months of observable history


def _day(ts):
    """A date as an integer day number, from an ISO-8601 stamp.  No clock, no timezone library."""
    y, mo, d = int(ts[0:4]), int(ts[5:7]), int(ts[8:10])
    # days since an arbitrary epoch: 400-year cycles make this exact
    yy = y - (1 if mo <= 2 else 0)
    era = (yy if yy >= 0 else yy - 399) // 400
    yoe = yy - era * 400
    doy = (153 * (mo + (-3 if mo > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe


def panel_rule(snap):
    """The panel's selection rule, STATED and time-only -- never selected by outcome.

    For each package in the snapshot: up to PANEL_PER_PKG stable versions published at least
    PANEL_MIN_AGE_DAYS before the snapshot's last instant, most recent first.  The age floor is what
    makes a full 12-month window observable for every member; the per-package cap is what bounds the
    fetch.  A package whose releases are all younger than the floor contributes nothing and is COUNTED.
    """
    PK = snap["packages"]
    now = max(m["published_at"] for p in PK.values() for m in p["versions"].values())
    now_day = _day(now)
    picked, too_young = [], 0
    for name, p in sorted(PK.items()):
        cands = [(m["published_at"], v) for v, m in p["versions"].items()
                 if not m["prerelease"] and not m["yanked"]]
        cands.sort(reverse=True)
        old = [(t, v) for (t, v) in cands if now_day - _day(t) >= PANEL_MIN_AGE_DAYS]
        if not old:
            too_young += 1
            continue
        for t, v in old[:PANEL_PER_PKG]:
            picked.append({"package": name, "version": v, "role": "panel", "published_at": t})
    return picked, too_young, now


def extend_panel(eco):
    path = os.path.join(PKG, "snapshot_%s.json" % eco)
    snap = json.load(io.open(path, encoding="utf-8"))
    picked, too_young, now = panel_rule(snap)
    print("  panel cohort: %d declaring versions from %d package(s); %d package(s) too young, "
          "counted and excluded" % (len(picked), len(set(x["package"] for x in picked)), too_young))
    if eco == "pypi":
        want = [x for x in picked
                if not ((snap["packages"].get(x["package"], {}).get("versions", {})
                         .get(x["version"]) or {}).get("deps"))]
        print("  pypi: declarations needing a metadata fetch: %d" % len(want))
        t0 = time.time()
        for i, x in enumerate(want):
            try:
                info = pypi_declared(x["package"], x["version"])
            except Exception as e:
                snap["errors"].append("%s==%s: %s" % (x["package"], x["version"], e))
                continue
            snap.setdefault("requirement_scan", {})["%s==%s" % (x["package"], x["version"])] = info
            snap["packages"][x["package"]]["versions"][x["version"]]["deps"] = info["deps"]
            if i % 25 == 0:
                print("    %3d/%d %s==%s %.0fs" % (i + 1, len(want), x["package"],
                                                   x["version"], time.time() - t0))
    # the panel is ADDITIVE: the depth-1/depth-2 declaring set is untouched, so their numbers stay put
    have = set((d["package"], d["version"]) for d in snap["declaring"])
    added = [x for x in picked if (x["package"], x["version"]) not in have]
    snap["declaring"].extend(added)
    snap["panel"] = {"rule": "%d most recent stable versions per package at least %d days old"
                             % (PANEL_PER_PKG, PANEL_MIN_AGE_DAYS),
                     "added": len(added), "packages_too_young": too_young, "as_of": now}
    reseal(snap, path)
    print("  panel additions: %d (declaring set now %d)" % (len(added), len(snap["declaring"])))


def main():
    eco = sys.argv[1] if len(sys.argv) > 1 else ""
    if eco == "--panel":
        for which in ("npm", "pypi"):
            print("building the decay panel for %s ..." % which)
            extend_panel(which)
        return 0
    if eco == "--depth2":
        for which in ("npm", "pypi"):
            print("extending %s to depth 2 ..." % which)
            snap, path = (extend_npm() if which == "npm" else extend_pypi())
            reseal(snap, path)
        return 0
    if eco not in ("npm", "pypi"):
        print("usage: fetch_snapshot.py npm|pypi|--depth2")
        return 2
    out = os.path.join(PKG, "snapshot_%s.json" % eco)
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    print("fetching %s ..." % eco)
    snap = build_npm() if eco == "npm" else build_pypi()
    # A CONTENT hash over what the numbers are computed from, with no wall clock in it: the same
    # registry state must hash the same on a re-run, or the pin certifies nothing.
    body = json.dumps({k: snap[k] for k in ("ecosystem", "frame", "declaring")},
                      sort_keys=True, ensure_ascii=False)
    pkgs = json.dumps({n: {"versions": {v: {"t": m["published_at"], "d": m["deps"],
                                             "p": m["prerelease"], "y": m["yanked"]}
                                       for v, m in p["versions"].items()}}
                       for n, p in snap["packages"].items()},
                      sort_keys=True, ensure_ascii=False)
    snap["content_sha256"] = hashlib.sha256((body + pkgs).encode("utf-8")).hexdigest()
    snap["packages_count"] = len(snap["packages"])
    snap["declaring_count"] = len(snap["declaring"])
    io.open(out, "w", encoding="utf-8").write(json.dumps(snap, indent=1, sort_keys=True) + "\n")
    print("wrote %s" % out)
    print("  packages %d | declaring versions %d | errors %d"
          % (snap["packages_count"], snap["declaring_count"], len(snap["errors"])))
    print("  content_sha256 %s" % snap["content_sha256"][:32])
    for e in snap["errors"][:10]:
        print("    ! %s" % e[:100])
    return 0


if __name__ == "__main__":
    sys.exit(main())
