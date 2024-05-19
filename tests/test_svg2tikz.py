# -*- coding: utf-8 -*-
"""Test top level functions of svg2tikz"""
import unittest

import sys
import os
from io import StringIO

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz import convert_file, convert_svg
from tests.common import (
    SVG_2_RECT,
    SVG_3_RECT,
    SVG_ARROW,
    SVG_TEXT_BLUE,
    SVG_DEFS,
    SVG_PAINT,
    SVG_NO_HEIGHT,
)


class InterfaceTest(unittest.TestCase):
    """Class test for all the interfaces"""

    def test_basicsvg(self):
        """Test converting simple svg"""
        code = convert_file(StringIO(SVG_2_RECT))
        assert "rect" in code

    def test_basic_codeonly(self):
        """Test converting basic svg with codeonly"""
        code = convert_file(StringIO(SVG_2_RECT), codeoutput="codeonly")
        assert "documentclass" not in code
        assert r"\begin{tikzpicture}" not in code

    def test_basic_figonly(self):
        """Test converting basic svg with figonly"""
        code = convert_file(StringIO(SVG_2_RECT), codeoutput="figonly")
        assert "documentclass" not in code
        assert r"\begin{tikzpicture}" in code

    def test_no_ids(self):
        """Test converting basic svg 2"""
        code = convert_file(StringIO(SVG_3_RECT), ids=[], verbose=True)
        assert "rect1" in code
        assert "rect2" in code

    def test_select_id_rect1(self):
        """Test converting basic svg 2 with selection"""
        code = convert_file(StringIO(SVG_3_RECT), ids=["rect1"], verbose=True)
        assert "rect1" in code
        assert "rect2" not in code

    def test_select_id_rect1and3(self):
        """Test converting basic svg 2 with multiple selection"""
        code = convert_file(StringIO(SVG_3_RECT), ids=["rect1", "rect3"], verbose=True)
        assert "rect1" in code
        assert "rect2" not in code
        assert "rect3" in code


class PaintingTest(unittest.TestCase):
    """Test class to test painting"""

    def test_inherited_fill(self):
        """Testing the inherited painting"""
        code = convert_file(StringIO(SVG_PAINT))
        self.assertTrue("fill=red" in code)


class TestTextMode(unittest.TestCase):
    """Class to test the texmode"""

    def test_escape(self):
        """Test the escape mode"""
        code = convert_file(StringIO(SVG_TEXT_BLUE), codeoutput="codeonly")
        self.assertTrue(r"a\%b" in code)
        code = convert_file(
            StringIO(SVG_TEXT_BLUE), codeoutput="codeonly", texmode="escape"
        )
        self.assertTrue(r"a\%b" in code)

    def test_raw(self):
        """Test the raw mode"""
        code = convert_file(
            StringIO(SVG_TEXT_BLUE), codeoutput="codeonly", texmode="raw"
        )
        self.assertTrue(r"a%b" in code)

    def test_math(self):
        """Test the math mode"""
        code = convert_file(
            StringIO(SVG_TEXT_BLUE), codeoutput="codeonly", texmode="math"
        )
        self.assertTrue(r"$a%b$" in code)

    def test_bad_textmode_option(self):
        """Test texmode option to attribute without texmode--attribute set"""
        print("hello")
        code = convert_file(
            StringIO(SVG_TEXT_BLUE), texmode="attribute", texmode_attribute=None
        )
        self.assertEqual(code, "")


class DifformSVGTest(unittest.TestCase):
    """Test class for limit case of SVG"""

    def test_no_svgheight_error(self):
        """Test with no height in the viewbox"""
        code = convert_file(StringIO(SVG_NO_HEIGHT))
        self.assertTrue("rectangle" in code)


class DefsTest(unittest.TestCase):
    """Test class for def property of SVG"""

    def test_no_used_defs(self):
        """Test when defs are not used"""
        code = convert_file(StringIO(SVG_DEFS))
        self.assertTrue("circle" not in code)


class MarkersTest(unittest.TestCase):
    """Test class for marker option"""

    def test_marker_options_ignore(self):
        """Test ignore option with marking"""
        code = convert_file(
            StringIO(SVG_ARROW), markings="ignore", codeoutput="codeonly"
        )
        self.assertTrue(">" not in code)

    def test_marker_options_arrows(self):
        """Test arrows option with marking"""
        code = convert_file(
            StringIO(SVG_ARROW), markings="arrows", arrow=">", codeoutput="codeonly"
        )
        self.assertTrue("->" in code, f'code="{code}"')


class CommandlineModule(unittest.TestCase):
    """
    Test class for the command line functions
    """

    def test_convert_svg_output_str(self):
        """Test of convert_svg"""

        code = convert_svg(
            SVG_ARROW, returnstring=True, codeoutput="codeonly", indent=False
        )
        truecode = r"""\path[draw=black,line width=0.254cm,->] (2.54, 3.175) -- (5.08, 3.175) -- (6.35, 1.905);



"""
        self.assertEqual(truecode, code)

    def test_convert_svg_output_stream(self):
        """Test of convert_svg"""

        output_stream = StringIO()
        convert_svg(
            SVG_ARROW,
            no_output=False,
            returnstring=False,
            codeoutput="codeonly",
            indent=False,
            output=output_stream,
        )

        truecode = r"""\path[draw=black,line width=0.254cm,->] (2.54, 3.175) -- (5.08, 3.175) -- (6.35, 1.905);



"""
        self.assertEqual(truecode, output_stream.getvalue())
        output_stream.close()

    def test_convert_svg_output_file(self):
        """Test of convert_svg"""

        filename = "tests/testdest/convert_svg_output_file"
        convert_svg(
            SVG_ARROW,
            no_output=False,
            returnstring=False,
            codeoutput="codeonly",
            indent=False,
            output=filename,
        )

        truecode = r"""\path[draw=black,line width=0.254cm,->] (2.54, 3.175) -- (5.08, 3.175) -- (6.35, 1.905);



"""
        with open(filename, "r", encoding="utf8") as f:
            self.assertEqual(truecode, f.read())

    def test_convert_file_output_str(self):
        """Test of convert_svg"""

        code = convert_file(
            StringIO(SVG_ARROW), returnstring=True, codeoutput="codeonly", indent=False
        )
        truecode = r"""\path[draw=black,line width=0.254cm,->] (2.54, 3.175) -- (5.08, 3.175) -- (6.35, 1.905);



"""
        self.assertEqual(truecode, code)

    def test_convert_file_output_stream(self):
        """Test of convert_svg"""

        output_stream = StringIO()
        convert_file(
            StringIO(SVG_ARROW),
            no_output=False,
            returnstring=False,
            codeoutput="codeonly",
            indent=False,
            output=output_stream,
        )

        truecode = r"""\path[draw=black,line width=0.254cm,->] (2.54, 3.175) -- (5.08, 3.175) -- (6.35, 1.905);



"""
        self.assertEqual(truecode, output_stream.getvalue())
        output_stream.close()

    def test_convert_file_output_file(self):
        """Test of convert_svg"""

        filename = "tests/testdest/convert_svg_output_file"
        convert_file(
            StringIO(SVG_ARROW),
            no_output=False,
            returnstring=False,
            codeoutput="codeonly",
            indent=False,
            output=filename,
        )

        truecode = r"""\path[draw=black,line width=0.254cm,->] (2.54, 3.175) -- (5.08, 3.175) -- (6.35, 1.905);



"""
        with open(filename, "r", encoding="utf8") as f:
            self.assertEqual(truecode, f.read())
