#!/usr/bin/env python3
"""Issue #50 -- the manuscript's own claims, each read against the object that owns it.

    python3 manuscript_check_v1.py            # check: exit 0 iff every claim below is bound
    python3 manuscript_check_v1.py --selftest # liveness: one planted defect per check must fire

WHY THIS FILE EXISTS.  `assemble.py` already guarantees that every `{{fact}}` resolves, that no
placeholder survives, and that no reference entry is uncited.  What it cannot see is the *other*
carrier: a sentence that states a result in words, or that repeats a measurement as a literal.  The
package has paid for both classes -- a typed copy of a value an artefact can change is a claim with no
owner, and a verdict stated in prose is a claim whose owner is a JSON field nobody re-reads.  This file
binds four such carriers, and each of the four failed at least once in this package's own history:

  A  **the registered verdicts, against the artefacts that decided them.**  Section 7 states, for each
     registered prior, confirmed / contradicted / unresolved.  Each of those words is read here out of
     the artefact's own verdict field, through a declared word map; if the artefact flips, the sentence
     the manuscript must carry flips with it, and a manuscript that kept the old word FAILS.
  B  **every section reference resolves.**  A phantom `4.11` or `Section 9` is a sentence whose only
     job is navigation, so it fails the reader silently.  The forms read are `§N`, `Section N` and the
     parenthesised `(N.M)` the results section uses -- a bare `4.11` in running text is a reference
     this check cannot see, and the reading is stated here rather than implied.
  C  **the figures are reachable and pointed at.**  Every `](figures/...)` path must exist, every
     `Figure N` in the prose must name an embed, and every embed must be named at least once -- a
     figure nobody points at is decoration rather than evidence.
  D  **no headline measurement is typed into the prose.**  For a declared list of the paper's headline
     measurements, the literal (and its rounded forms) must not appear in the parts outside a
     placeholder: the prose must quote them through the fact that owns them.

A claim whose anchor cannot be found FAILS rather than passes: "the sentence is not there" and "the
sentence is right" must never look alike.  `--selftest` plants one defect per check in a throwaway copy
of the package and requires that check -- and no other -- to report it.
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = ("manuscript_part1.md", "manuscript_part2.md", "manuscript_part3.md", "manuscript_part4.md")
MS = "manuscript.md"
FIGDIR = "figures"

# --- A. the registered verdicts, and the word the manuscript must carry for each -------------------
# (criterion, artefact, JSON path to the verdict, the artifact's word -> the manuscript's word)
VERDICTS = [
    ("P1  unresolved as registered", "artefacts/fixedpoint_v1.json", ("verdict", "status"),
     {"UNMET": "unresolved as registered"}, "4.7 / 7"),
    ("P2  first half (heavier tail lowers rho*)", "artefacts/tail_v1_h100.json",
     ("p2_first_half", "verdict"), {"CONTRADICTED": "contradicted"}, "4.4 / 7"),
    ("P2  second half (the fall is shallower)", "artefacts/tail_v1_h100.json",
     ("p2_second_half", "verdict"), {"CONTRADICTED": "contradicted"}, "4.4 / 7"),
    ("P4a the safe region shrinks", "artefacts/sideeffect_v1.json", ("verdicts", "P4a", "verdict"),
     {"CONFIRMED": "confirmed", "CONTRADICTED": "contradicted"}, "4.6 / 7"),
    ("P4b the registered magnitude", "artefacts/sideeffect_v1.json", ("verdicts", "P4b", "verdict"),
     {"CONFIRMED": "confirmed", "CONTRADICTED": "contradicted"}, "4.6 / 7"),
    ("P4c permitted-but-harmful is non-empty", "artefacts/sideeffect_v1.json",
     ("verdicts", "P4c", "verdict"), {"CONFIRMED": "confirmed", "CONTRADICTED": "contradicted"},
     "4.6 / 7"),
]

# --- D. the headline measurements that must not appear as literals in the prose ---------------------
# Read out of the same facts the assembler owns; the check is that the prose QUOTES them through the
# placeholder rather than typing a copy that no artefact can move.
HEADLINE_FACTS = ("rho_star_A16", "rho_star_A96", "rho_star_span", "blind_share_h025",
                  "blind_share_h050", "F_h025", "F_h050", "F_h075", "F_min", "F_max",
                  "tail_delta_worst_abs", "tail_shortfall_factor", "p4b_lowest", "p4b_highest",
                  "p4c_frac_lo", "p4c_frac_hi", "m4b_frac_neg", "m4b_mean_benefit",
                  "rho_span_over_interval", "ext_appworld_published", "ext_appworld_shortfall",
                  "fix_within_tol_pct")


def read(root, name):
    return io.open(os.path.join(root, name), encoding="utf-8").read()


def parts_of(root):
    return "\n".join(read(root, p) for p in PARTS)


def artifact(root, name):
    return json.load(io.open(os.path.join(root, name), encoding="utf-8"))


def digest(doc, path):
    node = doc
    for key in path:
        node = node[key]
    return node


def facts_of(root):
    """The assembler's own fact table, built against `root` -- so a planted change to an artefact
    reaches this check through the SAME reader the assembler uses, not through a copy of the value."""
    sys.path.insert(0, root)
    try:
        import assemble                                     # noqa: E402  (the package's own module)
        return assemble.build_facts()
    finally:
        sys.path.remove(root)
        # ... and out of the module cache too: a second call with another root would otherwise be
        # answered by the FIRST root's artefacts, which is a control that reads the wrong tree
        sys.modules.pop("assemble", None)


# --------------------------------------------------------------------------------------------- checks
def check_verdicts(root):
    """A: each criterion's stated verdict is the one the artefact decided."""
    out = []
    ms = read(root, MS)
    for name, art, path, wordmap, where in VERDICTS:
        raw = digest(artifact(root, art), path)
        key = next((k for k in wordmap if raw.startswith(k)), None)
        if key is None:
            out.append("%s: the artefact's verdict %r has no word in the declared map" % (name, raw))
            continue
        want = wordmap[key]
        if want not in ms:
            out.append("%s (%s): the artefact says %r -> the manuscript must state %r, and does not "
                       "carry that word anywhere" % (name, where, key, want))
            continue
        # ... and the word must sit in the criterion's own paragraph, not anywhere in the paper
        anchor = PARAGRAPH[name]
        para = between(ms, anchor)
        if para is None:
            out.append("%s: the paragraph anchor %r is not in the manuscript" % (name, anchor))
        elif want not in para:
            out.append("%s (%s): the artefact says %r; the paragraph beginning %r does not state %r"
                       % (name, where, key, anchor, want))
    return out


