# -*- coding: utf-8 -*-
"""Test TikZPathExporter class"""
import unittest

import sys
import os
from io import StringIO

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from svg2tikz.extensions.tikz_export import TikZPathExporter
from tests.common import SVG_4_RECT, SVG_EMPTY, SVG_TEXT


class TestTikZPathExporter(unittest.TestCase):
    """Test all functions related to geometry from tikz_export"""

    def test_convert_unit(self):
        """Test converting between units"""
        tzpe = TikZPathExporter(inkscape_mode=False)

        units = {
            "in": 96.0,
            "pt": 1.3333333333333333,
            "px": 1.0,
            "mm": 3.779527559055118,
            "cm": 37.79527559055118,
            "m": 3779.527559055118,
            "km": 3779527.559055118,
            "Q": 0.94488188976378,
            "pc": 16.0,
        }

        for inp, val_i in units.items():
            tzpe.options.input_unit = inp
            for out, val_o in units.items():
                tzpe.options.output_unit = out
                conv = tzpe.convert_unit(1)

                self.assertEqual(conv, val_i / val_o)

    def test_height(self):
        """Test converting between units"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.options.noreversey = False

        for i in range(10):
            tzpe.height = 10 + i  # Set a height value
            for j in range(10):
                true_val = 10 + i - j
                test_val = tzpe.update_height(j)
                self.assertEqual(true_val, test_val)

        tzpe.options.noreversey = True
        for i in range(10):
            tzpe.height = 10 + i  # Set a height value
            for j in range(10):
                true_val = j
                test_val = tzpe.update_height(j)
                self.assertEqual(true_val, test_val)


    def test_get_node_form_id(self):
        """Test converting between units"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.convert(StringIO(SVG_4_RECT), no_output=True,returnstring=True)

        self.assertEqual(None, tzpe.get_node_from_id("Not_an_id"))
        ids = ["rect1", "rect2", "rect3"]

        for a in ids:
            self.assertEqual(a, tzpe.get_node_from_id(a).get("id", ""))

    def test_get_color(self):
        """Test getting color"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.convert(StringIO(SVG_4_RECT), no_output=True,returnstring=True)
        self.assertEqual(["blue", "navy", "yellow", "green"], tzpe.colors)
        # self.assertEqual("red", tzpe.get_color("red"))
        # self.assertEqual("black", tzpe.get_color("r"))  # r is not a valid color

        # It should not be added to list of color
        # self.assertEqual(
            # {
                # "red": "red",
            # },
            # tzpe.colors,
        # )

        # self.assertEqual(
            # "cffffff", tzpe.get_color("rgb(255,255,255)")
        # )  # r is not a valid color
        # self.assertEqual({"red": "red", "rgb(255,255,255)": "cffffff"}, tzpe.colors)


    def test_get_text(self):
        """Return content of a text node as string"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.convert(StringIO(SVG_TEXT), no_output=True,returnstring=True)
        test_text = tzpe.get_text(tzpe.get_node_from_id("textNode"))
        true_text = "Test Text\n"
        self.assertEqual(true_text, test_text)

    def test_effect(self):
        """Test effect function"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.convert(StringIO(SVG_EMPTY), no_output=True,returnstring=True)
        tzpe.options.output_unit = "mm"
        tzpe.options.input_unit = "cm"
        tzpe.options.noreversey = False
        tzpe.options.scale = 0.8
        tzpe.options.wrap = True
        tzpe.options.indent = True
        tzpe.options.verbose = False
        tzpe.options.codeoutput = "standalone"
        tzpe.options.crop = False
        tzpe.options.returnstring = False
        tzpe.effect()

        true_path = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{tikz}

\begin{document}


\def \globalscale {0.800000}
\begin{tikzpicture}[y=1mm, x=1mm, yscale=\globalscale,xscale=\globalscale, inner sep=0pt, outer sep=0pt]

\end{tikzpicture}
\end{document}
"""
        test_path = tzpe.output_code
        self.assertEqual(test_path, true_path)

    def test_save_raw(self):
        """Test raw saving"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.convert(StringIO(SVG_4_RECT), no_output=True,returnstring=True)
        tzpe.output_code = "Test save"
        tzpe.options.clipboard = False
        tzpe.options.mode = "effect"
        tzpe.options.output = "tests/testdest/output.tex"
        tzpe.save_raw(None)

        with open(tzpe.options.output, "r", encoding="utf8") as f:
            self.assertEqual(f.readline(), "Test save")

        os.remove(tzpe.options.output)

    def test_convert(self):
        """Test convert svg to tikz"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        true_path = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{tikz}

\begin{document}
\definecolor{blue}{RGB}{0,0,255}
\definecolor{navy}{RGB}{0,0,128}
\definecolor{yellow}{RGB}{255,255,0}
\definecolor{green}{RGB}{0,128,0}


\def \globalscale {1.000000}
\begin{tikzpicture}[y=1cm, x=1cm, yscale=\globalscale,xscale=\globalscale, inner sep=0pt, outer sep=0pt]
  \path[draw=blue,line width=0.200cm] (0.1, 3.9) rectangle (119.9, -35.9);



  \path[draw=navy,fill=yellow,line width=1.000cm] (40.0, -6.0) rectangle (80.0, -26.0);



  \path[draw=green,line width=1.000cm] (40.0, -6.0) rectangle (80.0, -26.0);



  \path[draw=green,line width=1.000cm] (40.0, -6.0) rectangle (80.0, -26.0);




\end{tikzpicture}
\end{document}
"""
        test_path = tzpe.convert(StringIO(SVG_4_RECT), no_output=True,returnstring=True)
        self.assertEqual(test_path, true_path)


if __name__ == "__main__":
    unittest.main()
