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

    def test_calc_arc(self):
        """Test arc angle and radius computation for various configurations.

        Notes
        -----
        Expected values were determined with visual aid.
        """
        V = inkex.transforms.Vector2d

        cases = [
            (
                "zero-length arc",
                {
                    "cp": V(3.0, 3.0),
                    "r_i": V(2.0, 2.0),
                    "ang": 0.0,
                    "fa": 0.0,
                    "fs": 0.0,
                    "pos": V(3.0, 3.0),
                },
                {
                    "start": 0,
                    "end": 0,
                    "r": V(2, 2),
                },
            ),
            (
                "elliptic arc fa=0 fs=0",
                {
                    "cp": V(3.0, 3.0),
                    "r_i": V(1.0, 2.0),
                    "ang": 0.0,
                    "fa": 0.0,
                    "fs": 0.0,
                    "pos": V(3.0, 11.0),
                },
                {
                    "start": -90,
                    "end": -270,
                    "r": V(2, 4),
                },
            ),
            (
                "real-world arc fa=0 fs=0",
                {
                    "cp": V(2.0351807, 26.0215522),
                    "r_i": V(3.7795276, 7.559055100000002),
                    "ang": 0.0,
                    "fa": 0.0,
                    "fs": 0.0,
                    "pos": V(1.5789307000000004, 22.428779199999997),
                },
                {
                    "start": -0.05758947401401947,
                    "end": -28.443965116484787,
                    "r": V(3.7795276, 7.559055100000002),
                },
            ),
            (
                "real-world arc fa=1 fs=0",
                {
                    "cp": V(2.0351807, 26.0215522),
                    "r_i": V(3.7795276, 7.559055100000002),
                    "ang": 0.0,
                    "fa": 1.0,
                    "fs": 0.0,
                    "pos": V(1.5789307000000004, 22.428779199999997),
                },
                {
                    "start": 151.55603488351522,
                    "end": -180.05758947401404,
                    "r": V(3.7795276, 7.559055100000002),
                },
            ),
            (
                "real-world arc fa=1 fs=1",
                {
                    "cp": V(2.0351807, 26.0215522),
                    "r_i": V(3.7795276, 7.559055100000002),
                    "ang": 0.0,
                    "fa": 1.0,
                    "fs": 1.0,
                    "pos": V(1.5789307000000004, 22.428779199999997),
                },
                {
                    "start": -360.05758947401404,
                    "end": -28.443965116484787,
                    "r": V(3.7795276, 7.559055100000002),
                },
            ),
        ]

        for label, inputs, expected in cases:
            with self.subTest(label):
                start, end, r = calc_arc(
                    inputs["cp"],
                    inputs["r_i"],
                    inputs["ang"],
                    inputs["fa"],
                    inputs["fs"],
                    inputs["pos"],
                )
                self.assertEqual(start, expected["start"])
                self.assertEqual(end, expected["end"])
                self.assertEqual(r.x, expected["r"].x)
                self.assertEqual(r.y, expected["r"].y)
