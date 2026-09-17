#!/usr/bin/env python3
"""Issue #47 -- the MANUSCRIPT's typed claims, each read against the object that owns it.

    python3 manuscript_check_v1.py            # check: exit 0 iff every typed claim matches its owner
    python3 manuscript_check_v1.py --selftest # liveness: one planted wrong claim per check

WHY THIS FILE EXISTS.  `readme_check_v1.py` binds the README's figures to the artefacts that own them,
and until this file existed **nothing bound the manuscript's prose** -- so the same defect kept
appearing in the carrier with no check, found by review instead of by the package.  The round-2 review
located three instances (a step count that disagreed with the script's own printed step list, a
freeze-check count that disagreed with its result file, and a roadmap pointing one section past its
object); the author's own census of the manuscript then found a fourth of the same class that the
review had not carried (SS6.3's multi-sentence key count, which then read "51 appear in more than one
sentence" where the verdict rows say 58) and a fifth sentence-shaped one (SS3.5's sentence, which then
read "roughly 13 cluster MDEs" where paging's value is 1.53).  A class is fixed by binding the carrier,
not by repairing instances -- four repairs without a binding guarantee a fifth.

The probe that closed the fifth then found a SIXTH inside the very sentence it reads: the repaired
sentence typed the aggregate "up to 13" beside its three placeholders, so the rule this file states and
the implementation of it disagreed (measured in `ck_witness_magnitudes`, which now reads the rule as
written).  A repair that leaves a magnitude in the prose is not a binding.

WHAT IS CHECKED, and against what:

* **the typed counts** -- each is a declared claim, read out of the manuscript's parts (the source the
  assembler renders from, not its own output) and compared with the value recomputed from the artefact
  that owns it: the run's step count against `reproduce.sh`'s own step banners, the freeze check's
  count against `freeze_check_v1_results.json:n_checks`, the support counts against
  `support_verdicts_v1.json:rows`, the mutation count against
  `external_cell_mutation_v1_results.json:n_mutations`, the detectors-fired count against the census's
  own printed line in `run.log`, the MDE inflation range against the sufficiency artefact's own
  min-max of `mde_inflation_factor`, and the liveness bound against the runner's own case list;
* **every section reference resolves** -- `Section N` / `§N` must name a heading the manuscript
  actually carries.  A phantom "Section 9" is the instance that motivated this: the paragraph's only
  job is navigation, so a reference to a section that does not exist fails the reader silently;
* **the roadmap's claims are about the sections they name** -- SS1.5 is a list of sentences of the form
  "Section N <verb> <object>"; the object is matched against the heading SS N carries.  This is what
  the off-by-one broke: "Section 8 states the threats" named a section that exists (the conclusion)
  and describes the wrong one, which a resolution test alone cannot see.

A claim whose anchor is missing FAILS rather than passes: "the claim is not in the manuscript" and
"the claim is right" must never look alike.  `--selftest` plants one wrong claim per check and requires
that check -- and ONLY that check -- to fail.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = ("manuscript_part1.md", "manuscript_part2.md", "manuscript_part3.md")
FILES = PARTS + ("reproduce.sh", "run.log", "canonical_results.json",
                 "freeze_check_v1_results.json", "external_cell_mutation_v1_results.json",
                 "support_verdicts_v1.json", "sufficiency_v1_results.json", "canonical_runner.py")

WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
           "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}

# SS1.5's roadmap: each sentence names a section AND describes it, so the check is two-part -- the
# section must exist, and its heading must carry the declared keyword.
ROADMAP = [
    ("Section 2", "Related work"),
    ("Section 3", "Instrument and design"),
    ("Section 4", "Results"),
    ("Section 5", "The limits"),
    ("Section 6", "Methodology"),
    ("Section 7", "The registered priors"),
    ("Section 8", "Conclusion"),
]


def load():
    return {f: io.open(os.path.join(HERE, f), encoding="utf-8").read() for f in FILES}


def manuscript(texts):
    """The manuscript's parts, concatenated -- the SOURCE the assembler renders from.

    Checking the parts rather than the rendered `manuscript.md` is deliberate: a repair that fixes the
    rendered file and not the parts is undone by the next assembly, and the parts are what a
    re-rendering reads.
    """
    return "\n".join(texts[p] for p in PARTS)


def _multi(support_json):
    out = {}
    for rid in json.loads(support_json)["rows"]:
        k = rid.split(":")[1]
        out[k] = out.get(k, 0) + 1
    return out


def _detectors(run_log):
    m = re.search(r"detectors firing on a planted instance:\s*(\d+) of (\d+)", run_log)
    if not m:
        return None
    if m.group(1) != m.group(2):
        return None                      # a detector that does not fire is not "8 of 8"
    return m.group(1)


def _inflation(suf_json):
    d = json.loads(suf_json)
    blocks = d["part_A_why_the_cell_design_cannot_resolve"]["blocks"]
    vals = [b["mde_inflation_factor"] for b in blocks]
    if not vals:
        return None
    return "%.1f\u2013%.1f\u00d7" % (min(vals), max(vals))


def _liveness_cases(texts):
    src = texts["canonical_runner.py"]
    start = src.index("    cases = [")
    end = src.index("\n    ]", start)
    return len(re.findall(r'\n        \("', src[start:end]))


# ----------------------------------------------------------------------------- checks
def ck_steps(texts, c):
    m = re.search(r"It has \*\*(\w+)\*\* steps,", manuscript(texts))
    want = len(re.findall(r"^printf '\\n== \d+\.", texts["reproduce.sh"], re.M))
    if want == 0:
        return False, "reproduce.sh prints no step banner: the instrument found nothing to count"
    if not m:
        return False, "the step sentence is not in the manuscript parts"
    got = WORDNUM.get(m.group(1), m.group(1))
    return got == want, "manuscript %r (%s) | reproduce.sh prints %d step marker(s)" % (
        m.group(1), got, want)


def ck_liveness(texts, c):
    """The sentence's bound must be the runner's own case list, and both mechanisms must be named."""
    m = manuscript(texts)
    hit = re.search(r"corrupts the input of each of its \*\*(\d+)\s*\n?named cases\*\*", m)
    if not hit:
        return False, "the liveness sentence's bound is not in the manuscript parts"
    want = _liveness_cases(texts)
    if want == 0:
        return False, "the runner's case list could not be read: nothing to compare against"
    if int(hit.group(1)) != want:
        return False, "manuscript says %s named cases; the runner's list holds %d" % (hit.group(1), want)
    body = m[hit.start():hit.start() + 900]
    missing = [w for w in ("primitive", "recorded field", "cross-check") if w not in body]
    if missing:
        return False, "the bound's mechanisms are unstated: %s" % missing
    return True, "%d named case(s), both mechanisms named (the runner's own case list)" % want


def ck_freeze(texts, c):
    m = re.search(r"artefacts, `(\d+)`\s*\n?checks including the digest table", manuscript(texts))
    want = json.loads(texts["freeze_check_v1_results.json"])["n_checks"]
    if not m:
        return False, "the freeze-count sentence is not in the manuscript parts"
    return m.group(1) == str(want), "manuscript %r | freeze_check_v1_results.json %d" % (m.group(1), want)


def ck_support(texts, c):
    m = re.search(r"of the cited keys `(\d+)` appear in more than one sentence", manuscript(texts))
    n_multi = sum(1 for v in _multi(texts["support_verdicts_v1.json"]).values() if v > 1)
    if not m:
        return False, "the multi-sentence-key sentence is not in the manuscript parts"
    return m.group(1) == str(n_multi), "manuscript %r | verdict rows hold %d key(s) in >1 sentence" % (
        m.group(1), n_multi)


def ck_mutations(texts, c):
    m = re.search(r"check-liveness, `(\d+)` mutations", manuscript(texts))
    want = json.loads(texts["external_cell_mutation_v1_results.json"])["n_mutations"]
    if not m:
        return False, "the mutation-count sentence is not in the manuscript parts"
    return m.group(1) == str(want), "manuscript %r | the mutation artefact ran %d" % (m.group(1), want)


def ck_detectors(texts, c):
    m = re.search(r"with (\d+) of (\d+) detectors", manuscript(texts))
    want = _detectors(texts["run.log"])
    if not m:
        return False, "the detector sentence is not in the manuscript parts"
    if want is None:
        return False, "run.log does not carry a 'detectors firing on a planted instance: N of N' line"
    return m.group(1) == want, "manuscript %r of %r | run.log printed %s of %s" % (
        m.group(1), m.group(2), want, want)


def ck_inflation(texts, c):
    """EVERY occurrence, not the first: the phrase appears in more than one carrier, and a rule that
    checked only the first would pass while a later copy drifted."""
    want = _inflation(texts["sufficiency_v1_results.json"])
    got = [("%s\u2013%s\u00d7" % (m.group(1), m.group(2)))
           for m in re.finditer(r"optimistic by ([\d.]+)\u2013([\d.]+)\u00d7", manuscript(texts))]
    if not got:
        return False, "the inflation-range claim is not in the manuscript parts"
    if want is None:
        return False, "the sufficiency artefact carries no mde_inflation_factor to take a range of"
    wrong = [g for g in got if g != want]
    return (not wrong), "%d occurrence(s) %s | sufficiency_v1_results.json min-max %r%s" % (
        len(got), got, want, "" if not wrong else " -- DISAGREEING: %s" % wrong)


def ck_section_refs(texts, c):
    """Every Section N / SS N must name a heading that exists."""
    m = manuscript(texts)
    heads = {int(h.group(1)): h.group(2).strip() for h in re.finditer(r"^## (\d+)\. (.+)$", m, re.M)}
    if not heads:
        return False, "no numbered `## N.` heading found: nothing to resolve the references against"
    refs = set()
    for r in re.finditer(r"\bSections? (\d+)\b", m):
        refs.add(int(r.group(1)))
    for r in re.finditer(r"\u00a7(\d+)(?:\.\d+)?", m):
        refs.add(int(r.group(1)))
    missing = sorted(r for r in refs if r not in heads)
    return (not missing), "%d section number(s) referenced, headings 1..%d%s" % (
        len(refs), max(heads), "" if not missing else " -- NO SUCH SECTION: %s" % missing)


def ck_roadmap(texts, c):
    """Each roadmap entry must name a section whose heading carries the object the sentence names."""
    m = manuscript(texts)
    if "### 1.5 Roadmap" not in m:
        return False, "the roadmap section is not in the manuscript parts"
    start = m.index("### 1.5 Roadmap")
    block = m[start:m.index("\n## ", start)]
    heads = {int(h.group(1)): h.group(2) for h in re.finditer(r"^## (\d+)\. (.+)$", m, re.M)}
    bad = []
    for label, keyword in ROADMAP:
        n = int(re.search(r"\d+", label).group(0))
        if n not in heads:
            bad.append("%s does not exist" % label)
            continue
        if keyword.lower() not in heads[n].lower():
            bad.append("%s is headed %r, which the roadmap's sentence does not describe"
                       % (label, heads[n]))
    if "Section 6.4" not in block:
        bad.append("the roadmap does not name Section 6.4 for the threats")
    return (not bad), ("; ".join(bad) if bad else
                       "%d roadmap entr(ies) name the section they describe" % len(ROADMAP))


def ck_witness_magnitudes(texts, c):
    """The specificity-control sentence must state every magnitude it carries as a resolved placeholder.

    The rule is a UNIVERSAL -- "every magnitude this sentence states is one the assembler resolves" -- and
    it was first implemented as a search for the decimals the artefact holds, in the two spellings the
    author computed (2dp and 1dp).  A universal implemented as a search for the expected forms cannot see
    the form that was not expected.  Measured, at an export of the round-3 head, in this very sentence: the
    aggregate `13` -- typed in prose beside the three placeholders -- became `99` and left this file at
    `11 check(s), 0 failed` with `assemble.py` at exit 0; the spelling set held {12.95, 13.12, 1.53, 13.0,
    13.1, 1.5} and `13` was not in it.  The typed form was also FALSE: it read "up to 13" while the largest
    of the three magnitudes it summarises is 13.12.

    Both are repaired: the sentence carries one carriage per magnitude, and this check reads the rule as
    written -- with the placeholder spans taken out, NO digit may remain.  The artefact is still read, so
    the sentence cannot be bound to nothing: the owner must carry all three keys.
    """
    m = manuscript(texts)
    marker = "The instrument calls this test the **specificity control**"
    if marker not in m:
        return False, "the specificity-control sentence is not in the manuscript parts"
    start = m.index(marker)
    stop = m.find("\n\n", start)
    sent = m[start:stop if stop != -1 else len(m)]
    facts = json.loads(texts["canonical_results.json"])["facts"]
    keys = ["limit.L2_null_shift.%s" % prob for prob in ("ski", "sched", "paging")]
    missing = [k for k in keys if k not in facts]
    if missing:
        return False, "the artefact does not carry %s -- nothing to bind against" % missing
    held = ", ".join("%s %.2f" % (k.split(".")[-1], facts[k]["value"]) for k in keys)
    outside = re.sub(r"\{\{[^{}]*\}\}", "", sent)
    typed = re.findall(r"\d[\d.,]*", outside)
    if typed:
        return False, ("%d magnitude(s) typed in the sentence, resolved from nothing: %s -- the artefact "
                       "holds %s; a typed copy beside a placeholder can disagree with it silently"
                       % (len(typed), typed, held))
    spans = re.findall(r"\{\{[^{}]*\}\}", sent)
    named = re.findall(r"\{\{X:facts\.limit\.L2_null_shift\.([a-z]+)\.value", sent)
    if len(spans) != 3 or sorted(named) != ["paging", "sched", "ski"]:
        return False, ("the sentence carries %d placeholder(s) (%s), expected exactly the three "
                       "specificity-control magnitudes" % (len(spans), named or "none"))
    return True, ("3 magnitudes, each only a placeholder resolved from the artefact (%s); "
                  "0 digit outside a placeholder" % held)


def ck_figure(texts, c):
    """The figure must be shown in the manuscript AND the file it names must be committed.

    Both halves, because the bar asks for both and each can fail alone: an embed naming a file that is not
    in the tree is a broken image, and a committed figure no sentence shows is a package the reader never
    sees.  The byte-level read -- that the file is what the generator produces -- lives in
    `figures/make_figures_v1.py --check`, which `reproduce.sh` runs; this is the manuscript's half.
    """
    m = manuscript(texts)
    embeds = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", m, re.S)
    if not embeds:
        return False, ("the manuscript shows no figure at all (`![...](...)` occurs 0 times) -- "
                       "Presentation requirements item 1: text-only manuscripts are incomplete")
    missing = [e for e in embeds if not os.path.exists(os.path.join(HERE, e))]
    if missing:
        return False, "the manuscript embeds %s, which is not in the package" % missing
    for e in embeds:
        if not e.startswith("figures/"):
            return False, "the embedded figure %r does not live under figures/" % e
    return True, "%d figure(s) shown, each naming a committed file (%s)" % (len(embeds), ", ".join(embeds))



CHECKS = [
    ("manuscript/step_count_is_the_one_reproduce_sh_prints", ck_steps),
    ("manuscript/liveness_bound_is_the_runner's_case_list", ck_liveness),
    ("manuscript/freeze_check_count_is_the_freeze_result's", ck_freeze),
    ("manuscript/support_multi_sentence_count_is_the_verdict_rows", ck_support),
    ("manuscript/mutation_count_is_the_mutation_result's", ck_mutations),
    ("manuscript/detector_count_is_the_census's_own_line", ck_detectors),
    ("manuscript/inflation_range_is_the_sufficiency_artifact's", ck_inflation),
    ("manuscript/every_section_reference_resolves", ck_section_refs),
    ("manuscript/the_roadmap_names_the_section_it_describes", ck_roadmap),
    ("manuscript/the_witness_magnitudes_are_resolved_not_typed", ck_witness_magnitudes),
    ("manuscript/the_figure_is_shown_and_its_file_is_committed", ck_figure),
]

# (check, file, the claim to break, what to replace it with).  Breaking one claim must fail its own
# check and no other -- an exact list, not "something went red" (the confounded battery of R343).
def _mut_steps(texts):
    """Break the manuscript's step-count word wherever it stands, read from the text, never typed."""
    m = re.search(r"It has \*\*([a-z]+)\*\* steps", texts["manuscript_part3.md"])
    if not m:
        return ("manuscript_part3.md", None, None)
    wrong = "seven" if m.group(1) != "seven" else "eight"
    return ("manuscript_part3.md", m.group(0), "It has **%s** steps" % wrong)


