import sys

CURRENT_METHOD = None
METHOD_NUM_STACK = []
METHOD_MAP = {}
METHOD_NUM = 0

def get_current_method():
    return CURRENT_METHOD

def set_current_method(method, stack_depth, mid):
    global CURRENT_METHOD
    CURRENT_METHOD = (method, stack_depth, mid)
    return CURRENT_METHOD

def trace_init():
    global CURRENT_METHOD
    global METHOD_NUM_STACK
    global METHOD_MAP
    global METHOD_NUM
    CURRENT_METHOD = None
    METHOD_NUM_STACK.clear()
    METHOD_MAP.clear()
    METHOD_NUM = 0

    start = (METHOD_NUM, None, [])
    METHOD_NUM_STACK.append(start)
    METHOD_MAP[METHOD_NUM] = start

def trace_call(method):
    global CURRENT_METHOD
    global METHOD_NUM_STACK
    global METHOD_MAP
    global METHOD_NUM
    METHOD_NUM += 1

    # create our method invocation
    # method_num, method_name, children
    n = (METHOD_NUM, method, [])
    METHOD_MAP[METHOD_NUM] = n
    # add ourselves as one of the children to the previous method invocation
    METHOD_NUM_STACK[-1][2].append(n)
    # and set us as the current method.
    METHOD_NUM_STACK.append(n)

def trace_return():
    METHOD_NUM_STACK.pop()

def trace_set_method(method):
    cm = None
    if CURRENT_METHOD is not None:
        cm = CURRENT_METHOD[0]
    set_current_method(method, len(METHOD_NUM_STACK), METHOD_NUM_STACK[-1][0])
    return cm

def convert_comparisons(comparisons, inputstr):
    light_comparisons = []
    for idx, (method, stack_depth, mid) in comparisons:
        if idx is None: continue
        light_comparisons.append((idx, inputstr[idx], mid))
    return light_comparisons

def convert_method_map(method_map):
    light_map = {}
    for k in method_map:
        method_num, method_name, children = method_map[k]
        light_map[k] = (k, method_name, [c[0] for c in children])
    return light_map

