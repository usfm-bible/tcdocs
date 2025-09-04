# U25010 rx, ep, ebr

M. Hosken

Proposed for 3.1.2

This proposal adds 3 new markers: \\rx (cross reference), \\ep (explanatory
paragraph) and \\ebr (explanatory bridged text) with categories of char, sectionpara and
sectionpara respectively. They are introduced as main text replacements for \\xt,
\\ip and \\iex. As such, these markers are deprecated for use in main text (and
anywhere outside \\x for \\xt) as of 3.2 with the intent to remove them in 4. No
projects are expected to use these markers until 3.2, but they are available for
use now.

In summary:

| Marker | Replacing | Category     | Context                           |
| ------ | --------- | ------------ | --------------------------------- |
| rx     | xt        | char         | Outside of \\x cross reference    |
| ep     | ip        | sectionpara  | Outside of introductions          |
| ebr    | iex       | sectionpara  | Outside of introductions          |

## \\rx

### Introduction

The \\rx marker is added to identify reference lists. It has two purposes. The
first is to give a character style to use for styling reference lists (rather
than the references within the list). The second is for tooling to identify
reference lists for automatic parsing and processing. A reference list may
contain just a single reference.

```
male and female He created them.\f + \fr 1:27\ft Cited in \rx Matthew 19:4
and Mark 10:6\rx*\f*
```

More fully this would become:

```
male and female He created them.\f + \fr 1:27\ft Cited in \rx \ref Matthew
19:4|MAT 19:4\ref* and \ref Mark 10:6|MRK 10:6\ref*\rx*\f*
```

### Rationale

\\xt has served well in its dual role of identifying references in cross
references and in other contexts. But there is confusion, in that within a \\x
cross reference, \\xt is structural and implicitly closed, while elsewhere it is
simple a character style. \\rx is introduced to reduce \\xt to just having a
cross reference structural role and no general character styling role.

The conversion is simple in that all uses of \\xt outside of \\x should be
replaced with \\rx. No projects are expected to do this until USFM 3.2, but the
marker is made available now.

## \\ep

This marker is used for introductory explanatory text found as part of the main
body text rather than before the first chapter. It is treated as section heading
material for processes such as gridding

## \\ebr

This marker is used to explain gaps in the versification, for example if some
scripture text is not included due to manuscript attestation.



These two markers 
