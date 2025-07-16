# Generalised Attributes

Reorganised ready for final standardisation. Add to USFM 3.2.

## Specification

Both USX and USJ have a mechanism for the addition of arbitrary attributes to any node. USFM, on the other hand, has only very limited support for attributes. Typically support for what are attributes in USX, end up being added piecemeal to USFM. Examples include \\cat, \\cp, \\va, etc. What is needed is a generalised mechanism that minimises the cost and maximises the benefit.

Character styles (\<char\>) and milestones (\<ms\>) already have a generalised mechanism through the | attributes separator. This mechanism is sufficient for those limited cases, but even then not without problems. In XML and JSON, the attributes occur at the head of the node. Since the attribute can affect the processing of the content, it helps for stream processing situations for the attributes to be before the content.

The extension to the USFM syntax is to allow any node/marker to have attributes up front. Currently they are assumed to be 'at the back' as in a \\w. During v3 of the standard this current behaviour for \<char\> elements remain. But we also allow them at the front and also in the elements: \<para\>, \<verse\>, \<chapter\>, \<note\>, \<cell\>, \<figure\>, \<link\>, \<periph\>, \<ref\>, \<row\>, \<sidebar\>. (\<table\>, \<list\> are represented in USFM by milestones.) 

The syntax is similar to that of attribute lists but with a separator between the list and the node contents. The grammar is:

```
<marker> ::= "\\" <HS>* <marker_name> (<attribute_list>
| <default_attribute>)? content <marker_end>  
<marker_name> ::= <letter>+ <digit>*
<attribute_list> ::= "|" <attribute> (" " <attribute>)* "|" <HS>*
<default_attribute> ::= "|" <ATTRIBTEXT> "|" <HS>*
<attribute> ::= <ATTRIBNAME> "=" '"' <ATTRIBTEXT> '"'
```

Undefined components of the grammar are capitalised and reflect those in the main USFM grammar. The \<marker\_end\> component is dependent on how a node is closed. For \<char\> elements, it is explicit but for \<para\> elements it is implicit.

For example:

```
\p|cat="emphasised"| \v|script="Arab"| 1 And the \nd Lord\nd* said ...
```

This shows two examples of adding attributes to a node.

* \\p takes a category. This is the same as extending to allow \\p \\cat emphasised\\cat\* but in a more generic way.  
* \\v This contrived example allows the addition of an undefined script attribute to a verse (for example to indicate in which script the verse number should be rendered).

Here is another example in which the first 3 USFM fragments result in the same USX

```
\f |aid="mynote"| + \cat person\cat*\fr 1:3 \ft Got some text at last\f*
\f |mynote| + \cat person\cat*\fr 1:3 \ft Got some text at last\f*
\f |aid="mynote" cat="person"| + \fr 1:3 \ft Got some text at last\f*
<note style="f" cat="person" aid="mynote">
  <char style="fr">1:3</char>
  <char style="ft">Got some text at last</char>
</node>
```

Of the three, the third presents most naturally.

For backward compatibility we allow \<char\> elements to also have attribute lists at the end as well as the beginning. This is slightly ridiculous and no generator is expected to generate such USFM. If there is any conflict over the value of an attribute so defined twice, the later definition wins. All the USFM examples in the following convert to the same USX. And yes the last one, while legal in USFM 3, is ridiculous and should never occur.

```
\w Jésus|Jesus\w*
\w Jésus|lemma="Jesus"\w*
\w |lemma="Jesus"|Jésus\w*
\w |Jesus|Jésus\w*
\w |Fred|Jésus|Jesus\w*
<char style="w" lemma="Jesus">Jésus</char>
```

The requirement for the attribute list to be delimited by a final | character is required even if the content of the node is empty. Thus `\w|Jesus|\w*` is valid while `\w|Jesus\w*` is not due to the ambiguity with the previous interpretation in 3.1.

The use of attribute lists at the end of a node is deprecated as of the version of the standard that incorporates this proposal (3.2) and will be removed at the next major release (4).

## Original Proposal & Discussion

The remainder of this document consists a summary of the original proposal and the discussion that lead to the specification above.

### The a Milestone

The proposal is for a new milestone called \\`a`. The milestone may take a single attribute or multiple attributes as per any other milestone. It is not paired and must occur before any content of the parent element it occurs in. For example:

```
\tc1 \a|lang="en"\* maps

\ip \a|authorship\* The book of John was written...
```

The default attribute of \\a is that of the *anchor id:* aid[^1] Thus the second example could be written `\ip \a|aid="authorship"\* The book of John was written…`  
Notice that any space around the milestone is ignored. This makes for easier reading. It is valid because the milestone occurs before any content within the element and element initial whitespace is disregarded for processing.

The `a` milestone interacts with other ways of representing attributes naturally. Thus the following all have the same underlying content model:

```
\f + \a|mynote\*\cat person\cat*\fr 1:3 \ft Got some text at last\f*
\f + \a|aid="mynote" cat="person"\*\fr 1:3 \ft Got some text at last\f*
\f + \cat person\cat*\a|mynote\*\fr 1:3\ft Got some text at last\f*
<note style="f" cat="person" aid="mynote">
  <char style="fr">1:3</char>
  <char style="ft">Got some text at last</char>
</node>
```

Likewise it is possible to make a character element quite ugly with these equivalents:

```
\w Jésus|Jesus\w*
\w \a|lemma="Jesus"\*Jésus\w*
<char style="w" lemma="Jesus">Jésus</char>
```

Although this equivalence may well help a typesetting system that wants its attributes up front.

### Delimiters

Various alternative delimiters were discussed:

- \\ As in `\p |aid="hello"\ text`
- { }

The conclusion was that \| is best because:

- It resolves the ambiguity of an empty char style whether the attributes are at the front or back
- It adds no new lexical items
- Has minimal ambiguity
