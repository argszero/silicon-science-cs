#!/usr/bin/env python3
"""verify_fixture.py -- the committed fixture is the bytes this package measured.

`fixture/SHA256SUMS` holds one line per fixture file. This program recomputes the digest and
compares; a mismatch means the fixture on disk is not the one the recorded results were produced
from, and every number downstream is then about some other data. That is a hard failure, not a
warning.

    python3 verify_fixture.py              # verify, exit 1 on mismatch
    python3 verify_fixture.py --print-sha  # print the digest (used by reproduce.sh)
"""
import hashlib
import os
import sys

SUMS = "fixture/SHA256SUMS"


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def recorded():
    if not os.path.exists(SUMS):
        return {}
    out = {}
    for line in open(SUMS):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, name = line.partition("  ")
        out[name.strip()] = digest.strip()
    return out


def main(argv):
    # `--print-sha` is consumed by command substitution, so in that mode stdout carries the
    # digest and NOTHING else -- a status line mixed into it becomes a second word of the hash and
    # the caller's command fails in a way that looks like a missing dependency.
    quiet = len(argv) > 1 and argv[1] == "--print-sha"
    say = (lambda *a: None) if quiet else print
    want = recorded()
    if not want:
        say("  [FAIL] %s is missing or empty -- the fixture is unverified" % SUMS)
        return 1
    failed = 0
    for name, digest in sorted(want.items()):
        if not os.path.exists(name):
            say("  [FAIL] %s is recorded but absent" % name)
            failed += 1
            continue
        got = sha256(name)
        ok = got == digest
        say("  [%s] %s%s" % ("ok" if ok else "FAIL", name,
                               "" if ok else "  recorded %s, on disk %s" % (digest[:16], got[:16])))
        if not ok:
            failed += 1
    if len(argv) > 1 and argv[1] == "--print-sha":
        for name, digest in sorted(want.items()):
            if name.endswith(".npz"):
                print(digest)
                break
        return 0 if failed == 0 else 1
    say("FIXTURE: %s" % ("OK" if failed == 0 else "%d MISMATCHED" % failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
