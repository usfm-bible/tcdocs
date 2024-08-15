#!/usr/bin/env python3

import xml.etree.ElementTree as et
import regex, logging
from copy import copy

logger = logging.getLogger(__name__)

usfmns = "{http://usfm.bible/parse/2023}"
relaxns = "{http://relaxng.org/ns/structure/1.0}"

class State:
    def __init__(self, parent, index, attributes=[], nsmap=None, current=None):
        self.parent = parent
        self.index = index
        if current is None:
            self.setcurr()
        else:
            self.current = current
        if nsmap is None:
            self.nsmap = {}
            self.nsrevmap = {}
        else:
            self.nsmap = nsmap.copy()
            self.nsrevmap = {v:k for k, v in nsmap.items()}
        self.stack = []
        self.attributes = set(attributes)
        self.key = None         # set when processing attributes
        self.atend = False

    def __str__(self):
        if self.istext():
            res = "{}".format(self.current)
        else:
            res = "{}".format(self.current.tag)
        res += f" at {self.index} in {self.parent.tag if self.parent else ''}"
        return res

    def setcurr(self):
        if self.index == 0:
            if isinstance(self.parent, str):
                self.current = self.parent
                return
            else:
                self.current = self.parent.text
            if self.current is None or self.current.strip() == "":
                self.advance()
            return

        ind = (self.index - 1) // 2
        if ind >= len(self.parent):
            self.current = None
            return
        curr = list(self.parent)[ind]
        if (self.index & 1) == 0:
            self.current = curr.tail
            if self.current is None or self.current.strip() == "":
                self.advance()
        else:
            self.current = curr
        logger.debug(f"SET {self.index}, {self.current} in {self.parent}")

    def copy(self, parent=None, index=None, current=None, attributes=[]):
        res = self.__class__(parent, self.index if index is None else index,
                    attributes=attributes, nsmap=self.nsmap, current=current)
        return res

    def updatensmap(self, parent):
        for k, v in parent.attrib:
            if k.startswith("xmlns"):
                if k.startswith("xmlns:"):
                    self.nsmap[k[6:]] = v
                    self.nsrevmap[v] = k[6:]
                else:
                    self.nsmap[""] = v

    def advance(self):
        logger.debug(f"ADVANCING {self.index}, {self.current} in {self.parent}")
        if (self.index & 1) == 1:
            self.current = self.current.tail
            if self.current is None or self.current.strip() == "":
                self.index += 1

        if isinstance(self.parent, str):
            return True
        if self.parent is None or self.index >= 2 * len(self.parent):
            self.current = None
            self.atend = True
            return False
        elif (self.index & 1) == 0:
            self.current = list(self.parent)[self.index // 2]
        self.index += 1
        logger.debug(f"Advanced to {self.index}, {self.current} in {self.parent}")
        return True

    def istext(self):
        return (self.index & 1 == 0)

    def push(self):
        self.stack.append((self.index, self.current, self.attributes, len(self.results)))
        logger.debug(f"Pushed {self.stack[-1]}")

    def pop(self):
        if len(self.stack):
            self.index, self.current, self.attributes, reslen = self.stack.pop()
            logger.debug(f"Popped: {self.index}, {self.current}, {self.attributes}, {reslen}")
            if reslen < len(self.results):
                self.results = self.results[:reslen]

    def drop(self):
        if len(self.stack):
            self.stack.pop()

    def useattrib(self, attrib):
        self.attributes.add(attrib)

    def unuseattrib(self, attrib):
        self.attributes.discard(attrib)

    def update(self, other):
        pass


class Failure(str):
    def __bool__(self):
        return False

allrngels = ("element", "attribute", "group", "interleave", "choice", "optional", "zeroOrMore",
             "oneOrMore", "list", "mixed", "ref", "parentRef", "empty", "text", "value",
             "data", "notAllowed", "externalRef", "grammar",
             "start", "define",
             "name", "anyName", "nsName", "choice",
             "except",
             "usfm:match", "usfm:matchpair", "usfm:properties")
# oops handle aliases
allrngattr = ("name", "type", "href", "combine", "ns", "datatypeLibrary")
allrngmultis = ("zeroOrMore", "optional", "oneOrMore", "interleave", "mixed")
allrngtexts = ("text", "data", "value")


class RelaxValidator:

    def __init__(self, grammar):
        self.grammar = grammar
        self.start = grammar.find(f'{relaxns}start')
        self.defines = {}
        for d in grammar.findall(f'{relaxns}define'):
            name = d.get('name', None)
            if name is not None:
                self.defines[name] = list(d)

    def parse(self, root, state=None):
        if state is None:
            state = State(None, 1, current=root)
        res = self._validate(self.start, state)
        if res:
            return state
        else:
            return res

    def _validate(self, vel, state):
        results = []
        state.push()
        for c in vel:
            res = self.proc_child(c, state)
            if not res:
                state.pop()
                return res
        state.drop()
        return True

    def proc_child(self, vel, state):
        t = vel.tag[len(relaxns):] if vel.tag.startswith(relaxns) else vel.tag
        fn = getattr(self, t, None)
        if fn is not None:
            res = fn(vel, state)
        else:
            res = Failure("Unknown grammar element {} in {}".format(t, state))
        return res

    def _nsconvert(self, name, state):
        if ":" in name:
            qname = name[:name.find(":")]
            res = "{{{}}}{}".format(state.nsmap.get(qname, ""), name[len(qname):])
            return res
        return name

    def _localns(self, tag, state):
        if tag.startswith("{"):
            url = tag[1:tag.find("}")]
            localns = state.nsrevmap.get(url, "unk")
            return "{}:{}".format(localns, tag[len(url)+2:])
        else:
            return tag

    def _testname(self, testname, vel, state):
        testname = self._nsconvert(testname, state)
        if (name := vel.findtext(f"{relaxns}name")) is not None:
            return testname == name
        if (nclass := vel.find(f"{relaxns}anyName")) is not None:
            if (eexcept := nclass.find(f"{relaxns}except")) is not None:
                return not self._testname(testname, eexcept, state)
            return True
        elif (nclass := vel.find(f"{relaxns}nsName")) is not None:
            ns = nclass.get("ns", "")
            if ns == "" and testname.startswith("{"):
                return False
            elif not testname.startswith("{{{}}}".format(ns)):
                return False
            if (eexcept := nclass.find(f"{relaxns}except")) is not None:
                return not self._testname(testname, eexcept, state)
            return True
        elif (nclass := vel.find(f"{relaxns}choice")) is not None:
            for c in nclass:
                if self._testname(testname, c, state):
                    return True
        return False

    def ref(self, vel, state):
        name = vel.get('name', None)
        if name is not None:
            vels = self.defines.get(name, [])
            logger.debug(f"calling {name}")
            res = self._validate(vels, state)
            logger.debug(f"return from {name} = {res}")
            return res
        return Failure("Undefined reference {} at {}".format(name, state))

    def element(self, vel, state):
        if state.atend:
            return Failure("At end of parent in {}".format(state))
        el = state.current
        if state.istext():
            return Failure("Unexpected text node in {}".format(state))
        if not self._testname(el.tag, vel, state):
            return Failure("Bad element name of {} in {}".format(el.tag, state))
        results = []
        newstate = state.copy(parent=el, index=0)
        newstate.element = el
        res = self._validate(vel, newstate)
        if res:
            state.update(newstate)
            state.advance()
        return res

    def attribute(self, vel, state):
        el = state.element
        for k in el.attrib.keys():
            if k not in state.attributes and self._testname(k, vel, state):
                name = k
                break
        else:
            return Failure("Attribute not found in {}".format(state))
        state.useattrib(name)
        newstate = state.copy(current=el.attrib.get(name), index=0)
        newstate.key = name
        logger.debug(f"Attribute [{name}] = {newstate.current}")
        #if name == "sid" and newstate.current == "qt_123":
        #    import pdb; pdb.set_trace()
        res = self._validate(vel, newstate)
        if res:
            state.update(newstate)
        else:
            state.unuseattrib(name)
        return res

    def name(self, vel, state):
        # names are handled elsewhere
        return True

    def anyName(self, vel, state):
        return True

    def nsName(self, vel, state):
        return True

    def empty(self, vel, state):
        if state.current is None:
            return True
        return False

    def group(self, vel, state):
        return self._validate(vel, state)

    def choice(self, vel, state):
        for c in vel:
            state.push()
            res = self.proc_child(c, state)
            if res:
                state.drop()
                return res
            state.pop()
        return Failure("choice failed in {}".format(state))

    def optional(self, vel, state):
        return self._nOrMore(vel, state, 0, maxc=0)

    def _nOrMore(self, vel, state, minc, maxc=None):
        i = 0
        state.push()
        while True:
            res = self._validate(vel, state)
            if not res or (maxc is not None and i >= maxc):
                if i < minc:
                    state.pop()
                    return Failure("Too few matches {}/{} at {}".format(i+1, minc, state)) if res else res
                else:
                    state.drop()
                    return True
            i += 1

    def zeroOrMore(self, vel, state):
        return self._nOrMore(vel, state, 0)

    def oneOrMore(self, vel, state):
        return self._nOrMore(vel, state, 1)

    def interleave(self, vel, state):
        ismatched = set()
        state.push()
        hitone = True
        lastfail = Failure("interleave failed at {}".format(state))
        while hitone:
            hitone = False
            for c in vel:
                if id(c) in ismatched and not c.tag in allrngmultis:
                    continue
                state.push()
                res = self.proc_child(c, state)
                if res:
                    state.drop()
                    ismatched.add(id(c))
                    state.advance()
                    hitone = True
                else:
                    state.pop()
                    lastfail = res
        if all(id(c) in ismatched for c in vel):
            state.drop()
            return True
        else:
            state.pop()
            return lastfail

    def text(self, vel, state):
        if state.atend:
            return Failure("At end of parent in {}".format(state))
        res = self._validate(vel, state)
        logger.debug(state.current)
        if res:
            state.advance()
        return res

    def data(self, vel, state):
        if not state.istext():
            return Failure("String expected in data test at {}".format(state))
        val = state.current
        datatype = vel.get("type", None)
        res = True
        if datatype == "string":
            if (testxt := vel.findtext(f'{relaxns}param[@name="minLength"]')) is not None:
                if int(testxt) > len(val):
                    res = False
            if (testxt := vel.findtext(f'{relaxns}param[@name="pattern"]')) is not None:
                if not regex.match(testxt, val):
                    res = False
        if not res:
            return Failure("Faulty string value {} at {}".format(val, state))
        return True

    def value(self, vel, state):
        if not state.istext():
            return Failure("String expected in value test at {}".format(state))
        if state.current != vel.text:
            return Failure("Faulty string {} not equal to value {} at {}".format(state.current, vel.text, state))
        return True


class USXState(State):
    attribescapere = regex.compile("([\\~\"'])")
    usfmescapere = regex.compile("([\\~])")

    def __init__(self, parent, index, attributes=[], nsmap=None, current=None, context=None):
        super().__init__(parent, index, attributes=attributes, nsmap=nsmap, current=current)
        self.usxstack = []
        self.context = context
        self.results = []

    def copy(self, parent=None, index=None, current=None, attributes=[]):
        res = self.__class__(parent, self.index if index is None else index,
                    attributes=attributes, nsmap=self.nsmap, current=current, context=self.context)
        return res

    def addresult(self, *s, text=False, attribute=False):
        if text:
            if attribute:
                s = [self.attribescapere.sub(r"\\\1", x) for x in s]
            else:
                s = [self.usfmescapere.sub(r"\\\1", x).replace("//", "\\//") for x in s]
        logger.debug(f"out: {s}")
        self.results.extend(s)

    def update(self, other):
        self.results.extend(other.results)

    def push(self):
        super().push()
        self.usxstack.append(len(self.context.matchids))
        logger.debug(f"usxpush onto {self.usxstack}")

    def pop(self):
        super().pop()
        logger.debug(f"usxpop from {self.usxstack}")
        r = self.usxstack.pop()
        if r < len(self.context.matchids):
            self.context.matchids = self.context.matchids[:r]


escapes = {
    'n' : '\n',
    '\\': '\\',
}

class USXConverter(RelaxValidator):

    def __init__(self, grammar, **kw):
        super().__init__(grammar)
        self.aliases = {}
        for a in grammar.findall(f"{usfmns}alias"):
            name = a.get("name").replace("usfm:", "")
            self.aliases[name] = a[0]
        self.matchids = []
        for k, v in kw.items():
            setattr(self, k, v)

    def pushmatch(self, key, value):
        self.matchids.append((key, value))
        logger.debug(f"Pushing match to {self.matchids}")

    def popmatch(self, key):
        logger.debug(f"Popping match from {self.matchids}")
        while len(self.matchids):
            k, v = self.matchids.pop()
            if k == key:
                return v
        return ""

    def parse(self, root, state=None):
        if state is None:
            state = USXState(None, 1, current=root, context=self)
        return super().parse(root, state=state)

    def proc_child(self, vel, state):
        if vel.tag.startswith(usfmns):
            t = vel.tag[len(usfmns):]
            a = self.aliases.get(t, None)
            if a is not None:
                tmp = vel
                vel = copy(a)
                vel.attrib = {k: v for k,v in a.attrib.items()}
                vel.text = tmp.text
                for k, v in tmp.attrib.items():
                    vel.set(k, v)
                t = a.tag.replace(usfmns, "")
            t = "usfm_" + t
        elif vel.tag.startswith(relaxns):
            t = vel.tag[len(relaxns):]
        else:
            return Failure("Unexpected tag {}".format(vel.tag))
        logger.debug(f"{t} for {state}")
        fn = getattr(self, t, None)
        if fn is not None:
            res = fn(vel, state)
        else:
            res = Failure("Unknown grammar element {} in {}".format(vel.tag, state))
        logger.debug(f"From {t}[{vel.attrib}] = {res}")
        return res

    def _getmatchfield(self, vel, base):
        res = vel.get(base+'out', None)
        if res is None:
            res = vel.get(base, None)
        if res is None:
            return None
        elif res == '':
            return ''
        elif res.startswith("'"):
            return regex.sub(r"\\(.)", lambda m: escapes.get(m.group(1), m.group(1)), res[1:-1])
        else:
            return None

    def usfm_match(self, vel, state):
        if vel.get("noout", "false").lower() in ("true", "1"):
            return True
        if vel.get("skip", "") == self.outversion:
            return False
        if (res := self._getmatchfield(vel, 'before')) is not None:
            state.addresult(res)
        if (idcode := vel.get('matchid', None)) is not None:
            if not state.istext():
                return Failure("String expected in value test at {}".format(state))
            self.pushmatch(idcode, state.current)
        res = vel.get('matchref', None)
        if res is not None and res != '':
            state.addresult(self.popmatch(res))
        else:
            res = self._getmatchfield(vel, 'match')
            if res is None:
                res = vel.text
            if res is None:
                if not state.istext():
                    return Failure("String expected in value test at {}".format(state))
                state.addresult(state.current or "", text=True, attribute=state.key is not None)
            else:
                state.addresult(res)
        if (res := self._getmatchfield(vel, 'after')) is not None:
            state.addresult(res)
        return True

    def usfm_text(self, vel, state):
        if not state.istext():
            return Failure("String expected in value test at {}".format(state))
        if state.current is not None:
            state.addresult(state.current, text=True)
        return True

    def usfm_matchpair(self, vel, state):
        if (res := self._getmatchfield(vel, 'before')) is not None:
            state.addresult(res)
        state.addresult(state.key)
        if (res := self._getmatchfield(vel, 'between')) is not None:
            state.addresult(res)
        if state.current is not None:
            state.addresult(state.current, text=True, attribute=True)
        if (res := self._getmatchfield(vel, 'after')) is not None:
            state.addresult(res)
        return True
    

def usxtousfm(doc, grammar):
    p = USXConverter(grammar.getroot())
    res = p.parse(doc.getroot())
    if not res:
        return res
    return "".join(res.results)

def main():
    import argparse, sys
    import xml.etree.ElementTree as et

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="Input USX file")
    parser.add_argument("-g", "--grammar", required=True, help="Grammar RelaxNG XML file")
    parser.add_argument("-o", "--outfile", help="Output USFM file")
    args = parser.parse_args()

    d = et.parse(args.infile)
    g = et.parse(args.grammar)
    res = usxtousfm(d, g)
    if res:
        if args.outfile:
            with open(args.outfile, "w", encoding="utf-8") as outf:
                outf.write(res)
        else:
            sys.stdout.write(res)

if __name__ == "__main__":
    main()
