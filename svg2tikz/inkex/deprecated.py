# coding=utf-8
#
# Copyright (C) 2018 - Martin Owens <doctormo@mgail.com>
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
"""
Provide some documentation to existing extensions about why they're failing.
"""
#
# We ignore a lot of pylint warnings here:
#
# pylint: disable=invalid-name,unused-argument,missing-docstring,too-many-public-methods
#

import os
import sys
import traceback
import warnings
import argparse
from argparse import ArgumentParser

# import inkex
# import svg2tikz.inkex
import svg2tikz.inkex.utils
import svg2tikz.inkex.units
from svg2tikz.inkex.base import SvgThroughMixin, InkscapeExtension
from svg2tikz.inkex.localization import inkex_gettext as _

warnings.simplefilter("default")
# To load each of the deprecated sub-modules (the ones without a namespace)
# we will add the directory to our pythonpath so older scripts can find them

INKEX_DIR = os.path.abspath(os.path.dirname(__file__))
SIMPLE_DIR = os.path.join(INKEX_DIR, 'deprecated-simple')

if os.path.isdir(SIMPLE_DIR):
    sys.path.append(SIMPLE_DIR)

try:
    DEPRECATION_LEVEL = int(os.environ.get('INKEX_DEPRECATION_LEVEL', 1))
except ValueError:
    DEPRECATION_LEVEL = 1

def _deprecated(msg, stack=2, level=DEPRECATION_LEVEL):
    """Internal method for raising a deprecation warning"""
    if level > 1:
        msg += ' ; '.join(traceback.format_stack())
    if level:
        warnings.warn(msg, category=DeprecationWarning, stacklevel=stack + 1)

