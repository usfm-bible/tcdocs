
import re
from dataclasses import dataclass
from usfmtc.xmlutils import isempty
import xml.etree.ElementTree as et

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
    if bkel is None:
        return
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

escapes = {
    '\\' : '\\',
    'n': '\n'
}

def add_specials(t, node, parent, istext=False):
    t = re.sub(r'\\(.)', lambda m: escapes.get(m.group(1), "\\"+m.group(1)), t)
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

alignments = {
    "c": "start", "cc": "centre", "cr": "end",
    "h": "start", "hc": "centre", "hr": "end"
}
def cleanup(node, parent=None):
    if node.tag == 'para':
        # cleanup specials and spaces
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
    elif node.tag == "cell":
        s = node.get("style", "")
        if "-" in s:
            start, end = s.split("-")
            startn = int(re.sub(r"^\D+", "", start))
            endn = int(end)
            span = endn - startn + 1
            node.set("colspan", str(span))
            node.set("style", start)
        celltype = re.sub(r"^t(.*?)\d.*$", r"\1", s)
        node.set("align", alignments.get(celltype, "start"))
    elif node.tag == "char":
        if node.get('style', '') == "xt" and ('href' in node.attrib or 'link-href' in node.attrib) \
                and (len(node) != 1 or node.text is not None or node[0].tag != 'ref'):
            refnode = et.Element('ref', loc=node.get('href', node.get('link-href', '')), gen="true")
            refnode.text = node.text
            refnode[:] = node[:]
            node[:] = [refnode]
            node.text = None
            node = refnode
    for k, v in node.attrib.items():
        node.attrib[k] = re.sub(r"\\(.)", r"\1", v)
    for c in node:
        cleanup(c, parent=node)

def protect(txt):
    if txt is not None:
        return re.sub(r'(["=|\\~/])', r'\\\1', txt)
    return None

def messup(node, parent=None):
    ''' Opposite of cleanup, to prepare a USX XML structure for USFM generation.
        Returns a copy of the structure so as not to polute the core data. '''
    if parent is None:
        newnode = et.Element(node.tag, attrib=node.attrib)
    else:
        newnode = et.SubElement(parent, node.tag, attrib=node.attrib)
    newnode.text = protect(node.text)
    newnode.tail = protect(node.tail)

    if newnode.tag == "figure":
        src = newnode.get("file", None)
        if src is not None:
            del newnode.attrib['file']
            newnode.set('src', src)
    elif newnode.tag == "cell":
        tag = newnode.get("style", "")
        span = int(newnode.get("colspan", "1"))
        if span > 1:
            start = int(re.sub(r"^\D+", "", tag))
            tag = tag + "-" + str(start + span - 1)
            newnode.set("style", tag)
    # convert \xt\ref Genesis 1:1|loc="GEN 1:1"\ref*|link-href="GEN 1:1"\xt*
    # back to \xt Genesis 1:1|link-href="GEN 1:1"\xt*
    elif newnode.tag == "char" and node.get('style', '').endswith('xt') and not newnode.text and len(node) == 1:
        c = node[0]
        if c.tag == "ref" and not c.tail:
            newnode.text = protect(c.text)
            return newnode
    for k, v in newnode.attrib.items():
        newnode.attrib[k] = protect(v)
    for c in node:
        messup(c, parent=newnode)
    return newnode


