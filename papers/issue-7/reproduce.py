"""
reproduce.py — CANONICAL runner for issue #7 "Type-Evident Code".

One command reproduces every number in the manuscript:

    python3 reproduce.py [--corpus <root>] [--check-commits]

Deterministic (stdlib `ast` only, no randomness, no network beyond optional
commit verification). Expected output committed at
`expected_output/manuscript_results.txt`; the README's one-command spec diffs
a fresh run against that file.

Corpus layout (see README / corpus manifest below): <root> contains the 7
shallow clones; each package's *source* subtree is analyzed (tests excluded).

Falsifiable claims reproduced here:
  C1: recoverable fraction of unannotated params from default values alone,
      split into strong (typed literal) vs None-only (optionality) evidence;
      per-package mean with t-CI (n=4 partially-annotated packages).
  C2: annotation coverage and recoverability by package domain.
  C3: redundancy — annotated params whose default's literal type matches the
      annotation; per-package mean with t-CI (n=5 annotated packages).
"""
from __future__ import annotations

import ast
import glob
import math
import os
import subprocess
import sys
from collections import Counter

# --- corpus manifest: package -> (source subtree, pinned commit) --------------
# Pinned 2026-08-25 (research phase R7). These hashes make the corpus
# reproducible: `git clone <url> <root>/<pkg> && git checkout <commit>`.
PACKAGES = {
    "click":    {"src": "click/src/click",       "commit": "2c8cd3ac958a", "domain": "CLI framework"},
    "dateutil": {"src": "dateutil/src/dateutil", "commit": "48bd1af97e71", "domain": "date parsing"},
    "flask":    {"src": "flask/src/flask",       "commit": "d318b6834711", "domain": "web framework"},
    "gunicorn": {"src": "gunicorn/gunicorn",     "commit": "36f2a3c1b80d", "domain": "web server"},
    "httpie":   {"src": "httpie/httpie",         "commit": "5b604c37c6c6", "domain": "CLI"},
    "tqdm":     {"src": "tqdm/tqdm",             "commit": "96f2e60e4584", "domain": "CLI/progress"},
    "typer":    {"src": "typer/typer",           "commit": "9a7b2e83f6b6", "domain": "CLI framework"},
}

LITERAL_TYPES = {
    int: "int", str: "str", float: "float", bool: "bool", type(None): "None",
    bytes: "bytes", list: "list", dict: "dict", set: "set", tuple: "tuple",
}


def const_type(node: ast.AST):
    """Type name of a constant/literal node, or None."""
    if isinstance(node, ast.Constant):
        return LITERAL_TYPES.get(type(node.value))
    if isinstance(node, ast.List):
        return "list"
    if isinstance(node, ast.Tuple):
        return "tuple"
    if isinstance(node, ast.Dict):
        return "dict"
    if isinstance(node, ast.Set):
        return "set"
    if isinstance(node, ast.ListComp):
        return "list"
    if isinstance(node, ast.DictComp):
        return "dict"
    return None


