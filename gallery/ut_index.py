import sys
sys.path = [".."] + sys.path  # Use construct from repo, not pip
from construct import (
    Construct,
    byte2int,
    int2byte,
    stream_read,
    stream_write,
    integertypes,
    IntegerError,
    Struct,
)


class Idx(Construct):
    """
    Format for "Index" objects in Unreal Tournament 1999 packages.
    Index objects are variable length signed integers with the following structure:

    +------------------------------------+-------------------------+--------------+
    | Byte 0                             | Bytes 1-3               | Byte 4       |
    +----------+----------+--------------+----------+--------------+--------------+
    | Sign Bit | More Bit | Data Bits[6] | More Bit | Data Bits[7] | Data Bits[8] |
    +----------+----------+--------------+----------+--------------+--------------+

    If the "More" bit is 0 in any byte, that's the end of the Index. Otherwise,
    keep going. There cannot be more than 5 bytes in an Index so Byte 4 doesn't
    have a "More" bit.
    """
    lengths = {0: 6, 1: 7, 2: 7, 3: 7, 4: 8}
    negative_bit = 0x80

    @staticmethod
    def _get_data_mask(length):
        return (0xFF ^ (0xFF << length)) & 0xFF

    @staticmethod
    def _get_more_bit(length):
        return 1 << length

    def _parse(self, stream, context, path):
        result = 0
        sign = 1
        i = 0
        depth = 0
        while True:
            length = self.lengths[i]
            bits = byte2int(stream_read(stream, 1, path))
            mask = self._get_data_mask(length)
            data = bits & mask
            more = self._get_more_bit(length) & bits
            if (i == 0) and (self.negative_bit & bits):
                sign = -1
            result |= data << depth
            if not more:
                break
            i += 1
            depth += length
        return sign * result

    def _build(self, obj, stream, context, path):
        if not isinstance(obj, integertypes):
            raise IntegerError("Value is not an integer")
        to_write = obj
        for i in range(5):
            byte = 0
            length = self.lengths[i]
            if i == 0:
                negative = obj < 0
                byte |= self.negative_bit * negative
                if negative:
                    to_write *= -1
            mask = self._get_data_mask(length)
            byte |= to_write & mask
            to_write >>= length
            more_bit = (to_write > 0) and self._get_more_bit(length)
            byte |= more_bit
            byte &= 0xFF
            stream_write(stream, int2byte(byte), 1, path)
            if not more_bit:
                break
        return obj


if __name__ == "__main__":
    c = Struct("index" / Idx())
    test_data = [
        [0x0f, 0x40, 0xff],  # 0x0f
        [0x4f, 0x40, 0xff],  # (0x40 << 6) + 0x0f = 0x100f
        [0x8f, 0x40, 0xff],  # -0x0f
        [0xcf, 0x40, 0xff],  # -((0x40 << 6) + 0x0f) = 0x100f
        [0x4f, 0x80, 0x40, 0xff],  # (0x40 << 13) + 0x0f = 0x8000f
        [0x4f, 0x80, 0x80, 0x40, 0xff],  # (0x40 << 20) + 0x0f = 0x400000f
        [0x4f, 0x80, 0x80, 0x80, 0x8f, 0xff]  # 0x8f << 27 + 0x0f = 0x47800000f
    ]
    expected_values = [
        0x0f,
        0x100f,
        -0x0f,
        -0x100f,
        0x8000f,
        0x400000f,
        0x47800000f
    ]
    for test, ev in zip(test_data, expected_values):
        assert c.parse(bytes(test)).index == ev
        new_bytes = c.build(dict(index=ev))
        assert new_bytes == bytes(test[:len(new_bytes)])
    print("All tests passed!")
