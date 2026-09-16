#!/usr/bin/env python3
"""The SUPPORT limb of citation integrity, for issue #47's manuscript.

A citation owes TWO relations, and they are read in different places:

  * IDENTITY -- the record is the work the entry names.  Read in the LIST, by
    `refs_resolve_v1.py`, which compares the returned year / venue / authors against the entry's own
    line and prints `identity-exact` or `identity-ok`.

  * SUPPORT -- the work the entry names is the work the claim at its in-text key needs.  Read in the
    TEXT: the sentence the key sits in, and whether that work can carry it.  A record can be real,
    correctly identified by every field, and still unable to carry the sentence it is cited for.

This file is the second limb, read PER OCCURRENCE and not per key: the same work cited in two
sentences is two support questions, and a per-key read hides the one that fails.  (Measured on the
committed manuscript: 147 cited keys, 221 occurrences, 52 keys cited in more than one sentence.)

THE ROW IDENTITY IS THE TEXT, NOT A COORDINATE.  A row is identified by (part, key, digest of the
sentence).  Line numbers are printed but never identify: an earlier version keyed rows by
`part:line:key`, and then inserting one sentence re-keyed every row below it -- 41 rows went from
bound to unread, which is a defect in the instrument and not in the readings.  With the text as the
identity, an unrelated edit moves nothing, and an edit to a cited sentence makes the row and its
occurrence fail to match -- which is exactly the signal, and is reported as a pair.

The reading is a human judgement; the mechanisable half is the BINDING.  Verdicts live in
`support_verdicts_v1.json` as (role, verdict, basis) against the sentence VERBATIM, and `--check`
verifies that the committed text still contains that sentence at that key.  `--bind` is the
authoring act that records the quote and is never performed by `--check`.

Usage:
    python3 support_read_v1.py --check                   # verify the limb (read-only)
    python3 support_read_v1.py --bind                    # record the quotes the reads were made on
    python3 support_read_v1.py --build [--out DIR]       # write support_read_v1.json + support-read.md
    python3 support_read_v1.py --selftest                # mutation battery: every check must fail

Exit status: 0 only when every cited occurrence is read, every read binds, and none is unsupported.
"""
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = ["manuscript_part1.md", "manuscript_part2.md", "manuscript_part3.md"]
VERDICTS = "support_verdicts_v1.json"
OUT_JSON = "support_read_v1.json"
OUT_MD = "support-read.md"
ROLES = ("origin", "instance-of-set", "bound-source", "method-source", "baseline", "survey",
         "contrast", "systems-evidence", "instrument-anchor")
VERDICT_VALUES = ("supports", "unsupported")
CITE = re.compile(r"\[@([A-Za-z0-9_.:-]+)\]")
ABBR = ("e.g.", "i.e.", "cf.", "Fig.", "Eq.", "al.", "vs.", "etc.", "Sec.", "no.", "approx.")
MIN_BASIS_WORDS = 5


def pkgdir():
    """The directory holding the manuscript parts.

    This file lives in the package's `research/` (git-ignored) while the parts are committed one
    level up, so the parts are looked for where they actually are rather than assumed.  Reading the
    wrong directory is fail-closed: `check` reports "read nothing" instead of passing.
    """
    if any(os.path.exists(os.path.join(HERE, p)) for p in PARTS):
        return HERE
    return os.path.dirname(HERE)


def paragraphs(text):
    """Yield (first_line_number, paragraph) with wrapped lines joined."""
    out, buf, start = [], [], None
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip():
            if start is None:
                start = i
            buf.append(line.strip())
        elif buf:
            out.append((start, " ".join(buf)))
            buf, start = [], None
    if buf:
        out.append((start, " ".join(buf)))
    return out


def sentences(para):
    """Split a paragraph into sentences, guarding known abbreviations."""
    guard = para
    for a in ABBR:
        guard = guard.replace(a, a.replace(".", "\x00"))
    parts = re.split(r"(?<=[.;:])\s+(?=[A-Z*`\(])", guard)
    return [p.replace("\x00", ".").strip() for p in parts if p.strip()]


def digest(sentence):
    return hashlib.sha1(sentence.encode("utf-8")).hexdigest()[:12]


def rid_of(part_key, key, sentence):
    return "%s:%s:%s" % (part_key, key, digest(sentence))


