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


DOUBLED_PERIOD = re.compile(r"\.\.")


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
    # The separator period belongs to the ENTRY, not to the name.  A name that already
    # carries its own final period -- an initial (`Wald, A.`) or the abbreviation
    # (`et al.`) -- must not receive a second one.  Measured on the head before this
    # condition: 55 of 102 entries printed `A..` and 45 printed `et al..`, 101 doubled
    # periods in all, while the name-ORDER change in this same function was being
    # verified.  The order was checked and the punctuation it produced was not, which is
    # why the property is now measured over the whole list (doubled_periods).
    name = auth or "Anonymous"
    line = "%s%s *%s*." % (name, "" if name.endswith(".") else ".", title)
    venue = oneline(rec["venue"])
    if venue:
        line += " %s," % venue
    if rec["year"]:
        line += " %s." % rec["year"]
    if rec["doi"]:
        line += " `%s`" % rec["doi"]
    assert "\n" not in line, "a rendered entry must be one line"
    return line


def doubled_periods(entries):
    """Every entry carrying two adjacent periods -- the WHOLE list, never a sample.

    A property of the renderer, so it is measured on the renderer's output.  Sampling
    the entries one happens to look at is exactly how a doubled period survived a round
    in which this same function's name ORDER was verified: the predicate that was
    checked was true, and the punctuation it produced was not read.  Returns
    `[(key, context)]`, one per occurrence.
    """
    out = []
    for key, line in entries:
        for m in DOUBLED_PERIOD.finditer(line):
            out.append((key, line[max(0, m.start() - 20):m.end() + 8]))
    return out


def punctuation_section(dbl, n_entries):
    """The rendered-punctuation block of reference-check.md, generated in the same run."""
    parts = [
        "## Rendered punctuation -- one period per separator, over the whole list\n\n",
        "Not a citation check but a **renderer** check, recorded here because this file is\n",
        "the carrier the citation layer defers to, and because the defect it measures\n",
        "shipped once: `render()` wrote the entry's separator period after a name that\n",
        "already ended in one, so `Wald, A.` rendered as `Wald, A..` and `... ; et al.` as\n",
        "`et al..`. Measured on the head that carried the defect: **101 doubled periods on\n",
        "101 of the 102 entries**, one per entry, in three forms -- a capital initial (55),\n",
        "the abbreviation `et al.` (45) and a lowercase initial (1, `Vaart, A. W. v. d..`).\n",
        "The same count was 47 on the head before the name-order change, all of them\n",
        "`et al..`. The whole list is measured; a sample is what missed it.\n\n",
        "| measure | value |\n|---|---|\n",
        "| entries rendered | %d |\n" % n_entries,
        "| entries carrying a doubled period | **%d** |\n" % len(set(k for k, _ in dbl)),
        "| doubled periods | **%d** |\n" % len(dbl),
    ]
    if dbl:
        parts.append("\n**FAIL** -- a name that already carries a period is being given a second one:\n\n")
        for key, ctx in dbl[:10]:
            parts.append("* `%s` -- `%s`\n" % (key, ctx))
    else:
        parts.append("\n**PASS** -- no entry in the rendered list carries two adjacent periods.\n")
    parts.append("\nThe condition lives in one place, `render()`: the separator period is written\n"
                 "only when the name does not already end in one (`name.endswith('.')`), which also\n"
                 "removes the `et al..` form that predates this revision. The count above is the\n"
                 "property, held over all %d entries.\n\n" % n_entries)
    return "".join(parts)


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
    r"""Every bracketed group in the body, split into citation markers and the rest.

    The separator is an explicit escape sequence, never the literal text `u2013` inside a
    character class.  The first version of this function wrote the class as `[,u2013-]`,
    which is a class containing the characters `,`, `u`, `2`, `0`, `1`, `3`, `-` -- so the
    digits 0-3 acted as separators: "1" split to an empty string and was dropped, while
    "14" produced a phantom 4.  It reported 42 of 102 entries covered while the journal's
    gate reported 102/102 in the same file.  A separator set containing digits is not a
    separator set, and a mis-reporting counter is worse than no counter.

    The class ALSO excluded the newline (`[^\]\n]{0,60}`), which turned out to be the
    same failure in a second guise.  The journal's gate matches
    `\[(\d+(?:\s*[,\u2013-]\s*\d+)*)\]`, and `\s` matches a newline -- so the gate reads a
    bracket group the manuscript's own reflow split across a line break, while this
    counter could not see it.  Measured consequence on one blob: the gate reported
    `AMBIGUOUS ... (2) [128, 512]` and `cited=104`, while this counter reported "the
    unmatched set is empty" and 15 non-citation groups.  A window narrower than the
    reference instrument's is not a conservative window -- it is a DIFFERENT
    measurement, and the file that carries the deferral then asserts the contrary of
    what the gate says.  The class now spans newlines exactly as the gate's `\s*` does.
    """
    cites, other = set(), set()
    EN, DASH, COMMA = "\u2013", "\u2014", ","
    for m in re.finditer(r"\[([^\]]{0,60})\]", body):
        # one canonical form for classification AND for the listing: a group the
        # manuscript's reflow split is the same group, and its listed text is one line
        body_in = " ".join(m.group(1).split())
        inner = "[" + body_in + "]"
        if re.fullmatch(r"\d+(?:\s*[\u2013\u2014,-]\s*\d+)*", body_in):
            nums = [int(x) for x in re.findall(r"\d+", body_in)]
            if len(nums) == 2 and re.search(r"[\u2013\u2014-]", body_in):
                cites.update(range(nums[0], nums[1] + 1))      # a [12-14] range expands
            else:
                cites.update(nums)
        else:
            # one line in the list: a group the reflow split would otherwise be printed
            # across two lines and break the bullet it is written into
            other.add(inner)
    return cites, other


