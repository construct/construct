# -*- coding: utf-8 -*-

import struct, io, binascii, collections, sys

from construct.lib import *
from construct.expr import *
from construct.version import *


#===============================================================================
# exceptions
#===============================================================================
class ConstructError(Exception):
    pass
class SizeofError(ConstructError):
    pass
class AdaptationError(ConstructError):
    pass
class ValidationError(ConstructError):
    pass
class StreamError(ConstructError):
    pass
class FormatFieldError(ConstructError):
    pass
class IntegerError(ConstructError):
    pass
class StringError(ConstructError):
    pass
class MappingError(ConstructError):
    pass
class RangeError(ConstructError):
    pass
class RepeatError(ConstructError):
    pass
class ConstError(ConstructError):
    pass
class ExplicitError(ConstructError):
    pass
class UnionError(ConstructError):
    pass
class SelectError(ConstructError):
    pass
class SwitchError(ConstructError):
    pass
class PaddingError(ConstructError):
    pass
class TerminatedError(ConstructError):
    pass
class RawCopyError(ConstructError):
    pass
class ChecksumError(ConstructError):
    pass


#===============================================================================
# used internally
#===============================================================================
def singleton(arg):
    return arg()


def _read_stream(stream, length):
    if length < 0:
        raise StreamError("length must be non-negative, found %s" % length)
    try:
        data = stream.read(length)
    except Exception:
        raise StreamError("stream.read() failed, requested %s bytes" % (length,))
    if len(data) != length:
        raise StreamError("could not read enough bytes, expected %d, found %d" % (length, len(data)))
    return data


def _read_stream_entire(stream):
    try:
        return stream.read()
    except Exception:
        raise StreamError("stream.read() failed when reading entire stream until EOF")


def _write_stream(stream, length, data):
    if length < 0:
        raise StreamError("length must be non-negative, found %s" % length)
    if len(data) != length:
        raise StreamError("could not write bytes, expected %d, found %d" % (length, len(data)))
    try:
        written = stream.write(data)
    except Exception:
        raise StreamError("stream.write() failed, given %r" % (data,))
    if written is not None and written != length:
        raise StreamError("could not write bytes, expected %d, written %d" % (length, written))


def _seek_stream(stream, offset, whence=0):
    try:
        return stream.seek(offset, whence)
    except Exception:
        raise StreamError("stream.seek failed: offset %s whence %s" % (offset, whence,))


def _tell_stream(stream):
    try:
        return stream.tell()
    except Exception:
        raise StreamError("stream.tell failed")


class CodeGen:
    def __init__(self):
        self.blocks = []
        self.nextid = 0
        self.decompiledcache = {}
        self.parsercache = {}

    def allocateId(self):
        self.nextid += 1
        return self.nextid

    def append(self, block):
        block = [s for s in block.splitlines() if s.strip()]
        firstline = block[0]
        trim = len(firstline) - len(firstline.lstrip())
        block = "\n".join(s[trim:] for s in block)
        if block not in self.blocks:
            self.blocks.append(block)

    def toString(self):
        return "\n".join(self.blocks + [""])


def mergefields(*subcons):

    def select(sc):
        if isinstance(sc, (Renamed, Embedded)):
            return select(sc.subcon)
        # experimental support for EmbeddedBitStruct
        # if isinstance(sc, (Restreamed, CompilableMacro)):
        #     return select(sc.subcon)
        if isinstance(sc, (Struct, Sequence, FocusedSeq, Union)):
            return list(sc.subcons)
        raise ConstructError("Embedding only works with: Struct, Sequence, FocusedSeq, Union")

    result = []
    for sc in subcons:
        if sc.flagembedded:
            result.extend(select(sc))
        else:
            result.append(sc)
    return result


#===============================================================================
# abstract constructs
#===============================================================================
class Construct(object):
    r"""
    The mother of all constructs.

    This object is generally not directly instantiated, and it does not directly implement parsing and building, so it is largely only of interest to subclass implementors. There are also other abstract classes sitting on top of this one.

    The external user API:

    * ``parse()``
    * ``parse_stream()``
    * ``build()``
    * ``build_stream()``
    * ``sizeof()``
    * ``compile()``
    * ``benchmark()``
    * ``testcompiled()``

    Subclass authors should not override the external methods. Instead, another API is available:

    * ``_parse()``
    * ``_build()``
    * ``_sizeof()``
    * ``_emitdecompiled()``
    * ``_emitparse()``
    * ``_emitbuild()``
    * ``__getstate__()``
    * ``__setstate__()``

    Attributes and Inheritance:

    All constructs have a name and flags. The name is used for naming struct members and context dictionaries. Note that the name can be a string, or None by default. A single underscore "_" is a reserved name, used as up-level in nested containers. The name should be descriptive, short, and valid as a Python identifier, although these rules are not enforced. The flags specify additional behavioral information about this construct. Flags are used by enclosing constructs to determine a proper course of action. Flags are often inherited from inner subconstructs but that depends on each class.
    """
    __slots__ = ["name", "flagbuildnone", "flagembedded"]

    def __init__(self):
        self.name = None
        self.flagbuildnone = False
        self.flagembedded = False

    def __repr__(self):
        return "<%s: %s%s%s>" % (self.__class__.__name__, self.name, " +nonbuild" if self.flagbuildnone else "", " +embedded" if self.flagembedded else "")

    def __getstate__(self):
        """Obtain a dictionary representing this construct's state."""
        attrs = {}
        if hasattr(self, "__dict__"):
            attrs.update(self.__dict__)
        slots = []
        c = self.__class__
        while c is not None:
            if hasattr(c, "__slots__"):
                slots.extend(c.__slots__)
            c = c.__base__
        for name in slots:
            if hasattr(self, name):
                attrs[name] = getattr(self, name)
        return attrs

    def __setstate__(self, attrs):
        """Set this construct's state to a given state."""
        for name, value in attrs.items():
            setattr(self, name, value)

    def __copy__(self):
        """Returns a copy of this construct."""
        self2 = object.__new__(self.__class__)
        self2.__setstate__(self, self.__getstate__())
        return self2

    def parse(self, data, **kw):
        r"""
        Parse an in-memory buffer (often bytes object). Strings, buffers, memoryviews, and other complete buffers can be parsed with this method.

        Whenever data cannot be read, ConstructError or its derivative is raised. This method is NOT ALLOWED to raise any other exceptions although (1) user-defined lambdas can raise arbitrary exceptions which are propagated (2) external libraries like numpy can raise arbitrary exceptions which are propagated (3) some list and dict lookups can raise IndexError and KeyError which are propagated.

        Context entries are passed only as keyword parameters \*\*kw.

        :param \*\*kw: context entries, usually empty

        :returns: some value, usually based on bytes read from the stream but sometimes it is computed from nothing or from the context dictionary, sometimes its non-deterministic

        :raises ConstructError: raised for any reason
        """
        return self.parse_stream(io.BytesIO(data), **kw)

    def parse_stream(self, stream, **kw):
        r"""
        Parse a stream. Files, pipes, sockets, and other streaming sources of data are handled by this method.

        Whenever data cannot be read, ConstructError or its derivative is raised. This method is NOT ALLOWED to raise any other exceptions although (1) user-defined lambdas can raise arbitrary exceptions which are propagated (2) external libraries like numpy can raise arbitrary exceptions which are propagated (3) some list and dict lookups can raise IndexError and KeyError which are propagated.

        Context entries are passed only as keyword parameters \*\*kw.

        :param \*\*kw: context entries, usually empty

        :returns: some value, usually based on bytes read from the stream but sometimes it is computed from nothing or from the context dictionary, sometimes its non-deterministic

        :raises ConstructError: raised for any reason
        """
        context = Container(**kw)
        return self._parse(stream, context, "(parsing)")

    def _parse(self, stream, context, path):
        """
        Override in your subclass.
        """
        raise NotImplementedError

    def build(self, obj, **kw):
        r"""
        Build an object in memory (a bytes object).

        Whenever data cannot be written, ConstructError or its derivative is raised. This method is NOT ALLOWED to raise any other exceptions although (1) user-defined lambdas can raise arbitrary exceptions which are propagated (2) external libraries like numpy can raise arbitrary exceptions which are propagated (3) some list and dict lookups can raise IndexError and KeyError which are propagated.

        Context entries are passed only as keyword parameters \*\*kw.

        :param \*\*kw: context entries, usually empty

        :returns: bytes

        :raises ConstructError: raised for any reason
        """
        stream = io.BytesIO()
        self.build_stream(obj, stream, **kw)
        return stream.getvalue()

    def build_stream(self, obj, stream, **kw):
        r"""
        Build an object directly into a stream.

        Whenever data cannot be written, ConstructError or its derivative is raised. This method is NOT ALLOWED to raise any other exceptions although (1) user-defined lambdas can raise arbitrary exceptions which are propagated (2) external libraries like numpy can raise arbitrary exceptions which are propagated (3) some list and dict lookups can raise IndexError and KeyError which are propagated.

        Context entries are passed only as keyword parameters \*\*kw.

        :param \*\*kw: context entries, usually empty

        :raises ConstructError: raised for any reason
        """
        context = Container(**kw)
        self._build(obj, stream, context, "(building)")

    def _build(self, obj, stream, context, path):
        """
        Override in your subclass.
        """
        raise NotImplementedError

    def sizeof(self, **kw):
        r"""
        Calculate the size of this object, optionally using a context.

        Some constructs have fixed size (like FormatField), some have variable-size and can determine their size given a context entry (like Bytes(this.otherfield1)), and some cannot determine their size (like VarInt).

        Whenever size cannot be determined, SizeofError is raised. This method is NOT ALLOWED to raise any other exception, even if eg. context dictionary is missing a key, or subcon propagates ConstructError-derivative exception.

        Context entries are passed only as keyword parameters \*\*kw.

        :param \*\*kw: context entries, usually empty

        :returns: integer if computable, SizeofError otherwise

        :raises SizeofError: size could not be determined in actual context, or is impossible to be determined
        """
        context = Container(**kw)
        return self._sizeof(context, "(sizeof)")

    def _sizeof(self, context, path):
        """
        Override in your subclass.
        """
        raise SizeofError

    def compile(self):
        """
        Transforms a construct into another construct that does same thing (has same parsing and building semantics) but is faster (has better performance). Compiled instances compile into itself, obviously. This method returns a Compiled instance.

        There are restrictions on what can be compiled (see documentation site, Compilation chapter). Some classes do not compile or compile only in certain circumstances.

        Returned instance has additional ``source`` field and ``tofile`` method, aside of regular ``parse`` ``build`` ``sizeof``.

        :returns: Compiled instance

        :raises NotImplementedError: raised for any reason
        """
        code = CodeGen()
        code.append("""
            from construct import *
            from construct.lib import *
            from io import BytesIO
            from struct import pack, unpack, calcsize
            import sys
            import collections

            assert sys.version_info[:2] >= (3,4)
            assert version_string == %r

            def read_bytes(io, count):
                assert count >= 0
                data = io.read(count)
                assert len(data) == count
                return data
            def restream(data, func):
                return func(BytesIO(data))
        """ % (version_string, ))
        code.append("""
            def parseall(io, this):
                return %s
            compiledschema = Compiled(None, None, parseall)
        """ % (self._compileparse(code),))

        source = code.toString()
        from types import ModuleType
        compiled = compile(source, '', 'exec')
        module = ModuleType("construct_compile_target")
        exec(compiled, module.__dict__)

        compiledschema = module.compiledschema
        compiledschema.source = source
        compiledschema.defersubcon = self
        return compiledschema

    def _decompile(self, code, recursive=False):
        """Used internally."""
        if id(self) in code.decompiledcache:
            return code.decompiledcache[id(self)]

        try:
            cname = "decompiled_%s" % code.allocateId()
            code.append("""
                %s = %s
            """ % (cname, self._emitdecompiled(code), ))
            code.decompiledcache[id(self)] = cname
            return cname
        except NotImplementedError:
            if recursive:
                raise NotImplementedError
            cname = "decompiled_%s" % code.allocateId()
            code.append("""
                %s = Decompiled(lambda io,this: %s)
            """ % (cname, self._compileparse(code, recursive=True), ))
            code.decompiledcache[id(self)] = cname
            return cname

    def _compileparse(self, code, recursive=False):
        """Used internally."""
        if id(self) in code.parsercache:
            return code.parsercache[id(self)]

        try:
            emitted = self._emitparse(code)
            code.parsercache[id(self)] = emitted
            return emitted
        except NotImplementedError:
            if recursive:
                raise NotImplementedError
            emitted = "%s._parse(io, this, None)" % (self._decompile(code, recursive=True), )
            code.parsercache[id(self)] = emitted
            return emitted

    def _compilebuild(self, code):
        """Used internally."""
        raise NotImplementedError

    def _emitdecompiled(self, code):
        """
        Override in your subclass.
        """
        raise NotImplementedError

    def _emitparse(self, code):
        """
        Override in your subclass.
        """
        raise NotImplementedError

    def _emitbuild(self, code):
        """
        Override in your subclass.
        """
        raise NotImplementedError

    def benchmark(self, sampledata):
        """
        Measures performance of your construct (its parsing and building runtime), both for this instance and its compiled equivalent (does not fail if its not compilable). Uses timeit module over 1000 samples.

        You need to provide a sample data for parsing testing. This data gets parsed into an object that gets reused for building testing. Sizeof is not tested.

        :returns: string containing runtimes and descriptions
        """
        from timeit import timeit

        try:
            parsetime = "failed"
            buildtime = "failed"
            compiletime = "failed"
            parsetime2 = "failed"
            buildtime2 = "failed"

            sampleobj = self.parse(sampledata)
            parsetime = timeit(lambda: self.parse(sampledata), number=1000)/1000
            self.build(sampleobj)
            buildtime = timeit(lambda: self.build(sampleobj), number=1000)/1000
            compiled = self.compile()
            compiletime = timeit(lambda: self.compile(), number=100)/100
            compiled.parse(sampledata)
            parsetime2 = timeit(lambda: compiled.parse(sampledata), number=1000)/1000
            compiled.build(sampleobj)
            buildtime2 = timeit(lambda: compiled.build(sampleobj), number=1000)/1000
        except Exception:
            pass

        lines = [
            "Timeit measurements:",
            "compiling:         {:.20f} sec/call",
            "parsing:           {:.20f} sec/call",
            "parsing compiled:  {:.20f} sec/call",
            "building:          {:.20f} sec/call",
            "building compiled: {:.20f} sec/call",
            ""
        ]
        return "\n".join(lines).format(compiletime, parsetime, parsetime2, buildtime, buildtime2)

    def testcompiled(self, sampledata):
        """
        Checks correctness of compiled equivalent class by comparing parse and build results of both this and compiled instances.

        You need to provide a sample data for parsing testing. This data gets parsed into an object that gets reused for building testing. Sizeof is not tested.
        """
        sampleobj = self.parse(sampledata)
        compiled = self.compile()
        assert self.parse(sampledata) == compiled.parse(sampledata)
        assert self.build(sampleobj) == compiled.build(sampleobj)

    def __rtruediv__(self, name):
        """
        Used for renaming subcons, usually part of a Struct, like Struct("index" / Byte).
        """
        if name is not None:
            if not isinstance(name, stringtypes):
                raise TypeError("name must be b-string or u-string or None", name)
        return Renamed(name, self)

    __rdiv__ = __rtruediv__

    def __add__(self, other):
        """
        Used for making Struct like ("index"/Byte + "prefix"/Byte).
        """
        lhs = self.subcons  if isinstance(self,  Struct) else [self]
        rhs = other.subcons if isinstance(other, Struct) else [other]
        return Struct(*(lhs + rhs))

    def __rshift__(self, other):
        """
        Used for making Sequences like (Byte >> Short).
        """
        lhs = self.subcons  if isinstance(self,  Sequence) else [self]
        rhs = other.subcons if isinstance(other, Sequence) else [other]
        return Sequence(*(lhs + rhs))

    def __getitem__(self, count):
        """
        Used for making Arrays and Ranges like Byte[5] or Byte[:].
        """
        if isinstance(count, slice):
            if count.step is not None:
                raise ValueError("slice must not contain a step: %r" % count)
            min = 0 if count.start is None else count.start
            max = 2**64 if count.stop is None else count.stop
            return Range(min, max, self)
        elif isinstance(count, int) or callable(count):
            return Array(count, self)
        else:
            raise TypeError("expected an int, a context lambda, or a slice thereof, but found %r" % count)


class Subconstruct(Construct):
    r"""
    Abstract subconstruct (wraps an inner construct, inheriting its name and flags). Parsing and building is by default deferred to subcon, same as sizeof.

    :param subcon: Construct instance
    """
    __slots__ = ["subcon"]
    def __init__(self, subcon):
        if not isinstance(subcon, Construct):
            raise TypeError("subcon should be a Construct field")
        super(Subconstruct, self).__init__()
        self.name = subcon.name
        self.subcon = subcon
        self.flagbuildnone = subcon.flagbuildnone
        self.flagembedded = subcon.flagembedded
    def _parse(self, stream, context, path):
        return self.subcon._parse(stream, context, path)
    def _build(self, obj, stream, context, path):
        return self.subcon._build(obj, stream, context, path)
    def _sizeof(self, context, path):
        return self.subcon._sizeof(context, path)


class Adapter(Subconstruct):
    r"""
    Abstract adapter class.

    Needs to implement ``_decode()`` for parsing and ``_encode()`` for building.

    :param subcon: Construct instance
    """
    def _parse(self, stream, context, path):
        return self._decode(self.subcon._parse(stream, context, path), context)
    def _build(self, obj, stream, context, path):
        return self.subcon._build(self._encode(obj, context), stream, context, path)
    def _decode(self, obj, context):
        raise NotImplementedError
    def _encode(self, obj, context):
        raise NotImplementedError


class SymmetricAdapter(Adapter):
    r"""
    Abstract adapter class.

    Needs to implement ``_decode()`` only, for both parsing and building.

    :param subcon: Construct instance
    """
    def _encode(self, obj, context):
        return self._decode(obj, context)


class Validator(SymmetricAdapter):
    r"""
    Abstract class that validates a condition on the encoded/decoded object.

    Needs to implement ``_validate()`` that returns a bool (or a truthy value)

    :param subcon: Construct instance
    """
    def _decode(self, obj, context):
        if not self._validate(obj, context):
            raise ValidationError("object failed validation: %s" % (obj,))
        return obj
    def _validate(self, obj, context):
        raise NotImplementedError


class Tunnel(Subconstruct):
    r"""
    Abstract class that allows other constructs to read part of the stream as if they were reading the entrie stream. See Prefixed for example.

    Needs to implement ``_decode()`` for parsing and ``_encode()`` for building.
    """
    def _parse(self, stream, context, path):
        data = _read_stream_entire(stream)  # reads entire stream
        data = self._decode(data, context)
        return self.subcon.parse(data, **context)
    def _build(self, obj, stream, context, path):
        data = self.subcon.build(obj, **context)
        data = self._encode(data, context)
        _write_stream(stream, len(data), data)
    def _sizeof(self, context, path):
        raise SizeofError
    def _decode(self, data, context):
        raise NotImplementedError
    def _encode(self, data, context):
        raise NotImplementedError


