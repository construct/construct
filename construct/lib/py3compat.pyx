import cStringIO

StringIO = BytesIO = cStringIO.StringIO

int2byte = chr
byte2int = ord
bchr = lambda i: i


def u(s):
    return unicode(s, "unicode_escape")


def str2bytes(s):
    return s


def str2unicode(s):
    return unicode(s, "unicode_escape")


def bytes2str(b):
    return b


def decodebytes(b, encoding):
    return b.decode(encoding)


def advance_iterator(it):
    return it.next()