def bracket_groups_selftest():
    """Controls for the counter, run on every generation and printed into the report.

    A check that never fires is decoration, so each case below is one the counter has
    actually got wrong, or could.  Returns [(name, ok, observed)].
    """
    cases = []

    def case(name, text, want_cites, want_other):
        c, o = bracket_groups(text)
        ok = (c == set(want_cites)) and (o == set(want_other))
        cases.append((name, ok, {"cites": sorted(c), "other": sorted(o)}))

    # 1. THE defect this revision repairs: a group split by the manuscript's own reflow
    #    must be seen, and classified as the gate classifies it
    case("a bracket group split by a line break is seen and classified as a citation group",
         "text over `K_BAND = [8, 32, 128,\n  512]` here",
         [8, 32, 128, 512], [])
    # 2. the same group unwrapped must classify identically (the wrap must not matter)
    case("the same group unwrapped classifies identically",
         "text over `K_BAND = [8, 32, 128, 512]` here", [8, 32, 128, 512], [])
    # 3. a numeric range still expands
    case("a numeric range expands to its members", "see [12-14] there",
         [12, 13, 14], [])
    # 4. a non-numeric group is listed, on one line even when the source wraps it
    case("a non-numeric group is listed, on one line",
         "the interval [\n  -0.0050, 0.1014] is wide", [], ["[-0.0050, 0.1014]"])
    # 5. the empty case must be empty
    case("no brackets yields no citation and no non-citation group",
         "plain prose without brackets", [], [])
    return cases

