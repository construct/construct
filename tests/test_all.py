import sys
from construct import *
from construct.lib import LazyContainer
import zlib

class ZlibCodec(object):
    encode = staticmethod(zlib.compress)
    decode = staticmethod(zlib.decompress)

import warnings
import traceback
import unittest
warnings.filterwarnings("ignore", category=DeprecationWarning)



all_tests = [
    #
    # constructs
    #
    [Byte(None).parse, b"\x00", 0, None],
    [Byte(u"unicode_name").parse, b"\x00", 0, None],
    [Byte(b"bytes_name").parse, b"\x00", 0, None],
    [Byte("string").parse, b"\x00", 0, None],

    [VarInt("varint").parse, b"\x05", 5, None],
    [VarInt("varint").parse, b"\x85\x05", 645, None],
    [VarInt("varint").build, 5, b"\x05", None],
    [VarInt("varint").build, 645, b"\x85\x05", None],
    [VarInt("varint").parse, b"", None, FieldError],
    [VarInt("varint").build, -1, None, ValueError],

    [MetaArray(lambda ctx: 3, UBInt8("metaarray")).parse, b"\x01\x02\x03", [1, 2, 3], None],
    [MetaArray(lambda ctx: 3, UBInt8("metaarray")).parse, b"\x01\x02", None, ArrayError],
    [MetaArray(lambda ctx: 3, UBInt8("metaarray")).build, [1, 2, 3], b"\x01\x02\x03", None],
    [MetaArray(lambda ctx: 3, UBInt8("metaarray")).build, [1, 2], None, ArrayError],

    [Range(3, 5, UBInt8("range")).parse, b"\x01\x02\x03", [1, 2, 3], None],
    [Range(3, 5, UBInt8("range")).parse, b"\x01\x02\x03\x04", [1, 2, 3, 4], None],
    [Range(3, 5, UBInt8("range")).parse, b"\x01\x02\x03\x04\x05", [1, 2, 3, 4, 5], None],
    [Range(3, 5, UBInt8("range")).parse, b"\x01\x02", None, RangeError],
    [Range(3, 5, UBInt8("range")).build, [1, 2, 3], b"\x01\x02\x03", None],
    [Range(3, 5, UBInt8("range")).build, [1, 2, 3, 4], b"\x01\x02\x03\x04", None],
    [Range(3, 5, UBInt8("range")).build, [1, 2, 3, 4, 5], b"\x01\x02\x03\x04\x05", None],
    [Range(3, 5, UBInt8("range")).build, [1, 2], None, RangeError],
    [Range(3, 5, UBInt8("range")).build, [1, 2, 3, 4, 5, 6], None, RangeError],

    [RepeatUntil(lambda obj, ctx: obj == 9, UBInt8("repeatuntil")).parse, b"\x02\x03\x09", [2, 3, 9], None],
    [RepeatUntil(lambda obj, ctx: obj == 9, UBInt8("repeatuntil")).parse, b"\x02\x03\x08", None, ArrayError],
    [RepeatUntil(lambda obj, ctx: obj == 9, UBInt8("repeatuntil")).build, [2, 3, 9], b"\x02\x03\x09", None],
    [RepeatUntil(lambda obj, ctx: obj == 9, UBInt8("repeatuntil")).build, [2, 3, 8], None, ArrayError],

    [Struct("struct", UBInt8("a"), UBInt16("b")).parse, b"\x01\x00\x02", Container(a=1)(b=2), None],
    [Struct("struct", UBInt8("a"), UBInt16("b"), Struct("inner", UBInt8("c"), UBInt8("d"))).parse, b"\x01\x00\x02\x03\x04", Container(a=1)(b=2)(inner=Container(c=3)(d=4)), None],
    [Struct("struct", UBInt8("a"), UBInt16("b"), Embedded(Struct("inner", UBInt8("c"), UBInt8("d")))).parse, b"\x01\x00\x02\x03\x04", Container(a=1)(b=2)(c=3)(d=4), None],
    [Struct("struct", UBInt8("a"), UBInt16("b")).build, Container(a=1)(b=2), b"\x01\x00\x02", None],
    [Struct("struct", UBInt8("a"), UBInt16("b"), Struct("inner", UBInt8("c"), UBInt8("d"))).build, Container(a=1)(b=2)(inner=Container(c=3)(d=4)), b"\x01\x00\x02\x03\x04", None],
    [Struct("struct", UBInt8("a"), UBInt16("b"), Embedded(Struct("inner", UBInt8("c"), UBInt8("d")))).build, Container(a=1)(b=2)(c=3)(d=4), b"\x01\x00\x02\x03\x04", None],

    [Sequence("sequence", UBInt8("a"), UBInt16("b")).parse, b"\x01\x00\x02", [1, 2], None],
    [Sequence("sequence", UBInt8("a"), UBInt16("b"), Sequence("foo", UBInt8("c"), UBInt8("d"))).parse, b"\x01\x00\x02\x03\x04", [1, 2, [3, 4]], None],
    [Sequence("sequence", UBInt8("a"), UBInt16("b"), Embedded(Sequence("foo", UBInt8("c"), UBInt8("d")))).parse, b"\x01\x00\x02\x03\x04", [1, 2, 3, 4], None],
    [Sequence("sequence", UBInt8("a"), UBInt16("b")).build, [1, 2], b"\x01\x00\x02", None],
    [Sequence("sequence", UBInt8("a"), UBInt16("b"), Sequence("foo", UBInt8("c"), UBInt8("d"))).build, [1, 2, [3, 4]], b"\x01\x00\x02\x03\x04", None],
    [Sequence("sequence", UBInt8("a"), UBInt16("b"), Embedded(Sequence("foo", UBInt8("c"), UBInt8("d")))).build, [1, 2, 3, 4], b"\x01\x00\x02\x03\x04", None],

    [Switch("switch", lambda ctx: 5, {1:UBInt8("x"), 5:UBInt16("y")}).parse, b"\x00\x02", 2, None],
    [Switch("switch", lambda ctx: 6, {1:UBInt8("x"), 5:UBInt16("y")}).parse, b"\x00\x02", None, SwitchError],
    [Switch("switch", lambda ctx: 6, {1:UBInt8("x"), 5:UBInt16("y")}, default=UBInt8("x")).parse, b"\x00\x02", 0, None],
    [Switch("switch", lambda ctx: 5, {1:UBInt8("x"), 5:UBInt16("y")}, include_key=True).parse, b"\x00\x02", (5, 2), None],
    [Switch("switch", lambda ctx: 5, {1:UBInt8("x"), 5:UBInt16("y")}).build, 2, b"\x00\x02", None],
    [Switch("switch", lambda ctx: 6, {1:UBInt8("x"), 5:UBInt16("y")}).build, 9, None, SwitchError],
    [Switch("switch", lambda ctx: 6, {1:UBInt8("x"), 5:UBInt16("y")}, default=UBInt8("x")).build, 9, b"\x09", None],
    [Switch("switch", lambda ctx: 5, {1:UBInt8("x"), 5:UBInt16("y")}, include_key=True).build, ((5, 2),), b"\x00\x02", None],
    [Switch("switch", lambda ctx: 5, {1:UBInt8("x"), 5:UBInt16("y")}, include_key=True).build, ((89, 2),), None, SwitchError],

    [Select("select", UBInt32("a"), UBInt16("b"), UBInt8("c")).parse, b"\x07", 7, None],
    [Select("select", UBInt32("a"), UBInt16("b")).parse, b"\x07", None, SelectError],
    [Select("select", UBInt32("a"), UBInt16("b"), UBInt8("c"), include_name=True).parse, b"\x07", ("c", 7), None],
    [Select("select", UBInt32("a"), UBInt16("b"), UBInt8("c")).build, 7, b"\x00\x00\x00\x07", None],
    [Select("select", UBInt32("a"), UBInt16("b"), UBInt8("c"), include_name=True).build, (("c", 7),), b"\x07", None],
    [Select("select", UBInt32("a"), UBInt16("b"), UBInt8("c"), include_name=True).build, (("d", 7),), None, SelectError],

    [Peek(UBInt8("peek")).parse, b"\x01", 1, None],
    [Peek(UBInt8("peek")).parse, b"", None, None],
    [Peek(UBInt8("peek")).build, 1, b"", None],
    [Peek(UBInt8("peek"), perform_build=True).build, 1, b"\x01", None],
    [Struct("peek", Peek(UBInt8("a")), UBInt16("b")).parse, b"\x01\x02", Container(a=1)(b=0x102), None],
    [Struct("peek", Peek(UBInt8("a")), UBInt16("b")).build, Container(a=1, b=0x102), b"\x01\x02", None],

    [Computed("computed", lambda ctx: "moo").parse, b"", "moo", None],
    [Computed("computed", lambda ctx: "moo").build, None, b"", None],
    [Struct("s", Computed("c", lambda ctx: None)).parse, b"", Container(c=None), None],
    [Struct("s", Computed("c", lambda ctx: None)).build, Container(c=None), b"", None],
    [Struct("s", Computed("c", lambda ctx: None)).build, Container(), b"", None],

    [Anchor("anchor").parse, b"", 0, None],
    [Anchor("anchor").build, None, b"", None],

    [LazyBound("lazybound", lambda: UBInt8("byte")).parse, b"\x02", 2, None],
    [LazyBound("lazybound", lambda: UBInt8("byte")).build, 2, b"\x02", None],

    [Pass.parse, b"", None, None],
    [Pass.build, None, b"", None],

    [Terminator.parse, b"", None, None],
    [Terminator.parse, b"x", None, TerminatorError],
    [Terminator.build, None, b"", None],

    [Pointer(lambda ctx: 2, UBInt8("pointer")).parse, b"\x00\x00\x07", 7, None],
    [Pointer(lambda ctx: 2, UBInt8("pointer")).build, 7, b"\x00\x00\x07", None],

    [OnDemand(UBInt8("ondemand")).parse(b"\x08").read, (), 8, None],
    [Struct("ondemand", UBInt8("a"), OnDemand(UBInt8("b")), UBInt8("c")).parse, b"\x07\x08\x09", Container(a=7)(b=LazyContainer(None, None, None, None))(c=9), None],
    [Struct("ondemand", UBInt8("a"), OnDemand(UBInt8("b"), advance_stream=False), UBInt8("c")).parse, b"\x07\x09", Container(a=7)(b=LazyContainer(None, None, None, None))(c=9), None],

    [OnDemand(UBInt8("ondemand")).build, 8, b"\x08", None],
    [Struct("ondemand", UBInt8("a"), OnDemand(UBInt8("b")), UBInt8("c")).build, Container(a=7)(b=8)(c=9), b"\x07\x08\x09", None],
    [Struct("ondemand", UBInt8("a"), OnDemand(UBInt8("b"), force_build=False), UBInt8("c")).build, Container(a=7)(b=LazyContainer(None, None, None, None))(c=9), b"\x07\x00\x09", None],
    [Struct("ondemand", UBInt8("a"), OnDemand(UBInt8("b"), force_build=False, advance_stream=False), UBInt8("c")).build, Container(a=7)(b=LazyContainer(None, None, None, None))(c=9), b"\x07\x09", None],

    [Struct("reconfig", Reconfig("foo", UBInt8("bar"))).parse, b"\x01", Container(foo=1), None],
    [Struct("reconfig", Reconfig("foo", UBInt8("bar"))).build, Container(foo=1), b"\x01", None],

    [Buffered(UBInt8("buffered"), lambda x:x, lambda x:x, lambda x:x).parse, b"\x07", 7, None],
    [Buffered(GreedyRange(UBInt8("buffered")), lambda x:x, lambda x:x, lambda x:x).parse, b"\x07", None, SizeofError],
    [Buffered(UBInt8("buffered"), lambda x:x, lambda x:x, lambda x:x).build, 7, b"\x07", None],
    [Buffered(GreedyRange(UBInt8("buffered")), lambda x:x, lambda x:x, lambda x:x).build, [7], None, SizeofError],

    [Restream(UBInt8("restream"), lambda x:x, lambda x:x, lambda x:x).parse, b"\x07", 7, None],
    [Restream(GreedyRange(UBInt8("restream")), lambda x:x, lambda x:x, lambda x:x).parse, b"\x07", [7], None],
    [Restream(UBInt8("restream"), lambda x:x, lambda x:x, lambda x:x).parse, b"\x07", 7, None],
    [Restream(GreedyRange(UBInt8("restream")), lambda x:x, lambda x:x, lambda x:x).parse, b"\x07", [7], None],

    #
    # adapters
    #
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8).parse, b"\x01" * 8, 255, None],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8, signed=True).parse, b"\x01" * 8, -1, None],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8, swapped=True, bytesize=4).parse, b"\x01" * 4 + b"\x00" * 4, 0x0f, None],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8).build, 255, b"\x01" * 8, None],
    [BitIntegerAdapter(Field("bitintegeradapter", lambda c: 8), lambda c: 8).build, 255, b"\x01" * 8, None],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8).build, -1, None, BitIntegerError],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8, signed=True).build, -1, b"\x01" * 8, None],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8, swapped=True, bytesize=4).build, 0x0f, b"\x01" * 4 + b"\x00" * 4, None],

    [MappingAdapter(UBInt8("mappingadapter"), {2:"x", 3:"y"}, {"x":2, "y":3}).parse, b"\x03", "y", None],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x", 3:"y"}, {"x":2, "y":3}).parse, b"\x04", None, MappingError],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x", 3:"y"}, {"x":2, "y":3}, decdefault="foo").parse, b"\x04", "foo", None],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x", 3:"y"}, {"x":2, "y":3}, decdefault=Pass).parse, b"\x04", 4, None],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x", 3:"y"}, {"x":2, "y":3}).build, "y", b"\x03", None],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x", 3:"y"}, {"x":2, "y":3}).build, "z", None, MappingError],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x", 3:"y"}, {"x":2, "y":3}, encdefault=17).build, "foo", b"\x11", None],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x", 3:"y"}, {"x":2, "y":3}, encdefault=Pass).build, 4, b"\x04", None],

    [FlagsAdapter(UBInt8("flagsadapter"), {"a":1, "b":2, "c":4, "d":8, "e":16, "f":32, "g":64, "h":128}).parse, b"\x81", FlagsContainer(a=True, b=False, c=False, d=False, e=False, f=False, g=False, h=True), None],
    [FlagsAdapter(UBInt8("flagsadapter"), {"a":1, "b":2, "c":4, "d":8, "e":16, "f":32, "g":64, "h":128}).build, FlagsContainer(a=True, b=False, c=False, d=False, e=False, f=False, g=False, h=True), b"\x81", None],

    [IndexingAdapter(Array(3, UBInt8("indexingadapter")), 2).parse, b"\x11\x22\x33", 0x33, None],
    [IndexingAdapter(Array(3, UBInt8("indexingadapter")), 2)._encode, (0x33, {}), [None, None, 0x33], None],

    [SlicingAdapter(Array(3, UBInt8("indexingadapter")), 1, 3).parse, b"\x11\x22\x33", [0x22, 0x33], None],
    [SlicingAdapter(Array(3, UBInt8("indexingadapter")), 1, 3)._encode, ([0x22, 0x33], {}), [None, 0x22, 0x33], None],

    [Padding(4).parse, b"\x00\x00\x00\x00", None, None],
    [Padding(4, strict=True).parse, b"\x00\x00\x00\x00", None, None],
    [Padding(4, strict=True).parse, b"????", None, PaddingError],
    [Padding(4).build, None, b"\x00\x00\x00\x00", None],
    [Padding(4, strict=True).build, None, b"\x00\x00\x00\x00", None],
    [lambda none: Padding(4, pattern=b"??"), None, None, PaddingError],

    # [LengthValueAdapter(Sequence("lengthvalueadapter", UBInt8("length"), Field("value", lambda ctx: ctx.length))).parse, b"\x05abcde", b"abcde", None],
    # [LengthValueAdapter(Sequence("lengthvalueadapter", UBInt8("length"), Field("value", lambda ctx: ctx.length))).build, b"abcde", b"\x05abcde", None],

    [TunnelAdapter(PascalString("data", encoding=ZlibCodec), GreedyRange(UBInt16("elements"))).parse, b"\rx\x9cc`f\x18\x16\x10\x00u\xf8\x01-", [3] * 100, None],
    [TunnelAdapter(PascalString("data", encoding=ZlibCodec), GreedyRange(UBInt16("elements"))).build, [3] * 100, b"\rx\x9cc`f\x18\x16\x10\x00u\xf8\x01-", None],

    [Const(b"MZ").parse, b"MZ", b"MZ", None],
    [Const(b"MZ").parse, b"ELF", None, ConstError],
    [Const(b"MZ").build, None, b"MZ", None],
    [Const(b"MZ").build, b"MZ", b"MZ", None],
    [Const("const", b"MZ").parse, b"MZ", b"MZ", None],
    [Const("const", b"MZ").parse, b"ELF", None, ConstError],
    [Const("const", b"MZ").build, None, b"MZ", None],
    [Const("const", b"MZ").build, b"MZ", b"MZ", None],
    [Const(ULInt32("const"), 255).parse, b"\xff\x00\x00\x00", 255, None],
    [Const(ULInt32("const"), 255).parse, b"\x00\x00\x00\x00", 255, ConstError],
    [Const(ULInt32("const"), 255).build, None, b"\xff\x00\x00\x00", None],
    [Const(ULInt32("const"), 255).build, 255, b"\xff\x00\x00\x00", None],

    [ExprAdapter(UBInt8("expradapter"),
        encoder=lambda obj, ctx: obj // 7,
        decoder=lambda obj, ctx: obj * 7).parse,
        b"\x06", 42, None],
    [ExprAdapter(UBInt8("expradapter"),
        encoder=lambda obj, ctx: obj // 7,
        decoder=lambda obj, ctx: obj * 7).build,
        42, b"\x06", None],

    #
    # macros
    #
    [Aligned(UBInt8("aligned")).parse, b"\x01\x00\x00\x00", 1, None],
    [Aligned(UBInt8("aligned")).build, 1, b"\x01\x00\x00\x00", None],
    [Struct("aligned", Aligned(UBInt8("a")), UBInt8("b")).parse, b"\x01\x00\x00\x00\x02", Container(a=1)(b=2), None],
    [Struct("aligned", Aligned(UBInt8("a")), UBInt8("b")).build, Container(a=1)(b=2), b"\x01\x00\x00\x00\x02", None],

    [Bitwise(Field("bitwise", 8)).parse, b"\xff", b"\x01" * 8, None],
    [Bitwise(Field("bitwise", lambda ctx: 8)).parse, b"\xff", b"\x01" * 8, None],
    [Bitwise(Field("bitwise", 8)).build, b"\x01" * 8, b"\xff", None],
    [Bitwise(Field("bitwise", lambda ctx: 8)).build, b"\x01" * 8, b"\xff", None],

    [Union("union",
        UBInt32("a"),
        Struct("b", UBInt16("a"), UBInt16("b")),
        BitStruct("c", Padding(4), Octet("a"), Padding(4)),
        Struct("d", UBInt8("a"), UBInt8("b"), UBInt8("c"), UBInt8("d")),
        Embedded(Struct("q", UBInt8("e"))),
        ).parse,
        b"\x11\x22\x33\x44",
        Container(a=0x11223344)
            (b=Container(a=0x1122)(b=0x3344))
            (c=Container(a=0x12))
            (d=Container(a=0x11)(b=0x22)(c=0x33)(d=0x44))
            (e=0x11),
        None],
    [Union("union",
        UBInt32("a"),
        Struct("b", UBInt16("a"), UBInt16("b")),
        BitStruct("c", Padding(4), Octet("a"), Padding(4)),
        Struct("d", UBInt8("a"), UBInt8("b"), UBInt8("c"), UBInt8("d")),
        Embedded(Struct("q", UBInt8("e"))),
        ).build,
        Container(a=0x11223344,
            b=Container(a=0x1122, b=0x3344),
            c=Container(a=0x12),
            d=Container(a=0x11, b=0x22, c=0x33, d=0x44),
            e=0x11,
        ),
        b"\x11\x22\x33\x44",
        None],
    [Union("union",
        Struct("sub1", ULInt8("a"), ULInt8("b")),
        Struct("sub2", ULInt16("c")),
        ).build, dict(sub1=dict(a=1, b=2)), b"\x01\x02", None],
    [Union("union",
        Struct("sub1", ULInt8("a"), ULInt8("b")),
        Struct("sub2", ULInt16("c")),
        ).build, dict(sub2=dict(c=3)), b"\x03\x00", None],
    [Union("union",
        Embed(Struct("sub1", ULInt8("a"), ULInt8("b"))),
        Embed(Struct("sub2", ULInt16("c"))),
        buildfrom=None,
        ).build, dict(a=1, b=2), b"\x01\x02", None],
    [Union("union",
        Embed(Struct("sub1", ULInt8("a"), ULInt8("b"))),
        Embed(Struct("sub2", ULInt16("c"))),
        buildfrom=None,
        ).build, dict(c=3), b"\x03\x00", None],
    [Union("union",
        Embed(Struct("sub1", ULInt8("a"), ULInt8("b"))),
        Embed(Struct("sub2", ULInt16("c"))),
        buildfrom=0,
        ).build, dict(a=1, b=2), b"\x01\x02", None],
    [Union("union",
        Embed(Struct("sub1", ULInt8("a"), ULInt8("b"))),
        Embed(Struct("sub2", ULInt16("c"))),
        buildfrom=1,
        ).build, dict(c=3), b"\x03\x00", None],
    [Union("union",
        Embed(Struct("sub1", ULInt8("a"), ULInt8("b"))),
        Embed(Struct("sub2", ULInt16("c"))),
        buildfrom="sub1",
        ).build, dict(a=1, b=2), b"\x01\x02", None],
    [Union("union",
        Embed(Struct("sub1", ULInt8("a"), ULInt8("b"))),
        Embed(Struct("sub2", ULInt16("c"))),
        buildfrom="sub2",
        ).build, dict(c=3), b"\x03\x00", None],
    [Union("samesize",
        Struct("both", ULInt8("a"), ULInt8("b")),
        ULInt16("c"),
        ).sizeof, None, 2, None],
    [Union("mixedsize",
        Struct("both", ULInt8("a"), ULInt8("b")),
        ULInt32("c"),
        ).sizeof, None, 4, None],

    [Enum(UBInt8("enum"), q=3, r=4, t=5).parse, b"\x04", "r", None],
    [Enum(UBInt8("enum"), q=3, r=4, t=5).parse, b"\x07", None, MappingError],
    [Enum(UBInt8("enum"), q=3, r=4, t=5, _default_="spam").parse, b"\x07", "spam", None],
    [Enum(UBInt8("enum"), q=3, r=4, t=5, _default_=Pass).parse, b"\x07", 7, None],
    [Enum(UBInt8("enum"), q=3, r=4, t=5).build, "r", b"\x04", None],
    [Enum(UBInt8("enum"), q=3, r=4, t=5).build, "spam", None, MappingError],
    [Enum(UBInt8("enum"), q=3, r=4, t=5, _default_=9).build, "spam", b"\x09", None],
    [Enum(UBInt8("enum"), q=3, r=4, t=5, _default_=Pass).build, 9, b"\x09", None],

    [PrefixedArray(UBInt8("array"), UBInt8("count")).parse, b"\x03\x01\x01\x01", [1, 1, 1], None],
    [PrefixedArray(UBInt8("array"), UBInt8("count")).parse, b"\x00", [], None],
    [PrefixedArray(UBInt8("array"), UBInt8("count")).parse, b"", None, ArrayError],
    [PrefixedArray(UBInt8("array"), UBInt8("count")).parse, b"\x03\x01\x01", None, ArrayError],
    # Fix: sizeof takes a context, not an obj.
    [PrefixedArray(UBInt8("array"), UBInt8("count")).sizeof, [1, 1, 1], 4, SizeofError],
    [PrefixedArray(UBInt8("array"), UBInt8("count")).build, [1, 1, 1], b"\x03\x01\x01\x01", None],

    [IfThenElse("ifthenelse", lambda ctx: True, UBInt8("then"), UBInt16("else")).parse, b"\x01", 1, None],
    [IfThenElse("ifthenelse", lambda ctx: False, UBInt8("then"), UBInt16("else")).parse, b"\x00\x01", 1, None],
    [IfThenElse("ifthenelse", lambda ctx: True, UBInt8("then"), UBInt16("else")).build, 1, b"\x01", None],
    [IfThenElse("ifthenelse", lambda ctx: False, UBInt8("then"), UBInt16("else")).build, 1, b"\x00\x01", None],

    [Optional(ULInt32("int")).parse, b"\x01\x00\x00\x00", 1, None],
    [Optional(ULInt32("int")).build, 1, b"\x01\x00\x00\x00", None],
    [Optional(ULInt32("int")).parse, b"?", None, None],
    [Optional(ULInt32("int")).build, None, b"", None],

    [ULInt24('int24').parse, b"\x01\x02\x03", 197121, None],
    [ULInt24('int24').build, 197121, b"\x01\x02\x03", None],
    [Struct('foo', ULInt24('int24')).parse, b"\x01\x02\x03", Container(int24=197121), None],
    [Struct('foo', ULInt24('int24')).build, Container(int24=197121), b"\x01\x02\x03", None],
]


class TestAll(unittest.TestCase):
    def _run_tests(self, tests):
        errors = []
        for i, (func, args, res, exctype) in enumerate(tests):
            if type(args) is not tuple:
                args = (args,)
            try:
                r = func(*args)
            except:
                t, ex, tb = sys.exc_info()
                if exctype is None:
                    errors.append("%d::: %s" % (i, "".join(traceback.format_exception(t, ex, tb))))
                    continue
                if t is not exctype:
                    errors.append("%s: raised %r, expected %r" % (func, t, exctype))
                    continue
            else:
                if exctype is not None:
                    print("Testing: %r", (i, func, args, res, exctype))
                    errors.append("%s: expected exception %r" % (func, exctype))
                    continue
                if r != res:
                    errors.append("%s: returned %r, expected %r" % (func, r, res))
                    continue
        return errors

    def test_all(self):
        errors = self._run_tests(all_tests)
        if errors:
            self.fail("\n=========================\n".join(str(e) for e in errors))

