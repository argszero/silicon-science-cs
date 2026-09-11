"""Dependency-free all-MiniLM-L6-v2 dense retriever port (torch + numpy only).

Same discipline as the reader port: the local HF snapshot is read directly
(safetensors parsed by hand, WordPiece vocabulary rebuilt from the tokenizer
files). Mean pooling then L2 normalisation, which is the published pooling
configuration for this sentence-transformers model. Validated in
eval_retriever.py before any study number is reported.
"""
import json, math, os, re, struct, unicodedata
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


def load_vocab(path):
    vocab = {}
    for i, line in enumerate(open(path, encoding="utf-8")):
        vocab[line.rstrip("\n")] = i
    return vocab


PUNCT = set(list("!\"#$%&'()*+,-./:;=?@[\\]^_`{|}~"))


class WordPiece:
    """BERT normalisation plus pre-tokenisation plus greedy longest-match WordPiece."""

    def __init__(self, vocab_path, lowercase=True, strip_accents=None):
        self.vocab = load_vocab(vocab_path)
        self.ids = {v: k for k, v in self.vocab.items()}
        self.lower = lowercase
        self.strip_accents = lowercase if strip_accents is None else strip_accents
        self.cls = self.vocab["[CLS]"]
        self.sep = self.vocab["[SEP]"]
        self.unk = self.vocab["[UNK]"]
        self.max_len = 512

    def normalize(self, text):
        out = []
        for ch in text:
            cp = ord(ch)
            if cp == 0 or cp == 0xFFFD or unicodedata.category(ch) in ("Cc", "Cf"):
                continue
            if ch.isspace():
                out.append(" ")
            else:
                out.append(ch)
        text = "".join(out)
        if self.lower:
            text = text.lower()
        if self.strip_accents:
            text = "".join(c for c in unicodedata.normalize("NFD", text)
                           if unicodedata.category(c) != "Mn")
        # handle_chinese_chars: pad CJK ranges with spaces
        out = []
        for ch in text:
            cp = ord(ch)
            if (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
                    0x20000 <= cp <= 0x2A6DF or 0x2A700 <= cp <= 0x2B73F or
                    0x2B740 <= cp <= 0x2B81F or 0x2B820 <= cp <= 0x2CEAF or
                    0xF900 <= cp <= 0xFAFF or 0x2F800 <= cp <= 0x2FA1F):
                out.append(" " + ch + " ")
            else:
                out.append(ch)
        text = "".join(out)
        out = []
        for ch in text:
            if ch == " " or ch.isspace():
                out.append(" ")
            elif ch in PUNCT or unicodedata.category(ch).startswith("P") or unicodedata.category(ch) == "So":
                out.append(" " + ch + " ")
            else:
                out.append(ch)
        return re.sub(r"\s+", " ", text).strip()

    def wordpiece(self, word):
        if word in self.vocab:
            return [word]
        pieces = []
        start = 0
        while start < len(word):
            end = len(word)
            cur = None
            while start < end:
                sub = word[start:end]
                if start > 0:
                    sub = "##" + sub
                if sub in self.vocab:
                    cur = sub
                    break
                end -= 1
            if cur is None:
                return [self.unk]
            pieces.append(cur)
            start = end
        return pieces

    def encode(self, text):
        ids = [self.cls]
        for word in self.normalize(text).split(" "):
            if word == "":
                continue
            for p in self.wordpiece(word):
                ids.append(self.vocab.get(p, self.unk))
        ids.append(self.sep)
        return ids[: self.max_len - 1] + [self.sep] if len(ids) > self.max_len else ids

    def decode(self, ids):
        out = []
        for i in ids:
            t = self.ids.get(int(i), "[UNK]")
            if t in ("[CLS]", "[SEP]", "[PAD]"):
                continue
            out.append(t[2:] if t.startswith("##") else (" " + t))
        return "".join(out).strip()


