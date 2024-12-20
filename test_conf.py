from peco2 import *

ws = rep(r'/\s+|#.+')
tok = lambda *f: seq(ws, *f)

num = tok(put(r'/[-+]?\d+', map=float))
string = tok('"',put(r'/[^"]*'),'"')
name = tok(put(r'/[_a-zA-Z][_a-zA-Z0-9]*'))

val = lambda p, s: val(p, s)
array = seq(tok('['), cut, grp(rep(val), map=list), tok(']'))
item = grp(name, tok('='), val)
obj = seq(tok('{'), cut, grp(rep(item),map=dict), tok('}'))
val = alt(num, string, array, obj)

main = seq(grp(rep(item), map=dict), ws, eof)


def test():
    src = '''
    # comment
    vm = {
        ip = [192 168 44 44]
        memory = 1024
        synced_folders = [{
            host_path = "data/"
            guest_path = "/var/www"
            type = "default"
        }]
    }
    log = "conf.log"
    '''
    obj = {'vm': {'ip': [192.0, 168.0, 44.0, 44.0], 'memory': 1024.0,
           'synced_folders': [{'host_path': 'data/', 'guest_path': '/var/www',
           'type': 'default'}]}, 'log': 'conf.log'}
    _, s = Peco(src).parse(main)
    assert s and s.stk.v == obj
