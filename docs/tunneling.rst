=================
Tunneling tactics
=================


Obtaining raw bytes
-------------------

When some value needs to be processed as both a parsed object and its raw bytes representation, both of these can be obtained using RawCopy. You can build from either the object or raw bytes as well. Dict also happen to contain the stream offsets, if you need to know at which position it resides in the stream or if you need to know its size in bytes.

When building, if both the ``"value"`` and ``"data"`` keys are present, then the ``"data"`` key is used and the ``"value"`` key is ignored. This is undesirable in the case that you parse some data for the purpose of modifying it and writing it back; in this case, delete the ``"data"`` key when modifying the ``"value"`` key to correctly rebuild the former.

>>> d = RawCopy(Byte)
>>> d.parse(b"\xff")
Container(data=b'\xff', value=255, offset1=0, offset2=1, length=1)
>>> d.build(dict(data=b"\xff"))
b'\xff'
>>> d.build(dict(value=255))
b'\xff'


Endianness
----------

When little endianness is needed, either use integer fields like ``Int*l`` or ``BytesInteger(swapped=True)`` or swap bytes of an arbitrary field:

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

In case that endianness is determined at parse/build time, you can pass endianness (``swapped`` parameter) by the context:

>>> d = BytesInteger(2, swapped=this.swapped)
>>> d.build(1, swapped=True)
b'\x01\x00'
>>> d = BitsInteger(16, swapped=this.swapped)
>>> d.build(1, swapped=True)
b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'


Working with bytes subsets
--------------------------------------------

``Greedy*`` constructs consume as much data as possible, they read until EOF. This is convenient when building from a list of unknown length but becomes a problem when parsing it back and the list needs to be separated from following data. This can be achieved either by prepending a byte count (see ``Prefixed``) or by prepending an element count (see ``PrefixedArray``):

``VarInt`` encoding is recommended because it is both compact and never overflows. Also and optionally, the length field can include its own size. If so, length field must be of fixed size.

>>> d = Prefixed(VarInt, GreedyRange(Int32ul))
>>> d.parse(b"\x08abcdefgh")
ListContainer([1684234849, 1751606885])

>>> d = PrefixedArray(VarInt, Int32ul)
>>> d.parse(b"\x02abcdefgh")
ListContainer([1684234849, 1751606885])

There are also other means of restricting constructs to substreamed data. All 3 classes below work by substreaming data, meaning the subcon is not given the original stream but a new ``BytesIO`` made out of pre-read bytes. This allows ``Greedy*`` fields to work properly.

``FixedSized`` consumes a specified amount and then exposes inner construct to a new stream built out of those bytes. When building, it appends a padding to make a specified total.

>>> d = FixedSized(10, Byte)
>>> d.parse(b'\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00')
255

``FixedSized`` is similar to ``Padded``. The results seem identical but the implementation is entirely different. ``FixedSized`` uses a substream and ``Padded`` uses stream.tell(). Therefore:

::

    # valid
    FixedSized(10, GreedyBytes)
    # UNSAFE
    Padded(10, GreedyBytes)

``NullTerminated`` consumes bytes up to first occurance of the term. When building, it just writes the subcon followed by the term.

>>> d = NullTerminated(Byte)
>>> d.parse(b'\xff\x00')
255

.. warning::

    The term can be multiple bytes, to support string classes with UTF16/32 encodings for example. Be warned however: as reported in Issue #1046, the data read must be a multiple of the term length and the term must start at a unit boundary, otherwise strange things happen when parsing.

``NullStripped`` consumes bytes till EOF, and for that matter should be restricted by ``Prefixed``, ``FixedSized`` etc, and then strips paddings. Subcon is parsed using a new stream built using those stripped bytes. When building, it just builds the subcon as-is.

>>> d = NullStripped(Byte)
>>> d.parse(b'\xff\x00\x00')
255


Working with different bytes
--------------------------------------------------

``RestreamData`` allows you to insert a field that parses some data that came either from some other field, from the context (like ``Bytes``) or some literal hardcoded value in your code. Comes handy when for example, you are testing a large struct by parsing null bytes, but some field is unable to parse null bytes (like ``Numpy``). It substitutes the stream with another data for the purposes of parsing a particular field in a ``Struct``.

Instead of data itself (bytes object) you can reference another stream (taken from the context like ``this._stream``) or use a Construct that parses into bytes (including those exposed via context like ``this._subcons.field``).

::

    >>> d = RestreamData(b"\x01", Int8ub)
    >>> d.parse(b"")
    1
    >>> d.build(0)
    b''

