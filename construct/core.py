from struct import Struct as Packer
from struct import error as PackerError
from io import BytesIO, StringIO
import sys
import collections

# from construct.macros import UBInt8
from construct.lib.py3compat import int2byte, unknownstring2bytes, stringtypes
from construct.lib import Container, ListContainer, LazyContainer


#===============================================================================
# exceptions
#===============================================================================
class ConstructError(Exception):
    pass
class FieldError(ConstructError):
    pass
class SizeofError(ConstructError):
    pass
class AdaptationError(ConstructError):
    pass
class ArrayError(ConstructError):
    pass
class RangeError(ConstructError):
    pass
class SwitchError(ConstructError):
    pass
class SelectError(ConstructError):
    pass
class TerminatorError(ConstructError):
    pass
class OverwriteError(ValueError):
    pass
class PaddingError(ConstructError):
    pass
class ConstError(ConstructError):
    pass
class StringError(ConstructError):
    pass
class ChecksumError(ConstructError):
    pass



#===============================================================================
# abstract constructs
#===============================================================================
class Construct(object):
    """
    The mother of all constructs.

    This object is generally not directly instantiated, and it does not directly implement parsing and building, so it is largely only of interest to subclass implementors.

    The external user API:

     * ``parse()``
     * ``parse_stream()``
     * ``build()``
     * ``build_stream()``
     * ``sizeof()``

    Subclass authors should not override the external methods. Instead, another API is available:

     * ``_parse()``
     * ``_build()``
     * ``_sizeof()``

    There is also a flag API:

     * ``_set_flag()``
     * ``_clear_flag()``
     * ``_inherit_flags()``
     * ``_is_flag()``

    And stateful copying:

     * ``__getstate__()``
     * ``__setstate__()``

    Attributes and Inheritance
    ==========================

    All constructs have a name and flags. The name is used for naming struct members and context dictionaries. Note that the name can either be a string, or None if the name is not needed. A single underscore ("_") is a reserved name, and so are names starting with a less-than character ("<"). The name should be descriptive, short, and valid as a Python identifier, although these rules are not enforced.

    The flags specify additional behavioral information about this construct. Flags are used by enclosing constructs to determine a proper course of action. Flags are inherited by default, from inner subconstructs to outer constructs. The enclosing construct may set new flags or clear existing ones, as necessary.

    For example, if ``FLAG_COPY_CONTEXT`` is set, repeaters will pass a copy of the context for each iteration, which is necessary for OnDemand parsing.
    """

    FLAG_COPY_CONTEXT          = 0x0001
    FLAG_DYNAMIC               = 0x0002
    FLAG_EMBED                 = 0x0004
    FLAG_NESTING               = 0x0008

    __slots__ = ["name", "conflags"]
    def __init__(self, name, flags=0):
        if name is not None:
            if not isinstance(name, stringtypes):
                raise TypeError("name must be some sort of string or None", name)
            # NOTE: this tests the name that can be a byte string or unicode string
            # and only the unicode has startswith method
            bname = unknownstring2bytes(name)
            if bname == b"_" or bname[:1] ==b"<":
                raise ValueError("reserved name: either _ or starts with < ", name)
        self.name = name
        self.conflags = flags

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.name)

    def _set_flag(self, flag):
        """
        Set the given flag or flags.

        :param int flag: flag to set; may be OR'd combination of flags
        """
        self.conflags |= flag

    def _clear_flag(self, flag):
        """
        Clear the given flag or flags.

        :param int flag: flag to clear; may be OR'd combination of flags
        """
        self.conflags &= ~flag

    def _inherit_flags(self, *subcons):
        """
        Pull flags from subconstructs.
        """
        for sc in subcons:
            self._set_flag(sc.conflags)

    def _is_flag(self, flag):
        """
        Check whether a given flag is set.

        :param int flag: flag to check
        """
        return bool(self.conflags & flag)

    def __getstate__(self):
        """
        Obtain a dictionary representing this construct's state.
        """
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
        """
        Set this construct's state to a given state.
        """
        for name, value in attrs.items():
            setattr(self, name, value)

    def __copy__(self):
        """
        Returns a copy of this construct.
        """
        self2 = object.__new__(self.__class__)
        self2.__setstate__(self, self.__getstate__())
        return self2

    def parse(self, data):
        """
        Parse an in-memory buffer.

        Strings, buffers, memoryviews, and other complete buffers can be parsed with this method.
        """
        return self.parse_stream(BytesIO(data))

    def parse_stream(self, stream):
        """
        Parse a stream.

        Files, pipes, sockets, and other streaming sources of data are handled by this method.
        """
        return self._parse(stream, Container())

    def _parse(self, stream, context):
        """
        Override in your subclass.
        """
        raise NotImplementedError()

    def build(self, obj):
        """
        Build an object in memory.

        :returns: bytes
        """
        stream = BytesIO()
        self.build_stream(obj, stream)
        return stream.getvalue()

    def build_stream(self, obj, stream):
        """
        Build an object directly into a stream.

        :returns: None
        """
        self._build(obj, stream, Container())

    def _build(self, obj, stream, context):
        """
        Override in your subclass.
        """
        raise NotImplementedError()

    def sizeof(self, context=None):
        """
        Calculate the size of this object, optionally using a context.

        Some constructs have no fixed size and can only know their size for a given hunk of data. These constructs will raise an error if they are not passed a context.

        :param context: a container

        :returns: int of the length of this construct
        :raises SizeofError: the size could not be determined
        """
        if context is None:
            context = Container()
        return self._sizeof(context)

    def _sizeof(self, context):
        """
        Override in your subclass.
        """
        raise SizeofError("Constructs cannot compute size by default. ")


class Subconstruct(Construct):
    """
    Abstract subconstruct (wraps an inner construct, inheriting its name and flags).

    Subconstructs wrap an inner Construct, inheriting its name and flags.

    :param subcon: the construct to wrap
    """
    __slots__ = ["subcon"]
    def __init__(self, subcon):
        super(Subconstruct, self).__init__(subcon.name, subcon.conflags)
        self.subcon = subcon
    def _parse(self, stream, context):
        return self.subcon._parse(stream, context)
    def _build(self, obj, stream, context):
        self.subcon._build(obj, stream, context)
    def _sizeof(self, context):
        return self.subcon._sizeof(context)


class Adapter(Subconstruct):
    """
    Abstract adapter parent class.

    Adapters should implement ``_decode()`` and ``_encode()``.

    :param subcon: the construct to wrap
    """
    __slots__ = []
    def _parse(self, stream, context):
        return self._decode(self.subcon._parse(stream, context), context)
    def _build(self, obj, stream, context):
        self.subcon._build(self._encode(obj, context), stream, context)
    def _decode(self, obj, context):
        raise NotImplementedError()
    def _encode(self, obj, context):
        raise NotImplementedError()



#===============================================================================
# Helper methods
#===============================================================================

def _read_stream(stream, length):
    if length < 0:
        raise ValueError("length must be >= 0", length)
    data = stream.read(length)
    if len(data) != length:
        raise FieldError("could not read enough bytes, expected %d, found %d" % (length, len(data)))
    return data

def _write_stream(stream, length, data):
    if length < 0:
        raise ValueError("length must be >= 0", length)
    if len(data) != length:
        raise FieldError("could not write bytes, expected %d, found %d" % (length, len(data)))
    stream.write(data)



#===============================================================================
# Fields
#===============================================================================

