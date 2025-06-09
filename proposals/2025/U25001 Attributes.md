# Generalised Attributes

Reorganised ready for final standardisation

## Specification

Both USX and USJ have a mechanism for the addition of arbitrary attributes to any node. USFM, on the other hand, has only very limited support for attributes. Typically support for what are attributes in USX, end up being added piecemeal to USFM. Examples include \\cat, \\cp, \\va, etc. What is needed is a generalised mechanism that minimises the cost and maximises the benefit.

Character styles (\<char\>) and milestones (\<ms\>) already have a generalised mechanism through the | attributes separator. This mechanism is sufficient for those limited cases, but even then not without problems. In XML and JSON, the attributes occur at the head of the node. Since the attribute can affect the processing of the content, it helps for stream processing situations for the attributes to be before the content.

The extension to the USFM syntax is to allow any node/marker to have attributes up front. Currently they are assumed to be 'at the back' as in a \\w. During v3 of the standard this current behaviour for \<char\> elements remain. But we also allow them at the front and also in elements such as \<para\>, \<verse\>, \<chapter\>, etc.

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

The remainder of this document consists of the original proposal and the discussion that lead to the specification above.

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

### Issues

There are no known issues with this proposal

### Discussion

Please enter any comments in this discussion area rather than adding comments to this doc. The conclusion of any discussion will be then transferred into the main document above this heading. The advantage of this approach is that the discussion can be kept as part of the history of the document once it is placed in the tcdocs repository. Please also keep styling to that which conforms to markdown export.

DJG: I was surprised by the assertion that “element initial whitespace is disregarded for processing”, and checked it in TeX. It is indeed correct (`\par {} { } This paragraph starts at entirely the normal place`).

---

KWS:  I am concerned by the complexity of adding an additional marker to carry attribute information, particularly with how that will affect our ability to manipulate usfm data with regex and how a lot of the established Regex code base will be affected.  I would like to consider a solution that would add attributes directly to USF markers similar to the way they are added to Milestones. 

#### Adding attributes directly to markers

 This alternative proposal would allow any paragraph or opening character marker to be followed by   |\<attributes\>\\\<space\>  For example :  
\\tc1|lang="en"\\\<space\>  
\\ip|authorship\\\<space\>  
Instead of  \\w Jésus|Jesus\\w\* one could write:  
\\w|Jesus\\ Jésus\\w\*  
This proposal adds only a backslash and a space to the current lemma attribute markup.  The space after the final \\  is structural. This proposal  introduces a limitation on USFM, USX and USJ to not allow \\ or other escaped characters (e.g. \\\* \\|)  in attributes.   
It can be applied to Notes without any ambiguity.  
\\f|mynote\\ \+ \\cat person\\cat\*\\fr 1:3\\ft Got some text at last\\f\*  
Or, assuming note is the default attr:  
\\f|note="mynote" cat="person"\\ \+ \\fr 1:3\\ft Got some text at last\\f\*  
Selecting markers in Regex is a concern I have. Currently the Regex for a generalized marker, (except for verse and chapter) is:   
\\\\\\+?\\w+\[\*\\s\]   
The following Regex with with the new attribute markup would cover both milestones and markers with attributes:  
\\\\\\+?\\w+(\\s\*\\|\[^\\\\\]\*?\\\\)?\[\*\\s\]  
(The embedded marker code \\+? can be removed for full 3.1.)  
MH: Note this regex has a bug in that it doesn't disambiguate escape chars and doesn't properly identify the end of the attributes. (Parsing is hard if done properly).  
KS: I have added the limitation (see above and below) that escaped characters are not allowed in attributes. Do not see how you could make a simple regex following your proposal that allows escaped characters in attrs. 

The Regex for the current proposal would be slightly more complex and only covers markers with attributes but not milestones:  
\\\\\\+?\\w+\[\*\\s\](\\\\a\\s\*\\|\[^\\\\\]\*?\\\\\\\*\\s\*)?  
But by treating the attributes as a full milestone, one only has to match milestones and then associate those attributes with the parent. Using milestones this regex simplifies to:  
\\\\\\+?\\w+\[\*\\s\](\\\\a\\s\*\\|.\*?\\\\\\\*\\s\*)?  
MH: Although we could have a debate about pulling out individual key, values and whether a newline can occur in the attribute list, etc. Notice that with \\a, a marker is still just a marker and parsing does not change since a milestone is still a milestone, etc.  
KS: I agree, and for that reason I favor your original proposal if we want to require all characters may occur in an attr.

##### Advantages

* Because it doesn't add another marker, modifying Regex coding would be easier.  
* It aligns regular marker attributes with Milestone marker attributes.  
  * But the identification of the end of the attributes needs special parsing handling, so no.  
* People could not misuse it by adding it in the middle of text as an anchor the way the current proposal would allow. (See the discussion on Anchors).   
  * The grammar does that already for \\cat  
