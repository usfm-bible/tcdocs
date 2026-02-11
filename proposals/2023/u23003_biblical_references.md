# USFM Scripture Referencing Standard

M. Hosken and USFM Technical Committee

Version 1.0

# Executive Summary

This document introduces a scheme for biblical references. It aims to allow the referencing of any content in a scripture file down to the character level. In particular it features the ability to reference:

- words & characters  
- notes (footnotes, etc.), section headings, introductory material  
- marker attributes  
- across scripture sources

Some examples

```
MAT 2:1!3      # third word of Matthew chapter 2 verse 1
MAT 2:1!3-4    # words 3-4 of Matthew chapter 2 verse 1
MAT 2:1!3-2!4  # word 3 of Matthew 2:1 to verse 2 word 4
MAT 2:1!3-2:4  # word 3 of Matthew 2:1 to chapter 2 verse 4
MAT 2:1-4      # verse 1 to 4 of Matthew chapter 2
MAT 2-4        # chapters 2 to 4 of Matthew
```

As an extreme example we could use `en-t-wsg+sil.MAT 1:1!f!5+6` for the 6th character in the 5th word in the first footnote in Matthew chapter 1 verse 1 in the wsg back translation (into English) SIL project. Although this is overkill for nearly all situations and nobody would ever type such a thing\!



# Introduction

This document is a normative basic standard for scripture references. Notice it is not concerned with localised references, even for English. There already exists an informal specification for scripture references which resolves within a particular translation down to the verse level. But there are desires to extend this reference in other directions: 

- To be recognisable as a standard book, chapter, verse reference.
- To be able to reference text in other translations.
- To be able to reference a word or even part of a word within a verse.
- To be able to reference any text, even non scriptural text, within a text file. This does not include syntactic characters like <> around an element tag in USX or = or " in attributes in USFM, etc. These are not part of the data model.
- To treat USFM, USX and USJ files identically. References are to data in the data model, not a particular serialisation. The closest serialisation to the underlying data model is USX.
- To be able to inject / associate material (notes, implicit information, illustrations, etc.) directly into the text with surgical precision.  
- To allow milestone-dependent features without having to insert milestone markers into the text

---
# Executive Summary (Alternate)

This document defines a **normative, serialization-independent scheme for scripture references**.
All references in this scheme are treated as **ranges**, which may be progressively refined—from book, to chapter, to verse, to word, and finally to character.

The scheme is designed to allow **precise, unambiguous identification of any textual content in a scripture file**, independent of whether that content is represented in USFM, USX, or USJ. References operate on the underlying data model rather than on any particular file serialization.

In particular, the scheme supports referencing:

* verses, words, and individual characters
* notes (footnotes, cross-references), section headings, and introductory material
* marker attributes and other associated non-scriptural text
* content across translations and scripture products

### Examples

```
MAT 2:1!3        # third word of Matthew chapter 2 verse 1
MAT 2:1!3-4      # words 3–4 of Matthew chapter 2 verse 1
MAT 2:1!3-2!4    # word 3 of Matthew 2:1 to verse 2 word 4
MAT 2:1!3-2:4    # word 3 of Matthew 2:1 to chapter 2 verse 4
MAT 2:1-4        # verses 1 to 4 of Matthew chapter 2
MAT 2-4          # chapters 2 to 4 of Matthew
```

As an extreme example, the reference:

```
en-t-wsg+sil.MAT 1:1!f!5+6
```

identifies the **6th character of the 5th word in the first footnote** attached to Matthew 1:1 in the *wsg* back translation (into English) for the SIL project. While such references are rarely written by hand, they illustrate the expressive power and precision of the scheme.

# Introduction (Alternate)

This document defines a **normative, foundational standard for scripture references**. It is not concerned with localized reference conventions (even for English), but with a **general, language-independent reference scheme**.

Existing informal scripture reference conventions resolve references within a single translation and typically only to the verse level. This standard extends that model to support a broader and more precise set of requirements, while remaining recognizable as a conventional book-chapter-verse reference.

Specifically, the scheme is designed:

* to remain recognizable as a standard book, chapter, and verse reference
* to reference text across different translations and scripture products
* to reference individual words or parts of words within a verse
* to reference any textual content within a scripture file, including non-scriptural material such as notes and headings
  (excluding syntactic markup characters, such as  <> around an element tag in USX or a backslash \\ in USFM, which are not part of the underlying data model)
* to treat USFM, USX, and USJ files identically by referencing the shared data model rather than any particular serialization
  (with USX being closest to that underlying model)
* to allow notes, implicit information, illustrations, and similar material to be associated with the text with precise positional control
* to support milestone-dependent features without requiring the insertion of milestone markers into the text

  ---

# Basic Reference

The current basic reference consists of a book ID, a chapter number and a verse number, which may have an informal verse subsection reference (e.g. a). The `Wordref` and `Charref` grammatical elements are discussed later.

