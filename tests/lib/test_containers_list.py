from tests.declarativeunittest import *
from construct import *
from construct.lib import *


def test_str():
    l = ListContainer(range(5))
    assert str(l) == "ListContainer: \n    0\n    1\n    2\n    3\n    4"
    assert repr(l) == "ListContainer([0, 1, 2, 3, 4])"

    l = ListContainer(range(5))
    print(repr(str(l)))
    print(repr((l)))
    l.append(l)
    assert str(l) == "ListContainer: \n    0\n    1\n    2\n    3\n    4\n    <recursion detected>"
    assert repr(l) == "ListContainer([0, 1, 2, 3, 4, <recursion detected>])"
