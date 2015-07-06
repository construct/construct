from construct.lib.binary import encode_bin, decode_bin

try:
    bytes
except NameError:
    bytes = str


class BitStreamReader(object):
    __slots__ = ["substream", "buffer", "total_size"]

    def __init__(self, substream):
        self.substream = substream
        self.total_size = 0
        self.buffer = ""

    def close(self):
        if self.total_size % 8 != 0:
            raise ValueError("total size of read data must be a multiple of 8",
                             self.total_size)

    def tell(self):
        return self.substream.tell()

    def seek(self, pos, whence=0):
        self.buffer = ""
        self.total_size = 0
        self.substream.seek(pos, whence)

    def read(self, count):
        if count < 0:
            raise ValueError("count cannot be negative")

        l = len(self.buffer)
        if count == 0:
            data = ""
        elif count <= l:
            data = self.buffer[:count]
            self.buffer = self.buffer[count:]
        else:
            data = self.buffer
            count -= l
            count_bytes = count // 8
            if count & 7:
                count_bytes += 1
            buf = encode_bin(self.substream.read(count_bytes))
            data += buf[:count]
            self.buffer = buf[count:]
        self.total_size += len(data)
        return data


class BitStreamWriter(object):
    __slots__ = ["substream", "buffer", "pos"]

    def __init__(self, substream):
        self.substream = substream
        self.buffer = []
        self.pos = 0

    def close(self):
        self.flush()

    def flush(self):
        raw = decode_bin("".join(self.buffer))
        self.substream.write(raw)
        self.buffer = []
        self.pos = 0

    def tell(self):
        return self.substream.tell() + self.pos // 8

    def seek(self, pos, whence=0):
        self.flush()
        self.substream.seek(pos, whence)

    def write(self, data):
        if not data:
            return
        if not isinstance(data, bytes):
            raise TypeError("data must be a string, not %r" % (type(data),))
        self.buffer.append(data)
