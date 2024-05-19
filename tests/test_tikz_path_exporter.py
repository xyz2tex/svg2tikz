# -*- coding: utf-8 -*-
"""Test TikZPathExporter class"""
import unittest

import sys
import os
from io import StringIO

# Use local svg2tikz version
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")

# pylint: disable=wrong-import-position
from inkex.transforms import Vector2d
from svg2tikz.tikz_export import TikZPathExporter
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
            for out, val_o in units.items():
                tzpe.options.output_unit = out
                conv = tzpe.convert_unit(f"{val_o}{inp}")
                self.assertTrue(abs(conv - val_i) < 1e-5)

    def test_convert_unit_coord(self):
        """Test converting between unit coordinate"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.height = 5
        tzpe.options.output_unit = "px"
        tzpe.options.noreversey = True

        coord = Vector2d(5, 5)
        output_coord = tzpe.convert_unit_coord(coord)
        self.assertTupleEqual((coord.x, coord.y), (output_coord.x, output_coord.y))

        tzpe.options.noreversey = False
        output_coord = tzpe.convert_unit_coord(coord, False)
        self.assertTupleEqual((coord.x, coord.y), (output_coord.x, output_coord.y))

        output_coord = tzpe.convert_unit_coord(coord, True)
        self.assertTupleEqual(
            (coord.x, tzpe.height - coord.y), (output_coord.x, output_coord.y)
        )

    def test_convert_unit_coords(self):
        """Test converting between unit coordinates"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.height = 5
        tzpe.options.output_unit = "px"
        tzpe.options.noreversey = True

        coords = [Vector2d(1, 1), Vector2d(2, 2), Vector2d(3, 3)]
        output_coords = tzpe.convert_unit_coords(coords)
        for coord, output_coord in zip(coords, output_coords):
            self.assertTupleEqual((coord.x, coord.y), (output_coord.x, output_coord.y))

        tzpe.options.noreversey = False
        output_coords = tzpe.convert_unit_coords(coords, False)
        for coord, output_coord in zip(coords, output_coords):
            self.assertTupleEqual((coord.x, coord.y), (output_coord.x, output_coord.y))

        output_coords = tzpe.convert_unit_coords(coords, True)
        for coord, output_coord in zip(coords, output_coords):
            self.assertTupleEqual(
                (coord.x, tzpe.height - coord.y), (output_coord.x, output_coord.y)
            )

    def test_round_value(self):
        """Test rounding a value"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        number = 0.123456789
        tzpe.options.round_number = 1
        self.assertEqual(tzpe.round_value(number), 0.1)
        tzpe.options.round_number = 2
        self.assertEqual(tzpe.round_value(number), 0.12)
        tzpe.options.round_number = 3
        self.assertEqual(tzpe.round_value(number), 0.123)

    def test_round_coord(self):
        """Test rounding a coordinate"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        coord = Vector2d(0.123456789, 0.123456789)

        tzpe.options.round_number = 1
        output_coord = tzpe.round_coord(coord)
        self.assertEqual(output_coord.x, 0.1)

    def test_round_coords(self):
        """Test rounding a coordinates"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        coord = Vector2d(0.123456789, 0.123456789)
        coords = [coord, coord]

        tzpe.options.round_number = 1
        output_coords = tzpe.round_coords(coords)
        self.assertEqual(output_coords[1].x, 0.1)

    def test_coord_to_tz(self):
        """Test rounding and converting a coordinate to tz format"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        coord = Vector2d(0.123456789, 0.123456789)
        tzpe.options.round_number = 1
        self.assertEqual(tzpe.coord_to_tz(coord), "(0.1, 0.1)")

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

    def test_get_color(self):
        """Test getting color"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.convert(StringIO(SVG_4_RECT), no_output=True, returnstring=True)
        self.assertEqual(["navy"], tzpe.colors)
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
        tzpe.convert(StringIO(SVG_TEXT), no_output=True, returnstring=True)
        test_text = tzpe.get_text(tzpe.svg.getElementById("textNode"))
        true_text = "Test Text\n"
        self.assertEqual(true_text, test_text)

    def test_handle_markers(self):
        """Test the handling of a marker"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        with open("tests/testfiles/arrows_marking.svg", encoding="utf8") as svg_file:
            tzpe.convert(svg_file=svg_file, no_output=True, returnstring=True)
            # Changing arrows options does not work
            tzpe.options.arrow = "latex"
            # Reversed arrow are not well generated
            for id_node, expected_out in zip(
                ["noA", "ar", "al", "arl", "a_r", "a_l", "a_rl", "ar_l"],
                [[], ["->"], ["<-"], ["<->"]],
            ):
                node = tzpe.svg.getElementById(id_node)
                # pylint: disable=protected-access
                out_markers = tzpe._handle_markers(node.specified_style())
                self.assertEqual(expected_out, out_markers)

            # Include options
            tzpe.options.markings = "include"
            for id_node in ["noA", "ar", "al", "arl", "a_r", "a_l", "a_rl", "ar_l"]:
                node = tzpe.svg.getElementById(id_node)
                # pylint: disable=protected-access
                out_markers = tzpe._handle_markers(node.specified_style())
                self.assertEqual(out_markers, [])

            # Include options
            tzpe.options.markings = "notAOption"
            for id_node in ["noA", "ar", "al", "arl", "a_r", "a_l", "a_rl", "ar_l"]:
                node = tzpe.svg.getElementById(id_node)
                # pylint: disable=protected-access
                out_markers = tzpe._handle_markers(node.specified_style())
                self.assertEqual(out_markers, [])

    def test_handle_shape(self):
        """Testing handling unkwon shape"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.convert(StringIO(SVG_TEXT), no_output=True, returnstring=True)
        text_node = tzpe.svg.getElementById("textNode")

        # pylint: disable=protected-access
        emtpy_str, empty_list = tzpe._handle_shape(text_node)
        self.assertEqual(empty_list, [])
        self.assertEqual(emtpy_str, "")

    def test_handle_text(self):
        """Testing handling ignoring text"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.convert(
            StringIO(SVG_TEXT), no_output=True, returnstring=True, ignore_text=True
        )
        text_node = tzpe.svg.getElementById("textNode")

        # pylint: disable=protected-access
        emtpy_str = tzpe._handle_text(text_node)
        self.assertEqual(emtpy_str, "")

    def test_effect(self):
        """Test effect function"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.convert(StringIO(SVG_EMPTY), no_output=True, returnstring=True)
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
\begin{tikzpicture}[y=1mm, x=1mm, yscale=\globalscale,xscale=\globalscale, every node/.append style={scale=\globalscale}, inner sep=0pt, outer sep=0pt]

\end{tikzpicture}
\end{document}
"""
        test_path = tzpe.output_code
        self.assertEqual(test_path, true_path)

    def test_save_raw(self):
        """Test raw saving"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        tzpe.convert(StringIO(SVG_4_RECT), no_output=True, returnstring=True)
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
\definecolor{navy}{RGB}{0,0,128}


\def \globalscale {1.000000}
\begin{tikzpicture}[y=1cm, x=1cm, yscale=\globalscale,xscale=\globalscale, every node/.append style={scale=\globalscale}, inner sep=0pt, outer sep=0pt]
  \path[draw=blue,line width=0.02cm] (0.01, 3.99) rectangle (11.99, 0.01);



  \path[draw=navy,fill=yellow,line width=0.1cm] (4.0, 3.0) rectangle (8.0, 1.0);



  \path[draw=green,line width=0.1cm] (4.0, 3.0) rectangle (8.0, 1.0);



  \path[draw=green,line width=0.1cm] (4.0, 3.0) rectangle (8.0, 1.0);




\end{tikzpicture}
\end{document}
"""
        test_path = tzpe.convert(
            StringIO(SVG_4_RECT), no_output=True, returnstring=True
        )
        self.assertEqual(test_path, true_path)

    def test_none_input_file(self):
        """Test convert when input is None"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        true_path = ""
        test_path = tzpe.convert(None, no_output=True, returnstring=True)
        self.assertEqual(test_path, true_path)

    def test_print_version(self):
        """Test convert when only asking for a print"""
        tzpe = TikZPathExporter(inkscape_mode=False)
        true_path = ""
        tzpe.arg_parser.set_defaults(printversion=True)
        test_path = tzpe.convert(
            StringIO(SVG_4_RECT),
            no_output=True,
            returnstring=True,
        )
        self.assertEqual(test_path, true_path)
