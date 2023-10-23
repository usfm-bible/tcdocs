
import re

allpartypes = {
    'Section': """ms mse ms1 ms2 ms2e ms3 ms3e mr s s1 s2 s3 s4 s1e s2e s3e s4e sr r sp
                    sd1 sd2 sd3 sd4 periph iex"""
}

partypes = {e: k for k, v in allpartypes.items() for e in v.split()}

def addvids(lastp, endp, base, v, endv, atend=False):
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
        if lastp.tag == 'para' and partypes.get(lastp.get('style', None), None) == "Section" \
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
            res[-1].append(endv)
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
        pv = v.parent
        pl = lastv.parent
        if id(pv) == id(pl):
            v.addprevious(ev) 
        else:
            endp = addvids(pl, pv, v, eid, ev)
        lastv = v
    if lastv is not None and lastp is not None:
        eid = lastv.get('sid', None)
        ev = lastv.makeelement('verse', {'eid': eid or ''})
        addvids(lastv.parent, lastp, None, eid, ev, atend=True)

    lastc = None
    for c in root.findall('.//chapter'):
        if lastc is not None:
            cel = c.makeelement('chapter', {'eid': lastc.get('sid', '')})
            c.addprevious(cel)
        lastc = c
    if lastc is not None:
        root.append(lastc.makeelement('chapter', {'eid': lastc.get('sid', '')}))

    if 0:
        for r in root.findall('.//row'):
            p = r.getprevious()
            if r.parent is not None and r.parent.tag == "table":
                continue
            if p is not None and p.tag == 'table':
                i, oldp = r.getindex()
                p.append(r)
                oldp.remove(r)
                r.parent = p
            else:
                # there's a bug here, surely newp is never attached
                i, oldp = r.getindex()
                newp = r.makeelement('table', {})
                oldp.remove(r)
                oldp.insert(i, newp)
                r.parent = newp
            newp.parent = oldp
            newp.append(r)
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

def cleanup(node):
    if node.tag == 'para':
        i = -1
        if len(node) and node[i].tag == 'verse' and node[i].get('eid', None) is not None:
            i -= 1
        if len(node) >= -i:
            if node[i].tail is not None:
                node[i].tail = node[i].tail.rstrip()
        elif node.text is not None:
            node.text = re.sub(r"^[ \t\n]*(.*?)[ \t\n]*$", r"\1", node.text)
    elif node.tag in ('chapter', 'verse'):
        node.text = None
    elif node.tag == "figure":
        src = node.get("src", None)
        if src is not None:
            del node.attrib['src']
            node.set('file', src)
    for c in node:
        cleanup(c)

def strnormal(s, t):
    if s is None:
        return ""
    if not len(s.strip()):
        return ""
    if t in ('para', 'char'):
        return re.sub("[\n\s]+", " ", s)
    else:
        return s.strip()

def attribnorm(d):
    banned = ('closed', 'status')
    return {k:v for k, v in d.items() if k not in banned and not k.startswith(" ")}

def etCmp(a, b, at=None, bt=None, verbose=False):
    aattrib = attribnorm(a.attrib)
    battrib = attribnorm(b.attrib)
    if a.tag != b.tag or aattrib != battrib:
        if verbose:
            print("tag or attribute: ", a, aattrib, b, battrib)
        return False
    if strnormal(a.text, a.tag) != strnormal(b.text, b.tag):
        if verbose:
            print("text or tag: ", a.text, a.tag, b, b.tag)
        return False
    if strnormal(a.tail, at) != strnormal(b.tail, bt):
        if verbose:
            print("tail or attributes: ", strnormal(a.tail, at), strnormal(b.tail, bt))
        return False
    if len(a) != len(b):
        if verbose:
            print("length mismatch: ", len(a), len(b))
            if len(a) > len(b):
                print("first item in a not in b: ", a[len(b)])
            else:
                print("first item in b not in a: ", b[len(a)])
        return False
    for ac, bc in zip(a, b):
        if not etCmp(ac, bc, a.tag if a is not None else None, b.tag if b is not None else None, verbose=verbose):
            if verbose:
                print("child mismatch: ", ac, bc)
            return False
    return True


