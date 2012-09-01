from construct import Struct, UBInt8, Debugger, Enum


foo = Struct("foo",
    UBInt8("bar"),
    Debugger(
        Enum(UBInt8("spam"),
            ABC = 1,
            DEF = 2,
            GHI = 3,
        )
    ),
    UBInt8("eggs"),
)


print foo.parse("\x01\x02\x03")

print foo.parse("\x01\x04\x03")

