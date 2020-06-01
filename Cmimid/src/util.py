import urllib.parse
import copy
import os
import random
import json
import subprocess
import grammartools as G
#from fuzzingbook.GrammarFuzzer import tree_to_string
import hashlib
PARSE_SUCCEEDED = 10
MAX_SAMPLES = 100
MAX_PROC_SAMPLES = 100

Epsilon = '-'
NoEpsilon = '='

def hashit(s, n=3):
    return hashlib.md5(s.encode()).hexdigest()[0:n]

def tree_to_str_r(tree):
    assert False
    #return tree_to_string(tree)

class O:
    def __init__(self, **keys): self.__dict__.update(keys)
    def __repr__(self): return str(self.__dict__)

def init_log(prefix, var, module):
    with open('%s.log' % module, 'a+') as f:
        print(prefix, ':==============',var, file=f)

def do(command, env=None, shell=False, log=False, inputv=None, timeout=PARSE_SUCCEEDED, **args):
    result = None
    if inputv:
        result = subprocess.Popen(command,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            shell = shell,
            env=dict(os.environ, **({} if env is None else env))
        )
        result.stdin.write(inputv)
        stdout, stderr = result.communicate(timeout=timeout)
    else:
        result = subprocess.Popen(command,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            shell = shell,
            env=dict(os.environ, **({} if env is None else env))
        )
        stdout, stderr = result.communicate(timeout=timeout)
    if log:
        with open('build/do.log', 'a+') as f:
            print(json.dumps({'cmd':command, 'env':env, 'exitcode':result.returncode}), env, flush=True, file=f)
    if stdout is None: stdout = b''
    if stderr is None: stderr = b''
    result.kill()
    return O(returncode=result.returncode, stdout=stdout, stderr=stderr)

def tree_to_str(tree):
    expanded = []
    to_expand = [tree]
    while to_expand:
        (key, children, *rest), *to_expand = to_expand
        if G.is_nt(key):
            #assert children # not necessary
            to_expand = children + to_expand
        else:
            assert not children
            expanded.append(key)
    return ''.join(expanded)

def tree_to_pstr(tree, op_='', _cl=''):
    expanded = []
    to_expand = [tree]
    while to_expand:
        (key, children), *to_expand = to_expand
        if G.is_nt(key):
            expanded.append(op_)
            to_expand = children + [(_cl, [])] + to_expand
        else:
            assert not children
            expanded.append(key)
    return ''.join(expanded)

def tree_to_pstr_r(tree, op_='', _cl=''):
    symbol, children, *_ = tree
    if children:
        return "%s%s%s" % (op_, ''.join(tree_to_pstr_r(c, op_, _cl) for c in children), _cl)
    else:
        # TODO: assert symbol is terminal
        # TODO: check if we need to parenthesize this too. We probably
        # need this if the terminal symbols are more than one char wide.
        #return "%s%s" % (op_, _cl)
        return "%s%s%s" % (op_, symbol, _cl)

EXEC_MAP = {}

def check_lowcost(o, x, e, ut, module, sa1, sa2):
    s = tree_to_str(ut)
    if s in EXEC_MAP: return EXEC_MAP[s]
    tn = "%s_test.csv" % module
    with open(tn, 'w+') as f: print(s, file=f, end='')
    result = do([module, tn])
    with open('%s.log' % module, 'a+') as f:
        print('------------------', file=f)
        print('original:', repr(o), file=f)
        print('updated:', repr(s), file=f)
        print('Checking:',e, file=f)
        print('1:', repr(sa1), file=f)
        print('2:', repr(sa2), file=f)
        print(' '.join([module, repr(s)]), file=f)
        print(":=", result.returncode, file=f)
        print("\n", file=f)
    v = (result.returncode == 0)
    EXEC_MAP[s] = v
    return v

def check_accurate(o, x, e, ut, module, sa1, sa2):
    assert module.endswith('.x')
    module = module[0:-2] + '.c'
    s = tree_to_str(ut)
    if s in EXEC_MAP: return EXEC_MAP[s]
    updated_ps = tree_to_pstr(ut, op_='{', _cl='}')
    tn = "%s_test.csv" % module
    with open(tn, 'w+') as f: print(s, file=f, end='')

    trace_out = do(["./bin/parsed_out.sh",tn, module] ).stdout.decode('UTF-8', 'ignore')
    val = None
    v = False
    parsed_ps = None
    try:
        parsed_ps = trace_out.strip()
        v = (parsed_ps == updated_ps)
    except:
        parsed_ps = 'ERROR'
        v = False

    with open('%s.log' % module, 'a+') as f:
        print('------------------', file=f)
        print(' '.join(["python3", "build/%s" % module, s]), file=f)
        print('Checking:',e, file=f)
        print('original:', repr(o), file=f)
        print('tmpl:', repr(x), file=f)
        print('updated:', repr(s), file=f)
        print('XXXX:', repr(sa1), file=f)
        print('REPL:', repr(sa2), file=f)
        print('ops:', repr(updated_ps), file=f)
        print('pps:', repr(parsed_ps), file=f)
        print(":=", v, file=f)
    #     print(' '.join([module, repr(s)]), file=f)
    #     print("\n", file=f)
    # v = (result.returncode == 0)
    EXEC_MAP[s] = v
    return v

