#!/usr/bin/env python3
"""#93 R428 -- the citation authenticity report, and the check that owns it.

Why this file exists.  The journal requires every reference to be verified against a real external record before
submission, and a fabricated citation is academic misconduct rather than a formatting slip.  A report written by
hand is a CLAIM that the verification happened; this script is the verification, and it keeps the raw answers so the
claim can be re-read later without re-querying the network.

The join it makes is the first thing that went wrong.  The manuscript cites by LABEL (`[@wang2026]`) and the built
records are keyed by IDENTIFIER (an arXiv id or a DOI), so the report is driven by the manuscript's citation order
read through `cite_check` and the identifier is looked up in `refs_keys.json` -- the first draft drove it off
`refs_built.json` and produced **0 rows** while printing a clean-looking summary, a report that verified nothing
because it had joined on the wrong field.

Two modes, and the split is deliberate:
  --query   (network) ask Crossref for every DOI and the arXiv API for every arXiv key, then write
            `reference-check.json` (the raw answers) and `reference-check.md` (its rendering, one block per entry,
            in the manuscript's citation order).
  (default) (offline) re-read the committed answers and check the report against them: one row per cited record,
            every entry naming its method and the record found, none unverified or mismatched, the .md being the
            rendering of the .json, and the numbering matching the manuscript.  A battery corrupts a copy per
            check, because a check that never fires is decoration.

Run:  python3 refs/reference_check.py --query           (network; from the package root)
      python3 refs/reference_check.py [--selftest]      (offline; the mode reproduce.sh uses)
"""
import io
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                 # the package root: ../ from refs/
BUILT = os.path.join(HERE, "refs_built.json")
KEYS = os.path.join(HERE, "refs_keys.json")
MD = os.path.join(ROOT, "reference-check.md")
JSON = os.path.join(ROOT, "reference-check.json")
UA = "emrg-journal-refcheck/1.0 (silicon-science-cs submission)"
THRESH = 0.80          # normalized title token overlap below this is a MISMATCH


def load_keys():
    """label -> record.  `refs_keys.json` is what the manuscript cites by; `refs_built.json` is keyed by
    identifier.  Reading the wrong one produced an empty report, so only this one drives the query."""
    return json.loads(io.open(KEYS, encoding="utf-8").read())["keys"]


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())


