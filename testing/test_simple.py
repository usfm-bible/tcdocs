import pytest

def test_idbk(usfm):
    res = None
    bke = usfm.getroot().find(".//book")
    if bke is not None:
        res = bke.get("code", None)
    if res is None:
        msg = 'missing book code'
        if 'idbk' in usfm.xfails:
            pytest.xfail(msg)
        else:
            pytest.fail(msg)
