# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Martin Owens <doctormo@gmail.com>
#                    Sergei Izmailov <sergei.a.izmailov@gmail.com>
#                    Ryan Jarvis <ryan@shopboxretail.com>
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
Interface for all group based elements such as Groups, Use, Markers etc.
"""

from lxml import etree # pylint: disable=unused-import

from ..paths import Path
from ..utils import addNS
from ..transforms import Transform

from ._base import ShapeElement

try:
    from typing import Optional  # pylint: disable=unused-import
except ImportError:
    pass

class GroupBase(ShapeElement):
    """Base Group element"""
    def get_path(self):
        ret = Path()
        for child in self:
            if isinstance(child, ShapeElement):
                ret += child.path.transform(child.transform)
        return ret

    def shape_box(self, transform=None):
        bbox = None
        effective_transform = Transform(transform) * self.transform
        for child in self:
            if isinstance(child, ShapeElement):
                child_bbox = child.bounding_box(transform=effective_transform)
                if child_bbox is not None:
                    bbox += child_bbox
        return bbox


class Group(GroupBase):
    """Any group element (layer or regular group)"""
    tag_name = 'g'

    @classmethod
    def new(cls, label, *children, **attrs):
        attrs['inkscape:label'] = label
        return super(Group, cls).new(*children, **attrs)


    def effective_style(self):
        """A blend of each child's style mixed together (last child wins)"""
        style = self.style
        for child in self:
            style.update(child.effective_style())
        return style

    @property
    def groupmode(self):
        """Return the type of group this is"""
        return self.get('inkscape:groupmode', 'group')


class Layer(Group):
    """Inkscape extension of svg:g"""

    def _init(self):
        self.set('inkscape:groupmode', 'layer')

    @classmethod
    def _is_class_element(cls, el):
        # type: (etree.Element) -> bool
        return el.attrib.get(addNS('inkscape:groupmode'), None) == "layer"


class Anchor(GroupBase):
    """An anchor or link tag"""
    tag_name = 'a'

    @classmethod
    def new(cls, href, *children, **attrs):
        attrs['xlink:href'] = href
        return super(Anchor, cls).new(*children, **attrs)


class ClipPath(GroupBase):
    """A path used to clip objects"""
    tag_name = 'clipPath'


class Marker(GroupBase):
    """The <marker> element defines the graphic that is to be used for drawing arrowheads
     or polymarkers on a given <path>, <line>, <polyline> or <polygon> element."""
    tag_name = 'marker'
