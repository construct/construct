"""
Portable Network Graphics (PNG) file format
Official spec: http://www.w3.org/TR/PNG

Original code contributed by Robin Munn (rmunn at pobox dot com)
(although the code has been extensively reorganized to meet Construct's
coding conventions)
"""
from construct import *


#===============================================================================
# utils
#===============================================================================
def Coord(name, field=UBInt8):
    return Struct(name,
        field("x"),
        field("y"),
    )

compression_method = Enum(UBInt8("compression_method"),
    deflate = 0,
    _default_ = Pass
)


#===============================================================================
# 11.2.3: PLTE - Palette
#===============================================================================
plte_info = Struct("plte_info",
    Value("num_entries", lambda ctx: ctx._.length / 3),
    Array(lambda ctx: ctx.num_entries,
        Struct("palette_entries",
            UBInt8("red"),
            UBInt8("green"),
            UBInt8("blue"),
        ),
    ),
)

#===============================================================================
# 11.2.4: IDAT - Image data
#===============================================================================
idat_info = OnDemand(
    Field("idat_info", lambda ctx: ctx.length),
)

#===============================================================================
# 11.3.2.1: tRNS - Transparency
#===============================================================================
trns_info = Switch("trns_info", lambda ctx: ctx._.image_header.color_type, 
    {
        "greyscale": Struct("data",
            UBInt16("grey_sample")
        ),
        "truecolor": Struct("data",
            UBInt16("red_sample"),
            UBInt16("blue_sample"),
            UBInt16("green_sample"),
        ),
        "indexed": Array(lambda ctx: ctx.length,
            UBInt8("alpha"),
        ),
    }
)

#===============================================================================
# 11.3.3.1: cHRM - Primary chromacities and white point
#===============================================================================
chrm_info = Struct("chrm_info",
    Coord("white_point", UBInt32),
    Coord("red", UBInt32),
    Coord("green", UBInt32),
    Coord("blue", UBInt32),
)

#===============================================================================
# 11.3.3.2: gAMA - Image gamma
#===============================================================================
gama_info = Struct("gama_info",
    UBInt32("gamma"),
)

#===============================================================================
# 11.3.3.3: iCCP - Embedded ICC profile
#===============================================================================
iccp_info = Struct("iccp_info",
    CString("name"),
    compression_method,
    Field("compressed_profile", 
        lambda ctx: ctx._.length - (len(ctx.name) + 2)
    ),
)

#===============================================================================
# 11.3.3.4: sBIT - Significant bits
#===============================================================================
sbit_info = Switch("sbit_info", lambda ctx: ctx._.image_header.color_type, 
    {
        "greyscale": Struct("data",
            UBInt8("significant_grey_bits"),
        ),
        "truecolor": Struct("data",
            UBInt8("significant_red_bits"),
            UBInt8("significant_green_bits"),
            UBInt8("significant_blue_bits"),
        ),
        "indexed": Struct("data",
            UBInt8("significant_red_bits"),
            UBInt8("significant_green_bits"),
            UBInt8("significant_blue_bits"),
        ),
        "greywithalpha": Struct("data",
            UBInt8("significant_grey_bits"),
            UBInt8("significant_alpha_bits"),
        ),
        "truewithalpha": Struct("data",
            UBInt8("significant_red_bits"),
            UBInt8("significant_green_bits"),
            UBInt8("significant_blue_bits"),
            UBInt8("significant_alpha_bits"),
        ),
    }
)

#===============================================================================
# 11.3.3.5: sRGB - Standard RPG color space
#===============================================================================
srgb_info = Struct("srgb_info",
    Enum(UBInt8("rendering_intent"),
        perceptual = 0,
        relative_colorimetric = 1,
        saturation = 2,
        absolute_colorimetric = 3,
        _default_ = Pass,
    ),
)

#===============================================================================
# 11.3.4.3: tEXt - Textual data
#===============================================================================
text_info = Struct("text_info",
    CString("keyword"),
    Field("text", lambda ctx: ctx._.length - (len(ctx.keyword) + 1)),
)

#===============================================================================
# 11.3.4.4: zTXt - Compressed textual data
#===============================================================================
ztxt_info = Struct("ztxt_info",
    CString("keyword"),
    compression_method,
    OnDemand(
        Field("compressed_text",
            # As with iCCP, length is chunk length, minus length of
            # keyword, minus two: one byte for the null terminator,
            # and one byte for the compression method.
            lambda ctx: ctx._.length - (len(ctx.keyword) + 2),
        ),
    ),
)

#===============================================================================
# 11.3.4.5: iTXt - International textual data
#===============================================================================
itxt_info = Struct("itxt_info",
    CString("keyword"),
    UBInt8("compression_flag"),
    compression_method,
    CString("language_tag"),
    CString("translated_keyword"),
    OnDemand(
        Field("text",
            lambda ctx: ctx._.length - (len(ctx.keyword) + 
            len(ctx.language_tag) + len(ctx.translated_keyword) + 5),
        ),
    ),
)

