#!/usr/bin/env python3

# nuitka configuration
# nuitka-project: --onefile
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/usx.rng=usx.rng
# nuitka-project-if: {OS} in ("Windows",):
#     nuitka-project: --output-filename=usfmconv.exe
# nuitka-project-else:
#     nuitka-project: --output-filename=usfmconv.bin

import os, json
from usfmtc.sfmparser import parseusfm, UsfmParserBackend
from usfmtc.parser import NoParseError
from usfmtc.extension import Extensions
from usfmtc.xmlutils import ParentElement, prettyxml, writexml
from usfmtc.usxparser import USXConverter
from usfmtc.grammar import UsfmGrammarParser
from usfmtc.diagrams import UsfmRailRoad
from usfmtc.usxmodel import addesids, cleanup, messup, canonicalise
from usfmtc.usjproc import usxtousj, usjtousx
from usfmtc.usfmparser import USFMParser, Grammar
from usfmtc.usfmgenerate import usx2usfm
import xml.etree.ElementTree as et

def _readsrc(src):
    if hasattr(src, "read"):
        return src.read()
    elif not isinstance(src, str):      # we're a parsed xml doc
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
    if isinstance(data, (str, bytes)):
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

def usfmGrammar(gsrc, extensions=[], altparser=True, backend=None, start=None):
    """ Create UsfmGrammarParser from gsrc as used by USX.fromUsfm """
    if altparser:
        rdoc = _grammarDoc(gsrc, extensions)
        return _usfmGrammar(rdoc, backend, start)
    else:
        res = Grammar()
        if len(extensions):
            for e in extensions:
                res.readmrkrs(e)
        return res


_filetypes = {".xml": "usx", ".usx": "usx", ".usfm": "usfm", ".sfm": "usfm3.0", ".json": "usj"}

def readFile(infpath, informat=None, gramfile=None, grammar=None, extfiles=[], altparser=True):
    """ Reads a USFM file of a given type or inferred from the filename
        extension. extfiles allows for extra markers.ext files to extend the grammar"""
    if informat is None:
        inroot, ext = os.path.splitext(infpath)
        intype = _filetypes.get(ext.lower(), informat)
    else:
        intype = informat
    if intype is None:
        return None

    if intype == "usx":
        usxdoc = USX.fromUsx(infpath)
    elif intype == "usj":
        usxdoc = USX.fromUsj(infpath)
    elif intype.startswith("usfm"):
        if grammar is None:
            if gramfile is None:
                for a in ([], ['..', '..', '..', 'grammar']):
                    gramfile = os.path.join(os.path.dirname(__file__), *a, "usx.rng")
                    if os.path.exists(gramfile):
                        break
            fname = getattr(infpath, 'name', infpath)
            extfiles.append(os.path.join(os.path.dirname(fname), "markers.ext"))
            exts = [x for x in extfiles if os.path.exists(x)]
            grammar = usfmGrammar(gramfile, extensions=exts, altparser=altparser)
        usxdoc = USX.fromUsfm(infpath, grammar, altparser=altparser)
    return usxdoc


