import usfmtc.railroad as rr

usfmns = "{http://usfm.bible/parse/2023}"

CSS_STYLE = '''
    svg.railroad-diagram {{
        background-color: hsl(30,20%,95%);
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
        stroke: black;
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
    svg.railroad-diagram g.altterminal rect {{
        fill: {altcolor}
    }}
'''

class UsfmRailRoad:
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
            'altcolor': 'rgb(251, 252, 207)',
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

    def append_or(self, context=None, groupby=0, **kw):
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

    def match(self, txt, context, alt=None, **kw):
        cls = {k: kw.get(k, None) for k in ('href',)}
        if alt is None or not len(alt):
            lcontext = context
        else:
            lcontext = self.append_or(context)
            lcontext.append(self.WrappedRail(rr.Terminal(alt, **cls), lcontext))
            cls["cls"] = "altterminal"
        lcontext.append(self.WrappedRail(rr.Terminal(txt, **cls), lcontext))
        return context

    def terminal(self, name,  context, **kw):
        context.append(self.WrappedRail(rr.NonTerminal(name), context))
        return context

    def backref(self, index, context=None, **kw):
        context.append(self.WrappedRail(rr.Terminal("\u21D0 {}".format(chr(0x278A + index))), context))
        return context

    def add_terminal(self, name, value, context, **kw):
        self.terminals[name] = value

    def add_define(self, name, e, context=None, box=False, **kw):
        if box:
            bres = self.WrappedRailList(rr.Group, context, name, swap=True)
            context.append(bres)
            res = self.append_seq(context=bres)
        else:
            res = self.append_seq(context=context)
        self.defines[name] = res
        return res

    def ref(self, name, res, **kw):
        return self.terminal(name, res)

    def end_ref(self, e, name, **kw):
        pass


class XmlRailRoad(UsfmRailRoad):

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

