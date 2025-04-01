
def notempty(s):
    if s is None:
        return False
    return len(s.strip()) != 0

def failfor(usfm, tcode, s):
    if tcode in usfm.xfails:
        pytest.xfail(s)
    else:
        pytest.fail(s)

