# Anchors and Inline Referencing

Approved for addition USFM 3.2.

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

## Issues

Material after this point is discussion that resulted in the description above and may refer to ideas that are not described.

#### Attribute name

The attribute name of `aid` is proposed. Is this most suitable? A shorter name of `a` may be more convenient but it clashes with the `\a` marker which can be confusing for users. But the `\a` marker is no longer being proposed. Thus `a` is open.

#### Tables

In order to support cell referencing, do we need to reduce the reference back to a single separator and use something like `mytable3:5`. This would completely break any namespacing. So we either find a different way or we allow multiple separators: `t:mytable/3/5`  
The problem here is that this would require an extension to the U23003 grammar, which makes this a special case. One way forward might be to use `t:mytable!r3!c5!2` for the second word in the cell. The reason for `r` and `c` is to fit the row and column into a U23003 grammatical structure using ids.

#### Identifiable Elements

The elements not currently eligible for receiving an @aid are: book, cell, chapter, char, link, ms, optbreak, periph, ref, row, usx, verse and allowed in: figure, note, para, sidebar, table.

Note we explicitly do not allow the attribute on milestones because the likelihood of its abuse is so huge.

Do we want to extend this facility to things like \<char\>?

#### Namespace Structure

Should we explicitly limit namespaces to digits and a single lowercase letter. The reason for lowercase letters is that for some texts there is a desire for chapters to take letters instead of digits as in A:3. There is not likely to be a long list of namespaces. By using a single namespace letter we are making the reference structure clearer.  
Namespaces could potentially stack. Thus if there is a table with a \\k in it then one might say `t:k:well:3:5`. Life can start to get confusing. There is no need for this capability yet.

## Discussion

Please enter any comments in this discussion area rather than adding comments to this doc. The conclusion of any discussion will be then transferred into the main document above this heading. The advantage of this approach is that the discussion can be kept as part of the history of the document once it is placed in the tcdocs repository. Please also keep styling to that which conforms to markdown export.

DJG: There seems to be inconsistency between `k:ark` and `k.ark` Is this accidental or is the implication that they should be treated as equal? (and hence there be code to make sure that they are). I think this should be probably be clarified.  
	As per U23003 there should be no semantic difference between k:ark and k.ark  
MH: You are correct. `k:ark` and `k.ark` are equivalent in every way.

DJG: The statement that a glossary has no `C:V` structure is true for the printed form, but if notes are in use in Paratext glossaries, it  archives the entire glossary state at each new / modified note. The use of `C:V` structure in the glossary is thus sometimes recommended as a work-around to stop paratext grinding to a halt. Breaking the glossary into chapters and verses also helps with change-tracking for back-translations.  Glossaries may also have ‘chapters’ for the different letters of the alphabet, and thus be printed using `\c 1 \cl A`  even if verse numbers are not in use. I offer this comment as a note of the status-quo about how USFM is in use, not to request a rewrite, but perhaps a minor re-wording, e.g.  “no significant / agreed / canonical C:V structure” would be in order.  
But this should not be relied on in referencing.

JK: Re: the attribute name 'aid': aid is fine with me. I like that the 'id' part helps to express its purpose.

JK: Re: Separators for table row and column: I think tables are an additional structure being added just above the word and character level. For that reason I think that the additional separator character makes sense (since we have the practice in 23003 of having different characters for different aspects of a reference like \!word and \+character). So NUM t:census\_first/2/1, rather than NUM t:census\_first\!r2\!c1.

JK: Re extending this to \<char\>: It would steer people away from creating user-defined attributes when they wish to be able to point to specific texts by name. However, I suppose the clear downside is the likelihood of abuse (rather than using u23003 references), right?
