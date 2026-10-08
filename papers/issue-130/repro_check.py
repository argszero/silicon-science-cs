#!/usr/bin/env python3
"""repro_check -- the DETERMINISM certificate for the issue-130 instrument family.

It owns ONE property: re-running a committed instrument reproduces its artefact BYTE-FOR-BYTE.

Why it exists (R567). A sha256 quoted in notes.md is a claim about a REPRODUCTION, not about the
file that happened to be on disk when the note was written. The committed spike_v3 hash (c31e9fb2)
was reproduced by NOTHING -- not by two fresh runs (f620be59, da9c7a67), not by itself under a
pinned PYTHONHASHSEED (73692ca4). Two defects were behind it:
  D1 a seed built from `hash(str)`, which Python randomizes per process -> different DRAWS
     (spike_v0: benign eps* spread up to 0.037 over 3 runs; spike_v3: the character arm only,
     because the token arm used the stable cell-level rng, which localised the defect);
  D2 `sum(...)` over a set intersection, whose iteration order is string-hash order -> different
     last BITS (spike_v2 cosine cells only, max |delta| 2.78e-15; no count changed).
An accuracy certificate (|S(A,A)-1| < 1e-12) cannot see either: it owns a different property.

Method: run each instrument twice, save each artefact aside, compare sha256; then leave the
research dir holding one canonical (freshly reproduced) artefact per instrument and write the
measured hashes to artefact_hashes.json -- GENERATED, never hand-typed into prose.

  --selftest : prove the comparator can FAIL, on three plants
      P1 two identical objects                     -> PASS  (must not fire on a healthy pair)
      P2 objects differing in one byte             -> FAIL  (must fire on a changed artefact)
      P3 two PROCESSES of a hash(str)-seeded script -> FAIL  (the real-world defect, planted)
"""
import io, os, sys, json, shutil, hashlib, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
INSTRUMENTS = ["spike_v0", "spike_v1", "spike_v2", "spike_v3", "spike_v4", "spike_v5", "spike_v6",
               "spike_v7", "floor_v2", "floor_v3"]
# R570: spike_v4 (the fusion axis) joins the family. It is the FIRST instrument written after the
# R567 audit, so it inherits every rule from the start: stable integer seeds, sorted keys,
# math.fsum for order-independent reduction, and a `sim` call into spike_v2 rather than a
# re-derived statistic -- an instrument that re-implements a statistic it could import is a
# second place for the same defect to live.
# R572: spike_v5 (the null KEY axis) joins. Its seeds are derived from the LENGTHS only
# (`SEED0 + L1*1000003 + L2*10007 + salt`), never from `hash(str)`, and every statistic is imported
# from spike_v0/spike_v2 -- which is also what makes K2/K3 (exact object identities between pools)
# assertable at all.

def sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()

def artefact(name):
    return os.path.join(HERE, name + "_results.json")

def run(name):
    """Run one instrument to completion, in its own process, in the research dir."""
    p = subprocess.run([PY, name + ".py"], cwd=HERE, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def compare_two_runs(name, tmp):
    rc1, o1 = run(name)
    if rc1 != 0:
        return {"instrument": name, "verdict": "ERROR", "detail": "run 1 exit %d" % rc1}
    a = os.path.join(tmp, name + ".a.json"); shutil.copyfile(artefact(name), a)
    rc2, o2 = run(name)
    if rc2 != 0:
        return {"instrument": name, "verdict": "ERROR", "detail": "run 2 exit %d" % rc2}
    b = os.path.join(tmp, name + ".b.json"); shutil.copyfile(artefact(name), b)
    ha, hb = sha(a), sha(b)
    same = (ha == hb)
    if not same:  # keep the diverging pair so a failure can be read, not just reported
        shutil.copyfile(a, os.path.join(tmp, name + ".run1.json"))
        shutil.copyfile(b, os.path.join(tmp, name + ".run2.json"))
    return {"instrument": name, "verdict": "PASS" if same else "FAIL",
            "sha256": ha[:32], "bytes": os.path.getsize(a), "two_runs_identical": same}

def selftest():
    """Two-sided: the comparator must accept identical objects and reject a one-byte change and a
    hash(str)-seeded pair of processes."""
    tmp = tempfile.mkdtemp(prefix="reprocheck_")
    x = os.path.join(tmp, "x"); y = os.path.join(tmp, "y")
    io.open(x, "wb").write(b"abc\n"); io.open(y, "wb").write(b"abc\n")
    cases = []
    cases.append(("P1 identical objects -> PASS", sha(x) == sha(y), True))
    io.open(y, "wb").write(b"abd\n")
    cases.append(("P2 one byte differs -> FAIL", sha(x) == sha(y), False))
    plant = os.path.join(tmp, "plant.py")
    io.open(plant, "w").write("import random\n"
                              "r = random.Random(hash('seed'))\n"
                              "print(r.random())\n")
    outs = [subprocess.run([PY, plant], capture_output=True, text=True).stdout for _ in range(2)]
    cases.append(("P3 hash(str)-seeded processes -> FAIL (differ)", outs[0] == outs[1], False))
    ok = True
    for label, got, want in cases:
        good = (got == want)
        ok = ok and good
        print("  [%s] %s   (comparator said %s, required %s)"
              % ("OK" if good else "BAD", label, got, want))
    shutil.rmtree(tmp, ignore_errors=True)
    print("SELFTEST", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1

def main():
    if "--selftest" in sys.argv:
        return selftest()
    tmp = tempfile.mkdtemp(prefix="reprocheck_")
    rows = []
    for name in INSTRUMENTS:
        r = compare_two_runs(name, tmp)
        rows.append(r)
        print("  %-9s %-5s sha256=%s" % (name, r.get("verdict"),
                                         r.get("sha256", "-")[:32]))
        if r.get("verdict") == "ERROR":
            print("      %s" % r.get("detail"))
    # leave a canonical artefact per instrument (the second run already did; make it explicit)
    manifest = {}
    for name in INSTRUMENTS:
        rc, out = run(name)
        p = artefact(name)
        manifest[name] = {"sha256": sha(p), "bytes": os.path.getsize(p),
                          "two_runs_identical": next(
                              (r.get("two_runs_identical") for r in rows
                               if r["instrument"] == name), False)}
    io.open(os.path.join(HERE, "artefact_hashes.json"), "w", encoding="utf-8").write(
        json.dumps({"generated_by": "repro_check.py",
                    "property": "each instrument re-run reproduces its artefact byte-for-byte",
                    "instrument_hashes": manifest}, indent=1, sort_keys=True) + "\n")
    shutil.rmtree(tmp, ignore_errors=True)
    bad = [r["instrument"] for r in rows if r.get("verdict") != "PASS"]
    print("\nDETERMINISM CERTIFICATE: %s  (%d/%d instruments reproduce byte-for-byte)"
          % ("ALL PASS" if not bad else "FAIL: " + ",".join(bad),
             len(rows) - len(bad), len(rows)))
    return 0 if not bad else 1

if __name__ == "__main__":
    sys.exit(main())
