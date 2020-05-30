import sys
from clang.cindex import Index, Config, CursorKind, TokenKind
import os

# Notes: We need both STACK_EXIT and SCOPE_EXIT because
# Break causes both STACK and SCOPE exits while
# Continue only causes SCOPE exit.

# Notes: We need to sanitize C because our parser is
# essentially held together with duct tape
# 1. No macros -- translate all macros to expansions
# 2. No enums -- enums with case statements fail
# 3. Absolutely no C++ comments
# 4. Put braces around individual case statements in a switch
# 5. Braces initialization of struct members does not work as expected in many places
# 6. Defaults in switch should not contain breaks.
# 7. Really no macros, even for things like isdigit or strncmp
# 8. No labels. If labels are necessary, remember to ensure processing on statement.

LIBCLANG_PATH = os.environ['LIBCLANG_PATH']
Config.set_library_file(LIBCLANG_PATH)

CURRENT_STACK = [(0, '0')]

counter = 0;
def get_id():
    global counter
    counter += 1
    return counter

def compound_body_with_cb(node, alt):
    #assert node.extent.start.line != node.extent.end.line
    salt = str(alt)
    rep = ""
    if node.kind == CursorKind.COMPOUND_STMT:
        src = to_string(node)
        assert (src[0], src[-1]) == ('{', '}')
        assert (src[1], src[-2]) == ('\n', '\n')
        rep = src[2:-2]
    else:
        rep = to_string(node)
        if rep[-1] != "}" and rep[-1] != "\n" and rep[-1] != ";":
            rep += " ;"

    return '''\
{
cmimid__scope_enter(__LINE__, %s, %s);
%s
cmimid__scope_exit(__LINE__, CMIMID_EXIT);
}''' % (salt, '0' if alt == 0 else '1 /*else*/', rep)


class AstNode:
    def __init__(self, node):
        self.node = node


    def check_children_not_macro(self):
        for c in self.node.get_children():
            if c.extent.start.line != c.extent.end.line:
                continue
            if c.extent.start.column != c.extent.end.column:
                continue
            if c.kind == CursorKind.CASE_STMT: # I have no idea why I dont get this.
                continue
            raise Exception("We do not know how to handle macros in code")

    def to_src(self):
        src = ''.join(SRC[self.node.extent.begin_int_data-2:self.node.extent.end_int_data-2])
        if self.node.extent.start.line == self.node.extent.end.line:
            lines = [SRC[self.node.extent.start.line-1]]
            lines[0] = lines[0][self.node.extent.start.column-1:self.node.extent.end.column-1]
        else:
            lines = SRC[self.node.extent.start.line-1: self.node.extent.end.line] # last line not included
            lines[0] = lines[0][self.node.extent.start.column-1:]
            lines[-1] = lines[-1][:self.node.extent.end.column-1]
        return ''.join(lines)

    def __repr__(self):
        return " ".join([t.spelling for t in self.node.get_tokens()])

class SpellingNode(AstNode):
    def __repr__(self): return self.node.spelling

class SrcNode(AstNode):
    def __repr__(self):
        s = self.to_src()
        if not s: bp()
        return s

class StmtNode(AstNode):
    def __repr__(self): return "%s;" % super().__repr__()



class EnumDecl(StmtNode): pass
class TypedefDecl(StmtNode): pass
class IntegerLiteral(AstNode): pass
class StructDecl(StmtNode): pass
class VarDecl(StmtNode): pass
class UnionDecl(StmtNode): pass
class TypeDecl(StmtNode): pass

class CallExpr(SrcNode): pass
class ParenExpr(SrcNode): pass
class UnexposedExpr(SrcNode): pass
class DeclRefExpr(SrcNode): pass
class CharacterLiteral(SrcNode): pass
class CXXUnaryExpr(SrcNode): pass
class CStyleCastexpr(SrcNode): pass

