"""Issue #153: generate manuscript.md from manuscript_prose.md + results.json + placement.json.

No figure in the manuscript is typed.  Every number is a `{{n:key}}` marker resolved from
results.json; every table is generated; every citation group is expanded from the stored
verification state.  The generator then runs a stray-number scan over the body it produced and
FAILS if a multi-digit number or decimal appears that it cannot bind to an artifact.  That is
the same discipline as the stray scan recorded for #128: "does the number appear" is not a
binding, "was this token produced by an artifact" is.

Markers
  {{n:path}}          a number from results.json; `cells[R,K,T].field` indexes the cell list
  {{table:cells}}     the per-cell table
  {{table:controls}}  the positive-control table
  {{cites:SECTION:THEME}}  every placed reference of that theme, as [r12,r13,...]
  {{cite:name}}       a named work read in full (see NAMED)
  {{refs}}            the reference list, generated from placement.json
"""
import html
import json
import re
import sys

# Works the paper leans on directly.  Six of the eight this list used to carry were the
# SIX of these used to be the SAME WORKS as corpus entries, matched by DOI -- printed twice, once
# in the corpus section and once under "read in full", so 247 entry lines described 241 distinct
# works.  One work is one entry: the six now resolve to their corpus entry through NAMED_ALIAS, and
# only the two documents Crossref does not index stay here, each with the body responsible and the
# date it was read.
NAMED = {
    "rocksdb_compaction": dict(
        authors="RocksDB", year="2026",
        title="Compaction",
        venue="RocksDB wiki, revision read 2026-10-27",
        url="https://github.com/facebook/rocksdb/wiki/Compaction",
        difference="the taxonomy and the some-to-some overlap rule are read as the deployed "
                   "family this paper models; no policy of theirs is evaluated"),
    "rocksdb_overview": dict(
        authors="RocksDB", year="2026",
        title="RocksDB Overview",
        venue="RocksDB wiki, revision read 2026-10-27",
        url="https://github.com/facebook/rocksdb/wiki/RocksDB-Overview",
        difference="level style versus universal style is read as background; the merge "
                   "decision itself is not specified there"),
}

# corpus DOIs that a NAMED key used to duplicate: the key resolves to the corpus entry
NAMED_ALIAS = {
    "oneil1996": "10.1007/s002360050048",
    "paging_lookahead": "10.7146/brics.v2i50.19951",
    "semi_online_two": "10.1142/s0217595923500033",
    "semi_online_uniform": "10.1051/ro/2024042",
    "disk_sched": "10.1145/588160.588165",
    "mts_optimal": "10.1145/146585.146588",
}

# What this paper does that each harvested theme does not.  One line per theme, hand-written
# and true, emitted per entry by the theme the corpus recorded -- which is why the lines differ
# across the list instead of repeating one formula 239 times.
THEME_DIFFERENCE = {
    "flash-write-amp": "write amplification is counted as forced relocations in a merge model, "
                       "not measured against a device",
    "lsm-compaction": "no engine is instrumented; one policy's merge decision is scored against "
                      "an exact optimum at a fixed horizon",
    "kv-engine": "the store is the setting the policy lives in, not the object measured here",
    "logstructured-fs": "cleaning is the historical ancestor of the cost, not a competing model "
                        "scored on the same instances",
    "levels-tiering": "the two deployed families are not compared with each other; one family's "
                      "decision is compared with the optimum",
    "lookahead-online": "the quantity is the minimum cost attainable at a horizon, not a "
                        "competitive ratio against an adversary",
    "competitive-paging": "no competitive ratio is claimed: the optimum is computed exactly per "
                          "instance and the gap is reported per cell",
    "sched-lookahead": "the lookahead bounds a merge decision inside a compaction window rather "
                       "than a scheduling queue",
    "mts-kserver": "no task system is solved; the framework is cited as the scoring convention "
                   "this paper adopts",
    "ski-rental": "the minimal online decision is cited as the base case, and no algorithm is "
                  "derived from it",
}


PLACEHOLDER = re.compile(r"^[^\w]*$")


