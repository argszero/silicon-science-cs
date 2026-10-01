#!/usr/bin/env python3
"""#93 R428 -- every link and image in the product resolves at the PRODUCT's own base.

Why this file exists.  A markdown link resolves relative to the directory of the file that carries it, not to the
repository root and not to the directory the reader is standing in.  The parts of this manuscript are drafted in
`research/manuscript/` and assembled into `papers/issue-93/manuscript.md`, so a figure path written for the parts
(`../figures/x.png`) is broken in the product, and a path written for the product (`figures/x.png`) is broken in
the parts -- the same link cannot be right in both, which is a statement about a BASE and not about a link.  Since
the product is what a reader has, the product's base is the one that must resolve, and this check reads the product.

Two-sided by construction: a local path that does not exist is a FAIL, an `http(s)` or in-page link is not treated
as local, and a battery proves both directions and that an image is read as well as a link.

Run:  python3 check_links.py [--selftest]
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCT = os.path.join(HERE, "manuscript.md")
LINK = re.compile(r"(!?)\[[^\]]*\]\(([^)\s]+)\)")
EXTERNAL = ("http://", "https://", "mailto:", "#")


def local(paths):
    return [p for p in paths if not p.startswith(EXTERNAL)]


def scan(text, root=HERE):
    """(all links, local links, broken local links).  Ends are stripped so a path with a title still resolves."""
    paths = [m.group(2).strip() for m in LINK.finditer(text)]
    loc = local(paths)
    broken = [p for p in loc if not os.path.exists(os.path.join(root, p.split("#")[0]))]
    return paths, loc, broken


def main():
    if not os.path.exists(PRODUCT):
        print("NOT RUN -- no manuscript.md beside this script")
        return 2
    text = io.open(PRODUCT, encoding="utf-8").read()
    paths, loc, broken = scan(text)
    print("  %-46s %-4s %s" % ("L1-links-and-images-parse", "PASS" if paths else "FAIL",
                               "%d link(s), %d local" % (len(paths), len(loc))))
    print("  %-46s %-4s %s" % ("L2-every-local-target-resolves", "PASS" if not broken else "FAIL",
                               "broken: %s" % (broken[:5] or "none")))
    imgs, _l, broken_i = scan("\n".join(m.group(0) for m in LINK.finditer(text) if m.group(1) == "!"))
    print("  %-46s %-4s %s" % ("L3-images-are-read-as-images", "PASS" if imgs and not broken_i else "FAIL",
                               "%d image(s), broken: %s" % (len(imgs), broken_i[:3] or "none")))
    bad = (not paths) or broken or not imgs or broken_i
    print("\nLINK CHECK: %s -- %d link(s), %d local, %d broken"
          % ("FAIL" if bad else "PASS", len(paths), len(loc), len(broken)))
    rc = 1 if bad else 0
    if "--selftest" in sys.argv:
        cases = [
            ("a local target that does not exist is caught",
             lambda t: t + "\n\n![gone](figures/not_here.png)\n", True),
            ("an http link is not treated as local",
             lambda t: t + "\n\nsee [arxiv](https://arxiv.org/abs/1111.11111)\n", False),
            ("an in-page anchor is not treated as local",
             lambda t: t + "\n\nsee [above](#5-results)\n", False),
            ("a local image that does exist is not reported",
             lambda t: t + "\n\n![fig](figures/fig1_sign_law_and_cost_ratio.png)\n", False),
        ]
        fired = 0
        for name, mutate, want_broken in cases:
            _p, _l, b2 = scan(mutate(text))
            got = bool(b2)
            ok = got == want_broken
            print("  %-58s %s" % (name[:58], "caught" if ok else "MISSED"))
            fired += 1 if ok else 0
            if not ok:
                rc = 1
        print("BATTERY: %d of %d case(s) fired" % (fired, len(cases)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
