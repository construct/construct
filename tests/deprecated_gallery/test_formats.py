from tests.declarativeunittest import *
from construct import *
from construct.lib import *

from deprecated_gallery import  *


def test_png():
    commondumpdeprecated(png_file, "sample.png")

def test_emf():
    commondumpdeprecated(emf_file, "emf1.emf")

def test_bitmap():
    commondumpdeprecated(bitmap_file, "bitmap1.bmp")
    commondumpdeprecated(bitmap_file, "bitmap4.bmp")
    commondumpdeprecated(bitmap_file, "bitmap8.bmp")
    commondumpdeprecated(bitmap_file, "bitmap24.bmp")

def test_wmf():
    commondumpdeprecated(wmf_file, "wmf1.wmf")

def test_gif():
    commondumpdeprecated(gif_file, "sample.gif")

def test_mbr():
    commondumpdeprecated(mbr_format, "mbr1")

def test_cap():
    commondumpdeprecated(cap_file, "cap2.cap")

def test_snoop():
    commondumpdeprecated(snoop_file, "snoop1")

def test_pe32():
    commondumpdeprecated(pe32_file, "python.exe")
    commondumpdeprecated(pe32_file, "NOTEPAD.EXE")
    commondumpdeprecated(pe32_file, "sqlite3.dll")

def test_elf32():
    commondumpdeprecated(elf32_file, "ctypes.so")
