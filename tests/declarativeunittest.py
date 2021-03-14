import pytest
import platform
import io

xfail = pytest.mark.xfail
skip = pytest.mark.skip
skipif = pytest.mark.skipif

import os, math, random, collections, itertools, io, hashlib, binascii, tempfile

from construct import *
from construct.lib import *

ident = lambda x: x
if platform.system() == "Windows":
    class ZeroIO(io.BufferedIOBase):
        def read(self, __size=None):
            if __size is not None:
                return bytes(__size)
            else:
                return bytes(0)

        def read1(self, __size=0):
            return bytes(__size)

    devzero = ZeroIO()
else:    
    devzero = open("/dev/zero", "rb")

        

def raises(func, *args, **kw):
    try:
        return func(*args, **kw)
    except Exception as e:
        return e.__class__


def common(format, datasample, objsample, sizesample=SizeofError, **kw):
    obj = format.parse(datasample, **kw)
    assert obj == objsample
    data = format.build(objsample, **kw)
    assert data == datasample
    # following are implied by above (re-parse and re-build)
    # assert format.parse(format.build(obj)) == obj
    # assert format.build(format.parse(data)) == data
    if isinstance(sizesample, int):
        size = format.sizeof(**kw)
        assert size == sizesample
    else:
        size = raises(format.sizeof, **kw)
        assert size == sizesample


def commonhex(format, hexdata):
    commonbytes(format, binascii.unhexlify(hexdata))


def commondumpdeprecated(format, filename):
    filename = "tests/deprecated_gallery/blobs/" + filename
    with open(filename,'rb') as f:
        data = f.read()
    commonbytes(format, data)


def commondump(format, filename):
    filename = "tests/gallery/blobs/" + filename
    with open(filename,'rb') as f:
        data = f.read()
    commonbytes(format, data)


def commonbytes(format, data):
    obj = format.parse(data)
    data2 = format.build(obj)