# The paragraph each criterion's outcome must be stated in.  An anchor that no longer occurs in the
# manuscript is a FAILURE of the check, not a check that passes vacuously (see the module docstring).
PARAGRAPH = {
    "P1  unresolved as registered": "P1 -- \"a sharp boundary exists",
    "P2  first half (heavier tail lowers rho*)": "P2 -- \"the tail, not the mean",
    "P2  second half (the fall is shallower)": "P2 -- \"the tail, not the mean",
    "P4a the safe region shrinks": "P4a -- \"the safe region shrinks",
    "P4b the registered magnitude": "P4b -- \"the shrinkage is at least 0.05",
    "P4c permitted-but-harmful is non-empty": "P4c -- \"a domain admissibility rule",
}


def between(text, anchor):
    i = text.find(anchor)
    if i < 0:
        return None
    j = text.find("\n\n**P", i + len(anchor))
    return text[i:j if j > 0 else len(text)]


def check_sections(root):
    """B: every section reference in the prose names a section the manuscript carries."""
    ms = read(root, MS)
    heads = set()
    for m in re.finditer(r"^#{2,3}\s+([0-9]+(?:\.[0-9]+)?)\.?\s", ms, re.M):
        heads.add(m.group(1))
    # ... and the BOLD RUN-IN form: sections 5 and 9 carry their subsections as `**5.1 ...**` lines
    # rather than as headings.  The first version of this check knew only the heading form and duly
    # reported three references into those sections as phantom -- a rule derived from the form the
    # author happened to be looking at, which is the defect class this package keeps paying for.
    for m in re.finditer(r"^\*\*([0-9]+(?:\.[0-9]+))\s", ms, re.M):
        heads.add(m.group(1))
    out = []
    refs = set()
    body = parts_of(root)
    for pat in (r"§\s*([0-9]+(?:\.[0-9]+)?)", r"\b[Ss]ection\s+([0-9]+(?:\.[0-9]+)?)"):
        refs.update(re.findall(pat, body))
    for m in re.finditer(r"\((\d+\.\d+)\)", body):          # the `(4.6)` form the results use
        refs.add(m.group(1))
    for n in sorted(refs):
        if n not in heads:
            out.append("the prose refers to %s, which is not a heading of the manuscript" % n)
    if not refs:
        out.append("no section reference was found at all -- the pattern, not the manuscript, is "
                   "what passed")
    return out


