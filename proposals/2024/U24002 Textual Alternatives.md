# Textual Alternatives

M. Hosken

## Executive Summary

This is a proposal to add a new character style `\ta` which allows for alternate text based on a text identifier. While a full Anglicisation project would result in a separate text, it is often convenient to run both texts together during translation and development. Consider the alternative spelling of color/colour. This would be represented as

```
so he made him a robe of many \ta colors|uk="colours"\ta*.

then the \ta rooster|aus="cockerel" uk="cock"\ta* crowed a third time.

Haj so kerela jekh manuś saves si les sǎ e lumǎ haj xasarela pesqo \ta
ʒivipen|a="gi" b="ilo" c="ʒivimos" d="ʒivimos"\ta*?
```

The new marker is a simple character style with arbitrary attributes.

## Justification

While there are more complex models for describing alternative text, as discussed below, the committee decided that the likelihood of there being much tooling support for this marker was low and therefore that it should be kept as simple as possible. Should this new marker prove popular, there is nothing to stop more complex models being added around it for larger runs of text. Where particular styling (at the character level) is required for a particular alternative, this can be achieved through using empty default strings, which are supported in a character style when there are attributes.

## Discussion

1. Do we want to namespace the id as in `\ta rooster|a-aus="cockeral" a-uk="cock"\ta*` so that the controlling attributes are clearly identified?

# Previous Discussion Document

This proposal adds 5 new markers to support textual alternatives to USFM. A textual alternative is an alternative text based on an alternative id. Four of the markers form two milestone pairs. One pair is for an alternative that matches an id (or id list) and one pair is for a non matching alternative. For example:

```
Haj so kerela jekh manuś saves si les sǎ e lumǎ haj xasarela pesqo \ta-s\*
ʒivipen\ta-e\*\ta-s|a\*gi\ta-e\*\ta-s|b\*ilo\ta-e\*\ta-s|alt="c d"\*
ʒivimos\ta-e\*?
```

But that is a lot of syntax for simple text. Even the line wrapping is problematic. So we introduce a fifth convenience marker that puts the textual alternatives into attributes:

```
Haj so kerela jekh manuś saves si les sǎ e lumǎ haj xasarela pesqo \ta
ʒivipen|a="gi" b="ilo" c="ʒivimos" d="ʒivimos"\ta*?
```

The proposed additional markers are:

```
\ta\ta* \ta-s\* \ta-e\* \tan-s\* \tan-e\*
```

## Introduction

There are numerous contexts in which it might be useful to be able to produce multiple texts from a single source text. For example:

- Anglicisation or other dialectal variation  
- different target audiences such as using catholic key terms that differ from protestant ones;  
- key term differences (for example the only difference between the Shangdi and Shen editions of the Chinese Bible is the word used for God).  
- How numbers are presented: 120, one hundred twenty, one hundred and twenty  
- the CEV comes in American / British and Australian versions where the Australian only differs from the British in one word i.e. USA rooster, UK cock, AUS cockerel.  
- Minor local dialect differences which would allow a single project to handle them all without having to fork (and subsequently maintain) multiple translation text(s)  
- In a Back Translation, highlight alternative senses of a word, or different ways to render a phrase for a consultant to understand the possible range of meanings, but still leave the text clean for publishing just the primary rendering.  
- To be able to use words from different (high/low) registers in the same translation (the version to be understood by the average reader on the street, and the formal churchy language)

It is much more convenient in such situations to hold the texts as a single text, since the alternatives are small and rare and managing two texts just for these variations is too great an overhead.

This proposal addresses the question of how we might encode such alternation in USFM.

### Use Cases

\[MP\] In a project in South Asia, there are two related languages being worked on in parallel, and they try to be as close in meaning as possible. However, there are times when the different dialects are forced to render something differently. The team maintains a SINGLE back translation of both dialects, but currently has no way of identifying differences between the 2 vernacular language texts. They don’t want to maintain separate back translations, but need to be able to present each one as a true reflection of the vernacular (for consultants, but also during publishing in print and electronically).