def occurrences(pkg):
    """Every citation occurrence: content identity, key, sentence, and the line it sits on."""
    rows = []
    for p in sorted(PARTS):
        path = os.path.join(pkg, p)
        if not os.path.exists(path):
            continue
        m = re.search(r"part(\d)", p)
        kp = "rt" + (m.group(1) if m else p)
        text = io.open(path, encoding="utf-8").read()
        for start, para in paragraphs(text):
            for s in sentences(para):
                for k in CITE.findall(s):
                    rows.append({"id": rid_of(kp, k, s), "part": p, "part_key": kp, "line": start,
                                 "key": k, "sentence": s})
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        # Two identical sentences citing the same key are the same claim twice; the identity is the
        # text, so they are one row, and the duplication is reported rather than hidden.
        seen, uniq = set(), []
        for r in rows:
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            uniq.append(r)
        rows = uniq
    return rows


def load(data_dir):
    with io.open(os.path.join(data_dir, VERDICTS), encoding="utf-8") as fh:
        return json.load(fh)


def check(pkg, data_dir=None, quiet=False):
    """Return (failures, stats).  Every failure names the object it read."""
    fail, note = [], []
    occ = occurrences(pkg)
    by_id = {o["id"]: o for o in occ}
    data = load(data_dir or pkg)
    rows = data.get("rows") or {}
    for r in (data.get("roles") or {}):
        if r not in ROLES:
            fail.append("undeclared role %r in %s" % (r, VERDICTS))
    unread = [i for i in by_id if i not in rows]
    orphan = [i for i in rows if i not in by_id]

    def key_of(rid):
        return rid.split(":", 2)[1] if rid.count(":") >= 2 else rid

    # Pair an orphan with an unread occurrence of the SAME key, when that pairing is unambiguous:
    # one row and one occurrence differ only in their text, which means the cited sentence was
    # edited and the read must be re-made.  Anything else is reported as itself.
    o_by_key, u_by_key = {}, {}
    for i in orphan:
        o_by_key.setdefault(key_of(i), []).append(i)
    for i in unread:
        u_by_key.setdefault(key_of(i), []).append(i)
    paired = set()
    for k in sorted(set(o_by_key) & set(u_by_key)):
        if len(o_by_key[k]) == 1 and len(u_by_key[k]) == 1:
            oi, ui = o_by_key[k][0], u_by_key[k][0]
            paired.update((oi, ui))
            fail.append("%s: the sentence at this key was edited, so the read no longer binds it.\n"
                        "      read  : %r\n      in text: %r\n      -> re-read this occurrence"
                        % (k, (rows[oi].get("sentence") or "")[:90], by_id[ui]["sentence"][:90]))
    for i in unread:
        if i not in paired:
            fail.append("%s: cited but never read (%r)" % (i, by_id[i]["sentence"][:70]))
    for i in orphan:
        if i not in paired:
            fail.append("%s: a read whose sentence is no longer in the manuscript (the citation was "
                        "edited out or the row is stale): %r"
                        % (i, (rows[i].get("sentence") or "")[:70]))

    n_sup = n_uns = 0
    for rid, row in sorted(rows.items()):
        v = row.get("verdict", "")
        if v not in VERDICT_VALUES:
            fail.append("%s: verdict %r is not one of %s" % (rid, v, list(VERDICT_VALUES)))
            continue
        if row.get("role") not in ROLES:
            fail.append("%s: role %r is not a declared role" % (rid, row.get("role")))
        basis = (row.get("basis") or "").strip()
        if len(basis.split()) < MIN_BASIS_WORDS:
            fail.append("%s: basis is empty or too short to be a read (%r)" % (rid, basis[:40]))
        if not row.get("sentence"):
            fail.append("%s: the row records no sentence, so nothing binds it to the text" % rid)
        if v == "unsupported":
            n_uns += 1
            fail.append("%s: UNSUPPORTED -- the work at this key cannot carry its sentence (%s)"
                        % (rid, (row.get("why") or basis)[:110]))
            note.append("%s  [%s]  %s" % (rid, row.get("role"),
                                          (row.get("why") or row.get("basis"))[:120]))
        else:
            n_sup += 1
    if not occ:
        fail.append("no citation occurrences found: the check read nothing")
    rep, rdetail = report_current(pkg, data_dir or pkg, occ=occ)
    fail += rep
    return fail, {"occurrences": len(occ), "keys": len({o["key"] for o in occ}),
                  "report": rdetail,
                  "supports": n_sup, "unsupported": n_uns,
                  "unread": len(unread), "orphan_rows": len(orphan),
                  "unsupported_list": note, "rows": len(rows)}


