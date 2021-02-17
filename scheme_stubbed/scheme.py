"""A Scheme interpreter and its read-eval-print loop."""
from __future__ import print_function  # Python 2 compatibility

import sys
import os

from scheme_builtins import *
from scheme_reader import *
from ucb import main, trace


##############
# Eval/Apply #
##############

def scheme_eval(expr, env, is_tail=False): # Optional third argument is ignored
    """Evaluate Scheme expression EXPR in environment ENV.

    >>> expr = read_line('(+ 2 2)')
    >>> expr
    Pair('+', Pair(2, Pair(2, nil)))
    >>> scheme_eval(expr, create_global_frame())
    4
    """
    # Created by Rui Gao
    if isinstance(expr, Pair):
        operator = scheme_eval(expr.first, env)
        if scheme_procedurep(operator):
            if isinstance(operator, MacroProcedure):
                return scheme_apply(operator, list(expr.rest), env)
            args = [scheme_eval(e, env) for e in expr.rest]
            if is_tail:
                if isinstance(operator, LambdaProcedure) and operator.recursive_call:
                    return ThunkProcedure(operator, args)
                else:
                    return scheme_apply(operator, args, env)
            else:
                return complete_apply(operator, args, env)
        elif scheme_special_formp(operator):
            return operator(expr.rest).eval(env, is_tail)
        else:
            raise SchemeError('Invalid operator: {}'.format(operator))
    elif isinstance(expr, str):
        if expr in special_forms:
            return special_forms[expr]
        return env.lookup(expr)
    elif isinstance(expr, ThunkProcedure) and not is_tail:
        return expr.apply([], env)
    return expr
    # End

def scheme_apply(procedure, args, env):
    """Apply Scheme PROCEDURE to argument values ARGS (a Scheme list) in
    environment ENV."""
    # Created by Rui Gao
    return procedure.apply(args, env)
    # End

################
# Environments #
################

class Frame(object):
    """An environment frame binds Scheme symbols to Scheme values."""

    def __init__(self, parent):
        """An empty frame with parent frame PARENT (which may be None)."""
        "Your Code Here"
        # Created by Rui Gao
        self.parent = parent
        self.bindings = {}
        # End

    def __repr__(self):
        if self.parent is None:
            return '<Global Frame>'
        s = sorted(['{0}: {1}'.format(k, v) for k, v in self.bindings.items()])
        return '<{{{0}}} -> {1}>'.format(', '.join(s), repr(self.parent))

    def define(self, symbol, value):
        """Define Scheme SYMBOL to have VALUE."""
        self.bindings[symbol] = value
        return symbol

    # Created by Rui Gao
    def lookup(self, symbol):
        """Lookup VALUE bound to Scheme SYMBOL in the environment starts with self."""
        if symbol in self.bindings:
            return self.bindings[symbol]
        elif self.parent:
            return self.parent.lookup(symbol)
        else:
            raise SchemeError("Undefined symbol: {}".format(symbol))
    # END

##############
# Procedures #
##############

class Procedure(object):
    """The supertype of all Scheme procedures."""

def scheme_procedurep(x):
    return isinstance(x, Procedure)

class BuiltinProcedure(Procedure):
    """A Scheme procedure defined as a Python function."""

    def __init__(self, fn, use_env=False, name='builtin'):
        self.name = name
        self.fn = fn
        self.use_env = use_env

    def __str__(self):
        return '#[{0}]'.format(self.name)

    def apply(self, args, env):
        """Apply SELF to ARGS in ENV, where ARGS is a Scheme list.

        >>> env = create_global_frame()
        >>> plus = env.bindings['+']
        >>> twos = Pair(2, Pair(2, nil))
        >>> plus.apply(twos, env)
        4
        """
        # Created by Rui Gao
        try:
            if (self.use_env):
                return self.fn(*args, env)
            else:
                return self.fn(*args)
        except TypeError as e:
            raise SchemeError(e)
        # END


