#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""\
Convert SVG to TikZ/PGF commands for use with (La)TeX

This script is an Inkscape extension for exporting from SVG to (La)TeX. The
extension recreates the SVG drawing using TikZ/PGF commands, a high quality TeX
macro package for creating graphics programmatically.

The script is tailored to Inkscape SVG, but can also be used to convert arbitrary
SVG files from the command line.

Author: Kjell Magne Fauske
"""

# Copyright (C) 2008, 2009, 2010 Kjell Magne Fauske, http://www.fauskes.net
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import platform

__version__ = "2.0.0"
__author__ = "Devillez Louis, Kjell Magne Fauske"
__maintainer__ = "Deville Louis"
__email__ = "louis.devillez@gmail.com"


import sys

from textwrap import wrap
import codecs
import io
import os
from subprocess import Popen, PIPE

import re
import math

from math import sin, cos, atan2
from math import pi as mpi

import logging

import ctypes
import inkex
from inkex.transforms import Vector2d
from lxml import etree

#### Utility functions and classes

TIKZ_BASE_COLOR = [
        "black",
        "red",
        "green",
        "blue",
        "cyan",
        "yellow",
        "magenta",
        "white",
        "gray"
        ]

SPECIAL_TEX_CHARS = ["$", "\\", "%", "_", "#", "{", r"}", "^", "&"]
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
_tex_charmap = dict(list(zip(SPECIAL_TEX_CHARS, SPECIAL_TEX_CHARS_REPLACE)))


def escape_texchars(input_string):
    r"""Escape the special LaTeX-chars %{}_^

    Examples:

    >>> escape_texchars('10%')
    '10\\%'
    >>> escape_texchars('%{}_^\\$')
    '\\%\\{\\}\\_\\^{}$\\backslash$\\$'
    """
    return "".join([_tex_charmap.get(c, c) for c in input_string])


def copy_to_clipboard(text):
    """Copy text to the clipboard

    Returns True if successful. False otherwise.
    """

    text_type = str

    def _do_windows_clipboard(text):
        # from http://pylabeditor.svn.sourceforge.net/viewvc/pylabeditor/trunk/src/shells.py?revision=82&view=markup

        cf_unicode_text = 13
        ghnd = 66

        ctypes.windll.kernel32.GlobalAlloc.restype = ctypes.c_void_p
        ctypes.windll.kernel32.GlobalLock.restype = ctypes.c_void_p

        text = text_type(text, "utf8")
        buffer_size = (len(text) + 1) * 2
        h_global_mem = ctypes.windll.kernel32.GlobalAlloc(
            ctypes.c_uint(ghnd), ctypes.c_size_t(buffer_size)
        )
        lp_global_mem = ctypes.windll.kernel32.GlobalLock(ctypes.c_void_p(h_global_mem))
        ctypes.cdll.msvcrt.memcpy(
            ctypes.c_void_p(lp_global_mem),
            ctypes.c_wchar_p(text),
            ctypes.c_int(buffer_size),
        )
        ctypes.windll.kernel32.GlobalUnlock(ctypes.c_void_p(h_global_mem))
        if ctypes.windll.user32.OpenClipboard(0):
            ctypes.windll.user32.EmptyClipboard()
            ctypes.windll.user32.SetClipboardData(
                ctypes.c_int(cf_unicode_text), ctypes.c_void_p(h_global_mem)
            )
            ctypes.windll.user32.CloseClipboard()
            return True
        return False

    def _call_command(command, text):
        # see https://bugs.launchpad.net/ubuntu/+source/inkscape/+bug/781397/comments/2
        try:
            devnull = os.open(os.devnull, os.O_RDWR)
            with Popen(command, stdin=PIPE, stdout=devnull, stderr=devnull) as proc:
                proc.communicate(text)
                if not proc.returncode:
                    return True

        except OSError:
            pass
        return False

    def _do_linux_clipboard(text):
        # try xclip first, then xsel
        xclip_cmd = ["xclip", "-selection", "clipboard"]
        success = _call_command(xclip_cmd, text)
        if success:
            return True

        xsel_cmd = ["xsel"]
        success = _call_command(xsel_cmd, text)
        return success

    def _do_osx_clipboard(text):
        pbcopy_cmd = ["pbcopy"]
        return _call_command(pbcopy_cmd, text)
        # try os /linux

    if os.name == "nt" or platform.system() == "Windows":
        return _do_windows_clipboard(text)
    if os.name == "mac" or platform.system() == "Darwin":
        return _do_osx_clipboard(text)
    return _do_linux_clipboard(text)


def nsplit(seq, n_split=2):
    """Split a sequence into pieces of length n

    If the length of the sequence isn't a multiple of n, the rest is discarded.
    Note that nsplit will strings into individual characters.

    Examples:
    >>> nsplit('aabbcc')
    [('a', 'a'), ('b', 'b'), ('c', 'c')]
    >>> nsplit('aabbcc',n_split=3)
    [('a', 'a', 'b'), ('b', 'c', 'c')]

    # Note that cc is discarded
    >>> nsplit('aabbcc',n_split=4)
    [('a', 'a', 'b', 'b')]
    """
    return list(zip(*[iter(seq)] * n_split))


def chunks(string, c_l):
    """Split a string or sequence into pieces of length c_l and return an iterator"""
    for i in range(0, len(string), c_l):
        yield string[i : i + c_l]


def _ns(element_name, name_space="svg"):
    return inkex.addNS(element_name, name_space)


def filter_tag(node):
    """
    A function to see if a node should be draw or not
    """
    if type(node) is etree._Element:
        return False
    if type(node) is etree._Comment:
        return False
    if node.TAG == "desc":
        return False
    if node.TAG == "namedview":
        return False
    if node.TAG == "defs":
        return False
    if node.TAG == "svg":
        return False
    return True


#### Output configuration section

TEXT_INDENT = "  "

CROP_TEMPLATE = r"""
\usepackage[active,tightpage]{preview}
\PreviewEnvironment{tikzpicture}
"""

# Templates
STANDALONE_TEMPLATE = (
    r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{tikz}
%(cropcode)s
\begin{document}
%(colorcode)s
%(gradientcode)s
\def \globalscale {%(scale)f}
\begin{tikzpicture}[y=1%(unit)s, x=1%(unit)s, yscale=%(ysign)s\globalscale,"""
    r"""xscale=\globalscale, inner sep=0pt, outer sep=0pt%(extraoptions)s]
%(pathcode)s
\end{tikzpicture}
\end{document}
"""
)