class StaticField(Construct):
    """
    A fixed-size byte field.

    :param name: field name
    :param length: number of bytes in the field
    """
    __slots__ = ["length"]
    def __init__(self, name, length):
        super(StaticField, self).__init__(name)
        self.length = length
    def _parse(self, stream, context):
        return _read_stream(stream, self.length)
    def _build(self, obj, stream, context):
        _write_stream(stream, self.length, int2byte(obj) if isinstance(obj, int) else obj)
    def _sizeof(self, context):
        return self.length


class FormatField(StaticField):
    """
    A field that uses ``struct`` to pack and unpack data.

    See ``struct`` documentation for instructions on crafting format strings.

    :param name: name of the field
    :param endianness: format endianness string; one of "<", ">", or "="
    :param format: a single format character
    """
    __slots__ = ["packer"]
    def __init__(self, name, endianity, format):
        if endianity not in (">", "<", "="):
            raise ValueError("endianity must be be '=', '<', or '>'",
                endianity)
        if len(format) != 1:
            raise ValueError("must specify one and only one format char")
        self.packer = Packer(endianity + format)
        super(FormatField, self).__init__(name, self.packer.size)
    def __getstate__(self):
        attrs = super(FormatField, self).__getstate__()
        attrs["packer"] = attrs["packer"].format
        return attrs
    def __setstate__(self, attrs):
        attrs["packer"] = Packer(attrs["packer"])
        return super(FormatField, self).__setstate__(attrs)
    def _parse(self, stream, context):
        try:
            return self.packer.unpack(_read_stream(stream, self.length))[0]
        except Exception:
            raise FieldError("packer %r error during parsing" % self.packer.format)
    def _build(self, obj, stream, context):
        try:
            _write_stream(stream, self.length, self.packer.pack(obj))
        except Exception:
            raise FieldError("packer %r error during building, given value %s" % (self.packer.format, obj))


class MetaField(Construct):
    r"""
    A variable-length field. The length is obtained at runtime from a function.

    :param name: name of the field
    :param lengthfunc: callable that takes a context and returns length as an int

    Example::

        >>> foo = Struct("foo",
        ...     Byte("length"),
        ...     MetaField("data", lambda ctx: ctx["length"])
        ... )
        >>> foo.parse("\x03ABC")
        Container(data = 'ABC', length = 3)
        >>> foo.parse("\x04ABCD")
        Container(data = 'ABCD', length = 4)
    """
    __slots__ = ["lengthfunc"]
    def __init__(self, name, lengthfunc):
        super(MetaField, self).__init__(name)
        self.lengthfunc = lengthfunc
        self._set_flag(self.FLAG_DYNAMIC)
    def _parse(self, stream, context):
        return _read_stream(stream, self.lengthfunc(context))
    def _build(self, obj, stream, context):
        _write_stream(stream, self.lengthfunc(context), obj)
    def _sizeof(self, context):
        return self.lengthfunc(context)



#===============================================================================
# arrays and repeaters
#===============================================================================
class MetaArray(Subconstruct):
    """
    An array (repeater) of a meta-count. The array will iterate exactly ``countfunc()`` times. Will raise ArrayError if less elements are found.

    .. seealso::

        The :func:`~construct.macros.Array` macro, :func:`Range` and :func:`RepeatUntil`.

    :param countfunc: a function that takes the context as a parameter and returns the number of elements of the array (count)
    :param subcon: the subcon to repeat ``countfunc()`` times

    Example::

        MetaArray(lambda ctx: 5, UBInt8("foo"))
    """
    __slots__ = ["countfunc"]
    def __init__(self, countfunc, subcon):
        super(MetaArray, self).__init__(subcon)
        self.countfunc = countfunc
        self._clear_flag(self.FLAG_COPY_CONTEXT)
        self._set_flag(self.FLAG_DYNAMIC)
    def _parse(self, stream, context):
        obj = ListContainer()
        c = 0
        count = self.countfunc(context)
        try:
            if self.subcon.conflags & self.FLAG_COPY_CONTEXT:
                while c < count:
                    obj.append(self.subcon._parse(stream, context.__copy__()))
                    c += 1
            else:
                while c < count:
                    obj.append(self.subcon._parse(stream, context))
                    c += 1
        except ConstructError:
            raise ArrayError("expected %d, found %d" % (count, c), sys.exc_info()[1])
        return obj
    def _build(self, obj, stream, context):
        count = self.countfunc(context)
        if len(obj) != count:
            raise ArrayError("expected %d, found %d" % (count, len(obj)))
        if self.subcon.conflags & self.FLAG_COPY_CONTEXT:
            for subobj in obj:
                self.subcon._build(subobj, stream, context.__copy__())
        else:
            for subobj in obj:
                self.subcon._build(subobj, stream, context)
    def _sizeof(self, context):
        return self.subcon._sizeof(context) * self.countfunc(context)


class Range(Subconstruct):
    r"""
    A range-array. The subcon will iterate between ``mincount`` to ``maxcount`` times. If less than ``mincount`` elements are found, raises RangeError.

    .. seealso::

        The :func:`~construct.macros.GreedyRange` and :func:`~construct.macros.OptionalGreedyRange` macros.

    The general-case repeater. Repeats the given unit for at least ``mincount`` times, and up to ``maxcount`` times. If an exception occurs (EOF, validation error), the repeater exits. If less than ``mincount`` units have been successfully parsed, a RangeError is raised.

    .. note:: This object requires a seekable stream for parsing.

    :param mincount: the minimal count
    :param maxcount: the maximal count
    :param subcon: the subcon to repeat

    Example::

        >>> c = Range(3, 7, UBInt8("foo"))
        >>> c.parse("\x01\x02")
        Traceback (most recent call last):
          ...
        construct.core.RangeError: expected 3..7, found 2
        >>> c.parse("\x01\x02\x03")
        [1, 2, 3]
        >>> c.parse("\x01\x02\x03\x04\x05\x06")
        [1, 2, 3, 4, 5, 6]
        >>> c.parse("\x01\x02\x03\x04\x05\x06\x07")
        [1, 2, 3, 4, 5, 6, 7]
        >>> c.parse("\x01\x02\x03\x04\x05\x06\x07\x08\x09")
        [1, 2, 3, 4, 5, 6, 7]
        >>> c.build([1,2])
        Traceback (most recent call last):
          ...
        construct.core.RangeError: expected 3..7, found 2
        >>> c.build([1,2,3,4])
        '\x01\x02\x03\x04'
        >>> c.build([1,2,3,4,5,6,7,8])
        Traceback (most recent call last):
          ...
        construct.core.RangeError: expected 3..7, found 8
    """
    __slots__ = ["mincount", "maxcount"]

    def __init__(self, mincount, maxcount, subcon):
        if not 0 <= mincount <= maxcount:
            raise RangeError("unsane mincount %s and maxcount %s" % (mincount,maxcount))
        super(Range, self).__init__(subcon)
        self.mincount = mincount
        self.maxcount = maxcount
        self._clear_flag(self.FLAG_COPY_CONTEXT)
        self._set_flag(self.FLAG_DYNAMIC)

    def _parse(self, stream, context):
        obj = ListContainer()
        c = 0
        try:
            if self.subcon.conflags & self.FLAG_COPY_CONTEXT:
                while c < self.maxcount:
                    pos = stream.tell()
                    obj.append(self.subcon._parse(stream, context.__copy__()))
                    c += 1
            else:
                while c < self.maxcount:
                    pos = stream.tell()
                    obj.append(self.subcon._parse(stream, context))
                    c += 1
        except ConstructError:
            if c < self.mincount:
                raise RangeError("expected %d to %d, found %d" %
                    (self.mincount, self.maxcount, c))
            stream.seek(pos)
        return obj

    def _build(self, obj, stream, context):
        if not isinstance(obj, collections.Sequence):
            raise RangeError("expected sequence type, found %s" % type(obj))
        if len(obj) < self.mincount or len(obj) > self.maxcount:
            raise RangeError("expected %d to %d, found %d" %
                (self.mincount, self.maxcount, len(obj)))
        cnt = 0
        try:
            if self.subcon.conflags & self.FLAG_COPY_CONTEXT:
                for subobj in obj:
                    self.subcon._build(subobj, stream, context.__copy__())
                    cnt += 1
            else:
                for subobj in obj:
                    self.subcon._build(subobj, stream, context)
                    cnt += 1
        except ConstructError:
            if cnt < self.mincount:
                raise RangeError("expected %d to %d, found %d" %
                    (self.mincount, self.maxcount, len(obj)), sys.exc_info()[1])

    def _sizeof(self, context):
        raise SizeofError("cannot calculate size")



