#!/usr/bin/env python
import sys
import util
import json
import fuzzingbook.Parser as P

def main(args):
    with open(args[0]) as f:
        mined = json.load(f)
    with open(args[1], mode='r+b') as f:
        v = f.read().decode()
    mgrammar = mined['[grammar]']
    mstart = mined['[start]']
    parser = P.IterativeEarleyParser(P.non_canonical(mgrammar), start_symbol=mstart)
    try:
        result = parser.parse(v)
        for tree in result:
            s = util.tree_to_str(tree)
            if s == v:
                print('parsed')
                sys.exit(0)
            else:
                print('Invalid match %s' % repr(v))
                sys.exit(1)
    except SyntaxError:
        print('Can not parse - syntax %s' % repr(v))
        sys.exit(2)

if __name__ == '__main__':
    main(sys.argv[1:])