class ParmDecl(AstNode): pass
class DeclStmt(AstNode): pass
class CompoundAssignmentOperator(AstNode): pass
class TypeRef(AstNode): pass
class UnaryOperator(AstNode): pass
class BinaryOperator(AstNode): pass
class DefaultStmt(AstNode): pass
class NullStmt(AstNode):
    def __repr__(self):
        return ';'

class ReturnStmt(AstNode):
    def __repr__(self):
        return '''\
cmimid__return(__LINE__, CMIMID_RETURN);
%s ;''' % super().__repr__()

class BreakStmt(AstNode):
    def __repr__(self):
        return '''\
cmimid__break(__LINE__, CMIMID_BREAK);
%s ;''' % super().__repr__()

class ContinueStmt(AstNode):
    def __repr__(self):
        return '''\
cmimid__continue(__LINE__, CMIMID_CONTINUE);
%s ;''' % super().__repr__()

class GotoStmt(AstNode):
    def __repr__(self):
        # it is not clear how exactly we should handle this.
        assert False
        return '''\
cmimid__goto(__LINE__, CMIMID_GOTO);
%s ;''' % super().__repr__()



def extent(node):
    return range(node.extent.start.line,node.extent.end.line+1)


class LabelStmt(AstNode):
    def __repr__(self):
        assert False
        return '''\
cmimid__label(__LINE__, CMIMID_LABEL, %s, %s);
%s ;''' % (CURRENT_STACK[-1][0], CURRENT_STACK[-1][1], super().__repr__())


class CaseStmt(AstNode):
    def __repr__(self):
       children = list(self.node.get_children())
       if len(children) == 2:
           label = to_string(children[0])
           body = compound_body_with_cb(children[1], label)
           return '''case %s: %s;''' % (label, body)
       src = []
       for child in children:
           c = to_string(child)
           src.append(c)
       return '\n'.join(src)


class ForStmt(AstNode):
    def __repr__(self):
        outer_range = extent(self.node)
        tokens = [t for t in self.node.get_tokens()]
        children = list(self.node.get_children()) # this is OK because of assert
        # now, ensure that all children are within the range.
        self.check_children_not_macro()

        body_child = children[-1]
        #assert body_child.kind is CursorKind.COMPOUND_STMT

        for_part_tokens = [t for t in tokens if
                t.extent.end_int_data <= body_child.extent.begin_int_data]
        for_part = ' '.join([t.spelling for t in for_part_tokens])

        c = get_id()
        assert len(CURRENT_STACK) > 0
        CURRENT_STACK.append(('CMIMID_FOR', c))
        body = compound_body_with_cb(children[-1], 0)
        CURRENT_STACK.pop()
        assert len(CURRENT_STACK) > 0
        return '''\
cmimid__stack_enter(__LINE__, CMIMID_FOR, %s);
%s %s
cmimid__stack_exit(__LINE__, CMIMID_EXIT);''' % (c, for_part, body)


class DoStmt(AstNode):
    def __repr__(self):
        outer_range = extent(self.node)
        children = list(self.node.get_children())
        self.check_children_not_macro()
        assert(len(children) == 2)

        cond = to_string(children[1])
        c = get_id()
        assert len(CURRENT_STACK) > 0
        CURRENT_STACK.append(('CMIMID_WHILE', c))
        body = compound_body_with_cb(children[0], 0)
        CURRENT_STACK.pop()
        assert len(CURRENT_STACK) > 0

        return '''\
cmimid__stack_enter(__LINE__, CMIMID_WHILE, %s);
do %s while (%s);
cmimid__stack_exit(__LINE__, CMIMID_EXIT);''' % (c, body, cond)


class WhileStmt(AstNode):
    def __repr__(self):
        outer_range = extent(self.node)
        children = list(self.node.get_children())
        self.check_children_not_macro()
        assert(len(children) == 2)

        cond = to_string(children[0])
        c = get_id()
        assert len(CURRENT_STACK) > 0
        CURRENT_STACK.append(('CMIMID_WHILE', c))
        body = compound_body_with_cb(children[1], 0)
        CURRENT_STACK.pop()
        assert len(CURRENT_STACK) > 0

        return '''\
cmimid__stack_enter(__LINE__, CMIMID_WHILE, %s);
while (%s) %s
cmimid__stack_exit(__LINE__, CMIMID_EXIT);''' % (c, cond, body)


