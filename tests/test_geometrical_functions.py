# -*- coding: utf-8 -*-
"""Test all geometrical functions of svg2tikz"""
import unittest

import sys
import os

import inkex

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz.tikz_export import calc_arc


# pylint: disable=too-many-public-methods
class TestGeometricalFunctions(unittest.TestCase):
    """Test all functions related to geometry from tikz_export"""

    # pylint: disable=too-many-statements
    def test_calc_arc(self):
        """Test arc computing

        Value determined with visual aid"""

        cp = inkex.transforms.Vector2d(3.0, 3.0)
        r_i = inkex.transforms.Vector2d(2.0, 2.0)
        ang = 0.0
        fa = 0.0
        fs = 0.0
        pos = inkex.transforms.Vector2d(3.0, 3.0)
        start_ang_o, end_ang_o, r_o = calc_arc(cp, r_i, ang, fa, fs, pos)
        true_start_ang = 0
        true_end_ang = 0
        true_r = inkex.transforms.Vector2d(2, 2)
        self.assertEqual(start_ang_o, true_start_ang)
        self.assertEqual(end_ang_o, true_end_ang)
        self.assertEqual(true_r.x, r_o.x)
        self.assertEqual(true_r.y, r_o.y)

        cp = inkex.transforms.Vector2d(3.0, 3.0)
        r_i = inkex.transforms.Vector2d(1.0, 2.0)
        ang = 0.0
        fa = 0.0
        fs = 0.0
        pos = inkex.transforms.Vector2d(3.0, 11.0)
        start_ang_o, end_ang_o, r_o = calc_arc(cp, r_i, ang, fa, fs, pos)
        true_start_ang = -90
        true_end_ang = -270
        true_r = inkex.transforms.Vector2d(2, 4)

        self.assertEqual(start_ang_o, true_start_ang)
        self.assertEqual(end_ang_o, true_end_ang)
        self.assertEqual(true_r.x, r_o.x)
        self.assertEqual(true_r.y, r_o.y)

        cp = inkex.transforms.Vector2d(2.0351807, 26.0215522)
        r_i = inkex.transforms.Vector2d(3.7795276, 7.559055100000002)
        ang = 0.0
        fa = 0.0
        fs = 0.0
        pos = inkex.transforms.Vector2d(1.5789307000000004, 22.428779199999997)
        start_ang_o, end_ang_o, r_o = calc_arc(cp, r_i, ang, fa, fs, pos)
        true_start_ang = -0.05758947401401947
        true_end_ang = -28.443965116484787
        true_r = inkex.transforms.Vector2d(3.7795276, 7.559055100000002)

        self.assertEqual(start_ang_o, true_start_ang)
        self.assertEqual(end_ang_o, true_end_ang)
        self.assertEqual(true_r.x, r_o.x)
        self.assertEqual(true_r.y, r_o.y)

        fa = 1.0
        start_ang_o, end_ang_o, r_o = calc_arc(cp, r_i, ang, fa, fs, pos)
        true_start_ang = 151.55603488351522
        true_end_ang = -180.05758947401404
        true_r = inkex.transforms.Vector2d(3.7795276, 7.559055100000002)

        self.assertEqual(start_ang_o, true_start_ang)
        self.assertEqual(end_ang_o, true_end_ang)
        self.assertEqual(true_r.x, r_o.x)
        self.assertEqual(true_r.y, r_o.y)

        fs = 1.0
        start_ang_o, end_ang_o, r_o = calc_arc(cp, r_i, ang, fa, fs, pos)
        true_start_ang = -360.05758947401404
        true_end_ang = -28.443965116484787
        true_r = inkex.transforms.Vector2d(3.7795276, 7.559055100000002)

        self.assertEqual(start_ang_o, true_start_ang)
        self.assertEqual(end_ang_o, true_end_ang)
        self.assertEqual(true_r.x, r_o.x)
        self.assertEqual(true_r.y, r_o.y)
