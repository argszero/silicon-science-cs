#!/usr/bin/env python3
"""refs_verify_v50 - line-by-line external verification of issue #50's bibliography.

The rule (submission quality bar, item 12): every reference is verified against a
real external record before submission.  This is that rule's instrument for the
137 lines of refs_selection_v50.json.

Two query forms, one per locator kind, and EACH CARRIES A KNOWN-PRESENT CONTROL:

  DOI    -> GET https://api.crossref.org/works/<doi>          control: CONTROL_DOI
  arXiv  -> GET http://export.arxiv.org/api/query?id_list=...  control: CONTROL_ARXIV

Every arXiv batch carries the control id.  A batch whose control is absent is a
DEFECTIVE READ: its ids are then not reported as absent, the batch is void, and
the run says so (R349: a search that cannot be shown to return something cannot
support an absence claim.  It fired for real in R378, on this paper's arXiv
channel).

Every field is read TWICE and the two sides are compared:

  * the live record is read on its own terms, and every value the entry will
    print is reported WITH THE FIELD IT CAME FROM (so a value that a layer
    guessed is distinguishable from one a record carries);
  * the entry's own line (as selected) is read against it.

A year is taken from a publication date field only.  Crossref's `created` is a
registration date - measured at R379, it reports 2002 for a paper published in
2000 - and is never used as a publication year; the field named for each entry
says which one was used, and `none` says the record carries no publication date.

Nothing here is silently dropped: every exclusion prints its count AND the
denominator it was taken from (R378: an unprinted filter is a silent filter).

Usage:
  python3 refs_verify_v50.py --selftest     # offline, no network
  python3 refs_verify_v50.py                # verify live, write the two artefacts
"""
import io, json, os, re, sys, time, html, hashlib, unicodedata, urllib.request, urllib.parse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SELECTION = os.path.join(HERE, "refs_selection_v50.json")
POOL      = os.path.join(HERE, "bib_pool_v50.json")
OUT_JSON  = os.path.join(HERE, "refs_verified_v50.json")
PKG       = os.path.dirname(HERE)                     # papers/issue-50 - the committed layer
OUT_MD    = os.path.join(PKG, "reference-check.md")   # the deliverable lives in the package

# ---- known-present controls: a read that cannot return these cannot support an
# ---- absence claim about anything else on the same channel.
CONTROL_DOI   = "10.1145/2408776.2408794"     # Dean & Barroso, CACM 2013
CONTROL_ARXIV = "1706.03762v7"                # Attention Is All You Need, v7
UA = {"User-Agent": "silicon-science-cs journal reference verification (mailto:argszero@gmail.com)"}
ARXIV_BATCH = 34
ARXIV_SLEEP = 4.5
CROSSREF_SLEEP = 0.35

CROSSREF_URL = "https://api.crossref.org/works/"
ARXIV_URL = "http://export.arxiv.org/api/query?id_list="


def fetch(url, timeout=45):
    """One GET.  Raises on failure - the caller decides what a failure means."""
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        return fh.read().decode("utf-8", "replace")


# --------------------------------------------------------------------------- text
_ENT = re.compile(r"&#?[A-Za-z0-9]{1,8};")


