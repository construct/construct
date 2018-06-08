=============
Miscellaneous
=============


Special
=============

Embedded
--------

Special wrapper that allows outer multiple-subcons construct to merge fields from another multiple-subcons construct. Embedded does not change a field, only wraps it like a candy with a flag.

.. warning::

    Can only be used between Struct Sequence FocusedSeq Union LazyStruct, although they can be used interchangably, for example Struct can embed fields from a Sequence. There is also :class:`~construct.core.EmbeddedSwitch` macro that pseudo-embeds a Switch. Its not possible to embed IfThenElse.

>>> outer = Struct(
...     Embedded(Struct(
...         "data" / Bytes(4),
...     )),
... )
>>> outer.parse(b"1234")
Container(data=b'1234')

Renamed
-------

Adds a name string to a field (which by default is None). This class is only used internally and you should use the / and * operators instead. Naming fields is needed when working with Structs and Unions, but also sometimes with Sequences and FocusedSeq.

::

    "num" / Byte       <-->  Renamed(Byte, newname="num")
    Byte * "comment"   <-->  Renamed(Byte, newdocs="comment")
    Byte * parsedhook  <-->  Renamed(byte, newparsed=parsedhook)


Miscellaneous
=============

Const
-----

A constant value that is required to exist in the data and match a given value. If the value is not matching, ConstError is raised. Useful for so called magic numbers, signatures, asserting correct protocol version, etc.

>>> d = Const(b"IHDR")
>>> d.build(None)
b'IHDR'
>>> d.parse(b"JPEG")
construct.core.ConstError: expected b'IHDR' but parsed b'JPEG'

By default, Const uses a Bytes field with size matching the value. However, other fields can also be used:

>>> d = Const(255, Int32ul)
>>> d.build(None)
b'\xff\x00\x00\x00'

The shortcoming is that it only works if the amount and exact bytes are known in advance. To check if a "variable" data meets some criterium (not mere equality), you would need the :class:`~construct.core.Check` class. There is also :class:`~construct.core.OneOf` and :class:`~construct.core.NoneOf` class.

Const also accepts an `exception` keyword argument to override `ConstError`.

Computed
--------

Represents a value dynamically computed from the context. Computed does not read or write anything to the stream. It only computes a value (usually by extracting a key from a context dictionary) and returns its computed value as the result. Usually Computed fields are used for computations on the context dict. Context is explained in a previous chapter. However, Computed can also produce values based on external environment, random module, or constants. For example:

>>> st = Struct(
...     "width" / Byte,
...     "height" / Byte,
...     "total" / Computed(this.width * this.height),
... )
>>> st.parse(b"12")
Container(width=49, height=50, total=2450)
>>> st.build(dict(width=4,height=5))
b'\x04\x05'

>>> d = Computed(lambda ctx: os.urandom(10))
>>> d.parse(b"")
b'[\x86\xcc\xf1b\xd9\x10\x0f?\x1a'


Index
-------

Fields that are inside Array GreedyRange RepeatUntil can reference their index within the outer list. This is being effectuated by repeater class maintaining a context entry "_index" and updating it between each iteration. Note that some classes do context nesting (like Struct), but they do copy the key over. You can access the key using Index class, or refer to the context entry directly, using `this._index` expression. Some constructions are only possible with direct method, when you want to use the index as parameter of a construct, like in `Bytes(this._index+1)`.


>>> d = Array(3, Index)
>>> d.parse(b"")
[0, 1, 2]
>>> d = Array(3, Struct("i" / Index))
>>> d.parse(b"")
[Container(i=0), Container(i=1), Container(i=2)]

>>> d = Array(3, Computed(this._index+1))
>>> d.parse(b"")
[1, 2, 3]
>>> d = Array(3, Struct("i" / Computed(this._index+1)))
>>> d.parse(b"")
[Container(i=1), Container(i=2), Container(i=3)]


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

>>> st = Struct(
...     "a" / Default(Byte, 0),
... )
>>> st.build(dict(a=1))
b'\x01'
>>> st.build(dict())
b'\x00'


Check
-----

When fields are expected to be coherent in some way but integrity cannot be checked by merely comparing data with constant bytes using Const field, then a Check field can be put in place to get a key from context dict and check if the integrity is preserved. For example, maybe there is a count field (implied being non-negative but the field is signed type):

