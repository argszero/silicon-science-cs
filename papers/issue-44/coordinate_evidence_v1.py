#!/usr/bin/env python3
"""Issue #44 -- COORDINATE EVIDENCE: the package's coordinate-dependent reads, pinned to one file.

    python3 coordinate_evidence_v1.py --write    # (re)record the reading; needs the git coordinate
    python3 coordinate_evidence_v1.py --check     # verify the record; works in an exported package

WHY THIS FILE EXISTS.  A round-2 review found that this package's instrument audit FAILED when the
package was exported -- a copy with no `.git` above it.  The cause was a single read:

    subprocess.run(["git", "show", "HEAD:papers/issue-44/verify_refs.py"], cwd=PKG)

An audit is supposed to be evidence about THIS package.  A read of "whatever HEAD is here right
now" is evidence about the CHECKOUT, and it silently changes meaning with it -- at the head under
review it read the historical blob, at the current head it read a different one and passed for a
different reason.  Two defects in one line: not self-contained, and not pinned.

The fix is to make every coordinate-dependent read (i) live in THIS file, (ii) name its coordinate
explicitly, and (iii) be recorded in a committed artefact `coordinate_evidence.json` that the audit
reads.  `--check` then works anywhere -- it recomputes the reading from the RECORD -- and, when the
git coordinate happens to be resolvable, it additionally ties the record to the live blob, so the
record cannot drift silently.  When the coordinate is unavailable the check says so in its output
rather than passing quietly: an unavailable coordinate is a DECLARED state, not a silent pass.

Network-free and deterministic.  Exit status is the verdict (0 = the record is sound).
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = HERE
RECORD = os.path.join(HERE, "coordinate_evidence.json")

# The census's answer to the question "where can a coordinate enter this package?" is a count of
# the reads in each class.  This module is the declared home of class C1 (git object reads): the
# census in instrument_audit.py fails if a git read appears anywhere else.
COORDINATE_CLASS = "C1 git object read"

# The reading to pin.  `extract` is the rule the audit also applies to the recorded lines, so the
# reading is recomputable from the record alone.
READS = [
    {
        "id": "reviewed_head_self_test_status",
        "repository_path": "papers/issue-44/verify_refs.py",
        "commit": "e54495bec9563d856204372060ca68442c69dc89",
        "commit_short": "e54495b",
        "commit_role": ("the head the round-2 review of record (comment 5683220375) was written "
                        "against"),
        "extract": r"\btests\b",
        "extract_note": "stripped source lines mentioning `tests`",
        "status_markers": ["problems", "return"],
        "reading_note": ("uses of `tests` vs uses that feed the run status; the self-test of the "
                         "bracket counter and of the citation support test was PRINTED in this "
                         "blob and could not fail the run"),
    },
]


def blob_of(commit, rel):
    """The git coordinate, resolved.  Returns (text, reason): text is None when unavailable."""
    root, d = None, HERE
    for _ in range(8):
        d = os.path.dirname(d)
        if os.path.exists(os.path.join(d, ".git")):
            root = d
            break
    if root is None:
        return None, "no .git above this package (an exported or relocated copy)"
    r = subprocess.run(["git", "show", "%s:%s" % (commit, rel)], cwd=root,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, ("commit %s is not resolvable in this checkout (shallow clone, single-branch "
                      "fetch, or a deleted branch)" % commit[:7])
    return r.stdout, "resolved"


def read_one(spec):
    """The reading, recomputed from a blob text.  Always the same rule, so the record and the
    live blob are compared by one definition."""
    lines = [l.strip() for l in spec["text"].split("\n") if re.search(spec["extract"], l)]
    feeding = [l for l in lines if any(m in l for m in spec["status_markers"])]
    return {"uses": len(lines), "feeding_status": len(feeding), "extracted": lines}


def write_record():
    rec = {"schema": 1,
           "note": ("Every coordinate-dependent read in this package is pinned here. Produced by "
                    "coordinate_evidence_v1.py --write; verified by --check, which the instrument "
                    "audit runs. Do not hand-edit: --write is the only writer."),
           "reads": []}
    for spec in READS:
        text, why = blob_of(spec["commit"], spec["repository_path"])
        if text is None:
            print("REFUSED: cannot record %s -- %s" % (spec["id"], why))
            return 1
        rd = read_one(dict(spec, text=text))
        rec["reads"].append({
            "id": spec["id"],
            "coordinate": COORDINATE_CLASS,
            "repository_path": spec["repository_path"],
            "commit": spec["commit"],
            "commit_short": spec["commit_short"],
            "commit_role": spec["commit_role"],
            "blob_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "extract": spec["extract"],
            "extract_note": spec["extract_note"],
            "status_markers": spec["status_markers"],
            "reading_note": spec["reading_note"],
            "extracted": rd["extracted"],
            "reading": {"uses": rd["uses"], "feeding_status": rd["feeding_status"]},
        })
        print("recorded %s: %s @ %s blob %s uses=%d feeding_status=%d"
              % (spec["id"], spec["repository_path"], spec["commit_short"],
                 hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], rd["uses"],
                 rd["feeding_status"]))
    io.open(RECORD, "w", encoding="utf-8").write(
        json.dumps(rec, indent=2, sort_keys=False, ensure_ascii=False) + "\n")
    print("wrote %s" % os.path.basename(RECORD))
    return 0


def check_record():
    if not os.path.exists(RECORD):
        print("FAIL coordinate record missing: %s" % os.path.basename(RECORD))
        return 1
    rec = json.load(io.open(RECORD, encoding="utf-8"))
    bad = 0
    for entry in rec["reads"]:
        spec = next(s for s in READS if s["id"] == entry["id"])
        # (1) the reading must be recomputable from the RECORDED lines -- no coordinate needed
        rd = read_one({"extract": entry["extract"], "status_markers": entry["status_markers"],
                       "text": "\n".join(entry["extracted"])})
        ok_rec = ({k: rd[k] for k in ("uses", "feeding_status")} == entry["reading"])
        # (2) the record must agree with the generator's own table (id, path, commit, rule)
        ok_pin = (entry["repository_path"] == spec["repository_path"]
                  and entry["commit"] == spec["commit"]
                  and entry["extract"] == spec["extract"]
                  and entry["status_markers"] == spec["status_markers"]
                  and entry["coordinate"] == COORDINATE_CLASS)
        # (3) the declared blob digest must be a plausible digest of the recorded surface
        ok_sha = bool(re.fullmatch(r"[0-9a-f]{64}", entry.get("blob_sha256", "")))
        # (4) the live coordinate, when present, must AGREE -- this is what stops silent drift
        text, why = blob_of(entry["commit"], entry["repository_path"])
        if text is None:
            live = "not available here: %s" % why
            ok_live = True
        else:
            live_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
            live_rd = read_one({"extract": entry["extract"], "status_markers": entry["status_markers"],
                                "text": text})
            ok_live = (live_sha == entry["blob_sha256"]
                       and {k: live_rd[k] for k in ("uses", "feeding_status")}
                       == entry["reading"])
            live = ("git agrees: blob %s, reading uses=%d feeding_status=%d"
                    % (live_sha[:8], live_rd["uses"], live_rd["feeding_status"]))
        print("%-6s %-32s uses=%d feeding_status=%d | record=%s | pinned=%s | cross-check: %s"
              % ("OK" if (ok_rec and ok_pin and ok_sha and ok_live) else "FAIL",
                 entry["id"], entry["reading"]["uses"], entry["reading"]["feeding_status"],
                 "recomputes" if ok_rec else "MISMATCH",
                 "declared" if ok_pin else "MISMATCH", live))
        bad += 0 if (ok_rec and ok_pin and ok_sha and ok_live) else 1
    if bad:
        print("coordinate evidence: %d record(s) unsound" % bad)
        return 1
    print("coordinate evidence: OK (%d read(s), all recomputable from the record)"
          % len(rec["reads"]))
    return 0


def main():
    argv = sys.argv[1:]
    if "--write" in argv:
        return write_record()
    return check_record()


if __name__ == "__main__":
    sys.exit(main())
