---
title: Biblical References
author: M. Hosken
status: open
code: 23003
issue: 
---

# Biblical References

M. Hosken

## Executive Summary

This document introduces a scheme for biblical references down to the character level. Thus it supports ranges of references from traditional verse references through word references to character references. In addition it allows referencing other scripture books withing a reference as well. A fully specified character reference might look like:
```
wsg-t-en.MAT 1:1!5+6
```
Although this is overkill for nearly all situations.

## Introduction
The purpose of this document is to propose a normative basic standard for scripture references. Notice it is not concerned with Localised references, even for English. There already exists an informal specification for scripture references which resolves within a particular translation down to the verse level. But there are desires to extend this reference in two directions.
- To be able to referencetext in other translations
- To be able to reference a word or even part of a word within a verse.

This proposal will examine both of these extensions and propose a grammar for a scripture reference list that includes scripture reference ranges.

## Basic Reference
The current basic reference consists of a book id, a chapter number and a verse number, which may have an informal Verse subsection reference (e.g. a).
```
Reflist = RefRange (ws* Refsep ws* RefRange)*
RefRange = Reference (ws* "-" ws* Reference)?
Reference = Fullref | ContextRef
FullRef = BookId ws* Chapter (chaptersep Verse)?
ContextRef = Chapter (chaptersep Verse)? | Verse
BookId = [0-9A-Z]{3}
Refsep = ';' | ','
chaptersep = ws* (":" | ".") ws* 
Chapter = digits
Verse = digits (subverse)? | "end"
subverse = "a" | "b" | "c" | "d" | "e" | "f"
digits = ("0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9")+
ws = " " | [\p{Zs}\u2OOB-\u200F\u202A-\u202E]
```
A reference list is a list of verse ranges. A verse range may consist of a single reference or a first and last reference. Notice that verse ranges are inclusive of both the first and last verses. One of the difficulties of verse ranges is that if you want to finish at the end of a chapter, you have to know how many verses are in that chapter. To alleviate that need, we allow the keyword `end`.
Further, it is not uncommon for people to want to reference a whole chapter.  For example JHN 3 refer to the whole of John chapter 3. In effect it is equivalent to JHN 3:1-end.
The definition of `BookId` is informal. A more formal definition would be an enumeration of every book code, including apocryphal books.

### Contextual References
This grammar is more complicated than might first be expected due to the desire to support contextual references. Contextual References are references that only make sense in the context of another reference. For example consider the reference range GEN 1-11. The range consists of two references. The first reference is Genesis chapter 1. The second is ambiguous. Is it verse 11 or chapter 11, and which book are we talking about? The book is obvious: Genesis, because that is what is in scope. But the 11 being a chapter or verse, while perhaps obvious to a human reader is less obvious to a computer. If the range were: GEN 1:1-11, then we would say the 11 is a verse reference, since if we wanted a chapter reference we might use GEN 1:1-11:32 (since GEN 11 has 32 verses). Or to disambiguate the verse reference, we might use GEN 1:1-1:11.
But our use of GEN 1-11 places the first reference as a chapter reference rather than a verse reference. Thus the second reference is interpretted in the context of a chapter reference rather than a verse reference and the ambiguity is resolved in favour of a chapter. Thus the fully disambiguated reference to the verse level would be GEN 1:1-11:end.

### Single Chapter Books
The book of Jude has only one chapter. What therefore does JUD 1-4 mean? It could mean Jude chapters 1-4. But that is not valid. Instead interpretting the range as JUD 1:1-1:4 makes better sense. This is a semantic rule and cannot be covered by the grammar.

## External References
There are two core questions to resolve when extending references to be able to reference a different translation.
- How to reference a bible translation
- How to integrate such a reference into a verse reference

### Translation Reference
This work builds on discussions held on how to reference not only a translation but a scripture product. In summary, a scripture product reference is a sequence of components separated by `+`. The complete string of components may be truncated at the point where no other information is needed to disambiguate the product / translation. The components are:

