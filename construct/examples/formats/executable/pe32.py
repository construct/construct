"""
Portable Executable (PE) 32 bit, little endian
Used on MSWindows systems (including DOS) for EXEs and DLLs

1999 paper:
http://download.microsoft.com/download/1/6/1/161ba512-40e2-4cc9-843a-923143f3456c/pecoff.doc

2006 with updates relevant for .NET:
http://download.microsoft.com/download/9/c/5/9c5b2167-8017-4bae-9fde-d599bac8184a/pecoff_v8.doc
"""
import time

from construct import (
    Adapter,
    Array,
    Bytes,
    Const,
    Container,
    Enum,
    ExprAdapter,
    FlagsEnum,
    HexDump,
    If,
    IfThenElse,
    Int16sl,
    Int16ul,
    Int32ul,
    Int64ul,
    Int8ul,
    OnDemand,
    OnDemandPointer,
    Padding,
    Pass,
    Pointer,
    String,
    Struct,
    Tell,
    this,
)


class UTCTimeStampAdapter(Adapter):
    def _decode(self, obj, context):
        return time.ctime(obj)

    def _encode(self, obj, context):
        return int(time.mktime(time.strptime(obj)))


def UTCTimeStamp():
    return UTCTimeStampAdapter(Int32ul)


class NamedSequence(Adapter):
    """
    creates a mapping between the elements of a sequence and their respective
    names. this is useful for sequences of a variable length, where each
    element in the sequence has a name (as is the case with the data
    directories of the PE header)
    """
    __slots__ = ["mapping", "rev_mapping"]
    prefix = "unnamed_"

    def __init__(self, subcon, mapping):
        super(NamedSequence, self).__init__(subcon)
        self.mapping = mapping
        self.rev_mapping = dict((v, k) for k, v in mapping.items())

    def _encode(self, obj, context):
        obj2 = [None] * len(obj)
        for name, value in obj.items():
            if name in self.rev_mapping:
                index = self.rev_mapping[name]
            elif name.startswith("__"):
                obj2.pop(-1)
                continue
            elif name.startswith(self.prefix):
                index = int(name.split(self.prefix)[1])
            else:
                raise ValueError("no mapping defined for %r" % (name,))
            obj2[index] = value
        return obj2

    def _decode(self, obj, context):
        obj2 = Container()
        for i, item in enumerate(obj):
            if i in self.mapping:
                name = self.mapping[i]
            else:
                name = "%s%d" % (self.prefix, i)
            setattr(obj2, name, item)
        return obj2


msdos_header = "msdos_header" / Struct(
    Const(b"MZ"),
    "partPag" / Int16ul,
    "page_count" / Int16ul,
    "relocation_count" / Int16ul,
    "header_size" / Int16ul,
    "minmem" / Int16ul,
    "maxmem" / Int16ul,
    "relocation_stackseg" / Int16ul,
    "exe_stackptr" / Int16ul,
    "checksum" / Int16ul,
    "exe_ip" / Int16ul,
    "relocation_codeseg" / Int16ul,
    "table_offset" / Int16ul,
    "overlay" / Int16ul,
    Padding(8),
    "oem_id" / Int16ul,
    "oem_info" / Int16ul,
    Padding(20),
    "coff_header_pointer" / Int32ul,
    "_assembly_start" / Tell,
    "code" / OnDemand(HexDump(Bytes(this.coff_header_pointer - this._assembly_start))),
)

symbol_table = "symbol_table" / Struct(
    "name" / String(8, padchar = b"\x00"),
    "value" / Int32ul,
    "section_number" / Enum(ExprAdapter(Int16sl,
            encoder = lambda obj, ctx: obj + 1,
            decoder = lambda obj, ctx: obj - 1,
        ),
        UNDEFINED = -1,
        ABSOLUTE = -2,
        DEBUG = -3,
        _default_ = Pass,
    ),
    "complex_type" / Enum(Int8ul,
        NULL = 0,
        POINTER = 1,
        FUNCTION = 2,
        ARRAY = 3,
    ),
    "base_type" / Enum(Int8ul,
        NULL = 0,
        VOID = 1,
        CHAR = 2,
        SHORT = 3,
        INT = 4,
        LONG = 5,
        FLOAT = 6,
        DOUBLE = 7,
        STRUCT = 8,
        UNION = 9,
        ENUM = 10,
        MOE = 11,
        BYTE = 12,
        WORD = 13,
        UINT = 14,
        DWORD = 15,
    ),
    "storage_class" / Enum(Int8ul,
        END_OF_FUNCTION = 255,
        NULL = 0,
        AUTOMATIC = 1,
        EXTERNAL = 2,
        STATIC = 3,
        REGISTER = 4,
        EXTERNAL_DEF = 5,
        LABEL = 6,
        UNDEFINED_LABEL = 7,
        MEMBER_OF_STRUCT = 8,
        ARGUMENT = 9,
        STRUCT_TAG = 10,
        MEMBER_OF_UNION = 11,
        UNION_TAG = 12,
        TYPE_DEFINITION = 13,
        UNDEFINED_STATIC = 14,
        ENUM_TAG = 15,
        MEMBER_OF_ENUM = 16,
        REGISTER_PARAM = 17,
        BIT_FIELD = 18,
        BLOCK = 100,
        FUNCTION = 101,
        END_OF_STRUCT = 102,
        FILE = 103,
        SECTION = 104,
        WEAK_EXTERNAL = 105,
    ),
    "number_of_aux_symbols" / Int8ul,
    "aux_symbols" / Array(this.number_of_aux_symbols, Bytes(18))
)

