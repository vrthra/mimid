# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Jonathan M. Lange <jml@mumak.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Library for formatting trees."""

import itertools


class Options(object):

    def __init__(self,
                 FORK=u'\u251c',
                 LAST=u'\u2514',
                 VERTICAL=u'\u2502',
                 HORIZONTAL=u'\u2500',
                 NEWLINE=u'\u23ce'):
        self.FORK = FORK
        self.LAST = LAST
        self.VERTICAL = VERTICAL
        self.HORIZONTAL = HORIZONTAL
        self.NEWLINE = NEWLINE


ASCII_OPTIONS = Options(FORK=u'|',
                        LAST=u'+',
                        VERTICAL=u'|',
                        HORIZONTAL=u'-',
                        NEWLINE=u'\n')

class Colors:

    CBLACK  = '\33[30m'
    CRED    = '\33[31m'
    CGREEN  = '\33[32m'
    CYELLOW = '\33[33m'
    CBLUE   = '\33[34m'
    CVIOLET = '\33[35m'
    CBEIGE  = '\33[36m'
    CWHITE  = '\33[37m'

    CBLACKBG  = '\33[40m'
    CREDBG    = '\33[41m'
    CGREENBG  = '\33[42m'
    CYELLOWBG = '\33[43m'
    CBLUEBG   = '\33[44m'
    CVIOLETBG = '\33[45m'
    CBEIGEBG  = '\33[46m'
    CWHITEBG  = '\33[47m'

    CGREY    = '\33[90m'
    CRED2    = '\33[91m'
    CGREEN2  = '\33[92m'
    CYELLOW2 = '\33[93m'
    CBLUE2   = '\33[94m'
    CVIOLET2 = '\33[95m'
    CBEIGE2  = '\33[96m'
    CWHITE2  = '\33[97m'

    CGREYBG    = '\33[100m'
    CREDBG2    = '\33[101m'
    CGREENBG2  = '\33[102m'
    CYELLOWBG2 = '\33[103m'
    CBLUEBG2   = '\33[104m'
    CVIOLETBG2 = '\33[105m'
    CBEIGEBG2  = '\33[106m'
    CWHITEBG2  = '\33[107m'

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'

def _format_newlines(prefix, formatted_node, options):
    """
    Convert newlines into U+23EC characters, followed by an actual newline and
    then a tree prefix so as to position the remaining text under the previous
    line.
    """
    replacement = u''.join([
        options.NEWLINE,
        u'\n',
        prefix])
    return formatted_node.replace(u'\n', replacement)


def _format_tree(node, format_node, get_children, options, prefix=u''):
    children = list(get_children(node))
    next_prefix = u''.join([prefix, options.VERTICAL, u'   '])
    for child in children[:-1]:
        yield u''.join([prefix,
                        options.FORK,
                        options.HORIZONTAL,
                        options.HORIZONTAL,
                        u' ',
                        _format_newlines(next_prefix,
                                         format_node(child),
                                         options)])
        for result in _format_tree(child,
                                   format_node,
                                   get_children,
                                   options,
                                   next_prefix):
            yield result
    if children:
        last_prefix = u''.join([prefix, u'    '])
        yield u''.join([prefix,
                        options.LAST,
                        options.HORIZONTAL,
                        options.HORIZONTAL,
                        u' ',
                        _format_newlines(last_prefix,
                                         format_node(children[-1]),
                                         options)])
        for result in _format_tree(children[-1],
                                   format_node,
                                   get_children,
                                   options,
                                   last_prefix):
            yield result


def format_tree(node, format_node, get_children, options=None):
    lines = itertools.chain(
        [format_node(node)],
        _format_tree(node, format_node, get_children, options or Options()),
        [u''],
    )
    return u'\n'.join(lines)


def format_ascii_tree(tree, format_node, get_children):
    """ Formats the tree using only ascii characters """
    return format_tree(tree,
                       format_node,
                       get_children,
                       ASCII_OPTIONS)


def print_tree(*args, **kwargs):
    print(format_ascii_tree(*args, **kwargs))

def hilight_leaf(x):
    if x[1]:
        return repr(x[0].encode())
    else:
        #return Colors.CRED + repr(x[0].encode('utf-8')) + Colors.ENDC
        return repr(x[0].encode('utf-8'))

def tree_to_str(node):
    name, children, *rest = node
    if not children:
        return name
    return ''.join(tree_to_str(c) for c in children)

def usage():
    print('''
ftree.py <json file> <tree numbers>*
    Display the selected trees from <json file>
    if <tree numbers> is empty, all trees are shown if not, only selected trees are shown
    ''')
    sys.exit(0)

def main(args):
    if not args or args[0] == '-h': usage()
    import json
    jsonfn = args[0]
    with open(jsonfn) as f:
        jsont = json.load(f)
    if isinstance(jsont, dict):
        jsont = [jsont]
    trees = range(len(jsont))
    if len(args) > 1:
        trees = [int(v) for v in args[1:]]
    for tree in trees:
        print(jsont[tree]['arg'], repr(tree_to_str(jsont[tree]['tree'])))
        print_tree(jsont[tree]['tree'], format_node=hilight_leaf, get_children=lambda x: x[1])

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
