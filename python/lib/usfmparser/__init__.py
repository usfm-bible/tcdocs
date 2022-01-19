#!/usr/bin/python3

import os, argparse, logging, re
from .fparser import createParser, make_tokenizer, debug_print
from .funcparserlib import parser as fpp
from .funcparserlib.parser import some, finished, oneplus
from .funcparserlib.lexer import Token
from .usxmodel import usx, char, para, chapter, verse, note, book, milestone, figure, optbreak

def style_error(e, prefix=""):
    res = prefix + e[0] + "at {}".format(e[1])
    return res

def flatten_content(content, strip=False):
    res = []
    if content is None:
        return res
    for c in content:
        if isinstance(c, (list, tuple)):
            res.extend(flatten_content(c))
        elif c is not None:
            res.append(c)
    if strip and len(res):
        if isinstance(res[0], str):
            res[0] = res[0].lstrip()
        if isinstance(res[-1], str):
            res[-1] = res[-1].rstrip()
    return res

def isempty(s):
    return s is None or re.match(r"^\s*$", s)

class UsfmParser:
    _tokenspecs = [
        ('EndTag',      (r"\\(?P<embed>\+?)(?P<tname>[a-z][a-z0-9]*)?\*", )),
        ('Tag',         (r"\\(?P<embed>\+?)(?P<tname>[a-z][a-z0-9]*)(?:\s|(?!\*))", )),
        ('Attribute',   (r"(?P<key>[a-z][a-z0-9]*)\s*=\"(?P<val>.*?)\"\s*", )),
        ('Pipe',        (r"\|", )),
        ('Word',        (r"[^\s\\\|]+?(?=[\\\s|]|$)", )),
        ('Ws',          (r"\s", ))
    ]

    def __init__(self):
        self._tags = {}
        self.initbook()

    def initbook(self):
        self.currchap = None
        self.currverse = None
        self.errors = []
        self.bkid = None

    def _readstylesheet(self, fname):
        currtag = None
        with open(fname, encoding="utf-8") as inf:
            for l in inf.readlines():
                m = re.match(r"^(?:#!)?\s*\\(\S+)\s*(.*?)$", l.strip())
                if m is None:
                    continue
                mkr = m.group(1)
                val = m.group(2)
                if mkr == "Marker":
                    currtag = val
                    self._tags[currtag] = {}
                else:
                    self._tags[currtag][mkr] = val

    def _tokenize(self, content):
        t = make_tokenizer(self._tokenspecs)
        return list(t(content))

    def Tag(self, test):
        return some(lambda t: t.type == "Tag" and t.tname == test)

    def _tagtype(self, tag):
        return self._tags.get(tag, {}).get('StyleType', '').lower()

    def TagType(self, test):
        return some(lambda t: t.type == "Tag" and t.embed == "" and self._tagtype(t.tname) == test.lower())

    def EndTag(self, name=None):
        return some(lambda t: t.type == "EndTag" and t.embed == "" and (name is None or t.tname == name))

    def TagEmbed(self):
        return some(lambda t: t.type == "Tag" and t.embed == "+" and self._tagtype(t.tname) == "character")

    def EndTagEmbed(self):
        def _tt(t):
            if t.type == 'EndTag':
                return t.embed == "+"
            return False
        return some(_tt)

    def TagUnknown(self):
        return some(lambda t: t.type == "Tag" and t.tname not in self._tags)

    def CmpTag(self, opening, ending):
        if opening is None or ending is None:
            return True
        if opening.type != "Tag":
            return False
        if ending.type != "EndTag":
            return False
        if opening.embed != ending.embed:
            return False
        if opening.tname != ending.tname:
            return False
        return True

    def streq(self, t, test):
        if test == r"\n":
            test = "\n"
        return t.value == test

    def strneq(self, t, test):
        if test == r"\n":
            test = "\n"
        return t.value != test

    def Word(self):
        return oneplus(some(lambda t: t.type in ("Word", "Pipe"))) >> self.merge_tokens

    def Ws(self):
        return some(lambda t: t.type == "Ws")

    def Pipe(self):
        return some(lambda t: t.type == "Pipe")

    def TokenType(self, test):
        return some(lambda t: t.type == test)

    def finished(self):
        return finished

    def merge_tokens(self, b):
        res = Token(b[0].type, "".join(x.value for x in b), b[0].start, b[-1].end)
        return res

    def make_usx(self, i, c):
        content = flatten_content([i] + c)
        return usx(attrib={"version": "2.0"}, *content)

    def make_id(self, tag, idword, idline):
        if idline is None:
            idline = ""
        self.bkid = idword.value
        return book(attrib={'style': tag.tname, 'code': self.bkid}, *[idline])

    def make_para(self, tag, content):
        content = flatten_content(content, strip=True)
        try:
            return para(attrib={'style': tag.tname}, *content)
        except ValueError:
            return para(attrib={'style': tag.tname, 'error': '1'})

    def make_chapter(self, tag, content):
        cid = "{} {}".format(self.bkid, content.value)
        self.currchap = chapter(attrib={'style': tag.tname, 'number': content.value, 'sid': cid})
        return self.currchap

    def make_alt(self, token, content, base):
        base.set("altnumber", content)
        return base

    def make_pub(self, token, content, base):
        self.currverse.set("pubnumber", content)
        return base

    def make_char(self, tag, c):
        return char(attrib={'style': tag.tname}, *c)

    def make_verse(self, tag, content):
        sid = "{}:{}".format(self.currchap.get('sid'), content.value)
        self.currverse = verse(attrib={'style': tag.tname, 'number': content.value, 'sid': sid})
        return self.currverse

    def make_note(self, tag, caller, content):
        content = [c for c in content if c is not None]
        return note(attrib={'style': tag.tname, 'caller': caller.value}, *content)

    def make_milestone(self, tag, content):
        attribs = {'style': tag.tname}
        if content is not None:
            for v in content:
                attribs[v.key] = v.val
        return milestone(attrib=attribs)

    def make_fig(self, tag, content):
        values = content.split("|") if content is not None else [""]
        attribs = {'style': tag.tname}
        for i, a in enumerate(("file", "size", "loc", "copy", "alt", "ref")):
            if i+1 >= len(values):
                break
            attribs[a] = values[i+1]
        return figure(attrib=attribs, *[values[0]])

    def make_figattrib(self, tag, content, attr):
        content = flatten_content(content, strip=True)
        attribs = {'style': tag.tname}
        if attr is not None:
            for v in attr:
                attribs["file" if v.key == "src" else v.key] = v.val
        return figure(attrib=attribs, *content)

    def make_break(self):
        return optbreak()

    def do_error(self, label, token):
        self.errors.append((label, token))
        return None

    def str_join(self, *content):
        out = []
        for i, a in enumerate(content):
            if isinstance(a, Token):
                v = a.value
                if v == "\n":
                    if i < len(content) - 1:
                        v = v[:-1] + " "
                    else:
                        v = v[:-1]
                out.append(v)
            elif isinstance(a, (list, tuple)):
                out.append(self.str_join(*a))
        return "".join(out)

    def dump(self, *content):
        pass

    def cleanup_usx(self, usx):
        ''' Inserts verse and chapter eid elements appropriately '''
        lastv = None
        for v in usx.findall('.//verse'):
            if lastv is None:
                lastv = v
                continue
            eid = lastv.get('sid')
            ev = verse(attrib={'eid': eid})
            pv = v.getparent()
            pl = lastv.getparent()
            if id(pv) == id(pl):
                v.addprevious(ev)
            else:
                endp = pl
                pl = pl.getnext()
                block = False
                while id(pl) != id(pv):
                    if pl.tag == 'para' and self._tags.get(pl.get('style'), {}).get('TextType', '') != 'Section':
                        if not block:
                            pl.set('vid', eid)
                            endp = pl
                    else:
                        block = True
                    pl = pl.getnext()
                if not block and pv.index(v) > 0 or not isempty(pv.text):
                    v.addprevious(ev)
                else:
                    endp.append(ev)
            lastv = v
        if lastv is not None:
            eid = lastv.get('sid')
            ev = verse(attrib={'eid': eid})
            pl = lastv.getparent()
            endp = pl
            block = False
            while pl is not None:
                if pl.tag == 'para' and self._tags.get(pl.get('style'), {}).get('TextType', '') != 'Section':
                    if not block:
                        pl.set('vid', eid)
                        endp = pl
                else:
                    block = True
                pl = pl.getnext()
            endp.append(ev)

        lastc = None
        for c in usx.findall('.//chapter'):
            if lastc is not None:
                c.addprevious(chapter(attrib={'eid': lastc.get('sid')}))
            lastc = c
        if lastc is not None:
            usx.append(chapter(attrib={'eid': lastc.get('sid')}))

        return usx
