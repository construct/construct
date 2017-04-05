============
Lazy parsing
============

.. note::

    Certain constructs are available only for seekable streams (in-memory and files) and some require tellable streams (which in fact is a subset of seekability). Sockets and pipes do not support seeking, so you'll have to first read the data from the stream, and parse it in-memory, or use the :func:`~construct.core.Rebuffered` wrapper.


Structs Sequences and Ranges
----------------------------

Lazy* constructs allow lazy construction and deconstruction, meaning the data is actually parsed only when it's requested (demanded). Lazy parsing (also called on-demand parsing but that term is reserved here) is very useful with record-oriented data, where you don't have to actually parse the data unless it's actually needed. The result of parsing is a different container that remembers names of the members and their location in the stream, and when the data is accessed by key (or attribute for that matter) then that field is parsed. Members are parsed only once each.

Essentially almost every code that uses the base classes also works on these but there are few things that one has to be aware of when using lazy equivalents.

`LazyStruct` works like Struct but parses into a LazyContainer.

    Equivalent to Struct construct, however fixed size members are parsed on demand, others are parsed immediately. If entire struct is fixed size then entire parse is essentially one seek.

`LazySequence` works like Sequence but parses into a LazySequenceContainer.

    Equivalent to Sequence construct, however fixed size members are parsed on demand, others are parsed immediately. If entire sequence is fixed size then entire parse is essentially one seek.

`LazyRange` works like Range but parses into a LazyRangeContainer.

    Equivalent to Range construct, but members are parsed on demand. Works only with fixed size subcon.


OnDemand
--------

There is a different approach to lazy parsing, where only one field is made lazy. Parsing returns a parameterless lambda that when called, returns the parsed data. Right now, each time the lambda is called the object is parsed again, so it the inner subcon is non-deterministic, each parsing may return a different object. Builds from a parsed object or a lambda.

>>> OnDemand(Byte).parse(b"\xff")
<function OnDemand._parse.<locals>.<lambda> at 0x7fdc241cfc80>
>>> _()
255
>>> OnDemand(Byte).build(16)
b'\x10'

There is also OnDemandPointer class.

>>> OnDemandPointer(lambda ctx: 2, Byte).parse(b"\x01\x02\x03garbage")
<function OnDemand._parse.<locals>.effectuate at 0x7f6f011ad510>
>>> _()
3


LazyBound
---------

A lazy-bound construct that binds to the construct only at runtime. Useful for recursive data structures (like linked lists or trees), where a construct needs to refer to itself (while it doesn't exist yet).

>>> st = Struct(
...     "value"/Byte,
...     "next"/If(this.value > 0, LazyBound(lambda ctx: st)),
... )
...
>>> st.parse(b"\x05\x09\x00")
Container(value=5)(next=Container(value=9)(next=Container(value=0)(next=None)))
...
>>> print(st.parse(b"\x05\x09\x00"))
Container: 
    value = 5
    next = Container: 
        value = 9
        next = Container: 
            value = 0
            next = None

