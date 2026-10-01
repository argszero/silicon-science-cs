#!/usr/bin/env python3
"""#93 R414 -- the classical limb: named works, read by TITLE SEARCH, with a STRICT identity test.

Why the title and not a recalled DOI: this journal measured it (R403, `papers/issue-87/artefacts/refs/NOTES.md`)
-- a hand list of 40 DOIs recalled from memory returned 8 records that do not exist and several that name a
work other than the one the list labelled.  A DOI recalled from memory is a claim the registry refutes, so
the limb is built the other way round: the title is the query, the record is the answer, and an entry is
written from the record the search returned.

TWO identity rules, both declared, both reported per query (no threshold is ever lowered; a requirement is
added and measured):

  rule A  full-title   normalized-title token Jaccard >= 0.85   (stopword-free)
  rule B  main-title   the same test on the MAIN title only -- the text before the first ':' on both sides
                       -- AND SATISFYING A DECLARED METADATA EXPECTATION (see below).  The main title is
                       read because a registry record frequently stores a work's main title WITHOUT its
                       subtitle: "Alarm fatigue: a patient safety concern" returns a record titled
                       "Alarm Fatigue".

WHY RULE B OWES AN EXPECTATION (measured this round, from the limb's own output).  A main title is a weak
identifier, and the failure was read before it was coded: the query "Crying wolf: an empirical study of SSL
warning effectiveness" and the record "Crying wolf: Warning about societal risks can be reputationally
harmful" (PsyArXiv 10.31234/osf.io/gtr53) share a main title EXACTLY and are different works.  No title
formula separates that pair from a true one -- the query "The confused deputy: (or why capabilities might
have been invented)" and the record "The Confused Deputy" (10.1145/54289.871709, Hardy 1988) also share a
main title exactly.  So rule B is admitted only where an expectation is declared (author family, and a year
with +-1 tolerance) and the returned record satisfies it; where no expectation is declared, rule B is
REFUSED and the query falls back to rule A.  Every refusal and its reason are recorded.

CONTROLS.  The limb must be able to report absence, must refuse the substitution rule A would take, and must
refuse rule B where it has no expectation to stand on -- all three are read below.

INDEX   Crossref REST API (api.crossref.org), field = `query.bibliographic` (a title search; no date window
        -- these are named works), read to 8 candidate rows.  Crossref's other date fields are NOT read.
        A NOT FOUND verdict therefore means "not found within 8 candidate rows of the title query" and is
        reported as that, not as "absent from the registry".
SCAN DATE 2026-09-22        OUTPUT  refs_classic.json
"""
import io
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refs_harvest import fetch   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "refs_classic.json")
SCAN_DATE = "2026-09-22"

