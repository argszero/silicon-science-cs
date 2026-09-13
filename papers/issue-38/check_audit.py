#!/usr/bin/env python3
"""Self-audit of validate.py for issue #38: every check must be able to FAIL.

A check that never fires is decoration. Two batches of mutations are applied to a
throwaway copy of the package -- each mutator asserts that it actually changed the
file, and the sandbox manifest digest is refreshed so that the digest check cannot be
the reason a semantic mutation is caught -- and every mutation must produce at least
one [FAIL] and a non-zero exit.

    python3 check_audit.py      (from papers/issue-38/)

This is deliberately NOT part of reproduce.sh: it audits the suite, not the result.
"""
#!/usr/bin/env python3
import hashlib, json, os, re, shutil, subprocess, sys, tempfile

SRC = "/Users/argszero/.emrg/journal-work/silicon-science-cs/papers/issue-38"


def set_path(doc, path, value):
    """Set 'a.b[3].c' -> value. Returns the previous value."""
    m = re.match(r"^([A-Za-z0-9_]+)", path)
    cur, rest = doc, path
    while True:
        m = re.match(r"^([A-Za-z0-9_]+)", rest)
        key = m.group(1)
        rest = rest[m.end():]
        idx = None
        if rest.startswith("["):
            j = rest.index("]")
            idx = int(rest[1:j])
            rest = rest[j + 1:]
        last = rest == ""
        if last and idx is None:
            old = cur[key]
            cur[key] = value
            return old
        nxt = cur[key][idx] if idx is not None else cur[key]
        if not rest.startswith("."):
            # terminal with index
            old = cur[key][idx]
            cur[key][idx] = value
            return old
        rest = rest[1:]
        cur = nxt


MUTATIONS = [
    ("artefact", "reductions.cells", 269),
    ("artefact", "reductions.failures", 1),
    ("artefact", "anchors.greedy_le_random_rate", 0.99),
    ("artefact", "anchors.market_exact_at_sigma_zero", False),
    ("artefact", "law_grid.p1_verdict.n_endpoint_rising", 49),
    ("artefact", "law_grid.collapse_fit.b", 1.2),
    ("artefact", "law_grid.cells[0].A", 99.0),
    ("artefact", "oos.scores.fitted_power_law.median_rel_err", 0.10),
    ("artefact", "closure.forms_scored_on_unseen_cells.H_gap.median_rel_err", 0.50),
    ("artefact", "closure.attention_agnostic.fraction_cells_never_fitted.median_A", 5.0),
    ("artefact", "mechanism.oracle_mismatch_rate[1].rate", 0.05),
    ("artefact", "p3_ablation.specialisation_off_boundary_still_exists", False),
    ("artefact", "p3_ablation.verdict", "CONFIRMED"),
    ("artefact", "ADD_elapsed_seconds", 12.5),
]

ok, bad = 0, []
for kind, path, value in MUTATIONS:
    sand = tempfile.mkdtemp(prefix="corrupt38-")
    try:
        for f in ("validate.py", "canonical_results.json", "make_figures.py"):
            shutil.copy(os.path.join(SRC, f), sand)
        shutil.copytree(os.path.join(SRC, "figures"), os.path.join(sand, "figures"))
        before = open(os.path.join(sand, "canonical_results.json"), "rb").read()
        doc = json.loads(before)
        if path.startswith("ADD_"):
            doc[path[4:]] = value
        else:
            set_path(doc, path, value)
        after = json.dumps(doc, indent=1, sort_keys=True).encode()
        assert after != before, "mutator did not change the file"      # mutators must bite
        open(os.path.join(sand, "canonical_results.json"), "wb").write(after)
        # Keep the sandbox SELF-CONSISTENT: refresh the manifest digest so that the
        # digest check cannot be the reason a semantic mutation is caught. Without
        # this, every artefact mutation trips the digest check and "at least one
        # check fired" would be satisfied by decoration.
        mp = os.path.join(sand, "figures", "manifest.json")
        man = json.load(open(mp))
        man["artefact_sha256"] = hashlib.sha256(after).hexdigest()
        json.dump(man, open(mp, "w"), indent=1, sort_keys=True)
        r = subprocess.run([sys.executable, "validate.py"], cwd=sand,
                           capture_output=True, text=True)
        lines = [l.strip() for l in r.stdout.splitlines() if "[FAIL]" in l]
        nfail = len(lines)
        caught = nfail >= 1 and r.returncode != 0
        if caught:
            print("        fired: %s" % "; ".join(l.split("]")[1].split()[0] for l in lines))
        print("  [%s] %-58s FAILs=%d exit=%d" % ("ok" if caught else "MISS", path, nfail,
                                                 r.returncode))
        if caught:
            ok += 1
        else:
            bad.append(path)
    finally:
        shutil.rmtree(sand, ignore_errors=True)

