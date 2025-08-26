# U25009 Paragraph Label (\\pl ... \\pl\*) Marker

**Submitted by:** K. Spielmann  
**Proposed for:** USFM 3.2

This proposal introduces a new character style marker, `\pl ...\pl*`, to be used specifically for in-line subheadings at the beginning of paragraphs.

## Introduction

In many USFM projects, translators and editors include short, in-line subheadings or labels at the beginning of a paragraph. At present, this is often done by reusing existing character style markers such as `\bd ...\bd*` (bold) or `\em ...\em*` (emphasis), or by resorting to structural subheadings (e.g., `\is1`). These practices create inconsistency and ambiguity, both in the semantic meaning of the markup and in its rendering across platforms.

## Usage

The most common use case is in introductory material, where short labels precede explanatory text. Current practices include:

* **Using bold (**`\bd ...\bd*`**)**   
  Danish example (*Bibelen på hverdagsdansk*, 2022 — Introduction to Matthew). Note the mixture of `\ili` and `\ip`:

```
\ili \bd Forfatter, datering og baggrund:\bd* Denne beretning ...
\ip Samtidig gør Mattæus det klart, at den undervisning, som ...
\ili \bd Indhold:\bd* Bogen er en gennemgang af Jesu liv fra hans...
\ili \bd Budskab:\bd* Mattæusʼ hensigt er at vise, at Jesus er den person,... 

```

* **Using emphasis (**`\em ...\em*`**)**  
  Igbo example (*Baịbụlụ Nsọ* (Igbo Living Bible), 1988 — Introduction to Matthew):

```
\im \em ONYE DERE YA:\em* Matiu
\im \em OGE E DERE YA:\em* Afọ 60–70 M.A.K.
```

* **Using structural subheadings (**`\is1` **)**  
  Gbagyi example (*Gbagyi Nyizeyenya Baibwulu: Shekwoyi Ɓədagbma* (Gbagyi Contemporary Bible), 2025 — Introduction to Matthew):

```
\im Matiyu Nabagyi Manai, kwo wunya ntu Yeisu fyífyi ɓo nu n əwo kalalai...
\is1 Nyakayi
\im Matiyu n a ɓə yi wo ge Levyi nyi.
```

With the new marker, these examples would be standardized as:

```
\ip \pl Forfatter, datering og baggrund:\pl* Denne beretning om Jesus...
\ip Samtidig gør Mattæus det klart, at den undervisning, som ...
\ip \pl Indhold:\pl* Bogen er en gennemgang af Jesu liv fra hans...
\ip \pl Budskab:\pl* Mattæusʼ hensigt er at vise, at Jesus er den person,...
```

```
\im \pl ONYE DERE YA:\pl* Matiu
\im \pl OGE E DERE YA:\pl* Afọ 60–70 M.A.K.
```

```
\im \pl Nyakayi:\pl* Matiyu n a ɓə yi wo ge Levyi nyi.
```

## Benefits

* **Semantic Clarity:** Provides a clear and dedicated marker for in-line subheadings.  
* **Markup consistency and improved processing:** Facilitates accurate rendering and transformation in publishing systems, applications, and digital tools. For example, paragraphs that begin with this marker can be specially processed to give them a hanging indent for publication (as in the Danish example).  
* **Consistency Across Projects:** Promotes uniform markup practices in introductions and similar sections.  
* **Backward Compatibility:** Does not affect existing markers; older projects can continue as they are, while new projects can migrate progressively.

## Discussion

It was noted by the committee that `\pl ...\pl*` marker is a character style whereas all other `\p` markers are paragraph styles. Nevertheless semantic clarity was judged to outweigh this inconsistency.  
Other proposed markers which were considered and rejected:

* `\kl` key label   
* `\pk` paragraph key   
* `\sl` section label 
