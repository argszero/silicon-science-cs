#!/usr/bin/env python3
"""Issue #118 -- build the numbered reference list, number the manuscript's citations, and CHECK.

Three duties, and a fourth that is the one a reader depends on:

  number  -- assign [N] to every verified entry, ordered by ROLE then identifier
  render  -- write the References section, each entry carrying its stated difference
  check   -- coverage: every entry cited, every in-text key curated, count >= the journal floor;
             plus: NO literal [N] in the body (a number typed into the body re-points when the
             list is renumbered -- the body must cite by identifier)
  render_check -- the COMMITTED manuscript.md must equal what render produces from the source

Usage:
    /usr/bin/python3 refs_build.py check          # coverage + literal-citation scan
    /usr/bin/python3 refs_build.py render         # write manuscript.md
    /usr/bin/python3 refs_build.py render-check   # committed == built?
"""
import json
import os
import re
import sys

CUR = "refs/curated.json"
AUTH = "refs/authors.json"
MS = "manuscript.src.md"
OUT = "manuscript.md"
MIN_REFS = 100
MARKER = "<!-- REFERENCES -->"

# role order: construct -> the discipline; then the remedies, the systems, then the theory
ROLE_ORDER = ["construct", "balancing", "capacity", "serving", "architecture",
              "efficiency", "security", "survey", "theory"]
ROLE_NAME = {
    "construct": "The construct: capacity, dropping, and the routing discipline",
    "balancing": "Load balancing: the field's standard remedy",
    "capacity": "Capacity and the straggler effect",
    "serving": "Inference serving: the decode regime",
    "architecture": "Named architectures",
    "efficiency": "Efficiency and systems adjacency",
    "security": "Capacity overflow as an attack surface",
    "survey": "Surveys and the design space",
    "theory": "Theory: occupancy, tails, order statistics",
}

# Accept both modern (2605.11689) and pre-2007 (math/0508451, cs/0407023) arXiv identifiers.
# Two id FORMS live in the pool and both must be matched verbatim: modern (2605.11689)
# and pre-2007 with a category prefix (math/0508451, cs/0407023 -- seven digits, NO dot).
IDRE = re.compile(r"(?:[a-z\-]+(?:\.[A-Z]{2})?/\d{7}|\d{4}\.\d{4,5})")
TOKEN = re.compile(r"\[\[(.*?)\]\]", re.S)


def load():
    """(entries, order, num, authors) -- the four things every consumer needs.

    The authors map is RETURNED rather than parked in a module global: a global is initialised only
    on the path that happens to call the loader, so a second consumer (the report generator) reads
    an empty map and every entry looks authorless -- a silent defect in the shape of the one this
    whole component exists to prevent.
    """
    data = json.load(open(CUR))
    entries = {e["bare"]: e for e in data["entries"]}
    authors = load_authors()
    uncovered = sorted(set(entries) - set(authors))
    if uncovered:
        raise SystemExit("%d curated entries have no author record: %s -- run "
                         "`python3 refs_tool.py verify`" % (len(uncovered), uncovered[:8]))
    order = []
    for role in ROLE_ORDER:
        for i in sorted(k for k, v in entries.items() if v["role"] == role):
            order.append(i)
    leftover = sorted(k for k in entries if k not in order)
    order += leftover
    num = {i: n + 1 for n, i in enumerate(order)}
    return entries, order, num, authors


def cite(txt, num, fail_loud=True):
    def rep(m):
        ids = IDRE.findall(m.group(1))
        nums = []
        for i in ids:
            if i not in num:
                if fail_loud:
                    raise SystemExit("UNKNOWN identifier in the manuscript: %r" % i)
                nums.append("?")
            else:
                nums.append(str(num[i]))
        return "[" + ", ".join(nums) + "]"
    return TOKEN.sub(rep, txt)


def load_authors():
    """The author component of every entry, as `refs_tool.py verify` read it from the records.

    It is an INPUT artefact (a record of a network act, like `refs/verify.log`), not a derived one,
    so nothing here regenerates it -- but its COVERAGE is asserted: an identifier in the curated set
    with no author record is refused rather than rendered without one, which is the defect this
    component exists to prevent.
    """
    data = json.load(open(AUTH))
    return data["authors"]


def split_name(raw):
    """A record's name -> (family, given), decided by the ORDER THE RECORD USED.

    A name carrying a comma is already `Family, Given` (the abstract-page carrier's order);
    otherwise the last whitespace-separated token is the family (the API carrier's `Given Family`).
    One token and no more is a family name with no given name to initialise -- the house rule's own
    exception, printed alone rather than padded.
    """
    raw = " ".join(raw.split())
    if "," in raw:
        fam, given = raw.split(",", 1)
        return fam.strip(), given.strip()
    parts = raw.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[-1], " ".join(parts[:-1])


def initials(given):
    """`Maria-Florina Balcan` -> `M. F.` -- one initial per part of the given name, hyphens included."""
    out = []
    for part in re.split(r"[\s\-]+", given.strip()):
        if part:
            out.append(part[0].upper() + ".")
    return " ".join(out)


