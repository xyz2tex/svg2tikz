#!/usr/bin/env python/
# -*- coding: utf-8 -*-

"""\
Convert SVG to TikZ/PGF commands for use with (La)TeX

This script is an Inkscape extension for exporting from SVG to (La)TeX. The
extension recreates the SVG drawing using TikZ/PGF commands, a high quality TeX
macro package for creating graphics programmatically.

The script is tailored to Inkscape SVG, but can also be used to convert arbitrary
SVG files from the command line.

Author: Kjell Magne Fauske, Devillez Louis
"""

import platform

__version__ = "3.0.0"
__author__ = "Devillez Louis, Kjell Magne Fauske"
__maintainer__ = "Deville Louis"
__email__ = "louis.devillez@gmail.com"


import sys

from textwrap import wrap
import codecs
import io
import os
from subprocess import Popen, PIPE

from math import sin, cos, atan2, radians, degrees
from math import pi as mpi

import logging

import ctypes
import inkex
from inkex.transforms import Vector2d
from lxml import etree

try:
    SYS_OUTPUT_BUFFER = sys.stdout.buffer
except AttributeError:
    logging.warning("Sys has no output buffer, redirecting to None")
    SYS_OUTPUT_BUFFER = None

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
    "gray",
]

LIST_OF_SHAPES = [
    "path",
    "rect",
    "circle",
    "ellipse",
    "line",
    "polyline",
    "polygon",
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


def filter_tag(node):
    """
    A function to see if a node should be draw or not
    """
    # pylint: disable=comparison-with-callable
    # As it is done in lxml
    if node.tag == etree.Comment:
        return False
    if node.TAG in [
        "desc",
        "namedview",
        "defs",
        "svg",
        "symbol",
        "title",
        "style",
        "metadata",
    ]:
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
    r"""xscale=\globalscale, every node/.append style={scale=\globalscale}, inner sep=0pt, outer sep=0pt%(extraoptions)s]
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
    r"""xscale=\globalscale, every node/.append style={scale=\globalscale}, inner sep=0pt, outer sep=0pt%(extraoptions)s]
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
    "text-anchor": (
        "anchor",
        DICT,
        {"start": "south west", "middle": "south", "end": "south east"},
    ),
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
    ang = radians(ang)

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

    ang0 = degrees(ang_0)
    ang1 = degrees(ang_1)

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
    """
    Convert an svg arrow_name to tikz name of the arrow
    """
    strip_name = arrow_name.split("url")[1][1:-1]

    if "Arrow1" in strip_name:
        return "latex"
    if "Arrow2" in strip_name:
        return "stealth"
    if "Stop" in strip_name:
        return "|"
    return "latex"


def marking_interpret(marker):
    """
    Interpret the arrow from its name and its direction and convert it to tikz code
    """
    raw_marker = ""
    if marker:
        arrow_style = parse_arrow_style(marker)
        raw_marker = arrow_style[:]
        if "end" in marker:
            raw_marker += " reversed"
    return raw_marker


def options_to_str(options: list) -> str:
    """
    Convert a list of options to a str with comma separated value.
    If the list is empty, return an empty str
    """
    return f"[{','.join(options)}]" if len(options) > 0 else ""


def return_arg_parser_doc():
    """
    Methode to return the arg parser of TikzPathExporter to help generate the doc
    """
    tzp = TikZPathExporter()
    return tzp.arg_parser


