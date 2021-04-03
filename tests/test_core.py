# -*- coding: utf-8 -*-

from tests.declarativeunittest import *
from construct import *
from construct.lib import *

def test_bytes():
    d = Bytes(4)
    common(d, b"1234", b"1234", 4)
    assert d.parse(b"1234567890") == b"1234"
    assert raises(d.parse, b"") == StreamError
    assert raises(d.build, b"looooooooooooooong") == StreamError
    assert d.build(1) == b"\x00\x00\x00\x01"
    assert d.build(0x01020304) == b"\x01\x02\x03\x04"

    d = Bytes(this.n)
    common(d, b"1234", b"1234", 4, n=4)
    assert d.parse(b"1234567890",n=4) == b"1234"
    assert d.build(1, n=4) == b"\x00\x00\x00\x01"
    assert raises(d.build, b"", n=4) == StreamError
    assert raises(d.build, b"toolong", n=4) == StreamError
    assert raises(d.sizeof) == SizeofError
    assert raises(d.sizeof, n=4) == 4

def test_greedybytes():
    common(GreedyBytes, b"1234", b"1234", SizeofError)

def test_bytes_issue_827():
    d = Bytes(3)
    assert d.build(bytearray(b'\x01\x02\x03')) == b'\x01\x02\x03'
    d = GreedyBytes
    assert d.build(bytearray(b'\x01\x02\x03')) == b'\x01\x02\x03'

def test_bitwise():
    common(Bitwise(Bytes(8)), b"\xff", b"\x01\x01\x01\x01\x01\x01\x01\x01", 1)
    common(Bitwise(Array(8,Bit)), b"\xff", [1,1,1,1,1,1,1,1], 1)
    common(Bitwise(Array(2,Nibble)), b"\xff", [15,15], 1)
    common(Bitwise(Array(1,Octet)), b"\xff", [255], 1)

    common(Bitwise(GreedyBytes), bytes(10), bytes(80), SizeofError)

def test_bytewise():
    common(Bitwise(Bytewise(Bytes(1))), b"\xff", b"\xff", 1)
    common(BitStruct("p1"/Nibble, "num"/Bytewise(Int24ub), "p2"/Nibble), b"\xf0\x10\x20\x3f", Container(p1=15, num=0x010203, p2=15), 4)
    common(Bitwise(Sequence(Nibble, Bytewise(Int24ub), Nibble)), b"\xf0\x10\x20\x3f", [0x0f,0x010203,0x0f], 4)
    common(Bitwise(Bytewise(GreedyBytes)), bytes(10), bytes(10), SizeofError)

def test_ints():
    common(Byte, b"\xff", 255, 1)
    common(Short, b"\x00\xff", 255, 2)
    common(Int, b"\x00\x00\x00\xff", 255, 4)
    common(Long, b"\x00\x00\x00\x00\x00\x00\x00\xff", 255, 8)

    common(Int8ub, b"\x01", 0x01, 1)
    common(Int16ub, b"\x01\x02", 0x0102, 2)
    common(Int32ub, b"\x01\x02\x03\x04", 0x01020304, 4)
    common(Int64ub, b"\x01\x02\x03\x04\x05\x06\x07\x08", 0x0102030405060708, 8)

    common(Int8sb, b"\x01", 0x01, 1)
    common(Int16sb, b"\x01\x02", 0x0102, 2)
    common(Int32sb, b"\x01\x02\x03\x04", 0x01020304, 4)
    common(Int64sb, b"\x01\x02\x03\x04\x05\x06\x07\x08", 0x0102030405060708, 8)
    common(Int8sb, b"\xff", -1, 1)
    common(Int16sb, b"\xff\xff", -1, 2)
    common(Int32sb, b"\xff\xff\xff\xff", -1, 4)
    common(Int64sb, b"\xff\xff\xff\xff\xff\xff\xff\xff", -1, 8)

    common(Int8ul, b"\x01", 0x01, 1)
    common(Int16ul, b"\x01\x02", 0x0201, 2)
    common(Int32ul, b"\x01\x02\x03\x04", 0x04030201, 4)
    common(Int64ul, b"\x01\x02\x03\x04\x05\x06\x07\x08", 0x0807060504030201, 8)

    common(Int8sl, b"\x01", 0x01, 1)
    common(Int16sl, b"\x01\x02", 0x0201, 2)
    common(Int32sl, b"\x01\x02\x03\x04", 0x04030201, 4)
    common(Int64sl, b"\x01\x02\x03\x04\x05\x06\x07\x08", 0x0807060504030201, 8)
    common(Int8sl, b"\xff", -1, 1)
    common(Int16sl, b"\xff\xff", -1, 2)
    common(Int32sl, b"\xff\xff\xff\xff", -1, 4)
    common(Int64sl, b"\xff\xff\xff\xff\xff\xff\xff\xff", -1, 8)

def test_ints24():
    common(Int24ub, b"\x01\x02\x03", 0x010203, 3)
    common(Int24ul, b"\x01\x02\x03", 0x030201, 3)
    common(Int24sb, b"\xff\xff\xff", -1, 3)
    common(Int24sl, b"\xff\xff\xff", -1, 3)

def test_floats():
    common(Half, b"\x00\x00", 0., 2)
    common(Half, b"\x35\x55", 0.333251953125, 2)
    common(Single, b"\x00\x00\x00\x00", 0., 4)
    common(Single, b"?\x99\x99\x9a", 1.2000000476837158, 4)
    common(Double, b"\x00\x00\x00\x00\x00\x00\x00\x00", 0., 8)
    common(Double, b"?\xf3333333", 1.2, 8)

def test_formatfield():
    d = FormatField("<","L")
    common(d, b"\x01\x02\x03\x04", 0x04030201, 4)
    assert raises(d.parse, b"") == StreamError
    assert raises(d.parse, b"\x01\x02") == StreamError
    assert raises(d.build, 2**100) == FormatFieldError
    assert raises(d.build, 1e9999) == FormatFieldError
    assert raises(d.build, "string not int") == FormatFieldError