def render_author(name):
    """`Given Middle Family` -> `Family, G. M.`, the house form; one token stays alone.

    A registry sometimes stores a dash in the family field (two entries here carry `-` with
    given-name initials beside it).  That is not a name and must never be printed as one: the
    family token has no letter, so the component is reported as not established instead of
    standing in the author position as a hyphen.
    """
    toks = [t for t in re.sub(r"\s+", " ", html.unescape(name or "")).split() if t]
    if not toks:
        return ""
    if PLACEHOLDER.match(toks[-1]):
        # A registry may put a dash where the family name belongs and carry the whole name in the
        # given-name field.  The record then DOES have an author, and the entry used to say it did
        # not -- a false statement about a record the same entry had just verified.  The name is
        # printed in the order the record gives it, because inverting it would require knowing
        # which token is the family, and that is exactly what the record did not supply.
        toks = toks[:-1]
        if not toks:
            return ""
        return " ".join(toks)
    if len(toks) == 1:
        return toks[0]                      # mononym: no initial to invent
    family = toks[-1]
    # a registry may store the family in the capitals of its own field; the entry prints
    # the form, so the fold is applied here rather than trusted to the source
    if family.isupper() and len(family) > 1:
        family = family[:1].upper() + family[1:].lower()
    inits = " ".join(t[0].upper() + "." for t in toks[:-1] if t[0].isalpha())
    return ("%s, %s" % (family, inits)).strip().rstrip(",")


def render_authors(names):
    out = [render_author(n) for n in (names or [])]
    out = [a for a in out if a]
    if not out:
        return "author not established on Crossref for this DOI"
    if len(out) >= 4:
        return "; ".join(out[:3] + ["et al."])
    return "; ".join(out)



MODEL = dict(K=3, R=3, Tmax=8, Rmax=5, Kmax=5)

# named works are numbered after the corpus, so every citation key in the paper is numeric
# three digits on purpose: the reference gate reads a 4-digit run at line start as a
# YEAR, so a [1000]-style marker is never parsed as an entry
# A key resolves to a NUMBER, and the six aliases resolve to the corpus entry that carries the
# same DOI -- one work, one entry.  The two documents Crossref does not index are numbered after
# the corpus, three digits on purpose: the journal's reference gate reads a 4-digit run at line
# start as a year, so a [1000]-style marker is never parsed as an entry.
NAMED_NUM = dict((k, str(240 + i)) for i, k in enumerate(NAMED))


def bind_aliases(order):
    """Point every alias at the entry whose DOI it names, and refuse an alias with no target."""
    by_doi = dict((e["doi"].lower(), e["_ref"]) for e in order)
    for k, doi in NAMED_ALIAS.items():
        if doi not in by_doi:
            raise SystemExit("alias %r names DOI %s, which no corpus entry carries" % (k, doi))
        NAMED_NUM[k] = by_doi[doi]


def load():
    res = json.load(open("results.json"))
    place = json.load(open("placement.json"))
    return res, place


def resolve(res, path):
    """Resolve `cells[R,K,T].field` or a dotted key path in results.json."""
    m = re.match(r"cells\[(\d+),(\d+),(\d+)\]\.(\w+)$", path)
    if m:
        R, K, T, field = (int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4))
        for c in res["cells"]:
            if (c["R"], c["K"], c["T"]) == (R, K, T):
                if field not in c:
                    raise KeyError("no field %r in cell %s" % (field, path))
                return c[field]
        raise KeyError("no such cell %s" % path)
    cur = res
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(path)
        cur = cur[part]
    return cur


