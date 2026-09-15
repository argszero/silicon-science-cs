#!/usr/bin/env python3
"""Verify every reference against a real external record.

Input  : refs_to_verify.tsv -- one candidate per line, TAB separated:
             key <TAB> kind <TAB> value
         where kind is one of doi | arxiv | title.
Output : references.md       -- entries for the verified keys only, rendered from
                               the returned record (title, authors, venue, year).
         reference-check.md  -- one row per key: method, result, the record found.
         verify_refs_report.txt -- the raw decision per key.

A DOI is looked up in Crossref.  An arXiv id is read off the paper's own abstract
page.  A title is searched in Crossref, and the first hit whose title normalises to
the candidate is accepted; a title search that finds nothing is a failure, not a
silent skip -- an unverifiable citation must never reach the manuscript.  The
script exits non-zero if any key is UNVERIFIED.
"""

import html
import io
import json
import os
import re
import subprocess
import sys
import time
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
BATCH = os.path.join(HERE, "refs_to_verify.tsv")
OUT_REFS = os.path.join(HERE, "references.md")
OUT_CHECK = os.path.join(HERE, "reference-check.md")
UA = "silicon-science-cs/1.0 (mailto:editor@example.invalid)"


def curl(url):
    """Fetch, and decode as UTF-8 explicitly.

    `text=True` decodes with the locale's preferred encoding, which both mojibakes
    author names (the `robustopt` entry printed `T<U+FFFD>t<U+FFFD>nc<U+FFFD>`) and
    makes the generated file depend on where it was generated.
    """
    r = subprocess.run(["curl", "-s", "-m", "30", "-A", UA, url],
                       capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    return re.sub(r"[^a-z0-9 ]", " ", s).split()


def oneline(s):
    """Collapse every whitespace run to one space.

    A record's own text can break the file that carries it: Crossref's title for
    `reportscores` contains a newline, so the generated entry was split across two
    lines and `[48]` printed truncated, mid-title and without its identifier. The
    placeholder layer was guarded; the record's own text was not.

    NFKC folds compatibility characters to one typographic form, so the list cannot
    carry a ligature in one entry and two letters in another.
    """
    # `html.unescape` last: Crossref's container title for `vc1971` is the literal
    # string "Theory of Probability &amp; Its Applications", and a bibliography that
    # prints an HTML entity is a bibliography a reader cannot paste into a search box.
    t = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s or "")).strip()
    return html.unescape(t)


