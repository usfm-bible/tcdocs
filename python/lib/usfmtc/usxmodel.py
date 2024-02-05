
import re

# This should be read from usx.rng
allpartypes = {
    'Section': """ms mse ms1 ms2 ms2e ms3 ms3e mr s s1 s2 s3 s4 s1e s2e s3e s4e sr r sp
                    sd sd1 sd2 sd3 sd4 periph iex ip mte mte1 mte2 cl cd""",
    'NonVerse': """lit cp pb p1 p2 k1 k2 rem sts"""
}

partypes = {e: k for k, v in allpartypes.items() for e in v.split()}

def _addvids(lastp, endp, base, v, endv, atend=False):
    res = lastp
    lastp = lastp.getnext()
    pending = []
    while lastp is not None:
        if lastp.tag == "chapter":
            break
        if lastp.tag not in ('para', 'table', 'row'):
            if id(lastp) == id(endp):
                break
            lastp = lastp.getnext()
            continue
        if lastp.tag == 'para' and partypes.get(lastp.get('style', None), None) in ("Section", "NonVerse") \
                or (not len(lastp) and (lastp.text is None or lastp.text.strip() == "")):
            pending.append(lastp)
        elif id(lastp) != id(endp) or atend or endp[0].tag != "verse" or (endp.text is not None and endp.text.strip() != ""):
            for p in pending:
                p.set('vid', v)
            pending = []
            lastp.set('vid', v)
            res = lastp
        if id(lastp) == id(endp):
            break
        lastp = lastp.getnext()
    if id(res) == id(endp) and base is not None:
        base.addprevious(endv)
    elif res.tag == "table":
        if len(res):
            res[-1][-1].append(endv)
    else:
        res.append(endv)
    return res

def addesids(root):
    lastv = None
    if root.get('version', None) is None:
        root.set('version', '3.0')
    bkel = root.find('./book')
    bk = bkel.get('code', 'UNK').upper()
    bkel.set('code', bk)
    currchap = 0
    lastp = None
    for v in list(root.iter()):
        if v.tag == "chapter":
            currchap = v.get('number')
            currverse = 0
            v.set('sid', "{} {}".format(bk, currchap))
            continue
        elif v.tag == "para":
            lastp = v
            continue
        elif v.tag != "verse" or v.get('eid', None) is not None:
            continue
        currverse = v.get('number')
        v.set('sid', "{} {}:{}".format(bk, currchap, currverse))
        if lastv is None:
            lastv = v
            continue
        eid = lastv.get('sid', None)
        ev = v.makeelement('verse', {'eid': eid or ""})
        pv = v.getparent()
        pl = lastv.getparent()
        if id(pv) == id(pl):
            v.addprevious(ev) 
        else:
            endp = _addvids(pl, pv, v, eid, ev)
        lastv = v
    if lastv is not None and lastp is not None:
        eid = lastv.get('sid', None)
        ev = lastv.makeelement('verse', {'eid': eid or ''})
        _addvids(lastv.getparent(), lastp, None, eid, ev, atend=True)

    lastc = None
    for c in root.findall('.//chapter'):
        if lastc is not None:
            cel = c.makeelement('chapter', {'eid': lastc.get('sid', '')})
            c.addprevious(cel)
        lastc = c
    if lastc is not None:
        root.append(lastc.makeelement('chapter', {'eid': lastc.get('sid', '')}))

    return root

aligns = { "": "start", "r": "end", "c": "center" }
def cell_aligns(root):
    for e in root.findall('.//cell'):
        if e.get('align', None) is not None:
            continue
        s = e.get('style', None)
        if s is None:
            continue
        v = re.match(r"^t[ch](.?)\d+", s)
        if v is None:
            continue
        a = aligns[v.group(1)]
        e.set('align', a)

