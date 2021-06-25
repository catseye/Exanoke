#!/usr/bin/env python

# Exanoke reference interpreter
# ... implemented in a Questionable Manner

from optparse import OptionParser
import sys


class AST(object):
    def __init__(self, type, children=[], value=None, index=0, formals=[]):
        self.type = type
        self.value = value
        self.index = index
        self.formals = formals
        self.children = []
        for child in children:
            self.add_child(child)

    def add_child(self, item):
        assert isinstance(item, AST)
        self.children.append(item)

    def __repr__(self):
        if self.value is None:
            return 'AST(%r,%r)' % (self.type, self.children)
        if not self.children:
            return 'AST(%r,value=%r)' % (self.type, self.value)
        return 'AST(%r,%r,value=%r)' % (self.type, self.children, self.value)


class Scanner(object):
    def __init__(self, text):
        self.text = text
        self.token = None
        self.type = None
        self.scan()

    def scan_single_char(self, chars, type):
        text = self.text
        token = ''

        if len(text) == 0:
            return False
        for char in chars:
            if text.startswith(char):
                token += char
                text = text[1:]
                break
        if token:
            self.text = text
            self.token = token
            self.type = type
            return True
        else:
            return False

    def scan_multi_char(self, chars, type):
        text = self.text
        token = ''
        while True:
            if len(text) == 0:
                return False
            found = False
            for char in chars:
                if text.startswith(char):
                    token += char
                    text = text[1:]
                    found = True
                    break
            if not found:
                if token:
                    self.text = text
                    self.token = token
                    self.type = type
                    return True
                else:
                    return False

    def scan_atom(self):
        text = self.text
        token = ''
        if len(text) == 0:
            return False
        if text.startswith(':'):
            token += ':'
            text = text[1:]
        else:
            return False
        while len(text) != 0 and text[0].isalpha():
            token += text[0]
            text = text[1:]
        self.text = text
        self.token = token
        self.type = 'atom'
        return True

    def scan_smallifier(self):
        text = self.text
        token = ''
        if len(text) == 0:
            return False
        if text.startswith('<'):
            token += '<'
            text = text[1:]
        else:
            return False
        while len(text) != 0 and text[0].isalpha():
            token += text[0]
            text = text[1:]
        self.text = text
        self.token = token
        self.type = 'smallifier'
        return True

    def scan_identifier(self):
        text = self.text
        token = ''
        if len(text) == 0:
            return False
        while len(text) != 0 and (text[0].isalpha() or text[0] == '?'):
            token += text[0]
            text = text[1:]
        if not token:
            return False
        self.text = text
        self.token = token
        self.type = 'identifier'
        return True

    def scan(self):
        self.scan_multi_char(' \t\r\n', 'whitespace')
        if not self.text:
            self.token = None
            self.type = 'EOF'
            return
        if self.scan_single_char('(),#', 'goose egg'):
            return
        if self.scan_atom():
            return
        if self.scan_identifier():
            return
        if self.scan_smallifier():
            return
        self.token = self.text[0]
        self.text = self.text[1:]
        self.type = 'unknown character'

    def expect(self, token):
        if self.token == token:
            self.scan()
        else:
            raise SyntaxError("Expected '%s', but found '%s'" %
                              (token, self.token))

    def expect_type(self, type):
        self.check_type(type)
        self.scan()

    def on(self, token):
        return self.token == token

    def on_type(self, type):
        return self.type == type

    def check_type(self, type):
        if not self.type == type:
            raise SyntaxError("Expected %s, but found %s ('%s')" %
                              (type, self.type, self.token))

    def consume(self, token):
        if self.token == token:
            self.scan()
            return True
        else:
            return False


