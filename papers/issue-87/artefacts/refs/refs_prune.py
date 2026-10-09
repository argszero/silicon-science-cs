#!/usr/bin/env python3
"""#87 R403 -- prune the harvested pools into the package's committed evidence, without the raw bulk.

The raw pools are ~2.6 MB of records (regenerable from the committed scripts + the stated form); what the
package must carry is the FORM and the two limbs' MEASUREMENTS:

  * the search form (indices, date fields, windows with both endpoints, terms, scan date, and the coordinate
    arXiv does not offer -- a filter on a paper's latest version);
  * per-query counts, so the window's own population is readable;
  * the classical limb's per-query verdicts: the strict identity test (stopword-free title-token Jaccard
    >= 0.85), what it matched, and what it refused -- including the entries the LOOSER rule would have
    substituted (measured, and the reason the rule is strict);
  * the recalled-DOI limb's failure measurement.

Writes into the build package (path given as argv[1]).
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STOP = {"a", "an", "the", "of", "on", "for", "and", "in", "to", "with", "over", "from", "at", "by", "is", "are"}


def toks(s):
    import re
    return {w for w in re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split() if w not in STOP}


def jac(a, b):
    A, B = toks(a), toks(b)
    return len(A & B) / float(len(A | B)) if A and B else 0.0


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    raw = json.loads(io.open(os.path.join(HERE, "refs_raw.json"), encoding="utf-8").read())
    pool2 = json.loads(io.open(os.path.join(HERE, "refs_pool2.json"), encoding="utf-8").read())
    classic = json.loads(io.open(os.path.join(HERE, "refs_classic.json"), encoding="utf-8").read())

    # --- limb 1: the recalled-DOI pass, measured
    doi_limb = dict(
        queried=40, returned=raw.get("n_crossref_ok"), no_record=len(raw["errors"]),
        no_record_ids=[e[0] for e in raw["errors"]],
        note="A DOI recalled from memory is a claim the registry refutes: 8 of 40 returned no record, and "
             "several that returned one named a different work (`10.1103/RevModPhys.75.715` is not a "
             "quantum-computation review; `10.1103/RevModPhys.74.1` returns a carbon-nanotube paper). This "
             "limb was RETIRED: the classical works are read by title search instead.")
    subs = []          # explicit, from the round's own log (below)
    for doi, named, returned in [
        ("10.1214/aos/1013699998", "random features", "The control of the false discovery rate in multiple testing under dependency"),
        ("10.1162/089976698300017746", "kernel regression and the smoothing literature", "Natural Gradient Works Efficiently in Learning"),
        ("10.1103/RevModPhys.75.715", "quantum information and computation", "Decoherence, einselection, and the quantum origins of the classical"),
        ("10.1103/RevModPhys.74.1", "quantum computation and information", "Optical simulations of electron diffraction by carbon nanotubes"),
        ("10.1126/science.1058040", "quantum algorithms", "The Sequence of the Human Genome"),
        ("10.1103/PhysRevLett.80.4811", "quantum computation with a small number of qubits", "Breakup of Spiral Waves into Chemical Turbulence"),
        ("10.1038/s41534-019-0187-2", "quantum-kernel implementation on hardware", "Variational ansatz-based quantum simulation of imaginary time evolution"),
        ("10.1103/PhysRevLett.122.140504", "the kernel-advantage claim", "Accelerated Variational Quantum Eigensolver"),
    ]:
        if doi in raw["crossref"]:
            subs.append(dict(doi=doi, entry_named=named, record_returned=returned))
    doi_limb["substitutions"] = subs

    # --- limb 2: the title-search pass, with the loose rule re-scored for the record
    rows = []
    for q, v in sorted(classic["queries"].items()):
        top = v.get("top") or {}
        loose = [h["title"] for h in v.get("hits", [])[:3]
                 if h.get("title") and (jac(q, h["title"]) >= 0.6)]
        rows.append(dict(
            query=q, verdict=v["identity"], rule=v["rule"],
            jaccard_top=round(jac(q, top.get("title", "")), 3),
            jaccard_matched=(round(jac(q, v["matched"]["title"]), 3) if v.get("matched") else None),
            matched=(dict(doi=v["matched"]["doi"], title=v["matched"]["title"], year=v["matched"]["year"],
                          authors=v["matched"]["authors"], venue=v["matched"]["venue"])
                     if v.get("matched") else None),
            top_returned=dict(doi=top.get("doi"), title=top.get("title"), year=top.get("year")),
            near_misses=[t for t in loose if t != (v.get("matched") or {}).get("title")][:2],
        ))
    n_match = sum(1 for r in rows if r["verdict"] == "match")

    # --- the form, and the per-query counts
    form = dict(raw["form"])
    form["arxiv_pass2"] = dict(index="arXiv API (export.arxiv.org)", date_field="submittedDate",
                              window=list(pool2["window"]),
                              queries={k: blk["query"] for k, blk in pool2["queries"].items()})
    form["classical_limb"] = dict(index=classic["index"], field=classic["field"],
                                  rule="stopword-free title-token Jaccard >= 0.85",
                                  n_queries=len(classic["queries"]), n_matched=n_match)
    rep = dict(
        round="R403", scan_date=classic["scan_date"],
        form=form,
        counts=dict(
            pass1_unique_arxiv=raw.get("n_unique_arxiv"), pass1_crossref_records=raw.get("n_crossref_ok"),
            pass1_doi_no_record=len(raw["errors"]),
            pass2_unique_arxiv=len({r["id"] for blk in pool2["queries"].values() for r in blk["rows"]}),
            classical_queries=len(classic["queries"]), classical_matched=n_match,
            classical_not_found=len(classic["queries"]) - n_match),
        arxiv_pass1={k: dict(query=blk["query"], window=list(blk["window"]), n=blk["n_returned"])
                     for k, blk in raw["arxiv"].items()},
        recalled_doi_limb=doi_limb,
        classical_limb=rows,
        note="The raw pools (~2.6 MB) are not committed: they are regenerable from the three committed "
             "scripts plus the form above, and the selection is made against their record set. The "
             "per-atom entries this form produced are `papers/issue-87/references.json`.")
    p = os.path.join(out, "refs_form.json")
    io.open(p, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    print("wrote %s (%d bytes)" % (p, os.path.getsize(p)))
    print("counts: %s" % json.dumps(rep["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
