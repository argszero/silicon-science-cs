#!/usr/bin/env python3
"""#93 R424 -- the bibliography's SELECTION INTEGRITY: was every work in the list a decision to include it?

Why this file exists.  R416 recorded a refusal as a **sentence inside the `difference` line** of a row that sat in
`ARXIV` ("... unrelated to overslight but retained in the pool, and it is not selected.").  `refs_build_v93.py`
takes every row of a selection table as selected, so that work -- a cs.RO paper on robot grasp packing -- was
built into the bibliography.  Nothing in the pipeline read the sentence: the refusal was a claim with no owner,
and the submission bar ("every entry genuinely cited") would have forced a citation to a paper about gripper
geometry.  That is the journal's citation-padding failure arrived at from the inside.

The repair has two halves, and this check owns the second: the refusal is now a **field** (`SEL.NOT_SELECTED`, with
a reason) which the build reads, and every property below is read **two-sided** -- a refused work that enters the
bibliography, and a selected work that the register silently drops, are both defects.

The checks are pure functions over (selected rows, refused rows, built record, key map, manuscript text), so the
battery can feed each one its OWN crafted object instead of mutating the live tree (Class 108).

Run:  python3 refs_check3.py              (read the live artifacts; exit 1 on any failure)
      python3 refs_check3.py --selftest   (plus the mutation battery: each check must fire on its own plant)
"""
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILT = os.path.join(HERE, "refs_built.json")
KEYS = os.path.join(HERE, "refs_keys.json")
MANUSCRIPT = sorted(glob.glob(os.path.join(ROOT, "manuscript", "part*.md")))

CITE = re.compile(r"\[@([^\]]+)\]")

# Phrases that mean "this work was CONSIDERED AND REFUSED".  They belong in the register's reason field, never in
# a difference line: a difference states what the cited work does NOT do, and a sentence that instead says the
# work is not being cited is a selection decision wearing the clothes of a difference.
REFUSAL_PHRASES = ("not selected", "not cited", "is excluded", "was excluded", "do not cite", "cannot be cited",
                   "retained in the pool", "unrelated to")


def load_selection():
    sys.path.insert(0, HERE)
    import refs_selection_v93 as SEL
    return list(SEL.ARXIV) + list(SEL.DOI), list(SEL.NOT_SELECTED)


def load_live():
    selected, refused = load_selection()
    built = json.loads(io.open(BUILT, encoding="utf-8").read())
    keys = json.loads(io.open(KEYS, encoding="utf-8").read())["keys"]
    text = "".join(io.open(p, encoding="utf-8").read() for p in MANUSCRIPT)
    # The DOI limb's exclusions are declared in the stage-2 check, not in the selection module.  Read it from
    # there rather than re-typing the four ids: a re-typed copy would be a third carrier of the decision.
    try:
        sys.path.insert(0, HERE)
        import refs_check2
        stage2_refused = list(refs_check2.REFUSED)
    except Exception as exc:                                    # absent or unreadable is reported, never skipped
        stage2_refused = None
        print("NOTE: the stage-2 refusal list could not be read (%s): that carrier is NOT covered" % exc)
    return dict(selected=selected, refused=refused, built=built, keys=keys, text=text,
                stage2_refused=stage2_refused,
                selection_src=io.open(os.path.join(HERE, "refs_selection_v93.py"), encoding="utf-8").read())


# ---------------------------------------------------------------------------------------------------------------
# the six properties