>>> st = Struct(
...     "num" / Int8sb,
...     "integrity1" / Check(this.num > 0),
... )
>>> st.parse(b"\xff")
ValidationError: check failed during parsing

Or there is a collection and a count provided and the count is expected to match the collection length (which might go out of sync by mistake). Note that Rebuild is more appropriate but the check is also possible:

>>> st = Struct(
...     "count" / Byte,
...     "items" / Byte[this.count],
... )
>>> st.build(dict(count=9090, items=[]))
FormatFieldError: packer '>B' error during building, given value 9090
>>> st = Struct(
...     "integrity" / Check(this.count == len_(this.items)), 
...     "count" / Byte, 
...     "items" / Byte[this.count],
... )
>>> st.build(dict(count=9090, items=[]))
ValidationError: check failed during building

Check also accepts an `exception` keyword argument to override `ValidationError`.

Error
------

You can also explicitly raise an error, declaratively with a construct.

>>> Error.parse(b"")
ExplicitError: Error field was activated during parsing


FocusedSeq
----------

When a sequence has some fields that could be ommited like Const Padding Terminated, the user can focus on one particular field that is useful. Only one field can be focused on, and can be referred by index or name. Other fields must be able to build without a value:

>>> d = FocusedSeq(1 or "num", 
...     Const(b"MZ"),
...     "num" / Byte,
...     Terminated,
... )
>>> d.parse(b"MZ\xff")
255
>>> d.build(255)
b'MZ\xff'


Pickled
----------

For convenience, arbitrary Python objects can be preserved using the famous pickle protocol. Almost any type can be pickled, but you have to understand that pickle uses its own (homebrew) protocol that is not a standard outside Python. Therefore, you can forget about parsing the binary blobs using other languages. There are also some minor considerations, like pickle protocol requiring Python 3.0 version or so. Its useful, but it automates things beyond your understanding.

>>> obj = [1, 2.3, {}]
>>> Pickled.build(objobj)
b'\x80\x03]q\x00(K\x01G@\x02ffffff}q\x01e.'
>>> Pickled.parse(_)
[1, 2.3, {}]


Numpy
----------

Numpy arrays can be preserved and retrived along with their element type (dtype), dimensions (shape) and items. This is effectuated using the Numpy binary protocol, so parsing blobs produced by this class with other langagues (or other frameworks than Numpy for that matter) is not possible. Otherwise you could use PrefixedArray but this class is more convenient.

>>> import numpy
>>> obj = numpy.asarray([1,2,3])
>>> Numpy.build(obj)
b"\x93NUMPY\x01\x00F\x00{'descr': '<i8', 'fortran_order': False, 'shape': (3,), }            \n\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00"


NamedTuple
----------

Both arrays, structs and sequences can be mapped to a namedtuple from collections module. To create a named tuple, you need to provide a name and a sequence of fields, either a string with space-separated names or a list of strings. Just like the stadard namedtuple does.

>>> d = NamedTuple("coord", "x y z", Byte[3])
>>> d = NamedTuple("coord", "x y z", Byte >> Byte >> Byte)
>>> d = NamedTuple("coord", "x y z", "x"/Byte + "y"/Byte + "z"/Byte)
>>> d.parse(b"123")
coord(x=49, y=50, z=51)


Timestamp
----------

Datetimes can be represented using Timestamp class. It supports modern formats and even MSDOS one. Note however that this class is not guaranteed to provide "exact" accurate values, due to several reasons explained in the docstring.

>>> d = Timestamp(Int64ub, 1., 1970)
>>> d.parse(b'\x00\x00\x00\x00ZIz\x00')
<Arrow [2018-01-01T00:00:00+00:00]>
>>> d = Timestamp(Int32ub, "msdos", "msdos")
>>> d.parse(b'H9\x8c"')
<Arrow [2016-01-25T17:33:04+00:00]>


Hex and HexDump
------------------

Integers and bytes can be displayed in hex form, for convenience. Note that parsing still results in int-alike and bytes-alike objects, and those results are unmodified, the hex form appears only when pretty-printing. If you want to obtain hexlified bytes, you need to use binascii.hexlify() on parsed results.