class IfStmt(AstNode):
    def __init__(self, node, with_cb=True, my_id=0):
        super().__init__(node)
        self.with_cb = with_cb
        self.my_id = my_id

    def __repr__(self):
        c = get_id()
        cond =  ""
        if_body = ""
        else_body = ""

        for i, child in enumerate(self.node.get_children()):
            if i == 0:   # if condition
                cond = "%s" % to_string(child)
            elif i == 1: # if body
                assert len(CURRENT_STACK) > 0
                CURRENT_STACK.append(('CMIMID_IF', c))
                if_body = compound_body_with_cb(child, self.my_id)
                CURRENT_STACK.pop()
                assert len(CURRENT_STACK) > 0
            elif i == 2: # else body (exists if there is an else)
                if child.kind == CursorKind.IF_STMT:
                    # else if -> no before/after if callbacks
                    else_body = "%s" % repr(IfStmt(child, with_cb=False, my_id=self.my_id+1))
                else:
                    CURRENT_STACK.append(('CMIMID_IF', c))
                    else_body = compound_body_with_cb(child, self.my_id+1)
                    CURRENT_STACK.pop()
                    assert len(CURRENT_STACK) > 0

        block = "if ( %s ) %s" % (cond, if_body)
        if else_body != "":
            block += " else %s" % else_body

        if self.with_cb:
            return '''\
cmimid__stack_enter(__LINE__, CMIMID_IF, %s);
%s
cmimid__stack_exit(__LINE__, CMIMID_EXIT);''' % (c, block)

        return block


class SwitchStmt(AstNode):
    def __repr__(self):
        c = get_id()
        children = list(self.node.get_children())
        assert(len(children) == 2)
        assert(children[1].kind == CursorKind.COMPOUND_STMT)
        assert len(CURRENT_STACK) > 0
        CURRENT_STACK.append(('CMIMID_SWITCH', c))
        switch_expr = to_string(children[0])
        body = to_string(children[1])
        CURRENT_STACK.pop()
        assert len(CURRENT_STACK) > 0
        return '''\
cmimid__stack_enter(__LINE__, CMIMID_SWITCH, %s);
switch (%s) %s
cmimid__stack_exit(__LINE__, CMIMID_EXIT)''' % (c, switch_expr, body)


class CompoundStmt(AstNode):
    def __repr__(self):
        outer_range = extent(self.node)
        stmts = []
        children = list(self.node.get_children())
        self.check_children_not_macro()
        label = None
        ilabel = 0
        seen_default = False
        for i,child in enumerate(children):
            rep = to_string(child)
            if child.kind == CursorKind.LABEL_STMT:
                # what is the outer scope here? Hopefully it is
                # in CURRENT_STACK[-1]
                pass
            elif child.kind == CursorKind.CASE_STMT:
                assert not seen_default
                gchildren = list(child.get_children())
                label = to_string(gchildren[0])
                assert len(gchildren) == 2
                fall_through = [label]
                while(gchildren[1].kind == CursorKind.CASE_STMT):
                    # fall through. We do not count it as a separate option.
                    child = gchildren[1]
                    gchildren = list(child.get_children())
                    label = to_string(gchildren[0])
                    fall_through.append(label)
                    assert len(gchildren) == 2
                ilabel += 1
                body = to_string(gchildren[1])
                rep = '''\
%s
cmimid__scope_enter(__LINE__, %d, 0);
%s
''' % ("\n".join(["case %s:" % c for c in fall_through]), ilabel, body)

            elif child.kind == CursorKind.DEFAULT_STMT:
                seen_default = True
                gchildren = list(child.get_children())
                assert len(gchildren) == 1
                body = to_string(gchildren[0])
                ilabel += 1 # We dont expect any more after default
                rep = '''\
default:
cmimid__scope_enter(__LINE__, %d, 1/*default*/);
%s;
''' % (ilabel, body.strip())
            if not rep:
               print("REP:", child.kind, child.extent, file=sys.stderr)
               continue

            # handle missing semicolons
            if rep.strip()[-1] not in {'}', ';'}:
                rep += ";"

            stmts.append(rep)
        if seen_default:
            stmts.append("cmimid__scope_exit(__LINE__, CMIMID_EXIT/*case default*/);")

        body = "\n".join(stmts)
        return '''\
{
%s
}''' % body


