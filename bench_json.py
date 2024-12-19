from peco import *
import json

mknum = to(lambda x: float(x))

ws = eat(r'\s*')
scan = lambda f: seq(ws, f)
skip = lambda c: scan(eat(c))

number = seq(push(eat(r'-?([1-9]\d*|0)(\.\d+)?((e|E)[-+]?\d+)?')), mknum)

value = lambda s: value(s)

array = group(seq(skip(r'\['), opt(list_of(value, skip(','))), skip(']')))
value = alt(scan(number), array)
jsonp = seq(array, ws)


def main():
    v = tuple(tuple(range(10)) for _ in range(100))
    #v = tuple(tuple(range(3)) for _ in range(3))
    x = json.dumps(v)
    for _ in range(2000):
        s = parse(x, jsonp)
    assert s.ok and s.stack[0] == v

main()
