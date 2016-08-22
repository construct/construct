import unittest

from construct.formats.graphics.png import png_file

class TestPngFormat(unittest.TestCase):

    def test_parse(self):
        with open('tests/sample.png','rb') as f:
            sample = png_file.parse(f.read())
            self.assertEqual(sample, Container({'chunks': [Container({'data': Container({'significant_alpha_bits': 8, 'significant_green_bits': 8, 'significant_red_bits': 8, 'significant_blue_bits': 8}), 'length': 4, 'type': 'sBIT', 'crc': 2080924808}), Container({'data': Container({'text': 'gnome-screenshot', 'keyword': 'Software'}), 'length': 25, 'type': 'tEXt', 'crc': 4010000190}), Container({'data': <construct.lib.container.LazyContainer object at 0x7ffb2034c418>, 'length': 8192, 'type': 'IDAT', 'crc': 1554473045}), Container({'data': <construct.lib.container.LazyContainer object at 0x7ffb2034c470>, 'length': 8192, 'type': 'IDAT', 'crc': 1490082961}), Container({'data': <construct.lib.container.LazyContainer object at 0x7ffb2034c4c8>, 'length': 8192, 'type': 'IDAT', 'crc': 4247891774}), Container({'data': <construct.lib.container.LazyContainer object at 0x7ffb2034c520>, 'length': 8192, 'type': 'IDAT', 'crc': 3667621403}), Container({'data': <construct.lib.container.LazyContainer object at 0x7ffb2034c578>, 'length': 7390, 'type': 'IDAT', 'crc': 1033426802}), Container({'data': None, 'length': 0, 'type': 'IEND', 'crc': 2923585666})], 'image_header': Container({'crc': 1278104008, 'color_type': 'truewithalpha', 'bit_depth': 8, 'height': 438, 'compression_method': 'deflate', 'width': 732, 'length': 13, 'filter_method': 'adaptive5', 'interlace_method': 'none'})})