class Compiled(Construct):
    """Used internally."""
    __slots__ = ["source", "defersubcon", "parsefunc", "buildfunc", "sizefunc"]

    def __init__(self, source, defersubcon, parsefunc=None, buildfunc=None, sizefunc=None):
        self.source = source
        self.defersubcon = defersubcon
        self.parsefunc = parsefunc
        self.buildfunc = buildfunc
        self.sizefunc = sizefunc

    def _parse(self, stream, context, path):
        if self.parsefunc:
            return self.parsefunc(stream, context)
        else:
            return self.defersubcon._parse(stream, context, path)

    def _build(self, obj, stream, context, path):
        if self.buildfunc:
            return self.buildfunc(obj, stream, context)
        else:
            return self.defersubcon._build(obj, stream, context, path)

    def _sizeof(self, context, path):
        if self.sizefunc:
            return self.sizefunc(context)
        else:
            return self.defersubcon._sizeof(context, path)

    def compile(self):
        return self

    def _compileparse(self, code):
        raise ConstructError("Compiled instance can compile() into self but cannot _compileparse() or _compilebuild()")

    def _compilebuild(self, code):
        raise ConstructError("Compiled instance can compile() into self but cannot _compileparse() or _compilebuild()")

    def tofile(self, filename):
        """
        Saves the ``source`` field into a text file (preferably with .py extension).
        """
        with open(filename, 'wt') as f:
            f.write(self.source)


class CompilableMacro(Subconstruct):
    """Used internally."""
    __slots__ = ["compileparsefunc"]

    def __init__(self, subcon, compileparsefunc):
        super(CompilableMacro, self).__init__(subcon)
        self.compileparsefunc = compileparsefunc

    def _emitparse(self, code):
        return self.compileparsefunc(self, code)

    def _emitbuild(self, code):
        raise NotImplementedError


class Decompiled(Construct):
    """Used internally."""
    __slots__ = ["parsefunc"]

    def __init__(self, parsefunc):
        super(Decompiled, self).__init__()
        self.parsefunc = parsefunc

    def _parse(self, stream, context, path):
        return self.parsefunc(stream, context)


#===============================================================================
# bytes and bits
#===============================================================================
class Bytes(Construct):
    r"""
    Field consisting of a specified number of bytes. 

    Parses into a bytes (of given length). Builds into the stream directly (but checks that given object matches specified length). Can also build from an integer for convenience (although BytesInteger should be used instead). Size is the specified length.

    :param length: integer or context lambda

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Bytes(4)
        >>> d.parse(b'beef')
        b'beef'
        >>> d.build(b'beef')
        b'beef'
        >>> d.build(0)
        b'\x00\x00\x00\x00'
        >>> d.sizeof()
        4

        # inside Struct, preceded by `field1` member
        >>> d = Bytes(this.field1)
        ...
    """
    __slots__ = ["length"]

    def __init__(self, length):
        super(Bytes, self).__init__()
        self.length = length

    def _parse(self, stream, context, path):
        length = self.length(context) if callable(self.length) else self.length
        return _read_stream(stream, length)

    def _build(self, obj, stream, context, path):
        length = self.length(context) if callable(self.length) else self.length
        data = integer2bytes(obj, length) if isinstance(obj, int) else obj
        _write_stream(stream, length, data)
        return data

    def _sizeof(self, context, path):
        try:
            return self.length(context) if callable(self.length) else self.length
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")

    def _emitparse(self, code):
        return "read_bytes(io, %s)" % (self.length,)


@singleton
class GreedyBytes(Construct):
    r"""
    Field consisting of unknown number of bytes. 

    Parses the stream to the end. Builds into the stream directly (without checks). Size is undefined.

    :raises StreamError: stream failed when reading until EOF

    Example::

        >>> GreedyBytes.parse(b"asislight")
        b'asislight'
        >>> GreedyBytes.build(b"asislight")
        b'asislight'
    """

    def _parse(self, stream, context, path):
        return _read_stream_entire(stream)

    def _build(self, obj, stream, context, path):
        stream.write(obj)

    def _emitparse(self, code):
        return "io.read()"