```py
Reflist = RefRange (ws* refsep ws* RefRange)*
RefRange = Reference (ws* "-" ws* Reference)?
Reference = FullRef | ContextRef | NameRef

FullRef = BookId (ws+ Chapter (chaptersep Verse)? Wordref?)?
ContextRef = Chapter (chaptersep Verse)? Wordref?
    	| Verse Wordref? | WordrefOnly Mrkref* | Charref Mrkref*
refsep = ";" | ","
bidi = "\u200E" | "\u200F"
```

What is being described is a list of references, although the list may degenerate to a single reference. The core concept is that everything in a reference is a range, whether it is explicitly expressed as a range or as a single reference. For example `GEN 1` is implicitly the range `GEN 1:1-1:31`. Even a verse is a range of words inside the verse. We can consider `GEN 1:23` to be a sequence of refinements. We start with the book `GEN`, which is effectively `GEN 1:1-50:33`. This is refined by the chapter number to just the range above, and then verse 23 refines the chapter to just the verse. That verse is itself a range of words in the verse and so on all the way down to a range of characters.

An implementation will typically have three top level objects. The Reference is the most limited object and refers to a single location in the text. Given that a reference is also a range, the precise location is interpretted either as the end of the range or the beginning depending on application context. Typically a reference refers to the start of a range, but when it is the second in an explicit range then the end of its range is used. A RefRange consists of a starting and ending reference. They may both be the same (in which case the second is optional), since the first reference is interpretted as its start and the second its end. A Reflist is the most generic and may consist of a list of RefRanges (which in turn may be references).

A reference may consist of a full reference or a contextual reference. We will return to named references (`NameRef`) in a much later section. A full reference starts with a book id and has the necessary chapter and verse if needed.  It is awkward to always use full references. Notice that the example did not say `GEN 1:1-GEN 1:31`. People do not express references that way. They may well use `GEN 1:1-31`. The second reference in the range is a contextual reference. It is based on the previous reference (`GEN 1:1`) and is considered relative to it. To formalise and disambiguate contextual references. A contextual reference is relative to the parent of the previous reference. Thus `GEN 1:1` is a verse with chapter 1 as its parent. Thus `31` is relative to `GEN 1`. This also works for `GEN 1-31`. Here the first reference is a chapter and its parent is the book, thus the `31` here is relative to `GEN` and so is a chapter. There is another shorthand used in scripture references which is not supported. For example some people will use GEN 1:23-4. An implementation may support this if it wants, but it is not required and such references should never be generated.

The book of Jude has only one chapter. What therefore does `JUD 1-4` mean? It could mean Jude chapters 1-4. But that is not valid. Instead interpreting the range as `JUD 1:1-1:4` makes better sense.  In effect a reference to JUD is both a full book range and also a chapter range already. When refining JUD, we in effect are refining JUD 1. This only applies to primary text references (being discussed now). For other types of references, JUD refers to the whole book.

Unfortunately, it is not possible to resolve whether a book is single chapter or not within the grammar itself and so identifying that `JUD 1-4` in effect means `JUD 1:1-1:4` is up to the processor. This is no different from deciding whether `MAT 3:158` is out of range, which is also not achievable via the grammar and only by the processor.

In right to left script contexts, it is sometimes necessary to add bidirectional control characters to the reference to give appropriate layout.

## Chapter Verse

```py
chaptersep = bidi? ( ":" | "." )
Chapter = digits
Verse = digits Subverse? | Subverse | "end"
Subverse = letter
```

The chapter number is always a number in ASCII digits. Likewise for the verse. But verses can be more complicated. A verse may take a subverse letter as in `LUK 11:2b`. Only a simple ascii lowercase letter may be used for a subverse identifier. A verse may also be the keyword `end` which is the last verse in the chapter. Implementations may use a verse number greater than the last verse in the chapter internally.

There are also bridged verses in some translations, e.g. `LUK 11:34-35`. There is no special treatment for bridged verses. They are treated as a normal verse range. If a range is required, for example we want to extend to the end of that paragraph an initial thought might be `LUK 11:34-35-36` but this is identical in meaning to `LUK 11:34-36`. The correspondence also extends to verse lists, which are simply treated as reference lists.

### Versification Schemes

Different translations may work to different versifications. For example: the NIV has `MAL 3:1-18; 4:1-6` while a typical French translation will have `MAL 3:1-24`. A scripture reference is interpretted according to the versification of the scripture being referenced. Thus references to other translations are assumed to be interpretted according to that translation referenced and not the translation from where it was referenced. A higher level protocol (e.g. Module format) may override this to say that references within its file are interpreted according to a different versification. The handling of such matters is outside the scope of this standard.

## Book Identifiers

```py
BookId = (TransId booksep)? BookCode
booksep = ":" | "."
BookCode = capital (capital | digit){2}
  	| digit (capital{2} | digit capital | capital digit)
TransId = Langtag ("+" Transcode ("+" Productid)?)?
```

A BookId consists of 3 digits or upper case letters of which one must be a letter in order to distinguish a book from a chapter or verse. A standard list of book codes is given in Appendix 1\.

### Translation Reference

This work builds on discussions held on how to reference not only a translation but a scripture product. In summary, a scripture product reference is a sequence of components separated by `+`. The complete string of components may be truncated at the point where no other information is needed to disambiguate the product / translation. The components are:

#### *Language Tag*

```py
Langtag = Lang ("-" Script)? ("-" Region)? ("-" Variant)*
           	("-" Ns ("-" Extval)+)*
lang = letter{2,3} ("-" Extlang)?
Extlang = letter{3}
Script = letter{4}
Region = letter{2}
Variant = letter{5,8}
Ns = letter
Extval = letter{5,8}
letter = "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" |
   	"k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t" |
   	"u" | "v" | "w" | "x" | "y" | "z"
```

The language tag component consists of a [BCP47 language tag](https://www.rfc-editor.org/info/bcp47). The only difference is that the language tag is expressed entirely in lowercase. Notice that the components of a language tag are separated by `-`. For details of the grammar of a language tag, see the full grammar. Only a subset of BCP47 is used here, but it is nearly full and sufficient for identifying translations.

#### *Translation ID*

```py
Transcode = id
```

There are a number of translations even within a language group. This is even discounting the 200 English translations. Consider, for example, the New International Version (NIV). The code for this translation could well be NIV. But there are many versions of the NIV. These can be further identified, separated by a hyphen \- as in a language tag. Thus `niv-1978`.

The implications of this naming scheme is for some kind of registry or registries. For any given language tag, there needs to be one list of translation ids, even if only to have an implicit id for the language tag, such that if a new translation comes along, the old default, empty id, keeps referring to the same translation, if so desired. In the case of English, which is the one language that is the outlier of complexity for this system, there needs to be an agreed registry. While such a registry is needed for this standard, it is beyond the scope of this standard to specify one or to be dependent on its existence. Such a registry might then, for example, equate niv and niv-2011. This equivalence could change in the future.

#### *Product ID*

```py
Productid = id
id = idinit , idmid* , [ idfinal ]
idinit = letter | "_" 
idmid = letter | digit | "_"
idfinal = letter | digit
digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
digits = digit+
```

When it comes to a verse reference, the product ID is unlikely to be needed. The product ID may be used to identify different scripture products associated with the translation. Examples of products would be various study editions. Again, there needs to be a list for each translation id of the recognised product ids. How this is managed is outside the scope of this standard.

To alleviate the need somewhat, we propose that the default product id for a translation be `text`. This allows other product ids to be added without having to first define a default. In effect `en+niv.GEN` is the same as `en+niv+text.GEN`.

# Word And Character References

```py
Wordref = (wordrefSep WordrefOnly | Mrkref) Mrkref*
WordrefOnly = (digits | "end") (charrefSep Charref)?
Charref = (digits | "end") "+"?
wordrefSep = "!"
charrefSep = "+"
```

At the other end of the scale is the desire to reference words or even characters within a verse. Extending the range model where we say that a chapter is a range of verses, we can say that a verse is a range of words and a word is a range of characters. The word index is separated from the verse by `!` and the character index from the word index by `+`. The word `end` may also be used as the last word in the verse or character in the word.

There are various issues to address with this model:

- What constitutes a word? Most languages have a clear word break (a space), but some do not. Care needs to be taken in specifying a word break model.  
- Scripture can contain both primary scripture text and also out of band associated text in the same scripture file, like footnotes or other items.  
- At the character level there is the question of what constitutes a character? Is text, in Unicode terms, interpreted as NFD or NFC? Is punctuation considered part of a ‘word’?  
- How are word and character references included in a reference unambiguously?

Since a scripture reference is designed to identify the same ranges regardless of the serialisation of the text, whether in USFM, USX or USJ, the text is analysed without any character level markup. For example, \\\~ in USFM is a single \~ character and not two characters. Likewise \&emdash; in USX is a single character and not a word.

## Word segmentation

Accurate word segmentation is a difficult problem, particularly for non-wordspaced languages. Such languages do not have spaces between words, instead they use spaces as discourse or grammatical markers. Thankfully there are some factors in our favour. Scriptural texts are highly controlled. By this we mean that such texts are carefully edited and characters that would otherwise be missing from normal documents in a language, can and are inserted in scripture text. A primary example  of this is the zero width space (ZWSP, U+200B). This invisible character acts like a space for word segmentation and Iinebreaking, but otherwise is not seen. Therefore we can assume that any necessary character for word segmentation can be inserted.

Linguistically accurate word segmentation is not required. The reason for character locations to be identified by word is that it makes indexing by humans easier. Humans are not expected to come up with character level references over a long range of characters. So refining a range to a word first before counting characters is helpful. Thus it is sufficient for a ‘word’ in this context, to be defined as a sequence of non-space characters whether those characters are strictly word-forming or not. This also mitigates any arguments over what is truly a word or not in a particular language.

While the USFM standard considers any space characters other than those in ASCII (i.e. space, tab, carriage return, newline) to be content characters that must not be changed, they are not considered word-forming in any way. They are also often effectively invisible in that it is not possible to count how many space characters are in a sequence. Punctuation characters are also non-word-forming, but are visible and countable. Therefore we include them as being referenceable. Also this mitigates the question of when a punctuation character gets used as a word-forming character. A marker delimits a word, but may itself be considered part of the final character of that word. Multiple spaces may include content spaces, but they are ignored for referencing purposes. The precise set of space characters is given in the main grammar. ZWSP (U+200B) is included as a space character. Bidi controls are also treated as word delimiting.

```py
ws = " " | [\u00A0\u1680\u2000-\u200B\u200E\u200F\u202A-\u202F
            \u205F\u2066-\u2069\u3000]
```

In summary, a word is a sequence of non-space characters. In addition a marker or element delimits a word. Thus

`"anthro\f + \ft human\f*pomorphic"`

is two words, with the `+` and `human` not being counted, since they are part of a note. See later for access to note and other text not considered part of the main scripture text.

Word and character indexing are 1 based, that is the first word is numbered 1 and so on. As with verse numbers, we reserve the word "end" to signify the last word in a verse. 

## Character References

Within a word, we consider characters, as discussed above. Characters, therefore, are indexed from the beginning of a word. Even a character is a range, it consists of the character plus any non scriptural text groupings following it, as will be discussed later. But it also includes the gap between it and the next scriptural character. There are times when it is desirable to associate information with such a gap, for example implied Hebrew morphology. We use an extra \+ for this. Accessing the position before a word can use character position 0, for example `GEN 2:3!4+0`.

As with verses and words, we support the use of "end" for the end of a word. The range of values for a character index is 0 to the length of the word in characters, inclusive. A character reference may not reference outside the  word it is based on.

The purpose of character indexing is to allow access to the smallest components of a word, including individual diacritics. For this reason, character indexing proceeds by treating text as being in the decomposed normalization (NFD). This is in contrast to most text which is stored composed (NFC). The effect of this is that it is hard for humans to interpret character indices.

## Examples

| Range | Description |
| :---- | :---- |
| `GEN 7:8!2-6` | Genesis ch 7 vs 8 words 2-6 |
| `GEN 7:8!2-12!3` | Genesis ch 7 vs 8 word 2 to vs 12 word 3 |
| `wsg-gong.JHN 3:16` | John 3:16 from the Gondi translation and Gunjala script |
| `en-t-wsg:JHN 3:16` | John 3:16 from the Gondi back translation into English |
| `en-t-wsg.MAT 1:1!5+6` | All that for a single letter\! (6th letter of 5th word in Mat 1:1) |

# Non Scriptural Text

Scripture files consist of more than just pure scripture text. They often contain subheadings, footnotes, cross references, and introductory paragraphs. They also contain introductory paragraphs to set things like table of contents identifiers, headers, etc. Markers may have attributes that contain extra information. There are different categories of markers and how they work with regard to referencing.

```py
Mrkref = "!" id ("[" digits "]")? (wordrefSep WordrefOnly)?
```

## Notes

Notes correspond to <note> elements in the USX and include footnotes and cross references. They are anchored following a particular character, and are considered part of the preceding character (and so word). As stated earlier a character reference is a range including all the non scriptural text following the character. For example, consider this USFM fragment:

```
\v 2 Hello\f + \fr 1:2\ft A greeting\f* everyone
```

A reference to the word greeting might be: `1:2!1!f!3` This is a reference to chapter 1 verse 2, the first word (which includes the following note, since it is part of the last character of the word), the first f marker following and its 3rd word (considering the `1:2` after the \\fr as the first word). The reference could also be shortened to `1:2!f!3`. This is interpreted as chapter 1 verse 2, the first f marker in the verse and its 3rd word.

If there is more than one occurrence of a marker in a range and we want to reference after the first, we use `[]` as in `6:8!f[3]`. Notice that we count from 1, thus `1:2!f` is equivalent to `1:2!f[1]`.

## Section Headings

It is awkward to refer to a section heading in terms of the verse that precedes it. In effect, section paragraphs are associated with the text that follows them, rather than the text that precedes them. Consider this example USFM fragment:

```
\c 1
\p
\v 12 At once the Spirit made him go into the desert,
\v 13 where he stayed 40 days, being tempted by Satan.
Wild animals were there also, but angels came and helped him.
\s1 Jesus Calls Four Fishermen
\r (Mt 4.12-22; Lk 4.14-15; 5.1-11)
\p
\v 14 After John had been put in prison, Jesus went to Galilee
and preached the Good News from God.
```

The subheading text in the `\s1`[^1] is associated with 1:14 rather than 1:13. We might reference the word Four via `1:14!s1!3`.

[^1]:  Markers themselves are not strictly part of any text, they are metadata governing the structure and formatting of the text. References are only concerned with text.

By saying that non verse paragraphs are associated with the first word in the following verse paragraph, we get around any confusion. For example, if a subheading occurs before a paragraph that does not start with a new verse, then the subheading is associated with the first word of the new paragraph, and so as part of the previous verse. Notice that here we are deviating from a strict refinement model. In effect, we refine inwards if appropriate, but if something in the reference is best dealt with by expanding the refinement, we do that. In this case, an expansion of the refinement goes out to the paragraph and all preceding subheading paragraphs.

Section heading markers are identified in the USFM grammar with a marker category of `sectionpara`. The current list as of 3.1.1 is cd, cl, iex, mr, ms, ms1, ms2, ms3, mte, mte1, mte2, r, restore, s, s1, s2, s3, s4, sd, sd1, sd2, sd3, sd4, sp, sr.

The `\\\\cl` marker is interesting. There are two ways it is used, either before the first chapter or following any particular chapter. In both cases it is a paragraph marker. Following a chapter it is treated like any other section heading. Before chapter one it is referenceable like an introductory paragraph.

## Introductory Paragraphs

With no verse to anchor to, referencing introductory material can be problematic. Using range refinement, we can treat the whole book as a range and then refine it based on the nth occurrence of a marker in a file. For example:

```
\id MRK - Good News Study Bible - Notes Material
\is1 The Story
\ip \bk Mark's\bk* story of Jesus is told quickly and with an
abundance of details that enhance its dramatic impact. Jesus
appears suddenly in Judea, where he joins those who are being
baptized in the Jordan by John the Baptist. Just as suddenly,
he returns to Galilee, where he proclaims the message that the
\w kingdom of god\w* is about to arrive…
\c 1
\p
\v 1 sample verse
```

There are a couple of ways to refer to the word  kingdom here. `MRK 0!ip!53` involves a lot of counting. The `0` for the chapter references material before chapter 1 and is necessary because there needs to be a chapter number between a book and a word reference. And then we count 53 words into the paragraph. This is not uncommon with lots of introductory material. Notice that all the text in the marker is included, even the primary text in any markers within that paragraph. Alternatively  `MRK 0!ip!w!1` also does the job. This is again based on range refinement. `MRK 0!ip` refines the book of Mark to the first ip marker contents. Within that we refine further using `!w` to the first w marker contents and then we find the first word in that.

## Attributes

Character markers may take attributes. For example:

```
\v 1 L'\w Éternel|strong="H3068"\w* \w dit|strong="H559"
x-morph="strongMorph:TH8799"\w* à \w Abram|strong="H87"\w*:
Va-t-\w en|strong="H3212" x-morph="strongMorph:TH8798"\w* de ton.
```

Things can get messy when auto generated text gets involved\! For some strange reason we want to refer to the strong attribute for the 8th word en (L',  Éternel, dit, à, Abram, :, Va-t-, en). It has a value of H3212. There are different ways of writing the reference. `1:1!8!strong` counts to the 8th word. Notice that while there is no space before the `\w`, it is considered a separate word. In this example case, the 8th word cannot be refined by the `strong`. Instead we expand the refinement to the containing element (`w`) and then refine back to the attribute. Alternatively the reference might be: `1:1!w[4]!strong` which counts `\w` and then gets the strong attribute.

To make things easier, we consider a marker's attributes to be associated with every character in the main text of the marker. Milestones, of course, have no main text in the marker and so the attributes can only be referenced via the milestone marker, as per the second reference in the example above.

Due to the overloading of `!` there is a constraint that attribute names cannot be the same as contained marker names.

Another example is:

```
\v 2 Hello\f + \cat rephrase\cat*\fr 1:2\ft A greeting\f* everyone
```

One might think that the category may be referenced as `1:2!f!cat`. This makes sense in USFM markup terms, with the cat marker inside the footnote. But the underlying data model is closest to USX and in USX the cat becomes a category attribute. This means that cat is not the correct reference. Instead it is `1:2!f!category`. Also `greeting` is still the 3rd word and not the 4th in the footnote. In addition, since we are working with a USX based model, the caller is accessed as an attribute as in `1:2!f!caller`. Verse numbers are also `2:1!number` for example.

Attribute names are not referenceable since you need to include the attribute name in the reference to reference the name, which seems rather circular and redundant.

## Paragraphs

This mechanism also allows for further limiting a verse range to a particular paragraph within that verse range. This isn't strictly non-scriptural text, but it applies. Consider the following fragment, which occurs in LUK 8:

```
\p
\v 9 Then the \w disciples\w* said, “Teacher! What is the
meaning of this parable?” they asked Jesus.
\v 10 So Jesus said, “God gave you the knowledge to know about his
kingdom. But in order to fulfil that which is written in scripture,
I am telling them with parables. Therefore
\q1 ‘They will look but not see [it],
\q2 they will listen but they don't understand’
\m he told like that the disciples.
```

We can reference the q1 paragraph as `LUK 8:10!q1` with or without the `[1]`. A key question is: how can we reference the text from the start of verse 10 up to the start of the q1 paragraph? The reference `LUK 8:10` consists of everything in this example following `\v 10`.  We need, somehow, to be able to reference the containing paragraph. And this is what we allow. The containing paragraph is considered to be the first paragraph before a reference. Thus `LUK 8:10!p` references just the text in the verse in its containing paragraph (which is of type p). Unfortunately, this makes implementing reference range extraction something beyond what a regular expression can handle (even if it could handle all the rest\!)

# Identifiers

Referencing paragraphs not within the standard CV structure can be problematic, having to count what can be a lot of introductory paragraphs, and then to see them go out of alignment if a paragraph gets inserted. An alternative approach is to label paragraphs in some way. The specification for a reference is extended to support non CV addressing of material.

```py
Reference = FullRef | ContextRef | NameRef
NameRef = BookId (ws+ Namespace chaptersep Nameval) Wordref?
Namespace = letter+
Nameval = NameInit NameChar*
NameChar = [\p{L}\p{Nl}\p{Other_ID_Start}\p{Mn}\p{Mc}
		    \p{Nd}\p{Pc}\p{Other_ID_Continue} -\p{Pattern_Syntax}
            -\p{Pattern_White_Space}]
NameInit =  [\p{L}\p{Nl}\p{Other_ID_Start}-\p{Pattern_Syntax}
            -\p{Pattern_White_Space}]
Other_ID_Start = [\u1885\u1886\u2118\u212E\u309B\u309C]
Other_ID_Continue = \u00B7\u0387\u1369-\u1371\u19DA\u200C\u200D
            \u30FB\uFF65]
Pattern_Space = [\u0009-\u000D\u0020\u00B5\u200E\u200F\u2028\u2029]
```

Pattern\_Syntax is too long to include but does include all standard ASCII punctuation. Notice that hyphen: `-` is in this list and so would not be allowed as part of an identifier, which is just as well given it is used to specify reference ranges.

The NameRef is split into a Namespace and NameVal. The NameSpace parallels the chapter number, but is non-numeric, unlike a chapter number. The NameSpace gives the type of the reference and the NameVal component, which is akin to the verse number, is the identifier as interpreted by the NameSpace. Namespaces are reserved by this standard and may only be added through this standard. Those currently defined are:

| Namespace | NameVal interpretation |
| :---- | :---- |
| a | Value of the @aid attribute in an appropriate element (see USFM U25002) |
| k | Keyword identifier (either @key or the text value folded into an identifier) |
| t | @aid for a table/row/column. E.g. NEH t:Israel/6/1 |

The `k` namespace locates paragraphs containing a `\k` element. If the element has a @key attribute, that is used for its identifier. Otherwise a key is generated from the text of the element by deleting all characters that are not in a NameChar (or NameInit for the first character). The paragraph containing the \\k element is what is matched by the k:.

# Conclusion

Here we bring together all the grammar fragments into a complete grammar:

```py
Reflist = RefRange (ws* refsep ws* RefRange)*
RefRange = Reference (ws* "-" ws* Reference)?
Reference = FullRef | ContextRef | NameRef

NameRef = BookId ws+ Namespace chaptersep Nameval Wordref?
Namespace = letter+
Nameval = NameInit NameChar*
NameChar = [\p{L}\p{Nl}\p{Other_ID_Start}\p{Mn}\p{Mc}
		    \p{Nd}\p{Pc}\p{Other_ID_Continue} -\p{Pattern_Syntax}
            -\p{Pattern_White_Space}]
NameInit = [\p{L}\p{Nl}\p{Other_ID_Start}-\p{Pattern_Syntax}
    		-\p{Pattern_White_Space}]

FullRef = BookId (ws+ Chapter (chaptersep Verse)? Wordref?)?
ContextRef = Chapter (chaptersep Verse)? Wordref?
    	| Verse Wordref? | WordrefOnly Mrkref* | Charref Mrkref*

BookId = (TransId booksep)? BookCode
booksep = ":" | "."
BookCode = capital (capital | digit){2}
  	| digit (capital{2} | digit capital | capital digit)
TransId = Langtag ("+" Transcode ("+" Productid)?)?
Langtag = Lang ("-" Script)? ("-" Region)? ("-" Variant)*
           	("-" Ns ("-" Extval)+)*
lang = letter{2,3} ("-" Extlang)?
Extlang = letter{3}
Script = letter{4}
Region = letter{2}
Variant = letter{5,8}
Ns = letter
Extval = letter{5,8}
Transcode = id
Productid = id

refsep = ";" | ","
chaptersep = bidi? ":" | "."
Chapter = digits
Verse = digits Subverse? | Subverse | "end"
Subverse = letter
wordrefSep = "!"
WordrefOnly = (digits | "end") (charrefSep Charref)?
Wordref = (wordrefSep WordrefOnly | Mrkref) Mrkref*
charrefSep = "+"
Charref = (digits | "end") "+"?
Mrkref = "!" id ("[" digits "]")? (wordrefSep WordrefOnly)?

id = idinit idmid* idfinal?
idinit = letter | "_"
idmid = letter | digit | "_"
idfinal = letter | digit
digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
digits = digit+
ws = " " | [\u00A0\u1680\u2000-\u200B\u200E\u200F\u202A-\u202F
            \u205F\u2066-\u2069\u3000]
bidi = [\u200E\u200F]
letter = "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" |
   	"k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t" |
   	"u" | "v" | "w" | "x" | "y" | "z"
capital = "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" |
    	"K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T" |
    	"U" | "V" | "W" | "X" | "Y" | "Z"
```

# Appendix 1\. Book Codes

The following is the standard list of book codes for purposes of interchange.	

| 3 Ltr | Index[^2] | Name |
| :---- | :---- | :---- |
| GEN | 01 | Genesis |
| EXO | 02 | Exodus |
| LEV | 03 | Leviticus |
| NUM | 04 | Numbers |
| DEU | 05 | Deuteronomy |
| JOS | 06 | Joshua |
| JDG | 07 | Judges |
| RUT | 08 | Ruth |
| 1SA | 09 | 1 Samuel |
| 2SA | 10 | 2 Samuel |
| 1KI | 11 | 1 Kings |
| 2KI | 12 | 2 Kings |
| 1CH | 13 | 1 Chronicles |
| 2CH | 14 | 2 Chronicles |
| EZR | 15 | Ezra |
| NEH | 16 | Nehemiah |
| EST | 17 | Esther |
| JOB | 18 | Job |
| PSA | 19 | Psalms |
| PRO | 20 | Proverbs |
| ECC | 21 | Ecclesiastes |
| SNG | 22 | Song of Songs |
| ISA | 23 | Isaiah |
| JER | 24 | Jeremiah |
| LAM | 25 | Lamentations |
| EZK | 26 | Ezekiel |
| DAN | 27 | Daniel |
| HOS | 28 | Hosea |
| JOL | 29 | Joel |
| AMO | 30 | Amos |
| OBA | 31 | Obadiah |
| JON | 32 | Jonah |
| MIC | 33 | Micah |
| NAM | 34 | Nahum |
| HAB | 35 | Habakkuk |
| ZEP | 36 | Zephaniah |
| HAG | 37 | Haggai |
| ZEC | 38 | Zechariah |
| MAL | 39 | Malachi |
| MAT | 41 | Matthew |
| MRK | 42 | Mark |
| LUK | 43 | Luke |
| JHN | 44 | John |
| ACT | 45 | Acts |
| ROM | 46 | Romans |
| 1CO | 47 | 1 Corinthians |
| 2CO | 48 | 2 Corinthians |
| GAL | 49 | Galatians |
| EPH | 50 | Ephesians |
| PHP | 51 | Philippians |
| COL | 52 | Colossians |
| 1TH | 53 | 1 Thessalonians |
| 2TH | 54 | 2 Thessalonians |
| 1TI | 55 | 1 Timothy |
| 2TI | 56 | 2 Timothy |
| TIT | 57 | Titus |
| PHM | 58 | Philemon |
| HEB | 59 | Hebrews |
| JAS | 60 | James |
| 1PE | 61 | 1 Peter |
| 2PE | 62 | 2 Peter |
| 1JN | 63 | 1 John |
| 2JN | 64 | 2 John |
| 3JN | 65 | 3 John |
| JUD | 66 | Jude |
| REV | 67 | Revelation |
| TOB | 68 | Tobit |
| JDT | 69 | Judith |
| ESG | 70 | Esther Greek |
| WIS | 71 | Wisdom of Solomon |
| SIR | 72 | Sirach also Ecclesiasticus |
| BAR | 73 | Baruch |
| LJE | 74 | Letter of Jeremiah |
| S3Y | 75 | Prayer of Azariah and the Song of the Three Jews |
| SUS | 76 | Susanna |
| BEL | 77 | Bel and the Dragon |
| 1MA | 78 | 1 Maccabees |
| 2MA | 79 | 2 Maccabees |
| 3MA | 80 | 3 Maccabees |
| 4MA | 81 | 4 Maccabees |
| 1ES | 82 | 1 Esdras (Greek) |
| 2ES | 83 | 2 Esdras (Latin) |
| MAN | 84 | Prayer of Manasseh |
| PS2 | 85 | Psalm 151 |
| ODA |  | Odes |
| PSS |  | Psalms of Solomon |
| JSA |  | Joshua A. |
| JDB |  | Joshua B. |
| TBS |  | Tobit S. |
| SST |  | Susanna Th. |
| DNT |  | Daniel Th. |
| BLT |  | Bel Th. |
| 3ES |  | 3 Ezra |
| EZA |  | Apocalypse of Ezra |
| 5EZ |  | 5 Ezra |
| 6EZ |  | 6 Ezra |
| DAG | B2 | Daniel (in Greek) |
| PS3 |  | Psalms 152-155 |
| 2BA |  | 2 Baruch (Apocalypse) |
| LBA |  | Letter of Baruch |
| JUB |  | Jubilees |
| ENO |  | Enoch |
| 1MQ |  | 1 Meqabyan/Mekabis |
| 2MQ |  | 2 Meqabyan/Mekabis |
| 3MQ |  | 3 Meqabyan/Mekabis |
| REP |  | Reproof (Proverbs 25-31) |
| 4BA |  | 4 Baruch (Rest of Baruch) |
| LAO | C3 | Letter to the Laodiceans |
| FRT | A0 | Front Matter |
| GLO | A9 | Glossary / Wordlist |
| CNC | A8 | Concordance |
| XXA | 94 | Extra Material |
| XXB | 95 | Extra Material |
| XXC | 96 | Extra Material |
| XXD | 97 | Extra Material |
| XXE | 98 | Extra Material |
| XXF | 99 | Extra Material |
| XXG | 100 | Extra Material |
| XXM | 101 | Extra Material (maps, not in PT) |
| XXS | 102 | Extra Material (not in PT) |
| BAK | A1 | Back Matter |
| OTH | A2 | Other Matter |
| INT | A7 | Introductory Peripherals |
| TDX | B0 | Topical Index |
| NDX | B1 | Names Index |

[^2]:  Current Paratext 9 Index code

# Appendix 2\. RegexBNF Grammar

EBNF (Extended Backus Naur Form) is the most commonly used grammar for describing other grammars. But it is hard to read and so we use a regular expression based grammar commonly referred to as RegexBNF for the grammar in this document. We formally specify this grammar in  EBNF:

```py
letter       = "a" | "b" | ... | "z" | "A" | ... | "Z" ;
digit        = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
hex_digit    = digit | "A" | "B" | "C" | "D" | "E" | "F" | "a" | "b" | "c"
                     | "d" | "e" | "f" ;
char       	= letter | digit | unicode_escape ;
unicode_escape = "\u" hex_digit hex_digit hex_digit hex_digit ;
string     	= '"' { char } '"' ;
identifier 	= letter { letter | digit | "_" } ;

expression   = term { opt_ws "|" opt_ws term } ;
term         = factor { opt_ws factor } ;
factor       = base [ quantifier ] ;

base    	= identifier
        	| string
        	| "[" char_class "]"
        	| "(" opt_ws expression opt_ws ")" ;

quantifier   = "*" | "+" | "?" | fixed ;
fixed        = "{" digit [ "," digit ] "}" ;

ws           = " " | "\t" | "\n" ;
opt_ws       = [ ws ] ;   	(* optional whitespace *)

char_class   = char_range { char_range } ;
char_range   = rchar "-" rchar | rchar ;
rchar        = char | property ;
property     = "\p{" identifier "}" ;

rule         = identifier opt_ws "=" opt_ws expression ;
grammar      = { rule } ;
```

The Scripture Reference grammar is expressed in EBNF as:

```py
Reflist = RefRange { ws* , refsep , ws* , RefRange } ;
refsep = ";" | "," ;
RefRange = Reference , [ ws* , "-" , ws* , Reference ] ;
Reference = FullRef | ContextRef | NameRef ;

---

NameRef = BookId , ws+ , Namespace , chaptersep , Nameval , [ Wordref ] ;
Namespace = letter+ ;
Nameval = NameInit , NameChar* ;
NameChar = <<A Unicode character that is a letter, a number letter,
    an "other" ID start character, a mark, a nonspacing mark,
    a decimal digit, a connector punctuation, or an "other" ID continue
    character, but not a pattern syntax or pattern whitespace character>> ;
NameInit = <<A Unicode character that is a letter, a number letter,
    or an "other" ID start character, but not a pattern syntax or pattern
    whitespace character>> ;

---

FullRef = BookId , [ ws+ , Chapter , [ chaptersep , Verse ] , [ Wordref ] ] ;
ContextRef = Chapter , [ chaptersep , Verse ] , [ Wordref ]
       	| Verse , [ Wordref ]
       	| WordrefOnly , { Mrkref }
       	| Charref , { Mrkref } ;

---

BookId = [ TransId , booksep ] , BookCode ;
booksep = ":" | "." ;
BookCode = capital , (capital | digit){2}
     	| digit , (capital{2} | digit , capital | capital , digit) ;
TransId = Langtag , [ "+" , Transcode , [ "+" , Productid ] ] ;
Langtag = Lang , [ "-" , Script ] , [ "-" , Region ] , [ "-" , Variant ]*
    	, [ "-" , Ns , { "-" , Extval }+ ]* ;
Lang = letter{2,3} , [ "-" , Extlang ] ;
Extlang = letter{3} ;
Script = letter{4} ;
Region = letter{2} ;
Variant = letter{5,8} ;
Ns = letter ;
Extval = letter{5,8} ;
Transcode = id ;
Productid = id ;

---

chaptersep = ":" | "." ;
Chapter = digits ;
Verse = digits , [ Subverse ] | Subverse | "end" ;
Subverse = letter ;
wordrefSep = "!" ;
WordrefOnly = (digits | "end") , [ charrefSep , Charref ] ;
Wordref = (wordrefSep , WordrefOnly | Mrkref) , { Mrkref } ;
charrefSep = "+" ;
Charref = (digits | "end") , [ "+" ] ;
Mrkref = "!" , id , [ "[" , digits , "]" ] , [ wordrefSep , WordrefOnly ] ;

---

id = idinit , idmid* , [ idfinal ] ;
idinit = letter | "_" ;
idmid = letter | digit | "_" ;
idfinal = letter | digit ;
digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
digits = digit+ ;
ws = " " | <<A Unicode character from the given ranges>> ;
letter = "a" | "b" | ... | "z" ;
capital = "A" | "B" | ... | "Z" ;
```

# Changes

## 1.0

- Initial release Feb 2026

