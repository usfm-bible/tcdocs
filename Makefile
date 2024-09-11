
PYTHON ?= python
CHUNKSIZE ?= 0
JOBS ?= 0
MILESTONES="ms=zaln-s,zaln-e,k-s,k-e,zms,ts-s,ts-e"

unknown:
	@- echo "There are various useful targets:"
	@- echo "files      core files: usx.rng, usfm.ext, glossary.adoc, etc."
	@- echo "diagrams   All the svg and png syntax diagrams"
	@- echo "tests      Run all the tests"
	@- echo "single     Run a single test TEST=path"
	@- echo "dbl        Set DBLDIR and test against dbl zips"
	@- echo "doc        Create documentation files"
	@- echo "settings variables: CHUNKSIZE=0, PYTHON=python"

diagrams: markers/images/schema/pngs/p_rail.png

markers/images/schema/pngs/p_rail.png : grammar/usx.rng python/scripts/mkraildiagrams
	$(PYTHON) python/scripts/mkraildiagrams -g $< -o markers/images/schema -z 1 -p "/" ${LOGGING}
	- cd markers/images/schema; for f in *.svg; do inkscape -d 300 -o "pngs/$${f%.svg}.png" $$f & done

short: TESTEXCLUDES := -x stress
short: tests
test1: TESTSET := -t 1
test1: tests
single1: TESTSET := -t 1
single1: single

tests: testresults.log
#	@- echo "usfmxtest on tests: `grep 'Passed' testresults.log | wc -l` passed / `head -n -1 testresults.log | grep -v '^XML:' | wc -l`"

testresults.log : grammar/usx.rng
	- $(PYTHON) python/scripts/usfmxtest -E tests/markers.ext -j ${JOBS} ${TESTEXCLUDES} ${TESTSET} -q -o $@ -g $< tests
	- $(PYTHON) python/scripts/lxmltest.py -g grammar/usx.rng -E tests/markers.ext -o $@ -A tests

grammar/usx.rng : grammar/usx.rnc
	$(PYTHON) python/scripts/urnc2rng $< $@

dbl: grammar/usx.rng
	$(PYTHON) python/scripts/usfmtestdbl -g $< --oneerror --skipfile=skipmelist.txt -C ${CHUNKSIZE} -T 300 -l debug ${DBLDIR} | tee dbltest.log

single: grammar/usx.rng $(TEST)/origin.usfm
	$(PYTHON) python/scripts/usfmxtest -E tests/markers.ext -l debug ${TESTSET} -P -g $< $(TEST)
	$(PYTHON) python/scripts/lxmltest.py -g $< -E tests/markers.ext $(TEST)/origin.xml

singledbl: grammar/usx.rng
	$(PYTHON) python/scripts/usfmtestdbl -g $< --oneerror --skipfile=skipmelist.txt -C ${CHUNKSIZE} -T 300 -l debug -M ${MATCH} ${DBLDIR}

doc: files diagrams 

manual/antora/modules/ROOT/pages/glossary.adoc: grammar/usx.rng
	$(PYTHON) python/scripts/mkglossary -o $@ $<

files: grammar/usx.rng grammar/usfm.ext manual/antora/modules/ROOT/pages/glossary.adoc

grammar/usfm.ext : grammar/usx.rng
	$(PYTHON) python/scripts/usfmmkext -o $@ $<

