"""Reproduce the central recovery results of issue #83 (add-carry DESTROY cell).

Self-contained from a fresh clone: trains the c=0.01 SFT base (600 steps),
collapses it with 1500-step KL-anchored GRPO (the #79 DESTROY recipe), then runs
the recovery arms from the SAME collapsed checkpoint:
  continue   : 500 steps self-anchored outcome-only RL
  kl-reanchor: 500 steps KL-anchored GRPO with ref = SFT base, beta 0.01 and 1.0
  sft-replay : 600 steps supervised replay on the base's data recipe (c=0.01)
All evals at held-out seed 777 (carry class): greedy n=384, pass@64 n=48.

Output: prints CELL KEY=value rows; validate.py asserts the two-tier scheme of
manuscript section 8 (Tier A exact-value cells + Tier B mechanism cells).
CPU-only, ~10-core; ~60-90 min total.
"""
import os, sys, random, time
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "ckpts")
os.makedirs(RES, exist_ok=True)
sys.path.insert(0, HERE)

from tasks import CharTok, make_example, parse_answer, truth_answer
from spike_sft import TinyGPT, CFG as SCFG
import spike_rl, addY, parityY  # noqa

tok = CharTok()
cfg = dict(SCFG)
EV = 777


def load(path):
    m = TinyGPT(cfg, tok.vocab)
    m.load_state_dict(torch.load(path, map_location="cpu"))
    m.eval()
    return m


def acc_carry(model, n=384, seed=EV):
    model.eval()
    rng = random.Random(seed)
    ok = 0
    for _ in range(n):
        while True:
            a = rng.randint(10, 99); b = rng.randint(10, 99)
            if a + b >= 100:
                break
        prompt = "add:%d+%d=" % (a, b)
        ids = tok.encode(prompt)
        eq = ids.index(tok.stoi["="])
        x = torch.tensor([ids[:eq + 1]], dtype=torch.long)
        y = model.generate(x, max_new=16)
        txt = tok.decode(y[0].tolist())
        got = parse_answer(txt)
        want = str(a + b)  # parse_answer returns a digit STRING — compare like-for-like
        if got is not None and got == want:
            ok += 1
    return ok / n


def pass64_carry(model, n=48, seed=EV, temp=0.8):
    import torch.nn.functional as F
    model.eval()
    rng = random.Random(seed)
    succ = 0
    for _ in range(n):
        while True:
            a = rng.randint(10, 99); b = rng.randint(10, 99)
            if a + b >= 100:
                break
        prompt = "add:%d+%d=" % (a, b)
        want = str(a + b)  # parse_answer returns a digit STRING — compare like-for-like
        ids = tok.encode(prompt)
        x0 = torch.tensor([ids], dtype=torch.long)
        hit = False
        for _ in range(64):
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


def grpo_step_recovery(model, ref, opt, L, rng, n_group=8, beta=0.01, rng_gen=None):
    """Outcome-only GRPO step with KL anchor to an arbitrary ref (spike_rl logic)."""
    import torch.nn.functional as F
    model.train()
    ids, prompt, answer = make_example(tok, "add", L, rng)
    eq = ids.index(tok.stoi["="])
    prompt_ids = ids[:eq + 1]
    samples = spike_rl.sample_group(model, tok, cfg, prompt_ids, n_group)
    rs = spike_rl.group_rewards(tok, prompt, answer, samples)
    rmean = sum(rs) / len(rs)
    rstd = (sum((r - rmean) ** 2 for r in rs) / len(rs)) ** 0.5 + 1e-8
    advs = [(r - rmean) / rstd for r in rs]
    total = 0.0
    for s, a in zip(samples, advs):
        s_in = s.unsqueeze(0)
        lg, _ = model(s_in[:, :-1])
        lg = lg.log_softmax(-1)
        tok_ids = s_in[:, 1:]
        logp = lg.gather(-1, tok_ids.unsqueeze(-1)).squeeze(-1).sum()
        with torch.no_grad():
            ref_lg, _ = ref(s_in[:, :-1])
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