def c1_selection_matches_the_build(sel):
    """Every selected row is in the built artifact, and every built entry is a selected row."""
    selected_ids = [i for i, _d in sel["selected"]]
    built_ids = [e["key"] for e in sel["built"]["entries"]]
    bad = []
    if len(set(selected_ids)) != len(selected_ids):
        bad.append("a row is selected twice: %s" % sorted({i for i in selected_ids if selected_ids.count(i) > 1}))
    missing = sorted(set(selected_ids) - set(built_ids))
    extra = sorted(set(built_ids) - set(selected_ids))
    if missing:
        bad.append("selected but not built: %s" % missing)
    if extra:
        bad.append("built but not selected: %s" % extra)
    counts = (len(selected_ids), len(built_ids), sel["built"]["n_entries"], sel["built"]["n_unique_keys"])
    if len(set(counts)) != 1:
        bad.append("four carriers of the selected count disagree: %r" % (counts,))
    return (not bad), "selected %d = built %d (artifact says %d/%d)" % counts, bad


def c2_the_register_is_disjoint_from_the_selection(sel):
    """No identifier may be both selected and refused, in either direction, FROM EITHER CARRIER of the decision.

    The exclusion decision has two carriers in this pipeline, and the asymmetry between them is how the R416
    defect survived: the arXiv limb's refusals live in `SEL.NOT_SELECTED` (a field, after R424), while the DOI
    limb's four exclusions live in the stage-2 check's own `REFUSED` list -- one limb's invariant held, its
    sibling's absent.  A property read against only one carrier is a property read against neither, so both are
    read here, and the battery plants a violation through each.
    """
    selected_ids = {i for i, _d in sel["selected"]}
    refused_ids = [i for i, _r in sel["refused"]]
    stage2 = sel.get("stage2_refused")
    bad = []
    if stage2 is None:
        # An UNREADABLE carrier is a failure.  Reading it as an empty list would let this check pass vacuously
        # the moment the other module moved -- a check that tolerates a no-match is blind to its object going
        # away (Class 110), and this file's whole subject is a decision whose reader did not read it.
        bad.append("the stage-2 refusal carrier could not be read: the property is NOT covered")
        stage2 = []
    for i in refused_ids:
        if i in selected_ids:
            bad.append("%s is refused AND selected" % i)
    for i in stage2:
        if i in selected_ids:
            bad.append("%s is refused by the stage-2 limb's own list AND selected" % i)
    for i in sorted(selected_ids):
        if i in set(refused_ids) or i in set(stage2):
            bad.append("%s is selected AND refused" % i)
    if len(set(refused_ids)) != len(refused_ids):
        bad.append("the register repeats an id: %s" % sorted({i for i in refused_ids
                                                              if refused_ids.count(i) > 1}))
    return ((not bad),
            "selected %d | register %d | stage-2 refusals %d | overlap 0"
            % (len(selected_ids), len(refused_ids), len(stage2)), bad)


def c3_no_difference_line_carries_its_own_exclusion(sel):
    """The R416 defect itself: a refusal written into a difference line instead of into the register."""
    bad = []
    for ident, diff in sel["selected"]:
        low = diff.lower()
        for phrase in REFUSAL_PHRASES:
            if phrase in low:
                j = low.index(phrase)
                bad.append("%s: its difference line says %r (a selection decision belongs in NOT_SELECTED)"
                           % (ident, diff[max(0, j - 40):j + len(phrase) + 30]))
    return (not bad), "%d difference line(s) read, 0 carrying a refusal" % len(sel["selected"]), bad


def c4_the_refusal_is_recorded_in_the_artifact(sel):
    """The built record must carry the register, with the same ids and a reason that says something."""
    bad = []
    rec = sel["built"]
    if "not_selected" not in rec or "n_not_selected" not in rec:
        bad.append("the built artifact carries no not-selected register (a refusal the pipeline never recorded)")
    else:
        ids_a = sorted(i for i, _r in sel["refused"])
        ids_b = sorted(x["id"] for x in rec["not_selected"])
        if ids_a != ids_b:
            bad.append("register ids differ: selection %r vs artifact %r" % (ids_a, ids_b))
        if rec["n_not_selected"] != len(sel["refused"]):
            bad.append("artifact says %d refused, the selection says %d" % (rec["n_not_selected"],
                                                                           len(sel["refused"])))
        n_ref = len(sel["built"]["n_selected_arxiv"]) if isinstance(sel["built"].get("n_selected_arxiv"), str) \
            else sel["built"].get("n_selected_arxiv")
        if n_ref != len([1 for i, _d in sel["selected"] if not i.startswith("10.")]):
            bad.append("the artifact's arXiv count %r is not the selection's" % (n_ref,))
    return (not bad), "register in the artifact: %d row(s)" % len(sel["refused"]), bad


