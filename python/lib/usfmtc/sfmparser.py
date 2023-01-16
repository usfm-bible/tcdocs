#!/usr/bin/python3

import re, logging
from dataclasses import dataclass
import xml.etree.ElementTree as et
import regex

logger = logging.getLogger("sfmparser")

class GlobalState:
    def __init__(self, txt):
        self.str = txt
        self.captures = []
        self.refs = {}
        self.defstack = []
        self.cstack = []

    def _ensure(self, index):
        if index >= len(self.captures):
            self.captures.extend([""] * (index - len(self.captures) + 1))

    def capture(self, index, txt):
        self._ensure(index)
        self.captures[index] += txt

    def init(self, index, txt):
        self._ensure(index)
        self.captures[index] = ""

    def getcapture(self, index):
        return self.captures[index]

    def pop(self):
        return self.captures.pop()

    def getref(self, name):
        return self.refs.get(name)

class State:
    def __init__(self, gs, pos=0):
        self.gs = gs
        self.pos = pos

    def __call__(self):
        return self.gs.str[self.pos:]

    def extend(self, offset):
        return State(self.gs, pos=self.pos + offset)

class PrintContext:
    def __init__(self):
        self.indent = 0

    def do_indent(self, indent=2):
        self.indent += indent

    def unindent(self, indent=2):
        self.indent = max(0, self.indent-indent)

    def str(self, s, index=0):
        return s.asstr(context=self)

class NoParseError(Exception):
    def __init__(self, msg='', state=None):
        self.msg = msg
        self.state = state

    def __str__(self):
        return self.msg

class Parser:
    debug = True #False

    def __init__(self, p, **kw):
        self.define(p)
        self.properties = {}
        p = kw.get('parent', None)
        self.index = getattr(p, 'index') + 1 if p is not None else 0
        self.to = kw.get('to', '')
        if 'inref' in kw:
            self.inref = kw['inref']

    def __str__(self):
        context = PrintContext()
        return context.str(self)

    def define(self, p):
        f = getattr(p, 'run', p)
        if self.debug:
            def lastof(l):
                return l[-1] if len(l) else ""
            def runfn(s, **kw):
                if not len(s()):
                    raise NoParseError("<EOF>", s)
                try:
                    res = f(s)
                    good = True
                    rese = None
                except NoParseError as e:
                    good = False
                    rese = e
                logger.debug('{}ing[{}/{}:{}.{}{}->{}] {} at {} = "{}"...'.format("match" if good else "fail", s.gs.defstack,
                        self.to, self.index, kw.get('index', ""), s.gs.cstack, repr(self),
                        getattr(self, 'name', 'UNK'),
                        s.pos, s()[:10].replace("\n", "\\n")))
                if rese is not None:
                    raise(rese)
                return res
        else:
            def runfn(s, **kw):
                if not len(s()):
                    raise NoParseError("<EOF>", s)
                return f(s)
        setattr(self, 'run', runfn)

    def run(self, s):
        """State -> (b, State)"""
        raise NotImplementedError('you must define() a parser')

    def parse(self, s):
        """State -> b"""
        try:
            (tree, _) = self.run(s)
        except NoParseError as e:
            if len(s()):
                tok = s()
                raise NoParseError('%s: %s' % (e.msg, tok), e.state)
        return tree

    def asstr(self, **kw):
        return ""

    def __repr__(self):
        return ""

    def merge(self, other, mode=None):
        return (self, other)

    def empty(self):
        return False


class String(Parser):
    def __init__(self, reg, dump=False, **kw):
        self.keep = not dump
        def text(s):
            m = regex.match(self.re, s())
            if not m:
                raise NoParseError(f'String ({self.re}) not found', s)
            return (m.group(1) if self.keep else None, s.extend(m.end()))
        super().__init__(text, **kw)
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


