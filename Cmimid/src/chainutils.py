import subprocess
import json
import os
import os.path
import config
import pudb
brk = pudb.set_trace

def compile_src(executable):
    with open('build/exec_file', 'w+') as f:
        print('''
pfuzzer=../taints
cp examples/*.h ./build
cp -r build/* $pfuzzer/build
cp examples/%(program)s.c $pfuzzer/build
(
cd ../taints;
./install/bin/trace-instr build/%(program)s.c ./samples/excluded_functions 2>err >out
)
# generate metadata
echo | $pfuzzer/build/%(program)s.c.instrumented
cp $pfuzzer/build/metadata build/
''' % {'program':executable}, file=f)
    do(["bash", "./build/exec_file"], shell=False, input='')

def strsearch(Y, x):
    comparisons = []
    N = len(Y)
    n = len(x)
    i = 0
    while i+n <= N:
        found=True
        j = 0
        while found and j < n:
            comparisons.append((Y[i+j], x[j], i+j, j))
            if (Y[i+j] == x[j]):
                found = True
            else:
                found = False
            j += 1
        if found:
            return comparisons
        i +=1
    return comparisons

class O:
    def __init__(self, **keys): self.__dict__.update(keys)
    def __repr__(self): return str(self.__dict__)

def do(command, env=None, shell=False, log=False,input=None, **args):
    result = subprocess.Popen(command,
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        shell=shell
    )
    stdout, stderr = result.communicate(timeout=config.TIMEOUT, input=input.encode('ascii'))
    return O(returncode=result.returncode, stdout=stdout, stderr=stderr)

def check_debug():
    if os.path.exists('/tmp/.debug'):
        os.remove('/tmp/.debug')
        brk()

def execute(executable, my_input):
    # first write the input in taints build
    with open('../taints/build/%s.input' % executable, 'w+') as f:
        print(my_input, end='', file=f)
    with open('build/exec_file', 'w+') as f:
        print('''
exec ../taints/build/%(program)s.c.uninstrumented < ../taints/build/%(program)s.input
''' % {'program':executable}, file=f)
    result1 = do(["bash", "./build/exec_file"], shell=False, input=my_input)
    if result1.returncode == 0:
        return (True, result1)

    # try to identify if we have an EOF
    with open('build/exec_file', 'w+') as f:
        print('''
../taints/build/%(program)s.c.instrumented < ../taints/build/%(program)s.input
gzip -c output > build/output.gz
exec ../taints/install/bin/trace-taint -me build/metadata -po build/pygmalion.json -t build/output.gz
''' % {'program':executable}, file=f)

    with open('../taints/build/%s.input' % executable, 'w+') as f:
        print(my_input + config.eof_char, end='', file=f)
    result2 = do(["bash", "./build/exec_file"], shell=False, input=my_input)
    return (False, result2)


def get_comparisons():
    input_comparisons = []
    with open('build/pygmalion.json') as pg:
        lines = pg.readlines()
    for sline in lines:
        if sline.startswith('#'): continue
        line = json.loads(sline)
        if line['type'] == 'INPUT_COMPARISON':
            if 'strip_input' in line['stack']: continue
            if line['operator'] in {'tokenstore', 'tokencomp', 'eof'}:
                continue
            if line['operator'] == 'switch':
                assert len(line['index']) == 1
                for k in line['operand']:
                    input_comparisons.append(O(**{
                        'x': line['index'][0], 'op': '==', 'op_B': k, 'op_A': line['value'], 'stack': line['stack'], 'id': line['id']
                        }))
            elif line['operator'] == '==':
                assert len(line['index']) == 1
                input_comparisons.append(
                        O(**{
                            'x': line['index'][0], 'op': line['operator'], 'op_B':line['operand'][0], 'op_A': line['value'], 'stack': line['stack'], 'id': line['id']
                                }))
            elif line['operator'] == 'conversion':
                continue
            elif line['operator'] == 'strcmp':
                # the index indicates which items in the input were touched.
                # so for strcmp, length of index array corresponds to the length
                # of operand
                Bchars = line['operand'][0]
                Achars = line['value']
                idxs = line['index']
                assert len(idxs) <= len(Bchars)

                # now, for each element in the index array, there is a corresponding
                # element of operand
                for i,k in enumerate(idxs):
                    op_B = Bchars[i]
                    if i >= len(line['value']): break
                    op_A = Achars[i]
                    input_comparisons.append(O(**{
                        'x': k, 'op': '==', 'op_B': op_B, 'op_A': op_A, 'stack': line['stack'], 'id': line['id']
                        }))
                    if op_A != op_B: break

            elif line['operator'] == 'strsearch':
                # the index indicates which items in the input were touched.
                # so for strcmp, length of index array corresponds to the length
                # of operand
                Bchars = line['operand'][0]
                Achars = line['value']
                idxs = line['index']
                comparisons = strsearch(Achars, Bchars)
                for (y, x, i_j, j) in comparisons:
                    op_A, op_B = y, x
                    k = idxs[i_j]
                    #assert chain.sys_arg()[k] + config.eof_char == op_A
                    input_comparisons.append(O(**{
                        'x': k, 'op': '==', 'op_B': op_B, 'op_A': op_A, 'stack': line['stack'], 'id': line['id']
                        }))

            else:
                assert False
    #for i in input_comparisons:
    #    if i.x >= len(chain.sys_arg()):
    #        continue
    #    assert chain.sys_arg()[i.x] == i.op_A
    return input_comparisons


def get_functions():
    functions = []
    with open('build/metadata') as f:
        lines = f.readlines()
    for sline in lines:
        line = json.loads(sline)
        if not 'f' in line: continue
        functions.append(line['f'])
    return functions

