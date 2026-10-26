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
import json
import re
import sys

NAMED = {
    "oneil1996": ("r_oo", "P. O'Neil, E. Cheng, D. Gawlick, E. O'Neil. The log-structured "
                          "merge-tree (LSM-tree). Acta Informatica, 1996. "
                          "DOI 10.1007/s002360050048"),
    "rocksdb_compaction": ("r_rc", "RocksDB project documentation, *Compaction* (wiki, read "
                                  "2026-10-27): taxonomy of Classic Leveled / Tiered / "
                                  "Tiered+Leveled / FIFO, and the statement that LevelDB and "
                                  "RocksDB compaction is some-to-some over overlapping data."),
    "rocksdb_overview": ("r_ro", "RocksDB project documentation, *RocksDB Overview* (wiki, read "
                                 "2026-10-27): level style vs universal style compaction, and "
                                 "the role of overlapping keys in L0."),
    "paging_lookahead": ("r_pl", "On Competitive On-Line Paging with Lookahead. BRICS report "
                                 "1995 (DOI 10.7146/brics.v2i50.19951); journal version 1997 "
                                 "(DOI 10.1016/s0304-3975(98)00118-2): competitive efficiency "
                                 "depends on k + l."),
    "semi_online_two": ("r_s2", "Semi-Online Scheduling on Two Identical Parallel Machines with "
                                "Initial-Lookahead Information. 2023. "
                                "DOI 10.1142/s0217595923500033."),
    "semi_online_uniform": ("r_su", "Semi-online scheduling on two uniform parallel machines "
                                    "with initial lookahead. 2024. DOI 10.1051/ro/2024042."),
    "disk_sched": ("r_ds", "Disk scheduling policies with lookahead. 2002. "
                           "DOI 10.1145/588160.588165."),
    "mts_optimal": ("r_mt", "An optimal on-line algorithm for metrical task systems. 1992. "
                            "DOI 10.1145/146585.146588."),
}

MODEL = dict(K=3, R=3, Tmax=8, Rmax=5, Kmax=5)


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
               "freedom, and both rules tie at zero losses. `w\\*` is the minimal exact horizon; "
               "it is 0 exactly where no genuine choice exists.")
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
        e["_ref"] = "r%d" % i
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
        if k not in NAMED:
            raise KeyError(k)
        return "[%s]" % NAMED[k][0]

    body = re.sub(r"\{\{cite:(\w+)\}\}", sub_cite, body)

    # reference list: placed corpus + the works read in full
    refs = ["### Corpus (DOI-verified against Crossref; see `reference-check.md`)", ""]
    for e in order:
        v = e["verified"]
        au = ", ".join(v["authors"][:3]) if v["authors"] else "(no author field in record)"
        refs.append("- **[%s]** %s. *%s*. %s. DOI %s."
                    % (e["_ref"], v["title"], v["venue"] or "(no venue field)",
                       au, v["doi"]))
    refs.append("")
    refs.append("### Works read in full for the comparison in §6 and §2.2")
    refs.append("")
    for k, (tag, text) in NAMED.items():
        refs.append("- **[%s]** %s" % (tag, text))
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
