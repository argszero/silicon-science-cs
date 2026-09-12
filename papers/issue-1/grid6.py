"""Full corrected grid v6 for issue #1: cued reader, non-tell query, full sweep.

Changes from grid3:
  * corpus4 removes the lexical tell (no gold-unique word appears in the question),
    so the lexical arm faces the same semantic challenge as the dense arm;
  * each condition now also runs SAMPLED decoding with several seeds, sharing one
    prompt cache, which gives the multi-run statistics the journal requires;
  * the perceived-position control is kept, and the tell audit is recorded per cell.

Writes grid6_results.json.
"""
import json, math, os, sys, time
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import corpus5 as corpus4
import mini_port
import smollm_port as reader_port

RD = reader_port.snap("HuggingFaceTB/SmolLM2-135M")
RT = reader_port.BPETok(os.path.join(RD, "tokenizer.json"))
KS = [1, 2, 4, 8]
SEEDS = [101, 202, 303, 404]
TEMP = 0.7


def evaluate_prompt(model, pids, aids, seeds=SEEDS, temp=TEMP):
    """One prompt forward for log-probabilities, then greedy and sampled continuations."""
    logits, cache = model.forward_cached(torch.tensor(pids))
    cur = logits[-1]
    lp0 = torch.log_softmax(cur, dim=-1)
    total = float(lp0[aids[0]])
    first_rank = int((lp0 > lp0[aids[0]]).sum())
    # remaining answer tokens' gold log-probabilities, incremental
    ac = cache
    for j in range(1, len(aids)):
        lg, ac = model.forward_cached(torch.tensor([aids[j - 1]]), ac)
        total += float(torch.log_softmax(lg[0], dim=-1)[aids[j]])
    # greedy continuation (shares the prompt cache)
    gen, gc, gcur = [], cache, cur
    for j in range(len(aids)):
        nid = int(gcur.argmax())
        gen.append(nid)
        if j != len(aids) - 1:
            lg, gc = model.forward_cached(torch.tensor([nid]), gc)
            gcur = lg[0]
    # sampled continuations, one per seed
    sampled = []
    for sd in seeds:
        g = torch.Generator().manual_seed(sd)
        sg, sc, scur = [], cache, cur
        for j in range(len(aids)):
            nid = int(torch.multinomial(torch.softmax(scur / temp, -1), 1, generator=g))
            sg.append(nid)
            if j != len(aids) - 1:
                lg, sc = model.forward_cached(torch.tensor([nid]), sc)
                scur = lg[0]
        sampled.append({"seed": sd, "exact": sg == aids, "first_ok": sg[0] == aids[0],
                        "text": RT.decode(sg)})
    return {"prompt_tokens": len(pids), "answer_tokens": len(aids),
            "mean_logprob": round(total / len(aids), 5),
            "first_token_gold_rank": first_rank,
            "greedy_exact": gen == aids,
            "greedy_text": RT.decode(gen),
            "sampled": sampled,
            "sampled_exact_rate": round(sum(1 for s in sampled if s["exact"]) / len(sampled), 4),
            "sampled_first_ok_rate": round(sum(1 for s in sampled if s["first_ok"]) / len(sampled), 4)}


def bm25_rank(query, docs, k1=1.2, b=0.75):
    toks = [[w.lower() for w in d.replace(".", " ").replace(":", " ").split()] for d in docs]
    qt = [w.lower() for w in query.replace(":", " ").replace("?", " ").split()]
    N = len(docs)
    avg = sum(len(t) for t in toks) / max(1, N)
    df = {}
    for t in toks:
        for w in set(t):
            df[w] = df.get(w, 0) + 1
    scores = []
    for i, t in enumerate(toks):
        s = 0.0
        tf = {}
        for w in t:
            tf[w] = tf.get(w, 0) + 1
        for w in qt:
            if w in tf:
                idf = math.log(1 + (N - df.get(w, 0) + 0.5) / (df.get(w, 0) + 0.5))
                s += idf * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * len(t) / max(1.0, avg)))
        scores.append(s)
    return sorted(range(N), key=lambda i: (-scores[i], i))