\[MP\] In PNG there are cluster projects that have a single back translation for 4 or 5 closely related vernacular texts.

\[MP\] Many language communities in North India have Hindu-oriented scriptures, but also need a Muslim-oriented version of the same text. Key words and phrases need to be changed, but the rest of the text stays the same. Having alternative translations in the same text would be excellent.

## Discussion

### Justification

Why do we need to store this information in the USFM file? Could we side reference the differences out of band?

One option is indeed to have a set of standard changes that run over the text, even if targeted to specific verses. This is an alternative of standard side referencing where a scripture reference text range is replaced by the alternative text. These ranges and changes are stored in a separate file and processed on a standard text. Using changes over direct references, makes the changes file more resilient to changes in the underlying text. But it is still a separate file that must be crafted and managed.

In most cases it is expected that a team will want to edit and review every difference, and since it is part of their text (as they understand it) it makes sense to store it as part of the text rather than in a separate file.

This proposal does not preclude the use of a separate changes file to achieve the same thing. But there is a considerable difference between retrofitting a set of changes, e.g. Anglicisation to an already complete translation over adding the alternatives as one goes.

\[DG\]  Simple rule based approaches may, however, be totally unsuitable. In some multi-dialectal situations it may be that a given word is widely understood in one sense, but other dialects also use it in other senses. A case-by-case analysis would be necessary here.  E.g. in Romani *hulavel*  is the verb for ‘separates’ or ‘combs’ , but in some dialects the majority-language word is borrowed for ‘separate’ leaving *hulavel* as only  ‘combs’. There are multiple similar words, e.g.  *astarel*  ‘start’ or ‘catch’,  *xoli*   ‘upset/angry’,  ‘’upset/sad’ or ‘rage’, *cipil*  ‘shout’ or ‘scream in pain/rage’, *den muj*  ‘say’ or ‘shout’.  

\[DG\] Another situation is that of homonyms/homographs. Many romani dialects have no word for lake, river or sea, so all of them are rendered as ‘the water Galilee’ and similar. Some dialects, however, have *len*  ‘lake’, which is a homonym/homograph of both the demonstrative  ‘them’ and ‘take.3PL’. While a speaker of the dialect  would recognise which word is meant from context, a rule-set to distinguish which one is a suitable target for an automatic process is going to be fraught with errors, and there will be considerable amounts of  context for a list of standard changes.

\[DG\]  Any fragmentation into 2 or more files/projects brings the high risk that important changes elsewhere are lost.  In a project with contextual changes files, these  files would be in an unfamiliar format for normal translators. They should be worked on in parallel to the text when the team are discussing renderings, but will likely be forgotten or accidentally invalidated by a typo. Having the alternative variants in the same single source text prevents these issues.  It is also, of course, far simpler for a MTT to get used to typing a strange incantation into USFM than to try to create an entry in some external file that would successfully reference some particular occurrence of *len* in a given verse.  For the above reasons out-of-band solutions, while OK in some specific circumstances, do not meet the use-case of a normal translator, unless Paratext provides full support (which is currently assumed unlikely).

\[DG\] While we are used to national boundaries defining dialect in the context of English, the variation of dialects can  also be very fluid in a  multi-dialect minority language situation, varying over a few kilometers, or multiple dialects being in the same church,  whether that is in a displaced community or where dialects meet geographically.  For example the user of a scripture app might want to switch between a more dialectal reading for home-use and a more ‘communal’/’popular’ rendering for church, or an evangelist might be glad to have multiple dialects available on his device to choose the best variety for his audience. This of course foresees app support for this marker, but if it were to exist, this ability to switch dialects would be very useful to the evangelist who suddenly finds himself face-to-face with a speaker of a rare dialect in a location where network connection is poor.

\[MH\] During translation it is helpful to see all the variants, even if in the end the variants are flattened into their own projects for distribution and publication.

### Design

There are a number of approaches to this question. But there are a few factors to try to keep in mind:

