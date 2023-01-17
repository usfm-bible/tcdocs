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

class UsfmParser:

    _manies = {
        '+': 'append_plus',
        '?': 'append_opt',
        '*': 'append_star',
    }

    def __init__(self, doc, backend):
        self.aliases = {}
        self.back = backend
        self.doc = doc
        self.defines = {}
        self.parse()
        self.idcount = 1
        self.groups = []
        self.ids = {}
        self.groupings = []
        self.elementlist = []
        self.nodes = []

    def parseRef(self, name, flattens=set(), flattenall=False):
        self.flattens = flattens
        self.flattenall = flattenall
        e = self.get_ref(name)
        self.curr = self.back.append_seq()
        if e is None:
            print("Can't find {}".format(name))
            return None
        self.groups = [name]
        self.idcount = 1
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

    def proc_children(self, e, res, skip=True, start=0, parent=None, index=0, **kw):
        for i, c in enumerate(sorted(e, key=lambda x:int(x.get(f"{usfmns}order", 0)))):
            if i < start:
                continue
            t = re.sub(r"^\{.*\}", "", c.tag)
            if c.tag.startswith(usfmns) and t in self.aliases:
                base = self.aliases[t]
                newe = c.makeelement(base.tag, base.attrib.copy())
                for k, v in c.attrib.items():
                    newe.set(k, v)
                if c.text is not None and len(c.text) and hasattr(base, 'default'):
                    newe.set(base.default, c.text)
                c = newe
                t = re.sub(r"^\{.*\}", "", c.tag)
            if (m := c.get(f"{usfmns}many", None)) is not None:
                res = getattr(self.back, self._manies[m])(res, **kw)
            if (not skip or t in ("match", "matchpair")) and c.get(f"{usfmns}ignore", "false") not in ("true", "1"):
                fn = getattr(self, t, None)
                if fn is not None:
                    if fn(c, res, skip=skip, index=i, parent=e, **kw) is None:
                        break
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
        if n is None or v is None:
            return res
        self.back.add_terminal(n, v, res)

    def attribute(self, e, res, **kw):
        name = e.findtext(f"./{relaxns}name") or "*"
        parms = {}
        nover = e.get(f'{usfmns}name-override', None)
        if nover is not None:
            parms['name-override'] = nover
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
        res = self.back.append_seq(res, forced=e.get(f"{usfmns}seq", "false") in ("true", "1"))
        cont = True
        for a in ('before', 'match', 'after'):
            v = e.get(a, None)
            if a == "match":
                dump = e.get('dump', 'false') in ("true", "1")
                capture = None
                if (d := e.get('id', None)) is not None:
                    lastres = res
                    res = self.back.append_group(self.idcount, res)
                    k = (self.groups[-1], d)
                    if k in self.ids:
                        capture = self.ids[k]
                    else:
                        self.ids[k] = self.idcount
                        capture = self.idcount
                        self.idcount += 1
                    logger.debug(f"{k} := {capture}")
                    res = self.back.append_seq(res, capture=capture, dump=dump)
                    dump = False
                if v is not None and len(v):
                    if a == "match" and v != v.upper() and v[0] not in "'/":
                        v = "'{}'".format(v)
                    res = self.back.match(v, res, dump=dump)
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
                res = self.back.match(v, res, dump=True)
        # this needs more work: @ahead
        return res if cont else None

    def matchpair(self, e, res, **kw):
        res = self.back.append_seq(res, forced=e.get(f"{usfmns}seq", "false") in ("true", "1"))
        for a in ('before', 'first', 'between', 'second', 'after'):
            v = e.get(a, None)
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
        pv = e.get(f'{usfmns}propval', None)
        if pv is not None:
            pe = self.elementlist[-1]
            pe.propmap[e.text] = pv
        return self.back.match('"'+e.text+'"', res)

    def ref(self, e, res, **kw):
        n = e.get('name', None)
        if n is None:
            return res
        elif n in self.flattens or self.flattenall:
            r = self.get_ref(n)
            self.groups.append(n)
            res = self.proc_children(r, res, **kw)
            self.groups.pop()
            return res
        elif "+"+n in self.flattens:
            return res
        elif n not in self.defines:
            r = self.get_ref(n)
            newres = self.back.add_define(n, r, **kw)
            self.defines[n] = newres
            self.elementlist.append(newres)
            self.groups.append(n)
            self.proc_children(r, newres, **kw)
            self.groups.pop()
            self.elementlist.pop()
        if len(self.elementlist):
            self.elementlist[-1].propmap.update(self.defines[n].propmap)
        return self.back.ref(n, res, **kw)

    def data(self, e, res, **kw):
        t = e.get('type', None)
        if t == 'string':
            reg = e.findtext('./{}param/[@name="pattern"]'.format(relaxns))
            if reg is not None:
                res = self.back.match("/"+reg+"/", res)
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