::

    >>> d = RestreamData(NullTerminated(GreedyBytes), Int16ub)
    >>> d.parse(b"\x01\x02\x00")
    258

    >>> d = RestreamData(FixedSized(2, GreedyBytes), Int16ub)
    >>> d.parse(b"\x01\x02\x00")
    258

::

    d = Struct(
        "numpy_data" / Computed(b"\x93NUMPY\x01\x00F\x00{'descr': '<i8', 'fortran_order': False, 'shape': (3,), }            \n\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00"),
        "numpy1" / RestreamData(this.numpy_data, Numpy),
        "numpy2" / Numpy, # this would fail when parsing null bytes
    )
    d.parse(...)


``Transformed`` allows you to process data before it gets into subcon (and after data left it) using simple bytes-to-bytes transformations. In fact, all core classes (like ``Bitwise``) that use ``Restreamed`` also use ``Transformed``. The only difference is that ``Transformed`` prefetches all bytes and transforms them in advance, but ``Restreamed`` fetches a unit at a time (few bytes usually). Therefore ``Restreamed`` can handle variable-sized fields, while ``Transformed`` works only with fixed-sized fields. For example:

::

    >>> from construct.lib import *
    >>> d = Transformed(Bytes(16), bytes2bits, 2, bits2bytes, 2)
    >>> d.parse(b"\x00\x00")
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

``Transformed`` can also process unknown amount of bytes, if that amount is entire data. Decode amount and encode amount are then set to None.

::

    >>> from construct.lib import *
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

``Restreamed`` is similar to ``Transformed``, but the main difference is that ``Transformed`` requires fixed-sized subcon because it reads all bytes in advance, processes them, and then feeds them to the subcon. ``Restreamed`` on the other hand, reads few bytes at a time, the minimum amount on each stream read. Since both are used mostly internally, there is no tutorial how to use it, other than this short code above.


Processing data with XOR and ROL
----------------------------------------

This chapter is mostly relevant to KaitaiStruct compiler implementation, as following constructs exist mostly for that purpose.

Data can be transformed by XORing with a single or several bytes, and the key can also be taken from the context at runtime. Key can be of any positive length.

>>> d = ProcessXor(0xf0 or b'\xf0', Int16ub)
>>> print(hex(d.parse(b"\x00\xff")))
0xf00f
>>> d.sizeof()
2

Data can also be rotated (cycle shifted). Rotation is to the left on parsing, and to the right on building. Amount is in bits, and can be negative to make rotation right instead of left. Group size defines the size of chunks to which rotation is applied.

>>> d = ProcessRotateLeft(4, 1, Int16ub)
>>> print(hex(d.parse(b'\x0f\xf0')))
0xf00f
>>> d = ProcessRotateLeft(4, 2, Int16ub)
>>> print(hex(d.parse(b'\x0f\xf0')))
0xff00
>>> d.sizeof()
2

Note that the classes read entire stream till EOF so they should be wrapped in ``FixedSized``, ``Prefixed`` etc unless you actually want to process the entire remaining stream.


Compression and checksuming
----------------------------------------

Data can be easily checksummed. Note that checksum field does not need to be ``Bytes``, and lambda may return an integer or otherwise.

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


Data can also be easily compressed. Supported encodings include zlib/gzip/bzip2/lzma and entire codecs module. When parsing, entire stream is consumed. When building, it puts compressed bytes without marking the end. Use ``Prefixed`` when an encoded-length field immediately precedes the compressed data, or ``FixedSized`` when that length is available elsewhere in the context. An unbounded ``Compressed`` is suitable when the compressed data occupies the entire remaining stream.

>>> d = Prefixed(VarInt, Compressed(GreedyBytes, "zlib"))
>>> d.build(bytes(100))
b'\x0cx\x9cc`\xa0=\x00\x00\x00d\x00\x01'
>>> len(_)
13

LZ4 compression is also supported. It provides less compaction but does it at higher throughputs. This class is also supposed to be used with ``Prefixed`` class.

>>> d = Prefixed(VarInt, CompressedLZ4(GreedyBytes))
>>> d.build(bytes(100))
b'"\x04"M\x18h@d\x00\x00\x00\x00\x00\x00\x00#\x0b\x00\x00\x00\x1f\x00\x01\x00KP\x00\x00\x00\x00\x00\x00\x00\x00\x00'
>>> len(_)
35


.. _compressed-length-fields:

Compressed data with a separate length field
----------------------------------------------------

