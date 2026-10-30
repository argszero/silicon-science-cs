"""Issue #153 stage 2: place the pool, verify each placed DOI against Crossref, and
generate reference-check.md from that stored state.

Why placement is a separate stage: the 100-reference floor applies to entries that are
CITED, i.e. entries that name a section and the sentence they support.  #149 lost most of
its pool at exactly this step (270 mechanically kept -> 166 rule-kept -> 102 placeable), so
the placed count is the only count the floor may be read against.

Each placed entry names (section, claim).  The claim is a sentence the manuscript will
carry; the record is placed only if its title (or abstract, where Crossref exposes one)
names the construct that sentence is about.  Everything else is pruned WITH A REASON and
counted -- a silent drop is a lie about the pool.

Verification state is stored, and reference-check.md is generated from the stored state by
a pure function, so regenerating it is byte-stable.  A DOI that Crossref does not return is
NOT kept: there is no such thing as a placed-but-unverifiable reference.

Outputs (all re-derivable from pool.json + Crossref):
  placement.json      stored verification state + placement decisions
  reference-check.md  the authenticity report, generated
  placement_report.txt the tally
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

SCAN_DATE = "2026-10-26"
UA = {"User-Agent": "silicon-science-cs/1.0 (mailto:how2how2how2-arch@example.org)"}

# bucket -> (section, claim, construct the record must name)
BUCKETS = {
    "lsm-compaction": (
        "§2 Background",
        "The compaction policy, not the storage medium, is what sets an LSM engine's write "
        "amplification.", r"(compaction|lsm|log[- ]structured merge)"),
    "levels-tiering": (
        "§2 Background",
        "Leveled and tiered compaction are the two deployed families, and the field compares "
        "them empirically in terms of read/write/space trade-offs.",
        # The word must MODIFY a storage construct.  The pattern used to end in a bare
        # `leveled|tiered`, which admits any English sentence that happens to use the adjective --
        # the review found three such entries in this bucket (middle-school "leveled writing",
        # "kilogram-leveled" phase-change preparation, "Leveled Product Codes" for block repair).
        # `tiering`/`tiered` is this bucket's own term and is used as one throughout the corpus;
        # `leveled` is the homonym-prone word (middle-school leveled writing, kilogram-leveled
        # materials, leveled product codes for block repair), so it is admitted only where it
        # MODIFIES a compaction/storage construct.  The first tightening required the modifier for
        # both words and pruned 37 legitimate storage-tiering works; this one is the narrow form
        # the data supports.
        r"((level(ed)?|tier(ed)?)[- ]compaction|tiered"
        r"|level(ed)?[- ]?(compaction|layout|storage|sst|tree|lsm))"),
    "flash-write-amp": (
        "§2 Background",
        "Write amplification is the cost the whole log-structured design is organised around.",
        r"(write amplification|multi-write|wear leveling)"),
    "kv-engine": (
        "§2 Background",
        "The systems that carry these policies are LSM-based key-value stores.",
        r"(key[- ]value store|key[- ]value storage|storage engine|lsm[- ]tree)"),
    "logstructured-fs": (
        "§2 Background",
        "Cleaning in a log-structured file system is the ancestor of compaction: the same "
        "forced relocation under a capacity bound.",
        r"(log[- ]structured|cleaner|cleaning|garbage collection)"),
    "data-placement": (
        "§2 Background",
        "Reorganization under an online arrival sequence is the same shape of cost problem.",
        r"(data placement|reorganiz|reconfigur|migration cost)"),
    "lookahead-online": (
        "§7 Relation to online algorithms with lookahead",
        "Bounded lookahead has been characterised for other online problems; this paper asks "
        "how much future a compaction decision needs.",
        r"(lookahead|look-ahead|semi[- ]online)"),
    "competitive-paging": (
        "§7 Relation to online algorithms with lookahead",
        "Paging is the classical case where the offline optimum is computable and the online "
        "rule is scored against it.",
        r"(paging|cache eviction|belady|offline optimal|competitive caching)"),
    "mts-kserver": (
        "§7 Relation to online algorithms with lookahead",
        "Metrical task systems supply the general framework in which a decision rule is scored "
        "against an offline optimum.",
        r"(metrical task|k[- ]server|work function)"),
    "sched-lookahead": (
        "§7 Relation to online algorithms with lookahead",
        "In scheduling, lookahead is known to improve competitive ratios and its value has been "
        "bounded.",
        r"(lookahead|look-ahead|semi[- ]online|future information)"),
    "ski-rental": (
        "§7 Relation to online algorithms with lookahead",
        "Ski rental is the minimal online decision: pay-as-you-go against a one-off cost.",
        # Two vocabularies, both required: the problem's name AND the field's.  A bare
        # `ski rental` admits a sport-and-leisure study of a ski-hire shop's customer data, which
        # the review found in this bucket; `ski` alone additionally hits the author name Kurkoski,
        # which is why a substring count is never a census.
        r"(?=[\s\S]*(ski[- ]rental|ski rental))"
        r"(?=[\s\S]*(competitive|online|algorithm|ratio|metrical))"),
    "scheduling-theory": (
        "§7 Relation to online algorithms with lookahead",
        "Online scheduling is where competitive ratio against an offline optimum is the "
        "standard yardstick.",
        r"(competitive ratio|competitive analysis)"),
}


# Same word, different object.  Kept as an explicit list with a single reason so the tally
# can be read: `caching` returns wireless caching-placement papers, and `placement` returns
# circuit and file layout work.  (#149 measured exactly this: a homonym list catches some,
# a reviewed pass catches the rest.)
# The word a bucket's construct test used to accept on its own, per bucket.  When a record still
# matches the WORD but no longer the CONSTRUCT, it is pruned with that reason rather than with the
# generic one, so the tally says which failure this was.
# Word boundaries matter: without them `tier(ed)?` matches inside `Tiering`, and the class then
# reports every pruned storage-tiering work as a homonym -- a label that over-counts is as useless
# as one that under-counts.
HOMONYM_WORD = {
    "levels-tiering": r"\b(leveled|level|tiered|tier)\b",
    "ski-rental": r"(ski[- ]rental|ski rental)",
}

ADJACENT = re.compile(
    r"(wireless|cellular|d2d|small cell|5g|edge cach|network cach|content delivery|"
    r"information[- ]centric|social network|blockchain|smart contract|"
    r"instruction scheduling|register allocation|compiler|neural|transformer|"
    r"federated learn|reinforcement learn|graph neural|crowdsourc)", re.I)


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def verify(doi):
    """Ask Crossref for THE record this DOI names. Returns a dict or None."""
    u = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    try:
        req = urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=45) as f:
            m = json.load(f)["message"]
    except Exception:
        return None
    return dict(
        doi=m.get("DOI", ""),
        title=clean((m.get("title") or [""])[0]),
        year=(m.get("issued", {}).get("date-parts") or [[None]])[0][0],
        type=m.get("type", ""),
        venue=clean((m.get("container-title") or [""])[0])[:80],
        authors=[clean("%s %s" % (a.get("given", ""), a.get("family", "")))
                 for a in (m.get("author") or [])][:6])


def place(pool):
    rows, prune = [], []
    for r in pool["records"]:
        sec, claim, pat = BUCKETS[r["theme"]]
        hay = r["title"] + "  " + (r.get("abstract") or "")
        if ADJACENT.search(hay):
            prune.append(dict(doi=r["doi"], reason="adjacent construct (same word, other object)",
                              theme=r["theme"], title=r["title"]))
            continue
        if not re.search(pat, hay, re.I):
            word = HOMONYM_WORD.get(r["theme"])
            if word and re.search(word, hay, re.I):
                prune.append(dict(doi=r["doi"],
                                  reason="the section's word occurs, but not as this section's "
                                         "construct",
                                  theme=r["theme"], title=r["title"]))
            else:
                prune.append(dict(doi=r["doi"], reason="names no construct this section uses",
                                  theme=r["theme"], title=r["title"]))
            continue
        rows.append(dict(doi=r["doi"], title=r["title"], year=r["year"], theme=r["theme"],
                         section=sec, claim=claim,
                         judgement="abstract" if len(r.get("abstract") or "") >= 120 else "title-only"))
    return rows, prune


def reapply():
    """Re-derive the placement DECISION from the rule, keeping every stored verification record.

    A rule change has to be able to move the artifact it governs, and the artifact's two halves are
    different kinds of thing: `verified` is a RECORD of what Crossref returned on a date, and
    `section`/`theme`/`placed` are DERIVED from the rule.  Re-running the whole harvest would
    re-ask the registry and let a record silently change; trusting the stored decision would leave
    the tightened rule inert.  So the decision is recomputed, the records are kept, and any record
    the new rule admits for the first time is fetched and reported by DOI.
    """
    pool = json.load(open("pool.json"))
    prev = json.load(open("placement.json"))
    have = dict((e["doi"], e["verified"]) for e in prev["entries"])
    before = dict((e["doi"], e) for e in prev["entries"])

    cand, prune = place(pool)
    cand_doi = {r["doi"] for r in cand}
    lost = sorted(set(before) - cand_doi)
    gained = sorted(cand_doi - set(before))
    print("re-applying the placement rule")
    print("  previously placed : %d" % len(before))
    print("  placed now        : %d" % len(cand))
    print("  dropped by the rule: %d" % len(lost))
    for d in lost:
        print("     DROP %s  [%s] %s" % (d, before[d]["theme"], before[d]["title"][:80]))
    print("  newly admitted     : %d" % len(gained))

    stored, unverifiable = [], []
    for r in sorted(cand, key=lambda x: (x["section"], x["doi"])):
        rec = have.get(r["doi"])
        if rec is None:
            rec = verify(r["doi"])          # only for DOIs the rule newly admits
            if rec is None:
                unverifiable.append(r)
                print("     UNVERIFIABLE %s" % r["doi"])
                continue
            print("     FETCHED %s  %s" % (r["doi"], rec["title"][:70]))
            time.sleep(0.15)
        r2 = dict(r)
        r2["verified"] = rec
        stored.append(r2)

    placed = sorted(stored, key=lambda x: (x["section"], (x["verified"]["title"] or "").lower(),
                                           x["doi"]))
    state = dict(search_form=pool["search_form"], scan_date=SCAN_DATE,
                 candidates=len(cand), pruned=len(prune), unverifiable=len(unverifiable),
                 placed=len(placed), entries=placed,
                 pruned_reasons=dict((k, sum(1 for p in prune if p["reason"] == k))
                                     for k in set(p["reason"] for p in prune)))
    json.dump(state, open("placement.json", "w"), indent=1, sort_keys=True)
    json.dump(prune, open("placement_pruned.json", "w"), indent=1, sort_keys=True)
    write_reference_check(pool, state, placed)
    print("  pruned reasons: %s" % json.dumps(state["pruned_reasons"], sort_keys=True))
    print("  placed %d (floor 100 -> %s)" % (len(placed), "PASS" if len(placed) >= 100 else "SHORT"))
    return 0


def main():
    if "--reapply" in sys.argv:
        return reapply()
    if "--render-only" in sys.argv:
        # regenerate the report from the stored state; no network, no re-verification
        state = json.load(open("placement.json"))
        pool = json.load(open("pool.json"))
        write_reference_check(pool, state, state["entries"])
        print("reference-check.md re-rendered from placement.json (%d entries)"
              % len(state["entries"]))
        return 0
    pool = json.load(open("pool.json"))
    cand, prune = place(pool)
    print("candidates naming their section's construct: %d" % len(cand))
    print("pruned at placement                         : %d" % len(prune))

    by_section = {}
    for r in cand:
        by_section.setdefault(r["section"], []).append(r)
    for s in sorted(by_section):
        j = {}
        for r in by_section[s]:
            j[r["judgement"]] = j.get(r["judgement"], 0) + 1
        print("  %-46s %3d  %s" % (s, len(by_section[s]), json.dumps(j, sort_keys=True)))

    # verify every candidate against Crossref; a DOI Crossref does not return is dropped
    stored, unverifiable = [], []
    for i, r in enumerate(sorted(cand, key=lambda x: (x["section"], x["doi"])), 1):
        rec = verify(r["doi"])
        if rec is None:
            unverifiable.append(r)
            print("  UNVERIFIABLE %s" % r["doi"])
        else:
            r2 = dict(r)
            r2["verified"] = rec
            stored.append(r2)
        if i % 40 == 0:
            print("  verified %d/%d" % (i, len(cand)))
        time.sleep(0.15)

    placed = sorted(stored, key=lambda x: (x["section"], (x["verified"]["title"] or "").lower(),
                                           x["doi"]))
    state = dict(search_form=pool["search_form"], scan_date=SCAN_DATE,
                 candidates=len(cand), pruned=len(prune), unverifiable=len(unverifiable),
                 placed=len(placed), entries=placed,
                 pruned_reasons=dict((k, sum(1 for p in prune if p["reason"] == k))
                                     for k in set(p["reason"] for p in prune)))
    json.dump(state, open("placement.json", "w"), indent=1, sort_keys=True)
    json.dump(prune, open("placement_pruned.json", "w"), indent=1, sort_keys=True)

    write_reference_check(pool, state, placed)

    report = [
        "PLACEMENT TALLY -- issue #153, stage 2",
        "",
        "harvested distinct          : %d" % len(pool["records"]),
        "named their construct       : %d" % len(cand),
        "pruned at placement         : %d  (reason: names no construct this section uses)"
        % len(prune),
        "unverifiable at Crossref    : %d  (dropped; never kept)" % len(unverifiable),
        "PLACED (floor applies here) : %d" % len(placed),
        "  judgement from abstract   : %d" % sum(1 for e in placed if e["judgement"] == "abstract"),
        "  judgement title-only      : %d" % sum(1 for e in placed if e["judgement"] == "title-only"),
        "",
        "by section:",
    ]
    for s in sorted(by_section):
        n = sum(1 for e in placed if e["section"] == s)
        report.append("  %-46s %3d" % (s, n))
    open("placement_report.txt", "w").write("\n".join(report) + "\n")
    print("\n".join(report))
    print("\nplaced %d ; floor 100 -> %s" % (len(placed), "PASS" if len(placed) >= 100 else "SHORT"))
    return 0


def write_reference_check(pool, state, placed):
    """reference-check.md is a pure function of the stored verification state."""
    out = ["# Reference authenticity check -- issue #153", "",
           "Generated by `place_refs.py` from `placement.json`; regenerating is byte-stable.",
           "Every entry below was checked by DOI against Crossref on %s and the record"
           % SCAN_DATE,
           "Crossref returned is stored next to it. No entry is kept that Crossref did not",
           "return.", "",
           "- search form: %s" % state["search_form"]["registry"],
           "- field `%s`, %d queries x %d rows, window %s"
           % (state["search_form"]["field"], len(state["search_form"]["queries"]),
              state["search_form"]["rows_per_query"], state["search_form"]["window"]),
           "- harvested %d distinct records; %d named their section's construct; %d placed"
           % (len(pool["records"]), state["candidates"], state["placed"]),
           "- %d pruned at placement, %d unverifiable and dropped"
           % (state["pruned"], state["unverifiable"]),
           "- placement judgement read from an abstract for %d entries, from title+venue for %d"
           % (sum(1 for e in placed if e["judgement"] == "abstract"),
              sum(1 for e in placed if e["judgement"] == "title-only")),
           "", "| # | key | section | verified record (Crossref) | DOI | judge |",
           "|---|-----|---------|----------------------------|-----|-------|"]
    for i, e in enumerate(placed, 1):
        v = e["verified"]
        parts = v["authors"][0].split() if v["authors"] else []
        key = re.sub(r"[^a-z0-9]+", "", (parts[-1].lower() if parts else "anon")) \
              + str(v["year"] or "n.d.")
        out.append("| %d | `%s` | %s | %s (%s) | %s | %s |"
                   % (i, key, e["section"], v["title"][:95].replace("|", "/"),
                      v["year"], v["doi"], e["judgement"]))
    out.append("")
    out.append("Placed: **%d** (floor 100; target ~105 and no widening for margin)." % state["placed"])
    open("reference-check.md", "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    sys.exit(main())


def write_reference_check(pool, state, placed):
    """reference-check.md is a pure function of the stored verification state."""
    out = ["# Reference authenticity check -- issue #153", "",
           "Generated by `place_refs.py` from `placement.json`; regenerating is byte-stable.",
           "Every entry below was checked by DOI against Crossref on %s and the record"
           % SCAN_DATE,
           "Crossref returned is stored next to it. No entry is kept that Crossref did not",
           "return.", "",
           "- search form: %s" % state["search_form"]["registry"],
           "- field `%s`, %d queries x %d rows, window %s"
           % (state["search_form"]["field"], len(state["search_form"]["queries"]),
              state["search_form"]["rows_per_query"], state["search_form"]["window"]),
           "- harvested %d distinct records; %d named their section's construct; %d placed"
           % (len(pool["records"]), state["candidates"], state["placed"]),
           "- %d pruned at placement, %d unverifiable and dropped"
           % (state["pruned"], state["unverifiable"]),
           "- placement judgement read from an abstract for %d entries, from title+venue for %d"
           % (sum(1 for e in placed if e["judgement"] == "abstract"),
              sum(1 for e in placed if e["judgement"] == "title-only")),
           "", "| # | key | section | verified record (Crossref) | DOI | judge |",
           "|---|-----|---------|----------------------------|-----|-------|"]
    for i, e in enumerate(placed, 1):
        v = e["verified"]
        parts = v["authors"][0].split() if v["authors"] else []
        key = re.sub(r"[^a-z0-9]+", "", (parts[-1].lower() if parts else "anon")) \
              + str(v["year"] or "n.d.")
        out.append("| %d | `%s` | %s | %s (%s) | %s | %s |"
                   % (i, key, e["section"], v["title"][:95].replace("|", "/"),
                      v["year"], v["doi"], e["judgement"]))
    out.append("")
    out.append("Placed: **%d** (floor 100; target ~105 and no widening for margin)." % state["placed"])
    open("reference-check.md", "w").write("\n".join(out) + "\n")
