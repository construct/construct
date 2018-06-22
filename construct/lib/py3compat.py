import sys

PY = sys.version_info[:2]
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PYPY = '__pypy__' in sys.builtin_module_names

try:
    import numpy
    supportsnumpy = True
except ImportError:
    supportsnumpy = False
try:
    import ruamel.yaml
    assert PY3
    supportsksyexport = True
except (ImportError, AssertionError):
    supportsksyexport = False
try:
    from enum import IntEnum
    supportsintenum = True
except ImportError:
    supportsintenum = False
try:
    from enum import IntFlag
    supportsintflag = True
except ImportError:
    supportsintflag = False

supportskwordered = PY >= (3,6) or PYPY
supportshalffloats = PY >= (3,6)


if PY3:
    #: PY2: str unicode
    #: PY3: bytes str
    stringtypes = (bytes, str, )
    #: PY2: int long
    #: PY3: int
    integertypes = (int, )
    #: PY2: unicode
    #: PY3: str
    unicodestringtype = str
    #: PY2: str
    #: PY3: bytes
    bytestringtype = bytes

    INT2BYTE_CACHE = {i:bytes((i,)) for i in range(256)}
    def int2byte(character):
        """Converts (0 through 255) integer into b'...' character."""
        return INT2BYTE_CACHE[character]

    def byte2int(character):
        """Converts b'...' character into (0 through 255) integer."""
        return ord(character)

    def str2bytes(string):
        """Converts '...' string into b'...' string. On PY2 they are equivalent. On PY3 its utf8 encoded."""
        return string.encode("utf8")

    def bytes2str(string):
        """Converts b'...' string into '...' string. On PY2 they are equivalent. On PY3 its utf8 decoded."""
        return string.decode("utf8")

    def str2unicode(string):
        """Converts '...' string into u'...' string. On PY2 its utf8 encoded. On PY3 they are equivalent."""
        return string

    def unicode2str(string):
        """Converts u'...' string into '...' string. On PY2 its utf8 decoded. On PY3 they are equivalent."""
        return string

    ITERATEBYTES_CACHE = {i:bytes((i,)) for i in range(256)}
    def iteratebytes(data):
        """Iterates though b'...' string yielding b'...' characters."""
        return (ITERATEBYTES_CACHE[i] for i in data)

    def iterateints(data):
        """Iterates though b'...' string yielding (0 through 255) integers."""
        return data

    def reprstring(data):
        """Ensures there is b- u- prefix before the string."""
        if isinstance(data, bytes):
            return repr(data)
        if isinstance(data, str):
            return 'u' + repr(data)

    def trimstring(data):
        """Trims b- u- prefix"""
        if isinstance(data, bytes):
            return repr(data)[1:]
        if isinstance(data, str):
            return repr(data)

    import builtins
    bytes = builtins.bytes

    def integers2bytes(ints):
        """Converts integer generator into bytes."""
        return bytes(ints)

    def bytes2integers(data):
        """Converts bytes into bytes/bytearray, so indexing/iterating yields integers."""
        return data


else:
    #: PY2: str unicode
    #: PY3: bytes str
    stringtypes = (str, unicode, )
    #: PY2: int long
    #: PY3: int
    integertypes = (long, int, )
    #: PY2: unicode
    #: PY3: str
    unicodestringtype = unicode
    #: PY2: str
    #: PY3: bytes
    bytestringtype = str

    def int2byte(character):
        """Converts (0 through 255) integer into b'...' character."""
        return chr(character)

    def byte2int(character):
        """Converts b'...' character into (0 through 255) integer."""
        return ord(character)

    def str2bytes(string):
        """Converts '...' string into b'...' string. On PY2 they are equivalent. On PY3 its utf8 encoded."""
        return string

    def bytes2str(string):
        """Converts b'...' string into '...' string. On PY2 they are equivalent. On PY3 its utf8 decoded."""
        return string

    def str2unicode(string):
        """Converts '...' string into u'...' string. On PY2 its utf8 encoded. On PY3 they are equivalent."""
        return string.encode("utf8")

    def unicode2str(string):
        """Converts u'...' string into '...' string. On PY2 its utf8 decoded. On PY3 they are equivalent."""
        return string.decode("utf8")

    def iteratebytes(data):
        """Iterates though b'...' string yielding b'...' characters."""
        return data

    def iterateints(data):
        """Iterates though b'...' string yielding (0 through 255) integers."""
        return bytearray(data)

    def reprstring(data):
        """Ensures there is b- u- prefix before the string."""
        if isinstance(data, str):
            return 'b' + repr(data)
        if isinstance(data, unicode):
            return repr(data)

    def trimstring(data):
        """Trims b- u- prefix"""
        if isinstance(data, str):
            return repr(data)
        if isinstance(data, unicode):
            return repr(data)[1:]

    def bytes(countorseq=0):
        """Backports bytes() from PY3."""
        if isinstance(countorseq, integertypes):
            return b"\x00" * countorseq
        else:
            return b"".join(chr(x) for x in countorseq)

    def integers2bytes(ints):
        """Converts integer generator into bytes."""
        return bytes(bytearray(ints))

    def bytes2integers(data):
        """Converts bytes into bytes/bytearray, so indexing/iterating yields integers."""
        return bytearray(data)
