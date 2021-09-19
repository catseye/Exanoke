Exanoke
=======

_Exanoke_ is a pure functional language which is syntactically restricted to
expressing the primitive recursive functions.

I'll assume you know what a primitive recursive function is.  If not, go look
it up, as it's quite interesting, if only for the fact that it demonstrates
even a genius like Kurt Gödel can sometimes be mistaken.  (He initially
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
way.  In PL-{GOTO}'s case, they just took PL and removed the `GOTO` command.
The rest of the language essentially contains only `for` loops, so what you
get is something in which you can only express primitive recursive functions.
(That imperative programs consisting of only `for` loops can express only and
exactly the primitive recursive functions was established by Meyer and Ritchie
in "The complexity of loop programs".)

But what about functional languages?

The approach I've taken in [TPiS][], and that I wanted to take in [Pixley][]
and [Robin][], is to provide an unrestricted functional language to the
programmer, and statically analyze it to see if you're going and writing
primitive recursive functions in it or not.

Thing is, that's kind of difficult.  Is it possible to take the same approach
PL-{GOTO} takes, and *syntactically* restrict a functional language to the
primitive recursive functions?

I mean, in a trivial sense, it must be; in the original definition, primitive
recursive functions *were* functions.  (Duh.)  But these have a highly
arithmetical flavour, with bounded sums and products and whatnot.  What
would primitive recursion look like in the setting of general (and symbolic)
functional programming?

Functional languages don't do the `for` loop thing, they do the recursion
thing, and there are no natural bounds on that recursion, so some restriction
on recursion would have to be captured by the grammar, and... well, it sounds
somewhat interesting, and doable, so let's try it.

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

### Note on these Criteria ###

In fact, these four criteria taken together do not strictly speaking
define primitive recursion.  They don't exclude functional programs which
always terminate but which aren't primitive recursive (for example, the
Ackermann function.)  However, determining that such functions terminate
requires a more sophisticated notion of "smallerness" — a reduction ordering
on their arguments.  Our notion of "smallerness" will be simple enough that
it will be easy to express syntactically, and will only capture primitive
recursion.

### Note on Critical Arguments ###

I should note, though, that the second point is an oversimplification.
Not *all* arguments need to be strictly "smaller" upon recursion — only
those arguments which are used to determine *if* the function recurses.
I'll call those the _critical arguments_.  Other arguments can take on
any value (which is useful for having "accumulator" arguments and such.)

When statically analyzing a function for primitive recursive-ness, you
need to check how it decides to recurse, to find out which arguments are
the critical arguments, so you can check that those ones always get
"smaller".

But we can proceed in a simpler fashion here — we can simply say that
the first argument to every function is the critical argument, and all
the rest aren't.  This is without loss of generality, as we can always
split some functionality which would require more than one critical
argument across multiple functions, each of which only has one critical
argument.  (Much like every `for` loop has only one loop variable.)

Data types
----------

Let's just go with pairs and atoms for now, although natural numbers would
be easy to add too.  Following Ruby, atoms are preceded by a colon; while I
find this syntax somewhat obnoxious, it is less obnoxious than requiring that
atoms are in ALL CAPS, which is what Exanoke originally had.  In truth, there
would be no real problem with allowing atoms, arguments, and function names
(and even `self`) to all be arbitrarily alphanumeric, but it would require
more static context checking to sort them all out, and we're trying to be
as syntactic as reasonably possible here.

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

Note that `<if` is not strictly necessary.  Its only use is to embed a
conditional into the first argument being passed to a recursive call.  You
could also use a regular `if` and make the recursive call in both branches,
one with `:true` as the first argument and the other with `:false`.

Examples
--------

    -> Tests for functionality "Evaluate Exanoke program"

`cons` can be used to make lists and trees and things.

    | cons(:hi, :there)
    = (:hi :there)
    
    | cons(:hi, cons(:there, :nil))
    = (:hi (:there :nil))

`head` extracts the first element of a cons cell.

    | head(cons(:hi, :there))
    = :hi

    | head(:bar)
    ? head: Not a cons cell

`tail` extracts the second element of a cons cell.

    | tail(cons(:hi, :there))
    = :there

    | tail(tail(cons(:hi, cons(:there, :nil))))
    = :nil

    | tail(:foo)
    ? tail: Not a cons cell

`<head` and `<tail` and syntactic variants of `head` and `tail` which
expect their argument to be "smaller than or equal in size to" a critical
argument.

    | <head cons(:hi, :there)
    ? Expected <smaller>, found "cons"

    | <tail :hi
    ? Expected <smaller>, found ":hi"

`if` is used for descision-making.

    | if :true then :hi else :there
    = :hi

    | if :hi then :here else :there
    = :there

`eq?` is used to compare atoms.

    | eq?(:hi, :there)
    = :false

    | eq?(:hi, :hi)
    = :true

