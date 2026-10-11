#!/usr/bin/env python3
"""Self-audit of spike_v0 (#124): plant the defect each certificate claims to catch, and require
that the certificate FIRES.  A check that never fires is decoration.

Three plants, each run against a FRESH copy of the clean instrument (Class 167: a plant is
conclusive only against a clean base), and each plant asserts its own substitution LANDED before
it may report a verdict (Class 168)."""
import os, shutil, subprocess, sys, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spike_v0.py")
CLEAN = open(SRC).read()


def run(src, workdir):
    p = os.path.join(workdir, "cand.py")
    with open(p, "w") as f:
        f.write(src)
    r = subprocess.run([sys.executable, "cand.py"], cwd=workdir, capture_output=True, text=True,
                       timeout=900)
    return r


def plant(name, old, new, expect_in_stderr):
    tmp = tempfile.mkdtemp(prefix="plant124_")
    # clean base: copy the whole research dir so imports/artefacts resolve
    for f in os.listdir(os.path.dirname(SRC)):
        s = os.path.join(os.path.dirname(SRC), f)
        if os.path.isfile(s):
            shutil.copy(s, tmp)
    planted = CLEAN.replace(old, new)
    # ASSERT THE SUBSTITUTION LANDED
    if old not in CLEAN:
        print("HARNESS DEFECT: anchor not found for", name); return False
    if planted == CLEAN or new not in planted:
        print("HARNESS DEFECT: substitution did not land for", name); return False
    n_occ = CLEAN.count(old)
    r = run(planted, tmp)
    fired = expect_in_stderr in (r.stderr + r.stdout)
    print("[%s] plant landed (anchor x%d) | exit=%d | certificate fired: %s"
          % (name, n_occ, r.returncode, fired))
    if not fired:
        tail = (r.stderr or r.stdout)[-600:]
        print("    --- output tail ---") ; print(tail)
    shutil.rmtree(tmp, ignore_errors=True)
    return fired


ok = True

# --- plant 1: the ORIGINAL defect -- a tail summed from P(X=0) with a clamp. Underflows at large n.
tail_clean = '''def tail(n, k, p, route="A"):
    if route == "A":
        return float(binom.sf(k - 1, n, p))
    return tail_B(n, k, p)'''
tail_plant = '''def tail(n, k, p, route="A"):
    # PLANT: route A is the underflowing recursion anchored at P(X=0)
    s = 0.0
    term = (1.0 - p) ** n
    for i in range(0, k):
        s += term
        if i < n and p > 0.0:
            term *= (n - i) / (i + 1) * p / (1.0 - p)
    return max(0.0, 1.0 - s)'''
# The owning certificate is the DEDICATED large-n check, not the routes-A/B comparison: that
# comparison's grid stops at n=400, below the n~1100 where the underflow appears (recorded).
ok &= plant("underflow-recursion", tail_clean, tail_plant, "the underflow defect has returned")

# --- plant 2: break the monotonicity of the tail (raise it in k)
mono_clean = '''    for p in (0.02, 0.10, 0.30, 0.49, 0.50):
        prev = 1.0
        for k in range(0, 201):
            t = tail(200, k, p)'''
mono_plant = '''    for p in (0.02, 0.10, 0.30, 0.49, 0.50):
        prev = 1.0
        for k in range(0, 201):
            t = tail(200, k, p) + (0.5 if k == 100 else 0.0)'''
ok &= plant("monotonicity-break", mono_clean, mono_plant, "violates its own monotonicity")

# --- plant 3: the Markov DP loses probability (a solver that silently drops mass)
mk_clean = '''    s = sum(tot.values())
    if abs(s - 1.0) > 1e-9:'''
mk_plant = '''    s = sum(tot.values()) * 0.98
    if abs(s - 1.0) > 1e-9:'''
ok &= plant("markov-mass-loss", mk_clean, mk_plant, "lost probability")

print()
print("SELF-AUDIT:", "ALL PLANTS CAUGHT" if ok else "A CERTIFICATE IS DECORATION")
sys.exit(0 if ok else 1)