def support_selftest():
    """Controls for the SUPPORT test, in the style of the counter's own.

    The support test decides whether a resolved record is the DECLARED work rather than merely a
    real one. It had no self-test: nothing showed it could fire, and a version that always returned
    None would have printed `support OK 102` and looked perfect. Each case below is one it must
    catch, one it must NOT catch, or one it CANNOT catch -- the last is deliberate, because a
    control should name its own blind spot.
    """
    cases = []

    def case(name, rec, intent, must_reject, why=""):
        fail = support_failure(rec, intent)
        rejected = fail is not None
        cases.append((name, rejected == must_reject,
                      "rejected: %s%s" % (fail or "no", (" (%s)" % why) if why else "")))

    case("the declared work, exactly matched, is accepted",
         {"title": "Attention Is All You Need", "venue": "NeurIPS", "type": "proceedings-article"},
         "Attention Is All You Need", False)
    case("a real work whose title is the SAME TOKENS in another order is rejected",
         {"title": "Rank to Learning", "venue": "JMLR", "type": "journal-article"},
         "Learning to Rank", True, "the test is the ORDERED token sequence")
    case("a secondary source carrying the EXACT declared title is rejected",
         {"title": "The Probable Error of a Mean", "type": "reference-entry",
          "venue": "SAGE Encyclopedia of Research Design"},
         "The Probable Error of a Mean", True, "a 2010 encyclopedia entry, not the 1908 paper")
    case("a record one token away from the declared work is rejected",
         {"title": "Attention Is All You Needs", "venue": "arXiv", "type": "preprint"},
         "Attention Is All You Need", True)
    case("a batch row with no declared intent is rejected rather than passed by default",
         {"title": "Attention Is All You Need", "venue": "NeurIPS", "type": "proceedings-article"},
         "", True, "an empty intent must not mean 'no expectation'")
    case("a subtitle carried by both the record and the intent matches",
         {"title": "MetaCost: A Case Study", "venue": "KDD", "type": "proceedings-article"},
         "MetaCost: A Case Study", False)
    case("BLIND SPOT: an intent copied from the record passes by construction",
         {"title": "Attention Is All You Need", "venue": "NeurIPS", "type": "proceedings-article"},
         "Attention Is All You Need", False,
         "this test cannot catch it; the report declares the back-filled count instead")
    return cases


def _selftest_only():
    """Network-free: both self-tests, printed, with a status that can fail.

    `reproduce.sh` deliberately does not run the network resolver, so without this flag the two
    liveness controls would run only when someone remembered the full resolver -- i.e. never on a
    reproduction. This is the entry point a reproduction (and the instrument audit) can call.
    """
    bad = 0
    for label, tests in (("counter", bracket_groups_selftest()), ("support", support_selftest()),
                    ("binding", binding_selftest())):
        print("%s self-test: %d cases" % (label, len(tests)))
        for name, ok, detail in tests:
            print("  %-4s %s -- %s" % ("PASS" if ok else "FAIL", name, detail))
            bad += 0 if ok else 1
    counts, disagreement = batch_marks_report()
    print("batch marks: %d cited -- clause-names-record %d, flagged %d, read %d"
          % (counts["cited"], counts["screen"], counts["flagged"], counts["read"]))
    print("  %-4s every committed mark equals the screen's verdict -- %d disagreement(s)%s"
          % ("PASS" if not disagreement else "FAIL", len(disagreement),
             "" if not disagreement else ": " + "; ".join(disagreement[:3])))
    bad += len(disagreement)
    print("selftest: %d case(s) failed" % bad)
    return 1 if bad else 0

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

    # the self-test is printed, not asserted in silence: a control whose result nobody
    # can read is a control nobody can check
    tests = bracket_groups_selftest()
    out.append("\n**Counter self-test (%d cases, run on this generation).** Each case is\n"
               "one the counter has got wrong or could, and the first is the defect this\n"
               "revision repairs -- a bracket group the manuscript's own reflow split\n"
               "across a line break:\n\n| case | result | observed |\n|---|---|---|\n"
               % len(tests))
    for name, ok, detail in tests:
        out.append("| %s | %s | `%s` |\n"
                   % (name, "**pass**" if ok else "**FAIL**",
                      "cites=%s other=%s" % (detail["cites"], detail["other"])))
    out.append("\n")

    if tool_out:
        def grab(pat):
            m = re.search(pat, tool_out)
            return int(m.group(1)) if m else None
        t_entries, t_cov = grab(r"entries=(\d+)"), grab(r"covered=(\d+)/")
        # The unmatched-set sentence above is answerable on the SAME blob: the gate prints
        # the numbers it could not place, so the two sets are compared rather than each
        # being asserted on its own.  This is the check that would have caught the
        # divergence at the previous head, where this file said "the unmatched set is
        # empty" while the gate printed two numbers into that very set.
        m_amb = re.search(r"AMBIGUOUS:[^\n]*?\((\d+)\)\s*\[([^\]]*)\]", tool_out)
        gate_unmatched = ([int(x) for x in re.findall(r"\d+", m_amb.group(2))]
                          if m_amb else [])
        sets_agree = (sorted(gate_unmatched) == sorted(unmatched))
        agree = (t_entries == len(entries) and t_cov == len(covered) and sets_agree)
        out.append("\n**Agreement between the two counters.** This section's counter reports %d\n"
                   "entries and %d covered; the journal's gate above reports %s and %s -- %s.\n"
                   "The counter exists to name the non-citation groups, so the two must agree; a\n"
                   "divergence is a defect in one of them and is printed here rather than left to be\n"
                   "noticed.\n"
                   % (len(entries), len(covered), t_entries, t_cov,
                      "**they agree**" if agree else
                      "**THEY DISAGREE: the gate's numbers are authoritative and the counter is the "
                      "defect**"))
        out.append("\n**Unmatched-set agreement -- the quantity this section defers on.** The\n"
                   "gate reports bracket numbers matching no entry: **%s**; this counter's\n"
                   "unmatched set is **%s** -- %s. This is the comparison the sentence above\n"
                   "depends on: at the previous head this file said the unmatched set was\n"
                   "empty while the gate printed two numbers into it, because the counter's\n"
                   "window excluded the line break the group was wrapped across. A deferral is\n"
                   "honest only if the deferring file and the gate read the same text.\n"
                   % (gate_unmatched if gate_unmatched else "none",
                      unmatched if unmatched else "none",
                      "**the sets agree**" if sets_agree else
                      "**THE SETS DISAGREE: the gate is authoritative**"))
    return "".join(out)
