#!/usr/bin/env python3
"""numgate_v1 - the tree's numbered references, by the form each one takes.

The rule (README.md -> Links):

    every cross-reference a tracked file makes is read by someone who has this
    repository and not necessarily anything else, so it must resolve *here*.
    ... A number is a position, and the rule is the set of the ways its list is
    identified - four, not the two one sentence states.

This tool is that rule's instrument for its **third form** - a **numbered
reference**.  A link is read by `.github/tools/linkgate.py` and a name by
`.github/tools/pointgate.py`; a number is read here.

Two classes of site, counted separately and never merged (the class a reading
admits is part of its count):

  carrier sites  read in a file `README.md` -> *Links* names - the journal's own
                 surfaces - where the form of the number fixes the **home** of
                 the list it indexes:

                   item N / step N / condition N   the list is **in this tree**
                   a section mark                  the package's own sections
                   #N                              the issue/PR namespace,
                                                   named by the form itself
                   op(N)                           the editor's checklist --
                                                   **outside this tree**
                   Rnnn                            the round record under
                                                   .emrg/** -- an attribution

  package sites  read in any other tracked file - a submission's own
                 materials.  Their numbers index **the citing file's own
                 lists** (the rule's first form), which are the package's
                 business and the reviewer's read, not the journal's: they are
                 counted and named, and no home is claimed for them.

The set is read off the tree (`git ls-files`), so a carrier added later joins by
being added - the set a census is taken over is part of its count (R396's census
read a set of seven it recalled, and could not see the tool R399 wrote inside
it).

What it does NOT read, and says so: **which position of that list** a number
means, and whether that position holds the requirement the reference *names*.
A number's list is enumerated here; *being in range is not agreeing*, and that
half stays a read.  The home printed for a carrier form is a property of the
**form**, stated in the table below; the tool does not decide, site by site,
whether a sentence named a different list - that is the sentence's own read
(README.md -> Links, the four identification forms).

The one form the rule forbids - a bare number into a list that lives only
outside this repository, `op(N)` - is what `--check` fails on; `#N` (the object
namespace) and `Rnnn` (an attribution, which dates the reading beside it) are
classes, not defects.

The instrument writes **no instance of any form it counts, except the
attribution `Rnnn` of its own header**: every fixture token in its `--selftest`
is built from parts at run time, so `numgate.py` is clean under its own check -
and its `--selftest` asserts that (a census of the tree's numbers that wrote one
would count itself).

Usage:
  python3 .github/tools/numgate.py            # report, exit 0
  python3 .github/tools/numgate.py --check    # exit 1 if the forbidden form is present
  python3 .github/tools/numgate.py --selftest # run the tool's own cases

Run it from the repository root; the relative tool path resolves there.
"""

import os
import re
import subprocess
import sys

# form          matcher                        class      the list it indexes
FORMS = [
    ("item N", re.compile(r"\bitem\s+\d+"),
     "tree", "README.md -> Quality bar"),
    ("step N", re.compile(r"\bstep\s+\d+"),
     "tree", "README.md -> Submission workflow"),
    ("condition N", re.compile(r"\bcondition\s+\d+"),
     "tree", ".github/REVIEW_TEMPLATE.md -> The two markers"),
    ("sec N", re.compile(r"\u00a7\d+(?:\.\d+)*"),
     "package", "a manuscript's own sections"),
    ("#N", re.compile(r"#\d+"),
     "object", "the journal's issue/PR namespace (the form names it)"),
    ("op(N)", re.compile(r"\bop\(\d+\)"),
     "outside", "the editor's checklist -- OUTSIDE this tree"),
    ("Rnnn", re.compile(r"\bR\d{3}\b"),
     "outside", "the round record under .emrg/** (an attribution, not a pointer)"),
]

# the one form whose list is in no tracked file and which is *not* self-naming
FORBIDDEN = {"op(N)"}

LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
CODE = re.compile(r"`([^`]+)`")


def repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def tracked(root):
    out = subprocess.run(["git", "-C", root, "ls-files"],
                         capture_output=True, text=True, check=True)
    return [p for p in out.stdout.splitlines() if p]


def links_section(text):
    """README.md -> Links, from its heading to the next `## ` heading."""
    m = re.search(r"(?m)^## Links[ \t]*$", text)
    if not m:
        return ""
    rest = text[m.end():]
    n = re.search(r"(?m)^## ", rest)
    return rest[:n.start()] if n else rest


def carriers(root):
    """The journal's own surfaces: the files `README.md` -> *Links* names.

    Read off that section - the path a bullet or the prose links to, where the
    file is tracked and is text - so a carrier named there joins by being named.
    """
    names = {"README.md"}
    sec = links_section(open(os.path.join(root, "README.md"),
                             encoding="utf-8").read())
    tracked_set = set(tracked(root))
    cand = [m.group(2) for m in LINK.finditer(sec)]
    cand += [m.group(1) for m in CODE.finditer(sec)]
    for c in cand:
        c = c.split("#")[0].strip()
        if c in tracked_set and c.endswith((".md", ".py")):
            names.add(c)
    return names


def sites(text):
    """Every numbered reference in `text`, by form, in file order.

    A site is the matched token; one line may carry several forms.  A tracked
    file that does not decode as text is outside the class: a number is written
    into text a reader reads.
    """
    out = []
    for label, rx, cls, home in FORMS:
        for m in rx.finditer(text):
            out.append((text.count("\n", 0, m.start()) + 1,
                        label, m.group(0).strip()))
    return sorted(out)


def classify(token):
    """The form of one token, or None if no form reads it."""
    for label, rx, _, _ in FORMS:
        if rx.fullmatch(token):
            return label
    return None


