#!/usr/bin/env python3
"""Flatten the harvested Crossref/arXiv caches into `candidates.json` and print an index.

The harvest is by TOPIC, so every record here exists -- the selection this supports is about
RELEVANCE, never about existence.  Reading the index is how the reference list gets chosen.
"""

from __future__ import annotations

import glob
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")


def main() -> int:
    rows = []
    for f in sorted(glob.glob(os.path.join(RAW, "cr_*.json"))):
        d = json.load(open(f))
        for it in d["message"]["items"]:
            t = (it.get("title") or [""])[0].strip()
            if not t:
                continue
            yr = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
            ct = it.get("container-title") or [""]
            rows.append({
                "src": "crossref", "id": it.get("DOI", ""),
                "title": re.sub(r"\s+", " ", t), "year": yr,
                "venue": (ct[0] if ct else ""), "type": it.get("type", ""),
                "authors": [f"{a.get('family', '')}|{a.get('given', '')}"
                            for a in (it.get("author") or [])],
            })
    for f in sorted(glob.glob(os.path.join(RAW, "ax_*.xml"))):
        x = open(f, encoding="utf-8", errors="replace").read()
        for e in re.findall(r"<entry>(.*?)</entry>", x, re.S):
            def g(tag):
                m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", e, re.S)
                return html.unescape(m.group(1)).strip() if m else ""

            aid = re.search(r"<id>http://arxiv.org/abs/([^<]+)</id>", e)
            pub = g("published")
            rows.append({
                "src": "arxiv", "id": aid.group(1) if aid else "",
                "title": re.sub(r"\s+", " ", g("title")),
                "year": int(pub[:4]) if pub[:4].isdigit() else None,
                "venue": "arXiv preprint", "type": "preprint",
                "authors": re.findall(r"<name>(.*?)</name>", e),
            })

    seen, out = set(), []
    for r in rows:
        k = r["title"].lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    with open(os.path.join(HERE, "candidates.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"{len(out)} unique candidates")
    for i, r in enumerate(out):
        au = r["authors"][0].split("|")[0] if r["authors"] else "?"
        print(f"{i:3d} [{r['src'][:2]}] {r['year']} {au:<14.14} {r['title'][:94]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
