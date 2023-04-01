# -*- coding: utf-8 -*-
"""Test all utily functions of svg2tikz"""
import unittest

import sys
import os

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz.extensions.tikz_export import calc_arc,Point


class TestGeometricalFunctions(unittest.TestCase):
    """Test all functions related to geometry from tikz_export"""

    def test_calc_arc(self):
        """Test arc computing"""
        """Value determined with visual aid"""

        cp = Point(2.0351807, 26.0215522)
        r_i = Point(3.7795276, 7.559055100000002)
        ang = 0.0
        fa = 0.0
        fs = 0.0
        pos = Point(1.5789307000000004, 22.428779199999997)
        start_ang_o, end_ang_o, r_o = calc_arc(cp, r_i ,ang, fa, fs ,pos)
        true_start_ang = -0.05758947401401947
        true_end_ang = -28.443965116484787
        true_r = Point(x=3.7795276, y=7.559055100000002)

        self.assertEqual(start_ang_o, true_start_ang)
        self.assertEqual(end_ang_o, true_end_ang)
        self.assertEqual(true_r, r_o)

        fa = 1.0
        start_ang_o, end_ang_o, r_o = calc_arc(cp, r_i ,ang, fa, fs ,pos)
        true_start_ang =151.55603488351522
        true_end_ang =-180.05758947401404
        true_r = Point(x=3.7795276, y=7.559055100000002)

        self.assertEqual(start_ang_o, true_start_ang)
        self.assertEqual(end_ang_o, true_end_ang)
        self.assertEqual(true_r, r_o)

        fs = 1.0
        start_ang_o, end_ang_o, r_o = calc_arc(cp, r_i ,ang, fa, fs ,pos)
        true_start_ang = -360.05758947401404
        true_end_ang = -28.443965116484787
        true_r = Point(x=3.7795276, y=7.559055100000002)

        self.assertEqual(start_ang_o, true_start_ang)
        self.assertEqual(end_ang_o, true_end_ang)
        self.assertEqual(true_r, r_o)





if __name__ == "__main__":
    unittest.main()
