import pytest
from shared import *
from usfmtc.usxmodel import iterusx

def test_chapterVerse(usfm):
    ''' Requires chapters and verses to be monotonically sequentially increasing from 1 '''
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

def test_chapterHeadings(usfm, grammar):
    ''' Do not allow headings immediately preceding a chapter. The chapter should come first. '''
    hasheading = False
    failures = []
    for node in usfm.getroot():     # only need top level paragraphs
        if node.tag == "chapter" and hasheading:
            failures.append(f"chapter {node.get('number', 0)} has preceding headings")
        if node.tag != "para":
            continue
        s = node.get('style', None)
        if s is None:
            failures.append(f"missing style for paragraph at {node.pos}")
            continue
        hasheading = grammar.marker_categories.get(s, '') in ('subpara', 'title')
    if len(failures):
        failfor(usfm, 'chapter_headings', f"{usfm.fname}:\n    " + "\n    ".join(failures))
