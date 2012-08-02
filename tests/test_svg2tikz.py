# -*- coding: utf-8 -*-

import unittest

from svg2tikz.extensions.tikz_export import  convert_svg, parse_transform
from svg2tikz.extensions.tikz_export import TikZPathExporter


basic_svg = r"""<?xml version="1.0" standalone="no"?>
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

basic2_svg = r"""<?xml version="1.0" standalone="no"?>
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
    def test_basicsvg(self):
        code = convert_svg(basic_svg)
        assert 'rect' in code

    def test_basic_codeonly(self):
        code = convert_svg(basic_svg, codeoutput="codeonly")
        assert 'documentclass' not in code
        assert r'\begin{tikzpicture}' not in code

    def test_basic_figonly(self):
        code = convert_svg(basic_svg, codeoutput="figonly")
        assert 'documentclass' not in code
        assert r'\begin{tikzpicture}' in code

    def test_no_ids(self):
        code = convert_svg(basic2_svg, ids=[], verbose=True)
        assert 'rect1' in code
        assert 'rect2' in code

    def test_select_id_rect1(self):
        code = convert_svg(basic2_svg, ids=['rect1'], verbose=True)
        assert 'rect1' in code
        assert 'rect2' not in code

    def test_select_id_rect1and3(self):
        code = convert_svg(basic2_svg, ids=['rect1', 'rect3'], verbose=True)
        assert 'rect1' in code
        assert 'rect2' not in code
        assert 'rect3' in code


paint_svg = r"""<?xml version="1.0" standalone="no"?>
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
    def test_inherited_fill(self):
        code = convert_svg(paint_svg)
        self.assertTrue('fill=red' in code)


class TestTransformation(unittest.TestCase):
    def test_exponential_notation_bug(self):
        converter = TikZPathExporter(inkscape_mode=False)
        transform = "matrix(1,-0.43924987,0,1,-2.3578e-6,37.193992)"
        trans1 = parse_transform(transform)
        self.assertFalse('e-06' in converter._convert_transform_to_tikz(trans1)[0])
        trans2 = parse_transform("translate(1e-6,0.03057816)")
        self.assertFalse('e-06' in converter._convert_transform_to_tikz(trans2)[0])


text_svg = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="10cm" height="3cm" viewBox="0 0 1000 300"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <desc>Example text01 - 'Hello, out there' in blue</desc>

  <text x="250" y="150">a%b</text>
</svg>"""

class TestTextMode(unittest.TestCase):
    def test_escape(self):
        code = convert_svg(text_svg, codeoutput="codeonly")
        self.assertTrue(r'a\%b' in code)
        code = convert_svg(text_svg, codeoutput="codeonly", texmode='escape')
        self.assertTrue(r'a\%b' in code)

    def test_raw(self):
        code = convert_svg(text_svg, codeoutput="codeonly", texmode='raw')
        self.assertTrue(r'a%b' in code)

    def test_math(self):
        code = convert_svg(text_svg, codeoutput="codeonly", texmode='math')
        self.assertTrue(r'$a%b$' in code)


no_height_svg = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
  <rect x=".01cm" y=".01cm" width="4.98cm" height="4.98cm"
        fill="none" stroke="blue" stroke-width=".02cm"/>
</svg>"""


class BugsTest(unittest.TestCase):
    def test_no_svgheight_error(self):
        code = convert_svg(no_height_svg)
        self.assertTrue('rectangle' in code)


defs_svg = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg viewBox = "0 0 1000 1000" version = "1.1">
    <defs>
        <!-- A circle of radius 200 -->
        <circle id = "s1" cx = "200" cy = "200" r = "200" fill = "yellow" stroke = "black" stroke-width = "3"/>
        <!-- An ellipse (rx=200,ry=150) -->
        <ellipse id = "s2" cx = "200" cy = "150" rx = "200" ry = "150" fill = "salmon" stroke = "black" stroke-width = "3"/>
    </defs>
    <use x = "100" y = "100" xlink:href="#s1"/>
    <use x = "100" y = "650" xlink:href="#s2"/>
</svg>"""

defs1_svg = r"""<?xml version="1.0" standalone="no"?>
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
    def test_no_used_defs(self):
        code = convert_svg(defs1_svg)
        self.assertTrue('circle' not in code)


arrows_svg = r"""<?xml version="1.0" standalone="no"?>
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

    def test_marker_options(self):
        code = convert_svg(arrows_svg, markers="ignore", codeoutput="codeonly")
        self.assertTrue('>' not in code)

    def test_marker2_options(self):
        code = convert_svg(arrows_svg, markers="arrows", codeoutput="codeonly")
        self.assertTrue('->' in code)


if __name__ == '__main__':
    unittest.main()
