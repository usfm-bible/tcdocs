#!/usr/bin/env python3

import regex
import xml.etree.ElementTree as et

class Tag(str):
    def __new__(cls, s):
        isend = False
        isplus = False
        if s.startswith("+"):
            isplus = True
            s = s[1:]
        if s.endswith("*"):
            isend = True
            s = s[:-1]
        res = super().__new__(cls, s)
        res.isplus = isplus
        res.isend = isend
        return res

    def __init__(self, s):
        self.isplus = getattr(self, 'isplus', False)
        self.isend = getattr(self, 'isend', False)

    def __repr__(self):
        return "Tag("+str(self)+")"

    def __str__(self):
        res = "+" if self.isplus else ""
        res += super().__str__()
        res += "*" if self.isend else ""
        return res

    def basestr(self):
        return super().__str__()

    def setpos(self, pos):
        self.pos = pos

class AttribText(str):
    pass

class OptBreak:

    def __repr__(self):
        return "OptBreak(" + str(self) + ")"
    def __str__(self):
        return "//"

class Lexer:

    tokenre = regex.compile(r'((?:[^\\|/]|\\[\\|\n]|/[^/])+)|([\\|\n]|//)')
    tagre = regex.compile(r'(?:\+?[a-zA-Z_][a-zA-Z_0-9-]*)?\*?')
    attribsre = regex.compile(r'([a-zA-Z_][a-zA-Z0-9_-]*)\s*=\s*"((?:[^"]|\\")*)"')
    textrunre = regex.compile(r'(?:[^\\]|\\[^a-zA-Z_*])*')

    def __init__(self, txt):
        self.txt = txt

    def __iter__(self):
        self.nexts = []
        self.cindex = 0
        return self

    def __next__(self):
        if len(self.nexts):
            return self.nexts.pop(0)
        curri = self.cindex
        res = ""
        lastres = None
        while (m := self.tokenre.match(self.txt, pos=curri)):
            curri = m.end()
            if m.group(1):
                res += m.group(1)
                continue
            else:
                lastres = res
            n = m.group(2)
            if n == "\n":
                res += n
                continue
            elif n == "\\":
                t = self.tagre.match(self.txt[m.end():])
                if not t:
                    res += self.txt[m.end()]
                    curri = m.end() + 1
                    continue
                else:
                    res = Tag(t.group(0))
                    curri += t.end()
                    break
            elif n == '|':
                t, curri = self.readAttrib(curri)
                if isinstance(t, str):
                    res = AttribText(t)
                elif len(t):
                    res = t
                else:
                    res = ""
                    continue
                break
            elif n == '//':
                res = OptBreak()
                break
        if self.cindex == curri:
            raise StopIteration
        if lastres:
            self.nexts.append(res)
            res = lastres
        self.cindex = curri
        return res

    def readAttrib(self, curri):
        res = {}
        resi = curri
        for m in self.attribsre.finditer(self.txt[curri:]):
            res[m.group(1)] = m.group(2)
            resi = m.end()
        if not len(res):
            m = self.textrunre.match(self.txt[curri:])
            if m:
                resi = m.end()
                res = m.group(0).strip()
        return res, resi + curri

