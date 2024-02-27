
import re
import xml.etree.ElementTree as et

class ParentElement(et.Element):
    def __init__(self, tag, attrib=None, parent=None):
        et.Element.__init__(self, tag, attrib)
        self.parent = parent

    def makeelement(self, tag, attrib):
        return self.__class__(tag, attrib, parent=self)

    def __str__(self):
        return "{}[{}]".format(self.tag, " ".join('@{}="{}"'.format(k, v) for k, v in self.attrib.items()))

    def __repr__(self):
        p = repr(self.parent) if self.parent is not None else ""
        return "{}/{}".format(p, str(self))

    def _getindex(self):
        if self.parent is None:
            return -1, None
        return list(self.parent).index(self), self.parent

    def getprevious(self):
        i, parent = self._getindex()
        return parent[i-1] if parent is not None and i > 0 else None

    def getnext(self):
        i, parent = self._getindex()
        return parent[i+1] if parent is not None and i < len(parent) - 1 else None
        
    def getnext_sibling(self):
        i, parent = self._getindex()
        if i < len(parent) - 1:
            return parent[i+1]
        while parent is not None and i == len(parent) - 1:
            i, parent = parent._getindex()
        while isempty(parent.text) and len(parent):
            parent = parent[0]
        return parent

    def getprevious_sibling(self):
        i, parent = self._getindex()
        if i > 0:
            return parent[i-1]
        while parent is not None and i == 0:
            i, parent = parent.get_index()
        while isempty(parent.tail) and len(parent):
            parent = parent[-1]
        return parent
        
    def addprevious(self, el):
        i, parent = self._getindex()
        if parent is not None:
            parent.insert(i, el)

    def getparent(self):
        return self.parent


def parsexml(infile):
    tb = et.TreeBuilder(element_factory=ParentElement)
    parser = et.XMLParser(target=tb)
    res = et.ElementTree()
    res.parse(infile, parser)
    return res

def writexml(outf, root):
    outf.write('<?xml version="1.0" encoding="utf-8"?>\n')
    qnames, ns = et._namespaces(root, None)
    _serialize_xml(outf.write, root, qnames, ns, True)
    outf.write("\n")

escapes = {
    '&': "&amp;",
    '<': "&lt;",
    '>': "&gt;",
    '"': "&quot;",
    "'": "&apos;"
}
def usfmToUsxEscapes(s):
    for k, v in escapes.items():
        if k in s:
            s = s.replace(k, v)
    return s
    

def _serialize_xml(write, elem, qnames, namespaces, short_empty_elements, **kwargs):
    tag = elem.tag
    text = elem.text
    tag = qnames[tag]
    if tag is None:
        if text:
            write(usfmToUsxEscapes(text))
        for e in elem:
            _serialize_xml(write, e, qnames, None, short_empty_elements)
    else:
        write("<" + tag)
        items = list(elem.items())
        if items or namespaces:
            if namespaces:
                for v, k in sorted(namespaces.items(), key=lambda x: x[1]):  # sort on prefix
                    if k:
                        k = ":" + k
                    write(" xmlns%s=\"%s\"" % (k, usfmToUsxEscapes(v)))
            for k, v in items:
                if not k.startswith(" ") and v is not None:
                    v = usfmToUsxEscapes(v)
                    write(" %s=\"%s\"" % (qnames[k], v))
        if text or len(elem) or not short_empty_elements:
            write(">")
            if text:
                write(usfmToUsxEscapes(text))
            for e in elem:
                _serialize_xml(write, e, qnames, None, short_empty_elements)
            write("</" + tag + ">")
        else:
            write(" />")
    if elem.tail:
        write(usfmToUsxEscapes(elem.tail))

def prettyxml(node, last=None, indent="", width=2):
    if node.tag in ('para', 'sidebar', 'table', 'chapter', 'usx', 'book'):
        if last is not None:
            last.tail = (last.tail or "").rstrip() + "\n" + indent
        indent += " " * width
    last = None
    for e in node:
        prettyxml(e, last=last, indent=indent, width=width)
        last = e

def isempty(s):
    if s is None:
        return True
    if any(c not in " \t" for c in s):
        return False
    return True

