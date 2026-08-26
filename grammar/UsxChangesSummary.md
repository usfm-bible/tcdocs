# Executive summary

Some USFM/USX development teams only use the USX form of the data. This document summarizes the changes between USFM 3.0.8 and USFM 3.1.2 that affect USX.

The goal of the USFM/USX technical committee when selecting changes for USFM 3.1.2 was to only allow changes that would not affect the existing structure of USX.

NOTE: The formatting of USFM styles is not included in the USFM 3.1 specification. The documentation has example usage along with formatted text and descriptions of USFM markers in this document will contain links to that online documentation.

# USX RNG schemas

The most recent RNG schema for USFM 3 is USFM 3.0.8 and is found [here](https://github.com/ubsicap/usx/blob/master/schema/usx.rng).

The RNG Schema for USFM 3.1.2 is found [here](https://github.com/usfm-bible/tcdocs/blob/3.1.2/grammar/usx.rng)

The largest difference between the two schemas is that the USFM 3.1.2 schema has annotations that are used to guide a reference USFM to USX parser. These annotations are in the `usfm` namespace which is ignored when using the schema to validate USX. For other changes see the sections on new styles.

# Upgrading from USMF 3.0 to USFM 3.1.2

Paratext 9 has an option to upgrade a USFM 3.0 project to USFM 3.1. No new markers or attributes are added during the upgrade process. The following changes will be made:
 - The `+` character before nested styles will be removed since it is no longer needed in USFM 3.1. The `+` was not included in the USX generated from USFM 3.0.
   - Example: `\bd bold\\+it bold-italic\\+it*\bd*`
   - Upgraded: `\bd bold\it bold-italic\it*\bd*`
   - USX: unchanged
 - Ending markers will be added when a character style is closed by the start of a new character style. This will not affect the USX since the `char` element is being closed in the same place, the USFM is just being made more explicit about where the style closes.
   - Example: `\bd bold\it italic\it*`
   - Upgraded: `\bd bold\bd*\it italic\it*`
   - USX: unchanged
 - To prevent footnotes and cross-references from having many new ending markers, USFM 3.1 defines the section markers for notes as special character styles that don't need ending markers. See [footnote character types](https://docs.usfm.bible/usfm/3.1.2/char/notes/footnote/index.html) and [cross reference character types](https://docs.usfm.bible/usfm/3.1.2/char/notes/crossref/index.html) for the list of markers treated this way.
 - The `xt` marker in a footnote is a regular character style. This means that an ending marker will be added for it and that it will be nested under the previous note section marker. This will create a minor difference in the USX, but it will not affect the meaning of the USX.
   - Example: `\f - \ft text\xt JHN 3.16\f*`
   - Upgraded: `\f - \ft text\xt JHN 3.16\xt*\f*`
   - 3.0 USX:<br>
	> `<note style='f' caller='-'>`<br>
	> &nbsp;&nbsp;`<char style='ft'>text</char>`<br>
	> &nbsp;&nbsp;`<char style='xt'>JHN 3.16</char>`<br>
	> `</note>`
   - 3.1 USX:<br>
   > `<note style='f' caller='-'>`<br>
   > &nbsp;&nbsp;`<char style='ft'>text`<br>
   > &nbsp;&nbsp;&nbsp;&nbsp;`<char style='xt'>JHN 3.16</char>`<br>
   > &nbsp;&nbsp;`</char>`<br>
   > `</note>`<br>

# New Paragraph Styles

## `ipc` - Introduction centered paragraph

A new paragraph style to be used in book introductions. This style is similar to the `pc` style for Scripture content.

See [ipc documentation](https://docs.usfm.bible/usfm/3.1.2/para/introductions/ipc.html) for more details.

## `mi#` - Indented continuation (margin) paragraph

The existing `mi` style had corresponding `mi1`, `mi2` and `mi3` styles added to make it more similar to other indented paragraph styles.

See [mi# documentation](https://docs.usfm.bible/usfm/3.1.2/para/paragraphs/mi.html) for more details.

# New Table Styles

The table heading (`th...`) markers and the table cell (`tc...`) markers have been expanded to allow for 12 columns. The USX schemas have just checked for the table heading and cell styles to match a pattern, but the Paratext stylesheet has required explicit numeric values on the markers.

There is no changed to the meaning of the markers.

# New Character Styles

## `pl` - Inline subheading

Added for inline headings that some projects use so semantic meaning could be given to the text rather than just using a style like `bd'.

There is [pl documentation](https://docs.usfm.bible/usfm/3.1.2/char/features/pl.html) for more details.

## `ta` - Text alternatives

Used to documentent alternate readings to text enclosed in the style. The attributes of the style are not a fixed set, but have the form `a-id` where the id is used to identify dialect of the alternative.

See [ta documentation](https://docs.usfm.bible/usfm/3.1.2/char/features/ta.html) for more details.

## `wl` - Non-vernacular words

This is similar to the `tl` marker, but that marker is used for transliterated text. The new `wl` marker is used for text that is still in the script used by the other language. The marker has an optional `lang` attribute that will contain the language code of the text.

See [wl documenation](https://docs.usfm.bible/usfm/3.1.2/char/features/wl.html) for more details.

# New Milestone markers

## `vid` - Current reference identifier

This milestone is only used for Scripture portions. The milestone has a required `ref` attribute for the reference being established and an optional `h` attribute for running header text. This milestone is a placeholder until USFM 3.2 is implemented that will allow attributes on paragraph elements.

See [vid documentation](https://docs.usfm.bible/usfm/3.1.2/ms/vid.html) for more details.

# Changes to existing styles

## `lit` marker can now occur in introductions

The purpose of the `lit` marker is still for liturgical notes/comments, but it can now occur in both introduction and Scripture content sections.

See [lit documention](https://docs.usfm.bible/usfm/3.1.2/para/paragraphs/lit.html) for more details.

## `IntroList` category added to schema

The `IntroList` category was added to the schema to allow styles like `ili1` to use `ListChar` character styles like `lik`.

This means that the embedded `ListChar` elements for lists in scripture content may also be used in introduction lists. See [scripture content lists](https://docs.usfm.bible/usfm/3.1.2/para/lists/index.html) for examples.

# Changes to attributes

## Optional `lang` attribute added to `tl` marker

The `lang` attribute was added to the `tl` marker to allow a language id be included on the tag.

See [tl documentation](https://docs.usfm.bible/usfm/3.1.2/char/features/tl.html) for more details.

## Most attribute checking removed from schema

The USX 3.0 schema had many rules about attributes that made the schema stricter than the new USX 3.1 schema. Unknown attributes will not cause problems for tools processing USX,

# Appendix A - Styles that were added and later Deprecated

A couple of styles were added in earlier discussion by the USFM/USX committee, and were later deprecated as not being needed. These styles are unlikely to occur in any project data.

# `efm` - Reference to caller of previous footnote in a study Bible

This was initially added to be used in study Bible content like the existing `fm` marker, but later discussion decided the additional marker wasn't needed.

# `t-s` and `t-e' - milestone markers

Added milestone markers that were later deprecated.

# Appendix B - Paratext 9.5 styles that are not in USX 3.1 schema

This appendix lists the styles in the Paratext 9.5 usfm_sb.sty stylesheet that are not included in the USX 3.1 schema to help anyone trying to determine why a style is not part of the schema.

## Deprecated and Obsolete styles removed

The following styles that were deprecated and obsolete in USFM 3.0 have been removed from USFM 3.1:
* conc - Peripherals - Back Matter Concordance
* cov - Peripherals - Other - Cover
* fs - Footnote - Footnote Summary
* glo - Peripherals - Back Matter Glossary
* idx - Peripherals - Back Matter Index
* maps - Peripherals - Back Matter Map Index
* intro - Peripherals - Front Matter Introduction
* ph - Paragraph - Hanging Indent - Level 1
* ph1 - Paragraph - Hanging Indent - Level 1
* ph2 - Paragraph - Hanging Indent - Level 2
* ph3 - Paragraph - Hanging Indent - Level 3
* phi - Paragraph - Indented - Hanging Indent
* pref - Peripherals - Front Matter Preface
* ps - Paragraph - No Break with Next Paragraph
* psi - Paragraph - Indented - No Break with Next
* pub - Peripherals - Front Matter Publication Data
* pubinfo - Publication - Information
* spine - Peripherals - Other - Spine
* toc - Peripherals - Front Matter Table of Contents
* tr1 - Table - Row - Level 1
* tr2 - Table - Row - Level 2
* wr...wr* - Auxiliary - Wordlist/Glossary Reference 

## Paratext styles not in USX

The Paratext style sheet has contained styles that have never been supported in USX. These were not included in the defintion of USFM 3.1:
* erq - Study - Reflective Questions
* erqe - Study - Reflective Questions Ending
* ms2e - Heading - Major Section Ending Level 2
* ms3e - Heading - Major Section Ending Level 3
* s1e - Heading - Section Ending Level 1
* s2e - Heading - Section Ending Level 2
* s3e - Heading - Section Ending Level 3
* s4e - Heading - Section Ending Level 4
* xtSee - Concordance and Names Index - Alternate Entry Target Reference
* xtSeeAlso - Concordance and Names Index - Additional Entry Target Reference
* zpa-xb - Periph - Book
* zpa-xc - Periph - Chapter
* zpa-xv - Periph - Verse
* zpa-d - Periph - Description

