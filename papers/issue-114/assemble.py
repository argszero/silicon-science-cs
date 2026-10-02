#!/usr/bin/env python3
"""Assemble `manuscript.md` from `manuscript.src.md`, and check it against what is committed.

WHY THIS FILE EXISTS
--------------------
The manuscript cites references by a **stable key** and prints them by a **number**, and those two
things are not the same object.  `refs/verify_refs.py` numbers the bibliography in the order it
verifies it (year, then key) and writes `refs/keys.json`; if a reference is inserted, every later
number moves, and a manuscript that had hand-copied the numbers would re-point every citation after
the insertion *silently* -- no check would read the displaced referent, because every check reads
the number the entry renders to.  So the source carries `[@key]` tokens and this step is the only
place a key becomes a number.

The References section is likewise not hand-written: it is lifted from `reference-list.md`, which
`verify_refs.py` generates from the verified records.  A hand-copied bibliography is a second copy
of a generated object, and the two drift.

  manuscript.src.md   +   refs/keys.json   +   reference-list.md   ->   manuscript.md

Usage:
    python3 assemble.py            # write manuscript.md
    python3 assemble.py --check    # assemble to a temp file and require it to equal the committed one

`--check` is the step that makes the product a checked object rather than a build artefact: it
compares the committed manuscript.md with what this file produces *now*, byte for byte, and prints
the count it read.  It exits nonzero on a difference, a missing token, or an unknown key.
"""

from __future__ import annotations

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "manuscript.src.md")
OUT = os.path.join(HERE, "manuscript.md")
KEYS = os.path.join(HERE, "refs", "keys.json")
REFS = os.path.join(HERE, "reference-list.md")

TOKEN = re.compile(r"\[@([a-z0-9-]+(?:\s*,\s*@?[a-z0-9-]+)*)\]")
PLACEHOLDER = "<!-- REFERENCES -->"
REF_HEAD = "## References"


def references_block() -> str:
    """The bibliography, in the house order, taken verbatim from the generated list."""
    text = io.open(REFS, encoding="utf-8").read()
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"^\[\d+\] ", l)), None)
    if start is None:
        raise SystemExit("reference-list.md carries no numbered entry -- nothing to assemble")
    body = "\n".join(lines[start:]).rstrip()
    return REF_HEAD + "\n\n" + body + "\n"


def render(src: str, keys: dict) -> str:
    unknown, used = [], set()

    def sub(m):
        ns = []
        for k in (x.strip().lstrip("@") for x in m.group(1).split(",")):
            if k not in keys:
                unknown.append(k)
                return m.group(0)
            used.add(k)
            ns.append(keys[k])
        return "[" + ",".join(str(n) for n in ns) + "]"

    body = TOKEN.sub(sub, src)
    if unknown:
        raise SystemExit("assemble: unknown citation key(s): " + ", ".join(sorted(set(unknown))))
    # A token the pattern did not match is a token this step did not render, and shipping it would
    # put a citation key into the product where a reader expects a number -- a defect no later check
    # in this package reads.  So the assembler refuses it here, naming the first one.
    leftover = re.search(r"\[@[^\]]*\]", body)
    if leftover:
        raise SystemExit("assemble: unrendered citation token: " + leftover.group(0)
                         + "  (a token split across a line break must keep its `@` on every key)")
    if PLACEHOLDER not in body:
        raise SystemExit(f"assemble: the source carries no {PLACEHOLDER} marker")
    body = body.replace(PLACEHOLDER, references_block()).rstrip() + "\n"
    return body, used


def main(argv) -> int:
    check = "--check" in argv
    keys = json.load(io.open(KEYS, encoding="utf-8"))
    src = io.open(SRC, encoding="utf-8").read()
    out, used = render(src, keys)

    print(f"assemble: {len(keys)} keys, {len(used)} cited by the source, "
          f"{len(keys) - len(used)} never cited here")

    if check:
        if not os.path.exists(OUT):
            print(f"assemble: FAIL -- {OUT} is absent")
            return 1
        have = io.open(OUT, encoding="utf-8").read()
        if have == out:
            print(f"assemble: COMMITTED MANUSCRIPT MATCHES THE BUILD ({len(out)} characters, {len(out.encode())} bytes)")
            return 0
        # report the first differing line, so a drift names itself
        hl, bl = have.splitlines(), out.splitlines()
        for i in range(max(len(hl), len(bl))):
            a = hl[i] if i < len(hl) else "<end of committed file>"
            b = bl[i] if i < len(bl) else "<end of assembled file>"
            if a != b:
                print(f"assemble: FAIL -- first difference at line {i + 1}")
                print(f"   committed: {a[:160]}")
                print(f"   assembled: {b[:160]}")
                break
        print("assemble: run `python3 assemble.py` to rebuild, then re-check")
        return 1

    io.open(OUT, "w", encoding="utf-8").write(out)
    print(f"assemble: wrote {OUT} ({len(out)} characters, {len(out.encode())} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
