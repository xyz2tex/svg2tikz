# coding=utf-8
#
# Copyright (C) 2018 Martin Owens <doctormo@gmail.com>
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
Parsing inx files for checking and generating.
"""

import os
from lxml import etree

try:
    from inspect import isclass
    from importlib import util
except ImportError:
    util = None  # type: ignore

from .base import InkscapeExtension
from .utils import Boolean

NSS = {
    'inx': 'http://www.inkscape.org/namespace/inkscape/extension',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
}
SSN = dict([(b, a) for (a, b) in NSS.items()])

class InxLookup(etree.CustomElementClassLookup):
    """Custom inx xml file lookup"""
    def lookup(self, node_type, document, namespace, name):  # pylint: disable=unused-argument
        if name == 'param':
            return ParamElement
        return InxElement

INX_PARSER = etree.XMLParser()
INX_PARSER.set_element_class_lookup(InxLookup())

class InxFile(object):
    """Open an INX file and provide useful functions"""
    name = property(lambda self: self.xml._text('name'))
    ident = property(lambda self: self.xml._text('id'))
    slug = property(lambda self: self.ident.split('.')[-1].title().replace('_', ''))
    kind = property(lambda self: self.metadata['type'])
    warnings = property(lambda self: sorted(list(set(self.xml.warnings))))

    def __init__(self, filename):
        if '<' in filename:
            self.filename = None
            self.doc = etree.ElementTree(etree.fromstring(filename, parser=INX_PARSER))
        else:
            self.filename = os.path.basename(filename)
            self.doc = etree.parse(filename, parser=INX_PARSER)
        self.xml = self.doc.getroot()
        self.xml.warnings = []

    def __repr__(self):
        return "<inx '{0.filename}' '{0.name}'>".format(self)

    @property
    def script(self):
        """Returns information about the called script"""
        command = self.xml.find_one('script/command')
        if command is None:
            return {}
        return {
            'interpreter': command.get('interpreter', None),
            'location': command.get('location', None),
            'script': command.text,
        }

    @property
    def extension_class(self):
        """Attempt to get the extension class"""
        script = self.script.get('script', None)
        if script is not None and util is not None:
            name = script[:-3].replace('/', '.')
            spec = util.spec_from_file_location(name, script)
            mod = util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for value in mod.__dict__.values():
                if 'Base' not in name and isclass(value) and  value.__module__ == name \
                    and issubclass(value, InkscapeExtension):
                    return value
        return None

    @property
    def metadata(self):
        """Returns information about what type of extension this is"""
        effect = self.xml.find_one('effect')
        output = self.xml.find_one('output')
        inputs = self.xml.find_one('input')
        data = {}
        if effect is not None:
            template = self.xml.find_one('inkscape:templateinfo')
            if template is not None:
                data['type'] = 'template'
                data['desc'] = self.xml._text('templateinfo/shortdesc', nss='inkscape')
                data['author'] = self.xml._text('templateinfo/author', nss='inkscape')
            else:
                data['type'] = 'effect'
                data['preview'] = Boolean(effect.get('needs-live-preview', 'true'))
                data['objects'] = effect._text('object-type', 'all')
        elif inputs is not None:
            data['type'] = 'input'
            data['extension'] = inputs._text('extension')
            data['mimetype'] = inputs._text('mimetype')
            data['tooltip'] = inputs._text('filetypetooltip')
            data['name'] = inputs._text('filetypename')
        elif output is not None:
            data['type'] = 'output'
            data['dataloss'] = Boolean(output._text('dataloss', 'false'))
            data['extension'] = output._text('extension')
            data['mimetype'] = output._text('mimetype')
            data['tooltip'] = output._text('filetypetooltip')
            data['name'] = output._text('filetypename')
        return data

    @property
    def menu(self):
        """Return the menu this effect ends up in"""
        def _recurse_menu(parent):
            for child in parent.xpath('submenu'):
                yield child.get('name')
                for subchild in _recurse_menu(child):
                    yield subchild
                break # Not more than one menu chain?
        menu = self.xml.find_one('effect/effects-menu')
        return list(_recurse_menu(menu)) + [self.name]

    @property
    def params(self):
        """Get all params at all levels"""
        # Returns any params at any levels
        return list(self.xml.xpath('//param'))

class InxElement(etree.ElementBase):
    def set_warning(self, msg):
        root = self.get_root()
        if hasattr(root, 'warnings'):
            root.warnings.append(msg)

    def get_root(self):
        """Get the root document element from any element descendent"""
        if self.getparent() is not None:
            return self.getparent().get_root()
        return self

    def get_default_prefix(self):
        tag = self.get_root().tag
        if '}' in tag:
            (url, tag) = tag[1:].split('}', 1)
            return SSN.get(url, 'inx')
        self.set_warning(f"No inx xml prefix.")
        return None # no default prefix

    def apply_nss(self, xpath, nss=None):
        """Add prefixes to any xpath string"""
        if nss is None:
            nss = self.get_default_prefix()
        def _process(seg):
            if ':' in seg or not seg or not nss:
                return seg
            return f"{nss}:{seg}"
        return "/".join([_process(seg) for seg in xpath.split("/")])

    def xpath(self, xpath, nss=None):
        """Namespace specific xpath searches"""
        return super().xpath(self.apply_nss(xpath, nss=nss), namespaces=NSS)

    def find_one(self, name, nss=None):
        """Return the first element matching the given name"""
        for elem in self.xpath(name, nss=nss):
            return elem
        return None

    def _text(self, name, default=None, nss=None):
        """Get text content agnostically"""
        for pref in ('', '_'):
            elem = self.find_one(pref + name, nss=nss)
            if elem is not None and elem.text:
                if pref == '_':
                    self.set_warning(f"Use of old translation scheme: <_{name}...>")
                return elem.text
        return default

class ParamElement(InxElement):
    """
    A param in an inx file.
    """
    name = property(lambda self: self.get('name'))
    param_type = property(lambda self: self.get('type', 'string'))

    @property
    def options(self):
        """Return a list of option values"""
        if self.param_type == 'notebook':
            return [option.get('name')
                for option in self.xpath('page')]
        return [option.get('value')
            for option in self.xpath('option')]

    def __repr__(self):
        return f"<param name='{self.name}' type='{self.param_type}'>"
