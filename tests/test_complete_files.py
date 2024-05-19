# -*- coding: utf-8 -*-
"""Test top level functions of svg2tikz"""
import unittest

import sys
import os
import io

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz import convert_file


# pylint: disable=too-many-public-methods
def create_test_from_filename(filename, utest, filename_output=None, **kwargs):
    """
    Function to test the complete conversion with svg2tikz.
    The svg should be located in tests/testsfiles/XXX.svg
    The tex should be located in tests/testsfiles/XXX.tex
    """
    filepath_input = f"tests/testfiles/{filename}"
    filepath_output = f"tests/testdest/{filename}.tex"

    if filename_output is None:
        filepath_test = f"{filepath_input}.tex"
    else:
        filepath_test = f"tests/testfiles/{filename_output}.tex"

    convert_file(f"{filepath_input}.svg", output=filepath_output, **kwargs)

    with io.open(filepath_test, encoding="utf-8") as fi:
        with io.open(filepath_output, encoding="utf-8") as fo:
            utest.assertListEqual(
                list(fi),
                list(fo),
            )

    os.remove(filepath_output)


class TestCompleteFiles(unittest.TestCase):
    """Class test for complete SVG"""

    def test_crop(self):
        """Test convert with crop"""
        filename = "crop"
        create_test_from_filename(filename, self, crop=True)

    def test_line_shape(self):
        """Test complete convert line tag"""
        filename = "line"
        create_test_from_filename(filename, self, markings="interpret")

    def test_linestyle(self):
        """Test complete convert line with different style"""
        filename = "lines_style"
        create_test_from_filename(filename, self, markings="interpret")

    def test_rectangle(self):
        """Test complete convert rectangle"""
        filename = "rectangle"
        create_test_from_filename(filename, self)

    def test_circle(self):
        """Test complete convert circle"""
        filename = "circle"
        create_test_from_filename(filename, self)

    def test_circle_verbose(self):
        """Test complete convert circle"""
        filename = "circle_verbose"
        create_test_from_filename(filename, self, verbose=True)

    def test_ellipse(self):
        """Test complete convert ellipse"""
        filename = "ellipse"
        create_test_from_filename(filename, self)
        create_test_from_filename(
            filename, self, noreversey=True, filename_output="ellipse_noreversey"
        )

    def test_polylines_polygones(self):
        """Test complete convert polylines and polygones"""
        filename = "polylines_polygones"
        create_test_from_filename(filename, self)

    def test_pentagone_round_corner(self):
        """Test complete convert pentagone with round corner"""
        filename = "pentagone_round_corner"
        create_test_from_filename(filename, self)

    def test_curves(self):
        """Test curve C and Q"""
        filename = "curves"
        create_test_from_filename(filename, self)

    def test_display_none_in_groups(self):
        """Test complete convert with none display"""
        filename = "display_none_in_group"
        create_test_from_filename(filename, self)

    def test_display_blocs_and_groups(self):
        """Test complete convert blocs and groups"""
        filename = "blocs_and_groups"
        create_test_from_filename(filename, self)

    def test_transforms(self):
        """Test complete convert transform"""
        filename = "transform"
        create_test_from_filename(filename, self)
        create_test_from_filename(
            filename, self, filename_output="transform_noreversey", noreversey=True
        )

    def test_image(self):
        """Test complete convert image"""
        filename = "image"
        create_test_from_filename(filename, self)

    def test_symbol_and_use(self):
        """Test complete convert symbol and use"""
        filename = "symbol_and_use"
        create_test_from_filename(filename, self)

    def test_text(self):
        """Test complete convert text"""
        filename = "text"
        create_test_from_filename(filename, self)
        create_test_from_filename(
            filename, self, filename_output="text_noreversey", noreversey=True
        )

    def test_switch(self):
        """Test complete convert simple switch case"""
        filename = "switch_simple"
        create_test_from_filename(
            filename, self, filename_output="switch_simple_noverbose"
        )
        create_test_from_filename(
            filename, self, verbose=True, filename_output="switch_simple_verbose"
        )

    def test_text_fill_color(self):
        """Test complete convert text with color case"""
        filename = "text_fill_color"
        create_test_from_filename(filename, self)

    def test_wrap(self):
        """Test complete convert wrap option"""
        filename = "rectangle_wrap"
        create_test_from_filename(filename, self, wrap=True)

    def test_nodes_and_transform(self):
        """Test complete convert transformation on nodes"""
        filename = "nodes_and_transform"
        create_test_from_filename(filename, self)

    def test_attribute_texmode(self):
        """Test per SVG object texmode with attribute"""
        filename = "attribute_texmode"
        create_test_from_filename(
            filename, self, texmode="attribute", texmode_attribute="data-texmode"
        )


if __name__ == "__main__":
    unittest.main()