def provenance_counts(path):
    """(claim, backfilled): counted PER ROW from the batch's provenance column.

    This replaces a header sentence that DECLARED the split ("Intents from the
    sentence's CLAIM: 20").  A declaration is not checkable: a reviewer could not
    tell which rows it described, and the round-3 review found the declared blind
    spot live in `pbft` -- a row whose intent had been back-filled from the record,
    so the support test asserted the record agreed with itself.

    The column makes the split derivable and the blind spot bounded per row: for a
    `claim` row the support test is a genuine check of the sentence against the
    record; for a `backfilled` row it is a tautology, and now says so where the row
    is, not in a header the rows cannot confirm.

    Fail-closed on a missing column, like every other absent-input path here: an
    unmarked batch is a malformed batch, not a batch with no claim-written intents.
    """
    n_claim = n_back = 0
    for line in io.open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        cols = line.rstrip("\n").split("\t")
        if len(cols) < 6 or not cols[5].strip():
            raise SystemExit(
                "refs_to_verify.tsv row %r carries no provenance field (column 6 must be "
                "`claim` or `backfilled`); defaulting would print a count the rows cannot "
                "confirm" % cols[0])
        mark = cols[5].strip()
        if mark == "claim":
            n_claim += 1
        elif mark == "backfilled":
            n_back += 1
        else:
            raise SystemExit("refs_to_verify.tsv row %r has provenance %r -- the only "
                             "values are `claim` and `backfilled`" % (cols[0], mark))
    return n_claim, n_back


# ---------------------------------------------------------------------------
# Round-3 question 2: does the CITING SENTENCE bind to the RECORD?
#
# The support test above can only check a row whose intent was written from the
# sentence (provenance `claim`).  For a `backfilled` row it asserts that the locator
# agrees with itself, so a wrong locator cannot show up there -- which is how `pbft`
# survived three rounds.  This screen covers that side: for every cited key it takes
# the manuscript clause that names the key and asks whether that clause carries a
# distinctive token of the record's TITLE, or a SURNAME of the record's authors.  If
# neither, the row is flagged for a human read -- never passed.
#
# It is a screen, not a proof, and the direction of its error is the safe one: a clause
# that names a work's ROLE ("two-sample comparison") rather than its title is flagged
# even when the record is right.  So the flagged rows are read and marked (column 7 of
# the batch, `anchor`), and the check below is that the marks agree with this screen --
# a row marked `screen` must actually bind, and no flagged row may stay unread.
# ---------------------------------------------------------------------------
PARTS = ["manuscript_part1.md", "manuscript_part2.md", "manuscript_part3.md"]

