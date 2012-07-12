#!/usr/bin/env python
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

__version__ = '0.1dev'
__author__ = 'Kjell Magne Fauske'


# Todo:
# Basic functionality:

# Stroke properties
#   - markers (map from Inkscape to TikZ arrow styles. No 1:1 mapping)
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
# TODO: Add a testing interface
import sys
from itertools import izip
from textwrap import wrap
from copy import deepcopy
import codecs
import itertools
import string
import StringIO
import copy

try:
    # This should work when run as an Inkscape extension
    import inkex
    import simplepath
    import simplestyle
except ImportError:
    # Use bundled files when run as a module or command line tool 
    from svg2tikz.inkexlib import inkex
    from svg2tikz.inkexlib import simplepath
    from svg2tikz.inkexlib import simplestyle

import pprint, os, re, math

from math import sin, cos, atan2, ceil
import logging

try:
    set
except NameError:
    # For Python 2.4 compatability
    from sets import Set as set



#### Utility functions and classes

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

    Works on Windows, *nix and Mac. Tries the following:
    1. Use the win32clipboard module from the win32 package.
    2. Calls the xclip command line tool (*nix)
    3. Calls the pbcopy command line tool (Mac)
    4. Try pygtk
    """
    # try windows first
    try:
        import win32clipboard

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        return True
    except:
        pass
        # try xclip
    try:
        import subprocess

        p = subprocess.Popen(['xclip', '-selection', 'c'], stdin=subprocess.PIPE)
        p.stdin.write(text)
        p.stdin.close()
        retcode = p.wait()
        return True
    except:
        pass
        # try pbcopy (Os X)
    try:
        import subprocess

        p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        p.stdin.write(text)
        p.stdin.close()
        retcode = p.wait()
        return True
    except:
        pass
        # try os /linux
    try:
        import subprocess

        p = subprocess.Popen(['xsel'], stdin=subprocess.PIPE)
        p.stdin.write(text)
        p.stdin.close()
        retcode = p.wait()
        return True
    except:
        pass
        # try pygtk
    try:
        # Code from
        # http://www.vector-seven.com/2007/06/27/
        #    passing-data-between-gtk-applications-with-gtkclipboard/
        import pygtk

        pygtk.require('2.0')
        import gtk
        # get the clipboard
        clipboard = gtk.clipboard_get()
        # set the clipboard text data
        clipboard.set_text(text)
        # make our data available to other applications
        clipboard.store()
        return True
    except:
        pass
        # try clip (Vista)
    try:
        import subprocess

        p = subprocess.Popen(['clip'], stdin=subprocess.PIPE)
        p.stdin.write(text)
        p.stdin.close()
        retcode = p.wait()
        return True
    except:
        pass

    return False


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
    return [xy for xy in izip(*[iter(seq)] * n)]


def chunks(s, cl):
    """Split a string or sequence into pieces of length cl and return an iterator
    """
    for i in xrange(0, len(s), cl):
        yield s[i:i + cl]

# Adapted from Mark Pilgrim's Dive into Python book
# http://diveintopython.org/scripts_and_streams/index.html#kgp.openanything 
def open_anything(source):
    # try to open with urllib (if source is http, ftp, or file URL)
    import urllib

    try:
        return urllib.urlopen(source)
    except (IOError, OSError):
        pass

        # try to open with native open function (if source is pathname)
    try:
        return open(source)
    except (IOError, OSError):
        pass

        # treat source as string
    import StringIO

    return StringIO.StringIO(str(source))


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
\begin{tikzpicture}[y=0.80pt,x=0.80pt,yscale=-1, inner sep=0pt, outer sep=0pt%(extraoptions)s]
%(pathcode)s
\end{tikzpicture}
\end{document}
"""

FIG_TEMPLATE = r"""
%(colorcode)s
\begin{tikzpicture}[y=0.80pt, x=0.8pt,yscale=-1, inner sep=0pt, outer sep=0pt%(extraoptions)s]
%(pathcode)s
\end{tikzpicture}
"""