def bind(pkg, data_dir):
    """Record, in the readings file, the sentence each read was made against.

    Binding is an AUTHORING act and `--check` never performs it: the quote is what makes an edit
    visible, so a tool that silently re-quoted the text would erase the only check that a reading
    still refers to the sentence it was made on.
    """
    path = os.path.join(data_dir, VERDICTS)
    data = json.load(io.open(path, encoding="utf-8"))
    rows = data["rows"]
    occ = {o["id"]: o for o in occurrences(pkg)}
    # a read may carry a stale identity after an edit; re-key it onto the occurrence whose key
    # matches, when that is unambiguous, and say so
    rekeyed = exact = 0
    for rid in list(rows):
        if rid in occ:
            continue
        row = rows[rid]
        # The recorded QUOTE is the anchor, and the fields of the stale id only disambiguate: an
        # earlier identity put the key last and this one puts it second, so reading a fixed position
        # was the defect that made the first migration move nothing.
        fields = set(rid.split(":"))
        hit = [o for o in occ.values()
               if row.get("sentence") and o["sentence"] == row["sentence"] and o["key"] in fields]
        if len(hit) == 1:
            rows[hit[0]["id"]] = rows.pop(rid)
            exact += 1
            continue
        # otherwise: unambiguous by key alone, where exactly one field of the id is a cited key
        kk = [f for f in fields if any(o["key"] == f for o in occ.values())]
        if len(kk) == 1:
            cands = [o for o in occ.values() if o["key"] == kk[0] and o["id"] not in rows]
            if len(cands) == 1:
                rows[cands[0]["id"]] = rows.pop(rid)
                rekeyed += 1
    newly = moved = 0
    for rid, row in rows.items():
        o = occ.get(rid)
        if o is None:
            continue
        if row.get("sentence") != o["sentence"]:
            moved += 0 if row.get("sentence") is None else 1
            newly += 1 if row.get("sentence") is None else 0
            row["sentence"] = o["sentence"]
    io.open(path, "w", encoding="utf-8").write(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print("bind: %d row(s) re-keyed by their quote, %d by key alone, %d newly bound, %d re-bound "
          "(quote changed), %d of %d occurrence(s) still unread"
          % (exact, rekeyed, newly, moved, len(set(occ) - set(rows)), len(occ)))
    return newly, moved


def report_current(pkg, data_dir, occ=None):
    """Return (problems, detail): does the SHIPPED report equal what a fresh build writes?

    A limb can be read correctly and its REPORT still be stale -- R344 left exactly that: the rows
    grew to 156 keys / 237 occurrences while `support-read.md` still reported the previous round's
    147 / 221, and every other check passed.  A reviewer reads the report, so the report is compared
    against the generator's own output rather than trusted to have been regenerated by hand.  A
    directory that ships no report is SKIPPED, not failed: the selftest runs this on synthetic
    directories, and reproduce.sh's digest block is what catches a MISSING file.
    """
    import tempfile
    problems, detail = [], {}
    with tempfile.TemporaryDirectory() as td:
        try:
            build(pkg, data_dir, out_dir=td)
        except SystemExit as e:
            # A build refuses exactly when a row is unread or orphaned, and the row-level checks
            # already fail on that, naming the occurrence.  Reporting it here as well would make
            # one defect produce two failures and a mutation case look like a different defect.
            detail["build"] = "refused (%s)" % e
            return [], detail
        for name in (OUT_MD, OUT_JSON):
            shipped = os.path.join(data_dir, name)
            if not os.path.exists(shipped):
                detail[name] = "not shipped here"
                continue
            have = io.open(shipped, encoding="utf-8").read()
            fresh = io.open(os.path.join(td, name), encoding="utf-8").read()
            if have == fresh:
                detail[name] = "current"
            else:
                detail[name] = "STALE"
                problems.append(
                    "%s is STALE: it does not match a fresh build from the rows -- the limb was "
                    "read but its report was never regenerated (run: python3 support_read_v1.py "
                    "--build)" % name)
    return problems, detail


def build(pkg, data_dir, out_dir=None):
    out_dir = out_dir or data_dir
    data = load(data_dir)
    rows = data["rows"]
    occ = occurrences(pkg)
    for rid in sorted(set(rows) - {o["id"] for o in occ}):
        raise SystemExit("cannot build: a read whose sentence is no longer in the manuscript: %s" % rid)
    recs = []
    for o in occ:
        row = rows.get(o["id"])
        if row is None:
            raise SystemExit("cannot build: no read for %s" % o["id"])
        recs.append(dict(o, role=row["role"], verdict=row["verdict"],
                         basis=row["basis"], why=row.get("why", "")))
    multi = {r["key"] for r in recs if sum(1 for x in recs if x["key"] == r["key"]) > 1}
    js = {"manuscript_parts": [p for p in PARTS if os.path.exists(os.path.join(pkg, p))],
          "occurrences": len(recs), "keys": len({r["key"] for r in recs}),
          "keys_cited_in_more_than_one_sentence": len(multi),
          "supports": sum(1 for r in recs if r["verdict"] == "supports"),
          "unsupported": sum(1 for r in recs if r["verdict"] == "unsupported"),
          "findings": data.get("findings", []),
          "roles": data["roles"], "rows": recs}
    io.open(os.path.join(out_dir, OUT_JSON), "w", encoding="utf-8").write(
        json.dumps(js, indent=1, ensure_ascii=False) + "\n")

    L = ["# Support read for issue #47", "",
         "The second limb of citation integrity: the work each entry names, against the **claim at",
         "the key it is cited for**. Generated by `support_read_v1.py --build` from",
         "`support_verdicts_v1.json`; the sentences are quoted verbatim from the manuscript parts, and",
         "`--check` fails when an edit leaves a read unbound or an occurrence unread.", "",
         "| measure | value |", "|---|---|",
         "| citation occurrences read | %d |" % js["occurrences"],
         "| distinct keys | %d |" % js["keys"],
         "| keys cited in more than one sentence | %d |" % js["keys_cited_in_more_than_one_sentence"],
         "| occurrences that support their sentence | %d |" % js["supports"],
         "| **occurrences that do not** | **%d** |" % js["unsupported"], "",
         "The unit is the OCCURRENCE, not the key: a work cited in two sentences is two support",
         "questions, and a per-key read hides the one that fails.  A row is identified by the text",
         "(part, key, digest of the sentence), never by a line number: a coordinate identity re-keys",
         "every row below an inserted sentence, which is an instrument defect and not a finding.", ""]
    if js["findings"]:
        L += ["## Findings from this read", "",
              "Each was found by reading the sentence at the key, and each was corrected in the",
              "manuscript.  The record is kept because a corrected finding that leaves no trace is",
              "indistinguishable from one that was never made.", ""]
        for f in js["findings"]:
            L += ["* **`%s`**" % f["occurrence"], "  * found: %s" % f["found"],
                  "  * action: %s" % f["action"]]
        L.append("")
    L += ["## The roles, declared", ""]
    for r, meaning in sorted(data["roles"].items()):
        L.append("* `%s` -- %s" % (r, meaning))
    L += ["", "## Every occurrence", "",
          "| key | role | verdict | basis | sentence (verbatim, truncated) |",
          "|---|---|---|---|---|"]
    for r in recs:
        L.append("| `%s` | %s | %s | %s | %s |"
                 % (r["key"], r["role"], r["verdict"], r["basis"].replace("|", "\\|"),
                    r["sentence"][:110].replace("|", "\\|")))
    L += ["", "## The occurrences that did not support their sentence", ""]
    uns = [r for r in recs if r["verdict"] == "unsupported"]
    if not uns:
        L.append("None: every occurrence in the committed manuscript carries its sentence.")
    for r in uns:
        L += ["* `%s` (`%s`) -- %s" % (r["id"], r["key"], r["why"] or r["basis"])]
    io.open(os.path.join(out_dir, OUT_MD), "w", encoding="utf-8").write("\n".join(L) + "\n")
    return js


# --------------------------------------------------------------------------------------
# self-test: the check's own behaviour, verified rather than asserted
# --------------------------------------------------------------------------------------

def selftest():
    import shutil
    import tempfile
    base = HERE
    tmp = tempfile.mkdtemp(prefix="support-selftest-")
    fails, fired = [], {}

    def copy_in(d):
        """Copy the parts and the readings into a throwaway directory (the same files the check reads)."""
        os.makedirs(d, exist_ok=True)
        src_dir = pkgdir()
        for f in PARTS + [VERDICTS]:
            src = os.path.join(src_dir, f)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(d, f))

    def verdicts(d):
        return os.path.join(d, VERDICTS)

    def force_clean(d):
        """Every row supports its sentence, so a failure is attributable to the mutation.

        Without this the battery is confounded: the live manuscript has unsupported occurrences of
        its own, they fail the check, and every mutation looks like it fired on their count alone.
        """
        data = json.load(io.open(verdicts(d), encoding="utf-8"))
        for r in data["rows"].values():
            r["verdict"] = "supports"
        io.open(verdicts(d), "w", encoding="utf-8").write(
            json.dumps(data, indent=1, ensure_ascii=False))

    def edit_verdicts(d, fn):
        data = json.load(io.open(verdicts(d), encoding="utf-8"))
        fn(data["rows"])
        io.open(verdicts(d), "w", encoding="utf-8").write(
            json.dumps(data, indent=1, ensure_ascii=False))

    def case(name, mutate, expect):
        d = os.path.join(tmp, name)
        copy_in(d)
        force_clean(d)
        mutate(d)
        try:
            f, _ = check(d)
        except Exception as e:                       # a crash is a failure of the check too
            f = ["the check raised %s: %s" % (type(e).__name__, e)]
        fired[name] = len(f)
        if len(f) != expect:
            fails.append("%s: %d failure(s), expected exactly %d -- a case must fail for ITS reason:"
                         " %s" % (name, len(f), expect, f[:2]))

    # positive control: a package whose every row supports its sentence passes, and the check read
    # something.  Built by forcing the verdicts, not by using the live manuscript: an unsupported
    # occurrence is a finding about the MANUSCRIPT, and a control that failed because of one would
    # report the manuscript's state as the check's defect.
    d0 = os.path.join(tmp, "clean")
    copy_in(d0)
    force_clean(d0)
    f0, st0 = check(d0)
    fired["clean_positive_control"] = len(f0)
    if f0:
        fails.append("positive control: a package with no unsupported row fails: %s" % f0[:2])
    if st0["occurrences"] == 0 or st0["rows"] == 0:
        fails.append("positive control: the check read nothing (occurrences=%d, rows=%d)"
                     % (st0["occurrences"], st0["rows"]))
    case("clean_positive_control_repeated", lambda d: None, expect=0)

    def drop_a_row(rows):
        rows.pop(sorted(rows)[0])
    def blank_a_verdict(rows):
        rows[sorted(rows)[0]]["verdict"] = ""
    def blank_a_basis(rows):
        rows[sorted(rows)[0]]["basis"] = ""
    def orphan_row(rows):
        rows["rt9:notcited:%s" % ("0" * 12)] = {"verdict": "supports", "role": "survey",
                                                "basis": "a row for a key no manuscript cites",
                                                "sentence": "a sentence that is not in the text"}
    def undeclared_role(rows):
        rows[sorted(rows)[0]]["role"] = "vibes"
    def plant_unsupported(rows):
        k = sorted(rows)[0]
        rows[k]["verdict"] = "unsupported"
        rows[k]["why"] = "planted: an unsupported anchor must be reported and must fail the check"
    def no_sentence(rows):
        rows[sorted(rows)[0]]["sentence"] = ""
    def edit_a_sentence(d):
        """The signal this identity exists for: a cited sentence is edited."""
        p = os.path.join(d, PARTS[1])
        t = io.open(p, encoding="utf-8").read()
        t = t.replace("The offline optimum is Belady's", "The offline optimum is Belady's own")
        io.open(p, "w", encoding="utf-8").write(t)
    def new_citation(d):
        p = os.path.join(d, PARTS[1])
        t = io.open(p, encoding="utf-8").read()
        t += "\nAn added sentence citing a work nobody read [@lassurvey].\n"
        io.open(p, "w", encoding="utf-8").write(t)

    case("drop_a_row", lambda d: edit_verdicts(d, drop_a_row), expect=1)
    case("blank_a_verdict", lambda d: edit_verdicts(d, blank_a_verdict), expect=1)
    case("blank_a_basis", lambda d: edit_verdicts(d, blank_a_basis), expect=1)
    case("orphan_row", lambda d: edit_verdicts(d, orphan_row), expect=1)
    case("undeclared_role", lambda d: edit_verdicts(d, undeclared_role), expect=1)
    case("row_with_no_sentence", lambda d: edit_verdicts(d, no_sentence), expect=1)
    case("plant_unsupported", lambda d: edit_verdicts(d, plant_unsupported), expect=1)
    # one edited sentence carries SEVEN keys, so it un-binds seven reads and each must be named: the
    # pairing rule is per key, and a case that reported one failure would be hiding six
    case("edit_a_cited_sentence_seven_keys", edit_a_sentence, expect=7)
    case("new_citation_unread", new_citation, expect=1)

    if f0:
        fails.append("positive control: the unmutated package fails: %s" % f0[:2])
    print("  [%s] clean positive control: %d occurrence(s), %d row(s), %d failure(s)"
          % ("ok" if not f0 else "FAIL", st0["occurrences"], st0["rows"], len(f0)))
    for name, exp in (("clean_positive_control_repeated", 0), ("drop_a_row", 1),
                      ("blank_a_verdict", 1), ("blank_a_basis", 1), ("orphan_row", 1),
                      ("undeclared_role", 1), ("row_with_no_sentence", 1),
                      ("plant_unsupported", 1), ("edit_a_cited_sentence_seven_keys", 7),
                      ("new_citation_unread", 1)):
        got = fired.get(name)
        print("  [%s] %s: %s failure(s) reported, expected %d"
              % ("ok" if got == exp else "FAIL", name, got, exp))
    for f in sorted(os.listdir(tmp)):
        shutil.rmtree(os.path.join(tmp, f), ignore_errors=True)
    os.rmdir(tmp)
    # ---- the REPORT, not just the rows.  Both directions: a freshly built pair must pass, and one
    # byte of drift in the report alone must fail -- with exactly one failure, so the case cannot
    # pass because the rows happened to fail.
    d = os.path.join(tmp, "report_freshness")
    copy_in(d)
    force_clean(d)
    build(d, d, out_dir=d)
    f, st = check(d)
    if f or st.get("report", {}).get(OUT_MD) != "current":
        fails.append("a freshly built report must pass: %s / %r" % (f[:1], st.get("report")))
    fired["report_fresh"] = len(f)
    p_md = os.path.join(d, OUT_MD)
    t = io.open(p_md, encoding="utf-8").read()
    planted = t.replace("| distinct keys |", "| distinct keys (stale) |", 1)
    if planted == t:
        fails.append("the staleness case planted nothing: the measure row was not found in the report")
    io.open(p_md, "w", encoding="utf-8").write(planted)
    f2, st2 = check(d)
    fired["report_stale"] = len(f2)
    if len(f2) != 1 or st2.get("report", {}).get(OUT_MD) != "STALE" or OUT_MD not in f2[0]:
        fails.append("a stale report must fail exactly once, naming the file -- %d failure(s), "
                     "detail %r, first %r" % (len(f2), st2.get("report"), f2[:1]))

    print("selftest: %d case(s) failed" % len(fails))
    for f in fails:
        print("  FAIL:", f)
    return not fails


