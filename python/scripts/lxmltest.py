#!/usr/bin/python3

from lxml import etree
import argparse, os, re, sys

try:
    from usfmtc.usxgrammar import usxenums
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
    from usfmtc.usxgrammar import usxenums

relaxns = "{http://relaxng.org/ns/structure/1.0}"

def get_expected_result(d):
    metad = os.path.join(d, "metadata.xml")
    if not os.path.exists(metad):
        return True
    doc = etree.parse(metad)
    res = doc.findtext("./xmlvalidated")
    if res is None:
        res = doc.findtext("./validated").lower() == "pass"
    else:
        res = res.lower()
    return res

parser = argparse.ArgumentParser()
parser.add_argument("infile",help="Input XML file")
parser.add_argument("-g","--grammar",help="Input rnc or rng grammar")
parser.add_argument("-m","--marker",action='append',default=[],help='type=mkr,mka,mkb')
parser.add_argument("-q","--quiet",action="store_true",help="Only output final results")
parser.add_argument("-o","--output",help="Output error reports to this file")
parser.add_argument("-A","--append",action="store_true",help="Append error reports")
args = parser.parse_args()

if args.grammar.endswith(".rnc"):
    with open(args.grammar, encoding="utf-8") as inf:
        usxdoc = inf.read()
    usxrng = etree.RelaxNG.from_rnc_string(usxdoc)
else:
    usxdoc = etree.parse(args.grammar)
    if len(args.marker):
        for s in args.marker:
            t, r = s.split('=')
            mks = re.split(r'[,;\s]\s*', r)
            ty = t.strip()
            e = usxdoc.find('./{0}define[@name="{1}.enum"]/{0}choice'.format(relaxns, usxenums[ty]))
            if e is None:
                print(f"Can't find an enum for {ty}. Tried {usxenums[ty]}")
                continue
            for m in mks:
                v = etree.Element(f'{relaxns}value')
                v.text = m.strip()
                e.insert(0, v)
    newdoc = etree.fromstring(etree.tostring(usxdoc))
    usxrng = etree.RelaxNG(etree=newdoc)

jobfiles = []
if os.path.isdir(args.infile):
    for dp, dn, fn in os.walk(args.infile):
        if "origin.xml" in fn:
            expected = get_expected_result(dp)
            jobfiles.append((os.path.join(dp, "origin.xml"), expected))
else:
    expected = get_expected_result(os.path.basename(args.infile))
    jobfiles = [(args.infile, expected)]

failed = 0
xfailed = 0
if args.output:
    outfile = open(args.output, "a" if args.append else "w", encoding="utf-8")
    myprint = lambda s: outfile.write(s+"\n")
else:
    myprint = print
for f in jobfiles:
    doc = etree.parse(f[0])
    res = True
    if not usxrng.validate(doc):
        if not args.quiet:
            log = usxrng.error_log
            myprint(f"XML: {f[0]} {'Failed' if f[1] else 'Passed'}: {log.last_error}")
        if f[1]:
            failed += 1
    elif not f[1]:
        myprint(f"XML: {f[0]} xFailed. passed when expected to fail")
        xfailed += 1
total = len(jobfiles)
print(f"lxmltest on {args.infile}: {total-failed} passed / {total} => {failed} failed, {xfailed} expected fails")
