---
title: Extending the Grammar
author: M. Hosken
status: open
code: 23001
issue: 
---

# Extending The Grammar

M. Hosken

## Executive Summary

This proposal adds a mechanism for USFM files to self describe user defined
markers. The result of this proposal is the addition of a new marker: `\\def'
that may only occur before any book headers.

## Introduction

USFM allows the addition of extra markers. Such user defined markers are
identified by an initial z to the marker. The difficulty is, when parsing or
generating USFM, how to treat such a user defined marker. Is it a paragraph
marker or a character marker or what?

The current mechanism for defining the structure of a USFM document is to use a
stylesheet and to use the \\OccursUnder field for a marker. This specifies what
marker a marker may occur under. There are numerous difficulties with this
mechanism. For example, if someone were to define a \\zp that behaves like \\p,
then all markers that have p in their \\OccursUnder have to be updated to
include zp.

Requiring such information, about parsing structure, to be stored in a separate
stylesheet limits the viability of a single USFM file on its own. If instead it
is possible to specify the extra information needed to parse a USFM file within
the file, then USFM files become self standing and tooling becomes much easier.
The use of user defined markers is relatively rare and so the number of times
such extensions are needed is quite low. In addition, there is nothing to stop
moving the extensions to an external file rather than repeating them for every
file in a project, if the savings are worth the increased cross file dependency
costs.

## Proposal

The proposed added marker is `\def`. Since the information following the marker
changes the parsing of the rest of the file, such markers must occur before any
content markers including book headers like `\h`. `\def` is followed by
structured text that is delimited by a newline. The structure of the content of
a \\def is:

`\def` _marker_  _category_ *space separated parameters*

For example:

```
\def z-aln charwithattrib lemma
```

The marker is the marker being defined. The category is one of a closed set of
parsing categories, for example: paragraph, character, list-paragraph. These
correspond to marker lists in the formal grammar for USFM/X. The final space
separated parameters are defined according to the category used. In the case of
a charwithattrib, the parameter is an optional default parameter for the milestone.
Thus `\z-aln aword|alemma\*` is equivalent to `\z-aln|lemma="alemma"\*`.
Notice that having a default attribute does not preclude the addition of other
attributes, although in that case, the default attribute does have to be
explicitly stated as in the second of these examples.

### Categories

The marker categories are driven by the different sets of markers in the grammar
at various points. The current list is:

| Category   | Parameters    | Description                                   |
| :--------- | :------------ | :-------------------------------------------- |
| BookHeaders |         | Book information including \\h \\toc#  |
| BookIntroduction |    | Book introductions including \\mt# \\imt# \\ip \\is \\io |
| Char        |         | Character markers including \\k \\wg \\nd \\pn \\xt   |
| CharWithAttrib | default\_attribute | Character markers with attributes including \\w \\rb  |
| CrossReferenceChar |     | CrossReference structural marker including \\xo \\xt  |
| FootnoteChar |     | Footnote structural marker including \\fr \\ft    |
| IntroChar |     | Introductory character style including \\ior \\iqt  |
| ListChar |     | List paragraph character style including \\liv \\lik \\litl  |
| List |     | List paragraph style including \\lh \\li |
| Milestone | default\_attribute    | Milestones including ts-s qt-e  |
| Para |     | Paragraph styles including \\p \\q \\m \\b \\s3 |
| Section |     | Section header styles including \\s1 \\r \\ip \\cl |

## Discussion

There are many options as to the structure and definition of this marker.

### Parameter lists

Currently the parameter list is single word, fixed position items. Options to
extend it include:

- Use quotation marks to allow spaces in a 'word'.
- Using key values: defattrib=lemma

The latter would mean the category list to no longer has to define the
parameter list structure.

### Marker name

`\def` is problematic for TeX since it is an important keyword in TeX. While
not a serious problem, it does mean TeX based systems have to be careful and
preprocess USFM files to remove the `\def`. It may be more convenient to use a
different marker.

