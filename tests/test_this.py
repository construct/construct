import unittest, pytest, os
from declarativeunittest import raises
ontravis = 'TRAVIS' in os.environ

from construct import *
from construct.lib import *


class TestThis(unittest.TestCase):

    def test_this(self):
        assert repr(this) == "this"

        this_example = Struct(
            # straight-forward usage: instead of passing (lambda ctx: ctx["length"]) use this.length
            "length" / Int8ub,
            "value" / Bytes(this.length),
            # an example of nesting: '_' refers to the parent's scope
            "nested" / Struct(
                "b1" / Int8ub,
                "b2" / Int8ub,
                "b3" / Computed(this.b1 * this.b2 + this._.length),
            ),
            # and conditions work as expected
            "condition" / IfThenElse(
                this.nested.b1 > 50,
                "c1" / Int32ub,
                "c2" / Int8ub,
            ),
        )
        assert this_example.parse(b"\x05helloABXXXX") == Container(length=5)(value=b'hello')(nested=Container(b1=65)(b2=66)(b3=4295))(condition=1482184792)
        assert this_example.build(dict(length=5, value=b'hello', nested=dict(b1=65, b2=66), condition=1482184792)) == b"\x05helloABXXXX"

    def test_this_getitem(self):
        gi = Struct(
            "length of text" / Int8ub,
            "text" / Bytes(this["length of text"]),
        )
        assert gi.parse(b"\x06World!") == Container({"length of text": 6, "text":b"World!"})
        assert gi.build({"length of text": 6, "text":b"World!"}) == b"\x06World!"

    def test_path(self):
        path = Path("path")
        x = ~((path.foo * 2 + 3 << 2) % 11)
        assert str(x) == 'not ((((path.foo * 2) + 3) >> 2) % 11)'
        assert repr(x) == 'not ((((path.foo * 2) + 3) >> 2) % 11)'
        assert not x(dict(foo=7))

    def test_obj(self):
        assert repr(obj_) == "obj_"
        assert repr(obj_ + 1 == 12) == "((obj_ + 1) == 12)"
        assert (obj_)(1,{}) == 1
        assert (obj_ + 10)(1,{}) == 11
        assert (obj_ == 12)(12,{})
        assert (obj_ != 12)(13,{})

    def test_functions(self):
        assert repr(len_(this.x)) == "len_(this.x)"
        assert repr(sum_(this.x)) == "sum_(this.x)"
        assert repr(len_) == "len_"
        assert repr(sum_) == "sum_"

        example = Struct(
            "items" / Byte[2],
            Check(len_(this.items) == 2),
            Check(sum_(this.items) == 10),
            Check(min_(this.items) == 3),
            Check(max_(this.items) == 7),
            "nega" / Int8sb,
            Check(this.nega == -1),
            Check(abs_(this.nega) == 1),
        )
        assert example.parse(b"\x03\x07\xff") == dict(items=[3,7], nega=-1)
        assert example.build(dict(items=[3,7], nega=-1)) == b"\x03\x07\xff"

        example = Struct(
            "items" / RepeatUntil(obj_ == 255, Byte),
        )
        assert example.parse(b"\x03\x07\xff") == dict(items=[3,7,255])
        assert example.build(dict(items=[3,7,255])) == b"\x03\x07\xff"

    @pytest.mark.xfail(reason="this does not support in operator")
    def test_this_inoperator(self):
        st1 = Struct(
            "if"  / If(this.data     in [1,2,3], Const(b"4")),
            "not" / If(this.data not in [1,2,3], Const(b"5")),
        )
        st2 = Struct(
             "if"  / If(lambda ctx: ctx.data     in [1,2,3], Const(b"4")),
             "not" / If(lambda ctx: ctx.data not in [1,2,3], Const(b"5")),
        )
        assert st1.build(data=1) == b'4'
        assert st1.build(data=7) == b'5'
        assert st2.build(data=1) == b'4'
        assert st2.build(data=7) == b'5'
