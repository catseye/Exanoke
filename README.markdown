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
*   You can write it in a language which is inherently restricted to
    expressing only primitive recursive functions.

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
thing, and there are no natural bounds on that recursion, so those would have
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
    "smaller" values than the arguments the function received.
*   There is a "smallest" value that an argument can take on, so that
    there is always a base case to the recursion, so that it always
    eventually terminates.
*   Higher-order functions are not used.

The first point can be enforced simply by providing a token that
refers to the function currently being defined (`self` is a reasonable
choice) to permit recursion, but to disallow calling any function that
has not yet occurred, lexically, in the program source.

The second point can be enforced by stating syntactic rules for
"smallerness".  (Gee, typing that made me feel a bit like George W. Bush!)

The third point can be enforced by providing some default behaviour when
functions are called with the "smallest" kinds of values.  This could be
as simple as terminating the program if you try to find a value "smaller"
than the "smallest" value.

The fourth point can be enforced by simply disallowing functions to be
passed to, or returned from, functions.

### Note on Critical Arguments ###

I should note, though, that the second point is an oversimplification.
Not *all* arguments need to be strictly "smaller" upon recursion -- only
those arguments which are used to determine *if* the function recurses.
I'll call those the _critical arguments_.  Other arguments can take on
any value (which is useful for having "accumulator" arguments and such.)

When statically analyzing a function for primitive recursive-ness, you
need to check how it decides to rescurse, to find out which arguments are
the critical arguments, so you can check that those ones always get
"smaller".

But we can proceed in a simpler fashion here -- we can simply say that
the first argument to every function is the critical argument, and all
the rest aren't.  I believe this is without loss of generality, as we can
always split some functionality which would require more than one critical
argument across multiple functions, each of which only has one critical
argument.  (Much like every `for` loop has only one loop variable.)

Data types
----------

Let's just go with pairs and atoms for now, although natural numbers would
be easy to add too.  Atoms are all-uppercase, and `TRUE` is the only truthy
atom.  Lists are by convention only (and by convention, lists compose via
the second element of each pair, and `NIL` is the agreed-upon list-terminating
atom, much love to it.)

Grammar
-------

    Exanoke     ::= {FunDef} Expr.
    FunDef      ::= "def" Ident "(" "#" {"," Ident} ")" Expr.
    Expr        ::= "cons" "(" Expr "," Expr ")"
                  | "if" Expr "then" Expr "else" Expr
                  | "self" "(" Smaller {"," Expr} ")"
                  | "eq?" "(" Expr "," Expr")"
                  | "cons?" "(" Expr ")"
                  | "not" "(" Expr ")"
                  | "#"
                  | Atom
                  | Ident ["(" Expr {"," Expr} ")"]
                  | Smaller.
    Smaller     ::= "<head" SmallerTerm
                  | "<tail" SmallerTerm
                  | "<if" Expr "then" Smaller "else" Smaller.
    SmallerTerm ::= "#"
                  | Smaller.
    Ident       ::= name<lowercase>.
    Atom        ::= name<uppercase>.

The first argument to a function does not have a user-defined name; it is
simply referred to as `#`.

The names of arguments defined in a function shall not shadow the names of
any previously-defined functions.

Note that `<if` does not seem to be truly necessary.  Its only use is to embed
a conditional into the first argument being passed to a recursive call.  You
could also use a regular `if` and make the recursive call in both branches,
one with `TRUE` as the first argument and the other with `FALSE`.  I think.

Examples
--------

    -> Tests for functionality "Evaluate Exanoke program"
    
    -> Functionality "Evaluate Exanoke program" is implemented by
    -> shell command "script/exanoke %(test-file)"