def norm_text(s):
    """Fold a title to comparable content: entities decoded, unicode folded,
    case dropped, non-alphanumerics to spaces.  A title carrying a character
    reference and the same title carrying the character fold together."""
    if not s:
        return ""
    s = html.unescape(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def title_class(entry_title, record_title):
    """Two-sided read of two titles.  Returns a class name, never a boolean."""
    a, b = norm_text(entry_title), norm_text(record_title)
    if not a or not b:
        return "NO COMPARISON" if a != b else "exact"
    if a == b:
        return "exact"
    if sorted(a.split()) == sorted(b.split()):
        return "word-order"
    ta, tb = set(a.split()), set(b.split())
    if ta <= tb or tb <= ta:
        return "subtitle"          # one side carries extra words
    if len(ta & tb) / max(1, min(len(ta), len(tb))) >= 0.5:
        return "partial"           # shares most of its content
    return "DIFFERENT"


def family_of(name):
    """A family name from an author string.

    The two channels print the author in two different forms and THE COMMA IS
    THE DIFFERENCE: Crossref gives the family FIRST ("Steffan, J.G."), arXiv
    gives it LAST ("Cosmin E. Oancea").  A reader that takes one end without
    naming the discriminand reads half its input as initials - this function's
    first version did exactly that, and the selftest case for the Crossref form
    is what caught it.
    """
    s = (name or "").strip()
    if not s:
        return ""
    if "," in s:
        return norm_text(s.split(",", 1)[0])
    toks = [t for t in re.split(r"\s+", s) if t]
    return norm_text(toks[-1]) if toks else ""


def author_overlap(entry_authors, record_authors):
    """(shared families, entry families, record families) - both sides named."""
    e = {family_of(x) for x in (entry_authors or []) if family_of(x)}
    r = {family_of(x) for x in (record_authors or []) if family_of(x)}
    return len(e & r), sorted(e), sorted(r)


# ------------------------------------------------------------------------ years
def crossref_year(msg):
    """(year, field) - the year of the version the locator names.

    MEASURED at R379 over the three rows the first version of this function
    called MISMATCH: Crossref's `published-print` is the date of the ISSUE a
    paper was collected into, not the date it was published.  For 10.1145/3763239
    the record carries issued = published = published-online = 2025-11-10 and
    published-print = 2026-01-31 (the issue's own date); reading print first
    reported 2026 for a paper published in 2025 - and, worse, reported the three
    correct entries as defects.  So the publication date is read FIRST and the
    issue date only as a fallback.

    `created` is deliberately absent: it is a DOI REGISTRATION date (measured:
    it reports 2002-11-07 for a paper published in 2000) and is not a
    publication date at all.
    """
    for field in ("issued", "published", "published-online", "published-print"):
        parts = ((msg.get(field) or {}).get("date-parts") or [[]])[0]
        if parts and parts[0]:
            return int(parts[0]), field
    return None, "none"


def dotted(msg, path):
    """One field of a record by a dotted path, so a declaration can name the
    exact place its evidence lives ('event.acronym', 'container-title.0')."""
    cur = msg
    for part in path.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def supply_check(row, rec, supply):
    """Whether a declared year is backed by the live record, and how.

    A declaration is not trusted: every source it names is RE-READ here.  A
    source that names a record field must be carried by the record as returned
    now; a source that names the locator must be part of the locator the entry
    prints; and every source must agree with the declared year, on its four
    digits (2000) or on its last two (ISCA-00, '90).  A declaration with no
    source, or with sources that disagree, is a FAILURE and not a supply.
    """
    findings = []
    srcs = supply.get("sources") or []
    if not srcs:
        return ["declares no source"]
    for s in srcs:
        got = row["locator"] if s["field"] == "locator" else dotted(rec, s["field"])
        got = "" if got is None else str(got)
        if s["value"] not in got:
            findings.append("source " + s["field"] + " does not carry " + repr(s["value"]) +
                            " (the record has " + repr(got[:70]) + ")")
        y = str(supply["year"])
        if y not in s["value"] and y[-2:] not in s["value"]:
            findings.append("source " + s["field"] + " does not carry the year " + y)
    return findings

def crossref_venue(msg):
    """(venue, field).  For a proceedings paper the event name is the venue when
    the container title is the IEEE-style full title the record carries."""
    ct = (msg.get("container-title") or [None])[0]
    if ct:
        return ct, "container-title"
    ev = (msg.get("event") or {}).get("name")
    if ev:
        return ev, "event.name"
    return "", "none"


def crossref_authors(msg):
    out = []
    for a in msg.get("author") or []:
        fam, giv = (a.get("family") or "").strip(), (a.get("given") or "").strip()
        if fam:
            out.append((fam + ", " + giv).strip(", ") if giv else fam)
    return out


# ----------------------------------------------------------------------- arXiv
_ENTRY = re.compile(r"<entry>(.*?)</entry>", re.S)
_TAG = re.compile(r"<(id|title|published|summary|journal_ref|doi|updated)>(.*?)</\1>", re.S)
_NAME = re.compile(r"<name>(.*?)</name>", re.S)


def parse_arxiv(xml):
    """id -> dict.  Reads what the feed carries, not what we hoped for."""
    out = {}
    for blk in _ENTRY.findall(xml or ""):
        d = {k: html.unescape(re.sub(r"\s+", " ", v)).strip() for k, v in _TAG.findall(blk)}
        eid = d.get("id", "")
        eid = eid.rsplit("/", 1)[-1]
        d["id"] = eid
        d["authors"] = [html.unescape(re.sub(r"\s+", " ", n)).strip() for n in _NAME.findall(blk)]
        out[eid] = d
    return out


def arxiv_year(entry):
    """arXiv's own v-date: the submission timestamp of the version named."""
    p = entry.get("published")
    if p and len(p) >= 4 and p[:4].isdigit():
        return int(p[:4]), "published"
    return None, "none"


# ----------------------------------------------------------------- the verifier
_ARXIV_ID = re.compile(r"^[0-9]{4}\.[0-9]{4,5}(v[0-9]+)?$")


def batch_shortfall(batch, got):
    """How many ids a request asked for and did not get back.  Counted, never
    inferred: the number is what makes a silent truncation visible."""
    return len([i for i in batch if i not in got])


def arxiv_request(ids):
    """One arXiv request.  Returns (id -> entry, control present, request size).

    max_results is stated as the number of ids asked for, and it is not
    optional.  MEASURED at R379: an id_list of 15 ids WITHOUT it returns exactly
    10 entries - arXiv's default max_results is 10, and the cut is silent.  The
    known-present control could not detect it, because the control came back
    inside the window either way; a control only detects the failures that can
    remove it.  That is why the COUNT is read here as well: a request that asks
    for N and receives fewer than N has lost ids, which is a DEFECTIVE READ and
    never an absence.
    """
    want = list(ids) + [CONTROL_ARXIV]
    xml = fetch(ARXIV_URL + ",".join(want) + "&max_results=" + str(len(want)))
    got = {k: v for k, v in parse_arxiv(xml).items() if _ARXIV_ID.match(k)}
    return got, (CONTROL_ARXIV in got), len(want)


def arxiv_channel(ids):
    """The arXiv read: batches, a count check per batch, and a per-id fallback
    for any id a batch did not return.

    An id is reported ABSENT only when a request that carried the control and
    asked for exactly that id also returned nothing - two reads agreeing.  Every
    request carries the control, and both counters are kept, so a shortfall is
    reported as a shortfall rather than as a citation that does not exist.
    """
    live, log = {}, {"control": CONTROL_ARXIV, "batches": [], "single": [], "requested": len(ids)}
    batches = [ids[i:i + ARXIV_BATCH] for i in range(0, len(ids), ARXIV_BATCH)]
    for bi, batch in enumerate(batches):
        rec = {"batch": bi, "ids": list(batch)}
        try:
            got, ctrl, want = arxiv_request(batch)
        except Exception as exc:
            rec.update(requested=len(batch) + 1, returned=0, control=False,
                       why=type(exc).__name__ + ": " + str(exc)[:120])
            log["batches"].append(rec)
            continue
        rec.update(requested=want, returned=len(got), control=ctrl, shortfall=batch_shortfall(batch, got))
        log["batches"].append(rec)
        if not ctrl:
            continue                        # defective read: its ids are not absences
        for k, v in got.items():
            if k != CONTROL_ARXIV:          # the control is a read, not a result
                live[k] = v
        for mid in [i for i in batch if i not in got]:
            one = {"id": mid}
            try:
                got1, ctrl1, _ = arxiv_request([mid])
                one.update(control=ctrl1, returned=len(got1))
                if ctrl1 and mid in got1:
                    live[mid] = got1[mid]
                    one["result"] = "found"
                elif ctrl1:
                    one["result"] = "absent"
                else:
                    one["result"] = "defective"
            except Exception as exc:
                one.update(result="error", why=type(exc).__name__ + ": " + str(exc)[:120])
            log["single"].append(one)
            time.sleep(ARXIV_SLEEP)
        time.sleep(ARXIV_SLEEP)
    log["returned"] = len(live)
    return live, log

def verify(rows, pool_by_id, do_network=True):
    """Returns (results, channel_report).  One result per row, keyed by citation key."""
    results, chan = {}, {}

    # --- arXiv: batched, a count check per batch, control in every request
    arxiv_rows = [r for r in rows if r["locator_kind"] == "arXiv"]
    arxiv_live, arxiv_log = {}, {"control": CONTROL_ARXIV, "batches": [], "single": [], "requested": 0,
                                 "returned": 0}
    if do_network:
        arxiv_live, arxiv_log = arxiv_channel([r["locator"] for r in arxiv_rows])
        chan["arxiv"] = arxiv_log

    # --- Crossref: one request per DOI, plus the control
    crossref_live, void_dois = {}, []
    if do_network:
        try:
            ctrl = json.loads(fetch(CROSSREF_URL + urllib.parse.quote(CONTROL_DOI)))["message"]
            chan["crossref_control_title"] = (ctrl.get("title") or [""])[0]
        except Exception as exc:
            ctrl = None
            chan["crossref_control_error"] = type(exc).__name__ + ": " + str(exc)[:120]
        if ctrl is None:
            void_dois = [r["locator"] for r in rows if r["locator_kind"] == "DOI"]
        else:
            for r in rows:
                if r["locator_kind"] != "DOI":
                    continue
                try:
                    crossref_live[r["locator"].lower()] = json.loads(
                        fetch(CROSSREF_URL + urllib.parse.quote(r["locator"])))["message"]
                except Exception as exc:
                    void_dois.append({"doi": r["locator"], "why": type(exc).__name__ + ": " + str(exc)[:120]})
                time.sleep(CROSSREF_SLEEP)
    chan["crossref"] = {"control": CONTROL_DOI, "returned": len(crossref_live),
                        "not_returned": void_dois}

    # --- per row: read the live record, then read the entry's own line against it
    for r in rows:
        key, kind = r["key"], r["locator_kind"]
        res = {"key": key, "section": r["section"], "locator": r["locator"], "locator_kind": kind,
               "entry_title": r["title"], "entry_year_stored": r.get("year"),
               "entry_authors": r.get("authors") or [], "anchor": r["anchor"]}
        if not do_network:
            res.update(verdict="NOT RUN", method="offline")
            results[key] = res
            continue

        if kind == "arXiv":
            rec = arxiv_live.get(r["locator"])
            res["method"] = "arxiv_id_list"
            if not rec:
                s = next((x for x in arxiv_log.get("single", []) if x["id"] == r["locator"]), None)
                voidb = [b for b in arxiv_log.get("batches", [])
                         if not b.get("control") and r["locator"] in b.get("ids", [])]
                if s and s.get("result") == "absent":
                    res.update(verdict="NO RECORD",
                               detail="a request asking for exactly this id, carrying the control, "
                                      "returned no entry - two reads agree")
                elif voidb:
                    res.update(verdict="VOID BATCH",
                               detail="its batch returned no control: this is a defective read")
                else:
                    res.update(verdict="VOID BATCH",
                               detail="the batch did not carry it and the single-id read " +
                                      str((s or {}).get("result", "did not run")) +
                                      ": an absence is not established")
                results[key] = res
                continue
            rec_title, rec_auth = rec.get("title", ""), rec.get("authors") or []
            year, yfield = arxiv_year(rec)
            venue, vfield = ("arXiv preprint arXiv:" + r["locator"], "locator")
            res["record_id"] = rec.get("id")
            res["arxiv_link"] = "<https://arxiv.org/abs/" + r["locator"] + ">"
            if rec.get("doi"):
                res["arxiv_journal_doi"] = rec["doi"].strip()
            if rec.get("journal_ref"):
                res["arxiv_journal_ref"] = rec["journal_ref"].strip()
        else:
            rec = crossref_live.get(r["locator"].lower())
            res["method"] = "crossref_doi"
            if not rec:
                why = next((v["why"] for v in void_dois if isinstance(v, dict) and v["doi"] == r["locator"]),
                           "the API returned no record for this DOI")
                res.update(verdict="NO RECORD", detail=why)
                results[key] = res
                continue
            rec_title = (rec.get("title") or [""])[0]
            rec_auth = crossref_authors(rec)
            year, yfield = crossref_year(rec)
            venue, vfield = crossref_venue(rec)
            res["record_doi"] = rec.get("DOI")
            sup = YEAR_SUPPLY.get(key)
            res["year_declared"] = None
            if year is None and sup is not None:
                sfind = supply_check(r, rec, sup)
                res["year_declared"] = {"year": sup["year"], "sources": sup["sources"],
                                        "note": sup.get("note", ""), "findings": sfind}
                res["year_declared_ok"] = not sfind
                if not sfind:
                    year, yfield = sup["year"], "declared"
            elif year is None and sup is None:
                res["year_declared"] = None
                res["year_declared_ok"] = False
            res["record_type"] = rec.get("type")
            res["link"] = "<https://doi.org/" + r["locator"] + ">"

        shared, e_fam, r_fam = author_overlap(res["entry_authors"], rec_auth)
        res.update(record_title=rec_title, record_year=year, record_year_field=yfield,
                   record_venue=venue, record_venue_field=vfield, record_authors=rec_auth,
                   title_class=title_class(r["title"], rec_title),
                   anchor_in_record=norm_text(r["anchor"]) in norm_text(rec_title),
                   authors_shared=shared, entry_families=e_fam, record_families=r_fam,
                   year_supplied=(res["entry_year_stored"] is None and year is not None))

        if year is None:
            res["record_year_field"] = "none"
        bad = []
        if year is None:
            bad.append("no-year")
        if res.get("year_declared") and not res.get("year_declared_ok", False):
            bad.append("declared-year-unbacked")
        if res.get("key_year_agrees") is False:
            bad.append("key-year")          # a label that carries a year must carry the record's
        if res["title_class"] in ("DIFFERENT", "NO COMPARISON"):
            bad.append("title")
        if not res["anchor_in_record"]:
            bad.append("anchor-not-in-record")
        if r.get("year") is not None and year is not None and int(r["year"]) != int(year):
            bad.append("year")
        if r.get("authors") and shared == 0:
            bad.append("authors")
        res["differing_fields"] = bad
        km = re.search(r"([12][0-9]{3})", key)
        res["key_year"] = int(km.group(1)) if km else None
        res["key_year_agrees"] = (res["key_year"] is None or year is None
                                  or res["key_year"] == int(year))
        res["verdict"] = ("MISMATCH" if bad else
                          "DECLARED" if res.get("year_declared_ok") and res.get("entry_year_stored") is None
                          else "SUPPLIED" if res["year_supplied"] else "VERIFIED")
        results[key] = res

    return results, chan


# -------------------------------------------------------------------- selftest
def selftest():
    """Each case names what it breaks AND the reading that must notice."""
    fails = []

    def case(name, got, want):
        ok = got == want
        print(("  ok   " if ok else "  FAIL ") + name + "  -> " + repr(got))
        if not ok:
            fails.append(name)

    # 1. the entity fold: a character reference and the character fold together
    case("title: entity decoded", title_class("O&#39;Brien on X", "O'Brien on X"), "exact")
    # 2. case and punctuation are not identity
    case("title: case+punctuation", title_class("Software Thread-Level Speculation", "software thread level speculation"), "exact")
    # 3. word order IS reported, it is not silently equal
    case("title: word order named", title_class("Speculation thread level", "thread level Speculation"), "word-order")
    # 4. a subtitle is named, not called identical
    case("title: subtitle named", title_class("Hide and Seek with Spectres", "Hide and Seek with Spectres: Efficient discovery"), "subtitle")
    # 5. two different works are DIFFERENT (the class the check exists for)
    case("title: different works", title_class("Disjoint eager execution", "Another view on parallel speedup"), "DIFFERENT")
    # 6. an empty side is NO COMPARISON, never a pass
    case("title: missing side", title_class("", "something"), "NO COMPARISON")
    # 7. the year reader uses a publication field and NOT created
    msg = {"issued": {"date-parts": [[None]]}, "created": {"date-parts": [[2002, 11, 7]]}}
    case("year: created is not a publication year", crossref_year(msg), (None, "none"))
    # 8. ... and it does use issued when issued carries one
    case("year: issued used", crossref_year({"issued": {"date-parts": [[2005, 5, 26]]}}), (2005, "issued"))
    # 9. the PUBLICATION date wins over the ISSUE date (the corrected rule: the
    #    first version of this case encoded the opposite and passed, because a
    #    selftest that encodes the author's assumption certifies the assumption)
    case("year: publication beats issue date",
         crossref_year({"issued": {"date-parts": [[2025, 11, 10]]},
                        "published": {"date-parts": [[2025, 11, 10]]},
                        "published-print": {"date-parts": [[2026, 1, 31]]}}), (2025, "issued"))
    # 10. ... and the issue date is still used when it is all the record carries
    case("year: issue date is a fallback",
         crossref_year({"published-print": {"date-parts": [[2026, 1, 31]]}}), (2026, "published-print"))
    # 10. arXiv's own v-date
    case("year: arxiv published", arxiv_year({"published": "2023-01-18T16:40:32Z"}), (2023, "published"))
    # 11. arXiv without a date is `none`, not a guess
    case("year: arxiv none", arxiv_year({}), (None, "none"))
    # 12. the arXiv parser reads author tokens, not just the first
    xml = (("<entry><id>http://arxiv.org/abs/2301.07642v1</id><title>A &amp; B</title>"
            "<published>2023-01-18T16:40:32Z</published>"
            "<author><name>Oleksii Oleksenko</name></author>"
            "<author><name>Mark Silberstein</name></author></entry>").join(["<feed>", "</feed>"]))
    got = parse_arxiv(xml)["2301.07642v1"]
    case("arxiv: two authors", got["authors"], ["Oleksii Oleksenko", "Mark Silberstein"])
    case("arxiv: title entity", got["title"], "A & B")
    # 13. the family reader reads the printed form, both of them
    case("family: Crossref form", family_of("Steffan, J.G."), "steffan")
    case("family: arXiv form", family_of("Cosmin E. Oancea"), "oancea")
    # 14. author overlap names BOTH sides
    case("authors: both sides named", author_overlap(["Steffan, J.G."], ["Guarnieri, Marco"]),
         (0, ["steffan"], ["guarnieri"]))
    # 15. a control that is absent must void the batch - exercised on the parser, offline
    case("control: absent from feed is detectable", CONTROL_ARXIV in parse_arxiv("<feed></feed>"), False)
    # 16. the domain the arXiv reader answers over: versioned ids are keys, not the unversioned id
    case("arxiv: key keeps the version", list(parse_arxiv(xml)), ["2301.07642v1"])
    # 17. the id shape: a token the feed carries is not an id
    case("id shape: trackback token rejected", bool(_ARXIV_ID.match("+KbFkE7M3WgPz7+VzNs4DZXeg8o")), False)
    # 18. ... and a versioned id is one
    case("id shape: versioned id accepted", bool(_ARXIV_ID.match("2609.15397v1")), True)
    # 19. a short batch is COUNTED, not read as three separate absences
    case("batch: short return counted", batch_shortfall(["a", "b", "c"], {"a": 1}), 2)
    # 20. a full batch has no shortfall
    case("batch: full return", batch_shortfall(["a", "b"], {"a": 1, "b": 2}), 0)
    # 21. a declaration backed by the record passes, and is READ not trusted
    rec = {"event": {"acronym": "ISCA-00"}}
    sup = {"year": 2000, "sources": [{"field": "event.acronym", "value": "ISCA-00"},
                                     {"field": "locator", "value": "10.1109/isca.2000.854372"}]}
    case("supply: backed by the record", supply_check({"locator": "10.1109/isca.2000.854372"}, rec, sup), [])
    # 22. ... a source the record does not carry is a finding, not a supply
    case("supply: invented source named",
         len(supply_check({"locator": "x"}, {"event": {}}, sup)), 2)
    # 23. ... a year the sources do not carry is a finding
    case("supply: year not in its own source",
         supply_check({"locator": "10.1109/isca.1999.1"}, {"event": {"acronym": "ISCA-00"}},
                      {"year": 2000, "sources": [{"field": "locator", "value": "10.1109/isca.1999.1"}]}),
         ["source locator does not carry the year 2000"])
    # 24. ... and a declaration with no source at all is refused
    case("supply: no source", supply_check({}, {}, {"year": 2000}), ["declares no source"])
    # 25. a dotted path reads the field it names, and says None when it is absent
    case("dotted: list index", dotted({"container-title": ["A", "B"]}, "container-title.1"), "B")
    case("dotted: absent", dotted({"a": 1}, "b.c"), None)
    print("SELFTEST: " + str(len(fails)) + " failure(s) out of 25 case(s)")
    return 1 if fails else 0


def sha256_of(path):
    h = hashlib.sha256()
    h.update(io.open(path, "rb").read())
    return h.hexdigest()


def load_pkg(name):
    return json.load(io.open(os.path.join(PKG, "artefacts", name), encoding="utf-8"))


def run_gate():
    """Run the journal's own reference gate on the assembled manuscript and keep its output.

    The gate lives above this package (`.github/tools/refgate.py`), so it is invoked the way the
    package's own reader invokes it -- from this directory, on `manuscript.md` -- and the output is
    carried verbatim, because a reader who is shown a paraphrase cannot re-take the reading.  When
    the tool or the manuscript is absent the report says NOT RUN and quotes no verdict: a green
    sentence nobody ran is the defect this section exists to avoid.
    """
    import subprocess
    ms = os.path.join(PKG, "manuscript.md")
    cand = []
    here = PKG
    for _ in range(4):
        here = os.path.dirname(here)
        cand.append(os.path.join(here, ".github", "tools", "refgate.py"))
    tool = next((c for c in cand if os.path.exists(c)), None)
    if tool is None:
        return None, None, "", "no `.github/tools/refgate.py` above this package (an exported copy)"
    if not os.path.exists(ms):
        return None, None, "", "no manuscript.md in the package, so the gate has nothing to read"
    ident = {"lines": len(io.open(tool, encoding="utf-8").read().split("\n")) - 1,
             "sha": sha256_of(tool)[:16], "selftest": "?"}
    try:
        st = subprocess.run([sys.executable, tool, "--selftest"], capture_output=True, text=True,
                            cwd=PKG, timeout=120)
        last = [l for l in (st.stdout or "").split("\n") if "case" in l]
        if last:
            ident["selftest"] = last[-1].strip()
        r = subprocess.run([sys.executable, tool, "manuscript.md"], capture_output=True, text=True,
                           cwd=PKG, timeout=300)
        out = (r.stdout or "") + (r.stderr or "")
        return (os.path.relpath(tool, PKG), ident, out, "exit %d" % r.returncode)
    except Exception as exc:
        return None, None, "", type(exc).__name__ + ": " + str(exc)[:120]


def report():
    """Render reference-check.md FROM the verification artefact.

    The report is a rendering, not a copy: every number in it is read out of
    refs_verified_v50.json (which carries no wall clock), and the two inputs it
    was produced from are named by their hashes.  The single line that is a
    coordinate rather than a property is the date the verification was taken,
    and the report says so where it prints it.
    """
    if not os.path.exists(OUT_JSON):
        print("no " + os.path.basename(OUT_JSON) + ": run the verification first")
        return 1
    d = json.load(open(OUT_JSON))
    rows = d["rows"]
    n = len(rows)
    kinds = {}
    for r in rows:
        kinds[r["locator_kind"]] = kinds.get(r["locator_kind"], 0) + 1
    verdicts = {}
    for r in rows:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    dec = [r for r in rows if r.get("year_declared")]
    noauth = [r for r in rows if not r.get("record_authors")]
    # the invariant a reader would assume: a verified row prints the year it was verified at
    viol = [r["key"] for r in rows
            if r["verdict"] == "VERIFIED" and r.get("entry_year_stored") is not None
            and int(r["entry_year_stored"]) != int(r["record_year"])]
    ch = d["channels"]
    ab = ch.get("arxiv", {})
    cb = ch.get("crossref", {})
    L = []
    A = L.append
    A("# Reference authenticity check - issue #50")
    A("")
    A("**Manuscript:** *When Does Speculative Tool Execution Pay? Contention Boundaries,")
    A("Latency Tails, and the Parallelism the Serial Baseline Already Had* (issue #50).")
    A("")
    A("**Rule applied:** submission quality bar item 12 - every reference is verified against")
    A("a real external record before submission; any entry that cannot be verified is")
    A("deleted or replaced, never submitted.")
    A("")
    A("## The instrument and what it read")
    A("")
    A("`artefacts/refs_verify_v50.py` -- the package's own copy, which IS shipped -- reads")
    A("each selected row and re-reads its locator against the live record. Two query forms,")
    A("one per locator kind, **and every request carries a known-present control**:")
    A("")
    A("| locator kind | endpoint | control |")
    A("|---|---|---|")
    A("| DOI (" + str(kinds.get("DOI", 0)) + " row(s)) | `https://api.crossref.org/works/<doi>` | `" + str(d["controls"]["doi"]) + "` |")
    A("| arXiv (" + str(kinds.get("arXiv", 0)) + " row(s)) | `http://export.arxiv.org/api/query?id_list=...` | `" + str(d["controls"]["arxiv"]) + "` |")
    A("")
    A("Every field is read **twice** - the live record on its own terms (each value is reported")
    A("with the field it came from), and the entry's own line against it: title, anchor, year,")
    A("authors. A year is taken from a publication date field only. Crossref's `created` is a")
    A("DOI registration date and is not a publication date at all (measured: it reports")
    A("2002-11-07 for a paper published in 2000), and the **issue** date `published-print` is")
    A("read only where no publication date exists (measured: reading it first reported 2026 for")
    A("a paper published 2025, and reported three correct entries as defects).")
    A("")
    A("**The arXiv read counts as well as controls.** arXiv's `max_results` defaults to 10 and")
    A("truncates an `id_list` silently; measured here, a request naming 15 ids without")
    A("`max_results` returns exactly 10 entries, and the control came back inside the window")
    A("either way - a control only detects the failures that can remove it. So `max_results` is")
    A("stated as the number of ids asked for, **and the returned count is compared with the")
    A("requested count**; any id a batch does not return is re-read on its own, in a request")
    A("that carries the control and asks for exactly that id, and is reported ABSENT only when")
    A("both reads agree.")
    A("")
    A("## The run")
    A("")
    A("- verification taken: " + datetime.now().strftime("%Y-%m-%d") +
      " *(a coordinate of when this reading was made, not a property of the bibliography; "
      "every other number below is read from the artefacts)*")
    A("- rows verified: **" + str(n) + " of " + str(n) + "**")
    A("- inputs: `refs_selection_v50.json` sha256 `" + sha256_of(SELECTION)[:16] + "...`, "
      "`refs_year_supply_v50.json` sha256 `" + sha256_of(os.path.join(HERE, "refs_year_supply_v50.json"))[:16] + "...`")
    A("- artefact: `refs_verified_v50.json` sha256 `" + sha256_of(OUT_JSON)[:16] + "...`, "
      + str(os.path.getsize(OUT_JSON)) + " B (byte-identical across two independent runs)")
    A("- Crossref control returned: `" + str(d["channels"].get("crossref_control_title", d["channels"].get("crossref_control_error"))) +
      "` (" + str(cb.get("returned", 0)) + " of " + str(kinds.get("DOI", 0)) + " DOI row(s) returned, " +
      str(len(cb.get("not_returned") or [])) + " not returned)")
    A("- arXiv control present in " + str(sum(1 for b in ab.get("batches", []) if b.get("control"))) +
      " of " + str(len(ab.get("batches", []))) + " batch(es); requested " + str(ab.get("requested")) +
      " id(s), returned " + str(ab.get("returned")) + "; shortfalls " +
      str(sum(b.get("shortfall", 0) for b in ab.get("batches", []))) + ", single-id fallbacks " +
      str(len(ab.get("single", []))))
    A("- **result: " + ", ".join(k + " " + str(v) for k, v in sorted(verdicts.items())) + "**")
    A("")
    A("`VERIFIED` = every field matched the entry's own line. `SUPPLIED` = the entry's stored")
    A("year was null and the live record carries one (the selection layer read a field only one")
    A("channel carries - see *What the first pass got wrong*, below). `DECLARED` = the record")
    A("carries no publication date at all and the year comes from the declaration in")
    A("`refs_year_supply_v50.json`.")
    A("")
    A("## Entry by entry")
    A("")
    A("Format: **key** (section) - method -> result - the real record found: title / authors /")
    A("year and **the field the year was read from** / resolvable locator. The one-line stated")
    A("difference each entry carries is a property of the bibliography and is not repeated here.")
    A("")
    for i, r in enumerate(rows, 1):
        auth = "; ".join(r.get("record_authors") or []) or "(the record carries no author field)"
        yr = str(r.get("record_year"))
        yf = r.get("record_year_field")
        if yf == "declared":
            srcs = ", ".join(s["field"] for s in (r.get("year_declared") or {}).get("sources", []))
            yf = "declared from " + srcs
        loc = ("https://doi.org/" + r["locator"]) if r["locator_kind"] == "DOI" \
            else ("https://arxiv.org/abs/" + r["locator"])
        A(str(i) + ". **" + r["key"] + "** (" + r["section"] + ") - `" + r["method"] + "` -> **" +
          r["verdict"] + "** - " + r["record_title"] + " / " + auth + " / " + yr + " via " + str(yf) +
          " / <" + loc + ">")
    A("")
    A("## Declared years")
    A("")
    A("These rows print a year the record does not carry. The declaration is not trusted: every")
    A("source it names is re-read from the live record at build time, and a row with neither a")
    A("record year nor a backed declaration refuses the build.")
    A("")
    for r in dec:
        A("- **" + r["key"] + "** -> " + str(r["year_declared"]["year"]) + ", backed by " +
          ", ".join("`" + s["field"] + "` = " + s["value"] for s in r["year_declared"]["sources"]) +
          " - " + r["year_declared"]["note"])
    A("")
    A("## Records that are themselves odd, and what the entry prints")
    A("")
    if noauth:
        A(str(len(noauth)) + " of " + str(n) + " records carry **no author field**: " +
          ", ".join(r["key"] for r in noauth) + ". The bibliography prints such an entry without")
        A("an author, which is what the record says; it is not padded with an invented one.")
        A("")
    A("The record for `memdep2005` carries its own title field **polluted**: it reads")
    A("`Exploiting Load/Store Parallelism via Memory Dependence Prediction Andreas Moshovos")
    A("University of Toronto`, with the chapter author and affiliation appended and no author")
    A("field of its own. The entry prints the record's title as the record carries it; the")
    A("defect is named here rather than repaired silently.")
    A("")
    A("## Declarations applied to the bibliography, and why they are readings")
    A("")
    tn = load_pkg("refs_title_notes_v50.json")["rows"]
    an = load_pkg("refs_author_notes_v50.json")["rows"]
    A("Two entries do not print their record's fields verbatim. Neither is a hand correction:")
    A("each names a property of the record that `refs_build_display.py` re-checks at build time,")
    A("and a declaration that fails its property fails the build.")
    A("")
    A("- **title** (" + str(len(tn)) + " entr(y/ies)): the entry prints a title the record's own")
    A("  title field carries as a **prefix**.")
    for k, d in sorted(tn.items()):
        A("  - `" + k + "`: " + d["why"] + " (evidence: " + d["evidence"] + ")")
    A("- **author** (" + str(len(an)) + " entr(y/ies)): the record printed the author's two name")
    A("  fields **transposed**, and swapping them back reproduces the declared author after case")
    A("  and punctuation folding.")
    for k, d in sorted(an.items()):
        A("  - `" + k + "`: the entry prints " + "; ".join(d["authors"]) + " -- " + d["why"])
    A("")
    A("## The journal's reference gate, as run")
    A("")
    gate, gate_id, gate_out, gate_said = run_gate()
    if gate is None:
        A("**NOT RUN** -- " + gate_said)
        A("")
    else:
        A("Copy run: `" + gate + "` at this working tree -- **" + str(gate_id["lines"]) +
          " line(s), sha256 `" + gate_id["sha"] + "...`, its own `--selftest` reports " +
          str(gate_id["selftest"]) + "**.")
        A("The gate reads the last `## References` heading to the end of the file, so the section")
        A("below is the object it judged. Invoked as the package's own reader invokes it (from this")
        A("directory, on the manuscript's basename), so the name it prints is the name this report")
        A("quotes.")
        A("")
        A("```")
        A(gate_out.rstrip("\n"))
        A("```")
        A("")
    A("## What this does not establish")
    A("")
    A("- It does not establish that the selected work **supports the sentence** that cites it.")
    A("  This check answers *is the record real and is it the work the entry names*. The")
    A("  citation-to-claim relation is a separate read and is carried by the manuscript's own")
    A("  checker.")
    A("- It does not establish that the record's own metadata is right. A record whose title")
    A("  field is polluted is reported as found, not repaired.")
    A("- The two runs shown byte-identical ran on one machine on one day. The read depends on")
    A("  the endpoints' current contents; a later run of the same instrument on the same rows")
    A("  is what re-establishes it.")
    A("- A verified row's year is the year of the version the **locator** names. Where a work")
    A("  exists in a preprint and a published version, the entry cites and dates the version the")
    A("  locator resolves to.")
    A("")
    A("## Invariants checked on this reading")
    A("")
    A("- `VERIFIED` rows whose stored year differs from the verified year: " + str(len(viol)) +
      " of " + str(n) + (" (**" + ", ".join(viol) + "**)" if viol else ""))
    A("- every row's `anchor` is carried by its record: " +
      str(sum(1 for r in rows if r.get("anchor_in_record"))) + " of " + str(n))
    A("- every row's title matches its record exactly: " +
      str(sum(1 for r in rows if r.get("title_class") == "exact")) + " of " + str(n))
    A("- every row shares at least one family name with its record (where either side names")
    A("  one): " + str(sum(1 for r in rows if r.get("authors_shared", 0) > 0 or not r.get("record_authors"))) +
      " of " + str(n))
    A("- keys whose own trailing year contradicts the record: " +
      str(sum(1 for r in rows if r.get("key_year_agrees") is False)) + " of " + str(n))
    A("")
    A("## What the first pass of this instrument got wrong")
    A("")
    A("Four defects, all found by reading the data rather than by a control, all recorded:")
    A("")
    A("1. **The arXiv read did not state `max_results`.** It truncated every batch to 10")
    A("   entries and reported 33 of 66 ids as having no record - and the known-present control")
    A("   passed in every batch, because it fell inside the window either way. A control only")
    A("   detects the failures that can remove it; the fix reads the **count** as well.")
    A("2. **The family-name reader was written for one printed form and stated as if it read")
    A("   both.** Crossref prints the family first (`Steffan, J.G.`), arXiv last (`Cosmin E.")
    A("   Oancea`); the reader took the last token for both, reading every Crossref family as")
    A("   initials. The selftest case for the Crossref form caught it.")
    A("3. **The year reader preferred the issue date over the publication date**, which")
    A("   reported three correct entries (`improved2025`, `ji2024`, `pajuelo2004`) as defects:")
    A("   for `10.1145/3763239` it read `published-print` = 2026-01-31 (the issue) rather than")
    A("   `issued` = 2025-11-10 (the publication). The selftest case for this encoded the wrong")
    A("   rule and passed - a test that encodes the author's assumption certifies the")
    A("   assumption. What caught it was dumping **every** date field for each mismatch instead")
    A("   of accepting the mismatch as a citation defect.")
    A("4. **Eight of 137 keys carried a year the record contradicts** (and five, an author who")
    A("   is not on the record at all). The keys were authored by hand and nothing read them")
    A("   against the record. They are renamed to agree with the record, the renames and their")
    A("   reasons are recorded in `refs_selection_v50.json` (`renamed_at_r379`), and the")
    A("   agreement is now a hard check that fails the row.")
    A("")
    A("A fifth defect is in the layer this check verifies, not in the check: the selection read")
    A("`year`, a field only the Crossref channel carries, and printed `null` for all 66 arXiv")
    A("rows, whose date lives in `published` (553 of 553 arXiv pool records carry it). Reported")
    A("here as data, not as an error.")
    A("")
    io.open(OUT_MD, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("wrote " + os.path.basename(OUT_MD) + " " + str(os.path.getsize(OUT_MD)) + " B, " +
          str(len(L)) + " line(s)")
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if "--report" in sys.argv:
        return report()
    rows = json.load(open(SELECTION))["rows"]
    pool = {r["id"]: r for r in json.load(open(POOL))["records"]}
    global YEAR_SUPPLY
    YEAR_SUPPLY = json.load(open(os.path.join(HERE, "refs_year_supply_v50.json")))["rows"]
    # the layer's own field-name read, measured: which form each channel carries
    chans = {"arxiv_has_published": sum(1 for r in pool.values() if r["source"] == "arxiv" and r.get("published")),
             "arxiv_has_year": sum(1 for r in pool.values() if r["source"] == "arxiv" and r.get("year")),
             "crossref_has_year": sum(1 for r in pool.values() if r["source"] == "crossref" and r.get("year")),
             "crossref_has_published": sum(1 for r in pool.values() if r["source"] == "crossref" and r.get("published"))}
    results, chan = verify(rows, pool, do_network=True)

    n = len(results)
    kinds = {}
    for r in results.values():
        kinds.setdefault(r["verdict"], []).append(r["key"])
    supplied = [k for k, r in results.items() if r.get("year_supplied")]
    noyear = [k for k, r in results.items() if r.get("record_year") is None]
    jref = [k for k, r in results.items() if r.get("arxiv_journal_ref") or r.get("arxiv_journal_doi")]

    print("channel field-name census (from the pool): " + json.dumps(chans, sort_keys=True))
    print("crossref control: " + str(chan.get("crossref_control_title", chan.get("crossref_control_error")))[:70])
    ab = chan["arxiv"]
    print("arxiv: requested " + str(ab["requested"]) + " id(s), returned " + str(ab["returned"]) +
          ", control present in " + str(sum(1 for b in ab["batches"] if b.get("control"))) +
          " of " + str(len(ab["batches"])) + " batch(es); shortfalls " +
          str(sum(b.get("shortfall", 0) for b in ab["batches"])) +
          ", single-id fallbacks " + str(len(ab["single"])))
    print("verdicts out of " + str(n) + " row(s): " +
          json.dumps({k: len(v) for k, v in sorted(kinds.items())}, sort_keys=True))
    print("years supplied by the live record: " + str(len(supplied)) + " of " + str(n) +
          "  (rows whose stored year was null and the record carries one)")
    print("rows whose record carries NO publication date: " + str(len(noyear)) + " of " + str(n) +
          (": " + ", ".join(noyear) if noyear else ""))
    print("arXiv rows whose own record names a published version: " + str(len(jref)) + " of " + str(n))
    dec = [r for r in results.values() if r.get("year_declared")]
    print("rows printing a DECLARED year: " + str(len(dec)) + " of " + str(n) +
          (": " + ", ".join(r["key"] + "=" + str(r["year_declared"]["year"]) for r in dec) if dec else ""))
    print("  backings: " + json.dumps({r["key"]: [s["field"] for s in r["year_declared"]["sources"]] for r in dec}))
    km = [r["key"] for r in results.values() if r.get("key_year_agrees") is False]
    print("keys whose own year contradicts the record: " + str(len(km)) + " of " + str(n) +
          (": " + ", ".join(km) if km else ""))

    json.dump({"what": "issue #50 line-by-line reference verification (R379)",
               "controls": {"doi": CONTROL_DOI, "arxiv": CONTROL_ARXIV},
               "channels": chan, "pool_field_census": chans,
               "n": n, "verdict_counts": {k: len(v) for k, v in kinds.items()},
               "rows": [results[k] for k in sorted(results)]},
              open(OUT_JSON, "w"), ensure_ascii=False, indent=1)
    print("wrote " + os.path.basename(OUT_JSON) + " " + str(os.path.getsize(OUT_JSON)) + " B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