def author_component(bare, title, authors):
    """The printed author component of one entry -- `Family, I.; ...; et al.`, per the house order.

    Three names then `et al.` from the fourth.  A record that carries NO author prints the sentence
    that says so, naming the record read and the identifier: the author position is never left
    silently empty (a reader cannot tell an unfetched field from an authorless work) and never
    filled by guesswork.
    """
    names = authors.get(bare)
    if names is None:
        raise SystemExit(
            "no author record for %s -- run `python3 refs_tool.py verify` (an entry whose authors "
            "were never read must not be rendered as though the record carried none): %s"
            % (bare, title[:60]))
    if not names:
        return ("Author not established on the record read for this identifier "
                "(arXiv:%s); the record names none" % bare)
    rendered = []
    for n in names:
        fam, given = split_name(n)
        ini = initials(given)
        rendered.append(("%s, %s" % (fam, ini)).strip().rstrip(",") if ini else fam)
    if len(rendered) > 3:
        return "; ".join(rendered[:3]) + "; et al."
    return "; ".join(rendered)


def reference_lines(entries, order, num, authors):
    """One entry per line, each SEPARATED from the next by a blank line.

    Consecutive line-start markers in a Markdown list are read as ONE paragraph by every CommonMark
    renderer (GitHub's preview included), so the 105 entries would print as a single wall and the
    boundaries would disappear -- the entry set is rendered, not just stored.
    """
    lines = []
    cur_role = None
    for i in order:
        r = entries[i]
        if r["role"] != cur_role:
            cur_role = r["role"]
            lines.append("")
            lines.append("**%s**" % ROLE_NAME.get(cur_role, cur_role))
            lines.append("")
        title = r["title"]
        year = (r.get("published") or "")[:4]
        comp = author_component(i, title, authors)
        loc = "arXiv:%s. https://arxiv.org/abs/%s" % (i, i)
        lines.append("[%d] %s%s. %s. %s - Difference from this work: %s."
                     % (num[i], comp, " (%s)" % year if year else "", title, loc, r["diff"]))
        lines.append("")
    return lines


def render(write=True):
    entries, order, num, authors = load()
    src = open(MS).read()
    if MARKER not in src:
        raise SystemExit("the source manuscript has no %s marker" % MARKER)
    body = cite(src, num)
    body = body.replace(MARKER, "\n".join(["## References", ""] + reference_lines(entries, order, num, authors)))
    if write:
        open(OUT, "w").write(body)
        print("wrote %s: %d chars, %d numbered references" % (OUT, len(body), len(order)))
    return body


def check():
    bad = False
    entries, order, num, _authors = load()
    src = open(MS).read()
    used = set()
    for tk in TOKEN.findall(src):
        used.update(IDRE.findall(tk))
    if not used:
        raise SystemExit("COVERAGE FAIL: the manuscript cites nothing")
    body_only = src[:src.index(MARKER)] if MARKER in src else src
    literal = re.findall(r"(?<!\[)\[\d+(?:\s*,\s*\d+)*\]", body_only)
    if literal:
        print("  LITERAL CITATION in the body: %s -> cite by identifier" % literal[:6])
        bad = True
    uncited = sorted(set(entries) - used)
    uncurated = sorted(used - set(entries))
    print("entries=%d  cited=%d  uncited=%d  uncurated=%d"
          % (len(entries), len(used), len(uncited), len(uncurated)))
    for i in uncited:
        print("  UNCITED   %s  (%s)" % (i, entries[i]["role"]))
        bad = True
    for i in uncurated:
        print("  UNCURATED %s  (cited but not in refs/curated.json)" % i)
        bad = True
    if len(entries) < MIN_REFS:
        print("  TOO FEW   %d < %d" % (len(entries), MIN_REFS))
        bad = True
    if bad:
        sys.exit(1)
    print("COVERAGE OK: all %d entries cited, all in-text keys curated, %d >= %d"
          % (len(entries), len(entries), MIN_REFS))


def render_check():
    """The committed manuscript.md must equal what the pipeline builds."""
    built = render(write=False)
    if not os.path.exists(OUT):
        print("  render-check: %s does not exist" % OUT)
        sys.exit(1)
    on_disk = open(OUT).read()
    if on_disk == built:
        print("render-check OK: %s equals the build (%d chars)" % (OUT, len(built)))
        return
    print("  render-check FAIL: %s differs from the build" % OUT)
    a, b = on_disk.splitlines(), built.splitlines()
    for n, (x, y) in enumerate(zip(a, b), 1):
        if x != y:
            print("    first difference at line %d:\n      disk:  %r\n      build: %r" % (n, x[:90], y[:90]))
            break
    else:
        print("    length differs: disk %d lines, build %d lines" % (len(a), len(b)))
    sys.exit(1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    {"check": check, "render": render, "render-check": render_check}[cmd]()
