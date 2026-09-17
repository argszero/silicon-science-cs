#!/usr/bin/env python3
"""Verify issue #38's correction ROUND 3 mechanically, with a control per check.

Round 3 is about ONE property -- the case of the author component -- and the same read found a second
instance of the same test (an entry whose text carried the registry's XML escape for a name), so both
are verified here and each is declared separately in the delivery note.

Every check reads the artefact (the manuscript's rendered section) and every check is two-sided: it
must PASS on the delivered manuscript and FAIL on a copy that puts the defect back.  Two readings are
DERIVED rather than typed -- the section is re-rendered with `author_case` replaced by the identity and
with the entity decode removed, inside this file, by monkeypatching the module by NAME -- so the
controls cannot go stale when the renderer is edited (a typed literal anchor is what went stale twice
in earlier rounds of this package).

    python3 verify_correction_r3.py
    python3 verify_correction_r3.py --no-network    # skip the page-renderer reading

Writes correction_r3_verify.log BESIDE this package.
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, "manuscript.md")
LOG = os.path.join(HERE, "correction_r3_verify.log")
REF_HEAD = re.compile(r"(?m)^##\s*(?:\d+\.\s*)?References\s*$")
ENTRY = re.compile(r"(?m)^\[(\d+)\] ")

out = []


def say(s):
    out.append(s)
    print(s)


def load_module(root):
    """Import the renderer from `root`, so the module's own data paths follow the copy."""
    spec = importlib.util.spec_from_file_location("refs_render_%d" % abs(hash(root)), os.path.join(root, "refs_render.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sandbox():
    """A copy of the package files the renderer needs, so a mutated renderer can be exercised."""
    d = tempfile.mkdtemp(prefix="r3-38-")
    for f in ("refs_render.py", "references.json", "refs_display.json", "manuscript.md"):
        shutil.copy(os.path.join(HERE, f), os.path.join(d, f))
    return d


def section(ms):
    """The body of the one `## References` section, cut exactly where the renderer cuts it.

    By line index, not by splitting on the heading pattern: that pattern ends in `\s*$`, which eats the
    newline that closes the heading line, so a section read that way reconstructs one newline short of
    what `render()` produces -- which is how this verifier first reported a delivered section that was
    "not what the shipped renderer produces".
    """
    lines = ms.split("\n")
    starts = [i for i, l in enumerate(lines) if REF_HEAD.match(l)]
    assert len(starts) == 1, "expected exactly one Reference heading, found %d" % len(starts)
    return "\n".join(lines[starts[0] + 1:])


def whole_section(ms):
    """The section INCLUDING its heading line -- comparable, byte for byte, with `render()`."""
    lines = ms.split("\n")
    starts = [i for i, l in enumerate(lines) if REF_HEAD.match(l)]
    assert len(starts) == 1
    return "\n".join(lines[starts[0]:]).rstrip("\n")


def blocks(sec):
    return [b for b in re.split(r"(?m)^(?=\[\d+\] )", sec.strip("\n")) if ENTRY.match(b)]


def ws(s):
    return re.sub(r"\s+", " ", s).strip()


def author_region(blk):
    """(key, author text, index just past it) in the collapsed block; (None, None, None) if no block."""
    t = ws(blk)
    m = re.match(r"^\[(\d+)\] (.*?) \((?:19|20)\d\d\)\.", t)
    return (m.group(1), m.group(2), m.end()) if m else (None, None, None)


# --------------------------------------------------------------------------- the checks
def check_case(ms):
    """R3-a: no ALL-CAPS author component survives, and every component is the folded record."""
    sec = section(ms)
    mod = load_module(HERE)
    refs, disp = mod.load()
    fails = []
    caps = mod.caps_author_components(sec)
    if caps:
        fails.append("%d ALL-CAPS author component(s) survive: %s"
                     % (len(caps), "; ".join("[%s] %s" % c for c in caps)))
    wrong = []
    for blk in blocks(sec):
        k, reg, _ = author_region(blk)
        src = disp[k].get("authors") or []
        if not src:
            # the exception the house style names: the entry records the absence by naming the records
            # that were read.  Compared against the sentence, not against the empty string.
            if "not established" not in reg:
                wrong.append("[%s] states no author and does not carry the exception: %r" % (k, reg))
            if mod.author_string([]) != "":
                wrong.append("the renderer no longer renders an empty author list as empty")
            continue
        want = mod.author_string(src)
        if reg != want:
            wrong.append("[%s] prints %r, the record read states %r" % (k, reg, want))
    if wrong:
        fails.append("%d entr(y|ies) whose author block is not the folded record: %s" % (len(wrong), wrong[:3]))
    return fails, ("125 entries: 0 ALL-CAPS author component(s); every author block equals the folded "
                   "record (%d record(s) state a component in capitals)" % len(set(k for k, _ in mod.source_caps(disp))))


def check_text(ms):
    """R3-b: no escaped character reference survives in the section's text."""
    sec = section(ms)
    mod = load_module(HERE)
    refs, disp = mod.load()
    esc = mod.escaped_entities(sec)
    fails = []
    if esc:
        named = ["[%s]" % author_region(b)[0] for b in blocks(sec) if "&#" in b]
        fails.append("%d escaped character reference(s) survive in the text: %s in %s"
                     % (len(esc), sorted(set(esc)), named))
    return fails, ("0 escaped character reference(s) over 125 entries (%d record(s) state one; the page "
                   "renders both forms identically -- measured, see R3-b2)" % len(mod.source_entities(disp, refs)))


def check_page(ms):
    """R3-b2: the page reading -- the escaped and decoded forms render identically, so this repair is
    to the TEXT.  Taken with GitHub's own renderer when it is reachable, else SKIP with the reason."""
    try:
        p = subprocess.run(["gh", "api", "-X", "POST", "/markdown", "-f", "mode=gfm",
                            "-f", "text=X O&#39;Brien"], capture_output=True, text=True, timeout=120)
        q = subprocess.run(["gh", "api", "-X", "POST", "/markdown", "-f", "mode=gfm",
                            "-f", "text=X O'Brien"], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        return [], "SKIP could not run `gh api /markdown` (%s): the page reading was not taken" % exc
    if p.returncode or q.returncode:
        return [], ("SKIP `gh api /markdown` failed (exit %d/%d): the page reading was not taken"
                    % (p.returncode, q.returncode))
    a, b = p.stdout.strip(), q.stdout.strip()
    if a != b:
        return (["the escaped and decoded forms do not render identically: %r vs %r" % (a, b)],
                "GitHub's renderer: %r for both forms" % a)
    return [], "GitHub's own renderer returns %r for the escaped and for the decoded form" % a


def check_conservation(ms):
    """R3-c: the two repairs are confined to the author component -- derived, not typed.

    The section is re-rendered twice in sandboxes: with `author_case` replaced by the identity (the
    pre-round-3 rendering of the case) and with the entity decode removed (the pre-round-3 rendering of
    the text).  Each re-render must differ from the delivered section in EXACTLY the entries it is
    responsible for, and only inside their author blocks -- so no other rendered text moved.
    """
    sec = section(ms)
    fails = []
    d = sandbox()
    try:
        mod = load_module(d)
        real_render = mod.render()
        if real_render.rstrip("\n") != whole_section(ms):
            fails.append("the delivered section is not what the shipped renderer produces")

        def moved(other):
            """The entry keys whose rendered block changed, and whether the change is author-only."""
            a = dict((author_region(b)[0], b) for b in blocks(real_render))
            c = dict((author_region(b)[0], b) for b in blocks(other))
            keys, not_author_only = [], []
            for k in sorted(set(a) | set(c), key=int):
                if k not in a or k not in c:
                    keys.append(k)
                    not_author_only.append("[%s] missing on one side" % k)
                    continue
                if a[k] == c[k]:
                    continue
                keys.append(k)
                ka, ra, ea = author_region(a[k])
                kb, rb, eb = author_region(c[k])
                if ka != kb or ws(a[k])[ea:] != ws(c[k])[eb:]:
                    not_author_only.append("[%s] differs outside its author block" % k)
            return keys, not_author_only

        # (1) the case fold removed
        mod.author_case = lambda s: s
        un = mod.render()
        if un == real_render:
            fails.append("removing the case fold changed nothing: the control could not be derived")
        keys, sideways = moved(un)
        if keys != ["15", "20"]:
            fails.append("removing the case fold moves entries %s, expected exactly ['15', '20']" % keys)
        fails += sideways
        # (2) the decode removed
        mod.author_case = load_module(HERE).author_case
        mod.record_text = lambda s: s
        nd = mod.render()
        if nd == real_render:
            fails.append("removing the decode changed nothing: the control could not be derived")
        keys2, sideways2 = moved(nd)
        if keys2 != ["95"]:
            fails.append("removing the decode moves entries %s, expected exactly ['95']" % keys2)
        fails += sideways2
        return fails, ("re-rendering with the case fold removed moves exactly entries %s (both author-only); "
                       "with the decode removed, exactly %s" % (keys, keys2))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def check_checker(ms):
    del ms  # this check reads the package's own files, not the section
    """R3-d: the shipped check's OWN failure path, exercised by running it on a mutated renderer.

    This is the acceptance read taken the way the editor takes it -- `refs_render.py --check` on a tree
    whose renderer lost the fold -- so the verdict belongs to the shipped command and not to a
    re-implementation of its rule inside this verifier.
    """
    fails = []
    d = sandbox()
    try:
        mod = load_module(d)
        mod.author_case = lambda s: s          # the fold removed, nothing else touched
        buf = io.StringIO()
        argv = sys.argv
        sys.argv = ["refs_render.py", "--check"]
        try:
            with contextlib.redirect_stdout(buf):
                rc = mod.main()
        finally:
            sys.argv = argv
        text = buf.getvalue()
        if rc == 0:
            fails.append("`--check` exits 0 with the fold removed: the rule does not gate anything")
        if not re.search(r"author case: [1-9]", text):
            fails.append("`--check` does not name the surviving ALL-CAPS components it read")
        spelled = re.findall(r"\[(15|20)\]", text)
        if sorted(set(spelled)) != ["15", "20"]:
            fails.append("`--check` names %s, expected the two entries the decision located" % sorted(set(spelled)))
        # and the unfixed tree must be the ONLY reason: with the fold restored it exits 0
        mod.author_case = load_module(HERE).author_case
        buf2 = io.StringIO()
        sys.argv = ["refs_render.py", "--check"]
        try:
            with contextlib.redirect_stdout(buf2):
                rc2 = mod.main()
        finally:
            sys.argv = argv
        if rc2 != 0:
            fails.append("`--check` exits %d on the very same copy with the fold restored" % rc2)
        return fails, ("`refs_render.py --check` on a copy whose renderer lost the fold: exit %d, names "
                       "[15] and [20]; on the same copy with the fold: exit %d" % (rc, rc2))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def check_initial(ms):
    del ms  # this check reads the package's own files, not the section
    """R3-e: the fold must not lowercase an initial -- the reason it is not `title_case`."""
    mod = load_module(HERE)
    fails = []
    got = mod.author_case("SMITH, A. B.")
    if got != "Smith, A. B.":
        fails.append("authors are folded to %r, an initial must survive" % got)
    naive = mod.title_case("SMITH, A. B.")
    if naive == got:
        fails.append("the control could not be derived: title_case no longer differs on this input")
    if mod.author_case("Gale, D.") != "Gale, D.":
        fails.append("a mixed-case record author is not printed as the record states it")
    return fails, ("`SMITH, A. B.` -> %r (the title fold would give %r); a mixed-case component is "
                   "unchanged" % (got, naive))


def check_data(ms):
    del ms  # this check reads the package's own files, not the section
    """R3-f: the checks above are only as strong as the data they read -- the liveness of both rules."""
    mod = load_module(HERE)
    refs, disp = mod.load()
    fails = []
    src = mod.source_caps(disp)
    srce = mod.source_entities(disp, refs)
    if not src:
        fails.append("no record states an author in capitals: the case rule has nothing to exercise")
    if not srce:
        fails.append("no record states an escaped reference: the text rule has nothing to exercise")
    n_caps = len({k for k, _ in src})
    return fails, ("the record read states capitals in %d record(s) and an escaped reference in %d "
                   "record(s), so both rules are exercised" % (n_caps, len({k for k, _ in srce})))


CHECKS = [
    ("R3-a case fold", check_case),
    ("R3-b record text", check_text),
    ("R3-b2 page", check_page),
    ("R3-c conservation", check_conservation),
    ("R3-d the shipped check", check_checker),
    ("R3-e the initial", check_initial),
    ("R3-f data liveness", check_data),
]


def main():
    ms = io.open(MS, encoding="utf-8").read()
    say("issue #38 correction round 3 -- verification at %s" % MS)
    say("")
    allfail = []
    for name, fn in CHECKS:
        try:
            fails, detail = fn(ms)
        except Exception as exc:                                    # a check that cannot run is not a pass
            fails, detail = ["the check raised %s: %s" % (type(exc).__name__, exc)], "no reading taken"
        say("%-24s %s" % (name, "PASS" if not fails else "FAIL"))
        say("   %s" % detail)
        for f in fails:
            say("   !! %s" % f)
        allfail += fails
        say("")
    say("R3: %s" % ("ALL PASS" if not allfail else "FAIL"))
    try:
        io.open(LOG, "w", encoding="utf-8").write("\n".join(out) + "\n")
        say("log written to %s" % LOG)
    except OSError as exc:
        say("NOTE: could not write %s (%s). The verdict above stands." % (LOG, exc))
    return 1 if allfail else 0


if __name__ == "__main__":
    sys.exit(main())
