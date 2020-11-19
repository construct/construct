=================
Tunneling tactics
=================


Obtaining raw bytes
-------------------

When some value needs to be processed as both a parsed object and its raw bytes representation, both of these can be obtained using RawCopy. You can build from either the object or raw bytes as well. Dict also happen to contain the stream offsets, if you need to know at which position it resides in the stream or if you need to know its size in bytes.

>>> d = RawCopy(Byte)
>>> d.parse(b"\xff")
Container(data=b'\xff', value=255, offset1=0, offset2=1, length=1)
>>> d.build(dict(data=b"\xff"))
b'\xff'
>>> d.build(dict(value=255))
b'\xff'


Endianness
----------

When little endianness is needed, either use integer fields like `Int*l` or `BytesInteger(swapped=True)` or swap bytes of an arbitrary field:

::

    Int24ul <--> ByteSwapped(Int24ub) <--> BytesInteger(3, swapped=True) <--> ByteSwapped(BytesInteger(3))

>>> Int24ul.build(0x010203)
b'\x03\x02\x01'

When bits within each byte need to be swapped, there is another wrapper:

>>> d = Bitwise(Bytes(8))
>>> d.parse(b"\x01")
b'\x00\x00\x00\x00\x00\x00\x00\x01'
>>> d = BitsSwapped(Bitwise(Bytes(8)))
>>> d.parse(b"\x01")
b'\x01\x00\x00\x00\x00\x00\x00\x00'

In case that endianness is determined at parse/build time, you can pass endianness (`swapped` parameter) by the context:

>>> d = BytesInteger(2, swapped=this.swapped)
>>> d.build(1, swapped=True)
b'\x01\x00'
>>> d = BitsInteger(16, swapped=this.swapped)
>>> d.build(1, swapped=True)
b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

Working with bytes subsets
--------------------------------------------

Greedy* constructs consume as much data as possible. This is convenient when building from a list of unknown length but becomes a problem when parsing it back and the list needs to be separated from following data. This can be achieved either by prepending a byte count (see Prefixed) or by prepending an element count (see PrefixedArray):

VarInt encoding is recommended because it is both compact and never overflows. Also and optionally, the length field can include its own size. If so, length field must be of fixed size.

>>> d = Prefixed(VarInt, GreedyRange(Int32ul))
>>> d.parse(b"\x08abcdefgh")
[1684234849, 1751606885]

>>> d = PrefixedArray(VarInt, Int32ul)
>>> d.parse(b"\x02abcdefgh")
[1684234849, 1751606885]

There are also other means of restricting constructs to substreamed data. All 3 classes below work by substreaming data, meaning the subcon is not given the original stream but a new BytesIO made out of pre-read bytes. This allows Greedy* fields to work properly.

FixedSized consumes a specified amount and then exposes inner construct to a new stream build out of those bytes. When building, it appends a padding to make a specified total.

>>> d = FixedSized(10, Byte)
>>> d.parse(b'\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00')
255

FixedSized is similar to Padded. The results seem identical but the implementation is entirely different. FixedSized uses a substream and Padded uses stream.tell(). Therefore:

::

    # valid
    FixedSized(10, GreedyBytes)
    # UNSAFE
    Padded(10, GreedyBytes)

NullTerminated consumes bytes up to first occurance of the term. When building, it just writes the subcon followed by the term.

>>> d = NullTerminated(Byte)
>>> d.parse(b'\xff\x00')
255

NullStripped consumes bytes till EOF, and for that matter should be restricted by Prefixed FixedSized etc, and then strips paddings. Subcon is parsed using a new stream build using those stripped bytes. When building, it just builds the subcon as-is.

>>> d = NullStripped(Byte)
>>> d.parse(b'\xff\x00\x00')
255


Working with different bytes
--------------------------------------------------

RestreamData allows you to insert a field that parses some data that came either from some other field, from the context (like Bytes) or some literal hardcoded value in your code. Comes handy when for example, you are testing a large struct by parsing null bytes, but some field is unable to parse null bytes (like Numpy). It substitutes the stream with another data for the purposes of parsing a particular field in a Struct.

Instead of data itself (bytes object) you can reference another stream (taken from the context like `this._stream`) or use a Construct that parses into bytes (including those exposed via context like `this._subcons.field`).

::

    >>> d = RestreamData(b"\x01", Int8ub)
    >>> d.parse(b"")
    1
    >>> d.build(0)
    b''