_SCREEN_CITE = re.compile(r"\s*\[@[^\]]+\]")
_SCREEN_SEPS = (", ", "; ", ". ", " \u2014 ", "\u2014")
_SCREEN_STOP = frozenset("""
the of and to in a is for on with that this by as at from are be we can their its our it
an not but which when where who how what why than then they these those was were has have
had does do did done using used use between among over under both each more most other
some such only also into out up down no yes if while during new novel based study paper
work works approach method methods model models result results data set sets system
systems analysis analyses
""".split())


def screen_tokens(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower())
            if len(w) >= 5 and w not in _SCREEN_STOP]


def screen_clause(flat, key):
    """The clause that NAMES the key (not the one before its citation cluster).

    The first version of this function cut at the previous separator, so for any key
    that is not the last of a citation cluster it read the PREVIOUS item's text -- an
    instrument measuring a span its name does not describe.  The clause now runs from
    the separator before the key to the separator after the key's cluster.
    """
    pat = "[@%s]" % key
    i = flat.find(pat)
    if i < 0:
        return None
    j = i + len(pat)
    while True:
        m = _SCREEN_CITE.match(flat, j)
        if not m:
            break
        j = m.end()
    right = min([x for x in (flat.find(s, j) for s in _SCREEN_SEPS) if x >= 0] or [len(flat)])
    left = max(flat.rfind(s, 0, i) for s in _SCREEN_SEPS)
    while left > 0 and not re.sub(r"\[@[^\]]+\]|[\s,;.]", "", flat[left + 1:i]):
        left = max(flat.rfind(s, 0, left) for s in _SCREEN_SEPS)
    return flat[left + 1:right].strip()


def screen_names(authors):
    return [w for w in re.findall(r"[A-Z][A-Za-z'\-]{3,}", authors or "")]


def screen_records(records):
    """{key: {"title":..., "names":[...]}} from the records THIS RUN resolved."""
    out = {}
    for key, rec in records.items():
        out[key] = {"title": title_of(rec["title"]), "names": screen_names(rec["authors"])}
    return out


def binding_screen(flat, records):
    """{key: (verdict, signal, clause)} -- BOUND, or NEEDS-READ (never PASS)."""
    count = {}
    for rec in records.values():
        for w in set(screen_tokens(rec["title"])):
            count[w] = count.get(w, 0) + 1
    distinct = set(w for w, n in count.items() if n <= 2)
    out = {}
    for key, rec in records.items():
        cl = screen_clause(flat, key)
        if cl is None:
            out[key] = ("UNCITED", "", "")
            continue
        # The clause WITHOUT its citation markers.  A key is often an author's surname
        # (`massey`, `massart`), so testing the names against the clause as printed made
        # the marker match itself: `two-sample comparison [@massey]` "named" Massey's paper
        # and the row was screened rather than read.  The prose is what is being tested.
        prose = _SCREEN_CITE.sub(" ", cl)
        ct = set(screen_tokens(prose))
        sig = sorted((ct & distinct & set(screen_tokens(rec["title"]))) |
                     set(n for n in rec["names"] if n.lower() in prose.lower()))
        out[key] = ("BOUND", ", ".join(sig), cl) if sig else ("NEEDS-READ", "", cl)
    return out


def manuscript_flat():
    text = ""
    for part in PARTS:
        p = os.path.join(HERE, part)
        if os.path.exists(p):
            text += io.open(p, encoding="utf-8").read() + "\n"
    return re.sub(r"\s+", " ", text)


def anchor_counts(path):
    """Column 7 (`anchor`) of the batch: `screen` | `read`.  Counted, not declared."""
    n_screen, n_read, marks = 0, 0, {}
    for raw in io.open(path, encoding="utf-8"):
        raw = raw.rstrip("\n")
        if not raw.strip() or raw.startswith("#"):
            continue
        cols = raw.split("\t")
        mark = cols[6].strip() if len(cols) > 6 else ""
        if mark not in ("screen", "read"):
            raise SystemExit(
                "refs_to_verify.tsv row %r carries anchor %r -- every row must say how its "
                "anchoring was established: `screen` (the citing clause names the record) or "
                "`read` (the clause was read against the record by the author)" % (cols[0], mark))
        marks[cols[0].strip()] = mark
        n_screen += mark == "screen"
        n_read += mark == "read"
    return n_screen, n_read, marks