#### Language Tag
The language tag component consists of a BCP47 language tag. The only difference is that the language tag is expressed entirely in lowercase. Notice that the components of a language tag are separated by `-`.

#### Translation Id
There are a number of translations even within a language group. This is even discounting the 200 English translations. Consider, for example the New International Version (NIV). The code for this translation could well be NIV. But there are many versions of the NIV. There can be further identified, separated by a hyphen `-` as in a language tag. Thus niv-1976

#### Product id
When it comes to a verse reference, the product id is unlikely to be needed. The product id may be used to identify different scripture products associated with the translation. Examples of products would be various study editions.

### Within a Verse Reference
Given the various separation for components in a reference, we need to find something suitable. The good news is that this separator is used to extend the bookld. We can, therefore use the same separators as used between a chapter and a verse. Thus we propose using the same separator.

### Conclusion
Bringing all this together a reference to a different translation might look like:
```
en-gb+niv+study.JHN 3:16
```
The first component is the language tag (which has two parts: language and region) and identifies the Anglicised NIV translation over the US English version. Then comes the translation id. Then within the translation there is the particular product, the NIV study bible. These are separated from the book code, which in turn is separated from the chapter:verse by a space.

Integrating this definition into our grammar, we get:
```
BookId = (TransId (":" | "."))? BookCode
BookCode = [O-9A-Z]{3}
TransId = langtag ("+" transcode ("+" productid)?)?
langtag = lang ("-" script)? ("-" region)? ("-" variant)* ("-" ns ("-" extval)+)*
lang = [a-z]{2,3} ("-" extlang)?
extlang = [a-z]{3}
script = [a-z]{4}
region = [a-z]{2}
variant = [a-z]{5,8}
ns = [a-z]
extval = [a-z]{5:8}
transcode = [0-9a-z]{1,8}
productid = [0-9a-z]{1,8}
```
A full BCP47 language tag is more complex than presented here. This grammer only accounts for the common language tags that are in use today. See BCP47 for the full format definition. The 8 character limit on a translation code is arbitrary at this point.

## Word And Character References
At the other end of the scale is the desire to reference words or even characters within a verse. Extending the range model where we say that a chapter is a range of verses, we can say that a verse is a range of words and a word is a range of characters.
There are various issues to address with this model:
- What constitutes a word? Most languages have a clear word break (a space), but some do not. Care needs to be taken in specifying a word break model.
- Scripture can contain both primary scripture text and also out of band associated text, like footnotes or other items.
- At the character level there is the question of what constitutes a character? Is text, in Unicode terms, interpretted as NFD or NFC? Is punctuation considered part of a 'word'?
- How are word and character references included in a reference unambiguously?

### Word segmentation
Accurate word segmentation is a difficult problem, particularly for
non-wordspaced languages. Such languages do not have spaces between words,
instead they use spaces as discourse or grammatical markers. Thankfully there
are some factors in our favour.
Scriptural texts are highly controlled. By this we mean that such texts are carefully edited and characters that would otherwise be missing from normal documents in a language, can and are inserted in scripture text. A primary example of this is the zero width space. This invisible character acts like a space for word segmentation and Iinebreaking, but otherwise is not seen. Therefore we can assume that any necessary character for word segmentation can be inserted.
Accurate word segmentation is not required. The reason for character locations to be identified by word is that it makes indexing by humans easier. Humans are not expected to come up with character level references, but it helps if a human can read and approximately locate the position in a text a reference is pointing to. Thus it is sufficient for a 'word' in this context, to be defined as a sequence of non-space characters whether those characters are strictly word forming or not. This also mitigates any arguments over what is truly a word or not in a particular language.
While the USFM standard considers any space characters other than those in ASCII
(i.e. space, tab, carriage return, newline) to be content characters that must
not be changed, they are not considered word forming in any way. They are also
often effectively invisible in that it is not possible to count how many space
charcaters are in a sequence. Punctuation characters are also non word forming,
but are visible and countable. Therefore we include them as being referenceable.
Also this mitigates the question of when a punctuation character gets used as a
word forming character. A marker is treated as a space. Multiple spaces are
treated as a single space. The precise set of space characters is yet to be
decided but will probably be closely aligned to \\p{Zs} (Unicode character of
general category Zs which includes all the various space characters. We extend
the list to include U+200B.)

