#!/usr/bin/env python3
"""R415 -- read each of the four required changes at the object it names.

Run against the package after the revision.  Every check reads the file (never a claim about the file), and
the script prints the line it read so the verdict is auditable.  Exit 0 = all four discharged.
"""
import io
import json
import os
import re
import subprocess
import sys

PKG = sys.argv[1] if len(sys.argv) > 1 else "."
p = lambda *a: os.path.join(PKG, *a)
rows = []


def check(n, what, ok, evidence):
    rows.append((n, what, ok, evidence))
    print("%-4s %-58s %s\n     %s" % (n, what, "ok" if ok else "NOT DISCHARGED", evidence))


p3 = io.open(p("manuscript_part3.md"), encoding="utf-8").read()
p1 = io.open(p("manuscript_part1.md"), encoding="utf-8").read()
p4 = io.open(p("manuscript_part4.md"), encoding="utf-8").read()
man = io.open(p("manuscript.md"), encoding="utf-8").read()
rep = io.open(p("reproduce.sh"), encoding="utf-8").read()
r409 = io.open(p("artefacts/instruments/r409_align_streams.py"), encoding="utf-8").read()
r412 = io.open(p("artefacts/instruments/r412_matchedlocal_tuned.py"), encoding="utf-8").read()

# ---- 1: §5.3's introductory sentence names the instrument that produced Table 4's alpha = 0 rows
# Read the RENDERED prose, not the source: a phrase is what a reader sees, and a hard line break inside it is
# a property of the file, not of the sentence (the first version of this check failed on exactly that).
flat = " ".join(p3.split())
i = flat.index("The alignment axis does move the sign")
intro = flat[i:i + 900].split("**Table 4 —")[0]
check(1, "§5.3's intro sentence names Table 4's instrument",
      "smoke_v10.py" in intro and "one target draw" in intro
      and "not" in intro and "6 target draws × 50 splits" in intro,   # the sentence must SEPARATE the two designs
      "reads: %s" % intro[:220])
_cap = flat[flat.index("**Table 4 —"):flat.index("| convention | γ = 0.1")]
check("1b", "the sentence and the caption beneath it agree on instrument and design",
      _cap.count("smoke_v10.py") >= 1 and "one target draw" in _cap and "not the map's" in _cap,
      "caption reads: %s" % _cap[:230])

# ---- 2: one numbering, and every cross-reference resolves
caps = [int(m.group(1)) for m in re.finditer(r'^\*\*Table (\d+)\b', man, re.M)]
mentions = [int(m.group(1)) for m in re.finditer(r'Table (\d+)\b', man)
            if not man[max(0, m.start() - 2):m.start()].endswith("**")]
uniq, contiguous = len(set(caps)) == len(caps), caps == list(range(1, len(caps) + 1))
resolved = all(n in set(caps) for n in mentions)
f7 = [l for l in p1.split("\n") if "§5.3, Table" in l]
asm = subprocess.run(["/usr/bin/python3", p("artefacts/assembly/manuscript_assembly.py")],
                     capture_output=True, text=True).stdout
c4 = [l for l in asm.split("\n") if l.startswith("CHECK 4")]
check(2, "the table numbering is unique and every reference resolves",
      uniq and contiguous and resolved and any("Tables 5 and 6" in l for l in f7)
      and any("duplicate numbers none" in l and "gaps none" in l for l in c4),
      "captions=%s | F7 pointer: %s | %s" % (caps, (f7[0].split("|")[-2].strip() if f7 else "?"), (c4[0][:96] if c4 else "?")))

# ---- 3: the build is named, the control reports, and the chain runs it
sent = [flat[j:j + 620] for j in [flat.index("12 of 12 bitwise")]] if "12 of 12 bitwise" in flat else []
build_pin = re.search(r'BUILD_PINNED = dict\(python="([\d.]+)", numpy="([\d.]+)"\)', r409)
c1_pin = re.search(r'C1_BUILD_PINNED = dict\(python="([\d.]+)", numpy="([\d.]+)"\)', r412)
run = subprocess.run(["/usr/bin/python3", p("artefacts/instruments/r409_align_streams.py"), "--control-only"],
                     capture_output=True, text=True)
ctl = [l.strip() for l in run.stdout.split("\n") if "verdict     :" in l or "build pinned:" in l or "build read  :" in l]
dig = json.load(io.open(p("artefacts/results_digest.json"), encoding="utf-8"))["quantities"]
check(3, "the bitwise sentence names its build; the control reports; the chain runs it",
      bool(sent) and "python 3.9.6" in " ".join(sent) and "numpy 2.0.2" in " ".join(sent)
      and "2.19e\u221211" in " ".join(sent)
      and build_pin and c1_pin and 'verdict=ctl_verdict' in r409 and 'c1_verdict' in r412
      and "--control-only" in rep and "--selftest" in rep
      and dig["alignment.control_reproduction"]["value"]["verdict"] == "BITWISE"
      and dig["alignment.control_foreign_build"]["value"]["worst_rel"] == 2.192e-11,
      "sentence: %s | pinned r409 %s r412 %s | reading: %s"
      % (" ".join(sent)[:190], build_pin.groups() if build_pin else None, c1_pin.groups() if c1_pin else None,
         " / ".join(ctl)[:150]))

# ---- 4: reproduce.sh states the count the assembly prints -- and every carrier is read against the owner
cc = subprocess.run(["/usr/bin/python3", p("artefacts/assembly/counts_check.py")], capture_output=True, text=True)
owner = re.search(r'CHECK 3 bindings: (\d+) bound', io.open(p("artefacts/assembly/assembly-report.txt"), encoding="utf-8").read())
stated = re.search(r'^BINDINGS=(\d+)', rep, re.M)
check(4, "reproduce.sh states the count the assembly prints, and the carriers are checked",
      bool(owner) and bool(stated) and owner.group(1) == stated.group(1)
      and "counts_check.py" in rep and cc.returncode == 0 and "COUNTS: PASS" in cc.stdout
      and "91 numeric bindings" not in rep and "91 numeric bindings" not in io.open(p("README.md"), encoding="utf-8").read(),
      "assembly prints %s, reproduce.sh declares %s, counts_check: %s"
      % (owner.group(1) if owner else "?", stated.group(1) if stated else "?", cc.stdout.strip().split("\n")[-1]))

bad = [n for n, _, ok, _ in rows if not ok]
print("\n%d of %d required changes discharged at their objects" % (len(rows) - len(bad), len(rows)))
sys.exit(1 if bad else 0)
