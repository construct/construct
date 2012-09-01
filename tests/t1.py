from construct import Aligned, Struct, Byte, Array, Debugger


s = Aligned(
    Struct('test',
        Byte('length'),
        Array(lambda ctx: ctx.length, Byte('x')),
    )
)
print Debugger(s).parse("\x03aaab")


