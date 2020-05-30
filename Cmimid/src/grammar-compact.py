import sys
import json
import grammartools

def main(args):
    gfname = args[0]
    with open(gfname) as f:
        gf = json.load(fp=f)
    grammar = gf['[grammar]']
    start = gf['[start]']
    command = gf['[command]']


    # now, what we want to do is first regularize the grammar by splitting each
    # multi-character tokens into single characters.
    g = grammartools.compact_grammar(grammar, start)
    print(json.dumps({'[start]': start, '[grammar]':g, '[command]': command}, indent=4))

if __name__ == '__main__':
    main(sys.argv[1:])