class FunctionDecl(AstNode):
    def type_info(self, v, i):
        tres = CMIMID_TYPE_UNKNOWN
        res = str(CMIMID_VALUE_UNKNOWN) # we need an int to be passed.
        if v.type.spelling == 'char':
            tres = CMIMID_TYPE_CHAR
            res = v.spelling
        elif v.type.spelling == 'int':
            tres = CMIMID_TYPE_INT
            res = v.spelling
        else:
            tres = CMIMID_TYPE_UNKNOWN
            res = '0'
        return "cmimid__method_arg(__LINE__,%d, %s, %s)" % (i, tres, res)

    # method context wrapper
    def __repr__(self):
        children = list(self.node.get_children())
        return_type = self.node.result_type.spelling
        function_name = self.node.spelling
        c = get_id()
        cparams = [p for p in children if p.kind == CursorKind.PARM_DECL]
        params = ", ".join([to_string(c) for c in cparams])

        type_params = [self.type_info(v, i) for i,v in enumerate(cparams)]

        if '...' in self.node.type.spelling:
            params = params + ", ..."
        if self.node.is_definition():
            param_info = ';'.join(type_params) + ';'
        #if children and children[-1].kind == CursorKind.COMPOUND_STMT:
            body = to_string(children[-1])
            return '''\
%s
%s(%s) {
%s
cmimid__method_enter(__LINE__, %s);
%s
cmimid__method_exit(__LINE__);
}''' % (return_type, function_name, params, param_info, c, body)
        else:
            # function declaration.
            return '''\
%s
%s(%s);''' % (return_type, function_name, params)

import pudb
bp = pudb.set_trace

FN_HASH = {
        CursorKind.FUNCTION_DECL: FunctionDecl,
        CursorKind.PARM_DECL: ParmDecl,
        CursorKind.VAR_DECL: VarDecl,
        CursorKind.TYPEDEF_DECL: TypedefDecl,
        CursorKind.INTEGER_LITERAL: IntegerLiteral,
        CursorKind.COMPOUND_STMT: CompoundStmt,
        CursorKind.DECL_STMT: DeclStmt,
        CursorKind.DECL_REF_EXPR: DeclRefExpr,
        CursorKind.IF_STMT: IfStmt,
        CursorKind.SWITCH_STMT: SwitchStmt,
        CursorKind.CASE_STMT: CaseStmt,
        CursorKind.LABEL_STMT: LabelStmt,
        CursorKind.DEFAULT_STMT: DefaultStmt,
        CursorKind.NULL_STMT: NullStmt,
        CursorKind.FOR_STMT: ForStmt,
        CursorKind.WHILE_STMT: WhileStmt,
        CursorKind.DO_STMT: DoStmt,
        CursorKind.RETURN_STMT: ReturnStmt,
        CursorKind.BREAK_STMT: BreakStmt,
        CursorKind.CONTINUE_STMT: ContinueStmt,
        CursorKind.STRUCT_DECL: StructDecl,
        CursorKind.TYPEDEF_DECL: TypeDecl,
        CursorKind.ENUM_DECL: EnumDecl,
        CursorKind.UNION_DECL: UnionDecl,
        CursorKind.CALL_EXPR: CallExpr,
        CursorKind.BINARY_OPERATOR: BinaryOperator,
        CursorKind.UNARY_OPERATOR: UnaryOperator,
        CursorKind.CXX_UNARY_EXPR: CXXUnaryExpr,
        CursorKind.CSTYLE_CAST_EXPR: CStyleCastexpr,
        CursorKind.TYPE_REF: TypeRef,
        CursorKind.PAREN_EXPR: ParenExpr,
        CursorKind.COMPOUND_ASSIGNMENT_OPERATOR: CompoundAssignmentOperator,
        CursorKind.UNEXPOSED_EXPR: UnexposedExpr,
        CursorKind.CHARACTER_LITERAL: CharacterLiteral,
        CursorKind.GOTO_STMT: GotoStmt,
        }


