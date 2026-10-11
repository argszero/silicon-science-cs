#!/bin/sh
# Fetch the pinned real matrices for spike_real.py (#126).
# Source: SuiteSparse Matrix Collection (Tim Davis), https://sparse.tamu.edu/MM/...
# Each extracted .mtx is verified against matrices/SHA256SUMS on every read (spike_real.verify_corpus),
# and the two truncated digests recorded there (mtx_sha = the extracted .mtx, tar_sha = the archive the
# collection served) are the provenance.  Run:  sh fetch_matrices.sh
set -e
cd "$(dirname "$0")/matrices"
for m in HB/arc130 HB/ash219 HB/ash292 HB/ash85 HB/bcsstk01 HB/bcsstk02 HB/bcsstk09 HB/west0067 \
         HB/gre_1107 HB/impcol_a HB/impcol_b HB/impcol_d HB/nos3 HB/west0381; do
    n=$(basename "$m")
    curl -sL -o "$n.tar.gz" "https://sparse.tamu.edu/MM/$m.tar.gz"
    tar xzf "$n.tar.gz" --strip-components=1 "$n/$n.mtx"
    rm -f "$n.tar.gz"
done
python3 - <<'PY'
import hashlib, os, sys
bad = 0
for line in open("SHA256SUMS"):
    p = line.split()
    if not p:
        continue
    name = p[0]
    want = [x.split("=", 1)[1] for x in p if x.startswith("mtx_sha=")][0]
    have = hashlib.sha256(open(name, "rb").read()).hexdigest()[:len(want)]
    ok = have == want
    print("%-16s %s" % (name, "OK" if ok else "MISMATCH"))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)
PY
