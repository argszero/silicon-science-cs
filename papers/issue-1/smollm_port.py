"""Dependency-free SmolLM2-135M reader port (torch + numpy only).

Reads the locally cached HF snapshot directly (safetensors parsed by hand,
BPE tokenizer rebuilt from tokenizer.json). Purpose: prove a real transformer
reader is measurable on this machine with zero PyPI installs. This is the
evidence pre-assessment for the issue-1 research direction.
"""
import json, os, math, re
import numpy as np, torch

HF = os.path.expanduser("~/.cache/huggingface/hub")


def snap(repo):
    base = os.path.join(HF, "models--" + repo.replace("/", "--"))
    s = os.path.join(base, "snapshots")
    return os.path.join(s, os.listdir(s)[0])


class ST:
    def __init__(self, path):
        self.path = path
        f = open(path, "rb")
        n = int.from_bytes(f.read(8), "little")
        self.header = json.loads(f.read(n))
        self.base = 8 + n
        self.cache = {}

    def get(self, name, dtype=torch.float32):
        if (name, str(dtype)) in self.cache:
            return self.cache[(name, str(dtype))]
        info = self.header[name]
        a, b = info["data_offsets"]
        dt = {"BF16": np.uint16, "F16": np.float16, "F32": np.float32}[info["dtype"]]
        mm = np.memmap(self.path, dtype=dt, mode="r", offset=self.base + a,
                       shape=(b - a) // np.dtype(dt).itemsize)
        if info["dtype"] == "BF16":
            u = mm.astype(np.uint32) * 65536
            t = u.view(np.float32).reshape(info["shape"]).copy()
        else:
            t = np.array(mm).reshape(info["shape"])
        out = torch.from_numpy(t).to(dtype)
        self.cache[(name, str(dtype))] = out
        return out


def b2u_table():
    bs = (list(range(ord("!"), ord("~") + 1))
          + list(range(ord("\u00a1"), ord("\u00ac") + 1))
          + list(range(ord("\u00ae"), ord("\u00ff") + 1)))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return dict(zip(bs, [chr(c) for c in cs]))


class BPETok:
    def __init__(self, path):
        tj = json.load(open(path))
        self.vocab = tj["model"]["vocab"]
        self.ids = {v: k for k, v in self.vocab.items()}
        self.merges = {}
        for i, m in enumerate(tj["model"]["merges"]):
            a, b = m.split(" ") if isinstance(m, str) else m
            self.merges[(a, b)] = i
        self.b2u = b2u_table()
        self.contr = re.compile(r"'(?:[sdmt]|ll|ve|re)")

    def _pieces(self, text):
        # GPT-2 regex equivalent, hand written (Python re has no \p{L}).
        # Applied per non-digit run after the Digits(individual_digits) split.
        i, n, out = 0, len(text), []
        while i != n:
            c = text[i]
            m = self.contr.match(text, i)
            if m:
                out.append(m.group(0))
                i = m.end()
                continue
            j, pref = i, ""
            if c == " " and i + 1 != n:
                pref, j = " ", i + 1
                c = text[j]
            k = j
            if c.isalpha():
                while k != n and text[k].isalpha():
                    k += 1
            elif not c.isspace():
                while k != n and (not text[k].isspace()) and (not text[k].isalpha()) and (not text[k].isdigit()):
                    k += 1
            else:
                while k != n and text[k].isspace():
                    k += 1
                if k != n:
                    k -= 1          # leave the last space for the next token
                out.append(text[i:k if k != i else i + 1])
                i = k if k != i else i + 1
                continue
            if k == j:
                out.append(text[i])
                i += 1
                continue
            out.append(text[i:k])
            i = k
        return out

    def _bpe(self, token):
        word = list(token)
        while len(word) != 1:
            pairs = set(zip(word, word[1:]))
            best = min(pairs, key=lambda p: self.merges.get(p, 10 ** 9))
            if best not in self.merges:
                break
            i, out = 0, []
            while i != len(word):
                if i != len(word) - 1 and (word[i], word[i + 1]) == best:
                    out.append(word[i] + word[i + 1])
                    i += 2
                else:
                    out.append(word[i])
                    i += 1
            word = out
        return word

    def encode(self, text):
        ids = []
        for run in re.split(r"(\d)", text):
            if run == "":
                continue
            if run.isdigit():
                seq = [run]
            else:
                seq = self._pieces(run)
            for p in seq:
                bs = "".join(self.b2u[b] for b in p.encode("utf-8"))
                for w in self._bpe(bs):
                    ids.append(self.vocab[w])
        return ids

    def decode(self, ids):
        s = "".join(self.ids[i] for i in ids)
        inv = {v: k for k, v in self.b2u.items()}
        bs = bytearray()
        for ch in s:
            if ch in inv:
                bs.append(inv[ch])
        return bs.decode("utf-8", errors="replace")


class Llama:
    def __init__(self, cfg_path, w_path, dtype=torch.float32):
        c = json.load(open(cfg_path))
        self.c = c
        self.st = ST(w_path)
        self.E = self.st.get("model.embed_tokens.weight", dtype)
        self.norm = self.st.get("model.norm.weight", dtype)
        self.h = c["hidden_size"]
        self.nh = c["num_attention_heads"]
        self.nkv = c["num_key_value_heads"]
        self.hd = self.h // self.nh
        self.eps = c["rms_norm_eps"]
        self.theta = c["rope_theta"]
        self.nlayer = c["num_hidden_layers"]
        self.causal = True
        self.use_rope = True
        self.transpose_attn_out = False

    def rms(self, x, w):
        v = x.pow(2).mean(-1, keepdim=True) + self.eps
        return x / v.sqrt() * w

    def rope(self, x, pos):
        if not self.use_rope:
            return x
        half = self.hd // 2
        inv = 1.0 / (self.theta ** (torch.arange(0, half, dtype=torch.float32) / half))
        ang = pos[:, None].float() * inv[None, :]
        cos = ang.cos()[:, None, :].to(x.dtype)
        sin = ang.sin()[:, None, :].to(x.dtype)
        x1, x2 = x[..., :half], x[..., half:]
        return torch.cat([x1 * cos - x2 * sin, x2 * cos + x1 * sin], -1)

    def forward(self, ids):
        T = ids.shape[0]
        x = self.E[ids].float()
        pos = torch.arange(T)
        mask = torch.triu(torch.full((T, T), float("-inf")), 1) if self.causal else torch.zeros(T, T)
        for i in range(self.nlayer):
            p = "model.layers.%d." % i
            hh = self.rms(x, self.st.get(p + "input_layernorm.weight"))
            q = (hh @ self.st.get(p + "self_attn.q_proj.weight").T).view(T, self.nh, self.hd)
            k = (hh @ self.st.get(p + "self_attn.k_proj.weight").T).view(T, self.nkv, self.hd)
            v = (hh @ self.st.get(p + "self_attn.v_proj.weight").T).view(T, self.nkv, self.hd)
            q = self.rope(q, pos)
            k = self.rope(k, pos)
            rep = self.nh // self.nkv
            K = k.repeat_interleave(rep, dim=1).transpose(0, 1)[None]
            V = v.repeat_interleave(rep, dim=1).transpose(0, 1)[None]
            att = (q.transpose(0, 1)[None] @ K.transpose(-1, -2)) / math.sqrt(self.hd) + mask
            att = att.softmax(-1)
            o = (att @ V)[0].transpose(0, 1).reshape(T, self.h)
            wo = self.st.get(p + "self_attn.o_proj.weight")
            if self.transpose_attn_out:
                wo = wo.t().contiguous()
            x = x + o @ wo.T
            hh = self.rms(x, self.st.get(p + "post_attention_layernorm.weight"))
            g = hh @ self.st.get(p + "mlp.gate_proj.weight").T
            u = hh @ self.st.get(p + "mlp.up_proj.weight").T
            x = x + (torch.nn.functional.silu(g) * u) @ self.st.get(p + "mlp.down_proj.weight").T
        x = self.rms(x, self.norm)
        return x @ self.E.float().T

    def forward_cached(self, ids, cache=None):
        """Incremental forward pass.

        ids holds only the NEW tokens; cache is a list of (k, v) tensors per layer
        holding the already-processed prefix, or None on the first call. Returns
        (logits, cache). Equivalence with forward() is verified in eval_fidelity.py.
        """
        T = ids.shape[0]
        off = 0 if cache is None else int(cache[0][0].shape[2])
        x = self.E[ids].float()
        pos = torch.arange(off, off + T)
        mask = torch.full((T, off + T), float("-inf"))
        for i in range(T):
            mask[i, :off + i + 1] = 0.0
        new_cache = []
        for i in range(self.nlayer):
            p = "model.layers.%d." % i
            hh = self.rms(x, self.st.get(p + "input_layernorm.weight"))
            q = (hh @ self.st.get(p + "self_attn.q_proj.weight").T).view(T, self.nh, self.hd)
            k = (hh @ self.st.get(p + "self_attn.k_proj.weight").T).view(T, self.nkv, self.hd)
            v = (hh @ self.st.get(p + "self_attn.v_proj.weight").T).view(T, self.nkv, self.hd)
            q = self.rope(q, pos)
            k = self.rope(k, pos)
            rep = self.nh // self.nkv
            K = k.repeat_interleave(rep, dim=1).transpose(0, 1)[None]
            V = v.repeat_interleave(rep, dim=1).transpose(0, 1)[None]
            if cache is not None:
                K = torch.cat([cache[i][0], K], dim=2)
                V = torch.cat([cache[i][1], V], dim=2)
            new_cache.append((K, V))
            att = (q.transpose(0, 1)[None] @ K.transpose(-1, -2)) / math.sqrt(self.hd) + mask[None, None]
            att = att.softmax(-1)
            o = (att @ V)[0].transpose(0, 1).reshape(T, self.h)
            x = x + o @ self.st.get(p + "self_attn.o_proj.weight").T
            hh = self.rms(x, self.st.get(p + "post_attention_layernorm.weight"))
            g = hh @ self.st.get(p + "mlp.gate_proj.weight").T
            u = hh @ self.st.get(p + "mlp.up_proj.weight").T
            x = x + (torch.nn.functional.silu(g) * u) @ self.st.get(p + "mlp.down_proj.weight").T
        x = self.rms(x, self.norm)
        return x @ self.E.float().T, new_cache

    def generate(self, ids, n_new, mode="greedy", temperature=1.0, gen=None):
        """Generate n_new tokens using the KV cache; returns (full ids, new ids)."""
        out = list(ids)
        logits, cache = self.forward_cached(torch.tensor(out))
        cur = logits[-1]
        added = []
        for _ in range(n_new):
            if mode == "greedy":
                nid = int(cur.argmax())
            else:
                nid = int(torch.multinomial(torch.softmax(cur / temperature, -1), 1, generator=gen))
            added.append(nid)
            out.append(nid)
            logits, cache = self.forward_cached(torch.tensor([nid]), cache)
            cur = logits[0]
        return out, added
