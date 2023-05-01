
PYTHON ?= python
CHUNKSIZE ?= 0
JOBS ?= 1

unknown:
	@- echo "There are various useful targets:"
	@- echo "diagrams   All the svg and png syntax diagrams"
	@- echo "tests      Run all the tests"
	@- echo "single     Run a single test TEST=path"
	@- echo "dbl        Set DBLDIR and test against dbl zips"
	@- echo "settings variables: CHUNKSIZE=0, PYTHON=python"

diagrams: markers/images/schema/p_rail.svg

markers/images/schema/p_rail.svg : grammar/usx.rng python/scripts/mkraildiagrams
	- $(PYTHON) python/scripts/mkraildiagrams -g $< -o markers/images/schema -z 1
	- cd markers/images/schema; for f in *.svg; do inkscape -d 300 -o "pngs/$${f%.svg}.png" $$f; done

tests: testresults.log
	@- echo "`grep 'Passed' $< | wc -l` Tests passed"
	@- echo "`grep 'Failed' $< | wc -l` Tests failed"

testresults.log : grammar/usx.rng
	$(PYTHON) python/scripts/usfmxtest -m "ms=zaln-s,zaln-e,k-s,zms" -m "section=s5" -m "bkhdr=sts" -j ${JOBS} -g $< tests | tee $@

grammar/usx.rng : grammar/usx.rnc
	$(PYTHON) python/scripts/urnc2rng $< $@

dbl: grammar/usx.rng
	$(PYTHON) python/scripts/usfmtestdbl -g $< --oneerror --skipfile=skipmelist.txt -C ${CHUNKSIZE} -T 300 -l debug ${DBLDIR} | tee dbltest.log

single: grammar/usx.rng $(TEST)/origin.usfm
	$(PYTHON) python/scripts/usfmxtest -m "ms=zaln-s,zaln-e,k-s,zms" -m "section=s5" -m "bkhdr=sts" -l debug -P -g $< $(TEST)