class RepeatUntil(Subconstruct):
    r"""
    An array that repeats until the predicate indicates it to stop. Note that the last element (which caused the repeat to exit) is included in the return value.

    :param predicate: a predicate function that takes (obj, context) and returns True if the stop-condition is met, or False to continue.
    :param subcon: the subcon to repeat.

    Example::

        # will read chars until '\x00' (inclusive)
        RepeatUntil(lambda obj, ctx: obj == b"\x00",
            Field("chars", 1)
        )
    """
    __slots__ = ["predicate"]
    def __init__(self, predicate, subcon):
        super(RepeatUntil, self).__init__(subcon)
        self.predicate = predicate
        self._clear_flag(self.FLAG_COPY_CONTEXT)
        self._set_flag(self.FLAG_DYNAMIC)
    def _parse(self, stream, context):
        obj = []
        try:
            if self.subcon.conflags & self.FLAG_COPY_CONTEXT:
                while True:
                    subobj = self.subcon._parse(stream, context.__copy__())
                    obj.append(subobj)
                    if self.predicate(subobj, context):
                        break
            else:
                while True:
                    subobj = self.subcon._parse(stream, context)
                    obj.append(subobj)
                    if self.predicate(subobj, context):
                        break
        except ConstructError:
            raise ArrayError("missing terminator", sys.exc_info()[1])
        return obj
    def _build(self, obj, stream, context):
        terminated = False
        if self.subcon.conflags & self.FLAG_COPY_CONTEXT:
            for subobj in obj:
                self.subcon._build(subobj, stream, context.__copy__())
                if self.predicate(subobj, context):
                    terminated = True
                    break
        else:
            for subobj in obj:
                #subobj = bchr(subobj)  -- WTF is that for?!
                #subobj = int2byte(subobj)  -- WTF is that for?!
                self.subcon._build(subobj, stream, context.__copy__())
                if self.predicate(subobj, context):
                    terminated = True
                    break
        if not terminated:
            raise ArrayError("missing terminator")
    def _sizeof(self, context):
        raise SizeofError("can't calculate size")


#===============================================================================
# structures and sequences
#===============================================================================
class Struct(Construct):
    """
    A sequence of named constructs, similar to structs in C. The elements are parsed and built in the order they are defined.

    .. seealso:: The :func:`~construct.macros.Embedded` macro.

    :param name: the name of the structure
    :param subcons: a sequence of subconstructs that make up this structure.
    :param nested: a keyword-only argument that indicates whether this struct creates a nested context. The default is True. This parameter is considered "advanced usage", and may be removed in the future.

    Example::

        Struct("foo",
            UBInt8("first_element"),
            UBInt16("second_element"),
            Padding(2),
            UBInt8("third_element"),
        )
    """
    __slots__ = ["subcons", "nested", "allow_overwrite"]
    def __init__(self, name, *subcons, **kw):
        self.nested = kw.pop("nested", True)
        self.allow_overwrite = kw.pop("allow_overwrite", False)
        if kw:
            raise TypeError("the only keyword argument accepted is 'nested'", kw)
        super(Struct, self).__init__(name)
        self.subcons = subcons
        self._inherit_flags(*subcons)
        self._clear_flag(self.FLAG_EMBED)
    def _parse(self, stream, context):
        if "<obj>" in context:
            obj = context["<obj>"]
            del context["<obj>"]
        else:
            obj = Container()
            if self.nested:
                context = Container(_ = context)
        for sc in self.subcons:
            if sc.conflags & self.FLAG_EMBED:
                context["<obj>"] = obj
                sc._parse(stream, context)
                if "<obj>" in context:
                    del context["<obj>"]
            else:
                subobj = sc._parse(stream, context)
                if sc.name is not None:
                    if sc.name in obj and not self.allow_overwrite:
                        raise OverwriteError("%r would be overwritten but allow_overwrite is False" % (sc.name,))
                    obj[sc.name] = subobj
                    context[sc.name] = subobj
        return obj
    def _build(self, obj, stream, context):
        if "<unnested>" in context:
            del context["<unnested>"]
        elif self.nested:
            context = Container(_ = context)
        for sc in self.subcons:
            if sc.conflags & self.FLAG_EMBED:
                context["<unnested>"] = True
                subobj = obj
            elif sc.name is None:
                subobj = None
            elif isinstance(sc, (Computed, Anchor, Checksum)):
                subobj = None
            else:
                subobj = obj[sc.name]
                context[sc.name] = subobj
            sc._build(subobj, stream, context)
    def _sizeof(self, context):
        #if self.nested:
        #    context = Container(_ = context)
        return sum(sc._sizeof(context) for sc in self.subcons)


class Sequence(Struct):
    """
    A sequence of unnamed constructs. The elements are parsed and built in the order they are defined.

    .. seealso:: The :func:`~construct.macros.Embedded` macro.

    :param name: the name of the structure
    :param subcons: a sequence of subconstructs that make up this structure.
    :param nested: a keyword-only argument that indicates whether this struct creates a nested context. The default is True. This parameter is considered "advanced usage", and may be removed in the future.

    Example::

        Sequence("foo",
            UBInt8("first_element"),
            UBInt16("second_element"),
            Padding(2),
            UBInt8("third_element"),
        )
    """
    __slots__ = []
    def _parse(self, stream, context):
        if "<obj>" in context:
            obj = context["<obj>"]
            del context["<obj>"]
        else:
            obj = ListContainer()
            if self.nested:
                context = Container(_ = context)
        for sc in self.subcons:
            if sc.conflags & self.FLAG_EMBED:
                context["<obj>"] = obj
                sc._parse(stream, context)
            else:
                subobj = sc._parse(stream, context)
                if sc.name is not None:
                    obj.append(subobj)
                    context[sc.name] = subobj
        return obj
    def _build(self, obj, stream, context):
        if "<unnested>" in context:
            del context["<unnested>"]
        elif self.nested:
            context = Container(_ = context)
        objiter = iter(obj)
        for sc in self.subcons:
            if sc.conflags & self.FLAG_EMBED:
                context["<unnested>"] = True
                subobj = objiter
            elif sc.name is None:
                subobj = None
            else:
                subobj = next(objiter)
                context[sc.name] = subobj
            sc._build(subobj, stream, context)


def _subobj(sc, obj):
    if sc.conflags & sc.FLAG_EMBED:
        return obj
    else:
        return obj[sc.name]

def _updcon(con, sc, obj):
    if sc.conflags & sc.FLAG_EMBED:
        con.update(obj)
    else:
        con[sc.name] = obj


