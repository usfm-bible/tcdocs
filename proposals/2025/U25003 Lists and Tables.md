# Lists and Tables

Approved for addition to USFM 3.2 as optional. In USFM 4 the additions will become required.

## Introduction

Currently USFM has no way of identifying and attributing lists and tables. Yes there is a \<table\> element in USX, but this is not stored in USFM and has to be inferred. It also, therefore, cannot hold attributes (for example @aid \- see U25002) that while available in USX/J are not available in USFM.

This proposal proposes the addition of a \<list\> element in USX and two pairs of milestones to represent the start and end of a \<list\> or \<table\>.

## Proposal

The following additions are proposed as optional in v3.2 and as required in v4.

### List

Where two lists follow on from each other, there is no clear way to delimit the two. Is `\b` sufficient or does there need to be a full paragraph? What if one wants a small gap within a list as well as separating lists? In addition, we would like to be able add categories to lists and @aid as well. Just as USX has a \<table\> element, we propose the addition of a \<list\> element to group list items into a coherent list with whole list attribution.  
The category of a list is taken from the cat, following the lead of the \<table\> element.

### Milestones

Neither \<table\> nor the proposed \<list\> element are representable in USFM. Instead they have to be inferred, and that, especially for lists, can be problematic. The proposal then is for two milestone pairs:

* `\list-s\*` and `\list-e\*` to start and end a \<list\> element  
* `\table-s\*` and `\table-e\*` to start and end a \<table\> element

Notice that the markers are quite long. This is not a problem since lists and tables are high level markers that would typically occur on their own line. The starting milestones would also carry the attributes for the corresponding USX elements. Notice that these are paragraph level milestones. This is a new concept in that all our milestones so far have not been paragraph closing.  
A paragraph closing milestone may not be followed by any text but only by the start of a new paragraph.

For backward compatibility the milestones are not required unless a list or table boundary is ambiguous or if attributes are to be provided to the corresponding \<table\> or \<list\> elements. If a starting milestone occurs, a closing milestone is required before any element that would currently indicate an end of table or list (e.g. `\p`).