>>> d = Hex(Int32ub)
>>> obj = d.parse(b"\x00\x00\x01\x02")
>>> obj
258
>>> print(obj)
0x00000102

>>> d = Hex(GreedyBytes)
>>> obj = d.parse(b"\x00\x00\x01\x02")
>>> obj
b'\x00\x00\x01\x02'
>>> print(obj)
unhexlify('00000102')

>>> d = Hex(RawCopy(Int32ub))
>>> obj = d.parse(b"\x00\x00\x01\x02")
>>> obj
{'data': b'\x00\x00\x01\x02',
 'length': 4,
 'offset1': 0,
 'offset2': 4,
 'value': 258}
>>> print(obj)
unhexlify('00000102')

Another variant is hexdumping, which shows both ascii representaion, hexadecimal representation, and offsets. Functionality is identical.

>>> d = HexDump(GreedyBytes)
>>> obj = d.parse(b"\x00\x00\x01\x02")
>>> obj
b'\x00\x00\x01\x02'
>>> print(obj)
hexundump('''
0000   00 00 01 02                                       ....
''')

>>> d = HexDump(RawCopy(Int32ub))
>>> obj = d.parse(b"\x00\x00\x01\x02")
>>> obj
{'data': b'\x00\x00\x01\x02',
 'length': 4,
 'offset1': 0,
 'offset2': 4,
 'value': 258}
>>> print(obj)
hexundump('''
0000   00 00 01 02                                       ....
''')


Conditional
===========

Union
-----

Treats the same data as multiple constructs (similar to C union statement) so you can "look" at the data in multiple views.

When parsing, all fields read the same data bytes, but stream remains at initial offset (or rather seeks back to original position after each subcon was parsed), unless parsefrom selects a subcon by index or name. When building, the first subcon that can find an entry in the dict (or builds from None, so it does not require an entry) is automatically selected.

.. warning:: If you skip `parsefrom` parameter then stream will be left back at starting offset, not seeked to any common denominator.

>>> d = Union(0, 
...     "raw" / Bytes(8),
...     "ints" / Int32ub[2],
...     "shorts" / Int16ub[4],
...     "chars" / Byte[8],
... )
>>> d.parse(b"12345678")
Container(raw=b'12345678', ints=[825373492, 892745528], shorts=[12594, 13108, 13622, 14136], chars=[49, 50, 51, 52, 53, 54, 55, 56])
>>> d.build(dict(chars=range(8)))
b'\x00\x01\x02\x03\x04\x05\x06\x07'

::

    Note that this syntax works ONLY on CPython 3.6 (and PyPy any version) due to ordered keyword arguments. There is similar syntax for many other constructs.
    >>> Union(0, raw=Bytes(8), ints=Int32ub[2], shorts=Int16ub[4], chars=Byte[8])

Select
------

Attempts to parse or build each of the subcons, in order they were provided.

::

    >>> d = Select(Int32ub, CString("utf8"))
    >>> d.build(1)
    b'\x00\x00\x00\x01'
    >>> d.build(u"Афон")
    b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00'

::

    Note that this syntax works ONLY on CPython 3.6 (and PyPy any version) due to ordered keyword arguments. There is similar syntax for many other constructs.
    >>> Select(num=Int32ub, text=CString("utf8"))

Optional
--------

Attempts to parse or build the subconstruct. If it fails during parsing, returns a None. If it fails during building, it puts nothing into the stream.

>>> d = Optional(Int64ul)
>>> d.parse(b"12345678")
4050765991979987505
>>> d.parse(b"")
None

>>> d.build(1)
b'\x01\x00\x00\x00\x00\x00\x00\x00'
>>> d.build(None)
b''


If
--

Parses or builds the subconstruct only if a certain condition is met. Otherwise, returns a None when parsing and puts nothing when building. The condition is a lambda that computes on the context just like in Computed examples.

>>> d = If(this.x > 0, Byte)
>>> d.build(255, x=1)
b'\xff'
>>> d.build(255, x=0)
b''


IfThenElse
----------

Branches the construction path based on a given condition. If the condition is met, the ``thensubcon`` is used, otherwise the ``elsesubcon`` is used. Fields like Pass and Error can be used here. Just for your curiosity, If is just a macro around this class.

