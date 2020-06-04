#!/usr/bin/env python
import sys
import pudb
import grammartools
# ulimit -s 100000
sys.setrecursionlimit(99000)
import random
import string
import util
import copy
import json
import re
import fuzz as F
import subprocess
b = pudb.set_trace
def is_nt(token):
    return token.startswith('<') and token.endswith('>')

def generalize_tokens(grammar):
    g_ = {}
    for k in grammar:
        new_rules = []
        for rule in grammar[k]:
            new_rule = []
            for token in rule:
                if not is_nt(token):
                    new_rule.extend(list(token))
                else:
                    new_rule.append(token)
            new_rules.append(new_rule)
        g_[k]  = new_rules
    return g_

def get_list_of_single_chars(grammar):
    lst = []
    for p,key in enumerate(grammar):
        for q,rule in enumerate(grammar[key]):
            for r,token in enumerate(rule):
                if is_nt(token): continue
                if len(token) == 1:
                    lst.append((key, q, r, token))
    return lst

def remove_recursion(d):
    new_d = {}
    for k in d:
        new_rs = []
        for t in d[k]:
            if t != k:
                new_rs.append(t)
        new_d[k] = new_rs
    return new_d

def fill_tree(tree, parent, gk):
    filled_tree = []
    to_fill = [(tree, filled_tree)]
    while to_fill:
        (node, filled_node), *to_fill = to_fill
        name, children = node
        if name == gk:
            new_node = [name, [[parent, []]]]
            filled_node.extend(new_node)
            my_node = filled_node
            # return my_node
        elif not children:
            if name in ASCII_MAP:
                new_node = [random.choice(ASCII_MAP[name]), []]
                filled_node.extend(new_node)
                # return (random.choice(ASCII_MAP[name]), [])
            else:
                new_node = [name, []]
                filled_node.extend(new_node)
                # return (name, [])
        else:
            # update the new nodes
            child_nodes = [[] for c in children]
            new_node = [name, child_nodes]
            filled_node.extend(new_node)
            to_fill = [(c, child_nodes[i]) for i,c in enumerate(children)] + to_fill
    return my_node, filled_tree


def replaceable_with_kind(stree, orig, parent, gk, command):
    my_node, tree0 = fill_tree(stree, parent, gk)
    #print(json.dumps(tree0, indent=4), file=sys.stderr)
    sval = util.tree_to_str(tree0)
    assert my_node is not None
    a1 = my_node, '', tree0
    if parent == orig:
        aX = ((gk, [[orig, []]]), '', tree0)
        val = util.is_a_replaceable_with_b(a1, aX, command)
        if val:
            return True
        else:
            return False
    else:
        for pval in ASCII_MAP[parent]:
            aX = ((gk, [[pval, []]]), '', tree0)
            val = util.is_a_replaceable_with_b(a1, aX, command)
            if val:
                continue
            else:
                return False
        return True


# string.ascii_letters The concatenation of the ascii_lowercase and ascii_uppercase constants described below. This value is not locale-dependent.
# string.ascii_lowercase The lowercase letters 'abcdefghijklmnopqrstuvwxyz'. This value is not locale-dependent and will not change.
# string.ascii_uppercase The uppercase letters 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'. This value is not locale-dependent and will not change.
# string.digits The string '0123456789'.
# string.hexdigits The string '0123456789abcdefABCDEF'.
# string.octdigits The string '01234567'.
# string.punctuation String of ASCII characters which are considered punctuation characters in the C locale: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~.
# string.printable String of ASCII characters which are considered printable. This is a combination of digits, ascii_letters, punctuation, and whitespace.
# string.whitespace A string containing all ASCII characters that are considered whitespace. This includes the characters space, tab, linefeed, return, formfeed, and vertical tab.

