#!/usr/bin/env python3
"""#87 R403 -- the classical/statistical limb, read by TITLE SEARCH rather than by a recalled DOI.

Why this pass exists, measured this round: a hand list of 40 DOIs recalled from memory was queried against
Crossref and **8** returned no record at all while several others resolved to a work the list did not name --
`10.1103/RevModPhys.75.715` ("Decoherence, einselection, and the quantum origins of the classical") is not
the quantum-computation review the list labelled it, and `10.1103/RevModPhys.74.1` returns "Optical
simulations of electron diffraction by carbon nanotubes".  A DOI recalled from memory is a claim the registry
refutes, so the classical limb is built the other way round: the title is the query, the record is the
answer, and the entry is written from the record the search returned.

The identity check is explicit and its control is in the file: for each query the returned title is compared
with the queried title (normalised), the comparison is recorded, and a title that does not match is reported
as NOT FOUND (the entry is not written) rather than silently accepted.

Writes refs_classic.json.
"""
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "refs_classic.json")
SCAN_DATE = "2026-09-21"
INDEX = "Crossref REST API (api.crossref.org)"
FIELD = "query.bibliographic (a title search; no date window -- the records are named works)"

TITLES = [
    # kernel machinery and its theory
    "Support-Vector Networks",
    "A training algorithm for optimal margin classifiers",
    "On the uniform convergence of relative frequencies of events to their probabilities",
    "Learning with Kernels: Support Vector Machines, Regularization, Optimization, and Beyond",
    "Kernel Methods for Pattern Analysis",
    "Theory of Reproducing Kernels",
    "Functions of positive and negative type and their connection with the theory of integral equations",
    "Gaussian Processes for Machine Learning",
    "Random Features for Large-Scale Kernel Machines",
    "Using the Nyström method to speed up kernel machines",
    "Nonlinear Component Analysis as a Kernel Eigenvalue Problem",
    "Kernel independent component analysis",
    "Learning with Kernels: a survey of kernel methods",
    "Multiple kernel learning, conic duality, and the SMO algorithm",
    "On the algorithmic implementation of multiclass kernel-based vector machines",
    "Choosing Multiple Parameters for Support Vector Machines",
    "Model Selection for Kernel Machines",
    "Kernel-target alignment",
    "On Kernel-Target Alignment",
    "Learning the Kernel Matrix with Semidefinite Programming",
    # statistics of comparison
    "Statistical Comparisons of Classifiers over Multiple Data Sets",
    "Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms",
    "On the control of the false discovery rate in multiple testing under dependency",
    "Controlling the false discovery rate: a practical and powerful approach to multiple testing",
    "Bootstrap confidence intervals",
    "An Introduction to the Bootstrap",
    "The design and analysis of computer experiments",
    "A study of cross-validation and bootstrap for accuracy estimation and model selection",
    # model selection, tuning and overfitting
    "On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation",
    "Bias in error estimation when using cross-validation for model selection",
    "Practical Bayesian Optimization of Machine Learning Algorithms",
    "Random Search for Hyper-Parameter Optimization",
    "Algorithms for Hyper-Parameter Optimization",
    # baselines and the machine-learning record
    "Random Forests",
    "Extremely randomized trees",
    "Statistical Modeling: The Two Cultures",
    "Gradient-based learning applied to document recognition",
    "The relationship between Precision-Recall and ROC curves",
    "No free lunch theorems for optimization",
    "The Lack of A Priori Distinctions Between Learning Algorithms",
    # quantum computation and machine learning anchors
    "Quantum machine learning",
    "Quantum computational advantage using photons",
    "Quantum supremacy using a programmable superconducting processor",
    "Simulating physics with computers",
    "Quantum theory, the Church-Turing principle and the universal quantum computer",
    "Quantum Computing in the NISQ era and beyond",
    "Supervised learning with quantum-enhanced feature spaces",
    "Quantum machine learning in feature Hilbert spaces",
    "Power of data in quantum machine learning",
    "Towards understanding the power of quantum kernels in the NISQ era",
    "Quantum advantage in learning from experiments",
    "Variational quantum algorithms",
    "Quantum convolutional neural networks",
    "Exponential concentration in quantum kernel methods",
    "Quantum kernel methods: the geometry of data in Hilbert space",
    "Quantum-enhanced machine learning",
    "Quantum algorithms for supervised and unsupervised machine learning",
]


STOP = {"a", "an", "the", "of", "on", "for", "and", "in", "to", "with", "over", "from", "at", "by", "is", "are"}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def toks(s):
    return {w for w in norm(s).split() if w not in STOP}


def jaccard(a, b):
    """Token Jaccard over the stopword-free titles: the identity test of the title limb."""
    A, B = toks(a), toks(b)
    if not A or not B:
        return 0.0
    return len(A & B) / float(len(A | B))


def fetch(url, tries=3, timeout=50):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-cs/refclassic"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:      # noqa: BLE001
            last = e
            time.sleep(2 + 2 * k)
    raise RuntimeError("fetch failed: %s (%s)" % (url, last))


def search(title):
    url = ("https://api.crossref.org/works?rows=3&select=DOI,title,author,issued,container-title,type,publisher"
           "&query.bibliographic=" + urllib.parse.quote(title))
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
            authors=[(a.get("family", "") + (", " + (a["given"].split()[0] if a.get("given") else "")))
                     for a in (m.get("author") or [])][:1],
            n_authors=len(m.get("author") or []), year=year,
            venue=" ".join(((m.get("container-title") or [""])[0] or m.get("publisher", "")).split()),
            type=m.get("type", ""), url="https://doi.org/" + m.get("DOI", ""),
        ))
    return out


def main():
    rep = dict(scan_date=SCAN_DATE, index=INDEX, field=FIELD, queries={}, errors=[])
    for t in TITLES:
        try:
            hits = search(t)
        except Exception as e:      # noqa: BLE001
            rep["errors"].append((t, repr(e)))
            print("ERR  %s" % t, flush=True)
            continue
        top = hits[0] if hits else None
        match = None
        for h in hits:
            qn, hn = norm(t), norm(h["title"])
            if not qn or not hn:
                continue
            j = jaccard(qn, hn)
            h["jaccard"] = j
            if j >= 0.85:          # STRICT: a loose matcher manufactures substitutions (measured this round)
                match = h
                break
        rep["queries"][t] = dict(top=top, hits=hits, matched=match,
                                top_jaccard=(top or {}).get("jaccard"),
                                rule="normalized-title token Jaccard >= 0.85",
                                identity="match" if match else "NOT FOUND")
        flag = "ok  " if match else "MISS"
        print("%s %-58s -> %s" % (flag, t[:58], (match or top or {}).get("title", "")[:56]), flush=True)
        time.sleep(0.5)
    n_ok = sum(1 for v in rep["queries"].values() if v["identity"] == "match")
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    print("\n%d of %d queries matched a record by title | errors %d | wrote %s"
          % (n_ok, len(TITLES), len(rep["errors"]), os.path.basename(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
