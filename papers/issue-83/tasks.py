"""Issue 79: synthetic task families, tokenizer, answer parsing (stdlib only)."""

import random
import string

CHARS = string.ascii_lowercase + string.digits + " :_=+"
ALPHA = "abcd"


class CharTok:
    def __init__(self):
        self.chars = CHARS
        self.stoi = dict((c, i) for i, c in enumerate(CHARS))
        self.itos = dict((i, c) for c, i in self.stoi.items())
        self.pad = len(CHARS)
        self.bos = len(CHARS) + 1
        self.vocab = len(CHARS) + 2

    def encode(self, text):
        return [self.bos] + [self.stoi[c] for c in text]

    def decode(self, ids):
        return "".join(self.itos.get(int(i), "?") for i in ids)


def make_count(tok, L, rng):
    sym = rng.choice(ALPHA)
    seq = "".join(rng.choice(ALPHA) for _ in range(L))
    n = seq.count(sym)
    prompt = "count:%s in:%s=" % (sym, seq)
    answer = "answer:%d_" % n
    return tok.encode(prompt + answer), prompt, answer


def make_add(tok, ndig, rng):
    a = rng.randint(10 ** (ndig - 1), 10 ** ndig - 1)
    b = rng.randint(10 ** (ndig - 1), 10 ** ndig - 1)
    s = a + b
    prompt = "add:%d+%d=" % (a, b)
    answer = "answer:%d_" % s
    return tok.encode(prompt + answer), prompt, answer


def make_par(tok, ndig, rng):
    a = rng.randint(10 ** (ndig - 1), 10 ** ndig - 1)
    b = rng.randint(10 ** (ndig - 1), 10 ** ndig - 1)
    s = a + b
    prompt = "par:%d+%d=" % (a, b)
    answer = "answer:%d_" % (s % 2)
    return tok.encode(prompt + answer), prompt, answer


def make_example(tok, task, L, rng):
    if task == "count":
        return make_count(tok, L, rng)
    if task == "add":
        return make_add(tok, L, rng)
    if task == "par":
        return make_par(tok, L, rng)
    raise ValueError(task)


def parse_answer(txt):
    marker = "answer:"
    if marker in txt:
        rest = txt.split(marker)[-1]
        digits = ""
        for c in rest:
            if c.isdigit():
                digits += c
            else:
                break
        if digits:
            return digits
    return None


def truth_answer(full_text):
    return parse_answer(full_text)


def selftest(n=1500, seed=0):
    rng = random.Random(seed)
    tok = CharTok()
    for task in ("count", "add"):
        for _ in range(n):
            L = rng.randint(4, 16) if task == "count" else rng.randint(1, 4)
            ids, prompt, answer = make_example(tok, task, L, rng)
            text = prompt + answer
            assert tok.decode(ids[1:]) == text, (task, text)
            assert parse_answer(text) == truth_answer(text)
    assert parse_answer("answer:12x_") == "12"
    assert parse_answer("answer:_") is None
    assert parse_answer("") is None
    for _ in range(300):
        L = rng.randint(1, 20)
        ids, prompt, answer = make_count(tok, L, rng)
        n = int(parse_answer(answer))
        head, tail = prompt.split(" in:", 1)
        sym = head[len("count:"):]
        seq = tail.rstrip("=")
        assert seq.count(sym) == n, (prompt, answer, n)
    for _ in range(300):
        ndig = rng.randint(1, 4)
        ids, prompt, answer = make_add(tok, ndig, rng)
        s = int(parse_answer(answer))
        inner = prompt[4:].strip("=")
        a, b = inner.split("+")
        assert int(a) + int(b) == s, (prompt, answer)
    print("tasks selftest OK charset=%d vocab=%d" % (len(tok.chars), tok.vocab))


if __name__ == "__main__":
    selftest()
