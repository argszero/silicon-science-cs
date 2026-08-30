#!/usr/bin/env python3
"""Issue #50 — fetch model-card data for the corpus from hf-mirror.com (SEQUENTIAL).

For each model in corpus.json:
  1. GET /api/models/{id}          -> snapshots/cards/{org}__{name}.json  (cardData + metadata)
  2. GET /{id}/raw/main/README.md  -> snapshots/readmes/{org}__{name}.md  (raw card content)
Resume-safe: skips already-fetched files. Sequential (sandbox blocks threaded
sockets). Usage: fetch_cards.py [max_new] — process at most max_new models per
call (default: all remaining); run repeatedly to continue.
"""
import json, sys, time, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
CARDS = SNAP / "cards"
READMES = SNAP / "readmes"
CARDS.mkdir(parents=True, exist_ok=True)
READMES.mkdir(parents=True, exist_ok=True)
MIRROR = "https://hf-mirror.com"

MODELS = json.load(open(ROOT / "corpus.json"))["models"]

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-census/1.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:
                time.sleep(2 * (i + 1))
                continue
            return None
        except Exception:
            if i == retries - 1:
                return None
            time.sleep(2 * (i + 1))
    return None

def safe_name(mid):
    return mid.replace("/", "__")

def main():
    max_new = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
    todo = []
    for m in MODELS:
        key = safe_name(m["id"])
        if not (CARDS / f"{key}.json").exists() or not (READMES / f"{key}.md").exists():
            todo.append(m["id"])
    print(f"remaining: {len(todo)}", flush=True)
    n_done = 0
    for mid in todo:
        if n_done >= max_new:
            break
        key = safe_name(mid)
        enc = urllib.parse.quote(mid, safe="/")
        cpath = CARDS / f"{key}.json"
        rpath = READMES / f"{key}.md"
        if not cpath.exists():
            raw = fetch(f"{MIRROR}/api/models/{enc}")
            if raw:
                try:
                    json.dump(json.loads(raw), open(cpath, "w"), indent=1)
                except Exception:
                    pass
        if not rpath.exists():
            r = fetch(f"{MIRROR}/{enc}/raw/main/README.md")
            if r is not None:
                rpath.write_bytes(r)
        n_done += 1
        if n_done % 20 == 0:
            nc = len(list(CARDS.glob("*.json")))
            print(f"  {nc}/{len(MODELS)} cards fetched", flush=True)
        time.sleep(0.3)
    nc = len(list(CARDS.glob("*.json")))
    nr = len(list(READMES.glob("*.md")))
    print(f"done this call: {n_done} | cards {nc}/{len(MODELS)}, readmes {nr}/{len(MODELS)}", flush=True)

if __name__ == "__main__":
    main()
