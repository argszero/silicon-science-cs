#!/bin/bash
# fetch_one.sh <url> <dest> — used by extract.py fetch-a (parallel via xargs)
url="$1"
dest="$2"
mkdir -p "$(dirname "$dest")"
if [ ! -f "$dest" ] || [ ! -s "$dest" ]; then
  curl -sL --max-time 20 "$url" -o "$dest"
  if [ ! -s "$dest" ]; then
    # fallback: raw.githubusercontent (jsDelivr may lag on brand-new SHAs)
    raw="${url/cdn.jsdelivr.net\/gh/raw.githubusercontent.com}"
    raw="${raw/@/\/}"
    curl -sL --max-time 30 "$raw" -o "$dest"
  fi
fi
