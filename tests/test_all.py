# -*- coding: utf-8 -*-

import unittest, pytest, os
from declarativeunittest import raises
ontravis = 'TRAVIS' in os.environ

from construct import *
from construct.lib import *

from io import BytesIO
import os, random, itertools, collections, hashlib, math
ident = lambda x: x



def common(format, data=NotImplemented, obj=NotImplemented, size=NotImplemented, eq=True):
    if data is not NotImplemented and obj is not NotImplemented:
        assert format.parse(data) == obj
        assert format.build(obj) == data
    else:
        # following are guaranteed by the above
        if obj is not NotImplemented:
            if eq:
                assert format.parse(format.build(obj)) == obj
            else:
                assert format.parse(format.build(obj))

        if data is not NotImplemented:
            if eq:
                assert format.build(format.parse(data)) == data
            else:
                assert format.build(format.parse(data))
    if size is not NotImplemented:
        if isinstance(size, int):
            assert format.sizeof() == size
        else:
            assert raises(format.sizeof) == size



class TestCore(unittest.TestCase):

    def test_byte(self):
        common(Byte, b"\x00", 0, 1)
        common(Byte, b"\xff", 255, 1)

    def test_ints(self):
        assert Int8ub.parse(b"\x01") == 0x01
        assert Int8ub.build(0x01) == b"\x01"
        assert Int8ub.sizeof() == 1
        assert Int16ub.parse(b"\x01\x02") == 0x0102
        assert Int16ub.build(0x0102) == b"\x01\x02"
        assert Int16ub.sizeof() == 2
        assert Int32ub.parse(b"\x01\x02\x03\x04") == 0x01020304
        assert Int32ub.build(0x01020304) == b"\x01\x02\x03\x04"
        assert Int32ub.sizeof() == 4
        assert Int64ub.parse(b"\x01\x02\x03\x04\x05\x06\x07\x08") == 0x0102030405060708
        assert Int64ub.build(0x0102030405060708) == b"\x01\x02\x03\x04\x05\x06\x07\x08"
        assert Int64ub.sizeof() == 8
        assert Int8sb.parse(b"\x01") == 0x01
        assert Int8sb.build(0x01) == b"\x01"
        assert Int8sb.sizeof() == 1
        assert Int16sb.parse(b"\x01\x02") == 0x0102
        assert Int16sb.build(0x0102) == b"\x01\x02"
        assert Int16sb.sizeof() == 2
        assert Int32sb.parse(b"\x01\x02\x03\x04") == 0x01020304
        assert Int32sb.build(0x01020304) == b"\x01\x02\x03\x04"
        assert Int32sb.sizeof() == 4
        assert Int64sb.parse(b"\x01\x02\x03\x04\x05\x06\x07\x08") == 0x0102030405060708
        assert Int64sb.build(0x0102030405060708) == b"\x01\x02\x03\x04\x05\x06\x07\x08"
        assert Int64sb.sizeof() == 8
        assert Int8ul.parse(b"\x01") == 0x01
        assert Int8ul.build(0x01) == b"\x01"
        assert Int8ul.sizeof() == 1
        assert Int16ul.parse(b"\x01\x02") == 0x0201
        assert Int16ul.build(0x0201) == b"\x01\x02"
        assert Int16ul.sizeof() == 2
        assert Int32ul.parse(b"\x01\x02\x03\x04") == 0x04030201
        assert Int32ul.build(0x04030201) == b"\x01\x02\x03\x04"
        assert Int32ul.sizeof() == 4
        assert Int64ul.parse(b"\x01\x02\x03\x04\x05\x06\x07\x08") == 0x0807060504030201
        assert Int64ul.build(0x0807060504030201) == b"\x01\x02\x03\x04\x05\x06\x07\x08"
        assert Int64ul.sizeof() == 8
        assert Int8sl.parse(b"\x01") == 0x01
        assert Int8sl.build(0x01) == b"\x01"
        assert Int8sl.sizeof() == 1
        assert Int16sl.parse(b"\x01\x02") == 0x0201
        assert Int16sl.build(0x0201) == b"\x01\x02"
        assert Int16sl.sizeof() == 2
        assert Int32sl.parse(b"\x01\x02\x03\x04") == 0x04030201
        assert Int32sl.build(0x04030201) == b"\x01\x02\x03\x04"
        assert Int32sl.sizeof() == 4
        assert Int64sl.parse(b"\x01\x02\x03\x04\x05\x06\x07\x08") == 0x0807060504030201
        assert Int64sl.build(0x0807060504030201) == b"\x01\x02\x03\x04\x05\x06\x07\x08"
        assert Int64sl.sizeof() == 8

    def test_ints24(self):
        common(Int24ub, b"\x01\x02\x03", 0x010203, 3)
        common(Int24ul, b"\x01\x02\x03", 0x030201, 3)
        common(Struct(int24=Int24ub), b"\x01\x02\x03", Container(int24=0x010203), 3)
        common(Struct(int24=Int24ul), b"\x01\x02\x03", Container(int24=0x030201), 3)

    def test_varint(self):
        common(VarInt, b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x10", 2**123, SizeofError)
        for n in [0,1,5,100,255,256,65535,65536,2**32,2**100]:
            common(VarInt, obj=n)
            assert len(VarInt.build(n)) >= len("%x" % n)//2
        for n in range(0, 127):
            common(VarInt, int2byte(n), n, SizeofError)

        assert raises(VarInt.parse, b"") == FieldError
        assert raises(VarInt.build, -1) == ValueError

    def test_varint_randomized(self):
        for i in range(100):
            common(VarInt, obj=random.randrange(0, 2**1024), size=SizeofError)
            common(VarInt, data=os.urandom(1024) + b"\x00\xff", eq=False, size=SizeofError)

    def test_floats(self):
        assert Single.build(1.2) == b"?\x99\x99\x9a"
        assert Double.build(1.2) == b"?\xf3333333"

    def test_floats_randomized(self):
        for i in range(100):
            x = random.random()
            assert abs(Single.parse(Single.build(x)) - x) < 1e-3
            assert Double.parse(Double.build(x)) == x

    def test_bytes(self):
        assert Bytes(4).parse(b"12345678") == b"1234"
        assert Bytes(4).build(b"1234") == b"1234"
        assert raises(Bytes(4).parse, b"") == FieldError
        assert raises(Bytes(4).build, b"toolong") == FieldError
        assert Bytes(4).build(1) == b"\x00\x00\x00\x01"
        assert Bytes(4).build(0x01020304) == b"\x01\x02\x03\x04"
        assert Bytes(4).sizeof() == 4

        assert Bytes(lambda ctx: ctx.n).parse(b"12345678",n=4) == b"1234"
        assert Bytes(lambda ctx: ctx.n).build(b"1234",n=4) == b"1234"
        assert Bytes(lambda ctx: ctx.n).sizeof(n=4) == 4
        assert Bytes(lambda ctx: ctx.n).build(1, n=4) == b"\x00\x00\x00\x01"
        assert raises(Bytes(lambda ctx: ctx.n).build, b"", n=4) == FieldError
        assert raises(Bytes(lambda ctx: ctx.n).build, b"toolong", n=4) == FieldError
        assert raises(Bytes(lambda ctx: ctx.n).sizeof) == SizeofError

    def test_greedybytes(self):
        common(GreedyBytes, b"1234", b"1234", SizeofError)

    def test_formatfield(self):
        assert FormatField("<","L").parse(b"\x12\x34\x56\x78") == 0x78563412
        assert FormatField("<","L").build(0x78563412) == b"\x12\x34\x56\x78"
        assert raises(FormatField("<","L").parse, b"") == FieldError
        assert raises(FormatField("<","L").parse, b"\x12\x34\x56") == FieldError
        assert raises(FormatField("<","L").build, "string not int") == FieldError
        assert FormatField("<","L").sizeof() == 4
        assert raises(FormatField("<","L").build, 2**100) == FieldError
        assert raises(FormatField("<","L").build, 9e9999) == FieldError

    def test_formatfield_ints_randomized(self):
        for endianess,dtype in itertools.product("<>=","bhlqBHLQ"):
            d = FormatField(endianess,dtype)
            for i in range(100):
                common(d, obj=random.randrange(0, 256**d.sizeof()//2))
                common(d, data=os.urandom(d.sizeof()))

    def test_formatfield_floats_randomized(self):
        # there is a roundoff eror because Python float is a C double
        # http://stackoverflow.com/questions/39619636/struct-unpackstruct-packfloat-has-roundoff-error
        # and analog although that was misplaced
        # http://stackoverflow.com/questions/39676482/struct-packstruct-unpackfloat-is-inconsistent-on-py3
        for endianess,dtype in itertools.product("<>=","fd"):
            d = FormatField(endianess, dtype)
            for i in range(100):
                x = random.random()*12345
                if dtype == "d":
                    assert d.parse(d.build(x)) == x
                else:
                    assert abs(d.parse(d.build(x)) - x) < 1e-3
            for i in range(100):
                b = os.urandom(d.sizeof())
                if not math.isnan(d.parse(b)):
                    assert d.build(d.parse(b)) == b

    def test_array(self):
        assert Byte[4].parse(b"1234") == [49, 50, 51, 52]
        assert Byte[4].build([49, 50, 51, 52]) == b"1234"

        assert Array(3,Byte).parse(b"\x01\x02\x03") == [1,2,3]
        assert Array(3,Byte).build([1,2,3]) == b"\x01\x02\x03"
        assert Array(3,Byte).parse(b"\x01\x02\x03additionalgarbage") == [1,2,3]
        assert raises(Array(3,Byte).parse, b"") == RangeError
        assert raises(Array(3,Byte).build, [1,2]) == RangeError
        assert raises(Array(3,Byte).build, [1,2,3,4,5,6,7,8]) == RangeError
        assert Array(3,Byte).sizeof() == 3

        assert Array(lambda ctx: 3, Byte).parse(b"\x01\x02\x03", n=3) == [1,2,3]
        assert Array(lambda ctx: 3, Byte).parse(b"\x01\x02\x03additionalgarbage", n=3) == [1,2,3]
        assert raises(Array(lambda ctx: 3, Byte).parse, b"", n=3) == RangeError
        assert Array(lambda ctx: 3, Byte).build([1,2,3], n=3) == b"\x01\x02\x03"
        assert raises(Array(lambda ctx: 3, Byte).build, [1,2], n=3) == RangeError
        assert Array(lambda ctx: ctx.n, Byte).parse(b"\x01\x02\x03", n=3) == [1,2,3]
        assert Array(lambda ctx: ctx.n, Byte).build([1,2,3], n=3) == b"\x01\x02\x03"
        assert raises(Array(lambda ctx: ctx.n, Byte).sizeof) == SizeofError
        assert Array(lambda ctx: ctx.n, Byte).sizeof(n=4) == 4

    def test_prefixedarray(self):
        common(PrefixedArray(Byte,Byte), b"\x02\x0a\x0b", [10,11], SizeofError)
        assert PrefixedArray(Byte, Byte).parse(b"\x03\x01\x02\x03") == [1,2,3]
        assert PrefixedArray(Byte, Byte).parse(b"\x00") == []
        assert PrefixedArray(Byte, Byte).build([1,2,3]) == b"\x03\x01\x02\x03"
        assert raises(PrefixedArray(Byte, Byte).parse, b"") == RangeError
        assert raises(PrefixedArray(Byte, Byte).parse, b"\x03\x01") == RangeError
        assert raises(PrefixedArray(Byte, Byte).sizeof) == SizeofError

    def test_prefixedarray_alternative2(self):
        def PrefixedArray(lengthfield, subcon):
            return FocusedSeq(1, 
                "count"/Rebuild(lengthfield, len_(this.items)), 
                "items"/subcon[this.count],
            )
        common(PrefixedArray(Byte,Byte), b"\x02\x0a\x0b", [10,11], SizeofError)

    @pytest.mark.xfail(raises=TypeError, reason="object of type 'instancemethod' has no len()")
    def test_prefixedarray_alternative3(self):
        def PrefixedArray(lengthfield, subcon):
            return FocusedSeq(1, 
                "count"/Rebuild(lengthfield, lambda ctx: len(ctx.items)), 
                "items"/Array(lambda ctx: ctx.count, subcon),
            )
        common(PrefixedArray(Byte,Byte), b"\x02\x0a\x0b", [10,11], AttributeError)

    def test_prefixedarray_alternative4(self):
        def PrefixedArray(lengthfield, subcon):
            return ExprAdapter(
                "count"/lengthfield >> "items"/subcon[lambda ctx: ctx.count],
                encoder = lambda obj,ctx: [len(obj), obj],
                decoder = lambda obj,ctx: obj[1],
            )
        common(PrefixedArray(Byte,Byte), b"\x02\x0a\x0b", [10,11], SizeofError)

    def test_range(self):
        assert Byte[2:4].parse(b"1234567890") == [49, 50, 51, 52]
        assert Byte[2:4].build([49, 50, 51, 52]) == b"1234"
        assert Byte[:4].parse(b"1234567890") == [49, 50, 51, 52]
        assert Byte[:4].build([49, 50, 51, 52]) == b"1234"
        assert raises(Byte[2:].parse, b"") == RangeError
        assert raises(Byte[2:].build, []) == RangeError

        assert Range(3, 5, Byte).parse(b"\x01\x02\x03") == [1,2,3]
        assert Range(3, 5, Byte).parse(b"\x01\x02\x03\x04") == [1,2,3,4]
        assert Range(3, 5, Byte).parse(b"\x01\x02\x03\x04\x05") == [1,2,3,4,5]
        assert Range(3, 5, Byte).parse(b"\x01\x02\x03\x04\x05\x06") == [1,2,3,4,5]
        assert raises(Range(3, 5, Byte).parse, b"") == RangeError
        assert Range(3, 5, Byte).build([1,2,3]) == b"\x01\x02\x03"
        assert Range(3, 5, Byte).build([1,2,3,4]) == b"\x01\x02\x03\x04"
        assert Range(3, 5, Byte).build([1,2,3,4,5]) == b"\x01\x02\x03\x04\x05"
        assert raises(Range(3, 5, Byte).build, [1,2]) == RangeError
        assert raises(Range(3, 5, Byte).build, [1,2,3,4,5,6]) == RangeError
        assert raises(Range(3, 5, Byte).build, 0) == RangeError
        assert raises(Range(3, 5, Byte).sizeof) == SizeofError
        assert Range(0, 100, Struct("id"/Byte)).parse(b'\x01\x02') == [Container(id=1),Container(id=2)]
        assert Range(0, 100, Struct("id"/Byte)).build([dict(id=i) for i in range(5)]) == b'\x00\x01\x02\x03\x04'
        assert raises(Range(0, 100, Struct("id"/Byte)).build, dict(id=1)) == RangeError
        assert raises(Range(0, 100, Struct("id"/Byte)).sizeof) == SizeofError
        assert Range(1, 1, Byte).sizeof() == 1
        assert raises(Range(1, 1, VarInt).sizeof) == SizeofError
        assert raises(Range(1, 9, Byte).sizeof) == SizeofError

    def test_greedyrange(self):
        common(GreedyRange(Byte), b"", [], SizeofError)
        common(GreedyRange(Byte), b"\x01\x02", [1,2], SizeofError)
        common(Byte[:], b"", [], SizeofError)
        common(Byte[:], b"\x01\x02", [1,2], SizeofError)

    def test_repeatuntil(self):
        assert RepeatUntil(obj_ == 9, Byte).parse(b"\x02\x03\x09garbage") == [2,3,9]
        assert RepeatUntil(obj_ == 9, Byte).build([2,3,9,1,1,1]) == b"\x02\x03\x09"
        assert raises(RepeatUntil(obj_ == 9, Byte).parse, b"\x02\x03\x08") == RangeError
        assert raises(RepeatUntil(obj_ == 9, Byte).build, [2,3,8]) == RangeError
        assert raises(RepeatUntil(obj_ == 9, Byte).sizeof) == SizeofError

    def test_struct(self):
        assert Struct("a" / Int16ul, "b" / Byte).parse(b"\x01\x00\x02") == Container(a=1)(b=2)
        assert Struct("a" / Int16ul, "b" / Byte).build(Container(a=1)(b=2)) == b"\x01\x00\x02"
        assert Struct("a"/Struct("b"/Byte)).parse(b"\x01") == Container(a=Container(b=1))
        assert Struct("a"/Struct("b"/Byte)).build(Container(a=Container(b=1))) == b"\x01"
        assert Struct("a"/Struct("b"/Byte)).sizeof() == 1
        assert raises(Struct("missingkey"/Byte).build, dict()) == KeyError
        assert Struct("a"/Byte, "a"/VarInt, "a"/Pass).build(dict(a=1)) == b"\x01\x01"
        assert Struct().parse(b"") == Container()
        assert Struct().build(dict()) == b""
        assert Struct(Padding(2)).parse(b"\x00\x00") == Container()
        assert Struct(Padding(2)).build(dict()) == b"\x00\x00"
        assert Struct(Padding(2)).sizeof() == 2
        assert raises(Struct(Bytes(this.missing)).sizeof) == SizeofError

    def test_struct_nested_embedded(self):
        assert Struct("a" / Byte, "b" / Int16ub, "inner" / Struct("c" / Byte, "d" / Byte)).parse(b"\x01\x00\x02\x03\x04") == Container(a=1)(b=2)(inner=Container(c=3)(d=4))
        assert Struct("a" / Byte, "b" / Int16ub, "inner" / Struct("c" / Byte, "d" / Byte)).build(Container(a=1)(b=2)(inner=Container(c=3)(d=4))) == b"\x01\x00\x02\x03\x04"
        assert Struct("a" / Byte, "b" / Int16ub, Embedded("inner" / Struct("c" / Byte, "d" / Byte))).parse(b"\x01\x00\x02\x03\x04") == Container(a=1)(b=2)(c=3)(d=4)
        assert Struct("a" / Byte, "b" / Int16ub, Embedded("inner" / Struct("c" / Byte, "d" / Byte))).build(Container(a=1)(b=2)(c=3)(d=4)) == b"\x01\x00\x02\x03\x04"

    @pytest.mark.xfail(not supportskwordered, reason="ordered kw was introduced in 3.6 and pypy")
    def test_struct_kwctor(self):
        common(Struct(a=Byte, b=Byte, c=Byte, d=Byte), b"\x01\x02\x03\x04", Container(a=1,b=2,c=3,d=4), 4)

    def test_sequence(self):
        common(Sequence(Int8ub, Int16ub), b"\x01\x00\x02", [1,2], 3)
        common(Int8ub >> Int16ub, b"\x01\x00\x02", [1,2], 3)

    def test_sequence_nested_embedded(self):
        common(Sequence(Int8ub, Int16ub, Sequence(Int8ub, Int8ub)), b"\x01\x00\x02\x03\x04", [1,2,[3,4]], 5)
        common(Sequence(Int8ub, Int16ub, Embedded(Sequence(Int8ub, Int8ub))), b"\x01\x00\x02\x03\x04", [1,2,3,4], 5)

    def test_computed(self):
        assert Computed(lambda ctx: "moo").parse(b"") == "moo"
        assert Computed(lambda ctx: "moo").build(None) == b""
        assert Computed(lambda ctx: "moo").sizeof() == 0
        assert Struct("c" / Computed(lambda ctx: "moo")).parse(b"") == Container(c="moo")
        assert Struct("c" / Computed(lambda ctx: "moo")).build({}) == b""
        assert Struct("c" / Computed(lambda ctx: "moo")).build(dict()) == b""
        assert Struct("c" / Computed(lambda ctx: "moo")).build(Container()) == b""
        assert raises(Computed(lambda ctx: ctx.missing).parse, b"") == AttributeError
        assert raises(Computed(lambda ctx: ctx["missing"]).parse, b"") == KeyError

        assert Computed(255).parse(b"") == 255
        assert Computed(255).build(None) == b""
        assert Struct(c=Computed(255)).parse(b"") == dict(c=255)
        assert Struct(c=Computed(255)).build({}) == b""

    def test_rawcopy(self):
        assert RawCopy(Byte).parse(b"\xff") == dict(data=b"\xff", value=255, offset1=0, offset2=1, length=1)
        assert RawCopy(Byte).build(dict(data=b"\xff")) == b"\xff"
        assert RawCopy(Byte).build(dict(value=255)) == b"\xff"
        assert RawCopy(Byte).sizeof() == 1

    def test_tell(self):
        assert Tell.parse(b"") == 0
        assert Tell.build(None) == b""
        assert Tell.sizeof() == 0
        assert Struct("a"/Tell, "b"/Byte, "c"/Tell).parse(b"\xff") == Container(a=0)(b=255)(c=1)
        assert Struct("a"/Tell, "b"/Byte, "c"/Tell).build(Container(a=0)(b=255)(c=1)) == b"\xff"
        assert Struct("a"/Tell, "b"/Byte, "c"/Tell).build(dict(b=255)) == b"\xff"

    def test_seek(self):
        assert (Seek(5) >> Byte).parse(b"01234x") == [5,120]
        assert (Bytes(10) >> Seek(5) >> Byte).build([b"0123456789",None,255]) == b"01234\xff6789"
        assert Seek(5).parse(b"") == 5
        assert Seek(5).build(None) == b""
        assert raises(Seek(5).sizeof) == SizeofError

        assert (Seek(10,1) >> Seek(-5,1) >> Bytes(1)).parse(b"0123456789") == [10,5,b"5"]

    def test_pass(self):
        common(Pass, b"", None, 0)
        common(Struct("empty"/Pass), b"", Container(empty=None), 0)

    def test_terminated(self):
        common(Terminated, b"", None, 0)
        common(Struct("end"/Terminated), b"", Container(end=None), 0)
        assert raises(Terminated.parse, b"x") == TerminatedError
        assert raises(Struct("end"/Terminated).parse, b"x") == TerminatedError

    def test_error(self):
        assert raises(Error.parse, b"") == ExplicitError
        assert raises(Error.build, None) == ExplicitError
        assert ("x"/Int8sb >> IfThenElse(this.x > 0, Int8sb, Error)).parse(b"\x01\x05") == [1,5]
        assert raises(("x"/Int8sb >> IfThenElse(this.x > 0, Int8sb, Error)).parse, b"\xff\x05") == ExplicitError

    def test_pointer(self):
        common(Pointer(lambda ctx: 2, "pointer"/Byte), b"\x00\x00\x07", 7, 0)

    def test_const(self):
        common(Const(b"MZ"), b"MZ", b"MZ", 2)
        common(Const(Bytes(4), b"****"), b"****", b"****", 4)
        common(Const(Int32ul, 255), b"\xff\x00\x00\x00", 255, 4)
        assert raises(Const(b"MZ").parse, b"ELF") == ConstError
        assert raises(Const(b"MZ").build, b"???") == ConstError
        assert raises(Const(Int32ul, 255).parse, b"\x00\x00\x00\x00") == ConstError
        common(Struct(sig=Const(b"MZ")), b"MZ", Container(sig=b"MZ"), 2)
        assert Struct(sig=Const(b"MZ")).build({}) == b"MZ"

    def test_switch(self):
        assert Switch(lambda ctx: 5, {1:Byte, 5:Int16ub}).parse(b"\x00\x02") == 2
        assert Switch(lambda ctx: 6, {1:Byte, 5:Int16ub}, default=Byte).parse(b"\x00\x02") == 0
        assert Switch(lambda ctx: 5, {1:Byte, 5:Int16ub}, includekey=True).parse(b"\x00\x02") == (5,2)
        assert Switch(lambda ctx: 5, {1:Byte, 5:Int16ub}).build(2) == b"\x00\x02"
        assert Switch(lambda ctx: 6, {1:Byte, 5:Int16ub}, default=Byte).build(9) == b"\x09"
        assert Switch(lambda ctx: 5, {1:Byte, 5:Int16ub}, includekey=True).build((5,2)) == b"\x00\x02"
        assert raises(Switch(lambda ctx: 6, {1:Byte, 5:Int16ub}).parse, b"\x00\x02") == SwitchError
        assert raises(Switch(lambda ctx: 6, {1:Byte, 5:Int16ub}).build, 9) == SwitchError
        assert raises(Switch(lambda ctx: 5, {1:Byte, 5:Int16ub}, includekey=True).build, (89,2)) == SwitchError
        assert Switch(lambda ctx: 5, {1:Byte, 5:Int16ub}).sizeof() == 2
        assert raises(Switch(lambda ctx: 5, {}).sizeof) == SwitchError

    def test_ifthenelse(self):
        common(IfThenElse(True_,  Int8ub, Int16ub), b"\x01", 1, 1)
        common(IfThenElse(False_, Int8ub, Int16ub), b"\x00\x01", 1, 2)

    def test_if(self):
        common(If(True_,  Int8ub), b"\x01", 1, 1)
        common(If(False_, Int8ub), b"", None, 0)

    def test_padding(self):
        assert Padding(4).parse(b"\x00\x00\x00\x00") == None
        assert Padding(4).build(None) == b"\x00\x00\x00\x00"
        assert Padding(4).sizeof() == 4
        assert Padding(4, strict=True).parse(b"\x00\x00\x00\x00") == None
        assert Padding(4, strict=True).build(None) == b"\x00\x00\x00\x00"
        assert Padding(4, pattern=b'x', strict=True).parse(b"xxxx") == None
        assert raises(Padding(4, strict=True).parse, b"????") == PaddingError
        assert raises(Padding(4, pattern=b'x', strict=True).parse, b"????") == PaddingError
        assert raises(Padding, 4, pattern=b"??") == PaddingError
        assert raises(Padding, 4, pattern=u"?") == PaddingError

    def test_padded(self):
        assert Padded(4, Byte).parse(b"\x01\x00\x00\x00") == 1
        assert Padded(4, Byte).build(1) == b"\x01\x00\x00\x00"
        assert Padded(4, Byte).sizeof() == 4
        assert Padded(4, Byte, strict=True).parse(b"\x01\x00\x00\x00") == 1
        assert raises(Padded(4, Byte, strict=True).parse, b"\x01???") == PaddingError
        assert Padded(4, Byte, strict=True).build(1) == b"\x01\x00\x00\x00"
        assert Padded(4, Byte, pattern=b'x', strict=True).parse(b"\x01xxx") == 1
        assert raises(Padded(4, Byte, pattern=b'x', strict=True).parse, b"\x01???") == PaddingError
        assert raises(Padded, 4, Byte, pattern=b"??") == PaddingError
        assert raises(Padded, 4, Byte, pattern=u"?") == PaddingError
        assert Padded(4, VarInt).sizeof() == 4
        assert Padded(4, Byte[this.missing]).sizeof() == 4

    def test_aligned(self):
        assert Aligned(4, Byte).parse(b"\x01\x00\x00\x00") == 1
        assert Aligned(4, Byte).build(1) == b"\x01\x00\x00\x00"
        assert Aligned(4, Byte).sizeof() == 4
        assert Struct(Aligned(4, "a"/Byte), "b"/Byte).parse(b"\x01\x00\x00\x00\x02") == Container(a=1)(b=2)
        assert Struct(Aligned(4, "a"/Byte), "b"/Byte).build(Container(a=1)(b=2)) == b"\x01\x00\x00\x00\x02"
        assert Struct(Aligned(4, "a"/Byte), "b"/Byte).sizeof() == 5
        assert Aligned(4, Int8ub).build(1) == b"\x01\x00\x00\x00"
        assert Aligned(4, Int16ub).build(1) == b"\x00\x01\x00\x00"
        assert Aligned(4, Int32ub).build(1) == b"\x00\x00\x00\x01"
        assert Aligned(4, Int64ub).build(1) == b"\x00\x00\x00\x00\x00\x00\x00\x01"
        assert Aligned(this.m, Byte).parse(b"\xff\x00", dict(m=2)) == 255
        assert Aligned(this.m, Byte).build(255, dict(m=2)) == b"\xff\x00"
        assert Aligned(this.m, Byte).sizeof(dict(m=2)) == 2
        assert raises(Aligned(this.m, Byte).sizeof) == SizeofError

    def test_alignedstruct(self):
        assert AlignedStruct(4, "a"/Int8ub, "b"/Int16ub, pattern=b"?").parse(b"\x01???\x00\x05??") == Container(a=1)(b=5)
        assert AlignedStruct(4, "a"/Int8ub, "b"/Int16ub, pattern=b"?").build(dict(a=1,b=5)) == b"\x01???\x00\x05??"

    def test_from_issue_87(self):
        assert ("string_name" / Byte).parse(b"\x01") == 1
        assert (u"unicode_name" / Byte).parse(b"\x01") == 1
        assert (b"bytes_name" / Byte).parse(b"\x01") == 1
        assert (None / Byte).parse(b"\x01") == 1

    def test_operators(self):
        common(Struct(Renamed("new", Renamed("old", Byte))), b"\x01", Container(new=1), 1)
        common(Struct("new" / ("old" / Byte)), b"\x01", Container(new=1), 1)
        common(Array(4, Byte), b"\x01\x02\x03\x04", [1,2,3,4], 4)
        common(Byte[4], b"\x01\x02\x03\x04", [1,2,3,4], 4)
        assert raises(Byte[2:3].parse, b"\x01") == RangeError
        assert Byte[2:3].parse(b"\x01\x02") == [1,2]
        assert Byte[2:3].parse(b"\x01\x02\x03") == [1,2,3]
        assert Byte[2:3].parse(b"\x01\x02\x03") == [1,2,3]
        assert Byte[2:3].parse(b"\x01\x02\x03\x04") == [1,2,3]
        assert raises(lambda: Byte[2:3:1]) == ValueError
        common(Struct("nums" / Byte[4]), b"\x01\x02\x03\x04", Container(nums=[1,2,3,4]), 4)
        common(Int8ub >> Int16ub, b"\x01\x00\x02", [1,2], 3)
        common(Int8ub >> Int16ub >> Int32ub, b"\x01\x00\x02\x00\x00\x00\x03", [1,2,3], 7)
        common(Int8ub[2] >> Int16ub[2], b"\x01\x02\x00\x03\x00\x04", [[1,2],[3,4]], 6)
        common(Sequence(Embedded(Sequence(Int8ub)), Embedded(Sequence(Int16ub)) ), b"\x01\x00\x02", [1,2], 3)
        common(Sequence(Int8ub) >> Sequence(Int16ub), b"\x01\x00\x02", [1,2], 3)
        common(Struct("count"/Byte, "items"/Byte[this.count], Pass, Terminated), b"\x03\x01\x02\x03", Container(count=3)(items=[1,2,3]), SizeofError)
        common("count"/Byte + "items"/Byte[this.count] + Pass + Terminated, b"\x03\x01\x02\x03", Container(count=3)(items=[1,2,3]), SizeofError)
        common(Struct(Embedded(Struct(a=Byte)), Embedded(Struct(b=Byte)) ), b"\x01\x02", Container(a=1)(b=2), 2)
        common(Struct(a=Byte) + Struct(b=Byte), b"\x01\x02", Container(a=1)(b=2), 2)

    def test_renamed(self):
        common(Struct(Renamed("new", Renamed("old", Byte))), b"\x01", Container(new=1), 1)

    def test_alias(self):
        assert Alias("b","a").parse(b"",Container(a=1)) == 1
        assert Alias("b","a").build(None,Container(a=1)) == b""
        assert Alias("b","a").sizeof() == 0
        assert Struct("a"/Byte, Alias("b","a")).parse(b"\x01") == Container(a=1)(b=1)
        assert Struct("a"/Byte, Alias("b","a")).build(dict(a=1)) == b"\x01"
        assert Struct("a"/Byte, Alias("b","a")).sizeof() == 1

    def test_bitsinteger(self):
        assert BitsInteger(8).parse(b"\x01\x01\x01\x01\x01\x01\x01\x01") == 255
        assert BitsInteger(8).build(255) == b"\x01\x01\x01\x01\x01\x01\x01\x01"
        assert BitsInteger(8).sizeof() == 8
        assert BitsInteger(8, signed=True).parse(b"\x01\x01\x01\x01\x01\x01\x01\x01") == -1
        assert BitsInteger(8, signed=True).build(-1) == b"\x01\x01\x01\x01\x01\x01\x01\x01"
        assert BitsInteger(8, swapped=True, bytesize=4).parse(b"\x01\x01\x01\x01\x00\x00\x00\x00") == 0x0f
        assert BitsInteger(8, swapped=True, bytesize=4).build(0x0f) == b"\x01\x01\x01\x01\x00\x00\x00\x00"
        assert BitsInteger(lambda ctx: 8).parse(b"\x01" * 8) == 255
        assert BitsInteger(lambda ctx: 8).build(255) == b"\x01" * 8
        assert BitsInteger(lambda ctx: 8).sizeof() == 8
        assert raises(BitsInteger(this.missing).sizeof) == SizeofError

    def test_bytesinteger(self):
        assert BytesInteger(4).parse(b"\x00\x00\x00\xff") == 255
        assert BytesInteger(4).build(255) == b"\x00\x00\x00\xff"
        assert BytesInteger(4).sizeof() == 4
        assert BytesInteger(4, signed=True).parse(b"\xff\xff\xff\xff") == -1
        assert BytesInteger(4, signed=True).build(-1) == b"\xff\xff\xff\xff"
        assert BytesInteger(4, swapped=True, bytesize=2).parse(b"\x00\xff\x00\x00") == 255
        assert BytesInteger(4, swapped=True, bytesize=2).build(255) == b"\x00\xff\x00\x00"
        assert BytesInteger(lambda ctx: 4).parse(b"\x00\x00\x00\xff") == 255
        assert BytesInteger(lambda ctx: 4).build(255) == b"\x00\x00\x00\xff"
        assert BytesInteger(lambda ctx: 4).sizeof() == 4
        assert raises(BytesInteger(this.missing).sizeof) == SizeofError

    def test_bitwise(self):
        assert Bitwise(Bytes(8)).parse(b"\xff") == b"\x01\x01\x01\x01\x01\x01\x01\x01"
        assert Bitwise(Bytes(8)).build(b"\x01\x01\x01\x01\x01\x01\x01\x01") == b"\xff"
        assert Bitwise(Bytes(8)).sizeof() == 1
        assert Bitwise(Bytes(lambda ctx: 8)).parse(b"\xff") == b"\x01\x01\x01\x01\x01\x01\x01\x01"
        assert Bitwise(Bytes(lambda ctx: 8)).build(b"\x01\x01\x01\x01\x01\x01\x01\x01") == b"\xff"
        assert Bitwise(Bytes(lambda ctx: 8)).sizeof() == 1

        assert Bitwise(Array(8,Bit)).parse(b"\xff") == [1,1,1,1,1,1,1,1]
        assert Bitwise(Array(8,Bit)).build([1,1,1,1,1,1,1,1]) == b"\xff"
        assert Bitwise(Array(2,Nibble)).parse(b"\xff") == [15,15]
        assert Bitwise(Array(2,Nibble)).build([15,15]) == b"\xff"
        assert Bitwise(Array(1,Octet)).parse(b"\xff") == [255]
        assert Bitwise(Array(1,Octet)).build([255]) == b"\xff"

    def test_bitstruct(self):
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "d"/BitsInteger(5)).parse(b"\xe1\x1f") == Container(a=7)(b=False)(c=8)(d=31)
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "d"/BitsInteger(5)).build(Container(a=7)(b=False)(c=8)(d=31)) == b"\xe1\x1f"
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "d"/BitsInteger(5)).sizeof() == 2
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "sub"/Struct("d"/Nibble, "e"/Bit)).parse(b"\xe1\x1f") == Container(a=7)(b=False)(c=8)(sub=Container(d=15)(e=1))
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "sub"/Struct("d"/Nibble, "e"/Bit)).sizeof() == 2
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "sub"/Struct("d"/Nibble, "e"/Bit)).build(Container(a=7)(b=False)(c=8)(sub=Container(d=15)(e=1))) == b"\xe1\x1f"

    def test_embeddedbitstruct(self):
        d = Struct(
            "len" / Byte, 
            EmbeddedBitStruct("data" / BitsInteger(8)),
        )
        assert d.parse(b"\x08\xff") == Container(len=8)(data=255)
        assert d.build(dict(len=8,data=255)) == b"\x08\xff"
        assert d.sizeof() == 2

    def test_bitstruct_from_issue_39(self):
        d = Struct(
            "len" / Byte, 
            EmbeddedBitStruct("data" / BitsInteger(lambda ctx: ctx._.len)),
        )
        assert d.parse(b"\x08\xff") == Container(len=8)(data=255)
        assert d.build(dict(len=8,data=255)) == b"\x08\xff"
        assert raises(d.sizeof) == SizeofError

    def test_bytewise(self):
        assert Bitwise(Bytewise(Bytes(1))).parse(b"\xff") == b"\xff"
        assert Bitwise(Bytewise(Bytes(1))).build(b"\xff") == b"\xff"
        assert Bitwise(Bytewise(Bytes(1))).sizeof() == 1
        assert BitStruct(Nibble, "num"/Bytewise(Int24ub), Nibble).parse(b"\xf0\x10\x20\x3f") == Container(num=0x010203)
        assert Bitwise(Sequence(Nibble, Bytewise(Int24ub), Nibble)).parse(b"\xf0\x10\x20\x3f") == [0x0f,0x010203,0x0f]

    def test_byteswapped(self):
        assert ByteSwapped(Bytes(5)).parse(b"12345?????") == b"54321"
        assert ByteSwapped(Bytes(5)).build(b"12345") == b"54321"
        assert ByteSwapped(Bytes(5)).sizeof() == 5
        assert ByteSwapped(Struct("a"/Byte, "b"/Byte)).parse(b"\x01\x02") == Container(a=2)(b=1)
        assert ByteSwapped(Struct("a"/Byte, "b"/Byte)).build(Container(a=2)(b=1)) == b"\x01\x02"

    def test_byteswapped_from_issue_70(self):
        assert ByteSwapped(BitStruct("flag1"/Bit, "flag2"/Bit, Padding(2), "number"/BitsInteger(16), Padding(4))).parse(b'\xd0\xbc\xfa') == Container(flag1=1)(flag2=1)(number=0xabcd)
        assert BitStruct("flag1"/Bit, "flag2"/Bit, Padding(2), "number"/BitsInteger(16), Padding(4)).parse(b'\xfa\xbc\xd1') == Container(flag1=1)(flag2=1)(number=0xabcd)

    def test_bitsswapped(self):
        assert BitsSwapped(Bytes(2)).parse(b"\x0f\x01") == b"\xf0\x80"
        assert BitsSwapped(Bytes(2)).build(b"\xf0\x80") == b"\x0f\x01"
        assert Bitwise(Bytes(8)).parse(b"\xf2") == b'\x01\x01\x01\x01\x00\x00\x01\x00'
        assert BitsSwapped(Bitwise(Bytes(8))).parse(b"\xf2") == b'\x00\x01\x00\x00\x01\x01\x01\x01'
        assert BitStruct("a"/Nibble, "b"/Nibble).parse(b"\xf1") == Container(a=15)(b=1)
        assert BitsSwapped(BitStruct("a"/Nibble, "b"/Nibble)).parse(b"\xf1") == Container(a=8)(b=15)

    def test_bitsswapped_from_issue_145(self):
        def LBitStruct(*subcons):
            return BitsSwapped(BitStruct(*subcons))
        assert LBitStruct("num"/Octet).parse(b"\x01") == Container(num=0x80)

    def test_slicing(self):
        assert Slicing(Array(4,Byte), 4, 1, 3, empty=0).parse(b"\x01\x02\x03\x04") == [2,3]
        assert Slicing(Array(4,Byte), 4, 1, 3, empty=0).build([2,3]) == b"\x00\x02\x03\x00"
        assert Slicing(Array(4,Byte), 4, 1, 3, empty=0).sizeof() == 4

    def test_indexing(self):
        assert Indexing(Array(4,Byte), 4, 2, empty=0).parse(b"\x01\x02\x03\x04") == 3
        assert Indexing(Array(4,Byte), 4, 2, empty=0).build(3) == b"\x00\x00\x03\x00"
        assert Indexing(Array(4,Byte), 4, 2, empty=0).sizeof() == 4

    def test_focusedseq(self):
        assert FocusedSeq(1, Const(b"MZ"), "num"/Byte, Terminated).parse(b"MZ\xff") == 255
        assert FocusedSeq(1, Const(b"MZ"), "num"/Byte, Terminated).build(255) == b"MZ\xff"
        assert FocusedSeq(1, Const(b"MZ"), "num"/Byte, Terminated).sizeof() == 1
        assert FocusedSeq("num", Const(b"MZ"), "num"/Byte, Terminated).parse(b"MZ\xff") == 255
        assert FocusedSeq("num", Const(b"MZ"), "num"/Byte, Terminated).build(255) == b"MZ\xff"
        assert FocusedSeq("num", Const(b"MZ"), "num"/Byte, Terminated).sizeof() == 1
        assert FocusedSeq(this.s, Const(b"MZ"), "num"/Byte, Terminated).parse(b"MZ\xff", s=1) == 255
        assert FocusedSeq(this.s, Const(b"MZ"), "num"/Byte, Terminated).sizeof(s=1) == 1
        assert FocusedSeq(this.s, Const(b"MZ"), "num"/Byte, Terminated).parse(b"MZ\xff", s="num") == 255
        assert FocusedSeq(this.s, Const(b"MZ"), "num"/Byte, Terminated).sizeof(s="num") == 1

        assert raises(FocusedSeq(123, Pass).parse, b"") == IndexError
        assert raises(FocusedSeq("missing", Pass).parse, b"") == IndexError
        assert raises(FocusedSeq(this.missing, Pass).parse, b"") == KeyError
        assert raises(FocusedSeq(123, Pass).build, {}) == IndexError
        assert raises(FocusedSeq("missing", Pass).build, {}) == IndexError
        assert raises(FocusedSeq(this.missing, Pass).build, {}) == KeyError
        assert raises(FocusedSeq(123, Pass).sizeof) == IndexError
        assert raises(FocusedSeq("missing", Pass).sizeof) == IndexError
        assert raises(FocusedSeq(this.missing, Pass).sizeof) == SizeofError

    def test_select(self):
        assert raises(Select(Int32ub, Int16ub).parse, b"\x07") == SelectError
        assert Select(Int32ub, Int16ub, Int8ub).parse(b"\x07") == 7
        assert Select(Int32ub, Int16ub, Int8ub).build(7) == b"\x00\x00\x00\x07"
        assert Select("a"/Int32ub, "b"/Int16ub, "c"/Int8ub, includename=True).parse(b"\x07") == ("c", 7)
        assert Select("a"/Int32ub, "b"/Int16ub, "c"/Int8ub, includename=True).build((("c", 7))) == b"\x07"
        assert raises(Select("a"/Int32ub, "b"/Int16ub, "c"/Int8ub, includename=True).build, (("d", 7))) == SelectError
        assert raises(Select(Byte).sizeof) == SizeofError

    @pytest.mark.xfail(not supportskwordered, reason="ordered kw was introduced in 3.6 and pypy")
    def test_select_kwctor(self):
        st = Select(a=Int8ub, b=Int16ub, c=Int32ub)
        assert st.parse(b"\x01\x02\x03\x04") == 0x01
        assert st.build(0x01020304) == b"\x01\x02\x03\x04"

    def test_peek(self):
        assert Peek(Int8ub).parse(b"\x01") == 1
        assert Peek(Int8ub).parse(b"") == None
        assert Peek(Int8ub).build(1) == b""
        assert Peek(Int8ub).build(None) == b""
        assert Peek(Int8ub).sizeof() == 0
        assert Peek(VarInt).sizeof() == 0
        assert Struct(Peek("a"/Int8ub), "b"/Int16ub).parse(b"\x01\x02") == Container(a=1)(b=0x0102)
        assert Struct(Peek("a"/Int8ub), "b"/Int16ub).build(dict(a=1,b=0x0102)) == b"\x01\x02"
        assert Struct(Peek("a"/Byte), Peek("b"/Int16ub)).parse(b"\x01\x02") == Container(a=1)(b=0x0102)
        assert Struct(Peek("a"/Byte), Peek("b"/Int16ub)).build(dict(a=0,b=0x0102)) == b""
        assert Struct(Peek("a"/Byte), Peek("b"/Int16ub)).sizeof() == 0

    def test_optional(self):
        assert Optional(Int32ul).parse(b"\x01\x00\x00\x00") == 1
        assert Optional(Int32ul).build(1) == b"\x01\x00\x00\x00"
        assert Optional(Int32ul).parse(b"???") == None
        assert Optional(Int32ul).build(None) == b""
        assert raises(Optional(Int32ul).sizeof) == SizeofError

    def test_union(self):
        assert Union("a"/Bytes(2), "b"/Int16ub).parse(b"\x01\x02") == Container(a=b"\x01\x02")(b=0x0102)
        assert Union("a"/Bytes(2), "b"/Int16ub).build(dict(a=b"zz"))  == b"zz"
        assert Union("a"/Bytes(2), "b"/Int16ub).build(dict(b=0x0102)) == b"\x01\x02"
        assert raises(Union("a"/Bytes(2), "b"/Int16ub).build, dict()) == UnionError
        assert Union("a"/Bytes(2), "b"/Int16ub, buildfrom=0).build(dict(a=b"zz",b=5))  == b"zz"
        assert Union("a"/Bytes(2), "b"/Int16ub, buildfrom=1).build(dict(a=b"zz",b=5))  == b"\x00\x05"
        assert Union("a"/Bytes(2), "b"/Int16ub, buildfrom="a").build(dict(a=b"zz",b=5))  == b"zz"
        assert Union("a"/Bytes(2), "b"/Int16ub, buildfrom="b").build(dict(a=b"zz",b=5))  == b"\x00\x05"
        assert Union("a"/Bytes(2), "b"/Int16ub, buildfrom=Pass).build({}) == b""
        assert raises(Union(Pass, buildfrom=123).parse, b"") == IndexError
        assert raises(Union(Pass, buildfrom="missing").build, {}) == IndexError

        assert raises(Union(Byte).sizeof) == SizeofError
        assert raises(Union(VarInt).sizeof) == SizeofError
        assert Union(Byte, VarInt, buildfrom=0).sizeof() == 1
        assert raises(Union(Byte, VarInt, buildfrom=1).sizeof) == SizeofError
        assert raises(Union(Pass, buildfrom=123).sizeof) == IndexError
        assert raises(Union(Pass, buildfrom="missing").sizeof) == IndexError
        assert raises(Union(Pass, buildfrom=this.missing).sizeof) == SizeofError

        assert (Union("b"/Int16ub) >> Byte).parse(b"\x01\x02\x03") == [Container(b=0x0102),0x01]
        assert (Union("b"/Int16ub, buildfrom=0) >> Byte).parse(b"\x01\x02\x03") == [Container(b=0x0102),0x03]
        assert (Union("b"/Int16ub, buildfrom="b") >> Byte).parse(b"\x01\x02\x03") == [Container(b=0x0102),0x03]

        assert (Union("a"/Int16ub, Embedded(Struct("b"/Int8ub, "c"/Int8ub))) >> Byte).parse(b"\x01\x02\x03") == [Container(a=0x0102, b=0x01, c=0x02), 0x01]
        assert (Union("a"/Int16ub, Embedded(Struct("b"/Int8ub, "c"/Int8ub)), buildfrom=0) >> Byte).parse(b"\x01\x02\x03") == [Container(a=0x0102, b=0x01, c=0x02), 0x03]
        assert (Union("a"/Int16ub, Embedded(Struct("b"/Int8ub, "c"/Int8ub)), buildfrom="a") >> Byte).parse(b"\x01\x02\x03") == [Container(a=0x0102, b=0x01, c=0x02), 0x03]
        assert Union("a"/Int16ub, Embedded(Struct("b"/Int8ub, "c"/Int8ub)), buildfrom="a").build(dict(a=0x0102)) == b"\x01\x02"
        assert Union("a"/Int16ub, Embedded(Struct("b"/Int8ub, "c"/Int8ub)), buildfrom=0).build(dict(a=0x0102)) == b"\x01\x02"
        assert Union("a"/Int16ub, Embedded(Struct("b"/Int8ub, "c"/Int8ub)), buildfrom=1).build(dict(b=0x01, c=0x02)) == b"\x01\x02"
        assert raises(Union("a"/Int16ub, Embedded(Struct("b"/Int8ub, "c"/Int8ub)), buildfrom=1).build, dict(b=0x01)) == KeyError
        assert raises(Union("a"/Int16ub, Embedded(Struct("b"/Int8ub, "c"/Int8ub)), buildfrom=1).build, dict()) == KeyError

    @pytest.mark.xfail(not supportskwordered, reason="ordered kw was introduced in 3.6 and pypy")
    def test_union_kwctor(self):
        st = Union(a=Int8ub, b=Int16ub, c=Int32ub)
        assert st.parse(b"\x01\x02\x03\x04") == Container(a=0x01,b=0x0102,c=0x01020304)
        assert st.build(Container(c=0x01020304)) == b"\x01\x02\x03\x04"

    def test_prefixed(self):
        assert Prefixed(Byte, Int16ul).parse(b"\x02\xff\xffgarbage") == 65535
        assert Prefixed(Byte, Int16ul).build(65535) == b"\x02\xff\xff"
        assert Prefixed(Byte, Int16ul).sizeof() == 3
        assert Prefixed(VarInt, GreedyBytes).parse(b"\x03abcgarbage") == b"abc"
        assert Prefixed(VarInt, GreedyBytes).build(b"abc") == b'\x03abc'
        assert Prefixed(Byte, Int64ub).sizeof() == 9
        assert Prefixed(Byte, Sequence(Peek(Byte), Int16ub, GreedyBytes)).parse(b"\x02\x00\xffgarbage") == [0,255,b'']
        assert raises(Prefixed(VarInt, GreedyBytes).sizeof) == SizeofError

    def test_compressed_zlib(self):
        zeros = bytes(10000)
        d = Compressed(GreedyBytes, "zlib")
        assert d.parse(d.build(zeros)) == zeros
        assert len(d.build(zeros)) < 50
        assert raises(d.sizeof) == SizeofError
        d = Compressed(GreedyBytes, "zlib", level=9)
        assert d.parse(d.build(zeros)) == zeros
        assert len(d.build(zeros)) < 50
        assert raises(d.sizeof) == SizeofError

    @pytest.mark.xfail(PY < (3,2), reason="gzip was added in 3.2")
    def test_compressed_gzip(self):
        zeros = bytes(10000)
        d = Compressed(GreedyBytes, "gzip")
        assert d.parse(d.build(zeros)) == zeros
        assert len(d.build(zeros)) < 50
        assert raises(d.sizeof) == SizeofError
        d = Compressed(GreedyBytes, "gzip", level=9)
        assert d.parse(d.build(zeros)) == zeros
        assert len(d.build(zeros)) < 50
        assert raises(d.sizeof) == SizeofError

    def test_compressed_bzip2(self):
        zeros = bytes(10000)
        d = Compressed(GreedyBytes, "bzip2")
        assert d.parse(d.build(zeros)) == zeros
        assert len(d.build(zeros)) < 50
        assert raises(d.sizeof) == SizeofError
        d = Compressed(GreedyBytes, "bzip2", level=9)
        assert d.parse(d.build(zeros)) == zeros
        assert len(d.build(zeros)) < 50
        assert raises(d.sizeof) == SizeofError

    @pytest.mark.xfail(PY < (3,3), reason="lzma module was added in 3.3")
    def test_compressed_lzma(self):
        zeros = bytes(10000)
        d = Compressed(GreedyBytes, "lzma")
        assert d.parse(d.build(zeros)) == zeros
        assert len(d.build(zeros)) < 200
        assert raises(d.sizeof) == SizeofError
        d = Compressed(GreedyBytes, "lzma", level=9)
        assert d.parse(d.build(zeros)) == zeros
        assert len(d.build(zeros)) < 200
        assert raises(d.sizeof) == SizeofError

    def test_compressed_prefixed(self):
        zeros = bytes(10000)
        d = Prefixed(VarInt, Compressed(GreedyBytes, "zlib"))
        st = Struct("one"/d, "two"/d)
        assert st.parse(st.build(Container(one=zeros,two=zeros))) == Container(one=zeros,two=zeros)
        assert raises(d.sizeof) == SizeofError

    def test_string(self):
        assert String(5).parse(b"hello") == b"hello"
        assert String(5).build(b"hello") == b"hello"
        assert raises(String(5).parse, b"") == FieldError
        assert String(5).build(b"") == b"\x00\x00\x00\x00\x00"
        assert String(12, encoding="utf8").parse(b"hello joh\xd4\x83n") == u"hello joh\u0503n"
        assert String(12, encoding="utf8").build(u"hello joh\u0503n") == b"hello joh\xd4\x83n"
        assert String(12, encoding="utf8").sizeof() == 12
        assert raises(String(5).build, u"hello") == StringError    # missing encoding
        assert String(10, padchar=b"X", paddir="right").parse(b"helloXXXXX") == b"hello"
        assert String(10, padchar=b"X", paddir="left").parse(b"XXXXXhello") == b"hello"
        assert String(10, padchar=b"X", paddir="center").parse(b"XXhelloXXX") == b"hello"
        assert String(10, padchar=b"X", paddir="right").build(b"hello") == b"helloXXXXX"
        assert String(10, padchar=b"X", paddir="left").build(b"hello") == b"XXXXXhello"
        assert String(10, padchar=b"X", paddir="center").build(b"hello") == b"XXhelloXXX"
        assert raises(String, 10, padchar=u"X", encoding="utf8") == StringError     # missing encoding
        assert String(5, trimdir="right").build(b"1234567890") == b"12345"
        assert String(5, trimdir="left").build(b"1234567890") == b"67890"
        assert String(5, padchar=b"X", paddir="left", encoding="utf8").sizeof() == 5
        assert String(5).sizeof() == 5

    def test_pascalstring(self):
        assert PascalString(Byte).parse(b"\x05hello????????") == b"hello"
        assert PascalString(Byte).build(b"hello") == b"\x05hello"
        assert PascalString(Byte, encoding="utf8").parse(b"\x05hello") == u"hello"
        assert PascalString(Byte, encoding="utf8").build(u"hello") == b"\x05hello"
        assert PascalString(Int16ub).parse(b"\x00\x05hello????????") == b"hello"
        assert PascalString(Int16ub).build(b"hello") == b"\x00\x05hello"
        assert raises(PascalString(Byte).sizeof) == SizeofError
        assert raises(PascalString(VarInt).sizeof) == SizeofError

    def test_cstring(self):
        assert CString().parse(b"hello\x00") == b"hello"
        assert CString().build(b"hello") == b"hello\x00"
        assert CString(encoding="utf8").parse(b"hello\x00") == u"hello"
        assert CString(encoding="utf8").build(u"hello") == b"hello\x00"
        assert CString(terminators=b"XYZ", encoding="utf8").parse(b"helloX") == u"hello"
        assert CString(terminators=b"XYZ", encoding="utf8").parse(b"helloY") == u"hello"
        assert CString(terminators=b"XYZ", encoding="utf8").parse(b"helloZ") == u"hello"
        assert CString(terminators=b"XYZ", encoding="utf8").build(u"hello") == b"helloX"
        assert CString(encoding="utf16").build(u"hello") == b"\xff\xfeh\x00"
        assert raises(CString(encoding="utf16").parse, b'\xff\xfeh\x00') == UnicodeDecodeError
        assert raises(CString().sizeof) == SizeofError

    def test_greedystring(self):
        assert GreedyString().parse(b"hello\x00") == b"hello\x00"
        assert GreedyString().build(b"hello\x00") == b"hello\x00"
        assert GreedyString().parse(b"") == b""
        assert GreedyString().build(b"") == b""
        assert GreedyString(encoding="utf8").parse(b"hello\x00") == u"hello\x00"
        assert GreedyString(encoding="utf8").parse(b"") == u""
        assert GreedyString(encoding="utf8").build(u"hello\x00") == b"hello\x00"
        assert GreedyString(encoding="utf8").build(u"") == b""
        assert raises(GreedyString().sizeof) == SizeofError

    def test_globally_encoded_strings(self):
        setglobalstringencoding("utf8")
        assert String(20).build(u"Афон") == String(20, encoding="utf8").build(u"Афон")
        assert PascalString(VarInt).build(u"Афон") == PascalString(VarInt, encoding="utf8").build(u"Афон")
        assert CString().build(u"Афон") == CString(encoding="utf8").build(u"Афон")
        assert GreedyString().build(u"Афон") == GreedyString(encoding="utf8").build(u"Афон")
        setglobalstringencoding(None)

    def test_lazybound(self):
        common(LazyBound(lambda ctx: Byte), b"\x01", 1, 1)

        st = Struct(
            "value"/Byte,
            "next"/If(this.value > 0, LazyBound(lambda ctx: st)),
        )
        common(st, b"\x05\x09\x00", Container(value=5)(next=Container(value=9)(next=Container(value=0)(next=None))), SizeofError)

    def test_unknown(self):
        assert Struct("length" / Byte, "inner" / Struct("inner_length" / Byte, "data" / Bytes(lambda ctx: ctx._.length + ctx.inner_length))).parse(b"\x03\x02helloXXX") == Container(length=3)(inner=Container(inner_length=2)(data=b"hello"))
        assert Struct("length" / Byte, "inner" / Struct("inner_length" / Byte, "data" / Bytes(lambda ctx: ctx._.length + ctx.inner_length))).sizeof(Container(inner_length=2)(_=Container(length=3))) == 7

    def test_noneof(self):
        assert NoneOf(Byte,[4,5,6,7]).parse(b"\x08") == 8
        assert raises(NoneOf(Byte,[4,5,6,7]).parse, b"\x06") == ValidationError

    def test_oneof(self):
        assert OneOf(Byte,[4,5,6,7]).parse(b"\x05") == 5
        assert OneOf(Byte,[4,5,6,7]).build(5) == b"\x05"
        assert raises(OneOf(Byte,[4,5,6,7]).parse, b"\x08") == ValidationError
        assert raises(OneOf(Byte,[4,5,6,7]).build, 8) == ValidationError

    def test_filter(self):
        assert Filter(obj_ != 0, Byte[:]).parse(b"\x00\x02\x00") == [2]
        assert Filter(obj_ != 0, Byte[:]).build([0,1,0,2,0]) == b"\x01\x02"

    def test_check(self):
        assert Check(this.x == 255).parse(b"", Container(x=255)) == None
        assert Check(this.x == 255).build(None, Container(x=255)) == b""
        assert Check(this.x == 255).sizeof() == 0

        assert Check(len_(this.a) == 3).parse(b"", Container(a=[1,2,3])) == None
        assert Check(len_(this.a) == 3).build(None, Container(a=[1,2,3])) == b""

    def test_hex(self):
        assert Hex(GreedyBytes).parse(b"abcd") == b"61626364"
        assert Hex(GreedyBytes).build(b"61626364") == b"abcd"
        assert Hex(GreedyBytes).parse(b"") == b""
        assert Hex(GreedyBytes).build(b"") == b""

    def test_hex_regression_188(self):
        d = Struct(Hex(Const(b"MZ")))
        assert d.parse(b"MZ") == Container()
        assert d.build(dict()) == b"MZ"

    def test_hexdump(self):
        assert HexDump(GreedyBytes).parse(b'abcdef') == '0000   61 62 63 64 65 66                                 abcdef\n'
        assert HexDump(GreedyBytes).build('0000   61 62 63 64 65 66                                 abcdef\n') == b'abcdef'
        assert HexDump(GreedyBytes).parse(b"") == ""
        assert HexDump(GreedyBytes).build("") == b""

    def test_hexdump_regression_188(self):
        d = Struct(HexDump(Const(b"MZ")))
        assert d.parse(b"MZ") == Container()
        assert d.build(dict()) == b"MZ"

    def test_lazystruct(self):
        assert LazyStruct().parse(b"") == Struct().parse(b"")
        assert LazyStruct().build({}) == Struct().build({})
        assert LazyStruct().sizeof() == Struct().sizeof()
        assert LazyStruct("a"/Byte, "b"/CString()).build(dict(a=1,b=b"abc")) == b"\x01abc\x00"
        assert raises(LazyStruct("a"/Byte, "b"/CString()).sizeof) == SizeofError
        assert LazyStruct("a"/Byte).build(dict(a=1)) == b"\x01"
        assert LazyStruct("a"/Byte).sizeof() == 1
        assert LazyStruct(Pass, Computed(lambda ctx: 0), Terminated).build(dict()) == b""
        assert LazyStruct(Pass, Computed(lambda ctx: 0), Terminated).sizeof() == 0
        assert LazyStruct("a"/Byte, "b"/LazyStruct("c"/Byte)).build(dict(a=1,b=dict(c=2))) == b"\x01\x02"
        assert LazyStruct().parse(b"") == dict()
        assert LazyStruct().build(dict()) == b""

        assert dict(LazyStruct("a"/Byte).parse(b"\x01")) == dict(a=1)
        assert LazyStruct("a"/Byte).build(dict(a=1)) == b"\x01"
        assert dict(LazyStruct("a"/Byte,"b"/CString()).parse(b"\x01abc\x00")) == dict(a=1,b=b"abc")
        assert LazyStruct("a"/Byte,"b"/CString()).build(dict(a=1,b=b"abc")) == b"\x01abc\x00"
        assert dict(LazyStruct(Pass, Computed(lambda ctx: 0), Terminated).parse(b"")) == dict()
        assert LazyStruct(Pass, Computed(lambda ctx: 0), Terminated).build(dict()) == b""

    def test_lazystruct_nested_embedded(self):
        assert dict(LazyStruct("a"/Byte,"b"/LazyStruct("c"/Byte)).parse(b"\x01\x02")) == dict(a=1,b=dict(c=2))
        assert LazyStruct("a"/Byte,"b"/LazyStruct("c"/Byte)).build(dict(a=1,b=dict(c=2))) == b"\x01\x02"
        assert dict(LazyStruct("a"/Byte,Embedded(LazyStruct("c"/Byte))).parse(b"\x01\x02")) == dict(a=1,c=2)
        assert LazyStruct("a"/Byte,Embedded(LazyStruct("c"/Byte))).build(dict(a=1,c=2)) == b"\x01\x02"

    def test_lazyrange(self):
        assert LazyRange(3,5,Byte).parse(b"\x01\x02\x03") == [1,2,3]
        assert LazyRange(3,5,Byte).parse(b"\x01\x02\x03\x04") == [1,2,3,4]
        assert LazyRange(3,5,Byte).parse(b"\x01\x02\x03\x04\x05") == [1,2,3,4,5]
        assert LazyRange(3,5,Byte).parse(b"\x01\x02\x03\x04\x05\x06") == [1,2,3,4,5]
        assert raises(LazyRange(3,5,Byte).parse, b"") == RangeError
        assert LazyRange(3,5,Byte).build([1,2,3]) == b"\x01\x02\x03"
        assert LazyRange(3,5,Byte).build([1,2,3,4]) == b"\x01\x02\x03\x04"
        assert LazyRange(3,5,Byte).build([1,2,3,4,5]) == b"\x01\x02\x03\x04\x05"
        assert raises(LazyRange(3,5,Byte).build, [1,2]) == RangeError
        assert raises(LazyRange(3,5,Byte).build, [1,2,3,4,5,6]) == RangeError
        assert raises(LazyRange(3,5,Byte).build, 0) == RangeError
        assert raises(LazyRange(3,5,Byte).sizeof) == SizeofError
        assert LazyRange(0,100,Struct("id"/Byte)).parse(b'\x01\x02') == [Container(id=1),Container(id=2)]
        assert LazyRange(0,100,Struct("id"/Byte)).build([dict(id=i) for i in range(5)]) == b'\x00\x01\x02\x03\x04'
        assert raises(LazyRange(0,100,Struct("id"/Byte)).build, dict(id=1)) == RangeError
        assert raises(LazyRange(0,100,Struct("id"/Byte)).sizeof) == SizeofError
        assert LazyRange(1,1,Byte).sizeof() == 1

        assert raises(LazyRange(-2, +7, Byte).parse, b"") == RangeError
        assert raises(LazyRange(-2, +7, Byte).build, {}) == RangeError
        assert raises(LazyRange(-2, +7, Byte).sizeof) == RangeError
        assert raises(LazyRange, 1, 1, VarInt) == SizeofError

        assert LazyRange(1,9,Byte).parse(b"12345") == Range(1,9,Byte).parse(b"12345")
        assert LazyRange(1,9,Byte).build([1,2,3]) == Range(1,9,Byte).build([1,2,3])

    def test_lazysequence(self):
        assert LazySequence(Int8ub, Int16ub).parse(b"\x01\x00\x02") == [1,2]
        assert LazySequence(Int8ub, Int16ub).build([1,2]) == b"\x01\x00\x02"
        assert LazySequence().parse(b"") == []
        assert LazySequence().build([]) == b""
        assert LazySequence().sizeof() == 0

        assert LazySequence(Int8ub,Int16ub).parse(b"\x01\x00\x02") == Sequence(Int8ub,Int16ub).parse(b"\x01\x00\x02")
        assert LazySequence(Int8ub,Int16ub).build([1,2]) == Sequence(Int8ub,Int16ub).build([1,2])
        assert LazySequence(Int8ub,Int16ub).sizeof() == Sequence(Int8ub,Int16ub).sizeof()

    def test_lazysequence_nested_embedded(self):
        assert LazySequence(Int8ub, Int16ub, LazySequence(Int8ub, Int8ub)).parse(b"\x01\x00\x02\x03\x04") == [1,2,[3,4]]
        assert LazySequence(Int8ub, Int16ub, LazySequence(Int8ub, Int8ub)).build([1,2,[3,4]]) == b"\x01\x00\x02\x03\x04"
        assert LazySequence(Int8ub, Int16ub, Embedded(LazySequence(Int8ub, Int8ub))).parse(b"\x01\x00\x02\x03\x04") == [1,2,3,4]
        assert LazySequence(Int8ub, Int16ub, Embedded(LazySequence(Int8ub, Int8ub))).build([1,2,3,4]) == b"\x01\x00\x02\x03\x04"

    def test_ondemand(self):
        assert OnDemand(Byte).parse(b"\x01garbage")() == 1
        assert OnDemand(Byte).build(1) == b"\x01"
        assert OnDemand(Byte).sizeof() == 1

        parseret = OnDemand(Byte).parse(b"\x01garbage")
        assert OnDemand(Byte).build(parseret) == b"\x01"

    def test_ondemandpointer(self):
        assert OnDemandPointer(lambda ctx: 2, Byte).parse(b"\x01\x02\x03garbage")() == 3
        assert OnDemandPointer(lambda ctx: 2, Byte).build(1) == b"\x00\x00\x01"
        assert OnDemandPointer(lambda ctx: 2, Byte).sizeof() == 0

    def test_from_issue_76(self):
        assert Aligned(4, Struct("a"/Byte, "f"/Bytes(lambda ctx: ctx.a))).parse(b"\x02\xab\xcd\x00") == Container(a=2)(f=b"\xab\xcd")
        assert Aligned(4, Struct("a"/Byte, "f"/Bytes(lambda ctx: ctx.a))).build(Container(a=2)(f=b"\xab\xcd")) == b"\x02\xab\xcd\x00"

    def test_flag(self):
        assert Flag.parse(b"\x00") == False
        assert Flag.parse(b"\x01") == True
        assert Flag.parse(b"\xff") == True
        assert Flag.build(False) == b"\x00"
        assert Flag.build(True) == b"\x01"
        assert Flag.sizeof() == 1

    def test_enum(self):
        assert Enum(Byte, q=3,r=4,t=5).parse(b"\x04") == "r"
        assert Enum(Byte, q=3,r=4,t=5).build("r") == b"\x04"
        assert Enum(Byte, q=3,r=4,t=5).build(4) == b"\x04"
        assert raises(Enum(Byte, q=3,r=4,t=5).parse, b"\x07") == MappingError
        assert raises(Enum(Byte, q=3,r=4,t=5).build, "spam") == MappingError
        assert Enum(Byte, q=3,r=4,t=5, default="spam").parse(b"\x07") == "spam"
        assert Enum(Byte, q=3,r=4,t=5, default=9).build("spam") == b"\x09"
        assert Enum(Byte, q=3,r=4,t=5, default=Pass).parse(b"\x07") == 7
        assert Enum(Byte, q=3,r=4,t=5, default=Pass).build(9) == b"\x09"
        assert Enum(Byte, q=3,r=4,t=5).sizeof() == 1

    def test_flagsenum(self):
        assert FlagsEnum(Byte, a=1,b=2,c=4,d=8,e=16,f=32,g=64,h=128).parse(b'\x81') == FlagsContainer(a=True,b=False,c=False,d=False,e=False,f=False,g=False,h=True)
        assert FlagsEnum(Byte, a=1,b=2,c=4,d=8,e=16,f=32,g=64,h=128).build(FlagsContainer(a=True,b=False,c=False,d=False,e=False,f=False,g=False,h=True)) == b'\x81'
        assert FlagsEnum(Byte, feature=4,output=2,input=1).parse(b'\x04') == FlagsContainer(output=False,feature=True,input=False)
        assert FlagsEnum(Byte, feature=4,output=2,input=1).build(dict(feature=True, output=True, input=False)) == b'\x06'
        assert FlagsEnum(Byte, feature=4,output=2,input=1).build(dict(feature=True)) == b'\x04'
        assert FlagsEnum(Byte, feature=4,output=2,input=1).build(dict()) == b'\x00'
        assert raises(FlagsEnum(Byte, feature=4,output=2,input=1).build, dict(unknown=True)) == MappingError

    @pytest.mark.xfail(PYPY, raises=ImportError, reason="numpy not on Travis pypy")
    def test_numpy(self):
        import numpy
        obj = numpy.array([1,2,3], dtype=numpy.int64)
        assert numpy.array_equal(Numpy.parse(Numpy.build(obj)), obj)

    def test_namedtuple(self):
        coord = collections.namedtuple("coord", "x y z")
        Coord = NamedTuple("coord", "x y z", Byte[3])
        assert Coord.parse(b"123") == coord(49,50,51)
        assert Coord.build(coord(49,50,51)) == b"123"
        assert Coord.sizeof() == 3

        Coord = NamedTuple("coord", "x y z", Byte >> Byte >> Byte)
        assert Coord.parse(b"123") == coord(49,50,51)
        assert Coord.build(coord(49,50,51)) == b"123"
        assert Coord.sizeof() == 3

        Coord = NamedTuple("coord", "x y z", Struct("x"/Byte, "y"/Byte, "z"/Byte))
        assert Coord.parse(b"123") == coord(49,50,51)
        assert Coord.build(coord(49,50,51)) == b"123"
        assert Coord.sizeof() == 3

    def test_rebuild(self):
        d = Struct("count"/Rebuild(Byte, len_(this.items)), "items"/Byte[this.count])
        assert d.parse(b"\x02ab") == Container(count=2)(items=[97,98])
        assert d.build(dict(count=None,items=[255])) == b"\x01\xff"
        assert d.build(dict(items=[255])) == b"\x01\xff"

    def test_probe(self):
        Probe().parse(b"")
        Probe().build(None)
        Struct("inserted"/Probe()).parse(b"")
        Struct("inserted"/Probe()).build({})

    def test_probeinto(self):
        Struct("inner"/Struct("nums"/Byte[:]), ProbeInto(this.inner)).parse(b"\x01\xff")
        Struct("inner"/Struct("nums"/Byte[:]), ProbeInto(this.inner)).build(dict(inner=dict(nums=[1,255])))
        Struct(ProbeInto(this.inner)).parse(b"")
        Struct(ProbeInto(this.inner)).build({})

    def test_restreamed(self):
        assert Restreamed(Int16ub, ident, 1, ident, 1, ident).parse(b"\x00\x01") == 1
        assert Restreamed(Int16ub, ident, 1, ident, 1, ident).build(1) == b"\x00\x01"
        assert Restreamed(Int16ub, ident, 1, ident, 1, ident).sizeof() == 2
        assert raises(Restreamed(VarInt, ident, 1, ident, 1, ident).sizeof) == SizeofError
        assert Restreamed(Bytes(2), None, None, lambda b: b*2, 1, None).parse(b"a") == b"aa"
        assert Restreamed(Bytes(1), lambda b: b*2, 1, None, None, None).build(b"a") == b"aa"
        assert Restreamed(Bytes(5), None, None, None, None, lambda n: n*2).sizeof() == 10

    def test_rebuffered(self):
        data = b"0" * 1000
        assert Rebuffered(Array(1000,Byte)).parse_stream(BytesIO(data)) == [48]*1000
        assert Rebuffered(Array(1000,Byte), tailcutoff=50).parse_stream(BytesIO(data)) == [48]*1000
        assert Rebuffered(Byte).sizeof() == 1
        assert raises(Rebuffered(VarInt).sizeof) == SizeofError

    def test_expradapter(self):
        MulDiv = ExprAdapter(Byte, obj_ // 7, obj_ * 7)
        assert MulDiv.parse(b"\x06") == 42
        assert MulDiv.build(42) == b"\x06"
        assert MulDiv.sizeof() == 1

        Ident = ExprAdapter(Byte, obj_+1, obj_-1)
        assert Ident.parse(b"\x02") == 1
        assert Ident.build(1) == b"\x02"
        assert Ident.sizeof() == 1

        self.test_hex()
        self.test_hexdump()
        self.test_cstring()

    def test_exprsymmetricadapter(self):
        self.test_filter()

    def test_exprvalidator(self):
        One = ExprValidator(Byte, lambda obj,ctx: obj in [1,3,5])
        assert One.parse(b"\x01") == 1
        assert raises(One.parse, b"\xff") == ValidationError
        assert One.build(5) == b"\x05"
        assert raises(One.build, 255) == ValidationError
        assert One.sizeof() == 1

        self.test_oneof()
        self.test_noneof()

    def test_ipaddress_from_issue_95(self):
        class IpAddressAdapter(Adapter):
            def _encode(self, obj, context):
                return list(map(int, obj.split(".")))
            def _decode(self, obj, context):
                return "{0}.{1}.{2}.{3}".format(*obj)
        IpAddress = IpAddressAdapter(Byte[4])

        assert IpAddress.parse(b"\x7f\x80\x81\x82") == "127.128.129.130"
        assert IpAddress.build("127.1.2.3") == b"\x7f\x01\x02\x03"
        assert IpAddress.sizeof() == 4

        IpAddress = ExprAdapter(Byte[4], 
            encoder = lambda obj,ctx: list(map(int, obj.split("."))),
            decoder = lambda obj,ctx: "{0}.{1}.{2}.{3}".format(*obj), )

        assert IpAddress.parse(b"\x7f\x80\x81\x82") == "127.128.129.130"
        assert IpAddress.build("127.1.2.3") == b"\x7f\x01\x02\x03"
        assert IpAddress.sizeof() == 4

    def test_lazybound_node(self):
        print("need some ideas how to test it")
        Node = Struct(
            "value" / Int8ub,
            "next" / LazyBound(lambda ctx: Node), )

    def test_checksum(self):
        d = Struct(
            "fields" / RawCopy(Struct(
                "a" / Byte,
                "b" / Byte,
            )),
            "checksum" / Checksum(Bytes(64), lambda data: hashlib.sha512(data).digest(), this.fields.data),
        )

        c = hashlib.sha512(b"\x01\x02").digest()
        assert d.parse(b"\x01\x02"+c) == Container(fields=dict(data=b"\x01\x02", value=Container(a=1)(b=2), offset1=0, offset2=2, length=2))(checksum=c)
        assert d.build(dict(fields=dict(data=b"\x01\x02"))) == b"\x01\x02"+c
        assert d.build(dict(fields=dict(value=dict(a=1,b=2)))) == b"\x01\x02"+c

    def test_from_issue_60(self):
        Header = Struct(
            "type" / Int8ub,
            "size" / Switch(lambda ctx: ctx.type,
            {
                0: Int8ub,
                1: Int16ub,
                2: Int32ub,
            }),
            "length" / Tell,
        )
        assert Header.parse(b"\x00\x05")             == Container(type=0)(size=5)(length=2)
        assert Header.parse(b"\x01\x00\x05")         == Container(type=1)(size=5)(length=3)
        assert Header.parse(b"\x02\x00\x00\x00\x05") == Container(type=2)(size=5)(length=5)
        assert Header.build(dict(type=0, size=5)) == b"\x00\x05"
        assert Header.build(dict(type=1, size=5)) == b"\x01\x00\x05"
        assert Header.build(dict(type=2, size=5)) == b"\x02\x00\x00\x00\x05"

        HeaderData = Struct(
            Embedded(Header),
            "data" / Bytes(lambda ctx: ctx.size),
        )
        assert HeaderData.parse(b"\x00\x0512345")             == Container(type=0)(size=5)(length=2)(data=b"12345")
        assert HeaderData.parse(b"\x01\x00\x0512345")         == Container(type=1)(size=5)(length=3)(data=b"12345")
        assert HeaderData.parse(b"\x02\x00\x00\x00\x0512345") == Container(type=2)(size=5)(length=5)(data=b"12345")
        assert HeaderData.build(dict(type=0, size=5, data=b"12345")) == b"\x00\x0512345"
        assert HeaderData.build(dict(type=1, size=5, data=b"12345")) == b"\x01\x00\x0512345"
        assert HeaderData.build(dict(type=2, size=5, data=b"12345")) == b"\x02\x00\x00\x00\x0512345"

    def test_struct_proper_context(self):
        d1 = Struct(
            "x"/Byte,
            "inner"/Struct(
                "y"/Byte,
                "a"/Computed(this._.x+1),
                "b"/Computed(this.y+2),
            ),
            "c"/Computed(this.x+3),
            "d"/Computed(this.inner.y+4),
        )
        d2 = Struct(
            "x"/Byte,
            "inner"/Embedded(Struct(
                "y"/Byte,
                "a"/Computed(this._.x+1),  # important
                "b"/Computed(this.y+2),    # important
            )),
            "c"/Computed(this.x+3),
            "d"/Computed(this.y+4),
        )
        assert d1.parse(b"\x01\x0f") == Container(x=1)(inner=Container(y=15)(a=2)(b=17))(c=4)(d=19)
        # a-field computed on nested context, merged only after entire inner-struct returns
        assert d2.parse(b"\x01\x0f") == Container(x=1)(y=15)(a=2)(b=17)(c=4)(d=19)

    def test_from_issue_171(self):
        attributes = BitStruct(
            "attr" / Aligned(8, Array(3, Struct(
                "attrCode" / BitsInteger(16),
                "attrValue" / Switch(this.attrCode, {
                    34: BitsInteger(8),
                    205: BitsInteger(2),
                    512: BitsInteger(2)
                }),
            ))),
        )
        blob = b"\x00\x22\x82\x00\xCD\x80\x80\x10"
        assert attributes.parse(blob) == Container(attr=[
            Container(attrCode=34)(attrValue=130),
            Container(attrCode=205)(attrValue=2),
            Container(attrCode=512)(attrValue=1), ])

    def test_from_issue_175(self):
        @PathFunc
        def comp_(num_array):
            return sum(x << ((len(num_array)-1-i)*8) for i,x in enumerate(num_array))

        test = Struct(
            "numArray" / RepeatUntil(obj_ < 128, Byte),
            "value" / Computed(comp_(this.numArray))
        )
        assert test.parse(b'\x87\x0f').value == 34575

    def test_from_issue_71(self):
        Inner = Struct(
            'name' / PascalString(Byte),
            'occupation' / PascalString(Byte),
        )
        Outer = Struct(
            'struct_type' / Int16ub,
            'payload_len' / Int16ub,
            'payload' / RawCopy(Inner),
            'serial' / Int16ub,
            'checksum' / Checksum(Bytes(64), lambda data: hashlib.sha512(data).digest(), this.payload.data),
            Check(len_(this.payload.data) == this.payload_len),
            Terminated,
        )

        payload = Inner.build(dict(name=b"unknown", occupation=b"worker"))
        payload_len = len(payload)
        Outer.build(Container(payload=Container(data=payload), payload_len=payload_len, serial=12345, struct_type=9001))

    def test_from_issue_28(self):

        def vstring(name, embed=True, optional=True):
            lfield = "_%s_length" % name.lower()
            s = Struct(
                lfield / Byte,
                name / Bytes(lambda ctx: getattr(ctx, lfield)))
            if optional:
                s = Optional(s)
            if embed:
                s = Embedded(s)
            return s

        def build_struct(embed_g=True, embed_h=True):
            s = "mystruct" / Struct(
                "a" / Int32ul,
                "b" / Int8ul,
                "c" / Int8ul,
                "d" / BitStruct("dx" / Bit[8]),
                "e" / BitStruct("ex" / Bit[8]),
                "f" / Float32b,
                vstring("g", embed=embed_g),
                vstring("h", embed=embed_h),
                "i" / BitStruct("ix" / Bit[8]),
                "j" / Int8sb,
                "k" / Int8sb,
                "l" / Int8sb,
                "m" / Float32l,
                "n" / Float32l,
                vstring("o"),
                vstring("p"),
                vstring("q"),
                vstring("r"))
            return s

        data = b'\xc3\xc0{\x00\x01\x00\x00\x00HOqA\x12some silly text...\x00\x0e\x00\x00\x00q=jAq=zA\x02dB\x02%f\x02%f\x02%f'
        print("\n\nNo embedding for neither g and h, i is a container --> OK")
        print(build_struct(embed_g=False, embed_h=False).parse(data))
        print("Embed both g and h, i is not a container --> FAIL")
        print(build_struct(embed_g=True, embed_h=True).parse(data))
        print("\n\nEmbed g but not h --> EXCEPTION")
        print(build_struct(embed_g=True, embed_h=False).parse(data))
        # When setting optional to False in vstring method, all three tests above work fine.

    def test_from_issue_231(self):
        u = Union("raw"/Byte[8], "ints"/Int32ub[2], buildfrom="ints")
        s = Struct("u"/u, "d"/Byte[4])

        buildret = s.build(dict(u=dict(ints=[1,2]),d=[0,1,2,3]))
        assert buildret == b"\x00\x00\x00\x01\x00\x00\x00\x02\x00\x01\x02\x03"
        assert s.build(s.parse(buildret)) == buildret

    def test_default(self):
        common(Struct("a"/Default(Byte,0), "b"/Default(Byte,0)), b"\x01\x02", Container(a=1)(b=2), 2)
        assert Struct("a"/Default(Byte,0), "b"/Default(Byte,0)).build(dict(a=1)) == b"\x01\x00"

    def test_from_issue_246(self):
        NumVertices = Bitwise(Aligned(8, Struct(
            'numVx4' / BitsInteger(4),
            'numVx8' / If(this.numVx4 == 0, BitsInteger(8)),
            'numVx16' / If(this.numVx4 == 0 and this.numVx8 == 255, BitsInteger(16)),
        )))
        common(NumVertices, b'\x02\x30', Container(numVx4=0, numVx8=35, numVx16=None))

        testBit = BitStruct(
            'a' / BitsInteger(8),
            'b' / If(this.a == 97, BitsInteger(8))
        )
        testByte = Struct(
            'a' / Byte,
            'b' / If(this.a == 97, Byte)
        )
        common(testBit, b'ab', Container(a=97, b=98))
        common(testByte, b'ab', Container(a=97, b=98))

    @pytest.mark.xfail(raises=AssertionError, reason="makes no sense")
    def test_from_issue_246_third(self):
        NumVertices = Union(
            'numVx4' /  Bitwise(Aligned(8, Struct('num'/ BitsInteger(4)))),
            'numVx8' /  Bitwise(Aligned(8, Struct('num'/ BitsInteger(12)))),
            'numVx16' / Bitwise(Aligned(8, Struct('num'/ BitsInteger(28)))),
        )
        common(NumVertices, b'\x01\x34\x56\x70', Container(numVx4=Container(num=0))(numVx8=Container(num=19))(numVx16=Container(num=1262951)))

    def test_from_issue_244(self):
        class AddIndexes(Adapter):
            def __init__(self, subcon):
                super(AddIndexes, self).__init__(subcon)
            def _decode(self, obj, context):
                for i,con in enumerate(obj):
                    con.index = i
                return obj

        assert AddIndexes(Struct("num"/Byte)[4]).parse(b"abcd") == [Container(num=97)(index=0),Container(num=98)(index=1),Container(num=99)(index=2),Container(num=100)(index=3),]