class LambdaProcedure(Procedure):
    """A procedure defined by a lambda expression or a define form."""

    def __init__(self, formals, body, env):
        """A procedure with formal parameter list FORMALS (a Scheme list),
        whose body is the Scheme list BODY, and whose parent environment
        starts with Frame ENV."""
        self.formals = formals
        self.body = body
        self.env = env
        self.recursive_call = False

    # Created by Rui Gao
    def apply(self, args, env):
        if len(args) != len(self.formals):
            raise SchemeError('Incorrect arguments number: expected {} but got {}'.format(len(self.formals), len(args)))
        new_env = Frame(self.env)
        for formal, arg in zip(self.formals, args):
            new_env.define(formal, arg)
        self.recursive_call = True
        for expr in self.body[:-1]:
            scheme_eval(expr, new_env)
        tail = self.body[-1]
        result = scheme_eval(tail, new_env, True)
        self.recursive_call = False
        return result
    # END

    def __str__(self):
        return str(Pair('lambda', Pair(self.formals, self.body)))

    def __repr__(self):
        return 'LambdaProcedure({0}, {1}, {2})'.format(
            repr(self.formals), repr(self.body), repr(self.env))

def add_builtins(frame, funcs_and_names):
    """Enter bindings in FUNCS_AND_NAMES into FRAME, an environment frame,
    as built-in procedures. Each item in FUNCS_AND_NAMES has the form
    (NAME, PYTHON-FUNCTION, INTERNAL-NAME)."""
    for name, fn, proc_name in funcs_and_names:
        frame.define(name, BuiltinProcedure(fn, name=proc_name))

#################
# Special Forms #
#################

"""
How you implement special forms is up to you. We recommend you encapsulate the
logic for each special form separately somehow, which you can do here.
"""

# Created by Rui Gao
def scheme_boolean(value):
    if value is False:
        return False
    else:
        return True    

def scheme_eval_boolean(expr, env, is_tail=False):
    result = scheme_eval(expr, env, is_tail)
    return scheme_boolean(result)

class SpecialForm(object):
    """The supertype of all Scheme special forms."""

class DefineForm(SpecialForm):
    """A Scheme special form with a syntax of 
    (define <name> <expression>) or
    (define (<name> [param] ...) <body> ...)"""

    def __init__(self, tail):
        """convert (define (<name> [param] ...) <body> ...)
        to (define <name> (lambda ([param] ...) <body> ...))"""
        validate_form(tail, 2)
        self.name = tail.first
        self.expr = tail.rest.first
        if isinstance(tail.first, Pair):
            self.expr = Pair('lambda', Pair(tail.first.rest, tail.rest))
            self.name = self.name.first
        validate_formals(Pair(self.name, nil))

    def eval(self, env, _):
        """Evaluate <expression> and 
        binds the value to <name> in the current environment.
        <name> must be a valid Scheme symbol."""
        env.define(self.name, scheme_eval(self.expr, env))
        return self.name

class IfForm(SpecialForm):
    """A Scheme special form with a syntax of 
    (if <predicate> <consequent> [alternative])"""

    def __init__(self, tail):
        validate_form(tail, 2, 3)
        self.predicate  = tail.first
        self.consequent = tail.rest.first
        self.alternative = tail.rest.rest

    def eval(self, env, is_tail=False):
        """Evaluate predicate, and then,
        if true, the consequent is evaluated and returned. 
        Otherwise, the alternative, if it exists, is evaluated and returned."""
        if scheme_eval_boolean(self.predicate, env):
            return scheme_eval(self.consequent, env, is_tail)
        elif self.alternative is not nil:
            return scheme_eval(self.alternative.first, env, is_tail)

