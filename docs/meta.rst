===========
The Context
===========

Meta constructs are the key to the declarative power of Construct. Meta constructs are constructs which are affected by the context of the construction (parsing or building). In other words, meta constructs are self-referring. The context is a dictionary that is created during the construction process by Structs and Sequences, and is "propagated" down and up to all constructs along the way, so that they could use it. It basically represents a mirror image of the construction tree, as it is altered by the different constructs. Nested structs create nested contexts, just as they create nested containers.

In order to see the context, let's try this snippet:

>>> class PrintContext(Construct):
...     def _parse(self, stream, context):
...         print(context)
...
>>> st = Struct(
...     "a" / Byte,
...     PrintContext(),
...     "b" / Byte,
...     PrintContext(),
... )
>>> st.parse(b"\x01\x02")
Container:
    a = 1
Container:
    a = 1
    b = 2
Container(a=1)(b=2)

As you can see, the context looks different at different points of the construction.

You may wonder what does the little underscore ('_') that is found in the context means. It basically represents the parent node, like the .. in unix pathnames ("../foo.txt"). We'll use it only when we refer to the context of upper layers.

Using the context is easy. All meta constructs take a function as a parameter, which is usually passed as a lambda function, although "big" functions are just as good. This function, unless otherwise stated, takes a single parameter called ctx (short for context), and returns a result calculated from that context.

>>> st = Struct(
...     "count" / Byte,
...     "data" / Bytes(lambda ctx: ctx["count"]),
... )
>>> st.parse(b"\x05abcde")
Container(count=5)(data=b'abcde')

Of course the function can return anything (it doesn't have to use ctx at all):

>>> st = Struct(
...     "ct" / Computed(lambda ctx: 7),
... )
>>> st.parse(b"")
Container(ct=7)

And here's how we use the special '_' name to get to the upper layer. Here the length of the string is calculated as ``length1 + length2``:

>>> st = Struct(
...     "length1" / Byte,
...     "inner" / Struct(
...             "length2" / Byte,
...             "sum" / Computed(lambda ctx: ctx._.length1 + ctx.length2),
...     ),
... )
>>> st.parse(b"12")
Container(length1=49)(inner=Container(length2=50)(sum=99))



Using `this` expression
===========================

Certain classes take a number of elements, or something similar, and allow a callable to be provided instead. This callable is called at parsing and building, and is provided the current context object. Context is always a Container, not a dict, so it supports attribute as well as key access. Amazingly, this can get even more fancy. Tomer Filiba provided even a better syntax. The `this` singleton object can be used to build a lambda expression. All four examples below are equivalent:

>>> lambda ctx: ctx["_"]["field"]
...
>>> lambda ctx: ctx._.field
...
>>> this._.field
...
>>> this["_"]["field"]

Of course, `this` can be mixed with other calculations. When evaluating, each instance of this is replaced by ctx.

>>> this.width * this.height - this.offset



Using `len_` builtin alikes
===========================

There used to be a bit of a hassle when you used to builtin functions like `len sum min max` on context items. Builtin `len` takes a list and returns an int but `len_` analog takes a lambda and returns a lambda. This allows to use this kind of shorthand:

>>> lambda ctx: len(ctx.items)
...
>>> len_(this.items)

These can be used in newly added Rebuild wrappers that take compute count/length fields from another items-alike field:

>>> st = Struct(
...     "count" / Rebuild(Byte, len_(this.items)),
...     "items" / Byte[this.count],
... )
>>> st.build(dict(items=[1,2,3,4,5]))
b'\x05\x01\x02\x03\x04\x05'

Incidentally, when the count field is directly before the items field you can also use PrefixedArray. However in some protocols these fields are separate and the other approach is good:

>>> PrefixedArray(Byte, Byte).build([1,2,3])
b'\x03\x01\x02\x03'




Using `obj_` expression
=======================

There is also an analog that takes both (obj, context) unlike the `this` singleton which only takes a context:

>>> obj_ > 0
...
>>> lambda obj,ctx: obj > 0

These can be used in few classes that use (obj, context) lambdas:

>>> RepeatUntil(obj_ == 0, Byte).build([1,2,0,1,0])
b'\x01\x02\x00'



Array
-----

When creating an Array, rather than specifying a constant length, you can instead specify that it repeats a variable number of times.

::

    PrefixedArray  <-->  FocusedSeq(1,
        "count"/Rebuild(lengthfield, len_(this.items)),
        "items"/subcon[this.count],


RepeatUntil
-----------

A repeater that repeats until a condition is met. The perfect example is null-terminated strings.

.. note:: For null-terminated strings, use :func:`~construct.CString`.

>>> loop = RepeatUntil(obj_ == 0, Byte)
>>> loop.parse(b"aioweqnjkscs\x00")
[97, 105, 111, 119, 101, 113, 110, 106, 107, 115, 99, 115, 0]


Switch
------

Branches the construction path based on a condition, similarly to C's switch statement.

>>> st = Struct(
...     "type" / Enum(Byte, INT1=1, INT2=2, INT4=3, STRING=4),
...     "data" / Switch(this.type,
...     {
...             "INT1" : Int8ub,
...             "INT2" : Int16ub,
...             "INT4" : Int32ub,
...             "STRING" : String(10),
...     }),
... )
>>> st.parse(b"\x02\x00\xff")
Container(type='INT2')(data=255)
>>> st.parse(b"\x04\abcdef\x00\x00\x00\x00")
Container(type='STRING')(data=b'\x07bcdef')

When the condition is not found in the switching table, and a default construct is not given, an exception is raised (SwitchError). In order to specify a default construct, set default (a keyword argument) when creating the Switch. Note that default is a construct, not a value.

>>> st = Struct(
...     "type" / Byte,
...     "data" / Switch(this.type, {
...             1 : Int8ul,
...             2 : Int8sl,
...         }, default = Int8ul),
... )
>>> st.parse(b"\xff\x01")
Container(type=255)(data=1)

When you want to ignore/skip errors, you can use the Pass construct, which is a no-op construct. Pass will simply return None, without reading anything from the stream. Pass will also not put anything into the stream.

>>> st = Struct(
...     "type" / Byte,
...     "data" / Switch(this.type, {
...             1 : Int8ul,
...             2 : Int8sl,
...     }, default = Pass),
... )
>>> st.parse(b"??????")
Container(type=63)(data=None)



Known deficiencies
==================

Logical ``and or not`` operators cannot be used in this expressions. You have to either use a lambda or equivalent bitwise operators:

>>> ~this.flag1 | this.flag2 & this.flag3
...
>>> lambda ctx: not ctx.flag1 or ctx.flag2 and ctx.flag3

``in`` operator cannot be used in this expressions, you have to use a lambda
 expression
>>> lambda ctx: ctx.value in (1, 2, 3)
