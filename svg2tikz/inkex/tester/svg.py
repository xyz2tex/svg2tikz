# coding=utf-8
#
# Copyright (C) 2018 Martin Owens
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110, USA.
#
"""
SVG specific utilities for tests.
"""

from lxml import etree

from inkex import SVG_PARSER

def svg(svg_attrs=''):
    """Returns xml etree based on a simple SVG element.

       svg_attrs: A string containing attributes to add to the
           root <svg> element of a minimal SVG document.
    """
    return etree.fromstring(str.encode(
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
        '<svg {}></svg>'.format(svg_attrs)), parser=SVG_PARSER)


def uu_svg(user_unit):
    """Same as svg, but takes a user unit for the new document.

    It's based on the ratio between the SVG width and the viewBox width.
    """
    return svg('width="1{}" viewBox="0 0 1 1"'.format(user_unit))

def svg_file(filename):
    """Parse an svg file and return it's document root"""
    with open(filename, 'r') as fhl:
        doc = etree.parse(fhl, parser=SVG_PARSER)
        return doc.getroot()
