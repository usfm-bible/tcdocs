#!/usr/bin/python3

import re, logging
from dataclasses import dataclass
import xml.etree.ElementTree as et
import regex
import usfmtc.parser as usfmp
from usfmtc.xmlutils import ParentElement

logger = logging.getLogger("sfmparser")

class GlobalState(usfmp.GlobalState):
    ''' text based global state '''
    def __init__(self, txt, timeout=1e7):
        super().__init__(timeout=timeout)
        self.str = txt
        self.captures = []
        self.refs = {}

    def __getitem__(self, key):
        return self.str[key]

    def __call__(self):
        return self.str

    def _ensure(self, index):
        if index >= len(self.captures):
            #self.captures.extend([""] * (index - len(self.captures) + 1))
            self.captures += [[[]] for i in range(index - len(self.captures) + 1)]

    def capture(self, index, txt):
        self._ensure(index)
        if isinstance(txt, (list, tuple)):
            txt = "".join(txt)
        logger.debug(f"Capture[{index}][{len(self.captures[index])-1}] = '{txt}'")
        self.captures[index][-1] = txt

    def init(self, index, txt):
        self._ensure(index)
        logger.debug(f"Init capture[{index}][{len(self.captures[index])}]")
        self.captures[index].append("")

    def release(self, index):
        self.captures[index].pop()
        logger.debug(f"Pop capture[{index}][{len(self.captures[index])}]")

    def getcapture(self, index):
        logger.debug(f"Get capture[{index}][{len(self.captures[index])}] = '{self.captures[index][-1]}'")
        return self.captures[index][-1]

    def pop(self):
        return self.captures.pop()

    def getref(self, name):
        return self.refs.get(name)


class Group(usfmp.Group):

    def _returnRes(self, res, s):
        res = super()._returnRes(res, s)
        if res is None:
            return None
        while res is not None and len(res) == 1:
            if isinstance(res, (str, Attribute, Element)):
                break
            res = res[0]
        final = self.result(res, self) if self.result is not None else res
        if self.capture and final is not None:
            s.gs.capture(self.capture, final)
        return final


class String(usfmp.Parser):
    def __init__(self, reg, dump=False, **kw):
        self.keep = not dump
        def text(s):
            m = regex.match(self.re, s.gs(), pos=s.pos)
            if not m:
                raise usfmp.NoParseError(f'String ({self.re}) not found', s)
            return (m.group(1) if self.keep else None, s.extend(m.end()-s.pos))
        super().__init__(text, **kw)
        reg = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m:chr(int(m.group(1), 16)), reg)
        self.re = reg if dump else "(" + reg + ")"
        self.name = "/" + reg + "/"

    def __repr__(self):
        return self.asstr()

    def asstr(self, context=None):
        return '/{}/{}'.format(self.re, "!" if self.keep else "")

    def merge(self, other, mode=None):
        if not isinstance(other, String):
            return super().merge(other, mode=mode)
        if mode and "|" in mode:
            ore = other.re[1:-1] if other.re.startswith("(") and other.re.endswith(")") else other.re
            if self.re.startswith("(") and self.re.endswith(")"):
                self.re = self.re[:-1] + "|" + ore + ")"
            else:
                self.re = "(" + self.re + "|" + ore + ")"
        elif self.keep and other.keep:
            return super().merge(other, mode=mode)
        else:
            self.re += other.re
        self.name = "/" + self.re + "/"
        self.keep |= other.keep
        return (self,)

    def empty(self):
        return len(self.name) == 0


class Reference(usfmp.Parser):
    def __init__(self, index, **kw):
        self.backref = index
        def test(s):
            v = s.gs.getcapture(self.backref)
            if s.gs().startswith(v, s.pos):
                return(v if not kw.get('dump', False) else None, s.extend(len(v)))
            else:
                raise usfmp.NoParseError(f'String from backref (v) not found', s)
        super().__init__(test, **kw)

    def __repr__(self):
        return "\u21D0{}".format(self.backref)

    def asstr(self, context=None):
        return "\u21D0{}".format(self.backref)


@dataclass
class Attribute:
    name: str
    value: str
    override: str

    def __init__(self, name, value, override, **kw):
        self.override = override
        if isinstance(value, list):
            if len(value) > 1:
                self.name, self.value = value
                return
            else:
                value = value[0]
        self.name = name
        self.value = value

    def __len__(self):
        return 1


class Element(list):
    def __init__(self, *a, name=None, propmap=None, **kw):
        self.name = name
        self.attributes = {}
        self.propmap = propmap
        self.kw = kw
        for e in a:
            self._append(e)
        if usfmp.Parser.debug:
            logger.debug(f"Create Element({self})")

    def _append(self, e):
        if isinstance(e, Attribute):
            if self.propmap is not None and e.override is not None and e.name == "_default":
                self.attributes[self.propmap.get(self.attributes[e.override], e.name)] = e.value
            else:
                self.attributes[e.name] = e.value
        elif isinstance(e, list) and not isinstance(e, Element):
            for c in e:
                self._append(c)
        else:
            self.append(e)

    def asEt(self, parent=None, elfactory=None):
        if elfactory is None:
            elfactory = ParentElement
        res = elfactory(self.name, attrib=self.attributes, parent=parent)
        if parent is not None:
            parent.append(res)
        def asetchild(c, res):
            if isinstance(c, str):
                if len(res):
                    res[-1].tail = c if res[-1].tail is None else res[-1].tail + c
                else:
                    res.text = c if res.text is None else res.text + c
            elif isinstance(c, Element):
                c.asEt(res, elfactory=elfactory)
            elif isinstance(c, list):
                for e in c:
                    asetchild(e, res)
        j = self[:]
        self.clear()
        for c in j:
            self._append(c)
        for c in self:
            asetchild(c, res)
        return res

    def __str__(self):
        return "{}<{}>{}".format(self.name, self.attributes, [str(x) for x in self])

    def __repr__(self):
        return str(self)


