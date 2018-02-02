"""
Executable and Linkable Format (ELF), 32 bit, big or little endian.
Used on Unix systems as a replacement of the older a.out format.

Big-endian support kindly submitted by Craig McQueen (mcqueen-c#edsrd1!yzk!co!jp).
"""

from construct import *


def elf32_body(ElfInt16, ElfInt32):
    elf32_program_header = Struct(
        "type" / Enum(ElfInt32,
            NULL = 0,
            LOAD = 1,
            DYNAMIC = 2,
            INTERP = 3,
            NOTE = 4,
            SHLIB = 5,
            PHDR = 6,
            default = Pass,
        ),
        "offset" / ElfInt32,
        "vaddr" / ElfInt32,
        "paddr" / ElfInt32,
        "file_size" / ElfInt32,
        "mem_size" / ElfInt32,
        "flags" / ElfInt32,
        "align" / ElfInt32,
    )
    
    elf32_section_header = Struct(
        "name_offset" / ElfInt32,
        "name" / Pointer(this._.strtab_data_offset + this.name_offset, CString(encoding=StringsAsBytes)),
        "type" / Enum(ElfInt32, 
            NULL = 0,
            PROGBITS = 1,
            SYMTAB = 2,
            STRTAB = 3,
            RELA = 4,
            HASH = 5,
            DYNAMIC = 6,
            NOTE = 7,
            NOBITS = 8,
            REL = 9,
            SHLIB = 10,
            DYNSYM = 11,
            default = Pass,
        ),
        "flags" / ElfInt32,
        "addr" / ElfInt32,
        "offset" / ElfInt32,
        "size" / ElfInt32,
        "link" / ElfInt32,
        "info" / ElfInt32,
        "align" / ElfInt32,
        "entry_size" / ElfInt32,
        "data" / Pointer(this.offset, Bytes(this.size)),
    )
    
    return Struct(
        "type" / Enum(ElfInt16,
            NONE = 0,
            RELOCATABLE = 1,
            EXECUTABLE = 2,
            SHARED = 3,
            CORE = 4,
        ),
        "machine" / Enum(ElfInt16,
            NONE = 0,
            M32 = 1,
            SPARC = 2,
            I386 = 3,
            Motorolla68K = 4,
            Motorolla88K = 5,
            Intel860 = 7,
            MIPS = 8,
            default = Pass,
        ),
        "version"              / ElfInt32,
        "entry"                / ElfInt32,
        "ph_offset"            / ElfInt32,
        "sh_offset"            / ElfInt32,
        "flags"                / ElfInt32,
        "header_size"          / ElfInt16,
        "ph_entry_size"        / ElfInt16,
        "ph_count"             / ElfInt16,
        "sh_entry_size"        / ElfInt16,
        "sh_count"             / ElfInt16,
        "strtab_section_index" / ElfInt16,
        
        # calculate the string table data offset (pointer arithmetics)
        # ugh... anyway, we need it in order to read the section names, later on
        "strtab_data_offset" / Pointer(this.sh_offset + this.strtab_section_index * this.sh_entry_size + 16, ElfInt32),
        
        "program_table" / Pointer(this.ph_offset, elf32_program_header[this.ph_count]),
        
        "sections" / Pointer(this.sh_offset, elf32_section_header[this.sh_count]),
    )

elf32_file = Struct(
    "identifier" / Struct(
        Const(b"\x7fELF"),
        "file_class" / Enum(Byte,
            NONE = 0,
            CLASS32 = 1,
            CLASS64 = 2,
        ),
        "encoding" / Enum(Byte,
            NONE = 0,
            LSB = 1,
            MSB = 2,            
        ),
        "version" / Byte,
        Padding(9),
    ),
    "body" / IfThenElse(this.identifier.encoding == "LSB",
        elf32_body(Int16ul, Int32ul),
        elf32_body(Int16ub, Int32ub),
    ),
)
