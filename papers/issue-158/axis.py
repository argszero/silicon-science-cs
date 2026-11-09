"""axis.py -- the paper's axis measured at the count that carries the evidence.

The manuscript's central number is a correlation between the local resolution of a distance and the
size of the boundary tie group it produces, and the manuscript says in section 8 that the evidence
count is the CONFIGURATION count, not the cell count: three seeds of one configuration are one
configuration measured thrice, so the seed-level cells are not independent observations.

A statistic and the minimum effect it must clear have to sit on the same denominator. They did not
until review M2 (2026-11-09): section 8 declared the configuration count the evidence count, then
quoted a threshold computed over the seed-level cells. Two sets of numbers are therefore produced
here, each labelled with the set it is composed over:

  * `configs` -- one (mean resolution, mean tie group) per (family, budget) configuration, the
    evidence count. This is the pair the manuscript quotes.
  * `cells`   -- one point per seed-level cell, the finer view. Reported beside the first and named
    for what it is, never as the evidence count.

The module is stdlib-only on purpose: make_manuscript.py renders the paper in environments where
numpy is absent (reproduce.sh step 6 runs it that way), so anything it needs cannot import
tiefloor.py, which is built on numpy.

Pure functions of their arguments; nothing here reads or writes a file.
"""

import math

# The two endpoint controls pin the instrument's ends and are not quantiser families: the float cell
# carries no code at all and the constructed one is a corpus rather than a code. Counting either as a
# configuration reports a set one member larger than the set the correlations are composed over --
# which is what the printed count did until review M1. They stay in the artefact; they are excluded
# from counts and from correlations.
CONTROL_PREFIXES = ("float", "constructed")

# Fisher-z constants for the minimum detectable effect: two-sided, conventional power.
Z_ALPHA, Z_POWER = 1.959963985, 0.8416212336


def is_family_cell(cell):
    return not cell["tag"].startswith(CONTROL_PREFIXES)


def config_key(cell):
    """The (family, budget) a cell belongs to -- 'Hamming/32bit/seed7' -> ('Hamming', '32bit')."""
    return tuple(cell["tag"].split("/")[:2])


def family_cells(cells):
    return [c for c in cells if is_family_cell(c)]


def configs_of(cells):
    """Distinct (family, budget) configurations over the FAMILY cells -- the evidence count."""
    return len({config_key(c) for c in family_cells(cells)})


def config_means(cells):
    """One (mean resolution, mean tie group) per configuration, in sorted key order.

    The mean is over the configuration's seeds. This is the unit the paper treats as independent,
    so it is the unit the correlation and its threshold are computed on.
    """
    groups = {}
    for c in family_cells(cells):
        groups.setdefault(config_key(c), []).append(c)
    keys = sorted(groups)
    xs = [sum(c["median_atoms"] for c in groups[k]) / len(groups[k]) for k in keys]
    ys = [sum(c["median_t"] for c in groups[k]) / len(groups[k]) for k in keys]
    return keys, xs, ys


def pearson_logs(xs, ys):
    """Pearson correlation on the logs of both axes -- the axis the paper's claim is stated on."""
    lx = [math.log(x) for x in xs]
    ly = [math.log(y) for y in ys]
    mx, my = sum(lx) / len(lx), sum(ly) / len(ly)
    num = sum((a - mx) * (b - my) for a, b in zip(lx, ly))
    den = math.sqrt(sum((a - mx) ** 2 for a in lx) * sum((b - my) ** 2 for b in ly))
    if den == 0:
        return float("nan")
    return num / den


def mde(n):
    """Smallest |r| a design with n independent points can detect (Fisher z, two-sided, power 0.8).

    This is a property of the design, not of the data: it says how large an effect had to be for this
    study to see one at all, which is what makes a refutation readable as evidence rather than as an
    absence of it (issue #2318).
    """
    return math.tanh((Z_ALPHA + Z_POWER) / math.sqrt(max(n - 3, 1)))


def at_evidence_count(cells):
    """The axis as the paper reports it: correlation and threshold over the configuration means."""
    keys, xs, ys = config_means(cells)
    n = len(keys)
    return {"n_configs": n,
            "log_log_pearson_configs": round(pearson_logs(xs, ys), 4),
            "mde_pearson_configs": round(mde(n), 4)}


def at_cell_count(cells, r, m):
    """The same pair over the seed-level cells, labelled as the finer view rather than the design."""
    fam = family_cells(cells)
    return {"n_cells": len(fam), "log_log_pearson": round(r, 4), "mde_pearson": round(m, 4)}
