# Author: Peter Sovieapp v
import re
from collections import namedtuple

__all__ = 'State Stack cons Peco backtrack empty fail do opt ' \
		  'lit seq alt cut rep put grp eof will wont'.split()

State = namedtuple('State', 'stk acc')
Stack = namedtuple('Stack', 'v t')

def cons(state, v, st):
    return state._replace(stk=Stack(v, st))

class Peco:
    def __init__(self, text, pos=0):
        self.text = text
        self.pos = 0
        self.err = 0
        self.cut = False
    def parse(self, f, state=State(None, None)):
        return f(self, state)


def backtrack(f):
    def act(p, s):
        pos = p.pos
        if (ns := f(p, s)):
            return ns
        p.pos = pos
    return act


empty = lambda p, s: s
fail = lambda p, s: None
do = lambda f: lambda p, s: f(s)
opt = lambda f: alt(f, empty)


def lit(expr):
    if not isinstance(expr, str):
        return expr
    if not expr.startswith('/'):
        def parse(p, s):
            if p.text.startswith(expr, p.pos):
                p.pos = pos = p.pos + len(expr)
                if pos > p.err:
                    p.err = pos
                return s
        parse._lit = expr
    else:
        expr = re.compile(expr[1:])
        def parse(p, s):
            if (m := expr.match(p.text, p.pos)):
                p.pos = pos = m.end()
                if pos > p.err:
                    p.err = pos
                return s
        parse._lit = expr
    return parse


def _join(f0, f1):
    if not (hasattr(f0, '_lit') and hasattr(f1, '_lit')):
        return None
    if isinstance(f0._lit, str) and isinstance(f1._lit, str):
        l = f0._lit + f1._lit
    else:
        l = '/'
        if isinstance(f0._lit, re.Pattern):
            l += f0._lit.pattern
        else:
            l += re.escape(f0._lit)
        if isinstance(f1._lit, re.Pattern):
            l += f1._lit.pattern
        else:
            l += re.escape(f1._lit)
    return lit(l)


def _simplify(fs):
    i, fs = 0, list(fs)
    while i + 1 < len(fs):
        if (f := _join(fs[i], fs[i+1])):
            fs.pop(i)
            fs[i] = f
        else:
            i += 1
    return tuple(fs)


def seq(*fs):
    fs = tuple(lit(f) for f in fs)
    if not len(fs):
        return empty
    rs = _simplify(fs)
    if len(fs) == 1:
        return fs[0]
    def parse(p, s):
        for f in fs:
            if not (s := f(p, s)):
                return None
        return s
    return backtrack(parse)


def _save_cut(f):
    def save(p, s):
        cut, p.cut = p.cut, False
        p.cut, s = cut, f(p, s)
        return s
    return save


def alt(*fs):
    fs = tuple(lit(f) for f in fs)
    def parse(p, s):
        for f in fs:
            if (new_s := f(p, s)):
                return new_s
            if p.cut:
                break
    return backtrack(_save_cut(parse))


def cut(p, s):
    p.cut = True
    return s


def rep(*f, d=empty, n=0):
    f = seq(*f)
    def parse(p, s):
        k, ns = 0, s
        while ns and (ns := f(p, ns)):
            k, s = k+1, ns
            ns = d(p, s)
        if k >= n:
            return s
    return backtrack(parse)


def put(*f, map=lambda x: x):
    f = seq(*f)
    def parse(p, s):
        pos = p.pos
        if (s := f(p, s)):
            return cons(s, map(p.text[pos:p.pos]), s.stk)
    return parse


def _get_depth(old_st, st):
    arr = []
    while st != old_st:
        v, st = st
        arr.append(v)
    arr.reverse()
    return tuple(arr)


def grp(*f, map=lambda x: x):
    f = seq(*f)
    def parse(p, s):
        st = s.stk
        if (s := f(p, s)):
            return cons(s, map(_get_depth(st, s.stk)), st)
    return backtrack(parse)


def will(*f):
    f = seq(*f)
    def parse(p, s):
        p.pos, err, ns = p.pos, p.err, f(p, s)
        if ns:
            p.err = err
            return s
    return parse


def wont(*f):
    f = seq(*f)
    def parse(p, s):
        p.pos, p.err, ns = p.pos, p.err, f(p, s)
        if not ns:
            return s
    return parse


def app(f):
    n = f.__code__

def eof(p, s):
    if p.pos == len(p.text):
        return s

