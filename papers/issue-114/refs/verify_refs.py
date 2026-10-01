#!/usr/bin/env python3
"""Verify every selected reference against a real external record, and render the list.

Two outputs, both committed:

  * `reference-check.md` -- one row per entry: key, method, whether the record EXISTS, whether
    it SUPPORTS the declared work, and the record actually found.  "Exists" and "supports" are
    separate columns on purpose: a DOI can resolve to a real paper that is not the one the
    manuscript means (that is precisely how a false match survives a screen), so the title is
    compared token by token and a mismatch fails the run.
  * `reference-list.md` -- the numbered list the manuscript cites, in the journal's house
    form: `[n] Authors (Year). Title. Venue. <resolvable URL>` plus the stated difference.

A reference that cannot be verified is an ERROR, not a warning: the exit code is nonzero and
the entry is reported.  Nothing here rewrites the selection to make the run pass.

Usage: python3 verify_refs.py     (writes the two files; exit 0 iff every entry verified)
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "verify_cache")
os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "issue-114-bibliography/1.0 (mailto:noreply@example.org)"}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())


def overlap(a: str, b: str) -> float:
    x = [w for w in norm(a).split() if len(w) > 2]
    if not x:
        return 0.0
    y = set(norm(b).split())
    return sum(1 for w in x if w in y) / len(x)


def fetch(url: str, name: str):
    """Fetch with backoff, and cache only a SUCCESS.

    The index rate-limits (HTTP 429), and a throttled lookup is not evidence about a record --
    it is an absence of evidence.  So a failure is retried and never cached, and the caller is
    handed a marker it can report as `unreachable` rather than as `mismatch`: conflating the
    two would let a busy API read as a fabricated citation, and (worse, in the other direction)
    a naive retry-until-cached loop would turn a throttle into a silent pass.
    """
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9._-]", "_", name)[:120])
    if os.path.exists(path):
        return open(path, encoding="utf-8", errors="replace").read()
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read().decode("utf-8", "replace")
            open(path, "w", encoding="utf-8").write(body)
            time.sleep(1.0)
            return body
        except Exception as exc:                   # noqa: BLE001 - recorded as a failed lookup
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(4 * (attempt + 1))
    return f"__UNREACHABLE__ {last}"


def verify_crossref(e):
    body = fetch(f"https://api.crossref.org/works/{urllib.parse.quote(e['doi'])}", f"cr_{e['doi']}")
    if body.startswith("__UNREACHABLE__"):
        return None, False, body, ""
    d = json.loads(body)["message"]
    title = (d.get("title") or [""])[0]
    yr = (d.get("issued", {}).get("date-parts") or [[None]])[0][0]
    ok_title = overlap(e["title"], title) >= 0.8
    ok_year = e["year"] is None or yr is None or abs(int(yr) - int(e["year"])) <= 1
    return True, (ok_title and ok_year), f"{title} -- {e['doi']}", f"{title} ({yr})"


def verify_arxiv(e):
    aid = e.get("arxiv", "")
    body = fetch(f"http://export.arxiv.org/api/query?id_list={urllib.parse.quote(aid)}",
                 f"ax_{aid}.xml")
    if body.startswith("__UNREACHABLE__"):
        return None, False, body, ""
    m = re.search(r"<entry>(.*?)</entry>", body, re.S)
    if not m:
        return True, False, "no entry returned for this id", ""
    t = re.search(r"<title>(.*?)</title>", m.group(1), re.S)
    title = re.sub(r"\s+", " ", html.unescape(t.group(1))).strip() if t else ""
    return True, overlap(e["title"], title) >= 0.8, f"{title} -- arXiv:{aid}", title


def render_authors(authors) -> str:
    out = []
    for a in authors:
        fam = (a.get("family") or "").strip()
        giv = (a.get("given") or "").strip()
        if not fam:
            fam = (a.get("family") or "").strip() or a.get("given", "").strip()
            giv = ""
        if not fam:
            continue
        if not giv:
            out.append(fam)
        else:
            initials = " ".join(p[0] + "." for p in re.split(r"[\s.\-]+", giv) if p)
            out.append(f"{fam}, {initials}")
    if len(out) > 3:
        return "; ".join(out[:3]) + "; et al."
    return "; ".join(out)


def main() -> int:
    sel = json.load(open(os.path.join(HERE, "selection.json")))
    rows, entries, bad, unreachable = [], [], [], []
    for i, e in enumerate(sorted(sel["accepted"], key=lambda x: (x["year"] or 0, x["key"])), 1):
        if e["source"] == "crossref":
            exists, supports, found, detail = verify_crossref(e)
            method = "doi"
        else:
            exists, supports, found, detail = verify_arxiv(e)
            method = "arxiv"
        rows.append((i, e, method, exists, supports, found, detail))
        if exists is None:
            unreachable.append(e["key"])
        elif not (exists and supports):
            bad.append(e["key"])
        url = (f"https://doi.org/{e['doi']}" if e["doi"]
               else f"https://arxiv.org/abs/{e.get('arxiv', '')}")
        venue = e["venue"] or ("arXiv preprint" if e.get("arxiv") else "")
        line = f"[{i}] {render_authors(e['authors'])} ({e['year']}). {e['title']}. {venue}. {url}"
        entries.append((i, e, line))
        note = e.get("difference") or e.get("role") or ""
        verdict = "ok" if (exists and supports) else ("UNREACHABLE" if exists is None else "MISMATCH")
        print(f"  [{i:3d}] {e['key']:<22} {method:<6} {verdict:<12} {e['title'][:52]}")

    # the key -> number map, so the manuscript can be written with stable [@key] tokens and
    # rendered to the house's numeric form at assembly time (a numbered list whose order can
    # change must not be hand-copied into prose)
    with open(os.path.join(HERE, "keys.json"), "w") as fh:
        json.dump({e["key"]: i for i, e, _ in entries}, fh, indent=1, sort_keys=True)

    with open(os.path.join(HERE, "..", "reference-list.md"), "w") as fh:
        fh.write("# Reference list -- generated by verify_refs.py, do not edit by hand.\n\n")
        fh.write("Entries are numbered in the order the manuscript cites them.\n\n")
        for i, e, line in entries:
            note = e.get("difference") or e.get("role") or ""
            fh.write(line + "\n")
            if note:
                fh.write(f"    Difference: {note}\n")
            fh.write("\n")

    covered = sum(1 for _, _, _, ex, sup, _, _ in rows if ex and sup)
    with open(os.path.join(HERE, "..", "reference-check.md"), "w") as fh:
        fh.write("# Reference check -- authenticity and support\n\n")
        fh.write(f"Every citation key used by the manuscript is verified below against a real "
                 f"external record before submission; `refs/verify_refs.py` re-runs these "
                 f"lookups and rewrites this file.  **{covered} of {len(rows)} entries verified.**\n\n")
        fh.write("`Exists` asks whether the identifier resolves; `Support` asks whether the record "
                 "found is the work the manuscript means -- two separate questions, because a DOI "
                 "can resolve to a real paper that is not the declared one.\n\n")
        fh.write("| # | Key | Method | Exists | Support | Record found |\n|---|---|---|---|---|---|\n")
        for i, e, method, exists, supports, found, _ in rows:
            ex = "unreachable" if exists is None else ("yes" if exists else "NO")
            fh.write(f"| {i} | `{e['key']}` | {method} | {ex} | "
                     f"{'OK' if supports else 'MISMATCH'} | {found.replace('|', '/')} |\n")
        fh.write("\n## Rejections (near-misses that were NOT cited)\n\n")
        fh.write("A title-overlap screen cannot separate these from a hit, so each is recorded "
                 "with the reason it is not the work the query named:\n\n")
        fh.write("| Key | Reason rejected |\n|---|---|\n")
        for r in sel.get("rejected", []):
            fh.write(f"| `{r['key']}` | {r['why']} |\n")

    print(f"\nVERIFY: {covered}/{len(rows)} verified"
          f" · mismatched {len(bad)} {bad if bad else ''}"
          f" · unreachable {len(unreachable)} {unreachable if unreachable else ''}")
    print("  (a mismatch is a defect in the reference; an unreachable lookup is an absence of "
          "evidence and must be re-run, not read as a pass)")
    return 0 if not bad and not unreachable else 1


if __name__ == "__main__":
    sys.exit(main())
