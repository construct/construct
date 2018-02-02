==========
The Basics
==========


Fields
======

Fields are the most fundamental unit of construction: they **parse** (read data from the stream and return an object) and **build** (take an object and write it down onto a stream). There are many kinds of fields, each working with a different type of data (numeric, boolean, strings, etc.).

Some examples of parsing:

>>> from construct import Int16ub, Int16ul
>>> Int16ub.parse(b"\x01\x02")
258
>>> Int16ul.parse(b"\x01\x02")
513

Some examples of building:

>>> from construct import Int16ub, Int16sb
>>> Int16ub.build(31337)
'zi'
>>> Int16sb.build(-31337)
'\x86\x97'

Other fields like:

>>> Flag.parse(b"\x01")
True

>>> Enum(Byte, g=8, h=11).parse(b"\x08")
'g'
>>> Enum(Byte, g=8, h=11).build(11)
b'\x0b'

>>> Float32b.build(12.345)
b'AE\x85\x1f'
>>> Single.parse(_)
12.345000267028809


Variable-length fields
======================

>>> VarInt.build(1234567890)
b'\xd2\x85\xd8\xcc\x04'
>>> VarInt.sizeof()
construct.core.SizeofError: cannot calculate size

Fields are sometimes fixed size and some composites behave differently when they are composed of those. Keep that detail in mind. Classes that cannot determine size always raise SizeofError in response. There are few classes where same instance may return an integer or raise SizeofError depending on circumstances. Array size depends on whether count of elements is constant (can be a context lambda) and subcon is fixed size (can be variable size). For example, many classes take context lambdas and SizeofError is raised if the key is missing from the context.

>>> Int16ub[2].sizeof()
4
>>> VarInt[1].sizeof()
construct.core.SizeofError: cannot calculate size


Structs
=======

For those of you familiar with C, Structs are very intuitive, but here's a short explanation for the larger audience. A Struct is a collection of ordered and usually named fields (field means an instance of Construct class), that are parsed/built in that same order. Names are used for two reasons: (1) when parsed, values are returned in a dictionary where keys are matching the names, and when build, each field gets build with a value taken from a dictionary from a matching key (2) parsed and build fields values are inserted into the context dictionary under mathing names. 

>>> format = Struct(
...     "signature" / Const(b"BMP"),
...     "width" / Int8ub,
...     "height" / Int8ub,
...     "pixels" / Array(this.width * this.height, Byte),
... )
>>> format.build(dict(width=3,height=2,pixels=[7,8,9,11,12,13]))
b'BMP\x03\x02\x07\x08\t\x0b\x0c\r'
>>> format.parse(b'BMP\x03\x02\x07\x08\t\x0b\x0c\r')
Container(signature=b'BMP')(width=3)(height=2)(pixels=[7, 8, 9, 11, 12, 13])

Usually members are named but there are some classes that build from nothing and return nothing on parsing, so they have no need for a name (they can stay anonymous). Duplicated names within same struct can have unknown side effects.

>>> test = Struct(
...     Const(b"XYZ"),
...     Padding(2),
...     Pass,
...     Terminated,
... )
>>> test.build({})
b'XYZ\x00\x00'
>>> test.parse(_)
Container()

Note that this syntax works ONLY on Python 3.6 due to ordered keyword arguments:

>>> Struct(a=Byte, b=Byte, c=Byte, d=Byte)

Operator `+` can also be used to make Structs, and to merge them. Structs are embedded (not nested) when added.

>>> st = "count"/Byte + "items"/Byte[this.count] + Terminated
>>> st.parse(b"\x03\x01\x02\x03")
Container(count=3)(items=[1, 2, 3])


Containers
----------

What is that Container object, anyway? Well, a Container is a regular Python dictionary. It provides pretty-printing and accessing items as attributes as well as keys, and preserves insertion order in addition to the normal facilities of dictionaries. Let's see more of those:

>>> st = Struct("float"/Single)
>>> x = st.parse(b"\x00\x00\x00\x01")
>>> x
Container(float=1.401298464324817e-45)
>>> x.float
1.401298464324817e-45
>>> x["float"]
1.401298464324817e-45
>>> print(x)
Container:
    float = 1.401298464324817e-45

Thanks to blapid, containers can also be searched. Structs nested within Structs return containers within containers on parsing. One can search the entire "tree" of dicts for a particular name. Regular expressions are supported.

>>> con = Container(Container(a=1,d=Container(a=2)))
>>> con.search("a")
1
>>> con.search_all("a")
[1, 2]


