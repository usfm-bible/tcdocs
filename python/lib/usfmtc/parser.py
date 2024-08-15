
import logging, time, re

logger = logging.getLogger(__name__)

class GlobalState:
    def __init__(self, timeout=1e7):
        self.defstack = []
        self.cstack = []
        self.lasterror = None
        self.time = time.time() + timeout

    def __call__(self):
        return self

    def __getitem__(self, key):
        raise NotImplementedError("Indexing not implemented")


class State:
    def __init__(self, gs, pos=0):
        self.gs = gs
        self.pos = pos

    def copy(self):
        return self.__class__(self.gs, self.pos)

    # Assumes gs is string like somewhat
    def __call__(self):
        return self.gs[self.pos:]

    def extend(self, offset):
        res = self.copy()
        res.pos = self.pos + offset
        return res

    def atend(self):
        return len(self.gs()) - self.pos == 0

    # Definitely expects gs to 'be' a string
    def getcontext(self):
        s = self.gs()
        end = s.find("\n", self.pos)
        if end == 0:
            end = s[self.pos + 1:].find("\n") + 1
        tok = s[self.pos:end] if end >= 0 else s[self.pos:]
        return tok

    def debug(self, good, to, index, kwindex, rep, name, respos):
        return '{}ing[{}/{}:{}.{}{}->{}] {} at {}->{} = "{}"...'.format("match" if good else "fail", self.defstack,
                    to, index, kwindex, "["+",".join(map(str, self.cstack))+"]", rep, name, self.pos, respos, self()[:10].replace("\n", "\\n"))

    @property
    def lasterror(self):
        return self.gs.lasterror

    @lasterror.setter
    def lasterror(self, val):
        self.gs.lasterror = val

    @property
    def cstack(self):
        return self.gs.cstack

    @property
    def defstack(self):
        return self.gs.defstack


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
            def runfn(s, **kw):
                try:
                    res = f(s)
                    rese = None
                except NoParseError as e:
                    res = None
                    rese = e
                logger.debug(s.debug(rese is None, self.to, self.index, kw.get('index', ''), repr(self), getattr(self, 'name', 'UNK'),
                                     (res[1].pos if res is not None else "?")))
                if time.time() > s.gs.time:
                    raise TimeoutError()
                if rese is not None:
                    raise(rese)
                return res
        else:
            def runfn(s, **kw):
                if s.atend():
                    raise NoParseError("<EOF>", s)
                return f(s)
        setattr(self, 'run', runfn)

    def run(self, s):
        """State -> (b, State)"""
        raise NotImplementedError('you must define() a parser')

    def parse(self, s):
        """State -> b"""
        try:
            (tree, finals) = self.run(s)
        except NoParseError as e:
            if not s.atend():
                tok = e.state.getcontext()
                raise NoParseError('%s: %s' % (e.msg, tok), e.state)
        if not finals.atend():
            if finals.lasterror is not None:
                tok = finals.lasterror.state.getcontext()
                raise NoParseError("{}: {}".format(finals.lasterror.msg, tok), finals.lasterror.state)
            else:
                tok = finals.getcontext()
                raise NoParseError("Incomplete match: {}".format(tok), finals)
        return tree

    def asstr(self, **kw):
        return ""

    def __repr__(self):
        return ""

    def merge(self, other, mode=None):
        return (self, other)

    def empty(self):
        return False


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
        s.cstack.append(0)
        while self._loop(i):
            subres = []
            nohit = True
            for j, c in enumerate(self.children):
                if self.mode == "|+":
                    matched = c.mc
                news = cuts
                if (n := getattr(c, "inref", None)) is not None:
                    s.defstack.append(n)
                s.cstack[-1] += 1
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
                        s.cstack.pop()
                        s.lasterror = e
                        if self.capture:
                            s.gs.release(self.capture)
                        raise e
                if n is not None:
                    s.defstack.pop()
                if self.mode == "|+":
                    if cuts.pos != news.pos and matched and c.mc:
                        if self.capture:
                            s.gs.release(self.capture)
                        s.cstack.pop()
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
        if self.capture:
            s.gs.release(self.capture)
        s.cstack.pop()
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
        if not any(x in self.mode for x in '*+&'):
            if '?' in self.mode:
                res = res[0] if len(res) and not isinstance(res, str) else None
        return res

    def empty(self):
        self.children = [x for x in self.children if not x.empty()]
        return len(self.children) == 0

def Skip(**kw):
    return Parser(lambda s:(None, s), **kw)

