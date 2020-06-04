#!/usr/bin/env python3
import sys
import json
import fuzz as F
import grammartools as G

def asciimap_to_nt(key):
    # convert '[__DIGIT__]' to '<__DIGIT__>'
    # convert '[__DIGIT__]+' to '<__DIGIT_s__>'
    if key[-1] == '+':
        orig = key[3:-4]
        return ('+', "<__%s_s__>" % orig)
    else:
        orig = key[3:-3]
        return ('', "<__%s__>" % orig)
import pudb
b = pudb.set_trace
def enhance_grammar(g):
    # convert '[__DIGIT__]' to '<__DIGIT__>'
    # convert '[__DIGIT__]+' to '<__DIGIT_s__>'
    # add both definitions.
    g_ = {}
    added = set()
    for key in g:
        new_rules = []
        g_[key] = new_rules
        for rule in g[key]:
            new_rule = []
            new_rules.append(new_rule)
            for token in rule:
                if G.is_nt(token):
                    new_rule.append(token)
                elif token in F.ASCII_MAP or token[0:-1] in F.ASCII_MAP:
                    rep, nk = asciimap_to_nt(token)
                    new_rule.append(nk)
                    added.add((rep, nk, token))
                else:
                    new_rule.append(token)
    for rep, nk, token in added:
        if rep == '+':
            r, key = asciimap_to_nt(token[0:-1])
            g_[nk] = [[key], [key, nk]]
            g_[key] = [[k] for k in F.ASCII_MAP[token[0:-1]]]
        else:
            g_[nk] = [[k] for k in F.ASCII_MAP[token]]
    return g_
def usage():
    print('''
parsinggrammar.py <json grammar>
    Given a grammar in ebnf format, convert it to the fuzzingbook
    canonical grammar format
            ''')
    sys.exit(0)
def main(args):
    if not args or args[0] == '-h': usage()
    gfname = args[0]
    with open(gfname) as f:
        gf = json.load(fp=f)
    grammar = gf['[grammar]']
    start = gf['[start]']
    command = gf['[command]']

    g = enhance_grammar(grammar)

    print(json.dumps({'[start]': start, '[grammar]':g, '[command]': command}, indent=4))

if __name__ == '__main__':
    main(sys.argv[1:])