category_markers = {
    "attrib": "cp vp usfm ca va cat",
    "cell": "th1 th2 th3 th4 th5 th6 th7 th8 th9 th10 th11 th12 tc1 tc2 tc3 tc4 tc5 tc6 tc7 tc8 tc9 tc10 tc11 tc12 tcr1 tcr2 tcr3 tcr4 tcr5 tcr6 tcr7 tcr8 tcr9 tcc1 tcc2 tcc3 tcc4 tcc5 tcc6 tcc7 tcc8 tcc9 tcc10 tcc11 tcc12 thc1 thc2 thc3 thc4 thc5 thc6 thc7 thc8 thc9 thc10 thc11 tch12 thr1 thr2 thr3 thr4 thr5 thr6 thr7 thr8 thr9 thr10 thr11 thr12",
    "char": "qac qs add addpn bk dc efm fm fv k nd ndx ord png pn pro qt rq sig sls tl wg wh wa wj jmp no it bdit bd em sc sup w rb",
    "crossreference": "ex x",
    "crossreferencechar": "xt xop xo xta xk xq xot xnt xdc",
    "footnote": "fe f efe ef",
    "footnotechar": "fr ft fk fqa fq fl fw fdc fp",
    "header": "ide h1 h2 h3 h toc1 toc2 toc3 toca1 toca2 toca3",
    "internal": "id periph v fig esb esbe",
    "chapter": "c",
    "introchar": "ior iqt",
    "introduction": "imt1 imt2 imt3 imt4 imte1 imte2 imte imt ib ie ili1 ili2 ili imi imq im io1 io2 io3 io4 iot io ipi ipq ipr iq1 iq2 iq3 iq is1 is2 is",
    "list": "lh li1 li2 li3 li4 lim1 lim2 lim3 lim4 lim li lf",
    "listchar": "litl lik liv1 liv2 liv3 liv4 liv5 liv",
    "milestone": "ts-s ts-e ts t-s t-e qt1-s qt1-e qt2-s qt2-e qt3-s qt3-e qt4-s qt4-e qt5-s qt5-e qt-s qt-e",
    "otherpara": "rem sts lit pb p1 p2 qa k1 k2",
    "sectionpara": "ip iex restore ms1 ms2 ms3 ms mr mte1 mte2 mte r s1 s2 s3 s4 sr sp sd1 sd2 sd3 sd4 sd s cl cd",
    "title": "mt1 mt2 mt3 mt4 mt",
    "versepara": "cls nb pc pi1 pi2 pi3 pi po pr pmo pmc pmr pm ph1 ph2 ph3 ph p q1 q2 q3 q4 qc qr qm1 qm2 qm3 qm qd q b d mi1 mi2 mi3 mi4 mi m",
}

marker_categories = {t:k for k, v in category_markers.items() for t in v.split(' ')}

attribmap = { 'jmp' : 'href', 'k' : 'key', 'qt-s': 'who', 'qt1-s': 'who', 'qt2-s': 'who',
    'qt3-s': 'who', 'qt4-s': 'who', 'qt5-s': 'who', 'rb': 'gloss', 't-s': 'sid', 'ts-s': 'sid',
    'w': 'lemma' }

attribtags = { 'cp': 'pubnumber', 'ca': 'altnumber', 'vp': 'pubnumber',
    'va': 'altnumber', 'cat': 'category', 'usfm': 'version' }

class Node:
    def __init__(self, parser, usxtag, tag):
        self.parser = parser
        self.tag = tag
        parent = parser.stack[-1] if len(parser.stack) else None
        self.element = parser.factory(usxtag, {} if tag is None else {"style": tag},
                    parent=getattr(parent, 'element', None))
        if parent:
            parent.addNodeElement(self.element)
        self.attribnodes = []

    def addNodeElement(self, e):
        self.element.append(e)

    def appendElement(self, child):
        if isinstance(child, OptBreak):
            c = self.parser.factory("optbreak", {}, parent=self.element)
            self.element.append(c)
        self.clearAttribNodes()

    def appendText(self, txt):
        if len(self.element):
            if self.element[-1].tail is None or self.element[-1].tail == "":
                self.element[-1].tail = txt.lstrip() if self.element.text is None or self.element.text == "" else txt
            else:
                self.element[-1].tail += txt
        elif self.element.text is None or self.element.text == "":
            self.element.text = txt.lstrip()
        else:
            self.element.text += txt
        self.clearAttribNodes()

    def addAttributes(self, d):
        self.element.attrib.update(d)
        self.clearAttribNodes()

    def addDefaultAttrib(self, t):
        defattrib = attribmap.get(self.tag, None)
        if defattrib is None and self.tag.endswith("-e"):
            defattrib = 'eid'
        if defattrib is None:
            defattrib = "_unknown_"
        self.element.set(defattrib, t)
        self.clearAttribNodes()

    def addAttribNode(self, node):
        self.attribnodes.append(self)

    def clearAttribNodes(self):
        if not len(self.attribnodes):
            return
        for n in self.attribnodes:
            self.parser.removeParser(n)
        self.attribnodes = []

    def isEmpty(self):
        if not len(self) and self.text is None:
            return True
        return False

    def close(self):
        if getattr(self, 'element', None) is None:
            return
        if len(self.element):
            if self.element[-1].tail is not None:
                self.element[-1].tail = self.element[-1].tail.rstrip()
        elif self.element.text is not None:
            self.element.text = self.element.text.rstrip()
        self.clearAttribNodes()
        