coff_header = "coff_header" / Struct(
    Const(b"PE\x00\x00"),
    "machine_type" / Enum(Int16ul,
        UNKNOWN = 0x0,
        AM33 = 0x1d3,
        AMD64 = 0x8664,
        ARM = 0x1c0,
        EBC = 0xebc,
        I386 = 0x14c,
        IA64 = 0x200,
        M32R = 0x9041,
        MIPS16 = 0x266,
        MIPSFPU = 0x366,
        MIPSFPU16 = 0x466,
        POWERPC = 0x1f0,
        POWERPCFP = 0x1f1,
        R4000 = 0x166,
        SH3 = 0x1a2,
        SH3DSP = 0x1a3,
        SH4 = 0x1a6,
        SH5= 0x1a8,
        THUMB = 0x1c2,
        WCEMIPSV2 = 0x169,
        _default_ = Pass
    ),
    "number_of_sections" / Int16ul,
    "time_stamp" / UTCTimeStamp(),
    "symbol_table_pointer" / Int32ul,
    "number_of_symbols" / Int32ul,
    "optional_header_size" / Int16ul,
    "characteristics" / FlagsEnum(Int16ul,
        RELOCS_STRIPPED = 0x0001,
        EXECUTABLE_IMAGE = 0x0002,
        LINE_NUMS_STRIPPED = 0x0004,
        LOCAL_SYMS_STRIPPED = 0x0008,
        AGGRESSIVE_WS_TRIM = 0x0010,
        LARGE_ADDRESS_AWARE = 0x0020,
        MACHINE_16BIT = 0x0040,
        BYTES_REVERSED_LO = 0x0080,
        MACHINE_32BIT = 0x0100,
        DEBUG_STRIPPED = 0x0200,
        REMOVABLE_RUN_FROM_SWAP = 0x0400,
        SYSTEM = 0x1000,
        DLL = 0x2000,
        UNIPROCESSOR_ONLY = 0x4000,
        BIG_ENDIAN_MACHINE = 0x8000,
    ),

    # symbol table
    "symbol_table" / Pointer(this.symbol_table_pointer, Array(this.number_of_symbols, symbol_table))
)

def PEPlusField():
    return IfThenElse(this.pe_type == "PE32_plus",
        Int64ul,
        Int32ul,
    )

optional_header = "optional_header" / Struct(
    # standard fields
    "pe_type" / Enum(Int16ul,
        PE32 = 0x10b,
        PE32_plus = 0x20b,
    ),
    "major_linker_version" / Int8ul,
    "minor_linker_version" / Int8ul,
    "code_size" / Int32ul,
    "initialized_data_size" / Int32ul,
    "uninitialized_data_size" / Int32ul,
    "entry_point_pointer" / Int32ul,
    "base_of_code" / Int32ul,

    # only in PE32 files
    "base_of_data" / If(this.pe_type == "PE32", Int32ul),

    # WinNT-specific fields
    "image_base" / PEPlusField(),
    "section_aligment" / Int32ul,
    "file_alignment" / Int32ul,
    "major_os_version" / Int16ul,
    "minor_os_version" / Int16ul,
    "major_image_version" / Int16ul,
    "minor_image_version" / Int16ul,
    "major_subsystem_version" / Int16ul,
    "minor_subsystem_version" / Int16ul,
    Padding(4),
    "image_size" / Int32ul,
    "headers_size" / Int32ul,
    "checksum" / Int32ul,
    "subsystem" / Enum(Int16ul,
        UNKNOWN = 0,
        NATIVE = 1,
        WINDOWS_GUI = 2,
        WINDOWS_CUI = 3,
        POSIX_CIU = 7,
        WINDOWS_CE_GUI = 9,
        EFI_APPLICATION = 10,
        EFI_BOOT_SERVICE_DRIVER = 11,
        EFI_RUNTIME_DRIVER = 12,
        EFI_ROM = 13,
        XBOX = 14,
        _default_ = Pass
    ),
    "dll_characteristics" / FlagsEnum(Int16ul,
        NO_BIND = 0x0800,
        WDM_DRIVER = 0x2000,
        TERMINAL_SERVER_AWARE = 0x8000,
    ),
    "reserved_stack_size" / PEPlusField(),
    "stack_commit_size" / PEPlusField(),
    "reserved_heap_size" / PEPlusField(),
    "heap_commit_size" / PEPlusField(),
    "loader_flags" / Int32ul,
    "number_of_data_directories" / Int32ul,

    NamedSequence(
        Array(this.number_of_data_directories,
            "data_directories" / Struct(
                "address" / Int32ul,
                "size" / Int32ul,
            )
        ),
        mapping = {
            0 : 'export_table',
            1 : 'import_table',
            2 : 'resource_table',
            3 : 'exception_table',
            4 : 'certificate_table',
            5 : 'base_relocation_table',
            6 : 'debug',
            7 : 'architecture',
            8 : 'global_ptr',
            9 : 'tls_table',
            10 : 'load_config_table',
            11 : 'bound_import',
            12 : 'import_address_table',
            13 : 'delay_import_descriptor',
            14 : 'complus_runtime_header',
        }
    ),
)