def binding_check(flat, records, marks):
    """The marks must agree with the screen.  Returns (problems, screen, counts)."""
    screen = binding_screen(flat, records)
    problems = []
    for key in sorted(marks):
        if key not in screen:
            continue
        verdict, mark = screen[key][0], marks[key]
        if verdict == "BOUND" and mark != "screen":
            problems.append("row %r is marked %s but its clause does name the record"
                            % (key, mark))
        if verdict == "NEEDS-READ" and mark != "read":
            problems.append("row %r is marked %s but its clause names neither the record's "
                            "title nor its authors" % (key, mark))
    counts = {"cited": len(screen),
              "flagged": sum(1 for v in screen.values() if v[0] == "NEEDS-READ"),
              "screen": sum(1 for v in screen.values() if v[0] == "BOUND"),
              "uncited": sum(1 for v in screen.values() if v[0] == "UNCITED"),
              "read": sum(1 for k, m in marks.items() if m == "read" and k in screen
                          and screen[k][0] == "NEEDS-READ")}
    return problems, screen, counts


def binding_section(flat, records, marks):
    problems, screen, counts = binding_check(flat, records, marks)
    out = ["## Does the citing sentence bind to the record?  (round-3 question 2)\n\n",
           "The support test above cannot see a wrong locator on a `backfilled` row, because\n"
           "such a row's intent IS what the locator returned. This screen covers that side and\n"
           "runs on every cited key, whichever way its intent was written: it takes the\n"
           "manuscript **clause that names the key** and asks whether that clause carries a\n"
           "distinctive token of the record's title or a surname of its authors. A clause that\n"
           "names the work's *role* rather than its title (\"two-sample comparison\") is flagged\n"
           "even when the record is right, so the screen's error is in the safe direction and a\n"
           "flagged row is never passed -- it is read against its record by the author, and the\n"
           "mark is recorded per row in column 7 (`anchor`) of the batch.\n\n",
           "| measure | value |\n|---|---|\n",
           "| cited keys | %d |\n" % counts["cited"],
           "| clause names the record (screen) | **%d** |\n" % counts["screen"],
           "| flagged for reading (clause names neither) | %d |\n" % counts["flagged"],
           "| flagged rows read and marked `read` | %d |\n" % counts["read"],
           "| **flagged rows left unread** | **%d** |\n" % (counts["flagged"] - counts["read"]),
           "| marks that disagree with the screen | %d |\n\n" % len(problems),
           "The screen is a control, and its control is the defect it was built for. Applied to\n"
           "the round-3 `pbft` row as it stood -- clause *\"practical Byzantine replication makes\n"
           "that bound an engineering parameter\"* against the record its locator then returned,\n"
           "*\"Dynamic-sized lock-free data structures\"* -- it shares no title token and no author\n"
           "surname, so the row is flagged for reading, and the reading finds the mis-anchor. The\n"
           "screen would thus have surfaced the defect the review found by hand; the selftest pins\n"
           "that case, and the flagged clauses are printed so the reading is checkable rather than\n"
           "asserted:\n\n",
           "| key | record | clause that cites it |\n|---|---|---|\n"]
    for key in sorted(screen):
        verdict, _sig, cl = screen[key]
        if verdict == "NEEDS-READ":
            out.append("| `%s` | %s | %s |\n"
                       % (key, records[key]["title"][:70].replace("|", "/"),
                          cl[:110].replace("|", "/")))
    out.append("\n")
    return "".join(out), problems, counts


