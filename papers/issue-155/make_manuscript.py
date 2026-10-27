#!/usr/bin/env python3
"""Issue #155 -- generate manuscript.md from manuscript_prose.md + results.json + placement.json.

No number in the manuscript is typed by hand. Every one is either a `{{n:path}}` marker
resolved from results.json, a `{{p:path}}` percentage of one, a table generated from a
results.json list, or a citation number assigned by this program. After substituting, the
generator runs a stray-number scan over the body it produced and **refuses to write the
paper** if a multi-digit number appears that no substitution produced.

Why refusal rather than a warning: the scan exists to make "I typed a number from memory"
impossible to merge. A warning would be read once and then live in the file forever.

Markers
  {{n:path}}                 a number from results.json
  {{p:path}}                 the same, as a percentage with one decimal
  {{cites:SECTION}}          every placed reference of that section, as [1,2,3]
  {{cites:SECTION:recent}}   the same, restricted to year >= RECENT_YEAR
  {{cites:SECTION:earlier}}  the same, restricted to year <  RECENT_YEAR
  {{cite:key}}               one placed reference by key
  {{table:name}}             a generated table
  {{refs}}                   the reference list, generated from placement.json

Selectors in a path: `name[n]`, `name[n,m]`, `name[n,m,k]` pick the single row of a list
whose n / n,m / n,m,k fields match. A selector that matches zero or two rows is an error --
a table the prose silently reads the wrong row of is worse than a missing table.

`--check` recomputes and compares against the committed manuscript.md byte for byte instead
of writing it, so `reproduce.sh` can verify the manuscript without rewriting the artifact a
previous verification described.
"""
import html
import json
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
PROSE = os.path.join(HERE, "manuscript_prose.md")
OUT = os.path.join(HERE, "manuscript.md")
RECENT_YEAR = 2024
REF_FLOOR = 100


# ---------------------------------------------------------------------------
# loading and formatting
# ---------------------------------------------------------------------------

def load():
    res = json.load(open(os.path.join(HERE, "results.json"), encoding="utf-8"))
    place = json.load(open(os.path.join(HERE, "placement.json"), encoding="utf-8"))
    return res, place


def fmt(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        # plain digits, no thousands separator: a separator would split one number into two
        # in the stray-number scan and quietly weaken it
        return str(v)
    if isinstance(v, float):
        return ("%.4f" % v).rstrip("0").rstrip(".")
    raise TypeError("cannot format %r" % (v,))


def pct(v):
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise TypeError("percentage of %r" % (v,))
    return "%.1f" % (100.0 * v)


# a key may carry digits after its first letter: results.json holds `T1`, `T2`, `T3`
PART = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[([0-9]+(?:,[0-9]+)*)\])?$")
ROWKEYS = ("n", "m", "k")


def resolve(res, path):
    cur = res
    for part in path.split("."):
        m = PART.match(part)
        if not m:
            raise KeyError("bad path segment %r in %r" % (part, path))
        name, idx = m.group(1), m.group(2)
        if not isinstance(cur, dict) or name not in cur:
            raise KeyError("no key %r in %r" % (name, path))
        cur = cur[name]
        if idx is not None:
            if not isinstance(cur, list):
                raise KeyError("%r is not a list in %r" % (name, path))
            want = [int(x) for x in idx.split(",")]
            rows = [r for r in cur
                    if all(r.get(ROWKEYS[i]) == v for i, v in enumerate(want))]
            if len(rows) != 1:
                raise KeyError("selector [%s] matched %d rows of %r"
                               % (idx, len(rows), name))
            cur = rows[0]
    return cur


def computed(res, key):
    """Values composed here from artifact rows only -- the prose never does arithmetic.

    Each one answers a question the prose asks and no single stored key holds. Everything
    it is built from is a stored number, and the result enters the stray scan like any
    substituted value, so a composed number is as bound as a stored one.
    """
    if key == "total_distinct_windows":
        return sum(r["windows"] for r in res["threshold_distinct"])
    if key == "total_ties_windows":
        return res["threshold_ties_totals"]["windows"]
    if key == "ties_gap_scope_windows":
        return res["gap_summary"]["ties_windows"]
    if key == "cert_pairs_total":
        return res["certificate"]["distinct"]["pairs"] + res["certificate"]["ties"]["pairs"]
    if key == "agree_distinct_n7_pct":
        r = [x for x in res["threshold_distinct"] if x["n"] == 7][0]
        return "%.1f" % (100.0 * (1.0 - r["lds_understates_fraction"]))
    if key == "agree_ties_pct":
        s = res["gap_summary"]
        return "%.1f" % (100.0 * (1.0 - s["ties_nonzero"] / s["ties_windows"]))
    if key == "rules_informative_cells":
        return sum(1 for r in res["rules"] if r["k"] < r["m"])
    if key == "rules_forced_cells":
        return sum(1 for r in res["rules"] if r["k"] >= r["m"])
    if key == "rules_informative_min_pct":
        v = [100.0 * r["aligned_fraction"] for r in res["rules"] if r["k"] < r["m"]]
        return "%.1f" % min(v)
    if key == "rules_informative_max_pct":
        v = [100.0 * r["aligned_fraction"] for r in res["rules"] if r["k"] < r["m"]]
        return "%.1f" % max(v)
    if key == "inline_cells":
        bad = [r for r in res["rules"] if r["k"] >= r["m"] and r["aligned_fraction"] != 0.0]
        return len(bad)
    raise KeyError("no computed value %r" % key)


