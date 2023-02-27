
unknown:
	@- echo "There are various useful targets:"
	@- echo "diagrams    All the svg and png syntax diagrams"
	@- echo "tests       Run all the tests"

diagrams: markers/images/schema/p_rail.svg

markers/images/schema/p_rail.svg : grammar/usx.rng python/scripts/mkraildiagrams
	- python/scripts/mkraildiagrams -g $< -o markers/images/schema -z 1
	- cd markers/images/schema; for f in *.svg; do inkscape -d 300 -o "pngs/$${f%.svg}.png" $$f; done

tests: testresults.log
	@- echo "`grep 'Passed' $< | wc -l` Tests passed"
	@- echo "`grep 'Failed' $< | wc -l` Tests failed"

testresults.log : grammar/usx.rng
	python/scripts/usfmxtest -m "ms=zaln-s,zaln-e,k-s" -m "section=s5" -g $< tests | tee $@

grammar/usx.rng : grammar/usx.rnc
	python/scripts/urnc2rng $< $@

