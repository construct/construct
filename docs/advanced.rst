============
The Basics, part 2
============


Integers and floats
===================

Basic computer science 101. All integers follow the Int{8,16,24,32,64}{u,s}{b,l,n} and floats follow the Float{16,32,64}{b,l} naming patterns. Endianness can be either big-endian, little-endian or native. Integers can be signed or unsigned (non-negative only). Floats do not have a unsigned type.

>>> Int64sl.build(500)
b'\xf4\x01\x00\x00\x00\x00\x00\x00'
>>> Int64sl.build(-23)
b'\xe9\xff\xff\xff\xff\xff\xff\xff'

Few fields have aliases, Byte among integers and Single among floats.

::

    Byte    <-->  Int8ub
    Short   <-->  Int16ub
    Int     <-->  Int32ub
    Long    <-->  Int64ub
    Half    <-->  Float16b
    Single  <-->  Float32b
    Double  <-->  Float64b

Integers can also be variable-length encoded for compactness. Google invented a popular encoding:

>>> VarInt.build(1234567890)
b'\xd2\x85\xd8\xcc\x04'

Long integers (or those of particularly odd sizes) can be encoded using a fixed-sized `BytesInteger`. Here is a 128-bit integer.

>>> BytesInteger(16).build(255)
b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff'

Some numerical classes are implemented using `struct` module, others use BytesInteger field.

>>> FormatField("<","l").build(1)
b'\x01\x00\x00\x00'
>>> BytesInteger(4, swapped=True).build(1)
b'\x01\x00\x00\x00'



Bytes and bits
==============

.. warning::

    Python 3 known problem:

    Unprefixed string literals like "data" are on Python 3 interpreted as unicode. This casues failures when using fields like `Bytes`.

"Strings" of bytes (`str` in PY2 and `bytes` in PY3) can be moved around as-is. Bits are discussed in a later chapter.

>>> Bytes(5).build(b"12345")
b'12345'
>>> Bytes(5).parse(b"12345")
b'12345'

Bytes can also be consumed until end of stream. Tunneling is discussed in a later chapter.

>>> GreedyBytes.parse(b"39217839219...")
b'39217839219...'


Strings
========

.. warning::

    Python 2 known problem:

    Unprefixed string literals like "text" are on Python 2 interpreted as bytes. This causes failures when using fields that operate on unicode objects only like String* classes.

.. note::

    Encodings like UTF8 UTF16 UTF32 (including little-endian) work fine with all String* classes. However two of them, PaddedString and CString, support only encodings listed explicitly in :class:`~construct.core.possiblestringencodings` .

PaddedString is a fixed-length construct that pads built string with null bytes, and strips those same null bytes when parsing. Strings can also be trimmed when building. If you supply a too long string, the construct will chop it off apart instead of raising a StringError.

To be honest, using this class is not recommended. It is provided only for ancient data formats.

>>> PaddedString(10, "utf8").build("Афон")
b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00\x00'

PascalString is a variable length string that is prefixed by a length field. This scheme was invented in Pascal language that put Byte field instead of C convention of appending null \\0 byte at the end. Note that the length field does not need to be Byte, and can also be variable length itself, as shown below. VarInt is recommended when designing new protocols.

>>> PascalString(VarInt, "utf8").build("Афон")
b'\x08\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd'

CString is another string representation, that always ends with a null \\0 terminating byte at the end. This scheme was invented in C language and is known in the computer science community very well. One of the authors, Kernighan or Ritchie, admitted that it was one of the most regretable design decisions in history.

>>> CString("utf8").build(b"hello")
b'hello\x00'

Last would be GreedyString which does the same thing as GreedyBytes, plus encoding. It reads until the end of stream and then decodes data using specified encoding. Greedy* classes are usually used with tunneling constructs, which are discussed in a later chapter.

>>> GreedyString("utf8").parse(b"329817392189")
'329817392189'


Mappings
==========

Booleans are flags:

>>> Flag.parse(b"\x01")
True
>>> Flag.build(True)
b'\x01'

Enum translates between string labels and integer values. Parsing returns a string (if value has mapping) but returns an integer otherwise. This creates no problem since Enum can build from string and integer representations just the same. Note that resulting string has a special implementation, so it can be converted into a corresponding integer.

>>> d = Enum(Byte, one=1, two=2, four=4, eight=8)
>>> d.parse(b"\x01")
'one'
>>> int(d.parse(b"\x01"))
1
>>> d.parse(b"\xff")
255
>>> int(d.parse(b"\xff"))
255

Note that string values can also be obtained using attribute members. 

>>> d.build(d.one or "one" or 1)
b'\x01'
>>> d.one
'one'

FlagsEnum decomposes an integer value into a set of string labels:

>>> d = FlagsEnum(Byte, one=1, two=2, four=4, eight=8)
>>> d.parse(b"\x03")
Container(one=True, two=True, four=False, eight=False)
>>> d.build(dict(one=True,two=True))
b'\x03'

Note that string values can also be obtained using attribute members. 

>>> d.build(d.one|d.two or "one|two" or 1|2)
b'\x03'

Both Enum and FlagsEnum support merging labels from IntEnum and IntFlag (enum34 module):

::

    import enum
    class E(enum.IntEnum or enum.IntFlag):
        one = 1
        two = 2

    Enum(Byte, E) <--> Enum(Byte, one=1, two=2)
    FlagsEnum(Byte, E) <--> FlagsEnum(Byte, one=1, two=2)

For completeness, there is also Mapping class, but using it is not recommended. Consider it a last resort.

::

    >>> x = object
    >>> d = Mapping(Byte, {x:0})
    >>> d.parse(b"\x00")
    x
    >>> d.build(x)
    b'\x00'


Processing files
===========================

.. warning::

    Python 3 known problem:

    Opening a file without mode like ``open(filename)`` implies text mode, which cannot be parsed or build.

Constructs can parse both in-memory data (bytes) and binary files:

>>> d = Struct(...)
>>> d.parse(bytes(1000))

>>> with open('/dev/zero', 'rb') as f:
...     d.parse_stream(f)

>>> d.parse_file('/dev/zero')


Documenting fields
========================

Top-most structures should have elaborate descriptions, documenting who made them and from what specifications. Individual fields can also have docstrings, but field names should be descriptive, not the docstrings.

::

    """
    Full docstring with autor, email, links to RFC-alike pages.
    """ * \
    Struct(
        "title" / CString("utf8"),
        Padding(2) * "reserved, see 8.1",
    )
