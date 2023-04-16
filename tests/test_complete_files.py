# -*- coding: utf-8 -*-
"""Test top level functions of svg2tikz"""
import unittest

import sys
import os
import io

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz.extensions.tikz_export import convert_file


def create_test_from_filename(filename, utest):
    """
    Function to test the complete conversion with svg2tikz.
    The svg should be located in tests/testsfiles/XXX.svg
    The tex should be located in tests/testsfiles/XXX.tex
    """
    filepath_input = f"tests/testfiles/{filename}"
    filepath_output = f"tests/testdest/{filename}.tex"

    convert_file(f"{filepath_input}.svg", output=f"{filepath_output}")

    with io.open(f"{filepath_input}.tex", encoding="utf-8") as fi:
        with io.open(filepath_output, encoding="utf-8") as fo:
            utest.assertListEqual(
                list(fi),
                list(fo),
            )

    os.remove(filepath_output)


class TestCompleteFiles(unittest.TestCase):
    """Class test for complete SVG"""

    def test_pentagone_round_corner(self):
        """Test complete converte pentagone with round corner"""
        filename = "pentagone_round_corner"
        create_test_from_filename(filename, self)

    def test_three_rectangles_with_translation(self):
        """Test complete converte pentagone with round corner"""
        filename = "three_rectangles_with_translate"
        create_test_from_filename(filename, self)

    def test_four_basics_rectangles(self):
        """Test complete converte pentagone with round corner"""
        filename = "four_basics_rectangles"
        create_test_from_filename(filename, self)


if __name__ == "__main__":
    unittest.main()
