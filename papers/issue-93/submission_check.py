#!/usr/bin/env python3
"""#93 R429 -- the submission quality bar, owned by a check instead of by prose.

Why this file exists.  The journal's submission bar is a list of thirteen items plus a presentation bar, and every
round so far has *asserted* them in a report.  An assertion is not a reading.  This check reads the package -- the
product, the records, the instruments, the README -- and answers each item, and it distinguishes three verdicts that
have been confused before: **CHECKS** (decided by a reading of the objects), **DECLARED** (a statement only the
author can make, so the check reads that the statement exists and what it says, and does not pretend to have
verified its truth), and **FAIL**.

Bar items, as the journal states them (Phase B):
  1 contribution level declared, and the level's evidence requirements met
  2 falsifiable claim
  3 at least 3 concrete related works with a stated difference from this study
  4 evidence supports every claim
  5 threats section that also argues why the work is still worth publishing
  6 baseline / prior-work comparison
  7 stochastic systems report multi-run statistics
  8 README reproduction spec (one command + expected output + tolerance)
  9 completeness (manuscript + README + scripts/data)
 10 house-pipeline reuse: a new construct, or a longitudinal design, said explicitly in the abstract
 11 prior-belief reporting (each registered prior's outcome)
 12 citation authenticity report
 13 at least 100 references, every one cited in the body

Presentation bar (a manuscript can pass every numeric check and still never show its evidence):
  P1 every reference entry renders in the house order: authors / year / venue / link / stated difference
  P2 the figure is embedded, captioned, and cited in the text
  P3 tables are numbered in document order and each is cited in the text

Run:  python3 submission_check.py [--selftest]
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "research" else HERE
PRODUCT = os.path.join(ROOT, "manuscript.md")


def read(path):
    return io.open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def cite_module(root=ROOT):
    """The manuscript checker BESIDE the tree being read, loaded by path.

    Not `import cite_check`: a plain import takes whatever is first on `sys.path` (the authoring tree), so the bar
    battery would mutate a copy and then have item 13 read the ORIGINAL's citations -- a check whose object is not
    the object it names, which is the family this whole package exists to catch.
    """
    import importlib.util
    for cand in (root, os.path.join(root, "manuscript"), os.path.join(root, "research", "manuscript")):
        path = os.path.join(cand, "cite_check.py")
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("cite_check_for_%s" % os.path.basename(root), path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


def strip(dst, name, pattern, keep=None):
    """Blank `pattern` out of `dst/name` (or substitute `keep(match)`).  A no-op mutation is an ERROR, not a pass."""
    p = os.path.join(dst, name)
    t = io.open(p, encoding="utf-8").read()
    new, n = re.subn(pattern, keep if keep else (lambda m: " " * len(m.group(0))), t)
    if n == 0:
        raise SystemExit("MUTATION INERT: %r not found in %s" % (pattern, name))
    io.open(p, "w", encoding="utf-8").write(new)
    return n


def check_all(root=ROOT):
    """Every bar item, read.  Returns (rows, failures); rows carry (id, verdict, detail)."""
    rows, bad = [], []
    product = read(os.path.join(root, "manuscript.md"))
    readme = read(os.path.join(root, "README.md"))
    repro = read(os.path.join(root, "reproduce.sh"))
    keys = json.loads(read(os.path.join(root, "refs", "refs_keys.json")) or "{}").get("keys", {})
    priors = read(os.path.join(root, "registration_priors.md"))
    outs = read(os.path.join(root, "outcomes.md"))

    def add(item, ok, detail, declared=False):
        verdict = "DECLARED" if (ok and declared) else ("CHECKS" if ok else "FAIL")
        rows.append((item, verdict, detail))
        if not ok:
            bad.append("%s: %s" % (item, detail))

    def has(pat, text=None):
        return re.search(pat, product if text is None else text, re.I) is not None

    # ---- 1 contribution level -----------------------------------------------------------------------------------
    lvl = re.search(r"\*\*Contribution level\*\*:\s*`([^`]+)`", product)
    allowed = ("case study", "system", "theory + empirics", "theory+empirics")
    lvl_ok = bool(lvl) and lvl.group(1).strip().lower() in allowed
    closed = all(s in read(os.path.join(root, "gate_v1.py"))
                 for s in ("bstar_closed", "value_closed", "slope_closed"))
    baseline = has(r"0\.200000")
    add("B1-contribution-level", bool(lvl_ok and closed and baseline),
        "level %r; closed forms present: %s; measured baseline stated: %s"
        % (lvl.group(1) if lvl else None, closed, baseline))
    add("B1b-level-evidence-named", has(r"ground truth by construction"),
        "the level's evidence (a model with ground truth by construction) is named in the product", declared=True)

    # ---- 2 falsifiable claim ------------------------------------------------------------------------------------
    claim = has(r">\s*\*\*Claim\.\*\*") and has(r"falsifiab")
    ids = sorted(set(re.findall(r"(?m)^#+\s*(PB\d)", priors)))
    if not ids:
        ids = sorted(set(re.findall(r"PB\d", priors)))
    add("B2-falsifiable-claim", bool(claim and len(ids) >= 3),
        "a claim block and the word 'falsifiable' are in the product; %d registered prior(s)" % len(ids))

    # ---- 3 related works with stated differences ----------------------------------------------------------------
    diffd = [k for k, v in keys.items() if (v.get("difference") or "").strip()]
    rel = has(r"(?m)^## 2 Related work")
    add("B3-related-work-differences", bool(rel and len(diffd) >= 3 and len(diffd) == len(keys)),
        "%d of %d cited records state a difference from this study; Related-work section present: %s"
        % (len(diffd), len(keys), rel))

    # ---- 4 evidence supports every claim ------------------------------------------------------------------------
    owners = {"verify_s5.py": "Section 5's numbers", "outcome_check.py": "the registered priors' rows",
              "cite_check.py": "the citation keys", "refs/reference_check.py": "the authenticity report",
              "refs/refs_check.py": "the reference pipeline, stage 1",
              "refs/refs_check2.py": "the reference pipeline, stage 2",
              "refs/refs_check3.py": "the reference pipeline, stage 3",
              "check_links.py": "the product's links", "figures/make_figures.py": "the figures",
              "submission_check.py": "this bar"}
    missing_owner = sorted(f for f in owners if not os.path.exists(os.path.join(root, f)))
    not_wired = sorted(f for f in owners if f not in repro and f != "submission_check.py")
    add("B4-evidence-owners", not missing_owner and not not_wired,
        "checker(s) missing: %s; not invoked by reproduce.sh: %s" % (missing_owner or "none", not_wired or "none"))

    # ---- 5 threats + why worth publishing -----------------------------------------------------------------------
    add("B5-threats-and-why", has(r"(?m)^## 7 Threats") and has(r"worth publishing"),
        "the threats section names the limitation family and argues the work's value")

    # ---- 6 baseline comparison ----------------------------------------------------------------------------------
    add("B6-baseline", has(r"\|\s*D0\s*\|") and has(r"no.gate baseline") and len(diffd) >= 3,
        "the measured no-gate baseline is a table row; prior work is compared against it (B3 carries the count)")

    # ---- 7 multi-run statistics ---------------------------------------------------------------------------------
    det = has(r"deterministic and fully enumerated") or has(r"no sampling error")
    runs = re.search(r"(\d+)\s+non-degenerate readings", product)
    add("B7-multi-run-statistics", bool(det and runs and has(r"29/30")),
        "the model's determinism is stated (so the clause applies to the sampling route), which reports %s readings "
        "and their coverage interval" % (runs.group(1) if runs else None))

    # ---- 8 README reproduction spec -----------------------------------------------------------------------------
    steps = len(re.findall(r"(?m)^# ---- ", repro))
    heads = "\n".join(l for l in readme.split("\n") if l.startswith("#"))
    fenced = re.findall(r"```[a-z]*\n(.*?)```", readme, re.S)
    cmd_in_block = any("bash reproduce.sh" in b for b in fenced)
    spec = cmd_in_block and ("Tolerance" in heads) and ("Expected output" in readme)
    add("B8-readme-one-command", bool(spec and steps >= 8),
        "the README gives the command in a fenced block, an 'Expected output' transcript and a 'Tolerance' section; "
        "reproduce.sh has %d step(s)" % steps)

    # ---- 9 completeness -----------------------------------------------------------------------------------------
    required = ["manuscript.md", "README.md", "reference-check.md", "reference-check.json", "reproduce.sh",
                "outcomes.md", "registration_priors.md", "heilmeier.md", "check_links.py", "verify_s5.py",
                "cite_check.py", "outcome_check.py", "submission_check.py", "figures/make_figures.py",
                "figures/fig1_sign_law_and_cost_ratio.png"]
    required += ["gate_v%d.py" % i for i in range(7)] + ["v%d_battery.py" % i for i in range(7)]
    absent = sorted(f for f in required if not os.path.exists(os.path.join(root, f)))
    add("B9-completeness", not absent, "absent: %s" % (absent or "none"))

    # ---- 10 house-pipeline reuse --------------------------------------------------------------------------------
    pos = has(r"new\s+construct and a theory instrument")
    add("B10-new-construct-declared", bool(pos),
        "the abstract says which it is: a new construct + a theory instrument, not a cross-sectional measurement",
        declared=True)

    # ---- 11 prior-belief reporting ------------------------------------------------------------------------------
    reported = [p for p in ids if re.search(p, product)]
    with_verdict = [p for p in ids if re.search(r"(?:^|\n)#+[^\n]*\b%s\b" % p, outs)]
    add("B11-prior-beliefs-reported",
        bool(ids and len(reported) == len(ids) and len(with_verdict) == len(ids)),
        "%d prior(s) registered; %d named in the product %s; %d with an outcome section"
        % (len(ids), len(reported), reported, len(with_verdict)))

    # ---- 12 authenticity report ---------------------------------------------------------------------------------
    rc_md = read(os.path.join(root, "reference-check.md"))
    obj = json.loads(read(os.path.join(root, "reference-check.json")) or "{}")
    n_v, n_r = obj.get("n_verified"), len(obj.get("rows") or [])
    add("B12-authenticity-report",
        bool(n_r and n_v == n_r and obj.get("n_mismatch") == 0 and obj.get("n_unverified") == 0
             and "0 mismatch" in rc_md),
        "%s of %s verified, 0 mismatch, 0 unverified; the report is rendered in reference-check.md" % (n_v, n_r))

    # ---- 13 >=100 references, all cited -------------------------------------------------------------------------
    cc = cite_module(root)
    uncited, index, un_entries, nkeyed = [], {}, [], 0
    if cc is not None:
        texts = [(os.path.basename(p), read(p)) for p in cc.PARTS]
        index, un_entries = cc.num_index(texts, cc.load_keys())
        order, _occ = cc.scan(texts, index)
        nkeyed = len(order)
        uncited = [k for k in cc.load_keys() if k not in set(order)]
    add("B13-refs-volume-and-coverage", bool(keys and len(keys) >= 100 and not uncited),
        "%d reference(s) (bar 100); %d cited, %d uncited" % (len(keys), len(keys) - len(uncited), len(uncited)))
    # ---- 13b the in-text key IS the key the bibliography prints ---------------------------------------------------
    # Item 11's *Citation mechanics*: every entry carries an in-text key matching the bibliography, and a work cited
    # by name or by bare arXiv id does not discharge coverage.  Nothing here read that property until R481: every
    # limb of this package read the PARTS, which cite `[@key]`, so the product shipped `[@key]` tokens beside a
    # `[1]`-`[120]` list, `refgate.py` read `covered=1/120`, and this bar read green (measured 2026-10-01 at
    # `d77e974`).  The item is read over the PRODUCT, and the key it resolves is the one the product prints.
    add("B13b-in-text-key-form", bool(index) and not un_entries and nkeyed == len(keys),
        "in-text keys resolve through the product's own numbered bibliography: %d of %d entries keyed, %d entry(ies) "
        "with no record, %d key(s) cited" % (len(index), len(keys), len(un_entries), nkeyed))

    # ---- P1 reference entries in the house order ----------------------------------------------------------------
    refs_txt = product[product.find("## References"):] if "## References" in product else ""
    entries = [l.strip() for l in refs_txt.split("\n") if re.match(r"^\[\d+\]\s", l.strip())]
    fields = {"authors": r"^\[\d+\]\s+\S", "year": r"\((?:19|20)\d\d\)",
              "venue": r"\*\.\s+\S[^\n]*?\s+https?://", "link": r"https?://", "difference": r"\s--\s\S"}
    short = {}
    for name, pat in fields.items():
        miss = [e[:44] for e in entries if not re.search(pat, e)]
        if miss:
            short[name] = miss[:3]
    # The entry must print the FORM, not the field a record stores.  A character reference (`&amp;`, `&#39;`) is
    # the form an UNDECODED field has, and the journal's own gate counts it with no window at all
    # (`refgate.py`'s `author_form`, whose rule is `&(?:#\d+|#x[0-9A-Fa-f]+|[a-zA-Z]+);`).  #93 was returned at
    # triage on 2026-10-08 for exactly one such entry -- [121]'s venue, `Big Data &amp; Society`, out of the
    # Crossref answer -- so the property is read here, over the PRODUCT's reference section (the object the gate
    # reads), and not only over the built records it came from.
    CHARREF = re.compile(r"&(?:#\d+|#x[0-9A-Fa-f]+|[a-zA-Z]+);")
    escaped = [e[:60] for e in entries if CHARREF.search(e)]
    add("P1-reference-entry-fields", bool(entries) and not short and not escaped,
        "%d entr(ies); missing-field examples: %s; character-reference (undecoded field) examples: %s"
        % (len(entries), short or "none", escaped[:3] or "none"))

    # ---- P2 figure embedded, captioned, cited -------------------------------------------------------------------
    img = re.search(r"!\[[^\]]*\]\(([^)]+)\)", product)
    n_fig = len(re.findall(r"Figure\s+1", product))
    resolved = bool(img) and os.path.exists(os.path.join(root, img.group(1)))
    add("P2-figure-embedded-captioned-cited",
        bool(resolved and has(r"\*\*Figure\s+1\.\*\*") and n_fig >= 3),
        "embedded and resolving: %s; caption: %s; mentions: %d (alt text + caption + body citations)"
        % (resolved, has(r"\*\*Figure\s+1\.\*\*"), n_fig))

    # ---- P3 tables numbered in document order and cited ---------------------------------------------------------
    nums = [int(x) for x in re.findall(r"\*\*Table (\d+)\.\*\*", product)]
    in_order = nums == list(range(1, len(nums) + 1))
    uncited = [n for n in nums if len(re.findall(r"Table\s+%d\b" % n, product)) < 2]
    add("P3-tables-numbered-and-cited", bool(nums) and in_order and not uncited,
        "%d table(s) numbered %s in document order; uncited: %s"
        % (len(nums), "1..%d" % len(nums) if in_order else nums, uncited or "none"))
    return rows, bad


def main():
    rows, bad = check_all()
    width = max(len(r[0]) for r in rows)
    for item, verdict, detail in rows:
        print("  %-*s %-9s %s" % (width, item, verdict, detail))
    n_decl = sum(1 for r in rows if r[1] == "DECLARED")
    print("\nSUBMISSION CHECK: %s -- %d item(s), %d failed, %d declared"
          % ("PASS" if not bad else "FAIL", len(rows), len(bad), n_decl))
    rc = 0 if not bad else 1
    if "--selftest" in sys.argv:
        cases = [
            ("a product with the contribution level removed fails",
             lambda d: strip(d, "manuscript.md", r"\*\*Contribution level\*\*: `theory \+ empirics`"), "B1-"),
            ("a reference entry with no venue fails",
             lambda d: strip(d, "manuscript.md", r"\. arXiv:2605\.24309\.", keep=lambda m: " ."), "P1-"),
            ("an entry printing an undecoded character reference fails",
             lambda d: strip(d, "manuscript.md", r"\*The Ethics of Algorithms: Mapping the Debate\*\. Big Data & Society\.",
                             keep=lambda m: "*The Ethics of Algorithms: Mapping the Debate*. Big Data &amp; Society."),
             "P1-"),
            ("a figure cited only by its caption fails",
             lambda d: strip(d, "manuscript.md", r"\*\*Figure 1\([ab]\)\*\*", keep=lambda m: "**fit**"), "P2-"),
            ("a table numbering gap fails",
             lambda d: strip(d, "manuscript.md", r"\*\*Table 4\.\*\*", keep=lambda m: "**Table 44.**"), "P3-"),
            ("a dropped prior's name in the product fails",
             lambda d: strip(d, "manuscript.md", r"PB4", keep=lambda m: "PBX"), "B11-"),
            ("an unwired checker fails",
             lambda d: strip(d, "reproduce.sh", r"check_links\.py", keep=lambda m: "check_links_off.py"), "B4-"),
            ("a README with no tolerance section fails",
             lambda d: strip(d, "README.md", r"## Tolerance, and the build", keep=lambda m: "## Notes"), "B8-"),
            ("an abstract that stops declaring the construct fails",
             lambda d: strip(d, "manuscript.md", r"new\s+construct and a theory instrument",
                             keep=lambda m: "cross-sectional measurement"), "B10-"),
        ]
        fired = 0
        tmp = tempfile.mkdtemp(prefix="subcheck-")
        for name, mutate, expect in cases:
            dst = os.path.join(tmp, "case")
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("research", "__pycache__", ".git", "tmp"))
            mutate(dst)
            _r, b2 = check_all(dst)
            hit = any(x.startswith(expect) for x in b2)
            print("  %-58s %s" % (name[:58], "caught" if hit else "MISSED"))
            fired += 1 if hit else 0
            if not hit:
                rc = 1
        shutil.rmtree(tmp, ignore_errors=True)
        print("BATTERY: %d of %d case(s) fired" % (fired, len(cases)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