``Compressed`` gives its subcon a **decompressed** stream. The subcon can be
``GreedyBytes`` for a byte string, or a ``Struct`` or another construct describing
the decompressed content. In particular, ``Compressed(Bytes(10), "zlib")``
reads all remaining compressed input, then returns ten decompressed bytes; it
does not bound the compressed input. If the decompressed format must consume
all of its input, include ``Terminated`` in that format.

When a header already supplies the encoded length, put ``FixedSized`` outside
``Compressed``. This leaves following fields available to the enclosing struct::

    Struct(
        "compressed_size" / Int32ul,
        "version" / Byte,
        "payload" / FixedSized(this.compressed_size,
            Compressed(GreedyBytes, "zlib")),
        "trailer" / Const(b"END"),
    )

That definition requires the encoded length when building, too. It cannot
derive it from the length of the uncompressed payload. Likewise, a ``Rebuild``
before the payload cannot measure bytes that have not yet been written.

For a seekable stream, reserve the length field, write the compressed payload
once, and then fill in its measured length with ``Pointer``. The following
example format has a version byte between the length and the payload. Parsing
uses the stored length; building lets the compressor determine the length.
``Pointer`` restores the stream position, so the trailer is still written
after the payload.

.. doctest:: compressed-length

    >>> from construct import (Byte, Compressed, Const, FixedSized, GreedyBytes,
    ...                        IfThenElse, Int32ul, Pointer, Rebuild, Struct,
    ...                        Tell, this)
    >>> compressed = Compressed(GreedyBytes, "zlib")
    >>> packet = Struct(
    ...     "size_offset" / Tell,
    ...     "compressed_size" / Rebuild(Int32ul, 0),
    ...     "version" / Byte,
    ...     "payload_start" / Tell,
    ...     "payload" / IfThenElse(this._parsing,
    ...         FixedSized(this.compressed_size, compressed), compressed),
    ...     "payload_end" / Tell,
    ...     Pointer(this.size_offset,
    ...         Rebuild(Int32ul, this.payload_end - this.payload_start)),
    ...     "trailer" / Const(b"END"),
    ... )
    >>> payload = b"hello" * 100
    >>> encoded = packet.build(dict(version=1, payload=payload))
    >>> decoded = packet.parse(encoded)
    >>> decoded.payload == payload
    True
    >>> decoded.compressed_size == len(encoded) - 4 - 1 - 3
    True
    >>> packet.build(decoded) == encoded
    True

The initial ``Rebuild`` writes a placeholder when building; when parsing it
reads the stored length normally. The later ``Pointer`` replaces the placeholder
when building and reads it again when parsing. ``Tell`` records positions in the
current stream, so the same definition also works when the packet starts at a
nonzero offset. The compressed length excludes the header and trailer. Callers
do not need to provide a length, and a supplied length is recomputed on build.

This recipe requires a seekable, tellable stream. ``build()`` uses an in-memory
stream and satisfies that requirement. For a non-seekable destination, build the
packet into bytes first, then write those bytes to the destination. Prefer
``Prefixed`` when the wire format permits an adjacent length prefix; it already
manages that case.


Encryption and authentication
----------------------------------------------------

Subcons can also be easily encrypted and authenticated in a AEAD manner. Please note that the data sometimes needs to be aligned to a particular block size that depends on the encryption scheme used.

::

    >>> from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    >>> d = Struct(
    ...     "iv" / Default(Bytes(16), os.urandom(16)),
    ...     "enc_data" / EncryptedSym(
    ...         Aligned(16,
    ...             Struct(
    ...                 "width" / Int16ul,
    ...                 "height" / Int16ul,
    ...             )
    ...         ),
    ...         lambda ctx: Cipher(algorithms.AES(ctx._.key), modes.CBC(ctx.iv))
    ...     )
    ... )
    >>> key128 = b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
    >>> d.build({"enc_data": {"width": 5, "height": 4}}, key=key128)
    b"o\x11i\x98~H\xc9\x1c\x17\x83\xf6|U:\x1a\x86+\x00\x89\xf7\x8e\xc3L\x04\t\xca\x8a\xc8\xc2\xfb'\xc8"
    >>> d.parse(b"o\x11i\x98~H\xc9\x1c\x17\x83\xf6|U:\x1a\x86+\x00\x89\xf7\x8e\xc3L\x04\t\xca\x8a\xc8\xc2\xfb'\xc8", key=key128)
    Container: 
        iv = b'o\x11i\x98~H\xc9\x1c\x17\x83\xf6|U:\x1a\x86' (total 16)
        enc_data = Container: 
            width = 5
            height = 4