class CondForm(SpecialForm):
    """A Scheme special form with a syntax of
    (cond <clause> ...)
    Each clause may be of the following form:
    (<test> [expression] ...) or 
    (else [expression] ...) for the last clause."""

    def __init__(self, tail):
        """Convert the last clause of the form (if exists)
        (else [expression] ...) to
        (#t [expression] ...)"""
        validate_form(tail, 1)
        last_clause = tail[-1]
        if last_clause.first == 'else':
            last_clause.first = True
        self.clauses = tail
    
    def eval(self, env, is_tail=False):
        """Starts with the first clause, evaluate test.
        If true, evaluate the expressions in order, returning the last one.
        If there are none, return what test evaluated to instead.
        If test is false, proceed to the next clause.
        If there are no more clauses, the return value is undefined."""
        for clause in self.clauses:
            test, exprs = clause.first, clause.rest
            result = scheme_eval(test, env)
            if scheme_boolean(result):
                if exprs is not nil:
                    for expr in exprs[:-1]:
                        scheme_eval(expr, env)
                    result = scheme_eval(exprs[-1], env, is_tail)
                return result

class AndForm(SpecialForm):
    """A Scheme special form with a syntax of 
    (and [test] ...)"""

    def __init__(self, tail):
        self.tests = tail

    def eval(self, env, is_tail=False):
        """Evaluate the tests in order, returning the first false value.
        If no test is false, return the last test.
        If no arguments are provided, return #t."""
        if self.tests is nil:
            return True
        tests = self.tests
        while tests is not nil:
            result = scheme_eval(tests.first, env, is_tail and tests.rest is nil)
            if not scheme_boolean(result):
                return result
            tests = tests.rest
        return result

class OrForm(SpecialForm):
    """A Scheme special form with a syntax of 
    (or [test] ...)"""

    def __init__(self, tail):
        self.tests = tail

    def eval(self, env, is_tail=False):
        """Evaluate the tests in order, returning the first true value.
        If no test is true and there are no more tests left, return #f"""
        tests = self.tests
        while tests is not nil:
            result = scheme_eval(tests.first, env, is_tail and tests.rest is nil)
            if scheme_boolean(result):
                return result
            tests = tests.rest
        return False

class LetForm(SpecialForm):
    """A Scheme special form with a syntax of 
    (let ([binding] ...) <body> ...)
    Each binding is of the following form:
    (<name> <expression>)"""

    def __init__(self, tail):
        validate_form(tail, 2)
        self.binding = tail.first
        self.body = tail.rest

    def eval(self, env, is_tail=False):
        """First, the expression of each binding is evaluated in the current frame.
        Next, a new frame that extends the current environment is created and
        each name is bound to its corresponding evaluated expression in it.
        Finally the body expressions are evaluated in order,
        returning the evaluated last one."""
        new_env = Frame(env)
        for expr in self.binding:
            validate_form(expr, 2, 2)
            validate_formals(Pair(expr.first, nil))
            new_env.define(expr.first, scheme_eval(expr.rest.first, env))
        for expr in self.body[:-1]:
            scheme_eval(expr, new_env)
        return scheme_eval(self.body[-1], new_env, is_tail)

class BeginForm(SpecialForm):
    """A Scheme special form with a syntax of 
    (begin <expression> ...)"""

    def __init__(self, tail):
        validate_form(tail, 1)
        self.exprs = tail

    def eval(self, env, is_tail=False):
        """Evaluate each expression in order in the current environment,
        returning the evaluated last one."""
        for expr in self.exprs[:-1]:
            scheme_eval(expr, env)
        return scheme_eval(self.exprs[-1], env, is_tail)

class LambdaForm(SpecialForm):
    """A Scheme special form with a syntax of 
    (lambda ([param] ...) <body> ...)"""

    def __init__(self, tail):
        validate_form(tail, 2)
        self.formals = tail.first
        validate_formals(self.formals)
        self.body = tail.rest

    def eval(self, env, is_tail=False):
        """Create a new lambda with 
        params as its parameters and 
        the body expressions as its body."""
        return LambdaProcedure(self.formals, self.body, env)

