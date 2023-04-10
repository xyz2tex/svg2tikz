# -*- coding: utf-8 -*-
"""Test class GraphicsState of svg2tikz"""
import unittest

import sys
import os

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz.extensions.tikz_export import TikZPathExporter, GraphicsState

SVG = r"""<?xml version="1.0" standalone="no"?>
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
        fill="none" stroke="black" stroke-width="100" color="red" opacity="0.8"
        transform="translate(-9.08294, -40.2406)"
        marker-end="url(#Triangle)"  />

 <path id="pathB" d="M 1000 750 L 2000 750 L 2500 1250"
        fill="none" stroke="blue" stroke-width="50"
        marker-end="url(#Triangle)" marker-start="url(#Triangle)" />
</svg>"""


class TestGraphicsState(unittest.TestCase):
    """Test the class GraphicsState"""

    def test_markers(self):
        """Test the fetching of markers"""
        tt = TikZPathExporter()
        tt.parse(SVG)
        n = tt.get_node_from_id("pathA")
        gs = GraphicsState(n)

        self.assertTrue("Triangle" in gs.marker[2])
        self.assertTrue(gs.marker[0] is None)
        self.assertTrue(gs.marker[1] is None)
        gs2 = GraphicsState(tt.get_node_from_id("pathB"))
        self.assertTrue("Triangle" in gs2.marker[2])
        self.assertTrue("Triangle" in gs2.marker[0])

    def test_get_graphic_state(self):
        """Test get_graphics_state"""
        tt = TikZPathExporter()
        tt.parse(SVG)
        n = tt.get_node_from_id("pathA")

        # _get_graphic_state is tested here
        gs = GraphicsState(n)
        self.assertEqual(gs.fill, {"fill": "none"})
        self.assertEqual(gs.stroke, {"stroke": "black", "stroke-width": "100"})
        self.assertTrue(gs.is_visible)
        self.assertEqual(gs.transform, [["translate", (-9.08294, -40.2406)]])
        self.assertEqual(gs.color, "red")
        self.assertEqual(gs.opacity, "0.8")

    def test_get_parent_states(self):
        """Test _get_parent_states"""
        tt = TikZPathExporter()
        tt.parse(SVG)
        n = tt.get_node_from_id("pathA")

        gs = GraphicsState(n)
        self.assertEqual(gs.parent_states, None)

    def test_accumulate(self):
        """Test accumulate"""

        tt = TikZPathExporter()
        tt.parse(SVG)

        gs_a = GraphicsState(tt.get_node_from_id("pathA"))
        gs_b = GraphicsState(tt.get_node_from_id("pathB"))
        gs_c = gs_a.accumulate(gs_b)

        self.assertEqual(gs_c.fill, {})
        self.assertEqual(gs_c.stroke, {"stroke": "blue", "stroke-width": "50"})
        self.assertTrue(gs_c.is_visible)
        self.assertEqual(gs_c.transform, [["translate", (-9.08294, -40.2406)]])
        self.assertEqual(gs_c.color, None)
        self.assertEqual(gs_c.opacity, "0.8")


if __name__ == "__main__":
    unittest.main()
