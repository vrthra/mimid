import sys
import fuzz as F
import grammartools as G
import util
import pudb
bp = pudb.set_trace
import json
import subprocess

import copy, random

import pta
random.seed(0)

def to_grammar(tree, grammar):
    node, children, _, _ = tree
    if not children: return grammar
    tokens = []
    if node not in grammar:
        grammar[node] = list()
    for c in children:
        tokens.append(c[0])
        to_grammar(c, grammar)
    grammar[node].append(tuple(tokens))
    return grammar

def merge_grammar(g1, g2):
    all_keys = set(list(g1.keys()) + list(g2.keys()))
    merged = {}
    for k in all_keys:
        alts = set(g1.get(k, []) + g2.get(k, []))
        merged[k] = alts
    return {k:[l for l in merged[k]] for k in merged}

def convert_to_grammar(my_trees):
    grammar = {}
    ret = []
    for my_tree in my_trees:
        tree = my_tree['tree']
        start = tree[0]
        src_file = my_tree['original']
        arg_file = my_tree['arg']
        ret.append((start, src_file, arg_file))
        g = to_grammar(tree, grammar)
        grammar = merge_grammar(grammar, g)
    return ret, grammar

def check_empty_rules(grammar):
    new_grammar = {}
    for k in grammar:
        if ':if_' in k:
            name, marker = k.split('#')
            if name.endswith(' *'):
                new_grammar[k] = grammar[k].add(('',))
            else:
                new_grammar[k] = grammar[k]
        elif k in ':while_': # or k in ':for_':
            # TODO -- we have to check the rules for sequences of whiles.
            # for now, ignore.
            new_grammar[k] = grammar[k]
        else:
            new_grammar[k] = grammar[k]
    return new_grammar


def collapse_alts(rules, k):
    ss = [[str(r) for r in rule] for rule in rules]
    x = pta.generate_grammar(ss, k[1:-1])
    return x

def collapse_rules(grammar):
    r_grammar = {}
    for k in grammar:
        new_grammar = collapse_alts(grammar[k], k)
        # merge the new_grammar with r_grammar
        # we know none of the keys exist in r_grammar because
        # new keys are k prefixed.
        for k_ in new_grammar:
            r_grammar[k_] = new_grammar[k_]
    return r_grammar

def convert_spaces_in_keys(grammar):
    keys = {key: key.replace(' ', '_') for key in grammar}
    new_grammar = {}
    for key in grammar:
        new_alt = []
        for rule in grammar[key]:
            new_rule = []
            for t in rule:
                for k in keys:
                    t = t.replace(k, keys[k])
                new_rule.append(t)
            new_alt.append(new_rule)
        new_grammar[keys[key]] = new_alt
    return new_grammar

MAX_CHECKS = 1000
def check_grammar(g, start, command):
    for k in g:
        check_key(g, k, start, command)

def check_key(g, gk, start, command):
    fg = G.get_focused_grammar(g, (gk, []))
    fuzzer = F.LimitFuzzer(fg)
    tree = None
    check = 0
    while tree is None:
        tree = fuzzer.iter_gen_key(G.focused_key(start), max_depth=0)
        val = util.check('', '', '<__MINE_CHECK__(%d/%d)>' % (check, MAX_CHECKS), tree, command, '', '')
        check += 1
        if not val:
            tree = None
        if check > MAX_CHECKS:
            print("Exhausted limit for key:%s" % gk, file=sys.stderr)
            return

def usage():
    print('''
grammar-miner.py <generalized parse trees>
    Given a set of generalized parse trees, mine the grammar
            ''')
    sys.exit(0)

def main(args):
    if not args or args[0] == '-h': usage()
    tracefile = args[0]
    with open(tracefile) as f:
        generalized_trees  = json.load(f)
    ret, g = convert_to_grammar(generalized_trees)
    cmds = {src for starts,src,arg in ret}
    starts = {starts for starts,src,arg in ret}
    assert len(cmds) == 1
    cmd = list(cmds)[0]
    assert len(starts) == 1
    start_symbol = list(starts)[0]
    g = G.grammar_gc(g, start_symbol) # garbage collect
    check_grammar(g, start_symbol, cmd)
    with open('build/g1_.json', 'w+') as f: json.dump(g, f)

    g = check_empty_rules(g) # add optional rules
    g = G.grammar_gc(g, start_symbol) # garbage collect
    check_grammar(g, start_symbol, cmd)
    with open('build/g2_.json', 'w+') as f: json.dump(g, f)

    g = collapse_rules(g) # learn regex
    g = G.grammar_gc(g, start_symbol) # garbage collect
    check_grammar(g, start_symbol, cmd)
    with open('build/g3_.json', 'w+') as f: json.dump(g, f)

    g = convert_spaces_in_keys(g) # fuzzable grammar
    g = G.grammar_gc(g, start_symbol) # garbage collect
    check_grammar(g, start_symbol, cmd)
    with open('build/g4_.json', 'w+') as f: json.dump(g, f)
    print(json.dumps({'[start]': start_symbol, '[grammar]':g, '[command]':cmd}, indent=4))

if __name__ == '__main__':
    main(sys.argv[1:])

