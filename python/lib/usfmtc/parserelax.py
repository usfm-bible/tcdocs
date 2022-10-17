#!/usr/bin/python3

import xml.etree.ElementTree as et
import re

manys = {
    '':  "sequence",
    '+': "oneOrMore",
    '*': "zeroOrMore",
    '?': "optional"
}

rmanys = {v:k for k,v in manys.items()}

class RelaxUSFMParser:
    def __init__(self, doc, backend, grammar, keeps=None):
        self.doc = doc
        self.back = backend
        self.grammar = grammar
        self.keeps = keeps or {}
        self.visited = set()
        self.used = set()
        self.groups = []
        self.idcount = 0
        self.ids = {}

    def _global(self, t):
        return self.doc.globalise(t)

    def _local(self, t):
        return self.doc.localise(t)

    def procChildren(self, e, curr, quietRefs=False, nofollow=False, usfm=True):
        ncurr = curr
        usfmonly = False
        gusfmorder = self._global('usfm:order')
        for i, c in sorted(enumerate(e), key=lambda x: (int(x[1].get(gusfmorder, 0)), x[0])):
            if usfmonly and not self._local(c.tag).startswith("usfm:") \
                    or c.get(self._global("usfm:ignore"), "false").lower() == "true":
                continue
            scurr = self.parseGrammar(c, ncurr, parent=e, quietRefs=quietRefs)
            if not nofollow:
                if scurr is None:
                    usfmonly = True
                else:
                    ncurr = scurr
            if e.get(self._global('usfm:done'), False):
                break
        return ncurr

    def makeSequence(self, tag, e, curr, t=None, name=None, noadd=False):
        nums = int(e.get('grouping', 8)) if e is not None else 8
        ncurr = self.back.sequence(combine=tag, parent=curr, groupby=nums, t=t, name=name)
        if curr is not None and id(curr) != id(ncurr) and not noadd:
            curr.append(ncurr)
        return ncurr

    def makeElement(self, tag, e, curr, name):
        res = self.makeSequence(tag, e, curr, t="element", name=name)
        self.back.elementStart(name, res)
        return res

    def endElement(self, ncurr):
        self.back.elementEnd(ncurr)

    def makeAttribute(self, tag, e, curr, name):
        res = self.makeSequence(tag, e, curr, t="attribute", name=name)
        self.back.attributeStart(name, res)
        return res

    def endAttribute(self, ncurr):
        self.back.attributeEnd(ncurr)

    def makeTag(self, vals, curr, e, prefix=None, refid=None, refbase=None):
        ocurr = curr
        if e.get('id', None):
            curr = self.makeRef(e, e.get('id'), curr)
        if len(vals) == 1:
            if prefix:
                ncurr = self.makeSequence("sequence", e, curr)
                self.makeTerminal('"{}"'.format(prefix), ncurr)
            else:
                ncurr = curr
            self.makeTerminal(vals[0][1:-1] if vals[0].startswith('"') else vals[0], ncurr, keep=True)
        else:
            if prefix is not None and len(prefix):
                self.makeTerminal('"{}"'.format(prefix), curr)
            ncurr = self.makeSequence("choice", e, curr)
            for v in vals:
                self.makeTerminal(v, ncurr, keep=True)
        return ocurr

    def makeEndTag(self, txt, curr, e, prefix=None, refid=None, refbase=None, term=None):
        if refid is not None:
            self.makeBackRef(e, refid, curr)
            if term is not None and len(term):
                self.makeTerminal('"{}"'.format(term), curr)
        else:
            self.makeTerminal('"{}{}{}"'.format(prefix or "", (txt or "").strip(), term or ""), curr)

    def makeTerminal(self, name, curr, ref=False, keep=False, many=""):
        m = manys.get(many, "sequence")
        sub = curr if m == "sequence" else self.makeSequence(m, None, curr)
        res = self.back.terminal(name, curr, ref=ref, keep=keep)
        sub.append(res)
        return curr

    def makeRef(self, e, tid, curr):
        ''' Make a back referenceable group, returning the sequence within it '''
        self.ids[(self.groups[-1], tid)] = self.idcount
        grp = self.back.refgroup(self.idcount, curr)
        self.idcount += 1
        return self.makeSequence("sequence", e, grp)

    def makeBackRef(self, e, tid, curr):
        self.back.backref(self, self.groups[-1], tid, self.ids, curr)

    def makeLookAhead(self, val, curr):
        res = self.back.lookahead(val, curr)
        curr.append(res)

    def makeLookBehind(self, val, curr):
        res = self.back.lookbehind(val, curr)
        curr.append(res)

    def parseGrammar(self, e, curr, parent=None, quietRefs=False, inparent=False):
        if curr is None:
            self.curr = self.makeSequence("sequence", None, None)
            curr = self.curr
            # quietRefs = False
        tag = self._local(e.tag)
        if e.get(self._global('usfm:parent'), "false") == "true" and not inparent:
            p = curr.parent.parent
            if p is not None:
                pc = self.makeSequence("sequence", None, p, noadd=True)
                p.insert(-1, pc)
            else:
                pc = curr
            self.parseGrammar(e, pc, parent=parent, quietRefs=quietRefs, inparent=True)
            return curr
        if e.get(self._global("usfm:stacked"), "false") == "true":
            scurr = self.makeSequence("stack", e, curr)
            curr = scurr
        else:
            scurr = None
        if tag == 'element':
            tag = "stack" if e.get(self._global("usfm:stacked"), "false") == "true" else "group"
            name = e.findtext(self._global('name'))
            ncurr = self.makeElement(tag, e, curr, name)
            self.procChildren(e, ncurr, nofollow=(tag in ("choice", "stack")), quietRefs=quietRefs)
            self.endElement(ncurr)
        elif tag in ("interleave", "choice", "oneOrMore", "zeroOrMore", "optional", "group", "stack"):
            ncurr = self.makeSequence(tag, e, curr)
            self.procChildren(e, ncurr, nofollow=(tag in ("choice", "stack")), quietRefs=quietRefs)
        elif tag == 'attribute':
            if not any([self._local(n.tag).startswith("usfm:") for n in e]):
                return curr
            name = e.findtext(self._global('name'))
            ncurr = self.makeAttribute('sequence', e, curr, name)
            self.procChildren(e, ncurr, quietRefs=quietRefs)
            self.endAttribute(ncurr)
        elif tag in ("text", "empty"):
            self.procChildren(e, curr)
        elif tag == "ref":
            if id(e) in self.used:
                return curr
            name = e.get('name')
            if not quietRefs and (name in self.visited or 
                        (name not in self.keeps and "+"+name not in self.keeps)):
                self.makeTerminal(name, curr, ref=True)
            else:
                if not quietRefs and "+"+name not in self.keeps:
                    self.visited.add(name)
                self.grammar.parseRef(name, curr=curr, parser=self, quietRefs=quietRefs)
        elif tag == "data":
            if e.get('type', '') == "string":
                reg = e.findtext('./{}/[@name="pattern"]'.format(self.doc.globalise('param')))
                if reg is None:
                    self.makeTerminal("text", curr)
                elif reg:
                    self.makeTerminal('/{}/'.format(reg), curr)
        elif tag == "value":
            self.makeTerminal('"{}"'.format(e.text.strip()), curr)
        elif tag == "usfm:tag":
            rcurr = self.makeSequence("sequence", e, curr)
            rcurr = self._addstrip("left", e, rcurr)
            refid = e.get('id', None)
            pref = e.get('prefix', '\\')
            if e.text is not None and e.text.strip() != "":
                vals = ['"{}"'.format(e.text.strip())]
            else:
                vals = self._getvals(parent)
                parent.set(self._global('usfm:done'), True)
            curr = self.makeTag(vals, rcurr, e, prefix=pref, refid=refid)
            if scurr is not None:
                curr = self.makeSequence("sequence", e, scurr)
                scurr = None
            curr = self._addstrip("right", e, curr, default="right single")
            # curr = None
        elif tag == "usfm:endtag":
            many = e.get('many', '')
            ncurr = self.makeSequence(manys.get(many, 'sequence'), e, curr)
            ncurr = self._addstrip("left", e, ncurr)
            prefix = e.get('prefix', '\\')
            refid = e.get('id', None)
            terminate = e.get('term', '*')
            self.makeEndTag(e.text, ncurr, e, prefix=prefix, refid=refid, term=terminate)
            ncurr = self._addstrip("right", e, ncurr)
        elif tag in ("usfm:attrib", "usfm:text"):
            if e.get("startlist", "false") == "true":
                p = curr.parent.parent
                if p is not None:
                    pc = self.makeSequence("sequence", None, p, noadd=True)
                    p.insert(-1, pc)
                else:
                    pc = curr
                self.makeTerminal('"|"', pc)
                self.makeTerminal('WS', pc, many="?")
                ncurr = self.makeSequence("choice", e, curr)
            else:
                ncurr = curr
            curr = self.makeSequence("sequence", e, ncurr)
            #curr = ncurr
            curr = self._addstrip("left", e, curr)
            fbreg = parent.findtext('{}[@type="string"]/{}[@name="pattern"]'.format(
                                            self._global('data'), self._global('param')))
            if fbreg is None:
                fbreg = parent.find('{}[@type="integer"]'.format(self._global('data')))
                if fbreg is not None:
                    fbreg = '\d+'
            reg = e.get("re", fbreg)
            done = False
            if tag == "usfm:attrib":
                if e.text is not None and e.text.strip() != "":
                    name = e.text.strip()
                else:
                    name = parent.findtext(self._global('name'))
                if name is not None:
                    self.makeTerminal('"{}="'.format(name), curr)
                self.makeTerminal("'\"'", curr)
            else:
                if e.text is not None and e.text.strip() != "":
                    q = '"' if not e.get('noquotes', 'false') == 'true' else ''
                    self.makeTerminal('{0}{1}{0}'.format(q, e.text), curr)
                    done = True
                elif n := e.get("name", None):
                    self.makeTerminal(n, curr)
                    done = True
            if done:
                pass
            elif reg is None:
                self.makeTerminal("Text", curr)
            else:
                self.makeTerminal("/"+reg+"/", curr)
            if tag == "usfm:attrib":
                self.makeTerminal("'\"'", curr)
            curr = self._addstrip("right", e, curr)
            curr = None
        elif tag == "usfm:repeat":
            rep = self.makeSequence("sequence", e, None)
            rep = self.procChildren(e, rep)
            if rep is not None and len(rep) == 1:
                rep = rep[0]
            init = None
            if e.get('initattriblist', "false") == "true":
                init = self.makeSequence("sequence", e, None)
                self.makeTerminal('"|"', init)
            curr = self.back.addrepeat(rep, curr, init=init)
        elif tag == "usfm:property":
            for k, v in e.attrib.items():
                setattr(curr, k, v)

        if scurr is not None:
            curr = self.makeSequence("sequence", e, scurr)
        return curr

    def parseRef(self, name, curr):
        top = self.defines.get(name, self.tops.get(name, None))
            
    def _addstrip(self, side, e, curr, default="", **attrs):
        if curr is None:
            curr = self.curr
        alt = e.get("lookahead" if side == "right" else "lookbehind", None)
        if alt is not None:
            ncurr = self.makeSequence("choice", None, curr)
            if side == "right":
                self.makeLookAhead('"{}"'.format(alt), ncurr)
            else:
                self.makeLookBehind('"{}"'.format(alt), ncurr)
            curr = ncurr
        stripvals = e.get("strip", default).split()
        m = [x[-1] for t in ("both", side) for x in stripvals if x.startswith(t)]
        if len(m):
            many = m[0] if m[0] in manys else ""
        else:
            many = None
        if many is not None:
            curr = self.makeTerminal("WS", curr, many=many)
        return curr

    def _getvals(self, e):
        res = []
        for c in e:
            tag = self._local(c.tag)
            if tag in ("interleave", "choice"):
                res.extend(self._getvals(c))
            elif tag == "value":
                res.append('"{}"'.format(c.text))
            elif tag == "data" and c.get('type', '') == 'string':
                reg = c.findtext('./{}/[@name="pattern"]'.format(self._global('param')))
                if reg is None:
                    res.append("text")
                elif len(reg):
                    res.append('/{}/'.format(reg))
            elif tag == "ref":
                name = c.get('name')
                ref = self.grammar.defines.get(name, [])
                self.used.add(id(c))
                res.extend(self._getvals(ref))
        return res

        
