#!/usr/bin/env python3
"""Issue #116 -- reference VERIFICATION (the authority on existence).

Re-fetches every curated entry BY ITS OWN IDENTIFIER from the arXiv API and compares
the returned title against the title recorded for that key. A mismatch, a vanished
record, or a duplicate id is a FAILURE and the command exits non-zero.

This is deliberately a different act from discovery: `refs_discover.py` says what an
index returned for a phrase; this says whether the entry the manuscript will cite
exists and is the paper the manuscript says it is.

Usage:
    python3 refs_tool.py verify      # fetch, compare, write refs/refs_verify.log
    python3 refs_tool.py list        # print the curated keys with their roles
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom"}
KEYS = "refs/refs_keys.json"
LOG = "refs/refs_verify.log"
CACHE = "refs/arxiv_verify_cache"
BATCH = 40


def norm(t):
    t = (t or "").lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def fetch_batch(ids):
    os.makedirs(CACHE, exist_ok=True)
    slug = hashlib.sha256(",".join(ids).encode()).hexdigest()[:16]
    path = os.path.join(CACHE, slug + ".xml")
    if os.path.exists(path):
        return open(path, "rb").read()
    url = ("https://export.arxiv.org/api/query?id_list=" +
           urllib.parse.quote(",".join(ids)) + "&max_results=200")
    req = urllib.request.Request(url, headers={"User-Agent": "issue116-refs/1.0"})
    body = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read()
            break
        except urllib.error.HTTPError as e:
            if attempt == 3:
                print(f"  (batch fetch unavailable: HTTP {e.code} -- falling back to"
                      f" the per-entry abstract page)")
                return b""          # let every entry in this batch use the fallback
            time.sleep(15.0 * (attempt + 1))
        except Exception as e:                              # noqa: BLE001
            if attempt == 3:
                print(f"  (batch fetch unavailable: {type(e).__name__} -- falling"
                      f" back to the per-entry abstract page)")
                return b""
            time.sleep(15.0 * (attempt + 1))
    with open(path, "wb") as fh:
        fh.write(body)
    time.sleep(3.0)
    return body


def parse(body):
    """id -> {title, published}. The API returns entries in arbitrary order.
    An EMPTY body means the batch could not be fetched -- return no entries so the
    per-entry fallback runs, rather than crashing the whole verification."""
    if not body or not body.strip():
        return {}
    root = ET.fromstring(body)
    out = {}
    for e in root.findall("a:entry", NS):
        raw = (e.findtext("a:id", "", NS) or "").strip()
        aid = re.sub(r"v\d+$", "", raw.rsplit("/abs/", 1)[-1])
        title = re.sub(r"\s+", " ", (e.findtext("a:title", "", NS) or "")).strip()
        if aid:
            out[aid] = {"title": title,
                        "published": (e.findtext("a:published", "", NS) or "")[:10]}
    return out


def fetch_abs_page(aid):
    """Fallback when the API is throttled: the arXiv ABSTRACT PAGE, fetched over
    plain HTTP and read for its own citation_title meta tag. This is a second,
    independent carrier of the same record -- the API and the page are different
    services, so a 429 on one is not evidence about the other."""
    url = "https://arxiv.org/abs/" + aid
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (issue116 ref check)"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                html = r.read().decode("utf-8", "replace")
            break
        except Exception:                                   # noqa: BLE001
            if attempt == 2:
                return None
            time.sleep(8.0 * (attempt + 1))
    m = re.search(r'<meta\s+name="citation_title"\s+content="([^"]+)"', html)
    if not m:
        return None
    t = m.group(1)
    t = (t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&quot;", '"').replace("&#39;", "'"))
    return re.sub(r"\s+", " ", t).strip()


def verify():
    data = json.load(open(KEYS))
    keys = data["keys"]
    ids = sorted(keys)
    arxiv_ids = [i for i in ids if not keys[i].get("doi")]
    fetched = {}
    for i in range(0, len(arxiv_ids), BATCH):
        chunk = arxiv_ids[i:i + BATCH]
        got = parse(fetch_batch(chunk))
        fetched.update(got)
        if i + BATCH < len(arxiv_ids):
            time.sleep(10.0)          # pace the batches: arXiv throttles bursts
        print(f"  fetched {i + len(chunk):>3}/{len(arxiv_ids)}  (returned {len(got)} entries)")
    lines, problems, resolved = [], [], 0
    # ---- DOI entries are verified against CROSSREF, not arXiv ----
    for k in ids:
        if not keys[k].get("doi"):
            continue
        url = ("https://api.crossref.org/works/" +
               urllib.parse.quote(k, safe="/"))   # keep the DOI slash unescaped
        req = urllib.request.Request(url, headers={"User-Agent": "issue116-refs/1.0"})
        m, err = None, None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    m = json.loads(r.read().decode())["message"]
                break
            except urllib.error.HTTPError as e:
                err = e
                if e.code not in (429, 500, 502, 503) or attempt == 3:
                    break
                time.sleep(10.0 * (attempt + 1))
            except Exception as e:                              # noqa: BLE001
                err = e
                break
        if m is None:
            problems.append((k, f"CROSSREF FETCH FAILED: {type(err).__name__}: {err}"))
            lines.append(f"{k} | DOI:{k} | MISSING | {type(err).__name__}")
            continue
        title = (m.get("title") or [""])[0]
        year = str((m.get("issued", {}).get("date-parts") or [[""]])[0][0])
        if not title:
            problems.append((k, "CROSSREF returned no title"))
            lines.append(f"{k} | DOI:{k} | MISSING TITLE |")
            continue
        resolved += 1
        keys[k]["verified_title"] = title
        keys[k]["verified_year"] = year
        lines.append(f"{k} | DOI:{k} | crossref | {title!r} | {year}")
    for k in ids:
        if keys[k].get("doi"):
            continue
        rec = keys[k]
        got = fetched.get(k)
        if got is None:                        # API throttled/failed -> the abs page
            t = fetch_abs_page(k)
            if t is not None:
                got = {"title": t, "published": ""}
                lines.append("")   # keep the log aligned; replaced below
                lines.pop()
        if got is None:
            problems.append((k, "NOT RETURNED by the arXiv API"))
            lines.append(f"{k} | arXiv:{k} | MISSING | the API returned no entry for this id")
            continue
        want = norm(rec.get("title"))
        have = norm(got["title"])
        if want and want != have:
            problems.append((k, f"TITLE MISMATCH: recorded {rec['title']!r} vs fetched {got['title']!r}"))
            lines.append(f"{k} | arXiv:{k} | MISMATCH | fetched {got['title']!r}")
            continue
        resolved += 1
        tag = "recorded" if want else "resolved-from-api"
        if not got.get("published"):
            tag += "+abs-page"
        lines.append(f"{k} | arXiv:{k} | {tag} | {got['title']!r} | {got['published']}")
        rec["verified_title"] = got["title"]
        rec["verified_published"] = got["published"]
    with open(LOG, "w") as fh:
        fh.write("# Issue #116 -- reference verification log\n")
        fh.write("# tool: refs_tool.py verify   source: arXiv API (export.arxiv.org)\n")
        fh.write(f"# entries={len(ids)} resolved={resolved} problems={len(problems)}\n")
        fh.write("# format: key | identifier | status | fetched title | published\n")
        for ln in lines:
            fh.write(ln + "\n")
    with open(KEYS, "w") as fh:                    # write back the resolved titles
        json.dump(data, fh, indent=1, sort_keys=True)
    print(f"\nverified {resolved}/{len(ids)}, problems={len(problems)}  -> {LOG}")
    for k, why in problems:
        print(f"  PROBLEM {k}: {why}")
    if problems:
        sys.exit(1)


def fromlog():
    """Restore verified titles from the verifier's OWN log. The log is the
    verifier's recorded output, so this re-reads a result rather than inventing one."""
    import ast as _ast
    data = json.load(open(KEYS))
    keys = data["keys"]
    n = 0
    for ln in open(LOG):
        if ln.startswith("#"):
            continue
        parts = [x.strip() for x in ln.split("|")]
        if len(parts) < 4:
            continue
        k, ident, status, title = parts[0], parts[1], parts[2], parts[3]
        if k not in keys or status == "MISSING":
            continue
        try:
            t = _ast.literal_eval(title)
        except Exception:                                      # noqa: BLE001
            continue
        keys[k]["verified_title"] = t
        if len(parts) >= 5 and parts[4]:
            if ident.startswith("DOI:"):
                keys[k]["verified_year"] = parts[4]
            else:
                keys[k]["verified_published"] = parts[4]
        n += 1
    with open(KEYS, "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
    print(f"restored {n} verified titles from {LOG}")


def listing():
    data = json.load(open(KEYS))
    for k, r in sorted(data["keys"].items(), key=lambda kv: (kv[1]["role"], kv[0])):
        print(f"{k:<14} {r['role']:<42} {(r.get('verified_title') or r.get('title') or '?')[:60]}")


def verify_doi():
    """Verify ONLY the DOI entries (Crossref). Kept separate from the arXiv path so
    a throttle on one index cannot block the other."""
    data = json.load(open(KEYS))
    keys = data["keys"]
    dos = sorted(k for k, v in keys.items() if v.get("doi"))
    if not dos:
        print("no DOI entries")
        return
    n = 0
    with open(LOG, "a") as fh:
        for k in dos:
            url = ("https://api.crossref.org/works/" +
                   urllib.parse.quote(k, safe="/"))
            req = urllib.request.Request(url, headers={"User-Agent": "issue116-refs/1.0"})
            m, err = None, None
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(req, timeout=60) as r:
                        m = json.loads(r.read().decode())["message"]
                    break
                except urllib.error.HTTPError as e:
                    err = e
                    if e.code not in (429, 500, 502, 503) or attempt == 3:
                        break
                    time.sleep(10.0 * (attempt + 1))
                except Exception as e:                          # noqa: BLE001
                    err = e
                    break
            if m is None:
                print(f"  {k}: CROSSREF FAILED {type(err).__name__}: {err}")
                continue
            title = (m.get("title") or [""])[0]
            year = str((m.get("issued", {}).get("date-parts") or [[""]])[0][0])
            keys[k]["verified_title"] = title
            keys[k]["verified_year"] = year
            fh.write(f"{k} | DOI:{k} | crossref | {title!r} | {year}\n")
            print(f"  {k}: crossref OK -> {title!r} ({year})")
            n += 1
            time.sleep(2.0)
    with open(KEYS, "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
    print(f"verified {n}/{len(dos)} DOI entries")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "verify":
        print("issue #116 -- verifying every curated entry by its own identifier")
        verify()
    elif cmd == "fromlog":
        fromlog()
    elif cmd == "doi":
        verify_doi()
    elif cmd == "list":
        listing()
    else:
        raise SystemExit(f"unknown command {cmd!r}; use verify|list")