def scan(root):
    """Every site in the tree, split into the two classes of the reading."""
    car = carriers(root)
    per, pkg = {}, {}
    files = tracked(root)
    read = 0
    for f in files:
        p = os.path.join(root, f)
        if not os.path.exists(p):
            continue
        try:
            body = open(p, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        read += 1
        for ln, label, tok in sites(body):
            bucket = per if f in car else pkg
            bucket.setdefault(label, []).append((f, ln, tok))
    return per, pkg, car, read, len(files)


def report(root, verbose=True):
    per, pkg, car, read, total_files = scan(root)
    if verbose:
        sites_c = sum(len(v) for v in per.values())
        sites_p = sum(len(v) for v in pkg.values())
        print("numgate_v1 - the tree's numbered references, by the form "
              "each one takes")
        print("set: %d tracked files read as text (of %d, `git ls-files`); "
              "carriers: %d (README.md -> Links); forms: %d"
              % (read, total_files, len(car), len(FORMS)))
        print("sites=%d  carrier=%d  package=%d" % (sites_c + sites_p,
                                                    sites_c, sites_p))
        print("%-13s %7s %9s  %s" % ("form", "carrier", "carriers", "list home"))
        for label, _, cls, home in FORMS:
            hits = per.get(label, [])
            print("%-13s %7d %9d  %s"
                  % (label, len(hits), len({f for f, _, _ in hits}), home))
        print("package sites: %d over %d files - the citing file's own lists "
              "(the rule's first form; no home claimed here)"
              % (sites_p, len({f for v in pkg.values() for f, _, _ in v})))
        print("not read here: which position of the list a number means, and "
              "whether that position holds the requirement the reference names")
    return per, pkg


def check(per, pkg=None):
    """The verdict: the forbidden form is absent, and named where present."""
    rows = [(f, ln, tok) for label in FORBIDDEN for f, ln, tok in per.get(label, [])]
    if pkg is not None:
        rows += [(f, ln, tok) for label in FORBIDDEN
                 for f, ln, tok in pkg.get(label, [])]
    for f, ln, tok in sorted(set(rows)):
        print("OUTSIDE %s:%d %s - a number into a list no tracked file holds"
              % (f, ln, tok))
    return sorted(set(rows))


def _t(kind, n):
    """A fixture token built from parts: the instrument writes no instance of
    the forms it counts, so its own file is clean under its own check."""
    return {"item": "item %d", "step": "step %d", "condition": "condition %d",
            "sec": "\u00a7%d", "hash": "#%d", "op": "op(%d)",
            "R": "R%03d"}[kind] % n


def selftest():
    cases = []
    cases.append(("a_number_in_the_tree_is_read",
                  classify(_t("item", 11)) == "item N"
                  and classify(_t("step", 6)) == "step N"
                  and classify(_t("condition", 2)) == "condition N"))
    cases.append(("a_package_section_is_read_as_in_package",
                  classify(_t("sec", 4)) == "sec N"))
    cases.append(("the_object_namespace_is_read",
                  classify(_t("hash", 42)) == "#N"))
    cases.append(("the_forbidden_form_is_read_and_named",
                  classify(_t("op", 4)) == "op(N)" and "op(N)" in FORBIDDEN))
    cases.append(("an_attribution_is_read",
                  classify(_t("R", 399)) == "Rnnn"))
    cases.append(("a_form_no_carrier_writes_is_not_read",
                  classify("[12]") is None and classify("v1.2") is None))
    cases.append(("every_form_the_tool_reads_is_in_the_class",
                  {classify(_t(k, 1)) for k in
                   ("item", "step", "condition", "sec", "hash", "op", "R")}
                  == {l for l, _, _, _ in FORMS}))
    fixture = ("## Links\n\n- Registry: [`INSTANCES.md`](INSTANCES.md)\n"
               "- Gate: [`.github/tools/refgate.py`](.github/tools/refgate.py) "
               "-- counts entries\n- Archive: [`bk`](https://example.com/bk)\n")
    cases.append(("the_links_section_is_delimited",
                  "INSTANCES.md" in links_section(fixture)
                  and "Archive" in links_section(fixture)))
    root = repo_root()
    car = carriers(root)
    cases.append(("the_carrier_set_is_read_off_links",
                  "README.md" in car and "INSTANCES.md" in car
                  and ".github/tools/refgate.py" in car))
    cases.append(("the_set_is_the_tracked_files",
                  all(os.path.exists(os.path.join(root, f))
                      for f in tracked(root))))
    got = sites("see README.md -> workflow %s, %s, and %s\n"
                % (_t("step", 4), _t("op", 9), _t("hash", 50)))
    cases.append(("sites_are_found_by_form",
                  {label for _, label, _ in got} == {"step N", "op(N)", "#N"}))
    cases.append(("the_forbidden_form_makes_check_fail",
                  len(check({"op(N)": [("x.md", 1, _t("op", 9))]})) == 1
                  and check({"Rnnn": [("x.md", 1, _t("R", 399))]}) == []))
    cases.append(("the_two_classes_are_counted_apart",
                  len(check({}, {"op(N)": [("p.md", 1, _t("op", 9))]})) == 1))
    cases.append(("the_instrument_writes_only_its_own_attributions",
                  {label for _, label, _ in
                   sites(open(os.path.abspath(__file__), encoding="utf-8").read())}
                  <= {"Rnnn"}))
    ok = sum(1 for _, passed in cases if passed)
    for name, passed in cases:
        print("  %s %s" % ("ok  " if passed else "FAIL", name))
    print("selftest: %d/%d cases ok" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    per, pkg = report(repo_root())
    if "--check" in argv:
        bad = check(per, pkg)
        print("NUMGATE: %s" % ("FAIL" if bad else "PASS"))
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
