# encoding: utf-8


def int_to_bin(number, width=32):
    r"""
    Convert an integer into its binary representation in a bytes object.
    Width is the amount of bits to generate. If width is larger than the actual
    amount of bits required to represent number in binary, sign-extension is
    used. If it's smaller, the representation is trimmed to width bits.
    Each "bit" is either '\x00' or '\x01'. The MSBit is first.

    Examples:

        >>> int_to_bin(19, 5)
        '\x01\x00\x00\x01\x01'
        >>> int_to_bin(19, 8)
        '\x00\x00\x00\x01\x00\x00\x01\x01'
    """
    if number < 0:
        number += 1 << width
    i = width - 1
    bits = ["\x00"] * width
    while number and i >= 0:
        bits[i] = "\x00\x01"[number & 1]
        number >>= 1
        i -= 1
    return "".join(bits)

# heavily optimized for performance


def bin_to_int(bits, signed_value=False):
    r"""
    Logical opposite of int_to_bin. Both '0' and '\x00' are considered zero,
    and both '1' and '\x01' are considered one. Set sign to True to interpret
    the number as a 2-s complement signed integer.
    """
    bits = "".join("01"[ord(b) & 1] for b in bits)
    if signed_value and bits[0] == "1":
        bits = bits[1:]
        bias = 1 << len(bits)
    else:
        bias = 0
    return int(bits, 2) - bias

_char_to_bin = [0] * 256
_bin_to_char = {}

for i in range(256):
    ch = chr(i)
    bin = int_to_bin(i, 8)
    # Populate with for both keys i and ch, to support Python 2 & 3
    _char_to_bin[i] = bin
    _bin_to_char[bin] = ch


def encode_bin(data):
    """
    Create a binary representation of the given b'' object. Assume 8-bit
    ASCII. Example:

        >>> encode_bin('ab')
        b"\x00\x01\x01\x00\x00\x00\x00\x01\x00\x01\x01\x00\x00\x00\x01\x00"
    """
    return "".join(_char_to_bin[ord(ch)] for ch in data)


def decode_bin(data):
    if len(data) & 7:
        raise ValueError("Data length must be a multiple of 8")
    i = 0
    j = 0
    l = len(data) // 8
    chars = [""] * l
    while j < l:
        chars[j] = _bin_to_char[data[i:i + 8]]
        i += 8
        j += 1
    return "".join(chars)


def swap_bytes(bits, bytesize=8):
    r"""
    Bits is a b'' object containing a binary representation. Assuming each
    bytesize bits constitute a bytes, perform a endianness byte swap. Example:

        >>> swap_bytes(b'00011011', 2)
        b'11100100'
    """
    i = 0
    l = len(bits)
    output = [""] * ((l // bytesize) + 1)
    j = len(output) - 1
    while i < l:
        output[j] = bits[i: i + bytesize]
        i += bytesize
        j -= 1
    return "".join(output)
