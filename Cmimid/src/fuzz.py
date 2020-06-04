import sys
import random
import json
import re
import util
import grammartools as G
import fuzzingbook.Parser as P
#from fuzzingbook.GrammarFuzzer import tree_to_string
import string
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

class Fuzzer:
    def __init__(self, grammar):
        self.grammar = grammar

    def fuzz(self, key='<start>', max_num=None, max_depth=None):
        raise NotImplemented()

FUZZRANGE = 10

class LimitFuzzer(Fuzzer):
    def symbol_cost(self, grammar, symbol, seen):
        if symbol in self.key_cost: return self.key_cost[symbol]
        if symbol in seen:
            self.key_cost[symbol] = float('inf')
            return float('inf')
        v = min((self.expansion_cost(grammar, rule, seen | {symbol})
                    for rule in grammar.get(symbol, [])), default=0)
        self.key_cost[symbol] = v
        return v

    def expansion_cost(self, grammar, tokens, seen):
        return max((self.symbol_cost(grammar, token, seen)
                    for token in tokens if token in grammar), default=0) + 1

    def nonterminals(self, rule):
        return [t for t in rule if G.is_nt(t)]

    def iter_gen_key(self, key, max_depth):
        def get_def(t):
            if t in ASCII_MAP:
                return [random.choice(ASCII_MAP[t]), []]
            elif t and t[-1] == '+' and t[0:-1] in ASCII_MAP:
                num = random.randrange(FUZZRANGE) + 1
                val = [random.choice(ASCII_MAP[t[0:-1]]) for i in range(num)]
                return [''.join(val), []]
            elif G.is_nt(t):
                return [t, None]
            else:
                return [t, []]

        cheap_grammar = {}
        for k in self.cost:
            # should we minimize it here? We simply avoid infinities
            rules = self.grammar[k]
            min_cost = min([self.cost[k][str(r)] for r in rules])
            #grammar[k] = [r for r in grammar[k] if self.cost[k][str(r)] == float('inf')]
            cheap_grammar[k] = [r for r in self.grammar[k] if self.cost[k][str(r)] == min_cost]

        root = [key, None]
        queue = [(0, root)]
        while queue:
            # get one item to expand from the queue
            (depth, item), *queue = queue
            key = item[0]
            if item[1] is not None: continue
            grammar = self.grammar if depth < max_depth else cheap_grammar
            chosen_rule = random.choice(grammar[key])
            expansion = [get_def(t) for t in chosen_rule]
            item[1] = expansion
            for t in expansion: queue.append((depth+1, t))
            #print("Fuzz: %s" % key, len(queue), file=sys.stderr)
        #print(file=sys.stderr)
        return root

    def gen_key(self, key, depth, max_depth):
        if key in ASCII_MAP:
            return (random.choice(ASCII_MAP[key]), [])
        if key and key[-1] == '+' and key[0:-1] in ASCII_MAP:
            m = random.randrange(FUZZRANGE) + 1
            return (''.join([random.choice(ASCII_MAP[key[0:-1]]) for i in range(m)]), [])
        if key not in self.grammar: return (key, [])
        if depth > max_depth:
            #return self.gen_key_cheap_iter(key)
            clst = sorted([(self.cost[key][str(rule)], rule) for rule in self.grammar[key]])
            rules = [r for c,r in clst if c == clst[0][0]]
        else:
            rules = self.grammar[key]
        return (key, self.gen_rule(random.choice(rules), depth+1, max_depth))

    def gen_rule(self, rule, depth, max_depth):
        return [self.gen_key(token, depth, max_depth) for token in rule]

    def fuzz(self, key='<start>', max_depth=10):
        return util.tree_to_str(self.iter_gen_key(key=key, max_depth=max_depth))

    def __init__(self, grammar):
        super().__init__(grammar)
        self.key_cost = {}
        self.cost = self.compute_cost(grammar)

    def compute_cost(self, grammar):
        cost = {}
        for k in grammar:
            cost[k] = {}
            for rule in grammar[k]:
                cost[k][str(rule)] = self.expansion_cost(grammar, rule, set())
            if len(grammar[k]):
                assert len([v for v in cost[k] if v != float('inf')]) > 0
        return cost

def usage():
    print('''
fuzz.py <inferred json grammar> <uninstrumented-exec> <count>
    Use the provided inferred grammar to generate inputs, and validate them against the given executable.
    The output is in <uninstrumented-exec>.fuzz file.
    The <count> is the number of times to generate inputs.
    ''')
    sys.exit(0)

import subprocess
def main(args):
    if not args or args[0] == '-h': usage()
    errors = []
    with open(args[0]) as f:
        s = json.load(f)
    grammar = s['[grammar]']
    command = s.get('[command]')
    #if len(args) > 1:
    command = args[1]
    f = LimitFuzzer(grammar)
    #key = args[2] if len(args)> 2 else s['[start]']
    key = s['[start]']
    count = int(args[2])
    for i in range(count):
        try:
            v = f.fuzz(key)
            #print(repr(v))
            p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            data, err = p.communicate(input=v.encode())
            #print(p.returncode)
            if p.returncode != 0:
                print("Not accepted: (%d/%d)" % (len(errors), i), repr(v))
                errors.append(v)
        except RecursionError:
            pass

    with open("%s.fuzz" % command, 'w+') as f:
        print("%s %d/%d" % (command, count - len(errors), count), file=f)
    return errors

def process_token(i):
    if i and i[0] == '<' and ' ' in  i:
        return i.split(' ')[0] + '>'
    elif i and i[0] == '<':
        return i
    else:
        return repr(i)

if __name__ == '__main__':
    errors = main(sys.argv[1:])
    print()
    for e in errors:
        print(repr(e))
        print()

    print(len(errors))