class USX:
    @classmethod
    def fromUsx(cls, src, elfactory=None):
        """ Loads USX and creates USX object to hold it """
        if elfactory is None:
            elfactory = ParentElement
        tb = et.TreeBuilder(element_factory=elfactory)
        parser = et.XMLParser(target=tb)
        if os.path.exists(src):
            inf = open(src, encoding="utf_8_sig")
        else:
            inf = src
        if hasattr(inf, "read"):
            anet = et.ElementTree()
            anet.parse(inf, parser=parser)
            res = anet.getroot()
            if src != inf:
                inf.close()
        else:
            try:
                res = et.fromstring(src, parser=parser)
            except et.ParseError:
                return None
        return cls(res)

    @classmethod
    def fromUsfm(cls, src, grammar, altparser=True, elfactory=None, timeout=1e7):
        """ Parses USFM using UsfmGrammarParser grammar and creates USX object.
            Raise usfmtc.parser.NoParseError on error.
            elfactory must take parent and pos named parameters not as attributes
        """
        data = _readsrc(src)

        if not altparser:
            p = USFMParser(data, factory=elfactory or ParentElement, grammar=grammar)
            xml = p.parse()
        else:
        # This can raise usfmtc.parser.NoParseError
            result = parseusfm(data, grammar, timeout=timeout, isdata=True)
            xml = result.asEt(elfactory=elfactory)

        cleanup(xml)            # normalize space, de-escape chars, cell aligns, etc.
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

    def outUsx(self, file=None, **kw):
        """ Output pretty XML USX. If file is None returns string """
        if self.xml is None:
            return None
        prettyxml(self.xml)
        self._outwrite(file, self.xml, fn=writexml)

    def outUsfm(self, grammar, file=None, altparser=True, **kw):
        """ Output USFM from USX object. grammar is et doc. If file is None returns string """
        el = messup(self.xml)
        if not altparser:
            return self._outwrite(file, el, fn=usx2usfm)
        parser = USXConverter(grammar.getroot(), **kw)
        res = parser.parse(el)
        if res:
            dat = "".join(res.results)
            return self._outwrite(file, dat)
        return False

    def outUsj(self, file=None, ensure_ascii=False, **kw):
        """ Output USJ from USX object. If file is None returns dict """
        res = usxtousj(self.xml)
        if file is None:
            return res
        else:
            dat = json.dumps(res, indent=2, ensure_ascii=ensure_ascii)
            self._outwrite(file, dat)

    def saveAs(self, outfpath, outformat=None, addesids=False, grammar=None,
                gramfile=None, version=None, altparser=True, **kw):
        """ Saves the document to a file in the appropriate format, either given
            or inferred from the filename extension. """
        if outformat is None:
            outroot, ext = os.path.splitext(outfpath)
            outtype = _filetypes.get(ext.lower(), outformat)
        else:
            outtype = outformat
        if outtype is None:
            return

        if outtype == "usx":
            if addesids:
                usxdoc.addesids()
            self.outUsx(outfpath, **kw)
        elif outtype == "usj":
            self.outUsj(outfpath, **kw)
        elif outtype == "usfm":
            if grammar is None and altparser:
                if gramfile is None:
                    for a in ([], ['..', '..', '..', 'grammar']):
                        gramfile = os.path.join(os.path.dirname(__file__), *a, "usx.rng")
                        if os.path.exists(gramfile):
                            break
                grammar = _grammarDoc(gramfile)
            if outtype == "usfm3.0":
                outtype = "usfm"
                if version is None:
                    version = "3.0"
            self.outUsfm(grammar, outfpath, outversion=version, altparser=altparser, **kw)

    def canonicalise(self):
        canonicalise(self.getroot())

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

