#!/usr/bin/env python3
"""envgate_v1 - the environment a package *declares*, read against the modules its code *imports*.

The rule (README.md -> Quality bar item 5, workflow step 4, and the paragraph
*A tolerance is read against a build*): a package's one-command reproduction owes
its environment twice.  The **version** half - every name it declares must carry a
version, or the declared tolerance is one no reader can test - is read by the
paragraph named above and by the reviewer.  This tool reads the other half, which
had no instrument: **the declared set of names must be as wide as the set the code
imports.**

Why the second half is its own defect and not a case of the first: a declared set
can pin every version it names and still be narrower than the code.  Measured
twice - `papers/issue-128`'s `spike_v3.py` imports `scipy.optimize.milp` while its
README named numpy and matplotlib (R548), and `papers/issue-142`'s
`spike_ident_v5.py:54` imports `scipy.signal` while its README named CPython 3.9.6,
numpy 2.0.2 and matplotlib 3.9.4 - every version it named was right, and the run
died with `ModuleNotFoundError` in the very environment the spec declares (R590).
A version pin cannot be missing for a name that is never mentioned.

**What this tool reads, and what it does not.**

  * the **used set** is computed: every `.py` file under the package directory
    (recursively, minus `__pycache__` and any `research/` workspace) is parsed with
    `ast`, and every level-0 `import X` / `from X.Y import z` contributes the
    top-level name `X`.
  * a used name is **local**, not a dependency, when it resolves to a `.py` file or
    a package directory *inside* the package - at its root or in any subdirectory,
    since a script that runs from `artefacts/` imports its neighbours there by name
    (`spike_ident_v6` importing `spike_ident_v5`; `predsplit_v1` importing
    `boundary_v1` one directory down) - one package, not a dependency.
  * a used name is **stdlib** when `sys.stdlib_module_names` carries it (CPython
    3.10+) or, on 3.9, when the standard library's own directories carry
    `<name>.py`, `<name>/`, or `<name>.*.so` — in `<dir>` or in its `lib-dynload/`,
    because the compiled extension modules (`math`, `unicodedata`, `_ssl`) live there
    and are as much the interpreter's own as the pure-Python ones.  The second test is
    a path test and needs the module **installed nowhere**, which is what makes the
    tool usable on a runner that does not have the package's dependencies.
  * **everything else is third-party**, and that is the set the declaration is
    read against.
  * the **declared set** is not parsed out of prose, because prose has no schema.
    The read is one-directional and mechanical: *for each used third-party name, is
    that name written anywhere in the package's declared-environment carriers?*
    The carriers are read off the package root - `README.md` (the spec carrier the
    submission checklist names), the one-command script, and the dependency-manifest
    filenames the ecosystem uses - and the tool **prints which of them exist and
    the `file:line` where each name was found**, so the editor reads the evidence
    rather than the verdict.  A name mentioned only in passing counts as named:
    that is the heuristic's known direction of error, and it is stated here rather
    than hidden, because the alternative - a parser that guesses which sentence is
    the declaration - fails in both directions and cannot be re-read.

**What this tool does not decide.**  It does not read versions: *named* and
*versioned* are two debts, and the second is `README.md` -> *A tolerance is read
against a build*.  It does not decide whether the named environment is the one the
spec runs in (that needs a run).  It does not know every distribution-to-import
alias - `sklearn` is `scikit-learn`, `cv2` is `opencv-python` - so it carries a
short stated alias table and prints it; a name whose alias is not in that table is
reported as missing, and the editor reads it against the declaration.

Classes, every one counted and named:
  third-party  - imported, not stdlib, not local: the set the declaration must cover
  local        - resolves inside the package (a sibling instrument)
  stdlib       - the interpreter's own
  unknown      - the standard library directory could not be located; reported apart
                 and never merged into either side

**What the verdict is about is the set it read.**  An empty set is `NOT RUN`, never
`PASS`: a package that ships no Python has nothing to compare, and the string a real
pass prints must not also be the string printed for a comparison that never happened.
A package with no declared-environment carrier at its root is `NOT RUN` for the same
reason - there is nothing to read the used set against.

Usage:
  python3 .github/tools/envgate.py papers/issue-<N>            # report, exit 0/1
  python3 .github/tools/envgate.py papers/issue-<N> --json      # same, machine-readable
  python3 .github/tools/envgate.py --selftest                   # the tool's own plants

Exit: 0 = PASS (or NOT RUN, with its reason) · 1 = FAIL (names the missing modules)
      · 2 = NOT RUN when the editor asked for a verdict on a set that is empty.
"""
import ast
import json
import os
import re
import subprocess
import sys
import sysconfig
import tempfile

