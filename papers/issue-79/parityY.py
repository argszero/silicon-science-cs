"""Issue 79 third axis: parity family (par of a+b, answer in {0,1}).

Contrast cell: at thin coverage of the failing class, add DESTROYED (wide
99-value answer space) while count CREATEs (small answer space, large
equivalence classes). Parity has a 2-VALUE answer space and the largest
possible equivalence classes (all mixed-parity pairs share the answer rule),
so RL should be robustly load-bearing even at coverage where add failed.

Prompt format reuses the digit parser: "par:23+46=" -> "answer:1_" (1 = odd,
0 = even). make_par added to tasks.make_example under task name "par" so
spike_sft.accuracy / spike_rl.grpo_step work unchanged (L doubles as ndig).
"""
import os
import random
import time
import torch
from tasks import CharTok, parse_answer, truth_answer
from spike_sft import TinyGPT, CFG as SCFG


def par_pair(rng, ndig):
    lo = pow(10, ndig - 1)
    hi = pow(10, ndig) - 1
    a = rng.randint(lo, hi)
    b = rng.randint(lo, hi)
    return a, b


def gen_par(tok, rng, ndig, mode):
    while True:
        a, b = par_pair(rng, ndig)
        p = (a + b) % 2
        if mode == "any":
            break
        if mode == "even" and p == 0:
            break
        if mode == "odd" and p == 1:
            break
    prompt = "par:%d+%d=" % (a, b)
    answer = "answer:%d_" % p
    return tok.encode(prompt + answer), prompt, answer


def acc_par(model, tok, cfg, ndig, mode, n=384, seed=0):
    model.eval()
    rng = random.Random(seed)
    ok = 0
    for _ in range(n):
        ids, prompt, answer = gen_par(tok, rng, ndig, mode)
        eq = ids.index(tok.stoi["="])
        x = torch.tensor([ids[:eq + 1]], dtype=torch.long)
        y = model.generate(x, max_new=16)
        txt = tok.decode(y[0].tolist())
        got = parse_answer(txt)
        want = truth_answer(prompt + answer)
        if got is not None and got == want:
            ok += 1
    return ok / n


def make_model(cfg, tok, seed):
    torch.manual_seed(seed)
    random.seed(seed)
    return TinyGPT(cfg, tok.vocab)


def load_model(cfg, tok, path):
    m = TinyGPT(cfg, tok.vocab)
    m.load_state_dict(torch.load(path, map_location="cpu"))
    m.eval()
    return m


def sft_par(cfg, tok, model, steps, seed, p_odd):
    """SFT with fraction p_odd of odd-sum (answer 1) examples; rest even."""
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps)
    rng = random.Random(seed)
    eq_tok = tok.stoi["="]
    t0 = time.time()
    for step in range(1, steps + 1):
        model.train()
        X, Y = [], []
        for _ in range(cfg["batch"]):
            mode = "odd" if rng.random() < p_odd else "even"
            ids, _, _ = gen_par(tok, rng, 2, mode)
            ids = ids[:cfg["block_size"]]
            eq = ids.index(eq_tok)
            x = ids[:-1]
            y = ids[1:]
            for j in range(len(y)):
                if j < eq:
                    y[j] = -1
            X.append(x + [tok.pad] * (cfg["block_size"] - 1 - len(x)))
            Y.append(y + [-1] * (cfg["block_size"] - 1 - len(y)))
        xb = torch.tensor(X, dtype=torch.long)
        yb = torch.tensor(Y, dtype=torch.long)
        logits, loss = model(xb, yb)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % 300 == 0 or step == steps:
            ev = acc_par(model, tok, cfg, 2, "even", n=128)
            od = acc_par(model, tok, cfg, 2, "odd", n=128)
            print("  sft_par step %d loss=%.3f acc_even=%.3f acc_odd=%.3f t=%.0fs" % (
                step, loss.item(), ev, od, time.time() - t0), flush=True)
    return model