TITLES = [
    # --- detection, screening and the cost of a wrong decision -------------------------------
    "The meaning and use of the area under a receiver operating characteristic (ROC) curve",
    "Basic principles of ROC analysis",
    "A method of comparing the areas under receiver operating characteristic curves derived from the same cases",
    "The relative operating characteristic in psychology",
    "Index for rating diagnostic tests",
    # --- alarms, alerts and what unfaithful signals do to the checker -------------------------
    "Alarm fatigue: a patient safety concern",
    "Monitor alarm fatigue: an integrative review",
    "Cry Wolf: The Psychology of False Alarms",
    "Overriding of drug safety alerts in computerized physician order entry",
    "Physicians' decisions to override computerized drug alerts in primary care",
    "Effects of computerized physician order entry and clinical decision support systems on medication safety",
    "The effect of computerised physician order entry with clinical decision support on the rates of adverse drug events",
    # --- warnings, dialogs and habituation ----------------------------------------------------
    "Why phishing works",
    "You've been warned: an empirical study of the effectiveness of web browser phishing warnings",
    "Crying wolf: an empirical study of SSL warning effectiveness",
    "How polymorphic warnings reduce habituation in the brain: insights from an fMRI study",
    "Your attention please: designing security-decision UIs to make genuine risks harder to ignore",
    "Improving SSL warnings: comprehension and adherence",
    "Alice in warningland: a large-scale field study of browser security warning effectiveness",
    "Reading this may harm your computer: the psychology of malware warnings",
    "So long, and no thanks for the externalities: the rational rejection of security advice by users",
    "Improving computer security dialogs",
    # --- authorization, the mediating reference, and the artifact that says yes ---------------
    "The protection of information in computer systems",
    "The confused deputy: (or why capabilities might have been invented)",
    "Programming semantics for multiprogrammed computations",
    "A note on the confinement problem",
    "Protection",
    "Reflections on trusting trust",
    "Security engineering: a guide to building dependable distributed systems",
    "On the formal definition of separation-of-duty policies and their composition",
    "Zero trust architecture",
    "The Byzantine generals problem",
    # --- the economics of an unobservable action ---------------------------------------------
    "The economics of information",
    "The market for lemons: quality uncertainty and the market mechanism",
    "Theory of the firm: managerial behavior, agency costs and ownership structure",
    "Moral hazard and observability",
    "Optimal contracts and competitive markets with costly state verification",
    "Crime and punishment: an economic approach",
    "The economic theory of public enforcement of law",
    "Costly monitoring, financial intermediation, and equilibrium credit rationing",
    # --- human-automation interaction: the checker's own failure modes ------------------------
    "Humans and automation: use, misuse, disuse, abuse",
    "Trust in automation: designing for appropriate reliance",
    "Complacency and bias in human use of automation: an attentional integration",
    "Ironies of automation",
    "The out-of-the-loop performance problem and level of control in automation",
    "Aviation automation: the search for a human-centered approach",
    "Moral crumple zones: cautionary tales in human-robot interaction",
    "Meaningful human control over autonomous systems: a philosophical account",
    "The effects of interruptions on task performance, annoyance, and anxiety in the user interface",
    "If not now, when? The effects of interruption at different moments within task execution",
    "Principles of mixed-initiative user interfaces",
    # --- human-in-the-loop as a method --------------------------------------------------------
    "Human-in-the-loop machine learning: a state of the art",
    "Interactive machine learning for health informatics: when do we need the human-in-the-loop?",
    "Algorithmic accountability: journalistic investigation of computational power structures",
    "The ethics of algorithms: mapping the debate",
    # --- the human check in practice ----------------------------------------------------------
    "A surgical safety checklist to reduce morbidity and mortality in a global population",
    "An intervention to decrease catheter-related bloodstream infections in the ICU",
    "Modern code review: a case study at Google",
    "Characteristics of useful code reviews: an empirical study at Microsoft",
    "Expectations, outcomes, and challenges of modern code review",
    # --- false positives and overdiagnosis in screening at scale ------------------------------
    "Long-term psychosocial consequences of false-positive screening mammography",
    "Overdiagnosis in cancer",
    "The psychological costs of screening",
    "Effect of screening and adjuvant therapy on mortality from breast cancer",
]

STOP = {"a", "an", "the", "of", "on", "for", "and", "in", "to", "with", "over", "from", "at", "by",
        "is", "are", "as", "or", "into", "its"}

# Controls: the limb must be able to report ABSENCE, and must refuse a substitution.  A control is not a
# bibliography candidate; it is counted separately and asserts on the reading below.
CONTROLS = [
    # (query title, expected verdict)
    ("A note on the confinement problem", "match"),                       # known present
    ("Quantum kernels for underwater basket weaving", "NOT FOUND"),       # known absent
    ("Protection", "NOT FOUND"),                                          # the substitution case (rule A)
    ("Crying wolf: an empirical study of SSL warning effectiveness", "NOT FOUND"),  # rule B: no expectation
]

