all: manual.pdf

../../grammar/usx.rng : ../../grammar/usx.rnc
	- ../../python/scripts/urnc2rng $< $@

../../markers/images/schema/p_rail.svg : ../../grammar/usx.rng ../../python/scripts/mkraildiagrams
	- ../../python/scripts/mkraildiagrams -g $< -o ../../markers/images/schema -z 1
	- cd ../../markers/images/schema; for f in *.svg; do inkscape -d 300 -o "pngs/$${f%.svg}.png" $$f; done

manual.pdf : manual.adoc usfm-theme.yml ../../markers/images/schema/p_rail.svg
	- asciidoctor-pdf --trace -a pdf-themesdir=. -a pdf-theme=usfm -a pdf-fontsdir="../../fonts;GEM_FONTS_DIR" $<

