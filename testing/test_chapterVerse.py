import pytest
from shared import *
from usfmtc.usxmodel import iterusx

def test_chapterVerse(usfm):
    nextChapter = 1
    nextVerse = 1;
    failures=[]
    for node, isin in iterusx(usfm.getroot()):
        if not isin:
            continue
        if node.tag == "chapter" and node.get("eid") is None:
            chapter = int(node.get("number"))
            if chapter != nextChapter:
                failures.append(f'chapter {nextChapter} expected, got {chapter}')
            nextChapter = chapter + 1
            nextVerse = 1
        elif node.tag == "verse" and node.get("eid") is None:
            verseStr = node.get("number");
            parts = verseStr.split("-")
            if len(parts) == 1:
                verseStart = verseEnd = parts[0]
            else:
                verseStart = parts[0]
                verseEnd = parts[1]
            verse = int(verseStart)
            if verse != nextVerse:
                failures.append(f'verse {chapter}:{nextVerse} expected, got {verse}')
                if verse == nextVerse + 1:
                    nextVerse = verse + 1
            else:
                nextVerse = int(verseEnd) + 1
    if len(failures):
        failfor(usfm, 'chapter_verse', f"{usfm.fname}:\n    " + "\n    ".join(failures))
