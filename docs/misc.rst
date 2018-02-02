=============
Miscellaneous
=============


Special
=============

Embedded
--------

Embeds a struct into the enclosing struct, merging fields. Can also embed sequences into sequences.

.. warning:: 

    Can only be used between Struct Sequence FocusedSeq Union, although they can be used interchangably, for example Struct can embed fields from a Sequence. 

    EmbeddedBitStruct is not currently supported (yet to be resolved).

>>> outer = Struct(
...     Embedded(Struct(
...         "data" / Bytes(4),
...     )),
... )
>>> outer.parse(b"1234")
Container(data=b'1234')

Renamed
-------

Adds a name string to a field (which by default is None). This class is only used internally and you should use the / operator instead. Naming fields is needed when working with Structs and Unions, but also sometimes with Sequences and FocusedSeq.

::

    "num"/Byte  <-->  Renamed("num",Byte)


Miscellaneous
=============

Const
-----

A constant value that is required to exist in the data and match a given value. If the value is not matching, ConstError is raised. Useful for so called magic numbers, signatures, asserting correct protocol version, etc.

>>> Const(b"IHDR").build(None)
b'IHDR'
>>> Const(b"IHDR").parse(b"JPEG")
construct.core.ConstError: expected b'IHDR' but parsed b'JPEG'

By default, Const uses a Bytes field with size mathing the value. However, other fields can also be used:

>>> Const(Int32ul, 1).build(None)
b'\x01\x00\x00\x00'

The shortcoming is that it only works if the amount and exact bytes are known in advance. To check if a "variable" data meets some criterium (not mere equality), you would need the Check class.


Computed
--------

Represents a dynamically computed value from the context. Computed does not read or write anything to the stream. It only computes a value (usually by extracting a key from a context dictionary) and returns its computed value as the result. Usually Computed fields are used for computations on the context object. Context is explained in a previous chapter. However, Computed can also produce values based on external environment, random module, or constants. For example:

>>> st = Struct(
...     "width" / Byte,
...     "height" / Byte,
...     "total" / Computed(this.width * this.height),
... )
>>> st.parse(b"12")
Container(width=49)(height=50)(total=2450)
>>> st.build(dict(width=4,height=5))
b'\x04\x05'

>>> Computed(lambda ctx: os.urandom(10)).parse(b"")
b'[\x86\xcc\xf1b\xd9\x10\x0f?\x1a'


Rebuild
-------

When there is an array separated from its length field, the Rebuild wrapper can be used to measure the length of the list when building. Note that both the `len_` and `this` expressions are used as discussed in meta chapter. Only building is affected, parsing is simply deferred to subcon.

>>> st = Struct(
...     "count" / Rebuild(Byte, len_(this.items)),
...     "items" / Byte[this.count],
... )
>>> st.build(dict(items=[1,2,3]))
b'\x03\x01\x02\x03'

When the length field is directly before the items, `PrefixedArray` can be used instead:

>>> d = PrefixedArray(Byte, Byte)
>>> d.build([1,2,3])
b'\x03\x01\x02\x03'


Default
-------

Allows to make a field have a default value, which comes handly when building a Struct from a dict with missing keys. Only building is affected, parsing is simply deferred to subcon.

>>> st = Struct("a" / Default(Byte, 0))
>>> st.build(dict(a=1))
b'\x01'
>>> st.build(dict())
b'\x00'


Check
-----

When fields are expected to be coherent in some way but integrity cannot be checked by merely comparing data with constant bytes using Const field, then a Check field can be put in place to get a key from context dict and check if the integrity is preserved. For example, maybe there is a count field (implied being non-negative but the field is signed type):

>>> st = Struct(num=Int8sb, integrity1=Check(this.num > 0))
>>> st.parse(b"\xff")
ValidationError: check failed during parsing

Or there is a collection and a count provided and the count is expected to match the collection length (which might go out of sync by mistake). Note that Rebuild is more appropriate but the check is also possible:

>>> st = Struct(count=Byte, items=Byte[this.count])
>>> st.build(dict(count=9090, items=[]))
FormatFieldError: packer '>B' error during building, given value 9090
>>> st = Struct(integrity=Check(this.count == len_(this.items)), count=Byte, items=Byte[this.count])
>>> st.build(dict(count=9090, items=[]))
ValidationError: check failed during building


Error
------

You can also explicitly raise an error, declaratively with a construct.

>>> Error.parse(b"")
ExplicitError: Error field was activated during parsing


FocusedSeq
----------

When a sequence has some fields that could be ommited like Const Padding Terminated, the user can focus on one particular field that is useful. Only one field can be focused on, and can be referred by index or name. Other fields must be able to build without a value:

>>> d = FocusedSeq(1 or "num", Const(b"MZ"), "num"/Byte, Terminated)
>>> d.parse(b"MZ\xff")
255
>>> d.build(255)
b'MZ\xff'


Numpy
-----

Numpy arrays can be preserved and retrived along with their dtype, shape and items. Otherwise, if dtype is known, you could use PrefixedArray, and if shape is known too, you could use Array. However this class is more convenient.

>>> import numpy
>>> Numpy.build(numpy.asarray([1,2,3]))
b"\x93NUMPY\x01\x00F\x00{'descr': '<i8', 'fortran_order': False, 'shape': (3,), }            \n\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00"


NamedTuple
----------