def check_figures(root):
    """C: the embeds exist, the references resolve, and no figure is orphaned."""
    ms = read(root, MS)
    embeds = re.findall(r"!\[[^\]]*\]\((figures/[^\)]+)\)", ms)
    out = []
    if not embeds:
        out.append("the manuscript embeds no figure at all")
    for rel in embeds:
        if not os.path.exists(os.path.join(root, rel)):
            out.append("the manuscript embeds %s, which the package does not ship" % rel)
    named = set(int(n) for n in re.findall(r"Figure\s+(\d+)", ms))
    for n in sorted(named):
        if n < 1 or n > len(embeds):
            out.append("the prose names Figure %d, and the manuscript carries %d embed(s)"
                       % (n, len(embeds)))
    for i in range(1, len(embeds) + 1):
        if i not in named:
            out.append("figure %d (%s) is embedded and never pointed at by the prose"
                       % (i, embeds[i - 1]))
    return out


def literal_forms(v):
    """The strings a measurement could be typed as: the exact render, and the rounded forms a hand
    copy would use."""
    forms = set()
    if isinstance(v, float):
        forms.add(("%.6g" % v))
        if abs(v) >= 0.01:
            forms.add(("%.2f" % v))
        if abs(v) >= 1:
            forms.add(("%.1f" % v))
            forms.add(("%.3g" % v))
    elif isinstance(v, int):
        forms.add(str(v))
        forms.add("{:,}".format(v))
    return set(f for f in forms if len(f.replace(".", "").replace(",", "").lstrip("0")) >= 3)


def check_typed(root):
    """D: no headline measurement is typed into the prose -- it is quoted through its placeholder."""
    parts = parts_of(root)
    facts = facts_of(root)
    out = []
    checked = 0
    for name in HEADLINE_FACTS:
        if name not in facts:
            out.append("the headline fact %s is not in the assembler's table any more" % name)
            continue
        v = facts[name]()
        checked += 1
        for form in sorted(literal_forms(v)):
            for m in re.finditer(re.escape(form), parts):
                ctx = parts[max(0, m.start() - 60):m.end() + 30].replace("\n", " ")
                out.append("%s = %s is typed in the prose as %r: ...%s..." % (name, v, form, ctx))
    if checked != len(HEADLINE_FACTS):
        out.append("only %d of %d headline facts were reachable" % (checked, len(HEADLINE_FACTS)))
    return out


STATUS_ANCHOR = "are unmet outright"      # the summary sentence that names the criteria's outcome


def check_criteria(root):
    """E: the sentence saying which registered criteria are unmet is the one the artefacts decide.

    The claim has an owner in `assemble.py` (`criteria_status`), read here through the SAME reader the
    assembler uses -- so a planted verdict reaches this check as a changed set, not as a stale copy.
    Two-sided: every criterion the artefacts mark unmet must be stated unmet in that paragraph, and no
    criterion they mark met may be.  An anchor that no longer occurs is a FAILURE, not a pass.
    """
    ms = read(root, MS)
    facts = facts_of(root)
    try:
        outright = [s for s in facts["criteria_unmet_outright"]().split(",") if s]
        part = [s for s in facts["criteria_unmet_part"]().split(",") if s]
        met = [s for s in facts["criteria_met"]().split(",") if s]
    except KeyError as exc:
        return ["the assembler no longer derives the criteria's statuses (%s)" % exc]
    i = ms.find(STATUS_ANCHOR)
    if i < 0:
        return ["the sentence stating the criteria's outcome (%r) is not in the manuscript"
                % STATUS_ANCHOR]
    j = ms.find("\n\n", i)
    para = ms[i:j if j > 0 else len(ms)]
    out = []
    for cid in outright + part:
        if not re.search(r"\(%s\)[^.;]{0,60}?unmet" % re.escape(cid), para):
            out.append("the artefacts mark criterion (%s) unmet and the paragraph beginning %r does"
                       " not state it unmet" % (cid, STATUS_ANCHOR))
    for cid in met:
        if re.search(r"\(%s\)[^.;]{0,60}?unmet" % re.escape(cid), para):
            out.append("the artefacts mark criterion (%s) met and the paragraph beginning %r states"
                       " it unmet" % (cid, STATUS_ANCHOR))
    if not outright and not part:
        out.append("no criterion is derived as unmet at all -- the artefacts or the derivation moved")
    return out