# ---------------------------------------------------------------------------
# references
# ---------------------------------------------------------------------------

def clean(text):
    """Crossref titles carry markup (<i>, <scp>) and entities (&#39;, &amp;)."""
    t = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(t).strip()


def render_author(name):
    """`Given Middle Family` -> `Family, G. M.` -- the form the house style admits."""
    toks = [t for t in name.replace(".", ". ").split() if t]
    if not toks:
        return ""
    family = toks[-1]
    initials = " ".join(t[0] + "." for t in toks[:-1] if t[0].isalpha())
    return ("%s, %s" % (family, initials)).strip().rstrip(",")


def order_and_number(place):
    """Stable order and the numeric keys the reference gate reads.

    Sorted by (section, title, doi) so the numbering is a function of the corpus and not
    of the order an author happened to write the placement in.
    """
    entries = sorted(place["placed"],
                     key=lambda e: (e["section"], (e["title"] or "").lower(), e["doi"]))
    by_section = {}
    for i, e in enumerate(entries, 1):
        e["_num"] = i
        by_section.setdefault(e["section"], []).append(e)
    return entries, by_section


def cite_list(rows):
    return "[" + ",".join(str(e["_num"]) for e in rows) + "]"


def reference_list(entries):
    out = ["## References", ""]
    for e in entries:
        authors = [render_author(a).rstrip(" ,") for a in e.get("authors") or []]
        authors = [a for a in authors if a]
        # "; " between authors, not ", ": "Hui, Yang, Wang" is one person's name or three
        # authors depending on who reads it, and a reference list cannot afford that
        if len(authors) > 4:
            astr = "; ".join(authors[:4]) + "; et al."
        elif authors:
            astr = "; ".join(authors)
        else:
            astr = "(no author field in the record)"
        venue = clean(e.get("venue") or "") or "(no venue field in the record)"
        year = e.get("year") or ""
        title = clean(e.get("title") or "") or "(no title field in the record)"
        entry = "[%d] %s. %s. %s, %s. DOI %s." % (
            e["_num"], astr.rstrip(".,"), title.rstrip("."), venue, year, e["doi"])
        out.append(entry)
        # a blank line between entries: consecutive entry lines are ONE paragraph to every
        # CommonMark renderer, which is how a 100-entry list renders as a wall
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# tables (generated, never typed)
# ---------------------------------------------------------------------------

