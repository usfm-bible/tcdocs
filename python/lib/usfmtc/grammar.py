#!/usr/bin/python3

import re
import logging

logger = logging.getLogger(__name__)

usfmns = "{http://usfm.bible/parse/2023}"
relaxns = "{http://relaxng.org/ns/structure/1.0}"

class AttribElement:
    def __init__(self, tag, attrib):
        self.tag = tag
        self.attrib = attrib


class UsfmGrammarParser:

    _manies = {
        '+': 'append_plus',
        '?': 'append_opt',
        '*': 'append_star',
    }

    def __init__(self, doc, backend, flattenre=True, hrefprefix=""):
        self.aliases = {}
        self.back = backend
        self.doc = doc
        self.flattenre = flattenre
        self.hrefprefix = hrefprefix or ""
        self.defines = {}
        self.vars = {}
        self.parse()
        self.idcount = 1
        self.groups = []
        self.ids = {}
        self.groupings = []
        self.elementlist = []
        self.nodes = []

    def parseRef(self, name, flattens=set(), flattenall=True):
        self.flattens = flattens
        self.flattenall = flattenall
        if flattenall:
            self.defines = {}
        self.idcount = 1
        self.ids = {}
        e = self.get_ref(name)
        self.curr = self.back.append_seq()
        if e is None:
            print("Can't find {}".format(name))
            return None
        self.groups = [name]
        self.attribnodes = [None]
        res = self.proc_children(e, self.curr, False)
        self.groups.pop()
        return res

    def get_ref(self, name):
        res = self.doc.find('.//{}define[@name="{}"]'.format(relaxns, name))
        if res is None:
            raise IndexError(f"{name} not in grammar")
        return res

    def parse(self):
        for e in self.doc.getroot():
            if e.tag == usfmns+"alias":
                self.alias(e, None)
            elif e.tag == usfmns + "terminal":
                self.terminal(e, None)
            elif e.tag == relaxns+"start":
                self.start = e

    def expandvars(self, s):
        if not self.flattenre:
            return s
        if s is None:
            return None
        return re.sub(r"\$\{(.*?)\}", lambda m:self.expandvars(self.vars.get(m.group(1), "'"+m.group(1)+"'")[1:-1]), s)

    def getorder(self, e):
        if f'{usfmns}order' not in e.attrib and \
                e.tag in (f'{relaxns}optional', '{relaxns}oneOrMore', '{relaxns}zeroOrMore', '{relaxns}group') and \
                len(e) == 1 and e[0].tag == f"{relaxns}group" and f'{usfmns}order' in e[0].attrib:
            return int(e[0].get(f'{usfmns}order', 0))
        else:
            return int(e.get(f'{usfmns}order', 0))

    def proc_children(self, e, res, skip=True, start=0, parent=None, index=0, **kw):
        for i, c in enumerate(sorted(e, key=lambda x:self.getorder(x))):
            if i < start:
                continue
            t = re.sub(r"^\{.*\}", "", c.tag)
            if c.tag.startswith(usfmns) and t in self.aliases:
                base = self.aliases[t]
                newe = c.makeelement(base.tag, {k: v for k, v in base.attrib.items()})
                for k, v in c.attrib.items():
                    newe.set(k, self.expandvars(v))
                if c.text is not None and len(c.text) and hasattr(base, 'default'):
                    newe.set(base.default, c.text)
                c = newe
                t = re.sub(r"^\{.*\}", "", c.tag)
            if (m := c.get(f"{usfmns}many", None)) is not None:
                newres = getattr(self.back, self._manies[m])(res, **kw)
                if len(res.propmap):
                    newres.propmap = res.propmap.copy()
                res = newres
            if (not skip or t in ("match", "matchpair")) and c.get(f"{usfmns}ignore", "false") not in ("true", "1"):
                fn = getattr(self, t, None)
                if fn is not None:
                    if fn(c, res, skip=skip, index=i, parent=e, **kw) is None:
                        break
        if getattr(res, 'children', None) is not None:
            for c in res.children:
                res.propmap.update(getattr(c, 'propmap', {}))
        return res

    def push_element(self, val):
        self.nodes.append(val)

    def pop_element(self):
        return self.nodes.pop()

