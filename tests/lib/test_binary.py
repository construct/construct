from tests.declarativeunittest import *
from construct.lib.binary import *


def test_integer2bits():
    assert integer2bits(0, 0, False) == b""
    assert integer2bits(0, 0, True) == b""
    assert integer2bits(19, 5) == b"\x01\x00\x00\x01\x01"
    assert integer2bits(19, 8) == b"\x00\x00\x00\x01\x00\x00\x01\x01"
    assert integer2bits(-13, 5, True) == b"\x01\x00\x00\x01\x01"
    assert integer2bits(-13, 8, True) == b"\x01\x01\x01\x01\x00\x00\x01\x01"
    assert raises(integer2bits, 0, -1) == ValueError
    assert raises(integer2bits, -1, 8, False) == ValueError
    assert raises(integer2bits, -2**64, 8, True) == ValueError
    assert raises(integer2bits,  2**64, 8, True) == ValueError
    assert raises(integer2bits, -2**64, 8, False) == ValueError
    assert raises(integer2bits,  2**64, 8, False) == ValueError

def test_integer2bytes():
    assert integer2bytes(0, 0, False) == b""
    assert integer2bytes(0, 0, True) == b""
    assert integer2bytes(0, 4) == b"\x00\x00\x00\x00"
    assert integer2bytes(1, 4) == b"\x00\x00\x00\x01"
    assert integer2bytes(19, 4) == b'\x00\x00\x00\x13'
    assert integer2bytes(255, 1) == b"\xff"
    assert integer2bytes(255, 4) == b"\x00\x00\x00\xff"
    assert integer2bytes(-1, 4, True) == b"\xff\xff\xff\xff"
    assert integer2bytes(-255, 4, True) == b"\xff\xff\xff\x01"
    assert raises(integer2bytes, 0, -1) == ValueError
    assert raises(integer2bytes, -1, 8, False) == ValueError
    assert raises(integer2bytes, -2**64, 4, True) == ValueError
    assert raises(integer2bytes,  2**64, 4, True) == ValueError
    assert raises(integer2bytes, -2**64, 4, False) == ValueError
    assert raises(integer2bytes,  2**64, 4, False) == ValueError

def test_bits2integer():
    assert bits2integer(b"", False) == 0
    assert bits2integer(b"", True) == 0
    assert bits2integer(b"\x01\x00\x00\x01\x01", False) == 19
    assert bits2integer(b"\x01\x00\x00\x01\x01", True) == -13

def test_bytes2integer():
    assert bytes2integer(b"", False) == 0
    assert bytes2integer(b"", True) == 0
    assert bytes2integer(b"\x00") == 0
    assert bytes2integer(b"\x00", True) == 0
    assert bytes2integer(b"\xff") == 255
    assert bytes2integer(b"\xff", True) == -1
    assert bytes2integer(b'\x00\x00\x00\x13', False) == 19
    assert bytes2integer(b'\x00\x00\x00\x13', True) == 19

def test_cross_integers():
    for i in [-300,-255,-100,-1,0,1,100,255,300]:
        assert bits2integer(integer2bits(i,64,signed=(i<0)),signed=(i<0)) == i
        assert bytes2integer(integer2bytes(i,8,signed=(i<0)),signed=(i<0)) == i
        assert bits2bytes(integer2bits(i,64,signed=(i<0))) == integer2bytes(i,8,signed=(i<0))
        assert bytes2bits(integer2bytes(i,8,signed=(i<0))) == integer2bits(i,64,signed=(i<0))

def test_bytes2bits():
    assert bytes2bits(b"") == b""
    assert bytes2bits(b"ab") == b"\x00\x01\x01\x00\x00\x00\x00\x01\x00\x01\x01\x00\x00\x00\x01\x00"

def test_bits2bytes():
    assert bits2bytes(b"") == b""
    assert bits2bytes(b"\x00\x01\x01\x00\x00\x00\x00\x01\x00\x01\x01\x00\x00\x00\x01\x00") == b"ab"
    assert raises(bits2bytes, b"\x00") == ValueError
    assert raises(bits2bytes, b"\x00\x00\x00\x00\x00\x00\x00") == ValueError

def test_swapbytes():
    assert swapbytes(b"") == b""
    assert swapbytes(b"abcd") == b"dcba"

def test_swapbytesinbits():
    assert swapbytesinbits(b"") == b""
    assert swapbytesinbits(b"0000000011111111") == b"1111111100000000"
    assert raises(swapbytesinbits, b"1") == ValueError

def test_swapbitsinbytes():
    assert swapbitsinbytes(b"") == b""
    assert swapbitsinbytes(b"\xf0") == b"\x0f"
    assert swapbitsinbytes(b"\xf0\x00") == b"\x0f\x00"
