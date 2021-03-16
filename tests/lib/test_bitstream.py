from tests.declarativeunittest import *
from construct.lib.bitstream import *


def test_restreamed():
    # tested by Bitwise Bytewise ByteSwapped BitsSwapped cases
    pass

def test_rebuffered():
    z = b"0"

    print("sequential read")
    bstream = RebufferedBytesIO(io.BytesIO(z*1000))
    assert bstream.read(1000) == z*1000

    print("random reads")
    data = os.urandom(1000)
    bstream = RebufferedBytesIO(io.BytesIO(data))
    for i in range(50):
        o1 = random.randrange(0, 480)
        o2 = random.randrange(520, 1000)
        assert bstream.seek(o1) == o1
        assert bstream.tell() == o1
        assert bstream.read(o2-o1) == data[o1:o2]
        assert bstream.tell() == o2

    print("sequential writes")
    bstream = RebufferedBytesIO(io.BytesIO())
    for i in range(10):
        assert bstream.write(z*100) == 100
    assert bstream.seek(0) == 0
    assert bstream.read(1000) == z*1000

    print("random writes")
    data = os.urandom(1000)
    bstream = RebufferedBytesIO(io.BytesIO())
    assert bstream.write(data) == len(data)
    for i in range(50):
        o1 = random.randrange(0, 480)
        o2 = random.randrange(520, 1000)
        assert bstream.seek(o1) == o1
        assert bstream.tell() == o1
        assert bstream.write(data[o1:o2]) == o2-o1
        assert bstream.tell() == o2
    assert bstream.seek(0) == 0
    assert bstream.read(len(data)) == data

    print("cutting off trail")
    data = os.urandom(1000)
    bstream = RebufferedBytesIO(io.BytesIO(data), tailcutoff=50)
    for i in range(15):
        at = bstream.tell()
        assert bstream.read(50) == data[at:at+50]
        jumpback = random.randrange(1, 19)
        assert bstream.seek(-jumpback, 1)
