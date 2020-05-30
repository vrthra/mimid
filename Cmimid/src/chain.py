import string
import json
import enum
import sys
import os.path

import config
import chainutils

import random
random.seed(config.RandomSeed)
import numpy as np
np.random.seed(config.RandomSeed)


import pudb
brk = pudb.set_trace

COMPARE_OPERATORS = {'==': lambda x, y: x == y}

class EState(enum.Enum):
    Trim = enum.auto()
    Append = enum.auto()
    Unknown = enum.auto()

class Prefix:
    def __init__(self):
        pass

    def __repr__(self):
        return repr(self.my_arg)

    def solve(self, prefix, my_traces, seen):
        raise NotImplemnted

    def continue_valid(self, prefix):
        raise NotImplemnted

class Search(Prefix):

    def continue_valid(self, prefix):
        if  random.uniform(0,1) > config.Return_Probability:
            return [prefix + random.choice(config.All_Characters)]
        return []

    def parsing_state(self, h, limit_len):
        # If the any goes beyond the current official input, then it
        # is reasonable to assume that an EOF check was made.
        if h.x == limit_len:
            return EState.Append
        # We could ideally assume that anything else is a trim, since we no longer
        # need to detect EOF.
        return EState.Trim

    def comparisons_at(self, x, cmp_traces):
        return [(i,t) for i,t in enumerate(cmp_traces) if x == t.x]

    def get_previous_fixes(self, end, sprefix, seen):
        similar = [i for i in seen
                       if sprefix[:end] in i and len(i) > len(sprefix[:end])]
        return [i[end] for i in similar]

class DeepSearch(Search):

    def extract_solutions(self, elt, lst_solutions, flip=False):
        original = elt.op_B
        fn = COMPARE_OPERATORS[elt.op]
        result = fn(elt.op_A, elt.op_B)
        myfn = fn if not flip else lambda a, b: not fn(a, b)
        fres = lambda x: x if result else not x
        return [c for c in lst_solutions if fres(myfn(c, original))]

    def get_lst_solutions_at_divergence(self, cmp_stack, v):
        # if we dont get a solution by inverting the last comparison, go one
        # step back and try inverting it again.
        stack_size = len(cmp_stack)
        while v < stack_size:
            # now, we need to skip everything till v. That is, our cmp_stack
            # is in reversed form. So, we want to diverge at the end of a
            # chain starting from index at -1.
            assert cmp_stack[-1] is cmp_stack[v:][-1]
            diverge, *satisfy = cmp_stack[v:]
            lst_solutions = config.All_Characters
            for i,elt in reversed(satisfy):
                lst_solutions = self.extract_solutions(elt, lst_solutions, False)

            # now we need to diverge here
            i, elt = diverge
            lst_solutions = self.extract_solutions(elt, lst_solutions, True)
            if lst_solutions:
                return lst_solutions
            v += 1
        return []

    def get_corrections(self, cmp_stack, constraints):
        """
        cmp_stack contains a set of comparions, with the last comparison made
        at the top of the stack, and first at the bottom. Choose a point
        somewhere and generate a character that conforms to everything until
        then.
        """
        if not cmp_stack:
            return [[l] for l in config.All_Characters if constraints(l)]

        stack_size = len(cmp_stack)
        lst_positions = list(range(stack_size-1,-1,-1))
        solutions = []

        for point_of_divergence in lst_positions:
            lst_solutions = self.get_lst_solutions_at_divergence(cmp_stack,
                    point_of_divergence)
            lst = [l for l in lst_solutions if constraints(l)]
            if lst:
                solutions.append(lst)
        return solutions

    def solve(self, arg_prefix, traces, seen):
        # we are assuming a character by character comparison.
        # so get the comparison with the last element.
        while traces:
            h, *ltrace = traces
            end =  h.x
            k = self.parsing_state(h, limit_len=len(arg_prefix))
            new_prefix = arg_prefix[:end]
            fixes = self.get_previous_fixes(end, arg_prefix, seen)
            kind = None

            if k == EState.Trim:
                # A character comparison of the *last* char.
                # This was a character comparison. So collect all
                # comparisons made using this character. until the
                # first comparison that was made otherwise.
                # Now, try to fix the last failure
                cmp_stack = self.comparisons_at(h.x, traces)
                # Now, try to fix the last failure
                corr = self.get_corrections(cmp_stack, lambda i: i not in fixes)
                if not corr: raise Exception('Exhausted attempts: %s' % fixes)
                chars = sorted(set(sum(corr, [])))
                kind = EState.Trim

            elif k == EState.Append:
                assert new_prefix == arg_prefix
                chars = config.All_Characters
                kind = EState.Append
            else:
                assert k == EState.Unknown
                # Unknown what exactly happened. Strip the last and try again
                traces = ltrace
                continue

            return kind, ["%s%s" % (new_prefix, new_char) for new_char in chars]

        return []

