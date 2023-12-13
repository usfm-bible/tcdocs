
import re
import xml.etree.ElementTree as et

alljobs = {
    "BookHeaders":          ("bkhdrs", ("BookHeaders.para.style.enum",)),
    "BookTitles":           ("bktitles", ("BookTitles.para.style.enum",)),
    "BookIntroduction":     ("bkintro", ('BookIntroduction.para.style.enum',)),
    "BookIntroductionEndTitles": ("bkintroend", ("BookIntroductionEndTitles.para.style.enum",)),
    "ChapterContent":       ("chaptercontent", ),
    "ChapterStart":         ("chapter",),
    "ChapterEnd":           ("chapterend",),
    "Char":                 ("char", ("Char.char.style.enum", "+char.closed", "Break",
                                        "CharWithAttrib.enum", "CharContent", "FullChar.char.style.enum"), ("+char.link", )),
    "CharEmbed":            ("charembed", ("Char.char.style.enum", "+char.closed", "Break",
                                            "CharEmbedWithAttrib", "CharWithAttrib.enum", "FullChar.char.style.enum"), ("+char.link", )),
    "CharWithAttrib":       ("charattrib", ("CharWithAttrib.enum")),
    "CrossReference":       ("crossref",),
    "CrossReferenceChar":   ("xchar",("CrossReferenceChar.char.style.enum", "+char.closed")),
    "Figure":               ("fig",("FigureTwo", "FigureThree")),
    "Footnote":             ("f", tuple(), ("category", )),
    "FootnoteChar":         ("fchar", ("FootnoteVerse", "FootnoteChar.char.style.enum", "char.closed")),
    "List":                 ("list", ("List.para.style.enum",)),
    "ListChar":             ("listchar", ("+char.closed", "ListChar.char.style.enum",)),
    "Milestone":            ("ms", ("MilestoneWithAttrib.enum", "MilestoneWithAttrib.ms.style.qt", "Milestone.enum")),
    "Para":                 ("p", ("VersePara", "NonVersePara", "Para.para.style.enum", "Para.nonpara.style.enum", "Break")),
    "PeripheralDivision":   ("periph", ("Peripheral.FRT.periph.id.enum", "Peripheral.INT.periph.id.enum",
                                        "Peripheral.BAK.periph.id.enum", "Peripheral.OTH.periph.id.enum", "PeripheralContent")),
    "Scripture":            ("id", ("BookIdentification", "BookIdentification.book.code.enum", "ChapterContent")),
    "Sidebar":              ("esb",),
    "Table":                ("table", ("TableContent",)),
    "VerseStart":           ("verse",),
    "VerseEnd":             ("verseend",),
    "category":             ("cat",),
    "char.link":            ("link",),
}

usxenums = {
    'bookidentification': 'BookIdentification.book.code',
    'peripheralbookidentification': 'PeripheralBookIdentification.book.code',
    'periperhaldividedbookidentification': 'PeripheralDividedBookIdentification.book.code',
    'frt': 'Peripheral.FRT.periph.id',
    'int': 'Peripheral.INT.periph.id',
    'bak': 'Peripheral.BAK.periph.id',
    'oth': 'Peripheral.OTH.periph.id',
    'bkhdr': 'BookHeaders.para.style',
    'booktitles': 'BookTitle.para.style',
    'bookintroduction': 'BookIntroduction.para.style',
    'bookintroductionendtitles': 'BookIntroductionEndTitles.para.style',
    'para': 'Para.para.style',
    'section': 'Section.para.style',
    'list': 'List.para.style',
    'cellalign': 'Cell.align',
    'introchar': 'IntroChar.char.style',
    'char': 'Char.char.style',
    'listchar': 'ListChar.char.style',
    'ms': 'Milestone',
    'footnotechar': 'FootnoteChar.char.style',
    'crossrefchar': 'CrossReferenceChar.char.style',
}

relaxns = "{http://relaxng.org/ns/structure/1.0}"

def addmarkers(rdoc, markers):
    for s in markers:
        t, r = s.split('=')
        mks = re.split(r'[,;\s]\s*', r)
        ty = t.strip()
        e = rdoc.find('./{0}define[@name="{1}.enum"]/{0}choice'.format(relaxns, usxenums.get(ty, None)))
        if e is None:
            print(f"Can't find an enum for {ty}.")
            continue
        for m in mks:
            v = et.Element(f'{relaxns}value')
            v.text = m.strip()
            e.insert(0, v)