class XmlParser:
    def __init__(self, doc, backend):
        self.doc = doc
        self.back = backend
        self.groupings = []
        self.elements = {}

    def parseRef(self, name, flattens=set()):
        self.flattens = flattens
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
            reg = e.findtext('./{}param/[@name="pattern"]'.format(relaxns))
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

# ----------------------------------------------------------------------------

import usfmtc.railroad as rr
CSS_STYLE = '''
    svg.railroad-diagram {{
        background-color:hsl(30,20%,95%);
    }}
    svg.railroad-diagram path {{
        stroke-width: {line-width};
        stroke: black;
        fill: none;
    }}
    svg.railroad-diagram text {{
        font-size: {text-size};
        text-anchor: middle;
        font-family: {font};
    }}
    svg.railroad-diagram text.label {{
        text-anchor:start;
    }}
    svg.railroad-diagram text.comment {{
        font-family: {font};
        font-size: {comment-size};
    }}
    svg.railroad-diagram rect{{
        stroke-width: {line-width};
        stroke:black;
        fill: {color};
    }}
    svg.railroad-diagram rect.group-box {{
        stroke: gray;
        stroke-dasharray: 10 5;
        fill: none;
    }}
    .terminal {{
        font-family: {font};
    }}
'''

class RailRoad:
    def __init__(self):
        self.terminals = {}
        self.defines = {}

    class WrappedRail:
        def __init__(self, content, parent):
            self.rtype = content
            self.parent = parent
            self.properties = {}
        def asRail(self):
            return self.rtype
        def getProperty(self, k, default):
            return self.properties.get(k, default)
        def __str__(self):
            return f"WrappedRail({self.rtype})"

    class WrappedRailList(list):
        def __init__(self, rtype, parent, *args, swap=False, forced=False, **kw):
            self.properties = {}
            self.rtype = rtype
            self.parent = parent
            self.args = list(args)
            self.swap = swap
            self.forced = forced
            self.kw = kw
            self.propmap = {}

        def asRail(self):
            content = []
            for x in self:
                y = x.asRail()
                if y is not None:
                    content.append(y)
            if self.rtype == rr.Choice and self.kw.get('groupby', 0) > 0:
                s = []
                for i in range(0, len(content), self.kw['groupby']):
                    s.append(self.rtype(3 if len(content) - i > 3 else 0,
                                *content[i:i+self.kw['groupby']], **self.kw))
                return rr.HorizontalChoice(*s, **self.kw)
            if self.swap:
                return self.rtype(*(content + list(self.args)), **self.kw) if len(content) else None
            else:
                return self.rtype(*(list(self.args) + content), **self.kw) if len(content) else None
        def getProperty(self, k, default):
            return self.properties.get(k, default)
        def __str__(self):
            return f"WrappedRailList({self.rtype}{self.args})[" + ", ".join(str(x) for x in self) + "]"

    def output(self, top, **kw):
        defaults = {
            'font': 'DejaVu Sans',
            'text-size': '12px',
            'comment-size': '14px',
            'color': 'rgb(210, 255, 210)',
            'line-width': '2'}
        defaults.update(kw)
        return rr.Diagram(top.asRail(), type='complex', css=CSS_STYLE.format(**defaults))

    def attrib_start(self, parser, e, context, name, **kw):
        res = self.append_seq(context, stacked=e.get("{}stacked".format(usfmns), "false") in ("true", "1"))
        res.name = name
        parser.push_element(res)
        return res

    def attrib_end(self, parser, e, context, **kw):
        parser.pop_element()
        return context

    def elem_start(self, parser, e, context, name, **kw):
        res = self.append_seq(context, stacked=e.get("{}stacked".format(usfmns), "false") in ("true", "1"))
        res.name = name
        parser.push_element(res)
        return res

    def elem_end(self, parser, e, context, **kw):
        parser.pop_element()
        return context

    def append_type(self, context, tclass, *a, swap=False, forced=False, **kw):
        if context is not None and not forced \
                and (context.rtype == tclass or context.rtype == rr.Stack and tclass == rr.Sequence):
            return context
        else:
            res = self.WrappedRailList(tclass, context, *a, swap=swap, forced=forced, **kw)
            if context is not None:
                context.append(res)
            return res

    def append_seq(self, context=None, stacked=False, forced=False, **kw):
        return self.append_type(context, rr.Stack if stacked else rr.Sequence, forced=forced)

    def append_opt(self, context=None, **kw):
        return self.append_type(context, rr.Choice, 0, rr.Skip())

    def append_or(self, context=None, groupby=None, **kw):
        return self.append_type(context, rr.Choice, 0, groupby=groupby)

    def append_plus(self, context=None, **kw):
        bet = context.getProperty("between", None)
        if bet is not None:
            rep = rr.Terminal(bet)
            res = self.append_type(context, rr.OneOrMore, rep, swap=True)
        else:
            res = self.append_type(context, rr.OneOrMore, swap=True)
        return res

    def append_star(self, context=None, **kw):
        res = self.WrappedRailList(rr.ZeroOrMore, context)   # returns Choice(OneOrMore)
        context.append(res)
        return res

    def append_group(self, index, context=None, **kw):
        label = chr(0x278A + index)
        res = self.WrappedRailList(rr.Group, context, label, swap=True)
        context.append(res)
        return res

    def append_interleave(self, context=None, **kw):
        def inter(repeat, *items):
            return rr.OneOrMore(rr.MultipleChoice(0, "any", *items), repeat)
        bet = context.getProperty("interleave_between", None)
        rep = rr.Terminal(bet) if bet is not None else None
        res = self.WrappedRailList(inter, context, bet)
        context.append(res)
        return res

    def match(self, txt, context, **kw):
        context.append(self.WrappedRail(rr.Terminal(txt), context))
        return context

    def terminal(self, name,  context, **kw):
        context.append(self.WrappedRail(rr.NonTerminal(name), context))
        return context

    def backref(self, index, context=None, **kw):
        context.append(self.WrappedRail(rr.Terminal("\u21D0 {}".format(chr(0x278A + index))), context))
        return context

    def add_terminal(self, name, value, context, **kw):
        self.terminals[name] = value

    def add_define(self, e, name, **kw):
        res = self.append_seq()
        self.defines[name] = res
        return res

    def ref(self, name, res, **kw):
        return self.terminal(name, res)

    def end_ref(self, e, name, **kw):
        pass


