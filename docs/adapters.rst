=======================
Adapters and Validators
=======================

Adapting
==============

Adapting is the process of converting one representation of an object to another. One representation is usually "lower" (closer to the byte level), and the other "higher" (closer to the python object model). The process of converting the lower representation to the higher one is called decoding, and the process of converting the higher level representation to the lower one is called encoding. Encoding and decoding are expected to be symmetrical, so that they counter-act each other ``encode(decode(x)) == x`` and ``decode(encode(x)) == x``.

Custom adapter classes derive from the abstract Adapter class, and implement their own versions of `_decode` and `_encode`, as shown below:

::

    class IpAddressAdapter(Adapter):
        def _decode(self, obj, context, path):
            return ".".join(map(str, obj))

        def _encode(self, obj, context, path):
            return list(map(int, obj.split(".")))

    IpAddress = IpAddressAdapter(Byte[4])

As you can see, the IpAddressAdapter encodes a string of the format "XXX.XXX.XXX.XXX" to a list of 4 integers like [XXX, XXX, XXX, XXX]. This representation then gets handed over to Array(4, Byte) which turns it into bytes.

Note that the adapter does not perform any manipulation of the stream, it only converts between objects!

::

    class Adapter(Subconstruct):
        def _parse(self, stream, context, path):
            return self._decode(self.subcon._parse(stream, context, path), context, path)

        def _build(self, obj, stream, context, path):
            return self.subcon._build(self._encode(obj, context, path), stream, context, path)

This is called separation of concern, and is a key feature of component-oriented programming. It allows us to keep each component very simple and unaware of its consumers. Whenever we need a different representation of the data, we don't need to write a new Construct -- we only write the suitable adapter.

So, let's see our adapter in action:

>>> IpAddress.parse(b"\x01\x02\x03\x04")
'1.2.3.4'
>>> IpAddress.build("192.168.2.3")
b'\xc0\xa8\x02\x03'

Having the representation separated from the actual parsing or building means an adapter is loosely coupled with its underlying construct. As with enums for example, we can use the same enum for `Byte` or `Int32sl` or `VarInt`, as long as the underlying construct returns an object that we can map. Moreover, we can stack several adapters on top of one another, to create a nested adapter.


Using expressions instead of classes
------------------------------------

Adaters can be created declaratively using ExprAdapter. Note that this construction is not recommended, unless its much cleaner than Adapter. Use can use `obj_` expression to generate lambdas that operate on the object passed around.

For example, month in object model might be `1..12` but data format saves it as `0..11`.

::

    >>> d = ExprAdapter(Byte, obj_+1, obj_-1)
    >>> d.parse(b'\x04')
    5
    >>> d.build(5)
    b'\x04'

Or another example, where some of the bits are unset in both parsed/build objects:

::

    >>> d = ExprSymmetricAdapter(Byte, obj_ & 0b00001111)
    >>> d.parse(b"\xff")
    15
    >>> d.build(255)
    b'\x0f'


Validating and filtering
==============================

Validating means making sure the parsed/built object meets a given condition. Validators simply raise `ValidationError` if the lambda predicate indicates False when called with the actual object. You can write custom validators by deriving from the Validator class and implementing the `_validate` method.

::

    class VersionNumberValidator(Validator):
        def _validate(self, obj, context, path):
            return obj in [1,2,3]

    VersionNumber = VersionNumberValidator(Byte)

::

    >>> VersionNumber.build(3)
    b'\x03'
    >>> VersionNumber.build(88)
    ValidationError: object failed validation: 88

For reference, this is how it works under the hood (in core library):

::

    class Validator(SymmetricAdapter):
        def _decode(self, obj, context, path):
            if not self._validate(obj, context, path):
                raise ValidationError("object failed validation: %s" % (obj,))
            return obj



Using expressions instead of classes
------------------------------------

Validators can also be created declaratively using ExprValidator. Unfortunately `obj_` expression does not work with `in` (contains) operator, nor with `and or not` logical operators. But it still has the advantage that it can be declared inlined. Adapter and Validator derived classes cannot be inlined inside a Struct.

For example, if 7 out of 8 bits are not allowed to be set (like a flag boolean):

::

    >>> d = ExprValidator(Byte, obj_ & 0b11111110 == 0)
    >>> d.build(1)
    b'\x01'
    >>> d.build(88)
    ValidationError: object failed validation: 88

ExprValidator also accepts an `exception` keyword argument to override `ValidationError`.
