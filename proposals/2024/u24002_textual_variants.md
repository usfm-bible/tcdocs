---
title: Textual Variants
author: M. Hosken
status: open
code: 24002
issue: 
---

# Textual Variants

M. Hosken

## Executive Summary

This proposal adds 5 new markers to support textual variants to USFM. A textual
variant is an alternative text based on a variant id. Four of the markers form
two milestone pairs. One pair is for a variant that matches and id (or id list)
and one pair is for a non matching variant. For example:

```
Haj so kerela jekh manuś saves si les sǎ e lumǎ haj xasarela pesqo \tv-s\*
ʒivipen\tv-e\*\tv-s|a\*gi\tv-e|a\*\tv-s|b\*ilo\tv-e|b\*\tv-s|var="c d"\*
ʒivimos\tv-e|var="c d"*?
```

But that is a lot of syntax for simple text. Even the line wrapping is
problematic. So we introduce a fifth convenience marker that puts the textual
variants into attributes:

```
Haj so kerela jekh manuś saves si les sǎ e lumǎ haj xasarela pesqo \tv
ʒivipen|a="gi" b="ilo" c="ʒivimos" d="ʒivimos"\tv*?
```

The proposed additional markers are:

```
\tv \tv-s \tv-e \tvn-s \tvn-e
```

## Introduction

There are numerous contexts in which it might be useful to be able to produce
multiple texts from a single source text. For example, Anglicisation or other
dialectal variation; different target audiences such as using catholic key terms
that differ from protestant ones. It is much more convenient in such situations
to hold the texts as a single text, since the variants are small and rare and
managing two texts just for these variations is too great an overhead.

This proposal addresses the question of how we might encode such variation in
USFM.

## Discussion

There are a number of approaches to this question. But there are a few factors
to try to keep in mind:

- The resulting USFM shouldn't be too 'ugly' since users have to directly
  interact with it.
- We don't want to nest markers if we can help it.
- The text should not be ambiguous in its interpretation.

A first cut solution would be to use a character style:

```
Haj so kerela jekh manuś saves si les sǎ e lumǎ haj xasarela pesqo \tv
ʒivipen\tv*\tv gi|a\tv*\tv ilo|b\tv*\tv ʒivimos|var="c d"\tv*?
```

This keeps each variant in its own marker and is semantically clear. The
attribute specifies which variant id the text is appropriate for, and if missing
is for the text with no textual variant. This works well at the character level,
but unfortunately does not work where different paragraphs are involved, which
does occur.

For this reason, the basic structural element needs to be a milestone. But for
many variants, the difference is merely a word difference, and so a convenience
marker is also proposed that brings all the simple textual variants into a
single character style, making it easier for users to interact with. Thus the
example immediately above is not proposed and we can use the tv marker for the
convenience character style.

In addition to a positive assertion, as in 'include this text if the variant id
is as specified' we need a negative assertion: 'include this text if the variant
id is other than specified'. We could just rely on the list of variant ids being
a closed set. But this would introduce significant instability if a user were to
add a new variant id to their list.

### Variant id

A variant id is a single identifier, identical in structure to the tag of a usfm
marker. I.e. it is simple ASCII, not starting with a digit, etc. By being a
single word, it allows a list of ids to be a simple space separated list. It
also allows the variant id to be used as an attribute name in the tv character
style.

In the case of the tv character style, if a variant id is not found in the
attribute list, the main text of the character style is used.

Notice for the milestone, the variant ids list is repeated in the closing
milestone. This is to ensure appropriate synchronisation between open and closing
mailestones.

