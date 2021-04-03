# -*- coding: utf-8 -*-

from tests.declarativeunittest import *
from construct import *
from construct.lib import *
from tests.test_compiler import example, exampledata


def test_class_bytes_parse(benchmark):
    d = Bytes(100)
    benchmark(d.parse, bytes(100))

def test_class_bytes_parse_compiled(benchmark):
    d = Bytes(100)
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_bytes_build(benchmark):
    d = Bytes(100)
    benchmark(d.build, bytes(100))

def test_class_bytes_build_compiled(benchmark):
    d = Bytes(100)
    d = d.compile()
    benchmark(d.build, bytes(100))

def test_class_greedybytes_parse(benchmark):
    d = GreedyBytes
    benchmark(d.parse, bytes(100))

def test_class_greedybytes_parse_compiled(benchmark):
    d = GreedyBytes
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_greedybytes_build(benchmark):
    d = GreedyBytes
    benchmark(d.build, bytes(100))

def test_class_greedybytes_build_compiled(benchmark):
    d = GreedyBytes
    d = d.compile()
    benchmark(d.build, bytes(100))

def test_class_bitwise1_parse(benchmark):
    d = Bitwise(Bytes(800))
    benchmark(d.parse, bytes(100))

def test_class_bitwise1_parse_compiled(benchmark):
    d = Bitwise(Bytes(800))
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_bitwise1_build(benchmark):
    d = Bitwise(Bytes(800))
    benchmark(d.build, bytes(800))

def test_class_bitwise2_parse(benchmark):
    d = Bitwise(RepeatUntil(obj_ == 1, Byte))
    benchmark(d.parse, bytes(99)+b"\x01")

def test_class_bitwise2_parse_compiled(benchmark):
    d = Bitwise(RepeatUntil(obj_ == 1, Byte))
    d = d.compile()
    benchmark(d.parse, bytes(99)+b"\x01")

def test_class_bitwise2_build(benchmark):
    d = Bitwise(RepeatUntil(obj_ == 1, Byte))
    benchmark(d.build, [0 if i<800-1 else 1 for i in range(800)])

def test_class_bytewise1_parse(benchmark):
    d = Bitwise(Bytewise(Bytes(100)))
    benchmark(d.parse, bytes(100))

def test_class_bytewise1_parse_compiled(benchmark):
    d = Bitwise(Bytewise(Bytes(100)))
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_bytewise1_build(benchmark):
    d = Bitwise(Bytewise(Bytes(100)))
    benchmark(d.build, bytes(100))

def test_class_bytewise2_parse(benchmark):
    d = Bitwise(Bytewise(RepeatUntil(obj_ == 1, Byte)))
    benchmark(d.parse, bytes(99)+b"\x01")

def test_class_bytewise2_parse_compiled(benchmark):
    d = Bitwise(Bytewise(RepeatUntil(obj_ == 1, Byte)))
    d = d.compile()
    benchmark(d.parse, bytes(99)+b"\x01")

def test_class_bytewise2_build(benchmark):
    d = Bitwise(Bytewise(RepeatUntil(obj_ == 1, Byte)))
    benchmark(d.build, [0 if i<100-1 else 1 for i in range(100)])

def test_class_formatfield_parse(benchmark):
    d = FormatField(">", "L")
    benchmark(d.parse, bytes(4))

def test_class_formatfield_parse_compiled(benchmark):
    d = FormatField(">", "L")
    d = d.compile()
    benchmark(d.parse, bytes(4))

def test_class_formatfield_build(benchmark):
    d = FormatField(">", "L")
    benchmark(d.build, 0)

def test_class_formatfield_build_compiled(benchmark):
    d = FormatField(">", "L")
    d = d.compile()
    benchmark(d.build, 0)

def test_class_bytesinteger_parse(benchmark):
    d = BytesInteger(16)
    benchmark(d.parse, bytes(16))

def test_class_bytesinteger_parse_compiled(benchmark):
    d = BytesInteger(16)
    d = d.compile()
    benchmark(d.parse, bytes(16))

def test_class_bytesinteger_build(benchmark):
    d = BytesInteger(16)
    benchmark(d.build, 0)

def test_class_bytesinteger_build_compiled(benchmark):
    d = BytesInteger(16)
    d = d.compile()
    benchmark(d.build, 0)

