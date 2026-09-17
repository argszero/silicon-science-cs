#!/usr/bin/env python3
"""Issue #47 -- the README's own figures, each read against the artefact that OWNS it.

    python3 readme_check_v1.py            # check: exit 0 iff every figure matches
    python3 readme_check_v1.py --selftest # liveness: one planted wrong figure per check

WHY THIS FILE EXISTS.  A number written into a README is a claim about some other artefact, and
nothing in this package read the README's numbers against those artefacts.  Three of them had drifted
by two rounds: the step count still said eight when `reproduce.sh` ran nine, the freeze-check count
said 55 when the check reported 57, and the coordinate bullet typed "12 source files" while the census
enumerated 15 (it had listed a draft file that the commit does not ship).  Every one of those figures
was read by a human and none by a check -- the same failure this package has been bitten by twice
already: the object that is verified and the object a reader opens are two artefacts.

WHAT IS CHECKED, and against what:

* the quoted verdict block -- `facts recomputed` and the four criterion states, against
  `canonical_results.json` (the file the runner writes, not the runner's own printout);
* the stage table -- against the table `run.log` printed in the same run, line for line (a
  repaginated table differs, which is the defect R330 found in this very table);
* the freeze-check count and the external-mutation count, against their result files' own counts;
* the support counts (keys / occurrences / multi-sentence keys), against the verdict rows;
* the stated-difference count, against `reference-check.md` AND recomputed from `references.md`;
* the reference-entry count, against the manuscript's numbered `## References` section;
* the step count, against `reproduce.sh`'s own step markers;
* the census's source-file count, against the directory -- and the README must NAME that instrument
  rather than type a number, because the list is enumerated at run time;
* the counts the script table states for the two CHECKER modules, against the modules themselves: every
  other figure in this README has an artefact that owns it and these two had none, so the table drifted
  (it said nine checks and nine mutations for `manuscript_check_v1.py` while the module held eleven of
  each, and nothing read either number).  The owner of a program's count is the program, so the check
  asks it and compares -- a count with no owner is a count that will not be read again.

A figure whose anchor is missing fails rather than passes: "the claim is not in the file" and "the
claim is right" must never look alike.  `--selftest` plants one wrong figure per check and requires
that check -- and ONLY that check -- to fail, so every check is known to be able to fail, and to fail
on its own claim.
"""
import importlib.util
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

FILES = ("README.md", "reproduce.sh", "run.log", "canonical_results.json",
         "freeze_check_v1_results.json", "external_cell_mutation_v1_results.json",
         "support_verdicts_v1.json", "references.md", "reference-check.md", "manuscript.md")

WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
           "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def load():
    return {f: io.open(os.path.join(HERE, f), encoding="utf-8").read() for f in FILES}


def grab(pat, text, flags=0):
    m = re.search(pat, text, flags)
    return m.groups() if m else None


def table(text):
    """The stage table as printed: the header line plus every consecutive row-shaped line after it."""
    out, started = [], False
    for raw in text.split("\n"):
        s = raw.strip()
        if not started:
            if s.startswith("stage") and "script" in s and "flag agrees" in s:
                started, out = True, [s]
            continue
        if re.match(r"^\S+\s+\S+\s+\S+\s+\S+\s+\S+$", s):
            out.append(s)
        else:
            break
    return out


def marker_carriers(entries):
    """Entries carrying the journal's element: a `Difference` marker after the LAST link token.

    The rule is restated here rather than imported so this file can fail on its own artefact; the two
    other implementations in the package are checked against each other by their own selftests.
    """
    ok = 0
    for e in entries:
        toks = list(re.finditer(r"https?://\S+|arXiv:[0-9.]+v?\d*|\b10\.\d{4,5}/\S+", e))
        if toks and toks[-1].end() < len(e) and "Difference" in e[toks[-1].end():]:
            ok += 1
    return ok


def ref_entries(text):
    return re.findall(r"(?m)^\[@[^\]]+\].*$", text)


# ---------------------------------------------------------------------------------------------
# Each check returns (ok, detail).  `t` is the dict of file texts; the artefacts are parsed in
# `ctx()` so a broken JSON file fails the checks that need it instead of raising at import.
# ---------------------------------------------------------------------------------------------
def ctx(t):
    return {"canon": json.loads(t["canonical_results.json"]),
            "fz": json.loads(t["freeze_check_v1_results.json"]),
            "ext": json.loads(t["external_cell_mutation_v1_results.json"]),
            "sup": json.loads(t["support_verdicts_v1.json"])}


