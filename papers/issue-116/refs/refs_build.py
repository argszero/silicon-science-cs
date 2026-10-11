#!/usr/bin/env python3
"""Issue #116 -- build the numbered reference list, number the manuscript's
citations, and CHECK COVERAGE.

Numbering rule: entries are ordered by ROLE (R1..R10) and then by identifier, and
the manuscript cites by identifier, so a number can never drift from its entry.

Three duties:
  1. number   -- assign [N] to every curated entry
  2. render   -- write the References section, each entry with a difference clause
  3. check    -- coverage: every entry cited, every in-text key curated, and the
                 count >= the journal's floor. Fails (exit 1) if either side is
                 empty-of-the-other, so it is a check rather than a statement.

Usage:
    python3 refs_build.py check     # coverage only, exit non-zero on failure
    python3 refs_build.py render    # write manuscript_numbered.md (citations -> [N])
"""
import hashlib
import json
import os
import re
import sys

KEYS = "refs/refs_keys.json"
MS = "manuscript.src.md"
OUT = "manuscript.md"
MIN_REFS = 100
MARKER = ("## References\n\n(Generated from the pipeline; full verification table"
          " in reference-check.md.)")

ROLE_ORDER = ["R1_chunked_policy_horizon", "R2_policy_latency_efficiency",
              "R3_delay_networked_sampled_data", "R4_staleness_anytime_imprecise",
              "R5_receding_horizon_and_horizon_length", "R6_lqg_lyapunov_covariance",
              "R7_abstraction_options_macro", "R8_amortization_and_compute",
              "R9_disturbance_and_saturation", "R10_setting_control_and_manipulation"]

DIFF = {
    "R1_chunked_policy_horizon":
        "fixes, schedules or improves the execution horizon rather than deriving its boundary",
    "R2_policy_latency_efficiency":
        "lowers the per-query price; we decide how much inference to buy at that price",
    "R3_delay_networked_sampled_data":
        "treats delay as a stability constraint on a fixed controller; here delay is the age of the observation under a priced query",
    "R4_staleness_anytime_imprecise":
        "prices observation freshness or computation time exogenously; here the staleness is produced by the decision variable itself",
    "R5_receding_horizon_and_horizon_length":
        "bounds the horizon by prediction quality and a terminal cost; our window ends at a real-time floor and a stability-margin ceiling",
    "R6_lqg_lyapunov_covariance":
        "used here as the exact instrument (ground truth), not as a contribution",
    "R7_abstraction_options_macro":
        "amortizes a learned decision over a span, not a priced query over a commit horizon",
    "R8_amortization_and_compute":
        "amortizes a modelling or learning cost, not a per-query price",
    "R9_disturbance_and_saturation":
        "characterises the nonlinearity; we use it to break the second-moment equivalence that hides the disturbance channel",
    "R10_setting_control_and_manipulation":
        "evaluates a policy or a platform; we evaluate a deployment parameter common to all of them",
}

TOKEN = re.compile(r"\[\[(.*?)\]\]", re.S)   # a cluster: [[a]] or [[a], [b]]
IDRE = re.compile(r"\d{4}\.\d{4,5}|10\.\d{4,}/[^\s\]]+")


def load():
    data = json.load(open(KEYS))
    keys = data["keys"]
    order = []
    for role in ROLE_ORDER:
        for i in sorted(k for k, v in keys.items() if v["role"] == role):
            order.append(i)
    extra = sorted(k for k in keys if k not in order)
    order += extra
    num = {i: n + 1 for n, i in enumerate(order)}
    return keys, order, num


def cite(txt, num):
    def rep(m):
        ids = IDRE.findall(m.group(1))
        return "[" + ", ".join(str(num[i]) for i in ids) + "]"
    return TOKEN.sub(rep, txt)


def fmt_author(a):
    """One author in the house form `Family, I.`

    The record is the source; the split is only DERIVED where the record does not
    give it. arXiv's API states one unstuffed token in "Given Family" order and its
    abstract page states the same author as "Family, Given" -- the two carriers of
    one record differ in order, so the comma decides which form is in hand and the
    last token is the family only when there is no comma. A name the record gives as
    one token prints as that token (`Student.`), never padded to `Family, I.`.
    """
    fam, giv = a.get("family"), a.get("given")
    if not fam:
        s = (a.get("name") or "").strip()
        if "," in s:
            fam, giv = s.split(",", 1)
        else:
            toks = s.split()
            fam, giv = ((toks[-1], " ".join(toks[:-1])) if toks else ("", ""))
        if fam and fam.isupper() and len(fam) > 1:      # the registry's stored form
            fam = fam.title()                            # O'BRIEN -> O'Brien
    fam = (fam or "").strip()
    giv = giv or ""
    initials = " ".join(f"{p[0].upper()}." for tok in giv.split()
                        for p in tok.split("-") if p)
    return f"{fam}, {initials}".rstrip(", ").strip() if initials else fam


def author_str(authors):
    """The entry's author component, or None when the record carries no author.

    `et al.` for four or more (the first three then `; et al.`), all of them for
    two or three, one for one -- the house style the published manuscripts hold.
    """
    parts = [p for p in (fmt_author(a) for a in authors or []) if p]
    if not parts:
        return None
    if len(parts) >= 4:
        return "; ".join(parts[:3]) + "; et al."
    return "; ".join(parts)


def ident_of(i, r):
    return f"DOI {r['doi']}" if r.get("doi") else f"arXiv:{i}"