* Provides an economical alternative way of adding lemma attributes to \\w …\\w\* markup that puts the attribute at the beginning of the span, which is good for parsing. It would even allow us to deprecate the current system if we wanted to.  
  * It saves 3 or 4 chars: \\tc1|lang="en"\\ vs \\tc1 \\a|lang="en"\\\*  
* Applied to Notes without ordering ambiguity.

##### Disadvantages

* The  proposed aid anchors would need to be explicitly specified as an attribute  
  * MH: Not necessarily  
* It introduces a new \\\<space\> special (and no, one can't simply match up to the next \\ since \\ is used for escaping).  
  * This is significant  
* It introduces the need for special parsing between content initial and content final attributes.

---

#### Counter proposal by MH

In the above proposal to add attributes directly to markers:  replace final \\\<space\> with |

##### Rationale

Above proposal introduces:

* a new \\\<space\> special (one can't simply match up to the next \\ since \\ is used for escaping).  
* It introduces the need for special parsing between content initial and content final attributes.

##### Proposal

a final | might work as in:  
\\w|Jesus|Jésus\\w\* or \\w|lemma="Jesus"| Jésus\\w\*  
Notice the perhaps clearer layout using structural space after the second | (which would be optional).

##### Examples

Replacing \\cp and  \\vp with attributes on \\c and \\v   
\\c |cp="one" ca="A" nopub="true" label="Chapter A"| 1  
\\v |aid="hello" pub="a"| 1 In the beginning

#### Anti-counter proposal KWS

Making USFM able to do everything that XML and USJ do means that it will lose essential simplicity. I would rather introduce a limitation on USFM, USX and USJ to not allow \\ or other escaped characters (e.g. \\\\ \\\* \\|) or newline \\n in attributes.   
Also I want to clarify that the above proposal is to not put a space after the marker when adding an attribute (this is what the regex assumes). I have therefore corrected the text and examples above:  
	The spaces before  | and after the final \\ are structural. \=\> The space after the final \\ is structural.   
\\tc1 |lang="en"\\ \=\> \\tc1|lang="en"\\\<space\>   
\\ip |authorship\\ \=\> \\ip|authorship\\\<space\> 

#### Antianti-counter proposal MH

Matching an unescaped backslash using a regular expressions is actually pretty hard. We want to match a \\ if it is preceded by 0 or an even number of \\. So the standard expression insertion to match a marker and all its attributes would be:  
	\\\\(.\*)?\\s\*(?:\\|(?:\[^|\]|\\\\\\\\)+\\||\\s)\\s\*  
And for a backslash followed by a space it is similar:  
 \\\\(.\*)?\\s\*(?:\\|(?:\[^|\]|\\\\\\\\)+\\\\)?\\s+)  
---

#### Curly Braces Up Front Counterproposal (JWR)

Attributes occur in a curly brace delimited list immediately after the marker to which they pertain.  The attribute list has the same scope as the corresponding marker.

Examples:

```
\w {lemma="λόγος"} word \w* of God

\w {source="ἀγαθὸν ποιεῖν"} doing good \w*

\w {source="בֵּית לֶחֶם"} Bethlehem \w*

\p {align="center"} This is a centered paragraph. \p*
```

BNF:

```
<marker> ::= "\\" <marker_name> [<attribute_list>] <text> <marker_end>  
<marker_name> ::= <letter>+  
<attribute_list> ::= "{" <attribute> ("," <attribute>)* "}"  
<attribute> ::= <key> "=" <value>  
<key> ::= <letter>+  
<value> ::= '"' <any_text_except_quotes> '"'  
<text> ::= <word_or_space>*  
<word_or_space> ::= <word> | " "  
<word> ::= <letter_or_symbol>+  
<marker_end> ::= "\\" <marker_name> "*"
```

Comparison of USFM and USX:

USFM:

```
\f {aid="gcn-001" cat="consultant-note"} \fr Genesis 1:1
\ft  This may well mean creation from chaos, not from nothing. Consider whether your translation conveys this nuance clearly.
\f*
```

USX:

```
<note style="f" aid="gcn-001" cat="consultant-note">
  <char style="fr">Genesis 1:1</char>
  <char style="ft">
    This may well mean creation from chaos, not from nothing. Consider whether your translation conveys this nuance clearly.
  </char>
</note>
```

Advantages:

* Similar to lists of attributes in XML, HTML.  
* Scope of attributes is flexible and explicit, following existing conventions in XML, HTML.  
* Easier to parse \- attributes are known at the beginning of a marker, and can be immediately used to process following content.  
* Unambiguous.  
* Does not require a new marker, adds this capability to all markers instead.

Disadvantages / problem areas

* { and } will need to be added to the escaped characters list. Yet more meta characters.  
* The BNF does not account for escaped characters like "  
* The only difference between this and using | to delimit is the use of { }  
* The footnote example is missing its caller

[^1]:  This may change and is dependent on the discussion around 25002 Anchors
