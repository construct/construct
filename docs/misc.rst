=============
Miscellaneous
=============

Conditional
===========

Optional
--------

Attempts to parse or build the subconstruct; if it fails, returns a default
value. By default, the default value is ``None``.

>>> foo = Optional(UBInt32("foo"))
>>> foo.parse("\x12\x34\x56\x78")
305419896
>>> print foo.parse("\x12\x34\x56")
None
>>>
>>> foo = Optional(UBInt32("foo"), default = 17)
>>> foo.parse("\x12\x34\x56\x78")
305419896
>>> foo.parse("\x12\x34\x56")
17


If
--

Parses or builds the subconstruct only if a certain condition is met.
Otherwise, returns a default value. By default, the default value is ``None``.

>>> foo = Struct("foo",
...     Flag("has_options"),
...     If(lambda ctx: ctx["has_options"],
...         Bytes("options", 5)
...     )
... )
>>>
>>> foo.parse("\x01hello")
Container(has_options = True, options = 'hello')
>>>
>>> foo.parse("\x00hello")
Container(has_options = False, options = None)
>>>


IfThenElse
----------

Branches the construction path based on a given condition. If the condition is
met, the ``then_construct`` is used; otherwise the ``else_construct`` is used.

>>> foo = Struct("foo",
...     Byte("a"),
...     IfThenElse("b", lambda ctx: ctx["a"] > 7,
...         UBInt32("foo"),
...         UBInt16("bar")
...     ),
... )
>>>
>>> foo.parse("\x09\xaa\xbb\xcc\xdd")    # <-- condition is met
Container(a = 9, b = 2864434397L)
>>> foo.parse("\x02\xaa\xbb")            # <-- condition is not met
Container(a = 2, b = 43707)


Alignment and Padding
=====================

Aligned
-------

Aligns the subconstruct to a given modulus boundary (default is 4).

>>> foo = Aligned(UBInt8("foo"))
>>> foo.parse("\xff\x00\x00\x00")
255
>>> foo.build(255)
'\xff\x00\x00\x00'


AlignedStruct
-------------

Automatically aligns all the fields of the Struct to the modulus
boundary.

>>> foo = AlignedStruct("foo",
...     Byte("a"),
...     Byte("b"),
... )
>>>
>>> foo.parse("\x01\x00\x00\x00\x02\x00\x00\x00")
Container(a = 1, b = 2)
>>> foo.build(Container(a=1,b=2))
'\x01\x00\x00\x00\x02\x00\x00\x00'


Padding
-------

Padding is a sequence of bytes or bits that contains no data (its value is
discarded), and is necessary only for padding, etc.

>>> foo = Struct("foo",
...     Byte("a"),
...     Padding(2),
...     Byte("b"),
... )
>>>
>>> foo.parse("\x01\x00\x00\x02")
Container(a = 1, b = 2)


Special Constructs
==================

Rename
------

Renames a construct.

>>> foo = Struct("foo",
...     Rename("xxx", Byte("yyy")),
... )
>>>
>>> foo.parse("\x02")
Container(xxx = 2)


Alias
-----

Creates an alias for an existing field of a Struct.

>>> foo = Struct("foo",
...     Byte("a"),
...     Alias("b", "a"),
... )
>>>
>>> foo.parse("\x03")
Container(a = 3, b = 3)


Value
-----

Represents a computed value. Value does not read or write anything to the
stream; it only returns its computed value as the result.

>>> foo = Struct("foo",
...     Byte("a"),
...     Value("b", lambda ctx: ctx["a"] + 7)
... )
>>>
>>> foo.parse("\x02")
Container(a = 2, b = 9)


Terminator
----------

Asserts the end of the stream has been reached (so that no more trailing data
is left unparsed).

.. note:: Terminator is a singleton object. Do not try to "instantiate" it (i.e., ``Terminator()``).

>>> Terminator.parse("")
>>> Terminator.parse("x")
Traceback (most recent call last):
  .
  .
construct.extensions.TerminatorError: end of stream not reached


Pass
----

A do-nothing construct; useful in Switches and Enums.

.. note:: Pass is a singleton object. Do not try to "instantiate" it (i.e., ``Pass()``).

>>> print Pass.parse("xyz")
None


Const
-----

A constant value that is required to exist in the data. If the value is not
matched, ConstError is raised. Useful for magic numbers, signatures, asserting
correct protocol version, etc.

>>> foo = Const(Bytes("magic", 6), "FOOBAR")
>>> foo.parse("FOOBAR")
'FOOBAR'
>>> foo.parse("FOOBAX")
Traceback (most recent call last):
  .
  .
construct.extensions.ConstError: expected 'FOOBAR', found 'FOOBAX'
>>>


Peek
----

Parses the subconstruct but restores the stream position afterwards
("peeking").

.. note:: Works only with seekable streams (in-memory and files).

>>> foo = Struct("foo",
...     Byte("a"),
...     Peek(Byte("b")),
...     Byte("c"),
... )
>>> foo.parse("\x01\x02")
Container(a = 1, b = 2, c = 2)


Union
-----

Treats the same data as multiple constructs (similar to C's union statement).
When building, each subconstruct parses the same data (so you can "look" at
the data in multiple views); when writing, the first subconstruct is used to
build the final result.

.. note:: Works only with seekable streams (in-memory and files).

>>> foo = Union("foo",
...     UBInt32("a"),
...     UBInt16("b"),                            # <-- note that this field is
of a different size
...     Struct("c", UBInt16("high"), UBInt16("low")),
...     LFloat32("d"),
... )
>>>
>>> print foo.parse("\xaa\xbb\xcc\xdd")
Container:
    a = 2864434397L
    b = 43707
    c = Container:
        high = 43707
        low = 52445
    d = -1.8440714901698642e+018
>>>
>>> foo.build(Container(a = 0x11223344, b=0,c=Container(low=0, high=0),d=0)) #
<-- only "a" is used for building
'\x11"3D'


LazyBound
---------

A lazy-bound construct; it binds to the construct only at runtime. Useful for
recursive data structures (like linked lists or trees), where a construct
needs to refer to itself (while it doesn't exist yet).

>>> foo = Struct("foo",
...     Flag("has_next"),
...     If(lambda ctx: ctx["has_next"], LazyBound("next", lambda: foo)),
... )
>>>
>>> print foo.parse("\x01\x01\x01\x00")
Container:
    has_next = True
    next = Container:
        has_next = True
        next = Container:
            has_next = True
            next = Container:
                has_next = False
                next = None
>>>