def c5_the_keys_cover_the_selection_exactly(sel):
    """The key map is derived from the built records; a key with no record, or a record with no key, is a defect."""
    bad = []
    keys = sel["keys"]
    built_ids = sorted(e["key"] for e in sel["built"]["entries"])
    key_ids = sorted(v["identifier"] for v in keys.values())
    if built_ids != key_ids:
        bad.append("the key map and the built records name different identifiers (%d vs %d)"
                   % (len(key_ids), len(built_ids)))
    if len(keys) != len(sel["selected"]):
        bad.append("key count %d != selected %d" % (len(keys), len(sel["selected"])))
    return (not bad), "keys %d = built %d" % (len(keys), len(built_ids)), bad


def c6_the_manuscript_never_cites_a_refused_work(sel):
    """The end the padding failure would have been paid at: a refused work appearing in the manuscript.

    Two limbs, and the first is a statement about a state the live tree cannot be in: a refused work is not built,
    so it has no key, so no citation can name it.  That impossibility is ASSERTED here rather than read as an
    empty list -- an empty list is what a broken lookup also returns (Class 114), and Class 113's rule is that an
    unreachable state is deleted and its impossibility asserted.  The check still owns the limb, because a work
    refused AFTER it was keyed would be reachable; the battery feeds it exactly that crafted object.
    """
    refused_ids = {i for i, _r in sel["refused"]}
    refused_keys = [k for k, v in sel["keys"].items() if v["identifier"] in refused_ids]
    bad = []
    if refused_keys:
        bad.append("a refused work carries a key in the key map: %s (a refused work must not be citable)"
                   % refused_keys)
    cited = set()
    for m in CITE.finditer(sel["text"]):
        cited.update(x.strip().lstrip("@").strip() for x in m.group(1).split(";"))
    for k in sorted(cited):
        if k in refused_keys:
            bad.append("the manuscript cites [@%s], a work the register refuses" % k)
    for i in sorted(refused_ids):
        if i in sel["text"]:
            bad.append("the manuscript text carries the refused identifier %s" % i)
    return ((not bad),
            "refused %d id(s): no key maps any of them (asserted), and %d citation key(s) name none of them"
            % (len(refused_ids), len(cited)), bad)


def c7_every_refusal_states_a_reason(sel):
    bad = []
    for ident, reason in sel["refused"]:
        r = " ".join((reason or "").split())
        if len(r) < 60:
            bad.append("%s: the refusal states no usable reason (%d chars)" % (ident, len(r)))
    return (not bad), "%d refusal(s), each with a reason" % len(sel["refused"]), bad


