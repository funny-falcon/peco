from peco2 import *


mkrepeat = lambda a: ('repeat', *a)
mkcall = lambda n: ('call', n)
mkfunc = lambda n, b: ('func', n, b)
mkblock = lambda b: ('block', b)

ws = lit(r'/\s*|#.*')
tok = lambda *f: seq(*f, ws)

name = tok(put(r'/[a-zA-Z_][a-zA-Z0-9_]*'))
num = tok(put(r'/-?[0-9]+', map=float))

cmd = lambda p, s: cmd(p, s)
block = lambda end: grp(rep(seq(wont(end), cmd)), end, map=mkblock)

cmd = alt(
    grp(tok(put('/fd|bk|lt|rt')), cut, num, map=tuple),
    tok(put('/pu|pd', map=lambda m: (m,))),
    grp(tok('repeat'), cut, num, tok(r'['), block(tok(r']')), map=mkrepeat),
    seq(name, map1(mkcall))
)

func = seq(tok('to'), cut, name, block(tok('end')), map2(mkfunc))
main = seq(ws, grp(rep(alt(func, cmd)), map=mkblock))


def test():
    src = '''
    to star
      repeat 5 [fd 100 rt 144]
    end
    star
    '''
    p, s = Peco(src).parse(main)
    result = ('block',
               (('func',
                 'star',
                 ('block',
                  (('repeat',
                    5.0,
                    ('block',
                     (('fd', 100.0),
                      ('rt', 144.0)))),))),
                ('call', 'star')))
    assert s and s.stk.v == result
    err = '''
    to center_top
      pu
      fd 80
      rt !90
      fd 20
      lt 90
      pd
    end
    '''
    p, s = Peco(err).parse(seq(main, eof))
    assert not s and p.loc(p.maxpos) == (4, 9)
