#!/usr/bin/env python3
"""Check the manuscript against the artefacts it quotes.

The manuscript is assembled from the part files, and every measurement in it is a
placeholder resolved out of canonical_results.json.  A manuscript that assembles is
not yet a checked manuscript: the checks below are the ones that could have caught
the failure modes we have actually met on this package.

  RECOMPUTE  a fresh assembly, run from a foreign directory, is byte-identical to
             the committed manuscript.md -- so the committed file is a product of
             the committed sources and not of an earlier edit.
  READ       a mutation control: one fact is changed in a throwaway copy of the
             artefact and the assembly is re-run; the rendered text must change in
             the mutated value.  Without this, a placeholder whose value was
             hand-typed to match the artefact would pass every other check here.
  COMPLETE   no placeholder and no reference marker survives into the manuscript.
  NUMBERS    the number of resolved placeholders is reported and gated.
  CITATIONS  every cited key has an entry, every entry is cited, the entry count is
             gated at the journal's bar, and every entry appears in reference-check.md.
  PUNCTUATION the compiled reference list carries ONE period per separator, checked over
             every entry rather than the entries a reader happens to look at.  A renderer
             that appends the separator period to a name already ending in one renders
             `Wald, A..` and `et al..` -- 55 of 102 entries at the head where every other
             citation check passed, because the predicate under review was the name ORDER
             and the punctuation it produced was never read.
  LAYOUT     tables and figures are numbered in document order, embedded, captioned,
             and cited in the running text; every embedded figure file exists.
  AUDIT      numbers that are not placeholders are listed for review, so that a
             hand-typed measurement has to be looked at rather than trusted.
  COUNTS     spelled-out counts are checked against sizes derived from the artefact and
             from the document's own enumerations.  The audit class above lists only inline
             code spans carrying a decimal, so three defects shipped through a green run:
             "the four registered priors" (there are three), and a sentence counting
             "three of the four consequences" over a list of four.  A count in words is a
             measurement too, and it is the class this file could not see.

The verdict is the exit status.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_REFS = 100          # journal bar: at least 100 references, all cited
MIN_PLACEHOLDERS = 60   # the manuscript's numbers must come from the artefact

PARTS = ["manuscript_part1.md", "manuscript_part2.md", "manuscript_part3.md"]
PLACEHOLDER = re.compile(r"\{\{[A-Za-z]+:[^}]*\}\}")
CITE = re.compile(r"\[@([A-Za-z0-9_.:-]+)\]")
CAPTION = re.compile(r"\*\*(Table|Figure) (\d+)\.\*\*")
EMBED = re.compile(r"!\[Figure (\d+)\]\(([^)]+)\)")
TABLE_ROW_DECIMAL = re.compile(r"(?<![\w.])\d+\.\d+(?![\w])")


# ------------------------------------------------------------------ spelled-out counts ---------
# The words a count can be written in, and the noun phrases that name a collection whose size is
# known independently of the sentence under test.  Longest-first, so "registered criteria" is not
# matched as "criteria".
SPELLED = {w: i for i, w in enumerate(
    ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"])}
SPELLED_WORD = "(?:" + "|".join(sorted(SPELLED, key=len, reverse=True)) + ")"
COUNT_NOUNS = [("registered priors", "registered priors"), ("registered prior", "registered priors"),
               ("registered criteria", "registered criteria"), ("consequences", "consequences"),
               ("contributions", "contributions"), ("tables", "tables"), ("figures", "figures")]


def enumerated_items(text, anchor):
    """Count the numbered items that follow an anchor, in order.

    Blank lines and indented continuation lines belong to the current item, not to the end of the
    list: breaking on a continuation counted Section 1's four consequences as ONE, which is a derived
    size that is wrong -- worse than no derived size at all.  The anchor must not span a line break
    (the assembled paragraph wraps mid-phrase), so it is chosen inside one line.
    """
    i = text.find(anchor)
    if i < 0:
        return None
    n = 0
    for line in text[i:].split("\n")[1:]:
        if re.match(r"^%d\. " % (n + 1), line):
            n += 1
        elif line.strip() == "" or line[:1] in (" ", "\t"):
            continue
        else:
            break
    return n


def count_registry(committed, facts):
    """Every size from a source other than the sentence being tested."""
    reg = {"registered priors": len(facts.get("prior_evidence", {})),
           "registered criteria": len(facts.get("criteria", {})),
           "tables": len(re.findall(r"\*\*Table \d+\.\*\*", committed)),
           "figures": len(re.findall(r"\*\*Figure \d+\.\*\*", committed)),
           "consequences": enumerated_items(committed, "one-point comparison cannot see:")}
    i = committed.find("**Contributions.**")
    reg["contributions"] = (len(re.findall(r"^\((i|ii|iii|iv|v|vi)\) ", committed[i:], re.M))
                            if i >= 0 else None)
    return reg


def scan_spelled_counts(committed, reg):
    """-> (contradictions, subset_claims, listing).

    The window is a SENTENCE, not a line.  The manuscript is hard-wrapped, and the class's own
    motivating defect -- the abstract's count of counter-intuitive consequences -- lies across a
    line break in the shipped text: `... fix its detectability. Four` / `consequences are
    counter-intuitive ...`.  Scanning line by line made the class silent on exactly that form
    (measured: the wrapped defect gave "7 checked, 0 contradictions"; unwrapped, 8 and 1).

    `WS` is a whitespace run of AT MOST ONE newline, so a wrapped phrase is joined while a blank
    line or a paragraph break cannot.  A sentence-ending period also blocks the join, because the
    pattern requires whitespace immediately after the count word.

    A subset claim ("K of the M X") is checked for consistency with the derived M and k <= M and is
    also LISTED, because whether the sentence identifies its own subset cannot be read by a regex --
    the defect that motivated this class was an unnamed subset, not an impossible count.
    """
    contradictions, subsets, listing = [], [], []
    ws = r"(?:[ \t]*\n[ \t]*|[ \t]+)"
    nouns = "|".join(re.escape(n) for n, _ in COUNT_NOUNS)
    named = re.compile(r"\b(%s)%s((?:[a-z-]+%s)?(?:%s))\b" % (SPELLED_WORD, ws, ws, nouns), re.I)
    pair = re.compile(r"\b(%s)%sof%sthe%s(%s)%s([a-z-]+)"
                      % (SPELLED_WORD, ws, ws, ws, SPELLED_WORD, ws), re.I)

    # MARKUP IS NOT BETWEEN THE COUNT AND ITS NOUN.  "**All four** consequences" is a count of
    # consequences, and the emphasis markers hid it from the previous pattern.  The view below
    # replaces markup with spaces at IDENTICAL LENGTH, so every offset still maps to the shipped
    # text and the line numbers and table mask remain those of the manuscript itself.
    def emphasise_off(text):
        return re.sub(r"[*_]", lambda m: " " * len(m.group(0)), text)

    view = emphasise_off(committed)

    # table rows are numbers, not prose -- excluded by OFFSET, since the scan no longer walks lines
    excluded, off = [], 0
    for line in committed.split("\n"):
        if line.strip().startswith("|"):
            excluded.append((off, off + len(line)))
        off += len(line) + 1

    def line_of(pos):
        return committed.count("\n", 0, pos) + 1

    def in_table(pos):
        return any(a <= pos < b for a, b in excluded)

    def shown(text):
        return " ".join(text.split())

    spans = [m.span() for m in pair.finditer(view)]
    for m in named.finditer(view):
        if in_table(m.start()):
            continue
        # the subset form is the more specific construct: "three of the five consequences" carries
        # the count ONCE, so the plain scan must not report "five consequences" as a second defect.
        # The self-test caught this double count; one defective clause should yield one finding.
        if any(a <= m.start() < b for a, b in spans):
            continue
        key = dict(COUNT_NOUNS).get(shown(m.group(2)).lower())
        if key is None:
            continue
        got, want = SPELLED[m.group(1).lower()], reg.get(key)
        entry = (line_of(m.start()), shown(committed[m.start():m.end()]), key, got, want)
        listing.append(entry)
        if want is not None and got != want:
            contradictions.append(entry)
    for m in pair.finditer(view):
        if in_table(m.start()):
            continue
        k, total = SPELLED[m.group(1).lower()], SPELLED[m.group(2).lower()]
        noun = m.group(3).lower()
        key, want = dict(COUNT_NOUNS).get(noun), reg.get(dict(COUNT_NOUNS).get(noun))
        txt = shown(committed[m.start():m.end()])
        subsets.append((line_of(m.start()), txt, k, total, key, want))
        if k > total or (want is not None and total != want):
            contradictions.append((line_of(m.start()), txt, key or "?", total, want))
    return contradictions, subsets, listing


def counts_selftest():
    """A scanner that stopped matching would pass every run that depends on it.  Three sides: a
    contradiction must fire, the correct text must not, and the WRAPPED form -- the form the
    class's own window has to join, and the one the shipped defect takes -- must be exercised on
    both."""
    reg = {"registered priors": 3, "registered criteria": 4, "consequences": 4,
           "contributions": 4, "tables": 6, "figures": 6}
    cases = [
             # THE WRAPPED FORM, both sides.  The class's window is a sentence, and its motivating
             # defect is split by the manuscript's own reflow -- so the form its window must join is
             # the form its self-test has to exercise.  (The previous six cases were all single-line)
             ("detectability. Four\nconsequences are counter-intuitive", 0,
              "a WRAPPED count that agrees with the artefact does not fire"),
             ("detectability. Three\nconsequences are counter-intuitive", 1,
              "a WRAPPED count that contradicts the artefact fires"),
             ("Three\n\nconsequences are counter-intuitive", 0,
              "a blank line is NOT joined: the window is one newline, not a paragraph"),
             ("**All four** consequences are invisible", 0,
              "markup between the count and its noun does not hide the count"),
             ("**All three** consequences are invisible", 1,
              "an emphasised count that contradicts the artefact still fires"),
             ("the four registered priors all `CONFIRMED`", 1, "a count that contradicts the artefact fires"),
             ("the three registered priors all `CONFIRMED`", 0, "the correct count does not fire"),
             ("All four consequences are invisible to a one-point comparison", 0, "a matching count does not fire"),
             ("Three of the five consequences are invisible", 1, "a subset claim over the wrong total fires"),
             ("only three of the four consequences are named", 0, "a consistent subset claim is not a contradiction"),
             ("six figures and six tables", 0, "two correct counts in one sentence do not fire")]
    bad = []
    for text, want, why in cases:
        got = len(scan_spelled_counts(text, reg)[0])
        if got != want:
            bad.append("%r -> %d contradictions, expected %d (%s)" % (text, got, want, why))
    return not bad, "%d cases, %d unexpected: %s" % (len(cases), len(bad), "; ".join(bad)[:150])

rows = []


def check(name, ok, detail=""):
    rows.append((name, bool(ok), detail))
    print("%-8s %-44s %s" % ("PASS" if ok else "FAIL", name, detail))


def run_assemble(out_path, facts=None, cwd=None):
    cmd = [sys.executable, os.path.join(HERE, "assemble.py"), "--out", out_path]
    if facts:
        cmd += ["--facts", facts]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    r = subprocess.run(cmd, cwd=cwd or HERE, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
    return r


def main():
    ms_path = os.path.join(HERE, "manuscript.md")
    if not os.path.exists(ms_path):
        check("exists/manuscript.md", False, "run assemble.py first")
        return 1
    committed = open(ms_path, encoding="utf-8").read()

    # ---------------------------------------------------------------- RECOMPUTE --
    foreign = tempfile.mkdtemp(prefix="ms_chk_")
    try:
        fresh_path = os.path.join(foreign, "manuscript.md")
        r = run_assemble(fresh_path, cwd=foreign)
        check("recompute/assembly_from_a_foreign_cwd",
              r.returncode == 0 and os.path.exists(fresh_path),
              r.stderr.strip()[:120])
        fresh = open(fresh_path, encoding="utf-8").read() if os.path.exists(fresh_path) else ""
        check("recompute/byte_identical_to_committed", fresh == committed,
              "" if fresh == committed else "%d vs %d bytes" % (len(fresh), len(committed)))

        # ------------------------------------------------------------------ READ --
        # One fact is changed in a copy of the artefact; the render must move.
        facts_path = os.path.join(HERE, "canonical_results.json")
        blob = json.load(open(facts_path, encoding="utf-8"))
        blob["manuscript_facts"]["crit_a"]["median_abs_error"] = 0.99999
        mut_path = os.path.join(foreign, "mutated_results.json")
        with open(mut_path, "w", encoding="utf-8") as fh:
            json.dump(blob, fh)
        mut_out = os.path.join(foreign, "manuscript_mutated.md")
        r2 = run_assemble(mut_out, facts=mut_path, cwd=foreign)
        mutated = open(mut_out, encoding="utf-8").read() if os.path.exists(mut_out) else ""
        check("read/mutation_control_fires",
              r2.returncode == 0 and "0.99999" in mutated and mutated != committed,
              "rendered 0.99999" if "0.99999" in mutated else "the mutation did not reach the prose")
        # a second control: an absent fact must be a hard error, not a silent blank
        blob2 = json.load(open(facts_path, encoding="utf-8"))
        del blob2["manuscript_facts"]["crit_b"]["tol"]
        bad_path = os.path.join(foreign, "broken_results.json")
        with open(bad_path, "w", encoding="utf-8") as fh:
            json.dump(blob2, fh)
        r3 = run_assemble(os.path.join(foreign, "broken.md"), facts=bad_path, cwd=foreign)
        check("read/missing_fact_is_fatal", r3.returncode != 0,
              "exit %d" % r3.returncode)
    finally:
        shutil.rmtree(foreign, ignore_errors=True)

    # -------------------------------------------------------------- COMPLETE ----
    check("complete/no_placeholder_survives", not PLACEHOLDER.search(committed),
          PLACEHOLDER.search(committed).group(0) if PLACEHOLDER.search(committed) else "")
    check("complete/no_reference_marker", "<!-- REFERENCES -->" not in committed)
    n_ph = sum(len(PLACEHOLDER.findall(open(os.path.join(HERE, p), encoding="utf-8").read()))
               for p in PARTS)
    check("numbers/placeholder_count_gated", n_ph >= MIN_PLACEHOLDERS,
          "%d placeholders (floor %d)" % (n_ph, MIN_PLACEHOLDERS))

    # -------------------------------------------------------------- CITATIONS ---
    parts_text = "".join(open(os.path.join(HERE, p), encoding="utf-8").read() for p in PARTS)
    cited = []
    for key in CITE.findall(parts_text):
        if key not in cited:
            cited.append(key)
    refs = {}
    refs_path = os.path.join(HERE, "references.md")
    if os.path.exists(refs_path):
        for line in open(refs_path, encoding="utf-8"):
            if line.startswith("[@"):
                key, _, text = line.rstrip("\n")[2:].partition("] ")
                refs[key] = text
    check("citations/every_cited_key_has_an_entry", set(cited) <= set(refs),
          "missing: %s" % sorted(set(cited) - set(refs))[:5])
    check("citations/every_entry_is_cited", set(refs) <= set(cited),
          "uncited: %s" % sorted(set(refs) - set(cited))[:5])
    check("citations/count_meets_the_bar", len(cited) >= MIN_REFS,
          "%d cited / %d required" % (len(cited), MIN_REFS))
    rc_path = os.path.join(HERE, "reference-check.md")
    rc = open(rc_path, encoding="utf-8").read() if os.path.exists(rc_path) else ""
    checked_keys = set(re.findall(r"^\|\s*`?([A-Za-z0-9_.:-]+)`?\s*\|", rc, re.M))
    check("citations/every_entry_is_authenticity_checked", set(cited) <= checked_keys,
          "%d of %d in reference-check.md" % (len(set(cited) & checked_keys), len(cited)))

    # ------------------------------------------------------------ PUNCTUATION ------
    # Measured on the manuscript's OWN compiled list -- the artefact a reader meets --
    # and over the whole list, since the defect is a property of the renderer and it
    # touched 55 entries at once.  The condition lives in verify_refs.render(); this is
    # the guard that fires on every reproduction, without network access.
    # The entry list is the block under the References heading, so the denominator below
    # is the bibliography's own length.  Counting every line that begins with a marker
    # instead gave 107 "entries" for a 102-entry list: five body paragraphs open with a
    # citation.  The length is asserted against the cited-key count, so a truncated or
    # renumbered list fails here too.
    ref_block = []
    if "## References" in committed:
        ref_block = [l for l in committed.split("## References", 1)[1].split("\n")[1:]
                     if re.match(r"^\[\d+\] ", l)]
    dbl = [l[:70] for l in ref_block if ".." in l]
    check("punctuation/no_doubled_period_in_the_references",
          not dbl and len(ref_block) == len(cited),
          "%d entries in the reference list, %d carrying two adjacent periods%s%s" %
          (len(ref_block), len(dbl),
           "" if len(ref_block) == len(cited) else " (list length != %d cited keys)" % len(cited),
           (": " + "; ".join(dbl[:3])) if dbl else ""))

    # ------------------------------------------------------------------ LAYOUT --
    caps = CAPTION.findall(committed)
    for kind in ("Table", "Figure"):
        nums = [int(n) for k, n in caps if k == kind]
        check("layout/%s_numbered_in_document_order" % kind.lower(),
              nums == sorted(nums) and nums == list(range(1, len(nums) + 1)),
              "numbers %s" % nums)
        uncited = [n for n in nums
                   if len(re.findall(r"\b%s %d\b" % (kind, n), committed)) < 2]
        check("layout/every_%s_cited_in_the_text" % kind.lower(), not uncited,
              "not cited: %s" % uncited)
    embeds = [int(n) for n, _ in EMBED.findall(committed)]
    cap_figs = [int(n) for k, n in caps if k == "Figure"]
    check("layout/every_figure_embedded", embeds == cap_figs,
          "embeds %s vs captions %s" % (embeds, cap_figs))
    missing_files = [p for _, p in EMBED.findall(committed)
                     if not os.path.exists(os.path.join(HERE, p))]
    check("layout/every_embedded_file_exists", not missing_files, str(missing_files))

    # ------------------------------------------------------------------- COUNTS --
    # A count written in words is a measurement (see the COUNTS note at the top of this file).
    facts_blob = json.load(open(os.path.join(HERE, "canonical_results.json"), encoding="utf-8"))
    reg = count_registry(committed, facts_blob)
    bad_counts, subset_claims, spelled = scan_spelled_counts(committed, reg)
    check("counts/every_collection_size_is_derivable",
          all(v is not None for v in reg.values()),
          "derived %s" % ", ".join("%s=%s" % (k, reg[k]) for k in sorted(reg)))
    check("counts/spelled_out_counts_agree_with_the_artefact", not bad_counts,
          "%d spelled counts checked, %d contradict the derived size%s"
          % (len(spelled), len(bad_counts),
             (": " + "; ".join("line %d %r != %s" % (l, t, w) for l, t, _, _, w in bad_counts))
             if bad_counts else ""))
    for lineno, text, key, got, want in spelled:
        print("    line %4d  %-26s %d %s" % (lineno, text, got,
                                             "= %s" % key if got == want else "CONTRADICTS %s=%s" % (key, want)))
    for lineno, text, k, total, key, want in subset_claims:
        print("    SUBSET CLAIM  line %4d  %-32s k=%d of M=%d%s"
              % (lineno, text, k, total, " (matches %s)" % key if key and total == want else ""))
    selftest_ok, selftest_detail = counts_selftest()
    check("counts/scanner_selftest", selftest_ok, selftest_detail)

    # ------------------------------------------------------------------- AUDIT --
    # Numbers outside a placeholder: listed so a hand-typed measurement is seen, not trusted.
    audit = []
    for i, line in enumerate(committed.split("\n"), 1):
        if line.strip().startswith("|") or line.strip().startswith("\\") or "figures/" in line:
            continue
        for m in re.finditer(r"`([^`]*)`", line):
            if TABLE_ROW_DECIMAL.search(m.group(1)):
                audit.append((i, m.group(1)))
    check("audit/number_candidates_reported", True,
          "%d inline code spans carry a decimal (listed below, NOT verified here: this class is a "
          "reading aid. The verification is instrument_audit.py check D4, which resolves every "
          "placeholder through the renderer and requires each hand-typed value to be a value the "
          "artefact records, with a declared residual)" % len(audit))
    for i, tok in audit[:40]:
        print("    line %4d  %s" % (i, tok))
    if len(audit) > 40:
        print("    ... %d more" % (len(audit) - 40))

    failed = [n for n, ok, _ in rows if not ok]
    print("\nmanuscript check: %d run, %d failed" % (len(rows), len(failed)))
    if failed:
        for n in failed:
            print("  FAILED:", n)
    print("verdict:", "OK" if not failed else "NOT READY")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