# ---- Tag methods ---

    def alias(self, e, res, **kw):
        n = e.get('name', None)
        if n is None:
            return res
        if n.startswith("usfm:"):
            n = n[5:]
        a = AttribElement(e[0].tag, e[0].attrib)
        d = e.get('def', None)
        if d is not None:
            a.default = d
        self.aliases[n] = a
        return res

    def terminal(self, e, res, **kw):
        n = e.get('name', None)
        v = e.get('value', None)
        val = self.expandvars(v)
        if n is None or v is None:
            return res
        self.vars[n] = val
        self.back.add_terminal(n, val, res)

    def attribute(self, e, res, **kw):
        name = e.findtext(f"./{relaxns}name") or "*"
        parms = {}
        nover = e.get(f'{usfmns}fallback-from', None)
        if nover is not None:
            parms['fallback-from'] = nover
        res = self.back.attrib_start(self, e, res, name, **parms)
        g = int(e.get(f"{usfmns}grouping", 0))
        self.groupings.append(g)
        self.proc_children(e, res)
        res = self.back.attrib_end(self, e, res)
        self.groupings.pop()
        return res

    def element(self, e, res, **kw):
        name = e.findtext(f"./{relaxns}name")
        res = self.back.elem_start(self, e, res, name)
        g = int(e.get(f"{usfmns}grouping", 0))
        self.groupings.append(g)
        self.elementlist.append(res)
        self.proc_children(e, res, False)
        res = self.back.elem_end(self, e, res)
        self.elementlist.pop()
        self.groupings.pop()
        return res

    def match(self, e, res, **kw):
        attrib = e.get('{usfmns}attrib', None)
        if attrib is not None:
            print(f"{attrib=}")
            res = self.back.attrib_start(self, e, res, attrib)
        res = self.back.append_seq(res, forced=e.get(f"{usfmns}seq", "false") in ("true", "1"))
        cont = True
        for a in ('before', 'match', 'after'):
            v = self.expandvars(e.get(a, None))
            if a == "match":
                dump = e.get('dump', 'false') in ("true", "1")
                capture = None
                if (d := e.get('matchid', None)) is not None:
                    lastres = res
                    k = (self.groups[-1], d)
                    if k not in self.ids:
                        self.ids[k] = self.idcount
                        self.idcount += 1
                    capture = self.ids[k]
                    res = self.back.append_group(capture, res)
                    logger.debug(f"{k} := {capture}")
                    res = self.back.append_seq(res, capture=capture, dump=dump)
                    dump = False
                if v is not None and len(v) and v != "''":
                    if a == "match" and v != v.upper() and v[0] not in "'/":
                        v = "'{}'".format(v)
                    res = self.back.match(v, res, dump=dump, alt=self.expandvars(e.get(a+"out", None)))
                elif (r := e.get('matchref', None)) not in (None, ""):
                    for j in range(len(self.groups) - 1, -1, -1):
                        k = (self.groups[j], r)
                        if k in self.ids:
                            logger.debug(f"{k} = {self.ids[k]} {self.groups}")
                            self.back.backref(self.ids[k], res, dump=dump)
                            break
                else:
                    self.proc_children(kw.get('parent', e), res, False, start=kw.get('index', 0)+1)
                    cont = False
                if d is not None:
                    res = lastres
            elif v is not None:
                res = self.back.match(v, res, dump=True, alt=self.expandvars(e.get(a+"out", None)))
        # this needs more work: @ahead
        if attrib is not None:
            res = self.back.attrib_end(self, e, res)
        return res if cont else None

    def matchpair(self, e, res, **kw):
        fb = self.expandvars(e.get('fallback', None))
        if fb is not None:
            res = self.back.append_or(res)
            self.back.match(fb, res)
        res = self.back.append_seq(res, forced=e.get(f"{usfmns}seq", "false") in ("true", "1"))
        for a in ('before', 'first', 'between', 'second', 'after'):
            v = self.expandvars(e.get(a, None))
            if v is not None:
                res = self.back.match(v, res, dump=a not in ('first', 'second'))
        return res

    def optional(self, e, res, **kw):
        res = self.back.append_opt(res)
        return self.proc_children(e, res, **kw)

    def group(self, e, res, **kw):
        res = self.back.append_seq(res, forced=e.get(f"{usfmns}seq", "false") in ("true", "1"))
        return self.proc_children(e, res, **kw)

    def choice(self, e, res, **kw):
        res = self.back.append_or(res, groupby=self.groupings[-1] if len(self.groupings) else 0)
        return self.proc_children(e, res, **kw)

    def oneOrMore(self, e, res, **kw):
        res = self.back.append_plus(res)
        return self.proc_children(e, res, **kw)

    def zeroOrMore(self, e, res, **kw):
        res = self.back.append_star(res)
        return self.proc_children(e, res, **kw)

    def interleave(self, e, res, **kw):
        res = self.back.append_interleave(res)
        return self.proc_children(e, res, **kw)

    def value(self, e, res, **kw):
        ekw = {}
        pv = e.get(f'{usfmns}propval', None)
        if pv is not None:
            pe = self.elementlist[-1]
            pe.propmap[e.text] = pv
            res.propmap[e.text] = pv
        pl = e.get(f'{usfmns}href', None)
        if pl is not None:
            ekw['href'] = self.hrefprefix + pl.format(e.text)
        return self.back.match('"'+e.text+'"', res, **ekw)

    def ref(self, e, res, **kw):
        if e is None and 'name' in kw:
            n = kw['name']
            del kw['name']
        else:
            alt = e.get(f'{usfmns}alt', None)
            if alt is not None:
                res = self.back.append_or(res)
                self.ref(None, res, name=alt, **kw)
            n = e.get('name', None)
        if n is None:
            return res
        elif n in self.flattens:
            r = self.get_ref(n)
            self.groups.append(n)
            res = self.proc_children(r, res, **kw)
            self.groups.pop()
            return res
        elif "+"+n in self.flattens:
            return res
        elif n not in self.defines and self.flattenall:
            r = self.get_ref(n)
            newres = self.back.add_define(n, r, context=res, box=self.flattenall, **kw)
            self.defines[n] = newres
            self.groups.append(n)
            res = self.proc_children(r, newres, **kw)
            self.groups.pop()
            return res
        if self.flattenall and len(self.elementlist):
            self.elementlist[-1].propmap.update(self.defines[n].propmap)
        return self.back.ref(n, res, **kw)

    def data(self, e, res, **kw):
        t = e.get('type', None)
        if t == 'string':
            usfmp = e.find(f'./{usfmns}pattern')
            if usfmp is None:
                reg = e.findtext('./{}param/[@name="pattern"]'.format(relaxns))
                if reg is not None:
                    reg = "/" + reg + "/"
            else:
                reg = self.expandvars(usfmp.get('name', None))
            if reg is not None:
                res = self.back.match(reg, res)
            else:
                res = self.back.match('TEXT', res)
        elif t == "integer":
            res = self.back.match("/[0-9]+/", res)
        elif t == "boolean":
            res = self.back.match('BOOL', res)
        return res

    def properties(self, e, res, **kw):
        res.properties.update(e.attrib)
        return res

    def text(self, e, res, **kw):
        return self.proc_children(e, res, **kw)

