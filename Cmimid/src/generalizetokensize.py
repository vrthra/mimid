import sys
import json
import util
import pta

import grammartools

def collapse_alts(rules, k):
    ss = [[str(r) for r in rule] for rule in rules]
    x = pta.generate_grammar(ss, k[1:-1])
    return x

def is_token_rule(key, grammar):
    has_generalizable_token = False
    for rule in grammar[key]:
        for t in rule:
            if grammartools.is_nt(t): return False
            if (t[0], t[-1]) == ('[', ']'):
                has_generalizable_token = True

    return has_generalizable_token


def collapse_rules(grammar):
    r_grammar = {}
    for k in grammar:
        if is_token_rule(k, grammar):
            new_grammar = collapse_alts(grammar[k], k)
            # merge the new_grammar with r_grammar
            # we know none of the keys exist in r_grammar because
            # new keys are k prefixed.
            for k_ in new_grammar:
                r_grammar[k_] = new_grammar[k_]
        else:
            r_grammar[k] = grammar[k]
    return r_grammar

def collect_repeating_range(grammar):
    return collapse_rules(grammar)

def main(args):
    gfname = args[0]
    with open(gfname) as f:
        gf = json.load(fp=f)
    grammar = gf['[grammar]']
    start = gf['[start]']
    command = gf['[command]']
    g_ = collect_repeating_range(grammar)
    print(json.dumps({'[start]': start, '[grammar]':g_, '[command]': command}, indent=4))

if __name__ == '__main__':
    main(sys.argv[1:])

