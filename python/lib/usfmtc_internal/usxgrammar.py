
import re
import xml.etree.ElementTree as et

alljobs = {
    "BookHeaders":          ("bkhdrs", ("Header.para.style.enum",)),
    "BookTitles":           ("bktitles", ("Title.para.style.enum",)),
    "BookIntroduction":     ("bkintro", ('Introduction.para.style.enum',)),
    "BookIntroductionEndTitles": ("bkintroend", ("Title.para.style.enum",)),
    "ChapterContent":       ("chaptercontent", ),
    "ChapterStart":         ("chapter",),
    "ChapterEnd":           ("chapterend",),
    "Char":                 ("char", ("Char.char.style.enum", "+char.closed", "Attributes", "Break",
                                        "CharContent", "FullChar.char.style.enum", "FullCharExtra.char.style.enum")),
    "CharEmbed":            ("charembed", ("Char.char.style.enum", "+char.closed", "Attributes", "Break",
                                            "FullChar.char.style.enum", "FullCharExtra.char.style.enum")),
    "CrossReference":       ("crossref",("CrossReference.style.enum",)),
    "CrossReferenceChar":   ("xchar",("CrossReferenceChar.char.style.enum", "+char.closed")),
    "Figure":               ("fig",("FigureTwo", "Attributes", "FigureThree")),
    "Footnote":             ("f", ("NoteCharEmbed", "Attributes", "Footnote.style.enum"), ("category", )),
    "FootnoteChar":         ("fchar", ("FootnoteVerse", "FootnoteChars.char.style.enum", "char.closed")),
    "List":                 ("list", ("List.para.style.enum",)),
    "ListChar":             ("listchar", ("+char.closed", "ListChar.char.style.enum",)),
    "Milestone":            ("ms", ("Milestone.style.enum", "Attributes")),
    "Para":                 ("p", ("VersePara", "NonVersePara", "VersePara.para.style.enum", "OtherPara.para.style.enum", "Para.nonpara.style.enum", "Break")),
    "PeripheralDivision":   ("periph", ("Peripheral.FRT.periph.id.enum", "Peripheral.INT.periph.id.enum",
                                        "Peripheral.BAK.periph.id.enum", "Peripheral.OTH.periph.id.enum", "PeripheralContent")),
    "Reference":            ("ref",),
    "Scripture":            ("id", ("BookIdentification", "BookIdentification.book.code.enum", "ChapterContent")),
    "Sidebar":              ("esb",),
    "Table":                ("table", ("TableContent",)),
    "VerseStart":           ("verse",),
    "VerseEnd":             ("verseend",),
    "category":             ("cat",),
}