# The dependency-manifest filenames the ecosystem uses.  Read off the package root
# and printed with present/absent, so the carrier set is visible and not recalled.
MANIFESTS = ["README.md", "reproduce.sh", "requirements.txt", "requirements-dev.txt",
             "environment.yml", "environment.yaml", "pyproject.toml", "setup.py"]

# Distribution name differs from the import name for these; the table is short on
# purpose and printed in the report, so a name outside it is a read and not a guess.
ALIASES = {
    "sklearn": ["scikit-learn"],
    "cv2": ["opencv-python", "opencv"],
    "PIL": ["pillow"],
    "yaml": ["pyyaml", "py-yaml"],
    "skimage": ["scikit-image"],
    "bs4": ["beautifulsoup4"],
    "dateutil": ["python-dateutil"],
    "dotenv": ["python-dotenv"],
    "mpl_toolkits": ["matplotlib"],
    "pkg_resources": ["setuptools"],
    "google": ["google"],
}

SKIP_DIRS = {"__pycache__", ".git", "research", ".venv", "venv"}


def _stdlib_dirs():
    """The interpreter's own library roots — `stdlib` and, beside it, `platstdlib`."""
    out = []
    for key in ("stdlib", "platstdlib"):
        path = sysconfig.get_paths().get(key)
        if path and os.path.isdir(path) and path not in out:
            out.append(path)
    return out


def _stdlib_entries(directory):
    """Top-level names a library root provides, extension modules included.

    A pure-Python module is `<dir>/<name>.py` and a package is `<dir>/<name>/`, but
    `math` and `unicodedata` are neither: they are compiled extension modules, and on
    a framework build they sit in `<dir>/lib-dynload/` as `<name>.cpython-39-darwin.so`.
    A listing that reads only `.py` files and directories therefore reports the
    interpreter's own modules as third-party and asks the author to declare them —
    measured at R591 against `papers/issue-126`, whose `math` and `unicodedata` were
    named MISSING by exactly that window.
    """
    found = set()
    for entry in os.listdir(directory):
        base, ext = os.path.splitext(entry)
        if ext in (".py", ".so", ".pyd"):
            found.add(base.split(".")[0])
        elif os.path.isdir(os.path.join(directory, entry)) and not entry.startswith(
                ("site-packages", "dist-packages", "config-", "lib-dynload")):
            found.add(entry)
    dynload = os.path.join(directory, "lib-dynload")
    if os.path.isdir(dynload):
        for entry in os.listdir(dynload):
            found.add(entry.split(".")[0])
    return found


def stdlib_names():
    """Return (set_of_stdlib_top_level_names, instrument) or (None, reason)."""
    names = getattr(sys, "stdlib_module_names", None)
    if names is not None:
        return set(names) | set(sys.builtin_module_names), "sys.stdlib_module_names"
    # CPython 3.9 has no stdlib_module_names; the library's own directories answer
    # the same question without importing anything.
    dirs = _stdlib_dirs()
    if not dirs:
        return None, "sysconfig reported no stdlib directory"
    found = set(sys.builtin_module_names)
    try:
        for directory in dirs:
            found |= _stdlib_entries(directory)
    except OSError as exc:                                     # pragma: no cover
        return None, "cannot list the stdlib directory: %s" % exc
    return found, "the stdlib directories (%s)" % ", ".join(dirs)