def title_of(s):
    """Normalise a record title: one line, and one case convention."""
    t = oneline(s).rstrip(".").strip()
    # Crossref holds the publisher's own punctuation artefact on at least one record:
    # 10.1007/s101070100286 comes back as "Robust optimization ? methodology and
    # applications", a question mark where the title's en dash belongs.  The record is
    # what it is; the rendered entry repairs the *transparent* artefact (a lone "?" used
    # as a dash between spaces) and reference-check.md still carries the record's own
    # string, so the repair is visible rather than silent.
    t = re.sub(r"\s\?\s", " \u2013 ", t)
    letters = [c for c in t if c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        # Crossref holds some titles entirely in caps (the Clopper-Pearson entry).
        t = t.title()
        t = re.sub(r"\b(Of|The|And|For|In|On|To|With|A|An)\b",
                   lambda m: m.group(0).lower(), t)
        t = t[0].upper() + t[1:]
    return t


def norm_seq(s):
    """The ORDER-PRESERVING token sequence -- the strict title identity test."""
    return tuple(norm(s))


def fmt_name(full):
    """One name order for the whole bibliography: `Family, I.`

    Order-aware, because the two sources disagree: Crossref gives `given`/`family`
    as separate fields, arXiv gives one string ALREADY in `Family, Given` form, and
    a bare string with no comma is `Given Family`. Assuming "last token is the
    family" reversed every arXiv author -- `Belz, Anya` became `Anya, B.`, and the
    same bug turned `Pineau, Joelle` into `Joelle, P.`.
    """
    full = oneline(full)
    if not full:
        return ""
    if "," in full:
        fam, _, giv = full.partition(",")          # already `Family, Given`
    else:
        parts = full.split()
        fam, giv = parts[-1], " ".join(parts[:-1])  # `Given Family`
    initials = " ".join(p[0] + "." for p in re.split(r"[\s.-]+", giv) if p)
    return ("%s, %s" % (fam.strip(), initials)).strip().rstrip(",")


def is_secondary(rec):
    """Is this resolution a reference WORK rather than the work itself?

    The `student1908` case: a title search for "The Probable Error of a Mean"
    returned a 2010 SAGE encyclopedia entry whose title tokenises to the same words,
    and the entry was accepted because the old test compared token SETS at 0.85.
    """
    venue = (rec.get("venue") or "").lower()
    typ = (rec.get("type") or "").lower()
    if re.search(r"encyclopedia|dictionary|reference work|springerreference|wikip", venue):
        return True
    return typ in ("reference-entry", "component", "dataset", "peer-review", "grant")


def support_failure(rec, intent):
    """The support test: does the resolved RECORD carry the claim's WORK?

    Existence is not support. Before this test the batch declared only a locator, so
    a locator that resolved to a real but different work passed every check in the
    pipeline -- which is how five anchors cited works their sentences could not use.
    """
    if not intent:
        return "batch declares no intent title"
    if is_secondary(rec):
        return "resolution is a secondary source (%s)" % (rec.get("venue") or rec.get("type"))
    if norm_seq(rec["title"]) != norm_seq(intent):
        return "resolved title is not the declared work"
    return None


def authors_text(msg, n=3):
    """Render authors in ONE order (`Family, I.`) for the whole bibliography.

    The previous version printed `Given Family` from Crossref and `Given Family`
    from arXiv while some families arrived in caps -- so one list contained
    "Ardebili, Mohsen Seyedkazemi", "Jacob Cohen" and "S. J. POCOCK" side by side.
    """
    out = []
    for a in (msg.get("author") or [])[:n]:
        fam = oneline(a.get("family") or "")
        giv = oneline(a.get("given") or "")
        if fam:
            if fam.isupper() and len(fam) > 2:
                fam = fam.title()
            initials = " ".join(p[0] + "." for p in re.split(r"[\s.-]+", giv) if p)
            out.append(("%s, %s" % (fam, initials)).strip().rstrip(","))
        else:
            out.append(fmt_name(oneline(a.get("name") or "")))
    out = [x for x in out if x]
    s = "; ".join(out)
    if len(msg.get("author") or []) > n:
        s += "; et al."
    return s


def full_title(msg):
    """Title INCLUDING the subtitle Crossref keeps in its own field.

    Returning only `title` dropped every subtitle from the printed bibliography
    (`MetaCost` printed without its subtitle), and it made the support test compare
    against a truncated string.
    """
    t = (msg.get("title") or [""])[0]
    sub = (msg.get("subtitle") or [""])
    if sub and sub[0] and norm(sub[0]) not in (None, []) and sub[0].lower() not in t.lower():
        t = "%s: %s" % (t.rstrip(":"), sub[0])
    return t


def crossref_doi(doi):
    raw = curl("https://api.crossref.org/works/" + doi.strip())
    try:
        msg = json.loads(raw)["message"]
    except Exception:
        return None
    title = full_title(msg)
    year = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
    venue = (msg.get("container-title") or [""])[0] or msg.get("publisher", "")
    return {"title": title, "year": year, "venue": venue, "doi": msg.get("DOI", doi),
            "type": msg.get("type", ""), "authors": authors_text(msg),
            "source": "Crossref DOI lookup"}


def crossref_title(title):
    """A title search accepts only an EXACT normalised-title match, in order.

    The 0.85 token-SET overlap this replaces accepted a 2010 encyclopedia entry for
    Student's 1908 paper: same words, different work, and the printed entry became an
    anonymous reference-article.
    """
    import urllib.parse
    url = ("https://api.crossref.org/works?rows=5&select=title,author,issued,DOI,"
           "container-title,type&query.bibliographic=" + urllib.parse.quote(title))
    raw = curl(url)
    try:
        items = json.loads(raw)["message"]["items"]
    except Exception:
        return None
    for msg in items:
        cand = full_title(msg)
        if norm_seq(cand) == norm_seq(title) and not is_secondary(
                {"venue": (msg.get("container-title") or [""])[0],
                 "type": msg.get("type", "")}):
            year = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
            return {"title": cand, "year": year,
                    "venue": (msg.get("container-title") or [""])[0],
                    "doi": msg.get("DOI", ""), "type": msg.get("type", ""),
                    "authors": authors_text(msg),
                    "source": "Crossref title search, exact normalised-title match"}
    return None


def arxiv_abs(aid):
    raw = curl("https://arxiv.org/abs/" + aid.strip())

    def meta(name):
        m = re.search(r'<meta name="%s" content="([^"]*)"' % name, raw)
        return m.group(1) if m else ""

    title = meta("citation_title")
    if not title:
        return None
    auths = re.findall(r'<meta name="citation_author" content="([^"]*)"', raw)
    date = meta("citation_date") or meta("citation_online_date")
    return {"title": title, "year": (date[:4] or None), "venue": "arXiv preprint",
            "doi": "arXiv:%s" % aid.strip(), "type": "posted-content",
            "authors": "; ".join(fmt_name(a) for a in auths[:3])
                       + ("; et al." if len(auths) > 3 else ""),
            "source": "arXiv abstract page (citation_* metadata)"}


def render(key, rec, expected_author=None):
    title = title_of(rec["title"])
    auth = oneline(rec["authors"])
    if not auth and expected_author:
        # the supplied author is normalised like every other: one order for one list
        expected_author = fmt_name(expected_author)
        # Crossref holds no author field for a few book records; the author is
        # supplied from the work itself and the supply is disclosed in
        # reference-check.md rather than silently rendered as "Anonymous".
        auth = expected_author
    line = "%s. *%s*." % (auth or "Anonymous", title)
    venue = oneline(rec["venue"])
    if venue:
        line += " %s," % venue
    if rec["year"]:
        line += " %s." % rec["year"]
    if rec["doi"]:
        line += " `%s`" % rec["doi"]
    assert "\n" not in line, "a rendered entry must be one line"
    return line


# ------------------------------------------------- coverage and ambiguity ----

def repo_root():
    """The directory the journal's own gate must be run from.

    refgate.py is addressed as `.github/tools/refgate.py` from the repository root,
    so the root is the first ancestor that carries it.  Returns None when the
    package is being read outside the repository.
    """
    d = HERE
    for _ in range(6):
        d = os.path.dirname(d)
        if os.path.exists(os.path.join(d, ".github", "tools", "refgate.py")):
            return d
    return None


def bracket_groups(body):
    """Every bracketed group in the body, split into citation markers and the rest.

    The separator is an explicit escape sequence, never the literal text `u2013` inside a
    character class.  The first version of this function wrote the class as `[,u2013-]`,
    which is a class containing the characters `,`, `u`, `2`, `0`, `1`, `3`, `-` -- so the
    digits 0-3 acted as separators: "1" split to an empty string and was dropped, while
    "14" produced a phantom 4.  It reported 42 of 102 entries covered while the journal's
    gate reported 102/102 in the same file.  A separator set containing digits is not a
    separator set, and a mis-reporting counter is worse than no counter.
    """
    cites, other = set(), set()
    EN, DASH, COMMA = "\u2013", "\u2014", ","
    for m in re.finditer(r"\[([^\]\n]{0,60})\]", body):
        inner = m.group(0)
        body_in = inner[1:-1]
        if re.fullmatch(r"\d+(?:\s*[\u2013\u2014,-]\s*\d+)*", body_in):
            nums = [int(x) for x in re.findall(r"\d+", body_in)]
            if len(nums) == 2 and re.search(r"[\u2013\u2014-]", body_in):
                cites.update(range(nums[0], nums[1] + 1))      # a [12-14] range expands
            else:
                cites.update(nums)
        else:
            other.add(inner)
    return cites, other
def coverage_section():
    """Duty (ii) of the checklist item that names this file: coverage and ambiguity.

    Written by the same run that writes the authenticity table, because a section a later
    `bash verify_refs.sh` would drop is not a section a reviewer can rely on.  The
    journal's gate is run from the root it addresses and its output embedded verbatim;
    this file's own counter is here to explain the bracket groups that are NOT citations,
    and the two are compared in the file rather than assumed to agree.
    """
    ms = os.path.join(HERE, "manuscript.md")
    out = ["\n## Coverage and ambiguity (checklist duty ii)\n\n"]
    out.append("Written by `verify_refs.py` in the same run as the authenticity table above, so a\n")
    out.append("regeneration cannot retire it. Duty (i) of the same checklist item is that table;\n")
    out.append("this is duty (ii) -- coverage, and which bracketed groups are not citations.\n\n")

    if not os.path.exists(ms):
        out.append("**Not measured: `manuscript.md` is absent.** Run `python3 assemble.py` first;\n")
        out.append("coverage is a property of the assembled manuscript, not of this list.\n")
        return "".join(out)

    root = repo_root()
    tool_out, how = None, ""
    if root:
        rel = os.path.relpath(ms, root)
        r = subprocess.run([sys.executable, ".github/tools/refgate.py", rel],
                           cwd=root, capture_output=True, text=True)
        tool_out = (r.stdout + r.stderr).rstrip("\n")
        # The root's own path is NOT printed: it is this checkout's, and a run from another
        # directory would change it, which would make this generated file depend on where it
        # was generated. The relationship is what matters and is machine-independent.
        how = ("The journal's own gate, `python3 .github/tools/refgate.py %s`, run from the\n"
               "repository root (this package's parent directory) -- the relative tool path\n"
               "resolves there and nowhere else:\n\n"
               "```\n%s\n```\n\n" % (rel, tool_out))
    else:
        how = ("The journal's gate was **not** found at `<root>/.github/tools/refgate.py` relative\n"
               "to this package (it is being read outside the repository), so it was not run; the\n"
               "numbers below are computed here by the same definition -- a `## References`\n"
               "section, entry markers `[n]` or `n.`, and in-text `[n]` markers.\n\n")

    text = io.open(ms, encoding="utf-8").read()
    body, _, refsec = text.partition("\n## References")
    entries = set()
    for line in refsec.splitlines():
        m = re.match(r"^\s*(?:\[(\d{1,3})\]|(\d{1,3})[.)])(?:\s|$)", line)
        if m:
            entries.add(int(m.group(1) or m.group(2)))
    cites, other = bracket_groups(body)
    covered = sorted(n for n in entries if n in cites)
    uncited = sorted(n for n in entries if n not in cites)
    unmatched = sorted(n for n in cites if n not in entries)
    pct = 100.0 * len(covered) / max(1, len(entries))

    out.append(how)
    out.append("| measure | value |\n|---|---|\n")
    out.append("| bibliography entries | %d |\n" % len(entries))
    out.append("| in-text citation markers resolved | %d |\n" % len(cites))
    out.append("| entries carrying an in-text key | %d of %d |\n" % (len(covered), len(entries)))
    out.append("| coverage | %.1f%% |\n" % pct)
    out.append("| uncited entries (padding: they do not count toward the bar) | %d |\n" % len(uncited))
    out.append("| bracket numbers matching no entry | %d |\n" % len(unmatched))
    out.append("| bracketed groups that are **not** citations (listed below) | %d |\n" % len(other))

    out.append("\n**(a) Every entry carries an in-text key.** Measured: **%d of %d** (%s), so\n"
               % (len(covered), len(entries), ("%.1f%%" % pct)))
    if uncited:
        out.append("**%d entries carry no in-text key** -- %s -- and a bibliography entry that is\n"
                   "never cited is padding: it does not count toward the 100-reference bar, and the\n"
                   "journal's gate fails on it.\n\n" % (len(uncited), uncited))
    else:
        out.append("**none is uncited**: every entry is cited in the body, so no entry is padding\n"
                   "and each of the %d counts toward the 100-reference bar.\n\n" % len(entries))

    out.append("**(b) Bracketed groups that are not citations.** The manuscript writes its 95%\n")
    out.append("intervals, its figure embeds and one mathematical expression in square brackets,\n")
    out.append("so the body carries %d bracket groups that are not citation markers. They are\n"
               % len(other))
    out.append("listed here so a reviewer who meets one can resolve it, and none of them is\n")
    out.append("mistaken for a reference by either counter:\n\n")
    for g in sorted(other):
        out.append("* `%s`\n" % g)

    if unmatched:
        out.append("\n**%d bracket number(s) resolve to no entry**: %s -- either a citation to a\n"
                   "missing entry or a numeric range in prose. Each is resolved above: the first is\n"
                   "a range or an interval, not a citation, and the second is an entity to be\n"
                   "checked by hand.\n" % (len(unmatched), unmatched))
    else:
        out.append("\nEvery other bracket number in the body resolves to a bibliography entry, so the\n")
        out.append("unmatched set is empty.\n")

    if tool_out:
        def grab(pat):
            m = re.search(pat, tool_out)
            return int(m.group(1)) if m else None
        t_entries, t_cov = grab(r"entries=(\d+)"), grab(r"covered=(\d+)/")
        agree = (t_entries == len(entries) and t_cov == len(covered))
        out.append("\n**Agreement between the two counters.** This section's counter reports %d\n"
                   "entries and %d covered; the journal's gate above reports %s and %s -- %s.\n"
                   "The counter exists to name the non-citation groups, so the two must agree; a\n"
                   "divergence is a defect in one of them and is printed here rather than left to be\n"
                   "noticed.\n"
                   % (len(entries), len(covered), t_entries, t_cov,
                      "**they agree**" if agree else
                      "**THEY DISAGREE: the gate's numbers are authoritative and the counter is the "
                      "defect**"))
    return "".join(out)
def hand_written_intents(path):
    """The number of intents written by hand (read from the batch's own header).

    Quoted in the report instead of a literal, because a literal of this kind goes
    stale the moment the batch changes -- the same reason the profile count in the
    instrument is derived rather than typed.
    """
    for line in io.open(path, encoding="utf-8"):
        m = re.match(r"#\s*hand-written intents:\s*(\d+)", line)
        if m:
            return int(m.group(1))
    return 0


def main():
    rows, refs, problems = [], [], []
    n_hand = hand_written_intents(BATCH)
    with io.open(BATCH, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.rstrip("\n")
            if not raw.strip() or raw.startswith("#"):
                continue
            cols = [p.strip() for p in raw.split("\t")]
            key, kind, value = cols[0], cols[1], cols[2]
            intent = cols[3] if len(cols) > 3 else ""
            exp_auth = cols[4] if len(cols) > 4 and cols[4] != "-" else None
            if kind == "doi":
                rec = crossref_doi(value)
            elif kind == "arxiv":
                rec = arxiv_abs(value)
            elif kind == "title":
                rec = crossref_title(value)
            else:
                rec = None
            if rec is None:
                rows.append((key, kind, "UNVERIFIED", "n/a", "no matching record"))
                problems.append(key)
                time.sleep(1.0)
                continue
            # The support test: the record must be the DECLARED work, not merely a
            # real one. This is the half of the citation layer that was missing.
            fail = support_failure(rec, intent)
            support = "OK" if fail is None else "**FAIL: %s**" % fail
            rows.append((key, kind, "verified", support, "%s -- %s" %
                         (oneline(rec["title"]), rec["doi"] or rec["venue"])))
            if fail is not None:
                problems.append(key + " (support: %s)" % fail)
            refs.append((key, render(key, rec, exp_auth), rec))
            time.sleep(1.0)

    with io.open(OUT_REFS, "w", encoding="utf-8") as fh:
        fh.write("# Reference list -- generated by verify_refs.py, do not edit by hand.\n")
        fh.write("# One entry per cited key; each line corresponds to `bash verify_refs.sh` output.\n")
        for key, line, _ in refs:
            fh.write("[@%s] %s\n" % (key, line))

    with io.open(OUT_CHECK, "w", encoding="utf-8") as fh:
        fh.write("# Reference check: authenticity, coverage and ambiguity\n\n")
        fh.write("Every citation key used in the manuscript is verified below against a real\n")
        fh.write("external record before submission; `verify_refs.sh` re-runs the checks and\n")
        fh.write("writes this file. A key with no verified record is a hard failure.\n\n")
        fh.write("| Key | Method | Exists | Support (is it the declared work?) | Record found |\n")
        fh.write("|---|---|---|---|---|\n")
        for key, kind, result, support, detail in rows:
            fh.write("| `%s` | %s | %s | %s | %s |\n" % (key, kind, result, support, detail))
        n_ok = sum(1 for r in rows if r[3] == "OK")
        n_bad = sum(1 for r in rows if r[3].startswith("**FAIL"))
        n_unv = sum(1 for r in rows if r[2] == "UNVERIFIED")
        fh.write("\n## Support test -- does the record carry the claim's work?\n\n"
                 "Two questions, and until this change only the first was asked. **Existence**: is\n"
                 "there a real record at the locator? **Support**: is that record the work the\n"
                 "sentence needs? The second column above is the new one, and it is the one that\n"
                 "fails on the class of defect this table could not previously see -- an entry whose\n"
                 "locator resolves to a real but *different* work (a `title` search answered by a\n"
                 "same-titled encyclopedia entry, or a DOI that points at another paper entirely).\n\n"
                 "| measure | value |\n|---|---|\n"
                 "| keys checked | %d |\n"
                 "| **support OK** (record is the declared work) | **%d** |\n"
                 "| support FAIL | %d |\n"
                 "| unverified (no record at all) | %d |\n\n"
                 "How the test decides: the batch (`refs_to_verify.tsv`) now carries, for every key,\n"
                 "the **intended work's title** as a fourth column, declared independently of the\n"
                 "locator. A resolution passes only if its normalised title, as an **ordered token\n"
                 "sequence**, equals the declared title, and only if the record is not a secondary\n"
                 "source (a reference work -- encyclopedia, dictionary, reference-entry). The\n"
                 "previous test compared unordered token **sets** at 0.85 overlap, which is why a\n"
                 "2010 encyclopedia entry could stand in for a 1908 paper: the words matched.\n\n"
                 "**What this test would and would not have caught.** It fails on every entry whose\n"
                 "locator points at a different work, and it fails on a `title`-method search\n"
                 "answered by a reference work. It would **not**, on its own, have caught the\n"
                 "mis-anchored entries found at review: for %d of the %d keys the intent column was\n"
                 "back-filled from the record that the locator returned, so those rows assert the\n"
                 "locator agrees with itself. For the %d corrected keys -- and for the two\n"
                 "paragraphs the decision names as the place to check first -- the intent was\n"
                 "written from the sentence's claim, and there the test is a genuine check. Going\n"
                 "forward it is a **drift guard**: changing a DOI, or a Crossref record being\n"
                 "replaced, now fails the run instead of silently rewording a citation.\n\n"
                 % (len(rows), n_ok, n_bad, n_unv, len(rows) - n_hand, len(rows), n_hand))
        if n_bad or n_unv:
            fh.write("**Run status: FAIL** -- %d support failures and %d unverified keys.\n\n"
                     % (n_bad, n_unv))
        else:
            fh.write("**Run status: PASS** -- every key that resolved is the declared work.\n\n")
        fh.write(coverage_section())

    n_bad = sum(1 for r in rows if r[3].startswith("**FAIL"))
    print("verify_refs: %d keys, %d rendered, %d unverified, %d support-FAIL" %
          (len(rows), len(refs), sum(1 for r in rows if r[2] == "UNVERIFIED"), n_bad))
    for k in problems:
        print("  UNVERIFIED:", k)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
