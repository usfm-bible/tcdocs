#!/usr/bin/env python3

from typing import Optional, List, Tuple
from dataclasses import dataclass
import re

@dataclass
class MarkerRef:
    mrkr: str
    index: Optional[int] = None
    word: Optional[int] = None
    char: Optional[str] = None

    def __eq__(self, context:'MarkerRef'):
        if self.mrkr != context.mrkr:
            return False
        elif self.index != context.index:
            return False
        elif self.word != context.word:
            return False
        elif self.char != context.char:
            return False

    def __str__(self):
        return self.str(force=True)

    def str(self, context: Optional['MarkerRef']=None, force: bool=False):
        res = []
        if force or context is None or context.mrkr != self.mrkr or context.index != self.index:
            res.append("!"+self.mrkr)
            if self.index is not None:
                res.append("[" + str(self.index) + "]")
        if self.word is not None and (force or context is None or context.word != self.word):
            if len(res):
                res.append("!")
            res.append(str(self.word))
        if self.char is not None and (force or context is None or context.char != self.char):
            if len(res):
                res.append("+")
            res.append(str(self.char))
        return "".join(res)


_regexes = {
    "book": r"""(?P<transid>(?:[a-z0-9_-]*[+])*)
                    (?P<book>(?:[A-Z][A-Z0-9][A-Z0-9]|[0-9](?:[A-Z][A-Z]|[0-9][A-Z]|[A-Z][0-9])))
                    \s*{chap}""",
    "id": r"(?:[a-z][a-z0-9_-]*[a-z0-9]?)",
    "charref": r"(?:(?:[0-9]|end)[+]?)",
    "wordrefanon": r"",
    "mrkref": r"(?:\!{id}(?:\[[0-9]\])?(?:\!(?:[0-9|end)(?:[+]{charref})?)?)",
    "wordrefonly": r"(?P<word>[0-9]|end)(?P<char>[+]{charref})?",
    "wordref1": r"""(?:(?: \!(?P<word1>[0-9]|end)(?:[+](?P<char1>{charref}))?
                          |(?P<mrk1>{mrkref}))
                       (?P<mrkn1>{mrkref}*))""",
    "wordref2": r"""(?:(?: \!(?P<word2>[0-9]|end)(?:[+](?P<char2>{charref}))?
                          |(?P<mrk2>{mrkref}))
                       (?P<mrkn2>{mrkref}*))""",
    "verse1": r"(?P<verse1>[0-9]+)(?P<subv1>[a-z]?|end)",
    "verse2": r"(?P<verse2>[0-9]+)(?P<subv2>[a-z]?|end)",
    "chapter": r"(?:(?P<chap>[0-9]+))",
    "chap": r"{chapter}(?:[:.]{verse1})?{wordref1}?",
    "context": r"""(?:{chap}
                    | {verse2}{wordref2}? | {wordrefonly}(?P<mrkn3>{mrkref}*)
                    | (?P<char3>{charref})(?P<mrkn4>{mrkref}*))(?=[-;,\s]|$)"""
    }

regexes = _regexes
for i in range(3):
    regexes = {k: v.format(**regexes) for k, v in regexes.items()}

def intend(s: str) -> Optional[int]:
    if not s:
        return None
    elif s == "end":
        return -1
    return int(s)

def strend(s: int) -> str:
    if s == -1:
        return "end"
    else:
        return str(s)

def parse_wordref(s: str) -> Tuple[int, Optional[str]]:
    b = s.split("+", 1)
    word = int(b[0])
    char = "+" + b[1] if len(b) > 1 else None
    return (word, char)

_reindex = re.compile(r"([0-9a-z_-]+)(?:\[([0-9]+\]))?")
def asmarkers(s: str, t: str) -> List[MarkerRef]:
    res = []
    if s is None or not len(s):
        return res
    b = s.split("!")
    b += t.split("!")
    i = 0
    while i < len(b):
        if not len(b[i]):
            i += 1
            continue
        if not (m := _reindex.match(b[i])):
            raise SyntaxError("Badly formed marker reference {} in {}".format(b, s))
        mrkr = m.group(1)
        ind = int(m.group(2)) if m.group(2) else None
        if i < len(b) - 1 and len(b[i+1]) and b[i+1][0] in "0123456789":
            word, charref = parse_wordref(b[i+1])
            i += 1
        else:
            word = None
            charref = None
        res.append(MarkerRef(mrkr, index=ind, word=word, char=charref))
        i += 1
    return res if len(res) else None
            