def ann_type_name(node: ast.AST) -> str:
    """Rough type name from an annotation node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Subscript):
        return ast.unparse(node.value)
    if isinstance(node, ast.Attribute):
        return ast.unparse(node)
    if isinstance(node, (ast.List, ast.Tuple)):
        return "list" if isinstance(node, ast.List) else "tuple"
    return ast.unparse(node) if node else "?"


def analyze_file(path: str):
    src = open(path, encoding="utf-8", errors="replace").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    stats = Counter()
    funcs = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        funcs += 1
        pos_args = [a for a in node.args.args if a.arg != "self"]
        n_args = len(node.args.args)
        defaults = [None] * (n_args - len(node.args.defaults)) + list(node.args.defaults)
        arg_defaults = dict(zip([a.arg for a in node.args.args], defaults))
        for a in pos_args:
            stats["params_total"] += 1
            if a.annotation is not None:
                stats["params_annotated"] += 1
                d = arg_defaults.get(a.arg)
                if d is not None:
                    dt = const_type(d)
                    at = ann_type_name(a.annotation)
                    if dt and at and at.lower() == dt:
                        stats["params_redundant"] += 1
            else:
                stats["params_unannotated"] += 1
                d = arg_defaults.get(a.arg)
                if d is not None:
                    dt = const_type(d)
                    if dt:
                        stats[f"evident_default_{dt}"] += 1
        if node.returns is not None:
            stats["ret_annotated"] += 1
        else:
            stats["ret_unannotated"] += 1
            if (len(node.body) == 1 and isinstance(node.body[0], ast.Return)
                    and node.body[0].value is not None
                    and const_type(node.body[0].value)):
                stats["evident_return_constant"] += 1
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) \
                    and sub.func.id == "isinstance" and len(sub.args) == 2 \
                    and isinstance(sub.args[0], ast.Name) \
                    and isinstance(sub.args[1], ast.Name):
                stats[f"guard_{sub.args[1].id}"] += 1
                stats["isinstance_guards"] += 1
    return {"file": path, "funcs": funcs, "stats": stats}


def analyze_package(root: str):
    files = []
    for pat in ("**/*.py", "*.py"):
        files.extend(glob.glob(os.path.join(root, pat), recursive=True))
    files = [f for f in files if "/test" not in f and "/tests" not in f
             and "test_" not in os.path.basename(f)]
    agg = Counter()
    n_files = 0
    for f in sorted(files):
        r = analyze_file(f)
        if r is None:
            continue
        n_files += 1
        agg.update(r["stats"])
    return n_files, agg


def pct(part, whole):
    return 100.0 * part / whole if whole else 0.0


def t_ci(values):
    """95% two-sided t-CI on per-package percentages: mean ± t*sd/sqrt(n)."""
    n = len(values)
    if n < 2:
        return values[0] if n else float("nan"), float("nan"), n
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    sd = math.sqrt(var)
    # t_{n-1, 0.975}: n=4 -> 3.182, n=5 -> 2.776, n=6 -> 2.571, n=7 -> 2.447
    t_table = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365}
    t = t_table.get(n, 2.0)
    return mean, t * sd / math.sqrt(n), n


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Canonical runner for issue #7")
    ap.add_argument("--corpus", default="corpus", help="root dir containing the 7 pinned clones")
    ap.add_argument("--check-commits", action="store_true",
                    help="verify each clone is at its pinned commit (needs network-free local git)")
    args = ap.parse_args()

    if args.check_commits:
        for pkg, meta in PACKAGES.items():
            d = os.path.join(args.corpus, pkg)
            try:
                head = subprocess.run(
                    ["git", "-C", d, "rev-parse", "--short=12", "HEAD"],
                    capture_output=True, text=True, check=True).stdout.strip()
            except Exception as e:
                print(f"WARN: cannot read commit for {pkg}: {e}")
                continue
            ok = head == meta["commit"]
            print(f"commit-check {pkg}: {head} {'OK' if ok else 'MISMATCH (expected ' + meta['commit'] + ')'}")

    rows = []
    for pkg, meta in PACKAGES.items():
        root = os.path.join(args.corpus, meta["src"])
        n_files, agg = analyze_package(root)
        s = agg
        tot = s["params_total"]
        ann = s["params_annotated"]
        unann = s["params_unannotated"]
        evident = sum(v for k, v in s.items() if k.startswith("evident_default_"))
        evident_none = s.get("evident_default_None", 0)
        evident_strong = evident - evident_none
        ret_un = s["ret_unannotated"]
        ret_ev = s["evident_return_constant"]
        redund = s["params_redundant"]
        guards = s["isinstance_guards"]
        print(f"\n=== {pkg} [{meta['domain']}] ({n_files} files) ===")
        print(f"  params: {tot} total | {ann} annotated ({pct(ann, tot):.1f}%) | {unann} unannotated")
        print(f"  unannotated: {evident} default-evident ({pct(evident, unann):.1f}%) "
              f"— strong(typed) {evident_strong} ({pct(evident_strong, unann):.1f}%), "
              f"None-only {evident_none} ({pct(evident_none, unann):.1f}%)")
        for k in sorted(k for k in s if k.startswith("evident_default_")):
            print(f"    - {k.replace('evident_default_', '')}: {s[k]}")
        print(f"  returns: {s['ret_annotated']} annotated | {ret_un} unannotated "
              f"({ret_ev} constant-evident, {pct(ret_ev, ret_un):.1f}%)")
        print(f"  redundancy: {redund} annotated params whose default type matches "
              f"({pct(redund, ann):.1f}% of annotated)")
        print(f"  isinstance guards naming types: {guards}")
        decomp = {k.replace("evident_default_", ""): v
                  for k, v in s.items() if k.startswith("evident_default_")}
        rows.append({
            "package": pkg, "domain": meta["domain"], "files": n_files,
            "params_total": tot, "params_annotated": ann, "params_unannotated": unann,
            "evident": evident, "evident_pct": pct(evident, unann),
            "strong": evident_strong, "strong_pct": pct(evident_strong, unann),
            "none": evident_none, "none_pct": pct(evident_none, unann),
            "ret_annotated": s["ret_annotated"], "ret_unannotated": ret_un,
            "ret_evident": ret_ev, "ret_evident_pct": pct(ret_ev, ret_un),
            "redundant": redund, "redundant_pct": pct(redund, ann),
            "guards": guards, "decomp": decomp,
        })

    # ---- aggregate (pooled, weighted) ----
    tot_p = sum(r["params_total"] for r in rows)
    tot_ann = sum(r["params_annotated"] for r in rows)
    tot_un = sum(r["params_unannotated"] for r in rows)
    tot_ev = sum(r["evident"] for r in rows)
    tot_strong = sum(r["strong"] for r in rows)
    tot_none = sum(r["none"] for r in rows)
    tot_red = sum(r["redundant"] for r in rows)
    print("\n=== aggregate (pooled over 7 packages) ===")
    print(f"params: {tot_p} total | {tot_ann} annotated | {tot_un} unannotated ({pct(tot_un, tot_p):.1f}%)")
    print(f"C1  default-evident: {tot_ev}/{tot_un} = {pct(tot_ev, tot_un):.1f}% of unannotated")
    print(f"C1  strong(typed):   {tot_strong}/{tot_un} = {pct(tot_strong, tot_un):.1f}% of unannotated")
    print(f"C1  None-only:       {tot_none}/{tot_un} = {pct(tot_none, tot_un):.1f}% of unannotated")
    decomp = Counter()
    for r in rows:
        decomp.update(r["decomp"])
    print("C1  evidence decomposition: " + ", ".join(
        f"{k} {v}" for k, v in sorted(decomp.items(), key=lambda kv: -kv[1])))
    print(f"C3  redundant:       {tot_red}/{tot_ann} = {pct(tot_red, tot_ann):.1f}% of annotated")
    print(f"isinstance guards total: {sum(r['guards'] for r in rows)}")

    # ---- per-package statistics + t-CI (packages are the sampling unit) ----
    # C1 population of interest: PARTIALLY-annotated packages (annotation
    # coverage < 95%) — fully-annotated packages (click/flask/typer ~99-100%)
    # have no annotation burden to recover, so they are outside C1's scope.
    # C3 population: packages with annotated params (>=1).
    c1_pkgs = [r for r in rows if r["params_annotated"] / max(1, r["params_total"]) < 0.95]
    c3_pkgs = [r for r in rows if r["params_annotated"] > 0]
    print("\n=== per-package means with 95% t-CI (packages as sampling unit) ===")
    for label, vals in (
        ("C1 total default-evident %", [r["evident_pct"] for r in c1_pkgs]),
        ("C1 strong(typed) %        ", [r["strong_pct"] for r in c1_pkgs]),
        ("C1 None-only %            ", [r["none_pct"] for r in c1_pkgs]),
        ("C3 redundancy %           ", [r["redundant_pct"] for r in c3_pkgs]),
        ("ret constant-evident %    ", [r["ret_evident_pct"] for r in c1_pkgs]),
    ):
        m, hw, n = t_ci(vals)
        print(f"{label}: mean {m:.1f}% ± {hw:.1f}% (n={n})")

    print("\npackages in C1 (coverage<95%): " + ", ".join(r["package"] for r in c1_pkgs))
    print("packages in C3 (annotated>0):   " + ", ".join(r["package"] for r in c3_pkgs))


if __name__ == "__main__":
    main()
