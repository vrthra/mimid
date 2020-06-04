#!/usr/bin/env python
import sys
import os
import glob
import json
import pudb
bp = pudb.set_trace

import mimid_context
import taints

CMIMID_METHOD=0
CMIMID_EXIT=1
CMIMID_BREAK=2
CMIMID_CONTINUE=3
CMIMID_FOR=4
CMIMID_WHILE=5
CMIMID_IF=6
CMIMID_SWITCH=7
CMIMID_RETURN=8
CMIMID_DO=9
CMIMID_GOTO=10
CMIMID_LABEL=11

CMIMID_VALUE_UNKNOWN=0
CMIMID_TYPE_UNKNOWN=1000
CMIMID_TYPE_INT=1001
CMIMID_TYPE_CHAR=1002



kind_map={CMIMID_FOR:'for', CMIMID_WHILE:'while', CMIMID_IF:'if', CMIMID_SWITCH:'switch'}

class O:
    def __init__(self, **keys): self.__dict__.update(keys)
    def __repr__(self): return str(self.__dict__)

def read_json(json_file):
    json_arr = []
    with open(json_file) as f:
        arr =  f.readlines()
    for i,a in enumerate(arr):
        if a.startswith('#'):
            continue
        json_arr.append(json.loads(a))
    return json_arr

cmimid_stack =  []
pseudo_method_stack = []
non_empty_methods = set()
popped_stack = []

def to_key(method, name, num): return '%s:%s_%s' % (method, name, num)

method_specialization = []
line = None

def track_stack(e, gen_events):
    global method_specialization, line
    line = int(e.info[0])
    if e.fun in {'cmimid__method_arg'}:
        _line, _ith, typ, val = e.info
        if int(typ) == CMIMID_TYPE_CHAR:
            method_specialization.append(chr(int(val)))
        elif int(typ) == CMIMID_TYPE_INT:
            method_specialization.append(int(val))
        else:
            # ignore unknowns
            pass

    elif e.fun in {'cmimid__method_enter'}:
        mname = METHOD_PREFIX[-1]
        cmimid_stack.append(('method', mname, line))
        gen_events.append((line, ('method_enter', mname, method_specialization)))
        method_specialization = []

    elif e.fun in {'cmimid__method_exit'}:
        x = cmimid_stack.pop()
        popped_stack.append(x)
        method, mname, line = x
        assert method == 'method'
        gen_events.append((line, ('method_exit', mname)))

    elif e.fun in {'cmimid__stack_enter'}:
        _line, stack_kind, stack_id, *_args = [int(i) for i in e.info]
        str_skind = kind_map[stack_kind]

        key = to_key(METHOD_PREFIX[-1], str_skind, stack_id)

        pseudo_method_stack.append(key)
        cmimid_stack.append(('stack', stack_id, str_skind, line))
        gen_events.append((line, ('stack_enter', str_skind, stack_id)))

    elif e.fun in {'cmimid__stack_exit'}:
        x = cmimid_stack.pop()
        popped_stack.append(x)
        stack, stack_id, str_skind, line = x
        assert stack == 'stack'
        gen_events.append((line,('stack_exit', stack_id)))
        pseudo_method_stack.pop()

    elif e.fun in {'cmimid__scope_enter'}:
        _line, scope_alt, is_default_or_else, *args = [int(i) for i in e.info]
        if is_default_or_else == '1':
            non_empty_methods.add(pseudo_method_stack[-1])
        cmimid_stack.append(('scope', scope_alt, args, line))
        gen_events.append((line, ('scope_enter', scope_alt)))

    elif e.fun in {'cmimid__scope_exit'}:
        x = cmimid_stack.pop()
        popped_stack.append(x)
        scope, scope_alt, args, line = x
        assert scope == 'scope'
        gen_events.append((line, ('scope_exit', scope_alt)))


    elif e.fun in {'cmimid__return'}:
        # For return, unwind all until the method.
        assert cmimid_stack
        while True:
            t = cmimid_stack.pop()
            popped_stack.append(t)
            if t[0] == 'method':
                method, mid, line = t
                gen_events.append((line, ('method_exit', mid)))
                # stop unwinding
                break
            elif t[0] == 'stack':
                stack, stack_id, stack_kind, line = t
                gen_events.append((line, ('stack_exit', stack_id)))
            elif t[0] == 'scope':
                scope, scope_kind, args, line = t
                gen_events.append((line, ('scope_exit', scope_kind)))

    elif e.fun in {'cmimid__break'}:
        # break is a little return. Unwind until the next
        # stack that is a loop.
        assert cmimid_stack
        while True:
            t = cmimid_stack.pop()
            popped_stack.append(t)
            if t[0] == 'method':
                # this should never happen.
                assert False
            elif t[0] == 'stack':
                stack, stack_id, str_skind, line = t
                gen_events.append((line, ('stack_exit', stack_id)))
                if str_skind in {'for', 'while', 'switch'}:
                    # this should not happen.
                    assert False
            elif t[0] == 'scope':
                scope, scope_kind, args, line = t
                gen_events.append((line, ('scope_exit', scope_kind)))
                stack, stack_id, str_skind, line = cmimid_stack[-1]
                if str_skind in {'for', 'while', 'switch'}:
                    # stop unwinding. The stack would get popped next.
                    break
    elif e.fun in {'cmimid__continue'}:
        # continue is a little break. Unwind until the next
        # scope that is scope of a loop.
        assert cmimid_stack
        while True:
            t = cmimid_stack.pop()
            popped_stack.append(t)
            if t[0] == 'method':
                # this should never happen.
                assert False
            elif t[0] == 'stack':
                stack, stack_id, str_skind, line = t
                # we should exit before the first _loop_ or _switch_
                # which is the parent for _continue_
                assert str_skind not in {'for', 'while', 'switch'}
                gen_events.append((line, ('stack_exit', stack_id)))
            elif t[0] == 'scope':
                scope, scope_kind, args, line = t
                gen_events.append((line, ('scope_exit', scope_kind)))
                stack, stack_id, skind, line = cmimid_stack[-1]
                if skind in {'for', 'while', 'switch'}:
                    # stop unwinding
                    break
    else:
        # TODO need goto
        assert False

