=================
Transition to 2.10
=================


Overall
==========

Dropped support for Python 2.7 and 3.5 (pypy is also supported)

Bytes GreedyBytes can build from bytearrays (not just bytes)

Embedded and EmbeddedSwitch were permanently removed

Exceptions always display path information

build_file() opens a file for both reading and writing

BytesInteger BitsInteger can take lambda for swapped parameter

cloudpickle is now supported and tested for

ZigZag signed integer encoding from Protocol Buffers added

FormatField now supports ? format string

CompressedLZ4 tunneling class added

Windows is now officially supported and tested for

BytesInteger and BitsInteger are checking numbers are valid

BitsInteger swapped semantic was fixed

Compilation covers building as well, parsing slightly improved

Array GreedyRange RepeatUntil builders use discard option

Sequence build fixed, no longer skips subcons on short obj

Lazy class fixed, seeks the not-yet parsed subcon
