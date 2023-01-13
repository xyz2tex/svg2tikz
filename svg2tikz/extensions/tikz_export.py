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

__version__ = '1.0.0dev'
__author__ = 'Kjell Magne Fauske'

# Todo:
# Basic functionality:

# Stroke properties
# - markers (map from Inkscape to TikZ arrow styles. No 1:1 mapping)
# Fill properties
#   - linear shading
#   - radial shading
# Paths:
#
# Text
#
# Other stuff:
# - Better output code formatting!
# - Add a + prefix to coordinates to speed up pgf parsing
# - Transformations
#   - default property values.The initial fill property is set to 'black'.
#     This is currently not handled.
# - ConTeXt template support.


import sys

from textwrap import wrap
from copy import deepcopy
import codecs
import io
import copy
import os
from subprocess import Popen, PIPE
from lxml import etree

try:
    # This should work when run as an Inkscape extension
    import inkex
    # import simplepath
    # import simplestyle
except ImportError:
    # Use bundled files when run as a module or command line tool
    # from svg2tikz.inkex import inkex
    import svg2tikz.inkex as inkex
    # from /vg2tikz.inkex import simplepath
    # from svg2tikz.inkex import simplestyle

import re
import math

from math import sin, cos, atan2
import logging

#### Utility functions and classes

SPECIAL_TEX_CHARS = ['$', '\\', '%', '_', '#', '{', r'}', '^', '&']
SPECIAL_TEX_CHARS_REPLACE = [r'\$', r'$\backslash$', r'\%', r'\_', r'\#',
                             r'\{', r'\}', r'\^{}', r'\&']
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