class Parser(object):
    def __init__(self, text):
        self.scanner = Scanner(text)
        self.defining = None
        self.defined = {}
        self.formals = None

    def program(self):
        fundefs = []
        while self.scanner.on('def'):
            fundefs.append(self.fundef())
        self.defining = None
        expr = self.expr()
        return AST('Program', [expr] + fundefs)

    def ident(self):
        self.scanner.check_type('identifier')
        name = self.scanner.token
        self.scanner.scan()
        return name

    def fundef(self):
        self.scanner.expect('def')
        name = self.ident()
        if name in self.defined:
            raise SyntaxError('Function "%s" already defined' % name)
        args = []
        self.scanner.expect('(')
        self.scanner.expect('#')
        self.formals = {}
        i = 1
        while self.scanner.consume(','):
            ident = self.ident()
            args.append(ident)
            self.formals[ident] = i
            i += 1
        self.scanner.expect(')')
        self.defining = name
        self.self_arity = len(args) + 1
        expr = self.expr()
        self.defining = None
        self.formals = None
        self.defined[name] = len(args) + 1
        return AST('FunDef', [expr], formals=args, value=name)

    def expr(self):
        if self.scanner.consume("cons"):
            self.scanner.expect("(")
            e1 = self.expr()
            self.scanner.expect(",")
            e2 = self.expr()
            self.scanner.expect(")")
            return AST('Cons', [e1, e2])
        elif self.scanner.consume("head"):
            self.scanner.expect("(")
            e1 = self.expr()
            self.scanner.expect(")")
            return AST('Head', [e1])
        elif self.scanner.consume("tail"):
            self.scanner.expect("(")
            e1 = self.expr()
            self.scanner.expect(")")
            return AST('Tail', [e1])
        elif self.scanner.consume("if"):
            e1 = self.expr()
            self.scanner.expect("then")
            e2 = self.expr()
            self.scanner.expect("else")
            e3 = self.expr()
            return AST('If', [e1, e2, e3])
        elif self.scanner.consume("self"):
            if self.defining is None:
                raise SyntaxError('Use of "self" outside of a function body')
            args = []
            self.scanner.expect("(")
            e1 = self.smaller()
            args.append(e1)
            while self.scanner.consume(','):
                args.append(self.expr())
            if len(args) != self.self_arity:
                raise SyntaxError('Arity mismatch on self (expected %d, got %d)' %
                    (self.self_arity, len(args)))
            self.scanner.expect(")")
            return AST('Call', args, value=self.defining)
        elif self.scanner.consume("eq?"):
            self.scanner.expect("(")
            e1 = self.expr()
            self.scanner.expect(",")
            e2 = self.expr()
            self.scanner.expect(")")
            return AST('Eq?', [e1, e2])
        elif self.scanner.consume("cons?"):
            self.scanner.expect("(")
            e1 = self.expr()
            self.scanner.expect(")")
            return AST('Cons?', [e1])
        elif self.scanner.consume("not"):
            self.scanner.expect("(")
            e1 = self.expr()
            self.scanner.expect(")")
            return AST('Not', [e1])
        elif self.scanner.consume("#"):
            if self.defining is None:
                raise SyntaxError('Use of "#" outside of a function body')
            return AST('ArgRef', index=0)
        elif self.scanner.on_type("atom"):
            atom = self.scanner.token
            self.scanner.scan()
            return AST('Atom', value=atom)
        elif self.scanner.on_type("identifier"):
            ident = self.scanner.token
            self.scanner.scan()
            if self.scanner.on('('):
                self.scanner.expect('(')
                if ident not in self.defined:
                    raise SyntaxError('Undefined function "%s"' % ident)
                args = [self.expr()]
                while self.scanner.consume(','):
                    args.append(self.expr())
                if len(args) != self.defined[ident]:
                    raise SyntaxError('Arity mismatch (expected %d, got %d)' %
                        (self.defined[ident], len(args)))
                self.scanner.expect(')')
                return AST('Call', args, value=ident)
            else:
                if self.defining is None:
                    raise SyntaxError('Reference to argument "%s" '
                                      'outside of a function body' % ident)
                if ident not in self.formals:
                    raise SyntaxError('Undefined argument "%s"' % ident)
                return AST('ArgRef', index=self.formals[ident])
        else:
            return self.smaller()

    def smaller(self):
        if self.scanner.consume("<head"):
            e1 = self.smallerterm()
            return AST('Head', [e1])
        elif self.scanner.consume("<tail"):
            e1 = self.smallerterm()
            return AST('Tail', [e1])
        elif self.scanner.consume("<if"):
            e1 = self.expr()
            self.scanner.expect("then")
            e2 = self.smallerterm()
            self.scanner.expect("else")
            e3 = self.smallerterm()
            return AST('If', [e1, e2, e3])
        else:
            raise SyntaxError('Expected <smaller>, found "%s"' %
                              self.scanner.token)

    def smallerterm(self):
        if self.scanner.consume("#"):
            return AST('ArgRef', index=0)
        else:
            return self.smaller()


