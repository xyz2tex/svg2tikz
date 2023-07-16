# -*- coding: utf-8 -*-
"""Test all utily functions of svg2tikz"""
import unittest

import sys
import os

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz.tikz_export import (
    escape_texchars,
    copy_to_clipboard,
)


class TestUtilityFunctions(unittest.TestCase):
    """Test all utility functions from tikz_export"""

    def test_exscape_texchars(self):
        """Test escape texchars
        - Single char
        - Combinaison of chars
        """
        special_tex_chars = [
            ["$", r"\$"],
            ["\\", r"$\backslash$"],
            ["%", r"\%"],
            ["_", r"\_"],
            ["#", r"\#"],
            ["{", r"\{"],
            ["}", r"\}"],
            ["^", r"\^{}"],
            ["&", r"\&"],
            ["$#&{}", r"\$\#\&\{\}"],
        ]
        for symbols in special_tex_chars:
            self.assertEqual(symbols[1], escape_texchars(symbols[0]))

    @unittest.skip("cannot run in GH action")
    def test_copy_to_clipboard(self):
        """Test copy"""
        self.assertTrue(copy_to_clipboard(b"Test text"))


if __name__ == "__main__":
    unittest.main()