def binding_selftest():
    """Cases a screen for sentence-to-record binding must fail on when broken."""
    tests = []

    def case(name, text, records, key, want):
        flat = re.sub(r"\s+", " ", text)
        got = binding_screen(flat, records)[key][0]
        tests.append((name, got == want, "verdict %s (wanted %s)" % (got, want)))

    pbft_clause = ("and practical Byzantine replication makes that bound an engineering "
                   "parameter [@pbft].")
    case("flag_wrong_locator", pbft_clause,
         {"pbft": {"title": "Dynamic-sized lock-free data structures",
                   "names": ["Castro", "Liskov"]}}, "pbft", "NEEDS-READ")
    case("bound_after_repair", pbft_clause,
         {"pbft": {"title": "Practical byzantine fault tolerance and proactive recovery",
                   "names": ["Castro", "Liskov"]}}, "pbft", "BOUND")
    case("bound_by_surname",
         "the Dvoretzky-Kiefer-Wolfowitz bound with its sharp constant [@dkw].",
         {"dkw": {"title": "Asymptotic minimax character of the sample distribution function",
                  "names": ["Dvoretzky", "Kiefer", "Wolfowitz"]}}, "dkw", "BOUND")
    # A key that is also an author surname must not let the citation marker certify itself.
    case("marker_is_not_a_name", "two-sample comparison [@massey].",
         {"massey": {"title": "The Kolmogorov-Smirnov Test for Goodness of Fit",
                     "names": ["Massey"]}}, "massey", "NEEDS-READ")
    case("list_not_decided", "proxies are optimised instead of goals [@concreteproblems].",
         {"concreteproblems": {"title": "Concrete Problems in AI Safety", "names": ["Amodei"]}},
         "concreteproblems", "NEEDS-READ")
    # The clause must be the one that NAMES the key, not the previous item's text.
    mid = ("step-up and step-down multiplicity corrections [@bh1995] [@hochberg1988] [@byk2001], "
           "alpha spending across interim analyses [@landemets].")
    flat_mid = re.sub(r"\s+", " ", mid)
    cl = screen_clause(flat_mid, "hochberg1988")
    tests.append(("mid_cluster_clause_is_own_item",
                  "multiplicity corrections" in cl and "alpha spending" not in cl,
                  "clause %r" % cl[:70]))
    cl2 = screen_clause(flat_mid, "landemets")
    tests.append(("later_item_clause", "alpha spending" in cl2 and "multiplicity" not in cl2,
                  "clause %r" % cl2[:70]))
    return tests


def rendered_records(path):
    """{key: {"title":..., "names":[...]}} read back off the committed references.md."""
    out = {}
    if not os.path.exists(path):
        return out
    for line in io.open(path, encoding="utf-8"):
        m = re.match(r"\[@([A-Za-z0-9_.:-]+)\]\s*(.*)", line)
        if not m:
            continue
        rest = m.group(2).strip()
        t = re.search(r"\*(.+?)\*", rest)
        out[m.group(1)] = {"title": title_of(t.group(1) if t else rest),
                           "names": screen_names(rest.split("*")[0])}
    return out


def batch_marks_report():
    """Network-free: every committed mark must equal the screen's verdict, recomputed here.

    This is the half a reproduction can run -- `binding_check` needs the freshly resolved
    records, so its agreement check lives in the resolver; this reads the committed
    references.md and the manuscript text and repeats the comparison offline.  Returns
    (counts, disagreements).
    """
    marks = anchor_counts(BATCH)[2]
    screen = binding_screen(manuscript_flat(), rendered_records(OUT_REFS))
    bad = []
    for key, mark in sorted(marks.items()):
        if key not in screen:
            bad.append("%s: carries a mark but no sentence cites it" % key)
            continue
        want = "screen" if screen[key][0] == "BOUND" else "read"
        if mark != want:
            bad.append("%s: marked %s, its clause scores %s" % (key, mark, want))
    for key in sorted(screen):
        if key not in marks:
            bad.append("%s: cited but carries no mark" % key)
    counts = {"cited": len(screen),
              "screen": sum(1 for v in screen.values() if v[0] == "BOUND"),
              "flagged": sum(1 for v in screen.values() if v[0] == "NEEDS-READ"),
              "read": sum(1 for k, m in marks.items()
                          if m == "read" and k in screen and screen[k][0] == "NEEDS-READ")}
    return counts, bad


