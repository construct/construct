The Context
===========

Meta constructs are the key to the declarative power of Construct. Meta
constructs are constructs which are affected by the context of the
construction (parsing or building). In other words, meta constructs are
self-referring.
The context is a dictionary that is created during the construction process,
by Structs, and is "propagated" down and up to all constructs along the way,
so that they could use it. It basically represents a mirror image of the
construction tree, as it is altered by the different constructs. Structs
create nested contexts, just as they create nested Containers.

In order to see the context, let's try this snippet:

>>> class PrintContext(Construct):
...     def _parse(self, stream, context):
...         print context
...
>>> foo = Struct("foo",
...     Byte("a"),
...     Byte("b"),
...     PrintContext("c"),
...     Struct("bar",
...         Byte("a"),
...         Byte("b"),
...         PrintContext("c"),
...     ),
...     PrintContext("d"),
... )
>>>
>>> foo.parse("\x01\x02\x03\x04")
{'_': {'a': 1, 'b': 2}}
{'_': {'a': 3, 'b': 4, '_': {'a': 1, 'c': None, 'b': 2}}}
{'_': {'a': 1, 'c': None, 'b': 2, 'bar': Container(a = 3, b = 4, c = None)}}
Container(a = 1, b = 2, bar = Container(a = 3, b = 4, c = None), c = None, d =
None)
>>>

As you can see, the context looks different in different points of the
construction.

You may wonder what does the little underscore ('_') that is found in the
context means. It basically represents the parent node, like the .. in unix
pathnames ("../foo.txt"). We'll use it only when we refer to the context of
upper layers.

Using the context is easy. All meta constructs take a function as a parameter,
which is usually passed as a lambda function, although "big" functions are
just as good. This function, unless otherwise stated, takes a single parameter
called ctx (short for context), and returns a result calculated from that
context.

>>> foo = Struct("foo",
...     Byte("length"),
...     Field("data", lambda ctx: ctx.length * 2 + 1),  # <-- calculate
the length of the string
... )
>>>
>>> foo.parse("\x05abcdefghijkXXX")
Container(data = 'abcdefghijk', length = 5)


Of course the function can return anything (it doesn't have to use ctx at
all):

>>> foo = Struct("foo",
...     Byte("length"),
...     Field("data", lambda ctx: 7),
... )
>>>
>>> foo.parse("\x99abcdefg")
Container(data = 'abcdefg', length = 153)


And here's how we use the special '_' name to get to the upper layer. Here the
length of the string is calculated as ``length1 + length2``.

>>> foo = Struct("foo",
...     Byte("length1"),
...     Struct("bar",
...         Byte("length2"),
...         Field("data", lambda ctx: ctx._.length1 + ctx.length2),
...     )
... )
>>>
>>> foo.parse("\x02\x03abcde")
Container(bar = Container(data = 'abcde', length2 = 3), length1 = 2)

.. autofunction:: construct.Field

Array
-----

When creating an :ref:`Array <repeaters>`, rather than specifying a constant
length, you can instead specify that it repeats a variable number of times.

>>> foo = Struct("foo",
...     Byte("length"),
...     Array(lambda ctx: ctx.length, UBInt16("data")),
... )
>>>
>>> foo.parse("\x03\x00\x01\x00\x02\x00\x03")
Container(data = [1, 2, 3], length = 3)


RepeatUntil
-----------

A repeater that repeats until a condition is met. The perfect example is
null-terminated strings.

.. note:: For null-terminated strings, use :func:`~construct.CString`.

>>> foo = RepeatUntil(lambda obj, ctx: obj == "\x00", Field("data", 1))
>>>
>>> foo.parse("abcdef\x00this is another string")
['a', 'b', 'c', 'd', 'e', 'f', '\x00']
>>>
>>> foo2 = StringAdapter(foo)
>>> foo2.parse("abcdef\x00this is another string")
'abcdef\x00'


Switch
------

Branches the construction path based on a condition, similarly to C's switch
statement.

>>> foo = Struct("foo",
...     Enum(Byte("type"),
...         INT1 = 1,
...         INT2 = 2,
...         INT4 = 3,
...         STRING = 4,
...     ),
...     Switch("data", lambda ctx: ctx.type,
...         {
    ...             "INT1" : UBInt8("spam"),
    ...             "INT2" : UBInt16("spam"),
    ...             "INT4" : UBInt32("spam"),
    ...             "STRING" : String("spam", 6),
    ...         }
    ...     )
... )
>>>
>>>
>>> foo.parse("\x01\x12")
Container(data = 18, type = 'INT1')
>>>
>>> foo.parse("\x02\x12\x34")
Container(data = 4660, type = 'INT2')
>>>
>>> foo.parse("\x03\x12\x34\x56\x78")
Container(data = 305419896, type = 'INT4')
>>>
>>> foo.parse("\x04abcdef")
Container(data = 'abcdef', type = 'STRING')


