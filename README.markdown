Exanoke
=======

*This language is a work very much in progress.*

_Exanoke_ is a pure functional language which is syntactically restricted to
expressing the primitive recursive functions.

I'll assume you know what a primitive recursive function is.  If not, go look
it up, it's quite interesting, even if only for the fact that it demonstrates
even a genius like Kurt Goedel can sometimes be mistaken.  (He initially
thought that all functions could be expressed primitive recursively, until
Ackermann came up with a counterexample.)

So, you have a program.  There are two ways that you can ensure that it
implements a primtive recursive function:

*   You can statically analyze the bastard, and prove that all of its
    loops eventually terminate, and so forth; or
*   You can write it in a language which naturally restricts you to the
    primitive recursive functions.

The second option is the route [PL-{GOTO}][] takes.  But that's an imperative
language, and it's fairly easy to restrict an imperative language in this
way.  In PL-{GOTO}'s case, they just took PL and removed the `GOTO` construct.
The rest of the language essentially contains only `for` loops, so what you
get is something in which you can only express primitive recursive functions.

But what about functional languages?

The approach I've taken in [TPiS][], and that I wanted to take in [Pixley][]
and [Robin][], is to provide an unrestricted functional language to the
programmer, and statically analyze it to see if you're going and writing
primitive recursive functions in it or not.

Thing is, that's kind of difficult.  Is it possible to take the same approach
PL-{GOTO} takes, and *syntactically* restrict a functional language to the
primitive recursive functions?  It *should* be possible... and easier than
statically analyzing an arbitrary program... but it's not immediately trivial.
Functional languages don't do the `for` loop thing, they do the recursion
thing, and there are no natural bound on recursion, and they would have
to be embodied by the grammar, and... well, it sounds interesting, but
doable.  So let's try it.

[Pixley]: https://catseye.tc/projects/pixley/
[PL-{GOTO}]: http://catseye.tc/projects/pl-goto.net/
[Robin]: https://github.com/catseye/Robin
[TPiS]: http://catseye.tc/projects/tpis/

Ground Rules
------------

Here are some ground rules about how to tell if a functional program is
primitive recursive:

*   It doesn't perform mutual recursion.
*   When recursion happens, it's always with arguments that are strictly
    "smaller" than the arguments the function received.
*   There is always a base case to the recursion, so that it always
    eventually terminates.
*   Higher-order functions are not used.

The first point can be enforced simply by providing a token that
refers to the function currently being defined (`self` is a reasonable
choice) to permit recursion, but to disallow calling any function that
has not yet occurred, lexically, in the program source.

The second point can be enforced by stating syntactic rules for
"smallerness".  (Gee, typing that made me feel a bit like George W. Bush!)

The third point can be enforced by providing some default behaviour when
functions are called with the "smallest" kinds of values.

The fourth point can be enforced by simply disallowing functions to be
passed to, or returned from, functions.

TODO explain critical arguments and how the only critical argument in
an Exanoke function is always the first argument.

Data types
----------

Let's just go with pairs and atoms for now, although natural numbers would
be easy to add too.  Atoms are all-uppercase, and `TRUE` is the only truthy
atom.  Lists are by convention only (and by convention, lists compose via
the second element of each pair, and `NIL` is the agreed-upon list-terminating
atom, much love to it.)

Arguments do not have user-defined names, they're just referred to strings of
`#` symbols: `#` is the first argument to the function, `##` is the second,
etc.  When a function is defined, the name of the last argument is given, to
specify how many arguments the function takes.

Grammar
-------

    Exanoke     ::= {FunDef} Expr.
    FunDef      ::= "def" name<lowercase> "(" FirstArg | Arg ")" Expr.
    FirstArg    ::= "#".
    Arg         ::= "##" {"#"}.
    Expr        ::= "cons" "(" Expr Expr ")"
                  | "if" Expr "then" Expr "else" Expr
                  | "self" "(" Smaller {Expr} ")"
                  | "eq?" "(" Expr Expr")"
                  | "cons?" Expr
                  | "not" Expr
                  | "(" Expr ")"
                  | name<lowercase> "(" {Expr} ")"
                  | FirstArg
                  | Arg
                  | Atom
                  | Smaller.
    Smaller     ::= "<head" SmallerTerm
                  | "<tail" SmallerTerm
                  | "<if" Expr "then" Smaller "else" Smaller.
    SmallerTerm ::= Smaller
                  | FirstArg.
    Atom        ::= name<uppercase>.

