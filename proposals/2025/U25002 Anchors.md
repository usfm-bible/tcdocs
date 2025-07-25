# Anchors and Inline Referencing

Approved for addition USFM 3.2 due to them being applied to paragraphs.

## Introduction

Aligning data between a scripture file and another data source is a difficult problem to solve. On one level it is far better to keep such data outside of the scripture file and to link it to the appropriate place in the scripture file using some kind of referencing scheme, such as described in U23003. But some locations, particularly to text outside of the standard C:V structure can be hard to reference. Are there ways in which we can introduce extra reference points into a scripture file without cluttering the file and making text processing of the file nigh on impossible?

This document proposes extensions to the existing C:V based scheme that allow referencing particularly to non scripture text within a scripture file, which can be hard to reference. The basis of such a scheme is to express an extended reference using a *namespace*:*identifier* scheme. Thus in parsing a reference, if the chapter component is non-numeric, it is treated as a namespace id and the verse component, following the : or . is an identifier interpreted by that namespace. The precise syntax of such a reference is specified in U23003.

The following namespaces are proposed:

| Namespace | Identifier |
| :---- | :---- |
| a | @aid identifier |
| k | Glossary entry |
| t | Tables also specified by @aid but only in a table element. Allows row.column sub referencing |

## The aid Attribute

To reference, typically non-scripture, elements, we introduce an `aid` attribute to the following elements: figure, para, sidebar, table, note. These are clearly identifiable units of text and content that have a clear boundary and so are most appropriate for being referenced by a name or id. The aid attribute value must be unique within a book.  
For example:

```
<par style="ip" aid="authorship">The book of John is recognised as having an author called John...</par>
<figure src="cn12345.jpg" ref="MRK 9:6" aid="picstorm">Jesus calms the storm</figure>

\ip|aid="authorship"| The book of John is recognised as having an author called John...
\fig Jesus calms the storm|src="cn12345.jpg" ref="MRK 9:16" aid="picstorm"\fig*
```

Notice that in the USFM, no new marker has been added. Instead the extended attribute syntax, new to 3.2, is used. This makes sense since  @aid is also a 3.2 addition.  
Within a scripture reference, this id is referenced using the `a` namespace as in: `JHN a.authorship` or `JHN a:picstorm`. Notice that, as per U23003, there is no difference whether `:` or `.` is used as the separator between the namespace and the identifier.

### Keywords

A glossary consists of a number of paragraphs with no C:V structure. But a paragraph is typically identifiable by the \\k element it contains. Rather than having to explicitly give an aid for each paragraph, it would be much more convenient if the systems involved would synthesize an anchor based on the \\k element. A \\k element may have a @key attribute, and if this exists, it is used. Notice where a paragraph has more than one \\k definition in it, it may have more than one implicit anchor that may be used. Also, if the same key occurs more than once in a document, the first is referred to. For example:

```
\p Phrase \k Light of the World|LotW\k*. Jesus calls himself the Light of the World as a title designed to emphasize his drawing people to himself and for them to understand the world through him.

GLO k.LotW
```

Notice that the reference is not to the keyword itself, but to its containing paragraph.

A keyword can contain any text, but not all text is suitable for use within an identifier. The identifier is constrained to conform to a Unicode ID pattern, in that they start with an ID\_Start: \[\\p{L}\\p{Nl}\\p{Other\_ID\_Start}-\\p{Pattern\_Syntax}-\\p{Pattern\_White\_Space}\], and then consiste of ID\_Continue characters: \[\\p{ID\_Start}\\p{Mn}\\p{Mc}\\p{Nd}\\p{Pc}\\p{Other\_ID\_Continue}-\\p{Pattern\_Syntax}-\\p{Pattern\_White\_Space}\]  
This limited character set also applies to the @key attribute of the \\k element.  
Any characters that may not be included in the identifier are simply removed from the keyword string to create the identifier

### Tables

We allow anchoring of cells in a table. But equally, cells are readily identifiable via row.col. Thus we would support

```
NUM t.mytable_5_2
```

The `t` namespace refers to a cell in a table. The identifier has 3 components, separated by `_`. The first is an identifier as specified in the table@aid attribute. Its character set is further limited to not include `_` in the attribute value. The second component is a number that specifies the row and the last component is a number specifying the column in that row. `_` is used because it is not considered a pattern syntax character. Pattern syntax characters are not allowed in identifiers within U23003.