def table(name, res):
    if name == "threshold_distinct":
        out = ["| n | windows | `runs(p)` violations | windows where LDS understates | share |",
               "|---|---|---|---|---|"]
        for r in res["threshold_distinct"]:
            out.append("| %d | %d | %d | %d | %.4f |"
                       % (r["n"], r["windows"], r["runs_p_violations"],
                          r["lds_understates_windows"], r["lds_understates_fraction"]))
        return "\n".join(out)

    if name == "threshold_ties":
        out = ["| n | m | windows | T1 | T2 | T3 | LDS | mean required k |",
               "|---|---|---|---|---|---|---|---|"]
        for r in res["threshold_ties"]:
            v = r["violations"]
            out.append("| %d | %d | %d | %d | %d | %d | %d | %.4f |"
                       % (r["n"], r["m"], r["windows"], v["T1"], v["T2"], v["T3"], v["LDS"],
                          r["required_k_mean"]))
        return "\n".join(out)

    if name == "gap_distinct":
        out = ["| n | windows | gap 0 | gap 1 | gap 2 | max gap |",
               "|---|---|---|---|---|---|"]
        for r in res["gap_distinct"]:
            h = r["histogram"]
            out.append("| %d | %d | %d | %d | %d | %d |"
                       % (r["n"], r["windows"], h.get("0", 0), h.get("1", 0),
                          h.get("2", 0), r["max"]))
        return "\n".join(out)

    if name == "gap_ties":
        out = ["| n | m | windows | gap 0 | gap 1 | max gap |",
               "|---|---|---|---|---|---|"]
        for r in res["gap_ties"]:
            h = r["histogram"]
            out.append("| %d | %d | %d | %d | %d | %d |"
                       % (r["n"], r["m"], r["windows"], h.get("0", 0), h.get("1", 0),
                          r["max"]))
        return "\n".join(out)

    if name == "rules":
        out = ["| n | m | k | windows | aligned rule loses | share | worst ratio | "
               "anti-rule control loses | share | cell measures? |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for r in res["rules"]:
            forced = r["k"] >= r["m"]
            out.append("| %d | %d | %d | %d | %d | %.4f | %.2f | %d | %.4f | %s |"
                       % (r["n"], r["m"], r["k"], r["windows"], r["aligned_loses"],
                          r["aligned_fraction"], r["aligned_worst_ratio"],
                          r["control_loses"], r["control_fraction"],
                          "no -- k >= m forces it" if forced else "yes -- k < m"))
        return "\n".join(out)

    raise KeyError("no table %r" % name)


# ---------------------------------------------------------------------------
# reflow
# ---------------------------------------------------------------------------

def reflow(text, width=96):
    """Re-wrap prose paragraphs; leave headings, tables, lists, quotes and refs untouched."""
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
            flush()
            fence = not fence
            out.append(line)
            continue
        if fence:
            out.append(line)
            continue
        # `[` is in this list because the reference entries start with `[12]`: reflowing
        # them would glue the whole bibliography into one paragraph, and the reference
        # gate would then count one entry where there are a hundred
        if (not st or st.startswith(("#", "|", "- ", "* ", "> ", "[", "!"))
                or re.match(r"^\d+\. ", st)):
            flush()
            out.append(line)
            continue
        buf.append(line)
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def generate():
    res, place = load()
    entries, by_section = order_and_number(place)
    prose = open(PROSE, encoding="utf-8").read()

    # ---- skeleton scan: the prose must carry NO number of its own ------------
    # Every number the manuscript prints is produced by a marker, so before a single
    # substitution the prose must contain none. Scanning the skeleton is what makes
    # this a binding instead of a pool test: a scan of the *substituted* body accepts
    # any typed number that happens to equal some value an artifact emitted, which is
    # exactly how a planted `37` once passed. The exemptions are the lexical forms the
    # paper legitimately writes: headings, §-references, code spans (which hold the
    # formulas), four-digit years, and the markers themselves.
    skel = re.sub(r"(?m)^#{1,6} .*$", " ", prose)
    skel = re.sub(r"§\s?\d+(?:\.\d+)?", " ", skel)
    skel = re.sub(r"`[^`]*`", " ", skel)
    skel = re.sub(r"\b(?:19|20)\d{2}\b", " ", skel)
    skel = re.sub(r"\{\{[^}]*\}\}", " ", skel)
    typed = [t for t in re.findall(r"\d+(?:\.\d+)?", skel)
             if len(t.replace(".", "")) > 1]
    if typed:
        print("TYPED NUMBERS IN THE PROSE (no marker produced them): %s" % sorted(set(typed)))
        print("  -> write it as a {{n:...}} marker bound to results.json, or it does not go in.")
        return None, None

    bound = []          # every value a substitution produced, for the stray scan
    cited = set()       # every reference number the body actually cites

    def sub_n(m):
        key = m.group(1)
        try:
            v = resolve(res, key)
        except KeyError:
            # composed values come back as ints or formatted strings; the substitution
            # must be text, and the binding must hold the exact form printed
            s = str(computed(res, key))
            bound.append(s)
            return s
        s = fmt(v)
        bound.append(s)
        return s

    body = re.sub(r"\{\{n:([^}]+)\}\}", sub_n, prose)

    def sub_p(m):
        key = m.group(1)
        try:
            v = resolve(res, key)
        except KeyError:
            raise KeyError("percentage of a computed value is not supported: %r" % key)
        s = pct(v)
        bound.append(s)
        return s

    body = re.sub(r"\{\{p:([^}]+)\}\}", sub_p, body)

    def sub_cites(m):
        section, scope = m.group(1), m.group(2)
        rows = by_section.get(section)
        if rows is None:
            raise KeyError("no placed references for section %r (have: %s)"
                           % (section, sorted(by_section)))
        if scope == "recent":
            rows = [e for e in rows if (e.get("year") or 0) >= RECENT_YEAR]
        elif scope == "earlier":
            rows = [e for e in rows if (e.get("year") or 0) < RECENT_YEAR]
        elif scope:
            raise KeyError("unknown citation scope %r" % scope)
        if not rows:
            # an empty bracket is a sentence that cites nothing: the prose claims a body of
            # work where the corpus has none, so this is refused rather than printed as []
            raise KeyError("section %r / scope %r selects no reference" % (section, scope))
        for e in rows:
            cited.add(e["_num"])
        s = cite_list(rows)
        bound.extend(re.findall(r"\d+", s))
        return s

    body = re.sub(r"\{\{cites:([^:}]+)(?::([a-z]+))?\}\}", sub_cites, body)

    by_key = {e["key"]: e for e in entries}

    def sub_cite(m):
        k = m.group(1)
        if k not in by_key:
            raise KeyError("no placed reference with key %r" % k)
        e = by_key[k]
        cited.add(e["_num"])
        s = "[%d]" % e["_num"]
        bound.extend(re.findall(r"\d+", s))
        return s

    body = re.sub(r"\{\{cite:([A-Za-z0-9_]+)\}\}", sub_cite, body)

    def sub_nplaced(m):
        s = str(len(entries))
        bound.append(s)
        return s

    body = re.sub(r"\{\{nplaced\}\}", sub_nplaced, body)

    def sub_table(m):
        t = table(m.group(1), res)
        bound.extend(re.findall(r"\d+(?:\.\d+)?", t))
        return t

    body = re.sub(r"\{\{table:([a-z_]+)\}\}", sub_table, body)

    refs = reference_list(entries)
    body = body.replace("{{refs}}", refs)

    # ---- residual markers are an error: an unresolved marker would print as literal text
    left = re.findall(r"\{\{[^}]*\}\}", body)
    if left:
        print("UNRESOLVED MARKERS: %s" % sorted(set(left)))
        return None, None

    # ---- citation coverage, both ways -------------------------------------
    uncited = [e["_num"] for e in entries if e["_num"] not in cited]
    if uncited:
        print("UNCITED REFERENCES (%d of %d): %s"
              % (len(uncited), len(entries), uncited[:20]))
        print("  -> a bibliography entry the body never cites is padding; refusing to write.")
        return None, None
    bogus = sorted(n for n in cited if n < 1 or n > len(entries))
    if bogus:
        print("CITED NUMBERS OUTSIDE THE BIBLIOGRAPHY: %s" % bogus)
        return None, None

    # ---- stray-number scan -------------------------------------------------
    allowed = set()
    for s in bound:
        allowed.add(s)
        allowed.add(s.replace(".", ""))
    for s in re.findall(r"\d+(?:\.\d+)?", refs):
        allowed.add(s)

    scan = body.split("## References")[0]
    # not figures: headings (section numbers), §4.3-style references, `code spans`,
    # years, and the fenced-environment markers. Everything else must have been produced.
    scan = re.sub(r"(?m)^#{1,6} .*$", " ", scan)
    scan = re.sub(r"§\s?\d+(?:\.\d+)?", " ", scan)
    scan = re.sub(r"`[^`]*`", " ", scan)
    scan = re.sub(r"\b(?:19|20)\d{2}\b", " ", scan)
    stray = []
    for tok in re.findall(r"\d+(?:\.\d+)?", scan):
        if len(tok.replace(".", "")) <= 1:
            continue
        if tok in allowed:
            continue
        stray.append(tok)
    if stray:
        print("STRAY NUMBERS (not bound to any artifact): %s" % sorted(set(stray)))
        print("  -> a number in the prose that no program emitted; refusing to write the paper.")
        return None, None

    body = reflow(body)
    if len(entries) < REF_FLOOR:
        print("REFERENCE FLOOR NOT MET: %d < %d" % (len(entries), REF_FLOOR))
        return None, None
    return body, dict(entries=len(entries), cited=len(cited), bound=len(bound))


def main():
    body, info = generate()
    if body is None:
        return 1

    if "--check" in sys.argv[1:]:
        if not os.path.exists(OUT):
            print("ARTIFACT ABSENT: manuscript.md -- run without --check to write it")
            return 1
        stored = open(OUT, encoding="utf-8").read()
        if stored != body:
            print("STALE: manuscript.md does not match what this generator produces")
            print("       re-run without --check and re-read what changed")
            return 1
        print("MANUSCRIPT: IN SYNC (%d refs, %d cited, %d bound numbers)"
              % (info["entries"], info["cited"], info["bound"]))
        return 0

    open(OUT, "w", encoding="utf-8").write(body)
    print("manuscript.md written: %d characters" % len(body))
    print("  references: %d, all cited in the body (%d distinct numbers cited)"
          % (info["entries"], info["cited"]))
    print("  numbers bound to artifacts: %d" % info["bound"])
    print("  stray-number scan: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