def ck_facts(t, c):
    g = grab(r"facts recomputed: (\d+) \| disagreeing with the artefact's own value: (\d+)",
             t["README.md"])
    n = len(c["canon"]["facts"])
    return (g is not None and int(g[0]) == n and int(g[1]) == 0
            and c["canon"]["ALL_PASS"] is True,
            "README %s | canonical_results.json: %d fact(s), ALL_PASS=%s"
            % (g, n, c["canon"]["ALL_PASS"]))


def ck_states(t, c):
    st = c["canon"]["criteria"]
    want = "criteria: " + ", ".join(
        "%s=%s" % (k[0], "MET" if st[k]["state"] == "measured" else "UNMET") for k in sorted(st))
    return want in t["README.md"], "want %r | present=%s" % (want, want in t["README.md"])


def ck_table(t, c):
    r_rows, l_rows = table(t["README.md"]), table(t["run.log"])
    n = len(c["canon"]["stages"])
    diff = next(("%s != %s" % (a, b) for a, b in zip(r_rows, l_rows) if a != b), "")
    return ((r_rows == l_rows and len(l_rows) - 1 == n),
            "%d README row(s) vs %d run.log row(s) vs %d stage(s)%s"
            % (len(r_rows) - 1, len(l_rows) - 1, n, (" | first difference: " + diff) if diff else ""))


def ck_freeze(t, c):
    g1 = grab(r"\*\*(\d+) checks\*\* re-deriving every number in `design_freeze_v1\.md`", t["README.md"])
    g2 = grab(r"\((\d+) checks, the F0b amendment included\)", t["README.md"])
    want = str(c["fz"]["n_checks"])
    return (g1 is not None and g2 is not None and g1[0] == g2[0] == want,
            "README %s / %s | freeze_check_v1_results.json: %s check(s)" % (g1, g2, want))


def ck_mutations(t, c):
    g1 = grab(r"\*\*(\d+) mutations\*\* of the external cell", t["README.md"])
    g2 = grab(r"\((\d+) mutations\)", t["README.md"])
    want = str(c["ext"]["n_mutations"])
    return (g1 is not None and g2 is not None and g1[0] == g2[0] == want,
            "README %s / %s | external_cell_mutation_v1_results.json: %s mutation(s)"
            % (g1, g2, want))


def ck_support(t, c):
    keys = [rid.split(":", 2)[1] for rid in c["sup"]["rows"]]
    distinct, multi = len(set(keys)), len(set(k for k in keys if keys.count(k) > 1))
    g = grab(r"(\d+) keys appear as (\d+) occurrences, and (\d+)\s+keys are cited", t["README.md"])
    return (g is not None and (int(g[0]), int(g[1]), int(g[2])) == (distinct, len(keys), multi),
            "README %s | verdict rows: %d key(s), %d occurrence(s), %d multi-sentence key(s)"
            % (g, distinct, len(keys), multi))


def ck_difference(t, c):
    entries = ref_entries(t["references.md"])
    g1 = grab(r"rendered entries carrying the stated difference: (\d+) of\s+(\d+)", t["README.md"])
    g2 = grab(r"rendered entries carrying the stated difference.*?\|\s*\*\*(\d+) of (\d+)\*\*",
              t["reference-check.md"], re.S)
    carriers = marker_carriers(entries)
    return (g1 is not None and g2 is not None and g1 == g2
            and (int(g2[0]), int(g2[1])) == (carriers, len(entries)),
            "README %s / reference-check.md %s | references.md: %d carrier(s) of %d entr(y|ies)"
            % (g1, g2, carriers, len(entries)))


def ck_refcount(t, c):
    md = t["manuscript.md"]
    m_entries = re.findall(r"(?m)^\[(\d+)\]", md[md.index("## References"):])
    entries = ref_entries(t["references.md"])
    g1 = grab(r"`(\d+)` entries in one `## References` section", t["README.md"])
    g2 = grab(r"\((\d+) lines\)\. Each names what that work", t["README.md"])
    return (g1 is not None and g2 is not None and g1[0] == g2[0] == str(len(m_entries)) == str(len(entries)),
            "README %s / %s | manuscript.md: %d numbered entry(ies); references.md: %d"
            % (g1, g2, len(m_entries), len(entries)))


