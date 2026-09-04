"""Shared pass@k harness for matched-budget base vs RL comparison.
Samples kmax rollouts per prompt once; nested pass@k for each k in the list.
"""
import random
import torch
import torch.nn.functional as F
from tasks import parse_answer, truth_answer


@torch.no_grad()
def passk(model, tok, prompt_ids, want, kmax, temp, block_size):
    """Boolean success at each k from 1 to kmax (nested)."""
    x0 = torch.tensor([prompt_ids], dtype=torch.long)
    got_any = False
    hits = []
    for k in range(1, kmax + 1):
        if not got_any:
            x = x0
            for _ in range(16):
                logits, _ = model(x[:, -block_size:])
                logits = logits[:, -1, :]
                probs = F.softmax(logits / temp, dim=-1)
                nxt = torch.multinomial(probs, 1)
                x = torch.cat([x, nxt], dim=1)
            txt = tok.decode(x[0].tolist())
            got = parse_answer(txt)
            if got is not None and got == want:
                got_any = True
        hits.append(got_any)
    return hits


def passk_curve(model, tok, gen, ndig, mode, k_list, n=48, temp=0.8, seed=0, block_size=96):
    rng = random.Random(seed)
    kmax = max(k_list)
    counts = dict((k, 0) for k in k_list)
    total = 0
    while total < n:
        ids, prompt, answer = gen(tok, rng, ndig, mode)
        eq = ids.index(tok.stoi["="])
        want = truth_answer(prompt + answer)
        hits = passk(model, tok, ids[:eq + 1], want, kmax, temp, block_size)
        for k in k_list:
            if hits[k - 1]:
                counts[k] = counts[k] + 1
        total = total + 1
    return dict((k, counts[k] / n) for k in k_list)
