# -*- coding: utf-8 -*-
"""verify_fixture.py -- is the committed input the bytes this package measured?

The fixture is the trace's day-01 duration table, stored xz-compressed. The digest that identifies
it is the sha256 of the **decompressed** bytes: a re-compression with a different preset produces
different storage and the same data, and the data is what every number in the paper came from.

`fixture/MEMBER_SHA256` holds that digest plus the provenance of the archive member (URL, size,
member name). This program reads it, decompresses the fixture, and compares.

Exit contract (the journal's, from #158's self-triage):
  0  verified: the decompressed bytes are the recorded bytes
  1  mismatch or missing provenance -- a failure, and it names the two digests
  3  NOT RUN: the fixture is absent, so nothing was verified (never a pass, never a failure)

`--selftest` proves the comparison can FAIL: it runs the same predicate on a digest with one hex
digit changed and on a truncated stream, and both must be refused. A guard nobody has seen fail is
not a guard.
"""
import hashlib
import lzma
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIR = os.path.join(HERE, "fixture")
MEMBER = "function_durations_percentiles.anon.d01.csv"
BLOB = os.path.join(FIXTURE_DIR, MEMBER + ".xz")
PROVENANCE = os.path.join(FIXTURE_DIR, "MEMBER_SHA256")


def recorded_digest(path=PROVENANCE):
    """The digest this package recorded, read from the provenance file (never hard-coded twice)."""
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tok = line.split()
        if len(tok) >= 1 and len(tok[0]) == 64:
            return tok[0].lower()
    return None


def digest_of_blob(path=BLOB):
    """(sha256, byte count) of the DECOMPRESSED member, streamed so memory is not a function of input.

    The count comes back with the digest because the two are read from the same stream: reporting
    the compressed file's size as the decompressed size is a print that lies about its own number.
    """
    h = hashlib.sha256()
    n = 0
    with lzma.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def check(blob=BLOB, provenance=PROVENANCE):
    """(ok, message). The one predicate both `main` and `--selftest` use -- not a copy each."""
    if not os.path.exists(blob):
        return None, "fixture absent: %s" % os.path.relpath(blob, HERE)
    want = recorded_digest(provenance)
    if not want:
        return False, "no digest recorded in %s" % os.path.relpath(provenance, HERE)
    try:
        got, nbytes = digest_of_blob(blob)
    except (lzma.LZMAError, OSError) as e:
        return False, "fixture cannot be decompressed (%s: %s)" % (type(e).__name__, e)
    if got != want:
        return False, "digest mismatch\n   recorded %s\n   actual   %s" % (want, got)
    return True, "sha256 %s (%d B decompressed)" % (got, nbytes)


def selftest():
    fails = 0

    def expect(name, ok, detail=""):
        nonlocal fails
        print("  [%s] %s%s" % ("ok" if ok else "FAIL", name, (" -- " + detail) if detail else ""))
        if not ok:
            fails += 1

    import tempfile

    if not os.path.exists(BLOB):
        print("  [SKIP] the fixture is absent, so the refusals cannot be demonstrated here")
        print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
        return 0 if fails == 0 else 1

    real = recorded_digest()
    expect("the committed fixture verifies against its own recorded digest",
           check()[0] is True, check()[1].split("\n")[0])

    tmp = tempfile.mkdtemp()
    try:
        # 1. one hex digit changed: the predicate must refuse. This is the defect that actually
        #    happens -- a digest recorded from a different day's member, or a typo.
        bad = "0" + real[1:] if real[0] != "0" else "1" + real[1:]
        p = os.path.join(tmp, "MEMBER_SHA256")
        open(p, "w").write(bad + "  " + MEMBER + "\n")
        expect("a digest with one hex digit changed is refused", check(BLOB, p)[0] is False,
               check(BLOB, p)[1].split("\n")[0])

        # 2. a truncated stream: the same predicate, reached through the decompressor's failure.
        #    Without this case, a broken `digest_of_blob` would look like a refusing guard.
        with lzma.open(BLOB, "rb") as f:
            head = f.read(4096)
        trunc = os.path.join(tmp, "trunc.csv.xz")
        open(trunc, "wb").write(lzma.compress(head))
        expect("a stream that decompresses to the wrong bytes is refused",
               check(trunc, PROVENANCE)[0] is False, check(trunc, PROVENANCE)[1].split("\n")[0])

        # 3. absent fixture: NOT RUN, distinct from both pass and fail.
        expect("an absent fixture returns None (NOT RUN), not False",
               check(os.path.join(tmp, "nope.xz"), PROVENANCE)[0] is None)
    finally:
        for n in os.listdir(tmp):
            os.remove(os.path.join(tmp, n))
        os.rmdir(tmp)

    print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    ok, msg = check()
    if ok is None:
        print("NOT RUN: %s" % msg)
        print("         this package cannot verify an input it does not have; nothing was checked")
        return 3
    if ok and "--print-sha" in argv:
        # exactly one line: this value is consumed by command substitution upstream, and a log
        # line leaking into it is the defect #158 paid for twice.
        print(msg.split()[-1])
        return 0
    if ok:
        print("fixture integrity: OK -- %s" % msg)
        print("   member %s, stored as %s (%d B compressed)"
              % (MEMBER, os.path.basename(BLOB), os.path.getsize(BLOB)))
        return 0
    print("FAILED: %s" % msg)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