class XMLRailRoad(RailRoad):

    def elem_start(self, parser, e, context, name, **kw):
        seq = self.append_type(context, rr.Sequence, forced=True)
        context = self.match(f"<{name}>", seq)
        res = self.append_type(seq, rr.Choice, 0, forced=True, noclose=1)
        res.attribs = {}
        return res

    def elem_end(self, parser, e, context, **kw):
        if context.args[0] == len(context):
            context.append(self.WrappedRail(rr.Skip(), context))
        elif context.args[0] > len(context):
            print(f"{context} has index of {context.args[0]} but length of {len(context)}")
            context.args[0] = len(context) - 1
        return context

    def attrib_start(self, parser, e, context, name, **kw):
        parent = context
        while parent is not None and parent.kw.get('noclose', 0) == 0:
            parent = parent.parent
        s = self.WrappedRailList(rr.Sequence, parent)
        n = self.WrappedRail(rr.Terminal(f"@{name}"), s)
        s.append(n)
        if parent is None:
            context.append(s)
        elif getattr(parent, 'attribs', {}).get(name, None) is None:
            parent.insert(0, s)
            parent.args[0] += 1
            parent.attribs[name] = 1
        return s

    def attrib_end(self, parser, e, context, **kw):
        if context[-1].rtype in (rr.Choice, rr.HorizontalChoice):
            context[-1].kw['noclose'] = 7
        return context