### Including And Ignoring Notes
At the simplest level, footnote (or any other note) text is not part of the main scripture text. They may or may not be printed, if word counting through a text, it is very awkward to have to include notes into the count. There are many other reason why it is easier to ignore notes when word counting through the text. And so we ignore them for primary referencing.
But there are also good reasons for people to want to reference text within notes. For example, when interlinearising some people want to interlinearise their footnote text. Interlinearising is a primary out-of-band text linkage use case for which word level and even character level referencing is necessary. For this reason, we provide a mechanism for referencing notes and the words and characters within them. In effect one specifies the note number in a verse and then uses the proposed word and character referencing below that. The detailed syntax is described below.
_Discuss other USFM markers including \s and \r_ 

### Normalization
The normalization encoding model question is relatively easy. We just have to pick one. The relative strengths and weaknesses of NFC vs NFD are:

#### NFC
This is the most common way that data is stored. Given NFC and NFD are canonically equivalent, there is no content difference between the two normal forms.

#### NFD
The problem with NFC is that some characters, for example: é, which is one code in NFC, but two in NFD may need to have its diacritic individually referenced, and for this we need to use NFD.

#### Conclusion
Given the need to be able to reference components in precomposed characters, referencing needs to index characters based on NFD encoding. There may be better arguments why this decision should be reversed.

### Syntax

#### Separators
Word and character components of a reference fit most naturally after the verse number. We cannot use the existing chapter separator after a verse number because that would cause all kinds of confusion at whether 1:2 means chapter 1 verse 2 or verse 1 word 2. It is better to use a different separator. We propose ! and +.
For example GEN 2:3!4+5 is Genesis charter 2 verse 3 word 4 character 5. It might be tempting to use charter separators after a ! but this can cause confusion when dealing with the component hierarchy.

#### Component Hierarchy
A second concern is in interpreting the second reference in a range. For example what should 1!2-3 mean? Does it mean verse 1 word 2 to verse 3? Or does it mean verse 1 word 2 to word 3? The most intuitive interpretation is the Iatter. But why?
In reading and interpretting a reference, we typically think from the large to the small:
```
                                        note -- word -- char
                                       / n    !       +
translation -- Book -- Chapter -- Verse -- word -- char
            :.                 :.        !       +
```
when interpretting a reference in the context of another reference, we start from the position in the hierarchy of the other reference. A pure number therefore is at the same level in the hierarchy. for example in GEN 2:3!4+5-7, the 7 is interpretted as a character. On the other hand GEN 2:3!4-7!8, the 7 is a word index and 8 the character. But why is this not verse 7 word 8? This is an ambiguity. To resolve it, we need to use a different separator. The basic principle is that a separator followed by a sequence (in this case digits) must be unique, but the separator defines the type of the following component. In this case of the character index, we can reuse `+` from the translation.

| Range           | Description                               |
| --------------- | ----------------------------------------- |
| GEN 7:8!2-6       | Genesis ch 7 vs 8 words 2-6  |
| GEN 7:8!2-12!3  | Genesis ch 7 vs 8 word 2 to vs 12 word 3 |
| wsg-gong.JHN 3:16 | John 3:16 from the Gondi translation and script |
| wsg-t-en.JHN 3:16 | John 3:16 from the Gondi back translation into English |
| REV 3.20!n1!4+3-5 | Revelation 3:20, 1st note (including cross references), 4th word characters 3-5 |
| wsg-t-en.MAT 1:1!5+6 | All that for a single letter! |


#### Grammar Extensions
```
Verse = VerseNum ("!" WordRef)? 
VerseNum = digits (subverse)? | "end"
WordRef = (Noteref "!")? digits ("+" Charref)?
Noteref = "n" digits
Charref = digits
ContextRef = Chapter (chaptersep Verse)? | Verse | WordRef | Charref
```
This grammar is technically ambiguous. For example a reference that consists only of a sequence of digits may be a chapter or a verse or a wordref or a charref. It is only in the context of another reference that the ambiguity may be resolved.