def scripts(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(".py"):
                out.append(os.path.join(dirpath, name))
    return out


def imports_of(path):
    """[(top_level_name, lineno)] for every level-0 import in the file."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        src = fh.read()
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as exc:
        return None, "cannot parse %s: %s" % (path, exc)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hits.append((alias.name.split(".")[0], node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level:          # a relative import is inside the package
                continue
            if node.module:
                hits.append((node.module.split(".")[0], node.lineno))
    return hits, None


def local_modules(root, found_scripts):
    """Top-level names that resolve to something inside the package.

    A package's instruments are not all at its root: `papers/issue-50` keeps its
    estimators in `artefacts/`, and `artefacts/predsplit_v1.py` imports its neighbour
    as `import boundary_v1` because the running script's own directory is on
    `sys.path`.  So the set is every module stem and every directory name under the
    package — read off the package's own file list, needing no import and no installed
    dependency.  It errs toward *local*, which is the direction that cannot turn a
    sibling into a demand on the author's declaration.
    """
    names = set()
    for path in found_scripts:
        rel = os.path.relpath(path, root)
        parts = rel.split(os.sep)
        names.add(os.path.splitext(parts[-1])[0])
        names.update(parts[:-1])
    return names


def carriers(root):
    out = []
    for name in MANIFESTS:
        path = os.path.join(root, name)
        out.append((name, path if os.path.isfile(path) else None))
    return out


def find_name(name, carrier_paths, aliases):
    """First (file, lineno, text) naming `name` or one of its aliases, else None."""
    spellings = [name] + aliases.get(name, [])
    pats = [re.compile(r"(?<![\w.])" + re.escape(s) + r"(?![\w])", re.I) for s in spellings]
    for label, path in carrier_paths:
        if not path:
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, 1):
                    if any(p.search(line) for p in pats):
                        return (os.path.basename(path), i, line.strip()[:160])
        except OSError:
            continue
    return None


def read_package(root):
    """Return the report dict this tool prints.  No printing here."""
    found = scripts(root)
    report = {"root": root, "scripts": found, "used": {}, "declared": {}, "carriers": [],
              "missing": [], "classes": {"third-party": [], "local": [], "stdlib": [],
                                         "unknown": []}, "instrument": None,
              "reason": None, "verdict": None}
    if not found:
        report["verdict"] = "NOT RUN"
        report["reason"] = "the package ships no Python - nothing imports anything"
        return report

    stdlib, instrument = stdlib_names()
    report["instrument"] = instrument
    if stdlib is None:
        report["verdict"] = "NOT RUN"
        report["reason"] = "cannot classify imports: %s" % instrument
        return report

    local = local_modules(root, found)
    seen = {}
    for path in found:
        hits, err = imports_of(path)
        if hits is None:
            report["verdict"] = "NOT RUN"
            report["reason"] = err
            return report
        for name, lineno in hits:
            seen.setdefault(name, []).append(
                ("%s:%d" % (os.path.relpath(path, root), lineno)))
    report["used"] = seen

    for name in sorted(seen):
        if name in stdlib:
            report["classes"]["stdlib"].append(name)
        elif name in local:
            report["classes"]["local"].append(name)
        elif _in_stdlib_dir(name):
            report["classes"]["stdlib"].append(name)
        else:
            report["classes"]["third-party"].append(name)

    carriers_found = carriers(root)
    report["carriers"] = [(label, bool(path)) for label, path in carriers_found]
    live = [(label, path) for label, path in carriers_found if path]

    if not live:
        report["verdict"] = "NOT RUN"
        report["reason"] = ("no declared-environment carrier at the package root "
                            "(looked for: %s)" % ", ".join(MANIFESTS))
        return report

    for name in report["classes"]["third-party"]:
        hit = find_name(name, live, ALIASES)
        report["declared"][name] = hit
        if hit is None:
            report["missing"].append(name)

    report["verdict"] = "FAIL" if report["missing"] else "PASS"
    return report


def _in_stdlib_dir(name):
    """Fallback used when sys.stdlib_module_names is absent (CPython 3.9)."""
    for directory in _stdlib_dirs():
        try:
            if name in _stdlib_entries(directory):
                return True
        except OSError:                                        # pragma: no cover
            continue
    return False


def render(report, as_json=False):
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print("envgate_v1 - the declared environment read against the modules the code imports")
    print("root: %s" % report["root"])
    if report["verdict"] == "NOT RUN":
        print("ENVGATE: NOT RUN - %s" % report["reason"])
        return
    print("set: %d Python file(s) parsed with ast · classifier: %s"
          % (len(report["scripts"]), report["instrument"]))
    print("carriers read (package root): %s"
          % ", ".join("%s%s" % (label, "" if present else " (absent)")
                      for label, present in report["carriers"]))
    print("classes: third-party=%d local=%d stdlib=%d"
          % (len(report["classes"]["third-party"]), len(report["classes"]["local"]),
             len(report["classes"]["stdlib"])))
    if report["classes"]["local"]:
        print("  local (sibling modules, not dependencies): %s"
              % ", ".join(report["classes"]["local"]))
    if not report["classes"]["third-party"]:
        print("used: 0 third-party module(s) - the package imports only the stdlib "
              "and its own modules")
        print("ENVGATE: PASS")
        return
    print("third-party module          first import              declared at")
    for name in report["classes"]["third-party"]:
        where = report["used"].get(name, ["?"])[0]
        hit = report["declared"].get(name)
        noted = "MISSING" if hit is None else "%s:%d" % (hit[0], hit[1])
        print("  %-26s %-25s %s" % (name, where, noted))
    if report["missing"]:
        print("MISSING: %d of %d third-party module(s) named nowhere in the declared "
              "carriers: %s"
              % (len(report["missing"]), len(report["classes"]["third-party"]),
                 ", ".join(report["missing"])))
        print("ENVGATE: FAIL")
    else:
        print("ENVGATE: PASS")


# --------------------------------------------------------------------------- plants


PLANT = {
    "declared-everything": {
        "README.md": "**Environment**: CPython 3.9.6 with numpy 2.0.2 and matplotlib 3.9.4.\n",
        "a.py": "import numpy\nimport matplotlib.pyplot as plt\nprint(numpy.__version__)\n",
    },
    "missing-scipy": {                      # the #142 shape, dotted ImportFrom included
        "README.md": "**Environment**: CPython 3.9.6 with numpy 2.0.2 and matplotlib 3.9.4.\n",
        "a.py": "import numpy\nfrom scipy.signal import lfilter\n",
    },
    "declared-in-the-script-only": {
        "reproduce.sh": "# environment: numpy 2.0.2\npython3 a.py\n",
        "a.py": "import numpy\n",
    },
    "stdlib-only": {
        "README.md": "**Environment**: CPython 3 standard library only.\n",
        "a.py": "import json, os\nfrom pathlib import Path\n",
    },
    "stdlib-extension-modules": {            # math/unicodedata are compiled, not .py
        "README.md": "**Environment**: CPython 3 standard library only.\n",
        "a.py": "import math\nfrom unicodedata import normalize\n",
    },
    "no-python": {
        "README.md": "**Environment**: none needed; bash only.\n",
        "reproduce.sh": "echo hi\n",
    },
    "no-carrier": {
        "a.py": "import numpy\n",
    },
    "sibling-import": {
        "README.md": "**Environment**: numpy 2.0.2\n",
        "v1.py": "import numpy\n",
        "v6.py": "import v1\nimport numpy\n",
    },
    "sibling-in-subdirectory": {             # issue-50's shape: artefacts/*.py
        "README.md": "**Environment**: numpy 2.0.2\n",
        "artefacts/base_v1.py": "import numpy\n",
        "artefacts/run_v2.py": "import base_v1\nimport numpy\n",
    },
    "alias-declared": {
        "README.md": "**Environment**: scikit-learn 1.5.0\n",
        "a.py": "from sklearn.linear_model import Ridge\n",
    },
    "passing-mention-counts": {             # documents the heuristic's error direction
        "README.md": "**Environment**: numpy 2.0.2.  Unlike scipy, numpy is enough.\n",
        "a.py": "import numpy\nfrom scipy import stats\n",
    },
}


def _run(root):
    """Run the tool as the reader does, in a child process, and return its output."""
    here = os.path.abspath(__file__)
    proc = subprocess.run([sys.executable, here, root],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout


def selftest():
    expect = {
        "declared-everything": ("PASS", 0),
        "missing-scipy": ("FAIL", 1),
        "declared-in-the-script-only": ("PASS", 0),
        "stdlib-only": ("PASS", 0),
        "stdlib-extension-modules": ("PASS", 0),
        "no-python": ("NOT RUN", 2),
        "no-carrier": ("NOT RUN", 2),
        "sibling-import": ("PASS", 0),
        "sibling-in-subdirectory": ("PASS", 0),
        "alias-declared": ("PASS", 0),
        "passing-mention-counts": ("PASS", 0),
    }
    cases, ok = [], 0
    tmp = tempfile.mkdtemp(prefix="envgate-selftest-")
    for label, files in PLANT.items():
        root = os.path.join(tmp, label)
        os.makedirs(root)
        for name, text in files.items():
            target = os.path.join(root, name)
            parent = os.path.dirname(target)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent)
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(text)
        code, out = _run(root)
        verdict = "NOT RUN" if "NOT RUN" in out else ("FAIL" if "FAIL" in out else "PASS")
        want, want_code = expect[label]
        good = verdict == want and code == want_code
        # a plant must also name the member it caught, not only the verdict
        if label == "missing-scipy" and "scipy" not in out:
            good = False
        if label == "no-carrier" and "no declared-environment carrier" not in out:
            good = False
        if label == "stdlib-extension-modules" and "third-party=0" not in out:
            good = False
        if label == "sibling-in-subdirectory" and "third-party=1" not in out:
            good = False
        cases.append((label, good, "%s/exit %d (want %s/exit %d)"
                      % (verdict, code, want, want_code)))
        ok += 1 if good else 0
    # the negative control: the same plant read with its declaration widened
    root = os.path.join(tmp, "missing-scipy")
    with open(os.path.join(root, "README.md"), "a", encoding="utf-8") as fh:
        fh.write("and scipy 1.13.1 for the filter step.\n")
    code, out = _run(root)
    good = code == 0 and "ENVGATE: PASS" in out
    cases.append(("missing-scipy + declaration widened -> PASS", good,
                  "exit %d" % code))
    ok += 1 if good else 0
    for label, good, detail in cases:
        print("  [%s] %-46s %s" % ("ok" if good else "FAIL", label, detail))
    print("selftest: %d/%d cases ok" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print("usage: envgate.py <package-dir> [--json] | --selftest", file=sys.stderr)
        return 2
    root = args[0]
    if not os.path.isdir(root):
        print("envgate: %s is not a directory" % root, file=sys.stderr)
        return 2
    report = read_package(root)
    render(report, as_json)
    if report["verdict"] == "PASS":
        return 0
    if report["verdict"] == "FAIL":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