class Bunch(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __str__(self):
        return self.__dict__.__str__()

    def __repr__(self):
        return self.__dict__.__repr__()


def copy_to_clipboard(text):
    """Copy text to the clipboard

    Returns True if successful. False otherwise.
    """

    import sys
    if sys.version < '3':
        text_type = unicode
    else:
        text_type = str

    def _do_windows_clipboard(text):
        # from http://pylabeditor.svn.sourceforge.net/viewvc/pylabeditor/trunk/src/shells.py?revision=82&view=markup
        import ctypes

        CF_UNICODETEXT = 13
        GHND = 66

        ctypes.windll.kernel32.GlobalAlloc.restype = ctypes.c_void_p
        ctypes.windll.kernel32.GlobalLock.restype = ctypes.c_void_p

        text = text_type(text, 'utf8')
        bufferSize = (len(text)+1)*2
        hGlobalMem = ctypes.windll.kernel32.GlobalAlloc(ctypes.c_uint(GHND), ctypes.c_size_t(bufferSize))
        lpGlobalMem = ctypes.windll.kernel32.GlobalLock(ctypes.c_void_p(hGlobalMem))
        ctypes.cdll.msvcrt.memcpy( ctypes.c_void_p(lpGlobalMem), ctypes.c_wchar_p(text), ctypes.c_int(bufferSize))
        ctypes.windll.kernel32.GlobalUnlock(ctypes.c_void_p(hGlobalMem))
        if ctypes.windll.user32.OpenClipboard(0):
           ctypes.windll.user32.EmptyClipboard()
           ctypes.windll.user32.SetClipboardData( ctypes.c_int(CF_UNICODETEXT), ctypes.c_void_p(hGlobalMem) )
           ctypes.windll.user32.CloseClipboard()
           return True
        else:
           return False

    def _call_command(command, text):
        # see https://bugs.launchpad.net/ubuntu/+source/inkscape/+bug/781397/comments/2
        try:
            devnull = os.open(os.devnull, os.O_RDWR)
            p = Popen(command, stdin=PIPE, stdout=devnull, stderr=devnull)
            out, err = p.communicate(text)
            if not p.returncode:
                return True

        except OSError:
            pass
        return False

    def _do_linux_clipboard(text):
        # try xclip first, then xsel
        xclip_cmd = ['xclip', '-selection', 'clipboard']
        success = _call_command(xclip_cmd, text)
        if success:
            return True

        xsel_cmd = ['xsel']
        success = _call_command(xsel_cmd, text)
        return success

    def _do_osx_clipboard(text):
        pbcopy_cmd = ['pbcopy']
        return _call_command(pbcopy_cmd, text)
        # try os /linux

    if os.name == 'nt' or platform.system() == 'Windows':
        return _do_windows_clipboard(text)
    elif os.name == 'mac' or platform.system() == 'Darwin':
        return _do_osx_clipboard(text)
    else:
        return _do_linux_clipboard(text)


def nsplit(seq, n=2):
    """Split a sequence into pieces of length n

    If the length of the sequence isn't a multiple of n, the rest is discarded.
    Note that nsplit will strings into individual characters.

    Examples:
    >>> nsplit('aabbcc')
    [('a', 'a'), ('b', 'b'), ('c', 'c')]
    >>> nsplit('aabbcc',n=3)
    [('a', 'a', 'b'), ('b', 'c', 'c')]

    # Note that cc is discarded
    >>> nsplit('aabbcc',n=4)
    [('a', 'a', 'b', 'b')]
    """
    return [xy for xy in zip(*[iter(seq)] * n)]


def chunks(s, cl):
    """Split a string or sequence into pieces of length cl and return an iterator
    """
    for i in range(0, len(s), cl):
        yield s[i:i + cl]


# Adapted from Mark Pilgrim's Dive into Python book
# http://diveintopython.org/scripts_and_streams/index.html#kgp.openanything
def open_anything(source):
    # try to open with urllib (if source is http, ftp, or file URL)
    try:
        from urllib import urlopen
        to_unicode = unicode
    except ImportError:  # Python3
        from urllib.request import urlopen
        import urllib.error
        to_unicode = str

    try:
        return urlopen(source)
    except (IOError, OSError, ValueError):
        pass

        # try to open with native open function (if source is pathname)
    try:
        return open(source)
    except (IOError, OSError):
        pass

        # treat source as string
    import io

    return io.StringIO(to_unicode(source))


def _ns(element_name, name_space='svg'):
    return inkex.addNS(element_name, name_space)


#### Output configuration section

TEXT_INDENT = "  "

CROP_TEMPLATE = r"""
\usepackage[active,tightpage]{preview}
\PreviewEnvironment{tikzpicture}
"""

# Templates
STANDALONE_TEMPLATE = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{tikz}
%(cropcode)s
\begin{document}
%(colorcode)s
%(gradientcode)s
\def \globalscale {%(scale)f}
\begin{tikzpicture}[y=0.80pt, x=0.80pt, yscale=-\globalscale, xscale=\globalscale, inner sep=0pt, outer sep=0pt%(extraoptions)s]
%(pathcode)s
\end{tikzpicture}
\end{document}
"""

FIG_TEMPLATE = r"""
%(colorcode)s
%(gradientcode)s
\def \globalscale {%(scale)f}
\begin{tikzpicture}[y=0.80pt, x=0.80pt, yscale=-\globalscale, xscale=\globalscale, inner sep=0pt, outer sep=0pt%(extraoptions)s]
%(pathcode)s
\end{tikzpicture}
"""

SCALE = 'scale'
DICT = 'dict'
DIMENSION = 'dimension'
FACTOR = 'factor'  # >= 1

# Map Inkscape/SVG stroke and fill properties to corresponding TikZ options.
# Format:
#   'svg_name' : ('tikz_name', value_type, data)
PROPERTIES_MAP = {
    'opacity': ('opacity', SCALE, ''),
    # filling
    'fill-opacity': ('fill opacity', SCALE, ''),
    'fill-rule': ('', DICT,
                  dict(nonzero='nonzero rule', evenodd='even odd rule')),
    # stroke
    'stroke-opacity': ('draw opacity', SCALE, ''),
    'stroke-linecap': ('line cap', DICT,
                       dict(butt='butt', round='round', square='rect')),
    'stroke-linejoin': ('line join', DICT,
                        dict(miter='miter', round='round', bevel='bevel')),
    'stroke-width': ('line width', DIMENSION, ''),
    'stroke-miterlimit': ('miter limit', FACTOR, ''),
    'stroke-dashoffset': ('dash phase', DIMENSION, '0')
}

# default values according to the SVG spec.
DEFAULT_PAINTING_VALUES = {
    # fill
    'fill': 'black',
    'fill-rule': 'nonzero',
    'fill-opacity': 1,
    # stroke
    'stroke': 'none',
    'stroke-width': 1,
    'stroke-linecap': 'butt',
    'stroke-linejoin': 'miter',
    'stroke-miterlimit': 4,
    'stroke-dasharray': 'none',
    'stroke-dashoffset': 0,
    'stroke-opacity': 1,
}

STROKE_PROPERTIES = set([
    'stroke', 'stroke-width', 'stroke-linecap',
    'stroke-linejoin', 'stroke-miterlimit',
    'stroke-dasharray', 'stroke-dashoffset',
    'stroke-opacity',
])

FILL_PROPERTIES = set([
    'fill', 'fill-rule', 'fill-opacity',
])


# The calc_arc function is based on the calc_arc function in the
# paths_svg2obj.py script bundled with Blender 3D
# Copyright (c) jm soler juillet/novembre 2004-april 2007,
def calc_arc(cpx, cpy, rx, ry, ang, fa, fs, x, y):
    """
    Calc arc paths
    """
    PI = math.pi
    ang = math.radians(ang)
    rx = abs(rx)
    ry = abs(ry)
    px = abs((cos(ang) * (cpx - x) + sin(ang) * (cpy - y)) * 0.5) ** 2.0
    py = abs((cos(ang) * (cpy - y) - sin(ang) * (cpx - x)) * 0.5) ** 2.0
    rpx = rpy = 0.0
    if abs(rx) > 0.0:
        rpx = px / (rx ** 2.0)
    if abs(ry) > 0.0:
        rpy = py / (ry ** 2.0)
    pl = rpx + rpy
    if pl > 1.0:
        pl = pl ** 0.5
        rx *= pl
        ry *= pl
    carx = sarx = cary = sary = 0.0
    if abs(rx) > 0.0:
        carx = cos(ang) / rx
        sarx = sin(ang) / rx
    if abs(ry) > 0.0:
        cary = cos(ang) / ry
        sary = sin(ang) / ry
    x0 = carx * cpx + sarx * cpy
    y0 = (-sary) * cpx + cary * cpy
    x1 = carx * x + sarx * y
    y1 = (-sary) * x + cary * y
    d = (x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0)
    if abs(d) > 0.0:
        sq = 1.0 / d - 0.25
    else:
        sq = -0.25
    if sq < 0.0:
        sq = 0.0
    sf = sq ** 0.5
    if fs == fa:
        sf = -sf
    xc = 0.5 * (x0 + x1) - sf * (y1 - y0)
    yc = 0.5 * (y0 + y1) + sf * (x1 - x0)
    ang_0 = atan2(y0 - yc, x0 - xc)
    ang_1 = atan2(y1 - yc, x1 - xc)
    ang_arc = ang_1 - ang_0
    if ang_arc < 0.0 and fs == 1:
        ang_arc += 2.0 * PI
    elif ang_arc > 0.0 and fs == 0:
        ang_arc -= 2.0 * PI

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

    return ang0, ang1, rx, ry


def parse_transform(transform):
    """Parse a transformation attribute and return a list of transformations"""
    # Based on the code in parseTransform in the simpletransform.py module.
    # Copyright (C) 2006 Jean-Francois Barraud
    # Reimplemented here due to several bugs in the version shipped with
    # Inkscape 0.46

    if not transform:
        return []
    stripped_transform = transform.strip()
    result = re.match("(translate|scale|rotate|skewX|skewY|matrix)\s*\(([^)]*)\)\s*,?", stripped_transform)
    if result is None:
        raise SyntaxError("Invalid transformation " + transform)

    transforms = []
    # -- translate --
    if result.group(1) == "translate":
        args = result.group(2).replace(',', ' ').split()
        dx = float(args[0])
        if len(args) == 1:
            dy = 0.0
        else:
            dy = float(args[1])
        matrix = [[1, 0, dx], [0, 1, dy]]
        transforms.append(['translate', (dx, dy)])
        # -- scale --
    if result.group(1) == "scale":
        args = result.group(2).replace(',', ' ').split()
        sx = float(args[0])
        if len(args) == 1:
            sy = sx
        else:
            sy = float(args[1])
        matrix = [[sx, 0, 0], [0, sy, 0]]
        transforms.append(['scale', (sx, sy)])
        # -- rotate --
    if result.group(1) == "rotate":
        args = result.group(2).replace(',', ' ').split()
        a = float(args[0])  # *math.pi/180
        if len(args) == 1:
            cx, cy = (0.0, 0.0)
        else:
            cx, cy = list(map(float, args[1:]))
        matrix = [[math.cos(a), -math.sin(a), cx], [math.sin(a), math.cos(a), cy]]
        transforms.append(['rotate', (a, cx, cy)])
        # -- skewX --
    if result.group(1) == "skewX":
        a = float(result.group(2))  # "*math.pi/180
        matrix = [[1, math.tan(a), 0], [0, 1, 0]]
        transforms.append(['skewX', (a,)])
        # -- skewY --
    if result.group(1) == "skewY":
        a = float(result.group(2))  # *math.pi/180
        matrix = [[1, 0, 0], [math.tan(a), 1, 0]]
        transforms.append(['skewY', (a,)])
        # -- matrix --
    if result.group(1) == "matrix":
        # a11,a21,a12,a22,v1,v2=result.group(2).replace(' ',',').split(",")
        matrix_params = tuple(map(float, result.group(2).replace(',', ' ').split()))
        a11, a21, a12, a22, v1, v2 = matrix_params
        matrix = [[a11, a12, v1], [a21, a22, v2]]
        transforms.append(['matrix', matrix_params])

    if result.end() < len(stripped_transform):
        return transforms + parse_transform(stripped_transform[result.end():])
    else:
        return transforms


def parse_color(c):
    """Creates a rgb int array"""
    # Based on the code in parseColor in the simplestyle.py module
    # Fixes a few bugs. Should be removed when fixed upstreams.
    if c in list(inkex.colors.SVG_COLOR.keys()):
        c = inkex.colors.SVG_COLOR[c]
        # need to handle 'currentColor'
    if c.startswith('#') and len(c) == 4:
        c = '#' + c[1:2] + c[1:2] + c[2:3] + c[2:3] + c[3:] + c[3:]
    elif c.startswith('rgb('):
        # remove the rgb(...) stuff
        tmp = c.strip()[4:-1]
        numbers = [number.strip() for number in tmp.split(',')]
        converted_numbers = []
        if len(numbers) == 3:
            for num in numbers:
                if num.endswith(r'%'):
                    converted_numbers.append(int(float(num[0:-1]) * 255 / 100))
                else:
                    converted_numbers.append(int(num))
            return tuple(converted_numbers)
        else:
            return 0, 0, 0
    try:
        r = int(c[1:3], 16)
        g = int(c[3:5], 16)
        b = int(c[5:], 16)
    except ValueError:
        return 0, 0, 0
    return r, g, b


def parse_style(s):
    """Create a dictionary from the value of an inline style attribute"""
    # This version strips leading and trailing whitespace from keys and values
    if s:
        return dict([list(map(str.strip, i.split(":"))) for i in s.split(";") if len(i)])
    else:
        return {}


class GraphicsState(object):
    """A class for handling the graphics state of an SVG element

    The graphics state includes fill, stroke and transformations.
    """
    fill = {}
    stroke = {}
    is_visible = True
    transform = []
    color = None
    opacity = 1
    marker_start = None
    marker_mid = None
    marker_end = None

    def __init__(self, svg_node):
        self.svg_node = svg_node
        self._parent_states = None
        self._get_graphics_state(svg_node)

    def _get_graphics_state(self, node):
        """Return the painting state of the node SVG element"""
        if node is None:
            return
        style = parse_style(node.get('style', ''))
        # get stroke and fill properties
        stroke = {}
        fill = {}

        for stroke_property in STROKE_PROPERTIES:
            stroke_val = style.get(stroke_property) or node.get(stroke_property)
            if stroke_val:
                stroke[stroke_property] = stroke_val

        for fill_property in FILL_PROPERTIES:
            fill_val = style.get(fill_property) or node.get(fill_property)
            if fill_val:
                fill[fill_property] = fill_val

        display = style.get('display') or node.get('display')
        visibility = style.get('visibility') or node.get('visibility')
        if display == 'none' or visibility == 'hidden':
            is_visible = False
        else:
            is_visible = True

        self.color = style.get('color') or node.get('color')
        self.stroke = stroke
        self.fill = fill
        self.is_visible = is_visible
        opacity = style.get('opacity') or node.get('opacity')
        self.opacity = opacity or 1
        transform = node.get('transform', '')
        if transform:
            self.transform = parse_transform(transform)
        else:
            self.transform = []

        self.marker_start = style.get('marker-start') or node.get('marker-start')
        self.marker_mid = style.get('marker-mid') or node.get('marker-mid')
        self.marker_end = style.get('marker-end') or node.get('marker-end')

    def _get_parent_states(self, node=None):
        """Returns the parent's graphics states as a list"""
        if node is None:
            node = self.svg_node
        parent_node = node.getparent()
        if not parent_node:
            return None
        parents_state = []
        while parent_node:
            parents_state.append(GraphicsState(parents_state))
            parent_node = parent_node.getparent()
        return parents_state

    parent_states = property(fget=_get_parent_states)

    def accumulate(self, state):
        new_state = GraphicsState(None)
        new_state.fill = copy.copy(self.fill)
        new_state.stroke = copy.copy(self.stroke)
        new_state.transform = copy.copy(self.transform)
        new_state.opacity = copy.copy(self.opacity)
        new_state.marker_start = copy.copy(self.marker_start)
        new_state.marker_end = copy.copy(self.marker_end)
        new_state.marker_mid = copy.copy(self.marker_mid)
        new_state.fill.update(state.fill)
        new_state.stroke.update(state.stroke)
        if new_state.stroke.get('stroke', '') == 'none':
            del new_state.stroke['stroke']
        if new_state.fill.get('fill', '') == 'none':
            del new_state.fill['fill']
        new_state.transform += state.transform
        new_state.is_visible = self.is_visible and state.is_visible
        if state.color:
            new_state.color = state.color

        new_state.opacity *= state.opacity
        new_state.marker_start = state.marker_start
        new_state.marker_mid = state.marker_mid
        new_state.marker_end = state.marker_end
        return new_state

    def __str__(self):
        return "fill %s\nstroke: %s\nvisible: %s\ntransformations: %s\nmarker-start: %s\nmarker-mid: %s\nmarker-end: %s" % \
               (self.fill, self.stroke, self.is_visible, self.transform, self.marker_start, self.marker_mid,
                self.marker_end)


class TikZPathExporter(inkex.Effect):
    def __init__(self, inkscape_mode=True):
        self.inkscape_mode = inkscape_mode
        inkex.Effect.__init__(self)
        if not hasattr(self, 'unittouu'):
            self.svg.unittouu = inkex.unittouu

        self._set_up_options()

        self.text_indent = ''
        self.x_o = self.y_o = 0.0
        # px -> cm scale factors
        self.x_scale = 0.02822219
        # SVG has its origin in the upper left corner, while TikZ' origin is
        # in the lower left corner. We therefore have to reverse the y-axis.
        self.y_scale = -0.02822219
        self.colors = {}
        self.color_code = ""
        self.gradient_code = ""
        self.output_code = ""
        self.used_gradients = set()
        self.selected_sorted = []

    def _set_up_options(self):
        parser = self.arg_parser
        parser.set_defaults(codeoutput='standalone', crop=False, clipboard=False,
                            wrap=False, indent=True, returnstring=False, scale=1,
                            mode='effect', notext=False, verbose=False, texmode='escape', markings='ignore')
        parser.add_argument('--codeoutput', dest='codeoutput',
                          choices=('standalone', 'codeonly', 'figonly'),
                          help="Amount of boilerplate code (standalone, figonly, codeonly).")
        parser.add_argument('-t', '--texmode', dest='texmode', default='escape',
                          choices=('math', 'escape', 'raw'),
                          help="Set text mode (escape, math, raw). Defaults to 'escape'")
        parser.add_argument('--markings', dest='markings', default='ignore',
                          choices=('ignore', 'translate', 'arrows'),
                          help="Set markings mode (ignore, translate, arrows). Defaults to 'ignore'")
        self._add_booloption(parser, '--crop',
                             dest="crop",
                             help="Use the preview package to crop the tikzpicture")
        self._add_booloption(parser, '--clipboard',
                             dest="clipboard",
                             help="Export to clipboard")
        self._add_booloption(parser, '--wrap',
                             dest="wrap",
                             help="Wrap long lines")
        self._add_booloption(parser, '--indent', default=True)
        parser.add_argument('-to', '--tikzoutput',  type=str,
                          dest='outputfile', default=None,
                          help="")

        self._add_booloption(parser, '--latexpathtype', dest="latexpathtype", default=True)
        parser.add_argument('-r', '--removeabsolute',
                          dest='removeabsolute', default=None,
                          help="")

        if self.inkscape_mode:
            parser.add_argument('--returnstring', action='store_true', dest='returnstring',
                              help="Return as string")
            parser.add_argument("--tab")  # Dummy option. Needed because Inkscape passes the notebook
            # tab as an option.
        parser.add_argument('-m', '--mode', dest='mode',
                          choices=('output', 'effect', 'cli'), help="Extension mode (effect default)")
        self._add_booloption(parser, '--notext', dest='ignore_text', default=False,
                             help="Ignore all text")
        if not self.inkscape_mode:
            parser.add_argument('--standalone', dest='codeoutput',
                              action='store_const', const='standalone',
                              help="Generate a standalone document")
            parser.add_argument('--figonly', dest='codeoutput',
                              action='store_const', const='figonly',
                              help="Generate figure only")
            parser.add_argument('--codeonly', dest='codeoutput',
                              action='store_const', const='codeonly',
                              help="Generate drawing code only")
            parser.add_argument('--scale', dest='scale', type=float,
                              help="Apply scale to resulting image, defaults to 1.0")
            parser.add_argument('-V', '--version', dest='printversion', action='store_true',
                              help="Print version information and exit", default=False),
        self._add_booloption(parser, '--verbose', dest='verbose', default=False,
                             help="Verbose output (useful for debugging)")

    def parse(self, file_or_string=None):
        """Parse document in specified file or on stdin"""
        try:
            if file_or_string:
                try:
                    stream = open(file_or_string, 'r')
                except (IOError, OSError):
                    try:
                        to_unicode = unicode
                    except:  # python 3
                        to_unicode = str
                    stream = io.StringIO(to_unicode(file_or_string))
            else:
                stream = open(self.args[-1], 'r')
        except:
            stream = sys.stdin
        self.document = etree.parse(stream)
        stream.close()

    def _add_booloption(self, parser, *args, **kwargs):
        if self.inkscape_mode:
            kwargs['action'] = 'store'
            kwargs['type'] = inkex.Boolean
            parser.add_argument(*args, **kwargs)
        else:
            kwargs['action'] = 'store_true'
            parser.add_argument(*args, **kwargs)

    def getselected(self):
        """Get selected nodes in document order

        The nodes are stored in the selected dictionary and as a list of
        nodes in selected_sorted.
        """
        self.selected_sorted = []
        if len(self.options.ids) == 0:
            return
            # Iterate over every element in the document

        for node in self.document.getiterator():
            node_id = node.get('id', '')
            if node_id in self.options.ids:
                # self.svg.selected[node_id] = node # useless for now and clash with property setting and setters of selected
                self.selected_sorted.append(node)

    def get_node_from_id(self, node_ref):
        if node_ref.startswith('url('):
            node_id = re.findall(r'url\((.*?)\)', node_ref)
            if len(node_id) > 0:
                ref_id = node_id[0]
        else:
            ref_id = node_ref
        if ref_id.startswith('#'):
            ref_id = ref_id[1:]

        ref_node = self.document.xpath('//*[@id="%s"]' % ref_id,
                                       namespaces=inkex.NSS)
        if len(ref_node) == 1:
            return ref_node[0]
        else:
            return None

    def transform(self, coord_list, cmd=None):
        """Apply transformations to input coordinates"""
        coord_transformed = []
        # TEMP:
        if cmd == 'Q':
            return tuple(coord_list)
        try:
            if not len(coord_list) % 2:
                for x, y in nsplit(coord_list, 2):
                    # coord_transformed.append("%.4fcm" % ((x-self.x_o)*self.x_scale))
                    # oord_transformed.append("%.4fcm" % ((y-self.y_o)*self.y_scale))
                    coord_transformed.append("%.4f" % x)
                    coord_transformed.append("%.4f" % y)
            elif len(coord_list) == 1:
                coord_transformed = ["%.4fcm" % (coord_list[0] * self.x_scale)]
            else:
                coord_transformed = coord_list
        except:
            coord_transformed = coord_list
        return tuple(coord_transformed)

    def pxToPt(self, pixels):
        return pixels * 0.8;

    def get_color(self, color):
        """Return a valid xcolor color name and store color"""

        if color in self.colors:
            return self.colors[color]
        else:
            r, g, b = parse_color(color)
            if not (r or g or b):
                return "black"
            if color.startswith('rgb'):
                xcolorname = "c%02x%02x%02x" % (r, g, b)
            else:
                xcolorname = color.replace('#', 'c')
            self.colors[color] = xcolorname
            self.color_code += "\\definecolor{%s}{RGB}{%s,%s,%s}\n" \
                               % (xcolorname, r, g, b)
            return xcolorname

    def _convert_gradient(self, gradient_node, gradient_tikzname):
        """Convert an SVG gradient to a PGF gradient"""

        # http://www.w3.org/TR/SVG/pservers.html
        def bpunit(offset):
            bp_unit = ""
            if offset.endswith("%"):
                bp_unit = offset[0:-1]
            else:
                bp_unit = str(int(round((float(offset)) * 100)))
            return bp_unit

        if gradient_node.tag == _ns('linearGradient'):
            c = ""
            c += "\pgfdeclarehorizontalshading{%s}{100bp}{\n" % gradient_tikzname
            stops = []
            for n in gradient_node:
                if n.tag == _ns('stop'):
                    stops.append("color(%spt)=(%s)" % (bpunit(n.get("offset")), self.get_color(n.get("stop-color"))))
            c += ";".join(stops)
            c += "\n}\n"
            return c

        else:
            return ""

    def _handle_gradient(self, gradient_ref, node=None):
        grad_node = self.get_node_from_id(gradient_ref)
        gradient_id = grad_node.get('id')
        if grad_node is None:
            return []
        gradient_tikzname = gradient_id
        if gradient_id not in self.used_gradients:
            grad_code = self._convert_gradient(grad_node, gradient_tikzname)
            if grad_code:
                self.gradient_code += grad_code
                self.used_gradients.add(gradient_id)
        if gradient_id in self.used_gradients:
            return ['shade', 'shading=%s' % gradient_tikzname]
        else:
            return []

    def _handle_markers(self, state, accumulated_state):
        # http://www.w3.org/TR/SVG/painting.html#MarkerElement
        if self.options.markings == 'ignore':
            return []
        if state.marker_start:
            if state.marker_start == 'none' and accumulated_state.marker_start:
                pass

    def convert_svgstate_to_tikz(self, state, accumulated_state=None, node=None):
        """Return a node's SVG styles as a list of TikZ options"""
        if not state.is_visible:
            return [], []

        options = []
        transform = []

        if state.color:
            options.append('color=%s' % self.get_color(state.color))

        stroke = state.stroke.get('stroke', '')
        if stroke != 'none':
            if stroke:
                if stroke == 'currentColor':
                    options.append('draw')
                else:
                    options.append('draw=%s' % self.get_color(stroke))
            else:
                # need to check if parent element has stroke set
                if 'stroke' in accumulated_state.stroke:
                    options.append('draw')

        fill = state.fill.get('fill')
        if fill != 'none':
            if fill:
                if fill == 'currentColor':
                    options.append('fill')
                elif fill.startswith('url('):
                    pass
                    # shadeoptions = self._handle_gradient(fill)
                    # options.extend(shadeoptions)
                else:
                    options.append('fill=%s' % self.get_color(fill))
            else:
                if 'fill' in accumulated_state.fill:
                    options.append('fill')

        marker_options = self._handle_markers(state, accumulated_state)
        if marker_options:
            options += marker_options

        # dash pattern has to come before dash phase. This is a bug in TikZ 2.0
        # Fixed in CVS.
        dasharray = state.stroke.get('stroke-dasharray')
        if dasharray and dasharray != 'none':
            lengths = list(map(self.svg.unittouu, [i.strip() for i in dasharray.split(',')]))
            dashes = []
            for idx, length in enumerate(lengths):
                lenstr = "%0.2fpt" % (length * 0.8 * self.options.scale)
                if idx % 2:
                    dashes.append("off %s" % lenstr)
                else:
                    dashes.append("on %s" % lenstr)
            options.append('dash pattern=%s' % " ".join(dashes))

        try:
            opacity = float(state.opacity)
            if opacity < 1.0:
                options.append('opacity=%.03f' % opacity)
        except:
            pass

        for svgname, tikzdata in PROPERTIES_MAP.items():
            tikzname, valuetype, data = tikzdata
            value = state.fill.get(svgname) or state.stroke.get(svgname)
            if not value:
                continue
            if valuetype == SCALE:
                val = float(value)
                if not val == 1:
                    options.append('%s=%.3f' % (tikzname, float(value)))
            elif valuetype == DICT:
                if tikzname:
                    options.append('%s=%s' % (tikzname, data.get(value, '')))
                else:
                    options.append('%s' % data.get(value, ''))
            elif valuetype == DIMENSION:
                # FIXME: Handle different dimensions in a general way
                if value and value != data:
                    options.append('%s=%.3fpt' % (tikzname, self.svg.unittouu(value) * 0.8 * self.options.scale)),
            elif valuetype == FACTOR:
                try:
                    val = float(value)
                    if val >= 1.0:
                        options.append('%s=%.2f' % (tikzname, val))
                except ValueError:
                    pass

        if len(state.transform) > 0:
            transform = self._convert_transform_to_tikz(state.transform)
        else:
            transform = []

        return options, transform

    def _convert_transform_to_tikz(self, transform):
        """Convert a SVG transform attribute to a list of TikZ transformations"""
        # return ""
        if not transform:
            return []

        options = []
        for cmd, params in transform:
            if cmd == 'translate':
                x, y = params
                options.append("shift={(%s,%s)}" % (round(x, 5) or '0', round(y, 5) or '0'))
                # There is bug somewere.
                # shift=(400,0) is not equal to xshift=400

            elif cmd == 'rotate':
                if params[1] or params[2]:
                    options.append("rotate around={%s:(%s,%s)}" % params)
                else:
                    options.append("rotate=%s" % round(params[0], 5))
            elif cmd == 'matrix':
                options.append("cm={{%s,%s,%s,%s,(%s,%s)}}" % tuple([round(x, 5) for x in params]))
            elif cmd == 'skewX':
                options.append("xslant=%.3f" % math.tan(params[0] * math.pi / 180))
            elif cmd == 'skewY':
                options.append("yslant=%.3f" % math.tan(params[0] * math.pi / 180))
            elif cmd == 'scale':
                if params[0] == params[1]:
                    options.append("scale=%.3f" % params[0])
                else:
                    options.append("xscale=%.3f,yscale=%.3f" % params)

        return options

    def _handle_group(self, groupnode, graphics_state, accumulated_state):
        s = ""
        tmp = self.text_indent

        self.text_indent += TEXT_INDENT
        group_id = groupnode.get('id')
        code = self._output_group(groupnode, accumulated_state.accumulate(graphics_state))
        self.text_indent = tmp
        if self.options.verbose and group_id:
            extra = "%% %s" % group_id
        else:
            extra = ''
        goptions, transformation = self.convert_svgstate_to_tikz(graphics_state, graphics_state, groupnode)
        options = transformation + goptions
        if len(options) > 0:
            pstyles = [','.join(options)]
            if 'opacity' in pstyles[0]:
                pstyles.append('transparency group')

            if self.options.indent:
                s += "%s\\begin{scope}[%s]%s\n%s%s\\end{scope}\n" % \
                     (self.text_indent, ",".join(pstyles), extra,
                      code, self.text_indent)
            else:
                s += "\\begin{scope}[%s]%s\n%s\\end{scope}\n" % \
                     (",".join(pstyles), extra, code)
        elif self.options.verbose:
            if self.options.indent:
                s += "%s\\begin{scope}%s\n%s%s\\end{scope}\n" % \
                     (self.text_indent, extra, code, self.text_indent)
            else:
                s += "\\begin{scope}\n%s\\end{scope}\n" % \
                     (code,)
        else:
            s += code
        return s

    def _handle_image(self, node):
        """Handles the image tag and returns a code, options tuple"""
        # http://www.w3.org/TR/SVG/struct.html#ImageElement
        # http://www.w3.org/TR/SVG/coords.html#PreserveAspectRatioAttribute
        #         Convert the pixel values to pt first based on http://www.endmemo.com/sconvert/pixelpoint.php
        x = self.svg.unittouu(node.get('x', '0'));
        y = self.svg.unittouu(node.get('y', '0'));

        width = self.pxToPt(self.svg.unittouu(node.get('width', '0')));
        height = self.pxToPt(self.svg.unittouu(node.get('height', '0')));

        href = node.get(_ns('href', 'xlink'));
        isvalidhref = 'data:image/png;base64' not in href;
        if (self.options.latexpathtype and isvalidhref):
            href = href.replace(self.options.removeabsolute, '');
        if (not isvalidhref):
            href = 'base64 still not supported';
            # print (" x:%s, y:%s, w:%s, h:%s, %% Href %s," % (x, y,width, height,  node.get(_ns('href', 'xlink'))));
        # return None, []
        return ('image', (x, y, width, height, href)), []

    def _handle_path(self, node):
        try:
            raw_path = node.get('d')
            #p = simplepath.parsePath(raw_path)
            p = inkex.Path(raw_path).to_arrays()

            #             logging.warning('Path Values %s'%(len(p)),);
            for path_punches in p:
                #                 Scale, and 0.8 has to be applied to the path values
                try:
                    cmd, xy = path_punches;
                    path_punches[1] = [self.svg.unittouu(str(val)) for val in xy];
                except ValueError:
                    pass;
        except:
            e = sys.exc_info()[0];
            logging.warning('Failed to parse path %s, will ignore it', raw_path)
            logging.warning('Exception %s' % (e), );
            logging.warning('Values %s' % (path_punches));
            p = None
        return p, []

    def _handle_shape(self, node):
        """Extract shape data from node"""
        options = []
        if node.tag == _ns('rect'):
            inset = node.get('rx', '0') or node.get('ry', '0')
            # TODO: ry <> rx is not supported by TikZ. Convert to path?
            x = self.svg.unittouu(node.get('x', '0'))
            y = self.svg.unittouu(node.get('y', '0'))
            # map from svg to tikz
            width = self.svg.unittouu(node.get('width', '0'))
            height = self.svg.unittouu(node.get('height', '0'))
            if width == 0.0 or height == 0.0:
                return None, []
            if inset:
                # TODO: corner radius is not scaled by PGF. Find a better way to fix this.
                options = ["rounded corners=%s" % self.transform([self.svg.unittouu(inset) * 0.8 * self.options.scale])]
            return ('rect', (x, y, width + x, height + y)), options
        elif node.tag in [_ns('polyline'),
                          _ns('polygon')]:
            points = node.get('points', '').replace(',', ' ')
            points = list(map(self.svg.unittouu, points.split()))
            if node.tag == _ns('polyline'):
                cmd = 'polyline'
            else:
                cmd = 'polygon'

            return (cmd, points), options
        elif node.tag in _ns('line'):
            points = [node.get('x1'), node.get('y1'),
                      node.get('x2'), node.get('y2')]
            points = list(map(self.svg.unittouu, points))
            # check for zero lenght line
            if not ((points[0] == points[2]) and (points[1] == points[3])):
                return ('polyline', points), options

        if node.tag == _ns('circle'):
            # ugly code...
            center = list(map(self.svg.unittouu, [node.get('cx', '0'), node.get('cy', '0')]))
            r = self.svg.unittouu(node.get('r', '0'))
            if r > 0.0:
                return ('circle', self.transform(center) + self.transform([r])), options

        elif node.tag == _ns('ellipse'):
            center = list(map(self.svg.unittouu, [node.get('cx', '0'), node.get('cy', '0')]))
            rx = self.svg.unittouu(node.get('rx', '0'))
            ry = self.svg.unittouu(node.get('ry', '0'))
            if rx > 0.0 and ry > 0.0:
                return ('ellipse', self.transform(center) + self.transform([rx])
                        + self.transform([ry])), options
        else:
            return None, options

        return None, options

    def _handle_text(self, node):
        if self.options.ignore_text:
            return None, []
        raw_textstr = self.get_text(node).strip()
        if self.options.texmode == 'raw':
            textstr = raw_textstr
        elif self.options.texmode == 'math':
            textstr = "$%s$" % raw_textstr
        else:
            textstr = escape_texchars(raw_textstr)

        x = self.svg.unittouu(node.get('x', '0'))
        y = self.svg.unittouu(node.get('y', '0'))
        p = [('M', [x, y]), ('TXT', textstr)]
        return p, []

    def _handle_use(self, node, graphics_state, accumulated_state=None):
        # Find the id of the use element link
        ref_id = node.get(_ns('href', 'xlink'))
        if ref_id.startswith('#'):
            ref_id = ref_id[1:]

        use_ref_node = self.document.xpath('//*[@id="%s"]' % ref_id,
                                           namespaces=inkex.NSS)
        if len(use_ref_node) > 0:
            # len(use_ref_node) > 1 means that there are several elements with the
            # same id. According to the XML spec the value should be unique.
            # SVG generated by some tools (for instance Matplotlib) does not obey this rule,
            # so we just pick the first one. Should probably generate a warning as well.
            use_ref_node = use_ref_node[0]
        else:
            return ""

        # create a temp group
        g_wrapper = etree.Element(_ns('g'))
        use_g = etree.SubElement(g_wrapper, _ns('g'))

        # transfer attributes from use element to new group except
        # x, y, width, height and href
        for key in list(node.keys()):
            if key not in ('x', 'y', 'width', 'height',
                           _ns('href', 'xlink')):
                use_g.set(key, node.get(key))
        if node.get('x') or node.get('y'):
            transform = node.get('transform', '')
            transform += ' translate(%s,%s) ' \
                         % (self.svg.unittouu(node.get('x', 0)), self.svg.unittouu(node.get('y', 0)))
            use_g.set('transform', transform)
            #
        use_g.append(deepcopy(use_ref_node))
        return self._output_group(g_wrapper, accumulated_state)

    def _write_tikz_path(self, pathdata, options=None, node=None):
        """Convert SVG paths, shapes and text to TikZ paths"""
        s = pic = pathcode = imagecode = ""
        # print "Pathdata %s" % pathdata
        if not pathdata or len(pathdata) == 0:
            return ""
        if node is not None:
            node_id = node.get('id', '')
        else:
            node_id = ''

        current_pos = [0.0, 0.0]
        for cmd, params in pathdata:
            # transform coordinates
            tparams = self.transform(params, cmd)
            # SVG paths
            # moveto
            if cmd == 'M':
                s += "(%s,%s)" % tparams
                current_pos = params[-2:]
            # lineto
            elif cmd == 'L':
                s += " -- (%s,%s)" % tparams
                current_pos = params[-2:]
            # cubic bezier curve
            elif cmd == 'C':
                s += " .. controls (%s,%s) and (%s,%s) .. (%s,%s)" % tparams
                current_pos = params[-2:]
            # quadratic bezier curve
            elif cmd == 'Q':
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
                s += " .. controls (%.4f,%.4f) and (%.4f,%.4f) .. (%.4f,%.4f)" \
                     % (cp1x, cp1y, cp2x, cp2y, qp2x, qp2y)
                current_pos = params[-2:]
            # close path
            elif cmd == 'Z':
                s += " -- cycle"
                closed_path = True
            # arc
            elif cmd == 'A':
                start_ang_o, end_ang_o, rx, ry = calc_arc(current_pos[0], current_pos[1], *params)
                # pgf 2.0 does not like angles larger than 360
                # make sure it is in the +- 360 range
                start_ang = start_ang_o % 360
                end_ang = end_ang_o % 360
                if start_ang_o < end_ang_o and not (start_ang < end_ang):
                    start_ang -= 360
                elif start_ang_o > end_ang_o and not (start_ang > end_ang):
                    end_ang -= 360
                ang = params[2]
                if rx == ry:
                    # Todo: Transform radi
                    radi = "%.3f" % rx
                else:
                    radi = "%3f and %.3f" % (rx, ry)
                if ang != 0.0:
                    s += "{[rotate=%s] arc(%.3f:%.3f:%s)}" % (ang, start_ang, end_ang, radi)
                else:
                    s += "arc(%.3f:%.3f:%s)" % (start_ang, end_ang, radi)
                current_pos = params[-2:]
                pass
            elif cmd == 'TXT':
                s += " node[above right] (%s) {%s}" % (node_id, params)
            # Shapes
            elif cmd == 'rect':
                s += "(%s,%s) rectangle (%s,%s)" % tparams
                closed_path = True
            elif cmd in ['polyline', 'polygon']:
                points = ["(%s,%s)" % (x, y) for x, y in chunks(tparams, 2)]
                if cmd == 'polygon':
                    points.append('cycle')
                    closed_path = True
                s += " -- ".join(points)
            # circle and ellipse does not use the transformed parameters
            elif cmd == 'circle':
                s += "(%s,%s) circle (%s)" % params
                closed_path = True
            elif cmd == 'ellipse':
                s += "(%s,%s) ellipse (%s and %s)" % params
                closed_path = True
            elif cmd == 'image':
                closed_path = False;
                pic += "\\node[anchor=north west,inner sep=0, scale=\globalscale] (image) at (%s,%s) {\includegraphics[width=%spt,height=%spt]{%s}}" % params;
        #                 pic += "\draw (%s,%s) node[below right]  {\includegraphics[width=%spt,height=%spt]{%s}}" % params;

        if options:
            optionscode = "[%s]" % ','.join(options)
        else:
            optionscode = ""

        if (s != ''):
            pathcode = "\\path%s %s;" % (optionscode, s)
        if (pic != ''):
            imagecode = "%s;" % (pic)
        if self.options.wrap:
            pathcode = "\n".join(wrap(pathcode, 80, subsequent_indent="  ", break_long_words=False))
            imagecode = "\n".join(wrap(imagecode, 80, subsequent_indent="  ", break_long_words=False))
        if self.options.indent:
            pathcode = "\n".join([self.text_indent + line for line in pathcode.splitlines(False)]) + "\n"
            imagecode = "\n".join([self.text_indent + line for line in imagecode.splitlines(False)]) + "\n"
        if self.options.verbose and node_id:
            pathcode = "%s%% %s\n%s\n" % (self.text_indent, node_id, pathcode)
            imagecode = "%s%% %s\n%s\n" % (self.text_indent, node_id, imagecode)
        return pathcode + '\n' + imagecode + '\n';

    def get_text(self, node):
        """Return content of a text node as string"""
        # For recent versions of lxml we can simply write:
        # return etree.tostring(node,method="text")
        text = ""
        if node.text is not None:
            text += node.text
        for child in node:
            text += self.get_text(child)
        if node.tail:
            text += node.tail
        return text

    def _output_group(self, group, accumulated_state=None):
        """Process a group of SVG nodes and return corresponding TikZ code

        The group is processed recursively if it contains sub groups.
        """
        s = ""
        options = []
        transform = []
        for node in group:
            pathdata = None
            options = []
            graphics_state = GraphicsState(node)
            node_id = node.get('id')
            if node.tag == _ns('path'):
                pathdata, options = self._handle_path(node)

            # is it a shape?
            elif node.tag in [_ns('rect'),
                              _ns('polyline'),
                              _ns('polygon'),
                              _ns('line'),
                              _ns('circle'),
                              _ns('ellipse'), ]:
                shapedata, options = self._handle_shape(node)
                if shapedata:
                    pathdata = [shapedata]
            elif node.tag == _ns('image'):
                # pathdata, options = self._handle_image(node)
                imagedata, options = self._handle_image(node)
                if imagedata:
                    pathdata = [imagedata]

            # group node
            elif node.tag == _ns('g'):
                s += self._handle_group(node, graphics_state, accumulated_state)
                continue

            elif node.tag == _ns('text') or node.tag == _ns('flowRoot'):
                pathdata, options = self._handle_text(node)

            elif node.tag == _ns('use'):
                s += self._handle_use(node, graphics_state, accumulated_state)

            else:
                logging.debug("Unhandled element %s", node.tag)

            goptions, transformation = self.convert_svgstate_to_tikz(graphics_state, accumulated_state, node)
            options = transformation + goptions + options
            s += self._write_tikz_path(pathdata, options, node)
        return s

    def effect(self):
        s = ""
        nodes = self.selected_sorted
        # If no nodes is selected convert whole document.
        if len(nodes) == 0:
            nodes = self.document.getroot()
            graphics_state = GraphicsState(nodes)
        else:
            graphics_state = GraphicsState(None)
        goptions, transformation = self.convert_svgstate_to_tikz(graphics_state, graphics_state,
                                                                 self.document.getroot())
        options = transformation + goptions
        # Recursively process list of nodes or root node
        s = self._output_group(nodes, graphics_state)

        # Add necessary boiling plate code to the generated TikZ code.
        codeoutput = self.options.codeoutput
        if len(options) > 0:
            extraoptions = ',\n%s' % ','.join(options)
        else:
            extraoptions = ''
        if not self.options.crop:
            cropcode = ""
        else:
            cropcode = CROP_TEMPLATE
        if codeoutput == 'standalone':
            output = STANDALONE_TEMPLATE % dict(pathcode=s,
                                                colorcode=self.color_code,
                                                cropcode=cropcode,
                                                extraoptions=extraoptions,
                                                gradientcode=self.gradient_code,
                                                scale=self.options.scale)
        elif codeoutput == 'figonly':
            output = FIG_TEMPLATE % dict(pathcode=s, colorcode=self.color_code,
                                         extraoptions=extraoptions,
                                         gradientcode=self.gradient_code,
                                         scale=self.options.scale)
        else:
            output = s

        self.output_code = output
        if self.options.returnstring:
            return output

    def save_raw(self, output_code):
        if self.options.clipboard:
            success = copy_to_clipboard(self.output_code.encode('utf8'))
            if not success:
                logging.error('Failed to put output on clipboard')
        if self.options.mode == 'effect':
            if self.options.outputfile and not self.options.clipboard:
                print(self.options.outputfile)
                f = codecs.open(self.options.outputfile, 'w', 'utf8')
                f.write(self.output_code)
                f.close()
                # Serialize document into XML on stdout
            self.document.write(sys.stdout.buffer)

        if self.options.mode == 'output':
            print(self.output_code.encode('utf8'))

    def convert(self, svg_file, cmd_line_mode=False, **kwargs):
        self.options = self.arg_parser.parse_args()
        if self.options.printversion:
            print_version_info()
            return
        self.options.returnstring = True
        self.options.__dict__.update(kwargs)
        if self.options.scale is None:
            self.options.scale = 1
        if cmd_line_mode:
            if self.options.input_file is not None and len(self.options.input_file) > 0:
                if os.path.exists(self.options.input_file):
                    svg_file = self.options.input_file
                else:
                    logging.error('Input file %s does not exists', self.args[0])
                    return
            else:
                # Correct ?
                logging.error('No file were specified')
                return

        self.parse(svg_file)
        self.getselected()
        self.svg.get_ids()
        output = self.effect()
        if self.options.clipboard:
            success = copy_to_clipboard(self.output_code.encode('utf8'))
            if not success:
                logging.error('Failed to put output on clipboard')
            output = ""

        if self.options.outputfile:
            f = codecs.open(self.options.outputfile, 'w', 'utf8')
            f.write(self.output_code)
            f.close()
            output = ""

        return output


def convert_file(svg_file, **kwargs):
    effect = TikZPathExporter(inkscape_mode=False)
    return effect.convert(svg_file, **kwargs)


def convert_svg(svg_source, **kwargs):
    effect = TikZPathExporter(inkscape_mode=False)
    source = open_anything(svg_source)
    tikz_code = effect.convert(source.read(), **kwargs)
    source.close()
    return tikz_code


def main_inkscape():
    """Inkscape interface"""
    # Create effect instance and apply it.
    effect = TikZPathExporter(inkscape_mode=True)
    effect.run()


def print_version_info():
    print("svg2tikz version % s" % __version__)


def main_cmdline(**kwargs):
    """Main command line interface"""
    effect = TikZPathExporter(inkscape_mode=False)
    tikz_code = effect.convert(svg_file=None, cmd_line_mode=True, **kwargs)
    if tikz_code:
        print(tikz_code)


if __name__ == '__main__':
    main_inkscape()
