# Author: Peter Sovietov
import re
from collections import namedtuple

Peco = namedtuple('Peco', 'text pos ok stack glob')

head = lambda p: p[0]
tail = lambda p: p[1]


def eat(expr):
    code = re.compile(expr)

    def parse(s):
        if (m := code.match(s.text, s.pos)) is None:
            return s._replace(ok=False)
        pos = s.pos + len(m.group())
        s.glob['err'] = max(s.glob['err'], pos)
        return s._replace(pos=pos)
    return parse


def seq(*funcs):
    def parse(s):
        for f in funcs:
            if not (s := f(s)).ok:
                return s
        return s
    return parse


def alt(*funcs):
    def parse(s):
        for f in funcs:
            if (new_s := f(s)).ok:
                return new_s
        return new_s
    return parse


def many(f):
    def parse(s):
        while (new_s := f(s)).ok:
            s = new_s
        return s
    return parse


def push(f):
    def parse(s):
        pos = s.pos
        if not (s := f(s)).ok:
            return s
        return s._replace(stack=(s.text[pos:s.pos], s.stack))
    return parse


def get_args(st, n):
    args = [None] * n
    for i in range(n):
        args[n - 1 - i], st = head(st), tail(st)
    return tuple(args), st


def to(f):
    n = f.__code__.co_argcount

    def parse(s):
        args, st = get_args(s.stack, n)
        return s._replace(stack=(f(*args), st))
    return parse


def get_depth(old_st, st):
    d = 0
    while st != old_st:
        d, st = d + 1, tail(st)
    return d


def group(f):
    def parse(s):
        stack = s.stack
        if not (s := f(s)).ok:
            return s
        return s._replace(stack=get_args(s.stack, get_depth(stack, s.stack)))
    return parse


def peek(f):
    def parse(s):
        return s._replace(ok=f(s).ok)
    return parse


def npeek(f):
    def parse(s):
        return s._replace(ok=not f(s).ok)
    return parse


def memo(f):
    def parse(s):
        key = f, s.pos
        tab = s.glob['tab']
        if key not in tab:
            tab[key] = f(s)
        return tab[key]
    return parse


def left(f):
    def parse(s):
        key = f, s.pos
        tab = s.glob['tab']
        if key not in tab:
            tab[key] = s._replace(ok=False)
            pos = s.pos
            while (s := f(s._replace(pos=pos))).pos > tab[key].pos:
                tab[key] = s
        return tab[key]
    return parse


def eof(s):
    return s._replace(ok=s.ok and s.pos == len(s.text))


def parse(text, f):
    return eof(f(Peco(text, 0, True, None, dict(err=0, tab={}))))


empty = lambda s: s
opt = lambda f: alt(f, empty)
some = lambda f: seq(f, many(f))
list_of = lambda f, d: seq(f, many(seq(d, f)))
