#!/usr/bin/python3

from .funcparserlib.parser import finished, some, a, pure, maybe, skip, oneplus, \
                          forward_decl, Parser, NoParseError, State, _Tuple, _Ignored
from .funcparserlib import parser as fpp
from .funcparserlib.lexer import Token, LexerError
from functools import reduce
import logging, re, types

def dummy_print(s):
    pass

debug_print = dummy_print

class NoParseFail(Exception):
    def __init__(self, msg="", state=None):
        self.msg = msg
        self.state = state

    def __str__(self):
        return self.msg

def make_tokenizer(specs):
    """[(str, (str, int?))] -> (str -> Iterable(Token))"""

    def compile_spec(spec):
        name, args = spec
        return name, re.compile(*args)

    compiled = [compile_spec(s) for s in specs]

    def match_specs(specs, str, i, position):
        line, pos = position
        for type, regexp in specs:
            m = regexp.match(str, i)
            if m is not None:
                value = m.group()
                nls = value.count('\n')
                n_line = line + nls
                if nls == 0:
                    n_pos = pos + len(value)
                else:
                    n_pos = len(value) - value.rfind('\n') - 1
                res = Token(type, value, (line, pos + 1), (n_line, n_pos))
                for k, v in m.groupdict().items():
                    if v is not None:
                        setattr(res, k, v)
                return res
        else:
            errline = str.splitlines()[line - 1]
            raise LexerError((line, pos + 1), errline)

    def f(str):
        length = len(str)
        line, pos = 1, 0
        i = 0
        while i < length:
            t = match_specs(compiled, str, i, (line, pos))
            yield t
            line, pos = t.end
            i += len(t.value)

    return f

def makeerrmsg(t):
    if isinstance(t, Token):
        if t.start is None or t.end is None:
            loc = ""
        else:
            loc = "{0[0]},{0[1]}-{1[0]},{1[1]}: ".format(t.start, t.end)
        msg = "{}: {} at {}".format(e.msg, t, loc)
    else:
        msg = "{}: {}".format(e.msg, t)
    return msg

def parse(self, tokens):
    try:
        (tree, _) = self.run(tokens, State())
        return tree
    except NoParseError as e:
        max = e.state.max
        if len(tokens) > max:
            t = tokens[max]
            msg = makerrmsg(t)
        else:
            msg = "Got unexpected end of file"
        #if e.state is not None:
        #    msg = "{}, expected: {}".format(msg, e.state.parser.name)
        e.msg = msg
        raise
    except NoParseFail as e:
        e.msg += " at {}".format(e.state.pos)
        raise
Parser.parse = parse

def magic(v1, v2):
    vs = [v for v in [v1, v2] if not isinstance(v, _Ignored)]
    if len(vs) == 1:
        return vs[0]
    elif len(vs) == 2:
        if isinstance(vs[0], _Tuple):
            return _Tuple(v1 + (v2,))
        else:
            return _Tuple(vs)
    else:
        return _Ignored(())

def __add__(self, other):
    @Parser
    def _add(tokens, s):
        (v1, s2) = self.run(tokens, s)
        if not hasattr(s2, 'vars'):
            s2.vars = dict(getattr(s, 'vars', {}).items())
        s2.vars[self.name] = v1
        (v2, s3) = other.run(tokens, s2)
        debug_print("Doing {}: {} + {}: {}".format(self.name, self, other.name, other))
        s3.vars = dict(getattr(s2, 'vars', {}).items())
        s3.vars[other.name] = v2
        return magic(v1, v2), s3

    # or in terms of bind and pure:
    # _add = self.bind(lambda x: other.bind(lambda y: pure(magic(x, y))))
    _add.name = '(%s , %s)' % (self.name, other.name)
    debug_print("adding: {} as {}".format(_add.name, _add))
    return _add
Parser.__add__ = __add__

