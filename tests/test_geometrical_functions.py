# -*- coding: utf-8 -*-
"""Test all utily functions of svg2tikz"""
import unittest

import sys
import os

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz.extensions.tikz_export import calc_arc


class TestGeometricalFunctions(unittest.TestCase):
    """Test all functions related to geometry from tikz_export"""

    def test_calc_arc(self):
        """Test arc computing"""
        # TODO
        self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()