ACCURATE_BUT_COSTLY = False

if ACCURATE_BUT_COSTLY:
    check = check_accurate
else:
    check = check_lowcost

def to_modifiable(derivation_tree):
    node, children, *rest = derivation_tree
    return [node, [to_modifiable(c) for c in children], *rest]


def node_include(i, j):
    name_i, children_i, s_i, e_i = i
    name_j, children_j, s_j, e_j = j
    return s_i <= s_j and e_i >= e_j

def get_ref(node, node_name):
    stack = [node]
    while stack:
        my_node, *stack = stack
        name, children, *rest = my_node
        if name == node_name:
            return my_node
        else:
            stack = children + stack
    return None

def copy_rec(tree):
    filled_tree = []
    to_fill = [(tree, filled_tree)]
    while to_fill:
        (node, filled_node), *to_fill = to_fill
        name, children, *rest = node
        if not children:
            new_node = [name, [], *rest]
            filled_node.extend(new_node)
        else:
            child_nodes = [[] for c in children]
            new_node = [name, child_nodes]
            filled_node.extend(new_node)
            to_fill = [(c, child_nodes[i]) for i,c in enumerate(children)] + to_fill
    return filled_tree

# replace the given node in a2 by the node in a1
def replace_nodes(a2, a1):
    node2, _, t2 = a2
    node1, _, t1 = a1
    str2_old = tree_to_str(t2)

    # first change the name of the node, then copy the tree.
    tmpl_name = '___cmimid___'
    old_name = node2[0]
    node2[0] = tmpl_name

    #vstr = str(t2)
    #v = json.dumps(t2)
    #t2_new = json.loads(v)
    t2_new = copy_rec(t2)
    node2[0] = old_name

    # now find the reference to tmpl_name in t2_new
    node2 = get_ref(t2_new, tmpl_name)
    node2.clear()
    for n in node1:
        node2.append(n)
    str2_new = tree_to_str(t2_new)
    assert str2_old != str2_new
    return t2_new

def is_compatible(a1, a2, module):
    t1 = is_a_replaceable_with_b(a1, a2, module)
    if not t1: return False
    t2 = is_a_replaceable_with_b(a2, a1, module)
    return t2

def is_a_replaceable_with_b(a1, a2, module):
    n1, f1, t1 = a1
    n2, f2, t2 = a2
    if tree_to_str(n1) == tree_to_str(n2): return True
    t_x = replace_nodes(a1, (('XXXX', []), None, a2))
    x = tree_to_str(t_x)
    updated_tree = replace_nodes(a1, a2)
    updated_string = tree_to_str(updated_tree)
    o = tree_to_str(t1)
    v = check(o, x, n1[0], updated_tree, module, tree_to_str(a1[0]), tree_to_str(a2[0]))
    return v

def is_node_method(node):
    node_name = node[0]
    if (node_name[0], node_name[-1]) != ('<', '>'): return False
    return not is_node_pseudo(node)

def is_node_pseudo(node):
    node_name = node[0]
    if (node_name[0], node_name[-1]) != ('<', '>'): return False
    if ':if_' in node_name: return True
    if ':while_' in node_name: return True
    return False

def parse_pseudo_name(node_name):
    assert (node_name[0], node_name[-1]) == ('<','>')
    return decode_name(node_name[1:-1])

def decode_name(node_name_stack):
    node_name, mstack = node_name_stack.split('#')
    method_stack = json.loads(mstack)
    method_ctrl_alt_name, can_empty = node_name.split(' ')
    method, ctrl_cid_altid = method_ctrl_alt_name.split(':')
    ctrl, cid_altid = ctrl_cid_altid.split('_')
    assert ctrl in {'while', 'if'}
    cid, altid = cid_altid.split(',')

    if 'while' == ctrl:
        assert altid == '0'
    return method, ctrl, int(cid), altid, can_empty, method_stack

def unparse_pseudo_name(method, ctrl, ctrl_id, alt_num, can_empty, cstack):
    return "<%s>" % encode_name(method, ctrl, ctrl_id, alt_num, can_empty, cstack)

def encode_name(method, ctrl, ctrl_id, alt_num, can_empty, stack):
    assert ctrl in {'while', 'if'}
    return '%s:%s_%s,%s %s#%s' % (method, ctrl, ctrl_id, alt_num, can_empty, json.dumps(stack))

def encode_method_name(name, my_args):
    # trick to convert args that are not of type str for later.
    #if args and hasattr(args[0], 'tag'):
    #    self.name = "%s:%s" % (args[0].tag, self.name)

    if not my_args:
        return name
    else:
        return "%s(%s)" % (name, urllib.parse.quote('_'.join([str(i) for i in my_args])))

def parse_method_name(mname):
    assert (mname[0], mname[-1]) == ('<', '>')
    name = mname[1:-1]
    if '.' in name:
        nname, my_id = name.split('.')
        return nname, my_id
    else:
        return name, '0'

def unparse_method_name(mname, my_id):
    return '<%s.%s>' % (mname, my_id)


def sample(elts, pop_len):
    if len(elts) < pop_len:
        pop_len = len(elts)
    if pop_len == -1:
        return elts
    return random.sample(elts, pop_len)
