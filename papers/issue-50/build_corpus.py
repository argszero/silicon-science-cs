#!/usr/bin/env python3
"""Issue #50 — build stratified corpus of open-weight model repos from HF mirror.

Strata:
  - popularity: top-downloaded (overall sort=downloads desc), long-tail (ascending)
  - org type: foundation-lab orgs (top-N per org) vs community (top overall)
Fetches model-list items (id, downloads, likes, pipeline_tag, library_name, tags,
createdAt) via hf-mirror.com and writes corpus.json (pinned snapshot).
Resume-safe: skips orgs already fetched (cache in snapshots/list/).
"""
import json, sys, time, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
LIST = SNAP / "list"
LIST.mkdir(parents=True, exist_ok=True)
MIRROR = "https://hf-mirror.com"

FOUNDATION_ORGS = [
    "meta-llama", "mistralai", "microsoft", "google", "deepseek-ai", "QwenLM",
    "bigscience", "tiiuae", "stabilityai", "EleutherAI", "cohere", "allenai",
    "upstage", "nvidia", "intel", "ai21labs",
]

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-census/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except Exception as e:
            if i == retries - 1:
                print(f"  FAIL {url}: {e}", flush=True)
                return None
            time.sleep(2 * (i + 1))
    return None

def cached_fetch(key, url):
    f = LIST / f"{key}.json"
    if f.exists():
        return json.load(open(f))
    d = fetch(url)
    if d is not None:
        json.dump(d, open(f, "w"), indent=1)
    return d

def main():
    items = {}
    # 1. top-downloaded overall (community + everything)
    d = cached_fetch("top_downloads_60", f"{MIRROR}/api/models?limit=60&sort=downloads&direction=-1")
    for m in d or []:
        items[m["id"]] = m
    print(f"top-downloads: {len(d or [])} items", flush=True)
    # 2. long-tail: paginate deep into the least-popular public models
    # (mirror rejects sort=direction=1; use large offsets instead)
    for off in (500, 550, 600):
        d = cached_fetch(f"offset_{off}", f"{MIRROR}/api/models?limit=30&offset={off}")
        for m in d or []:
            items[m["id"]] = m
        time.sleep(0.4)
    print(f"long-tail offsets: fetched", flush=True)
    # 3. foundation-lab orgs: top-8 per org
    orgs_ok = []
    for org in FOUNDATION_ORGS:
        d = cached_fetch(f"org_{org}", f"{MIRROR}/api/models?author={org}&limit=8&sort=downloads&direction=-1")
        if d is None:
            continue
        orgs_ok.append(org)
        for m in d:
            items[m["id"]] = m
        time.sleep(0.4)
    print(f"orgs fetched: {len(orgs_ok)} ({', '.join(orgs_ok)})", flush=True)
    print(f"TOTAL unique models: {len(items)}", flush=True)
    # write corpus
    recs = []
    for mid, m in sorted(items.items()):
        recs.append({
            "id": mid,
            "org": mid.split("/")[0],
            "downloads": m.get("downloads"),
            "likes": m.get("likes"),
            "pipeline_tag": m.get("pipeline_tag"),
            "library_name": m.get("library_name"),
            "tags": m.get("tags", []),
            "createdAt": m.get("createdAt"),
        })
    out = {"title": "Model Cards in the Wild", "issue": 50,
           "snapshot": "2026-08-30", "n_models": len(recs),
           "models": recs}
    json.dump(out, open(ROOT / "corpus.json", "w"), indent=1)
    print(f"wrote corpus.json: {len(recs)} models", flush=True)

if __name__ == "__main__":
    main()
