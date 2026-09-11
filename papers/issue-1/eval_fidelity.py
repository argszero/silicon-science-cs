"""Fidelity validation for the issue-1 dependency-free reader port.

Gate: no study number may be reported before this harness passes.
Checks:
 1 tokenizer round-trip exactness on held-out prose and unicode edge cases
 2 vocabulary idempotence over every merged token in the 49152-token vocab
 3 held-out bits-per-token and perplexity over 512-token windows
 4 comparison baselines: uniform, unigram (add-1), interpolated bigram
 5 power check: four deliberate implementation corruptions must degrade the metric
 6 task-level sanity: planted-evidence scoring under oracle, full-context, no-evidence
 7 determinism: repeated computation yields a byte-identical results digest

Writes fidelity_results.json next to this file. Offline by construction.
"""
import glob, hashlib, json, math, os, sys, time
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
import smollm_port as port

SNAP = port.snap("HuggingFaceTB/SmolLM2-135M")
CFG_PATH = os.path.join(SNAP, "config.json")
WTS_PATH = os.path.join(SNAP, "model.safetensors")
VOCAB_SIZE = 49152


def corpus_docs():
    """Held-out English prose: the FROZEN corpus shipped with this package.

    The documents are frozen in fidelity_corpus.json so this gate is identical in every clone,
    instead of depending on which manuscripts happen to exist in the working tree. They are the
    author's own previously written manuscripts plus journal READMEs, used only as a
    natural-English perplexity probe; the file carries its own provenance note.
    """
    cands = [os.path.join(HERE, "fidelity_corpus.json"),
             os.path.join(HERE, os.pardir, "fidelity_corpus.json")]
    path = next((os.path.abspath(c) for c in cands if os.path.exists(c)), None)
    if path is None:
        raise SystemExit(
            "fidelity_corpus.json not found next to this script (looked in " +
            " and ".join(os.path.abspath(c) for c in cands) + ").\n" +
            "The reader-fidelity gate scores its held-out perplexity on a frozen corpus; " +
            "without the file the gate cannot run and no number in this package is verifiable.")
    blob = json.load(open(path, encoding="utf-8"))
    docs = [(d["name"], d["text"]) for d in blob["docs"]]
    if len(docs) != blob.get("documents"):
        raise SystemExit("fidelity_corpus.json is internally inconsistent: %d docs against a declared %s"
                         % (len(docs), blob.get("documents")))
    return docs


EDGE_CASES = [
    "Hello world",
    "The access code for room 42 is 7183.",
    "\u4e2d\u6587\u6d4b\u8bd5\uff1a\u8bb0\u5fc6\u4f53\u7cfb\u7edf\u7684\u8fb9\u754c\u5728\u54ea\u91cc\uff1f",
    "emoji \U0001f9e0\U0001f680 and flags \U0001f1e8\U0001f1f3",
    "combining marks: e\u0301 a\u0308 n\u0303",
    "   leading and trailing   spaces   ",
    "tabs\there\nand\nnewlines\n\n\n",
    "code: def f(x): return x ** 2  # note",
    "url https://example.org/a?b=c\u0026d=e",
    "numbers 0 1 12 123 1234 12345 1234567890",
    "punctuation ! \" # $ % \u0026 ' ( ) * + , - . / : ; @ [ ] ^ _ ` { | } ~",
    "zero\u200bwidth\u200bjoin\u200ber",
    "mixed CJK and latin: \u65e5\u672c\u8a9e text \u6df7\u5408 123",
    "repeated   spaces     and\ttabs",
    "dash - hyphen - em \u2014 dash \u2013 en",
]


