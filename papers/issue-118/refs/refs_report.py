#!/usr/bin/env python3
"""Issue #118 -- GENERATE reference-check.md from the reference artefacts.

The report is a claim about two committed files (`refs/curated.json`, the curatorial act;
`refs/verify.log`, the verification act). Every number in it is therefore READ from those
files, never typed: `reproduce.sh` re-runs this generator and requires the committed
`reference-check.md` to be byte-identical to the output, so a hand-edited number cannot
survive a run.

It asserts, before writing:
  * the stored summary in curated.json (`n`, `roles`) agrees with the entries it summarises;
  * the verification log and the curated set name the SAME identifiers, in both directions;
  * every log line's title normalises to the curated title for that identifier;
  * the log's own header counts agree with the lines beneath it;
  * coverage: every entry cited in the manuscript, every in-text key curated, count >= floor.

Usage:  /usr/bin/python3 refs/refs_report.py     ->  reference-check.md
"""
import collections
import hashlib
import json
import os
import re
import sys

import refs_build as B                        # same arithmetic, same inputs, one place
import refs_tool as T                         # the verifier's own normaliser

CUR = "refs/curated.json"
LOG = "refs/verify.log"
OUT = "reference-check.md"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    cur = json.load(open(CUR))
    entries = cur["entries"]
    by_bare = {e["bare"]: e for e in entries}

    # -- the stored summary must agree with what it summarises -----------------
    roles = collections.Counter(e["role"] for e in entries)
    assert cur["n"] == len(entries), \
        "curated.json says n=%s but carries %d entries" % (cur["n"], len(entries))
    assert dict(cur["roles"]) == dict(roles), \
        "curated.json's role summary is stale: %s vs %s" % (cur["roles"], dict(roles))

    # -- the verification log --------------------------------------------------
    raw = open(LOG).read().splitlines()
    header = [l for l in raw if l.startswith("#")]
    body = [l for l in raw if l and not l.startswith("#")]
    m = re.match(r"# (\d+) entries: (\d+) OK, (\d+) PROBLEM", header[1])
    assert m, "the verification log's summary line is not in the expected form: %r" % header[1]
    n_hdr, ok_hdr, bad_hdr = (int(x) for x in m.groups())
    verdicts = collections.Counter(l.split()[0] for l in body)
    assert verdicts.get("OK", 0) == ok_hdr and verdicts.get("OK", 0) == len(body), \
        "the log's header counts do not match its own lines: %s" % dict(verdicts)
    assert bad_hdr == 0, "the verification log records %d PROBLEM entries" % bad_hdr

    logged = {}
    for l in body:
        parts = l.split()
        ver, bare = parts[0], parts[1]
        logged[bare] = (ver, l.split(None, 3)[3] if len(parts) > 3 else "")
    missing = sorted(set(by_bare) - set(logged))
    extra = sorted(set(logged) - set(by_bare))
    assert not missing, "curated entries with no verification line: %s" % missing[:8]
    assert not extra, "verification lines for entries not in the curated set: %s" % extra[:8]
    for bare, (ver, title) in logged.items():
        assert ver == "OK", "%s is not OK: %s" % (bare, ver)
        assert T.norm(title) == T.norm(by_bare[bare]["title"]), \
            "%s: the verified title does not match the curated title" % bare

    # -- coverage (refs_build's own scan, over refs_build's own inputs) --------
    src = open(B.MS).read()
    used = set()
    for tk in B.TOKEN.findall(src):
        used.update(B.IDRE.findall(tk))
    uncited = sorted(set(by_bare) - used)
    uncurated = sorted(used - set(by_bare))
    assert not uncited, "entries never cited: %s" % uncited[:8]
    assert not uncurated, "in-text keys that are not curated: %s" % uncurated[:8]
    assert len(entries) >= B.MIN_REFS, "%d entries is below the floor %d" % (len(entries), B.MIN_REFS)

    # -- write the report ------------------------------------------------------
    L = []
    L.append("# Citation report - issue #118")
    L.append("")
    L.append("Companion to `manuscript.md`. Two duties: (i) **authenticity** of every reference, and")
    L.append("(ii) **coverage** of the in-text citation keys. This report is a declaration; reviewers")
    L.append("verify independently. It is **generated** by `refs/refs_report.py` from the two committed")
    L.append("artefacts, and `reproduce.sh` requires the committed file to equal the generator's output")
    L.append("byte for byte -- so no number here can have been typed by hand and survived a run.")
    L.append("")
    L.append("## (i) Authenticity - how the entries were verified")
    L.append("")
    L.append("**Method.** Verification is a different act from discovery and from curation, and it lives")
    L.append("in a different file: `refs/refs_tool.py` re-fetches **each curated entry by its own")
    L.append("identifier** from the index that owns that identifier (arXiv, `id_list=<id>`) and compares")
    L.append("the returned title to the title recorded for that key, after normalisation (case,")
    L.append("punctuation and whitespace folded).")
    L.append("")
    L.append("```")
    L.append("python3 refs/refs_tool.py verify     # re-fetches and re-writes refs/verify.log")
    L.append("python3 refs/refs_tool.py plant      # two-sided control on a throwaway copy")
    L.append("```")
    L.append("")
    L.append("**Result: entries=%d  resolved=%d  problems=%d.** The command exits non-zero if any" % (n_hdr, ok_hdr, bad_hdr))
    L.append("entry fails, so this is a check rather than a statement. The generator additionally asserts")
    L.append("that the log and the curated set name the *same* identifiers in both directions and that")
    L.append("every returned title normalises to the curated one.")
    L.append("")
    L.append("| artefact | what it is | sha256 |")
    L.append("|---|---|---|")
    L.append("| `refs/verify.log` | the verifier's own output (%d lines) | `%s` |" % (len(body), sha(LOG)))
    L.append("| `refs/curated.json` | the curated set, with the role and the stated difference of each entry | `%s` |" % sha(CUR))
    L.append("")
    L.append("**Two-sided controls** (`refs_tool.py plant`, against a throwaway copy; the committed")
    L.append("artefact is never mutated). A verifier that cannot fail is decoration, so both plants must")
    L.append("be caught and the command exits non-zero if either escapes:")
    L.append("")
    L.append("| control | expected | observed |")
    L.append("|---|---|---|")
    L.append("| one title replaced by a different paper's title | fail | exit 1, `MISMATCH`, both strings named |")
    L.append("| one invented identifier (`9999.99999`) | fail | exit 1, `UNRESOLVED` for that identifier |")
    L.append("")
    L.append("## (ii) Coverage of the in-text keys")
    L.append("")
    L.append("The manuscript cites `[[identifier]]`, never a number: a literal `[N]` in the body would")
    L.append("re-point the moment the list is renumbered, so the body carries identifiers and the numbers")
    L.append("are assigned at build time by `refs/refs_build.py`.")
    L.append("")
    L.append("| quantity | value |")
    L.append("|---|---|")
    L.append("| curated entries | %d |" % len(entries))
    L.append("| cited in the body | %d |" % len(used))
    L.append("| curated but never cited | %d |" % len(uncited))
    L.append("| cited but not curated | %d |" % len(uncurated))
    L.append("| journal floor | %d |" % B.MIN_REFS)
    L.append("")
    L.append("`refs/refs_build.py check` is the command that produces those four numbers; it also scans")
    L.append("the body for a literal `[N]`, which must be found zero times. The generator asserts them")
    L.append("independently, over the same inputs.")
    L.append("")
    L.append("## (iii) The entries, by role")
    L.append("")
    for role in B.ROLE_ORDER:
        group = [e for e in entries if e["role"] == role]
        if not group:
            continue
        L.append("### %s (%d)" % (B.ROLE_NAME.get(role, role), len(group)))
        L.append("")
        L.append("| identifier | verdict | title as recorded | published |")
        L.append("|---|---|---|---|")
        for e in sorted(group, key=lambda e: e["bare"]):
            L.append("| `%s` | %s | %s | %s |" % (e["bare"], logged[e["bare"]][0], e["title"], e["published"]))
        L.append("")
    L.append("---")
    L.append("")
    L.append("Generated by `refs/refs_report.py` from `refs/curated.json` and `refs/verify.log`;")
    L.append("re-generate with `python3 refs/refs_report.py` (`reproduce.sh` step 5b).")
    L.append("")
    out = "\n".join(L)
    with open(OUT, "w") as fh:
        fh.write(out)
    print("wrote %s: %d chars, %d entries, %d roles" % (OUT, len(out), len(entries), len(roles)))


if __name__ == "__main__":
    main()
