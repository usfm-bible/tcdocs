# Explicitly Marked Unicode

A Unicode Scalar Value (USV) Representation Standard

K. Spielmann

Approved for addition to USFM 3.2.

## Executive Summary

This proposal introduces two new markers for use in USFM only: `\u` and `\U`. They are followed by 4 or 8 hexadecimal digits respectively. The resulting character is inserted in the content of the file. Thus the use of `\u0020` results in a content space rather than a structural space. The content space may be removed during subsequent processing such as canonicalisation. This corresponds directly to the use of `&#x….;` type entities in USX and `\u` in USJ. Notice that in USJ there is no `\U` and that USVs above U+FFFF are stored as surrogate pairs as per UTF-16.

## Introduction

Both USX and USJ have a mechanism for representing **Unicode Scalar Value** as part of content. In order to be fully compatible with those formats USFM needs a way of inserting USVs by number into a text**.** This document defines a standard approach for representing Unicode Scalar Values (USVs) across the three different formats:

* **USFM – USFM Unicode Escape Sequences**  
* **USX – XML Numeric Character References \- NCRs**  
* **USJ – JSON Unicode Escape Sequences**

The goal is to maintain consistency while respecting each format's constraints and maximizing readability and compatibility.

### Implementation

While these are two markers in USFM, they are not considered part of the grammar, even as they may not be used in any other way in the grammar. They are typically handled during the lexical phase of parsing and so do not appear in usx.rnc. This is true for the other serialisations as well.

---

## Standard Representations

### Standard Format Markers

USVs shall be represented using a format based on the approach used by Python and many other programming languages. 

#### Proposed USFM Representation

USFM Unicode Escape Sequences are defined as follows:

* **For BMP characters (≤ U+FFFF):**  
  * `\uXXXX` (4-digit uppercase hexadecimal Unicode code point)  
* **For characters beyond BMP (U+10000 to U+10FFFF):**  
  * `\UXXXXXXXX` (8-digit uppercase hexadecimal Unicode code point)

**Examples:**

* `\u0020` (Space, U+0020)  
* `\U0001F600` (Grinning Face, U+1F600)

This format maintains compatibility with JSON’s BMP escape sequences while allowing **all** USVs to be represented unambiguously.

**Use example:**

* `\p \u0020Text` (A regular space at the beginning of a paragraph.)

Two consecutive regular spaces at the beginning of a paragraph must be reduced to a single structural space in USFM and therefore will not naturally occur. However, such a space can easily be introduced into USX or USJ content. To preserve this space when converting to USFM, it must be explicitly represented using an escape sequence

---

### XML Numeric Character References (NCRs)

XML supports direct Unicode Numeric Character References (NCRs), which shall be used as follows:

#### Hexadecimal NCR Format

```
&#xXXXX;
```

Where:

* `&#x` is a prefix indicating a hexadecimal NCR.  
* `XXXX` is the **Unicode code point in uppercase hexadecimal**.  
* `;` terminates the NCR.

**Examples:**

* `&#x0020;` (Space, U+0020)  
* `&#x1F600;` (Grinning Face, U+1F600)

This format is natively supported in XML and requires no additional processing.

---

### JSON Unicode Escape Sequences

Since JSON natively supports only **Basic Multilingual Plane (BMP)** characters using `\uXXXX` (UTF-16), code points beyond **U+FFFF** require surrogate pairs.

#### Proposed JSON Representation

USVs shall be represented using the **same format as Standard Format Markers**, ensuring compatibility with JSON parsers.

**Example Encoding Rules:**

* **For BMP characters (≤ U+FFFF):**  
  * `\uXXXX` (direct JSON-compatible encoding)  
* **For characters beyond U+FFFF:**  
  * `\UXXXXXXXX` (full Unicode representation, but JSON parsers must preprocess to surrogate pairs if necessary)  
  * `\U0001F600` (U+1F600) → `\uD83D\uDE00`

**Examples:**

| Unicode Code Point | Standard Format Marker | XML NCR | JSON Escape Sequence |
| ----- | ----- | ----- | ----- |
| U+0020 (Space) | `\u0020` | `&#x0020;` | `\u0020` |
| U+1F600 (😀) | `\U0001F600` | `&#x1F600;` | `\uD83D\uDE00` |

**Implementation Note:**

* JSON parsers must **preprocess `\UXXXXXXXX`** and convert characters beyond U+FFFF into their UTF-16 surrogate pairs before usage.

---

## Issues

* Json requires most BMP characters to be encoded with escape sequences (if they are represented that way. Note you can just stick in utf8), Should USJ allow \\UXXXXXXXX codes or accept UMP characters to use surrogate pairs. When converted to USFM or USK normally we want them converted to regular characters. What are the rules for when **JSON Escape Sequences** are preserved as **XML NCR** or **USFM Escape Sequences** or not.  
  * From the RFC ([https://www.ietf.org/rfc/rfc4627.txt](https://www.ietf.org/rfc/rfc4627.txt)): "JSON text SHALL be encoded in Unicode.  The default encoding is UTF-8."  
  * But non BMP characters are stored in surrogate pairs when escaped, or directly in utf-8  
* Handling of escaped characters like the backslash,  
* Handling of field leading spaces when converting to USFM  
* In USX and USJ, the Unicode entities will be processed as if the Unicode value were inserted in the file. This means that &\#x0020;Test will start a paragraph with a space that will be stripped. I assume we should do the same for USFM, but other uses of \\u for structurally parsed stuff would not happen so \\u005cp is not the same as \\p. I.e. it would store \<p\>\\p\</p\> or whatever.  
* 

## Discussion

After discussions within the committee, it was noted that these values are converted into their rendered form within the XML and JSON standards earlier on in the pre-processing phase by a parser. So there was agreement that a similar process of parsing be followed for the USFM. In which case, there is ultimately no semantic difference between representing a character either in the rendered form or as a Unicode Scalar Value (USV). However, the USV does allow for the concept of “escaping” characters within the USFM which is a syntactic step after the document is rendered. But there is already the “\\” character to do that in the USFM.

Therefore, the USV may be characterized as “syntactic sugar” which allows for an alternate representation of characters for those who may desire to use it. The main use-case identified was for typesetting where such codes would make working with invisible characters easier and allow for quick corrections for those who are comfortable using it. Moreover, it allows for symmetry with the USX and USJ serializations. There it has been accepted so far by the committee.