def run_cell(model, tok_m, enc_m, arm, inst_id, n_chunks, interference, kind, filler, gold_frac=0.5):
    ins = corpus4.make_instance(inst_id, n_chunks, interference, kind=kind, filler=filler,
                                gold_frac=gold_frac)
    docs = [ln["text"] for ln in ins["lines"]]
    gold_pos = ins["gold_pos"]
    aids = RT.encode(" " + ins["gold_code"])
    qe = enc_m.encode(tok_m, [ins.get("retriever_query", ins["question"])])
    de = enc_m.encode(tok_m, docs)
    sims = (de @ qe).tolist()
    dense = sorted(range(len(docs)), key=lambda i: (-sims[i], i))
    bm = bm25_rank(ins.get("retriever_query", ins["question"]), docs)
    out = {"arm": arm, "inst_id": inst_id, "n_chunks": n_chunks, "interference": interference,
           "kind": kind, "filler": filler, "gold_pos": gold_pos, "gold_frac": gold_frac,
           "dense_rank_gold": dense.index(gold_pos), "bm25_rank_gold": bm.index(gold_pos),
           "dense_recall": {str(k): int(dense.index(gold_pos) < k) for k in KS},
           "bm25_recall": {str(k): int(bm.index(gold_pos) < k) for k in KS},
           "tell_audit": corpus4.tell_audit(ins), "tell_applicable": ins["n_distract"] + 0 != 0,
           "n_family": sum(1 for ln in ins["lines"] if ln["kind"] in ("gold", "distract"))}
    conds = {"oracle": corpus4.oracle_indices(ins), "full": corpus4.all_indices(ins),
             "no_evidence": corpus4.no_evidence_indices(ins)}
    for k in KS:
        conds["dense_k%d" % k] = sorted(dense[:k])
    conds["bm25_k4"] = sorted(bm[:4])
    for name, idxs in conds.items():
        r = evaluate_prompt(model, RT.encode(corpus4.context_text(ins, idxs)), aids)
        r["n_context_chunks"] = len(idxs)
        r["gold_in_context"] = gold_pos in idxs
        out[name] = r
    return out


def build_plan():
    """The full corrected sweep plan: main grid, type control, length control, position ladder."""
    plan = []
    # main sweep: three context budgets x the interference ladder x two instances
    for n_chunks in [64, 128, 256]:
        for inter in [0.0, 0.15, 0.3, 0.45, 0.6, 0.8]:
            for inst in [0, 1]:
                plan.append(("MAIN", inst, n_chunks, inter, "status", "related", 0.5))
    # separator control: different-entity distractors at matched density and length
    for inst in [0, 1]:
        plan.append(("TYPE_entity", inst, 256, 0.6, "entity", "related", 0.5))
    # recall-matched type control: both distractor families at densities where the dense
    # retriever still returns the gold record, so the type contrast is measured at fixed
    # retrieval success rather than at "retrieved" versus "missed" (revision round 1, RC3).
    for (nc, it) in [(64, 0.15), (64, 0.30), (128, 0.15)]:
        for kind in ("status", "entity"):
            for inst in [0, 1, 2, 3, 4, 5]:
                plan.append(("TYPERM_" + kind, inst, nc, it, kind, "related", 0.5))
    # pure-length control: same length, no competition for the answer
    for inst in [0, 1]:
        plan.append(("FILLER_neutral", inst, 256, 0.0, "status", "neutral", 0.5))
    # evidence position ladder at fixed length and interference
    for gf in [0.0, 0.25, 0.75, 1.0]:
        for inst in [0, 1]:
            plan.append(("POSITION", inst, 256, 0.6, "status", "related", gf))
    return plan


def main():
    t_start = time.time()
    torch.set_num_threads(10)
    model = reader_port.Llama(os.path.join(RD, "config.json"), os.path.join(RD, "model.safetensors"))
    tok_m, enc_m = mini_port.load_minilm()
    cells = []
    plan = build_plan()
    for arm, inst, n_chunks, inter, kind, filler, gf in plan:
        c = run_cell(model, tok_m, enc_m, arm, inst, n_chunks, inter, kind, filler, gf)
        cells.append(c)
        print("%-12s L=%3d I=%.2f gf=%.1f i%d | full %+.3f dk4 %+.3f bm4 %+.3f none %+.3f | "
              "exact g%d s%.2f | rank d%3d b%3d | rec@1 d%d b%d | tell %s" % (
                  arm, n_chunks, inter, gf, inst, c["full"]["mean_logprob"],
                  c["dense_k4"]["mean_logprob"], c["bm25_k4"]["mean_logprob"],
                  c["no_evidence"]["mean_logprob"], int(c["full"]["greedy_exact"]),
                  c["full"]["sampled_exact_rate"], c["dense_rank_gold"], c["bm25_rank_gold"],
                  c["dense_recall"]["1"], c["bm25_recall"]["1"],
                  "clean" if c["tell_audit"]["clean"] else "TELL"))
        sys.stdout.flush()
    res = {"cells": cells, "plan_size": len(plan), "k": KS, "seeds": SEEDS, "temperature": TEMP,
           "environment": {"reader": "SmolLM2-135M port (KV-cached)", "retriever": "MiniLM-L6-v2 port + BM25"}}
    open(os.path.join(HERE, "grid6_results.json"), "w").write(json.dumps(res, indent=1, sort_keys=True))
    print("GRID6 DONE in %.0f s | cells %d" % (time.time() - t_start, len(cells)))


if __name__ == "__main__":
    main()
