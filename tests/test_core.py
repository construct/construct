import unittest

from construct import *
from construct.lib.py3compat import PY26


class TestStruct(unittest.TestCase):
    def test_build_from_nested_dicts(self):
        s = Struct(None, Struct('substruct1', Byte('field1')))
        self.assertEqual(s.build(dict(substruct1=dict(field1=5))), b'\x05')


class TestStaticField(unittest.TestCase):

    def setUp(self):
        self.sf = StaticField("staticfield", 2)

    def test_trivial(self):
        pass

    def test_parse(self):
        self.assertEqual(self.sf.parse(b"ab"), b"ab")

    def test_build(self):
        self.assertEqual(self.sf.build(b"ab"), b"ab")

    def test_parse_too_short(self):
        self.assertRaises(FieldError, self.sf.parse, b"a")

    def test_build_too_short(self):
        self.assertRaises(FieldError, self.sf.build, b"a")

    def test_sizeof(self):
        self.assertEqual(self.sf.sizeof(), 2)

    def test_field_parse(self):
        f = Field('name', 6)
        self.assertEqual(f.parse(b'abcdef'), b'abcdef')
        self.assertEqual(f.parse(b'12abcdef'), b'12abcd')
        

class TestFormatField(unittest.TestCase):

    def setUp(self):
        self.ff = FormatField("formatfield", "<", "L")

    def test_trivial(self):
        pass

    def test_parse(self):
        self.assertEqual(self.ff.parse(b"\x12\x34\x56\x78"), 0x78563412)

    def test_build(self):
        self.assertEqual(self.ff.build(0x78563412), b"\x12\x34\x56\x78")

    def test_parse_too_short(self):
        self.assertRaises(FieldError, self.ff.parse, b"\x12\x34\x56")

    def test_build_too_long(self):
        if not PY26:
            self.assertRaises(FieldError, self.ff.build, 2**100)

    def test_build_wrong_value(self):
        self.assertRaises(FieldError, self.ff.build, 9e9999)
        self.assertRaises(FieldError, self.ff.build, "string not int")

    def test_sizeof(self):
        self.assertEqual(self.ff.sizeof(), 4)


class TestMetaField(unittest.TestCase):

    def setUp(self):
        self.mf = MetaField("metafield", lambda ctx: 3)

    def test_trivial(self):
        pass

    def test_parse(self):
        self.assertEqual(self.mf.parse(b"abc"), b"abc")

    def test_build(self):
        self.assertEqual(self.mf.build(b"abc"), b"abc")

    def test_parse_too_short(self):
        self.assertRaises(FieldError, self.mf.parse, b"ab")

    def test_build_too_short(self):
        self.assertRaises(FieldError, self.mf.build, b"ab")

    def test_sizeof(self):
        self.assertEqual(self.mf.sizeof(), 3)


class TestMetaFieldStruct(unittest.TestCase):

    def setUp(self):
        self.mf = MetaField("data", lambda ctx: ctx.length)
        self.s = Struct("struct", Byte("length"), self.mf)

    def test_trivial(self):
        pass

    def test_parse(self):
        c = self.s.parse(b"\x03ABC")
        self.assertEqual(c.length, 3)
        self.assertEqual(c.data, b"ABC")

        c = self.s.parse(b"\x04ABCD")
        self.assertEqual(c.length, 4)
        self.assertEqual(c.data, b"ABCD")

    def test_sizeof_default(self):
        # This no longer raises SizeofError bacuse that error means structure is variable size. If the context is missing entries then the error will reflect that, a missing key.
        self.assertRaises(AttributeError, self.mf.sizeof)

    def test_sizeof(self):
        context = Container(length=4)
        self.assertEqual(self.mf.sizeof(context), 4)


class TestAligned(unittest.TestCase):

    def test_from_issue_76(self):
        def barLength(ctx):
            # print("Context of field2 is", ctx)
            return ctx.field1
        test1 = Struct("test1",
            Aligned(
                Struct("test2",
                    ULInt8("field1"),
                    Field("field2", barLength)
                ),
                modulus=4,
            )
        )
        self.assertEqual(test1.parse(b"\x02\xab\xcd\x00"), Container(test2=Container(field1=2,field2=b"\xab\xcd")))


