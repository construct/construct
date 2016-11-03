import unittest, pytest, os
from declarativeunittest import raises
ontravis = 'TRAVIS' in os.environ

from construct import *
from construct.lib import *

from copy import copy
from random import randint, shuffle



class TestContainer(unittest.TestCase):

    def test_ctor(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        assert c == Container(c)

    def test_ctor_dict(self):
        c = Container({'a': 1})
        d = Container(a=1)
        assert c == d

    @pytest.mark.xfail(not supportskwordered, reason="ordered kw was introduced in 3.6 and pypy")
    def test_ctor_orderedkw(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        d = Container(a=1, b=2, c=3, d=4)
        assert c == d
        assert list(c.items()) == list(d.items())

    def test_pickling(self):
        import pickle

        empty = Container()
        empty_unpickled = pickle.loads(pickle.dumps(empty))
        assert empty_unpickled == empty

        nested = Container(a=1)(b=Container())(c=3)(d=Container(e=4))
        nested_unpickled = pickle.loads(pickle.dumps(nested))
        assert nested_unpickled == nested

    def test_getitem(self):
        c = Container(a=1)
        assert c["a"] == 1
        assert c.a == 1
        assert raises(lambda: c.unknownkey) == AttributeError
        assert raises(lambda: c["unknownkey"]) == KeyError

    def test_setitem(self):
        c = Container()
        c.a = 1
        assert c["a"] == 1
        assert c.a == 1
        c["a"] = 2
        assert c["a"] == 2
        assert c.a == 2

    def test_delitem(self):
        c = Container(a=1, b=2)
        del c.a
        assert "a" not in c
        assert raises(lambda: c.a) == AttributeError
        assert raises(lambda: c["a"]) == KeyError
        del c["b"]
        assert "b" not in c
        assert raises(lambda: c.b) == AttributeError
        assert raises(lambda: c["b"]) == KeyError
        assert c == Container()

    def test_update_dict(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        d = Container()
        d.update(c)
        assert d.a == 1
        assert d.b == 2
        assert d.c == 3
        assert d.d == 4
        assert c == d
        assert list(c.items()) == list(d.items())

    def test_update_items(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        d = Container()
        d.update([("a",1),("b",2),("c",3),("d",4)])
        assert d.a == 1
        assert d.b == 2
        assert d.c == 3
        assert d.d == 4
        assert c == d
        assert list(c.items()) == list(d.items())

    def test_pop(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        assert c.pop("b") == 2
        assert c.pop("d") == 4
        assert c.pop("a") == 1
        assert c.pop("c") == 3
        assert raises(c.pop, "missing") == KeyError
        assert c == Container()

    def test_popitem(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        assert c.popitem() == ("d",4)
        assert c.popitem() == ("c",3)
        assert c.popitem() == ("b",2)
        assert c.popitem() == ("a",1)
        assert raises(c.popitem) == IndexError

    def test_clear(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        c.clear()
        assert c == Container()

    def test_items(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        assert list(c.keys()) == ["a","b","c","d"]
        assert list(c.values()) == [1,2,3,4]
        assert list(c.items()) == [("a",1),("b",2),("c",3),("d",4)]
        assert list(c) == list(c.keys())

    def test_eq(self):
        c = Container(a=1)(b=2)(c=3)(d=4)(e=5)
        d = Container(a=1)(b=2)(c=3)(d=4)(e=5)
        assert c == c
        assert c == d

    def test_ne(self):
        c = Container(a=1)(b=2)(c=3)
        d = Container(a=1)(b=2)(c=3)(d=4)(e=5)
        assert c != d
        assert d != c

    def test_ne_items(self):
        c = Container(a=1)
        d = [("a" == 1)]
        assert c != d

    def test_ne_container(self):
        c = Container(a=1)
        d = Container(b=1)
        assert c != d

    def test_ne_values(self):
        c = Container(a=1)
        d = Container(a=2)
        assert c != d

    def test_copy(self):
        c = Container(a=1)
        d = c.copy()
        assert c == d
        assert c is not d

    def test_copy2(self):
        c = Container(a=1)
        d = copy(c)
        assert c == d
        assert c is not d

    def test_len_bool(self):
        c = Container(a=1)(b=2)(c=3)(d=4)
        assert len(c) == 4
        assert c
        c = Container()
        assert len(c) == 0
        assert not c

    def test_in(self):
        c = Container(a=1)
        assert "a" in c
        assert "b" not in c

    def test_regression_recursionlock(self):
        print("REGRESSION: recursion_lock() used to leave private keys.")
        c = Container()
        str(c); repr(c)
        assert not c

    def test_str_repr_empty(self):
        c = Container()
        assert str(c) == "Container: "
        assert repr(c) == "Container()"
        assert eval(repr(c)) == c

    def test_str_repr(self):
        c = Container(a=1)(b=2)(c=3)
        assert str(c) == "Container: \n    a = 1\n    b = 2\n    c = 3"
        assert repr(c) == "Container(a=1)(b=2)(c=3)"
        assert eval(repr(c)) == c

    def test_str_repr_nested(self):
        c = Container(a=1)(b=2)(c=Container())
        assert str(c) == "Container: \n    a = 1\n    b = 2\n    c = Container: "
        assert repr(c) == "Container(a=1)(b=2)(c=Container())"
        assert eval(repr(c)) == c

    def test_str_repr_recursive(self):
        c = Container(a=1)(b=2)
        c.c = c
        assert str(c) == "Container: \n    a = 1\n    b = 2\n    c = <recursion detected>"
        assert repr(c) == "Container(a=1)(b=2)(c=<recursion detected>)"

    @pytest.mark.xfail(PY3, reason="str() produces wrong test, test to be fixed")
    def test_str_full_printing(self):
        setglobalfullprinting(True)
        c = Container(data=b"\x01\x02\x034567890")
        assert str(c) == str("Container: \n    data = \x01\x02\x034567890 (total 10)")
        c = Container(data=u"\x01\x02\x034567890")
        assert str(c) == str("Container: \n    data = \x01\x02\x034567890 (total 10)")
        c = Container(data=b"\x01"*1024)
        assert str(c) == str("Container: \n    data = \x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01... (truncated, total 1024)")
        c = Container(data=u"\x01"*1024)
        assert str(c) == str("Container: \n    data = \x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01... (truncated, total 1024)")
        setglobalfullprinting(None)


class TestFlagsContainer(unittest.TestCase):

    def test_str(self):
        c = FlagsContainer(a=True, b=False, c=True, d=False)
        assert str(c)
        assert repr(c)

    def test_eq(self):
        c = FlagsContainer(a=True, b=False, c=True, d=False)
        d = FlagsContainer(a=True, b=False, c=True, d=False)
        assert c == d


class TestListContainer(unittest.TestCase):

    def test_str(self):
        l = ListContainer(range(5))
        assert str(l)
        assert repr(l)

        l = ListContainer(range(5))
        l.append(l)
        assert str(l)
        assert repr(l)


