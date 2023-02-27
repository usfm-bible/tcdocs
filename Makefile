
testresults.log : grammar/usx.rng
	python/scripts/usfmxtest -m "ms=zaln-s,zaln-e,k-s" -m "section=s5" -g $< tests | tee $@

grammar/usx.rng : grammar/usx.rnc
	python/scripts/urnc2rng $< $@

