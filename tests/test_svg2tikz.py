# -*- coding: utf-8 -*-

import unittest

from svg2tikz.extensions.tikz_export import convert_file


basic_svg = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <desc>Example rect01 - rectangle with sharp corners</desc>
  <!-- Show outline of canvas using 'rect' element -->
  <rect x="1" y="1" width="1198" height="398"
        fill="none" stroke="blue" stroke-width="2"/>
  <rect x="400" y="100" width="400" height="200"
        fill="yellow" stroke="navy" stroke-width="10"  />
</svg>
"""

class InterfaceTest(unittest.TestCase):
    
    def test_basicsvg(self):
        code = convert_file(basic_svg)
        self.failUnless('rect' in code)
    def test_basic_codeonly(self):
        code = convert_file(svg_file=basic_svg, codeoutput="codeonly")
        self.failIf('documentclass' in code)


if __name__ == '__main__':
    unittest.main()
