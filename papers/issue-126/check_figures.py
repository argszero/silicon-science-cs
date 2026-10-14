#!/usr/bin/env python3
"""check_figures (#126, R551) -- the manuscript's figures are PRESENTATION, and no numeric certificate
reads them.

The submission bar asks for embedded figures with captions and in-text citations, and R551 found the
manuscript carrying five generated PNGs that the text never mentioned once: every numeric check passed,
every reference resolved, and a reader would have seen a paper with no figures at all (Class 178(b):
a presentation bar is invisible to a numeric validator).  So this file checks the four things a reader
sees and a validator does not:

  F1  every embedded asset EXISTS at the path the manuscript links (a link resolves at the linking
      file's own directory -- the base is part of the claim, R407/#87);
  F2  every figure in `figures/` is EMBEDDED (an unshown figure is not evidence);
  F3  every embed is CITED in the prose by its number, in order;
  F4  every caption is non-empty and names the artefact it was drawn from, so a figure cannot drift
      from the instrument that produced it.

Usage: python3 check_figures.py [--selftest]
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, "manuscript.md")
FIGDIR = os.path.join(HERE, "figures")
EMBED = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
ARTEFACT = re.compile(r"spike_[a-z0-9_]+_results\.json")


def analyse(text, base=HERE, figdir=FIGDIR):
    """Return a list of problems.  `base` and `figdir` are arguments so the plants can be run against a
    mutated manuscript rather than against a mutated repository."""
    problems = []
    embeds = EMBED.findall(text)
    # F3 must read the PROSE, not the caption: a caption saying "Figure 1 --" is a label, and counting
    # it as a citation made the check unable to see a figure the text never mentions (its own plant
    # proved it: removing the in-text call-out left the caption behind and the check stayed green).
    prose = EMBED.sub("", text)
    for i, (caption, path) in enumerate(embeds, 1):
        if not os.path.isfile(os.path.join(base, path)):
            problems.append("F1 the embed [%d] points at a missing asset: %s" % (i, path))
        if not EMBED_RE_CAP_OK(caption):
            problems.append("F4 the caption of figure %d is empty" % i)
        if not ARTEFACT.search(caption):
            problems.append("F4 the caption of figure %d names no source artefact" % i)
        if ("Figure %d" % i) not in prose:
            problems.append("F3 figure %d is never cited in the text" % i)
    seen = set(os.path.basename(p) for _c, p in embeds)
    if os.path.isdir(figdir):
        for f in sorted(os.listdir(figdir)):
            if f.lower().endswith(".png") and f not in seen:
                problems.append("F2 the figure %s is never embedded" % f)
    return problems


def EMBED_RE_CAP_OK(caption):
    return bool(caption.strip())


def main():
    text = io.open(MS, encoding="utf-8").read()
    problems = analyse(text)
    for p in problems:
        print("*** " + p)
    n_embeds = len(EMBED.findall(text))
    print("check_figures: %d embedded figure(s), %d problem(s)" % (n_embeds, len(problems)))
    return 0 if not problems else 1


def selftest():
    text = io.open(MS, encoding="utf-8").read()
    ok = True

    def holds(name, cond):
        nonlocal ok
        print("[%-34s] %s" % (name, "ok" if cond else "*** FAIL ***"))
        ok = ok and cond

    holds("clean-manuscript", analyse(text) == [])
    # plant F2: an un-embedded figure -- hide the first embed; the asset stays on disk
    first = EMBED.search(text)
    holds("plant-F2-unembedded", any("F2" in p for p in analyse(text[:first.start()] + text[first.end():])))
    # plant F1: a broken link -- point the first embed at a file that is not there
    holds("plant-F1-broken-link",
          any("F1" in p for p in analyse(EMBED.sub(lambda m: "![cap](figures/nope.png)", text, count=1))))
    # plant F3: drop the in-text citation of the first figure
    holds("plant-F3-uncited",
          any("F3" in p for p in analyse(text.replace("**Figure 1**", "**The first plot**", 1))))
    # plant F4: a caption that names no artefact
    holds("plant-F4-no-artefact",
          any("F4" in p for p in analyse(EMBED.sub(lambda m: "![caption without a source](%s)" % m.group(2),
                                                   text, count=1))))
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
