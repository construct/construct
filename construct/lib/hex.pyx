from cpython cimport dict, int, bytes, list
from .py3compat import byte2int, int2byte, bytes2str


# Map an integer in the inclusive range 0-255 to its string byte representation
_PRINTABLE = dict((i, ".") for i in range(256))
_PRINTABLE.update((i, bytes2str(int2byte(i))) for i in range(32, 128))


class HexString(bytes):

    """
    Represents bytes that will be hex-dumped to a string when its string
    representation is requested.
    """

    def __init__(self, data, int linesize=16):
        self.linesize = linesize

    def __new__(cls, data, *args, **kwargs):
        return bytes.__new__(cls, data)

    def __str__(self):
        if not self:
            return "''"
        return "\n" + "\n".join(hexdump(self, self.linesize))


def hexdump(data, int linesize):
    """
    data is a bytes object. The returned result is a string.

    :param linesize:
    :param data:
    """
    prettylines = []

    if len(data) < 65536:
        fmt = "%%04X   %%-%ds   %%s"
    else:
        fmt = "%%08X   %%-%ds   %%s"

    fmt = fmt % (3 * linesize - 1,)

    for i in range(0, len(data), linesize):
        line = data[i: i + linesize]
        hextext = " ".join('%02x' % byte2int(b) for b in line)
        rawtext = "".join(_PRINTABLE[byte2int(b)] for b in line)
        prettylines.append(fmt % (i, str(hextext), str(rawtext)))
    return prettylines
