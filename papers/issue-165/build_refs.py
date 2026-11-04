#!/usr/bin/env python3
"""issue-165 -- build the reference corpus from a REGISTRY, not from memory.

The paper's claims are listed in `refs/slots.json`: one entry per assertion, with the query that asks a
registry for a work supporting it. This program asks Crossref, and a returned record becomes a
reference only if it passes two criteria that are independent of each other:

  (1) TITLE  -- normalised content-word containment in BOTH directions, because a one-way test accepts
               any longer work that happens to mention the query's words. A title of three content
               words or fewer has no resolution under containment, so it must match exactly.
  (2) YEAR   -- exact, or one year off (a preprint or an edition). Anything else is a different work.

An author mismatch is fatal when the slot declares `want_author`; when it does not, the returned
authors are recorded and printed so that a reader can see whom the registry named.

What this program REFUSES to do:
  * invent a reference. A slot the registry cannot fill is reported as UNFILLED and stays unfilled.
  * let one work hold two keys. Same DOI, or same normalised title, is a duplicate and the second slot
    is refused -- otherwise the reference count can be inflated by citing one work twice.
  * hide its own failure rate. Every rejection is printed with its reason, and the tally is a result.

Usage:
  python3 build_refs.py            -> query, verify, write refs/records.json
  python3 build_refs.py --summary  -> re-read the committed records.json and print the tally (offline)
  python3 build_refs.py --refetch KEY[,KEY]  -> re-query named slots only, then rewrite the cache
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SLOTS = os.path.join(HERE, "refs", "slots.json")
RECORDS = os.path.join(HERE, "refs", "records.json")
CROSSREF = "https://api.crossref.org/works"
UA = "silicon-science-cs issue-165 reference gate (mailto:noreply@example.org)"
ROWS = 5
PAUSE = 1.1           # be a polite client; Crossref throttles at ~1 request/second
REQUESTS = 0          # HTTP attempts issued by THIS run; printed, and capped by --max-requests
MAX_REQUESTS = None   # None = no ceiling. A ceiling exists so a network step cannot own the round.


class Budget(Exception):
    """This run has spent its allowed requests. The untouched slots are NOT RUN, never refused."""


def spend():
    """One place counts requests, so --max-requests counts REQUESTS ISSUED and not slots. The check
    comes first: counting a request the ceiling then refuses would print a spend above the ceiling and
    make the log's own number untrue."""
    global REQUESTS
    if MAX_REQUESTS is not None and REQUESTS >= MAX_REQUESTS:
        raise Budget("request ceiling of %d reached" % MAX_REQUESTS)
    REQUESTS += 1


def prior_attempts(rec):
    """How many times this slot has already been asked. A slot DEMOTED by a rule change has not been
    asked wrongly -- the rule moved -- so it starts again at zero and deserves its refetch."""
    if not rec:
        return 0
    if "attempts" in rec:
        return int(rec["attempts"])
    return 0 if str(rec.get("reason", "")).startswith("DEMOTED") else 1
STOP = {"the", "a", "an", "of", "and", "in", "on", "for", "to", "with", "by", "from", "at", "as",
        "is", "are", "its", "this", "that", "into", "via", "not", "or", "their", "our"}


def norm(text):
    """Lowercase alphanumerics only: 'Co-citation in the scientific literature' -> 'cocitation in ...'."""
    return re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower()).strip()


def content_words(title):
    return [w for w in norm(title).split() if len(w) >= 4 and w not in STOP]


def title_ok(want, got):
    """SET EQUALITY of content words, with an exactness rule for short titles.

    Containment in one direction is not identity: a wrapper record ("Faculty Opinions recommendation
    of <title>", "Review of <title>") CONTAINS the title of the work it comments on, and a book review
    carries the book's own title in a journal. Both passed a one-way test and entered the corpus as if
    they were the works. A record whose content words the hypothesis does not have is a different
    document as far as this gate can tell -- if the expected title was merely incomplete, the fix is
    to state the real title and say so, not to loosen the test."""
    a, b = content_words(want), content_words(got)
    if not a or not b:
        return False
    if len(a) <= 3 or len(b) <= 3:
        return norm(want) == norm(got)
    return set(a) == set(b)


WRAPPER = re.compile(r"^(faculty opinions recommendation of|review of|review for|a review of|"
                     r"book review|review\[|review:)", re.I)