class MuForm(SpecialForm):
    """A Scheme special form with a syntax of 
    (mu ([param] ...) <body> ...)"""

    def __init__(self, tail):
        validate_form(tail, 2)
        self.formals = tail.first
        validate_formals(self.formals)
        self.body = tail.rest

    def eval(self, env, is_tail=False):
        """Create a new mu procedure with 
        params as its parameters and the body expressions as its body.
        When the procedure this form creates is called,
        the call frame will extend the environment the mu is called in."""
        return MuProcedure(self.formals, self.body)

class QuoteForm(SpecialForm):
    """A Scheme special form with a syntax of 
    (quote <expression>)"""

    def __init__(self, tail):
        validate_form(tail, 1, 1)
        self.expr = tail.first
        
    def eval(self, env, is_tail=False):
        """Returns the literal expression without evaluating it."""
        return self.expr

class DefineMacroForm(SpecialForm):
    """A Scheme special form with a syntax of 
    (define-macro (<name> [param] ...) <body> ...)"""

    def __init__(self, tail):
        validate_form(tail, 2)
        validate_form(tail.first, 1)
        self.name = tail.first.first
        self.params = tail.first.rest
        validate_formals(Pair(self.name, nil))
        validate_formals(self.params)
        self.body = tail.rest

    def eval(self, env, is_tail=False):
        """Constructs a new macro procedure with
        params as its parameters and
        the body expressions as its body and
        binds it to name in the current environment."""
        macro = MacroProcedure(self.params, self.body)
        env.define(self.name, macro)
        return self.name

special_forms = {
    'define': DefineForm,
    'if': IfForm,
    'cond': CondForm,
    'and': AndForm,
    'or': OrForm,
    'let': LetForm,
    'begin': BeginForm,
    'lambda': LambdaForm,
    'mu': MuForm,
    'quote': QuoteForm,
    'define-macro': DefineMacroForm,
}

def scheme_special_formp(x):
    return isinstance(x, type) and issubclass(x, SpecialForm) 
# END

# Utility methods for checking the structure of Scheme programs

def validate_form(expr, min, max=float('inf')):
    """Check EXPR is a proper list whose length is at least MIN and no more
    than MAX (default: no maximum). Raises a SchemeError if this is not the
    case.

    >>> validate_form(read_line('(a b)'), 2)
    """
    if not scheme_listp(expr):
        raise SchemeError('badly formed expression: ' + repl_str(expr))
    length = len(expr)
    if length < min:
        raise SchemeError('too few operands in form')
    elif length > max:
        raise SchemeError('too many operands in form')

def validate_formals(formals):
    """Check that FORMALS is a valid parameter list, a Scheme list of symbols
    in which each symbol is distinct. Raise a SchemeError if the list of
    formals is not a list of symbols or if any symbol is repeated.

    >>> validate_formals(read_line('(a b c)'))
    """
    symbols = set()
    def validate_and_add(symbol, is_last):
        if not scheme_symbolp(symbol):
            raise SchemeError('non-symbol: {0}'.format(symbol))
        if symbol in symbols:
            raise SchemeError('duplicate symbol: {0}'.format(symbol))
        symbols.add(symbol)

    while isinstance(formals, Pair):
        validate_and_add(formals.first, formals.rest is nil)
        formals = formals.rest

    # here for compatibility with DOTS_ARE_CONS
    if formals != nil:
        validate_and_add(formals, True)

def validate_procedure(procedure):
    """Check that PROCEDURE is a valid Scheme procedure."""
    if not scheme_procedurep(procedure):
        raise SchemeError('{0} is not callable: {1}'.format(
            type(procedure).__name__.lower(), repl_str(procedure)))

#################
# Dynamic Scope #
#################