FIG_TEMPLATE = (
    r"""
%(colorcode)s
%(gradientcode)s
\def \globalscale {%(scale)f}
\begin{tikzpicture}[y=1%(unit)s, x=1%(unit)s, yscale=%(ysign)s\globalscale,"""
    r"""xscale=\globalscale, inner sep=0pt, outer sep=0pt%(extraoptions)s]
%(pathcode)s
\end{tikzpicture}
"""
)

SCALE = "scale"
DICT = "dict"
DIMENSION = "dimension"
FACTOR = "factor"  # >= 1

# Map Inkscape/SVG stroke and fill properties to corresponding TikZ options.
# Format:
#   'svg_name' : ('tikz_name', value_type, data)
PROPERTIES_MAP = {
    "opacity": ("opacity", SCALE, ""),
    # filling
    "fill-opacity": ("fill opacity", SCALE, ""),
    "fill-rule": ("", DICT, {"nonzero": "nonzero rule", "evenodd": "even odd rule"}),
    # stroke
    "stroke-opacity": ("draw opacity", SCALE, ""),
    "stroke-linecap": (
        "line cap",
        DICT,
        {"butt": "butt", "round": "round", "rect": "rect"},
    ),
    "stroke-linejoin": (
        "line join",
        DICT,
        {
            "miter": "miter",
            "round": "round",
            "bevel": "bevel",
        },
    ),
    "stroke-width": ("line width", DIMENSION, ""),
    "stroke-miterlimit": ("miter limit", FACTOR, ""),
    "stroke-dashoffset": ("dash phase", DIMENSION, "0"),
}

# default values according to the SVG spec.
DEFAULT_PAINTING_VALUES = {
    # fill
    "fill": "black",
    "fill-rule": "nonzero",
    "fill-opacity": 1,
    # stroke
    "stroke": "none",
    "stroke-width": 1,
    "stroke-linecap": "butt",
    "stroke-linejoin": "miter",
    "stroke-miterlimit": 4,
    "stroke-dasharray": "none",
    "stroke-dashoffset": 0,
    "stroke-opacity": 1,
}

STROKE_PROPERTIES = set(
    [
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-miterlimit",
        "stroke-dasharray",
        "stroke-dashoffset",
        "stroke-opacity",
    ]
)

FILL_PROPERTIES = set(
    [
        "fill",
        "fill-rule",
        "fill-opacity",
    ]
)


def calc_arc(cp: Vector2d, r_i: Vector2d, ang, fa, fs, pos: Vector2d):
    """
    Calc arc paths

    It computes the start and end angle for a non rotated ellipse

    cp: initial control point
    r_i: x and y radius
    ang: x-axis-rotation
    fa: sweep flag
    fs: large sweep flag
    pos: final control point

    The calc_arc function is based on the calc_arc function in the
    paths_svg2obj.py script bundled with Blender 3D
    Copyright (c) jm soler juillet/novembre 2004-april 2007,
    Resource: https://developer.mozilla.org/fr/docs/Web/SVG/Tutorial/Paths#elliptical_arc (in french)
    """
    ang = math.radians(ang)

    r = Vector2d(abs(r_i.x), abs(r_i.y))
    p_pos = Vector2d(
        abs((cos(ang) * (cp.x - pos.x) + sin(ang) * (cp.y - pos.y)) * 0.5) ** 2.0,
        abs((cos(ang) * (cp.y - pos.y) - sin(ang) * (cp.x - pos.x)) * 0.5) ** 2.0,
    )
    rp = Vector2d(
        p_pos.x / (r.x**2.0) if abs(r.x) > 0.0 else 0.0,
        p_pos.y / (r.y**2.0) if abs(r.y) > 0.0 else 0.0,
    )

    p_l = rp.x + rp.y
    if p_l > 1.0:
        p_l = p_l**0.5
        r.x *= p_l
        r.y *= p_l

    car = Vector2d(
        cos(ang) / r.x if abs(r.x) > 0.0 else 0.0,
        cos(ang) / r.y if abs(r.y) > 0.0 else 0.0,
    )

    sar = Vector2d(
        sin(ang) / r.x if abs(r.x) > 0.0 else 0.0,
        sin(ang) / r.y if abs(r.y) > 0.0 else 0.0,
    )

    p0 = Vector2d(car.x * cp.x + sar.x * cp.y, (-sar.y) * cp.x + car.y * cp.y)
    p1 = Vector2d(car.x * pos.x + sar.x * pos.y, (-sar.y) * pos.x + car.y * pos.y)

    hyp = (p1.x - p0.x) ** 2 + (p1.y - p0.y) ** 2

    if abs(hyp) > 0.0:
        s_q = 1.0 / hyp - 0.25
    else:
        s_q = -0.25

    s_f = max(0.0, s_q) ** 0.5
    if fs == fa:
        s_f *= -1
    c = Vector2d(
        0.5 * (p0.x + p1.x) - s_f * (p1.y - p0.y),
        0.5 * (p0.y + p1.y) + s_f * (p1.x - p0.x),
    )
    ang_0 = atan2(p0.y - c.y, p0.x - c.x)
    ang_1 = atan2(p1.y - c.y, p1.x - c.x)
    ang_arc = ang_1 - ang_0
    if ang_arc < 0.0 and fs == 1:
        ang_arc += 2.0 * mpi
    elif ang_arc > 0.0 and fs == 0:
        ang_arc -= 2.0 * mpi

    ang0 = math.degrees(ang_0)
    ang1 = math.degrees(ang_1)

    if ang_arc > 0:
        if ang_0 < ang_1:
            pass
        else:
            ang0 -= 360
    else:
        if ang_0 < ang_1:
            ang1 -= 360

    return ang0, ang1, r


