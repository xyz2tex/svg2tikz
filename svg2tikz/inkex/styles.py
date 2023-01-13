# coding=utf-8
#
# Copyright (C) 2005 Aaron Spike, aaron@ekips.org
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
Two simple functions for working with inline css
and some color handling on top.
"""

import re
from collections import OrderedDict

from .utils import PY3
from .colors import Color, ColorIdError
from .tween import interpcoord, interpunit

if PY3:
    unicode = str  # pylint: disable=redefined-builtin,invalid-name

class Classes(list):
    """A list of classes applied to an element (used in css and js)"""
    def __init__(self, classes=None, callback=None):
        self.callback = None
        if isinstance(classes, (str, unicode)):
            classes = classes.split()
        super(Classes, self).__init__(classes or ())
        self.callback = callback

    def __str__(self):
        return " ".join(self)

    def _callback(self):
        if self.callback is not None:
            self.callback(self)

    def __setitem__(self, index, value):
        super(Classes, self).__setitem__(index, value)
        self._callback()

    def append(self, value):
        value = str(value)
        if value not in self:
            super(Classes, self).append(value)
            self._callback()

    def remove(self, value):
        value = str(value)
        if value in self:
            super(Classes, self).remove(value)
            self._callback()

    def toggle(self, value):
        """If exists, remove it, if not, add it"""
        value = str(value)
        if value in self:
            return self.remove(value)
        return self.append(value)

class Style(OrderedDict):
    """A list of style directives"""
    color_props = ('stroke', 'fill', 'stop-color', 'flood-color', 'lighting-color')
    opacity_props = ('stroke-opacity', 'fill-opacity', 'opacity', 'stop-opacity')
    unit_props = ('stroke-width')

    def __init__(self, style=None, callback=None, **kw):
        # This callback is set twice because this is 'pre-initial' data (no callback)
        self.callback = None
        # Either a string style or kwargs (with dashes as underscores).
        style = style or [(k.replace('_', '-'), v) for k, v in kw.items()]
        if isinstance(style, (str, unicode)):
            style = self.parse_str(style)
        # Order raw dictionaries so tests can be made reliable
        if isinstance(style, dict) and not isinstance(style, OrderedDict):
            style = [(name, style[name]) for name in sorted(style)]
        # Should accept dict, Style, parsed string, list etc.
        super(Style, self).__init__(style)
        # Now after the initial data, the callback makes sense.
        self.callback = callback

    @staticmethod
    def parse_str(style):
        """Create a dictionary from the value of an inline style attribute"""
        if style is None:
            style = ""
        for directive in style.split(';'):
            if ':' in directive:
                (name, value) = directive.split(':', 1)
                # FUTURE: Parse value here for extra functionality
                yield (name.strip().lower(), value.strip())

    def __str__(self):
        """Format an inline style attribute from a dictionary"""
        return self.to_str()

    def to_str(self, sep=";"):
        """Convert to string using a custom delimiter"""
        return sep.join(["{0}:{1}".format(*seg) for seg in self.items()])

    def __add__(self, other):
        """Add two styles together to get a third, composing them"""
        ret = self.copy()
        ret.update(Style(other))
        return ret

    def __iadd__(self, other):
        """Add style to this style, the same as style.update(dict)"""
        self.update(other)
        return self

    def __sub__(self, other):
        """Remove keys and return copy"""
        ret = self.copy()
        ret.__isub__(other)
        return ret

    def __isub__(self, other):
        """Remove keys from this style, list of keys or other style dictionary"""
        for key in other:
            self.pop(key, None)
        return self

    def __eq__(self, other):
        """Not equals, prefer to overload 'in' but that doesn't seem possible"""
        if not isinstance(other, Style):
            other = Style(other)
        for arg in set(self) | set(other):
            if self.get(arg, None) != other.get(arg, None):
                return False
        return True
    __ne__ = lambda self, other: not self.__eq__(other)

    def update(self, other):
        """Make sure callback is called when updating"""
        super(Style, self).update(Style(other))
        if self.callback is not None:
            self.callback(self)

    def __setitem__(self, key, value):
        super(Style, self).__setitem__(key, value)
        if self.callback is not None:
            self.callback(self)

    def get_color(self, name='fill'):
        """Get the color AND opacity as one Color object"""
        color = Color(self.get(name, 'none'))
        return color.to_rgba(self.get(name + '-opacity', 1.0))

    def set_color(self, color, name='fill'):
        """Sets the given color AND opacity as rgba to the fill or stroke style properties."""
        color = Color(color)
        if color.space == 'rgba':
            self[name + '-opacity'] = color.alpha
        self[name] = str(color.to_rgb())

    def update_urls(self, old_id, new_id):
        """Find urls in this style and replace them with the new id"""
        for (name, value) in self.items():
            if value == 'url(#{})'.format(old_id):
                self[name] = 'url(#{})'.format(new_id)

    def interpolate_prop(self, other, fraction, prop, svg=None):
        """Interpolate specific property."""
        a1 = self[prop]
        a2 = other.get(prop, None)
        if a2 is None:
            val = a1
        else:
            if prop in self.color_props:
                if isinstance(a1, Color):
                    val = a1.interpolate(Color(a2), fraction)
                elif a1.startswith('url(') or a2.startswith('url('):
                    # gradient requires changes to the whole svg
                    # and needs to be handled externally
                    val = a1
                else:
                    val = Color(a1).interpolate(Color(a2), fraction)
            elif prop in self.opacity_props:
                val = interpcoord(float(a1), float(a2), fraction)
            elif prop in self.unit_props:
                val = interpunit(a1, a2, fraction)
            else:
                val = a1
        return val

    def interpolate(self, other, fraction):
        # type: (Style, float) -> Style
        """Interpolate all properties."""
        style = Style()
        for prop, value in self.items():
            style[prop] = self.interpolate_prop(other, fraction, prop)
        return style


