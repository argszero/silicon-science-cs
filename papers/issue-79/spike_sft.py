"""Issue 79 spike part 1: SFT base with controllable competence p0.
Tasks: count (TinyZero-style) and add (carry split). Tiny GPT from scratch.
"""
import math, os, random, sys, time
import torch
import torch.nn as nn
import torch.nn.functional as F
from tasks import CharTok, make_example, parse_answer, truth_answer

CFG = dict(n_layer=4, n_embd=192, n_head=6, block_size=96, dropout=0.0, bias=False,
    lr=1e-3, wd=0.1, batch=64, steps=1200, eval_every=300, seed=0, task="count",
    L_train=8, L_test=[9, 12, 16], n_train_examples=4000, n_eval=384)


class CausalSelfAttention(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        C, H = cfg["n_embd"], cfg["n_head"]
        self.c_attn = nn.Linear(C, 3 * C, bias=cfg["bias"])
        self.c_proj = nn.Linear(C, C, bias=cfg["bias"])
        self.H = H
        self.register_buffer("mask", torch.tril(torch.ones(cfg["block_size"], cfg["block_size"])).view(1, 1, cfg["block_size"], cfg["block_size"]))

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.c_attn(x).split(C, dim=2)
        q = q.view(B, T, self.H, C // self.H).transpose(1, 2)
        k = k.view(B, T, self.H, C // self.H).transpose(1, 2)
        v = v.view(B, T, self.H, C // self.H).transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) / math.sqrt(C // self.H)
        att = att.masked_fill(self.mask[:, :, :T, :T] == 0, float("-inf"))
        att = F.softmax(att, dim=-1)
        y = att @ v
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.c_proj(y)


class Block(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        C = cfg["n_embd"]
        self.ln1 = nn.LayerNorm(C)
        self.attn = CausalSelfAttention(cfg)
        self.ln2 = nn.LayerNorm(C)
        self.mlp = nn.Sequential(nn.Linear(C, 4 * C, bias=cfg["bias"]), nn.GELU(), nn.Linear(4 * C, C, bias=cfg["bias"]))

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class TinyGPT(nn.Module):
    def __init__(self, cfg, vocab_size):
        super().__init__()
        C = cfg["n_embd"]
        self.tok_emb = nn.Embedding(vocab_size, C)
        self.pos_emb = nn.Parameter(torch.zeros(1, cfg["block_size"], C))
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg["n_layer"])])
        self.ln_f = nn.LayerNorm(C)
        self.head = nn.Linear(C, vocab_size, bias=False)
        self.block_size = cfg["block_size"]
        self.apply(self._init)

    def _init(self, m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, std=0.02)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        x = self.tok_emb(idx) + self.pos_emb[:, :T]
        for b in self.blocks:
            x = b(x)
        logits = self.head(self.ln_f(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1), ignore_index=-1)
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new=16, temperature=0.0):
        for _ in range(max_new):
            x = idx if idx.size(1) <= self.block_size else idx[:, -self.block_size:]
            logits, _ = self(x)
            logits = logits[:, -1, :]
            if temperature <= 0:
                nxt = logits.argmax(dim=-1, keepdim=True)
            else:
                probs = F.softmax(logits / temperature, dim=-1)
                nxt = torch.multinomial(probs, 1)
            idx = torch.cat([idx, nxt], dim=1)
        return idx


def batch_xy(cfg, tok, rng, L):
    """Answer-region-only loss: prompt tokens are masked (-1) so the model is
    supervised only on tokens after the '=' (the answer). Avoids mode collapse
    from prompt-token dilution."""
    X, Y = [], []
    eq_tok = tok.stoi["="]
    for _ in range(cfg["batch"]):
        ids, _, _ = make_example(tok, cfg["task"], L, rng)
        ids = ids[:cfg["block_size"]]
        eq = ids.index(eq_tok)
        x = ids[:-1]
        y = ids[1:]
        # target y[j] predicts ids[j+1]; answer tokens start at ids[eq+1]
        for j in range(len(y)):
            if j < eq:
                y[j] = -1
        X.append(x + [tok.pad] * (cfg["block_size"] - 1 - len(x)))
        Y.append(y + [-1] * (cfg["block_size"] - 1 - len(y)))
    return torch.tensor(X, dtype=torch.long), torch.tensor(Y, dtype=torch.long)


@torch.no_grad()
def accuracy(model, tok, cfg, L, n=384, seed=0, temperature=0.0):
    rng = random.Random(seed)
    model.eval()
    correct = 0
    for _ in range(n):
        ids, prompt, answer = make_example(tok, cfg["task"], L, rng)
        eq = ids.index(tok.stoi["="])
        x = torch.tensor([ids[:eq + 1]], dtype=torch.long)
        y = model.generate(x, max_new=16, temperature=temperature)
        txt = tok.decode(y[0].tolist())
        got = parse_answer(txt)
        want = truth_answer(prompt + answer)
        if got is not None and got == want:
            correct += 1
    return correct / n


def train(vol, task, steps, seed, out_dir):
    cfg = dict(CFG)
    cfg["n_train_examples"] = vol
    cfg["task"] = task
    cfg["steps"] = steps
    cfg["seed"] = seed
    torch.manual_seed(seed)
    random.seed(seed)
    tok = CharTok()
    model = TinyGPT(cfg, tok.vocab)
    nparams = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=cfg["steps"])
    rng = random.Random(seed)
    print("[sft] task=%s vol=%d steps=%d params=%.2fM seed=%d" % (task, vol, steps, nparams / 1e6, seed), flush=True)
    t0 = time.time()
    for step in range(1, cfg["steps"] + 1):
        model.train()
        L = random.randint(4, cfg["L_train"]) if task == "count" else cfg["L_train"]
        xb, yb = batch_xy(cfg, tok, rng, L)
        logits, loss = model(xb, yb)
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % cfg["eval_every"] == 0 or step == cfg["steps"]:
            tr = cfg["L_train"]
            acc_tr = accuracy(model, tok, cfg, tr, n=cfg["n_eval"] // 2)
            accs = {}
            for Lt in cfg["L_test"]:
                accs[Lt] = round(accuracy(model, tok, cfg, Lt, n=cfg["n_eval"] // 2), 3)
            print("  step %d loss=%.3f accTr(%d)=%.3f accTest=%s t=%.0fs" % (step, loss.item(), tr, acc_tr, accs, time.time() - t0), flush=True)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "sft_%s_v%d_s%d.pt" % (task, vol, seed))
    torch.save(model.state_dict(), path)
    print("[sft] DONE saved %s wall=%.0fs" % (path, time.time() - t0), flush=True)
    return path