`eq?` only compares atoms; it can't deal with cons cells.

    | eq?(cons(:one, :nil), cons(:one, :nil))
    = :false

`cons?` is used to detect cons cells.

    | cons?(:hi)
    = :false

    | cons?(cons(:wagga, :nil))
    = :true

`not` does the expected thing when regarding atoms as booleans.

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

We can define functions.  Here's the identity function.

    | def id(#)
    |     #
    | id(:woo)
    = :woo

Functions must be called with the appropriate arity.

    | def id(#)
    |     #
    | id(:foo, :bar)
    ? Arity mismatch (expected 1, got 2)

    | def snd(#, another)
    |     another
    | snd(:foo)
    ? Arity mismatch (expected 2, got 1)

Parameter names must be defined in the function definition.

    | def id(#)
    |     woo
    | id(:woo)
    ? Undefined argument "woo"

You can't call a parameter as if it were a function.

    | def wat(#, woo)
    |     woo(#)
    | wat(:woo)
    ? Undefined function "woo"

You can't define two functions with the same name.

    | def wat(#)
    |     :there
    | def wat(#)
    |     :hi
    | wat(:woo)
    ? Function "wat" already defined

You can't name a function with an atom.

    | def :wat(#)
    |     #
    | :wat(:woo)
    ? Expected identifier, but found atom (':wat')

Every function takes at least one argument.

    | def wat()
    |     :meow
    | wat()
    ? Expected '#', but found ')'

The first argument of a function must be `#`.

    | def wat(meow)
    |     meow
    | wat(:woo)
    ? Expected '#', but found 'meow'

The subsequent arguments don't have to be called `#`, and in fact, they
shouldn't be.

    | def snd(#, another)
    |     another
    | snd(:foo, :bar)
    = :bar

    | def snd(#, #)
    |     #
    | snd(:foo, :bar)
    ? Expected identifier, but found goose egg ('#')

A function can call a built-in.

    | def snoc(#, another)
    |     cons(another, #)
    | snoc(:there, :hi)
    = (:hi :there)

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

A function may recursively call itself, as long as it does so with
values which are smaller than or equal in size to the critical argument
as the first argument.

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

Arity must match when a function calls itself recursively.

    | def urff(#)
    |     self(<tail #, <head #)
    | urff(:woof)
    ? Arity mismatch on self (expected 1, got 2)

    | def urff(#, other)
    |     self(<tail #)
    | urff(:woof, :moo)
    ? Arity mismatch on self (expected 2, got 1)

The remaining tests demonstrate that a function cannot call itself if it
does not pass a values which is smaller than or equal in size to the
critical argument as the first argument.

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

Now, some practical examples, on Peano naturals.  Addition:

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

So, what of it?

It was not a particularly challenging design goal to meet; it's one of those
things that seems rather obvious after the fact, that you can just dictate
that one of the arguments is a critical argument, and only call yourself with
some smaller version of your critical argument in that position.  Recursive
calls map quite straightforwardly to `for` loops, and you end up with what is
essentially a functional version of of a `for` program.

I guess the question is, is it worth doing this primitive-recursion check as
a syntactic, rather than a static semantic, thing?

I think it is.  If you're concerned at all with writing functions which are
guaranteed to terminate, you probably have a plan in mind (however vague)
for how they will accomplish this, so it seems reasonable to require that you
mark up your function to indicate how it does this.  And it's certainly
easier to implement than analyzing an arbirarily-written function.

Of course, the exact syntactic mechanisms would likely see some improvement
in a practical application of this idea.  As alluded to in several places
in this document, any actually-distinct lexical items (name of the critical
argument, and so forth) could be replaced by simple static semantic checks
(against a symbol table or whatnot.)  Which arguments are the critical
arguments for a particular function could be indicated in the source.

One criticism (if I can call it that) of primitive recursive functions is
that, even though they can express any algorithm which runs in
non-deterministic exponential time (which, if you believe "polynomial
time = feasible", means, basically, all algorithms you'd ever care about),
for any primitive recursively expressed algorithm, theye may be a (much)
more efficient algorithm expressed in a general recursive way.

However, in my experience, there are many functions, generally non-, or
minimally, numerical, which operate on data structures, where the obvious
implementation _is_ primitive recursive.  In day-to-day database and web
programming, there will be operations which are series of replacements,
updates, simple transformations, folds, and the like, all of which
"obviously" terminate, and which can readily be written primitive recursively.

Limited support for higher-order functions could be added, possibly even to
Exanoke (as long as the "no mutual recursion" rule is still observed.)
After all (and if you'll forgive the anthropomorphizing self-insertion in
this sentence), if you pass me a primitive recursive function, and I'm
primitive recursive, I'll remain primitive recursive no matter how many times
I call your function.

Lastly, the requisite etymological denoument: the name "Exanoke" started life
as a typo for the word "example".

Happy primitive recursing!  
Chris Pressey  
Cornwall, UK, WTF  
Jan 5, 2013
