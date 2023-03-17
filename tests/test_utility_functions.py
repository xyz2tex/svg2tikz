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


_tex_charmap = dict(list(zip(SPECIAL_TEX_CHARS, SPECIAL_TEX_CHARS_REPLACE)))


def escape_texchars(input_string):
    pass

class TestUtilityFunctions(unittest.TestCase):
    """Test all utility functions from tikz_export"""
    def test_exscape_texchars(self):
        SPECIAL_TEX_CHARS = [
                ["$"],
                ["\\"],
                ["%"],
                ["_"],
                ["#"],
                ["{"],
                ["}"],
                ["^"],
                ["&"],
                ]
        SPECIAL_TEX_CHARS_REPLACE = [
            r"\$",
            r"$\backslash$",
            r"\%",
            r"\_",
            r"\#",
            r"\{",
            r"\}",
            r"\^{}",
            r"\&",
        ]


        self.assertTrue("Triangle" in gs2.marker[0])


if __name__ == "__main__":
    unittest.main()