class AttrFallbackStyle(object):
    """
    A container for a style and an element that may have competing styles

    If move is set to true, any new values are set to the style attribute
    and removed from the element attributes list.
    """
    # TODO: This doesn't cover iterating over styles, because we don't
    # have a list of known styles to check attribs for.
    def __init__(self, elem, move=False):
        self.elem = elem
        self.styles = [elem.style]
        self.styles.extend(elem.root.stylesheets.lookup(elem.get('id')))
        self.move = move

    def __getitem__(self, name):
        # Style is more improtant, followed by the element
        for style in self.styles:
            if name in style:
                return style[name]
        return self.elem.attrib.get(name, None)

    def __setitem__(self, name, value):
        # Set the item back into the attribs, or move it if requested.
        if name in self.elem.attrib:
            # The other reason to unset the attrib is if it's already in
            # the style dictionary so isn't needed here anyway.
            if not self.move and name not in self.styles[0]:
                self.elem.set(name, value)
                return
            self.elem.set(name, None)
        for style in self.styles:
            if name in style:
                style[name] = value
                return
        # Not set before (anywhere), so set to element style
        self.styles[0][name] = value

    def get(self, name, default=None):
        """Get with default"""
        try:
            return self[name]
        except KeyError:
            return default

    def set(self, name, value):
        """Set, nothing fancy"""
        self[name] = value

class StyleSheets(list):
    """
    Special mechanism which contains all the stylesheets for an svg document
    while also caching lookups for specific elements.

    This caching is needed because data can't be attached to elements as they are
    re-created on the fly by lxml so lookups have to be centralised.
    """
    def __init__(self, svg=None):
        super(StyleSheets, self).__init__()
        self.svg = svg

    def lookup(self, element_id, svg=None):
        """
        Find all styles for this element.
        """
        # This is aweful, but required because we can't know for sure
        # what might have changed in the xml tree.
        if svg is None:
            svg = self.svg
        for sheet in self:
            for style in sheet.lookup(element_id, svg=svg):
                yield style

