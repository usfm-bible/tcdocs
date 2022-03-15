all: manual.pdf

../grammar/usx.rng : ../grammar/usx.rnc
	- rnc2rng $< $@

images/p_rail.svg : ../grammar/usx.rng ../python/scripts/mkraildiagrams
	- ../python/scripts/mkraildiagrams -g $< -o images

manual.pdf : manual.adoc usfm-theme.yml images/p_rail.svg
	- asciidoctor-pdf -a pdf-themesdir=. -a pdf-theme=usfm $<