class Union(Construct):
    r"""
    Set of overlapping fields (like unions in C). When parsing, all fields read the same data. When building, either the first subcon that builds without exception is allowed to put into the stream, or the subcon is selected by index or name. Size is the maximum of subcon sizes.

    .. note:: Requires a seekable stream.

    :param name: name of the union
    :param buildfrom: the subcon used for building and calculating the total size, can be integer index or string name or None (then tries each subcon)
    :param subcons: subconstructs for parsing, one of them used for building

    Example::

        Union("union",
            Struct("sub1", ULInt8("a"), ULInt8("b") ),
            Struct("sub2", ULInt16("c") ),
        )

        .build(dict(sub1=dict(a=1,b=2))) -> b"\x01\x02"
        .build(dict(sub2=dict(c=3)))     -> b"\x03\x00"

        Union("union",
            Embed(Struct("sub1", ULInt8("a"), ULInt8("b") )),
            Embed(Struct("sub2", ULInt16("c") )),
        )

        .build(dict(a=1,b=2)) -> b"\x01\x02"
        .build(dict(c=3)) -> b"\x03\x00"
    """
    __slots__ = ["name","subcons","buildfrom"]
    def __init__(self, name, *subcons, **kw):
        super(Union, self).__init__(name)
        args = [Peek(sc,perform_build=True) for sc in subcons]
        self.buildfrom = kw.get("buildfrom", None)
        self.subcons = args
    def _parse(self, stream, context):
        ret = Container()
        for sc in self.subcons:
            _updcon(ret, sc, sc._parse(stream, context))
        return ret
    def _build(self, obj, stream, context):
        if self.buildfrom is not None:
            if isinstance(self.buildfrom, int):
                index = self.buildfrom
                name = self.subcons[index].name
                self.subcons[index]._build(_subobj(self.subcons[index], obj), stream, context)
            elif isinstance(self.buildfrom, str):
                index = next(i for i,sc in enumerate(self.subcons) if sc.name == self.buildfrom)
                name = self.subcons[index].name
                self.subcons[index]._build(_subobj(self.subcons[index], obj), stream, context)
            else:
                raise TypeError("buildfrom is not int or str")
        else:
            for sc in self.subcons:
                try:
                    sc._build(_subobj(sc, obj), stream, context)
                except Exception:
                    pass
                else:
                    break
    def _sizeof(self, context):
        return max([sc._sizeof(context) for sc in self.subcons])


#===============================================================================
# conditional
#===============================================================================
class Switch(Construct):
    """
    A conditional branch. Switch will choose the case to follow based on the return value of keyfunc. If no case is matched, and no default value is given, SwitchError will be raised.

    .. seealso:: :func:`Pass`.

    :param name: the name of the construct
    :param keyfunc: a function that takes the context and returns a key, which will be used to choose the relevant case.
    :param cases: a dictionary mapping keys to constructs. the keys can be any values that may be returned by keyfunc.
    :param default: a default value to use when the key is not found in the cases. if not supplied, an exception will be raised when the key is not found. You can use the builtin construct Pass for 'do-nothing'.
    :param include_key: whether or not to include the key in the return value of parsing. defualt is False.

    Example::

        Struct("foo",
            UBInt8("type"),
            Switch("value", lambda ctx: ctx.type, {
                    1 : UBInt8("spam"),
                    2 : UBInt16("spam"),
                    3 : UBInt32("spam"),
                    4 : UBInt64("spam"),
                }
            ),
        )
    """

    class NoDefault(Construct):
        def _parse(self, stream, context):
            raise SwitchError("no default case defined")
        def _build(self, obj, stream, context):
            raise SwitchError("no default case defined")
        def _sizeof(self, context):
            raise SwitchError("no default case defined")
    NoDefault = NoDefault("No default value specified")

    __slots__ = ["subcons", "keyfunc", "cases", "default", "include_key"]

    def __init__(self, name, keyfunc, cases, default = NoDefault,
                 include_key = False):
        super(Switch, self).__init__(name)
        self._inherit_flags(*cases.values())
        self.keyfunc = keyfunc
        self.cases = cases
        self.default = default
        self.include_key = include_key
        self._inherit_flags(*cases.values())
        self._set_flag(self.FLAG_DYNAMIC)
    def _parse(self, stream, context):
        key = self.keyfunc(context)
        obj = self.cases.get(key, self.default)._parse(stream, context)
        if self.include_key:
            return key, obj
        else:
            return obj
    def _build(self, obj, stream, context):
        if self.include_key:
            key, obj = obj
        else:
            key = self.keyfunc(context)
        case = self.cases.get(key, self.default)
        case._build(obj, stream, context)
    def _sizeof(self, context):
        case = self.cases.get(self.keyfunc(context), self.default)
        return case._sizeof(context)


class Select(Construct):
    """
    Selects the first matching subconstruct. It will literally try each of the subconstructs, until one matches.

    .. note:: Requires a seekable stream.

    :param name: the name of the construct
    :param subcons: the subcons to try (order-sensitive)
    :param include_name: a keyword only argument, indicating whether to include the name of the selected subcon in the return value of parsing. default is false.

    Example::

        Select("foo",
            UBInt64("large"),
            UBInt32("medium"),
            UBInt16("small"),
            UBInt8("tiny"),
        )
    """
    __slots__ = ["subcons", "include_name"]
    def __init__(self, name, *subcons, **kw):
        include_name = kw.pop("include_name", False)
        if kw:
            raise TypeError("the only keyword argument accepted "
                "is 'include_name'", kw)
        super(Select, self).__init__(name)
        self.subcons = subcons
        self.include_name = include_name
        self._inherit_flags(*subcons)
        self._set_flag(self.FLAG_DYNAMIC)
    def _parse(self, stream, context):
        for sc in self.subcons:
            pos = stream.tell()
            context2 = context.__copy__()
            try:
                obj = sc._parse(stream, context2)
            except ConstructError:
                stream.seek(pos)
            else:
                context.__update__(context2)
                if self.include_name:
                    return sc.name, obj
                else:
                    return obj
        raise SelectError("no subconstruct matched")
    def _build(self, obj, stream, context):
        if self.include_name:
            name, obj = obj
            for sc in self.subcons:
                if sc.name == name:
                    sc._build(obj, stream, context)
                    return
        else:
            for sc in self.subcons:
                stream2 = BytesIO()
                context2 = context.__copy__()
                try:
                    sc._build(obj, stream2, context2)
                except Exception:
                    pass
                else:
                    context.__update__(context2)
                    stream.write(stream2.getvalue())
                    return
        raise SelectError("no subconstruct matched", obj)
    def _sizeof(self, context):
        raise SizeofError("can't calculate size")


#===============================================================================
# stream manipulation
#===============================================================================
class Pointer(Subconstruct):
    """
    Changes the stream position to a given offset, where the construction should take place, and restores the stream position when finished.

    .. seealso::
        :func:`Anchor`, :func:`OnDemand` and the
        :func:`~construct.macros.OnDemandPointer` macro.

    .. note:: Requires a seekable stream.

    :param offsetfunc: a function that takes the context and returns an absolute stream position, where the construction would take place
    :param subcon: the subcon to use at ``offsetfunc()``

    Example::

        Struct("foo",
            UBInt32("spam_pointer"),
            Pointer(lambda ctx: ctx.spam_pointer,
                Array(5, UBInt8("spam"))
            )
        )
    """
    __slots__ = ["offsetfunc"]
    def __init__(self, offsetfunc, subcon):
        super(Pointer, self).__init__(subcon)
        self.offsetfunc = offsetfunc
    def _parse(self, stream, context):
        newpos = self.offsetfunc(context)
        origpos = stream.tell()
        stream.seek(newpos, 2 if newpos < 0 else 0)
        obj = self.subcon._parse(stream, context)
        stream.seek(origpos)
        return obj
    def _build(self, obj, stream, context):
        newpos = self.offsetfunc(context)
        origpos = stream.tell()
        stream.seek(newpos, 2 if newpos < 0 else 0)
        self.subcon._build(obj, stream, context)
        stream.seek(origpos)
    def _sizeof(self, context):
        return 0

