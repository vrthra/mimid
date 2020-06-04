import sys
import pudb
bp = pudb.set_trace
import util
import json
import os.path, copy, random
random.seed(0)

from generalizemethod import register_node, NODE_REGISTER, identify_compatibility_patterns


def can_the_loop_be_deleted(pattern, k, executable):
    xnodes = [xnode for xnode in NODE_REGISTER[k] if xnode[-1]['pattern'] == pattern]
    can_be_deleted = True
    for xnode in xnodes:
        node0, tree0, executable0, inputfile0, _info = xnode
        a = util.is_a_replaceable_with_b((node0, '', tree0), (['', [], 0, 0], '', tree0), executable)
        if not a:
            can_be_deleted = False
            break
    for xnode in xnodes:
        node0, tree0, executable0, inputfile0, info = xnode
        method1, ctrl1, cname1, num1, can_empty, cstack1 = util.parse_pseudo_name(node0[0])
        name = util.unparse_pseudo_name(method1, ctrl1, cname1, num1, util.Epsilon if can_be_deleted else util.NoEpsilon, cstack1)
        info['node'][0] = name

def update_pseudo_name(k_m, my_id):
    # fixup k_m with what is in my_id
    original = k_m[0]
    method, ctrl, cid, altid, can_empty, method_stack = util.parse_pseudo_name(original)
    if ctrl == 'if':
        name = util.unparse_pseudo_name(method, ctrl, cid, "%s.%d" % (altid, my_id), can_empty, method_stack)
    elif ctrl == 'while':
        assert altid == '0'
        name = util.unparse_pseudo_name(method, ctrl, cid, my_id, can_empty, method_stack)
    else:
        assert False
    k_m[0] = name
    return name, k_m

def collect_pseudo_nodes(node, tree, executable, inputfile):
    node_name, children, si, ei = node
    if util.is_node_pseudo(node):
        register_node(node, tree, executable, inputfile)

    for child in children:
        collect_pseudo_nodes(child, tree, executable, inputfile)

def update_original_pseudo_names(node_name):
    registered_xnodes = NODE_REGISTER[node_name]
    for xnode in registered_xnodes:
        # name it according to its pattern
        nodeX, treeX, executableX, inputfileX, infoX = xnode
        pattern = infoX['pattern']
        update_pseudo_name(infoX['node'], pattern)

def generalize_loop_trees(jtrees, log=False):
    my_trees = []
    for j in jtrees:
        tree = util.to_modifiable(j['tree']) # The tree ds.
        executable = j['original']
        inputfile = j['arg']
        # we skip START
        node_name, children, *rest = tree
        assert node_name == '<START>'
        for child in children:
            collect_pseudo_nodes(tree, tree, executable, inputfile)
        my_trees.append({'tree':tree, 'original': executable, 'arg': inputfile})

    for k in NODE_REGISTER:
        patterns = identify_compatibility_patterns(k)
        for p in patterns:
            can_the_loop_be_deleted(patterns[p], k, executable)

    # finally, update the original names.
    for k in NODE_REGISTER:
        if k == '<START>': continue
        update_original_pseudo_names(k)
    return my_trees

def usage():
    print('''
generalizeloop.py <trees json>
    Given the json file containing the extracted parse trees from the set of inputs
    generalize the loop names using active labelling.
    ''')
    sys.exit(0)

def main(args):
    if not args or args[0] == '-h': usage()
    tracefile = args[0]
    with open(tracefile) as f:
        mined_trees = json.load(f)
    util.init_log('generalize_loop', '', mined_trees[0]['original'])
    gmethod_trees = generalize_loop_trees(mined_trees)
    print(json.dumps(gmethod_trees, indent=4))

main(sys.argv[1:])
