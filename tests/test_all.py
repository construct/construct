import sys
from construct import *
from construct.lib import LazyContainer
import zlib

class ZlibCodec(object):
    encode = staticmethod(zlib.compress)
    decode = staticmethod(zlib.decompress)


# some tests require doing bad things...
import warnings
import six
import traceback
import unittest
warnings.filterwarnings("ignore", category = DeprecationWarning)


# declarative to the bitter end!
all_tests = [
    #
    # constructs
    #
    [MetaArray(lambda ctx: 3, UBInt8("metaarray")).parse, six.b("\x01\x02\x03"), [1,2,3], None],
    [MetaArray(lambda ctx: 3, UBInt8("metaarray")).parse, six.b("\x01\x02"), None, ArrayError],
    [MetaArray(lambda ctx: 3, UBInt8("metaarray")).build, [1,2,3], six.b("\x01\x02\x03"), None],
    [MetaArray(lambda ctx: 3, UBInt8("metaarray")).build, [1,2], None, ArrayError],
    
    [Range(3, 5, UBInt8("range")).parse, six.b("\x01\x02\x03"), [1,2,3], None],
    [Range(3, 5, UBInt8("range")).parse, six.b("\x01\x02\x03\x04"), [1,2,3,4], None],
    [Range(3, 5, UBInt8("range")).parse, six.b("\x01\x02\x03\x04\x05"), [1,2,3,4,5], None],
    [Range(3, 5, UBInt8("range")).parse, six.b("\x01\x02"), None, RangeError],
    [Range(3, 5, UBInt8("range")).build, [1,2,3], six.b("\x01\x02\x03"), None],
    [Range(3, 5, UBInt8("range")).build, [1,2,3,4], six.b("\x01\x02\x03\x04"), None],
    [Range(3, 5, UBInt8("range")).build, [1,2,3,4,5], six.b("\x01\x02\x03\x04\x05"), None],
    [Range(3, 5, UBInt8("range")).build, [1,2], None, RangeError],
    [Range(3, 5, UBInt8("range")).build, [1,2,3,4,5,6], None, RangeError],
    
    [RepeatUntil(lambda obj, ctx: obj == 9, UBInt8("repeatuntil")).parse, six.b("\x02\x03\x09"), [2,3,9], None],
    [RepeatUntil(lambda obj, ctx: obj == 9, UBInt8("repeatuntil")).parse, six.b("\x02\x03\x08"), None, ArrayError],
    [RepeatUntil(lambda obj, ctx: obj == 9, UBInt8("repeatuntil")).build, [2,3,9], six.b("\x02\x03\x09"), None],
    [RepeatUntil(lambda obj, ctx: obj == 9, UBInt8("repeatuntil")).build, [2,3,8], None, ArrayError],
    
    [Struct("struct", UBInt8("a"), UBInt16("b")).parse, six.b("\x01\x00\x02"), Container(a=1,b=2), None],
    [Struct("struct", UBInt8("a"), UBInt16("b"), Struct("foo", UBInt8("c"), UBInt8("d"))).parse, six.b("\x01\x00\x02\x03\x04"), Container(a=1,b=2,foo=Container(c=3,d=4)), None],
    [Struct("struct", UBInt8("a"), UBInt16("b"), Embedded(Struct("foo", UBInt8("c"), UBInt8("d")))).parse, six.b("\x01\x00\x02\x03\x04"), Container(a=1,b=2,c=3,d=4), None],
    [Struct("struct", UBInt8("a"), UBInt16("b")).build, Container(a=1,b=2), six.b("\x01\x00\x02"), None],
    [Struct("struct", UBInt8("a"), UBInt16("b"), Struct("foo", UBInt8("c"), UBInt8("d"))).build, Container(a=1,b=2,foo=Container(c=3,d=4)), six.b("\x01\x00\x02\x03\x04"), None],
    [Struct("struct", UBInt8("a"), UBInt16("b"), Embedded(Struct("foo", UBInt8("c"), UBInt8("d")))).build, Container(a=1,b=2,c=3,d=4), six.b("\x01\x00\x02\x03\x04"), None],
    
    [Sequence("sequence", UBInt8("a"), UBInt16("b")).parse, six.b("\x01\x00\x02"), [1,2], None],
    [Sequence("sequence", UBInt8("a"), UBInt16("b"), Sequence("foo", UBInt8("c"), UBInt8("d"))).parse, six.b("\x01\x00\x02\x03\x04"), [1,2,[3,4]], None],
    [Sequence("sequence", UBInt8("a"), UBInt16("b"), Embedded(Sequence("foo", UBInt8("c"), UBInt8("d")))).parse, six.b("\x01\x00\x02\x03\x04"), [1,2,3,4], None],
    [Sequence("sequence", UBInt8("a"), UBInt16("b")).build, [1,2], six.b("\x01\x00\x02"), None],
    [Sequence("sequence", UBInt8("a"), UBInt16("b"), Sequence("foo", UBInt8("c"), UBInt8("d"))).build, [1,2,[3,4]], six.b("\x01\x00\x02\x03\x04"), None],
    [Sequence("sequence", UBInt8("a"), UBInt16("b"), Embedded(Sequence("foo", UBInt8("c"), UBInt8("d")))).build, [1,2,3,4], six.b("\x01\x00\x02\x03\x04"), None],
    
    [Switch("switch", lambda ctx: 5, {1:UBInt8("x"), 5:UBInt16("y")}).parse, six.b("\x00\x02"), 2, None],
    [Switch("switch", lambda ctx: 6, {1:UBInt8("x"), 5:UBInt16("y")}).parse, six.b("\x00\x02"), None, SwitchError],
    [Switch("switch", lambda ctx: 6, {1:UBInt8("x"), 5:UBInt16("y")}, default = UBInt8("x")).parse, six.b("\x00\x02"), 0, None],
    [Switch("switch", lambda ctx: 5, {1:UBInt8("x"), 5:UBInt16("y")}, include_key = True).parse, six.b("\x00\x02"), (5, 2), None],
    [Switch("switch", lambda ctx: 5, {1:UBInt8("x"), 5:UBInt16("y")}).build, 2, six.b("\x00\x02"), None],
    [Switch("switch", lambda ctx: 6, {1:UBInt8("x"), 5:UBInt16("y")}).build, 9, None, SwitchError],
    [Switch("switch", lambda ctx: 6, {1:UBInt8("x"), 5:UBInt16("y")}, default = UBInt8("x")).build, 9, six.b("\x09"), None],
    [Switch("switch", lambda ctx: 5, {1:UBInt8("x"), 5:UBInt16("y")}, include_key = True).build, ((5, 2),), six.b("\x00\x02"), None],
    [Switch("switch", lambda ctx: 5, {1:UBInt8("x"), 5:UBInt16("y")}, include_key = True).build, ((89, 2),), None, SwitchError],
    
    [Select("select", UBInt32("a"), UBInt16("b"), UBInt8("c")).parse, six.b("\x07"), 7, None],
    [Select("select", UBInt32("a"), UBInt16("b")).parse, six.b("\x07"), None, SelectError],
    [Select("select", UBInt32("a"), UBInt16("b"), UBInt8("c"), include_name = True).parse, six.b("\x07"), ("c", 7), None],
    [Select("select", UBInt32("a"), UBInt16("b"), UBInt8("c")).build, 7, six.b("\x00\x00\x00\x07"), None],
    [Select("select", UBInt32("a"), UBInt16("b"), UBInt8("c"), include_name = True).build, (("c", 7),), six.b("\x07"), None],
    [Select("select", UBInt32("a"), UBInt16("b"), UBInt8("c"), include_name = True).build, (("d", 7),), None, SelectError],
    
    [Peek(UBInt8("peek")).parse, six.b("\x01"), 1, None],
    [Peek(UBInt8("peek")).parse, six.b(""), None, None],
    [Peek(UBInt8("peek")).build, 1, six.b(""), None],
    [Peek(UBInt8("peek"), perform_build = True).build, 1, six.b("\x01"), None],
    [Struct("peek", Peek(UBInt8("a")), UBInt16("b")).parse, six.b("\x01\x02"), Container(a=1,b=0x102), None],
    [Struct("peek", Peek(UBInt8("a")), UBInt16("b")).build, Container(a=1,b=0x102), six.b("\x01\x02"), None],
    
    [Value("value", lambda ctx: "moo").parse, six.b(""), "moo", None],
    [Value("value", lambda ctx: "moo").build, None, six.b(""), None],
    
    [Anchor("anchor").parse, six.b(""), 0, None],
    [Anchor("anchor").build, None, six.b(""), None],
    
    [LazyBound("lazybound", lambda: UBInt8("foo")).parse, six.b("\x02"), 2, None],
    [LazyBound("lazybound", lambda: UBInt8("foo")).build, 2, six.b("\x02"), None],
    
    [Pass.parse, six.b(""), None, None],
    [Pass.build, None, six.b(""), None],

    [Terminator.parse, six.b(""), None, None],
    [Terminator.parse, six.b("x"), None, TerminatorError],
    [Terminator.build, None, six.b(""), None],
    
    [Pointer(lambda ctx: 2, UBInt8("pointer")).parse, six.b("\x00\x00\x07"), 7, None],
    [Pointer(lambda ctx: 2, UBInt8("pointer")).build, 7, six.b("\x00\x00\x07"), None],
    
    [OnDemand(UBInt8("ondemand")).parse(six.b("\x08")).read, (), 8, None],
    [Struct("ondemand", UBInt8("a"), OnDemand(UBInt8("b")), UBInt8("c")).parse, 
        six.b("\x07\x08\x09"), Container(a=7,b=LazyContainer(None, None, None, None),c=9), None],
    [Struct("ondemand", UBInt8("a"), OnDemand(UBInt8("b"), advance_stream = False), UBInt8("c")).parse, 
        six.b("\x07\x09"), Container(a=7,b=LazyContainer(None, None, None, None),c=9), None],
    
    [OnDemand(UBInt8("ondemand")).build, 8, six.b("\x08"), None],
    [Struct("ondemand", UBInt8("a"), OnDemand(UBInt8("b")), UBInt8("c")).build, 
        Container(a=7,b=8,c=9), six.b("\x07\x08\x09"), None],
    [Struct("ondemand", UBInt8("a"), OnDemand(UBInt8("b"), force_build = False), UBInt8("c")).build, 
        Container(a=7,b=LazyContainer(None, None, None, None),c=9), six.b("\x07\x00\x09"), None],
    [Struct("ondemand", UBInt8("a"), OnDemand(UBInt8("b"), force_build = False, advance_stream = False), UBInt8("c")).build, 
        Container(a=7,b=LazyContainer(None, None, None, None),c=9), six.b("\x07\x09"), None],
    
    [Struct("reconfig", Reconfig("foo", UBInt8("bar"))).parse, six.b("\x01"), Container(foo=1), None],
    [Struct("reconfig", Reconfig("foo", UBInt8("bar"))).build, Container(foo=1), six.b("\x01"), None],
    
    [Buffered(UBInt8("buffered"), lambda x:x, lambda x:x, lambda x:x).parse, 
        six.b("\x07"), 7, None],
    [Buffered(GreedyRange(UBInt8("buffered")), lambda x:x, lambda x:x, lambda x:x).parse, 
        six.b("\x07"), None, SizeofError],
    [Buffered(UBInt8("buffered"), lambda x:x, lambda x:x, lambda x:x).build, 
        7, six.b("\x07"), None],
    [Buffered(GreedyRange(UBInt8("buffered")), lambda x:x, lambda x:x, lambda x:x).build, 
        [7], None, SizeofError],
    
    [Restream(UBInt8("restream"), lambda x:x, lambda x:x, lambda x:x).parse,
        six.b("\x07"), 7, None],
    [Restream(GreedyRange(UBInt8("restream")), lambda x:x, lambda x:x, lambda x:x).parse,
        six.b("\x07"), [7], None],
    [Restream(UBInt8("restream"), lambda x:x, lambda x:x, lambda x:x).parse,
        six.b("\x07"), 7, None],
    [Restream(GreedyRange(UBInt8("restream")), lambda x:x, lambda x:x, lambda x:x).parse,
        six.b("\x07"), [7], None],
    
    #
    # adapters
    #
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8).parse, six.b("\x01") * 8, 255, None],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8, signed_value = True).parse, six.b("\x01") * 8, -1, None],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8, swapped = True, bytesize = 4).parse, 
        six.b("\x01") * 4 + six.b("\x00") * 4, 0x0f, None],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8).build, 255, six.b("\x01") * 8, None],
    [BitIntegerAdapter(Field("bitintegeradapter", lambda c: 8), lambda c: 8).build, 255, six.b("\x01") * 8, None],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8).build, -1, None, BitIntegerError],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8, signed_value = True).build, -1, six.b("\x01") * 8, None],
    [BitIntegerAdapter(Field("bitintegeradapter", 8), 8, swapped = True, bytesize = 4).build, 
        0x0f, six.b("\x01") * 4 + six.b("\x00") * 4, None],
    
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x",3:"y"}, {"x":2,"y":3}).parse,
        six.b("\x03"), "y", None],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x",3:"y"}, {"x":2,"y":3}).parse,
        six.b("\x04"), None, MappingError],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x",3:"y"}, {"x":2,"y":3}, decdefault="foo").parse,
        six.b("\x04"), "foo", None],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x",3:"y"}, {"x":2,"y":3}, decdefault=Pass).parse,
        six.b("\x04"), 4, None],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x",3:"y"}, {"x":2,"y":3}).build,
        "y", six.b("\x03"), None],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x",3:"y"}, {"x":2,"y":3}).build,
        "z", None, MappingError],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x",3:"y"}, {"x":2,"y":3}, encdefault=17).build,
        "foo", six.b("\x11"), None],
    [MappingAdapter(UBInt8("mappingadapter"), {2:"x",3:"y"}, {"x":2,"y":3}, encdefault=Pass).build,
        4, six.b("\x04"), None],
        
    [FlagsAdapter(UBInt8("flagsadapter"), {"a":1,"b":2,"c":4,"d":8,"e":16,"f":32,"g":64,"h":128}).parse, 
        six.b("\x81"), Container(a=True, b=False,c=False,d=False,e=False,f=False,g=False,h=True), None],
    [FlagsAdapter(UBInt8("flagsadapter"), {"a":1,"b":2,"c":4,"d":8,"e":16,"f":32,"g":64,"h":128}).build, 
        Container(a=True, b=False,c=False,d=False,e=False,f=False,g=False,h=True), six.b("\x81"), None],
    
    [IndexingAdapter(Array(3, UBInt8("indexingadapter")), 2).parse, six.b("\x11\x22\x33"), 0x33, None],
    [IndexingAdapter(Array(3, UBInt8("indexingadapter")), 2)._encode, (0x33, {}), [None, None, 0x33], None],
    
    [SlicingAdapter(Array(3, UBInt8("indexingadapter")), 1, 3).parse, six.b("\x11\x22\x33"), [0x22, 0x33], None],
    [SlicingAdapter(Array(3, UBInt8("indexingadapter")), 1, 3)._encode, ([0x22, 0x33], {}), [None, 0x22, 0x33], None],
    
    [PaddingAdapter(Field("paddingadapter", 4)).parse, six.b("abcd"), six.b("abcd"), None],
    [PaddingAdapter(Field("paddingadapter", 4), strict = True).parse, six.b("abcd"), None, PaddingError],
    [PaddingAdapter(Field("paddingadapter", 4), strict = True).parse, six.b("\x00\x00\x00\x00"), six.b("\x00\x00\x00\x00"), None],
    [PaddingAdapter(Field("paddingadapter", 4)).build, six.b("abcd"), six.b("\x00\x00\x00\x00"), None],
    
    [LengthValueAdapter(Sequence("lengthvalueadapter", UBInt8("length"), Field("value", lambda ctx: ctx.length))).parse,
        six.b("\x05abcde"), six.b("abcde"), None],
    [LengthValueAdapter(Sequence("lengthvalueadapter", UBInt8("length"), Field("value", lambda ctx: ctx.length))).build,
        six.b("abcde"), six.b("\x05abcde"), None],
        
    [TunnelAdapter(PascalString("data", encoding = ZlibCodec), GreedyRange(UBInt16("elements"))).parse, 
        six.b("\rx\x9cc`f\x18\x16\x10\x00u\xf8\x01-"), [3] * 100, None],
    [TunnelAdapter(PascalString("data", encoding = ZlibCodec), GreedyRange(UBInt16("elements"))).build, 
        [3] * 100, six.b("\rx\x9cc`f\x18\x16\x10\x00u\xf8\x01-"), None],
    
    [Const(Field("const", 2), six.b("MZ")).parse, six.b("MZ"), six.b("MZ"), None],
    [Const(Field("const", 2), six.b("MZ")).parse, six.b("MS"), None, ConstError],
    [Const(Field("const", 2), six.b("MZ")).build, six.b("MZ"), six.b("MZ"), None],
    [Const(Field("const", 2), six.b("MZ")).build, six.b("MS"), None, ConstError],
    [Const(Field("const", 2), six.b("MZ")).build, None, six.b("MZ"), None],
    
    [ExprAdapter(UBInt8("expradapter"), 
        encoder = lambda obj, ctx: obj // 7, 
        decoder = lambda obj, ctx: obj * 7).parse, 
        six.b("\x06"), 42, None],
    [ExprAdapter(UBInt8("expradapter"), 
        encoder = lambda obj, ctx: obj // 7, 
        decoder = lambda obj, ctx: obj * 7).build, 
        42, six.b("\x06"), None],
   
    #
    # macros
    #
    [Aligned(UBInt8("aligned")).parse, six.b("\x01\x00\x00\x00"), 1, None],
    [Aligned(UBInt8("aligned")).build, 1, six.b("\x01\x00\x00\x00"), None],
    [Struct("aligned", Aligned(UBInt8("a")), UBInt8("b")).parse, 
        six.b("\x01\x00\x00\x00\x02"), Container(a=1,b=2), None],
    [Struct("aligned", Aligned(UBInt8("a")), UBInt8("b")).build, 
        Container(a=1,b=2), six.b("\x01\x00\x00\x00\x02"), None],
    
    [Bitwise(Field("bitwise", 8)).parse, six.b("\xff"), six.b("\x01") * 8, None],
    [Bitwise(Field("bitwise", lambda ctx: 8)).parse, six.b("\xff"), six.b("\x01") * 8, None],
    [Bitwise(Field("bitwise", 8)).build, six.b("\x01") * 8, six.b("\xff"), None],
    [Bitwise(Field("bitwise", lambda ctx: 8)).build, six.b("\x01") * 8, six.b("\xff"), None],
    
    [Union("union", 
        UBInt32("a"), 
        Struct("b", UBInt16("a"), UBInt16("b")), 
        BitStruct("c", Padding(4), Octet("a"), Padding(4)), 
        Struct("d", UBInt8("a"), UBInt8("b"), UBInt8("c"), UBInt8("d")),
        Embedded(Struct("q", UBInt8("e"))),
        ).parse,
        six.b("\x11\x22\x33\x44"),
        Container(a=0x11223344, 
            b=Container(a=0x1122, b=0x3344), 
            c=Container(a=0x12),
            d=Container(a=0x11, b=0x22, c=0x33, d=0x44),
            e=0x11,
        ),
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
        six.b("\x11\x22\x33\x44"),
        None],

    [Enum(UBInt8("enum"),q=3,r=4,t=5).parse, six.b("\x04"), "r", None],
    [Enum(UBInt8("enum"),q=3,r=4,t=5).parse, six.b("\x07"), None, MappingError],
    [Enum(UBInt8("enum"),q=3,r=4,t=5, _default_ = "spam").parse, six.b("\x07"), "spam", None],
    [Enum(UBInt8("enum"),q=3,r=4,t=5, _default_ =Pass).parse, six.b("\x07"), 7, None],
    [Enum(UBInt8("enum"),q=3,r=4,t=5).build, "r", six.b("\x04"), None],
    [Enum(UBInt8("enum"),q=3,r=4,t=5).build, "spam", None, MappingError],
    [Enum(UBInt8("enum"),q=3,r=4,t=5, _default_ = 9).build, "spam", six.b("\x09"), None],
    [Enum(UBInt8("enum"),q=3,r=4,t=5, _default_ =Pass).build, 9, six.b("\x09"), None],

    [PrefixedArray(UBInt8("array"), UBInt8("count")).parse, six.b("\x03\x01\x01\x01"), [1,1,1], None],
    [PrefixedArray(UBInt8("array"), UBInt8("count")).parse, six.b("\x03\x01\x01"), None, ArrayError],
    [PrefixedArray(UBInt8("array"), UBInt8("count")).sizeof, [1,1,1], 4, None],
    [PrefixedArray(UBInt8("array"), UBInt8("count")).build, [1,1,1], six.b("\x03\x01\x01\x01"), None],
    
    [IfThenElse("ifthenelse", lambda ctx: True, UBInt8("then"), UBInt16("else")).parse, 
        six.b("\x01"), 1, None],
    [IfThenElse("ifthenelse", lambda ctx: False, UBInt8("then"), UBInt16("else")).parse, 
        six.b("\x00\x01"), 1, None],
    [IfThenElse("ifthenelse", lambda ctx: True, UBInt8("then"), UBInt16("else")).build, 
        1, six.b("\x01"), None],
    [IfThenElse("ifthenelse", lambda ctx: False, UBInt8("then"), UBInt16("else")).build, 
        1, six.b("\x00\x01"), None],
    
    [Magic(six.b("MZ")).parse, six.b("MZ"), six.b("MZ"), None],
    [Magic(six.b("MZ")).parse, six.b("ELF"), None, ConstError],
    [Magic(six.b("MZ")).build, None, six.b("MZ"), None],
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

if __name__ == "__main__":
    unittest.main()
