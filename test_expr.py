from peco2 import *

ws = lit(r'/\s*')
tok = lambda *f: seq(ws, *f)

mkvar = lambda x: ('var', x)
mknum = lambda x: ('num', x)
def mkbops(grp):
    e = grp[0]
    for i in range(1, len(grp), 2):
        print(len(grp), i)
        e = (grp[i], e, grp[i+1])
    return e

var = tok(put(r'/[a-zA-Z][a-zA-Z0-9]*', map=mkvar))
num = tok(put(r'/\d+', map=mknum))

expr = lambda p, s: expr(p, s)

factor = alt(
    seq(tok('('), cut, expr, tok(')')),
    var,
    num
)

term = grp(rep(factor, d=tok(put(r'/\*|/')), n=1), map=mkbops)
expr = grp(rep(term, d=tok(put(r'/\+|-')), n=1), map=mkbops)

main = seq(expr, ws, eof)


def test():
    x = '  (foo+ bar)*4 - (12/ a) '
    y = ('-', ('*', ('+', ('var', 'foo'), ('var', 'bar')), ('num', '4')),
         ('/', ('num', '12'), ('var', 'a')))
    _, s = Peco(x).parse(main)
    assert s and s.stk.v == y
    err_x = '(b*b - 3* a*c )) + a'
    err_y = '               ^'
    p, s = Peco(err_x).parse(main)
    assert not s and ' ' * p.maxpos + '^' == err_y