def run_rl_arms(model_init_path, ref_path, steps, seed=0, n_group=8, beta=0.01, tag="arm"):
    torch.manual_seed(seed); random.seed(seed)
    model = load(model_init_path)
    ref = load(ref_path)
    for p in ref.parameters():
        p.requires_grad_(False)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-5)
    rng = random.Random(seed)
    t0 = time.time()
    for step in range(1, steps + 1):
        rs, loss = grpo_step_recovery(model, ref, opt, 2, rng, n_group=n_group, beta=beta)
        if step % 500 == 0 or step == steps:
            ca = acc_carry(model)
            p64 = pass64_carry(model)
            print("  %s step %d ca=%.3f p64=%.3f t=%.0fs" % (tag, step, ca, p64, time.time() - t0), flush=True)
    return model


def sft_replay(model_path, steps=600, seed=0, p_carry=0.01, tag="sftreplay"):
    torch.manual_seed(seed); random.seed(seed)
    m = load(model_path)
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, weight_decay=0.1)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps)
    rng = random.Random(seed)
    eq_tok = tok.stoi["="]
    t0 = time.time()
    for step in range(1, steps + 1):
        m.train()
        X, Y = [], []
        for _ in range(64):
            mode = "carry" if rng.random() < p_carry else "nocarry"
            ids, _, _ = addY.gen_add(tok, rng, 2, mode)
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
        logits, loss = m(xb, yb)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % 300 == 0 or step == steps:
            ca = acc_carry(m)
            p64 = pass64_carry(m)
            print("  %s step %d loss=%.3f ca=%.3f p64=%.3f t=%.0fs" % (tag, step, loss.item(), ca, p64, time.time() - t0), flush=True)
    return m


def main():
    base_path = os.path.join(RES, "sft_addY_cov010_s0.pt")
    if not os.path.exists(base_path):
        print("[repro] training c=0.01 SFT base (600 steps)...", flush=True)
        m = addY.make_model(cfg, tok, 0)
        addY.sft_mixed(cfg, tok, m, 600, 0, 0.01)
        torch.save(m.state_dict(), base_path)
    mbase = load(base_path)
    b_ca, b_p64 = acc_carry(mbase), pass64_carry(mbase)
    print("CELL base_s0: ca=%.3f p64=%.3f" % (b_ca, b_p64), flush=True)

    coll_path = os.path.join(RES, "rl_collapsed_s0.pt")
    if not os.path.exists(coll_path):
        print("[repro] collapsing with 1500-step GRPO...", flush=True)
        m = run_rl_arms(base_path, base_path, 1500, seed=0, tag="collapse")
        torch.save(m.state_dict(), coll_path)
    mcoll = load(coll_path)
    c_ca, c_p64 = acc_carry(mcoll), pass64_carry(mcoll)
    print("CELL collapsed_s0: ca=%.3f p64=%.3f" % (c_ca, c_p64), flush=True)

    # policy-space arms (500 steps each from the collapsed checkpoint)
    arms = {
        "continue": (coll_path, coll_path, 0.01),
        "klreanchor_b001": (coll_path, base_path, 0.01),
        "klreanchor_b10": (coll_path, base_path, 1.0),
    }
    for tag, (init, refp, beta) in arms.items():
        outp = os.path.join(RES, "rec_%s.pt" % tag)
        if not os.path.exists(outp):
            print("[repro] arm %s (500 steps, beta=%.2f)..." % (tag, beta), flush=True)
            m = run_rl_arms(init, refp, 500, seed=0, beta=beta, tag=tag)
            torch.save(m.state_dict(), outp)
        m = load(outp)
        ca, p64 = acc_carry(m), pass64_carry(m)
        print("CELL %s: ca=%.3f p64=%.3f" % (tag, ca, p64), flush=True)

    # data-replay arm (600 steps)
    replay_path = os.path.join(RES, "rec_sftreplay.pt")
    if not os.path.exists(replay_path):
        print("[repro] arm sftreplay (600 steps)...", flush=True)
        m = sft_replay(coll_path, steps=600, tag="sftreplay")
        torch.save(m.state_dict(), replay_path)
    m = load(replay_path)
    r_ca, r_p64 = acc_carry(m), pass64_carry(m)
    print("CELL sftreplay: ca=%.3f p64=%.3f" % (r_ca, r_p64), flush=True)

    print("REPRODUCE DONE", flush=True)


if __name__ == "__main__":
    main()