def computed(res, key):
    """Values composed here (from artifact numbers only), so the prose never does arithmetic."""
    cells = res["cells"]
    if key == "model.K":
        return MODEL["K"]
    if key == "model.R":
        return MODEL["R"]
    if key == "model.Tmax":
        return MODEL["Tmax"]
    if key == "model.Rmax":
        return MODEL["Rmax"]
    if key == "model.Kmax":
        return MODEL["Kmax"]
    if key == "range.loss_min_pct":
        v = min(100.0 * c["greedy_loss"] / c["traces"] for c in cells if c["K"] >= 3)
        return round(v, 1)
    if key == "range.loss_max_pct":
        v = max(100.0 * c["greedy_loss"] / c["traces"] for c in cells if c["K"] >= 3)
        return round(v, 1)
    if key == "wstar0_k2_cells":
        # The cells with w*=0 that ARE K=2 controls: the predicate the sentence asserts.  It had no
        # key, so the sentence borrowed the complement's and printed 1 where the table shows three.
        return sum(1 for c in cells if c["K"] == 2 and c["wstar"] == 0)
    if key == "wstar0_minus_k2_cells":
        # The complement, kept beside it: the cells with w*=0 that are NOT K=2 controls, where a
        # real choice exists and the zero horizon means the first genuine choice is the last flush.
        # Written as its own predicate rather than as `eq0 - |K=2|`: that arithmetic is only equal
        # to this set when every K=2 cell has w*=0, and an identity that holds by accident of the
        # grid is exactly what the guard below has to be able to lose.
        return sum(1 for c in cells if c["K"] != 2 and c["wstar"] == 0)
    if key == "detail.k5t6_loss":
        return res["cells"][[i for i, c in enumerate(cells)
                            if (c["R"], c["K"], c["T"]) == (3, 5, 6)][0]]["greedy_loss"]
    if key == "detail.k5t6_traces":
        return res["cells"][[i for i, c in enumerate(cells)
                            if (c["R"], c["K"], c["T"]) == (3, 5, 6)][0]]["traces"]
    if key == "lookahead.w1_loss":
        return res["lookahead_worse"]["w1_loss"]
    if key == "lookahead.w0_loss":
        return res["lookahead_worse"]["w0_loss"]
    if key == "lookahead.deployed_loss":
        return res["lookahead_worse"]["deployed_loss"]
    if key == "control.exact_loss":
        return res["control"]["exact_loss"]
    if key == "control.exact_traces":
        return res["control"]["exact_traces"]
    if key == "control.refuting_loss":
        return res["control"]["refuting_loss"]
    # remaining keys map onto flat results.json fields under their published names
    alias = {"anti.wins": "anti_wins", "anti.loses": "anti_loses",
             "anti.choice_cells": "anti_choice_cells"}
    if key in alias:
        return res[alias[key]]
    raise KeyError(key)


# A marker that states a COUNT OF ROWS of the per-cell table, with the predicate it asserts.
# The predicate is applied to the table as printed, not to results.json: the failure this exists
# for was a marker that agreed with the artifact's own arithmetic and disagreed with the table a
# reader sees, so the binding has to be to the same text the reader compares against.
ROW_COUNT_KEYS = {
    "wstar_eq0_cells": lambda w, k: w == 0,
    "wstar0_k2_cells": lambda w, k: w == 0 and k == 2,
    "wstar0_minus_k2_cells": lambda w, k: w == 0 and k != 2,
}


LEVEL_CLAIM = re.compile(r"Contribution level:\s*\**\s*`([^`]+)`")


def check_exception_is_stated(prose, res):
    """A census with an exception must not reach a paper that omits it.

    This guard exists because of the defect that produced the exception: the package used to
    state that the fan-in correspondence held in `17 of the 17` cells, and that number was
    `cells where fanin_gap_max == 0` -- a statistic pinned to 0 for every input by construction,
    so it could not have reported anything else.  The count that CAN move said 16, with 120
    decisions failing in one cell.  A green statistic that cannot vary hid a false sentence, and
    the sentence sat in the abstract.  So the rule is mechanical in both directions: if the
    census holds failures, the prose must carry the failure count; and if the prose carries one,
    the census must hold it.  Neither direction reads the other's intent, and both read the
    template rather than the rendered body, where a marker has already become a number.
    """
    ex = res.get("fanin_exception") or {}
    below = ex.get("below", 0)
    marker = "{{n:fanin_exception.below}}"
    problems = []
    if below and marker not in prose:
        problems.append("the census has %d decision(s) below the widest alternative and the prose "
                        "never states %s" % (below, marker))
    if not below and marker in prose:
        problems.append("the prose cites %s but the census holds no failures" % marker)
    if ex.get("cells", 0) + res.get("cells_with_fanin_gap_min_zero", 0) != res.get("n_cells"):
        problems.append("the cells that agree (%s) and the cells that fail (%s) do not add up to "
                        "the grid (%s)" % (res.get("cells_with_fanin_gap_min_zero"),
                                           ex.get("cells"), res.get("n_cells")))
    return problems