def overlap(a, b):
    ta, tb = set(norm(a).split()), set(norm(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / float(len(ta | tb))


def get(url, tries=3):
    """One request with a small backoff.  Returns (body, error)."""
    import time
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as fh:
                return fh.read().decode("utf-8", "replace"), None
        except Exception as exc:                                  # a flake is retried, then recorded
            last = "%s: %s" % (type(exc).__name__, exc)
            time.sleep(1.5 * (i + 1))
    return None, last


def ask_crossref(doi):
    body, err = get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe=""))
    if err:
        return None, err
    try:
        msg = json.loads(body)["message"]
    except Exception as exc:
        return None, "unparseable Crossref answer: %r" % exc
    year = None
    for k in ("published-print", "published-online", "issued", "created"):
        parts = (msg.get(k) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            year = str(parts[0][0])
            break
    return {"found_title": (msg.get("title") or [""])[0], "found_year": year, "found_doi": msg.get("DOI"),
            "container": (msg.get("container-title") or [""])[0], "type": msg.get("type")}, None


ARX_ENTRY = re.compile(r"<entry>(.*?)</entry>", re.S)


def ask_arxiv(pairs):
    """(label, identifier) pairs; batched, because the API takes an id_list.  Answers come back keyed by LABEL."""
    out, errors = {}, {}
    for i in range(0, len(pairs), 50):
        chunk = pairs[i:i + 50]
        url = ("http://export.arxiv.org/api/query?id_list=%s&max_results=%d"
               % (",".join(ident for _lab, ident in chunk), len(chunk) + 5))
        body, err = get(url)
        if err:
            for lab, _ident in chunk:
                errors[lab] = err
            continue
        seen = {}
        for blob in ARX_ENTRY.findall(body):
            mid = re.search(r"<id>\s*(\S+?)\s*</id>", blob)
            mti = re.search(r"<title>(.*?)</title>", blob, re.S)
            mpu = re.search(r"<published>\s*(\d{4})", blob)
            if not mid:
                continue
            base = re.sub(r"v\d+$", "", mid.group(1).rsplit("/", 1)[-1])
            seen[base] = {"found_title": re.sub(r"\s+", " ", mti.group(1)).strip() if mti else "",
                          "found_year": mpu.group(1) if mpu else None, "found_arxiv": base}
        for lab, ident in chunk:
            if ident in seen:
                out[lab] = seen[ident]
            else:
                errors[lab] = "the arXiv API returned no record for %s" % ident
    return out, errors


def citation_order(keys):
    """The manuscript's [n] order (labels), read through the manuscript's own checker: one owner per count."""
    for cand in (ROOT, os.path.join(ROOT, "manuscript")):
        if os.path.exists(os.path.join(cand, "cite_check.py")):
            if cand not in sys.path:
                sys.path.insert(0, cand)
            import cite_check
            texts = [(os.path.basename(p), io.open(p, encoding="utf-8").read()) for p in cite_check.PARTS]
            order, _occ = cite_check.scan(texts)
            return [k for k in order if k in keys]
    return sorted(keys)


def query():
    recs = load_keys()
    order = citation_order(recs)
    if not order:
        print("REFUSING -- the manuscript cites none of the %d record(s); the join is wrong" % len(recs))
        return 2
    arx = [(k, recs[k]["identifier"]) for k in order if recs[k]["source"] == "arxiv"]
    doi = [k for k in order if recs[k]["source"] == "crossref"]
    print("querying %d DOI(s) at Crossref and %d arXiv key(s) in %d batch(es)"
          % (len(doi), len(arx), (len(arx) + 49) // 50))
    answers, errs = {}, {}
    for k in doi:
        got, err = ask_crossref(recs[k]["identifier"])
        if err:
            errs[k] = err
        else:
            answers[k] = dict(got, method="Crossref /works/<doi>")
    got, er = ask_arxiv(arx)
    for k, v in got.items():
        answers[k] = dict(v, method="arXiv API id_list")
    for k, v in er.items():
        if k not in answers:
            errs[k] = v
    rows = []
    for k in order:
        e = recs[k]
        a = answers.get(k)
        if not a:
            rows.append(dict(key=k, identifier=e["identifier"], title=e["title"], source=e["source"],
                             verdict="UNVERIFIED",
                             method="no query returned a record (%s)" % errs.get(k, "not queried"),
                             found="", similarity=None, detail=""))
            continue
        sim = overlap(e["title"], a.get("found_title", ""))
        verdict = "VERIFIED" if sim >= 0.999 else ("VERIFIED (title differs in form)" if sim >= THRESH
                                                   else "MISMATCH")
        extra = ["query: %s" % e["identifier"]]
        if a.get("found_doi"):
            extra.append("DOI %s" % a["found_doi"])
        if a.get("found_arxiv"):
            extra.append("arXiv %s" % a["found_arxiv"])
        if a.get("container"):
            extra.append(a["container"])
        if a.get("found_year"):
            extra.append("year %s (manuscript: %s)" % (a["found_year"], e.get("year")))
        rows.append(dict(key=k, identifier=e["identifier"], title=e["title"], source=e["source"],
                         verdict=verdict, method=a["method"], found=a.get("found_title", ""),
                         similarity=round(sim, 3), detail="; ".join(extra)))
    obj = dict(study="issue #93", threshold=THRESH, rows=rows,
               n_verified=sum(1 for r in rows if r["verdict"].startswith("VERIFIED")),
               n_mismatch=sum(1 for r in rows if r["verdict"] == "MISMATCH"),
               n_unverified=sum(1 for r in rows if r["verdict"] == "UNVERIFIED"))
    io.open(JSON, "w", encoding="utf-8").write(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    io.open(MD, "w", encoding="utf-8").write(render(obj))
    print("verified %d, mismatch %d, unverified %d of %d"
          % (obj["n_verified"], obj["n_mismatch"], obj["n_unverified"], len(rows)))
    return 0 if obj["n_mismatch"] == 0 and obj["n_unverified"] == 0 else 1


def render(obj):
    L = ["# Reference authenticity report -- issue #93", "",
         "Every reference in `manuscript.md` was checked against a real external record: a DOI through Crossref, an",
         "arXiv key through the arXiv API. The method, the record found and the title agreement are recorded per",
         "entry, in the manuscript's citation order (the `[n]` the bibliography renders in). The network half is",
         "regenerated with `python3 refs/reference_check.py --query`; `reproduce.sh` re-reads the committed answers",
         "offline and refuses a report that has drifted from them.", "",
         "| | |", "|---|---|",
         "| entries checked | %d |" % len(obj["rows"]),
         "| verified | %d |" % obj["n_verified"],
         "| mismatch | %d |" % obj["n_mismatch"],
         "| unverified | %d |" % obj["n_unverified"],
         "| title-agreement threshold | %.2f (normalized token overlap; below it an entry is a MISMATCH) |"
         % obj["threshold"], "",
         "## Method", "",
         "* **Has a DOI ->** `https://api.crossref.org/works/<doi>`; the returned title must agree with the",
         "  manuscript's entry (normalized token overlap >= %.2f). The DOI and container returned are printed, so a"
         % obj["threshold"],
         "  reader can see what was matched; a year difference is printed rather than failed, because an arXiv",
         "  preprint and its published version legitimately carry different years.",
         "* **No DOI ->** `http://export.arxiv.org/api/query?id_list=<id>,...`; the returned title must agree and",
         "  the arXiv id is printed.", "",
         "## Entries", ""]
    for i, r in enumerate(obj["rows"], 1):
        L.append("**[%d] %s** (%s) -- %s" % (i, r["key"], r["source"], r["verdict"]))
        L.append("")
        L.append("> manuscript: *%s*" % r["title"])
        L.append(">")
        L.append("> %s -> found *%s*%s" % (r["method"], r["found"],
                                           "" if r["similarity"] is None else
                                           "  (title overlap %.2f)" % r["similarity"]))
        if r.get("detail"):
            L.append(">")
            L.append("> %s" % r["detail"])
        L.append("")
    L.append("## Verdict")
    L.append("")
    L.append("**%d of %d references verified against a real external record; %d mismatch; %d unverified.**"
             % (obj["n_verified"], len(obj["rows"]), obj["n_mismatch"], obj["n_unverified"]))
    L.append("")
    L.append("No entry is retained on the strength of its own text: each is either matched to a record fetched from")
    L.append("Crossref or arXiv, or it is reported as unverified and removed before submission.")
    return "\n".join(L) + "\n"


def checks(obj, recs, md_text, order, built_count):
    """Every property the report claims, read back.  Returns (rows, failures)."""
    rows, bad = [], []
    by = {r["key"]: r for r in obj["rows"]}
    keys = list(recs)

    def add(name, ok, detail=""):
        rows.append((name, "PASS" if ok else "FAIL", detail))
        if not ok:
            bad.append("%s: %s" % (name, detail))

    add("C1-one-row-per-cited-record", len(obj["rows"]) == len(keys) == len(by),
        "%d rows, %d records, %d unique" % (len(obj["rows"]), len(keys), len(by)))
    add("C2-no-record-missing", set(by) == set(keys),
        "missing %s / extra %s" % (sorted(set(keys) - set(by))[:4], sorted(set(by) - set(keys))[:4]))
    # The counts and the rows are two carriers of one property, and the verdict has to be taken from the object the
    # claim is about: a report whose rows say MISMATCH while its summary says 0 is exactly the defect this family of
    # checks exists for (Class 112 -- a counter other than the one the verdict is read from).
    r_mis = sum(1 for r in obj["rows"] if r["verdict"] == "MISMATCH")
    r_unv = sum(1 for r in obj["rows"] if r["verdict"] == "UNVERIFIED")
    add("C3-no-mismatch-and-no-unverified",
        obj["n_unverified"] == 0 and obj["n_mismatch"] == 0 and r_mis == 0 and r_unv == 0,
        "stated %d/%d, rows %d/%d" % (obj["n_mismatch"], obj["n_unverified"], r_mis, r_unv))
    add("C4-every-entry-names-method-and-record", all(r["method"] and r["found"] for r in obj["rows"]),
        "%d entry(ies), each with method + found title" % len(obj["rows"]))
    add("C5-threshold-is-the-one-the-report-states", obj["threshold"] == THRESH, "%.2f" % obj["threshold"])
    rk = [r["key"] for r in obj["rows"]]
    div = next((("row %d: report %s vs manuscript %s" % (i, a, b))
                for i, (a, b) in enumerate(zip(rk, order), 1) if a != b), None)
    add("C6-manuscript-order", rk == order, div or "identical")
    add("C7-counts-in-the-rendered-verdict",
        ("**%d of %d references verified" % (obj["n_verified"], len(obj["rows"]))) in md_text,
        "the rendering's verdict line reads %d of %d" % (obj["n_verified"], len(obj["rows"])))
    add("C8-md-is-the-rendering-of-json", md_text.rstrip("\n") == render(obj).rstrip("\n"),
        "the .md on disk is byte-equal to the rendering of the .json (%d bytes)" % len(md_text))
    add("C9-every-entry-rendered", all(("**[%d] %s**" % (i, r["key"])) in md_text
                                       for i, r in enumerate(obj["rows"], 1)),
        "%d entry(ies) numbered and present in the rendering" % len(obj["rows"]))
    add("C10-the-queried-identifier-is-the-one-in-the-record",
        all(r["identifier"] and ("query: %s" % r["identifier"]) in (r["detail"] or "")
            for r in obj["rows"] if r["verdict"].startswith("VERIFIED")),
        "every verified row names the identifier it was queried with")
    def implied(r):
        if r["similarity"] is None:
            return "UNVERIFIED"
        if r["similarity"] >= 0.999:
            return "VERIFIED"
        return "VERIFIED (title differs in form)" if r["similarity"] >= obj["threshold"] else "MISMATCH"
    wrong = [r["key"] for r in obj["rows"] if implied(r) != r["verdict"]]
    add("C12-verdict-follows-the-stated-similarity", not wrong, "row(s) whose verdict contradicts their overlap: "
        "%s" % (wrong[:4] or "none"))
    add("C11-volume-bar-and-its-two-carriers", len(obj["rows"]) >= 100 and built_count == len(obj["rows"]),
        "%d reference(s) (bar 100); refs_built.json holds %d" % (len(obj["rows"]), built_count))
    return rows, bad


def main():
    recs = load_keys()
    if "--query" in sys.argv:
        return query()
    if not os.path.exists(JSON):
        print("NOT RUN -- no %s; run with --query first (network)" % os.path.basename(JSON))
        return 2
    obj = json.loads(io.open(JSON, encoding="utf-8").read())
    md_text = io.open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
    order = citation_order(recs)
    built_count = len(json.loads(io.open(BUILT, encoding="utf-8").read())["entries"])
    rows, bad = checks(obj, recs, md_text, order, built_count)
    for name, verdict, detail in rows:
        print("  %-52s %-4s %s" % (name, verdict, detail))
    print("\nREFERENCE CHECK: %s -- %d check(s), %d failed"
          % ("PASS" if not bad else "FAIL", len(rows), len(bad)))
    rc = 0 if not bad else 1
    if "--selftest" in sys.argv:
        import copy
        cases = [
            ("a row that says MISMATCH while the summary says 0 is caught",
             lambda o: o["rows"][0].update(verdict="MISMATCH", similarity=0.02), "C3-no-mismatch"),
            ("a row whose verdict contradicts its own overlap is caught",
             lambda o: o["rows"][0].update(verdict="MISMATCH"), "C12-verdict-follows"),
            ("an entry with no record found fails",
             lambda o: o["rows"][1].update(found="", verdict="UNVERIFIED"), "C4-every-entry-names"),
            ("a dropped entry is caught",
             lambda o: o["rows"].pop(2), "C1-one-row-per-cited-record"),
            ("a reordered report is caught",
             lambda o: (o["rows"].insert(0, o["rows"].pop(3)), None)[1], "C6-manuscript-order"),
            ("an entry the rendering does not carry is caught",
             lambda o: o["rows"][4].update(key="not_in_the_rendering_9999"), "C9-every-entry-rendered",
             "keep_md"),
            ("a verified row that hides its query identifier is caught",
             lambda o: o["rows"][0].update(detail="DOI 10.x/fake"), "C10-the-queried-identifier"),
            ("a stale .md fails the rendering test",
             lambda o: None, "C8-md-is-the-rendering-of-json"),
            ("a table entry renamed away from the built count is caught",
             lambda o: None, "C11-volume-bar"),
        ]
        fired = 0
        for case in cases:
            name, mutate, expect = case[0], case[1], case[2]
            keep_md = len(case) > 3
            o = copy.deepcopy(obj)
            mutate(o)
            if expect.startswith("C8"):
                md2 = md_text.replace("## Verdict", "## Verdict (stale)")
            elif keep_md:
                # The rendering must be the one from BEFORE the mutation: re-rendering the mutated object would
                # let the plant satisfy itself -- the plant's whole point is a .json the .md does not carry.
                md2 = md_text
            else:
                md2 = render(o)
            bc = built_count - 1 if expect.startswith("C11") else built_count
            _r, b2 = checks(o, recs, md2, order, bc)
            hit = any(x.startswith(expect) for x in b2)
            print("  %-58s %s" % (name[:58], "caught" if hit else "MISSED"))
            fired += 1 if hit else 0
            if not hit:
                rc = 1
        print("BATTERY: %d of %d case(s) fired" % (fired, len(cases)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