class Chain:

    def __init__(self, executable, learner):
        self.learner = learner
        self.executable = executable
        self.reset()
        self.solver = DeepSearch()
        if not os.path.exists('./build/metadata'):
            chainutils.compile_src(self.executable)

    def reset(self):
        self._my_arg = None
        self.seen = set()
        self.starting_fn = '<start>'
        self.last_fn = self.starting_fn
        self.traces = []
        return self.last_fn

    def prune(self, solutions):
        # never retry an argument.
        return [s for s in solutions if s not in self.seen]

    def choose(self, solutions):
        return [random.choice(self.prune(solutions))]

    def get_comparisons(self):
        return chainutils.get_comparisons()

    def execute(self, my_input):
        return chainutils.execute(self.executable, my_input)


    def evaluate(self, arg):
        self.current_prefix = arg

        print(">", repr(self.current_prefix), "(%s: %d %s %d)" % (
            self.learner.cur_state,
            self.learner.env.last_stack_len,
            self.learner.env.e, self.learner.env.i), end="\r")
        done, v = self.execute(self.current_prefix)
        if done:
            print(">",repr(self.current_prefix))
            return None, [self.starting_fn], self.starting_fn, True, []

        self.seen.add(self.current_prefix)
        self.traces = self.get_comparisons()
        sol_kind, new_solutions = self.solver.solve(self.current_prefix, list(reversed(self.traces)), self.seen)
        # new_state is the function seen in last comparison

        close_idx = len(self.current_prefix)
        true_trace = [i for i in self.traces if i.x < close_idx]
        if not true_trace:
            brk()
        state = "%s@%d" %(true_trace[-1].stack[-1],true_trace[-1].id)
        #state = true_trace[-1].stack[-1]
        return sol_kind, true_trace[-1].stack, state, False, self.prune(new_solutions)

class Env:
    def __init__(self, chain):
        self.chain = chain
        self.prefix = ''
        self.kind = EState.Append
        self.solutions = []
        self.last_stack_len = 0
        self.e = '_'
        self.i = 0

        # TODO: how to deal with blacklist
        # We need to create a different Q table with only blacklisted and associated characters which
        # together is considered a state.
        # We will use this table if we detect that a blacklisted state is entered, and update the table
        # with the reward.
        # If necessary, we can trim our prefix one extra character to make sure that the blacklist table
        # gets the opportunity to predict the next char.

        # REQUIRED: The basic blocks per method so that we can produce a Q table with methodname + blockid
        # as the state. Note that in a pinch, Cmimid instrumentation can provide a more coarse grained
        # identifier (not as fine as the basic block but not as coarse as the function name alone)
        self.blacklist = set()

    def reset(self):
        self.prefix = ''
        self.kind = EState.Append
        self.solutions = []
        self.last_stack_len = 0
        return self.chain.reset()

    def step(self, action, cur_state):
        if self.kind == EState.Append:
            self.prefix = self.prefix + action
        else:
            self.prefix = self.prefix[0:-1] + action
        kind, stack, state, done, solutions = self.chain.evaluate(self.prefix)
        self.solutions = solutions
        # what should the next state be?
        # if solutions given is prefix + ... then we have an append
        if done:
            self.last_stack_len = len(stack)
            return stack, stack[-1], 100, True
        else:
            self.kind = kind
            reward = -1
            if kind == EState.Trim:
                next_state = cur_state
                reward = -10 # * len(stack)
            elif kind == EState.Append:
                next_state = state #stack[-1]
                if len(stack)  == self.last_stack_len:
                    if next_state == cur_state:
                        reward = -10
                    else:
                        reward = -10
                elif len(stack) < self.last_stack_len:
                    reward = 10
                else:
                    reward = -10
            else:
                assert False
            self.last_stack_len = len(stack)

            #if next_state != self.chain.starting_fn:
            #    if kind == EState.Append and next_state not in stack:
            #        brk()

            return stack, next_state, reward, False