def c8_the_legend_and_the_blocks_name_each_other(sel):
    """The selection's docstring legend and the table's own `# ---- X` markers are two carriers of one fact.

    R425 found the legend naming a bucket `K  statistics of comparison` that the table does not have (those works
    sit inside `I`).  A legend is a CLAIM about the table, so both directions are defects: a letter the legend
    names with no block behind it, and a block whose letter the legend never mentions.  The two carriers are read
    from the SOURCE TEXT, which the battery supplies as a crafted object -- a plant that rewrote the real module
    and restored it would leave the tree one crash away from a corrupted selection (Class 108).
    """
    src = sel.get("selection_src")
    if not isinstance(src, str) or not src:
        return (False, "the selection source was not readable: the property is NOT covered",
                ["`selection_src` carries no source text"])
    try:
        doc = src.split('"""', 2)[1]
    except IndexError:
        return (False, "the selection source carries no docstring", ["no docstring to read the legend from"])
    # The legend is a TWO-COLUMN block (`A  ...` on the left, `G  ...` on the right), so a bucket letter is not
    # necessarily at the start of a line -- the first version of this reader required `^\s*[A-K]` and therefore
    # missed the whole right-hand column, reporting three buckets as un-named by a legend that names them
    # (a reader narrower than its object, the Class 114 family, found by running it on the live tree).
    legend = set(re.findall(r"\b([A-K])\s{2}\S", doc))
    blocks = set(re.findall(r"^\s*# ---- ([A-Z])\s\s", src, re.M))
    bad = []
    for letter in sorted(legend - blocks):
        bad.append("the legend names bucket %s and no block carries it" % letter)
    for letter in sorted(blocks - legend):
        bad.append("the table has block %s and the legend never names it" % letter)
    if not legend or not blocks:
        bad.append("legend %d letter(s), blocks %d: one carrier is unreadable" % (len(legend), len(blocks)))
    return ((not bad), "legend %d bucket(s) %s | blocks %d" % (len(legend), "".join(sorted(legend)),
                                                              len(blocks)), bad)


CHECKS = (
    ("C1-selection-matches-the-build", c1_selection_matches_the_build),
    ("C2-register-disjoint", c2_the_register_is_disjoint_from_the_selection),
    ("C3-no-prose-exclusion", c3_no_difference_line_carries_its_own_exclusion),
    ("C4-refusal-in-the-artifact", c4_the_refusal_is_recorded_in_the_artifact),
    ("C5-keys-cover-the-selection", c5_the_keys_cover_the_selection_exactly),
    ("C6-manuscript-cites-no-refused-work", c6_the_manuscript_never_cites_a_refused_work),
    ("C7-refusal-has-a-reason", c7_every_refusal_states_a_reason),
    ("C8-legend-matches-the-blocks", c8_the_legend_and_the_blocks_name_each_other),
)


def run(sel):
    return {name: fn(sel) for name, fn in CHECKS}


# ---------------------------------------------------------------------------------------------------------------
# the battery: one plant per check, each fed its own crafted object

def _copy(sel):
    return json.loads(json.dumps(sel))


def sel_drop_a_built_entry(s):
    s["built"]["entries"] = s["built"]["entries"][1:]
    return s


def sel_add_a_built_entry_not_selected(s):
    s["built"]["entries"] = s["built"]["entries"] + [dict(s["built"]["entries"][0], key="9999.99999")]
    return s


def sel_refused_also_selected(s):
    s["selected"] = s["selected"] + [(s["refused"][0][0], "Also claimed as selected; the register and the "
                                                                    "selection overlap.")]
    return s


def sel_stage2_refused_also_selected(s):
    """The SECOND carrier of the exclusion decision: the DOI limb's list lives in the stage-2 check."""
    s["selected"] = s["selected"] + [(s["stage2_refused"][0], "Also claimed as selected; the stage-2 limb's "
                                                               "refusal list and the selection overlap.")]
    return s


def sel_stage2_carrier_unreadable(s):
    """The carrier itself goes away: an unreadable list must FAIL, not read as empty."""
    s["stage2_refused"] = None
    return s


def sel_selected_also_refused(s):
    s["refused"] = s["refused"] + [(s["selected"][0][0], "A selected work parked in the register: the property "
                                                           "read the other way, and it is the same defect.")]
    return s


def sel_prose_exclusion(s):
    """THE R416 DEFECT, replayed: a refusal written into a difference line."""
    ident, diff = s["selected"][0]
    s["selected"] = [(ident, diff + " Unrelated to this study, and it is not selected.")] + s["selected"][1:]
    return s


def sel_forget_the_register(s):
    del s["built"]["not_selected"]
    del s["built"]["n_not_selected"]
    return s