## Conclusion

The final full grammar is therefore:

```
Reflist = RefRange (ws* Refsep ws* RefRange)*
RefRange = Reference (ws* "-" ws* Reference)?
Reference = Fullref | ContextRef
FullRef = BookId ws* Chapter (chaptersep Verse)?
ContextRef = Chapter (chaptersep Verse)? | Verse
BookId = (TransId (":" | "."))? BookCode
BookCode = [O-9A-Z]{3}
TransId = langtag ("+" transcode ("+" productid)?)?
Refsep = ';' | ','
chaptersep = ws* (":" | ".") ws* 
Chapter = digits
Verse = VerseNum ("!" WordRef)? 
VerseNum = digits (subverse)? | "end"
WordRef = (Noteref "!")? digits ("+" Charref)?
Noteref = "n" ("[" digits "]")?
Charref = digits
ContextRef = Chapter (chaptersep Verse)? | Verse | WordRef | Charref
subverse = "a" | "b" | "c" | "d" | "e" | "f"
digits = ("0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9")+
ws = " " | [\p{Zs}\u2OOB-\u200F\u202A-\u202E]
langtag = lang ("-" script)? ("-" region)? ("-" variant)* ("-" ns ("-" extval)+)*
lang = [a-z]{2,3} ("-" extlang)?
extlang = [a-z]{3}
script = [a-z]{4}
region = [a-z]{2}
variant = [a-z]{5,8}
ns = [a-z]
extval = [a-z]{5:8}
transcode = [0-9a-z]{1,8}
productid = [0-9a-z]{1,8}
```

# Outstanding Issues

## Zero width assertions

This referencing scheme allows reference down to a single character. But it
doesn't allow reference to the zero width point between characters. There are
situations where information wants to be associated with a point between two
characters. How can we mark this position? Perhaps with a trailing +?
Indexing is 1 based. So we can say: the zerowith position after the char. Thus
to insert at the start of the bible, one might say `GEN 1:1!1+0+`.

## Referencing into non-verse text

How do we reference into a footnote or a section heading?
We will call such text, out-of-band text. Consider a footnote. This is anchored
at a particular character in the text and so may either be counted over a range
(for example a verse or word). Thus we might say: `GEN 1:1!f` would be the first
footnote in GEN 1:1. For the second we would say `GEN 1:1!f[2]`.
Or if we wanted the footnote after the
3rd word, we might say: `GEN 1:1!3!f` and then for the 4th word in that
footnote we would say `GEN 1:1!3!f!4`. Notes associate backwards and so are
considered part of the character they follow.

What if a note is surrounded by spaces? Is it counted as a word? No it still is
associated with the last character of the previous word. What about notes at the
start of a verse or some other marker anchor? Here they are associated with that
anchor and cannot be referenced in relation to a word (unless the word index is
0).

For subheadings. The key is to notice that subheadings associate forwards. Thus
the subheading before verse 1 is associated with v1. Thus `GEN 1:1!s!f` is the
first footnote in the first subheading before GEN 1:1. Subheadings are counted
forward, thus s[1] comes before s[2].

We can think of using a word reference marker `!` as a way of referring to the
whole of the marked text, but also to its first word. It is a word range (more
akin to a verse, really, but using `:` would cause problems with book ids.)
Since markers never start with a digit and words always do, the two categories
are disambiguated.

### Referencing Marker Arguments

Here we discuss referencing verse numbers and footnote markers, etc.

Again we can use the 0th word for these.

For a subheading before the start of a chapter, that subheading is associated
both with the chapter number itself `GEN 1:0!s` and also with the first verse
`GEN 1:1!s`. In each case also with the zeroth word of each: `GEN 1:0!0+0!s` and
`GEN 1:1!0+0!s`.

### Referencing Introductory Material

What about `\h` or `\ip` material?


