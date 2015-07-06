"""
Various containers.
"""
from cyordereddict import OrderedDict


class Container(OrderedDict):
    __delattr__ = OrderedDict.__delitem__
    __setattr__ = OrderedDict.__setitem__

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def update(self, seq, **kw):
        if hasattr(seq, "keys"):
            for k in seq.keys():
                self[k] = seq[k]
        else:
            for k, v in seq:
                self[k] = v
        dict.update(self, kw)

    def copy(self):
        inst = self.__class__()
        inst.update(self.iteritems())
        return inst

    __update__ = update
    __copy__ = copy


def recursion_lock(retval, lock_name="__recursion_lock__"):
    def decorator(func):
        def wrapper(self, *args, **kw):
            if getattr(self, lock_name, False):
                return retval
            setattr(self, lock_name, True)
            try:
                return func(self, *args, **kw)
            finally:
                setattr(self, lock_name, False)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


class FlagsContainer(Container):

    """
    A container providing pretty-printing for flags.

    Only set flags are displayed.
    """

    @recursion_lock("<...>")
    def __pretty_str__(self, nesting=1, indentation="    "):
        attrs = []
        ind = indentation * nesting
        for k in self.keys():
            v = self[k]
            if not k.startswith("_") and v:
                attrs.append(ind + k)
        if not attrs:
            return "%s()" % (self.__class__.__name__,)
        attrs.insert(0, self.__class__.__name__ + ":")
        return "\n".join(attrs)


class ListContainer(list):

    """
    A container for lists.
    """
    __slots__ = ["__recursion_lock__"]

    def __str__(self):
        return self.__pretty_str__()

    @recursion_lock("[...]")
    def __pretty_str__(self, nesting=1, indentation="    "):
        if not self:
            return "[]"
        ind = indentation * nesting
        lines = ["["]
        for elem in self:
            lines.append("\n")
            lines.append(ind)
            if hasattr(elem, "__pretty_str__"):
                lines.append(elem.__pretty_str__(nesting + 1, indentation))
            else:
                lines.append(repr(elem))
        lines.append("\n")
        lines.append(indentation * (nesting - 1))
        lines.append("]")
        return "".join(lines)


class LazyContainer(object):

    __slots__ = ["subcon", "stream", "pos", "context", "_value"]

    def __init__(self, subcon, stream, pos, context):
        self.subcon = subcon
        self.stream = stream
        self.pos = pos
        self.context = context
        self._value = NotImplemented

    def __eq__(self, other):
        try:
            return self._value == other._value
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return self.__pretty_str__()

    def __pretty_str__(self, nesting=1, indentation="    "):
        if self._value is NotImplemented:
            text = "<unread>"
        elif hasattr(self._value, "__pretty_str__"):
            text = self._value.__pretty_str__(nesting, indentation)
        else:
            text = str(self._value)
        return "%s: %s" % (self.__class__.__name__, text)

    def read(self):
        self.stream.seek(self.pos)
        return self.subcon._parse(self.stream, self.context)

    def dispose(self):
        self.subcon = None
        self.stream = None
        self.context = None
        self.pos = None

    def _get_value(self):
        if self._value is NotImplemented:
            self._value = self.read()
        return self._value

    value = property(_get_value)

    has_value = property(lambda self: self._value is not NotImplemented)


if __name__ == "__main__":
    c = Container(x=5)
    c.y = 8
    c.z = 9
    c.w = 10
    c.foo = 5

    print (c)