class Ref:
    rebook = re.compile(regexes["book"], re.X)
    recontext = re.compile(regexes["context"], re.X)

    def __init__(self, string: Optional[str] = None,
                    context: Optional['Ref'] = None, start: int = 0, **kw):
        parmlist = ('product', 'book', 'chapter', 'verse', 'subverse', 'word', 'char', 'mrkrs')
        if string is not None:
            self.parse(string, context=context, start=start)
        elif context is not None:
            for a in parmlist:
                setattr(self, a, kw.get(a, getattr(context, a, None)))
        else:
            for a in parmlist:
                setattr(self, a, kw.get(a, None))

    def parse(self, s: str, context: Optional['Ref'] = None, start: int = 0):
        p = {}
        if m := self.rebook.match(s, pos=start):
            p['product'] = m.group('transid') or None
            p['book'] = m.group('book')
            p['chapter'] = int(m.group('chap')) if m.group('chap') else None
            p['verse'] = intend(m.group('verse1'))
            p['subverse'] = m.group('subv1') or None
            p['word'] = intend(m.group('word1'))
            p['char'] = intend(m.group('char1'))
            p['mrkrs'] = asmarkers(m.group("mrk1"), m.group("mrkn1"))
        elif not (m:= self.recontext.match(s, pos=start)):
            raise SyntaxError("Cannot parse {}".format(s))
        elif m.group('verse1'):       # we know we have a chapter and verse
            p['chapter'] = int(m.group('chap'))
            p['verse'] = intend(m.group('verse1'))
            p['subverse'] = m.group('subv1') or None
            p['word'] = intend(m.group('word1'))
            p['char'] = intend(m.group('char1'))
            p['mrkrs'] = asmarkers(m.group("mrk1"), m.group("mrkn1"))
        elif m.group('subv2'):
            p['verse'] = intend(m.group('verse2'))
            p['subverse'] = m.group('subv2') or None
            p['word'] = intend(m.group('word2'))
            p['char'] = intend(m.group('char2'))
            p['mrkrs'] = asmarkers(m.group("mrk2"), m.group("mrkn2"))
        elif m.group('word'):
            p['word'] = intend(m.group('word'))
            p['char'] = intend(m.group('char'))
            p['mrkrs'] = asmarkers("", m.group('mrkn3'))
        elif m.group('char3'):
            p['char'] = intend(m.group('char3'))
            p['mrkrs'] = asmarkers("", m.group('mrkn4'))
        elif not m.group('chap') and m.group('word1'):
            p['word'] = intend(m.group('word1'))
            p['char'] = intend(m.group('char1'))
            p['mrkrs'] = asmarkers(m.group('mrk1'), m.group('mrkn1'))
        elif context is not None and context.char:
            p['char'] = intend(m.group('chap'))
        elif context is not None and context.word:
            p['word'] = intend(m.group('chap'))
            p['char'] = intend(m.group('char1'))
        elif context is not None and context.verse:
            p['verse'] = intend(m.group('chap'))
            p['word'] = intend(m.group('word1'))
            p['char'] = intend(m.group('char1'))
        else:
            p['chapter'] = int(m.group('chap'))
            p['word'] = intend(m.group('word1'))
            p['char'] = intend(m.group('char1'))
        self.strend = m.end(0)
        self.__init__(None, context, **p)

    def __str__(self):
        return self.str()

    def str(self, context: Optional['Ref'] = None, force: bool = False):
        if context is None:
            context = Ref()
        res = []
        sep = ''
        if context.product != self.product:
            res.append(self.product)
            res.append('.')
            force = True
        if force or context.book != self.book:
            res.append(self.book)
            res.append(' ')
            force = True
        if force or context.chapter != self.chapter:
            res.append(str(self.chapter))
        sep = ':'
        if self.verse is not None and (force or context.verse != self.verse):
            if len(res):
                res.append(sep)
            res.append(strend(self.verse))
            res.append(self.subverse or "")
        sep = "!"
        if self.word is not None and (force or context.word != self.word):
            if len(res):
                res.append(sep)
            res.append(strend(self.word))
        sep = "+"
        if self.char is not None and (force or context.char != self.char):
            if len(res):
                res.append(sep)
            res.append(strend(self.char))
        sep = "!"
        if self.mrkrs is not None and len(self.mrkrs):
            forcemkr = False
            for i, m in enumerate(self.mrkrs):
                if not forcemkr and context is not None and i < len(context.mrkrs):
                    if context.mrkrs[i] != m:
                        res.append(m.str(context=contex.mrkrs[i], force=force or len(res)))
                        forcemkr = True
                elif force or forcemkr:
                    res.append(m.str(force=True))
        return "".join(res)

    @property
    def first(self):
        return self

    @property
    def last(self):
        return self

class RefRange:
    def __init__(self, first: Optional[Ref] = None, last: Optional[Ref] = None):
        self.first = first
        self.last = last

    def str(self, context: Optional[Ref] = None, force: bool = False):
        res = [self.first.str(context, force=force)]
        res.append("-")
        res.append(self.last.str(self.first, force=force))
        return "".join(res)

    def __str__(self):
        return self.str()


class RefList(List):
    def __init__(self, content: str | List[Ref | RefRange], context: Optional[Ref] = None, start: int = 0):
        if isinstance(content, list):
            super().__init__(content)
        else:
            self.parse(content, context, start=start)

    def parse(self, s: str, context: Optional[Ref] = None, start: int = 0):
        bits = re.split(r"\s*[,;]\s*", s[start:])
        res = []
        for b in bits:
            first = Ref(b, context=context)
            nextstart = first.strend
            if not (m := re.match(r"\s*-\s*", s[nextstart:])):
                if nextstart < len(b):
                    raise SyntaxError("Bad range in {}".format(s[start:]))
                else:
                    res.append(first)
                    context = first
            else:
                nextstart += m.end()
                last = Ref(b, context=first, start=nextstart)
                res.append(RefRange(first, last))
                context = last
        self.__init__(res)

    def __str__(self):
        return "; ".join(str(s) for s in self)

    def str(self, context: Optional[Ref] = None, force: bool = False):
        res = []
        for r in self:
            res.append(r.str(context, force=force))
            context = r.last
        return "; ".join(res)


def main():
    import sys

    if len(sys.argv) > 1:
        s = " ".join(sys.argv[1:])
        res = RefList(s)
        print(res.str(force=True))

if __name__ == "__main__":
    main()
