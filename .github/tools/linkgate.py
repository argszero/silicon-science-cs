#!/usr/bin/env python3
"""linkgate_v1 - the tree's own cross-references, read as the renderer reads them.

The rule (README.md -> Links): *every cross-reference a tracked file makes is
read by someone who has this repository and not necessarily anything else, so
it must resolve here*.  This tool is that rule's instrument for its **first
form** - a markdown link target `](...)` - over the **set** of tracked markdown
carriers (`git ls-files '*.md'`).

Two things the tool does not decide, and says so:

* the rule's **second and third forms** - a `see X` pointer and a numbered
  reference - resolve only inside the namespace of a list the citing sentence
  or its carrier names.  Which list is meant is a read, not a computation, so
  those forms stay a read (op(4); README.md -> Links).
* a target resolves at the **linking file's own directory** - the renderer's
  base - never at the repository root.  Resolving from the root manufactures
  false BROKENs (`papers/README.md` -> `issue-42/manuscript.md`): the defect
  R265 caught in the first census instrument.

Class of one target, decided by form, every form counted and named:
  path         - everything else; resolved with os.path.exists at the base
  url          - carries a scheme (`https://...`, `mailto:`), another system's
  placeholder  - carries `<...>`, a form an author instantiates
  anchor       - starts with `#`, an in-page position (0 in this tree today)
  rooted       - starts with `/`, a repository-root path written as absolute
  empty        - no target at all

Usage:
  python3 .github/tools/linkgate.py            # report, exit 0
  python3 .github/tools/linkgate.py --check    # exit 1 if any path is broken
  python3 .github/tools/linkgate.py --selftest # run the tool's own cases

Run it from the repository root; the relative tool path resolves there.
"""

import os
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]*(?:\s[^)]*)?)\)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")


def repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def is_carrier(name):
    """The set's one membership rule: a markdown file.  A `.py` source that
    contains a `](...)`-shaped string is outside the set, not a broken link."""
    return name.endswith(".md")


def carriers(root):
    """The set: every tracked markdown file, read at the reader's own head."""
    out = subprocess.run(
        ["git", "-C", root, "ls-files", "*.md"],
        capture_output=True, text=True, check=True,
    )
    return sorted(p for p in out.stdout.splitlines() if is_carrier(p))


def classify(target):
    if not target:
        return "empty"
    if target.startswith("#"):
        return "anchor"
    if "<" in target or ">" in target:
        return "placeholder"
    if target.startswith("/"):
        return "rooted"
    if SCHEME.match(target) or target.startswith("//"):
        return "url"
    return "path"


def targets_in(text):
    """Every `](...)` target, in file order."""
    return [m.group(1) for m in LINK.finditer(text)]


def resolves(root, rel_file, target):
    bare = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not bare:
        return True  # an anchor-only target points inside the file itself
    base = os.path.dirname(os.path.join(root, rel_file))
    return os.path.exists(os.path.normpath(os.path.join(base, bare)))


def report(root, files=None, verbose=True):
    counts = {"path": 0, "url": 0, "placeholder": 0, "anchor": 0,
              "rooted": 0, "empty": 0}
    resolved, broken = 0, []
    files = carriers(root) if files is None else files
    for rel in files:
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            text = fh.read()
        for target in targets_in(text):
            kind = classify(target)
            counts[kind] += 1
            if kind == "path":
                if resolves(root, rel, target):
                    resolved += 1
                else:
                    broken.append((rel, target))
            elif kind == "rooted" and resolves(root, rel, target.lstrip("/")):
                resolved += 1
    total = sum(counts.values())
    paths = counts["path"] + counts["rooted"]
    if verbose:
        print("linkgate_v1 - the tree's markdown cross-references, resolved at "
              "the linking file's own directory")
        print("set: %d tracked markdown carriers (git ls-files '*.md') at the "
              "reader's head" % len(files))
        print("targets=%d links=%d resolved=%d broken=%d"
              % (total, paths, resolved, len(broken)))
        print("forms not read as links: url=%d placeholder=%d anchor=%d "
              "empty=%d rooted=%d"
              % (counts["url"], counts["placeholder"], counts["anchor"],
                 counts["empty"], counts["rooted"]))
        print("not decided here: a `see X` pointer and a numbered reference - "
              "the list they index is a read")
        for rel, target in broken:
            print("BROKEN %s -> %s" % (rel, target))
    return len(broken), total, paths, resolved, counts


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        def write(rel, body):
            full = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as fh:
                fh.write(body)

        write("b.md", "# b\n")
        write("c.md", "# c\n")
        write("sub/b.md", "# nested b\n")
        write("deep/x.md", "[a name the root holds](b.md)\n")
        write("note.py", "PAT = r\"['\\u2019-]\"  # )](x) is not a link\n")
        write("sub/a.md",
              "[sib](b.md)\n[up](../c.md)\n[gone](nope.md)\n"
              "[web](https://example.com/x)\n[form](figures/<file>)\n"
              "[here](#sec)\n")

        body = open(os.path.join(tmp, "sub/a.md"), encoding="utf-8").read()
        got = targets_in(body)
        by_form = {classify(t) for t in got}
        found = [t for t in got
                 if classify(t) == "path" and not resolves(tmp, "sub/a.md", t)]

        cases = [
            ("base_is_the_linking_files_directory",
             resolves(tmp, "sub/a.md", "b.md") is True),
            ("the_root_is_not_the_base",
             resolves(tmp, "deep/x.md", "b.md") is False),
            ("dotted_relative_target_resolves_upward",
             resolves(tmp, "sub/a.md", "../c.md") is True),
            ("missing_target_is_reported", found == ["nope.md"]),
            ("url_is_not_a_cross_reference", classify("https://e.com/x") == "url"),
            ("placeholder_form_is_not_a_cross_reference",
             classify("figures/<file>") == "placeholder"),
            ("anchor_only_target_is_named_by_its_own_form",
             classify("#sec") == "anchor"),
            ("the_class_names_every_form_it_reads",
             {"path", "url", "placeholder", "anchor"} <= by_form),
            ("non_markdown_carriers_are_outside_the_set",
             is_carrier("note.py") is False and is_carrier("sub/a.md") is True),
        ]
        ok = sum(1 for _, passed in cases if passed)
        for name, passed in cases:
            print("  %s %s" % ("ok  " if passed else "FAIL", name))
        print("selftest: %d/%d cases ok" % (ok, len(cases)))
        return 0 if ok == len(cases) else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    broken, _, _, _, _ = report(repo_root())
    if "--check" in argv:
        print("LINKGATE: %s" % ("FAIL" if broken else "PASS"))
        return 1 if broken else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