::

    >>> d = RestreamData(NullTerminated(GreedyBytes), Int16ub)
    >>> d.parse(b"\x01\x02\x00")
    0x0102

    >>> d = RestreamData(FixedSized(2, GreedyBytes), Int16ub)
    >>> d.parse(b"\x01\x02\x00")
    0x0102

::

    d = Struct(
        "numpy_data" / Computed(b"\x93NUMPY\x01\x00F\x00{'descr': '<i8', 'fortran_order': False, 'shape': (3,), }            \n\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00"),
        "numpy1" / RestreamData(this.numpy_data, Numpy),
        "numpy2" / Numpy, # this would fail when parsing null bytes
    )
    d.parse(bytes(1000))


Transformed allows you to process data before it gets into subcon (and after data left it) using simple bytes-to-bytes transformations. In fact, all core classes (like Bitwise) that use Restreamed also use Transformed. The only difference is that Transformed prefetches all bytes and transforms them in advance, but Restreamed fetches a unit at a time (few bytes usually). Therefore Restreamed can handle variable-sized fields, while Transformed works only with fixed-sized fields. For example:

::

    >>> d = Transformed(Bytes(16), bytes2bits, 2, bits2bytes, 2)
    >>> d.parse(b"\x00\x00")
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

Transformed can also process unknown amount of bytes, if that amount is entire data. Decode amount and encode amount are then set to None.

::

    >>> d = Transformed(GreedyBytes, bytes2bits, None, bits2bytes, None)
    >>> d.parse(b"\x00\x00")
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

::

    # Bitwise implementation
    try:
        size = subcon.sizeof()
        macro = Transformed(subcon, bytes2bits, size//8, bits2bytes, size//8)
    except SizeofError:
        macro = Restreamed(subcon, bytes2bits, 1, bits2bytes, 8, lambda n: n//8)

Restreamed is similar to Transformed, but the main difference is that Transformed requires fixed-sized subcon because it reads all bytes in advance, processes them, and then feeds them to the subcon. Restreamed on the other hand, reads few bytes at a time, the minimum amount on each stream read. Since both are used mostly internally, there is no tutorial how to use it, other than this short code above.


Processing data with XOR and ROL
----------------------------------------

This chapter is mostly relevant to KaitaiStruct compiler implementation, as following constructs exist mostly for that purpose.

Data can be transformed by XORing with a single or several bytes, and the key can also be taken from the context at runtime. Key can be of any positive length.

>>> d = ProcessXor(0xf0 or b'\xf0', Int16ub)
>>> d.parse(b"\x00\xff")
0xf00f
>>> d.sizeof()
2

Data can also be rotated (cycle shifted). Rotation is to the left on parsing, and to the right on building. Amount is in bits, and can be negative to make rotation right instead of left. Group size defines the size of chunks to which rotation is applied.

>>> d = ProcessRotateLeft(4, 1, Int16ub)
>>> d.parse(b'\x0f\xf0')
0xf00f
>>> d = ProcessRotateLeft(4, 2, Int16ub)
>>> d.parse(b'\x0f\xf0')
0xff00
>>> d.sizeof()
2

Note that the classes read entire stream till EOF so they should be wrapped in FixedSized Prefixed etc unless you actually want to process the entire remaining stream.


Compression and checksuming
----------------------------------------

Data can be easily checksummed. Note that checksum field does not need to be Bytes, and lambda may return an integer or otherwise.

::

    import hashlib
    d = Struct(
        "fields" / RawCopy(Struct(
            Padding(1000),
        )),
        "checksum" / Checksum(Bytes(64),
            lambda data: hashlib.sha512(data).digest(),
            this.fields.data),
    )
    d.build(dict(fields=dict(value={})))

::

    import hashlib
    d = Struct(
        "offset" / Tell,
        "checksum" / Padding(64),
        "fields" / RawCopy(Struct(
            Padding(1000),
        )),
        "checksum" / Pointer(this.offset, Checksum(Bytes(64),
            lambda data: hashlib.sha512(data).digest(),
            this.fields.data)),
    )
    d.build(dict(fields=dict(value={})))


Data can also be easily compressed. Supported encodings include zlib/gzip/bzip2/lzma and entire codecs module. When parsing, entire stream is consumed. When building, puts compressed bytes without marking the end. This construct should be used with :class:`~construct.core.Prefixed` or entire stream.

>>> d = Prefixed(VarInt, Compressed(GreedyBytes, "zlib"))
>>> d.build(bytes(100))
b'\x0cx\x9cc`\xa0=\x00\x00\x00d\x00\x01'
