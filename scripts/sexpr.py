"""Generate the TFT carrier schematic: symbols from the stock KiCad libraries,
one local label per pin (net names), no wires. Usage: gen_sch.py OUT.kicad_sch"""
import sys, uuid, math

LIB = "/usr/share/kicad/symbols/"


def parse(s):
    toks, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in "()":
            toks.append(c); i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j = i + 1; buf = []
            while s[j] != '"':
                if s[j] == "\\": buf.append(s[j:j+2]); j += 2
                else: buf.append(s[j]); j += 1
            toks.append('"' + "".join(buf) + '"'); i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in "()": j += 1
            toks.append(s[i:j]); i = j
    stack = [[]]
    for t in toks:
        if t == "(": stack.append([])
        elif t == ")": x = stack.pop(); stack[-1].append(x)
        else: stack[-1].append(t)
    return stack[0][0]


def dump(x, ind=0):
    if not isinstance(x, list): return x
    if all(not isinstance(e, list) for e in x):
        return "(" + " ".join(x) + ")"
    out = "(" + " ".join(e for e in x if not isinstance(e, list) and x.index(e) == 0)
    parts = []
    head = []
    for e in x:
        if isinstance(e, list): break
        head.append(e)
    out = "(" + " ".join(head)
    for e in x[len(head):]:
        out += "\n" + "\t" * (ind + 1) + (dump(e, ind + 1) if isinstance(e, list) else e)
    return out + "\n" + "\t" * ind + ")"


_libs = {}
def libsym(lib, name):
    if lib not in _libs: _libs[lib] = parse(open(LIB + lib + ".kicad_sym").read())
    for e in _libs[lib]:
        if isinstance(e, list) and e[0] == "symbol" and e[1] == f'"{name}"':
            return e
    raise KeyError(name)


def pins(sym):
    out = {}
    def walk(x):
        for e in x:
            if isinstance(e, list):
                if e[0] == "pin":
                    at = next(a for a in e if isinstance(a, list) and a[0] == "at")
                    num = next(a for a in e if isinstance(a, list) and a[0] == "number")[1].strip('"')
                    ln = float(next(a for a in e if isinstance(a, list) and a[0] == "length")[1])
                    out[num] = (float(at[1]), float(at[2]), float(at[3]), ln)
                else:
                    walk(e)
    walk(sym)
    return out


U = lambda: f'"{uuid.uuid4()}"'
ROOT = str(uuid.uuid4())