class MuProcedure(Procedure):
    """A procedure defined by a mu expression, which has dynamic scope.
     _________________
    < Scheme is cool! >
     -----------------
            \   ^__^
             \  (oo)\_______
                (__)\       )\/\
                    ||----w |
                    ||     ||
    """

    def __init__(self, formals, body):
        """A procedure with formal parameter list FORMALS (a Scheme list) and
        Scheme list BODY as its definition."""
        self.formals = formals
        self.body = body

    # Created by Rui Gao
    def apply(self, args, env):
        """follow the same evaluation rules as lambda procedures.
        However, the Frame created has its parent as the Frame it is called in,
        not the Frame it was defined in."""
        return LambdaProcedure(self.formals, self.body, env).apply(args, env)
    # End

    def __str__(self):
        return str(Pair('mu', Pair(self.formals, self.body)))

    def __repr__(self):
        return 'MuProcedure({0}, {1})'.format(
            repr(self.formals), repr(self.body))


##################
# Tail Recursion #
##################


# Make classes/functions for creating tail recursive programs here?

def complete_apply(procedure, args, env):
    """Apply procedure to args in env; ensure the result is not a Thunk.
    Right now it just calls scheme_apply, but you will need to change this
    if you attempt the optional questions."""
    val = scheme_apply(procedure, args, env)
    # Created by Rui Gao
    while isinstance(val, ThunkProcedure):
        val = val.apply(args, env)
    # End
    return val

# Created by Rui Gao
class ThunkProcedure(Procedure):
    """Delay the evaluation of expressions in tail contexts and then
    evaluate it at a later time by wrapping an expression in.
    A thunk should contain all the information needed
    to evaluate that expression even outside the frame of scheme_eval."""

    def __init__(self, procedure, args):
        self.procedure = procedure
        self.args = args

    def apply(self, _, env):
        return scheme_apply(self.procedure, self.args, env)
# END


####################
# Extra Procedures #
####################

# Created by Rui Gao
class MacroProcedure(Procedure):
    """A procedure defined by a define-macro expression,
    It is applied to its arguments without first evaluating them.
    Then the result of this application is evaluated."""

    def __init__(self, params, body):
        self.params = params
        self.body = body

    def apply(self, args, env):
        return scheme_eval(LambdaProcedure(self.params, self.body, env).apply(args, env), env)
# End

def scheme_map(fn, s, env):
    validate_type(fn, scheme_procedurep, 0, 'map')
    validate_type(s, scheme_listp, 1, 'map')
    return s.map(lambda x: complete_apply(fn, Pair(x, nil), env))

def scheme_filter(fn, s, env):
    validate_type(fn, scheme_procedurep, 0, 'filter')
    validate_type(s, scheme_listp, 1, 'filter')
    head, current = nil, nil
    while s is not nil:
        item, s = s.first, s.rest
        if complete_apply(fn, Pair(item, nil), env):
            if head is nil:
                head = Pair(item, nil)
                current = head
            else:
                current.rest = Pair(item, nil)
                current = current.rest
    return head

def scheme_reduce(fn, s, env):
    validate_type(fn, scheme_procedurep, 0, 'reduce')
    validate_type(s, lambda x: x is not nil, 1, 'reduce')
    validate_type(s, scheme_listp, 1, 'reduce')
    value, s = s.first, s.rest
    while s is not nil:
        value = complete_apply(fn, scheme_list(value, s.first), env)
        s = s.rest
    return value

################
# Input/Output #
################

def read_eval_print_loop(next_line, env, interactive=False, quiet=False,
                         startup=False, load_files=()):
    """Read and evaluate input until an end of file or keyboard interrupt."""
    if startup:
        for filename in load_files:
            scheme_load(filename, True, env)
    while True:
        try:
            src = next_line()
            while src.more_on_line:
                expression = scheme_read(src)
                result = scheme_eval(expression, env)
                if not quiet and result is not None:
                    print(repl_str(result))
        except (SchemeError, SyntaxError, ValueError, RuntimeError) as err:
            if (isinstance(err, RuntimeError) and
                'maximum recursion depth exceeded' not in getattr(err, 'args')[0]):
                raise
            elif isinstance(err, RuntimeError):
                print('Error: maximum recursion depth exceeded')
            else:
                print('Error:', err)
        except KeyboardInterrupt:  # <Control>-C
            if not startup:
                raise
            print()
            print('KeyboardInterrupt')
            if not interactive:
                return
        except EOFError:  # <Control>-D, etc.
            print()
            return

