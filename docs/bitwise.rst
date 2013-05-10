=======
History
=======

In Construct 1.XX, parsing and building were performed at the bit level: the
entire data was converted to a string of 1's and 0's, so you could really work
with bit fields. Every construct worked with bits, except some (which were
named ByteXXX) that worked on whole octets. This made it very easy to work
with single bits, such as the flags of the TCP header, 7-bit ASCII characters,
or fields that were not aligned to the byte boundary (nibbles et al).

This approach was easy and flexible, but had two main drawbacks:

* Most data is byte-aligned (with very few exceptions)
* The overhead was too big.

Since constructs worked on bits, the data had to be first converted to a
bit-string, which meant you had to hold the entire data set in memory. Not
only that, but you actually held 8 times the size of the original data (it was
a bit-string). According to some tests I made, you were limited to files of
about 50MB (and that was slow due to page-thrashing).

So as of Construct 2.XX, all constructs work with bytes:

* Less memory consumption
* No unnecessary bytes-to-bits/bits-to-bytes coversions
* Can rely on python's built in struct module for numeric packing/unpacking
  (faster, tested)
* Can directly parse-from/build-to file-like objects (without in-memory
  buffering)

But how are we supposed to work with raw bits? The only difference is that we
must explicitly declare that: BitFields handle parsing/building bit fields,
and BitStructs handle to/from conversions.

BitStruct
=========

A BitStruct is a sequence of constructs that are parsed/built in the specified
order, much like normal Structs. The difference is that BitStruct operate on
bits rather than bytes. When parsing a BitStruct, the data is first converted
to a bit stream (a stream of 1's and 0's), and only then is it fed to the
subconstructs. The subconstructs are expected to operate on bits instead of
bytes. For reference, see the code snippet in the BitField section.

.. note:: BitStruct is actually just a wrapper for the :func:`~construct.macros.Bitwise` construct.

Important notes
---------------

* Non-nestable - BitStructs are not nestable/stackable; writing something
  like ``BitStruct("foo", BitStruct("bar", Octet("spam")))`` will not work. You
  can use regular Structs inside BitStructs.
* BitStructs are embeddable.

  .. seealso:: The :func:`~construct.macros.EmbeddedBitStruct` macro.

* Byte-Aligned - The total size of the elements of a BitStruct must be a
  multiple of 8 (due to alignment issues)
* Pointers and OnDemand - Do not place Pointers or OnDemands inside
  BitStructs, since it uses an internal stream, so external stream offsets
  will turn out wrong.


BitField
========

.. autofunction:: construct.BitField

Convenience wrappers for BitField
---------------------------------

Bit
 A single bit
Nibble
 A sequence of 4 bits (half a byte)
Octet
 An sequence of 8 bits (byte)

The Bit/Byte Duality
====================

Most simple fields (such as Flag, Padding, Terminator, etc.) are ignorant to
the granularity of the data they operate on. The actual granularity depends on
the enclosing layers.

Here's a snippet of code that operates on bytes:

>>> c1 = Struct("foo",
...     Padding(2),
...     Flag("myflag"),
...     Padding(5),
... )
>>>
>>> c1.parse("\x00\x00\x01\x00\x00\x00\x00\x00")
Container(myflag = True)


And here's a snippet of code that operates on bits. The only difference is
BitStruct in place of a normal Struct:

>>> c2 = BitStruct("foo",
...     Padding(2),
...     Flag("myflag"),
...     Padding(5),
... )
>>>
>>> c2.parse("\x20")
Container(myflag = True)
>>>


So unlike "classical Construct", there's no need for BytePadding and
BitPadding. If Padding is enclosed by a BitStruct, it operates on bits;
otherwise, it operates on bytes.
