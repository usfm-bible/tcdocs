
import re

def escaped(s):
    return s
    return re.sub(r'([\\|"/])', r'\\\1', s)

def proc_start_ms(el, tag, pref, emit, ws):
    if "style" not in el.attrib:
        return
    extra = ""
    if "altnumber" in el.attrib:
        extra += " \\{0}a {1}\\{0}a*".format(pref, el.get("altnumber"))
    if "pubnumber" in el.attrib:
        extra += " \\{0}p {1}".format(pref, escaped(el.get("pubnumber")))
    emit("\\{0} {1}{2}{3}".format(el.get("style"), el.get("number"), extra, ws))

def append_attribs(el, emit, attribmap={}, tag=None, nows=False):
    s = el.get('style', el.tag)
    if tag is not None and type(tag) != tuple:
        tag = (tag, tag)
    at_start = tag is None and not nows
    if tag is None:
        l = list(el.attrib.items())
    elif tag[1] not in el.attrib:
        return
    else:
        l = [(tag[0], el.get(tag[1], ""))]
    l = [(k, v) for k,v in l if k not in ('style', 'status', 'title')]
    if not len(l):
        return
    if len(l) == 1 and l[0][0] == attribmap.get(s, ''):
        emit("|"+escaped(l[0][1]))
    else:
        attribs = ['{0}="{1}"'.format(k, escaped(v)) for k,v in l]
        if len(attribs):
            emit("|"+" ".join(attribs))

def get(el, k):
    return el.get(k, "")

class Emitter:
    def __init__(self, outf):
        self.outf = outf

    def __call__(self, s, text=False):
        if s is None:
            return
        s = re.sub(r"\s*\n\s*", "\n", s)
        if text:
            s = escaped(s)
        self.outf.write(s)

def iterels(el, events):
    if 'start' in events:
        yield ('start', el)
    for c in el:
        yield from iterels(c, events)
    if 'end' in events:
        yield ('end', el)

def usx2usfm(outf, root, grammar=None, lastel=None):
    if grammar is None:
        attribmap = {}
        mcats = {}
    else:
        attribmap = grammar.attribmap
        mcats = grammar.marker_categories
    emit = Emitter(outf)
    version = "3.1"
    paraelements = ("chapter", "para", "row", "sidebar", "verse")
    for (ev, el) in iterels(root, ("start", "end")):
        s = el.get("style", "")

        if ev == "start":
            if el.tag in paraelements and s != "":
                if lastel is not None and lastel.tail is not None:
                    emit(lastel.tail.rstrip(), text=True)
                emit("\n")
            elif el.tag == "table":
                if lastel is not None and lastel.tail is not None:
                    emit(lastel.tail.rstrip(), text=True)
            elif lastel is not None:
                emit(lastel.tail, text=True)
            lastel = None
            prespace = False
            if el.tag == "chapter":
                proc_start_ms(el, "chapter", "c", emit, "")
            elif el.tag == "verse":
                proc_start_ms(el, "verse", "v", emit, " ")
            elif el.tag == "book":
                emit("\\{0} {1}".format(s, el.get("code")))
                prespace = True
            elif el.tag in ("row", "para"):
                if (el.text is None or not el.text.strip()) and (len(el) and el[0].tag in paraelements):
                    emit("\\{0}".format(s))
                else:
                    emit("\\{0} ".format(s))
            elif el.tag in ("link", "char"):
                emit("\\{0} ".format(s))
            elif el.tag in ("note", "sidebar"):
                emit("\\{0} {1} ".format(s, el.get("caller")))
                if "category" in el.attrib:
                    emit("\\cat {0}\\cat*".format(el.get("category")))
            elif el.tag == "unmatched":
                emit("\\" + el.get("style", " "))
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
                isbare = el.get("_bare", "").lower() in ("1", "true")
                el.attrib.pop("_bare", None)
                append_attribs(el, emit, attribmap=attribmap)
                emit("\\*" if not isbare else " ")
            elif el.tag == "ref":
                emit("\\ref ")
            elif el.tag == "usx":
                version = el.get("version", "3.1")
            elif el.tag in ("table", ):
                pass
            else:
                raise SyntaxError(el.tag)
            if el.text is not None and len(el.text.lstrip()):
                if prespace:
                    emit(" ")
                if not(len(el)) and prespace:
                    emit(el.text.strip(), text=True)
                else:
                    emit(el.text.lstrip(), text=True)
            lastel = None
            lastopen = el

        elif ev == "end":
            if lastel is not None and lastel.tail is not None:
                if el.tag in ("para", "row", "sidebar"):
                    emit(lastel.tail.rstrip())
                else:
                    emit(lastel.tail)
            if el.tag == "note":
                emit("\\{}*".format(s))
            elif el.tag in ("char", "link", "figure") and mcats.get(s, "") not in ('footnotechar', 'crossreferencechar'):
                append_attribs(el, emit, attribmap=attribmap)
                emit("\\{}*".format(s))
            elif el.tag == "sidebar":
                emit("\n\\{}e\n".format(s))
            elif el.tag == "ref" and el.get('gen', 'false').lower() != 'true':
                append_attribs(el, emit, attribmap=attribmap, nows=True)
                emit("\\ref*")
            elif el.tag == "book" and float(version) >= 3.1:
                emit("\n\\usfm {}".format(version))
            lastel = el
    return lastel