# The declared metadata expectation: a rule B (main-title) match is admitted only where the query declares
# the work's author family, and only if the returned record's authors carry it.  A year, where declared, is
# read with +-1 tolerance (a registry's publication year and a paper's own year disagree by one routinely).
EXPECT = {
    "Alarm fatigue: a patient safety concern": ("Sendelbach", 2013),
    "Monitor alarm fatigue: an integrative review": ("Cvach", 2012),
    # two coordinates were corrected after the first run (both readings kept in refs_classic_r1.json):
    # the record Crossref returns is dated 2014, and the mis-recalled 2016 refused it by 2 years.
    "Algorithmic accountability: journalistic investigation of computational power structures": ("Diakopoulos", 2014),
    "Alice in warningland: a large-scale field study of browser security warning effectiveness": ("Akhawe", 2013),
    "Aviation automation: the search for a human-centered approach": ("Billings", 1997),
    "Crime and punishment: an economic approach": ("Becker", 1968),
    "Cry Wolf: The Psychology of False Alarms": ("Breznitz", 1984),
    "Humans and automation: use, misuse, disuse, abuse": ("Parasuraman", 1997),
    "Ironies of automation": ("Bainbridge", 1983),
    "Overdiagnosis in cancer": ("Welch", 2010),
    "Protection": ("Lampson", 1974),
    # corrected the same way: the registry's record is the 3rd edition (2020), not the 2001 printing.
    "Security engineering: a guide to building dependable distributed systems": ("Anderson", 2020),
    "The confused deputy: (or why capabilities might have been invented)": ("Hardy", 1988),
    "The economics of information": ("Stigler", 1961),
    "The ethics of algorithms: mapping the debate": ("Mittelstadt", 2016),
    "The market for lemons: quality uncertainty and the market mechanism": ("Akerlof", 1970),
    "Theory of the firm: managerial behavior, agency costs and ownership structure": ("Jensen", 1976),
    "Trust in automation: designing for appropriate reliance": ("Lee", 2004),
    "You've been warned: an empirical study of the effectiveness of web browser phishing warnings": ("Egelman", 2008),
    "Your attention please: designing security-decision UIs to make genuine risks harder to ignore": ("Bravo-Lillo", 2013),
    "Improving SSL warnings: comprehension and adherence": ("Felt", 2015),
    "How polymorphic warnings reduce habituation in the brain: insights from an fMRI study": ("Anderson", 2015),
    "Modern code review: a case study at Google": ("Sadowski", 2018),
    "So long, and no thanks for the externalities: the rational rejection of security advice by users": ("Herley", 2009),
    "The effect of computerised physician order entry with clinical decision support on the rates of adverse drug events": ("Wolfstadt", 2008),
}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def main_title(s):
    """The main title: the text before the first ':' (a registry often stores only this part)."""
    return (s or "").split(":")[0].strip()


def toks(s):
    return {w for w in norm(s).split() if w not in STOP}


def jaccard(a, b):
    """Token Jaccard over the stopword-free titles: the identity test of the title limb."""
    A, B = toks(a), toks(b)
    if not A or not B:
        return 0.0
    return len(A & B) / float(len(A | B))


def search(title, rows=8):
    url = ("https://api.crossref.org/works?rows=%d&select=DOI,title,author,issued,container-title,type,publisher"
           "&query.bibliographic=" % rows + urllib.parse.quote(title))
    items = json.loads(fetch(url))["message"]["items"]
    out = []
    for m in items:
        year = None
        for k in ("issued", "published", "created"):
            parts = (m.get(k) or {}).get("date-parts") or []
            if parts and parts[0] and parts[0][0]:
                year = parts[0][0]
                break
        out.append(dict(
            doi=m.get("DOI", ""), title=" ".join((m.get("title") or [""])[0].split()),
            authors=[(a.get("family", "") + ", " + (a["given"].split()[0] if a.get("given") else ""))
                     for a in (m.get("author") or [])][:3],
            n_authors=len(m.get("author") or []), year=year,
            venue=" ".join(((m.get("container-title") or [""])[0] or m.get("publisher", "")).split()),
            type=m.get("type", ""), url="https://doi.org/" + m.get("DOI", ""),
        ))
    return out


def expectation_holds(exp, hit):
    """Read the declared expectation against the record the search returned. Returns (ok, why)."""
    if exp is None:
        return False, "no expectation declared: rule B has no identity power without one"
    family, year = exp
    fams = " | ".join(hit.get("authors") or [])
    if family.lower() not in fams.lower():
        return False, "record authors (%s) do not carry the declared family %r" % (fams or "none", family)
    if year is not None and hit.get("year") is not None and abs(int(hit["year"]) - int(year)) > 1:
        return False, "record year %s is outside %d +-1" % (hit["year"], year)
    return True, "declared family %r and year %s +-1 both hold" % (family, year)


