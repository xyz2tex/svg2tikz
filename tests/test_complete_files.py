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


def create_test_from_filename(filename, utest, **kwargs):
    """
    Function to test the complete conversion with svg2tikz.
    The svg should be located in tests/testsfiles/XXX.svg
    The tex should be located in tests/testsfiles/XXX.tex
    """
    filepath_input = f"tests/testfiles/{filename}"
    filepath_output = f"tests/testdest/{filename}.tex"

    convert_file(f"{filepath_input}.svg", output=f"{filepath_output}", **kwargs)

    with io.open(f"{filepath_input}.tex", encoding="utf-8") as fi:
        with io.open(filepath_output, encoding="utf-8") as fo:
            utest.assertListEqual(
                list(fi),
                list(fo),
            )

    os.remove(filepath_output)


class TestCompleteFiles(unittest.TestCase):
    """Class test for complete SVG"""

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

    def test_ellipse(self):
        """Test complete convert ellipse"""
        filename = "ellipse"
        create_test_from_filename(filename, self)

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

    def test_switch(self):
        """Test complete convert simple switch case"""
        filename = "switch_simple"
        create_test_from_filename(filename, self)

    def test_text_fill_color(self):
        """Test complete convert text with color case"""
        filename = "text_fill_color"
        create_test_from_filename(filename, self)


if __name__ == "__main__":
    unittest.main()
