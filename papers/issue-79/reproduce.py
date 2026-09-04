"""Reproduce the six central cells of issue #79 (WALL/RACE/CREATE/DESTROY/GREEDY-BLIND/NO-GAP).

Re-trains RL from the persisted SFT bases (or re-runs SFT if a base is missing)
and evaluates at the fixed held-out eval seed 777, mirroring the manuscript's
regime-table numbers. CPU-only, ~10-core; ~40-60 min total.

Output: prints KEY=value rows; `validate.py` asserts the manuscript numbers
against these with tolerance.

Cells (each = SFT base ckpt -> KL-anchored GRPO -> held-out-777 eval):
  WALL        add c=0.00 (nc2 base)        -> carry greedy 0.000, pass@64 0.000
  RACE        count L20 seeds 0..2         -> rl_greedy ~ {0.17,0.08,0.00}
  CREATE      count L12 seeds 0..2         -> rl_greedy ~ {0.38,0.51,0.57}
  DESTROY     add c=0.01 seed 0            -> rl_carry < base_carry (0.083 vs 0.156)
  GREEDY-BLIND parity c=0.10 seed 0        -> rl odd greedy 0.000, pass@64 1.0
"""
import os
import sys
import torch
import random
import addY
import parityY
import spike_rl
from tasks import CharTok, parse_answer, truth_answer, make_example
from spike_sft import CFG as SCFG, TinyGPT

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpts")
cfg = dict(SCFG)
tok = CharTok()
EV = 777

# ---------------- cell runners (mirror the originals) ----------------


def acc_model(model, gen_fn, mode, n=384, seed=EV):
    model.eval()
    rng = random.Random(seed)
    ok = 0
    for _ in range(n):
        ids, prompt, answer = gen_fn(rng, mode)
        eq = ids.index(tok.stoi["="])
        x = torch.tensor([ids[:eq + 1]], dtype=torch.long)
        y = model.generate(x, max_new=16)
        txt = tok.decode(y[0].tolist())
        got = parse_answer(txt)
        want = truth_answer(prompt + answer)
        if got is not None and got == want:
            ok += 1
    return ok / n


def passk_model(model, gen_fn, mode, k, n=48, seed=EV, temp=0.8):
    import torch.nn.functional as F
    model.eval()
    rng = random.Random(seed)
    succ = 0
    for _ in range(n):
        ids, prompt, answer = gen_fn(rng, mode)
        eq = ids.index(tok.stoi["="])
        want = truth_answer(prompt + answer)
        x0 = torch.tensor([ids[:eq + 1]], dtype=torch.long)
        hit = False
        for _ in range(k):
            x = x0
            for _ in range(16):
                logits, _ = model(x[:, -cfg["block_size"]:])
                logits = logits[:, -1, :]
                probs = F.softmax(logits / temp, dim=-1)
                nxt = torch.multinomial(probs, 1)
                x = torch.cat([x, nxt], dim=1)
            txt = tok.decode(x[0].tolist())
            got = parse_answer(txt)
            if got is not None and got == want:
                hit = True
                break
        if hit:
            succ += 1
    return succ / n


def gen_count(rng, L, mode="any"):
    ids, prompt, answer = make_example(tok, "count", L, rng)
    return ids, prompt, answer


def gen_add(rng, mode):
    while True:
        a = rng.randint(10, 99)
        b = rng.randint(10, 99)
        c_ = addY.has_carry(a, b)
        if mode == "any":
            break
        if mode == "nocarry" and not c_:
            break
        if mode == "carry" and c_:
            break
    prompt = "add:%d+%d=" % (a, b)
    answer = "answer:%d_" % (a + b)
    return tok.encode(prompt + answer), prompt, answer


def gen_par(rng, mode):
    return parityY.gen_par(tok, rng, 2, mode)


def ensure_sft(kind, *args):
    """Return path to the SFT base for a cell, training it from scratch if absent
    (so `bash reproduce.sh` works from a fresh clone with no checkpoints)."""
    if kind == "count":
        seed = args[0]
        path = os.path.join(RES, "sft_count_v4000_s%d.pt" % seed)
        if not os.path.exists(path):
            import spike_sft
            print("  [repro] training count base seed %d (vol 4000, 600 steps)..." % seed, flush=True)
            spike_sft.train(4000, "count", 600, seed, RES)
    elif kind == "add":
        c, seed, lab = args
        path = os.path.join(RES, "sft_addY_cov%s_s%d.pt" % (lab, seed) if c > 0.0 else "sft_addY_nc2_s%d.pt" % seed)
        if not os.path.exists(path):
            m = addY.make_model(cfg, tok, seed)
            print("  [repro] training add base cov=%s seed %d (600 steps)..." % (lab, seed), flush=True)
            addY.sft_mixed(cfg, tok, m, 600, seed, c)
            torch.save(m.state_dict(), path)
    elif kind == "par":
        c, seed, lab = args
        path = os.path.join(RES, "sft_par_cov%s_s%d.pt" % (lab, seed))
        if not os.path.exists(path):
            m = parityY.make_model(cfg, tok, seed)
            print("  [repro] training parity base cov=%s seed %d (600 steps)..." % (lab, seed), flush=True)
            parityY.sft_par(cfg, tok, m, 600, seed, c)
            torch.save(m.state_dict(), path)
    assert os.path.exists(path), path
    return path