def url_of(i, r):
    return (f"https://doi.org/{r['doi']}" if r.get("doi")
            else f"https://arxiv.org/abs/{i}")


def year_of(r):
    y = r.get("verified_year") or r.get("published") or r.get("verified_published")
    return str(y)[:4] if y else None


def entry_line(i, r, num):
    """The ONE carrier of an entry's printed form. render() and render_check() both
    call it, so the committed product and the checked product cannot drift apart."""
    title = r.get("verified_title") or r.get("title")
    if not title:
        raise SystemExit(f"entry {i} has no title: run `refs_tool.py verify` first")
    au = author_str(r.get("verified_authors"))
    if au is None:
        # The rule's exception: a work whose RECORD carries no author. The position
        # is never left silently empty and never filled by guesswork -- the absence
        # is RECORDED, naming the record that was read (the same line stands in
        # reference-check.md).
        au = ("author not established on the record read for this identifier"
              f" [{ident_of(i, r)}]")
    yr = year_of(r) or "n.d."
    return (f"[{num[i]}] {au} ({yr}). {title}. {ident_of(i, r)}. {url_of(i, r)}"
            f" - Difference from this work: {DIFF[r['role']]}.")


def render():
    keys, order, num = load()
    ms = open(MS).read()
    body = cite(ms, num)
    lines = ["## References", ""]
    for i in order:
        lines.append(entry_line(i, keys[i], num))
        lines.append("")
    if MARKER not in body:
        raise SystemExit("the source manuscript has no REFERENCES marker")
    body = body.replace(MARKER, "\n".join(lines).rstrip())
    open(OUT, "w").write(body)
    print(f"wrote {OUT}: {len(body)} chars, {len(order)} numbered references")
    check()


def check():
    bad = False                    # must be initialised BEFORE any branch sets it,
                                   # or a later `bad = False` erases the fault
    keys, order, num = load()
    ms = open(MS).read()
    body = ms
    used_tokens = TOKEN.findall(body)
    used = set()
    for tk in used_tokens:
        used.update(IDRE.findall(tk))
    if not used:
        raise SystemExit("COVERAGE FAIL: the manuscript cites nothing")
    # A number typed into the BODY is a claim whose referent can move: the body must
    # cite by identifier, so a literal [N] in the body is a defect even when it
    # currently points at the right entry.
    body_only = body[:body.index("## References")] if "## References" in body else body
    literal = re.findall(r"(?<!\[)\[\d+(?:\s*,\s*\d+)*\]", body_only)
    if literal:
        print(f"  LITERAL CITATION in the body: {literal[:6]}  -> cite by identifier")
        bad = True
    uncited = sorted(set(keys) - used)
    uncurated = sorted(used - set(keys))
    print(f"entries={len(keys)}  cited={len(used)}  "
          f"uncited={len(uncited)}  uncurated={len(uncurated)}")
    for i in uncited:
        print(f"  UNCITED  {i}  ({keys[i]['role']})")
        bad = True
    for i in uncurated:
        print(f"  UNCURATED {i}  (cited in the text but not in refs_keys.json)")
        bad = True
    if len(keys) < MIN_REFS:
        print(f"  TOO FEW  {len(keys)} < {MIN_REFS}")
        bad = True
    # The CITATION REPORT states the product's digest, and until this round no step read
    # that copy: the manuscript could be rebuilt and the report would go on quoting the
    # old digest with every check green -- a stated value with no reader (the class R482
    # fixed for this package's counts). So the report's line is compared against the
    # file the pipeline just built, not against a literal typed here.
    rc_path = "reference-check.md"
    if not os.path.exists(rc_path):
        print(f"  MISSING: {rc_path} (its stated digest cannot be read)")
        bad = True
    else:
        m = re.search(r"`manuscript\.md` sha256 `([0-9a-f]{64})`", open(rc_path).read())
        dig = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
        if not m:
            print(f"  {rc_path} states no `manuscript.md` sha256")
            bad = True
        elif m.group(1) != dig:
            print(f"  {rc_path} states the digest {m.group(1)[:16]}... but the built"
                  f" {OUT} is {dig[:16]}...")
            bad = True
        else:
            print(f"  {rc_path} states the built product's digest ({dig[:16]}...)")
    if bad:
        sys.exit(1)
    print(f"COVERAGE OK: all {len(keys)} entries cited, all in-text keys curated,"
          f" and {len(keys)} >= {MIN_REFS}")


def render_check():
    """The COMMITTED manuscript.md must equal what the render produces from
    manuscript.src.md -- otherwise the file a reader reads is not the file the
    pipeline builds."""
    keys, order, num = load()
    built = cite(open(MS).read(), num)
    lines = ["## References", ""]
    for i in order:
        lines.append(entry_line(i, keys[i], num))
        lines.append("")
    if MARKER not in built:
        print("  RENDER MISMATCH: the source has no REFERENCES marker")
        sys.exit(1)
    built = built.replace(MARKER, "\n".join(lines).rstrip())
    committed = open(OUT).read()
    if built != committed:
        print(f"  RENDER MISMATCH: committed {OUT} ({len(committed)} chars) != built"
              f" ({len(built)} chars)")
        sys.exit(1)
    print(f"RENDER OK: the committed {OUT} equals the built product"
          f" ({len(committed)} chars, {len(order)} references)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        check()
    elif cmd == "render":
        render()
    elif cmd == "render-check":
        render_check()
    else:
        raise SystemExit("use check|render|render-check")