class Learner: pass
class QLearner(Learner):
    def __init__(self, program, qarr=None):
        self.program = program
        self.actions = config.All_Characters
        starting_state = '<start>'
        self.cur_state = starting_state
        self.env = Env(Chain(program, self))
        self.states = [starting_state] + chainutils.get_functions()
        #self.action_reward = {}
        self.action_chars = {}

        self.alpha = 0.5 # learning rate
        self.gamma = 0.90 # discount factor -- 0.8 - 0.99
        self.epsilon_init = 1.0 # explore/exploit factor
        self.epsilon = self.epsilon_init
        self.epsilon_min = 0.001
        self.epsilon_decay = 0.999
        self.qarrf = 'Q.json'
        if os.path.exists(self.qarrf):
            with open(self.qarrf) as f:
                self.Q = json.load(fp=f)
        else:
            self.Q = {'_': {a:0 for a in self.actions}}

    def update_epsilon(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon = (100.0 - len(self.env.prefix))/100.0
        else:
            self.epsilon = self.epsilon_min
        #    self.epsilon *= self.epsilon_decay


    def sidx(self, state):
        return next(i for i,a in enumerate(self.states) if a == state)

    def aidx(self, action):
        return next(i for i,a in enumerate(self.actions) if a == action)

    def update_Q(self, state, action, new_state, reward):
        if state not in self.Q: self.Q[state] = dict(self.Q['_'])
        if new_state not in self.Q: self.Q[new_state] = dict(self.Q['_'])

        self.Q[state][action] = ((1 - self.alpha) * self.Q[state][action]) + \
                self.alpha * (reward + self.gamma * max(self.Q[new_state].values()))
        return True

    def randargmax(self, hm, actions):
        items = [(k,v) for k,v in hm.items() if k in actions]
        max_val = max([v for k,v in items])
        return random.choice([k for k,v in items if v == max_val])

    def printS_(self, s, f):
        print(s, file=f)
        for a in self.actions:
            print("%s:%0.4f" % (repr(a)[1:-1], self.Q[s][a]), end=',', file=f)
        print('',file=f)

    def printS(self, s=None):
        if s is None:
            s = self.cur_state
        with open('Qs.debug', 'w+') as f:
            self.printS_(s, f)

    def printQ(self):
        with open('Q.debug', 'w+') as f:
            for s in self.states: self.printS_(s, f)

    def next_action(self):
        if not self.env.solutions:
            self.env.e = 'r'
            return random.choice(config.All_Characters)
        chars = [c[-1] for c in self.env.solutions] if self.env.solutions else config.All_Characters
        if self.cur_state in self.env.blacklist:
            self.env.e = 'B(....)'
            return random.choice(chars)
        elif random.uniform(0,1) < self.epsilon:
            self.env.e = 'R(%s)' % self.epsilon
            return random.choice(chars)
        else:
            self.env.e = '^(%s)' % self.epsilon
            maxval = max(self.Q[self.cur_state].values())
            if maxval == 0:
                self.env.e = '.(%s)' % self.epsilon
            act = self.randargmax(self.Q[self.cur_state], chars)
            return act

    def learn(self, episodes):
        # start over each time.
        self.cur_state = self.env.reset()
        done = False

        for _ in range(episodes):
            self.epsilon = self.epsilon_init
            self.cur_state = self.env.reset()
            for i in range(config.MaxIter):
                self.env.i = i
                chainutils.check_debug()
                self.printS()
                action = self.next_action()
                last_stack, next_state, reward, done = self.env.step(action, self.cur_state)

                # We can only trust appends
                if self.env.kind == EState.Append:
                    prefix_checked_chars = [i.op_B for i in self.env.chain.traces if i.stack == last_stack] # TODO; shold we filter close_char

                    str_prefix = ''.join(prefix_checked_chars)
                    key = next_state #self.cur_state
                    if key not in self.action_chars:
                        self.action_chars[key] = str_prefix

                    old_prefix = self.action_chars[key]
                    if key != self.env.chain.starting_fn:
                        if len(str_prefix) > len(old_prefix):
                            # we need a way to handle loops.
                            if not set(old_prefix).issubset(set(str_prefix)):
                                self.env.blacklist.add(key)
                                #if not key in {'json_is_literal', 'has_char'}:
                                #    brk()
                                #    print()
                            self.action_chars[key] = str_prefix
                        else:
                            if not set(str_prefix).issubset(set(old_prefix)):
                                self.env.blacklist.add(key)
                                #if not key in {'json_is_literal', 'has_char'}:
                                #    brk()
                                #    print()
                    #print("> ", key, repr(self.action_chars[key]))

                self.update_Q(self.cur_state, action, next_state, reward)
                self.cur_state = next_state
                if done:
                    break
                self.update_epsilon()
            with open('Q.json', 'w+') as f:
                json.dump(self.Q, fp=f)

def main(program, *rest):
    learner = QLearner(program)
    learner.learn(100)

main(*sys.argv[1:])