def ck_steps(t, c):
    g = grab(r"the (\w+)-step run below", t["README.md"])
    steps = re.findall(r"printf '\\n== (\d+)\.", t["reproduce.sh"])
    return (g is not None and WORDNUM.get(g[0]) == len(steps)
            and steps == [str(i) for i in range(1, len(steps) + 1)],
            "README '%s' (%s) | reproduce.sh: %d step marker(s) %s"
            % (g[0] if g else None, WORDNUM.get(g[0]) if g else None, len(steps), steps))


def ck_census(t, c):
    typed = re.search(r"over \d+ source file", t["README.md"])
    named = "a census over **every** `.py`/`.sh` file the package ships" in t["README.md"]
    g = grab(r"coordinate census over (\d+) source file", t["run.log"])
    on_disk = len([f for f in os.listdir(HERE) if f.endswith((".py", ".sh"))])
    return (typed is None and named and g is not None and int(g[0]) == on_disk,
            "README types a count: %s | names the instrument: %s | run.log %s vs %d file(s) on disk"
            % (typed.group(0) if typed else "no", named, g, on_disk))


def ck_verdicts(t, c):
    """Every verdict `reproduce.sh` prints is listed in the README, and nothing else is.

    The list is one line per VERDICT, so it goes stale the moment a step is added -- it already had
    (the two flip-bound verdicts of R347 were never added).  The script is the owner: it prints a
    label, and the label is the claim.
    """
    labels = re.findall(r'(?m)^\s*verdict "([^"]+)"', t["reproduce.sh"])
    blocks = re.findall(r"```[a-z]*\n(.*?)```", t["README.md"], re.S)
    block = next((b for b in blocks if "REPRODUCE: ALL GREEN" in b), None)
    listed = re.findall(r"(?m)^  ([^:\n]+): OK$", block or "")
    return (block is not None and listed == labels,
            "README lists %s | reproduce.sh prints %s" % (listed, labels))


def ck_repro_freeze(t, c):
    g = grab(r"design-freeze document against the artefacts -- (\d+) checks", t["reproduce.sh"])
    want = str(c["fz"]["n_checks"])
    return (g is not None and g[0] == want,
            "reproduce.sh %s | freeze_check_v1_results.json: %s check(s)" % (g, want))


def ck_repro_stages(t, c):
    g = grab(r"#   1\. the (\w+) stages \(", t["reproduce.sh"])
    n = len(c["canon"]["stages"])
    return (g is not None and WORDNUM.get(g[0]) == n,
            "reproduce.sh '%s' (%s) | canonical_results.json: %d stage(s)"
            % (g[0] if g else None, WORDNUM.get(g[0]) if g else None, n))


TOOL_COUNT_ROWS = ("manuscript_check_v1.py", "readme_check_v1.py")