def to_ast(node):
    if node.kind in FN_HASH:
        return FN_HASH[node.kind](node)
    else:
        print("ToAST:", node.kind, file=sys.stderr)
        assert False
        return AstNode(node)

STOPPED = False
def to_string(node):
    global STOPPED
    stp = os.environ.get('STOP')
    if stp is not None and not STOPPED:
        line = node.location.line
        if int(line) > int(stp):
            STOPPED = True

    v = to_ast(node)
    return repr(v)

# DEBUG
def traverse(node, level):
    print('%s %-35s %-20s %-10s [%-6s:%s - %-6s:%s] %s %s ' % (' ' * level,
    node.kind, node.spelling, node.type.spelling, node.extent.start.line, node.extent.start.column,
    node.extent.end.line, node.extent.end.column, node.location.file, node.mangled_name))
    if node.kind == clang.cindex.CursorKind.CALL_EXPR:
        for arg in node.get_arguments():
            print("ARG=%s %s" % (arg.kind, arg.spelling))

    for child in node.get_children():
        traverse(child, level+1)
# DEBUG

skipped = []
parsed_extent = []
SRC = []

def store(arg):
    with open(arg) as f:
        SRC.extend(f.readlines())

displayed_till = 0
def display_till(last):
    for i in range(displayed_till, last):
        print(SRC[i], end='')

CMIMID_TYPE_UNKNOWN=1000
CMIMID_VALUE_UNKNOWN=0
CMIMID_TYPE_INT=1001
CMIMID_TYPE_CHAR=1002

def parse(arg):
    global displayed_till
    idx = Index.create()
    CFLAGS = os.environ.get('CFLAGS', '') #'-xc++ std=c++14')
    translation_unit = idx.parse(arg, args =  CFLAGS.split(' '))
    # IMPORTANT: If you change values here, remember to change in src/events.py too
    print('''\
#define CMIMID_METHOD 0
#define CMIMID_EXIT 1
#define CMIMID_BREAK 2
#define CMIMID_CONTINUE 3
#define CMIMID_FOR 4
#define CMIMID_WHILE 5
#define CMIMID_IF 6
#define CMIMID_SWITCH 7
#define CMIMID_RETURN 8
#define CMIMID_DO 9
#define CMIMID_GOTO 10
#define CMIMID_LABEL 11

#define CMIMID_VALUE_UNKNOWN 0
#define CMIMID_TYPE_UNKNOWN 1000
#define CMIMID_TYPE_INT 1001
#define CMIMID_TYPE_CHAR 1002

void cmimid__line(int i, int l) {}

void cmimid__method_arg(int l, int i, int type, int val) {}

void cmimid__method_enter(int l, int i) {}
void cmimid__method_exit(int l) {}
void cmimid__stack_enter(int l, int i, int j) {}
void cmimid__stack_exit(int l, int i) {}
void cmimid__scope_enter(int l, int i, int j) {}
void cmimid__scope_exit(int l, int i) {}
void cmimid__break(int l, int i) {}
void cmimid__continue(int l, int i) {}
void cmimid__goto(int l, int i) {}
void cmimid__label(int l, int i, int j, int k) {}
void cmimid__return(int l, int i) {}

''')
    for i in translation_unit.cursor.get_children():
        if i.location.file.name == sys.argv[1]:
            display_till(i.extent.start.line-1)
            print(to_string(i), file=sys.stdout)
            displayed_till = i.extent.end.line
        else:
            pass
           #skipped.append(to_string(i))
    display_till(len(SRC))

store(sys.argv[1])
parse(sys.argv[1])
#for i in skipped:
#    print(repr(i), file=sys.stderr)
