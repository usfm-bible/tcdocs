import pytest
from shared import *

def test_threeq2s(usfm):
    q2count = 0
    for i, p in enumerate(usfm.getroot()):
        if p.tag == "q2":
            q2count += 1
            if q2count > 2 and p.get('vid', '') != "ISA 44:24":
                failfor(usfm, "threeq2s",
                        f"Found {q2count} consecutive \\q2 at {p.get('vid', '')} in {usfm.name}")
        else:
            q2count = 0
