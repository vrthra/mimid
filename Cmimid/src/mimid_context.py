import taints
import util
import sys

indent = 0
def log(i, var, line):
    global indent
    if i > 0:
        indent += i
    s = '-->' if i > 0 else '<--'
    print('|', ' ' * indent,s, var, "\t\t", line, file=sys.stderr)
    if i < 0:
        indent += i

class method__:
    def __init__(self, name, args):
        self.name = util.encode_method_name(name, args)
        self.method_name = self.name
        taints.trace_call(self.name)

    def __repr__(self): return self.name

    def __enter__(self, line):
        self._old_name = taints.trace_set_method(self.name)
        log(1, self.name, line)
        self.stack = []
        return self

    def __exit__(self, line, *args):
        taints.trace_return()
        taints.trace_set_method(self._old_name)
        log(-1, self.name, line)

class stack__:
    def __init__(self, name, num, method_i, can_empty):
        self.stack = method_i.stack
        self.method_name = method_i.method_name
        self.can_empty = can_empty # * means yes. + means no, ? means to be determined
        self.name, self.num = name, num

    def __repr__(self): return self.name

    def __enter__(self, line):
        if self.name in {'while', 'for'}:
            self.stack.append(0)
        elif self.name in {'if', 'switch'}:
            self.stack.append(-1)
        else:
            assert False
        return self

    def __exit__(self, *args):
        self.stack.pop()

import json
class scope__:
    def __init__(self, alt, stack_i):
        self.name, self.num, self.method_name, self.alt = stack_i.name, stack_i.num, stack_i.method_name, alt
        self.stack = stack_i.stack
        self.method_name = stack_i.method_name
        self.can_empty = stack_i.can_empty

    def __repr__(self): return self.name

    def __enter__(self, line):
        if self.name in {'while', 'for'}:
            self.stack[-1] += 1
        elif self.name in {'if', 'switch'}:
            pass
        else:
            assert False, self.name
        encoded_name = util.encode_name(self.method_name, self.name, self.num, self.alt, self.can_empty, self.stack)
        taints.trace_call(encoded_name)
        self._old_name = taints.trace_set_method(self.name)
        log(1, self.name + ' ' + str(self.num) + ' ' + str(self.alt), line)
        return self

    def __exit__(self, line, *args):
        log(-1, self.name, line)
        taints.trace_return()
        taints.trace_set_method(self._old_name)