class Peek(Subconstruct):
    r"""
    Peeks at the stream: parses without changing the stream position. See also Union. If the end of the stream is reached when peeking, returns None.

    .. note:: Requires a seekable stream.

    :param subcon: the subcon to peek at
    :param perform_build: whether or not to perform building. by default this parameter is set to False, meaning building is a no-op.

    Example::

        Peek(UBInt8("foo"))
    """
    __slots__ = ["perform_build"]
    def __init__(self, subcon, perform_build=False):
        super(Peek, self).__init__(subcon)
        self.perform_build = perform_build
    def _parse(self, stream, context):
        pos = stream.tell()
        try:
            return self.subcon._parse(stream, context)
        except FieldError:
            pass
        finally:
            stream.seek(pos)
    def _build(self, obj, stream, context):
        if self.perform_build:
            try:
                pos = stream.tell()
                self.subcon._build(obj, stream, context)
            except:
                stream.seek(pos)
                raise
    def _sizeof(self, context):
        return self.subcon._sizeof(context)


class OnDemand(Subconstruct):
    r"""
    Allows for on-demand (lazy) parsing. When parsing, it will return a LazyContainer that represents a pointer to the data, but does not actually parses it from stream until it's "demanded". By accessing the 'value' property of LazyContainers, you will demand the data from the stream. The data will be parsed and cached for later use. You can use the 'has_value' property to know whether the data has already been demanded.

    .. seealso:: The :func:`~construct.macros.OnDemandPointer` macro.

    .. note:: Requires a seekable stream.

    :param subcon: the subcon to read/write on demand
    :param advance_stream: whether or not to advance the stream position. by default this is True, but if subcon is a pointer, this should be False.
    :param force_build: whether or not to force build. If set to False, and the LazyContainer has not been demaned, building is a no-op.

    Example::

        OnDemand(Array(10000, UBInt8("foo"))
    """
    __slots__ = ["advance_stream", "force_build"]
    def __init__(self, subcon, advance_stream = True, force_build = True):
        super(OnDemand, self).__init__(subcon)
        self.advance_stream = advance_stream
        self.force_build = force_build
    def _parse(self, stream, context):
        obj = LazyContainer(self.subcon, stream, stream.tell(), context)
        if self.advance_stream:
            stream.seek(self.subcon._sizeof(context), 1)
        return obj
    def _build(self, obj, stream, context):
        if not isinstance(obj, LazyContainer):
            self.subcon._build(obj, stream, context)
        elif self.force_build or obj.has_value:
            self.subcon._build(obj.value, stream, context)
        elif self.advance_stream:
            stream.seek(self.subcon._sizeof(context), 1)

class Buffered(Subconstruct):
    """
    Creates an in-memory buffered stream, which can undergo encoding and decoding prior to being passed on to the subconstruct.

    .. seealso:: The :func:`~construct.macros.Bitwise` macro.

    .. warning:: Do not use pointers inside ``Buffered``.

    :param subcon: the subcon which will operate on the buffer
    :param encoder: a function that takes a string and returns an encoded string (used after building)
    :param decoder: a function that takes a string and returns a decoded string (used before parsing)
    :param resizer: a function that takes the size of the subcon and "adjusts" or "resizes" it according to the encoding/decoding process.

    Example::

        Buffered(BitField("foo", 16),
            encoder = decode_bin,
            decoder = encode_bin,
            resizer = lambda size: size / 8,
        )
    """
    __slots__ = ["encoder", "decoder", "resizer"]
    def __init__(self, subcon, decoder, encoder, resizer):
        super(Buffered, self).__init__(subcon)
        self.encoder = encoder
        self.decoder = decoder
        self.resizer = resizer
    def _parse(self, stream, context):
        data = _read_stream(stream, self._sizeof(context))
        stream2 = BytesIO(self.decoder(data))
        return self.subcon._parse(stream2, context)
    def _build(self, obj, stream, context):
        size = self._sizeof(context)
        stream2 = BytesIO()
        self.subcon._build(obj, stream2, context)
        data = self.encoder(stream2.getvalue())
        assert len(data) == size
        _write_stream(stream, self._sizeof(context), data)
    def _sizeof(self, context):
        return self.resizer(self.subcon._sizeof(context))

class Restream(Subconstruct):
    """
    Wraps the stream with a read-wrapper (for parsing) or a write-wrapper (for building). The stream wrapper can buffer the data internally, reading it from- or writing it to the underlying stream as needed. For example, BitStreamReader reads whole bytes from the underlying stream, but returns them as individual bits.

    .. seealso:: The :func:`~construct.macros.Bitwise` macro.

    When the parsing or building is done, the stream's close method will be invoked. It can perform any finalization needed for the stream wrapper, but it must not close the underlying stream.

    .. warning:: Do not use pointers inside ``Restream``.

    :param subcon: the subcon
    :param stream_reader: the read-wrapper
    :param stream_writer: the write wrapper
    :param resizer: a function that takes the size of the subcon and "adjusts" or "resizes" it according to the encoding/decoding process.

    Example::

        Restream(BitField("foo", 16),
            stream_reader = BitStreamReader,
            stream_writer = BitStreamWriter,
            resizer = lambda size: size / 8,
        )
    """
    __slots__ = ["stream_reader", "stream_writer", "resizer"]
    def __init__(self, subcon, stream_reader, stream_writer, resizer):
        super(Restream, self).__init__(subcon)
        self.stream_reader = stream_reader
        self.stream_writer = stream_writer
        self.resizer = resizer
    def _parse(self, stream, context):
        stream2 = self.stream_reader(stream)
        obj = self.subcon._parse(stream2, context)
        stream2.close()
        return obj
    def _build(self, obj, stream, context):
        stream2 = self.stream_writer(stream)
        self.subcon._build(obj, stream2, context)
        stream2.close()
    def _sizeof(self, context):
        return self.resizer(self.subcon._sizeof(context))


#===============================================================================
# miscellaneous
#===============================================================================
class Reconfig(Subconstruct):
    """
    Reconfigures a subconstruct. Reconfig can be used to change the name and set and clear flags of the inner subcon.

    :param name: the new name
    :param subcon: the subcon to reconfigure
    :param setflags: the flags to set (default is 0)
    :param clearflags: the flags to clear (default is 0)

    Example::

        Reconfig("foo", UBInt8("bar"))
    """
    __slots__ = []
    def __init__(self, name, subcon, setflags = 0, clearflags = 0):
        subcon.name = name
        super(Reconfig, self).__init__(subcon)
        self._set_flag(setflags)
        self._clear_flag(clearflags)



class Anchor(Construct):
    r"""
    Gets the stream position when parsing or building.

    Anchors are useful for adjusting relative offsets to absolute positions, or to measure sizes of Constructs.

    To get an absolute pointer, use an Anchor plus a relative offset. To get a size, place two Anchors and measure their difference using Compute or the subtract field.

    :param name: the name of the anchor
    :param subtract: name of another Anchor or a lambda taking contect and returning int

    .. note:: Requires a tellable stream.

    .. seealso:: :func:`Pointer`
    """
    __slots__ = ["name", "subtract"]
    def __init__(self, name, subtract=None):
        super(Anchor, self).__init__(name)
        self.subtract = subtract
    def _parse(self, stream, context):
        position = stream.tell()
        if callable(self.subtract):
            position -= self.subtract(context)
        if isinstance(self.subtract, str):
            position -= context[self.subtract]
        context[self.name] = position
        return position
    def _build(self, obj, stream, context):
        position = stream.tell()
        if callable(self.subtract):
            position -= self.subtract(context)
        if isinstance(self.subtract, str):
            position -= context[self.subtract]
        context[self.name] = position
    def _sizeof(self, context):
        return 0