def parent_map():
    parent = {}
    for sp in string.whitespace:
        parent[sp] = '[__WHITESPACE__]'
    for digit in string.digits:
        parent[digit] = '[__DIGIT__]'
    for ll in string.ascii_lowercase:
        parent[ll] = '[__ASCII_LOWER__]'
    for ul in string.ascii_uppercase:
        parent[ul] = '[__ASCII_UPPER__]'
    for p in string.punctuation:
        parent[p] = '[__ASCII_PUNCT__]'

    parent['[__WHITESPACE__]'] = '[__ASCII_PRINTABLE__]'

    parent['[__DIGIT__]']      = '[__ASCII_ALPHANUM__]'
    parent['[__ASCII_LOWER__]']      = '[__ASCII_LETTER__]'
    parent['[__ASCII_UPPER__]']      = '[__ASCII_LETTER__]'
    parent['[__ASCII_LETTER__]']      = '[__ASCII_ALPHANUM__]'
    parent['[__ASCII_ALPHANUM__]']      = '[__ASCII_PRINTABLE__]'
    parent['[__PUNCT__]']               = '[__ASCII_PRINTABLE__]'
    return parent

ASCII_MAP = {
        '[__WHITESPACE__]': string.whitespace,
        '[__DIGIT__]': string.digits,
        '[__ASCII_LOWER__]': string.ascii_lowercase,
        '[__ASCII_UPPER__]': string.ascii_uppercase,
        '[__ASCII_PUNCT__]': string.punctuation,
        '[__ASCII_LETTER__]': string.ascii_letters,
        '[__ASCII_ALPHANUM__]': string.ascii_letters + string.digits,
        '[__ASCII_PRINTABLE__]': string.printable
        }
PARENT_MAP = parent_map()
def find_max_generalized(tree, kind, gk, command):
    if kind not in PARENT_MAP: return kind
    parent = PARENT_MAP[kind]
    if replaceable_with_kind(tree, kind, parent, gk, command):
        return find_max_generalized(tree, parent, gk, command)
    else:
        return kind

def do_n(tree, kind, gk, command, n):
    ret = []
    for i in range(n):
        pval = random.choice(ASCII_MAP[kind])
        ret.append([pval, []])
    return (gk, ret)

def find_max_widened(tree, kind, gk, command):
    my_node, tree0 = fill_tree(tree, kind, gk)
    sval = util.tree_to_str(tree0)
    assert my_node is not None
    a1 = my_node, '', tree0

    # this is a single character. Now, try 2, 4 etc.
    pvals = do_n(tree, kind, gk, command, 2)
    aX = (pvals, '', tree0)
    val = util.is_a_replaceable_with_b(a1, aX, command)
    if not val: return kind
    pvals = do_n(tree, kind, gk, command, 4)
    aX = (pvals, '', tree0)
    val = util.is_a_replaceable_with_b(a1, aX, command)
    if not val: return kind
    return kind + '+'