# non-JSON mutations: a figure digest, and a missing figure
for name, mutate in (("manifest_artefact_digest", "digest"), ("figure_deleted", "delete")):
    sand = tempfile.mkdtemp(prefix="corrupt38-")
    try:
        for f in ("validate.py", "canonical_results.json"):
            shutil.copy(os.path.join(SRC, f), sand)
        shutil.copytree(os.path.join(SRC, "figures"), os.path.join(sand, "figures"))
        mp = os.path.join(sand, "figures", "manifest.json")
        before = open(mp, "rb").read()
        man = json.loads(before)
        if mutate == "digest":
            man["artefact_sha256"] = "0" * 64
            open(mp, "w").write(json.dumps(man, indent=1, sort_keys=True))
        else:
            os.unlink(os.path.join(sand, "figures", man["figures"][1]["file"]))
        if mutate == "digest":
            assert open(mp, "rb").read() != before, "mutator did not change the file"
        r = subprocess.run([sys.executable, "validate.py"], cwd=sand, capture_output=True, text=True)
        nfail = r.stdout.count("[FAIL]")
        caught = nfail >= 1 and r.returncode != 0
        print("  [%s] %-58s FAILs=%d exit=%d" % ("ok" if caught else "MISS", name, nfail,
                                                 r.returncode))
        if caught:
            ok += 1
        else:
            bad.append(name)
    finally:
        shutil.rmtree(sand, ignore_errors=True)

ok1 = ok
print("batch 1 (artefact fields, manifest, figures): %d/%d caught" % (ok1, len(MUTATIONS) + 2))

# ---------------- batch 2: breakdowns, exponent table, ablation, mechanisms -------------
def hamming(doc):
    for s in doc["mechanism"]["hamming"]:
        if s["gamma"] == 1.0 and s["beta"] == 0.5 and s["sigma"] == 0.05:
            s["series"][2]["rate"] = 0.99
            return
    raise AssertionError("hamming series not found")


def wrong_block(doc):
    for s in doc["mechanism"]["wrong_block_rate"]:
        if s["gamma"] == 1.0 and s["beta"] == 2.0 and s["sigma"] == 0.05:
            s["series"][2]["rate"] = 0.5
            return
    raise AssertionError("wrong-block series not found")


MUT = [
    ("A_by_gamma[0.25]", lambda d: d["closure"]["A_by_gamma"]["0.25"].__setitem__("median", 5.0)),
    ("A_by_distribution[uniform]", lambda d: d["closure"]["A_by_distribution"]["uniform"].__setitem__("median", 5.0)),
    ("exponent_by_gamma[1.0]", lambda d: d["closure"]["exponent_by_gamma"].__setitem__("1.0", 1.4)),
    ("A_by_m[1]", lambda d: d["law_grid"]["A_by_m"]["1"].__setitem__("median", 1.0)),
    ("sigma_star[beta=0,N=64]", lambda d: d["p3_ablation"]["sigma_star_specialisation_off"].__setitem__("64", 5.0)),
    ("amplification[N=16]", lambda d: d["p3_ablation"]["amplification_beta_max_over_beta_0"].__setitem__("16", 1.0)),
    ("market_exactly_zero_at_sigma0", lambda d: d["p3_ablation"].__setitem__("market_regret_exactly_zero_when_information_perfect", False)),
    ("one_constant.c", lambda d: d["closure"]["one_constant"].__setitem__("c", 9.0)),
    ("hamming[gamma=1,beta=0.5,sigma=0.05]", hamming),
    ("wrong_block[gamma=1,beta=2.0,sigma=0.05]", wrong_block),
]

ok, bad = 0, []
for name, fn in MUT:
    sand = tempfile.mkdtemp(prefix="corrupt38b-")
    try:
        for f in ("validate.py", "canonical_results.json"):
            shutil.copy(os.path.join(SRC, f), sand)
        shutil.copytree(os.path.join(SRC, "figures"), os.path.join(sand, "figures"))
        fp = os.path.join(sand, "canonical_results.json")
        before = open(fp, "rb").read()
        doc = json.loads(before)
        fn(doc)
        after = json.dumps(doc, indent=1, sort_keys=True).encode()
        assert after != before, "mutator did not change the file"
        open(fp, "wb").write(after)
        mp = os.path.join(sand, "figures", "manifest.json")
        man = json.load(open(mp))
        man["artefact_sha256"] = hashlib.sha256(after).hexdigest()
        json.dump(man, open(mp, "w"), indent=1, sort_keys=True)
        r = subprocess.run([sys.executable, "validate.py"], cwd=sand, capture_output=True, text=True)
        lines = [l.strip() for l in r.stdout.splitlines() if "[FAIL]" in l]
        caught = len(lines) >= 1 and r.returncode != 0
        print("  [%s] %-46s -> %s" % ("ok" if caught else "MISS", name,
                                      "; ".join(l.split("]")[1].split()[0] for l in lines) or "NOTHING"))
        ok += 1 if caught else 0
        if not caught:
            bad.append(name)
    finally:
        shutil.rmtree(sand, ignore_errors=True)




print("corruption audit: %d/%d mutations caught" % (ok1 + ok, len(MUTATIONS) + 2 + len(MUT)))
if bad:
    print("NOT CAUGHT: %s" % bad)
sys.exit(1 if bad else 0)
