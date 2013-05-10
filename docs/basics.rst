==========
The Basics
==========

Fields
======

Fields are the most fundamental unit of construction: they **parse** (read
data from the stream and return an object) and **build** (take an object and
write it down onto a stream). There are many kinds of fields, each working
with a different type of data (numeric, boolean, strings, etc.).

Some examples of parsing:

>>> from construct import UBInt16, ULInt16
>>> UBInt16("foo").parse("\x01\x02")
258
>>> ULInt16("foo").parse("\x01\x02")
513

Some examples of building:

>>> from construct import UBInt16, SBInt16
>>> UBInt16("foo").build(31337)
'zi'
>>> SBInt16("foo").build(-31337)
'\x86\x97'

Structs
=======

For those of you familiar with C, Structs are very intuitive, but here's a
short explanation for the larger audience. A Struct is a sequenced collection
of fields or other components, that are parsed/built in that order. Note that
if two or more fields of a Struct have the same name, the last field "wins";
that is, the last field's value will be the value returned from a parse.

>>> from construct import Struct, UBInt8, SLInt16, LFloat32
>>> c = Struct("foo",
...     UBInt8("a"),
...     SLInt16("b"),
...     LFloat32("c"),
... )
>>> c
<Struct('foo')>
>>> c.parse("\x07\x00\x01\x00\x00\x00\x01")
Container(a = 7, b = 256, c = 2.350988701644575e-038)

Containers
----------

What *is* that Container object, anyway? Well, a Container is a regular Python
dictionary. It provides pretty-printing and accessing items as attributes, in
addition to the normal facilities of dictionaries. Let's see more of those:

>>> x = c.parse("\x07\x00\x01\x00\x00\x00\x01")
>>> x
Container(a = 7, b = 256, c = 2.350988701644575e-038)
>>> x.a
7
>>> x.b
256
>>> print x
Container:
    a = 7
    b = 256
    c = 2.350988701644575e-038

Building
--------

And here is how we build Structs:

>>> # Rebuild the parsed object.
>>> c.build(x)
'\x07\x00\x01\x00\x00\x00\x01'

>>> # Mutate the parsed object and build...
>>> x.b = 5000
>>> c.build(x)
'\x07\x88\x13\x00\x00\x00\x01'

>>> # ...Or, we can create a new container.
>>> c.build(Container(a = 9, b = 1234, c = 56.78))
'\t\xd2\x04\xb8\x1ecB'

.. note::

   Building is fully duck-typed and can be done with any object.

>>> class Foo(object): pass
...
>>> f = Foo()
>>> f.a = 1
>>> f.b = 2
>>> f.c = 3
>>> c.build(f)
'\x01\x02\x00\x00\x00@@'

Nested
------

Structs can be nested. Structs can contain other Structs, as well as any
construct. Here's how it's done:

>>> c = Struct("foo",
...     UBInt8("a"),
...     UBInt16("b"),
...     Struct("bar",
...         UBInt8("a"),
...         UBInt16("b"),
...     )
... )
>>> x = c.parse("ABBabb")
>>> x
Container(a = 65, b = 16962, bar = Container(a = 97, b = 25186))
>>> print x
Container:
    a = 65
    b = 16962
    bar = Container:
        a = 97
        b = 25186
>>> x.a
65
>>> x.bar
Container(a = 97, b = 25186)
>>> x.bar.b
25186

As you can see, Containers provide human-readable representations of the data,
which is very important for large data structures.

Embedding
---------

A Struct can be embedded into an enclosing Struct. This means all the fields
of the embedded Struct will be merged into the fields of the enclosing Struct.
This is useful when you want to split a big Struct into multiple parts, and
then combine them all into one Struct.

>>> foo = Struct("foo",
...     UBInt8("a"),
...     UBInt8("b"),
... )
>>> bar = Struct("bar",
...     foo, # This Struct is not embedded.
...     UBInt8("c"),
...     UBInt8("d"),
... )
>>> bar2= Struct("bar",
...     Embed(foo), # This Struct is embedded.
...     UBInt8("c"),
...     UBInt8("d"),
... )
>>> bar.parse("abcd")
Container(c = 99, d = 100, foo = Container(a = 97, b = 98))
>>> bar2.parse("abcd")
Container(a = 97, b = 98, c = 99, d = 100)

.. seealso:: The :func:`~construct.macros.Embedded` macro.

Sequences
=========

Sequences are very similar to Structs, but operate with lists rather than
containers. Sequences are less commonly used than Structs, but are very handy
in certain situations. Since a list is returned in place of an attribute
container, the names of the sub-constructs are not important; two constructs
with the same name will not override or replace each other.

Parsing
-------

>>> c = Sequence("foo",
...     UBInt8("a"),
...     UBInt16("b"),
... )
>>> c
<Sequence('foo')>
>>> c.parse("abb")
[97, 25186]


Building
--------

>>> c.build([1,2])
'\x01\x00\x02'


Nested
------

>>> c = Sequence("foo",
...     UBInt8("a"),
...     UBInt16("b"),
...     Sequence("bar",
...         UBInt8("a"),
...         UBInt16("b"),
...     )
... )
>>> c.parse("ABBabb")
[65, 16962, [97, 25186]]


Embedded
--------

Like Structs, Sequences are compatible with the Embed wrapper. Embedding one
Sequence into another causes a merge of the parsed lists of the two Sequences.

>>> foo = Sequence("foo",
...     UBInt8("a"),
...     UBInt8("b"),
... )
>>> bar = Sequence("bar",
...     foo,                  # <-- unembedded
...     UBInt8("c"),
...     UBInt8("d"),
... )
>>> bar2 = Sequence("bar",
...     Embed(foo),           # <-- embedded
...     UBInt8("c"),
...     UBInt8("d"),
... )
>>> bar.parse("abcd")
[[97, 98], 99, 100]
>>> bar2.parse("abcd")
[97, 98, 99, 100]

.. _repeaters:

Repeaters
=========

Repeaters, as their name suggests, repeat a given unit for a specified number
of times. At this point, we'll only cover static repeaters. Meta-repeaters
will be covered in the meta-constructs tutorial.

We have four kinds of static repeaters. In fact, for those of you who wish to
go under the hood, two of these repeaters are actually wrappers around Range.

.. autofunction:: construct.Range

.. autofunction:: construct.Array

.. autofunction:: construct.GreedyRange

.. autofunction:: construct.OptionalGreedyRange

Nesting
-------

As with all constructs, Repeaters can be nested too. Here's an example:

>>> c = Array(5, Array(2, UBInt8("foo")))
>>> c.parse("aabbccddee")
[[97, 97], [98, 98], [99, 99], [100, 100], [101, 101]]