class TestAnchor(unittest.TestCase):

    def test_from_issue_60(self):
        Header = Struct("header",
            UBInt8("type"),
            Switch("size", lambda ctx: ctx.type,
            {
                0: UBInt8("size"),
                1: UBInt16("size"),
                2: UBInt32("size")
            }),
            Anchor("length"),
        )
        self.assertEqual(Header.parse(b"\x00\x05"), Container(type=0, size=5, length=2))
        self.assertEqual(Header.parse(b"\x01\x00\x05"), Container(type=1, size=5, length=3))
        self.assertEqual(Header.parse(b"\x02\x00\x00\x00\x05"), Container(type=2, size=5, length=5))

        self.assertEqual(Header.build(Container(type=0, size=5)), b"\x00\x05")
        self.assertEqual(Header.build(Container(type=1, size=5)), b"\x01\x00\x05")
        self.assertEqual(Header.build(Container(type=2, size=5)), b"\x02\x00\x00\x00\x05")

    def test_subtract(self):
        Header = Struct("header",
            UBInt8("type"),
            Anchor("start"),
            Switch("size", lambda ctx: ctx.type,
            {
                0: UBInt8("size"),
                1: UBInt16("size"),
                2: UBInt32("size")
            }),
            Anchor("end", subtract="start"),
        )
        self.assertEqual(Header.parse(b"\x00\x05"), Container({'start': 1, 'end': 1, 'type': 0, 'size': 5}))
        self.assertEqual(Header.parse(b"\x01\x00\x05"), Container({'start': 1, 'end': 2, 'type': 1, 'size': 5}))
        self.assertEqual(Header.parse(b"\x02\x00\x00\x00\x05"), Container({'start': 1, 'end': 4, 'type': 2, 'size': 5}))



class TestEmbedOptional(unittest.TestCase):

    def test_from_issue_28(self):
        def vstring(name, embed=True, optional=True):
            lfield = "_%s_length" % name.lower()
            s = Struct(name,
                ULInt8(lfield),
                String(name, lambda ctx: ctx.lfield))
            if optional:
                s = Optional(s)
            if embed:
                s = Embed(s)
            return s

        def build_struct(embed_g=True, embed_h=True):
            s = Struct(
                "mystruct",
                ULInt32("a"),
                ULInt8("b"),
                ULInt8("c"),
                BitStruct(
                    "d",
                    BitField("d_bit7", 1),
                    BitField("d_bit6", 1),
                    BitField("d_bit5", 1),
                    BitField("d_bit4", 1),
                    BitField("d_bit3", 1),
                    BitField("d_bit2", 1),
                    BitField("d_bit1", 1),
                    BitField("d_bit0", 1)),
                BitStruct(
                    "e",
                    BitField("e_bit7", 1),
                    BitField("e_bit6", 1),
                    BitField("e_bit5", 1),
                    BitField("e_bit4", 1),
                    BitField("e_bit3", 1),
                    BitField("e_bit2", 1),
                    BitField("e_bit1", 1),
                    BitField("e_bit0", 1)),
                BFloat32("f"),
                vstring("g", embed=embed_g),
                vstring("h", embed=embed_h),
                BitStruct(
                    "i",
                    BitField("i_bit7", 1),
                    BitField("i_bit6", 1),
                    BitField("i_bit5", 1),
                    BitField("i_bit4", 1),
                    BitField("i_bit3", 1),
                    BitField("i_bit2", 1),
                    BitField("i_bit1", 1),
                    BitField("i_bit0", 1)),
                SBInt8("j"),
                SBInt8("k"),
                SBInt8("l"),
                LFloat32("m"),
                LFloat32("n"),
                vstring("o"),
                vstring("p"),
                vstring("q"),
                vstring("r"))
            return s

        data = b'\xc3\xc0{\x00\x01\x00\x00\x00HOqA\x12some silly text...\x00\x0e\x00\x00\x00q=jAq=zA\x02dB\x02%f\x02%f\x02%f'
        print ("\n\nNo embedding for neither g and h, i is a container --> OK")
        print build_struct(embed_g=False, embed_h=False).parse(data)
        print ("Embed both g and h, i is not a container --> FAIL")
        print build_struct(embed_g=True, embed_h=True).parse(data)
        print ("\n\nEmbed g but not h --> EXCEPTION")
        print build_struct(embed_g=True, embed_h=False).parse(data)
        # When setting optional to False in vstring method, all three tests above work fine.

