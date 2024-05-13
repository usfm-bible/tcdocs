---
title: Bible Module Specification
author: J. Wickberg (draft)
status: open
code: 24001
issue: 
---

# Bible Module Specification

J\. Wickberg

## Executive Summary

This proposal specifies the grammar of a Bible Module extraction script. The extraction script is used
to specify which portions of books should be extracted into an output file for further processing.

The grammar
is starting with the grammar for scripts that Paratext uses to support Bible Modules.

## Introduction


## Proposal

### Specify versification of script references

A script that is going to be used by more than one project should use the `\vrs` command to specify the versification of the verse references used in the script so that the references can be translated into the versification of projects using the script

`\vrs` _versificationName_

For example:

```
\vrs English
```

### Select content to be included in output

The `\inc` command allows the script to specify  markers (and their content) which are excluded from the output by default to be included in the output:

| Option | Description |
| --- | --- |
| fig | figures |
| v | verse numbers |
| f | footnotes |
| x | cross references |
| s | section headings |

Example:
```
\inc v f x
```
This will cause verse numbers, footnotes and cross references to be included in the output. Section headings and figures will still be excluded.

### Select verse range to be extracted
The `\ref` command is used to copy the text of a verse, a verse range, or an entire chapter from a project. Paragraph markers will be included in output.

The reference format is limited: it allows hyphen and comma (without a following space) but does not allow semicolon.

`\ref`_reference range_

Example of selected verses from chapter:

```
\ref PSA 72:1-7,18-19
```
Example for an entire chapter: 
```
\ref PSA 12 
 ```
 
### Select verse range to be extracted without paragraph markers
The `\refnp` command is used to copy the verse range with no paragraph markers from the project. The same reference range format is supported as that of the `\ref` command.

`\refnp`_reference range_

Example: 
```
\refnp LUK 1:1-4 
```
### Replace text in most recent extracted range
The `\rep` command can be used to find text in the most recently extracted range and replace it with other text in the output.

To separate the text to find from the text to replace, type `=>` (an equal sign and a greater than sign).

If you need to prevent a replacement from occurring more than once, include enough surrounding context so that the text to find is unique.

Example: 
```
\rep he=>Jesus 
```
### Include other Bible module file

The `\mod` command is used to include the content of one module in the content of another module. The module which contains the other is sometimes called a "parent" module, and the module included is sometimes called a "child" module.

Example: 
```
\mod child_module.sfm
```

### Handling of other content in script file
The specification can also contain any of the following:

* Lines which begin with markers from the project stylesheet (for example, \s (headings), \p (paragraphs), and \rem (comments)) with text which will be copied to the content.

* References embedded in output text converted according to reference settings

  The output text may contain strings in form `$(BBB C:V)` for references to be formatted according to reference settings.  The BBB is the three-character book abbreviation, C is the chapter number and V is the verse number.

   A formatted reference can occur anywhere in the specification after the \id line. For example, in \sr section range references. This reference format does not have the limitations of the \ref format.

   The reference:
  * must be surrounded by parentheses,
  * must use the standard three-character book abbreviation.
  * must use the default punctuation for references (a colon to separate the chapter number and verse number, and a hyphen to separate verse numbers).

  When the reference is copied to the Bible module:
   * the standard three-character book abbreviation is replaced by the choice for cross references on the Book Names tab of the Scripture Reference Settings dialog.
   * The default punctuation is replaced by the punctuation specified on the Reference Format tab of the Scripture Reference Settings dialog.
 
   For example, in a project where:
   * the cross reference choice is to use the book abbreviation
   * the book abbreviation for the book of Revelation is Ap,
   *  the chapter verses separator is a period
   *  the range of verses separator is a hyphen
   
   $(REV 1:1-16) becomes Ap 1.1-16 in the content of the module.
 
   To override this default behavior, use any of the following:
  * $a(BBB C:V) to use the book Abbreviation
  * $s(BBB C:V) to use the book Short Name
  * $l(BBB C:V) to use the book Long Name
            
            
## Examples


## Discussion


