# -*- coding: utf-8 -*-

from declarativeunittest import *
from construct import *
from construct.lib import *


class TestCore(unittest.TestCase):

    def test_bytes(self):
        common(Bytes(4), b"1234", b"1234", 4)
        assert Bytes(4).parse(b"12345678") == b"1234"
        assert raises(Bytes(4).parse, b"") == StreamError
        assert raises(Bytes(4).build, b"toolong") == StreamError
        assert Bytes(4).build(1) == b"\x00\x00\x00\x01"
        assert Bytes(4).build(0x01020304) == b"\x01\x02\x03\x04"
        assert Bytes(4).sizeof() == 4

        assert Bytes(this.n).parse(b"12345678",n=4) == b"1234"
        assert Bytes(this.n).build(b"1234",n=4) == b"1234"
        assert Bytes(this.n).sizeof(n=4) == 4
        assert Bytes(this.n).build(1, n=4) == b"\x00\x00\x00\x01"
        assert raises(Bytes(this.n).build, b"", n=4) == StreamError
        assert raises(Bytes(this.n).build, b"toolong", n=4) == StreamError
        assert raises(Bytes(this.n).sizeof) == SizeofError

    def test_greedybytes(self):
        common(GreedyBytes, b"1234", b"1234", SizeofError)

    def test_bitwise(self):
        assert Bitwise(Bytes(8)).parse(b"\xff") == b"\x01\x01\x01\x01\x01\x01\x01\x01"
        assert Bitwise(Bytes(8)).build(b"\x01\x01\x01\x01\x01\x01\x01\x01") == b"\xff"
        assert Bitwise(Bytes(8)).sizeof() == 1
        assert Bitwise(Array(8,Bit)).parse(b"\xff") == [1,1,1,1,1,1,1,1]
        assert Bitwise(Array(8,Bit)).build([1,1,1,1,1,1,1,1]) == b"\xff"
        assert Bitwise(Array(2,Nibble)).parse(b"\xff") == [15,15]
        assert Bitwise(Array(2,Nibble)).build([15,15]) == b"\xff"
        assert Bitwise(Array(1,Octet)).parse(b"\xff") == [255]
        assert Bitwise(Array(1,Octet)).build([255]) == b"\xff"

    def test_bytewise(self):
        assert Bitwise(Bytewise(Bytes(1))).parse(b"\xff") == b"\xff"
        assert Bitwise(Bytewise(Bytes(1))).build(b"\xff") == b"\xff"
        assert Bitwise(Bytewise(Bytes(1))).sizeof() == 1
        assert BitStruct(Nibble, "num"/Bytewise(Int24ub), Nibble).parse(b"\xf0\x10\x20\x3f") == Container(num=0x010203)
        assert Bitwise(Sequence(Nibble, Bytewise(Int24ub), Nibble)).parse(b"\xf0\x10\x20\x3f") == [0x0f,0x010203,0x0f]

    def test_ints(self):
        common(Byte, b"\xff", 255, 1)
        common(Short, b"\x00\xff", 255, 2)
        common(Int, b"\x00\x00\x00\xff", 255, 4)
        common(Long, b"\x00\x00\x00\x00\x00\x00\x00\xff", 255, 8)
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
        common(Int24sb, b"\xff\xff\xff", -1, 3)
        common(Int24sl, b"\xff\xff\xff", -1, 3)

    def test_floats(self):
        assert Single.build(1.2) == b"?\x99\x99\x9a"
        assert Double.build(1.2) == b"?\xf3333333"

    def test_formatfield(self):
        common(FormatField("<","L"), b"\x12\x34\x56\x78", 0x78563412, 4)
        assert raises(FormatField("<","L").parse, b"") == StreamError
        assert raises(FormatField("<","L").parse, b"\x12\x34\x56") == StreamError
        assert raises(FormatField("<","L").build, "string not int") == FormatFieldError
        assert raises(FormatField("<","L").build, 2**100) == FormatFieldError
        assert raises(FormatField("<","L").build, 9e9999) == FormatFieldError

    def test_formatfield_ints_randomized(self):
        for endianess,dtype in itertools.product("<>=","bhlqBHLQ"):
            d = FormatField(endianess, dtype)
            for i in range(100):
                obj = random.randrange(0, 256**d.sizeof()//2)
                assert d.parse(d.build(obj)) == obj
                data = os.urandom(d.sizeof())
                assert d.build(d.parse(data)) == data

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

    def test_bytesinteger(self):
        common(BytesInteger(4), b"\x00\x00\x00\xff", 255, 4)
        common(BytesInteger(4, signed=True), b"\xff\xff\xff\xff", -1, 4)
        assert raises(BytesInteger(this.missing).sizeof) == SizeofError
        assert raises(BytesInteger(4, signed=False).build, -1) == IntegerError

    def test_bitsinteger(self):
        assert BitsInteger(8).parse(b"\x01\x01\x01\x01\x01\x01\x01\x01") == 255
        assert BitsInteger(8).build(255) == b"\x01\x01\x01\x01\x01\x01\x01\x01"
        assert BitsInteger(8).sizeof() == 8
        assert BitsInteger(8, signed=True).parse(b"\x01\x01\x01\x01\x01\x01\x01\x01") == -1
        assert BitsInteger(8, signed=True).build(-1) == b"\x01\x01\x01\x01\x01\x01\x01\x01"
        assert raises(BitsInteger(this.missing).sizeof) == SizeofError
        assert raises(BitsInteger(8, signed=False).build, -1) == IntegerError

    def test_varint(self):
        common(VarInt, b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x10", 2**123, SizeofError)
        for n in [0,1,5,100,255,256,65535,65536,2**32,2**100]:
            assert VarInt.parse(VarInt.build(n)) == n
            assert len(VarInt.build(n)) >= len("%x" % n)//2
        for n in range(0, 127):
            common(VarInt, int2byte(n), n, SizeofError)

        assert raises(VarInt.parse, b"") == StreamError
        assert raises(VarInt.build, -1) == IntegerError

    def test_string(self):
        common(String(10, encoding=StringsAsBytes), b"hello\x00\x00\x00\x00\x00", b"hello", 10)
        common(String(10, encoding="utf8"), b"hello\x00\x00\x00\x00\x00", u"hello", 10)

        s = u"Афон"
        for e,us in [("utf8",1),("utf16",2),("utf_16_le",2),("utf32",4),("utf_32_le",4)]:
            data = (s.encode(e)+b"\x00"*100)[:100]
            common(String(100, encoding=e), data, s, 100)

        for e in [StringsAsBytes,"ascii","utf8","utf16","utf_16_le","utf32","utf_32_le"]:
            String(10, encoding=e).sizeof() == 10
            String(this.n, encoding=e).sizeof(n=10) == 10

    def test_pascalstring(self):
        common(PascalString(Byte, encoding=StringsAsBytes), b"\x05hello", b"hello")
        common(PascalString(Byte, encoding="utf8"), b"\x05hello", u"hello")
        common(PascalString(Int16ub, encoding=StringsAsBytes), b"\x00\x05hello", b"hello")
        common(PascalString(Int16ub, encoding="utf8"), b"\x00\x05hello", u"hello")
        common(PascalString(VarInt, encoding=StringsAsBytes), b"\x05hello", b"hello")
        common(PascalString(VarInt, encoding="utf8"), b"\x05hello", u"hello")
        common(PascalString(Byte, encoding=StringsAsBytes), b"\x00", b"")
        common(PascalString(Byte, encoding="utf8"), b"\x00", u"")

        for e in [StringsAsBytes,"ascii","utf8","utf16","utf_16_le","utf32","utf_32_le"]:
            raises(PascalString(Byte, encoding=e).sizeof) == SizeofError
            raises(PascalString(VarInt, encoding=e).sizeof) == SizeofError

    def test_cstring(self):
        s = u"Афон"
        for e,us in [("utf8",1),("utf16",2),("utf_16_le",2),("utf32",4),("utf_32_le",4)]:
            common(CString(encoding=e), s.encode(e)+b"\x00"*us, s)

        common(CString(encoding=StringsAsBytes), b"aooh"+b"\x00", b"aooh")

        CString(encoding="utf8").build(s) == b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd'+b"\x00"
        CString(encoding="utf16").build(s) == b'\xff\xfe\x10\x04D\x04>\x04=\x04'+b"\x00\x00"
        CString(encoding="utf32").build(s) == b'\xff\xfe\x00\x00\x10\x04\x00\x00D\x04\x00\x00>\x04\x00\x00=\x04\x00\x00'+b"\x00\x00\x00\x00"

        for e in [StringsAsBytes,"ascii","utf8","utf16","utf_16_le","utf32","utf_32_le"]:
            raises(CString(encoding=e).sizeof) == SizeofError

    def test_greedystring(self):
        s = u"Афон"
        for e,us in [("utf8",1),("utf16",2),("utf_16_le",2),("utf32",4),("utf_32_le",4)]:
            common(GreedyString(encoding=e), s.encode(e), s)

        common(GreedyString(encoding=StringsAsBytes), b"hello", b"hello")
        common(GreedyString(encoding="utf8"), b"hello", u"hello")
        common(GreedyString(encoding=StringsAsBytes), b"", b"")
        common(GreedyString(encoding="utf8"), b"", u"")

        for e in [StringsAsBytes,"ascii","utf8","utf16","utf_16_le","utf32","utf_32_le"]:
            raises(GreedyString(encoding=e).sizeof) == SizeofError

    def test_string_global_encoding(self):
        setglobalstringencoding("utf8")
        assert String(20).build(u"Афон") == String(20, encoding="utf8").build(u"Афон")
        assert PascalString(VarInt).build(u"Афон") == PascalString(VarInt, encoding="utf8").build(u"Афон")
        assert CString().build(u"Афон") == CString(encoding="utf8").build(u"Афон")
        assert GreedyString().build(u"Афон") == GreedyString(encoding="utf8").build(u"Афон")
        setglobalstringencoding(None)

    def test_flag(self):
        common(Flag, b"\x00", False, 1)
        common(Flag, b"\x01", True, 1)

    def test_enum(self):
        common(Enum(Byte, a=1, b=2), b"\x01", "a", 1)
        common(Enum(Byte, a=1, b=2), b"\x02", "b", 1)
        assert raises(Enum(Byte, a=1, b=2).parse, b"\xff") == MappingError
        assert raises(Enum(Byte, a=1, b=2).build, "unknown") == MappingError
        Enum(Byte, a=1, b=2).build(1) == b"\x01"
        assert raises(Enum(Byte, a=1, b=2).build, 255) == MappingError

    @pytest.mark.xfail(PY < (3,4), raises=AttributeError, reason="IntEnum introduced in 3.4, IntFlag introduced in 3.6")
    def test_enum_enum34(self):
        import enum
        class E(enum.IntEnum):
            a = 1
        class F(enum.IntEnum):
            b = 2
        common(Enum(Byte, E, F), b"\x01", "a", 1)
        common(Enum(Byte, E, F), b"\x02", "b", 1)

    @pytest.mark.xfail(PY < (3,6), raises=AttributeError, reason="IntEnum introduced in 3.4, IntFlag introduced in 3.6")
    def test_enum_enum36(self):
        import enum
        class E(enum.IntEnum):
            a = 1
        class F(enum.IntFlag):
            b = 2
        common(Enum(Byte, E, F), b"\x01", "a", 1)
        common(Enum(Byte, E, F), b"\x02", "b", 1)

    @pytest.mark.xfail(reason="Enum no longer supports default")
    def test_enum_issue_298(self):
        # also tests Enum when default case value overlaps with another label's value
        st = Struct(
            "ctrl" / Enum(Byte,
                NAK = 0x15,
                STX = 0x02,
                default = 0x02,
            ),
            "optional" / If(this.ctrl == "NAK", Byte),
        )
        common(st, b"\x15\xff", Container(ctrl='NAK')(optional=255))
        common(st, b"\x02", Container(ctrl='STX')(optional=None))

        # FlagsEnum is not affected by same bug
        st = Struct(
            "flags" / FlagsEnum(Byte, a=1),
            Check(lambda ctx: ctx.flags == FlagsContainer(a=1)),
        )
        st.parse(b"\x01")
        st.build(dict(flags=FlagsContainer(a=1)))

        # Flag is not affected by same bug
        st = Struct(
            "flag" / Flag,
            Check(lambda ctx: ctx.flag == True),
        )
        st.parse(b"\x01")
        st.build(dict(flag=True))

    def test_flagsenum(self):
        assert FlagsEnum(Byte, a=1,b=2,c=4,d=8,e=16,f=32,g=64,h=128).parse(b'\x81') == FlagsContainer(a=True,b=False,c=False,d=False,e=False,f=False,g=False,h=True)
        assert FlagsEnum(Byte, a=1,b=2,c=4,d=8,e=16,f=32,g=64,h=128).build(FlagsContainer(a=True,b=False,c=False,d=False,e=False,f=False,g=False,h=True)) == b'\x81'
        assert FlagsEnum(Byte, feature=4,output=2,input=1).parse(b'\x04') == FlagsContainer(output=False,feature=True,input=False)
        assert FlagsEnum(Byte, feature=4,output=2,input=1).build(dict(feature=True, output=True, input=False)) == b'\x06'
        assert FlagsEnum(Byte, feature=4,output=2,input=1).build(dict(feature=True)) == b'\x04'
        assert FlagsEnum(Byte, feature=4,output=2,input=1).build(dict()) == b'\x00'
        assert raises(FlagsEnum(Byte, feature=4,output=2,input=1).build, dict(unknown=True)) == MappingError

    @pytest.mark.xfail(PY < (3,4), raises=AttributeError, reason="IntEnum introduced in 3.4, IntFlag introduced in 3.6")
    def test_flagsenum_enum34(self):
        import enum
        class E(enum.IntEnum):
            a = 1
        class F(enum.IntEnum):
            b = 2
        common(FlagsEnum(Byte, E, F), b"\x01", FlagsContainer(a=True,b=False), 1)
        common(FlagsEnum(Byte, E, F), b"\x02", FlagsContainer(a=False,b=True), 1)
        common(FlagsEnum(Byte, E, F), b"\x03", FlagsContainer(a=True,b=True), 1)

    @pytest.mark.xfail(PY < (3,6), raises=AttributeError, reason="IntEnum introduced in 3.4, IntFlag introduced in 3.6")
    def test_flagsenum_enum36(self):
        import enum
        class E(enum.IntEnum):
            a = 1
        class F(enum.IntFlag):
            b = 2
        common(FlagsEnum(Byte, E, F), b"\x01", FlagsContainer(a=True,b=False), 1)
        common(FlagsEnum(Byte, E, F), b"\x02", FlagsContainer(a=False,b=True), 1)
        common(FlagsEnum(Byte, E, F), b"\x03", FlagsContainer(a=True,b=True), 1)

    def test_struct(self):
        common(Struct("a"/Int16ul, "b"/Byte), b"\x01\x00\x02", Container(a=1,b=2), 3)
        common(Struct("a"/Struct("b"/Byte)), b"\x01", Container(a=Container(b=1)), 1)
        assert raises(Struct("missingkey"/Byte).build, dict()) == KeyError
        assert Struct("a"/Byte, "a"/VarInt, "a"/Pass).build(dict(a=1)) == b"\x01\x01"
        common(Struct(), b"", Container(), 0)
        common(Struct(Padding(2)), b"\x00\x00", Container(), 2)
        assert raises(Struct(Bytes(this.missing)).sizeof) == SizeofError

    def test_struct_nested_embedded(self):
        common(Struct("a"/Byte, "b"/Int16ub, "inner"/Struct("c"/Byte, "d"/Byte)), b"\x01\x00\x02\x03\x04", Container(a=1,b=2,inner=Container(c=3,d=4)), 5)
        common(Struct("a"/Byte, "b"/Int16ub, Embedded("inner"/Struct("c"/Byte, "d"/Byte))), b"\x01\x00\x02\x03\x04", Container(a=1,b=2,c=3,d=4), 5)

    @pytest.mark.xfail(not supportskwordered, reason="ordered kw was introduced in 3.6")
    def test_struct_kwctor(self):
        common(Struct(a=Byte, b=Byte, c=Byte, d=Byte), b"\x01\x02\x03\x04", Container(a=1,b=2,c=3,d=4), 4)

    def test_struct_proper_context(self):
        # adjusted to support new embedding semantics
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
                "a"/Computed(this.x+1),  # important
                "b"/Computed(this.y+2),  # important
            )),
            "c"/Computed(this.x+3),
            "d"/Computed(this.y+4),
        )
        assert d1.parse(b"\x01\x0f") == Container(x=1)(inner=Container(y=15)(a=2)(b=17))(c=4)(d=19)
        # a-field computed on nested context, merged only after entire inner-struct returns
        assert d2.parse(b"\x01\x0f") == Container(x=1)(y=15)(a=2)(b=17)(c=4)(d=19)

    @pytest.mark.xfail(reason="Struct._sizeof is broken, Struct nesting is the problem")
    def test_struct_sizeof_context_nesting(self):
        st = Struct(
            "length"/Byte,
            "inner"/Struct(
                "inner_length"/Byte,
                Probe(),
                "data"/Bytes(this._.length + this.inner_length),
        ))
        assert st.parse(b"\x03\x02helloXXX") == Container(length=3,inner=Container(inner_length=2,data=b"hello"))
        assert st.sizeof(length=3,inner=Container(inner_length=2)) == 7

        st = Struct(
            "a" / Byte,
            "inner" / Struct(
                "b" / Byte,
                If(this._.a == 1, Byte),
                If(this.b == 1, Byte),
            ),
            If(this.a == 1, Byte),
            If(this.inner.b == 1, Byte),
        )
        assert st.sizeof(a=0,inner=Container(b=0)) == 2
        assert st.sizeof(a=1,inner=Container(b=1)) == 6

    @pytest.mark.xfail(raises=KeyError, reason="unknown problem, heisen-bug?")
    def test_struct_issue_566(self):
        inner = Struct(
            Embedded(Struct(
                "b" / Byte,
            )),
            "c" / If(this._.a > 0, Byte),
        )
        outer = Struct(
            "a" / Byte,
            "inner" / inner,
        )
        outer.parse(b'\x01\x02\x03') == Container(a=1)(inner=Container(b=2)(c=3))
        outer.build(Container(a=1)(inner=Container(b=2)(c=3))) == b'\x01\x02\x80\x03\x04'

    def test_sequence(self):
        common(Sequence(Int8ub, Int16ub), b"\x01\x00\x02", [1,2], 3)
        common(Int8ub >> Int16ub, b"\x01\x00\x02", [1,2], 3)

    def test_sequence_nested_embedded(self):
        common(Sequence(Int8ub, Int16ub, Sequence(Int8ub, Int8ub)), b"\x01\x00\x02\x03\x04", [1,2,[3,4]], 5)
        common(Sequence(Int8ub, Int16ub, Embedded(Sequence(Int8ub, Int8ub))), b"\x01\x00\x02\x03\x04", [1,2,3,4], 5)

    def test_array(self):
        assert Byte[4].parse(b"1234") == [49,50,51,52]
        assert Byte[4].build([49,50,51,52]) == b"1234"

        assert Array(3,Byte).parse(b"\x01\x02\x03") == [1,2,3]
        assert Array(3,Byte).build([1,2,3]) == b"\x01\x02\x03"
        assert Array(3,Byte).parse(b"\x01\x02\x03additionalgarbage") == [1,2,3]
        assert raises(Array(3,Byte).parse, b"") == StreamError
        assert raises(Array(3,Byte).build, [1,2]) == RangeError
        assert raises(Array(3,Byte).build, [1,2,3,4,5,6,7,8]) == RangeError
        assert Array(3,Byte).sizeof() == 3

        assert Array(3, Byte).parse(b"\x01\x02\x03", n=3) == [1,2,3]
        assert Array(3, Byte).parse(b"\x01\x02\x03additionalgarbage", n=3) == [1,2,3]
        assert raises(Array(3, Byte).parse, b"", n=3) == StreamError
        assert Array(3, Byte).build([1,2,3], n=3) == b"\x01\x02\x03"
        assert raises(Array(3, Byte).build, [1,2], n=3) == RangeError
        assert Array(this.n, Byte).parse(b"\x01\x02\x03", n=3) == [1,2,3]
        assert Array(this.n, Byte).build([1,2,3], n=3) == b"\x01\x02\x03"
        assert raises(Array(this.n, Byte).sizeof) == SizeofError
        assert Array(this.n, Byte).sizeof(n=4) == 4

    def test_array_nontellable(self):
        assert Array(5, Byte).parse_stream(devzero) == [0,0,0,0,0]

    def test_range(self):
        assert Byte[2:4].parse(b"1234567890") == [49,50,51,52]
        assert Byte[2:4].build([49,50,51,52]) == b"1234"
        assert Byte[:4].parse(b"1234567890") == [49,50,51,52]
        assert Byte[:4].build([49,50,51,52]) == b"1234"
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
        assert raises(Range(3, 5, Byte).sizeof) == SizeofError
        assert Range(0, 100, Struct("id"/Byte)).parse(b'\x01\x02') == [Container(id=1),Container(id=2)]
        assert Range(0, 100, Struct("id"/Byte)).build([dict(id=i) for i in range(5)]) == b'\x00\x01\x02\x03\x04'
        assert Range(1, 1, Byte).sizeof() == 1
        assert raises(Range(1, 1, VarInt).sizeof) == SizeofError
        assert raises(Range(1, 9, Byte).sizeof) == SizeofError

    @pytest.mark.xfail(PY2, reason="for unknown reason, fails only on PY2")
    def test_range_nontellable(self):
        assert Range(5, 5, Byte).parse_stream(devzero) == [0,0,0,0,0]

    def test_greedyrange(self):
        common(GreedyRange(Byte), b"", [], SizeofError)
        common(GreedyRange(Byte), b"\x01\x02", [1,2], SizeofError)
        common(Byte[:], b"", [], SizeofError)
        common(Byte[:], b"\x01\x02", [1,2], SizeofError)

    def test_repeatuntil(self):
        assert RepeatUntil(obj_ == 9, Byte).parse(b"\x02\x03\x09garbage") == [2,3,9]
        assert RepeatUntil(obj_ == 9, Byte).build([2,3,9,1,1,1]) == b"\x02\x03\x09"
        assert raises(RepeatUntil(obj_ == 9, Byte).parse, b"\x02\x03\x08") == StreamError
        assert raises(RepeatUntil(obj_ == 9, Byte).build, [2,3,8]) == RepeatError
        assert raises(RepeatUntil(obj_ == 9, Byte).sizeof) == SizeofError
        assert RepeatUntil(lambda x,lst,ctx: lst[-2:]==[0,0], Byte).parse(b"\x01\x00\x00\xff") == [1,0,0]
        assert RepeatUntil(lambda x,lst,ctx: lst[-2:]==[0,0], Byte).build([1,0,0,4]) == b"\x01\x00\x00"

    def test_renamed(self):
        common(Struct(Renamed("new", Renamed("old", Byte))), b"\x01", Container(new=1), 1)

    def test_const(self):
        common(Const(b"MZ"), b"MZ", b"MZ", 2)
        common(Const(b"****", Bytes(4)), b"****", b"****", 4)
        common(Const(255, Int32ul), b"\xff\x00\x00\x00", 255, 4)
        assert raises(Const(b"MZ").parse, b"ELF") == ConstError
        assert raises(Const(b"MZ").build, b"???") == ConstError
        assert raises(Const(255, Int32ul).parse, b"\x00\x00\x00\x00") == ConstError
        common(Struct(sig=Const(b"MZ")), b"MZ", Container(sig=b"MZ"), 2)
        assert Struct(sig=Const(b"MZ")).build({}) == b"MZ"

    def test_const_nonbytes(self):
        # non-prefixed string literals are unicode on Python 3
        assert raises(lambda: Const(u"no prefix string")) == StringError

    def test_computed(self):
        assert Computed("moo").parse(b"") == "moo"
        assert Computed("moo").build(None) == b""
        assert Computed("moo").sizeof() == 0
        assert Struct("c" / Computed("moo")).parse(b"") == Container(c="moo")
        assert Struct("c" / Computed("moo")).build({}) == b""
        assert Struct("c" / Computed("moo")).build(dict()) == b""
        assert Struct("c" / Computed("moo")).build(Container()) == b""
        assert raises(Computed(lambda ctx: ctx.missing).parse, b"") == AttributeError
        assert raises(Computed(lambda ctx: ctx["missing"]).parse, b"") == KeyError

        assert Computed(255).parse(b"") == 255
        assert Computed(255).build(None) == b""
        assert Struct(c=Computed(255)).parse(b"") == dict(c=255)
        assert Struct(c=Computed(255)).build({}) == b""

    def test_rebuild(self):
        d = Struct("count"/Rebuild(Byte, len_(this.items)), "items"/Byte[this.count])
        assert d.parse(b"\x02ab") == Container(count=2)(items=[97,98])
        assert d.build(dict(count=None,items=[255])) == b"\x01\xff"
        assert d.build(dict(items=[255])) == b"\x01\xff"

    def test_default(self):
        common(Struct("a"/Default(Byte,0), "b"/Default(Byte,0)), b"\x01\x02", Container(a=1)(b=2), 2)
        assert Struct("a"/Default(Byte,0), "b"/Default(Byte,0)).build(dict(a=1)) == b"\x01\x00"

    def test_check(self):
        common(Check(True), b"", None, 0)
        common(Check(this.x == 255), b"", None, 0, x=255)
        common(Check(len_(this.a) == 3), b"", None, 0, a=[1,2,3])
        assert raises(Check(False).parse, b"") == ValidationError
        assert raises(Check(this.x == 255).parse, b"", x=0) == ValidationError
        assert raises(Check(len_(this.a) == 3).parse, b"", a=[]) == ValidationError

    def test_error(self):
        assert raises(Error.parse, b"") == ExplicitError
        assert raises(Error.build, None) == ExplicitError
        assert ("x"/Int8sb >> IfThenElse(this.x > 0, Int8sb, Error)).parse(b"\x01\x05") == [1,5]
        assert raises(("x"/Int8sb >> IfThenElse(this.x > 0, Int8sb, Error)).parse, b"\xff\x05") == ExplicitError

    def test_focusedseq(self):
        assert FocusedSeq(1, Const(b"MZ"), "num"/Byte, Terminated).parse(b"MZ\xff") == 255
        assert FocusedSeq(1, Const(b"MZ"), "num"/Byte, Terminated).build(255) == b"MZ\xff"
        assert FocusedSeq(1, Const(b"MZ"), "num"/Byte, Terminated).sizeof() == 3
        assert FocusedSeq("num", Const(b"MZ"), "num"/Byte, Terminated).parse(b"MZ\xff") == 255
        assert FocusedSeq("num", Const(b"MZ"), "num"/Byte, Terminated).build(255) == b"MZ\xff"
        assert FocusedSeq("num", Const(b"MZ"), "num"/Byte, Terminated).sizeof() == 3
        assert FocusedSeq(this._.s, Const(b"MZ"), "num"/Byte, Terminated).parse(b"MZ\xff", s=1) == 255
        assert FocusedSeq(this._.s, Const(b"MZ"), "num"/Byte, Terminated).sizeof(s=1) == 3
        assert FocusedSeq(this._.s, Const(b"MZ"), "num"/Byte, Terminated).parse(b"MZ\xff", s="num") == 255
        assert FocusedSeq(this._.s, Const(b"MZ"), "num"/Byte, Terminated).sizeof(s="num") == 3

        assert raises(FocusedSeq(123, Pass).parse, b"") == IndexError
        assert raises(FocusedSeq(123, Pass).build, {}) == IndexError
        # assert raises(FocusedSeq(123, Pass).sizeof) == IndexError
        assert raises(FocusedSeq("missing", Pass).parse, b"") == KeyError
        assert raises(FocusedSeq("missing", Pass).build, {}) == KeyError
        # assert raises(FocusedSeq("missing", Pass).sizeof) == KeyError
        assert raises(FocusedSeq(this.missing, Pass).parse, b"") == KeyError
        assert raises(FocusedSeq(this.missing, Pass).build, {}) == KeyError
        # assert raises(FocusedSeq(this.missing, Pass).sizeof) == SizeofError

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

        Coord = NamedTuple("coord", "x y z", Range(3, 3, Byte))
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

    def test_union(self):
        assert Union(None, "a"/Bytes(2), "b"/Int16ub).parse(b"\x01\x02") == Container(a=b"\x01\x02")(b=0x0102)
        assert raises(Union(123, Pass).parse, b"") == KeyError
        assert raises(Union("missing", Pass).parse, b"") == KeyError

        assert Union(None, "a"/Bytes(2), "b"/Int16ub).build(dict(a=b"zz"))  == b"zz"
        assert Union(None, "a"/Bytes(2), "b"/Int16ub).build(dict(b=0x0102)) == b"\x01\x02"
        assert Union(None, "a"/Bytes(2), "b"/Int16ub, Pass).build(dict()) == b""
        assert raises(Union(None, "a"/Bytes(2), "b"/Int16ub).build, dict()) == UnionError
        # build skips parsefrom, invalid or not
        # assert raises(Union(123, Pass).build, None) == None
        # assert raises(Union("missing", Pass).build, None) == None

        assert raises(Union(None, Byte).sizeof) == SizeofError
        assert raises(Union(None, VarInt).sizeof) == SizeofError
        assert raises(Union(0, Byte, VarInt).sizeof) == SizeofError
        assert raises(Union(1, Byte, VarInt).sizeof) == SizeofError
        assert raises(Union(123, Pass).sizeof) == SizeofError
        assert raises(Union("missing", Pass).sizeof) == SizeofError
        assert raises(Union(this.missing, Pass).sizeof) == SizeofError

        # regression check, so first subcon is not parsefrom by accident
        assert raises(Union, Byte, VarInt) == UnionError

    def test_union_embedded(self):
        d = Union(None, "a"/Int16ub, Embedded(Struct("b"/Int8ub, "c"/Int8ub))) >> Byte
        assert d.parse(b"\x01\x02\x03") == [Container(a=0x0102, b=0x01, c=0x01), 0x01]

        d = Union(None, "a"/Int16ub, Embedded(Struct("b"/Int8ub, "c"/Int8ub)))
        assert d.parse(b"\x01\x02") == Container(a=0x0102, b=0x01, c=0x01)
        assert d.build(dict(a=0x0102)) == b"\x01\x02"
        assert d.build(dict(b=0x01)) == b"\x01"
        assert d.build(dict(c=0x01)) == b"\x01"
        assert raises(d.build, dict()) == UnionError

    @pytest.mark.xfail(not supportskwordered, reason="ordered kw was introduced in 3.6")
    def test_union_kwctor(self):
        st = Union(None, a=Int8ub, b=Int16ub, c=Int32ub)
        assert st.parse(b"\x01\x02\x03\x04") == Container(a=0x01,b=0x0102,c=0x01020304)
        assert st.build(Container(c=0x01020304)) == b"\x01\x02\x03\x04"

    def test_union_issue_348(self):
        u = Union(None,
            Int8=Prefixed(Int16ub, Int8ub[:]),
            Int16=Prefixed(Int16ub, Int16ub[:]),
            Int32=Prefixed(Int16ub, Int32ub[:]),
        )
        assert u.parse(b'\x00\x04\x11\x22\x33\x44') == {'Int16': [4386, 13124], 'Int32': [287454020], 'Int8': [17, 34, 51, 68]}
        assert u.build(dict(Int16=[4386, 13124])) == b'\x00\x04\x11\x22\x33\x44'
        assert u.build(dict(Int32=[287454020])) == b'\x00\x04\x11\x22\x33\x44'

    def test_select(self):
        assert raises(Select(Int32ub, Int16ub).parse, b"\x07") == SelectError
        assert Select(Int32ub, Int16ub, Int8ub).parse(b"\x07") == 7
        assert Select(Int32ub, Int16ub, Int8ub).build(7) == b"\x00\x00\x00\x07"
        assert Select("a"/Int32ub, "b"/Int16ub, "c"/Int8ub, includename=True).parse(b"\x07") == ("c", 7)
        assert Select("a"/Int32ub, "b"/Int16ub, "c"/Int8ub, includename=True).build((("c", 7))) == b"\x07"
        assert raises(Select("a"/Int32ub, "b"/Int16ub, "c"/Int8ub, includename=True).build, (("d", 7))) == SelectError
        assert raises(Select(Byte).sizeof) == SizeofError

    @pytest.mark.xfail(not supportskwordered, reason="ordered kw was introduced in 3.6")
    def test_select_kwctor(self):
        st = Select(a=Int8ub, b=Int16ub, c=Int32ub)
        assert st.parse(b"\x01\x02\x03\x04") == 0x01
        assert st.build(0x01020304) == b"\x01\x02\x03\x04"

    def test_optional(self):
        assert Optional(Int32ul).parse(b"\x01\x00\x00\x00") == 1
        assert Optional(Int32ul).build(1) == b"\x01\x00\x00\x00"
        assert Optional(Int32ul).parse(b"???") == None
        assert Optional(Int32ul).build(None) == b""
        assert raises(Optional(Int32ul).sizeof) == SizeofError

    def test_if(self):
        common(If(True,  Byte), b"\x01", 1, 1)
        common(If(False, Byte), b"", None, 0)

    def test_ifthenelse(self):
        common(IfThenElse(True,  Int8ub, Int16ub), b"\x01", 1, 1)
        common(IfThenElse(False, Int8ub, Int16ub), b"\x00\x01", 1, 2)

    def test_switch(self):
        assert Switch(5, {1:Byte, 5:Int16ub}).parse(b"\x00\x02") == 2
        assert Switch(6, {1:Byte, 5:Int16ub}, default=Byte).parse(b"\x00\x02") == 0
        assert Switch(5, {1:Byte, 5:Int16ub}, includekey=True).parse(b"\x00\x02") == (5,2)
        assert Switch(5, {1:Byte, 5:Int16ub}).build(2) == b"\x00\x02"
        assert Switch(6, {1:Byte, 5:Int16ub}, default=Byte).build(9) == b"\x09"
        assert Switch(5, {1:Byte, 5:Int16ub}, includekey=True).build((5,2)) == b"\x00\x02"
        assert raises(Switch(6, {1:Byte, 5:Int16ub}).parse, b"\x00\x02") == SwitchError
        assert raises(Switch(6, {1:Byte, 5:Int16ub}).build, 9) == SwitchError
        assert raises(Switch(5, {1:Byte, 5:Int16ub}, includekey=True).build, (89,2)) == SwitchError
        assert Switch(5, {1:Byte, 5:Int16ub}).sizeof() == 2
        assert raises(Switch(5, {}).sizeof) == SwitchError

    def test_switch_issue_357(self):
        inner = Struct(
            "computed" / Computed(4),
        )
        inner2 = Struct(
            "computed" / Computed(7),
        )
        st1 = Struct(
            "a" / inner,
            "b" / Switch(5, {1: inner2}, inner),
            Probe(),
        )
        st2 = Struct(
            "a" / inner,
            "b" / Switch(5, {}, inner),
            Probe(),
        )
        assert st1.parse(b"") == st2.parse(b"")

    @pytest.mark.xfail(reason="unknown cause")
    def test_stopif(self):
        d = Struct("x"/Byte, StopIf(this.x == 0), Error)
        common(d, b"\x00", Container(x=0))
        common(d, b"\x01\x02", Container(x=1,y=2))

        d = Sequence(Byte, StopIf(this.x == 0), Error)
        common(d, b"\x00", [0])
        common(d, b"\x01\x02", [1,None,2])

        d = FocusedSeq(0, Byte, StopIf(this.x == 0), Error)
        common(d, b"\x00", 0)

        d = GreedyRange(FocusedSeq(0, 'x'/Byte, StopIf(this.x == 0)))
        assert d.parse(b"\x01\x00?????") == [1]
        assert d.build([]) == b""
        assert d.build([0]) == b"\x00"
        assert d.build([1]) == b"\x01"
        assert d.build([1,0,2]) == b"\x01\x00"

    def test_padding(self):
        common(Padding(4), b"\x00\x00\x00\x00", None, 4)
        assert raises(Padding, 4, pattern=b"?????") == PaddingError
        assert raises(Padding, 4, pattern=u"?") == PaddingError

    def test_padded(self):
        common(Padded(4, Byte), b"\x01\x00\x00\x00", 1, 4)
        assert raises(Padded, 4, Byte, pattern=b"?????") == PaddingError
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
        assert Aligned(this.m, Byte).parse(b"\xff\x00", m=2) == 255
        assert Aligned(this.m, Byte).build(255, m=2) == b"\xff\x00"
        assert Aligned(this.m, Byte).sizeof(m=2) == 2
        assert raises(Aligned(this.m, Byte).sizeof) == SizeofError

    def test_alignedstruct(self):
        assert AlignedStruct(4, "a"/Int8ub, "b"/Int16ub).parse(b"\x01\x00\x00\x00\x00\x05\x00\x00") == Container(a=1)(b=5)
        assert AlignedStruct(4, "a"/Int8ub, "b"/Int16ub).build(dict(a=1,b=5)) == b"\x01\x00\x00\x00\x00\x05\x00\x00"

    def test_bitstruct(self):
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "d"/BitsInteger(5)).parse(b"\xe1\x1f") == Container(a=7)(b=False)(c=8)(d=31)
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "d"/BitsInteger(5)).build(Container(a=7)(b=False)(c=8)(d=31)) == b"\xe1\x1f"
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "d"/BitsInteger(5)).sizeof() == 2
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "sub"/Struct("d"/Nibble, "e"/Bit)).parse(b"\xe1\x1f") == Container(a=7)(b=False)(c=8)(sub=Container(d=15)(e=1))
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "sub"/Struct("d"/Nibble, "e"/Bit)).sizeof() == 2
        assert BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "sub"/Struct("d"/Nibble, "e"/Bit)).build(Container(a=7)(b=False)(c=8)(sub=Container(d=15)(e=1))) == b"\xe1\x1f"

    @pytest.mark.xfail(reason="new embedding semantics, needs fixing")
    def test_embeddedbitstruct1(self):
        d = Struct(
            "len" / Byte,
            EmbeddedBitStruct("data" / BitsInteger(8)),
        )
        assert d.parse(b"\x08\xff") == Container(len=8)(data=255)
        assert d.build(dict(len=8,data=255)) == b"\x08\xff"
        assert d.sizeof() == 2

    @pytest.mark.xfail(reason="new embedding semantics, needs fixing")
    def test_embeddedbitstruct2_issue_39(self):
        d = Struct(
            "len" / Byte,
            EmbeddedBitStruct("data" / BitsInteger(this.len)),
        )
        assert d.parse(b"\x08\xff") == Container(len=8)(data=255)
        assert d.build(dict(len=8,data=255)) == b"\x08\xff"
        assert raises(d.sizeof) == SizeofError

    def test_pointer(self):
        common(Pointer(2,             Byte), b"\x00\x00\x07", 7, SizeofError)
        common(Pointer(lambda ctx: 2, Byte), b"\x00\x00\x07", 7, SizeofError)

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

    def test_seek(self):
        assert Seek(5).parse(b"") == 5
        assert Seek(5).build(None) == b""
        assert (Seek(5) >> Byte).parse(b"01234x") == [5,120]
        assert (Seek(5) >> Byte).build([5,255]) == b"\x00\x00\x00\x00\x00\xff"
        assert (Bytes(10) >> Seek(5) >> Byte).parse(b"0123456789") == [b"0123456789",5,ord('5')]
        assert (Bytes(10) >> Seek(5) >> Byte).build([b"0123456789",None,255]) == b"01234\xff6789"
        assert Struct("data"/Bytes(10), Seek(5), "addin"/Byte).parse(b"0123456789") == Container(data=b"0123456789")(addin=53)
        assert Struct("data"/Bytes(10), Seek(5), "addin"/Byte).build(dict(data=b"0123456789",addin=53)) == b"01234\x356789"
        assert (Seek(10,1) >> Seek(-5,1) >> Bytes(1)).parse(b"0123456789") == [10,5,b"5"]
        assert (Seek(10,1) >> Seek(-5,1) >> Bytes(1)).build([None,None,255]) == b"\x00\x00\x00\x00\x00\xff"
        assert raises(Seek(5).sizeof) == SizeofError

    def test_tell(self):
        assert Tell.parse(b"") == 0
        assert Tell.build(None) == b""
        assert Tell.sizeof() == 0
        assert Struct("a"/Tell, "b"/Byte, "c"/Tell).parse(b"\xff") == Container(a=0)(b=255)(c=1)
        assert Struct("a"/Tell, "b"/Byte, "c"/Tell).build(Container(a=0)(b=255)(c=1)) == b"\xff"
        assert Struct("a"/Tell, "b"/Byte, "c"/Tell).build(dict(b=255)) == b"\xff"

    def test_pass(self):
        common(Pass, b"", None, 0)
        common(Struct("empty"/Pass), b"", Container(empty=None), 0)

    def test_terminated(self):
        common(Terminated, b"", None, 0)
        common(Struct("end"/Terminated), b"", Container(end=None), 0)
        common(BitStruct("end"/Terminated), b"", Container(end=None), 0)
        assert raises(Terminated.parse, b"x") == TerminatedError
        assert raises(Struct("end"/Terminated).parse, b"x") == TerminatedError
        assert raises(BitStruct("end"/Terminated).parse, b"x") == TerminatedError

    def test_restreamed(self):
        assert Restreamed(Int16ub, ident, 1, ident, 1, ident).parse(b"\x00\x01") == 1
        assert Restreamed(Int16ub, ident, 1, ident, 1, ident).build(1) == b"\x00\x01"
        assert Restreamed(Int16ub, ident, 1, ident, 1, ident).sizeof() == 2
        assert raises(Restreamed(VarInt, ident, 1, ident, 1, ident).sizeof) == SizeofError
        assert Restreamed(Bytes(2), lambda b: b*2, 1, None, None, None).parse(b"a") == b"aa"
        assert Restreamed(Bytes(1), None, None, lambda b: b*2, 1, None).build(b"a") == b"aa"
        assert Restreamed(Bytes(5), None, None, None, None, lambda n: n*2).sizeof() == 10

    def test_restreamed_partial_read(self):
        d = Restreamed(Bytes(255), ident, 1, ident, 1, ident)
        assert raises(d.parse, b"") == StreamError

    def test_rebuffered(self):
        data = b"0" * 1000
        assert Rebuffered(Array(1000,Byte)).parse_stream(io.BytesIO(data)) == [48]*1000
        assert Rebuffered(Array(1000,Byte), tailcutoff=50).parse_stream(io.BytesIO(data)) == [48]*1000
        assert Rebuffered(Byte).sizeof() == 1
        assert raises(Rebuffered(Byte).sizeof) == None
        assert raises(Rebuffered(VarInt).sizeof) == SizeofError

    def test_rawcopy(self):
        assert RawCopy(Byte).parse(b"\xff") == dict(data=b"\xff", value=255, offset1=0, offset2=1, length=1)
        assert RawCopy(Byte).build(dict(data=b"\xff")) == b"\xff"
        assert RawCopy(Byte).build(dict(value=255)) == b"\xff"
        assert RawCopy(Byte).sizeof() == 1

    def test_rawcopy_issue_289(self):
        # When you build from a full dict that has all the keys, the if data kicks in, and replaces the context entry with a subset of a dict it had to begin with.
        st = Struct(
            "raw" / RawCopy(Struct("x"/Byte, "len"/Byte)),
            "array" / Byte[this.raw.value.len],
        )
        print(st.parse(b"\x01\x02\xff\x00"))
        print(st.build(dict(raw=dict(value=dict(x=1, len=2)), array=[0xff, 0x01])))
        print(st.build(st.parse(b"\x01\x02\xff\x00")))
        # this is not buildable, array is not passed and cannot be deduced from raw data
        # print(st.build(dict(raw=dict(data=b"\x01\x02\xff\x00"))))

    def test_rawcopy_issue_358(self):
        # RawCopy overwritten context value with subcon return obj regardless of None
        d = Struct("a"/RawCopy(Byte), "check"/Check(this.a.value == 255))
        assert d.build(dict(a=dict(value=255))) == b"\xff"

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

    def test_prefixed(self):
        assert Prefixed(Byte, Int16ul).parse(b"\x02\xff\xff??????") == 65535
        assert Prefixed(Byte, Int16ul).build(65535) == b"\x02\xff\xff"
        assert Prefixed(Byte, Int16ul).sizeof() == 3
        assert Prefixed(VarInt, GreedyBytes).parse(b"\x03abc??????") == b"abc"
        assert Prefixed(VarInt, GreedyBytes).build(b"abc") == b'\x03abc'
        assert Prefixed(Byte, Int64ub).sizeof() == 9
        assert Prefixed(Byte, Sequence(Peek(Byte), Int16ub, GreedyBytes)).parse(b"\x02\x00\xff????????") == [0,255,b'']
        assert raises(Prefixed(VarInt, GreedyBytes).sizeof) == SizeofError

    def test_prefixedarray(self):
        common(PrefixedArray(Byte,Byte), b"\x02\x0a\x0b", [10,11], SizeofError)
        assert PrefixedArray(Byte, Byte).parse(b"\x03\x01\x02\x03") == [1,2,3]
        assert PrefixedArray(Byte, Byte).parse(b"\x00") == []
        assert PrefixedArray(Byte, Byte).build([1,2,3]) == b"\x03\x01\x02\x03"
        assert raises(PrefixedArray(Byte, Byte).parse, b"") == StreamError
        assert raises(PrefixedArray(Byte, Byte).parse, b"\x03\x01") == StreamError
        assert raises(PrefixedArray(Byte, Byte).sizeof) == SizeofError

    def test_restreamdata(self):
        assert RestreamData(b"\xff", Byte).parse(b"") == 255
        assert RestreamData(b"\xff", Byte).parse(b"\x00") == 255
        assert RestreamData(b"\xff", Byte).build(0) == b"\x00"
        assert RestreamData(b"\xff", Byte).sizeof() == 1

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

    def test_checksum_nonbytes_issue_323(self):
        st = Struct(
            "vals" / Byte[2],
            "checksum" / Checksum(Byte, lambda vals: sum(vals) & 0xFF, this.vals),
        )
        assert st.parse(b"\x00\x00\x00") == Container(vals=[0, 0])(checksum=0)
        assert raises(st.parse, b"\x00\x00\x01") == ChecksumError

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

    @pytest.mark.xfail(PY < (3,2), raises=AttributeError, reason="gzip was added in 3.2")
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

    @pytest.mark.xfail(PY < (3,3), raises=ImportError, reason="lzma module was added in 3.3")
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

    def test_lazystruct(self):
        assert LazyStruct().parse(b"") == Struct().parse(b"")
        assert LazyStruct().build({}) == Struct().build({})
        assert LazyStruct().sizeof() == Struct().sizeof()
        assert LazyStruct("a"/Byte, "b"/CString(encoding=StringsAsBytes)).build(dict(a=1,b=b"abc")) == b"\x01abc\x00"
        assert raises(LazyStruct("a"/Byte, "b"/CString(encoding=StringsAsBytes)).sizeof) == SizeofError
        assert LazyStruct("a"/Byte).build(dict(a=1)) == b"\x01"
        assert LazyStruct("a"/Byte).sizeof() == 1
        assert LazyStruct(Pass, Computed(0), Terminated).build(dict()) == b""
        assert LazyStruct(Pass, Computed(0), Terminated).sizeof() == 0
        assert LazyStruct("a"/Byte, "b"/LazyStruct("c"/Byte)).build(dict(a=1,b=dict(c=2))) == b"\x01\x02"
        assert LazyStruct().parse(b"") == dict()
        assert LazyStruct().build(dict()) == b""

        assert dict(LazyStruct("a"/Byte).parse(b"\x01")) == dict(a=1)
        assert LazyStruct("a"/Byte).build(dict(a=1)) == b"\x01"
        assert dict(LazyStruct("a"/Byte,"b"/CString(encoding=StringsAsBytes)).parse(b"\x01abc\x00")) == dict(a=1,b=b"abc")
        assert LazyStruct("a"/Byte,"b"/CString(encoding=StringsAsBytes)).build(dict(a=1,b=b"abc")) == b"\x01abc\x00"
        assert dict(LazyStruct(Pass, Computed(0), Terminated).parse(b"")) == dict()
        assert LazyStruct(Pass, Computed(0), Terminated).build(dict()) == b""

    @pytest.mark.xfail(not supportskwordered, reason="ordered kw was introduced in 3.6")
    def test_lazystruct_kwctor(self):
        common(LazyStruct(a=Byte, b=Byte, c=Byte, d=Byte), b"\x01\x02\x03\x04", Container(a=1,b=2,c=3,d=4), 4)

    def test_lazystruct_nested_embedded(self):
        assert dict(LazyStruct("a"/Byte,"b"/LazyStruct("c"/Byte)).parse(b"\x01\x02")) == dict(a=1,b=dict(c=2))
        assert LazyStruct("a"/Byte,"b"/LazyStruct("c"/Byte)).build(dict(a=1,b=dict(c=2))) == b"\x01\x02"
        assert dict(LazyStruct("a"/Byte,Embedded(LazyStruct("c"/Byte))).parse(b"\x01\x02")) == dict(a=1,c=2)
        assert LazyStruct("a"/Byte,Embedded(LazyStruct("c"/Byte))).build(dict(a=1,c=2)) == b"\x01\x02"

    def test_lazysequence(self):
        assert LazySequence(Int8ub, Int16ub).parse(b"\x01\x00\x02") == [1,2]
        assert LazySequence(Int8ub, Int16ub).build([1,2]) == b"\x01\x00\x02"
        assert LazySequence().parse(b"") == []
        assert LazySequence().build([]) == b""
        assert LazySequence().sizeof() == 0

        assert LazySequence(Int8ub,Int16ub).parse(b"\x01\x00\x02") == Sequence(Int8ub,Int16ub).parse(b"\x01\x00\x02")
        assert LazySequence(Int8ub,Int16ub).build([1,2]) == Sequence(Int8ub,Int16ub).build([1,2])
        assert LazySequence(Int8ub,Int16ub).sizeof() == Sequence(Int8ub,Int16ub).sizeof()

    @pytest.mark.xfail(not supportskwordered, reason="ordered kw was introduced in 3.6")
    def test_lazysequence_kwctor(self):
        common(LazySequence(a=Byte, b=Byte, c=Byte, d=Byte), b"\x01\x02\x03\x04", [1,2,3,4], 4)

    def test_lazysequence_nested_embedded(self):
        assert LazySequence(Int8ub, Int16ub, LazySequence(Int8ub, Int8ub)).parse(b"\x01\x00\x02\x03\x04") == [1,2,[3,4]]
        assert LazySequence(Int8ub, Int16ub, LazySequence(Int8ub, Int8ub)).build([1,2,[3,4]]) == b"\x01\x00\x02\x03\x04"
        assert LazySequence(Int8ub, Int16ub, Embedded(LazySequence(Int8ub, Int8ub))).parse(b"\x01\x00\x02\x03\x04") == [1,2,3,4]
        assert LazySequence(Int8ub, Int16ub, Embedded(LazySequence(Int8ub, Int8ub))).build([1,2,3,4]) == b"\x01\x00\x02\x03\x04"

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

    def test_ondemand(self):
        assert OnDemand(Byte).parse(b"\x01garbage")() == 1
        assert OnDemand(Byte).build(1) == b"\x01"
        assert OnDemand(Byte).sizeof() == 1

        parseret = OnDemand(Byte).parse(b"\x01garbage")
        assert OnDemand(Byte).build(parseret) == b"\x01"

    def test_lazybound(self):
        common(LazyBound(lambda ctx: Byte), b"\x01", 1, 1)

        st = Struct(
            "value"/Byte,
            "next"/If(this.value > 0, LazyBound(lambda ctx: st)),
        )
        common(st, b"\x05\x09\x00", Container(value=5)(next=Container(value=9)(next=Container(value=0)(next=None))), SizeofError)

    def test_lazybound_node(self):
        print("need some ideas how to test it")
        Node = Struct(
            "value" / Int8ub,
            "next" / LazyBound(lambda ctx: Node), )

    def test_expradapter(self):
        MulDiv = ExprAdapter(Byte, obj_ * 7, obj_ // 7)
        assert MulDiv.parse(b"\x06") == 42
        assert MulDiv.build(42) == b"\x06"
        assert MulDiv.sizeof() == 1

        Ident = ExprAdapter(Byte, obj_-1, obj_+1)
        assert Ident.parse(b"\x02") == 1
        assert Ident.build(1) == b"\x02"
        assert Ident.sizeof() == 1

        self.test_hex()
        self.test_hexdump()

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

    def test_ipaddress_adapter_issue_95(self):
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

    def test_oneof(self):
        assert OneOf(Byte,[4,5,6,7]).parse(b"\x05") == 5
        assert OneOf(Byte,[4,5,6,7]).build(5) == b"\x05"
        assert raises(OneOf(Byte,[4,5,6,7]).parse, b"\x08") == ValidationError
        assert raises(OneOf(Byte,[4,5,6,7]).build, 8) == ValidationError

    def test_noneof(self):
        assert NoneOf(Byte,[4,5,6,7]).parse(b"\x08") == 8
        assert raises(NoneOf(Byte,[4,5,6,7]).parse, b"\x06") == ValidationError

    def test_filter(self):
        assert Filter(obj_ != 0, Byte[:]).parse(b"\x00\x02\x00") == [2]
        assert Filter(obj_ != 0, Byte[:]).build([0,1,0,2,0]) == b"\x01\x02"

    def test_slicing(self):
        assert Slicing(Array(4,Byte), 4, 1, 3, empty=0).parse(b"\x01\x02\x03\x04") == [2,3]
        assert Slicing(Array(4,Byte), 4, 1, 3, empty=0).build([2,3]) == b"\x00\x02\x03\x00"
        assert Slicing(Array(4,Byte), 4, 1, 3, empty=0).sizeof() == 4

    def test_indexing(self):
        assert Indexing(Array(4,Byte), 4, 2, empty=0).parse(b"\x01\x02\x03\x04") == 3
        assert Indexing(Array(4,Byte), 4, 2, empty=0).build(3) == b"\x00\x00\x03\x00"
        assert Indexing(Array(4,Byte), 4, 2, empty=0).sizeof() == 4

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

    def test_operators_issue_87(self):
        assert ("string_name" / Byte).parse(b"\x01") == 1
        assert (u"unicode_name" / Byte).parse(b"\x01") == 1
        assert (b"bytes_name" / Byte).parse(b"\x01") == 1
        assert (None / Byte).parse(b"\x01") == 1

    def test_from_issue_76(self):
        assert Aligned(4, Struct("a"/Byte, "f"/Bytes(lambda ctx: ctx.a))).parse(b"\x02\xab\xcd\x00") == Container(a=2)(f=b"\xab\xcd")
        assert Aligned(4, Struct("a"/Byte, "f"/Bytes(lambda ctx: ctx.a))).build(Container(a=2)(f=b"\xab\xcd")) == b"\x02\xab\xcd\x00"

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
        setglobalstringencoding(StringsAsBytes)
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
        setglobalstringencoding(None)

    # def test_from_issue_28(self):

    #     def vstring(name, embed=True, optional=True):
    #         lfield = "_%s_length" % name.lower()
    #         s = Struct(
    #             lfield / Byte,
    #             name / Bytes(lambda ctx: getattr(ctx, lfield)))
    #         if optional:
    #             s = Optional(s)
    #         if embed:
    #             s = Embedded(s)
    #         return s

    #     def build_struct(embed_g=True, embed_h=True):
    #         s = "mystruct" / Struct(
    #             "a" / Int32ul,
    #             "b" / Int8ul,
    #             "c" / Int8ul,
    #             "d" / BitStruct("dx" / Bit[8]),
    #             "e" / BitStruct("ex" / Bit[8]),
    #             "f" / Float32b,
    #             vstring("g", embed=embed_g),
    #             vstring("h", embed=embed_h),
    #             "i" / BitStruct("ix" / Bit[8]),
    #             "j" / Int8sb,
    #             "k" / Int8sb,
    #             "l" / Int8sb,
    #             "m" / Float32l,
    #             "n" / Float32l,
    #             vstring("o"),
    #             vstring("p"),
    #             vstring("q"),
    #             vstring("r"))
    #         return s

    #     data = b'\xc3\xc0{\x00\x01\x00\x00\x00HOqA\x12some silly text...\x00\x0e\x00\x00\x00q=jAq=zA\x02dB\x02%f\x02%f\x02%f'
    #     print("\n\nNo embedding for neither g and h, i is a container --> OK")
    #     print(build_struct(embed_g=False, embed_h=False).parse(data))
    #     print("Embed both g and h, i is not a container --> FAIL")
    #     print(build_struct(embed_g=True, embed_h=True).parse(data))
    #     print("\n\nEmbed g but not h --> EXCEPTION")
    #     print(build_struct(embed_g=True, embed_h=False).parse(data))
    #     # When setting optional to False in vstring method, all three tests above work fine.

    def test_from_issue_231(self):
        u = Union(0, "raw"/Byte[8], "ints"/Int[2])
        s = Struct("u"/u, "d"/Byte[4])

        buildret = s.build(dict(u=dict(ints=[1,2]),d=[0,1,2,3]))
        assert buildret == b"\x00\x00\x00\x01\x00\x00\x00\x02\x00\x01\x02\x03"
        assert s.build(s.parse(buildret)) == buildret

    def test_from_issue_246(self):
        NumVertices = Bitwise(Aligned(8, Struct(
            'numVx4' / BitsInteger(4),
            'numVx8' / If(this.numVx4 == 0, BitsInteger(8)),
            'numVx16' / If(this.numVx4 == 0 & this.numVx8 == 255, BitsInteger(16)),
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

        NumVertices = Union(None,
            'numVx4' / Bitwise(Aligned(8, Struct('num'/ BitsInteger(4) ))),
            'numVx8' / Bitwise(Aligned(8, Struct('num'/ BitsInteger(12)))),
            'numVx16'/ Bitwise(Aligned(8, Struct('num'/ BitsInteger(28)))),
        )
        assert NumVertices.parse(b'\x01\x34\x56\x70') == Container(numVx4=Container(num=0))(numVx8=Container(num=19))(numVx16=Container(num=1262951))

    def test_from_issue_244(self):
        class AddIndexes(Adapter):
            def __init__(self, subcon):
                super(AddIndexes, self).__init__(subcon)
            def _decode(self, obj, context):
                for i,con in enumerate(obj):
                    con.index = i
                return obj

        assert AddIndexes(Struct("num"/Byte)[4]).parse(b"abcd") == [Container(num=97)(index=0),Container(num=98)(index=1),Container(num=99)(index=2),Container(num=100)(index=3),]

    def test_from_issue_269(self):
        st = Struct("enabled" / Byte, If(this.enabled, Padding(2)))
        assert st.build(dict(enabled=1)) == b"\x01\x00\x00"
        assert st.build(dict(enabled=0)) == b"\x00"
        st = Struct("enabled" / Byte, "pad" / If(this.enabled, Padding(2)))
        assert st.build(dict(enabled=1)) == b"\x01\x00\x00"
        assert st.build(dict(enabled=0)) == b"\x00"

    def test_hanging_issue_280(self):
        st = BitStruct('a'/BitsInteger(20), 'b'/BitsInteger(12))
        assert raises(st.parse, b'\x00') == StreamError

    def test_from_issue_324(self):
        d = Struct(
            "vals" / Prefixed(Byte, RawCopy(
                Struct("a" / Byte[2]),
            )),
            "checksum" / Checksum(
                Byte,
                lambda data: sum(iterateints(data)) & 0xFF,
                this.vals.data
            ),
        )
        assert d.build(dict(vals=dict(value=dict(a=[0,1])))) == b"\x02\x00\x01\x01"
        assert d.build(dict(vals=dict(data=b"\x00\x01"))) == b"\x02\x00\x01\x01"

    # def test_embeddedif_issue_296(self):
    #     st = 'BuggedStruct' / Struct(
    #         'ctrl' / Bytes(1),
    #         Probe(),
    #         Embedded(If(
    #             this.ctrl == b'\x02',
    #             Struct('etx' / Const(b'\x03')),
    #         )),
    #         Probe(),
    #     )
    #     p1 = st.parse(b'\x02\x03')
    #     p3 = st.parse(b'\x06')

    # def test_embeddedif_issue_312(self):
    #     st = Struct(
    #         'name'/CString(encoding="utf8"),
    #         Embedded(If(len_(this.name) > 0,
    #             Struct('index'/Byte),
    #         )),
    #     )
    #     assert st.parse(b'bob\x00\x05') == Container(name='bob')(index=5)
    #     assert st.parse(b'\x00') == Container(name='')

    @pytest.mark.xfail(strict=True, reason="this cannot work, Struct checks flagembedded before building")
    def test_embeddedswitch_issue_312_cannotwork(self):
        st = Struct(
            'name'/CString(encoding="utf8"),
            If(len_(this.name) > 0,
                Embedded(Struct('index'/Byte)),
            ),
        )
        assert st.parse(b'bob\x00\x05') == Container(name='bob')(index=5)
        assert st.parse(b'\x00') == Container(name='')

    def test_from_issue_357(self):
        inner = Struct(
            "computed" / Computed(4),
        )
        st1 = Struct(
            "a" / inner,
            Check(this.a.computed == 4),
        )
        st2 = Struct(
            "b" / Switch(0, {}, inner),
            Check(this.b.computed == 4),
        )
        assert st1.build(dict(a={})) == b""
        assert st2.build(dict(b={})) == b""

    def test_context_is_container(self):
        st = Struct(Check(lambda ctx: type(ctx) is Container))
        st.parse(b"")

    def test_from_issue_362(self):
        FORMAT = Struct(
            "my_tell" / Tell,
            "my_byte" / Byte,
        )
        BIT_FORMAT = BitStruct(
            "my_tell" / Tell,
            "my_bits" / Bit[8],
        )
        for i in range(5):
            assert FORMAT.parse(b'\x00').my_tell == 0
        for i in range(5):
            assert BIT_FORMAT.parse(b'\x00').my_tell == 0


    def test_compiler_recursion(self):
        raises(Construct().compile) == NotImplementedError
