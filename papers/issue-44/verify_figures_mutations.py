#!/usr/bin/env python3
"""Issue #44 -- attack the figure verifier, and report which check fires.

    python3 verify_figures_mutations.py

A check that never fires is decoration.  This script copies the package to a scratch
directory, mutates the copy one defect at a time, runs `verify_figures.py` there, and
records which check caught it.  The baseline (the unmutated copy) must come out clean, or
the harness is measuring itself.

Two kinds of mutation:

* PIPELINE mutations change a source file in the copy -- a plotted array, an artefact, a
  label, the manifest, a committed PNG -- and require the verifier to exit non-zero and to
  name the check that caught it.
* PREDICATE controls call the verifier's own functions on a synthetic input that violates
  exactly one property, for the properties a real render cannot be made to violate.

The pixel audit is a BACKSTOP, and its power is worth stating exactly: an emptied series is
caught by the artist digest, because the numbers read back off the axes change; the pixel
audit catches the cases a digest cannot see, such as an artist that fails to draw at all.

Exit status carries the verdict: 0 only if the baseline is clean, every mutation fires, and
every named check is the one that fires.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = ("make_figures.py", "verify_figures.py", "canonical_runner.py", "reproduce.sh",
       "canonical_results.json", "run.log",
       "results_v0.json", "results_v1.json", "results_v2.json", "results_v3.json",
       "results_v4.json")
FIGDIR = "figures"


def stage(dst):
    for name in PKG:
        shutil.copy2(os.path.join(HERE, name), os.path.join(dst, name))
    shutil.copytree(os.path.join(HERE, FIGDIR), os.path.join(dst, FIGDIR))


def run_verify(d):
    p = subprocess.run([sys.executable, "verify_figures.py"], cwd=d,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True)
    return p.returncode, p.stdout


def edit(path, old, new, count=1):
    with io.open(path, encoding="utf-8") as fh:
        t = fh.read()
    if t.count(old) != count:
        raise AssertionError("anchor fired %d times in %s" % (t.count(old), path))
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(t.replace(old, new, count))


# ------------------------------------------------------------------ mutations
def m_series(d):
    """A plot whose DATA changed while every artefact stayed byte-identical."""
    edit(os.path.join(d, "make_figures.py"),
         '        ax[1].plot([r["k"] for r in rs], [r["error"] for r in rs], "o-", ms=3.0, lw=0.9,',
         '        ax[1].plot([r["k"] for r in rs], [r["error"] * 1.001 for r in rs], "o-", ms=3.0, lw=0.9,')
    return "series digest"


def m_source(d):
    """An artefact changed in a key no figure plots."""
    p = os.path.join(d, "results_v0.json")
    o = json.load(io.open(p, encoding="utf-8"))
    o["n_mc"] = o["n_mc"] + 1
    io.open(p, "w", encoding="utf-8").write(json.dumps(o, indent=2, sort_keys=True))
    return "source artefact digests unchanged"


def m_label(d):
    """A label the caption promises is no longer drawn."""
    edit(os.path.join(d, "make_figures.py"),
         '"perfect prediction")', '"")')
    return "draws 'perfect prediction'"


def m_png(d):
    """A committed PNG that no longer matches its manifest entry."""
    p = os.path.join(d, FIGDIR, "fig3_rule.png")
    with io.open(p, "ab") as fh:
        fh.write(b"\x00")
    return "committed PNG matches its manifest entry"


def m_manifest(d):
    """A manifest that lost a figure."""
    p = os.path.join(d, FIGDIR, "manifest.json")
    o = json.load(io.open(p, encoding="utf-8"))
    o["figures"] = o["figures"][:-1]
    io.open(p, "w", encoding="utf-8").write(json.dumps(o, indent=2, sort_keys=True))
    return "figure list unchanged"


def m_caption(d):
    """A figure whose caption went missing."""
    p = os.path.join(d, FIGDIR, "manifest.json")
    o = json.load(io.open(p, encoding="utf-8"))
    o["figures"][2]["caption"] = ""
    io.open(p, "w", encoding="utf-8").write(json.dumps(o, indent=2, sort_keys=True))
    return "every figure has a caption"


def m_build(d):
    """NOT a defect: a different matplotlib build must be reported, not failed."""
    p = os.path.join(d, FIGDIR, "manifest.json")
    o = json.load(io.open(p, encoding="utf-8"))
    o["matplotlib"] = "0.0-not-this-build"
    io.open(p, "w", encoding="utf-8").write(json.dumps(o, indent=2, sort_keys=True))
    return None          # expected to still pass


def m_empty_panel(d):
    """A panel whose series is never drawn -- the axes still render, so only the
    artist digest (or, for a grossly empty canvas, the pixel audit) can see it."""
    edit(os.path.join(d, "make_figures.py"),
         '    ax[1].semilogy(range(len(dec), len(known)), [r["factor"] for r in und], "o", ms=3.6,\n'
         '                   color=BLUE, label="not decidable at %d streams" % streams)',
         '    pass  # the whole series is removed')
    return "series digest"


MUTATIONS = (("M1 plotted array changed, artefacts untouched", m_series),
             ("M2 artefact changed in an unplotted key", m_source),
             ("M3 a promised label is not drawn", m_label),
             ("M4 committed PNG tampered", m_png),
             ("M5 manifest lost a figure", m_manifest),
             ("M8 a panel's series is not drawn", m_empty_panel),
             ("M6 a caption is empty", m_caption),
             ("M7 CLEAN CONTROL: different matplotlib build", m_build))


# -------------------------------------------------------- predicate controls
def predicate_controls():
    """Call the verifier's checks on inputs that violate exactly one property."""
    sys.path.insert(0, HERE)
    import verify_figures as V

    rows = []

    # a text element far outside the viewBox must be reported
    tmp = tempfile.mkdtemp(prefix="issue44-pred-")
    try:
        p = os.path.join(tmp, "canvas.svg")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
                     'width="100" height="100">' + "<path/>" * 40 +
                     '<text x="900" y="900">outside</text></svg>')
        au = V.Audit()
        V.audit_svg(p, [], au, "synthetic")
        caught = [n for ok, n, _d in au.rows if not ok and "inside the canvas" in n]
        rows.append(("P1 a label outside the canvas is reported", bool(caught)))

        # a blank drawing must be reported
        p = os.path.join(tmp, "blank.svg")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
                     'width="100" height="100"></svg>')
        au = V.Audit()
        V.audit_svg(p, [], au, "synthetic")
        caught = [n for ok, n, _d in au.rows if not ok and "not blank" in n]
        rows.append(("P2 a blank drawing is reported", bool(caught)))

        # a missing label must be reported
        p = os.path.join(tmp, "labelled.svg")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
                     'width="100" height="100">' + "<path/>" * 40 +
                     '<text x="10" y="10">present</text></svg>')
        au = V.Audit()
        V.audit_svg(p, ["present", "absent"], au, "synthetic")
        caught = [n for ok, n, _d in au.rows if not ok and "absent" in n]
        rows.append(("P3 an absent label is reported", bool(caught)))

        # P4/P5: the pixel audit -- a blank canvas, and a canvas whose ink is all on one
        # half (the shape a silently empty panel takes)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        white = os.path.join(tmp, "white.png")
        fig = plt.figure(figsize=(4, 2), dpi=100)
        fig.savefig(white, facecolor="white")
        plt.close(fig)
        au = V.Audit()
        V.pixel_audit(white, au, "synthetic")
        caught = [n for ok, n, _d in au.rows if not ok and "has ink" in n]
        rows.append(("P4 a blank canvas is reported", bool(caught)))

        # The per-half check is a GROSS test: it fires when a half carries essentially no
        # ink at all.  A panel that keeps its frame but loses its series is caught by the
        # artist digest instead, which is what M8 demonstrates.
        import numpy as np
        half = os.path.join(tmp, "half.png")
        arr = np.full((100, 100, 4), 255, dtype=np.uint8)
        arr[:, :50, :3] = 0
        fig = plt.figure(figsize=(1, 1), dpi=100)
        ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
        ax.imshow(arr)
        fig.savefig(half, dpi=100, facecolor="white")
        plt.close(fig)
        au = V.Audit()
        V.pixel_audit(half, au, "synthetic")
        caught = [n for ok, n, _d in au.rows if not ok and "both halves" in n]
        rows.append(("P5 a half with no ink at all is reported", bool(caught)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return rows


def main():
    base = tempfile.mkdtemp(prefix="issue44-mut-")
    ok = True
    try:
        # ---- baseline: the harness must not be measuring itself
        pristine = os.path.join(base, "pristine")
        os.makedirs(pristine)
        stage(pristine)
        code, out = run_verify(pristine)
        print("baseline: exit %d -- %s" % (code, out.strip().splitlines()[-1]))
        if code != 0:
            print("FAIL: the baseline copy is not clean; the harness is measuring itself")
            print(out)
            return 1

        for i, (name, fn) in enumerate(MUTATIONS):
            d = os.path.join(base, "m%d" % i)
            os.makedirs(d)
            stage(d)
            expect = fn(d)
            code, out = run_verify(d)
            if expect is None:
                good = (code == 0 and "reported only" in out)
                print("%-46s %s (exit %d, build difference reported, not failed)"
                      % (name, "OK" if good else "DID NOT BEHAVE", code))
                ok &= good
                if not good:
                    print(out)
            else:
                # the verifier prefixes each failure with the figure label, so the
                # fragment is matched, not reconstructed
                good = code != 0 and "FAIL " in out and (expect in out)
                print("%-46s %s (exit %d, caught by %r)"
                      % (name, "FIRED" if good else "DID NOT FIRE", code, expect))
                ok &= good
                if not good:
                    print(out)
            shutil.rmtree(d, ignore_errors=True)

        for name, good in predicate_controls():
            print("%-46s %s" % (name, "FIRED" if good else "DID NOT FIRE"))
            ok &= good
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("\nMUTATIONS: %s" % ("ALL FIRED" if ok else "SOMETHING DID NOT FIRE"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