class XmlGrammarParser:
    def __init__(self, doc, backend, flattenre=True):
        self.flattenre = flattenre
        self.doc = doc
        self.back = backend
        self.groupings = []
        self.elements = {}

    def expandvars(self, s):
        if not self.flattenre:
            return s
        if s is None:
            return None
        return re.sub(r"\$\{(.*?)\}", lambda m:self.vars.get(m.group(1), "'"+m.group(1)+"'")[1:-1], s)

    def parseRef(self, name, flattens=set(), flattenall=True):
        self.flattens = flattens
        self.flattenall = flattenall
        e = self.get_ref(name)
        self.curr = self.back.append_seq()
        if e is None:
            print("Can't find {}".format(name))
            return None
        self.elements = {}
        res = self.proc_children(e, self.curr)
        return res

    def get_ref(self, name):
        return self.doc.find(f'.//{relaxns}define[@name="{name}"]')

    def parse(self):
        pass

    def proc_children(self, e, res):
        for c in e:
            t = re.sub(r"^\{.*\}", "", c.tag)
            fn = getattr(self, t, None)
            if fn is not None:
                if fn(c, res, parent=e) is None:
                    break
        return res

    def attribute(self, e, res, **kw):
        name = e.findtext(f"./{relaxns}name") or "*"
        res = self.back.attrib_start(self, e, res, name)
        g = int(e.get(f"{usfmns}grouping", 0))
        self.groupings.append(g)
        self.proc_children(e, res)
        self.groupings.pop()
        res = self.back.attrib_end(self, e, res)
        return res

    def element(self, e, res, **kw):
        name = e.findtext(f"./{relaxns}name")
        if name in self.elements:
            res = self.elements[name]
        else:
            res = self.back.elem_start(self, e, res, name)
        g = int(e.get(f"{usfmns}grouping", 0))
        self.groupings.append(g)
        self.proc_children(e, res)
        self.groupings.pop()
        self.elements[name] = res
        res = self.back.elem_end(self, e, res)
        return res

    def optional(self, e, res, **kw):
        res = self.back.append_opt(res)
        return self.proc_children(e, res)

    def group(self, e, res, **kw):
        res = self.back.append_seq(res, forced=e.get(f"{usfmns}seq", "false") in ("true", "1"))
        return self.proc_children(e, res)
        
    def choice(self, e, res, **kw):
        res = self.back.append_or(res, groupby=self.groupings[-1] if len(self.groupings) else 0)
        return self.proc_children(e, res)

    def oneOrMore(self, e, res, **kw):
        res = self.back.append_plus(res)
        return self.proc_children(e, res)

    def zeroOrMore(self, e, res, **kw):
        res = self.back.append_star(res)
        return self.proc_children(e, res)

    def interleave(self, e, res, **kw):
        res = self.back.append_interleave(res)
        return self.proc_children(e, res)

    def value(self, e, res, **kw):
        return self.back.match('"'+e.text+'"', res)

    def ref(self, e, res, **kw):
        n = e.get('name', None)
        if n is None:
            return res
        elif n in self.flattens:
            r = self.get_ref(n)
            return self.proc_children(r, res)
        elif "+"+n in self.flattens:
            return res
        else:
            return self.back.ref(n, res)

    def data(self, e, res, **kw):
        t = e.get('type', None)
        if t == 'string':
            usfmp = e.find(f'./{usfmns}pattern')
            if usfmp is None:
                reg = e.findtext('./{}param/[@name="pattern"]'.format(relaxns))
            else:
                reg = self.expandvars(e.get('name', None))
            if reg is not None:
                res = self.back.match("/"+reg+"/", res)
            else:
                res = self.back.match('TEXT', res)
        elif t == "integer":
            res = self.back.match("/[0-9]+/", res)
        elif t == "boolean":
            res = self.back.match('BOOL', res)
        return res

    def text(self, e, res, **kw):
        if e.tag.startswith(usfmns):
            return res
        return self.back.match("TEXT", res)

    def empty(self, e, res, **kw):
        return self.back.match("EMPTY", res)

    def properties(self, e, res, **kw):
        res.properties.update(e.attrib)
        return res

