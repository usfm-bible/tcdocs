# tcdocs

This is the document repository for the USFM/X Technical Committee.

## Manual

To create the manual pdf file you need:

- asciidoctor-pdf
- pygments
- rnc2rng
- fonts:
  - DejaVu Sans (has good symbol support for diagrams)
    - Not sure how to share this across systems, since the theme requires it to be in /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf. More asciidoctor-pdf expertise needed.

Then:

```
cd markers
make
```

to build `manual.pdf`
