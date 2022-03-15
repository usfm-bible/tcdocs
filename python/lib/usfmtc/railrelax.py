#!/usr/bin/python

import xml.etree.ElementTree as et
from usfmtc import railroad
from usfmtc.railroad import Diagram, Choice, Optional, Terminal, NonTerminal, Sequence, DEFAULT_STYLE, Group, Sequence, OneOrMore, ZeroOrMore, HorizontalChoice, Stack, Comment, MultipleChoice
import re

class ETDoc:

    class NSTreeBuilder(et.TreeBuilder):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.ns = {}
            self.rns = {}

        def start_ns(self, prefix, uri):
            self.ns[prefix] = uri
            self.rns[uri] = prefix

    def __init__(self, inf):
        self.tb = self.NSTreeBuilder()
        self.parser = et.XMLParser(target=self.tb)
        self.doc = et.parse(inf, self.parser)

    # pretend we are an ElementTree
    def __getattr__(self, k):
        return getattr(self.doc, k)

    def localise(self, t):
        res = re.sub(r'^\{(.*?)\}', lambda m: self.tb.rns.get(m.group(1), m.group(0))+":", t)
        res = res[1:] if res[0] == ":" else res
        return res

    def globalise(self, t):
        if ':' not in t and '' in self.tb.ns:
            return "{{{}}}{}".format(self.tb.ns[''], t)
        else:
            return re.sub(r"^(.*?):", lambda m: "{{{}}}".format(self.tb.ns.get(m.group(1), m.group(1))), t)

    def teq(self, a, b):
        return self.localise(a) == self.localise(a)

def getvals(choice, doc):
    res = []
    tag = doc.localise(choice.tag)
    if tag == "value":
        return [choice.text]
    if tag == "choice":
        for e in choice:
            if doc.teq(e.tag, "value"):
                res.append(e.text)
    return res

def bigChoice(e, t, c, default=0, **kw):
    if len(c) < e.groupby + 2:
        return Choice(getattr(e, 'default', default), *c, **kw)
    else:
        s = []
        for i in range(0, len(c), e.groupby):
            s.append(Choice(3 if len(c) - i > 3 else 0, *c[i:i+e.groupby], **kw))
        return HorizontalChoice(*s, **kw)

actions = {
    'choice': lambda e,t,c: bigChoice(e, t, c),
    'attributed': lambda e,t,c: bigChoice(e, t, c, default=len(c) - 1, noclose=1),
    'attributes': lambda e,t,c: bigChoice(e, t, c, default=len(c) - 1, noclose=7),
    'interleave': lambda e,t,c: ZeroOrMore(bigChoice(e, t, c)),
    'terminal': lambda e,t,c: Terminal(t),
    'nonterminal': lambda e,t,c: NonTerminal(t),
    'optional': lambda e,t,c: Optional(c[0], getattr(e, 'skip', True)),
    'group': lambda e,t,c: Group(c[0], t),
    'sequence': lambda e,t,c: Sequence(*c),
    'oneormore': lambda e,t,c: OneOrMore(c[0], getattr(e, 'opt', None)),
    'zeroormore': lambda e,t,c: ZeroOrMore(c[0], getattr(e, 'opt', None)),
    'stack': lambda e,t,c: Stack(*c)
}

manys = {
    '':  "sequence",
    '+': "oneOrMore",
    '*': "zeroOrMore",
    '?': "optional"
}

CSS_STYLE = '''\
    svg.railroad-diagram {
        background-color:hsl(30,20%,95%);
    }
    svg.railroad-diagram path {
        stroke-width: 2;
        stroke: black;
        fill: none;
    }
    svg.railroad-diagram text {
        font-size: 12pt;
        text-anchor: middle;
        font-family: DejaVu Sans
    }
    svg.railroad-diagram text.label {
        text-anchor:start;
    }
    svg.railroad-diagram text.comment {
        font-family: DejaVu Sans;
        font-size: 15pt;
    }
    svg.railroad-diagram rect{
        stroke-width: 2;
        stroke:black;
        fill: rgb(210, 255, 210);
    }
    svg.railroad-diagram rect.group-box {
        stroke: gray;
        stroke-dasharray: 10 5;
        fill: none;
    }
    .terminal {
        font-family: DejaVu Sans;
    }
'''