class IdNode(Node):
    def appendText(self, t):
        m = regex.match(r"\s*(\S{3})\s+(.*?)(?:\n|$)", t)
        if m:
            self.element.set('code', m.group(1))
            self.element.text = m.group(2)
        self.parser.removeTag('id')

class USXNode(Node):
    def appendText(self, t):
        self.element.set('version', t.strip())

class AttribNode(Node):
    def __init__(self, parser, parent, tag):
        self.parent = parent
        self.parent.addAttribNode(self)
        self.tag = tag

    def addNodeElement(self, e):
        self.parent.addNodeElement(e)

    def appendText(self, t):
        attrib = attribtags[self.tag]
        self.parent.element.set(attrib, t.strip())

class NumberNode(Node):
    def __init__(self, parser, usxtag, tag):
        super().__init__(parser, usxtag, tag)
        self.hasarg = False

    def appendText(self, t):
        if not self.hasarg:
            b = t.lstrip().split(' ', 1)
            self.element.set('number', b[0].strip())
            self.hasarg = True
        else:
            b = ['', t]
        if len(b) > 1 and b[1].strip():
            self.parser.removeTag(self.tag)
            self.parser.stack[-1].appendText(b[1])

    def addNodeElement(self, e):
        self.parser.removeTag(self.tag)
        self.parser.stack[-1].addNodeElement(e)

class NoteNode(Node):
    def __init__(self, parser, usxtag, tag):
        super().__init__(parser, usxtag, tag)
        self.hascaller = False

    def appendText(self, t):
        if self.hascaller:
            super().appendText(t)
        self.element.set('caller', t.strip())
        self.hascaller = True

class PeriphNode(Node):
    def appendText(self, t):
        m = regex.match(r"^\s*(.*?)\s*(?:|\s*(.*?)\s*)$", t)
        if m:
            self.element.set('alt', m.group(1))
            if m.group(2):
                self.element.set('id', m.group(2))


paratypes = ('header', 'introduction', 'list', 'otherpara', 'sectionpara', 'versepara', 'title', 'chapter')
def setupParser(cls):
    # tag closed types
    for a in (('introchar', 'char'), ('listchar', 'char'), ('char', 'char'), ('milestone', 'ms'), ):
        def maketype(c, t):
            def dotype(self, tag):
                if tag.isend:
                    return self.removeTag(str(tag))
                return self.addNode(Node(self, c, str(tag)))
            return dotype
        setattr(cls, a[0], maketype(*a))
    # implicit closed paras
    for a in paratypes:
        def dotype(self, tag):
            self.removeType(paratypes)
            return self.addNode(Node(self, 'para', str(tag)))
        if not hasattr(cls, a):
            setattr(cls, a, dotype)


