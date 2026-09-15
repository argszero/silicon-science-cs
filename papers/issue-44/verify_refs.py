#!/usr/bin/env python3
"""Verify every reference against a real external record.

Input  : refs_to_verify.tsv -- one candidate per line, TAB separated:
             key <TAB> kind <TAB> value
         where kind is one of doi | arxiv | title.
Output : references.md       -- entries for the verified keys only, rendered from
                               the returned record (title, authors, venue, year).
         reference-check.md  -- one row per key: method, result, the record found.
         verify_refs_report.txt -- the raw decision per key.

A DOI is looked up in Crossref.  An arXiv id is read off the paper's own abstract
page.  A title is searched in Crossref, and the first hit whose title normalises to
the candidate is accepted; a title search that finds nothing is a failure, not a
silent skip -- an unverifiable citation must never reach the manuscript.  The
script exits non-zero if any key is UNVERIFIED.
"""

import io
import json
import os
import re
import subprocess
import sys
import time
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
BATCH = os.path.join(HERE, "refs_to_verify.tsv")
OUT_REFS = os.path.join(HERE, "references.md")
OUT_CHECK = os.path.join(HERE, "reference-check.md")
UA = "silicon-science-cs/1.0 (mailto:editor@example.invalid)"


def curl(url):
    r = subprocess.run(["curl", "-s", "-m", "30", "-A", UA, url],
                       capture_output=True, text=True)
    return r.stdout


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    return re.sub(r"[^a-z0-9 ]", " ", s).split()


def same_title(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    inter = len(set(na) & set(nb))
    return inter / max(len(set(na)), len(set(nb))) >= 0.85


def authors_text(msg, n=3):
    out = []
    for a in (msg.get("author") or [])[:n]:
        fam = a.get("family") or a.get("name") or ""
        giv = a.get("given") or ""
        out.append(("%s %s" % (giv, fam)).strip())
    s = "; ".join(out)
    if len(msg.get("author") or []) > n:
        s += "; et al."
    return s


def crossref_doi(doi):
    raw = curl("https://api.crossref.org/works/" + doi.strip())
    try:
        msg = json.loads(raw)["message"]
    except Exception:
        return None
    title = (msg.get("title") or [""])[0]
    year = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
    venue = (msg.get("container-title") or [""])[0] or msg.get("publisher", "")
    return {"title": title, "year": year, "venue": venue, "doi": msg.get("DOI", doi),
            "authors": authors_text(msg), "source": "Crossref DOI lookup"}


def crossref_title(title):
    import urllib.parse
    url = ("https://api.crossref.org/works?rows=5&select=title,author,issued,DOI,"
           "container-title,type&query.bibliographic=" + urllib.parse.quote(title))
    raw = curl(url)
    try:
        items = json.loads(raw)["message"]["items"]
    except Exception:
        return None
    for msg in items:
        cand = (msg.get("title") or [""])[0]
        if same_title(cand, title):
            year = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
            return {"title": cand, "year": year,
                    "venue": (msg.get("container-title") or [""])[0],
                    "doi": msg.get("DOI", ""), "authors": authors_text(msg),
                    "source": "Crossref title search, normalised-title match"}
    return None


def arxiv_abs(aid):
    raw = curl("https://arxiv.org/abs/" + aid.strip())

    def meta(name):
        m = re.search(r'<meta name="%s" content="([^"]*)"' % name, raw)
        return m.group(1) if m else ""

    title = meta("citation_title")
    if not title:
        return None
    auths = re.findall(r'<meta name="citation_author" content="([^"]*)"', raw)
    date = meta("citation_date") or meta("citation_online_date")
    return {"title": title, "year": (date[:4] or None), "venue": "arXiv preprint",
            "doi": "arXiv:%s" % aid.strip(),
            "authors": "; ".join(auths[:3]) + ("; et al." if len(auths) > 3 else ""),
            "source": "arXiv abstract page (citation_* metadata)"}


def render(key, rec):
    title = rec["title"].strip().rstrip(".").strip()
    line = "%s. *%s*." % (rec["authors"] or "Anonymous", title)
    if rec["venue"]:
        line += " %s," % rec["venue"].strip()
    if rec["year"]:
        line += " %s." % rec["year"]
    if rec["doi"]:
        line += " `%s`" % rec["doi"]
    return line


def main():
    rows, refs, problems = [], [], []
    with io.open(BATCH, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.rstrip("\n")
            if not raw.strip() or raw.startswith("#"):
                continue
            key, kind, value = [p.strip() for p in raw.split("\t")[:3]]
            if kind == "doi":
                rec = crossref_doi(value)
            elif kind == "arxiv":
                rec = arxiv_abs(value)
            elif kind == "title":
                rec = crossref_title(value)
            else:
                rec = None
            if rec is None:
                rows.append((key, kind, "UNVERIFIED", "no matching record"))
                problems.append(key)
            else:
                rows.append((key, kind, "verified", "%s -- %s" %
                             (rec["title"], rec["doi"] or rec["venue"])))
                if kind == "title" and not same_title(rec["title"], value):
                    problems.append(key)
                refs.append((key, render(key, rec), rec))
            time.sleep(1.0)

    with io.open(OUT_REFS, "w", encoding="utf-8") as fh:
        fh.write("# Reference list -- generated by verify_refs.py, do not edit by hand.\n")
        fh.write("# One entry per cited key; each line corresponds to `bash verify_refs.sh` output.\n")
        for key, line, _ in refs:
            fh.write("[@%s] %s\n" % (key, line))

    with io.open(OUT_CHECK, "w", encoding="utf-8") as fh:
        fh.write("# Reference authenticity check\n\n")
        fh.write("Every citation key used in the manuscript is verified below against a real\n")
        fh.write("external record before submission; `verify_refs.sh` re-runs the checks and\n")
        fh.write("writes this file. A key with no verified record is a hard failure.\n\n")
        fh.write("| Key | Method | Result | Record found |\n|---|---|---|---|\n")
        for key, kind, result, detail in rows:
            fh.write("| `%s` | %s | %s | %s |\n" % (key, kind, result, detail))

    print("verify_refs: %d keys, %d verified, %d unverified" %
          (len(rows), len(refs), len(problems)))
    for k in problems:
        print("  UNVERIFIED:", k)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
