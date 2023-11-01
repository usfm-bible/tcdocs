---
title: Character Model
author: M. Hosken
status: open
code: 23002
issue: 
---

# Character Model

M. Hosken

## Executive Summary

This document describes the character model for USFM and USX. While being based
on Unicode, there are some specific character model characteristics for both
USFM and USX. USX has a simpler model. The key findings are:

- \\ is used to escape certain characters that have other meanings in parsing
- \\u\|1234\\* is introduced as a Unicode character element milestone
- The whitespace handline model is described

## Introduction

Scripture files contain all kinds of interesting characters, in particular,
spaces. There are various kinds of spaces. Part of the difficulty of editing
scripture text, therefore, is ensuring that the right kind of space is in the
right place in the text. This is very hard to do given spaces are either just
whitespace or even invisible. An ideal solution would make all the different
kinds of spaces visible and identifiable. But without that capability, users
have, over the years come up with various informal representations for key
spaces, to differentiate them.

In addition, in USFM, various characters are significant, and it is necessary to
be able to escape them to reduce them to their original meaning.

This table lists special character sequences, their meaning in USFM and their
corresponding representation in USX.

| Chars | USFM meaning            | USX  |
| ----- | ----------------------- | ---- |
| ~     | hard space \u00A0       | \\u00A0 |
| //    | soft line break         | \<optbreak/\> |
| \\\\    | escaped backslash: \\    | \\ |
| \\~    | escaped tilde ~         | ~ |
| /\\/   | escaped //              | // |
| \\u\|1234\\* | Milestone for char U+1234 | &#x1234; |

## Extended Unicode

It is common to be able to insert any Unicode character by code rather than just
the character itself. In XML there are character entities: '\&#xabcd;' In USFM
there is no such mechanism. A lesser approach is proposed here.

We propose the addition of a \u milestone: \u|abcd\* which has a single default
attribute that is the hexadecimal representation of the Unicode Scalar Value to
appear in the file at that point.

This approach is different to a character entity in that the character is not
simply replaced while processing, it is treated as a full character content and
only expands to the character when such milestones are explicitly processed.
This can happen at any time after the file has been parsed. Thus it is not
possible to use such milestones to create other markers. Thus for example:

```
\u|005C\*p
```

This is not the same as the marker `\p`. But it is two content characters `\\`
following by `p`. When converting to USX, character entities may be used thus:

```
\u|1234\* -> &#x1234;
```

The problem with such a mapping is that it is very hard when parsing USX to get
character entities passed to the XML parser as character entities and not simply
the character they represent.

## Escaping Characters

As seen above, there are various characters that have direct parsing meaning and
so to be treated as content, need to be escaped. This is a list:

| Chars | Unescaped USFM meaning            
| ----- | --------------------------------- |
| \\~   | hard space \u00A0                 |
| \\\\  | backslash marks USFMs or special chars    |
| \\\|  | \| indicates the start of a list of attributes    |
| \\"   | " delimits the value of an attribute  |
| \\/   | // indicates an optional break, escaping either one breaks the sequence |

### Non Escaped Characters

There are certain characters that we propose not to escape:

```
\\\<space\>
```

Ensuring space remains as content makes the implementation of parsers much
harder. There is little to be gained. If really needed a user may use the
Unicode milestone `\u|0020\*`. But even this may be problematic depending on
where the Unicode milestone is expanded. For example, there is no expectation
that `\u005C\*p` is interpretted as the marker `\p`.

# Whitespace Handling

This section describes how whitespace is to be treated in both USFM and USX.
There are two kinds of whitespace: _structural_ or _ignorable_ and _content_ or
_significant_. _structural_ whitespace is used to delimit markers and to provide
a visual layout to the source scripture file. It does not appear in any printed
output and is ignored. _content_ whitespace is treated as part of the text and
appears in printed output.

Whitespace characters consist only of the space, U+0020, the newline
characters U+000A and U+000D, and tab U+0009. All other whitespace characters
are treated as content characters just as if they were the letter 'a'. The
concept of horizontal whitespace removes the newline characters from the list.

## Whitespace Reduction and Ignoring

A sequence of whitespace characters is reduced to a single whitespace character.
For the purposes of parsing, this is a single space. Notice that in outputting
canonical USFM, newlines may be inserted, for example before paragraph markers.

Reduction only occurs in the following places:

- Where the sequence contains a newline
- In USX at the start and end of an element's content. This reduced whitespace
  is eliminated at the start of an element's content and at the end unless the
  element is a \<char\> element. The corresponding whitespace is also treated
  identically in USFM.
- Whitespace is reduced, but not eliminated, before a verse marker (\\v)
- After the verse parameter, a delimiting space character is required. All
  following whitespace after that, is ignored.
- A single whitespace is required betweeen a marker and its parameter. The only
  markers that take parameters are: \\c, \\v, \\f, \\x, \\fe.
- Only horizontal whitespace is allowed between attributes in a list and this is
  reduced to a single space.
