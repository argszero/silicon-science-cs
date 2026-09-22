#!/usr/bin/env python3
"""R419 -- read the round-3 required change at the object it names, and show the reading can fail.

The R446 editorial re-check (2026-09-22T01:12Z) closed R444's four changes and left ONE defect:

  (D) "the run has three build-bound steps but declares one, and the declared one is last, so a reader on
       another build stops at step 1/5 and never sees the BUILD_BOUND reading the revision built."

Every check below reads a file or runs an instrument -- never a claim about either -- and prints what it read,
so the verdict is auditable.  The script is also its own battery: `--selftest` runs it against scratch copies of
the package with the defect RE-INTRODUCED one property at a time, and every plant must move the exit code.  A
checker is believed once it has been made to fail on purpose (R415's rule); a claim of "discharged" that cannot
go red is a claim nobody has tested.

Usage:
  python3 artefacts/assembly/verify_revision_round3.py [--pkg DIR]     exit 0 = (D) discharged
  python3 artefacts/assembly/verify_revision_round3.py --selftest     the battery, on scratch copies
"""
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

PY = "/usr/bin/python3"
FOREIGN = os.path.expanduser("~/.asdf/installs/python/3.14.6/bin/python3")
READING_WORDS = ("reported", "rendered", "exact")


def checks(pkg):
    """Returns (ok, rows) where a row is (id, what, ok, evidence-read)."""
    p = lambda *a: os.path.join(pkg, *a)
    rows = []
    add = lambda i, w, ok, e: rows.append((i, w, ok, e))
    rep = io.open(p("reproduce.sh"), encoding="utf-8").read()
    readme = io.open(p("README.md"), encoding="utf-8").read()
    # A phrase is what a READER sees: a hard line break inside it is a property of the file, not of the
    # sentence.  Every prose probe below reads this flattened form (R415's lesson, relearned here when the
    # foreign-build sentence wrapped between "Python" and "3.9.6 / numpy 2.0.2" and the probe went red on a
    # sentence that was present).
    flat = " ".join(readme.split())
    cc_src = io.open(p("artefacts", "assembly", "counts_check.py"), encoding="utf-8").read()
    bodies = re.split(r'^echo "=== \d+/\d+ ', rep, flags=re.M)[1:]   # one block per step, split at the NUMBERED
    # step headers only -- the preamble is `echo "=== build ...` and splitting on a bare `=== ` put it in the
    # list, shifting every body by one (the first version of this check read step 5's body as step 4's).

    # ---- 1: ONE numbering basis -- the steps are 1..N with no duplicate and no gap, and each carries a
    # reading word, so "five steps" is a property of the file rather than of the prose around it.
    heads = re.findall(r'^echo "=== (\d+)/(\d+) ([^\n]*)', rep, re.M)
    nums = [int(a) for a, _, _ in heads]
    dens = set(b for _, b, _ in heads)
    worded = [h for h in heads if any(w in h[2].lower() for w in READING_WORDS)]
    add("1", "the run numbers its steps on one basis (1..N, no duplicate, no gap)",
        nums == list(range(1, len(nums) + 1)) and len(dens) == 1 and len(nums) >= 5,
        "step headers read: %s | denominator(s): %s" % (nums, sorted(dens)))
    add("1b", "every step header names how it was read (REPORTED / RENDERED / EXACT)",
        len(worded) == len(heads) and len(heads) > 0,
        "with a reading word: %d of %d -- %s"
        % (len(worded), len(heads), [h[2][:34] for h in heads]))

    # ---- 2: the three build-bound steps are DECLARED, and none of them is last.  The defect was an
    # under-count plus an ordering: a reader on another build met a stop condition first.
    #
    # The classification is TWO-SIDED and reads two objects: what each header DECLARES (REPORTED / RENDERED /
    # EXACT) and what each body actually CALLS.  Reading only one of them is not enough -- a body that calls the
    # tolerance comparator under a header that declares an exact reading is the very under-declaration this
    # round repairs, and it is exactly what a keyword-only classification (the first version of this check,
    # which misread step 4/5 as build-bound because its body runs the counts checker's battery) would hide.
    declared = {int(a): ("build-bound" if any(w in h.lower() for w in ("reported", "rendered")) else "exact")
                for a, _, h in heads}
    called = {}
    for head, body in zip(heads, bodies):
        b = body
        bb_call = ("build_bound.py" in b) or ("--control-only" in b)
        ex_call = ("cmp -s" in b) or ("GATE: PASS" in b) or ("same " in b)
        called[int(head[0])] = ("build-bound" if bb_call and not ex_call else
                                "exact" if ex_call and not bb_call else "mixed")
    bb = sorted(n for n, k in declared.items() if k == "build-bound")
    ex = sorted(n for n, k in declared.items() if k == "exact")
    disagree = {n: (declared[n], called[n]) for n in declared if declared[n] != called[n]}
    # The preamble DECLARES the count of build-bound steps in words; read the number out of that sentence and
    # require it to equal what the bodies do -- this is the under-count, read at the object.
    m = re.search(r'TOLERANCE -- WHICH STEPS ARE READ AGAINST THE PINNED BUILD: \*\*(\w+)\*\*', rep)
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    n_declared = words.get(m.group(1).lower()) if m else None
    add("2", "the run declares the number of build-bound steps that its bodies carry",
        n_declared is not None and n_declared == len(bb),
        "preamble declares %s build-bound step(s); the headers declare %s (steps %s)"
        % (n_declared, len(bb), bb))
    add("2a", "every step's declared reading is the one its body carries",
        not disagree,
        "declared vs called: %s" % {n: called[n] for n in sorted(called)})
    add("2b", "no build-bound step is unreachable: every one precedes the first stop condition",
        len(bb) > 0 and len(ex) > 0 and max(bb) < min(ex),
        "build-bound steps %s | exact (stop-condition) steps %s -- the reader meets %d before %d"
        % (bb, ex, len(bb), min(ex)))
    # ... and the manifest states each step's reading, so "ALL GREEN" is never read without them.
    man = rep[rep.index("manifest of what was compared"):]
    man_steps = [l.strip() for l in man.split("\n") if re.match(r'\s*echo "\s*\d+/%d ' % len(heads), l)]
    add("2c", "the manifest names all %d steps and their readings" % len(heads),
        len(man_steps) == len(heads) and all(any(w in l for w in ("REPORTED", "RENDERED", "EXACT"))
                                             for l in man_steps)
        and sum(1 for w in ("REPORTED", "RENDERED", "EXACT") if w in man) == 3,
        "%d manifest line(s): %s" % (len(man_steps), [(l.split("--")[0].strip(), "REPORTED" if "REPORTED" in l
                                                       else "RENDERED" if "RENDERED" in l else "EXACT")
                                                      for l in man_steps]))

    # ---- 3: the comparator's three states are REACHABLE, measured on plants (not asserted).
    dig = p("artefacts", "results_digest.json")
    with tempfile.TemporaryDirectory() as tmp:
        d = json.load(io.open(dig, encoding="utf-8"))
        key = "panel.q8_over_q6_ratio_of_the_mid_band"
        base = d["quantities"][key]["value"]["mean"]
        plants = {}
        for name, val in (("ulp", math.nextafter(base, 2.0)), ("big", base * (1 + 1e-5))):
            c = json.loads(json.dumps(d))
            c["quantities"][key]["value"]["mean"] = val
            fp = os.path.join(tmp, name + ".json")
            io.open(fp, "w", encoding="utf-8").write(json.dumps(c, sort_keys=True))
            plants[name] = fp
        c = json.loads(json.dumps(d))
        del c["quantities"][key]
        fp = os.path.join(tmp, "struct.json")
        io.open(fp, "w", encoding="utf-8").write(json.dumps(c, sort_keys=True))
        plants["struct"] = fp
        runs = {}
        for name, arg in (("unperturbed", dig), ("ulp", plants["ulp"]), ("big", plants["big"]),
                          ("struct", plants["struct"])):
            r = subprocess.run([PY, p("artefacts", "assembly", "build_bound.py"), "json", dig, arg,
                                "--label", name], capture_output=True, text=True)
            verdict = re.search(r'verdict\s+:\s+(\w+)', r.stdout)
            runs[name] = (r.returncode, verdict.group(1) if verdict else "?")
    add("3", "the comparator's three verdicts are reachable, and only a real departure exits non-zero",
        runs["unperturbed"] == (0, "BITWISE") and runs["ulp"] == (0, "BUILD_BOUND")
        and runs["big"][0] == 1 and runs["big"][1] == "FAIL"
        and runs["struct"][0] == 1 and runs["struct"][1] == "FAIL",
        "unperturbed %s | 1-ULP plant %s | 1e-5 plant %s | structural plant %s"
        % (runs["unperturbed"], runs["ulp"], runs["big"], runs["struct"]))

    # ---- 4: the loss that slipped past the previous checker is now caught, at the object, by a plant.
    with tempfile.TemporaryDirectory() as tmp:
        dst = os.path.join(tmp, "pkg")
        os.makedirs(os.path.join(dst, "artefacts", "assembly"))
        for rel in ("README.md", "reproduce.sh", "manuscript.md",
                    "artefacts/assembly/assembly-report.txt", "artefacts/results_digest.json"):
            shutil.copy(p(*rel.split("/")), os.path.join(dst, rel))
        rd, rpm = os.path.join(dst, "README.md"), os.path.join(dst, "reproduce.sh")
        # (a) a REQUIRED count re-worded out of the checker's declared phrasing, in the README
        t = io.open(rd, encoding="utf-8").read()
        assert "76 quantities, each read out" in t
        io.open(rd, "w", encoding="utf-8").write(t.replace("76 quantities, each read out", "76 quantities"))
        lost = subprocess.run([PY, p("artefacts", "assembly", "counts_check.py"), "--pkg", dst],
                              capture_output=True, text=True)
        # (b) the same loss in the RUN, with the README restored to its committed text first
        shutil.copy(p("README.md"), rd)
        t = io.open(rpm, encoding="utf-8").read()
        assert "76 quantities read out" in t
        io.open(rpm, "w", encoding="utf-8").write(t.replace("76 quantities read out", "the digest"))
        lost2 = subprocess.run([PY, p("artefacts", "assembly", "counts_check.py"), "--pkg", dst],
                               capture_output=True, text=True)
    own = subprocess.run([PY, p("artefacts", "assembly", "counts_check.py")], capture_output=True, text=True)
    bat = subprocess.run([PY, p("artefacts", "assembly", "counts_check.py"), "--selftest"],
                         capture_output=True, text=True)
    add("4", "a required count LOST from a carrier turns the counts checker red (the previous version passed it)",
        lost.returncode == 1 and "no longer stated" in lost.stdout
        and lost2.returncode == 1
        and own.returncode == 0 and "absent-by-design" in cc_src
        and bat.returncode == 0 and re.search(r'(\d+) case\(s\), \1 caught', bat.stdout) is not None,
        "planted loss -> counts_check exit %d (%s) | planted run-loss -> exit %d | unmutated -> exit %d | "
        "battery: %s" % (lost.returncode, [l for l in lost.stdout.split("\n") if "no longer stated" in l][:1],
                         lost2.returncode, own.returncode, bat.stdout.strip().split("\n")[0]))

    # ---- 5: the revised README declares the same three build-bound steps, and carries the foreign-build
    # measurement this round made -- the claim and the reading are the same sentence's neighbours.
    sec = readme[readme.index("## Which steps are read against the pinned build"):] \
        if "## Which steps are read against the pinned build" in readme else ""
    add("5", "the README declares the three build-bound steps and no longer calls every artefact exact",
        "Tolerance: exact" not in readme
        and sec.count("| 1/5 |") == 1 and sec.count("| 2/5 |") == 1 and sec.count("| 3/5 |") == 1
        and "**REPORTED**" in sec and "**RENDERED**" in sec and sec.count("**EXACT**") >= 2,
        "the tolerance section's rows: %s" % re.findall(r'\| (\d)/5 \|', sec))
    # The claim is read in the paragraph that MAKES it, not anywhere in the file: a probe over the whole text
    # is satisfied by a quoted instrument line elsewhere, and the first version of this check stayed green on
    # a plant that gutted the very sentence it names (the plant was inert -- R415's rule: a mutation proves
    # nothing until it is shown to change the property under test).
    i = flat.find("**Measured on a foreign build")
    para = flat[i:i + 900] if i >= 0 else ""
    add("5b", "the foreign-build paragraph names both builds, the verdict, the worst departure and the exit code",
        i >= 0 and "3.14.6" in para and "2.5.1" in para and "3.9.6" in para and "2.0.2" in para
        and "BUILD_BOUND" in para and "1.610e-16" in para and "exits **0**" in para,
        "the paragraph reads: %s" % para[:260])
    return all(ok for _, _, ok, _ in rows), rows


