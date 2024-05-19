# -*- coding: utf-8 -*-
"""Test all functions to parsing of svg2tikz"""
import unittest

import sys
import os

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position

from svg2tikz.tikz_export import (
    parse_arrow_style,
    marking_interpret,
)


class TestParseArrow(unittest.TestCase):
    """Test arrow parsing"""

    def test_parse_arrow_style(self):
        """Test parse_arrow_style function"""
        for input_arrow, output_arrow in zip(
            ["Arrow1", "Arrow2", "Stop", "Triangle"], ["latex", "stealth", "|", "latex"]
        ):
            for pos in ["start", "end"]:
                input_arrow_style = f'marker-{pos}=url"(#{input_arrow})"'
                output_arrow_style = parse_arrow_style(input_arrow_style)
                self.assertEqual(output_arrow, output_arrow_style)

    def test_marking_interpret(self):
        """Test marking interprite function"""
        for input_arrow, output_arrow in zip(
            ["Arrow1", "Arrow2", "Stop", "Triangle"], ["latex", "stealth", "|", "latex"]
        ):
            for pos, post in zip(["start", "end"], ["", " reversed"]):
                input_arrow_style = f'marker-{pos}=url"(#{input_arrow})"'
                output_arrow_style = marking_interpret(input_arrow_style)
                self.assertEqual(output_arrow + post, output_arrow_style)