GK = '<__GENERALIZE__>'
MAX_CHECKS = 1000
def generalize_single_token(grammar, start, k, q, r, command, blacklist):
    # first we replace the token with a temporary key
    gk = GK
    # was there a previous widened char? and if ther wase,
    # do we belong to it?
    char = grammar[k][q][r]
    if r > 0 and grammar[k][q][r-1][-1] == '+':
        # remove the +
        last_char = grammar[k][q][r-1][0:-1]
        if last_char in ASCII_MAP and char in ASCII_MAP[last_char]:
            #we are part of the last.
            grammar[k][q][r] = last_char + '+'
            return grammar

    g_ = copy.deepcopy(grammar)
    g_[k][q][r] = gk
    g_[gk] = [[char]]
    #reachable_keys = grammartools.reachable_dict(g_)
    # now, we need a path to reach this.
    fg = grammartools.get_focused_grammar(g_, (gk, []))
    fuzzer = F.LimitFuzzer(fg)
    #skel_tree = find_path_key(g_, start, gk, reachable_keys, fuzzer)
    tree = None
    check = 0
    while tree is None:
        #tree = flush_tree(skel_tree, fuzzer, gk, char)
        #tree = fuzzer.gen_key(grammartools.focused_key(start), depth=0, max_depth=1)
        tree = fuzzer.iter_gen_key(grammartools.focused_key(start), max_depth=1)
        val = util.check(char, char, '<__CHECK__(%d/%d)>' % (check, MAX_CHECKS), tree, command, char, char)
        check += 1
        if not val:
            tree = None
        if check > MAX_CHECKS:
            print("Exhausted limit for key:%s, rule:%d, token:%d, char:%s" % (k, q, r, char), file=sys.stderr)
            blacklist.append((k, q, r, char))
            #raise "Exhausted limit for key:%s, rule:%d, token:%d, char:%s" % (k, q, r, char)
            return grammar
        # now we need to make sure that this works.

    gen_token = find_max_generalized(tree, char, gk, command)
    if gen_token != char:
        # try widening
        gen_token = find_max_widened(tree, gen_token, gk, command)
    del g_[gk]
    g_[k][q][r] = gen_token
    # preserve the order
    grammar[k][q][r] = gen_token
    return grammar

def remove_duplicate_repetitions(g):
    new_g = {}
    for k in g:
        new_rules = []
        for rule in g[k]:
            #srule = ''.join(rule)
            new_rule = []
            last = -1
            for i,t in enumerate(rule):
                if last >= 0 and len(t) > 0 and t[-1] == '+' and t == rule[last]:
                    continue
                else:
                    last = i
                new_rule.append(t)
            #snrule = ''.join(new_rule)
            #if srule != snrule:
            #    print("change:",file=sys.stderr)
            #    print("  ", srule, file=sys.stderr)
            #    print("  ", snrule, file=sys.stderr)
            new_rules.append(new_rule)
        new_g[k] = new_rules
    return new_g

def usage():
    print('''
generalizetokens.py <grammar file>
    Given a mined grammar, which contains multiple chars digits etc as
    alternatives widen them to character classes. The
    character classes are then widened to their parents (seen below)
    until one of the checks in MAX_CHECKS fail.

    [__WHITESPACE__]        => [__ASCII_PRINTABLE__]
    [__DIGIT__]             => [__ASCII_ALPHANUM__]
    [__ASCII_LOWER__]       => [__ASCII_LETTER__]
    [__ASCII_UPPER__]       => [__ASCII_LETTER__]
    [__ASCII_LETTER__]      => [__ASCII_ALPHANUM__]
    [__ASCII_ALPHANUM__]    => [__ASCII_PRINTABLE__]
    [__PUNCT__]             => [__ASCII_PRINTABLE__]
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

    # now, what we want to do is first regularize the grammar by splitting each
    # multi-character tokens into single characters.
    generalized_grammar = generalize_tokens(grammar)

    # next, we want to get the list of all such instances

    list_of_things_to_generalize = get_list_of_single_chars(generalized_grammar)
    #print(len(list_of_things_to_generalize), file=sys.stderr)

    # next, we want to generalie each in turn
    # finally, we want to generalize the length.
    #reachable_keys = reachable_dict(grammar)
    g_ = generalized_grammar
    blacklist = []
    for k, q, r, t in list_of_things_to_generalize:
        assert g_[k][q][r] == t
        bl = []
        g_ = generalize_single_token(g_, start, k, q, r, command, bl)
        if bl:
            print("Blacllisted:", bl, file=sys.stderr)
            blacklist.extend(bl)

    g = remove_duplicate_repetitions(g_)
    g = grammartools.remove_duplicate_rules_in_a_key(g)

    # finally, we want to generalize the length.
    #g = generalize_size(g_)
    print(json.dumps({'[start]': start, '[grammar]':g, '[command]': command, '[blacklist]': blacklist}, indent=4))

if __name__ == '__main__':
    main(sys.argv[1:])