class StyleSheet(list):
    """
    A style sheet, usually the CDATA contents of a style tag, but also
    a css file used with a css. Will yield multiple Style() classes.
    """
    comment_strip = re.compile(r"//.*?\n")

    def __init__(self, content=None, callback=None):
        super(StyleSheet, self).__init__()
        self.callback = None
        # Remove comments
        content = self.comment_strip.sub('', (content or ''))
        # Parse rules
        for block in content.split('}'):
            if block:
                self.append(block)
        self.callback = callback

    def __str__(self):
        return '\n' + '\n'.join([str(style) for style in self]) + '\n'

    def _callback(self, style=None): # pylint: disable=unused-argument
        if self.callback is not None:
            self.callback(self)

    def add(self, rule, style):
        """Append a rule and style combo to this stylesheet"""
        self.append(ConditionalStyle(rules=rule, style=str(style), callback=self._callback))

    def append(self, other):
        """Make sure callback is called when updating"""
        if isinstance(other, str):
            if '{' not in other:
                return # Warning?
            rules, style = other.strip('}').split('{', 1)
            other = ConditionalStyle(rules=rules, style=style.strip(), callback=self._callback)
        super(StyleSheet, self).append(other)
        self._callback()

    def lookup(self, element_id, svg):
        """Lookup the element_id against all the styles in this sheet"""
        for style in self:
            for elem in svg.xpath(style.to_xpath()):
                if elem.get('id', None) == element_id:
                    yield style

class ConditionalStyle(Style):
    """
    Just like a Style object, but includes one or more
    conditional rules which places this style in a stylesheet
    rather than being an attribute style.
    """
    def __init__(self, rules='*', style=None, callback=None, **kwargs):
        super(ConditionalStyle, self).__init__(style=style, callback=callback, **kwargs)
        self.rules = [ConditionalRule(rule) for rule in rules.split(',')]

    def __str__(self):
        """Return this style as a css entry with class"""
        content = self.to_str(";\n  ")
        rules = ",\n".join(str(rule) for rule in self.rules)
        if content:
            return "{0} {{\n  {1};\n}}".format(rules, content)
        return "{0} {{}}".format(rules)

    def to_xpath(self):
        """Convert all rules to an xpath"""
        # This can be converted to cssselect.CSSSelector (lxml.cssselect) later if we have
        # coverage problems. The main reason we're not is that cssselect is doing exactly
        # this xpath transform and provides no extra functionality for reverse lookups.
        return '|'.join([rule.to_xpath() for rule in self.rules])

class ConditionalRule(object):
    """A single css rule"""
    step_to_xpath = [
        (re.compile(r'\[(\w+)\^=([^\]]+)\]'), r'[starts-with(@\1,\2)]'), # Starts With
        (re.compile(r'\[(\w+)\$=([^\]]+)\]'), r'[ends-with(@\1,\2)]'), # Ends With
        (re.compile(r'\[(\w+)\*=([^\]]+)\]'), r'[contains(@\1,\2)]'), # Contains
        (re.compile(r'\[([^@\(\)\]]+)\]'), r'[@\1]'), # Attribute (start)
        (re.compile(r'#(\w+)'), r"[@id='\1']"), # Id Match
        (re.compile(r'\s*>\s*([^\s>~\+]+)'), r'/\1'), # Direct child match
        #(re.compile(r'\s*~\s*([^\s>~\+]+)'), r'/following-sibling::\1'),
        #(re.compile(r'\s*\+\s*([^\s>~\+]+)'), r'/following-sibling::\1[1]'),
        (re.compile(r'\s*([^\s>~\+]+)'), r'//\1'), # Decendant match
        (re.compile(r'\.(\w+)'), r"[contains(concat(' ', normalize-space(@class), ' '), ' \1 ')]"),
        (re.compile(r'//\['), r'//*['), # Attribute only match
        (re.compile(r'//(\w+)'), r'//svg:\1'), # SVG namespace addition
    ]

    def __init__(self, rule):
        self.rule = rule.strip()

    def __str__(self):
        return self.rule

    def to_xpath(self):
        """Attempt to convert the rule into a simplified xpath"""
        ret = self.rule
        for matcher, replacer in self.step_to_xpath:
            ret = matcher.sub(replacer, ret)
        return ret
