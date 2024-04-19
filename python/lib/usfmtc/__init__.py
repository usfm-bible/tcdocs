
import os
from usfmtc.sfmparser import parseusfm, UsfmParserBackend
from usfmtc.parser import NoParseError
from usfmtc.extension import Extensions
from usfmtc.xmlutils import ParentElement, prettyxml, writexml
from usfmtc.usxgrammar import addmarkers
from usfmtc.usxparser import USXConverter
from usfmtc.grammar import UsfmGrammarParser
from usfmtc.diagrams import UsfmRailRoad
from usfmtc.usxmodel import addesids, cell_aligns, cleanup
from usfmtc.usjproc import usxtousj, usjtousx
import xml.etree.ElementTree as et

def _readsrc(src):
    if hasattr(src, "read"):
        return src.read()
    elif not isinstance(src, str):
        return src
    elif len(src) < 128 and os.path.exists(src):
        with open(src, encoding="utf-8") as inf:
            data = inf.read()
        return data
    elif "\n" in src or len(src) > 127:
        return src
    else:
        raise FileNotFoundError(src)

def _grammarDoc(gsrc, extensions=[], factory=et):
    data = _readsrc(gsrc)
    if isinstance(data, str):
        rdoc = factory.ElementTree(factory.fromstring(data))
    else:
        rdoc = data
    for ef in extensions:
        e = Extensions(ef)
        dirty = e.applyto(rdoc, factory=factory)
    return rdoc

def _usfmGrammar(rdoc, backend=None, start=None):
    if backend is None:
        backend = UsfmParserBackend()
    sfmproc = UsfmGrammarParser(rdoc, backend)
    if start is None:
        start = "Scripture"
    parser = sfmproc.parseRef(start)
    return parser

def usfmGrammar(gsrc, extensions=[], backend=None, start=None):
    """ Create UsfmGrammarParser from gsrc as used by USX.fromUsfm """
    rdoc = _grammarDoc(gsrc, extensions)
    return _usfmGrammar(rdoc, backend, start)


class USX:
    @classmethod
    def fromUsx(cls, src, elfactory=None):
        """ Loads USX and creates USX object to hold it """
        if elfactory is None:
            elfactory = ParentElement
        tb = et.TreeBuilder(element_factory=elfactory)
        parser = et.XMLParser(target=tb)
        if hasattr(src, "read") or os.path.exists(src):
            anet = et.ElementTree()
            anet.parse(src, parser=parser)
            res = anet.getroot()
        else:
            res = et.fromstring(src, parser=parser)
        return cls(res)

    @classmethod
    def fromUsfm(cls, src, grammar, elfactory=None, timeout=1e7):
        """ Parses USFM using UsfmGrammarParser grammar and creates USX object.
            Raise usfmtc.parser.NoParseError on error. """
        data = _readsrc(src)

        # This can raise usfmtc.parser.NoParseError
        result = parseusfm(data, grammar, timeout=timeout, isdata=True)

        xml = result.asEt(elfactory=elfactory)
        cleanup(xml)            # convert // and ~ etc.
        cell_aligns(xml)        # create cell @aligns
        res = cls(xml)
        return res

    @classmethod
    def fromUsj(cls, src, elfactory=None):
        data = _readsrc(src)
        djson = json.loads(data)
        xml = usjtousx(djson, elfactory=elfactory)
        return cls(xml)

    def __init__(self, xml):
        self.xml = xml      # an Element, not an ElementTree

    def _outwrite(self, file, dat, fn=None):
        if fn is None:
            fn = lambda f, d: f.write(d)
        if file is None:
            fh = io.StringIO()
            fn(fh, dat)
            res = fh.getvalue()
            fh.close()
            return res
        if not hasattr(file, "read"):
            fh = open(file, "w", encoding="utf-8")
            fn(fh, dat)
            fh.close()
        else:
            fn(file, dat)
        return True

    def outUsx(self, file=None):
        """ Output pretty XML USX. If file is None returns string """
        if self.xml is None:
            return None
        prettyxml(self.xml)
        self._outwrite(file, self.xml, fn=writexml)

    def outUsfm(self, grammar, file=None):
        """ Output USFM from USX object. grammar is et doc. If file is None returns string """
        parser = USXConverter(grammar.getroot())
        res = parser.parse(self.xml)
        if res:
            dat = "".join(res.results)
            return self._outwrite(file, dat)
        return False

    def outUsj(self, file=None):
        """ Output USJ from USX object. If file is None returns dict """
        res, _ = usxtousj(self.xml.getroot())
        if file is None:
            return res
        else:
            dat = json.dumps(res, indent=2)
            self._outwrite(file, dat)

    def getroot(self):
        """ Returns root XML element """
        return self.xml

    def addesids(self):
        """ Add esids to USX object (eid, sids, vids) """
        addesids(self.xml)

    @property
    def version(self):
        return self.getroot().get('version', None)

    @version.setter
    def version(self, version):
        self.getroot().set('version', str(version))