# pylint: disable=too-many-ancestors
class TikZPathExporter(inkex.Effect, inkex.EffectExtension):
    """Class to convert a svg to tikz code"""

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
        self.args_parsed = False

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

        parser.add_argument(
            "--round-number",
            dest="round_number",
            type=int,
            default=4,
            help="Number of significative number after the decimal",
        )

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
            default="",
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

    def convert_unit(self, value: float) -> float:
        """Convert value from the user unit to the output unit which is an option"""
        ret = self.svg.unit_to_viewport(value, self.options.output_unit)
        return ret

    def convert_unit_coord(self, coord: Vector2d, update_height=True) -> Vector2d:
        """
        Convert a coord (Vector2D)) from the user unit to the output unit
        """
        y = self.convert_unit(coord[1])
        return Vector2d(
            self.convert_unit(coord[0]),
            self.update_height(y) if update_height else y,
        )

    def convert_unit_coords(self, coords, update_height=True):
        """
        Convert a list of coords (Vector2D)) from the user unit to the output unit
        """
        return [self.convert_unit_coord(coord, update_height) for coord in coords]

    def round_value(self, value):
        """Round a value with respect to the round number of the class"""
        return round(value, self.options.round_number)

    def round_coord(self, coord):
        """Round a coordinante(Vector2D) with respect to the round number of the class"""
        return Vector2d(self.round_value(coord[0]), self.round_value(coord[1]))

    def round_coords(self, coords):
        """Round a coordinante(Vector2D) with respect to the round number of the class"""
        return [self.round_coord(coord) for coord in coords]

    def rotate_coord(self, coord: Vector2d, angle: float) -> Vector2d:
        """
        rotate a coordinate around (0,0) of angle radian
        """
        return Vector2d(
            coord.x * cos(angle) - coord.y * sin(angle),
            coord.x * sin(angle) + coord.y * cos(angle),
        )

    def coord_to_tz(self, coord: Vector2d) -> str:
        """
        Convert a coord (Vector2d) which is round and converted to tikz code
        """
        c = self.round_coord(coord)
        return f"({c.x}, {c.y})"

    def update_height(self, y_val):
        """Compute the distance between the point and the bottom of the document"""
        if not self.options.noreversey:
            return self.height - y_val
        return y_val

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

    # def _convert_gradient(self, gradient_node, gradient_tikzname):
    # """Convert an SVG gradient to a PGF gradient"""

    # # http://www.w3.org/TR/SVG/pservers.html
    # def bpunit(offset):
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

    # return ""

    # def _handle_gradient(self, gradient_ref):
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
    # return []

    def _handle_markers(self, style):
        """
        Convert marking style from svg to tikz code
        """
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

    def _handle_dasharray(self, style):
        """
        Convert dasharry style from svg to tikz code
        """
        dasharray = style.get("stroke-dasharray")

        if dasharray is None or dasharray == "none":
            return []

        lengths = dasharray.replace(",", " ").replace("  ", " ").split(" ")
        dashes = []
        for idx, length in enumerate(lengths):
            l = self.round_value(self.convert_unit(float(length)))
            lenstr = f"{l}{self.options.output_unit}"
            if idx % 2:
                dashes.append(f"off {lenstr}")
            else:
                dashes.append(f"on {lenstr}")

        return [f"dash pattern={' '.join(dashes)}"]

    def get_shape_inside(self, node=None):
        """
        Get back the shape from the shape_inside style attribute
        """
        style = node.specified_style()
        url = style.get("shape-inside")
        if url is None:
            return None
        shape = inkex.properties.match_url_and_return_element(url, self.svg)
        return shape

    def style_to_tz(self, node=None):
        """
        Convert the style from the svg to the option to apply to tikz code
        """

        style = node.specified_style()

        # No display
        if style.get("display") == "none" or not node.is_visible:
            if node.TAG == "g":
                return ["none"]
            return []

        options = []

        # Stroke and fill
        for use_path in (
            [("fill", "text")]
            if node.TAG == "text"
            else [("stroke", "draw"), ("fill", "fill")]
        ):
            value = style.get(use_path[0])
            if value != "none" and value is not None:
                options.append(
                    f"{use_path[1]}={self.convert_color_to_tikz(style.get_color(use_path[0]))}"
                )

            if value is None and use_path[0] == "fill" and node.TAG in LIST_OF_SHAPES:
                # svg shapes with no fill option should fill by black
                # https://www.w3.org/TR/2011/REC-SVG11-20110816/painting.html#FillProperty
                options.append("fill")

        # Other props
        for svgname, tikzdata in PROPERTIES_MAP.items():
            tikzname, valuetype, data = tikzdata
            value = style.get(svgname)

            if value is None or value == "none":
                continue

            if valuetype in [SCALE, FACTOR]:
                val = float(value)

                if val < 1 and valuetype == FACTOR:
                    continue

                if val != 1:
                    options.append(f"{tikzname}={self.round_value(float(value))}")
            elif valuetype == DICT:
                if tikzname:
                    options.append(f"{tikzname}={data.get(value,'')}")
                else:
                    options.append(data.get(value, ""))
            elif valuetype == DIMENSION:
                if value and value != data:
                    options.append(
                        f"{tikzname}="
                        f"{self.round_value(self.convert_unit(value))}"
                        f"{self.options.output_unit}"
                    )

        # Arrow marker handling
        options += self._handle_markers(style)

        # Dash-array
        options += self._handle_dasharray(style)

        return options

    def trans_to_tz(self, node=None, is_node=False):
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

            # Translation
            if trans.is_translate():
                tr = self.convert_unit_coord(Vector2d(trans.e, trans.f), False)

                # Global scale do not impact transform
                if not self.options.noreversey or is_node:
                    tr.y *= -1

                tr.x *= self.options.scale
                tr.y *= self.options.scale

                options.append("shift={" + self.coord_to_tz(tr) + "}")

            # Rotation
            elif trans.is_rotate():
                # get angle
                ang = -self.round_value(trans.rotation_degrees())

                # If reverse coord, we rotate around old origin
                if not self.options.noreversey:
                    options.append(
                        "rotate around={"
                        + f"{ang}:{self.coord_to_tz(Vector2d(0.0, self.update_height(0)))}"
                        + "}"
                    )
                else:
                    options.append(f"rotate={ang}")
            elif trans.is_scale():
                x = self.round_value(trans.a)
                y = self.round_value(trans.d)

                if x == y:
                    options.append(f"scale={x}")
                else:
                    options.append(f"xscale={x},yscale={y}")

            elif "matrix" in str(trans):
                # print(trans)
                tr = self.convert_unit_coord(Vector2d(trans.e, trans.f), False)
                a = self.round_value(trans.a)
                b = self.round_value(trans.b)
                c = self.round_value(trans.c)
                d = self.round_value(trans.d)

                # globalscale do not impact transform
                if not self.options.noreversey or is_node:
                    tr.y *= -1
                    b *= -1
                    c *= -1

                if not self.options.noreversey and not is_node:
                    tr.x += -c * self.update_height(0)
                    tr.y += (1 - d) * self.update_height(0)

                tr.x *= self.options.scale
                tr.y *= self.options.scale
                options.append(f"cm={{ {a},{b},{c}" f",{d},{self.coord_to_tz(tr)}}}")

            # Not possible to get them directly
            # elif "skewX" in str(trans):
            # options.append(f"xslant={math.tan(trans.c * math.pi / 180)}")
            # elif "skewY" in str(trans):
            # options.append(f"yslant={math.tan(trans.b * math.pi / 180)}")
            # elif "scale" in str(trans):
            # if trans.a == trans.d:
            # options.append(f"scale={trans.a}")
            # else:
            # options.append(f"xscale={trans.a},yscale={trans.d}")
        return options

    def _handle_group(self, groupnode):
        """
        Convert a svg group to tikzcode
        """
        options = self.style_to_tz(groupnode) + self.trans_to_tz(groupnode)

        old_indent = self.text_indent

        if len(options) > 0:
            self.text_indent += TEXT_INDENT

        group_id = groupnode.get_id()
        code = self._output_group(groupnode)

        self.text_indent = old_indent

        if code == "":
            return ""

        extra = ""
        if self.options.verbose and group_id:
            extra = f"%% {group_id}"

        hide = "none" in options

        s = ""
        if len(options) > 0 or self.options.verbose:
            # Remove it from the list
            if hide or self.options.verbose:
                if "none" in options:
                    options.remove("none")

            pstyles = [",".join(options)]

            if "opacity" in pstyles[0]:
                pstyles.append("transparency group")

            s += self.text_indent + "\\begin{scope}"
            s += f"[{','.join(pstyles)}]{extra}\n{code}"
            s += self.text_indent + "\\end{scope}\n"

            if hide:
                s = "%" + s.replace("\n", "\n%")[:-1]
        else:
            s = code
        return s

    def _handle_switch(self, groupnode):
        """
        Convert a svg switch to tikzcode
        All the elements are returned for now
        """
        options = self.trans_to_tz(groupnode)

        old_indent = self.text_indent

        if len(options) > 0:
            self.text_indent += TEXT_INDENT

        group_id = groupnode.get_id()
        code = self._output_group(groupnode)

        self.text_indent = old_indent

        if code == "":
            return ""

        extra = ""
        if self.options.verbose and group_id:
            extra = f"%% {group_id}"

        hide = "none" in options

        s = ""
        if len(options) > 0 or self.options.verbose:
            # Remove it from the list
            if hide or self.options.verbose:
                options.remove("none")

            pstyles = [",".join(options)]

            if "opacity" in pstyles[0]:
                pstyles.append("transparency group")

            s += self.text_indent + "\\begin{scope}"
            s += f"[{','.join(pstyles)}]{extra}\n{code}"
            s += self.text_indent + "\\end{scope}\n"

            if hide:
                s = "%" + s.replace("\n", "\n%")[:-1]
        else:
            s = code
        return s

    def _handle_image(self, node):
        """Handles the image tag and returns tikz code"""
        p = self.convert_unit_coord(Vector2d(node.left, node.top))

        width = self.round_value(self.convert_unit(node.width))
        height = self.round_value(self.convert_unit(node.height))

        href = node.get("xlink:href")
        isvalidhref = href is not None and "data:image/png;base64" not in href
        if not isvalidhref:
            href = "base64 still not supported"
            return f"% Image {node.get_id()} not included. Base64 still not supported"

        if self.options.latexpathtype:
            href = href.replace(self.options.removeabsolute, "")

        return (
            r"\node[anchor=north west,inner sep=0, scale=\globalscale]"
            + f" ({node.get_id()}) at {self.coord_to_tz(p)} "
            + r"{\includegraphics[width="
            + f"{width}{self.options.output_unit},height={height}{self.options.output_unit}]"
            + "{"
            + href
            + "}}"
        )

    def convert_path_to_tikz(self, path):
        """
        Convert a path from inkex to tikz code
        """
        s = ""

        for command in path.proxy_iterator():
            letter = command.letter.upper()

            # transform coords
            tparams = self.convert_unit_coords(command.control_points)
            # moveto
            if letter == "M":
                s += self.coord_to_tz(tparams[0])

            # lineto
            elif letter in ["L", "H", "V"]:
                s += f" -- {self.coord_to_tz(tparams[0])}"

            # cubic bezier curve
            elif letter == "C":
                s += f".. controls {self.coord_to_tz(tparams[0])} and {self.coord_to_tz(tparams[1])} .. {self.coord_to_tz(tparams[2])}"

            # quadratic bezier curve
            elif letter == "Q":
                # http://fontforge.sourceforge.net/bezier.html

                # current_pos is qp0
                qp1, qp2 = tparams
                cp1 = current_pos + (2.0 / 3.0) * (qp1 - current_pos)
                cp2 = cp1 + (qp2 - current_pos) / 3.0
                s += f" .. controls {self.coord_to_tz(cp1)} and {self.coord_to_tz(cp2)} .. {self.coord_to_tz(qp2)}"
            # close path
            elif letter == "Z":
                s += " -- cycle"
            # arc
            elif letter == "A":
                # Do not shift other values
                command = command.to_absolute()

                r = Vector2d(
                    self.convert_unit(command.rx), self.convert_unit(command.ry)
                )
                # Get acces to this vect2D ?
                pos = Vector2d(command.x, command.y)
                pos = self.convert_unit_coord(pos)
                sweep = command.sweep

                if not self.options.noreversey:
                    sweep = 1 - sweep
                    r.y *= -1

                start_ang_o, end_ang_o, r = calc_arc(
                    current_pos,
                    r,
                    command.x_axis_rotation,
                    command.large_arc,
                    sweep,
                    pos,
                )
                r = self.round_coord(r)

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
            # Get the last position
            current_pos = tparams[-1]
        return s

    def _handle_shape(self, node):
        """Extract shape data from node"""
        options = []
        if node.TAG == "rect":
            inset = node.rx or node.ry
            x = node.left
            y = node.top
            corner_a = self.convert_unit_coord(Vector2d(x, y))

            width = node.width
            height = node.height

            # map from svg to tikz
            if width == 0.0 or height == 0.0:
                return "", []

            corner_b = self.convert_unit_coord(Vector2d(x + width, y + height))

            if inset and abs(inset) > 1e-5:
                unit_to_scale = self.round_value(self.convert_unit(inset))
                options = [f"rounded corners={unit_to_scale}{self.options.output_unit}"]

            return (
                f"{self.coord_to_tz(corner_a)} rectangle {self.coord_to_tz(corner_b)}",
                options,
            )

        if node.TAG in ["polyline", "polygon"]:
            points = node.get_path().control_points
            points = self.round_coords(self.convert_unit_coords(points))
            points = [f"({vec.x}, {vec.y})" for vec in points]

            path = " -- ".join(points)

            if node.TAG == "polygon":
                path += "-- cycle"

            return f"{path};", []

        if node.TAG == "line":
            p_a = self.convert_unit_coord(Vector2d(node.x1, node.y1))
            p_b = self.convert_unit_coord(Vector2d(node.x2, node.y2))
            # check for zero lenght line
            if not ((p_a[0] == p_b[0]) and (p_a[1] == p_b[1])):
                return f"{self.coord_to_tz(p_a)} -- {self.coord_to_tz(p_b)}", []

        if node.TAG == "circle":
            center = self.convert_unit_coord(Vector2d(node.center.x, node.center.y))

            r = self.round_value(self.convert_unit(node.radius))
            if r > 0.0:
                return (
                    f"{self.coord_to_tz(center)} circle ({r}{self.options.output_unit})",
                    [],
                )

        if node.TAG == "ellipse":
            center = Vector2d(node.center.x, node.center.y)
            center = self.round_coord(self.convert_unit_coord(center))
            r = self.round_coord(self.convert_unit_coord(node.radius, False))
            if r.x > 0.0 and r.y > 0.0:
                return (
                    f"{self.coord_to_tz(center)} ellipse ({r.x}{self.options.output_unit} and {r.y}{self.options.output_unit})",
                    [],
                )

        return "", []

    def _handle_text(self, node):
        if self.options.ignore_text:
            return "", []

        raw_textstr = node.get_text(" ").strip()
        if self.options.texmode == "raw":
            textstr = raw_textstr
        elif self.options.texmode == "math":
            textstr = f"${raw_textstr}$"
        else:
            textstr = escape_texchars(raw_textstr)

        shape = self.get_shape_inside(node)
        if shape is None:
            p = Vector2d(node.x, node.y)
        else:
            # TODO Not working yet
            p = Vector2d(shape.left, shape.bottom)

        # We need to apply a rotation to coord
        # In tikz rotate only rotate the node, not its coordinate
        ang = 0.0
        trans = node.transform
        if trans.is_rotate():
            # get angle
            ang = atan2(trans.b, trans.a)
        p = self.convert_unit_coord(self.rotate_coord(p, ang))

        # scale do not impact node
        if self.options.noreversey:
            p.y *= -1

        return f"({node.get_id()}) at {self.coord_to_tz(p)}" + "{" + f"{textstr}" + "}"

    def get_text(self, node):
        """Return content of a text node as string"""
        return etree.tostring(node, method="text").decode("utf-8")

    # pylint: disable=too-many-branches
    def _output_group(self, group):
        """Process a group of SVG nodes and return corresponding TikZ code

        The group is processed recursively if it contains sub groups.
        """
        string = ""
        for node in group:
            if not filter_tag(node):
                continue

            if node.TAG == "use":
                node = node.unlink()

            if node.TAG == "switch":
                string += self._handle_switch(node)
                continue

            if node.TAG == "g":
                string += self._handle_group(node)
                continue
            try:
                goptions = self.style_to_tz(node) + self.trans_to_tz(
                    node, node.TAG in ["text", "flowRoot", "image"]
                )
            except AttributeError as msg:
                attr = msg.args[0].split("attribute")[1].split(".")[0]
                logging.warning("%s attribute cannot be represented", attr)

            pathcode = ""

            if self.options.verbose:
                string += self.text_indent + f"%{node.get_id()}\n"

            if node.TAG == "path":
                optionscode = options_to_str(goptions)

                pathcode = f"\\path{optionscode} {self.convert_path_to_tikz(node.path)}"

            elif node.TAG in LIST_OF_SHAPES:
                # Add indent
                pathcode, options = self._handle_shape(node)

                optionscode = options_to_str(goptions + options)

                pathcode = f"\\path{optionscode} {pathcode}"

            elif node.TAG in ["text", "flowRoot"]:
                pathcode = self._handle_text(node)

                # Check if the anchor is set, otherwise default to south west
                contains_anchor = False
                for goption in goptions:
                    if goption.startswith("anchor="):
                        contains_anchor = True
                if not contains_anchor:
                    goptions += ["anchor=south west"]

                optionscode = options_to_str(goptions)
                # Convert a rotate around to a rotate option
                if "rotate around={" in optionscode:
                    splited_options = optionscode.split("rotate around={")
                    ang = splited_options[1].split(":")[0]
                    optionscode = (
                        splited_options[0]
                        + f"rotate={ang}"
                        + splited_options[1].split("}", 1)[1]
                    )

                pathcode = f"\\node{optionscode} {pathcode}"

            elif node.TAG == "image":
                pathcode = self._handle_image(node)

            # elif node.TAG == "symbol":
            # # to implement: handle symbol as reusable code
            # pass

            else:
                logging.debug("Unhandled element %s", node.tag)
                continue

            if self.options.wrap:
                string += "\n".join(
                    wrap(
                        self.text_indent + pathcode,
                        80,
                        subsequent_indent="  ",
                        break_long_words=False,
                        drop_whitespace=False,
                        replace_whitespace=False,
                    )
                )
            else:
                string += self.text_indent + pathcode

            string += ";\n\n\n\n"

        return string

    def effect(self):
        """Apply the conversion on the svg and fill the template"""
        string = ""

        if not self.options.indent:
            self.text_indent = ""

        root = self.document.getroot()
        if "height" in root.attrib:
            self.height = self.convert_unit(self.svg.viewbox_height)
        nodes = self.svg.selected
        # If no nodes is selected convert whole document.

        if len(nodes) == 0:
            nodes = root

        # Recursively process list of nodes or root node
        string = self._output_group(nodes)

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
                out = self.output_code

                if isinstance(self.options.output, io.BufferedWriter):
                    out = out.encode("utf8")

                self.options.output.write(out)

    def run(self, args=None, output=SYS_OUTPUT_BUFFER):
        """
        Custom inkscape entry point to remove agr processing
        """
        try:
            # We parse it ourself in command line but letting it with inkscape
            if not self.args_parsed:
                if args is None:
                    args = sys.argv[1:]

                self.parse_arguments(args)

            if (
                isinstance(self.options.input_file, str)
                and "DOCUMENT_PATH" not in os.environ
            ):
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
        self.args_parsed = True

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


