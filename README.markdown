Exanoke
=======

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
be easy to add too.  Following Ruby, atoms are preceded by a colon; while I
find this syntax somewhat obnoxious, it is less obnoxious than requiring that
atoms are in ALL CAPS, which is what Exanoke originally had.  In truth, there
would be no real problem with allowing atoms, parameters, and function names
to all be arbitrarily alphanumeric, but it would require more static context
checking to sort them all out, and we're trying to be heavily syntactic here.

`:true` is the only truthy atom.  Lists are by convention only, and, by
convention, lists compose via the second element of each pair, and `:nil` is
the agreed-upon list-terminating atom, much love to it.

Grammar
-------

    Exanoke     ::= {FunDef} Expr.
    FunDef      ::= "def" Ident "(" "#" {"," Ident} ")" Expr.
    Expr        ::= "cons" "(" Expr "," Expr ")"
                  | "head" "(" Expr ")"
                  | "tail" "(" Expr ")"
                  | "if" Expr "then" Expr "else" Expr
                  | "self" "(" Smaller {"," Expr} ")"
                  | "eq?" "(" Expr "," Expr")"
                  | "cons?" "(" Expr ")"
                  | "not" "(" Expr ")"
                  | "#"
                  | ":" Ident
                  | Ident ["(" Expr {"," Expr} ")"]
                  | Smaller.
    Smaller     ::= "<head" SmallerTerm
                  | "<tail" SmallerTerm
                  | "<if" Expr "then" Smaller "else" Smaller.
    SmallerTerm ::= "#"
                  | Smaller.
    Ident       ::= name.

The first argument to a function does not have a user-defined name; it is
simply referred to as `#`.  Again, there would be no real problem if we were
to allow the programmer to give it a better name, but more static context
checking would be involved.

Note that `<if` does not seem to be truly necessary.  Its only use is to embed
a conditional into the first argument being passed to a recursive call.  You
could also use a regular `if` and make the recursive call in both branches,
one with `:true` as the first argument and the other with `:false`.

Examples
--------

    -> Tests for functionality "Evaluate Exanoke program"
    
    -> Functionality "Evaluate Exanoke program" is implemented by
    -> shell command "script/exanoke %(test-file)"

Basic examples.

    | cons(:hi, :there)
    = (:hi :there)
    
    | cons(:hi, cons(:there, :nil))
    = (:hi (:there :nil))

    | head(cons(:hi, :there))
    = :hi

    | tail(cons(:hi, :there))
    = :there

    | tail(tail(cons(:hi, cons(:there, :nil))))
    = :nil

    | tail(:foo)
    ? tail: Not a cons cell

    | head(:bar)
    ? head: Not a cons cell

    | <head cons(:hi, :there)
    ? Expected <smaller>, found "cons"

    | <tail :hi
    ? Expected <smaller>, found ":hi"

    | if :true then :hi else :there
    = :hi

    | if :hi then :here else :there
    = :there

    | eq?(:hi, :there)
    = :false

    | eq?(:hi, :hi)
    = :true

`eq?` only compares atoms; it can't deal with cons cells.

    | eq?(cons(:one, :nil), cons(:one, :nil))
    = :false

    | cons?(:hi)
    = :false

    | cons?(cons(:wagga, :nil))
    = :true

    | not(:true)
    = :false

    | not(:false)
    = :true

Cons cells are falsey.

    | not(cons(:wanga, :nil))
    = :true

