from peco2 import *
import json

ws = lit(r'/\s*')
tok = lambda f: seq(ws, f)

number = put(r'/-?([1-9]\d*|0)(\.\d+)?((e|E)[-+]?\d+)?', map=float)

value = lambda p, s: value(p, s)

array = grp(tok('['), rep(value, d=tok(',')), tok(']'))
value = alt(tok(number), array)
jsonp = seq(array, ws)


def main():
    v = tuple(tuple(range(10)) for _ in range(100))
    #v = tuple(tuple(range(3)) for _ in range(3))
    x = json.dumps(v)
    for _ in range(2000):
        s = Peco(x).parse(jsonp)
    assert s.stk.v == v

main()
