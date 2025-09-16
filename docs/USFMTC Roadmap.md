# USFMTC Roadmap

This document contains a summary roadmap of agreed changes to the standard in current and future versions. The changes listed here are already approved by the USFMTC and subject to the final release of a given version, may be used in text of that version in anticipation of the release.

## In Discussion

The following documents are in discussion at the USFMTC. Comments are welcomed:

- [U23003 USFM References](https://docs.google.com/document/d/1U0CrIJkU4h4pPOhhifN1y-HJU5f5r6nGD6d2rLuMeeM/edit?tab=t.0)  
- [U25005 Linkages File](https://docs.google.com/document/d/1laqLE89qIal8i1GgoaCtZfW_ltSc0cqoFrPIq7bAZvY/edit)

# Version 3

## 3.1 \- released

Versions 3.1 and 3.1.1 are already released. Explain why there is no list for 3.1 and introduction of USJ, main differences etc.  
The transition from 3.0 to 3.1 is hard to document because 3.0 is not formally specified, and 3.1 is about resolving ambiguities and regularising the grammar. The main differences in 3.1 are:

- USFM, USX and USJ all have the same content model, based on USX.  
- BookTitles are optional  
- Byte Order Mark is allowed at the start of the file  
- BookIdentification may be any 3 letter/digit code  
- Other peripherals may be of any type  
- Bookheaders support \\sts  
- Distinguish Section, Verse and Other paragraph types in the grammar  
- @vid has extended reference syntax  
- Character styles must close explicitly. The only markers with implicit closure are paragraph markers and note (footnote or cross reference) structural markers  
- \+ is optional before a marker since closure is now unambiguous  
- \\ is required to escape certain characters: \\ ' " | \~ //  
- Whitespace rules and canonicalisation rules are given  
- \\fv is now simply a character style and requires closing

### 3.1.1 \- released

- Move p1, p2 from OtherPara to PeriphPara. I.e. they are not used in scripture files  
- Fix optbreak  
- Add \\ipc to correspond to \\pc  
- Add \\lit for use in introductory paragraphs  
- Book codes must contain at least one letter  
- Markers.ext \\category may contain multiple entries

### 3.1.2

- Add lang attribute to \\tl and \\wl  
- Add \\ta [U24002](https://github.com/usfm-bible/tcdocs/blob/main/proposals/2024/U24002%20Textual%20Alternatives.md)  
- Add new marker categories:  
  * cell (tc1..12, tcc1..12, tcr1..12, th1..12, thc1..12, thr1..12)  
  * attribute (cp, vp, usfm, ca, va, cat) indicates the contents are an attribute in USX  
- Add vid milestone to specify current reference from [U25008](https://github.com/usfm-bible/tcdocs/blob/main/proposals/2025/U25008%20vid.md)

## 3.2

- Add explicit unicode to USFM [U25004](https://github.com/usfm-bible/tcdocs/blob/main/proposals/2025/U25004%20Explicit%20Unicode.md)  
- Add \<list\> [U25003](https://github.com/usfm-bible/tcdocs/blob/main/proposals/2025/U25003%20Lists%20and%20Tables.md) optionally  
- Add \* (wildcard) to attributes in markers.ext [U24002](https://github.com/usfm-bible/tcdocs/blob/main/proposals/2024/U24002%20Textual%20Alternatives.md). E.g. a-\* to allow anything with an a- prefix  
- Add node initial attributes [U25001](https://github.com/usfm-bible/tcdocs/blob/main/proposals/2025/U25001%20Attributes.md) e.g. `\ip |aid="author"| The author is unknown`   
- Add anchors [U25002](https://github.com/usfm-bible/tcdocs/blob/main/proposals/2025/U25002%20Anchors.md)  
- Allow character styles in the caption of a \<figure\>, but not notes  
- \\v is not allowed in paragraphs of type otherpara and sectionpara  
- Add new marker categories  
  * standalone (no markers yet). A bare milestone with no attributes or delimiter

# Version 4

- \<list\> is required from [U25003](https://github.com/usfm-bible/tcdocs/blob/main/proposals/2025/U25003%20Lists%20and%20Tables.md)  
- \\xt may not be used as a general character style. It is only used in cross references.  
- 