### Runtime ###


class SExpr(object):
    def __repr__(self):
        return "SExpr()"


class Atom(SExpr):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return "Atom('%s')" % self.text

    def __eq__(self, other):
        return isinstance(other, Atom) and self.text == other.text


class Cons(SExpr):
    def __init__(self, head, tail):
        self.head = head
        self.tail = tail

    def __str__(self):
        return "(%s %s)" % (self.head, self.tail)

    def __repr__(self):
        return "Cons(%s, %s)" % (self.head.__repr__(), self.tail.__repr__())

    def __eq__(self, other):
        return False  # isinstance(other, Cons) and self.head == other.head and self.tail == other.tail


class FunDef(object):
    def __init__(self, expr, args):
        self.expr = expr
        self.args = args


TRUE = Atom(':true')
FALSE = Atom(':false')


class Evaluator(object):
    def __init__(self, ast):
        self.fundefs = {}
        for fundef in ast.children[1:]:
            self.fundefs[fundef.value] = FunDef(
                fundef.children[0], fundef.children[1:]
            )
        self.bindings = []

    def eval(self, ast):
        if ast.type == 'Atom':
            return Atom(ast.value)
        elif ast.type == 'Cons':
            v1 = self.eval(ast.children[0])
            v2 = self.eval(ast.children[1])
            return Cons(v1, v2)
        elif ast.type == 'Head':
            v1 = self.eval(ast.children[0])
            if not isinstance(v1, Cons):
                raise TypeError("head: Not a cons cell")
            return v1.head
        elif ast.type == 'Tail':
            v1 = self.eval(ast.children[0])
            try:
                return v1.tail
            except AttributeError:
                raise TypeError("tail: Not a cons cell")
        elif ast.type == 'If':
            v1 = self.eval(ast.children[0])
            if v1 == TRUE:
                return self.eval(ast.children[1])
            else:
                return self.eval(ast.children[2])
        elif ast.type == 'Eq?':
            v1 = self.eval(ast.children[0])
            v2 = self.eval(ast.children[1])
            if v1 == v2:
                return TRUE
            else:
                return FALSE
        elif ast.type == 'Cons?':
            v1 = self.eval(ast.children[0])
            if isinstance(v1, Cons):
                return TRUE
            else:
                return FALSE
        elif ast.type == 'Not':
            v1 = self.eval(ast.children[0])
            if v1 == TRUE:
                return FALSE
            else:
                return TRUE
        elif ast.type == 'Call':
            fundef = self.fundefs[ast.value]
            bindings = self.bindings
            self.bindings = [self.eval(expr) for expr in ast.children]
            result = self.eval(fundef.expr)
            self.bindings = bindings
            return result
        elif ast.type == 'ArgRef':
            return self.bindings[ast.index]
        elif ast.type == 'Program':
            return self.eval(ast.children[0])
        else:
            raise NotImplementedError("%s" % ast)


def main(argv):
    optparser = OptionParser(__doc__)
    optparser.add_option("-a", "--show-ast",
                         action="store_true", dest="show_ast", default=False,
                         help="show parsed AST instead of evaluating")
    (options, args) = optparser.parse_args(argv[1:])
    with open(args[0], 'r') as f:
        text = f.read()
    p = Parser(text)
    try:
        prog = p.program()
    except SyntaxError as e:
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        sys.exit(1)
    if options.show_ast:
        from pprint import pprint
        pprint(prog)
        sys.exit(0)
    try:
        ev = Evaluator(prog)
        print(str(ev.eval(prog)))
    except TypeError as e:
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