MUTATIONS = [
    # DERIVED, NOT PINNED.  This anchor first read `**eleven**`, and the step count legitimately became
    # `twelve` in the same round that added a step -- so the case reported "the anchor occurs 0 time(s)"
    # about a correction that had just made the package right.  A mutation anchor is itself a claim about
    # an artefact; read the word out of the manuscript and break that.
    ("manuscript/step_count_is_the_one_reproduce_sh_prints", _mut_steps),
    ("manuscript/liveness_bound_is_the_runner's_case_list",
     "manuscript_part3.md", "each of its **12\nnamed cases**", "each of its **113\nnamed cases**"),
    ("manuscript/freeze_check_count_is_the_freeze_result's",
     "manuscript_part3.md", "artefacts, `57`\nchecks including", "artefacts, `46`\nchecks including"),
    ("manuscript/support_multi_sentence_count_is_the_verdict_rows",
     "manuscript_part3.md", "of the cited keys `58` appear", "of the cited keys `51` appear"),
    ("manuscript/mutation_count_is_the_mutation_result's",
     "manuscript_part3.md", "check-liveness, `13` mutations", "check-liveness, `12` mutations"),
    ("manuscript/detector_count_is_the_census's_own_line",
     "manuscript_part3.md", "with 8 of 8 detectors", "with 7 of 8 detectors"),
    ("manuscript/inflation_range_is_the_sufficiency_artifact's",
     "manuscript_part2.md", "optimistic by 3.7\u20136.3\u00d7", "optimistic by 3.2\u20136.3\u00d7"),
    ("manuscript/every_section_reference_resolves",
     "manuscript_part1.md", "### 1.5 Roadmap", "### 1.5 Roadmap\n\nSection 9 is a phantom."),
    ("manuscript/the_roadmap_names_the_section_it_describes",
     "manuscript_part1.md", "and its Section 6.4 states", "and its Section 8 states"),
    ("manuscript/the_witness_magnitudes_are_resolved_not_typed",
     "manuscript_part2.md",
     "one per problem, by ski rental\n`{{X:facts.limit.L2_null_shift.ski.value|2f}}`",
     "one per problem, by ski rental\n`12.95`"),
    # The same check at the member the first implementation could NOT see: a ROUNDED aggregate typed in
    # the prose beside the three placeholders.  The text is the one the round-3 delivery actually carried
    # (measured then: `13` -> `99` left 11 checks at 0 failed, `assemble.py` at exit 0), restored verbatim
    # -- so the case fails on the rule as written and would have passed the rule as first implemented.
    ("manuscript/the_witness_magnitudes_are_resolved_not_typed",
     "manuscript_part2.md",
     "is penalised, one per problem, by ski rental",
     "is penalised by up to `13` cluster MDEs, one per problem: ski rental"),
    ("manuscript/the_figure_is_shown_and_its_file_is_committed",
     "manuscript_part2.md", "](figures/fig1_witness.svg)", "](figures/fig_absent.svg)"),
]