def sel_drift_the_key_count(s):
    k = list(s["keys"])[0]
    del s["keys"][k]
    return s


def sel_cite_a_refused_key(s):
    """Craft the state the live tree cannot reach: a refused work that carries a key, then cite it.  The key is
    injected BY WAY OF THE PARSE (a real key-map shape), so the plant reaches the check's own lookup."""
    ident = s["refused"][0][0]
    s["keys"]["refused2001"] = dict(s["keys"][list(s["keys"])[0]], identifier=ident, key="refused2001")
    s["text"] = s["text"] + "\nThe pipeline is discussed elsewhere [@refused2001].\n"
    return s


def sel_key_a_refused_work_without_citing_it(s):
    """The same crafted state, cited nowhere: the key map itself must refuse to carry a refused work."""
    ident = s["refused"][0][0]
    s["keys"]["refused2001"] = dict(s["keys"][list(s["keys"])[0]], identifier=ident, key="refused2001")
    return s


def sel_name_the_refused_id_in_the_text(s):
    s["text"] = s["text"] + "\nSee arXiv:%s for the packing result.\n" % s["refused"][0][0]
    return s


def sel_legend_names_a_missing_block(s):
    """The R425 defect itself, replayed: the legend names a bucket the table does not have.

    The plant targets the legend's LAST line, which is a single-column line and therefore exists verbatim in the
    source -- the first version aimed at the `F` line, whose text continues on the same line with the right-hand
    column, so the anchor was absent and the plant was INERT (reported as such rather than counted as a pass).
    """
    anchor = "  J  the economics of an oversight decision (DOI)"
    assert anchor in s["selection_src"], "plant anchor absent: the legend is not in the expected shape"
    s["selection_src"] = s["selection_src"].replace(anchor, anchor + "\n  K  statistics of comparison", 1)
    return s


def sel_block_the_legend_never_names(s):
    """The other direction: the table gains a block the legend does not mention."""
    s["selection_src"] = s["selection_src"].replace("ARXIV = [",
                                                    "# ---- L  a block added without a legend entry\nARXIV = [", 1)
    return s


def sel_selection_source_unreadable(s):
    s["selection_src"] = None
    return s


def sel_blank_reason(s):
    s["refused"] = [(s["refused"][0][0], "n/a")]
    return s


def sel_drift_the_arxiv_count(s):
    s["built"]["n_selected_arxiv"] = s["built"]["n_selected_arxiv"] + 1
    return s


def sel_drop_a_selected_row(s):
    s["selected"] = s["selected"][1:]
    return s