def main():
    args = sys.argv[1:]
    if args == ["--selftest"]:
        return 0 if selftest() else 1
    if args and args[0] == "--bind":
        bind(pkgdir(), HERE)
        return 0
    if args and args[0] == "--build":
        out = None
        if "--out" in args:
            out = args[args.index("--out") + 1]
        js = build(pkgdir(), HERE, out_dir=out)
        print("support read: %d occurrence(s), %d key(s), %d supports, %d unsupported, "
              "%d finding(s) on record"
              % (js["occurrences"], js["keys"], js["supports"], js["unsupported"],
                 len(js["findings"])))
        return 0
    fail, st = check(pkgdir(), data_dir=HERE)
    print("support read: %d occurrence(s) over %d key(s) -- %d support, %d do not; "
          "unread %d, stale rows %d" % (st["occurrences"], st["keys"], st["supports"],
                                        st["unsupported"], st["unread"], st["orphan_rows"]))
    print("support report: %s"
          % (", ".join("%s %s" % (k, v) for k, v in sorted(st.get("report", {}).items()))
             or "not checked"))
    for line in st["unsupported_list"]:
        print("  UNSUPPORTED:", line)
    for f in fail:
        print("  FAIL:", f)
    if not fail:
        print("SUPPORT LIMB: OK -- every cited occurrence carries the sentence it is attached to")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
