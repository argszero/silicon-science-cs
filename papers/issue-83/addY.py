"""Issue 79 decisive (Y) experiment: add family, systematic-error base.
Base SFT on no-carry 2-digit pairs only (partial rule).
Failing class: carry 2-digit prompts at the same length.
"""
import os
import random
import time
import torch
import torch.nn.functional as F
from tasks import CharTok, parse_answer, truth_answer
from spike_sft import TinyGPT, CFG as SCFG


def add_pair(rng, ndig):
    lo = pow(10, ndig - 1)
    hi = pow(10, ndig) - 1
    a = rng.randint(lo, hi)
    b = rng.randint(lo, hi)
    return a, b


def has_carry(a, b):
    sa = str(a)
    sb = str(b)
    n = max(len(sa), len(sb))
    carry = 0
    for i in range(n):
        da = int(sa[n - 1 - i]) if i < len(sa) else 0
        db = int(sb[n - 1 - i]) if i < len(sb) else 0
        total = da + db + carry
        carry = total // 10
    return carry == 1


def gen_add(tok, rng, ndig, mode):
    while True:
        a, b = add_pair(rng, ndig)
        c = has_carry(a, b)
        if mode == "any":
            break
        if mode == "nocarry" and not c:
            break
        if mode == "carry" and c:
            break
    prompt = "add:%d+%d=" % (a, b)
    answer = "answer:%d_" % (a + b)
    return tok.encode(prompt + answer), prompt, answer


def acc_mode(model, tok, cfg, ndig, mode, n=256, seed=0):
    model.eval()
    rng = random.Random(seed)
    ok = 0
    seen = 0
    while seen < n:
        ids, prompt, answer = gen_add(tok, rng, ndig, mode)
        eq = ids.index(tok.stoi["="])
        x = torch.tensor([ids[:eq + 1]], dtype=torch.long)
        y = model.generate(x, max_new=16)
        txt = tok.decode(y[0].tolist())
        got = parse_answer(txt)
        want = truth_answer(prompt + answer)
        if got is not None and got == want:
            ok = ok + 1
        seen = seen + 1
    return ok / n


def passk_mode(model, tok, cfg, ndig, mode, k, n=48, seed=0, temp=0.8):
    model.eval()
    rng = random.Random(seed)
    succ = 0
    trials = 0
    while trials < n:
        ids, prompt, answer = gen_add(tok, rng, ndig, mode)
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
            succ = succ + 1
        trials = trials + 1
    return succ / n


def sft_nocarry(cfg, tok, model, steps, seed):
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps)
    rng = random.Random(seed)
    eq_tok = tok.stoi["="]
    t0 = time.time()
    for step in range(1, steps + 1):
        model.train()
        X, Y = [], []
        for _ in range(cfg["batch"]):
            ids, _, _ = gen_add(tok, rng, 2, "nocarry")
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
            nc = acc_mode(model, tok, cfg, 2, "nocarry", n=128)
            ca = acc_mode(model, tok, cfg, 2, "carry", n=128)
            print("  step %d loss=%.3f acc_nocarry=%.3f acc_carry=%.3f t=%.0fs" % (step, loss.item(), nc, ca, time.time() - t0), flush=True)
    return model


def make_model(cfg, tok, seed):
    torch.manual_seed(seed)
    random.seed(seed)
    return TinyGPT(cfg, tok.vocab)


def load_model(cfg, tok, path):
    m = TinyGPT(cfg, tok.vocab)
    m.load_state_dict(torch.load(path, map_location="cpu"))
    m.eval()
    return m


def sft_mixed(cfg, tok, model, steps, seed, p_carry):
    """SFT with a fraction p_carry of carry examples (sparse coverage)."""
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps)
    rng = random.Random(seed)
    eq_tok = tok.stoi["="]
    t0 = time.time()
    for step in range(1, steps + 1):
        model.train()
        X, Y = [], []
        for _ in range(cfg["batch"]):
            mode = "carry" if rng.random() < p_carry else "nocarry"
            ids, _, _ = gen_add(tok, rng, 2, mode)
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
            nc = acc_mode(model, tok, cfg, 2, "nocarry", n=128)
            ca = acc_mode(model, tok, cfg, 2, "carry", n=128)
            print("  sft_mixed step %d loss=%.3f acc_nc=%.3f acc_ca=%.3f t=%.0fs" % (step, loss.item(), nc, ca, time.time() - t0), flush=True)
    return model
