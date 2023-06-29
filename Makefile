
PYTHON ?= python
CHUNKSIZE ?= 0
JOBS ?= 0

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

short: TESTEXCLUDES := -x stress
short: tests

tests: testresults.log
#	@- echo "usfmxtest on tests: `grep 'Passed' testresults.log | wc -l` passed / `head -n -1 testresults.log | grep -v '^XML:' | wc -l`"

testresults.log : grammar/usx.rng
	@- $(PYTHON) python/scripts/usfmxtest -m "ms=zaln-s,zaln-e,k-s,zms" -m "section=s5" -m "bkhdr=sts" -j ${JOBS} ${TESTEXCLUDES} -q -o $@ -g $< tests
	@- $(PYTHON) python/scripts/lxmltest.py -g grammar/usx.rng -m "ms=zaln-s,zaln-e,k-s,zms" -m "section=s5" -m "bkhdr=sts" -o $@ -A tests

grammar/usx.rng : grammar/usx.rnc
	$(PYTHON) python/scripts/urnc2rng $< $@

dbl: grammar/usx.rng
	$(PYTHON) python/scripts/usfmtestdbl -g $< --oneerror --skipfile=skipmelist.txt -C ${CHUNKSIZE} -T 300 -l debug ${DBLDIR} | tee dbltest.log

single: grammar/usx.rng $(TEST)/origin.usfm
	$(PYTHON) python/scripts/usfmxtest -m "ms=zaln-s,zaln-e,k-s,zms" -m "section=s5" -m "bkhdr=sts" -l debug -P -g $< $(TEST)
	$(PYTHON) python/scripts/lxmltest.py -g $< -m "ms=zaln-s,zaln-e,k-s,zms" -m "section=s5" -m "bkhdr=sts" $(TEST)/origin.xml