class USFMParser:

    def __init__(self, txt, factory=None):
        if factory is None:
            factory = et.Element
        self.factory = factory
        self.lexer = Lexer(txt)

    def parse(self):
        self.result = []
        self.stack = []
        rootnode = Node(self, 'usx', None)
        rootnode.addAttributes({'version': '3.0'})
        self.parent = rootnode
        self.stack.append(rootnode)

        for t in self.lexer:
            if isinstance(t, Tag):
                tagtype = marker_categories.get(t.basestr(), 'internal')
                if tagtype in ('internal', 'chapter'):
                    tagtype = t.basestr()
                    tagtype = "_"+tagtype
                    if tagtype == "_":   # end of milestone
                        tagtype = "milestone"
                fn = getattr(self, tagtype, self.unknown)
                self.parent = fn(t)
                continue
            if self.parent is None:
                continue
            if isinstance(t, dict):
                self.parent.addAttributes(t)
            elif isinstance(t, AttribText):
                self.parent.addDefaultAttrib(t)
            elif isinstance(t, OptBreak):
                self.parent.appendElement(t)
            elif isinstance(t, str):
                self.parent.appendText(t)
        return self.stack[0].element

    def removeParser(self, n):
        if n in self.stack:
            self.stack.remove(n)
        if n == self.parent:
            self.parent = self.stack[-1] if len(self.stack) else None

    def addNode(self, node):
        self.stack.append(node)
        return node

    def removeTag(self, tag):
        tag = str(tag).rstrip('*')
        tag = str(tag).lstrip('+')
        oldstack = self.stack[:]
        while len(self.stack):
            curr = self.stack.pop()
            if curr.tag == tag:
                break
        else:
            self.stack = oldstack
        return self.stack[-1]

    def removeType(self, t):
        if isinstance(t, str):
            t = [t]
        oldstack = self.stack[:]
        while len(self.stack):
            curr = self.stack.pop()
            curr.close()
            if curr is not None and marker_categories.get(curr.tag, None) in t:
                break
        else:
            self.stack = oldstack
        return self.stack[-1]

    def _id(self, tag):
        parent = self.addNode(IdNode(self, "book", str(tag)))
        return parent

    def _c(self, tag):
        self.removeType(paratypes)
        return self.addNode(NumberNode(self, "chapter", str(tag)))

    def _v(self, tag):
        return self.addNode(NumberNode(self, "verse", str(tag)))

    def _fig(self, tag):
        if tag.isend:
            return self.removeTag(str(tag))
        return self.addNode(Node(self, "figure", str(tag)))

    def _esb(self, tag):
        return self.addNode(Node(self, "sidebar", str(tag)))

    def _esbe(self, tag):
        return self.removeTag("esb")

    def _periph(self, tag):
        self.removeTag(str(tag))
        return self.addNode(PeriphNode(self, "periph", str(tag)))

    def attrib(self, tag):
        if tag.isend:
            return self.removeTag(str(tag))
        else:
            parent = AttribNode(self, self.parent, str(tag))
        self.stack.append(parent)
        return parent

    def cell(self, tag):
        self.removeType('cell')
        if not tag.isend:
            return self.addNode(Node(self, 'cell', str(tag)))
        return self.parent

    def footnote(self, tag):
        if tag.isend:
            return self.removeTag(str(tag))
        return self.addNode(NoteNode(self, 'note', str(tag)))

    def crossreference(self, tag):
        if tag.isend:
            return self.removeTag(str(tag))
        return self.addNode(NoteNode(self, 'note', str(tag)))

    def crossreferencechar(self, tag):
        self.removeType('crossreferencechar')
        return self.addNode(Node(self, 'char', str(tag)))

    def footnotechar(self, tag):
        self.removeType('footnotechar')
        return self.addNode(Node(self, 'char', str(tag)))

    def unknown(self, tag):
        self.addNode(Node(self, 'ms', str(tag)))
        return self.parent

setupParser(USFMParser)

def main():
    import sys
    p = USFMParser(sys.argv[1])
    e = p.parse()
    et.indent(e)
    et.dump(e)

if __name__ == '__main__': main()

