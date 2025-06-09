# Lists and Tables

Approved for addition to USFM 4.

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

## Issues

### Required or Not Required?

Currently it is proposed that \<list\> is a required element around a list and that the USFM milestones are only required if needed, but if they occur they must occur as a pair. Do we want to relax some of those constraints to improve backward compatibility or tighten them to ensure greater consistency?  
For backward compatibility, the milestones are not required. Clearly, if the milestones are taking attributes such as @aid or even @cat, then a milestone has to exist to carry the information. If one side is marked, it is required that the other be marked. I.e. the milestones must occur in a pair and are not free to be used independently.  
Probably will be required in a later version.

## Discussion

Please enter any comments in this discussion area rather than adding comments to this doc. The conclusion of any discussion will be then transferred into the main document above this heading. The advantage of this approach is that the discussion can be kept as part of the history of the document once it is placed in the tcdocs repository. Please also keep styling to that which conforms to markdown export.

### Required?

DJG: From the above, it is not clear if `\list-s … \list-e` and `\table-s … \table-e` are intended to be required elements or optional for where there is ambiguity / a need for an @aid. If an attribute is needed then the milestones are necessary to hold the attribute.

### Implications

Would it be appropriate to convert `\esb` and `\esbe` into milestones to correspond to \<sidebar\>? If USFM were being invented from scratch, then this would make sense. But given the existing standard, there is no such expectation. Rather than calling `\esb` and `\esbe` paragraphs, we can call them 'bare milestones' in that they have no explicit closing marker and cannot take attributes. But neither are they paragraphs that can take content other than other paragraphs.  
USFM has a number of what are best described as bare milestones: `\b`, `\pb`, `\esb`, `\esbe`. These bare milestones are such that they close the previous paragraph (they are paragraph level milestones).  
