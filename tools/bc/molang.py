"""Tiny Molang evaluator used only by the preview renderer (not shipped)."""
from __future__ import annotations

import math
import re

TOKEN = re.compile(r"\s*(?:(\d+\.\d*|\.\d+|\d+)f?|([A-Za-z_][A-Za-z0-9_.]*)|'([^']*)'|(&&|\|\||==|!=|<=|>=|\?\?|[-+*/()?:,<>!;=]))")


def tokenize(s):
    pos, out = 0, []
    s = s.strip()
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m:
            raise ValueError(f'bad molang near {s[pos:pos+10]!r}')
        num, ident, sval, op = m.groups()
        if sval is not None:
            out.append(('str', sval))
        elif num is not None:
            out.append(('num', float(num)))
        elif ident is not None:
            out.append(('id', ident.lower()))
        else:
            out.append(('op', op))
        pos = m.end()
    out.append(('end', None))
    return out


def _deg(f):
    return lambda x: f(math.radians(x))


FUNCS = {
    'math.sin': _deg(math.sin), 'math.cos': _deg(math.cos), 'math.abs': abs,
    'math.clamp': lambda x, a, b: max(a, min(b, x)), 'math.lerp': lambda a, b, t: a + (b - a) * t,
    'math.pow': math.pow, 'math.sqrt': math.sqrt, 'math.min': min, 'math.max': max,
    'math.floor': math.floor, 'math.ceil': math.ceil, 'math.round': round, 'math.mod': math.fmod,
    'math.exp': math.exp, 'math.pi': None, 'math.random': lambda a, b: (a + b) / 2,
    'math.atan2': lambda y, x: math.degrees(math.atan2(y, x)),
}


class Parser:
    def __init__(self, toks, env):
        self.t = toks
        self.i = 0
        self.env = env

    def peek(self):
        return self.t[self.i]

    def next(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def expect(self, op):
        tok = self.next()
        if tok != ('op', op):
            raise ValueError(f'expected {op} got {tok}')

    def parse(self):
        v = self.ternary()
        return v

    def ternary(self):
        c = self.logic_or()
        if self.peek() == ('op', '?'):
            self.next()
            a = self.ternary()
            if self.peek() == ('op', ':'):
                self.next()
                b = self.ternary()
            else:
                b = 0.0
            return a if c else b
        return c

    def logic_or(self):
        v = self.logic_and()
        while self.peek() == ('op', '||'):
            self.next()
            r = self.logic_and()
            v = 1.0 if (v or r) else 0.0
        return v

    def logic_and(self):
        v = self.cmp()
        while self.peek() == ('op', '&&'):
            self.next()
            r = self.cmp()
            v = 1.0 if (v and r) else 0.0
        return v

    def cmp(self):
        v = self.add()
        while self.peek()[0] == 'op' and self.peek()[1] in ('<', '>', '<=', '>=', '==', '!='):
            op = self.next()[1]
            r = self.add()
            v = float({'<': lambda: v < r, '>': lambda: v > r, '<=': lambda: v <= r, '>=': lambda: v >= r, '==': lambda: v == r, '!=': lambda: v != r}[op]())
        return v

    def add(self):
        v = self.mul()
        while self.peek()[0] == 'op' and self.peek()[1] in '+-' and len(self.peek()[1]) == 1:
            op = self.next()[1]
            r = self.mul()
            v = v + r if op == '+' else v - r
        return v

    def mul(self):
        v = self.unary()
        while self.peek()[0] == 'op' and self.peek()[1] in ('*', '/'):
            op = self.next()[1]
            r = self.unary()
            v = v * r if op == '*' else (v / r if r else 0.0)
        return v

    def unary(self):
        tok = self.peek()
        if tok == ('op', '-'):
            self.next()
            return -self.unary()
        if tok == ('op', '!'):
            self.next()
            return 0.0 if self.unary() else 1.0
        return self.primary()

    def primary(self):
        tok = self.next()
        if tok[0] in ('num', 'str'):
            return tok[1]
        if tok == ('op', '('):
            v = self.ternary()
            self.expect(')')
            return v
        if tok[0] == 'id':
            name = tok[1]
            name = name.replace('query.', 'q.').replace('variable.', 'v.').replace('context.', 'c.')
            if self.peek() == ('op', '('):
                self.next()
                args = []
                if self.peek() != ('op', ')'):
                    args.append(self.ternary())
                    while self.peek() == ('op', ','):
                        self.next()
                        args.append(self.ternary())
                self.expect(')')
                if name in FUNCS and FUNCS[name]:
                    return float(FUNCS[name](*args))
                return float(self.env.get(name, 0.0))
            if name == 'math.pi':
                return math.pi
            if name == 'this':
                return 0.0
            val = self.env.get(name, 0.0)
            return val if isinstance(val, str) else float(val)
        raise ValueError(f'unexpected {tok}')


def evaluate(expr, env=None):
    if isinstance(expr, (int, float)):
        return float(expr)
    env = env or {}
    try:
        # only evaluate last statement for multi-statement strings
        parts = [p for p in str(expr).split(';') if p.strip()]
        return Parser(tokenize(parts[-1]), env).parse()
    except Exception:
        return 0.0
