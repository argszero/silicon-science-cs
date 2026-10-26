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
        r"((level(ed)?|tier(ed)?)[- ]compaction|leveled|tiered)"),
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
        r"(ski[- ]rental|ski rental)"),
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
            prune.append(dict(doi=r["doi"], reason="names no construct this section uses",
                              theme=r["theme"], title=r["title"]))
            continue
        rows.append(dict(doi=r["doi"], title=r["title"], year=r["year"], theme=r["theme"],
                         section=sec, claim=claim,
                         judgement="abstract" if len(r.get("abstract") or "") >= 120 else "title-only"))
    return rows, prune


def main():
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

    # reference-check.md is a pure function of the stored state
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


if __name__ == "__main__":
    sys.exit(main())
