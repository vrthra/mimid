.SECONDARY:

PYTHON=python3
pfuzzer=../taints
CC=clang-8

CFLAGS=-xc++ -std=c++14
CFLAGS=-I/usr/lib/llvm-8/lib/clang/8.0.0/include

EXAMPLE_C_SOURCE=example3.c

LIBCLANG_PATH=/usr/local/Cellar/llvm/8.0.1/lib/libclang.dylib
LIBCLANG_PATH=/usr/lib/llvm-8/lib/libclang.so

CLANG_FORMAT=/usr/local/Cellar/llvm/8.0.1/bin/clang-format
CLANG_FORMAT=/usr/lib/llvm-8/bin/clang-format

instrument: | build
	CFLAGS=$(CFLAGS) LIBCLANG_PATH=$(LIBCLANG_PATH) $(PYTHON) ./src/instrument.py examples/$(EXAMPLE_C_SOURCE) | $(CLANG_FORMAT) > build/$(EXAMPLE_C_SOURCE)

build/%.out: examples/%.c
	$(CC) $(CFLAGS) -g -o $@ $< -I ./examples

build/%.o.x: build/%.orig.c
	$(CC) $(CFLAGS) -g -o $@ $< -I ./examples


build/%.orig.c: examples/%.c
	CFLAGS=$(CFLAGS) LIBCLANG_PATH=$(LIBCLANG_PATH) $(PYTHON) ./src/simplify.py $< > $@_.tmp
	cat $@_.tmp | $(CLANG_FORMAT) > $@_
	mv $@_ $@

build/json.out: examples/json.c | build
	$(CC) $(CFLAGS) -g -o $@ $^ -I ./examples

build: ; mkdir -p $@

build/%.c: build/%.orig.c build/%.out build/%.o.x src/instrument.py | build
	cp examples/*.h build/
	CFLAGS=$(CFLAGS) LIBCLANG_PATH=$(LIBCLANG_PATH) $(PYTHON) ./src/instrument.py $< > $@_.tmp
	cat $@_.tmp | $(CLANG_FORMAT) > $@_
	mv $@_ $@

build/%.x: build/%.c
	$(CC) $(CFLAGS) -g -o $@ $^ -I ./examples

build/%.d: examples/%.c src/instrument.py | build
	cp examples/*.h build/
	CFLAGS=$(CFLAGS) LIBCLANG_PATH=$(LIBCLANG_PATH) $(PYTHON) ./src/instrument.py $<

build/%.input: examples/%.input
	cat $< > $@

build/%.inputs.done: examples/%.grammar
	mkdir -p build/$*
	#for i in examples/$*.input.*; do echo $$i; cp $$i build/; done
	$(PYTHON) src/generateinputs.py examples/$*.grammar $* ./build/$*.out ./build/ 100
	touch $@

build/%.json.done: build/%.x build/%.inputs.done
	mkdir -p $(pfuzzer)/build/
	rm -rf $(pfuzzer)/build/*
	cp examples/*.h build
	cp -r build/* $(pfuzzer)/build
	for i in build/$*.input.*; \
	do\
	  echo $$i; \
	  cp $$i $(pfuzzer)/build/$*.input; \
	  (cd $(pfuzzer) && $(MAKE) build/$*.taint;) ; \
		cp $(pfuzzer)/build/pygmalion.json build/$*/$$(basename $$i).json; \
		cp $$i build/$*/ ; \
	done

build/tiny.events: build/tiny.json.done
	$(PYTHON) ./src/tokenevents.py build/tiny/ > $@_
	mv $@_ $@

build/mjs.events: build/mjs.json.done
	$(PYTHON) ./src/tokenevents.py build/mjs/ > $@_
	mv $@_ $@


build/%.events: build/%.json.done
	$(PYTHON) ./src/events.py build/$* > $@_
	mv $@_ $@


build/%.tree: build/%.events
	$(PYTHON) ./src/treeminer.py $< > build/$*-trees.json
	$(PYTHON) ./src/generalizemethod.py build/$*-trees.json > build/$*-method_trees.json
	$(PYTHON) ./src/generalizeloop.py build/$*-method_trees.json > build/$*-loop_trees.json
	cp build/$*-loop_trees.json $@

build/%.mgrammar: build/%.tree
	$(PYTHON) ./src/grammar-miner.py build/$*.tree > build/$*-mined_g.json
	$(PYTHON) ./src/generalizetokens.py build/$*-mined_g.json > build/$*-general_tokens.json
	#$(PYTHON) ./src/generalizetokensize.py build/$*-general_tokens.json > build/$*-general_tokensize.json
	cp build/$*-general_tokens.json $@

build/%.grammar: build/%.mgrammar
	$(PYTHON) ./src/grammar-compact.py build/$*.mgrammar > build/$*-compact.json
	cp build/$*-compact.json $@


build/%.pgrammar: build/%.grammar
	$(PYTHON) ./src/parsinggrammar.py build/$*.grammar > build/$*-parsing.json
	cp build/$*-parsing.json $@

UNBUF=script -q -e -c
PARSECOUNT=1000
build/%.precision: build/%.pgrammar
	$(UNBUF) "$(PYTHON) src/check_precision.py examples/$*.grammar build/$*.pgrammar ./build/$*.x ./build/$* $(PARSECOUNT) $*" /dev/null | tee $@.log
	mv build/$*/$*.precision_ $@

build/%.showtree: build/%.tree
	$(PYTHON) ./src/ftree.py build/$*.tree | less -r

build/%.showg: build/%.grammar
	cat build/$*.grammar | jq . -C | less -r

view:
	CFLAGS=$(CFLAGS) ${PYTHON} ./bin/pyclasvi.py -l $(LIBCLANG_PATH)

clean:
	rm -rf build/*.json build/*.grammar

clobber:
	rm -rf build/*
	cd $(pfuzzer) && $(MAKE) clean


dump:
	clang -Xclang -ast-dump -fsyntax-only $(src) -I examples

FUZZCOUNT=1000
build/%.fuzz: build/%.grammar build/%.out
	$(PYTHON) ./src/fuzz.py  $^ $(FUZZCOUNT)
	mv build/$*.out.fuzz $@