class RChoice(list):

    def __init__(self, *a, combine="choice", parent=None, groupby=8):
        super().__init__(a)
        if combine == "group":
            combine = "sequence"
        self.combine = combine
        self.parent = parent
        self.groupby = groupby
        self.repeat = None

    def asXml(self, parent):
        if not len(self):
            return None
        n = et.SubElement(parent, self.combine)
        if len(self) > 1 and self.combine not in ("choice", "sequence"):
            n = et.SubElement(n, "sequence")
        for c in self:
            c.asXml(n)
        return n

    def asRail(self):
        if not len(self):
            return None
        if self.combine == "interleave":
            opts = []
            nonopts = []
            for e in self:
                if isinstance(e, RChoice):
                    if e.combine == "optional":
                        opts.append(e[0])
                        continue
                nonopts.append(e)
            rep = self.repeat.asRail() if self.repeat is not None else None
            o = ZeroOrMore(Choice(0, *[r for r in (v.asRail() for v in opts) if r is not None]), rep) if len(opts) else None
            n = MultipleChoice(0, "all", *[r for r in (v.asRail() for v in nonopts) if r is not None]) if len(nonopts) else None
            if n is None:
                return o
            else:
                if o is not None:
                    n.items.append(o)
                return n
        contents = [r for r in (v.asRail() for v in self) if r is not None]
        if len(contents) > 1 and self.combine not in ("choice", "sequence", "stack", "attributed", "attributes"):
            contents = [actions["sequence"](self, None, contents)]
        if len(contents) < 2 and self.combine in ("choice", "sequence", "stack", "attributed", "attributes"):
            return contents[0]
        elif len(contents):
            return actions[self.combine.lower()](self, self.combine, contents)
        return None
        

class RTerminal:
    def __init__(self, text, parent=None, ref=False, focus=False):
        self.text = text
        self.parent = parent
        self.focus = focus
        self.ref = ref

    def asXml(self, parent):
        n = et.SubElement(parent, ("Non" if self.ref else "")+"Terminal")
        if self.focus:
            n.set('class', "highlight")
        n.text = self.text
        return n

    def asRail(self):
        res = actions[("non" if self.ref else "")+"terminal"](self, self.text, None)
        if self.focus:
            res.cls = 'highlight'
        return res


class RGroup(list):
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

    def asXml(self, parent):
        n = et.SubElement(parent, "group", name=self.name)
        if len(self) > 1:
            n = et.SubElement(n, "sequence")
        for c in self:
            c.asXml(n)
        return n

    def asRail(self):
        if not len(self):
            return None
        contents = [r for r in (v.asRail() for v in self) if r is not None]
        if len(contents) > 1:
            contents = [actions["sequence"](self, None, contents)]
        if len(contents):
            return actions["group"](self, self.name, contents)
        return None
        
class RItem:
    def __init__(self, item, *a, **kw):
        self.item = item
        self.a = a
        self.kw = kw

    def asRail(self):
        return getattr(railroad, self.item)(*self.a, **self.kw)

def getlastchoice(e):
    if isinstance(e, RChoice):
        if e.combine == 'sequence':
            return getlastchoice(e[-1])
        else:
            return e
    elif isinstance(e, RGroup):
        return getlastchoice(e[-1])
    else:
        return None

