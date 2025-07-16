import pytest
from shared import *
from usfmtc.usxmodel import iterusx

def test_idbk(usfm):
    ''' Tests that a file has a book code '''
    res = None
    bke = usfm.getroot().find(".//book")
    if bke is not None:
        res = bke.get("code", None)
    if res is None:
        msg = 'missing book code'
        failfor(usfm, 'idbk', msg)

def test_betweenpara(usfm):
    ''' Fails if there is any text between paragraph type elements '''
    for p in usfm.getroot():
        if notempty(p.tail):
            failfor(usfm, 'betweenpara',
                    f'Text: "{p.tail.strip()}" found between paragraphs at {p.get("vid", "UNK")}')

@pytest.mark.weak
def test_textinnotes(usfm):
    ''' Fails if there is text directly in a note, not inside a subelement '''
    for n in usfm.getroot().findall('.//note'):
        failure = None
        if notempty(n.text):
            failure = n.text.strip()
        for e in n:
            if notempty(e.tail):
                failure = e.tail.strip()
        if failure is not None:
            failfor(usfm, 'textinnotes',
                    f'Text: "{failure}" found inside note at {usfm.fname} {n.get("vid", "UNK")}')
            return

def test_verseinsidebar(usfm):
    errors = []
    for s in usfm.getroot().findall(".//sidebar"):
        for v in s.findall(".//verse"):
            errors.append(v.get("sid", ""))
    if len(errors):
        failfor(usfm, 'verseinsidebar',
                f"The following verses occur in sidebars: {usfm.fname} {errors}")

tagstyles = {
    "chapter": "c",
    "verse": "v",
    "unmatched": " u",
    "table": " t",
    "ref": "ref",
    "optbreak": "//",
    "periph" : " p"
}

def test_attributes(usfm):
    def mkerror(e, a):
        res = f"attribute {a} missing from {e.tag}/{e.get('style', '')}"
        if e.get('vid', None) is not None:
            res += f" {e.get('vid')}"
        return res

    grammar = usfm.grammar
    grammar.attributes[" u"] = ["marker"]
    grammar.attributes[" t"] = ["vid?"]
    grammar.attributes[" p"] = ["alt?", "id?"]
    failures = []
    for e, isin in iterusx(usfm.getroot()):
        if not isin:
            continue
        a = set(e.attrib.keys())
        a.discard("closed")
        a.discard("status")
        if "style" not in a and e.tag not in tagstyles:
            failures.append(mkerror(e, "style"))
        a.discard("style")
        s = tagstyles.get(e.tag, e.get("style", ''))
        if s in ("fig", "rem") or s.startswith("z"):
            continue            # so many figs fail that the error is worthless
        for k in grammar.attributes.get(s, []):
            if k.endswith("?"):
                k = k[:-1]
            elif k not in a:
                failures.append(mkerror(e, k))
            a.discard(k)
        for k in list(a):
            if k.startswith("x"):
                a.discard(k)
        if len(a):
            failures.append(f"Extra attributes: {' '.join(sorted(a))} found in {e.tag}/{e.get('style', '')} at {e.get('vid', 'UNK')}")
    if len(failures):
        failfor(usfm, 'attributes', f"{usfm.fname}:\n    " + "\n    ".join(failures))

