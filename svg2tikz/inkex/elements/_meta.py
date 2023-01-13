# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Martin Owens <doctormo@gmail.com>
#                    Maren Hachmann <moini>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# pylint: disable=arguments-differ
"""
Provide extra utility to each svg element type specific to its type.

This is useful for having a common interface for each element which can
give path, transform, and property access easily.
"""

import math

from lxml import etree

from ..styles import StyleSheet
from ..transforms import Vector2d

from ._base import BaseElement

class Defs(BaseElement):
    """A header defs element, one per document"""
    tag_name = 'defs'

class StyleElement(BaseElement):
    """A CSS style element containing multiple style definitions"""
    tag_name = 'style'

    def set_text(self, content):
        """Sets the style content text as a CDATA section"""
        self.text = etree.CDATA(str(content))

    def stylesheet(self):
        """Return the StyleSheet() object for the style tag"""
        return StyleSheet(self.text, callback=self.set_text)

class Script(BaseElement):
    """A javascript tag in SVG"""
    tag_name = 'script'

    def set_text(self, content):
        """Sets the style content text as a CDATA section"""
        self.text = etree.CDATA(str(content))

class Desc(BaseElement):
    """Description element"""
    tag_name = 'desc'

class Title(BaseElement):
    """Title element"""
    tag_name = 'title'

class NamedView(BaseElement):
    """The NamedView element is Inkscape specific metadata about the file"""
    tag_name = 'sodipodi:namedview'

    current_layer = property(lambda self: self.get('inkscape:current-layer'))

    @property
    def center(self):
        """Returns view_center in terms of document units"""
        return Vector2d(self.root.unittouu(self.get('inkscape:cx') or 0),
                        self.root.unittouu(self.get('inkscape:cy') or 0))

    def get_guides(self):
        """Returns a list of guides"""
        return self.findall('sodipodi:guide')

    def new_guide(self, position, orient=True, name=None):
        """Creates a new guide in this namedview"""
        if orient is True:
            elem = Guide().move_to(0, position, (0, 1))
        elif orient is False:
            elem = Guide().move_to(position, 0, (1, 0))
        if name:
            elem.set('inkscape:label', str(name))
        return self.add(elem)


class Guide(BaseElement):
    """An inkscape guide"""
    tag_name = 'sodipodi:guide'

    is_horizontal = property(lambda self: self.get('orientation').startswith('0,') and not
                                          self.get('orientation') == '0,0')
    is_vertical = property(lambda self: self.get('orientation').endswith(',0'))
    point = property(lambda self: Vector2d(self.get('position')))

    @classmethod
    def new(cls, pos_x, pos_y, angle, **attrs):
        guide = super(Guide, cls).new(**attrs)
        guide.move_to(pos_x, pos_y, angle=angle)
        return guide

    def move_to(self, pos_x, pos_y, angle=None):
        """
        Move this guide to the given x,y position,

        Angle may be a float or integer, which will change the orientation. Alternately,
        it may be a pair of numbers (tuple) which will set the orientation directly.
        If not given at all, the orientation remains unchanged.
        """
        self.set('position', "{:g},{:g}".format(float(pos_x), float(pos_y)))
        if isinstance(angle, str):
            if ',' not in angle:
                angle = float(angle)

        if isinstance(angle, (float, int)):
            # Generate orientation from angle
            angle = (math.sin(math.radians(angle)), -math.cos(math.radians(angle)))

        if isinstance(angle, (tuple, list)) and len(angle) == 2:
            angle = "{:g},{:g}".format(*angle)

        if angle is not None:
            self.set('orientation', angle)
        return self

class Metadata(BaseElement):
    """Inkscape Metadata element"""
    tag_name = 'metadata'

class ForeignObject(BaseElement):
    """SVG foreignObject element"""
    tag_name = 'foreignObject'

class Switch(BaseElement):
    """A switch element"""
    tag_name = 'switch'

class Grid(BaseElement):
    """A namedview grid child"""
    tag_name = 'inkscape:grid'