SCALE = 'scale'
DICT = 'dict'
DIMENSION = 'dimension'
FACTOR = 'factor' # >= 1

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
        rx *= pl;
        ry *= pl
    carx = sarx = cary = sary = 0.0
    if abs(rx) > 0.0:
        carx = cos(ang) / rx
        sarx = sin(ang) / rx
    if abs(ry) > 0.0:
        cary = cos(ang) / ry
        sary = sin(ang) / ry
    x0 = (carx) * cpx + (sarx) * cpy
    y0 = (-sary) * cpx + (cary) * cpy
    x1 = (carx) * x + (sarx) * y
    y1 = (-sary) * x + (cary) * y
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
    if (ang_arc < 0.0 and fs == 1):
        ang_arc += 2.0 * PI
    elif (ang_arc > 0.0 and fs == 0):
        ang_arc -= 2.0 * PI

    ang0 = math.degrees(ang_0)
    ang1 = math.degrees(ang_1)

    if ang_arc > 0:
        if (ang_0 < ang_1):
            pass
        else:
            ang0 -= 360
    else:
        if (ang_0 < ang_1):
            ang1 -= 360

    return (ang0, ang1, rx, ry)


def parse_transform(transf):
    """Parse a transformation attribute and return a list of transformations"""
    # Based on the code in parseTransform in the simpletransform.py module.
    # Copyright (C) 2006 Jean-Francois Barraud
    # Reimplemented here due to several bugs in the version shipped with
    # Inkscape 0.46
    if transf == "" or transf == None:
        return(mat)
    stransf = transf.strip()
    result = re.match("(translate|scale|rotate|skewX|skewY|matrix)\s*\(([^)]*)\)\s*,?", stransf)
    transforms = []
    #-- translate --
    if result.group(1) == "translate":
        args = result.group(2).replace(',', ' ').split()
        dx = float(args[0])
        if len(args) == 1:
            dy = 0.0
        else:
            dy = float(args[1])
        matrix = [[1, 0, dx], [0, 1, dy]]
        transforms.append(['translate', (dx, dy)])
        #-- scale --
    if result.group(1) == "scale":
        args = result.group(2).replace(',', ' ').split()
        sx = float(args[0])
        if len(args) == 1:
            sy = sx
        else:
            sy = float(args[1])
        matrix = [[sx, 0, 0], [0, sy, 0]]
        transforms.append(['scale', (sx, sy)])
        #-- rotate --
    if result.group(1) == "rotate":
        args = result.group(2).replace(',', ' ').split()
        a = float(args[0])#*math.pi/180
        if len(args) == 1:
            cx, cy = (0.0, 0.0)
        else:
            cx, cy = map(float, args[1:])
        matrix = [[math.cos(a), -math.sin(a), cx], [math.sin(a), math.cos(a), cy]]
        transforms.append(['rotate', (a, cx, cy)])
        #-- skewX --
    if result.group(1) == "skewX":
        a = float(result.group(2))#"*math.pi/180
        matrix = [[1, math.tan(a), 0], [0, 1, 0]]
        transforms.append(['skewX', (a,)])
        #-- skewY --
    if result.group(1) == "skewY":
        a = float(result.group(2))#*math.pi/180
        matrix = [[1, 0, 0], [math.tan(a), 1, 0]]
        transforms.append(['skewY', (a,)])
        #-- matrix --
    if result.group(1) == "matrix":
        #a11,a21,a12,a22,v1,v2=result.group(2).replace(' ',',').split(",")
        mparams = tuple(map(float, result.group(2).replace(',', ' ').split()))
        a11, a21, a12, a22, v1, v2 = mparams
        matrix = [[a11, a12, v1], [a21, a22, v2]]
        transforms.append(['matrix', mparams])

    if result.end() < len(stransf):
        return transforms + parse_transform(stransf[result.end():])
    else:
        return transforms


def parseColor(c):
    """Creates a rgb int array"""
    # Based on the code in parseColor in the simplestyle.py module
    # Fixes a few bugs. Should be removed when fixed upstreams.
    if c in simplestyle.svgcolors.keys():
        c = simplestyle.svgcolors[c]
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
            return (0, 0, 0)
    try:
        r = int(c[1:3], 16)
        g = int(c[3:5], 16)
        b = int(c[5:], 16)
    except:
        return (0, 0, 0)
    return (r, g, b)