Both arrays, structs and sequences can be mapped to a namedtuple from collections module. To create a named tuple, you need to provide a name and a sequence of fields, either a string with space-separated names or a list of strings. Just like the stadard namedtuple does.

>>> NamedTuple("coord", "x y z", Byte[3]).parse(b"123")
coord(x=49, y=50, z=51)
>>> NamedTuple("coord", "x y z", Byte >> Byte >> Byte).parse(b"123")
coord(x=49, y=50, z=51)
>>> NamedTuple("coord", "x y z", "x"/Byte + "y"/Byte + "z"/Byte).parse(b"123")
coord(x=49, y=50, z=51)



Conditional
===========

Union
-----

Treats the same data as multiple constructs (similar to C union statement) so you can "look" at the data in multiple views.

When parsing, all fields read the same data bytes, but stream remains at initial offset (or rather seeks back to original position after each subcon was parsed), unless parsefrom selects a subcon by index or name. When building, the first subcon that can find an entry in the dict (or builds from None, so it does not require an entry) is automatically selected.

.. warning:: If you skip `parsefrom` parameter then stream will be left back at starting offset, not seeked to any common denominator.

>>> d = Union(0, "raw"/Bytes(8), "ints"/Int32ub[2], "shorts"/Int16ub[4], "chars"/Byte[8])
>>> d.parse(b"12345678")
Container(raw=b'12345678')(ints=[825373492, 892745528])(shorts=[12594, 13108, 13622, 14136])(chars=[49, 50, 51, 52, 53, 54, 55, 56])
>>> d.build(dict(chars=range(8)))
b'\x00\x01\x02\x03\x04\x05\x06\x07'

::

    Note that this syntax works ONLY on Python 3.6 due to ordered keyword arguments:
    >>> Union(0, raw=Bytes(8), ints=Int32ub[2], shorts=Int16ub[4], chars=Byte[8])

Select
------

Attempts to parse or build each of the subcons, in order they were provided.

>>> Select(Int32ub, CString(encoding="utf8")).build(1)
b'\x00\x00\x00\x01'
>>> Select(Int32ub, CString(encoding="utf8")).build("Афон")
b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00'

::

    Note that this syntax works ONLY on Python 3.6 due to ordered keyword arguments:
    >>> Select(num=Int32ub, text=CString(encoding="utf8"))

Optional
--------

Attempts to parse or build the subconstruct. If it fails during parsing, returns a None. If it fails during building, it puts nothing into the stream.

>>> Optional(Int64ul).parse(b"12345678")
4050765991979987505
>>> Optional(Int64ul).parse(b"")
None

>>> Optional(Int64ul).build(1)
b'\x01\x00\x00\x00\x00\x00\x00\x00'
>>> Optional(Int64ul).build(None)
b''


If
--

Parses or builds the subconstruct only if a certain condition is met. Otherwise, returns a None when parsing and puts nothing when building. The condition is a lambda that computes on the context just like in Computed examples.

>>> If(this.x > 0, Byte).build(255, x=1)
b'\xff'
>>> If(this.x > 0, Byte).build(255, x=0)
b''


IfThenElse
----------

Branches the construction path based on a given condition. If the condition is met, the ``thensubcon`` is used, otherwise the ``elsesubcon`` is used. Fields like Pass or Error can be used here. Just for your curiosity, If is just a macro around this class.

>>> IfThenElse(this.x > 0, VarInt, Byte).build(255, x=1)
b'\xff\x01'
>>> IfThenElse(this.x > 0, VarInt, Byte).build(255, x=0)
b'\xff'

Switch
------

Branches the construction based on a return value from a function. This is a more general implementation then IfThenElse.

.. warning:: You can use Embedded(Switch(...)) but not Switch(Embedded(...)). Sames applies to If and IfThenElse macros.

>>> Switch(this.n, { 1:Byte, 2:Int32ub }).build(5, n=1)
b'\x05'
>>> Switch(this.n, { 1:Byte, 2:Int32ub }).build(5, n=2)
b'\x00\x00\x00\x05'


StopIf
------

Checks for a condition after each element, and stops a Struct Sequence Range from parsing or building following elements.

>>> Struct('x'/Byte, StopIf(this.x == 0), 'y'/Byte)
>>> Sequence('x'/Byte, StopIf(this.x == 0), 'y'/Byte)
>>> GreedyRange(FocusedSeq(0, 'x'/Byte, StopIf(this.x == 0)))



Alignment and padding
=====================

Padding
-------

Adds additional null bytes (a filler) analog to Padded but without a subcon that follows it. This field can usually be anonymous inside a Struct.

>>> Padding(4).build(None)
b'\x00\x00\x00\x00'
>>> Padding(4).parse(b"****")
None

Padded
------

Appends additional null bytes after subcon to achieve a fixed length.

>>> Padded(4, Byte).build(255)
b'\xff\x00\x00\x00'
>>> Padded(this.numfield, Byte)
...

Aligned
-------

Appends additional null bytes after subcon to achieve a given modulus boundary.

>>> Aligned(4, Int16ub).build(1)
b'\x00\x01\x00\x00'
>>> Aligned(this.numfield, Int16ub)
...

AlignedStruct
-------------

Automatically aligns each member to modulus boundary. It does NOT align entire Struct, but each member separately.

>>> AlignedStruct(4, "a"/Int8ub, "b"/Int16ub).build(dict(a=1,b=5))
b'\x01\x00\x00\x00\x00\x05\x00\x00'
