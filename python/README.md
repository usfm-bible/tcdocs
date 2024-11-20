# usfmtc

Unified Standard Format Markup is the primary file format for the source of
bible translations. It is available in 3 serializations: USFM which is a simple
text markup using TeX style backslash codes to mark the various elements; USX
which is an XML serialization and USJ which is a JSON serialization.

The usfmtc package contains parsers and generators for USFM, USX and USJ. There
are two parsers and generators for USFM: validating and non validating.

The package comes with a script: usfmconv that can read any of the 3 file
formats and output to any of the 3 file formats.

The primary entry point for python is the usfmtc module:

```
from usfmtc import readFile

usfmdoc = readFile(infile)
usfmdoc.saveAs(outfile)
```