def Bitwise(subcon):
    r"""
    Converts the stream from bytes to bits, and passes the bitstream to underlying subcon. Bitstream is a stream that contains 8 times as many bytes, and each byte is either \\x00 or \\x01.

    Parsing building and size are deferred to subcon, although size gets divided by 8.

    Analog to :class:`~construct.core.Bytewise` that transforms bits back to bytes.

    .. warning:: Remember that subcon must consume or produce an amount of bytes that is a multiple of encoding or decoding units. For example, in a Bitwise context you should process a multiple of 8 bits or the stream will fail during parsing/building.

    .. warning:: Do NOT use seeking/telling classes inside Restreamed context.

    :param subcon: Construct instance, any field that works with bits (like BitsInteger) or is bit-byte agnostic (like Struct or Flag)

    See :class:`~construct.core.Restreamed` for raisable exceptions.

    Example::

        >>> d = Bitwise(Octet)
        >>> d.parse(b"\xff")
        255
        >>> d.build(1)
        b'\x01'
        >>> d.sizeof()
        1
    """
    macro = Restreamed(subcon, bytes2bits, 1, bits2bytes, 8, lambda n: n//8)
    def _emitparse(self, code):
        if subcon.sizeof() % 8:
            raise ConstructError("Bitwise cannot compile with subcon size not a multiple of 8")
        return "restream(bytes2bits(read_bytes(io, %s)), lambda io: %s)" % (subcon.sizeof()//8, subcon._compileparse(code), )
    return CompilableMacro(macro, _emitparse)


def Bytewise(subcon):
    r"""
    Converts the bitstream back to normal byte stream. Must be used within Bitwise.

    Parsing building and size are deferred to subcon, although size gets multiplied by 8.

    Analog to :class:`~construct.core.Bitwise` that transforms bytes to bits.

    .. warning:: Remember that subcon must consume or produce an amount of bytes that is a multiple of encoding or decoding units. For example, in a Bitwise context you should process a multiple of 8 bits or the stream will fail during parsing/building.

    .. warning:: Do NOT use seeking/telling classes inside Restreamed context.

    :param subcon: Construct instance, any field that works with bytes or is bit-byte agnostic

    :raises NotImplementedError: compiled

    See :class:`~construct.core.Restreamed` for raisable exceptions.

    Example::

        >>> d = Bitwise(Bytewise(Byte))
        >>> d.parse(b"\xff")
        255
        >>> d.build(255)
        b'\xff'
        >>> d.sizeof()
        1
    """
    macro = Restreamed(subcon, bits2bytes, 8, bytes2bits, 1, lambda n: n*8)
    def _emitparse(self, code):
        return "restream(bits2bytes(read_bytes(io, %s)), lambda io: %s)" % (subcon.sizeof()*8, subcon._compileparse(code), )
    return CompilableMacro(macro, _emitparse)


#===============================================================================
# integers and floats
#===============================================================================
class FormatField(Construct):
    r"""
    Field that uses `struct` module to pack and unpack CPU-sized integers and floats. This is used to implement most Int* Float* fields, but for example cannot pack 24-bit integers, which is left to :class:`~construct.core.BytesInteger` class.

    See `struct module <https://docs.python.org/3/library/struct.html>`_ documentation for instructions on crafting format strings.

    Parses into an integer. Builds from an integer into specified byte count and endianness. Size is determined by `struct` module according to specified format string.

    :param endianity: string, character like: < > =
    :param format: string, character like: f d B H L Q b h l q

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises FormatFieldError: wrong format string, or struct.(un)pack complained about the value

    Example::

        >>> d = FormatField(">", "H") or Int16ub
        >>> d.parse(b"\x01\x00")
        256
        >>> d.build(256)
        b"\x01\x00"
        >>> d.sizeof()
        2
    """
    __slots__ = ["fmtstr","length"]

    def __init__(self, endianity, format):
        if endianity not in list("=<>"):
            raise ValueError("endianity must be like: = < >", endianity)
        if format not in list("fdBHLQbhlq"):
            raise ValueError("format must be like: f d B H L Q b h l q", format)
        super(FormatField, self).__init__()
        self.fmtstr = endianity+format
        self.length = struct.calcsize(endianity+format)

    def _parse(self, stream, context, path):
        data = _read_stream(stream, self.length)
        try:
            return struct.unpack(self.fmtstr, data)[0]
        except Exception:
            raise FormatFieldError("struct %r error during parsing" % self.fmtstr)

    def _build(self, obj, stream, context, path):
        try:
            data = struct.pack(self.fmtstr, obj)
        except Exception:
            raise FormatFieldError("struct %r error during building, given value %r" % (self.fmtstr, obj))
        _write_stream(stream, self.length, data)

    def _sizeof(self, context, path):
        return self.length

    def _emitparse(self, code):
        return "unpack(%r, read_bytes(io, %s))[0]" % (self.fmtstr, self.length)


class BytesInteger(Construct):
    r"""
    Field that packs arbitrarily large integers. Some Int24* fields use this class.

    Parses into an integer. Builds from an integer into specified byte count and endianness. Size is specified in ctor.

    Analog to :class:`~construct.core.BitsInteger` that operates on bits. In fact, ``BytesInteger(n)`` is same as ``Bitwise(BitsInteger(8*n))`` and ``BitsInteger(n)`` is same as ``Bytewise(BytesInteger(n//8)))`` .

    :param length: integer or context lambda, number of bytes in the field
    :param signed: bool, whether the value is signed (two's complement), default is False (unsigned)
    :param swapped: bool, whether to swap byte order (little endian), default is False (big endian)

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises IntegerError: given a negative value when field is not signed, or not an integer

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = BytesInteger(4) or Int32ub
        >>> d.parse(b"abcd")
        1633837924
        >>> d.build(1)
        b'\x00\x00\x00\x01'
        >>> d.sizeof()
        4
    """
    __slots__ = ["length", "signed", "swapped"]

    def __init__(self, length, signed=False, swapped=False):
        super(BytesInteger, self).__init__()
        self.length = length
        self.signed = signed
        self.swapped = swapped

    def _parse(self, stream, context, path):
        length = self.length(context) if callable(self.length) else self.length
        data = _read_stream(stream, length)
        if self.swapped:
            data = data[::-1]
        return bytes2integer(data, self.signed)

    def _build(self, obj, stream, context, path):
        if not isinstance(obj, integertypes):
            raise IntegerError("value is not an integer")
        if obj < 0 and not self.signed:
            raise IntegerError("value is negative, but field is not signed", obj)
        length = self.length(context) if callable(self.length) else self.length
        data = integer2bytes(obj, length)
        if self.swapped:
            data = data[::-1]
        _write_stream(stream, len(data), data)

    def _sizeof(self, context, path):
        try:
            return self.length(context) if callable(self.length) else self.length
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")

    def _emitparse(self, code):
        return "int.from_bytes(read_bytes(io, %s), byteorder=%r, signed=%s)" % (self.length, 'little' if self.swapped else 'big', self.signed)


class BitsInteger(Construct):
    r"""
    Field that packs arbitrarily large (or small) integers. Some fields (Bit Nibble Octet) use this class. Must be enclosed in :class:`~construct.core.Bitwise` context.

    Parses into an integer. Builds from an integer into specified bit count and endianness. Size (in bits) is specified in ctor.

    Note that little-endianness is only defined for multiples of 8 bits.

    Analog to :class:`~construct.core.BytesInteger` that operates on bytes. In fact, ``BytesInteger(n)`` is same as ``Bitwise(BitsInteger(8*n))`` and ``BitsInteger(n)`` is same as ``Bytewise(BytesInteger(n//8)))`` .

    :param length: integer or context lambda, number of bits in the field
    :param signed: bool, whether the value is signed (two's complement), default is False (unsigned)
    :param swapped: bool, whether to swap byte order (little endian), default is False (big endian)

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises IntegerError: given a negative value when field is not signed, or not an integer

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Bitwise(BitsInteger(8)) or Bitwise(Octet)
        >>> d.parse(b"\x10")
        16
        >>> d.build(255)
        b'\xff'
        >>> d.sizeof()
        1
    """
    __slots__ = ["length", "signed", "swapped"]

    def __init__(self, length, signed=False, swapped=False):
        super(BitsInteger, self).__init__()
        self.length = length
        self.signed = signed
        self.swapped = swapped

    def _parse(self, stream, context, path):
        length = self.length(context) if callable(self.length) else self.length
        data = _read_stream(stream, length)
        if self.swapped:
            if length & 7:
                raise IntegerError("little-endianness is only defined for multiples of 8 bits")
            data = swapbytes(data)
        return bits2integer(data, self.signed)

    def _build(self, obj, stream, context, path):
        if not isinstance(obj, integertypes):
            raise IntegerError("value is not an integer")
        if obj < 0 and not self.signed:
            raise IntegerError("value is negative, but field is not signed", obj)
        length = self.length(context) if callable(self.length) else self.length
        data = integer2bits(obj, length)
        if self.swapped:
            if length & 7:
                raise IntegerError("little-endianness is only defined for multiples of 8 bits")
            data = swapbytes(data)
        _write_stream(stream, len(data), data)

    def _sizeof(self, context, path):
        try:
            return self.length(context) if callable(self.length) else self.length
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")

    def _emitparse(self, code):
        return "bits2integer(read_bytes(io, %s)%s, %s)" % (self.length, "[::-1]" if self.swapped else "", self.signed, )


@singleton
def Bit():
    """A 1-bit integer, must be enclosed in a Bitwise (eg. BitStruct)"""
    return BitsInteger(1)
@singleton
def Nibble():
    """A 4-bit integer, must be enclosed in a Bitwise (eg. BitStruct)"""
    return BitsInteger(4)
@singleton
def Octet():
    """A 8-bit integer, must be enclosed in a Bitwise (eg. BitStruct)"""
    return BitsInteger(8)

@singleton
def Int8ub():
    """Unsigned, big endian 8-bit integer"""
    return FormatField(">", "B")
@singleton
def Int16ub():
    """Unsigned, big endian 16-bit integer"""
    return FormatField(">", "H")
@singleton
def Int32ub():
    """Unsigned, big endian 32-bit integer"""
    return FormatField(">", "L")
@singleton
def Int64ub():
    """Unsigned, big endian 64-bit integer"""
    return FormatField(">", "Q")

@singleton
def Int8sb():
    """Signed, big endian 8-bit integer"""
    return FormatField(">", "b")
@singleton
def Int16sb():
    """Signed, big endian 16-bit integer"""
    return FormatField(">", "h")
@singleton
def Int32sb():
    """Signed, big endian 32-bit integer"""
    return FormatField(">", "l")
@singleton
def Int64sb():
    """Signed, big endian 64-bit integer"""
    return FormatField(">", "q")

@singleton
def Int8ul():
    """Unsigned, little endian 8-bit integer"""
    return FormatField("<", "B")
@singleton
def Int16ul():
    """Unsigned, little endian 16-bit integer"""
    return FormatField("<", "H")
@singleton
def Int32ul():
    """Unsigned, little endian 32-bit integer"""
    return FormatField("<", "L")
@singleton
def Int64ul():
    """Unsigned, little endian 64-bit integer"""
    return FormatField("<", "Q")

@singleton
def Int8sl():
    """Signed, little endian 8-bit integer"""
    return FormatField("<", "b")
@singleton
def Int16sl():
    """Signed, little endian 16-bit integer"""
    return FormatField("<", "h")
@singleton
def Int32sl():
    """Signed, little endian 32-bit integer"""
    return FormatField("<", "l")
@singleton
def Int64sl():
    """Signed, little endian 64-bit integer"""
    return FormatField("<", "q")

@singleton
def Int8un():
    """Unsigned, native endianity 8-bit integer"""
    return FormatField("=", "B")
@singleton
def Int16un():
    """Unsigned, native endianity 16-bit integer"""
    return FormatField("=", "H")
@singleton
def Int32un():
    """Unsigned, native endianity 32-bit integer"""
    return FormatField("=", "L")
@singleton
def Int64un():
    """Unsigned, native endianity 64-bit integer"""
    return FormatField("=", "Q")

@singleton
def Int8sn():
    """Signed, native endianity 8-bit integer"""
    return FormatField("=", "b")
@singleton
def Int16sn():
    """Signed, native endianity 16-bit integer"""
    return FormatField("=", "h")
@singleton
def Int32sn():
    """Signed, native endianity 32-bit integer"""
    return FormatField("=", "l")
@singleton
def Int64sn():
    """Signed, native endianity 64-bit integer"""
    return FormatField("=", "q")

Byte  = Int8ub
Short = Int16ub
Int   = Int32ub
Long  = Int64ub

@singleton
def Float32b():
    """Big endian, 32-bit IEEE floating point number"""
    return FormatField(">", "f")
@singleton
def Float32l():
    """Little endian, 32-bit IEEE floating point number"""
    return FormatField("<", "f")
@singleton
def Float32n():
    """Native endianity, 32-bit IEEE floating point number"""
    return FormatField("=", "f")

@singleton
def Float64b():
    """Big endian, 64-bit IEEE floating point number"""
    return FormatField(">", "d")
@singleton
def Float64l():
    """Little endian, 64-bit IEEE floating point number"""
    return FormatField("<", "d")
@singleton
def Float64n():
    """Native endianity, 64-bit IEEE floating point number"""
    return FormatField("=", "d")

Single = Float32b
Double = Float64b

native = (sys.byteorder == "little")

@singleton
def Int24ub():
    """A 3-byte big-endian unsigned integer, as used in ancient file formats."""
    return BytesInteger(3, signed=False, swapped=False)
@singleton
def Int24ul():
    """A 3-byte little-endian unsigned integer, as used in ancient file formats."""
    return BytesInteger(3, signed=False, swapped=True)
@singleton
def Int24un():
    """A 3-byte native-endian unsigned integer, as used in ancient file formats."""
    return BytesInteger(3, signed=False, swapped=native)
@singleton
def Int24sb():
    """A 3-byte big-endian signed integer, as used in ancient file formats."""
    return BytesInteger(3, signed=True, swapped=False)
@singleton
def Int24sl():
    """A 3-byte little-endian signed integer, as used in ancient file formats."""
    return BytesInteger(3, signed=True, swapped=True)
@singleton
def Int24sn():
    """A 3-byte native-endian signed integer, as used in ancient file formats."""
    return BytesInteger(3, signed=True, swapped=native)


@singleton
class VarInt(Construct):
    r"""
    VarInt encoded integer. Each 7 bits of the number are encoded in one byte of the stream, where leftmost bit (MSB) is unset when byte is terminal. Scheme is defined at Google site related to `Protocol Buffers <https://developers.google.com/protocol-buffers/docs/encoding>`_.

    Can only encode non-negative numbers.

    Parses into an integer. Builds from an integer. Size is undefined.

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises IntegerError: given a negative value, or not an integer

    Example::

        >>> VarInt.build(1)
        b'\x01'
        >>> VarInt.build(2**100)
        b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x04'
    """

    def _parse(self, stream, context, path):
        acc = []
        while True:
            b = byte2int(_read_stream(stream, 1))
            acc.append(b & 0b01111111)
            if not b & 0b10000000:
                break
        num = 0
        for b in reversed(acc):
            num = (num << 7) | b
        return num

    def _build(self, obj, stream, context, path):
        if not isinstance(obj, integertypes):
            raise IntegerError("value is not an integer")
        if obj < 0:
            raise IntegerError("varint cannot build from negative number: %r" % (obj,))
        while obj > 0b01111111:
            _write_stream(stream, 1, int2byte(0b10000000 | (obj & 0b01111111)))
            obj >>= 7
        _write_stream(stream, 1, int2byte(obj))

    def _emitdecompiled(self, code):
        return "VarInt"


#===============================================================================
# strings
#===============================================================================
globalstringencoding = None


@singleton
class StringsAsBytes:
    """
    Used for marking String* classes to not encode/decode bytes (allows using `str` on Python 2).
    """
    pass


possiblestringencodings = dict(
    StringsAsBytes=1,
    ascii=1,
    utf8=1, utf_8=1, U8=1,
    utf16=2, utf_16=2, U16=2, utf_16_be=2, utf_16_le=2,
    utf32=4, utf_32=4, U32=4, utf_32_be=4, utf_32_le=4,
)


def setglobalstringencoding(encoding):
    r"""
    Sets the encoding globally for all String PascalString CString GreedyString instances. Note that encoding specified expiciltly in a particular construct supersedes it. Note also that global encoding is applied during parsing and building (not class instantiation).

    See :class:`~construct.core.StringsAsBytes` for non-encoding, allowing using `str` on Python 2.

    :param encoding: string like "utf8", or StringsAsBytes, or None (disable global override)
    """
    global globalstringencoding
    globalstringencoding = encoding


class StringEncoded(Adapter):
    """Used internally."""
    __slots__ = ["encoding"]

    def __init__(self, subcon, encoding):
        super(StringEncoded, self).__init__(subcon)
        self.encoding = encoding

    def _decode(self, obj, context):
        encoding = self.encoding or globalstringencoding
        if isinstance(encoding, str):
            return obj.decode(encoding)
        if isinstance(encoding, StringsAsBytes.__class__):
            if not isinstance(obj, bytestringtype):
                raise StringError("decoding must result in bytes type")
            return obj
        raise StringError("String* classes require explicit encoding")

    def _encode(self, obj, context):
        encoding = self.encoding or globalstringencoding
        if isinstance(encoding, str):
            return obj.encode(encoding)
        if isinstance(encoding, StringsAsBytes.__class__):
            if not isinstance(obj, bytestringtype):
                raise StringError("encoding must result in bytes type")
            return obj
        raise StringError("String* classes require explicit encoding")

    def _emitparse(self, code):
        encoding = self.encoding or globalstringencoding
        if isinstance(encoding, str):
            return "(%s).decode(%r)" % (self.subcon._compileparse(code), encoding, )
        if isinstance(encoding, StringsAsBytes.__class__):
            return "(%s)" % (self.subcon._compileparse(code), )
        raise StringError("String* classes require explicit encoding")


class StringPaddedTrimmed(Construct):
    """Used internally."""
    __slots__ = ["length", "encoding"]

    def __init__(self, length, encoding):
        super(StringPaddedTrimmed, self).__init__()
        self.length = length
        self.encoding = encoding

    def _parse(self, stream, context, path):
        length = self.length(context) if callable(self.length) else self.length

        encoding = self.encoding or globalstringencoding
        if encoding is StringsAsBytes:
            encoding = "StringsAsBytes"
        if encoding not in possiblestringencodings:
            raise StringError("encoding not implemented: %r" % (encoding,))
        unitsize = possiblestringencodings[encoding]
        finalunit = b"\x00" * unitsize

        if length % unitsize:
            raise StringError("byte length must be multiple of encoding-unit, %s" % (unitsize,))
        obj = _read_stream(stream, length)
        while obj[-unitsize:] == finalunit:
            obj = obj[:-unitsize]
        return obj

    def _build(self, obj, stream, context, path):
        length = self.length(context) if callable(self.length) else self.length

        encoding = self.encoding or globalstringencoding
        if encoding is StringsAsBytes:
            encoding = "StringsAsBytes"
        if encoding not in possiblestringencodings:
            raise StringError("encoding not implemented: %r" % (encoding,))
        unitsize = possiblestringencodings[encoding]
        finalunit = b"\x00" * unitsize

        if length % unitsize:
            raise StringError("byte length must be multiple of encoding-unit, %s" % (unitsize,))
        if len(obj) % unitsize:
            raise StringError("string length must be multiple of encoding-unit, %s" % (unitsize,))
        if len(obj) > length-unitsize:
            obj = obj[:length-unitsize]
        obj = obj.ljust(length, b"\x00")
        _write_stream(stream, len(obj), obj)

    def _sizeof(self, context, path):
        length = self.length(context) if callable(self.length) else self.length
        return length

    def _emitparse(self, code):
        encoding = self.encoding or globalstringencoding
        if encoding is StringsAsBytes:
            encoding = "StringsAsBytes"
        if encoding not in possiblestringencodings:
            raise StringError("encoding not implemented: %r" % (encoding,))
        unitsize = possiblestringencodings[encoding]
        finalunit = b"\x00" * unitsize

        code.append(r"""
            def parse_paddedtrimmedstring(io, length, unitsize, finalunit):
                if length % unitsize:
                    raise StringError
                obj = read_bytes(io, length)
                while obj[-unitsize:] == finalunit:
                    obj = obj[:-unitsize]
                return obj
        """)
        return "parse_paddedtrimmedstring(io, %r, %r, %r)" % (self.length, unitsize, finalunit, )


class StringNullTerminated(Construct):
    """Used internally."""
    __slots__ = ["encoding"]

    def __init__(self, encoding=None):
        super(StringNullTerminated, self).__init__()
        self.encoding = encoding

    def _parse(self, stream, context, path):
        encoding = self.encoding or globalstringencoding
        if encoding is StringsAsBytes:
            encoding = "StringsAsBytes"
        if encoding not in possiblestringencodings:
            raise StringError("encoding not implemented: %r" % (encoding,))
        unitsize = possiblestringencodings[encoding]
        finalunit = b"\x00" * unitsize

        result = []
        while True:
            unit = _read_stream(stream, unitsize)
            if unit == finalunit:
                break
            result.append(unit)
        return b"".join(result)

    def _build(self, obj, stream, context, path):
        encoding = self.encoding or globalstringencoding
        if encoding is StringsAsBytes:
            encoding = "StringsAsBytes"
        if encoding not in possiblestringencodings:
            raise StringError("encoding not implemented: %r" % (encoding,))
        unitsize = possiblestringencodings[encoding]
        finalunit = b"\x00" * unitsize

        if len(obj) % unitsize:
            raise StringError("string length must be multiple of encoding-unit, %s" % (unitsize,))
        data = obj + finalunit
        _write_stream(stream, len(data), data)

    def _emitdecompiled(self, code):
        encoding = self.encoding or globalstringencoding
        if encoding is StringsAsBytes:
            encoding = "StringsAsBytes"
        if encoding not in possiblestringencodings:
            raise StringError("encoding not implemented: %r" % (encoding,))

        return "StringNullTerminated(encoding=%r)" % (encoding,)

    def _emitparse(self, code):
        encoding = self.encoding or globalstringencoding
        if encoding is StringsAsBytes:
            encoding = "StringsAsBytes"
        if encoding not in possiblestringencodings:
            raise StringError("encoding not implemented: %r" % (encoding,))
        unitsize = possiblestringencodings[encoding]
        finalunit = b"\x00" * unitsize

        code.append("""
            def parse_nullterminatedstring(io, unitsize, finalunit):
                result = []
                while True:
                    unit = read_bytes(io, unitsize)
                    if unit == finalunit:
                        break
                    result.append(unit)
                return b"".join(result)
        """)
        return "parse_nullterminatedstring(io, %r, %r)" % (unitsize, finalunit, )


def String(length, encoding=None):
    r"""
    Configurable, fixed-length or variable-length string field.

    When parsing, the byte string is stripped of null bytes (per encoding unit), then decoded. Length is an integer or context lambda. When building, the string is encoded, then trimmed to specified length minus encoding unit, then padded to specified length. Size is same as length parameter.

    :param length: integer or context lambda, length in bytes (not unicode characters)
    :param encoding: string like "utf8" "utf16" "utf32", or StringsAsBytes, or None (use global override)

    :raises StringError: String* classes require explicit encoding
    :raises StringError: building a unicode string but no encoding
    :raises StringError: specified length or object for building is not a multiple of unit
    :raises StringError: selected encoding is not on supported list

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = String(10, encoding=StringsAsBytes)
        >>> d.build(b"hello")
        b'hello\x00\x00\x00\x00\x00'
        >>> d.parse(_)
        b'hello'
        >>> d.sizeof()
        10

        >>> d = String(10, encoding="utf8")
        >>> d.build(u"Афон")
        b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00\x00'
        >>> d.parse(_)
        u'Афон'

        >>> d = String(10, encoding=StringsAsBytes, padchar=b"XYZ", paddir="center")
        >>> d.build(b"abc")
        b'XXXabcXXXX'
        >>> d.parse(b"XYZabcXYZY")
        b'abc'

        >>> d = String(10, encoding=StringsAsBytes, trimdir="right")
        >>> d.build(b"12345678901234567890")
        b'1234567890'
    """
    return StringEncoded(StringPaddedTrimmed(length, encoding), encoding)


def PascalString(lengthfield, encoding=None):
    r"""
    Length-prefixed string. The length field can be variable length (such as VarInt) or fixed length (such as Int64ub). VarInt is recommended when designing new protocols. Stored length is in bytes, not characters. Size is not defined.

    :param lengthfield: Construct instance, field used to parse and build the length (like VarInt Int64ub)
    :param encoding: string like "utf8" "utf16" "utf32", or StringsAsBytes, or None (use global override)

    :raises StringError: String* classes require explicit encoding
    :raises StringError: building a unicode string but no encoding

    Example::

        >>> d = PascalString(VarInt, encoding="utf8")
        >>> d.build(u"Афон")
        b'\x08\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd'
        >>> d.parse(_)
        u'Афон'
    """
    return StringEncoded(Prefixed(lengthfield, GreedyBytes), encoding)


def CString(encoding=None):
    r"""
    String ending in a terminating null byte (or null bytes in case of UTF16 UTF32).

    :param encoding: string like "utf8" "utf16" "utf32", or StringsAsBytes, or None (use global override)

    :raises StringError: String* classes require explicit encoding
    :raises StringError: building a unicode string but no encoding
    :raises StringError: object for building is not a multiple of unit
    :raises StringError: selected encoding is not on supported list

    Example::

        >>> d = CString(encoding="utf8")
        >>> d.build(u"Афон")
        b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00'
        >>> d.parse(_)
        u'Афон'
    """
    return StringEncoded(StringNullTerminated(encoding), encoding)
        # ExprAdapter(
        #     RepeatUntil(lambda obj,lst,ctx: int2byte(obj) in terminators, Byte),
        #     decoder = lambda obj,ctx: b''.join(int2byte(c) for c in obj[:-1]),
        #     encoder = lambda obj,ctx: iterateints(obj+terminators), ),
        # encoding)


def GreedyString(encoding=None):
    r"""
    String that reads entire stream until EOF, and writes a given string as-is. If no encoding is specified, this is essentially GreedyBytes.

    Analog to :class:`~construct.core.GreedyBytes` , and identical when no enoding is used.

    :param encoding: string like "utf8" "utf16" "utf32", or StringsAsBytes, or None (use global override)

    :raises StringError: String* classes require explicit encoding
    :raises StringError: building a unicode string but no encoding
    :raises StreamError: stream failed when reading until EOF

    Example::

        >>> d = GreedyString(encoding="utf8")
        >>> d.build(u"Афон")
        b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd'
        >>> d.parse(_)
        u'Афон'
    """
    return StringEncoded(GreedyBytes, encoding)


#===============================================================================
# mappings
#===============================================================================
@singleton
class Flag(Construct):
    r"""
    One byte (or one bit) field that maps to True or False. Other non-zero bytes are also considered True. Size is defined as 1.

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes

    Example::

        >>> Flag.parse(b"\x01")
        True
        >>> Flag.build(True)
        b'\x01'
    """

    def _parse(self, stream, context, path):
        return _read_stream(stream, 1) != b"\x00"

    def _build(self, obj, stream, context, path):
        _write_stream(stream, 1, b"\x01" if obj else b"\x00")

    def _sizeof(self, context, path):
        return 1

    def _emitparse(self, code):
        return "(read_bytes(io, 1) != b'\\x00')"


class Enum(Adapter):
    r"""
    Translates unicode label names to subcon values, and vice versa. 

    semantics???
    Size is same as subcon, unless it raises SizeofError.

    :param subcon: Construct instance, subcon to map to/from
    :param \*merge: optional, list of enum.IntEnum and enum.IntFlag instances, to merge labels and values from
    :param \*\*mapping: dict, mapping string names to values

    :raises MappingError: label (during building) or value (during parsing) cannot be translated, and no default was provided

    Example::

        >>> d = Enum(Byte, zero=0, one=1)
        >>> d.parse(b"\x01")
        'one'
        >>> d.parse(b"\xff")
        construct.core.MappingError: parsing failed, no decoding mapping for 255
        >>> d.build("one")
        b'\x01'
        >>> d.build(1)
        b'\x01'
        >>> d.build(255)
        construct.core.MappingError: building failed, no decoding mapping for 255
        >>> d.build("missing")
        construct.core.MappingError: building failed, no decoding mapping for "missing"
        >>> d.sizeof()
        1

        import enum
        class E(enum.IntEnum):
            one = 1
        class F(enum.IntFlag):
            two = 2
        Enum(Byte,      E, F) <--> Enum(Byte,      one=1, two=2)
        FlagsEnum(Byte, E, F) <--> FlagsEnum(Byte, one=1, two=2)
    """
    __slots__ = ["encmapping", "decmapping"]

    def __init__(self, subcon, *merge, **mapping):
        super(Enum, self).__init__(subcon)
        for enum in merge:
            for enumentry in enum:
                mapping[enumentry.name] = enumentry.value
        self.encmapping =      {k:v for k,v in mapping.items()}
        self.encmapping.update({v:v for k,v in mapping.items()})
        self.decmapping =      {v:k for k,v in mapping.items()}
        self.decmapping.update({k:k for k,v in mapping.items()})

    def _decode(self, obj, context):
        try:
            return self.decmapping[obj]
        except KeyError:
            raise MappingError("parsing failed, no mapping for %r" % (obj,))

    def _encode(self, obj, context):
        try:
            return self.encmapping[obj]
        except KeyError:
            raise MappingError("building failed, no mapping for %r" % (obj,))


class FlagsEnum(Adapter):
    r"""
    Translates unicode label names to subcon integer (sub)values, and vice versa.

    semantics???
    Size is same as subcon, unless it raises SizeofError.

    :param subcon: Construct instance, must operate on integers
    :param \*merge: optional, list of enum.IntEnum and enum.IntFlag instances, to merge labels and values from
    :param \*\*flags: dict, mapping string names to integer values

    Can raise arbitrary exceptions when computing | and & and value is non-integer.

    Example::

        >>> d = FlagsEnum(Byte, a=1, b=2, c=4, d=8)
        >>> d.parse(b"\x03")
        Container(c=False)(b=True)(a=True)(d=False)

        import enum
        class E(enum.IntEnum):
            one = 1
        class F(enum.IntFlag):
            two = 2
        Enum(Byte,      E, F) <--> Enum(Byte,      one=1, two=2)
        FlagsEnum(Byte, E, F) <--> FlagsEnum(Byte, one=1, two=2)
    """
    __slots__ = ["flags"]

    def __init__(self, subcon, *merge, **flags):
        super(FlagsEnum, self).__init__(subcon)
        for enum in merge:
            for enumentry in enum:
                flags[enumentry.name] = enumentry.value
        self.flags = flags

    def _decode(self, obj, context):
        obj2 = FlagsContainer()
        for name,value in self.flags.items():
            obj2[name] = bool(obj & value)
        return obj2

    def _encode(self, obj, context):
        try:
            flags = 0
            for name,value in obj.items():
                if value:
                    flags |= self.flags[name]
            return flags
        except AttributeError:
            raise MappingError("building failed, object is not a dictionary: %r" % (obj,))
        except KeyError:
            raise MappingError("building failed, unknown flag: %s" % (name,))


class Mapping(Adapter):
    r"""
    Adapter that maps objects to other objects. Translates objects before parsing and before building.

    .. note:: It used to be used internally by Flag IfThenElse etc but became deprecated.

    :param subcon: Construct instance, subcon to map to/from
    :param decoding: dict, for decoding (parsing) mapping
    :param encoding: dict, for encoding (building) mapping
    :param decdefault: object, default return value when object is not found in the mapping, if no object is given then exception is raised, if ``Pass`` is used, the unmapped object is passed as-is
    :param encdefault: object, default return value when object is not found in the mapping, if no object is given then exception is raised, if ``Pass`` is used, the unmapped object is passed as-is

    Example::

        ???
    """
    __slots__ = ["encoding", "decoding", "encdefault", "decdefault"]

    def __init__(self, subcon, decoding, encoding, decdefault=NotImplemented, encdefault=NotImplemented):
        super(Mapping, self).__init__(subcon)
        self.decoding = decoding
        self.encoding = encoding
        self.decdefault = decdefault
        self.encdefault = encdefault

    def _decode(self, obj, context):
        try:
            return self.decoding[obj]
        except (KeyError, TypeError):
            if self.decdefault is NotImplemented:
                raise MappingError("parsing failed, no decoding mapping for %r" % (obj,))
            if self.decdefault is Pass:
                return obj
            return self.decdefault

    def _encode(self, obj, context):
        try:
            return self.encoding[obj]
        except (KeyError, TypeError):
            if self.encdefault is NotImplemented:
                raise MappingError("building failed, no encoding mapping for %r" % (obj,))
            if self.encdefault is Pass:
                return obj
            return self.encdefault


def SymmetricMapping(subcon, mapping, default=NotImplemented):
    r"""
    Defines a symmetric mapping, same mapping is used on parsing and building.

    This is just a macro around :class:`~construct.core.Mapping`.

    :param subcon: Construct instance, subcon to map to/from
    :param mapping: dict, for decoding (parsing) mapping
    :param default: object, default return value when object is not found in the mapping, if no object is given then exception is raised, if ``Pass`` is used, the unmapped object is passed as-is

    Example::

        ???
    """
    return Mapping(subcon,
        decoding = dict((v,k) for k,v in mapping.items()),
        encoding = mapping,
        decdefault = default,
        encdefault = default,
    )


#===============================================================================
# structures and sequences
#===============================================================================
class Struct(Construct):
    r"""
    Sequence of usually named constructs, similar to structs in C. The members are parsed and build in the order they are defined. If a member is anonymous (its name is None) then it gets parsed and the value discarded, or it gets build from nothing (from None).

    Some fields do not need to be named, since they are built without value anyway. See: Const Padding Check Error Pass Terminated Seek Tell for examples of such fields. :class:`~construct.core.Embedded` fields do not need to (and should not) be named.

    Operator + can also be used to make Structs (although not recommended).

    Parses into a Container (dict with attribute and key access) where keys match subcon names. If field has embedded flag, its assuned to parse into a dict which entries get merged with result dict. Builds from a dict (not necessarily a Container) where each member gets a value from the dict matching the subcon name. If field has build-from-none flag, it gets build even when there is no mathing entry in the dict. If field has embedded flag, it gets build from the entire dict itself. Size is the sum of all subcon sizes, unless any subcon raises SizeofError.

    This class does context nesting, meaning its members are given access to a new dictionary where the "_" entry points to the outer context. When parsing, each member gets parsed and subcon parse return value is inserted into context under matching key only if the member was named. When building, the matching entry gets inserted into context before subcon gets build, and if subcon build returns a new value (not None) that gets replaced in the context.

    This class supports embedding. :class:`~construct.core.Embedded` semantics dictate, that during instance creation (in ctor), each field is checked for embedded flag, and its subcons members merged. This changes behavior of some code examples. Only few classes are supported: Struct Sequence FocusedSeq Union, although those can be used interchangably (a Struct can embed a Sequence, or rather its members). EmbeddedBitStruct is not currently supported (yet to be resolved).

    :param \*subcons: Construct instances, list of members, some can be anonymous
    :param \*\*kw: Construct instances, list of members (requires Python 3.6)

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises KeyError: building a subcon but found no corresponding key in dictionary

    Example::

        >>> d = Struct("num"/Int8ub, "data"/Bytes(this.num))
        >>> d.parse(b"\x04DATA")
        Container(num=4)(data=b"DATA")
        >>> d.build(dict(num=4, data=b"DATA"))
        b"\x04DATA"

        >>> d = Struct(Const(b"MZ"), Padding(2), Pass, Terminated)
        >>> d.build({})
        b'MZ\x00\x00'
        >>> d.parse(_)
        Container()
        >>> d.sizeof()
        4

        Alternative syntax (not recommended):
        >>> ("a"/Byte + "b"/Byte + "c"/Byte + "d"/Byte)

        Alternative syntax, but requires Python 3.6:
        >>> Struct(a=Byte, b=Byte, c=Byte, d=Byte)
    """
    __slots__ = ["subcons"]

    def __init__(self, *subcons, **kw):
        super(Struct, self).__init__()
        subcons = list(subcons) + list(k/v for k,v in kw.items())
        self.subcons = mergefields(*subcons)

    def _parse(self, stream, context, path):
        obj = Container()
        context = Container(_ = context)
        for sc in self.subcons:
            try:
                subobj = sc._parse(stream, context, path)
                if sc.name:
                    obj[sc.name] = subobj
                    context[sc.name] = subobj
            except StopIteration:
                break
        return obj

    def _build(self, obj, stream, context, path):
        context = Container(_ = context)
        context.update(obj)
        for sc in self.subcons:
            try:
                if sc.flagbuildnone:
                    subobj = obj.get(sc.name, None)
                else:
                    subobj = obj[sc.name] # raises KeyError

                if sc.name:
                    context[sc.name] = subobj

                buildret = sc._build(subobj, stream, context, path)
                if buildret is not None:
                    if sc.name:
                        context[sc.name] = buildret
            except StopIteration:
                break
        return context

    def _sizeof(self, context, path):
        context = Container(_ = context)
        try:
            return sum(sc._sizeof(context, path) for sc in self.subcons)
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")

        # try:
        #     def isStruct(sc):
        #         return isStruct(sc.subcon) if isinstance(sc, Renamed) else isinstance(sc, Struct)
        #     def nest(context, sc):
        #         if isStruct(sc) and not sc.flagembedded and sc.name in context:
        #             context2 = context[sc.name]
        #             context2["_"] = context
        #             return context2
        #         else:
        #             return context
        #     return sum(sc._sizeof(nest(context, sc), path) for sc in self.subcons)
        # except (KeyError, AttributeError):
        #     raise SizeofError("cannot calculate size, key not found in context")

    def _emitparse(self, code):
        fname = "parse_struct_%s" % code.allocateId()
        block = """
            def %s(io, this):
                this = Container(_ = this)
        """ % (fname, )
        for sc in self.subcons:
            block += """
                %s%s
            """ % ("this[%r] = " % sc.name if sc.name else "", sc._compileparse(code))
        block += """
                del this._
                return this
        """
        code.append(block)
        return "%s(io, this)" % (fname,)


class Sequence(Construct):
    r"""
    Sequence of usually un-named constructs. The members are parsed and build in the order they are defined. If a member is named, its parsed value gets inserted into the context. This allows using members that refer to previous members. :class:`~construct.core.Embedded` fields do not need to (and should not) be named.

    Operator >> can also be used to make Sequences (although not recommended).

    Parses into a ListContainer (list with pretty-printing) where values are in same order as subcons. If field has embedded flag, its assumed to parse into a list which elements get merged with result list. Builds from a list (not necessarily a ListContainer) where each subcon is given the element at respective position. If field has embedded flag, it gets build from a following subset of entire list. Size is the sum of all subcon sizes, unless any subcon raises SizeofError.

    This class does context nesting, meaning its members are given access to a new dictionary where the "_" entry points to the outer context. When parsing, each member gets parsed and subcon parse return value is inserted into context under matching key only if the member was named. When building, the matching entry gets inserted into context before subcon gets build, and if subcon build returns a new value (not None) that gets replaced in the context.

    This class supports embedding. :class:`~construct.core.Embedded` semantics dictate, that during instance creation (in ctor), each field is checked for embedded flag, and its subcons members merged. This changes behavior of some code examples. Only few classes are supported: Struct Sequence FocusedSeq Union, although those can be used interchangably (a Struct can embed a Sequence, or rather its members). EmbeddedBitStruct is not currently supported (yet to be resolved).

    :param \*subcons: Construct instances, list of members, some can be named
    :param \*\*kw: Construct instances, list of members (requires Python 3.6)

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises KeyError: building a subcon but found no corresponding key in dictionary

    Example::

        >>> d = Sequence(Byte, Float32b)
        >>> d.build([0, 1.23])
        b'\x00?\x9dp\xa4'
        >>> d.parse(_)
        [0, 1.2300000190734863] # a ListContainer

        Alternative syntax (not recommended):
        >>> (Byte >> "Byte >> "c"/Byte >> "d"/Byte)

        Alternative syntax, but requires Python 3.6:
        >>> Sequence(a=Byte, b=Byte, c=Byte, d=Byte)
    """
    __slots__ = ["subcons"]

    def __init__(self, *subcons, **kw):
        super(Sequence, self).__init__()
        subcons = list(subcons) + list(k/v for k,v in kw.items())
        self.subcons = mergefields(*subcons)

    def _parse(self, stream, context, path):
        obj = ListContainer()
        context = Container(_ = context)
        for i,sc in enumerate(self.subcons):
            try:
                subobj = sc._parse(stream, context, path)
                obj.append(subobj)
                if sc.name:
                    context[sc.name] = subobj
            except StopIteration:
                break
        return obj

    def _build(self, obj, stream, context, path):
        context = Container(_ = context)
        for i,(sc,subobj) in enumerate(zip(self.subcons, obj)):
            try:
                if sc.name:
                    context[sc.name] = subobj

                buildret = sc._build(subobj, stream, context, path)
                if buildret is not None:
                    if sc.name:
                        context[sc.name] = buildret
            except StopIteration:
                break

    def _sizeof(self, context, path):
        context = Container(_ = context)
        try:
            return sum(sc._sizeof(context, path) for sc in self.subcons)
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")

    def _emitparse(self, code):
        fname = "parse_sequence_%s" % code.allocateId()
        block = """
            def %s(io, this):
                result = ListContainer()
                this = Container(_ = this)
        """ % (fname,)
        for sc in self.subcons:
            block += """
                result.append(%s)
            """ % (sc._compileparse(code))
            if sc.name:
                block += """
                this[%r] = result[-1]
                """ % (sc.name, )
        block += """
                return result
        """
        code.append(block)
        return "%s(io, this)" % (fname,)


#===============================================================================
# arrays ranges and repeaters
#===============================================================================
class Array(Subconstruct):
    r"""
    Homogenous array of elements, similar to C# generic T[].

    Parses into a ListContainer (a list). Parsing and building stops when either count items were procssed or StopIteration was raised. Builds from a list. If given list has more or less than count elements, raises RangeError. Size is defined as count multiplied by subcon size, but only if subcon is fixed size.

    Operator [] can be used to make Array and Range instances (recommended).

    :param count: integer or context lambda, strict amount of elements
    :param subcon: Construct instance, subcon to process individual elements

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises RangeError: specified count is not valid
    :raises RangeError: given object has different length than specified count

    Can propagate any exception from the lambdas, possibly non-ConstructError.

    Example::

        >>> d = Array(5, Byte) or Byte[5]
        >>> d.build(range(5))
        b'\x00\x01\x02\x03\x04'
        >>> d.parse(_)
        [0, 1, 2, 3, 4]

        Alternative syntax (recommended):
        >>> Bytes[5] creates Array
        >>> Byte[3:5], Byte[3:], Byte[:5] creates Range
        >>> Byte[:] creates GreedyRange
    """
    __slots__ = ["count"]

    def __init__(self, count, subcon):
        super(Array, self).__init__(subcon)
        self.count = count

    def _parse(self, stream, context, path):
        count = self.count
        if callable(count):
            count = count(context)
        if not 0 <= count:
            raise RangeError("invalid count %s" % (count,))
        obj = ListContainer()
        try:
            for i in range(count):
                obj.append(self.subcon._parse(stream, context, path))
        except StopIteration:
            pass
        return obj

    def _build(self, obj, stream, context, path):
        count = self.count
        if callable(count):
            count = count(context)
        if not 0 <= count:
            raise RangeError("invalid count %s" % (count,))
        if not len(obj) == count:
            raise RangeError("expected %d elements, found %d" % (count, len(obj)))
        try:
            for subobj in obj:
                self.subcon._build(subobj, stream, context, path)
        except StopIteration:
            pass

    def _sizeof(self, context, path):
        try:
            count = self.count
            if callable(count):
                count = count(context)
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")
        return count * self.subcon._sizeof(context, path)

    def _emitparse(self, code):
        return "ListContainer((%s) for i in range(%s))" % (self.subcon._compileparse(code), self.count)


class Range(Subconstruct):
    r"""
    Homogenous array of elements, similar to C# generic T[], but works with unknown count of elements using following rules.

    Parses into a ListContainer (a list). Parsing stops when either max count was reached or an exception occured inside subcon. If count is less than min, raises RangeError. Builds from a list. If given list has more than max elements, raises RangeError. Size is defined as min (max) multiplied by subcon size, but only if min==max and subcon is fixed size.

    Operator [] can be used to make Array and Range instances (recommended).

    This class is used internally to implement :class:`~construct.core.GreedyRange`.

    :param min: integer or context lambda, the minimal count
    :param max: integer or context lambda, the maximal count
    :param subcon: Construct instance, subcon to process individual elements

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises StreamError: stream is not seekable and tellable
    :raises RangeError: consumed or produced too little or too many elements, or specified min and max are not valid
    :raises NotImplementedError: compiled (unless its Array)

    Can propagate any exception from the lambdas, possibly non-ConstructError.

    Example::

        >>> d = Range(3,5,Byte) or Byte[3:5]
        >>> d.parse(b'\x01\x02\x03\x04')
        [1,2,3,4]
        >>> d.build([1,2,3,4])
        b'\x01\x02\x03\x04'
        >>> d.build([1,2])
        construct.core.RangeError: expected from 3 to 5 elements, found 2
        >>> d.build([1,2,3,4,5,6])
        construct.core.RangeError: expected from 3 to 5 elements, found 6

        Alternative syntax (recommended):
        >>> Bytes[5] creates Array
        >>> Byte[3:5], Byte[3:], Byte[:5] creates Range
        >>> Byte[:] creates GreedyRange
    """
    __slots__ = ["min", "max"]

    def __init__(self, min, max, subcon):
        super(Range, self).__init__(subcon)
        self.min = min
        self.max = max

    def _parse(self, stream, context, path):
        min = self.min(context) if callable(self.min) else self.min
        max = self.max(context) if callable(self.max) else self.max
        if not 0 <= min <= max:
            raise RangeError("invalid min %s and max %s" % (min, max))
        obj = ListContainer()
        try:
            while len(obj) < max:
                fallback = _tell_stream(stream)
                obj.append(self.subcon._parse(stream, context, path))
        except StopIteration:
            pass
        except ExplicitError:
            raise
        except Exception:
            if len(obj) < min:
                raise RangeError("expected %d to %d elements, found %d" % (min, max, len(obj)))
            _seek_stream(stream, fallback)
        return obj

    def _build(self, obj, stream, context, path):
        min = self.min(context) if callable(self.min) else self.min
        max = self.max(context) if callable(self.max) else self.max
        if not 0 <= min <= max:
            raise RangeError("invalid min %s and max %s" % (min, max))
        if not min <= len(obj) <= max:
            raise RangeError("expected %d to %d elements, found %d" % (min, max, len(obj)))
        try:
            for subobj in obj:
                self.subcon._build(subobj, stream, context, path)
        except StopIteration:
            pass
        except ExplicitError:
            raise
        except Exception:
            if len(obj) < min:
                raise RangeError("expected %d to %d, found %d" % (min, max, len(obj)))
            else:
                raise

    def _sizeof(self, context, path):
        try:
            min = self.min(context) if callable(self.min) else self.min
            max = self.max(context) if callable(self.max) else self.max
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")
        if min == max:
            return min * self.subcon._sizeof(context, path)
        raise SizeofError("cannot calculate size, unless element count and size is fixed")

    def _emitdecompiled(self, code):
        return "Range(%s, %s, %s)" % (self.min, self.max, self.subcon._decompile(code), )


def GreedyRange(subcon):
    r"""
    Homogenous array of elements, similar to C# generic T[], but works with unknown count of elements by parsing until end of stream.

    Semantics are like for Range(0, 2**64, subcon).

    :param subcon: Construct instance, subcon to process individual elements

    See :class:`~construct.core.Range` for raisable exceptions.

    Example::

        >>> d = GreedyRange(Byte) or Byte[:]
        >>> d.build(range(8))
        b'\x00\x01\x02\x03\x04\x05\x06\x07'
        >>> d.parse(_)
        [0, 1, 2, 3, 4, 5, 6, 7]

        Alternative syntax (recommended):
        >>> Bytes[5] creates Array
        >>> Byte[3:5], Byte[3:], Byte[:5] creates Range
        >>> Byte[:] creates GreedyRange
    """
    return Range(0, 2**64, subcon)


class RepeatUntil(Subconstruct):
    r"""
    Homogenous array of elements, similar to C# generic IEnumerable<T>, that repeats until the predicate indicates it to stop. Note that the last element (that predicate indicated as True) is included in the return list.

    Parse iterates indefinately until last element passed the predicate. Build iterates indefinately over given list, until an element passed the precicate (or raises RepeatError if no element passed it). Size is undefined.

    :param predicate: lambda that takes (obj, list, context) and returns True to break or False to continue (or a truthy value)
    :param subcon: Construct instance, subcon used to parse and build each element

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises RepeatError: consumed all elements in the stream but neither passed the predicate
    :raises NotImplementedError: compiled

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = RepeatUntil(lambda x,lst,ctx: x > 7, Byte)
        >>> d.build(range(20))
        b'\x00\x01\x02\x03\x04\x05\x06\x07\x08'
        >>> d.parse(b"\x01\xff\x02")
        [1, 255]

        >>> d = RepeatUntil(lambda x,lst,ctx: lst[-2:] == [0,0], Byte)
        >>> d.parse(b"\x01\x00\x00\xff")
        [1, 0, 0]
    """
    __slots__ = ["predicate"]

    def __init__(self, predicate, subcon):
        super(RepeatUntil, self).__init__(subcon)
        self.predicate = predicate

    def _parse(self, stream, context, path):
        obj = ListContainer()
        while True:
            subobj = self.subcon._parse(stream, context, path)
            obj.append(subobj)
            if self.predicate(subobj, obj, context):
                return obj

    def _build(self, obj, stream, context, path):
        for i,subobj in enumerate(obj):
            self.subcon._build(subobj, stream, context, path)
            if self.predicate(subobj, obj[:i+1], context):
                break
        else:
            raise RepeatError("expected any item to match predicate, when building")

    def _sizeof(self, context, path):
        raise SizeofError("cannot calculate size, amount depends on actual data")


#===============================================================================
# specials
#===============================================================================
class Embedded(Subconstruct):
    r"""
    Special wrapper that allows outer many-subcons construct to merge fields from another many-subcons construct. Embedded does not change a field, only wraps it like a candy with a flag.

    .. warning:: 

        Can only be used between Struct Sequence FocusedSeq Union, although they can be used interchangably, for example Struct can embed fields from a Sequence. 

        EmbeddedBitStruct is not currently supported (yet to be resolved).

    Parsing building and size are deferred to subcon.

    :param subcon: Construct instance, field to embed inside outer struct or sequence

    Example::

        >>> outer = Struct(
        ...     Embedded(Struct(
        ...         "data" / Bytes(4),
        ...     )),
        ... )
        >>> outer.parse(b"1234")
        Container(data=b'1234')
    """

    def __init__(self, subcon):
        super(Embedded, self).__init__(subcon)
        self.flagembedded = True

    def _emitparse(self, code):
        return self.subcon._compileparse(code)


class Renamed(Subconstruct):
    r"""
    Special wrapper that allows outer Struct or Sequence to see a field as having a name (or a different name). Library classes do not have names (its None). Renamed does not change a field, only wraps it like a candy with a label. Used internally by / operator.

    Also this wrapper is responsible for building a path info (a chain of names) that gets attached to error message when parsing, building, or sizeof fails. Fields that are not named do not appear in the path string.

    Parsing building and size are deferred to subcon.

    :param newname: string
    :param subcon: Construct instance, field to rename

    Example::

        >>> "number" / Int32ub
        <Renamed: number>
    """

    def __init__(self, newname, subcon):
        super(Renamed, self).__init__(subcon)
        self.name = newname

    def _parse(self, stream, context, path):
        try:
            path += " -> %s" % (self.name,)
            return self.subcon._parse(stream, context, path)
        except ConstructError as e:
            if "\n" in str(e):
                raise
            raise e.__class__("%s\n    %s" % (e, path))

    def _build(self, obj, stream, context, path):
        try:
            path += " -> %s" % (self.name,)
            return self.subcon._build(obj, stream, context, path)
        except ConstructError as e:
            if "\n" in str(e):
                raise
            raise e.__class__("%s\n    %s" % (e, path))

    def _sizeof(self, context, path):
        try:
            path += " -> %s" % (self.name,)
            return self.subcon._sizeof(context, path)
        except ConstructError as e:
            if "\n" in str(e):
                raise
            raise e.__class__("%s\n    %s" % (e, path))

    def _emitparse(self, code):
        return self.subcon._compileparse(code)


#===============================================================================
# miscellaneous
#===============================================================================
class Const(Subconstruct):
    r"""
    Field enforcing a constant. It is used for file signatures, to validate that the given pattern exists. Data in the stream must strictly match the specified value.

    Note that a variable sized subcon may still provide positive verification. Const does not consume a precomputed amount of bytes, but depends on the subcon to read the appropriate amount (eg. VarInt is acceptable). Whatever subcon parses into, gets compared against the specified value.

    Parses using subcon and return its value (after checking). Builds using subcon from nothing (or given object, if not None). Size is deferred to subcon.

    :param value: expected value, usually a bytes literal
    :param subcon: optional, Construct instance, subcon used to build value from, assumed to be Bytes if value parameter was a bytes literal

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises ConstError: parsed data does not match specified value, or building from wrong value
    :raises StringError: given non-bytes value, perhaps unicode

    Example::

        >>> d = Const(b"IHDR")
        >>> d.build(None)
        b'IHDR'
        >>> d.parse(b"JPEG")
        construct.core.ConstError: expected b'IHDR' but parsed b'JPEG'

        >>> d = Const(255, Int32ul)
        >>> d.build(None)
        b'\xff\x00\x00\x00'
    """
    __slots__ = ["value"]

    def __init__(self, value, subcon=None):
        if subcon is None:
            if not isinstance(value, bytestringtype):
                raise StringError("given non-bytes value, perhaps unicode? %r" % (value,))
            subcon = Bytes(len(value))
        super(Const, self).__init__(subcon)
        self.value = value
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        obj = self.subcon._parse(stream, context, path)
        if obj != self.value:
            raise ConstError("parsing expected %r but parsed %r" % (self.value, obj))
        return obj

    def _build(self, obj, stream, context, path):
        if obj not in (None, self.value):
            raise ConstError("building expected None or %r but got %r" % (self.value, obj))
        return self.subcon._build(self.value, stream, context, path)

    def _sizeof(self, context, path):
        return self.subcon._sizeof(context, path)

    def _emitparse(self, code):
        code.append("""
            def parse_const(value, expected):
                assert value == expected
                return value
        """)
        return "parse_const(%s, %r)" % (self.subcon._compileparse(code), self.value,)


class Computed(Construct):
    r"""
    Field computing a value from the context dictionary or some outer source like os.urandom or random module. Underlying byte stream is unaffected. The source can be non-deterministic.

    Parsing and Building return the value returned by the context lambda (although a constant value can also be used). Size is defined as 0 because parsing and building does not consume or produce bytes into the stream.

    :param func: context lambda or constant value

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::
        >>> d = Struct(
        ...     "width" / Byte,
        ...     "height" / Byte,
        ...     "total" / Computed(this.width * this.height),
        ... )
        >>> d.build(dict(width=4,height=5))
        b'\x04\x05'
        >>> d.parse(b"12")
        Container(width=49)(height=50)(total=2450)

        >>> d = Computed(7)
        >>> d.parse(b"")
        7
        >>> d = Computed(lambda ctx: 7)
        >>> d.parse(b"")
        7

        >>> import os
        >>> d = Computed(lambda ctx: os.urandom(10))
        >>> d.parse(b"")
        b'\x98\xc2\xec\x10\x07\xf5\x8e\x98\xc2\xec'
    """
    __slots__ = ["func"]

    def __init__(self, func):
        super(Computed, self).__init__()
        self.func = func
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        return self.func(context) if callable(self.func) else self.func

    def _build(self, obj, stream, context, path):
        return self.func(context) if callable(self.func) else self.func

    def _sizeof(self, context, path):
        return 0

    def _emitparse(self, code):
        return "%r" % (self.func,)


class Rebuild(Subconstruct):
    r"""
    Field where building does not require a value, because the value gets recomputed when needed. Comes handy when building a Struct from a dict with missing keys.

    Parsing defers to subcon. Building is defered to subcon, but it builds from a value provided by the context lambda (or constant). Size is defered to subcon.

    .. seealso:: Useful for length and count fields when :class:`~construct.core.Prefixed` and :class:`~construct.core.PrefixedArray` cannot be used.

    :param subcon: Construct instance, subcon to defer to
    :param func: context lambda or constant value

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Struct(
        ...     "count" / Rebuild(Byte, len_(this.items)),
        ...     "items" / Byte[this.count],
        ... )
        >>> d.build(dict(items=[1,2,3]))
        b'\x03\x01\x02\x03'
    """
    __slots__ = ["func"]

    def __init__(self, subcon, func):
        super(Rebuild, self).__init__(subcon)
        self.func = func
        self.flagbuildnone = True

    def _build(self, obj, stream, context, path):
        obj = self.func(context) if callable(self.func) else self.func
        self.subcon._build(obj, stream, context, path)
        return obj

    def _emitparse(self, code):
        return self.subcon._compileparse(code)


class Default(Subconstruct):
    r"""
    Field where building does not require a value, because the value gets taken from default. Comes handy when building a Struct from a dict with missing keys.

    Parsing defers to subcon. Building is defered to subcon, but it builds from a default (if given object is None) or from given object. Building does not require a value, but can accept one. Size is defered to subcon.

    :param subcon: Construct instance, subcon to defer to
    :param value: context lambda or constant value

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Struct(
        ...     "a" / Default(Byte, 0),
        ... )
        >>> d.build(dict(a=1))
        b'\x01'
        >>> d.build(dict())
        b'\x00'
    """
    __slots__ = ["value"]

    def __init__(self, subcon, value):
        super(Default, self).__init__(subcon)
        self.value = value
        self.flagbuildnone = True

    def _build(self, obj, stream, context, path):
        obj = (self.value(context) if callable(self.value) else self.value) if obj is None else obj
        self.subcon._build(obj, stream, context, path)
        return obj

    def _emitparse(self, code):
        return self.subcon._compileparse(code)


class Check(Construct):
    r"""
    Checks for a condition, and raises ValidationError if the check fails.

    Parsing and building return nothing (but check the condition). Size is defined as 0. Stream is not affected by either operation.

    :param func: bool or context lambda, that gets run on parsing and building

    :raises ValidationError: lambda returned false

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        Check(lambda ctx: len(ctx.payload.data) == ctx.payload_len)
        Check(len_(this.payload.data) == this.payload_len)
    """

    def __init__(self, func):
        super(Check, self).__init__()
        self.func = func
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        passed = self.func(context) if callable(self.func) else self.func
        if not passed:
            raise ValidationError("check failed during parsing")

    def _build(self, obj, stream, context, path):
        passed = self.func(context) if callable(self.func) else self.func
        if not passed:
            raise ValidationError("check failed during building")

    def _sizeof(self, context, path):
        return 0

    def _emitparse(self, code):
        code.append("""
            def parse_check(condition):
                assert condition
        """)
        return "parse_check(%r)" % (self.func,)


@singleton
class Error(Construct):
    r"""
    Raises ExplicitError, unconditionally.

    Parsing and building always raise ExplicitError. Size is undefined.

    :raises ExplicitError: unconditionally, on parsing and building

    Example::

        >>> d = Struct("num"/Byte, Error)
        >>> d.parse(b"data...")
        construct.core.ExplicitError: Error field was activated during parsing
    """

    def __init__(self):
        super(self.__class__, self).__init__()
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        raise ExplicitError("Error field was activated during parsing")

    def _build(self, obj, stream, context, path):
        raise ExplicitError("Error field was activated during building")

    def _emitdecompiled(self, code):
        return "Error"

    def _emitparse(self, code):
        code.append("""
            def parse_error():
                assert False
        """)
        return "parse_error()"


class FocusedSeq(Construct):
    r"""
    Allows constructing more elaborate "adapters" than Adapter class.

    Parse does parse all subcons in sequence, but returns only the element that was selected (discards other values). Build does build all subcons in sequence, where each gets build from nothing (except the selected subcon which is given the object). Size is the sum of all subcon sizes, unless any subcon raises SizeofError.

    This class does context nesting, meaning its members are given access to a new dictionary where the "_" entry points to the outer context. When parsing, each member gets parsed and subcon parse return value is inserted into context under matching key only if the member was named. When building, the matching entry gets inserted into context before subcon gets build, and if subcon build returns a new value (not None) that gets replaced in the context.

    This class supports embedding. :class:`~construct.core.Embedded` semantics dictate, that during instance creation (in ctor), each field is checked for embedded flag, and its subcons members merged. This changes behavior of some code examples. Only few classes are supported: Struct Sequence FocusedSeq Union, although those can be used interchangably (a Struct can embed a Sequence, or rather its members). EmbeddedBitStruct is not currently supported (yet to be resolved).

    This class is used internally to implement :class:`~construct.core.PrefixedArray`.

    :param parsebuildfrom: integer index or string name or context lambda, selects a subcon
    :param \*subcons: Construct instances, list of members, some can be named
    :param \*\*kw: Construct instances, list of members (requires Python 3.6)

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises IndexError: selector does not match any subcon
    :raises KeyError: selector does not match any subcon

    :raises NotImplementedError: compiled with non-constant selector

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Excample::

        >>> d = FocusedSeq(1 or "num", Const(b"SIG"), "num"/Byte, Terminated)
        >>> d.parse(b"SIG\xff")
        255
        >>> d.build(255)
        b'SIG\xff'

        PrefixedArray <--> FocusedSeq(1,
            "count" / Rebuild(lengthfield, len_(this.items)),
            "items" / subcon[this.count],
        )
    """

    def __init__(self, parsebuildfrom, *subcons, **kw):
        super(FocusedSeq, self).__init__()
        self.parsebuildfrom = parsebuildfrom
        subcons = list(subcons) + list(k/v for k,v in kw.items())
        self.subcons = mergefields(*subcons)

    def _parse(self, stream, context, path):
        context = Container(_ = context)
        parsebuildfrom = self.parsebuildfrom
        if callable(parsebuildfrom):
            parsebuildfrom = parsebuildfrom(context)
        if isinstance(parsebuildfrom, int):
            index = parsebuildfrom
            self.subcons[index]  # raises IndexError
        if isinstance(parsebuildfrom, str):
            index = {sc.name:i for i,sc in enumerate(self.subcons) if sc.name}[parsebuildfrom] # raises KeyError
        for i,sc in enumerate(self.subcons):
            parseret = sc._parse(stream, context, path)
            if sc.name:
                context[sc.name] = parseret
            if i == index:
                finalret = parseret
        return finalret

    def _build(self, obj, stream, context, path):
        context = Container(_ = context)
        parsebuildfrom = self.parsebuildfrom
        if callable(parsebuildfrom):
            parsebuildfrom = parsebuildfrom(context)
        if isinstance(parsebuildfrom, int):
            index = parsebuildfrom
            self.subcons[index]  # raises IndexError
        if isinstance(parsebuildfrom, str):
            index = {sc.name:i for i,sc in enumerate(self.subcons) if sc.name}[parsebuildfrom] # raises KeyError
        context[index] = obj
        sc = self.subcons[index]
        if sc.name:
            context[sc.name] = obj
        for i,sc in enumerate(self.subcons):
            buildret = sc._build(obj if i==index else None, stream, context, path)
            if buildret is not None:
                if sc.name:
                    context[sc.name] = buildret
            if i == index:
                finalret = buildret
        return finalret

    def _sizeof(self, context, path):
        context = Container(_ = context)
        try:
            return sum(sc._sizeof(context, path) for sc in self.subcons)
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")

    def _emitparse(self, code):
        if callable(self.parsebuildfrom):
            raise NotImplementedError("FocusedSeq does not compile non-constant selectors")
        fname = "parse_focusedseq_%s" % code.allocateId()
        block = """
            def %s(io, this):
                result = []
                this = Container(_ = this)
        """ % (fname, )
        for sc in self.subcons:
            block += """
                result.append(%s)
            """ % (sc._compileparse(code), )
            if sc.name:
                block += """
                this[%r] = result[-1]
                """ % (sc.name, )
        parsebuildfrom = self.parsebuildfrom
        if isinstance(parsebuildfrom, int):
            index = parsebuildfrom
            self.subcons[index]  # raises IndexError
        if isinstance(parsebuildfrom, str):
            index = {sc.name:i for i,sc in enumerate(self.subcons) if sc.name}[parsebuildfrom] # raises KeyError
        block += """
                return result[%s]
        """ % (index, )
        code.append(block)
        return "%s(io, this)" % (fname,)


@singleton
class Numpy(Construct):
    r"""
    Preserves numpy arrays (both shape, dtype and values).

    Parses using `numpy.load() <https://docs.scipy.org/doc/numpy/reference/generated/numpy.load.html#numpy.load>`_ and builds using `numpy.save() <https://docs.scipy.org/doc/numpy/reference/generated/numpy.save.html#numpy.save>`_ functions, using Numpy binary protocol. Size is undefined.

    :raises ImportError: numpy could not be imported during parsing or building
    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes

    Can propagate numpy.load() and numpy.save() exceptions.

    Example::

        >>> import numpy
        >>> a = numpy.asarray([1,2,3])
        >>> Numpy.build(a)
        b"\x93NUMPY\x01\x00F\x00{'descr': '<i8', 'fortran_order': False, 'shape': (3,), }            \n\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00"
        >>> Numpy.parse(_)
        array([1, 2, 3])
    """

    def __init__(self):
        super(self.__class__, self).__init__()

    def _parse(self, stream, context, path):
        import numpy
        return numpy.load(stream)

    def _build(self, obj, stream, context, path):
        import numpy
        numpy.save(stream, obj)

    def _emitdecompiled(self, code):
        return "Numpy"


class NamedTuple(Adapter):
    r"""
    Both arrays, structs, and sequences can be mapped to a namedtuple from `collections module <https://docs.python.org/3/library/collections.html#collections.namedtuple>`_. To create a named tuple, you need to provide a name and a sequence of fields, either a string with space-separated names or a list of string names, like the standard namedtuple.

    Parses into a collections.namedtuple instance, and builds from such instance (although it also builds from lists and dicts). Size is undefined.

    :param tuplename: string
    :param tuplefields: string or list of strings
    :param subcon: Construct instance, either Struct Sequence Array Range

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises AdaptationError: subcon is neither Struct Sequence Array Range

    Can propagate collections exceptions.

    Example::

        >>> d = NamedTuple("coord", "x y z", Byte[3])
        >>> d = NamedTuple("coord", "x y z", Byte >> Byte >> Byte)
        >>> d = NamedTuple("coord", "x y z", "x"/Byte + "y"/Byte + "z"/Byte)
        >>> d.parse(b"123")
        coord(x=49, y=50, z=51)
    """
    __slots__ = ["tuplename", "tuplefields"]

    def __init__(self, tuplename, tuplefields, subcon):
        if not isinstance(subcon, (Struct,Sequence,Array,Range)):
            raise AdaptationError("subcon is neither Struct Sequence Array Range")
        super(NamedTuple, self).__init__(subcon)
        self.tuplename = tuplename
        self.tuplefields = tuplefields
        import collections
        self.factory = collections.namedtuple(tuplename, tuplefields)

    def _decode(self, obj, context):
        # Note: Sequence happens to be also a Struct, thus ordering
        if isinstance(self.subcon, (Sequence,Array,Range)):
            return self.factory(*obj)
        if isinstance(self.subcon, Struct):
            return self.factory(**obj)
        raise AdaptationError("subcon is neither Struct Sequence Array Range")

    def _encode(self, obj, context):
        # Note: Sequence happens to be also a Struct, thus ordering
        if isinstance(self.subcon, (Sequence,Array,Range)):
            return list(obj)
        if isinstance(self.subcon, Struct):
            return {sc.name:getattr(obj,sc.name) for sc in self.subcon.subcons if sc.name}
        raise AdaptationError("subcon is neither Struct Sequence Array Range")

    def _emitparse(self, code):
        fname = "factory_%s" % code.allocateId()
        code.append("""
            %s = collections.namedtuple(%r, %r)
        """ % (fname, self.tuplename, self.tuplefields, ))
        # Note: Sequence happens to be also a Struct, thus ordering
        if isinstance(self.subcon, (Sequence,Array,Range)):
            return "%s(*(%s))" % (fname, self.subcon._compileparse(code), )
        if isinstance(self.subcon, Struct):
            return "%s(**(%s))" % (fname, self.subcon._compileparse(code), )
        raise AdaptationError("subcon is neither Struct Sequence Array Range")


#===============================================================================
# conditional
#===============================================================================
class Union(Construct):
    r"""
    Treats the same data as multiple constructs (similar to C union) so you can look at the data in multiple views. Fields are usually named (so parsed values are inserted into dictionary under same name). :class:`~construct.core.Embedded` fields do not need to (and should not) be named.

    Parses subcons in sequence, and reverts the stream back to original position after each subcon. Afterwards, advances the stream by selected subcon. Builds from any subcon that has a matching key in given dict. Size is undefined (because parsefrom is not used for building).

    This class does context nesting, meaning its members are given access to a new dictionary where the "_" entry points to the outer context. When parsing, each member gets parsed and subcon parse return value is inserted into context under matching key only if the member was named. When building, the matching entry gets inserted into context before subcon gets build, and if subcon build returns a new value (not None) that gets replaced in the context.

    This class supports embedding. :class:`~construct.core.Embedded` semantics dictate, that during instance creation (in ctor), each field is checked for embedded flag, and its subcons members merged. This changes behavior of some code examples. Only few classes are supported: Struct Sequence FocusedSeq Union, although those can be used interchangably (a Struct can embed a Sequence, or rather its members). EmbeddedBitStruct is not currently supported (yet to be resolved).

    .. warning:: If you skip `parsefrom` parameter then stream will be left back at starting offset, not seeked to any common denominator.

    :param parsefrom: how to leave stream after parsing, can be integer index or string name selecting a subcon, or None (leaves stream at initial offset, the default), or context lambda
    :param \*subcons: Construct instances, list of members, some can be anonymous
    :param \*\*kw: Construct instances, list of members (requires Python 3.6)

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises StreamError: stream is not seekable and tellable
    :raises UnionError: selector does not match any subcon, or dict given to build does not contain any keys matching any subcon
    :raises IndexError: selector does not match any subcon
    :raises KeyError: selector does not match any subcon

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Union(0, "raw"/Bytes(8), "ints"/Int32ub[2], "shorts"/Int16ub[4], "chars"/Byte[8])
        >>> d.parse(b"12345678")
        Container(raw=b'12345678')(ints=[825373492, 892745528])(shorts=[12594, 13108, 13622, 14136])(chars=[49, 50, 51, 52, 53, 54, 55, 56])
        >>> d.build(dict(chars=range(8)))
        b'\x00\x01\x02\x03\x04\x05\x06\x07'

        Alternative syntax, but requires Python 3.6:
        >>> Union(0, raw=Bytes(8), ints=Int32ub[2], shorts=Int16ub[4], chars=Byte[8])
    """
    __slots__ = ["parsefrom", "subcons"]

    def __init__(self, parsefrom, *subcons, **kw):
        if isinstance(parsefrom, Construct):
            raise UnionError("parsefrom should be either: None int str context-function")
        super(Union, self).__init__()
        self.parsefrom = parsefrom
        subcons = list(subcons) + list(k/v for k,v in kw.items())
        self.subcons = mergefields(*subcons)

    def _parse(self, stream, context, path):
        obj = Container()
        context = Container(_ = context)
        fallback = _tell_stream(stream)
        forwards = {}
        for i,sc in enumerate(self.subcons):
            subobj = sc._parse(stream, context, path)
            if sc.name:
                obj[sc.name] = subobj
                context[sc.name] = subobj
            forwards[i] = _tell_stream(stream)
            if sc.name:
                forwards[sc.name] = _tell_stream(stream)
            _seek_stream(stream, fallback)
        parsefrom = self.parsefrom
        if callable(parsefrom):
            parsefrom = parsefrom(context)
        if parsefrom is not None:
            _seek_stream(stream, forwards[parsefrom]) # raises KeyError
        return obj

    def _build(self, obj, stream, context, path):
        context = Container(_ = context)
        context.update(obj)
        for sc in self.subcons:
            if sc.flagbuildnone:
                subobj = obj.get(sc.name, None)
            elif sc.name in obj:
                subobj = obj[sc.name]
            else:
                continue

            if sc.name:
                context[sc.name] = subobj

            buildret = sc._build(subobj, stream, context, path)
            if buildret is not None:
                if sc.name:
                    context[sc.name] = buildret
            return buildret
        else:
            raise UnionError("cannot build, none of subcons were found in the dictionary %r" % (obj, ))

    def _sizeof(self, context, path):
        raise SizeofError("Union builds depending on actual object dict, size is unknown")

    def _emitparse(self, code):
        if callable(self.parsefrom):
            raise NotImplementedError("Union does not compile non-constant parsefrom")
        fname = "parse_union_%s" % code.allocateId()
        block = """
            def %s(io, this):
                this = Container(_ = this)
                fallback = io.tell()
        """ % (fname, )
        if isinstance(self.parsefrom, type(None)):
            index = -1
            skipfallback = False
            skipforward = True
        if isinstance(self.parsefrom, int):
            index = self.parsefrom
            self.subcons[index] # raises IndexError
            skipfallback = True
            skipforward = self.subcons[index].sizeof() == self.subcons[-1].sizeof()
        if isinstance(self.parsefrom, str):
            index = {sc.name:i for i,sc in enumerate(self.subcons) if sc.name}[self.parsefrom] # raises KeyError
            skipfallback = True
            skipforward = self.subcons[index].sizeof() == self.subcons[-1].sizeof()

        for i,sc in enumerate(self.subcons):
            block += """
                %s%s
            """ % ("this[%r] = " % sc.name if sc.name else "", sc._compileparse(code))
            if i == index and not skipforward:
                block += """
                forward = io.tell()
                """
            if i < len(self.subcons)-1:
                block += """
                io.seek(fallback)
                """
        if not skipfallback:
            block += """
                io.seek(fallback)
            """
        if not skipforward:
            block += """
                io.seek(forward)
            """
        block += """
                del this._
                return this
        """
        code.append(block)
        return "%s(io, this)" % (fname,)


class Select(Construct):
    r"""
    Selects the first matching subconstruct.

    Parses and builds by literally trying each subcon in sequence until one of them parses or builds without exception. Stream gets reverted back to original position after each failed attempt. Size is not defined.

    :param \*subcons: Construct instances, list of members, some can be anonymous
    :param \*\*kw: Construct instances, list of members (requires Python 3.6)
    :param includename: indicates whether to include name of selected subcon in the return value of parsing, default is False

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises StreamError: stream is not seekable and tellable
    :raises SelectError: neither subcon succeded when parsing or building

    Example::

        >>> d = Select(Int32ub, CString(encoding="utf8"))
        >>> d.build(1)
        b'\x00\x00\x00\x01'
        >>> d.build(u"Афон")
        b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd\x00'

        Alternative syntax, but requires Python 3.6:
        >>> Select(num=Int32ub, text=CString(encoding="utf8"))
    """
    __slots__ = ["subcons", "includename"]

    def __init__(self, *subcons, **kw):
        super(Select, self).__init__()
        self.subcons = list(subcons) + list(k/v for k,v in kw.items() if k != "includename")
        self.flagbuildnone = all(sc.flagbuildnone for sc in self.subcons)
        self.flagembedded = all(sc.flagembedded for sc in self.subcons)
        self.includename = kw.pop("includename", False)

    def _parse(self, stream, context, path):
        for sc in self.subcons:
            fallback = _tell_stream(stream)
            try:
                obj = sc._parse(stream, context, path)
            except ExplicitError:
                raise
            except ConstructError:
                _seek_stream(stream, fallback)
            else:
                return (sc.name,obj) if self.includename else obj
        raise SelectError("no subconstruct matched")

    def _build(self, obj, stream, context, path):
        if self.includename:
            name, obj = obj
            for sc in self.subcons:
                if sc.name == name:
                    return sc._build(obj, stream, context, path)
        else:
            for sc in self.subcons:
                try:
                    data = sc.build(obj, **context)
                except ExplicitError:
                    raise
                except Exception:
                    pass
                else:
                    _write_stream(stream, len(data), data)
                    return
        raise SelectError("no subconstruct matched: %s" % (obj,))


def Optional(subcon):
    r"""
    Makes an optional field.

    Parsing attempts to parse subcon. If sub-parsing fails, returns None and reports success. Building attempts to build subcon. If sub-building fails, writes nothing and reports success. Size is undefined, because whether bytes would be consumed or produced depends on actual data and actual context.

    :param subcon: Construct instance

    Example::

        Optional  <-->  Select(subcon, Pass)

        >>> d = Optional(Int64ul)
        >>> d.parse(b"12345678")
        4050765991979987505
        >>> d.parse(b"")
        None
        >>> d.build(1)
        b'\x01\x00\x00\x00\x00\x00\x00\x00'
        >>> d.build(None)
        b''
    """
    return Select(subcon, Pass)


def If(condfunc, subcon):
    r"""
    If-then conditional construct.

    Parsing evaluates condition, if True then subcon is parsed, otherwise just returns None. Building also evaluates condition, if True then subcon gets build from, otherwise does nothing. Size is either same as subcon or 0, depending how condfunc evaluates.

    :param condfunc: bool or context lambda (or a truthy value)
    :param subcon: Construct instance, used if condition indicates True

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        If <--> IfThenElse(condfunc, subcon, Pass)

        >>> d = If(this.x > 0, Byte)
        >>> d.build(255, x=1)
        b'\xff'
        >>> d.build(255, x=0)
        b''
    """
    return IfThenElse(condfunc, subcon, Pass)


def IfThenElse(condfunc, thensubcon, elsesubcon):
    r"""
    If-then-else conditional construct, similar to ternary operator.

    Parsing and building evaluates condition, and defers to either subcon depending on the value.
    Size is computed the same way.

    :param condfunc: bool or context lambda (or a truthy value)
    :param thensubcon: Construct instance, used if condition indicates True
    :param elsesubcon: Construct instance, used if condition indicates False

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = IfThenElse(this.x > 0, VarInt, Byte)
        >>> d.build(255, dict(x=1))
        b'\xff\x01'
        >>> d.build(255, dict(x=0))
        b'\xff'
    """
    macro = Switch(
        lambda ctx: bool(condfunc(ctx)) if callable(condfunc) else bool(condfunc),
        {True:thensubcon, False:elsesubcon},
    )
    def _emitparse(self, code):
        return "(%s) if (%s) else (%s)" % (thensubcon._compileparse(code), condfunc, elsesubcon._compileparse(code), )
    return CompilableMacro(macro, _emitparse)


class Switch(Construct):
    r"""
    A conditional branch.

    Parsing and building evaluate keyfunc and select a subcon based on the value and dictionary entries. Dictionary (cases) maps values into subcons. If no case matches and no default field is given, SwitchError is raised. Note that default is a Construct instance, not a dictionary key. Size is evaluated in same way as parsing and building.

    .. warning:: You can use Embedded(Switch(...)) but not Switch(Embedded(...)). Same applies to If and IfThenElse macros.

    :param keyfunc: context lambda or constant, that matches some key in cases
    :param cases: dict mapping keys to Construct instances
    :param default: optional, Construct instance, used when keyfunc is not found in cases, Pass is a possible value for this parameter, default is a class that raises SwitchError
    :param includekey: optional, bool, whether to include the key in return value when parsing, default is False

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises SwitchError: keyfunc value is not in the dict and no default was given

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Switch(this.n, { 1:Int8ub, 2:Int16ub, 4:Int32ub })
        >>> d.build(5, n=1)
        b'\x05'
        >>> d.build(5, n=4)
        b'\x00\x00\x00\x05'
    """

    @singleton
    class NoDefault(Construct):
        def _parse(self, stream, context, path):
            raise SwitchError("no default case defined, parsing failed")
        def _build(self, obj, stream, context, path):
            raise SwitchError("no default case defined, building failed")
        def _sizeof(self, context, path):
            raise SwitchError("no default case defined, sizeof failed")

    __slots__ = ["subcons", "keyfunc", "cases", "default", "includekey"]

    def __init__(self, keyfunc, cases, default=NoDefault, includekey=False):
        super(Switch, self).__init__()
        self.keyfunc = keyfunc
        self.cases = cases
        self.default = default
        self.includekey = includekey
        allcases = list(cases.values())
        if default is not self.NoDefault:
            allcases.append(default)
        self.flagbuildnone = all(sc.flagbuildnone for sc in allcases)
        self.flagembedded = all(sc.flagembedded for sc in allcases)

    def _parse(self, stream, context, path):
        key = self.keyfunc(context) if callable(self.keyfunc) else self.keyfunc
        obj = self.cases.get(key, self.default)._parse(stream, context, path)
        return (key,obj) if self.includekey else obj

    def _build(self, obj, stream, context, path):
        if self.includekey:
            key,obj = obj
        else:
            key = self.keyfunc(context) if callable(self.keyfunc) else self.keyfunc
        case = self.cases.get(key, self.default)
        return case._build(obj, stream, context, path)

    def _sizeof(self, context, path):
        try:
            key = self.keyfunc(context) if callable(self.keyfunc) else self.keyfunc
            sc = self.cases.get(key, self.default)
            return sc._sizeof(context, path)
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")


class StopIf(Construct):
    r"""
    Checks for a condition, and stops certain classes (Struct Sequence Range FocusedSeq) from parsing or building further.

    Parsing and building check the condition, and raise StopIteration if indicated. Size is not defined.

    :param condfunc: bool or context lambda (or truthy value)

    :raises StopIteration: used internally

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> Struct('x'/Byte, StopIf(this.x == 0), 'y'/Byte)
        >>> Sequence('x'/Byte, StopIf(this.x == 0), 'y'/Byte)
        >>> GreedyRange(FocusedSeq(0, 'x'/Byte, StopIf(this.x == 0)))
    """

    def __init__(self, condfunc):
        super(StopIf, self).__init__()
        self.condfunc = condfunc
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        condfunc = self.condfunc
        if callable(condfunc):
            condfunc = condfunc(context)
        if condfunc:
            raise StopIteration

    def _build(self, obj, stream, context, path):
        condfunc = self.condfunc
        if callable(condfunc):
            condfunc = condfunc(context)
        if condfunc:
            raise StopIteration

    def _sizeof(self, context, path):
        return SizeofError("StopIf cannot determine size because it depends on actual context which then depends on actual data and outer constructs")


#===============================================================================
# alignment and padding
#===============================================================================
def Padding(length, pattern=b"\x00"):
    r"""
    Appends null bytes.

    Parsing consumes specified amount of bytes and discards it. Building writes specified pattern byte multiplied into specified length. Size is same as specified.

    :param length: integer or context lambda, length of the padding
    :param pattern: b-character, padding pattern, default is \\x00

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises PaddingError: length was negative
    :raises PaddingError: pattern was not bytes (b-character)

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Padding(4)
        >>> d.build(None)
        b'\x00\x00\x00\x00'
        >>> d.parse(b"****")
        None
        >>> d.sizeof()
        4
    """
    return Padded(length, Pass, pattern=pattern)


class Padded(Subconstruct):
    r"""
    Appends additional null bytes to achieve a length.

    Note that subcon can actually be variable size, it is the eventual amount of bytes that is read or written during parsing or building that determines actual padding.

    Parsing first parses subcon, then consumes an amount of bytes to sum up to specified length, and discards it. Building first builds subcon, then writes specified pattern byte to sum up to specified length. Size is same as specified.

    :param length: integer or context lambda, length of the padding
    :param subcon: Construct instance
    :param pattern: b-character, padding pattern, default is \\x00

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises PaddingError: length was negative, or subcon read or written more than the length (would cause negative pad)
    :raises PaddingError: pattern was not bytes (b-character)

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Padded(4, Byte)
        >>> d.build(255)
        b'\xff\x00\x00\x00'
        >>> d.parse(_)
        255
        >>> d.sizeof()
        4

        >>> d = Padded(4, VarInt)
        >>> d.build(1)
        b'\x01\x00\x00\x00'
        >>> d.build(70000)
        b'\xf0\xa2\x04\x00'
    """
    __slots__ = ["length", "pattern"]

    def __init__(self, length, subcon, pattern=b"\x00"):
        if not isinstance(pattern, bytes) or len(pattern) != 1:
            raise PaddingError("pattern expected to be bytes of length 1")
        super(Padded, self).__init__(subcon)
        self.length = length
        self.pattern = pattern

    def _parse(self, stream, context, path):
        length = self.length(context) if callable(self.length) else self.length
        position1 = _tell_stream(stream)
        obj = self.subcon._parse(stream, context, path)
        position2 = _tell_stream(stream)
        padlen = length - (position2 - position1)
        if padlen < 0:
            raise PaddingError("subcon parsed %d bytes but was allowed only %d" % (position2-position1, length))
        _read_stream(stream, padlen)
        return obj

    def _build(self, obj, stream, context, path):
        length = self.length(context) if callable(self.length) else self.length
        position1 = _tell_stream(stream)
        subobj = self.subcon._build(obj, stream, context, path)
        position2 = _tell_stream(stream)
        padlen = length - (position2 - position1)
        if padlen < 0:
            raise PaddingError("subcon build %d bytes but was allowed only %d" % (position2-position1, length))
        _write_stream(stream, padlen, self.pattern * padlen)
        return subobj

    def _sizeof(self, context, path):
        try:
            return self.length(context) if callable(self.length) else self.length
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")

    def _emitparse(self, code):
        return "(%s, read_bytes(io, %s - %s))[0]" % (self.subcon._compileparse(code), self.length, self.subcon.sizeof())


class Aligned(Subconstruct):
    r"""
    Appends additional null bytes to achieve a length that is shortest multiple of a modulus.

    Note that subcon can actually be variable size, it is the eventual amount of bytes that is read or written during parsing or building that determines actual padding.

    Parsing first parses subcon, then consumes an amount of bytes to sum up to specified length, and discards it. Building first builds subcon, then writes specified pattern byte to sum up to specified length. Size is subcon size plus modulo remainder, unless SizeofError was raised.

    :param modulus: integer or context lambda, modulus to final length
    :param subcon: Construct instance
    :param pattern: optional, b-character, padding pattern, default is \\x00

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises PaddingError: modulus was less than 2
    :raises PaddingError: pattern was not bytes (b-character)

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Aligned(4, Int16ub)
        >>> d.parse(b'\x00\x01\x00\x00')
        1
        >>> d.sizeof()
        4
    """
    __slots__ = ["subcon", "modulus", "pattern"]

    def __init__(self, modulus, subcon, pattern=b"\x00"):
        if not isinstance(pattern, bytes) or len(pattern) != 1:
            raise PaddingError("pattern expected to be bytes character")
        super(Aligned, self).__init__(subcon)
        self.modulus = modulus
        self.pattern = pattern

    def _parse(self, stream, context, path):
        modulus = self.modulus(context) if callable(self.modulus) else self.modulus
        if modulus < 2:
            raise PaddingError("expected modulo 2 or greater")
        position1 = _tell_stream(stream)
        obj = self.subcon._parse(stream, context, path)
        position2 = _tell_stream(stream)
        pad = -(position2 - position1) % modulus
        _read_stream(stream, pad)
        return obj

    def _build(self, obj, stream, context, path):
        modulus = self.modulus(context) if callable(self.modulus) else self.modulus
        if modulus < 2:
            raise PaddingError("expected modulo 2 or greater")
        position1 = _tell_stream(stream)
        subobj = self.subcon._build(obj, stream, context, path)
        position2 = _tell_stream(stream)
        pad = -(position2 - position1) % modulus
        _write_stream(stream, pad, self.pattern * pad)
        return subobj

    def _sizeof(self, context, path):
        try:
            modulus = self.modulus(context) if callable(self.modulus) else self.modulus
            if modulus < 2:
                raise PaddingError("expected modulo 2 or greater")
            subconlen = self.subcon._sizeof(context, path)
            return subconlen + (-subconlen % modulus)
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")

    def _emitparse(self, code):
        return "(%s, read_bytes(io, -%s %% %s))[0]" % (self.subcon._compileparse(code), self.subcon.sizeof(), self.modulus, )


def AlignedStruct(modulus, *subcons, **kw):
    r"""
    Makes a structure where each field is aligned to the same modulus (it is a struct of aligned fields, NOT an aligned struct).

    See :class:`~construct.core.Aligned` and :class:`~construct.core.Struct` for semantics and raisable exceptions.

    :param modulus: integer or context lambda, passed to each member
    :param \*subcons: Construct instances, list of members, some can be anonymous
    :param \*\*kw: Construct instances, list of members (requires Python 3.6)

    Example::

        >>> d = AlignedStruct(4, "a"/Int8ub, "b"/Int16ub)
        >>> d.build(dict(a=1,b=5))
        b'\x01\x00\x00\x00\x00\x05\x00\x00'
        >>> d.parse(_)
        Container(a=1)(b=5)
        >>> d.sizeof()
        8
    """
    subcons = list(subcons) + list(k/v for k,v in kw.items())
    return Struct(*[Aligned(modulus, sc) for sc in subcons])


def BitStruct(*subcons, **kw):
    r"""
    Makes a structure inside a Bitwise.

    See :class:`~construct.core.Bitwise` and :class:`~construct.core.Struct` for semantics and raisable exceptions.

    :param \*subcons: Construct instances, list of members, some can be anonymous
    :param \*\*kw: Construct instances, list of members (requires Python 3.6)

    Example::

        BitStruct  <-->  Bitwise(Struct(...))

        >>> d = BitStruct(
        ...     "a" / Flag,
        ...     "b" / Nibble,
        ...     "c" / BitsInteger(10),
        ...     "d" / Padding(1),
        ... )
        >>> d.parse(b"\xbe\xef")
        Container(a=True)(b=7)(c=887)(d=None)
        >>> d.sizeof()
        2
    """
    return Bitwise(Struct(*subcons, **kw))


EmbeddedBitStruct = NotImplementedError


# def EmbeddedBitStruct(*subcons, **kw):
#     r"""
#     Makes an embedded BitStruct.

#     See :class:`~construct.core.Bitwise` and :class:`~construct.core.Embedded` and :class:`~construct.core.Struct` for semantics and raisable exceptions.

#     :param \*subcons: Construct instances, list of members, some can be anonymous
#     :param \*\*kw: Construct instances, list of members (requires Python 3.6)

#     Example::

#         EmbeddedBitStruct  <-->  Embedded(Bitwise(Struct(...)))
#     """
#     return Embedded(Bitwise(Struct(*subcons, **kw)))


#===============================================================================
# stream manipulation
#===============================================================================
class Pointer(Subconstruct):
    r"""
    Jumps in the stream forth and back for one field.

    Parsing and building seeks the stream to new location, processes subcon, and seeks back to original location. Size is not defined.

    Offset can be positive, indicating a position from stream beginning forward, or negative, indicating a position from EOF backwards.

    :param offset: integer or context lambda, positive or negative
    :param subcon: Construct instance

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises StreamError: stream is not seekable and tellable

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Pointer(8, Bytes(1))
        >>> d.parse(b"abcdefghijkl")
        b'i'
        >>> d.build(b"Z")
        b'\x00\x00\x00\x00\x00\x00\x00\x00Z'
    """
    __slots__ = ["offset"]

    def __init__(self, offset, subcon):
        super(Pointer, self).__init__(subcon)
        self.offset = offset

    def _parse(self, stream, context, path):
        offset = self.offset(context) if callable(self.offset) else self.offset
        fallback = _tell_stream(stream)
        _seek_stream(stream, offset, 2 if offset < 0 else 0)
        obj = self.subcon._parse(stream, context, path)
        _seek_stream(stream, fallback)
        return obj

    def _build(self, obj, stream, context, path):
        offset = self.offset(context) if callable(self.offset) else self.offset
        fallback = _tell_stream(stream)
        _seek_stream(stream, offset, 2 if offset < 0 else 0)
        buildret = self.subcon._build(obj, stream, context, path)
        _seek_stream(stream, fallback)
        return buildret

    def _sizeof(self, context, path):
        raise SizeofError


class Peek(Subconstruct):
    r"""
    Peeks at the stream.

    Parsing sub-parses (and returns None if failed), then reverts stream to original position. Building does nothing (its NOT deferred). Size is defined as 0 because there is no building.
    
    This class is used in :class:`~construct.core.Union` class to parse each member.

    :param subcon: Construct instance

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises StreamError: stream is not seekable and tellable

    Example::

        >>> d = Sequence(Peek(Int8ub), Peek(Int16ub))
        >>> d.parse(b"\x01\x02")
        [1, 258]
        >>> d.sizeof()
        0
    """

    def __init__(self, subcon):
        super(Peek, self).__init__(subcon)
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        fallback = _tell_stream(stream)
        try:
            return self.subcon._parse(stream, context, path)
        except ExplicitError:
            raise
        except ConstructError:
            pass
        finally:
            _seek_stream(stream, fallback)

    def _build(self, obj, stream, context, path):
        pass

    def _sizeof(self, context, path):
        return 0


class Seek(Construct):
    r"""
    Seeks the stream.

    Parsing and building seek the stream to given location (and whence), and return stream.seek() return value. Size is not defined.

    .. seealso:: Analog :class:`~construct.core.Pointer` wrapper that has same side effect but also processes a subcon, and also seeks back.

    :param at: integer or context lambda, where to jump to
    :param whence: optional, integer or context lambda, is the offset from beginning (0) or from current position (1) or from EOF (2), default is 0

    :raises StreamError: stream is not seekable

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = (Seek(5) >> Byte)
        >>> d.parse(b"01234x")
        [5, 120]

        >>> d = (Bytes(10) >> Seek(5) >> Byte)
        >>> d.build([b"0123456789", None, 255])
        b'01234\xff6789'
    """
    __slots__ = ["at", "whence"]

    def __init__(self, at, whence=0):
        super(Seek, self).__init__()
        self.at = at
        self.whence = whence
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        at = self.at(context) if callable(self.at) else self.at
        whence = self.whence(context) if callable(self.whence) else self.whence
        return _seek_stream(stream, at, whence)

    def _build(self, obj, stream, context, path):
        at = self.at(context) if callable(self.at) else self.at
        whence = self.whence(context) if callable(self.whence) else self.whence
        return _seek_stream(stream, at, whence)

    def _sizeof(self, context, path):
        raise SizeofError("Seek only moves the stream, size is not meaningful")

    def _emitparse(self, code):
        return "io.seek(%s, %s)" % (self.at, self.whence, )


@singleton
class Tell(Construct):
    r"""
    Tells the stream.

    Parsing and building return current stream offset using using stream.tell(). Size is defined as 0 because parsing and building does not consume or add into the stream.

    Tell is useful for adjusting relative offsets to absolute positions, or to measure sizes of Constructs. To get an absolute pointer, use a Tell plus a relative offset. To get a size, place two Tells and measure their difference using a Compute field. However, its recommended to use :class:`~construct.core.RawCopy` instead of manually extracting two positions and computing difference.

    :raises StreamError: stream is not tellable

    Example::

        >>> d = Struct("num"/VarInt, "offset"/Tell)
        >>> d.parse(b"X")
        Container(num=88)(offset=1)
        >>> d.build(dict(num=88))
        b'X'
    """

    def __init__(self):
        super(self.__class__, self).__init__()
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        return _tell_stream(stream)

    def _build(self, obj, stream, context, path):
        return _tell_stream(stream)

    def _sizeof(self, context, path):
        return 0

    def _emitparse(self, code):
        return "io.tell()"


@singleton
class Pass(Construct):
    r"""
    No-op construct, useful as default cases for Switch and Enum.

    Parsing returns None. Building does nothing. Size is 0 by definition.

    Example::

        >>> Pass.parse(b"")
        None
        >>> Pass.build(None)
        b''
        >>> Pass.sizeof()
        0
    """

    def __init__(self):
        super(self.__class__, self).__init__()
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        return None

    def _build(self, obj, stream, context, path):
        pass

    def _sizeof(self, context, path):
        return 0

    def _emitdecompiled(self, code):
        return "Pass"

    def _emitparse(self, code):
        return "None"


@singleton
class Terminated(Construct):
    r"""
    Asserts end of stream (EOF). You can use it to ensure no more unparsed data follows in the stream.

    Parsing checks if stream reached EOF, and raises TerminatedError if not. Building does nothing. Size is defined as 0 because parsing and building does not consume or add into the stream.

    :raises TerminatedError: stream not at EOF when parsing

    Example::

        >>> Terminated.parse(b"")
        None
        >>> Terminated.parse(b"remaining")
        construct.core.TerminatedError: expected end of stream
    """

    def __init__(self):
        super(self.__class__, self).__init__()
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        try:
            if stream.read(1):
                raise TerminatedError("expected end of stream")
        except IOError:
            # Restreamed.read(1) does not return empty string like BytesIO
            pass

    def _build(self, obj, stream, context, path):
        pass

    def _sizeof(self, context, path):
        return 0

    def _emitdecompiled(self, code):
        return "Terminated"


class Restreamed(Subconstruct):
    r"""
    Transforms bytes between the underlying stream and the subcon.

    Used internally to implement :class:`~construct.core.Bitwise` :class:`~construct.core.Bytewise` :class:`~construct.core.ByteSwapped` :class:`~construct.core.BitsSwapped` .

    .. warning:: Remember that subcon must consume or produce an amount of bytes that is a multiple of encoding or decoding units. For example, in a Bitwise context you should process a multiple of 8 bits or the stream will fail during parsing/building.

    .. warning:: Do NOT use seeking/telling classes inside Restreamed context.

    :param subcon: Construct instance, subcon which will operate on the buffer
    :param encoder: function that takes bytes and returns bytes (used when building)
    :param encoderunit: integer ratio, encoder takes that many bytes at once
    :param decoder: function that takes bytes and returns bytes (used when parsing)
    :param decoderunit: integer ratio, decoder takes that many bytes at once
    :param sizecomputer: function that computes amount of bytes outputed

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Can also raise arbitrary exceptions in its implementation.

    Example::

        Bitwise  <--> Restreamed(subcon, bits2bytes, 8, bytes2bits, 1, lambda n: n//8)
        Bytewise <--> Restreamed(subcon, bytes2bits, 1, bits2bytes, 8, lambda n: n*8)
    """
    __slots__ = ["decoder", "decoderunit", "encoder", "encoderunit", "sizecomputer"]

    def __init__(self, subcon, decoder, decoderunit, encoder, encoderunit, sizecomputer):
        super(Restreamed, self).__init__(subcon)
        self.decoder = decoder
        self.decoderunit = decoderunit
        self.encoder = encoder
        self.encoderunit = encoderunit
        self.sizecomputer = sizecomputer

    def _parse(self, stream, context, path):
        stream2 = RestreamedBytesIO(stream, self.decoder, self.decoderunit, self.encoder, self.encoderunit)
        obj = self.subcon._parse(stream2, context, path)
        stream2.close()
        return obj

    def _build(self, obj, stream, context, path):
        stream2 = RestreamedBytesIO(stream, self.decoder, self.decoderunit, self.encoder, self.encoderunit)
        buildret = self.subcon._build(obj, stream2, context, path)
        stream2.close()
        return buildret

    def _sizeof(self, context, path):
        if self.sizecomputer is None:
            raise SizeofError("Restreamed cannot calculate size without a sizecomputer")
        else:
            return self.sizecomputer(self.subcon._sizeof(context, path))


class Rebuffered(Subconstruct):
    r"""
    Caches bytes from underlying stream, so it becomes seekable and tellable, and also becomes blocking on reading. Useful for processing non-file streams like pipes, sockets, etc.

    .. warning:: Experimental implementation. May not be mature enough.

    :param subcon: Construct instance, subcon which will operate on the buffered stream
    :param tailcutoff: optional, integer, amount of bytes kept in buffer, by default buffers everything

    Can also raise arbitrary exceptions in its implementation.

    Example::

        Rebuffered(..., tailcutoff=1024).parse_stream(nonseekable_stream)
    """
    __slots__ = ["stream2", "tailcutoff"]

    def __init__(self, subcon, tailcutoff=None):
        super(Rebuffered, self).__init__(subcon)
        self.stream2 = RebufferedBytesIO(None, tailcutoff=tailcutoff)

    def _parse(self, stream, context, path):
        self.stream2.substream = stream
        return self.subcon._parse(self.stream2, context, path)

    def _build(self, obj, stream, context, path):
        self.stream2.substream = stream
        return self.subcon._build(obj, self.stream2, context, path)


#===============================================================================
# tunneling and byte/bit swapping
#===============================================================================
class RawCopy(Subconstruct):
    r"""
    Used to obtain byte representation of a field (aside of object value).

    Returns a dict containing both parsed subcon value, the raw bytes that were consumed by subcon, starting and ending offset in the stream, and amount in bytes. Builds either from raw bytes representation or a value used by subcon. Size is same as subcon.

    Object is a dictionary with either "data" or "value" keys, or both.

    :param subcon: Construct instance

    :raises StreamError: stream is not seekable and tellable
    :raises RawCopyError: building and neither data or value was given

    Example::

        >>> d = RawCopy(Byte)
        >>> d.parse(b"\xff")
        Container(data=b'\xff')(value=255)(offset1=0)(offset2=1)(length=1)
        >>> d.build(dict(data=b"\xff"))
        '\xff'
        >>> d.build(dict(value=255))
        '\xff'
    """

    def _parse(self, stream, context, path):
        offset1 = _tell_stream(stream)
        obj = self.subcon._parse(stream, context, path)
        offset2 = _tell_stream(stream)
        _seek_stream(stream, offset1)
        data = _read_stream(stream, offset2-offset1)
        return Container(data=data, value=obj, offset1=offset1, offset2=offset2, length=(offset2-offset1))

    def _build(self, obj, stream, context, path):
        if 'data' in obj:
            data = obj['data']
            offset1 = _tell_stream(stream)
            _write_stream(stream, len(data), data)
            offset2 = _tell_stream(stream)
            return Container(obj, data=data, offset1=offset1, offset2=offset2, length=len(data))
        if 'value' in obj:
            value = obj['value']
            offset1 = _tell_stream(stream)
            ret = self.subcon._build(value, stream, context, path)
            value = value if ret is None else ret
            offset2 = _tell_stream(stream)
            _seek_stream(stream, offset1)
            data = _read_stream(stream, offset2-offset1)
            return Container(obj, data=data, value=value, offset1=offset1, offset2=offset2, length=(offset2-offset1))
        raise RawCopyError('RawCopy cannot build, both data and value keys are missing')

    def _emitdecompiled(self, code):
        return "RawCopy(%s)" % (self.subcon._decompile(code), )


def ByteSwapped(subcon):
    r"""
    Swap the byte order within boundaries of given subcon. Requires a fixed sized subcon.

    :param subcon: Construct instance, subcon on top of byte swapped bytes

    :raises SizeofError: ctor or compiler could not compute subcon size

    See :class:`~construct.core.Restreamed` for raisable exceptions.

    Example::

        Int24ul <--> ByteSwapped(Int24ub) <--> BytesInteger(3, swapped=True)
    """
    macro = Restreamed(subcon,
        lambda s: s[::-1], subcon.sizeof(),
        lambda s: s[::-1], subcon.sizeof(),
        lambda n: n)
    def _emitparse(self, code):
        return "restream(read_bytes(io, %s)[::-1], lambda io: %s)" % (subcon.sizeof(), subcon._compileparse(code), )
    return CompilableMacro(macro, _emitparse)


def BitsSwapped(subcon):
    r"""
    Swap the bit order within each byte within boundaries of given subcon. Does NOT require a fixed sized subcon.

    :param subcon: Construct instance, subcon on top of bit swapped bytes

    :raises SizeofError: compiler could not compute subcon size

    See :class:`~construct.core.Restreamed` for raisable exceptions.

    Example::

        >>> d = Bitwise(Bytes(8))
        >>> d.parse(b"\x01")
        '\x00\x00\x00\x00\x00\x00\x00\x01'
        >>>> BitsSwapped(d).parse(b"\x01")
        '\x01\x00\x00\x00\x00\x00\x00\x00'
    """
    macro = Restreamed(subcon,
        lambda s: swapbits(s), 1,
        lambda s: swapbits(s), 1,
        lambda n: n)
    def _emitparse(self, code):
        return "restream(swapbits(read_bytes(io, %s)), lambda io: %s)" % (subcon.sizeof(), subcon._compileparse(code), )
    return CompilableMacro(macro, _emitparse)


class Prefixed(Subconstruct):
    r"""
    Prefixes a field with byte count.

    Parses the length field. Then reads that amount of bytes, and parses subcon using only those bytes. Constructs that consume entire remaining stream are constrained to consuming only the specified amount of bytes (a substream). When building, data gets prefixed by its length. Optionally, length field can include its own size. Size is the sum of both fields sizes, unless either raises SizeofError.

    Analog to :class:`~construct.core.PrefixedArray` which prefixes with an element count, instead of byte count. Semantics is similar but implementation is different.

    .. seealso:: :class:`~construct.core.VarInt` is recommended for new protocols, as its more compact and never overflows.

    :param lengthfield: Construct instance, field used for storing the length
    :param subcon: Construct instance, subcon used for storing the value
    :param includelength: optional, bool, whether length field should include its own size, default is False

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises NotImplementedError: compiled with includelength on

    Example::

        >>> Prefixed(VarInt, GreedyRange(Int32ul)).parse(b"\x08abcdefgh")
        [1684234849, 1751606885]

        >>> PrefixedArray(VarInt, Int32ul).parse(b"\x02abcdefgh")
        [1684234849, 1751606885]
    """
    __slots__ = ["name", "lengthfield", "subcon", "includelength"]

    def __init__(self, lengthfield, subcon, includelength=False):
        super(Prefixed, self).__init__(subcon)
        self.lengthfield = lengthfield
        self.includelength = includelength

    def _parse(self, stream, context, path):
        length = self.lengthfield._parse(stream, context, path)
        if self.includelength:
            length -= self.lengthfield._sizeof(context, path)
        stream2 = io.BytesIO(_read_stream(stream, length))
        return self.subcon._parse(stream2, context, path)

    def _build(self, obj, stream, context, path):
        stream2 = io.BytesIO()
        obj = self.subcon._build(obj, stream2, context, path)
        data = stream2.getvalue()
        length = len(data)
        if self.includelength:
            length += self.lengthfield._sizeof(context, path)
        self.lengthfield._build(length, stream, context, path)
        _write_stream(stream, len(data), data)
        return obj

    def _sizeof(self, context, path):
        return self.lengthfield._sizeof(context, path) + self.subcon._sizeof(context, path)

    def _emitparse(self, code):
        if self.includelength:
            raise NotImplementedError("Prefixed does not compile with includelength")
        return "restream(read_bytes(io, %s), lambda io: %s)" % (self.lengthfield._compileparse(code), self.subcon._compileparse(code), )


def PrefixedArray(lengthfield, subcon):
    r"""
    Prefixes an array with item count (as opposed to prefixed by byte count, see :class:`~construct.core.Prefixed`).

    :param lengthfield: Construct instance, field used for storing the element count
    :param subcon: Construct instance, subcon used for storing each element

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises RangeError: consumed or produced too little elements

    Example::

        >>> Prefixed(VarInt, GreedyRange(Int32ul)).parse(b"\x08abcdefgh")
        [1684234849, 1751606885]

        >>> PrefixedArray(VarInt, Int32ul).parse(b"\x02abcdefgh")
        [1684234849, 1751606885]
    """
    macro = FocusedSeq(1,
        "count" / Rebuild(lengthfield, len_(this.items)),
        "items" / subcon[this.count],
    )
    def _emitparse(self, code):
        return "ListContainer((%s) for i in range(%s))" % (subcon._compileparse(code), lengthfield._compileparse(code), )
    return CompilableMacro(macro, _emitparse)


class RestreamData(Subconstruct):
    """
    Parses a field on external data.

    Parsing defers to subcon, but provides it a separate stream based on bytes data provided by datafunc (a bytes literal or context lambda). Building and sizeof are deferred to subcon.

    :param datafunc: bytes or context lambda, provides data for subcon to parse
    :param subcon: Construct instance, subcon used for storing the value

    Can propagate any exception from the lambdas, possibly non-ConstructError.

    Example::

        >>> RestreamData(b"\xff", Byte).parse(b"")
        255
    """
    __slots__ = ["datafunc"]
    def __init__(self, datafunc, subcon):
        super(RestreamData, self).__init__(subcon)
        self.datafunc = datafunc

    def _parse(self, stream, context, path):
        data = self.datafunc
        if callable(data):
            data = data(context)
        stream2 = io.BytesIO(data)
        return self.subcon._parse(stream2, context, path)

    def _emitparse(self, code):
        return "restream(%r, lambda io: %s)" % (self.datafunc, self.subcon._compileparse(code), )


class Checksum(Construct):
    r"""
    Field that is build or validated by a hash of a given byte range. Usually used with :class:`~construct.core.RawCopy` .

    semantics???

    :param checksumfield: a subcon field that reads the checksum, usually Bytes(int)
    :param hashfunc: function that takes bytes and returns whatever checksumfield takes when building, usually from hashlib module
    :param bytesfunc: context lambda that returns bytes (or object) to be hashed, usually like this.rawcopy1.data

    :raises ChecksumError: parsing and actual checksum does not match actual data

    Can propagate any exception from the lambdas, possibly non-ConstructError.

    Example::

        import hashlib
        d = Struct(
            "fields" / RawCopy(Struct(
                "a" / Byte,
                "b" / Byte,
            )),
            "checksum" / Checksum(Bytes(64), lambda data: hashlib.sha512(data).digest(), this.fields.data),
        )
        d.build(dict(fields=dict(value=dict(a=1,b=2))))
        -> b'\x01\x02\xbd\xd8\x1a\xb23\xbc\xebj\xd23\xcd'...
    """
    __slots__ = ["checksumfield", "hashfunc", "bytesfunc"]

    def __init__(self, checksumfield, hashfunc, bytesfunc):
        super(Checksum, self).__init__()
        self.checksumfield = checksumfield
        self.hashfunc = hashfunc
        self.bytesfunc = bytesfunc
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        hash1 = self.checksumfield._parse(stream, context, path)
        hash2 = self.hashfunc(self.bytesfunc(context))
        if hash1 != hash2:
            raise ChecksumError("wrong checksum, read %r, computed %r" % (
                hash1 if not isinstance(hash1,bytes) else binascii.hexlify(hash1),
                hash2 if not isinstance(hash2,bytes) else binascii.hexlify(hash2), ))
        return hash1

    def _build(self, obj, stream, context, path):
        hash2 = self.hashfunc(self.bytesfunc(context))
        self.checksumfield._build(hash2, stream, context, path)
        return hash2

    def _sizeof(self, context, path):
        return self.checksumfield._sizeof(context, path)


class Compressed(Tunnel):
    r"""
    Compresses and decompresses underlying stream when processing subcon. When parsing, entire stream is consumed. When building, puts compressed bytes without marking the end. This construct should be used with :class:`~construct.core.Prefixed` .

    :param subcon: Construct instance, subcon used for storing the value
    :param encoding: string, any of module names like zlib/gzip/bzip2/lzma, otherwise any of codecs module bytes<->bytes encodings, each codec usually requires some Python version
    :param level: optional, integer between 0..9, although lzma discards it, some encoders allow different compression levels

    :raises StreamError: stream failed when reading until EOF
    :raises ImportError: needed module could not be imported by ctor

    Example::

        >>> d = Prefixed(VarInt, Compressed(GreedyBytes, "zlib"))
        >>> d.build(bytes(100))
        b'\x0cx\x9cc`\xa0=\x00\x00\x00d\x00\x01'

   """
    __slots__ = ["encoding", "level", "lib"]

    def __init__(self, subcon, encoding, level=None):
        super(Compressed, self).__init__(subcon)
        self.encoding = encoding
        self.level = level
        if self.encoding == "zlib":
            import zlib
            self.lib = zlib
        elif self.encoding == "gzip":
            import gzip
            self.lib = gzip
        elif self.encoding == "bzip2":
            import bz2
            self.lib = bz2
        elif self.encoding == "lzma":
            import lzma
            self.lib = lzma
        else:
            import codecs
            self.lib = codecs

    def _decode(self, data, context):
        if self.encoding in ("zlib", "gzip", "bzip2", "lzma"):
            return self.lib.decompress(data)
        return self.lib.decode(data, self.encoding)

    def _encode(self, data, context):
        if self.encoding in ("zlib", "gzip", "bzip2", "lzma"):
            if self.level is None or self.encoding == "lzma":
                return self.lib.compress(data)
            else:
                return self.lib.compress(data, self.level)
        return self.lib.encode(data, self.encoding)


#===============================================================================
# lazy equivalents
#===============================================================================
class LazyStruct(Construct):
    r"""
    Equivalent to :class:`~construct.core.Struct` regarding semantics, however fixed size members are parsed on demand, others are parsed immediately.

    .. note:: For performance, if entire struct is fixed size then entire parsing is only one stream seek.

    .. warning:: Members that depend on earlier (named) context entries do not work properly, because since this class is lazy, there is no guarantee that previous members were parsed and put into context dictionary.

    :raises StreamError: stream is not seekable and tellable
    """
    __slots__ = ["subcons", "offsetmap", "totalsize", "subsizes", "keys"]
    def __init__(self, *subcons, **kw):
        super(LazyStruct, self).__init__()
        self.subcons = list(subcons) + list(k/v for k,v in kw.items()) 

        try:
            keys = Container()
            self.offsetmap = {}
            at = 0
            for sc in self.subcons:
                if sc.flagembedded:
                    raise SizeofError
                if sc.name:
                    keys[sc.name] = None
                    self.offsetmap[sc.name] = (at, sc)
                at += sc.sizeof()
            self.totalsize = at
            self.keys = list(keys.keys())
        except SizeofError:
            self.offsetmap = None
            self.totalsize = None

        self.subsizes = []
        for sc in self.subcons:
            try:
                self.subsizes.append(sc.sizeof())
            except SizeofError:
                self.subsizes.append(None)

    def _parse(self, stream, context, path):
        if self.offsetmap is not None:
            position = _tell_stream(stream)
            _seek_stream(stream, self.totalsize, 1)
            return LazyContainer(self.keys, self.offsetmap, {}, stream, position, context)
        context = Container(_ = context)
        offsetmap = {}
        keys = Container()
        values = {}
        position = _tell_stream(stream)
        for (sc,size) in zip(self.subcons, self.subsizes):
            if sc.flagembedded:
                subobj = list(sc._parse(stream, context, path).items())
                keys.update(subobj)
                values.update(subobj)
                context.update(subobj)
            elif size is None:
                subobj = sc._parse(stream, context, path)
                if sc.name:
                    keys[sc.name] = None
                    values[sc.name] = subobj
                    context[sc.name] = subobj
            else:
                if sc.name:
                    keys[sc.name] = None
                    offsetmap[sc.name] = (_tell_stream(stream), sc)
                _seek_stream(stream, size, 1)
        return LazyContainer(list(keys.keys()), offsetmap, values, stream, 0, context)

    def _build(self, obj, stream, context, path):
        context = Container(_ = context)
        context.update(obj)
        for sc in self.subcons:
            if sc.flagembedded:
                subobj = obj
            elif sc.flagbuildnone:
                subobj = obj.get(sc.name, None)
            else:
                subobj = obj[sc.name]
            buildret = sc._build(subobj, stream, context, path)
            if buildret is not None:
                if sc.flagembedded:
                    context.update(buildret)
                if sc.name:
                    context[sc.name] = buildret
        return context

    def _sizeof(self, context, path):
        if self.totalsize is not None:
            return self.totalsize
        else:
            raise SizeofError("cannot calculate size, not all members are fixed size")


class LazySequence(Construct):
    r"""
    Equivalent to :class:`~construct.core.Sequence` regarding semantics, however fixed size members are parsed on demand, others are parsed immediately.

    .. note:: For performance, if entire sequence is fixed size then entire parsing is only one stream seek.

    .. warning:: Members that depend on earlier (named) context entries do not work properly, because since this class is lazy, there is no guarantee that previous members were parsed and put into context dictionary.

    :raises StreamError: stream is not seekable and tellable
    """
    __slots__ = ["subcons", "offsetmap", "totalsize", "subsizes"]
    def __init__(self, *subcons, **kw):
        super(LazySequence, self).__init__()
        self.subcons = list(subcons) + list(k/v for k,v in kw.items())

        try:
            self.offsetmap = {}
            at = 0
            for i,sc in enumerate(self.subcons):
                if sc.flagembedded:
                    raise SizeofError
                self.offsetmap[i] = (at, sc)
                at += sc.sizeof()
            self.totalsize = at
        except SizeofError:
            self.offsetmap = None
            self.totalsize = None

        self.subsizes = []
        for sc in self.subcons:
            try:
                self.subsizes.append(sc.sizeof())
            except SizeofError:
                self.subsizes.append(None)

    def _parse(self, stream, context, path):
        context = Container(_ = context)
        if self.totalsize is not None:
            position = _tell_stream(stream)
            _seek_stream(stream, self.totalsize, 1)
            return LazySequenceContainer(len(self.subcons), self.offsetmap, {}, stream, position, context)
        offsetmap = {}
        values = {}
        i = 0
        for sc,size in zip(self.subcons, self.subsizes):
            if sc.flagembedded:
                subobj = list(sc._parse(stream, context, path))
                for e in subobj:
                    values[i] = e
                    context[i] = e
                    i += 1
            elif size is None:
                obj = sc._parse(stream, context, path)
                values[i] = obj
                context[i] = obj
                i += 1
            else:
                offsetmap[i] = (_tell_stream(stream), sc)
                _seek_stream(stream, size, 1)
                i += 1
        return LazySequenceContainer(i, offsetmap, values, stream, 0, context)

    def _build(self, obj, stream, context, path):
        context = Container(_ = context)
        objiter = iter(obj)
        for i,sc in enumerate(self.subcons):
            if sc.flagembedded:
                subobj = objiter
            else:
                subobj = next(objiter)
                if sc.name:
                    context[sc.name] = subobj
            context[i] = subobj
            buildret = sc._build(subobj, stream, context, path)
            if buildret is not None:
                if sc.flagembedded:
                    context.update(buildret)
                if sc.name:
                    context[sc.name] = buildret
                context[i] = buildret

    def _sizeof(self, context, path):
        if self.totalsize is not None:
            return self.totalsize
        else:
            raise SizeofError("cannot calculate size, not all members are fixed size")


class LazyRange(Construct):
    r"""
    Equivalent to :class:`~construct.core.Range` regarding semantics, however fixed size members are parsed on demand, others are parsed immediately.

    .. note:: Works only with fixed size subcon. Performance wise, entire parse is essentially one stream seek.

    :raises StreamError: stream is not seekable and tellable
    """
    __slots__ = ["subcon", "min", "max", "subsize"]
    def __init__(self, min, max, subcon):
        super(LazyRange, self).__init__()
        self.subcon = subcon
        self.min = min
        self.max = max
        self.subsize = subcon.sizeof()

    def _parse(self, stream, context, path):
        currentmin = self.min(context) if callable(self.min) else self.min
        currentmax = self.max(context) if callable(self.max) else self.max
        if not 0 <= currentmin <= currentmax:
            raise RangeError("unsane min %s and max %s" % (currentmin, currentmax))
        starts = _tell_stream(stream)
        ends = _seek_stream(stream, 0, 2)
        remaining = ends - starts
        objcount = min(remaining//self.subsize, currentmax)
        if objcount < currentmin:
            raise RangeError("not enough bytes %d to read the min %d of %d bytes each" % (remaining, currentmin, self.subsize))
        _seek_stream(stream, starts + objcount*self.subsize, 0)
        return LazyRangeContainer(self.subcon, self.subsize, objcount, stream, starts, context)

    def _build(self, obj, stream, context, path):
        currentmin = self.min(context) if callable(self.min) else self.min
        currentmax = self.max(context) if callable(self.max) else self.max
        if not 0 <= currentmin <= currentmax:
            raise RangeError("unsane min %s and max %s" % (currentmin, currentmax))
        if not isinstance(obj, collections.Sequence):
            raise RangeError("expected sequence type, found %s" % type(obj))
        if not currentmin <= len(obj) <= currentmax:
            raise RangeError("expected from %d to %d elements, found %d" % (currentmin, currentmax, len(obj)))
        try:
            for i,subobj in enumerate(obj):
                context[i] = subobj
                self.subcon._build(subobj, stream, context, path)
        except ConstructError:
            if len(obj) < currentmin:
                raise RangeError("expected %d to %d, found %d" % (currentmin, currentmax, len(obj)))

    def _sizeof(self, context, path):
        try:
            currentmin = self.min(context) if callable(self.min) else self.min
            currentmax = self.max(context) if callable(self.max) else self.max
            if not 0 <= currentmin <= currentmax:
                raise RangeError("unsane min %s and max %s" % (currentmin, currentmax))
            if currentmin == currentmax:
                return self.min * self.subsize
            else:
                raise SizeofError("cannot calculate size, min not equal to max")
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")


class OnDemand(Subconstruct):
    r"""
    Allows for lazy parsing of one field.

    Parsing returns a parameterless lambda that when called, parses subcon at then-current stream offset and returns parsed value. Object is cached after first parsing, so non-deterministic subcons will be affected. Builds from both the parameterless lambda and subcon acceptable value. Size is same as subcon, unless it raises SizeofError.

    .. note:: Works only with fixed size subcon.

    :param subcon: Construct instance, must be fixed size

    :raises StreamError: stream is not seekable and tellable

    Example::

        >>> d = OnDemand(Byte)
        >>> d.parse(b"\xff")
        <function OnDemand._parse.<locals>.<lambda> at 0x7fdc241cfc80>
        >>> _()
        255
        >>> d.build(255)
        b'\xff'

        Can also re-build from the lambda returned at parsing.

        >>> d.parse(b"\xff")
        <function OnDemand._parse.<locals>.<lambda> at 0x7fcbd9855f28>
        >>> d.build(_)
        b'\xff'
    """

    def _parse(self, stream, context, path):
        offset = _tell_stream(stream)
        _seek_stream(stream, self.subcon._sizeof(context, path), 1)
        cache = {}
        def effectuate():
            if not cache:
                fallback = _tell_stream(stream)
                _seek_stream(stream, offset)
                obj = self.subcon._parse(stream, context, path)
                _seek_stream(stream, fallback)
                cache["value"] = obj
            return cache["value"]
        return effectuate

    def _build(self, obj, stream, context, path):
        obj = obj() if callable(obj) else obj
        return self.subcon._build(obj, stream, context, path)


class LazyBound(Construct):
    r"""
    Lazy-bound construct that binds to the construct only at runtime. Useful for recursive data structures (like linked-lists or trees), where a construct needs to refer to itself (while it does not exist yet).

    :param subconfunc: context lambda returning a Construct instance, can also return Pass or itself

    Example::

        >>> d = Struct(
        ...     "value"/Byte,
        ...     "next"/If(this.value > 0, LazyBound(lambda ctx: d)),
        ... )
        ...
        >>> d.parse(b"\x05\x09\x00")
        Container(value=5)(next=Container(value=9)(next=Container(value=0)(next=None)))
        ...
        >>> print(d.parse(b"\x05\x09\x00"))
        Container:
            value = 5
            next = Container:
                value = 9
                next = Container:
                    value = 0
                    next = None
    """
    __slots__ = ["subconfunc"]

    def __init__(self, subconfunc):
        super(LazyBound, self).__init__()
        self.subconfunc = subconfunc

    def _parse(self, stream, context, path):
        return self.subconfunc(context)._parse(stream, context, path)

    def _build(self, obj, stream, context, path):
        return self.subconfunc(context)._build(obj, stream, context, path)

    def _sizeof(self, context, path):
        try:
            return self.subconfunc(context)._sizeof(context, path)
        except (KeyError, AttributeError):
            raise SizeofError("cannot calculate size, key not found in context")


#===============================================================================
# adapters and validators
#===============================================================================
class ExprAdapter(Adapter):
    r"""
    A generic adapter that takes ``encoder`` and ``decoder`` as parameters. You can use ExprAdapter instead of writing a full-blown class when only a simple lambda is needed.

    :param subcon: Construct instance, subcon to adapt
    :param encoder: lambda that takes (obj, context) and returns an encoded version of obj, or None for identity function
    :param decoder: lambda that takes (obj, context) and returns an decoded version of obj, or None for identity function

    Example::

        # adds +1 to build values and subtracts -1 from parsed objects
        ExprAdapter(Byte,
            encoder = lambda x,ctx: x+1,
            decoder = lambda x,ctx: x-1 )
    """
    __slots__ = ["_decode","_encode"]
    def __init__(self, subcon, decoder, encoder):
        super(ExprAdapter, self).__init__(subcon)
        ident = lambda obj,ctx: obj
        self._decode = decoder if callable(decoder) else ident
        self._encode = encoder if callable(encoder) else ident


class ExprSymmetricAdapter(ExprAdapter):
    """
    Macro around :class:`~construct.core.ExprAdapter`.

    :param subcon: Construct instance, subcon to adapt
    :param encoder: lambda that takes (obj, context) and returns both encoded version and decoded version of obj, or None for identity function

    implement???

    Example::

        # unsets 4 out of 8 bits in parsed and build values
        ExprSymmetricAdapter(Byte, encoder = lambda x,ctx: x & 0b00001111)
    """
    def __init__(self, subcon, encoder):
        super(ExprAdapter, self).__init__(subcon)
        ident = lambda obj,ctx: obj
        self._decode = encoder if callable(encoder) else ident
        self._encode = encoder if callable(encoder) else ident


class ExprValidator(Validator):
    r"""
    A generic adapter that takes ``validator`` as parameter. You can use ExprValidator instead of writing a full-blown class when only a simple lambda is needed.

    :param subcon: Construct instance, subcon to adapt
    :param encoder: lambda that takes (obj, context) and returns a bool

    Example::

        ExprValidator(Byte, validator = lambda obj,ctx: obj in [1,3,5])
        OneOf(Byte, [1,3,5])
    """
    def __init__(self, subcon, validator):
        super(ExprValidator, self).__init__(subcon)
        self._validate = validator


def OneOf(subcon, valids):
    r"""
    Validates that the object is one of the listed values, both during parsing and building.

    .. note:: For performance, you should provide a set/frozenset but if items are not hashable, then a list would work the same, just slower.

    :param subcon: Construct instance, subcon to validate
    :param valids: collection implementing __contains__, usually a list or set

    :raises ValidationError: parsed or build value is not among valids

    Example::

        >>> d = OneOf(Byte, [1,2,3])
        >>> d.parse(b"\x01")
        1
        >>> d.parse(b"\xff")
        construct.core.ValidationError: object failed validation: 255
    """
    return ExprValidator(subcon, lambda obj,ctx: obj in valids)


def NoneOf(subcon, invalids):
    r"""
    Validates that the object is none of the listed values, both during parsing and building.

    .. note:: For performance, you should provide a set/frozenset but if items are not hashable, then a list would work the same, just slower.

    :param subcon: Construct instance, subcon to validate
    :param invalids: collection implementing __contains__, usually a list or set

    :raises ValidationError: parsed or build value is among invalids

    """
    return ExprValidator(subcon, lambda obj,ctx: obj not in invalids)


def Filter(predicate, subcon):
    r"""
    Filters a list leaving only the elements that passed through the predicate.

    :param subcon: Construct instance, usually a Range Array Sequence
    :param predicate: lambda that takes (obj, context) and returns a bool

    Can propagate any exception from the lambda, possibly non-ConstructError.

    Example::

        >>> d = Filter(obj_ != 0, Byte[:])
        >>> d.parse(b"\x00\x02\x00")
        [2]
        >>> d.build([0,1,0,2,0])
        b'\x01\x02'
    """
    return ExprSymmetricAdapter(subcon, lambda obj,ctx: [x for x in obj if predicate(x,ctx)])


class Slicing(Adapter):
    r"""
    Adapter for slicing a list. Works with Range and Sequence and their lazy equivalents.

    :param subcon: Construct instance, subcon to slice
    :param count: integer, expected number of elements, needed during building
    :param start: integer for start index (or None for entire list)
    :param stop: integer for stop index (or None for up-to-end)
    :param step: integer, step (or 1 for every element)
    :param empty: object, value to fill the list with, during building

    Example::

        example???
    """
    __slots__ = ["count", "start", "stop", "step", "empty"]
    def __init__(self, subcon, count, start, stop, step=1, empty=None):
        super(Slicing, self).__init__(subcon)
        self.count = count
        self.start = start
        self.stop = stop
        self.step = step
        self.empty = empty
    def _decode(self, obj, context):
        return obj[self.start:self.stop:self.step]
    def _encode(self, obj, context):
        if self.start is None:
            return obj
        elif self.stop is None:
            output = [self.empty] * self.count
            output[self.start::self.step] = obj
        else:
            output = [self.empty] * self.count
            output[self.start:self.stop:self.step] = obj
        return output


class Indexing(Adapter):
    r"""
    Adapter for indexing a list (getting a single item from that list). Works with Range and Sequence and their lazy equivalents.

    :param subcon: Construct instance, subcon to index
    :param count: integer, expected number of elements, needed during building
    :param index: integer, index of the list to get
    :param empty: object, value to fill the list with, during building

    Example::

        example???
    """
    __slots__ = ["count", "index", "empty"]
    def __init__(self, subcon, count, index, empty=None):
        super(Indexing, self).__init__(subcon)
        self.count = count
        self.index = index
        self.empty = empty
    def _decode(self, obj, context):
        return obj[self.index]
    def _encode(self, obj, context):
        output = [self.empty] * self.count
        output[self.index] = obj
        return output


def Hex(subcon):
    r"""
    Adapter for (un)hexlifying bytes.

    Example::

        >>> d = Hex(GreedyBytes)
        >>> d.parse(b"abcd")
        b'61626364'
        >>> d.build("01020304")
        b'\x01\x02\x03\x04'
    """
    return ExprAdapter(subcon,
        decoder = lambda obj,ctx: None if obj is None else binascii.hexlify(obj),
        encoder = lambda obj,ctx: None if subcon.flagbuildnone else binascii.unhexlify(obj),
    )


def HexDump(subcon, linesize=16):
    r"""
    Adapter for (un)hexdumping bytes. A hex-dump is a string with X bytes per newline, each line shows both offset, ascii representation, and hexadecimal representation.

    :param linesize: optional, integer, default is 16 bytes per line

    Example::

        >>> d = HexDump(Bytes(10))
        >>> d.parse(b"12345abc;/")
        '0000   31 32 33 34 35 61 62 63 3b 2f                     12345abc;/       \n'
    """
    return ExprAdapter(subcon,
        decoder = lambda obj,ctx: None if obj is None else hexdump(obj, linesize=linesize),
        encoder = lambda obj,ctx: None if subcon.flagbuildnone else hexundump(obj, linesize=linesize),
    )


#===============================================================================
# end of file
#===============================================================================
