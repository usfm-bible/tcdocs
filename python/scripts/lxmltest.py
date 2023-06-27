#!/usr/bin/python3

from lxml import etree
import argparse, os

parser = argparse.ArgumentParser()
parser.add_argument("infile",help="Input XML file")
parser.add_argument("-g","--grammar",help="Input rnc or rng grammar")
args = parser.parse_args()

with open(args.grammar, encoding="utf-8") as inf:
    usxdoc = inf.read()
if args.grammar.endswith(".rnc"):
    usxrng = etree.RelaxNG.from_rnc_string(usxdoc)
else:
    usxrng = etree.RelaxNG(file=args.grammar)

jobfiles = []
if os.path.isdir(args.infile):
    for dp, dn, fn in os.walk(args.infile):
        if "origin.xml" in fn:
            jobfiles.append(os.path.join(dp, "origin.xml"))
else:
    jobfiles = [args.infile]

failed = 0
for f in jobfiles:
    doc = etree.parse(f)
    if not usxrng.validate(doc):
        print(f"{f} failed")
        failed += 1
total = len(jobfiles)
print(f"{total-failed} passed / {total} => {failed} failed")
