#!/usr/bin/env python3

import re
import xml.etree.ElementTree as et

categories = {
    "char":         "Char.char",
    "crossreference":   "CrossReference",
    "crossreferencechar":   "CrossReferenceChar.char",
    "footnote":     "Footnote",
    "footnotechar": "FootnoteChar.char",
    "header":       "Header.para",
    "internal":     "Internal",
    "introchar":    "IntroChar.char",
    "introduction": "Introduction.para",
    "list":         "List.para",
    "listchar":     "ListChar.char",
    "milestone":    "Milestone",
    "otherpara":    "OtherPara.para",
    "sectionpara":  "SectionPara.para",
    "title":        "Title.para",
    "versepara":    "VersePara.para",
}


class SFMFile:
    def __init__(self, fname):
        self.fname = fname
        self.markers = {}
        self.parse()

    def parse(self):
        with open(self.fname, encoding="utf-8") as inf:
            for l in inf.readlines():
                s = l.strip()
                s = re.sub(r'#.*$', '', s)
                if not s.startswith("\\"):
                    continue
                b = s[1:].split(None, 1)
                b = self.preproc(b)
                mk = b[0].lower()
                if mk == "marker":
                    curr = {}
                    self.markers[b[1]] = curr
                else:
                    curr[mk] = b[1]

    def preproc(self, b):
        return b

relaxns = "{http://relaxng.org/ns/structure/1.0}"

class Extensions(SFMFile):
    def preproc(self, b):
        if b[0].lower() == "category":
            b[1] = b[1].lower()
        return b

    def applyto(self, rdoc, factory=et):
        res = False     # nothing added
        allcats = set([x.get('category', "").split()[0] for x in self.markers.values()])
        for a in allcats:
            if a not in categories:
                continue
            ms = [k for k, v in self.markers.items() if a in v.get('category', "").split()]
            enum = categories[a]+".style.enum"
            e = rdoc.find('./{0}define[@name="{1}"]/{0}choice'.format(relaxns, enum))
            allmks = set([v.text for v in e.findall(f'./{relaxns}value')])
            added = False
            for m in ms:
                if m in allmks:
                    continue
                else:
                    v = factory.Element(f'{relaxns}value')
                    v.text = m
                    e.insert(0, v)
                    added = True
            res = res or added
        return res
