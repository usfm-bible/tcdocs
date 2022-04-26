#!/usr/bin/python3

from usfmtc import railroad
from usfmtc.railroad import Diagram, Choice, Optional, Terminal, NonTerminal, Sequence, DEFAULT_STYLE, Group, Sequence, OneOrMore, ZeroOrMore, HorizontalChoice, Stack, Comment, MultipleChoice

def bigChoice(e, t, c, default=0, **kw):
    if len(c) == 0:
        return None
    elif len(c) < e.groupby + 2:
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

rmanys = {v:k for k,v in manys.items()}

CSS_STYLE = '''\
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

class RChoice(list):
    def __init__(self, *a, combine="choice", parent=None, groupby=8):
        super().__init__(a)
        if combine == "group":
            combine = "sequence"
        self.combine = combine
        self.parent = parent
        self.groupby = groupby
        self.repeat = None

    def asRail(self):
        if not len(self):
            return None
        if self.combine == "interleave":
            opts = []
            nonopts = []
            for e in self:
                if isinstance(e, RChoice):
                    if e.combine == "optional":
                        if len(e):
                            opts.append(e[0])
                        continue
                nonopts.append(e)
            rep = self.repeat.asRail() if self.repeat is not None else None
            ocontents = [r for r in (v.asRail() for v in opts) if r is not None]
            o = None
            if len(ocontents):
                o = ZeroOrMore(Choice(0, *ocontents), rep) if len(opts) else None
            ncontents = [r for r in (v.asRail() for v in nonopts) if r is not None] + ocontents
            n = None
            if len(ncontents):
                n = MultipleChoice(0, "all", *ncontents) if len(nonopts) else None
            if n is None:
                return o
            else:
                return n
        contents = [r for r in (v.asRail() for v in self) if r is not None]
        if not len(contents):
            return None
        if len(contents) > 1 and self.combine not in ("choice", "sequence", "stack", "attributed", "attributes"):
            contents = [actions["sequence"](self, None, contents)]
        if len(contents) < 2 and self.combine in ("choice", "sequence", "stack", "attributed", "attributes"):
            return contents[0]
        elif len(contents):
            return actions[self.combine.lower()](self, self.combine, contents)
        return None

    def append(self, val):
        super().append(val)

    def mergemany(self, many):
        mymany = rmanys.get(self.combine, '')
        s = many+mymany
        if '*' in s:
            return '*'
        elif s == '?+' or s == '+?':
            return '*'
        elif s == '??':
            return '?'
        elif s == '++':
            return '+'
        else:
            return s


class RTerminal:
    def __init__(self, text, parent=None, ref=False, focus=False):
        self.text = text
        self.parent = parent
        self.focus = focus
        self.ref = ref

    def asRail(self):
        res = actions[("non" if self.ref else "")+"terminal"](self, self.text, None)
        if self.focus:
            res.cls = 'highlight'
        return res


class RGroup(list):
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

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


class SplitRail:
    def __init__(self, curr, isstack=False):
        self.all = RChoice(combine="attributed", parent=curr)
        self.seq = RChoice(combine="sequence", parent = self.all)
        if isstack:
            self.main = RChoice(self.seq, combine="stack", parent=self.all)
            self.seq.parent = self.main
        else:
            self.main = self.seq
        self.all.append(self.main)
        self.mod = ""

    def setmod(self, modifier):
        self.mod = modifier

    def append(self, e):
        self.main.append(e)

    def newattrib(self, name):
        res = RChoice(RTerminal("@"+name+self.mod, parent=self.all), combine="sequence")
        self.all.insert(-1, res)    # self.all[-1] == self.main (the mainline content)
        return res

    def finishAttribute(self, last):
        last = getlastchoice(last)
        if last is not None:
            last.combine = "attributes"

    def finish(self):
        if len(self.all):
            children = self.all[:]
            self.all.clear()
        for a in children:
            if isinstance(a, RChoice) and rmanys.get(a.combine, '') != '':
                for c in a:
                    if isinstance(c, RChoice) and c.combine == 'sequence' and isinstance(c[0], RTerminal):
                        c.name += rmanys[a.combine]
                    self.all.append(c)
                    c.parent = self.all
            else:
                self.all.append(a)

    def asRail(self):
        return self.all.asRail()


class SFMRail:
    def __init__(self):
        pass

    def output(self, top, **kw):
        defaults = {
            'font': 'DejaVu Sans',
            'text-size': '12px',
            'comment-size': '14px',
            'color': 'rgb(210, 255, 210)',
            'line-width': '2'}
        defaults.update(kw)
        content = top.asRail()
        res = Diagram(content, type='complex', css=CSS_STYLE.format(**defaults))
        return res

    def sequence(self, combine="sequence", parent=None, groupby=8):
        #if parent is not None and isinstance(parent, SplitRail):
        #    parent.setmod(rmanys.get(combine, ""))
        #    return parent
        #else:
        return RChoice(combine=combine, parent=parent, groupby=groupby)

    def terminal(self, name, curr, ref=False):
        return RTerminal(name, parent=curr, ref=ref)

    def group(self, name, curr):
        res = RGroup(name, parent=curr)
        #ncurr = self.sequence(parent=res)
        #res.append(ncurr)
        if curr is not None:
            curr.append(res)
        return res

    def refgroup(self, num, curr):
        return self.group(chr(0x278A + num), curr)

    def backref(self, parser, group, tid, refs, curr):
        f = (group, tid)
        if f not in refs:
            p = curr
            while p is not None:
                if isinstance(p, RGroup):
                    f = (p.name, tid)
                    if f in refs:
                        break
                    p = p.parent
        c = refs[f]
        t = self.terminal('\u21D0 {}'.format(chr(0x278A + c)), curr)
        curr.append(t)

    def lookahead(self, val, curr):
        return self.terminal('\u21D2 {}'.format(val), curr)

    def lookbehind(self, val, curr):
        return self.terminal('\u21D0 {}'.format(val), curr)

    def addrepeat(self, rep, curr):
        if isinstance(curr, RChoice):
            curr.repeat = rep

# Methods needed for processing XML
    def elementStart(self, name, curr, isstack=False):
        res = SplitRail(curr, isstack)
        return res

    def elementEnd(self, curr):
        curr.finish()

    def attributeStart(self, name, curr):
        scurr = curr
        currmany = ""
        while scurr is not None and not isinstance(scurr, SplitRail):
            if isinstance(scurr, RChoice):
                currmany = scurr.mergemany(currmany)
            scurr = scurr.parent
        if scurr is None:
            scurr = curr
        if currmany == "+":
            currmany = ""
        elif currmany == "*":
            currmany = "?"
        if not isinstance(scurr, SplitRail):
            scurr.append(RTerminal("@"+name+currmany, scurr))
            return scurr
        else:
            return scurr.newattrib(name+currmany)

    def attributeEnd(self, base, last):
        if isinstance(base, SplitRail):
            base.finishAttribute(last)
