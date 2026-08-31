#!/usr/bin/env python3
"""Issue #52 — component-level language classification (extract.py).

For each of the 32 pinned repos:
  1. Split the recursive tree into top-level source components (dirs containing
     source files; repo root if flat).
  2. Classify each component by source-file extensions + build manifests:
       RUST  — Cargo.toml present or *.rs dominant
       C     — CMake/Makefile/autotools/meson + *.c/*.h dominant
       CPP   — *.cc/*.cpp/*.hpp dominant
       MIXED — Rust and C/C++ both substantial (neither >2x the other)
       OTHER — no source or auxiliary only
  3. Per-repo aggregation: component counts by class, Rust share.
  4. Rust-side repos: binding_vs_rewrite signal from Cargo.toml (build.rs,
     cc/bindgen deps, -sys crates) — BINDING vs REWRITE vs UNCLEAR.

Emits snapshots/component_classes.json + snapshots/repo_signals.json.
Deterministic; reads only committed/pinned inputs (corpus.json + trees/).
"""
import json, re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
TREES = ROOT / "snapshots" / "trees"
CORPUS = json.load(open(ROOT / "corpus.json"))

RS_EXT = {".rs"}
C_EXT = {".c", ".h"}
CPP_EXT = {".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".h++"}
BUILD_RUST = {"Cargo.toml", "Cargo.lock", "build.rs"}
BUILD_C = {"CMakeLists.txt", "Makefile", "Makefile.am", "configure.ac",
           "configure.in", "meson.build", "GNUmakefile"}
SKIP_DIRS = {".git", ".github", "vendor", "third_party", "third-party",
             "contrib", "doc", "docs", "man", "test", "tests", "examples",
             "benchmark", "benchmarks", "fuzz", "target", "build", "cmake",
             ".vscode", ".idea", "licenses", "debian", "packaging"}

def load_tree(repo):
    return json.load(open(TREES / (repo.replace("/", "__") + ".json")))

def split_components(entries):
    """Top-level components: root files -> '' ; top-level dirs -> 'dir/'."""
    comps = {}
    for e in entries:
        if e.get("type") != "blob":
            continue
        path = e["path"]
        parts = path.split("/")
        if len(parts) == 1:
            key = ""
        else:
            key = parts[0] + "/"
        comps.setdefault(key, []).append(path)
    return comps

def classify_component(paths):
    """Language verdict for a component. Pass-B semantic refinement (R96):
    C/C++ files that are FFI-only are AUXILIARY, not implementation:
      - .h/.hpp headers when the component also has Rust (declarations, not impl)
      - files under examples/ include/ tests/ fuzz/ subpaths (demo/shims)
    MIXED requires genuine C/C++ implementation alongside Rust."""
    rs = c_impl = cpp_impl = 0
    has_rust_build = has_c_build = False
    FFI_AUX = ("examples/", "include/", "tests/", "fuzz/", "benches/")
    for p in paths:
        ext = Path(p).suffix.lower()
        is_rust = ext in RS_EXT
        is_c = ext in C_EXT or ext in CPP_EXT
        if not is_rust and not is_c:
            base = Path(p).name
            if base in BUILD_RUST:
                has_rust_build = True
            if base in BUILD_C:
                has_c_build = True
            continue
        if is_rust:
            rs += 1
            continue
        # C/C++: FFI-auxiliary iff header w/ Rust present, or under aux subpath
        aux_subpath = any(s in "/" + p + "/" for s in FFI_AUX)
        if aux_subpath:
            continue  # examples/include/tests are auxiliary
        if ext in (".h", ".hpp", ".hh", ".hxx"):
            # header: decide after we know whether Rust is present (below)
            c_impl += 0  # provisional; headers may be FFI declarations
            continue
        if ext in C_EXT or ext in CPP_EXT:
            if ext in C_EXT:
                c_impl += 1
            else:
                cpp_impl += 1
    # headers: count as implementation only if component has NO Rust
    for p in paths:
        ext = Path(p).suffix.lower()
        if ext not in (".h", ".hpp", ".hh", ".hxx"):
            continue
        if any(s in "/" + p + "/" for s in FFI_AUX):
            continue
        if rs == 0:
            if ext == ".h":
                c_impl += 1
            else:
                cpp_impl += 1
    c = c_impl
    cpp = cpp_impl
    total_src = rs + c + cpp
    if total_src == 0:
        return "OTHER", (rs, c, cpp, has_rust_build, has_c_build)
    # Manifest-aware verdict: a component's own build manifest dominates.
    if has_rust_build and has_c_build and (c + cpp) > 0:
        # dual build system AND actual C/C++ implementation in the same component
        return "MIXED", (rs, c, cpp, has_rust_build, has_c_build)
    if has_rust_build:
        # Rust project; C files here are auxiliary (vendored headers/fixtures);
        # a co-present Makefile without C source is a cargo wrapper, not a C build
        return "RUST", (rs, c, cpp, has_rust_build, has_c_build)
    if has_c_build:
        # C/C++ build system present; but if the source is all-Rust (e.g. a
        # meson.build used for a Rust integration), the manifest alone must not
        # override the source evidence
        if rs > 0 and c + cpp == 0:
            return "RUST", (rs, c, cpp, has_rust_build, has_c_build)
        # decide by extension dominance
        if cpp > 0 and cpp >= c:
            return "CPP", (rs, c, cpp, has_rust_build, has_c_build)
        return "C", (rs, c, cpp, has_rust_build, has_c_build)
    # No build manifest -> extension dominance
    if rs > 0 and rs >= c + cpp:
        return "RUST", (rs, c, cpp, has_rust_build, has_c_build)
    if cpp > 0 and cpp >= c:
        if rs > 0 and rs * 2 >= cpp:
            return "MIXED", (rs, c, cpp, has_rust_build, has_c_build)
        return "CPP", (rs, c, cpp, has_rust_build, has_c_build)
    if c > 0:
        if rs > 0 and rs * 2 >= c:
            return "MIXED", (rs, c, cpp, has_rust_build, has_c_build)
        return "C", (rs, c, cpp, has_rust_build, has_c_build)
    return "OTHER", (rs, c, cpp, has_rust_build, has_c_build)

def main():
    repos = []
    for p in CORPUS["tiers"]["pairs"]:
        for side in ("c_side", "rust_side"):
            repos.append((p[side]["repo"], p[side]["tier"], side))
    result = {}
    for repo, tier, side in repos:
        tree = load_tree(repo)
        comps = split_components(tree["tree"])
        classes = {}
        for key, paths in comps.items():
            # skip vendored/aux dirs
            k = key.rstrip("/")
            if k in SKIP_DIRS or any(s in k for s in ("third_party", "vendor")):
                continue
            cls, stats = classify_component(paths)
            classes[key] = {"class": cls, "rs": stats[0], "c": stats[1],
                            "cpp": stats[2], "rust_build": stats[3],
                            "c_build": stats[4], "files": len(paths)}
        cnt = Counter(v["class"] for v in classes.values())
        result[repo] = {
            "tier": tier, "side": side,
            "components": len(classes),
            "classes": dict(cnt),
            "component_detail": classes,
        }
        print(f"{repo:44s} comps={len(classes):3d} {dict(cnt)}", flush=True)
    json.dump(result, open(ROOT / "snapshots" / "component_classes.json", "w"), indent=2)
    print("wrote snapshots/component_classes.json")

if __name__ == "__main__":
    main()