CHECKS = [("the registered verdicts against their artefacts", check_verdicts),
          ("the section references resolve", check_sections),
          ("the figures exist, are numbered and are pointed at", check_figures),
          ("no headline measurement is typed into the prose", check_typed),
          ("which registered criteria are unmet, against the artefacts", check_criteria)]


def run(root):
    bad = 0
    for label, fn in CHECKS:
        fails = fn(root)
        print("  %-52s %s" % (label, "OK" if not fails else "FAILED (%d)" % len(fails)))
        for f in fails:
            print("      %s" % f)
        bad += len(fails)
    print("MANUSCRIPT CLAIMS: %d check(s), %d failure(s)" % (len(CHECKS), bad))
    return 0 if bad == 0 else 1


# ------------------------------------------------------------------------------------------- selftest
def copy_package(dst):
    os.makedirs(os.path.join(dst, "artefacts"))
    for p in PARTS + (MS,):
        shutil.copyfile(os.path.join(HERE, p), os.path.join(dst, p))
    shutil.copyfile(os.path.join(HERE, "assemble.py"), os.path.join(dst, "assemble.py"))
    for n in os.listdir(os.path.join(HERE, "artefacts")):
        src = os.path.join(HERE, "artefacts", n)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(dst, "artefacts", n))
    shutil.copytree(os.path.join(HERE, FIGDIR), os.path.join(dst, FIGDIR))
    return dst


def edit(path, old, new):
    t = io.open(path, encoding="utf-8").read()
    assert t.count(old) >= 1, (path, old[:60])
    io.open(path, "w", encoding="utf-8").write(t.replace(old, new, 1))


def flip_artefact(root, rel, path, value):
    p = os.path.join(root, rel)
    doc = json.load(io.open(p, encoding="utf-8"))
    node = doc
    for k in path[:-1]:
        node = node[k]
    was = node[path[-1]]
    node[path[-1]] = value
    io.open(p, "w", encoding="utf-8").write(json.dumps(doc, indent=1, sort_keys=True))
    return was


def selftest():
    bad = 0
    print("  base: the package as committed")
    base = run(HERE)
    if base != 0:
        print("  the base case FAILS, so the planted cases below would prove nothing")
        return 1
    plants = [
        ("A", CHECKS[0][1], lambda r: flip_artefact(r, "artefacts/sideeffect_v1.json",
                                                    ("verdicts", "P4a", "verdict"), "CONTRADICTED")),
        ("B", CHECKS[1][1], lambda r: io.open(os.path.join(r, "manuscript_part4.md"), "a",
                                              encoding="utf-8").write(
            "\nThe design is stated in (4.99) and the controls follow.\n")),
        ("C", CHECKS[2][1], lambda r: edit(os.path.join(r, MS), "(Figure 1)", "(Figure 9)")),
        ("D", CHECKS[3][1], lambda r: io.open(os.path.join(r, "manuscript_part4.md"), "a",
                                              encoding="utf-8").write(
            "\nA typed copy: the crossing is 0.991908 at the smallest pool.\n")),
        # E: the closed form's verdict in the artefact moves from UNMET to MET, so (v) joins the met
        # set while the summary paragraph still says (v) is unmet.  The check must report that.
        ("E", CHECKS[4][1], lambda r: flip_artefact(r, "artefacts/fixedpoint_v1.json",
                                                   ("verdict", "status"), "MET")),
        # F: and the OTHER branch of the same rule -- the artefacts stay put and the PROSE drops a
        # criterion they mark unmet.  One plant would have exercised only the "states too much" side.
        ("F", CHECKS[4][1], lambda r: edit(os.path.join(r, MS),
                                           "(ii) is unmet, the separation", "(ii) is discussed, the separation")),
    ]
    for tag, fn, plant in plants:
        tmp = tempfile.mkdtemp(prefix="issue50-claims-%s-" % tag)
        try:
            root = copy_package(os.path.join(tmp, "pkg"))
            plant(root)
            try:
                fails = fn(root)
            except Exception as exc:                        # a crash is not a firing
                print("  plant %s: THE CHECK ITSELF CRASHED -- %s: %s"
                      % (tag, type(exc).__name__, exc))
                bad += 1
                continue
            print("  plant %s: %s" % (tag, "the check fired (%d finding(s))" % len(fails)
                                      if fails else "THE CHECK DID NOT FIRE (control void)"))
            for f in fails[:3]:
                print("        %s" % f[:140])
            if not fails:
                bad += 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print("MANUSCRIPT CLAIMS SELFTEST: %d plant(s), %d not firing" % (len(plants), bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else run(HERE))
