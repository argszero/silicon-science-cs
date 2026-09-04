"""Issue 79 spike part 2: GRPO (RLVR) on top of an SFT base checkpoint.
Outcome reward = exact final-answer correctness. KL anchor to the SFT base.
"""
import math
import os
import random
import time

import torch
import torch.nn.functional as F

from tasks import CharTok, make_example, parse_answer, truth_answer
from spike_sft import TinyGPT, CFG as SCFG, accuracy


@torch.no_grad()
def sample_group(model, tok, cfg, prompt_ids, n, temperature=0.8):
    """Sample n completions; return list of (token_ids_tensor_1d, correct_bool)."""
    x0 = torch.tensor([prompt_ids], dtype=torch.long)
    out = []
    for _ in range(n):
        x = x0
        for _ in range(16):
            logits, _ = model(x[:, -cfg["block_size"]:])
            logits = logits[:, -1, :]
            probs = F.softmax(logits / temperature, dim=-1)
            nxt = torch.multinomial(probs, 1)
            x = torch.cat([x, nxt], dim=1)
        txt = tok.decode(x[0].tolist())
        out.append(x[0])
    return out


def group_rewards(tok, prompt, answer, samples):
    want = truth_answer(prompt + answer)
    rs = []
    for s in samples:
        txt = tok.decode(s.tolist())
        got = parse_answer(txt)
        rs.append(1.0 if (got is not None and got == want) else 0.0)
    return rs


def grpo_step(model, ref, opt, tok, cfg, L, rng, n_group=8, beta=0.01):
    model.train()
    ids, prompt, answer = make_example(tok, cfg["task"], L, rng)
    eq = ids.index(tok.stoi["="])
    prompt_ids = ids[:eq + 1]
    samples = sample_group(model, tok, cfg, prompt_ids, n_group)
    rs = group_rewards(tok, prompt, answer, samples)
    rmean = sum(rs) / len(rs)
    rstd = (sum((r - rmean) ** 2 for r in rs) / len(rs)) ** 0.5 + 1e-8
    advs = [(r - rmean) / rstd for r in rs]
    total = 0.0
    # policy loss with group-normalized advantage; build as one graph
    logits = None
    # loop samples for clarity at spike scale
    for s, a in zip(samples, advs):
        s_in = s.unsqueeze(0)
        lg, _ = model(s_in[:, :-1])
        lg = lg.log_softmax(-1)
        tok_ids = s_in[:, 1:]
        logp = lg.gather(-1, tok_ids.unsqueeze(-1)).squeeze(-1).sum()
        with torch.no_grad():
            ref_in = s_in[:, :-1]
            ref_lg, _ = ref(ref_in)
            ref_lg = ref_lg.log_softmax(-1)
            ref_logp = ref_lg.gather(-1, tok_ids.unsqueeze(-1)).squeeze(-1).sum()
        ntok = s_in.size(1) - 1
        w = (logp - ref_logp).detach() / ntok
        total = total + (-a * (logp / ntok) + beta * w * (logp / ntok))
    loss = total / n_group
    opt.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    return rs, loss.item()


def run_rl(ckpt_path, task, L_eval, steps=400, seed=0, n_group=8):
    torch.manual_seed(seed)
    random.seed(seed)
    cfg = dict(SCFG)
    cfg["task"] = task
    tok = CharTok()
    model = TinyGPT(cfg, tok.vocab)
    sd = torch.load(ckpt_path, map_location="cpu")
    model.load_state_dict(sd)
    ref = TinyGPT(cfg, tok.vocab)
    ref.load_state_dict(sd)
    ref.eval()
    for p in ref.parameters():
        p.requires_grad_(False)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-5)
    rng = random.Random(seed)
    print("[rl] start ckpt=%s task=%s L_eval=%d steps=%d" % (os.path.basename(ckpt_path), task, L_eval, steps), flush=True)
    acc_before = accuracy(model, tok, cfg, L_eval, n=128)
    t0 = time.time()
    for step in range(1, steps + 1):
        L = L_eval
        rs, loss = grpo_step(model, ref, opt, tok, cfg, L, rng, n_group=n_group)
        if step % 50 == 0 or step == steps:
            acc = accuracy(model, tok, cfg, L_eval, n=128)
            print("  step %d loss=%.3f rew_mean=%.3f acc(%d)=%.3f t=%.0fs" % (step, loss, sum(rs) / len(rs), L_eval, acc, time.time() - t0), flush=True)
    print("[rl] acc before=%.3f after=%.3f" % (acc_before, accuracy(model, tok, cfg, L_eval, n=128)), flush=True)
    return model, tok
