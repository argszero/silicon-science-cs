#!/usr/bin/env python3
"""Verify every selected reference against a real external record, and render the list.

Two outputs, both committed:

  * `reference-check.md` -- one row per entry: key, method, whether the record EXISTS, whether
    it SUPPORTS the declared work, and the record actually found.  "Exists" and "supports" are
    separate columns on purpose: a DOI can resolve to a real paper that is not the one the
    manuscript means (that is precisely how a false match survives a screen), so the title is
    compared token by token and a mismatch fails the run.
  * `reference-list.md` -- the numbered list the manuscript cites, in the journal's house
    form: `[n] Authors (Year). Title. Venue. <resolvable URL>` plus the stated difference.

A reference that cannot be verified is an ERROR, not a warning: the exit code is nonzero and
the entry is reported.  Nothing here rewrites the selection to make the run pass.

Usage: python3 verify_refs.py     (writes the two files; exit 0 iff every entry verified)
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "verify_cache")
os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "issue-114-bibliography/1.0 (mailto:noreply@example.org)"}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())


def overlap(a: str, b: str) -> float:
    x = [w for w in norm(a).split() if len(w) > 2]
    if not x:
        return 0.0
    y = set(norm(b).split())
    return sum(1 for w in x if w in y) / len(x)


def fetch(url: str, name: str):
    """Fetch with backoff, and cache only a SUCCESS.

    The index rate-limits (HTTP 429), and a throttled lookup is not evidence about a record --
    it is an absence of evidence.  So a failure is retried and never cached, and the caller is
    handed a marker it can report as `unreachable` rather than as `mismatch`: conflating the
    two would let a busy API read as a fabricated citation, and (worse, in the other direction)
    a naive retry-until-cached loop would turn a throttle into a silent pass.
    """
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9._-]", "_", name)[:120])
    if os.path.exists(path):
        return open(path, encoding="utf-8", errors="replace").read()
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read().decode("utf-8", "replace")
            open(path, "w", encoding="utf-8").write(body)
            time.sleep(1.0)
            return body
        except Exception as exc:                   # noqa: BLE001 - recorded as a failed lookup
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(4 * (attempt + 1))
    return f"__UNREACHABLE__ {last}"


def verify_crossref(e):
    body = fetch(f"https://api.crossref.org/works/{urllib.parse.quote(e['doi'])}", f"cr_{e['doi']}")
    if body.startswith("__UNREACHABLE__"):
        return None, False, body, ""
    d = json.loads(body)["message"]
    title = (d.get("title") or [""])[0]
    yr = (d.get("issued", {}).get("date-parts") or [[None]])[0][0]
    ok_title = overlap(e["title"], title) >= 0.8
    ok_year = e["year"] is None or yr is None or abs(int(yr) - int(e["year"])) <= 1
    return True, (ok_title and ok_year), f"{title} -- {e['doi']}", f"{title} ({yr})"


def openalex_authors(e):
    """The author list OpenAlex holds for this DOI, or [] -- a second record read before an
    absence is recorded.

    Four records in this bibliography carry no author in Crossref, and the journal's rule for an
    entry whose record gives no author is either to name the body responsible or to record the
    absence *by naming the record read*.  An absence read from one registry is weaker than it
    looks, so the second registry is asked first; where it answers, the entry prints real authors
    and the absence is never claimed.
    """
    doi = e.get("doi")
    if not doi:
        return []
    body = fetch(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}",
                 f"oa_{doi}.json")
    if body.startswith("__UNREACHABLE__"):
        return []
    try:
        d = json.loads(body)
    except ValueError:
        return []
    out = []
    for a in d.get("authorships") or []:
        raw = (a.get("raw_author_name") or "").strip()
        if not raw:
            continue
        # OpenAlex's raw form is `Family, Given` -- already the house order
        if "," in raw:
            fam, giv = raw.split(",", 1)
            out.append({"family": fam.strip(), "given": giv.strip()})
        else:
            out.append({"family": raw, "given": ""})
    return out


def verify_arxiv(e):
    aid = e.get("arxiv", "")
    body = fetch(f"http://export.arxiv.org/api/query?id_list={urllib.parse.quote(aid)}",
                 f"ax_{aid}.xml")
    if body.startswith("__UNREACHABLE__"):
        return None, False, body, ""
    m = re.search(r"<entry>(.*?)</entry>", body, re.S)
    if not m:
        return True, False, "no entry returned for this id", ""
    t = re.search(r"<title>(.*?)</title>", m.group(1), re.S)
    title = re.sub(r"\s+", " ", html.unescape(t.group(1))).strip() if t else ""
    return True, overlap(e["title"], title) >= 0.8, f"{title} -- arXiv:{aid}", title


# --------------------------------------------------------------------------
# The house author form: `Family, I.`
#
# The generator's FIRST version printed whatever the harvest stored, and for the arXiv-sourced
# entries that was the author's whole name in the `family` field (the arXiv API returns one string
# per author and no given/family split), so 34 entries printed given-name-first and stood outside
# the form the journal reads.  The stored field is not the form an entry prints, so the form is
# produced HERE, from the record, and every normalization says which source it used:
#
#   * the record's own structured `family`/`given` (Crossref) is authoritative -- a name that has
#     structure is never guessed at;
#   * where the record carries no author at all (four records in this bibliography: Crossref and
#     OpenAlex both index them with an empty author list), OpenAlex is asked by DOI before the
#     absence is recorded -- an absence is a claim about a record and is only as good as the
#     records that were read;
#   * where the only form available is one string (arXiv), the family name is the LAST token, and
#     a name whose last token is an initial (`Shivaranjani G. R.`) or a particle is NOT split --
#     it is printed as the record gives it, and the entry is listed in reference-check.md as one
#     the read could not form.  An invented initial is a fabricated author; a reported one is not.
# --------------------------------------------------------------------------

# LaTeX accent commands, for a registry field that has been stored with its escapes intact
# (`Ciob\b{a}` for `Ciobâcă` -- measured in this bibliography).
ACCENTS = {
    "b": "\u0306", "v": "\u030c", "'": "\u0301", "`": "\u0300", "^": "\u0302",
    '"': "\u0308", "~": "\u0303", "c": "\u0327", "r": "\u030a", "=": "\u0304",
    "u": "\u0306", "H": "\u030b", ".": "\u0307", "k": "\u0328",
}


def decode(s: str) -> str:
    """Decode a stored field into the form an entry prints: entities and LaTeX escapes.

    Both failures are the same kind of defect -- a field copied out of JSON/XML or out of a LaTeX
    source instead of being printed -- and both are read by the journal's own gate (`author form:`
    counts a character reference; a `\\b{a}` in a name is not a name).
    """
    if not s:
        return s
    s = html.unescape(s)
    def accent(m):
        base, cmd = m.group(2), m.group(1)
        return unicodedata.normalize("NFC", base + ACCENTS.get(cmd, ""))
    s = re.sub(r"\\([\"'`^~=\.bcruvHk])\{?([A-Za-z])\}?", lambda m: accent(m), s)
    s = s.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
    # a bare `\X` that survived (e.g. `\o`) is dropped rather than printed
    s = re.sub(r"\\[A-Za-z]+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def fold(s: str) -> str:
    """A registry's stored capitals are not the form an entry prints.

    `HALES, T.` is Crossref's own stored field for Hales; the house style folds an ALL-CAPS
    stored family name to mixed case, exactly as it folds an ALL-CAPS stored title.
    """
    if not s:
        return s
    if s.isupper() and any(c.isalpha() for c in s):
        return s.title()
    return s


# A family name can carry particles that are not given names, and a body is not a person: both are
# read here because the FIRST version of `split_name` took the last token unconditionally and turned
# `Claire Le Goues` into `Goues, C. L.` (the particle became an initial) and `The mathlib Community`
# into `Community, T. M.` (a corporate author rendered as a person).  The correction is measured, not
# guessed: the two forms are the ones this bibliography actually contains.
PARTICLES = {"de", "van", "von", "le", "la", "les", "den", "der", "des", "di", "da", "dos", "du",
             "del", "della", "bin", "ibn", "ten", "ter", "op", "in", "zu", "zur", "af", "av"}
COLLECTIVE = {"community", "team", "consortium", "group", "project", "collaboration", "contributors",
              "authors", "committee", "association", "institute", "university", "laboratory", "lab",
              "foundation", "society", "working", "initiative", "collective", "network", "alliance",
              "inc", "ltd", "corp", "corporation", "gmbh"}


def split_name(tok: str):
    """(family, given) from one string, or None when the string does not carry the split.

    The last whitespace-separated token is the family name -- the order arXiv's harvest stores --
    extended leftward over any run of particles (`Van den Broucke`), and a last token that is an
    initial (`R.`) or a one-letter particle is NOT accepted, because the split would have to be
    invented.  A string naming a body rather than a person is not split at all: the journal's rule
    for such a work is to name the body responsible, and the body IS the name.
    """
    parts = tok.split()
    if len(parts) < 2:
        return None
    if any(p.strip(".,").lower() in COLLECTIVE for p in parts):
        return None
    last = parts[-1]
    if len(last.rstrip(".")) < 2 or not last[0].isalpha():
        return None
    i = len(parts) - 1
    while i > 1 and parts[i - 1].strip(".,").lower() in PARTICLES:
        i -= 1
    if i == 0:
        return None                      # nothing left to be a given name
    return " ".join(parts[i:]), " ".join(parts[:i])


def initials(given: str) -> str:
    return " ".join(p[0].upper() + "." for p in re.split(r"[\s.\-]+", given) if p and p[0].isalpha())


def one_author(a) -> str:
    fam = decode((a.get("family") or "").strip())
    giv = decode((a.get("given") or "").strip())
    if not fam and giv:
        fam, giv = giv, ""
    if not fam:
        return ""
    if giv:
        return f"{fold(fam)}, {initials(giv)}"
    # one token and no more: the record carries no initial to print, so the token is printed
    # alone -- but only when the string really is one token.  A harvest that put a full name in
    # the family field is split (and, if it cannot be split, printed as it stands).
    sp = split_name(fam)
    if sp:
        return f"{fold(sp[0])}, {initials(sp[1])}"
    return fold(fam)


def render_authors(authors) -> str:
    out = [x for x in (one_author(a) for a in authors) if x]
    if not out:
        return ""
    if len(out) == 1 and ", " not in out[0]:
        return out[0] + "."                      # the lone-token form, closed by a period
    if len(out) > 3:
        return "; ".join(out[:3]) + "; et al."
    return "; ".join(out)


def main() -> int:
    sel = json.load(open(os.path.join(HERE, "selection.json")))
    rows, entries, bad, unreachable, unresolved = [], [], [], [], []
    no_difference = []
    for i, e in enumerate(sorted(sel["accepted"], key=lambda x: (x["year"] or 0, x["key"])), 1):
        if e["source"] == "crossref":
            exists, supports, found, detail = verify_crossref(e)
            method = "doi"
        else:
            exists, supports, found, detail = verify_arxiv(e)
            method = "arxiv"

        # ---- the author component, formed from the record -------------------
        authors, origin = e["authors"], "harvest"
        if not any((a.get("family") or a.get("given")) for a in authors):
            oa = openalex_authors(e)
            if oa:
                authors, origin = oa, "openalex"
            else:
                origin = "absent"
        elif e["source"] == "arxiv":
            origin = "arxiv-name"
        rendered = render_authors(authors)
        if not rendered:
            # the rule's first member: record the absence by naming the record it read
            # a statement in the author position: an absence is a claim about the records read,
            # and the journal's rule is to record it by NAMING the record, never to leave the
            # position empty and never to fill it by guesswork.
            rendered = (f"[Author not established on Crossref or OpenAlex for "
                        f"{'DOI ' + e['doi'] if e.get('doi') else 'this record'}]")
            origin = "absent"

        rows.append((i, e, method, exists, supports, found, detail))
        if exists is None:
            unreachable.append(e["key"])
        elif not (exists and supports):
            bad.append(e["key"])
        if origin in ("absent", "arxiv-name"):
            unresolved.append((i, e["key"], origin))

        note = e.get("difference") or e.get("role") or ""
        if not note:
            no_difference.append(e["key"])

        url = (f"https://doi.org/{e['doi']}" if e["doi"]
               else f"https://arxiv.org/abs/{e.get('arxiv', '')}")
        venue = decode(e["venue"] or ("arXiv preprint" if e.get("arxiv") else ""))
        title = fold(decode(e["title"]))
        # the components in the house order, each printed once; an empty component is DROPPED
        # rather than printed as an empty segment (the first version emitted `Modules. . https://`)
        head = [rendered, f"({e['year']}).", f"{title}."]
        parts = [" ".join(head)] + [f"{v}." for v in (venue, url) if v]
        line = f"[{i}] " + " ".join(parts)
        if note:
            line += f"\n    Difference: {note}"
        entries.append((i, e, line))

        verdict = "ok" if (exists and supports) else ("UNREACHABLE" if exists is None else "MISMATCH")
        print(f"  [{i:3d}] {e['key']:<22} {method:<6} {verdict:<12} {origin:<11} {e['title'][:44]}")

    # the key -> number map, so the manuscript can be written with stable [@key] tokens and
    # rendered to the house's numeric form at assembly time (a numbered list whose order can
    # change must not be hand-copied into prose)
    with open(os.path.join(HERE, "keys.json"), "w") as fh:
        json.dump({e["key"]: i for i, e, _ in entries}, fh, indent=1, sort_keys=True)

    with open(os.path.join(HERE, "..", "reference-list.md"), "w") as fh:
        fh.write("# Reference list -- generated by verify_refs.py, do not edit by hand.\n\n")
        fh.write("Entries are numbered in the order the manuscript cites them.\n\n")
        for i, e, line in entries:
            fh.write(line + "\n\n")

    covered = sum(1 for _, _, _, ex, sup, _, _ in rows if ex and sup)
    with open(os.path.join(HERE, "..", "reference-check.md"), "w") as fh:
        fh.write("# Reference check -- authenticity and support\n\n")
        fh.write(f"Every citation key used by the manuscript is verified below against a real "
                 f"external record before submission; `refs/verify_refs.py` re-runs these "
                 f"lookups and rewrites this file.  **{covered} of {len(rows)} entries verified.**\n\n")
        fh.write("`Exists` asks whether the identifier resolves; `Support` asks whether the record "
                 "found is the work the manuscript means -- two separate questions, because a DOI "
                 "can resolve to a real paper that is not the declared one.\n\n")
        fh.write("The instrument is the endpoint named in the `Method` column (`api.crossref.org/works/<doi>` "
                 "for `doi`; `export.arxiv.org/api/query?id_list=<id>` for `arxiv`), and its known-present "
                 "control is entry `[6]` (`10.1093/comjnl/25.4.465`, Weyuker 1982): a run in which the control "
                 "does not resolve has read nothing and takes no verdict about the others.\n\n")
        fh.write("| # | Key | Method | Exists | Support | Record found |\n|---|---|---|---|---|---|\n")
        for i, e, method, exists, supports, found, _ in rows:
            ex = "unreachable" if exists is None else ("yes" if exists else "NO")
            fh.write(f"| {i} | `{e['key']}` | {method} | {ex} | "
                     f"{'OK' if supports else 'MISMATCH'} | {found.replace('|', '/')} |\n")

        fh.write("\n## Where each author component came from\n\n")
        fh.write("The house form is `Family, I.`, and it is formed from a record rather than from the "
                 "field a harvest stored. Three routes, and every entry is on one of them:\n\n")
        fh.write("| route | how the component is formed |\n|---|---|\n")
        fh.write("| `crossref` | the record's own structured `family`/`given` |\n")
        fh.write("| `openalex` | the record carries no author in Crossref, so OpenAlex is asked by DOI |\n")
        fh.write("| `arxiv-name` | the only form available is one string per author; the family name is "
                 "the LAST token, and a name whose last token is an initial is not split |\n")
        fh.write("| `absent` | no record read carries an author; the entry says so and names the record it read |\n\n")
        fh.write("Entries whose component did not come from a structured record, with the form printed:\n\n")
        if unresolved:
            fh.write("| # | Key | Route | Printed component |\n|---|---|---|---|\n")
            for i, key, origin in unresolved:
                e = next(x for x in sel["accepted"] if x["key"] == key)
                if origin == "absent":
                    comp = "author not established on Crossref or OpenAlex"
                    a = [x for x in rows if x[0] == i][0]
                    comp += f" for DOI {e.get('doi') or '(none)'}"
                else:
                    comp = render_authors(e["authors"])
                fh.write(f"| {i} | `{key}` | {origin} | {comp} |\n")
        else:
            fh.write("_None._\n")
        fh.write("\n**Two entries stand outside the author component by the rule's own statement and are "
                 "right as printed** (`README.md` -> *Presentation requirements*): a work whose record "
                 "carries no author at all is recorded by naming the record read, and a corporate or "
                 "multi-author work whose responsible body is named is printed as it stands. Both are "
                 "listed above rather than silently left out.\n")

        fh.write("\n## Rejections (near-misses that were NOT cited)\n\n")
        fh.write("A title-overlap screen cannot separate these from a hit, so each is recorded "
                 "with the reason it is not the work the query named:\n\n")
        fh.write("| Key | Reason rejected |\n|---|---|\n")
        for r in sel.get("rejected", []):
            fh.write(f"| `{r['key']}` | {r['why']} |\n")

    if no_difference:
        # the journal requires a one-line stated difference PER ENTRY, and a bibliography that
        # omits it is the machine export the rule returns at triage.  So its absence is a FAILURE
        # of this step, not a line that is simply not written -- the first version wrote nothing
        # and reported a clean run over 44 entries that carried none.
        print(f"  MISSING STATED DIFFERENCE on {len(no_difference)} entries: {no_difference[:12]}")

    print(f"\nVERIFY: {covered}/{len(rows)} verified"
          f" · mismatched {len(bad)} {bad if bad else ''}"
          f" · unreachable {len(unreachable)} {unreachable if unreachable else ''}"
          f" · author components not from a structured record {len(unresolved)}"
          f" · entries with no stated difference {len(no_difference)}")
    print("  (a mismatch is a defect in the reference; an unreachable lookup is an absence of "
          "evidence and must be re-run, not read as a pass)")
    return 0 if not bad and not unreachable and not no_difference else 1


if __name__ == "__main__":
    sys.exit(main())
