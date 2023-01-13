"""
Element based interface provides the bulk of features that allow you to
interact directly with the SVG xml interface.

See the documentation for each of the elements for details on how it works.
"""

from ._base import SVG_PARSER, load_svg, ShapeElement, BaseElement
from ._svg import SvgDocumentElement
from ._groups import Group, Layer, Anchor, Marker, ClipPath
from ._polygons import PathElement, Polyline, Polygon, Line, Rectangle, Circle, Ellipse
from ._text import FlowRegion, FlowRoot, FlowPara, FlowDiv, FlowSpan, TextElement, \
                   TextPath, Tspan, SVGfont, FontFace, Glyph, MissingGlyph
from ._use import Symbol, Use
from ._meta import Defs, StyleElement, Script, Desc, Title, NamedView, Guide, \
                   Metadata, ForeignObject, Switch, Grid
from ._filters import Filter, Pattern, Gradient, LinearGradient, RadialGradient, \
                      PathEffect, Stop, MeshGradient, MeshRow, MeshPatch
from ._image import Image
