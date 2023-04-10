# -*- coding: utf-8 -*-
"""Test top level functions of svg2tikz"""
import unittest

import sys
import os

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz.extensions.tikz_export import convert_svg

BASIC_SVG = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <desc>Example rect01 - rectangle with sharp corners</desc>
  <!-- Show outline of canvas using 'rect' element -->
  <rect x="1" y="1" width="1198" height="398" id="rect1"
        fill="none" stroke="blue" stroke-width="2"/>
  <rect x="400" y="100" width="400" height="200" id="rect2"
        fill="yellow" stroke="navy" stroke-width="10"  />
</svg>
"""

BASIC_SVG_2 = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <desc>Example rect01 - rectangle with sharp corners</desc>
  <!-- Show outline of canvas using 'rect' element -->
  <rect x="1" y="1" width="1198" height="398" id="rect1"
        fill="none" stroke="blue" stroke-width="2"/>
  <rect x="400" y="100" width="400" height="200" id="rect2"
        fill="yellow" stroke="navy" stroke-width="10"  />
  <rect x="400" y="100" width="400" height="200" id="rect3"
        fill="none" stroke="green" stroke-width="10"  />
</svg>
"""


class InterfaceTest(unittest.TestCase):
    """Class test for all the interfaces"""

    def test_basicsvg(self):
        """Test converting simple svg"""
        code = convert_svg(BASIC_SVG)
        assert "rect" in code

    def test_basic_codeonly(self):
        """Test converting basic svg with codeonly"""
        code = convert_svg(BASIC_SVG, codeoutput="codeonly")
        assert "documentclass" not in code
        assert r"\begin{tikzpicture}" not in code

    def test_basic_figonly(self):
        """Test converting basic svg with figonly"""
        code = convert_svg(BASIC_SVG, codeoutput="figonly")
        assert "documentclass" not in code
        assert r"\begin{tikzpicture}" in code

    def test_no_ids(self):
        """Test converting basic svg 2"""
        code = convert_svg(BASIC_SVG_2, ids=[], verbose=True)
        assert "rect1" in code
        assert "rect2" in code

    def test_select_id_rect1(self):
        """Test converting basic svg 2 with selection"""
        code = convert_svg(BASIC_SVG_2, ids=["rect1"], verbose=True)
        assert "rect1" in code
        assert "rect2" not in code

    def test_select_id_rect1and3(self):
        """Test converting basic svg 2 with multiple selection"""
        code = convert_svg(BASIC_SVG_2, ids=["rect1", "rect3"], verbose=True)
        assert "rect1" in code
        assert "rect2" not in code
        assert "rect3" in code


PAINT_SVG = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1"
     fill="red">
  <desc>Example rect01 - rectangle with sharp corners</desc>
  <!-- Show outline of canvas using 'rect' element -->
  <rect x="1" y="1" width="1198" height="398"
     stroke="blue" stroke-width="2"/>
</svg>
"""


class PaintingTest(unittest.TestCase):
    """Test class to test painting"""

    def test_inherited_fill(self):
        """Testing the inherited painting"""
        code = convert_svg(PAINT_SVG)
        self.assertTrue("fill=red" in code)


TEXT_SVG = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="10cm" height="3cm" viewBox="0 0 1000 300"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <desc>Example text01 - 'Hello, out there' in blue</desc>

  <text x="250" y="150">a%b</text>
</svg>"""


class TestTextMode(unittest.TestCase):
    """Class to test the texmode"""

    def test_escape(self):
        """Test the escape mode"""
        code = convert_svg(TEXT_SVG, codeoutput="codeonly")
        self.assertTrue(r"a\%b" in code)
        code = convert_svg(TEXT_SVG, codeoutput="codeonly", texmode="escape")
        self.assertTrue(r"a\%b" in code)

    def test_raw(self):
        """Test the raw mode"""
        code = convert_svg(TEXT_SVG, codeoutput="codeonly", texmode="raw")
        self.assertTrue(r"a%b" in code)

    def test_math(self):
        """Test the math mode"""
        code = convert_svg(TEXT_SVG, codeoutput="codeonly", texmode="math")
        self.assertTrue(r"$a%b$" in code)


NO_HEIGHT_SVG = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
  <rect x=".01cm" y=".01cm" width="4.98cm" height="4.98cm"
        fill="none" stroke="blue" stroke-width=".02cm"/>
</svg>"""


class DifformSVGTest(unittest.TestCase):
    """Test class for limit case of SVG"""

    def test_no_svgheight_error(self):
        """Test with no height in the viewbox"""
        code = convert_svg(NO_HEIGHT_SVG)
        self.assertTrue("rectangle" in code)


DEFS_SVG = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="10cm" height="3cm" viewBox="0 0 100 30" version="1.1"
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <desc>Example Use01 - Simple case of 'use' on a 'rect'</desc>
  <defs>
    <rect id="MyRect" width="60" height="10"/>
        <circle id = "s1" cx = "200" cy = "200" r = "200" fill = "yellow" stroke = "black" stroke-width = "3"/>
        <ellipse id = "s2" cx = "200" cy = "150" rx = "200" ry = "150" fill = "salmon" stroke = "black" stroke-width = "3"/>
  </defs>
  <rect x=".1" y=".1" width="99.8" height="29.8"
        fill="none" stroke="blue" stroke-width=".2" />
  <use x="20" y="10" xlink:href="#MyRect" />
</svg>"""


class DefsTest(unittest.TestCase):
    """Test class for def property of SVG"""

    def test_no_used_defs(self):
        """Test when defs are not used"""
        code = convert_svg(DEFS_SVG)
        self.assertTrue("circle" not in code)


ARROWS_SVG = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="4in" height="2in"
     viewBox="0 0 4000 2000" version="1.1"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="Triangle"
      viewBox="0 0 10 10" refX="0" refY="5"
      markerUnits="strokeWidth"
      markerWidth="4" markerHeight="3"
      orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" />
    </marker>
  </defs>
  <path d="M 1000 750 L 2000 750 L 2500 1250"
        fill="none" stroke="black" stroke-width="100"
        marker-end="url(#Triangle)"  />
</svg>"""


class MarkersTest(unittest.TestCase):
    """Test class for marker option"""

    def test_marker_options_ignore(self):
        """Test ignore option with marking"""
        code = convert_svg(ARROWS_SVG, markings="ignore", codeoutput="codeonly")
        self.assertTrue(">" not in code)

    def test_marker_options_arrows(self):
        """Test arrows option with marking"""
        code = convert_svg(
            ARROWS_SVG, markings="arrows", arrow=">", codeoutput="codeonly"
        )
        self.assertTrue("->" in code, f'code="{code}"')


if __name__ == "__main__":
    unittest.main()
