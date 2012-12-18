"""
Construct 2 -- Parsing Made Fun

Homepage:
    http://construct.readthedocs.org

Hands-on example:
    >>> from construct import *
    >>> s = Struct("foo",
    ...     UBInt8("a"),
    ...     UBInt16("b"),
    ... )
    >>> s.parse("\\x01\\x02\\x03")
    Container(a = 1, b = 515)
    >>> print s.parse("\\x01\\x02\\x03")
    Container:
        a = 1
        b = 515
    >>> s.build(Container(a = 1, b = 0x0203))
    "\\x01\\x02\\x03"
"""

from construct.core import *
from construct.adapters import *
from construct.macros import *
from construct.lib.expr import this
from construct.debug import Probe, Debugger
from construct.version import version, version_string as __version__


#===============================================================================
# Metadata
#===============================================================================
__author__ = "Tomer Filiba <tomerfiliba@gmail.com>"
__maintainer__ = "Corbin Simpson <MostAwesomeDude@gmail.com>"

#===============================================================================
# Shorthand expressions
#===============================================================================
Bits = BitField
Byte = UBInt8
Bytes = Field
Const = ConstAdapter
Tunnel = TunnelAdapter
Embed = Embedded

#===============================================================================
# exposed names
#===============================================================================
__all__ = [
    'AdaptationError', 'Adapter', 'Alias', 'Aligned', 'AlignedStruct',
    'Anchor', 'Array', 'ArrayError', 'BFloat32', 'BFloat64', 'Bit', 'BitField',
    'BitIntegerAdapter', 'BitIntegerError', 'BitStruct', 'Bits', 'Bitwise',
    'Buffered', 'Byte', 'Bytes', 'CString', 'CStringAdapter', 'Const',
    'ConstAdapter', 'ConstError', 'Construct', 'ConstructError', 'Container',
    'Debugger', 'Embed', 'Embedded', 'EmbeddedBitStruct', 'Enum', 'ExprAdapter',
    'Field', 'FieldError', 'Flag', 'FlagsAdapter', 'FlagsContainer',
    'FlagsEnum', 'FormatField', 'GreedyRange', 'HexDumpAdapter', 'If',
    'IfThenElse', 'IndexingAdapter', 'LFloat32', 'LFloat64', 'LazyBound',
    'LengthValueAdapter', 'ListContainer', 'MappingAdapter', 'MappingError',
    'MetaArray', 'MetaField', 'NFloat32', 'NFloat64', 'Nibble', 'NoneOf',
    'Octet', 'OnDemand', 'OnDemandPointer', 'OneOf', 'OpenRange', 'Optional',
    'OptionalGreedyRange', 'PaddedStringAdapter', 'Padding',
    'PaddingAdapter', 'PaddingError', 'PascalString', 'Pass', 'Peek',
    'Pointer', 'PrefixedArray', 'Probe', 'Range', 'RangeError', 'Reconfig',
    'Rename', 'RepeatUntil', 'Restream', 'SBInt16', 'SBInt32',
    'SBInt64', 'SBInt8', 'SLInt16', 'SLInt32', 'SLInt64', 'SLInt8', 'SNInt16',
    'SNInt32', 'SNInt64', 'SNInt8', 'Select', 'SelectError', 'Sequence',
    'SizeofError', 'SlicingAdapter', 'StaticField', 'String',
    'StringAdapter', 'Struct', 'Subconstruct', 'Switch', 'SwitchError',
    'SymmetricMapping', 'Terminator', 'TerminatorError', 'Tunnel',
    'TunnelAdapter', 'UBInt16', 'UBInt32', 'UBInt64', 'UBInt8', 'ULInt16',
    'ULInt32', 'ULInt64', 'ULInt8', 'UNInt16', 'UNInt32', 'UNInt64', 'UNInt8',
    'Union', 'ValidationError', 'Validator', 'Value', "Magic", "this",
]