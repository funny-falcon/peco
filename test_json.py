from peco2 import *

mktrue = map0(True)
mkfalse = map0(False)
mknone = map0(None)

ws = lit(r'/\s*')
tok = lambda *f: seq(*f, ws)

number = tok(put(r'/-?([1-9]\d+|0)(\.\d+)?((e|E)[-+]?\d+)?', map=float))
uXXXX = lit(r'/u(\d|[a-f]|[A-F]){4}')
escaped = seq(r'\\', alt(r'/["\\/bfnrt]', uXXXX))
string = put(tok('"'), cut, rep(alt(r'/[^"\\]+', escaped)), tok('"'), map=eval)

true = seq(tok('true'), mktrue)
false = seq(tok('false'), mkfalse)
null = seq(tok('null'), mknone)

value = lambda p, s: value(p, s)

array = grp(tok('['), cut, rep(value, d=tok(',')), tok(']'))
member = grp(string, tok(':'), value)
obj = grp(tok('{'), cut, rep(member, d=tok(',')), tok('}'), map=dict)
value = alt(number, string, true, false, null, obj, array)
json = seq(ws, alt(obj, array))


def test():
    x = '{ "Object":{"Zoom": false, "Property1":{"Property2":' \
        '{"Color":[0,153,255,-0]},"Width":40}} }'
    y = {'Object': {'Zoom': False, 'Property1': {'Property2': {'Color':
         (0.0, 153.0, 255.0, -0.0)}, 'Width': 40.0}}}
    p, s = Peco(x).parse(json)
    assert s and s.stk.v == y