def _tool_lists(fname):
    """Ask the program for its own counts.

    A count about a tool has no artefact behind it unless the tool is read.  The module's own lists are
    the owner: this module answers for itself -- loading a second copy of itself would be a second owner
    -- and any other module is loaded from its file, which is the same object the run reads.
    """
    if fname == "readme_check_v1.py":
        return len(CHECKS), len(MUTATIONS)
    spec = importlib.util.spec_from_file_location(
        "_asked_" + os.path.splitext(fname)[0], os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return len(mod.CHECKS), len(mod.MUTATIONS)


def ck_tool_counts(t, c):
    """The counts the script table states for the two checker modules are the lists those modules hold.

    The rule, stated as it is implemented (a rule implemented more narrowly than it is written is the
    defect this very round repaired in the manuscript check): the README states, for
    `manuscript_check_v1.py` and `readme_check_v1.py`, one `(N checks, M mutations)` pair each; the
    multiset of such pairs in the document must equal the modules' own (checks, mutations) counts, and
    each pair must stand in the table row that names its module -- the README carries these counts in
    that one shape and nowhere else, so a pair appearing twice, or a third pair, fails.

    Every other figure in this README is bound to a result file, a printed log line or the directory;
    these two were bound to nothing, so the table drifted.  Measured at an export of the head this check
    was written against: the README stated nine checks and nine mutations for `manuscript_check_v1.py`
    while the module held eleven of each, and the README check was green.  A number is only read if
    something reads it; when the owner is a program, it is read by asking the program.
    """
    readme = t["README.md"]
    pairs = sorted((int(a), int(b))
                   for a, b in re.findall(r"\((\d+) checks, (\d+) mutations\)", readme))
    want = {fname: _tool_lists(fname) for fname in TOOL_COUNT_ROWS}
    if sorted(want.values()) != pairs:
        return False, "the README states the pair(s) %s; the modules hold %s" % (
            pairs, sorted(want.values()))
    rows = []
    for fname in TOOL_COUNT_ROWS:
        n, m = want[fname]
        row = [line for line in readme.splitlines() if line.startswith("| `%s` |" % fname)]
        if len(row) != 1 or "(%d checks, %d mutations)" % (n, m) not in row[0]:
            return False, ("the README's row for `%s` does not carry `(%d checks, %d mutations)` "
                           "(%d row(s) name it)" % (fname, n, m, len(row)))
        rows.append("`%s` %d/%d" % (fname, n, m))
    return True, "README pair(s) %s == the modules' own lists (%s)" % (pairs, "; ".join(rows))


CHECKS = [
    ("readme/facts_recomputed_is_the_artefact's_own_count", ck_facts),
    ("readme/criterion_states_are_their_recorded_states", ck_states),
    ("readme/stage_table_is_the_one_run_log_printed", ck_table),
    ("readme/freeze_check_count_is_the_freeze_result's", ck_freeze),
    ("readme/mutation_count_is_the_mutation_result's", ck_mutations),
    ("readme/support_counts_are_the_verdict_rows", ck_support),
    ("readme/stated_difference_count_is_the_rendered_layer", ck_difference),
    ("readme/reference_count_is_the_manuscript's_section", ck_refcount),
    ("readme/step_count_is_reproduce_sh's_own_markers", ck_steps),
    ("readme/census_count_is_the_directory_and_is_not_typed", ck_census),
    ("readme/verdict_list_is_the_one_reproduce_sh_prints", ck_verdicts),
    ("readme/tool_counts_are_the_modules'_own_lists", ck_tool_counts),
    ("reproduce_sh/freeze_check_count_is_the_freeze_result's", ck_repro_freeze),
    ("reproduce_sh/stage_count_is_the_runner's_stage_list", ck_repro_stages),
]

# (check name, file, the figure to break, what to replace it with).  Breaking a figure must fail its
# own check and no other -- an exact count, not "something went red": a mutation battery whose cases
# already fail for other reasons proves nothing (the confounded battery of R343).
def mut_step_count(texts):
    """Break the README's step-count word wherever it stands, wrapping and all.

    Same defect as `mut_facts_recomputed`'s pinned figure: the anchor `the ten-step run below` is a
    literal embedding a word the README owns, and re-wrapping the sentence is enough to make it match
    nothing -- which happened while this very paragraph was corrected.  The word is read from the
    README instead of typed.
    """
    m = re.search(r"(the\s+)([a-z]+)(-step run below)", texts["README.md"])
    if not m:
        return ("README.md", None, None)
    wrong = "nine" if m.group(2) != "nine" else "eight"
    return ("README.md", m.group(0), m.group(1) + wrong + m.group(3))


def mut_facts_recomputed(texts):
    """Break the README's `facts recomputed` figure wherever it stands.

    DERIVED, NOT PINNED.  The first version typed the figure (`facts recomputed: 77 |`), so when the
    figure legitimately moved to 113 the anchor matched nothing and the battery reported a failure
    about a correction that had just made the package correct.  A mutation anchor is itself a claim
    about an artefact, and a typed copy of a number the package can change is the defect this whole
    file exists to catch -- so the case reads the README and breaks the value it finds.
    """
    m = re.search(r"facts recomputed: (\d+) \|", texts["README.md"])
    if not m:
        return ("README.md", None, None)
    n = int(m.group(1))
    return ("README.md", "facts recomputed: %d |" % n, "facts recomputed: %d |" % (n - 1))


MUTATIONS = [
    ("readme/facts_recomputed_is_the_artefact's_own_count", mut_facts_recomputed),
    ("readme/criterion_states_are_their_recorded_states",
     "README.md", "criteria: a=MET, b=MET", "criteria: a=UNMET, b=MET"),
    ("readme/stage_table_is_the_one_run_log_printed",
     "README.md", "  anchor       anchor_smoke.py                       8      0 yes",
     "  anchor       anchor_smoke.py                       9      0 yes"),
    ("readme/freeze_check_count_is_the_freeze_result's",
     "README.md", "**57 checks**", "**56 checks**"),
    ("readme/mutation_count_is_the_mutation_result's",
     "README.md", "**13 mutations**", "**12 mutations**"),
    ("readme/support_counts_are_the_verdict_rows",
     "README.md", "237 occurrences", "236 occurrences"),
    ("readme/stated_difference_count_is_the_rendered_layer",
     "README.md", "stated difference: 156 of", "stated difference: 155 of"),
    ("readme/reference_count_is_the_manuscript's_section",
     "README.md", "`156` entries in one", "`157` entries in one"),
    ("readme/step_count_is_reproduce_sh's_own_markers", mut_step_count),
    ("readme/census_count_is_the_directory_and_is_not_typed",
     "README.md", "a census over **every** `.py`/`.sh` file the package ships",
     "a census over all 12 source files"),
    ("readme/verdict_list_is_the_one_reproduce_sh_prints",
     "README.md", "  design freeze: OK\n", ""),
    ("reproduce_sh/freeze_check_count_is_the_freeze_result's",
     "reproduce.sh", "-- 57 checks, including the digest table",
     "-- 56 checks, including the digest table"),
    ("reproduce_sh/stage_count_is_the_runner's_stage_list",
     "reproduce.sh", "the eight stages (seven frozen", "the nine stages (seven frozen"),
    ("readme/tool_counts_are_the_modules'_own_lists",
     "README.md", "(11 checks, 12 mutations)", "(10 checks, 12 mutations)"),
]


def run_all(texts):
    """Every check, each in its own guard: a check that raises is a FAILED check, not a crash."""
    try:
        c = ctx(texts)
    except Exception as exc:
        return [(n, False, "the artefacts a check reads could not be parsed: %s: %s"
                 % (type(exc).__name__, exc)) for n, _ in CHECKS]
    rows = []
    for name, fn in CHECKS:
        try:
            ok, detail = fn(texts, c)
        except Exception as exc:
            ok, detail = False, "raised %s: %s" % (type(exc).__name__, exc)
        rows.append((name, bool(ok), detail))
    return rows


def report(rows):
    bad = 0
    for name, ok, detail in rows:
        bad += 0 if ok else 1
        print("%-6s %-58s %s" % ("PASS" if ok else "FAIL", name, detail))
    return bad


def selftest():
    texts = load()
    # The battery runs on a CLEAN base.  If the shipped package is already failing, the cases would
    # prove nothing (every mutation would show the same failures for someone else's reason) -- the
    # confounded battery of R343.  Say so instead of reporting cases that fire for the wrong reason.
    base = [n for n, ok, _ in run_all(texts) if not ok]
    if base:
        print("FAIL   the battery needs a clean base; already failing: %s" % base)
        return 1
    # Coverage is itself a claim about the battery and needs its own read: a check with NO planted
    # figure is decoration -- nothing shows it can fail -- and the case list is what claims it can.
    uncovered = [n for n, _ in CHECKS if n not in set(case[0] for case in MUTATIONS)]
    if uncovered:
        print("FAIL   %d check(s) carry no planted figure: %s" % (len(uncovered), uncovered))
        return 1
    bad = 0
    for name, spec, *rest in MUTATIONS:
        f, old, new = spec(texts) if callable(spec) else (spec,) + tuple(rest)
        if old is None:
            print("FAIL   %-58s the mutation anchor could not be derived from %s" % (name, f))
            bad += 1
            continue
        hits = texts[f].count(old)
        if hits != 1:
            print("FAIL   %-58s the mutation anchor occurs %d time(s) in %s" % (name, hits, f))
            bad += 1
            continue
        kept = dict(texts)
        kept[f] = texts[f].replace(old, new)
        failed = [n for n, ok, _ in run_all(kept) if not ok]
        ok = failed == [name]
        print("%-6s %-58s failed=%s expected=[%r]" % ("PASS" if ok else "FAIL", name, failed, name))
        bad += 0 if ok else 1
    print("selftest: %d case(s), %d failure(s) over %d check(s)" % (len(MUTATIONS), bad, len(CHECKS)))
    return 1 if bad else 0


def main():
    rows = run_all(load())
    bad = report(rows)
    print("readme check: %d check(s), %d failed" % (len(rows), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