def parse_arrow_style(arrow_name):
    """Docstring"""
    strip_name = arrow_name.split("url")[1][1:-1]

    if "Arrow1" in strip_name:
        return "latex"
    if "Arrow2" in strip_name:
        return "stealth"
    if "Stop" in strip_name:
        return "|"
    return "latex"


def marking_interpret(marker):
    """Docstring"""
    raw_marker = ""
    if marker:
        arrow_style = parse_arrow_style(marker)
        raw_marker = arrow_style[:]
        if "end" in marker:
            raw_marker += " reversed"
    return raw_marker


# pylint: disable=too-many-ancestors
class TikZPathExporter(inkex.Effect, inkex.EffectExtension):
    """Class to export a svg to tikz code"""

    def __init__(self, inkscape_mode=True):
        self.inkscape_mode = inkscape_mode
        inkex.Effect.__init__(self)
        inkex.EffectExtension.__init__(self)
        self._set_up_options()

        self.text_indent = TEXT_INDENT
        self.colors = []
        self.color_code = ""
        self.gradient_code = ""
        self.output_code = ""
        self.used_gradients = set()
        self.height = 0
        self.round_number = 4

    def _set_up_options(self):
        parser = self.arg_parser
        parser.set_defaults(
            codeoutput="standalone",
            crop=False,
            clipboard=False,
            wrap=False,
            indent=True,
            returnstring=False,
            scale=1,
            mode="effect",
            notext=False,
            verbose=False,
            texmode="escape",
            markings="ignore",
        )
        parser.add_argument(
            "--codeoutput",
            dest="codeoutput",
            choices=("standalone", "codeonly", "figonly"),
            help="Amount of boilerplate code (standalone, figonly, codeonly).",
        )
        parser.add_argument(
            "-t",
            "--texmode",
            dest="texmode",
            default="escape",
            choices=("math", "escape", "raw"),
            help="Set text mode (escape, math, raw). Defaults to 'escape'",
        )
        parser.add_argument(
            "--markings",
            dest="markings",
            default="arrows",
            choices=("ignore", "include", "interpret", "arrows"),
            help="Set markings mode. Defaults to 'ignore'",
        )
        parser.add_argument(
            "--arrow",
            dest="arrow",
            default="latex",
            choices=("latex", "stealth", "to", ">"),
            help="Set arrow style for markings mode arrow. Defaults to 'latex'",
        )
        parser.add_argument(
            "--output-unit",
            dest="output_unit",
            default="cm",
            choices=("mm", "cm", "m", "in", "pt", "px", "Q", "pc"),
            help="Set output units. Defaults to 'cm'",
        )

        self._add_booloption(
            parser,
            "--crop",
            dest="crop",
            help="Use the preview package to crop the tikzpicture",
        )
        self._add_booloption(
            parser, "--clipboard", dest="clipboard", help="Export to clipboard"
        )
        self._add_booloption(parser, "--wrap", dest="wrap", help="Wrap long lines")
        self._add_booloption(parser, "--indent", default=True, help="Indent lines")

        self._add_booloption(
            parser,
            "--latexpathtype",
            dest="latexpathtype",
            default=True,
            help="Allow path modification for image",
        )
        self._add_booloption(
            parser,
            "--noreversey",
            dest="noreversey",
            help="Do not reverse the y axis (Inkscape axis)",
            default=False,
        )

        parser.add_argument(
            "--removeabsolute",
            dest="removeabsolute",
            default=None,
            help="Remove the value of removeabsolute from image path",
        )

        if self.inkscape_mode:
            parser.add_argument(
                "--returnstring",
                action="store_true",
                dest="returnstring",
                help="Return as string",
            )
            parser.add_argument(
                "--tab"
            )  # Dummy option. Needed because Inkscape passes the notebook
            # tab as an option.

        # utility ?
        parser.add_argument(
            "-m",
            "--mode",
            dest="mode",
            choices=("output", "effect", "cli"),
            default="cli",
            help="Extension mode (effect default)",
        )
        self._add_booloption(
            parser,
            "--notext",
            dest="ignore_text",
            default=False,
            help="Ignore all text",
        )
        parser.add_argument(
            "--scale",
            dest="scale",
            type=float,
            default=1,
            help="Apply scale to resulting image, defaults to 1.0",
        )
        if not self.inkscape_mode:
            parser.add_argument(
                "--standalone",
                dest="codeoutput",
                action="store_const",
                const="standalone",
                help="Generate a standalone document",
            )
            parser.add_argument(
                "--figonly",
                dest="codeoutput",
                action="store_const",
                const="figonly",
                help="Generate figure only",
            )
            parser.add_argument(
                "--codeonly",
                dest="codeoutput",
                action="store_const",
                const="codeonly",
                help="Generate drawing code only",
            )
            parser.add_argument(
                "-V",
                "--version",
                dest="printversion",
                action="store_true",
                help="Print version information and exit",
                default=False,
            )
        self._add_booloption(
            parser,
            "--verbose",
            dest="verbose",
            default=False,
            help="Verbose output (useful for debugging)",
        )

    def _add_booloption(self, parser, *args, **kwargs):
        if self.inkscape_mode:
            kwargs["action"] = "store"
            kwargs["type"] = inkex.Boolean
            parser.add_argument(*args, **kwargs)
        else:
            kwargs["action"] = "store_true"
            parser.add_argument(*args, **kwargs)

    def convert_unit(self, value):
        """Convert value from the user unit to the output unit which is an option"""
        ret = self.svg.unit_to_viewport(
                value, self.options.output_unit
                )
        return ret

    def convert_unit_coordinate(self, coordinate, update_height=True):
        """
        Convert a coordinate (Vector2D)) from the user unit to the output unit
        """
        y = self.convert_unit(coordinate[1])
        return Vector2d(
            self.convert_unit(coordinate[0]),
            self.update_height(y) if update_height else y,
        )

    def convert_unit_coordinates(self, coordinates, update_height=True):
        """
        Convert a list of coordinates (Vector2D)) from the user unit to the output unit
        """
        return [
            self.convert_unit_coordinate(coordinate, update_height)
            for coordinate in coordinates
        ]

    def round_value(self, value):
        """Round a value with respect to the round number of the class"""
        return round(value, self.round_number)

    def round_coordinate(self, coordinate):
        """Round a coordinante(Vector2D) with respect to the round number of the class"""
        return Vector2d(
            self.round_value(coordinate[0]), self.round_value(coordinate[1])
        )

    def round_coordinates(self, coordinates):
        """Round a coordinante(Vector2D) with respect to the round number of the class"""
        return [self.round_coordinate(coordinate) for coordinate in coordinates]

    def update_height(self, y_val):
        """Compute the distance between the point and the bottom of the document"""
        if not self.options.noreversey:
            return self.height - y_val
        return y_val

    def get_node_from_id(self, node_ref):
        """Return the node with the id node_ref. If there is none return None"""
        if node_ref.startswith("url("):
            node_id = re.findall(r"url\((.*?)\)", node_ref)
            if len(node_id) > 0:
                ref_id = node_id[0]
        else:
            ref_id = node_ref
        if ref_id.startswith("#"):
            ref_id = ref_id[1:]

        ref_node = self.document.xpath(f'//*[@id="{ref_id}"]', namespaces=inkex.NSS)
        if len(ref_node) == 1:
            return ref_node[0]
        return None

    def transform(self, coord_list, cmd=None):
        """Apply transformations to input coordinates"""
        coord_transformed = []

        if cmd == "Q":
            return tuple(coord_list)

        if not isinstance(coord_list, list):
            coord_transformed = coord_list
        elif not len(coord_list) % 2:
            for x_pos, y_pos in nsplit(coord_list, 2):
                coord_transformed.append(f"{x_pos:.4f}")
                coord_transformed.append(f"{y_pos:.4f}")
        elif len(coord_list) == 1:
            coord_transformed = [f"{coord_list[0]:.4f}cm"]
        else:
            coord_transformed = coord_list

        return tuple(coord_transformed)

    def convert_color_to_tikz(self, color):
        """
        Convert a svg color to tikzcode and add it to the list of known colors
        """
        color = color.to_rgb()
        xcolorname = str(color.to_named()).replace("#", "c")
        if xcolorname in TIKZ_BASE_COLOR:
            return xcolorname
        if xcolorname not in self.colors:
            self.colors.append(xcolorname)
            self.color_code += "\\definecolor{" + f"{xcolorname}" + "}{RGB}{"
            self.color_code += f"{color.red},{color.green},{color.blue}" + "}\n"
        return xcolorname

    def _convert_gradient(self, gradient_node, gradient_tikzname):
        """Convert an SVG gradient to a PGF gradient"""

        # http://www.w3.org/TR/SVG/pservers.html
        def bpunit(offset):
            # bp_unit = ""
            # if offset.endswith("%"):
            # bp_unit = offset[0:-1]
            # else:
            # bp_unit = str(int(round((float(offset)) * 100)))
            # return bp_unit

            # if gradient_node.tag == _ns("linearGradient"):
            # c = ""
            # c += (
            # r"\pgfdeclarehorizontalshading{"
            # + f"{gradient_tikzname}"
            # + "}{100bp}{\n"
            # )
            # stops = []
            # for n in gradient_node:
            # if n.tag == _ns("stop"):
            # stops.append(
            # f"color({bpunit(n.get('offset'))}pt)="
            # f"({self.get_color(n.get('stop-color'))})"
            # )
            # c += ";".join(stops)
            # c += "\n}\n"
            # return c

            return ""

    def _handle_gradient(self, gradient_ref):
        # grad_node = self.get_node_from_id(gradient_ref)
        # gradient_id = grad_node.get("id")
        # if grad_node is None:
        # return []
        # gradient_tikzname = gradient_id
        # if gradient_id not in self.used_gradients:
        # grad_code = self._convert_gradient(grad_node, gradient_tikzname)
        # if grad_code:
        # self.gradient_code += grad_code
        # self.used_gradients.add(gradient_id)
        # if gradient_id in self.used_gradients:
        # return ["shade", f"shading={gradient_tikzname}"]
        return []

    def _handle_markers(self, style):
        "Convert marking style from svg to tikz code"
        # http://www.w3.org/TR/SVG/painting.html#MarkerElement
        ms = style.get("marker-start")
        me = style.get("marker-end")

        # Avoid options "-" on empty path
        if ms is None and me is None:
            return []

        if self.options.markings == "ignore":
            return []

        if self.options.markings == "include":
            # TODO to implement:
            # Include arrow as path object
            # Define custom arrow and use them
            return []

        if self.options.markings == "interpret":
            start_arrow = marking_interpret(ms)
            end_arrow = marking_interpret(me)

            return [start_arrow + "-" + end_arrow]

        if self.options.markings == "arrows":
            start_arrow = self.options.arrow[:] if ms is not None else ""
            if ms is not None and "end" in ms:
                start_arrow += " reversed"

            if start_arrow == self.options.arrow:
                start_arrow = "<"
                if me is not None and "end" in me:
                    start_arrow = ">"

            end_arrow = self.options.arrow[:] if me is not None else ""
            if me and "start" in me:
                end_arrow += " reversed"

            if end_arrow == self.options.arrow:
                end_arrow = ">"
                if me is not None and "start" in me:
                    end_arrow = "<"

            return [start_arrow + "-" + end_arrow]
        return []

    def convert_svgstyle_to_tikzstyle(self, node=None):
        """
        Convert the style from the svg to the option to apply to tikz code
        """

        if not node.is_visible:
            return []

        style = node.specified_style()
        if style.get("display") == "none":
            if node.TAG == "g":
                return ["none"]
            return []

        options = []

        for use_path in [("stroke", "draw"), ("fill", "fill")]:
            value = style.get(use_path[0])
            if value != "none" and value is not None:
                options.append(
                    f"{use_path[1]}={self.convert_color_to_tikz(style.get_color(use_path[0]))}"
                )

            if value != "none" and value is None and use_path[0] == "fill":
                shapes = [
                    "path",
                    "rect",
                    "circle",
                    "ellipse",
                    "line",
                    "polyline",
                    "polygon",
                ]

                if node.TAG in shapes:
                    # svg shapes with no fill option should fill by black
                    # https://www.w3.org/TR/2011/REC-SVG11-20110816/painting.html#FillProperty
                    options.append("fill")

        for svgname, tikzdata in PROPERTIES_MAP.items():
            tikzname, valuetype, data = tikzdata
            value = style.get(svgname)

            if value is None or value == "none":
                continue

            if valuetype == SCALE:
                val = float(value)
                if val != 1:
                    options.append(f"{tikzname}={float(value):.3f}")
            elif valuetype == DICT:
                if tikzname:
                    options.append(f"{tikzname}={data.get(value,'')}")
                else:
                    options.append(data.get(value, ""))
            elif valuetype == DIMENSION:
                if value and value != data:
                    options.append(
                        f"{tikzname}="
                        f"{self.convert_unit(value):.3f}"
                        f"{self.options.output_unit}"
                    )
            elif valuetype == FACTOR:
                try:
                    val = float(value)
                    if val >= 1.0:
                        options.append(f"{tikzname}={val:.2f}")
                except ValueError:
                    pass

        # How to get arrows
        marker_options = self._handle_markers(style)
        if marker_options:
            options += marker_options

        # TODO DO we need to fill those empty shapes ?
        # svg shapes with no fill option should fill by black
        # https://www.w3.org/TR/2011/REC-SVG11-20110816/painting.html#FillProperty
        # yes

        # TODO add test with dash-array
        dasharray = style.get("stroke-dasharray")
        if dasharray is not None and dasharray != "none":
            split_str = ","
            if split_str not in dasharray:
                split_str = " "
            lengths = list(
                map(self.convert_unit, [i.strip() for i in dasharray.split(split_str)])
            )
            dashes = []
            for idx, length in enumerate(lengths):
                lenstr = f"{length:0.3f}{self.options.output_unit}"
                if idx % 2:
                    dashes.append(f"off {lenstr}")
                else:
                    dashes.append(f"on {lenstr}")
            options.append(f"dash pattern={' '.join(dashes)}")

        return options

    def convert_transform_to_tikz(self, node=None):
        """
        Convert inkex transform to tikz code
        """
        transform = node.transform
        # TODO decompose matrix in list of transform

        options = []

        for trans in [transform]:
            # Empty transform
            if str(trans) == "":
                continue
            if trans.is_translate():
                mov = Vector2d(trans.e, trans.f)
                mov = self.round_coordinate(self.convert_unit_coordinate(mov))

                options.append("shift={" + f"({mov[0]},{mov[1]})" + "}")
            elif trans.is_rotate():
                # TODO get center of rotation
                options.append(f"rotate={-trans.rotation_degrees()}")
            elif trans.is_scale():
                x = trans.a
                y = trans.d

                if x == y:
                    options.append(f"scale={x}")
                else:
                    options.append(f"xscale={x},yscale={y}")

            elif "matrix" in str(trans):
                tx = self.convert_unit(trans.e)
                ty = self.update_height(self.convert_unit(trans.f))
                options.append(
                    f"cm={{ {self.round_value(trans.a)},{self.round_value(trans.b)},{self.round_value(trans.c)}"
                    f",{self.round_value(trans.d)},({tx},{ty})}}"
                )
            elif "skewX" in str(trans):
                options.append(f"xslant={math.tan(trans.c * math.pi / 180)}")
            elif "skewY" in str(trans):
                options.append(f"yslant={math.tan(trans.b * math.pi / 180)}")
            elif "scale" in str(trans):
                if trans.a == trans.d:
                    options.append(f"scale={trans.a}")
                else:
                    options.append(f"xscale={trans.a},yscale={trans.d}")
            else:
                pass
        return options

    def _handle_group(self, groupnode):
        s = ""

        goptions = self.convert_svgstyle_to_tikzstyle(groupnode)
        transformation = self.convert_transform_to_tikz(groupnode)

        options = transformation + goptions
        tmp = self.text_indent

        if len(options) > 0:
            self.text_indent += TEXT_INDENT
        group_id = groupnode.get_id()
        code = self._output_group(groupnode)
        self.text_indent = tmp

        if code == "":
            return ""
        if self.options.verbose and group_id:
            extra = f"%% {group_id}"
        else:
            extra = ""

        hide = "none" in options
        if len(options) > 0:
            if hide:
                options.remove("none")
            pstyles = [",".join(options)]
            if "opacity" in pstyles[0]:
                pstyles.append("transparency group")

            if self.options.indent:
                s += self.text_indent + "\\begin{scope}"
                s += f"[{','.join(pstyles)}]{extra}\n{code}"
                s += self.text_indent + "\\end{scope}\n"
            else:
                s += "\\begin{scope}"
                s += f"[{','.join(pstyles)}]{extra}\n{code}"
                s += "\\end{scope}\n"
        elif self.options.verbose:
            if self.options.indent:
                s += self.text_indent + "\\begin{scope}"
                s += f"{extra}\n{code}{self.text_indent}"
                s += "\\end{scope}\n"
            else:
                s += "\\begin{scope}\n" + f"{code}" + "\\end{scope}\n"
        else:
            s += code
        if hide:
            s = "%" + s.replace("\n", "\n%")[:-1]
        return s

    def _handle_image(self, node):
        """Handles the image tag and returns a code, options tuple"""
        # http://www.w3.org/TR/SVG/struct.html#ImageElement
        # http://www.w3.org/TR/SVG/coords.html#PreserveAspectRatioAttribute
        #         Convert the pixel values to pt first based on http://www.endmemo.com/sconvert/pixelpoint.php
        p = self.round_coordinate(self.convert_unit_coordinate(node.x, node.y))

        width = inkex.units.convert_unit(self.convert_unit(node.width), "pt", "px")
        height = inkex.units.convert_unit(self.convert_unit(node.height), "pt", "px")

        href = node.href
        isvalidhref = "data:image/png;base64" not in href
        if self.options.latexpathtype and isvalidhref:
            href = href.replace(self.options.removeabsolute, "")
        if not isvalidhref:
            href = "base64 still not supported"
            return ""
        return (
            r"\\node[anchor=north west,inner sep=0, scale=\globalscale]"
            + f" ({node.get_id()}) at ({p[0]}, {p[1]}) "
            + r"{\includegraphics[width="
            + f"{width}pt,height={height}pt]"
            + "{"
            + f"{href}"
            + "}"
        )

    def convert_path_to_tikz(self, path):
        """
        Convert a path from inkex to tikz code
        """
        s = ""

        for command in path.proxy_iterator():
            # transform coordinates
            tparams = self.round_coordinates(
                self.convert_unit_coordinates(command.control_points)
            )
            # SVG paths
            # moveto
            letter = command.letter.upper()
            if letter == "M":
                current_pos = tparams[0]
                s += f"({tparams[0][0]},{tparams[0][1]})"
            # lineto
            elif letter in ["L", "H", "V"]:
                current_pos = tparams[0]
                s += f" -- ({tparams[0][0]},{tparams[0][1]})"
            # cubic bezier curve
            elif letter == "C":
                s += (
                    f" .. controls ({tparams[0][0]}, {tparams[0][1]})"
                    f" and ({tparams[1][0]}, {tparams[1][1]}) .. ({tparams[2][0]}, {tparams[2][1]})"
                )
                current_pos = tparams[2]
            # quadratic bezier curve
            elif letter == "Q":
                # need to convert to cubic spline
                # CP1 = QP0 + 2/3 *(QP1-QP0)
                # CP2 = CP1 + 1/3 *(QP2-QP0)
                # http://fontforge.sourceforge.net/bezier.html
                qp0x, qp0y = current_pos
                qp1x, qp1y, qp2x, qp2y = tparams
                cp1x = qp0x + (2.0 / 3.0) * (qp1x - qp0x)
                cp1y = qp0y + (2.0 / 3.0) * (qp1y - qp0y)
                cp2x = cp1x + (qp2x - qp0x) / 3.0
                cp2y = cp1y + (qp2y - qp0y) / 3.0
                s += (
                    f" .. controls ({cp1x:.4f}, {cp1y:.4f}) and ({cp2x:.4f},"
                    f" {cp2y:.4f}) .. ({qp2x:.4f}, {qp2y:.4f})"
                )
                current_pos = tparams[-1]
            # close path
            elif letter == "Z":
                s += " -- cycle"
            # arc
            elif letter == "A":
                # Do not shift other values
                # tparams = self.round_coordinates(self.convert_unit_coordinates(command.control_points))
                command = command.to_absolute()

                cp = Vector2d(current_pos[0], current_pos[1])
                r = Vector2d(
                    self.convert_unit(command.rx), self.convert_unit(command.ry)
                )
                pos = Vector2d(command.x, command.y)
                pos = self.convert_unit_coordinate(pos)
                sweep = command.sweep

                if not self.options.noreversey:
                    sweep = 1 - sweep
                    r.y *= -1

                start_ang_o, end_ang_o, r = calc_arc(
                    cp, r, command.x_axis_rotation, command.large_arc, sweep, pos
                )

                r.x = self.round_value(r.x)
                r.y = self.round_value(r.y)

                # pgf 2.0 does not like angles larger than 360
                # make sure it is in the +- 360 range
                start_ang = self.round_value(start_ang_o % 360)
                end_ang = self.round_value(end_ang_o % 360)
                if start_ang_o < end_ang_o and not start_ang < end_ang:
                    start_ang -= 360
                elif start_ang_o > end_ang_o and not start_ang > end_ang:
                    end_ang -= 360

                ang = self.round_value(command.x_axis_rotation)
                if r.x == r.y:
                    # Todo: Transform radi
                    radi = f"{r.x}"
                else:
                    radi = f"{r.x} and {r.y}"
                if ang != 0.0:
                    s += (
                        "{" + f"[rotate={ang}] arc({start_ang}"
                        ":{end_ang}:{radi})" + "}"
                    )
                else:
                    s += f"arc({start_ang}:{end_ang}:{radi})"
                current_pos = tparams[-1]
        return s

    def _handle_shape(self, node):
        """Extract shape data from node"""
        options = []
        if node.TAG == "rect":
            inset = node.rx or node.ry
            x = node.left
            y = node.top
            corner_a = Vector2d(x, y)
            corner_a = self.round_coordinate(self.convert_unit_coordinate(corner_a))

            width = node.width
            height = node.height

            # map from svg to tikz
            if width == 0.0 or height == 0.0:
                return "", []

            corner_b = Vector2d(x + width, y + height)
            corner_b = self.round_coordinate(self.convert_unit_coordinate(corner_b))

            if inset and abs(inset) > 1e-5:
                unit_to_scale = self.round_value(
                    self.convert_unit(inset)
                )
                options = [f"rounded corners={unit_to_scale}{self.options.output_unit}"]

            return (
                f"({corner_a[0]}, {corner_a[1]}) rectangle ({corner_b[0]}, {corner_b[1]})",
                options,
            )

        if node.TAG in ["polyline", "polygon"]:
            points = node.get_path().get_points()
            points = self.round_coordinates(self.convert_unit_coordinates(points))
            points = [f"({vec.x}, {vec.y})" for vec in points]

            path = " -- ".join(points)

            if node.TAG == "polygon":
                path += "-- cycle"

            return f"{path};", []

        if node.TAG == "line":
            p_a = Vector2d(node.x1, node.y1)
            p_a = self.round_coordinate(self.convert_unit_coordinate(p_a))
            p_b = Vector2d(node.x2, node.y2)
            p_b = self.round_coordinate(self.convert_unit_coordinate(p_b))
            # check for zero lenght line
            print("lien")
            if not ((p_a[0] == p_b[0]) and (p_a[1] == p_b[1])):
                return f"({p_a[0]}, {p_a[1]}) -- ({p_b[0], p_b[1]});", []

        if node.tag == _ns("circle"):
            center = Vector2d(node.center.x, node.center.y)
            center = self.round_coordinate(self.convert_unit_coordinate(center))

            r = self.round_value(self.convert_unit(node.radius))
            if r > 0.0:
                return (
                    f"({center[0]}, {center[1]}) circle ({r}{self.options.output_unit})",
                    [],
                )

        if node.TAG == "ellipse":
            center = Vector2d(node.center.x, node.center.y)
            center = self.round_coordinate(self.convert_unit_coordinate(center))

            rx = self.round_value(self.convert_unit(node.radius[0]))
            ry = self.round_value(self.convert_unit(node.radius[1]))
            if rx > 0.0 and ry > 0.0:
                return (
                    f"({center[0]}, {center[1]}) ellipse ({rx}{self.options.output_unit} and {ry}{self.options.output_unit})",
                    [],
                )

        return "", []

    def _handle_text(self, node):
        if self.options.ignore_text:
            return "", []

        raw_textstr = node.get_text().strip()
        if self.options.texmode == "raw":
            textstr = raw_textstr
        elif self.options.texmode == "math":
            textstr = f"${raw_textstr}$"
        else:
            textstr = escape_texchars(raw_textstr)

        p = Vector2d(node.x, node.y)
        p = self.round_coordinate(self.convert_unit_coordinate(p))

        return (
            f" \node[above right] (node.get_id()) at ({p.x}, {p.y})"
            + "{"
            + f"{textstr}"
            + "}"
        )

    def get_text(self, node):
        """Return content of a text node as string"""
        return etree.tostring(node, method="text").decode("utf-8")

    def _output_group(self, group):
        """Process a group of SVG nodes and return corresponding TikZ code

        The group is processed recursively if it contains sub groups.
        """
        string = ""
        # transform = []
        for node in group:
            if not filter_tag(node):
                continue

            if node.TAG == "g":
                string += self._handle_group(node)
                continue

            if node.TAG == "use":
                node = node.unlink()

            options = []
            goptions = self.convert_svgstyle_to_tikzstyle(node)
            goptions += self.convert_transform_to_tikz(node)

            cmd = []

            if node.TAG == "path":
                # Add indent
                if len(goptions) > 0:
                    optionscode = f"[{','.join(goptions)}]"
                else:
                    optionscode = ""

                pathcode = self.convert_path_to_tikz(node.path)
                if pathcode != "":
                    cmd.append(f"\\path{optionscode} {pathcode}")

            elif node.TAG in [
                "rect",
                "ellipse",
                "circle",
                "line",
                "polygon",
                "polyline",
            ]:
                # Add indent
                pathcode, options = self._handle_shape(node)
                goptions += options
                if len(goptions) > 0:
                    optionscode = f"[{','.join(goptions)}]"
                else:
                    optionscode = ""

                if pathcode != "":
                    if self.options.verbose:
                        cmd.append(f"%{node.get_id()}")
                    cmd.append(f"\\path{optionscode} {pathcode}")

            elif node.TAG in ["text", "flowRoot"]:
                pathcode = self._handle_text(node)

                if pathcode != "":
                    if self.options.verbose:
                        cmd.append(f"%{node.get_id()}\n")
                    cmd.append(f"{pathcode};")

            elif node.TAG == "image":
                pathcode = self._handle_image(node)
                if pathcode != "":
                    if self.options.verbose:
                        cmd.append(f"%{node.get_id()}\n")
                    cmd.append(f"{pathcode}")

            elif node.tag == _ns("symbol"):
                # to implement: handle symbol as reusable code
                cmd = self._handle_group(node)

            else:
                logging.debug("Unhandled element %s", node.tag)
                continue
            cmd = [self.text_indent + c for c in cmd]
            string += "\n".join(cmd) + ";\n\n\n\n"

        if self.options.wrap:
            string = "\n".join(
                wrap(string, 80, subsequent_indent="  ", break_long_words=False)
            )

        return string

    def effect(self):
        """Apply the conversion on the svg and fill the template"""
        string = ""
        nodes = self.svg.selected

        # If no nodes is selected convert whole document.

        root = self.document.getroot()
        if "height" in root.attrib:
            self.height = self.convert_unit(self.svg.viewbox_height)
        if len(nodes) == 0:
            nodes = self.document.getroot()
        # Recursively process list of nodes or root node
        string = self._output_group(nodes)

        # goptions = self.convert_svgstyle_to_tikzstyle(root)
        # transformation = self.convert_transform_to_tikz(root)
        # options = transformation + goptions
        options = []
        # Add necessary boiling plate code to the generated TikZ code.
        codeoutput = self.options.codeoutput
        if len(options) > 0:
            extraoptions = f",\n{','.join(options)}"
        else:
            extraoptions = ""
        if not self.options.crop:
            cropcode = ""
        else:
            cropcode = CROP_TEMPLATE
        if codeoutput == "standalone":
            output = STANDALONE_TEMPLATE % {
                "pathcode": string,
                "colorcode": self.color_code,
                "unit": self.options.output_unit,
                "ysign": "-" if self.options.noreversey else "",
                "cropcode": cropcode,
                "extraoptions": extraoptions,
                "gradientcode": self.gradient_code,
                "scale": self.options.scale,
            }
        elif codeoutput == "figonly":
            output = FIG_TEMPLATE % {
                "pathcode": string,
                "colorcode": self.color_code,
                "unit": self.options.output_unit,
                "ysign": "-" if self.options.noreversey else "",
                "extraoptions": extraoptions,
                "gradientcode": self.gradient_code,
                "scale": self.options.scale,
            }
        else:
            output = string

        self.output_code = output
        if self.options.returnstring:
            return output
        return ""

    def save_raw(self, _):
        """Save the file from the save as menu from inkscape"""
        if self.options.clipboard:
            success = copy_to_clipboard(self.output_code.encode("utf8"))
            if not success:
                logging.error("Failed to put output on clipboard")

        elif self.options.output is not None:
            if isinstance(self.options.output, str):
                with codecs.open(self.options.output, "w", "utf8") as stream:
                    stream.write(self.output_code)
            else:
                self.options.output.write(self.output_code.encode("utf8"))

    def run(self, _args=None, output=sys.stdout.buffer):
        """
        Custom inkscape entry point to remove agr processing
        """
        try:
            if isinstance(self.options.input_file, str):
                if "DOCUMENT_PATH" not in os.environ:
                    os.environ["DOCUMENT_PATH"] = self.options.input_file

            if self.options.output is None:
                self.options.output = output
            self.load_raw()
            self.save_raw(self.effect())
        except inkex.utils.AbortExtension as err:
            inkex.utils.errormsg(str(err))
            sys.exit(inkex.utils.ABORT_STATUS)
        finally:
            self.clean_up()

    def convert(self, svg_file=None, no_output=False, **kwargs):
        """Convert SVG file to tikz path"""
        self.options = self.arg_parser.parse_args()

        if self.options.printversion:
            print_version_info()
            return ""

        if svg_file is not None:
            self.options.input_file = svg_file

        self.options.__dict__.update(kwargs)

        if self.options.input_file is None:
            print("No input file -- aborting")
            return ""
        if no_output:
            self.run(output=None)
        else:
            self.run()

        if self.options.returnstring:
            return self.output_code
        return ""


def convert_file(svg_file, no_output=True, **kwargs):
    """
    Convert SVG file to tikz code
    - Svg file can be a str representing the path to a file
    - A steam object of a file
    """
    effect = TikZPathExporter(inkscape_mode=False)
    return effect.convert(svg_file, no_output, returnstring=True, **kwargs)


def convert_svg(svg_source, **kwargs):
    """
    Convert a SVG to tikz code
    - svg source is a str representing a svg
    """

    # TODO better handling
    effect = TikZPathExporter(inkscape_mode=False)
    tikz_code = effect.convert(io.StringIO(svg_source), **kwargs)
    return tikz_code


def main_inkscape():
    """Inkscape interface"""
    # Create effect instance and apply it.
    effect = TikZPathExporter(inkscape_mode=True)
    effect.run()


def print_version_info():
    """Print the version of svg2tikz"""
    print(f"svg2tikz version {__version__}")


def main_cmdline(**kwargs):
    """Main command line interface"""
    effect = TikZPathExporter(inkscape_mode=False)
    effect.convert(**kwargs)


if __name__ == "__main__":
    main_inkscape()