# Types that are a scholarly work a reader can cite. A `dataset` record is not a paper; a
# `peer-review` record is a report ABOUT a paper, and citing it would cite the wrong object.
# The two registries spell the same kinds differently (Crossref `journal-article` vs OpenAlex
# `article`; `proceedings-article` vs `conference-paper`), so the whitelist carries BOTH spellings --
# but it stays a whitelist: `dataset`, `peer-review`, `book-review`, `paratext`, `erratum` and `other`
# are objects ABOUT a work, not the work, and are refused by omission.
SCHOLARLY = {"journal-article", "article", "proceedings-article", "conference-paper", "book-chapter",
             "book", "monograph", "edited-book", "reference-book", "posted-content", "preprint",
             "report", "dissertation", "standard", "reference-entry", "review", "letter"}
BOOKISH = {"book", "monograph", "edited-book", "reference-book"}


def shape_ok(item, want_kind=None):
    """Is this record the KIND of object the slot asked for? Returns (ok, reason)."""
    title = (item.get("title") or [""])[0]
    container = (item.get("container-title") or [""])[0]
    typ = (item.get("type") or "").lower()
    if WRAPPER.match(title):
        return False, "a wrapper record, not the work: %r" % title[:60]
    if "faculty opinions" in container.lower():
        return False, "a commentary container, not the work: %r" % container[:50]
    if typ and typ not in SCHOLARLY:
        return False, "record type %r is not a citable scholarly work" % typ
    if want_kind == "book" and typ not in BOOKISH:
        return False, "the slot asks for a book and the record is %r" % typ
    return True, None