class BertEncoder:
    """all-MiniLM-L6-v2: 6-layer BERT, mean pooling, L2 normalisation."""

    def __init__(self, cfg_path, w_path, dtype=torch.float32):
        c = json.load(open(cfg_path))
        self.c = c
        self.st = ST(w_path)
        self.h = c["hidden_size"]
        self.nh = c["num_attention_heads"]
        self.hd = self.h // self.nh
        self.nlayer = c["num_hidden_layers"]
        self.eps = c["layer_norm_eps"]
        self.maxpos = c["max_position_embeddings"]
        self.act = c["hidden_act"]
        self.pooling = "mean"
        self.reverse_attention = False

    def _ln(self, x, p):
        m = x.mean(-1, keepdim=True)
        v = x.var(-1, unbiased=False, keepdim=True)
        return (x - m) / torch.sqrt(v + self.eps) * self.st.get(p + ".weight") + self.st.get(p + ".bias")

    def _act(self, x):
        if self.act == "gelu":
            return torch.nn.functional.gelu(x)
        return torch.nn.functional.relu(x)

    def embeddings(self, ids, ttids):
        w = self.st.get("embeddings.word_embeddings.weight")[ids]
        p = self.st.get("embeddings.position_embeddings.weight")[torch.arange(ids.shape[-1])]
        t = self.st.get("embeddings.token_type_embeddings.weight")[ttids]
        return self._ln(w + p + t, "embeddings.LayerNorm")

    def forward(self, ids, ttids, mask):
        x = self.embeddings(ids, ttids)
        T = ids.shape[-1]
        add = (1.0 - mask[:, None, None, :].float()) * -10000.0
        for i in range(self.nlayer):
            pre = "encoder.layer.{}.attention.".format(i)
            q = (x @ self.st.get(pre + "self.query.weight").T + self.st.get(pre + "self.query.bias"))
            k = (x @ self.st.get(pre + "self.key.weight").T + self.st.get(pre + "self.key.bias"))
            v = (x @ self.st.get(pre + "self.value.weight").T + self.st.get(pre + "self.value.bias"))
            q = q.view(1, T, self.nh, self.hd).transpose(1, 2)
            k = k.view(1, T, self.nh, self.hd).transpose(1, 2)
            v = v.view(1, T, self.nh, self.hd).transpose(1, 2)
            att = (q @ k.transpose(-1, -2)) / math.sqrt(self.hd) + add
            att = att.softmax(-1)
            if self.reverse_attention:
                att = att.flip(-1)
            ctx = (att @ v).transpose(1, 2).reshape(1, T, self.h)
            ctx = ctx @ self.st.get(pre + "output.dense.weight").T + self.st.get(pre + "output.dense.bias")
            x = self._ln(x + ctx, pre + "output.LayerNorm")
            post = "encoder.layer.{}.intermediate.".format(i)
            inter = self._act(x @ self.st.get(post + "dense.weight").T + self.st.get(post + "dense.bias"))
            out = "encoder.layer.{}.output.".format(i)
            h = inter @ self.st.get(out + "dense.weight").T + self.st.get(out + "dense.bias")
            x = self._ln(x + h, out + "LayerNorm")
        return x

    def pool(self, x, mask):
        if self.pooling == "mean":
            m = mask[:, :, None].float()
            s = (x * m).sum(1) / m.sum(1).clamp(min=1e-9)
        else:
            s = x[:, 0]
        return s

    def encode(self, tok, texts, batch_note=None):
        if isinstance(texts, str):
            texts = [texts]
        out = []
        with torch.no_grad():
            for t in texts:
                ids = tok.encode(t)
                ii = torch.tensor([ids])
                tt = torch.zeros_like(ii)
                mk = torch.ones_like(ii)
                x = self.forward(ii, tt, mk)
                e = self.pool(x, mk)[0]
                e = e / e.norm(p=2).clamp(min=1e-9)
                out.append(e)
        if len(out) == 1:
            return out[0]
        return torch.stack(out)


def load_minilm():
    d = snap("sentence-transformers/all-MiniLM-L6-v2")
    tok = WordPiece(os.path.join(d, "vocab.txt"))
    enc = BertEncoder(os.path.join(d, "config.json"), os.path.join(d, "model.safetensors"))
    return tok, enc
