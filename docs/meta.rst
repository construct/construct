===========
The Context
===========

Meta constructs are the key to the declarative power of Construct. Meta constructs are constructs which are affected by the context of the construction (during parsing and building). The context is a dictionary that is created during the parsing and building process by Structs and Sequences, and is "propagated" down and up to all constructs along the way, so that other members can access other members parsing or building resuslts. It basically represents a mirror image of the construction tree, as it is altered by the different constructs. Nested structs create nested contexts, just as they create nested containers.

In order to see the context, let's try this snippet:

>>> class PrintContext(Construct):
...     def _parse(self, stream, context, path):
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

Using the context is easy. All meta constructs take a function as a parameter, which is usually passed as a lambda function, although "big" named functions are just as good. This function, unless otherwise stated, takes a single parameter called ctx (short for context), and returns a result calculated from that context.

>>> st = Struct(
...     "count" / Byte,
...     "data" / Bytes(this.count),
... )
>>> st.parse(b"\x05abcde")
Container(count=5)(data=b'abcde')

Of course the function can return anything (it does not need to depend on the context):

>>> Computed(lambda ctx: 7)
>>> Computed(lambda ctx: os.urandom(16))

And here's how we use the special '_' name to get to the upper container in a nested containers situation (which happens when parsing nested Structs). Here the length of the string is calculated as ``length1 + length2`` but note the fields are on different levels:

>>> st = Struct(
...     "length1" / Byte,
...     "inner" / Struct(
...         "length2" / Byte,
...         "sum" / Computed(this._.length1 + this.length2),
...     ),
... )
>>> st.parse(b"12")
Container(length1=49)(inner=Container(length2=50)(sum=99))



Nesting and embedding
============================

Context entries can also be passed directly through `parse` and `build` methods. However, one should take into account that some classes are nesting context (like Struct Sequence Union FocusedSeq), so entries passed to these end up on upper level. Compare these two examples:

>>> d = Bytes(this.n)
>>> d.parse(bytes(100), n=4)
b'\x00\x00\x00\x00'

>>> d = Struct(
...     "data" / Bytes(this._.n),
... )
>>> d.parse(bytes(100), n=4)
Container(data=b'\x00\x00\x00\x00')

Embedding also complicates using the context. Notice that `count` is on same level as `data` because embedding simply "levels the plainfield".

>>> outer = Struct(
...     "count" / Byte,
...     Embedded(Struct(
...         "data" / Bytes(this.count),
...     )),
... )
>>> outer.parse(b"\x041234")
Container(count=4)(data=b'1234')



Using `this` expression
============================

Certain classes take a number of elements, or something similar, and allow a callable to be provided instead. This callable is called at parsing and building, and is provided the current context object. Context is always a Container, not a dict, so it supports attribute as well as key access. Amazingly, this can get even more fancy. Tomer Filiba provided an even better syntax. The `this` singleton object can be used to build a lambda expression. All four examples below are equivalent, but first is recommended:

>>> this._.field
...
>>> lambda ctx: ctx._.field
...
>>> this["_"]["field"]
...
>>> lambda ctx: ctx["_"]["field"]

Of course, `this` expression can be mixed with other calculations. When evaluating, each instance of `this` is replaced by context Container which supports attribute access to keys.

>>> this.width * this.height - this.offset

When creating an Array ("items" field), rather than specifying a constant count, you can use a previous field value as count.

>>> st = Struct(
...     "count" / Rebuild(Byte, len_(this.items)),
...     "items" / Byte[this.count],
... )
>>> st.build(dict(items=[1,2,3,4,5]))
b'\x05\x01\x02\x03\x04\x05'

Switch can branch the construction path based on previously parsed value.

>>> st = Struct(
...     "type" / Enum(Byte, INT1=1, INT2=2, INT4=3, STRING=4),
...     "data" / Switch(this.type,
...     {
...         "INT1" : Int8ub,
...         "INT2" : Int16ub,
...         "INT4" : Int32ub,
...         "STRING" : String(10),
...     }),
... )
>>> st.parse(b"\x02\x00\xff")
Container(type='INT2')(data=255)
>>> st.parse(b"\x04\abcdef\x00\x00\x00\x00")
Container(type='STRING')(data=b'\x07bcdef')



Using `len_` expression
============================

There used to be a bit of a hassle when you used built-in functions like `len sum min max abs` on context items. Built-in `len` takes a list and returns an integer but `len_` analog takes a lambda and returns a lambda. This allows you to use this kind of shorthand:

>>> len_(this.items)
...
>>> lambda ctx: len(ctx.items)

These can be used in newly added Rebuild wrappers that compute count/length fields from another list-alike field:

>>> st = Struct(
...     "count" / Rebuild(Byte, len_(this.items)),
...     "items" / Byte[this.count],
... )
>>> st.build(dict(items=[1,2,3,4,5]))
b'\x05\x01\x02\x03\x04\x05'



Using `obj_` expression
============================

There is also an analog that takes (obj, context) or (obj, list, context) unlike `this` singleton which only takes a context (a single parameter):

>>> obj_ > 0
...
>>> lambda obj,ctx: obj > 0

These can be used in at least one construct:

>>> RepeatUntil(obj_ == 0, Byte).parse(b"aioweqnjkscs\x00")
[97, 105, 111, 119, 101, 113, 110, 106, 107, 115, 99, 115, 0]



Using `list_` expression (not yet implemented)
============================

There is also a third expression that takes (obj, list, context) and computes on the second parameter (the list). In constructs that use lambdas with all 3 parameters, those constructs usually process lists of elements and the 2nd parameter is a list of elements processed so far.

These can be used in at least one construct: 

>>> RepeatUntil(list_[-1] == 0, Byte).parse(b"aioweqnjkscs\x00")
[97, 105, 111, 119, 101, 113, 110, 106, 107, 115, 99, 115, 0]

In that example, `list_` gets substituted with following, at each iteration. Index -1 means last element:

::

    list_ <- [97]
    list_ <- [97, 105]
    list_ <- [97, 105, 111]
    list_ <- [97, 105, 111, 119]
    ...

Known deficiencies
============================

Logical ``and`` ``or`` ``not`` operators cannot be used in this expressions. You have to either use a lambda or equivalent bitwise operators:

>>> ~this.flag1 | this.flag2 & this.flag3
...
>>> lambda ctx: not ctx.flag1 or ctx.flag2 and ctx.flag3

Contains operator ``in`` cannot be used in this expressions, you have to use a lambda:

>>> lambda ctx: ctx.value in (1, 2, 3)

Lambdas (unlike this expressions) are not compilable.