class Computed(Construct):
    r"""
    A computed value.

    Underlying byte stream is unaffected. When parsing `func(context)` provides the value.

    :param name: the name of the value
    :param func: a function that takes the context and return the computed value

    Example::

        Struct("struct",
            UBInt8("width"),
            UBInt8("height"),
            Computed("total", lambda ctx: ctx.width * ctx.height),
        )

        .parse(b'\x04\x05') -> Container(width=4,height=5,total=20)
        .build(Container(width=4,height=5,total=20)) -> b'\x04\x05'
    """
    __slots__ = ["func"]
    def __init__(self, name, func):
        super(Computed, self).__init__(name)
        self.func = func
        self._set_flag(self.FLAG_DYNAMIC)
    def _parse(self, stream, context):
        return self.func(context)
    def _build(self, obj, stream, context):
        pass
    def _sizeof(self, context):
        return 0

#class Dynamic(Construct):
#    """
#    Dynamically creates a construct and uses it for parsing and building.
#    This allows you to create change the construction tree on the fly.
#    Deprecated.
#
#    Parameters:
#    * name - the name of the construct
#    * factoryfunc - a function that takes the context and returns a new
#      construct object which will be used for parsing and building.
#
#    Example:
#    def factory(ctx):
#        if ctx.bar == 8:
#            return UBInt8("spam")
#        if ctx.bar == 9:
#            return String("spam", 9)
#
#    Struct("foo",
#        UBInt8("bar"),
#        Dynamic("spam", factory),
#    )
#    """
#    __slots__ = ["factoryfunc"]
#    def __init__(self, name, factoryfunc):
#        super(Dynamic, self).__init__(name, self.FLAG_COPY_CONTEXT)
#        self.factoryfunc = factoryfunc
#        self._set_flag(self.FLAG_DYNAMIC)
#    def _parse(self, stream, context):
#        return self.factoryfunc(context)._parse(stream, context)
#    def _build(self, obj, stream, context):
#        return self.factoryfunc(context)._build(obj, stream, context)
#    def _sizeof(self, context):
#        return self.factoryfunc(context)._sizeof(context)

class LazyBound(Construct):
    """
    Lazily bound construct, useful for constructs that need to make cyclic references (linked-lists, expression trees, etc.).

    :param name: the name of the construct
    :param bindfunc: the function (called without arguments) returning the bound construct

    Example::

        foo = Struct("foo",
            UBInt8("bar"),
            LazyBound("next", lambda: foo),
        )
    """
    __slots__ = ["bindfunc", "bound"]
    def __init__(self, name, bindfunc):
        super(LazyBound, self).__init__(name)
        self.bound = None
        self.bindfunc = bindfunc
    def _parse(self, stream, context):
        if self.bound is None:
            self.bound = self.bindfunc()
        return self.bound._parse(stream, context)
    def _build(self, obj, stream, context):
        if self.bound is None:
            self.bound = self.bindfunc()
        self.bound._build(obj, stream, context)
    def _sizeof(self, context):
        if self.bound is None:
            self.bound = self.bindfunc()
        return self.bound._sizeof(context)

class Pass(Construct):
    """
    A do-nothing construct, useful as the default case for Switch, or to indicate Enums.

    .. seealso:: :func:`Switch` and the :func:`~construct.macros.Enum` macro.

    .. note:: This construct is a singleton. Do not try to instatiate it, as it  will not work.

    Example::

        Pass
        .parse(b'...') -> None
        .build(None) -> None
    """
    __slots__ = []
    def _parse(self, stream, context):
        return None
    def _build(self, obj, stream, context):
        assert obj is None
    def _sizeof(self, context):
        return 0

Pass = Pass(None)
"""
A do-nothing construct, useful as the default case for Switch, or
to indicate Enums.

.. seealso:: :func:`Switch` and the :func:`~construct.macros.Enum` macro.

.. note:: This construct is a singleton. Do not try to instatiate it, as it  will not work.

Example::

    Pass
    .parse(b'...') -> None
    .build(None) -> None
"""

class Terminator(Construct):
    """
    Asserts the end of the stream has been reached at the point it's placed. You can use this to ensure no more unparsed data follows.

    .. note::
        * This construct is only meaningful for parsing. For building, it's a no-op.
        * This construct is a singleton. Do not try to instatiate it, as it will not work.

    Example::

        Terminator
    """
    __slots__ = []
    def _parse(self, stream, context):
        if stream.read(1):
            raise TerminatorError("expected end of stream")
    def _build(self, obj, stream, context):
        assert obj is None
    def _sizeof(self, context):
        return 0

Terminator = Terminator(None)
"""
Asserts the end of the stream has been reached at the point it's placed.
You can use this to ensure no more unparsed data follows.

.. note::
    * This construct is only meaningful for parsing. For building, it's a no-op.
    * This construct is a singleton. Do not try to instatiate it, as it will not work.

Example::

    Terminator
"""


# ==============================================================================
# Extra
# ==============================================================================
class ULInt24(StaticField):
    """
    A custom made construct for handling 3-byte types
    as used in ancient file formats.

    Better implementation would be writing a more flexible version of
    FormatField, rather then specifically implementing it for this case.
    """
    __slots__ = ["packer"]

    def __init__(self, name):
        self.packer = Packer("<BH")
        super(ULInt24, self).__init__(name, self.packer.size)

    def __getstate__(self):
        attrs = super(ULInt24, self).__getstate__()
        attrs["packer"] = attrs["packer"].format
        return attrs

    def __setstate__(self, attrs):
        attrs["packer"] = Packer(attrs["packer"])
        return super(ULInt24, self).__setstate__(attrs)

    def _parse(self, stream, context):
        vals = self.packer.unpack(_read_stream(stream, self.length))
        return vals[0] + (vals[1] << 8)

    def _build(self, obj, stream, context):
        vals = (obj % 256, obj >> 8)
        _write_stream(stream, self.length, self.packer.pack(*vals))


class Padding(Construct):
    r"""
    A padding field (adds bytes when building, discards bytes when parsing).

    :param length: length of the field. can be either an integer or a function that takes the context as an argument and returns the length
    :param pattern: the padding pattern (b-string character). default is b"\x00"
    :param strict: whether to verify during parsing that the stream contains the pattern. raises an exception if actual padding differs from the pattern. default is False.

    Example::

        Struct("struct",
            Byte("num"),
            Padding(4),
        )

        .parse(b"\xff\x00\x00\x00\x00") -> Container(num=255)
        .build(Container(num=255)) -> b"\xff\x00\x00\x00\x00"
        .sizeof() -> 5
    """
    __slots__ = ["length", "pattern", "strict"]
    def __init__(self, length, pattern=b"\x00", strict=False):
        if len(pattern) != 1:
            raise PaddingError("expected a pattern of single byte, given %r" % pattern)
        super(Padding, self).__init__(None)
        self.length = length
        self.pattern = pattern
        self.strict = strict
    def _parse(self, stream, context):
        length = self.length(context) if callable(self.length) else self.length
        read = _read_stream(stream, length)
        if self.strict:
            expected = length * self.pattern
            if read != expected:
                raise PaddingError("expected %r, found %r" % (expected, read))
        return None
    def _build(self, obj, stream, context):
        length = self.length(context) if callable(self.length) else self.length
        padding = length * self.pattern
        _write_stream(stream, length, padding)
    def _sizeof(self, context):
        length = self.length(context) if callable(self.length) else self.length
        return length