def check_tokenizer():
    docs = corpus_docs()
    rt_total = 0
    rt_ok = 0
    rt_fail = []
    for name, t in docs:
        for i in range(0, max(1, len(t) - 420), 700):
            chunk = t[i:i + 400]
            if len(chunk.strip()) < 40:
                continue
            rt_total += 1
            if tok.decode(tok.encode(chunk)) == chunk:
                rt_ok += 1
            elif len(rt_fail) < 4:
                rt_fail.append([name, i, chunk[:80]])
    edge_ok = sum(1 for s in EDGE_CASES if tok.decode(tok.encode(s)) == s)
    edge_fail = [s[:40] for s in EDGE_CASES if tok.decode(tok.encode(s)) != s]
    added_ids = set()
    try:
        tj = json.load(open(os.path.join(SNAP, "tokenizer.json")))
        added_ids = set(int(t["id"]) for t in tj.get("added_tokens", []))
    except Exception:
        pass
    bad_ids = []
    bad_total = 0
    bad_special = 0
    bad_set = set()
    ids = sorted(int(v) for v in tok.vocab.values())
    for tid in ids:
        text = tok.decode([tid])
        if tok.encode(text) != [tid]:
            bad_total += 1
            bad_set.add(tid)
            if (text.startswith(chr(60)) and text.endswith(chr(62))) or text.startswith(chr(60) + "|"):
                bad_special += 1
            if len(bad_ids) < 16:
                bad_ids.append([tid, text[:24]])
    inv = {v: k for k, v in tok.b2u.items()}

    def raw_bytes(tid):
        out = bytearray()
        for ch in tok.ids[tid]:
            if ch in inv:
                out.append(inv[ch])
        return bytes(out)

    def standalone_utf8(rb):
        try:
            rb.decode("utf-8")
            return True
        except Exception:
            return False

    n_control = 0
    n_fragment = 0
    unexplained = []
    for tid in sorted(bad_set):
        if tid in added_ids:
            n_control += 1
        elif not standalone_utf8(raw_bytes(tid)):
            n_fragment += 1
        else:
            unexplained.append(tid)
    special_like = len(unexplained) == 0
    return {
        "documents": len(docs),
        "roundtrip_cases": rt_total,
        "roundtrip_ok": rt_ok,
        "roundtrip_rate": round(rt_ok / max(1, rt_total), 6),
        "roundtrip_failures": rt_fail,
        "edge_cases": len(EDGE_CASES),
        "edge_ok": edge_ok,
        "edge_failures": edge_fail,
        "vocab_ids_checked": len(ids),
        "vocab_idempotent": len(ids) - bad_total,
        "vocab_non_idempotent_count": bad_total,
        "vocab_non_idempotent_all_special_markers": special_like,
        "vocab_added_tokens_declared": len(added_ids),
        "vocab_non_idempotent_control_tokens": n_control,
        "vocab_non_idempotent_byte_fragments": n_fragment,
        "vocab_non_idempotent_unexplained": unexplained[:8],
        "vocab_non_idempotent_fully_explained": len(unexplained) == 0 and n_control == len(added_ids),
        "vocab_non_idempotent_sample": bad_ids,
    }


def make_windows(docs, ntok=512, budget=24):
    """Non-overlapping 512-token windows, deterministic order."""
    wins = []
    for name, t in docs:
        ids = tok.encode(t)
        for i in range(0, len(ids) - ntok, ntok):
            wins.append((name, ids[i:i + ntok]))
            if len(wins) >= budget:
                return wins
    return wins

tok = port.BPETok(os.path.join(SNAP, "tokenizer.json"))


def reader(**flags):
    """Build the reader; flags select deliberate corruptions for the power check."""
    m = port.Llama(CFG_PATH, WTS_PATH)
    for k, v in flags.items():
        setattr(m, k, v)
    return m


def score_model(model, windows, tag):
    """Held-out bits per token: mean negative log2 probability of the observed next token."""
    nats = 0.0
    ntok = 0
    t0 = time.time()
    with torch.no_grad():
        for name, ids in windows:
            x = torch.tensor(ids)
            lg = model.forward(x).float()
            lp = torch.log_softmax(lg[:-1], dim=-1)
            tgt = x[1:]
            nats += float(-lp[torch.arange(len(tgt)), tgt].sum())
            ntok += len(tgt)
    bits = nats / max(1, ntok) / math.log(2)
    return {"tag": tag, "tokens": ntok, "nats_per_token": round(nats / max(1, ntok), 6),
            "bits_per_token": round(bits, 6), "perplexity": round(2.0 ** bits, 4),
            "seconds": round(time.time() - t0, 1)}