def track_comparison(e, inputstring, gen_events):
    # {'type': 'INPUT_COMPARISON', 'index': [3],
    # 'length': 4, 'value': '\n',
    # 'operator': 'strcmp',
    # 'operand': ['\n'],
    # 'id': 1, 'stack': ['_real_program_main']}
    indexes = [int(i) for i in e['index']]
    #for i in indexes:
    #    assert i < len(inputstring)
    for i in indexes:
        # we need only the accessed indexes
        # some of the access may go up to the last null byte
        if i < len(inputstring):
            gen_events.append(('_', ('comparison', i, inputstring)))
        else:
            assert i == len(inputstring)

def show_nested(gen_events):
    indent = 0
    for e in gen_events:
        if '_enter' in e[0]:
            print("|\t" * indent, e)
            indent += 1
        elif '_exit' in e[0]:
            indent -= 1
            print("|\t" * indent, e)
def fire_events(gen_events, inputstring, event_dir, ifile):
    comparisons = []
    taints.trace_init()
    method = []
    for line, e in gen_events:
        if 'method_enter' == e[0]:
            _, mname, args = e
            method.append(mimid_context.method__(name=mname, args=args))
            method[-1].__enter__(line)
        elif 'method_exit' == e[0]:
            method[-1].__exit__(line)
            x = method.pop()
            assert x.method_name.startswith(e[1])

        elif 'stack_enter' == e[0]:
            stack, str_skind, stack_id = e

            can_empty = '?'
            if e[1] in {'while', 'for'}:
                can_empty = '?'
            elif e[1] in {'switch', 'if'}:
                # first need to check if the switch has default an if has else
                key = to_key(method[-1].method_name, str_skind, stack_id)
                if key in non_empty_methods:
                    can_empty = '=' # has default
                else:
                    can_empty = '-' # no default
            _, name, num = e
            method.append(mimid_context.stack__(name=name, num=num, method_i=method[-1], can_empty=can_empty))
            method[-1].__enter__(line)
        elif 'stack_exit' == e[0]:
            method[-1].__exit__(line)
            method.pop()

        elif 'scope_enter' == e[0]:
            method.append(mimid_context.scope__(alt=e[1], stack_i=method[-1]))
            method[-1].__enter__(line)

        elif 'scope_exit' == e[0]:
            method[-1].__exit__(line)
            method.pop()

        elif 'comparison' == e[0]:
            idx = e[1]
            method_, stackdepth_, mid = taints.get_current_method()
            comparisons.append((idx, inputstring[idx], mid))
            print(repr(inputstring[idx]), '-' * mimid_context.indent, mid, file=sys.stderr)


    j = { 'comparisons_fmt': 'idx, char, method_call_id',
          'comparisons':comparisons,
                'method_map_fmt': 'method_call_id, method_name, children',
                'method_map': taints.convert_method_map(taints.METHOD_MAP),
                'inputstr': inputstring,
                'original': '%s.x' % (event_dir), # the original -- non instrumented exec
                'arg': ifile # the file name of input str
                }
    return j


METHOD_PREFIX = None
NOIGNORE_OPS = {'tokencomp'}
def process_events(events, inputstring, event_dir, ifile):
    global METHOD_PREFIX
    gen_events = []

    assert not cmimid_stack
    for i,e in enumerate(events):
        if e['type'] == 'CMIMID_EVENT':
            track_stack(O(**e), gen_events)
        elif e['type'] == 'INPUT_COMPARISON':
            if e['operator'] not in NOIGNORE_OPS:
                continue
            track_comparison(e, inputstring, gen_events)
        #elif e['type'] == 'CMIMID_ACCESS':
        #    if e['fun'] == 'load':
        #        track_comparison(e, inputstring, gen_events)
        #    elif e['fun'] == 'mem_access':
        #        track_comparison(e, inputstring, gen_events)
        elif e['type'] == 'STACK_EVENT':
            # this only gets us the top level methods
            # i.e no pseudo methods.
            METHOD_PREFIX = e['stack']

            pass
    assert not cmimid_stack
    return fire_events(gen_events, inputstring, event_dir, ifile)

def usage():
    print("""
tokenevents.py <subject dir>
    Extract the buffer accesses from traces.
    <subject dir> The directory that corresponds to each subject.  Each input <subject>.input.<n>
                  will have a <subject>.input.<n>.json file associated with it within the subject dir.
    The output is a JSON string that has the pygmalion events converted to cmimid events with control
    flow information associated with the comparisons. The tokens are specifically identified and
    their access convert to mimid events.
    """)
    sys.exit(0)

def main(args):
    if not args or args[0] == '-h': usage()
    event_dir = args[0]
    returns = []
    lst = [event_dir]
    if os.path.isdir(event_dir):
        if event_dir.endswith('/'):
            event_dir = event_dir[0:-1]
        lst = glob.glob("%s/*.json" % event_dir)
    for arg in lst:
        ifile = arg.replace('.json', '')
        with open(ifile, mode='r+b') as f:
            inputstr = f.read().decode()
        max_len = len(inputstr)
        assert max_len == os.path.getsize(ifile)

        events = read_json(arg)
        ret = process_events(events, inputstr, event_dir, ifile)
        returns.append(ret)
    print(json.dumps(returns))

if __name__ == '__main__':
    main(sys.argv[1:])
