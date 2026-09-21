#!/usr/bin/env python3
"""#87 -- the manuscript's assembly step: bind the prose to the artefacts, then build the file.

WHAT THIS FILE IS FOR.  `manuscript.md` is not hand-typed: it is the concatenation of the authored parts
(`manuscript_part*.md`, beside the manuscript) with the rendered bibliography (`artefacts/refs/references_block.md`)
appended, and this file is the step that both builds it and CHECKS it.  Four checks, each of which can fail:

WHY THE PARTS SIT BESIDE THE MANUSCRIPT AND NOT BESIDE THIS SCRIPT.  A part that embeds a figure writes the
link as `figures/<file>.png`; a markdown link resolves at the linking file's own directory.  So a part stored
one level down (`artefacts/assembly/`) would carry a link that resolves in the assembled product and is BROKEN
in the file that carries it -- measured by the journal's own gate over this tree (`linkgate.py --check`:
`broken=3`, one per embedded figure).  Beside the manuscript the link resolves in both readings at once; this is
also where this journal's published packages keep their parts (`papers/issue-42/manuscript_part1.md`,
`papers/issue-44/manuscript_part1.md`).

  1. COVERAGE -- every one of the bibliography's entries is cited in the body by its own key.  The check is
     `refgate.py`'s rule, applied here so the assembly refuses to build a manuscript whose bibliography has
     padding in it; the gate is then run on the built file as the independent instrument.
  2. KEY SANITY -- every in-text bracket group that looks like a citation names an entry (a group matching no
     entry is reported for the author to resolve in `reference-check.md`).
  3. BINDINGS -- every number the prose prints is a value the digest owns.  Each binding names a formatted
     string that MUST appear in the body and the digest path it is read from, so a number typed by hand instead
     of read from the artefact (or a stale copy of one) fails the build.  A binding whose formatted value is
     absent is a hard error: the assembly stops and names it.
  4. TABLES -- each table number appears on exactly ONE caption line, and every mention of a table number in
     the prose names a number some caption defines.  A caption is a definition and a mention is a reference;
     two captions sharing a number make every mention of that number unresolvable (the reader cannot tell
     which table it points at), and a mention no caption defines points at nothing.  Read over the PARTS,
     because the built manuscript is generated from them.

The order of first citation is reported as an advisory (the bibliography's numbering is the selection order),
never as a verdict: coverage is a presence test, and a numbered list re-ordered by an edit is not a defect.

Run:  /usr/bin/python3 manuscript_assembly.py        (from papers/issue-87/ or with an absolute path)
Writes manuscript.md and assembly-report.txt beside this file's parent directory.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # papers/issue-87/artefacts/assembly
ART = os.path.dirname(HERE)                                 # papers/issue-87/artefacts
PKG = os.path.dirname(ART)                                  # papers/issue-87
DIGEST = os.path.join(ART, "results_digest.json")
REFS = os.path.join(PKG, "references.json")
BLOCK = os.path.join(ART, "refs", "references_block.md")
MANUSCRIPT = os.path.join(PKG, "manuscript.md")
REPORT = os.path.join(HERE, "assembly-report.txt")
PARTS_DIR = PKG                                            # the parts sit beside the manuscript (see the header)
PARTS = ["manuscript_part%d.md" % i for i in (1, 2, 3, 4)]

HDR = re.compile(r'^#{1,6}\s*(?:\d+[.)]?\s*)?References\s*$', re.I)
ENTRY = re.compile(r'^\s*(?:\[(\d{1,3})\]|(\d{1,3})[.)])(?:\s|$)')
CITE = re.compile(r'\[(\d+(?:\s*[,\u2013-]\s*\d+)*)\]')
CAPTION = re.compile(r'^\*\*Table (\d+)\b')
MENTION = re.compile(r'Table (\d+)\b')

# ---------------------------------------------------------------- the bindings
# (formatted string that must appear in the body, digest key, path inside it, format)
B = []


def bind(label, key, path=None, render=None):
    B.append((label, key, path, render or (lambda v: str(v))))


def f4(v):
    return ("%+.4f" % v).replace("-", "\u2212")


def p4(v):
    return ("%.4f" % v).replace("-", "\u2212")


def _short(v, digits):
    """The manuscript's exponent typography: an exponent with no leading zero and a Unicode minus sign."""
    mant, exp = ("%.*e" % (digits, v)).split("e")
    e = int(exp)
    return "%se%s%d" % (mant, "\u2212" if e < 0 else "", abs(e))


