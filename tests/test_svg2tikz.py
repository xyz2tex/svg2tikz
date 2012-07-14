# -*- coding: utf-8 -*-

import unittest

from svg2tikz.extensions.tikz_export import convert_file, convert_svg, parse_transform
from svg2tikz.extensions.tikz_export import TikZPathExporter

#from svg2tikz.extensions.tikz_export import GraphicsState
from lxml import etree
from cStringIO import StringIO


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
        code = convert_svg(paint_svg, codeoutput="codeonly")
        assert 'fill=red' in code


class TestTransformation(unittest.TestCase):

    def test_scientific_notation_bug(self):
        converter = TikZPathExporter(inkscape_mode=False)
        transform = "matrix(1,-0.43924987,0,1,-2.3578e-6,37.193992)"
        trans = parse_transform(transform)
        self.assertNotIn('e-06', converter._convert_transform_to_tikz(trans)[0])


#class TestGraphicsState(unittest.TestCase):
#    def test_basic(self):
#        doc = etree.parse(StringIO(paint_svg))
#        root = doc.getroot()
#        state = GraphicsState(root)
#        print state

if __name__ == '__main__':
    unittest.main()
