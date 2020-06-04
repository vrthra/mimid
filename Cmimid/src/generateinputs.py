import sys
import util
import os
import random
import json
import re
import fuzz as F
import fuzzingbook.Parser as P

def usage():
    print('''
generateinputs.py  <grammar> <start> <command> <directory> <count>
    Given a grammar, the starting nonterminal, and an uninstrumented executable to validate the inputs against,
    generate <count> number of valid inputs and store them in <directory> in the format <command>.input.<n>
            ''')
    sys.exit(0)

import subprocess
def main(args):
    if not args or args[0] == '-h': usage()
    errors = []
    with open(args[0]) as f:
        s = json.load(f)
    grammar = s['[grammar]']
    start = s['[start]']
    key = args[1]
    command = args[2]
    directory = args[3]
    count = int(args[4])
    os.makedirs(directory, exist_ok=True)
    fuzzer = F.LimitFuzzer(grammar)
    i = 0
    seen = set()
    while True:
        try:
            v = fuzzer.fuzz(start)
            if not v.strip(): continue
            if v in seen: continue
            seen.add(v)
            print(repr(v))
            fn = '%s/%s.input.x' % (directory, key)
            with open(fn, 'w+') as f:
                print(v, end='', file=f)
            o = util.do([command, fn])
            if o.returncode != 0:
                continue
            else:
                i += 1
                with open('%s/%s.input.%d' % (directory, key, i), 'w+') as fn:
                    print(v, end='', file=fn)
        except RecursionError:
            pass
        if i >= count: break
    return errors

def process_token(i):
    if i and i[0] == '<' and ' ' in  i:
        return i.split(' ')[0] + '>'
    elif i and i[0] == '<':
        return i
    else:
        return repr(i)

if __name__ == '__main__':
    main(sys.argv[1:])