def test_formatfield_ints_randomized():
    for endianess,dtype in itertools.product("<>=","bhlqBHLQ"):
        d = FormatField(endianess, dtype)
        for i in range(100):
            obj = random.randrange(0, 256**d.sizeof()//2)
            assert d.parse(d.build(obj)) == obj
            data = os.urandom(d.sizeof())
            assert d.build(d.parse(data)) == data

def test_formatfield_floats_randomized():
    # there is a roundoff error because Python float is a C double
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

def test_formatfield_bool_issue_901():
    d = FormatField(">","?")
    assert d.parse(b"\x01") == True
    assert d.parse(b"\xff") == True
    assert d.parse(b"\x00") == False
    assert d.build(True) == b"\x01"
    assert d.build(False) == b"\x00"
    assert d.sizeof() == 1

def test_bytesinteger():
    d = BytesInteger(0)
    common(d, b"", 0, 0)
    d = BytesInteger(4, signed=True, swapped=False)
    common(d, b"\x01\x02\x03\x04", 0x01020304, 4)
    common(d, b"\xff\xff\xff\xff", -1, 4)
    d = BytesInteger(4, signed=False, swapped=this.swapped)
    common(d, b"\x01\x02\x03\x04", 0x01020304, 4, swapped=False)
    common(d, b"\x04\x03\x02\x01", 0x01020304, 4, swapped=True)
    assert raises(BytesInteger(-1).parse, b"") == IntegerError
    assert raises(BytesInteger(-1).build, 0) == IntegerError
    assert raises(BytesInteger(8).build, None) == IntegerError
    assert raises(BytesInteger(8, signed=False).build, -1) == IntegerError
    assert raises(BytesInteger(8, True).build,  -2**64) == IntegerError
    assert raises(BytesInteger(8, True).build,   2**64) == IntegerError
    assert raises(BytesInteger(8, False).build, -2**64) == IntegerError
    assert raises(BytesInteger(8, False).build,  2**64) == IntegerError
    assert raises(BytesInteger(this.missing).sizeof) == SizeofError

def test_bitsinteger():
    d = BitsInteger(0)
    common(d, b"", 0, 0)
    d = BitsInteger(8)
    common(d, b"\x01\x01\x01\x01\x01\x01\x01\x01", 255, 8)
    d = BitsInteger(8, signed=True)
    common(d, b"\x01\x01\x01\x01\x01\x01\x01\x01", -1, 8)
    d = BitsInteger(16, swapped=True)
    common(d, b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01", 0xff00, 16)
    d = BitsInteger(16, swapped=this.swapped)
    common(d, b"\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00", 0xff00, 16, swapped=False)
    common(d, b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01", 0xff00, 16, swapped=True)
    assert raises(BitsInteger(-1).parse, b"") == IntegerError
    assert raises(BitsInteger(-1).build, 0) == IntegerError
    assert raises(BitsInteger(5, swapped=True).parse, bytes(5)) == IntegerError
    assert raises(BitsInteger(5, swapped=True).build, 0) == IntegerError
    assert raises(BitsInteger(8).build, None) == IntegerError
    assert raises(BitsInteger(8, signed=False).build, -1) == IntegerError
    assert raises(BitsInteger(8, True).build,  -2**64) == IntegerError
    assert raises(BitsInteger(8, True).build,   2**64) == IntegerError
    assert raises(BitsInteger(8, False).build, -2**64) == IntegerError
    assert raises(BitsInteger(8, False).build,  2**64) == IntegerError
    assert raises(BitsInteger(this.missing).sizeof) == SizeofError

def test_varint():
    d = VarInt
    common(d, b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x10", 2**123, SizeofError)
    for n in [0,1,5,100,255,256,65535,65536,2**32,2**100]:
        assert d.parse(d.build(n)) == n
    for n in range(0, 127):
        common(d, int2byte(n), n, SizeofError)
    assert raises(d.parse, b"") == StreamError
    assert raises(d.build, -1) == IntegerError
    assert raises(d.build, None) == IntegerError
    assert raises(d.sizeof) == SizeofError

def test_varint_issue_705():
    d = Struct('namelen' / VarInt, 'name' / Bytes(this.namelen))
    d.build(Container(namelen = 400, name = bytes(400)))
    d = Struct('namelen' / VarInt, Check(this.namelen == 400))
    d.build(dict(namelen=400))

def test_zigzag():
    d = ZigZag
    common(d, b"\x00", 0)
    common(d, b"\x05", -3)
    common(d, b"\x06", 3)
    for n in [0,1,5,100,255,256,65535,65536,2**32,2**100]:
        assert d.parse(d.build(n)) == n
    for n in range(0, 63):
        common(d, int2byte(n*2), n, SizeofError)
    assert raises(d.parse, b"") == StreamError
    assert raises(d.build, None) == IntegerError
    assert raises(d.sizeof) == SizeofError

def test_zigzag_regression():
    d = ZigZag
    assert isinstance(d.parse(b"\x05"), integertypes)
    assert isinstance(d.parse(b"\x06"), integertypes)
    d = Struct('namelen' / ZigZag, Check(this.namelen == 400))
    d.build(dict(namelen=400))

def test_paddedstring():
    common(PaddedString(10, "utf8"), b"hello\x00\x00\x00\x00\x00", u"hello", 10)

    d = PaddedString(100, "ascii")
    assert d.parse(b"X"*100) == u"X"*100
    assert d.build(u"X"*100) == b"X"*100
    assert raises(d.build, u"X"*200) == PaddingError

    for e,us in [("utf8",1),("utf16",2),("utf_16_le",2),("utf32",4),("utf_32_le",4)]:
        s = u"Афон"
        data = (s.encode(e)+bytes(100))[:100]
        common(PaddedString(100, e), data, s, 100)
        s = u""
        data = bytes(100)
        common(PaddedString(100, e), data, s, 100)

    for e in ["ascii","utf8","utf16","utf-16-le","utf32","utf-32-le"]:
        PaddedString(10, e).sizeof() == 10
        PaddedString(this.n, e).sizeof(n=10) == 10

def test_pascalstring():
    for e,us in [("utf8",1),("utf16",2),("utf_16_le",2),("utf32",4),("utf_32_le",4)]:
        for sc in [Byte, Int16ub, Int16ul, VarInt]:
            s = u"Афон"
            data = sc.build(len(s.encode(e))) + s.encode(e)
            common(PascalString(sc, e), data, s)
            common(PascalString(sc, e), sc.build(0), u"")

    for e in ["utf8","utf16","utf-16-le","utf32","utf-32-le","ascii"]:
        raises(PascalString(Byte, e).sizeof) == SizeofError
        raises(PascalString(VarInt, e).sizeof) == SizeofError

def test_cstring():
    for e,us in [("utf8",1),("utf16",2),("utf_16_le",2),("utf32",4),("utf_32_le",4)]:
        s = u"Афон"
        common(CString(e), s.encode(e)+bytes(us), s)
        common(CString(e), bytes(us), u"")

    CString("utf8").build(s) == b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd'+b"\x00"
    CString("utf16").build(s) == b'\xff\xfe\x10\x04D\x04>\x04=\x04'+b"\x00\x00"
    CString("utf32").build(s) == b'\xff\xfe\x00\x00\x10\x04\x00\x00D\x04\x00\x00>\x04\x00\x00=\x04\x00\x00'+b"\x00\x00\x00\x00"

    for e in ["utf8","utf16","utf-16-le","utf32","utf-32-le","ascii"]:
        raises(CString(e).sizeof) == SizeofError

def test_greedystring():
    for e,us in [("utf8",1),("utf16",2),("utf_16_le",2),("utf32",4),("utf_32_le",4)]:
        s = u"Афон"
        common(GreedyString(e), s.encode(e), s)
        common(GreedyString(e), b"", u"")

    for e in ["utf8","utf16","utf-16-le","utf32","utf-32-le","ascii"]:
        raises(GreedyString(e).sizeof) == SizeofError

def test_string_encodings():
    # checks that "-" is replaced with "_"
    common(GreedyString("utf-8"), b"", u"")
    common(GreedyString("utf-8"), b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd', u"Афон")

def test_flag():
    d = Flag
    common(d, b"\x00", False, 1)
    common(d, b"\x01", True, 1)
    d.parse(b"\xff") == True

def test_enum():
    d = Enum(Byte, one=1, two=2, four=4, eight=8)
    common(d, b"\x01", "one", 1)
    common(d, b"\xff", 255, 1)
    assert d.parse(b"\x01") == d.one
    assert d.parse(b"\x01") == "one"
    assert int(d.parse(b"\x01")) == 1
    assert d.parse(b"\xff") == 255
    assert int(d.parse(b"\xff")) == 255
    assert d.build(8) == b'\x08'
    assert d.build(255) == b"\xff"
    assert d.build(d.eight) == b'\x08'
    assert d.one == "one"
    assert int(d.one) == 1
    assert raises(d.build, "unknown") == MappingError
    assert raises(lambda: d.missing) == AttributeError

def test_enum_enum34():
    import enum
    class E(enum.IntEnum):
        a = 1
    class F(enum.IntEnum):
        b = 2
    d = Enum(Byte, E, F)
    common(d, b"\x01", "a", 1)
    common(d, b"\x02", "b", 1)

def test_enum_enum36():
    import enum
    class E(enum.IntEnum):
        a = 1
    class F(enum.IntFlag):
        b = 2
    d = Enum(Byte, E, F)
    common(d, b"\x01", "a", 1)
    common(d, b"\x02", "b", 1)

def test_enum_issue_298():
    d = Struct(
        "ctrl" / Enum(Byte,
            NAK = 0x15,
            STX = 0x02,
        ),
        Probe(),
        "optional" / If(lambda this: this.ctrl == "NAK", Byte),
    )
    common(d, b"\x15\xff", Container(ctrl='NAK', optional=255))
    common(d, b"\x02", Container(ctrl='STX', optional=None))

    # FlagsEnum is not affected by same bug
    d = Struct(
        "flags" / FlagsEnum(Byte, a=1),
        Check(lambda ctx: ctx.flags == Container(_flagsenum=True, a=1)),
    )
    common(d, b"\x01", dict(flags=Container(_flagsenum=True, a=True)), 1)

    # Flag is not affected by same bug
    d = Struct(
        "flag" / Flag,
        Check(lambda ctx: ctx.flag == True),
    )
    common(d, b"\x01", dict(flag=True), 1)

def test_enum_issue_677():
    d = Enum(Byte, one=1)
    common(d, b"\xff", 255, 1)
    common(d, b"\x01", EnumIntegerString.new(1, "one"), 1)
    assert isinstance(d.parse(b"\x01"), EnumIntegerString)
    d = Enum(Byte, one=1).compile()
    common(d, b"\xff", 255, 1)
    common(d, b"\x01", EnumIntegerString.new(1, "one"), 1)
    assert isinstance(d.parse(b"\x01"), EnumIntegerString)

    d = Struct("e" / Enum(Byte, one=1))
    assert str(d.parse(b"\x01")) == 'Container: \n    e = (enum) one 1'
    assert str(d.parse(b"\xff")) == 'Container: \n    e = (enum) (unknown) 255'
    d = Struct("e" / Enum(Byte, one=1)).compile()
    assert str(d.parse(b"\x01")) == 'Container: \n    e = (enum) one 1'
    assert str(d.parse(b"\xff")) == 'Container: \n    e = (enum) (unknown) 255'

def test_flagsenum():
    d = FlagsEnum(Byte, one=1, two=2, four=4, eight=8)
    common(d, b"\x03", Container(_flagsenum=True, one=True, two=True, four=False, eight=False), 1)
    assert d.build({}) == b'\x00'
    assert d.build(dict(one=True,two=True)) == b'\x03'
    assert d.build(8) == b'\x08'
    assert d.build(1|2) == b'\x03'
    assert d.build(255) == b"\xff"
    assert d.build(d.eight) == b'\x08'
    assert d.build(d.one|d.two) == b'\x03'
    assert raises(d.build, dict(unknown=True)) == MappingError
    assert raises(d.build, "unknown") == MappingError
    assert d.one == "one"
    assert d.one|d.two == "one|two"
    assert raises(lambda: d.missing) == AttributeError

def test_flagsenum_enum34():
    import enum
    class E(enum.IntEnum):
        a = 1
    class F(enum.IntEnum):
        b = 2
    d = FlagsEnum(Byte, E, F)
    common(d, b"\x01", Container(_flagsenum=True, a=True,b=False), 1)
    common(d, b"\x02", Container(_flagsenum=True, a=False,b=True), 1)
    common(d, b"\x03", Container(_flagsenum=True, a=True,b=True), 1)

def test_flagsenum_enum36():
    import enum
    class E(enum.IntEnum):
        a = 1
    class F(enum.IntFlag):
        b = 2
    d = FlagsEnum(Byte, E, F)
    common(d, b"\x01", Container(_flagsenum=True, a=True,b=False), 1)
    common(d, b"\x02", Container(_flagsenum=True, a=False,b=True), 1)
    common(d, b"\x03", Container(_flagsenum=True, a=True,b=True), 1)

def test_mapping():
    x = object
    d = Mapping(Byte, {x:0})
    common(d, b"\x00", x, 1)

def test_struct():
    common(Struct(), b"", Container(), 0)
    common(Struct("a"/Int16ub, "b"/Int8ub), b"\x00\x01\x02", Container(a=1,b=2), 3)
    common(Struct("a"/Struct("b"/Byte)), b"\x01", Container(a=Container(b=1)), 1)
    common(Struct(Const(b"\x00"), Padding(1), Pass, Terminated), bytes(2), {}, SizeofError)
    assert raises(Struct("missingkey"/Byte).build, {}) == KeyError
    assert raises(Struct(Bytes(this.missing)).sizeof) == SizeofError
    d = Struct(Computed(7), Const(b"JPEG"), Pass, Terminated)
    assert d.build(None) == d.build({})

def test_struct_nested():
    d = Struct("a"/Byte, "b"/Int16ub, "inner"/Struct("c"/Byte, "d"/Byte))
    common(d, b"\x01\x00\x02\x03\x04", Container(a=1,b=2,inner=Container(c=3,d=4)), 5)

def test_struct_kwctor():
    d = Struct(a=Byte, b=Byte, c=Byte, d=Byte)
    common(d, b"\x01\x02\x03\x04", Container(a=1,b=2,c=3,d=4), 4)

def test_struct_proper_context():
    # adjusted to support new embedding semantics
    d = Struct(
        "x"/Byte,
        "inner"/Struct(
            "y"/Byte,
            "a"/Computed(this._.x+1),
            "b"/Computed(this.y+2),
        ),
        "c"/Computed(this.x+3),
        "d"/Computed(this.inner.y+4),
    )
    assert d.parse(b"\x01\x0f") == Container(x=1, inner=Container(y=15, a=2, b=17), c=4, d=19)

def test_struct_sizeof_context_nesting():
    d = Struct(
        "a" / Computed(1),
        "inner" / Struct(
            "b" / Computed(2),
            Check(this._.a == 1),
            Check(this.b == 2),
        ),
        Check(this.a == 1),
        Check(this.inner.b == 2),
    )
    d.sizeof()

def test_sequence():
    common(Sequence(), b"", [], 0)
    common(Sequence(Int8ub, Int16ub), b"\x01\x00\x02", [1,2], 3)
    common(Int8ub >> Int16ub, b"\x01\x00\x02", [1,2], 3)
    d = Sequence(Computed(7), Const(b"JPEG"), Pass, Terminated)
    assert d.build(None) == d.build([None,None,None,None])

def test_sequence_nested():
    d = Sequence(Int8ub, Int16ub, Sequence(Int8ub, Int8ub))
    common(d, b"\x01\x00\x02\x03\x04", [1,2,[3,4]], 5)

def test_array():
    common(Byte[0], b"", [], 0)
    common(Byte[4], b"1234", [49,50,51,52], 4)

    d = Array(3, Byte)
    common(d, b"\x01\x02\x03", [1,2,3], 3)
    assert d.parse(b"\x01\x02\x03additionalgarbage") == [1,2,3]
    assert raises(d.parse, b"") == StreamError
    assert raises(d.build, [1,2]) == RangeError
    assert raises(d.build, [1,2,3,4,5,6,7,8]) == RangeError

    d = Array(this.n, Byte)
    common(d, b"\x01\x02\x03", [1,2,3], 3, n=3)
    assert d.parse(b"\x01\x02\x03", n=3) == [1,2,3]
    assert d.parse(b"\x01\x02\x03additionalgarbage", n=3) == [1,2,3]
    assert raises(d.parse, b"", n=3) == StreamError
    assert raises(d.build, [1,2], n=3) == RangeError
    assert raises(d.build, [1,2,3,4,5,6,7,8], n=3) == RangeError
    assert raises(d.sizeof) == SizeofError
    assert raises(d.sizeof, n=3) == 3

    d = Array(3, Byte, discard=True)
    assert d.parse(b"\x01\x02\x03") == []
    assert d.build([1,2,3]) == b"\x01\x02\x03"
    assert d.sizeof() == 3

@xfail(ONWINDOWS, reason="/dev/zero not available on Windows")
def test_array_nontellable():
    assert Array(5, Byte).parse_stream(devzero) == [0,0,0,0,0]

def test_greedyrange():
    d = GreedyRange(Byte)
    common(d, b"", [], SizeofError)
    common(d, b"\x01\x02", [1,2], SizeofError)

    d = GreedyRange(Byte, discard=False)
    assert d.parse(b"\x01\x02") == [1,2]
    assert d.build([1,2]) == b"\x01\x02"

    d = GreedyRange(Byte, discard=True)
    assert d.parse(b"\x01\x02") == []
    assert d.build([1,2]) == b"\x01\x02"

def test_repeatuntil():
    d = RepeatUntil(obj_ == 9, Byte)
    common(d, b"\x02\x03\x09", [2,3,9], SizeofError)
    assert d.parse(b"\x02\x03\x09additionalgarbage") == [2,3,9]
    assert raises(d.parse, b"\x02\x03\x08") == StreamError
    assert raises(d.build, [2,3,8]) == RepeatError

    d = RepeatUntil(lambda x,lst,ctx: lst[-2:] == [0,0], Byte)
    # d = RepeatUntil(lst_[-2:] == [0,0], Byte)
    assert d.parse(b"\x01\x00\x00\xff") == [1,0,0]
    assert d.build([1,0,0,4]) == b"\x01\x00\x00"
    d = RepeatUntil(True, Byte)
    assert d.parse(b"\x00") == [0]
    assert d.build([0]) == b"\x00"

    d = RepeatUntil(obj_ == 9, Byte, discard=True)
    assert d.parse(b"\x02\x03\x09additionalgarbage") == []
    assert raises(d.parse, b"\x02\x03\x08") == StreamError
    assert d.build([2,3,8,9]) == b"\x02\x03\x08\x09"
    assert raises(d.build, [2,3,8]) == RepeatError

def test_const():
    common(Const(b"MZ"), b"MZ", b"MZ", 2)
    common(Const(b"MZ", Bytes(2)), b"MZ", b"MZ", 2)
    common(Const(255, Int32ul), b"\xff\x00\x00\x00", 255, 4)
    assert raises(Const(b"MZ").parse, b"???") == ConstError
    assert raises(Const(b"MZ").build, b"???") == ConstError
    assert raises(Const(255, Int32ul).parse, b"\x00\x00\x00\x00") == ConstError
    assert Struct(Const(b"MZ")).build({}) == b"MZ"
    # non-prefixed string literals are unicode on Python 3
    assert raises(lambda: Const("no prefix string")) == StringError

def test_computed():
    common(Computed(255), b"", 255, 0)
    common(Computed(lambda ctx: 255), b"", 255, 0)
    assert Computed(255).build(None) == b""
    assert Struct(Computed(255)).build({}) == b""
    assert raises(Computed(this.missing).parse, b"") == KeyError
    assert raises(Computed(this["missing"]).parse, b"") == KeyError

@xfail(reason="_index fails during parsing or building, not during compilation")
def test_index():
    d = Array(3, Bytes(this._index+1))
    common(d, b"abbccc", [b"a", b"bb", b"ccc"])
    d = GreedyRange(Bytes(this._index+1))
    common(d, b"abbccc", [b"a", b"bb", b"ccc"])
    d = RepeatUntil(lambda o,l,ctx: ctx._index == 2, Bytes(this._index+1))
    common(d, b"abbccc", [b"a", b"bb", b"ccc"])

    d = Array(3, Struct("i" / Index))
    common(d, b"", [Container(i=0),Container(i=1),Container(i=2)], 0)
    d = GreedyRange(Struct("i" / Index, "d" / Bytes(this.i+1)))
    common(d, b"abbccc", [Container(i=0,d=b"a"),Container(i=1,d=b"bb"),Container(i=2,d=b"ccc")])
    d = RepeatUntil(lambda o,l,ctx: ctx._index == 2, Index)
    common(d, b"", [0,1,2])

def test_rebuild():
    d = Struct(
        "count" / Rebuild(Byte, len_(this.items)),
        "items"/Byte[this.count],
    )
    assert d.parse(b"\x02ab") == Container(count=2, items=[97,98])
    assert d.build(dict(count=None,items=[255])) == b"\x01\xff"
    assert d.build(dict(count=-1,items=[255])) == b"\x01\xff"
    assert d.build(dict(items=[255])) == b"\x01\xff"

def test_rebuild_issue_664():
    d = Struct(
        "bytes" / Bytes(1),
        Check(this.bytes == b"\x00"),
        "bytesinteger" / BytesInteger(4),
        Check(this.bytesinteger == 255),
        "pascalstring" / PascalString(Byte, "utf8"),
        Check(this.pascalstring == u"text"),
        "enum" / Enum(Byte, label=255),
        Check(this.enum == "label"),
        "flagsenum" / FlagsEnum(Byte, label=255),
        Check(lambda this: this.flagsenum == Container(label=True)),
        "upfield" / Computed(200),
        "nestedstruct" / Struct(
            "nestedfield" / Computed(255),
            Check(this._.upfield == 200),
            Check(this.nestedfield == 255),
        ),
        Check(this.upfield == 200),
        Check(this.nestedstruct.nestedfield == 255),
        "sequence" / Sequence(Computed(1), Computed(2), Computed(3), Computed(4)),
        Check(this.sequence == [1,2,3,4]),
        "array" / Array(4, Byte),
        Check(this.array == [1,2,3,4]),
        "greedyrange" / GreedyRange(Byte),
        Check(this.greedyrange == [1,2,3,4]),
        "repeatuntil" / RepeatUntil(obj_ == 4, Byte),
        Check(this.repeatuntil == [1,2,3,4]),
        # Timestamp
        # Union
        # IfThenElse
    )
    obj = Container(
        bytes = 0,
        bytesinteger = 255,
        pascalstring = u"text",
        enum = "label",
        flagsenum = dict(label=True),
        # nestedstruct = dict(),
        # sequence = [1,2,3,4],
        array = [1,2,3,4],
        greedyrange = [1,2,3,4],
        repeatuntil = [1,2,3,4],
    )
    d.build(obj)

def test_default():
    d = Default(Byte, 0)
    common(d, b"\xff", 255, 1)
    d.build(None) == b"\x00"

def test_check():
    common(Check(True), b"", None, 0)
    common(Check(this.x == 255), b"", None, 0, x=255)
    common(Check(len_(this.a) == 3), b"", None, 0, a=[1,2,3])
    assert raises(Check(False).parse, b"") == CheckError
    assert raises(Check(this.x == 255).parse, b"", x=0) == CheckError
    assert raises(Check(len_(this.a) == 3).parse, b"", a=[]) == CheckError

def test_error():
    assert raises(Error.parse, b"") == ExplicitError
    assert raises(Error.build, None) == ExplicitError
    assert ("x"/Int8sb >> IfThenElse(this.x > 0, Int8sb, Error)).parse(b"\x01\x05") == [1,5]
    assert raises(("x"/Int8sb >> IfThenElse(this.x > 0, Int8sb, Error)).parse, b"\xff\x05") == ExplicitError

def test_focusedseq():
    common(FocusedSeq("num", Const(b"MZ"), "num"/Byte, Terminated), b"MZ\xff", 255, SizeofError)
    common(FocusedSeq(this._.s, Const(b"MZ"), "num"/Byte, Terminated), b"MZ\xff", 255, SizeofError, s="num")

    d = FocusedSeq("missing", Pass)
    assert raises(d.parse, b"") == UnboundLocalError
    assert raises(d.build, {}) == UnboundLocalError
    assert raises(d.sizeof) == 0
    d = FocusedSeq(this.missing, Pass)
    assert raises(d.parse, b"") == KeyError
    assert raises(d.build, {}) == KeyError
    assert raises(d.sizeof) == 0

def test_pickled():
    import pickle
    obj = [(), 1, 2.3, {}, [], bytes(1), ""]
    data = pickle.dumps(obj)
    common(Pickled, data, obj)

def test_numpy():
    import numpy
    obj = numpy.array([1,2,3], dtype=numpy.int64)
    assert numpy.array_equal(Numpy.parse(Numpy.build(obj)), obj)

@xfail(reason="docs stated that it throws StreamError, not true at all")
def test_numpy_error():
    import numpy, io
    numpy.load(io.BytesIO(b""))

def test_namedtuple():
    coord = collections.namedtuple("coord", "x y z")
    d = NamedTuple("coord", "x y z", Array(3, Byte))
    common(d, b"123", coord(49,50,51), 3)
    d = NamedTuple("coord", "x y z", GreedyRange(Byte))
    common(d, b"123", coord(49,50,51), SizeofError)
    d = NamedTuple("coord", "x y z", Struct("x"/Byte, "y"/Byte, "z"/Byte))
    common(d, b"123", coord(49,50,51), 3)
    d = NamedTuple("coord", "x y z", Sequence(Byte, Byte, Byte))
    common(d, b"123", coord(49,50,51), 3)

    assert raises(lambda: NamedTuple("coord", "x y z", BitStruct("x"/Byte, "y"/Byte, "z"/Byte))) == NamedTupleError

def test_timestamp():
    import arrow
    d = Timestamp(Int64ub, 1, 1970)
    common(d, b'\x00\x00\x00\x00ZIz\x00', arrow.Arrow(2018,1,1), 8)
    d = Timestamp(Int64ub, 1, 1904)
    common(d, b'\x00\x00\x00\x00\xd6o*\x80', arrow.Arrow(2018,1,1), 8)
    d = Timestamp(Int64ub, 10**-7, 1600)
    common(d, b'\x01\xd4\xa2.\x1a\xa8\x00\x00', arrow.Arrow(2018,1,1), 8)
    d = Timestamp(Int32ub, "msdos", "msdos")
    common(d, b'H9\x8c"', arrow.Arrow(2016,1,25,17,33,4), 4)

def test_hex():
    d = Hex(Int32ub)
    common(d, b"\x00\x00\x01\x02", 0x0102, 4)
    obj = d.parse(b"\x00\x00\x01\x02")
    assert str(obj) == "0x00000102"
    assert str(obj) == "0x00000102"

    d = Hex(GreedyBytes)
    common(d, b"\x00\x00\x01\x02", b"\x00\x00\x01\x02")
    common(d, b"", b"")
    obj = d.parse(b"\x00\x00\x01\x02")
    assert str(obj) == "unhexlify('00000102')"
    assert str(obj) == "unhexlify('00000102')"

    d = Hex(RawCopy(Int32ub))
    common(d, b"\x00\x00\x01\x02", dict(data=b"\x00\x00\x01\x02", value=0x0102, offset1=0, offset2=4, length=4), 4)
    obj = d.parse(b"\x00\x00\x01\x02")
    assert str(obj) == "unhexlify('00000102')"
    assert str(obj) == "unhexlify('00000102')"

def test_hexdump():
    d = HexDump(GreedyBytes)
    common(d, b"abcdef", b"abcdef")
    common(d, b"", b"")
    obj = d.parse(b"\x00\x00\x01\x02")
    repr = \
'''hexundump("""
0000   00 00 01 02                                       ....
""")
'''
    pass
    assert str(obj) == repr
    assert str(obj) == repr

    d = HexDump(RawCopy(Int32ub))
    common(d, b"\x00\x00\x01\x02", dict(data=b"\x00\x00\x01\x02", value=0x0102, offset1=0, offset2=4, length=4), 4)
    obj = d.parse(b"\x00\x00\x01\x02")
    repr = \
'''hexundump("""
0000   00 00 01 02                                       ....
""")
'''
    assert str(obj) == repr
    assert str(obj) == repr

def test_hexdump_regression_issue_188():
    # Hex HexDump were not inheriting subcon flags
    d = Struct(Hex(Const(b"MZ")))
    assert d.parse(b"MZ") == Container()
    assert d.build(dict()) == b"MZ"
    d = Struct(HexDump(Const(b"MZ")))
    assert d.parse(b"MZ") == Container()
    assert d.build(dict()) == b"MZ"

def test_union():
    d = Union(None, "a"/Bytes(2), "b"/Int16ub)
    assert d.parse(b"\x01\x02") == Container(a=b"\x01\x02", b=0x0102)
    assert raises(Union(123, Pass).parse, b"") == KeyError
    assert raises(Union("missing", Pass).parse, b"") == KeyError
    assert d.build(dict(a=b"zz"))  == b"zz"
    assert d.build(dict(b=0x0102)) == b"\x01\x02"
    assert raises(d.build, {}) == UnionError

    d = Union(None, "a"/Bytes(2), "b"/Int16ub, Pass)
    assert d.build({}) == b""

    # build skips parsefrom, invalid or not
    assert raises(Union(123, Pass).build, {}) == b""
    assert raises(Union("missing", Pass).build, {}) == b""

    assert raises(Union(None, Byte).sizeof) == SizeofError
    assert raises(Union(None, VarInt).sizeof) == SizeofError
    assert raises(Union(0, Byte, VarInt).sizeof) == SizeofError
    assert raises(Union(1, Byte, VarInt).sizeof) == SizeofError
    assert raises(Union(123, Pass).sizeof) == SizeofError
    assert raises(Union("missing", Pass).sizeof) == SizeofError
    assert raises(Union(this.missing, Pass).sizeof) == SizeofError

    # regression check, so first subcon is not parsefrom by accident
    assert raises(Union, Byte, VarInt) == UnionError

def test_union_kwctor():
    d = Union(None, a=Int8ub, b=Int16ub, c=Int32ub)
    assert d.parse(b"\x01\x02\x03\x04") == Container(a=0x01,b=0x0102,c=0x01020304)
    assert d.build(Container(c=0x01020304)) == b"\x01\x02\x03\x04"

def test_union_issue_348():
    d = Union(None,
        Int8=Prefixed(Int16ub, GreedyRange(Int8ub)),
        Int16=Prefixed(Int16ub, GreedyRange(Int16ub)),
        Int32=Prefixed(Int16ub, GreedyRange(Int32ub)),
    )
    assert d.parse(b'\x00\x04\x11\x22\x33\x44') == {'Int16': [4386, 13124], 'Int32': [287454020], 'Int8': [17, 34, 51, 68]}
    assert d.build(dict(Int16=[4386, 13124])) == b'\x00\x04\x11\x22\x33\x44'
    assert d.build(dict(Int32=[287454020])) == b'\x00\x04\x11\x22\x33\x44'

def test_select():
    d = Select(Int32ub, Int16ub, Int8ub)
    common(d, b"\x00\x00\x00\x07", 7)
    assert raises(Select(Int32ub, Int16ub).parse, b"") == SelectError
    assert raises(Select(Byte).sizeof) == SizeofError

def test_select_kwctor():
    d = Select(a=Int8ub, b=Int16ub, c=Int32ub)
    assert d.parse(b"\x01\x02\x03\x04") == 0x01
    assert d.build(0x01020304) == b"\x01\x02\x03\x04"

def test_optional():
    d = Optional(Int32ul)
    assert d.parse(b"\x01\x00\x00\x00") == 1
    assert d.build(1) == b"\x01\x00\x00\x00"
    assert d.parse(b"???") == None
    assert d.parse(b"") == None
    assert d.build(None) == b""
    assert raises(d.sizeof) == SizeofError

def test_optional_in_struct_issue_747():
    d = Struct("field" / Optional(Int32ul))
    assert d.parse(b"\x01\x00\x00\x00") == {"field": 1}
    assert d.build({"field": 1}) == b"\x01\x00\x00\x00"
    assert d.parse(b"???") == {"field": None}
    assert d.build({"field": None}) == b""
    assert d.parse(b"") == {"field": None}
    assert raises(d.sizeof) == SizeofError

def test_optional_in_bit_struct_issue_747():
    d = BitStruct("field" / Optional(Octet))
    assert d.parse(b"\x01") == {"field": 1}
    assert d.build({"field": 1}) == b"\x01"
    assert d.parse(b"???") == {"field": ord("?")}
    assert d.build({"field": None}) == b""
    assert d.parse(b"") == {"field": None}
    assert raises(d.sizeof) == SizeofError

def test_select_buildfromnone_issue_747():
    d = Struct("select" / Select(Int32ub, Default(Bytes(3), b"abc")))
    assert d.parse(b"def") == dict(select=b"def")
    assert d.parse(b"\x01\x02\x03\x04") == dict(select=0x01020304)
    assert d.build(dict(select=b"def")) == b"def"
    assert d.build(dict(select=0xbeefcace)) == b"\xbe\xef\xca\xce"
    assert d.build(dict()) == b"abc"

    d = Struct("opt" / Optional(Byte))
    assert d.build(dict(opt=1)) == b"\x01"
    assert d.build(dict()) == b""

def test_if():
    common(If(True,  Byte), b"\x01", 1, 1)
    common(If(False, Byte), b"", None, 0)

def test_ifthenelse():
    common(IfThenElse(True,  Int8ub, Int16ub), b"\x01", 1, 1)
    common(IfThenElse(False, Int8ub, Int16ub), b"\x00\x01", 1, 2)

def test_switch():
    d = Switch(this.x, {1:Int8ub, 2:Int16ub, 4:Int32ub})
    common(d, b"\x01", 0x01, 1, x=1)
    common(d, b"\x01\x02", 0x0102, 2, x=2)
    assert d.parse(b"", x=255) == None
    assert d.build(None, x=255) == b""
    assert raises(d.sizeof) == SizeofError
    assert raises(d.sizeof, x=1) == 1

    d = Switch(this.x, {}, default=Byte)
    common(d, b"\x01", 1, 1, x=255)

def test_switch_issue_357():
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

def test_stopif():
    d = Struct("x"/Byte, StopIf(this.x == 0), "y"/Byte)
    common(d, b"\x00", Container(x=0))
    common(d, b"\x01\x02", Container(x=1,y=2))

    d = Sequence("x"/Byte, StopIf(this.x == 0), "y"/Byte)
    common(d, b"\x01\x02", [1,None,2])

    d = GreedyRange(FocusedSeq("x", "x"/Byte, StopIf(this.x == 0)))
    assert d.parse(b"\x01\x00?????") == [1]
    assert d.build([]) == b""
    assert d.build([0]) == b"\x00"
    assert d.build([1]) == b"\x01"
    assert d.build([1,0,2]) == b"\x01\x00"

def test_padding():
    common(Padding(4), b"\x00\x00\x00\x00", None, 4)
    assert raises(Padding, 4, pattern=b"?????") == PaddingError
    assert raises(Padding, 4, pattern=u"?") == PaddingError

def test_padded():
    common(Padded(4, Byte), b"\x01\x00\x00\x00", 1, 4)
    assert raises(Padded, 4, Byte, pattern=b"?????") == PaddingError
    assert raises(Padded, 4, Byte, pattern=u"?") == PaddingError
    assert Padded(4, VarInt).sizeof() == 4
    assert Padded(4, Byte[this.missing]).sizeof() == 4

def test_aligned():
    common(Aligned(4, Byte), b"\x01\x00\x00\x00", 1, 4)
    common(Struct("a"/Aligned(4, Byte), "b"/Byte), b"\x01\x00\x00\x00\x02", Container(a=1, b=2), 5)
    assert Aligned(4, Int8ub).build(1) == b"\x01\x00\x00\x00"
    assert Aligned(4, Int16ub).build(1) == b"\x00\x01\x00\x00"
    assert Aligned(4, Int32ub).build(1) == b"\x00\x00\x00\x01"
    assert Aligned(4, Int64ub).build(1) == b"\x00\x00\x00\x00\x00\x00\x00\x01"
    d = Aligned(this.m, Byte)
    common(d, b"\xff\x00", 255, 2, m=2)
    assert raises(d.sizeof) == SizeofError
    assert raises(d.sizeof, m=2) == 2

def test_alignedstruct():
    d = AlignedStruct(4, "a"/Int8ub, "b"/Int16ub)
    common(d, b"\x01\x00\x00\x00\x00\x05\x00\x00", Container(a=1, b=5), 8)

def test_bitstruct():
    d = BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "d"/BitsInteger(5))
    common(d, b"\xe1\x1f", Container(a=7, b=False, c=8, d=31), 2)
    d = BitStruct("a"/BitsInteger(3), "b"/Flag, Padding(3), "c"/Nibble, "sub"/Struct("d"/Nibble, "e"/Bit))
    common(d, b"\xe1\x1f", Container(a=7, b=False, c=8, sub=Container(d=15, e=1)), 2)

def test_pointer():
    common(Pointer(2,             Byte), b"\x00\x00\x07", 7, 0)
    common(Pointer(lambda ctx: 2, Byte), b"\x00\x00\x07", 7, 0)

    d = Struct(
        'inner' / Struct(),
        'x' / Pointer(0, Byte, stream=this.inner._io),
    )
    d.parse(bytes(20)) == 0

def test_peek():
    d = Peek(Int8ub)
    assert d.parse(b"\x01") == 1
    assert d.parse(b"") == None
    assert d.build(1) == b""
    assert d.build(None) == b""
    assert d.sizeof() == 0
    d = Peek(VarInt)
    assert d.sizeof() == 0

    d = Struct("a"/Peek(Int8ub), "b"/Int16ub)
    common(d, b"\x01\x02", Container(a=0x01, b=0x0102), 2)
    d = Struct(Peek("a"/Byte), Peek("b"/Int16ub))
    d.parse(b"\x01\x02") == Container(a=0x01, b=0x0102)
    d.build(Container(a=0x01, b=0x0102)) == b"\x01\x02"
    d.sizeof() == 0

def test_seek():
    d = Seek(5)
    assert d.parse(b"") == 5
    assert d.build(None) == b""
    assert (d >> Byte).parse(b"01234x") == [5,120]
    assert (d >> Byte).build([5,255]) == b"\x00\x00\x00\x00\x00\xff"
    assert (Bytes(10) >> d >> Byte).parse(b"0123456789") == [b"0123456789",5,ord('5')]
    assert (Bytes(10) >> d >> Byte).build([b"0123456789",None,255]) == b"01234\xff6789"
    assert Struct("data"/Bytes(10), d, "addin"/Byte).parse(b"0123456789") == Container(data=b"0123456789", addin=53)
    assert Struct("data"/Bytes(10), d, "addin"/Byte).build(dict(data=b"0123456789",addin=53)) == b"01234\x356789"
    assert (Seek(10,1) >> Seek(-5,1) >> Bytes(1)).parse(b"0123456789") == [10,5,b"5"]
    assert (Seek(10,1) >> Seek(-5,1) >> Bytes(1)).build([None,None,255]) == b"\x00\x00\x00\x00\x00\xff"
    assert raises(d.sizeof) == SizeofError

def test_tell():
    d = Tell
    assert d.parse(b"") == 0
    assert d.build(None) == b""
    assert d.sizeof() == 0
    d = Struct("a"/Tell, "b"/Byte, "c"/Tell)
    assert d.parse(b"\xff") == Container(a=0, b=255, c=1)
    assert d.build(Container(a=0, b=255, c=1)) == b"\xff"
    assert d.build(dict(b=255)) == b"\xff"

def test_pass():
    common(Pass, b"", None, 0)
    common(Struct("empty"/Pass), b"", Container(empty=None), 0)

def test_terminated():
    common(Terminated, b"", None, SizeofError)
    common(Struct(Terminated), b"", Container(), SizeofError)
    common(BitStruct(Terminated), b"", Container(), SizeofError)
    assert raises(Terminated.parse, b"x") == TerminatedError
    assert raises(Struct(Terminated).parse, b"x") == TerminatedError
    assert raises(BitStruct(Terminated).parse, b"x") == TerminatedError

def test_rawcopy():
    d = RawCopy(Byte)
    assert d.parse(b"\xff") == dict(data=b"\xff", value=255, offset1=0, offset2=1, length=1)
    assert d.build(dict(data=b"\xff")) == b"\xff"
    assert d.build(dict(value=255)) == b"\xff"
    assert d.sizeof() == 1
    d = RawCopy(Padding(1))
    assert d.build(None) == b'\x00'

def test_rawcopy_issue_289():
    # When you build from a full dict that has all the keys, the if data kicks in, and replaces the context entry with a subset of a dict it had to begin with.
    d = Struct(
        "raw" / RawCopy(Struct("x"/Byte, "len"/Byte)),
        "array" / Byte[this.raw.value.len],
    )
    print(d.parse(b"\x01\x02\xff\x00"))
    print(d.build(dict(raw=dict(value=dict(x=1, len=2)), array=[0xff, 0x01])))
    print(d.build(d.parse(b"\x01\x02\xff\x00")))
    # this is not buildable, array is not passed and cannot be deduced from raw data
    # print(d.build(dict(raw=dict(data=b"\x01\x02\xff\x00"))))

def test_rawcopy_issue_358():
    # RawCopy overwritten context value with subcon return obj regardless of None
    d = Struct("a"/RawCopy(Byte), "check"/Check(this.a.value == 255))
    assert d.build(dict(a=dict(value=255))) == b"\xff"

def test_rawcopy_issue_888():
    # If you use build_file() on a RawCopy that has only a value defined, then
    # RawCopy._build may also attempt to read from the file, which won't work
    # if build_file opened the file for writing only.
    d = RawCopy(Byte)
    d.build_file(dict(value=0), filename="example_888")

def test_byteswapped():
    d = ByteSwapped(Bytes(5))
    common(d, b"12345", b"54321", 5)
    d = ByteSwapped(Struct("a"/Byte, "b"/Byte))
    common(d, b"\x01\x02", Container(a=2, b=1), 2)

def test_byteswapped_from_issue_70():
    d = ByteSwapped(BitStruct("flag1"/Bit, "flag2"/Bit, Padding(2), "number"/BitsInteger(16), Padding(4)))
    assert d.parse(b'\xd0\xbc\xfa') == Container(flag1=1, flag2=1, number=0xabcd)
    d = BitStruct("flag1"/Bit, "flag2"/Bit, Padding(2), "number"/BitsInteger(16), Padding(4))
    assert d.parse(b'\xfa\xbc\xd1') == Container(flag1=1, flag2=1, number=0xabcd)

def test_bitsswapped():
    d = BitsSwapped(Bytes(2))
    common(d, b"\x0f\x01", b"\xf0\x80", 2)
    d = Bitwise(Bytes(8))
    common(d, b"\xf2", b'\x01\x01\x01\x01\x00\x00\x01\x00', 1)
    d = BitsSwapped(Bitwise(Bytes(8)))
    common(d, b"\xf2", b'\x00\x01\x00\x00\x01\x01\x01\x01', 1)
    d = BitStruct("a"/Nibble, "b"/Nibble)
    common(d, b"\xf1", Container(a=15, b=1), 1)
    d = BitsSwapped(BitStruct("a"/Nibble, "b"/Nibble))
    common(d, b"\xf1", Container(a=8, b=15), 1)

def test_prefixed():
    d = Prefixed(Byte, Int16ul)
    assert d.parse(b"\x02\xff\xff??????") == 65535
    assert d.build(65535) == b"\x02\xff\xff"
    assert d.sizeof() == 3
    d = Prefixed(VarInt, GreedyBytes)
    assert d.parse(b"\x03abc??????") == b"abc"
    assert d.build(b"abc") == b'\x03abc'
    assert raises(d.sizeof) == SizeofError
    d = Prefixed(Byte, Sequence(Peek(Byte), Int16ub, GreedyBytes))
    assert d.parse(b"\x02\x00\xff????????") == [0,255,b'']

    d = Prefixed(Byte, GreedyBytes)
    common(d, b"\x0a"+bytes(10), bytes(10), SizeofError)
    d = Prefixed(Byte, GreedyString("utf-8"))
    common(d, b"\x0a"+bytes(10), u"\x00"*10, SizeofError)

def test_prefixedarray():
    common(PrefixedArray(Byte,Byte), b"\x02\x0a\x0b", [10,11], SizeofError)
    assert PrefixedArray(Byte, Byte).parse(b"\x03\x01\x02\x03") == [1,2,3]
    assert PrefixedArray(Byte, Byte).parse(b"\x00") == []
    assert PrefixedArray(Byte, Byte).build([1,2,3]) == b"\x03\x01\x02\x03"
    assert raises(PrefixedArray(Byte, Byte).parse, b"") == StreamError
    assert raises(PrefixedArray(Byte, Byte).parse, b"\x03\x01") == StreamError
    assert raises(PrefixedArray(Byte, Byte).sizeof) == SizeofError

def test_fixedsized():
    d = FixedSized(10, Byte)
    common(d, b'\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00', 255, 10)
    d = FixedSized(-255, Byte)
    assert raises(d.parse, bytes(10)) == PaddingError
    assert raises(d.build, 0) == PaddingError
    assert raises(d.sizeof) == PaddingError
    d = FixedSized(10, GreedyBytes)
    common(d, bytes(10), bytes(10), 10)
    d = FixedSized(10, GreedyString("utf-8"))
    common(d, bytes(10), u"\x00"*10, 10)

def test_nullterminated():
    d = NullTerminated(Byte)
    common(d, b'\xff\x00', 255, SizeofError)
    d = NullTerminated(GreedyBytes, include=True)
    assert d.parse(b'\xff\x00') == b'\xff\x00'
    d = NullTerminated(GreedyBytes, include=False)
    assert d.parse(b'\xff\x00') == b'\xff'
    d = NullTerminated(GreedyBytes, consume=True) >> GreedyBytes
    assert d.parse(b'\xff\x00') == [b'\xff', b'']
    d = NullTerminated(GreedyBytes, consume=False) >> GreedyBytes
    assert d.parse(b'\xff\x00') == [b'\xff', b'\x00']
    d = NullTerminated(GreedyBytes, require=True)
    assert raises(d.parse, b'\xff') == StreamError
    d = NullTerminated(GreedyBytes, require=False)
    assert d.parse(b'\xff') == b'\xff'
    d = NullTerminated(GreedyBytes)
    common(d, bytes(1), b"", SizeofError)
    d = NullTerminated(GreedyString("utf-8"))
    common(d, bytes(1), u"", SizeofError)
    d = NullTerminated(GreedyBytes, term=bytes(2))
    common(d, b"\x01\x00\x00\x02\x00\x00", b"\x01\x00\x00\x02", SizeofError)

def test_nullstripped():
    d = NullStripped(GreedyBytes)
    common(d, b'\xff', b'\xff', SizeofError)
    assert d.parse(b'\xff\x00\x00') == b'\xff'
    assert d.build(b'\xff') == b'\xff'
    d = NullStripped(GreedyBytes, pad=b'\x05')
    common(d, b'\xff', b'\xff', SizeofError)
    assert d.parse(b'\xff\x05\x05') == b'\xff'
    assert d.build(b'\xff') == b'\xff'
    d = NullStripped(GreedyString("utf-8"))
    assert d.parse(bytes(10)) == u""
    assert d.build(u"") == b""
    d = NullStripped(GreedyBytes, pad=bytes(2))
    assert d.parse(bytes(10)) == b""
    assert d.parse(bytes(11)) == b""

def test_restreamdata():
    d = RestreamData(b"\x01", Int8ub)
    common(d, b"", 1, 0)
    d = RestreamData(b"", Padding(1))
    assert d.build(None) == b''

    d = RestreamData(io.BytesIO(b"\x01\x02"), Int16ub)
    assert d.parse(b"\x01\x02\x00") == 0x0102
    assert d.build(None) == b''

    d = RestreamData(NullTerminated(GreedyBytes), Int16ub)
    assert d.parse(b"\x01\x02\x00") == 0x0102
    assert d.build(None) == b''

    d = RestreamData(FixedSized(2, GreedyBytes), Int16ub)
    assert d.parse(b"\x01\x02\x00") == 0x0102
    assert d.build(None) == b''

@xfail(reason="unknown, either StreamError or KeyError due to this.entire or this._.entire")
def test_restreamdata_issue_701():
    d = Struct(
        'entire' / GreedyBytes,
        'ac' / RestreamData(this.entire, Struct(
            'a' / Byte,
            Bytes(len_(this._.entire)-1),
            'c' / Byte,
        )),
    )
    # StreamError: stream read less then specified amount, expected 1, found 0
    assert d.parse(b'\x01GGGGGGGGGG\x02') == Container(entire=b'\x01GGGGGGGGGG\x02', ac=Container(a=1,b=2))

    d = FocusedSeq('ac'
        'entire' / GreedyBytes,
        'ac' / RestreamData(this.entire, Struct(
            'a' / Byte,
            Bytes(len_(this._.entire)-1),
            'c' / Byte,
        )),
    )
    # KeyError: 'entire'
    assert d.parse(b'\x01GGGGGGGGGG\x02') == Container(a=1,b=2)

def test_transformed():
    d = Transformed(Bytes(16), bytes2bits, 2, bits2bytes, 2)
    common(d, bytes(2), bytes(16), 2)
    d = Transformed(GreedyBytes, bytes2bits, None, bits2bytes, None)
    common(d, bytes(2), bytes(16), SizeofError)
    d = Transformed(GreedyString("utf-8"), bytes2bits, None, bits2bytes, None)
    common(d, bytes(2), u"\x00"*16, SizeofError)

def test_transformed_issue_676():
    d = Struct(
         'inner1' / BitStruct(
             'a' / Default(BitsInteger(8), 0),
         ),
         'inner2' / BitStruct(
             'a' / Default(BitsInteger(lambda this: 8), 0),
         ),
         Probe(),
         Check(this.inner1.a == 0),
         Check(this.inner2.a == 0),
    )
    d.build({})

def test_restreamed():
    d = Restreamed(Int16ub, ident, 1, ident, 1, ident)
    common(d, b"\x00\x01", 1, 2)
    d = Restreamed(VarInt, ident, 1, ident, 1, ident)
    assert raises(d.sizeof) == SizeofError
    d = Restreamed(Bytes(2), lambda b: b*2, 1, lambda b: b[0:1], 1, lambda n: n*2)
    common(d, b"aa", b"aa", 4)

def test_restreamed_partial_read():
    d = Restreamed(Bytes(255), ident, 1, ident, 1, ident)
    assert raises(d.parse, b"") == StreamError

def test_processxor():
    d = ProcessXor(0, Int16ub)
    common(d, b"\xf0\x0f", 0xf00f, 2)
    d = ProcessXor(0xf0, Int16ub)
    common(d, b"\x00\xff", 0xf00f, 2)
    d = ProcessXor(bytes(10), Int16ub)
    common(d, b"\xf0\x0f", 0xf00f, 2)
    d = ProcessXor(b"\xf0\xf0\xf0\xf0\xf0", Int16ub)
    common(d, b"\x00\xff", 0xf00f, 2)

    d = ProcessXor(0xf0, GreedyBytes)
    common(d, b"\x00\xff", b"\xf0\x0f", SizeofError)
    d = ProcessXor(b"\xf0\xf0\xf0\xf0\xf0", GreedyBytes)
    common(d, b"\x00\xff", b"\xf0\x0f", SizeofError)
    d = ProcessXor(b"X", GreedyString("utf-8"))
    common(d, b"\x00", u"X", SizeofError)
    d = ProcessXor(b"XXXXX", GreedyString("utf-8"))
    common(d, b"\x00", u"X", SizeofError)

def test_processrotateleft():
    d = ProcessRotateLeft(0, 1, GreedyBytes)
    common(d, bytes(10), bytes(10))
    d = ProcessRotateLeft(0, 2, GreedyBytes)
    common(d, bytes(10), bytes(10))
    d = ProcessRotateLeft(4, 1, GreedyBytes)
    common(d, b'\x0f\xf0', b'\xf0\x0f')
    d = ProcessRotateLeft(4, 2, GreedyBytes)
    common(d, b'\x0f\xf0', b'\xff\x00')

def test_checksum():
    d = Struct(
        "fields" / RawCopy(Struct(
            "a" / Byte,
            "b" / Byte,
        )),
        "checksum" / Checksum(Bytes(64), lambda data: hashlib.sha512(data).digest(), this.fields.data),
    )

    c = hashlib.sha512(b"\x01\x02").digest()
    assert d.parse(b"\x01\x02"+c) == Container(fields=dict(data=b"\x01\x02", value=Container(a=1, b=2), offset1=0, offset2=2, length=2), checksum=c)
    assert d.build(dict(fields=dict(data=b"\x01\x02"))) == b"\x01\x02"+c
    assert d.build(dict(fields=dict(value=dict(a=1,b=2)))) == b"\x01\x02"+c

def test_checksum_nonbytes_issue_323():
    d = Struct(
        "vals" / Byte[2],
        "checksum" / Checksum(Byte, lambda vals: sum(vals) & 0xFF, this.vals),
    )
    assert d.parse(b"\x00\x00\x00") == Container(vals=[0, 0], checksum=0)
    assert raises(d.parse, b"\x00\x00\x01") == ChecksumError

def test_compressed_zlib():
    zeros = bytes(10000)
    d = Compressed(GreedyBytes, "zlib")
    assert d.parse(d.build(zeros)) == zeros
    assert len(d.build(zeros)) < 50
    assert raises(d.sizeof) == SizeofError
    d = Compressed(GreedyBytes, "zlib", level=9)
    assert d.parse(d.build(zeros)) == zeros
    assert len(d.build(zeros)) < 50
    assert raises(d.sizeof) == SizeofError

def test_compressed_gzip():
    zeros = bytes(10000)
    d = Compressed(GreedyBytes, "gzip")
    assert d.parse(d.build(zeros)) == zeros
    assert len(d.build(zeros)) < 50
    assert raises(d.sizeof) == SizeofError
    d = Compressed(GreedyBytes, "gzip", level=9)
    assert d.parse(d.build(zeros)) == zeros
    assert len(d.build(zeros)) < 50
    assert raises(d.sizeof) == SizeofError

def test_compressed_bzip2():
    zeros = bytes(10000)
    d = Compressed(GreedyBytes, "bzip2")
    assert d.parse(d.build(zeros)) == zeros
    assert len(d.build(zeros)) < 50
    assert raises(d.sizeof) == SizeofError
    d = Compressed(GreedyBytes, "bzip2", level=9)
    assert d.parse(d.build(zeros)) == zeros
    assert len(d.build(zeros)) < 50
    assert raises(d.sizeof) == SizeofError

def test_compressed_lzma():
    zeros = bytes(10000)
    d = Compressed(GreedyBytes, "lzma")
    assert d.parse(d.build(zeros)) == zeros
    assert len(d.build(zeros)) < 200
    assert raises(d.sizeof) == SizeofError
    d = Compressed(GreedyBytes, "lzma", level=9)
    assert d.parse(d.build(zeros)) == zeros
    assert len(d.build(zeros)) < 200
    assert raises(d.sizeof) == SizeofError

def test_compressed_prefixed():
    zeros = bytes(10000)
    d = Prefixed(VarInt, Compressed(GreedyBytes, "zlib"))
    st = Struct("one"/d, "two"/d)
    assert st.parse(st.build(Container(one=zeros,two=zeros))) == Container(one=zeros,two=zeros)
    assert raises(d.sizeof) == SizeofError

def test_compressedlz4():
    zeros = bytes(10000)
    d = CompressedLZ4(GreedyBytes)
    assert d.parse(d.build(zeros)) == zeros
    assert len(d.build(zeros)) < 100
    assert raises(d.sizeof) == SizeofError

def test_rebuffered():
    data = b"0" * 1000
    assert Rebuffered(Array(1000,Byte)).parse_stream(io.BytesIO(data)) == [48]*1000
    assert Rebuffered(Array(1000,Byte), tailcutoff=50).parse_stream(io.BytesIO(data)) == [48]*1000
    assert Rebuffered(Byte).sizeof() == 1
    assert raises(Rebuffered(Byte).sizeof) == 1
    assert raises(Rebuffered(VarInt).sizeof) == SizeofError

def test_lazy():
    d = Struct(
        'dup' / Lazy(Computed(this.exists)),
        'exists' / Computed(1),
    )
    obj = d.parse(b'')
    assert obj.dup() == 1

    d = Lazy(Byte)
    x = d.parse(b'\x00')
    assert x() == 0
    assert d.build(0) == b'\x00'
    assert d.build(x) == b'\x00'
    assert d.sizeof() == 1

def test_lazy_seek():
    d = Struct(
        "a" / Int8ub,
        "b" / Lazy(Bytes(2)),
        "c" / Int16ub,
        "d" / Lazy(Bytes(4))
    )
    obj = d.parse(b"\x01\x02\x03\x04\x05\x06\x07\x08\x09")

    assert obj.a == 0x01
    assert obj.b() == b'\x02\x03'
    assert obj.c == 0x0405
    assert obj.d() == b'\x06\x07\x08\x09'

def test_lazystruct():
    d = LazyStruct(
        "num1" / Int8ub,
        "num2" / BytesInteger(1),
        "prefixed1" / Prefixed(Byte, Byte),
        "prefixed2" / Prefixed(Byte, Byte, includelength=True),
        "prefixedarray" / PrefixedArray(Byte, Byte),
    )
    obj = d.parse(b"\x00\x00\x01\x00\x02\x00\x01\x00")
    assert obj.num1 == obj["num1"] == obj[0] == 0
    assert obj.num2 == obj["num2"] == obj[1] == 0
    assert obj.prefixed1 == obj["prefixed1"] == obj[2] == 0
    assert obj.prefixed2 == obj["prefixed2"] == obj[3] == 0
    assert obj.prefixedarray == obj["prefixedarray"] == obj[4] == [0]
    assert len(obj) == 5
    assert list(obj.keys()) == ['num1', 'num2', 'prefixed1', 'prefixed2', 'prefixedarray']
    assert list(obj.values()) == [0, 0, 0, 0, [0]]
    assert list(obj.items()) == [('num1', 0), ('num2', 0), ('prefixed1', 0), ('prefixed2', 0), ('prefixedarray', [0])]
    assert repr(obj) == "<LazyContainer: 5 items cached, 5 subcons>"
    assert str(obj) == "<LazyContainer: 5 items cached, 5 subcons>"
    assert d.build(obj) == b"\x00\x00\x01\x00\x02\x00\x01\x00"
    assert d.build(Container(obj)) == b"\x00\x00\x01\x00\x02\x00\x01\x00"
    assert raises(d.sizeof) == SizeofError

def test_lazyarray():
    d = LazyArray(5, Int8ub)
    obj = d.parse(b"\x00\x01\x02\x03\x04")
    assert repr(obj) == "<LazyListContainer: 0 of 5 items cached>"
    for i in range(5):
        assert obj[i] == i
    assert obj[:] == [0,1,2,3,4]
    assert obj == [0,1,2,3,4]
    assert list(obj) == [0,1,2,3,4]
    assert len(obj) == 5
    assert repr(obj) == "<LazyListContainer: 5 of 5 items cached>"
    assert str(obj) == "<LazyListContainer: 5 of 5 items cached>"
    assert d.build([0,1,2,3,4]) == b"\x00\x01\x02\x03\x04"
    assert d.build(ListContainer([0,1,2,3,4])) == b"\x00\x01\x02\x03\x04"
    assert d.build(obj) == b"\x00\x01\x02\x03\x04"
    assert d.build(obj[:]) == b"\x00\x01\x02\x03\x04"
    assert d.sizeof() == 5

    d = LazyArray(5, VarInt)
    obj = d.parse(b"\x00\x01\x02\x03\x04")
    assert repr(obj) == "<LazyListContainer: 5 of 5 items cached>"
    for i in range(5):
        assert obj[i] == i
    assert obj[:] == [0,1,2,3,4]
    assert obj == [0,1,2,3,4]
    assert list(obj) == [0,1,2,3,4]
    assert len(obj) == 5
    assert repr(obj) == "<LazyListContainer: 5 of 5 items cached>"
    assert str(obj) == "<LazyListContainer: 5 of 5 items cached>"
    assert d.build([0,1,2,3,4]) == b"\x00\x01\x02\x03\x04"
    assert d.build(ListContainer([0,1,2,3,4])) == b"\x00\x01\x02\x03\x04"
    assert d.build(obj) == b"\x00\x01\x02\x03\x04"
    assert d.build(obj[:]) == b"\x00\x01\x02\x03\x04"
    assert raises(d.sizeof) == SizeofError

def test_lazybound():
    d = LazyBound(lambda: Byte)
    common(d, b"\x01", 1)

    d = Struct(
        "value" / Byte,
        "next" / If(this.value > 0, LazyBound(lambda: d)),
    )
    common(d, b"\x05\x09\x00", Container(value=5, next=Container(value=9, next=Container(value=0, next=None))))

    d = Struct(
        "value" / Byte,
        "next" / GreedyBytes,
    )
    data = b"\x05\x09\x00"
    while data:
        x = d.parse(data)
        data = x.next
        print(x)

def test_expradapter():
    MulDiv = ExprAdapter(Byte, obj_ * 7, obj_ // 7)
    assert MulDiv.parse(b"\x06") == 42
    assert MulDiv.build(42) == b"\x06"
    assert MulDiv.sizeof() == 1

    Ident = ExprAdapter(Byte, obj_-1, obj_+1)
    assert Ident.parse(b"\x02") == 1
    assert Ident.build(1) == b"\x02"
    assert Ident.sizeof() == 1

def test_exprsymmetricadapter():
    pass

def test_exprvalidator():
    One = ExprValidator(Byte, lambda obj,ctx: obj in [1,3,5])
    assert One.parse(b"\x01") == 1
    assert raises(One.parse, b"\xff") == ValidationError
    assert One.build(5) == b"\x05"
    assert raises(One.build, 255) == ValidationError
    assert One.sizeof() == 1

def test_ipaddress_adapter_issue_95():
    class IpAddressAdapter(Adapter):
        def _encode(self, obj, context, path):
            return list(map(int, obj.split(".")))
        def _decode(self, obj, context, path):
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

def test_oneof():
    assert OneOf(Byte,[4,5,6,7]).parse(b"\x05") == 5
    assert OneOf(Byte,[4,5,6,7]).build(5) == b"\x05"
    assert raises(OneOf(Byte,[4,5,6,7]).parse, b"\x08") == ValidationError
    assert raises(OneOf(Byte,[4,5,6,7]).build, 8) == ValidationError

def test_noneof():
    assert NoneOf(Byte,[4,5,6,7]).parse(b"\x08") == 8
    assert raises(NoneOf(Byte,[4,5,6,7]).parse, b"\x06") == ValidationError

def test_filter():
    d = Filter(obj_ != 0, GreedyRange(Byte))
    assert d.parse(b"\x00\x02\x00") == [2]
    assert d.build([0,1,0,2,0]) == b"\x01\x02"

def test_slicing():
    d = Slicing(Array(4,Byte), 4, 1, 3, empty=0)
    assert d.parse(b"\x01\x02\x03\x04") == [2,3]
    assert d.build([2,3]) == b"\x00\x02\x03\x00"
    assert d.sizeof() == 4

def test_indexing():
    d = Indexing(Array(4,Byte), 4, 2, empty=0)
    assert d.parse(b"\x01\x02\x03\x04") == 3
    assert d.build(3) == b"\x00\x00\x03\x00"
    assert d.sizeof() == 4

def test_probe():
    common(Probe(), b"", None, 0)
    common(Probe(lookahead=32), b"", None, 0)

    common(Struct(Probe()), b"", {}, 0)
    common(Struct(Probe(lookahead=32)), b"", {}, 0)
    common(Struct("value"/Computed(7), Probe(this.value)), b"", dict(value=7), 0)

def test_debugger():
    common(Debugger(Byte), b"\xff", 255, 1)

def test_repr():
    assert repr(Byte) == '<FormatField>'
    assert repr("num"/Byte) == '<Renamed num <FormatField>>'
    assert repr(Default(Byte, 0)) == '<Default +nonbuild <FormatField>>'
    assert repr(Struct()) == '<Struct +nonbuild>'

def test_operators():
    common(Struct("new" / ("old" / Byte)), b"\x01", Container(new=1), 1)
    common(Struct(Renamed(Renamed(Byte, newname="old"), newname="new")), b"\x01", Container(new=1), 1)

    common(Array(4, Byte), b"\x01\x02\x03\x04", [1,2,3,4], 4)
    common(Byte[4], b"\x01\x02\x03\x04", [1,2,3,4], 4)
    common(Struct("nums" / Byte[4]), b"\x01\x02\x03\x04", Container(nums=[1,2,3,4]), 4)

    common(Int8ub >> Int16ub, b"\x01\x00\x02", [1,2], 3)
    common(Int8ub >> Int16ub >> Int32ub, b"\x01\x00\x02\x00\x00\x00\x03", [1,2,3], 7)
    common(Int8ub[2] >> Int16ub[2], b"\x01\x02\x00\x03\x00\x04", [[1,2],[3,4]], 6)

    common(Sequence(Int8ub) >> Sequence(Int16ub), b"\x01\x00\x02", [1,2], 3)
    common(Struct("count"/Byte, "items"/Byte[this.count], Pass, Terminated), b"\x03\x01\x02\x03", Container(count=3, items=[1,2,3]), SizeofError)
    common("count"/Byte + "items"/Byte[this.count] + Pass + Terminated, b"\x03\x01\x02\x03", Container(count=3, items=[1,2,3]), SizeofError)
    common(Struct(a=Byte) + Struct(b=Byte), b"\x01\x02", Container(a=1, b=2), 2)

    d = Byte * "description"
    assert d.docs == "description"
    d = "description" * Byte
    assert d.docs == "description"
    """
    description
    """ * \
    Byte
    assert d.docs == "description"
    d = Renamed(Renamed(Byte, newdocs="old"), newdocs="new")
    assert d.docs == "new"

def test_operators_issue_87():
    assert ("string_name" / Byte).parse(b"\x01") == 1
    assert (u"unicode_name" / Byte).parse(b"\x01") == 1
    assert (b"bytes_name" / Byte).parse(b"\x01") == 1
    assert (None / Byte).parse(b"\x01") == 1

def test_from_issue_76():
    d = Aligned(4, Struct("a"/Byte, "f"/Bytes(lambda ctx: ctx.a)))
    common(d, b"\x02\xab\xcd\x00", Container(a=2, f=b"\xab\xcd"))

def test_from_issue_60():
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
    assert Header.parse(b"\x00\x05")             == Container(type=0, size=5, length=2)
    assert Header.parse(b"\x01\x00\x05")         == Container(type=1, size=5, length=3)
    assert Header.parse(b"\x02\x00\x00\x00\x05") == Container(type=2, size=5, length=5)
    assert Header.build(dict(type=0, size=5)) == b"\x00\x05"
    assert Header.build(dict(type=1, size=5)) == b"\x01\x00\x05"
    assert Header.build(dict(type=2, size=5)) == b"\x02\x00\x00\x00\x05"

def test_from_issue_171():
    attributes = BitStruct(
        "attr" / Aligned(8, Array(3, Struct(
            "attrCode" / BitsInteger(16),
            "attrValue" / Switch(this.attrCode, {
                34: BitsInteger(8),
                205: BitsInteger(2),
                512: BitsInteger(2),
            }),
        ))),
    )
    blob = b"\x00\x22\x82\x00\xCD\x80\x80\x10"
    assert attributes.parse(blob) == Container(attr=[
        Container(attrCode=34, attrValue=130),
        Container(attrCode=205, attrValue=2),
        Container(attrCode=512, attrValue=1), ])

def test_from_issue_175():
    @FuncPath
    def comp_(num_array):
        return sum(x << ((len(num_array)-1-i)*8) for i,x in enumerate(num_array))

    test = Struct(
        "numArray" / RepeatUntil(obj_ < 128, Byte),
        "value" / Computed(comp_(this.numArray))
    )
    assert test.parse(b'\x87\x0f').value == 34575

def test_from_issue_71():
    Inner = Struct(
        'name' / PascalString(Byte, "utf8"),
        'occupation' / PascalString(Byte, "utf8"),
    )
    Outer = Struct(
        'struct_type' / Int16ub,
        'payload_len' / Int16ub,
        'payload' / RawCopy(Inner),
        'serial' / Int16ub,
        'checksum' / Checksum(Bytes(64),
            lambda data: hashlib.sha512(data).digest(),
            this.payload.data),
        Check(len_(this.payload.data) == this.payload_len),
        Terminated,
    )

    payload = Inner.build(Container(
        name=u"unknown",
        occupation=u"worker",
    ))
    Outer.build(Container(
        struct_type=9001,
        payload_len=len(payload),
        payload=Container(data=payload),
        serial=12345,
    ))

def test_from_issue_231():
    u = Union(0, "raw"/Byte[8], "ints"/Int[2])
    s = Struct("u"/u, "d"/Byte[4])

    buildret = s.build(dict(u=dict(ints=[1,2]),d=[0,1,2,3]))
    assert buildret == b"\x00\x00\x00\x01\x00\x00\x00\x02\x00\x01\x02\x03"
    assert s.build(s.parse(buildret)) == buildret

def test_from_issue_246():
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
    assert NumVertices.parse(b'\x01\x34\x56\x70') == Container(numVx4=Container(num=0), numVx8=Container(num=19), numVx16=Container(num=1262951))

def test_from_issue_244():
    class AddIndexes(Adapter):
        def _decode(self, obj, context, path):
            for i,con in enumerate(obj):
                con.index = i
            return obj

    d = AddIndexes(Struct("num"/Byte)[4])
    assert d.parse(b"abcd") == [Container(num=97, index=0),Container(num=98, index=1),Container(num=99, index=2),Container(num=100, index=3),]

def test_from_issue_269():
    d = Struct("enabled" / Byte, If(this.enabled, Padding(2)))
    assert d.build(dict(enabled=1)) == b"\x01\x00\x00"
    assert d.build(dict(enabled=0)) == b"\x00"
    d = Struct("enabled" / Byte, "pad" / If(this.enabled, Padding(2)))
    assert d.build(dict(enabled=1)) == b"\x01\x00\x00"
    assert d.build(dict(enabled=0)) == b"\x00"

def test_hanging_issue_280():
    d = BitStruct('a'/BitsInteger(20), 'b'/BitsInteger(12))
    assert raises(d.parse, b'\x00') == StreamError

def test_from_issue_324():
    d = Struct(
        "vals" / Prefixed(Byte, RawCopy(
            Struct("a" / Byte[2]),
        )),
        "checksum" / Checksum(
            Byte,
            lambda data: sum(data) & 0xFF,
            this.vals.data
        ),
    )
    assert d.build(dict(vals=dict(value=dict(a=[0,1])))) == b"\x02\x00\x01\x01"
    assert d.build(dict(vals=dict(data=b"\x00\x01"))) == b"\x02\x00\x01\x01"

def test_from_issue_357():
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

def test_context_is_container():
    d = Struct(Check(lambda ctx: type(ctx) is Container))
    d.parse(b"")

def test_from_issue_362():
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

@xfail(raises=AttributeError, reason="can't access Enums inside BitStruct")
def test_from_issue_781():
    d = Struct(
        "animal" / Enum(Byte, giraffe=1),
    )

    x = d.parse(b"\x01")
    assert x.animal == "giraffe"  # works
    assert x.animal == d.animal.giraffe  # works

    d = BitStruct(
        "animal" / Enum(BitsInteger(8), giraffe=1),
    )

    x = d.parse(b"\x01")
    assert x.animal == "giraffe"  # works
    assert x.animal == d.animal.giraffe  # AttributeError: 'Transformed' object has no attribute 'animal'

def test_this_expresion_compare_container():
    st = Struct(
        "flags" / FlagsEnum(Byte, a=1),
        Check(lambda this: this.flags == Container(_flagsenum=True, a=1)),
    )
    common(st, b"\x01", dict(flags=Container(_flagsenum=True, a=True)), 1)

def test_pickling_constructs():
    import cloudpickle

    d = Struct(
        "count" / Byte,
        "greedybytes" / Prefixed(Byte, GreedyBytes),
        "formatfield" / FormatField("=","Q"),
        "bytesinteger" / BytesInteger(1),
        "varint" / VarInt,
        "text1" / PascalString(Byte, "utf8"),
        "text2" / CString("utf8"),
        "enum" / Enum(Byte, zero=0),
        "flagsenum" / FlagsEnum(Byte, zero=0),
        "array1" / Byte[5],
        "array2" / Byte[this.count],
        "greedyrange" / Prefixed(Byte, GreedyRange(Byte)),
        "if1" / IfThenElse(True, Byte, Byte),
        "padding" / Padding(1),
        "peek" / Peek(Byte),
        "tell" / Tell,
        "this1" / Byte[this.count],
        "obj_1" / RepeatUntil(obj_ == 0, Byte),
        "len_1" / Computed(len_(this.array1)),
    )
    data = bytes(100)

    du = cloudpickle.loads(cloudpickle.dumps(d, protocol=-1))
    assert du.parse(data) == d.parse(data)

def test_pickling_constructs_issue_894():
    import cloudpickle

    fundus_header = Struct(
        'width' / Int32un,
        'height' / Int32un,
        'bits_per_pixel' / Int32un,
        'number_slices' / Int32un,
        'unknown' / PaddedString(4, 'ascii'),
        'size' / Int32un,
        'img' / Int8un,
    )

    cloudpickle.dumps(fundus_header)

def test_exposing_members_attributes():
    d = Struct(
        "animal" / Enum(Byte, giraffe=1),
    )
    assert isinstance(d.animal, Renamed)
    assert isinstance(d.animal.subcon, Enum)
    assert d.animal.giraffe == "giraffe"

    d = Sequence(
        "animal" / Enum(Byte, giraffe=1),
    )
    assert isinstance(d.animal, Renamed)
    assert isinstance(d.animal.subcon, Enum)
    assert d.animal.giraffe == "giraffe"

    d = FocusedSeq(0,
        "animal" / Enum(Byte, giraffe=1),
    )
    assert isinstance(d.animal, Renamed)
    assert isinstance(d.animal.subcon, Enum)
    assert d.animal.giraffe == "giraffe"

    d = Union(None,
        "animal" / Enum(Byte, giraffe=1),
    )
    assert isinstance(d.animal, Renamed)
    assert isinstance(d.animal.subcon, Enum)
    assert d.animal.giraffe == "giraffe"

def test_exposing_members_context():
    d = Struct(
        "count" / Byte,
        "data" / Bytes(lambda this: this.count - this._subcons.count.sizeof()),
        Check(lambda this: this._subcons.count.sizeof() == 1),
    )
    common(d, b"\x05four", Container(count=5, data=b"four"))

    d = Sequence(
        "count" / Byte,
        "data" / Bytes(lambda this: this.count - this._subcons.count.sizeof()),
        Check(lambda this: this._subcons.count.sizeof() == 1),
    )
    common(d, b"\x05four", [5,b"four",None])

    d = FocusedSeq("count",
        "count" / Byte,
        "data" / Padding(lambda this: this.count - this._subcons.count.sizeof()),
        Check(lambda this: this._subcons.count.sizeof() == 1),
    )
    common(d, b'\x04\x00\x00\x00', 4, SizeofError)

    d = Union(None,
        "chars" / Byte[4],
        "data" / Bytes(lambda this: this._subcons.chars.sizeof()),
        Check(lambda this: this._subcons.chars.sizeof() == 4),
    )
    assert d.parse(b"\x01\x02\x03\x04") == dict(chars=[1,2,3,4],data=b"\x01\x02\x03\x04")

def test_isparsingbuilding():
    d = Struct(
        Check(this._parsing & this._._parsing),
        Check(~this._building & ~this._._building),
        Check(~this._sizing & ~this._._sizing),
    )
    d.parse(b'')
    d = Struct(
        Check(~this._parsing & ~this._._parsing),
        Check(this._building & this._._building),
        Check(~this._sizing & ~this._._sizing),
    )
    d.build(None)
    d = Struct(
        Check(~this._parsing & ~this._._parsing),
        Check(~this._building & ~this._._building),
        Check(this._sizing & this._._sizing),
    )
    d.sizeof()
    # ---------------------------------
    d = Sequence(
        Check(this._parsing & this._._parsing),
        Check(~this._building & ~this._._building),
        Check(~this._sizing & ~this._._sizing),
    )
    d.parse(b'')
    d = Sequence(
        Check(~this._parsing & ~this._._parsing),
        Check(this._building & this._._building),
        Check(~this._sizing & ~this._._sizing),
    )
    d.build(None)
    d = Sequence(
        Check(~this._parsing & ~this._._parsing),
        Check(~this._building & ~this._._building),
        Check(this._sizing & this._._sizing),
    )
    d.sizeof()
    # ---------------------------------
    d = FocusedSeq("none",
        "none" / Pass,
        Check(this._parsing & this._._parsing),
        Check(~this._building & ~this._._building),
        Check(~this._sizing & ~this._._sizing),
    )
    d.parse(b'')
    d = FocusedSeq("none",
        "none" / Pass,
        Check(~this._parsing & ~this._._parsing),
        Check(this._building & this._._building),
        Check(~this._sizing & ~this._._sizing),
    )
    d.build(None)
    d = FocusedSeq("none",
        "none" / Pass,
        Check(~this._parsing & ~this._._parsing),
        Check(~this._building & ~this._._building),
        Check(this._sizing & this._._sizing),
    )
    d.sizeof()
    # ---------------------------------
    d = Union(None,
        "none" / Pass,
        Check(this._parsing & this._._parsing),
        Check(~this._building & ~this._._building),
        Check(~this._sizing & ~this._._sizing),
    )
    d.parse(b'')
    d = Union(None,
        "none" / Pass,
        Check(~this._parsing & ~this._._parsing),
        Check(this._building & this._._building),
        Check(~this._sizing & ~this._._sizing),
    )
    d.build(dict(none=None))
    d = Union(None,
        "none" / Pass,
        Check(~this._parsing & ~this._._parsing),
        Check(~this._building & ~this._._building),
        Check(this._sizing & this._._sizing),
    )
    # doesnt check context because _sizeof just raises the error
    assert raises(d.sizeof) == SizeofError
    # ---------------------------------
    d = LazyStruct(
        Check(this._parsing & this._._parsing),
        Check(~this._building & ~this._._building),
        Check(~this._sizing & ~this._._sizing),
    )
    d.parse(b'')
    d = LazyStruct(
        Check(~this._parsing & ~this._._parsing),
        Check(this._building & this._._building),
        Check(~this._sizing & ~this._._sizing),
    )
    d.build({})
    d = LazyStruct(
        Check(~this._parsing & ~this._._parsing),
        Check(~this._building & ~this._._building),
        Check(this._sizing & this._._sizing),
    )
    d.sizeof()

def test_struct_stream():
    d = Struct(
        'fixed' / FixedSized(10, Struct(
            'data' / GreedyBytes,
            # check a substream
            Check(lambda this: stream_size(this._io) == 10),
            Check(lambda this: stream_iseof(this._io)),
            # checks parent original stream
            Check(lambda this: stream_size(this._._io) == 20),
            Check(lambda this: not stream_iseof(this._._io)),
        )),
        # checks mid-parsing
        Check(lambda this: stream_tell(this._io, None) == 10),
        Check(lambda this: stream_size(this._io) == 20),
        Check(lambda this: not stream_iseof(this._io)),
        'rest' / GreedyBytes,
        # checks after parsed to EOF
        Check(lambda this: stream_tell(this._io, None) == 20),
        Check(lambda this: stream_size(this._io) == 20),
        Check(lambda this: stream_iseof(this._io)),
        Check(lambda this: stream_seek(this._io, 0, 2, None) == 20),
        # checks nested struct stream
        Check(lambda this: stream_tell(this.fixed._io, None) == 10),
        Check(lambda this: stream_size(this.fixed._io) == 10),
    )
    d.parse(bytes(20))

def test_struct_root_topmost():
    d = Struct(
        'x' / Computed(1),
        'inner' / Struct(
            'inner2' / Struct(
                'x' / Computed(this._root.x),
                'z' / Computed(this._params.z),
                'zz' / Computed(this._root._.z),
            ),
        ),
        Probe(),
    )
    # setGlobalPrintPrivateEntries(True)
    # d.parse(b'', z=2)
    assert d.parse(b"", z=2) == Container(x=1, inner=Container(inner2=Container(x=1,z=2,zz=2)))

def test_parsedhook_repeatersdiscard():
    outputs = []
    def printobj(obj, ctx):
        outputs.append(obj)
    d = GreedyRange(Byte * printobj, discard=True)
    assert d.parse(b"\x01\x02\x03") == []
    assert outputs == [1,2,3]

    outputs = []
    def printobj(obj, ctx):
        outputs.append(obj)
    d = Array(3, Byte * printobj, discard=True)
    assert d.parse(b"\x01\x02\x03") == []
    assert outputs == [1,2,3]

    outputs = []
    def printobj(obj, ctx):
        outputs.append(obj)
    d = RepeatUntil(lambda obj,lst,ctx: ctx._index == 2, Byte * printobj, discard=True)
    assert d.parse(b"\x01\x02\x03") == []
    assert outputs == [1,2,3]

def test_exportksy():
    d = Struct(
        "nothing" / Pass * "field docstring",

        "data1" / Bytes(10),
        "data2" / GreedyBytes,

        "bitstruct" / BitStruct(
            "flag" / Flag,
            "padding" / Padding(7),
            "int32" / Int32ub,
            "int32le" / BytesInteger(4),
            "int4a" / Nibble,
            "int4b" / BitsInteger(4),
        ),

        "int32" / Int32ub,
        "float32" / Float32b,
        "int32le" / BytesInteger(4, swapped=True),
        "varint" / VarInt,

        "string1" / PaddedString(10, "utf8"),
        "string2" / PascalString(Byte, "utf8"),
        "string3" / CString("utf8"),
        "string4" / GreedyString("utf8"),

        "flag" / Flag,
        "enum" / Enum(Byte, one=1, two=2),
        "flagsenum" / FlagsEnum(Byte, one=1, two=2),

        "struct1" / Struct(Byte, "named"/Byte),
        "sequence1" / Sequence(Byte, "named"/Byte),

        "array2d" / Array(5, Array(5, Byte)),
        "greedyrange" / GreedyRange(Byte),
        "repeatuntil" / RepeatUntil(obj_ == 0, Byte),

        "const1" / Const(b"ABCD"),
        "const2" / Const(1, Int32ub),
        # Computed
        # Index
        "rebuild" / Rebuild(Byte, 0),
        "default" / Default(Byte, 0),
        "namedtuple1" / NamedTuple("coord", "x y z", "x"/Byte + "y"/Byte + "z"/Byte),
        "namedtuple2" / NamedTuple("coord", "x y z", Byte >> Byte >> Byte),
        "namedtuple3" / NamedTuple("coord", "x y z", Byte[3]),
        "namedtuple4" / NamedTuple("coord", "x y z", GreedyRange(Byte)),
        "timestamp1" / Timestamp(Int32ub, 1, 1970),
        "timestamp2" / Timestamp(Int32ub, "msdos", "msdos"),
        "hex" / Hex(Int32ub),
        "hexdump" / HexDump(Int32ub),

        # Union
        "if1" / If(this.num == 0, Byte),
        "ifthenelse1" / IfThenElse(this.num == 0, Byte, Byte),
        # Switch

        "padding" / Padding(5),
        "padded" / Padded(5, Byte),

        "pointer1" / Pointer(0x1000, Int32ub),
        "pointer2" / Pointer(this.pointer1, Int32ub),
        "pass1" / Pass,
        # Terminated

        "prefixed" / Prefixed(Byte, GreedyBytes),
        "prefixedarray" / PrefixedArray(Byte, Byte),
        # Compressed
    ) * \
    "struct docstring"
    print(d.export_ksy(filename="example_ksy.ksy"))

@xfail(reason="both sizeof fail because length is 1 level up than when parsing")
def test_from_issue_692():
    # https://stackoverflow.com/questions/44747202/pythons-construct-sizeof-for-construct-depending-on-its-parent

    AttributeHandleValuePair = Struct(
        "handle" / Int16ul,
        "value" / GreedyBytes,
    )
    AttReadByTypeResponse = Struct(
        "length" / Int8ul,  # The size in bytes of each handle/value pair
        "datalist" / Array(2, FixedSized(this.length, AttributeHandleValuePair)),
    )
    assert AttReadByTypeResponse.parse(b"\x04\x01\x02\x03\x04\x01\x02\x03\x04") == Container(length=4,datalist=[dict(handle=0x0201,value=b'\x03\x04'),dict(handle=0x0201,value=b'\x03\x04')])
    assert AttReadByTypeResponse.sizeof(length=4) == 1+2*4

    AttributeHandleValuePair = Struct(
        "handle" / Int16ul,
        "value" / Bytes(this._.length - 2),
    )
    AttReadByTypeResponse = Struct(
        "length" / Int8ul,  # The size in bytes of each handle/value pair
        "datalist" / AttributeHandleValuePair[2],
    )
    assert AttReadByTypeResponse.parse(b"\x04\x01\x02\x03\x04\x01\x02\x03\x04") == Container(length=4,datalist=[dict(handle=0x0201,value=b'\x03\x04'),dict(handle=0x0201,value=b'\x03\x04')])
    assert AttReadByTypeResponse.sizeof(length=4) == 1+2*(2+4-2)

def test_greedyrange_issue_697():
    d = BitStruct(
        "rest" / Bytewise(GreedyRange(Byte)),
    )
    d.parse(bytes(5))

def test_greedybytes_issue_697():
    d = BitStruct(
        "rest" / Bytewise(GreedyBytes),
    )
    d.parse(bytes(5))

def test_hex_issue_709():
    # Make sure, the fix doesn't destroy already working code
    d = Hex(Bytes(1))
    obj = d.parse(b"\xff")
    assert "unhexlify('ff')" in str(obj)

    d = Struct("x" / Hex(Byte))
    obj = d.parse(b"\xff")
    assert "x = 0xFF" in str(obj)

    d = HexDump(Bytes(1))
    obj = d.parse(b"\xff")
    assert "hexundump" in str(obj)

    # The following checks only succeed after fixing the issue
    d = Struct("x" / Hex(Bytes(1)))
    obj = d.parse(b"\xff")
    assert "x = unhexlify('ff')" in str(obj)

    d = Struct("x" / HexDump(Bytes(1)))
    obj = d.parse(b"\xff")
    assert "x = hexundump" in str(obj)

    d = Struct("x" / Struct("y" / Hex(Bytes(1))))
    obj = d.parse(b"\xff")
    assert "y = unhexlify('ff')" in str(obj)

@xfail(reason="Enable to see path information in stream operations")
def test_showpath():
    # trips stream_read
    d = Struct("inner"/Struct("x"/Byte))
    d.parse(b"")

@xfail(reason="Enable to see path information in stream operations")
def test_showpath2():
    x = Struct(
        'foo' / Bytes(1),
        'a' / Struct(
            'foo' / Bytes(1),
            'b' / Struct(
                'foo' / Bytes(1),
                'c' / Struct(
                    'foo' / Bytes(1),
                    'bar' / Bytes(1)
                )
            )
        )
    )
    x.parse(b'\xff' * 5)
    x.parse(b'\xff' * 3)
    # StreamError: Error in path (parsing) -> a -> b -> c -> foo
    # stream read less than specified amount, expected 1, found 0

def test_buildfile_issue_737():
    Byte.build_file(Byte.parse(b'\xff'), 'example_737')
    assert Byte.parse_file('example_737') == 255

@xfail(reason="Context is not properly processed, see #771 and PR #784")
def test_struct_issue_771():
    spec = Struct(
        'a' / Int32ul,
        'b' / Struct(
            'count' / Int32ul,
            'entries' / Byte[this.count]
        )
    )
    data = b'\x01\x00\x00\x00\x02\x00\x00\x00\x0a\x0b'
    info = spec.parse(data)
    assert info == {'a': 1, 'b': {'count': 2, 'entries': [0x0a, 0x0b]}}
    assert spec.build(info) == data
    assert spec.sizeof(**info) == 10

def test_struct_copy():
    import copy
    d = Struct(
        "a" / Int16ub,
        "b" / Int8ub,
    )
    d_copy = copy.copy(d)
    
    common(d, b"\x00\x01\x02", Container(a=1,b=2), 3)
    common(d_copy, b"\x00\x01\x02", Container(a=1,b=2), 3)

def test_switch_issue_913_using_enum():
    enum = Enum(Byte, Zero=0, One=1, Two=2)
    mapping = {
        enum.Zero: Pass,
        enum.One: Int8ul,
        enum.Two: Int16ul,
    }

    d = Switch(keyfunc = this.x, cases = mapping)
    common(d, b"", None, 0, x="Zero")
    common(d, b"\xab", 171, 1, x="One")
    common(d, b"\x09\x00", 9, 2, x="Two")

def test_switch_issue_913_using_strings():
    mapping = {
        "Zero": Pass,
        "One": Int8ul,
        "Two": Int16ul,
    }

    d = Switch(keyfunc = this.x, cases = mapping)
    common(d, b"", None, 0, x="Zero")
    common(d, b"\xab", 171, 1, x="One")
    common(d, b"\x09\x00", 9, 2, x="Two")

def test_switch_issue_913_using_integers():
    mapping = {
        0: Pass,
        1: Int8ul,
        2: Int16ul,
    }

    d = Switch(keyfunc = this.x, cases = mapping)
    common(d, b"", None, 0, x=0)
    common(d, b"\xab", 171, 1, x=1)
    common(d, b"\x09\x00", 9, 2, x=2)