class Aligned(Construct):
    r"""
    Aligns subcon to modulus boundary using padding pattern

    :param subcon: the subcon to align
    :param modulus: the modulus boundary (default is 4)
    :param pattern: the padding pattern (default is \x00)

    Example::

        Aligned(
            Byte("num"),
            modulus=4,
        )

        .parse(b"\xff\x00\x00\x00") -> Container(num=255)
        .build(Container(num=255)) -> b"\xff\x00\x00\x00"
        .sizeof() -> 4

        Aligned(
            ULInt16("num"),
            modulus=4,
        )

        .parse(b"\xff\x00\x00\x00") -> Container(num=255)
        .build(Container(num=255)) -> b"\xff\x00\x00\x00"
        .sizeof() -> 4
    """
    __slots__ = ["subcon", "modulus", "pattern"]
    def __init__(self, subcon, modulus=4, pattern=b"\x00"):
        if modulus < 2:
            raise ValueError("modulus must be at least 2", modulus)
        if len(pattern) != 1:
            raise PaddingError("expected a pattern of single byte, given %r" % pattern)
        super(Aligned, self).__init__(subcon.name)
        self.subcon = subcon
        self.modulus = modulus
        self.pattern = pattern
    def _parse(self, stream, context):
        position1 = stream.tell()
        obj = self.subcon._parse(stream, context)
        position2 = stream.tell()
        pad = -(position2 - position1) % self.modulus
        _read_stream(stream, pad)
        return obj
    def _build(self, obj, stream, context):
        position1 = stream.tell()
        self.subcon._build(obj, stream, context)
        position2 = stream.tell()
        pad = -(position2 - position1) % self.modulus
        _write_stream(stream, pad, self.pattern * pad)
    def _sizeof(self, context):
        return self.subcon._sizeof(context)


class Const(Construct):
    r"""
    Constant field enforcing a constant value. It is used for file signatures, to validate that the given pattern exists. When parsed, the value must match.

    :param data: a bytes object
    :param subcon: the subcon to validate
    :param value: the expected value

    Example::

        Const(b"IHDR")

        Const("signature", b"IHDR")

        Const(ULInt64("signature"), 123)

    """
    __slots__ = ["subcon", "value"]
    def __init__(self, subcon, value=None):
        if value is None:
            subcon, value = StaticField(None, len(subcon)), subcon
        if isinstance(subcon, str):
            subcon, value = StaticField(subcon, len(value)), value
        super(Const, self).__init__(subcon.name)
        self.subcon = subcon
        self.value = value
    def _parse(self, stream, context):
        obj = self.subcon._parse(stream, context)
        if obj != self.value:
            raise ConstError("expected %r but parsed %r" % (self.value,obj))
        return obj
    def _build(self, obj, stream, context):
        self.subcon._build(self.value, stream, context)
    def _sizeof(self, context):
        return self.subcon._sizeof(context)


class String(Construct):
    r"""
    A configurable, variable-length string field.

    When parsing, the byte string is stripped of pad character (as specified) from the direction (as specified) then decoded (as specified). Length is a constant integer or a function of the context.
    When building, the string is encoded (as specified) then padded (as specified) from the direction (as specified) or trimmed as bytes (as specified).

    The padding character and direction must be specified for padding to work. The trim direction must be specified for trimming to work.

    :param name: name
    :param length: length in bytes (not unicode characters), as int or function
    :param encoding: encoding (e.g. "utf8") or None for bytes
    :param padchar: optional byte or unicode character to pad out strings
    :param paddir: direction to pad out strings (one of: right left both)
    :param trimdir: direction to trim strings (one of: right left)

    Example::

        String("string", 5)
        .parse(b"hello") -> b"hello"
        .build(u"hello") raises StringError
        .sizeof() -> 5

        String("string", 12, encoding="utf8")
        .parse(b"hello joh\xd4\x83n") -> u'hello joh\u0503n'
        .build(u'abc') -> b'abc\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        .sizeof() -> 12

        String("string", 10, padchar="X", paddir="right")
        .parse(b"helloXXXXX") -> b"hello"
        .build(u"hello") -> b"helloXXXXX"

        String("string", 5, trimdir="right")
        .build(u"hello12345") -> b"hello"

        String("string", lambda ctx: ctx.somefield)
        .sizeof() -> ?
    """
    __slots__ = ["length", "encoding", "padchar", "paddir", "trimdir"]
    def __init__(self, name, length, encoding=None, padchar=b"\x00", paddir="right", trimdir="right"):
        if not isinstance(padchar, bytes):
            if encoding:
                if isinstance(encoding, str):
                    padchar = padchar.encode(encoding)
                else:
                    padchar = encoding.encode(padchar)
            else:
                raise TypeError("padchar must be or be encodable to a byte string")
        if len(padchar) != 1:
            raise ValueError("padchar must be 1 character byte string, given %r" % (padchar,))
        if paddir not in ("right", "left", "center"):
            raise ValueError("paddir must be one of: right left center", paddir)
        if trimdir not in ("right", "left"):
            raise ValueError("trimdir must be one of: right left", trimdir)
        super(String, self).__init__(name)
        self.length = length
        self.encoding = encoding
        self.padchar = padchar
        self.paddir = paddir
        self.trimdir = trimdir
    def _parse(self, stream, context):
        length = self.length(context) if callable(self.length) else self.length
        obj = _read_stream(stream, length)
        padchar = self.padchar
        if self.paddir == "right":
            obj = obj.rstrip(padchar)
        elif self.paddir == "left":
            obj = obj.lstrip(padchar)
        else:
            obj = obj.strip(padchar)
        if self.encoding:
            if isinstance(self.encoding, str):
                obj = obj.decode(self.encoding)
            else:
                obj = self.encoding.decode(obj)
        return obj
    def _build(self, obj, stream, context):
        length = self.length(context) if callable(self.length) else self.length
        padchar = self.padchar
        if self.encoding:
            if isinstance(self.encoding, str):
                obj = obj.encode(self.encoding)
            else:
                obj = self.encoding.encode(obj)
        else:
            if not isinstance(obj, bytes):
                raise StringError("no encoding provided but building from unicode string?")
        if self.paddir == "right":
            obj = obj.ljust(length, padchar)
        elif self.paddir == "left":
            obj = obj.rjust(length, padchar)
        else:
            obj = obj.center(length, padchar)
        if len(obj) > length:
            if self.trimdir == "right":
                obj = obj[:length]
            elif self.trimdir == "left":
                obj = obj[-length:]
            else:
                raise StringError("expected a string of length %s given %s (%r)" % (length,len(obj),obj))
        _write_stream(stream, length, obj)
    def _sizeof(self, context):
        return self.length(context) if callable(self.length) else self.length