def baselines(train_ids, eval_ids, V=VOCAB_SIZE):
    """Reference points on the same held-out tokens: uniform, unigram, interpolated bigram."""
    import numpy as np
    tr = np.array(train_ids, dtype=np.int64)
    ev = np.array(eval_ids, dtype=np.int64)
    uni = np.bincount(tr, minlength=V).astype(np.float64)
    uni_p = (uni + 1.0) / (uni.sum() + V)
    uni_bits = float(-np.mean(np.log2(uni_p[ev])))
    big = {}
    for a, b in zip(tr[:-1], tr[1:]):
        k = (int(a), int(b))
        big[k] = big.get(k, 0) + 1
    prev_cnt = np.bincount(tr[:-1], minlength=V).astype(np.float64)
    lam = 0.75
    nll = 0.0
    n = 0
    for a, b in zip(ev[:-1], ev[1:]):
        p_ml = big.get((int(a), int(b)), 0) / max(1.0, prev_cnt[int(a)])
        p = lam * p_ml + (1.0 - lam) * uni_p[int(b)]
        nll += -math.log2(max(p, 1e-12))
        n += 1
    return {"uniform_bits_per_token": round(math.log2(V), 4),
            "unigram_add1_bits_per_token": round(uni_bits, 4),
            "bigram_interp_bits_per_token": round(nll / max(1, n), 4),
            "train_tokens": int(tr.size), "eval_tokens": int(ev.size),
            "bigram_types": len(big), "interp_lambda": lam,
            "vocab": V}

FACTS = [("red", "7391"), ("blue", "4820"), ("green", "6157")]
FILLER_TOKENS = 768


def task_sanity(model, eval_docs, n_inst=3):
    """Is the reader usable for the study at all?

    Planted-evidence scoring: mean log probability of the gold code tokens under
    (a) oracle context = evidence adjacent to the question,
    (b) full context = evidence at a controlled mid position inside filler,
    (c) no evidence = the same filler with the evidence sentence removed.
    A usable reader must separate (a) and (c), and must not be at a floor.
    """
    pool = []
    for name, t in eval_docs:
        pool.extend(tok.encode(t))
    rows = []
    for k, (color, code) in enumerate(FACTS[:n_inst]):
        gold_text = "Record: the %s vault requires access code %s at all times." % (color, code)
        q_text = "Question: the access code for the %s vault is" % color
        gold_ids = tok.encode(" " + code)
        start = (k * 977) % max(1, len(pool) - FILLER_TOKENS)
        filler = pool[start:start + FILLER_TOKENS]
        half = len(filler) // 2
        prompts = {
            "oracle": tok.encode(gold_text) + tok.encode(q_text),
            "full_mid": filler[:half] + tok.encode(gold_text) + filler[half:] + tok.encode(q_text),
            "no_evidence": filler + tok.encode(q_text),
        }
        row = {"fact": color, "code": code, "gold_tokens": len(gold_ids)}
        for cond, pids in prompts.items():
            full = pids + gold_ids
            x = torch.tensor(full)
            with torch.no_grad():
                lg = model.forward(x).float()
            lp = torch.log_softmax(lg, dim=-1)
            n = len(full)
            s = 0.0
            for j in range(len(gold_ids)):
                s += float(lp[n - len(gold_ids) + j - 1, gold_ids[j]])
            row[cond + "_prompt_tokens"] = len(pids)
            row[cond + "_mean_logprob"] = round(s / len(gold_ids), 5)
        row["oracle_minus_full"] = round(row["oracle_mean_logprob"] - row["full_mid_mean_logprob"], 5)
        row["oracle_minus_none"] = round(row["oracle_mean_logprob"] - row["no_evidence_mean_logprob"], 5)
        rows.append(row)
        del prompts
    return {"instances": rows,
            "mean_oracle_minus_full": round(sum(r["oracle_minus_full"] for r in rows) / len(rows), 5),
            "mean_oracle_minus_none": round(sum(r["oracle_minus_none"] for r in rows) / len(rows), 5)}