def __or__(self, other):
    @Parser
    def _or(tokens, s):
        try:
            return self.run(tokens, s)
        except NoParseError as e:
            s1 = State(s.pos, e.state.max)
            s1.vars = getattr(s, 'vars', {})
            return other.run(tokens, s1)

    _or.name = '(%s | %s)' % (self.name, other.name)
    return _or

def __run__(self, tokens, s):
    v, news = self._run(tokens, s)
    debug_print("trying {}: {} -> {}".format(self.name, self, v))
    if not hasattr(news, 'vars'):
        news.vars = dict(getattr(s, 'vars', {}).items())
    news.vars[self.name] = v
    return v, news
Parser.run = __run__

def defparse(self, p):
    f = getattr(p, 'run', p)
    setattr(self, '_run', f)
Parser.define = defparse

def many(p):
    @Parser
    def _many(tokens, s):
        """Iterative implementation preventing the stack overflow."""
        res = []
        try:
            while True:
                (v, s) = p.run(tokens, s)
                res.append(v)
        except NoParseError as e:
            s1 = State(s.pos, e.state.max)
            s1.vars = getattr(s, 'vars', {})
            return res, s1

    _many.name = '{ %s }' % p.name
    return _many

def createParser(grtext, results, gvars=None, debug=False):
    opmap = {"+": "__add__", "|": "__or__", "%": "__mod__"}
    modmap = {"+": oneplus, "*": many, "?": maybe}

    if debug:
        fpp.debug = True
        debug_print = print
    else:
        debug_print = dummy_print

    def tokenize(s):
        specs = [
            ("Space",   (r"[ \t\r\n]+", )),
            ("Regex",   (r"r([\"']).*?(\1(?<!\\)|\n)", )),
            ("String",  (r"([\"']).*?(\1(?<!\\)|\n)", )),
            ("Comment", (r"#.*", )),
            ("Func",    (r"(?P<fname>[A-Za-z_][A-Za-z_0-9]*)\((?P<params>.*?)\)", )),
            ("Name",    (r"[A-Za-z_][A-Za-z_0-9]*", )),
            ("Op",      (r"[:?*+%|{}<>=;.()]", )),
            ("Any",     (r".", ))
        ]
        useless = ["Space", "Comment"]
        t = make_tokenizer(specs)
        return [x for x in t(s) if x.type not in useless]

    def tok(k):
        return lambda t: t.type == k
    def tokval(k, s):
        return lambda t: t.type == k and t.value == s
    def op(s):
        return some(tokval("Op", s)).named("(Op: %s)" % s)
    def skipop(s):
        return skip(some(tokval("Op", s))).named("(skip Op: %s)" % s)
    def notop(s):
        return some(lambda t: t.type != "Op" or t.value != s).named("(Op not: %s)" % s)

    def make_ret(b):
        return b
    def make_name(b):
        n = b.value
        @Parser
        def _doname(t, s):
            return results[n].run(t, s)
        _doname.name = n
        return _doname
    def make_regex(b):
        return some(lambda t: re.match(b, t.value) is not None).named("(regex: %s)" % b)
    def make_string(b):
        return some(lambda t: t.value == b).named("(string: %s)" % b)
    def make_func(b):
        return eval(b.value, gvars, None)

    def make_seq(b):
        res = b[0]
        for a in b[1:]:
            res = res + a
        debug_print(f"make_seq: Joining sequence {b} to make {res}")
        return res
    def make_choice(b):
        res = b[0]
        for a in b[1]:
            res = res | a
        return res
    def make_named(b):
        if b[0] is not None:
            b[1].named(b[0].value)
        debug_print(f"make_named: Changing name of {b[1]} {b[1].name} to {b[0]}")
        return b[1]
    def make_rule(b):
        debug_print(f"make_rule {b}")
        if b[0] is not None:
            n = b[0].value
            if n in results:
                results[n].define(b[1])
            else:
                results[n] = b[1]
            results[n].named(n)
            debug_print(f"Defining: {b[0].value}")
        return b[1]

    def make_mod(b):
        if b[1] is not None:
            res = modmap[b[1].value](b[0]).named(b[0].name)
        else:
            res = b[0]
        debug_print(f"make_mod {b}, returning {res}")
        return res

    def make_cond(b):
        debug_print(f"make_cond: {b}")
        p, c = b
        if c is None:
            return p
        cond = c.value
        @Parser
        def _pcond(t, s):
            v1, s2 = p.run(t, s)
            if not hasattr(s2, 'vars'):
                s2.vars = getattr(s, 'vars', {})
            s2.vars[p.name] = v1
            # import pdb; pdb.set_trace()
            if not eval(cond, gvars, s2.vars):
                raise NoParseError("Condition %s failed" % cond, s)
            return v1, s2
        _pcond.name = p.name
        debug_print("Creating condition: {} {} becomes {}".format(p.name, p, _pcond))
        return _pcond
    def make_action(b):
        debug_print(f"make_action: {b}")
        p, a = b
        if a is None:
            return p
        action = a.value
        @Parser
        def _pact(t, s):
            v1, s1 = p.run(t, s)
            if not hasattr(s1, 'vars'):
                s1.vars = {}
            #print(s1.vars)
            v1 = eval(action, gvars, s1.vars)
            return v1, s1
        _pact.name = p.name
        debug_print("Creating action: {} {} becomes {}".format(p.name, p, _pact))
        return _pact
    def do_errortoken(txt):
        def _doerror(b):
            raise NoParseFail("Syntax Error: {}".format(txt), State(b.start, b.end))
        return _doerror

    '''
    rule = ruleid choice action? ';' {make_rule};
    ruleid = Name ':';
    action = '{' char* '}';
    choice = Seq ('|' seq)*;
    Seq = Elem_main+ {make_seq};
    Elem_main = Elem Modifier? { make_mod };
    Elem = Item Condition? { make_cond };
    Item = (Name '=')? Elem_term { make_named };
    Elem_term = subexpr | term;
    Modifier = '?' | '*' | '+';
    Condition = '<' char* '>';
    subexpr = '(' choice ')';
    term = Name {make_name}
        | String {make_string}
        | Regex {make_regex};
    '''
    name = some(tok("Name")).named("Name")
    #term = (name >> make_name) | (some(tok("String")) >> make_string) | (some(tok("Regex")) >> make_regex)
    term = (name >> make_name) | (some(tok("String")).named("String") >> make_string) \
                               | (some(tok("Regex")).named("Regex") >> make_regex) \
                               | (some(tok("Func")).named("Func") >> make_func)
    choice = forward_decl().named("choice")
    subexpr = skipop('(') + choice + skipop(')')
    cond = skipop("<") + notop(">") + skipop(">")
    cond.name = 'Condition'
    modifier = op("?") | op("*") | op("+")
    modifier.name = 'Modifier'
    elemterm = subexpr | term
    elemterm.name = 'Elem_term'
    item = maybe(name + skipop('=')) + elemterm >> make_named
    item.name = "Item"
    elem = (item + maybe(cond)) >> make_cond
    elem.name = 'Elem'
    elemmain = (elem + maybe(modifier)) >> make_mod
    elemmain.name = 'Elem_main'
    seq = oneplus(elemmain) >> make_seq
    seq.name = 'Seq'
    choice.define((seq + many(skipop("|") + seq)) >> make_choice)
    action = skipop('{') + notop("}") + skipop('}')
    ruleid = name + skipop(':')
    rule = ((ruleid + ((choice + maybe(action)) >> make_action)) >> make_rule) + (skipop(';') | (name >> do_errortoken("Missing ;")))
    pegparser = many(rule) + finished
    tokens = tokenize(grtext)
    res = pegparser.parse(tokens)
    return res

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-g','--grammar',required=True,help="input grammar")
    parser.add_argument('-d','--debug',action='store_true',help='Run parser in debug')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(filename="fparser.log", level=logging.DEBUG)
        fpp.debug = True
    with open(args.grammar) as inf:
        gr = inf.read()
        results = {}
        pegparser = createParser(gr, results)

