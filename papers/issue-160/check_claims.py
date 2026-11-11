# -*- coding: utf-8 -*-
"""check_claims.py -- does the artefact still say what the paper says it says?

Every quantitative statement in the manuscript is a sentence about `results/crossover.json`. This
program is what keeps those sentences honest: it reads the artefact and re-derives

  (1) each registered prior's verdict (MET / UNMET / NOT RUN) from the numbers, and
  (2) the internal identities the artefact must satisfy whatever the data says.

and then asserts the registered verdicts are still the ones the paper reports. If a number moves
far enough to flip a prior, this fails -- which is the point: a refuted prior that quietly becomes
agreement is the failure mode a measurement paper cannot afford.

Exit: 0 every claim holds · 1 a claim moved or an identity broke · 3 NOT RUN (no artefact).

`--selftest` runs the identical predicate on two mutated copies of the artefact and requires both to
be refused, so the gate is demonstrated to bite rather than asserted to.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "results", "crossover.json")
PROVENANCE = os.path.join(HERE, "fixture", "MEMBER_SHA256")

# The priors as registered on issue #160, with the threshold each one names. `test` is applied to a
# value read out of the artefact -- a prior is never compared against a number typed here.
CLAIMS = [
    dict(id="P2' limb 1", path="cells.0.binds_frac", op=">=", threshold=0.50,
         registered="MET",
         text="censoring binds on at least half the rows at a 2x-median timeout"),
    dict(id="P2' limb 2", path="cells.4.binds_frac", op="<", threshold=0.10,
         registered="UNMET",
         text="censoring binds on under a tenth of the rows at a 32x-median timeout"),
    dict(id="P3", path="cost.K_at_5.median", op=">=", threshold=20,
         registered="MET",
         text="the median workload needs at least 20 timeout levels to certify within 5%"),
]

CONTROL = dict(id="no-censoring control", path="controls.no_censoring_identified_and_exact_frac",
               op="==", threshold=1.0, registered="MET",
               text="a timeout above the row maximum identifies the quantile exactly, every time")


def verdict_line_states_the_pair(text, law_gaps, checked_levels):
    """Does the P3 verdict line print BOTH counts, and say which one is the law's?

    Review round 2, minor 1. The line printed the law's `K` (25) as the answer to "how many timeout
    levels", while the abstract printed the checked price (26) three paragraphs above: the marker was
    bound correctly and to the wrong quantity, so no gate could see it -- the binding was never the
    defect. This predicate is what makes the pair printable-but-not-substitutable: the line must carry
    both numbers, and the law's number must be attached to the word *gap*, because that is the only
    thing that distinguishes the two counts in the reader's hands.

    It is a text predicate on purpose. A sentence is the object under test here, and the failure it
    guards is a sentence quoting one quantity under another's name.
    """
    for line in text.splitlines():
        if not line.startswith("**P3"):
            continue
        has_both = (str(law_gaps) in line) and (str(checked_levels) in line)
        names_the_law = _GAP_WORD.search(line) is not None
        law_before_checked = (line.find(str(law_gaps)) < line.find(str(checked_levels))
                              if has_both else False)
        return has_both, names_the_law, law_before_checked, line
    return False, False, False, ""


_GAP_WORD = re.compile(r"\bgaps?\b", re.I)
# One author in the form this bibliography prints: `Family, I.` or `Family, I. J.`
_AUTHOR_TOKEN = re.compile(r"^[^;,]+,\s*(?:[A-Z\u00c0-\u00de]\.(?:\s*[A-Z\u00c0-\u00de]\.)*)$")


def reproduction_steps():
    """How many steps `reproduce.sh` actually runs, counted off the script itself.

    Review minor 2: the manuscript said "six steps" while the script ran eight, and no gate owned the
    number. One function, used by the renderer that prints the sentence and by the identity that
    checks it, so the two cannot disagree -- a second parser would be a copy free to drift.
    """
    path = os.path.join(HERE, "reproduce.sh")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return len([ln for ln in text.splitlines() if ln.startswith('step "')])


def get(art, dotted):
    """Read a dotted path out of the artefact; a missing path is a failure, never a default."""
    cur = art
    for part in dotted.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError("artefact has no %s" % dotted)
    return cur


def holds(value, op, threshold):
    if op == ">=":
        return value >= threshold
    if op == "<":
        return value < threshold
    if op == "==":
        return abs(value - threshold) <= 1e-12
    if op == ">":
        return value > threshold
    raise ValueError("unknown operator %r" % op)


def verdict(claim, art):
    v = get(art, claim["path"])
    return v, ("MET" if holds(v, claim["op"], claim["threshold"]) else "UNMET")


def identities(art):
    """The statements that must hold whatever the data turns out to be. Returns [(name, ok, detail)]."""
    out = []
    cl = art["count_limit"]
    refused = sum(cl["refused"].values())
    out.append(("rows read = usable + refused",
                cl["rows"] == cl["usable"] + refused,
                "%d vs %d + %d" % (cl["rows"], cl["usable"], refused)))
    # Exact, not re-multiplied: asserting `resolvable + round(frac * usable) == usable` passes on a
    # rounding coincidence, so it would stay green while the fractions drifted from their counts.
    out.append(("resolvable_frac is resolvable/usable to 4 dp",
                cl["resolvable_frac"] == round(cl["resolvable"] / float(cl["usable"]), 4),
                "%d/%d = %.4f vs %.4f" % (cl["resolvable"], cl["usable"],
                                          cl["resolvable"] / float(cl["usable"]), cl["resolvable_frac"])))
    out.append(("unresolvable_frac is the complement of resolvable_frac",
                cl["unresolvable_frac"] == round(1.0 - cl["resolvable_frac"], 4),
                "%.4f vs 1 - %.4f" % (cl["unresolvable_frac"], cl["resolvable_frac"])))
    # EQUALITY, not the weaker `<=` it carried until the revision round: `resolvable(count, q)` is
    # `count * (1-q) >= 1`, so at q = 0.99 it flips at exactly count = 100 and "fewer than 100
    # invocations" IS "unresolvable" -- the same rows by construction, not two findings that happen
    # to agree. Written as `<=`, the gate would have stayed green if the two ever began to differ,
    # which is the one thing it should catch: the paper prints both as separate rows.
    out.append(("every row with Count < 100 is unresolvable, and the two sets are equal",
                cl["below_100"] == cl["usable"] - cl["resolvable"],
                "%d below 100 vs %d unresolvable (%d - %d)"
                % (cl["below_100"], cl["usable"] - cl["resolvable"], cl["usable"], cl["resolvable"])))
    out.append(("below_100 <= below_1000", cl["below_100"] <= cl["below_1000"],
                "%d <= %d" % (cl["below_100"], cl["below_1000"])))
    out.append(("below_100_frac is below_100/usable to 4 dp",
                cl["below_100_frac"] == round(cl["below_100"] / float(cl["usable"]), 4),
                "%d/%d = %.4f vs %.4f" % (cl["below_100"], cl["usable"],
                                          cl["below_100"] / float(cl["usable"]), cl["below_100_frac"])))
    for cell in art["cells"]:
        out.append(("k=%d: binds + identified = 1" % cell["k"],
                    abs(cell["binds_frac"] + cell["identified_frac"] - 1.0) < 5e-5,
                    "%.4f + %.4f" % (cell["binds_frac"], cell["identified_frac"])))
        out.append(("k=%d: rows == usable" % cell["k"], cell["rows"] == cl["usable"],
                    "%d vs %d" % (cell["rows"], cl["usable"])))
    fracs = [c["binds_frac"] for c in art["cells"]]
    out.append(("binds is non-increasing in the timeout multiplier",
                all(a >= b for a, b in zip(fracs, fracs[1:])),
                " -> ".join("%.4f" % f for f in fracs)))
    # The registration is the authority, not the artefact. Without these two lines the artefact
    # certifies its own configuration: change Q or the timeout grid inside the program and the
    # artefact regenerates consistently, step 3 stays byte-identical, and every claim below is
    # evaluated against numbers that answer a different question. Found by planting exactly that.
    out.append(("q is the registered 0.99", art["q"] == 0.99, "q = %r" % (art["q"],)))
    out.append(("the timeout grid is the registered {2,4,8,16,32}",
                list(art["kgrid"]) == [2, 4, 8, 16, 32]
                and [c["k"] for c in art["cells"]] == [2, 4, 8, 16, 32],
                str(art["kgrid"])))
    out.append(("the precision ladder is the registered {5%,10%,20%}",
                sorted(art["eps"]) == [0.05, 0.1, 0.2], str(art["eps"])))
    out.append(("every k in the pre-declared grid is present",
                [c["k"] for c in art["cells"]] == list(art["kgrid"]),
                str([c["k"] for c in art["cells"]])))
    out.append(("the artefact records the digest of the bytes it read",
                len(get(art, "input.sha256_of_decompressed_bytes")) == 64,
                get(art, "input.sha256_of_decompressed_bytes")[:16] + "..."))
    # ---- the cost law travels with its check (registered criterion (ii), review M1) ----------
    # §6 prices a certification. Until this revision round nothing ran the procedure whose cost it
    # prices, and the registration's criterion (ii) asked for exactly that. The residual lives in the
    # artefact beside the law, and these lines are what make the two inseparable: the check cannot be
    # dropped, and the finding it produced cannot quietly evaporate.
    cc = art.get("cost_check")
    if cc is None:
        out.append(("the cost law's check is present and states its residual", False,
                    "no cost_check block: criterion (ii) would again be unverified"))
    else:
        eps_tags = sorted(cc["by_eps"])
        out.append(("every precision in the registered ladder has a residual, at K-1, K and K+1",
                    eps_tags == ["eps_10", "eps_20", "eps_5"]
                    and all(all(k in cc["by_eps"][e] for k in
                                ("at_K_minus_1", "at_K", "at_K_plus_1")) for e in eps_tags)
                    and all("residual_max" in cc["by_eps"][e]["at_K"] for e in eps_tags),
                    ",".join(eps_tags)))
        for tag in eps_tags:
            blk = cc["by_eps"][tag]
            held = cc["holds_at"][tag]
            # What the paper sells must attain eps on EVERY row, not typically: a price that buys
            # the precision usually is not a certification, and the worst row is the one that
            # decides whether a reader can rely on the number.
            out.append(("%s: the level count the paper states attains eps on every row" % tag,
                        blk[held]["rows_over_eps"] == 0,
                        "%s: %d of %d rows over eps (residual max %.4f)"
                        % (held, blk[held]["rows_over_eps"], blk[held]["rows"],
                           blk[held]["residual_max"])))
            # And the finding, asserted rather than narrated: the law's own K is NOT enough. If a
            # later change made K sufficient, §6's sentence about the off-by-one would be false and
            # this line is what would say so.
            out.append(("%s: the law's own K does not attain eps (K counts gaps, not levels)" % tag,
                        blk["at_K"]["rows_over_eps"] > 0,
                        "at_K: %d of %d rows over eps (residual max %.4f)"
                        % (blk["at_K"]["rows_over_eps"], blk["at_K"]["rows"],
                           blk["at_K"]["residual_max"])))
            # Review round 2, minor 1: the two counts are one level apart under ANY parameters --
            # `K` counts the gaps between timed levels and a certification needs the levels, so the
            # difference is structural rather than a property of this workload. Asserting it here is
            # what lets the next check hold the sentence to the pair: if the delta were ever not 1,
            # the sentence's own arithmetic would be wrong and this line would say so first.
            out.append(("%s: the checked price is exactly one level above the law's gap count" % tag,
                        blk["at_K_plus_1"]["levels_median"] == blk["at_K"]["levels_median"] + 1,
                        "law K=%d checked=%d (delta %d)"
                        % (blk["at_K"]["levels_median"], blk["at_K_plus_1"]["levels_median"],
                           blk["at_K_plus_1"]["levels_median"] - blk["at_K"]["levels_median"])))

        rec = cc["reconstruction"]
        out.append(("the reconstruction limb actually drew from the rows it reports",
                    rec["rows"] > 0 and rec["draws_per_row"] > 0 and rec["seed"] == 20261110,
                    "%d rows x %d draws, seed %d"
                    % (rec["rows"], rec["draws_per_row"], rec["seed"])))

    # ---- the reproduction's step count is read from the script, not remembered ---------------
    # Review minor 2: the manuscript said "six steps" while the script ran eight, and no gate owned
    # the number. The renderer now derives it from `reproduce.sh` itself, so the sentence cannot go
    # stale; this line re-derives the same number a second way and refuses a script whose declared
    # constant disagrees with its own call sites -- the script's own guard, read by the gate too.
    script = os.path.join(HERE, "reproduce.sh")
    if os.path.exists(script):
        text = open(script, encoding="utf-8").read()
        declared = [ln for ln in text.splitlines() if ln.startswith("TOTAL_STEPS=")]
        sites = reproduction_steps()
        out.append(("reproduce.sh: the declared step count equals its own call sites",
                    len(declared) == 1 and int(declared[0].split("=")[1]) == sites,
                    "declared %s, call sites %d"
                    % (declared[0].split("=")[1] if declared else "?", sites)))
    else:
        out.append(("reproduce.sh is present so its step count can be read", False, "missing"))

    # ---- bibliography entries print names, not the registry's stored fields ------------------
    # Review minor 4: `[74]` printed `III, J. P.` because the DOI's record stores the suffix in the
    # family field, and five more entries printed an ALL-CAPS family. The fix is applied at render;
    # this re-applies THE RENDERER'S OWN function to all 120 entries, so the check cannot be a copy
    # that drifts from the code that produces the paper.
    try:
        import make_manuscript as mm
    except Exception as e:                                   # pragma: no cover - reported, not hidden
        out.append(("the renderer is importable so author form can be re-checked", False, str(e)))
        make_manuscript_mod = None
    else:
        make_manuscript_mod = mm
    if make_manuscript_mod is not None:
        refs_path = os.path.join(HERE, "refs.json")
        if os.path.exists(refs_path):
            rj = json.load(open(refs_path, encoding="utf-8"))
            refs = rj.get("refs", rj)
            offenders = []
            for slug in sorted(refs):
                printed = make_manuscript_mod.rendered_entry(refs[slug], slug)
                if make_manuscript_mod.ALLCAPS_FAMILY.search(printed):
                    offenders.append(slug)
            out.append(("no entry prints an ALL-CAPS or suffix-shaped family name",
                        not offenders,
                        "%d of %d entries: %s"
                        % (len(offenders), len(refs), ", ".join(offenders[:4]) or "none")))

            nulls, noauth = [], 0
            for slug in sorted(refs):
                printed = make_manuscript_mod.rendered_entry(refs[slug], slug)
                if "None" in printed:
                    nulls.append(slug)
                title = (refs[slug].get("title") if isinstance(refs[slug], dict) else "") or ""
                head = printed.split(title, 1)[0] if (title and title in printed) else printed
                head, _year, _tail = make_manuscript_mod._split_at_year(head)
                if not head.strip().rstrip(",;").rstrip():
                    noauth += 1
            # Review round 2, minor 2: three of the 120 entries printed their author
            # given-name-first (`Mohammad Shahrad;`) where the other 117 print `Family, I.`. The
            # cause is a second assembly path: an arXiv record gives one `<name>` string per author
            # and no family/given split, so `entry_of_arxiv` joined those strings verbatim while
            # `entry_of` built the form from Crossref's fields. Found by reading the assembled text,
            # so the census is the whole list -- a form defect found by sampling is a form defect
            # with a denominator. Every count below is reported with it.
            with_auth, conform, outside = 0, 0, []
            for slug in sorted(refs):
                printed = make_manuscript_mod.rendered_entry(refs[slug], slug)
                title = (refs[slug].get("title") if isinstance(refs[slug], dict) else "") or ""
                head = printed.split(title, 1)[0] if (title and title in printed) else printed
                head, _year, _tail = make_manuscript_mod._split_at_year(head)
                head = head.strip()
                if head.endswith(".."):
                    head = head[:-1]
                # Separators only: the last initial ends in a period, and stripping it turns
                # `Whitt, W.` into `Whitt, W`, which fails the predicate it is read for.
                head = head.rstrip().rstrip(",;").rstrip()
                if not head:
                    continue
                with_auth += 1
                toks = [t.strip() for t in head.split(";") if t.strip()]
                if all(t.lower().startswith("et al") or _AUTHOR_TOKEN.match(t) for t in toks):
                    conform += 1
                else:
                    outside.append(slug)
            out.append(("every entry that prints an author prints it in one form",
                        not outside and conform == with_auth,
                        "%d of %d entries with an author are in house form: %s"
                        % (conform, with_auth, ", ".join(outside[:4]) or "none")))
            out.append(("no entry prints a null slot where a field belongs",
                        not nulls,
                        "%d of %d entries: %s"
                        % (len(nulls), len(refs), ", ".join(nulls[:4]) or "none")))
            out.append(("the entries that print no year are counted rather than rendered", True,
                        "%d of %d entries carry no author segment" % (noauth, len(refs))))
        else:
            out.append(("refs.json is present so author form can be checked", False, "missing"))

    # ---- is the refuted margin the reconstruction's, or the workload's? (review question 2) ---
    # §5 now says the refutation survives a sensitivity sweep over ladder shapes AND that the margin
    # it clears the threshold by is narrower than the spread those shapes produce. Both are asserted,
    # because a sentence comparing two numbers is exactly the kind that can stay green after one of
    # them moves. The threshold is read from CLAIMS -- the gate that decides the verdict -- never
    # retyped here.
    ks = art.get("knot_sweep")
    if ks is None:
        out.append(("the crossover is re-measured over coarser ladders", False,
                    "no knot_sweep block: question 2 would be answered in prose only"))
    else:
        thr = [c["threshold"] for c in CLAIMS if c["id"] == "P2' limb 2"][0]
        fr = [s_["binds_frac"] for s_ in ks["sets"]]
        full = [s_ for s_ in ks["sets"] if s_["knots"] == ks["full_knots"]]
        out.append(("every ladder shape tested still refutes the registered threshold",
                    len(full) == 1 and all(f > thr for f in fr),
                    "%d shapes, min %.4f, threshold %.4f" % (len(fr), min(fr), thr)))
        spread, margin = max(fr) - min(fr), full[0]["binds_frac"] - thr if full else None
        out.append(("the reconstruction's own spread is wider than the refutation's margin",
                    full and spread > margin,
                    "spread %.4f vs margin %s" % (spread, "%.4f" % margin if margin else "?")))
        out.append(("the sweep holds the interpolation family fixed and says so",
                    "family held fixed" in ks.get("family", ""), ks.get("family", "")[:48]))

    # ---- the level is stated where a reader enters (review question 6) -----------------------
    # ---- the verdict line states the pair, not one of the two (review round 2, minor 1) -------
    # The site a reader consults to learn whether the registration's belief survived. A line that
    # prints the law's gap count as the answer to "how many levels" under-claims by one, and the
    # previous head did exactly that while every gate stayed green -- because the marker behind it
    # was bound correctly, to the wrong quantity. This reads the rendered paper.
    ms_path = os.path.join(HERE, "manuscript.md")
    if cc is None or not os.path.exists(ms_path):
        out.append(("the P3 verdict line states both counts", False,
                    "no artefact or no rendered manuscript -- this check has NOT RUN"))
    else:
        law_gaps = cc["by_eps"]["eps_5"]["at_K"]["levels_median"]
        checked = cc["by_eps"]["eps_5"]["at_K_plus_1"]["levels_median"]
        text = open(ms_path, encoding="utf-8").read()
        both, names_law, law_first, line = verdict_line_states_the_pair(text, law_gaps, checked)
        out.append(("the P3 verdict line prints both the law's gap count and the checked price",
                    both, "law=%d checked=%d | line: %s" % (law_gaps, checked, line[:100])))
        out.append(("the P3 verdict line says which of the two is the law's gap count",
                    names_law, line[:100]))

    # Four carriers have to agree: the registration, the manuscript, the README, and the review's
    # own reading. Two of them are authored text in this package and both are asserted; the
    # registration is not in the package and is named here rather than read.
    rd = os.path.join(HERE, "README.md")
    pr = os.path.join(HERE, "manuscript_prose.md")
    if os.path.exists(rd) and os.path.exists(pr):
        readme, prose = open(rd, encoding="utf-8").read(), open(pr, encoding="utf-8").read()
        out.append(("README and manuscript declare the same contribution level",
                    "case study" in readme and "case study" in prose,
                    "README %s / manuscript %s"
                    % ("case study" in readme, "case study" in prose)))
        out.append(("README states a reproducibility level, not only a command",
                    "Reproducibility level" in readme,
                    "found" if "Reproducibility level" in readme else "absent"))
    else:
        out.append(("README and manuscript are present so the level can be checked", False, "missing"))

    return out


def evaluate(art, provenance=PROVENANCE):
    """(claims, identities, failures). Pure: same artefact in, same verdicts out."""
    claims = []
    fails = []
    for c in CLAIMS + [CONTROL]:
        try:
            v, got = verdict(c, art)
        except (KeyError, IndexError, TypeError) as e:
            claims.append((c["id"], None, "MISSING", c["registered"], str(e)))
            fails.append("%s: %s" % (c["id"], e))
            continue
        claims.append((c["id"], v, got, c["registered"], c["text"]))
        if got != c["registered"]:
            fails.append("%s moved: registered %s, artefact now says %s (value %s)"
                         % (c["id"], c["registered"], got, v))
    ids = identities(art)
    for name, ok, detail in ids:
        if not ok:
            fails.append("identity broken: %s (%s)" % (name, detail))
    # the numbers must belong to the committed bytes, not merely to some run
    if os.path.exists(provenance):
        for line in open(provenance, encoding="utf-8"):
            tok = line.split()
            if tok and not tok[0].startswith("#") and len(tok[0]) == 64:
                rec = tok[0].lower()
                if get(art, "input.sha256_of_decompressed_bytes") != rec:
                    fails.append("the artefact was produced from other bytes than the fixture records")
                break
    return claims, ids, fails


def report(art):
    claims, ids, fails = evaluate(art)
    print("claim                                        value      now      registered")
    for cid, v, got, reg, text in claims:
        shown = "-" if v is None else ("%.4f" % v if isinstance(v, float) else str(v))
        flag = "" if got == reg else "   <-- MOVED"
        print("  %-42s %9s  %-8s %-8s%s" % (cid, shown, got, reg, flag))
    print("\nidentities (%d):" % len(ids))
    for name, ok, detail in ids:
        print("  [%s] %s -- %s" % ("ok" if ok else "FAIL", name, detail))
    return fails


def selftest():
    """The gate must refuse two mutations, using the same `evaluate` the real run uses."""
    fails = 0

    def expect(name, ok, detail=""):
        nonlocal fails
        print("  [%s] %s%s" % ("ok" if ok else "FAIL", name, (" -- " + detail) if detail else ""))
        if not ok:
            fails += 1

    if not os.path.exists(ART):
        print("  [SKIP] no artefact to mutate")
        return 1
    base = json.load(open(ART, encoding="utf-8"))

    print("selftest: the artefact as committed")
    f0 = report(base)
    expect("the committed artefact satisfies every claim", not f0, "; ".join(f0[:2]))

    # 1. the refuted limb quietly becomes agreement -- the exact drift this gate exists to catch.
    m1 = json.loads(json.dumps(base))
    m1["cells"][4]["binds_frac"] = 0.05
    m1["cells"][4]["identified_frac"] = 0.95
    f1 = evaluate(m1)[2]
    expect("a refuted limb flipped into agreement is refused",
           any("limb 2" in x for x in f1), (f1 or ["(not refused)"])[0])

    # 2. an identity broken by a plausible-looking single edit: the split fractions no longer sum.
    m2 = json.loads(json.dumps(base))
    m2["cells"][0]["identified_frac"] = 0.50
    f2 = evaluate(m2)[2]
    expect("binds + identified != 1 is refused", any("binds + identified" in x for x in f2),
           (f2 or ["(not refused)"])[0])

    # 3. numbers that belong to a different input than the fixture records.
    m3 = json.loads(json.dumps(base))
    m3["input"]["sha256_of_decompressed_bytes"] = "0" * 64
    f3 = evaluate(m3)[2]
    expect("an artefact from other bytes than the fixture is refused",
           any("other bytes" in x for x in f3), (f3 or ["(not refused)"])[0])

    # 4. the verdict line quotes one of the two counts as the other (review round 2, minor 1).
    #    The predicate is the one the gate runs, not a copy: a refusal demonstrated on a second
    #    implementation of the rule is not a refusal of the rule.
    cc = base.get("cost_check") or {}
    if cc:
        law = cc["by_eps"]["eps_5"]["at_K"]["levels_median"]
        chk = cc["by_eps"]["eps_5"]["at_K_plus_1"]["levels_median"]
        old_line = ("**P3 — certifying the median workload to 5%% needs at least 20 timeout levels.** "
                    "**MET**: the median is %d, with a 90th percentile of %d across rows."
                    % (law, law + 73))
        both, names, _, _ = verdict_line_states_the_pair(old_line, law, chk)
        expect("a verdict line that quotes only the law's gap count is refused", not both,
               "law=%d checked=%d, line prints both=%s" % (law, chk, both))
        pair_line = ("**P3 — MET.** The law's number is %d, the count of **gaps**; certification "
                     "needs the levels, one more: %d." % (law, chk))
        both2, names2, first2, _ = verdict_line_states_the_pair(pair_line, law, chk)
        expect("a verdict line that states the pair and names the law's count is accepted",
               both2 and names2 and first2, "both=%s names=%s law_first=%s" % (both2, names2, first2))
        unnamed = ("**P3 — MET.** The law's number is %d and the checked one is %d." % (law, chk))
        _, names3, _, _ = verdict_line_states_the_pair(unnamed, law, chk)
        expect("a verdict line that prints both without saying which is the law's is refused",
               not names3, "names_the_law=%s" % names3)
        swapped = ("**P3 — MET.** The levels are %d; the gaps number %d." % (chk, law))
        both4, names4, first4, _ = verdict_line_states_the_pair(swapped, law, chk)
        expect("a verdict line that prints the two counts in the wrong order is refused",
               both4 and names4 and not first4, "law_first=%s" % first4)

    print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if not os.path.exists(ART):
        print("NOT RUN: %s is absent, so no claim was checked" % os.path.relpath(ART, HERE))
        return 3
    art = json.load(open(ART, encoding="utf-8"))
    fails = report(art)
    if fails:
        print("\nCLAIMS: %d PROBLEM(S)" % len(fails))
        for f in fails:
            print("   - %s" % f)
        return 1
    print("\nCLAIMS: OK -- every registered prior's verdict follows from the artefact")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
