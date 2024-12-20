# Author: Yura Sokolov
# Heavily inspired by https://github.com/true-grue/peco by Peter Sovietov
import re
from collections import namedtuple
from dataclasses import dataclass

__all__ = 'State Stack PosState cons Peco backtrack empty fail ' \
          'do map0 map1 map2 map3 mapN map1acc map2acc map3acc mapNacc opt ' \
          'lit seq alt cut rep put grp eof will wont'.split()

State = namedtuple('State', 'stk acc')
Stack = namedtuple('Stack', 'v t')
PosState = namedtuple('PosState', 'pos state')

_uniq = object()
def cons(state, v, st=_uniq):
    if st is _uniq:
        st = state.stk
    return state._replace(stk=Stack(v, st))

@dataclass
class Peco:
    text: str
    pos: int = 0
    maxpos: int = 0
    maxst: State = None
    cut: bool = False
    def __init__(self, text, pos=0):
        self.text = text
        self.pos = pos
    def parse(self, f, state=State(None, None)):
        return self, f(self, state)
    def loc(self, pos):
        text = self.text
        line = text.count('\n', 0, pos)
        col = pos - text.rfind('\n', 0, pos) - 1
        return line, col


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
map0 = lambda v: lambda p, s: cons(s, v, s.stk)
map1 = lambda f: lambda p, s: cons(s, f(s.stk.v), s.stk.t)
map2 = lambda f: lambda p, s: cons(s, f(s.stk.t.v, s.stk.v), s.stk.t.t)
map3 = lambda f: lambda p, s: cons(s, f(s.stk.t.t.v, s.stk.t.v, s.stk.v), s.stk.t.t.t)
def mapN(f):
    n = f.__code__.co_argcount
    def app(p, s):
        a, st = [], s.stk
        while len(a) < n:
            a.append(st.v)
            st = st.t
        a.reverse()
        return cons(s, f(*a), st)
    return app
map1acc = lambda f: lambda p, s: cons(s, f(s.stk.v, acc=s.acc), s.stk.t)
map2acc = lambda f: lambda p, s: cons(s, f(s.stk.t.v, s.stk.v, acc=s.acc), s.stk.t.t)
map3acc = lambda f: lambda p, s: cons(s, f(s.stk.t.t.v, s.stk.t.v, s.stk.v, acc=s.acc), s.stk.t.t.t)
def mapNacc(f):
    n = f.__code__.co_argcount
    def app(p, s):
        a, st = [], s.stk
        while len(a) < n:
            a.append(st.v)
            st = st.t
        a.reverse()
        return cons(s, f(*a), st, acc=s.acc)
    return app
opt = lambda f: alt(f, empty)


def lit(expr):
    if not isinstance(expr, str):
        return expr
    if not expr.startswith('/'):
        def parse(p, s):
            if p.text.startswith(expr, p.pos):
                p.pos = pos = p.pos + len(expr)
                if pos > p.maxpos:
                    p.maxpos = pos
                    p.maxst = s
                return s
        parse._lit = expr
    else:
        expr = re.compile('(?:'+expr[1:]+')')
        def parse(p, s):
            if (m := expr.match(p.text, p.pos)):
                p.pos = pos = m.end()
                if pos > p.maxpos:
                    p.maxpos = pos
                    p.maxst = s
                return s
        parse._lit = expr
    return parse


def seq(*fs):
    fs = tuple(lit(f) for f in fs)
    if not len(fs):
        return empty
    fs = _simplify_seq(fs)
    if len(fs) == 1:
        return fs[0]
    @backtrack
    def parse(p, s):
        for f in fs:
            if not (s := f(p, s)):
                return None
        return s
    parse._seq = fs
    return parse


def alt(*fs):
    fs = tuple(lit(f) for f in fs)
    fs = _simplify_alt(fs)
    if len(fs) == 1 and hasattr(fs[0], '_lit'):
        return fs[0]
    def parse(p, s):
        for f in fs:
            if (new_s := f(p, s)):
                return new_s
            if p.cut:
                break
    parse = _save_cut(parse)
    parse._alt = fs
    return parse


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


def put(*f, map=None, maps=None):
    f = seq(*f)
    maps = _map(map, maps)
    def parse(p, s):
        pos = p.pos
        if (s := f(p, s)):
            return cons(s, maps(p.text[pos:p.pos], s), s.stk)
    return parse


def grp(*f, map=None, maps=None):
    f = seq(*f)
    maps = _map(map, maps)
    def parse(p, s):
        st = s.stk
        if (s := f(p, s)):
            return cons(s, maps(_get_depth(st, s.stk), s), st)
    return parse


def will(*f):
    f = seq(*f)
    def parse(p, s):
        p.pos, maxpos, maxst, ns = p.pos, p.maxpos, p.maxst, f(p, s)
        if ns:
            p.maxpos = maxpos
            p.maxst = maxst
            return s
    return parse


def wont(*f):
    f = seq(*f)
    def parse(p, s):
        p.pos, p.maxpos, p.maxst, ns = p.pos, p.maxpos, p.maxst, f(p, s)
        if not ns:
            return s
    return parse


def eof(p, s):
    if p.pos == len(p.text):
        return s


# private


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
            l += "(?:"+re.escape(f0._lit)+")"
        if isinstance(f1._lit, re.Pattern):
            l += f1._lit.pattern
        else:
            l += "(?:"+re.escape(f1._lit)+")"
    return lit(l)


def _simplify_seq(fs):
    i, fs = 0, list(fs)
    while i < len(fs):
        f = fs[i]
        if hasattr(f, '_seq'):
            fs[i:i+1] = f._seq
        else:
            i += 1
    i = 0
    while i + 1 < len(fs):
        if (f := _join(fs[i], fs[i+1])):
            fs.pop(i)
            fs[i] = f
        else:
            i += 1
    return tuple(fs)


def _map(map, maps):
    if maps is not None:
        return maps
    if map is not None:
        return lambda v, s: map(v)
    return lambda v, s: v


def _save_cut(f):
    def save(p, s):
        cut, p.cut = p.cut, False
        p.cut, s = cut, f(p, s)
        return s
    return save


def _alt(f0, f1):
    if not (hasattr(f0, '_lit') and hasattr(f1, '_lit')):
        return None
    l = '/(?:'
    if isinstance(f0._lit, re.Pattern):
        l += f0._lit.pattern
    else:
        l += re.escape(f0._lit)
    l += '|'
    if isinstance(f1._lit, re.Pattern):
        l += f1._lit.pattern
    else:
        l += re.escape(f1._lit)
    l += ')'
    return lit(l)


def _simplify_alt(fs):
    i, fs = 0, list(fs)
    while i < len(fs):
        f = fs[i]
        if hasattr(f, '_alt'):
            fs[i:i+1] = f._alt
        else:
            i += 1
    i = 0
    while i + 1 < len(fs):
        if (f := _alt(fs[i], fs[i+1])):
            fs.pop(i)
            fs[i] = f
        else:
            i += 1
    return tuple(fs)


def _get_depth(old_st, st):
    arr = []
    while st != old_st:
        v, st = st
        arr.append(v)
    arr.reverse()
    return tuple(arr)