def check_level_agreement(prose, readme):
    """The declared contribution level, read the same way off both carriers that state it.

    The review found the copies disagreeing, and the disagreement was invisible because no
    program compared them: the abstract declared `theory+empirics`, the registration's
    conditional -- whose condition had already fired -- called for a case study, and
    `README.md` declared nothing at all.  A guard cannot read the registration (it lives on
    the issue tracker, outside the tree), and a guard that guessed at it would be checking
    its own copy of a decision.  What it can bind is the two carriers that ARE in the
    package: exactly one claim each, and the same claim in both.  Silence fails, because a
    carrier that states no level is not agreeing with the one that does -- it is the seat
    the reviewer had to reconstruct by hand.
    """
    problems = []
    got = {}
    for name, text in (("manuscript_prose.md", prose), ("README.md", readme)):
        found = [f.strip() for f in LEVEL_CLAIM.findall(text or "")]
        if not found:
            problems.append("%s declares no contribution level" % name)
        elif len(found) > 1:
            problems.append("%s declares %d contribution levels: %s" % (name, len(found), found))
        else:
            got[name] = found[0]
    if len(got) == 2 and got["manuscript_prose.md"] != got["README.md"]:
        problems.append("the two carriers disagree: the abstract says %r, README says %r"
                        % (got["manuscript_prose.md"], got["README.md"]))
    return problems


def check_row_count_keys(prose, bound_values):
    """Compare every row-count marker with the table as this generator printed it.

    `prose` is the TEMPLATE, with its `{{n:...}}` markers still in place.  The first version of the
    clause rule scanned the substituted body, where every marker has already become a number, so it
    found no markers at all and could not fire: a guard reading the output instead of the claim.
    """
    problems = []
    table = cell_table(json.load(open("results.json")))
    rows = []
    for line in table.split("\n"):
        m = re.match(r"\|\s*R=(\d+) K=(\d+) T=(\d+)\s*\|", line)
        if not m:
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append((int(m.group(2)), int(cols[-1])))       # (K, w*)
    if len(rows) != 17:
        problems.append("the emitted table has %d rows, expected 17 -- cannot bind against it"
                        % len(rows))
        return problems
    # the arithmetic these keys used to rely on: every K=2 cell has w*=0.  Asserted, because a key
    # defined as a difference is only that set while this holds.
    bad = [(k, w) for (k, w) in rows if k == 2 and w != 0]
    if bad:
        problems.append("a K=2 control row does not have w*=0 (%s); the complement keys are then "
                        "not counting what their names say" % bad)
    for key, pred in ROW_COUNT_KEYS.items():
        if key not in bound_values:
            continue
        want = sum(1 for (k, w) in rows if pred(w, k))
        got = int(bound_values[key])
        if got != want:
            problems.append("{{n:%s}} printed %d, but the table it describes has %d row(s) with "
                            "that property (%d rows read)" % (key, got, want, len(rows)))
    # ---- and the sentence, not only the value ------------------------------------------------
    # The defect the review found was not a wrong number: the marker's number was right and the
    # sentence asserted the OTHER predicate.  A value check cannot see that; the key's own name
    # can.  `minus` in a key means "the complement of", so a sentence carrying that key may not
    # assert the property it is the complement of, and a key that counts `K = 2` cells must be
    # used where `K = 2` is what is being claimed.
    # The unit is the CLAUSE, not the sentence.  The first version of this check read sentences and
    # asked whether the word "not" appeared anywhere in one; the sentence carrying the defect also
    # carried "The qualifier is not a hedge", so an unrelated word cleared it.  A window wide
    # enough to hold an innocuous token is not a check.
    # the marker's own colon is a clause separator, so a marker is replaced by a punctuation-free
    # sentinel before the split -- otherwise the key is severed from the clause that carries it and
    # the rule reads an empty clause (the first version did exactly that and never fired).
    marked = re.sub(r"\{\{n:([^}]+)\}\}", lambda m: "\x00%s\x00" % m.group(1), prose)
    for clause in re.split(r"[.;:,]|\s[\u2014\u2013-]\s|\s(?:and|but|while|whereas)\s", marked):
        keys = re.findall(r"\x00([^\x00]+)\x00", clause)
        if not keys:
            continue
        names_k2 = re.search(r"K\s*=\s*2", clause)
        for key in keys:
            if "minus" in key and names_k2:
                problems.append("{{n:%s}} is the complement of the `K = 2` count, but the clause "
                                "using it is where `K = 2` is asserted: %r"
                                % (key, clause.strip()[:140]))
            if key.endswith("_k2_cells") and "minus" not in key and not names_k2:
                problems.append("{{n:%s}} counts `K = 2` cells, but the clause using it does not "
                                "name `K = 2`: %r" % (key, clause.strip()[:140]))
    return problems