def test_class_bitsinteger_parse(benchmark):
    d = Bitwise(BitsInteger(128, swapped=True))
    benchmark(d.parse, bytes(128//8))

def test_class_bitsinteger_parse_compiled(benchmark):
    d = Bitwise(BitsInteger(128, swapped=True))
    d = d.compile()
    benchmark(d.parse, bytes(128//8))

def test_class_bitsinteger_build(benchmark):
    d = Bitwise(BitsInteger(128, swapped=True))
    benchmark(d.build, 0)

def test_class_bitsinteger_build_compiled(benchmark):
    d = Bitwise(BitsInteger(128, swapped=True))
    d = d.compile()
    benchmark(d.build, 0)

def test_class_varint_parse(benchmark):
    d = VarInt
    benchmark(d.parse, b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x10")

def test_class_varint_parse_compiled(benchmark):
    d = VarInt
    d = d.compile()
    benchmark(d.parse, b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x10")

def test_class_varint_build(benchmark):
    d = VarInt
    benchmark(d.build, 2**100)

# ZigZag

def test_class_paddedstring_parse(benchmark):
    d = PaddedString(100, "utf8")
    benchmark(d.parse, b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00\x00'+bytes(100))

def test_class_paddedstring_parse_compiled(benchmark):
    d = PaddedString(100, "utf8")
    d = d.compile()
    benchmark(d.parse, b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00\x00'+bytes(100))

def test_class_paddedstring_build(benchmark):
    d = PaddedString(100, "utf8")
    benchmark(d.build, u"Афон")

def test_class_pascalstring_parse(benchmark):
    d = PascalString(Byte, "utf8")
    benchmark(d.parse, b'\x08\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd'+bytes(100))

def test_class_pascalstring_parse_compiled(benchmark):
    d = PascalString(Byte, "utf8")
    d = d.compile()
    benchmark(d.parse, b'\x08\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd'+bytes(100))

def test_class_pascalstring_build(benchmark):
    d = PascalString(Byte, "utf8")
    benchmark(d.build, u"Афон")

def test_class_cstring_parse(benchmark):
    d = CString("utf8")
    benchmark(d.parse, b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00'+bytes(100))

def test_class_cstring_parse_compiled(benchmark):
    d = CString("utf8")
    d = d.compile()
    benchmark(d.parse, b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00'+bytes(100))

def test_class_cstring_build(benchmark):
    d = CString("utf8")
    benchmark(d.build, u"Афон")

def test_class_greedystring_parse(benchmark):
    d = GreedyString("utf8")
    benchmark(d.parse, b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00'+bytes(100))

def test_class_greedystring_parse_compiled(benchmark):
    d = GreedyString("utf8")
    d = d.compile()
    benchmark(d.parse, b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00'+bytes(100))

def test_class_greedystring_build(benchmark):
    d = GreedyString("utf8")
    benchmark(d.build, u"Афон")

def test_class_flag_parse(benchmark):
    d = Flag
    benchmark(d.parse, bytes(1))

def test_class_flag_parse_compiled(benchmark):
    d = Flag
    d = d.compile()
    benchmark(d.parse, bytes(1))

def test_class_flag_build(benchmark):
    d = Flag
    benchmark(d.build, False)

def test_class_flag_build_compiled(benchmark):
    d = Flag
    d = d.compile()
    benchmark(d.build, False)

def test_class_enum_parse(benchmark):
    d = Enum(Byte, zero=0)
    benchmark(d.parse, bytes(1))

def test_class_enum_parse_compiled(benchmark):
    d = Enum(Byte, zero=0)
    d = d.compile()
    benchmark(d.parse, bytes(1))

def test_class_enum_build(benchmark):
    d = Enum(Byte, zero=0)
    benchmark(d.build, 0)

def test_class_enum_build_compiled(benchmark):
    d = Enum(Byte, zero=0)
    d = d.compile()
    benchmark(d.build, 0)

def test_class_flagsenum_parse(benchmark):
    d = FlagsEnum(Byte, a=1, b=2, c=4, d=8)
    benchmark(d.parse, bytes(1))

def test_class_flagsenum_parse_compiled(benchmark):
    d = FlagsEnum(Byte, a=1, b=2, c=4, d=8)
    d = d.compile()
    benchmark(d.parse, bytes(1))

def test_class_flagsenum_build(benchmark):
    d = FlagsEnum(Byte, a=1, b=2, c=4, d=8)
    benchmark(d.build, Container(a=False, b=False, c=False, d=False))

def test_class_mapping_parse(benchmark):
    x = "object"
    d = Mapping(Byte, {x:0})
    benchmark(d.parse, bytes(1))

def test_class_mapping_parse_compiled(benchmark):
    x = "object"
    d = Mapping(Byte, {x:0})
    d = d.compile()
    benchmark(d.parse, bytes(1))

def test_class_mapping_build(benchmark):
    x = "object"
    d = Mapping(Byte, {x:0})
    benchmark(d.build, x)

def test_class_mapping_build_compiled(benchmark):
    x = "object"
    d = Mapping(Byte, {x:0})
    d = d.compile()
    benchmark(d.build, x)

def test_class_struct_parse(benchmark):
    d = Struct("a"/Byte, "b"/Byte, "c"/Byte, "d"/Byte, "e"/Byte)
    benchmark(d.parse, bytes(5))

def test_class_struct_parse_compiled(benchmark):
    d = Struct("a"/Byte, "b"/Byte, "c"/Byte, "d"/Byte, "e"/Byte)
    d = d.compile()
    benchmark(d.parse, bytes(5))

def test_class_struct_build(benchmark):
    d = Struct("a"/Byte, "b"/Byte, "c"/Byte, "d"/Byte, "e"/Byte)
    benchmark(d.build, dict(a=0, b=0, c=0, d=0, e=0))

def test_class_struct_build_compiled(benchmark):
    d = Struct("a"/Byte, "b"/Byte, "c"/Byte, "d"/Byte, "e"/Byte)
    d = d.compile()
    benchmark(d.build, dict(a=0, b=0, c=0, d=0, e=0))

def test_class_sequence_parse(benchmark):
    d = Sequence(Byte, Byte, Byte, Byte, Byte)
    benchmark(d.parse, bytes(5))

def test_class_sequence_parse_compiled(benchmark):
    d = Sequence(Byte, Byte, Byte, Byte, Byte)
    d = d.compile()
    benchmark(d.parse, bytes(5))

def test_class_sequence_build(benchmark):
    d = Sequence(Byte, Byte, Byte, Byte, Byte)
    benchmark(d.build, [0]*5)

def test_class_sequence_build_compiled(benchmark):
    d = Sequence(Byte, Byte, Byte, Byte, Byte)
    d = d.compile()
    benchmark(d.build, [0]*5)

def test_class_array_parse(benchmark):
    d = Array(100, Byte)
    benchmark(d.parse, bytes(100))

def test_class_array_parse_compiled(benchmark):
    d = Array(100, Byte)
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_array_build(benchmark):
    d = Array(100, Byte)
    benchmark(d.build, [0]*100)

def test_class_array_build_compiled(benchmark):
    d = Array(100, Byte)
    d = d.compile()
    benchmark(d.build, [0]*100)

def test_class_greedyrange_parse(benchmark):
    d = GreedyRange(Byte)
    benchmark(d.parse, bytes(100))

def test_class_greedyrange_parse_compiled(benchmark):
    d = GreedyRange(Byte)
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_greedyrange_build(benchmark):
    d = GreedyRange(Byte)
    benchmark(d.build, [0]*100)

def test_class_repeatuntil_parse(benchmark):
    d = RepeatUntil(obj_ > 0, Byte)
    benchmark(d.parse, bytes(i<100 for i in range(100)))

def test_class_repeatuntil_parse_compiled(benchmark):
    d = RepeatUntil(obj_ > 0, Byte)
    d = d.compile()
    benchmark(d.parse, bytes(i<100 for i in range(100)))

def test_class_repeatuntil_build(benchmark):
    d = RepeatUntil(obj_ > 0, Byte)
    benchmark(d.build, [int(i<99) for i in range(100)])

def test_class_repeatuntil_build_compiled(benchmark):
    d = RepeatUntil(obj_ > 0, Byte)
    d = d.compile()
    benchmark(d.build, [int(i<99) for i in range(100)])

def test_class_const_parse(benchmark):
    d = Const(bytes(10))
    benchmark(d.parse, bytes(10))

def test_class_const_parse_compiled(benchmark):
    d = Const(bytes(10))
    d = d.compile()
    benchmark(d.parse, bytes(10))

def test_class_const_build(benchmark):
    d = Const(bytes(10))
    benchmark(d.build, bytes(10))

def test_class_const_build_compiled(benchmark):
    d = Const(bytes(10))
    d = d.compile()
    benchmark(d.build, bytes(10))

def test_class_computed_parse(benchmark):
    d = Computed(this.entry)
    benchmark(d.parse, bytes(), entry=1)

def test_class_computed_parse_compiled(benchmark):
    d = Computed(this.entry)
    d = d.compile()
    benchmark(d.parse, bytes(), entry=1)

def test_class_computed_build(benchmark):
    d = Computed(this.entry)
    benchmark(d.build, None, entry=1)

def test_class_computed_build_compiled(benchmark):
    d = Computed(this.entry)
    d = d.compile()
    benchmark(d.build, None, entry=1)

# - not supported by compiler
# Index

def test_class_rebuild_parse(benchmark):
    d = Rebuild(Int32ub, 0)
    benchmark(d.parse, bytes(4))

def test_class_rebuild_parse_compiled(benchmark):
    d = Rebuild(Int32ub, 0)
    d = d.compile()
    benchmark(d.parse, bytes(4))

def test_class_rebuild_build(benchmark):
    d = Rebuild(Int32ub, 0)
    benchmark(d.build, None)

def test_class_rebuild_build_compiled(benchmark):
    d = Rebuild(Int32ub, 0)
    d = d.compile()
    benchmark(d.build, None)

def test_class_default_parse(benchmark):
    d = Default(Int32ub, 0)
    benchmark(d.parse, bytes(4))

def test_class_default_parse_compiled(benchmark):
    d = Default(Int32ub, 0)
    d = d.compile()
    benchmark(d.parse, bytes(4))

def test_class_default_build(benchmark):
    d = Default(Int32ub, 0)
    benchmark(d.build, None)

def test_class_default_build_compiled(benchmark):
    d = Default(Int32ub, 0)
    d = d.compile()
    benchmark(d.build, None)

def test_class_check_parse(benchmark):
    d = Check(this.entry == 1)
    benchmark(d.parse, bytes(), entry=1)

def test_class_check_parse_compiled(benchmark):
    d = Check(this.entry == 1)
    d = d.compile()
    benchmark(d.parse, bytes(), entry=1)

def test_class_check_build(benchmark):
    d = Check(this.entry == 1)
    benchmark(d.build, None, entry=1)

def test_class_check_build_compiled(benchmark):
    d = Check(this.entry == 1)
    d = d.compile()
    benchmark(d.build, None, entry=1)

# - raises exception
# Error

def test_class_focusedseq_parse(benchmark):
    d = FocusedSeq("num", Const(bytes(10)), "num"/Int32ub, Terminated)
    benchmark(d.parse, bytes(14))

def test_class_focusedseq_parse_compiled(benchmark):
    d = FocusedSeq("num", Const(bytes(10)), "num"/Int32ub, Terminated)
    d = d.compile()
    benchmark(d.parse, bytes(14))

def test_class_focusedseq_build(benchmark):
    d = FocusedSeq("num", Const(bytes(10)), "num"/Int32ub, Terminated)
    benchmark(d.build, 0)

def test_class_focusedseq_build_compiled(benchmark):
    d = FocusedSeq("num", Const(bytes(10)), "num"/Int32ub, Terminated)
    d = d.compile()
    benchmark(d.build, 0)

def test_class_pickled_parse(benchmark):
    d = Pickled
    if PY3:
        data = b'\x80\x03]q\x00()K\x01G@\x02ffffff}q\x01]q\x02C\x01\x00q\x03X\x00\x00\x00\x00q\x04e.'
    else:
        data = b"(lp0\n(taI1\naF2.3\na(dp1\na(lp2\naS'1'\np3\naS''\np4\na."
    benchmark(d.parse, data)

def test_class_pickled_parse_compiled(benchmark):
    d = Pickled
    d = d.compile()
    if PY3:
        data = b'\x80\x03]q\x00()K\x01G@\x02ffffff}q\x01]q\x02C\x01\x00q\x03X\x00\x00\x00\x00q\x04e.'
    else:
        data = b"(lp0\n(taI1\naF2.3\na(dp1\na(lp2\naS'1'\np3\naS''\np4\na."
    benchmark(d.parse, data)

def test_class_pickled_build(benchmark):
    d = Pickled
    if PY3:
        data = b'\x80\x03]q\x00()K\x01G@\x02ffffff}q\x01]q\x02C\x01\x00q\x03X\x00\x00\x00\x00q\x04e.'
    else:
        data = b"(lp0\n(taI1\naF2.3\na(dp1\na(lp2\naS'1'\np3\naS''\np4\na."
    benchmark(d.build, d.parse(data))

def test_class_numpy_parse(benchmark):
    d = Numpy
    data = b"\x93NUMPY\x01\x00F\x00{'descr': '<i8', 'fortran_order': False, 'shape': (3,), }            \n\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00"
    benchmark(d.parse, data)

def test_class_numpy_parse_compiled(benchmark):
    d = Numpy
    d = d.compile()
    data = b"\x93NUMPY\x01\x00F\x00{'descr': '<i8', 'fortran_order': False, 'shape': (3,), }            \n\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00"
    benchmark(d.parse, data)

def test_class_numpy_build(benchmark):
    d = Numpy
    data = b"\x93NUMPY\x01\x00F\x00{'descr': '<i8', 'fortran_order': False, 'shape': (3,), }            \n\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00"
    benchmark(d.build, d.parse(data))

def test_class_namedtuple1_parse(benchmark):
    t = collections.namedtuple("coord", "x y z")
    d = NamedTuple("coord", "x y z", Array(3, Byte))
    benchmark(d.parse, bytes(3))

def test_class_namedtuple1_parse_compiled(benchmark):
    t = collections.namedtuple("coord", "x y z")
    d = NamedTuple("coord", "x y z", Array(3, Byte))
    d = d.compile()
    benchmark(d.parse, bytes(3))

def test_class_namedtuple1_build(benchmark):
    t = collections.namedtuple("coord", "x y z")
    d = NamedTuple("coord", "x y z", Array(3, Byte))
    benchmark(d.build, t(1,2,3))

def test_class_namedtuple2_parse(benchmark):
    t = collections.namedtuple("coord", "x y z")
    d = NamedTuple("coord", "x y z", Struct("x"/Byte, "y"/Byte, "z"/Byte))
    benchmark(d.parse, bytes(3))

def test_class_namedtuple2_parse_compiled(benchmark):
    t = collections.namedtuple("coord", "x y z")
    d = NamedTuple("coord", "x y z", Struct("x"/Byte, "y"/Byte, "z"/Byte))
    d = d.compile()
    benchmark(d.parse, bytes(3))

def test_class_namedtuple2_build(benchmark):
    t = collections.namedtuple("coord", "x y z")
    d = NamedTuple("coord", "x y z", Struct("x"/Byte, "y"/Byte, "z"/Byte))
    benchmark(d.build, t(x=1,y=2,z=3))

def test_class_timestamp1_parse(benchmark):
    d = Timestamp(Int64ub, 1, 1970)
    benchmark(d.parse, bytes(8))

def test_class_timestamp1_parse_compiled(benchmark):
    d = Timestamp(Int64ub, 1, 1970)
    d = d.compile()
    benchmark(d.parse, bytes(8))

def test_class_timestamp1_build(benchmark):
    import arrow
    d = Timestamp(Int64ub, 1, 1970)
    benchmark(d.build, arrow.Arrow(2000,1,1))

def test_class_timestamp2_parse(benchmark):
    d = Timestamp(Int32ub, "msdos", "msdos")
    benchmark(d.parse, b'H9\x8c"')

def test_class_timestamp2_parse_compiled(benchmark):
    d = Timestamp(Int32ub, "msdos", "msdos")
    d = d.compile()
    benchmark(d.parse, b'H9\x8c"')

def test_class_timestamp2_build(benchmark):
    import arrow
    d = Timestamp(Int32ub, "msdos", "msdos")
    benchmark(d.build, arrow.Arrow(2000,1,1))

def test_class_hex_parse(benchmark):
    d = Hex(GreedyBytes)
    benchmark(d.parse, bytes(100))

def test_class_hex_parse_compiled(benchmark):
    d = Hex(GreedyBytes)
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_hex_build(benchmark):
    d = Hex(GreedyBytes)
    benchmark(d.build, bytes(100))

def test_class_hexdump_parse(benchmark):
    d = HexDump(GreedyBytes)
    benchmark(d.parse, bytes(100))

def test_class_hexdump_parse_compiled(benchmark):
    d = HexDump(GreedyBytes)
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_hexdump_build(benchmark):
    d = HexDump(GreedyBytes)
    benchmark(d.build, bytes(100))

def test_class_union_parse(benchmark):
    d = Union(0, "raw"/Bytes(8), "ints"/Int32ub[2], "shorts"/Int16ub[4], "chars"/Byte[8])
    benchmark(d.parse, bytes(8))

def test_class_union_parse_compiled(benchmark):
    d = Union(0, "raw"/Bytes(8), "ints"/Int32ub[2], "shorts"/Int16ub[4], "chars"/Byte[8])
    d = d.compile()
    benchmark(d.parse, bytes(8))

def test_class_union_build(benchmark):
    d = Union(0, "raw"/Bytes(8), "ints"/Int32ub[2], "shorts"/Int16ub[4], "chars"/Byte[8])
    benchmark(d.build, dict(chars=[0]*8))

def test_class_union_build_compiled(benchmark):
    d = Union(0, "raw"/Bytes(8), "ints"/Int32ub[2], "shorts"/Int16ub[4], "chars"/Byte[8])
    d = d.compile()
    benchmark(d.build, dict(chars=[0]*8))

def test_class_select_parse(benchmark):
    d = Select(Int32ub, CString("utf8"))
    benchmark(d.parse, bytes(20))

def test_class_select_parse_compiled(benchmark):
    d = Select(Int32ub, CString("utf8"))
    d = d.compile()
    benchmark(d.parse, bytes(20))

def test_class_select_build(benchmark):
    d = Select(Int32ub, CString("utf8"))
    benchmark(d.build, u"...")

# - combines performance of other fields
# Optional

def test_class_if_parse(benchmark):
    d = If(this.cond, Byte)
    benchmark(d.parse, bytes(4), cond=True)

def test_class_if_parse_compiled(benchmark):
    d = If(this.cond, Byte)
    d = d.compile()
    benchmark(d.parse, bytes(4), cond=True)

def test_class_if_build(benchmark):
    d = If(this.cond, Byte)
    benchmark(d.build, 0, cond=True)

def test_class_if_build_compiled(benchmark):
    d = If(this.cond, Byte)
    d = d.compile()
    benchmark(d.build, 0, cond=True)

def test_class_ifthenelse_parse(benchmark):
    d = IfThenElse(this.cond, Byte, Byte)
    benchmark(d.parse, bytes(4), cond=True)

def test_class_ifthenelse_parse_compiled(benchmark):
    d = IfThenElse(this.cond, Byte, Byte)
    d = d.compile()
    benchmark(d.parse, bytes(4), cond=True)

def test_class_ifthenelse_build(benchmark):
    d = IfThenElse(this.cond, Byte, Byte)
    benchmark(d.build, 0, cond=True)

def test_class_ifthenelse_build_compiled(benchmark):
    d = IfThenElse(this.cond, Byte, Byte)
    d = d.compile()
    benchmark(d.build, 0, cond=True)

def test_class_switch_parse(benchmark):
    d = Switch(this.n, { 1:Int8ub, 2:Int16ub, 4:Int32ub })
    benchmark(d.parse, bytes(4), n=4)

def test_class_switch_parse_compiled(benchmark):
    d = Switch(this.n, { 1:Int8ub, 2:Int16ub, 4:Int32ub })
    d = d.compile()
    benchmark(d.parse, bytes(4), n=4)

def test_class_switch_build(benchmark):
    d = Switch(this.n, { 1:Int8ub, 2:Int16ub, 4:Int32ub })
    benchmark(d.build, 0, n=4)

def test_class_switch_build_compiled(benchmark):
    d = Switch(this.n, { 1:Int8ub, 2:Int16ub, 4:Int32ub })
    d = d.compile()
    benchmark(d.build, 0, n=4)

# - raises exception
# StopIf

def test_class_padding_parse(benchmark):
    d = Padding(100)
    benchmark(d.parse, bytes(100))

def test_class_padding_parse_compiled(benchmark):
    d = Padding(100)
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_padding_build(benchmark):
    d = Padding(100)
    benchmark(d.build, None)

def test_class_padding_build_compiled(benchmark):
    d = Padding(100)
    d = d.compile()
    benchmark(d.build, None)

def test_class_padded_parse(benchmark):
    d = Padded(100, Byte)
    benchmark(d.parse, bytes(101))

def test_class_padded_parse_compiled(benchmark):
    d = Padded(100, Byte)
    d = d.compile()
    benchmark(d.parse, bytes(101))

def test_class_padded_build(benchmark):
    d = Padded(100, Byte)
    benchmark(d.build, 0)

def test_class_padded_build_compiled(benchmark):
    d = Padded(100, Byte)
    d = d.compile()
    benchmark(d.build, 0)

def test_class_aligned_parse(benchmark):
    d = Aligned(100, Byte)
    benchmark(d.parse, bytes(100))

def test_class_aligned_parse_compiled(benchmark):
    d = Aligned(100, Byte)
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_aligned_build(benchmark):
    d = Aligned(100, Byte)
    benchmark(d.build, 0)

def test_class_aligned_build_compiled(benchmark):
    d = Aligned(100, Byte)
    d = d.compile()
    benchmark(d.build, 0)

# - combines performance of other fields
# AlignedStruct
# BitStruct

def test_class_pointer_parse(benchmark):
    d = Pointer(8, Bytes(4))
    benchmark(d.parse, bytes(12))

def test_class_pointer_parse_compiled(benchmark):
    d = Pointer(8, Bytes(4))
    d = d.compile()
    benchmark(d.parse, bytes(12))

def test_class_pointer_build(benchmark):
    d = Pointer(8, Bytes(4))
    benchmark(d.build, bytes(4))

def test_class_pointer_build_compiled(benchmark):
    d = Pointer(8, Bytes(4))
    d = d.compile()
    benchmark(d.build, bytes(4))

def test_class_peek_parse(benchmark):
    d = Sequence(Peek(Int8ub), Peek(Int16ub))
    benchmark(d.parse, bytes(2))

def test_class_peek_parse_compiled(benchmark):
    d = Sequence(Peek(Int8ub), Peek(Int16ub))
    d = d.compile()
    benchmark(d.parse, bytes(2))

def test_class_peek_build(benchmark):
    d = Sequence(Peek(Int8ub), Peek(Int16ub))
    benchmark(d.build, [None,None])

def test_class_peek_build_compiled(benchmark):
    d = Sequence(Peek(Int8ub), Peek(Int16ub))
    d = d.compile()
    benchmark(d.build, [None,None])

# - not worth measuring
# Seek
# Tell
# Pass
# Terminated

def test_class_rawcopy_parse(benchmark):
    d = RawCopy(Byte)
    benchmark(d.parse, bytes(1))

def test_class_rawcopy_parse_compiled(benchmark):
    d = RawCopy(Byte)
    d = d.compile()
    benchmark(d.parse, bytes(1))

def test_class_rawcopy_build1(benchmark):
    d = RawCopy(Byte)
    benchmark(d.build, dict(data=bytes(1)))

def test_class_rawcopy_build2(benchmark):
    d = RawCopy(Byte)
    benchmark(d.build, dict(value=0))

def test_class_byteswapped1_parse(benchmark):
    d = ByteSwapped(Bytes(100))
    benchmark(d.parse, bytes(100))

def test_class_byteswapped1_parse_compiled(benchmark):
    d = ByteSwapped(Bytes(100))
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_byteswapped1_build(benchmark):
    d = ByteSwapped(Bytes(100))
    benchmark(d.build, bytes(100))

def test_class_bitsswapped1_parse(benchmark):
    d = BitsSwapped(Bytes(100))
    benchmark(d.parse, bytes(100))

def test_class_bitsswapped1_parse_compiled(benchmark):
    d = BitsSwapped(Bytes(100))
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_bitsswapped1_build(benchmark):
    d = BitsSwapped(Bytes(100))
    benchmark(d.build, bytes(100))

def test_class_bitsswapped2_parse(benchmark):
    d = BitsSwapped(RepeatUntil(obj_ == 1, Byte))
    benchmark(d.parse, bytes(99)+b"\x80")

def test_class_bitsswapped2_parse_compiled(benchmark):
    d = BitsSwapped(RepeatUntil(obj_ == 1, Byte))
    d = d.compile()
    benchmark(d.parse, bytes(99)+b"\x80")

def test_class_bitsswapped2_build(benchmark):
    d = BitsSwapped(RepeatUntil(obj_ == 1, Byte))
    benchmark(d.build, [0 if i<100-1 else 1 for i in range(100)])

def test_class_prefixed_parse(benchmark):
    d = Prefixed(Byte, GreedyBytes)
    benchmark(d.parse, b"\xff"+bytes(255))

def test_class_prefixed_parse_compiled(benchmark):
    d = Prefixed(Byte, GreedyBytes)
    d = d.compile()
    benchmark(d.parse, b"\xff"+bytes(255))

def test_class_prefixed_build(benchmark):
    d = Prefixed(Byte, GreedyBytes)
    benchmark(d.build, bytes(255))

def test_class_prefixedarray_parse(benchmark):
    d = PrefixedArray(Byte, Byte)
    benchmark(d.parse, b"\xff"+bytes(255))

def test_class_prefixedarray_parse_compiled(benchmark):
    d = PrefixedArray(Byte, Byte)
    d = d.compile()
    benchmark(d.parse, b"\xff"+bytes(255))

def test_class_prefixedarray_build(benchmark):
    d = PrefixedArray(Byte, Byte)
    benchmark(d.build, [0]*255)

def test_class_prefixedarray_build_compiled(benchmark):
    d = PrefixedArray(Byte, Byte)
    d = d.compile()
    benchmark(d.build, [0]*255)

def test_class_fixedsized_parse(benchmark):
    d = FixedSized(100, GreedyBytes)
    benchmark(d.parse, bytes(100))

def test_class_fixedsized_parse_compiled(benchmark):
    d = FixedSized(100, GreedyBytes)
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_fixedsized_build(benchmark):
    d = FixedSized(100, GreedyBytes)
    benchmark(d.build, bytes(100))

def test_class_fixedsized_build_compiled(benchmark):
    d = FixedSized(100, GreedyBytes)
    d = d.compile()
    benchmark(d.build, bytes(100))

def test_class_nullterminated_parse(benchmark):
    d = NullTerminated(GreedyBytes)
    benchmark(d.parse, b'\x01'*99+b'\x00')

def test_class_nullterminated_parse_compiled(benchmark):
    d = NullTerminated(GreedyBytes)
    d = d.compile()
    benchmark(d.parse, b'\x01'*99+b'\x00')

def test_class_nullterminated_build(benchmark):
    d = NullTerminated(GreedyBytes)
    benchmark(d.build, b'\x01'*99)

def test_class_nullstripped_parse(benchmark):
    d = NullStripped(GreedyBytes)
    benchmark(d.parse, bytes(100))

def test_class_nullstripped_parse_compiled(benchmark):
    d = NullStripped(GreedyBytes)
    d = d.compile()
    benchmark(d.parse, bytes(100))

def test_class_nullstripped_build(benchmark):
    d = NullStripped(GreedyBytes)
    benchmark(d.build, bytes(100))

# - measured by other fields
# RestreamData
# Transformed
# - not compilable
# Restreamed
# ProcessXor
# ProcessRotateLeft
# Checksum
# - decompilable
# Compressed
# - not compilable
# Rebuffered

# - not compilable
# LazyBound

# - not compilable
# ExprAdapter
# ExprSymmetricAdapter
# ExprValidator
# OneOf
# NoneOf
# Filter
# Slicing
# Indexing

def test_overall_parse(benchmark):
    d = example
    benchmark(d.parse, exampledata)

def test_overall_parse_compiled(benchmark):
    d = example
    d = d.compile()
    benchmark(d.parse, exampledata)

def test_overall_build(benchmark):
    d = example
    obj = example.parse(exampledata)
    benchmark(d.build, obj)

def test_overall_build_compiled(benchmark):
    d = example
    d = d.compile()
    obj = example.parse(exampledata)
    benchmark(d.build, obj)
