# -*- coding: utf-8 -*-

import unittest, pytest, os
from declarativeunittest import raises
ontravis = 'TRAVIS' in os.environ

from construct import *
from construct.lib import *
from construct.examples.formats import *

from io import BytesIO
import os, random, itertools, hashlib, binascii
from binascii import hexlify, unhexlify
ident = lambda x: x



def common(format, data, obj, size=None):
    assert format.parse(data) == obj
    assert format.build(obj) == data
    # following are guaranteed by the above
    # assert format.parse(format.build(obj)) == obj
    # assert format.build(format.parse(data)) == data
    if size is not None:
        if isinstance(size, Exception):
            assert raises(format.sizeof) == size
        else:
            assert format.sizeof() == size

def commondump(format, filename):
    if ontravis:
        filename = "examples/formats/" + filename
    if not ontravis:
        filename = "tests/examples/formats/" + filename
    with open(filename,'rb') as f:
        data = f.read()
    commonbytes(format, data)

def commonhex(format, hexdata):
    commonbytes(format, binascii.unhexlify(hexdata))

def commonbytes(format, data):
    obj = format.parse(data)
    print(obj)
    data2 = format.build(obj)
    print(hexlify(data))
    print(hexlify(data2))
    # assert hexlify(data2) == hexlify(data)



class TestFormats(unittest.TestCase):

    def test_png(self):
        commondump(png_file, "sample.png")

    def test_emf(self):
        commondump(emf_file, "emf1.emf")

    def test_bitmap(self):
        commondump(bitmap_file, "bitmap1.bmp")
        commondump(bitmap_file, "bitmap4.bmp")
        commondump(bitmap_file, "bitmap8.bmp")
        commondump(bitmap_file, "bitmap24.bmp")

    def test_mbr(self):
        commondump(mbr_format, "mbr1")

    def test_cap(self):
        commondump(cap_file, "cap2.cap")

    def test_snoop(self):
        commondump(snoop_file, "snoop1")

    def test_pe32file(self):
        commondump(pe32_file, "python.exe")