def convert_file(svg_file, no_output=True, returnstring=True, **kwargs):
    """
    Convert SVG file to tikz code

    :param svg_file: input file representend by a path or a stream
    :type svg_file: str, stream object
    :param no_output: If the output is redirected to None (default: True)
    :type no_output: Bool
    :param returnstring: if the output code should be returned
    :type returnstring: Bool
    :param kwargs: See argparse output / svg2tikz -h / commandline documentation
    :return: tikz code or empty string
    :rtype: str
    """

    kwargs["returnstring"] = returnstring
    effect = TikZPathExporter(inkscape_mode=False)
    return effect.convert(svg_file, no_output, **kwargs)


def convert_svg(svg_source, no_output=True, returnstring=True, **kwargs):
    """
    Convert SVG to tikz code

    :param svg_source: content of svg file
    :type svg_source: str
    :param no_output: If the output is redirected to None (default: True)
    :type no_output: Bool
    :param returnstring: if the output code should be returned
    :type returnstring: Bool
    :param kwargs: See argparse output / svg2tikz -h / commandline documentation
    :return: tikz code or empty string
    :rtype: str
    """

    kwargs["returnstring"] = returnstring
    effect = TikZPathExporter(inkscape_mode=False)
    return effect.convert(io.StringIO(svg_source), no_output, **kwargs)


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