def battery(live):
    """One plant per check, each fed its own crafted object.

    The control is the one case whose plant MUST be inert -- its property is "the object is unchanged and no check
    fires", so an unchanged object is its PASS and not a missed plant.  Reading the control through the same
    "a plant must change the object" rule as the others is how a battery reports its own control as a defect
    (this file's first run did exactly that, and the rule is now split by case).
    """
    base = _copy(live)
    base["refused_keys"] = []
    rows, bad = [], []
    cases = [
        ("unmutated (control)", lambda s: s, None),
        ("a built entry with no selection row", sel_add_a_built_entry_not_selected, "C1-selection-matches-the-build"),
        ("a selected row that was never built", sel_drop_a_built_entry, "C1-selection-matches-the-build"),
        ("a selected row dropped from the selection", sel_drop_a_selected_row, "C1-selection-matches-the-build"),
        ("the arXiv count drifted in the artifact", sel_drift_the_arxiv_count, "C4-refusal-in-the-artifact"),
        ("the refused id also claimed as selected", sel_refused_also_selected, "C2-register-disjoint"),
        ("a selected id parked in the register", sel_selected_also_refused, "C2-register-disjoint"),
        ("a stage-2-refused id also claimed as selected", sel_stage2_refused_also_selected,
         "C2-register-disjoint"),
        ("the stage-2 refusal carrier goes unreadable", sel_stage2_carrier_unreadable, "C2-register-disjoint"),
        ("THE R416 DEFECT: a refusal written into a difference line", sel_prose_exclusion,
         "C3-no-prose-exclusion"),
        ("the artifact records no register at all", sel_forget_the_register, "C4-refusal-in-the-artifact"),
        ("the key map loses a record", sel_drift_the_key_count, "C5-keys-cover-the-selection"),
        ("the manuscript cites a refused work's key (crafted: the live tree cannot)", sel_cite_a_refused_key,
         "C6-manuscript-cites-no-refused-work"),
        ("a refused work carries a key at all, cited nowhere", sel_key_a_refused_work_without_citing_it,
         "C6-manuscript-cites-no-refused-work"),
        ("the manuscript names a refused identifier", sel_name_the_refused_id_in_the_text,
         "C6-manuscript-cites-no-refused-work"),
        ("a refusal with no usable reason", sel_blank_reason, "C7-refusal-has-a-reason"),
        ("the legend names a bucket no block carries (the R425 defect)", sel_legend_names_a_missing_block,
         "C8-legend-matches-the-blocks"),
        ("a block the legend never names", sel_block_the_legend_never_names, "C8-legend-matches-the-blocks"),
        ("the selection source goes unreadable", sel_selection_source_unreadable, "C8-legend-matches-the-blocks"),
    ]
    for name, mutate, want in cases:
        before = json.dumps(base, sort_keys=True)
        s = mutate(_copy(base))
        after = json.dumps(s, sort_keys=True)
        changed = after != before
        got = run(s)
        failing = [k for k, v in got.items() if not v[0]]
        if want is None:
            # the CONTROL: its plant is inert BY DESIGN, and its property is that no check fires on the live tree
            ok = (not changed) and not failing
            rows.append((name, "ok" if ok else "MISSED",
                         "inert, and no check fires" if ok
                         else ("control was MUTATED" if changed else "control already fails: %s" % failing)))
            if not ok:
                bad.append(name)
            continue
        if not changed:
            rows.append((name, "MUTATION INERT", "the plant changed nothing the checks read"))
            bad.append(name)
            continue
        ok = want in failing
        rows.append((name, "caught" if ok else "MISSED",
                     "fired %s" % (want if ok else (failing or "NOTHING"))))
        if not ok:
            bad.append(name)
    return rows, bad


def main():
    if "--selftest" in sys.argv:
        live = load_live()
        rows, bad = battery(live)
        print("mutation battery (%d cases, one plant per check):" % len(rows))
        for name, verdict, detail in rows:
            print("  %-62s %-14s %s" % (name[:62], verdict, detail))
        print("  caught %d/%d" % (len(rows) - len(bad), len(rows)))
        if bad:
            print("  MISSED/INERT: %s" % bad)
        got = run(live)
        n_ok = sum(1 for v in got.values() if v[0])
        print("\nchecks %d/%d PASS on the live artifacts" % (n_ok, len(got)))
        for k in sorted(got, key=lambda s: int(s.split("-")[0][1:])):
            print("  %-36s %-4s %s" % (k, "PASS" if got[k][0] else "FAIL", got[k][1]))
        for k in sorted(got, key=lambda s: int(s.split("-")[0][1:])):
            for b in got[k][2]:
                print("  BAD %s: %s" % (k, b))
        return 0 if (not bad and n_ok == len(got)) else 1
    live = load_live()
    got = run(live)
    n_ok = 0
    for k in sorted(got, key=lambda s: int(s.split("-")[0][1:])):
        ok, detail, bad = got[k]
        n_ok += ok
        print("  %-36s %-4s %s" % (k, "PASS" if ok else "FAIL", detail))
        for b in bad:
            print("      BAD %s" % b)
    print("\nchecks %d/%d PASS" % (n_ok, len(got)))
    return 0 if n_ok == len(got) else 1


if __name__ == "__main__":
    sys.exit(main())
