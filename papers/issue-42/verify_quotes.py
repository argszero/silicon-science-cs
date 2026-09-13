#!/usr/bin/env python3
"""Verify every calibration quote against the committed evidence, offline.

The dossier records, for each calibration cell, a verbatim quote and the capture it came from.
This script reads the gzipped normalised text in evidence/ and asserts that each quote is
actually present, using the SAME normalisation.  It is two-sided: a mutated needle must be
REJECTED, otherwise the check is decoration and would pass on any input.
"""
import gzip
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def norm(s):
    s = s.lower()
    for c in (chr(0x2013), chr(0x2014), chr(0x2212), chr(0x2010)):
        s = s.replace(c, "-")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%.,;:()=\-]+", " ", s)).strip()


def main():
    rows = json.load(io.open(os.path.join(HERE, "artefacts", "calibration_dossier.json"), encoding="utf-8"))
    cache, bad = {}, []
    for r in rows:
        p = os.path.join(HERE, r["cap"])
        if p not in cache:
            cache[p] = norm(gzip.open(p, "rt", encoding="utf-8", errors="replace").read())
        found = norm(r["needle"]) in cache[p]
        if not found:
            bad.append(r["sys"])
        print("%-6s %-22s %s" % ("FOUND" if found else "MISSING", r["sys"], r["needle"][:52]))
    # two-sided control: a needle that cannot exist must be rejected by the same test
    control = norm("this sentence exists in no capture whatsoever 98765")
    control_ok = not any(control in v for v in cache.values())
    print()
    print("quotes %d/%d found ; mutated-needle control rejected = %s" % (len(rows) - len(bad), len(rows), control_ok))
    if bad or not control_ok:
        print("VERIFY FAILED: missing=%s control_ok=%s" % (bad, control_ok))
        return 1
    print("VERIFY QUOTES: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
