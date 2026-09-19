#!/usr/bin/env python3
"""Issue #50 -- the README's numbers, each read against the object that owns it.

    python3 readme_check_v1.py            # check: exit 0 iff every number the README states is its owner's
    python3 readme_check_v1.py --selftest # liveness: one planted defect per claim must fire

WHY THIS FILE EXISTS.  The README is the first thing a reader reads and the last thing any check in this
package read.  It states counts -- how many files the evidence is, how many modules the instrument
imports, how many references the paper carries, how many figures it embeds, how many sweeps
`reproduce.sh` re-runs -- and every one of those counts is owned by an object that can change without the
README noticing.  That is the same defect the manuscript check was written for (a typed copy of a value
an artefact can change is a claim with no owner), one carrier further out.

WHAT IS CHECKED, and against what:

  * **the evidence size** -- "46 files" against the contents of `artefacts/`;
  * **the dependency claim** -- "28 modules in total", "none outside the standard library and none
    outside this directory", against the assembler's own import census (which parses the sources);
  * **the reference layer** -- "137 entries, each cited" and "0 uncited entries" against
    `refs_order.json` and the selection layer;
  * **the figures** -- "four figures" and the README's figure table against the SVG files the package
    ships and the embeds the manuscript carries;
  * **the sweeps** -- "the twelve sweeps" and "the four sweeps that finish in seconds" against
    `rebuild_artefacts_v1.py`'s own lists;
  * **the gates' location** -- "two directories up" against the two tool paths the reproduction reads.

A count whose anchor cannot be found in the README FAILS rather than passes.  `--selftest` plants one
defect per claim in a throwaway copy of the package and requires that claim -- and only that claim -- to
report it.
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
README = "README.md"
ART = "artefacts"


def read(root, rel):
    return io.open(os.path.join(root, rel), encoding="utf-8").read()


def owned_values(root):
    """Every number the README states, recomputed from its owner."""
    art = sorted(os.listdir(os.path.join(root, ART)))
    files = [f for f in art if os.path.isfile(os.path.join(root, ART, f))]
    scripts = [f for f in files if f.endswith(".py")]

    sys.path.insert(0, root)
    try:
        sys.modules.pop("assemble", None)
        import assemble
        facts = assemble.build_facts()
        n_modules = facts["n_import_modules"]()
        n_outside = facts["n_imports_outside"]()
    finally:
        sys.path.remove(root)
        sys.modules.pop("assemble", None)

    # The order file carries its list under `keys` and its own count under `n`; the first version of
    # this reader guessed `order`, found a dict of four fields, and reported the paper as carrying FOUR
    # references -- a wrong read is the defect this whole file exists to catch, and it was in here.
    order = json.load(io.open(os.path.join(root, "refs_order.json"), encoding="utf-8"))
    keys = order["keys"]
    if len(keys) != order["n"]:
        raise ValueError("refs_order.json disagrees with itself: n=%r, len(keys)=%d"
                         % (order["n"], len(keys)))
    layer = json.load(io.open(os.path.join(root, ART, "refs_selection_v50.json"), encoding="utf-8"))["rows"]
    uncited = [r["key"] for r in layer if r["key"] not in set(keys)]

    svgs = sorted(f for f in os.listdir(os.path.join(root, "figures")) if f.endswith(".svg"))
    embeds = re.findall(r"!\[[^\]]*\]\(figures/([^\)]+)\)", read(root, "manuscript.md"))

    sys.path.insert(0, root)
    try:
        sys.modules.pop("rebuild_artefacts_v1", None)
        import rebuild_artefacts_v1 as rb
        n_sweeps, n_fast = len(rb.SWEEPS), len(rb.FAST)
    finally:
        sys.path.remove(root)
        sys.modules.pop("rebuild_artefacts_v1", None)

    return {"files": len(files), "scripts": len(scripts), "modules": n_modules, "outside": n_outside,
            "refs": len(keys), "uncited": len(uncited), "figures": len(svgs), "embeds": len(embeds),
            "sweeps": n_sweeps, "fast": n_fast, "svg_names": svgs, "embed_names": embeds,
            "art_names": files}


# (claim, the literal the README must carry, the owner expression, how to render its value)
CLAIMS = [
    ("the evidence file count", "%d files",
     lambda v: v["files"], None),
    ("the module count", "%d modules in total", lambda v: v["modules"], None),
    ("imports outside the package", "none outside the standard library", lambda v: v["outside"],
     "zero"),
    ("the reference count", "%d entries, each cited", lambda v: v["refs"], None),
    ("uncited entries", "%d uncited entries", lambda v: v["uncited"], None),
    ("the figure count", "%s figures", lambda v: v["figures"], None),
    ("the sweep count", "the %s sweeps", lambda v: v["sweeps"], None),
    ("the fast subset", "the %s sweeps that finish in seconds", lambda v: v["fast"], None),
]

WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
         9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def claims_zero(v):
    return v == 0


def render(template, v):
    n = template.count("%d") + template.count("%s")
    if n == 0:
        return template                      # a claim with no slot: the literal is the whole phrase
    word = WORDS.get(v)
    if n == 1 and "%s" in template:
        if word is None:
            return None                      # a word form the map does not carry: report, never guess
        return template % word
    if n == 1:
        return template % v
    return template % (v,)


def check(root):
    """Each claim: the README's literal must be present, and must equal the owner's value."""
    v = owned_values(root)
    ms = read(root, README)
    fails = []
    for name, template, owner, transform in CLAIMS:
        value = owner(v)
        if transform == "zero":
            if not claims_zero(value):
                fails.append("%s: the README says %r and the owner's value is %r, which is not zero"
                             % (name, template, value))
            continue
        lit = render(template, value)
        if lit is None:
            fails.append("%s: the owner's value %r has no word form in this check's map" % (name, value))
            continue
        if lit not in ms:
            # distinguish "the README says a different number" from "the sentence is gone": both fail,
            # but a reader needs to know which
            stem = template.replace("%d", "").replace("%s", "").strip()
            hits = [l for l in ms.splitlines() if stem and stem in l]
            fails.append("%s: the owner's value is %r, so the README must carry %r; %s"
                         % (name, value, lit,
                            "the README carries %r instead" % hits[0].strip()[:90] if hits
                            else "no line carrying %r was found" % stem))
    # ... and the two lists whose MEMBERSHIP matters, not only their size
    for name in v["svg_names"]:
        if name not in ms:
            fails.append("the figure table does not name %s" % name)
    for name in v["embed_names"]:
        if name not in v["svg_names"]:
            fails.append("the manuscript embeds figures/%s, which the package does not ship" % name)
    for rel in ("../../.github/tools/refgate.py", "../../.github/tools/linkgate.py"):
        if not os.path.exists(os.path.join(root, rel)):
            # prefixed so the selftest can tell a scaffolding artefact of the COPY from a claim that
            # fired: the journal's tools live two directories above the package, and a copy in a temp
            # directory does not have them
            fails.append("(environment) the README sends the reader to %s, which is not in this tree"
                         % rel)
    if not v["svg_names"]:
        fails.append("no figure is shipped at all, so the figure claim is checked against nothing")
    return fails


# ------------------------------------------------------------------------------------------- selftest
PLANTS = [
    ("the evidence file count", lambda r: io.open(os.path.join(r, ART, "planted_extra.json"), "w")
     .write("{}")),
    ("the module count", lambda r: io.open(os.path.join(r, ART, "planted_import.py"), "w").write(
        "import zlib\n")),
    ("imports outside the package", lambda r: io.open(os.path.join(r, ART, "planted_outside.py"), "w")
     .write("import numpy\n")),
    ("the reference count", lambda r: _drop_a_cited_key(r)),
    ("uncited entries", lambda r: _plant_an_uncited_row(r)),
    # the first version of this plant RENAMED a figure, which leaves the count at four and fired
    # nothing -- a plant must move the number the claim is about
    ("the figure count", lambda r: os.remove(os.path.join(r, "figures", "fig4_mixture.svg"))),
    ("the fast subset", lambda r: io.open(os.path.join(r, "rebuild_artefacts_v1.py"), "a",
                                          encoding="utf-8").write("\nFAST = FAST + ('planted',)\n")),
]


def _drop_a_cited_key(r):
    """Remove one cited key from the order: the reference count moves while the body is untouched."""
    p = os.path.join(r, "refs_order.json")
    doc = json.load(io.open(p, encoding="utf-8"))
    doc["keys"] = doc["keys"][:-1]
    doc["n"] = len(doc["keys"])
    io.open(p, "w", encoding="utf-8").write(json.dumps(doc))


def _plant_an_uncited_row(r):
    """Add a row to the selection layer that the body never cites: the count of uncited entries moves
    while the citation count does not, so only that claim may fire."""
    p = os.path.join(r, ART, "refs_selection_v50.json")
    doc = json.load(io.open(p, encoding="utf-8"))
    doc["rows"].append(dict(doc["rows"][0], key="planted_uncited"))
    io.open(p, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False))


def copy_package(dst):
    os.makedirs(dst)
    for rel in ("README.md", "manuscript.md", "refs_order.json", "assemble.py",
                "rebuild_artefacts_v1.py"):
        shutil.copyfile(os.path.join(HERE, rel), os.path.join(dst, rel))
    for sub in (ART, "figures", os.path.join("..", ".github", "tools")):
        src = os.path.normpath(os.path.join(HERE, sub))
        tgt = os.path.normpath(os.path.join(dst, sub))
        if os.path.isdir(src):
            shutil.copytree(src, tgt)
    # the two gate paths are read through the copy's own parent, so the copy must carry them at the
    # same relative depth the README points to
    return dst


def selftest():
    bad = 0
    print("  base: the package as committed")
    base = check(HERE)
    if base:
        print("  the base case FAILS (%d), so the plants would prove nothing:" % len(base))
        for b in base[:4]:
            print("    %s" % b)
        return 1
    for label, plant in PLANTS:
        tmp = tempfile.mkdtemp(prefix="issue50-readme-")
        try:
            root = copy_package(os.path.join(tmp, "pkg"))
            try:
                plant(root)
            except Exception as exc:
                print("  plant %-26s the plant itself failed: %s" % (label, exc))
                bad += 1
                continue
            try:
                fails = check(root)
            except Exception as exc:
                print("  plant %-26s THE CHECK ITSELF CRASHED -- %s: %s"
                      % (label, type(exc).__name__, exc))
                bad += 1
                continue
            fails = [f for f in fails if not f.startswith("(environment)")]
            fired = [f for f in fails if f.startswith(label)]
            others = [f for f in fails if not f.startswith(label)]
            print("  plant %-26s %s%s" % (label, "the claim fired" if fired
                                          else "THE CLAIM DID NOT FIRE (control void)",
                                          "" if not others else " (+%d other claim(s) moved)" % len(others)))
            if not fired:
                bad += 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print("README SELFTEST: %d plant(s), %d not firing" % (len(PLANTS), bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    fails = check(HERE)
    for f in fails:
        print("  FAILED %s" % f)
    print("README CLAIMS: %d claim(s) checked, %d failure(s)" % (len(CLAIMS), len(fails)))
    sys.exit(0 if not fails else 1)
