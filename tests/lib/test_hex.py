from tests.declarativeunittest import *
from construct.lib.hex import *


def test_hexdump():
    for i in range(100):
        assert hexundump(hexdump(b"?"*i,32),32) == b"?"*i

def test_hexundump_issue_882():
    data1 = (hexdump(hexundump(
"""
0000   30 31 32 33 34 35 36 5C 0123456\\
0008   38                      8

""", linesize=8), linesize=8))

    data2 = (hexdump(hexundump(
"""
0000   30 31 32 33 34 35 36 37 01234567
0008   38                      8

""", linesize=8), linesize=8))

    print(data1)
    print(data2)
    assert data1 == hexdump(b"0123456\\8", 8)
    assert data2 == hexdump(b"012345678", 8)
