#!/usr/bin/env bash

filename=$PWD/$1
prog=$2
cp $filename ../taints/build/my.input
( cd ../taints/;
cat build/my.input | $prog.instrumented
gzip -c output > build/output.gz
./install/bin/trace-taint -me build/metadata -po build/pygmalion.json -t build/output.gz
) 2>build/err 1>build/out

mv ../taints/build/pygmalion.json $filename.json
python src/events.py $filename.json > $filename.trace 2>/dev/null
PARSE=1 python src/treeminer.py $filename.trace 2>/dev/null