section = "section" / Struct(
    "name" / String(8, padchar = b"\x00"),
    "virtual_size" / Int32ul,
    "virtual_address" / Int32ul,
    "raw_data_size" / Int32ul,
    "raw_data_pointer" / Int32ul,
    "relocations_pointer" / Int32ul,
    "line_numbers_pointer" / Int32ul,
    "number_of_relocations" / Int16ul,
    "number_of_line_numbers" / Int16ul,
    "characteristics" / FlagsEnum(Int32ul,
        TYPE_REG = 0x00000000,
        TYPE_DSECT = 0x00000001,
        TYPE_NOLOAD = 0x00000002,
        TYPE_GROUP = 0x00000004,
        TYPE_NO_PAD = 0x00000008,
        TYPE_COPY = 0x00000010,
        CNT_CODE = 0x00000020,
        CNT_INITIALIZED_DATA = 0x00000040,
        CNT_UNINITIALIZED_DATA = 0x00000080,
        LNK_OTHER = 0x00000100,
        LNK_INFO = 0x00000200,
        TYPE_OVER = 0x00000400,
        LNK_REMOVE = 0x00000800,
        LNK_COMDAT = 0x00001000,
        MEM_FARDATA = 0x00008000,
        MEM_PURGEABLE = 0x00020000,
        MEM_16BIT = 0x00020000,
        MEM_LOCKED = 0x00040000,
        MEM_PRELOAD = 0x00080000,
        ALIGN_1BYTES = 0x00100000,
        ALIGN_2BYTES = 0x00200000,
        ALIGN_4BYTES = 0x00300000,
        ALIGN_8BYTES = 0x00400000,
        ALIGN_16BYTES = 0x00500000,
        ALIGN_32BYTES = 0x00600000,
        ALIGN_64BYTES = 0x00700000,
        ALIGN_128BYTES = 0x00800000,
        ALIGN_256BYTES = 0x00900000,
        ALIGN_512BYTES = 0x00A00000,
        ALIGN_1024BYTES = 0x00B00000,
        ALIGN_2048BYTES = 0x00C00000,
        ALIGN_4096BYTES = 0x00D00000,
        ALIGN_8192BYTES = 0x00E00000,
        LNK_NRELOC_OVFL = 0x01000000,
        MEM_DISCARDABLE = 0x02000000,
        MEM_NOT_CACHED = 0x04000000,
        MEM_NOT_PAGED = 0x08000000,
        MEM_SHARED = 0x10000000,
        MEM_EXECUTE = 0x20000000,
        MEM_READ = 0x40000000,
        MEM_WRITE = 0x80000000,
    ),

    "raw_data" / OnDemandPointer(this.raw_data_pointer, HexDump(Bytes(this.raw_data_size))),

    "line_numbers" / OnDemandPointer(this.line_numbers_pointer,
        Array(this.number_of_line_numbers,
            Struct(
                "type" / Int32ul,
                "line_number" / Int16ul,
            )
        )
    ),
    
    "relocations" / OnDemandPointer(this.relocations_pointer,
        Array(this.number_of_relocations,
            Struct(
                "virtual_address" / Int32ul,
                "symbol_table_index" / Int32ul,
                "type" / Int16ul,
            )
        )
    ),
)

pe32_file = "pe32_file" / Struct(
    # headers
    msdos_header,
    coff_header,
    "_start_of_optional_header" / Tell,
    optional_header,
    "_end_of_optional_header" / Tell,
    Padding(lambda ctx: min(0, 
            ctx.coff_header.optional_header_size -
            ctx._end_of_optional_header +
            ctx._start_of_optional_header
        )
    ),

    # sections
    "sections" / Array(this.coff_header.number_of_sections, section)
)

#pe32_file = Debugger(pe32_file)


if __name__ == "__main__":
    print (pe32_file.parse_stream(open("../../../tests/NOTEPAD.EXE", "rb")))
    print (pe32_file.parse_stream(open("../../../tests/sqlite3.dll", "rb")))
