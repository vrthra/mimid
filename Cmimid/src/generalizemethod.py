import sys
import pudb
bp = pudb.set_trace
import util
import json
import os.path, copy, random
random.seed(0)

NODE_REGISTER = {}

def update_method_stack(node, old_name, new_name):
    nname, children, *rest = node
    if not (':if_' in nname or ':while_' in nname):
        return
    method, ctrl, cname, num, can_empty, cstack = util.parse_pseudo_name(nname)
    assert method == old_name
    name = util.unparse_pseudo_name(new_name, ctrl, cname, num, can_empty, cstack)
    #assert '?' not in name
    node[0] = name
    for c in node[1]:
        update_method_stack(c, old_name, new_name)

def update_method_name(k_m, my_id):
    # fixup k_m with what is in my_id
    original = k_m[0]
    method, old_id = util.parse_method_name(original)
    name = util.unparse_method_name(method, my_id)
    k_m[0] = name

    for c in k_m[1]:
        update_method_stack(c, original[1:-1], name[1:-1])

    return name, k_m

def register_node(node, tree, executable, input_file):
    # we want to save a copy of the tree so we can modify it later.
    node_name = node[0]
    template_name = '__CMIMID__NODE__'
    node[0] = template_name
    new_tree = copy.deepcopy(tree)
    node[0] = node_name
    new_node = util.get_ref(new_tree, template_name)
    new_node[0] = node_name
    if node_name not in NODE_REGISTER: NODE_REGISTER[node_name] = []
    new_elt = (new_node, new_tree, executable, input_file,
            {'inputstr': util.tree_to_str(new_tree), 'node':node, 'tree':tree})
    NODE_REGISTER[node_name].append(new_elt)
    return new_elt

def collect_nodes_single(node, tree, executable, inputfile, seen):
    node_name, children, si, ei = node
    elt = None
    if util.is_node_method(node):
        elt = register_node(node, tree, executable, inputfile)
        if node_name in seen:
            elt[4]['seen'] = seen[node_name]
        else:
            seen[node_name] = elt
    if len(children) == 1:
        collect_nodes_single(children[0], tree, executable, inputfile, seen)
    else:
        # no longer the single inheritance line.
        for child in children:
            collect_nodes(child, tree, executable, inputfile)


def collect_nodes(node, tree, executable, inputfile):
    node_name, children, si, ei = node
    elt = None
    if util.is_node_method(node):
        elt = register_node(node, tree, executable, inputfile)
    if len(children) == 1:
        collect_nodes_single(children[0], tree, executable, inputfile, {node_name: elt})
    else:
        for child in children:
            collect_nodes(child, tree, executable, inputfile)

def get_compatibility_pattern(xnode, sampled_nodes):
    node0, tree0, executable0, inputfile0, _info = xnode
    results = []
    a0 = node0, inputfile0, tree0
    for snode in sampled_nodes:
        nodeX, treeX, executableX, inputfileX, _info = snode
        aX = nodeX, inputfileX, treeX
        result = util.is_compatible(a0, aX, executable0)
        results.append(result)
    return ''.join(['1' if i else '0' for i in results])

def identify_buckets(node_name):
    all_elts = NODE_REGISTER[node_name]
    # remove the duplicate nodes
    elts = [e for e in all_elts if 'seen' not in e[4]]
    seen_elts = [e for e in all_elts if 'seen' in e[4]]
    first, *rest = elts
    first[4]['pattern'] = 0
    buckets = [first]
    for enode in rest:
        node0, tree0, executable0, inputfile0, _info0 = enode
        a0 = node0, inputfile0, tree0
        compatible = None
        for bi, bnode in enumerate(buckets):
            node1, tree1, executable1, inputfile1, _info1 = bnode
            a1 = node1, inputfile1, tree1
            result = util.is_compatible(a0, a1, executable0)
            if result:
                compatible = bi
                enode[4]['pattern'] = bi
                break
        if compatible is None:
            enode[4]['pattern'] = len(buckets)
            buckets.append(enode)

    for e in seen_elts:
        e_seen = e[4]['seen']
        e_seen_pattern = e_seen[4]['pattern']
        e[4]['pattern'] = e_seen_pattern
    return {i:i for i,b in enumerate(buckets)}

def identify_compatibility_patterns(node_name):
    registered_xnodes = NODE_REGISTER[node_name]
    sampled_xnodes = util.sample(registered_xnodes, util.MAX_PROC_SAMPLES)
    my_patterns = {}
    count = 0
    for xnode in registered_xnodes:
        pattern = get_compatibility_pattern(xnode, sampled_xnodes)
        if pattern not in my_patterns:
            my_patterns[pattern] = count
            count += 1
        _nodeX, _treeX, _executableX, _inputfileX, infoX = xnode
        infoX['pattern'] = my_patterns[pattern]
    return my_patterns

def update_original_method_names(node_name):
    registered_xnodes = NODE_REGISTER[node_name]
    for xnode in registered_xnodes:
        # name it according to its pattern
        nodeX, treeX, executableX, inputfileX, infoX = xnode
        pattern = infoX['pattern']
        update_method_name(infoX['node'], pattern)

# The idea is to first collect and register all nodes by their names.
# Next, we sample N of these, and use the pattern of matches
# (Todo: Do we simply use the pattern of compatibility or the pattern
# of left to right replaceability -- that is, a is replaceable with b
# but b is not replaceable with a is 10 while full compatibility would
# be 11 -> 1)
def generalize_method_trees(jtrees, log=False):
    my_trees = []
    for i,j in enumerate(jtrees):
        tree = util.to_modifiable(j['tree']) # The tree ds.
        executable = j['original']
        inputfile = j['arg']
        print("progress: %s %d/%d" % (inputfile, i, len(jtrees)) ,file=sys.stderr, flush=True)
        # we skip START
        node_name, children, *rest = tree
        assert node_name == '<START>'
        for child in children:
            collect_nodes(tree, tree, executable, inputfile)
        my_trees.append({'tree':tree, 'original': executable, 'arg': inputfile})

    for i,k in enumerate(NODE_REGISTER):
        print("compat: %s %d/%d" % (k, i, len(NODE_REGISTER)),file=sys.stderr, flush=True)
        identify_compatibility_patterns(k) # XTODO: switch to identify_buckets

    # finally, update the original names.
    for i,k in enumerate(NODE_REGISTER):
        print("update: %s %d/%d" % (k, i, len(NODE_REGISTER)),file=sys.stderr, flush=True)
        if k == '<START>': continue
        update_original_method_names(k)
    return my_trees

def usage():
    print('''
generalizemethod.py <trees json>
        Given the json file containing the extracted parse trees from the set of inputs
        generalize the method names using active labelling.
            ''')
    sys.exit(0)

def main(args):
    if not args or args[0] == '-h': usage()
    tracefile = args[0]
    with open(tracefile) as f:
        mined_trees = json.load(f)
    gmethod_trees = generalize_method_trees(mined_trees)
    print(json.dumps(gmethod_trees, indent=4))

if __name__ == '__main__':
    main(sys.argv[1:])