>>> d = IfThenElse(this.x > 0, VarInt, Byte)
>>> d.build(255, x=1)
b'\xff\x01'
>>> d.build(255, x=0)
b'\xff'

In particular, you can use different subcons for parsing and building. The context entries have boolean values and always exist (sizeof has both values as False). For convenience, those two entries are duplicated in Struct Sequence FocusedSeq Union nested contexts. You dont need to reach for the top-most entry. This comes handy when using hackish constructs to achieve some complex semantics that are not available in the core library.

::

    Struct(
        If(this._parsing, ...),
        If(this._building, ...),
    )


Switch
------

Branches the construction based on a return value from a context function. This is a more general implementation than IfThenElse. If no cases match the actual, it just passes successfully, although that behavior can be overriden.

>>> d = Switch(this.n, { 1:Int8ub, 2:Int16ub, 4:Int32ub })
>>> d.build(5, n=1)
b'\x05'
>>> d.build(5, n=4)
b'\x00\x00\x00\x05'

>>> d = Switch(this.n, {}, default=Byte)
>>> d.parse(b"\x01", n=255)
1
>>> d.build(1, n=255)
b"\x01"


EmbeddedSwitch
----------------

Macro that simulates embedding Switch, which under new embedding semantics is not possible. This macro does NOT produce a Switch. It generates classes that behave the same way as you would expect from embedded Switch, only that. Instance created by this macro CAN be embedded.

All fields should have unique names. Otherwise fields that were not selected during parsing may return None and override other fields context entries that have same name. This is because `If` field returns None value if condition is not met, but the Struct inserts that None value into the context entry regardless.

::

    d = EmbeddedSwitch(
        Struct(
            "type" / Byte,
        ),
        this.type,
        {
            0: Struct("name" / PascalString(Byte, "utf8")),
            1: Struct("value" / Byte),
        }
    )

    # generates essentially following
    d = Struct(
        "type" / Byte,
        "name" / If(this.type == 0, PascalString(Byte, "utf8")),
        "value" / If(this.type == 1, Byte),
    )

    # both parse like following
    >>> d.parse(b"\x00\x00")
    Container(type=0, name=u'', value=None)
    >>> d.parse(b"\x01\x00")
    Container(type=1, name=None, value=0)


StopIf
------

Checks for a condition after each element, and stops a Struct Sequence GreedyRange from parsing or building following elements.

::

    Struct('x'/Byte, StopIf(this.x == 0), 'y'/Byte)
    Sequence('x'/Byte, StopIf(this.x == 0), 'y'/Byte)
    GreedyRange(FocusedSeq(0, 'x'/Byte, StopIf(this.x == 0)))


Alignment and padding
=====================

Padding
-------

Adds additional null bytes (a filler) analog to Padded but without a subcon that follows it. This field is usually anonymous inside a Struct. Internally this is just Padded(Pass).

>>> d = Padding(4) or Padded(4, Pass)
>>> d.parse(b"****")
None
>>> d.build(None)
b'\x00\x00\x00\x00'


Padded
------

Appends additional null bytes after subcon to achieve a fixed length. Note that implementation of this class uses stream.tell() to find how many bytes were written by the subcon.

>>> d = Padded(4, Byte)
>>> d.build(255)
b'\xff\x00\x00\x00'

Similar effect can be obtained using FixedSized, but the implementation is rather different. FixedSized uses a separate BytesIO, which means that Greedy* fields should work properly with it (and fail with Padded) and also the stream does not need to be tellable (like pipes sockets etc).


Aligned
-------

Appends additional null bytes after subcon to achieve a given modulus boundary. This implementation also uses stream.tell().

>>> d = Aligned(4, Int16ub)
>>> d.build(1)
b'\x00\x01\x00\x00'


AlignedStruct
-------------

Automatically aligns each member to modulus boundary. It does NOT align entire Struct, but each member separately.

>>> d = AlignedStruct(4, "a"/Int8ub, "b"/Int16ub)
>>> d.build(dict(a=0xFF,b=0xFFFF))
b'\xff\x00\x00\x00\xff\xff\x00\x00'
