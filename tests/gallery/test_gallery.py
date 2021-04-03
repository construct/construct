from tests.declarativeunittest import *
from construct import *
from construct.lib import *

from gallery import pe32file, UTIndex


def test_pe32():
    commondump(pe32file, "python37-win32.exe")
    commondump(pe32file, "python37-win64.exe")
    commondump(pe32file, "SharpZipLib0860-dotnet20.dll")
    commondump(pe32file, "sqlite3.dll")

def test_utindex():
    d = UTIndex()
    test_data = [
        [0x0f],  # 0x0f
        [0x4f, 0x40],  # (0x40 << 6) + 0x0f = 0x100f
        [0x8f],  # -0x0f
        [0xcf, 0x40],  # -((0x40 << 6) + 0x0f) = -0x100f
        [0x4f, 0x80, 0x40],  # (0x40 << 13) + 0x0f = 0x8000f
        [0x4f, 0x80, 0x80, 0x40],  # (0x40 << 20) + 0x0f = 0x400000f
        [0x4f, 0x80, 0x80, 0x80, 0x8f],  # 0x8f << 27 + 0x0f = 0x47800000f
    ]
    expected_values = [
        0x0f,
        0x100f,
        -0x0f,
        -0x100f,
        0x8000f,
        0x400000f,
        0x47800000f,
    ]
    for test, ev in zip(test_data, expected_values):
        assert d.parse(bytes(test)) == ev
        assert d.build(ev) == bytes(test)
    assert raises(d.sizeof) == SizeofError