Basic examples.

    | cons(HI, THERE)
    = (HI THERE)
    
    | cons(HI, cons(THERE, NIL))
    = (HI (THERE NIL))

    | <head cons(HI, THERE)
    = HI

    | <tail cons(HI, THERE)
    = THERE

    | <tail <tail (cons(HI, cons(THERE, NIL)))
    = NIL

    | <tail FOO
    ? tail: Not a cons cell

    | <head BAR
    ? head: Not a cons cell

    | if TRUE then HI else THERE
    = HI

    | if HI then HERE else THERE
    = THERE

    | eq?(HI, THERE)
    = FALSE

    | eq?(HI, HI)
    = TRUE

    | cons?(HI)
    = FALSE

    | cons?(cons(WAGGA, NIL))
    = TRUE

    | not(TRUE)
    = FALSE

    | not(FALSE)
    = TRUE

    | not(cons(WANGA, NIL))
    = TRUE

    | #
    ? Use of "#" outside of a function body

    | self(FOO)
    ? Use of "self" outside of a function body

    | def id(#)
    |     #
    | id(WOO)
    = WOO

    | def id(#)
    |     #
    | id(FOO, BAR)
    ? Arity mismatch

    | def id(#)
    |     woo
    | id(WOO)
    ? Undefined argument "woo"

    | def wat(#, woo)
    |     woo(#)
    | wat(WOO)
    ? Undefined function "woo"

    | def wat(#)
    |     THERE
    | def wat(#)
    |     HI
    | wat(WOO)
    ? Function "wat" already defined

    | def WAT(#)
    |     #
    | WAT(WOO)
    ? Expected identifier, but found atom ('WAT')

    | def wat(meow)
    |     meow
    | wat(WOO)
    ? Expected '#', but found 'meow'

    | def snd(#, another)
    |     another
    | snd(FOO, BAR)
    = BAR

    | def snd(#, another)
    |     another
    | snd(FOO)
    ? Arity mismatch

    | def snoc(#, another)
    |     cons(another, #)
    | snoc(THERE, HI)
    = (HI THERE)

    | def count(#)
    |     self(<tail #)
    | count(cons(A, cons(B, NIL)))
    ? tail: Not a cons cell

    | def count(#)
    |     if eq?(#, NIL) then NIL else self(<tail #)
    | count(cons(A, cons(B, NIL)))
    = NIL

    | def last(#)
    |     if not(cons?(#)) then # else self(<tail #)
    | last(cons(A, cons(B, GRAAAP)))
    = GRAAAP

    | def count(#, acc)
    |     if eq?(#, NIL) then acc else self(<tail #, cons(ONE, acc))
    | count(cons(A, cons(B, NIL)), NIL)
    = (ONE (ONE NIL))

    | def double(#)
    |     cons(#, #)
    | def quadruple(#)
    |     double(double(#))
    | quadruple(MEOW)
    = ((MEOW MEOW) (MEOW MEOW))

    | def quadruple(#)
    |     double(double(#))
    | def double(#)
    |     cons(#, #)
    | MEOW
    ? Undefined function "double"

    | def urff(#)
    |     self(cons(#, #))
    | urff(WOOF)
    ? Expected <smaller>, found "cons"

    | def urff(#)
    |     self(#)
    | urff(GRAAAAP)
    ? Expected <smaller>, found "#"

    | def urff(#, boof)
    |     self(boof)
    | urff(GRAAAAP, SKOOOORP)
    ? Expected <smaller>, found "boof"

    | def urff(#, boof)
    |     self(<tail boof)
    | urff(GRAAAAP, SKOOOORP)
    ? Expected <smaller>, found "boof"

    | def urff(#)
    |     self(WANGA)
    | urff(GRAAAAP)
    ? Expected <smaller>, found "WANGA"

    | def urff(#)
    |     self(if eq?(A, A) then <head # else <tail #)
    | urff(GRAAAAP)
    ? Expected <smaller>, found "if"

    | def urff(#)
    |     self(<if eq?(A, A) then <head # else <tail #)
    | urff(GRAAAAP)
    ? head: Not a cons cell

    | def urff(#)
    |     self(<if eq?(self(<head #), A) then <head # else <tail #)
    | urff(GRAAAAP)
    ? head: Not a cons cell

    | def urff(#)
    |     self(<if self(<tail #) then <head # else <tail #)
    | urff(cons(GRAAAAP, FARRRRP))
    ? tail: Not a cons cell

TODO more examples here...

Discussion
----------

I'm pretty sure this holds water, at this point.

The name "Exanoke" started life as a typo for the word "example".
