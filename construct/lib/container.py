"""
Various containers.
"""


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


class Container(dict):
    """
    A generic container of attributes.

    Containers are the common way to express parsed data.
    """
    __slots__ = ["__keys_order__"]

    def __init__(self, *args, **kw):
        object.__setattr__(self, "__keys_order__", [])
        for arg in args:
            for k, v in arg.items():
                self[k] = v
        for k, v in kw.items():
            self[k] = v

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setitem__(self, key, val):
        if key not in self:
            self.__keys_order__.append(key)
        dict.__setitem__(self, key, val)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.__keys_order__.remove(key)

    __delattr__ = __delitem__
    __setattr__ = __setitem__

    def clear(self):
        dict.clear(self)
        del self.__keys_order__[:]

    def pop(self, key, *default):
        val = dict.pop(self, key, *default)
        self.__keys_order__.remove(key)
        return val

    def popitem(self):
        k, v = dict.popitem(self)
        self.__keys_order__.remove(k)
        return k, v

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

    def _search(self, name, search_all):
        items = []
        for key in self.keys():
            try:
                if key == name:
                    if search_all:
                        items.append(self[key])
                    else:
                        return self[key]
                if type(self[key]) == Container or type(self[key]) == ListContainer:
                    ret = self[key]._search(name, search_all)
                    if ret is not None:
                        if search_all:
                            items.extend(ret)
                        else:
                            return ret
            except:
                pass
        if search_all:
            return items
        else:
            return None

    def search(self, name):
        return self._search(name, False)

    def search_all(self, name):
        return self._search(name, True)

    __update__ = update
    __copy__ = copy

    def __iter__(self):
        return iter(self.__keys_order__)

    iterkeys = __iter__

    def itervalues(self):
        return (self[k] for k in self.__keys_order__)

    def iteritems(self):
        return ((k, self[k]) for k in self.__keys_order__)

    def keys(self):
        return self.__keys_order__

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))

    @recursion_lock("<...>")
    def __pretty_str__(self, nesting=1, indentation="    "):
        attrs = []
        ind = indentation * nesting
        for k, v in self.iteritems():
            if not k.startswith("_"):
                text = [ind, k, " = "]
                if hasattr(type(v), "__pretty_str__"):
                    text.append(v.__pretty_str__(nesting + 1, indentation))
                else:
                    text.append(repr(v))
                attrs.append("".join(text))
        if not attrs:
            return "%s()" % (self.__class__.__name__,)
        attrs.insert(0, self.__class__.__name__ + ":")
        return "\n".join(attrs)

    __str__ = __pretty_str__


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
            if hasattr(type(elem), "__pretty_str__"):
                lines.append(elem.__pretty_str__(nesting + 1, indentation))
            else:
                lines.append(repr(elem))
        lines.append("\n")
        lines.append(indentation * (nesting - 1))
        lines.append("]")
        return "".join(lines)

    def _search(self, name, search_all):
        items = []
        for item in self:
            try:
                ret = item._search(name, search_all)
            except:
                continue
            if ret is not None:
                if search_all:
                    items.extend(ret)
                else:
                    return ret
        if search_all:
            return items
        else:
            return None

    def search(self, name):
        return self._search(name, False)

    def search_all(self, name):
        return self._search(name, True)


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
        elif hasattr(type(self._value), "__pretty_str__"):
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
