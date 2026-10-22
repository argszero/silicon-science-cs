#!/usr/bin/env python3
"""Input-coverage instrument for issue #145.

The construct
-------------
A release has a **declared dependency closure**: the dependency names its manifest
declares. Its **provenance statement** names *inputs* (in-toto `subject` +
SLSA v1 `buildDefinition.resolvedDependencies`, or SLSA v0.2 `materials`).

    input coverage  c = |{declared dependencies that some named input identifies}|
                        -------------------------------------------------------
                                   |declared dependencies|

The whole construct turns on one distinction that is easy to lose in a string
match: **the build's source-repository URI is an input, and it is not a closure
member.**  A statement that says "built from git+https://github.com/x/y@refs/heads/main"
has named its source, not its dependencies.  So identity of an input is decided by
a *parser* for the two forms that actually identify a package (a purl, or a
registry tarball URL), never by substring containment anywhere in the URI.

Reporting rules that are part of the construct, not of the formatting:
  * a release with **no** declared dependencies has `c = None` (n/a), never 0.0 —
    "the closure is empty" and "nothing in the closure is covered" are different
    facts and must not share a cell;
  * a release with **no** attestation has `c = None` and `attested = False` — the
    coverage question is not asked of it, and it is not counted as zero coverage.

Everything here is a pure function of (statement, dependency list); the fetching
lives in `probe_coverage.py` / `enumerate.py`.
"""
import base64
import json
import re
import urllib.parse

NPM_PURL_PREFIXES = ("pkg:npm/", "pkg:npm%2f")
NPM_REGISTRY_HOSTS = ("registry.npmjs.org",)

_PURL_RE = re.compile(r"^pkg:(?P<type>[a-z0-9.+-]+)/(?P<rest>.+)$", re.I)


def parse_purl(uri):
    """('npm', 'name-or-@scope/name') for a purl naming a package, else None.

    A purl with a version qualifier is normalised to the name; qualifiers and
    subpaths are dropped.  The name is percent-decoded, because the canonical
    form of a scoped purl encodes `@` and `/`.
    """
    m = _PURL_RE.match(uri.strip())
    if not m:
        return None
    ptype = m.group("type").lower()
    rest = urllib.parse.unquote(m.group("rest"))
    rest = rest.split("#", 1)[0].split("?", 1)[0]          # drop subpath + qualifiers
    # a version separator is an '@' that is not the scoped-name marker at index 0
    at = rest.rfind("@")
    if at > 0:
        rest = rest[:at]
    rest = rest.strip("/")
    if not rest:
        return None
    return (ptype, rest.lower())


def parse_npm_tarball(uri):
    """Package name for an npm registry tarball URL, else None.

    `https://registry.npmjs.org/<name>/-/<name>-<version>.tgz` and the scoped
    form `https://registry.npmjs.org/@scope/<name>/-/<name>-<ver>.tgz`.
    """
    try:
        p = urllib.parse.urlsplit(uri.strip())
    except ValueError:
        return None
    if p.scheme not in ("http", "https") or p.hostname not in NPM_REGISTRY_HOSTS:
        return None
    parts = [urllib.parse.unquote(x) for x in p.path.strip("/").split("/")]
    if "-" not in parts:
        return None
    idx = parts.index("-")
    head = parts[:idx]
    if not head:
        return None
    return "/".join(head).lower()


def identified_package(uri, ecosystem="npm"):
    """The package an input URI identifies *as a package*, or None.

    None is the important return: a source-repository URI, a container image, a
    build-configuration URI and an unparseable string all identify no package,
    and therefore cover no closure member.
    """
    if ecosystem == "npm":
        q = parse_purl(uri)
        if q and q[0] == "npm":
            return q[1]
        name = parse_npm_tarball(uri)
        if name:
            return name
    return None


def coverage(deps, input_uris, ecosystem="npm"):
    """(n_covered, n_deps, c) with c None when the closure is empty.

    `deps` are declared dependency *names*; `input_uris` are the named inputs of
    the release's provenance statement.  Both are sets of identities, so the
    arithmetic is set intersection — no estimation, no sampling, no proxy.
    """
    dset = {d.strip().lower() for d in deps if d and d.strip()}
    covered = set()
    for u in input_uris:
        pkg = identified_package(u, ecosystem=ecosystem)
        if pkg and pkg in dset:
            covered.add(pkg)
    n, m = len(covered), len(dset)
    return (n, m, (n / m) if m else None)


def decode_statements(bundle):
    """Decode every DSSE envelope in an npm/PyPI attestation bundle.

    A payload that does not decode is reported in `undecodable` rather than
    silently dropped: an instrument that hides a decode failure reports a
    smaller input set and a *lower* coverage, which is the direction that would
    make its own claim look stronger.
    """
    out, bad = [], 0
    for att in bundle.get("attestations", []) or []:
        b = att.get("bundle") or {}
        env = b.get("dsseEnvelope") or {}
        payload = env.get("payload")
        if not payload:
            bad += 1
            continue
        try:
            st = json.loads(base64.b64decode(payload))
        except Exception:
            bad += 1
            continue
        out.append({
            "predicateType": att.get("predicateType"),
            "statement": st,
            "certificate": bool((b.get("verificationMaterial") or {}).get("certificate")),
        })
    return out, bad


def attested_inputs(statements):
    """Named inputs of the build, as URIs.

    SLSA v1: `predicate.buildDefinition.resolvedDependencies[].uri`.
    SLSA v0.2: `predicate.materials[].uri`.
    The in-toto `subject` is the *output* and is deliberately not read here: a
    subject is the artifact being signed, not an input to its build.
    """
    uris = []
    for s in statements:
        pred = (s["statement"].get("predicate") or {})
        bd = pred.get("buildDefinition") or {}
        for m in bd.get("resolvedDependencies") or []:
            if m.get("uri"):
                uris.append(m["uri"])
        for m in pred.get("materials") or []:
            if m.get("uri"):
                uris.append(m["uri"])
    return uris


def build_type(statements):
    for s in statements:
        bd = ((s["statement"].get("predicate") or {}).get("buildDefinition") or {})
        if bd.get("buildType"):
            return bd["buildType"]
    return None


def oidc_issuer(bundle):
    """The OIDC issuer of the signing certificate, if the bundle carries one.

    Read from the certificate's SAN extension in unverified form: the issuer's
    host is the last DNS name / the URI in the SAN list.  This is an identity
    label for grouping, not an authenticated claim — the paper never treats it
    as evidence that a build happened where it says.
    """
    for att in bundle.get("attestations", []) or []:
        vm = (att.get("bundle") or {}).get("verificationMaterial") or {}
        cert = vm.get("certificate") or {}
        raw = cert.get("rawBytes")
        if not raw:
            continue
        try:
            der = base64.b64decode(raw)
        except Exception:
            continue
        uris = re.findall(rb"https?://[A-Za-z0-9./_%+-]+", der)
        for u in uris:
            h = urllib.parse.urlsplit(u.decode("ascii", "ignore")).hostname
            if h:
                return h
    return None