class RelaxXMLParser(RelaxUSFMParser):
    def parseGrammar(self, e, curr, parent=None, quietRefs=False):
        if curr is None:
            self.curr = self.makeSequence("sequence", None, None)
            curr = self.curr
            quietRefs = False
        if e.get(self._global("usfm:stacked"), "false") == "true":
            scurr = self.makeSequence("stack", e, curr)
            curr = scurr
        else:
            scurr = None
        tag = self._local(e.tag)
        if tag in ("interleave", "choice", "oneOrMore", "zeroOrMore", "optional", "group"):
            ncurr = self.makeSequence(tag, e, curr) if tag != "interleave" else curr
            curr = self.procChildren(e, ncurr, usfm=False, nofollow=True)
        elif tag == "element":
            name = e.findtext(self._global('name'))
            pcurr = self.makeSequence("sequence", e, curr)
            self.makeTerminal("<{}>".format(name), pcurr)
            ncurr = self.back.elementStart(name, pcurr, e.get(self._global("usfm:stacked"), "false") == "true")
            if ncurr is None:
                ncurr = pcurr
            else:
                pcurr.append(ncurr)
            for c in e:
                self.parseGrammar(c, ncurr, e)
            self.makeTerminal("</{}>".format(name), ncurr)
            self.back.elementEnd(ncurr)
        elif tag == "attribute":
            name = e.findtext(self._global('name'))
            g = e.find(self._global("usfm:tag"))
            if g is not None:
                grouping = int(g.get("grouping", 8))
            v = self.back.attributeStart(name, curr)
            for c in e:
                last = self.parseGrammar(c, v, parent=e)
            self.back.attributeEnd(curr, last)
        elif tag == "ref":
            if id(e) in self.used:
                return curr
            name = e.get('name')
            if not quietRefs and (name in self.visited or 
                        (name not in self.keeps and "+"+name not in self.keeps)):
                self.makeTerminal(name, curr, ref=True)
            else:
                if not quietRefs and "+"+name not in self.keeps:
                    self.visited.add(name)
                self.grammar.parseRef(name, curr=curr, parser=self, quietRefs=quietRefs)
        elif tag in ("text", "empty"):
            self.makeTerminal(e.get("name", tag), curr)
        elif tag == "value":
            if e.text is not None and e.text.strip() != "":
                self.makeTerminal('"{}"'.format(e.text.strip()), curr)
        elif tag == "data":
            ntype = e.get("type", "unknown")
            if ntype == "boolean":
                ntype = "BOOL"
            elif ntype == "string":
                reg = e.findtext('./{}/[@name="pattern"]'.format(self.doc.globalise('param')))
                if reg is None:
                    ntype = "text"
                elif reg:
                    ntype = '/{}/'.format(reg)
            self.makeTerminal(ntype, curr)
        if scurr is not None:
            curr = self.makeSequence("sequence", e, scurr)
        return curr
            

class Grammar:
    def __init__(self, doc):
        self.defines = {}
        self.markers = {}
        self.doc = doc

    def parse(self, doc):
        for e in doc:
            t = self.doc.localise(e.tag)
            if t == "start":
                self.defines[None] = e
            elif t == "define":
                name = e.get("name", "")
                self.defines[name] = e

    def parseRef(self, name, curr=None, parser=None, quietRefs=False):
        top = self.defines.get(name, None)
        if top is None:
            return
        if not quietRefs and name is not None:
            ncurr = parser.back.group(name, curr)
            if curr is None:
                parser.curr = ncurr
        else:
            ncurr = curr
        parser.groups.append(name)
        res = parser.procChildren(top, ncurr, quietRefs=quietRefs)
        parser.groups.pop()
        return res


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
        def nsget(m):
            return "{{{}}}".format(self.tb.ns.get(m.group(1), m.group(1)))
        if ':' not in t and '' in self.tb.ns:
            return "{{{}}}{}".format(self.tb.ns[''], t)
        else:
            return re.sub(r"^(.*?):", nsget, t)

    def teq(self, a, b):
        return self.localise(a) == self.localise(a)

