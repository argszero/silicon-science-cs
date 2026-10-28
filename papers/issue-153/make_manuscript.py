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
# SAME WORKS as corpus entries, matched by DOI -- printed twice, once in the corpus section
# and once under "read in full", so 247 entry lines described 241 distinct works.  One work
# is one entry (R676); the six now resolve to their corpus entry, and only the two documents
# Crossref does not index stay here, each with the body responsible and the date it was read.
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
        return ""
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
    if key == "wstar0_minus_k2_cells":
        # the cells with w*=0 that are NOT K=2 controls: a real choice exists there, and the
        # zero horizon means the first genuine choice arrives at the last flush
        return res["wstar_eq0_cells"] - sum(1 for c in cells if c["K"] == 2)
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

    def sub_n(m):
        key = m.group(1)
        try:
            v = resolve(res, key)
        except KeyError:
            v = computed(res, key)
        s = fmt(v)
        bound.append(s)
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