class RDiagram:
    def __init__(self, name, doc, recurse=False, tag=None, usfm=True, keeps=None, cwidth=0):
        self.name = name
        self.doc = doc
        self.tag = tag or name
        self.curr = []
        self.elem = None
        self.recurse = recurse
        self.visited = set([name])
        self.keeps = set(keeps) if keeps else set()
        self.idcount = 0
        self.ids = {}
        self.isUsfm = usfm
        if cwidth != 0:
            railroad.CHAR_WIDTH = cwidth

    def addElement(self, e, grammar, curr=None, attrcurr=None, group=None):
        '''Generates a diagram for the XML description. Incomplete'''
        tag = self.doc.localise(e.tag)
        if tag in ("interleave", "choice", "oneOrMore", "zeroOrMore", "optional", "group"):
            ncurr = RChoice(combine=tag, parent=curr)
            for c in e:
                self.addElement(c, grammar, curr=ncurr, attrcurr=attrcurr)
            if len(ncurr):
                curr.append(ncurr)
            curr = ncurr
        elif tag == "element":
            name = e.findtext(self.doc.globalise('name'))
            pcurr = RChoice(combine="sequence", parent=curr)
            curr.append(pcurr)
            elem = RTerminal("<{}>".format(name), parent=pcurr)
            pcurr.append(elem)
            ncurr = RChoice(combine="attributed", parent=pcurr)
            scurr = RChoice(combine="sequence", parent=ncurr)
            ncurr.append(scurr)
            pcurr.append(ncurr)
            for c in e:
                self.addElement(c, grammar, curr=scurr, attrcurr=ncurr)
            curr = pcurr
        elif tag == "attribute":
            name = e.findtext(self.doc.globalise('name'))
            if isinstance(attrcurr, RChoice) and attrcurr.combine == "optional":
                name += "?"
                #attrcurr.parent.remove(attrcurr)
                attrcurr = attrcurr.parent
            v = RChoice(RTerminal("@"+name, parent=attrcurr), combine="sequence")
            if attrcurr is not None:
                attrcurr.insert(-1, v)
            else:
                curr.append(v)
            for c in e:
                last = self.addElement(c, grammar, curr=v)
            last = getlastchoice(last)
            if last is not None:
                last.combine = "attributes"
        elif tag == "ref":
            if e.get(self.doc.globalise("usfm:ignore"), "false").lower() == "true":
                return
            name = e.get('name')
            if name in self.visited or (name not in self.keeps and "+"+name not in self.keeps):
                curr.append(RTerminal(name, ref=True, parent=curr))
            else:
                if "+"+name not in self.keeps:
                    self.visited.add(name)
                grammar.makediagram(name, curr=curr, attrcurr=attrcurr, rdia=self, usfm=False)
        elif tag in ("text", "empty"):
            name = e.get("name", tag)
            curr.append(RTerminal(name, parent=curr))
        elif tag == "value":
            if e.text is not None and e.text.strip() != "":
                curr.append(RTerminal('"{}"'.format(e.text.strip())))
        elif tag == "data":
            ntype = e.get("type", "")
            if ntype == "boolean":
                ntype = "BOOL"
            curr.append(RTerminal(ntype, parent=curr))
        return curr

    def addElementUsfm(self, e, grammar, parent=None, curr=None, group=None):
        ''' Generates a diagram for the USFM.'''
        tag = self.doc.localise(e.tag)
        if tag in ("interleave", "choice", "oneOrMore", "zeroOrMore", "optional", "group"):
            nums = int(e.get(self.doc.globalise('usfm:grouping'), 8))
            ncurr = RChoice(combine=tag, parent=curr, groupby=nums)
            for c in e:
                self.addElementUsfm(c, grammar, curr=ncurr, parent=e, group=group)
            if len(ncurr):
                curr.append(ncurr)
        elif tag in ("element", "attribute"):
            if e.get(self.doc.globalise("usfm:ignore"), "false").lower() == "true":
                return
            ncurr = RChoice(combine="sequence", parent=curr)
            for c in sorted(e, key=lambda x:int(x.get(self.doc.globalise('usfm:order'), 0))):
                self.addElementUsfm(c, grammar, curr=ncurr, parent=e, group=group)
            curr.append(ncurr)
        elif tag in ("text", "empty"):
            for c in e:
                self.addElementUsfm(c, grammar, curr=curr, parent=e, group=group)
        elif tag == "ref":
            if e.get(self.doc.globalise("usfm:ignore"), "false").lower() == "true":
                return
            name = e.get('name')
            if name in self.visited or (name not in self.keeps and "+"+name not in self.keeps):
                curr.append(RTerminal(name, ref=True, parent=curr))
            else:
                if "+"+name not in self.keeps:
                    self.visited.add(name)
                grammar.makediagram(name, curr=curr, rdia=self)
        elif tag == "usfm:tag":
            rcurr = RChoice(combine="sequence", parent=curr)
            curr.append(rcurr)
            curr = rcurr
            curr = self.addstrip("left", e, curr)
            if 'id' in e.attrib:
                tid = e.get('id')
                self.ids[(group, tid)] = self.idcount
                ncurr = RGroup(chr(0x278A+self.idcount))
                self.idcount += 1
                curr.append(ncurr)
                curr = ncurr
            if e.text is not None and e.text.strip() != "":
                curr.append(RTerminal('"\\{}"'.format(e.text.strip())))
            else:
                ncurr = RChoice(combine="sequence", parent=curr)
                curr.append(ncurr)
                ncurr.append(RTerminal('"\\"'))
                vals = self.getvals(parent, grammar)
                nums = int(e.get('grouping', 8))
                curr.append(RChoice(*[RTerminal('"{}"'.format(v), parent=curr) for v in vals], combine="choice", parent=curr, groupby=nums))
            curr = self.addstrip("right", e, rcurr, default="right single")
        elif tag == "usfm:endtag":
            many = e.get('many', '')
            ncurr = RChoice(combine=manys.get(many, 'sequence'), parent=curr)
            curr.append(ncurr)
            curr = ncurr
            curr = self.addstrip("left", e, curr)
            if 'id' in e.attrib:
                tid = e.get('id')
                c = self.ids[(group, tid)]
                curr.append(RTerminal('\u21D0 {}'.format(chr(0x278A + c))))
                curr.append(RTerminal('"*"'))
            else:
                if e.text is None:
                    e.text = ""
                curr.append(RTerminal('"\\{}*"'.format(e.text.strip())))
            curr = self.addstrip("right", e, curr)
        elif tag == "usfm:attrib":
            curr = self.addstrip("left", e, curr)
            fbreg = parent.findtext('{}[@type="string"]/{}[@name="pattern"]'.format(
                                            self.doc.globalise('data'), self.doc.globalise('param')))
            if e.text is not None and e.text.strip() != "":
                curr.append(RTerminal('"{}="'.format(e.text)))
            curr.append(RTerminal("'\"'"))
            reg = e.get("re", fbreg)
            if reg is None:
                curr.append(RTerminal("Text"))
            else:
                curr.append(RTerminal("/"+reg+"/"))
            curr.append(RTerminal("'\"'"))
            curr = self.addstrip("right", e, curr)
        elif tag == "usfm:text":
            curr = self.addstrip("left", e, curr)
            fbreg = parent.findtext('{}[@type="string"]/{}[@name="pattern"]'.format(
                                            self.doc.globalise('data'), self.doc.globalise('param')))
            reg = e.get("re", fbreg)
            if e.text is not None and e.text.strip() != "":
                q = '"' if not e.get('noquotes', 'false') == 'true' else ''
                curr.append(RTerminal('{0}{1}{0}'.format(q, e.text)))
            elif reg is None:
                curr.append(RTerminal("Text"))
            else:
                curr.append(RTerminal("/"+reg+"/"))
            curr = self.addstrip("right", e, curr)
        elif tag == "usfm:repeat":
            rep = RChoice(combine="sequence")
            for c in e:
                self.addElementUsfm(c, grammar, curr=rep, parent=e, group=group)
            if len(rep) == 1:
                rep = rep[0]
            if isinstance(curr, RChoice):
                curr.repeat = rep

    def getvals(self, e, grammar):
        res = []
        for c in e:
            tag = self.doc.localise(c.tag)
            if tag in ("interleave", "choice"):
                res.extend(self.getvals(c, grammar))
            elif tag == "value":
                res.append(c.text)
            elif tag == "ref":
                name = c.get('name')
                ref = grammar.defines.get(name).content
                res.extend(self.getvals(ref, grammar))
        return res

    def addstrip(self, side, e, curr, default=""):
        alt = e.get("lookahead" if side == "right" else "lookbehind", None)
        if alt is not None:
            ncurr = RChoice(RTerminal('{} "{}"'.format("\u21D2" if side == "right" else "\u21D0", alt)),
                            combine="choice")
            curr.append(ncurr)
        else:
            ncurr = curr
        stripvals = e.get("strip", default).split()
        ws = RTerminal("WS")
        for t in ("both", side):
            m = [x[-1] for t in ("both", side) for x in stripvals if x.startswith(t)]
            if len(m):
                many = manys.get(m[0], "sequence")
            else:
                many = None
        if many is not None:
            ocurr = RChoice(ws, parent=ncurr, combine=many)
            ncurr.append(ocurr)
        return curr

    def asXml(self):
        top = et.Element("grammar")
        res = et.ElementTree(top)
        self.curr.asXml(top)
        return res

    def asRail(self):
        content = self.curr.asRail()
        res = Diagram(content, type='complex', css=CSS_STYLE)
        return res
        