def fmt(v):
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return ("%.3f" % v).rstrip("0").rstrip(".")
    return str(v)


def cell_table(res):
    out = ["| cell | traces | visible states | refuting | deployed non-optimal | worst excess "
           "| cheapest-overlap | w\\* |",
           "|---|---|---|---|---|---|---|---|"]
    for c in res["cells"]:
        out.append("| R=%d K=%d T=%d | %d | %d | %d | %d (%.1f%%) | %.3f | %d%s | %d |"
                   % (c["R"], c["K"], c["T"], c["traces"], c["states"], c["refuting"],
                      c["greedy_loss"], 100.0 * c["greedy_loss"] / c["traces"],
                      c["greedy_worst"], c["anti_loss"],
                      " (control)" if c["K"] == 2 else "", c["wstar"]))
    out.append("")
    out.append("Cells with `K = 2` are controls: the legal merge set is a singleton, no rule has "
               "freedom, and both rules tie at zero losses. `w\\*` is the minimal exact horizon, "
               "and `w\\* = 0` holds in %d of the %d cells -- not only where no choice exists: "
               "it holds exactly where the zero-lookahead rule is already exact, which includes "
               "the `K = 2` controls (no choice ever exists) and one cell with `K = 5` where the "
               "first genuine choice arrives at the last flush. `make_figure.py` asserts that "
               "equivalence over every cell."
               % (res["wstar_eq0_cells"], len(res["cells"])))
    return "\n".join(out)


def control_table(res):
    c = res["control"]
    out = ["| control | cell | traces lost by the rule | traces |",
           "|---|---|---|---|"]
    out.append("| `min Opt(S)`, in a cell with `w\\* = 0` | R=3 K=5 T=6 | %d | %d |"
               % (c["exact_loss"], c["exact_traces"]))
    out.append("| `min Opt(S)`, in a refuting cell | R=3 K=3 T=6 | %d | %d |"
               % (c["refuting_loss"], c["refuting_traces"]))
    out.append("")
    out.append("An exact visible-state rule exists in the first cell and cannot exist in the "
               "second; the same rule is used in both, so the pair separates \"no rule can do "
               "it\" from \"we did not find one\".")
    return "\n".join(out)


def reflow(text, width=96):
    """Re-wrap prose paragraphs; leave headings, tables, lists and fenced blocks untouched."""
    import textwrap
    out, buf, fence = [], [], False
    def flush():
        if not buf:
            return
        para = " ".join(x.strip() for x in buf)
        out.extend(textwrap.wrap(para, width=width, break_long_words=False,
                                 break_on_hyphens=False) or [""])
        del buf[:]
    for line in text.split("\n"):
        st = line.strip()
        if st.startswith("```"):
            flush(); fence = not fence; out.append(line); continue
        if fence:
            out.append(line); continue
        if (not st or st.startswith(("#", "|", "- ", "* ", ">" )) or re.match(r"^\d+\. ", st)):
            flush(); out.append(line); continue
        buf.append(line)
    flush()
    return "\n".join(out)


def themes(place):
    """section -> theme -> [ref index] over the placed entries, stable order."""
    order = sorted(place["entries"], key=lambda e: (e["section"], e["theme"],
                                                    (e["verified"]["title"] or "").lower(),
                                                    e["doi"]))
    mapping = {}
    for i, e in enumerate(order, 1):
        e["_ref"] = "%d" % i
        mapping.setdefault(e["section"], {}).setdefault(e["theme"], []).append(e["_ref"])
    return order, mapping