class DeprecatedEffect(object):
    """An Inkscape effect, takes SVG in and outputs SVG, providing a deprecated layer"""

    def __init__(self):
        super(DeprecatedEffect, self).__init__()

        self._doc_ids = None

        # These are things we reference in the deprecated code, they are provided
        # by the new effects code, but we want to keep this as a Mixin so these
        # items will keep pylint happy and let use check our code as we write.
        if not hasattr(self, 'svg'):
            from .elements import SvgDocumentElement
            self.svg = SvgDocumentElement()
        if not hasattr(self, 'arg_parser'):
            self.arg_parser = ArgumentParser()
        if not hasattr(self, 'run'):
            self.run = self.affect

    @classmethod
    def _deprecated(cls, name, msg=_('{} is deprecated and should be removed'), stack=3):
        """Give the user a warning about their extension using a deprecated API"""
        _deprecated(
            msg.format('Effect.' + name, cls=cls.__module__ + '.' + cls.__name__),
            stack=stack)

    @property
    def OptionParser(self):
        self._deprecated(
            'OptionParser',
            _('{} or `optparse` has been deprecated and replaced with `argparser`. '
              'You must change `self.OptionParser.add_option` to '
              '`self.arg_parser.add_argument`; the arguments are similar.'))
        return self

    def add_option(self, *args, **kw):
        # Convert type string into type method as needed
        if 'type' in kw:
            kw['type'] = {
                'string': str,
                'int': int,
                'float': float,
                'inkbool': inkex.utils.Boolean,
            }.get(kw['type'])
        if kw.get('action', None) == 'store':
            # Default store action not required, removed.
            kw.pop('action')
        args = [arg for arg in args if arg != ""]
        self.arg_parser.add_argument(*args, **kw)

    def effect(self):
        self._deprecated('effect', _('{} method is now a required method. It should '
                                     'be created on {cls}, even if it does nothing.'))

    @property
    def current_layer(self):
        self._deprecated('current_layer',\
            _('{} is now a method in the SvgDocumentElement class. Use `self.svg.get_current_layer()` instead.'))
        return self.svg.get_current_layer()

    @property
    def view_center(self):
        self._deprecated('view_center',\
            _('{} is now a method in the SvgDocumentElement class. Use `self.svg.get_center_position()` instead.'))
        return self.svg.namedview.center

    @property
    def selected(self):
        self._deprecated('selected', _('{} is now a dict in the SvgDocumentElement class. Use `self.svg.selected`.'))
        return dict([(elem.get('id'), elem) for elem in self.svg.selected])

    @property
    def doc_ids(self):
        self._deprecated('doc_ids', _('{} is now a method in the SvgDocumentElement class.'
                                      'Use `self.svg.get_ids()` instead.'))
        if self._doc_ids is None:
            self._doc_ids = dict.fromkeys(self.svg.get_ids())
        return self._doc_ids

    def getdocids(self):
        self._deprecated('getdocids', _('Use `self.svg.get_ids()` instead of {} and `doc_ids`.'))
        self._doc_ids = None
        self.svg.ids.clear()

    def getselected(self):
        self._deprecated('getselected', _('{} has been removed'))

    def getElementById(self, eid):
        self._deprecated('getElementById',\
            _('{} is now a method in the SvgDocumentElement class. Use `self.svg.getElementById(eid)` instead.'))
        return self.svg.getElementById(eid)

    def xpathSingle(self, xpath):
        self._deprecated('xpathSingle', _('{} is now a new method in the SvgDocumentElement class. '
                                          'Use `self.svg.getElement(path)` instead.'))
        return self.svg.getElement(xpath)

    def getParentNode(self, node):
        self._deprecated('getParentNode',\
            _('{} is no longer in use. Use the lxml `.getparent()` method instead.'))
        return node.getparent()

    def getNamedView(self):
        self._deprecated('getNamedView',\
            _('{} is now a property of the SvgDocumentElement class. '
              'Use `self.svg.namedview` to access this element.'))
        return self.svg.namedview

    def createGuide(self, posX, posY, angle):
        from .elements import Guide
        self._deprecated('createGuide',\
            _('{} is now a method of the namedview element object. '
              'Use `self.svg.namedview.add(Guide().move_to(x, y, a))` instead.'))
        return self.svg.namedview.add(Guide().move_to(posX, posY, angle))

    def affect(self, args=sys.argv[1:], output=True):  # pylint: disable=dangerous-default-value
        # We need a list as the default value to preserve backwards compatibility
        self._deprecated('affect', _('{} is now `Effect.run()`. The `output` argument has changed.'))
        #FIX ME: should have not change here
        self.args = args[-1:]
        return self.run(args=args)

    @property
    def args(self):
        self._deprecated('args', _('self.args[-1] is now self.options.input_file.'))
        #FIX ME: should have not change here
        return self.args

    @property
    def svg_file(self):
        self._deprecated('svg_file', _('self.svg_file is now self.options.input_file.'))
        return self.options.input_file

    def save_raw(self, ret):
        # Derived class may implement "output()"
        # Attention: 'cubify.py' implements __getattr__ -> hasattr(self, 'output') returns True
        if hasattr(self.__class__, 'output'):
            self._deprecated('output', 'Use `save()` or `save_raw()` instead.', stack=5)
            return getattr(self, 'output')()
        return inkex.base.InkscapeExtension.save_raw(self, ret)

    def uniqueId(self, old_id, make_new_id=True):
        self._deprecated('uniqueId', _('{} is now a method in the SvgDocumentElement class. '
                                       ' Use `self.svg.get_unique_id(old_id)` instead.'))
        return self.svg.get_unique_id(old_id)

    def getDocumentWidth(self):
        self._deprecated('getDocumentWidth', _('{} is now a property of the SvgDocumentElement class. '
                                               'Use `self.svg.width` instead.'))
        return self.svg.get('width')

    def getDocumentHeight(self):
        self._deprecated('getDocumentHeight', _('{} is now a property of the SvgDocumentElement class. '
                                                'Use `self.svg.height` instead.'))
        return self.svg.get('height')

    def getDocumentUnit(self):
        self._deprecated('getDocumentUnit', _('{} is now a property of the SvgDocumentElement class. '
                                              'Use `self.svg.unit` instead.'))
        return self.svg.unit

    def unittouu(self, string):
        self._deprecated('unittouu', _('{} is now a method in the SvgDocumentElement class. '
                                       'Use `self.svg.unittouu(str)` instead.'))
        return self.svg.unittouu(string)

    def uutounit(self, val, unit):
        self._deprecated('uutounit', _('{} is now a method in the SvgDocumentElement class. '
                                       'Use `self.svg.uutounit(value, unit)` instead.'))
        return self.svg.uutounit(val, unit)

    def addDocumentUnit(self, value):
        self._deprecated('addDocumentUnit', _('{} is now a method in the SvgDocumentElement class. '
                                              'Use `self.svg.add_unit(value)` instead.'))
        return self.svg.add_unit(value)

class Effect(SvgThroughMixin, DeprecatedEffect, InkscapeExtension):
    """An Inkscape effect, takes SVG in and outputs SVG"""
    pass