def parseStyle(s):
    """Create a dictionary from the value of an inline style attribute"""
    # This version strips leading and trailing whitespace from keys and values
    if s:
        return dict([map(string.strip, i.split(":")) for i in s.split(";") if len(i)])
    else:
        return {}


class GraphicsState(object):
    """A class for handling the graphics state of an SVG element
    
    The graphics state includs fill, stroke and transformations.
    """
    fill = {}
    stroke = {}
    is_visible = True
    transform = []
    color = None
    opacity = 1

    def __init__(self, svg_node):
        self.svg_node = svg_node
        self._parent_states = None
        self._get_graphics_state(svg_node)

    def _get_graphics_state(self, node):
        """Return the painting state of the node SVG element"""
        if node is None: return
        style = parseStyle(node.get('style', ''))
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
        if opacity:
            self.opacity = opacity
        else:
            self.opacity = 1

        transform = node.get('transform', '')
        if transform:
            self.transform = parse_transform(transform)
        else:
            self.transform = []

    def _get_parent_states(self, node=None):
        """Returns the parent's graphics states as a list"""
        if node == None:
            node = self.svg_node
        parent_node = node.getparent()
        if not parent_node:
            return None
        parents_state = []
        while parent_node:
            parents_state.append(GraphicsState(parent_state))
            parent_node = parent_node.getparent()
        return parents_state


    parent_states = property(fget=_get_parent_states)

    def accumulate(self, state):
        newstate = GraphicsState(None)
        newstate.fill = copy.copy(self.fill)
        newstate.stroke = copy.copy(self.stroke)
        newstate.transform = copy.copy(self.transform)
        newstate.opacity = copy.copy(self.opacity)
        newstate.fill.update(state.fill)
        newstate.stroke.update(state.stroke)
        if newstate.stroke.get('stroke', '') == 'none':
            del newstate.stroke['stroke']
        if newstate.fill.get('fill', '') == 'none':
            del newstate.fill['fill']
        newstate.transform += state.transform
        newstate.is_visible = self.is_visible and state.is_visible
        if state.color:
            newstate.color = state.color

        newstate.opacity *= state.opacity
        return newstate

    def __str__(self):
        return "fill %s\nstroke: %s\nvisible: %s\ntransformations: %s" %\
               (self.fill, self.stroke, self.is_visible, self.transform)