def strip_timings(obj):
    """Remove wall-clock fields before writing an artifact.

    R241 lesson (#93): a same-machine byte-identity check is blind to timing
    fields, so an artifact that contains them can stop reproducing byte-for-byte
    on another machine. Timings are printed to stdout for the operator only.
    """
    if isinstance(obj, dict):
        return {k: strip_timings(v) for k, v in obj.items() if k not in ("seconds", "elapsed_seconds")}
    if isinstance(obj, list):
        return [strip_timings(v) for v in obj]
    return obj


def digest(obj):
    core = {k: v for k, v in obj.items() if k != "seconds"}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()[:16]


def main():
    t0 = time.time()
    torch.set_num_threads(10)
    docs = corpus_docs()
    train_docs = [d for i, d in enumerate(docs) if i % 2 == 0]
    eval_docs = [d for i, d in enumerate(docs) if i % 2 == 1]
    print("corpus documents:", len(docs), "train:", len(train_docs), "eval:", len(eval_docs))
    res = {"corpus": {"documents": len(docs), "train_docs": len(train_docs), "eval_docs": len(eval_docs),
                      "eval_names": [n for n, _ in eval_docs]}}
    res["tokenizer"] = check_tokenizer()
    print("tokenizer:", json.dumps({k: v for k, v in res["tokenizer"].items() if "failures" not in k}))
    model = reader()
    wins = make_windows(eval_docs, 512, 24)
    res["held_out"] = score_model(model, wins, "clean_512_windows")
    print("held_out:", res["held_out"])
    train_ids = []
    for name, t in train_docs:
        train_ids.extend(tok.encode(t)[:40000])
    eval_ids = []
    for name, t in eval_docs:
        eval_ids.extend(tok.encode(t))
    res["baselines"] = baselines(train_ids, eval_ids)
    print("baselines:", json.dumps(res["baselines"]))
    small = wins[:4]
    power = {}
    power["control"] = score_model(model, small, "control")
    for tag, flag, val in [("no_causal_mask", "causal", False),
                           ("rope_disabled", "use_rope", False),
                           ("attn_out_transposed", "transpose_attn_out", True),
                           ("wrong_rope_theta_1e3", "theta", 1000.0)]:
        old = getattr(model, flag)
        setattr(model, flag, val)
        power[tag] = score_model(model, small, tag)
        setattr(model, flag, old)
    base_bits = power["control"]["bits_per_token"]
    for k, v in power.items():
        v["ratio_to_control"] = round(v["bits_per_token"] / base_bits, 3)
    # Two-directional power. Weight/position errors must RAISE bits (ratio well above 1).
    # A leaking causal mask must LOWER bits (ratio below 1), because the target token
    # becomes visible to the model; that arm is a leakage detector, not a degradation arm.
    deg = ["rope_disabled", "attn_out_transposed", "wrong_rope_theta_1e3"]
    power["invariants"] = {
        "degradation_arms": deg,
        "leakage_arms": ["no_causal_mask"],
        "all_degradation_arms_above_1p15x": all(power[a]["ratio_to_control"] > 1.15 for a in deg),
        "leakage_arm_below_1x": power["no_causal_mask"]["ratio_to_control"] < 1.0}
    print("power invariants:", power["invariants"])
    res["power_check"] = power
    print("power_check:", json.dumps({k: {"bits": v.get("bits_per_token"), "x": v.get("ratio_to_control")}
                                      for k, v in power.items()}))
    res["task_sanity"] = task_sanity(model, eval_docs)
    print("task_sanity:", json.dumps({k: v for k, v in res["task_sanity"].items() if k != "instances"}))
    # --- KV-cache equivalence (added R267, when the cache was introduced for generation) ---
    probe = tok.encode("Archive record 7: the current vault code for the red sector is 1234.")
    long_probe = tok.encode(" ".join(["Archive record 7: the current vault code for the red sector is 1234."] * 80))
    full_lp = model.forward(torch.tensor(long_probe))
    cached_lp, cache = model.forward_cached(torch.tensor(long_probe))
    inc_max = 0.0
    _, c0 = model.forward_cached(torch.tensor(probe))
    for extra in [1, 2, 3, 4]:
        a = model.forward(torch.tensor(probe + probe[:extra]))
        b, _ = model.forward_cached(torch.tensor(probe[:extra]), c0)
        inc_max = max(inc_max, float((a[-1] - b[-1]).abs().max()))
    seq = list(probe)
    for _ in range(6):
        lg = model.forward(torch.tensor(seq))[-1]
        seq.append(int(lg.argmax()))
    _, added_cached = model.generate(probe, 6, mode="greedy")
    cache_check = {
        "full_vs_cached_max_abs_diff": round(float((full_lp - cached_lp).abs().max()), 6),
        "incremental_max_abs_diff": round(inc_max, 6),
        "greedy_uncached_equals_cached": seq[len(probe):] == added_cached,
        "probe_tokens": len(long_probe),
    }
    res["kv_cache"] = cache_check
    print("kv_cache:", json.dumps(cache_check))

    d1 = score_model(model, small[:2], "det1")
    d2 = score_model(model, small[:2], "det2")
    k1 = {k: v for k, v in d1.items() if k not in ("tag", "seconds")}
    k2 = {k: v for k, v in d2.items() if k not in ("tag", "seconds")}
    res["determinism"] = {"payload_run1": k1, "payload_run2": k2,
                          "digest_run1": digest(k1), "digest_run2": digest(k2),
                          "identical": digest(k1) == digest(k2)}
    print("determinism:", res["determinism"])
    tk = res["tokenizer"]
    ho = res["held_out"]
    checks = {
        "roundtrip_exact_on_held_out_prose": tk["roundtrip_rate"] == 1.0,
        "edge_cases_exact": tk["edge_ok"] == tk["edge_cases"],
        "non_idempotent_ids_fully_explained": tk["vocab_non_idempotent_fully_explained"] is True,
        "held_out_bits_plausible_band_3_to_8": 3.0 < ho["bits_per_token"] < 8.0,
        "beat_interpolated_bigram_baseline": ho["bits_per_token"] < res["baselines"]["bigram_interp_bits_per_token"],
        "power_degradation_arms_detected": power["invariants"]["all_degradation_arms_above_1p15x"],
        "power_leakage_arm_detected": power["invariants"]["leakage_arm_below_1x"],
        "deterministic_across_repeats": res["determinism"]["identical"],
        "task_sanity_separates_evidence_from_absence": res["task_sanity"]["mean_oracle_minus_none"] > 0.5,
        "kv_cache_full_sequence_exact": res["kv_cache"]["full_vs_cached_max_abs_diff"] == 0.0,
        "kv_cache_incremental_within_tolerance": res["kv_cache"]["incremental_max_abs_diff"] < 1e-3,
        "kv_cache_greedy_matches_uncached": res["kv_cache"]["greedy_uncached_equals_cached"],
    }
    res["verdict"] = {"checks": checks, "pass": all(checks.values())}
    print("VERDICT:", json.dumps(res["verdict"]))
    res["elapsed_seconds"] = round(time.time() - t0, 1)
    res["environment"] = {"python": sys.version.split()[0], "torch": torch.__version__,
                          "threads": torch.get_num_threads(), "model": "HuggingFaceTB/SmolLM2-135M (local cache, BF16)"}
    canonical = strip_timings(res)
    open(os.path.join(HERE, "fidelity_results.json"), "w").write(json.dumps(canonical, indent=1, sort_keys=True) + chr(10))
    print("artifact keys:", len(canonical), "| wall-clock fields stripped:", "seconds" not in json.dumps(canonical))
    print("ELAPSED", res["elapsed_seconds"], "s")
    print("WROTE fidelity_results.json")


if __name__ == "__main__":
    main()