#===============================================================================
# 11.3.5.1: bKGD - Background color
#===============================================================================
bkgd_info = Switch("bkgd_info", lambda ctx: ctx._.image_header.color_type, 
    {
        "greyscale": Struct("data",
            UBInt16("background_greyscale_value"),
            Alias("grey", "background_greyscale_value"),
        ),
        "greywithalpha": Struct("data",
            UBInt16("background_greyscale_value"),
            Alias("grey", "background_greyscale_value"),
        ),
        "truecolor": Struct("data",
            UBInt16("background_red_value"),
            UBInt16("background_green_value"),
            UBInt16("background_blue_value"),
            Alias("red", "background_red_value"),
            Alias("green", "background_green_value"),
            Alias("blue", "background_blue_value"),
        ),
        "truewithalpha": Struct("data",
            UBInt16("background_red_value"),
            UBInt16("background_green_value"),
            UBInt16("background_blue_value"),
            Alias("red", "background_red_value"),
            Alias("green", "background_green_value"),
            Alias("blue", "background_blue_value"),
        ),
        "indexed": Struct("data",
            UBInt16("background_palette_index"),
            Alias("index", "background_palette_index"),
        ),
    }
)

#===============================================================================
# 11.3.5.2: hIST - Image histogram
#===============================================================================
hist_info = Array(lambda ctx: ctx._.length / 2,
    UBInt16("frequency"),
)

#===============================================================================
# 11.3.5.3: pHYs - Physical pixel dimensions
#===============================================================================
phys_info = Struct("phys_info",
    UBInt32("pixels_per_unit_x"),
    UBInt32("pixels_per_unit_y"),
    Enum(UBInt8("unit"),
        unknown = 0,
        meter = 1,
        _default_ = Pass
    ),
)

#===============================================================================
# 11.3.5.4: sPLT - Suggested palette
#===============================================================================
def splt_info_data_length(ctx):
    if ctx.sample_depth == 8:
        entry_size = 6
    else:
        entry_size = 10
    return (ctx._.length - len(ctx.name) - 2) / entry_size

splt_info = Struct("data",
    CString("name"),
    UBInt8("sample_depth"),
    Array(lambda ctx: splt_info_data_length,
        IfThenElse("table", lambda ctx: ctx.sample_depth == 8,
            # Sample depth 8
            Struct("table",
                UBInt8("red"),
                UBInt8("green"),
                UBInt8("blue"),
                UBInt8("alpha"),
                UBInt16("frequency"),
            ),
            # Sample depth 16
            Struct("table",
                UBInt16("red"),
                UBInt16("green"),
                UBInt16("blue"),
                UBInt16("alpha"),
                UBInt16("frequency"),
            ),
        ),
    ),
)

#===============================================================================
# 11.3.6.1: tIME - Image last-modification time
#===============================================================================
time_info = Struct("data",
    UBInt16("year"),
    UBInt8("month"),
    UBInt8("day"),
    UBInt8("hour"),
    UBInt8("minute"),
    UBInt8("second"),
)

#===============================================================================
# chunks
#===============================================================================
default_chunk_info = OnDemand(
    HexDumpAdapter(Field(None, lambda ctx: ctx.length))
)

chunk = Struct("chunk",
    UBInt32("length"),
    String("type", 4),
    Switch("data", lambda ctx: ctx.type, 
        {
            "PLTE" : plte_info,
            "IEND" : Pass,
            "IDAT" : idat_info,
            "tRNS" : trns_info,
            "cHRM" : chrm_info,
            "gAMA" : gama_info,
            "iCCP" : iccp_info,
            "sBIT" : sbit_info,
            "sRGB" : srgb_info,
            "tEXt" : text_info,
            "zTXt" : ztxt_info,
            "iTXt" : itxt_info,
            "bKGD" : bkgd_info,
            "hIST" : hist_info,
            "pHYs" : phys_info,
            "sPLT" : splt_info,
            "tIME" : time_info,
        },
        default = default_chunk_info,
    ),
    UBInt32("crc"),
)

image_header_chunk = Struct("image_header",
    UBInt32("length"),
    Magic(b"IHDR"),
    UBInt32("width"),
    UBInt32("height"),
    UBInt8("bit_depth"),
    Enum(UBInt8("color_type"),
        greyscale = 0,
        truecolor = 2,
        indexed = 3,
        greywithalpha = 4,
        truewithalpha = 6,
        _default_ = Pass,
    ),
    compression_method,
    Enum(UBInt8("filter_method"),
        # "adaptive filtering with five basic filter types"
        adaptive5 = 0,
        _default_ = Pass,
    ),
    Enum(UBInt8("interlace_method"),
        none = 0,
        adam7 = 1,
        _default_ = Pass,
    ),
    UBInt32("crc"),
)


#===============================================================================
# the complete PNG file
#===============================================================================
png_file = Struct("png",
    Magic(b"\x89PNG\r\n\x1a\n"),
    image_header_chunk,
    Rename("chunks", GreedyRange(chunk)),
)
