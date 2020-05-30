import json
import sys



def extract_key(jgrammar, key, new_grammar):
    # first extract the definition.
    rules = jgrammar[key]
    new_grammar[key] = rules
    # then go through the rules
    for rule in rules:
        for token in rule:
            if token not in jgrammar:
                continue
            else:
                if token in new_grammar:
                    continue
                else:
                    extract_key(jgrammar, token, new_grammar)
    return new_grammar


def main(args):
    json_file = args[0]
    key = (args[1] if len(args) > 1 else '<START>')
    with open(json_file) as f:
        jval = json.load(f)
    new_grammar = {}
    json.dump(extract_key(jval, key, new_grammar), sys.stdout)


main(sys.argv[1:])
