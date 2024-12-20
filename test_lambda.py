from peco2 import *

ws = lit(r'/\s*')
tok = lambda *f: seq(*f, ws)

mkfun = map2(lambda args, body: ('fun', args, body))
mkapp = mapN(lambda func, args: ('app', func, args))

expr = lambda p, s: expr(p, s)
atom = tok(put(r'/[a-zA-Z]'))
func = seq(tok('λ'), cut, atom, tok('.'), expr, mkfun)
pars = seq(tok('('), cut, expr, tok(')'))
one = alt(func, pars, atom)
expr = seq(one, opt(seq(expr, mkapp)))


def test():
    x = ' λb. λg. (λa.b g(a))  '
    y = ('fun', 'b',
          ('fun', 'g',
           ('fun', 'a',
            ('app', 'b',
             ('app', 'g', 'a')))))
    p, s = Peco(x).parse(seq(ws, expr))
    assert s and s.stk.v == y