class RGrammar:
    def __init__(self, doc):
        self.defines = {}
        self.markers = {}
        self.doc = doc

    def parse(self, doc):
        for e in doc:
            t = self.doc.localise(e.tag)
            if t == "start":
                self.defines[None] = RDefine(None, e, self.doc)
            elif t == "define":
                name = e.get("name", "")
                self.defines[name] = RDefine(name, e, self.doc)
        for v in self.defines.values():
            v.collect_markers(self)

    def makediagram(self, name, curr=None, rdia=None, usfm=True, attrcurr=None):
        if name not in self.defines:
            if name not in self.markers:
                return None
            else:
                top = self.markers[name]
        else:
            top = self.defines[name]
        ncurr = RGroup(top.name, parent=curr)
        if curr is None:
            rdia.curr = ncurr
        if curr is not None:
            curr.append(ncurr)
        for e in top.content:
            if usfm:
                rdia.addElementUsfm(e, self, curr=ncurr, group=top.name)
            else:
                rdia.addElement(e, self, curr=ncurr, group=top.name, attrcurr=attrcurr)
        return rdia

    def getvals(self, name):
        e = self.defines[name].content[0]
        return getvals(e, self.doc)

class RDefine:
    def __init__(self, name, content, doc):
        self.name = name
        self.content = content
        self.doc = doc

    def collect_markers(self, grammar):
        for e in self.content:
            t = self.doc.localise(e.tag)
            if t != "element":
                continue
            for c in e:
                if self.doc.teq(c.tag, "attribute") and c.get('name', '') == "style":
                    break
            else:
                continue
            d = c[0]
            if re.sub('^\{.*?\}', '', d.tag) == "ref":
                vals = grammar.getvals(d.get('name', ''))
            else:
                vals = getvals(d, self.doc)
            for v in vals:
                grammar.markers[v] = self

    def analyse(self):
        for e in self.content:
            if e.tag == "element":
                for c in e:
                    if c.tag == "attribute" and c.get('name', '') == "style":
                        continue
                    if c.tag == "interleave":
                        continue
                    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("infile",help="Input RelaxNG file")
    parser.add_argument("-o","--outfile",help="output file")
    parser.add_argument("-t","--tag",help="tag to look for")
    parser.add_argument("-r","--recurse",action="store_true",default=False,help="Recurse references")
    parser.add_argument("-k","--keep",action="append",default=[],help="tags to recurse into")
    args = parser.parse_args()

    rdoc = ETDoc(args.infile)
    rgram = RGrammar(rdoc)
    rgram.parse(rdoc.getroot())
    rdia = RDiagram(args.tag, rdoc, keeps=args.keep, cwidth=6)
    rdia = rgram.makediagram(args.tag, rdia=rdia)
    with open(args.outfile, "w", encoding="utf-8") as outf:
        if args.outfile.lower().endswith("xml"):
            odoc = rdia.asXml()
            odoc.write(outf, encoding="unicode", xml_declaration=True)
        elif args.outfile.lower().endswith("svg"):
            d = rdia.asRail()
            d.writeSvg(outf.write)