Nesting and embedding
---------------------

Structs can be nested. Structs can contain other Structs, as well as any other constructs. Here's how it's done:

>>> st = Struct(
...     "inner" / Struct(
...         "data" / Bytes(4),
...     )
... )
>>> st.parse(b"1234")
Container(inner=Container(data=b'1234'))
>>> print(_)
Container:
    inner = Container:
        data = b'1234'

A Struct can be embedded into an enclosing Struct. This means that all fields of the embedded Struct get merged into the fields of the enclosing Struct. This is useful when you want to split a big Struct into multiple parts, and then combine them all into one Struct. If names are duplicated, consistency is not guaranteed (you should avoid that).

>>> outer = Struct(
...     Embedded(Struct(
...         "data" / Bytes(4),
...     )),
... )
>>> outer.parse(b"1234")
Container(data=b'1234')

As you can see, Containers provide human-readable representations of the data, which is very important for large data structures.

.. seealso:: The :func:`~construct.core.Embedded` macro.


Sequences
=========

Sequences are very similar to Structs, but operate with lists rather than containers. Sequences are less commonly used than Structs, but are very handy in certain situations. Since a list is returned in place of an attribute container, the names of the sub-constructs are not important. Two constructs with the same name will not override or replace each other. Names are used for the purposes of context dict.

Operator `>>` can be used to make Sequences, or to merge them.

Building and parsing
--------------------

>>> seq = Int16ub >> CString(encoding="utf8") >> GreedyBytes
>>> seq.parse(b"\x00\x80lalalaland\x00\x00\x00\x00\x00")
[128, 'lalalaland', b'\x00\x00\x00\x00']

Nesting and embedding
---------------------

Like Structs, Sequences are compatible with the Embedded wrapper. Embedding one Sequence into another causes a merge of the parsed lists of the two Sequences.

>>> nseq = Sequence(Byte, Byte, Sequence(Byte, Byte))
>>> nseq.parse(b"abcd")
[97, 98, [99, 100]]

>>> nseq = Sequence(Byte, Byte, Embedded(Sequence(Byte, Byte)))
>>> nseq.parse(b"abcd")
[97, 98, 99, 100]

.. seealso:: The :func:`~construct.core.Embedded` macro.


Repeaters
=========

Repeaters, as their name suggests, repeat a given unit for a specified number of times. At this point, we'll only cover static repeaters where count is a constant int. Meta-repeaters take values at parse/build time from the context and they will be covered in the meta-constructs tutorial. Ranges differ from Sequences in that they are homogenous, they process elements of same kind. We have four kinds of repeaters. For those of you who wish to look under the hood, two of these repeaters are actually wrappers around Range.

Arrays have a fixed constant count of elements. Operator `[]` is used instead of calling the `Array` class.

>>> Byte[10].parse(b"1234567890")
[49, 50, 51, 52, 53, 54, 55, 56, 57, 48]
>>> Byte[10].build([1,2,3,4,5,6,7,8,9,0])
b'\x01\x02\x03\x04\x05\x06\x07\x08\t\x00'

Ranges are similar but they take a range (pun) of element counts. User can specify the minimum and maximum count.

>>> Byte[3:5].parse(b"1234")
[49, 50, 51, 52]
>>> Byte[3:5].parse(b"12")
construct.core.RangeError: expected 3 to 5, found 2
>>> Byte[3:5].build([1,2,3,4,5,6,7])
construct.core.RangeError: expected from 3 to 5 elements, found 7

GreedyRange is essentially a Range from 0 to 2**64.

>>> Byte[:].parse(b"dsadhsaui")
[100, 115, 97, 100, 104, 115, 97, 117, 105]
>>> Byte[:].min
0
>>> Byte[:].max
18446744073709551616

RepeatUntil is different than the others. Each element is tested by a lambda predicate. The predicate signals when a given element is the terminal element. The repeater inserts all previous items along with the terminal one, and returns just the same.

Note that all elements accumulated during parsing are provided as additional lambda parameter (second in order).

>>> RepeatUntil(lambda obj,lst,ctx: obj > 10, Byte).parse(b"\x01\x05\x08\xff\x01\x02\x03")
[1, 5, 8, 255]
>>> RepeatUntil(lambda obj,lst,ctx: obj > 10, Byte).build(range(20))
b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'

>>> RepeatUntil(lambda x,lst,ctx: lst[-2:]==[0,0], Byte).parse(b"\x01\x00\x00\xff")
[1, 0, 0]