def report(pkg):
    ok, rows = checks(pkg)
    for i, what, good, ev in rows:
        print("%-4s %-78s %s\n     %s" % (i, what, "ok" if good else "NOT DISCHARGED", ev))
    n = sum(1 for _, _, g, _ in rows if g)
    print("\n%d of %d check(s) pass at their objects: (D) %s"
          % (n, len(rows), "DISCHARGED" if ok else "NOT DISCHARGED"))
    return 0 if ok else 1


def selftest():
    """The battery: re-introduce defect (D) one property at a time on scratch copies, and read the exit code."""
    pkg = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cases, allok = [], True

    def scratch():
        dst = os.path.join(tmpdir, "pkg")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(pkg, "artefacts", "assembly"), os.path.join(dst, "artefacts", "assembly"))
        for rel in ("README.md", "reproduce.sh", "manuscript.md"):
            shutil.copy(os.path.join(pkg, rel), os.path.join(dst, rel))
        shutil.copy(os.path.join(pkg, "artefacts", "results_digest.json"),
                    os.path.join(dst, "artefacts", "results_digest.json"))
        return dst

    def case(name, mutate, want):
        nonlocal allok
        dst = scratch()
        if mutate:
            mutate(dst)
        r = subprocess.run([PY, os.path.abspath(__file__), "--pkg", dst], capture_output=True, text=True)
        good = r.returncode == want
        allok = allok and good
        cases.append((name, want, r.returncode, good))

    def edit(rel, old, new, count=1):
        def apply(dst):
            fp = os.path.join(dst, rel)
            t = io.open(fp, encoding="utf-8").read()
            assert old in t, "plant not present in %s: %r" % (rel, old)
            out = t.replace(old, new, -1 if count == 0 else count)   # count=0 means ALL: str.replace's own
            # `count=0` replaces NOTHING, and a plant that changes no text is inert -- it would score the case
            # against an unmutated package and read as "the check missed it".  So the mutation is asserted.
            assert out != t, "plant made no change in %s: %r" % (rel, old)
            io.open(fp, "w", encoding="utf-8").write(out)
        return apply

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = tmp
        case("unmutated package", None, 0)
        case("(D) re-introduced: the digest step made the FIRST step, before the reported ones",
             lambda d: io.open(os.path.join(d, "reproduce.sh"), "w", encoding="utf-8").write(
                 io.open(os.path.join(pkg, "reproduce.sh"), encoding="utf-8").read().replace(
                     "2/5 results digest", "1/5 results digest", 1).replace(
                     "1/5 the two new instruments", "2/5 the two new instruments", 1)),
             1)
        case("(D) re-introduced: a second numbering basis appears (the assembly step renumbered 3/5)",
             lambda d: io.open(os.path.join(d, "reproduce.sh"), "w", encoding="utf-8").write(
                 io.open(os.path.join(pkg, "reproduce.sh"), encoding="utf-8").read().replace(
                     "=== 4/5 manuscript assembly", "=== 3/5 manuscript assembly", 1)),
             1)
        case("(D) re-introduced: the preamble's count of build-bound steps understated (three -> one)",
             edit("reproduce.sh", "PINNED BUILD: **three**", "PINNED BUILD: **one**"), 1)
        case("(D) re-introduced: the build-bound reading declared but never built (the comparator removed)",
             edit("reproduce.sh", "artefacts/assembly/build_bound.py json", "true # "), 1)
        case("a step header that declares no reading word",
             edit("reproduce.sh", "=== 3/5 figures (a rendering: reported, never a stop condition)",
                  "=== 3/5 figures"), 1)
        case("the README's foreign-build measurement removed (the build is no longer named)",
             edit("README.md", "3.14.6", "3.14.5", count=0), 1)
        case("the README's tolerance section removed (the under-declaration returns)",
             edit("README.md", "## Which steps are read against the pinned build",
                  "## Tolerance: exact -- byte-identical"), 1)
        case("the counts checker's two-sidedness removed (required rows made optional)",
             edit("artefacts/assembly/counts_check.py", 'REQUIRED = "required"', 'REQUIRED = "absent-design"'), 1)
    print("ROUND-3 VERIFIER SELFTEST -- %d case(s), %d caught" % (len(cases), sum(1 for c in cases if c[3])))
    for name, want, got, good in cases:
        print("  %-6s %-88s exit %d (want %d)" % ("ok" if good else "MISSED", name, got, want))
    print("SELFTEST: %s" % ("PASS" if allok else "FAIL"))
    return 0 if allok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    pkg = argv[argv.index("--pkg") + 1] if "--pkg" in argv else \
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return report(pkg)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
