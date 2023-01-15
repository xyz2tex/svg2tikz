# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Martin Owens <doctormo@gmail.com>
#                    Sergei Izmailov <sergei.a.izmailov@gmail.com>
#                    Thomas Holder <thomas.holder@schrodinger.com>
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
Interface for all shapes/polygons such as lines, paths, rectangles, circles etc.
"""

from ..paths import Path
from ..transforms import Transform, ImmutableVector2d, Vector2d
from ..utils import addNS
from ..units import convert_unit

from ._base import ShapeElement

class PathElementBase(ShapeElement):
    """Base element for path based shapes"""
    get_path = lambda self: self.get('d')

    @classmethod
    def new(cls, path, **attrs):
        return super(PathElementBase, cls).new(d=Path(path), **attrs)

    def set_path(self, path):
        """Set the given data as a path as the 'd' attribute"""
        self.set('d', str(Path(path)))

    def apply_transform(self):
        """Apply the internal transformation to this node and delete"""
        if 'transform' in self.attrib:
            self.path = self.path.transform(self.transform)
            self.set('transform', Transform())

    @property
    def original_path(self):
        """Returns the original path if this is a LPE, or the path if not"""
        return Path(self.get('inkscape:original-d', self.path))

    @original_path.setter
    def original_path(self, path):
        if addNS('inkscape:original-d') in self.attrib:
            self.set('inkscape:original-d', str(Path(path)))
        else:
            self.path = path


class PathElement(PathElementBase):
    """Provide a useful extension for path elements"""
    tag_name = 'path'

    @classmethod
    def arc(cls, center, rx, ry=None, **kw): # pylint: disable=invalid-name
        """Generate a sodipodi arc (special type)"""
        others = [(name, kw.pop(name, None)) for name in ('start', 'end', 'open')]
        elem = cls(**kw)
        elem.set('sodipodi:cx', center[0])
        elem.set('sodipodi:cy', center[1])
        elem.set('sodipodi:rx', rx)
        elem.set('sodipodi:ry', ry or rx)
        elem.set('sodipodi:type', 'arc')
        for name, value in others:
            if value is not None:
                elem.set('sodipodi:'+name, str(value).lower())
        return elem

    @classmethod
    def star(cls, center, radi, sides, rounded=None):
        """Generate a sodipodi start (special type)"""
        elem = cls()
        elem.set('sodipodi:cx', center[0])
        elem.set('sodipodi:cy', center[1])
        elem.set('sodipodi:r1', radi[0])
        elem.set('sodipodi:r2', radi[1])
        elem.set('sodipodi:arg1', 0.85)
        elem.set('sodipodi:arg2', 1.3)
        elem.set('sodipodi:sides', sides)
        elem.set('inkscape:rounded', rounded)
        elem.set('sodipodi:type', 'star')
        return elem


class Polyline(ShapeElement):
    """Like a path, but made up of straight line segments only"""
    tag_name = 'polyline'

    def get_path(self):
        return Path('M' + self.get('points'))

    def set_path(self, path):
        points = ['{:g},{:g}'.format(x, y) for x, y in Path(path).end_points]
        self.set('points', ' '.join(points))


class Polygon(ShapeElement):
    """A closed polyline"""
    tag_name = 'polygon'
    get_path = lambda self: 'M' + self.get('points') + ' Z'


class Line(ShapeElement):
    """A line segment connecting two points"""
    tag_name = 'line'
    get_path = lambda self: 'M{0[x1]},{0[y1]} L{0[x2]},{0[y2]} Z'.format(self.attrib)

    @classmethod
    def new(cls, start, end, **attrs):
        start = Vector2d(start)
        end = Vector2d(end)
        return super(Line, cls).new(x1=start.x, y1=start.y,
                                    x2=end.x, y2=end.y, **attrs)


class RectangleBase(ShapeElement):
    """Provide a useful extension for rectangle elements"""
    left = property(lambda self: convert_unit(self.get('x', '0'), 'px'))
    top = property(lambda self: convert_unit(self.get('y', '0'), 'px'))
    right = property(lambda self: self.left + self.width)
    bottom = property(lambda self: self.top + self.height)
    width = property(lambda self: convert_unit(self.get('width', '0'), 'px'))
    height = property(lambda self: convert_unit(self.get('height', '0'), 'px'))
    rx = property(lambda self: convert_unit(self.get('rx', self.get('ry', 0.0)), 'px'))
    ry = property(lambda self: convert_unit(self.get('ry', self.get('rx', 0.0)), 'px')) # pylint: disable=invalid-name

    def get_path(self):
        """Calculate the path as the box around the rect"""
        if self.rx:
            rx, ry = self.rx, self.ry # pylint: disable=invalid-name
            return 'M {1},{0.top}'\
                   'L {2},{0.top}    A {0.rx},{0.ry} 0 0 1 {0.right},{3}'\
                   'L {0.right},{4}  A {0.rx},{0.ry} 0 0 1 {2},{0.bottom}'\
                   'L {1},{0.bottom} A {0.rx},{0.ry} 0 0 1 {0.left},{4}'\
                   'L {0.left},{3}   A {0.rx},{0.ry} 0 0 1 {1},{0.top} z'\
                .format(self, self.left + rx, self.right - rx, self.top + ry, self.bottom - ry)

        return 'M {0.left},{0.top} h{0.width}v{0.height}h{1} z'.format(self, -self.width)


class Rectangle(RectangleBase):
    """Provide a useful extension for rectangle elements"""
    tag_name = 'rect'

    @classmethod
    def new(cls, left, top, width, height, **attrs):
        return super().new(x=left, y=top, width=width, height=height, **attrs)


class EllipseBase(ShapeElement):
    """Absorbs common part of Circle and Ellipse classes"""

    def get_path(self):
        """Calculate the arc path of this circle"""
        rx, ry = self._rxry()
        cx, y = self.center.x, self.center.y - ry
        return ('M {cx},{y} '
                'a {rx},{ry} 0 1 0 {rx}, {ry} '
                'a {rx},{ry} 0 0 0 -{rx}, -{ry} z'
                ).format(cx=cx, y=y, rx=rx, ry=ry)

    @property
    def center(self):
        return ImmutableVector2d(convert_unit(self.get('cx', '0'), 'px'), convert_unit(self.get('cy', '0'), 'px'))

    @center.setter
    def center(self, value):
        value = Vector2d(value)
        self.set("cx", value.x)
        self.set("cy", value.y)

    def _rxry(self):
        # type: () -> Vector2d
        """Helper function """
        raise NotImplementedError()

    @classmethod
    def new(cls, center, radius, **attrs):
        circle = super(EllipseBase, cls).new(**attrs)
        circle.center = center
        circle.radius = radius
        return circle


class Circle(EllipseBase):
    """Provide a useful extension for circle elements"""
    tag_name = 'circle'

    @property
    def radius(self):
        return convert_unit(self.get('r', '0'), 'px')

    @radius.setter
    def radius(self, value):
        self.set("r", value)

    def _rxry(self):
        r = self.radius
        return Vector2d(r, r)


class Ellipse(EllipseBase):
    """Provide a similar extension to the Circle interface"""
    tag_name = 'ellipse'

    @property
    def radius(self):
        return ImmutableVector2d(convert_unit(self.get('rx', '0'), 'px'), convert_unit(self.get('ry', '0'), 'px'))

    @radius.setter
    def radius(self, value):
        value = Vector2d(value)
        self.set("rx", str(value.x))
        self.set("ry", str(value.y))

    def _rxry(self):
        return self.radius