def run_all(texts):
    rows = []
    for name, fn in CHECKS:
        try:
            ok, detail = fn(texts, None)
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
    base = [n for n, ok, _ in run_all(texts) if not ok]
    if base:
        print("FAIL   the battery needs a clean base; already failing: %s" % base)
        return 1
    # Coverage is itself a claim about the battery and needs its own read: a check with NO planted claim
    # is decoration -- nothing shows it can fail -- and the case list is what claims it can.  A check may
    # carry more than one case (a class repaired at one spelling needs the case for the other).
    uncovered = [n for n, _ in CHECKS if n not in set(case[0] for case in MUTATIONS)]
    if uncovered:
        print("FAIL   %d check(s) carry no planted claim: %s" % (len(uncovered), uncovered))
        return 1
    bad = 0
    for name, spec, *rest in MUTATIONS:
        # A case is either a literal (file, old, new) or a callable that derives its own anchor from the
        # text -- the derived form is preferred wherever the value can legitimately move (see _mut_steps),
        # because a typed anchor turns a correct change into a red battery.
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
    # The bound is read from the runner's own case list on both sides, so a case added there moves the
    # manuscript's claim.  Stated here rather than asserted as a mutation: the list is the runner's,
    # and a planted case would have to be planted in the runner to be honest.
    print("NOTE   the runner's case list holds %d case(s), read from canonical_runner.py; the liveness\n"
          "       check compares the manuscript's bound against this list, not against a typed 12"
          % _liveness_cases(texts))
    print("selftest: %d case(s), %d failure(s) over %d check(s)" % (len(MUTATIONS), bad, len(CHECKS)))
    return 1 if bad else 0


def main():
    rows = run_all(load())
    bad = report(rows)
    print("manuscript check: %d check(s), %d failed" % (len(rows), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
