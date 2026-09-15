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
  LAYOUT     tables and figures are numbered in document order, embedded, captioned,
             and cited in the running text; every embedded figure file exists.
  AUDIT      numbers that are not placeholders are listed for review, so that a
             hand-typed measurement has to be looked at rather than trusted.

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
          "%d inline code spans carry a decimal (reviewed below)" % len(audit))
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
