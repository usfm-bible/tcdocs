import pytest

def notempty(s):
    if s is None:
        return False
    return len(s.strip()) != 0

def failfor(usfm, tcode, s):
    if tcode in usfm.xfails:
        pytest.xfail(s)
    else:
        pytest.fail(s)

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

