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
        if failure is not None and len(failure):
            failfor(usfm, 'textinnotes',
                    f'Text: "{failure}" found inside note at {usfm.fname} {n.get("vid", "UNK")}')
            return

def test_badtextloc(usfm):
    ''' Tests for text in the wrong places in the file '''
    errors = []
    badlocs = set(["row", "table", "list", "sidebar", "ms"])
    for eloc, isin in usfm.iterusx():
        if isin:
            if eloc.tag in badlocs and notempty(eloc.text):
                errors.append(eloc.get('vid', str(eloc)))
        elif eloc.parent is None or eloc.parent.tag in badlocs:
            if notempty(eloc.tail):
                errors.append(eloc.get('vid', str(eloc)))
    if len(errors):
        failfor(usfm, 'badtextloc',
                f"The following elements contain text they should not in {usfm.name}: {errors}")

def test_badverseloc(usfm):
    ''' Test for all the places \\v should not occur '''
    errors = []
    for eloc, isin in usfm.iterusx():
        if eloc.tag != "verse" or not isin or eloc.get('sid', None) is None:
            continue
        p = eloc.parent
        if p.tag == "para" and p.parent is None:
            continue
        elif p.tag == "cell":
            for a in ("row", "table"):
                p = p.parent
                if p is None or p.tag != a:
                    break
            else:
                if p.parent is None:
                    continue
        else:
            continue
        errors.append(eloc.get('sid', eloc.get('number')))
    if len(errors):
        failfor(usfm, 'badverseloc',
                f"The following verses occur in bad locations: {usfm.fname} {errors}")

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
    ''' Ensures all required attributes exist and reports on extra attributes'''
    currc = "0"
    currv = "0"
    def mkerror(e, a):
        res = f"attribute {a} missing from {e.tag}/{e.get('style', '')}"
        if e.get('vid', None) is not None:
            res += f" {e.get('vid')}"
        else:
            res += f"{usfm.book} {currc}:{currv}"
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
        if s == "c":
            currc = e.get("number")
        elif s == "v":
            oldv = currv
            currv = e.get("number")
            if currv is None:
                currv = oldv
        elif s in ("fig", "rem") or s.startswith("z"):
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

def test_initref(usfm):
    currchap = None
    currverse = None
    for i, e in enumerate(usfm.getroot()):
        if e.tag == "chapter":
            currchap = e.get("number")
            continue
        s = e.get("style", None)
        if usfm.grammar.marker_categories.get(s, '') == "versepara":
            if e.get("vid", None) is not None or s == "d" \
                    or (currchap is not None \
                    and (currverse is not None or (len(e) and e[0].tag == "verse"))):
                break   # we're done testing
            else:
                breakpoint()
                failfor(usfm, "noinitref",
                    f"Initial reference missing in {usfm.fname} at {e.pos}")
        elif e.tag == "ms" and s == "vid":
            if e.get('ref', None) is not None:
                currchap = "1"      # we don't care about the reference itself
                currverse = "1"     # we don't care what the actual value is
