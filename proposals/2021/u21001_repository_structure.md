---
title: Repository Structure
author: M. Hosken
status: open
code: 21001
issue: 
---

# Repository Structure

M. Hosken

## Executive Summary

This document describes the structure of the usfm.org repository. It introduces
three areas of the repository:

- Proposal documents (proposals/)
- USFM/X description documents (markers/, miscellaneous/, grammar/)
- Committee documents (committee/)

This proposal is for a new document: commitee/repository\_structure.md that
contains everything followsing this executive summary.

## Introduction

There are various models for how a standards committee runs, but at its core,
the work of a committee is the processing of documents. Proposal documents come
in and a documented standard comes out! Proposal documents are important because
they provide the history of how the standard becomes what it is. It is the
living memory of the committee.

Proposal documents, while they contain the story of the standard, are unhelpful
for anyone wanting to understand the standard. They do not want to have to read
the story longitudinally. Instead they want to understand the standard as it
stands today. For this other documents are needed. USFM has an excellent
document in the form of the [USFM
User Manual](https://ubsicap.github.io/usfm/about/index.html). While this is
primarily a user manual for the standard, it is an excellent user manual. This
manual may be supported by other documentation which may, in due course, be
incorporated in the manual, but may also include other technical detail that
is not directly relevant to users and so may not be appropriate for the manual.
For example, details of parsing. In addition, there is a need for a formal
language specification.

## File Formats

Before discussing the structure of the committee repository, it is worth talking
about file formats. A git repository can work with any file format and while we
are using git to manage the repository, it is unlikely that most of the
documents in the repository will see much merging.

### Markdown (Github Flavour)

Markdown is a simple file format to work with. It is presented well in Github
and encourages concentration on the content over the form of the document. It
also makes it easy to edit and repurpose documents collaboratively. The greatest
difficulty with Markdown is the handling of images, since each image has to be
stored as a separate file and then referenced from the markdown document. In
describing the repository directory structure, how markdown images will be
handled is described.

Markdown is the primary document file format.

#### Use of Markdown

There are various flavours of Markdown and this committee uses the Github
flavour of Markdown. In greater detail, the pandoc expression of Github flavour
of Markdown. In addition, we would use the following language types for
marking fenced code sections.

- **usfm** for USFM fragments
- **xml** for USX fragments

Discuss how to produce 2 output docs from single source docs.

### PDF

In some cases, especially where the document is not intended to be edited, for
example in proposal documents, it may be easier to use PDF. This can happen if
the document is graphically rich or requires the use of different fonts.

PDF is not ideal in that it is not editable and cannot be merged. But it does
generally guarantee visual integrity across systems and where Markdown is
insufficient, PDF is a good fallback format.

## Repository Structure

To reflect the two stages of standards development (inputs and outputs), the
repository has different top level directories to hold documents for the
different aspects of the committee's work. For each directory we also consider
the role of issues against content in that directory.

Files in the all the directories are considered to be owned by the technical
committee and any committee member may make changes under the authority of the
techincal committee.

### proposals

Proposal documents are not designed to be edited, at least collaboratively. They
are the inputs that the committee discusses to then create the outputs. As such,
the proposal documents form a simple document registry ordered in time. Within
the proposals/ directory there would be a directory for each year, as a means to
break up the list. Within each year's directory, each document is given a number
to make it easier to manage documents. It also helps to use an identifying
letter (u for USFM) before the number that makes it easier to spot document codes. Thus the
document code for this document is u21001. This structure is based on the
successful document registry scheme used by the Unicode Consortium.

The full filename for a document may be anything but is generally the document
code followed by a non space separated descriptive title. Thus this document is
`u21001_repository_structure.md`. Any other associated files with a document,
for example images, should follow the same initial document code. Each
proposals/ year directory contains an images/ directory so that images
associated with documents can be stored separately and not clutter the directory
listing. If a document has a lot of images, a document may be itself a directory
with everything needed for it within that. The directory is named as if it were
a document (with no extension).

Sometimes there is more than one document that needs to be grouped with other
documents under the same number. In this case the document code may be suffixed
with a letter. For example u21001a. Notice that the document number is 3 digits.
It is not anticipated that the committee will need to address more than a
thousand documents a year. It is unlikely even to address a hundred!

Documents are considerd to be owned by their author and committee members should
not make changes to other people's proposal documents. Thus issues are requests
for the author to make changes to their proposal. At some point, proposal
documents are considered closed and no changes should be made to them. They have
been actioned and the changes should affect the actioned results rather than the
proposal that caused the actions.

It is expected that a proposal has a corresponding issue.

This document aims to present an exemplar of a proposal document. The structure
of a proposal document is lightweight. The header of:

```
---
title: Proposal Title
author: An. Author, An O. Author
status: open or completed or rejected
issue: github issue number if relevant
code: document code
---
```

Proposals are expected to begin with an executive summary that states, in
summary, how the world will be different once this proposal is acted upon.

#### index.md

Each year directory also contains one `index.md` file that consists of a list of
all the documents in the directory. Each entry in the list includes: the
document number, the title, the author. Once the document is included in the
repository, they document number becomes a link to the document (even if
within a subdirectory).

The advantage of a version control system is that document revision is easy and
sometimes proposals go through a number of revisions. There is no need to track
each revision of the document. So, for example, the commitee may review this
document and decide that changes are needed and that they are not ready to copy
the contents of the document into a commitee document, even with modifications.
Instead they want to make changes to the document (either directly or via the
author) and then review it again later. This document may be revised in situe
and re-reviewed, since older revisions are recoverable via the wonders of git.

The pre-allocation of document numbers is helpful in allowing authors to include
the document code in the filename and even the document text. Document numbers
should only be allocated once an author is sure the document will be accepted
into the registry. Document acceptance is very open in that it does not require
committee approval to add a document. Clearly anything unsuitable for the
repository will not be added. Whether a document exists is evident from there
being a link for it in the index.md.

### markers

The primary structure of the USFM user manual is around descriptions of markers.
This is a good primary descriptive mechanism. The markers directory contains
extra descriptive detail for each marker in the standard. Each marker has an
associated Markdown file that contains more description on the marker as
developed by the committee. Information from these files may or may not end up
in the user manual. Thus there might be a file markers/pb.md containing further
description of the pb marker. The markers/ directory has an images/
subdirectory.

Issues against documents in the markers directory can become work items for the
technical committee or can spawn a proposal document. But, naturally, they are
requests to add content or make changes to the relevant marker documents. These
would probably be the main issues that get raised.

### documentation

There are situations that may need describing that are not best discussed in the
description of a particular marker. These can be discussed in documents in the
miscellaneous/ directory. Documents are not coded and just have a descriptive
title. The miscellaneous/ directory has an images/ subdirectory.

Like issues against documents in the markers directory, issues againsts
miscellaneous/ documents may spawn work items for the technical committee.

This directory also includes such components as document templates as well as bits that go into the docs.

### grammar

In developing a formal grammar, the committee will create various files as well
as documents. These are all kept in a suitable tree withing the grammar/
directory. The structure is yet to be agreed and is flexible to the needs of
that project.

Issues in this directory would be to fix problems in the files in this tree.

### committee

The committee/ directory contains documents pertinant to the description of the
committee. For example, it is intended that once agreed, much of the content of
this proposal end up as a document in that directory.

Issues in this directory would reflect small changes not worth raising a
proposal document for to committee documents.