def add_specials(t, node, parent, istext=False):
    t = re.sub(r"\\(.)", r"\1", t)      # remove escape markers
    if "~" in t:
        t = t.replace("~", "\u00A0")
    if "//" in t:
        j = t.index("//")
        bk = parent.makeelement("optbreak", {})
        for i, c in enumerate(parent):
            if id(c) == id(node):
                if istext:
                    node.append(bk)
                else:
                    parent.insert(i+1, bk)
                bk.tail = t[j+2:]
                return t[:j]
    return t
                
def cleanup(node, parent=None):
    if node.tag == 'para':
        i = -1
        if len(node) and node[i].tag == 'verse' and node[i].get('eid', None) is not None:
            i -= 1
        if len(node) >= -i:
            if node[i].tail is not None:
                node[i].tail = node[i].tail.rstrip()
                node[i].tail = add_specials(node[i].tail, node, parent)
        elif node.text is not None:
            node.text = re.sub(r"^[ \t\n]*(.*?)[ \t\n]*$", r"\1", node.text)
            node.text = add_specials(node.text, node, parent, istext=True)
    elif node.tag in ('chapter', 'verse'):
        node.text = None
    elif node.tag == "figure":
        src = node.get("src", None)
        if src is not None:
            del node.attrib['src']
            node.set('file', src)
    for k, v in node.attrib.items():
        node.attrib[k] = re.sub(r"\\(.)", r"\1", v)
    for c in node:
        cleanup(c, parent=node)

unescapes = {
    "&amp;": '&',
    "&lt;": '<',
    "&gt;": '>',
    "&quot;": '"',
    "&apos;": "'"
}

def strnormal(s, t, mode=0):
    ''' strips whitespace according to element type and mode:
        mode & 1 strips lhs
        mode & 2 strips rhs
    '''
    if s is None:
        return ""
    if not len(s.lstrip()):
        return ""
    res = re.sub("[\n\s]+", " ", s) if t in ('para', 'char') else s
    if mode & 1 == 1:
        res = res.lstrip()
    if mode & 2 == 2:
        res = res.rstrip()
    res = re.sub(r"[ \n]*\n[ ]*", "\n", res)
    for k, v in unescapes.items():
        if k in res:
            res = res.replace(k, v)
    return res

def attribnorm(d):
    banned = ('closed', 'status')
    return {k: strnormal(v, None) for k, v in d.items() if k not in banned and not k.startswith(" ")}

def etCmp(a, b, at=None, bt=None, verbose=False, endofpara=False):
    aattrib = attribnorm(a.attrib)
    battrib = attribnorm(b.attrib)
    if a.tag != b.tag or aattrib != battrib:
        if verbose:
            print("tag or attribute: ", a, aattrib, b, battrib)
        return False
    mode = 1 if len(a) else 3
    if strnormal(a.text, a.tag, mode) != strnormal(b.text, b.tag, mode):
        if verbose:
            print("text or tag: ", a.text, a.tag, b, b.tag)
        return False
    if len(a) != len(b):
        if verbose:
            print("length mismatch: ", len(a), len(b))
            if len(a) > len(b):
                print("first item in a not in b: ", a[len(b)])
            else:
                print("first item in b not in a: ", b[len(a)])
        return False
    lasti = 0
    for lasti, e in enumerate(reversed(a)):
        if a.tag not in ('char', 'note'):
            break
    lasti = len(a) - 1 - lasti
    for i, (ac, bc) in enumerate(zip(a, b)):
        act = a.tag if a is not None else None
        bct = b.tag if b is not None else None
        eop = a.tag == 'para' or endofpara and (i == lasti) 
        if not etCmp(ac, bc, act, bct, verbose=verbose, endofpara=eop):
            if verbose:
                print("child mismatch {}, {} [{}]: ".format(str(ac), str(bc), i))
            return False
        mode = 2 if eop or a.tag != "char" else 0
        if strnormal(ac.tail, act, mode) != strnormal(bc.tail, bct, mode):
            if verbose:
                print("tail or attributes: \"{}\", \"{}\" (at end of para={})".format(strnormal(ac.tail, act, mode), strnormal(bc.tail, bct, mode), str(eop)))
            return False
    return True