def main():
    if "--selftest-only" in sys.argv:
        return _selftest_only()
    rows, refs, problems = [], [], []
    n_claim, n_backfill = provenance_counts(BATCH)
    with io.open(BATCH, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.rstrip("\n")
            if not raw.strip() or raw.startswith("#"):
                continue
            cols = [p.strip() for p in raw.split("\t")]
            key, kind, value = cols[0], cols[1], cols[2]
            intent = cols[3] if len(cols) > 3 else ""
            exp_auth = cols[4] if len(cols) > 4 and cols[4] != "-" else None
            prov = cols[5].strip() if len(cols) > 5 else ""
            if prov not in ("claim", "backfilled"):
                raise SystemExit("row %r has no valid provenance field" % key)
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

    # The rendered list's punctuation, measured over every entry -- and a failure, not a
    # note: a reader meets the bibliography, and 55 entries printed `A..` unnoticed.
    dbl = doubled_periods([(k, line) for k, line, _ in refs])
    if dbl:
        problems.append("doubled period on %d entries (%s)" %
                        (len(set(k for k, _ in dbl)),
                         ", ".join(sorted(set(k for k, _ in dbl))[:5])))

    # Round-3 question 2: the marks in column 7 must agree with a screen recomputed here,
    # from the manuscript text and the records THIS run resolved.
    _n_screen_rows, _n_read_rows, marks = anchor_counts(BATCH)
    binding_text, binding_problems, binding_counts = binding_section(
        manuscript_flat(), screen_records(dict((k, rec) for k, _l, rec in refs)), marks)
    problems.extend(binding_problems)
    print("binding screen: %d cited -- %d clause-names-record, %d flagged, %d read, %d mark(s) "
          "disagreeing" % (binding_counts["cited"], binding_counts["screen"],
                           binding_counts["flagged"], binding_counts["read"],
                           len(binding_problems)))

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
                 "**What this test would and would not have caught, per row.** It fails on every\n"
                 "entry whose locator points at a different work, and it fails on a `title`-method\n"
                 "search answered by a reference work. It can only *check* a row whose intent was\n"
                 "written from the citing sentence, so the batch now carries a **provenance column**\n"
                 "and the counts below are **counted from it, per row**:\n\n"
                 "| provenance | rows | what the support test means for them |\n"
                 "|---|---|---|\n"
                 "| `claim` | **%d** | the sentence fixed the work and the locator was then found -- a genuine check |\n"
                 "| `backfilled` | **%d** | the intent is the locator's own returned title -- the test asserts the locator agrees with itself |\n\n"
                 "This replaces a header that DECLARED the split as a bare count (\"20\"), which a\n"
                 "reviewer could not run: the rows did not record which way any intent was written.\n"
                 "The MARK is still a declaration by the author -- what the column changes is that the\n"
                 "blind spot is now per row and spot-checkable: any row marked `claim` can be checked\n"
                 "by reading its citing sentence and deciding whether that record is the work the\n"
                 "sentence needs.\n"
                 "and the round-3 review found the declared blind spot live in `pbft`. That row was\n"
                 "a **backfilled** row when the review met it, i.e. the defect sat on the side the\n"
                 "declaration named; its repair is itself marked `claim`, because the sentence\n"
                 "fixed the work and the locator was then chosen for that work. The historical 20 is\n"
                 "not recoverable from the tree and is no longer quoted; the rule by which a row is\n"
                 "marked is stated in the batch header, and the number of corrected locators the\n"
                 "tree CAN derive (16, from the round-1 repair diff) is a different set from the\n"
                 "marked rows -- so the batch quotes only what the column carries.\n\n"
                 "Going forward the column is also a **drift guard**: changing a DOI, or a Crossref\n"
                 "record being replaced, fails the run instead of silently rewording a citation.\n\n"
                 % (len(rows), n_ok, n_bad, n_unv, n_claim, n_backfill))
        fh.write(punctuation_section(dbl, len(refs)))
        fh.write(binding_text)
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
    # A self-test whose failure does not reach the status is not a control: until this line the
    # counter's cases were printed into the report and the run exited 0 whatever they said.
    for label, tests in (("counter", bracket_groups_selftest()), ("support", support_selftest()),
                    ("binding", binding_selftest())):
        for name, ok, _detail in tests:
            if not ok:
                problems.append("SELFTEST %s: %s" % (label, name))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