def parseusfm(infilename, parser, timeout=1e7, isdata=True):
    if isdata:
        dat = infilename
    elif hasattr(infilename, 'read'):
        dat = infilename.read().decode("utf-8")
    else:
        with open(infilename, encoding="utf-8") as inf:
            dat = inf.read()
    gs = GlobalState(dat, timeout=timeout)
    return parser.parse(usfmp.State(gs))

escapes = {
    '\\' : '\\',
    'n': '\n'
}

def expandescape(s):
    return re.sub(r'\\(.)', lambda m: escapes.get(m.group(1), "\\"+m.group(1)), s)

class UsfmParserBackend:
    _terminals = {
        'text': lambda **kw : Text(**kw),
        'ws': lambda **kw: String(r"\s", **kw),
        'word': lambda **kw: Text(**kw)
    }
    _grouptypes = {
        'sequence': "&",
        'choice': "|",
        'optional': "?",
        'zeroOrMore': "*",
        'oneOrMore': "+"
    }

    def __init__(self):
        self.references = {}
        self.elements = []
        self.nodes = []
        self.defines = {}
        self.defstack = []
        pass

    def _trimTo(self, curr):
        i = self.nodes.index(curr)
        self.nodes[:] = self.nodes[:i]

    def get_nodename(self):
        res = {}
        if len(self.nodes):
            res['to'] = self.nodes[-1].name
        return res

# --- Parser backend API

    def attrib_start(self, parser, e, context, name, **kw):
        if name == "*":
            name = "_default"
        group = Group(name=name, parent=context, mode="&",
                        result=(lambda r,s: Attribute(name, r, kw.get('fallback-from', None))),
                        **self.get_nodename())
        self.nodes.append(group)
        return group

    def attrib_end(self, parser, e, context, **kw):
        self._trimTo(context)
        return context

    def elem_start(self, parser, e, context, name, **kw):
        group = Group(name=name, parent=context, mode="&",
                    result=(lambda r,s: Element(r, name=name, propmap=s.propmap.copy())),
                    **self.get_nodename())
        self.nodes.append(group)
        return group

    def elem_end(self, parser, e, context, **kw):
        self._trimTo(context)
        return context

    def append_seq(self, context=None, to=None, **kw):
        return Group(parent=context, mode="&", **self.get_nodename(), **kw)

    def append_opt(self, context=None, to=None, **kw):
        return Group(parent=context, mode="?", **self.get_nodename(), **kw)

    def append_or(self, context=None, to=None, **kw):
        return Group(parent=context, mode="|", **self.get_nodename(), **kw)

    def append_plus(self, context=None, to=None, **kw):
        bet = context.properties.get("between", None)
        # handle "between"
        return Group(parent=context, mode="+", **self.get_nodename(), **kw)

    def append_star(self, context=None, to=None, **kw):
        return Group(parent=context, mode="*", **self.get_nodename(), **kw)

    def append_group(self, index, context=None, to=None, **kw):
        group = Group(parent=context, mode="&", **self.get_nodename(), **kw)
        return group

    def append_interleave(self, context=None, to=None, **kw):
        return Group(parent=context, mode="|+", **self.get_nodename(), **kw)

    def match(self, name, context, dump=False, to=None, **kw):
        if not len(name):
            return context
        if name[0] in "\"'":
            res = String(regex.escape(expandescape(name[1:-1])), parent=context, dump=dump, **self.get_nodename(), **kw)
        elif name.startswith("/"):
            res = String(name[1:-1], parent=context, dump=dump, **self.get_nodename(), **kw)
        else:
            res = self._terminals.get(name.lower(), lambda **kw: usfmp.Skip(**kw))(parent=context, dump=dump, **self.get_nodename(), **kw)
        context.append(res)
        return context

    def terminal(self, name, context, to=None, **kw):
        return self.match(name, context, dump=True, **self.get_nodename(), **kw)

    def backref(self, index, context=None, to=None, **kw):
        res = Reference(index, parent=context, **self.get_nodename(), **kw)
        context.append(res)
        return context

    def add_terminal(self, name, value, context, **kw):
        if value[0] in "\"'":
            res = lambda **kw: String(regex.escape(value[1:-1]), **kw)
        elif value[0].startswith("/"):
            res = lambda **kw: String(value[1:-1], **kw)
        self._terminals[name.lower()] = res

    def add_define(self, name, e, context=None, **kw):
        res = self.append_seq(context, inref=name)
        self.defines[name] = res
        return res

    def ref(self, name, context, **kw):
        res = self.defines[name]
        context.append(res)
        return res