`self` and `#` can only be used inside function definitions.

    | #
    ? Use of "#" outside of a function body

    | self(:foo)
    ? Use of "self" outside of a function body

    | def id(#)
    |     #
    | id(:woo)
    = :woo

    | def id(#)
    |     #
    | id(:foo, :bar)
    ? Arity mismatch (expected 1, got 2)

    | def id(#)
    |     woo
    | id(:woo)
    ? Undefined argument "woo"

    | def wat(#, woo)
    |     woo(#)
    | wat(:woo)
    ? Undefined function "woo"

    | def wat(#)
    |     :there
    | def wat(#)
    |     :hi
    | wat(:woo)
    ? Function "wat" already defined

    | def :wat(#)
    |     #
    | :wat(:woo)
    ? Expected identifier, but found atom (':wat')

    | def wat(meow)
    |     meow
    | wat(:woo)
    ? Expected '#', but found 'meow'

    | def snd(#, another)
    |     another
    | snd(:foo, :bar)
    = :bar

    | def snd(#, another)
    |     another
    | snd(:foo)
    ? Arity mismatch (expected 2, got 1)

    | def snoc(#, another)
    |     cons(another, #)
    | snoc(:there, :hi)
    = (:hi :there)

    | def count(#)
    |     self(<tail #)
    | count(cons(:alpha, cons(:beta, :nil)))
    ? tail: Not a cons cell

    | def count(#)
    |     if eq?(#, :nil) then :nil else self(<tail #)
    | count(cons(:alpha, cons(:beta, :nil)))
    = :nil

    | def last(#)
    |     if not(cons?(#)) then # else self(<tail #)
    | last(cons(:alpha, cons(:beta, :graaap)))
    = :graaap

    | def count(#, acc)
    |     if eq?(#, :nil) then acc else self(<tail #, cons(:one, acc))
    | count(cons(:A, cons(:B, :nil)), :nil)
    = (:one (:one :nil))

Functions can call other user-defined functions.

    | def double(#)
    |     cons(#, #)
    | def quadruple(#)
    |     double(double(#))
    | quadruple(:meow)
    = ((:meow :meow) (:meow :meow))

Functions must be defined before they are called.

    | def quadruple(#)
    |     double(double(#))
    | def double(#)
    |     cons(#, #)
    | :meow
    ? Undefined function "double"

Argument names may shadow previously-defined functions, because we
can syntactically tell them apart.

    | def snoc(#, other)
    |     cons(other, #)
    | def snocsnoc(#, snoc)
    |     snoc(snoc(snoc, #), #)
    | snocsnoc(:blarch, :glamch)
    = (:blarch (:blarch :glamch))

    | def urff(#)
    |     self(<tail #, <head #)
    | urff(:woof)
    ? Arity mismatch on self (expected 1, got 2)

    | def urff(#, other)
    |     self(<tail #)
    | urff(:woof, :moo)
    ? Arity mismatch on self (expected 2, got 1)

    | def urff(#)
    |     self(cons(#, #))
    | urff(:woof)
    ? Expected <smaller>, found "cons"

    | def urff(#)
    |     self(#)
    | urff(:graaap)
    ? Expected <smaller>, found "#"

    | def urff(#, boof)
    |     self(boof)
    | urff(:graaap, :skooorp)
    ? Expected <smaller>, found "boof"

    | def urff(#, boof)
    |     self(<tail boof)
    | urff(:graaap, :skooorp)
    ? Expected <smaller>, found "boof"

    | def urff(#)
    |     self(:wanga)
    | urff(:graaap)
    ? Expected <smaller>, found ":wanga"

    | def urff(#)
    |     self(if eq?(:alpha, :alpha) then <head # else <tail #)
    | urff(:graaap)
    ? Expected <smaller>, found "if"

    | def urff(#)
    |     self(<if eq?(:alpha, :alpha) then <head # else <tail #)
    | urff(:graaap)
    ? head: Not a cons cell

    | def urff(#)
    |     self(<if eq?(self(<head #), :alpha) then <head # else <tail #)
    | urff(:graaap)
    ? head: Not a cons cell

    | def urff(#)
    |     self(<if self(<tail #) then <head # else <tail #)
    | urff(cons(:graaap, :skooorp))
    ? tail: Not a cons cell

Some practical examples, on Peano naturals.  Addition:

    | def inc(#)
    |   cons(:one, #)
    | def add(#, other)
    |   if eq?(#, :nil) then other else self(<tail #, inc(other))
    | 
    | add(cons(:one, cons(:one, :nil)), cons(:one, :nil))
    = (:one (:one (:one :nil)))

Multiplication:

    | def inc(#)
    |   cons(:one, #)
    | def add(#, other)
    |   if eq?(#, :nil) then other else self(<tail #, inc(other))
    | def mul(#, other)
    |   if eq?(#, :nil) then :nil else
    |     add(other, self(<tail #, other))
    | def three(#)
    |   cons(:one, cons(:one, cons(:one, #)))
    | 
    | mul(three(:nil), three(:nil))
    = (:one (:one (:one (:one (:one (:one (:one (:one (:one :nil)))))))))

Factorial!  There are 24 `:one`'s in this test's expectation.

    | def inc(#)
    |   cons(:one, #)
    | def add(#, other)
    |   if eq?(#, :nil) then other else self(<tail #, inc(other))
    | def mul(#, other)
    |   if eq?(#, :nil) then :nil else
    |     add(other, self(<tail #, other))
    | def fact(#)
    |   if eq?(#, :nil) then cons(:one, :nil) else
    |     mul(#, self(<tail #))
    | def four(#)
    |   cons(:one, cons(:one, cons(:one, cons(:one, #))))
    | 
    | fact(four(:nil))
    = (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one (:one :nil))))))))))))))))))))))))

Discussion
----------

The name "Exanoke" started life as a typo for the word "example".