TODO still not entirely sure about `<if`.

Examples
--------

    | cons(HI THERE)
    = (HI THERE)
    
    | (cons(HI cons(THERE NIL)))
    = (HI (THERE NIL))

    | <head cons(HI THERE)
    = HI

    | <tail cons(HI THERE)
    = THERE

    | <tail <tail (cons(HI cons(THERE NIL)))
    = NIL

    | <tail FOO
    ? Not a cons cell

    | <head BAR
    ? Not a cons cell

    | if TRUE then HI else THERE
    = HI

    | if HI then HERE else THERE
    = THERE

    | eq?(HI THERE)
    = FALSE

    | eq?(HI HI)
    = TRUE

    | cons? HI
    = FALSE

    | cons? cons(WAGGA NIL)
    = TRUE

    | not TRUE
    = FALSE

    | not FALSE
    = TRUE

    | not cons(WANGA NIL)
    = TRUE

    | #
    ? Not in a function body

    | self(FOO)
    ? Not in a function body

    | def id(#)
    |     #
    | id(WOO)
    = WOO

    | def id(#)
    |     #
    | id(FOO BAR)
    ? Arity mismatch

    | def id(#)
    |     ##
    | id(WOO)
    ? Arity mismatch

    | def snd(##)
    |     ##
    | snd(FOO BAR)
    = BAR

    | def snd(##)
    |     ##
    | snd(FOO)
    ? Arity mismatch

    | def snoc(##)
    |     cons(## #)
    | snoc(THERE HI)
    = (HI THERE)

    | def count(#)
    |     self(<tail #)
    | count(cons(A cons(B NIL)))
    ? Not a cons cell

    | def count(#)
    |     if eq?(# NIL) then NIL else self(<tail #)
    | count(cons(A cons(B NIL)))
    = NIL

    | def last(#)
    |     if not cons? # then # else self(<tail #)
    | last(cons(A cons(B GRAAAP)))
    = GRAAAP

    | def count(##)
    |     if eq?(# NIL) then ## else self(<tail # cons(ONE ##))
    | count(cons(A cons(B NIL)) NIL)
    = (ONE (ONE NIL))

    | def double(#)
    |     cons(# #)
    | def quadruple(#)
    |     double(double(#))
    | quadruple MEOW
    = ((MEOW MEOW) (MEOW MEOW))

    | def quadruple(#)
    |     double(double(#))
    | def double(#)
    |     cons(# #)
    | MEOW
    ? Undefined function

    | def urff(#)
    |     self(cons(# #))
    | urff(WOOF)
    ? Expected <smaller>, found "cons"

    | def urff(#)
    |     self(#)
    | urff(GRAAAAP)
    ? Expected <smaller>, found "#"

    | def urff(##)
    |     self(##)
    | urff(GRAAAAP SKOOOORP)
    ? Expected <smaller>, found "##"

    | def urff(##)
    |     self(<tail ##)
    | urff(GRAAAAP SKOOOORP)
    ? Expected <smallerterm>, found "##"

    | def urff(#)
    |     self(WANGA)
    | urff(GRAAAAP)
    ? Expected <smaller>, found "WANGA"

    | def urff(#)
    |     self(if eq?(self(#) A) then <head # else <tail #)
    | urff(GRAAAAP)
    ? Expected <smaller>, found "self"

    | def urff(#)
    |     self(if self(<tail #) then <head # else <tail #)
    | urff(cons(GRAAAAP FARRRRP))
    ? Not a cons cell

TODO more examples here...

Discussion
----------

I don't know if this holds water yet or not.

The name "Exanoke" started life as a typo for the word "example".
