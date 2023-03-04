# -*- coding: utf-8 -*-
import unittest

try:
    # svg2tikz installed into system's python path?
    import svg2tikz
except ImportError:
    # if not, have a look into default directory
    import sys, os

    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")
    import svg2tikz


from svg2tikz.extensions.tikz_export import TikZPathExporter, GraphicsState

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
  <path id="pathA" d="M 1000 750 L 2000 750 L 2500 1250"
        fill="none" stroke="black" stroke-width="100"
        marker-end="url(#Triangle)"  />

 <path id="pathB" d="M 1000 750 L 2000 750 L 2500 1250"
        fill="none" stroke="black" stroke-width="100"
        marker-end="url(#Triangle)" marker-start="url(#Triangle)" />
</svg>"""


class TestGraphicsState(unittest.TestCase):
    def test_markers(self):
        tt = TikZPathExporter()
        tt.parse(arrows_svg)
        n = tt.get_node_from_id("pathA")
        gs = GraphicsState(n)

        self.assertTrue("Triangle" in gs.marker[2])
        self.assertTrue(gs.marker[0] is None)
        self.assertTrue(gs.marker[1] is None)
        gs2 = GraphicsState(tt.get_node_from_id("pathB"))
        self.assertTrue("Triangle" in gs2.marker[2])
        self.assertTrue("Triangle" in gs2.marker[0])


if __name__ == "__main__":
    unittest.main()
