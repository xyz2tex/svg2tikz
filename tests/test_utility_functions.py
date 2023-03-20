# -*- coding: utf-8 -*-
"""Test all utily functions of svg2tikz"""
import unittest

import sys
import os
import io

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz.extensions.tikz_export import (
    escape_texchars,
    copy_to_clipboard,
    nsplit,
    chunks,
    open_anything,
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

    def test_copy_to_clipboard(self):
        """Test copy"""
        self.assertTrue(copy_to_clipboard(b"Test text"))

    def test_nsplit(self):
        """Test splitting"""
        self.assertEqual(nsplit("aabbcc"), [("a", "a"), ("b", "b"), ("c", "c")])
        self.assertEqual(
            nsplit("aabbcc", n_split=3), [("a", "a", "b"), ("b", "c", "c")]
        )
        self.assertEqual(nsplit("aabbcc", n_split=4), [("a", "a", "b", "b")])

    def test_chunks(self):
        """Test chunks"""
        for vals in zip(chunks("aabbcc", 2), ["aa", "bb", "cc"]):
            self.assertEqual(vals[0], vals[1])
        for vals in zip(chunks("aabbcc", 3), ["aab", "bcc"]):
            self.assertEqual(vals[0], vals[1])
        for vals in zip(chunks("aabbcc", 4), ["aabb", "cc"]):
            self.assertEqual(vals[0], vals[1])

    def test_open_anything(self):
        """Test to open files"""

        self.assertTrue(isinstance(open_anything("do_not_exist.txt"), io.StringIO))
        self.assertTrue(isinstance(open_anything("README.md"), io.StringIO))


if __name__ == "__main__":
    unittest.main()