def deprecate(func):
    """Function decorator for deprecation functions which have a one-liner
    equivalent in the new API. The one-liner has to passed as a string
    to the decorator.

    >>> @deprecate
    >>> def someOldFunction(*args):
    >>>     '''Example replacement code someNewFunction('foo', ...)'''
    >>>     someNewFunction('foo', *args)

    Or if the args API is the same:

    >>> someOldFunction = deprecate(someNewFunction)

    """

    def _inner(*args, **kwargs):
        _deprecated('{0.__module__}.{0.__name__} -> {0.__doc__}'.format(func), stack=2)
        return func(*args, **kwargs)
    _inner.__name__ = func.__name__
    if func.__doc__:
        _inner.__doc__ = "Deprecated -> " + func.__doc__
    return _inner

class DeprecatedDict(dict):
    @deprecate
    def __getitem__(self, key):
        return super(DeprecatedDict, self).__getitem__(key)

    @deprecate
    def __iter__(self):
        return super(DeprecatedDict, self).__iter__()

# legacy inkex members

class lazyproxy(object):
    """Proxy, use as decorator on a function with provides the wrapped object.
    The decorated function is called when a member is accessed on the proxy.
    """
    def __init__(self, getwrapped):
        '''
        :param getwrapped: Callable which returns the wrapped object
        '''
        self._getwrapped = getwrapped

    def __getattr__(self, name):
        return getattr(self._getwrapped(), name)

    def __call__(self, *args, **kwargs):
        return self._getwrapped()(*args, **kwargs)

@lazyproxy
def optparse():
    _deprecated('inkex.optparse was removed, use "import optparse"', stack=3)
    import optparse as wrapped
    return wrapped

@lazyproxy
def etree():
    _deprecated('inkex.etree was removed, use "from lxml import etree"', stack=3)
    from lxml import etree as wrapped
    return wrapped

@lazyproxy
def InkOption():
    import optparse
    class wrapped(optparse.Option):
        TYPES = optparse.Option.TYPES + ("inkbool", )
        TYPE_CHECKER = dict(optparse.Option.TYPE_CHECKER)
        TYPE_CHECKER["inkbool"] = lambda _1, _2, v: str(v).capitalize() == 'True'
    return wrapped

@lazyproxy
def localize():
    _deprecated('inkex.localize was moved to inkex.localization.localize.', stack=3)
    from .localization import localize as wrapped
    return wrapped

def are_near_relative(a, b, eps):
    _deprecated('inkex.are_near_relative was moved to '
                'inkex.units.are_near_relative', stack=2)
    return inkex.units.are_near_relative(a, b, eps)

def debug(what):
    _deprecated('inkex.debug was moved to inkex.utils.debug.', stack=2)
    return inkex.utils.debug(what)

# legacy inkex members <= 0.48.x

def unittouu(string):
    _deprecated('inkex.unittouu is now a method in the SvgDocumentElement class. '
            'Use `self.svg.unittouu(str)` instead.', stack=2)
    return inkex.units.convert_unit(string, 'px')

# optparse.Values.ensure_value

def ensure_value(self, attr, value):
    _deprecated('Effect().options.ensure_value was removed.', stack=2)
    if getattr(self, attr, None) is None:
        setattr(self, attr, value)
    return getattr(self, attr)

argparse.Namespace.ensure_value = ensure_value # type: ignore

@deprecate
def zSort(inNode, idList):
    """self.svg.get_z_selected()"""
    sortedList = []
    theid = inNode.get("id")
    if theid in idList:
        sortedList.append(theid)
    for child in inNode:
        if len(sortedList) == len(idList):
            break
        sortedList += zSort(child, idList)
    return sortedList

class DeprecatedSvgMixin(object):
    """Mixin which adds deprecated API elements to the SvgDocumentElement"""
    @property
    def selected(self):
        """svg.selection"""
        return self.selection

    @selected.setter
    def set_selected(self, *ids):
        """svg.selection.set(*ids)"""
        return self.selection.set(*ids)

    @deprecate
    def get_z_selected(self):
        """svg.selection.paint_order()"""
        return self.selection.paint_order()

    @deprecate
    def get_selected(self, *types):
        """svg.selection.filter(*types).values()"""
        return self.selection.filter(*types).values()

    @deprecate
    def get_selected_or_all(self, *types):
        """Set select_all = True in extension class"""
        if not self.selection:
            self.selection.set_all()
        return self.selection.filter(*types)

    @deprecate
    def get_selected_bbox(self):
        """selection.bounding_box()"""
        return self.selection.bounding_box()

    @deprecate
    def get_first_selected(self, *types):
        """selection.filter(*types).first() or [0] if you'd like an error"""
        return self.selection.filter(*types).first()