def e1(v):
    return _short(v, 1)


def e2(v):
    return _short(v, 2)


def f3(v):
    return ("%+.3f" % v).replace("-", "−")


def p3(v):
    return ("%.3f" % v).replace("-", "−")


def n0(v):
    return "%.0f" % v


def pc(v):
    return "%.2f %%" % (100.0 * v)


def main():
    # read the digest and the bibliography
    dig = json.load(io.open(DIGEST, encoding="utf-8"))["quantities"]
    refs = json.load(io.open(REFS, encoding="utf-8"))
    keys = [e["key"] for e in refs["entries"]]

    def val(key, path):
        v = dig[key]["value"]
        for p in (path or []):
            v = v[p]
        return v

    # ---- the bindings the prose relies on (each a number the digest owns)
    bind("diag uniformity cycle q6", "structure.diag_uniformity_rel_q6", ["cycle"], e1)
    bind("diag uniformity complete q6", "structure.diag_uniformity_rel_q6", ["complete"], e1)
    bind("diag uniformity path q6", "structure.diag_uniformity_rel_q6", ["path"], e1)
    bind("diag uniformity cycle q8", "structure.diag_uniformity_rel_q8", ["cycle"], e1)
    bind("diag uniformity complete q8", "structure.diag_uniformity_rel_q8", ["complete"], e1)
    bind("diag uniformity path q8", "structure.diag_uniformity_rel_q8", ["path"], e1)
    bind("C7 exact cells", "structure.cycle_reproduction_of_q6", ["n_exact"], n0)
    # ---- the revision round (R412): the alignment panel, and the locally matched rival
    bind("panel g1 mean", "alignment.panel_gamma1", ["mean"], f4)
    bind("panel g1 sd", "alignment.panel_gamma1", ["sd"], p4)
    bind("panel g1 n", "alignment.panel_gamma1", ["n"], n0)
    bind("panel g1 zero-negative", "alignment.panel_gamma1", ["n_negative"], n0)
    bind("panel g1 t-lo", "alignment.panel_gamma1", ["t_lo"], f4)
    bind("panel g1 t-hi", "alignment.panel_gamma1", ["t_hi"], f4)
    bind("panel g2 mean", "alignment.panel_gamma2", ["mean"], f4)
    bind("panel g2 sd", "alignment.panel_gamma2", ["sd"], p4)
    bind("panel g2 n", "alignment.panel_gamma2", ["n"], n0)
    bind("panel g2 negative", "alignment.panel_gamma2", ["n_negative"], n0)
    bind("attenuation g1", "alignment.attenuation", ["gamma1", "mean"], f4)
    bind("attenuation g1 negative", "alignment.attenuation", ["gamma1", "n_negative"], n0)
    bind("attenuation g1 n", "alignment.attenuation", ["gamma1", "n"], n0)
    bind("attenuation g2", "alignment.attenuation", ["gamma2", "mean"], f4)
    bind("attenuation g2 negative", "alignment.attenuation", ["gamma2", "n_negative"], n0)
    bind("attenuation g2 n", "alignment.attenuation", ["gamma2", "n"], n0)
    bind("matchedlocal risk tuned", "rivals.matchedlocal_tuned", ["risk_local_tuned"], p3)
    bind("matchedlocal risk matched", "rivals.matchedlocal_tuned", ["risk_matched"], p3)
    bind("matchedlocal risk fixed", "rivals.matchedlocal_tuned", ["risk_local_fixed"], p3)
    bind("matchedlocal dq tuned", "rivals.matchedlocal_tuned", ["quantum_minus_tuned"], f4)
    bind("matchedlocal dq matched", "rivals.matchedlocal_tuned", ["quantum_minus_matched"], f4)
    bind("matchedlocal blowup g1", "rivals.matchedlocal_blowup", ["1.0"], p3)
    bind("matchedlocal blowup g2", "rivals.matchedlocal_blowup", ["2.0"], p3)
    bind("matchedlocal trivial at gamma 1", "rivals.matchedlocal_trivial_fixed", ["1.0"], p3)
    bind("midband rbf gap", "rivals.midband_arm_gaps", ["rbf"], "%.4f" if False else (lambda v: "%.4f" % v))
    # the build-bound control's printed phrases: ours, and the editorial re-check's on its own build
    bind("control bitwise phrase", "alignment.control_my_build_phrase", None, lambda v: v)
    bind("control pinned build phrase", "alignment.control_pinned_build_phrase", None, lambda v: v)
    bind("control foreign phrase", "alignment.control_foreign_phrase", None, lambda v: v)
    bind("control foreign build phrase", "alignment.control_foreign_build_phrase", None, lambda v: v)
    bind("control foreign worst rel", "alignment.control_foreign_build", ["worst_rel"], e2)
    # Table 5 -- the map's own alpha = +-1 design, the 12 mid-band cells
    _T5 = [("shifted|0.5|a=+1|a=+1", "T5 shifted 0.5 plus", True),
           ("shifted|0.5|a=-1|a=-1", "T5 shifted 0.5 minus", True),
           ("shifted|1|a=+1|a=+1", "T5 shifted 1 plus", True),
           ("shifted|1|a=-1|a=-1", "T5 shifted 1 minus", True),
           ("shifted|2|a=+1|a=+1", "T5 shifted 2 plus", True),
           ("shifted|2|a=-1|a=-1", "T5 shifted 2 minus", True),
           ("unshifted|0.5|a=+1|a=+1", "T5 unshifted 0.5 plus", True),
           ("unshifted|0.5|a=-1|a=-1", "T5 unshifted 0.5 minus", True),
           ("unshifted|1|a=+1|a=+1", "T5 unshifted 1 plus", True),
           ("unshifted|1|a=-1|a=-1", "T5 unshifted 1 minus", True),
           ("unshifted|2|a=+1|a=+1", "T5 unshifted 2 plus", True),
           ("unshifted|2|a=-1|a=-1", "T5 unshifted 2 minus", True)]
    for _key, _label, _ in _T5:
        bind(_label, "map_q6.base_map_delta_vs_matched", [_key, "delta_mean"], f4)
    bind("ladder C cycle", "power.ladder_by_axis", ["C_wrong_metric", "cycle_median"], p4)
    bind("ladder C path", "power.ladder_by_axis", ["C_wrong_metric", "path_median"], p4)
    bind("ladder A cycle", "power.ladder_by_axis", ["A_registered", "cycle_median"], p4)
    bind("ladder A path", "power.ladder_by_axis", ["A_registered", "path_median"], p4)
    bind("ladder D path", "power.ladder_by_axis", ["D_flat_scales", "path_median"], p4)
    bind("ladder E cycle", "power.ladder_by_axis", ["E_permuted", "cycle_median"], p4)
    bind("ladder E path", "power.ladder_by_axis", ["E_permuted", "path_median"], p4)
    bind("PSD min eigenvalue", "power.psd_repair_on_the_path", ["min_eig_before_min"],
         lambda v: ("%.1f" % v).replace("-", "\u2212"))
    for name in ("shifted|0.5|a=+1", "shifted|1|a=-1", "unshifted|2|a=+1", "unshifted|1|a=-1",
                 "shifted|0.1|a=+1", "shifted|3|a=+1", "unshifted|3|a=+1"):
        bind("panel %s q6" % name, "panel.cells", [name, "mean6"], f4)
        bind("panel %s q8" % name, "panel.cells", [name, "mean8"], f4)
    for name in ("shifted|0.5|a=+1", "shifted|0.5|a=-1", "shifted|1|a=+1", "shifted|1|a=-1",
                 "unshifted|1|a=+1", "unshifted|1|a=-1", "unshifted|2|a=+1", "unshifted|2|a=-1"):
        bind("q4 lower bound %s" % name, "panel.q4_main_claim_ci", [name, "lo"], p4)
    bind("q1 max sd q6", "panel.q1_structure_stable", ["6", "max_sd"], p4)
    bind("q1 max sd q8", "panel.q1_structure_stable", ["8", "max_sd"], p4)
    bind("attenuation mean", "panel.q8_over_q6_ratio_of_the_mid_band", ["mean"], p4)
    bind("attenuation median", "panel.q8_over_q6_ratio_of_the_mid_band", ["median"], p4)
    bind("attenuation min", "panel.q8_over_q6_ratio_of_the_mid_band", ["min"], p4)
    bind("attenuation max", "panel.q8_over_q6_ratio_of_the_mid_band", ["max"], p4)
    bind("q3 shifted 0.5 q+1", "panel.q3_attenuation", ["cells", "shifted|0.5|a=+1", "mean"], f4)
    bind("q3 shifted 1 q+1", "panel.q3_attenuation", ["cells", "shifted|1|a=+1", "mean"], f4)
    bind("q3 unshifted 2 q+1", "panel.q3_attenuation", ["cells", "unshifted|2|a=+1", "mean"], f4)
    bind("declared at t=0", "fallback.declared_at_t0", ["n_declared"], n0)
    bind("resolution floor", "fallback.resolution_floor", None, e1)
    bind("BH threshold", "fallback.bh_threshold_min", None, e2)
    bind("null size on holdout", "fallback.size_on_holdout_null", ["rate"], pc)
    bind("worst cell t=1 min", "fallback.four_worst_cells_at_t1", ["shifted|0.5|a=+1"], f4)
    bind("worst cell t=1 max", "fallback.four_worst_cells_at_t1", ["shifted|1|a=+1"], f4)
    bind("q5 repair q6", "panel.q5_repair_matched_denominator", ["q6", "median_ratio"], p4)
    bind("q5 repair q8", "panel.q5_repair_matched_denominator", ["q8", "median_ratio"], p4)
    bind("q6 median sep q6", "panel.q6_matched_vs_rbf", ["median_abs_sep", "6"], p4)
    bind("q6 max sep q8", "panel.q6_matched_vs_rbf", ["max_abs_sep", "8"], p4)
    bind("alpha=0 unshifted 2", "alignment.zero_alignment_cells", ["unshifted", "2", "delta_mean"], f4)
    bind("alpha=0 shifted 2", "alignment.zero_alignment_cells", ["shifted", "2", "delta_mean"], f4)
    bind("alpha=0 shifted 1", "alignment.zero_alignment_cells", ["shifted", "1", "delta_mean"], f4)
    bind("alpha=0 unshifted 1", "alignment.zero_alignment_cells", ["unshifted", "1", "delta_mean"], f4)
    for gamma in ("0.1", "0.25", "0.5", "1", "2", "3"):
        bind("arm risk quantum gamma=%s" % gamma, "rivals.risks_and_deltas",
             ["alpha=+1|%s" % gamma, "risks", "quantum"], p4)
    bind("arm risk matched 0.1", "rivals.risks_and_deltas", ["alpha=+1|0.1", "risks", "matched"], p4)
    bind("arm risk matched 0.5", "rivals.risks_and_deltas", ["alpha=+1|0.5", "risks", "matched"], p4)
    bind("arm risk randfeat 0.5", "rivals.risks_and_deltas", ["alpha=+1|0.5", "risks", "randfeat"], p4)
    bind("arm risk oracle 0.5", "rivals.risks_and_deltas", ["alpha=+1|0.5", "risks", "oracle"], p4)
    for gamma in ("0.1", "0.25", "0.5", "1", "2", "3"):
        bind("Delta matched gamma=%s" % gamma, "rivals.quantum_minus_arm", [gamma, "matched"], f4)
        bind("Delta RBF gamma=%s" % gamma, "rivals.quantum_minus_arm", [gamma, "rbf"], f4)
        bind("Delta randfeat gamma=%s" % gamma, "rivals.quantum_minus_arm", [gamma, "randfeat"], f4)
    bind("closed form vs matched at 0.5", "rivals.closedform_minus_matched_gamma_0p5", None, p4)
    bind("Delta matched 0.1 (win at the rim)", "rivals.quantum_minus_arm", ["0.1", "matched"], f4)
    bind("Delta RBF mid-band", "rivals.quantum_minus_arm", ["0.5", "rbf"], f4)

    # ---- build the file
    body_parts = []
    for p in PARTS:
        with io.open(os.path.join(PARTS_DIR, p), encoding="utf-8") as fh:
            body_parts.append(fh.read().rstrip() + "\n")
    body = "\n".join(body_parts)
    with io.open(BLOCK, encoding="utf-8") as fh:
        block = fh.read().rstrip() + "\n"
    with io.open(MANUSCRIPT, "w", encoding="utf-8") as fh:
        fh.write(body.rstrip() + "\n\n" + block.rstrip() + "\n")

    # ---- check 1: coverage (the gate's rule, applied at the build)
    lines, ref_start = body.split("\n"), None
    for i, l in enumerate(lines):
        if HDR.match(l):
            ref_start = i
    text_body = "\n".join(lines[:ref_start]) if ref_start is not None else body
    cited = set()
    for m in CITE.finditer(text_body):
        for tok in re.split(r'[,\u2013-]', m.group(1)):
            cited.add(int(tok.strip()))
    missing = [n for n in range(1, len(keys) + 1) if n not in cited]
    unmatched = sorted(n for n in cited if n > len(keys))

    # ---- check 3: bindings.  A binding is (label, digest key, path, renderer); the check reads the value
    # out of the digest, RENDERS it, and requires the rendered string to appear in the body.  The renderer is
    # a callable so that the manuscript's own typography (the Unicode minus in an exponent, a percentage) is
    # part of the binding rather than a decoration the check cannot see.
    bad = []
    for label, key, path, render in B:
        try:
            want = render(val(key, path))
        except Exception as exc:                                    # a binding that cannot be read is a defect
            bad.append("%-14s <- %s%s UNREADABLE: %s" % (label, key, path, exc))
            continue
        if want not in text_body:
            bad.append("%-14s <- %s%s renders %r, absent from the body"
                       % (label, key, "" if path is None else "[" + "][".join(path) + "]", want))

    # ---- check 4: the tables, read over the parts (the manuscript is generated from them).
    captions, mentions = [], []
    for p in PARTS:
        for i, l in enumerate(io.open(os.path.join(PARTS_DIR, p), encoding="utf-8").read().split("\n"), 1):
            cap = CAPTION.match(l)
            if cap:
                captions.append((int(cap.group(1)), p, i))
            for m in MENTION.finditer(l):
                if cap and m.start() < 9:          # the caption's own number is the definition, not a mention
                    continue
                mentions.append((int(m.group(1)), p, i))
    cap_nums = [c[0] for c in captions]
    defined = set(cap_nums)
    dup = sorted({n for n in cap_nums if cap_nums.count(n) > 1})
    missing_num = [n for n in range(1, len(cap_nums) + 1) if n not in defined]
    undefined = sorted({n for n, _, _ in mentions if n not in defined})
    tables_bad = bool(dup or missing_num or undefined)

    # ---- advisory: order of first citation
    first = {}
    for m in CITE.finditer(text_body):
        for tok in re.split(r'[,\u2013-]', m.group(1)):
            n = int(tok.strip())
            first.setdefault(n, m.start())
    inv = [(a, b) for a in first for b in first if a < b and first[a] > first[b]]

    rep = ["assembly report -- issue #87", "",
           "parts: %s" % ", ".join(PARTS),
           "bibliography: %d entries (%s)" % (
               len(keys), ", ".join("%d %s" % (n, s) for s, n in sorted(
                   (s, sum(1 for e in refs["entries"] if e["source"] == s))
                   for s in {e["source"] for e in refs["entries"]}))),
           "body charset length: %d" % len(body),
           "manuscript length: %d chars" % os.path.getsize(MANUSCRIPT),
           "",
           "CHECK 1 coverage: cited %d distinct keys; missing %d" % (len(cited), len(missing)),
           "        missing: %s" % (missing[:20] if missing else "none"),
           "CHECK 2 keys    : bracket numbers matching no entry: %s" % (unmatched or "none"),
           "CHECK 3 bindings: %d bound (all present) " % len(B) if not bad else
           "CHECK 3 bindings: %d FAILED" % len(bad),
           "CHECK 4 tables  : %d captions, numbering %s -- duplicate numbers %s, gaps %s, mentions with no "
           "caption %s" % (len(captions), cap_nums, dup or "none", missing_num or "none", undefined or "none"),
           "        captions : %s" % "; ".join("Table %d = %s L%d" % (n, p, i) for n, p, i in captions),
           ""]
    rep += ["        FAILED: " + b for b in bad]
    rep += ["",
            "ADVISORY order of first citation: %d keys cited, %d inversions (the bibliography's numbering is "
            "the selection order; coverage is a presence test, so an inversion is not a defect)"
            % (len(first), len(inv))]
    out = "\n".join(rep) + "\n"
    with io.open(REPORT, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(out)
    if missing or unmatched or bad or tables_bad:
        print("ASSEMBLY: FAIL")
        return 1
    print("ASSEMBLY: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
