#!/usr/bin/env python3
"""Toy language + reference interpreter for issue #114.

WHY THIS FILE EXISTS
--------------------
The study's instrument needs a program space whose *semantics is known by
construction*, so that "this change is semantics-preserving" and "this change is
a defect" are decided by an oracle rather than by a human label.  This module
supplies the ground truth: a tiny straight-line language over the finite ring
Z_M, whose meaning is the complete table  x -> output(x)  for x in Z_M.

Two programs are semantically equivalent iff their tables are equal.  That is
exact and decidable (256-point tables), which is what makes the downstream
specificity/exposure measurements possible without any annotation.

LANGUAGE (v0, deliberately small but not trivial)
-------------------------------------------------
  expr := <int>                      constant, reduced mod M
        | x                        the single input variable
        | (add e1 e2) | (sub e1 e2) | (mul e1 e2)
        | (max e1 e2) | (min e1 e2)
        | (mod e1 <int>)           e1 % n, 1 <= n < M
        | (lt e1 e2)               boolean, encoded as 0/1
        | (not b) | (and b1 b2) | (or b1 b2)
        | (ite c e1 e2)            c truthy iff != 0

Everything is an element of Z_M = {0,...,M-1}; booleans are the subset {0,1}.
No side effects, no variables, no recursion -- so the denotation is a total
function of the single input and the table IS the semantics.

USAGE
-----
    from toylang import parse, table, equivalent
    p = parse("(ite (lt x 128) (mul x 2) (sub 200 x))")
    table(p)            # tuple of M ints -- the complete meaning
    equivalent(p, q)    # exact semantic equality
"""

from __future__ import annotations

import re

M = 256  # modulus: all values live in Z_M


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\(|\)|[^\s()]+")

_BINOPS = {"add", "sub", "mul", "max", "min", "lt", "and", "or"}
_UNOPS = {"not"}
_ARITY = {
    "add": 2, "sub": 2, "mul": 2, "max": 2, "min": 2,
    "lt": 2, "and": 2, "or": 2, "not": 1, "ite": 3, "mod": 2,
}


def tokenize(src: str):
    return _TOKEN_RE.findall(src)


def _build(op: str, args, src: str):
    if op not in _ARITY:
        raise SyntaxError(f"unknown operator {op!r} in {src!r}")
    if len(args) != _ARITY[op]:
        raise SyntaxError(f"{op} takes {_ARITY[op]} args, got {len(args)}")
    node = (op, *args)
    if op == "mod":
        n = node[2]
        if n[0] != "const" or not (1 <= n[1] < M):
            raise SyntaxError("mod's second argument must be an int literal in 1..M-1")
    return node


def parse(src: str):
    """Parse an s-expression source string into an AST (nested tuples)."""
    toks = tokenize(src)
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else None

    def take():
        nonlocal pos
        if pos >= len(toks):
            raise SyntaxError(f"unexpected end of input in {src!r}")
        t = toks[pos]
        pos += 1
        return t

    def parse_expr():
        t = take()
        if t == "(":
            op = take()
            if op in ("(", ")"):
                raise SyntaxError(f"expected an operator after '(' in {src!r}")
            args = []
            while peek() != ")":
                if peek() is None:
                    raise SyntaxError(f"unclosed '(' in {src!r}")
                args.append(parse_expr())
            take()  # consume ')'
            return _build(op, args, src)
        if t == "x":
            return ("x",)
        if re.fullmatch(r"-?\d+", t):
            return ("const", int(t) % M)
        raise SyntaxError(f"unexpected token {t!r} in {src!r}")

    node = parse_expr()
    if pos != len(toks):
        raise SyntaxError(f"trailing tokens after expression in {src!r}")
    return node


# --------------------------------------------------------------------------
# printing
# --------------------------------------------------------------------------

def to_str(e) -> str:
    op = e[0]
    if op == "const":
        return str(e[1])
    if op == "x":
        return "x"
    return "(" + op + " " + " ".join(to_str(a) for a in e[1:]) + ")"


# --------------------------------------------------------------------------
# the reference interpreter  ==  the semantics oracle
# --------------------------------------------------------------------------

def eval_expr(e, x: int) -> int:
    """Evaluate AST `e` at input `x`, in Z_M."""
    op = e[0]
    if op == "const":
        return e[1] % M
    if op == "x":
        return x % M
    if op == "add":
        return (eval_expr(e[1], x) + eval_expr(e[2], x)) % M
    if op == "sub":
        return (eval_expr(e[1], x) - eval_expr(e[2], x)) % M
    if op == "mul":
        return (eval_expr(e[1], x) * eval_expr(e[2], x)) % M
    if op == "mod":
        # the divisor is a literal by construction; assert it rather than assume,
        # so an ill-typed program fails loudly instead of yielding a bogus table
        if e[2][0] != "const" or not (1 <= e[2][1] < M):
            raise ValueError(f"mod divisor must be a literal in 1..M-1, got {e[2]!r}")
        return eval_expr(e[1], x) % e[2][1]
    if op == "max":
        return max(eval_expr(e[1], x), eval_expr(e[2], x))
    if op == "min":
        return min(eval_expr(e[1], x), eval_expr(e[2], x))
    if op == "lt":
        return 1 if eval_expr(e[1], x) < eval_expr(e[2], x) else 0
    if op == "not":
        return 0 if eval_expr(e[1], x) else 1
    if op == "and":
        return 1 if (eval_expr(e[1], x) and eval_expr(e[2], x)) else 0
    if op == "or":
        return 1 if (eval_expr(e[1], x) or eval_expr(e[2], x)) else 0
    if op == "ite":
        return eval_expr(e[2], x) if eval_expr(e[1], x) else eval_expr(e[3], x)
    raise ValueError(f"unknown node {op!r}")


def table(e, domain=None):
    """The complete denotation of `e`: output for every input. This IS the semantics."""
    if domain is None:
        domain = range(M)
    return tuple(eval_expr(e, x) for x in domain)


def equivalent(a, b, domain=None) -> bool:
    """Exact semantic equivalence: the two programs denote the same function."""
    return table(a, domain) == table(b, domain)