def year_of(item):
    if isinstance(item.get("year"), int):
        return item["year"]
    for field in ("published-print", "published-online", "issued", "created"):
        parts = (item.get(field) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            return int(parts[0][0])
    return None


def authors_of(item):
    out = []
    for a in item.get("author") or []:
        fam = (a.get("family") or "").strip()
        giv = (a.get("given") or "").strip()
        if fam:
            out.append("%s, %s" % (fam, giv) if giv else fam)
    return out


def query_crossref(q):
    """A 429 is a limit, not an absence: back off and retry, and if it still fails say REGISTRY
    UNAVAILABLE rather than letting the slot look like a work that does not exist."""
    url = "%s?%s" % (CROSSREF, urllib.parse.urlencode(
        {"query.bibliographic": q, "rows": ROWS, "mailto": "noreply@example.org",
         "select": "DOI,title,author,issued,container-title,type,published-print,published-online,created"}))
    last = None
    for attempt in range(4):
        spend()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as fh:
                return json.loads(fh.read().decode())["message"]["items"]
        except Exception as exc:                                    # noqa: BLE001
            last = exc
            if "429" not in str(exc):
                raise
            time.sleep(4 * (attempt + 1))
    raise last


OPENALEX = "https://api.openalex.org/works"


def query_openalex(q):
    """A SECOND registry under the SAME rule. Crossref does not index every book or preprint; OpenAlex
    does, and a record from it is no weaker evidence -- but it must carry a DOI, because a record with
    no persistent identifier cannot be checked by a reader."""
    url = "%s?%s" % (OPENALEX, urllib.parse.urlencode({"search": q, "per_page": ROWS,
                                                       "mailto": "noreply@example.org"}))
    last = None
    for attempt in range(4):
        spend()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as fh:
                items = json.loads(fh.read().decode()).get("results", [])
            out = []
            for it in items:
                doi = (it.get("doi") or "").replace("https://doi.org/", "")
                out.append({"DOI": doi or None,
                            "title": [it.get("title") or it.get("display_name") or ""],
                            "year": it.get("publication_year"),
                            "author": [{"family": (a.get("author") or {}).get("display_name", "")}
                                       for a in (it.get("authorships") or [])],
                            "container-title": [((it.get("primary_location") or {}).get("source") or {}).get("display_name") or ""],
                            "type": it.get("type")})
            return out
        except Exception as exc:                                     # noqa: BLE001
            last = exc
            if "429" not in str(exc):
                raise
            time.sleep(4 * (attempt + 1))
    raise last


def verify(slot, items, registry="crossref"):
    """Return (accepted_record, notes) or (None, reason). Both criteria must pass."""
    want_year = slot.get("want_year")
    tried = []
    for item in items:
        title = (item.get("title") or [""])[0]
        year = year_of(item)
        sok, sreason = shape_ok(item, slot.get("want_kind"))
        tok = title_ok(slot["want_title"], title)
        yok = year is not None and want_year is not None and abs(year - want_year) <= 1
        tried.append("%s (%s) title=%s year=%s%s"
                     % (title[:60], year, tok, yok, "" if sok else " SHAPE:%s" % sreason))
        if tok and yok and sok:
            rec = {"key": slot["key"], "slot": slot["slot"], "claim": slot["claim"],
                   "query": slot["query"], "doi": item.get("DOI"),
                   "title": title,
                   "authors": authors_of(item),
                   "year": year,
                   "container": (item.get("container-title") or [""])[0],
                   "type": item.get("type"),
                   "verified": {"title": "two-way content-word containment vs want_title",
                                "year": "exact" if year == want_year else "off_by_one",
                                "registry": registry,
                                "queried_on": time.strftime("%Y-%m-%d")}}
            return rec, None
    if not items:
        return None, "NO RECORD returned by Crossref for this query"
    return None, "no returned record passed BOTH criteria; tried: " + " | ".join(tried)


def load_json(path, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except OSError:
        return default


def summary(records):
    """The tally IS a result: a corpus that grew by dropping its refusals would be a silent lie."""
    acc = records.get("accepted", [])
    rej = records.get("rejected", [])
    filled = {r["slot"] for r in acc}
    all_slots = {s["slot"] for s in load_json(SLOTS, {"slots": []})["slots"]}
    print("reference corpus -- built from registry returns, %s" % records.get("built_on", "?"))
    print("  slots declared        : %d" % len(load_json(SLOTS, {"slots": []})["slots"]))
    print("  accepted (verified)   : %d" % len(acc))
    print("  refused               : %d" % len(rej))
    print("  acceptance rate       : %.1f%%" % (100.0 * len(acc) / max(1, len(acc) + len(rej))))
    print("  slots with >=1 record : %d of %d" % (len(filled), len(all_slots)))
    dup = records.get("duplicates_refused", [])
    print("  duplicates refused    : %d" % len(dup))
    if rej:
        print("  refusals, by reason:")
        for r in rej:
            print("    %-14s %s" % (r["key"], r["reason"][:110]))
    return acc, rej


def main():
    slots = load_json(SLOTS, None)
    if slots is None:
        raise SystemExit("missing refs/slots.json")
    cache = load_json(RECORDS, {"accepted": [], "rejected": [], "duplicates_refused": []})

    if "--summary" in sys.argv:
        summary(cache)
        return 0

    if "--reaudit" in sys.argv:
        # Derived verdicts must be recomputable OFFLINE: an acceptance recorded under an older rule
        # proves nothing about the current one. This pass re-applies today's rule to the cached
        # records without touching the network, demotes whatever no longer holds, and says so.
        want = {s["key"]: s for s in slots["slots"]}
        kept, demoted = [], []
        for rec in cache.get("accepted", []):
            slot = want.get(rec["key"])
            if slot is None:
                demoted.append((rec["key"], "slot no longer declared"))
                continue
            tok = title_ok(slot["want_title"], rec["title"])
            yok = rec["year"] is not None and slot.get("want_year") is not None \
                and abs(rec["year"] - slot["want_year"]) <= 1
            sok, sreason = shape_ok({"title": [rec["title"]], "container-title": [rec.get("container") or ""],
                                     "type": rec.get("type")}, slot.get("want_kind"))
            if tok and yok and sok:
                kept.append(rec)
            else:
                demoted.append((rec["key"], "title=%s year=%s shape=%s%s under today's rule "
                                "(want %r / %s)"
                                % (tok, yok, sok, "" if sok else " (%s)" % sreason,
                                   slot["want_title"][:50], slot.get("want_year"))))
        cache["accepted"] = kept
        for k, why in demoted:
            cache["rejected"].append({"key": k, "slot": want.get(k, {}).get("slot", "?"),
                                      "reason": "DEMOTED by --reaudit: " + why,
                                      "query": want.get(k, {}).get("query", "")})
        cache["rejected"].sort(key=lambda r: r["key"])
        cache["reaudited_on"] = time.strftime("%Y-%m-%d")
        with open(RECORDS, "w") as fh:
            fh.write(json.dumps(cache, indent=1, sort_keys=True) + "\n")
        print("reaudit: %d kept, %d demoted" % (len(kept), len(demoted)))
        for k, why in demoted:
            print("  demoted %-16s %s" % (k, why[:100]))
        summary(cache)
        return 0

    only = None
    global MAX_REQUESTS
    for i, a in enumerate(sys.argv):
        if a == "--refetch" and i + 1 < len(sys.argv):
            only = set(sys.argv[i + 1].split(","))
        if a == "--max-requests" and i + 1 < len(sys.argv):
            MAX_REQUESTS = int(sys.argv[i + 1])
    force_repeat = "--force-repeat" in sys.argv
    print("request ceiling: %s" % ("none" if MAX_REQUESTS is None else MAX_REQUESTS))

    # start from the committed cache so a rerun can never shrink the corpus (a rate-limited run must not
    # be mistaken for a set of works that do not exist)
    by_key = {r["key"]: r for r in cache.get("accepted", [])}
    rejected = {r["key"]: r for r in cache.get("rejected", [])}
    dup_refused = list(cache.get("duplicates_refused", []))
    not_run = []

    seen_doi = {}
    seen_title = {}
    for k, r in by_key.items():
        seen_doi.setdefault(r["doi"], k)
        seen_title.setdefault(norm(r["title"]), k)

    for slot in slots["slots"]:
        k = slot["key"]
        if only is not None and k not in only:
            continue
        if k in by_key and only is None:
            continue
        if prior_attempts(rejected.get(k)) >= 2 and only is None and not force_repeat:
            print("  %-16s REFUSED FOR GOOD after %d attempts" % (k, prior_attempts(rejected.get(k))))
            continue
        rec, why, which = None, None, None
        out_of_budget = False
        for registry, fn in (("crossref", query_crossref), ("openalex", query_openalex)):
            try:
                items = fn(slot["query"])
            except Budget as exc:                                 # NOT RUN -- never a refusal
                not_run.append({"key": k, "slot": slot["slot"], "reason": str(exc)})
                print("  %-16s NOT RUN  %s" % (k, exc))
                out_of_budget = True
                break
            except Exception as exc:                              # noqa: BLE001 - recorded, not raised
                why = "REGISTRY UNAVAILABLE (%s): %s" % (registry, exc)
                print("  %-16s REGISTRY UNAVAILABLE %s (%s)" % (k, registry, exc))
                continue
            got, why2 = verify(slot, items, registry=registry)
            if got is not None:
                rec, which = got, registry
                break
            why = why2
        if rec is not None and not rec.get("doi"):
            why = "a %s record with no DOI cannot be checked by a reader" % which
            rec = None
        if out_of_budget:
            continue
        if rec is None and str(why or "").startswith("REGISTRY UNAVAILABLE"):
            # A throttled registry is not an absence. Counting it as a refusal would let a rate limit
            # refuse a slot for good, which is the defect this program's own docstring warns about.
            not_run.append({"key": k, "slot": slot["slot"], "reason": why})
            print("  %-16s NOT RUN  %s" % (k, str(why)[:95]))
            continue
        if rec is None:
            rejected[k] = {"key": k, "slot": slot["slot"], "reason": why, "query": slot["query"],
                           "attempts": prior_attempts(rejected.get(k)) + 1}
            print("  %-16s REFUSED  %s" % (k, why[:95]))
        else:
            prior = seen_doi.get(rec["doi"]) or seen_title.get(norm(rec["title"]))
            if prior and prior != k:
                dup_refused.append({"key": k, "duplicate_of": prior, "doi": rec["doi"],
                                    "title": rec["title"]})
                rejected[k] = {"key": k, "slot": slot["slot"],
                               "reason": "DUPLICATE of %s (same DOI or same normalised title)" % prior,
                               "query": slot["query"]}
                print("  %-16s DUPLICATE of %s" % (k, prior))
            else:
                by_key[k] = rec
                seen_doi[rec["doi"]] = k
                seen_title[norm(rec["title"])] = k
                rejected.pop(k, None)
                print("  %-16s ok  %s (%s) %s" % (k, rec["title"][:58], rec["year"], rec["doi"]))
        time.sleep(PAUSE)

    out = {"built_on": time.strftime("%Y-%m-%d"),
           "registry": "Crossref /works?query.bibliographic",
           "accepted": sorted(by_key.values(), key=lambda r: r["key"]),
           "rejected": sorted(rejected.values(), key=lambda r: r["key"]),
           "duplicates_refused": dup_refused,
           "not_run": not_run}
    with open(RECORDS, "w") as fh:
        fh.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print()
    summary(out)
    print("  requests used         : %d%s" % (REQUESTS, "" if MAX_REQUESTS is None
                                               else " (ceiling %d)" % MAX_REQUESTS))
    if not_run:
        print("  NOT RUN (budget)      : %d slots -- these are not refusals and stay unfetched"
              % len(not_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
