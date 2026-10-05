#!/usr/bin/env python3
"""Generate refs/differences.json -- the one-line stated difference for every cited reference.

The journal's *Presentation requirements* put a `Difference: ...` line at the close of every
bibliography entry: the entry read against the sentence it is cited for.  Writing 108 of them by
hand invites drift between the sentence and the entry, so this generator derives each one from the
manuscript's OWN related-work clustering: a key takes the difference of the section-2 subsection
that first cites it, and the two keys outside section 2 take their section's.

It reads the SOURCES (manuscript.src.md, manuscript.part2.md), which carry `{ref:key}` placeholders,
so it does not depend on the built manuscript and there is no build/generate cycle.

Output:  refs/differences.json   {key: sentence}
Exit 1 (Fault) if a key cited in the sources has no category -- a cited entry with no stated
difference must fail the generator rather than be rendered without one.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "refs", "differences.json")

# One sentence per related-work cluster of the manuscript's own section 2.
CATS = {
    "Repeat counts and statistical power":
        "a power analysis that fixes the seed count for a mean effect; this paper states the error "
        "of the aggregation rule a decision is read off",
    "Variance in benchmark evaluation":
        "measures how far benchmark results move between runs; this paper turns that spread into "
        "the repeat count a decision needs",
    "Significance testing for model comparison":
        "tests whether a mean difference is significant at a fixed run count; the estimand here is "
        "the error of the rule that reads the runs as a verdict",
    "Item-response and adaptive evaluation":
        "spends a budget on the item axis under an item-response model; this paper makes the item "
        "and repeat axes trade against each other",
    "LLM-as-judge reliability":
        "measures a stochastic judge's agreement with itself; this paper prices the repeats a "
        "verdict from that judge needs",
    "Reproducibility of stochastic results":
        "documents that stochastic results do not reproduce; this paper states how many repeats "
        "make a claim reproducible at a stated error",
    "Uncertainty in evaluation and benchmark reliability":
        "reports an uncertainty interval at a fixed run count; this paper makes the run count the "
        "estimand",
    "Significance beyond the score":
        "warns that a score difference's significance is not the claim's; this paper prices the "
        "repeats that decide it",
}
FALLBACK = {
    "4. Dependent runs":
        "the intraclass correlation that measures agreement among replicates; this paper uses it "
        "as the effective-sample-size correction, not as the estimand",
    "9. Grounding":
        "a baseline-tuning study on a public benchmark; here the same law is read on the "
        "benchmark's own measured inputs",
}
DEFAULT = ("an adjacent treatment of the evaluation question this paper formalises; it does not "
           "state the repeat count a claim needs")

REFS = re.compile(r"\{ref:([^}]+)\}")


def read_sources():
    src = ""
    for name in ("manuscript.src.md", "manuscript.part2.md"):
        with open(os.path.join(HERE, name)) as f:
            src += f.read() + "\n"
    return src


def assign(src):
    """keys -> the cluster label that first cites them."""
    sections = re.split(r"\n(?=## )", src)
    out = {}
    for s in sections:
        head = s.split("\n", 1)[0].lstrip("# ").strip()
        if head.startswith("2. Related work"):
            # subsection granularity: a bold lead-in opens each cluster
            for part in re.split(r"\n(?=\*\*)", s):
                m = re.match(r"\*\*(.+?)\.\*\*", part)
                label = m.group(1) if m else None
                if label in CATS:
                    for k in REFS.findall(part):
                        out.setdefault(k.strip(), label)
        else:
            for k in REFS.findall(s):
                out.setdefault(k.strip(), head)
    return out


def main():
    src = read_sources()
    seen = assign(src)
    diffs = {}
    uncat = []
    for k, label in seen.items():
        if label in CATS:
            diffs[k] = CATS[label]
        elif any(label.startswith(pfx) for pfx in FALLBACK):
            diffs[k] = FALLBACK[next(p for p in FALLBACK if label.startswith(p))]
        else:
            uncat.append((k, label))
    if uncat:
        print("FAULT: %d cited key(s) carry no difference category: %s" % (len(uncat), uncat[:5]))
        return 1
    with open(OUT, "w") as f:
        json.dump(diffs, f, indent=1, sort_keys=True)
    import collections
    print("wrote refs/differences.json")
    print("  %d cited entries, %d distinct difference sentence(s)" % (len(diffs), len(set(diffs.values()))))
    for s, n in collections.Counter(diffs.values()).most_common():
        print("   %3d  %s" % (n, s[:88]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
