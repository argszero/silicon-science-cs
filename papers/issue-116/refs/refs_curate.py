#!/usr/bin/env python3
"""Issue #116 -- CURATION: choose which discovered entries the paper will cite.

Reads refs/candidates.json and a hand-written selection of arXiv ids (grouped by
the role each plays in the argument), pulls every TITLE FROM THE DISCOVERY FILE
(never retyped, so a title cannot drift from what the index returned), and writes
refs/refs_keys.json.

A selected id that is not in the discovery file is a hard error unless it is listed
in EXTRAS with an explicit reason -- so an id can never be invented silently.

Usage: python3 refs_curate.py
"""
import hashlib
import json

CAND = "refs/candidates.json"
OUT = "refs/refs_keys.json"

# id -> the role the entry plays. Titles come from the discovery file.
SELECT = {
    "R1_chunked_policy_horizon": [
        "2608.02547", "2511.04421", "2408.17355", "2609.36250", "2507.07969", "2605.15944",
        "2603.01891", "2604.06067", "2605.19592", "2607.12992", "2605.25537",
        "2512.05964", "2604.25050", "2609.27167", "2410.16981", "2609.39873",
        "2606.22540", "2603.18091", "2609.03715", "2608.15938", "2604.02965",
        "2403.09504", "2002.06836", "2608.00793", "2609.19200",
    ],
    "R2_policy_latency_efficiency": [
        "2605.00884", "2609.34319", "2607.12287", "2608.12932", "2609.17210",
        "2607.02646", "2609.18732", "2606.17040", "2609.36967",
    ],
    "R3_delay_networked_sampled_data": [
        "2409.05113", "2004.08332", "1803.09487", "1902.06235", "1811.07534",
        "1912.08734", "2303.08428", "2101.00649", "1904.12660", "1512.04797",
        "1604.06350", "2112.14507", "1903.06368", "1906.01434",
    ],
    "R4_staleness_anytime_imprecise": [
        "1810.10983", "1701.06927", "1506.08637", "2403.08807", "1301.7384", "2603.08493",
        "2011.01112", "1905.04391", "1306.0448", "1007.0683", "2405.14636",
        "2603.06403", "2512.18725", "2510.06153",
    ],
    "R5_receding_horizon_and_horizon_length": [
        "1402.4568", "1208.3830", "2206.04477", "2102.11122", "2404.16391",
        "2108.08014", "2511.09290", "2609.22276",
    ],
    "R6_lqg_lyapunov_covariance": [
        "1807.10715", "2605.15926", "1507.02100", "2406.07324", "2003.05999",
        "1807.04700", "2004.08932", "2511.14358", "2602.07425", "2602.18002",
        "2211.00867", "1010.2265", "2104.10383", "1511.03488", "1410.5083", "2305.19262",
        "2204.06207",
    ],
    "R7_abstraction_options_macro": [
        "2102.12571", "2012.14942", "2004.08646", "2011.03813", "1301.7381",
        "2507.10251", "2506.13690",
    ],
    "R8_amortization_and_compute": [
        "1805.08913", "1610.05735", "2404.12484", "2205.11640", "2608.08644",
    ],
    "R9_disturbance_and_saturation": [
        "2101.02859", "1902.09032", "1912.06331", "1311.0388", "2504.08005",
        "1608.03729", "2602.18247", "2110.13356",
    ],
    "R10_setting_control_and_manipulation": [
        "2406.06005", "2408.00342", "2204.05681", "2210.10549", "2107.08149",
        "2003.02327", "1612.01554", "2209.08728", "2308.14265",
        "2603.25981", "2506.01392", "1709.10087", "2504.03515", "2203.13251",
        "2203.08098", "2205.14292", "2010.04296", "2403.00336", "2312.11374",
        "2011.00778", "1811.08067", "2311.09062",
    ],
}

# Entries that are NOT in the discovery file, each with the reason it is admitted.
# The registration's own anchors, already verified by identifier in earlier rounds.
DOI_EXTRAS = {
    "10.15607/rss.2023.xix.016": "R1_chunked_policy_horizon",
}

EXTRAS = {
    "2606.00537": "R1_chunked_policy_horizon",
    "2609.36471": "R1_chunked_policy_horizon",
    "2609.37772": "R1_chunked_policy_horizon",
    "2609.36540": "R1_chunked_policy_horizon",
}


def load_verified():
    """Preserve the fields another step owns: curate decides WHAT is cited,
    refs_tool decides WHETHER it exists. Re-running curate must not erase the
    verification record (it did, once -- the titles were then restored from the
    verifier's own log)."""
    try:
        prev = json.load(open(OUT))["keys"]
    except Exception:                                          # noqa: BLE001
        return {}
    keep = ("verified_title", "verified_year", "verified_published")
    return {k: {f: v[f] for f in keep if f in v} for k, v in prev.items()}


def main():
    prior = load_verified()
    disc = json.load(open(CAND))
    by_id = {c["arxiv"]: c for c in disc["candidates"]}
    keys, missing = {}, []
    roles = {}
    for role, ids in SELECT.items():
        roles[role] = []
        for i in ids:
            c = by_id.get(i)
            if c is None:
                missing.append((role, i))
                continue
            keys[i] = {"arxiv": i, "title": c["title"], "published": c["published"],
                       "category": c["category"], "role": role}
            roles[role].append(i)
    for i, role in EXTRAS.items():
        if i in keys:
            continue
        keys[i] = {"arxiv": i, "title": None, "published": None,
                   "category": None, "role": role, "source": "registration anchor"}
        roles.setdefault(role, []).append(i)
    for i, role in DOI_EXTRAS.items():
        keys[i] = {"doi": i, "title": None, "published": None, "category": None,
                   "role": role, "source": "registration anchor (DOI, Crossref-verified)"}
        roles.setdefault(role, []).append(i)
    for k, extra in prior.items():                 # carry the verifier's record over
        if k in keys:
            keys[k].update(extra)
    if missing:
        raise SystemExit("SELECTED IDS NOT IN THE DISCOVERY FILE (would be invented "
                         "citations):\n  " + "\n  ".join(f"{r} {i}" for r, i in missing))
    out = {"n": len(keys), "by_role_count": {r: len(v) for r, v in roles.items()},
           "keys": keys}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(f"{len(keys)} curated entries -> {OUT}")
    for r in sorted(roles):
        print(f"  {r:<42} {len(roles[r]):>3}")
    print("sha256", hashlib.sha256(open(OUT, "rb").read()).hexdigest())
    print("NOTE: curation decides what is CITED. Titles of discovery entries are"
          " copied from candidates.json; the 4 EXTRAS carry no title here and are"
          " resolved by refs_tool.py, which is the only authority on existence.")


if __name__ == "__main__":
    main()