def run_count(L, seed, steps=400):
    ckpt = ensure_sft("count", seed)
    m0 = TinyGPT(cfg, tok.vocab)
    m0.load_state_dict(torch.load(ckpt, map_location="cpu")); m0.eval()
    b_g = acc_model(m0, lambda rng, m: gen_count(rng, L, m), "any")
    b_p64 = passk_model(m0, lambda rng, m: gen_count(rng, L, m), "any", 64)
    rl, _ = spike_rl.run_rl(ckpt, "count", L, steps=steps, seed=seed, n_group=8)
    rl_ckpt = os.path.join(RES, "rl_count_L%d_s%d.pt" % (L, seed))
    torch.save(rl.state_dict(), rl_ckpt)
    r_g = acc_model(rl, lambda rng, m: gen_count(rng, L, m), "any")
    r_p64 = passk_model(rl, lambda rng, m: gen_count(rng, L, m), "any", 64)
    print("CELL count L%d s%d: base_g=%.3f base_p64=%.3f rl_g=%.3f rl_p64=%.3f" % (L, seed, b_g, b_p64, r_g, r_p64), flush=True)


def run_add_cov(c, seed, lab):
    ckpt = ensure_sft("add", c, seed, lab)
    m0 = addY.load_model(cfg, tok, ckpt)
    b_ca = acc_model(m0, lambda rng, m: gen_add(rng, m), "carry")
    b_p64 = passk_model(m0, lambda rng, m: gen_add(rng, m), "carry", 64)
    rl, _ = spike_rl.run_rl(ckpt, "add", 2, steps=500, seed=seed, n_group=8)
    rl_ckpt = os.path.join(RES, "rl_addY_cov%s_s%d.pt" % (lab, seed))
    torch.save(rl.state_dict(), rl_ckpt)
    r_ca = acc_model(rl, lambda rng, m: gen_add(rng, m), "carry")
    r_p64 = passk_model(rl, lambda rng, m: gen_add(rng, m), "carry", 64)
    print("CELL add cov%s s%d: base_ca=%.3f base_p64=%.3f rl_ca=%.3f rl_p64=%.3f" % (lab, seed, b_ca, b_p64, r_ca, r_p64), flush=True)


def run_par(c, seed, lab):
    ckpt = ensure_sft("par", c, seed, lab)
    m0 = parityY.load_model(cfg, tok, ckpt)
    b_od = parityY.acc_par(m0, tok, cfg, 2, "odd", n=384, seed=EV)
    b_p64 = passk_model(m0, lambda rng, m: gen_par(rng, m), "odd", 64)
    rl, _ = spike_rl.run_rl(ckpt, "par", 2, steps=500, seed=seed, n_group=8)
    rl_ckpt = os.path.join(RES, "rl_par_cov%s_s%d.pt" % (lab, seed))
    torch.save(rl.state_dict(), rl_ckpt)
    r_od = parityY.acc_par(rl, tok, cfg, 2, "odd", n=384, seed=EV)
    r_p64 = passk_model(rl, lambda rng, m: gen_par(rng, m), "odd", 64)
    print("CELL par cov%s s%d: base_odd=%.3f base_p64=%.3f rl_odd=%.3f rl_p64=%.3f" % (lab, seed, b_od, b_p64, r_od, r_p64), flush=True)


def main():
    # WALL (add c=0)
    print("CELL add c=0.00 s0 (WALL) - expect rl_ca=0.000 rl_p64=0.000", flush=True)
    run_add_cov(0.0, 0, "000")
    # RACE (count L20 seeds 0..2)
    for s in (0, 1, 2):
        run_count(20, s, steps=500)
    # CREATE (count L12 seeds 0..2)
    for s in (0, 1, 2):
        run_count(12, s, steps=400)
    # DESTROY (add c=0.01 seed 0)
    run_add_cov(0.01, 0, "010")
    # GREEDY-BLIND (parity c=0.10 seed 0)
    run_par(0.10, 0, "100")
    print("REPRODUCE DONE", flush=True)


if __name__ == "__main__":
    main()