class Group(Parser):
    def __init__(self, *a, name="", mode="&", parent=None, result=None, capture=None, **kw):
        super().__init__(self, parent=parent, **kw)
        self.children = list(a)
        self.mode = mode
        self.result = result
        self.name = name + mode
        self.capture = capture
        self.propmap = {}
        if parent is not None:
            parent.append(self)

    def __repr__(self):
        return "Group[{}]{}".format(self.name, f"\u21D2{self.capture}" if self.capture else "")

    def asstr(self, context=None):
        ext = re.sub(r"[|&]", "", self.mode) + (f"\u21D2{self.capture}" if self.capture else "")
        sep = self.mode if self.mode == "|" else " "
        res = []
        if context is not None and len(self.children) > 1:
            context.do_indent()
        for i, x in enumerate(self.children):
            v = str(x) if context is None else context.str(x, index=i)
            if v != "":
                res.append(v)
        indent = 0 if context is None else context.indent
        if not len(self.children):
            return ""
        elif len(self.children) == 1:
            return sep.join(res) + ext
        else:
            context.unindent()
            return "( " + (sep+"\n"+(" "*indent)).join(res) + " )" + ext

    def run(self, s):
        done = False
        i = 0
        res = []
        cuts = s
        allfailed = True
        if self.mode == "|+":
            for c in self.children:
                c.mc = False
        if self.capture:
            s.gs.init(self.capture, "")
        s.gs.cstack.append(0)
        while self._loop(i):
            subres = []
            nohit = True
            for j, c in enumerate(self.children):
                if self.mode == "|+":
                    matched = c.mc
                news = cuts
                if (n := getattr(c, "inref", None)) is not None:
                    s.gs.defstack.append(n)
                s.gs.cstack[-1] += 1
                try:
                    (newv, news) = c.run(cuts, index=j)
                except NoParseError as e:
                    if n is not None:
                        s.gs.defstack.pop()
                    if self.mode.startswith('|') and (j < len(self.children) - 1 or not allfailed):
                        continue
                    elif any(x in self.mode for x in '?*') or ('+' in self.mode and i > 0):
                        done = True
                        break
                    else:
                        s.gs.cstack.pop()
                        raise e
                if n is not None:
                    s.gs.defstack.pop()
                if self.mode == "|+":
                    if matched and c.mc:
                        s.gs.cstack.pop()
                        raise NoParseError(f'Interleave multiply matched {c} in {self}', s)
                    elif cuts.pos != news.pos:  # real match
                        c.mc = True
                    else:
                        continue
                allfailed = False
                nohit = False
                cuts = news
                if newv is not None:
                    subres.append(newv)
                if self.mode.startswith('|'):
                    break
            else:
                if nohit:
                    break
            s = cuts
            if nohit and done:    # be greedy
                break
            if len(subres):
                res.append(subres)
            if self.mode in '?|':
                break
            i += 1
        s.gs.cstack.pop()
        return (self._returnRes(res, s), s)

    def append(self, parser):
        if len(self.children):
            lasts = self.children[-1].merge(parser, mode=self.mode)
            self.children = self.children[:-1] + list(lasts)
        else:
            self.children.append(parser)

    def _loop(self, i):
        if '*' in self.mode or '+' in self.mode:
            return True
        if i > 0:
            return False
        return True

    def _returnRes(self, res, s):
        if isinstance(res, list) and not len(res):
            return None
        if not any(x in self.mode for x in '*+'):
            if '?' in self.mode:
                res = res[0] if len(res) and not isinstance(res, str) else None
        while res is not None and len(res) == 1:
            if isinstance(res, (str, Attribute, Element)):
                break
            res = res[0]
        final = self.result(res, self) if self.result is not None else res
        if self.capture:
            s.gs.capture(self.capture, final)
        return final

    def empty(self):
        self.children = [x for x in self.children if not x.empty()]
        return len(self.children) == 0

def Skip(**kw):
    return Parser(lambda s:(None, s), **kw)

class Reference(Parser):
    def __init__(self, index, **kw):
        self.backref = index
        def test(s):
            v = s.gs.getcapture(self.backref)
            if s().startswith(v):
                return(v if not kw.get('dump', False) else None, s.extend(len(v)))
            else:
                raise NoParseError(f'String from backref (v) not found', s)
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
        if Parser.debug:
            logger.debug(f"Create Element({self})")

    def _append(self, e):
        if isinstance(e, Attribute):
            if self.propmap is not None and e.override is not None:
                self.attributes[self.propmap.get(self.attributes[e.override], e.name)] = e.value
            else:
                self.attributes[e.name] = e.value
        elif isinstance(e, list) and not isinstance(e, Element):
            for c in e:
                self._append(c)
        else:
            self.append(e)

    def asEt(self, parent=None):
        if parent is None:
            res = et.Element(self.name, attrib=self.attributes)
        else:
            res = et.SubElement(parent, self.name, attrib=self.attributes)
        res.set(' parent', parent)
        def asetchild(c, res):
            if isinstance(c, str):
                if len(res):
                    res[-1].tail = c if res[-1].tail is None else res[-1].tail + c
                else:
                    res.text = c if res.text is None else res.text + c
            elif isinstance(c, Element):
                c.asEt(res)
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


def parseusfm(infilename, parser):
    with open(infilename, encoding="utf-8") as inf:
        dat = inf.read()
    gs = GlobalState(dat)
    return parser.parse(State(gs))
    
        
class UsfmParserBackend:
    _terminals = {
        'text': lambda **kw : Text(**kw),
        'ws': lambda **kw: String("\s", **kw),
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
        group = Group(name=name, parent=context, mode="&",
                        result=(lambda r,s: Attribute(name, r, kw.get('name-override', None))),
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
        if name[0] in "\"'":
            res = String(regex.escape(name[1:-1]), parent=context, dump=dump, **self.get_nodename(), **kw)
        elif name.startswith("/"):
            res = String(name[1:-1], parent=context, dump=dump, **self.get_nodename(), **kw)
        else:
            res = self._terminals.get(name.lower(), lambda **kw: Skip(**kw))(parent=context, dump=dump, **self.get_nodename(), **kw)
        context.append(res)
        return context

    def terminal(self, name, context, to=None, **kw):
        return self.match(name, context, dump=True, **self.get_nodename(), **kw)

    def backref(self, index, context=None, to=None, **kw):
        res = Reference(index, parent=context, **self.get_nodename(), **kw)
        context.append(res)
        return context

    def add_terminal(self, name, value, **kw):
        if value[0] in "\"'":
            res = lambda **kw: String(regex.escape(value[1:-1]), **kw)
        elif value[0].startswith("/"):
            res = lambda **kw: String(value[1:-1], **kw)
        self._terminals[name.lower()] = res

    def add_define(self, name, e, **kw):
        res = self.append_seq(inref=name)
        self.defines[name] = res
        return res

    def ref(self, name, context, **kw):
        res = self.defines[name]
        context.append(res)
        return res