class TikZPathExporter(inkex.Effect):
    def __init__(self, inkscape_mode=True):
        self.inkscape_mode = inkscape_mode
        inkex.Effect.__init__(self)

        parser = self.OptionParser
        parser.set_defaults(codeoutput='standalone', crop=False, clipboard=False,
            wrap=True, indent=True, returnstring=False,
            mode='effect', notext=False, verbose=False)
        parser.add_option('--codeoutput', dest='codeoutput',
            choices=('standalone', 'codeonly', 'figonly'),
            help="Amount of boilerplate code (standalone, figonly, codeonly).")

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
        parser.add_option("-o", "--output",
            action="store", type="string",
            dest="outputfile", default=None,
            help="")
        if self.inkscape_mode:
            parser.add_option('--returnstring', action='store_true', dest='returnstring',
                help="Return as string")

        parser.add_option('-m', '--mode', dest='mode',
            choices=('output', 'effect', 'cli'), help="Extension mode (effect default)")

        self._add_booloption(parser, '--notext', dest='ignore_text', default=False,
            help="Ignore all text")
        if not self.inkscape_mode:
            parser.add_option('--standalone', dest='codeoutput',
                action='store_const', const='standalone',
                help="Generate a standalone document")
            parser.add_option('--figonly', dest='codeoutput',
                action='store_const', const='figonly',
                help="Generate figure only")
            parser.add_option('--codeonly', dest='codeoutput',
                action='store_const', const='codeonly',
                help="Generate drawing code only")
        self._add_booloption(parser, '--verbose', dest='verbose', default=False,
            help="Verbose output (useful for debugging)")

        self.text_indent = ''
        self.x_o = self.y_o = 0.0
        # px -> cm scale factors
        self.x_scale = 0.02822219;
        # SVG has its origin in the upper left corner, while TikZ' origin is
        # in the lower left corner. We therefore have to reverse the y-axis.
        self.y_scale = -0.02822219;
        self.colors = {}
        self.colorcode = ""
        self.shadecode = ""
        self.output_code = ""

    def parse(self, file_or_string=None):
        """Parse document in specified file or on stdin"""
        try:
            if file_or_string:
                try:
                    stream = open(file_or_string, 'r')
                except:
                    stream = StringIO.StringIO(file_or_string)
            else:
                stream = open(self.args[-1], 'r')
        except:
            stream = sys.stdin
        self.document = inkex.etree.parse(stream)
        stream.close()

    def _add_booloption(self, parser, *args, **kwargs):
        if self.inkscape_mode:
            kwargs['action'] = 'store'
            kwargs['type'] = 'inkbool'
            parser.add_option(*args, **kwargs)
        else:
            kwargs['action'] = 'store_true'
            parser.add_option(*args, **kwargs)

    def getselected(self):
        """Get selected nodes in document order

        The nodes are stored in the selected dictionary and as a list of
        nodes in selected_sorted.
        """
        self.selected_sorted = []
        self.selected = {}
        if len(self.options.ids) == 0:
            return
            # Iterate over every element in the document
        for node in self.document.getiterator():
            id = node.get('id', '')
            if id in self.options.ids:
                self.selected[id] = node
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
                    #coord_transformed.append("%.4fcm" % ((x-self.x_o)*self.x_scale))
                    #oord_transformed.append("%.4fcm" % ((y-self.y_o)*self.y_scale))
                    coord_transformed.append("%.4f" % x)
                    coord_transformed.append("%.4f" % y)
            elif len(coord_list) == 1:
                coord_transformed = ["%.4fcm" % (coord_list[0] * self.x_scale)]
            else:
                coord_transformed = coord_list
        except:
            coord_transformed = coord_list
        return tuple(coord_transformed)

    def get_color(self, color):
        """Return a valid xcolor color name and store color"""

        if color in self.colors:
            return self.colors[color]
        else:
            r, g, b = parseColor(color)
            if not (r or g or b):
                return "black"
            if color.startswith('rgb'):
                xcolorname = "c%02x%02x%02x" % (r, g, b)
            else:
                xcolorname = color.replace('#', 'c')
            self.colors[color] = xcolorname
            self.colorcode += "\\definecolor{%s}{RGB}{%s,%s,%s}\n"\
            % (xcolorname, r, g, b)
            return xcolorname

    def _convert_gradient(self, gradient_node):
        """Convert an SVG gradient to a PGF gradient"""
        # http://www.w3.org/TR/SVG/pservers.html
        pass

    def _handle_gradient(self, gradient_ref, node=None):
        grad_node = self.get_node_from_id(gradient_ref)
        if grad_node == None:
            return []
        return ['shade', 'shading=%s' % grad_node.get('id')]


    def convert_svgstate_to_tikz(self, state, accumulated_state=None, node=None):
        """Return a node's SVG styles as a list of TikZ options"""
        if state.is_visible == False:
            return [], []

        options = []
        transform = []

        if state.color:
            options.append('color=%s' % self.get_color(state.color))

        stroke = state.stroke.get('stroke', '')
        if stroke <> 'none':
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
        if fill <> 'none':
            if fill:
                if fill == 'currentColor':
                    options.append('fill')
                #elif fill.startswith('url('):
                #    shadeoptions = self._handle_gradient(fill)
                #    options.extend(shadeoptions)
                else:
                    options.append('fill=%s' % self.get_color(fill))
            else:
                # Todo: check parent element
                if 'fill' in accumulated_state.fill:
                    options.append('fill')

        # dash pattern has to come before dash phase. This is a bug in TikZ 2.0
        # Fixed in CVS.             
        dasharray = state.stroke.get('stroke-dasharray')
        if dasharray and dasharray <> 'none':
            lengths = map(inkex.unittouu, [i.strip() for i in dasharray.split(',')])
            dashes = []
            for idx, length in enumerate(lengths):
                lenstr = "%0.2fpt" % (length * 0.8)
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

        for svgname, tikzdata in PROPERTIES_MAP.iteritems():
            tikzname, valuetype, data = tikzdata
            value = state.fill.get(svgname) or state.stroke.get(svgname)
            if not value: continue
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
                if value and value <> data:
                    options.append('%s=%.3fpt' % (tikzname, inkex.unittouu(value) * 0.80)),
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
        #return ""
        if not transform:
            return []

        options = []
        for cmd, params in transform:
            if cmd == 'translate':
                x, y = params
                options.append("shift={(%s,%s)}" % (x or '0', y or '0'))
                # There is bug somewere.
                # shift=(400,0) is not equal to xshift=400

            elif cmd == 'rotate':
                if params[1] or params[2]:
                    options.append("rotate around={%s:(%s,%s)}" % params)
                else:
                    options.append("rotate=%s" % params[0])
            elif cmd == 'matrix':
                options.append("cm={{%s,%s,%s,%s,(%s,%s)}}" % params)
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
        id = groupnode.get('id')
        code = self._output_group(groupnode, accumulated_state.accumulate(graphics_state))
        self.text_indent = tmp
        if self.options.verbose and id:
            extra = "%% %s" % id
        else:
            extra = ''
        goptions, transformation = self.convert_svgstate_to_tikz(graphics_state, graphics_state, groupnode)
        options = transformation + goptions
        if len(options) > 0:
            pstyles = [','.join(options)]
            if 'opacity' in pstyles[0]:
                pstyles.append('transparency group')

            if self.options.indent:
                s += "%s\\begin{scope}[%s]%s\n%s%s\\end{scope}\n" %\
                     (self.text_indent, ",".join(pstyles), extra,
                      code, self.text_indent)
            else:
                s += "\\begin{scope}[%s]%s\n%s\\end{scope}\n" %\
                     (",".join(pstyles), extra, code)
        elif self.options.verbose:
            if self.options.indent:
                s += "%s\\begin{scope}%s\n%s%s\\end{scope}\n" %\
                     (self.text_indent, extra, code, self.text_indent)
            else:
                s += "\\begin{scope}\n%s\\end{scope}\n" %\
                     (code,)
        else:
            s += code
        return s

    def _handle_image(self, node):
        """Handles the image tag and returns a code, options tuple"""
        # http://www.w3.org/TR/SVG/struct.html#ImageElement
        # http://www.w3.org/TR/SVG/coords.html#PreserveAspectRatioAttribute
        x = node.get('x', '0')
        y = node.get('y', '0')
        print "%% Href %s" % node.get(inkex.addNS('href', 'xlink'))
        return None, []

    def _handle_path(self, node):
        p = simplepath.parsePath(node.get('d'))
        return p, []

    def _handle_shape(self, node):
        """Extract shape data from node"""
        options = []
        if node.tag == inkex.addNS('rect', 'svg'):
            inset = node.get('rx', '0') or node.get('ry', '0')
            # TODO: ry <> rx is not supported by TikZ. Convert to path?
            x = inkex.unittouu(node.get('x', '0'))
            y = inkex.unittouu(node.get('y', '0'))
            # map from svg to tikz
            width = inkex.unittouu(node.get('width', '0'))
            height = inkex.unittouu(node.get('height', '0'))
            if (width == 0.0 or height == 0.0):
                return None, []
            if inset:
                # TODO: corner radius is not scaled by PGF. Find a better way to fix this. 
                options = ["rounded corners=%s" % self.transform([inkex.unittouu(inset) * 0.8])]
            return ('rect', (x, y, width + x, height + y)), options
        elif node.tag in [inkex.addNS('polyline', 'svg'),
                          inkex.addNS('polygon', 'svg'),
                          ]:
            points = node.get('points', '').replace(',', ' ')
            points = map(inkex.unittouu, points.split())
            if node.tag == inkex.addNS('polyline', 'svg'):
                cmd = 'polyline'
            else:
                cmd = 'polygon'

            return (cmd, points), options
        elif node.tag in inkex.addNS('line', 'svg'):
            points = [node.get('x1'), node.get('y1'),
                      node.get('x2'), node.get('y2')]
            points = map(inkex.unittouu, points)
            # check for zero lenght line
            if not ((points[0] == points[2]) and (points[1] == points[3])):
                return ('polyline', points), options

        if node.tag == inkex.addNS('circle', 'svg'):
            # ugly code...
            center = map(inkex.unittouu, [node.get('cx', '0'), node.get('cy', '0')])
            r = inkex.unittouu(node.get('r', '0'))
            if r > 0.0:
                return ('circle', self.transform(center) + self.transform([r])), options

        elif node.tag == inkex.addNS('ellipse', 'svg'):
            center = map(inkex.unittouu, [node.get('cx', '0'), node.get('cy', '0')])
            rx = inkex.unittouu(node.get('rx', '0'))
            ry = inkex.unittouu(node.get('ry', '0'))
            if rx > 0.0 and ry > 0.0:
                return ('ellipse', self.transform(center) + self.transform([rx])
                + self.transform([ry])), options
        else:
            return None, options

        return None, options

    def _handle_text(self, node):
        if not self.options.ignore_text:
            textstr = self.get_text(node)
            x = node.get('x', '0')
            y = node.get('y', '0')
            p = [('M', [x, y]), ('TXT', textstr)]
            return p, []
        else:
            return None, []

    def _handle_use(self, node, graphics_state, accumulated_state=None):
        # Find the id of the use element link
        ref_id = node.get(inkex.addNS('href', 'xlink'))
        if ref_id.startswith('#'):
            ref_id = ref_id[1:]

        use_ref_node = self.document.xpath('//*[@id="%s"]' % ref_id,
            namespaces=inkex.NSS)
        if len(use_ref_node) == 1:
            use_ref_node = use_ref_node[0]
        else:
            return ""

        # create a temp group
        g_wrapper = inkex.etree.Element(inkex.addNS('g', 'svg'))
        use_g = inkex.etree.SubElement(g_wrapper, inkex.addNS('g', 'svg'))

        # transfer attributes from use element to new group except
        # x, y, width, height and href
        for key in node.keys():
            if key not in ('x', 'y', 'width', 'height',
                           inkex.addNS('href', 'xlink')):
                use_g.set(key, node.get(key))
        if node.get('x') or node.get('y'):
            transform = node.get('transform', '')
            transform += ' translate(%s,%s) '\
            % (node.get('x', 0), node.get('y', 0))
            use_g.set('transform', transform)
            #
        use_g.append(deepcopy(use_ref_node))
        return self._output_group(g_wrapper, accumulated_state)

    def _write_tikz_path(self, pathdata, options=[], node=None):
        """Convert SVG paths, shapes and text to TikZ paths"""
        s = pathcode = ""
        #print "Pathdata %s" % pathdata
        if not pathdata or len(pathdata) == 0:
            return ""
        if node is not None:
            id = node.get('id', '')
        else:
            id = ''

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
                #CP1 = QP0 + 2/3 *(QP1-QP0)
                #CP2 = CP1 + 1/3 *(QP2-QP0)
                # http://fontforge.sourceforge.net/bezier.html
                qp0x, qp0y = current_pos
                qp1x, qp1y, qp2x, qp2y = tparams
                cp1x = qp0x + (2.0 / 3.0) * (qp1x - qp0x)
                cp1y = qp0y + (2.0 / 3.0) * (qp1y - qp0y)
                cp2x = cp1x + (qp2x - qp0x) / 3.0
                cp2y = cp1y + (qp2y - qp0y) / 3.0
                s += " .. controls (%.4f,%.4f) and (%.4f,%.4f) .. (%.4f,%.4f)"\
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
                if ang <> 0.0:
                    s += "{[rotate=%s] arc(%.3f:%.3f:%s)}" % (ang, start_ang, end_ang, radi)
                else:
                    s += "arc(%.3f:%.3f:%s)" % (start_ang, end_ang, radi)
                current_pos = params[-2:]
                pass
            elif cmd == 'TXT':
                s += " node[above right] (%s) {%s}" % (id, params)
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

        if options:
            optionscode = "[%s]" % ','.join(options)
        else:
            optionscode = ""

        pathcode = "\\path%s %s;" % (optionscode, s)
        if self.options.wrap:
            pathcode = "\n".join(wrap(pathcode, 80, subsequent_indent="  ",
                break_long_words=False))

        if self.options.indent:
            pathcode = "\n".join([self.text_indent + line for line in pathcode.splitlines(False)]) + "\n"
        if self.options.verbose and id:
            pathcode = "%s%% %s\n%s\n" % (self.text_indent, id, pathcode)
        return pathcode

    def get_text(self, node):
        """Return content of a text node as string"""
        # For recent versions of lxml we can simply write:
        # return etree.tostring(node,method="text")
        text = ""
        if node.text != None:
            text += node.text
        for child in node:
            text += self.get_text(child)
        if node.tail:
            text += node.tail
        return text

    def _output_group(self, group, accumulated_state=None):
        """Proceess a group of SVG nodes and return corresponding TikZ code
        
        The group is processed recursively if it contains sub groups. 
        """
        s = ""
        options = []
        transform = []
        for node in group:
            pathdata = None
            options = []
            graphics_state = GraphicsState(node)
            #print graphics_state 
            id = node.get('id')
            if node.tag == inkex.addNS('path', 'svg'):
                pathdata, options = self._handle_path(node)


            # is it a shape?
            elif node.tag in [inkex.addNS('rect', 'svg'),
                              inkex.addNS('polyline', 'svg'),
                              inkex.addNS('polygon', 'svg'),
                              inkex.addNS('line', 'svg'),
                              inkex.addNS('circle', 'svg'),
                              inkex.addNS('ellipse', 'svg'), ]:
                shapedata, options = self._handle_shape(node)
                if shapedata:
                    pathdata = [shapedata]
            elif node.tag == inkex.addNS('image', 'svg'):
                pathdata, options = self._handle_image(node)

            # group node
            elif node.tag == inkex.addNS('g', 'svg'):
                s += self._handle_group(node, graphics_state, accumulated_state)
                continue

            elif node.tag == inkex.addNS('text', 'svg'):
                pathdata, options = self._handle_text(node)

            elif node.tag == inkex.addNS('use', 'svg'):
                s += self._handle_use(node, graphics_state, accumulated_state)

            else:
                # unknown element
                pass

            goptions, transformation = self.convert_svgstate_to_tikz(graphics_state, accumulated_state, node)
            #print goptions, transformation, options
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
            output = STANDALONE_TEMPLATE % dict(pathcode=s,\
                colorcode=self.colorcode,\
                cropcode=cropcode,\
                extraoptions=extraoptions)
        elif codeoutput == 'figonly':
            output = FIG_TEMPLATE % dict(pathcode=s, colorcode=self.colorcode,\
                extraoptions=extraoptions)
        else:
            output = s

        self.output_code = output
        if self.options.returnstring:
            return output

    def output(self):
        if self.options.clipboard:
            success = copy_to_clipboard(self.output_code)
            if not success:
                logging.error('Failed to put output on clipboard')
        if self.options.mode == 'effect':
            if self.options.outputfile and not self.options.clipboard:
                f = codecs.open(self.options.outputfile, 'w', 'utf8')
                f.write(self.output_code)
                f.close()
                # Serialize document into XML on stdout
            self.document.write(sys.stdout)

        if self.options.mode == 'output':
            print self.output_code.encode('utf8')

    def convert(self, svg_file, **kwargs):
        self.getoptions()
        self.options.returnstring = True
        #self.options.crop=True
        self.options.__dict__.update(kwargs)
        self.parse(svg_file)
        self.getposinlayer()
        self.getselected()
        self.getdocids()
        output = self.effect()
        if self.options.clipboard:
            success = copy_to_clipboard(self.output_code)
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
    effect = TikZPathExporter(inkscape_mode=False);
    return effect.convert(svg_file, **kwargs)


def convert_svg(svg_source, **kwargs):
    effect = TikZPathExporter(inkscape_mode=False);
    source = open_anything(svg_source)
    tikz_code = effect.convert(source.read(), **kwargs)
    source.close()
    return tikz_code


def main_inkscape():
    """Inkscape interface"""
    # Create effect instance and apply it.
    effect = TikZPathExporter(inkscape_mode=True)
    effect.affect()


def main_cmdline(**kwargs):
    """Main command line interface"""
    effect = TikZPathExporter(inkscape_mode=False);
    tikz_code = effect.convert(svg_file=None, **kwargs)
    print tikz_code.encode('utf8')


if __name__ == '__main__':
    main_inkscape()