def judge(query_title, hits):
    """Apply both declared rules to one query's candidate rows; record the near-misses each would take."""
    for h in hits:
        h["jaccard_full"] = round(jaccard(norm(query_title), norm(h["title"])), 4)
        h["jaccard_main"] = round(jaccard(norm(main_title(query_title)), norm(main_title(h["title"]))), 4)
    m_a = next((h for h in hits if h["jaccard_full"] >= 0.85), None)
    exp = EXPECT.get(query_title)
    m_b, why = None, None
    for h in hits:
        if h["jaccard_main"] >= 0.85:
            ok, why = expectation_holds(exp, h)
            if ok:
                m_b = h
            break
    if m_b is None and why is None:
        why = ("no candidate row reached the main-title rule (>= 0.85)"
               if exp is not None else "no expectation declared: rule B has no identity power without one")
    return dict(
        matched=m_a or m_b,
        rule=("A" if m_a else ("B" if m_b else None)),
        verdict=("match" if (m_a or m_b) else "NOT FOUND"),
        main_title_tokens=len(toks(main_title(query_title))),
        expectation=({"author_family": exp[0], "year": exp[1]} if exp else None),
        ruleB_refused=m_b is None,
        ruleB_refusal_reason=(None if m_b is not None else why),
        ruleA=dict(verdict=("match" if m_a else "NOT FOUND"), hit=(m_a or {}).get("title", ""), doi=(m_a or {}).get("doi", "")),
        ruleB=dict(verdict=("match" if m_b else "NOT FOUND"), hit=(m_b or {}).get("title", ""), doi=(m_b or {}).get("doi", "")),
        near_miss={(h["doi"] or h["title"]): h["jaccard_main"] for h in hits if 0.4 <= h["jaccard_main"] < 0.85},
    )


def main():
    rep = dict(scan_date=SCAN_DATE, index="Crossref REST API (api.crossref.org)",
               field="query.bibliographic (a title search; no date window)",
               rows_read=8,
               rules={"A_full_title": "normalized-title token Jaccard >= 0.85",
                      "B_main_title": "same test on the text before the first ':', AND the returned record "
                                      "must satisfy a declared (author family, year +-1) expectation; "
                                      "without an expectation rule B is refused"},
               expectations=EXPECT,
               queries={}, controls={}, errors=[])
    for t in TITLES:
        try:
            hits = search(t)
        except Exception as e:      # noqa: BLE001
            rep["errors"].append((t, repr(e)))
            print("ERR  %s" % t, flush=True)
            continue
        j = judge(t, hits)
        j["hits"] = hits
        rep["queries"][t] = j
        print("%s[%s] %-60s -> %s" % ("ok " if j["verdict"] == "match" else "MISS", j["rule"] or "-",
                                      t[:60], (j["matched"] or (hits[0] if hits else {}) or {}).get("title", "")[:48]),
              flush=True)
        time.sleep(0.5)
    for t, expected in CONTROLS:
        hits = search(t)
        j = judge(t, hits)
        rep["controls"][t] = dict(expected=expected, verdict=j["verdict"],
                                  rule_selects=j["rule"], top=(hits[0] if hits else {}).get("title", ""),
                                  top_jaccard_main=(hits[0] if hits else {}).get("jaccard_main"),
                                  ok=(j["verdict"] == expected))
        print("C   %-45s expected %-9s got %-9s (%s)" % (t[:45], expected, j["verdict"],
                                                         "as expected" if j["verdict"] == expected else "WRONG"),
              flush=True)
        time.sleep(0.5)
    n_ok = sum(1 for v in rep["queries"].values() if v["verdict"] == "match")
    n_a = sum(1 for v in rep["queries"].values() if v["ruleA"]["verdict"] == "match")
    n_b = sum(1 for v in rep["queries"].values() if v["ruleB"]["verdict"] == "match")
    n_refused = sum(1 for v in rep["queries"].values() if v["ruleB_refused"])
    # A DOI that answers two different queries is serving two entries: one record cannot be two works.  The
    # check is a POST-PASS because a collision is a property of the pool, not of any single query.
    owners = {}
    for t, j in rep["queries"].items():
        if j["matched"]:
            owners.setdefault(j["matched"]["doi"], []).append(t)
    collisions = {d: ts for d, ts in owners.items() if len(ts) > 1}
    rep.update(n_queries=len(TITLES), n_matched=n_ok, n_ruleA=n_a, n_ruleB=n_b,
               n_ruleB_refused=n_refused, n_unique_dois=len(owners),
               collisions=collisions,
               n_controls_ok=sum(1 for c in rep["controls"].values() if c["ok"]), n_controls=len(CONTROLS))
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    print("\nrule A alone %d | rule B alone %d | rule B refused %d | either %d of %d queries"
          % (n_a, n_b, n_refused, n_ok, len(TITLES)))
    print("unique DOIs %d | collisions %d %s" % (len(owners), len(collisions),
                                                 list(collisions.values()) if collisions else ""))
    print("controls %d/%d | errors %d | wrote %s"
          % (rep["n_controls_ok"], len(CONTROLS), len(rep["errors"]), os.path.basename(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
