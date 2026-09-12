"""Figures and the result table for issue #1, generated from the canonical artefact.

Deterministic by construction: Agg backend, fixed figure size and dpi, PNG metadata stripped of
the Software tag, and a fixed output order. Each figure's sha256 and the exact data arrays it plots
are recorded in figures/manifest.json, so every plotted number is traceable to
canonical_results.json (the canonical-run traceability the journal's bar requires).

Usage:  python3 make_figures.py      (run from this directory)
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARTIFACT = os.path.join(HERE, "canonical_results.json")
FIGDIR = os.path.join(HERE, "figures")

# Colour-blind safe pair used consistently across figures.
C_READ = "#1b6ca8"
C_RETR = "#c1440e"


def load():
    if not os.path.exists(ARTIFACT):
        raise SystemExit("canonical_results.json not found in %s - run canonical_runner.py first" % HERE)
    try:
        import matplotlib
    except ImportError:
        raise SystemExit("matplotlib is required to build the figures and is not importable by %s.\n"
                         "Install it (pip install matplotlib) or run this script with an interpreter that has it." % sys.executable)
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return json.load(open(ARTIFACT, encoding="utf-8")), plt


def save(fig, plt, name):
    path = os.path.join(FIGDIR, name)
    fig.savefig(path, format="png", dpi=140, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    return {"file": "figures/" + name,
            "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
            "bytes": os.path.getsize(path)}


def pooled(grid, key):
    """Mean of a per-cell field over the two instances, by interference level, pooled over lengths."""
    out = {}
    for row in grid:
        out.setdefault(row["I"], []).append(row[key])
    return {I: sum(v) / len(v) for I, v in sorted(out.items())}


def fig1_crossover(art, plt):
    """Core outcome: the comparison as a function of interference, and the gap that defines it."""
    grid = art["derived"]["main_grid"]
    Is = sorted({row["I"] for row in grid})
    read = pooled(grid, "full")
    retr = pooled(grid, "dense_k4")
    gap = art["derived"]["gap_by_interference"]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
    ax.plot(Is, [read[I] for I in Is], "o-", color=C_READ, lw=2, ms=6,
            label="full-context reading")
    ax.plot(Is, [retr[I] for I in Is], "s-", color=C_RETR, lw=2, ms=6,
            label="dense retrieval (k=4)")
    ax.axvspan(0.02, max(Is) + 0.04, color=C_READ, alpha=0.06, lw=0)
    ax.annotate("reading wins\n(28 of 30 distractor cells)", xy=(0.42, -0.55), ha="center",
                fontsize=9, color=C_READ)
    ax.annotate("the zero-distractor rung\nis a null, not a lead", xy=(0.0, 0.02), xytext=(0.10, 0.28),
                fontsize=9, color=C_RETR,
                arrowprops=dict(arrowstyle="->", color=C_RETR, lw=1.2))
    ax.set_xlabel("interference density $I$ (share of confusable distractor records)")
    ax.set_ylabel("gold-answer log-probability (nats)")
    ax.set_title("(a) The comparison inverts at the interference boundary", fontsize=10)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8.5, loc="lower left", frameon=False)

    xs = [float(k) for k in gap]
    ys = [gap[k] for k in gap]
    ax2.axhline(0.0, color="#555", lw=1)
    ax2.bar(xs, ys, width=0.055, color=[C_RETR if y > 0 else C_READ for y in ys])
    ax2.set_xlabel("interference density $I$")
    ax2.set_ylabel("retrieval minus reading (nats)")
    ax2.set_title("(b) The deficit appears at once, then saturates", fontsize=10)
    ax2.grid(alpha=0.25, axis="y")
    ax2.annotate("+0.06", xy=(0.0, ys[0]), xytext=(0.0, ys[0] + 0.22), ha="center",
                 fontsize=8.5, color=C_RETR)
    ax2.annotate("saturates near $-1$ nat\n(no interior threshold)", xy=(0.62, -1.0),
                 fontsize=8.5, color=C_READ, ha="center")
    return save(fig, plt, "fig1_crossover.png"), {"I": Is, "reading": [read[I] for I in Is],
                                                  "retrieval": [retr[I] for I in Is], "gap": ys}


def fig2_type(art, plt):
    """Distractor type at matched density, WITH the recall-matched control that qualifies it."""
    d = art["derived"]
    unmatched = [(d["type_contrast_dense4"]["same_entity_status"] - d["type_contrast"]["same_entity_status"],
                  d["type_contrast_dense4"]["different_entity"] - d["type_contrast"]["different_entity"])]
    ms = d["type_contrast_matched_subset"]
    matched = [(ms["status_retrieval_k4"] - ms["status_reading"],
                ms["entity_retrieval_k4"] - ms["entity_reading"])]
    x = [0, 1]
    w = 0.36
    fig, ax = plt.subplots(figsize=(5.6, 3.9))
    ax.bar([i - w / 2 for i in x], unmatched[0], w, color=C_RETR,
           label="unmatched (gold outside k=4 for status)")
    ax.bar([i + w / 2 for i in x], matched[0], w, color=C_READ,
           label="recall-matched (%d pairs, gold in k=4 both)" % ms["n_pairs"])
    for i, (u, m) in enumerate(zip(unmatched[0], matched[0])):
        ax.text(i - w / 2, u + (0.06 if u >= 0 else -0.06), "%.2f" % u, ha="center",
                va="bottom" if u >= 0 else "top", fontsize=8.5, color=C_RETR)
        ax.text(i + w / 2, m + (0.06 if m >= 0 else -0.06), "%.2f" % m, ha="center",
                va="bottom" if m >= 0 else "top", fontsize=8.5, color=C_READ)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["same entity,\ndiffering status\n(confusable)", "different entity\n(separable)"])
    ax.set_ylabel("retrieval minus reading (nats)")
    ax.set_title("Matched length and density: the two-nat type contrast\nis a rank contrast, not a discrimination margin",
                 fontsize=10)
    ax.grid(alpha=0.25, axis="y")
    ax.legend(fontsize=8, frameon=False, loc="lower center")
    return save(fig, plt, "fig2_distractor_type.png"), {
        "unmatched_same_entity_gap": unmatched[0][0], "unmatched_different_entity_gap": unmatched[0][1],
        "matched_same_entity_gap": matched[0][0], "matched_different_entity_gap": matched[0][1],
        "matched_n_pairs": ms["n_pairs"],
        "matched_difference": ms["gap_difference_entity_minus_status"],
        "matched_difference_lo": ms["difference_ci"]["lo"],
        "matched_difference_hi": ms["difference_ci"]["hi"]}


def fig3_position(art, plt):
    """Evidence position dominates the reader side, while retrieval cannot see position at all."""
    grid = art["derived"]["main_grid"]
    pos = {float(k): v for k, v in art["derived"]["position"].items()}
    fracs = sorted(pos)
    # sampled exact rate at the same cells, from the position ladder (L=256, I=0.60)
    # The position ladder is carried by two arms: the POSITION arm at 0.00 / 0.25 / 0.75 / 1.00 and
    # the MAIN arm at the mid-point 0.50. Take both so the two panels describe the same five cells.
    cells = [c for c in art["sweep"]["cells"]
             if c["n_chunks"] == 256 and c["interference"] == 0.6
             and c["arm"] in ("POSITION", "MAIN")]
    rate = {}
    for c in cells:
        rate.setdefault(c["gold_frac"], []).append(c["full"]["sampled_exact_rate"])
    rate = {k: sum(v) / len(v) for k, v in sorted(rate.items())}
    rfrac = sorted(rate)
    # the retrieval arm cannot see position: one reference line, averaged over the ladder
    retr_ref = sum(c["dense_k4"]["mean_logprob"] for c in cells) / len(cells)

    if fracs != rfrac:
        raise SystemExit("position panels disagree on the sampled points: %s against %s" % (fracs, rfrac))
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
    ax.plot(fracs, [pos[f] for f in fracs], "o-", color=C_READ, lw=2, ms=6)
    ax.axvspan(0.20, 0.80, color="#c1440e", alpha=0.06, lw=0)
    ax.axhline(retr_ref, color=C_RETR, ls="--", lw=1.4,
               label="dense retrieval (k=4), position-independent")
    ax.set_xlabel("position of the gold record in the context (fraction)")
    ax.set_ylabel("gold-answer log-probability (nats)")
    ax.set_title("(a) Reading is U-shaped in evidence position", fontsize=10)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8.5, frameon=False, loc="lower center")

    ax2.bar(rfrac, [rate[f] for f in rfrac], width=0.13, color=C_READ)
    ax2.set_xlabel("position of the gold record in the context (fraction)")
    ax2.set_ylabel("sampled exact-match rate (4 seeds)")
    ax2.set_title("(b) Sampling agrees: the interior is unanswerable", fontsize=10)
    ax2.set_ylim(0, 1.0)
    ax2.grid(alpha=0.25, axis="y")
    for f in rfrac:
        ax2.text(f, rate[f] + 0.03, "%.2f" % rate[f], ha="center", fontsize=8.5)
    return save(fig, plt, "fig3_position.png"), {"fracs": fracs, "reading": [pos[f] for f in fracs],
                                                 "sampled_exact": {str(f): rate[f] for f in rfrac},
                                                 "retrieval_reference": round(retr_ref, 4)}


def results_table(art):
    """Markdown result table, generated from the canonical artefact so it cannot drift."""
    grid = art["derived"]["main_grid"]
    d = art["derived"]
    lines = []
    lines.append("| context (chunks) | interference | reading | retrieval k=4 | gap | greedy exact | sampled exact (Wilson 95%) |")
    lines.append("|---|---|---|---|---|---|---|")
    wil = {(r["L"], r["I"]): r for r in d["sampled_wilson"]}
    for row in grid:
        w = wil.get((row["L"], row["I"]))
        ci = "[%.3f, %.3f]" % (w["lo"], w["hi"]) if w else "-"
        lines.append("| %d | %.2f | %+.3f | %+.3f | %+.3f | %d/2 | %.3f %s |" % (
            row["L"], row["I"], row["full"], row["dense_k4"], row["gap_dense4"],
            row["greedy_exact"], row["sampled_exact_mean"], ci))
    out = ["# Result table (generated from canonical_results.json)", "",
           "Gold-answer mean log-probability in nats; retrieval is the dense retriever at $k=4$. "
           "Sampled exact intervals are Wilson 95% over 8 decodes (2 instances x 4 seeds).", ""] + lines
    out += ["", "## Summary statistics", "",
            "- retrieval minus reading, by interference: " + ", ".join(
                "%.2f: %+.3f" % (float(k), v) for k, v in sorted(d["gap_by_interference"].items())),
            "- retrieval's point estimate is ahead in %d of %d cells on the zero-interference rung and in %d of %d distractor cells" % (
                d["retrieval_ahead_no_distractor"], d["n_no_distractor"],
                d["retrieval_ahead_with_distractor"], d["n_with_distractor"]),
            "- length-only sweep (reading, I=0): " + ", ".join(
                "L=%s: %+.3f" % (k, v) for k, v in sorted(d["length_only"].items())),
            "- distractor type at matched density: same-entity reading %+.3f against retrieval %+.3f; "
            "different-entity reading %+.3f against retrieval %+.3f" % (
                d["type_contrast"]["same_entity_status"], d["type_contrast_dense4"]["same_entity_status"],
                d["type_contrast"]["different_entity"], d["type_contrast_dense4"]["different_entity"]),
            "- evidence position (reading): " + ", ".join(
                "%s: %+.3f" % (k, v) for k, v in sorted(d["position"].items(), key=lambda kv: float(kv[0]))),
            "- pooled gold recovery over the %d distractor cells: dense %s (k=1), %s (k=4), %s (k=8); BM25 %s (k=4)" % (
                d["n_with_distractor"], d["pooled_recall_distractor_cells"]["dense_k1"],
                d["pooled_recall_distractor_cells"]["dense_k4"],
                d["pooled_recall_distractor_cells"]["dense_k8"], d["pooled_recall_bm25_k4"]),
            ""]
    text = "\n".join(out)
    path = os.path.join(HERE, "results_table.md")
    open(path, "w", encoding="utf-8").write(text)
    return {"file": "results_table.md", "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "bytes": len(text.encode())}


def main():
    art, plt = load()
    os.makedirs(FIGDIR, exist_ok=True)
    manifest = {"artifact_sha256": art.get("sha256"), "figures": []}
    f1, d1 = fig1_crossover(art, plt)
    f2, d2 = fig2_type(art, plt)
    f3, d3 = fig3_position(art, plt)
    for f, data in ((f1, d1), (f2, d2), (f3, d3)):
        f["plotted"] = data
        manifest["figures"].append(f)
        print("%-32s %8d bytes  %s" % (f["file"], f["bytes"], f["sha256"][:16]))
    tbl = results_table(art)
    manifest["table"] = tbl
    print("%-32s %8d bytes  %s" % (tbl["file"], tbl["bytes"], tbl["sha256"][:16]))
    mpath = os.path.join(FIGDIR, "manifest.json")
    blob = json.dumps(manifest, indent=1, sort_keys=True)
    open(mpath, "w", encoding="utf-8").write(blob)
    print("FIGURES DONE | manifest sha256 %s" % hashlib.sha256(blob.encode()).hexdigest()[:16])


if __name__ == "__main__":
    main()