def main():
    res, place = load()
    # the positive control is measured by lemma_scale; record it here from that program
    import lemma_scale as S
    def rule_losses(R, K, T):
        r = S.analyse(R, K, T)
        groups = r["groups"]
        opt = {}
        for key, g in groups.items():
            inter = set(g["argmins"][0])
            for a in g["argmins"][1:]:
                inter &= set(a)
            opt[key] = min(inter) if inter else None
        from lemma import Cell, Solver
        import itertools
        lost = 0
        for tr in itertools.product(range(R), repeat=T):
            c = Cell(R, K, T)
            live, runs, total = tuple([0] * R), (), 0
            for i in range(T):
                runs2, live2 = c.step(runs, live, tr[i])
                cand = c.legal(runs2) if len(runs2) > K else ()
                if not cand:
                    runs, live = runs2, live2
                    continue
                key = (i, runs2, live2, tr[i])
                pick = opt.get(key)
                if pick is None or pick not in cand:
                    pick = max(cand, key=lambda rr: (c.merge(runs2, rr, live2)[1], -rr))
                runs, paid = c.merge(runs2, pick, live2)
                total += paid
                live = live2
            if total > Solver(tr, R, K).opt_from(0, (), tuple([0] * R)):
                lost += 1
        return lost, R ** T

    ex_loss, ex_n = rule_losses(3, 5, 6)
    rf_loss, rf_n = rule_losses(3, 3, 6)
    res["control"] = dict(exact_loss=ex_loss, exact_traces=ex_n,
                          refuting_loss=rf_loss, refuting_traces=rf_n)
    json.dump(res, open("results.json", "w"), indent=1, sort_keys=True)

    order, mapping = themes(place)
    bind_aliases(order)
    prose = open("manuscript_prose.md").read()

    bound = []          # every number produced by substitution, for the stray scan
    bound_values = {}   # key -> the string it printed, for the row-count binding below

    def sub_n(m):
        key = m.group(1)
        try:
            v = resolve(res, key)
        except KeyError:
            v = computed(res, key)
        s = fmt(v)
        bound.append(s)
        bound_values[key] = s
        return s

    body = re.sub(r"\{\{n:([^}]+)\}\}", sub_n, prose)

    def sub_table(m):
        which = m.group(1)
        if which == "cells":
            t = cell_table(res)
        elif which == "controls":
            t = control_table(res)
        else:
            raise KeyError(which)
        bound.extend(re.findall(r"\d+(?:\.\d+)?", t))
        return t

    body = re.sub(r"\{\{table:(\w+)\}\}", sub_table, body)

    def sub_cites(m):
        section, theme = m.group(1), m.group(2)
        wanted = mapping.get(section, {}).get(theme)
        if wanted is None:
            # section labels are prose-side names; fall back to suffix match
            for sec, th in mapping.items():
                if sec.split()[0] == "§" + section:
                    wanted = th.get(theme)
                    if wanted:
                        break
        if not wanted:
            raise KeyError("no placed references for section %s theme %s" % (section, theme))
        bound.extend(re.findall(r"\d+", " ".join(wanted)))
        return "[" + ", ".join(wanted) + "]"

    body = re.sub(r"\{\{cites:(\d+):([\w-]+)\}\}", sub_cites, body)

    def sub_cite(m):
        k = m.group(1)
        # NAMED_NUM is the alias-aware map: a key whose work lives in the corpus resolves to
        # that entry's number, so `{{cite:oneil1996}}` and the corpus entry print as one [n]
        if k not in NAMED_NUM:
            raise KeyError(k)
        return "[%s]" % NAMED_NUM[k]

    body = re.sub(r"\{\{cite:(\w+)\}\}", sub_cite, body)

    # reference list: placed corpus + the works read in full
    # The journal's reference gate reads `[12]` at the START of a line, and counts entries
    # not separated from the one above by a blank line as a single paragraph to any
    # CommonMark renderer.  Both forms are emitted deliberately.
    refs = ["### Corpus: DOI-verified against Crossref (see `reference-check.md`)", ""]
    for e in order:
        v = e["verified"]
        # house form: authors (Family, I.) -- year in parentheses -- title -- venue -- a
        # resolvable URL -- the one-line stated difference.  Emitted from stored fields only;
        # the difference line is the theme's, written once and applied per entry, so the list
        # does not repeat one invented formula 239 times.
        diff = THEME_DIFFERENCE.get(e["theme"])
        if not diff:
            raise SystemExit("theme %r has no stated difference; add one before emitting"
                             % e["theme"])
        # the author component ends with exactly one period: `Family, I.` already carries it,
        # `et al` takes it from the format, and neither prints `..`
        refs.append("[%s] %s. (%s). %s. %s. https://doi.org/%s. Difference: %s."
                    % (e["_ref"], render_authors(v.get("authors")).rstrip("."),
                       v.get("year") or e.get("year") or "--",
                       html.unescape(v["title"] or "(no title field)").rstrip("."),
                       html.unescape(v["venue"] or "(no venue field)").rstrip("."),
                       v["doi"], diff))
        refs.append("")
    refs.append("### Works read in full, which Crossref does not index")
    refs.append("")
    for k, d in NAMED.items():
        refs.append("[%s] %s. (%s). %s. %s. %s. Difference: %s."
                    % (NAMED_NUM[k], d["authors"], d["year"], d["title"], d["venue"],
                       d["url"], d["difference"]))
        refs.append("")
    refs = "\n".join(refs)
    body = body.replace("{{refs}}", refs)

    # ---- stray-number scan: every multi-digit number must have been produced above -------
    allowed = set()
    for s in bound:
        allowed.add(s)
        allowed.add(s.replace(".", ""))
    for s in re.findall(r"\d+(?:\.\d+)?", refs):
        allowed.add(s)
    scan = body.split("## References")[0]
    # not figures: section numbers (§4.3), identifiers and traces in `code spans`, and years.
    # Everything else must have been produced by a substitution above.
    scan = re.sub(r"(?m)^#{1,6} .*$", " ", scan)   # headings: section numbering, no figures
    scan = re.sub(r"§\s?\d+(?:\.\d+)?", " ", scan)
    scan = re.sub(r"`[^`]*`", " ", scan)
    scan = re.sub(r"\b(?:19|20)\d{2}\b", " ", scan)
    stray = []
    for tok in re.findall(r"\d+(?:\.\d+)?", scan):
        if len(tok.replace(".", "")) <= 1:      # single digits: section numbering, enumerations
            continue
        if tok in allowed:
            continue
        stray.append(tok)
    if stray:
        print("STRAY NUMBERS (not bound to any artifact): %s" % sorted(set(stray)))
        print("  -> a number in the prose that no program emitted; refusing to write the paper.")
        return 1

    # ---- row-count binding: a marker that states a count of table rows, read against the table --
    # The stray scan above cannot see this class.  It polices multi-digit tokens, and the defect the
    # review found was a BOUND MARKER whose predicate was the complement of the sentence's: the
    # marker printed `1`, one digit, and the sentence contradicted a table three lines above it.
    # Widening the token class would flood on section numbers and enumerations, so the repair is to
    # bind these markers to the rows AS PRINTED: parse the table we just emitted, apply the key's
    # own predicate to each row, and refuse to write the paper when a marker disagrees with it.
    if problems := check_row_count_keys(prose, bound_values):
        for p in problems:
            print("ROW-COUNT MARKER: %s" % p)
        print("  -> a marker that counts table rows disagrees with the table; refusing to write.")
        return 1

    # ---- contribution level: the same claim, off both carriers that state one ---------------
    # Same class as the row-count defect above and the same reason for a guard: the level is a
    # claim a reader meets in the abstract and again in README, and nothing compared the two.
    if problems := check_level_agreement(prose, open("README.md").read()):
        for p in problems:
            print("CONTRIBUTION LEVEL: %s" % p)
        print("  -> the declared level is not one claim off every carrier; refusing to write.")
        return 1

    if problems := check_exception_is_stated(prose, res):
        for p in problems:
            print("UNSTATED EXCEPTION: %s" % p)
        print("  -> a census with an exception and prose without it; refusing to write.")
        return 1

    body = reflow(body)

    open("manuscript.md", "w").write(body)
    n_cited = len(order)
    print("manuscript.md written: %d characters" % len(body))
    print("  markers bound: %d numbers, %d tables, %d citation groups"
          % (len(bound), 2, len(re.findall(r"\{\{cites:", prose))))
    print("  references: %d corpus + %d read in full = %d"
          % (n_cited, len(NAMED), n_cited + len(NAMED)))
    print("  stray-number scan: clean")
    if n_cited + len(NAMED) < 100:
        print("  REFERENCE FLOOR NOT MET: %d < 100" % (n_cited + len(NAMED)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