unescapes = {
    "&amp;": '&',
    "&lt;": '<',
    "&gt;": '>',
    "&quot;": '"',      #'
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
    res = re.sub("[\n\\s]+", " ", s) if t in ('para', 'char') else s
    if mode & 1 == 1:
        res = res.lstrip()
    if mode & 2 == 2:
        res = res.rstrip()
    res = re.sub(r"[ \n]*\n[ ]*", "\n", res)
    for k, v in unescapes.items():
        if k in res:
            res = res.replace(k, v)
    return res

def canonicalise(node, endofpara=False, factory=et):
    if node.text is not None:
        mode = 1 if len(node) else 3
        node.text = strnormal(node.text, node.tag, mode)
    lasti = 0
    for lasti, e in enumerate(reversed(node)):
        if e.tag not in ('char', 'note'):
            break
    lasti = len(node) - 1 - lasti
    for i, c in enumerate(node):
        eop = c.tag == 'para' or (endofpara and (i == lasti))
        canonicalise(c, endofpara=eop)
        if c.tail is not None:
            mode = 2 if eop or c.tag != "char" else 0
            c.tail = strnormal(c.tail, c.tag, mode)
    if node.tag == "note":
        style = node.get("style", "")
        replace = "xt" if style in ("x", "ex") else "ft"
        if node.text is not None:
            ft = node.makeelement("char", {"style": replace})
            ft.text = node.text
            node.text = None
            node.insert(0, ft)
        inserted = 0
        for i, c in enumerate(list(node)):
            if c.tail is not None:
                ft = node.makeelement("char", {"style": replace})
                node.insert(i + inserted + 1, ft)
                inserted += 1
                ft.text = c.tail
                c.tail = None

def attribnorm(d):
    banned = ('closed', 'status', 'vid', 'version')
    return {k: strnormal(v, None) for k, v in d.items() if k not in banned and not k.startswith(" ") and v is not None and len(v)}

def listWithoutChapterVerseEnds(node):
    nodeList = []
    for child in node:
        if (child.tag != "verse" and child.tag != "chapter") or child.get("eid") is None:
            nodeList.append(child)
    return nodeList

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
            print("text or tag: ", a.text, a.tag, b.text, b.tag)
        return False
    lista = listWithoutChapterVerseEnds(a)
    listb = listWithoutChapterVerseEnds(b)
    if len(lista) != len(listb):
        if verbose:
            print("length mismatch: ", len(lista), len(listb))
            commonIndex = min(len(lista), len(listb)) - 1
            if commonIndex >= 0:
                print(f'item {commonIndex} in a: {lista[commonIndex]}')
                print(f'item {commonIndex} in b: {listb[commonIndex]}')
            if len(lista) > len(listb):
                print("first item in a not in b: ", lista[len(listb)])
            else:
                print("first item in b not in a: ", listb[len(lista)])
        return False
    lasti = 0
    for lasti, e in enumerate(reversed(lista)):
        if e.tag not in ('char', 'note'):
            break
    lasti = len(lista) - 1 - lasti
    for i, (ac, bc) in enumerate(zip(lista, listb)):
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

@dataclass
class USXLoc:
    el: et.Element
    attrib: str     # " text", " tail". Where the .char indexes into
    char: int       

def findel(node, tag, attrib, limits=[]):
    """ Search for an element with the given tag and attrib matching forwards from
        node, including down into children. Returns a node. Limits is a list of stop
        tags that cause the search to fail, returning None. """
    try:
        res = _findelchild(node, tag, attrib, limits)
    except StopIteration:
        return None
    if res is not None:
        return res
    start = list(node.parent).index(node)
    for i in range(start + 1, len(node.parent)):
        try:
            res = _findelchild(c, tag, attrib, limits)
        except StopIteration:
            return None
        if res is not None:
            return res
    return None

def _findelchild(node, tag, attrib, limits=[]):
    """ Recursively search for a node with given tag and attributes returning the node
        on success or None. Limits is a list of stop tags, which if encountered trigger
        a StopIteration exception. """
    if node.tag == tag:
        for k, v in attrib.items():
            if node.get(k, None) != v:
                break
        else:
            return node
    elif node.tag in limits:
        raise StopIteration("Hit the stop")
    for c in node:
        res = _findelchild(node, tag, attrib, limits)
        if res is not None:
            return res
    return None

def findtext(node, limits):
    """ Iterator returning text strings until an element in limits is encountered """
    yield from _findtextchild(node, limits)

def _findtextchild(node, limits):
    """ Recursively iterates returning text strings between elements until an element
        in limits is encountered."""
    if not isempty(node.text):
        yield (node.text, node, " text")
    for c in node:
        if c.tag in limits:
            return
        yield from _findtextchild(c, limits)
        if not isempty(c.tail):
            yield (c.tail, c, " tail")

    
def findref(ref, root, atend=False, parindex=0):
    """ From a reference, return a USXLoc (element, attribute and char index) """
    if ref.book:
        bk = root.findtext("./book/@code")
        if bk != ref.book:
            raise ValueError("Reference book {} != text book {}".format(ref, bk))
    if ref.chapter is not None and ref.chapter > 0:
        for pari, el in enumerate(root[parindex:], start=parindex):
            if el.tag == "chapter" and el.get('number', 0) == ref.chapter:
                parindex = pari
                break
        else:
            raise ValueError("Chapter reference {} out of range".format(ref))
    if parindex < len(root) - 1 and ref.verse is not None and ref.verse > 0:
        el = findel(root[parindex+1:], "verse", {"number": ref.verse}, limits=("chapter",))
        if el is None:
            raise ValueError("Reference verse {} out of range".format(ref))
    a = ""
    w = -1
    c = -1
    clen = -1
    t = ""
    if ref.word is not None or ref.char is not None:
        if ref.word is None or ref.word == 0:
            t = str(el.get('number', ""))
            a = "number"
            c = 0
            clen = len(t)
        else:
            word = ref.word
            for t, el, a in findtext(el, limits=("chapter", "verse")):
                b = reg.split("([\u0020\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000]+)", t)
                l = (len(b) + 1) // 2
                if not len(b[0]):
                    l -= 1
                if l < word:
                    word -= l
                    continue
                c = sum(len(s) for s in b[:word*2])
                clen = len(b[word*2])
                break
            else:
                raise ValueError("Reference word {} out of range".format(ref))
        if ref.char is not None:
            if ref.char > clen:
                raise ValueError("Reference char {} out of range for word length {}".format(ref, clen))
            c += ref.char
        elif atend:
            c += clen
    elif atend:
        # find end of verse or chapter
        pass
    res = USXLoc(el, a, c)
    # handle mrkrs
    return res

def copy_range(root, a, b):
    """ Create a new tree from a starting USXloc to an ending one. """
    factory = cls(root)
    pstack = []
    t = a.el
    while t is not None:
        pstack.append(t)
        t = t.parent
    t = pstack.pop()                            # usx
    res = factory(t.tag, attrib=t.attrib)
    p = pstack.pop()                            # paragraph
    curri = list(t).index(p)
    if a.el.tag != "chapter":
        for i in range(curri-1, -1, -1):
            if t[curri].tag == "chapter":
                c = factory("chapter", attrib=t[curri].attrib, parent=t)
                res.append(c)
                break
    curr = factory(p.tag, attrib=p.attrib, parent=t)
    res.append(curr)
    for c in reversed(pstack):
        n = factory(el.tag, attrib=el.attrib, parent=curr)
        curr.append(n)
        curr = n

    # we have a copied tree down to the first ref element
    hit = False
    if a.attrib == " text":
        if id(b.el) == id(a.el) and b.attrib == " text":
            curr.text = a.el.tex[a.char:b.char+1]
            return res
        curr.text = a.el.text[a.char:]
    if a.attrib != " tail":
        hit = _copy_downto(curr, a.el, b, factory)
    else:
        if id(b.el) == id(a.el) and b.attrib == " tail":
            curr.tail = a.el.tail[a.char:b.char+1]
            return res
        curr.tail = a.el.tail[a.char:]
    if not hit:
        _copy_upto(curr, a, b)
    return res

def _copy_downto(curr, el, b, factory):
    """ Copies as much of el into curr until it hits b, or everything """
    n = factory(el.tag, el.attrib, parent=curr)
    curr.append(n)
    if b.attrib == " text" and id(el) == id(b.el):
        n.text = el.text[:b.char+1]
        return True
    else:
        n.text = el.text
    for c in el:
        if _copy_downto(n, c, b, factory):
            return True
    if b.attrib == " tail" and id(el) == id(b.el):
        n.tail = el.tail[:b.char+1]
        return True
    else:
        n.tail = el.tail
    return False

def _copy_upto(curr, el, a, b, factory):
    """ Copy from the parent into curr going down each of its children until it hits b.
        Keep going up until we eventually hit b or the end of the world. """
    p = el.parent
    if p is None:
        raise ValueError("Reference {} not found".format(b))
    pi = list(p).index(el)
    cp = curr.parent
    for e in list(p)[pi+1:]:
        if _copy_downto(cp, e, b, factory):
            return True
    return _copy_upto(cp, p, a, b, factory)
