from tests.declarativeunittest import *
from construct import *
from construct.lib import *


def test_path():
    path = Path("path")
    x = ~((path.foo * 2 + 3 << 2) % 11)
    assert repr(x) == "not ((((path['foo'] * 2) + 3) << 2) % 11)"
    assert str(x) == "not ((((path['foo'] * 2) + 3) << 2) % 11)"
    assert x(dict(foo=7)) == False

def test_this():
    assert repr(this.x) == "this['x']"
    assert str(this.x) == "this['x']"
    assert repr(this.x == 0) == "(this['x'] == 0)"
    assert str(this.x == 0) == "(this['x'] == 0)"

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
    common(this_example, b"\x05helloABXXXX", Container(length=5, value=b'hello', nested=Container(b1=65, b2=66, b3=4295), condition=1482184792))

def test_this_getitem():
    d = Struct(
        "num" / Int8ub,
        "dup1" / Computed(this.num),
        "dup2" / Computed(this["num"]),
        Check(this.num == 0),
        Check(this.dup1 == 0),
        Check(this.dup2 == 0),
    )
    common(d, b"\x00", Container(num=0, dup1=0, dup2=0), 1)

def test_functions():
    assert repr(len_(this.x)) == "len_(this['x'])"
    assert str(len_(this.x)) == "len_(this['x'])"
    assert repr(len_) == "len_"
    assert str(len_) == "len_"

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
    common(example, b"\x03\x07\xff", Container(items=[3,7], nega=-1), 3)

def test_obj():
    assert repr(obj_) == "obj_"
    assert repr(obj_ + 1 == 12) == "((obj_ + 1) == 12)"
    assert str(obj_) == "obj_"
    assert str(obj_ + 1 == 12) == "((obj_ + 1) == 12)"

    assert (obj_)(1,{}) == 1
    assert (obj_ + 10)(1,{}) == 11
    assert (obj_ == 12)(12,{})
    assert (obj_ != 12)(13,{})

    assert (obj_)(1,[],{}) == 1
    assert (obj_ + 10)(1,[],{}) == 11
    assert (obj_ == 12)(12,[],{})
    assert (obj_ != 12)(13,[],{})

    example = Struct(
        "items" / RepeatUntil(obj_ == 255, Byte),
    )
    common(example, b"\x03\x07\xff", Container(items=[3,7,255]))

@xfail(reason="faulty implementation, needs fixing")
def test_list():
    assert repr(list_) == "list_"
    assert str(list_) == "list_"
    assert repr(list_ == [0, 1, 2]) == "(list_ == [0, 1, 2])"
    assert str(list_ == [0, 1, 2]) == "(list_ == [0, 1, 2])"
    assert repr(list_[-1]) == "list_[-1]"
    assert str(list_[-1]) == "list_[-1]"
    assert repr(list_[-1] == 0) == "(list_[-1] == 0)"
    assert str(list_[-1] == 0) == "(list_[-1] == 0)"
    assert repr(list_[-1] + 1) == "(list_[-1] + 1)"
    assert str(list_[-1] + 1) == "(list_[-1] + 1)"
    # missing str

    assert (list_)(1,[],{}) == []
    assert (list_[-1])(1,[2,3,4],{}) == 4
    # below fail
    assert (list_[-1] + 1)(1,[2,3,4],{}) == 5
    assert (list_[-1] == 4)(1,[2,3,4],{}) == True
    assert (len_(list_))(1,[2,3,4],{}) == 3
    assert (len_(list_[:]))(1,[2,3,4],{}) == 3

    example = Struct(
        "items" / RepeatUntil(list_[-1] == 255, Byte),
    )
    common(example, b"\x03\x07\xff", Container(items=[3,7,255]))

@xfail(reason="this expression does not support in operator")
def test_this_in_operator():
    d = Struct(
        "if"  / If(this.data     in [1,2,3], Const(b"4")),
        "not" / If(this.data not in [1,2,3], Const(b"5")),
    )
    assert d.build(dict(data=1)) == b'4'
    assert d.build(dict(data=7)) == b'5'

def test_lambda_in_operator():
    d = Struct(
         "if"  / If(lambda ctx: ctx.data     in [1,2,3], Const(b"4")),
         "not" / If(lambda ctx: ctx.data not in [1,2,3], Const(b"5")),
    )
    assert d.build(dict(data=1)) == b'4'
    assert d.build(dict(data=7)) == b'5'

def test_this_shift_operator():
    d = Struct(
       "a" / Byte,
       "ls" / Computed(this.a << 1),
       "rs" / Computed(this.a >> 1),
    )
    assert d.parse(b"\x02") == Container(a=2, ls=4, rs=1)
