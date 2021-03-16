from tests.declarativeunittest import *
from construct import *
from construct.lib import *


d = Struct(
    "aa" / Int8ub,
    "ab" / Struct(
        "aba" / Int8ub,
        "abb" / Int8ub,
        "abc" / Struct(
            "abca" / Int8ub,
            "abcb" / Switch(this.abca, {
                1 : Struct("abcb1a" / Int8ub),
                2 : Struct("abcb2a" / Int8ub),
                3 : Struct("abcb3a" / Int8ub),
                4 : Struct("abcb4a" / Int8ub),
            }),
        ),
    ),
    "ac" / Int8ub,
    "ad" / GreedyRange(Struct("ada" / Int8ub)),
)

def test_search_sanity():
    obj1 = d.parse(b"\x11\x21\x22\x02\x02\x13\x51\x52")

    assert obj1.search("bb") == None
    assert obj1.search("abcb") != None
    assert obj1.search("ad") != None
    assert obj1.search("aa") == 0x11
    assert obj1.search("aba") == 0x21
    assert obj1.search("abb") == 0x22
    assert obj1.search('ac') == 0x13

def test_search_functionality():
    obj1 = d.parse(b"\x11\x21\x22\x02\x02\x13\x51\x52")
    obj2 = d.parse(b"\x11\x21\x22\x03\x03\x13\x51\x52")

    assert obj1.search('abcb1a') == None
    assert obj1.search('abcb3a') == None
    assert obj1.search('abcb4a') == None
    assert obj1.search('abcb2a') == 0x02

    assert obj2.search('abcb1a') == None
    assert obj2.search('abcb2a') == None
    assert obj2.search('abcb4a') == None
    assert obj2.search('abcb3a') == 0x03

    # Return only the first one
    assert obj1.search("ada") == 0x51

def test_search_regexp():
    obj1 = d.parse(b"\x11\x21\x22\x02\x02\x13\x51\x52")
    obj2 = d.parse(b"\x11\x21\x22\x03\x03\x13\x51\x52")

    assert obj1.search('abcb[1-4]a') == 0x02
    assert obj2.search('abcb[1-4]a') == 0x03

def test_search_all_sanity():
    obj1 = d.parse(b"\x11\x21\x22\x02\x02\x13\x51\x52")

    assert obj1.search_all("bb") == []
    assert obj1.search_all("ad") != None
    assert obj1.search_all("aa") == [0x11]
    assert obj1.search_all("aba") == [0x21]
    assert obj1.search_all("abb") == [0x22]
    assert obj1.search_all('ac') == [0x13]

def test_search_all_functionality():
    obj1 = d.parse(b"\x11\x21\x22\x02\x02\x13\x51\x52")

    # Return all of them
    assert obj1.search_all("ada") == [0x51,0x52]

def test_search_all_regexp():
    obj1 = d.parse(b"\x11\x21\x22\x02\x02\x13\x51\x52")

    assert obj1.search_all("ab.*") == [0x21, 0x22, 0x02, 0x02]