When the condition is not found in the switching table, and a default
construct is not given, an exception is raised (SwitchError). In order to
specify a default construct, set default (a keyword argument) when creating
the Switch.

>>> foo = Struct("foo",
...     Byte("type"),
...     Switch("data", lambda ctx: ctx.type,
...         {
    ...             1 : UBInt8("spam"),
    ...             2 : UBInt16("spam"),
    ...         },
    ...         default = UBInt8("spam")            # <-- sets the default
    construct
    ...     )
... )
>>>
>>> foo.parse("\x01\xff")
Container(data = 255, type = 1)
>>>
>>> foo.parse("\x02\xff\xff")
Container(data = 65535, type = 2)
>>>
>>> foo.parse("\x03\xff\xff")                   # <-- uses the default
construct
Container(data = 255, type = 3)
>>>


When you want to ignore/skip errors, you can use the Pass construct, which is
a no-op construct. Pass will simply return None, without reading anything from
the stream.

>>> foo = Struct("foo",
...     Byte("type"),
...     Switch("data", lambda ctx: ctx.type,
...         {
    ...             1 : UBInt8("spam"),
    ...             2 : UBInt16("spam"),
    ...         },
    ...         default = Pass
    ...     )
... )
>>>
>>> foo.parse("\x01\xff")
Container(data = 255, type = 1)
>>>
>>> foo.parse("\x02\xff\xff")
Container(data = 65535, type = 2)
>>>
>>> foo.parse("\x03\xff\xff")
Container(data = None, type = 3)


Pointer
-------

Pointer allows for non-sequential construction. The pointer first changes the
stream position, constructs the subconstruct, and restores the original stream
position.

.. note::

    Pointers are available only for seekable streams (in-memory and files).
    Sockets and pipes do not suppose seeking, so you'll have to first read the
    data from the stream, and parse it in-memory.

>>> foo = Struct("foo",
...     Pointer(lambda ctx: 4, Byte("data1")),   # <-- data1 is at (absolute)
position 4
...     Pointer(lambda ctx: 7, Byte("data2")),   # <-- data2 is at (absolute)
position 7
... )
>>>
>>> foo.parse("\x00\x00\x00\x00\x01\x00\x00\x02")
Container(data1 = 1, data2 = 2)


Anchor
------

Anchor is not really a meta construct, but it strongly coupled with Pointer,
so I chose to list it here. Anchor simply returns the stream position at the
moment it's invoked, so Pointers can "anchor" relative offsets to absolute
stream positions using it. See the following example:

>>> foo = Struct("foo",
...     Byte("padding_length"),
...     Padding(lambda ctx: ctx.padding_length),
...     Byte("relative_offset"),
...     Anchor("absolute_position"),
...     Pointer(lambda ctx: ctx.absolute_position + ctx.relative_offset,
...         Byte("data")
...     ),
... )
>>>
>>> foo.parse("\x05\x00\x00\x00\x00\x00\x03\x00\x00\x00\xff")
Container(absolute_position = 7, data = 255, padding_length = 5,
relative_offset = 3)

OnDemand
--------

OnDemand allows lazy construction, meaning the data is actually parsed (or
built) only when it's requested (demanded). On-demand parsing is very useful
with record-oriented data, where you don't have to actually parse the data
unless it's actually needed. The result of OnDemand is an OnDemandContainer --
a special object that "remembers" the stream position where its data is found,
and parses it when you access its .value property.

.. note::

    Lazy construction is available only for seekable streams (in-memory and
    files). Sockets and pipes do not suppose seeking, so you'll have to first
    read the data from the stream, and parse it in-memory.

>>> foo = Struct("foo",
...     Byte("a"),
...     OnDemand(Bytes("bigdata", 20)),  # <-- this will be read only on
demand
...     Byte("b"),
... )
>>>
>>> x = foo.parse("\x0101234567890123456789\x02")
>>> x
Container(a = 1, b = 2, bigdata = OnDemandContainer(<unread>))
>>>
>>> x.bigdata
OnDemandContainer(<unread>)
>>> x.bigdata.has_value                      # <-- still unread
False
>>>
>>> x.bigdata.value                          # <-- demand the data
'01234567890123456789'
>>>
>>> x.bigdata.has_value                      # <-- already demanded
True
>>> x.bigdata
OnDemandContainer('01234567890123456789')