class CString(Construct):
    r"""
    A string ending in a terminator bytes character.

    ``CString`` is similar to the strings of C, C++, and other related programming languages.

    By default, the terminator is the NULL byte (b'\x00'). Terminators field can be a longer bytes string, and any of the characters breaks parsing. First character is used when building.

    :param name: name
    :param terminators: sequence of valid terminators, in order of preference
    :param encoding: encoding (e.g. "utf8") or None for bytes

    Example::

        CString("text")
        .parse(b"hello\x00") -> b"hello"
        .build(b"hello") -> b"hello\x00"

        CString("text", terminators=b"XYZ")
        .parse(b"helloX") -> b"hello"
        .parse(b"helloY") -> b"hello"
        .parse(b"helloZ") -> b"hello"
        .build(b"hello") -> b"helloX"
    """
    __slots__ = ["name", "terminators", "encoding", "charfield"]
    def __init__(self, name, terminators=b"\x00", encoding=None):
        if len(terminators) < 1:
            raise ValueError("terminators must be a bytes string of length >= 1")
        super(CString, self).__init__(name)
        self.terminators = terminators
        self.encoding = encoding
    def _parse(self, stream, context):
        obj = b""
        while True:
            char = _read_stream(stream, 1)
            if char in self.terminators:
                break
            obj += char
        if self.encoding:
            if isinstance(self.encoding, str):
                obj = obj.decode(self.encoding)
            else:
                obj = self.encoding.decode(obj)
        return obj
    def _build(self, obj, stream, context):
        if self.encoding:
            if isinstance(self.encoding, str):
                obj = obj.encode(self.encoding)
            else:
                obj = self.encoding.encode(obj)
        else:
            if not isinstance(obj, bytes):
                raise StringError("no encoding provided but building from unicode string?")
        obj += self.terminators[:1]
        _write_stream(stream, len(obj), obj)
    def _sizeof(self, context):
        raise SizeofError("cannot calculate size")


class GreedyString(Construct):
    r"""
    A string that reads the rest of the stream until EOF, or writes a given string as is.

    :param name: name
    :param encoding: encoding (e.g. "utf8") or None for bytes

    Example::

        GreedyString("greedy")
        .parse(b"hello\x00") -> b"hello\x00"
        .build(b"hello\x00") -> b"hello\x00"

        GreedyString("greedy", encoding="utf8")
        .parse(b"hello\x00") -> u"hello\x00"
        .build(u"hello\x00") -> b"hello\x00"
    """
    __slots__ = ["name", "encoding"]
    def __init__(self, name, encoding=None):
        super(GreedyString, self).__init__(name)
        self.encoding = encoding
    def _parse(self, stream, context):
        obj = stream.read()
        if self.encoding:
            if isinstance(self.encoding, str):
                obj = obj.decode(self.encoding)
            else:
                obj = self.encoding.decode(obj)
        return obj
    def _build(self, obj, stream, context):
        if self.encoding:
            if isinstance(self.encoding, str):
                obj = obj.encode(self.encoding)
            else:
                obj = self.encoding.encode(obj)
        else:
            if not isinstance(obj, bytes):
                raise StringError("no encoding provided but building from unicode string?")
        _write_stream(stream, len(obj), obj)
    def _sizeof(self, context):
        raise SizeofError("cannot calculate size")


class VarInt(Construct):
    r"""
    Varint encoded integer. Each 7 bits of the number are encoded in one byte in the stream.

    Scheme defined at Google's site:
    https://developers.google.com/protocol-buffers/docs/encoding

    Example::

        VarInt("number")
        .parse(b"\x85\x05") -> 645
        .build(645) -> b"\x85\x05"
    """
    def __init__(self, name):
        super(VarInt, self).__init__(name)
    def _parse(self, stream, context):
        acc = 0
        while True:
            b = ord(_read_stream(stream, 1))
            acc = (acc << 7) | (b & 127)
            if not b & 128:
                break
        return acc
    def _build(self, obj, stream, context):
        if obj < 0:
            raise ValueError("varint cannot build from negative number")
        while obj > 127:
            b = 128 | (obj & 127)
            obj >>= 7
            _write_stream(stream, 1, int2byte(b))
        _write_stream(stream, 1, int2byte(obj))
    def _sizeof(self, context):
        raise SizeofError("cannot calculate size")


class Checksum(Construct):
    r"""
    A field that is build or validated by a hash of a given byte range.

    :param checksumfield: a subcon field that reads the checksum, usually Bytes(int), it's name is reused
    :param hashfunc: a function taking bytes and returning whatever checksumfield takes
    :param startsat: name of an Anchor where checksumming starts, if None then starts at offset 0
    :param endsat: name of an Anchor where checksumming ends, if None then ends at current offset

    Example::

        def sha512(b):
            return hashlib.sha512(b).digest()

        Struct("struct",
            Byte("a"),
            Anchor("offset1"),
            Byte("b"),
            Anchor("offset2"),
            Checksum(Bytes("checksum",64), sha512, "offset1", "offset2"),
        )

        .parse(b"\x01\x02<...>") -> Container(a=1,b=2,offset1=1,offset2=2,checksum=b"<...>")
        .build(Container(a=1,b=2)) -> b"\x01\x02<...>"
        .sizeof() -> 64
    """
    __slots__ = ["name", "checksumfield", "hashfunc", "startsat", "endsat"]
    def __init__(self, checksumfield, hashfunc, startsat=None, endsat=None):
        if not isinstance(checksumfield, Construct):
            raise TypeError("checksumfield should be a Construct field")
        if not callable(hashfunc):
            raise TypeError("hashfunc should be a function(bytes) -> bytes")
        super(Checksum, self).__init__(checksumfield.name)
        self.checksumfield = checksumfield
        self.hashfunc = hashfunc
        self.startsat = startsat
        self.endsat = endsat
    def _parse(self, stream, context):
        hash1 = self.checksumfield._parse(stream, context)
        current = stream.tell()
        startsat = 0 if self.startsat is None else context[self.startsat]
        endsat = current if self.endsat is None else context[self.endsat]
        stream.seek(startsat, 0)
        hash2 = self.hashfunc(_read_stream(stream, endsat-startsat))
        stream.seek(current, 0)
        if hash1 != hash2:
            raise ChecksumError("wrong checksum, read %r, computed %r" % (hash1, hash2))
        return hash1
    def _build(self, obj, stream, context):
        current = stream.tell()
        startsat = 0 if self.startsat is None else context[self.startsat]
        endsat = current if self.endsat is None else context[self.endsat]
        stream.seek(startsat, 0)
        hash2 = self.hashfunc(_read_stream(stream, endsat-startsat))
        stream.seek(current, 0)
        self.checksumfield._build(hash2, stream, context)
    def _sizeof(self, context):
        return self.checksumfield._sizeof(context)


# class LengthValue(Construct):
#     r"""
#     Adapter for length-value pairs. When parsing, it returns only the value from the pair. When building, it calculates the length based on the value. Name of subcon is used.

#     See PrefixedArray and PascalString.

#     :param lengthfield: a subcon used for storing the length, can have no name
#     :param subcon: the subcon used for storing the value

#     Example::

#         LengthValue(Byte(), CString("text"))
#         .parse(b"\x06hello\0") -> b"hello"
#         .build(b"hello") -> b"\x06hello\0"
#     """
#     __slots__ = ["name", "lengthfield", "subcon"]
#     def __init__(self, lengthfield, subcon):
#         if not isinstance(lengthfield, Construct):
#             raise TypeError("lengthfield should be a Construct field")
#         if not isinstance(subcon, Construct):
#             raise TypeError("subcon should be a Construct field")
#         super(LengthValue, self).__init__(subcon.name)
#         self.lengthfield = lengthfield
#         self.subcon = subcon
#     def _parse(self, stream, context):
#         length = self.lengthfield._parse(stream, context)

#     def _build(self, obj, stream, context):
#         pass
#     def _sizeof(self, context):
#         return self.lengthfield._sizeof(context) + self.subcon._sizeof(context)

    # __slots__ = []
    # def _encode(self, obj, context):
    #     return (len(obj), obj)
    # def _decode(self, obj, context):
    #     return obj[1]