def main(hookcli=None, hookusx=None):

    import argparse, logging, sys
    from glob import glob

    parser = argparse.ArgumentParser()
    parser.add_argument("infile",nargs="+",help="Input file")
    parser.add_argument("-o", "--outfile",help="Output file, with inferred format")
    parser.add_argument("-F","--outformat",help="Output format [usfm, usx, usj, usfm3.0]")
    parser.add_argument("-I","--informat",help="Input format [usfm, usx, usj]")
    parser.add_argument("-g","--grammar",help="Grammar file to use, if needed")
    parser.add_argument("-e","--esids",action="store_true",
                        help="Add esids, vids, sids, etc. to USX output")
    parser.add_argument("-v","--version",default=None,help="Set USFM version [3.1]")
    parser.add_argument("-x","--extfiles",action="append",default=[],
                        help="markers.ext files to include")
    parser.add_argument("-V","--validate",action="store_true",help="Use validating parsers for USFM")
    parser.add_argument("-C","--canonical",action="store_true",help="Do not canonicalise")
    parser.add_argument("-A","--ascii",action="store_true",help="Output as ASCII only in json")
    parser.add_argument("-l","--logging",help="Set logging level to usfmxtest.log")
    parser.add_argument("-q","--quiet",action="store_true",help="Don't say much")
    parser.add_argument("--nooutput",action="store_true",help="Don't output any data")
    if hookcli is not None:
        hookcli(parser)
    args = parser.parse_args()

    if args.logging:
        try:
            loglevel = int(args.logging)
        except ValueError:
            loglevel = getattr(logging, args.logging.upper(), None)
        if isinstance(loglevel, int):
            parms = {'level':  loglevel, 'datefmt': '%d/%b/%Y %H:%M:%S',
                     'format': '%(asctime)s.%(msecs)03d %(levelname)s:%(module)s(%(lineno)d) %(message)s'}
            logfh = open("usfmconv.log", "w", encoding="utf-8")
            parms.update(stream=logfh, filemode="w") #, encoding="utf-8")
            try:
                logging.basicConfig(**parms)
            except FileNotFoundError as e:      # no write access to the log
                print("Exception", e)
        log = logging.getLogger('usfmconv')
    else:
        log = None

    def doerror(msg, doexit=True):
        if log:
            log.error(msg)
        if not args.quiet:
            print(msg)
        if doexit:
            sys.exit(1)
    
    fileexts = {"usx": ".xml", "usfm": ".usfm", "usj": ".json"}

    def _makeoutfile(infile, oformat):
        outext = fileexts.get(oformat, None)
        inroot, ext = os.path.splitext(infile)
        return inroot + outext if outext else None
    
    infiles = sum((glob(x) for x in args.infile), [])
    if not len(infiles):
        doerror("No files found in {args.infile}")

    root, ext = os.path.splitext(infiles[0])
    args.informat = args.informat or _filetypes.get(ext.lower(), args.informat)
    if args.outformat is None:
        if args.outfile is not None and not os.path.isdir(args.outfile):
            root, ext = os.path.splitext(args.outfile)
            args.outformat = _filetypes.get(ext.lower(), None)
    ingrammar = None
    outgrammar = None
    if args.informat.startswith("usfm") or args.outformat.startswith("usfm"):
        if args.grammar is None:
            for a in ([], ['..', '..', '..', 'grammar']):
                args.grammar = os.path.join(os.path.dirname(__file__), *a, "usx.rng")
                if os.path.exists(args.grammar):
                    break
        if args.informat.startswith("usfm"):
            args.extfiles.append(os.path.join(os.path.dirname(infiles[0]), "markers.ext"))
            exts = [x for x in args.extfiles if os.path.exists(x)]
            ingrammar = usfmGrammar(args.grammar, altparser=args.validate, extensions=exts)
        if args.outformat and args.outformat.startswith("usfm"):
            outgrammar = _grammarDoc(args.grammar)

    for infile in infiles:
        outfile = None
        if args.outfile is None:
            outfile = _makeoutfile(infile, args.outformat)
        elif os.path.isdir(args.outfile):
            outf = _makeoutfile(infile, args.outformat)
            if outf is None:
                doerror(f"invalid output format {args.format} in {args.outfile}")
            outfile = os.path.join(args.outfile, os.path.basename(outf))
        elif len(infiles) == 1:
            outfile = args.outfile

        if infile == "-":
            infile = sys.stdin
        if outfile == "-":
            outfile = sys.stdout

        usxdoc = None
        if not args.quiet:
            print(f"{infile} -> {outfile}" if outfile else f"{infile}")
        try:
            usxdoc = readFile(infile, informat=args.informat, grammar=ingrammar,
                              altparser=args.validate)
        except NoParseError as e:
            doerror(f"Failed to parse {infile}: {e}", False)

        if len(infiles) == 1 and usxdoc is None:
            doerror(f"Unable to read in {args.infile}")

        if hookusx is not None:
            hookusx(usxdoc, args)

        if args.nooutput or outfile is None or usxdoc is None:
            continue

        version = usxdoc.version
        if version is None:
            usxdoc.version = args.version or "3.1"
        elif args.version is not None:
            usxdoc.version = args.version

        if not args.canonical:
            usxdoc.canonicalise()

        usxdoc.saveAs(outfile, outformat=args.outformat, addesids=args.esids,
                      grammar=outgrammar, altparser=args.validate, ensure_ascii=args.ascii)

if __name__ == "__main__":
    main()
