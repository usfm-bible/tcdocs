
import re

def proc_start_ms(el, tag, pref, emit, ws):
    if "style" not in el.attrib:
        return
    extra = ""
    if "altnumber" in el.attrib:
        extra += " \\{0}a {1}\\{0}a*".format(pref, el.get("altnumber"))
    if "pubnumber" in el.attrib:
        extra += " \\{0}p {1}".format(pref, el.get("pubnumber"))
    emit("\\{0} {1}{2}{3}".format(el.get("style"), el.get("number"), extra, ws))

def append_attribs(el, emit, tag=None, nows=False):
    if tag is not None and type(tag) != tuple:
        tag = (tag, tag)
    at_start = tag is None and not nows
    if tag is None:
        l = el.attrib.items()
    elif tag[1] not in el.attrib:
        return
    else:
        l = [(tag[0], el.get(tag[1], ""))]
    for k,v in l:
        if k in ("style", "status", "title"):
            continue
        if at_start:
            emit(" ")
            at_start = False
        emit('|{0}="{1}"'.format(k, v))

def get(el, k):
    return el.get(k, "")

class Emitter:
    def __init__(self, outf):
        self.outf = outf
        self.last_ws = None
        self.init = True

    def __call__(self, s, keepws=False):
        if s is None:
            return
        s = re.sub(r"\s*\n\s*", "\n", s)
        if not s.startswith("\n"):
            if self.last_ws is not None and len(self.last_ws):
                self.outf.write(self.last_ws)
        self.last_ws = ""
        if self.init:
            s = s.lstrip("\n")
            if len(s):
                self.init = False
        i = min(s.rfind("\n"), s.rfind(" "))
        if i >= 0:
            self.last_ws = s[i:]
            s = s[:i]
        self.outf.write(s)

    def hasnows(self):
        return self.last_ws is not None and not len(self.last_ws)

    def addws(self):
        if self.last_ws is not None and not len(self.last_ws):
            self.last_ws = " "

def iterels(el, events):
    if 'start' in events:
        yield ('start', el)
    for c in el:
        yield from iterels(c, events)
    if 'end' in events:
        yield ('end', el)

def usx2usfm(outf, root):
    emit = Emitter(outf)
    parent = None
    stack = []
    lastel = None
    for (ev, el) in iterels(root, ("start", "end")):
        s = el.get("style", "")
        if lastel is not None:
            emit(lastel.tail, True)

        if ev == "start":
            if lastel is None and parent is not None:
                if parent.text is not None and len(parent.text.strip()):
                    emit.addws()
                emit(parent.text, True)
            if el.tag in ("chapter", "book", "para", "row", "sidebar", "verse") and s != "":
                emit("\n")
            if el.tag == "chapter":
                proc_start_ms(el, "chapter", "c", emit, "\n")
            elif el.tag == "verse":
                proc_start_ms(el, "verse", "v", emit, " ")
            elif el.tag == "book":
                emit("\\{0} {1} ".format(s, el.get("code")))
            elif el.tag in ("row", "para"):
                emit("\\{0}".format(s))
            elif el.tag in ("link", "char"):
                nested = "+" if parent is not None and parent.tag == "char" else ""
                emit("\\{0} ".format(nested + s))
            elif el.tag in ("note", "sidebar"):
                emit("\\{0} {1} ".format(s, el.get("caller")))
                if "category" in el.attrib:
                    emit("\\cat {0}\\cat*".format(el.get("category")))
            elif el.tag == "unmatched":
                emit("\\" + el.get(marker))
            elif el.tag == "figure":
                emit("\\{} ".format(s))
            elif el.tag == "cell":
                if "colspan" in el.attrib:
                    emit("\\{0}-{1} ".format(s, el.get("colspan")))
                else:
                    emit("\\{} ".format(s))
            elif el.tag == "optbreak":
                emit("//")
            elif el.tag == "ms":
                emit("\\{}".format(s))
                append_attribs(el, emit)
                emit("\\*")
            elif el.tag == "ref" and el.get('gen', 'false').lower() != 'true':
                emit("\\ref")
            elif el.tag in ("usx", "annot", "table", "usfm", "text", "ref"):
                pass
            else:
                raise SyntaxError(el.tag)
            stack.append(parent)
            parent = el
            lastel = None
            lastopen = el

        elif ev == "end":
            if id(lastopen) == id(el):
                if el.text is not None and len(el.text.strip()):
                    emit.addws()
                emit(el.text, True)
            parent = stack.pop()
            if el.tag == "note" and el.get("closed", "true") == "true":
                emit("\\{}*".format(s))
            elif el.tag in ("char", "link"):
                nested = "+" if parent is not None and parent.tag == "char" else ""
                if el.get("closed", "true") == "true":
                    append_attribs(el, emit, nows=True)
                    emit("\\{}*".format(nested + s))
            elif el.tag == "figure":
                for k in ("alt", ("src", "file"), "size", "loc", "copy", "ref"):
                    append_attribs(el, emit, k)
                emit("\\{}*".format(s))
            elif el.tag == "sidebar":
                emit.addws()
                if el.get("closed", "true") == "true":
                    emit("\\{}e ".format(s))
            elif el.tag == "ref" and el.get('gen', 'false').lower() != 'true':
                append_attribs(el, emit, nows=True)
                emit("\\ref*")
            lastel = el