- The resulting USFM shouldn't be too 'ugly' since users have to directly interact with it.  
- We don't want to nest markers if we can help it.  
- The text should not be ambiguous in its interpretation.

A first cut solution was to use a character style:

```
Haj so kerela jekh manuś saves si les sǎ e lumǎ haj xasarela pesqo \ta
ʒivipen\ta*\ta gi|a\ta*\ta ilo|b\ta*\ta ʒivimos|alt="c d"\ta*?
```

This keeps each alternative in its own marker and is semantically clear. The attribute specifies which alternative id the text is appropriate for, and if missing is for the text with no textual alternative. This works well at the character level, but unfortunately does not work where different paragraphs are involved, which does occur. 

For this reason, the basic structural element needs to be a milestone. But for many alternatives, the difference is merely a word difference, and so a convenience marker is also proposed that brings all the simple textual alternatives into a single character style, making it easier for users to interact with. Thus the example immediately above is not proposed and we can use the ta marker for the convenience character style.

In addition to a positive assertion, as in 'include this text if the alternative id is as specified' we need a negative assertion: 'include this text if the alternative id is other than specified'. We could just rely on the list of alternative ids being a closed set. But this would introduce significant instability if a user were to add a new alternative id to their list.

### Alternative id

An alternative id is a single identifier, identical in structure to the tag of a usfm marker. I.e. it is simple ASCII, not starting with a digit, etc. By being a single word, it allows a list of ids to be a simple space separated list. It also allows the alternative id to be used as an attribute name in the tv character style.

In the case of the ta character style, if an alternative id is not found in the attribute list, the main text of the character style is used.

### Milestones

We don't need to repeat the alt attribute in the closing milestone. One only needs id type attributes in a closing milestone if one needs to support a non-overlapping hierarchy. There is no need for such a non-overlapping hierarchy for textual alternatives. It would just get too confusing.

One difficulty with milestones that applies here (rather than generally), is that the milestones have to be balanced in the hierarchy. That is, within the document hierarchy, both milestones in the pair must have the same parent. This is because when a particular milestone is enabled or disabled, its contents must be a complete USFM structure. This is particularly true in USX.

## Alternatives

### \<ta\>

Another approach is to introduce a \<ta\> element into the USX that can contain pretty much anything. This then has a positive or a negative matching attribute with a list of alternative ids. We would then need to introduce \\ta and \\tae as internal milestones (like \\c and \\v) to start and stop the element.  
This is a fairly hefty syntax extension both in USFM and USX. What it gains us is an ensured balancing in the hierarchy. But how important is that at a grammatical level. We only need to resolve that at the semantic level.

### Milestones

The current proposal has each alternative simply enabled or disabled via the milestones. This has a couple of problems:

- A non aware processor will output all the variants regardless since they are included in the main text.  
- There is no way to work out what the 'default' case is for various cases

Another approach is to have a `\ta-s` and `\ta-e` to span a section that has alternatives and then to section off the particular alternatives within that, with the default coming first. E.g.

```
\ta-s\*
\p This is a long colorful paragraph in American English
\tav|uk\*
\p This is a long colourful paragraph using the English of his majesty
\tav|av\*
\p Verily is this a long and most colourful paragraph pertaining to the language of the king
\ta-e\*
```

But this is not processable with a regex because of the default material at the front.

### Conditional markers

Another alternative is to make all elements conditional, by adding one or two universal attributes, as in:

```
\p|alt="us"|\v 1 This is a long colorful paragraph in American English
\p|alt="uk"|\v 1 This is a long colourful paragraph using the English of his majesty
\p|alt="av"|\v 1 Verily is this a long and most colourful paragraph pertaining to the language of the king
```

In this case it is the whole paragraph that is conditional, even if it spans multiple source text lines and verses. This approach has the advantage of enforcing the hierarchy. But it does mean the 'default' needs to be identified. Perhaps we can have:

```
\p|nalt="uk av"|\v 1 This is a long colorful paragraph in American English
\p|alt="uk"|\v 1 This is a long colourful paragraph using the English of his majesty
\p|alt="av"|\v 1 Verily is this a long and most colourful paragraph pertaining to the language of the king
```

Notice this is all in addition to a `\ta` character style for short runs of alternative text.

# Discussion

### Display

This proposal either costs a lot for very little gain or will cause problems for projects. There are very few projects that need this and if it is to be supported well Paratext will need to provide the following features:

- Show only one dialect's view based on user choice  
- Generate and manage wordlist, biblical terms and parallel passages for each dialect

This is a lot of work for relatively small gain. It sounds like the costs outweigh the benefits and this feature would not get added to Paratext.

If, on the other hand, this is added with no Paratext support, then what does it gain over using a private use set of markers and tooling around that? If there is no Paratext support then this will impact project checking. Another alternative approach is to use special category footnotes to hold the variant text and then write ad hoc tooling to present the alternatives when needed.

But the whole point of standards is interoperability. So if there is enough interest in this, we don't want to have each organisation rolling its own. There is nothing special here from a tooling perspective at a minimum. For example, if an editor hides the parameters to markers, then it will hide these as well. So, standardising does not imply tooling and it does:

- Open the door to tooling in the future  
- Mean we all agree to represent this in the same way  
- Guide people on the right way to address this if they see a need in their context

What is problematic is that it has an open set of attributes. This is the first such marker.

Are the differences regular or contextual? If regular then some kind of .map can create a daughter? Project. If the changes are contextual, then the information needs to be in the USFM file somehow. Pulling the information out into side loaded information  requires greater tooling support so that people can see the alternatives in context. 

\[DG\] Support in paratext would be nice, but USFM/USX is used in other contexts, for example scripture websites, scripture apps, and the DBL. Standardisation of markup is of benefit to all. If every project that needs this feature invents its own ad-hoc solution with locally-defined tooling, then this is a return to the disunited situation of pre-unification SFM.  I believe the USFM committee should concern itself with the standard, and not with tooling.

\[DG\] **IF** Paratext developers decided to provide a basic level of support (i.e. something, but not the full support discussed above), it could provide rendering options to colour the versions of the text differently (when checking all variants) or hide some variants, basically some switched styling. However, there is no *requirement* that this proposal receive any support from Paratext or other tooling, beyond not choking on the new markup.

\[DG\] (Probably belongs somewhere else in the document) Testing and checking in a dialect-unification project wastes enormous amounts of time due to word-choice and ‘everyone says this’ / ‘no they don’t, my neighbours say ….’ debates. The result can be hurt feelings and the prospect that valued team members feel that their contributions are continually rejected and their fellow dialect speakers’ needs are being ignored. This affirmation of linguistic diversity and knowledge (even if the final version will not be printed in their dialect) is of value.  The ability to record dialectal variants and move on would be of enormous benefit for team unity and would aid the checking process no end. A separate ‘changes file’ maintained outside Paratext would be very unlikely to provide any assistance to the social aspects of the translating/testing/checking process.

\[MH\] The advantage of not supporting this is that the tool makers don't have to expend effort in 'supporting' this with syntax colouring and switching and all the nice things you are asking for. You are much more likely to get what you want if you say: we would be happy with no special tooling support and if there is enough interest then we can revisit the need for tooling support. Because I am seeing that currently the tool makers don't have the capacity to engage with this and if you demand it be supported, they will simply reject the proposal.

\[DG\] I am entirely happy with no tooling support. My suggestion (to users) is that for the current situation of no support from tools is that the “convenience” form above be the most used, with the default rendering being the most commonly used:

```
then the \ta rooster|aus="cockerel" uk="cock"\ta* crowed a third time.
```

This preserves a printable text in any present tooling, data is preserved and accessible (e.g. via a changes file), and it is also the most visually clear USFM for translators. Where markup within the fragment is somehow necessary), however, the milestone form would be required, and thus at least *some*  kind of changes file would be required for all variants.  
