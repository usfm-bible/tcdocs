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

- 

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
| ~     | hard spcae \u00A0       | \u00A0 |
| //    | soft line break         | <optbreak/> |
| \\    | escaped backslash: \    | \ |
| \~    | escaped tilde ~         | ~ |
| /\/   | escaped //              | // |
| \u|1234\* | Milestone for char U+1234 | &#x1234; |

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


