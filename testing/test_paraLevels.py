import pytest
import re
from shared import *

def test_paraLevels(usfm):
    leveledMarkers = ["q", "qm", "li", "lim", "iq", "ili", "io"]
    currentPrefix = None
    currentLevel = -1
    lastVerse = None
    failures = []
    for node in usfm.getroot():
        if node.tag != "para":
            continue
        style = node.get("style")
        if style == None:
            continue
        paraVerse = node.get("sid")
        if paraVerse == None:
            paraVerse = node.get("vid")
        if paraVerse:
            lastVerse = paraVerse
        if currentPrefix != None:
            m = re.match(r"^([a-z]+)(\d*)$", style)
            if m and m.group(1) == currentPrefix:
                if currentPrefix == style:
                    level = 1
                else:
                    level = int(style[len(currentPrefix):])
                
                if level == currentLevel:
                    continue
                elif level == currentLevel + 1 or level < currentLevel:
                    currentLevel = level
                else:
                    failures.append(f'at level {currentLevel} and next style was {style} near verse {lastVerse}')
            else:
                currentPrefix = None
        
        if currentPrefix == None:
            m = re.match(r"^([a-z]+)(\d*)$", style)
            if m and m.group(1) in leveledMarkers:
                if len(m.group(2)) == 0:
                    level = 1
                else:
                    level = int(m.group(2))
                if level != 1:
                    failures.append(f'style {style} should not start a block near verse {lastVerse}')
                else:
                    currentPrefix = m.group(1)
                    currentLevel = level
    
    if len(failures):
        failfor(usfm, 'paraLevels', f"{usfm.fname}:\n    " + "\n    ".join(failures))

            
            