def scheme_load(*args):
    """Load a Scheme source file. ARGS should be of the form (SYM, ENV) or
    (SYM, QUIET, ENV). The file named SYM is loaded into environment ENV,
    with verbosity determined by QUIET (default true)."""
    if not (2 <= len(args) <= 3):
        expressions = args[:-1]
        raise SchemeError('"load" given incorrect number of arguments: '
                          '{0}'.format(len(expressions)))
    sym = args[0]
    quiet = args[1] if len(args) > 2 else True
    env = args[-1]
    if (scheme_stringp(sym)):
        sym = eval(sym)
    validate_type(sym, scheme_symbolp, 0, 'load')
    with scheme_open(sym) as infile:
        lines = infile.readlines()
    args = (lines, None) if quiet else (lines,)
    def next_line():
        return buffer_lines(*args)

    read_eval_print_loop(next_line, env, quiet=quiet)

def scheme_open(filename):
    """If either FILENAME or FILENAME.scm is the name of a valid file,
    return a Python file opened to it. Otherwise, raise an error."""
    try:
        return open(filename)
    except IOError as exc:
        if filename.endswith('.scm'):
            raise SchemeError(str(exc))
    try:
        return open(filename + '.scm')
    except IOError as exc:
        raise SchemeError(str(exc))

def create_global_frame():
    """Initialize and return a single-frame environment with built-in names."""
    env = Frame(None)
    env.define('eval',
               BuiltinProcedure(scheme_eval, True, 'eval'))
    env.define('apply',
               BuiltinProcedure(complete_apply, True, 'apply'))
    env.define('load',
               BuiltinProcedure(scheme_load, True, 'load'))
    env.define('procedure?',
               BuiltinProcedure(scheme_procedurep, False, 'procedure?'))
    env.define('map',
               BuiltinProcedure(scheme_map, True, 'map'))
    env.define('filter',
               BuiltinProcedure(scheme_filter, True, 'filter'))
    env.define('reduce',
               BuiltinProcedure(scheme_reduce, True, 'reduce'))
    env.define('undefined', None)
    add_builtins(env, BUILTINS)
    return env

@main
def run(*argv):
    import argparse
    parser = argparse.ArgumentParser(description='CS 61A Scheme Interpreter')
    parser.add_argument('--pillow-turtle', action='store_true',
                        help='run with pillow-based turtle. This is much faster for rendering but there is no GUI')
    parser.add_argument('--turtle-save-path', default=None,
                        help='save the image to this location when done')
    parser.add_argument('-load', '-i', action='store_true',
                       help='run file interactively')
    parser.add_argument('file', nargs='?',
                        type=argparse.FileType('r'), default=None,
                        help='Scheme file to run')
    args = parser.parse_args()

    import scheme
    scheme.TK_TURTLE = not args.pillow_turtle
    scheme.TURTLE_SAVE_PATH = args.turtle_save_path
    sys.path.insert(0, '')
    sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(scheme.__file__))))

    next_line = buffer_input
    interactive = True
    load_files = []

    if args.file is not None:
        if args.load:
            load_files.append(getattr(args.file, 'name'))
        else:
            lines = args.file.readlines()
            def next_line():
                return buffer_lines(lines)
            interactive = False

    read_eval_print_loop(next_line, create_global_frame(), startup=True,
                         interactive=interactive, load_files=load_files)
    tscheme_exitonclick()